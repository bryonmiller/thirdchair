# Prospective v0.8.0 development and exploratory panel

Written 2026-10-21 before any v0.8.0 collection. Status: offline implementation
and review only; this document is not launch authorization. The owner approved
response-contract repair, a Port information/timing audit, and three new
anonymized, real-event-inspired scenario families. The owner subsequently
requested factorial copies of Grid, Port and Archive, completing six families
with four conditions each. The proposed actor-model
sensitivity comparison was explicitly excluded.

## Scope and preservation

The primary question remains whole-policy mediation: whether a full mediator
reduces escalation while preserving attribution and avoiding unjustified
concessions, compared with its independently executed empty-chair control.
Scripted linked verification has its own independent control. Shared-prefix
message effects remain secondary. No RL work or model replacement is included.

Work is on `research/v080-evidence-and-scenarios`, based on `7f8a8a4`.
Historical campaigns remain separate exploratory baselines. Do not repair,
replace, pool with, or append new data to historical outcomes. Raw results and
unpublished analyses remain local and are not part of this release.

The original Grid, Port and Archive inputs, engine, scoring and mediator
policies remain unchanged. Historical protocols remain intact. A local
214-file preservation inventory covers original claims, combined export,
legacy scenarios, engine/policies, key historical protocols and the pinned
Qwen model configuration. The new contract changes actor prompts and source
identity; even a new run of an original scenario is a new execution condition.

## Response contract and failure handling

`stance-map-0.8.0` asks actors for one `evidence_stances` map. Its keys include
support, reject and uncertain citations. The runner derives sorted internal
`evidence_ids` from those keys. It does not infer a stance, change a belief or
action, or discard inconvenient evidence. Known-ID checks still use only the
actor's authorized evidence and delivered checks. Redundant wire lists are
rejected with specific feedback. One structured correction remains the limit.

Raw responses, correction attempts and usage stay in the record. The manifest
and successful actor attempts identify the new contract. Existing historical
record validators retain both internal fields. A nominal HTTP success containing
an embedded provider error stops with retained usage; it is not a schema-repair
opportunity and triggers no extra request. Existing approved execution wrappers'
bounded 429 handling and host-service design are not rebuilt or relaxed.

Offline projections of captured failures are developer diagnostics only. A
projection passing schema validation is neither a successful historical match
nor evidence that a live model will follow the new instructions.

## Complete 24-condition panel

Six families in `eval_data/scenarios/v080/` each have four counterfactual
conditions: State B responsible versus independent nonstate action crossed with
a genuine versus forged document. `--scenario expanded-v080` selects exactly
these **24 conditions**. `--scenario all` still selects the three historical
inputs for compatibility; those are excluded from the factorial panel.
`list-scenarios` lists both, with distinct scenario IDs.

| Family | Document whose authenticity varies |
| --- | --- |
| Grid outage before a basing vote | Vendor credential-revocation and log-custody notice |
| Port shutdown during a sanctions fight | Customs gate-image custody receipt |
| Archive leak before peace talks | Police record-preservation and access certificate |
| Relay outage | Terminal-repair safety certificate |
| Fuel shutdown | Restoration-package safety certificate |
| Software cascade | Replacement-update safety certificate |

The first three families are prospective adaptations, not edits to historical
files or extensions of their batches. Their original disputed documents could
assert or imply attribution; toggling authenticity alone would create incoherent
crossed cells. The factorial copies instead use specific containment/custody
claims that can be genuine or fabricated under either responsibility condition.
Political pressure, criminal participation and government commissioning remain
separate. The forger's identity is unspecified. Even a genuine document does
not authenticate every inference a government draws from it.

Within each family, public events, initial A information, actions, budget,
timing and physical cost parameters are fixed across the four versions.
B's private tasking information and later attribution evidence follow the
responsibility factor. Other private cards, checks and neutral reporting are
changed wherever necessary to keep that assignment coherent. In the Archive
nonstate version, for example, stolen state tooling explains a real historical
code match without implying current state control. The document claim remains
the same; its evaluator validity and issuer check follow authenticity only.

Opaque-ID namespace and card identities stay constant within a family.
The new Grid/Port/Archive copies remove the old `-P` suffix from the target ID
in both authenticity conditions; always use opaque IDs for collection. Their
metadata records the original scenario and its SHA-256. The previous twelve
satellite/pipeline/software inputs are byte-for-byte unchanged. Neither role prompt
templates nor the scoring engine have changed in this panel expansion; new
scenario content necessarily changes the information presented to each role.
See the [provenance appendix](v080_scenario_provenance.md) and
[outcome-free review packet](v080_scenario_review.md).

## Offline campaign options, awaiting a separate run approval

Retain the existing three pinned model configurations:

| Model | Pinned provider | Previously fixed role |
| --- | --- | --- |
| `openai/gpt-4.1-mini` | OpenAI | State A |
| `qwen/qwen3-235b-a22b-2507` | DeepInfra | State B |
| `anthropic/claude-haiku-4.5` | Anthropic | Mediator |

Temperature 0.2, maximum 4096 tokens, no API seed, no provider fallback. The
configuration hash remains
`327528b5cedbc474304d8f464fd5c09f362f0b452045a6d7aadc0cbce19cb241`.
When rotating seats, each model carries its configuration into its assigned
role. Do not rotate only labels or reuse controls across assignments. This is
role rotation, not the excluded replacement-model sensitivity comparison.
Provider IDs cannot freeze weights.

