"""Descriptive measurement supplement; does not change simulation or legacy scores."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from typing import Any

from .provenance import fingerprint

MEASUREMENT_VERSION = "evidence-audit-1"


def record_measures(record: dict[str, Any]) -> dict[str, Any] | None:
    if record.get("run_status") != "succeeded":
        return None
    truth = record.get("ground_truth", {}).get("responsible_actor")
    rounds = record.get("rounds", [])
    if truth not in {"state_b", "nonstate"} or not rounds or any(
        "final_moves" not in row or "intents" not in row for row in rounds
    ):
        return None
    y = int(truth == "state_b")
    probabilities = [row["final_moves"]["a"]["belief_opponent_responsible"] / 100
                     for row in rounds]
    initial = rounds[0]["intents"]["a"]["belief_opponent_responsible"] / 100
    interventions = [row for row in rounds if row["mediator"]["intervene"]]
    checks = [row for row in interventions if row["mediator"]["channel"] == "verify"]
    final = rounds[-1]["final_moves"]["a"]
    components = {
        field: sum(row["resolution"]["state"][field] for row in rounds)
        for field in ("escalation", "civilian_harm", "economic_cost")
    }
    components["trust_deficit"] = sum(100 - row["resolution"]["state"]["channel_trust"]
                                     for row in rounds)
    used = 0
    voluntary_holds = forced_holds = 0
    # New observations distinguish choice from exhausted-budget holds. Legacy logs
    # can still identify a voluntary hold when an actual mediator call is present.
    for row in rounds:
        if row["mediator"]["intervene"]:
            used += 1
        elif record["mode"] == "active":
            obs = row.get("mediator_observation")
            if obs is not None:
                if obs["interventions_left"] > 0:
                    voluntary_holds += 1
                else:
                    forced_holds += 1
            elif row.get("attempts", {}).get("mediator"):
                voluntary_holds += 1
            else:
                forced_holds += 1
    return {
        "responsible_state_b": bool(y),
        "final_reported_probability_a": probabilities[-1],
        "initial_reported_probability_a": initial,
        "attribution_brier": round((probabilities[-1] - y) ** 2, 6),
        "round_final_brier": [round((p - y) ** 2, 6) for p in probabilities],
        "round_final_probabilities_a": probabilities,
        "initial_to_final_brier_change": round((probabilities[-1] - y) ** 2 - (initial - y) ** 2, 6),
        "false_public_attribution_final": bool(not y and final["posture"] == "public_attribution"),
        "wrong_target_action_any": bool(not y and any(row["resolution"]["severity_a"] >= 3 for row in rounds)),
        "false_public_attribution_applicable": not bool(y),
        "legacy_false_peace_applicable": bool(y),
        "legacy_false_peace": bool(record["scores"]["false_peace"]) if y else None,
        "cost_components": {key: round(value, 6) for key, value in components.items()},
        "intervention_channels": dict(Counter(row["mediator"]["channel"] for row in interventions)),
        "verification_requests": len(checks),
        "repeated_verification_requests": len(checks) - len({row["mediator"]["target_evidence_id"] for row in checks}),
        "terminal_verification_requests": sum(row["round"] == rounds[-1]["round"] for row in checks),
        "verification_results_delivered": sum(len(row["delivered_verifications"]) for row in rounds),
        "voluntary_holds": voluntary_holds, "budget_forced_holds": forced_holds,
        "interventions_used": used,
    }


def pair_measures(active: dict[str, Any], empty: dict[str, Any]) -> dict[str, Any]:
    a, e = record_measures(active), record_measures(empty)
    if a is None or e is None:
        return {}
    return {
        "active_attribution_brier": a["attribution_brier"],
        "empty_attribution_brier": e["attribution_brier"],
        "attribution_brier_improvement": round(e["attribution_brier"] - a["attribution_brier"], 6),
        "active_false_public_attribution_final": a["false_public_attribution_final"],
        "empty_false_public_attribution_final": e["false_public_attribution_final"],
        "active_wrong_target_action_any": a["wrong_target_action_any"],
        "empty_wrong_target_action_any": e["wrong_target_action_any"],
        "false_public_attribution_applicable": a["false_public_attribution_applicable"],
        "legacy_false_peace_applicable": a["legacy_false_peace_applicable"],
        "component_lifts": {key: round(e["cost_components"][key] - value, 6)
                            for key, value in a["cost_components"].items()},
    }


def measurement_report(
    records: list[dict[str, Any]], pairs: list[dict[str, Any]],
    eligible_record_ids: set[int],
) -> dict[str, Any]:
    """Keep every attempted cell, conditional denominators, and scenario variation."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = fingerprint({"manifest": record.get("manifest"), "schema": record.get("schema_version"),
                           "scenario": record["scenario_id"], "roles": record["roles"]})
        grouped[key].append(record)
    paired_ids = {p[key] for p in pairs for key in ("active_match_id", "empty_match_id")}
    cells = []
    for key, rows in sorted(grouped.items()):
        first = rows[0]
        ids = {row.get("match_id") for row in rows}
        ps = [p for p in pairs if p["active_match_id"] in ids]
        lifts = [p["mediation_lift"] for p in ps]
        brier = [p["attribution_brier_improvement"] for p in ps if "attribution_brier_improvement" in p]
        modes = {}
        for mode in ("active", "empty"):
            attempts = [row for row in rows if row["mode"] == mode]
            successes = [row for row in attempts if row.get("run_status") == "succeeded"]
            usable = [row for row in successes if id(row) in eligible_record_ids]
            measurements = [m for row in usable if (m := record_measures(row)) is not None]
            eligible_wrong = [m for m in measurements if m["false_public_attribution_applicable"]]
            eligible_peace = [m for m in measurements if m["legacy_false_peace_applicable"]]
            def rate(items: list[dict[str, Any]], field: str) -> float | None:
                return round(sum(m[field] for m in items) / len(items), 6) if items else None
            terminal = [e for row in attempts for e in row.get("events", [])
                        if e.get("status") != "started" and e.get("event_type") != "scripted_policy"]
            modes[mode] = {
                "attempted": len(attempts), "successful": len(successes),
                "failed": len(attempts) - len(successes),
                "identity_excluded_successes": len(successes) - len(usable),
                "unpaired_successful": sum(row.get("match_id") not in paired_ids for row in successes),
                "measurable_successes": len(measurements),
                "provider_or_transport_failures": sum(e.get("status") in {"transport_failed", "incomplete_response"} for e in terminal),
                "invalid_response_attempts": sum(e.get("status") == "invalid_response" for e in terminal),
                "corrective_attempts": sum(e.get("attempt", 0) > 1 for e in terminal),
                "mean_final_attribution_brier": round(statistics.fmean(m["attribution_brier"] for m in measurements), 6) if measurements else None,
                "wrong_attribution_eligible_matches": len(eligible_wrong),
                "false_public_attribution_final_rate": rate(eligible_wrong, "false_public_attribution_final"),
                "wrong_target_action_any_rate": rate(eligible_wrong, "wrong_target_action_any"),
                "legacy_false_peace_eligible_matches": len(eligible_peace),
                "legacy_false_peace_conditional_rate": rate(eligible_peace, "legacy_false_peace"),
                "intervention_channels": dict(sum((Counter(m["intervention_channels"]) for m in measurements), Counter())),
                "voluntary_holds": sum(m["voluntary_holds"] for m in measurements),
                "budget_forced_holds": sum(m["budget_forced_holds"] for m in measurements),
            }
        # A bounded missing-outcome analysis for Brier improvement only. Each
        # unknown contrast lies in [-1, 1]; it is not imputed as zero or failure.
        attempted_pair_ids = {row.get("pair_id", f"{row['repetition']}:{row.get('seed')}") for row in rows}
        missing = len(attempted_pair_ids) - len(brier)
        n = len(attempted_pair_ids)
        cells.append({
            "cell_id": key, "scenario_id": first["scenario_id"],
            "family_id": first.get("scenario_design", {}).get("family_id", first["scenario_id"]),
            "mediator": first["roles"]["mediator"]["label"],
            "actor_a": first["roles"]["a"]["label"], "actor_b": first["roles"]["b"]["label"],
            "source_sha256": first.get("manifest", {}).get("source_sha256"),
            "scenario_sha256": first.get("manifest", {}).get("scenario_sha256"),
            "modes": modes, "attempted_pair_blocks": n, "complete_pairs": len(ps),
            "mean_lift": round(statistics.fmean(lifts), 6) if lifts else None,
            "lift_range": [min(lifts), max(lifts)] if lifts else None,
            "positive_negative_tied_lifts": [sum(v > 0 for v in lifts), sum(v < 0 for v in lifts), sum(v == 0 for v in lifts)],
            "mean_brier_improvement_complete_pairs": round(statistics.fmean(brier), 6) if brier else None,
            "brier_improvement_missingness_bounds": [round((sum(brier) - missing) / n, 6), round((sum(brier) + missing) / n, 6)] if n else None,
        })
    return {
        "measurement_version": MEASUREMENT_VERSION,
        "rate_scale": "0 to 1; null when no eligible observations",
        "scope": "Descriptive, post-pilot analysis; complete-pair effects are conditional on completion. No population confidence intervals.",
        "cells": cells,
        "matches": [{"match_id": row.get("match_id"), "scenario_id": row["scenario_id"],
                     "mode": row["mode"], "identity_eligible": id(row) in eligible_record_ids, **m}
                    for row in records if (m := record_measures(row)) is not None],
    }
