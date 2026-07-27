# Obligations for KSG-INTEGER-HARMONIC-001 revision 1

## AND/OR graph

```text
M1 integer digamma theorem ----+
                               AND--> M2 exact four-term reduction
C1 call-site coefficient map --+

M2 --+                         +--> E2 bounded Decimal containment
     AND--> E1 harmonic table -+--> E3 boundary/property tests
C1 --+                         +--> E4 serial/parallel and feature parity

E2 + E3 + E4 + D1 scoped docs/catalog + R1 resource parity
  --> revision-1 implementation decision
```

The minimal shared critical cut set is `M2` plus `C1`: every accepted implementation route relies
on the exact index map and on classifying only genuinely coefficient-cancelling call sites. The
Decimal oracle is independent of Rust arithmetic but shares the mathematical identity; exact
rational spot checks attack that shared node separately.

## Obligation table

| ID | Obligation | State | Completion evidence |
|---|---|---|---|
| M1 | Establish $\psi(m)=H_{m-1}-\gamma$ for positive integers. | closed | recurrence/base derivation in `call-site-map.md` |
| M2 | Cancel the four Euler constants and bind every off-by-one index. | closed | symbolic range derivation, exact rational replay through `n=16`, and three retained boundary values |
| C1 | Inventory every runtime digamma combination; retain the noninteger/non-cancelling path wherever required. | closed before implementation | `call-site-map.md`; the coefficient-sum-two heuristic remains explicitly excluded |
| E1 | Implement deterministic compensated harmonic prefixes without changing neighbor counts or public types. | implemented; final Rust replay open | Neumaier prefix, source-symmetric range helper, direct call-site review, and focused tests |
| E2 | Replay the complete committed 8,198-case Decimal corpus and freeze observed/allowed error honestly. | checker closed; final Rust replay open | observed maximum `8*EPSILON`, allowed finite-corpus ceiling `32*EPSILON`, unchanged fixture digest |
| E3 | Cover $k=1$, $k=n-1$, sparse/dense counts, symmetry in `nx/ny`, off-by-one faults, and release-family under/over-migration. | checker/self-test closed; final Rust replay open | 6,920 exact tuples, boundary tests, and 85 baseline-first mutations: 3 checker, 16 source/runtime, 30 affected-family, and 36 protected-family faults; every mutation is rejected in normal and optimized checker modes, and the top-level self-test passes normally and under `python -O` |
| E4 | Preserve serial/parallel bit identity and every affected feature path. | open | stable, parallel, all-feature, and release tests |
| R1 | Preserve or conservatively update memory/work preflight. | source analysis closed; final tests open | same `8*(n+1)` table shape, renamed resource term, resource-contract replay |
| I1 | Migrate runtime and release-family estimator identities without changing definition revisions. | runtime v4 and release-scope binding implemented; final catalog/software-identity replay open | KSG/ISX report assertions plus exact 15-family release checker and mutations; four families carry combined v2 labels for the separately scoped represented-input PID2 synergy correction |
| D1 | Update source docs, README validation wording, changelog, catalog/evidence paths, and generated views if their claims change. | active | coherence checkers |
| S1 | Keep statistical/support/downstream claims unchanged. | active | adversarial documentation review |
| X1 | Obtain and independently adjudicate dedicated external adversarial reviews. | open | retained Fable/Opus receipts; model prose remains advisory |

## Exceptional cases

- `k=0`, `k>=n`, zero arguments, and out-of-range counts remain rejected by caller validation.
- A zero local term is permitted and must not be reinterpreted as a statistical null.
- Large nearly cancelling harmonic values can still lose binary64 bits; bounded fixture agreement
  is not a universal enclosure.
- Non-cancelling experimental heuristics retain their separately reviewed digamma semantics.
