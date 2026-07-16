<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img alt="pid-rs logo" src="assets/logo-light.svg" width="200">
  </picture>
</p>

<h1 align="center">pid-rs</h1>

<p align="center">
  <strong>Shared-exclusions partial information decomposition and mutual-information estimators in Rust.</strong>
</p>

> **Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.** Version `0.9.0` is the first public
> source-review prerelease. It provides the exact reviewed source, proposed-1.0 scope records,
> review provenance, and checksums for reviewer feedback. It contains no registry packages,
> wheels, binaries, SBOMs, or docs.rs publication.

Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease.
This 0.9.0 review prerelease makes no 1.x compatibility promise.

Author and maintainer: **Sepehr Mahmoudian**. The 0.9 review release has no software DOI or Zenodo
record; those identifiers are intentionally deferred until after review.

Earlier pre-review tag refs were retired during repository cleanup. Their peeled commits remain in
Git history and the changelog links to immutable commit IDs; no earlier GitHub Releases existed.

<p align="center">
  <a href="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml"><img src="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg" alt="License: MIT OR Apache-2.0"></a>
  <img src="https://img.shields.io/badge/rustc-1.89%2B-orange.svg" alt="MSRV 1.89">
  <img src="https://img.shields.io/badge/pid--core-unsafe%20forbidden-success.svg" alt="pid-core: unsafe forbidden">
</p>

`pid-rs` implements the shared-exclusions PID measure `I^sx_∩` in two regimes:

- direct empirical-PMF categorical SxPID, including pointwise informative and misinformative atoms
  (Makkeh, Gutknecht & Wibral, 2021); and
- a default-off experimental implementation of the continuous k-nearest-neighbour estimator of
  Ehrlich et al. (2024), built on KSG mutual information.

It also supplies diagnostics and statistics needed to assess a result: geometry checks, Shannon
invariants, explicitly declared resampling distributions, typed permutation/surrogate nulls,
multiple-testing correction, preprocessing, and structured run-logs. Generic resampling summaries
are descriptive unless a statistic-specific calibration theorem is supplied. The estimator core is
safe Rust (`#![forbid(unsafe_code)]`) and reports all information quantities in nats.

## Method provenance and claim boundary

**“New in pid-rs” means an implementation, API, composition, diagnostic, or engineering contribution
new to this repository; it is not a claim of scientific novelty.** The exhaustive, versioned map
from methods to papers, external reference code, Rust/Python entry points, feature gates, repository
contributions, and unsupported requests is [`METHODS.md`](METHODS.md). Its machine-readable source
is [`method-catalog.json`](method-catalog.json).

The catalog uses these distinctions consistently:

| Label | Meaning |
|---|---|
| Paper-defined | The mathematical quantity or estimator is defined in a cited publication. |
| Paper-derived | pid-rs composes published quantities or algorithms; the composition itself may have no dedicated paper or theorem. |
| Project-defined | The diagnostic, contract, report, or workflow is specified by this repository and is not presented as a published mathematical method. |
| External reference code | A cited authors' or independent implementation is used for bounded comparison; it is not vendored or silently treated as proof. |
| No implementation | The request is explicitly unsupported; no feature flag or status label implies hidden code. |

Selected boundaries that are easy to confuse:

