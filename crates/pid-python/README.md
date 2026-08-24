# pid-core-rs

Typed Python bindings for the 0.9 review surface of
[`pid-core`](https://github.com/sepahead/pid-rs/tree/main/crates/pid-core), proposed for 1.0 without
making a 1.x compatibility promise. The distribution is `pid-core-rs`; the importable extension
module is `pid_core_rs`.

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** Python availability is a binding
status, not a new mathematical-method status. See the exhaustive
[`METHODS.md`](../../METHODS.md) matrix and its machine-readable
[`method-catalog.json`](../../method-catalog.json) source for each method's paper, Rust code,
Python code, feature gate, external validation code, and unsupported cases.

The default wheel intentionally exposes a narrow scientific contract:

- shared-exclusions PID evaluated directly on an empirical categorical PMF (two to four sources);
- a separately named empirical Williams--Beer `I_min` comparator;
- reusable equal-width quantizers fitted on training rows and applied with fixed edges;
- conditional, report-first Euclidean KSG mutual information under an explicit population-support
  assertion;
- finite-sample geometry and support diagnostics; and
- the project-defined typed software-identity envelope (software infrastructure, not an estimator).

Continuous shared-exclusions PID, full continuous PID3, hyperbolic KSG, target-adaptive pipelines,
and pre-1.0 compatibility calls are absent from ordinary wheels. Their availability in a research
build would not establish scientific validity.

| Python surface | What the binding does and does not claim |
|---|---|
| Categorical SxPID / `I_min` | Binds two distinct paper-defined empirical-PMF functionals; typed Python results do not make their atoms interchangeable. |
| SxPID interpretation metadata | Binds the project-defined aggregation and claim-boundary contract; it adds no estimator or scientific-novelty claim. |
| Fitted quantized SxPID | Binds the pid-rs composition of fitted equal-width quantization and categorical SxPID; it estimates a declared quantized estimand and has no separate continuous-estimator paper claim. |
| KSG MI report | Binds the cited KSG estimator plus project-defined support, diagnostic, provenance, resource, and error contracts. |
| Experimental continuous PID2/PID3 | Available only in an explicitly experimental source build; PID2 and the full lattice have paper-defined cores, pid-rs's incomplete PID3 result is a project-defined availability diagnostic, and the full lattice remains research-only here. |
| Experimental heuristics / Lorentz KSG | Project-defined heuristic bindings and a paper-derived Lorentz-KSG research adaptation; no shared-exclusions-paper or manifold-consistency claim follows from importability. |
| Added Gaussian-noise provenance | No Python binding exists. The project-defined experimental implementation is local Rust code with no defining method paper. |
| Wrapper types and GIL/cancellation behavior | Python/Rust interface engineering, not a statistical method or a separate scientific contribution claim. |
| `software_identity()` | Stable binding of a project-defined Rust software contract; local code exists, no defining paper or scientific-novelty claim, and no binary attestation. |

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
attribute. The old scalar and research calls are not re-exported at module root. Legacy Lorentz
metric spellings remain accepted by the experimental report and geometry-diagnostic functions,
which dispatch to the typed `experimental::hyperbolic` Rust APIs without changing stable Rust
types.

The deprecated migration module uses a fixed compatibility ceiling of 1 GiB for Rust-owned
wrapper/core work and 10 billion coarse operations; it does not accept caller-configurable
budgets. Its `RESOURCE_MAX_BYTES`, `RESOURCE_MAX_OPERATIONS_HINT`, and `RESOURCE_POLICY` attributes
make that weaker legacy contract explicit. Converting compatibility results into Python
lists/dictionaries crosses the CPython allocator boundary: sizes are preflighted where feasible and
allocation failures remain Python exceptions, but CPython object overhead is not charged exactly
against the Rust resource ceiling. Use the stable typed API for caller-controlled budgets.

The migration namespace's same-sample quantization functions are not one interchangeable PID
family. `compute_discrete_pid2/3` use Williams–Beer `I_min`; `compute_quantized_sxpid2/3/n` use
categorical Makkeh–Gutknecht–Wibral shared exclusions. They compute per-column ranges on the
evaluated rows and select bins with an exact binary64-significand rule, so their transformed
variables and empirical plug-in estimands depend on that sample. They materialize no edge vector
and are not the stable fitted-edge `EqualWidthQuantizer` route. Their historical flat dictionaries
omit the Rust wrapper's bin-count provenance; the SxPID dictionaries also omit typed atom
interpretation. The three-source `I_min` and MGW adapters share the same antichain-key dictionary
shape, so callers must retain method identity outside the dictionary. No mapping to continuous
shared exclusions is supplied, and a failed continuous nearest-neighbor diagnostic does not
validate these routes. The core wrappers apply their categorical estimator's aggregate resource
gate before quantization. The deprecated Python layer first applies an additional conservative
legacy preflight proportional to `columns * (num_bins + 1)`; it can reject large bin counts the
Rust exact-significand transform can represent, so admitted-call numerical parity is not equality
of accepted input domains. Use the stable fitted quantizer APIs when fixed training edges and
retained transform provenance are required.

The wheel contains `pid_core_rs.pyi` and `py.typed`, so editors and type checkers see the typed
result classes, canonical antichains, NumPy matrix shapes, and structured exception hierarchy.

## Typed software identity

The root and stable aliases return exactly the same dictionary, converted directly from the Rust
serialization rather than reconstructed independently in Python:

```python
import pid_core_rs as pid

identity = pid.software_identity()
assert identity == pid.stable.software_identity()
assert identity["identity_format"] == 1
assert identity["attestation"] == "none"
```

The shipped stub describes the closed nested dictionary with discriminated source variants. Its
repository checker binds the complete record and return graph, special-form imports, root/stable
call signatures and aliases, and exports; a decorator, executable body, shadowing assignment, or
conditional redefinition cannot silently weaken that checked shape. Its domains are intentionally
separate: the public Rust
declaration-signature revision covers only the exact proposed release-scope feature profiles;
source identity records a workspace, Cargo-package, or unavailable route; build context is selected
and incomplete; and the two
forensic SHA-256 values identify exact raw canonical repository-file bytes. Reference verification
depends on the layout in which `pid-core` is compiled, not on whether the final artifact is called
a package or wheel. An exact layout-matched workspace build includes the expected repository
markers and a root `.git` entry, and verifies the current root files. Other layouts carry the
manifest values without re-verifying those files; in particular, a source archive without `.git`
does not re-verify root reference files even if they are present. The resulting crate archive or
wheel need not contain their repository-relative paths. The declaration snapshots are
revision-scoped and checked against every HEAD-reachable registry-touch commit and direct tip
parent; unreachable never-merged branches and externally replaced history remain outside that
check. This is not a cryptographic signature or external transparency log. None of these fields
establishes Python API/ABI compatibility, scientific or
application validity, data quality, source/archive/executable equality, authenticity, or
cross-platform numerical identity. This project-defined binding has no estimator paper and format
1 makes no attestation claim.

The workspace `working_tree` value is captured by the Rust build script, not recomputed when Python
calls this function. Any effective `filter` attribute on a tracked package path (including unset or
unconfigured values), `attr.tree`, tracked symbolic links, tracked gitlinks, and incomplete Git
status inputs are represented as `unknown`; the probe never executes an external clean-filter
command under the stable-repository assumption. Git older than 2.45 also yields `unknown`.
Clean/dirty is a bounded, non-atomic build-time observation that assumes repository metadata and
package files were not concurrently mutated. A cached wheel or Rust artifact is not a live Git-tool
or object-store availability monitor.

## Empirical categorical shared-exclusions PID

Categorical calls take two-dimensional `numpy.int64` arrays. Labels may be signed and arbitrarily
large within `int64`; only equality matters, and Rust dense-encodes them deterministically.
The stable binding returns only averaged atoms and therefore names their class
`SxAveragedAtom`; there is no ambiguous `SxAtom` alias. Its immutable `interpretation` records
the `shared_exclusions_sxpid` measure, `empirical_pmf_average` aggregation, the antichain
Möbius-coordinate role, and the requirement to retain the containing result for the concrete
coordinate. Its project-defined guard says the atom alone establishes neither intentional
deception, causal effect, fault attribution, per-source responsibility, a measure-independent PID
coordinate, nor an unbiased population estimate. The average is an uncorrected empirical plug-in
functional, not a generic population expectation. Reading `net_nats` alone intentionally drops
that context; a bare atom also lacks its concrete antichain. Pointwise atoms remain available only
from the typed Rust result. Experimental migration dictionaries retain their historical all-float
shape and omit this metadata; they are not the persistence surface.
Consumers of persisted objects must require the exact supported `contract_revision`; an unknown
higher revision is not automatically compatible.

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
assert not quantized.values.flags.writeable
print(quantized.report.observed_joint_cardinality)
```

The report records exact fitted edges; `training_input_hash_sha256` for the optional training
input; `transform_input_hash_sha256` for the exact held-out `float64` bits; and
`categorical_output_hash_sha256` for the immutable labels and shape. These identities have
different versioned hash domains. It also records occupancy, scaling provenance, and the
out-of-range policy. Use `"clamp_to_boundary"` only when boundary clamping is part of the declared
observation/quantization model. The default `"error"` policy fails on held-out values outside the
fitted training range.

The report also exposes `distinct_binary64_edge_value_counts`,
`positive_width_interval_counts`, `reachable_binary64_label_counts`, `observed_label_counts`,
`reachable_joint_cardinality`, `structurally_unreachable_joint_cells`, and
`unobserved_reachable_joint_cells`. Nominal counts describe the requested partition; reachable
counts describe the fitted finite-binary64 map; observed counts describe this transform call.
Reachability is not population support, positive probability, or evidence that the bin count is
adequate. Adjacent representable endpoints can collapse nominal labels, and reachable labels need
not be contiguous. The implementation reports that structure without compacting labels.

Categorical SxPID final empirical-PMF component averages and selected two-source PID synergy
formulas use one correctly rounded reduction of already represented finite binary64 operands;
pointwise SxPID Möbius inversion remains compensated. This can change persisted averaged-atom or
synergy last bits and removes operand-order effects only for those named final multisets. It does
not make the estimator, probabilities, products, or logarithms exact. Python binding parity does
not widen that arithmetic or scientific claim.

For independent reimplementation, the three SHA-256 domains (including the final NUL byte shown as
`\0`) are `pid-rs/quantizer/training-input/f64-bits-le/v1\0`,
`pid-rs/quantizer/transform-input/f64-bits-le/v1\0`, and
`pid-rs/quantizer/categorical-output/u128-le/v1\0`. After the domain, encode `nrows` and `ncols` as
little-endian `u128`. Then encode every input value in row-major order as its exact `float64` bit
pattern in little-endian `u64`, or every categorical label in row-major order as little-endian
`u128`. No additional separator, length field, or text conversion is used; the canonical contract
and fixed vectors are documented in the [`pid-core` README](../pid-core/README.md).

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
