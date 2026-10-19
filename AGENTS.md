# The Third Chair: execution instructions

The research question is whether AI mediators de-escalate simulated interstate
cyber crises while preserving attribution accuracy and avoiding unjustified
concessions. Keep mediation central. Do not reframe this as only an attribution
benchmark or begin RL development.

- Inspect branch, status, and `docs/codex_handoff.md` before work. Preserve user
  changes, local model configurations, and every experimental batch.
- The preserved 0.6.1 baseline is commit
  `ae335fdebdc4e16997102b58ead60789c3c42656`. Develop new experiments on a separate
  branch and version; never append to, overwrite, or pool historical batches.
- Read `docs/shared_prefix_protocol.md`, `docs/public_history_repair.md`,
  `docs/post_verification_protocol.md`, `docs/methodology_review.md`, and
  `docs/annotation_guide.md` for this experiment. The roadmap's learning extensions
  are proposals, not authorized work.
- Local implementation, offline checks, documentation, and a reviewable PR are
  authorized. Leave merging to the owner. Paid API collection requires an agreed
  run plan and spending cap; do not launch a batch on your own.
- Do not read or display credential values. Check only whether named environment
  variables are present. Never commit local model settings, raw results, secrets,
  or unpublished materials without explicit approval. Stage explicit file paths;
  inspect the staged diff. `results/` and `eval_data/models.*.json` stay local,
  except their tracked README and example configuration.
- Write prospective protocols and limitations before collecting data. Preserve
  failures and interrupted journals; do not rerun cells until scores improve or
  tune prompts to obtain favorable mediation outcomes.
- Preserve role-authorized observations, private-message isolation, and delayed
  verification. Shared evaluator checkpoints must never become model prompts.
- Independent scenario review remains outstanding before substantive trials.
  Report modeled cost and attribution separately. Neither a self-reported
  acceptance nor a lower cost establishes successful mediation or accountability.
- Run `.venv/bin/python -m unittest discover -s tests_py` and
  `.venv/bin/python scripts/validate_project.py`. Tests use local fixtures, not
  paid APIs. Source ZIP generation writes build artifacts; it is not a read-only
  check. Update the handoff with verified checks and remaining gates.
