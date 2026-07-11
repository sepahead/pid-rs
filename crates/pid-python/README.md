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

print(pid.compute_mi(s1, t))          # KSG mutual information (nats)
print(pid.compute_pid2(s1, s2, t))    # {redundancy, unique_s1, unique_s2, synergy}
```

The module exports 21 functions plus a reusable `PlsProjector` class. Continuous estimators,
quantized SxPID, diagnostics, preprocessing, and the legacy binned `compute_discrete_pid2/3`
functions take 2-D, C-contiguous, finite `float64` arrays. Empirical-PMF categorical
`compute_discrete_sxpid2/3/n` takes C-contiguous `int64`; signed labels are dense-encoded and only
row equality is meaningful. Use `compute_quantized_sxpid2/3/n` when equal-width binning of
continuous values is intended.

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

The MI terms feeding PID atoms and co-information are always computed unclamped
(`NegativeHandling::Allow` is forced by the core, so `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`
holds by construction up to floating-point roundoff); only the standalone `compute_mi` takes a
`negative_handling` argument.

The `tie_epsilon` arguments are reserved compatibility fields and must remain exactly `0.0`.
Strict neighbor counts use the preceding representable radius; positive erosion values are
rejected. Collapsed radii and ambiguous positive k-th-neighbor shells raise runtime errors rather
than silently selecting a tie convention.

Continuous two-source redundancy/PID inputs must have equal source column counts. This is a
necessary small-ball scaling guard, not evidence that their intrinsic dimensions or reference
measures are compatible. The full continuous `compute_pid3` lattice necessarily contains
singleton-vs-pair mixed-dimensional branches and is disabled by default. Pass
`experimental_allow_mixed_dimension_lattice=True` only for reference reproduction or explicitly
labelled diagnostics; the opt-in does not validate the resulting atoms for scientific inference.

Some surface is experimental (e.g. the `hyperbolic`/`lorentz` metric is standalone pairwise-MI
only and unvalidated for concatenated invariants or ISX, and discrete PID is a different measure
from the continuous `I^sx_∩` — do not pool their atoms). See the
[repository README](https://github.com/sepahead/pid-rs) for the estimator references and scientific
cautions, which apply equally here.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.
