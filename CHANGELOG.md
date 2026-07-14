# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **The complete 1.0 capability boundary is now machine-checked.** The release scope assigns all
  391 direct `pid-core` exports to 34 unambiguous scientific/infrastructure families, records exact
  feature closure and non-claims, and discloses eleven research-feature mutations of stable
  types as blockers rather than promises. Ten pinned `cargo-public-api` profiles, byte-for-byte
  regeneration from both the frozen source commit and working tree, complete activation-profile
  diffs, canonical JSON-Schema validation, per-feature warning-free docs, and source plus
  compiled-signature mutation tests run in the dedicated `release-scope-coherence` CI job.
- **Full-history secret scanning now distinguishes public evidence digests from credentials.** A
  narrowly conjunctive gitleaks allowlist covers only the exact 64-hex
  `api_projection_sha256` lines in the canonical repository-cut JSON and
  `public_api_snapshot_sha256` lines in the pinned release-scope JSON; all other default rules and
  paths remain scanned.
- **Repository-local derived files are ignored without hiding reproducibility inputs.** Rust/fuzz
  targets, coverage/profiling output, Python/PyO3 environments and caches, maturin distributions,
  release staging, local credentials, editor metadata, OS noise, and agent scratch files are
  excluded. Lockfiles, audit/scope records, fuzz corpora, and byte-hashed fixtures remain explicitly
  trackable; native-library patterns are limited to the `pid_core_rs` extension instead of all
  shared libraries.
- **The 1.0 audit now starts from a reproducible five-repository cut.** A standard-library-only
  collector records each public HTTPS checkout's full commit/tree identity, clean status,
  submodules, locks, toolchains, tags, GitHub Releases, Git dependencies, and contract-file hashes.
  The canonical snapshot and its separate collection-time envelope explicitly mark every
  downstream integration `not_claimed`; deterministic and dirty/submodule/short-SHA
  failure-injection checks run in CI.
- **Pre-release metadata now says what actually exists.** The intended 0.9 publication is a
  GitHub-only source prerelease: reviewed source, proposed-1.0 scope records, review provenance, and
  checksums, with no crates.io, PyPI, docs.rs, binary, SBOM, separate build-provenance attestation,
  software-DOI, or Zenodo publication. GitHub release immutability automatically supplies a signed
  release attestation for the tag, commit, and six files. Until that prerelease exists, the README
  and release notes identify the tree as a candidate/draft, the CFF has no release date, and the 0.9
  changelog entry is unreleased. The 1.0 material remains explicitly proposed for review, downstream
  ecosystem compatibility is not claimed. Obsolete pre-review tag refs are retired while their
  commits remain reachable through immutable changelog links.
  `scripts/check-release-state.sh`
  enforces candidate, Git-free review/final source, and direct annotated-tag state transitions; its
  positive paths and failure injections are part of CI. A separate manual review workflow binds
  exact `v0.9.0` to the dispatch-time `main` commit and its tag CI, requires an administrator's
  immutability preflight acknowledgement without storing an elevated secret, safely replaces only
  incomplete drafts on retry, and verifies the immutable six-asset prerelease and automatic GitHub
  release attestation. The heavyweight registry workflow is manual and v1-or-later only. Packaged
  Rust/Python READMEs, Rustdoc, and type stubs
  now identify 0.9 as a review surface proposed for 1.0 without making a 1.x compatibility promise.
  The citation metadata uses the CFF 1.2 dual-license array and is schema-validated in CI with
  pinned `cffconvert` 2.0.0.
- **`sha2` 0.10 → 0.11** (workspace dependency; `digest` 0.11). SHA-256 output is unchanged, so every
  committed content address, fixture digest, and run-log hash stays byte-identical — verified by the
  existing digest-pinned fixture tests. No source changes were required.
- **`criterion` 0.5 → 0.8** (dev-dependency, benches only). `criterion::black_box` is deprecated in
  favour of `std::hint::black_box`; `benches/estimators.rs` now imports it from `std::hint`, which
  keeps the benches building under CI's `RUSTFLAGS=-D warnings`.

### Fixed

- **The `AGENTS.md` code map was stale and partly wrong.** The module table omitted eleven modules —
  most notably `pipeline.rs` (the entire `experimental::pipelines` surface: permutation nulls,
  Benjamini–Hochberg/Yekutieli FDR, PLS component selection, pair screening) plus `logistic.rs`,
  `hyperbolic.rs`, `hierarchy.rs`, and the kernel layer (`kdtree.rs`, `nn.rs`, `metric.rs`,
  `matrix.rs`, `par.rs`, `stats.rs`, `error.rs`, `distance_matrix.rs`) — and the `discrete_pid.rs`
  row named functions (`discrete_pid2`/`discrete_pid3`) that do not exist; the real surface is
  `imin_pid2`/`imin_pid3`. The table now lists every module with its feature gate, flags that
  `experimental-heuristics` baselines do not estimate the paper functional, the test-topology
  paragraph enumerates the actual `tests/` files, and the local command block and the `just doc`
  recipe (hence `just ci` / `just release-audit`) gain the two
  `cargo rustdoc … --lib -- --cfg docsrs` lines so the docs.rs CI gate is reproducible locally
  (its absence is how the broken gate entered the proposed 1.0 candidate).

- **Rustdoc/docs.rs CI gate could never pass.** `cargo rustdoc … --all-features -- --cfg docsrs`
  fails outright when a package exposes more than one buildable target, which `--all-features` does
  for both crates (the `exp0` bin, examples, benches). Both steps now pass `--lib`. The gate has
  been failing in the proposed 1.0 candidate; the equivalent `cargo doc` command in `AGENTS.md`
  is unaffected, which
  is why it went unnoticed.
- **Content-addressed fixtures broke on Windows checkouts.** Without a `.gitattributes`, git
  rewrote LF to CRLF in the JSON/JSONL test fixtures, so their bytes no longer matched the
  committed SHA-256 digests and both `ehrlich_ksg_matches_pinned_csxpid_on_committed_fixture`
  (`pid-core`) and `schema_one_golden_fixture_is_bounded_and_migratable` (`pid-runlog`) failed.
  Line endings are now pinned to LF, and byte-hashed assets (test fixtures, fuzz corpus) are marked
  `-text` so git never translates them.
- **Python binding test was platform-dependent.** `test_categorical_encoding_is_invariant_to_label_order_and_magnitude`
  fed `np.where(...)` results straight to the bindings; with Python int scalars that yields the
  platform default integer dtype, which is int32 on Windows under NumPy 1.x, while the bindings take
  int64. The dtype is now pinned explicitly.
- **SIGINT-cancellation test flaked on virtualized macOS CI runners.**
  `test_sigint_cancels_and_joins_long_rust_worker_promptly` now samples three post-join idle
  intervals and uses their minimum. A joined worker therefore tolerates an isolated VM scheduling
  spike, while a genuinely orphaned worker still burns roughly the whole of every interval and
  fails the unchanged 0.2 s bound.

## [0.9.0] - Unreleased

This is the first public review release, authored by Sepehr Mahmoudian. As a GitHub source
prerelease, it presents the proposed 1.0 API/scientific boundary so reviewers
can comment before 1.x compatibility is promised. Its attached payload is limited to source, scope
records, review provenance, and checksums; crates.io, PyPI, docs.rs, binaries, SBOMs, and
separate build-provenance attestations are outside this review release. GitHub release immutability
automatically supplies a signed release attestation for its tag, commit, and six attached files. No
software DOI or Zenodo record has been assigned, no downstream ecosystem compatibility is claimed,
and earlier release commits remain reachable through immutable changelog links.

## Proposed 1.0 change inventory included for 0.9 review

This review candidate prepares a possible first stable software/API release. “Stable” is deliberately
narrow: empirical
categorical PID, declared fitted quantization, and report-first Euclidean KSG MI form the default
surface. Continuous shared exclusions/PID, partial and full continuous PID3, hyperbolic KSG,
heuristics, hierarchy, and target-adaptive pipelines remain default-off experimental or
research-only features. API stability does not imply universal estimator validity; see
`KNOWN_LIMITATIONS.md` and `MIGRATION.md`.

