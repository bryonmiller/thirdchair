# Changelog

## 0.4.3 - 2026-10-18

Exploratory pilot responses selected neutral liaison-card IDs when requesting the documents those cards offered to authenticate. The liaison cards did not identify their target documents. This revision clarifies that interface across all three scenarios; it does not erase observed model failures or establish mediation effectiveness.

- Add explicit `verification_targets` to the three existing round-two neutral offers. Render linked IDs only after the neutral card has arrived and the target is already in the mediator's checkable set.
- Explain that the liaison card is not the target and that opaque IDs do not reveal private contents. Keep the original checkable set, private evidence text, validity labels, verification results, scoring, and action limits unchanged.
- Validate links and test opaque-ID remapping, withheld/future targets, private evidence boundaries, and delayed verification of the actual target. Invalid liaison-card selections remain invalid; no automatic substitution is performed.

Migration: preserve all 0.4.2 pilot successes and failures. Source and scenario hashes change, so use a separate 0.4.3 diagnostic batch. Do not rerun only failed cells or pool source versions. Live adherence to the revised interface remains untested. This repair addresses an information-presentation defect, not the outstanding accountability, inaction-cost, or generalization limitations.

## 0.4.2 - 2026-10-18

Live setup responses exposed ambiguous verification instructions: models supplied empty or null messages, or requested multiple checks without a target. This is a prompt and diagnostic repair, not a change to scoring or accepted actions.

- Explicitly describe hold, communication and verification field combinations; every intervention includes a non-empty message and verification selects exactly one listed evidence ID.
- Explain that the verification message is public and cannot assert the result of a pending check.
- Give complete correction guidance for null/empty messages and missing verification targets.
- Add simulated regression cases for the observed failures, a valid correction with delayed delivery and one intervention charge, and persistent invalid responses that remain failed.

Migration: retain the failed setup logs. Use a new output filename and rerun every diagnostic condition under 0.4.2; do not combine earlier successes with repaired runs. Local tests cannot establish live-model adherence to the revised prompt. Repeat the live diagnostic before freezing a research batch. Crisis dynamics and scoring remain `baseline-0.4.0`.

## 0.4.1 - 2026-10-17

OpenRouter controls for an exploratory live-model pilot. No live-provider trials were run to validate this release; HTTP integration tests use simulated responses. Crisis dynamics and scoring remain `baseline-0.4.0`.

- Configure provider allowlists/fallbacks, parameter enforcement, per-model token and reasoning budgets, optional temperature/seed, and timeout. Reject misspelled or invalid settings.
- Add a free `check-config` command. The run command rejects missing credentials, placeholders and uncontrolled OpenRouter routing before any paid call.
- Record exact request payloads, requested provider/reasoning settings, returned provider identity, missing provider metadata and completion finish reasons. Request OpenRouter routing metadata by default.
- Exclude mixed model/provider identities, missing required provider metadata and actor-provider mismatches from comparisons; separate mediator provider cohorts.
- Stop empty, truncated or blocked responses without a JSON-repair retry, retaining their raw response and usage.
- Add regression coverage and an OpenRouter pilot guide with an explicit live-validation gate.

Migration: use a new output file and keep 0.4.1 runs separate from 0.4.0. The OpenRouter example now requires exact provider endpoint slugs as well as model IDs. Generic endpoint configurations retain previous defaults.

## 0.4.0 - 2026-10-17

Audited descriptive baseline. No empirical model data informed these changes and no trained policy is included.

- Preserve evidence/checks in final decisions and retain seat-specific history, cumulative neutral evidence and verification targets.
- Require support/reject/uncertain evidence stances; randomize opaque runtime evidence IDs.
- Remove direct message-acceptance bonuses and hidden-truth/evidence penalties from public state dynamics; retain evaluator flags and add attribution Brier error.
- Report absolute active/control false peace separately from introduced failures; gate positive-lift wins; distinguish own severe actions from critical-match participation.
- Add fixed-actor schedules and configuration-specific report rows.
- Record requests, retry outcomes, full/partial events and configuration/source/scenario hashes. Reject duplicate or incompatible records and silent replay of interrupted calls.
- Add regression tests, CI validation and a generated source download before Pages deployment.
- Preserve the original scoring/protocol under docs/legacy; document the bounded research direction and unresolved inaction/accountability limitations.

Migration: response schemas, score semantics and IDs are incompatible with 0.3.0. Use new output paths and do not pool versions. See docs/audit_repairs.md.


## 0.3.0 - 2026-08-12

- Rebuilt the project as a three-model cyber-crisis mediation tournament.
- Added active and empty-chair twins, balanced and full seat rotation, private state briefs, delayed evidence authentication, and deterministic crisis resolution.
- Added three dynamic scenarios that distinguish false attribution from truth-erasing de-escalation.
- Added mediator, actor, and chair-gap analysis with no composite score that can hide false peace.
- Replaced the single-model runner, Inspect task, documents, and microsite with the Third Chair protocol and release materials.
- Kept the public host provider-neutral and prepared it for GitHub Pages or a custom domain.

## 0.2.0 - 2026-08-12

- Replaced the scripted crisis-game concept with a model-facing cyber attribution evaluation.
- Added three paired cases and a planted evidence item in each poisoned condition.
- Added a portable model runner, Inspect AI task, deterministic scorer, and paired analysis.
- Added a static site and GitHub Pages workflow that do not depend on the project workspace host.
- Removed scripted paths from the results story. No model finding is reported without a recorded response.
