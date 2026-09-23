# Finite conditional Bayes risk and information gain

Author: **Sepehr Mahmoudian**. pid-rs formal exposition, 2026. Cite the exact repository commit or release, and cite the classical scoring-rule and library sources separately. These are classical finite-probability identities formalized for this package, not a new PID functional or a scientific-priority claim.

The practical question is precise: how much lower can *unrestricted expected logarithmic prediction loss* become when a predictor receives an observation, and why can a supplied predictor still fail to realize that benefit? Thirteen exact targets have local Lean compilation, target/axiom/module inspection, and an identical-source fresh kernel replay in the selected development and final stages. The [conditional receipt](REPRODUCTION.json) records the observed source, toolchain, calls and limits. The earlier [four-foundation receipt](../REPRODUCTION.json) is a distinct historical execution. Portable automated replay and hosted verification remain open. Proof checking confirms the encoded statements under their imports and listed axioms; it does not establish that a physical sensor matches an encoded map.

## One finite law and its positive fibers

Let $K$, $Y$ and $O$ be finite nonempty alphabets. Let $p$ be a normalized native PMF on $K$, $T:K\to Y$ a target map and $A:K\to O$ an observation map. A state $k$ can encode all finite sensor randomness, so deterministic coordinate maps do not assume a noise-free device. The same exact $p$ and $T$ govern every comparison below. No independent sample, fitted model, Gaussian law or intervention is assumed. All logarithms are natural and quantities are in nats.

Write the joint and marginal masses as

$$
j(o,y)=\sum_{k:A(k)=o,\,T(k)=y}p(k),\qquad
p_O(o)=\sum_y j(o,y),\qquad p_Y(y)=\sum_o j(o,y).
$$

The formal `jointLaw`, `observationLaw` and `targetLaw` are native PMF pushforwards. The `observationSemantics` target checks their actual discrete-measure pushforwards, event masses, finite sums, marginals and support witnesses. For $p_O(o)>0$, define $r_o(y)=j(o,y)/p_O(o)$. The nonnegative $j(o,y)$ sum to $p_O(o)$, so $\sum_y r_o(y)=1$ and $r_o(y)>0$ exactly when $j(o,y)>0$. The `posteriorSemantics` target identifies this normalized PMF with Mathlib's filtered-and-mapped PMF and the target pushforward of the conditional measure on that **positive** observation fiber.

If $p_O(o)=0$, every $j(o,y)$ is zero by nonnegativity. The canonical posterior uses $p_Y$ as a normalized fallback there; `posteriorWithFallback` also permits any other normalized fallback. `nullFallbackRisk` proves that all such choices agree on supported states and have the same expected risk. The conditional measure itself is zero on a null fiber, so equality to a fallback PMF is asserted only on positive fibers. A zero count in a finite recording does not prove a population-null fiber.

A forecast $q:O\to\mathrm{PMF}(Y)$ is **admissible** when $q_o(y)>0$ for every $j(o,y)>0$. A positive joint cell has a supported state witness, and every supported state contributes to a positive joint cell. Thus `admissibilityOnStates` makes this equivalent to $q_{A(k)}(T(k))>0$ at each $k\in\mathrm{supp}(p)$. The posterior is admissible because its positive-fiber support is exactly the positive joint support. Forecast mass outside true support is allowed. Lean's real logarithm is total with $\log 0=0$; these results do not interpret zero forecast mass on a possible outcome as finite ordinary loss or prove an extended-real infinite-loss theorem.

## Conditional score and Bayes optimum

For an admissible forecast, `expectedLogLoss` is the actual `PMF.toMeasure` integral of $-\ln q_{A(k)}(T(k))$. Finite discrete integration gives the supported state sum. Grouping states by $(A(k),T(k))$ gives the joint-law sum:

$$
L_A(q)=\sum_{k\in\mathrm{supp}(p)}p(k)[-\ln q_{A(k)}(T(k))]
=\sum_{o,y:j(o,y)>0}j(o,y)[-\ln q_o(y)].
$$

`expectedLossSum` checks both equalities and integrability. A null fiber contributes no term because all its joint masses vanish. On each positive fiber, $j(o,y)=p_O(o)r_o(y)$, so the last expression is $\sum_{o:p_O(o)>0}p_O(o)\sum_{y:r_o(y)>0}r_o(y)[-\ln q_o(y)]$. For every included $y$, both $r_o(y)$ and $q_o(y)$ are positive. The elementary logarithm identity

$$
-\ln q_o(y)=-\ln r_o(y)+\ln\frac{r_o(y)}{q_o(y)}
$$

therefore separates entropy from excess loss. Define

$$
H(Y\mid A)=\sum_{o:p_O(o)>0}p_O(o)H(r_o),\qquad
D_A(q)=\sum_{o:p_O(o)>0}p_O(o)\mathrm{KL}(r_o\Vert q_o).
$$

