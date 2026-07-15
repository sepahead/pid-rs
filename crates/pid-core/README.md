# pid-core

[![CI](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Safe-Rust (`#![forbid(unsafe_code)]`) information-theory estimators with a deliberately narrow 0.9
review surface proposed for 1.0: empirical categorical SxPID, explicitly fitted quantized
variables, Williams--Beer `I_min`, and report-first Euclidean/Chebyshev KSG MI. Version 0.9 makes no
1.x compatibility promise. Continuous shared exclusions, continuous PID, hyperbolic geometry,
hierarchy, and target-adaptive pipelines are default-off research features.

```rust,ignore
use pid_core::experimental::continuous::{pid2_isx, Pid2Config};
use pid_core::MatRef;

// Columns are dimensions, rows are samples. Here: scalar S1, S2, T (n samples each).
let s1 = MatRef::new(&s1_data, n, 1)?;
let s2 = MatRef::new(&s2_data, n, 1)?;
let t  = MatRef::new(&t_data,  n, 1)?;
let pid = pid2_isx(
    s1,
    s2,
    t,
    &Pid2Config::assume_regular_full_dimensional(), // default-off experimental feature
)?;
println!("Red={:.3} Unq1={:.3} Unq2={:.3} Syn={:.3}",
         pid.redundancy, pid.unique_s1, pid.unique_s2, pid.synergy); // values in nats
# Ok::<(), pid_core::PidError>(())
```

## Discrete shared-exclusions PID (`i^sx_∩`)

For categorical data, `discrete_sxpid2` / `discrete_sxpid3` compute the shared-exclusions PID of
Makkeh, Gutknecht & Wibral (2021). Labels are exact categories: only row equality matters. The
reference fixtures agree numerically with the Abzinger/SxPID values used by IDTxl within `1e-12`
after converting bits to nats. The output contains pointwise and averaged atoms, split into
informative and misinformative parts; net atoms may be negative and are never clamped.

A standalone standard-library Python oracle also evaluates the published two-source event
probabilities with 80-digit Decimal arithmetic. Its checksummed corpus covers every nonempty binary
count table with at most four samples (494 tables); the Rust implementation agrees within four
binary64 epsilons. This finite implementation-path comparison is not external acceptance, a
deductive proof for larger domains, or evidence of population validity.

```rust
use pid_core::stable::categorical::discrete_sxpid2;
use pid_core::DiscreteMatRef;

fn main() -> Result<(), pid_core::PidError> {
    let s1_data = [0, 0, 1, 1];
    let s2_data = [0, 1, 0, 1];
    let t_data = [0, 1, 1, 0];
    let s1 = DiscreteMatRef::new(&s1_data, 4, 1)?;
    let s2 = DiscreteMatRef::new(&s2_data, 4, 1)?;
    let t = DiscreteMatRef::new(&t_data, 4, 1)?;
    let r = discrete_sxpid2(s1, s2, t)?;
    println!("Red={:.3} Unq1={:.3} Unq2={:.3} Syn={:.3}",
             r.red.net, r.unq1.net, r.unq2.net, r.syn.net);
    Ok(())
}
```

For numeric inputs, fit `stable::quantized::EqualWidthQuantizer` on training rows and apply its
fixed edges to evaluation rows. Exact edges, separate domain-tagged hashes of the training input,
transform input, and categorical output, scaling description, out-of-range policy, and occupancy
travel in `QuantizationReport`. This defines a quantized estimand; it does not estimate continuous
PID. Use `stable::quantized::fitted_quantized_sxpid2`,
`fitted_quantized_sxpid3`, or `fitted_quantized_sxpid_n` to serialize every transform report with
the averaged PID. Same-sample one-shot binning exists only under the conspicuous
`experimental::pipelines::exploratory_*` names. Those helpers return
`ExploratorySameSampleQuantizedResult<T>` so the exact `num_bins` remains outside stable
categorical encoding enums while travelling beside the categorical result.

The SHA-256 provenance preimages are a cross-language contract. Each domain string below includes
the final NUL byte shown as `\0`:

```text
pid-rs/quantizer/training-input/f64-bits-le/v1\0
pid-rs/quantizer/transform-input/f64-bits-le/v1\0
pid-rs/quantizer/categorical-output/u128-le/v1\0
```

For both input hashes, the preimage is `domain || u128_le(nrows) || u128_le(ncols)`, followed by
each row-major `f64::to_bits()` value encoded as `u64` little-endian. For the categorical-output
hash, the preimage starts with its categorical domain and the same two `u128` little-endian shape
fields, followed by each row-major label converted to `u128` and encoded little-endian. There is no
separator, length field, or text rendering beyond the domain's terminating NUL byte. Fixed-vector
tests in `quantizer.rs` anchor all three encodings.

This differs from `stable::imin::imin_pid2` / `imin_pid3` (Williams & Beer `I_min`) — a legacy
comparator with a different redundancy definition. The stable `I_min` calls take categorical
`DiscreteMatRef` values; fitted-quantized helpers embed every quantization report in their result.
A runnable SxPID demo on canonical gates: `cargo run --release --example discrete_sxpid`.

## Resource and copy contract

Stable estimators expose `*_resource_estimate` and `*_with_budget` variants for work controlled by
sample count, dimension, distinct categorical support, or retained pointwise output. Heap-owning
matrices, fitted transforms, and estimator reports deliberately do not implement ordinary
`Clone`: `Clone::clone` cannot return a structured allocation error or enforce a
`ResourceBudget`. Where copying is a supported workflow, use the type's
`try_clone_with_budget` method (and its copy-resource estimate when provided), or share immutable
state with `Arc` instead of duplicating it.

The default-off pipeline APIs follow the same convention for PLS/logistic fitting, cross-validation,
pair screening, bootstrap, and permutation schedules. Generic callback estimates cover the known
schedule, worker-stack, concurrent-resample, and retained-output costs; they cannot include work or
allocations hidden inside an opaque caller callback, which must enforce its own budget. The
experimental PLS and logistic dense solvers also apply conservative preflight and hard dimension
caps because nalgebra owns internal infallible allocations; these quarantined backends do not claim
that a successful preflight makes operating-system allocator exhaustion impossible.

```compile_fail
fn requires_clone<T: Clone>() {}
requires_clone::<pid_core::MatOwned>();
```

```compile_fail
use pid_core::stable::categorical::DiscreteSxPid2Result;
fn requires_clone<T: Clone>() {}
requires_clone::<DiscreteSxPid2Result>();
```

The budget covers allocations performed inside `pid-core`. Serialization (`serde_json`, file
writers), Python object conversion, and other third-party consumers can allocate their own output
buffers after an estimate has returned; apply those libraries' size limits separately. A
`Serialize` implementation is therefore not a promise that arbitrary serialization is bounded by
the estimator's `ResourceBudget`.

See the [repository README](https://github.com/sepahead/pid-rs) for the full feature list,
estimator references, scientific cautions, and validation strategy.

## Continuous-estimator domain

Continuous configurations default to an `Unspecified` support contract and fail closed. Ordinary
Chebyshev KSG requires an explicit `AssumeRegularFullDimensional` caller assertion covering every
marginal and joint population law used by the call, including boundary, density-regularity, and
finite-information obligations. Continuous shared exclusions uses a default-off research
constructor. Exact per-coordinate ties are
incompatible with ideal i.i.d., unrounded continuous-sample conditions and are rejected, but they
do not identify their cause or population support; all-unique observed values do not prove
continuity, full dimensionality, finite MI, or a common reference measure. Use
`continuous_input_diagnostics` / `continuous_joint_shell_diagnostics` to inspect exact
multiplicities and k-th-radius/shell behavior before choosing an estimator. Lorentz inputs use the
typed counterparts under `experimental::hyperbolic`, keeping the stable `Metric` and report types
identical in every feature profile. `ksg_mi_report`
attaches those diagnostics to the estimate together with structurally checked, caller-declared
preprocessing/observation-model provenance; `hyperbolic_ksg_mi_report` additionally requires
embedding-training provenance and records its fixed model/curvature and experimental status.
Scalar/local KSG APIs reject hyperbolic geometry so this provenance cannot be silently dropped.

Continuous shared exclusions compares neighborhoods across the separate source variables. Their
relative units and preprocessing therefore form part of the `I^sx_∩` estimand. Record every
standardization or projection and do not compare or pool atoms across different schemes.
`pid2_isx_report` attaches separate caller-declared preprocessing descriptions for both sources and
the target, the observation model, both estimator configs, restricted/experimental status, and
stable warnings. It retains the three complete signed KSG constituent reports, the complete ISX
source-union/radius/count/scaling/overlap report, and aligned local-contribution covariance plus
per-atom cancellation diagnostics. The covariance is descriptive local-contribution covariance,
not calibrated sampling uncertainty. Split-sample and cross-fit helpers require explicit split
identities and keep independently fitted fold coordinates separate instead of pooling them.

The two-source continuous estimator requires both source matrices to have the same ambient column
count because the small-ball disjunction compares their raw neighborhood radii. Equal ambient
dimensions are necessary, but do not establish equal intrinsic dimensions, compatible reference
measures, or comparable neighborhood geometry.

The full continuous PID3 lattice necessarily includes singleton-vs-pair source branches and thus
mixed ambient dimensions. It is absent unless `research-mixed-dimension-pid3` is enabled; setting
`Pid3Config::experimental_allow_mixed_dimension_lattice = true` preserves it only for reference
reproduction and explicitly labelled diagnostics, not as a validated mixed-dimensional scientific
estimate. `experimental::continuous::incomplete_pid3_diagnostic` is the conservative availability
surface: it returns only
dimension-compatible nodes/atoms and carries exact unavailable dependencies plus
support/dimension/warning metadata. Use `incomplete_pid3_report` to attach separate
caller-declared preprocessing descriptions for every source/target and the observation model. The
full research-gated `pid3_isx_report` attaches the same provenance to all 18 values. These
descriptions are checked only for nonemptiness.

The continuous KSG/PID path also requires finite mutual information. An exact deterministic map
between continuous variables has a singular joint law and infinite MI. An explicit
observation-noise model defines a different, finite-MI distribution; otherwise use an estimator
designed for discrete or mixed data.

It also requires a unique positive k-th-neighbor boundary: collapsed radii and positive shell ties
are rejected rather than resolved by an undocumented rank convention. Jitter changes the estimated
distribution and is appropriate only under an explicit observation-noise model or as a seeded,
reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support
estimator. KSG preserves signed finite-sample estimates by default; clamping to zero is an explicit
presentation transform and must not precede identities or inference. Same-sample supervised PLS
wrappers are exploratory and require explicit acknowledgement; fit projectors and choose
hyperparameters on training rows before estimating PID on a separate evaluation set.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.
