# Available information and fixed-predictor error in the occupancy recordings

This calculation explains a negative predictive result in the [retained office
sensor example](real-occupancy-sensors-example-2026-09-08.md). Adding CO₂ to light
reduces empirical conditional entropy on the later recording, but the fixed
two-sensor predictor has a larger conditional KL discrepancy. That increase
exceeds the information increment, so its log loss is worse.

This is a descriptive calculation on three finite empirical laws. It reconstructs
the original predictors from the original training counts. It fits no new model,
uses no new observations and supplies no population calibration, causal effect,
or new formally verified theorem. The logarithmic-score identity is classical;
the contribution here is its explicit numerical application to this retained
sensor result. Scientific priority for that application is not claimed.

## Scientific object and inputs

The source example computes the categorical shared-exclusions PID of Makkeh,
Gutknecht and Wibral, [arXiv:2002.03356v5](https://arxiv.org/html/2002.03356v5),
on the empirical PMF of each recording. The present calculation uses ordinary
conditional entropy, CMI and prediction loss on those same PMFs. It explains
their relation to the signed PID sum; it introduces no new redundancy definition
or estimator. It is not a calculation of the continuous Ehrlich functional.

The data are the [UCI Occupancy Detection dataset](https://doi.org/10.24432/C5X01N),
by Candanedo, licensed under CC BY 4.0. The retained example records the raw-data
provenance, units, time ordering, quantizer edges and original Rust execution.
Light is measured in lux and CO₂ in ppm. Their four-bin equal-width maps were
fitted on the 8,143 training rows. The target is the original binary occupancy
label, derived from photographs. A row represents a time-indexed measurement;
it is not an independent episode merely because it occupies a separate CSV row.

| Recording | Role in the original example | Rows |
|---|---|---:|
| `datatraining.txt` | Fit bin maps and both probability predictors | 8,143 |
| `datatest.txt` | Evaluate the frozen maps and predictors | 2,665 |
| `datatest2.txt` | Evaluate the frozen maps and predictors | 9,752 |

All three recordings have been inspected during development. None is an
untouched confirmation set for this later analysis. No IID assumption is needed
to calculate a functional of their specified empirical laws. An inference about
future recordings would need a separate sampling and model argument.

Let $H\in\{0,1,2,3\}$ be the light bin, $C\in\{0,1,2,3\}$ the CO₂ bin and
$Y\in\{0,1\}$ the occupancy label. Each recording has a nominal joint alphabet
of 32 cells. On the later recording, 16 cells are occupied, four have fewer than
five rows, and the smallest positive count is one. Empty empirical cells do not
establish population zeros. The calculator reads positive integer counts from
the [original descriptive JSON](real-occupancy-sensors-example-2026-09-08/descriptive-comparisons.json)
and checks the alphabet, unique keys and recording totals.

## Predictors and the exact-real identities

For either context $x=h$ or $x=(h,c)$, let $M(x,y)$ be its training count and
$M(x)=M(x,0)+M(x,1)$. The original add-one Bernoulli predictor is

$$
q(y\mid x)=\frac{M(x,y)+1}{M(x)+2}.
$$

The two predictions sum to one and are strictly positive. A context absent from
training predicts $1/2$ for each label. This is a specified smoothing rule; no
Gaussian prior or population model is required for the calculation. If read as
a Bayesian posterior mean, it would have its own Bernoulli/Beta model assumptions;
that interpretation is not used here.

For one evaluation recording, write $N(h,c,y)$ for the joint count and $n$ for
its positive total. Its empirical law is $p(h,c,y)=N(h,c,y)/n$. Marginal counts
define $p(y\mid h)$ and $p(y\mid h,c)$ wherever their contexts have positive
mass. Let $X_0=H$, $X_1=(H,C)$ and let $q_0,q_1$ denote the two fixed predictors.
All sums below omit zero empirical joint masses. Define, for $j\in\{0,1\}$,

$$
\begin{aligned}
L_j&=\sum_{h,c,y:p(h,c,y)>0}p(h,c,y)[-\log q_j(y\mid X_j)],\\
H_j&=\sum_{h,c,y:p(h,c,y)>0}p(h,c,y)[-\log p(y\mid X_j)],\\
D_j&=\sum_{h,c,y:p(h,c,y)>0}p(h,c,y)
\log\frac{p(y\mid X_j)}{q_j(y\mid X_j)}.
\end{aligned}
$$

Here $X_j$ inside a summand denotes its value at that key. Every logarithm has
a positive argument. Splitting $-\log q=-\log p+\log(p/q)$ and summing gives
$L_j=H_j+D_j$. Conditional KL discrepancy $D_j$ is nonnegative: at each
context, $-\log x\ge1-x$ implies

$$
\sum_{y:p_y>0}p_y\log\frac{p_y}{q_y}
\ge1-\sum_{y:p_y>0}q_y\ge0.
$$

The context weights are nonnegative, so averaging preserves the inequality.
The true conditional law attains equality. These are the logarithmic-score,
entropy and KL relations in Gneiting and Raftery,
[Example 3](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf).
An arbitrary predictor that assigns zero to an observed positive mass instead
has infinite loss; the finite subtraction used here would then require care.
The add-one predictors exclude that case.

Direct subtraction of the two conditional entropies gives

$$
\begin{aligned}
J&=H_0-H_1
=\sum_{h,c,y:p(h,c,y)>0}p(h,c,y)
\log\frac{p(y\mid h,c)}{p(y\mid h)}\\
&=I_p(C;Y\mid H).
\end{aligned}
$$

Consequently the attained log-loss gain is

$$
G=L_0-L_1=J+D_0-D_1.
$$

With the same law, source grouping and target, the two-source PID reconstruction
also gives $J=U_C+S$. Thus the signed allocation, available information and
attained prediction gain are three related quantities with different meanings.
The [analysis and decision note](../../PID_ALTERNATIVES_AND_INCREMENTAL_VALUE.md)
derives the PID identities and explains the corresponding learning and acquisition
decisions. Their CMI/log-loss connection is established acquisition work, including
[Covert et al., 2023](https://proceedings.mlr.press/v202/covert23a.html).

## Results

All values are nats per row, rounded to nine decimal places here. The retained
[calculation output](occupancy-fixed-predictor-loss-decomposition-2026-09-10/results.json)
contains the complete binary64 values and residuals.

| Recording | $H_0$ | $H_1$ | $D_0$ | $D_1$ | $G$ |
|---|---:|---:|---:|---:|---:|
| Training | 0.052756253 | 0.047804384 | 0.000126287 | 0.000441196 | 0.004636960 |
| Earlier evaluation | 0.087028128 | 0.078318289 | 0.010744807 | 0.011425755 | 0.008028892 |
| Later evaluation | 0.033083487 | 0.031525474 | 0.014359564 | 0.019236545 | −0.003318968 |

The later empirical CMI is $J\approx0.001558012$ nats. The extra discrepancy is
$D_1-D_0\approx0.004876981$ nats, which is larger. Therefore

$$
G\approx0.001558012-0.004876981=-0.003318968\text{ nats}.
$$

This explains the retained loss increase from about $0.047443051$ to
$0.050762019$ nats per row. It is compatible with the original MGW cancellation
$U_C+S\approx-0.178691053+0.180249065=0.001558012$ nats.
The augmented predictor also had a worse Brier score despite correcting four
additional classifications. The result illustrates why accuracy, probability
quality, added information and a signed synergy coordinate should be reported
separately.

Both evaluation recordings have positive gain available in their empirical laws;
only the earlier one has a positive attained gain for these particular fixed
predictors. This calculation does not identify why their errors differ. Model
restrictions, finite training data and changes across recordings are possible
explanations to test, rather than established causes.

## Numerical evidence and reproduction

The [calculator source](occupancy-fixed-predictor-loss-decomposition-2026-09-10/calculate.py)
is publication tooling. It imports no pid-rs implementation. It shares the
original counts, predictor specification, logarithmic identities and standard
library arithmetic with this analysis; it is not independent data or a second
population study. The core library remains Rust.

Run from the repository root with Python 3.14.6, the observed interpreter version:

```text
python3 -I -S -B audit/evidence/occupancy-fixed-predictor-loss-decomposition-2026-09-10/calculate.py audit/evidence/real-occupancy-sensors-example-2026-09-08/descriptive-comparisons.json
```

The source fixes the input digest, recording roster and comparison tolerance.
Count and conditional-probability ratios use `Fraction` until logarithms.
Log ratios use `math.log(numerator) - math.log(denominator)`; weighted sums use
`math.fsum`. Subsequent arithmetic is binary64, not rational or interval proof.
The gain is also calculated directly as an average of $\log(q_1/q_0)$, and CMI
directly from the joint and marginal count ratio. These paths are compared with
the entropy/KL identities and the historical values where present.

The single recorded run exited successfully in about 0.036 seconds with empty
stderr. Source and input bytes were unchanged across the call. All 19 finite
comparison residuals were within the preselected $10^{-12}$-nat fixture
tolerance; the largest absolute residual was $1.5269903397285844\times10^{-15}$
nats. The tolerance is not a proved binary64 error bound or a portability
guarantee. Timing is a single observation, not a benchmark.

Training contributes five comparisons. The original training record had no
historical predictive-loss values, so no historical loss comparison is claimed
there. Each evaluation recording contributes seven comparisons, including both
historical losses. The smallest predicted probability on the supported keys is
$12/6337$ for the baseline and $5/6116$ for the augmented model, in all three
recordings. These observed minima are not a declared probability floor for
arbitrary future contexts.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Original descriptive JSON | 59,023 | `15798710c848225b45276134fa26ae5c04f9ffb0535f2bea23e33a4e19cd3487` |
| Calculator | 6,398 | `8f74a60363f5141d9476ec66d216951895d8ffa39463941ac85d2f2424bc838a` |
| Recorded output | 4,535 | `1bdea76f69523f1c9738e1837d6aab7772cc8f445c5ba30d87c5a32e2c65a417` |

One draft source tried to read absent historical training scores. Review rejected
it before execution. The [inert rejected source and disposition](occupancy-fixed-predictor-loss-decomposition-2026-09-10/rejected-source.md)
preserve that path; the successful source makes absence explicit. No failed
native run is claimed for the rejected draft.

## Implications and next actions

For analysis, show the signed unique and synergy terms together with their CMI
sum. For prediction, compare frozen model loss under the same evaluation law.
The KL decomposition identifies the size of a model discrepancy; it does not
turn empirical conditional probabilities into known future probabilities.

For learning, keep task loss primary and compare any proposed PID feature or
regularizer with task-only and CMI-assisted controls under matched data and
tuning budgets. The current result supports no PID-guided learner advantage.
For a fixed set of two to four available sensor packages, compare affordable
subsets and the no-acquisition option before introducing an adaptive policy.
Use the chosen task loss and measured cost. This example measured no cost.

The next descriptive office study can compare the existing light baseline with
CO₂, temperature and humidity subsets, preserving training-only maps and all
outcomes. It must label these known recordings as development evidence. A claim
about future deployment needs new independent episodes or an explicitly justified
dependence model and selection-aware evaluation. A sequential study must specify
which readings and labels are available at each decision. These published
aggregate values can serve as frozen historical summaries. A current pointwise
PID contribution requires the realized target and candidate reading. Recomputing
an empirical KL diagnostic for a new recording requires its labelled joint data.
A prospective gate must use available history and fixed prior summaries, or an
explicit model-based expectation over unavailable values.