| Surface | Provenance and code/paper status |
|---|---|
| Categorical SxPID | Paper-defined shared-exclusions functional; stable direct empirical-PMF implementation. Abzinger/SxPID is external reference code. |
| Fitted quantized categorical PID | Project-defined compositions of fitted equal-width transforms with categorical SxPID or `I_min`; stable code for declared quantized estimands, with no dedicated estimator paper claimed. |
| Continuous shared exclusions / PID2 | Ehrlich et al. define the redundancy estimator and two-source atom reconstruction. pid-rs implements that paper-defined core experimentally and adds project-defined report, split-sample, and cross-fit contracts. |
| Incomplete / full continuous PID3 | The incomplete result is a project-defined availability diagnostic, not a complete PID. The full lattice is research-only reference reproduction whose mixed-dimensional branches lack a general consistency result. |
| General mixed-variable shared exclusions | Schick-Poland et al. define a measure-theoretic functional for arbitrary variable types; pid-rs has no practical general estimator or implementation for that functional. Barà et al.'s narrower discrete-target/continuous-source estimator is not implemented here. |
| Heuristics / Lorentz KSG | Heuristics are project-defined research baselines; Lorentz KSG is a paper-derived research adaptation. Neither has a pid-rs consistency result for the claimed target setting. |
| Shannon redundancy/vulnerability | Target-conditioned `r̄` and `v̄` follow the cited Shannon-invariants work. Target-free `Red°` and `Vul°` are project-defined entropy-ratio analogues, not those published target quantities. |
| Resampling and testing | Moving-block bootstrap, permutation schemes, and BH/BY use cited or standard procedures; pid-rs adds typed assumptions, failure retention, and provenance, not a generic calibration theorem. |
| Run logs and Python bindings | Project engineering around the estimator code; no statistical-method paper is claimed for the schema, replay tooling, wrappers, or result classes. |

For two sources, the four averaged atoms reconstruct the joint mutual information:

```text
I(S1,S2;T) = Red + Unq(S1) + Unq(S2) + Syn
```

