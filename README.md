<h1 align="center">pid-rs</h1>

<p align="center">
  <strong>Shared-exclusions partial information decomposition and mutual-information estimators in Rust.</strong>
</p>

<p align="center">
  <a href="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml"><img src="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg" alt="License: MIT OR Apache-2.0"></a>
  <img src="https://img.shields.io/badge/rustc-1.83%2B-orange.svg" alt="MSRV 1.83">
  <img src="https://img.shields.io/badge/pid--core-unsafe%20forbidden-success.svg" alt="pid-core: unsafe forbidden">
</p>

`pid-rs` implements the shared-exclusions PID measure `I^sx_∩` in two regimes:

- direct empirical-PMF categorical SxPID, including pointwise informative and misinformative atoms
  (Makkeh, Gutknecht & Wibral, 2021); and
- the continuous k-nearest-neighbour estimator of Ehrlich et al. (2024), built on KSG mutual
  information.

It also supplies the diagnostics and statistics needed to decide whether a result is credible:
geometry checks, Shannon invariants, moving-block uncertainty estimates, explicit permutation
nulls, multiple-testing correction, preprocessing, and structured run-logs. The estimator core is
safe Rust (`#![forbid(unsafe_code)]`) and reports all information quantities in nats.

For two sources, the four averaged atoms reconstruct the joint mutual information:

```text
I(S1,S2;T) = Red + Unq(S1) + Unq(S2) + Syn
```

Categorical three- and four-source decompositions use the full redundancy lattice: 18 and 166
atoms, respectively. The continuous 18-atom extension is retained only behind the explicit
mixed-dimensional research gate described below.

## Capabilities

| Area | Implemented surface |
|---|---|
| Continuous MI | KSG mutual information with exact Chebyshev neighbour queries and strict-radius marginal counts. |
| Continuous shared exclusions | Ehrlich et al. `I^sx_∩` redundancy and 2-source PID for equal-ambient-dimension sources; the 18-atom 3-source extension is an explicit mixed-dimensional research opt-in. |
| Empirical categorical SxPID | `discrete_sxpid2`, `discrete_sxpid3`, and `discrete_sxpid_n` (2–4 sources), with direct empirical-PMF pointwise and averaged signed atoms. |
| Explicit quantization | `quantized_sxpid2`, `quantized_sxpid3`, and `quantized_sxpid_n` equal-width-bin continuous inputs before SxPID. |
| Alternative discrete PID | Williams–Beer `I_min` via the legacy quantizing `discrete_pid2/3` APIs. This is a different measure; do not pool its atoms with `I^sx_∩`. |
| Screening | Co-information, O-information, and average degrees of redundancy (`r̄`) and vulnerability (`v̄`). |
| Diagnostics | Intrinsic dimension, distance concentration, Gromov hyperbolicity, and the `exp0` validation harness. |
| Preprocessing | Standardization, PCA, CountSketch projection, seeded jitter, and supervised PLS. |
| Uncertainty | Moving-block bootstrap for duplicate-safe statistics, fixed-grid subsample diagnostics for kNN statistics, exchangeable-row permutation tests, stationary-series surrogates, and BH/BY FDR adjustment. |
| Reproducibility | Seeded RNG, serial/parallel identity tests, and the `pid-runlog` JSONL schema with replay and consistency checks. |
| Python | A maturin/PyO3 module with 21 functions plus a reusable fitted PLS class; categorical SxPID accepts exact `int64` labels, continuous and quantized APIs accept `float64`. |

## Categorical data is not numeric data

The categorical SxPID entry points take `DiscreteMatRef` labels. They evaluate the empirical PMF
directly in binary64; this is not a claim of population-exact atoms. Only equality of complete
rows matters;
`0`, `1`, and `100` are three categories, not points on a number line. Sparse, negative (after
Python-side dense encoding), and non-monotone labels therefore do not change the mathematical
result under a bijective relabeling.

