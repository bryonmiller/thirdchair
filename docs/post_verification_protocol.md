# Post-verification mediation diagnostic: 0.6.0

Development protocol dated 2026-10-18, written after examining the 0.5.0 engineering smoke. This is a prospective specification for a new diagnostic, not a preregistered confirmatory study. Preserve the earlier batches and their protocols. No 0.6.0 live-model result is established by local tests.

## Question and fixed roles

Can a third-model mediator use a completed neutral check to guide a proportionate response, beyond providing the check result alone?

Keep State A as `model-a` (OpenAI GPT-4.1 mini), State B as `model-b` (Google Gemini 2.5 Flash Lite), and the LLM mediator as `model-c` (Anthropic Claude Haiku 4.5), with the existing pinned OpenRouter configurations. The third model is selected to keep its identity distinct from both actors. Its favorable descriptive result in a previous one-pair comparison is not evidence that it is the best mediator. This diagnostic does not rank mediator models or vary the actor pair.

## Conditions

Use the original port scenario and its public server-history variant. These are two variants of one development family, both with innocent State B. The three-round horizon, two-intervention budget, scenario content, and numerical engine stay unchanged.

| Condition | Round 1 | Round 2 | Round 3 |
| --- | --- | --- | --- |
| `delayed-message` active | Protocol hold | Protocol verification request | Claude joint message after the result arrives |
| `delayed-verification` active | Protocol hold | Same scheduled verification request | Protocol hold |
| Empty chair | No intervention | No verification request | No intervention |

The check targets the single currently checkable document linked by the round-two neutral card. It is selected from the authorized observation, never from sealed validity or responsibility. A missing or ambiguous available target fails the match with a diagnostic; there is no silent substitution. Both active conditions use the same neutral request wording. The result is delivered to both actors and the mediator before the third-round decisions.

Claude receives the normal role-authorized mediator context plus a condition-specific instruction to interpret established facts and remaining uncertainty and propose a concrete, proportionate next step. The instruction does not supply responsibility or require exoneration, blame, or a particular posture. It requires one joint message within the existing word limit; private messaging, another verification, or holding is invalid in this condition and gets the ordinary one corrective attempt. Failed completions remain failures.

Timing, the first check, and the final message opportunity are imposed by the protocol. This measures communication under a prescribed schedule, not autonomous timing or learned abstention. The verification control uses one intervention; the message arm uses two under the same cap. Report this additional intervention and API cost. A later generic-message control would be needed to separate evidence interpretation from the effect of receiving any extra message.

## Controls, execution, and interpretation

The combined `post-verification-study` schedule selects one LLM mediator and the scripted verification control, each with its own independently executed empty-chair counterpart. One schedule randomizes paired blocks across both policies and scenarios, and randomizes active/empty order within each block. Empty controls are not reused or counted as independent crisis families.

These are independent simulations. The shared seed determines evidence-ID mapping and schedule identity; it does not synchronize API randomness or create a shared-prefix fork. Actor intentions can differ before the final message. The direct comparison therefore includes trajectory variability, even with identical scheduled checks. Do not describe an individual pair as the isolated causal effect of its message.

The JSON summary's `post_verification_comparisons` reports the direct active-policy contrast within compatible source, scenario, actor configuration, repetition, and seed. It checks actor model/provider identity and matched check requests/results. Missing, failed, ambiguous, or incompatible arms remain visible with null effects. It reports:

- Modeled cost reduction: verification-only cost minus message-condition cost.
- Attribution Brier improvement: verification-only error minus message-condition error.
- Final reported probabilities, false public attribution, and final State A postures.
- First-two-round cost differences and pre-message attribution differences, exposing variation that precedes the intervention.

Positive differences favor the message condition. Keep the two outcome dimensions separate; do not manufacture a combined winner. Existing active/empty contrasts remain secondary context and are not substitutes for the direct comparison. The measurement supplement is `evidence-audit-2`, adding protocol-forced holds separately from voluntary and budget-forced holds.

Review the actual final message for evidence support, uncertainty, actionable de-escalation, and unsupported concessions. Compare actor actions before and after it; accepting an intervention is only a self-report. Both variants have innocent State B, so this diagnostic cannot test preservation of justified blame, comprehensive accountability, or general truth-preserving mediation. The restraint-favoring cost model still cannot support real-world welfare or RL reward claims.

## Engineering smoke and later research gate

One repetition produces **8 matches, 4 active/empty pairs, and 2 direct message-versus-verification comparisons**. It plans **98 paid model turns: 96 actor calls and two Claude calls**, before corrective attempts or failures. Local scheduled decisions cost no API credits. This is a bounded pipeline check, not a powered study.

Engineering smoke tests may proceed while independent scenario review is pending, provided that status is recorded and results remain exploratory. This clarifies the overly restrictive pre-smoke gate in the original 0.5.0 protocol; it does not retrospectively establish that an earlier batch received independent review. Keep scenario metadata marked as requiring review until that review actually occurs.

After the smoke, inspect all failures, correction attempts, target/result parity, message content, and provider identities before further collection. Do not rerun failed cells until they pass or change the schedule to improve outcomes. A repair requires a new version and fresh output path. Before a substantive larger study, obtain independent scenario review, freeze hypotheses and precision targets, plan repetitions using pilot variability, and add guilty/innocent counterfactual families and an actor-pair sensitivity test. No RL training follows automatically from this smoke.

## Commands after merging 0.6.0

From the existing WSL checkout, preserve the model settings already used in 0.5.0. The standard-library copy below refuses to overwrite an existing configuration.

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
source = Path('eval_data/models.followup-v050.json').read_bytes()
with Path('eval_data/models.mediation-v060.json').open('xb') as destination:
    destination.write(source)
PY

.venv/bin/third-chair check-config --models eval_data/models.mediation-v060.json
.venv/bin/third-chair plan \
  --models eval_data/models.mediation-v060.json \
  --scenario port-disclosure \
  --actor-a model-a --actor-b model-b --mediator model-c \
  --mediator-policy post-verification-study \
  --modes active,empty --repetitions 1 \
  --seed 8100 --order-seed 20261019
```

Freeze the merged commit, configuration, protocol, and scenario hashes before running. The order seed is an arbitrary fixed integer, not an execution date. The following command makes paid API requests; choose a fresh output path and retain the event journal.

```bash
.venv/bin/third-chair run \
  --models eval_data/models.mediation-v060.json \
  --scenario port-disclosure \
  --actor-a model-a --actor-b model-b --mediator model-c \
  --mediator-policy post-verification-study \
  --modes active,empty --repetitions 1 \
  --seed 8100 --order-seed 20261019 \
  --output results/mediation-v060-smoke.jsonl

.venv/bin/third-chair summarize results/mediation-v060-smoke.jsonl \
  --format json --output results/mediation-v060-smoke-summary.json
```

Retain all 0.5.0 records separately. Do not add new results to old files or pool controls across source versions. No new API key or model subscription is needed for the existing OpenRouter setup.
