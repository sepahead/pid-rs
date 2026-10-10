# Useful shared-exclusions notes and retained failures

Sepehr Mahmoudian · 10 October 2026.

These notes bring useful explanations out of older drafts. They are a current
source companion, not a new formal result, estimator or application benchmark.
The older PDFs remain unchanged and unqualified. A qualified PDF of these
notes is still open. Negative results belong beside the conclusions they limit.

## What is current, and what stays historical?

| Older material | Current useful content | Evidence boundary |
|---|---|---|
| Application screen | Common-law comparisons, explicit encoding and sampling, and simpler mutual-information/task-loss alternatives | Application recommendations need current data, access, consumer and held-out checks |
| Minimal-family draft | Removing absorbed branches preserves their logical union; see the example below | Historical generic checks do not establish current tool qualification, probabilities or Rust refinement |
| Application-requirements draft | A duplicate can add no ideal information yet harm a restricted classifier; see the exact example below | A constructed law is not a neural, flight or robotic result |
| Source-redundancy draft | A five-position categorical entropy budget and its zero-conditional-information counterexample; see below | Hand derivation with a published component-positivity premise, not a new kernel check |
| Stock-verifier draft | Source-found, loaded and executed identities differ; wrong requested targets and stale receipts must be refused | Old matching hashes and zero exits do not lift the current formal-promotion hold |

The [process report](../RESEARCH_PROCESS_EVIDENCE_2026_10_10.md) and
[reader contract](../RESEARCH_READER_AND_VERIFICATION_CONTRACT.md) separate these evidence types.
The [angular supplement](pdf/angular-relative-bound-20261005/relative-error.pdf) uses the **continuous Ehrlich** functional;
the examples below use **categorical Makkeh–Gutknecht–Wibral (MGW)** shared
exclusions. These are different objects. None is Williams–Beer `I_min`.

Existing active bounds need no rediscovery: see
[fixed-alphabet support-change continuity](../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md),
[the complete-row IID prefix-bias derivation](../audit/formal/lean-prefix-mgw-bias/EXPOSITION.md)
and [dependency-colouring assumptions](../DEPENDENCY_COLORED_SXPID_CONCENTRATION.md).
An observed law distance, minimum frequency or time spacing does not by
itself supply their population or independence premises.

## Vocabulary and assumptions

A finite law assigns nonnegative probabilities summing to one to complete
source-and-target states. An empirical law assigns observed relative
frequencies; it need not equal a population law. A supported state has strictly
positive probability. Natural logarithms give information and log loss in
**nats**. Probabilities and decoder-error rates are dimensionless.
MGW's paper uses base-two logarithms and bits; multiplying its values by
`ln(2)` converts them to the natural-log quantities used here.

An antichain is a nonempty family of nonempty source-index sets, none contained
in another. `13` denotes the set containing indices 1 and 3; a semicolon
separates members of the family. A downset consists of a node and every node
below it in the declared order. An atom is an increment in the finite lattice
reconstruction, not an independently usable sensor reward.

Conditional entropy measures the remaining average uncertainty about a
variable after given variables are known. Conditional mutual information
(CMI) measures their additional average target information under one common
law. It does not equal a difference of arbitrary fitted predictors' losses.
Log loss is minus the logarithm of the probability assigned to the outcome
that actually occurred. Zero predicted probability on positive true support
gives infinite loss, not zero.

