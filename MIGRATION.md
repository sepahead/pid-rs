# Previewing the proposed pid-rs 1.0 API in 0.9

pid-rs 0.9 is the published GitHub-only source-review prerelease for a proposed 1.0 API.
It narrows the default scientific surface without starting a 1.x compatibility promise. It does
not promote default-off research estimators to validated population measures.

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** Before migrating a method name across
the stable/experimental boundary, consult [`METHODS.md`](METHODS.md) and its machine-readable
source [`method-catalog.json`](method-catalog.json). A namespace, binding, or status change does not
turn a paper-derived composition into a paper-defined estimator or turn project-defined
infrastructure into a scientific method.

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
| `experimental-hyperbolic` | Research-only Lorentz-hyperbolic KSG and geometry diagnostics. |
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

The former Rust `SxAtom` type has been replaced before the 1.0 API freeze by
`SxPointwiseAtom` and `SxAveragedAtom`. Numeric components are now read through
`informative_nats()`, `misinformative_nats()`, and the derived `net_nats()` accessor. There is no
compatibility alias because it would erase the distinction being introduced. Serialized atoms add
the revisioned project-defined `interpretation` envelope. Persisted JSON must rename atom keys
`informative`, `misinformative`, and `net` to `informative_nats`, `misinformative_nats`, and
`net_nats`. Pointwise records rename `prob` to `empirical_probability` and add the exact
`empirical_count` used to derive that probability. The envelope now names the
`shared_exclusions_sxpid` measure, requires the containing coordinate/realization record, and lists
six standalone non-inferences, including measure-independence and population-unbiasedness.

Stable Python similarly replaces `SxAtom` with `SxAveragedAtom` and exposes the immutable
`SxAtomInterpretation`. Migrate `isinstance(value, pid_core_rs.SxAtom)` to
`isinstance(value, pid_core_rs.SxAveragedAtom)` and retain `value.interpretation` whenever a result
is persisted or passed across a boundary. Experimental migration dictionaries remain numeric-only
compatibility output and cannot carry this contract.

The experimental `QuantizedSxPid2BootstrapResult` now exposes `summary_status` rather than four
bare `RowBootstrapStat` fields. On `Complete`, the boxed `SxPid2BootstrapAtomSummaries` value has
one named `SxAveragedAtomBootstrapStat` field per atom; the scalar summary remains available
through `.summary`. The box is an API-layout detail and does not change the all-or-none scientific
status. The wrapper records that
the component is `signed_net_nats`, separates the original-point/moving-block summary scope from
the averaged SxPID estimand, and retains `num_bins`, `alpha`, every replicate outcome, effective
resample length, scheme, dependence declaration, seed, and algorithm revision. A failed replicate
returns `UnavailableDueToFailedReplicate` with all outcomes instead of discarding them in an error.

`discrete_sxpid2/3/n` now accepts `DiscreteMatRef`: signed integer values are category labels and
only row equality matters. Code that intended numeric equal-width binning must call the explicitly
quantized APIs or fit a reusable quantizer on training data and transform held-out data with its
recorded edges.

Never refit bin edges separately on evaluation folds. Persist edges, occupancy, training-data
provenance, and the input encoding with the result. Quantized PID is PID of the quantized variables,
not an approximation whose bin count can be omitted from the estimand.

The default-off same-sample compatibility helpers now return
`ExploratorySameSampleQuantizedResult<T>`. Read `quantization.num_bins` alongside
`categorical_result`; `into_categorical_result()` is available only when the caller deliberately
discards the wrapper provenance. The inner stable encoding is `Categorical`, because it describes
the labels supplied to the categorical estimator rather than the feature-only transform that
created them.

The review-source quantization hash names and meanings changed before the first tag:

- Rust `training_data_hash` / Python `training_data_hash_sha256` became
  `training_input_hash` / `training_input_hash_sha256`.
- Rust `transformed_data_hash` / Python `transformed_data_hash_sha256` split into
  `transform_input_hash` / `transform_input_hash_sha256` for the exact evaluation `f64` bit
  pattern, and `categorical_output_hash` / `categorical_output_hash_sha256` for the resulting
  labels and shape.