```rust
use pid_core::{discrete_sxpid2, DiscreteMatRef};

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

When starting from continuous measurements, opt into equal-width binning explicitly:

```rust,ignore
use pid_core::{quantized_sxpid2, MatRef};

let pid = quantized_sxpid2(s1, s2, target, 8)?;
```

Quantized results depend on the bin count and numeric scaling. Result metadata records which input
contract was used and each variable's observed cardinality.

## Continuous quickstart

```rust
use pid_core::{ksg_mi, pid2_isx, IsxConfig, KsgConfig, MatRef, NegativeHandling, Pid2Config};

fn main() -> Result<(), pid_core::PidError> {
    // This is a tiny API example, not enough data for a scientific estimate.
    let s1_data = [0.0, 1.0, 0.0, 1.0, 0.2, 0.8, 0.1, 0.9];
    let s2_data = [0.0, 0.0, 1.0, 1.0, 0.1, 0.9, 0.8, 0.2];
    // Explicit observation noise keeps this continuous relationship in the finite-MI domain.
    let noise = [0.03, -0.02, 0.01, -0.04, 0.02, -0.01, 0.04, -0.03];
    let t_data: Vec<f64> = (0..8).map(|i| s1_data[i] + s2_data[i] + noise[i]).collect();
    let s1 = MatRef::new(&s1_data, 8, 1)?;
    let s2 = MatRef::new(&s2_data, 8, 1)?;
    let t = MatRef::new(&t_data, 8, 1)?;

    let ksg = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
    let mi = ksg_mi(s1, t, &ksg)?;
    let pid = pid2_isx(s1, s2, t, &Pid2Config {
        ksg,
        isx: IsxConfig::default(),
    })?;
    println!("MI={mi:.3} Red={:.3} Syn={:.3}", pid.redundancy, pid.synergy);
    Ok(())
}
```

Runnable examples provide better-sized synthetic systems:

```bash
cargo run --release --example ksg_and_pid
cargo run --release --example discrete_sxpid
```

## Scientific cautions

These estimators are not interchangeable with ground truth.

- KSG and continuous `I^sx_∩` assume approximately i.i.d. samples. Subsample trajectories or use
  dependence-aware uncertainty methods.
- Continuous kNN formulas require an unambiguous k-th-neighbor shell. Zero radii and positive
  boundary ties are rejected with structured errors; quantized data needs a scientifically
  justified discrete model or explicitly seeded sensitivity analysis, not a silent tie convention.
- High intrinsic dimension and distance concentration can invalidate nearest-neighbour geometry.
- Exact deterministic maps between continuous variables have singular joint laws and infinite
  mutual information, outside this finite-MI estimator's domain. Add a scientifically justified
  observation-noise model, or use a suitable discrete/mixed estimator. Near-deterministic
  dependence can still require prohibitive sample sizes even in low dimension.
- For continuous `I^sx_∩`, the relative units and preprocessing of the separate source variables
  determine how source neighborhoods are compared and are therefore part of the estimand, not an
  innocuous implementation detail. Record the full scaling/projection scheme and do not compare or
  pool atoms obtained under different schemes.
- Two-source continuous `I^sx_∩` requires equal ambient source column counts because its
  small-ball disjunction compares raw source-neighborhood radii. Equality is necessary but does not
  prove equal intrinsic dimensions, compatible reference measures, or comparable neighborhood
  geometry.
- The full continuous PID3 lattice necessarily contains singleton-vs-pair branches, so it compares
  source neighborhoods with different ambient dimensions. `Pid3Config` and Python `compute_pid3`
  reject this path unless `experimental_allow_mixed_dimension_lattice` is explicitly enabled. That
  opt-in is for reference reproduction and labelled diagnostics; it does not validate the atoms as
  mixed-dimensional scientific estimates.
- `pid2_isx` combines KSG MI terms with an independently estimated `I^sx_∩` redundancy term. Their
  finite-sample biases differ, so a small near-zero atom may be estimator error.
- The `pls_project_then_*` convenience wrappers fit supervised PLS and evaluate PID on the same
  rows, so they are exploratory and require an explicit acknowledgement. For inference, fit the
  variable-specific projectors and select every hyperparameter on training data, then keep each
  fitted transform fixed while evaluating held-out rows; do not mix independently rotated foldwise
  coordinates in one kNN sample.
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
- With-replacement block bootstrap can duplicate rows and collapse kNN radii; even with jitter, those
  duplicates distort local-density statistics. Prefer `RowResampleScheme::Subsample` for KSG-based
  diagnostics and report the smaller subsample size; its raw m-sample quantiles are not calibrated
  confidence intervals for the full n-row estimate.
- Atom × source × window searches are multiple-testing problems. Use Benjamini–Hochberg only under
  its independence/positive-dependence assumptions; `benjamini_yekutieli` is the more conservative
  option when dependence within the predeclared family is unknown.

The exact Chebyshev kd-tree is an acceleration, not a complexity guarantee. Queries are typically
sublinear in low dimension but can degrade to a scan; the full estimator is worst-case quadratic.
Other metrics, small samples, and high-dimensional joints use the brute-force path directly.

## Validation

The suite checks independent ground truth as well as internal identities:

- KSG MI against the closed-form Gaussian-channel value `−½ ln(1 − ρ²)`.
- Two-source continuous `I^sx_∩`, plus the explicitly research-gated three-source reference
  reproduction, against the authors' public
  [`csxpid`](https://gitlab.gwdg.de/wibral/continuouspidestimator) implementation at pinned commit
  `7bb984611a422cf7944ece68993fe3a27e2eadec`; all redundancy/atom values on the committed fixture
  agree within `1e-12` nats after the recorded bit-to-nat conversion. The
  [generator](scripts/generate-csxpid-reference.py) records the backend and environment, and the
  [SHA-256 sidecar](crates/pid-core/tests/fixtures/csxpid_reference.json.sha256) covers its output.
- Continuous `I^sx_∩` against a semi-analytic paired Monte Carlo oracle: pointwise Gaussian terms
  are closed form, while the expectation is evaluated on the same finite sample.
- Discrete SxPID against the values used by IDTxl's Abzinger/SxPID backend, after converting bits
  to nats; all compared values agree within `1e-12`.
- MGW Theorems IV.2 and IV.3, categorical relabeling invariance, all source-subset
  self-redundancy identities, and reconstruction on the 4-, 18-, and 166-node lattices.
- Williams–Beer `I_min`, co-information, O-information, bootstrap/permutation semantics, and
  serial/parallel equality against hand-derived or deterministic fixtures.

`exp0` is a diagnostic, not a conventional pass/fail benchmark. Its default sweep deliberately
enters high-dimensional regimes where kNN estimates fail and may report `PIVOT` or `NO-GO` while
exiting successfully. `--strict-gate` enforces `GO` only on a curated one-dimensional Gaussian band
with analytic MI values.

```bash
cargo run -p pid-core --bin exp0 -- --seeds 4 --summary-json summary.json --runlog run.jsonl
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate run.jsonl
```

## Run-log guarantees

`pid-runlog` records versioned JSONL events, selected payload digests, order-sensitive full/logical
trace hashes, and an optional whole-file manifest. The schema-1 logical digest remains available
for sidecar compatibility, including its historical JSON-number normalization;
`logical_trace_hash_v2` retains that numeric compatibility while excluding only top-level event
clocks. New `replay_trace_hash_v2` and `logical_trace_hash_v3` digests preserve arbitrary-precision
payload numbers losslessly. Validation checks schema, ordering, lifecycle, causality, finite values,
and internal hash consistency. Replay makes recorded state inspectable and comparable; it does not
recompute an estimator without the original inputs and build.

These hashes are not authentication on their own. A log and colocated sidecar can be replaced
together. Tamper evidence requires storing the digest in a trusted external or signed anchor.

## Project status and installation

The latest tagged version is `v0.4.0`. The current branch contains breaking categorical/quantized
API work intended for `0.5.0`; see [CHANGELOG.md](CHANGELOG.md). There is no crates.io or PyPI
release. Build from source or use a Git dependency pinned to a reviewed commit SHA and commit the
resulting `Cargo.lock`:

```toml
[dependencies]
pid-core = { git = "https://github.com/sepahead/pid-rs", rev = "<40-character commit SHA>" }
```

An exact commit remains the strongest pin. Release tags are protected against update/deletion, and
the dependency lock records the resolved graph, but neither substitutes for reviewing the source
you execute.

## Python

The Python module is buildable from source with CPython 3.11 or newer. It is not currently
distributed on PyPI.

```bash
python -m pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

