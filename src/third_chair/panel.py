"""Offline coverage contract for the prospective 24-condition, three-model panel."""

from pathlib import Path

from .provenance import fingerprint, source_digest
from .scenario import load_scenario

FAMILIES = ("archive-talks", "grid-vote", "pipeline-shutdown", "port-sanctions",
            "satellite-outage", "software-cascade")
CONDITIONS = {f"{family}-{truth}-{document}" for family in FAMILIES
              for truth in ("nonstate", "state_b") for document in ("forged", "genuine")}


def validate_panel_inputs(paths, labels, rotation, modes, repetitions, seed, order_seed,
                          fixed_a, fixed_b, policy, mediator):
    if (len(labels) != 3 or len(set(labels)) != 3 or rotation != "full"
            or sorted(modes) != ["active", "empty"] or fixed_a or fixed_b or mediator
            or policy != "llm"):
        raise ValueError("Complete panel requires three distinct models, full rotation, "
                         "both arms and LLM mediation without fixed roles")
    if (type(repetitions) is not int or repetitions < 1
            or type(seed) is not int or type(order_seed) is not int):
        raise ValueError("Complete panel requires positive repetitions and recorded integer seeds")
    scenarios = [load_scenario(path) for path in paths]
    if len(scenarios) != 24 or {s["id"] for s in scenarios} != CONDITIONS:
        raise ValueError("Complete panel requires all 24 distinct frozen condition IDs")
    for scenario in scenarios:
        family = scenario.get("design", {}).get("family_id")
        if family not in FAMILIES or not scenario["id"].startswith(family + "-"):
            raise ValueError("Condition family provenance mismatch")


def _rows(rows):
    return [dict(row, scenario_path=str(Path(row["scenario_path"]).resolve())) for row in rows]


def panel_contract(schedule):
    """Freeze a complete plan, including order and scenario hashes; no credentials."""
    if not schedule or any(r.get("coverage_design") != "factorial24-full-v1" for r in schedule):
        raise ValueError("Expected a complete-panel schedule")
    contract = {
        "design": "factorial24-full-v1",
        "scenario_paths": sorted({str(Path(r["scenario_path"]).resolve()) for r in schedule}),
        "labels": sorted({r[role] for r in schedule for role in ("a", "b", "mediator")}),
        "repetitions": max(r["repetition"] for r in schedule),
        "seed": min(r["seed"] for r in schedule),
        "order_seed": schedule[0]["order_seed"],
        "schedule_sha256": fingerprint(_rows(schedule)),
        "source_sha256": source_digest(),
    }
    validate_panel_schedule(schedule, contract)
    return contract


def validate_panel_schedule(schedule, contract):
    """Reject omissions, duplicates, drift and changed order before any dispatch.

    Keep this contract outside mutable outcome/resume lists. Validate the entire
    frozen schedule, then skip previously attempted IDs using existing journals.
    """
    from .tournament import build_schedule
    if not isinstance(contract, dict) or contract.get("design") != "factorial24-full-v1":
        raise ValueError("A frozen complete-panel coverage contract is required")
    if contract.get("source_sha256") != source_digest():
        raise ValueError("Complete-panel source provenance changed")
    expected = build_schedule(
        scenario_paths=contract["scenario_paths"], labels=contract["labels"],
        rotation="full", modes=["active", "empty"], repetitions=contract["repetitions"],
        seed=contract["seed"], order_seed=contract["order_seed"], complete_panel=True)
    if (fingerprint(_rows(expected)) != contract["schedule_sha256"]
            or fingerprint(_rows(schedule)) != contract["schedule_sha256"]):
        raise ValueError("Complete-panel coverage, order or frozen scenario provenance changed")
    return {"conditions": 24, "assignments": 6, "repetitions": contract["repetitions"],
            "matches": len(expected), "planned_pairs": len(expected) // 2,
            "schedule_sha256": contract["schedule_sha256"]}
