# Dependency-colored concentration for finite-alphabet SxPID

Status: project-defined validation and proof composition. It is not a claim of scientific novelty.

Primary scope: the categorical shared-exclusions PID of Makkeh, Gutknecht, and Wibral in
`pid-rs`.

LaTeX/typeset paper source:
[`audit/formal/latex/dependency-colored-sxpid-concentration.tex`](audit/formal/latex/dependency-colored-sxpid-concentration.tex).

Rendered paper:
[`output/pdf/dependency-colored-sxpid-concentration.pdf`](output/pdf/dependency-colored-sxpid-concentration.pdf).

Lean modules:
[`audit/formal/lean/PidFiniteConvergence/Dependence.lean`](audit/formal/lean/PidFiniteConvergence/Dependence.lean)
and
[`audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean`](audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean).

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
| SxPID local continuity modulus | Project-defined validation of a paper-defined functional | Lean proves deterministic algebraic subclaims; a high-precision oracle and a bounded Rust comparison test cover committed laws; no certified binary64 interval API | A one-$\Lambda$ cumulative theorem, general-source Möbius-row bounds, and sharper complete two-source atom-specific bounds. Sharpness evidence is limited to the stated endpoints, the asymptotic coefficient, and one bounded near-tightness fixture case; none proves global sharpness |
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

## 5. Strengthened common-support local SxPID continuity

### 5.1 Claim packet and premises

This section records claim `SXPID-TV-001`, revision 2. Revision 2 records the revision-1 constants
as superseded baselines and retains the generic range extremizer for audit. It uses additional
shared-exclusions structure for the current bounds.

| Field | Content |
|---|---|
| Claim | Common-support local continuity of finite-discrete pointwise and averaged SxPID atoms |
| Objects | Two laws on one fixed complete finite source-target alphabet and the complete redundancy lattice |
| Assumptions | Equal finite support, a population cell floor, and exact-real arithmetic |
| Conclusion | General-source and sharper complete two-source moduli stated below |
| Evidence | Prose proof, machine-checked deterministic subclaims, high-precision oracle, and bounded Rust comparison |
| Not established | A binary64 theorem, estimator calibration, continuous PID validity, or full formal refinement |

Let $p$ and $q$ be laws on the complete joint alphabet. Define

$$
\delta=\|q-p\|_1,
\qquad
\eta=\frac{\delta}{2},
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

The total-variation convention in this section is

$$
\eta=\frac12\|q-p\|_1
=\sup_E|q(E)-p(E)|.
$$

Condition (9) implies equal support. A singleton supported cell has
$q(z)\ge p_{\min}-\eta>0$. Put

$$
p_s=(1-s)p+sq,
\qquad
\mu_s=p_{\min}-s\eta,
\qquad
0\le s\le1.
$$

Every supported cell of $p_s$ has mass at least $\mu_s>0$. All logarithms below are natural, so all
information values are in nats.

### 5.2 Path-oscillation lemma

Let $\Delta=q-p$. For any finite real function $g$ on the common support,

$$
\left|\sum_z\Delta(z)g(z)\right|
\le
\eta\left(\max_z g(z)-\min_z g(z)\right).
$$

The proof subtracts the midpoint of the range and uses $\sum_z\Delta(z)=0$. Empty event regions
carry no signed mass and do not enter the maximum or minimum. Therefore, if a differentiable
functional $F$ has

$$
\operatorname{osc}\nabla F(p_s)\le\frac1{\mu_s},
$$

then

$$
|F(q)-F(p)|
\le
\int_0^1\frac{\eta}{p_{\min}-s\eta}\,ds
=
\log\frac{p_{\min}}{p_{\min}-\eta}
=:\Lambda(\delta,p_{\min}).
\tag{10}
$$

This is an exact path integral. The strict inequality in (9) keeps every denominator positive.

### 5.3 One-$\Lambda$ cumulative theorem

Fix a supported realization $z=(s_1,\ldots,s_m,t)$ and a nonempty antichain $\alpha$ of nonempty
source subsets. For a source subset $a$, the event $\{S_a=s_a\}$ fixes its listed source
coordinates. Define

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

