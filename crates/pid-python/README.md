# pid-core-rs

Typed Python bindings for the stable 1.x surface of
[`pid-core`](https://github.com/sepahead/pid-rs/tree/main/crates/pid-core). The distribution is
`pid-core-rs`; the importable extension module is `pid_core_rs`.

The default wheel intentionally exposes a narrow scientific contract:

- shared-exclusions PID evaluated directly on an empirical categorical PMF (two to four sources);
- a separately named empirical Williams--Beer `I_min` comparator;
- reusable equal-width quantizers fitted on training rows and applied with fixed edges;
- conditional, report-first Euclidean KSG mutual information under an explicit population-support
  assertion; and
- finite-sample geometry and support diagnostics.

Continuous shared-exclusions PID, full continuous PID3, hyperbolic KSG, target-adaptive pipelines,
and pre-1.0 compatibility calls are absent from ordinary wheels. Their availability in a research
build would not establish scientific validity.

## Install or build

Python 3.11 or newer and NumPy 1.26 or newer are supported. From the repository root:

```text
python -m pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

To build the explicitly experimental migration wheel, opt in at compile time:

```text
maturin build --release --locked -m crates/pid-python/Cargo.toml \
  --features python-experimental
```

That build adds `pid_core_rs.experimental.migration`. The default build has no `experimental`
attribute. The old scalar and research calls are not re-exported at module root.

The deprecated migration module uses a fixed compatibility ceiling of 1 GiB for Rust-owned
wrapper/core work and 10 billion coarse operations; it does not accept caller-configurable
budgets. Its `RESOURCE_MAX_BYTES`, `RESOURCE_MAX_OPERATIONS_HINT`, and `RESOURCE_POLICY` attributes
make that weaker legacy contract explicit. Converting compatibility results into Python
lists/dictionaries crosses the CPython allocator boundary: sizes are preflighted where feasible and
allocation failures remain Python exceptions, but CPython object overhead is not charged exactly
against the Rust resource ceiling. Use the stable typed API for caller-controlled budgets.

The wheel contains `pid_core_rs.pyi` and `py.typed`, so editors and type checkers see the typed
result classes, canonical antichains, NumPy matrix shapes, and structured exception hierarchy.

## Empirical categorical shared-exclusions PID

Categorical calls take two-dimensional `numpy.int64` arrays. Labels may be signed and arbitrarily
large within `int64`; only equality matters, and Rust dense-encodes them deterministically.

```python
import numpy as np
import pid_core_rs as pid

s1 = np.array([[0], [0], [1], [1]], dtype=np.int64)
s2 = np.array([[0], [1], [0], [1]], dtype=np.int64)
target = np.bitwise_xor(s1, s2)

result = pid.compute_categorical_sxpid2(s1, s2, target)
print(result.redundancy.net_nats)
print(result.unique_s1.net_nats)
print(result.unique_s2.net_nats)
print(result.synergy.net_nats)
```

`SxPid2Result` and `SxPidLatticeResult` are immutable extension classes, not nested dictionaries.
Lattice entries use `Antichain.sets: tuple[int, ...]`, where each integer is a canonical source-set
bitmask. Negative shared-exclusions atoms are represented and never clamped.

`compute_categorical_imin_pid2` returns `IminPid2Result`. It evaluates the Williams--Beer `I_min`
functional on the same kind of empirical PMF. `I_min` and shared exclusions are different measures;
their atoms must not be pooled or relabelled as one another.

## Fitted equal-width quantization

Quantization defines a categorical estimand. Fit edges using training rows only, then reuse the
object on evaluation rows:

```python
training = np.array([[0.0], [10.0]], dtype=np.float64)
evaluation = np.array([[2.0], [8.0]], dtype=np.float64)

quantizer = pid.EqualWidthQuantizer.fit(
    training,
    2,
    preprocessing_description="raw sensor units; no scaling",
    out_of_range_policy="error",
)
quantized = quantizer.transform(evaluation)

assert quantizer.edges == ((0.0, 5.0, 10.0),)
assert quantized.values.shape == evaluation.shape
assert quantized.values.dtype == np.int64
print(quantized.report.observed_joint_cardinality)
```

The report records exact fitted edges, training and transformed SHA-256 identities, occupancy,
scaling provenance, and the out-of-range policy. Use `"clamp_to_boundary"` only when boundary
clamping is part of the declared observation/quantization model. The default `"error"` policy
fails on held-out values outside the fitted training range.

For two-source shared-exclusions PID on already fitted quantizers, use
`compute_fitted_quantized_sxpid2`. It attaches one quantization report per source and target. It
never silently refits edges on evaluation data.

## Conditional KSG mutual information

The stable continuous call is report-first and deliberately verbose:

```python
rng = np.random.default_rng(7)
x = rng.normal(size=(600, 1))
y = x + 0.5 * rng.normal(size=(600, 1))

report = pid.compute_mi_report(
    x,
    y,
    k=4,
    support_assertion="regular_full_dimensional_absolutely_continuous",
    preprocessing_description="training-fold standardization reused without refitting",
    observation_model_description="i.i.d. continuous observations with additive sensor noise",
    dependence_model_description="rows treated as independent draws",
)
print(report.value_nats)
print(report.x_diagnostics.unique_rows)
```

The support string is a caller assertion about every required marginal and joint population law;
the sample cannot prove it. Atomic, quantized, singular, mixed, rounded, or unknown support must be
routed to a matching estimand. Exact ties are evidence of incompatibility with ideal unrounded
continuous sampling, but do not identify the cause. Jitter is not a generic tie repair because it
changes the estimand.

## Resource limits, errors, and interruption

Every potentially quadratic Python call accepts `budget=ResourceBudget(...)` or inherits a bounded
default. Multi-input calls preflight the aggregate Rust-owned NumPy copies, encoding workspace, and
the core computation under one ceiling. Preflight failures occur before those retained copies or an
expensive pairwise computation are started.

A fitted `EqualWidthQuantizer` retains its fit-time core ceiling in `resource_budget`. A later
`transform(..., budget=...)` may tighten that ceiling for the wrapper call but cannot loosen the
fit-time ceiling stored in the fitted object.

```python
budget = pid.ResourceBudget(
    max_bytes=64_000_000,
    max_pairwise_distances=2_000_000,
    max_operations_hint=20_000_000,
    max_threads=1,
)
```

Failures use subclasses of `PidRsError`:

- `PidInputError` for shape, value, support-contract, and configuration failures;
- `PidResourceError` for budget, overflow, precision-policy, and allocation failures;
- `PidNumericalError` for ambiguous shells or unstable numerical geometry;
- `PidUnsupportedError` for requests outside the stable scientific surface; and
- `PidCancelledError` for a core computation that cooperatively stops before all work units finish.

Each instance has a stable string `code` and a `fields: dict[str, str]` payload. No stable result
uses an unexplained `NaN` sentinel.

Long Rust computations release the GIL only after each NumPy argument has been validated and copied
into Rust-owned row-major memory. This ownership boundary is essential: another Python thread may
mutate the original array after the copy without racing Rust reads. It also means noncontiguous and
read-only arrays are accepted by logical shape, then normalized safely. While an owned Rust worker
runs, the calling thread polls Python signals. A pending interrupt requests cooperative core
cancellation; the wrapper joins that worker before raising `KeyboardInterrupt`, so it cannot return
while hidden work continues or retain an orphaned input buffer. Cancellation is checked at bounded,
deterministic work-unit intervals and returns no partial estimate. It is cooperative polling, not a
hard real-time guarantee; individual allocator and CPython object-conversion calls remain separate
fallible boundaries. The POSIX SIGINT timing/no-orphan contract is exercised in the wheel tests,
with cross-platform core-token tests covering cancellation independently of OS signal delivery.

## Diagnostics namespace

The diagnostics are available both at module root and through `pid_core_rs.diagnostics`:

- `diagnose_continuous_input`;
- `distance_concentration_report`; and
- `intrinsic_dimension_report`.

Their typed outputs describe the finite sample. They are warnings and measurements, not proofs that
a population estimator theorem applies.

## License

Licensed under either [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
