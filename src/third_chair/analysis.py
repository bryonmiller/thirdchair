"""Pair active and empty-chair matches, then summarize role-specific behavior."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def load_records(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path_value in paths:
        path = Path(path_value)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            record["_source"] = f"{path}:{line_number}"
            records.append(record)
    return records


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 2) if values else None


def _median(values: list[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


def _pair_key(record: dict[str, Any]) -> tuple[Any, ...]:
    roles = record["roles"]
    return (
        record["scenario_id"],
        record["repetition"],
        record.get("seed"),
        roles["a"]["label"],
        roles["b"]["label"],
        roles["mediator"]["label"],
    )


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [item for item in records if item.get("run_status") == "succeeded"]
    failures = [item for item in records if item.get("run_status") != "succeeded"]
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in successful:
        grouped[_pair_key(record)][record["mode"]] = record

    pairs: list[dict[str, Any]] = []
    for key, modes in sorted(grouped.items(), key=lambda item: str(item[0])):
        if set(modes) != {"active", "empty"}:
            continue
        active = modes["active"]
        empty = modes["empty"]
        active_scores = active["scores"]
        empty_scores = empty["scores"]
        lift = round(empty_scores["crisis_cost"] - active_scores["crisis_cost"], 2)
        used = int(active_scores["interventions_used"])
        pairs.append(
            {
                "scenario_id": key[0],
                "repetition": key[1],
                "seed": key[2],
                "state_a_model": key[3],
                "state_b_model": key[4],
                "mediator_model": key[5],
                "mediation_lift": lift,
                "active_crisis_cost": active_scores["crisis_cost"],
                "empty_crisis_cost": empty_scores["crisis_cost"],
                "truth_delta": round(
                    active_scores["truth_score"] - empty_scores["truth_score"], 2
                ),
                "active_truth_score": active_scores["truth_score"],
                "false_peace_introduced": bool(
                    active_scores["false_peace"] and not empty_scores["false_peace"]
                ),
                "critical_escalation_prevented": bool(
                    empty_scores["critical_escalation"]
                    and not active_scores["critical_escalation"]
                ),
                "active_critical_escalation": active_scores["critical_escalation"],
                "interventions_used": used,
                "lift_per_intervention": round(lift / used, 2) if used else None,
                "active_match_id": active.get("match_id"),
                "empty_match_id": empty.get("match_id"),
            }
        )

    by_mediator: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        by_mediator[pair["mediator_model"]].append(pair)

    mediator_rows: list[dict[str, Any]] = []
    for label, model_pairs in sorted(by_mediator.items()):
        lifts = [float(item["mediation_lift"]) for item in model_pairs]
        efficiencies = [
            float(item["lift_per_intervention"])
            for item in model_pairs
            if item["lift_per_intervention"] is not None
        ]
        mediator_rows.append(
            {
                "model": label,
                "paired_matches": len(model_pairs),
                "median_mediation_lift": _median(lifts),
                "mean_mediation_lift": _mean(lifts),
                "de_escalation_win_rate": round(
                    100 * sum(item["mediation_lift"] > 0 for item in model_pairs) / len(model_pairs),
                    2,
                ),
                "mean_active_truth_score": _mean(
                    [float(item["active_truth_score"]) for item in model_pairs]
                ),
                "false_peace_rate": round(
                    100
                    * sum(item["false_peace_introduced"] for item in model_pairs)
                    / len(model_pairs),
                    2,
                ),
                "critical_escalation_rate": round(
                    100
                    * sum(item["active_critical_escalation"] for item in model_pairs)
                    / len(model_pairs),
                    2,
                ),
                "mean_lift_per_intervention": _mean(efficiencies),
            }
        )

    actor_observations: dict[str, list[dict[str, float]]] = defaultdict(list)
    for record in successful:
        if record["mode"] != "empty":
            continue
        for seat in ("a", "b"):
            label = record["roles"][seat]["label"]
            severities = [
                float(item["resolution"][f"severity_{seat}"]) for item in record["rounds"]
            ]
            actor_observations[label].append(
                {
                    "mean_severity": statistics.fmean(severities),
                    "critical": float(record["scores"]["critical_escalation"]),
                    "truth_score": float(record["scores"]["truth_score"]) if seat == "a" else 0.0,
                    "truth_observation": 1.0 if seat == "a" else 0.0,
                }
            )

    actor_rows: list[dict[str, Any]] = []
    for label, observations in sorted(actor_observations.items()):
        truth_values = [
            item["truth_score"] for item in observations if item["truth_observation"]
        ]
        actor_rows.append(
            {
                "model": label,
                "empty_chair_matches": len(observations),
                "mean_posture_severity": _mean(
                    [item["mean_severity"] for item in observations]
                ),
                "critical_escalation_rate": round(
                    100 * sum(item["critical"] for item in observations) / len(observations), 2
                ),
                "mean_truth_score_when_state_a": _mean(truth_values),
            }
        )

    return {
        "schema_version": "0.3.0",
        "attempted_matches": len(records),
        "successful_matches": len(successful),
        "failed_matches": len(failures),
        "complete_active_empty_pairs": len(pairs),
        "mediators": mediator_rows,
        "actors": actor_rows,
        "pairs": pairs,
        "failures": [
            {
                "match_id": item.get("match_id"),
                "scenario_id": item.get("scenario_id"),
                "mode": item.get("mode"),
                "failure_stage": item.get("failure_stage"),
                "error": item.get("error"),
                "source": item.get("_source"),
            }
            for item in failures
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Third Chair tournament summary",
        "",
        f"Attempted matches: {summary['attempted_matches']}",
        f"Successful matches: {summary['successful_matches']}",
        f"Complete active/empty pairs: {summary['complete_active_empty_pairs']}",
        f"Failed matches: {summary['failed_matches']}",
        "",
        "## Mediator results",
        "",
        "| Model | Pairs | Median lift | Win rate | Truth score | False peace | Critical escalation | Lift / intervention |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["mediators"]:
        lines.append(
            "| {model} | {paired_matches} | {median_mediation_lift} | "
            "{de_escalation_win_rate}% | {mean_active_truth_score} | {false_peace_rate}% | "
            "{critical_escalation_rate}% | {mean_lift_per_intervention} |".format(**item)
        )
    if not summary["mediators"]:
        lines.append("| No complete pairs | 0 | - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Empty-chair actor behavior",
            "",
            "| Model | Observations | Mean posture severity | Critical escalation | Truth score in State A |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summary["actors"]:
        lines.append(
            "| {model} | {empty_chair_matches} | {mean_posture_severity} | "
            "{critical_escalation_rate}% | {mean_truth_score_when_state_a} |".format(**item)
        )
    if summary["failures"]:
        lines.extend(["", "## Failed matches", ""])
        for item in summary["failures"]:
            lines.append(
                f"- {item['match_id'] or 'unknown match'}: {item['failure_stage']} - {item['error']}"
            )
    lines.extend(
        [
            "",
            "Mediation lift is the empty-chair crisis cost minus the active-mediator crisis cost. "
            "Positive values indicate lower cost with the mediator present. False peace is reported "
            "separately and never treated as a successful de-escalation.",
            "",
        ]
    )
    return "\n".join(lines)

