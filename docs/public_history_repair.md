# Public-event context repair: 0.6.1

Development amendment dated 2026-10-18. The [0.6.0 protocol](post_verification_protocol.md) remains the record of the earlier experiment. This amendment follows prompt inspection; it is not a preregistered confirmatory protocol.

## Defect and bounded repair

Every model request is stateless. The history renderer preserved earlier actor messages and public state values, but omitted earlier `public_event` text. This matters when a mediator is called only after a check: the original public account of the checked document may no longer appear anywhere in its prompt. It also affects actors' later requests, although their private evidence persists separately.

Version 0.6.1 retains each earlier public event in chronological history for both actors and the mediator, in all conditions. It preserves exactly the text already publicly available at that point. Public reports may contain false claims; retaining them does not certify them. The repair does not disclose private cards, private reasoning, future events, or sealed responsibility. It does not tell an actor how to update attribution or tell the mediator which government is innocent.

Document authenticity, the document's claim, and government responsibility remain separate judgments. Discrediting a document that dismissed a criminal lead reopens that lead; it does not identify the forger or, by itself, settle whether a government directed the incident. Evaluate messages against the information available to the mediator rather than the evaluator's answer key.

The original scenarios, consequence model, actors, selected mediator, scheduled check, token limits, and outcome definitions remain fixed. Prompt text changes from round two onward, so old controls are incompatible with new runs. The source and package identity enforce a version boundary.

## Next engineering check

Run the entire eight-match schedule once, with the existing pinned models and one repetition. It still plans 98 calls before corrections; prompts are slightly longer. Retain all failures and outcomes. Do not keep repeating the smoke or changing prompts until mediation scores improve. If requests carry the intended context and measurements reproduce, the engineering gate is satisfied even if the mediator fails or attribution worsens.

Review the two actual messages for correct identification of the checked claim, distinction between forgery and responsibility, proportionate next steps, and unsupported concessions. Record actor posture and reported probability separately from `accepts_intervention`; that field is a self-report and does not establish behavioral adoption.

Independent trajectories still prevent isolating an individual message's causal effect. Both port variants still have innocent State B. After this check, design any larger study separately: independent scenario review, guilty/innocent cases, repeated trials with a justified precision target, and actor sensitivity remain necessary. A shared-prefix final-round comparison would address pre-message trajectory variation but is not implemented here. This patch provides no evidence of real-world peace, lasting settlements, or RL readiness.

## Commands after merging

Update the checkout, install the package, and pass all 76 tests plus structural validation. Record the merged commit. Keep the existing OpenRouter environment and make a non-overwriting model configuration copy:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
source = Path('eval_data/models.mediation-v060.json').read_bytes()
with Path('eval_data/models.mediation-v061.json').open('xb') as destination:
    destination.write(source)
PY

.venv/bin/third-chair check-config --models eval_data/models.mediation-v061.json
.venv/bin/third-chair plan \
  --models eval_data/models.mediation-v061.json \
  --scenario port-disclosure \
  --actor-a model-a --actor-b model-b --mediator model-c \
  --mediator-policy post-verification-study \
  --modes active,empty --repetitions 1 \
  --seed 8100 --order-seed 20261019
```

The same schedule and evidence-ID mapping are intentional; no API seed is sent, and this is a separate versioned batch. Confirm eight matches and 98 planned turns. The next command spends API credits:

```bash
.venv/bin/third-chair run \
  --models eval_data/models.mediation-v061.json \
  --scenario port-disclosure \
  --actor-a model-a --actor-b model-b --mediator model-c \
  --mediator-policy post-verification-study \
  --modes active,empty --repetitions 1 \
  --seed 8100 --order-seed 20261019 \
  --output results/mediation-v061-smoke.jsonl

.venv/bin/third-chair summarize results/mediation-v061-smoke.jsonl \
  --format json --output results/mediation-v061-smoke-summary.json
```

Keep the main JSONL, its event journal, and summary. The main file already includes journal events; do not count both copies when totaling API cost. Analyze the new batch separately from earlier versions.