### Added

- **Narrow 1.0 stable namespace and compile-time research boundary.** Empty default features expose
  empirical categorical PID, fitted quantization, conditional report-first Euclidean KSG, and
  general diagnostics. Continuous shared exclusions/PID, hyperbolic KSG, heuristics, hierarchy,
  mixed-dimensional PID3, and target-adaptive pipelines require individually named default-off
  features; `experimental-all` exists for testing only.
- **Reusable fitted equal-width quantizer.** Training-only `fit` plus held-out `transform` preserves
  exact bin edges, out-of-range policy, data hashes, occupancy, scaling provenance, and resource
  estimates. The result states that the estimand is PID of the quantized variables.
- **Report-first and resource-bounded publication surface.** Stable continuous output carries a
  versioned estimand identity, assumption ledger, support/boundary contract, local radius/count/MI
  quantiles, backend/fallback state, warnings, provenance hashes, and memory/operation preflight.
- **Typed normalized Shannon-invariant states.** Average redundancy/vulnerability ratios return a
  `NormalizedInvariantReport` containing the exact definition, unit, numerator/denominator,
  explicit denominator-stability policy, and a defined/undefined status. Empty, non-finite,
  non-positive, too-small, or unrepresentable cases no longer escape as unexplained `NaN` values;
  `exp0` prints `undef` (and an empty CSV field) below its declared information-resolution floor.
- **Stable typed Python API.** Default wheels return result classes, ship `.pyi`/`py.typed`, copy and
  validate arrays before GIL release, poll Python signals while owned workers run, cooperatively
  cancel core work, always join workers before returning, and expose structured input, resource,
  numerical, and unsupported-operation exceptions. Pre-1.0 functions move to
  `experimental.migration` in an explicitly experimental source build.
- **Bounded run-log schema 2 and durable sidecars.** Streaming readers enforce file/line/event,
  string/container/depth budgets; typed PID provenance carries explicit hash identities; atomic
  sidecar replacement fsyncs the file on every desktop target and the parent directory on Unix;
  schema-1 fixtures remain readable. Decoded-event replay/validation, canonical hashing, manifest
  artifact/anchor construction, and JSON writing also enforce finite aggregate budgets and return
  structured errors.
- **Release assurance.** Cross-platform/default/MSRV/individual/all-feature/release/Python CI,
  deterministic property and fuzz corpora, coverage, semver/package review, zero-exception
  cargo-deny, SBOMs, checksums, artifact attestations, migration/limitations/reproduction guides,
  exact pre-registry package-archive compilation, explicit 1/2/3/4/available-thread identity
  fixtures, and a protected-environment release workflow form the 1.0 gate.
- **Categorical-label SxPID inputs.** `DiscreteMatRef` makes label equality—not numeric spacing—the
  contract of `discrete_sxpid2/3/n`. The old equal-width behavior is available explicitly as
  `quantized_sxpid2/3/n`. Results record the input encoding, observed cardinalities, and all
  non-empty source-subset mutual informations. This is a breaking 1.0 API change.
- **Python categorical/quantized split.** Stable `compute_categorical_sxpid*` functions take
  two-dimensional `int64` categorical arrays, while fitted quantizer objects define the explicit
  numeric-binning workflow. Stable calls return typed immutable result classes; deprecated
  pre-1.0 dictionary calls exist only in an explicitly experimental migration build.
- **Reusable experimental Python PLS model.** In the migration namespace,
  `PlsProjector.fit(x_train, y_train, out_dim)` returns a fitted projector that can transform
  held-out rows without target leakage. The compatibility `pls_transform` helper is explicitly
  training-only and absent from ordinary stable wheels.
- **Pinned CI supply chain.** Workflow and pre-commit actions use full commit SHAs; jobs have
  timeouts, repository checkout is non-persistent, maturin/NumPy/pytest are version-pinned, and
  weekly Cargo/Actions/Python Dependabot configuration is present.
- **External continuous-SxPID provenance.** A committed machine-readable fixture regenerates the
  two-source redundancy and all 18 three-source atoms with the authors' public `csxpid` package at
  commit `7bb984611a422cf7944ece68993fe3a27e2eadec`. The generator pins its SciPy kd-tree backend and
  minimal Python environment, records the bit-to-nat conversion, and emits a SHA-256 sidecar; Rust
  tests match every external value within `1e-12` nats.

- **Exact Chebyshev kd-tree for the KSG/`i^sx` hot loops** (`pid-core/src/kdtree.rs`).
  `ksg_local_mi_terms` and `ksg_local_mi_terms_xblocks` now build a kd-tree per space and
  answer k-th-neighbor and inclusive range-count queries with expected sublinear pruning when
  `metric = Chebyshev`, `n ≥ 128`, and joint dimensionality ≤ 16 (axis-aligned pruning
  degenerates in high dimensions, so the brute scan is kept there and for the hyperbolic
  metric). **Outputs are bit-identical to the brute scan** — same Chebyshev fold, the same
  `total_cmp` k-th distance value, the same inclusive counts on the `strict_radius`, and the
  same radius-collapse error. Worst-case queries can still scan the tree, so full-estimator
  complexity remains `O(n²)`. Enforced by
  parity tests that compare every local MI term to the brute backend bit-for-bit on smooth
  and tie-heavy (quantized) fixtures, below and above the activation threshold, plus
  duplicate-data and extreme-coordinate error parity.

- **Dependence-aware resampling nulls** (`PermutationScheme`): `permutation_pid3_with`
  and `permutation_rows_pvalue_with` accept an explicit scheme — `FullShuffle` (the historical
  Fisher–Yates null; exchangeable/i.i.d. rows only), `BlockShuffle { block_size }` (fixed,
  equal-sized block permutations; valid under whole-block exchangeability), or
  `CircularShift { min_shift }`, which rotates the shuffled variable's rows by a seeded
  pseudorandom offset `k ∈ [min_shift, n − min_shift]`, preserving its internal autocorrelation
  exactly (up to the wrap seam) while breaking cross-alignment — a stationary-series surrogate.
  The restricted offsets exclude the identity and do not form a transformation group, so their
  add-one tail fraction is explicitly an **approximate surrogate score**, not an exact
  randomization-test p-value. The original `permutation_pid3` /
  `permutation_rows_pvalue` delegate to `FullShuffle`, and the wrappers remain bit-identical to
  their explicit `_with(FullShuffle)` forms at the same seed. Full/block shuffles and circular
  offsets now use rejection-sampled bounded RNG draws rather than modulo reduction, eliminating
  the latter's minute finite-word bias. `CircularShift` validates
  `min_shift ≥ 1` and `n ≥ 2·min_shift + 1` (at least two distinct offsets), samples those
  offsets with replacement, and reports the resulting `n_valid`-based numerical floor.
  `BlockShuffle` requires `n % block_size == 0` and at least two blocks, so it covers every row
  without a short non-exchangeable tail. Both result types record the selected scheme; callers can
  therefore distinguish p-values from surrogate scores after the result leaves its call site.
- **Signed one-sided permutation alternatives** (`PermutationTail`):
  `permutation_pid3_with_tail` and `permutation_rows_pvalue_with_tail` accept `Upper` (null at least
  as large as observed) or `Lower` (null at most as large as observed) and record the choice in
  their results. Existing wrappers and `_with` APIs remain bit-identical `Upper` defaults. No
  absolute-value or implicit two-sided interpretation is applied to signed PID atoms.
- **Benjamini–Hochberg/Yekutieli FDR adjustments** (`benjamini_hochberg`,
  `benjamini_yekutieli`): step-up q-values for the many-atoms × sources × windows testing this
  crate's permutation p-values invite — closing
  the documented "no multiple-comparison correction" limitation. Missing, non-finite, or
  out-of-range p-values are rejected instead of propagated as unexplained `NaN` q-value sentinels;
  callers must resolve a typed, predeclared family policy upstream rather than drop failures
  post-hoc. BH documents its independence/positive-dependence contract; BY applies the harmonic
  correction for arbitrary dependence at a power cost. Hand-computed fixtures,
  clamping/monotonicity, and failure semantics are covered by tests. Feed either function genuine
  p-values under their stated null assumptions, not restricted circular-shift surrogate scores.
