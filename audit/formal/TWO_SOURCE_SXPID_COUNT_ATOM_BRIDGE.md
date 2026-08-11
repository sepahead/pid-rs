# Two-source categorical SxPID count-to-atom bridge

## Status

This is the **bounded accepted formal audit** of
[`TwoSourceMobiusAtomBridge.lean`](lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean).
The companion claim is
[`SX-COUNT-ATOM-BRIDGE-001`](../../claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md), with its paired
[LaTeX source](latex/two-source-sxpid-count-atom-bridge.tex) and
[rendered PDF](../../output/pdf/two-source-sxpid-count-atom-bridge.pdf).

The checked source extends the completed supplied-count event bridge from four signed-net
cumulatives to every informative, misinformative, and signed-net cumulative and two-source
Möbius atom. It gives one quantified result over a fixed 24-coordinate type. Exact identities,
the 71-route change registry, document checks, and review boundaries are recorded in the
[revision-2 receipt](../../claims/SX-COUNT-ATOM-BRIDGE-001/phase-a-verification-2026-08-10.md).

## Provenance boundary

The categorical shared-exclusions event functional, informative/misinformative decomposition,
signed-net value, and partial-information atom construction by Möbius inversion are defined by
Makkeh, Gutknecht, and Wibral (2021). The part-whole and formal-logic organization is elaborated by
Gutknecht, Wibral, and Makkeh (2021).

The following are paper-defined mathematical content used here:

- keyed source-event disjunctions and keyed target restrictions;
- informative and misinformative pointwise cumulative components;
- signed net as informative minus misinformative;
- atom construction by Möbius inversion; and
- empirical averaging from pointwise quantities.

The following are project-defined formalization and assurance choices:

- the Lean encodings and names;
- the concrete source-node, atom, component, and coordinate orders;
- the ordered 24-coordinate surface;
- the supplied exact-count interface and positive-support formulation;
- the exact rational and real product representatives;
- the theorem decomposition and replay design; and
- this claim packet and its bounded acceptance process.

This work defines no new PID measure. “Project-defined” here identifies an implementation or
assurance contribution, not scientific novelty. The paper-to-Lean transcription is reviewed prose
and code correspondence; Lean does not ingest or derive the publication text.

## Finite supplied-count model

Let the two possibly heterogeneous source alphabets and target alphabet be finite. A complete key
is $z=(s_1,s_2,t)$. Let $c_z\in\mathbb N$ be supplied on the complete key space and

$$
N=\sum_z c_z>0,
\qquad
Z_+=\{z:c_z>0\}.
$$

Zero-count complete keys are permitted. Only $Z_+$ enters the logarithms and empirical average.
For a cumulative node $\alpha$ and supported anchor $z$, define:

- $E_\alpha(z)$: the keyed source event;
- $T(z)$: the keyed target event;
- $E_{\alpha,t}(z)=E_\alpha(z)\cap T(z)$;
- $C_\alpha(z)$, $C_t(z)$, and $C_{\alpha,t}(z)$: their exact natural counts.

The completed count/event bridge proves all three event counts are positive on $Z_+$. Thus the
checked module does not assume its logarithm arguments are positive independently.

## The four cumulative nodes

| Order | Node | Keyed source event | Symbol |
|---:|---|---|---|
| 1 | source one | source one equals its anchor value | $C_1$ |
| 2 | source two | source two equals its anchor value | $C_2$ |
| 3 | joint sources | both sources equal their anchor values | $C_{12}$ |
| 4 | redundancy | source one or source two equals its anchor value | $C_R$ |

The redundancy source event is a union. The joint event is the intersection of the two singleton
source branches. These event facts are inherited, not reproved by the new atom module.

## Three local components

For each supported anchor, define exact positive rational arguments

$$
q^+_\alpha(z)=\frac{N}{C_\alpha(z)},
\qquad
q^-_\alpha(z)=\frac{C_t(z)}{C_{\alpha,t}(z)},
$$

and

$$
q^n_\alpha(z)
=\frac{N C_{\alpha,t}(z)}{C_\alpha(z)C_t(z)}
=\frac{q^+_\alpha(z)}{q^-_\alpha(z)}.
$$

The corresponding local values are natural logarithms:

$$
i^u_\alpha(z)=\log q^u_\alpha(z),
\qquad u\in\{+,-,n\}.
$$

Consequently

$$
i^n_\alpha(z)=i^+_\alpha(z)-i^-_\alpha(z).
$$

The checked module proves the informative and misinformative empirical count/log equalities directly,
then selects all three cases through one component type. All values are in nats.

## Empirical cumulatives

For each component and node,

$$
C^u_\alpha
=\sum_{z\in Z_+}\frac{c_z}{N}i^u_\alpha(z).
$$

No smoothing, pseudo-count, clamping, or uniform-on-support reweighting is inserted. Finite-sum
linearity yields

$$
C^n_\alpha=C^+_\alpha-C^-_\alpha.
$$

## Concrete two-source Möbius and zeta transforms

In cumulative order $[C_1,C_2,C_{12},C_R]$ and atom order $[U_1,U_2,S,R]$, the checked module fixes

