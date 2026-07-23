# Dependency-colored concentration for finite-alphabet SxPID

Status: project-defined validation and proof composition. It is not a claim of scientific novelty.

Primary scope: the Wibral-lineage categorical shared-exclusions PID in `pid-rs`.

LaTeX/typeset paper source:
[`audit/formal/latex/dependency-colored-sxpid-concentration.tex`](audit/formal/latex/dependency-colored-sxpid-concentration.tex).

Rendered paper:
[`output/pdf/dependency-colored-sxpid-concentration.pdf`](output/pdf/dependency-colored-sxpid-concentration.pdf).

Lean module:
[`audit/formal/lean/PidFiniteConvergence/Dependence.lean`](audit/formal/lean/PidFiniteConvergence/Dependence.lean).

Executable challenge suite:
[`scripts/generate-dependency-colored-sxpid-oracle.py`](scripts/generate-dependency-colored-sxpid-oracle.py).

Bounded Rust implementation comparison:
[`crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`](crates/pid-core/tests/dependency_colored_sxpid_oracle.rs).

PDF checker:
[`scripts/check-dependency-colored-sxpid-pdf.sh`](scripts/check-dependency-colored-sxpid-pdf.sh).

## Result map

| Object | Origin | Code in `pid-rs` | Result here |
|---|---|---|---|
| Categorical shared-exclusions PID | Paper-defined by Makkeh, Gutknecht, and Wibral; the lattice has a formal-logic basis from Gutknecht, Wibral, and Makkeh | `stable::categorical::{discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n}` and averaged forms; two to four sources | A dependency-colored finite-sample law bound and an almost-sure exact-real plug-in consistency implication when the displayed envelope vanishes |
| Hoeffding bounded-variable inequality | Paper-defined classical result | No estimator implementation; used in the proof | One color-class moment bound |
| Dependency-color concentration | Published background includes Janson's coloring method and later Hölder formulations | No public statistical API in this increment | A project-defined finite-alphabet proof composition with a class-size proxy that is optimal within the declared Hölder–Hoeffding proof scheme |
| Empirical-law $L^1$ deviation | Published independent and identically distributed (i.i.d.) background includes Weissman et al. | No public statistical API in this increment | A one-sided subset union bound under the stated color contract |
| SxPID local continuity modulus | Project-defined validation of a paper-defined functional | Lean proves generic deterministic lemmas; the categorical implementation and a bounded comparison test exist; no certified binary64 interval API | A safe common-support baseline with an exact Möbius row norm; the constants are not claimed to be sharp |
| Nonidentical-law drift envelope | Project-defined extension | Formal and executable evidence only | Concentration about the average row law plus an explicit bias term to a reference law |

The machine-readable authority is `method-catalog.json`. `METHODS.md` is its complete human
rendering. “Project-defined” means that this repository states the proof or evidence contract. It
does not mean that the mathematical ingredients are new to science.

## 1. Setup and assumptions

Let $Z_1,\ldots,Z_n$ take values in one finite alphabet $\mathcal Z$ of size $K$. For SxPID, one
row is the complete joint symbol

$$
Z_i=(S_{1i},\ldots,S_{mi},T_i).
$$

Dependence between the source and target coordinates in one row is unrestricted. That dependence
is the PID signal.

For the common-law theorem, every row has the same marginal law $P$. A deterministic map partitions
the row indices into occupied color classes $C_1,\ldots,C_r$. Put

$$
n_j=|C_j|>0,\qquad n=\sum_{j=1}^{r}n_j.
$$

The required dependence contract is:

1. The complete rows in each color class are mutually independent.
2. Dependence across different color classes can be arbitrary.
3. The color map is fixed independently of the observed row values.

Pairwise independence inside a color is not sufficient. A covariance cutoff is not sufficient.
An unspecified mixing label does not establish the color contract.

Define the empirical law and the class-size proxy

