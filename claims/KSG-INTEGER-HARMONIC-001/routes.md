# Route registry for KSG-INTEGER-HARMONIC-001 revision 1

| Route | Family | Independent starting point | Current result | Shared dependency | State |
|---|---|---|---|---|---|
| R-MATH | symbolic/special-function | positive-integer digamma recurrence | exact source-symmetric harmonic range reduction with mapped indices | correct runtime count construction | complete for the exact reduction |
| R-DECIMAL | computational high precision | standard-library `Decimal` harmonic sums | existing 8,198-cell oracle; current runtime maximum recorded as 96 binary64 epsilons | harmonic identity | complete for its bounded corpus |
| R-RATIONAL | exact finite algebra | `Fraction`/small-denominator harmonic values | zero failures over all 6,920 feasible tuples through `n=16`; generator self-tests include `11/6`, `5/6`, and `-1/3` | integer index map | complete for the bounded domain |
| R-BINARY64 | numerical implementation | compensated positive harmonic prefix plus source-symmetric range subtraction | final-source checker observes an 8-epsilon maximum and zero count-swap bit asymmetries on the 8,198-cell corpus | fixture correctness and exact index map | bounded checker complete; final Rust replay open |
| R-ADVERSARY | mutation/boundary | off-by-one, coefficient, compensation, decoy, heuristic, runtime-identity, and release-family under/over-migration attacks | 85 baseline-first mutations rejected: 3 checker, 16 source/runtime, 30 affected-family, and 36 protected-family faults; every mutation runs in normal and optimized checker modes, and the top-level self-test passes normally and under `python -O` | bounded source/checker/release markers | complete for named faults; final behavior replay open |

The earlier 16-epsilon observation used a compensated direct four-term harmonic expression. The
selected source-symmetric range expression instead observes eight epsilons on the same corpus and
is symmetric in the two count arguments by construction. Both are finite diagnostic observations;
neither is a universal rounding theorem.

The mathematical and Decimal routes are not independent at the harmonic identity. The rational
boundary route is directed specifically at that common cut and at the off-by-one map. Model review
is advisory attack generation and is not listed as an evidence route.
