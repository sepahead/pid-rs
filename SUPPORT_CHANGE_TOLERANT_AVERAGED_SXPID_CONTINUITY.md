# Support-change-tolerant continuity for averaged categorical SxPID

Status: analytically proved exact-real project theorem; formal and executable assurance remain
partial. The result concerns the paper-defined categorical shared-exclusions PID. This document
does not define a new PID measure or estimator. It makes no scientific-priority claim.

Claim packet:
[`claims/SX-SUPPORT-FREE-CONTINUITY-001/claim-v3.md`](claims/SX-SUPPORT-FREE-CONTINUITY-001/claim-v3.md).

The main result is an explicit exact-real total-variation modulus on the closed finite probability
simplex. It permits cells to enter or leave the support. It does not require a positive minimum
cell mass. The result applies to averaged categorical cumulatives and full-lattice atoms. It does
not give pointwise continuity for a disappearing realization.

The theorem fixes:

- one finite Cartesian-product alphabet;
- one source count;
- the paper-defined shared-exclusions events;
- the full finite redundancy lattice and its Möbius inverse;
- natural-logarithm units;
- and exact real arithmetic.

The theorem does not cover a changing observed alphabet, an adaptive quantizer, continuous or mixed
variables, a binary64 error bound, or estimator calibration.

## 1. Fixed finite setting

Let the source and target alphabets below be finite and nonempty, and let

$$
\mathcal Z
=
\mathcal S_1\times\cdots\times\mathcal S_m\times\mathcal T
$$

be their fixed Cartesian-product alphabet of size $K$. Let $p$ and $q$ be probability laws on all of
$\mathcal Z$, including zero-mass cells. Put

$$
\eta
=d_{\mathrm{TV}}(p,q)
=\frac12\lVert p-q\rVert_1.
$$

For any law functional $F$, write

$$
\Delta F=F(p)-F(q).
$$

Define the pointwise overlap and residuals

$$
r_z=\min\{p_z,q_z\},
\qquad
a_z=p_z-r_z,
\qquad
b_z=q_z-r_z.
$$

Then

$$
p=r+a,\qquad q=r+b,
$$

$$
\sum_z a_z=\sum_z b_z=\eta,
\qquad
\sum_zr_z=1-\eta=:R,
$$

and $a_zb_z=0$ for every $z$.

For a nonnegative vector $d$, use the continuous zero convention

$$
E(d)=-\sum_{z:d_z>0}d_z\log d_z.
$$

Write

$$
E_\vee=\max\{E(a),E(b)\},
\qquad
E_\Sigma=E(a)+E(b).
$$

These are entropies of subprobability residuals. They are not Shannon entropies of normalized laws.

## 2. A generic anchored-neighborhood theorem

Let $X$ be a finite set and, independently of Section 1, let $p$ and $q$ be probability laws on
$X$. Redefine $\eta$, $R$, $r$, $a$, $b$, $E_\vee$, and $E_\Sigma$ on $X$ by the formulas in
Section 1. Fix a neighborhood $N_x\subseteq X$ for every $x\in X$, and assume the anchor condition

$$
x\in N_x.
$$

For a nonnegative vector $v$, write

$$
v(N_x)=\sum_{y\in N_x}v_y.
$$

For a probability law $p$, define the support-restricted functional

$$
G_N(p)
=-\sum_{x:p_x>0}p_x\log p(N_x).
\tag{1}
$$

The anchor condition makes every logarithm in Equation (1) well-defined.

For $R>0$, define the overlap load

$$
T_N(r,d)
=
\sum_{x:r_x>0}
r_x\frac{d(N_x)}{r(N_x)}.
\tag{2}
$$

When $R=0$, define the common-overlap term below to be zero.

### Theorem 1: residual-plus-load bound

For any two laws $p,q$,

$$
\left|G_N(p)-G_N(q)\right|
\le
E_\vee
+
R\log\left(
1+\frac{\max\{T_N(r,a),T_N(r,b)\}}{R}
\right),
\tag{3}
$$

