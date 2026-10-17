# Audit repairs and remaining limits

Version 0.4.0, October 17, 2026. This change repairs the descriptive baseline using offline scripted reproductions. It does not implement or train the proposed RL environment. No real-model trial was run.

The original version is available at [commit 757334b](https://github.com/bryonmiller/thirdchair/tree/757334b77d2aa3dd110f490897775a26fdcb929a). Its preregistration and scoring guide are copied verbatim under `docs/legacy/`. Replaying 0.3.0 requires that source revision; revised prompts and scores must not be presented as the original experiment.

| Finding | Repair or disposition |
| --- | --- |
| Final decisions lost evidence/checks; mediation memory was incomplete | Shared actor context; cumulative neutral evidence and verification targets; seat-filtered message/action history |
| Summary hid persistent false peace and called every positive lift a win | Absolute active/control and introduced rates; gated win requires no active false peace |
| Passive actions dominate cost | Unresolved research blocker; no invented inaction coefficient added |
| Message acceptance mechanically reduced cost | Removed acceptance bonus and intervention exception to severe-action trust loss |
| Mediator identity confounded with actor configuration | Fixed-actor schedules, common seeds across candidates, configuration-specific rows and rotation limitations |
| Rejecting a forgery counted as reliance | Required support/reject/uncertain stances; only support counts; human consistency review remains necessary |
| Missing requests/settings and discarded partial calls | Manifest, source/scenario hashes, per-call journal, retries, partial moves and returned model IDs |
| Resume/pairing mixed or skipped configurations | Configuration/seed/repetition identities; reject changed settings and duplicate records; preserve interrupted journals |
| Absolute-error truth score was insufficient | Added Brier error; labeled old truth score as legacy; no calibration claim |
| Forged IDs and fixed timing offered shortcuts | Opaque runtime IDs remove suffix cues; public narratives and fixed timing remain limitations |
| Match-critical flag blamed both actors; no chair-gap statistic | Separate own severe-action rate from match participation; website reports role profiles |
| Missing archive, stale links, ignore rules and deployment-only CI | Source-only download build; CI tests/validators before Pages publication; corrected links and ignore rules |
| Hidden truth altered public escalation | Attribution/evidence judgments are evaluator fields, not hidden truth-dependent state changes |

## Compatibility

Actor JSON requires `evidence_stances` with exactly the cited IDs. Costs, prompts, record schema and IDs changed; old/new scores are incompatible. Analysis can inspect 0.3 records with provenance warnings but never pairs across versions. Full records contain private briefs and sealed truth for auditing; models receive only seat-filtered views.

Opaque IDs are the CLI default. `run_match(..., evidence_id_mode="original")` supports fixed audit fixtures and records the setting. It is not the default experimental condition.

## Validation

Run from the repository root without provider credentials:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests_py -v
python3 scripts/validate_project.py
python3 scripts/build_release.py --source-only
python3 scripts/validate_static_site.py
```

Regression fixtures cover context retention/isolation, delayed checks, partial failures, response corrections, HTTP retry records, all false-peace combinations, actor-specific attribution, mechanical lift, hidden-truth leakage, pairing/provenance, interrupted runs and opaque IDs. These establish implementation behavior, not model performance or construct validity.

The source download is generated at build time and excluded from Git to avoid recursive/stale archives. PDFs remain labeled archived contest documents. Local checks do not establish live-provider or deployment success.