$$
\widehat P_n(z)=\frac1n\sum_{i=1}^{n}\mathbf 1\{Z_i=z\},
\qquad
V_n=\left(\sum_{j=1}^{r}\sqrt{n_j}\right)^2.
$$

Also define the effective color factor

$$
d_{\mathrm{eff},n}=\frac{V_n}{n}.
$$

The Lean module proves the deterministic bounds

$$
1\le d_{\mathrm{eff},n}\le r.
$$

The upper bound is an equality for equal class sizes. Do not describe
$d_{\mathrm{eff},n}$ as an estimated effective sample size. It is a deterministic proof constant
derived from
the declared coloring.

## 2. Finite-sample empirical-law theorem

Assume $K\ge2$. For every $\varepsilon>0$,

$$
\Pr\!\left(\|\widehat P_n-P\|_1\ge\varepsilon\right)
\le
\min\!\left\{
1,
(2^K-2)\exp\!\left(-\frac{n^2\varepsilon^2}{2V_n}\right)
\right\}.
\tag{1}
$$

If at most $d$ colors are occupied, then $V_n\le dn$, so

$$
\Pr\!\left(\|\widehat P_n-P\|_1\ge\varepsilon\right)
\le
\min\!\left\{
1,
(2^K-2)\exp\!\left(-\frac{n\varepsilon^2}{2d}\right)
\right\}.
\tag{2}
$$

For $K=1$, the distance is zero and Equations (1) and (2) reduce to the true but empty statement
$0\le0$ for every $\varepsilon>0$. The time-uniform radius below contains
$\log(2^K-2)$, so that section requires $K\ge2$.

The subset factor is exponential in $K$. The resulting bound can be vacuous on a large alphabet.
This theorem makes no sharpness or sample-complexity claim.

If the support size $s=\lvert\operatorname{supp}(P)\rvert\ge2$ is known before the data are
inspected, $2^s-2$ can replace
$2^K-2$. This replacement is valid because common-law samples stay in
$\operatorname{supp}(P)$ almost surely. An observed support size is not a known population support
size. When $s=1$, the law distance is zero and the result is vacuous.

### Proof

Fix one nonempty proper subset $A$ of the alphabet. Define

$$
Y_i=\mathbf 1\{Z_i\in A\}-P(A),
\qquad
S_j=\sum_{i\in C_j}Y_i.
$$

Let

$$
R=\sum_{j=1}^{r}\sqrt{n_j},
\qquad
p_j=\frac{R}{\sqrt{n_j}}.
$$

Then $\sum_jp_j^{-1}=1$. Each $p_j\ge1$ because $R\ge\sqrt{n_j}$, so these are valid Hölder
exponents. Generalized Hölder gives

$$
\mathbb E\exp\!\left(\lambda\sum_jS_j\right)
\le
\prod_j\left(\mathbb E e^{p_j\lambda S_j}\right)^{1/p_j}.
$$

Rows are mutually independent inside each color. Hoeffding's lemma therefore gives

$$
\mathbb E e^{p_j\lambda S_j}
\le
\exp\!\left(\frac{n_jp_j^2\lambda^2}{8}\right).
$$

Hence

$$
\mathbb E\exp\!\left(\lambda\sum_jS_j\right)
\le
\exp\!\left(\frac{\lambda^2V_n}{8}\right).
$$

Chernoff optimization at $\lambda=4nt/V_n$ gives

$$
\Pr\!\left(\widehat P_n(A)-P(A)\ge t\right)
\le
\exp\!\left(-\frac{2n^2t^2}{V_n}\right).
$$

For two probability laws on a finite set,

$$
\frac12\|Q-P\|_1=\max_A\{Q(A)-P(A)\}.
$$

Set $t=\varepsilon/2$ and take a union bound over the $2^K-2$ nonempty proper subsets. This proves
Equation (1). Complements already encode the opposite sign. There is no additional factor of two.

Let $q_j>0$ satisfy $\sum_jq_j^{-1}=1$. These conditions force every $q_j\ge1$, so they define
valid Hölder exponents. Then