By definition, $B_\alpha=A_\alpha\cap C$, and the keyed realization belongs to $B_\alpha$. For a
law $Q$, define

$$
c_\alpha^+(z;Q)=-\log Q(A_\alpha),
$$

$$
c_\alpha^-(z;Q)
=
\log\frac{Q(C)}{Q(B_\alpha)},
\qquad
c_\alpha^{\mathrm{sx}}(z;Q)
=
\log\frac{Q(B_\alpha)}{Q(A_\alpha)Q(C)}.
$$

The following table gives each cell-gradient value. Here $A=A_\alpha$ and $B=B_\alpha$.

| Region | $\nabla c^+$ | $\nabla c^-$ | $\nabla c^{\mathrm{sx}}$ |
|---|---:|---:|---:|
| $B$ | $-1/Q(A)$ | $1/Q(C)-1/Q(B)$ | $1/Q(B)-1/Q(A)-1/Q(C)$ |
| $A\setminus C$ | $-1/Q(A)$ | $0$ | $-1/Q(A)$ |
| $C\setminus A$ | $0$ | $1/Q(C)$ | $-1/Q(C)$ |
| outside $A\cup C$ | $0$ | $0$ | $0$ |

The first oscillation is at most $1/Q(A)$. The second is at most $1/Q(B)$. For the net column,
every pairwise gradient difference is at most $1/Q(B)$. For example, the difference between the $B$ and
$A\setminus C$ values is $1/Q(B)-1/Q(C)$, and the difference between the $B$ and
$C\setminus A$ values is $1/Q(B)-1/Q(A)$. The remaining differences use
$Q(B)\le Q(A),Q(C)$. Since $p_s(B)\ge\mu_s$, Equation (10) gives

$$
|c_\alpha^u(z;q)-c_\alpha^u(z;p)|
\le\Lambda
\quad
\text{for }u\in\{+,-,\mathrm{sx}\}.
\tag{11}
$$

The direct net calculation is important. Adding separate informative and misinformative bounds
would give a valid but nonoptimal factor of two.

### 5.4 General-source atom and average bounds

Let $M$ be the fixed Möbius matrix of the complete redundancy lattice, and define

$$
\pi_\alpha^u(z;Q)
=
\sum_\beta M_{\alpha\beta}c_\beta^u(z;Q),
\qquad
r_\alpha=\sum_\beta|M_{\alpha\beta}|.
$$

Equation (11) and the triangle inequality give the general-source pointwise result

$$
|\pi_\alpha^u(z;q)-\pi_\alpha^u(z;p)|
\le r_\alpha\Lambda
\quad
\text{for }u\in\{+,-,\mathrm{sx}\}.
\tag{12}
$$

Makkeh, Gutknecht, and Wibral (2021), Theorem IV.3 and Appendix A, prove that the informative and
misinformative pointwise atoms are separately nonnegative at every node of the complete finite
antichain lattice for any finite source count. The paper uses bits. Multiplication by the positive
factor $\log 2$ preserves the result in nats. A positive-probability keyed realization is enough;
full support of the complete table is not required for that published theorem.

At the top node, the component zeta sums are at most $L$. Component nonnegativity therefore gives

$$
0\le\pi_\alpha^+(z;p),\pi_\alpha^-(z;p)\le L,
\qquad
-L\le\pi_\alpha^{\mathrm{sx}}(z;p)\le L.
\tag{13}
$$

The net cumulative also has a sharper lower endpoint. Write

$$
a=p(A_\alpha),\qquad b=p(B_\alpha),\qquad c=p(C).
$$

Then $a,c\ge b\ge p_{\min}$ and $a+c-b=p(A_\alpha\cup C)\le1$. Hence

$$
ac\le\frac{(a+c)^2}{4}\le\frac{(1+b)^2}{4}.
$$

Define

$$
h=\log\frac{2}{1+p_{\min}},
\qquad
J=L-2h\ge0.
$$

Since $4b/(1+b)^2$ is nondecreasing on $[0,1]$,

