# Finite-alphabet plug-in convergence

## Claim status

This document is **new project analysis in pid-rs**. It is a theoretical-validation note. It is not
a new PID functional, estimator, or scientific-novelty claim.

The note proves exact-real convergence for fixed finite categorical alphabets. It also gives local
continuity bounds and an elementary time-uniform i.i.d. bound. The Rust implementation uses
binary64 arithmetic. Therefore, this note does not prove convergence of an executable Rust output
sequence as the sample count tends to infinity.

The method origins remain separate from this project analysis:

| Quantity or composition | Origin | Code in pid-rs | Coverage in this note |
|---|---|---|---|
| Categorical shared-exclusions SxPID | Paper-defined by Makkeh, Gutknecht, and Wibral; the part-whole lattice is described by Gutknecht, Wibral, and Makkeh | `stable::categorical::discrete_sxpid2`, `discrete_sxpid3`, and `discrete_sxpid_n` for 2–4 sources | Exact-real plug-in convergence on a fixed finite support; local bounds; bounded code comparison |
| Williams--Beer `I_min` | Paper-defined by Williams and Beer | `stable::imin::imin_pid2` and `imin_pid3` | Exact-real plug-in convergence for 2–3 sources; local bounds; bounded code comparison |
| Shannon entropy and mutual-information terms | Paper-defined by Shannon | `diagnostics::{entropy_discrete, joint_entropy_discrete}` and the MI fields in categorical PID results | Exact-real plug-in convergence; an entropy continuity bound |
| Discrete co-information | Paper-defined; pid-rs uses Bell's sign convention and records McGill's opposite convention | `diagnostics::co_information_pairwise_discrete` | Exact-real convergence as a fixed entropy combination |
| Discrete O-information | Paper-defined by Rosas et al. | `diagnostics::o_information_discrete` | Exact-real convergence as a fixed entropy combination |
| Target-free `Red°` and `Vul°` | Project-defined analogues | `diagnostics::{red_degree_discrete, vul_degree_discrete}` | Ratio convergence when the population joint entropy is positive |
| Target-based `r̄` and `v̄` reports | Paper-defined ratios with a project-defined report policy | `diagnostics::{average_degree_of_redundancy, average_degree_of_vulnerability}` | Ratio convergence when joint MI is positive; eventual report status needs separation from the policy threshold |
| Fitted equal-width transform plus categorical PID | Project-defined composition; quantization has published background | `stable::quantized::{fitted_quantized_sxpid2, fitted_quantized_sxpid3, fitted_quantized_sxpid_n}` and `stable::imin::{imin_pid2_quantized, imin_pid3_quantized}` | Conditional corollary for one independent, frozen, almost-surely total finite-output transform |

The authoritative method and paper map is [METHODS.md](METHODS.md). The machine-readable source is
[method-catalog.json](method-catalog.json).

The mathematical paper is available as
[LaTeX source](audit/formal/latex/finite-alphabet-plugin-convergence.tex) and as a
[rendered PDF](output/pdf/finite-alphabet-plugin-convergence.pdf). The LaTeX paper states the full
derivations, proof boundaries, counterexamples, and correction ledger in a typeset form. The Lean
artifact remains the machine-checked deterministic core.

## 1. Fixed objects and notation

Fix the following objects:

- a source count $m$;
- finite deterministic source alphabets $\mathcal S_1,\ldots,\mathcal S_m$;
- a finite deterministic target alphabet $\mathcal T$;
- the joint alphabet

  $$
  \mathcal Z=\mathcal S_1\times\cdots\times\mathcal S_m\times\mathcal T;
  $$

- one probability law $P$ on $\mathcal Z$; and
- one fixed finite redundancy lattice whose nodes are nonempty antichains of nonempty source
  subsets.

For pid-rs SxPID, $m\in\{2,3,4\}$. For pid-rs `I_min`, $m\in\{2,3\}$.

Let $Z_1,Z_2,\ldots$ be observations. Let the prefix empirical law be

$$
\widehat P_n(z)=\frac1n\sum_{j=1}^{n}\mathbf 1\{Z_j=z\}.
$$

Let

$$
S=\operatorname{supp}(P),\qquad
p_{\min}=\min_{z\in S}P(z)>0.
$$

The minimum exists because $S$ is finite. All logarithms are natural. All information quantities
are in nats.

## 2. Main exact-real theorem

### Theorem 1: deterministic plug-in implication

Assume that a sequence of probability laws $Q_n$ has these properties:

1. $Q_n(z)\to P(z)$ for every $z\in\mathcal Z$.
2. $\operatorname{supp}(Q_n)\subseteq S$ for every $n$.

