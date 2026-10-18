"""Scheduled communication after a check, without privileged policy inputs."""

from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from third_chair.analysis import load_records, render_markdown, summarize_records
from third_chair.client import ModelResponse
from third_chair.cli import build_parser
from third_chair.measurement import record_measures
from third_chair.policies import (DELAYED_LABEL, DELAYED_MESSAGE, DELAYED_VERIFICATION,
                                 POST_VERIFICATION_STUDY, DelayedVerificationPolicy)
from third_chair.provenance import run_manifest
from third_chair.runner import ModelSeat, run_match
from third_chair.scenario import load_scenario
from third_chair.tournament import build_schedule, estimate_calls, run_schedule
from test_audit_regressions import SCENARIO, CaptureClient, chair, seats
from test_third_chair import actor_final, actor_intent

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "eval_data/scenarios/port-sanctions.json"
DISCLOSED = ROOT / "eval_data/variants/port-sanctions-disclosed.json"


def scripted_seat():
    return ModelSeat(DELAYED_LABEL, DelayedVerificationPolicy(), temperature=None,
                     max_tokens=1, send_seed=False)


def fixture(policy=DELAYED_MESSAGE, mode="active", mediator=None, cite_target=True):
    a = []
    for evidence in (["G01"], ["G06-P"] if cite_target else [], ["G09"]):
        a.extend([actor_intent(80, "harden_hotline", evidence),
                  actor_final(80, "harden_hotline", evidence, accepts=False)])
    models = seats(a=a, mediator=mediator if mediator is not None else [chair("joint")])
    med = scripted_seat() if policy == DELAYED_VERIFICATION else models["M"]
    record = run_match(scenario_path=SCENARIO, model_a=models["A"], model_b=models["B"],
                       mediator_model=med, mode=mode, repetition=1, seed=18,
                       evidence_id_mode="original", mediator_policy=policy, order_seed=42)
    return record, models