$$
\left(\sum_j\sqrt{n_j}\right)^2
\le
\left(\sum_jn_jq_j\right)\left(\sum_jq_j^{-1}\right)
=\sum_jn_jq_j.
$$

Equality holds for $q_j=R/\sqrt{n_j}$. Thus the selected exponents minimize the Hoeffding proxy
inside this proof scheme. This is not a claim that $V_n$ is the best possible constant for every
joint law.

## 3. Time-uniform envelope

Assume $K\ge2$. For an infinite row sequence, use one fixed map from the positive integers to a
finite or countable
color set. Only finitely many colors can be occupied in each prefix. The entire infinite collection
in each color must consist of mutually independent complete rows. Let $V_n$ use the nonempty class sizes in the
first $n$ rows. A uniform bound of at most $d$ occupied colors is required only for the coarse
radius in Equation (5).

For $0<\alpha<1$, set

$$
C_K=2^K-2,
\qquad
\alpha_n=\frac{\alpha}{n(n+1)}.
$$

The allocation telescopes:

$$
\sum_{n=1}^{N}\alpha_n
=\alpha\left(1-\frac1{N+1}\right)
\le\alpha.
$$

Lean proves the unit-scale finite identity exactly. Multiplication by the fixed scalar
$\alpha$ gives the displayed allocation. Define

$$
R_n=
\sqrt{
\frac{2V_n}{n^2}
\log\!\left(\frac{C_Kn(n+1)}{\alpha}\right)
},
\qquad
D_n=\min\{2,R_n\}.
\tag{3}
$$

Then

$$
\Pr\!\left(
\forall n\ge1:\
\|\widehat P_n-P\|_1\le D_n
\right)\ge1-\alpha.
\tag{4}
$$

The clip at two is exact because the $L^1$ distance between probability laws cannot exceed two.
For at most $d$ occupied colors, the coarser radius is

$$
D_n^{(d)}=
\min\!\left\{
2,
\sqrt{
\frac{2d}{n}
\log\!\left(\frac{C_Kn(n+1)}{\alpha}\right)
}
\right\}.
\tag{5}
$$

Under one uniform fixed bound $d$, the radius is $O(\sqrt{d\log(n)/n})$. For each positive
rational error threshold, the finite-sample tails are summable. Borel-Cantelli and a countable
intersection over those thresholds then give

$$
\|\widehat P_n-P\|_1\longrightarrow0
\quad\text{almost surely}.
$$

If the number of colors grows, the displayed envelope converges to zero under the sufficient
condition

$$
\frac{V_n\log n}{n^2}\longrightarrow0.
$$

This condition is not necessary for empirical-law convergence. For example, i.i.d. rows still
converge when a needlessly fine singleton coloring gives $V_n=n^2$. The condition is sufficient
for this declared-color envelope. One color per row also permits complete dependence across rows,
so the theorem cannot infer convergence from that coloring alone.

### Fixed-width overlapping-window corollary

Let $E_t$ be i.i.d. innovations, let $w\in\mathbb N$ be fixed before evaluation, and let

$$
Z_t=f(E_t,\ldots,E_{t+w-1})
$$

for one fixed measurable finite-output map $f$. Color row $t$ by $t\bmod w$. Two rows in the same
color use disjoint innovation blocks. The complete rows in each color class are therefore mutually
independent. The finite-sample theorem applies with the exact class-size proxy and with at most
$d=w$ colors.

This corollary covers a fixed categorical overlapping-window construction from i.i.d. innovations.
It does not cover circular wraparound windows, a width selected from evaluation outcomes, a
rolling-start sequence of repeated claims, or innovations with unspecified time dependence.

