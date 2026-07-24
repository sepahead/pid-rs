# Claim SX-SUPPORT-FREE-CONTINUITY-001, revision 2

## Record status

Revision 2 freezes a quantitative form of the qualitative claim in
[`claim-v1.md`](claim-v1.md). It was created on 2026-07-24 after exploratory proof,
counterexample, and formal work had begun. It is retrospective, not preregistered, and does not
establish scientific priority.

The claim disposition is **closed for the exact-real analytic claim**. The exact proof,
primary-source semantics, retained counterexamples, formal theorem map, implementation-separated
replay, and manuscript red-team review agree. The Lean route remains explicitly partial. Rust
conformance, binary64 enclosure, estimator calibration, authorship-independent peer review, and
consumer qualification remain separate claims.

## Claim class

This is a project-defined exact-real theorem about the paper-defined averaged categorical
shared-exclusions PID. It defines neither a new PID measure nor a new estimator.

The novelty-safe description is:

> A project-defined, support-change-tolerant total-variation modulus for averaged categorical
> shared-exclusions quantities on a fixed finite alphabet.

No priority claim is made.

## Fixed objects and conventions

- Fix a source count $m\geq1$.
- Fix nonempty finite source alphabets $\mathcal S_1,\ldots,\mathcal S_m$ and target alphabet
  $\mathcal T$.
- Fix their complete Cartesian-product alphabet
  $\mathcal Z=\mathcal S_1\times\cdots\times\mathcal S_m\times\mathcal T$, with
  $K=|\mathcal Z|$.
- Fix the full finite redundancy lattice, its order, and its Möbius inverse $M$.
- Use the paper-defined union-of-source-collection events.
- Sum local values only over positive-mass keyed realizations.
- Use exact real arithmetic and natural logarithms.

The alphabet, event map, lattice, and matrix do not vary with the law. Cells may enter or leave a
law's support inside the fixed alphabet.

For laws $p,q\in\Delta(\mathcal Z)$, put

$$
\eta=d_{\mathrm{TV}}(p,q)=\tfrac12\lVert p-q\rVert_1,\qquad R=1-\eta.
$$

Define

$$
r_z=\min\{p_z,q_z\},\qquad a_z=p_z-r_z,\qquad b_z=q_z-r_z.
$$

Then $\sum a=\sum b=\eta$, $\sum r=R$, and the positive supports of $a$ and $b$ are
disjoint. Define the subprobability residual entropy

$$
E(d)=-\sum_{z:d_z>0}d_z\log d_z,
$$

and

$$
E_\vee=\max\{E(a),E(b)\},\qquad E_\Sigma=E(a)+E(b).
$$

## Generic anchored-neighborhood claim

Let $X$ be finite and, independently of the preceding fixed-alphabet notation, let $p,q$ be laws
on $X$. Redefine $\eta$, $R$, $r$, $a$, $b$, $E_\vee$, and $E_\Sigma$ on $X$ by the formulas
above. Let $N_x\subseteq X$ be fixed with $x\in N_x$. Define

$$
G_N(p)=-\sum_{x:p_x>0}p_x\log p(N_x).
$$

For $R>0$, define

$$
T_N(r,d)=
\sum_{x:r_x>0}r_x\frac{d(N_x)}{r(N_x)}.
$$

The exact target inequality is

$$
|G_N(p)-G_N(q)|
\le
E_\vee+
R\log\!\left(
1+\frac{\max\{T_N(r,a),T_N(r,b)\}}R
\right).
\tag{V2.1}
$$

The common term is defined as zero when $R=0$. The statement includes $\eta=0$ and
$\eta=1$.

If $J\ge1$ and, for each $j\in\{1,\ldots,J\}$, $[x]_j$ is the class of $x$ under a fixed equivalence
relation $\sim_j$, and

$$
N_x=\bigcup_{j=1}^J[x]_j,
$$

then

$$
T_N(r,d)\le J\eta.
\tag{V2.2}
$$

The relations $\sim_j$ may differ. Define

$$
g_J(\eta)=
\begin{cases}
(1-\eta)\log\!\left(1+\dfrac{J\eta}{1-\eta}\right),
  &0<\eta<1,\\
0,&\eta\in\{0,1\}.
\end{cases}
$$

Then

$$
|G_N(p)-G_N(q)|\le E_\vee+g_J(\eta),
\qquad
g_J(\eta)\le J\eta.
\tag{V2.3}
$$

