# Changelog

## 0.7.0 - Unreleased

Add a separately versioned shared-prefix communication experiment while preserving the 0.6.1 source and live batch as the baseline. No new paid data have been collected.

- Save one prefix through verification delivery and both round-three intentions, then deep-copy it for a Claude joint message and a protocol hold. Retain the existing instruction, scenario content, role filtering, and numerical engine.
- Add separate offline plan, execution, and summary commands. Bind continuations to checkpoint and source/configuration identities; persist completed prefixes, reject interrupted journals and incompatible resumes, and retain failed prefixes and branches.
- Count shared completion usage once and branch usage separately, including corrective attempts and explicit missing-cost counts. Keep this design out of legacy active/empty reports.
- Add prospective protocol, durable execution instructions, handoff, and offline tests for prefix equality, disk round trips, isolation, provenance, resume behavior, missing outcomes, and costs. Independent scenario review remains outstanding before substantive trials.

## 0.6.1 - 2026-10-18

Repair a public-context omission identified during prompt inspection. Requests are stateless, but earlier public event reports were absent from history; only actor messages and state updates remained. A delayed mediator could receive a document-authenticity result without the earlier public report explaining the document's claim.

- Include past public events in the shared history renderer for both actors and the mediator, including the structured mediator observation. Reports retain their original wording and chronology; their presence is not an authenticity endorsement.
- Add regression checks across all three original scenarios for event retention and future-event exclusion, plus the delayed port check with private evidence still excluded.
- Keep the scenario content, numerical engine, check schedule, response instructions, and measurements unchanged. Do not prescribe the direction of attribution updates or require a particular outcome.

Migration: all subsequent-round actor and mediator prompts change. Preserve 0.6.0 logs and its protocol; use fresh 0.6.1 results and controls. The [repair protocol](docs/public_history_repair.md) specifies one bounded eight-match smoke and retains the review gate for larger research. No live-model outcome is established by this patch.

## 0.6.0 - 2026-10-18

Post-pilot engineering diagnostic for communication after verification. No live 0.6.0 outcome or learned policy is established by this release.

- Add `--mediator` to select one fixed LLM mediator. The combined `post-verification-study` requires three distinct actor/mediator labels and interleaves both scheduled policies and their empty controls in one randomized schedule.
- Add `delayed-message` (hold, verify, LLM joint message) and `delayed-verification` (hold, verify, hold). Both request the single available neutral-linked target in round two and receive its result in round three. Missing targets fail explicitly. The communication condition uses the existing response validation and one corrective attempt.
- Record imposed protocol actions separately from model completions, and identify the policy in manifests and resume checks. Distinguish protocol-forced holds from voluntary abstention. Preserve actual model/provider identity and costs.
- Add direct compatible message-versus-verification contrasts with failure/missingness status and pre-message trajectory differences. Retain independent active/empty controls; this is not a shared-prefix experiment.
- Specify an eight-match, 98-turn engineering smoke using GPT-4.1 mini and Gemini 2.5 Flash Lite as actors and Claude Haiku 4.5 as the third-model mediator. Freeze this post-pilot design before new collection; do not infer a model ranking.
- Clarify the review gate prospectively: engineering smokes may run with independent review pending; substantive research expansion requires that review. Do not retrospectively assert that prior runs met the earlier gate.

Migration: preserve 0.5.0 logs, configuration, and results. Use a new 0.6.0 configuration copy and output path. Scenario content, numerical consequences, actor prompts, and the two-intervention budget are unchanged. Timing is externally prescribed in the new diagnostic and must not be reported as learned behavior.

## 0.5.0 - 2026-10-18

Post-pilot development revision informed by primary literature and the completed 0.4.3 exploratory runs. No new live API trials or training validate this release.

- Add a cited methodology audit and prospective development protocol, including the September 2026 ProMediConv method overlap in legal mediation, explicit construct/estimand definitions, information-access limits, family-level inference, missingness, and human-review gates.
- Retain interstate crisis mediation as the central objective. Frame the evidence-access follow-up as a supporting diagnostic, distinguish de-escalation from durable settlement, and specify a later communication/reciprocal-restraint evaluation before any conditional RL extension. These framing changes add no new trial conditions or simulator mechanics.
- Keep original scenario files and the numerical engine unchanged. Add an opt-in port disclosure variant with the same latent truth/dynamics and matched opaque-ID mapping; it is a development information intervention, not a new held-out family.
- Add a deterministic verification comparator using a whitelisted mediator observation. Record local policy decisions separately from API events; actor calls remain paid. Do not give the policy private contents, answer keys, or future results.
- Add reproducible paired-block and within-block execution randomization. Keep independent controls; shared-prefix forks remain unimplemented.
- Add a versioned, post-hoc-compatible measurement supplement: paired Brier improvement, conditional false-public-attribution/false-peace denominators, wrong-target actions, temporal probabilities, cost components, completion/repair counts, and conservative missing-outcome bounds. No small-sample population confidence intervals or global safety score.
- Correct the trust-scale wording and specify reported attribution probability as a 0-to-100 integer about causation/authorization. Strengthen scenario consistency checks and blinded, contemporaneous-information annotation instructions.

Migration: preserve all 0.4.3 results and failures. Use fresh 0.5.0 output paths and controls. Do not pool versions or treat a reanalysis as preregistered. Independent review of the scenario manipulation is still required before scientific interpretation.

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