A separate strong-dependence route is available when its full sigma-field premise is known. Let
$\ell\in\mathbb N_0$. Call the ordered sequence strongly $\ell$-dependent when
$\sigma(Z_i:i\le t)$ is independent of $\sigma(Z_i:i\ge t+\ell+1)$ for every $t$.
Color index $t$ by $t\bmod(\ell+1)$. Consecutive indices in one color are separated by more than
$\ell$. Repeatedly separate the last row from the sigma-field generated by all preceding rows.
This ordered induction proves mutual independence of all complete rows in that color. Pairwise
lag independence alone does not prove this property. The common-law theorem still requires one
common row law. If row laws differ, use the drift theorem and meet its additional premises.

## 4. Nonidentical row laws and drift

Assume $K\ge2$. Now let row $i$ have law $P_i$. Keep the same within-color
mutual-independence contract. Define

$$
\overline P_n=\frac1n\sum_{i=1}^{n}P_i.
$$

Center each subset indicator by $P_i(A)$. The same proof gives

$$
\Pr\!\left(\|\widehat P_n-\overline P_n\|_1\ge\varepsilon\right)
\le
\min\!\left\{
1,
C_K\exp\!\left(-\frac{n^2\varepsilon^2}{2V_n}\right)
\right\}.
\tag{6}
$$

Let $P_\star$ be an explicit reference law, and define

$$
b_n=\|\overline P_n-P_\star\|_1.
$$

The triangle inequality gives

$$
\Pr\!\left(
\|\widehat P_n-P_\star\|_1\ge b_n+\varepsilon
\right)
\le
\min\!\left\{
1,
C_K\exp\!\left(-\frac{n^2\varepsilon^2}{2V_n}\right)
\right\}.
\tag{7}
$$

If $\lVert P_i-P_\star\rVert_1\le\beta_i$, then

$$
b_n\le\frac1n\sum_{i=1}^{n}\beta_i.
$$

Under one fixed infinite row-law sequence and coloring with the same premises, the all-prefix
reference-law envelope is

$$
\Pr\!\left(
\forall n\ge1:\
\|\widehat P_n-P_\star\|_1\le\min\{2,b_n+D_n\}
\right)\ge1-\alpha.
\tag{8}
$$

The bias term is necessary. Concentration about $\overline P_n$ does not identify a fixed
scientific estimand. A workflow must justify $b_n$; it must not infer it from the concentration
result.

## 5. Stronger local SxPID modulus

Let $p$ and $q$ be two laws on the complete joint alphabet. Set

$$
\delta=\|q-p\|_1,
\qquad
p_{\min}=\min_{z\in\operatorname{supp}(p)}p(z),
\qquad
L=\log(1/p_{\min}).
$$

Assume

$$
\operatorname{supp}(q)\subseteq\operatorname{supp}(p),
\qquad
0\le\delta<2p_{\min}.
\tag{9}
$$

Condition (9) implies equal support. For every SxPID event $E$ that contains the keyed supported
realization,

$$
p(E)\ge p_{\min},
\qquad
|q(E)-p(E)|\le\delta/2.
$$

All logarithms below are natural, so every information value is in nats. Fix a supported
realization $z=(s_1,\ldots,s_m,t)$ and a nonempty antichain $\alpha$ of nonempty source subsets.
For a source subset $a$, the event $\{S_a=s_a\}$ fixes all source coordinates in $a$. Define

$$
A_\alpha(s)
=
\bigcup_{a\in\alpha}\{S_a=s_a\},
\qquad
B_\alpha(s,t)
=
A_\alpha(s)\cap\{T=t\},
\qquad
C(t)=\{T=t\}.
$$

Each event contains $z$. For a law $Q$ whose three event masses are positive, define the
cumulative informative, misinformative, and net shared-exclusions values

$$
c_\alpha^+(z;Q)=-\log Q(A_\alpha(s)),
$$

$$
c_\alpha^-(z;Q)
=
\log\frac{Q(C(t))}{Q(B_\alpha(s,t))},
\qquad
c_\alpha^{\mathrm{sx}}(z;Q)
=
c_\alpha^+(z;Q)-c_\alpha^-(z;Q).
$$

