# Crisis mediation research roadmap

Current next step: the [0.6.0 post-verification mediation diagnostic](post_verification_protocol.md) fixes the third model as mediator and reserves its final intervention for communication after a check. It introduces no new crisis consequences or training. Independent review may remain pending for a labeled engineering smoke; it remains required before the substantive larger study.

The [0.5.0 methodology review](methodology_review.md) and [bounded evidence-access diagnostic](followup_protocol.md) guide immediate work within the mediation project. The diagnostic supports the original objective of crisis de-escalation with epistemic integrity. The environment extensions and RL work below remain proposals. The September 2026 [ProMediConv preprint](https://arxiv.org/html/2609.11101v1) trains a mediation strategy planner with RL in legal disputes. This overlaps with our proposed method, but does not answer the interstate de-escalation question. Neither learned strategy selection nor a change of domain alone establishes a contribution.

## Question and contribution

**Can AI mediators de-escalate simulated interstate crises while preserving accurate attribution and avoiding unjustified concessions?** Communication, verification, and abstention are candidate mechanisms. A successful crisis intervention may preserve dialogue or encourage reciprocal restraint without a comprehensive settlement; durable peace requires additional outcomes beyond the current horizon.

The candidate contribution is an empirical analysis of mediation outcomes, their mechanisms, and failures under adversarial uncertainty. A later learning study could examine reward-induced false peace and transfer failures. Training a mediator is not itself novel. [Mediated Multi-Agent Reinforcement Learning](https://arxiv.org/abs/2306.08419) trains constrained mediators; [ProMediate](https://aclanthology.org/2026.findings-acl.1479/) studies proactive interventions; [AgentMediation](https://ojs.aaai.org/index.php/AAAI/article/view/40177) addresses dispute mediation and superficial consensus. [Counterfactual RL deception detection](https://aclanthology.org/2025.findings-acl.1287/), [Welfare Diplomacy](https://arxiv.org/abs/2310.08901), [communication power regularization](https://arxiv.org/abs/2404.06387), and [SoCRATES](https://github.com/DISL-Lab/SoCRATES) further limit broad novelty claims.

The targeted review suggests a plausible question joining limited delayed verification, advisory actions, epistemic constraints and unfamiliar opponents. It does not establish absence of overlapping work. Compare exact mechanisms and experiments before a larger commitment. No high-impact publication claim is warranted yet.

## Immediate sequence within the mediation study

1. Complete the bounded evidence-access engineering diagnostic with its review status recorded. Obtain independent review before substantive research expansion. Its attribution-first analysis tests whether information availability explains an observed failure; it does not redefine mediation success.
2. Evaluate empty chair, the verification comparator, and full LLM mediation under matched actor configurations and information access. Report modeled de-escalation, attribution, and accountability indicators separately, including actual communication use and failed runs. A full-policy difference is not a clean estimate of communication: add a controlled ablation matching verification decisions/results and budgets before making that claim.
3. Develop and independently review a small set of meaningful reciprocal-restraint, temporary-pause, and containment opportunities. Connect proposals to observable actor choices and within-horizon implementation. Define unsupported concessions and preserved inquiry explicitly; do not award a numerical bonus for proposing an agreement or claiming to accept one. Freeze this new design before collecting its results.

These steps can produce a useful mediation evaluation without RL. If verification alone accounts for performance in the current cases, report that limit and test whether the scenarios offer meaningful opportunities for communication before expanding the study. The following learning extension is conditional on those findings and the decision gates below.

## Minimum environment for a later learning study

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

The 0.4.0 repair completes baseline implementation corrections, and 0.5.0 adds diagnostic measurements and controls. Neither establishes the proposed environment's construct validity, learning value, or transfer performance. The immediate priority is the mediation sequence above; a later decision is whether a small non-learning prototype can satisfy the learning-environment gates without a major rebuild.
