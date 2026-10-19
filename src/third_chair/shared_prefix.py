"""Versioned final-message forks, with durable prefixes and single-count usage."""

from __future__ import annotations

import copy
import random
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import __version__
from .analysis import _identity_issues
from .measurement import record_measures
from .policies import DELAYED_MESSAGE, SHARED_PREFIX, SHARED_PROTOCOL_VERSION
from .provenance import fingerprint, pair_identity, run_manifest
from .runner import ModelSeat, run_match, validate_prefix_checkpoint
from .scenario import load_scenario
from .tournament import _append_jsonl, _read_jsonl, build_schedule

BRANCHES = {"message", "no-message"}
PROTOCOL_VERSION = SHARED_PROTOCOL_VERSION


def build_shared_schedule(
    *, scenario_paths: list[Path], labels: list[str], actor_a: str, actor_b: str,
    mediator: str, repetitions: int, seed: int | None, order_seed: int,
) -> list[dict[str, Any]]:
    if order_seed is None:
        raise ValueError("Shared-prefix execution requires an explicit order seed")
    schedule = build_schedule(
        scenario_paths=scenario_paths, labels=labels, rotation="balanced", modes=["active"],
        repetitions=repetitions, seed=seed, fixed_a=actor_a, fixed_b=actor_b,
        mediator_label=mediator, mediator_policy=DELAYED_MESSAGE, order_seed=order_seed,
    )
    rng = random.Random(order_seed)
    for item in schedule:
        branches = ["message", "no-message"]
        rng.shuffle(branches)
        item.update(mediator_policy=SHARED_PREFIX, branch_order=branches,
                    protocol_version=PROTOCOL_VERSION)
    return schedule


def shared_manifest(scenario: dict[str, Any], seats: dict[str, ModelSeat],
                    order_seed: int) -> dict[str, Any]:
    return run_manifest(scenario, seats, order_seed=order_seed, mediator_policy=SHARED_PREFIX,
                        control_design="shared_prefix_final_message")


