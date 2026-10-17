"""Regression cases for the independently reproduced research-validity defects."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from third_chair.analysis import render_markdown, summarize_records
from third_chair.client import ModelResponse, OpenAICompatibleClient
from third_chair.engine import resolve_round
from third_chair.provenance import run_manifest, seat_config
from third_chair.runner import ModelSeat, _validate_visible_final, run_match
from third_chair.scenario import CrisisState, load_scenario, opaque_evidence_ids
from third_chair.schema import validate_actor_final
from third_chair.tournament import build_schedule, run_schedule
from test_third_chair import actor_final, actor_intent

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "eval_data/scenarios/grid-vote.json"


def chair(channel="hold", target=None, message="Audit message"):
    return dict(intervene=channel != "hold", channel=channel, message=message,
                target_evidence_id=target, diagnosis="uncertainty",
                predicted_escalation=40, reason="Audit decision")


class CaptureClient:
    def __init__(self, model, outputs=None):
        self.model = model
        self.outputs = list(outputs) if outputs is not None else None
        self.calls = []

    def chat(self, messages, **kwargs):
        self.calls.append(copy.deepcopy({"messages": messages, **kwargs}))
        if self.outputs is not None:
            value = self.outputs.pop(0)
        elif "independent third chair" in messages[0]["content"]:
            value = chair()
        elif "actually take this round" in messages[-1]["content"]:
            value = actor_final(20, "collect", [], accepts=False)
        else:
            value = actor_intent(20, "collect", [])
        if isinstance(value, Exception):
            raise value
        return ModelResponse(json.dumps(value), self.model, {}, {})


def seats(a=None, b=None, mediator=None):
    return {"A": ModelSeat("A", CaptureClient("provider/A", a)),
            "B": ModelSeat("B", CaptureClient("provider/B", b)),
            "M": ModelSeat("M", CaptureClient("provider/M", mediator))}


def execute(models, mode="active", event_sink=None):
    return run_match(scenario_path=SCENARIO, model_a=models["A"], model_b=models["B"],
                     mediator_model=models["M"], mode=mode, repetition=1, seed=12,
                     event_sink=event_sink, evidence_id_mode="original")


def fixture_pair(active_false=False, empty_false=False):
    base = dict(schema_version="0.3.0", run_status="succeeded", scenario_id="fixture",
                repetition=1, seed=10,
                roles={role: {"label": label, "requested_model": label}
                       for role, label in [("a", "A"), ("b", "B"), ("mediator", "M")]},
                rounds=[{"resolution": {"severity_a": 0, "severity_b": 5}}])
    score = dict(truth_score=20, critical_escalation=True, interventions_used=2)
    return [copy.deepcopy(base) | dict(mode="active", match_id="a", scores=score | {
                "crisis_cost": 120, "false_peace": active_false}),
            copy.deepcopy(base) | dict(mode="empty", match_id="e", scores=score | {
                "crisis_cost": 160, "false_peace": empty_false})]


class ContextTests(unittest.TestCase):
    def test_final_context_preserves_evidence_and_delayed_check(self):
        a = [actor_intent(20, "collect", ["G01"]), actor_final(20, "collect", [], accepts=False),
             actor_intent(70, "collect", ["G06-P"]), actor_final(70, "collect", [], accepts=False),
             actor_intent(10, "collect", []), actor_final(10, "collect", [], accepts=False)]
        models = seats(a=a, mediator=[chair(), chair("verify", "G06-P"), chair()])
        record = execute(models)
        self.assertEqual(record["run_status"], "succeeded", record.get("error"))
        final_prompt = models["A"].client.calls[-1]["messages"][-1]["content"]
        scenario = load_scenario(SCENARIO)
        self.assertIn(scenario["episodes"][0]["evidence"]["a"][0]["content"], final_prompt)
        self.assertIn(scenario["verification_results"]["G06-P"]["content"], final_prompt)
        self.assertIn("CURRENT CRISIS STATE", final_prompt)
        self.assertIn("ROUND 1", final_prompt)
        self.assertNotIn(scenario["seats"]["b"]["private_brief"], final_prompt)

    def test_private_history_and_mediator_memory_respect_seat_boundaries(self):
        secret = "PRIVATE_A_ONLY_SENTINEL"
        models = seats(mediator=[chair("private_a", message=secret), chair(), chair()])
        result = execute(models)
        self.assertEqual(result["run_status"], "succeeded")
        def content(label, call):
            return json.dumps(models[label].client.calls[call]["messages"])
        self.assertIn(secret, content("A", 2))
        self.assertNotIn(secret, content("B", 2))
        self.assertIn(secret, content("M", 1))
        first_neutral = load_scenario(SCENARIO)["episodes"][0]["evidence"]["mediator"][0]["content"]
        self.assertIn(first_neutral, content("M", 1))

    def test_earlier_citation_remains_verifiable(self):
        a = [actor_intent(20, "collect", ["G01"]), actor_final(20, "collect", [], accepts=False)]
        a += [actor_intent(20, "collect", []), actor_final(20, "collect", [], accepts=False)] * 2
        result = execute(seats(a=a, mediator=[chair(), chair("verify", "G01"), chair()]))
        self.assertEqual(result["run_status"], "succeeded", result.get("error"))
        self.assertEqual(result["rounds"][2]["delivered_verifications"][0]["target_id"], "G01")

    def test_visibility_uses_channel_not_message_prefix(self):
        move = actor_final(20, "collect", [], accepts=True)
        _validate_visible_final(move, postures={"collect"}, known_ids=set(),
                                mediator=chair("joint", message="No third-party verification yet"), seat="a")
        with self.assertRaisesRegex(ValueError, "cannot accept"):
            _validate_visible_final(move, postures={"collect"}, known_ids=set(),
                                    mediator=chair("private_a"), seat="b")

    def test_failed_round_retains_successful_calls_and_requests(self):
        models = seats(b=[actor_intent(20, "collect", []), RuntimeError("simulated outage")])
        journal = []
        record = execute(models, event_sink=journal.append)
        self.assertEqual(record["run_status"], "failed")
        successful = [e for e in record["events"] if e["status"] == "succeeded"]
        self.assertEqual(len(successful), 4)
        self.assertEqual(len(journal), len(record["events"]))
        self.assertIn("a", record["partial_round"]["final_moves"])
        self.assertEqual(record["returned_models"]["a"], ["provider/A"])
        self.assertEqual(record["failure_attempts"][0]["status"], "transport_failed")
        self.assertEqual(successful[0]["request"]["temperature"], 0.2)
        self.assertEqual(successful[0]["request"]["max_tokens"], 1400)
        self.assertTrue(successful[0]["request"]["messages"])

    def test_response_correction_is_recorded(self):
        models = seats(a=[{}, {}])
        record = execute(models)
        self.assertEqual(record["run_status"], "failed")
        self.assertEqual(len(record["failure_attempts"]), 2)
        self.assertIn("cannot be scored", record["failure_attempts"][1]["request"]["messages"][-1]["content"])


class ScoringTests(unittest.TestCase):
    def resolve(self, a, b=None, mediator=None, scenario=None):
        scenario = scenario or load_scenario(SCENARIO)
        return resolve_round(scenario=scenario, state=CrisisState.from_scenario(scenario),
                             episode=scenario["episodes"][0], final_a=a,
                             final_b=b or actor_final(20, "collect", [], accepts=False),
                             mediator=mediator or chair(), verified_invalid_ids={"G06-P"})

    def test_rejection_is_not_endorsement_and_does_not_change_physical_state(self):
        support = actor_final(20, "collect", ["G06-P"], accepts=False)
        reject = copy.deepcopy(support)
        reject["evidence_stances"]["G06-P"] = "reject"
        supported, rejected = self.resolve(support), self.resolve(reject)
        self.assertEqual(supported["invalid_evidence_after_check_a"], ["G06-P"])
        self.assertEqual(rejected["invalid_evidence_after_check_a"], [])
        self.assertEqual(supported["state"], rejected["state"])

    def test_mediator_acceptance_cannot_generate_mechanical_lift(self):
        for posture in ("collect", "sanctions"):
            scenario = load_scenario(SCENARIO)
            if posture not in {p["id"] for p in scenario["postures"]}:
                posture = scenario["postures"][4]["id"]
            no = actor_final(20, posture, [], accepts=False)
            yes = actor_final(20, posture, [], accepts=True)
            self.assertEqual(self.resolve(no, no)["state"], self.resolve(yes, yes, chair("joint"))["state"])

    def test_hidden_responsibility_does_not_leak_via_public_score(self):
        innocent = load_scenario(SCENARIO)
        guilty = copy.deepcopy(innocent)
        guilty["ground_truth"]["responsible_actor"] = "state_b"
        move = actor_final(90, "public_attribution", [], accepts=False)
        x, y = self.resolve(move, scenario=innocent), self.resolve(move, scenario=guilty)
        self.assertEqual(x["state"], y["state"])
        self.assertEqual(x["crisis_cost"], y["crisis_cost"])
        self.assertNotEqual(x["unjustified_escalation_a"], y["unjustified_escalation_a"])

    def test_brier_is_probability_squared_error(self):
        result = execute(seats(), mode="empty")
        self.assertEqual(result["scores"]["attribution_brier"], 0.04)

    def test_stances_must_cover_exactly_cited_ids(self):
        move = actor_final(20, "collect", ["known"], accepts=False)
        move["evidence_stances"] = {}
        with self.assertRaisesRegex(ValueError, "every cited"):
            validate_actor_final(move, postures={"collect"}, known_ids={"known"})


class AnalysisTests(unittest.TestCase):
    def test_all_false_peace_combinations_and_gated_success(self):
        for active_false in (False, True):
            for empty_false in (False, True):
                with self.subTest(active=active_false, empty=empty_false):
                    summary = summarize_records(fixture_pair(active_false, empty_false))
                    row = summary["mediators"][0]
                    self.assertEqual(row["false_peace_rate"], 100 * active_false)
                    self.assertEqual(row["empty_false_peace_rate"], 100 * empty_false)
                    self.assertEqual(row["false_peace_introduced_rate"], 100 * (active_false and not empty_false))
                    self.assertEqual(row["de_escalation_win_rate"], 100 * (not active_false))
                    self.assertEqual(row["positive_lift_rate"], 100)
                    self.assertIn("Gated win", render_markdown(summary))

    def test_duplicate_successes_are_rejected(self):
        pair = fixture_pair()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            summarize_records(pair + [copy.deepcopy(pair[0])])

    def test_changed_requested_model_does_not_pair(self):
        pair = fixture_pair()
        pair[1]["roles"]["a"]["requested_model"] = "changed-model"
        summary = summarize_records(pair)
        self.assertEqual(summary["complete_active_empty_pairs"], 0)
        self.assertEqual(summary["unpaired_successful_matches"], 2)

    def test_changed_returned_actor_model_does_not_pair(self):
        pair = fixture_pair()
        pair[0]["returned_models"] = {"a": ["version1"]}
        pair[1]["returned_models"] = {"a": ["version2"]}
        self.assertEqual(summarize_records(pair)["complete_active_empty_pairs"], 0)

    def test_mismatched_protocols_do_not_pair(self):
        pair = fixture_pair()
        pair[1]["schema_version"] = "0.4.0"
        self.assertEqual(summarize_records(pair)["complete_active_empty_pairs"], 0)

    def test_distinct_configurations_do_not_merge_into_one_report_row(self):
        pairs = fixture_pair()
        other = copy.deepcopy(pairs)
        for record in other:
            record["repetition"] = 2
            record["roles"]["a"]["requested_model"] = "different-actor"
        summary = summarize_records(pairs + other)
        self.assertEqual(summary["complete_active_empty_pairs"], 2)
        self.assertEqual(len(summary["mediators"]), 2)

    def test_match_critical_does_not_blame_quiet_actor(self):
        rows = {r["model"]: r for r in summarize_records(fixture_pair())["actors"]}
        self.assertEqual(rows["A"]["critical_escalation_rate"], 0)
        self.assertEqual(rows["A"]["match_critical_participation_rate"], 100)
        self.assertEqual(rows["B"]["critical_escalation_rate"], 100)


class ProvenanceTests(unittest.TestCase):
    def test_opaque_ids_are_consistent_and_do_not_encode_forgery(self):
        original = load_scenario(SCENARIO)
        changed, mapping = opaque_evidence_ids(original, seed=12, repetition=1)
        again, again_map = opaque_evidence_ids(original, seed=12, repetition=1)
        self.assertEqual(changed, again)
        self.assertEqual(mapping, again_map)
        self.assertEqual(len(mapping), len(set(mapping.values())))
        self.assertTrue(all(value.startswith("E") and value[1:].isdigit() for value in mapping.values()))
        self.assertNotIn("G06-P", json.dumps(changed))
        self.assertFalse(changed["verification_results"][mapping["G06-P"]]["valid"])
        self.assertIn(mapping["G06-P"], changed["ground_truth"]["forged_evidence_ids"])
        self.assertEqual(original["episodes"][0]["public_event"], changed["episodes"][0]["public_event"])
        self.assertNotEqual(mapping, opaque_evidence_ids(original, seed=13, repetition=1)[1])

    def schedule(self, seed=12, **kwargs):
        return build_schedule(scenario_paths=[SCENARIO], labels=["A", "B", "M"],
                              rotation="balanced", modes=["empty"], repetitions=1,
                              seed=seed, **kwargs)

    def test_seed_changes_schedule_identity(self):
        self.assertNotEqual(self.schedule(1)[0]["match_id"], self.schedule(2)[0]["match_id"])

    def test_fixed_actors_and_pair_seed_across_mediators(self):
        plan = self.schedule(fixed_a="A", fixed_b="B")
        self.assertEqual({(p["a"], p["b"]) for p in plan}, {("A", "B")})
        self.assertEqual({p["mediator"] for p in plan}, {"A", "B", "M"})
        self.assertEqual(len({p["seed"] for p in plan}), 1)

    def test_resume_skips_finished_but_rejects_changed_settings(self):
        models = seats()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matches.jsonl"
            plan = self.schedule()[:1]
            run_schedule(schedule=plan, model_seats=models, output=output)
            count = sum(len(s.client.calls) for s in models.values())
            run_schedule(schedule=plan, model_seats=models, output=output)
            self.assertEqual(count, sum(len(s.client.calls) for s in models.values()))
            self.assertTrue(output.with_suffix(".jsonl.events.jsonl").exists())
            models["A"].temperature = 0.8
            with self.assertRaisesRegex(ValueError, "configuration changed"):
                run_schedule(schedule=plan, model_seats=models, output=output)

    def test_interrupted_journal_cannot_be_silently_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matches.jsonl"
            output.with_suffix(".jsonl.events.jsonl").write_text('{"match_id":"unfinished"}\n')
            with self.assertRaisesRegex(ValueError, "Interrupted"):
                run_schedule(schedule=self.schedule(), model_seats=seats(), output=output)

    def test_new_seed_is_not_skipped_and_failed_matches_are_not_retried(self):
        models = seats(b=[RuntimeError("outage")])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matches.jsonl"
            run_schedule(schedule=self.schedule(1)[:1], model_seats=models, output=output)
            count = sum(len(s.client.calls) for s in models.values())
            run_schedule(schedule=self.schedule(1)[:1], model_seats=models, output=output)
            self.assertEqual(count, sum(len(s.client.calls) for s in models.values()))
            models["B"].client.outputs = None
            run_schedule(schedule=self.schedule(2)[:1], model_seats=models, output=output)
            records = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual([r["run_status"] for r in records], ["failed", "succeeded"])
            self.assertNotEqual(records[0]["match_id"], records[1]["match_id"])

    def test_changed_scenario_after_planning_is_rejected_before_calls(self):
        plan = self.schedule()[:1]
        plan[0]["scenario_sha256"] = "stale"
        models = seats()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "after planning"):
                run_schedule(schedule=plan, model_seats=models, output=Path(directory) / "out.jsonl")
        self.assertTrue(all(not s.client.calls for s in models.values()))

    def test_all_scenarios_run_and_pair_with_opaque_ids(self):
        records = []
        for path in sorted((ROOT / "eval_data/scenarios").glob("*.json")):
            for mode in ("active", "empty"):
                models = seats()
                record = run_match(scenario_path=path, model_a=models["A"], model_b=models["B"],
                                   mediator_model=models["M"], mode=mode, repetition=1, seed=44)
                self.assertEqual(record["run_status"], "succeeded", record.get("error"))
                self.assertTrue(record["evidence_id_map"])
                records.append(record)
        summary = summarize_records(records)
        self.assertEqual(summary["complete_active_empty_pairs"], 3)
        self.assertTrue(all(pair["mediation_lift"] == 0 for pair in summary["pairs"]))

    def test_manifest_records_configuration_without_api_key(self):
        client = OpenAICompatibleClient(base_url="https://example.test/v1", api_key="SECRET", model="fixed")
        model = ModelSeat("label", client, temperature=0.3)
        manifest = run_manifest(load_scenario(SCENARIO), {"a": model, "b": model, "mediator": model})
        self.assertNotIn("SECRET", json.dumps(manifest))
        self.assertEqual(seat_config(model)["endpoint"], "https://example.test/v1/chat/completions")
        other = ModelSeat("label", client, temperature=0.4)
        self.assertNotEqual(manifest["configuration_id"], run_manifest(load_scenario(SCENARIO), {"a": other, "b": model, "mediator": model})["configuration_id"])


class TransportTests(unittest.TestCase):
    @patch("third_chair.client.time.sleep")
    def test_retries_are_recorded_without_error_body(self, sleep):
        client = OpenAICompatibleClient(base_url="https://example.test", api_key="SECRET", model="m")
        failure = urllib.error.HTTPError(client.url, 429, "retry", {}, io.BytesIO(b"SECRET"))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "model": "m", "choices": [{"message": {"content": "{}"}}]
        }).encode()
        with patch("urllib.request.urlopen", side_effect=[failure, response]):
            result = client.chat([])
        self.assertEqual([a["status"] for a in result.transport_attempts], ["http_error", "succeeded"])
        self.assertNotIn("SECRET", json.dumps(result.transport_attempts))
        sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
