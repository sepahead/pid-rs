# pid-core-rs (Python bindings)

[![CI](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Python bindings (via [PyO3](https://pyo3.rs) + [maturin](https://www.maturin.rs)) for
[`pid-core`](https://github.com/sepahead/pid-rs/tree/main/crates/pid-core): continuous mutual information and **shared-exclusions partial
information decomposition** (`I^sx_∩` PID), implemented in Rust. The distribution is named `pid-core-rs`; the importable module is `pid_core_rs`.

## Install / build

Run these from the `crates/pid-python/` directory (where this crate's `pyproject.toml` lives), or pass `-m crates/pid-python/Cargo.toml` from the repo root. Requires Python >= 3.11 (the wheel is built against the stable `abi3-py311` ABI).

```bash
pip install maturin
cd crates/pid-python
maturin develop --release --locked   # build + install into the active venv
# or build a wheel:
maturin build --release --locked
```

## Use

```python
import numpy as np
import pid_core_rs as pid

n = 400
rng = np.random.default_rng(0)
s1 = rng.standard_normal((n, 1))
s2 = rng.standard_normal((n, 1))
t  = s1 + s2 + 0.2 * rng.standard_normal((n, 1))   # depends on both sources

support = "assume_absolutely_continuous"
print(pid.compute_mi(s1, t, support_contract=support))
print(pid.compute_pid2(s1, s2, t, support_contract=support))
```

The module exports 26 functions plus a reusable `PlsProjector` class. Continuous estimators,
quantized SxPID, diagnostics, preprocessing, and the legacy binned `compute_discrete_pid2/3`
functions take 2-D, C-contiguous, finite `float64` arrays. Empirical-PMF categorical
`compute_discrete_sxpid2/3/n` takes C-contiguous `int64`; signed labels are dense-encoded and only
row equality is meaningful. Use `compute_quantized_sxpid2/3/n` when equal-width binning of
continuous values is intended.

Every continuous estimator fails closed unless its caller explicitly declares a population-support
contract. The default `support_contract="unspecified"` preserves call parsing but raises
`ValueError`; it does not silently assume that floating-point data are continuous. Standard
Chebyshev KSG, continuous redundancy, co-information, PID2, invariants, and the full experimental
PID3 path require `"assume_absolutely_continuous"`. This is a caller assertion that every marginal
and joint law used by the estimator is full-dimensional and absolutely continuous with respect to
the relevant ambient Lebesgue measure. A finite sample cannot prove that assertion. Exact marginal
ties are incompatible with ideal i.i.d., unrounded continuous-sample conditions and are rejected,
but they do not identify their cause or population support.

The other stable strings are `"assume_smooth_manifold"`, `"atomic_or_mixed"`, `"quantized"`, and
`"singular_or_lower_dimensional"`. The smooth-manifold assertion is accepted only by the structured
`compute_mi_report` hyperbolic path. It asserts continuous X, Y, and joint densities relative to
the relevant manifold/product-manifold measures plus finite MI; it is not a consistency claim.
The three known-incompatible contracts are rejected by continuous estimators so callers can route the data to a matching
discrete, quantized, or mixed-law method. Unknown strings raise `ValueError`.

`continuous_input_diagnostics(x, k=3)` is available before choosing a support contract. It returns
exact row and per-coordinate cardinalities plus independently selected marginal-shell counts and
k-th-radius quantiles. Observed ties or duplicate rows can identify observations incompatible with
ideal estimator conditions but cannot determine their cause; all-unique values and shells do
**not** certify population continuity, finite mutual information, or a common reference measure.

Use `compute_mi_report` when an estimate will be saved, compared, or used scientifically. Its
required keyword-only `preprocessing_description` and `observation_model_description` preserve
assumptions that cannot be reconstructed from the arrays. The nested result carries the estimate,
configuration, method status and geometry model, curvature and hyperbolic dimensions, provenance,
stable warning codes/messages, exact-cardinality X/Y diagnostics, and marginal/joint shell-radius
diagnostics. This set is scoped rather than exhaustive: intrinsic dimension, distance concentration,
dependence, and k/sample-size sensitivity require separate checks.
Lorentz-hyperbolic MI is available only through this reporting API and additionally requires a
nonempty `embedding_training_provenance`; scalar `compute_mi(metric="hyperbolic", ...)` fails with
an instruction to use `compute_mi_report`. The report still labels hyperbolic/manifold KSG
experimental because no statistical consistency theorem has been established for this path.

For two-source continuous PID, `compute_pid2` remains the compact numeric compatibility surface.
Prefer `compute_pid2_report` for persistence or scientific handoff: it requires separate
caller-declared preprocessing descriptions for both sources and the target plus an observation
model, and keeps both estimator configurations, effective signed-MI handling,
experimental-restricted status, dimensions, support, MI/redundancy terms, atoms, and warnings.
Those strings are structurally checked only for nonemptiness. This is a metadata report, not a
full ISX-neighborhood diagnostic.

For supervised PLS preprocessing, fit only on training data and reuse the fitted projector on
held-out rows:

```python
projector = pid.PlsProjector.fit(x_train, y_train, out_dim=2)
x_train_pls = projector.transform(x_train)
x_test_pls = projector.transform(x_test)
```

Each transform returns `{"data": flat_values, "nrows": n, "ncols": out_dim}`. The compatibility
function `pls_transform(x, y, out_dim)` fits and transforms the same rows; it is training-only and
must not be used for held-out evaluation because fitting on the evaluation rows leaks their target
information into the projection.

Standalone `compute_mi` returns the signed finite-sample KSG estimate by default. Passing
`negative_handling="clamp_to_zero"` is an explicit presentation transform; do not use it before
algebraic identities or inference. The MI terms feeding PID atoms and co-information are always
computed unclamped
(`NegativeHandling::Allow` is forced by the core, so `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`
holds by construction up to floating-point roundoff); only the standalone `compute_mi` takes a
`negative_handling` argument.

The `tie_epsilon` arguments are reserved compatibility fields and must remain exactly `0.0`.
Strict neighbor counts use the preceding representable radius; positive erosion values are
rejected. Collapsed radii and ambiguous positive k-th-neighbor shells raise runtime errors rather
than silently selecting a tie convention.

`sampled_four_point_delta_summary(x, ...)` reports the mean, median, p90, p99, sampled maximum,
Monte Carlo standard error, exact finite-dataset diameter, and `2·delta/diameter` counterparts for
the sampled four-point deltas. These are distributional geometry diagnostics: even the sampled
maximum is only a lower bound on the sup-over-all-quadruples Gromov delta. The historical
`estimate_gromov_delta` name is retained for compatibility but returns only the sampled mean and is
deprecated because it overstates what is computed.

Continuous two-source redundancy/PID inputs must have equal source column counts. This is a
necessary small-ball scaling guard, not evidence that their intrinsic dimensions or reference
measures are compatible. Prefer `compute_pid3_partial` with the support contract and required
per-variable/observation provenance keywords for continuous three-source work. It estimates only
redundancy coordinates whose branches have equal
ambient dimensions, returns incompatible coordinates as `value=None`, and returns an atom only
when every redundancy in its exact Möbius expansion is available. Its nested result preserves the
sample/configuration metadata, scientific warnings, branch dimensions, and canonical unavailable
dependency keys. Available atoms are exact combinations of the returned redundancies, but they do
not form a complete 18-atom decomposition and remain experimental. The Python surface requires
separate caller-declared preprocessing descriptions for all sources/target and the observation
model, returns them under `provenance`, and checks only that they are nonempty.

The full continuous `compute_pid3` lattice necessarily contains singleton-vs-pair
mixed-dimensional branches and is disabled by default. Pass
`experimental_allow_mixed_dimension_lattice=True` only for reference reproduction or explicitly
labelled diagnostics; the opt-in does not validate the resulting atoms for scientific inference.
Its nested result keeps all 18 redundancies and atoms under dedicated mappings and attaches the
sample/configuration, support, ambient dimensions, experimental method status, and deterministic
scientific warnings. It also requires separate caller-declared preprocessing descriptions for all
three sources and the target plus an observation-model description, and returns those strings
under `provenance`; nonemptiness checks do not validate their truth.

Some surface is experimental (e.g. the `hyperbolic`/`lorentz` metric is standalone pairwise-MI
only and unvalidated for concatenated invariants or ISX, and discrete PID is a different measure
from the continuous `I^sx_∩` — do not pool their atoms). See the
[repository README](https://github.com/sepahead/pid-rs) for the estimator references and scientific
cautions, which apply equally here.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.