$$
-J=-L+2h
\le c_\alpha^{\mathrm{sx}}(z;p)
\le L.
\tag{14}
$$

The cumulative range width is $L+J=2(L-h)$. A Möbius row therefore gives net-atom oscillation at
most $2r_\alpha(L-h)$. Equation (13) independently gives oscillation at most $2L$.

For the empirical-law average

$$
\overline\pi_\alpha^u(Q)
=
\sum_{z\in\operatorname{supp}(Q)}
Q(z)\pi_\alpha^u(z;Q),
$$

split the change into a pointwise-value term and a probability-weight term. The first is at most
$r_\alpha\Lambda$. Midpoint centering of the second gives the general-source bounds

$$
\left|
\overline\pi_\alpha^\pm(q)-\overline\pi_\alpha^\pm(p)
\right|
\le
\min\left\{
L,\,
r_\alpha\Lambda+\eta L
\right\},
\tag{15}
$$

$$
\left|
\overline\pi_\alpha^{\mathrm{sx}}(q)
-\overline\pi_\alpha^{\mathrm{sx}}(p)
\right|
\le
\min\left\{
2L,\,
r_\alpha\Lambda
+\delta\min\!\left[L,r_\alpha(L-h)\right]
\right\}.
\tag{16}
$$

The outer amplitude caps follow at the averaged level. The common support has at most
$1/p_{\min}$ cells. Each averaged component atom is nonnegative and is at most its top component
sum, which is a source entropy or conditional source entropy. Thus each averaged component is at
most $\log|\operatorname{supp}(p)|\le L$ under both laws. The net average is in $[-L,L]$.

For the unique bottom row, $r_\alpha=1$ and the inner net weight coefficient is $L-h$. Every
nonbottom Möbius row is a nonzero integer vector with zero sum. Thus it has at least one positive
and one negative entry, so $r_\alpha\ge2$. Because $L-2h\ge0$, the inner coefficient then
simplifies to $L$.

### 5.5 Complete two-source improvement

For two sources, the Möbius row norm is not needed in the pointwise term. Let
$E_i=\{S_i=s_i\}$, $U=E_1\cup E_2$, and $C=\{T=t\}$. Redundancy is a one-event log, nested-log
ratio, or intersection-PMI functional. For a unique atom, define

$$
N(a,b)=\log\frac{a+b}{a},
$$

where $a$ is the mass of $E_i$ and $b$ is the mass of $U\setminus E_i$. Its gradient values are

$$
D_a=\frac1{a+b}-\frac1a,
\qquad
D_b=\frac1{a+b},
$$

and their diameter is $1/a$. A component unique atom is one such nested-event term. For a path law
$Q=p_s$, put

$$
x_a=Q(E_i\cap C),
\quad
x_b=Q((U\setminus E_i)\cap C),
\quad
y_a=Q(E_i\cap C^{\mathsf c}),
\quad
y_b=Q((U\setminus E_i)\cap C^{\mathsf c}).
$$

A net unique atom is $N(x+y)-N(x)$, with componentwise addition. If
$F_i=D_i(x+y)$ and $X_i=F_i-D_i(x)$ for $i\in\{a,b\}$, the lifted gradient values are
$F_a,F_b,X_a,X_b$, and zero. The keyed cell gives $x_a\ge\mu_s$. The $F$ pair has diameter
$1/(x_a+y_a)\le1/x_a$.
The same-index differences satisfy $F_i-X_i=D_i(x)$. Also,

$$
X_a-X_b
=
\frac1{x_a}-\frac1{x_a+y_a}.
$$

The two crossed differences are
$F_a-X_b=-1/(x_a+y_a)+D_b(x)$ and
$F_b-X_a=1/(x_a+y_a)+D_a(x)$. Each is a difference of two values in
$[0,1/x_a]$. Every individual value has magnitude at most $1/x_a$. These cases prove that the
lifted gradient diameter is at most $1/x_a$.

The same representation gives the net-unique range. Let $a,b$ be the target-region masses and let
$a_{\mathrm f}\ge a$, $b_{\mathrm f}\ge b$ be their full-event masses. Then

