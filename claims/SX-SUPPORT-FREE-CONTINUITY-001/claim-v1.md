# Claim SX-SUPPORT-FREE-CONTINUITY-001, revision 1

## Record status

This packet was created on 2026-07-24 after exploratory analysis, proof work, and formal work had
started. It is retrospective. It was not preregistered. It is not an independent audit, a blind
evaluation, or evidence of scientific priority.

The claim disposition is **open**. The defining papers establish the shared-exclusions semantics,
the finite redundancy lattice, the pointwise Möbius decomposition, and component nonnegativity.
They do not establish the closed-simplex continuity claim below.

## Claim class

This is a project-defined population-functional theorem about the paper-defined categorical
shared-exclusions PID. It does not define a new PID measure or estimator.

## Fixed objects

- Fix a source count $n\geq 1$.
- Fix finite source alphabets and a finite target alphabet.
- Let $\mathcal Z$ be their complete Cartesian-product alphabet.
- Let $\Delta(\mathcal Z)$ be the closed probability simplex on that fixed alphabet.
- Fix the full finite redundancy lattice $\mathcal A_n$ described in
  [conventions.md](conventions.md).
- Use exact real arithmetic and natural logarithms.

The alphabet, source count, event map, lattice order, and Möbius inverse do not change with the
law.

## Exact target statement

For every law $P\in\Delta(\mathcal Z)$, define each averaged categorical shared-exclusions
cumulative and atom by summing only over positive-mass realizations:

$$
C_\alpha^u(P)
=
\sum_{z\in\mathrm{supp}\,P}P(z)c_\alpha^u(z;P),
\qquad
\Pi_\alpha^u(P)
=
\sum_{z\in\mathrm{supp}\,P}P(z)\pi_\alpha^u(z;P),
$$

where $\alpha\in\mathcal A_n$ and $u\in\{+,-,\mathrm{net}\}$. The local terms and boundary
convention are fixed in [conventions.md](conventions.md).

The target claim is:

> Every map $P\mapsto C_\alpha^u(P)$ and $P\mapsto\Pi_\alpha^u(P)$ is continuous on the closed
> simplex $\Delta(\mathcal Z)$ in total variation. Since the alphabet and lattice are finite, the
> complete finite family is uniformly continuous. The statement remains valid when cells enter or
> leave the support and does not require a positive population cell-mass floor.

Equivalently, if $\mathcal F$ is the finite family of all listed cumulative and atom maps, then

$$
\forall\varepsilon>0\;\exists\delta>0\;\forall P,Q\in\Delta(\mathcal Z):
\quad
\lVert P-Q\rVert_1<\delta
\Longrightarrow
\max_{F\in\mathcal F}|F(P)-F(Q)|<\varepsilon.
$$

Revision 1 does not claim a sharp modulus or a global Lipschitz constant. A later quantitative
claim must freeze its exact formula, constants, distance convention, endpoint convention, and atom
scope in a new claim revision.

## Premises

1. $\mathcal Z$ is a fixed finite ambient alphabet, including cells that can have zero mass.
2. The full finite redundancy lattice and its order are fixed.
3. The event for an antichain is the paper-defined union of source-collection conjunctions.
4. Local terms are evaluated only for a positive-mass keyed realization.
5. Averaging is with the same law that defines the local event probabilities.
6. Informative and misinformative atoms use separate Möbius inversions.
7. Net terms are informative terms minus misinformative terms.
8. All mathematical quantities use exact real arithmetic.

## Non-solutions

The following results do not complete this claim:

- continuity only on one fixed support face;
- differentiability only in the interior of the simplex;
- convergence after eventual empirical-support stabilization;
- a bound that assumes a positive minimum cell mass;
- pointwise continuity for a realization whose mass tends to zero;
- a binary64 test or high-precision fixture;
- an abstract residual-entropy lemma without the shared-exclusions semantic bridge;
- a result for only one antichain, source count, or selected support pattern;
- a theorem for a data-dependent alphabet or changing lattice;
- a result for continuous, mixed, singular, or fitted-quantized inputs.

## Falsifiers

The claim is false if one can provide fixed finite $\mathcal Z$, fixed $\alpha$, and laws
$P_k\to P$ in total variation for which one listed averaged quantity does not converge.

Any claimed linear modulus is already false. The exact $T=S_1$ construction in
[failures/provenance-boundaries.md](failures/provenance-boundaries.md) has variation of order
$\eta\log(1/\eta)$, where $\eta$ is total variation.

## Evidence needed for closure

Closure requires:

1. a complete exact-real proof for every cumulative family;
2. transfer through the fixed full-lattice Möbius inverse;
3. an explicit proof that pointwise inversion followed by averaging equals inversion of averaged
   cumulatives;
4. a rigorous support-boundary convention with no use of $0\cdot\infty$;
5. a counterexample audit that includes support creation, support deletion, constant sources,
   copied sources, and near-zero cells;
6. a formal statement that preserves the paper-defined event semantics, or an explicit record that
   the semantic identification remains a prose proof.

Rust conformance, floating-point error, estimator consistency, and statistical calibration are
separate claims.

## Novelty-safe description

If the obligations close, use this description:

> A project-defined, support-change-tolerant continuity theorem for averaged categorical
> shared-exclusions quantities on a fixed finite alphabet.

Do not use a priority claim. A literature search can fail to find prior work without proving that
none exists.
