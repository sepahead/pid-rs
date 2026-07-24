# Numerical attack route memo

## Route record

| Field | Value |
|---|---|
| Route ID | `SX-SUPPORT-FREE-CONTINUITY-001-NUMERICAL-01` |
| Claim revision | 1 |
| Date | 2026-07-24 |
| Route class | Independent prototype, exact combinatorics, and numerical attack |
| Imported project estimator code | None |
| Arithmetic | Integer and rational combinatorics; 100-digit `Decimal` logarithms |
| Route status | Entropy-only bound rejected; candidate residual and overlap bounds survived the tested domains |
| Final-proof status | Open |

This route is retrospective. It was not preregistered. The prototype does not import `pid-rs`.
That separation reduces shared implementation risk. It does not make the route an independent
final audit. The open status records this historical revision-1 checkpoint; revision 2 was
adjudicated later from the exact analytic proof and its separately scoped evidence.

## Objects under attack

For a finite keyed-cell system with reflexive neighborhoods
$\mathcal N=(N_x)_{x=1}^K$, define

$$
G_{\mathcal N}(P)
=
-\sum_{x:P_x>0}P_x\log P(N_x).
$$

Here $K$ is the number of keyed rows in the reduced test system. It is not the source count. It
also need not equal the cardinality of a larger ambient Cartesian product.

The rejected entropy-only candidate was the direct transfer of the clipped Fannes expression

$$
F_K(\eta)
=
\begin{cases}
h_2(\eta)+\eta\log(K-1),&0\leq\eta\leq1-1/K,\\
\log K,&1-1/K<\eta\leq1.
\end{cases}
$$

For two laws $P,Q$, define

$$
r_x=\min\{P_x,Q_x\},\qquad
a=P-r,\qquad
b=Q-r,
$$

and

$$
\eta=\sum_xa_x=\sum_xb_x=d_{\mathrm{TV}}(P,Q),\qquad
t=1-\eta.
$$

The residual subprobability entropies are

$$
E_a=-\sum_xa_x\log a_x,\qquad
E_b=-\sum_xb_x\log b_x,\qquad
E_{\max}=\max\{E_a,E_b\}.
$$

Use the zero convention $0\log0=0$. Also define

$$
\ell(\eta)=-t\log t
$$

and, for a union of $J$ equivalence-relation branches,

$$
\gamma_J(\eta)
=
t\log\left(1+\frac{J\eta}{t}\right).
$$

The endpoint value is $\gamma_J(1)=0$. The route derived the fractional-cover bound

$$
\gamma_J(\eta)\leq J\ell(\eta).
$$

For a general neighborhood system, define the residual load

$$
L_{\mathcal N}(a)=\sum_x a(N_x)
$$

and the load budget

$$
\gamma_{\mathcal N}(a)
=
t\log\left(1+\frac{L_{\mathcal N}(a)}{t}\right).
$$

Use $\gamma_{\mathcal N}(a)=0$ at $\eta=1$.

The prototype used the smallest available overlap budget among the actual-load budget,
$\gamma_J$, and $J\ell$. Write the resulting source-event and target-intersection budgets as
$g_A$ and $g_B$.

## Candidate bounds that survived this route

These are candidate theorem formulas. A bounded numerical route does not prove them.

For an averaged cumulative, the tested direct bounds were

$$
|\Delta C_\alpha^+|
\leq E_{\max}+g_A,
$$

$$
|\Delta C_\alpha^-|
\leq E_{\max}+g_B+\ell,
$$

and

$$
|\Delta C_\alpha^{\mathrm{net}}|
\leq E_a+E_b+g_A+g_B+\ell.
$$

Let $M$ be the fixed Möbius matrix. For row $\alpha$, let

$$
s_\alpha=\sum_\beta M_{\alpha\beta}.
$$

The tested atom bounds were

$$
|\Delta\Pi_\alpha^+|
\leq
E_{\max}
+
\sum_\beta |M_{\alpha\beta}|g_{A,\beta},
$$