These two conditions imply that there is an $N_0$ such that
$\operatorname{supp}(Q_n)=S$ for every $n\ge N_0$. The required supported-event denominators are
positive on this tail. Thus, the following exact-real quantities are defined on that tail and
converge simultaneously to the corresponding quantities evaluated at $P$:

1. Every supported-realization SxPID cumulative informative term.
2. Every supported-realization SxPID cumulative misinformative term.
3. Every informative and misinformative SxPID Möbius atom.
4. Every signed net SxPID atom.
5. Every empirical-probability-weighted averaged SxPID atom.
6. Every supported-target `I_min` specific-information value.
7. Every two- and three-source `I_min` redundancy and Möbius atom.
8. Every fixed finite-alphabet Shannon entropy, mutual information, co-information, and
   O-information expression formed from the same law.

Pointwise SxPID convergence is keyed by the joint realization. It is not keyed by the position of a
record in a returned vector. A newly observed lexicographically earlier state can change all later
positions.

### Corollary 1: i.i.d. or stationary ergodic sampling

The conditions of Theorem 1 hold almost surely in either of these cases:

- $Z_j$ are i.i.d. with law $P$; or
- $(Z_j)$ is strictly stationary and ergodic, and its one-time marginal law is $P$.

Strict stationarity without ergodicity is not sufficient.

### Proof

For each fixed cell $z$, apply the strong law to the indicator $\mathbf 1\{Z_j=z\}$ in the i.i.d.
case. Apply the pointwise ergodic theorem to the same indicator in the stationary ergodic case. The
alphabet is finite. Therefore, one probability-one event gives simultaneous coordinate convergence
for all cells.

If $P(z)=0$, then that cell does not occur almost surely. In the stationary case, each time index
has zero probability for that cell, and a countable union still has probability zero. Thus,
$\operatorname{supp}(\widehat P_n)\subseteq S$ for all $n$, almost surely.

If $P(z)>0$, coordinate convergence gives $\widehat P_n(z)>P(z)/2>0$ for all sufficiently large
$n$. The support has finitely many positive cells. Take the largest of their finite entry times.
This gives eventual support equality.

Fix a supported realization $z=(s_1,\ldots,s_m,t)$ and an antichain $\alpha$. Let

$$
A_\alpha(s)=
\bigcup_{a\in\alpha}\{S_a=s_a\},\qquad
B_\alpha(s,t)=A_\alpha(s)\cap\{T=t\},\qquad
C(t)=\{T=t\}.
$$

Each required event contains $z$. Its population mass is at least $P(z)>0$. Event masses are finite
linear sums of cell masses. The following cumulative quantities are therefore continuous on the
fixed support face:

$$
c^+_\alpha(z;Q)=-\log Q(A_\alpha(s)),
$$

$$
c^-_\alpha(z;Q)=
\log\frac{Q(C(t))}{Q(B_\alpha(s,t))}.
$$

For a fixed lattice, Möbius inversion is one fixed finite linear map. It preserves convergence.
The signed atom is the difference of its informative and misinformative atoms. It also converges.
After support stabilization, each average is a fixed finite sum over $S$. Its weights and its
pointwise values converge. No off-support $x\log x$ argument is needed for this SxPID result.

For a nonempty source subset $a$ and a supported target value $t$, write

$$
J_a(t;Q)=
\sum_{s_a:Q(s_a,t)>0}
\frac{Q(s_a,t)}{Q(t)}
\log\frac{Q(s_a,t)}{Q(s_a)Q(t)}.
$$

After support stabilization, the positive marginal cells are fixed. Every denominator associated
with a positive numerator is positive. Each finite term is continuous. A finite minimum of
continuous functions is continuous, including at a tie. Target averaging and the fixed Möbius map
preserve convergence. A tie can remove differentiability. It does not remove continuity.

Finally, set $h(0)=0$ and $h(x)=-x\log x$ for $x>0$. The function $h$ is continuous on $[0,1]$.
Each finite-alphabet entropy is a finite sum of $h$. Marginalization and fixed finite linear
combinations preserve convergence. This proves the Shannon claims. ∎

## 3. Local continuity bounds

These bounds make the support dependence explicit. They are conservative. They are not uniform
over all finite-alphabet laws.

These are exact-real law-level bounds. They do not include binary64 rounding, platform `log`
variation, resource rejection, or implementation refinement. The Rust SxPID and `I_min` paths
reject sample counts above $2^{53}$. This theorem does not remove that executable limit.

Let $p$ be the probability vector of the fixed law $P$ from Section 1, and let $q$ be another law
on the same finite joint alphabet. Thus,

