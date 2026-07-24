# Conventions for SX-SUPPORT-FREE-CONTINUITY-001

## Ambient alphabet and laws

Let the source and target alphabets below be finite and nonempty, and let

$$
\mathcal Z
=
\mathcal S_1\times\cdots\times\mathcal S_n\times\mathcal T
$$

be their fixed finite Cartesian product. A law $P$ is a probability vector on all of
$\mathcal Z$, including zero-mass cells. Its support is

$$
\mathrm{supp}\,P=\{z\in\mathcal Z:P(z)>0\}.
$$

The theorem does not replace $\mathcal Z$ by the observed support. The same alphabet is used for
both laws in every comparison.

For two laws $P,Q$, use

$$
\eta=d_{\mathrm{TV}}(P,Q)
=\frac12\lVert P-Q\rVert_1.
$$

Every bound must state whether it uses $\eta$ or $\lVert P-Q\rVert_1$.

## Full finite redundancy lattice

Write $[n]=\{1,\ldots,n\}$ and
$\mathcal P_+([n])=\{a\subseteq[n]:a\neq\varnothing\}$.
The lattice $\mathcal A_n$ contains every nonempty antichain of
$\mathcal P_+([n])$.

Use the Williams--Beer order

$$
\alpha\preceq\beta
\quad\Longleftrightarrow\quad
\forall b\in\beta\;\exists a\in\alpha:\;a\subseteq b.
$$

Thus, for two sources, the least node is
$\{\{1\},\{2\}\}$ and the greatest node is $\{\{1,2\}\}$.
The lattice has 4, 18, and 166 nodes for 2, 3, and 4 sources.

The primary papers call this a lattice. The phrase “full finite redundancy lattice” is preferred.
It is complete in the order-theoretic sense because it is finite, but that wording is a derived
mathematical observation and not a quoted source claim.

## Keyed shared-exclusions event

Let $z=(s_1,\ldots,s_n,t)\in\mathrm{supp}\,P$. For a nonempty source collection
$a\subseteq[n]$, define

$$
E_a(s)=\bigcap_{i\in a}\{S_i=s_i\}.
$$

For $\alpha=\{a_1,\ldots,a_m\}\in\mathcal A_n$, define

$$
E_\alpha(s)=\bigcup_{j=1}^m E_{a_j}(s).
$$

This union of conjunctions is the paper-defined logical disjunction. It must not be replaced by an
intersection of branches.

Let $C_t=\{T=t\}$ and $B_\alpha(z)=C_t\cap E_\alpha(s)$. Since $z$ is a positive-mass keyed
realization,

$$
P(E_\alpha(s))\geq P(z)>0,\quad
P(C_t)\geq P(z)>0,\quad
P(B_\alpha(z))\geq P(z)>0.
$$

All local logarithms are therefore defined at every key that appears in the average.

## Local cumulatives

Use natural logarithms:

$$
c_\alpha^+(z;P)=-\log P(E_\alpha(s)),
$$

$$
c_\alpha^-(z;P)
=
\log\frac{P(C_t)}{P(B_\alpha(z))},
$$

$$
c_\alpha^{\mathrm{net}}(z;P)
=c_\alpha^+(z;P)-c_\alpha^-(z;P).
$$

Makkeh, Gutknecht, and Wibral state the defining formulas in bits. Multiplication by
$\ln 2>0$ converts bits to nats and preserves all signs and lattice identities.

## Pointwise atoms and Möbius orientation

For $u\in\{+,-,\mathrm{net}\}$, define the pointwise atoms by

$$
c_\alpha^u(z;P)
=
\sum_{\beta\preceq\alpha}\pi_\beta^u(z;P).
$$

The fixed Möbius inverse is the inverse of this down-set zeta relation. The informative and
misinformative families are inverted separately. The net family satisfies

$$
\pi_\alpha^{\mathrm{net}}
=
\pi_\alpha^+-\pi_\alpha^-.
$$

The published nonnegativity theorem applies to the paper-defined full lattice and gives

$$
\pi_\alpha^+(z;P)\geq0,\qquad
\pi_\alpha^-(z;P)\geq0.
$$

It does not give $\pi_\alpha^{\mathrm{net}}\geq0$. It also does not establish nonnegativity for an
arbitrary matrix, a truncated lattice, or a different PID definition.

## Averaging and the boundary

Define averaged quantities by support-restricted finite sums:

$$
C_\alpha^u(P)
=
\sum_{z\in\mathrm{supp}\,P}P(z)c_\alpha^u(z;P),
$$

$$
\Pi_\alpha^u(P)
=
\sum_{z\in\mathrm{supp}\,P}P(z)\pi_\alpha^u(z;P).
$$

This is the boundary convention. A zero-mass key is omitted. The packet does not assign a finite
local value to that key and does not use $0\cdot\infty$.

An equivalent fixed-alphabet totalization is permitted only after a proof defines every zero-weight
summand and proves equality with the support-restricted sum.

The primary workflow is pointwise inversion followed by averaging. Inversion of the averaged
cumulatives is equivalent only after using the fixed finite matrix and proving that finite linear
maps commute with the average.

## Scope exclusions

These conventions do not cover:

- a changing or observed-only alphabet;
- a changing, truncated, or data-selected lattice;
- a quantizer fitted on the same evaluation rows;
- a changing fitted transform;
- continuous or mixed-variable shared exclusions;
- a sample concentration statement;
- binary64 evaluation or certified numerical intervals.
