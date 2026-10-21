"""Print reproducible prospective power sensitivities. No model configuration is read."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from third_chair.power import required_repetitions, scheduled_power


def main():
    rows = []
    for effect in (.3, .5, .8):
        for completion in (1., .9):
            n = required_repetitions(effect=effect, completion=completion)
            rows.append({"paired_standardized_effect": effect,
                         "pair_completion_probability": completion,
                         "repetitions_per_condition_assignment_arm": n,
                         "matches": 288*n, "planned_turns": 3888*n,
                         "power_per_test": scheduled_power(n, effect, .05/288, completion)})
    print(json.dumps({"kind": "prospective_assumptions_not_research_results",
                      "conditions": 24, "seat_assignments": 6, "endpoints": 2,
                      "hypotheses": 288, "family_alpha": .05, "target_power": .9,
                      "method": "two-sided paired t; conservative Bonferroni planning for Holm analysis",
                      "recommended_effect": .5, "recommended_pair_completion": .9,
                      "sensitivity": rows}, indent=2))


if __name__ == "__main__":
    main()