$$
\exp(\pi_{\mathrm{unique}}^{\mathrm{sx}})
=
\frac{a(a_{\mathrm f}+b_{\mathrm f})}{a_{\mathrm f}(a+b)}
\ge
\frac{4a}{(1+a)^2}
\ge
\frac{4p_{\min}}{(1+p_{\min})^2}.
$$

Indeed, $b_{\mathrm f}\ge b$ and $a_{\mathrm f}+b_{\mathrm f}\le1$ imply

$$
\frac{a(a_{\mathrm f}+b_{\mathrm f})}{a_{\mathrm f}(a+b)}
\ge
\frac{a(a_{\mathrm f}+b)}{a_{\mathrm f}(a+b)}
\ge
\frac{a}{(1-b)(a+b)}.
$$

The last denominator is at most $(1+a)^2/4$ by the arithmetic-geometric mean inequality.
The function $4a/(1+a)^2$ is nondecreasing on $[0,1]$. The upper endpoint is $L$ because
$N(a_{\mathrm f},b_{\mathrm f})\le L$ and $N(a,b)\ge0$. Thus, under the $p$-law, a net unique atom
lies in $[-J,L]$.

For synergy, partition the source space into
$E_1\cap E_2$, $E_1\setminus E_2$, $E_2\setminus E_1$, and the outside region
$O=(E_1\cup E_2)^{\mathsf c}$. For any law, let $a,b,c,o$ be the masses of these four regions in
that order. Define

$$
\Phi(a,b,c)
=
\log\frac{(a+b)(a+c)}{a(a+b+c)}.
$$

Its gradient is

$$
D_a
=
\frac1{a+b}+\frac1{a+c}-\frac1a-\frac1{a+b+c},
$$

$$
D_b=\frac1{a+b}-\frac1{a+b+c},
\qquad
D_c=\frac1{a+c}-\frac1{a+b+c},
\qquad
D_o=0.
$$

Here $D_a\le0\le D_b,D_c$, and

$$
D_b-D_a=\frac1a-\frac1{a+c},
\qquad
D_c-D_a=\frac1a-\frac1{a+b}.
$$

Thus $\operatorname{osc}D\le1/a$. The informative synergy is $\Phi$ on the full source-event
partition. The misinformative synergy is $\Phi$ on the same partition restricted to $C$.

For a path law $Q=p_s$, define the target-region coordinates

$$
(x_a,x_b,x_c,x_o)
=
\bigl(
Q(E_1\cap E_2\cap C),
Q((E_1\setminus E_2)\cap C),
Q((E_2\setminus E_1)\cap C),
Q(O\cap C)
\bigr),
$$

and define $(y_a,y_b,y_c,y_o)$ by replacing $C$ with $C^{\mathsf c}$. The net synergy is the
conditioned difference

$$
G_\Phi(x,y)=\Phi(x+y)-\Phi(x).
$$

The keyed cell gives $x_a\ge\mu_s$. Its eight gradient values use $i\in\{a,b,c,o\}$:

$$
F_i=D_i(x+y),
\qquad
X_i=F_i-D_i(x).
$$

The complete pair audit is as follows:

- The $F$-$F$ pairs use the ordinary diamond bound.
- The $X_a$-$X_b$ and $X_a$-$X_c$ pairs are differences of two nonnegative diamond gaps in
  $[0,1/x_a]$.
- The $X_b$-$X_c$ pair is the difference of two reciprocal decrements in $[-1/x_a,0]$.
- The ordinary diamond signs give
  $-D_a(v),D_b(v),D_c(v)\in[0,1/v_a]$. Thus each $X_i$ is a difference of two
  values in $[0,1/x_a]$. This controls all pairs with the outside coordinate $o$.
  Same-index pairs satisfy $F_i-X_i=D_i(x)$.
- The crossed $a$-$b$ and $a$-$c$ pairs are differences of two nonnegative values in
  $[0,1/x_a]$.

After the symmetry $b\leftrightarrow c$, the only remaining crossed form is