- **Lossless run-log CLI comparisons.** `pid-runlog-replay --compare-v2` and
  `--compare-logical-v3` expose the arbitrary-precision trace generations directly. Bare replay
  summaries now use the library's lossless fallback contract, print v2/v3 hashes, and remain usable
  for valid payload numbers outside finite `f64`.
- **Adversarial PID property suite.** Seeded skewed empirical laws now exercise 2-, 3-, and
  4-source SxPID pointwise parts, every subset down-set, source-permutation equivariance, all 18
  `I_min` cumulatives/atoms, and the Shannon bounds `1 <= Red° <= m` and `0 <= Vul° <= 1`.
- **Fail-closed continuous-support contracts and diagnostics.** `KsgConfig`, `IsxConfig`, and
  `Pid3Config` now require a caller-declared population-support contract. Their default
  `Unspecified` contract rejects estimation; ordinary ambient-coordinate Chebyshev/L∞ continuous
  estimators accept only an explicit full-dimensional absolute-continuity assertion, while standalone hyperbolic MI has a
  separate experimental smooth-manifold assertion. Exact per-coordinate and row multiplicities
  plus marginal/joint k-th-shell radius diagnostics are public in Rust and Python. Exact ties are
  conservatively rejected as incompatible with ideal i.i.d., unrounded continuous-sample
  conditions, while their cause and population support remain unidentified; all-unique finite
  samples are never presented as proof of continuity. This intentionally breaking API/behavior
  change is part of 1.0.
  Exp0 now reports and skips support-incompatible projection baselines (for example, an empty
  CountSketch bucket yielding a constant coordinate) instead of aborting the whole diagnostic or
  weakening the estimator contract; baseline gate cases remain unchanged.
- **Structured KSG provenance reports.** `ksg_mi_report` / Python `compute_mi_report` preserve the
  presented estimate, the unclamped signed estimate, n/k/metric/negative handling/support
  assertion, preprocessing and observation-model
  descriptions, marginal and joint radius/shell diagnostics, and stable warnings. Hyperbolic
  reports additionally require embedding-training provenance and record Lorentz-hyperboloid model,
  curvature `-1`, row-width-derived manifold dimensions, experimental status, and the absence of a
  consistency theorem.
- **Complete continuous-PID2 reports.** `pid2_isx_report` retains the three complete signed KSG
  constituent reports, the complete ISX source-union/radius/count/scaling/overlap report, aligned
  local-contribution covariance, per-atom cancellation/amplification diagnostics, provenance,
  resource accounting, experimental status, and warnings. The covariance is explicitly
  descriptive local-contribution covariance, not calibrated sampling covariance. Split-sample and
  cross-fit report helpers require train/evaluation identities and keep fold coordinates separate.
  `pid3_isx_report`,
  `pid3_isx_partial_report`, and both Python PID3 surfaces likewise require per-variable/observation
  provenance and keep it with experimental status and warnings. Provenance text is caller-declared
  and checked structurally, not independently verified.
- **Report-first continuous co-information.** Pairwise and triplet reports retain every signed KSG
  constituent, compensated alternating sums, cancellation/amplification diagnostics, and explicit
  warnings that co-information is not a PID and same-sample extremum selection is biased.
- **Held-out hierarchy selection.** Same-sample hierarchy calls are screening-only. The explicit
  split API records screening/evaluation IDs and input hashes, family size, selection rule/count,
  evaluates selected PID2 pairs only on the declared evaluation matrices, and supplies no
  post-selection p-values.
  Enabling `experimental-hierarchy` no longer enables or embeds the independently gated full
  mixed-dimensional PID3 implementation.
- **Fitted preprocessing identity.** Standardization has explicit `Drop`, `Error`, `Zero`, and
  `LeaveCentered` constant-column policies; canonical `fit`/`fit_transform` calls require the
  choice and aggregate-budget variants check simultaneous fitted-state plus output memory.
  Standardizer, PCA, CountSketch, and PLS fitted objects
  expose deterministic training/parameter hashes; PLS hashes every fitted mean, scale, weight, and
  loading.
- **Typed resampling, null, and cancellation contracts.** Generic callbacks are fallible and
  resource-declared; dependence/block-length declarations, permutation assumptions/calibration,
  family definitions, seeds, algorithm revisions, and signed tails travel with results. Every
  requested replicate/fold failure is retained and prevents selective-subset summaries. Long-running
  resampling, permutation, PLS-CV/fit, and logistic-fit paths support cooperative cancellation.
- **Dimension-compatible partial continuous PID3.** `pid3_isx_partial` dynamically estimates only
  redundancy nodes whose antichain branches have equal ambient dimensions. For equal-dimensional
  sources specifically, 15 of 18 redundancies and 8 of 18 atoms are available; the remaining
  values carry their exact missing Möbius dependencies—never zeros or imputed values. The
  structured result carries n/k/metric/support/dimension provenance,
  experimental status, and deterministic scientific warnings; the full 18-number implementation
  remains behind its independent research opt-in.
- **Accurately named sampled four-point diagnostics.**
  `sampled_four_point_delta_summary` returns the mean, median, p90, p99, sampled maximum,
  with-replacement Monte Carlo standard error, exact finite-dataset diameter, and normalized
  counterparts. Monte Carlo standard error is undefined only for one draw; tiny negative variance
  roundoff is clamped with a scale-aware bound, while materially invalid variance is an error. The
  historical `gromov_hyperbolicity` wrapper was removed from the compiled 1.0 surface because it
  returned only the sampled mean, not the sup-over-all-quadruples Gromov constant. Exp0 and Python
  expose the accurately named summary.

### Changed

- **Signed KSG estimates are now the default.** `KsgConfig::default()` and the stable Python report
  path use `NegativeHandling::Allow`; `ClampToZero` remains an
  explicit presentation-only transform. This prevents the default API from biasing weak-signal
  estimates upward or hiding finite-sample failures, and avoids accidental clamping before
  algebraic identities or inference. Reports always retain the raw signed estimate, so explicit
  presentation clamping is reversible after serialization. This is a breaking behavior change in
  1.0.
- **Continuous local-term means use deterministic compensated summation.** KSG direct/x-block,
  two-source shared-exclusions, partial PID3 Möbius combinations, and full experimental PID3
  redundancy averages now use Neumaier accumulation in deterministic order. The estimands and
  neighbor searches are unchanged, while cancellation roundoff is reduced and serial/parallel
  evaluation remains bit-identical; frozen outputs can change in their last bits for this
  numerical-accuracy correction.
- **Discrete PID/SxPID reductions are numerically hardened.** Categorical SxPID event
  probabilities now sum exact empirical counts before one division; averaged atoms and the fixed
  two-source, shared three-source, and general Möbius inversions use deterministic compensated
  accumulation. The shared three-source inversion also hardens discrete `I_min` PID. Estimands and
  canonical `BTreeMap` order are unchanged, and the external SxPID references remain matched within
  `1e-12`.
- **Jitter is no longer documented as a generic duplicate repair.** Estimator errors, Rust/Python
  documentation, preprocessing guidance, and resampling docs now state that added noise changes
  the estimated distribution. It is appropriate only under an explicit observation-noise model or
  as a seeded, reported noise-scale sensitivity analysis; otherwise callers should use a discrete,
  quantized, or mixed-support estimator.
- **Continuous shared-exclusions now enforces its small-ball dimension contract.** Two-source
  `isx_redundancy`/`pid2_isx` rejects unequal ambient source column counts; equality remains only a
  necessary guard and does not establish compatible intrinsic geometry or reference measures. The
  full continuous PID3 lattice necessarily includes singleton-vs-pair mixed-dimensional branches.
  The final 1.0 API removes it from default builds and requires the
  `research-mixed-dimension-pid3` compile-time feature (or an explicitly experimental Python
  source build), rather than a runtime Boolean in stable code. The path is retained for
  pinned-reference reproduction and labelled diagnostics, not presented as validated
  mixed-dimensional inference. Full results keep support, ambient dimensions, experimental status,
  and warnings attached instead of returning bare 18-number maps.
  This is a breaking API/behavior change in 1.0.
