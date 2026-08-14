"""Structured-response parsing and validation."""

from __future__ import annotations

import json
from typing import Any


DIAGNOSES = {
    "uncertainty",
    "misinformation",
    "commitment_trap",
    "domestic_pressure",
    "reciprocity",
    "none",
}
CHANNELS = {"hold", "joint", "private_a", "private_b", "verify"}


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    if start < 0:
        raise ValueError("Response does not contain a JSON object")
    value, _ = json.JSONDecoder().raw_decode(stripped[start:])
    if not isinstance(value, dict):
        raise ValueError("Response JSON must be an object")
    return value


def _exact_fields(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if missing:
        raise ValueError(f"{label} is missing: {', '.join(missing)}")
    if extra:
        raise ValueError(f"{label} has unknown fields: {', '.join(extra)}")


def _probability(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    rounded = int(value)
    if rounded != value or not 0 <= rounded <= 100:
        raise ValueError(f"{field} must be an integer from 0 to 100")
    return rounded


def _short_text(value: Any, field: str, limit: int) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if len(value.split()) > limit:
        raise ValueError(f"{field} must not exceed {limit} words")


def _evidence_ids(value: Any, known_ids: set[str]) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("evidence_ids must be a list of strings")
    if len(value) != len(set(value)):
        raise ValueError("evidence_ids must not contain duplicates")
    unknown = sorted(set(value) - known_ids)
    if unknown:
        raise ValueError(f"Unknown evidence IDs: {', '.join(unknown)}")


def validate_actor_intent(
    value: dict[str, Any], *, postures: set[str], known_ids: set[str]
) -> None:
    required = {
        "belief_opponent_responsible",
        "posture",
        "public_message",
        "private_reason",
        "evidence_ids",
    }
    _exact_fields(value, required, "Actor intent")
    _probability(value["belief_opponent_responsible"], "belief_opponent_responsible")
    if value["posture"] not in postures:
        raise ValueError("Unknown posture")
    _short_text(value["public_message"], "public_message", 90)
    _short_text(value["private_reason"], "private_reason", 120)
    _evidence_ids(value["evidence_ids"], known_ids)


def validate_actor_final(
    value: dict[str, Any], *, postures: set[str], known_ids: set[str]
) -> None:
    required = {
        "belief_opponent_responsible",
        "posture",
        "accepts_intervention",
        "public_message",
        "evidence_ids",
    }
    _exact_fields(value, required, "Actor final move")
    _probability(value["belief_opponent_responsible"], "belief_opponent_responsible")
    if value["posture"] not in postures:
        raise ValueError("Unknown posture")
    if not isinstance(value["accepts_intervention"], bool):
        raise ValueError("accepts_intervention must be true or false")
    _short_text(value["public_message"], "public_message", 90)
    _evidence_ids(value["evidence_ids"], known_ids)


def validate_mediator(
    value: dict[str, Any], *, known_ids: set[str], interventions_left: int
) -> None:
    required = {
        "intervene",
        "channel",
        "message",
        "target_evidence_id",
        "diagnosis",
        "predicted_escalation",
        "reason",
    }
    _exact_fields(value, required, "Mediator move")
    if not isinstance(value["intervene"], bool):
        raise ValueError("intervene must be true or false")
    if value["channel"] not in CHANNELS:
        raise ValueError("Unknown mediator channel")
    if value["diagnosis"] not in DIAGNOSES:
        raise ValueError("Unknown mediator diagnosis")
    _probability(value["predicted_escalation"], "predicted_escalation")
    _short_text(value["reason"], "reason", 100)
    if not isinstance(value["message"], str) or len(value["message"].split()) > 120:
        raise ValueError("message must be a string of at most 120 words")

    target = value["target_evidence_id"]
    if target is not None and not isinstance(target, str):
        raise ValueError("target_evidence_id must be a string or null")
    if value["intervene"]:
        if interventions_left < 1:
            raise ValueError("The intervention budget is exhausted")
        if value["channel"] == "hold":
            raise ValueError("An intervention cannot use the hold channel")
        if not value["message"].strip():
            raise ValueError("An intervention requires a message")
        if value["channel"] == "verify":
            if target not in known_ids:
                raise ValueError("A verification request needs a known evidence ID")
        elif target is not None:
            raise ValueError("Only verification may name target_evidence_id")
    else:
        if value["channel"] != "hold":
            raise ValueError("A non-intervention must use the hold channel")
        if target is not None:
            raise ValueError("A non-intervention cannot target evidence")