- The three identities use different versioned hash domains. Do not compare a digest from one role
  to a digest from another, even when the underlying bytes happen to coincide.
- `QuantizerConfig::record_training_data_hash` and the matching Python keyword retain their old
  spelling, but now control only the optional training-input digest. Transform-input and
  categorical-output digests are always reported. Python's `quantized.values` is read-only; copy it
  explicitly before any downstream mutation.

## Continuous estimates

- Bare default continuous configurations are intentionally non-runnable. Make the population-law
  assertion explicit with the appropriate support constructor.
- KSG estimates are signed by default. Clamp only as a presentation transform and never before a
  PID or Shannon identity.
- Eligible positive-integer KSG local terms now use a compensated harmonic prefix and sorted
  two-range association. This changes internal binary64 association, so persisted estimates can
  change in their last bits. It does not change the public API, neighbor or shell rules, estimand,
  units, or the requirement to preserve signed inputs to PID/Shannon identities. The bounded
  revision-4 arithmetic corpus is not a universal numerical-error or estimator-validity result.
  Its `8 * f64::EPSILON`-nat corpus maximum uses a binary64-rounded stored reference and is attained
  on exactly 40 rows. Under the checker's stated Python `Decimal` directed-rounding semantics,
  including the fixed stress rows, the separately enclosed exact-rational maximum is below
  `9.761311 * f64::EPSILON` nats. Exact `Fraction(Decimal)` subtraction orders every one of the
  8,198 stored/exact-rounded reference pairs after canonical validation, and the compiled Rust
  test directly classifies the selected outputs as 354 positive zeros, no negative zeros, and
  7,844 nonzeros. Do not treat the two reference metrics as interchangeable or promote this
  fixed-corpus correspondence to a universal arithmetic, neighbor-count, estimator, support, or
  PID result. A helper evaluation's implementation-local purity also does not imply statistically
  independent observations.
- Use report-returning entry points for saved, compared, or published values. Scalar compatibility
  functions are not the publication path.
- Lorentz geometry no longer adds a feature-dependent variant to the stable `Metric`,
  `SupportContract`, report, or categorical-encoding types. Import `HyperbolicMetric` and the typed
  KSG/config/report, support-diagnostic, distance-matrix, distance-concentration,
  intrinsic-dimension, or four-point entry point from `experimental::hyperbolic`. Stable
  `KsgMiReport::curvature` and its reserved hyperbolic-dimension fields remain `None` in every
  feature profile; Lorentz reports carry concrete curvature and dimensions in
  `HyperbolicKsgMiReport`.
- Remove reads of `KsgMiReport::backend_fallback_occurred` (or the matching Python attribute).
  There is no fallback path: `neighbor_backend` names the selected implementation and a backend
  failure is returned as an error.
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
- Heuristic shared-exclusions formulas are project-defined research baselines; Lorentz KSG is a
  paper-derived research adaptation. Restoring an old import does not make either the cited
  shared-exclusions estimator or a proved manifold-MI estimator.
- `average_degree_of_redundancy` / `average_degree_of_vulnerability` are the target-conditioned
  cited $\bar r$ / $\bar v$ quantities. Do not migrate the project-defined target-free
  `red_degree_discrete` / `vul_degree_discrete`
  ($\mathrm{Red}^{\circ}$ / $\mathrm{Vul}^{\circ}$) as aliases for them.
- `SupportContract::AssumeRegularFullDimensional` no longer accepts one optional
  `intrinsic_dimension`. The contract asserts the required marginal and joint laws in their own
  ambient spaces; keep sample intrinsic-dimension estimates as separate diagnostics rather than a
  population-support declaration.

## Preprocessing and inference

- Migrate persisted uses of experimental `Jitter` to `GaussianNoiseTransform`. Construct a
  positive `GaussianNoiseSpecification`. Then add a purpose, input binding, and rationale with
  `GaussianNoiseDeclaration`. Use `GaussianNoiseStream` to bind all stream inputs to one matrix and
  workflow role. The consumed transform returns `GaussianNoiseApplicationResult`. Retain its
  report with the matrix.