$$
S=\operatorname{supp}(p),\qquad
p_{\min}=\min_{z\in S}p(z).
$$

Define

$$
\delta=\lVert q-p\rVert_1.
$$

Assume $\delta\le p_{\min}/2$. For any event $E$,

$$
|q(E)-p(E)|\le\delta.
$$

This uses a deliberately loose form of the total-variation bound. If $E$ contains a supported
cell, both the required population mass and the nearby mass are bounded away from zero. The mean
value theorem for $\log$ gives

$$
|c^+_\alpha(z;q)-c^+_\alpha(z;p)|
\le \frac{2\delta}{p_{\min}},
$$

$$
|c^-_\alpha(z;q)-c^-_\alpha(z;p)|
\le \frac{4\delta}{p_{\min}}.
$$

Let $M$ be the fixed Möbius matrix. Define its absolute row-sum norm by

$$
\lVert M\rVert_\infty=
\max_i\sum_j|M_{ij}|.
$$

The pointwise informative, misinformative, and net atom errors are at most

$$
\frac{2\lVert M\rVert_\infty\delta}{p_{\min}},\qquad
\frac{4\lVert M\rVert_\infty\delta}{p_{\min}},\qquad
\frac{6\lVert M\rVert_\infty\delta}{p_{\min}},
$$

respectively.

For averaged atoms, also require $\operatorname{supp}(q)\subseteq S$. This condition holds for an
empirical law sampled from $p$. Let $L=\log(1/p_{\min})$. The informative, misinformative, and net
averaged-atom errors are at most

$$
\lVert M\rVert_\infty
\left(\frac{2}{p_{\min}}+L\right)\delta,
$$

$$
\lVert M\rVert_\infty
\left(\frac{4}{p_{\min}}+L\right)\delta,
$$

and

$$
\lVert M\rVert_\infty
\left(\frac{6}{p_{\min}}+L\right)\delta.
$$

For the last weight-change term, use $c^+_\alpha-c^-_\alpha\in[-L,L]$ before the Möbius map. This
gives one factor of $L$ for the net atom instead of separately adding the two component bounds.

The support condition cannot be removed from a uniform linear guarantee of this form. A new cell
of mass $\varepsilon$ can contribute at order $\varepsilon\log(1/\varepsilon)$. No fixed constant
can bound that term by $C\varepsilon$ as $\varepsilon\downarrow0$.

Under the section-wide condition $\delta\le p_{\min}/2$, the common-support condition also implies
$\operatorname{supp}(q)=S$. Each supported cell retains mass at least $p_{\min}/2$.

### `I_min` bound

Assume $\operatorname{supp}(q)\subseteq S$ in addition to the section-wide condition
$\delta\le p_{\min}/2$. For a supported target $t$, use the notation from Theorem 1. The
conditional weights are $w=r/v$, where $r=q(s_a,t)$ and $v=q(t)$. The log term is
$\ell=\log(r/(uv))$, where $u=q(s_a)$.

Marginalization contracts the joint $L^1$ distance. The positive marginal masses are at least
$p_{\min}$ under $p$. Each of the three logarithm factors changes by at most
$2\delta/p_{\min}$. Thus, the log-term change is at most $6\delta/p_{\min}$. The
conditional-weight vectors satisfy

$$
\begin{aligned}
\sum_{s_a}|w_q(s_a)-w_p(s_a)|
&\le
\frac{\sum_{s_a}|r_q(s_a)-r_p(s_a)|}{v_q}
+\frac{|v_q-v_p|}{v_q} \\
&\le \frac{4\delta}{p_{\min}}.
\end{aligned}
$$

Also, $|\ell_p|\le\log(2/p_{\min})$ under the stated neighborhood. Therefore,

$$
|J_a(t;q)-J_a(t;p)|
\le
\left[4\log\left(\frac{2}{p_{\min}}\right)+6\right]
\frac{\delta}{p_{\min}}.
$$

A finite minimum is one-Lipschitz in the sup norm. Let $C_J$ denote the coefficient of $\delta$ in
the preceding bound. For a lattice node $\alpha$, define

$$
R_\alpha(t;Q)=\min_{a\in\alpha}J_a(t;Q).
$$

Define the target-averaged redundancy by

$$
I^{\min}_{\cap}(\alpha;Q)=\sum_t Q(t)R_\alpha(t;Q).
$$

Each $J_a(t;p)$ is a Kullback--Leibler divergence, so it is nonnegative. Also,

$$
J_a(t;p)
=\sum_{s_a}p(s_a\mid t)\log\frac{p(t\mid s_a)}{p(t)}
\le -\log p(t)\le L.
$$

