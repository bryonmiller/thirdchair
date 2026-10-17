# Bounded research direction

## Question and contribution

Can a mediator selecting bounded messages, verification or abstention reduce modeled harm while preserving evidence and legitimate inquiry under adversarial uncertainty?

The candidate contribution is an empirical analysis of reward-induced false peace and transfer failures. Training a mediator is not itself novel. [Mediated Multi-Agent Reinforcement Learning](https://arxiv.org/abs/2306.08419) trains constrained mediators; [ProMediate](https://aclanthology.org/2026.findings-acl.1479/) studies proactive interventions; [AgentMediation](https://ojs.aaai.org/index.php/AAAI/article/view/40177) addresses dispute mediation and superficial consensus. [Counterfactual RL deception detection](https://aclanthology.org/2025.findings-acl.1287/), [Welfare Diplomacy](https://arxiv.org/abs/2310.08901), [communication power regularization](https://arxiv.org/abs/2404.06387), and [SoCRATES](https://github.com/DISL-Lab/SoCRATES) further limit broad novelty claims.

The targeted review suggests a plausible question joining limited delayed verification, advisory actions, epistemic constraints and unfamiliar opponents. It does not establish absence of overlapping work. Compare exact mechanisms and experiments before a larger commitment. No high-impact publication claim is warranted yet.

## Minimum next environment

Build a separate module inside this repository with one transition core for scripted and later LLM actors. Train only the mediator: single-agent RL in a multi-agent environment. Preserve the existing baselines independently.

Use a Gymnasium-compatible finite-horizon interface with observations/history, legal-action masks, delayed checks and budgets. Six decision opportunities and two interventions are provisional development settings. Expose public state and authorized messages/evidence only. Observations, masks, diagnostic fields, previous-reward features and checkpoint metadata must not disclose latent responsibility.

Five action categories can produce 21 discrete slots: abstain, four templates across joint/private-A/private-B channels, and verification of up to eight evidence slots. Templates propose pause, containment, inquiry or closure. Actors retain their choices and may refuse. Closure must remain capable of an unjustified concession; masking every bad choice would erase the failure hypothesis.

Separate containment, coercion, attribution and settlement decisions. Model ongoing damage, evidence deadlines, collateral costs and enforceable commitments. Some cases must favor timely containment/investigation, others justified restraint. Messages act through actor responses, not numerical bonuses. These assumptions need independent review and are not geopolitical truths.

Both learned policies minimize the same operational harm, collateral and intervention-cost objective. The constrained variant adds registered false-peace and evidence-integrity risk budgets. Expected-risk constraints are not per-episode guarantees. Keep unsupported closure, false concessions, lost opportunities and attribution accuracy separate. Independent trace review and alternative reasonable rubrics test construct validity.

## Scenarios and comparisons

Start with two development mechanism families and coherent authentic/tampered and responsible/innocent variants. Hold out a different mechanism family and opponent response rule. Keep descendants of each base case and historical incident in one split. Identical observable histories should not elicit different decisions just because hidden truth differs.

Use [ICBe](https://github.com/CenterForPeaceAndSecurityStudies/ICBEdataset) and [ICB](https://sites.duke.edu/icbdata/data-collections/) for historical mechanisms after inspecting codebooks and selected releases. Record version, hashes, licensing and transformations before redistribution. Historical associations do not calibrate causal harm weights. Independent crisis/cyber review remains necessary. A later recognition audit cannot prove absence of contamination.

Compare empty chair, random valid actions, strong rules, a same-information planner, a matched-action LLM, ordinary RL and constrained RL. Keep unrestricted LLM mediation separate. Train against inexpensive fixed scripted opponents; freeze policies before unfamiliar LLM-actor tests using the same information and consequence interface. Establish adapter parity before interpreting transfer failure.

Start with tabular or compact methods if adequate. New RL algorithms, adaptive opponent training, full MARL, JEPA, Civilization integration and elaborate interfaces are outside scope.

## Decision gates

1. Pass information-isolation, delayed-check, event-replay, pairing and adapter-parity checks.
2. Independently validate multiple legitimate strategies and false-peace positive/negative cases. Stop if always-wait dominates or the hypothesis is encoded into the score.
3. Freeze reward components, outcome rubrics, feasible risk budgets and data splits before training.
4. Compare learning with rules and planning. If simple methods explain the result, drop the RL-methods framing unless a substantive benchmark finding remains.
5. Register effect/precision targets and plan sample size from pilot variance. Report paired block differences, family-specific effects, training-seed variation, failures and sensitivity. Repeated stories do not support population-level crisis claims.
6. Require untouched mechanisms/opponents for generalization and live LLM tests for LLM-transfer claims.
7. Reassess after a bounded prototype. A proposed initial learning cap, if earlier gates pass, is five seeds per variant and 20,000 episodes per seed. This is an investment limit, not a power calculation or proof that more training could not help.

The 0.4.0 repair completes baseline implementation corrections. It does not pass the proposed environment's construct-validity, learning or transfer gates. The next decision is whether a small non-learning prototype can satisfy them without a major rebuild.