Let $M$ be the fixed Möbius matrix for the chosen redundancy lattice. For
$u\in\{+,-,\mathrm{sx}\}$, the pointwise and averaged atoms are

$$
\pi_\alpha^u(z;Q)
=
\sum_\beta M_{\alpha\beta}c_\beta^u(z;Q),
\qquad
\overline\pi_\alpha^u(Q)
=
\sum_{z\in\operatorname{supp}(Q)}
Q(z)\pi_\alpha^u(z;Q).
$$

Define

$$
\Lambda(\delta,p_{\min})
=-\log\!\left(1-\frac{\delta}{2p_{\min}}\right).
\tag{10}
$$

Lean proves the one-log bound

$$
|\log q(E)-\log p(E)|\le\Lambda(\delta,p_{\min}).
$$

For one lattice node, the cumulative informative, misinformative, and net errors are at most

$$
\Lambda,\qquad 2\Lambda,\qquad 3\Lambda.
\tag{11}
$$

Let $M$ be the fixed Möbius matrix, and let

$$
r_\alpha=\sum_\beta|M_{\alpha\beta}|
$$

be the exact absolute row sum for atom $\alpha$. The pointwise atom bounds are

$$
r_\alpha\Lambda,
\qquad
2r_\alpha\Lambda,
\qquad
3r_\alpha\Lambda.
\tag{12}
$$

The common-support averaged atom bounds are

$$
r_\alpha\left(\Lambda+\frac{L\delta}{2}\right),
\qquad
r_\alpha\left(2\Lambda+\frac{L\delta}{2}\right),
\qquad
r_\alpha(3\Lambda+L\delta).
\tag{13}
$$

Equations (11)-(13) are conservative generic Möbius-row baselines. They do not use the
paper-defined nonnegativity of the informative and misinformative SxPID atoms. They are valid upper
bounds, but this document does not claim that they are sharp SxPID constants.

The informative and misinformative weight terms in Equation (13) use $L\delta/2$. A half-factor for
the net weight term does not follow from the generic cumulative-value range alone. The centered
half-range tightening is new in `pid-rs`. It is project-defined validation, not a claim of
scientific novelty or publication priority.

To see the weight term, write one component as

$$
\begin{aligned}
\left|
\sum_z q(z)\pi_\alpha^u(z;q)
-
\sum_z p(z)\pi_\alpha^u(z;p)
\right|
&\le
\sum_z q(z)
\left|\pi_\alpha^u(z;q)-\pi_\alpha^u(z;p)\right|\\
&\quad+
\left|\sum_z(q(z)-p(z))\pi_\alpha^u(z;p)\right|.
\end{aligned}
$$

For any finite real function $f$ and signed weights $h$ with $\sum_z h(z)=0$,

$$
\left|\sum_z h(z)f(z)\right|
\le
\frac{\sum_z|h(z)|}{2}
\left(\max_z f(z)-\min_z f(z)\right).
$$

This follows by centering $f$ at the midpoint of its range. Here $h=q-p$ and
$\sum_z|h(z)|=\delta$. At $p$, each cumulative informative and misinformative value is in
$[0,L]$. Therefore, the oscillation of its Möbius atom is at most $r_\alpha L$, which gives
$r_\alpha L\delta/2$. Each cumulative net value is in $[-L,L]$, so its atom oscillation is at most
$2r_\alpha L$. This gives the net term $r_\alpha L\delta$. It does not add separate informative
and misinformative weight terms.

For $\delta\le p_{\min}/2$, put $x=\delta/(2p_{\min})\le1/4$. Lean also proves

$$
\Lambda\le\frac{x}{1-x}\le\frac{4x}{3}
=\frac{2\delta}{3p_{\min}}.
\tag{14}
$$

Equations (10)-(14) improve the looser valid constants in
`FINITE_ALPHABET_PLUGIN_CONVERGENCE.md`. They remain exact-real law-level statements.

## 6. Composition with the concentration event

