# OpenRouter pilot setup

Version 0.4.3 supports controlled OpenRouter requests, explicit mediator action rules and neutral verification target links after exploratory setup failures. Offline and simulated-HTTP tests pass; the revised prompt still requires a real-provider smoke run. This guide prepares an exploratory evaluation of the existing three-scenario baseline. It does not authorize RL training or establish a confirmatory sample size.

## Configure three models

Install the merged revision and copy the template:

```bash
python3 -m pip install -e .
cp eval_data/models.example.json eval_data/models.json
```

Replace each `model` placeholder with an exact model ID from OpenRouter. Replace its `provider.only` placeholder with one provider endpoint slug available for that model. Copy the endpoint slug from the model's provider listing; a model vendor prefix is not necessarily the hosting provider. A base provider slug can cover multiple regions or variants, so use the full endpoint slug where offered and document any remaining ambiguity.

Set `OPENROUTER_API_KEY` in your local environment or secret manager. Do not put its value in this file, a transcript, or Git. Set a modest credit limit on the API key in OpenRouter before testing; the runner does not enforce a dollar budget.

| Configuration | Meaning |
| --- | --- |
| `provider.only` | One allowed provider endpoint for this model |
| `provider.allow_fallbacks: false` | Do not switch to other providers after failure |
| `provider.require_parameters: true` | Reject routes that cannot support requested parameters |
| `temperature: null` | Omit temperature when unsupported; this uses the provider default, not temperature zero |
| `send_seed: false` | Omit the API seed when unsupported; the experiment seed still controls evidence IDs and scheduling |
| `max_tokens` | Total completion budget, often shared by reasoning and visible output |
| `reasoning: null` | Omit reasoning controls; provider/model defaults apply |
| `reasoning: {"effort": "low"}` | Request a supported effort level |
| `reasoning: {"max_tokens": 1024}` | Request a supported reasoning budget; the total must be larger |
| `timeout` | Request timeout in seconds |

Use either reasoning effort or a reasoning token budget. The 4,096-token total in the example is a starting value, not a model-independent guarantee. Check the selected model/provider's supported parameters before the smoke run. Some models require reasoning, ignore optional controls, or need more output space. Do not set every model to identical unsupported parameters to create an appearance of fairness. Decide which inference settings define each experimental condition and record the differences.

The runner exposes a limited, validated subset of provider and reasoning controls. Unsupported configuration keys are rejected rather than silently ignored. It does not add model fallbacks, automatic model routing, tools or web search.

## Check locally before spending credits

```bash
third-chair check-config --models eval_data/models.json
third-chair plan --models eval_data/models.json \
  --scenario grid-vote --actor-a model-a --actor-b model-b \
  --modes active,empty --repetitions 1 --seed 4100
```

`check-config` makes no network requests and prints no API key values. It exits nonzero for incomplete setup. A pass only establishes local configuration consistency; it does not check credits, model availability or actual parameter support. `run` applies these same checks before calling a provider.

With three configured models, the planned schedule has six matches and at most 81 planned model turns before retries. The two state configurations stay fixed while each model takes the mediator seat. Separate role contexts permit a model to occupy both a state and mediator seat. These are independently executed matched controls, not shared-initial-intention forks.

## Run the diagnostic schedule

After reviewing the selected models' prices and settings:

```bash
third-chair run --models eval_data/models.json \
  --scenario grid-vote --actor-a model-a --actor-b model-b \
  --modes active,empty --repetitions 1 --seed 4100 \
  --output results/openrouter-smoke.jsonl

third-chair summarize results/openrouter-smoke.jsonl \
  --format json --output results/openrouter-smoke-summary.json
```

Inspect the JSONL, its `.events.jsonl` journal, the summary warnings, and OpenRouter usage. Proceed only after checking:

