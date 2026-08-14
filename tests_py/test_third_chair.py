from __future__ import annotations

import json
import unittest
from pathlib import Path

from third_chair.analysis import summarize_records
from third_chair.client import ModelResponse
from third_chair.runner import ModelSeat, run_match
from third_chair.scenario import load_scenario
from third_chair.schema import parse_json_object, validate_mediator
from third_chair.tournament import build_schedule, estimate_calls


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "eval_data" / "scenarios"


def actor_intent(belief: int, posture: str, evidence_ids: list[str]) -> dict:
    return {
        "belief_opponent_responsible": belief,
        "posture": posture,
        "public_message": "We will keep our response tied to evidence and reversible options.",
        "private_reason": "The evidence remains incomplete and an early irreversible step could backfire.",
        "evidence_ids": evidence_ids,
    }


def actor_final(
    belief: int, posture: str, evidence_ids: list[str], *, accepts: bool
) -> dict:
    return {
        "belief_opponent_responsible": belief,
        "posture": posture,
        "accepts_intervention": accepts,
        "public_message": "We will use the hotline and continue checking the disputed evidence.",
        "evidence_ids": evidence_ids,
    }


class FakeClient:
    def __init__(self, model: str, outputs: list[dict]) -> None:
        self.model = model
        self.outputs = [json.dumps(item) for item in outputs]

    def chat(self, messages, *, temperature, max_tokens, seed):
        return ModelResponse(
            content=self.outputs.pop(0),
            returned_model=self.model,
            usage={"prompt_tokens": 1, "completion_tokens": 1},
            raw={},
        )


class ThirdChairTests(unittest.TestCase):
    def test_all_scenarios_are_three_round_truth_asymmetric_games(self) -> None:
        paths = sorted(SCENARIOS.glob("*.json"))
        self.assertEqual(len(paths), 3)
        truths = []
        for path in paths:
            scenario = load_scenario(path)
            self.assertEqual(scenario["rounds"], 3)
            self.assertEqual(scenario["intervention_budget"], 2)
            self.assertEqual(len(scenario["postures"]), 7)
            self.assertTrue(scenario["ground_truth"]["forged_evidence_ids"])
            truths.append(scenario["ground_truth"]["responsible_actor"])
        self.assertEqual(truths.count("nonstate"), 2)
        self.assertEqual(truths.count("state_b"), 1)

    def test_mediator_validation_requires_a_known_verification_target(self) -> None:
        value = {
            "intervene": True,
            "channel": "verify",
            "message": "Authenticate the document before either side acts on it.",
            "target_evidence_id": "G06-P",
            "diagnosis": "misinformation",
            "predicted_escalation": 72,
            "reason": "The document is carrying most of the escalation pressure.",
        }
        validate_mediator(value, known_ids={"G06-P"}, interventions_left=2)
        with self.assertRaisesRegex(ValueError, "known evidence ID"):
            validate_mediator(value, known_ids={"G01"}, interventions_left=2)

    def test_parse_json_accepts_fenced_output(self) -> None:
        value = parse_json_object('```json\n{"intervene": false}\n```')
        self.assertFalse(value["intervene"])

    def test_balanced_pilot_schedule_rotates_three_models_once_per_scenario(self) -> None:
        schedule = build_schedule(
            scenario_paths=sorted(SCENARIOS.glob("*.json")),
            labels=["alpha", "beta", "gamma"],
            rotation="balanced",
            modes=["active", "empty"],
            repetitions=1,
            seed=4100,
        )
        self.assertEqual(len(schedule), 18)
        self.assertEqual(estimate_calls(schedule), 243)
        for scenario_id in {item["scenario_id"] for item in schedule}:
            active = [
                item
                for item in schedule
                if item["scenario_id"] == scenario_id and item["mode"] == "active"
            ]
            self.assertEqual(
                {item["mediator"] for item in active}, {"alpha", "beta", "gamma"}
            )

    def test_runner_records_model_moves_and_delayed_verification(self) -> None:
        a_outputs = [
        actor_intent(20, "collect", ["G01"]),
        actor_final(20, "collect", ["G01"], accepts=True),
        actor_intent(72, "public_attribution", ["G06-P"]),
        actor_final(68, "private_demarch", ["G06-P"], accepts=True),
        actor_intent(12, "collect", ["G08", "G09"]),
        actor_final(10, "collect", ["G08", "G09"], accepts=False),
    ]
        b_outputs = [
        actor_intent(15, "harden_hotline", ["B01"]),
        actor_final(15, "harden_hotline", ["B01"], accepts=True),
        actor_intent(20, "private_demarch", ["B03"]),
        actor_final(20, "harden_hotline", ["B03"], accepts=True),
        actor_intent(10, "harden_hotline", ["B04"]),
        actor_final(10, "harden_hotline", ["B04"], accepts=False),
    ]
        mediator_outputs = [
        {
            "intervene": True,
            "channel": "verify",
            "message": "Confirm the grid log while both sides keep their next steps reversible.",
            "target_evidence_id": "G01",
            "diagnosis": "uncertainty",
            "predicted_escalation": 48,
            "reason": "The first round needs a shared factual floor.",
        },
        {
            "intervene": True,
            "channel": "verify",
            "message": "Authenticate the published intercept before anyone treats it as a basis for retaliation.",
            "target_evidence_id": "G06-P",
            "diagnosis": "misinformation",
            "predicted_escalation": 79,
            "reason": "The new document is driving an abrupt change in posture.",
        },
    ]
        record = run_match(
            scenario_path=SCENARIOS / "grid-vote.json",
            model_a=ModelSeat("alpha", FakeClient("provider/alpha", a_outputs)),
            model_b=ModelSeat("beta", FakeClient("provider/beta", b_outputs)),
            mediator_model=ModelSeat(
                "gamma", FakeClient("provider/gamma", mediator_outputs)
            ),
            mode="active",
            repetition=1,
            seed=100,
        )
        self.assertEqual(record["run_status"], "succeeded", record.get("error"))
        self.assertEqual(len(record["rounds"]), 3)
        self.assertEqual(record["scores"]["interventions_used"], 2)
        self.assertIn("G06-P", record["scores"]["verified_invalid_ids"])
        self.assertFalse(record["scores"]["false_peace"])

    def test_summary_pairs_active_and_empty_chair_matches(self) -> None:
        base = {
        "schema_version": "0.3.0",
        "run_status": "succeeded",
        "scenario_id": "grid-vote",
        "repetition": 1,
        "seed": 4100,
        "roles": {
            "a": {"label": "alpha", "requested_model": "provider/alpha"},
            "b": {"label": "beta", "requested_model": "provider/beta"},
            "mediator": {"label": "gamma", "requested_model": "provider/gamma"},
        },
        "rounds": [
            {
                "resolution": {"severity_a": 1, "severity_b": 1},
            }
        ],
    }
        active = base | {
        "match_id": "active",
        "mode": "active",
        "scores": {
            "crisis_cost": 120,
            "truth_score": 90,
            "false_peace": False,
            "critical_escalation": False,
            "interventions_used": 2,
        },
    }
        empty = base | {
        "match_id": "empty",
        "mode": "empty",
        "scores": {
            "crisis_cost": 160,
            "truth_score": 85,
            "false_peace": False,
            "critical_escalation": True,
            "interventions_used": 0,
        },
    }
        summary = summarize_records([active, empty])
        self.assertEqual(summary["complete_active_empty_pairs"], 1)
        self.assertEqual(summary["pairs"][0]["mediation_lift"], 40)
        self.assertTrue(summary["pairs"][0]["critical_escalation_prevented"])


if __name__ == "__main__":
    unittest.main()
