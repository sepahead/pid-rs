# Finite-PMF logarithmic score: formal source and local evidence

Author: **Sepehr Mahmoudian**. Published source record, 23 September 2026.

Four finite-probability targets passed local Lean compilation, exact target and axiom inspection,
and a separate fresh kernel replay. They establish normalized probability masses, the finite
expectation formula, supported Gibbs nonnegativity, and logarithmic-score decomposition, lower
bound and attainment. This package preserves the exact eight compiled source files and two raw
owner observations. Its [receipt](REPRODUCTION.json) records the accepted local execution and its
limits. A portable automated replay gate and hosted verification of this package remain open.

The result is a classical probability foundation for the
[sensor-utility exposition](../../research/embodied-sensor-utility/EXPOSITION.md). It proves no
conditional sensor or PID theorem and makes no scientific-novelty claim. All thirteen additional
targets listed below remain open.

## Exact mathematical scope

Let $Y$ be a finite, nonempty alphabet, and let $r,q$ be normalized PMFs on it. Write
$r_y=\operatorname{mass}(r,y)$, $q_y=\operatorname{mass}(q,y)$, and
$S=\{y:r_y>0\}$. The scoring premise is $q_y>0$ for every $y\in S$.
It allows positive forecast mass outside $S$, as well as zeros outside $S$.
No sample, independence assumption, fitted model, or asymptotic limit occurs in these statements.

The measure $\mu_r$ is Mathlib's actual `PMF.toMeasure`, with every subset measurable. Natural
logarithms give nats. The source definitions are

$$
L_r(q)=\int_Y-\log q_y\,d\mu_r(y),\qquad
H(r)=-\sum_{y\in S}r_y\log r_y,\qquad
D(r\Vert q)=\sum_{y\in S}r_y\log(r_y/q_y).
$$

The four exports in [Candidate.lean](sources/FiniteSensorBayes/Candidate.lean) have the common
namespace `FiniteSensorBayesCandidate`:

| Export | Checked target and conclusion |
|---|---|
| `finiteMass` | `FiniteSensorBayes.Raw.FiniteMassTarget`: the discrete measure is a probability measure; real masses sum to one, lie in $[0,1]$, and are positive exactly on support; each singleton has its native PMF mass. |
| `finiteExpectation` | `FiniteSensorBayes.Raw.FiniteExpectationTarget`: every real function on the finite discrete space is integrable, with integral $\sum_y r_y f(y)$. |
| `gibbs` | `FiniteSensorBayes.Raw.GibbsTarget`: the stated supported positivity premise gives $D(r\Vert q)\ge0$. |
| `logScore` | `FiniteSensorBayes.LogScoreOwner.FiniteLogScoreTarget`: under that premise, $L_r(q)=H(r)+D(r\Vert q)$, $H(r)\le L_r(q)$, and $L_r(r)=H(r)$. |

The last export is one theorem with three conjuncts. It establishes proper scoring on the admitted
finite-loss domain, including attainment by the true law; it does not assert uniqueness of the
minimizer. All exports retain their fully quantified owner statements and one universe parameter.

Lean's `Real.log 0` is zero. At a zero true mass this convention contributes nothing to the
expectation. It cannot represent the infinite loss of predicting zero for a possible outcome.
The support premise therefore matters: these results make no extended-real claim for such an
inadmissible forecast. Normalization is supplied by genuine PMFs, rather than an assumption about
arbitrary input vectors.

Gneiting and Raftery's classical logarithmic-score discussion connects scoring, Shannon entropy
and KL divergence (§3.1, Example 3). Their convention maximizes `log q`; this package minimizes
its negative. The paper treats strict propriety, whereas the four exported targets here stop at
the stated lower bound and attainment. See
[*Strictly Proper Scoring Rules, Prediction, and Estimation*](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)
(2007, DOI [10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437)).

## Preserved sources and local execution

| Source | Role |
|---|---|
| [Contract.lean](sources/FiniteSensorBayes/Contract.lean) | Native PMF, mass, discrete measure, supported entropy/KL and further conditional definitions. A definition of an object proves no property of it. |
| [RawTargets.lean](sources/FiniteSensorBayes/RawTargets.lean) | Three accepted foundation propositions and thirteen still-open propositions. |
| [FiniteLogScoreTarget.lean](sources/FiniteSensorBayes/FiniteLogScoreTarget.lean) | The fourth owner proposition, using unchanged Contract definitions. |
| [Candidate.lean](sources/FiniteSensorBayes/Candidate.lean) | Four exported theorem proofs and four private theorem helpers. |
| [ExactTypeComponent.lean](sources/FiniteSensorBayesOwner/ExactTypeComponent.lean) | Closed, fully quantified target comparison and allowed-axiom inspection. |
| [ModuleInventory.lean](sources/FiniteSensorBayesOwner/ModuleInventory.lean) | Candidate-module declaration, import and axiom inventory, including private helpers. |
| [ImportBaseline.lean](sources/FiniteSensorBayesOwner/ImportBaseline.lean) | Owner import observation without the candidate. |
| [CoreJudge.lean](sources/FiniteSensorBayesOwner/CoreJudge.lean) | Four-export exact-target checks and whole-module observation with the candidate. |

