# Previewing the proposed pid-rs 1.0 API in 0.9

pid-rs 0.9 is the published GitHub-only source-review prerelease for a proposed 1.0 API.
It narrows the default scientific surface without starting a 1.x compatibility promise. It does
not promote default-off research estimators to validated population measures.

The 0.9 review point is a GitHub-only source prerelease, not a crates.io, PyPI, or docs.rs
publication. Its source, proposed scope records, review provenance, and checksums are intended for
inspection and reviewer feedback. No 0.9 registry installation is available, no software DOI or
Zenodo record is assigned, and earlier release commits remain reachable through immutable changelog
links after obsolete tag refs were retired. The heavyweight
signed-review and registry workflow is reserved for a later qualification.

## Toolchain and dependency changes

- The minimum supported Rust version is now **1.89** (formerly 1.83).
- `nalgebra` 0.35 / `simba` 0.10 replaces the 0.33/0.9 line. This removes the unmaintained
  transitive `paste` crate and lets `cargo-deny` run without advisory exceptions.
- All workspace crates and the `pid-core-rs` Python distribution are version 0.9.0.
- Any later registry qualification must resolve `pid-runlog` before `pid-core`; publish
  `pid-runlog` first and wait for the target index before qualifying `pid-core`.

Inspect the exact GitHub prerelease source with Rust 1.89 or newer:

```text
git clone https://github.com/sepahead/pid-rs.git
cd pid-rs
git checkout --detach v0.9.0
cargo check --locked
```

## Stable and experimental features

`pid-core` has an empty default feature set. The default build contains empirical categorical
estimators, fitted quantization, conditional report-first Euclidean KSG MI, and general
diagnostics. Research families require an explicit feature:

| Feature | Status |
|---|---|
| `parallel` | Stable exact data-parallel backend; output must be bit-identical to serial. |
| `experimental-continuous` | Continuous shared exclusions/PID2 and partial continuous PID3. |
| `experimental-hyperbolic` | Research-only Lorentz-hyperbolic pairwise KSG. |
| `experimental-heuristics` | Research-only heuristic shared-exclusions methods. |
| `experimental-hierarchy` | Research-only hierarchy helpers. |
| `research-mixed-dimension-pid3` | Full 18-atom continuous PID3 reference reproduction. |
| `experimental-pipelines` | Target-adaptive and continuous PID research pipelines. |
| `experimental-all` | Convenience union for testing, not an endorsement for scientific use. |

Do not enable `experimental-all` in a reusable library merely to recover old imports. Select the
smallest feature and preserve its status in saved output and downstream documentation.

A default Python wheel built locally from the review source exposes only stable functions. An
explicitly experimental source build uses the `python-experimental` Cargo feature; do not
redistribute it under a stable wheel label.

## Categorical and quantized inputs

`discrete_sxpid2/3/n` now accepts `DiscreteMatRef`: signed integer values are category labels and
only row equality matters. Code that intended numeric equal-width binning must call the explicitly
quantized APIs or fit a reusable quantizer on training data and transform held-out data with its
recorded edges.

Never refit bin edges separately on evaluation folds. Persist edges, occupancy, training-data
provenance, and the input encoding with the result. Quantized PID is PID of the quantized variables,
not an approximation whose bin count can be omitted from the estimand.

## Continuous estimates

- Bare default continuous configurations are intentionally non-runnable. Make the population-law
  assertion explicit with the appropriate support constructor.
- KSG estimates are signed by default. Clamp only as a presentation transform and never before a
  PID or Shannon identity.
- Use report-returning entry points for saved, compared, or published values. Scalar compatibility
  functions are not the publication path.
- Positive tied k-th-neighbour shells and zero radii fail closed. Do not treat jitter as a generic
  repair; added noise changes the estimand.
- Continuous shared exclusions/PID2 is experimental and requires equal source ambient dimensions.
  Equality is necessary for the implemented small-ball gauge, not proof of compatible intrinsic
  geometry.