class PostVerificationTests(unittest.TestCase):
    def test_delayed_mediator_sees_public_claim_behind_checked_document(self):
        a = []
        for evidence in (["P01"], ["P06-P"], ["P08"]):
            a.extend([actor_intent(80, "harden_hotline", evidence),
                      actor_final(80, "harden_hotline", evidence, accepts=False)])
        models = seats(a=a, mediator=[chair("joint")])
        record = run_match(scenario_path=PORT, model_a=models["A"], model_b=models["B"],
                           mediator_model=models["M"], mode="active", repetition=1,
                           seed=18, evidence_id_mode="original", mediator_policy=DELAYED_MESSAGE)
        self.assertEqual(record["run_status"], "succeeded", record.get("error"))
        self.assertEqual(len(models["M"].client.calls), 1)
        prompt = "\n".join(m["content"] for m in models["M"].client.calls[0]["messages"])
        scenario = load_scenario(PORT)
        self.assertIn(scenario["episodes"][1]["public_event"], prompt)
        self.assertIn(scenario["verification_results"]["P06-P"]["content"], prompt)
        self.assertIn(scenario["episodes"][1]["public_event"],
                      record["rounds"][2]["mediator_observation"]["history"])
        for seat in ("a", "b"):
            self.assertNotIn(scenario["seats"][seat]["private_brief"], prompt)
            for episode in scenario["episodes"]:
                for card in episode["evidence"][seat]:
                    self.assertNotIn(card["content"], prompt)
        self.assertNotIn(scenario["ground_truth"]["note"], prompt)

    def test_mixed_schedule_executes_with_opaque_ids_and_resumes_without_replaying_calls(self):
        class EvidenceClient(CaptureClient):
            def chat(self, messages, **kwargs):
                self.calls.append(copy.deepcopy(messages))
                prompt = messages[-1]["content"]
                evidence = prompt.split("YOUR EVIDENCE TO DATE\n", 1)[1].split("COMPLETED NEUTRAL CHECKS", 1)[0]
                ids = re.findall(r"\[(E\d+)\]", evidence)
                value = (actor_final(70, "harden_hotline", ids, accepts=False)
                         if "actually take this round" in prompt else
                         actor_intent(70, "harden_hotline", ids))
                return ModelResponse(json.dumps(value), self.model, {}, {})
        models = {"A": ModelSeat("A", EvidenceClient("provider/A")),
                  "B": ModelSeat("B", EvidenceClient("provider/B")),
                  "M": ModelSeat("M", CaptureClient("provider/M", [chair("joint"), chair("joint")])),
                  DELAYED_LABEL: scripted_seat()}
        schedule = build_schedule(scenario_paths=[PORT, DISCLOSED], labels=["A", "B", "M"],
                                  rotation="balanced", modes=["active", "empty"], repetitions=1,
                                  seed=8100, fixed_a="A", fixed_b="B", mediator_label="M",
                                  mediator_policy=POST_VERIFICATION_STUDY, order_seed=42)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"matches.jsonl"
            run_schedule(schedule=schedule, model_seats=models, output=output)
            records = load_records([output])
            summary = summarize_records(records)
            self.assertEqual(summary["successful_matches"], 8, summary["failures"])
            self.assertEqual(summary["complete_active_empty_pairs"], 4)
            self.assertEqual([r["status"] for r in summary["post_verification_comparisons"]],
                             ["complete", "complete"])
            self.assertEqual(sum(len(models[k].client.calls) for k in ("A", "B", "M")), 98)
            self.assertEqual(len(models["M"].client.calls), 2)
            run_schedule(schedule=schedule, model_seats=models, output=output)
            self.assertEqual(sum(len(models[k].client.calls) for k in ("A", "B", "M")), 98)

    def test_single_third_model_and_both_policies_share_one_randomized_schedule(self):
        kwargs = dict(scenario_paths=[PORT, DISCLOSED], labels=["A", "B", "M"],
                      rotation="balanced", modes=["active", "empty"], repetitions=1,
                      seed=8100, fixed_a="A", fixed_b="B", mediator_label="M",
                      mediator_policy=POST_VERIFICATION_STUDY, order_seed=20261019)
        schedule = build_schedule(**kwargs)
        self.assertEqual(schedule, build_schedule(**kwargs))
        self.assertEqual(len(schedule), 8)
        self.assertEqual(estimate_calls(schedule), 98)
        self.assertEqual({r["mediator"] for r in schedule}, {"M", DELAYED_LABEL})
        self.assertEqual({r["seed"] for r in schedule}, {18100})
        for i in range(0, len(schedule), 2):
            a, b = schedule[i:i + 2]
            self.assertEqual((a["mediator_policy"], a["scenario_id"]),
                             (b["mediator_policy"], b["scenario_id"]))
            self.assertEqual({a["mode"], b["mode"]}, {"active", "empty"})
        for changed in ({"mediator_label": None}, {"mediator_label": "A"},
                        {"fixed_a": "B"}, {"fixed_a": None, "fixed_b": None}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                build_schedule(**(kwargs | changed))
        parsed = build_parser().parse_args(["plan", "--models", "models.json", "--actor-a", "A",
                                           "--actor-b", "B", "--mediator", "M",
                                           "--mediator-policy", POST_VERIFICATION_STUDY])
        self.assertEqual(parsed.mediator, "M")

    def test_llm_only_called_after_result_and_sees_no_sealed_truth(self):
        record, models = fixture()
        self.assertEqual(record["run_status"], "succeeded", record.get("error"))
        self.assertEqual([r["mediator"]["channel"] for r in record["rounds"]],
                         ["hold", "verify", "joint"])
        self.assertEqual([r["mediator_decision_origin"] for r in record["rounds"]],
                         ["protocol", "protocol", "llm"])
        self.assertEqual(len(models["M"].client.calls), 1)
        self.assertEqual(len(models["A"].client.calls) + len(models["B"].client.calls), 12)
        self.assertEqual(record["scores"]["interventions_used"], 2)
        final = record["rounds"][2]
        self.assertEqual(final["mediator_observation"]["interventions_left"], 1)
        self.assertEqual(final["delivered_verifications"][0]["target_id"], "G06-P")
        prompt = json.dumps(models["M"].client.calls[0]["messages"])
        scenario = load_scenario(SCENARIO)
        self.assertIn(scenario["verification_results"]["G06-P"]["content"], prompt)
        self.assertNotIn(scenario["ground_truth"]["note"], prompt)
        self.assertNotIn(scenario["seats"]["a"]["private_brief"], prompt)
        self.assertIn("EXPERIMENTAL CONDITION: POST-VERIFICATION COMMUNICATION", prompt)
        self.assertEqual(record["returned_models"]["mediator"], ["provider/M"])
        self.assertEqual(record["missing_model_responses"]["mediator"], 0)
        local = [e for e in record["events"] if e.get("event_type") == "protocol_action"]
        self.assertEqual(len(local), 2)
        self.assertTrue(all(e["usage"]["cost"] == 0 and "raw_response" not in e for e in local))
        measured = record_measures(record)
        self.assertEqual(measured["protocol_forced_holds"], 1)
        self.assertEqual(measured["voluntary_holds"], 0)
        self.assertEqual(measured["budget_forced_holds"], 0)

    def test_verification_control_matches_check_without_mediator_api_calls(self):
        message, _ = fixture()
        control, models = fixture(DELAYED_VERIFICATION)
        self.assertEqual(control["run_status"], "succeeded", control.get("error"))
        self.assertEqual(len(models["M"].client.calls), 0)
        self.assertEqual([r["mediator"]["channel"] for r in control["rounds"]],
                         ["hold", "verify", "hold"])
        self.assertEqual(message["rounds"][1]["mediator"], control["rounds"][1]["mediator"])
        self.assertEqual(message["rounds"][2]["delivered_verifications"],
                         control["rounds"][2]["delivered_verifications"])
        self.assertEqual(control["scores"]["interventions_used"], 1)
        self.assertEqual(record_measures(control)["protocol_forced_holds"], 2)
        self.assertEqual(message["scores"]["crisis_cost"], control["scores"]["crisis_cost"])

    def test_missing_checkable_target_fails_without_fallback_or_mediator_call(self):
        record, models = fixture(cite_target=False)
        self.assertEqual(record["run_status"], "failed")
        self.assertEqual(record["failure_stage"], "round_2_mediator")
        self.assertIn("exactly one available neutral-linked target", record["error"])
        self.assertEqual(len(models["M"].client.calls), 0)
        self.assertEqual(len(record["rounds"]), 1)

    def test_final_channel_constraint_uses_existing_correction_then_records_failure(self):
        repaired, models = fixture(mediator=[chair(), chair("joint")])
        self.assertEqual(repaired["run_status"], "succeeded")
        self.assertEqual(len(models["M"].client.calls), 2)
        bad = [e for e in repaired["events"] if e["status"] == "invalid_response"]
        self.assertEqual(len(bad), 1)
        self.assertIn("round-three joint", bad[0]["validation_error"])
        failed, _ = fixture(mediator=[chair(), chair()])
        self.assertEqual(failed["run_status"], "failed")
        self.assertEqual(failed["failure_stage"], "round_3_mediator")
        self.assertEqual(len(failed["failure_attempts"]), 2)

    def test_direct_comparison_is_separate_from_empty_chair_pairs_and_missingness(self):
        message, _ = fixture()
        control, _ = fixture(DELAYED_VERIFICATION)
        empty_message, _ = fixture(mode="empty")
        empty_control, _ = fixture(DELAYED_VERIFICATION, mode="empty")
        summary = summarize_records([message, control, empty_message, empty_control])
        self.assertEqual(summary["complete_active_empty_pairs"], 2)
        comparison = summary["post_verification_comparisons"][0]
        self.assertEqual(comparison["status"], "complete")
        self.assertEqual(comparison["cost_reduction_vs_verification"], 0)
        self.assertEqual(comparison["brier_improvement_vs_verification"], 0)
        self.assertIn("Message versus scheduled verification only", render_markdown(summary))
        missing = summarize_records([message])["post_verification_comparisons"][0]
        self.assertEqual(missing["status"], "missing_or_ambiguous_arm")
        self.assertIsNone(missing["cost_reduction_vs_verification"])
        failed, _ = fixture(DELAYED_VERIFICATION, cite_target=False)
        incomplete = summarize_records([message, failed])["post_verification_comparisons"][0]
        self.assertEqual(incomplete["status"], "failed_or_identity_excluded_arm")
        self.assertIsNone(incomplete["brier_improvement_vs_verification"])

    def test_direct_comparison_rejects_wrong_check_or_changed_actor_provider(self):
        message, _ = fixture()
        control, _ = fixture(DELAYED_VERIFICATION)
        changed = copy.deepcopy(control)
        changed["rounds"][2]["delivered_verifications"][0]["content"] = "Different result"
        row = summarize_records([message, changed])["post_verification_comparisons"][0]
        self.assertEqual(row["status"], "scheduled_check_mismatch")
        self.assertIsNone(row["cost_reduction_vs_verification"])
        changed = copy.deepcopy(control)
        changed["returned_providers"]["a"] = ["different-provider"]
        row = summarize_records([message, changed])["post_verification_comparisons"][0]
        self.assertEqual(row["status"], "incompatible_actor_identity")
        # Independent prefix differences must not silently disqualify a valid schedule.
        changed = copy.deepcopy(control)
        changed["rounds"][1]["mediator"]["predicted_escalation"] += 5
        changed["rounds"][2]["intents"]["a"]["belief_opponent_responsible"] = 70
        row = summarize_records([message, changed])["post_verification_comparisons"][0]
        self.assertEqual(row["status"], "complete")
        self.assertEqual(row["pre_message_probability_difference"], .1)

    def test_policy_identity_prevents_resume_into_a_different_protocol(self):
        models = seats()
        roles = {role: models[label] for role, label in (("a", "A"), ("b", "B"), ("mediator", "M"))}
        scenario = load_scenario(SCENARIO)
        self.assertNotEqual(run_manifest(scenario, roles)["configuration_id"],
                            run_manifest(scenario, roles, mediator_policy=DELAYED_MESSAGE)["configuration_id"])
        kwargs = dict(scenario_paths=[SCENARIO], labels=list(models), rotation="balanced",
                      modes=["empty"], repetitions=1, seed=18, fixed_a="A", fixed_b="B",
                      mediator_label="M")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"matches.jsonl"
            run_schedule(schedule=build_schedule(**kwargs, mediator_policy=DELAYED_MESSAGE),
                         model_seats=models, output=output)
            with self.assertRaisesRegex(ValueError, "Mediator policy changed"):
                run_schedule(schedule=build_schedule(**kwargs), model_seats=models, output=output)


if __name__ == "__main__":
    unittest.main()