Thus, $0\le R_\alpha(t;p)\le L$. Marginalization gives
$\lVert q_T-p_T\rVert_1\le\delta$. Therefore,

$$
\begin{aligned}
\left|\sum_t q(t)R_\alpha(t;q)-\sum_t p(t)R_\alpha(t;p)\right|
&\le \sum_t q(t)|R_\alpha(t;q)-R_\alpha(t;p)| \\
&\quad +\sum_t|q(t)-p(t)|R_\alpha(t;p) \\
&\le (C_J+L)\delta.
\end{aligned}
$$

Since $L=\log(1/p_{\min})$, the last line is the target-averaged redundancy bound. Multiplication
by the absolute row-sum norm of the fixed `I_min` Möbius matrix gives the associated atom bound.

## 4. Shannon bounds and ratio conditions

Let one entropy term have an alphabet with $K\ge2$ cells. Put

$$
\varepsilon=\frac12\lVert q-p\rVert_1.
$$

Apply the Audenaert bound to diagonal density matrices with diagonals $p$ and $q$. Their trace
distance is $\varepsilon$, and their von Neumann entropies are $H(p)$ and $H(q)$. When
$0\le\varepsilon\le1-1/K$, the Fannes--Audenaert bound gives

$$
|H(q)-H(p)|
\le
\varepsilon\log(K-1)+h_2(\varepsilon),
$$

where

$$
h_2(x)=-x\log x-(1-x)\log(1-x).
$$

Use $h_2(0)=h_2(1)=0$. For a marginal entropy, use its own alphabet size $K_A$ and its own total
variation $\varepsilon_A$. If $\varepsilon_A>1-1/K_A$, use the valid bound $\log K_A$. If only the
joint total variation $\varepsilon$ is available, marginal contraction gives the safe bound

$$
|H(q_A)-H(p_A)|
\le
g_{K_A}\!\left(\min\left\{\varepsilon,1-1/K_A\right\}\right),
$$

where $g_K(x)=x\log(K-1)+h_2(x)$. An alphabet with $K_A=1$ has entropy difference zero. This
clipping is necessary because $g_K$ is not increasing after $1-1/K$. A fixed entropy linear
combination is bounded by the sum of the absolute coefficients times these term-specific bounds.
This includes mutual information, discrete co-information, and discrete O-information.

For a ratio $N/D$, assume $D_p\ge d>0$, $|D_q-D_p|\le d/2$, and $|N_p|\le B$. Then

$$
\left|\frac{N_q}{D_q}-\frac{N_p}{D_p}\right|
\le
\frac{2|N_q-N_p|}{d}
+\frac{2B|D_q-D_p|}{d^2}.
$$

The target-free `Red°` and `Vul°` limits therefore require positive population joint entropy. The
target-based `r̄` and `v̄` limits require positive population joint MI. All target-based input MI
terms must describe the same law, target, source order, units, preprocessing, evaluation sample,
and estimand. For the convergence claim, each input sequence must be the corresponding exact-real
finite-alphabet plug-in term formed from the same empirical law. A positive denominator alone does
not establish this semantic coherence. Report status has an extra rule. If the fixed policy
threshold is $\tau$, a population denominator that is strictly larger than $\tau$ guarantees
eventual `Defined` status. A population denominator below $\tau$ guarantees eventual non-defined
status. Equality at the threshold gives no eventual status guarantee.

## 5. Time-uniform i.i.d. bound

This section gives an elementary, conservative result. Hoeffding's inequality and union bounds are
published tools. Their use here is a paper-derived project bound. Its derivation is new in pid-rs,
but pid-rs makes no scientific-novelty claim for it.

Assume i.i.d. sampling from one fixed $K$-cell law. Let $0<\alpha<1$, and define

$$
\alpha_n=\frac{6\alpha}{\pi^2n^2}.
$$

For one cell, two-sided Hoeffding gives

$$
\Pr\left(
|\widehat P_n(z)-P(z)|\ge x
\right)
\le2e^{-2nx^2}.
$$

Apply a union bound over the $K$ cells and over all $n\ge1$. With probability at least
$1-\alpha$, simultaneously for every $n\ge1$,

$$
\lVert\widehat P_n-P\rVert_1
\le
B_n:=K
\sqrt{
\frac{\log\left(K\pi^2n^2/(3\alpha)\right)}{2n}
}.
$$

Let

$$
N_0=
\min\left\{r:
B_n\le p_{\min}/2\text{ for every }n\ge r
\right\}.
$$