The supported Gibbs inequality applies to each normalized positive-fiber posterior and its admitted forecast; hence $\mathrm{KL}(r_o\Vert q_o)\geq0$. Weighting by $p_O(o)>0$ and summing gives $D_A(q)\geq0$. At the posterior, each included KL is zero. No Gibbs premise is invoked for a null-fiber fallback. The `predictiveKL`, `logScoreDecomposition` and `bayesAttainmentMinimality` targets prove

$$
\boxed{L_A(q)=H(Y\mid A)+D_A(q)\geq H(Y\mid A),\qquad L_A(r)=H(Y\mid A).}
$$

This minimum ranges over all admissible PMF forecast rows. The targets do not assert unique minimization, representation by a selected model class or attainment by training. With the constant `Unit` observation, `noObservationRisk` makes Bayes risk equal to $H(Y)$.

## Information is defined independently of risk

Mutual information is the supported joint/marginal-ratio sum

$$
I(Y;A)=\sum_{o,y:j(o,y)>0}j(o,y)
\ln\frac{j(o,y)}{p_O(o)p_Y(y)}.
$$

The `informationDomains` target checks that every numerator and denominator in this and the conditional information sum below is positive on its selected support. On a positive joint cell, $j(o,y)=p_O(o)r_o(y)$ changes the log ratio to $\ln[r_o(y)/p_Y(y)]$. Expand that ratio as $\ln r_o(y)-\ln p_Y(y)$ and use the marginal identity $\sum_o p_O(o)r_o(y)=p_Y(y)$. The two terms become $-H(Y\mid A)$ and $H(Y)$. Thus `mutualInformationGain` proves that the independently defined $I(Y;A)$ equals $H(Y)-H(Y\mid A)$ and the no-observation minus observed Bayes-risk difference. It is nonnegative also because it is the weighted posterior KL against the admissible constant forecast $p_Y$.

Now let $V$ be another finite nonempty alphabet and $B:K\to V$ an additional observation. Write $t(o,v,y)$ for the joint PMF of $(A,B,T)$ and $p_{OV}(o,v)$ for the paired-observation marginal. The `Contract.lean` definition of conditional information is the independent triple-ratio sum

$$
I(Y;B\mid A)=\sum_{o,v,y:t(o,v,y)>0}t(o,v,y)
\ln\frac{t(o,v,y)p_O(o)}{p_{OV}(o,v)j(o,y)}.
$$

For $p_{OV}(o,v)>0$, put $r_{ov}(y)=t(o,v,y)/p_{OV}(o,v)$. A positive $t(o,v,y)$ projects to positive $j(o,y)$, so $r_o(y)>0$ wherever $r_{ov}(y)>0$. The supported ratio simplifies to $r_{ov}(y)/r_o(y)$. Regrouping by positive paired fibers gives

$$
I(Y;B\mid A)=\sum_{o,v:p_{OV}(o,v)>0}p_{OV}(o,v)
\mathrm{KL}(r_{ov}\Vert r_o)\geq0.
$$

This nonnegativity is the supported Gibbs inequality averaged over positive paired fibers; null paired fibers vanish. Expand the KL logarithm and use $\sum_v p_{OV}(o,v)r_{ov}(y)=p_O(o)r_o(y)$ to obtain $H(Y\mid A)-H(Y\mid A,B)$. Applying the MI entropy expansion to $A$ and $(A,B)$ gives the chain difference. `conditionalInformationGain` proves the complete identity

$$
R(A)-R(A,B)=I(Y;B\mid A)=H(Y\mid A)-H(Y\mid A,B)
=I(Y;A,B)-I(Y;A)\geq0,
$$

where $R$ is unrestricted posterior Bayes risk under the same $p,T$. This nonnegative gain concerns the **paired observation** $(A,B)$, which retains $A$. It is not a theorem about replacing $A$ with an unrelated observation. The [sensor report](../../../research/embodied-sensor-utility/EXPOSITION.md) then applies these classical identities to availability and categorical MGW atoms; those mask and PID correspondences remain handwritten.

## Supplied predictors can lose information's benefit

For two admissible forecasts $q_0,q_1$ on maps $A_0,A_1$ under the same $p,T$, `learnedLossGap` proves the **expected-loss difference**

$$
L_{A_0}(q_0)-L_{A_1}(q_1)
=[R(A_0)-R(A_1)]+D_{A_0}(q_0)-D_{A_1}(q_1).
$$

No nesting of $A_0,A_1$, learning algorithm or sign of this difference is assumed. If $A_1=(A_0,B)$, the Bayes-risk bracket is the conditional information above. Otherwise that identification needs another premise. Predictive KL is excess expected log loss relative to an unrestricted posterior; it can include approximation, estimation and optimization error, not only calibration.