- **Continuous kNN estimators reject ambiguous positive neighbor shells.** KSG direct/x-block,
  continuous shared-exclusions, and experimental PID3 now require exactly `k−1` observations
  strictly inside the selected positive radius and one on its boundary. Structured
  `AmbiguousKthNeighborShell` errors report the query, radius, and shell counts; brute-force and
  kd-tree paths agree, and parallel execution deterministically returns the lowest-index failure.
  This prevents continuous rank formulas from silently accepting duplicate/quantized distance
  ties. Smooth, previously valid reference estimates remain bit-identical.
- **Same-sample supervised PLS pipelines require an exploratory opt-in.** Both
  `PlsPid3Config` and `PlsDiscretePid3Config` add `exploratory_allow_same_sample_fit`; the
  convenience wrappers reject the default-unacknowledged workflow. Inferential use must fit one
  fixed projector per variable and select hyperparameters on training rows before evaluating
  held-out rows; independently rotated foldwise coordinates must not be mixed into one kNN sample.
  This is a breaking API/behavior change in 1.0.
- **MSRV is now Rust 1.89.** PyO3 and NumPy were upgraded to 0.29, removing the previously ignored
  PyO3 buffer/provenance advisories. Nalgebra 0.35 and simba 0.10 remove the unmaintained transitive
  `paste` dependency, so the 1.0 cargo-deny policy has no advisory exception.
- **Quantized SxPID bootstrap naming is explicit.** `bootstrap_discrete_sxpid2` and its result type
  are now `bootstrap_quantized_sxpid2` and `QuantizedSxPid2BootstrapResult`.
- **Permutation result provenance is explicit.** Both result types retain the selected
  `PermutationScheme`; the per-atom finite count is now named `n_valid` instead of the ambiguous
  `n_perm`, while the result-level `n_perm` remains the requested draw count.
- **Permutation inference is coherent across transformations.** `permutation_pid3_with` and
  `permutation_rows_pvalue_with` retain every requested transform outcome. One failure makes the
  predeclared tail fraction unavailable instead of conditioning on a transform-dependent successful
  subset. Circular-shift results retain their explicitly approximate surrogate interpretation.
- **Bootstrap APIs report descriptive distributions honestly.** `block_bootstrap` and paired/row
  variants require at least two draws, a typed resampling-validity declaration, and fallible
  callbacks. They retain every outcome and expose raw mean, sample spread, and percentiles only for
  the complete predeclared distribution; no generic standard-error or confidence-coverage claim is
  made. This is a breaking API change in 1.0.
- **Deprecated continuous PID3 bootstrap removed.** The old with-replacement `bootstrap_pid3`
  surface is not compiled or re-exported in 1.0. Moving-block replacement duplicates rows and is not
  a generic calibrated KSG/PID interval. Use explicitly declared random-origin subsample
  diagnostics where scientifically appropriate and report their effective-m raw percentiles.
- **Strict kNN radii have one exact meaning.** `tie_epsilon` is now a reserved compatibility field
  that must be exactly zero in KSG, continuous shared-exclusions, and PID3 configurations. Strict
  `< radius` counts use the preceding representable float; subtracting a positive material epsilon
  silently eroded valid neighborhoods. The smallest positive subnormal radius remains valid.
- **More accurate digamma values update estimator last bits.** The recurrence now shifts to 8
  before applying the truncated Bernoulli expansion. Stopping at 6 left approximately
  `9.3e-13` bias in `psi(1)`; the revised implementation matches the analytic integer identity
  `psi(n) = H_(n-1) - gamma` within `5e-14`. Consequently, frozen KSG, continuous-SxPID, PID,
  and dependent bootstrap reference bits change for this scientific accuracy correction.
- **Checked PID2 atom construction.** `Pid2Result::from_estimate` now returns `PidResult` and rejects
  non-finite estimates or overflowing atom subtractions instead of constructing infinities. This
  is a source-breaking API change in 1.0.
- **Fallible original-unit PLS weights.** `PlsProjector::y_weights` now returns
  `PidResult<Vec<f64>>`. A fitted scaled model can remain predictive even when a nonzero
  original-unit weight is smaller than the least subnormal `f64`; the accessor and
  `coefficients()` report that unrepresentability instead of silently returning zero. This is a
  source-breaking API change in 1.0.
- **Fallible original-unit standardization scales.** `Standardizer::inv_std` now returns
  `PidResult<Vec<f64>>` instead of a borrowed slice. The fitted projector keeps a finite scaled
  representation even when an original-unit reciprocal standard deviation would overflow; callers
  that inspect the derived reciprocal must handle that explicit error. This is a source-breaking
  API change in 1.0.
- **Subsample output is labeled as diagnostic.** Random-origin circular-grid subsampling without
  repeated row indices reports raw effective-m-sample quantiles, not an unproved conservative
  confidence interval for the n-sample estimate, and rejects selecting the entire grid because that
  produces a deterministic zero-width pseudo-distribution. `RowBootstrapResult::effective_resample_len`
  records the rounded realized `m`. Block origins and choices use rejection-sampled bounded draws.
- **Run-log sidecars expose lossless hash generations.** The serialized 1.0 `RunLogSummary` and
  `RunManifest` shapes add `trace_hash_v2` and `logical_trace_hash_v3`. Their serde defaults keep
  pre-1.0 sidecars readable, and sidecar verification accepts old files which omit exactly these
  additive fields. Existing unversioned fields retain schema-1 hashes where representable and use
  the corresponding lossless digest only when a generic number exceeds finite `f64`.

### Fixed

- **Categorical and extreme-value correctness.** Empirical categorical SxPID is invariant to
  bijective label changes; equal-width quantization no longer collapses large-offset or
  `[-MAX, MAX]` finite data;
  matrix shapes and resampling arithmetic use checked operations. Net SxPID atoms are formed as
  informative minus misinformative by construction, and union probabilities use a direct support
  scan instead of cancellation-prone inclusion–exclusion.
- **PID and geometry identities survive extreme binary64 scales.** Checked PID2 construction now
  exactly accumulates represented atoms, recovers a finite synergy after overflow or catastrophic
  cancellation when one is representable, and rejects tuples that cannot encode all three defining
  MI identities. Lorentz products use an exact integer superaccumulator with one ties-to-even
  rounding; hyperbolic distance uses a factored rapidity difference and doubled-half-chord staging;
  Gromov diagnostics prevalidate every row and rescale before halving. These changes preserve
  analytic residuals such as `MAX - MAX + 50*MIN_SUBNORMAL`, `MAX² - MAX² + 1 = 1`, final
  subnormal distances, and the exact four-point `delta = 2^-52` fixture instead of returning zero,
  NaN, or a seed-dependent success.
- **PLS, logistic, and quantization avoid representable-result failures.** PLS cross-validation
  accumulates PRESS/total variation in scale-factored coordinates, and PLS affine predictions use
  binary exponent/significand accumulation so a centered overflow can cancel to `MAX` while the
  very next overflowing input is rejected. Constant logistic features reduce exactly to zero-weight
  intercept-only directions. Equal-width quantization computes `floor(fraction * num_bins)` from
  the binary64 significand in `u128`, so bin counts above `2^53` and adjacent subnormals map to the
  intended bins without rounding the integer count through `f64`.
- **Fallible APIs no longer hide capacity panics or dead diagnostic branches.** Distance/hash
  allocations, bootstrap/permutation schedules, and Exp0 seed generation reserve fallibly;
  zero-area matrix concatenation is constant-time, and a finite resample that overflows only after
  jitter is reported as numerical instability rather than a configuration error. Exp0 now treats a
  coherently failed bootstrap/permutation distribution as a gate violation and continues to emit
  the diagnostic summary, replacing the unreachable former `n_valid < n_boot/2` test.