The integer $N_0$ is finite because $B_n\to0$. Intersect the probability-$1-\alpha$ concentration
event with the probability-one support-containment event from Section 2. The intersection still
has probability at least $1-\alpha$. On this event, support equality holds for all $n\ge N_0$.
Apply Section 3 with $p=P$ and $q=\widehat P_n$. Substitute the upper bound $B_n$ for the actual
$\delta$ in each displayed upper bound.

For a fixed earlier prefix $N$, the separate support-discovery bound is

$$
\Pr\left[
\operatorname{supp}(\widehat P_N)\ne S
\right]
\le |S|e^{-Np_{\min}}
\le Ke^{-Np_{\min}}.
$$

Once a state enters a cumulative prefix, it remains in every later prefix. This persistence does
not hold for a sliding window.

The bound needs a known positive lower bound on $p_{\min}$ to produce $N_0$. An empirical minimum
is not a valid substitute because a rare population cell can be absent. The simultaneous $L^1$
bound can be read at any almost-surely finite data-dependent index. The support equality and local
bounds in Section 3 additionally require that index to be at least $N_0$. The law must remain the
same fixed i.i.d. law. The result does not cover dependent windows, drift, feedback that changes
the sampling law, rejection-selected samples, or stationary ergodic data without an additional
rate assumption.

This probability statement controls the exact-real empirical law. It is not a confidence sequence
for Rust output. It does not include floating-point error, the platform logarithm, resource
failure, or the $2^{53}$ sample-count limit of the categorical PID paths.

## 6. Frozen-transform corollary

Let $\mathcal G$ be the sigma-field generated by a training artifact and its fitted transform.
Assume that the training artifact is independent of the raw evaluation sequence. Also assume:

1. The raw evaluation space is standard Borel.
2. A failure symbol $\bot$ is not in the finite output alphabet $\mathcal Z$.
3. One map $Q(\omega,x)$ is measurable from $\mathcal G\otimes\mathcal B(\mathcal X)$ to
   $\mathcal Z\cup\{\bot\}$. Thus, its random choice is determined by the training sigma-field.
4. The output alphabet and block structure are finite and fixed.
5. The map is frozen for every evaluation row and every prefix.
6. Evaluation rows are conditionally i.i.d. given $\mathcal G$.
7. $\Pr(Q(W_1)\ne\bot\mid\mathcal G)=1$ almost surely.

The transformed categorical law is the random conditional push-forward law

$$
P_Q(z)=\Pr(Q(W_1)=z\mid\mathcal G),\qquad z\in\mathcal Z.
$$

Condition on $\mathcal G$, and apply Corollary 1 to this finite law. The limit is the PID or Shannon
quantity of $P_Q$. It is not generally the same as the quantity of the unconditional mixture.
These functionals are nonlinear in the law.

`OutOfRangePolicy::Error` satisfies this corollary only when the conditional evaluation law has
mass one inside every inclusive fitted range and satisfies every input-validity rule. Let
$\eta=\eta(\mathcal G)$ be the conditional per-row failure probability. For each training outcome
with $\eta>0$, conditional i.i.d. sampling gives success probability $(1-\eta)^n$ for the first
$n$ rows, and the infinite prefix fails with conditional probability one. Unconditionally, the
failure probability from this mechanism is $\Pr(\eta>0)$. It is one only when $\eta>0$ almost
surely. Conditioning an accepted prefix on complete success does not preserve the original-law
infinite-prefix claim. Explicit rejection sampling can produce rows that are conditionally i.i.d.
given $\mathcal G$ from a conditional law when the success probability is positive. That law is a
different estimand and needs a declared sampling contract.

`OutOfRangePolicy::ClampToBoundary` gives a total range map for otherwise valid finite inputs. It
defines a tail-clamped categorical estimand. It is not the error-policy estimand.

The corollary excludes same-row fitting, changing transforms, arbitrary pooling across folds that
use different transforms, and target-adaptive fitting on evaluation rows. Training-target-adaptive
PLS is compatible only when it is fitted on the independent training artifact, frozen, and applied
to disjoint conditionally i.i.d. evaluation rows.

## 7. Falsification lenses and retained counterexamples

The following checks are part of the result. They show why stronger statements are false.