For common-law sampling, empirical support is a subset of population support almost surely. On the
event in Equation (4), if

$$
D_n<2p_{\min},
$$

then empirical and population supports are equal. The realized error satisfies $\delta\le D_n$,
and $\Lambda(\delta,p_{\min})$ is nondecreasing in $\delta$. Therefore, use $D_n$ on the right-hand side
of Equations (10)-(13). This gives simultaneous exact-real envelopes for every supported SxPID
cumulative term and every fixed Möbius atom.

A usable numerical envelope needs an externally justified lower bound on $p_{\min}$. Do not estimate
$p_{\min}$ from the same rows and substitute it without a separate confidence argument. The theorem
does not provide that argument.

For the drift extension, also require every $P_i$ to be supported inside
$\operatorname{supp}(P_\star)$. Define

$$
p_{\min,\star}
=
\min_{z\in\operatorname{supp}(P_\star)}P_\star(z).
$$

If

$$
b_n+D_n<2p_{\min,\star},
$$

then the realized error is at most $b_n+D_n$. Monotonicity gives the same support and modulus
composition with $b_n+D_n$ on the right-hand side.

A frozen finite-output transform can be handled conditionally on its independent training
artifact. Conditional on that artifact, the color map must be fixed. Every row must have the stated
conditional law. The complete rows in every color class must be mutually independent. A random
conditional $p_{\min}$ gives a conditional result unless a deterministic lower bound is available.

The displayed common-law envelope proves almost-sure exact-real plug-in consistency under the
sufficient condition
$V_n\log(n)/n^2\to0$. A fixed color count is sufficient. The displayed drift envelope proves
almost-sure exact-real reference-law SxPID consistency when this sufficient condition holds and
$b_n\to0$. These
conditions are not necessary conditions for consistency under a stronger sampling theorem.

These results do not cover continuous $I_\cap^{\mathrm{sx}}$, arbitrary overlapping windows,
adaptive preprocessing on evaluation rows, unknown mixing rates, or binary64 asymptotics.

## 7. Counterexamples and invalidated routes

The following failed routes remain part of the record.