def _validate_records(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Validate parent links even when analyzing on a later source revision."""
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        identifier = record.get("match_id")
        kind = record.get("record_type")
        if (not identifier or identifier in indexed or kind not in
                {"shared_prefix_prefix", "shared_prefix_branch"}):
            raise ValueError("Missing, duplicate, or non-shared-prefix record")
        if record.get("protocol_version") != PROTOCOL_VERSION:
            raise ValueError("Unknown shared-prefix protocol version")
        manifest = record.get("manifest", {})
        if (manifest.get("control_design") != "shared_prefix_final_message"
                or manifest.get("mediator_policy") != SHARED_PREFIX
                or manifest.get("protocol_version") != PROTOCOL_VERSION
                or not manifest.get("protocol_sha256")
                or manifest.get("configuration_id") != fingerprint(
                    {k: v for k, v in manifest.items() if k != "configuration_id"})):
            raise ValueError("Invalid shared-prefix manifest")
        pair_id = pair_identity(manifest, record["repetition"], record["seed"])
        branch = record.get("branch")
        suffix = "prefix" if kind == "shared_prefix_prefix" else branch
        if (record.get("prefix_id") != f"{pair_id}__prefix"
                or identifier != f"{pair_id}__{suffix}"
                or record.get("branch_order") not in
                (["message", "no-message"], ["no-message", "message"])):
            raise ValueError("Invalid shared-prefix identity or branch order")
        if kind == "shared_prefix_prefix":
            if branch is not None or record.get("run_status") not in {"prefix_ready", "failed"}:
                raise ValueError("Invalid prefix status")
            if record["run_status"] == "prefix_ready":
                validate_prefix_checkpoint(record, manifest, record["repetition"], record["seed"])
        else:
            if branch not in BRANCHES or record.get("run_status") not in {"succeeded", "failed"}:
                raise ValueError("Invalid continuation status")
            parent = indexed.get(record["prefix_id"])
            if (not parent or parent["run_status"] != "prefix_ready"
                    or record["manifest"] != parent["manifest"]
                    or record["checkpoint_sha256"] != parent["checkpoint_sha256"]
                    or record["branch_order"] != parent["branch_order"]):
                raise ValueError("Continuation has no compatible ready parent checkpoint")
            _validate_continuation_prefix(parent, record)
        indexed[identifier] = record
    return indexed


def _validate_continuation_prefix(parent: dict[str, Any], branch: dict[str, Any]) -> None:
    expected = copy.deepcopy(parent["checkpoint"]["rounds"])
    for row in expected:
        row["attempts"] = {"a": [], "b": [], "mediator": []}
    if branch["rounds"][:2] != expected:
        raise ValueError("Continuation history differs from its shared prefix")
    final = branch["rounds"][2] if len(branch["rounds"]) == 3 else branch["partial_round"]
    checkpoint = parent["checkpoint"]
    if (final.get("intents") != {"a": checkpoint["intent_a"], "b": checkpoint["intent_b"]}
            or final.get("mediator_observation") != checkpoint["observation"]):
        raise ValueError("Continuation intentions/observations differ from its prefix")
    if branch["run_status"] == "succeeded" and (
        len(branch["rounds"]) != 3
        or final["delivered_verifications"] != checkpoint["delivered_now"]
        or final["public_event"] != checkpoint["observation"]["public_event"]
    ):
        raise ValueError("Continuation verification/event differs from its prefix")
    # Prefix events are referenced, never embedded in continuation cost ledgers.
    if any(not event["stage"].startswith("round_3_")
           or "_intent_" in event["stage"] for event in branch["events"]):
        raise ValueError("Continuation contains a repeated prefix request")


def run_shared_schedule(
    *, schedule: list[dict[str, Any]], model_seats: dict[str, ModelSeat], output: str | Path,
) -> None:
    if not schedule:
        raise ValueError("Shared-prefix schedule is empty")
    output = Path(output)
    journal = output.with_suffix(output.suffix + ".events.jsonl")
    existing = _read_jsonl(output)
    indexed = _validate_records(existing)
    bound: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    expected_records: dict[str, tuple[dict[str, Any], list[str]]] = {}
    for item in schedule:
        if (item.get("mediator_policy") != SHARED_PREFIX
                or item.get("protocol_version") != PROTOCOL_VERSION
                or item.get("order_seed") is None
                or item.get("branch_order") not in
                (["message", "no-message"], ["no-message", "message"])):
            raise ValueError("Invalid shared-prefix schedule")
        scenario = load_scenario(item["scenario_path"])
        if fingerprint(scenario) != item["scenario_sha256"]:
            raise ValueError("Scenario changed after planning")
        seats = {role: model_seats[item[role]] for role in ("a", "b", "mediator")}
        manifest = shared_manifest(scenario, seats, item["order_seed"])
        unit = pair_identity(manifest, item["repetition"], item["seed"])
        for suffix in ("prefix", "message", "no-message"):
            identifier = f"{unit}__{suffix}"
            if identifier in expected_records:
                raise ValueError("Duplicate shared-prefix unit")
            expected_records[identifier] = (manifest, item["branch_order"])
        bound.append((item, manifest, unit))
    for record in existing:
        expected = expected_records.get(record["match_id"])
        if expected != (record["manifest"], record["branch_order"]):
            raise ValueError("Source, scenario, schedule, or configuration changed; use a new output")
    unfinished = {event["match_id"] for event in _read_jsonl(journal)} - indexed.keys()
    if unfinished:
        raise ValueError("Interrupted calls exist; preserve the journal and use a new output/repetition")

    output.parent.mkdir(parents=True, exist_ok=True)
    for item, manifest, unit in bound:
        common = dict(scenario_path=item["scenario_path"],
                      model_a=model_seats[item["a"]], model_b=model_seats[item["b"]],
                      mediator_model=model_seats[item["mediator"]], mode="active",
                      repetition=item["repetition"], seed=item["seed"],
                      mediator_policy=SHARED_PREFIX, order_seed=item["order_seed"],
                      event_sink=lambda event: _append_jsonl(journal, event))

        def persist(record: dict[str, Any]) -> None:
            if record["manifest"] != manifest:
                raise RuntimeError("Configuration changed during execution; preserve journal")
            record.update(protocol_version=PROTOCOL_VERSION, branch_order=item["branch_order"])
            _validate_records([*indexed.values(), record])
            _append_jsonl(output, record)
            indexed[record["match_id"]] = record

        prefix_id = f"{unit}__prefix"
        if prefix_id not in indexed:
            persist(run_match(**common))
        prefix = indexed[prefix_id]
        if prefix["run_status"] == "failed":
            continue
        for branch in item["branch_order"]:
            if f"{unit}__{branch}" not in indexed:
                persist(run_match(**common, prefix_checkpoint=prefix, shared_branch=branch))


def event_cost(record: dict[str, Any]) -> dict[str, Any]:
    """Only this record's actual completion events, including invalid responses."""
    total = Decimal(0)
    missing = calls = 0
    for event in record["events"]:
        if event.get("event_type") in {"protocol_action", "scripted_policy"}:
            continue
        if event.get("status") == "started":
            continue
        calls += 1
        cost = (event.get("usage") or {}).get("cost")
        if cost is None:
            missing += 1
        else:
            total += Decimal(str(cost))
    return {"recorded_cost_usd": float(total), "requests": calls,
            "requests_without_cost": missing}


def summarize_shared_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    indexed = _validate_records(records)
    prefixes = [r for r in records if r["record_type"] == "shared_prefix_prefix"]
    comparisons = []
    for prefix in prefixes:
        branches = {b: indexed.get(prefix["prefix_id"].removesuffix("prefix") + b)
                    for b in sorted(BRANCHES)}
        result = {"prefix_id": prefix["prefix_id"], "scenario_id": prefix["scenario_id"],
                  "checkpoint_sha256": prefix.get("checkpoint_sha256"),
                  "status": "incomplete", "issues": [], "cost_reduction": None,
                  "attribution_brier_improvement": None,
                  "costs": {"prefix": event_cost(prefix), **{
                      b: event_cost(r) if r else None for b, r in branches.items()}},
                  "branches": {b: {"status": r["run_status"] if r else "missing"}
                               for b, r in branches.items()}}
        for b, record in branches.items():
            if record and record["run_status"] == "succeeded":
                # The control has no mediator completion, but both actors must be eligible.
                identity_record = record if b == "message" else record | {"mode": "empty"}
                result["issues"].extend(f"{b}: {x}" for x in _identity_issues(identity_record))
                measures = record_measures(record)
                final = record["rounds"][-1]["final_moves"]["a"]
                result["branches"][b].update(
                    final_posture_a=final["posture"],
                    final_reported_probability=final["belief_opponent_responsible"] / 100,
                    modeled_cost=record["scores"]["crisis_cost"],
                    attribution_brier=record["scores"]["attribution_brier"],
                    interventions_used=record["scores"]["interventions_used"],
                    false_public_attribution=measures["false_public_attribution_final"],
                    false_public_attribution_applicable=measures["false_public_attribution_applicable"],
                    wrong_target_action_any=measures["wrong_target_action_any"],
                    false_peace_applicable=measures["legacy_false_peace_applicable"],
                    legacy_false_peace=record["scores"]["false_peace"]
                        if measures["legacy_false_peace_applicable"] else None)
        message, control = branches["message"], branches["no-message"]
        if all(r and r["run_status"] == "succeeded" for r in (message, control)):
            for key in ("returned_models", "returned_providers"):
                for seat in ("a", "b"):
                    if message[key][seat] != control[key][seat]:
                        result["issues"].append(f"Actor {seat} differs across branches: {key}")
            if not result["issues"]:
                result.update(status="complete", first_two_rounds_cost_difference=0.0,
                              pre_message_probability_difference=0.0,
                              cost_reduction=round(control["scores"]["crisis_cost"] -
                                                   message["scores"]["crisis_cost"], 6),
                              attribution_brier_improvement=round(
                                  control["scores"]["attribution_brier"] -
                                  message["scores"]["attribution_brier"], 6))
            else:
                result["status"] = "ineligible"
        comparisons.append(result)
    costs = [event_cost(r) for r in records]
    branches = [r for r in records if r["record_type"] == "shared_prefix_branch"]
    return {
        "schema_version": __version__, "protocol_version": PROTOCOL_VERSION,
        "attempted_units": len(prefixes),
        "ready_prefixes": sum(r["run_status"] == "prefix_ready" for r in prefixes),
        "failed_prefixes": sum(r["run_status"] == "failed" for r in prefixes),
        "successful_branches": sum(r["run_status"] == "succeeded" for r in branches),
        "failed_branches": sum(r["run_status"] == "failed" for r in branches),
        "missing_branches": 2 * sum(r["run_status"] == "prefix_ready" for r in prefixes) - len(branches),
        "complete_comparisons": sum(c["status"] == "complete" for c in comparisons),
        "recorded_cost_usd": float(sum((Decimal(str(c["recorded_cost_usd"])) for c in costs), Decimal(0))),
        "requests": sum(c["requests"] for c in costs),
        "requests_without_cost": sum(c["requests_without_cost"] for c in costs),
        "comparisons": comparisons,
        "warnings": ["Conditional final-message contrasts at fixed sampled prefixes.",
                     "Branches share a history and are not independent crisis families.",
                     "Modeled cost and attribution are separate; accountability remains incomplete.",
                     "Recorded costs exclude duplicated journals; missing usage is not zero cost."],
    }