| Lens | Falsifying construction or boundary | Consequence |
|---|---|---|
| Support and topology | Let a new cell have mass $\varepsilon\downarrow0$. Its local informative term can grow like $-\log\varepsilon$. | Pointwise continuity across support faces fails. Linear averaged bounds also fail without a common-support condition. |
| Probability | Draw $C\sim\operatorname{Bernoulli}(1/2)$, then set $Z_j=C$ for every $j$. The process is stationary but not ergodic. | A path sees only one state although the one-time marginal support has two states. Stationarity alone is insufficient. |
| Rare-state discovery | Give one state mass $\varepsilon$. It is absent after $n$ i.i.d. rows with probability $(1-\varepsilon)^n$. | No deterministic support-discovery time is uniform over all finite laws. |
| `I_min` differentiability | Move through a law where two source-specific information values tie and exchange minimizer order. | The finite minimum stays continuous, but a generic derivative, delta-method CLT, or fixed minimizer does not follow. |
| Transform design | Fit finite min/max ranges, then evaluate a nondegenerate continuous held-out law under the error policy. | Positive out-of-range mass usually remains. Infinite-prefix success then has probability zero. |
| Mixture target | Randomly select one of two fitted transforms, then average their push-forward laws before applying PID. | PID of the mixture need not equal the conditional PID or the average of conditional PIDs. |
| Indexing | Append a rare state that is lexicographically earlier than all common states. | Pointwise vector positions shift. A realization key is required. |
| Numerical refinement | Increase the prefix beyond the exact binary64 integer range, or change the platform `log` implementation. | The exact-real asymptotic theorem does not become a portable Rust-output theorem. |
| Downstream dependence | Reuse overlapping temporal windows, drift the law, or reject full samples after inspecting their columns. | The i.i.d. proof and its Hoeffding envelope do not apply. A separate dependence or selection theorem is required. |

## 8. Invalidated stronger claims

These proposals were considered and rejected. Do not use them without a new proof.

1. **Rejected:** “Strict stationarity is sufficient.” Ergodicity or another pathwise frequency
   condition is required.
2. **Rejected:** “All-unique samples identify the population support.” A sample cannot prove that
   claim.
3. **Rejected:** “Pointwise atoms converge by vector index.” They converge by realization key.
4. **Rejected:** “A deterministic support-discovery time works for every finite law.” Rare cells
   rule it out.
5. **Rejected:** “Conditioning on complete success preserves the original error-policy estimand.”
   It does not. Explicit rejection sampling can define a different conditional-law estimand, but
   it needs a separate contract.
6. **Rejected:** “A conditional fitted-transform limit is the PID of the unconditional mixture.”
   Nonlinearity rules it out in general.
7. **Rejected:** “Pool foldwise PMFs or atoms when each fold uses a different fitted map.” No such
   cross-fit theorem is proved here.
8. **Rejected:** “The Lean artifact proves the stochastic theorem or the Rust implementation.” It
   proves only the deterministic lemmas listed in Section 9.
9. **Rejected:** “A small fixture tolerance is a portable binary64 or `libm` error theorem.” The
   tolerance applies only to the committed cases.
10. **Rejected:** “There is a simple practical exact sign and tie routine for all input sizes.” A
    rational linear combination of logarithms can be reduced in principle to an integer-product
    comparison after denominator clearing. The resulting powers can be too large for a practical
    unrestricted implementation. No such API exists in pid-rs.
11. **Rejected:** “The i.i.d. time-uniform bound covers sliding or dependent windows.” It does not.
12. **Rejected:** “Continuity at an `I_min` tie implies a normal limit.” Continuity alone gives no
    differentiability or CLT.

### Corrected review defects

The review process found and corrected these defects before acceptance. This list retains the
invalid formulations and the reason for each correction.

1. An early local-bound draft introduced arbitrary laws $p$ and $q$ but reused $p_{\min}$ from a
   different law $P$. The rare-cell event can then violate the stated bound. Section 3 now sets
   $p=P$ explicitly.
2. An early Shannon draft substituted joint total variation directly into every marginal
   Fannes--Audenaert expression. The expression is not increasing after $1-1/K$. For example, a
   four-cell joint variation of $0.7$ can induce a binary marginal variation of $0.5$. The direct
   substitution gives less than the valid $\log 2$ entropy difference. Section 4 now clips each
   marginal bound at $1-1/K_A$ and handles $K_A=1$ separately.
3. An early transform draft required ordinary joint measurability but did not require the random
   map to be determined by the training sigma-field. With a trivial training sigma-field, the map
   $Q(\omega,x)=x\mathbin{\mathrm{xor}}W_1(\omega)$ can destroy conditional independence. Section 6
   now requires training-measurable map selection.
4. An early theorem draft did not restrict the convergence claim to the support-stabilized tail.
   Early supported-event denominators can be zero. It also did not exclude an empty antichain,
   whose union event is empty. Sections 1 and 2 now state both domain restrictions.
5. An early stopping-time sentence omitted the condition that the selected index must be at least
   $N_0$ before support and local-bound conclusions apply. Section 5 now separates the all-time
   $L^1$ statement from the support-stabilized conclusions.
