# Descriptive pilot protocol: 0.4.0

## Status and scope

Prepared October 17, 2026 after an offline audit. No comparative API trial or learned-policy experiment informed these repairs. This is a development protocol, not a registered confirmatory study. The [original preregistration](legacy/preregistration-0.3.0.md) is preserved verbatim at source commit `757334b77d2aa3dd110f490897775a26fdcb929a`.

The immediate question is whether the repaired runner preserves role-specific information and produces traceable descriptive comparisons. The current deterministic cost is not a validated measure of diplomatic harm and must not be used as an RL reward.

## Design

The legacy balanced schedule remains available: three scenarios, three rotations, two conditions and one repetition produce 18 matches and up to 243 model turns before retries. This is a development schedule, not a powered study.

For mediator comparisons, use `--actor-a` and `--actor-b` to hold actor configurations fixed while every configured model serves as mediator. A candidate may also serve as a state model, with independent role contexts. Keep rotated-seat results descriptive: different mediators otherwise face different opponents.

Active and empty-chair runs share scenario, role settings, repetition and seed. They are independent executions. Identical API seeds do not imply identical initial intentions. Shared-prefix forked controls are a future extension, not implemented in this release.

## Configuration and information

Freeze source, scenarios, model IDs/endpoints, temperatures, schemas and seeds for each batch. Records include source/scenario/configuration hashes, requested/returned models, request/response events and partial failures. Do not pool code or scoring versions. Manifests omit credential and header values; an opaque header digest detects changes.

Intent and final stages receive the same cumulative authorized evidence and completed checks. History preserves public actions and authorized messages. Private mediator messages reach only their recipient and the mediator. Citations require support/reject/uncertain stances.

Runtime evidence IDs are opaque and reproducible for the scenario, repetition and seed. This removes the forged-item suffix cue without editing the original scenarios. Narratives and disclosure timing remain public and fixed, so these are not held-out cases.

## Outcomes and inclusion

Include a pair only when both conditions succeed with matching source/scenario/configuration identity, repetition and seed. Do not pair different returned actor models. Duplicate successful records are errors.

Report paired crisis-cost differences and components, positive-lift rate, false-peace-gated win rate, absolute active/control false-peace rates, newly introduced false peace, attribution Brier error, labeled legacy truth score, critical-match frequency, actor-selected severity-5-or-higher actions, declared reliance on verified fabrications, intervention use and failures.

The gated win rate requires positive lift and no active false peace. The existing narrow predicate is retained: responsible State B, final State A belief below 50%, and severity at most one. It misses false concessions, abandoned inquiries and inaction harm. It is not a safety guarantee. No overall winner or scalar chair-gap claim follows from this pilot.

## Failures and missingness

Allow one response correction and up to four transport attempts for documented transient errors. Record both layers. Journal request-start and completion events; preserve prior successful calls and partial structured decisions on failure.

Recorded failures remain failures and are skipped on resume. Preserve interrupted journals and document a new output/repetition for any rerun. Do not silently replay paid calls. Provider failures are execution failures, not strategically bad decisions. Publish attempted/completed/paired counts and assess missing-outcome sensitivity before comparative interpretation.

## Analysis and gates

Report by scenario and exact actor/mediator configuration. Repeated runs within a story or fitted policy are not independent crises. More permutations or three repetitions do not substitute for a power or precision calculation.

Inspect traces for information leakage, verification timing, contradictory stances and implausible scoring. Human review should include all false-peace/critical cases and a random sample of the remainder, with identities masked. Brier accuracy alone does not establish calibration.

Confirmatory work requires an independently reviewed consequence model, outcome rubrics, held-out mechanisms/opponents, a registered effect/precision target and pilot-based sample planning. See [the research roadmap](research_roadmap.md). Record deviations and whether real-model observations motivated them; do not retrofit thresholds to obtain a desired result.