A small analytic control makes the boundary concrete. Let $Y$ be one fair bit. Give the baseline a constant observation and forecast $(1/2,1/2)$, so its loss and Bayes risk are $\ln2$. Let the second observation reveal $Y$, but let its supplied forecast assign probability $1/4$ to the true bit at each observation. The second Bayes risk is zero, while its expected loss and excess KL are $\ln4$. The expected-loss gain is $\ln2-\ln4=-\ln2$ even though Bayes information gain is $\ln2$. This is neither a measured sensor result nor a deployed predictor claim.

## Exact formal scope and evidence

The [frozen targets](../sources/FiniteSensorBayes/RawTargets.lean) and [conditional proof source](sources/FiniteSensorBayes/ConditionalCandidate.lean) expose the following thirteen checked exports. Arity lists the universe parameters of the exact target and theorem, not a count of data dimensions. The final owner observation reported exactly `Classical.choice`, `Quot.sound` and `propext` for **each** export. The whole candidate module has 50 theorem declarations, including 37 private helpers, checked against the same allowed axiom set.

| Export in `FiniteSensorBayesConditionalCandidate` | Frozen `FiniteSensorBayes.Raw` target | Universes | Role |
|---|---|---|---|
| `observationSemantics` | `ObservationSemanticsTarget` | `u,v,w` | Joint, marginal, measure and support semantics |
| `posteriorSemantics` | `PosteriorSemanticsTarget` | `u,v,w` | Positive-fiber posterior and conditional measure |
| `nullFallbackRisk` | `NullFallbackRiskTarget` | `u,v,w` | Risk independence of null-fiber fallback |
| `admissibilityOnStates` | `AdmissibilityOnStatesTarget` | `u,v,w` | Joint-cell/state support equivalence |
| `expectedLossSum` | `ExpectedLossSumTarget` | `u,v,w` | Integral, state sum and joint sum |
| `predictiveKL` | `PredictiveKLTarget` | `u,v,w` | Excess-loss nonnegativity and self-zero |
| `logScoreDecomposition` | `LogScoreDecompositionTarget` | `u,v,w` | Conditional score decomposition |
| `bayesAttainmentMinimality` | `BayesAttainmentMinimalityTarget` | `u,v,w` | Posterior attainment and minimality |
| `noObservationRisk` | `NoObservationRiskTarget` | `u,v` | Constant-observation entropy baseline |
| `informationDomains` | `InformationDomainsTarget` | `u,v,w,x` | Supported MI/CMI ratio positivity |
| `mutualInformationGain` | `MutualInformationGainTarget` | `u,v,w` | Independent MI equals Bayes gain |
| `conditionalInformationGain` | `ConditionalInformationGainTarget` | `u,v,w,x` | Paired-observation CMI and chain identities |
| `learnedLossGap` | `LearnedLossGapTarget` | `u,v,w,x` | Same-law supplied-forecast loss difference |

The [conditional publication page](PUBLICATION.md) and [receipt](REPRODUCTION.json) identify the exact shared and new source bytes, two raw owner observations, local exits, module inventory and kernel replay. Source comments saying “candidate” or “uncompiled” record their preparation state and remain unchanged so the published source matches the compiled bytes. The two stdout files are observations, not standalone acceptance; the root-adopted local result also depends on retained outer execution and custody records.

The result contains no availability-mask independence theorem, MGW reconstruction or signed-atom bridge, PID estimator calibration, population inference from empirical counts, floating-point/Rust refinement or physical sensor benefit. A changed observation policy can change the law and leaves the fixed-law comparison. The defining [MGW paper](https://arxiv.org/abs/2002.03356v5) concerns a separate categorical shared-exclusions functional. The classical scoring connection follows [Gneiting and Raftery (2007)](https://doi.org/10.1198/016214506000001437); the [foundation publication](../PUBLICATION.md) links the pinned primary Mathlib PMF, integral and logarithm source.

## Rust implementation and computational cost

This formal package adds no Rust evaluator or public API. The current Rust categorical MGW API described in the [sensor report](../../../research/embodied-sensor-utility/EXPOSITION.md#13-rust-implementation-and-computational-cost) computes a different object. A **prospective dense-table algorithm** would enumerate $|K|$ weighted states to construct a joint $(O,Y)$ table, then scan its $|O||Y|$ cells for supported score, entropy and KL sums; it would store $O(|O||Y|)$ entries. Assuming unit-cost state-map evaluation and arithmetic, this gives $O(|K|+|O||Y|)$ operations. Building and scanning the paired $(O,V,Y)$ table would take $O(|K|+|O||V||Y|)$ operations and could store $O(|O||V||Y|)$ entries. This is arithmetic and storage planning for an unimplemented evaluator, not a released Rust complexity measurement, binary64 error bound or measured latency. Feature extraction, model inference/training, repeated masks and resampling add costs; cancellation, resource limits and failure behavior would need a separate implementation contract. No timing is reported.

**Citation:** Sepehr Mahmoudian. *Finite conditional Bayes risk and information gain*. pid-rs, 2026. Include the exact repository commit or release; use [software citation metadata](../../../../CITATION.cff) for pid-rs. Authorship records responsibility, not scientific priority or independent review.