Categorical three- and four-source decompositions use the full redundancy lattice: 18 and 166
atoms, respectively. The continuous 18-atom extension is retained only behind the explicit
mixed-dimensional research gate described below.
[Lyu, Clark & Raviv (2026)](https://doi.org/10.1103/8rzp-w5z1) show why this computability claim
must remain separate from satisfying every desired cross-subsystem consistency property of a
multivariate lattice PID. Their result is not, by itself, evidence of a code defect or a direct
refutation of categorical SxPID.

## Proposed 1.0 scientific status (0.9 review surface)

A future 1.0 version would promise API and software compatibility for the approved default stable
surface. The 0.9 review release makes no such 1.x promise, and no version number turns an estimator
into a theorem or makes it valid outside its declared assumptions. Default builds exclude the
research families; opt-in features do not change their scientific status.

| Family | 1.0 status | Meaning |
|---|---|---|
| Empirical categorical SxPID (2–4 sources) | Stable | Direct binary64 evaluation on the empirical categorical PMF. |
| Fitted quantized categorical PID | Stable quantized estimands | SxPID or `I_min` of variables transformed by declared, reusable bin edges; neither path is continuous PID. |
| Williams–Beer `I_min` | Stable legacy comparator | A different redundancy definition; never pool these atoms with SxPID atoms. |
| Euclidean/Chebyshev KSG MI report | Conditional stable estimator | Software-stable under the explicit regular continuous-law and support contract. |
| Continuous two-source shared exclusions and PID2 | Experimental | Paper-defined Ehrlich-et-al. redundancy and PID2 atom construction; algebraic reconstruction does not remove finite-sample error in separately estimated terms. |
| Partial continuous PID3 | Experimental incomplete diagnostic | Dynamically available coordinates are not a complete PID. |
| Full continuous PID3 | Research-only | Mixed-dimensional branches lack a general consistency result. |
| Hyperbolic pairwise KSG | Research-only | Correct geodesic distance code does not establish estimator consistency. |
| Hyperbolic shared exclusions/PID | Unsupported | No product/disjunction estimator is provided. |
| Generic kNN bootstrap confidence intervals | Unsupported | Subsample percentiles are diagnostics, not calibrated confidence intervals. |
| Train-split supervised PLS→held-out PID | Exploratory | Fit/select on training data and estimate on held-out evaluation data. |

See [Known limitations](KNOWN_LIMITATIONS.md) before using a result in publication or a
consequential decision. The feature boundary and 0.4→1.0 source changes are listed in the
[migration guide](MIGRATION.md).

## Capabilities

| Area | Implemented surface |
|---|---|
| Continuous MI | KSG mutual information with exact Chebyshev neighbour queries and strict-radius marginal counts. |
| Continuous shared exclusions | Default-off experimental `I^sx_∩` redundancy and PID2; partial/full continuous PID3 are separately labelled research surfaces. |
| Empirical categorical SxPID | `discrete_sxpid2`, `discrete_sxpid3`, and `discrete_sxpid_n` (2–4 sources), with direct empirical-PMF pointwise and averaged signed atoms. |
| Explicit quantization | Reusable fitted equal-width quantization followed by categorical SxPID or `I_min` for a declared quantized estimand. |
| Alternative discrete PID | Williams–Beer `I_min` via explicit empirical-PMF APIs. This is a different measure; do not pool its atoms with `I^sx_∩`. |
| Screening and diagnostics | Shannon invariants with typed defined/undefined normalized-ratio states, intrinsic dimension, distance concentration, sampled four-point delta summaries, and the `exp0` diagnostic program. |
| Preprocessing | Explicit constant-column policies, fitted-state/training hashes, standardization, PCA, CountSketch projection, seeded observation-noise sensitivity, and supervised PLS. |
| Resampling/inference | Declared moving-block resampling distributions, random-origin kNN subsample diagnostics, typed permutation/surrogate nulls, complete failure outcomes, and BH/BY adjustment provenance. |
| Reproducibility | Seeded RNG, serial/parallel identity tests, structured estimator reports, and bounded `pid-runlog` replay/consistency checks. |
| Python | A maturin/PyO3 module with a stable default namespace and an explicit experimental build feature. |

## Categorical data is not numeric data

The categorical SxPID entry points take `DiscreteMatRef` labels. They evaluate the empirical PMF
directly in binary64; this is not a claim of population-exact atoms. Only equality of complete
rows matters;
`0`, `1`, and `100` are three categories, not points on a number line. Sparse, negative (after
Python-side dense encoding), and non-monotone labels therefore do not change the mathematical
result under a bijective relabeling.

```rust
use pid_core::stable::categorical::discrete_sxpid2;
use pid_core::DiscreteMatRef;

fn main() -> Result<(), pid_core::PidError> {
    let s1_data = [0, 0, 1, 1];
    let s2_data = [0, 1, 0, 1];
    let t_data  = [0, 1, 1, 0]; // XOR
    let s1 = DiscreteMatRef::new(&s1_data, 4, 1)?;
    let s2 = DiscreteMatRef::new(&s2_data, 4, 1)?;
    let t = DiscreteMatRef::new(&t_data, 4, 1)?;
    let pid = discrete_sxpid2(s1, s2, t)?;
    println!("Red={:.4} Syn={:.4}", pid.red.net, pid.syn.net);
    Ok(())
}
```

The distinction from `I_min` is concrete on the two-bit COPY of independent fair sources,
`T = (S1, S2)`: categorical SxPID assigns redundancy `ln(4/3)` nats, while `I_min` assigns `ln 2`
nats. The identity axiom of
[Harder, Salge & Polani (2013)](https://doi.org/10.1103/PhysRevE.87.012130) instead requires
redundancy equal to `I(S1;S2)`, which is zero for these independent sources. This tests that named
axiom, not every PID axiom; properties established for a functional in its defining paper and
broader PID desiderata should be stated separately.

When starting from continuous measurements, opt into equal-width binning explicitly:

```rust,ignore
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2, EqualWidthQuantizer, QuantizerConfig,
};

// Fit on training rows, then reuse exactly those edges on evaluation rows.
let s1_quantizer = EqualWidthQuantizer::fit(s1_train, 8, QuantizerConfig::default())?;
let s2_quantizer = EqualWidthQuantizer::fit(s2_train, 8, QuantizerConfig::default())?;
let target_quantizer = EqualWidthQuantizer::fit(target_train, 8, QuantizerConfig::default())?;
let s1 = s1_quantizer.transform_with_report(s1_eval)?;
let s2 = s2_quantizer.transform_with_report(s2_eval)?;
let target = target_quantizer.transform_with_report(target_eval)?;
let result = fitted_quantized_sxpid2(&s1, &s2, &target)?;
let pid = result.pid;
```

Quantized results depend on the bin count and numeric scaling. The composed result embeds all three
quantization reports—including exact edges, separate domain-tagged training-input,
transform-input, and categorical-output hashes, out-of-range policy, and occupancy—alongside the
PID and observed cardinalities.

Those SHA-256 preimages are reproducible outside Rust. Their NUL-terminated domains are
`pid-rs/quantizer/training-input/f64-bits-le/v1\0`,
`pid-rs/quantizer/transform-input/f64-bits-le/v1\0`, and
`pid-rs/quantizer/categorical-output/u128-le/v1\0`. Append `nrows` then `ncols` as little-endian
`u128`; append input matrices as row-major `f64` bit patterns in little-endian `u64`, or categorical
labels as row-major little-endian `u128`. The final `\0` denotes one zero byte, and no other
separator or text encoding is present. The canonical contract and fixed vectors are in the
[`pid-core` README](crates/pid-core/README.md).

## Continuous quickstart

```rust
use pid_core::stable::continuous::{ksg_mi_report, KsgConfig, KsgProvenance};
use pid_core::MatRef;

fn main() -> Result<(), pid_core::PidError> {
    // This is a tiny API example, not enough data for a scientific estimate.
    let s1_data = [0.03, 0.97, 0.14, 0.86, 0.22, 0.78, 0.35, 0.65];
    // Explicit observation noise keeps this example in the finite-MI domain.
    let noise = [0.03, -0.02, 0.01, -0.04, 0.02, -0.01, 0.04, -0.03];
    let t_data: Vec<f64> = (0..8).map(|i| s1_data[i] + noise[i]).collect();
    let s1 = MatRef::new(&s1_data, 8, 1)?;
    let t = MatRef::new(&t_data, 8, 1)?;

    // This is a population-law assertion, not something a finite sample can prove.
    let config = KsgConfig::assume_regular_full_dimensional();
    let provenance = KsgProvenance::new(
        "raw scalar measurements; no fitted preprocessing",
        "additive continuous observation noise",
        None,
    )?;
    let report = ksg_mi_report(s1, t, &config, &provenance)?;
    println!("MI={:.3} nats", report.estimate_nats);
    Ok(())
}
```

Runnable examples provide better-sized synthetic systems:

```bash
cargo run --release -p pid-core --features experimental-continuous --example ksg_and_pid
cargo run --release --example discrete_sxpid
```

## Scientific cautions

These estimators are not interchangeable with ground truth.

- Continuous estimators fail closed when their support contract is `Unspecified`. The ordinary
  ambient-coordinate Chebyshev/L∞ path requires an explicit
  `AssumeRegularFullDimensional` assertion covering every
  marginal and joint law used by the call—not merely numeric input types. Exact per-coordinate
  ties are incompatible with ideal i.i.d., unrounded continuous-sample conditions and are rejected,
  but they do not identify their cause or population support. Their absence does not prove
  continuity, full-dimensional support, finite MI, or compatible reference measures. Use
  `continuous_input_diagnostics` to inspect exact multiplicities and marginal k-th-shell/radius
  summaries before choosing an estimator. Prefer `ksg_mi_report` (Python: `compute_mi_report`) when
  a result leaves local scope: it carries these diagnostics together with support, preprocessing,
  observation-model, and geometry provenance.
- Two-source shared-exclusions and the PID2 atom reconstruction implement the cited Ehrlich-et-al.
  construction in its restricted domain. pid-rs adds report, split-sample, and cross-fit wrappers;
  neither paper provenance nor those wrappers supply a crate-level general consistency theorem. The
  default-off `pid2_isx_report` (Python
  experimental migration namespace: `compute_pid2_report`) retains all three signed KSG reports,
  the complete ISX source-union/radius/count/scaling/overlap report, atom/term values, provenance,
  warnings, and aligned local-contribution covariance/conditioning diagnostics. The covariance is
  descriptive local-contribution covariance—not calibrated sampling covariance. Split-sample and
  cross-fit helpers require explicit split identities and never pool independently fitted fold
  coordinates.
- KSG and continuous `I^sx_∩` assume approximately i.i.d. samples. Subsample trajectories or use
  dependence-aware uncertainty methods.
- Continuous kNN formulas require an unambiguous k-th-neighbor shell. Zero radii and positive
  boundary ties are rejected with structured errors; quantized data needs a scientifically
  justified discrete model, not a silent tie convention. Jitter changes the estimated distribution:
  use it only under an explicit observation-noise model or in a seeded, reported noise-scale
  sensitivity analysis; otherwise select a discrete, quantized, or mixed-support estimator.
- KSG returns signed finite-sample estimates by default. `NegativeHandling::ClampToZero` is an
  opt-in presentation transform; do not apply it to terms entering PID/Shannon identities or
  inferential procedures.
- High intrinsic dimension and distance concentration can invalidate nearest-neighbour geometry.
- Exact deterministic maps between continuous variables have singular joint laws and infinite
  mutual information, outside this finite-MI estimator's domain. An explicit observation-noise
  model defines a different, finite-MI distribution; otherwise use a suitable discrete/mixed
  estimator. Near-deterministic
  dependence can still require prohibitive sample sizes even in low dimension.
- A practical general estimator for arbitrary combinations of discrete, continuous, singular, and
  mixed support remains absent. [Barà et al. (2025)](https://doi.org/10.1103/58bg-5n9s) provide a
  narrower nearest-neighbour PID method for a discrete target with continuous sources; pid-rs does
  not implement that method, and its restricted orientation does not close the general gap.
- For continuous `I^sx_∩`, the relative units and preprocessing of the separate source variables
  determine how source neighborhoods are compared and are therefore part of the estimand, not an
  innocuous implementation detail. Record the full scaling/projection scheme and do not compare or
  pool atoms obtained under different schemes.
- Two-source continuous `I^sx_∩` requires equal ambient source column counts because its
  small-ball disjunction compares raw source-neighborhood radii. Equality is necessary but does not
  prove equal intrinsic dimensions, compatible reference measures, or comparable neighborhood
  geometry.
- The full continuous PID3 lattice necessarily contains singleton-vs-pair branches, so it compares
  source neighborhoods with different ambient dimensions. It is absent from default builds and
  requires the `research-mixed-dimension-pid3` Cargo feature (or an explicitly experimental Python
  build). That compile-time opt-in is for reference reproduction and labelled diagnostics; it does
  not validate the atoms as mixed-dimensional scientific estimates. Full results carry
  support/dimension/experimental status and deterministic warnings alongside the values.
  `pid3_isx_report` and the experimental Python migration surface
  additionally require and return caller-declared per-variable preprocessing and observation-model
  provenance, structurally checked only for nonemptiness.
  Prefer `incomplete_pid3_report` (experimental Python migration namespace:
  `compute_pid3_partial`), which requires the same provenance and reports every node/atom's
  dynamic availability instead of returning suspect numbers. For equal-dimensional sources
  specifically, 15 redundancy nodes and 8 atoms are available.
- Hyperbolic/Lorentz KSG remains standalone pairwise-MI-only and experimental, and is available
  only through the structured report that requires embedding-training provenance. Its
  smooth-manifold support assertion, fixed curvature `-1`, and use of Lorentz geodesic distance do
  not constitute a manifold-KSG consistency theorem; scalar/local APIs, concatenated invariants, and
  shared exclusions reject it. Lorentz KSG and geometry diagnostics use typed entry points under
  `experimental::hyperbolic`; enabling that feature does not add variants or fields to stable
  types.
- `sampled_four_point_delta_summary` reports a distribution over sampled quadruples. Its mean and
  quantiles are descriptive, and even its sampled maximum is only a lower bound on the
  sup-over-all-quadruples Gromov constant.
- `pid2_isx` combines KSG MI terms with an independently estimated `I^sx_∩` redundancy term. Their
  finite-sample biases differ, so a small near-zero atom may be estimator error.
- The default-off `pls_project_then_*` research wrappers fit supervised PLS and evaluate PID on the
  same rows, so they are exploratory and require an explicit acknowledgement. For inference, fit the
  variable-specific projectors and select every hyperparameter on training data, then keep each
  fitted transform fixed while evaluating held-out rows; do not mix independently rotated foldwise
  coordinates in one kNN sample. Fitted standardizers, PCA, and PLS projectors expose deterministic
  training/parameter hashes; choose an explicit constant-column policy when fitting a standardizer.
- Net `I^sx_∩` atoms can be negative and are never clamped. Informative and misinformative partial
  atoms are separately non-negative up to floating-point roundoff.
- `FullShuffle` permutation nulls require exchangeable rows. `BlockShuffle { block_size }` preserves
  order inside equal, non-overlapping blocks and yields a permutation p-value only when whole blocks
  are exchangeable; it requires `n % block_size == 0`. For a stationary autocorrelated series,
  `CircularShift { min_shift }` preserves serial structure better, but its restricted offsets yield
  an approximate stationary-surrogate score rather than an exact randomization-test p-value. Choose
  the block or shift scale from the dependence length. Any failed or non-finite transformation
  invalidates the complete result rather than merely reducing its reported count.
- Permutation alternatives are explicitly signed `Upper` or `Lower` tails and should be chosen
  before inspecting results. Shuffling one source defines an alignment/exchangeability null; it
  does not generally test “this signed PID atom equals zero,” and no implicit absolute-value
  two-sided test is applied.
- Generic resampling calls require a typed dependence and block-length-selection declaration,
  preserve every requested replicate/fold failure, and return raw empirical spread/percentiles only
  when the complete predeclared set succeeds. With-replacement block bootstrap can duplicate rows
  and collapse kNN radii. Adding jitter changes
  the resampled distribution and still distorts local-density statistics; use it only under the
  explicit noise-model/sensitivity-analysis contract above. Prefer `RowResampleScheme::Subsample`
  for KSG-based diagnostics and report the smaller subsample size; its raw m-sample quantiles are
  not calibrated confidence intervals for the full n-row estimate.
- Atom × source × window searches are multiple-testing problems. Use Benjamini–Hochberg only under
  its independence/positive-dependence assumptions; `benjamini_yekutieli` is the more conservative
  option when dependence within the predeclared family is unknown.

The exact Chebyshev kd-tree is an acceleration, not a complexity guarantee. Queries are typically
sublinear in low dimension but can degrade to a scan; the full estimator is worst-case quadratic.
Other metrics, small samples, and high-dimensional joints use the brute-force path directly.

## Validation

The suite triangulates analytic, external, and standalone reference paths with internal identities:

- KSG MI against the closed-form Gaussian-channel value `−½ ln(1 − ρ²)`.
- The integer KSG local-count arithmetic against a standard-library-only 80-digit Decimal
  harmonic-number oracle: 6,920 exhaustive feasible tuples through 16 samples plus 1,278 fixed
  stress tuples through one million samples. The measured maximum error is 96 binary64 epsilons
  and the enforced ceiling is 256; this checks the local arithmetic, not neighbor counts,
  estimator consistency, or support validity.
- Two-source continuous `I^sx_∩`, plus the explicitly research-gated three-source reference
  reproduction, against the authors' public
  [`csxpid`](https://gitlab.gwdg.de/wibral/continuouspidestimator) implementation at pinned commit
  `7bb984611a422cf7944ece68993fe3a27e2eadec`; all redundancy/atom values on the committed fixture
  agree within `1e-12` nats after the recorded bit-to-nat conversion. The
  [generator](scripts/generate-csxpid-reference.py) records the backend and environment, and the
  [SHA-256 sidecar](crates/pid-core/tests/fixtures/csxpid_reference.json.sha256) covers its output.
- Continuous `I^sx_∩` against a fixed-sample semi-analytic comparison: pointwise Gaussian terms
  are closed form, while the expectation and its ordinary Monte Carlo standard error are evaluated
  on the same seeded finite sample. This is a bounded estimator check, not population ground truth.
- Discrete SxPID against separate hard-coded fixtures from pinned Abzinger/SxPID and IDTxl
  `pid_goettingen` paths, after converting bits to nats; all compared values agree within `1e-12`.
  Those fixtures have no checked-in generator or environment lock and are not complete external
  reproduction bundles.
- Two-source categorical SxPID against a standard-library-only, 80-digit Decimal oracle that
  directly evaluates the published event-probability definition. The committed corpus exhausts
  all 494 nonempty binary count tables with at most four samples; every Rust atom component and MI
  term agrees within four binary64 epsilons. This finite implementation-path cross-check is not an
  external review, a proof for larger alphabets/lattices, or a population-validity claim.
- MGW Theorems IV.2 and IV.3, categorical relabeling invariance, all source-subset
  self-redundancy identities, and reconstruction on the 4-, 18-, and 166-node lattices.
- Williams–Beer `I_min`, co-information, O-information, bootstrap/permutation semantics, and
  serial/parallel equality against hand-derived or deterministic fixtures.

`exp0` is a diagnostic, not a conventional pass/fail benchmark. Its default sweep deliberately
enters high-dimensional regimes where kNN estimates fail and may report a `NO-GO` MI/coherence
verdict or a separate non-gating `PIVOT` geometry disposition while exiting successfully.
Atom-measure validation remains `not_adjudicated`, and atom-estimator validation remains `blocked`.
Unavailable optional estimates and diagnostics carry machine-readable produced/abstained/
not-requested states and reason codes without numeric placeholders. `--strict-gate` enforces `GO`
only on a separately scoped curated one-dimensional Gaussian band with analytic MI values.

```bash
cargo run -p pid-core --all-features --bin exp0 -- --seeds 4 --summary-json summary.json --runlog run.jsonl
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate run.jsonl
```

## Run-log guarantees

`pid-runlog` schema 2 records versioned JSONL events, typed scientific PID provenance, explicit
hash-algorithm/revision identities, order-sensitive trace hashes, and optional manifests/anchors.
Readers stream under `RunLogLimits` rather than loading unbounded files, and schema-2 canonical JSON
hashes preserve integer identity instead of silently converting arbitrary integers through
binary64. Schema 1 remains deliberately readable and has a golden migration into schema 2.
Validation checks schema, ordering, lifecycle, causality, finite/lossless values, paths, and internal
hash consistency. Replay makes recorded state inspectable and comparable; it does not recompute an
estimator without the original inputs and build.

These hashes are not authentication on their own. A log and colocated sidecar can be replaced
together. Tamper evidence requires storing the digest in a trusted external or signed anchor.

## Source use and registry status

The 0.9 review prerelease is distributed only through GitHub as source, scope records, provenance,
and checksum manifests. Version 0.9.0 is not published to crates.io or PyPI, and docs.rs does not
host 0.9.0 documentation. Do not treat registry installation commands for 0.9.0 as
available.

Use its checksum-verified source archive or pin its exact reviewed commit. A Git dependency can be
recorded as follows:

```toml
[dependencies]
pid-core = { git = "https://github.com/sepahead/pid-rs", rev = "<40-character commit SHA>" }
```

The `v0.9.0` review tag is annotated but deliberately unsigned under repository policy.
The attached source, scope, and provenance files are covered by SHA-256 and SHA-512 manifests; see
[release reproduction](RELEASE_REPRODUCTION.md). Checksums establish byte integrity, not signer
identity, and neither a tag nor a checksum substitutes for reviewing the estimator's scientific
assumptions. GitHub release immutability locks this prerelease's tag and six attached files and
automatically generates a cryptographically verifiable GitHub release attestation for the
tag, commit, and assets. The prerelease is not marked as the latest production release. Separate
build-provenance attestations, signed human review, SBOMs, and registry publication are reserved for
a later qualified release.

## Python

The Python extension supports CPython 3.11 or newer. Its distribution name is `pid-core-rs`; the
import name is `pid_core_rs`. No 0.9.0 wheel or source distribution is
published to PyPI. Build and test the exact reviewed source tree locally instead:

```bash
python -m pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

`compute_mi_report` and continuous diagnostics accept finite two-dimensional `float64` arrays.
`compute_categorical_sxpid2/3` and `compute_categorical_sxpid` accept two-dimensional `int64`
arrays and dense-encode complete signed-label rows without treating their magnitude as meaningful.
`EqualWidthQuantizer.fit(...)` and `compute_fitted_quantized_sxpid2(...)` preserve fitted edges and
occupancy in typed result objects. Inputs are copied/validated before long-running work releases the
GIL. A default wheel built locally from this source contains no continuous-PID, hyperbolic,
heuristic, hierarchy, or same-sample PLS entry points; pre-1.0 compatibility functions exist only
in an explicitly experimental source build under `pid_core_rs.experimental.migration`.

## Ecosystem use

The 0.9 review release and proposed core `pid-rs` 1.0 boundary are standalone. Compatibility with
Prisoma, Galadriel, Crebain, Haldir, external-authority adapters, and full-stack deployment profiles
is **not claimed** by this 0.9 review release. Those repositories may consume future anchored
compatibility evidence, but no
downstream service is a build or runtime dependency of `pid-rs`, and no PID result grants or
widens authorization.

## Workspace

| Crate | Purpose |
|---|---|
| [`pid-core`](crates/pid-core) | Estimators, PID lattices, invariants, diagnostics, preprocessing, and `exp0`. |
| [`pid-runlog`](crates/pid-runlog) | Versioned run-log schema plus replay/validate/compare CLI. |
| [`pid-python`](crates/pid-python) | PyO3/maturin bindings exposed as `pid_core_rs`. |

The workspace MSRV is Rust 1.89 and is checked in CI. The optional `parallel` feature must remain
bit-identical to the serial estimator path.

## References

This short list covers the principal PID/MI lineage. The exhaustive method-by-method bibliography,
including diagnostics, preprocessing, geometry, resampling, multiple testing, external code, and
entries with no dedicated paper, is in [`METHODS.md`](METHODS.md).

| Component | Reference |
|---|---|
| KSG mutual information | Kraskov, Stögbauer & Grassberger (2004), *Physical Review E* 69, 066138 |
| Discrete shared exclusions | Makkeh, Gutknecht & Wibral (2021), *Physical Review E* 103, 032149; [Abzinger/SxPID](https://github.com/Abzinger/SxPID) |
| PID parthood foundation | Gutknecht, Wibral & Makkeh (2021), [arXiv:2008.09535](https://arxiv.org/abs/2008.09535) |
| Continuous shared exclusions | Ehrlich et al. (2024), [Physical Review E 110, 014115](https://doi.org/10.1103/PhysRevE.110.014115); [external validation code](https://gitlab.gwdg.de/wibral/continuouspidestimator) |
| `I_min` PID | Williams & Beer (2010), [arXiv:1004.2515](https://arxiv.org/abs/1004.2515) |
| `r̄` and `v̄` | Gutknecht et al. (2025), [arXiv:2504.15779](https://arxiv.org/abs/2504.15779) |
| O-information | Rosas et al. (2019), [Physical Review E 100, 032305](https://doi.org/10.1103/PhysRevE.100.032305) |
| kNN sample complexity | Gao, Ver Steeg & Galstyan (2015), [arXiv:1411.2003](https://arxiv.org/abs/1411.2003) |

If you use this software in academic work, cite the specific method papers identified in
[`METHODS.md`](METHODS.md) and the software metadata in [`CITATION.cff`](CITATION.cff).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security
issues through the process in [SECURITY.md](SECURITY.md), not a public issue.

## License

Licensed under either [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
