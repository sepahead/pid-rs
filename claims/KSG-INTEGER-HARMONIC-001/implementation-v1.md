# Implementation checkpoint for KSG-INTEGER-HARMONIC-001 revision 1

## Implemented source

- `stats.rs` now builds `table[m]=H_(m-1)` with deterministic Neumaier compensation and evaluates
  the exact-real-equivalent source-symmetric range
  `(H_(n-1)-H_(max(x,y)-1))-(H_(min(x,y)-1)-H_(k-1))`.
- Ordinary KSG tree/brute and x-block tree/brute paths pass exclusive counts as `nx+1,ny+1`.
- Ehrlich ISX and the direct PID3 redundancy path pass their anchor-inclusive counts directly.
- The non-cancelling heuristic retains the general digamma path; its coefficient sum is two, so
  cancelling Euler's constant there would change the method.
- KSG and ISX runtime estimator revisions are
  `strict-unique-shell-integer-harmonic-report-v4` and
  `strict-unique-shell-integer-harmonic-isx-v4`.

Four of the 15 KSG-transitive release families also expose the separately adjudicated
`PID2-REPRESENTED-SUM-001` revision-2 correction, so their final v2 estimator revisions name both
integer-harmonic inputs and represented-input exact PID2 synergy summation: continuous PID2,
ISX heuristics, hierarchy, and PID2 screening. The heuristics family is included because its
listed experimental Python `compute_pid2` binding routes heuristic redundancy through the common
`Pid2Result` constructor; standalone Rust heuristic redundancy scalars are unchanged by that
PID2 correction.

No public declaration signature, neighbor-shell rule, support contract, definition revision, or
scientific origin changed.

## Targeted non-Cargo evidence

The production checker passes exact rational replay on 6,920 tuples and the unchanged 8,198-cell
Decimal corpus with observed maximum `8*f64::EPSILON`, a frozen `32*f64::EPSILON` finite-corpus
ceiling, and zero `x/y` swap bit asymmetries. Its baseline-first self-test rejects 85 named
mutations: three checker faults; 16 compensation, range, index, comment/string-decoy, heuristic,
call-site, and stale-runtime-identity source faults; 30 affected-family faults comprising one stale
estimator revision and one changed definition revision for each of the 15 emitting families; and
36 protected-family over-bumps comprising both estimator and definition changes for each of the 18
excluded families. Every mutation is replayed through both normal and optimized checker execution,
and the top-level self-test itself passes under normal and optimized Python.

This evidence is bounded. It does not prove universal correct rounding, KSG consistency, neighbor
correctness, population support, calibration, or downstream suitability.

## Open integration

Rust behavior, serial/parallel fixtures, every feature profile, release mode, resource contracts,
catalog identity, Python reports, external model attacks, and final software identity remain open.
The exact 15-family release-scope migration and its 85-mutation checker route are complete on the
current bytes. Cargo execution at this checkpoint is blocked before compilation by the
deliberately provisional method-catalog digest. The identity boundary will be rebound only after
shared catalog and release bytes settle.
