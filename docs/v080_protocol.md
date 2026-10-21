# Prospective v0.8.0 development and exploratory panel

Written 2026-10-21 before any v0.8.0 collection. Status: offline implementation
and review only; this document is not launch authorization. The owner approved
response-contract repair, a Port information/timing audit, and three new
anonymized, real-event-inspired scenario families. The proposed actor-model
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

## New panel

Three families in `eval_data/scenarios/v080/` extend the library to six families.
Each new family has four counterfactual conditions, crossing State B responsible
versus independent nonstate action with a genuine versus forged recovery safety
certificate. The certificate's content concerns a recovery procedure, not the
identity of the attacker. Its validity therefore does not encode innocence.

Within a family, public events, initial A information, action menu, budget,
timing and physical cost parameters are fixed. B's tasking information and
later A attribution evidence follow the responsibility condition. The
certificate's evaluator validity and delayed issuer check follow authenticity.
Opaque-ID namespace and card identities remain constant across conditions.
The real events motivate mechanisms; neither truth factor recreates historical
ground truth. Source and counterfactual distinctions are documented in the
[provenance appendix](v080_scenario_provenance.md).

`--scenario expanded-v080` selects all 12 conditions. Existing `--scenario all`
continues to select the original three inputs to preserve old command meaning;
`list-scenarios` includes both panels. The twelve conditions are not twelve
independent scenario families. The legacy cases are not retrospectively balanced
factorial controls and must not be pooled into this panel as if they were.

## Proposed collection plan, awaiting separate approval

Keep the completed Qwen campaign's exact roles and configuration:

| Role | Requested model | Pinned provider |
| --- | --- | --- |
| State A | `openai/gpt-4.1-mini` | OpenAI |
| State B | `qwen/qwen3-235b-a22b-2507` | DeepInfra |
| Mediator | `anthropic/claude-haiku-4.5` | Anthropic |

Temperature 0.2, maximum 4096 tokens, no API seed, no provider fallback. The
configuration hash remains
`327528b5cedbc474304d8f464fd5c09f362f0b452045a6d7aadc0cbce19cb241`.
No actor-model sensitivity arm is planned. Provider IDs cannot freeze weights.

Proposed first expanded panel: five repetitions per condition, two policies,
active/empty for each, totaling **240 matches and 120 pairs**. There are
**3060 planned model turns** before corrections: 900 full active, 720 full
empty, 720 scripted active, and 720 scripted empty. Full active may use fewer
than its 15 planned turns when the mediator exhausts its budget. One correction
can add a second physical request per model turn; bounded transport backoffs
are separate and must be preserved in the eventual frozen execution plan.

Use new repetition seeds starting at 88000 and recorded order seed 20261021;
the implementation derives scenario/repetition seeds from the schedule. Shuffle
the two policy schedules together, retaining distinct control IDs. The offline
proposal is recorded in `results/v080-development/PROPOSED-PLAN.json`, including
all 240 rows and source/scenario hashes; its status explicitly denies launch
authorization. Use a fresh `results/expanded-v080-<approved-run-id>/`
root, never historical output paths. Freeze source, scenario/config hashes,
full schedule, execution wrapper version, allowance assumptions and stop policy
with the owner's approval before any live dispatch. Existing approval receipts
remain consumed. No new paid smoke prerequisite is imposed.

The planning estimate for 240 matches is about **$1.71**.
New prompt length, corrections, retries and provider prices can change this;
it is not a current price quote or available-credit check. A **$2.50 new-panel
operational threshold** is proposed for review, checked between matches with
possible in-flight overshoot. Prior spending remains separately recorded and
does not disappear. No new threshold or account limit is activated here.

## Analysis commitments and limitations

Report every attempted cell, failure, missing outcome and correction, without
selective reruns. Report successful paired comparisons separately by family,
responsibility, authenticity and policy, with eligible denominators and
missingness sensitivity. Five pairs per cell are exploratory, not a power
calculation. Compare full and scripted effects relative to their own controls;
the trajectories are independent, not shared-prefix message contrasts.

Keep modeled crisis cost, reported-attribution Brier error, API dollars and
applicable false-peace indicators separate. False peace is applicable only in
the guilty-B conditions under the unchanged narrow predicate. Review public
accusations, private attribution reasoning, rejection of invalid evidence,
reciprocal proposals and unjustified concessions alongside numerical scores.
Distinguish proposed arrangements from implemented actions. Retain exact
transcripts with source IDs, roles and contemporaneous observations.

The scenarios introduce reciprocal recovery opportunities in the narrative;
the existing engine still has seven coarse postures and does not implement
contracts, technical restoration choices, welfare or deterrence payoffs. Its
cost model favors restraint. Do not claim that these narrative trade-offs
repair that measurement limitation. Verification is a predetermined,
claim-specific oracle, and the later attribution evidence is unusually strong.
B's internal tasking can also become checkable if B cites it. Track those target
choices rather than assuming all cases remain equally uncertain.

Three related template families do not establish broad external validity.
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

Owner clarification, 2026-10-21: after the fixed-role expanded panel, rerun the
same scenarios with models in different seats under a separately approved
prospective campaign. This is role rotation using the existing models, not a
replacement-model sensitivity study. The scheduler already supports balanced
and full permutations; no new execution mechanism is required. Preserve role
assignment in every record, give each assignment its own matched controls,
and keep batches separate. Rotating the mediator also changes its actor pair,
so rotation alone does not identify an isolated causal mediator-model effect.
No rotating-seat collection is authorized by this development/publication step.
