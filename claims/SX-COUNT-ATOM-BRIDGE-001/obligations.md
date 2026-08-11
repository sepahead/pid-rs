# Obligations for SX-COUNT-ATOM-BRIDGE-001 revision 1

> **Historical superseded obligation set.** These were the pre-integration requirements. The
> active closure ledger is [`obligations-v2.md`](obligations-v2.md).

## Acceptance rule

This packet is preliminary. A source-level theorem may be marked “implemented candidate” below,
but no obligation is closed merely because a declaration appears in a working tree. Acceptance
requires pinned kernel replay, exact source binding, negative semantic variations, rendered-PDF
verification, repository-wide scope coherence, and independent review.

## Obligation graph

```text
P0 publication/project boundary --------+
Q1 exact 24-coordinate surface ---------+
M1 Mobius/zeta inverse algebra ----------+--> A1 averaging commutes with Mobius
S1 coordinate-swap formula equivariance -+               |
C0 preserved count/event bridge --------------------------+
L1 all three local component arguments -------------------+
                                                            v
                                            E1 all-coordinate count equality
                                                            |
                                            P1 exact rational products
                                                            |
                                            G1 scaled-log and sign equivalences
                                                            |
           K1 kernel binding + K2 semantic variations + D1 scope/PDF + R1 review
                                                            |
                                                            v
                                               bounded acceptance decision
```

## Obligation table

| ID | Obligation | Current state | Candidate closure or required evidence |
|---|---|---|---|
| P0 | Separate paper-defined categorical quantities from the project-defined Lean transcription, coordinate order, and assurance composition. | documented candidate | `claim-v1.md`, `conventions.md`, public audit, and catalog review |
| Q1 | Fix four nodes, four atoms, three components, and a duplicate-free 24-coordinate order. | implemented candidate | `SxPid2Component`, `SxPid2Atom`, `SxPid2Coordinate`, order/cardinality theorems |
| M1 | Define concrete integer Möbius and zeta coefficients; prove both transforms are inverse and prove the reconstruction identities. | implemented candidate | coefficient, row-sum, inverse, joint-sum, and source reconstruction theorems |
| S1 | Fix exchange of source-labelled coordinate positions and prove involution and Möbius formula equivariance for an arbitrary four-entry cumulative function; claim no transport of source types, keys, counts, laws, or events. | implemented candidate | `sxPid2SwapNode`, `sxPid2SwapAtom`, and associated theorems |
| C0 | Reuse the completed supplied-count event semantics without widening its input boundary. | preserved dependency | `SX-COUNT-EVENT-BRIDGE-001` revision 2 and `TwoSourceCountEventBridge.lean` |
| L1 | Define informative, misinformative, and net local/averaged cumulatives; prove net subtraction and supported exact count-argument logarithms. | implemented candidate | component selectors, positivity, ratio, and local empirical-log theorems |
| A1 | Prove that finite positive-mass averaging of pointwise atoms equals Möbius inversion of averaged cumulatives for every component and atom. | implemented candidate | `averaged_pointwise_atom_eq_mobius_of_averaged_cumulatives` |
| E1 | Prove supplied-count equality for every cumulative and atom coordinate. | implemented candidate | cumulative, atom, and quantified all-24 count-expression theorems |
| P1 | Construct positive real and exact rational products for every coordinate and prove cast agreement. | implemented candidate | cumulative/atom/coordinate product positivity and cast theorems |
| G1 | Prove `(1/N) log R` normalization and exact positive, negative, and zero equivalences for every coordinate. | implemented candidate | scaled-log and three quantified sign theorems |
| K1 | Pin the exact Lean toolchain/dependencies, source bytes, ordered declarations, imports, and permitted axiom basis; replay normally and with optimized Python. | pending | kernel checker and reproducible evidence receipt |
| K2 | Show the gate rejects meaningful changes to order, coefficients, component selection, target restriction, support, averaging, products, signs, and residual scope. | pending | baseline-first static and isolated semantic variations |
| D1 | Bind the bounded claim into the method catalog, generated method view, assurance registry, public formal maps, limitations, changelog, and deterministic Markdown/LaTeX/PDF pair. | pending | repository integration changes and all corresponding checkers |
| R1 | Obtain independent mathematical, formal, provenance, executable-boundary, and PDF review. | pending | review records with every material concern resolved or retained |

## Required negative semantic variations

The gate design should include at least these distinct classes, without relying on name matching
alone:

1. swap source-one and source-two positions in only one order or coefficient table;
2. replace redundancy's source-event union with a different event operation;
3. erase the target restriction from a misinformative argument;
4. replace the joint cumulative with one marginal in the synergy row;
5. change a Möbius sign while retaining a type-correct theorem name;
6. weaken an inverse theorem to a reflexive or single-coordinate statement;
7. omit one component or duplicate one coordinate in the ordered surface;
8. average over all keys rather than positive support;
9. replace empirical weights `c(z)/N` by uniform support weights;
10. change net from informative minus misinformative to addition;
11. remove one exponent `c(z)` from a product;
12. replace an atom-product quotient with multiplication;
13. reverse one exact sign comparison;
14. remove positivity needed by a logarithm identity; and
15. widen documentation to a Rust, component-nonnegativity, statistical, or higher-source claim.

This list is a minimum review specification, not a claim that the future suite is exhaustive.

## Residual cut after candidate mathematical closure

Even if Q1 through G1 replay successfully, the following remain open:

- rows/bytes/files to exact counts;
- Rust node, atom, accumulation, binary64, and output refinement;
- standalone-certifier and Python refinement;
- parser, overflow, allocation, cancellation, and resource semantics;
- informative/misinformative atom nonnegativity;
- sampling and population statements; and
- three-source and general higher-source constructions.

No acceptance decision may silently treat these residual edges as prerequisites already proved.