$$
M=
\begin{pmatrix}
 1& 0&0&-1\\
 0& 1&0&-1\\
-1&-1&1& 1\\
 0& 0&0& 1
\end{pmatrix}.
$$

Thus, component by component,

$$
R=C_R,
\quad U_1=C_1-C_R,
\quad U_2=C_2-C_R,
\quad S=C_{12}-C_1-C_2+C_R.
$$

The zeta inverse is

$$
Z=
\begin{pmatrix}
1&0&0&1\\
0&1&0&1\\
1&1&1&1\\
0&0&0&1
\end{pmatrix},
$$

giving

$$
C_1=U_1+R,
\quad C_2=U_2+R,
\quad C_{12}=U_1+U_2+S+R,
\quad C_R=R.
$$

Lean proves both compositions are identities over any additive commutative group. This separates
the lattice algebra from real logarithms and empirical probabilities.

## Source-labelled coordinate exchange

The coordinate swap acts as

$$
C_1\leftrightarrow C_2,
\qquad U_1\leftrightarrow U_2,
$$

and fixes $C_{12}$, $C_R$, $S$, and $R$. The checked module proves both swap maps are
involutions and that Möbius inversion is equivariant under the swap. This is a formula theorem for
an arbitrary four-entry cumulative function. It does not transport heterogeneous source types,
keys, counts, laws, or inherited events, and it does not claim a Rust refinement.

## Averaging commutes with inversion

Let $m_\gamma$ denote the integer row for atom $\gamma$. The pointwise atom is

$$
\pi^u_\gamma(z)=\sum_\alpha m_{\gamma\alpha}i^u_\alpha(z).
$$

The checked module proves

$$
\sum_{z\in Z_+}\frac{c_z}{N}\pi^u_\gamma(z)
=\sum_\alpha m_{\gamma\alpha}
 \left(\sum_{z\in Z_+}\frac{c_z}{N}i^u_\alpha(z)\right).
$$

Accordingly, pointwise inversion followed by averaging equals averaging the four cumulatives
followed by inversion. This theorem is quantified over all three components and four atoms. The
same linearity also proves

$$
\Pi^n_\gamma=\Pi^+_\gamma-\Pi^-_\gamma.
$$

## The 24-coordinate surface

The project-defined coordinate order is:

| Block | Coordinates |
|---|---|
| informative cumulatives | $C^+_1,C^+_2,C^+_{12},C^+_R$ |
| misinformative cumulatives | $C^-_1,C^-_2,C^-_{12},C^-_R$ |
| net cumulatives | $C^n_1,C^n_2,C^n_{12},C^n_R$ |
| informative atoms | $U^+_1,U^+_2,S^+,R^+$ |
| misinformative atoms | $U^-_1,U^-_2,S^-,R^-$ |
| net atoms | $U^n_1,U^n_2,S^n,R^n$ |

The source defines one sum type for cumulative-or-atom coordinates, proves that its finite
cardinality is 24, proves the explicit order has length 24 with no duplicate, and proves the
order's finite-set projection is the complete coordinate universe. This fixes a mathematical
order but not an executable serialization.

The all-coordinate supplied-count theorem states, for arbitrary `coordinate`,

$$
\mathrm{averageCoordinate}(\widehat p_c,\mathrm{coordinate})
=\mathrm{countExpression}(c,\mathrm{coordinate}).
$$

The cumulative case uses the exact local log arguments. The atom case lifts that equality through
the fixed Möbius transform.

## Exact products

For a cumulative coordinate, define

$$
P^u_\alpha
=\prod_{z\in Z_+}\left(q^u_\alpha(z)\right)^{c_z}>0.
$$

An exact rational product is constructed in parallel. Write $A^u_\gamma$ for the product of an
atom and $P^u_\alpha$ for the product of a cumulative. Then

$$
A^u_{U_1}=\frac{P^u_1}{P^u_R},
\qquad
A^u_{U_2}=\frac{P^u_2}{P^u_R},
$$

$$
A^u_S=\frac{P^u_{12}P^u_R}{P^u_1P^u_2},
\qquad
A^u_R=P^u_R.
$$

All denominators are nonzero because the cumulative products are positive. The checked module proves
the real product is the cast of its exact rational counterpart.

Write $Q(c,\xi)$ for the cumulative or atom product selected by coordinate $\xi$. The finite
log-product rule yields, uniformly over all 24 coordinates,

$$
V(c,\xi)=\frac1N\log Q(c,\xi).
$$

Since $N>0$ and $Q(c,\xi)>0$,

$$
V(c,\xi)>0\iff Q(c,\xi)>1,
\qquad
V(c,\xi)<0\iff Q(c,\xi)<1,
\qquad
V(c,\xi)=0\iff Q(c,\xi)=1.
$$

This is an exact mathematical reduction. It does not prove that an existing executable constructs
the same rational product, performs a bounded comparison, or emits a matching record.

## Component-nonnegativity boundary

The checked module does **not** prove that every informative or misinformative atom is nonnegative. Its
sign theorems are conditional equivalences: a coordinate is positive, negative, or zero exactly
when its exact product lies above, below, or at one. They do not prove where a component atom's
product must lie. They also do not supply a counterexample to component nonnegativity.

