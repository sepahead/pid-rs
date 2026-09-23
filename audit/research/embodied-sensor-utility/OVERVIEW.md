---
author: Sepehr Mahmoudian
date: 2026-09-23
---

# Wibral-line PID for physical intelligence

The immediate application is **offline sensor analysis for embodied prediction**: two cameras, with optional audio, used to predict a separately measured future physical outcome. This is an attainable first step toward robust world models and robot policies. It is not yet a demonstrated training or control improvement.

The selected functional is **Makkeh–Gutknecht–Wibral categorical shared exclusions (MGW)**, in nats, with signed atoms. The [defining paper](https://arxiv.org/abs/2002.03356v5) is distinct from continuous shared exclusions and from other PID definitions. Fitted bins define a categorical estimand; raw sensor information is a different object.

## The practical finding

An extra sensor's value is not its synergy alone. For two-source atoms $R,U_1,U_2,S$, the added Shannon information is $U_2+S$. If source 1 is available with probability $a$ and source 2 with probability $b$, with availability indicators $M_1,M_2$ such that $M_1\perp M_2$ and $(M_1,M_2)\perp(X_1,X_2,Y)$, the added Bayes log-loss value is

$$
\Delta=b[(1-a)R+U_2+aS].
$$

Both predictors must see the same mask, and the complete-data policy and target law must remain fixed. Redundancy can provide backup value; unique information and synergy combine when sensors are present. The full proof includes correlated failures and data-dependent missingness in the [detailed report](EXPOSITION.md).

For independent fair bits $A,B,U$, set the same target $Y=(A,B)$ and baseline $X_1=A$. Candidate noise $U$ and useful complement $B$ both have MGW synergy $\ln(4/3)$. Their added information is respectively zero and $\ln2$. A duplicate $A$ has zero synergy but supplies backup value when the first copy is unavailable.

![One target law, three candidate sensors. Signed unique information distinguishes noise from a useful complement despite equal synergy; duplication can have backup value.](figures/signed-atoms-and-sensor-value.svg)

There is also a useful limit: the expected Bayes log-loss reduction relative to the no-source predictor, under a fixed law and exogenous availability, depends only on subset mutual information. For two to four sources, that is 3, 7 or 15 values. Full PID's 4, 18 or 166 atoms provide a finer allocation, but no extra decision information for that exact objective. PID must earn additional cost through a useful diagnostic question or a separately justified objective.

## What exists and what it supports

| Work | Useful role | Remaining boundary |
|---|---|---|
| Rust categorical MGW for 2–4 sources | Offline signed atom calculation with budgets and cancellation | No completed sensor benchmark follows from library availability |
| [Four classical finite-PMF foundations](../../formal/lean-finite-logscore/PUBLICATION.md) | Mass/measure, integral, Gibbs and log-score results checked locally in Lean | Unconditional law only; 13 downstream conditional sensor/application targets remain open |
| Equal-synergy and target-copy formal work | Reject an invalid synergy-only selection rule | Exact theorem premises and replay status remain in the theorem maps |
| Fixed-alphabet continuity and dependence-aware law bounds | Conditional tools for estimator sensitivity | A valid sampling/dependence model is still required |
| Finite-prefix mean, bias and gradient work | Mathematical tools for a future bounded encoder experiment | Not an implemented robot-training method |
| Availability exposition | Complete classical derivation, controls and experiment design | Conditional prediction and availability/mask arguments remain handwritten; no scientific-priority claim |

The [mathematical results guide](../../../MATHEMATICAL_RESULTS_GUIDE.md) points to standalone proofs and exact formal status. A verified mathematical intermediate step does not establish estimator calibration or physical value.

## Rust implementation and computational cost

Rust supplies budgeted categorical MGW for two to four sources through the [averaged API](../../../crates/pid-core/src/lib.rs). Event calculations are quadratic in the occupied complete states $K$ for each lattice node. Averaged output saves retained pointwise results; row and PMF storage remain. Dense log-score validation and evaluation over $K_Y$ target labels take $O(K_Y)$ work and $O(1)$ extra storage beyond the inputs.

No Rust log-score evaluator or learner is added; floating-point execution is unverified. Feature extraction, masked prediction, training and resampling add costs. Begin offline: latency and learning benefit are unmeasured. See the [full cost discussion](EXPOSITION.md#13-rust-implementation-and-computational-cost).

## The ecosystem connection

CREBAIN produces observations; NCP transports sensor records; Prisoma inspects experiments; pid-rs computes information; Galadriel can retain diagnostic evidence. Manwe supplies a separate tracking setting. The detailed report distinguishes existing consumers from proposals.

The current two-camera-plus-audio example records five images and 800 pressure samples over six 120-Hz body ticks. That proves a capture composition, not independent statistical replication. The missing step is a frozen feature table joined to future reference labels. Use one declared episode/landmark unit, preserve timing and missingness, fit transforms only on training episodes, and evaluate untouched episodes.

## How practical value will be tested

Start offline with all eight sensor subsets. Measure predictive loss, availability, runtime and memory. Keep fixed-model outages separate from retrained subset models. Compare MI/CMI, subset task loss and established masking methods. [Masked sensor training](https://proceedings.mlr.press/v270/skand25a.html) and [MAD multi-view reinforcement learning](https://proceedings.mlr.press/v305/almuzairee25a.html) are relevant baselines; no superiority to them is established here.

The detailed report derives a conservative paired-episode loss bound and states its independence and bounded-probability assumptions. It also explains why natural occlusion needs conditional laws, why more sensors can defeat finite-data estimation, and why an action-conditioned latent must not be evaluated against its own injected action.

Testing control, placement or re-identification requires explicit target, policy, association and cost contracts. Require useful task gains against matched baselines and retain negative results.

**How to cite:** Sepehr Mahmoudian, *Wibral-line PID for physical intelligence*, pid-rs technical report, 2026. Include the exact repository commit or release. Use the [citation metadata](../../../CITATION.cff) for the software and cite the defining method papers separately.
