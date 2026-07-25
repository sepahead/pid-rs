# Theorem and evidence map for SX-CERTIFIED-AVERAGED-PID2-001

## Scope

This is a map of analytic statements, executable checks, and open formal bridges. It is not a proof
assistant artifact. No theorem below should be described as machine checked unless the evidence
column explicitly says so.

## Mathematical statements

| ID | Statement | Analytic basis | Executable evidence | Formal status |
|---|---|---|---|---|
| T1 | Every supported key lies in its four source events and target event, so all event-log denominators are positive. | Finite-set inclusion and positive key count | Exact producer and verifier inequalities | Not kernel checked |
| T2 | $C^{\mathrm{sx}}_\alpha=C^+_\alpha-C^-_\alpha$ for each node. | Exact rational identity $NV/(UT)=(N/U)/(T/V)$ | Exact local ratio checks | Not kernel checked |
| T3 | The three nonredundancy net cumulatives equal empirical mutual information. | Substitute the self-source events in the empirical MI formula | Three independently reconstructed exact-expression equalities | Not kernel checked |
| T4 | $ZM=I_4$ for the pinned matrices. | Direct integer multiplication | Two independent exact matrix checks | Machine-executed algebra, not proof-kernel checked |
| T5 | Möbius-derived atoms reconstruct all cumulatives. | T4 and finite linearity | 12 exact arithmetic self-consistency checks per input | Not kernel checked; this consequence of $ZM=I_4$ is not independent semantic evidence |
| T6 | An empty canonical exact-term map denotes exact zero. | Empty finite sum | Exact-zero witness validation | Not complete for all logarithmic zero identities |
| T7 | For $1\le y<2$, $z=(y-1)/(y+1)$ lies in $[0,1/3)$; the separate $\log 2$ base case uses $y=2$, $z=1/3$, and no recursive range reduction. | Monotonic rational algebra and $2=(1+1/3)/(1-1/3)$ | Exact rational range-reduction grid and pinned $\log 2$ cases | Not kernel checked |
| T8 | Uniform convergence on $[0,1/3]$ permits termwise integration, and the truncated positive atanh series plus the recorded tail bound encloses $\log y$, including the $\log 2$ endpoint. | Weierstrass domination and geometric domination of the positive remainder | Integer fixed-point implementation | Not kernel checked |
| T9 | Exact-integer floor/ceiling operations preserve lower/upper fixed-point bounds. | Euclidean division inequalities | Arithmetic identity tests | Not kernel checked |
| T10 | Signed finite accumulation of per-term enclosures contains the exact log-linear sum. | Induction, with endpoint swap for negative coefficients | Independent coordinate enclosure construction | Not kernel checked |
| T11 | If $F_j\in J_j$ and $J_j\subseteq I_j$, then $F_j\in I_j$. | Set inclusion | Exact rational/dyadic subset predicate | Trivial analytically; implementation not verified |
| T12 | Verifier acceptance implies all 24 target containments under the trusted premises. | T1–T11 plus strict schema/reconstruction checks | Three live certificates, 72 containments | Conditional analytic theorem; no end-to-end formal proof |

## Evidence-layer separation

| Layer | Evidence | What it closes | What it does not close |
|---|---|---|---|
| Specification | Claim, conventions, schemas, fixed matrices | Exact object under discussion | Correctness of implementation |
| Exact execution | Independent integers, `Fraction`, matrix and term equality | Per-input algebra under runtime semantics | Python/runtime correctness |
| Analytic numerics | Range reduction, series, tail, outward integer rounding | Conditional exact-real enclosure | Verified implementation |
| Bounded qualification | 494 tables, 5,928 direct event-expression checks, 72 live containments, and 975 exact-rational logarithm enclosures | Enumerated-domain agreement and fault finding | Universal correctness |
| Mutation evidence | 21 semantic, one fixed-point source, one event-extraction source, four cross-artifact binding, six structural, two transport/invocation, and 34 static-policy mutations/adversaries or controls | Sensitivity to named faults | Absence of unnamed faults |
| Binding | Manifest, lockfile, verifier-source hashes | Drift detection for named bytes | Authorship, binary identity, custody |
| Statistics | None | Nothing | Population or confidence claims |
| Application | None | Nothing | Downstream validity |

## Open formal bridges

### F1: Published semantics to finite specification

Formalize the two-source antichain event map, target restriction, averaged informative and
misinformative cumulatives, and the fixed lattice in a proof assistant. Prove that the frozen
formulas in [../conventions.md](../conventions.md) instantiate the published SxPID definition.

### F2: Canonical JSON bytes to exact table

Specify duplicate-key rejection, ASCII token grammar, canonical decimal counts, lexicographic row
order, and resource limits. Prove that accepted bytes decode to one unique exact count table.

### F3: Exact table to 24 expressions

Prove the event-count extractor, direct MI identities, Möbius inversion, zeta reconstruction, and
canonical term combination.

### F4: Rational logarithm checker

Machine-check:

- floor-log2 range reduction;
- the atanh series identity;
- the stated remainder bound;
- signed fixed-point floor/ceiling operations;
- finite-sum enclosure; and
- adaptive-precision termination or fail-closed exhaustion.

### F5: Checker refinement

Connect the executable verifier to F1–F4. Possible routes include:

- Lean definitions with an extracted or reflected checker;
- Rocq plus a small extracted checker;
- a verified integer kernel with proof-carrying results; or
- a second small-kernel checker that validates explicit rational-log proof objects.

Verus, Creusot, or Kani can strengthen Rust memory/index/resource properties, but they do not by
themselves establish transcendental enclosure or published semantic identity.

### F6: Independent proof checking and custody

Pin proof-assistant versions, dependency commits, proof-object hashes, checker output, verifier
source, and the exact claim revision. Have an independent party replay the proof and executable
qualification from a separately acquired source snapshot.

## Permitted formal-method statement

Current:

> The exact containment claim has an analytic proof and two executable arithmetic paths, one of
> which independently reconstructs expressions and proves interval subset containment.

Not current:

> The certifier or verifier is formally verified.