- Do not encode an unmodified comparison as Gaussian noise with `standard_deviation = 0`.
  `GaussianNoiseSpecification` rejects zero. A complete scale study must bind its unmodified
  member, scale grid, stream-coupling policy, and probe reports in a higher-level trajectory.
- If noise follows fixed preprocessing, identify the transform and output units in
  `DeclaredAfterFixedPreprocessing`. Put the exact matrix hash in
  `GaussianNoiseInputBinding::ExactFixedPreprocessingOutput`. The transform rejects a different
  input. This check does not prove a valid fit split. Keep training and evaluation identities in
  the estimator report.
- Use one logical stream for each matrix and workflow role. For each resample, supply the exact
  `AfterDeclaredRowResampling` context. The report binds the caller-declared index digest and the
  input matrix separately. It does not prove that those indices produced that matrix.
- `RowResampleOutcome` now includes `resample_indices_hash_sha256`, and row-bootstrap provenance
  uses `V2SeparatedPerturbationStreams`. `BlockResamplingProvenance` now records
  `original_row_count`. Revision 2 keeps the row schedule fixed when the optional perturbation is
  absent or its scale or matrix width changes. It uses one perturbation substream for each
  replicate and input-matrix position. Do not compare revision-1 and revision-2 seeded values as
  if the numerical streams were unchanged.
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
- Long sampled four-point summaries and symmetric-distance matrices also have explicit
  `*_with_budget_and_cancellation` variants. Use them when a caller must be able to stop bounded
  diagnostic work cooperatively.

## Python outputs

The proposed future registry wheel uses typed result classes/stubs for the stable surface and
structured exceptions for configuration, support, resource, and numerical failures. There is no
0.9.0 PyPI wheel. When evaluating a wheel built locally from the review source, replace code that
relies on untyped dictionary key discovery with declared attributes or the documented serialized
representation. Long-running calls operate on owned/immutable inputs before releasing the GIL; do
not depend on concurrent mutation of an input NumPy buffer.

## Software identity and `exp0` provenance

Use top-level Rust `pid_core::software_identity()` or Python `pid_core_rs.software_identity()` when
recording the compiled core's identity. This is new project-defined software infrastructure with
local Rust/Python code and no defining estimator paper. It separates public Rust declaration
signature, source route, selected build context, forensic references, and explicit attestation
status.

`exp0` retains the JSON key `build_provenance`, but its value changed from the ad hoc
`crate_version` / `git_commit` / `rustc_version` / `features` object to the complete format-1
software-identity envelope. Update consumers to read `package_version`, the discriminated `source`
object, nullable `build.rustc_version`, and `build.enabled_features`. The envelope also adds
`public_rust_api_signature_identity`, `reference_artifacts`, and `attestation`; do not silently drop
them when preserving provenance. Because this value participates in `config_json`, the run-log
configuration hash intentionally changes across the migration.

Workspace Git, Cargo package metadata, and unavailable source routes have different fields and
semantics, so branch on `source.kind` rather than assuming a commit exists. Reference hashes cover
exact raw canonical repository-file bytes and `attestation` is `none`. Package builds may not
contain or re-verify those repository-relative files. Neither identity equality nor a hash match
establishes API compatibility, scientific/application validity, source/archive/executable equality,
authenticity, or cross-platform numerical identity.

For workspace Git, also branch on `source.working_tree`: any effective `filter` attribute on a
tracked package path (including unset or unconfigured values), `attr.tree`, tracked symbolic links,
tracked gitlinks, and incomplete status inputs are deliberately `unknown`. The observation is made
when the Rust build script runs and may be reused from Cargo's cache; it is not a live Git-tool or
object-store availability check. Git older than 2.45 also yields `unknown`. Treat clean/dirty as a
bounded, non-atomic observation that assumes repository metadata and package files were not
concurrently mutated during the probe.

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
6. Replace ad hoc build fields with `software_identity()` and migrate `exp0.build_provenance` as
   described above.
7. Run `python3 scripts/check-method-catalog.py` and review any changed paper/code/origin entry.
8. Run default, no-default, selected-feature, all-feature, and Python parity tests.
9. Read [known limitations](KNOWN_LIMITATIONS.md) and record which assumptions apply downstream.