$$
F_b-X_c
=
H(x+y)+D_c(x),
\qquad
H(v)=\frac1{v_a+v_b}-\frac1{v_a+v_c}.
$$

If $H(x+y)\ge0$, then $H(x+y)\le1/(x_a+x_b)$; combine this with
$D_c(x)-D_a(x)=1/x_a-1/(x_a+x_b)$ and $D_a(x)\le0$. If $H(x+y)<0$, use
$H(x+y)\ge-1/(x_a+x_c)$ and $D_c(x)\ge0$; the upper bound then follows from
$D_c(x)\le1/x_a$. The reverse inequality and the $F_c$-$X_b$ pair are symmetric. Hence every pair
of lifted gradient values differs by at most $1/x_a$.

The analogous conditioned nested-event calculation proves the same bound for each net unique
atom. Path integration therefore gives the complete two-source result

$$
|\pi_\alpha^u(z;q)-\pi_\alpha^u(z;p)|
\le\Lambda
\quad
\text{for every two-source atom and }u\in\{+,-,\mathrm{sx}\}.
\tag{17}
$$

The atom-specific ranges under the $p$-law improve the centered weight terms. The $p$-law diamond
satisfies

$$
0\le\Phi(a,b,c)\le J.
\tag{18}
$$

For the upper bound, put $u=a+b+c\ge a$. The arithmetic-geometric mean inequality gives
$(a+b)(a+c)\le(a+u)^2/4$. The ratio $(a+u)^2/(4au)$ is nondecreasing in $u\ge a$, so $u\le1$
reduces it to $(1+a)^2/(4a)$. This last expression is nonincreasing for $0<a\le1$.
Thus $a\ge p_{\min}$ gives Equation (18). Under the $p$-law, redundancy and unique net atoms lie in
$[-J,L]$, and net synergy lies in $[-J,J]$. These ranges apply to the $p$-weighted term in the
average-change split. The outer caps in the following table use support cardinality and therefore
bound the averaged values under both laws.
The resulting two-source bounds are

| Atom | Component average change | Net average change |
|---|---:|---:|
| Redundancy | $\min\{L,\Lambda+\eta L\}$ | $\min\{2L,\Lambda+\delta(L-h)\}$ |
| Either unique atom | $\min\{L,\Lambda+\eta L\}$ | $\min\{2L,\Lambda+\delta(L-h)\}$ |
| Synergy | $\min\{L,\Lambda+\eta J\}$ | $\min\{2L,\Lambda+\delta J\}$ |

These are project-defined validation bounds for the paper-defined SxPID atoms. They are not new PID
definitions or estimators. The complete two-source result uses only the displayed two-source log
expressions and elementary range arguments. It does not use the published general-source
component-nonnegativity result that supports Equations (13), (15), and (16).

### 5.6 Sharpness, superseded routes, and limits

The cumulative lower endpoint in Equation (14) is attained as an event bound when the
intersection has mass $p_{\min}$, the two exclusive regions each have mass
$(1-p_{\min})/2$, and there is no outside mass. This uses $p_{\min}\le1/3$ so the exclusive cells
respect the same floor. A separate nested event of mass $p_{\min}$ and an outside cell of mass
$1-p_{\min}$ attains the upper endpoint when $p_{\min}\le1/2$. These separate event laws do not
prove that a general Möbius-row bound is sharp.

The first revision used cumulative errors $(\Lambda,2\Lambda,3\Lambda)$ and pointwise errors
$(r_\alpha\Lambda,2r_\alpha\Lambda,3r_\alpha\Lambda)$. Those values remain valid triangle-inequality
baselines. They are superseded because they do not use the direct nested and intersection-PMI
gradients. The retained generic two-point extremizer
$f=(-r_\alpha L,r_\alpha L)$ is not shown to be SxPID-realizable and establishes no SxPID
sharpness.

A realizable two-source family shows that no fixed coefficient $cL$ with $c<1$ can replace the
$L$-order nonbottom net weight term uniformly as $p_{\min}\downarrow0$. In lexicographic
binary-cell order, let