6. An early transform draft treated a random conditional failure probability $\eta$ as if it were
   positive almost surely. The unconditional infinite-prefix failure probability is
   $\Pr(\eta>0)$, not always one. Section 6 now states the result on each training fiber and then
   gives the unconditional probability.
7. An early rejection statement did not distinguish complete-prefix selection from explicit
   rejection sampling. Rejection sampling can define an i.i.d. conditional-law sequence when its
   success probability is positive. It does not preserve the original estimand. Section 6 now
   requires a new declared estimand and sampling contract.
8. An early report-status sentence treated a population denominator above the threshold as a
   necessary condition for eventual `Defined` status. At threshold zero, start a binary table with
   $(n_{00},n_{01},n_{10},n_{11})=(2,0,0,2)$ and repeatedly append $01,10,00,11$. The empirical law
   converges to uniform independence, but empirical MI stays positive. Section 4 now says strict
   separation supplies a guarantee and equality supplies no guarantee.
9. An early downstream draft used “independent” or “fixed-law” without a common-law or ergodicity
   condition. Independent non-identical blocks need not have limiting frequencies. A stationary
   latent-constant process has a fixed one-time marginal but is not ergodic. Section 10 now states
   the required row laws.
10. An early evidence draft attributed fixed-quantizer inputs to the digest-bound JSON fixture.
    Those inputs occur only in the companion Rust test. Section 9 now separates the two evidence
    paths.
11. The first valid averaged-net bound used $2L$ by adding separate component envelopes. Directly
    using $c^+_\alpha-c^-_\alpha\in[-L,L]$ gives the tighter $L$ term now stated in Section 3.
12. An intermediate entropy-bound draft asserted $p_{\min}\le 1/K$. This is false when $K$ is the
    declared alphabet size and $P$ has sparse support; one-cell support has $p_{\min}=1$. No
    accepted bound uses this claim. Section 4 treats alphabet size and supported-cell mass
    separately.

## 9. Formal and numerical evidence boundary

The pinned Lean 4.32.0 artifact is in [audit/formal/lean](audit/formal/lean). It proves these
deterministic exact-real lemmas:

- eventual positivity at a positive limit;
- convergence of finite event masses;
- positivity of a finite sum of nonnegative cell masses when the event contains a positive cell;
- sequential-limit preservation by $\log$ and $-\log$ at positive limits, and by log ratios at
  positive limits;
- sequential-limit preservation by $-x\log x$, including at zero;
- preservation of convergence by a fixed finite linear combination;
- preservation of convergence by a fixed finite weighted sum;
- preservation of convergence by a finite nonempty minimum, including at ties; and
- preservation of convergence by a finite weighted sum of finite positive-limit log-ratio linear
  combinations.

The artifact does **not** encode an empirical PMF, an i.i.d. model, the strong law, the ergodic
theorem, a shared-exclusions event, a redundancy lattice, an `I_min` definition, or Rust refinement.
The checker binds the complete Lake manifest and all nine package revisions. It verifies each
dependency checkout's root, revision, origin, and clean status. It disables global and system Git
configuration and Git environment routing. It retains the checkout's local configuration to
verify the recorded origin. The checked project sources cannot contain the tokens `admit`, `axiom`,
`constant`, `sorry`, or `sorryAx`. The checker builds the project and replays its declarations with
Lean's bundled kernel checker. CI runs the same build and kernel checks. These checks strengthen
proof artifact verification. They do not enlarge the theorem boundary.

The independent Decimal generator is
[scripts/generate-finite-alphabet-plugin-oracle.py](scripts/generate-finite-alphabet-plugin-oracle.py).
It uses 100-digit standard-library Decimal arithmetic and direct definitions. It imports no pid-rs
code. Its digest-bound fixture covers:

- all 4, 18, and 166 averaged SxPID coordinates in listed 2-, 3-, and 4-source tables;
- informative, misinformative, and signed net values;
- realization-key changes after a late rare state;
- two- and three-source `I_min` tables;
- `I_min` left/tie/right minimizer crossings.

The Rust test also checks same-process, bit-identical categorical equality for separately fitted
error-policy and clamp-policy wrappers. For the committed Decimal fixture cases, it uses an
absolute acceptance envelope of $64\,\mathtt{f64::EPSILON}$ nats. This envelope is not a portable or
global binary64 error bound.

This is bounded implementation evidence. It is not a proof of Theorem 1, an external review, a
population validation, or a global floating-point bound.

## 10. Downstream contract audit

