# Threat model

## What needs protection

The project must protect model credentials, role boundaries, private scenario information, transcript integrity, and the distinction between real results and fixtures.

## Untrusted model-to-model content

A state can place text in its public message that looks like an instruction to the opponent or mediator. Every system prompt tells the receiving model to treat quoted actor content as untrusted and to keep its assigned role.

The runner passes only structured fields. It never inserts a model message as a system prompt. Validation rejects extra fields and unknown evidence IDs.

This does not eliminate semantic manipulation. Persuasion, bluffing, and strategic framing are part of the evaluation. The boundary is that one model should not be able to rewrite another seat's response contract.

## Private-information leakage

State private briefs and private reasons stay inside that seat's prompt and match record. The mediator sees only public messages, announced postures, cited evidence IDs, and neutral material.

The output record contains private information for research audit. Do not publish a live match transcript before deciding whether those fields should be redacted or separated from the public tape.

## Cross-seat memory

Provider calls are stateless from the runner's perspective. Every prompt is rebuilt from registered context. A model provider may retain data according to its own terms, so researchers should use approved accounts and review provider retention settings before running sensitive, nonfiction material.

The included scenarios are fictional and contain no operational secrets.

## Credential handling

API keys are read from environment variables. The model JSON stores only the environment-variable names. Results, prompts, errors, and raw provider responses must never contain keys.

The repository ignores `.env` files, private model configuration, generated result logs, and certificate files by default.

## Returned-model substitution

Routers and providers may return a model ID different from the requested ID. The runner stores both. A mismatch must be reviewed before the match enters a comparative claim.

## Retry bias

The runner permits one correction after a structured-output failure. Both attempts remain in the record. A failed second attempt ends the match. Repeated silent retries would select for lucky compliance and are not allowed.

## Scenario-answer leakage

The public release contains sealed truth, so models may eventually learn the cases. The contest pilot should record its date and exact model versions. Longitudinal work needs held-back scenarios stored outside the public repository until after collection.

## Score gaming

A model can lower escalation by choosing passive postures regardless of evidence. The archive case and narrow false-peace flag reveal only some instances. Correct attribution combined with harmful inaction can still receive a good score; this baseline must not be used for RL training. A model can also spend intervention tokens on harmless moments to appear active, so lift per intervention and timing annotation remain separate.

No numeric rule can prevent every game-specific strategy. Public transcripts and component scores are part of the security design.

## Researcher overreach

The simulation should not be presented as evidence that a model can mediate real armed conflict. It tests behavior inside three fictional cyber crises with a specific action engine. Public claims must stay at that level.