| Invalid route | Falsifying construction | Required correction |
|---|---|---|
| Replace mutual independence by pairwise independence | Let $U$ be uniform on $\mathbb F_2^4$. Use the 15 nonzero linear forms $\langle a,U\rangle$ as fair binary rows. Every pair is independent. All rows are zero with probability $1/16$, so the empirical $L^1$ error is one. The false one-color bound is $2\exp(-15/2)$, which is about $0.00111$. | Require mutual independence of all complete rows in each color. |
| Remove the color factor | Take $m$ independent fair bits and copy each bit once into every one of $d$ colors. Each color is i.i.d., but the colors are exact copies. Only $m=n/d$ independent values remain. | Keep $V_n$, or use the coarser factor $d$. |
| Infer convergence from one color per row | Set every row equal to one common fair bit. Each singleton color is independent. Here, $V_n=n^2$, and the empirical law does not converge to the fair law. | The declared-color envelope cannot prove convergence. Use a stronger valid coloring or a different sampling theorem. |
| Read the envelope condition as necessary | Let the rows be i.i.d. but assign every row a separate color. Then $V_n=n^2$, although the empirical law converges by the strong law. | State $V_n\log(n)/n^2\to0$ only as a sufficient condition for this envelope. |
| Condition only on a data-adaptive coloring | Let every row equal one fair bit. Select one occupied color from the observed bit value. Conditional rows are degenerate, but their conditional law is not the common unconditional law. | Require the full conditional common-law and independence premises, or use a fixed color map. |
| Substitute a mixing label for the color premise | Use a stationary fair two-state Markov chain with flip probability $\eta=1/100$. Its transition dependence decays geometrically. For two rows, the empirical $L^1$ error is one with probability $1-\eta=0.99$, above the false one-color bound $2e^{-1}$. | Use a theorem with an explicit mixing coefficient and rate, or prove a valid independence coloring. |
| Use pairwise lag independence as strong $\ell$-dependence | The finite-field construction has pairwise independence but has a joint failure. | Require $\sigma(Z_i:i\le t)$ to be independent of $\sigma(Z_i:i\ge t+\ell+1)$ for every $t$. Ordered induction then shows that each residue class modulo $\ell+1$ contains mutually independent complete rows. |
| Halve the net weight term from the generic range alone | On two points, take signed weights $h=(-\delta/2,\delta/2)$ and a generic row value $f=(-r_\alpha L,r_\alpha L)$. Then $\lvert\sum h f\rvert=r_\alpha L\delta$. The range premises alone permit this extremizer. This row value is not shown to be realizable by an SxPID atom when $r_\alpha>1$. It proves no SxPID sharpness claim. | Keep the generic range baseline unless a separate SxPID argument supplies a smaller range. |
| Allow $\delta=2p_{\min}$ in the log modulus | Move all mass from a least-probable supported cell. That cell becomes zero, and its required logs are undefined. | Keep $\delta<2p_{\min}$ strict. |
| Control only separate marginals | Set $S_1=S_2=X$. For $0<\rho<1$ and the supported realization $(X,T)=(0,0)$, use fair binary $X,T$ marginals with diagonal cells $(1+\rho)/4$ and off-diagonal cells $(1-\rho)/4$. Then replace $\rho$ by $-\rho$. Marginals do not change, but the pointwise redundancy changes by $\log((1+\rho)/(1-\rho))$. | Control the complete joint law. |
| Permit new support and retain a uniform linear averaged bound | Let $p(0,0,0)=1$. Let $q(0,0,0)=1-\varepsilon$ and $q(1,1,1)=\varepsilon$. Then $\lVert q-p\rVert_1=2\varepsilon$, while the averaged shared-exclusions redundancy is the binary entropy $-(1-\varepsilon)\log(1-\varepsilon)-\varepsilon\log\varepsilon$. | Require common support or use a non-linear boundary modulus. |
| Infer a population support floor from the observed minimum frequency | An unobserved positive cell has empirical frequency zero. | Use a justified external floor or a separate simultaneous lower-confidence argument. |

The executable challenge suite enumerates the finite-field pairwise-independence construction,
copied-color construction, singleton-color construction, and adaptive-color construction. It also
checks a support-deletion boundary, an unspecified-mixing construction, a generic net-weight range
extremizer, a univariate-marginal-only construction, and a new-support construction. The remaining
checks cover the telescoping allocation, class-size inequalities, high-precision one-log cases, all
displayed bounds on three committed two-source law pairs, and the fixed-window construction below.

The fixed-window fixture uses independent fair innovations $U_t,V_t$ and

$$
S_{1,t}=U_t\mathbin{\mathrm{OR}}U_{t+1},
\qquad
S_{2,t}=V_t\mathbin{\mathrm{OR}}V_{t+1},
\qquad
T_t=S_{1,t}\mathbin{\mathrm{XOR}}S_{2,t}.
$$

Even and odd starts are the two colors. Its exact joint count weights are $1:3:3:9$. The
high-precision Decimal oracle supplies the expected logarithmic values. For stored logarithmic
constants and bounds, the Rust reconstruction tolerance is

$$
32\varepsilon_{\mathrm{mach}}
\max(1,|x_{\mathrm{Rust}}|,|x_{\mathrm{oracle}}|).
$$

For categorical estimator outputs, the absolute comparison ceiling is
$32\varepsilon_{\mathrm{mach}}$ nats, where
$\varepsilon_{\mathrm{mach}}=2^{-52}$ for binary64. The test also checks that row reversal gives
bit-identical output.

## 8. Formal and executable boundary

The Lean module has no admitted proof placeholders. The repository checker rejects such
placeholders, builds the pinned Lean project, and replays its declarations with Lean's kernel
checker.

Lean proves:

- the event-mass $\delta/2$ lemma and exact attainment by the positive-coordinate event;
- positivity under the strict support margin;
- the one-log modulus, its monotonicity, and its rational simplification;
- both effective-color proxy inequalities and the normalized factor range;
- the generic absolute linear-row bound;
- the generic finite weighted-average perturbation bounds, including the centered half-range form;
- the exact unit-scale finite telescoping allocation; and
- the algebraic radius-exponent cancellation.

Lean does not encode:

- random variables or conditional laws;
- generalized Hölder, Hoeffding, Chernoff, or the probability union bound;
- the drift result or fixed-window independence argument;
- SxPID events, the redundancy lattice, or the identification of the generic row and weighted-average
  lemmas with SxPID atoms;
- refinement between the mathematical definitions and Rust; or
- binary64 rounding.

The radius declaration, positivity conditions, square-root substitution, and its probability
interpretation remain in the prose proof.

The Python challenge suite uses exact rational arithmetic for finite probability and count
identities. It uses 100-digit Decimal arithmetic for logarithms. Transcendental logarithms are not
exact rational values. From each local count-table pair, the Rust test independently reconstructs
both empirical laws. It also reconstructs $\delta$, $p_{\min}$, $\Lambda$, $L$, and every stored
node bound before it checks the implementation outputs. The test uses the scale-aware reconstruction
tolerance and the absolute categorical-output ceiling declared above. These checks are bounded
executable evidence. They are not a proof of the general theorem, a global binary64 bound, or
external review.

## 9. Ecosystem use boundary

| Consumer | What this result can supply | What is still required |
|---|---|---|
| Prisoma | A categorical SxPID law envelope after a frozen finite-output map when held-out rows meet the color contract | A concrete row law, a justified support floor, an independent transform receipt, and a test that the intended windows have the declared coloring |
| Galadriel | A dependence-aware categorical alternative to an i.i.d. plug-in claim | Removal of same-window fitting and generic jitter routes; an explicit observation and coloring contract |
| Haldir | A mathematical target for block or residue-class designs | A direct dependency, corrected atom interpretation, and proof that its sampling process meets strong $\ell$-dependence or another valid color contract |
| Crebain | A finite-alphabet validation component for a future integration | An exact observation mapping, a run-log contract, a direct dependency, and an explicit scientific estimand |

This result does not assert that any consumer already meets these premises. Integration remains
`not_claimed` until the consumer records and checks them.

## 10. References

- Makkeh, A., Gutknecht, A. J., and Wibral, M. (2021). “Introducing a differentiable measure of
  pointwise shared information.” *Physical Review E*, 103, 032149.
  <https://doi.org/10.1103/PhysRevE.103.032149>
- Gutknecht, A. J., Wibral, M., and Makkeh, A. (2021). “Bits and pieces: understanding information
  decomposition from part-whole relationships and formal logic.” *Proceedings of the Royal Society
  A*, 477, 20210110. <https://doi.org/10.1098/rspa.2021.0110>
- Hoeffding, W. (1963). “Probability inequalities for sums of bounded random variables.” *Journal
  of the American Statistical Association*, 58(301), 13-30.
  <https://doi.org/10.1080/01621459.1963.10500830>
- Janson, S. (2004). “Large deviations for sums of partly dependent random variables.” *Random
  Structures & Algorithms*, 24(3), 234-248. <https://doi.org/10.1002/rsa.20008>
- Pelekis, C., Ramon, J., and Wang, Y. (2017). “Hölder-type inequalities and their applications to
  concentration and correlation bounds.” *Indagationes Mathematicae*, 28(1), 170-182.
  <https://doi.org/10.1016/j.indag.2016.11.017>
- Weissman, T., Ordentlich, E., Seroussi, G., Verdú, S., and Weinberger, M. J. (2003).
  “Inequalities for the L1 deviation of the empirical distribution.” HPL-2003-97 (R.1).
  <https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2003/HPL-2003-97R1.pdf>