- **Experimental pipelines have aggregate resource contracts.** Bootstrap, permutation, PID2 pair
  screening, and PLS cross-validation expose estimates and `_with_budget` variants; parallel
  resampling charges private worker stacks and simultaneously live resamples. PLS/logistic fitting
  preflights checked products and hard-caps nalgebra solver dimensions, while documentation
  explicitly excludes opaque callback work and nalgebra's internal infallible allocator from claims
  the crate cannot enforce. Heap-owning experimental models/results no longer derive `Clone`.
- **Extreme geometry and jitter scales fail safely.** Lorentz distance validates each upper-sheet
  unit-hyperboloid row and uses the exact hyperbolic-polar half-chord identity, retaining tiny radial
  separations far from the origin without Lorentz or Poincaré cancellation. Unverifiable rows fail
  closed. Distance-concentration moments and row-bootstrap jitter scales are invariant across tiny
  and huge uniform scaling; Gromov sampling draws four distinct rows and rejects zero requests.
  Its seeded sample stream changes because the unbiased distinct-index sampler replaces the former
  modulo/collision-skipping stream, so identical seeds can produce different diagnostic values.
  Box–Muller sampling now redraws only exact zero instead of clamping every uniform draw below
  `1e-12`, restoring the Gaussian tail; rare seeded streams containing such draws therefore change.
- **No successful non-finite fitted models or finite-distribution summaries.** Logistic regression,
  standardization, PLS, distance concentration, Gromov hyperbolicity, KSG kd-tree spans, and
  bootstrap summaries reject overflowing finite inputs instead of returning `Ok` with NaN/∞ state.
  Logistic fitting rejects one-class data, uses scale-invariant logit/gradient convergence, and
  errors on iteration exhaustion. PLS uses scale-safe centering/norms, initializes from the most
  informative target direction regardless of column order, uses a conditioned solve, and reports
  non-convergence. Its prediction path keeps source/target scales factored, so extreme models can
  produce finite predictions even when a standalone coefficient is not representable. Pair
  screening and every bootstrap API propagate estimator failures.
- **Scale-safe preprocessing and diagnostics.** Standardization, PCA, intrinsic-dimension log
  ratios, and degree diagnostics avoid representable intermediate overflow/underflow. PCA rejects
  truncation through a numerically tied eigenspace, preserves tiny variation beside huge constant
  offsets, and all large output allocations fail as errors rather than capacity panics.
- **Discrete MI validates empirical state spaces.** Empty and ragged matrix inputs are rejected,
  and joint states are counted as boundary-preserving row tuples, preventing concatenation aliases
  that could violate `I(X;Y) <= min(H(X), H(Y))`. The plug-in estimate is now accumulated directly
  as `sum p(x,y) log(n n(x,y) / (n(x)n(y)))`, with compensated summation and exact `u128`
  independence products. This avoids entropy-subtraction cancellation beyond `2^53`; only a
  roundoff-scale negative result is restored to the mathematical zero bound, while a material
  negative value reports numerical instability.
- **Run-log schemas are strict and new hashes are lossless.** Event, nested, and sidecar records
  reject unknown fields. New `replay_trace_hash_v2` and `logical_trace_hash_v3` digests preserve
  arbitrary-precision payload numbers, while the older hash generations intentionally reproduce
  their released finite-`f64` normalization so existing sidecars still verify. The new
  `canonical_json_hash_v2` gives payload/config fields a lossless content address; schema-1
  validation accepts either canonical generation and recognizes mixed v1/v2 config anchors. JSON
  writers validate and serialize completely before creating or truncating their destination, so
  NaN/∞ cannot silently become `null` or damage an existing file.
- **Python numeric boundaries remain exact and panic-free.** `distance_stats.pairwise_count` is a
  Python integer rather than a lossy float, and impossible hash-projection allocations raise a
  Python exception.
- **Pair screening validates its requested family.** `screen_pid2_pairs` now requires at least two
  sources instead of returning a misleading successful empty screen for zero or one source.
- **Canonical run-log payload hashes without breaking schema-1 replay hashes.**
  `canonical_json_hash` recursively orders object keys, rejects non-finite floats instead of
  colliding with JSON `null`, and retains its released schema-1 number normalization. Trace hashes
  reject the same invalid values while preserving released replay/logical serialization.
  `logical_trace_hash_v2` removes only an event's top-level wall clock without invalidating old
  sidecars; canonical-v2, replay-v2, and logical-v3 additionally retain arbitrary-precision generic
  JSON numbers.
- **Documentation now matches the guarantees.** The README distinguishes categorical label inputs
  from explicit quantization, scopes the four-atom equation to two sources, describes the Gaussian
  check as
  a paired Monte Carlo oracle, states kd-tree worst cases, and treats run-log digests as internal
  consistency checks rather than authentication.
- **`discrete_pid` module doc: plug-in `I_min` atoms are non-negative, full stop.** The doc
  claimed finite-sample plug-in atoms "can come out negative even though the population
  values are not" — wrong side of a cross-repo contradiction (prisoma's grandplan §8.1.6 and
  its pytest assert WB non-negativity, and they are right): a pure plug-in computes the
  Williams–Beer decomposition of the empirical (binned) pmf, and WB non-negativity applies to any
  valid distribution, so atoms are non-negative up to scale-aware binary64 roundoff (without a
  universal `1e-15` bound); a materially negative atom indicates a bug. The doc now distinguishes
  the estimator-mixing paths (`pid2_isx`) where small negative atoms *are* estimator error,
  and keeps the true caveat: plug-in atoms are biased/noisy estimates of the population
  atoms.
- **README overclaim**: "permutation tests that respect sample dependence" — the shipped
  permutation null was a full-row shuffle, which the Known-limitations section itself said
  does *not* respect autocorrelation. The highlight now states which scheme respects what,
  while `BlockShuffle` states its whole-block exchangeability condition and `CircularShift` is
  documented as an approximate stationary surrogate.

## [0.4.0] - 2026-07-06

> **Why 0.4.0, not 0.3.1:** this release removes public Python parameters (the no-op
> `negative_handling` from three functions), changes `compute_pid3`'s output key format, and
> changes numerical outputs (CountSketch hash projection for all seeds, moving-block bootstrap
> CIs, bias-corrected Levina–Bickel intrinsic dimension) — breaking under the 0.x
> minor-version convention.

### Fixed
- **`HashProjector` CountSketch sign is now independent of the bucket hash.** Both were derived
  from one `splitmix64` value, so for every even `out_dim` the ±1 sign was a deterministic
  function of the bucket (sign = bucket parity): colliding features always added constructively
  and the sketch degenerated to unsigned feature hashing (for correlated inputs
  `E[‖Pv‖²] ≈ d²/out_dim` instead of `‖v‖²`). The sign now comes from a second, salted splitmix
  stream, restoring the actual Charikar–Chen–Farach-Colton (2002) CountSketch, with an
  unbiasedness regression test. Hash-projected outputs change for all seeds.
- **`bootstrap_pid3` / `bootstrap_rows_stats` now implement the true moving-block bootstrap
  (Künsch 1989).** Both previously drew blocks only from the fixed non-overlapping grid (starts
  at multiples of `block_size`) — a Carlstein-style scheme in which the trailing
  `n mod block_size` rows could never appear in any resample — while the docs cited MBB. Block
  starts are now uniform over all `n − block_size + 1` overlapping positions
  (`⌈n/block_size⌉` blocks, truncated to `n` rows); bootstrap CI values change.
  (`RowResampleScheme::Subsample` keeps the fixed grid — distinctness is what guarantees a
  duplicate-free subsample — and now documents its tail exclusion.)
- **`exp0` computes its MI terms with `NegativeHandling::Allow`.** They feed the
  inclusion–exclusion synergy atom, co-information, and r̄/v̄; the repo convention forbids
  clamping a term before a subtraction, and the previous `ClampToZero` silently biased the
  reported synergy in high-d breakdown regimes. The curated strict-gate band is unaffected.
