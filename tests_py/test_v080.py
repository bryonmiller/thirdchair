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
    def test_six_families_fully_cross_responsibility_and_authenticity(self):
        self.assertEqual(len(PATHS), 24)
        families = {}
        for path in PATHS:
            scenario = load_scenario(path)
            d = scenario["design"]
            families.setdefault(d["family_id"], set()).add((d["responsibility"], d["document_authenticity"]))
            self.assertEqual(scenario["ground_truth"]["responsible_actor"], d["responsibility"])
            authentic = d["document_authenticity"] == "genuine"
            target = self.document_id(scenario)
            self.assertEqual(scenario["verification_results"][target]["valid"], authentic)
            self.assertEqual(scenario["ground_truth"]["forged_evidence_ids"], [] if authentic else [target])
            validate_delayed_scenario(scenario)
        self.assertEqual(set(families), {"grid-vote", "port-sanctions", "archive-talks",
                                         "satellite-outage", "pipeline-shutdown", "software-cascade"})
        for conditions in families.values():
            self.assertEqual(conditions, {(r, a) for r in ("state_b", "nonstate") for a in ("genuine", "forged")})

    @staticmethod
    def document_id(scenario):
        return scenario["episodes"][1]["evidence"]["mediator"][0]["verification_targets"][0]

    def test_authenticity_changes_only_document_validity_and_check(self):
        for directory in sorted(PANEL.iterdir()):
            for responsibility in ("nonstate", "state_b"):
                scenarios = [load_scenario(directory / f"{directory.name}-{responsibility}-{a}.json")
                             for a in ("genuine", "forged")]
                normalized = []
                for scenario in scenarios:
                    target = self.document_id(scenario)
                    value = copy.deepcopy(scenario)
                    value.pop("id")
                    value["design"].pop("document_authenticity")
                    value["ground_truth"].pop("forged_evidence_ids")
                    value["ground_truth"].pop("note")
                    value["verification_results"][target].pop("valid")
                    value["verification_results"][target].pop("content")
                    for ep in value["episodes"]:
                        for cards in ep["evidence"].values():
                            for card in cards:
                                if card["id"] == target:
                                    card.pop("valid")
                    normalized.append(value)
                self.assertEqual(normalized[0], normalized[1], (directory.name, responsibility))

    def test_responsibility_does_not_change_the_document_claim_or_check(self):
        for directory in sorted(PANEL.iterdir()):
            for authenticity in ("genuine", "forged"):
                scenarios = [load_scenario(directory / f"{directory.name}-{r}-{authenticity}.json")
                             for r in ("nonstate", "state_b")]
                target = self.document_id(scenarios[0])
                for key in ("verification_results", "starting_state", "postures"):
                    if key == "verification_results":
                        self.assertEqual(scenarios[0][key][target], scenarios[1][key][target])
                    else:
                        self.assertEqual(scenarios[0][key], scenarios[1][key])
                self.assertNotEqual(scenarios[0]["seats"]["b"]["private_brief"],
                                    scenarios[1]["seats"]["b"]["private_brief"])
                decisive = set(scenarios[0]["ground_truth"]["decisive_evidence_ids"])
                evidence = [[c["content"] for ep in s["episodes"] for c in ep["evidence"]["a"]
                             if c["id"] in decisive] for s in scenarios]
                self.assertNotEqual(evidence[0], evidence[1])

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
                target = self.document_id(scenario)
                first_id = scenario["episodes"][0]["evidence"]["a"][0]["id"]
                final_id = scenario["ground_truth"]["decisive_evidence_ids"][0]
                for policy in ("llm", POLICY_NAME):
                    for mode in ("active", "empty"):
                        with self.subTest(path=path.name, policy=policy, mode=mode):
                            a_outputs = []
                            for ids in ([first_id], [first_id, target], [final_id]):
                                a_outputs.extend([actor_intent(35, "collect", ids),
                                                  actor_final(35, "collect", ids, accepts=False)])
                            models = seats(a=a_outputs, mediator=[chair("verify", first_id), chair("verify", target)])
                            if policy == POLICY_NAME:
                                models["M"] = ModelSeat("M", LinkedVerificationPolicy())
                            record = run_match(scenario_path=path, model_a=models["A"], model_b=models["B"],
                                               mediator_model=models["M"], mode=mode, repetition=1, seed=88001,
                                               evidence_id_mode="original", mediator_policy=policy)
                            self.assertEqual(record["run_status"], "succeeded", record.get("error"))
                            self.assertFalse(record["rounds"][0]["delivered_verifications"])
                            self.assertNotIn(target, [c["target_id"] for c in record["rounds"][1]["delivered_verifications"]])
                            final_checks = record["rounds"][2]["delivered_verifications"]
                            if mode == "active":
                                check = next(c for c in final_checks if c["target_id"] == target)
                                self.assertEqual(check["valid"], scenario["verification_results"][target]["valid"])
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
            self.assertEqual(len(rows), 240)
            self.assertEqual({r["mode"] for r in rows}, {"active", "empty"})
            all_rows.extend(rows)
        self.assertEqual(len(all_rows), 480)
        self.assertEqual(estimate_calls(all_rows), 6120)

    def test_full_rotation_covers_every_condition_assignment_and_control(self):
        kwargs = dict(scenario_paths=_scenario_paths("expanded-v080"), labels=["A", "B", "M"],
                      rotation="full", modes=["active", "empty"], repetitions=5,
                      seed=188000, order_seed=20261022, complete_panel=True)
        rows = build_schedule(**kwargs)
        self.assertEqual(len(rows), 1440)
        self.assertEqual(estimate_calls(rows), 19440)
        self.assertEqual(len({r["match_id"] for r in rows}), 1440)
        self.assertEqual(rows, build_schedule(**kwargs))
        coverage = {}
        for row in rows:
            assignment = (row["a"], row["b"], row["mediator"])
            self.assertEqual(set(assignment), {"A", "B", "M"})
            key = (row["scenario_id"], row["repetition"], assignment)
            coverage.setdefault(key, []).append(row)
        self.assertEqual(len(coverage), 720)
        for pair in coverage.values():
            self.assertEqual({r["mode"] for r in pair}, {"active", "empty"})
            self.assertEqual(pair[0]["seed"], pair[1]["seed"])


if __name__ == "__main__":
    unittest.main()