| Consumer | Covered path | Uncovered path |
|---|---|---|
| Prisoma | Use conditionally i.i.d. cases or episodes from one common conditional law. Use one evaluation row per unit, or separately establish conditionally i.i.d. rows. Split independent units. Fit all transforms on the fit partition. Freeze them. Apply them to a disjoint evaluation partition. Then call categorical PID. | Independent but non-identically distributed units; multiple dependent rows from one episode; same-row fitting; pooling outputs from different fitted maps; other dependent evaluation units without a separate theorem. |
| Galadriel | Direct categorical evaluation on i.i.d. rows with a fixed alphabet. | Continuous KSG on dependent temporal windows; same-window scaling; added-noise studies; circular delete-block analyses; complete-sample rejection after inspecting degeneracy. |
| Haldir | I.i.d. or strictly stationary and ergodic fixed-law rows for finite-alphabet entropy, co-information, O-information, SxPID, and positive-denominator ratio limits. | A fixed one-time marginal without ergodicity; drift; CUSUM; alarms; overlapping windows; post-alarm re-estimation; calibration. These need sequential and dependence-aware theory. |
| Crebain | The stable categorical and fitted-transform contracts can be used after an explicit dependency and input-contract review. | No current compatibility or adapter claim is established by this theorem. |

No downstream repository is a runtime dependency of pid-rs. This audit states mathematical
preconditions. It does not claim downstream qualification.

## 11. Reproduction

```text
python3 scripts/generate-finite-alphabet-plugin-oracle.py
cargo test --locked -p pid-core --test finite_alphabet_plugin_oracle
python3 scripts/check-lean-finite-convergence.py
scripts/check-finite-alphabet-convergence-pdf.sh
python3 scripts/check-method-catalog.py
```

## 12. Open mathematical work

The following results remain open in pid-rs:

1. A dependence-aware analogue for mixing or otherwise controlled temporal processes.
2. A sequential law that separates fixed-law monitoring from drift detection and post-alarm
   re-estimation.
3. A triangular-array or cross-fit theorem for changing fitted transforms.
4. Certified practical sign and tie evaluation for large empirical categorical PID expressions.
5. A deductive refinement from the mathematical formulas to Rust binary64 or an interval-arithmetic
   implementation.
6. A formal encoding of the empirical-law stochastic step and the actual SxPID and `I_min`
   definitions.

## References

- K. M. R. Audenaert, “A sharp continuity estimate for the von Neumann entropy,” 2007,
  [doi:10.1088/1751-8113/40/28/S18](https://doi.org/10.1088/1751-8113/40/28/S18).
- A. J. Bell, “The Co-Information Lattice,” 2003,
  [paper](https://www.rd.ntt/cs/team_project/icl/signal/ica2003/cdrom/data/0187.pdf).
- R. M. Gray and D. L. Neuhoff, “Quantization,” 1998,
  [doi:10.1109/18.720541](https://doi.org/10.1109/18.720541).
- A. J. Gutknecht, M. Wibral, and A. Makkeh, “Bits and Pieces: Understanding Information
  Decomposition from Part-Whole Relationships and Formal Logic,” 2021,
  [doi:10.1098/rspa.2021.0110](https://doi.org/10.1098/rspa.2021.0110).
- A. J. Gutknecht, F. E. Rosas, D. A. Ehrlich, A. Makkeh, P. A. M. Mediano, and M. Wibral,
  “Shannon Invariants: A Scalable Approach to Information Decomposition,” 2025,
  [doi:10.48550/arXiv.2504.15779](https://doi.org/10.48550/arXiv.2504.15779).
- W. Hoeffding, “Probability Inequalities for Sums of Bounded Random Variables,” 1963,
  [doi:10.1080/01621459.1963.10500830](https://doi.org/10.1080/01621459.1963.10500830).
- A. Makkeh, A. J. Gutknecht, and M. Wibral, “Introducing a Differentiable Measure of Pointwise
  Shared Information,” 2021,
  [doi:10.1103/PhysRevE.103.032149](https://doi.org/10.1103/PhysRevE.103.032149).
- W. J. McGill, “Multivariate Information Transmission,” 1954,
  [doi:10.1007/BF02289159](https://doi.org/10.1007/BF02289159).
- F. E. Rosas, P. A. M. Mediano, M. Gastpar, and H. J. Jensen, “Quantifying High-Order
  Interdependencies via Multivariate Extensions of the Mutual Information,” 2019,
  [doi:10.1103/PhysRevE.100.032305](https://doi.org/10.1103/PhysRevE.100.032305).
- C. E. Shannon, “A Mathematical Theory of Communication,” 1948,
  [doi:10.1002/j.1538-7305.1948.tb01338.x](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x).
- P. L. Williams and R. D. Beer, “Nonnegative Decomposition of Multivariate Information,” 2010,
  [arXiv:1004.2515](https://arxiv.org/abs/1004.2515).