$$
p_\varepsilon
=
\left(
\varepsilon,\frac16,\frac13,\varepsilon,
\frac12-5\varepsilon,\varepsilon,\varepsilon,\varepsilon
\right),
\qquad
0<\varepsilon<\frac1{12}.
$$

For net synergy, the values at $000$ and $111$ are

$$
-L+\log 10+o(1)
\quad\text{and}\quad
L-\log(40/3)+o(1).
$$

Their oscillation divided by $L$ tends to two as $\varepsilon\downarrow0$. Moving mass
$0<\rho<\varepsilon$ from $000$ to $111$ preserves support and gives $\delta=2\rho$. This proves
asymptotic necessity of the $\delta L$ centered net-weight coefficient for that decomposition. For
admissible $\rho<\varepsilon$, the $\Lambda$ pointwise-value term can dominate the total bound.
Thus this family does not prove that the full averaged bound is globally sharp. Whether every
nonbottom SxPID atom has a stronger exact lower floor remains open.

The asymptotic statement is a prose derivation from the displayed family. The executable fixture
checks only the finite case $\varepsilon=1/60$ and its near-tight pointwise $\Lambda$ ratios.

For $\delta\le p_{\min}/2$, put $\xi=\delta/(2p_{\min})\le1/4$. Lean also proves

$$
\Lambda\le\frac{\xi}{1-\xi}\le\frac{4\xi}{3}
=\frac{2\delta}{3p_{\min}}.
\tag{19}
$$

The results remain exact-real law-level statements. They do not establish a global binary64 error
bound, behavior after support creation, or a continuous-estimator theorem.

## 6. Composition with the concentration event

For common-law sampling, empirical support is a subset of population support almost surely. On the
event in Equation (4), if

$$
D_n<2p_{\min},
$$

then empirical and population supports are equal. The realized error satisfies $\delta\le D_n$.
The function $\Lambda(\delta,p_{\min})$ and every displayed right-hand side are nondecreasing in
$\delta$. Therefore, substitute $D_n$ for $\delta$ in Equation (10), and use the result in
Equations (11), (12), (15), (16), (17), and the two-source table. This gives simultaneous
exact-real envelopes for every supported cumulative term, every fixed general-source Möbius atom,
and every complete two-source atom.

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
| Substitute a mixing label for the color premise | Use a stationary fair two-state Markov chain with flip probability $\theta=1/100$. Its transition dependence decays geometrically. For two rows, the empirical $L^1$ error is one with probability $1-\theta=0.99$, above the false one-color bound $2e^{-1}$. | Use a theorem with an explicit mixing coefficient and rate, or prove a valid independence coloring. |
| Use pairwise lag independence as strong $\ell$-dependence | The finite-field construction has pairwise independence but has a joint failure. | Require $\sigma(Z_i:i\le t)$ to be independent of $\sigma(Z_i:i\ge t+\ell+1)$ for every $t$. Ordered induction then shows that each residue class modulo $\ell+1$ contains mutually independent complete rows. |
| Halve the net weight term from the generic range alone | On two points, take signed weights $w=(-\delta/2,\delta/2)$ and a generic row value $f=(-r_\alpha L,r_\alpha L)$. Then $\lvert\sum w f\rvert=r_\alpha L\delta$. The range premises alone permit this extremizer. This row value is not shown to be realizable by an SxPID atom when $r_\alpha>1$. It proves no SxPID sharpness claim. | Keep the generic range baseline unless a separate SxPID argument supplies a smaller range. |
| Allow $\delta=2p_{\min}$ in the log modulus | Move all mass from a least-probable supported cell. That cell becomes zero, and its required logs are undefined. | Keep $\delta<2p_{\min}$ strict. |
| Control only separate marginals | Set $S_1=S_2=X$. For $0<\rho<1$ and the supported realization $(X,T)=(0,0)$, use fair binary $X,T$ marginals with diagonal cells $(1+\rho)/4$ and off-diagonal cells $(1-\rho)/4$. Then replace $\rho$ by $-\rho$. Marginals do not change, but the pointwise redundancy changes by $\log((1+\rho)/(1-\rho))$. | Control the complete joint law. |
| Permit new support and retain a uniform linear averaged bound | Let $p(0,0,0)=1$. Let $q(0,0,0)=1-\varepsilon$ and $q(1,1,1)=\varepsilon$. Then $\lVert q-p\rVert_1=2\varepsilon$, while the averaged shared-exclusions redundancy is the binary entropy $-(1-\varepsilon)\log(1-\varepsilon)-\varepsilon\log\varepsilon$. | Require common support or use a non-linear boundary modulus. |
| Infer a population support floor from the observed minimum frequency | An unobserved positive cell has empirical frequency zero. | Use a justified external floor or a separate simultaneous lower-confidence argument. |

