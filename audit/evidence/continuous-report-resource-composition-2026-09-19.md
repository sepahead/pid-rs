# Complete continuous-report resource composition

Complete PID2 and co-information reports must budget the KSG reports they execute. The previous
preflight used a lighter scalar calculation for concatenated sources. This could admit a report
whose constituent pair-work estimates exceeded the caller's aggregate ceiling.

This is a correction to a project-defined engineering contract. PID2 still combines Ehrlich
continuous shared-exclusions redundancy with KSG mutual information. Co-information remains a
Shannon invariant, not a PID. No estimator formula, information unit, support assumption or
public declaration changes.

## Defect and correction

Let all inputs have the same number of rows, `n`, and write `P = n(n−1)/2`. Here `P` is one
triangular pair-work accounting unit. It is not a count of all metric calls or CPU instructions.

An ordinary KSG report includes four such units: estimation, source diagnostics, target
diagnostics and joint diagnostics. The scalar block calculation includes one. The complete
report paths allocate a concatenated source matrix and execute ordinary KSG reports, but their
preflight used the scalar block estimate for those terms.

| Complete report | Previous aggregate | Constituent report total |
| --- | --- | --- |
| Two-source PID2 | `4P + 4P + P + P = 10P` | `4P + 4P + 4P + P = 13P` |
| Pairwise co-information | `4P + 4P + P = 9P` | `3 × 4P = 12P` |
| Triplet co-information | `3 × 4P + 4 × P = 16P` | `7 × 4P = 28P` |

The final PID2 term is the ISX report's accounting unit. Its presence does not make the KSG
diagnostics part of the shared-exclusions definition.

The correction shares the ordinary KSG resource calculation through matrix shapes. Thus
preflight can compute the cost of the joined source without first allocating it. It includes
the same diagnostics, retained report data, operation hints and feature-dependent worker
storage as an explicit concatenation. The existing scalar block route stays separate.

The affected implementation is in [KSG preflight](../../crates/pid-core/src/ksg.rs) and
[support-diagnostic preflight](../../crates/pid-core/src/support.rs). Their callers are
[complete PID2 and cross-fit reports](../../crates/pid-core/src/pid2.rs) and
[complete co-information reports](../../crates/pid-core/src/ci.rs).

## Reproduced failure and regression

Before the correction, commit `1f90056921664c5d7f43a138daeaffaddbe128de` produced a complete
eight-row PID2 report with aggregate pair work `280` and constituent pair work `364`. A caller
ceiling of `280` was accepted. The native Rust reproduction then failed its assertion that the
constituent total fit that ceiling.

The fixed regression uses the deterministic eight-row fixture in
[continuous resource tests](../../crates/pid-core/tests/continuous_resource_contracts.rs).
It requires a ceiling of `363` to reject with requested work `364`, and a ceiling of `364` to
accept. Other resource ceilings are permissive, and the normal input/configuration checks apply.
The explicit continuous-model constructor selects the code path; these test rows establish no
population-support, independence or calibration result.

The KSG unit regression compares all three resource fields for block-shaped preflight and
explicit concatenation, across three row/dimension settings and thread requests of one and
three. [Complete-report tests](../../crates/pid-core/tests/continuous_reports.rs) also compare
co-information aggregate work with every retained constituent. Both serial and parallel
feature configurations pass the focused tests.

Operation hints include matrix copying in addition to constituent work. For scalar source
columns, the pairwise report copies `2n` elements. The triplet report copies `2n + 2n + 2n +
2n + 3n = 11n` elements: XY, XZ, YZ, a second XY, then XYZ. An initial test omitted this term
and failed with `105120` versus `105048` at `n = 36`. The difference, `72 = 2n`, identified
the incorrect test expectation. The retained regression requires the exact constituent sum
plus copying; production copying costs were not removed to satisfy the test.

## Alternatives and limits

A pair-work-only correction would leave operation and memory estimates on the wrong route.
Allocating the concatenation before aggregate admission would spend memory before that check.
Duplicating the ordinary formulas would permit future drift. A shared shape calculation fixes
the composition while keeping numerical execution intact. Replacing report execution with a
new block-native report or adding a runtime allocator ledger would require separate contracts.

Memory estimates deliberately sum conservative constituent storage allowances because reports
and local terms remain alive together. Correcting the component formula does not establish an
observed resident-memory ceiling breach in the old code, or a hard operating-system memory bound
in the corrected code. Operation hints remain engineering estimates.

Galadriel has a pinned historical regression that records the upstream undercount. A future
dependency update must preserve that witness and replace its active expectation with corrected
aggregate equality. This correction does not modify an externally owned Galadriel checkout or
qualify its data model, thresholds or deployment.
