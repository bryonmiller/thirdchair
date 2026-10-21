# Prospective balanced panel and sample-size plan

Written 2026-10-21 before v0.8.0 collection. This is an offline design and power
calculation, not research findings or spending authorization. Historical results
are neither replaced nor used to select favorable anticipated effects.

## Equal exposure and repeatability

The main comparison is whole-policy LLM mediation versus its independently
executed empty-chair control. Each of 24 conditions is crossed with all six
permutations of the same three configured models. A repetition contains 144
active/control pairs, or 288 matches. In every condition and repetition, each
model occupies each role twice, with the two possible assignments of its peers.
The empty-chair mediator label identifies the corresponding active assignment;
no mediator model is called in that arm. Controls are never reused.

`expanded-v080` without fixed actors now requires full rotation, both arms,
exactly three model labels and recorded scenario/order seeds. It validates all
24 IDs, shared family/repetition opaque-ID mappings, balanced repetitions,
unique assignments, arm pairing, order, scenario fingerprints and source identity.
The previous scheduler varied opaque-ID mappings by assignment. The new
`factorial24-full-v1` mode removes that offset and uses distinct family/repetition
seeds even above 100 repetitions. Historical scheduling defaults stay unchanged.

Every model receives the same initial input when placed in the same role and
condition. Role-specific briefs, private messages and delayed evidence remain
isolated; equal exposure does not mean giving a mediator the actors' secrets.
Dynamic history depends on earlier outputs and legitimately diverges between
models and arms. This is not a shared-prefix experiment. Matching seeds aligns
stimuli, not provider randomness: the pinned configuration sends no API seed.

Freeze the ordered schedule and coverage contract using `plan --plan-output`
to a fresh path. The execution wrapper must pass the preserved contract to
`run_schedule(coverage_contract=...)` and validate the full schedule before
skipping attempted IDs. Missing combinations, changed source/scenarios/order
or duplicate rows are rejected before dispatch. Each output records the contract
hash. Preserve the full manifest/configuration and returned model/provider
metadata too; label equality alone does not establish model equality. Changing
models, provider settings or the planned repetition count requires a new plan.

Randomize pair order and within-pair arm order with the recorded order seed.
Use fresh, stateless model requests and unchanged prompts/settings/scoring.
Do not replace failures, rerun until significant, stop when a p-value crosses
a threshold, or silently change provider/model versions. Financial or technical
stops leave a transparently incomplete dataset, not a smaller confirmatory plan.

## Estimands and tests

For each of the **144 condition/seat assignments**, define two paired differences:

1. Empty minus active `crisis_cost` (sum over rounds): positive favors mediation.
2. Empty minus active `attribution_brier` (State A's final reported attribution):
   positive favors accurate attribution.

The unit is one independent active/control pair, not a turn, token, actor or
the six role permutations. Analyze mean paired differences using two-sided
paired t tests and report raw-unit means, SDs and intervals. Pairing blocks
scenario, assignment, repetition, mapping and execution proximity; it does not
assume identical random trajectories. The [NIST paired-observation procedure](https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm)
gives the statistic and its n-1 degrees of freedom.

Use Holm familywise correction across all 144 x 2 = **288 prespecified tests**,
with family alpha 0.05. Keep untestable cells in the family as non-rejections;
report them as untestable rather than assigning invented research p-values.
Report conservative simultaneous Bonferroni t intervals as well as ordinary
95% intervals clearly labeled pointwise. Holm handles dependent tests; neither
correction requires assuming the six roles or four within-family variants are
independent. See the [Holm implementation reference](https://www.statsmodels.org/v0.14.4/generated/statsmodels.stats.multitest.multipletests.html)
and [NIST simultaneous intervals](https://itl.nist.gov/div898/handbook/prc/section4/prc473.htm).

Paired t inference assumes independent repetitions and sufficiently well-behaved
paired means. Inspect skew, floor/ceiling mass, zero variance and provider/time
clustering; report assumption failures. Add paired bootstrap intervals as
exploratory sensitivity, keeping whole repetitions together when aggregating
across cells. Do not choose whichever test produces the smaller p-value. Exact
small-sample t power below is a normal-difference planning model, not proof that
these bounded simulator scores are normally distributed.

API dollars, failures/corrections, public accusations and concessions remain
separate outcomes. False peace is applicable only where B is responsible;
report its paired discordance counts and descriptive uncertainty. This power
calculation does not power rare binary outcomes, model rankings, interactions,
scripted-policy comparisons or transcript judgments. Scripted verification
remains supported with separate controls, but is not included in these counts.

A significant cost decrease alone is insufficient to establish successful
mediation. A nonsignificant Brier difference does not demonstrate preserved
attribution. Report its interval and possible harm; a formal noninferiority
claim needs a justified raw-unit harm margin and its own prospective calculation.
Do not invent that margin from favorable observed results. The current narrow
false-peace predicate cannot establish the absence of unjustified concessions.

## Repetition recommendation and sensitivity

**Planning recommendation: 121 scheduled repetitions per condition, seat
assignment and arm.** This means 121 matched-pair opportunities in each of 144
cells, not 121 repetitions across the campaign as a whole.

Assumptions: 90% power per endpoint/cell; family alpha 0.05; two-sided tests;
paired standardized effect d_z = 0.5; and independent 90% pair completion.
The effect is mean paired difference divided by the SD of paired differences,
not the SD of either arm. A half-SD effect is a transparent moderate planning
target, not an empirically established or domain-validated minimum benefit.
There are no v0.8.0 data to estimate cell-specific variance. Raw-unit thresholds
must be interpreted against the eventual SD and reported intervals.

Power uses alpha 0.05/288, conservatively planning for Holm. A noncentral-t
calculation needs **109 complete pairs** at d_z = 0.5 with no missingness.
For fixed scheduled N, the calculator averages power over K ~ Binomial(N, 0.9),
including untestable K < 2 as zero power; it selects the smallest N meeting 90%.
This yields N = 121, expected power 0.90096, under the assumptions. Missingness
depending on outcomes, model or arm can bias complete-pair effects; extra
repetitions cannot repair that bias. Report all denominators and sensitivity
bounds, with no replacement runs. The 90% applies to each test separately, not
to detecting all 288 effects or both endpoints simultaneously.

| Paired effect d_z | Complete pairs, no missingness | Scheduled repeats, 90% pair completion | Matches | Planned model turns |
| --- | ---: | ---: | ---: | ---: |
| 0.3 | 289 | 322 | 92,736 | 1,251,936 |
| **0.5 (recommended planning target)** | **109** | **121** | **34,848** | **470,448** |
| 0.8 | 47 | 53 | 15,264 | 206,064 |

Turns exclude structured corrections and transport retries; exhausted mediator
budgets may reduce calls. No current dollar estimate or available balance is
verified. These counts substantially exceed earlier exploratory budgets and
are not authorization for a large run. Five repetitions per cell (1,440
matches) remain an exploratory mapping exercise, not this powered design.
No sample size guarantees statistical significance if an effect is absent,
smaller than assumed, or obscured by missingness or drift.

An alternative overall-average claim can require fewer repetitions but answers
a different question. For illustration only, two endpoints at family alpha
0.05, d_z = 0.5 and 90% usable *whole-panel repetition blocks* need 59 blocks.
That d_z is standardized by the SD of the panel average, not by cell SD; the
90% block availability assumption is much stronger than 90% pair availability.
This is not a recommended cheaper substitute or evidence for each combination.
Do not pool 144 correlated cells as if they were independent replications.

Reproduce the recommendation without credentials or dependencies:

```bash
.venv/bin/python scripts/plan_power.py
.venv/bin/third-chair plan --models eval_data/models.example.json \
  --scenario expanded-v080 --rotation full --modes active,empty \
  --repetitions 121 --seed 188000 --order-seed 20261022 \
  --plan-output /tmp/thirdchair-v080-plan-121.json
```

The numerical implementation integrates the noncentral t over its chi-square
denominator. Tests check known Student-t quantiles, nominal null size, quadrature
convergence, the minimum-N boundary and an independent synthetic Monte Carlo
simulation with missingness. The [paired-t power reference](https://www.statsmodels.org/dev/generated/statsmodels.stats.power.TTestPower.power.html)
defines d_z, n and the two-sided test; no statsmodels dependency is installed.
This methodological plan does not implement a finished confirmatory analysis
pipeline or substitute for an approved collection budget.

Repeated model calls can increase precision conditional on these six handcrafted
families and pinned endpoints. They do not create additional independent crisis
types, freeze provider weights or establish real-world external validity. Role
rotation changes actor opponents with the mediator, so it cannot by itself
identify a causal ranking of mediators. Independent review remains recommended
for stronger claims and is not a prerequisite for exploratory collection.
