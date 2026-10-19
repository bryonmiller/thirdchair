# Codex handoff

## Verified baseline, 2026-10-18

Checkout and live GitHub main both pointed to
`ae335fdebdc4e16997102b58ead60789c3c42656` at the start of this change. The
environment is WSL2, user `bryon`, repository `/home/bryon/projects/thirdchair`,
Python 3.12.3 in `.venv`. There were no tracked modifications and five untracked
local model configurations. No pre-existing AGENTS.md was found in the repository
or its ancestor directories.

The 0.6.1 raw records and saved summary verify 8 successful matches, 4 complete
active/empty pairs, no failed matches, and recorded API cost $0.05279373. Cost is
summed once from completion events in the main JSONL, excluding its duplicated
journal. The saved summary reproduces from the records. Original-port arms
differed by -0.1 in pre-message reported probability; disclosure-port arms
differed by -2.32 in first-two-round modeled cost. These independent runs do not
establish a causal communication benefit. Raw records remain local and unchanged.

Earlier local completed batches include smoke v1/v2/v3 (0/6, 5/6, 6/6 successful),
0.4.2 pilot (16/18), 0.4.3 diagnostic (18/18), 0.4.3 repeated batch (52/54),
0.5.0 smoke (16/16), and 0.6.0 smoke (8/8). These are exploratory or engineering
results, not substantive confirmatory trials. Do not pool release versions.

The baseline passed 76 unit tests and structural validation again before edits.
Static-site validation requires the generated source ZIP; its absence is a build
prerequisite, not a simulator failure. Local OpenRouter configurations are
available, but their required credential variable was absent in the audit
process. No credential values were inspected and no paid calls were made.

## Current development

Branch `codex/shared-prefix-v070` preserves the 0.6.1 baseline and develops the
separately versioned 0.7.0 shared-prefix experiment. See the prospective
[protocol](shared_prefix_protocol.md). The checkpoint ends after verification
delivery and both round-three actor intentions. Only final communication and
actor revision differ across branches. The existing mediator instruction,
scenario files, and consequence engine are retained.

No live 0.7.0 batch has been collected. Paid collection requires owner agreement
on the run plan and spending cap. The PR is for review; merging remains with the
owner. Keep raw results, local configuration, and unpublished source material out
of public commits.

Offline validation of the implementation passes 93 unit tests, including 17 new
shared-prefix tests, and structural validation. Tests cover prompt parity with
the existing delayed-message path, prefix equality through both intentions,
role isolation, full-precision state and evidence-order round trips, successful
and failed resumes, interrupted-call rejection, source/configuration/protocol
provenance, missing outcomes, and single-count costs. The offline two-variant plan
has two shared prefixes, four continuations, and 30 planned calls before retries.
This is a proposed engineering smoke, not an approved paid run or dollar cap.
The source-only release build and static-site validation also pass. The source
archive was inspected and contains no local configurations or raw results.

## Research gates

Independent scenario and role-information review remains outstanding before
substantive trials. Both port variants have innocent State B and form one
development family. The restraint-favoring cost model and narrow false-peace
predicate do not validate accountability or concessions. A larger study needs
counterfactual families, actor sensitivity, and a frozen precision/stopping plan.
Shared prefixes address pre-message divergence, not generalization, noisy oracle
validity, provider drift, or random completion variation. No RL work is underway.
