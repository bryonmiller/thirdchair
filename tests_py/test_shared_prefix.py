"""Offline shared-prefix execution, boundaries, durability, and analysis."""

from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from third_chair.analysis import load_records, summarize_records
from third_chair.cli import build_parser
from third_chair.client import ModelResponse
from third_chair.policies import DELAYED_MESSAGE, SHARED_PREFIX
from third_chair.provenance import fingerprint, source_digest
from third_chair.runner import ModelSeat, run_match
from third_chair.scenario import load_scenario
from third_chair.shared_prefix import (build_shared_schedule, event_cost, run_shared_schedule,
                                      summarize_shared_records)
from third_chair.tournament import _append_jsonl
from test_audit_regressions import chair
from test_third_chair import actor_wire, actor_final, actor_intent

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "eval_data/scenarios/port-sanctions.json"
DISCLOSED = ROOT / "eval_data/variants/port-sanctions-disclosed.json"


class FixtureClient:
    provider_metadata_required = True

    def __init__(self, role):
        self.model = f"fixture/{role}"
        self.role = role
        self.calls = []
        self.fail_on = set()
        self.invalid_on = set()
        self.interrupt_on = set()
        self.provider_name = "fixture-provider"

    def chat(self, messages, **kwargs):
        self.calls.append(copy.deepcopy({"messages": messages, **kwargs}))
        number = len(self.calls)
        if number in self.interrupt_on:
            raise KeyboardInterrupt()
        if number in self.fail_on:
            raise RuntimeError("Fixture transport failure")
        prompt = messages[1]["content"]
        if self.role == "M":
            value = chair("joint", message="Please pause attribution and investigate the port logs.")
        else:
            evidence = prompt.split("YOUR EVIDENCE TO DATE\n", 1)[1].split(
                "COMPLETED NEUTRAL CHECKS", 1)[0]
            ids = re.findall(r"\[(E\d+)\]", evidence)
            final = "actually take this round" in prompt
            received = "Please pause attribution" in prompt
            value = (actor_final(35 if received else 75, "collect" if received else "harden_hotline",
                                 ids, accepts=received) if final else
                     actor_intent(75, "harden_hotline", ids))
            if not final:
                value["private_reason"] = f"Private intent of {self.role} only."
        if number in self.invalid_on:
            value = {"invalid": True}
        return ModelResponse(json.dumps(actor_wire(value)), self.model, {"cost": 0.001}, {},
                             returned_provider=self.provider_name, finish_reason="stop")


def models():
    return {role: ModelSeat(role, FixtureClient(role), send_seed=False) for role in ("A", "B", "M")}


def schedule(paths=None, **changes):
    kwargs = dict(scenario_paths=paths or [PORT], labels=["A", "B", "M"],
                  actor_a="A", actor_b="B", mediator="M", repetitions=1, seed=8100,
                  order_seed=20261020)
    return build_shared_schedule(**(kwargs | changes))


def execute(seats, **kwargs):
    return run_match(scenario_path=PORT, model_a=seats["A"], model_b=seats["B"],
                     mediator_model=seats["M"], mode="active", repetition=1, seed=18100,
                     order_seed=20261020, mediator_policy=SHARED_PREFIX, **kwargs)


