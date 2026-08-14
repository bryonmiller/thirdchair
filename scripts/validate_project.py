"""Dependency-free structural checks for the Third Chair release."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from third_chair.scenario import load_scenario  # noqa: E402
from third_chair.tournament import build_schedule, estimate_calls  # noqa: E402


SCENARIOS = ROOT / "eval_data" / "scenarios"
REQUIRED_DOCS = {
    "annotation_guide.md",
    "brief.md",
    "hosting_guide.md",
    "model_run_guide.md",
    "preregistration.md",
    "proposal.md",
    "protocol.md",
    "scenario_design_notes.md",
    "scoring.md",
    "submission_copy.md",
    "threat_model.md",
}
PUBLIC_TEXT = [
    ROOT / "README.md",
    ROOT / "CITATION.cff",
    *sorted((ROOT / "docs").glob("*.md")),
    *sorted((ROOT / "site").glob("*.*")),
    *sorted((ROOT / "app").glob("*.tsx")),
]
BANNED_PUBLIC_PHRASES = {
    "\u2013": "Unicode en dash",
    "\u2014": "Unicode em dash",
    "let's dive": "tutorial signposting",
    "showcase": "promotional AI phrasing",
    "pivotal": "inflated AI phrasing",
    "tapestry": "inflated AI phrasing",
    "in today's rapidly": "generic AI opening",
    "not just": "negative parallelism",
    "isn't just": "negative parallelism",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_scenario(path: Path) -> str:
    scenario = load_scenario(path)
    label = scenario["id"]
    require(int(scenario["rounds"]) == 3, f"{label}: expected three rounds")
    require(int(scenario["intervention_budget"]) == 2, f"{label}: expected two interventions")

    postures = scenario["postures"]
    require(len(postures) == 7, f"{label}: expected seven postures")
    require(
        [int(item["severity"]) for item in postures] == list(range(7)),
        f"{label}: posture severity must be 0 through 6",
    )

    evidence_ids: set[str] = set()
    for episode in scenario["episodes"]:
        require(
            set(episode["evidence"]) == {"a", "b", "mediator"},
            f"{label}: each round needs all three evidence channels",
        )
        for seat_items in episode["evidence"].values():
            for item in seat_items:
                require(item["id"] not in evidence_ids, f"{label}: duplicate evidence ID")
                evidence_ids.add(item["id"])
                require(isinstance(item["valid"], bool), f"{label}: evidence validity missing")

    truth = scenario["ground_truth"]
    forged = set(truth["forged_evidence_ids"])
    decisive = set(truth["decisive_evidence_ids"])
    require(forged <= evidence_ids, f"{label}: forged item is not delivered")
    require(decisive <= evidence_ids, f"{label}: decisive evidence is not delivered")
    require(
        forged <= set(scenario["verification_results"]),
        f"{label}: forged item cannot be verified",
    )
    for item_id in forged:
        require(
            scenario["verification_results"][item_id]["valid"] is False,
            f"{label}: forged item verifies as valid",
        )
    return label


def validate_schemas() -> None:
    paths = sorted((ROOT / "eval_data" / "schemas").glob("*.schema.json"))
    require(len(paths) == 3, "Expected three response schemas")
    for path in paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        require(schema.get("additionalProperties") is False, f"{path.name}: extra fields allowed")


def validate_submission() -> None:
    submission = (ROOT / "docs" / "submission_copy.md").read_text(encoding="utf-8")
    abstract = submission.split("## Abstract\n\n", 1)[1].split("\n\n## Microsite", 1)[0]
    require(len(abstract.split()) == 150, "Submission abstract must be exactly 150 words")
    require("Yes, part time" in submission, "Work-interest answer changed unexpectedly")


def validate_public_text() -> None:
    for path in PUBLIC_TEXT:
        if not path.exists() or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        lowered = content.lower()
        for phrase, label in BANNED_PUBLIC_PHRASES.items():
            require(phrase not in lowered, f"{label} in {path}")


def validate_schedule(paths: list[Path]) -> None:
    schedule = build_schedule(
        scenario_paths=paths,
        labels=["model-a", "model-b", "model-c"],
        rotation="balanced",
        modes=["active", "empty"],
        repetitions=1,
        seed=4100,
    )
    require(len(schedule) == 18, "Balanced pilot must contain 18 matches")
    require(estimate_calls(schedule) == 243, "Balanced pilot call estimate changed")


def main() -> None:
    paths = sorted(SCENARIOS.glob("*.json"))
    require(len(paths) == 3, "Expected exactly three scenarios")
    ids = [validate_scenario(path) for path in paths]
    require(len(ids) == len(set(ids)), "Scenario IDs must be unique")

    present_docs = {path.name for path in (ROOT / "docs").glob("*.md")}
    require(REQUIRED_DOCS <= present_docs, "Required documentation is incomplete")
    validate_schemas()
    validate_submission()
    validate_schedule(paths)
    validate_public_text()
    print("Third Chair structural validation passed")


if __name__ == "__main__":
    main()