with the second term defined as zero when $R=0$.

#### Proof

Direct substitution gives the exact decomposition

$$
G_N(p)-G_N(q)
=C_N+U_{p,a}-U_{q,b},
\tag{4}
$$

where

$$
C_N
=
\sum_{x:r_x>0}
r_x\log\frac{r(N_x)+b(N_x)}{r(N_x)+a(N_x)},
\tag{5}
$$

$$
U_{p,a}
=-\sum_{x:a_x>0}a_x\log p(N_x),
\qquad
U_{q,b}
=-\sum_{x:b_x>0}b_x\log q(N_x).
\tag{6}
$$

Reflexivity gives

$$
a_x\le p(N_x)\le1,
\qquad
b_x\le q(N_x)\le1.
$$

Therefore

$$
0\le U_{p,a}\le E(a),
\qquad
0\le U_{q,b}\le E(b),
\tag{7}
$$

and

$$
|U_{p,a}-U_{q,b}|\le E_\vee.
\tag{8}
$$

For a residual $d\in\{a,b\}$, define

$$
C_N(d)
=
\sum_{x:r_x>0}
r_x\log\left(1+\frac{d(N_x)}{r(N_x)}\right).
$$

Then $C_N=C_N(b)-C_N(a)$, both terms are nonnegative, and hence

$$
|C_N|\le\max\{C_N(a),C_N(b)\}.
$$

Jensen's inequality with weights $r_x/R$ gives

$$
C_N(d)
\le
R\log\left(1+\frac{T_N(r,d)}R\right).
\tag{9}
$$

Equations (8) and (9) prove Equation (3). At $R=0$, the common sum is empty. At $\eta=0$,
both residuals vanish. These arguments cover both endpoints.

## 3. Unions of equivalence neighborhoods

Fix an integer $J\ge1$ and assume that

$$
N_x=\bigcup_{j=1}^{J}[x]_j,
\tag{10}
$$

where, for each $j$, $[x]_j$ is the equivalence class of $x$ under a fixed relation
$\sim_j$. The $J$ relations may differ.

### Lemma 2: fractional-cover load

For every nonnegative residual $d$ with total mass $\eta$,

$$
T_N(r,d)\le J\eta.
\tag{11}
$$

#### Proof

Use the union bound in the numerator and one branch in the denominator:

$$
\frac{d(N_x)}{r(N_x)}
\le
\sum_{j=1}^{J}\frac{d([x]_j)}{r([x]_j)}
$$

for every $x$ with $r_x>0$. For a fixed $j$, group $x$ by its equivalence class $D$.
Every class with positive overlap contributes

$$
\sum_{x\in D}r_x\frac{d(D)}{r(D)}=d(D).
$$

Summing the positive-overlap classes gives at most $\eta$; a class with no overlap has no
anchored $x$ in the defining sum and need not contribute its residual mass. Summing the $J$
relations gives Equation (11).

Define

$$
g_J(\eta)
=
\begin{cases}
(1-\eta)
\log\left(1+\dfrac{J\eta}{1-\eta}\right),
&0<\eta<1,\\
0,&\eta\in\{0,1\}.
\end{cases}
\tag{12}
$$

Theorem 1 and Lemma 2 give

$$
|G_N(p)-G_N(q)|
\le E_\vee+g_J(\eta).
\tag{13}
$$

Also,

$$
g_J(\eta)\le J\eta.
\tag{14}
$$

Equation (14) follows from $\log(1+x)\le x$. The exact function $g_J$ is not monotone on all of
$[0,1]$. Equation (14), not blind substitution into Equation (12), is the safe route when only
an upper bound on $\eta$ is known.

### Equality witness

The coefficient in Equation (12) is exact for this decomposition. Fix $J$ sources and states

$$
z,\quad c,\quad \ell_1,\ldots,\ell_J.
$$