$$
|\Delta\Pi_\alpha^-|
\leq
E_{\max}
+
\sum_\beta |M_{\alpha\beta}|g_{B,\beta}
+
|s_\alpha|\ell,
$$

and

$$
|\Delta\Pi_\alpha^{\mathrm{net}}|
\leq
E_a+E_b
+
\sum_\beta |M_{\alpha\beta}|
\left(g_{A,\beta}+g_{B,\beta}\right)
+
|s_\alpha|\ell.
$$

For the full lattices with two, three, and four sources, the exact matrix calculation gave

$$
M\mathbf 1=e_{\mathrm{bottom}}.
$$

Thus, one row sum is one and every other row sum is zero.

| Sources | Nodes | Row $\ell_1$-norm histogram | Maximum row norm | Positive / negative entries |
|---:|---:|---|---:|---:|
| 2 | 4 | $1:1,\ 2:2,\ 4:1$ | 4 | 5 / 4 |
| 3 | 18 | $1:1,\ 2:6,\ 4:9,\ 8:2$ | 8 | 33 / 32 |
| 4 | 166 | $1:1,\ 2:14,\ 4:55,\ 8:64,\ 16:25,\ 32:6,\ 64:1$ | 64 | 709 / 708 |

Every nonzero matrix entry in these calculations was $+1$ or $-1$.

## Exact falsifiers found

The route rejected an entropy-only Fannes transfer. Detailed constructions are retained in
[../failures/exact-counterexamples.md](../failures/exact-counterexamples.md).

### Earlier generic $K=16$ star

The exact difference is

$$
\frac{29}{30}\log15-\frac{14}{15}\log10
=
0.4687024409376938\ldots
$$

at $\eta=1/30$. The corresponding Fannes value is

$$
h_2(1/30)+\frac1{30}\log15
=
0.2364130860453042\ldots.
$$

This is an exact earlier falsifier for the generic neighborhood functional. It is not a
minimal-source SxPID result.

### Actual three-source, five-cell witness

For the bottom singleton antichain and constant target, the exact difference is

$$
\frac1{10}\log10+\frac9{10}\log\frac43
=
0.4891723745060074\ldots.
$$

Its union support is the five-state union-support face. It exceeds the Fannes--Audenaert entropy
expression computed on that face by

$$
\frac9{10}\log\frac65-\frac1{10}\log4
=
0.0254599650025701\ldots>0.
$$

The same witness attains

$$
E_{\max}+\gamma_3
$$

with equality. It therefore makes that candidate budget sharp at this instance. This route does
not claim that the same entropy expression formed with a larger complete ambient
Cartesian-product cardinality fails, and it did not prove that five cells are globally minimal.

### Actual four-source, six-pair witness

The six-pair half-transfer star has

$$
\eta=\frac1{12}
$$

and

$$
|\Delta G|
=
\frac1{12}\log6+\frac56\log\frac32
=
0.4872008791924749\ldots.
$$

Its excess over the support-size-seven Fannes expression is

$$
0.05105160703397634\ldots>0.
$$

Within the half-transfer star family, the excess is negative for branch counts
$m=1,\ldots,5$ and positive for $m=6$. This establishes minimality only inside that fixed
family. It does not establish global minimality over SxPID systems, antichains, or laws.

## Complete bounded test record

### Candidate generic coupling bound

The denominator-four exhaustive grid tested 44,840 neighborhood-and-law-pair cases.

| $K$ | Neighborhood class | Systems | Laws | Law pairs per system | Cases |
|---:|---|---:|---:|---:|---:|
| 2 | Directed reflexive | 4 | 5 | 10 | 40 |
| 3 | Directed reflexive | 64 | 15 | 105 | 6,720 |
| 4 | Symmetric reflexive | 64 | 35 | 595 | 38,080 |

### Candidate union-of-equivalences overlap bound

The denominator-four exhaustive grid tested 490,790 represented unions and law pairs for
$K\leq4$ and $J\leq3$.

