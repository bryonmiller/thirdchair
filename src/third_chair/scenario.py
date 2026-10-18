"""Scenario loading, prompt-safe evidence views, and mutable crisis state."""

from __future__ import annotations

import json
import copy
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "title",
    "one_line",
    "rounds",
    "starting_state",
    "intervention_budget",
    "seats",
    "mediator_brief",
    "postures",
    "episodes",
    "verification_results",
    "ground_truth",
}


def load_scenario(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    data = json.loads(scenario_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        raise ValueError(f"Scenario {scenario_path} is missing: {', '.join(missing)}")
    if set(data["seats"]) != {"a", "b"}:
        raise ValueError("Scenario seats must be a and b")
    if int(data["rounds"]) != len(data["episodes"]):
        raise ValueError("Scenario rounds must match the number of episodes")
    if [episode["round"] for episode in data["episodes"]] != list(
        range(1, int(data["rounds"]) + 1)
    ):
        raise ValueError("Scenario episode rounds must be consecutive")
    posture_ids = [item["id"] for item in data["postures"]]
    if len(posture_ids) != len(set(posture_ids)):
        raise ValueError("Scenario posture IDs must be unique")
    if data["ground_truth"]["responsible_actor"] not in {"state_b", "nonstate"}:
        raise ValueError("responsible_actor must be state_b or nonstate")
    evidence_rounds = {
        item["id"]: episode["round"]
        for episode in data["episodes"]
        for items in episode["evidence"].values()
        for item in items
    }
    all_items = [item for episode in data["episodes"]
                 for items in episode["evidence"].values() for item in items]
    if len(evidence_rounds) != len(all_items):
        raise ValueError("Evidence IDs must be globally unique; use public_disclosures to share cards")
    if any(type(item.get("valid")) is not bool for item in all_items):
        raise ValueError("Evidence validity must be an evaluator-only boolean")
    if not set(data["verification_results"]) <= set(evidence_rounds):
        raise ValueError("Verification results must reference existing evidence")
    for key, result in data["verification_results"].items():
        card = next(item for item in all_items if item["id"] == key)
        if type(result.get("valid")) is not bool or result["valid"] != card["valid"]:
            raise ValueError("Verification validity must agree with its evidence card")
    for field in ("forged_evidence_ids", "decisive_evidence_ids"):
        if not set(data["ground_truth"].get(field, [])) <= set(evidence_rounds):
            raise ValueError(f"{field} must reference existing evidence")
    forged = set(data["ground_truth"].get("forged_evidence_ids", []))
    if any(item["valid"] for item in all_items if item["id"] in forged):
        raise ValueError("Forged evidence cannot be marked valid")
    disclosed: set[str] = set()
    for episode in data["episodes"]:
        ids = episode.get("public_disclosures", [])
        if (not isinstance(ids, list) or not all(isinstance(key, str) for key in ids)
                or len(ids) != len(set(ids)) or disclosed.intersection(ids)
                or any(key not in evidence_rounds or evidence_rounds[key] > episode["round"]
                       for key in ids)):
            raise ValueError("public_disclosures must contain unique, existing, non-future IDs")
        disclosed.update(ids)
    design = data.get("design", {})
    if not isinstance(design, dict):
        raise ValueError("Scenario design metadata must be an object")
    for field in ("family_id", "evidence_namespace"):
        if field in design and (not isinstance(design[field], str) or not design[field].strip()):
            raise ValueError(f"design.{field} must be a non-empty string")
    for episode in data["episodes"]:
        for seat, items in episode["evidence"].items():
            for item in items:
                if "verification_targets" not in item:
                    continue
                targets = item["verification_targets"]
                if (seat != "mediator" or not isinstance(targets, list)
                        or not targets or not all(isinstance(t, str) for t in targets)
                        or len(targets) != len(set(targets))):
                    raise ValueError("verification_targets must be unique IDs on a neutral card")
                if any(t not in evidence_rounds or t not in data["verification_results"]
                       or evidence_rounds[t] > episode["round"] for t in targets):
                    raise ValueError("verification_targets must reference existing, non-future checkable evidence")
    return data


def public_evidence(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "source": item["source"],
        "reliability": item["reliability"],
        "content": item["content"],
    }


def opaque_evidence_ids(
    scenario: dict[str, Any], *, seed: int | None, repetition: int
) -> tuple[dict[str, Any], dict[str, str]]:
    """Remove source-ID cues without changing content, truth or delivery timing.

    The mapping is evaluator metadata, never a policy input. This removes an
    obvious suffix cue; it does not make public narratives unseen test cases.
    """
    ids = {item["id"] for episode in scenario["episodes"]
           for evidence in episode["evidence"].values() for item in evidence}
    namespace = scenario.get("design", {}).get("evidence_namespace", scenario["id"])
    salt = f"{namespace}:{seed}:{repetition}:evidence-v1:"
    ordered = sorted(ids, key=lambda item: hashlib.sha256((salt + item).encode()).hexdigest())
    mapping = {old: f"E{index:03d}" for index, old in enumerate(ordered, 1)}
    pattern = re.compile(r"(?<![A-Za-z0-9_-])(?:" + "|".join(
        re.escape(item) for item in sorted(ids, key=len, reverse=True)
    ) + r")(?![A-Za-z0-9_-])")

    def replace(value: Any) -> Any:
        if isinstance(value, str):
            return pattern.sub(lambda match: mapping[match.group()], value)
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {mapping.get(key, key): replace(item) for key, item in value.items()}
        return value

    return replace(copy.deepcopy(scenario)), mapping


def disclosed_evidence(scenario: dict[str, Any], round_number: int) -> list[dict[str, Any]]:
    """Return cards explicitly made public by this point, never future disclosures."""
    ids = [key for episode in scenario["episodes"] if episode["round"] <= round_number
           for key in episode.get("public_disclosures", [])]
    cards = {item["id"]: item for episode in scenario["episodes"]
             for items in episode["evidence"].values() for item in items}
    return [cards[key] for key in ids]


def evidence_text(items: list[dict[str, Any]]) -> str:
    if not items:
        return "No new evidence."
    lines: list[str] = []
    for item in items:
        view = public_evidence(item)
        lines.extend(
            [
                f"[{view['id']}] {view['source']} | stated reliability: {view['reliability']}",
                view["content"],
                "",
            ]
        )
    return "\n".join(lines).strip()


@dataclass
class CrisisState:
    escalation: float
    civilian_harm: float
    economic_cost: float
    channel_trust: float

    @classmethod
    def from_scenario(cls, scenario: dict[str, Any]) -> "CrisisState":
        start = scenario["starting_state"]
        return cls(
            escalation=float(start["escalation"]),
            civilian_harm=float(start["civilian_harm"]),
            economic_cost=float(start["economic_cost"]),
            channel_trust=float(start["channel_trust"]),
        )

    def view(self) -> dict[str, float]:
        return {
            "escalation": round(self.escalation, 2),
            "civilian_harm": round(self.civilian_harm, 2),
            "economic_cost": round(self.economic_cost, 2),
            "channel_trust": round(self.channel_trust, 2),
        }


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))