The committed star construction must attain the residual-plus-$g_J$ bound as an actual
paper-semantic categorical Sx event. This is an equality claim for the displayed decomposition; it
is not a claim that every final atom modulus below is globally sharp.

## Averaged cumulative claim

For a full-lattice node $\beta$, let $J_\beta=|\beta|$. Let $I_\beta^+$,
$I_\beta^-$, and $I_\beta^{\mathrm{net}}$ be the support-restricted averaged informative,
misinformative, and net cumulatives fixed in [`conventions.md`](conventions.md). Revision 2 claims

$$
|\Delta I_\beta^+|
\le E_\vee+g_{J_\beta}(\eta),
\tag{V2.4}
$$

$$
|\Delta I_\beta^-|
\le E_\vee+g_{J_\beta}(\eta)+g_1(\eta),
\tag{V2.5}
$$

$$
|\Delta I_\beta^{\mathrm{net}}|
\le E_\Sigma+2g_{J_\beta}(\eta)+g_1(\eta).
\tag{V2.6}
$$

The single residual-entropy term in Equation (V2.5) uses the pointwise nonnegativity and
surprisal envelope of the complete misinformative local expression. The sum $E_\Sigma$ in
Equation (V2.6) is deliberate: the retained exact net-residual counterexample rejects replacing
the two signed residual budgets by their maximum in this proof.

## Full-lattice atom claim

Use the orientation

$$
\Pi_\alpha^u=\sum_\beta M_{\alpha\beta}I_\beta^u.
$$

Define

$$
W_\alpha(\eta)=
\sum_\beta|M_{\alpha\beta}|g_{J_\beta}(\eta),
\qquad
s_\alpha=\sum_\beta M_{\alpha\beta}.
$$

For the full finite redundancy lattice with least node $\bot$,

$$
s_\alpha=\mathbf1\{\alpha=\bot\}.
\tag{V2.7}
$$

Using the paper-defined pointwise nonnegativity of informative and misinformative component atoms,
Revision 2 claims

$$
|\Delta\Pi_\alpha^+|
\le E_\vee+W_\alpha(\eta),
\tag{V2.8}
$$

$$
|\Delta\Pi_\alpha^-|
\le E_\vee+W_\alpha(\eta)+|s_\alpha|g_1(\eta),
\tag{V2.9}
$$

$$
|\Delta\Pi_\alpha^{\mathrm{net}}|
\le E_\Sigma+2W_\alpha(\eta)+|s_\alpha|g_1(\eta).
\tag{V2.10}
$$

These atom claims are restricted to the paper-defined full lattice. The row-sum and component-sign
arguments do not automatically transfer to a truncated node family or an arbitrary coefficient
matrix.

## Alphabet-only envelopes and continuity conclusion

For $\eta>0$, Revision 2 claims

$$
E_\vee
\le
e_K^\vee(\eta)
:=
\eta\log\frac{K-1}{\eta},
\tag{V2.11}
$$

and

$$
E_\Sigma
\le
e_K^\Sigma(\eta)
:=
\eta\log\frac{\lfloor K^2/4\rfloor}{\eta^2}.
\tag{V2.12}
$$

Both envelopes are defined as zero at $\eta=0$; when $K=1$, necessarily $\eta=0$.

Equations (V2.3)--(V2.12) imply that every support-restricted averaged categorical Sx cumulative
and full-lattice atom is uniformly continuous in total variation on the closed simplex over the
fixed alphabet, including across support creation and deletion, without a positive minimum
population cell-mass premise.

This conclusion does not extend to a disappearing realization's pointwise local value.

## Monotone transfer from an upper law-distance radius

The exact functions above are not all monotone on $[0,1]$. For $K\geq2$ and
$0\leq\eta\leq\varepsilon\leq1$, define

$$
\bar e_K^\vee(\varepsilon)
=
\varepsilon\left[1+\log\frac{K-1}{\varepsilon}\right],
$$

$$
\bar e_K^\Sigma(\varepsilon)
=
\varepsilon\left[
2+\log\frac{\lfloor K^2/4\rfloor}{\varepsilon^2}
\right],
$$

with both values zero at $\varepsilon=0$. Revision 2 claims

$$
E_\vee\leq\bar e_K^\vee(\varepsilon),\qquad
E_\Sigma\leq\bar e_K^\Sigma(\varepsilon),\qquad
g_J(\eta)\leq J\varepsilon.
\tag{V2.13}
$$

