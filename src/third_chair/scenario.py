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
    salt = f"{scenario['id']}:{seed}:{repetition}:evidence-v1:"
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

