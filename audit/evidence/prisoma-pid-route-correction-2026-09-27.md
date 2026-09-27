# Prisoma categorical-route correction — 27 September 2026

Author: Sepehr Mahmoudian.

The September [session handoff](../../SESSION_HANDOFF.md) incorrectly described Prisoma's
categorical screen at `be1c492` as Williams–Beer $I_{\min}$. Inspection of the exact source
shows a fitted-quantized Makkeh–Gutknecht–Wibral (MGW) shared-exclusions PID2 route. This correction
changes the method identification. It supplies no new estimator validation or application result.

## Exact sources

All rows refer to `crates/pid-sim/src/offline_harness.rs` in `sepahead/prisoma`.
The September file is byte-identical in the two listed commits. The later commit was read from a
locally cached remote ref; no current remote-main or deployed-state claim follows.

| Commit | File SHA-256 | Route inspected |
|---|---|---|
| [879a190](https://github.com/sepahead/prisoma/blob/879a1909a986bda381f86979b5c02e3cec89d68c/crates/pid-sim/src/offline_harness.rs) | `4f2f8da680d2248ca6cd2a05a370a15942f60f1f24b316fd08343e5666f5d21d` | `imin_pid2`, with the `quantized_imin_pid2` label |
| [be1c492](https://github.com/sepahead/prisoma/blob/be1c492a88574805da12ceb2a8e6fa057c8c4eba/crates/pid-sim/src/offline_harness.rs) | `4c077f95454b8f1d70dd793becee1646fc4423d5ad50dde5bd9845f810b3bd12` | `fitted_quantized_sxpid2_with_budget`, with the MGW averaged categorical PID2 label |
| [2c229fc](https://github.com/sepahead/prisoma/blob/2c229fc7eda40f85f24b68097a5de40b8db5e328/crates/pid-sim/src/offline_harness.rs) | `4c077f95454b8f1d70dd793becee1646fc4423d5ad50dde5bd9845f810b3bd12` | `fitted_quantized_sxpid2_with_budget`, with the MGW averaged categorical PID2 label |

The July [compatibility audit](../../ECOSYSTEM_COMPATIBILITY_AUDIT.md) and its
[PDF](../../output/pdf/ecosystem-compatibility-audit.pdf) bind the first commit. Their $I_{\min}$
statements remain correct for that source. Replacing them with MGW would falsify the historical
comparison. The mistaken September statement remains recoverable in prior commits; the active
handoff now carries this dated correction.

## Interpretation and limits

At the two September revisions, the categorical method and estimator strings name MGW shared
exclusions. The computation calls `fitted_quantized_sxpid2_with_budget`; it does not call
`imin_pid2`. The recorded relation for `CategoricalSx` is
`same_rows_fitted_quantization_descriptive`. `CategoricalSxPls` instead records
`same_rows_target_supervised_projection_and_fitted_quantization_warning`.
The code explicitly treats quantization as a separately requested estimand, not a fallback after
continuous estimation fails.

Both inspected September revisions pin pid-rs at `796c11e70f009634b853dc4ada6f565563d82f51`. These source observations
do not establish compatibility with current pid-rs, population calibration, held-out performance,
or a useful control or fusion intervention. No consumer code, experiment, mathematical statement,
PDF or historical receipt changed for this correction. The separately requested continuous route
is an Ehrlich PID2 composition; its support and sampling assumptions remain separate from the
finite categorical route.

Root inspection and a separate source council checked the exact calls and evaluation labels.
Their shared Git objects and filesystem do not provide independent execution evidence. No new
consumer execution was performed. The correction follows source identity rather than a generic
PID name or a dependency pin alone.

Cite Sepehr Mahmoudian, *Prisoma categorical-route correction* (2026), with the exact pid-rs
commit containing this record. Use [CITATION.cff](../../CITATION.cff) for the software.
The linked consumer commits identify the inspected method routes;
[the method catalog](../../METHODS.md) gives the defining PID references and their boundaries.
