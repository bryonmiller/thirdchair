# Bounded shared-pool request retries

This execution policy is opt-in and must be bound to the run authorization.
It does not change model prompts, scenario order, scientific scoring or completed
outcomes. A retry sends the identical request bytes for the current turn. It never
restarts a match, regenerates a previous response, or resumes a stopped process.

Retry only a complete HTTP 429 response whose top-level error metadata explicitly
identifies `upstream_provider_shared_pool`. Permit five additional attempts
(six total), with delays of 3, 6, 12, 24 and 45 seconds plus uniform 0-1 second
jitter. Honor a valid larger Retry-After value, including an HTTP date. Invalid
headers or ambiguous/malformed error bodies do not authorize retries. Jitter is
operational randomness and does not change any experiment seed.

Use one shared pacer per sequential runner: at least 1.5 seconds between request
starts for the same model. Preserve the scientific role/turn ordering. Pacing
reduces short bursts; it cannot guarantee upstream capacity or prevent every 429.

Before every physical dispatch, commit a fresh spending reservation. Retain the
full reservation for each rejected attempt unless reliable billing evidence
settles it. Continuing after an explicit shared-pool rejection is the sole new
exception to stopping on an unresolved dispatch. Timeouts, lost connections,
missing success costs, malformed responses, authentication/billing errors and
exhausted retries remain terminal. Each rejected request is journaled, even when
a later retry succeeds. Rejected reservations reduce the remaining budget.

Provider pinning remains the default. Enabling fallback or changing quantization,
model, max_tokens or require_parameters changes the configuration and requires
prospective documentation. Do not copy example model IDs into frozen campaigns.
Preserve failed historical cells; this policy applies prospectively only.

The utility in `scripts/request_retry.py` decides delays and pacing; the caller
must supply strict error classification, durable accounting and retry journaling.
It has no credential access, network transport, experiment-launch command or
automatic restart. Tests use synthetic clocks and responses.

References: [OpenRouter error handling](https://openrouter.ai/docs/api_reference/errors-and-debugging)
documents Retry-After; [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
documents provider restrictions and fallbacks. Neither establishes that every
rejected request is free or that retries guarantee campaign completion.