The executable challenge suite enumerates the finite-field pairwise-independence construction,
copied-color construction, singleton-color construction, and adaptive-color construction. It also
checks a support-deletion boundary, an unspecified-mixing construction, a generic net-weight range
extremizer, a univariate-marginal-only construction, and a new-support construction. The remaining
checks cover the telescoping allocation, class-size inequalities, high-precision one-log cases, all
displayed two-source bounds on four committed law pairs, and the fixed-window construction below.
One full-support binary pair has count vectors
$(10,100,200,10,250,10,10,10)$ and
$(1,100,200,10,250,10,10,19)$. It has
$\delta=3/100$, $\eta=3/200$, $p_{\min}=1/60$, and
$p_{\min}/(p_{\min}-\eta)=10$. Its largest observed synergy misinformative and net changes exceed
$0.97\Lambda$ and $0.95\Lambda$, respectively. This is bounded near-tightness evidence for the
one-$\Lambda$ pointwise constant. It is not a proof of global sharpness.

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

The checked Lean project has no admitted proof placeholders. The repository checker rejects such
placeholders, builds the pinned Lean project, and replays its declarations with Lean's kernel
checker.

Lean proves:

- the event-mass $\delta/2$ lemma and exact attainment by the positive-coordinate event;
- positivity under the strict support margin;
- the one-log modulus, its monotonicity, and its rational simplification;
- the centered zero-sum oscillation inequality;
- reciprocal-diameter bounds for negative-event-log, nested-log-ratio, and intersection-PMI
  gradient coordinates;
- the ordinary two-source diamond gradient diameter and the algebraic and logarithmic
  $0\le\Phi\le J$ bounds;
- the five-coordinate conditioned nested-event gradient diameter;
- both effective-color proxy inequalities and the normalized factor range;
- the generic absolute linear-row bound;
- component and net range transfer, the centered weight bounds, and the combined finite-average
  perturbation bounds;
- the factorized positive segment-event floor;
- the exact unit-scale finite telescoping allocation; and
- the algebraic radius-exponent cancellation.

Lean does not encode:

- random variables or conditional laws;
- generalized Hölder, Hoeffding, Chernoff, or the probability union bound;
- the drift result or fixed-window independence argument;
- differentiation, path integration, or the identification of event masses with the algebraic
  gradient coordinates;
- the eight-coordinate conditioned-diamond gradient bound used for two-source net synergy;
- SxPID events, the redundancy lattice, or the identification of the generic row and weighted-average
  lemmas with SxPID atoms;
- the published pointwise component-nonnegativity theorem;
- refinement between the mathematical definitions and Rust; or
- binary64 rounding.

The radius declaration, positivity conditions, square-root substitution, and its probability
interpretation remain in the prose proof.

The Python challenge suite uses exact rational arithmetic for finite probability and count
identities. It uses 100-digit Decimal arithmetic for logarithms. Transcendental logarithms are not
exact rational values. From each local count-table pair, the Rust test independently reconstructs
both empirical laws, $\delta$, $\eta$, $p_{\min}$, $\Lambda$, $L$, $h$, $J$, the atom family, and
every stored bound before it checks the implementation outputs. The test uses the scale-aware
reconstruction tolerance and the absolute categorical-output ceiling declared above. These checks
are bounded
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
