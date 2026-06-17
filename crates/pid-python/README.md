# pid-core-rs (Python bindings)

[![CI](https://github.com/sepehrmn/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehrmn/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Python bindings (via [PyO3](https://pyo3.rs) + [maturin](https://www.maturin.rs)) for
[`pid-core`](../pid-core): continuous mutual information and **shared-exclusions partial
information decomposition** (`I^sx_∩` PID), implemented in Rust. The module is `pid_core_rs`.

## Install / build

```bash
pip install maturin
maturin develop --release            # build + install into the active venv
# or build a wheel:
maturin build --release
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

print(pid.compute_mi(s1, t))                                   # KSG mutual information (nats)
print(pid.compute_pid2(s1, s2, t, negative_handling="allow"))  # {redundancy, unique_s1, unique_s2, synergy}
```

Inputs are 2-D, C-contiguous, finite `float64` arrays of shape `(n_samples, n_dims)`.
15 functions are exported (MI, redundancy, co-information, 2-/3-source PID, discrete PID,
Shannon invariants, geometry diagnostics, and PCA/PLS/hash/standardize preprocessing).

See the [repository README](https://github.com/sepehrmn/pid-rs) for the estimator references and
scientific cautions, which apply equally here.

## License

Licensed under either of [MIT](../../LICENSE-MIT) or [Apache-2.0](../../LICENSE-APACHE) at your option.
