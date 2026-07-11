# pid-core

[![CI](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Continuous mutual-information and **shared-exclusions partial information decomposition**
(`I^sx_∩` PID) estimators in safe Rust (`#![forbid(unsafe_code)]`).

```rust,ignore
use pid_core::{pid2_isx, IsxConfig, KsgConfig, MatRef, Pid2Config};

// Columns are dimensions, rows are samples. Here: scalar S1, S2, T (n samples each).
let s1 = MatRef::new(&s1_data, n, 1)?;
let s2 = MatRef::new(&s2_data, n, 1)?;
let t  = MatRef::new(&t_data,  n, 1)?;
let pid = pid2_isx(
    s1,
    s2,
    t,
    &Pid2Config::assume_absolutely_continuous(),
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

```rust
use pid_core::{discrete_sxpid2, DiscreteMatRef};

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

For continuous inputs, the separately named `quantized_sxpid2/3/n` functions perform equal-width
binning. Their results depend on numeric scaling and the selected bin count.

This differs from `discrete_pid2`/`discrete_pid3` (Williams & Beer `I_min`) — the measure SxPID was
built to replace. A runnable demo on canonical gates: `cargo run --release --example discrete_sxpid`.

See the [repository README](https://github.com/sepahead/pid-rs) for the full feature list,
estimator references, scientific cautions, and validation strategy.

## Continuous-estimator domain

Continuous configurations default to an `Unspecified` support contract and fail closed. Ordinary
Chebyshev KSG/shared exclusions require an explicit `AssumeAbsolutelyContinuous` caller assertion
covering every marginal and joint population law used by the call. Exact per-coordinate ties are
incompatible with ideal i.i.d., unrounded continuous-sample conditions and are rejected, but they
do not identify their cause or population support; all-unique observed values do not prove
continuity, full dimensionality, finite MI, or a common reference measure. Use
`continuous_input_diagnostics` / `continuous_joint_shell_diagnostics` to inspect exact
multiplicities and k-th-radius/shell behavior before choosing an estimator. `ksg_mi_report`
attaches those diagnostics to the estimate together with structurally checked, caller-declared
preprocessing/observation-model provenance; hyperbolic reports also require
embedding-training provenance and record their fixed
model/curvature and experimental status. Scalar/local KSG APIs reject hyperbolic geometry so this
provenance cannot be silently dropped.

Continuous shared exclusions compares neighborhoods across the separate source variables. Their
relative units and preprocessing therefore form part of the `I^sx_∩` estimand. Record every
standardization or projection and do not compare or pool atoms across different schemes.
`pid2_isx_report` attaches separate caller-declared preprocessing descriptions for both sources and
the target, the observation model, both estimator configs, restricted/experimental status, and
stable warnings. It is a metadata report, not a complete ISX-neighborhood diagnostic.

The two-source continuous estimator requires both source matrices to have the same ambient column
count because the small-ball disjunction compares their raw neighborhood radii. Equal ambient
dimensions are necessary, but do not establish equal intrinsic dimensions, compatible reference
measures, or comparable neighborhood geometry.

The full continuous PID3 lattice necessarily includes singleton-vs-pair source branches and thus
mixed ambient dimensions. It is disabled by default; setting
`Pid3Config::experimental_allow_mixed_dimension_lattice = true` preserves it only for reference
reproduction and explicitly labelled diagnostics, not as a validated mixed-dimensional scientific
estimate. `pid3_isx_partial` is the conservative availability surface: it returns only
dimension-compatible nodes/atoms and carries exact unavailable dependencies plus
support/dimension/warning metadata. Use `pid3_isx_partial_report` to attach separate
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