For source $j$, let $c$ and $\ell_j$ share one categorical value. Give every other
state-coordinate pair a distinct value. For the antichain

$$
\{\{1\},\ldots,\{J\}\},
$$

the source-union neighborhoods satisfy

$$
N_{\ell_j}=\{\ell_j,c\},
\qquad
N_z=\{z\},
\qquad
N_c=\{c,\ell_1,\ldots,\ell_J\}.
$$

Let the target be constant and set

$$
r_{\ell_j}=\frac{1-\eta}{J},
\qquad
a_z=\eta,
\qquad
b_c=\eta.
$$

Then

$$
G_N(p)-G_N(q)
=
E(a)+g_J(\eta).
\tag{15}
$$

Thus the residual term and the $J\eta$ load can be attained simultaneously by a paper-semantic
categorical Sx event.

## 4. Paper-defined shared-exclusions events

Specialize the generic finite set to $X=\mathcal Z$.

Let $\beta$ be one node of the full finite redundancy lattice. For every ambient key
$z=(s_1,\ldots,s_m,t)\in\mathcal Z$, define

$$
A_\beta(z)
=
\bigcup_{u\in\beta}
\{y:y_u=s_u\},
\tag{16}
$$

$$
C(z)=\{y:y_T=t\},
\qquad
B_\beta(z)=A_\beta(z)\cap C(z).
\tag{17}
$$

These are the finite-alphabet event semantics of Makkeh, Gutknecht, and Wibral, Equations
(15a)--(15b) and Appendix B. The present notation makes the law-independent keyed event map
explicit; it does not alter the paper-defined functional.

If $J_\beta=|\beta|$, then $A_\beta$ and $B_\beta$ are unions of $J_\beta$ equivalence
neighborhoods. The target event $C$ is one equivalence neighborhood.

The event map is therefore fixed on the complete alphabet, independently of the law. Local
logarithms and averages below evaluate these events only at positive-mass keys.

The averaged informative, misinformative, and net cumulatives can be written as

$$
I_\beta^+(p)=G_{A_\beta}(p),
\tag{18}
$$

$$
I_\beta^-(p)=G_{B_\beta}(p)-G_C(p),
\tag{19}
$$

$$
I_\beta^{\mathrm{net}}(p)
=G_{A_\beta}(p)-G_{B_\beta}(p)+G_C(p).
\tag{20}
$$

These identities use support-restricted sums. They do not evaluate a local logarithm at a
zero-mass key.

### Theorem 3: cumulative bounds

For every full-lattice node $\beta$,

$$
|\Delta I_\beta^+|
\le E_\vee+g_{J_\beta}(\eta),
\tag{21}
$$

$$
|\Delta I_\beta^-|
\le E_\vee+g_{J_\beta}(\eta)+g_1(\eta),
\tag{22}
$$

$$
|\Delta I_\beta^{\mathrm{net}}|
\le E_\Sigma+2g_{J_\beta}(\eta)+g_1(\eta).
\tag{23}
$$

#### Why Equation (22) has only one residual entropy

For a supported key,

$$
0\le c_\beta^-(z;p)\le-\log p_z.
$$

Indeed, $z\in B_\beta(z)\subseteq C(z)$ and $z\in A_\beta(z)$, so every keyed event
probability is at least $p_z$, while all event probabilities are at most one.

The $p$-residual average of $c_\beta^-$ lies in $[0,E(a)]$, and the $q$-residual average
lies in $[0,E(b)]$. Their difference is bounded by $E_\vee$. Separately bounding
$G_{B_\beta}$ and $G_C$ would lose this cancellation and produce an unnecessary second
residual entropy.

#### Why Equation (23) needs two residual entropies

For a supported key,

$$
|c_\beta^{\mathrm{net}}(z;p)|\le-\log p_z.
$$

The two endpoint residual averages are signed. Their difference is bounded by
$E(a)+E(b)$, not by their maximum. Section 9 gives an exact Sx-realizable counterexample to the
maximum-residual shortcut.