This distinction is essential. A generic sign classifier over the 24-coordinate type is not the
publication's component-nonnegativity theorem, and it must not be reported as one.

## Twenty-four-lens audit

| Lens | Question | Bounded finding |
|---:|---|---|
| 1 | Measure identity | The definitions remain categorical shared exclusions; no `I_min`, continuous KSG, or other PID is substituted. |
| 2 | Publication provenance | Event/component/Möbius mathematics is paper-defined; Lean encodings and assurance composition are project-defined. |
| 3 | Source arity | Every new theorem is fixed to exactly two sources through `Fin 2`. |
| 4 | Alphabet generality | Source alphabets may differ and all source/target alphabets are finite. |
| 5 | Count quantifier | Arbitrary natural counts are allowed; only total count must be positive. |
| 6 | Support | Zero cells are permitted and logarithms range only over positive-count anchors. |
| 7 | Event logic | The new module imports the completed keyed event semantics rather than redefining them. |
| 8 | Component signs | Net is informative minus misinformative with no clamp or absolute value. |
| 9 | Node order | Source one, source two, joint, redundancy are explicit and tested by length/order theorems. |
| 10 | Atom order | Unique one, unique two, synergy, redundancy are explicit and distinct from cumulative nodes. |
| 11 | Möbius coefficients | All two-source coefficients are literal integers in one table and one concrete transform. |
| 12 | Inverse algebra | Both Möbius-after-zeta and zeta-after-Möbius identities are stated. |
| 13 | Reconstruction | Marginal and joint cumulative reconstruction equations are explicit. |
| 14 | Coordinate symmetry | A coordinate swap exchanges only the two source-labelled node and atom positions; no source-type, key, count, law, or event transport is claimed. |
| 15 | Component linearity | Möbius inversion commutes with informative-minus-misinformative subtraction. |
| 16 | Averaging | Pointwise inversion and inversion after exact empirical averaging are proved equal. |
| 17 | Coordinate completeness | The type cardinality and list length are 24, the list has no duplicate, and its finite-set projection equals the complete coordinate universe. |
| 18 | Local exactness | Each supported local value is tied to an exact rational count argument. |
| 19 | Product construction | Count multiplicities become integer exponents; atom coefficients become products and quotients. |
| 20 | Exact-real bridge | Every real product is related to an exact rational cast. |
| 21 | Sign logic | Positive, negative, and zero statements use strict comparison or equality with one. |
| 22 | Implementation boundary | No theorem mentions Rust execution, binary64, parser, fields, or the standalone certifier. |
| 23 | Statistical boundary | The source contains no sampling, population, uncertainty, or calibration theorem. |
| 24 | Acceptance evidence | Exact source/kernel binding, 71 registered changes, categorical-only scope integration, deterministic PDF checks, page inspection, and separate read-only repository-workflow reviews are recorded. |

These lenses are a structured review, not 24 independent proofs.

## Open refinements and nonclaims

The accepted bounded result leaves all of the following open:

1. publication text to Lean-definition derivation;
2. rows, bytes, files, JSON, or another representation to exact counts;
3. Rust categorical sorting and histogram extraction;
4. Rust `NODES2` and `invert2` refinement;
5. Rust pointwise accumulation and result-field order;
6. binary64 logarithms and summation;
7. standalone-certifier and Python refinement;
8. compiler, runtime, parser, integer overflow, cancellation, allocation, and resource behavior;
9. component-atom nonnegativity;
10. sampling, concentration, uncertainty, consistency, and population validity;
11. continuous shared-exclusions estimators, quantized wrappers, `I_min`, and Shannon invariants;
12. three-source and general higher-source lattices;
13. scientific priority or uniqueness; and
14. release readiness or downstream authority.

## Acceptance evidence

The pinned checker binds 11 sources, eight imported modules, 339 declarations, and 246 named source
theorem axiom bases. Both semantic contracts compile with `lean -t 0`. Under normal and optimized
Python, the self-test rejects 40 static, five count/event, 17 atom-module, and nine atom-contract
changes. The catalog and assurance evidence are limited to stable categorical SxPID. The LaTeX/PDF
pair is deterministically checked and every rendered page was inspected. Separate read-only
formal, integration, and document reviews occurred within the repository workflow; they are not
external review or independent authorship. The exact receipt and residual cut are linked above.

## References

1. Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral, “Introducing a Differentiable Measure
   of Pointwise Shared Information,” *Physical Review E* 103, 032149 (2021),
   <https://doi.org/10.1103/PhysRevE.103.032149>.
2. Aaron J. Gutknecht, Michael Wibral, and Abdullah Makkeh, “Bits and Pieces: Understanding
   Information Decomposition from Part-Whole Relationships and Formal Logic,” *Proceedings of the
   Royal Society A* 477 (2021), <https://doi.org/10.1098/rspa.2021.0110>.

These references define the scientific object and its conceptual organization. They do not
define this repository's Lean interface, 24-coordinate order, checker design, or executable
refinement.
