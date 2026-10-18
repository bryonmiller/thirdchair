"""Information interventions, non-oracle baselines, and measurement denominators."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from third_chair.analysis import summarize_records
from third_chair.cli import _scenario_paths, build_parser
from third_chair.measurement import pair_measures, record_measures
from third_chair.policies import LinkedVerificationPolicy, POLICY_LABEL
from third_chair.provenance import run_manifest
from third_chair.runner import ModelSeat, _mediator_observation, _mediator_prompt, run_match
from third_chair.scenario import CrisisState, disclosed_evidence, load_scenario, opaque_evidence_ids
from third_chair.tournament import build_schedule, estimate_calls, run_schedule
from test_audit_regressions import SCENARIO, execute, seats
from test_third_chair import actor_final, actor_intent

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "eval_data/scenarios/port-sanctions.json"
DISCLOSED = ROOT / "eval_data/variants/port-sanctions-disclosed.json"


class MethodologyTests(unittest.TestCase):
    def test_port_variant_changes_only_disclosure_and_evaluator_metadata(self):
        original = load_scenario(PORT)
        variant = load_scenario(DISCLOSED)
        self.assertEqual(disclosed_evidence(variant, 1), [])
        self.assertEqual([x["id"] for x in disclosed_evidence(variant, 2)], ["H03"])
        self.assertEqual(disclosed_evidence(variant, 2), disclosed_evidence(variant, 3))
        for repetition in (1, 2, 3):
            self.assertEqual(opaque_evidence_ids(original, seed=17100, repetition=repetition)[1],
                             opaque_evidence_ids(variant, seed=17100, repetition=repetition)[1])
        variant.pop("design")
        variant["id"], variant["title"] = original["id"], original["title"]
        variant["episodes"][1].pop("public_disclosures")
        self.assertEqual(variant, original)

    def test_disclosure_reaches_each_role_at_correct_time_without_validity(self):
        models = seats()
        result = run_match(scenario_path=DISCLOSED, model_a=models["A"], model_b=models["B"],
                           mediator_model=models["M"], mode="active", repetition=1, seed=12)
        self.assertEqual(result["run_status"], "succeeded")
        card = load_scenario(PORT)["episodes"][1]["evidence"]["b"][0]["content"]
        for role in ("a", "mediator"):
            events = [e for e in result["events"] if e["stage"].endswith(role)]
            for e in events:
                text = json.dumps(e["request"]["messages"])
                self.assertEqual(card in text, not e["stage"].startswith("round_1_"))
                self.assertNotIn('\\"valid\\"', text)
        self.assertNotIn(card, json.dumps(result["rounds"][0]["mediator_observation"]))
        self.assertIn(card, json.dumps(result["rounds"][1]["mediator_observation"]))

    def test_scripted_observation_excludes_sealed_and_private_information(self):
        s = load_scenario(SCENARIO)
        a = actor_intent(80, "collect", ["G01"])
        b = actor_intent(0, "collect", ["B01"])
        a["private_reason"] = "PRIVATE_REASON_SENTINEL"
        kwargs = dict(scenario=s, state=CrisisState.from_scenario(s), episode=s["episodes"][0],
                      intent_a=a, intent_b=b, rounds=[], interventions_left=2,
                      verifiable_ids={"G01", "B01"}, verifications=[],
                      neutral_evidence=s["episodes"][0]["evidence"]["mediator"])
        obs = _mediator_observation(**kwargs)
        rendered = _mediator_prompt(**kwargs)
        text = json.dumps(obs)
        for secret in ("PRIVATE_REASON_SENTINEL", s["ground_truth"]["note"],
                       s["seats"]["a"]["private_brief"],
                       s["verification_results"]["G01"]["content"]):
            self.assertNotIn(secret, text)
            self.assertNotIn(secret, rendered)
        self.assertNotIn('"valid"', text)
        s["ground_truth"]["responsible_actor"] = "state_b"
        s["verification_results"]["G01"]["content"] = "HIDDEN_RESULT_CHANGED"
        self.assertEqual(obs, _mediator_observation(**kwargs))
        self.assertEqual(LinkedVerificationPolicy().decide(obs),
                         LinkedVerificationPolicy().decide(_mediator_observation(**kwargs)))

    def test_rule_prefers_available_link_and_never_requests_terminal_or_repeated_check(self):
        policy = LinkedVerificationPolicy()
        obs = dict(round=2, total_rounds=3, interventions_left=1, state={"escalation": 30},
                   completed_checks=[{"target_id": "E001", "content": "checked"}],
                   verifiable_ids=["E001", "E002", "E003"],
                   neutral_evidence=[{"verification_targets": ["E003", "HIDDEN"]}],
                   intents={role: {"evidence_stances": {}} for role in ("a", "b")})
        self.assertEqual(policy.decide(obs)["target_evidence_id"], "E003")
        obs["neutral_evidence"] = []
        self.assertEqual(policy.decide(obs)["target_evidence_id"], "E002")
        obs["round"] = 3
        self.assertEqual(policy.decide(obs)["channel"], "hold")
        obs["round"], obs["interventions_left"] = 2, 0
        self.assertEqual(policy.decide(obs)["channel"], "hold")

    def test_scripted_match_logs_decisions_delivers_checks_and_pairs(self):
        outputs = []
        for evidence in (["G01"], ["G06-P"], ["G09"]):
            outputs.extend([actor_intent(20, "collect", evidence),
                            actor_final(20, "collect", evidence, accepts=False)])
        records = []
        for mode in ("active", "empty"):
            models = seats(a=outputs)
            policy = ModelSeat(POLICY_LABEL, LinkedVerificationPolicy(), temperature=None,
                               max_tokens=1, send_seed=False)
            r = run_match(scenario_path=SCENARIO, model_a=models["A"], model_b=models["B"],
                          mediator_model=policy, mode=mode, repetition=1, seed=10,
                          evidence_id_mode="original")
            self.assertEqual(r["run_status"], "succeeded")
            self.assertEqual(len(models["A"].client.calls) + len(models["B"].client.calls), 12)
            records.append(r)
        active = records[0]
        decisions = [e for e in active["events"] if e.get("event_type") == "scripted_policy"]
        self.assertEqual(len(decisions), 2)
        self.assertEqual(active["rounds"][2]["delivered_verifications"][0]["target_id"], "G06-P")
        self.assertFalse(active["rounds"][2]["delivered_verifications"][0]["valid"])
        self.assertEqual(active["returned_models"]["mediator"], ["scripted/linked-verification-v1"])
        self.assertEqual(active["returned_providers"]["mediator"], ["local"])
        self.assertEqual(summarize_records(records)["complete_active_empty_pairs"], 1)
        measured = record_measures(active)
        self.assertEqual(measured["budget_forced_holds"], 1)
        self.assertEqual(measured["voluntary_holds"], 0)

    def test_cost_and_attribution_metrics_are_separate_with_conditional_denominators(self):
        active, empty = execute(seats()), execute(seats(), mode="empty")
        active["rounds"][-1]["final_moves"]["a"].update(
            belief_opponent_responsible=85, posture="public_attribution")
        active["rounds"][-1]["resolution"]["severity_a"] = 3
        delta = pair_measures(active, empty)
        self.assertAlmostEqual(delta["attribution_brier_improvement"], .04 - .7225)
        self.assertTrue(delta["active_false_public_attribution_final"])
        self.assertTrue(delta["active_wrong_target_action_any"])
        self.assertFalse(delta["legacy_false_peace_applicable"])
        self.assertEqual(set(delta["component_lifts"]),
                         {"escalation", "civilian_harm", "economic_cost", "trust_deficit"})
        cell = summarize_records([active, empty])["measurement"]["cells"][0]
        a = cell["modes"]["active"]
        self.assertEqual(a["false_public_attribution_final_rate"], 1)
        self.assertIsNone(a["legacy_false_peace_conditional_rate"])
        self.assertEqual(a["legacy_false_peace_eligible_matches"], 0)

    def test_failed_control_is_retained_and_missing_brier_not_imputed(self):
        active, empty = execute(seats()), execute(seats(), mode="empty")
        empty.update(run_status="failed", failure_stage="round_3_intent_b", error="invalid response")
        empty.pop("scores")
        summary = summarize_records([active, empty])
        self.assertEqual(summary["complete_active_empty_pairs"], 0)
        cell = summary["measurement"]["cells"][0]
        self.assertEqual(cell["modes"]["empty"]["failed"], 1)
        self.assertIsNone(cell["mean_brier_improvement_complete_pairs"])
        self.assertEqual(cell["brier_improvement_missingness_bounds"], [-1, 1])
        self.assertEqual(cell["modes"]["active"]["unpaired_successful"], 1)

    def test_identity_excluded_success_is_not_an_eligible_attribution_outcome(self):
        active, empty = execute(seats()), execute(seats(), mode="empty")
        active["returned_models"]["a"] = ["provider/A", "different-model"]
        summary = summarize_records([active, empty])
        cell = summary["measurement"]["cells"][0]
        self.assertEqual(cell["modes"]["active"]["successful"], 1)
        self.assertEqual(cell["modes"]["active"]["identity_excluded_successes"], 1)
        self.assertEqual(cell["modes"]["active"]["measurable_successes"], 0)
        self.assertIsNone(cell["modes"]["active"]["false_public_attribution_final_rate"])
        self.assertEqual(cell["brier_improvement_missingness_bounds"], [-1, 1])

    def test_scenario_validation_rejects_future_disclosure_duplicates_and_inconsistent_checks(self):
        base = load_scenario(PORT)
        bad = []
        future = copy.deepcopy(base); future["episodes"][0]["public_disclosures"] = ["H03"]; bad.append(future)
        dup = copy.deepcopy(base); dup["episodes"][0]["evidence"]["a"][1]["id"] = "P01"; bad.append(dup)
        truth = copy.deepcopy(base); truth["verification_results"]["P06-P"]["valid"] = True; bad.append(truth)
        for scenario in bad:
            with self.subTest(scenario=scenario["id"]), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"; path.write_text(json.dumps(scenario))
                with self.assertRaises(ValueError):
                    load_scenario(path)

    def test_randomized_schedule_preserves_pairs_seeds_and_family_mapping(self):
        kwargs = dict(scenario_paths=[PORT, DISCLOSED], labels=["A", "B", "M"],
                      rotation="balanced", modes=["active", "empty"], repetitions=3,
                      seed=7100, fixed_a="A", fixed_b="B")
        plan = build_schedule(**kwargs, order_seed=23)
        self.assertEqual(plan, build_schedule(**kwargs, order_seed=23))
        self.assertEqual({row["match_id"] for row in plan},
                         {row["match_id"] for row in build_schedule(**kwargs)})
        for index in range(0, len(plan), 2):
            a, b = plan[index:index+2]
            self.assertEqual((a["scenario_id"], a["mediator"], a["repetition"], a["seed"]),
                             (b["scenario_id"], b["mediator"], b["repetition"], b["seed"]))
            self.assertEqual({a["mode"], b["mode"]}, {"active", "empty"})
        for repetition in (1, 2, 3):
            self.assertEqual(len({row["seed"] for row in plan if row["repetition"] == repetition}), 1)
        rule = build_schedule(**kwargs, mediator_policy="linked-verification")
        self.assertEqual(len(rule), 12)
        self.assertEqual(estimate_calls(rule), 144)
        self.assertEqual(len(_scenario_paths("all")), 3)
        self.assertEqual(_scenario_paths("port-disclosure"), [PORT, DISCLOSED])

    def test_order_seed_changes_manifest_and_resume_rejects_changed_design(self):
        models = seats()
        roles = {role: models[label] for role, label in (("a", "A"), ("b", "B"), ("mediator", "M"))}
        s = load_scenario(SCENARIO)
        self.assertNotEqual(run_manifest(s, roles, order_seed=1)["configuration_id"],
                            run_manifest(s, roles, order_seed=2)["configuration_id"])
        args = dict(scenario_paths=[SCENARIO], labels=list(models), rotation="balanced",
                    modes=["empty"], repetitions=1, seed=10, fixed_a="A", fixed_b="B")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            run_schedule(schedule=build_schedule(**args, order_seed=1)[:1], model_seats=models, output=path)
            with self.assertRaisesRegex(ValueError, "Execution-order seed changed"):
                run_schedule(schedule=build_schedule(**args, order_seed=2)[:1], model_seats=models, output=path)
        parsed = build_parser().parse_args(["plan", "--models", "example.json", "--actor-a", "A",
                                          "--actor-b", "B", "--mediator-policy", "linked-verification",
                                          "--order-seed", "42"])
        self.assertEqual(parsed.order_seed, 42)


if __name__ == "__main__":
    unittest.main()