| Schedule across all 24 conditions | Repetitions | Matches | Planned model turns |
| --- | ---: | ---: | ---: |
| Full six seat assignments, LLM mediation and empty chair | 1 | 288 | 3888 |
| Full six seat assignments, LLM mediation and empty chair | 5 | 1440 | 19440 |
| Previous fixed roles, full and scripted policies with separate controls | 5 | 480 | 6120 |

These are alternatives, not an authorization to run their sum. Full rotation
uses the existing engine with a new complete-panel coverage contract. The full-rotation schedule
covers all six permutations, every condition and every repetition exactly once
per active/empty arm. Pair order and within-pair arm order are randomized and
recorded. The full-rotation count does not include scripted verification.
That comparator requires separate fixed ordered-actor-pair schedules with its
own controls; it must not be represented as another LLM mediator seat.

The owner subsequently required equal exposure and a repetition calculation.
The [prospective statistical plan](v080_statistical_plan.md) specifies the
complete-panel requirement, matched opaque-ID mapping across assignments,
paired tests, multiplicity, missingness and effect-size sensitivity. Its
moderate-effect recommendation is 121 scheduled repetitions per condition,
assignment and arm: 34,848 matches and 470,448 planned turns, subject to the
explicit assumptions. The one/five-repeat options above remain exploratory,
not powered substitutes. No new budget or collection is approved here.

For an **offline count preview** using the public placeholder configuration:

```bash
.venv/bin/third-chair plan \
  --models eval_data/models.example.json \
  --scenario expanded-v080 --rotation full --modes active,empty \
  --repetitions 5 --seed 188000 --order-seed 20261022
```

This command plans only and does not load a credential or call a provider.
Its placeholder labels are not the live configuration. The model-independent
schedule tests verify 1440 unique IDs, 720 complete planned pairs, common
family/repetition seeds across all roles and arms, and all role permutations.
Use `--plan-output` with a fresh path to freeze the coverage contract and full
ordered schedule. The complete panel refuses missing/duplicate cells, changed
provenance and incomplete designs before dispatch. Recorded seeds identify the schedule and
opaque IDs, not identical stochastic provider trajectories.

Full-active matches may use fewer than their 15 planned turns when mediator
budget is exhausted. One correction may add a second request per model turn;
transport retries are accounted separately. Preserve all failed or missing
outcomes without replacement runs. Save every response, role assignment,
returned model/provider, correction, check and score in a fresh versioned
output root under the existing host service with automatic restart disabled.

The earlier 240-match proposal, cost estimate and $2.50 threshold applied only
to the first twelve conditions with fixed roles. They are superseded planning
records, not a budget for the larger schedule. No current account allowance or
new live cost estimate is verified here. Role rotation changes model token
loads, particularly Claude's actor calls; do not scale cost only by match count.
Before collection, agree on one exact schedule, current budget estimate and
operational spending threshold, then freeze source/scenario/config hashes and
bind the existing tested execution wrapper. No paid preflight, trial, replay or
new automatic restart is authorized by this update. No additional paid smoke
prerequisite is imposed.

## Analysis commitments and limitations

Report every attempted cell, failure, missing outcome and correction, without
selective reruns. Report successful paired comparisons separately by family,
responsibility, authenticity and policy, with eligible denominators and
missingness sensitivity. Five pairs per cell are exploratory, not a power
calculation; the new statistical plan supplies prospective powered alternatives.
Compare full and scripted effects relative to their own controls;
the trajectories are independent, not shared-prefix message contrasts.

Keep modeled crisis cost, reported-attribution Brier error, API dollars and
applicable false-peace indicators separate. False peace is applicable only in
the guilty-B conditions under the unchanged narrow predicate. Review public
accusations, private attribution reasoning, rejection of invalid evidence,
reciprocal proposals and unjustified concessions alongside numerical scores.
Distinguish proposed arrangements from implemented actions. Retain exact
transcripts with source IDs, roles and contemporaneous observations.

The scenarios offer cooperation, recovery and evidence-sharing choices in the narrative;
the existing engine still has seven coarse postures and does not implement
contracts, technical restoration choices, welfare or deterrence payoffs. Its
cost model favors restraint. Do not claim that these narrative trade-offs
repair that measurement limitation. Verification is a predetermined,
claim-specific oracle, and the later attribution evidence is unusually strong.
B's internal tasking can also become checkable if B cites it. Track those target
choices rather than assuming all cases remain equally uncertain.

Six handcrafted families with shared templates do not establish broad external validity.
Anonymization does not guarantee that models cannot recognize public incidents
or recall them from training. Keeping names and sources out of prompts reduces
direct cues but does not make an unseen test set. Review remains automated;
independent review is recommended before stronger claims and does not block
explicitly labeled exploratory collection. No tuning for favorable mediation
outcomes is authorized.

The existing delayed-message and shared-prefix implementations can support a
separately approved timing diagnostic. Do not silently constrain the autonomous
mediator to save an intervention, add this as a primary arm, or infer a
communication benefit from the completed verification-first policy.

## Future seat rotation

Owner clarification, 2026-10-21: a future approved campaign may run the same
scenarios with models in different seats. A fixed-role campaign is not a
prerequisite. This is role rotation using the existing models, not a
replacement-model sensitivity study. The scheduler already supports balanced
and full permutations; no new execution mechanism is required. Preserve role
assignment in every record, give each assignment its own matched controls,
and keep batches separate. Rotating the mediator also changes its actor pair,
so rotation alone does not identify an isolated causal mediator-model effect.
No rotating-seat collection is authorized by this development/publication step.