class SharedPrefixTests(unittest.TestCase):
    def test_prefix_boundary_has_delivered_check_and_both_intentions(self):
        seats = models()
        prefix = execute(seats)
        self.assertEqual(prefix["run_status"], "prefix_ready", prefix.get("error"))
        checkpoint = prefix["checkpoint"]
        self.assertEqual(len(checkpoint["rounds"]), 2)
        self.assertEqual(len(checkpoint["completed_verifications"]), 1)
        self.assertEqual(checkpoint["delivered_now"][0]["requested_round"], 2)
        for actor, label in (("a", "A"), ("b", "B")):
            self.assertEqual(prefix["partial_round"]["intents"][actor], checkpoint[f"intent_{actor}"])
            self.assertEqual(len(seats[label].client.calls), 5)
        self.assertFalse(seats["M"].client.calls)
        self.assertEqual(prefix["manifest"]["source_sha256"], source_digest())
        self.assertEqual(prefix["manifest"]["package_version"], "0.8.0")
        self.assertEqual(prefix["checkpoint_sha256"], fingerprint(checkpoint))

    def test_prefix_equality_branch_isolation_and_only_message_changes_actor_context(self):
        seats = models()
        prefix = execute(seats)
        unchanged = copy.deepcopy(prefix)
        message = execute(seats, prefix_checkpoint=prefix, shared_branch="message")
        control = execute(seats, prefix_checkpoint=prefix, shared_branch="no-message")
        self.assertEqual(prefix, unchanged)
        for branch in (message, control):
            self.assertEqual(branch["run_status"], "succeeded", branch.get("error"))
            self.assertEqual(branch["checkpoint_sha256"], prefix["checkpoint_sha256"])
            self.assertEqual(branch["rounds"][-1]["intents"], prefix["partial_round"]["intents"])
            self.assertEqual(branch["rounds"][-1]["mediator_observation"], prefix["checkpoint"]["observation"])
            self.assertTrue(all(e["stage"].startswith("round_3_") for e in branch["events"]))
        self.assertEqual(message["rounds"][:2], control["rounds"][:2])
        for label in ("A", "B"):
            calls = seats[label].client.calls
            self.assertEqual(len(calls), 7)
            msg = copy.deepcopy(calls[-2])
            msg["messages"][1]["content"] = msg["messages"][1]["content"].replace(
                message["rounds"][-1]["mediator"]["message"], "No third-party message was sent.")
            self.assertEqual(msg, calls[-1])
        message["rounds"][0]["final_moves"]["a"]["posture"] = "counter_cyber"
        self.assertEqual(prefix, unchanged)
        self.assertNotEqual(message["rounds"][0], control["rounds"][0])

    def test_role_information_does_not_escape_checkpoint(self):
        seats = models()
        prefix = execute(seats)
        branch = execute(seats, prefix_checkpoint=prefix, shared_branch="message")
        self.assertEqual(branch["run_status"], "succeeded", branch.get("error"))
        scenario = load_scenario(PORT)
        med = "\n".join(m["content"] for m in seats["M"].client.calls[0]["messages"])
        self.assertIn(scenario["episodes"][1]["public_event"], med)
        self.assertIn(scenario["verification_results"]["P06-P"]["content"], med)
        self.assertNotIn(scenario["ground_truth"]["note"], med)
        for actor, label, other in (("a", "A", "B"), ("b", "B", "A")):
            self.assertNotIn(scenario["seats"][actor]["private_brief"], med)
            self.assertNotIn(f"Private intent of {label} only.", med)
            for call in seats[label].client.calls:
                prompt = str(call["messages"])
                self.assertNotIn(f"Private intent of {other} only.", prompt)
                self.assertNotIn(scenario["ground_truth"]["note"], prompt)
                self.assertNotIn('"checkpoint"', prompt)
            # Current opponent intentions do not enter the shared intention requests.
            self.assertNotIn("State B announced this posture", seats[label].client.calls[4]["messages"][1]["content"])
            self.assertNotIn("State A announced this posture", seats[label].client.calls[4]["messages"][1]["content"])

    def test_message_path_preserves_existing_delayed_message_prompts_and_scoring(self):
        original = models()
        baseline = run_match(scenario_path=PORT, model_a=original["A"], model_b=original["B"],
                             mediator_model=original["M"], mode="active", repetition=1,
                             seed=18100, order_seed=20261020, mediator_policy=DELAYED_MESSAGE)
        forked = models()
        prefix = execute(forked)
        branch = execute(forked, prefix_checkpoint=prefix, shared_branch="message")
        self.assertEqual(baseline["scores"], branch["scores"])
        for role in original:
            self.assertEqual(original[role].client.calls, forked[role].client.calls)

    def test_costs_count_prefix_once_and_reject_legacy_analysis(self):
        seats = models()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            records = load_records([output])
            summary = summarize_shared_records(records)
            self.assertEqual(summary["complete_comparisons"], 1)
            self.assertEqual(summary["requests"], 15)
            self.assertEqual(summary["requests_without_cost"], 0)
            self.assertEqual(summary["recorded_cost_usd"], 0.015)
            comparison = summary["comparisons"][0]
            self.assertEqual(comparison["costs"]["prefix"]["recorded_cost_usd"], 0.01)
            self.assertEqual(comparison["costs"]["message"]["recorded_cost_usd"], 0.003)
            self.assertEqual(comparison["costs"]["no-message"]["recorded_cost_usd"], 0.002)
            self.assertEqual(comparison["first_two_rounds_cost_difference"], 0)
            self.assertEqual(comparison["pre_message_probability_difference"], 0)
            self.assertEqual(comparison["branches"]["message"]["interventions_used"], 2)
            self.assertEqual(comparison["branches"]["no-message"]["interventions_used"], 1)
            self.assertIsNone(comparison["branches"]["message"]["legacy_false_peace"])
            with self.assertRaisesRegex(ValueError, "summarize-shared-prefix"):
                summarize_records(records)
            with self.assertRaises(ValueError):
                summarize_shared_records(load_records([output, output]))

    def test_correction_usage_counted_and_missing_cost_visible(self):
        seats = models()
        seats["A"].client.invalid_on = {1}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            records = load_records([output])
            summary = summarize_shared_records(records)
            self.assertEqual(summary["requests"], 16)
            self.assertEqual(summary["recorded_cost_usd"], 0.016)
            event = next(e for e in records[0]["events"] if e["status"] == "invalid_response")
            event["usage"] = {}
            self.assertEqual(event_cost(records[0])["requests_without_cost"], 1)

    def test_full_and_prefix_only_resume_do_not_replay_calls(self):
        seats = models()
        planned = schedule()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            prefix = execute(seats)
            prefix.update(protocol_version="shared-prefix-0.7.0", branch_order=planned[0]["branch_order"])
            _append_jsonl(output, prefix)
            run_shared_schedule(schedule=planned, model_seats=seats, output=output)
            self.assertEqual(sum(len(s.client.calls) for s in seats.values()), 15)
            before = output.read_bytes()
            run_shared_schedule(schedule=planned, model_seats=seats, output=output)
            self.assertEqual(sum(len(s.client.calls) for s in seats.values()), 15)
            self.assertEqual(output.read_bytes(), before)

    def test_checkpoint_roundtrip_preserves_card_order_and_exact_numeric_state(self):
        seats = models()
        # Engine state keeps more precision than its two-decimal public rendering.
        scenario = load_scenario(PORT)
        scenario["starting_state"]["economic_cost"] = 3.123456789
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scenario.json"
            path.write_text(json.dumps(scenario))
            common = dict(scenario_path=path, model_a=seats["A"], model_b=seats["B"],
                          mediator_model=seats["M"], mode="active", repetition=1,
                          seed=18100, order_seed=20261020, mediator_policy=SHARED_PREFIX)
            prefix = run_match(**common)
            self.assertEqual(prefix["run_status"], "prefix_ready", prefix.get("error"))
            state = prefix["checkpoint"]["state"]
            self.assertNotEqual(state["economic_cost"], round(state["economic_cost"], 2))
            memory = run_match(**common, prefix_checkpoint=prefix, shared_branch="message")
            requests = [copy.deepcopy(s.client.calls[-1]) for s in seats.values()]
            restored = json.loads(json.dumps(prefix, sort_keys=True))
            disk = run_match(**common, prefix_checkpoint=restored, shared_branch="message")
            self.assertEqual(memory["scores"], disk["scores"])
            self.assertEqual(requests, [s.client.calls[-1] for s in seats.values()])

    def test_resume_one_completed_branch(self):
        seats = models()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            original = run_match
            def interrupt_second_branch(**kwargs):
                if kwargs.get("shared_branch") == schedule()[0]["branch_order"][1]:
                    raise KeyboardInterrupt()
                return original(**kwargs)
            with patch('third_chair.shared_prefix.run_match', side_effect=interrupt_second_branch):
                with self.assertRaises(KeyboardInterrupt):
                    run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            before = len(seats["A"].client.calls)
            run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            self.assertEqual(len(seats["A"].client.calls), before + 1)
            self.assertEqual(summarize_shared_records(load_records([output]))["requests"], 15)

    def test_failed_prefix_retained_without_branches_or_replay(self):
        seats = models()
        seats["A"].client.fail_on = {1}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            for _ in range(2):
                run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            summary = summarize_shared_records(load_records([output]))
            self.assertEqual(summary["failed_prefixes"], 1)
            self.assertEqual(summary["successful_branches"], 0)
            self.assertEqual(summary["comparisons"][0]["status"], "incomplete")
            self.assertEqual(len(seats["A"].client.calls), 1)

    def test_failed_message_branch_preserves_control_and_is_not_retried(self):
        seats = models()
        seats["M"].client.fail_on = {1}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            for _ in range(2):
                run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            summary = summarize_shared_records(load_records([output]))
            self.assertEqual(summary["failed_branches"], 1)
            self.assertEqual(summary["successful_branches"], 1)
            self.assertIsNone(summary["comparisons"][0]["cost_reduction"])
            self.assertEqual(len(seats["M"].client.calls), 1)

    def test_resume_rejects_incompatible_provenance_before_calls(self):
        seats = models()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            count = sum(len(s.client.calls) for s in seats.values())
            for field, value in (("temperature", 0.9), ("max_tokens", 800), ("send_seed", True)):
                previous = getattr(seats["A"], field)
                setattr(seats["A"], field, value)
                with self.subTest(field=field), self.assertRaises(ValueError):
                    run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
                setattr(seats["A"], field, previous)
            with patch('third_chair.provenance.source_digest', return_value="changed"):
                with self.assertRaises(ValueError):
                    run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            with patch('third_chair.provenance.shared_protocol_digest', return_value="changed"):
                with self.assertRaises(ValueError):
                    run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            with self.assertRaises(ValueError):
                run_shared_schedule(schedule=schedule(order_seed=99), model_seats=seats, output=output)
            self.assertEqual(sum(len(s.client.calls) for s in seats.values()), count)

    def test_tampered_checkpoint_and_branch_history_rejected(self):
        seats = models()
        prefix = execute(seats)
        prefix["checkpoint"]["intent_a"]["posture"] = "counter_cyber"
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            execute(seats, prefix_checkpoint=prefix, shared_branch="message")
        self.assertFalse(seats["M"].client.calls)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            run_shared_schedule(schedule=schedule(), model_seats=models(), output=output)
            records = load_records([output])
            records[1]["rounds"][0]["public_event"] = "altered"
            with self.assertRaisesRegex(ValueError, "history differs"):
                summarize_shared_records(records)

    def test_interrupted_journal_and_partial_jsonl_block_replay(self):
        seats = models()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            _append_jsonl(output.with_suffix('.jsonl.events.jsonl'), {"match_id": "unfinished"})
            with self.assertRaisesRegex(ValueError, "Interrupted"):
                run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            self.assertFalse(seats["A"].client.calls)
            output.write_text('{"truncated":')
            with self.assertRaisesRegex(ValueError, "Incomplete JSONL"):
                run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)

    def test_real_interrupted_branch_request_cannot_be_replayed(self):
        seats = models()
        seats["M"].client.interrupt_on = {1}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forks.jsonl"
            with self.assertRaises(KeyboardInterrupt):
                run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            count = sum(len(s.client.calls) for s in seats.values())
            with self.assertRaisesRegex(ValueError, "Interrupted"):
                run_shared_schedule(schedule=schedule(), model_seats=seats, output=output)
            self.assertEqual(sum(len(s.client.calls) for s in seats.values()), count)
            self.assertEqual(load_records([output])[0]["run_status"], "prefix_ready")

    def test_changing_actor_identity_excludes_contrast(self):
        seats = models()
        prefix = execute(seats)
        message = execute(seats, prefix_checkpoint=prefix, shared_branch="message")
        seats["A"].client.provider_name = "different-provider"
        control = execute(seats, prefix_checkpoint=prefix, shared_branch="no-message")
        records = [prefix, message, control]
        for record in records:
            record.update(protocol_version="shared-prefix-0.7.0", branch_order=["message", "no-message"])
        summary = summarize_shared_records(records)
        self.assertEqual(summary["complete_comparisons"], 0)
        comparison = summary["comparisons"][0]
        self.assertEqual(comparison["status"], "ineligible")
        self.assertTrue(any("provider" in issue for issue in comparison["issues"]))
        self.assertIsNone(comparison["cost_reduction"])

    def test_two_variant_plan_and_cli_are_offline_and_deterministic(self):
        planned = schedule([PORT, DISCLOSED])
        self.assertEqual(planned, schedule([PORT, DISCLOSED]))
        self.assertEqual(len(planned), 2)
        self.assertEqual({r["seed"] for r in planned}, {18100})
        parser = build_parser()
        args = parser.parse_args(['plan-shared-prefix', '--models', 'unused.json',
                                  '--actor-a', 'A', '--actor-b', 'B', '--mediator', 'M',
                                  '--order-seed', '42'])
        self.assertEqual(args.command, 'plan-shared-prefix')
        for changes in ({"mediator": "A"}, {"order_seed": None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                schedule(**changes)
        seats = models()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'forks.jsonl'
            run_shared_schedule(schedule=planned, model_seats=seats, output=output)
            summary = summarize_shared_records(load_records([output]))
            self.assertEqual(summary['complete_comparisons'], 2)
            self.assertEqual(summary['requests'], 30)
            self.assertEqual(sum(len(s.client.calls) for s in seats.values()), 30)


if __name__ == "__main__":
    unittest.main()