Continuous functions, quantized SxPID, and the legacy binned `compute_discrete_pid2/3` functions
require finite, C-contiguous `float64` arrays. Exact `compute_discrete_sxpid2/3/n` functions require
C-contiguous `int64` arrays and dense-encode signed labels without treating their magnitude as
meaningful.

## Ecosystem use

In the sibling Crebain→Galadriel stack, Crebain emits a contract-frozen `PidObservation` JSONL
stream when `FusionConfig.emit_innovations` or `CREBAIN_PID_JSONL` is enabled. Galadriel consumes
that stream and can enable its optional `pid-core` integration. Its default detector remains NIS
plus correlation; KSG MI participates in optional escalation, while `I^sx` redundancy and synergy
atoms are advisory report fields. Crebain itself does not depend on this crate.

## Workspace

| Crate | Purpose |
|---|---|
| [`pid-core`](crates/pid-core) | Estimators, PID lattices, invariants, diagnostics, preprocessing, and `exp0`. |
| [`pid-runlog`](crates/pid-runlog) | Versioned run-log schema plus replay/validate/compare CLI. |
| [`pid-python`](crates/pid-python) | PyO3/maturin bindings exposed as `pid_core_rs`. |

The MSRV is Rust 1.83 and is checked in CI. The optional `parallel` feature must remain
bit-identical to the serial estimator path.