- All six matches succeeded and all three active/empty pairs are compatible.
- Request payloads, returned model IDs and provider identities match the intended conditions.
- Provider metadata is present for every response and no provider changed mid-match.
- Completions end normally, JSON responses satisfy the role schema, and reasoning leaves enough visible output space.
- Evidence, private messages and verification results appear only in their authorized role contexts.
- Actual usage, latency and failures fit the planned budget.

The client requests `X-OpenRouter-Metadata: enabled`. It reads a reported top-level provider when present, otherwise the uniquely selected provider in routing metadata. Provider display names may differ from request slugs; inspect the raw metadata rather than guessing an alias mapping. Summaries exclude a match when a role changes model/provider or lacks required provider metadata, and exclude pairs with different actor providers. The full failed or excluded records remain available. Report exclusions and failure rates; success-only comparisons can be biased.

An empty response or a finish reason other than `stop` stops that model turn without a JSON-correction retry. Usage and raw responses remain logged. A match failure does not cancel the rest of the scheduled matches. Ordinary invalid JSON still permits one correction; transport failures can trigger additional requests. The 81-turn estimate is not a spending cap. A seed does not guarantee deterministic API behavior.

If a response lacks provider identity, do not infer it from the requested model or silently count the pair. Inspect routing metadata and caching/account settings. OpenRouter documents that cache hits can omit router metadata. Keep such cases excluded until provenance is resolved. Routing metadata and matching provider names do not prove that weights, quantization or infrastructure stayed identical.

## Migrating after the verification prompt repair

Version 0.4.2 explicitly requires a non-empty public announcement for a verification request and exactly one listed evidence ID in `target_evidence_id`. It preserves the validator's existing acceptance rules, correction-attempt limit, action costs and scoring. The model must supply its own announcement; the runner does not invent text or silently repair an invalid action.

Keep the original failed setup files and use a new filename such as `results/openrouter-smoke-v3.jsonl`. Repeat all six diagnostic matches under the new source revision. Do not fill the failed pair with a new successful run or pool old and new prompt versions. Inspect initial validation failures and correction attempts even when a match eventually succeeds; they contribute to cost and interface reliability. A clean setup batch is a readiness check, not proof of a low failure rate.

## Migrating after the verification target-link repair

Version 0.4.3 adds `verification_targets` to neutral cards that already offered a named document check. The prompt links the liaison card to the target evidence ID, provided that target is already in the mediator's checkable set. It does not reveal uncited private evidence or expand the available actions. Selecting the liaison ID still fails validation; the runner does not silently substitute the target. Other opaque cited IDs may still have undisclosed contents, so the prompt explicitly forbids inventing descriptions from IDs alone.

Keep all 0.4.2 pilot records, including incomplete matches. Start a separate diagnostic across all three scenarios using a new output filename such as `results/openrouter-diagnostic-v043-r1.jsonl`. Inspect failure counts and denominators before comparing outcomes. Do not patch prompts per model, replace failed cells until they pass, or present success-only averages as overall model performance.

These links describe announced check availability, not authenticity. In the current three handcrafted cases, the round-two offers happen to target forged documents. Expanded counterfactual families must vary authenticity and check availability independently before making generalization claims. The cost-of-inaction and accountability model still needs separate research design work.

## Freeze the exploratory batch

Keep setup runs separate from reported pilot data. After successful smoke inspection, record the source commit, exact configurations, scenario set, outcome definitions, repetitions and exclusion policy. Choose a new output path. Any later parameter change or upgrade starts a new batch; resume checks reject changed settings, and recorded failures are not silently rerun.

For the first expanded exploratory pilot, use all three scenarios with the same fixed actors and active/empty conditions. That is 18 matches and at most 243 planned turns before retries for one repetition. Determine further repetitions from pilot variability and the intended precision, accounting for scenario/model clustering. Three public scenarios and the current inaction/accountability model remain limits on generalization.

## API references

Checked 2026-10-17:

- [Provider routing and endpoint slugs](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Reasoning budgets and visible output](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
- [Router metadata, including cache limitations](https://openrouter.ai/docs/guides/features/router-metadata)
- [Chat completions API](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion)
