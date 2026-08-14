# Results policy

No model results are included in version 0.3.0.

A finding belongs in this directory only when the release contains the raw JSONL needed to trace it. Every result must identify the role assignment, requested and returned models, scenario, mediator condition, repetition, timestamp, settings, transcript, verification choices, and deterministic scores.

Scripted choices, hand-written examples, unit-test fixtures, and interface walkthroughs are not model results. They must not appear in the tournament table.

Recommended filenames:

```text
pilot-matches.jsonl
pilot-summary.json
pilot.md
```

An active-mediator claim should have its matched empty-chair record. Missing and failed pairs remain visible.