## References

| Component | Reference |
|---|---|
| KSG mutual information | Kraskov, Stögbauer & Grassberger (2004), *Physical Review E* 69, 066138 |
| Discrete shared exclusions | Makkeh, Gutknecht & Wibral (2021), *Physical Review E* 103, 032149; [Abzinger/SxPID](https://github.com/Abzinger/SxPID) |
| PID parthood foundation | Gutknecht, Wibral & Makkeh (2021), [arXiv:2008.09535](https://arxiv.org/abs/2008.09535) |
| Continuous shared exclusions | Ehrlich et al. (2024), [Physical Review E 110, 014115](https://doi.org/10.1103/PhysRevE.110.014115); [reference implementation](https://gitlab.gwdg.de/wibral/continuouspidestimator) |
| `I_min` PID | Williams & Beer (2010), [arXiv:1004.2515](https://arxiv.org/abs/1004.2515) |
| `r̄` and `v̄` | Gutknecht et al. (2025), [arXiv:2504.15779](https://arxiv.org/abs/2504.15779) |
| O-information | Rosas et al. (2019), [Physical Review E 100, 032305](https://doi.org/10.1103/PhysRevE.100.032305) |
| kNN sample complexity | Gao, Ver Steeg & Galstyan (2015), [arXiv:1411.2003](https://arxiv.org/abs/1411.2003) |

If you use this software in academic work, cite the estimator papers and
[`CITATION.cff`](CITATION.cff).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security
issues through the process in [SECURITY.md](SECURITY.md), not a public issue.

## License

Licensed under either [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
