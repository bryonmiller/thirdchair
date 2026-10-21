"""Offline coverage, information equality and numerical power checks."""

import copy
import io
import json
import math
import random
import tempfile
import unittest
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from third_chair.cli import _scenario_paths, build_parser
from third_chair.panel import panel_contract, validate_panel_schedule
from third_chair.power import paired_t_power, required_repetitions, scheduled_power, t_critical
from third_chair.runner import run_match
from third_chair.scenario import load_scenario, opaque_evidence_ids
from third_chair.tournament import build_schedule, run_schedule
from test_audit_regressions import seats

ROOT = Path(__file__).resolve().parents[1]


class CompletePanelTests(unittest.TestCase):
    def setUp(self):
        self.kwargs = dict(scenario_paths=_scenario_paths("expanded-v080"),
                           labels=["A", "B", "M"], rotation="full", modes=["active", "empty"],
                           repetitions=2, seed=188000, order_seed=20261022, complete_panel=True)
        self.rows = build_schedule(**self.kwargs)
        self.contract = panel_contract(self.rows)

    def test_each_model_gets_every_condition_in_every_role_and_arm(self):
        counts = Counter((r["scenario_id"], r["mode"], r["repetition"], role, r[role])
                         for r in self.rows for role in ("a", "b", "mediator"))
        self.assertEqual(len(counts), 24 * 2 * 2 * 3 * 3)
        self.assertEqual(set(counts.values()), {2})
        self.assertEqual(validate_panel_schedule(self.rows, self.contract)["matches"], 576)
        self.assertEqual(self.rows, build_schedule(**self.kwargs))

    def test_common_mapping_across_truth_cells_roles_and_arms(self):
        mappings = defaultdict(set)
        seeds_by_family = defaultdict(set)
        for r in self.rows:
            scenario = load_scenario(r["scenario_path"])
            key = (scenario["design"]["family_id"], r["repetition"])
            mappings[key].add(json.dumps(opaque_evidence_ids(scenario, seed=r["seed"],
                                                           repetition=r["repetition"])[1], sort_keys=True))
            seeds_by_family[key].add(r["seed"])
        self.assertEqual({len(v) for v in mappings.values()}, {1})
        self.assertEqual(len({next(iter(v)) for v in seeds_by_family.values()}), 12)

    def test_missing_arm_condition_assignment_or_repeat_and_duplicates_rejected(self):
        variants = [self.rows[:-1], self.rows + [self.rows[0]],
                    [r for r in self.rows if r["scenario_id"] != self.rows[0]["scenario_id"]],
                    [r for r in self.rows if r["repetition"] == 1],
                    [r for r in self.rows if (r["a"], r["b"], r["mediator"]) != ("A", "B", "M")]]
        for rows in variants:
            with self.subTest(count=len(rows)), self.assertRaises(ValueError):
                validate_panel_schedule(rows, self.contract)

    def test_order_seed_roles_and_provenance_drift_rejected(self):
        for field, value in (("seed", 0), ("a", "M"), ("scenario_sha256", "bad"),
                             ("order_seed", 123), ("coverage_design", "other")):
            rows = copy.deepcopy(self.rows)
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_panel_schedule(rows, self.contract)
        with self.assertRaises(ValueError):
            validate_panel_schedule(list(reversed(self.rows)), self.contract)

    def test_incomplete_design_inputs_rejected(self):
        for changes in ({"rotation": "balanced"}, {"modes": ["active"]},
                        {"labels": ["A", "B", "M", "X"]}, {"order_seed": None},
                        {"seed": None}, {"scenario_paths": self.kwargs["scenario_paths"][:-1]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                build_schedule(**(self.kwargs | changes))

    def test_invalid_coverage_stops_before_dispatch_or_output_creation(self):
        with tempfile.TemporaryDirectory() as directory, patch("third_chair.tournament.run_match") as run:
            output = Path(directory) / "results.jsonl"
            for contract in (None, self.contract):
                with self.assertRaises(ValueError):
                    run_schedule(schedule=self.rows[:-1], model_seats={}, output=output,
                                 coverage_contract=contract)
            run.assert_not_called()
            self.assertFalse(output.exists())

    def test_cli_offline_plan_freezes_contract_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory, patch("socket.socket", side_effect=AssertionError):
            path = Path(directory) / "plan.json"
            args = ["plan", "--models", str(ROOT / "eval_data/models.example.json"),
                    "--scenario", "expanded-v080", "--rotation", "full", "--order-seed", "123",
                    "--plan-output", str(path)]
            with redirect_stdout(io.StringIO()):
                parsed = build_parser().parse_args(args)
                self.assertEqual(parsed.func(parsed), 0)
                with self.assertRaises(FileExistsError):
                    parsed.func(parsed)
            frozen = json.loads(path.read_text())
            validate_panel_schedule(frozen["schedule"], frozen["coverage_contract"])

    def test_frozen_source_and_scenario_drift_rejected(self):
        with patch("third_chair.panel.source_digest", return_value="changed"):
            with self.assertRaises(ValueError):
                validate_panel_schedule(self.rows, self.contract)
        def changed(path):
            value = load_scenario(path)
            value["mediator_brief"] += " Synthetic drift."
            return value
        with patch("third_chair.tournament.load_scenario", side_effect=changed):
            with self.assertRaises(ValueError):
                validate_panel_schedule(self.rows, self.contract)

    def test_resume_preserves_failed_cells_and_requires_same_full_contract(self):
        rows = build_schedule(**(self.kwargs | {"repetitions": 1}))
        contract = panel_contract(rows)
        calls = 0
        def synthetic_run(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                original = kwargs["model_a"]
                replacement = seats(a=[ValueError("synthetic failure")])["A"]
                replacement.client.model = original.client.model
                kwargs["model_a"] = type(original)(original.label, replacement.client)
            return run_match(**kwargs)
        models = seats()
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), \
                patch("socket.socket", side_effect=AssertionError("No network")), \
                patch("third_chair.tournament.os.fsync"), \
                patch("third_chair.tournament.run_match", side_effect=synthetic_run) as run:
            output = Path(directory) / "results.jsonl"
            run_schedule(schedule=rows, model_seats=models, output=output, coverage_contract=contract)
            before = output.read_bytes()
            records = [json.loads(line) for line in before.splitlines()]
            self.assertEqual(len(records), 288)
            self.assertEqual(records[0]["run_status"], "failed")
            self.assertEqual(sum(r["run_status"] == "succeeded" for r in records), 287)
            run.reset_mock()
            run_schedule(schedule=rows, model_seats=models, output=output, coverage_contract=contract)
            run.assert_not_called()
            self.assertEqual(before, output.read_bytes())

    def test_same_role_has_same_initial_inputs_for_all_models_every_condition(self):
        # Synthetic actors always make identical intentions. Compare messages,
        # not generated trajectories. Later responses may legitimately diverge.
        prompts = defaultdict(dict)
        with patch("socket.socket", side_effect=AssertionError("No network")):
            for row in self.rows:
                if row["mode"] != "active" or row["repetition"] != 1:
                    continue
                models = seats()
                result = run_match(scenario_path=row["scenario_path"], model_a=models[row["a"]],
                                   model_b=models[row["b"]], mediator_model=models[row["mediator"]],
                                   mode="active", repetition=1, seed=row["seed"])
                self.assertEqual(result["run_status"], "succeeded")
                for role in ("a", "b", "mediator"):
                    prompt = models[row[role]].client.calls[0]["messages"]
                    key = (row["scenario_id"], role)
                    prior = prompts[key]
                    if prior:
                        self.assertEqual(prompt, next(iter(prior.values())))
                    prior[row[role]] = prompt
        self.assertEqual(len(prompts), 24*3)
        self.assertTrue(all(set(p) == {"A", "B", "M"} for p in prompts.values()))


class PowerTests(unittest.TestCase):
    def test_known_student_t_quantiles_and_cauchy_identity(self):
        self.assertAlmostEqual(t_critical(10, .05), 2.2281388519649385, places=10)
        self.assertAlmostEqual(t_critical(30, .05), 2.0422724563012373, places=10)
        self.assertAlmostEqual(t_critical(1, .05), 1/math.tan(math.pi*.05/2), places=10)

    def test_null_size_and_quadrature_convergence(self):
        for n in (2, 10, 109, 322):
            for alpha in (.05, .05/288):
                self.assertAlmostEqual(paired_t_power(n, 0, alpha), alpha, places=9)
                self.assertAlmostEqual(paired_t_power(n, .5, alpha),
                                       paired_t_power(n, .5, alpha, steps=2080), places=9)

    def test_minimum_n_and_multiplicity(self):
        self.assertEqual(required_repetitions(.5, .8, 1, 1.), 34)
        self.assertEqual(required_repetitions(.5, .9, 288, 1.), 109)
        n = required_repetitions()
        self.assertEqual(n, 121)
        self.assertGreaterEqual(scheduled_power(n, .5, .05/288, .9), .9)
        self.assertLess(scheduled_power(n-1, .5, .05/288, .9), .9)

    def test_missing_pairs_and_effect_sensitivity(self):
        self.assertLess(scheduled_power(121, .5, .05/288, .8), .9)
        self.assertGreater(required_repetitions(.3), required_repetitions(.5))
        self.assertGreater(required_repetitions(.5), required_repetitions(.8))

    def test_independent_monte_carlo_checks_noncentral_t_and_missingness(self):
        rng = random.Random(20261021)
        repetitions = 20000
        hits = 0
        for _ in range(repetitions):
            n = sum(rng.random() < .9 for _ in range(121))
            statistic = (rng.gauss(0, 1) + .5*math.sqrt(n)) / math.sqrt(rng.gammavariate((n-1)/2, 2)/(n-1))
            hits += abs(statistic) > t_critical(n-1, .05/288)
        expected = scheduled_power(121, .5, .05/288, .9)
        self.assertLess(abs(hits/repetitions - expected), 4*math.sqrt(expected*(1-expected)/repetitions))

    def test_invalid_parameters_fail(self):
        for effect in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                required_repetitions(effect)
        for completion in (0, -1, 1.1):
            with self.assertRaises(ValueError):
                required_repetitions(completion=completion)


if __name__ == "__main__":
    unittest.main()