| $K$ | $J=1$ | $J=2$ | $J=3$ |
|---:|---:|---:|---:|
| 2 | 20 | 30 | 40 |
| 3 | 525 | 1,575 | 3,675 |
| 4 | 8,925 | 71,400 | 404,600 |

### Full binary SxPID grids

Every distinct denominator-two law pair was tested on the full binary two-source and three-source
systems.

| Sources | Cells | Nodes | Laws | Law pairs | Direct and atom inequalities |
|---:|---:|---:|---:|---:|---:|
| 2 | 8 | 4 | 36 | 630 | 30,240 |
| 3 | 16 | 18 | 136 | 9,180 | 1,982,880 |

The total was 9,810 law pairs and 2,013,120 scalar direct-or-atom inequality checks.

The route also ran:

- 20,000 randomized trials, each with a generic and a union-of-equivalences check;
- 900 randomized SxPID law-pair checks across two-source and three-source systems; and
- 30 randomized full four-source checks, each using all 166 lattice nodes.

No candidate residual, overlap, cumulative, or atom bound failed in these tested domains.
This is a bounded nonfinding, not a proof.

## Bounded $K=4$ entropy-only searches

The route searched every graph and every distinct law pair on four finite grids.

| Grid denominator | Graph class | Graphs | Laws | Pairs per graph | Graph-law-pair evaluations |
|---:|---|---:|---:|---:|---:|
| 10 | Directed reflexive | 4,096 | 286 | 40,755 | 166,932,480 |
| 12 | Directed reflexive | 4,096 | 455 | 103,285 | 423,055,360 |
| 10 | Symmetric reflexive | 64 | 286 | 40,755 | 2,608,320 |
| 20 | Symmetric reflexive | 64 | 1,771 | 1,567,335 | 100,309,440 |

These runs did not find a $K=4$ entropy-only violation. They do not prove that the five-cell
witness is globally minimal. The fast search used binary64 array calculations to select a
candidate extremum and then reevaluated that candidate with rational inputs and `Decimal`
logarithms. A missed near-tie remains possible.

## Numerical evidence class

All `Decimal` values are reference-only. They are not directed-rounding intervals. Tiny slacks at
the $10^{-100}$ scale are arithmetic residue, not negative certificates.

The strict counterexample signs do not rely only on `Decimal` output. They reduce to exact integer
inequalities where stated in the counterexample register.

## Ephemeral route artifacts

The following files were outside the repository when this memo was written:

| Ephemeral path | SHA-256 |
|---|---|
| `/tmp/support_free_sxpid_attack.py` | `f9027dfb8a3597a1d408b296e7c3e9908d3af257abfe27e1c7687413551c48fa` |
| `/tmp/support-free-sxpid-oracle-v1.json` | `378f5f9df747d20eceae148a7f158bcc241aa4ab23219567019425be7de9c913` |

The hashes identify the observed bytes. They do not preserve `/tmp`, authenticate an author, or
make the artifacts part of the release.

Revision 2 added a tracked, standard-library-only generator that imports no pid-rs code, immutable
fixtures, and a Rust replay test. This implementation separation reduces shared-code risk; it is
not independent authorship or review. The promoted artifacts and current replay status are
recorded in
[`../failures/exact-counterexamples.md`](../failures/exact-counterexamples.md).

## Untested domains

This route did not establish:

- continuum-wide minimality of the five-cell witness;
- a proof from the bounded $K=4$ nonfindings;
- exhaustive four-source laws;
- exhaustive nonbinary source or target alphabets;
- sharp global constants for the candidate bounds;
- interval-certified logarithms;
- conformance of Rust results to the exact-real functional;
- an end-to-end Rust refinement proof or certified binary64 enclosure;
- estimator consistency, concentration, or calibration.

Bounded searches also did not break a stronger net bound that replaces $E_a+E_b$ by
$E_{\max}$. That nonfinding is not sufficient. An exact residual construction invalidates that
shortcut inside the current proof decomposition, so the retained candidate uses $E_a+E_b$.
