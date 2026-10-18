# Evidence-access diagnostic within the mediation study: 0.5.0

Status: prospective development protocol written after reviewing the 0.4.3 exploratory pilot and repeated runs. It is not a registered confirmatory study. See the [methodology review and sources](methodology_review.md). The old [pilot protocol](preregistration.md) and original scenario files remain preserved.

## Role in the mediation study

The overarching question remains: **Can AI mediators de-escalate simulated interstate crises while preserving accurate attribution and avoiding unjustified concessions?** This bounded diagnostic examines an information-access problem exposed by the pilot. It supports subsequent evaluation of communication and reciprocal de-escalation. It does not replace the mediation objective or test all of it.

## Diagnostic question and estimands

Does making a relevant infrastructure-history fact public change reported attribution and wrongful-blame actions, and does an LLM mediator improve those outcomes beyond a simple same-information verification policy?

For this diagnostic only, within each scenario variant and exact actor/policy configuration, the primary descriptive contrast is mean paired final attribution Brier improvement: empty minus active. Compare original versus disclosure **within the same policy and release**, reporting their separate means before any difference-in-differences. A disclosure effect in the empty condition indicates information access matters even without mediation. An interaction is evidence about this environment, not proof that information access is the sole cause of previous errors.

Secondary: final false public attribution, any wrong-target action, the four modeled cost components, legacy cost lift, selected verification target and delivery time, repeated/terminal requests, unsupported assertions in prose, voluntary holds, forced holds, and completion/correction rates. Human ratings concern visible support at decision time and outcome truth in separate passes. No single safety score or overall winner.

## Conditions and freeze

Use fixed State A and B configurations, the original `port-sanctions` and its `port-sanctions-disclosed` variant, and active/empty conditions for every policy. Three configured LLM mediator candidates remain a practical exploratory comparator; the deterministic policy is a fourth candidate. Their communication strategies differ, so this does not isolate learning architecture or generative capacity.

These conditions compare no mediation, a verification policy with a neutral request announcement, and a full LLM mediator allowed to communicate, verify, or abstain. The full mediator may itself choose only verification. Inspect actual channel use before interpreting a contrast as evidence about communication. Full-policy versus scripted-policy differences also include verification selection and timing; a later communication ablation must match those factors and budgets before attributing an effect to messages alone.

The disclosure variant releases the existing H03 registry card publicly at the start of round two. It gives no truth label, does not consume a mediator intervention, and is present in active and empty conditions. Both versions retain the same truth, event text, private objectives, verification mechanism, and cost dynamics. Matching family/evidence namespaces preserve ID permutations at the same repetition and seed. Metadata and titles are evaluator-only. Model prompts cannot see family IDs, variant labels, or the answer key.

The scripted `linked-verification` policy receives a whitelist of the information available in the LLM mediator prompt: public state, current announced positions, authorized history, completed checks, neutral cards, checkable IDs, time, and budget. It never receives private actor reasons, concealed card contents, validity labels, or future check results. It:

1. Holds when no budget remains or a delayed check cannot arrive before the final decision.
2. Selects an unchecked target linked by an available neutral card.
3. Otherwise selects a cited ID with conflicting support/reject stances.
4. Otherwise selects an unchecked available ID, breaking ties by the opaque ID.

Its announcement names only the selected ID and does not invent its contents. This policy is a transparent, post-pilot development comparator. It is neither an oracle nor an optimal planner. Neutral-link cues and ID ordering can favor it; vary those in future held-out families.

Freeze the merged commit, model configuration hash, exact model/provider settings, prompts, correction policy, both scenario hashes, and schedule seed before a batch. All 0.5.0 actors receive clarified probability and trust-scale instructions; no 0.4.3 control can substitute for a 0.5.0 control. All original logs remain unchanged. `measurement_version=evidence-audit-1` labels post-hoc reanalysis of older records; it is not a rewrite of their original scores or protocol.

## Execution and stopping