Let

$$
L_\alpha=\sum_\beta|M_{\alpha\beta}|J_\beta.
$$

On an event where $d_{\mathrm{TV}}(\widehat p,p)\leq\varepsilon$, the claimed deterministic
radii are:

| Quantity | Radius |
|---|---:|
| $I_\beta^+$ | $\bar e_K^\vee+J_\beta\varepsilon$ |
| $I_\beta^-$ | $\bar e_K^\vee+(J_\beta+1)\varepsilon$ |
| $I_\beta^{\mathrm{net}}$ | $\bar e_K^\Sigma+(2J_\beta+1)\varepsilon$ |
| $\Pi_\alpha^+$ | $\bar e_K^\vee+L_\alpha\varepsilon$ |
| $\Pi_\alpha^-$ | $\bar e_K^\vee+(L_\alpha+\lvert s_\alpha\rvert)\varepsilon$ |
| $\Pi_\alpha^{\mathrm{net}}$ | $\bar e_K^\Sigma+(2L_\alpha+\lvert s_\alpha\rvert)\varepsilon$ |

The dependency-colored empirical-law theorem can supply such an $\varepsilon$ only under its
declared probability premises. This composition does not infer a valid coloring from data and
does not remove the exponential finite-alphabet factor in that law-distance theorem.

## Exact range caps

Let $K_S=\prod_i|\mathcal S_i|$. Each informative or misinformative cumulative and component
atom lies in $[0,\log K_S]$. Therefore each component difference can be capped by
$\log K_S$, and each net difference can be capped by $2\log K_S$.

These are functional range caps, not binary64 error bounds.

## Required retained falsifiers and scope guards

The evidence packet must retain:

1. the copied-source $T=S_1$ family, which rejects a global linear modulus and pointwise
   support-boundary continuity;
2. the exact three-source Sx witness whose union-support face has five states, which rejects
   substituting the ordinary active-face Fannes--Audenaert entropy radius for the
   neighborhood-functional bound and attains $E_\vee+g_3$ without making an ambient-cardinality
   claim;
3. the exact signed net-residual witness, which rejects a maximum-residual proof shortcut without
   claiming global sharpness of Equation (V2.10);
4. the V-poset truncated-family example, which rejects transferring the full-lattice row-sum and
   component-sign argument to an arbitrary node family; and
5. the growing-alphabet copied-source family, which rejects an alphabet-independent modulus.

Any bounded nonfinding must remain labelled as bounded and must not be promoted to a minimality
proof.

## Non-solutions and nonclaims

The following do not close Revision 2:

- fixed-support differentiability or an eventual-support argument;
- an abstract finite-vector lemma without the paper-semantic event bridge;
- a decimal comparison without exact identities or rigorous enclosures;
- bounded enumeration presented as a universal theorem;
- a binary64 fixture presented as exact-real refinement;
- a theorem on a selected antichain or truncated lattice;
- or a result for a changing alphabet or data-dependent quantizer.

Revision 2 does not claim:

- global Lipschitz continuity;
- pointwise continuity for disappearing keys;
- an alphabet-free modulus;
- global sharpness of every displayed cumulative or atom bound;
- a certified binary64 sign or tie;
- calibration under arbitrary dependence, drift, or repeated selection;
- consistency of continuous PID2;
- validity of full continuous PID3;
- or authority for an alert or action.

## Closure evidence and open bridges

The exact mathematical claim can close only if these artifacts agree:

- the derivation in
  [`../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md`](../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md);
- the standalone LaTeX/PDF rendering and reproducibility check;
- the source-semantic record in [`route-memos/provenance.md`](route-memos/provenance.md);
- the exact counterexamples in
  [`failures/exact-counterexamples.md`](failures/exact-counterexamples.md);
- the formal scope and theorem map in [`formal/theorem-map.md`](formal/theorem-map.md);
- and the implementation-separated generator plus bounded Rust replay.

The generator is standard-library-only and imports no pid-rs code. This reduces shared
implementation risk but is not independent authorship or review.

The current Lean module checks finite-vector overlap, residual entropy, abstract sign transfer,
generic Möbius row sums, and scalar $g_J$ properties. It does not formalize probability laws,
anchored neighborhoods, $T_N\leq J\eta$, paper-defined Sx events, the antichain lattice,
published component nonnegativity, sampling, Rust, or binary64 arithmetic. Those boundaries must
remain explicit even if the exact prose proof closes.
