# Model run guide

## 1. Review the protocol

Read the protocol, preregistration, scoring guide, and all three scenario files before spending API credits. Confirm that the action weights and private briefs match the claims you intend to make.

Run the local checks:

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests_py -v
python3 scripts/validate_project.py
```

## 2. Configure exact model IDs

Copy the example configuration:

```bash
cp eval_data/models.example.json eval_data/models.json
```

Replace all three placeholders with exact model IDs. Give each one a short, stable label. Keep API keys in environment variables. The configuration names those variables but never stores the keys.

The primary runner uses OpenAI-compatible chat-completion endpoints. OpenRouter is the simplest way to run model families from different providers through one protocol, but any compatible endpoint can be used.

## 3. Inspect the schedule

```bash
third-chair plan \
  --models eval_data/models.json \
  --scenario all \
  --rotation balanced \
  --modes active,empty \
  --repetitions 1
```

The legacy balanced schedule has 18 matches and up to 243 model turns before retries. A full seat swap has 36 matches and up to 486 turns.

Use the provider's current pricing page to estimate cost from the expected context and output length. Pricing changes too often to hard-code into this repository.

## 4. Run a small smoke schedule

Before the pilot, use one scenario and one condition. This command still runs three role assignments:

```bash
third-chair run \
  --models eval_data/models.json \
  --scenario grid-vote \
  --rotation balanced \
  --modes active \
  --repetitions 1 \
  --output results/smoke.jsonl
```

Inspect every response. Confirm that:

- each model stayed in its assigned seat;
- no private reason leaked into a later prompt;
- the mediator verified only evidence it had seen cited;
- private messages reached only the intended state;
- the provider returned the expected model ID; and
- the engine state changed in the expected direction.

Delete or clearly label the smoke file before reporting pilot results. Do not mix a setup run with the preregistered batch.

## 5. Run the balanced pilot

```bash
third-chair run \
  --models eval_data/models.json \
  --scenario all \
  --rotation balanced \
  --modes active,empty \
  --repetitions 1 \
  --seed 4100 \
  --output results/pilot-matches.jsonl
```

The runner appends one JSON object per completed or failed match plus a per-call event journal. It skips previously recorded matching identities, rejects incompatible provenance, and refuses automatic replay of an interrupted journal. Preserve partial logs and use a documented new output/repetition for a rerun.

Do not change model configuration, prompts, scenario files, temperature, seed, or scoring during the batch. If a change is necessary, stop and record a protocol deviation before beginning a new batch.

## 6. Summarize

```bash
third-chair summarize results/pilot-matches.jsonl \
  --output results/pilot.md

third-chair summarize results/pilot-matches.jsonl \
  --format json \
  --output results/pilot-summary.json
```

Check that all 18 matches succeeded and all nine active/empty pairs are complete. A summary with missing pairs is useful for debugging but should not be presented as the registered pilot without explanation.

## 7. Review the match tapes

Start with:

- every critical escalation;
- every negative mediation-lift pair;
- every false-peace flag;
- every case where the mediator spent no intervention;
- every structured-response retry; and
- every returned model ID that differs from the request.

Then conduct the blinded annotation described in the annotation guide.

## 8. Plan further evaluation

The old recommendation of three repetitions and full rotation is not a power calculation and does not remove opponent confounding. Use `--actor-a model-a --actor-b model-b` for fixed actor configurations across mediator candidates. Keep role rotation as a descriptive comparison.

Choose any confirmatory sample size from pilot variance, the effect or precision target, and clustering by scenario and model configuration. More repeats of the same three stories do not establish broad generalization. See [preregistration.md](preregistration.md) and [research_roadmap.md](research_roadmap.md). Do not train an RL policy against this baseline.

## Result integrity checklist

- Raw JSONL is present and readable.
- Every public number can be recomputed from that file.
- Requested and returned model IDs are shown.
- Failed matches remain visible.
- No fixture or hand-written transcript appears in results.
- Model settings and run date are stated.
- Provider costs and credits are not confused with research sponsorship.
- API keys and private account data are absent.