## 5. Transfer to full-lattice atoms

Let $M$ be the fixed Möbius inverse in the orientation

$$
\Pi_\alpha^u
=
\sum_\beta M_{\alpha\beta}I_\beta^u.
\tag{24}
$$

Define

$$
W_\alpha(\eta)
=
\sum_\beta
|M_{\alpha\beta}|g_{J_\beta}(\eta),
\tag{25}
$$

and the row sum

$$
s_\alpha=\sum_\beta M_{\alpha\beta}.
\tag{26}
$$

The full finite redundancy lattice has one least node $\bot$. Its down-set zeta matrix $Z$
satisfies

$$
Z e_\bot=\mathbf 1.
$$

Therefore

$$
M\mathbf 1=e_\bot,
\qquad
s_\alpha=\mathbf 1\{\alpha=\bot\}.
\tag{27}
$$

This identity need not hold for a truncated family without a least node.

The defining paper's Equation (19), Möbius inversion, and Theorem IV.3 prove pointwise
nonnegativity of the informative and misinformative component atoms on the full lattice:

$$
\pi_\alpha^+(z;p)\ge0,
\qquad
\pi_\alpha^-(z;p)\ge0.
\tag{28}
$$

All component atoms reconstruct the greatest-node cumulative. At that node, for a supported key
$z=(s,t)$,

$$
c_\top^+(z;p)=-\log p(S=s)\le-\log p_z,
\qquad
c_\top^-(z;p)=-\log p(S=s\mid T=t)\le-\log p_z.
$$

Consequently, for every atom,

$$
0\le\pi_\alpha^+(z;p)\le-\log p_z,
\qquad
0\le\pi_\alpha^-(z;p)\le-\log p_z.
\tag{29}
$$

Equation (29) is the sign-sharpening step. Averaged nonnegativity alone is not enough.

### Theorem 4: atom bounds

For every atom $\alpha$ of the full finite redundancy lattice,

$$
|\Delta\Pi_\alpha^+|
\le E_\vee+W_\alpha(\eta),
\tag{30}
$$

$$
|\Delta\Pi_\alpha^-|
\le E_\vee+W_\alpha(\eta)+|s_\alpha|g_1(\eta),
\tag{31}
$$

$$
|\Delta\Pi_\alpha^{\mathrm{net}}|
\le E_\Sigma+2W_\alpha(\eta)+|s_\alpha|g_1(\eta).
\tag{32}
$$

#### Proof

Split each averaged atom into overlap, left-residual, and right-residual weighted pointwise atoms.
For the overlap term, commute the fixed finite Möbius matrix with the finite weighted sum. Apply
the common-overlap bounds to every $A_\beta$, $B_\beta$, and $C$ term. Equation (27) gives
the target-event coefficient.

For the residual terms, Equations (28) and (29) place each component residual average in
$[0,E(a)]$ or $[0,E(b)]$. Their difference is bounded by $E_\vee$. For the net atom,

$$
\pi_\alpha^{\mathrm{net}}
=\pi_\alpha^+-\pi_\alpha^-,
$$

so

$$
|\pi_\alpha^{\mathrm{net}}(z;p)|
\le-\log p_z.
$$

The two signed residual averages require $E_\Sigma$. This proves Equations (30)--(32).

## 6. Alphabet-only entropy envelopes

Assume $\eta>0$. Let

$$
k_a=|\mathrm{supp}\,a|,
\qquad
k_b=|\mathrm{supp}\,b|.
$$

The residual supports are disjoint, so

$$
k_a+k_b\le K.
$$

Concavity of $-x\log x$ gives

$$
E(a)\le\eta\log\frac{k_a}{\eta},
\qquad
E(b)\le\eta\log\frac{k_b}{\eta}.
$$

Consequently,

$$
E_\vee
\le
e_K^\vee(\eta)
:=
\eta\log\frac{K-1}{\eta},
\tag{33}
$$

and

