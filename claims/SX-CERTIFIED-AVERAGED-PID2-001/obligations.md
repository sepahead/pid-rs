# Obligations for SX-CERTIFIED-AVERAGED-PID2-001

## Status terms

- **Closed analytically:** an exact prose argument closes the mathematical implication, conditional
  on its explicit trusted primitives.
- **Closed by exact replay:** executable checks recompute the obligation using exact integers or
  rationals on the stated input.
- **Qualified bounded:** the retained corpus or mutation suite covers its exact finite domain, but
  is not a universal proof.
- **Partial:** retained evidence proves only the listed subclaims.
- **Open:** no retained evidence closes the obligation.
- **External:** closure requires independent actors or infrastructure outside this worktree.
- **Out of scope:** a separate claim packet is required.

## Obligation graph

```text
P1 published SxPID provenance
  -> S1 fixed two-source event semantics
  -> E1 exact count-event reconstruction

B1 strict input/schema binding
  -> E1 exact count-event reconstruction

L1 fixed lattice + inverse algebra
E1 + L1
  -> X1 all 24 exact log-linear expressions

R1 rational logarithm range reduction
R2 positive-series tail bound
R3 outward fixed-point arithmetic
R1 + R2 + R3
  -> N1 independent exact-real enclosure

C1 strict certificate/schema/digest binding
X1 + N1 + C1
  -> I1 24 coordinate containments

Q1 exhaustive small-table replay
Q2 live producer/verifier containment replay
Q3 fail-closed negative controls
  -> D1 bounded implementation qualification

I1 + D1
  -> Z1 conditional claim adjudication

F1 kernel-checked verifier refinement
A1 committed repository-source identity
H1 independent-human custody
  -> stronger external/formal assurance, not imported into Z1
```

## Detailed obligations

| ID | Obligation | Status | Completion evidence | Remaining boundary |
|---|---|---|---|---|
| P1 | Identify the primary source for categorical SxPID event semantics and averaging. | Closed for provenance | [bindings.md](bindings.md), producer README, and the cited Makkeh et al. paper | Citation does not prove transcription |
| S1 | Freeze the two-source source events, redundancy disjunction, target intersection, component formulas, node order, and atom order. | Closed analytically | [conventions.md](conventions.md) and fixed identifiers in both implementations | No kernel-checked bibliographic refinement |
| B1 | Strictly parse one canonical count table and reject ambiguous or unsupported encodings. | Closed by exact replay for the implementation | Producer schema tests and verifier structural rejection tests | Parser/runtime correctness remains trusted |
| E1 | Reconstruct every event mass and the 12 cumulative expressions from exact integer counts. | Closed by exact replay, conditional on implementation | `src/extract.rs`, independent `reconstruct_coordinates`, 5,928 direct row-scan event-expression identities, exact positive-mass and net-ratio checks | No deductive source-to-byte refinement |
| L1 | Fix $M$ and $Z$, prove $ZM=I_4$, and reconstruct all atoms/cumulatives in all three components. | Closed by exact replay | `src/lattice2.rs`, independent integer-matrix check, exact zeta arithmetic self-consistency checks | Correct node/atom semantic identification remains a premise |
| X1 | Produce exactly the 24 stated canonical exact log-linear expressions and match every certificate term/identity/digest to independent reconstruction. | Closed by exact replay for accepted pairs | Independent verifier structure and term equality checks | Verifier implementation correctness remains trusted |
| R1 | Prove exact range reduction $x=2^e y$, $1\le y<2$. | Closed analytically and replayed | Verifier derivation and rational grid checks for numerators/denominators 1 through 96 | Python `Fraction` semantics trusted |
| R2 | Prove the positive atanh-series tail enclosure for $0\le z\le1/3$. | Closed analytically | Full geometric-tail derivation in the assurance paper, [conventions.md](conventions.md), and verifier implementation | Not kernel checked |
| R3 | Ensure every fixed-point multiplication/division and finite-sum operation rounds outward, including negative coefficients. | Closed analytically; implementation partial | Exact floor/ceiling recurrence and induction in the assurance paper, reciprocal/power identity checks, containment replay | No verified compilation/runtime |
| N1 | Independently enclose every exact log-linear expression without trusting producer arithmetic. | Closed analytically, conditional on R1–R3 and verifier correctness | `verify_certificate.py` | Python runtime and verifier source remain trusted |
| C1 | Treat every certificate field as untrusted; enforce exact schema, type, digest, lattice, resource, precision, source, and claim-boundary equality. | Closed by exact replay for registered cases | Strict verifier checks and resealed mutation suite | Unenumerated parser/logic faults remain possible |
| I1 | Accept only when the independent enclosure is a subset of the producer interval for each of 24 coordinates. | Closed by exact replay for three live certificates; analytically implied for any accepted pair | 72 live containments and verifier acceptance logic | Universal implementation correctness is not proved by three samples |
| Q1 | Exhaustively reconstruct all binary count tables with total $N\le4$. | Qualified bounded | 494 tables, 11,856 coordinates, 1,482 direct-MI identities, and 5,928 direct row-scan event-expression identities | No inference beyond that finite domain |
| Q2 | Replay producer and independent verifier on singleton, XOR, and asymmetric sparse tables. | Qualified bounded | 72 containments proved on 2026-07-24 | Three tables are not universal evidence |
| Q3 | Reject registered structural, semantic, arithmetic-evidence, resource, and binding mutations. | Qualified bounded | 21 verifier semantic mutations, one fixed-point source mutation, one event-extraction source mutation, four cross-artifact binding adversaries, six structural adversaries, two transport/invocation controls, and 34 static-policy mutations | Mutation adequacy is not program verification |
| D1 | Establish implementation fault sensitivity and independently varied route agreement. | Qualified bounded | Q1–Q3 and Rust tests | Unknown faults and common specification errors remain |
| Z1 | Adjudicate revision 1 without broadening it. | Conditionally supported | Exact argument, independent reconstruction/containment, bounded qualification, explicit exclusions | F1, H1, external transparency, and binary/custody evidence remain open |
| A1 | Bind the verifier and packet to committed repository-source identity. | Verifier sources bound; packet binding is satisfied only by a public commit whose tree contains these exact bytes | Verifier commit `b8b9a48b88cb28d812d8cbd70b8f999a3bac5a8e` and exact file hashes in [bindings.md](bindings.md); the packet identity is the first later public commit containing the final source-manifest value and packet bytes | Before publication the packet is not publicly retrievable; ordinary Git history is not an external transparency log, binary attestation, authorship proof, or independent custody record |
| F1 | Machine-check the complete byte-to-event-to-expression-to-enclosure verifier path. | Open | No such proof artifact | Candidate routes include Lean, Rocq, Verus/Creusot, or a small independently checked checker |
| H1 | Obtain independent-human custody, execution, and review. | External | None in this packet | Requires another person and retained custody record |
| P2 | Prove `pid-core` binary64 refinement. | Out of scope | None | Separate implementation/numerical claim |
| T1 | Prove population, sampling, consistency, calibration, or coverage results. | Out of scope | None | Separate statistical claim |
| A2 | Qualify downstream consumers and decisions. | Out of scope | None | Separate application claim |

## Required acceptance statement

The accepted wording is:

> The independent verifier conditionally proves interval containment for the exact averaged
> categorical SxPID2 expressions that it reconstructs from one canonical count table.

The following wording is prohibited:

- “the entire Rust implementation is formally verified”;
- “`pid-core` output is certified”;
- “the interval is a confidence interval”;
- “population SxPID is known”;
- “continuous PID is validated”; or
- “independent custody has been established.”