These meanings use the [MGW v5 definition, Equations (6), (15) and Theorem IV.3](https://arxiv.org/html/2002.03356v5)
and ordinary finite Shannon information; the
[MIT finite entropy and Fano notes](https://ocw.mit.edu/courses/6-441-information-theory-spring-2010/5c0b5a8a544cb2320778e4c9e5dea64f_MIT6_441S10_lec02.pdf)
give the classical entropy arguments, not a PID theorem.
Assigned finite-law calculations need no row-independence premise. Population
confidence, fitted decoder guarantees and deployment value need separate
sampling, selection and task assumptions. No such guarantees are added here.

## Repeated inputs: which categorical positions can change?

Fix three finite source variables `S1`, `S2`, `S3`, a finite target `T`, and
one normalized joint law `P`. Every expectation below uses that same law.
For a supported state `z = (s1,s2,s3,t)`, a source-set match requires agreement
on every index in that set. A family's event `W_alpha(z)` is the union of its
set matches: AND within each member, OR between members.

Define informative and misinformative cumulative values, both in nats, by

$$
r^+_\alpha(z)=-\ln P(W_\alpha(z)),\qquad
r^-_\alpha(z)=-\ln P(W_\alpha(z)\mid T=t).
$$

The anchor lies in every required event, so both logarithm arguments are
positive. Order families by `alpha <= beta` when every member of `beta`
contains a member of `alpha`. Define the component atoms `pi_beta^+` and
`pi_beta^-` by the finite reconstruction

$$
r^\sigma_\alpha(z)=\sum_{\beta\le\alpha}\pi^\sigma_\beta(z),
\qquad \sigma\in\{+,-\}.
$$

This equation defines which component increment is meant. We use MGW's
Theorem IV.3 for exact-real component nonnegativity. It is a cited premise,
not a result established by our scalar solver or floating-point code.
The **net** atom is the difference of the two components and may be negative.

A node is below the pair node `{12}` exactly when some member is contained
in `12`. Outside this downset, every member contains index 3. The available
sets are `3`, `13`, `23`, `123`; only `13` and `23` are incomparable. Thus the
outside positions are exactly

$$
K=\{\{3\},\{13\},\{23\},\{13;23\},\{123\}\}.
$$

Subtract the pair reconstruction from the top reconstruction. All downset
terms cancel, leaving the sum over `K`. At the top the source event fixes all
three sources; at the pair it fixes the first two. Their mass ratio is
`P(s3 | s1,s2)`. The target-conditioned ratio is `P(s3 | s1,s2,t)`. Hence

$$
\sum_{\beta\in K}\pi^+_\beta(z)=-\ln P(s_3\mid s_1,s_2),\qquad
\sum_{\beta\in K}\pi^-_\beta(z)=-\ln P(s_3\mid s_1,s_2,t).
$$

Let `c_beta^+` and `c_beta^-` be these component atoms averaged with the
joint weights: `c_beta^sigma = sum_z P(z) pi_beta^sigma(z)`, with the sum
over supported states and `sigma` either `+` or `-`.
Define `H3 = H(S3 | S1,S2)`,
`H3T = H(S3 | S1,S2,T)`, and `G = I(S3;T | S1,S2) = H3-H3T`.
All three are in nats and `0 <= H3T <= H3`. Averaging the displayed finite
sums gives `sum_K c_beta^+ = H3` and `sum_K c_beta^- = H3T`.

Define `n_beta = c_beta^+ - c_beta^-` and the absolute mass of the averaged
net atoms `M = sum_K |n_beta|`, also in nats. Component nonnegativity gives
`|c_beta^+-c_beta^-| <= c_beta^++c_beta^-`. Sum this inequality to obtain

$$
G\le M\le H3+H3T=2H3-G.
$$

The lower inequality is `|sum_K n_beta| <= sum_K |n_beta|` and `G >= 0`.
The signed sum is `G`; it is not `M`. For any subset of these five positions,
its summed net value lies between `-H3T` and `H3`: the informative sum
cannot exceed `H3` and the misinformative sum cannot exceed `H3T`.
The mean absolute **local** mass, `sum_z P(z) sum_K |pi_beta^+(z)-pi_beta^-(z)|`,
has the same upper bound but is a different quantity from `M`. Absolute
values and averaging cannot generally be interchanged.
In particular each `|n_beta|<=H3`, since its interval is `[-H3T,H3]`
and `H3T<=H3`. Small conditional source entropy controls magnitude;
small added CMI alone does not.

If `S3 = f(S1,S2)` everywhere on positive support, both local conditional
probabilities are one. Each component sum is then zero. A finite sum of
nonnegative components is zero only when each component is zero. Thus all
five positions vanish locally and on average under that exact premise.
Empirical predictability does not establish population determinism.

### What the captured simulation table does and does not show

An older CREBAIN/NEST report projects five lagged rows from one closed-loop
capture. Sources are completed-window spike counts for three channels in
population `d00.positive`. The target is whether channel 01's next-step east
acceleration **proposal** is nonzero, not observed physical actuation.

| Row | S1 | S2 | S3 | T |
|---|---:|---:|---:|---:|
| 1 | 28 | 29 | 28 | 1 |
| 2 | 30 | 30 | 30 | 1 |
| 3 | 29 | 29 | 28 | 0 |
| 4 | 0 | 29 | 28 | 0 |
| 5 | 0 | 32 | 30 | 1 |

Giving each row mass `1/5` defines this empirical law. Here `f(29)=28`
and `f(30)=f(32)=30`, so `S3=f(S2)` on its observed support. The five
outside positions vanish exactly under the stated mathematical definition.
Nevertheless the inside position `{2;3}` has net value `ln(2)/5` nats:
its source-event counts are `(3,2,3,3,2)`, while its only lower node
`{1;2;3}` has counts `(3,2,3,4,3)`. Informative differences are
`(0,0,0,ln(4/3),ln(3/2))`; the target-intersection counts are equal,
so the misinformative differences vanish. Averaging yields
`[ln(4/3)+ln(3/2)]/5 = ln(2)/5`.

Source 3 appearing in a label therefore does not imply added predictive
information. The retained pair `(S1,S2)` has five distinct values in this
tiny table; `(S2,S3)` repeats `(29,28)` three times. Zero empirical
conditional uncertainty is not population determinism.
Windows have unequal 19.9/20 ms durations, so counts are not matched-width
rates. The target was retrospective. No new capture, independence,
biological result, physical flight, held-out forecast or actuation benefit
is claimed. The original capture is omitted; its recorded hash is
`6dd62e7d5758fe9cd1776fd899dbfe8b964fbcf94dcb879254f143ac42f4d923`.
This is re-exposition of the preserved table, not a new raw-data extraction.

### Why zero added CMI is not enough

Let `S1` and `S3` be independent fair bits, `S2` a constant, and `T=S1`.
The four supported source/target states each have probability `1/4`.
Here `H3=H3T=ln(2)` and `G=0`; source 3 adds no target information.

The singleton `{3}` has immediate lower cover `{3;12}`. For any anchor,
the latter's union event has probability `3/4`; conditional on its target
it has probability one. Its net cumulative value is `ln(4/3)`. The source-3
singleton's net cumulative value is zero. Subtracting the lower cumulative
from the singleton cumulative gives

$$
n_{\{3\}}=-\ln(4/3)\ne0.
$$

The other outside atoms cancel it in their signed sum. Therefore `G=0`
does not force the individual net atoms to vanish. This is an exact
constructed counterexample, not a measured recording or estimator result.

An example reconstructed in a separate advisory context before draft/archive
exposure varies all three sources: take them
as independent fair bits and again set `T=S1`. Each of the eight source
triples has mass `1/8`, with its target fixed by source 1. The five net
atoms are now **all** nonzero, despite `G=0` and `H3=H3T=ln(2)`.
Each table entry is the natural logarithm of the displayed positive ratio.

| Position | Informative ratio | Misinformative ratio | Net ratio |
|---|---:|---:|---:|
| `{3}` | `5/4` | `3/2` | `5/6` |
| `{13;23}` | `16/15` | `1` | `16/15` |
| `{13}` | `9/8` | `1` | `9/8` |
| `{23}` | `9/8` | `4/3` | `27/32` |
| `{123}` | `32/27` | `1` | `32/27` |

For the anchor `(0,0,0,0)`, the event for `{3;12}` has source mass
`5/8`, target-intersection mass `3/8` and target mass `1/2`. Its net
cumulative is `ln(6/5)`; the `{3}` cumulative is zero, giving `ln(5/6)`.
The other net cumulatives needed for the cover calculation are:
`{12}`, `{13}`, `{123}`, `{12;13}` each give `ln(2)`;
`{3}` and `{23}` give zero; `{13;23}` and `{12;23}` give `ln(4/3)`;
`{12;13;23}` gives `ln(3/2)`. For two covers subtract their cumulatives
and add their meet cumulative. For three covers also subtract the triple
meet cumulative after adding all pair meets. This gives the remaining
four rows. The cover roster and meet convention are derived below.

Multiplying the informative ratios gives 2; the misinformative ratios
also give 2; the net ratios give 1. Taking logarithms recovers both
component budgets and the zero net sum. Bit relabelling preserves every
event mass, so the table is both local at each supported tuple and averaged.
A preserved exact-rational fixture calculation agrees with these entries.
It is one retrospective fixture, not a universal proof or Rust invocation.
The contexts share defining sources and prior project exposure; this is
not independent human confirmation or a claim of training-data absence.

### Near repeats require a valid decoder bound

Suppose source 3 has `m >= 2` declared labels. Fix a decoder `f(S1,S2)`
into that alphabet and let `epsilon = P[S3 != f(S1,S2)]`, in `[0,1]`.
Let `E` equal one on decoder error and zero otherwise. This indicator is
determined by the three sources. Apply the entropy
chain rule with that indicator: the error contributes at most its binary
entropy; given no error, source 3 is fixed; given an error, at most `m-1`
labels remain. Let `h` be binary entropy on `[0,1]`, in nats, with
`0 ln(0)=0`. Thus the classical Fano argument gives

$$
H3\le h(\epsilon)+\epsilon\ln(m-1),\qquad
h(x)=-x\ln x-(1-x)\ln(1-x),
$$

with `0 ln(0)=0`. Combining this with `H3T <= H3` bounds `M` by twice the
right side. If only `epsilon <= rho` is known, `rho` in `[0,1]`, maximize
that expression over `[0,rho]`: use `x=min(rho,1-1/m)`, not always `rho`.
Its derivative is `ln((1-x)(m-1)/x)`, which changes sign at `1-1/m`.
For `m=1`, the source is constant and the five components vanish.
A fitted decoder's observed error needs separate sampling and selection
evidence before this becomes a population bound.

Two limits must remain visible. Define the local net atom
`pi_beta(z)=pi_beta^+(z)-pi_beta^-(z)`, distinct from its averaged `n_beta`.
First, small mean entropy does not bound
every local atom. Set `S1=S2=0`, let `S3` equal 1 with probability
`epsilon` in `(0,1)`, and set `T=S3`. The rare tuple has outside atom
`pi_{ {3} }(z)=ln(1/epsilon)`, while `H3=h(epsilon)` tends to zero.

Second, a small decoder error alone is insufficient without alphabet
control. For an integer `j>=2`, keep the pair constant and `T=S3`, give
label 0 mass `1-1/j`, and give each of `2^j` other labels mass
`1/(j 2^j)`. The constant decoder's error is `1/j`, but
`H3=h(1/j)+ln(2)` tends to `ln(2)`, not zero. The outside singleton's
averaged net atom equals `H3`: every strictly lower event is certain
because it includes a constant-source branch. These are hand-derived
counterexamples, not executed studies or numerical certificates.

### The entropy ceiling can be approached, not always attained

This argument allows source alphabets to vary. Let `X` be uniform on `L`
labels, where `L` is a positive integer. Keep finite variables `U,V` and
their laws fixed as `L` grows; let them be independent of each other and
of `X`. Set `S1=X`, `S2` constant,
`S3=(U,V)` and `T=(X,U)`. Then `H3=H(U)+H(V)`, `H3T=H(V)`, `G=H(U)`.

For each supported pair `(u,v)`, let `p_uv=P(U=u,V=v)>0`. The `{3;12}`
union has mass `1/L+(1-1/L)p_uv`; its target-conditioned mass is one.
Let `r_L` be its averaged net cumulative. As `L` increases, each logarithm
converges to `-ln(p_uv)`. Summing finitely many weighted terms gives
`r_L -> H3`. The singleton's averaged cumulative is
`I((U,V);(X,U))=H(U)=G`: the target reveals `U`, while independent
`X` supplies no further information about `(U,V)`. The singleton-cover
identity therefore gives `n_{ {3} }=G-r_L`.

Let `Cminus` be the total magnitude of the negative net atoms in the five
positions. Since their signed sum is `G`, `M=G+2 Cminus`.
The single atom above gives `Cminus >= max(r_L-G,0)`. Thus the lower bound
on `M` approaches `2H3-G`, while the established upper bound is `2H3-G`.
This proves supremum sharpness over the permitted alphabet family, not
attainment for every fixed finite alphabet, a new formal theorem or priority.

## Duplicate inputs can harm a restricted predictor

This is another assigned law, not the four-state, two-fair-bit example above. Let the binary
target `T` be balanced. A binary observation `S` equals `T` with probability
`9/10` and disagrees with probability `1/10`, symmetrically. The four `(T,S)`
states `(0,0),(0,1),(1,0),(1,1)` have masses `9/20,1/20,1/20,9/20`.
Copies of `S` add no ideal information once `S` is known.

The [naive-Bayes definition](https://scikit-learn.org/stable/modules/naive_bayes.html)
uses a product of class-conditional feature probabilities. Our assigned
counterexample below is a derivation, not a result reported by that source.
Define a naive-Bayes rule that uses the true single-input class-conditional
probabilities but multiplies them for `k` identical copies, where
`k` is 1, 2 or 3. This factorization wrongly assumes conditional independence.
Given an observed `S=s`, its odds for `T=s` against `T!=s` become
`c=9^k`, rather than the correct odds 9. Its probability of agreement is
`c/(1+c)`. Its probability of disagreement is `1/(1+c)`.

Agreement therefore has loss `ln(1+1/c)`, and disagreement has loss
`ln(1+c)`. Average with the true agreement/disagreement weights:

$$
F(c)=\tfrac9{10}\ln(1+1/c)+\tfrac1{10}\ln(1+c)
=\ln(1+c)-\tfrac9{10}\ln c.
$$

Differentiate the final expression:

$$
F'(c)=\frac1{1+c}-\frac9{10c}
=\frac{c-9}{10c(1+c)}.
$$

It is strictly positive for `c>9`. Thus duplicate-copy odds 81 and 729
strictly increase expected loss above the one-input rule. On the rare wrong
outcome, losses rise from `ln(10)` to `ln(82)` to `ln(730)`.
Both the rare-outcome failure and the overall expected-loss failure matter.

The one-input rule is already the true posterior. A histogram rule using
the true joint law would not change that posterior when a copy is added.
An empirically fitted histogram has its own data and smoothing errors.
The historical draft also gives a possible training table: eight correct
observations per class, balanced fitted priors, four declared source labels
and one added count per label. Each denominator is `8+4=12`; observed-label
likelihoods `9/12` versus `1/12` again give odds 9 per copy. This is a
specified possible table, not the population law or an observed experiment.
PID does not repair the faulty factorization automatically. Direct log loss,
CMI, duplicate detection and grouped-model comparisons are simpler checks.
This example is a mechanism check, not evidence of SOTA or deployment gain.

### A negative control: duplication need not harm a fitted rule

Change the assigned law explicitly: now `P(S=T)=3/4`, with balanced
binary `T` and masses `3/8,1/8,1/8,3/8` on the four `(T,S)` states.
For a fixed possible training table, each class has three correct and
one wrong observation. Add one count to each of two declared labels;
the denominator is `4+2=6`. The single-input rule assigns confidence
`a=2/3` to `T=S`; duplicate naive-Bayes odds are `2^2=4`, giving
confidence `b=4/5`. Neither is the true confidence `3/4`.

Let `L_a` and `L_b` be their expected log losses under this **new** law.
Substitute its true correctness/error weights:

$$
L_a=-\tfrac34\ln(2/3)-\tfrac14\ln(1/3)
=\ln3-\tfrac34\ln2,
\qquad
L_b=\ln5-\tfrac34\ln4.
$$

Therefore

$$
L_b-L_a=\ln(5/3)-\tfrac34\ln2
=\tfrac14\ln\!\left(\frac{5^4}{3^4 2^3}\right)
=\tfrac14\ln(625/648)<0.
$$

The strict sign follows from `625<648`. Duplication improves this
already underconfident fitted rule, not the true posterior, which still
has lower expected loss. Thus the oracle harm example is not a universal
claim about fitted models. No sampled or deployment result is supplied.

Review caught a draft's erroneous exact denominator `1296` in this
control; its decimal losses and qualitative sign had been right. The
frozen erroneous report, route record and JSON label remain preserved
with an appended erratum. Counts of routes or lenses did not catch the
expression-to-calculation mismatch and are not correctness evidence.

## Minimal families preserve an OR, not an intersection

For a finite family `F` of finite branches, let `Min(F)` retain exactly those members
with no proper-subset member in `F`. A branch match means AND over that
branch's source tests; a family match means OR over its branches. If a
state matches a branch `A` in `F`, choose a smallest-cardinality branch
`B` in `F` contained in `A`. Such a branch exists because `A` is eligible
and `F` is finite. A proper-subset member of `B` would be eligible with
smaller cardinality, so `B` belongs to `Min(F)`. Matching `A` implies
matching `B`. Conversely `Min(F)` is contained in `F`. Both families
therefore match exactly the same states. This is an elementary finite-set
derivation, not a newly executed formal check.

Let the first branch family contain `12` and `13`, and the second contain
`2`. Their union contains all three branches. A state matching `12` already
matches `2`; remove the absorbed `12` branch. The remaining family is
`{2;13}`. Its event is still the first family's event **or** the second's.
It is not generally either operand alone or their intersection; degenerate
source maps can make those events coincide.

Use the same source maps, anchor and target slice throughout. Inconsistent
anchors or target restrictions can invalidate the identity; consistently
replacing the common anchor preserves it. Empty branches and families have separate true/false meanings;
valid PID antichains exclude them. Set normalization alone supplies no
probability, entropy, atom, sensor-removal or task-performance result.

## A bounded hand check of component positivity

This checks the five needed positions independently of simply assuming
positivity. It does not replace MGW's general theorem or qualify a proof tool.
A lower cover of a node is an immediate predecessor in the declared order.
The eighteen-node order gives the following covers.

| Node | Lower covers |
|---|---|
| `{3}` | `{3;12}` |
| `{13;23}` | `{3}`, `{12;13;23}` |
| `{13}` | `{12;13}`, `{13;23}` |
| `{23}` | `{12;23}`, `{13;23}` |
| `{123}` | `{12}`, `{13}`, `{23}` |

The meet is the greatest common lower bound. It is `Min(alpha union beta)`:
every branch of either operand contains a retained minimal branch, so this
family is below both operands. Any family below both has a member contained
in each retained branch, because that branch came from an operand; the
contained member can differ between branches. Thus it
is below the minimal family, establishing the greatest property. Its event
is the union of the operand events, by the normalization proof above.
Every strict lower
node lies below at least one cover: in a finite order extend it upward
until no intermediate strict lower node remains. Intersections of cover
downsets are meet downsets. Inclusion–exclusion on these finite downsets
therefore computes a component atom from cover cumulative values.

For any one of the five nodes, distinct cover events intersect exactly
in the node event. Write `W_A` for the source-match event on index set `A`.
For example, the covers of `{13}` have events
`(W_12 OR W_13)` and `(W_13 OR W_23)`, whose intersection is `W_13`
because `W_12 AND W_23 = W_123` is contained in `W_13`.
For `{13;23}`, intersect `W_3`
with `W_12 OR W_13 OR W_23` to get `W_13 OR W_23`. At the top,
any two of `W_12,W_13,W_23` intersect in `W_123`. The `{23}` case
exchanges indices 1 and 2; `{3}` has only one cover.

Choose the probability measure `Q` as either `P` or `P(. | T=t)`.
Let `k` be the number of covers (1, 2 or 3), `rho` the positive mass
of the node event, and `d_i>=0` the mass of the part of cover `i` outside
that event, for `i=1,...,k`. These extra parts are disjoint by the
intersection fact. A union of selected covers has mass `rho+sum_i d_i`
over the selected indices. Put `f(x)=-ln(x)` for `x>0`. Finite
downset inclusion–exclusion gives the component atom below. Here `C`
selects cover indices and `|C|` is their number. The empty selection uses
the node event.

$$
\sum_{C\subseteq\{1,\ldots,k\}}(-1)^{|C|}
 f\!\left(\rho+\sum_{i\in C}d_i\right).
$$

For a nonnegative increment `d` and integration variable `u`, repeatedly
apply the fundamental theorem of calculus
to `f(x)-f(x+d)=-integral_0^d f'(x+u) du`. The displayed finite
difference becomes the integral below. Each `u_i` ranges from zero to
the extra mass `d_i`; `(k-1)!` is the factorial of `k-1`.

$$
(k-1)!\int_0^{d_1}\!\cdots\!\int_0^{d_k}
 (\rho+u_1+\cdots+u_k)^{-k}\,du_k\cdots du_1\ge0.
$$

Write `f^{(k)}` for the `k`th derivative. Differentiation gives
`(-1)^k f^{(k)}(x)=(k-1)!/x^k`, which fixes the
sign. Every denominator is positive since `rho>0`; a zero-length interval
gives zero. Apply the calculation separately to both choices of `Q`.
This proves the required sign as a hand derivation for these five nodes,
not from redundancy monotonicity alone. The lattice/event correspondence,
calculus and whole statement are not newly kernel-verified here.

## Rust implementation and computational cost

Existing default-build `stable::categorical` APIs compute empirical MGW PID
for two to four aligned source matrices and a target. These notes introduce
no new Rust API, exclusion-budget diagnostic, decoder certifier or learner.
The [source route](../crates/pid-core/src/sxpid.rs) and
[engineering reference](../RUST_IMPLEMENTATION_AND_COST.md) state current
resource and numerical boundaries.

For the duplicate law there are four occupied joint cells; scoring the fixed
three displayed copy rules requires a constant number of logarithms. This
is conceptual work, not a runtime measurement. General categorical event
scans can grow quadratically with occupied support; preprocessing, lattice
inversion, training and resampling add costs. Mean absolute local atoms
require different aggregation from absolute averaged atoms.

Exact-real component positivity and zero identities do not certify binary64
inversion or residuals. Never clamp signed atoms or declare a rounded small
value exact zero. Resource guards and cooperative cancellation are not peak
memory or hard deadline guarantees. No timing or online qualification is
reported. Qualified formal correspondence, numerical error and statistical
calibration remain open.

## Retain useful failures and reopen only their actual gaps

The old draft checks preserve three specific source-level negatives:

- A declaration inspector can compare types or values through native
  reduction **before** refusing forbidden dependencies. Refusal must
  precede that comparison; this is a trust-order risk in our inspector,
  not an observed false Lean proof.
- A negative harness can count an unrelated earlier error at the same
  stage as the intended failure. A later persistence error can also hide
  the first classification error and omit its custody record. Require
  causal failure codes and preserve the first failure; a stage alone is
  not enough. The stopped production route refused missing prerequisites.
- Ordinary Python equality joins can lose original-input type distinctions:
  `0 == False` and `1 == 1.0`, despite different types. See the
  [Python numeric semantics](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex).
  A strict final-output comparison cannot recover a distinction already
  lost in an input join. These were manual witnesses, not forged trials.

These observations have not become repairs or completed qualification of
those stopped prototypes. Current process guidance supplies requirements,
not evidence that the old implementations now satisfy them.

Keep missing-glyph, bad-layout and repeat-byte PDF failures unchanged.
Do not normalize logs or alter a proof kernel, tolerance or frozen judge to
obtain a pass. The older stock audit's source observations and later historical
compilation records are different dated evidence; neither provides complete
source-to-executed-tool correspondence. The [current formal-promotion hold](../SESSION_HANDOFF.md#formal-integrity-checkpoint-of-2-october-2026)
remains in force. Anonymous Lean examples must not be counted as persistent
fresh-replay theorem exports.

Current application routes include neural recording, brain imaging, flight,
vision/touch and VLA/world-model questions, but the old plans do not establish
current access, suitable labels, causal input availability or held-out benefit.
The recorded occupancy study already contains losing comparisons. A positive
atom is not an acquisition or control decision. Reconsider a route only after
its exact law, representation, sampling unit, baseline and task gain are tested.

### Useful application proposals retained, but not run

The following are successors to archived **plans**, not new results. The
external sources establish tasks and data context, not that MGW improves
them. All encoders, horizons, thresholds and evaluation choices still
need a new frozen protocol before any study starts.

| Problem and source | Proposed finite-law inputs and target | Evaluation and scope |
|---|---|---|
| [NLB motor recordings](https://neurallatents.github.io/datasets.html) | Three disjoint neuron groups; pre-outcome spike counts in declared millisecond windows, four training-fitted labels per group, binary reach-direction target | Separate MC_Maze and MC_RTT laws. Hold out complete sessions/trials as appropriate; compare frozen versus retrained channel-loss predictors and direct log loss. Audit timing, unit-index conversion and labels. No biological or clinical gain demonstrated |
| [EuRoC drone recordings](https://projects.asl.ethz.ch/datasets/euroc-mav/) | Left-camera, right-camera and IMU summaries from past windows; declare intensity, angular-rate and acceleration units; four training-fitted labels per source; future yaw-change class | Hold out complete flights and keep overlapping windows together. Fix horizon, angular threshold, law weighting, synchronization and camera failures. Direct motion-class loss first; odometry and flight safety require different endpoints |
| [Vision/touch slip study](https://arxiv.org/html/2302.13564v1) | Two sources, visual and tactile summaries; four labels each and binary slip/stable target | Start with PID2, not an invented third modality. Hold out objects and grasp episodes; compare single modalities and direct loss at fixed false-alarm budget. Detection and pre-onset warning need different input deadlines. No force-control benefit demonstrated |
| [ZAPBench calcium forecasting](https://arxiv.org/html/2503.02618v1) | Recent/distant activity summaries and a future regional summary, with fixed session/stimulus context; encoded calcium activity is not spikes or voltage | Test original trace error and measured cost, not only encoded binary loss. Audit normalization causality, purge shared windows and group stimulus repeats. A single animal cannot establish cross-animal performance |

Crebain/NCP pressure-RMS retention and Prisoma/FLUX/VLA/world-model routes
remain proposals in the preserved application screen and current
[ecosystem guide](../ECOSYSTEM_CAPABILITIES.md). Freeze their revision,
physical or simulated units, availability, context, consumer and task before
using these bounds. A connectome alone is not a functional joint law;
encoded simulator commands are not observed physical actions. Rights and
access still need their own check. Do not use the unknown evaluation target
to choose an input online, or count restored siblings as independent episodes.

SxPID3 Programs A–E, the original nineteen finite obligations, hyperbolic
qualification and v1 release gates remain open. These notes neither close
them nor authorize branch, worktree or cloud-recovery deletion.

## Preserved sources and current successors

The five source partners below were fully read during this curation. Their
PDFs are not accepted current projections. Private runtime and capture
preimages are not made independently replayable by these links.

- [Application screen and status](../audit/archive/application-screen-20261001/ARCHIVE.md):
  current [application guide](../PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md)
  and [recorded occupancy results](../audit/evidence/real-occupancy-sensors-example-2026-09-08.md)
  retain the useful common-law and losing-comparison lessons. Newer multi-collection
  results still need their own complete publication.
- [Minimal-family draft and status](../audit/archive/mgw-minimal-meet-20261001/ARCHIVE.md):
  the logical example above is useful now; complete current native-proof
  publication and formal qualification remain open.
- [Application assumptions, source redundancy and stock audit](../audit/archive/shared-exclusions-research-findings-20261001/ARCHIVE.md):
  the decoder budget, captured table and duplicate-loss example above retain
  useful explanations without promoting old tool or application claims.
  The current reader/process reports govern verification accounting.

The archive also contains six failed PDFs, not six mathematical refutations:
missing glyphs, bad layout, and two failed repeated-byte pairs. Retain their
exact bytes and failure predicates. The angular report is available in output
with its original restricted-law and exploratory status.

Suggested citation: Sepehr Mahmoudian, *Useful shared-exclusions notes and
retained failures* (2026), with exact repository commit or release.
Cite defining papers separately; software citation: [CITATION.cff](../CITATION.cff).
