"""Provider-control regressions; all HTTP responses are simulated, never live results."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from third_chair.analysis import summarize_records
from third_chair.cli import build_parser
from third_chair.client import ModelResponse, OpenAICompatibleClient, response_provider
from third_chair.provenance import seat_config
from third_chair.runner import ModelSeat, _call_for_json, ScorableResponseError, run_match
from third_chair.tournament import (
    build_model_seats, build_schedule, configuration_issues, load_model_configs, run_schedule,
)
from test_audit_regressions import CaptureClient, SCENARIO, fixture_pair


def config_data():
    return {"models": [dict(
        label=label, model=f"vendor/{label}", base_url="https://openrouter.ai/api/v1",
        api_key_env="THIRD_CHAIR_TEST_KEY", temperature=None, max_tokens=4096,
        send_seed=False, timeout=45,
        provider={"only": ["pinned-host/region"], "allow_fallbacks": False,
                  "require_parameters": True},
        reasoning={"max_tokens": 1024},
    ) for label in ("A", "B", "M")]}


def load_config(data):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "models.json"
        path.write_text(json.dumps(data))
        return load_model_configs(path)


def http_response(raw):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(raw).encode()
    return response


def controlled_pair():
    pair = fixture_pair()
    for record in pair:
        record["manifest"] = {"roles": {
            role: {"provider_metadata_required": True} for role in ("a", "b", "mediator")
        }}
        called = ("a", "b", "mediator") if record["mode"] == "active" else ("a", "b")
        record["returned_models"] = {role: [role] for role in called}
        record["returned_providers"] = {role: ["PinnedHost"] for role in called}
        record["missing_provider_responses"] = {role: 0 for role in called}
    return pair


class ConfigurationTests(unittest.TestCase):
    @patch.dict("os.environ", {"THIRD_CHAIR_TEST_KEY": "SECRET"})
    def test_settings_reach_seats_and_manifest_without_credentials(self):
        configs = load_config(config_data())
        self.assertEqual(configuration_issues(configs), [])
        seat = build_model_seats(configs)["A"]
        settings = seat_config(seat)
        self.assertEqual(settings["max_tokens"], 4096)
        self.assertEqual(settings["reasoning"], {"max_tokens": 1024})
        self.assertEqual(settings["provider"]["only"], ["pinned-host/region"])
        self.assertIsNone(settings["temperature"])
        self.assertFalse(settings["send_seed"])
        self.assertTrue(settings["provider_metadata_required"])
        self.assertEqual(seat.client.extra_headers["X-OpenRouter-Metadata"], "enabled")
        self.assertNotIn("SECRET", json.dumps(settings))

    def test_unknown_or_invalid_settings_cannot_be_silently_ignored(self):
        changes = [
            {"max_token": 4000}, {"max_tokens": True}, {"max_tokens": 0},
            {"temperature": "0.2"}, {"temperature": float("nan")},
            {"send_seed": "false"}, {"timeout": -1},
            {"provider": {"only": "host"}}, {"provider": {"allow_fallbacks": "false"}},
            {"provider": {"unknown": True}}, {"reasoning": {"effort": "invalid"}},
            {"reasoning": {"effort": "low", "max_tokens": 1024}},
            {"reasoning": {"max_tokens": 4096}},
            {"reasoning": {"enabled": False, "effort": "high"}},
        ]
        for change in changes:
            with self.subTest(change=change):
                data = config_data()
                data["models"][0].update(change)
                with self.assertRaises(ValueError):
                    load_config(data)

    @patch.dict("os.environ", {}, clear=True)
    def test_offline_check_detects_missing_key_placeholders_and_uncontrolled_routes(self):
        data = config_data()
        data["models"][0].update(model="replace-with-exact-model-id", provider=None)
        issues = configuration_issues(load_config(data))
        self.assertTrue(any("placeholder" in item for item in issues))
        self.assertTrue(any("environment variable" in item for item in issues))
        self.assertTrue(any("provider.only" in item for item in issues))
        self.assertTrue(any("allow_fallbacks" in item for item in issues))
        self.assertTrue(any("require_parameters" in item for item in issues))

    @patch.dict("os.environ", {"THIRD_CHAIR_TEST_KEY": "SECRET"})
    def test_check_config_is_free_and_run_rejects_bad_setup_before_http(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "models.json"
            data = config_data()
            path.write_text(json.dumps(data))
            with patch("urllib.request.urlopen") as http, redirect_stdout(io.StringIO()) as output:
                args = build_parser().parse_args(["check-config", "--models", str(path)])
                self.assertEqual(args.func(args), 0)
                data["models"][0]["provider"]["allow_fallbacks"] = True
                path.write_text(json.dumps(data))
                self.assertEqual(args.func(args), 1)
                args = build_parser().parse_args(["run", "--models", str(path)])
                with self.assertRaisesRegex(ValueError, "Configuration is not ready"):
                    args.func(args)
                http.assert_not_called()
                self.assertNotIn("SECRET", output.getvalue())

    def test_old_generic_configuration_keeps_defaults(self):
        data = {"models": [dict(label=label, base_url="https://example.test/v1",
                               model=label, api_key_env="KEY") for label in ("A", "B", "M")]}
        config = load_config(data)[0]
        self.assertEqual(config.max_tokens, 1400)
        self.assertEqual(config.temperature, 0.2)
        self.assertTrue(config.send_seed)
        self.assertIsNone(config.provider)


class RequestAndResponseTests(unittest.TestCase):
    @patch.dict("os.environ", {"THIRD_CHAIR_TEST_KEY": "SECRET"})
    def test_http_request_and_journal_match_through_complete_paired_matches(self):
        models = build_model_seats(load_config(config_data()))
        requests = []

        def serve(request, timeout):
            payload = json.loads(request.data)
            requests.append(payload)
            self.assertEqual(timeout, 45)
            self.assertEqual(request.get_header("X-openrouter-metadata"), "enabled")
            self.assertNotIn("temperature", payload)
            self.assertNotIn("seed", payload)
            self.assertEqual(payload["max_tokens"], 4096)
            self.assertEqual(payload["reasoning"], {"max_tokens": 1024})
            self.assertFalse(payload["provider"]["allow_fallbacks"])
            value = CaptureClient(payload["model"]).chat(payload["messages"])
            return http_response({
                "model": payload["model"], "provider": "PinnedHost",
                "choices": [{"finish_reason": "stop", "message": {"content": value.content}}],
                "usage": {"completion_tokens": 120, "cost": 0.0001,
                          "completion_tokens_details": {"reasoning_tokens": 50}},
            })

        records = []
        with patch("urllib.request.urlopen", side_effect=serve):
            for mode in ("active", "empty"):
                record = run_match(scenario_path=SCENARIO, model_a=models["A"],
                                   model_b=models["B"], mediator_model=models["M"],
                                   mode=mode, repetition=1, seed=12)
                self.assertEqual(record["run_status"], "succeeded", record.get("error"))
                records.append(record)
        journal = [e["request"] for record in records for e in record["events"]
                   if e["status"] == "succeeded"]
        self.assertEqual(requests, journal)
        self.assertEqual(records[0]["returned_providers"]["mediator"], ["PinnedHost"])
        summary = summarize_records(records)
        self.assertEqual(summary["complete_active_empty_pairs"], 1)
        self.assertEqual(summary["pairs"][0]["returned_providers"]["a"], ["PinnedHost"])

    def test_provider_metadata_is_extracted_without_guessing_missing_values(self):
        self.assertEqual(response_provider({"provider": "Host"}), "Host")
        raw = {"openrouter_metadata": {"endpoints": {"available": [
            {"provider": "Wrong", "selected": False}, {"provider": "Host", "selected": True}
        ]}}}
        self.assertEqual(response_provider(raw), "Host")
        raw["openrouter_metadata"]["endpoints"]["available"][0]["selected"] = True
        self.assertIsNone(response_provider(raw))
        self.assertIsNone(response_provider({"model": "vendor/model"}))
        self.assertIsNone(response_provider({"openrouter_metadata": {"endpoints": None}}))

    def test_null_content_and_length_finish_keep_usage_without_json_retry(self):
        client = OpenAICompatibleClient(base_url="https://openrouter.ai/api/v1",
                                        api_key="SECRET", model="vendor/model")
        raw = {"model": "vendor/model", "provider": "Host", "choices": [
            {"finish_reason": "length", "message": {"content": None}}
        ], "usage": {"completion_tokens": 1400,
                     "completion_tokens_details": {"reasoning_tokens": 1400}}}
        events = []
        with patch("urllib.request.urlopen", return_value=http_response(raw)) as http:
            with self.assertRaises(ScorableResponseError):
                _call_for_json(ModelSeat("test", client), [], seed=10,
                               validator=lambda _: None, event_sink=lambda e: events.append(copy.deepcopy(e)))
            self.assertEqual(http.call_count, 1)
        self.assertEqual(events[-1]["status"], "incomplete_response")
        self.assertEqual(events[-1]["content"], "")
        self.assertEqual(events[-1]["usage"], raw["usage"])
        self.assertEqual(events[-1]["raw_response"], raw)

    def test_truncated_but_parseable_json_and_blocked_responses_are_not_scored(self):
        for reason in (None, "length", "content_filter", "error", "tool_calls"):
            with self.subTest(reason=reason):
                client = MagicMock(model="m", provider=None, reasoning=None)
                client.chat.return_value = ModelResponse("{}", "m", {}, {}, finish_reason=reason)
                validator = MagicMock()
                with self.assertRaises(ScorableResponseError):
                    _call_for_json(ModelSeat("m", client), [], seed=1, validator=validator,
                                   event_sink=lambda _: None)
                validator.assert_not_called()
                client.chat.assert_called_once()

    @patch.dict("os.environ", {"THIRD_CHAIR_TEST_KEY": "SECRET"})
    def test_resume_rejects_changed_provider_reasoning_or_sampling_settings(self):
        configs = load_config(config_data())
        models = build_model_seats(configs)
        for seat in models.values():
            seat.client.chat = CaptureClient(seat.client.model).chat
        plan = build_schedule(scenario_paths=[SCENARIO], labels=list(models), rotation="balanced",
                              modes=["empty"], repetitions=1, seed=1)[:1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "matches.jsonl"
            run_schedule(schedule=plan, model_seats=models, output=output)
            for change in ({"provider": {"only": ["different-host"]}},
                           {"reasoning": {"effort": "low"}}, {"max_tokens": 8000},
                           {"send_seed": True}, {"temperature": 0.2}):
                with self.subTest(change=change):
                    data = config_data()
                    data["models"][0].update(change)
                    changed = build_model_seats(load_config(data))
                    with self.assertRaisesRegex(ValueError, "configuration changed"):
                        run_schedule(schedule=plan, model_seats=changed, output=output)


class ProviderAnalysisTests(unittest.TestCase):
    def test_matching_provider_pair_is_eligible(self):
        self.assertEqual(summarize_records(controlled_pair())["complete_active_empty_pairs"], 1)

    def test_different_actor_providers_do_not_pair(self):
        pair = controlled_pair()
        pair[1]["returned_providers"]["a"] = ["OtherHost"]
        summary = summarize_records(pair)
        self.assertEqual(summary["complete_active_empty_pairs"], 0)
        self.assertTrue(any("actor providers differ" in warning for warning in summary["warnings"]))

    def test_missing_provider_on_even_one_response_is_not_treated_as_a_match(self):
        for field in ("missing_provider_responses", "missing_model_responses"):
            with self.subTest(field=field):
                pair = controlled_pair()
                pair[0][field] = {"a": 1}
                self.assertEqual(summarize_records(pair)["complete_active_empty_pairs"], 0)

    def test_mixed_provider_or_model_within_match_is_excluded_even_if_sets_match(self):
        for field in ("returned_providers", "returned_models"):
            for role in ("a", "mediator"):
                with self.subTest(field=field, role=role):
                    pair = controlled_pair()
                    pair[0][field][role] = ["one", "two"]
                    pair[1][field][role] = ["one", "two"]
                    self.assertEqual(summarize_records(pair)["complete_active_empty_pairs"], 0)

    def test_changed_mediator_provider_separates_report_rows(self):
        first = controlled_pair()
        second = copy.deepcopy(first)
        for record in second:
            record["repetition"] = 2
        second[0]["returned_providers"]["mediator"] = ["OtherHost"]
        summary = summarize_records(first + second)
        self.assertEqual(summary["complete_active_empty_pairs"], 2)
        self.assertEqual(len(summary["mediators"]), 2)


if __name__ == "__main__":
    unittest.main()