- **`RunLogWriter::append` refuses events that cannot be read back.** `serde_json` serializes
  non-finite `f64` as `null`, which `read_events` can never parse — a NaN metric silently
  corrupted the log and every replay/validate/compare path failed only after the run was over.
  `append` now round-trips each line before writing and errors immediately.
- **`intrinsic_dimension_levina_bickel` applies the MacKay–Ghahramani (2005) bias correction**
  (`k−2` normalisation instead of `k−1`; now requires `k ≥ 3`). The original pointwise estimator
  is biased upward by `(k−1)/(k−2)` (+12.5 % at the default `k = 10`); returned values shrink
  accordingly. `gromov_hyperbolicity` is redocumented as the mean four-point delta (a lower
  bound on the sup-defined Gromov δ), which is what it always computed.
- **Python API honesty:** removed the no-op `negative_handling` parameter from `compute_pid2`,
  `compute_co_information`, and `compute_invariants` — the core forces `Allow` on all three
  paths (correctly: the Möbius/co-information identities require it), so the knob was accepted,
  validated, and ignored. `compute_invariants` now computes its reported MI terms with `Allow`
  too, so the returned dict satisfies `co_information = mi_s1_t + mi_s2_t − mi_s1s2_t` exactly.
  Only `compute_mi` keeps `negative_handling`. `compute_pid3` now keys atoms by source-subset
  bitmask lists (e.g. `"[1, 6]"`), matching the discrete functions, instead of the `Antichain3`
  Debug dump (an unstable format that leaked internal zero-padding).
- **Test-integrity fixes:** `tests/ksg.rs` Gaussian MI/co-information tolerances (0.35/0.45
  nats) exceeded the analytic effect sizes (0.334/0.389 nats), so a dead-zero estimator passed
  both — tightened below the effect size with explicit zero-collapse bounds. Stale
  pre-correction comments asserting the false "I^sx Red → 0" expectation in
  `tests/gaussian_pid_atoms.rs` now state the oracle-confirmed ~0.225-nat picture; a σ=0.7
  comment claiming "~0.9 nats" (closed form: 0.556) was corrected; the misnamed
  `bootstrap_mean_of_gaussian_has_narrow_ci` (uniform data) was renamed.
- **Provenance honesty:** the fixed-data expected values in `tests/isx.rs` / `tests/pid3.rs`
  are relabeled as frozen regression pins of this implementation — their historical csxpid
  attribution left no dataset or invocation artifacts in the repo, so they are not presented as
  external validation anymore (README updated to match; a reproducible csxpid cross-check of
  the continuous estimator remains pending).
- **Citation/doc corrections:** Ehrlich et al. cited as published — Phys. Rev. E 110, 014115
  (2024), DOI in `CITATION.cff`; Kraskov 2004 section cites fixed (§III, not §IV/§II); the
  Barrett-2015 comment no longer calls MMI "the unique PID consistent with the standard axioms"
  (the axioms underdetermine the PID); `pipeline` docs no longer call the continuous `pid3_isx`
  "SxPID"; the stale `n=500` strict-gate rationale now says `n=4000`; `pls.rs` no longer cites
  a nonexistent `findings.md`; a dangling `§8.1.6` citation and a truncated "Williams & Beer
  2010 §;" were replaced with real citations; the README comparison table was corrected (dit is
  discrete-only — no KSG — but does implement SxPID as `PID_SX`; IDTxl ships BROJA and SxPID
  estimators, not `I_min`); "15 functions" → 18 across READMEs; run-log content-addressing
  claims now state exactly which record types carry payload hashes.
- **`exp0 --csv` emits parseable labeled tables.** The strict band previously appended
  36-column case rows directly after the 7-column Gaussian table with no header, and the gating
  band's MI values were absent from CSV entirely; tables are now blank-line separated, each
  with its own header, and the band gate emits its measured-vs-analytic MI rows. The summary
  JSON's 16-hex parameter fingerprint was renamed `param_fingerprint_fnv64` (previously
  `config_hash`, colliding with the run log's incompatible 64-hex SHA-256 `config_hash`).
- **Tooling gates made reachable/faithful:** CI now triggers on `v*` tag pushes so the tag-mode
  version-coherence guard can actually run (fetching real tag objects first); the smoke job
  uses `--locked`; `just lint` no longer excludes `pid-python` from clippy; `just deny` matches
  CI's `--all-features --locked`; `just ci` runs the version-coherence script and documents
  what it skips; `build.rs` resolves git paths via `git rev-parse --git-path` instead of
  hardcoding `../../.git/…` (no more perpetual build-script reruns for registry consumers and
  git worktrees).

- **`hierarchical_pairwise` / `hierarchical_triplet` now honour the PID-identity convention.**
  Every MI term they compute is forced to `NegativeHandling::Allow` (they feed the CI screen and
  the Level-2 atoms — clamping a term before a subtraction broke both identities and made the
  hierarchical CI diverge from `co_information_triplet` exactly in weak-dependence regimes),
  and, when `compute_pid` is set, the KSG/ISX `k`/`metric`/`tie_epsilon` consistency contract of
  `pid2_isx` is enforced instead of silently mixing mismatched neighbourhood geometries. A
  regression test pins the CI identity in a genuinely negative-MI regime.
- **`IsxMethod::DisjunctionFromLocalMi` no longer misattributes its formula to `i^sx`.** Its doc
  presented the unweighted `log(e^{i1}+e^{i2}-e^{i12})` as "the disjunction form"; the true
  shared-exclusions forms are probability-weighted (discrete, MGW 2021) and density-weighted
  with **no** joint term (continuous limit, Ehrlich et al. 2024 Def. 2) — the doc now states
  the implemented heuristic honestly and cross-references the oracle test. `HeuristicSketch`
  also dropped a dead `O(n²)` `(S1,S2,T)` joint-radius pass it computed but never used.
- **Discrete entry points reject empty input** (`discrete_pid2/3`, `discrete_sxpid2/3/_n`
  previously returned a silent all-zero "decomposition" for 0 rows), and `RowCountMismatch`
  errors across `isx.rs`/`pid3.rs` now report the operand that actually mismatches.
- **SxPID axiom coverage:** new tests for MGW 2021 Theorem IV.3 (non-negativity of every
  pointwise atom's informative/misinformative part; canonical gates + random 2-/3-/4-source
  sweeps) and Theorem IV.2 (monotonicity of the cumulative `i^±_∩` down-set sums along the
  full 18-node lattice order); the module doc's false "COPY unique < 0" example was replaced
  (UNQ's uninformative source, `log(3/4) < 0`), the identity-axiom incompatibility is now
  correctly attributed (Rauh–Bertschinger–Olbrich–Jost 2014 for ≥3 sources; BROJA satisfies
  identity + non-negativity at 2), and a garbled AND-gate closed-form comment was corrected
  (`I(S1;T) = 0.75·ln(4/3) = 0.2157615543…`, `Syn = ln2/2`).

- **Triple-check follow-ups:** O-information is now attributed to its originators (Rosas,
  Mediano, Gastpar & Jensen 2019, Phys. Rev. E 100, 032305) instead of being folded into the
  Gutknecht et al. 2025 Shannon-invariants reference (which correctly covers only `r̄`/`v̄`);
  CONTRIBUTING.md's pre-0.3.0 `--strict-gate` description was updated to the curated-band
  semantics; AGENTS.md now says `RUSTFLAGS=-D warnings` applies workflow-wide in CI (not just
  the test job); a leftover temporary audit probe (`examples/audit_tmp_invariants.rs`, whose
  premise the hierarchy fix made false) was removed; `RunLogWriter::append`'s round-trip guard
  gained a regression test (NaN/±inf rejected, nothing written, finite events unaffected);
  the README's Validation/Known-limitations sections were refreshed (Gaussian-oracle wording,
  the no-longer-true "fixed-grid bootstrap" limitation, unambiguous redundant-copy gate), and
  `discrete_sxpid_n` (2–4 sources) is now mentioned in the README feature map.