Some preserved owner comments say “uncompiled,” “proposal,” or “unadmitted.” They describe source
preparation before the accepted execution. They remain unchanged so these snapshots match the
compiled bytes. The later execution status is recorded here and in REPRODUCTION.json; the
comments neither retract that observation nor grant acceptance to the open targets.

The accepted candidate is 5,250 bytes, SHA-256
`393d6db5bac4a988b567b682692872ea175b0fd38f3fae40648c9fa9d817ad62`.
Development attempt 2 was the first complete success. One final replay used identical source
bytes in a fresh source/object location. Both stages recorded eight `lean --trust=0` compilations,
successful exact-target/module checks, and `leanchecker --fresh FiniteSensorBayes.Candidate`
returning zero. Local acceptance closed at 2026-09-23 10:27:20 UTC.

Lean was version 4.33.0; Mathlib was revision
`db584cd6d46c92f209a44c0f1c829460d327499d`. The exact binary and source hashes are in the receipt.
Every candidate declaration, including the private helpers, used only `Classical.choice`,
`Quot.sound`, and `propext`. The final
[import-baseline stdout](evidence/import-baseline.stdout) and
[core-judge stdout](evidence/core-judge.stdout) are unchanged raw outputs, including their markers.
They contain 4,824 and 4,825 import-closure rows respectively; the local outer check accepted the
declared candidate entry as the sole difference.

Those stdout records are observations, not standalone acceptance. The receipt projects the
retained native exits, outer acceptance, source identities, and pre/post dependency-census
observations. Full machine-specific execution records remain in local custody; their digests
identify those records but do not make them publicly replayable. Kernel replay uses the same Lean
implementation and does not independently rerun the owner's `run_cmd` checks. The declared
dependency census is not native-loader closure, independent source-to-cache authentication, or
continuous filesystem monitoring. No independent implementation, human review, institutional
review, or cryptographic attestation is claimed.

Attempt 1 is retained as negative evidence. Its 5,251-byte candidate had SHA-256
`faa7c242ee5a364cc8c17f238d5152b8c1d550eef4673825dd81a0ffa0e7bd0f`.
Compilation failed at line 121 because the style linter preferred `let` to `letI` in a proposition
and warnings were errors. It received no judge or kernel acceptance. The only candidate edit was
that one-token correction; statements, owner files, and linter settings were unchanged. The
receipt supplies a diagnostic summary and the original diagnostic hash; the machine-specific raw
diagnostic and failed source remain preserved locally.

The proof uses primary Mathlib facts from the pinned revision:
[PMF Basic](https://github.com/leanprover-community/mathlib4/blob/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Probability/ProbabilityMassFunction/Basic.lean)
for mass and measure properties,
[PMF Integrals](https://github.com/leanprover-community/mathlib4/blob/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Probability/ProbabilityMassFunction/Integrals.lean)
for `PMF.integral_eq_sum`, and
[Log Basic](https://github.com/leanprover-community/mathlib4/blob/db584cd6d46c92f209a44c0f1c829460d327499d/Mathlib/Analysis/SpecialFunctions/Log/Basic.lean)
for logarithm identities, the zero convention and `Real.one_sub_inv_le_log_of_pos`.
The complete finite-law derivation and examples belong to the linked sensor report.

## Open targets and use boundaries

These thirteen definitions in `FiniteSensorBayes.Raw` remain unproved by this package:

```text
ObservationSemanticsTarget       PosteriorSemanticsTarget
NullFallbackRiskTarget           AdmissibilityOnStatesTarget
ExpectedLossSumTarget            PredictiveKLTarget
LogScoreDecompositionTarget      BayesAttainmentMinimalityTarget
NoObservationRiskTarget          InformationDomainsTarget
MutualInformationGainTarget      ConditionalInformationGainTarget
LearnedLossGapTarget
```

In particular, the open `LogScoreDecompositionTarget` is conditional on observations and differs
from the accepted, unconditional `FiniteLogScoreTarget`. The sensor report's conditional Bayes
and availability arguments remain handwritten. No signed PID allocation, sensor-ranking rule,
sampling guarantee, estimator calibration, learned predictor improvement, or authentication
result follows from these four foundations. The source snapshots can be inspected publicly;
portable automated replay and hosted coverage require a separate admitted integration.

## Rust implementation and computational cost

This package adds no Rust API, executable log-score evaluator, benchmark, or floating-point
refinement theorem. Proof compilation and kernel replay are verification work, not sensor-model
inference or training. The report discusses prospective finite-vector evaluation costs; no new
runtime measurement is supplied here.

## Citation

Sepehr Mahmoudian. *Finite-PMF logarithmic score: formal source and local evidence*. pid-rs,
2026. Cite this record with its exact repository commit or release, and cite Gneiting–Raftery and
Mathlib separately for the classical method and library foundations. Authorship records
responsibility and does not establish scientific priority or independent review.