$$
E_\Sigma
\le
e_K^\Sigma(\eta)
:=
\eta\log\frac{\lfloor K^2/4\rfloor}{\eta^2}.
\tag{34}
$$

Define both envelopes as zero at $\eta=0$. If $K=1$, then $\eta=0$. The support-size
constants in Equations (33) and (34) are exact: one residual can occupy $K-1$ cells, and the
product $k_ak_b$ is largest at a balanced split.

Substituting Equations (33) and (34) into Theorems 3 and 4 gives moduli that depend only on:

- the fixed alphabet size $K$;
- the total variation $\eta$;
- the branch counts $J_\beta$;
- and the fixed Möbius matrix.

Every term tends to zero with $\eta$. Therefore all averaged categorical Sx cumulatives and
full-lattice atoms are uniformly continuous on the closed finite simplex, including across support
changes.

## 7. Range caps

Let

$$
K_S=\prod_{i=1}^{m}|\mathcal S_i|
$$

be the joint source-alphabet size. For every node,

$$
0\le I_\beta^+(p)\le H_p(S)\le\log K_S,
$$

$$
0\le I_\beta^-(p)\le H_p(S\mid T)\le\log K_S.
$$

The same upper bounds hold for each averaged informative or misinformative atom because the
component atoms are nonnegative and sum to the greatest-node component cumulative. Thus any
component difference can also be capped by $\log K_S$, and any net difference can be capped by
$2\log K_S$.

These caps are exact range statements. They are not floating-point error bounds.

## 8. Composition with a law-distance confidence radius

The exact functions in Equations (12), (33), and (34) are not all monotone on $[0,1]$. If a
statistical theorem supplies only

$$
\eta\le\varepsilon,
$$

do not replace $\eta$ by $\varepsilon$ in the exact formulas without a monotonicity proof.

For $K\ge2$, define the monotone upper envelopes

$$
\bar e_K^\vee(\varepsilon)
=
\varepsilon\left[
1+\log\frac{K-1}{\varepsilon}
\right],
\tag{35}
$$

$$
\bar e_K^\Sigma(\varepsilon)
=
\varepsilon\left[
2+\log\frac{\lfloor K^2/4\rfloor}{\varepsilon^2}
\right],
\tag{36}
$$

with value zero at $\varepsilon=0$. For $0\le\eta\le\varepsilon\le1$,

$$
E_\vee\le\bar e_K^\vee(\varepsilon),
\qquad
E_\Sigma\le\bar e_K^\Sigma(\varepsilon),
\qquad
g_J(\eta)\le J\varepsilon.
\tag{37}
$$

To verify the first two inequalities, put
$A=K-1\ge1$ and $B=\lfloor K^2/4\rfloor\ge1$. For
$0<\eta\le\varepsilon$, both $\log(A/\varepsilon)$ and
$\log(B/\varepsilon^2)$ are nonnegative, while

$$
\eta\log\frac{\varepsilon}{\eta}
=
\varepsilon
\left(\frac{\eta}{\varepsilon}\right)
\log\left(\frac{\varepsilon}{\eta}\right)
\le\frac{\varepsilon}{e}
\le\varepsilon.
$$

Therefore

$$
\eta\log\frac{A}{\eta}
\le
\varepsilon\log\frac{A}{\varepsilon}+\varepsilon,
$$

and

$$
\eta\log\frac{B}{\eta^2}
\le
\varepsilon\log\frac{B}{\varepsilon^2}+2\varepsilon.
$$

The endpoint $\eta=0$ follows by the zero convention. The last inequality in Equation (37)
follows from $g_J(\eta)\le J\eta\le J\varepsilon$.

Put

$$
L_\alpha=\sum_\beta|M_{\alpha\beta}|J_\beta.
\tag{38}
$$

On any event where $d_{\mathrm{TV}}(\widehat p,p)\le\varepsilon$, the following simultaneous
deterministic transfers hold:

In the table, both barred entropy envelopes are evaluated at $\varepsilon$.

| Quantity | Support-change-tolerant radius |
|---|---:|
| $I_\beta^+$ | $\bar e_K^\vee+J_\beta\varepsilon$ |
| $I_\beta^-$ | $\bar e_K^\vee+(J_\beta+1)\varepsilon$ |
| $I_\beta^{\mathrm{net}}$ | $\bar e_K^\Sigma+(2J_\beta+1)\varepsilon$ |
| $\Pi_\alpha^+$ | $\bar e_K^\vee+L_\alpha\varepsilon$ |
| $\Pi_\alpha^-$ | $\bar e_K^\vee+(L_\alpha+\lvert s_\alpha\rvert)\varepsilon$ |
| $\Pi_\alpha^{\mathrm{net}}$ | $\bar e_K^\Sigma+(2L_\alpha+\lvert s_\alpha\rvert)\varepsilon$ |

Each component row can be capped by $\log K_S$. Each net row can be capped by
$2\log K_S$.

The dependency-colored law theorem in
[`DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md)
supplies an $L^1$ radius $D_n$ under its declared mutual-within-color independence contract.
Set

$$
\varepsilon_n=D_n/2.
$$

The table then gives a finite-sample averaged categorical SxPID transfer with no population
support-mass floor. It does not validate the coloring from data. It does not remove the
exponential alphabet factor in the law-distance bound.

For a nonidentical-law result centered at an average law $\bar p_n$, let

$$
b_n=\lVert\bar p_n-p_\star\rVert_1.
$$

If the random $L^1$ radius is $D_n$, use

$$
\varepsilon_n
=
\min\left\{1,\frac{D_n+b_n}{2}\right\}.
$$

This separates random law error from the declared drift bias. An unknown $b_n$ remains an
unknown scientific bias.

## 9. Exact negative results and scope guards

### 9.1 No global linear modulus and no pointwise boundary theorem

Let $S_2$ be constant and $T=S_1$. Compare a binary copied source with rare probability
$\eta$ against the point mass obtained at $\eta=0$. The averaged unique-$S_1$ informative and
net atom equals

$$
h_2(\eta)
=-\eta\log\eta-(1-\eta)\log(1-\eta).
$$

The two-source bottom event is the whole sample space because the $S_2$ branch is constant, so its
local cumulative is zero. Möbius inversion therefore makes the unique-$S_1$ atom equal to the
$S_1$-node cumulative. The node's net local value is pointwise mutual information, which reduces
to source surprisal when $T=S_1$; its averaged cumulative is $I(S_1;T)$.

The $L^1$ law distance is $2\eta$, so

$$
\frac{h_2(\eta)}{2\eta}\longrightarrow\infty.
$$

The rare-key pointwise atom is $-\log\eta$. Thus:

- no global $C\lVert p-q\rVert_1$ modulus exists;
- the $\eta\log(1/\eta)$ order is necessary;
- and pointwise support-boundary continuity is false.

### 9.2 An active-face Fannes--Audenaert substitution is false

Use three sources, a constant target, the singleton antichain

$$
\{\{1\},\{2\},\{3\}\},
$$

and source states

$$
000,\quad011,\quad202,\quad330,\quad444.
$$

The first state is the center, the next three are leaves, and the last state is an isolated donor.
Set

$$
p=(0,3/10,3/10,3/10,1/10),
$$

$$
q=(1/10,3/10,3/10,3/10,0).
$$

Then $\eta=1/10$ and

$$
|G_N(p)-G_N(q)|
=
\frac1{10}\log10+\frac9{10}\log\frac43.
\tag{39}
$$

Here the union-support face has

$$
K_\cup
=
|\mathrm{supp}\,p\cup\mathrm{supp}\,q|
=5.
$$

The ordinary Fannes--Audenaert entropy radius on that five-state face is

$$
h_2(1/10)+\frac1{10}\log4.
$$

It is smaller. The exact excess is

$$
\frac9{10}\log\frac65-\frac1{10}\log4>0,
$$

equivalently

$$
6^9>4\cdot5^9.
$$

This example is an actual categorical Sx event. It rejects substituting the ordinary entropy
continuity radius computed on the union-support face for the neighborhood-functional bound, and it
attains the residual-plus-$g_3$ bound exactly. It does not say that a Fannes expression formed with
a larger ambient Cartesian-product cardinality must fail. With a constant target, the informative
and misinformative bottom atoms coincide and the net atom is zero.

A bounded search found no four-state counterexample. That non-finding does not prove that five
states are globally minimal.

### 9.3 The net residual maximum shortcut is false

Set $\eta\in(0,1)$ and $R=1-\eta$. Keep $S_2$ constant. Define laws on the displayed
$(S_1,T)$ cells:

$$
p(0,0)=\eta,
\qquad
p(1,2)=p(2,1)=R/2,
$$

$$
q(1,1)=\eta,
\qquad
q(1,2)=q(2,1)=R/2.
$$

As above, the constant-$S_2$ branch makes the bottom net cumulative zero, so the two-source
Möbius inversion identifies the unique-$S_1$ net atom with the $S_1$-node cumulative. The node's
local value is pointwise mutual information, while its averaged cumulative is $I(S_1;T)$. The
difference between its two residual-weighted contributions is

$$
2\eta\log\frac{1+\eta}{2\eta}.
\tag{40}
$$

For every $0<\eta<1$,

$$
2\eta\log\frac{1+\eta}{2\eta}
>
\eta\log\frac1\eta.
$$

After exponentiation, the strict inequality reduces to

$$
(1-\eta)^2>0.
$$

Thus the two signed residual budgets cannot be replaced by $E_\vee$ in this proof. This example
does not prove global sharpness of the complete net-atom modulus.

### 9.4 Full-lattice scope is necessary

On a three-element V-shaped poset with two incomparable minimal nodes and one greatest node,
constant cumulatives $c=(1,1,1)$ invert to atoms

$$
\pi=(1,1,-1).
$$

The greatest-row Möbius sum is $-1$. Therefore Equation (27) and component nonnegativity do not
extend to an arbitrary truncated family without a least node.

### 9.5 No alphabet-free modulus

Move total mass $\eta$ from one cell and spread it uniformly over an increasing number of new
cells in a copied-source construction. The averaged unique component contains

$$
\eta\log M
$$

when the new residual uses $M$ cells. No modulus independent of the fixed ambient alphabet can
hold.

### 9.6 The leading logarithmic coefficients are worst-case optimal

For fixed $K\ge2$, the upper entropy bounds have the small-distance forms

$$
e_K^\vee(\eta)
=
\eta\log\frac1\eta+O(\eta),
\qquad
e_K^\Sigma(\eta)
=
2\eta\log\frac1\eta+O(\eta),
\tag{41}
$$

Every $g_J(\eta)$ term is $O(\eta)$ for fixed $J$. Therefore every $W_\alpha$ and
row-sum-weighted $g_1$ term is $O(\eta)$ when the finite lattice, Möbius matrix, and branch counts
are fixed.

The copied-source path in Section 9.1 gives

$$
\lim_{\eta\downarrow0}
\frac{h_2(\eta)}
{\eta\log(1/\eta)}
=1.
\tag{42}
$$

This exhibits one fixed finite system and one fixed atom whose informative component has leading
coefficient one. Consider any family of fixed-system component bounds of the form

$$
c\,\eta\log(1/\eta)+O_{\mathcal F}(\eta),
$$

where the lower-order constant may depend on the fixed system $\mathcal F$, but $c$ is common to
the family. The witness forces $c\ge1$. The constant-target equality witness from Section 3 has
identical informative and misinformative component atoms at the bottom node and gives the same
worst-case lower coefficient for the misinformative family. This is not a claim that every system
or atom attains the coefficient.

For the fixed two-source system in Section 9.3, the complete unique-$S_1$ net atom is the mutual
information $I(S_1;T)$. With $R=1-\eta$, direct evaluation gives

$$
I_p(S_1;T)
=
-\eta\log\eta-R\log\frac{R}{2},
$$

and

$$
I_q(S_1;T)
=
\eta\log\frac{4\eta}{(1+\eta)^2}
+
R\log\frac{2}{1+\eta}.
$$

Subtracting gives

$$
\begin{aligned}
\left|
\Pi_{U_1}^{\mathrm{net}}(p)
-
\Pi_{U_1}^{\mathrm{net}}(q)
\right|
&=
2\eta\log\frac{1+\eta}{2\eta}
\\
&\quad+
(1-\eta)\log\frac{1+\eta}{1-\eta}.
\end{aligned}
\tag{43}
$$

Both terms are positive for $0<\eta<1$, and

$$
\lim_{\eta\downarrow0}
\frac{
\left|
\Pi_{U_1}^{\mathrm{net}}(p)
-
\Pi_{U_1}^{\mathrm{net}}(q)
\right|
}{
\eta\log(1/\eta)
}
=2.
\tag{44}
$$

This exhibits one fixed finite system and one fixed net atom with leading coefficient two.
Therefore any family of fixed-system net bounds

$$
c\,\eta\log(1/\eta)+O_{\mathcal F}(\eta)
$$

with a common leading coefficient must have $c\ge2$. Equations (42) and (44) establish worst-case
leading-order optimality only. They do not claim that every system or atom attains these
coefficients, or prove that the $O_{\mathcal F}(\eta)$ constants, branch terms, or every individual
modulus in Theorems 3 and 4 are globally sharp.

## 10. Evidence boundary

The result uses several evidence layers. They must not be merged into one claim.

| Layer | What it can establish | What remains outside it |
|---|---|---|
| Primary papers | Sx event semantics, full lattice, pointwise component signs | The support-change theorem |
| Exact prose proof | Theorems 1--4 and their finite-alphabet corollaries | Complete machine-checked Sx, lattice, and averaging composition |
| Lean | Finite-vector overlap, residual, entropy, and transfer lemmas; exact heterogeneous keyed Sx events; the finite equivalence-union load bound and its $A_\beta$, $B_\beta$, and $C$ corollaries; a generic row-sum lemma; and scalar endpoint bounds | The logarithmic transfer from the finite load to $g_J$; bundled probability and total-variation semantics; the concrete full lattice and published sign theorem; averaged Sx cumulatives and atoms; and Rust |
| Exact and high-precision generator | Fixed counterexamples, equality witnesses, and a bounded seeded challenge corpus | Universal proof, the historical grid searches, or interval certification |
| Rust comparison | Conformance on committed count tables | General refinement or binary64 enclosure |
| Dependency-colored probability theorem | A law-distance event under a declared color contract | Validation of that contract or repeated-alert calibration |

No current layer proves:

- a portable correctly rounded `f64` logarithm;
- a certified sign for an atom whose interval would contain zero;
- a general consistency theorem for continuous PID2;
- a valid full continuous PID3 estimator;
- or consumer authority for an alert or action.

## 11. References

1. Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral. “Introducing a differentiable measure
   of pointwise shared information.” *Physical Review E* 103, 032149 (2021).
   <https://doi.org/10.1103/PhysRevE.103.032149>
2. Aaron J. Gutknecht, Michael Wibral, and Abdullah Makkeh. “Bits and pieces: understanding
   information decomposition from part-whole relationships and formal logic.”
   *Proceedings of the Royal Society A* 477, 20210110 (2021).
   <https://doi.org/10.1098/rspa.2021.0110>
3. Koenraad M. R. Audenaert. “A sharp continuity estimate for the von Neumann entropy.”
   *Journal of Physics A* 40, 8127--8136 (2007).
   <https://doi.org/10.1088/1751-8113/40/28/S18>