First run the offline suite and plans. After independent review of the intervention, a single-repetition end-to-end smoke consists of 12 LLM-policy matches plus four scripted-policy matches: 16 matches and up to 210 API turns before corrections and early budget exhaustion. That is an engineering check, not a powered study. A live model may fail despite passing local tests. Preserve every failed cell and diagnose it; a repair requires a new source version and batch, not replacing failed rows.

Do not select repetition counts, thresholds, or additional models after looking for a favorable result. Before a larger collection, specify the desired precision/effect size, family sample, actor-pair sensitivity test, missingness analysis, and stopping rule. If findings are dominated by fixed case cues, an always-check heuristic, or unjustified action weights, stop expansion and revise the question. No RL training or large tournament is authorized by a successful smoke alone.

From the repository root in an activated environment (substitute your existing model configuration if named differently):

```bash
python -m unittest discover -s tests_py -v
python scripts/validate_project.py
cp eval_data/models.repeat-v043.json eval_data/models.followup-v050.json
third-chair check-config --models eval_data/models.followup-v050.json

third-chair plan --models eval_data/models.followup-v050.json \
  --scenario port-disclosure --actor-a model-a --actor-b model-b \
  --mediator-policy llm --modes active,empty --repetitions 1 \
  --seed 7100 --order-seed 20261018

third-chair plan --models eval_data/models.followup-v050.json \
  --scenario port-disclosure --actor-a model-a --actor-b model-b \
  --mediator-policy linked-verification --modes active,empty --repetitions 1 \
  --seed 7100 --order-seed 20261018
```

The model config and API key remain local; no new key is required. `plan` and tests are offline. For the reviewed smoke, replace `plan` with `run` and add separate fresh output paths, such as `results/followup-v050-llm-smoke.jsonl` and `results/followup-v050-rule-smoke.jsonl`. The actors still incur API costs in the scripted-policy condition. Execute these small policy batches close together and record their order; the current order randomization is within each command, not across separate commands. Counterbalance policy-batch order in later repetitions, or add a single mixed-policy schedule before inferential comparison.

Run `third-chair summarize` on the main match JSONL files, not their event journals. Each match already embeds its events; summing both sources double-counts usage. Retain the event journals as execution evidence. Inspect `measurement.cells`, conditional denominators, missingness bounds, and per-match trajectories, as well as legacy summary fields.

## Next mediation experiment

After the diagnostic and independent scenario review, retain de-escalation and attribution as separate outcome dimensions and specify how to assess unsupported concessions. Develop a small set of consequential opportunities for reciprocal restraint, temporary pauses, and containment while preserving legitimate investigation. Record what the mediator proposes, whether actors change their actions, and whether any agreed steps are actually implemented within the simulated horizon. These actions and implementation measures require further development; they are not new capabilities of 0.5.0.

Specify the empty-chair, verification, and full-mediator comparisons before collection, including an actor-pair sensitivity test and any controlled communication ablation. Formal settlement and long-term peace are separate future constructs. RL is an optional later method contingent on the environment and baseline gates in the [roadmap](research_roadmap.md); useful mediation research does not depend on training a policy.

## Interpretation rules

- Lower Brier error is better reported probabilistic accuracy against sealed truth. It does not establish calibration, sincerity, or optimal use of partial information.
- Better attribution alone is not successful mediation, and lower modeled cost alone is not truth-preserving de-escalation. Report both dimensions, alongside action traces and the limits of accountability measures.
- The port variant remains in the original port development family. Neither changing names nor changing evidence access creates an independent held-out case.
- Identical hidden truth with different public information should test adaptation. Conversely, changing only hidden truth while preserving observable histories must not require different policy actions; such twins are a leakage test, not a reasoning success criterion.
- Cost improvement is conditional on a deliberately simplified consequence model. Describe it as modeled cost, not prevented real harm.
- The summaries provide complete-pair effects and conservative Brier missingness bounds over attempted blocks. They do not invent missing outcomes or provide population confidence intervals from one family.
- Retain failures, inapplicable outcomes, and uncertainty. Do not use zero false peace as a general safety claim.