- `pid2_isx_report` now retains the complete three KSG constituent reports, complete ISX local
  diagnostics, aligned local-contribution covariance, and atom cancellation metrics. That
  covariance is descriptive, not calibrated sampling uncertainty. Use the split-sample/cross-fit
  report helpers with explicit split identities; fold-specific coordinates are returned separately
  and are never pooled.
- Continuous pairwise/triplet co-information has report-first entry points retaining every KSG
  constituent and cancellation diagnostics. User-facing hierarchy fields and selection variants
  now spell out `co_information`; migrate old `ci`-abbreviated field/variant names.
- Average redundancy/vulnerability helpers now return `NormalizedInvariantReport`, not a bare
  floating-point ratio. Read `value` only when `status` is `Defined`; otherwise retain the typed
  reason and the explicit `NormalizedInvariantPolicy` denominator threshold in serialized output.
- Partial continuous PID3 reports unavailable dependencies. Full continuous PID3 is inaccessible
  without `research-mixed-dimension-pid3` and remains research-only.

## Preprocessing and inference

- Fit `Standardizer`, PCA, PLS, and quantizers on training rows, then reuse the fitted object on
  held-out evaluation rows. `Standardizer::fit` requires an explicit choice among
  `Drop`, `Error`, `Zero`, and `LeaveCentered` for constant columns. Persist the fitted
  training/parameter hashes exposed by standardizer, PCA,
  CountSketch, and PLS objects.
- Same-sample supervised PLS→PID is exploratory and requires an explicit acknowledgement on its
  research feature.
- Experimental hierarchy PID evaluation now requires distinct screening/evaluation inputs and
  split identities; same-sample hierarchy APIs are screening-only and return no post-selection
  p-values.
- Generic resampling callbacks are fallible and resource-declared. Supply a typed dependence model
  and block-length-selection declaration; summaries retain every failure and do not summarize a
  selectively successful subset. Random-origin kNN subsample percentiles are diagnostics, not
  calibrated confidence intervals.
- Permutation outputs retain a typed null assumption, calibration class, family definition, seed,
  algorithm revision, scheme, and signed tail. Failed transforms make the predeclared tail fraction
  unavailable instead of silently shrinking its denominator.
- Long-running experimental resampling, permutation, PLS-CV/fit, and logistic-fit paths expose
  cooperative cancellation and return `PidError::Cancelled` without partial numerical output.

## Python outputs

The proposed future registry wheel uses typed result classes/stubs for the stable surface and
structured exceptions for configuration, support, resource, and numerical failures. There is no
0.9.0 PyPI wheel. When evaluating a wheel built locally from the review source, replace code that
relies on untyped dictionary key discovery with declared attributes or the documented serialized
representation. Long-running calls operate on owned/immutable inputs before releasing the GIL; do
not depend on concurrent mutation of an input NumPy buffer.

## Run-log compatibility

Schema-1 compatibility hashes remain readable. New output identifies the hash algorithm and
generation explicitly and uses bounded streaming parsing plus atomic durable sidecar replacement.
Prefer the newest lossless replay/logical hash fields. Run-log hashes establish internal
consistency only; anchor a release/run digest in a trusted signed system when authentication is
required.

## Migration checklist

1. Upgrade Rust to 1.89 or newer and regenerate the lockfile.
2. Remove broad experimental features; add back only the research family actually reviewed.
3. Replace numeric “categorical” inputs with `DiscreteMatRef` or an explicit fitted quantizer.
4. Replace saved scalar continuous values with structured reports and required provenance.
5. Recheck signed-negative handling, support assertions, PLS splits, and inference assumptions.
6. Run default, no-default, selected-feature, all-feature, and Python parity tests.
7. Read [known limitations](KNOWN_LIMITATIONS.md) and record which assumptions apply downstream.
