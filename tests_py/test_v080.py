"""Prospective response contract and anonymized scenario panel; synthetic only."""

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from third_chair.cli import _scenario_paths
from third_chair.client import ModelResponse
from third_chair.policies import (LinkedVerificationPolicy, POLICY_NAME,
                                  validate_delayed_scenario)
from third_chair.provenance import fingerprint, run_manifest
from third_chair.runner import ModelSeat, ScorableResponseError, _call_for_json, run_match
from third_chair.scenario import load_scenario, opaque_evidence_ids
from third_chair.schema import (ACTOR_RESPONSE_CONTRACT, normalize_actor_response,
                                validate_actor_final)
from third_chair.tournament import build_schedule, estimate_calls
from test_audit_regressions import chair, seats
from test_third_chair import actor_final, actor_intent, actor_wire

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "eval_data/scenarios/v080"
PATHS = sorted(PANEL.rglob("*.json"))


class WireClient:
    model = "synthetic/actor"
    provider_metadata_required = True

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, **kwargs):
        self.calls.append(copy.deepcopy(messages))
        response = self.responses.pop(0)
        if isinstance(response, ModelResponse):
            return response
        return ModelResponse(json.dumps(response), self.model, {"cost": .001}, {},
                             finish_reason="stop")


class ResponseContractTests(unittest.TestCase):
    def wire(self):
        value = actor_wire(actor_final(35, "collect", [], accepts=False))
        value["evidence_stances"] = {"E003": "reject", "E001": "support", "E002": "uncertain"}
        return value

    def validate(self, value):
        validate_actor_final(value, postures={"collect"}, known_ids={"E001", "E002", "E003"})

    def call(self, responses):
        client = WireClient(responses)
        events = []
        result = _call_for_json(ModelSeat("fixture", client), [], seed=None,
                                validator=self.validate, event_sink=lambda x: events.append(copy.deepcopy(x)),
                                response_adapter=normalize_actor_response)
        return result, client, events

    def test_one_authoritative_map_preserves_all_stances_and_decisions(self):
        raw = self.wire()
        before = copy.deepcopy(raw)
        value = normalize_actor_response(raw)
        self.validate(value)
        self.assertEqual(value["evidence_ids"], ["E001", "E002", "E003"])
        self.assertEqual({k: v for k, v in value.items() if k != "evidence_ids"}, raw)
        self.assertEqual(raw, before)

    def test_empty_map_is_allowed(self):
        value = self.wire() | {"evidence_stances": {}}
        self.validate(normalize_actor_response(value))

    def test_duplicate_representation_is_rejected_without_silent_repair(self):
        with self.assertRaisesRegex(ValueError, "Omit evidence_ids"):
            normalize_actor_response(self.wire() | {"evidence_ids": ["E001"]})

    def test_bad_stance_and_unavailable_evidence_are_rejected(self):
        for mapping in ({"E001": "believe"}, {"PRIVATE": "support"}, {"E001": None}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                self.validate(normalize_actor_response(self.wire() | {"evidence_stances": mapping}))

    def test_bad_map_types_are_rejected(self):
        for mapping in (None, [], "E001", {1: "support"}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                normalize_actor_response(self.wire() | {"evidence_stances": mapping})

    def test_other_contract_constraints_still_apply(self):
        for fields in ({"posture": "attack"}, {"belief_opponent_responsible": 101},
                       {"accepts_intervention": "yes"}, {"extra": True}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.validate(normalize_actor_response(self.wire() | fields))

    def test_specific_correction_is_bounded_and_raw_content_retained(self):
        bad = self.wire() | {"evidence_ids": ["E001"]}
        (value, attempts), client, events = self.call([bad, self.wire()])
        self.assertEqual(len(client.calls), 2)
        self.assertIn("Omit evidence_ids", client.calls[1][-1]["content"])
        self.assertEqual(json.loads(attempts[0]["content"]), bad)
        self.assertEqual(attempts[1]["actor_response_contract"], ACTOR_RESPONSE_CONTRACT)
        self.assertTrue(attempts[1]["evidence_ids_derived"])
        self.assertEqual(sum(a["usage"]["cost"] for a in attempts), .002)

    def test_second_invalid_response_stops(self):
        bad = self.wire() | {"evidence_ids": []}
        client = WireClient([bad, bad, self.wire()])
        with self.assertRaises(ScorableResponseError) as caught:
            _call_for_json(ModelSeat("fixture", client), [], seed=None, validator=self.validate,
                           event_sink=lambda x: None, response_adapter=normalize_actor_response)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(len(caught.exception.attempts), 2)

    def test_embedded_provider_error_is_not_corrected_even_with_valid_content(self):
        for raw in ({"error": {"code": 502, "message": "synthetic"}},
                    {"choices": [{"error": {"code": 502, "message": "synthetic"}}]}):
            response = ModelResponse(json.dumps(self.wire()), "synthetic/actor", {"cost": .003}, raw,
                                     finish_reason="stop")
            client = WireClient([response, self.wire()])
            with self.subTest(raw=raw), self.assertRaises(ScorableResponseError) as caught:
                _call_for_json(ModelSeat("fixture", client), [], seed=None, validator=self.validate,
                               event_sink=lambda x: None, response_adapter=normalize_actor_response)
            self.assertEqual(len(client.calls), 1)
            attempt = caught.exception.attempts[0]
            self.assertEqual(attempt["status"], "provider_error")
            self.assertEqual(attempt["usage"]["cost"], .003)
            self.assertEqual(attempt["raw_response"], raw)

    def test_json_schemas_match_new_wire_contract(self):
        for name in ("actor-intent", "actor-final"):
            schema = json.loads((ROOT / f"eval_data/schemas/{name}.schema.json").read_text())
            self.assertNotIn("evidence_ids", schema["required"])
            self.assertNotIn("evidence_ids", schema["properties"])
            self.assertIn("evidence_stances", schema["required"])


class ExpandedPanelTests(unittest.TestCase):
    def test_three_families_fully_cross_responsibility_and_authenticity(self):
        self.assertEqual(len(PATHS), 12)
        families = {}
        for path in PATHS:
            scenario = load_scenario(path)
            d = scenario["design"]
            families.setdefault(d["family_id"], set()).add((d["responsibility"], d["document_authenticity"]))
            self.assertEqual(scenario["ground_truth"]["responsible_actor"], d["responsibility"])
            authentic = d["document_authenticity"] == "genuine"
            self.assertEqual(scenario["verification_results"]["D1"]["valid"], authentic)
            self.assertEqual(scenario["ground_truth"]["forged_evidence_ids"], [] if authentic else ["D1"])
            validate_delayed_scenario(scenario)
        self.assertEqual(len(families), 3)
        for conditions in families.values():
            self.assertEqual(conditions, {(r, a) for r in ("state_b", "nonstate") for a in ("genuine", "forged")})

    def test_factor_conditions_keep_initial_public_context_and_opaque_mapping(self):
        for directory in PANEL.iterdir():
            scenarios = [load_scenario(p) for p in sorted(directory.glob("*.json"))]
            for scenario in scenarios[1:]:
                self.assertEqual(scenario["one_line"], scenarios[0]["one_line"])
                self.assertEqual(scenario["seats"]["a"], scenarios[0]["seats"]["a"])
                self.assertEqual(scenario["episodes"][0]["evidence"]["a"], scenarios[0]["episodes"][0]["evidence"]["a"])
                self.assertEqual([e["public_event"] for e in scenario["episodes"]],
                                 [e["public_event"] for e in scenarios[0]["episodes"]])
                self.assertEqual(opaque_evidence_ids(scenario, seed=987, repetition=1)[1],
                                 opaque_evidence_ids(scenarios[0], seed=987, repetition=1)[1])

    def test_real_world_identifiers_are_absent_from_scenario_inputs(self):
        banned = ("viasat", "ka-sat", "colonial", "darkside", "notpetya", "m.e.doc", "russia", "ukraine", "microsoft", "2021", "2022", "2017")
        for path in PATHS:
            content = path.read_text().lower()
            for token in banned:
                self.assertNotIn(token, content)

    def test_legacy_default_stays_separate(self):
        self.assertEqual(len(_scenario_paths("all")), 3)
        self.assertEqual(_scenario_paths("expanded-v080"), PATHS)
        self.assertTrue(set(_scenario_paths("all")).isdisjoint(PATHS))

    def test_unchanged_postures_and_new_manifest_identity(self):
        legacy = load_scenario(ROOT / "eval_data/scenarios/port-sanctions.json")
        for path in PATHS:
            scenario = load_scenario(path)
            self.assertEqual(scenario["postures"], legacy["postures"])
            manifest = run_manifest(scenario, seats())
            self.assertEqual(manifest["actor_response_contract"], ACTOR_RESPONSE_CONTRACT)
            self.assertEqual(manifest["scoring_version"], "baseline-0.4.0")
            old = {k: v for k, v in manifest.items() if k not in ("actor_response_contract", "configuration_id")}
            self.assertNotEqual(fingerprint(old), manifest["configuration_id"])

    def test_all_conditions_and_primary_arms_run_offline_with_delayed_checks(self):
        with patch("socket.socket", side_effect=AssertionError("Network forbidden in synthetic test")):
            for path in PATHS:
                scenario = load_scenario(path)
                for policy in ("llm", POLICY_NAME):
                    for mode in ("active", "empty"):
                        with self.subTest(path=path.name, policy=policy, mode=mode):
                            a_outputs = []
                            for ids in (["A1"], ["A1", "D1"], ["A3"]):
                                a_outputs.extend([actor_intent(35, "collect", ids),
                                                  actor_final(35, "collect", ids, accepts=False)])
                            models = seats(a=a_outputs, mediator=[chair("verify", "A1"), chair("verify", "D1")])
                            if policy == POLICY_NAME:
                                models["M"] = ModelSeat("M", LinkedVerificationPolicy())
                            record = run_match(scenario_path=path, model_a=models["A"], model_b=models["B"],
                                               mediator_model=models["M"], mode=mode, repetition=1, seed=88001,
                                               evidence_id_mode="original", mediator_policy=policy)
                            self.assertEqual(record["run_status"], "succeeded", record.get("error"))
                            self.assertFalse(record["rounds"][0]["delivered_verifications"])
                            self.assertNotIn("D1", [c["target_id"] for c in record["rounds"][1]["delivered_verifications"]])
                            final_checks = record["rounds"][2]["delivered_verifications"]
                            if mode == "active":
                                check = next(c for c in final_checks if c["target_id"] == "D1")
                                self.assertEqual(check["valid"], scenario["verification_results"]["D1"]["valid"])
                            else:
                                self.assertEqual(final_checks, [])
                            a_first = json.dumps(models["A"].client.calls[0])
                            self.assertNotIn(scenario["seats"]["b"]["private_brief"], a_first)
                            self.assertNotIn(scenario["episodes"][2]["evidence"]["a"][0]["content"], a_first)
                            self.assertNotIn('"evidence_ids"', a_first)
                            if policy == "llm" and mode == "active":
                                mediator_first = json.dumps(models["M"].client.calls[0])
                                self.assertNotIn(scenario["seats"]["b"]["private_brief"], mediator_first)
                                self.assertNotIn(scenario["ground_truth"]["note"], mediator_first)
                                self.assertNotIn(scenario["episodes"][0]["evidence"]["a"][0]["content"], mediator_first)

    def test_proposed_panel_schedule_counts_and_randomized_order(self):
        all_rows = []
        for policy in ("llm", POLICY_NAME):
            rows = build_schedule(scenario_paths=PATHS, labels=["A", "B", "M"], rotation="balanced",
                                  modes=["active", "empty"], repetitions=5, seed=88000,
                                  fixed_a="A", fixed_b="B", mediator_label="M" if policy == "llm" else None,
                                  mediator_policy=policy, order_seed=20261021)
            self.assertEqual(len(rows), 120)
            self.assertEqual({r["mode"] for r in rows}, {"active", "empty"})
            all_rows.extend(rows)
        self.assertEqual(len(all_rows), 240)
        self.assertEqual(estimate_calls(all_rows), 3060)


if __name__ == "__main__":
    unittest.main()
