# Historical numerical-claim witnesses

Status: **inert historical positive/negative witness archive; superseded where stated**.

This directory preserves eleven exact Markdown witnesses from snapshot
`86faa9a0850ca416f54a467230106b01d4162687` (tree
`4f6fddb80754645cf6fa0fa48cdb82db457bb478`). Four concern categorical
Williams--Beer `I_min` represented arithmetic; seven concern the project-defined
binary64 construction and compatibility guard around continuous PID2 coordinates.
The payload bytes are historical records, not current claim authority.

## Current successor map

| Historical group | What remains useful | Current successor evidence |
|---|---|---|
| `IMIN-TIE-SWAP-001` exact-tie and minimal source-swap witnesses | Exact count tables, source-order residual, wrapper reach, and the distinction between an internal binary64 branch and public scalar equivariance | `NUMERICAL_ASSURANCE.md` section 4.4; `crates/pid-core/tests/imin.rs`; `crates/pid-core/tests/imin_numerical_boundary.rs` |
| `IMIN-TIE-SWAP-001` Python-coverage correction | A test file is not wheel execution, and stable versus migration bindings need separate coverage | `crates/pid-python/tests/test_v1.py`; `crates/pid-python/tests/test_experimental_migration.py` |
| `IMIN-TIE-SWAP-001` rounding-carry correction | The correct halfway vector is `nextDown(2)+2^-53 -> 2`, not the rejected `2^-54` vector | `scripts/generate-exact-binary64-sum-oracle.py`; its frozen snapshot and generated fixture |
| `PID2-REPRESENTED-SUM-001` arithmetic and guard witnesses | Source-order residuals, exact-versus-historical compensation, fail-closed identity boundaries, overflow, and diagnostic routing | `PID2_REPRESENTED_COORDINATE_ASSURANCE.md`; `NUMERICAL_ASSURANCE.md`; `crates/pid-core/src/pid2.rs`; `crates/pid-core/tests/pid2.rs`; `scripts/check-pid2-represented-coordinate-v4.py` and its hostile suite |

The historical file `neumaier-guard-discriminator-open.md` is especially important
to interpret by date. Its bounded search did not find a discriminator and therefore
correctly left global exact-versus-Neumaier guard equivalence open at that time.
Current section 5.5 of `PID2_REPRESENTED_COORDINATE_ASSURANCE.md` supplies a different,
explicit four-coordinate overflow witness: exact atom reconstruction equals `J`,
whereas the declared Neumaier trace ends in NaN. That new witness narrowly supersedes
the old global-equivalence uncertainty. It does not invalidate the historical search,
make Neumaier summation generally unsound, or establish an estimator or PID defect.

## Boundaries

These records concern empirical tables or represented binary64 arithmetic under their
stated inputs. Synthetic PID2 coordinate tuples are not evidence that an Ehrlich/KSG
estimator or a probability law emits those tuples. A constructor rejection at an
overflow boundary is not a defect in the exact-real Makkeh--Gutknecht--Wibral or
Ehrlich shared-exclusions definitions. The archive proves no population, calibration,
frequency, portability, or universal floating-point theorem.

Run the archive-integrity checker in normal and optimized Python. It validates exact
bytes only; it does not promote historical prose into the active method catalog.
