# Shared-prefix post-verification communication: 0.7.0

Prospective development protocol, 2026-10-18. Written before any 0.7.0 paid data
collection, after inspection of the completed 0.6.1 engineering smoke. This is a
bounded communication diagnostic within the mediation study, not a registered
confirmatory trial. Preserve the 0.6.1 batch and protocol separately.

## Question and intervention

Given exactly the same crisis history, completed verification, and both actors'
final-round intentions, does a Claude joint message change their final actions,
modeled de-escalation, reported attribution accuracy, or unsupported concessions?

Keep the pinned State A GPT-4.1 mini, State B Gemini 2.5 Flash Lite, and mediator
Claude Haiku 4.5 configurations from 0.6.1. Keep both port variants, three rounds,
two interventions, evidence-ID mapping, prompt wording, consequence engine, and
response correction rules. Do not tune instructions to improve observed scores.
The existing post-verification instruction is reused verbatim.

Execute rounds one and two once: protocol hold, then the authorized neutral-linked
check. Deliver its result at the start of round three and generate both actor
intentions once, without exposing one actor's current intention to the other.
Freeze a checkpoint here, before the mediator or final actor revisions. Fork
independent deep copies:

| Branch | Final mediator action | Subsequent calls |
| --- | --- | --- |
| `message` | Claude joint message | Both actors revise once |
| `no-message` | Protocol hold | Both actors revise once |

Both branches already received the same verification result and announcement.
The control is verification without final communication, not an empty chair
throughout the crisis. Final actor calls are independent samples; API seeds do
not synchronize provider randomness. Branch order and prefix-block order are
randomized reproducibly by a required execution-order seed and recorded. No
branch sees the other's outcomes or requests. The mediator sees only its ordinary
authorized observation, never the full evaluator checkpoint or actor private
reasons. Actor prompts retain their own private context and the opponent's public
intention only. The message branch uses two interventions; control uses one.

## Provenance, persistence, and accounting

Use a fresh 0.7.0 output, separate from all earlier batches. Persist one typed
prefix record followed by two typed continuation records per unit. Source,
package, protocol, scenario, configuration, seed, repetition, branch order, and
checkpoint fingerprints bind the records. The prospective protocol's SHA-256 is
part of the manifest; editing it invalidates resume. A branch references its parent prefix
and checkpoint digest. Checkpoint equality includes the actual first two rounds,
delivered checks, round-three state, and both intentions, not merely a seed.

Completed prefixes can resume pending branches without purchasing the prefix
again. Completed or failed continuations are never replayed. Reject incompatible
settings, duplicate records, altered checkpoints, incomplete JSONL, or unfinished
calls in a journal. After interruption preserve the output and journal; use a
documented fresh output/repetition rather than silently replaying a paid call.
One failed branch must not prevent recording the other branch. A failed prefix
produces no continuations and remains a failed attempted unit.

Canonical costs come only from each record's own completion events, including
invalid and failed responses with returned usage. Do not count request-start
events, duplicated journal events, or inherited transcript attempts. Report
prefix and each branch's cost separately, missing usage explicitly, and their
sum once per unit. A successful unit plans 10 shared actor calls, 1 Claude call,
and 4 branch actor calls: 15 calls. Both port variants with one repetition plan
30 calls, before corrections and transport retries. This is a turn count, not a
spending authorization or a dollar cap.

## Analysis and stopping

Report attempted, prefix-ready, failed-prefix, completed-branch, failed-branch,
and eligible-pair counts. Retain missing outcomes with null contrasts. Pair only
the two branches bound to the same checkpoint with stable returned actor
model/provider identities and required metadata. Do not put these records into
the legacy active/empty tournament table.

Primary descriptive outcomes remain separate: modeled cost reduction
(`no-message` minus `message`) and final State A Brier improvement (same sign).
Also report final postures, reported probabilities, false public attribution,
wrong-target actions, intervention counts, and eligible legacy false-peace
denominators. Pre-message differences must be exactly zero by construction.
Review message interpretation, remaining uncertainty, concrete reversible steps,
unsupported concessions, and actor follow-through against contemporaneous
role-authorized information using the annotation guide. Self-reported acceptance
is not behavioral adoption. Never manufacture an aggregate winner.

One repetition is only an engineering smoke. Preserve every failure; do not
repeat cells or edit prompts until mediation looks effective. Validate local
fixtures and review the plan before requesting approval for a fresh paid batch
and spending cap. No paid run is authorized by this protocol. Independent
scenario review remains required before substantive trials.

## Offline commands and future execution

Use the existing local configuration to inspect the plan without changing it:

```bash
.venv/bin/python -m third_chair.cli plan-shared-prefix \
  --models eval_data/models.mediation-v061.json \
  --scenario port-disclosure \
  --actor-a model-a --actor-b model-b --mediator model-c \
  --repetitions 1 --seed 8100 --order-seed 20261020
```

Expect two units, four continuations, and 30 planned turns. The order seed is an
arbitrary fixed integer. It randomizes order; it is not a date of execution.
This proposed smoke plan still needs owner agreement and a dollar cap. Before
execution, freeze the reviewed source and protocol hashes, pinned configuration,
output path, retry allowance, and spending cap. `run-shared-prefix` accepts the
same plan arguments and requires an explicit fresh `--output`. It makes paid
calls and is not authorized by the offline command above.

After an approved future run, inspect its local records without paid calls:

```bash
.venv/bin/python -m third_chair.cli summarize-shared-prefix \
  results/shared-prefix-v070-smoke.jsonl
```

Only the main JSONL goes into this summary. Do not also supply its event journal.

## Limits

This estimates a conditional final-message contrast at sampled fixed prefixes,
not the total effect of autonomous mediation, verification timing, or a learned
policy. Branch sampling and order/provider drift still matter. A generic-message
control would be needed to isolate evidence interpretation from receiving any
message. Shared branches are dependent and do not create independent crises.
Both variants are innocent-B cases from one development family. No justified-blame
preservation, population diplomacy, calibration, durable peace, or RL-readiness
claim follows. The consequence model favors restraint and the legacy false-peace
flag misses many accountability and concession failures. Larger trials require
independent review, coherent guilty/innocent families, actor sensitivity, and
prospectively justified repetitions and stopping criteria.