### Added
- `LICENSE-MIT` / `LICENSE-APACHE` copies in every crate directory, so the published `.crate`
  packages and the Python wheel ship the license texts their metadata declares.

## [0.3.0] - 2026-07-01

### Changed
- Centralised the lint policy in `[workspace.lints]` (`unsafe_code = "forbid"`,
  `rust_2018_idioms`, `unreachable_pub`; adopted by `pid-core`/`pid-runlog`) and demoted five
  over-exposed `pub` helpers to `pub(crate)`. Bumped `anyhow` to clear a RUSTSEC advisory.
- Extended the bit-identical `parallel` (rayon) path beyond bare KSG marginal counting to the
  cost-dominating estimators: continuous `I^sx_∩` (`isx_redundancy`, `EhrlichKsg`), the 3-source
  redundancy loop (`redundancy_for_antichain` in `pid3_isx`), and the bootstrap resample loops
  (`block_bootstrap`, `block_bootstrap_paired`, `bootstrap_pid3`). All use an index-ordered
  collect followed by an index-ordered reduction (RNG streams are still drawn serially), so the
  `parallel` feature stays **`f64::to_bits`-identical** to the serial path.

### Added
- Criterion benchmark suite (`crates/pid-core/benches/estimators.rs`) covering the
  cost-dominating estimators (KSG MI, `I^sx_∩`, PID atoms, discrete SxPID).
- **Genuine discrete shared-exclusions PID `i^sx_∩` (`sxpid` module).** New `discrete_sxpid2` /
  `discrete_sxpid3` implement the actual Makkeh–Gutknecht–Wibral (2021, Phys. Rev. E 103, 032149)
  SxPID redundancy — the discrete sibling of the continuous `I^sx_∩` (`isx`/`pid2`/`pid3`), so the
  library now decomposes information with **one** measure across regimes (the discrete path was
  previously only Williams–Beer `I_min`, the measure SxPID was built to replace). Redundancy of an
  antichain `α` is `i^sx_∩(t:α) = log[ P(𝔱 ∩ ⋃_j 𝔞_j) / (P(t)·P(⋃_j 𝔞_j)) ]` (informative
  `−log P(⋃𝔞_j)` minus misinformative `log[P(t)/P(𝔱∩⋃𝔞_j)]`), with `P(⋃𝔞_j)` by inclusion–exclusion
  over collections and standard Möbius inversion on the redundancy lattice (reusing the measure-
  agnostic `discrete_mobius_inversion_3`). Output is **pointwise** (per-realization, signed) *and*
  averaged atoms, each split into informative/misinformative parts. Units **nats**; atoms may be
  negative (never clamped). Exposed to Python as `compute_discrete_sxpid2/3` and the general
  `compute_discrete_sxpid_n` (2–4 sources).
  - **Bit-faithful validation** (`tests/sxpid_reference.rs`): pointwise atom vectors reproduce the
    Abzinger/SxPID reference (`testing/test_gates.py`) for XOR, AND, UNQ, RDN, COPY, PwUnq, SUM, the
    **non-uniform** RndErr gate (probability-weighted averaging, independently re-derived), and a
    **multi-dimensional** source; the averaged values match **IDTxl's own**
    `test_estimators_multivariate_pid.py` to `1e-12` (e.g. `shared(AND)=0.12255624891826572` bits,
    3-source HASH `shared=0.1926450779…`, `pairs=−0.22686079…`, `syn=0.24511249…` bits — ×`ln 2`).
    The informative/misinformative split is pinned at the bottom *and* non-bottom lattice nodes, and
    a realization-keyed check guards the realization↔atom assignment.
  - **General `n`-source path** (`discrete_sxpid_n`, `2 ≤ n ≤ 4`, the count IDTxl's SxPID
    supports): same measure over the full antichain lattice, with a brute-force antichain
    enumeration (the 4-source lattice has the correct **166** nodes) and general Möbius inversion.
    Validated to reproduce `discrete_sxpid2`/`discrete_sxpid3` within `1e-12` and to
    satisfy reconstruction + exact source-swap symmetry at 4 sources. Bootstrap CIs for the atoms
    via `bootstrap_quantized_sxpid2`.
  - **Axiom property tests** (`tests/sxpid_axioms.rs`): reconstruction (`Σ_α Π(α)=I(S;T)`),
    self-redundancy, source-swap symmetry, real negativity, and an honest identity-axiom comparison —
    on the two-bit COPY of independent sources `I_min` attributes the maximal **1 bit** of redundancy
    while `i^sx` attributes only `log(4/3)≈0.415` bits (SxPID does **not** force averaged red to 0;
    per Bertschinger et al. the identity axiom is incompatible with global non-negativity).
