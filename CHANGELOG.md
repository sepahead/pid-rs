# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Exact categorical SxPID inputs.** `DiscreteMatRef` makes label equality—not numeric spacing—the
  contract of `discrete_sxpid2/3/n`. The old equal-width behavior is available explicitly as
  `quantized_sxpid2/3/n`. Results record the input encoding, observed cardinalities, and all
  non-empty source-subset mutual informations. This is a breaking API change intended for 0.5.0.
- **Python exact/quantized split.** The three `compute_discrete_sxpid*` functions now take
  C-contiguous `int64` categorical arrays; three new `compute_quantized_sxpid*` functions retain
  the `float64` + `num_bins` workflow. All returned dictionaries have deterministic key order.
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
- **Benjamini–Hochberg FDR adjustment** (`benjamini_hochberg`): step-up q-values for the
  many-atoms × sources × windows testing this crate's permutation p-values invite — closing
  the documented "no multiple-comparison correction" limitation. `NaN` p-values (e.g. a test
  whose every resample failed) pass through without counting toward `m`; finite entries
  outside `[0, 1]` are rejected. Hand-computed fixtures, clamping/monotonicity, and NaN semantics
  are covered by tests. Feed it genuine p-values under their stated null assumptions, not
  restricted circular-shift surrogate scores.

### Changed

- **MSRV is now Rust 1.83.** PyO3 and NumPy were upgraded to 0.29, removing the previously ignored
  PyO3 buffer/provenance advisories. The remaining `paste` advisory exception is narrowly scoped to
  an unmaintained transitive nalgebra dependency; removing it currently requires Rust 1.89.
- **Quantized SxPID bootstrap naming is explicit.** `bootstrap_discrete_sxpid2` and its result type
  are now `bootstrap_quantized_sxpid2` and `QuantizedSxPid2BootstrapResult`.
- **Permutation result provenance is explicit.** Both result types retain the selected
  `PermutationScheme`; the per-atom finite count is now named `n_valid` instead of the ambiguous
  `n_perm`, while the result-level `n_perm` remains the requested draw count.
- **Bootstrap APIs fail explicitly.** `block_bootstrap` and `block_bootstrap_paired` now return
  `PidResult`, report `n_valid`, reject invalid configuration/non-finite point estimates, and error
  when no resample is usable. This is a breaking API change intended for 0.5.0.
- **`bootstrap_pid3` now uses the same true moving-block construction as the row helper.** Starts
  are uniform over every overlapping block, including positions that reach the sample tail; all
  variables are resampled coherently and a zero-valid run is rejected.
- **Subsample output is labeled as diagnostic.** Fixed-grid subsampling without repeated row
  indices reports raw effective-m-sample quantiles, not an unproved conservative confidence
  interval for the n-sample estimate, and rejects selecting the entire grid because that produces
  a deterministic zero-width pseudo-distribution. Bootstrap block starts and subsample block
  choices now use rejection-sampled bounded draws rather than modulo reduction.
- **Downstream migration note.** The current Galadriel release remains safely pinned to pid-rs
  v0.4. When it adopts this 0.5 API, its categorical binary justification path should construct
  `DiscreteMatRef` values and call the three-argument `discrete_sxpid2`, not switch to quantization.

### Fixed

- **Categorical and extreme-value correctness.** Exact SxPID is invariant to bijective label
  changes; equal-width quantization no longer collapses large-offset or `[-MAX, MAX]` finite data;
  matrix shapes and resampling arithmetic use checked operations. Net SxPID atoms are formed as
  informative minus misinformative by construction, and union probabilities use a direct support
  scan instead of cancellation-prone inclusion–exclusion.
- **Extreme geometry and jitter scales fail safely.** Lorentz distance rejects overflowing
  cancellation magnitudes and difference quadratic forms instead of admitting off-hyperboloid
  points. Row-bootstrap jitter uses stable online moments, preserves the true zero variance of a
  constant `f64::MAX` column, and skips moment computation entirely when jitter is disabled.
- **No successful non-finite fitted models or finite-distribution summaries.** Logistic regression,
  standardization, PLS, distance concentration, Gromov hyperbolicity, KSG kd-tree spans, and
  bootstrap summaries reject overflowing finite inputs instead of returning `Ok` with NaN/∞ state.
  Pair screening now propagates estimator failures, and PID3 bootstrap rejects a run with zero
  coherent resamples.
  The generic row-bootstrap API retains its documented `n_valid == 0`/NaN sentinel for a wholly
  absent resampling distribution.
- **Pair screening validates its requested family.** `screen_pid2_pairs` now requires at least two
  sources instead of returning a misleading successful empty screen for zero or one source.
- **Canonical run-log payload hashes without breaking schema-1 replay hashes.**
  `canonical_json_hash` recursively orders object keys and rejects non-finite floats instead of
  colliding with JSON `null`. Trace hashes now reject the same invalid values but preserve the
  released replay and schema-1 logical serialization. The separately versioned
  `logical_trace_hash_v2` removes only an event's top-level wall clock, so nested payload fields
  named `timestamp_ns` remain hash-covered without invalidating old sidecars.
- **Documentation now matches the guarantees.** The README distinguishes exact categorical data
  from quantization, scopes the four-atom equation to two sources, describes the Gaussian check as
  a paired Monte Carlo oracle, states kd-tree worst cases, and treats run-log digests as internal
  consistency checks rather than authentication.
- **`discrete_pid` module doc: plug-in `I_min` atoms are non-negative, full stop.** The doc
  claimed finite-sample plug-in atoms "can come out negative even though the population
  values are not" — wrong side of a cross-repo contradiction (prisoma's grandplan §8.1.6 and
  its pytest assert WB non-negativity, and they are right): a pure plug-in computes the
  *exact* Williams–Beer decomposition of the empirical (binned) pmf, and WB non-negativity
  applies to any valid distribution, so atoms are non-negative up to float epsilon
  (±1e-15); a materially negative atom indicates a bug. The doc now says so, distinguishes
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

[Unreleased]: https://github.com/sepahead/pid-rs/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/sepahead/pid-rs/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/sepahead/pid-rs/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sepahead/pid-rs/releases/tag/v0.2.0
[0.1.0]: https://github.com/sepahead/pid-rs/commit/c8357751cccf7b6b6a4b3184c17d2ddf7d09817c
