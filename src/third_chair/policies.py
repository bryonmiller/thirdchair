"""Small, auditable mediator baselines operating on authorized observations only."""

from __future__ import annotations

from typing import Any


POLICY_NAME = "linked-verification"
POLICY_LABEL = "rule-linked-verification"


class LinkedVerificationPolicy:
    """A development comparator, not an optimal planner or learned policy."""

    model = "scripted/linked-verification-v1"

    def decide(self, observation: dict[str, Any]) -> dict[str, Any]:
        decision = {
            "intervene": False, "channel": "hold", "message": "",
            "target_evidence_id": None, "diagnosis": "none",
            "predicted_escalation": round(observation["state"]["escalation"]),
            "reason": "No useful, unfinished check within the remaining horizon.",
        }
        if (observation["interventions_left"] <= 0
                or observation["round"] >= observation["total_rounds"]):
            return decision
        checked = {item["target_id"] for item in observation["completed_checks"]}
        available = set(observation["verifiable_ids"]) - checked
        linked = {target for item in observation["neutral_evidence"]
                  for target in item.get("verification_targets", [])} & available
        a = observation["intents"]["a"]["evidence_stances"]
        b = observation["intents"]["b"]["evidence_stances"]
        disputed = {key for key in a.keys() & b.keys()
                    if {a[key], b[key]} == {"support", "reject"}} & available
        candidates = linked or disputed or available
        if candidates:
            target = min(candidates)
            decision.update(
                intervene=True, channel="verify", target_evidence_id=target,
                diagnosis="uncertainty",
                message=f"Please independently check evidence {target}; the result is pending.",
                reason="Prefer an available neutral link, then a disputed citation, "
                       "then an unchecked ID. Break ties by opaque ID.",
            )
        return decision

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Scripted mediators must use the authorized structured observation")