- **`exp0` `--strict-band` / analytically-grounded `--strict-gate`.** `--strict-gate` no longer
  enforces a verdict on the default high-dimension sweep (whose `PIVOT`/`NO-GO` is the documented,
  expected outcome). It now enforces `GO` (exit code 3 otherwise) only on a **curated band** where
  `GO` is legitimately expected and is checked against a **closed-form analytic ground truth**: a
  grid of jointly-Gaussian systems at `d=1`, `n=4000` (KSG's validated regime) whose three
  measure-independent MI terms `I(S1;T)`, `I(S2;T)`, `I(S1,S2;T)` must match their Cover–Thomas
  Gaussian values within the existing scale-aware tolerance (Barrett-2015 MMI atoms are printed for
  reference only — I^sx ≠ MMI). `--strict-gate` implies `--strict-band`, which runs and reports the
  band without enforcing. The four synthetic scenarios are still run at `d ∈ {2,4,8}` as a
  **non-gating** diagnostic alongside the band; they are a known non-`GO` regime (a reported finding,
  not a regression) and the gate's tolerances are deliberately not loosened to accommodate them.
- **`tests/gaussian_pid_atoms.rs` — cited analytic Gaussian PID-*atom* regression.** The previous
  Gaussian test covered MI only; this adds atom-level ground truth for the continuous `I^sx_∩`
  PID2 estimator. Identical sources (`S1==S2==T+noise`) assert Red ≈ I(X;T) and Unq1≈Unq2≈Syn≈0;
  independent additive sources (`S1⟂S2`, `T=S1+S2+noise`) assert the synergy-dominant regime. The
  measure-independent MI terms come from the closed-form Gaussian-channel MI `I=-½ln(1-ρ²)` (Kraskov
  2004; Cover & Thomas). A separate, clearly-labelled Barrett-2015 Gaussian **MMI** reference
  (`R_MMI=min(I(S1;T),I(S2;T))`) is a sanity comparison only (MMI ≠ I^sx).
- **Correction — `independent_additive` I^sx redundancy is positive, not zero.** An earlier version
  of `tests/gaussian_pid_atoms.rs` *assumed* `Red→0` for independent additive Gaussian sources
  ("derived, not assumed") and labelled the estimator's stable ~0.22 nats as over-attribution bias.
  That assumption was **wrong**. The bin-width→0 limit of the discrete shared-exclusions redundancy
  is `i^sx_∩(t:{1},{2}) → log[w1·e^{i1}+w2·e^{i2}]` (a probability-weighted average of pointwise-MI
  exponentials), which is **strictly positive** for this system. New
  `tests/sxpid_gaussian_oracle.rs` provides a **semi-analytic paired Monte Carlo oracle**
  (~0.225 nats; closed-form pointwise terms, finite-sample expectation) and
  asserts the KSG `I^sx_∩` estimator converges to it; the discrete `i^sx` in the fine-bin limit
  triangulates the same value. The false `Red==0` assertion and the "estimator bias" framing were
  removed from `gaussian_pid_atoms.rs`, `bin/exp0.rs`, and `AGENTS.md`.
- **Analytic discrete-PID ground-truth gates (`discrete_pid.rs` tests).** Two canonical
  Williams & Beer (2010) logic gates are now anchored to their closed-form `I_min` PID atoms at
  machine precision (`tol = 1e-9`), on an *exactly enumerated* input distribution (each of the four
  binary `(S1,S2)` states repeated equally, so the empirical law is exact and there is no sampling
  error): **XOR** is pure synergy (`Red=Unq1=Unq2=0`, `Syn=ln 2`, `I(S_i;T)=0`), and **AND** matches
  the derived `H(T)=¼ln4+¾ln(4/3)`, `I(S_i;T)=H(T)-½ln2`, `Red=I(S_i;T)`, `Unq_i=0`,
  `Syn=H(T)-I(S_i;T)` (all values derived in-comment, not tuned). Both also assert the PID identity
  `Red+Unq1+Unq2+Syn=I(S1,S2;T)` exactly.

### Fixed
- **Numerical-stability hardening across estimators & preprocessing:**
  `hyperbolic_distance_lorentz` reformulated to the exact `2·asinh(½·√⟨x−y, x−y⟩_L)` form
  (avoids catastrophic cancellation; coincident far-from-origin pairs now return 0 instead of
  NaN); `PcaProjector::fit` rejects non-finite Gram matrices and eigenvalues at/below a
  rank-aware noise floor (new `Err` returns); `block_bootstrap`/`block_bootstrap_paired`
  validate `alpha ∈ (0, 1)`; scale-relative guards added in the PLS, geometry, and `isx`
  heuristic paths.

- **`discrete_pid3_redundant_sources_dominant` tested the wrong lattice node.** The test read
  `redundancies[6]` and called it "Redundancy", but index 6 (antichain `{{0,1,2}}`) is the lattice
  **TOP**, whose `I_min` is the joint MI `I(S0,S1,S2;T)` — so the old `red > 0.3·I(S0;T)` assertion
  was vacuous (joint MI always exceeds a marginal MI). It now checks the scientifically meaningful
  claims for the near-copy-plus-noise system: the pairwise redundancy of the two near-copies
  (`redundancies[7]`, antichain `{{0},{1}}`) is sizable, the global all-singletons redundancy
  (`redundancies[16]`, diluted by the noise source S2) cannot exceed it, and the TOP node carries
  at least `I(S0;T)`.

- **`pid-runlog` logical trace hash** — `logical_trace_hash` / `logical_trace_hash_from_path`
  digest the ordered event sequence with wall-clock (`timestamp_ns`) fields excluded (the
  run-log filesystem URI/path is never part of an event, so it is excluded by construction).
  Two runs that are logically identical but differ only in timestamps now share the same
  `logical_trace_hash` while their `replay_trace_hash` differs. The hash is surfaced on
  `RunLogSummary` and `RunManifest`, the `pid-runlog-replay` CLI gains `--compare-logical
  <a> <b>` (and prints `logical_trace_hash` in its default report), and a regression test
  (`logical_trace_hash_ignores_timestamps_but_replay_hash_does_not`) pins the contract.
- **`pid-runlog` crash-safe live logging** — `RunLogWriter::sync_all()` / `flush_durable()`
  flush the buffer to the OS and `fsync` the underlying file so already-written events survive a
  crash/power loss.
- **`exp0` build provenance** — a `build_provenance` block (crate version, source git commit or
  `"unknown"`, rustc version, enabled feature set) is added to `exp0`'s run-log `config_json` and
  thereby folded into the SHA-256 `config_hash`, distinguishing source/toolchain configurations.
  This is best-effort metadata, not executable attestation: it omits the binary digest and several
  build inputs. Commit/rustc are captured at compile time via `crates/pid-core/build.rs`.
- `tests/parallel_bit_identity.rs` — a serial==parallel bit-identity guard asserting
  `f64::to_bits` equality (against frozen serial reference bit-patterns) for `ksg_local_mi_terms`,
  the 2-/3-source PID atoms and redundancies, the continuous `I^sx_∩` redundancy, and a
  block-bootstrap result; runs in both the default and `--features parallel` configurations.

## [0.2.0] - 2026-06-20

### Added
- **`pid-python`** — Python bindings (PyO3 + maturin) exposing the `pid_core_rs` module: 15
  functions over NumPy arrays (MI, redundancy, co-information, 2-/3-source PID, discrete PID,
  Shannon invariants, geometry diagnostics, PCA/PLS/hash/standardize preprocessing), an abi3
  wheel for Python 3.11+, a `pyproject.toml`, a pytest smoke suite, and a CI `python` job
  (maturin build + import test on Linux and macOS). `extension-module` is an opt-in feature so
  the plain `cargo` workspace still builds/links without libpython. The crate is distributed as a
  Python wheel (via maturin) and is not published to crates.io (`publish = false`).

### Changed
- Repository moved to `github.com/sepahead/pid-rs` (GitHub account rename); all URLs updated.
- Documentation accuracy pass across every README/markdown file: scoped the `unsafe`-forbidden
  claim to `pid-core`/`pid-runlog`, corrected the `exp0`/`--strict-gate` framing (CI runs `exp0`
  without `--strict-gate`, so it does not enforce a `GO`), and aligned the build/test commands
  with CI.

## [0.1.0] - 2026-06-17

Initial public release.

### Added

- **`pid-core`** — continuous and discrete information-decomposition estimators:
  - KSG mutual information (Kraskov et al. 2004), L∞ joint metric, strict-radius marginal
    counting, optional bit-identical `parallel` (rayon) path.
  - Continuous shared-exclusions redundancy `I^sx_∩` (Ehrlich et al. 2024), disjunction
    neighbourhoods.
  - 2- and 3-source PID atoms (`pid2_isx`, `pid3_isx`) whose Möbius identities hold by
    construction; discrete `I_min` PID over the full 18-antichain lattice.
  - Shannon invariants: co-information, O-information, average degrees of redundancy/vulnerability.
  - Geometry diagnostics (intrinsic dimension, distance concentration, Gromov hyperbolicity),
    preprocessing (standardisation, PCA, PLS, hash projection, seeded jitter), block bootstrap
    and permutation tests, and the `exp0` estimator-validation harness (a diagnostic
    GO/PIVOT/NO-GO gate that exits 0 by default; PIVOT/NO-GO is expected at high dimensions, and
    the opt-in `--strict-gate` flag exits non-zero unless the verdict is GO).
- **`pid-runlog`** — versioned, content-addressed run-log schema (per-record SHA-256 payload
  digests, a whole-trace replay hash, and a whole-file SHA-256 manifest; records are not
  prev-hash-chained) with a `pid-runlog-replay` validation CLI.
- Worked example (`cargo run --example ksg_and_pid`), CI (fmt / clippy `-D warnings` / tests /
  docs / MSRV / smoke), and an analytic-reference test suite (Gaussian-channel MI, XOR/COPY PID
  structure, PID identities to `1e-10`).

### Notes

This release incorporates fixes from an internal soundness audit: the default 2-source/
co-information paths no longer clamp MI terms before the algebraic identities; discrete-PID and
Shannon-invariant summation is now order-deterministic (`BTreeMap`); the permutation p-value uses
the add-one correction; and the public pipeline bootstrap/permutation helpers (`bootstrap_pid3`,
`permutation_pid3`, `bootstrap_rows_stats`, `permutation_rows_pvalue`) return `Err` instead of
panicking on invalid configuration (the lower-level `block_bootstrap`/`block_bootstrap_paired` keep
their documented `assert`-on-invalid-config contract). See the current
[scientific cautions](README.md#scientific-cautions) for estimator caveats.

[Unreleased]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...HEAD
[0.9.0]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...HEAD
[0.4.0]: https://github.com/sepahead/pid-rs/compare/78b99531b386344c69f8b822537a6cd38f0addb1...ad489f5bf5e15c164c599d069a6bee0f338c0e48
[0.3.0]: https://github.com/sepahead/pid-rs/compare/85c92c71f6c3e90ddac641d6bc544474727ab842...78b99531b386344c69f8b822537a6cd38f0addb1
[0.2.0]: https://github.com/sepahead/pid-rs/commit/85c92c71f6c3e90ddac641d6bc544474727ab842
[0.1.0]: https://github.com/sepahead/pid-rs/commit/c8357751cccf7b6b6a4b3184c17d2ddf7d09817c
