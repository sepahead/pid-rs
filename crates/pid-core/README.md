# pid-core

[![CI](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Safe-Rust (`#![forbid(unsafe_code)]`) information-theory estimators with a deliberately narrow 0.9
review surface proposed for 1.0: empirical categorical SxPID, explicitly fitted quantized
variables, Williams--Beer `I_min`, and report-first Euclidean/Chebyshev KSG MI. Version 0.9 makes no
1.x compatibility promise. Continuous shared exclusions, continuous PID, hyperbolic geometry,
hierarchy, and target-adaptive pipelines are default-off research features.

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** The exhaustive provenance and
availability matrix is
[`METHODS.md`](https://github.com/sepahead/pid-rs/blob/main/METHODS.md), generated from
[`method-catalog.json`](https://github.com/sepahead/pid-rs/blob/main/method-catalog.json). In
particular:

| Surface | Origin and boundary |
|---|---|
| Categorical SxPID and `I_min` | Implementations of separately cited paper-defined functionals; their atoms are not interchangeable. |
| SxPID interpretation types | Project-defined scope and claim-boundary metadata around the published SxPID atoms; no new estimator or mathematical novelty is claimed. |
| Fitted quantized categorical PID | pid-rs compositions of fitted equal-width quantization with categorical SxPID or `I_min`; stable code for declared quantized estimands, not paper-defined continuous estimators. |
| Finite-alphabet plug-in convergence | New project-defined theoretical validation for existing PID and Shannon quantities. It defines no estimator and makes no scientific-novelty claim. See the [proof and evidence boundary](https://github.com/sepahead/pid-rs/blob/main/FINITE_ALPHABET_PLUGIN_CONVERGENCE.md). |
| Dependency-colored SxPID concentration | New project-defined validation for the paper-defined categorical SxPID functional. It adds no estimator or public API. It includes one-Λ cumulative bounds, general-source Möbius-row bounds, and complete two-source atom bounds. Exact diamond analysis sharpens only the synergy modulus to Λ − η. The [derivation](https://github.com/sepahead/pid-rs/blob/main/DEPENDENCY_COLORED_SXPID_CONCENTRATION.md), [LaTeX source](https://github.com/sepahead/pid-rs/blob/main/audit/formal/latex/dependency-colored-sxpid-concentration.tex), [PDF](https://github.com/sepahead/pid-rs/blob/main/output/pdf/dependency-colored-sxpid-concentration.pdf), [Lean local-continuity core](https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean), [oracle generator](https://github.com/sepahead/pid-rs/blob/main/scripts/generate-dependency-colored-sxpid-oracle.py), and [Rust fixture test](https://github.com/sepahead/pid-rs/blob/main/crates/pid-core/tests/dependency_colored_sxpid_oracle.rs) have separate evidence boundaries. |
| Continuous shared exclusions / PID2 | Paper-defined Ehrlich-et-al. redundancy estimator and two-source atom reconstruction; experimental here, with separately estimated-term error and project-defined report workflows. |
| Incomplete / full continuous PID3 | pid-rs availability diagnostic versus research-only full-lattice reference reproduction; neither status implies a general mixed-dimensional theorem. |
| General mixed-variable shared exclusions | Schick-Poland et al. define a measure-theoretic functional for arbitrary variable types; this crate provides no practical general estimator for it. Barà et al.'s narrower discrete-target/continuous-source estimator is not implemented here. |
| Heuristics / Lorentz KSG | Project-defined heuristic baselines versus a paper-derived Lorentz-distance KSG adaptation; neither has a pid-rs consistency result for the claimed target setting. |
| r̄, v̄ / Red°, Vul° | The target-conditioned quantities follow the cited Shannon-invariants work; the target-free entropy ratios are explicitly project-defined analogues. |
| Resampling, reports, and resource contracts | Published or standard procedures where cited, surrounded by pid-rs assumptions, failure, provenance, and bounded-execution engineering; no generic calibration theorem is claimed. |
| Added Gaussian-noise provenance | Project-defined experimental Rust software with no defining method paper. Python and run-log schema 2 do not expose it. Gao et al. (2018) supplies KSG-assumption background only. |
| Typed software identity | Project-defined infrastructure implemented locally in Rust and exposed to Python; no estimator, defining paper, or scientific-novelty claim. |

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

## Discrete shared-exclusions PID (i<sup>sx</sup><sub>∩</sub>)

For categorical data, `discrete_sxpid2` / `discrete_sxpid3` compute the shared-exclusions PID of
Makkeh, Gutknecht & Wibral (2021). Labels are exact categories: only row equality matters. The
reference fixtures agree numerically with separate hard-coded values from pinned Abzinger/SxPID
and IDTxl `pid_goettingen` paths within `1e-12` after converting bits to nats. The fixtures have no
checked-in generator or environment lock, so they are bounded validation references rather than
complete external reproduction bundles. The output uses distinct `SxPointwiseAtom` and
`SxAveragedAtom` types, each split into informative and misinformative components; the net is
derived, may be negative, and is never clamped. Exact-real components are non-negative, but a
mathematical zero can retain a tiny negative binary64 residual, and near-cancellation can make the
sign of a much smaller net numerically unresolved. Consumers must use a scale-aware tolerance.

A pointwise entry represents one distinct positive-mass joint realization under the entire
empirical PMF, not one raw row and not a property of the displayed tuple in isolation. Averaged
atoms are uncorrected empirical-PMF plug-in averages over those distinct realizations; unobserved
states are absent, and neither population expectation nor unbiasedness is established. Every
serialized atom carries a project-defined `SxAtomInterpretation` that names the shared-exclusions
measure, identifies aggregation scope, and requires its containing result/record for the concrete
coordinate and pointwise realization. It states that the atom alone does not establish intentional
deception, causal effect, fault attribution, per-source responsibility, a measure-independent PID
coordinate, or an unbiased population estimate. The defining paper's operational receiver
interpretation concerns the cumulative local shared-information quantity; this crate does not
silently extend that story to an isolated Möbius atom. The metadata is an interpretation guard,
not a change to the paper-defined mathematics, and extracting `net_nats()` as a scalar discards it.
The categorical result embeds occupancy/encoding metadata but not source/target names, full matrix
shapes, or input hashes; retain those in caller provenance or a run log.
Persisted consumers must accept only an exactly understood interpretation-contract revision, not
an unknown higher revision.

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
             r.red.net_nats(), r.unq1.net_nats(), r.unq2.net_nats(), r.syn.net_nats());
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
comparator with a different redundancy definition. The stable categorical calls take
`DiscreteMatRef` values. The `imin_pid2_quantized` and `imin_pid3_quantized` compositions instead
accept fixed fitted quantizer outputs and embed every quantization report in their result.
A runnable SxPID demo on canonical gates: `cargo run --release --example discrete_sxpid`.

On the two-bit COPY of independent fair sources, T = (S₁, S₂), categorical SxPID assigns
redundancy ln(4/3) nats, whereas `I_min` assigns ln(2) nats. The identity axiom of
[Harder, Salge & Polani (2013)](https://doi.org/10.1103/PhysRevE.87.012130) instead requires
redundancy equal to I(S₁; S₂), which is zero for these independent sources. This comparison tests
that named axiom, not every PID axiom: distinguish the properties proved for each paper-defined
functional from broader PID desiderata.

The 18- and 166-node categorical lattices are computable for three and four sources, respectively.
[Lyu, Clark & Raviv (2026)](https://doi.org/10.1103/8rzp-w5z1) establish limits on universal
cross-subsystem consistency for multivariate lattice PID. That theoretical boundary is distinct
from enumerating and inverting a chosen lattice; it is not by itself evidence of an implementation
defect or a direct refutation of categorical SxPID.

## Finite-alphabet plug-in convergence (new project analysis)

The
[finite-alphabet plug-in convergence note](https://github.com/sepahead/pid-rs/blob/main/FINITE_ALPHABET_PLUGIN_CONVERGENCE.md)
proves exact-real convergence on fixed finite alphabets and fixed lattices. It covers SxPID for
2–4 sources, Williams--Beer `I_min` for 2–3 sources, and finite-alphabet Shannon entropy, mutual
information, co-information, and O-information. Prefix plug-in quantities converge almost surely
under i.i.d. or strictly stationary and ergodic sampling. Normalized ratios also need a strictly
positive population denominator. The existing PID and Shannon quantities keep the paper-defined or
project-defined origins in
[`METHODS.md`](https://github.com/sepahead/pid-rs/blob/main/METHODS.md). The convergence analysis is
new in pid-rs; it is not a new method or a scientific-novelty claim. The note retains the
derivations, counterexamples, and rejected stronger claims for later audit.
The repository also includes a standalone
[LaTeX paper](https://github.com/sepahead/pid-rs/blob/main/audit/formal/latex/finite-alphabet-plugin-convergence.tex)
and a checked
[PDF rendering](https://github.com/sepahead/pid-rs/blob/main/output/pdf/finite-alphabet-plugin-convergence.pdf).

For i.i.d. data, the note gives a conservative time-uniform envelope from Hoeffding's inequality
and union bounds. A usable support-stabilization time needs a known positive lower bound on
p<sub>min</sub>, the smallest supported cell mass. A training artifact must be independent of the raw
evaluation sequence. The frozen map must be measurable with respect to the training sigma-field
and raw input. It must return a valid finite output with conditional probability one. Evaluation
rows must be conditionally i.i.d. given the training sigma-field.

The pinned Lean artifact proves only deterministic exact-real continuity lemmas. It does not
formalize the stochastic theorem, the PID definitions, or Rust refinement. An independent
100-digit Decimal generator and a Rust test check only a bounded corpus. This base result does not
prove binary64 asymptotic convergence, dependent or drifting windows, same-row or
changing-transform fitting, arbitrary fold pooling, or statistical calibration.

### Dependency-colored categorical extension (new project analysis)

The separate
[dependency-colored SxPID concentration analysis](https://github.com/sepahead/pid-rs/blob/main/DEPENDENCY_COLORED_SXPID_CONCENTRATION.md)
uses a declared deterministic coloring of complete finite source-target rows. Rows must have a
common law. The complete rows in each nonempty color class must be mutually independent.
Dependence across colors can be arbitrary. The result gives a class-size concentration proxy that
is optimal within the declared Hölder–Hoeffding proof scheme, a telescoping all-prefix envelope,
an explicit average-law drift term, and local common-support SxPID atom bounds. The local result
gives one Λ bound for each cumulative term and general-source Möbius-row transfer. For two
sources, redundancy and unique information retain Λ. Exact diamond analysis gives the smaller
synergy modulus Λ − η and sharper averaged synergy caps. These are new project-defined validation
results for the published functional. They do not define a new PID measure or estimator.
The displayed envelope proves almost-sure exact-real plug-in consistency under the sufficient
condition
Vₙ log(n)/n² → 0; a fixed color count is sufficient. Its convergence guarantee for a fixed
reference law under drift also needs the explicit bias term to tend to zero. These conditions are
not necessary under a stronger sampling theorem.

The analysis includes a standalone LaTeX source and reproducible PDF. The
[Lean local-continuity core](https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean)
checks deterministic exact-real algebra only. It does not formalize probability, path integration,
SxPID identification, published component nonnegativity, or the analytic identification of the
conditioned-diamond coordinates with net synergy. Lean proves the exact ordinary-diamond diameter,
the exact candidate-extrema form and normalized corollaries for the eight conditioned-diamond
coordinates, the exact five-coordinate conditioned-nested diameter, and the refined logarithmic
linearization chain. The conditioned-nested zero-side-mass witness is algebraic only. It is not a
supported common-law perturbation or an SxPID-realizability claim. A standard-library
[oracle generator](https://github.com/sepahead/pid-rs/blob/main/scripts/generate-dependency-colored-sxpid-oracle.py)
uses exact Fraction arithmetic for finite identities and 400-digit Decimal arithmetic for
logarithms. It audits all 64 ordered conditioned-diamond coordinate pairs in each of seven exact
rational cases and the ordinary-diamond and conditioned-nested exact identities on the same
inputs. The cases include zero-lift and unnormalized algebra-only boundaries. It reconstructs
three endpoint-valid negative-lift counterexamples, realizes all nine exact extremal regimes with
six positive displayed masses that sum to one, and enumerates other invalid weaker premises.
It also includes six full two-source local atom challenges and a fixed overlapping-window
population law. One gradient case for each sign of `F_b - X_c` and one local atom case are bounded
challenges. The two gradient cases attain the refined bound exactly. The local law gives bounded
near-tightness evidence for the Λ − η synergy modulus. Six two-cell cases reject applying
that modulus to redundancy or unique information. The
[Rust fixture test](https://github.com/sepahead/pid-rs/blob/main/crates/pid-core/tests/dependency_colored_sxpid_oracle.rs)
checks categorical estimator outputs under an absolute ceiling of 32 × `f64::EPSILON` nats. It
uses a scale-aware tolerance with the same multiplier for reconstructed logarithmic constants and
bounds. A separate bounded numerical suite checks ten adaptive refined-modulus cases and six
endpoint-ceiling cases against 400-digit references for the exact real values represented by the
parsed binary64 inputs. Stored hexadecimal payloads bind each parsed operand and subtraction
result. The cases include adjacent branch-seam inputs, the exact lower endpoint of the
upper-branch floor ratio, and strict-support boundaries with normal or subnormal positive floors.
This is not a general interval implementation or binary64 theorem.
The result does not cover pairwise-only independence, adaptive colors, circular windows, an
unspecified mixing premise, continuous SxPID, or a same-sample estimate of the population support
floor.

## Typed software identity

The top-level `software_identity()` function returns a package-safe, serializable description of
the compiled `pid-core` instance. This is a stable **project-defined software contract** with local
code and no defining paper; it implements no PID, MI, or statistical estimator.

```rust
use pid_core::{software_identity, AttestationStatus};

let identity = software_identity();
assert_eq!(identity.package_name(), "pid-core");
assert_eq!(identity.attestation(), AttestationStatus::None);
assert_eq!(identity.reference_artifacts().len(), 2);
```

The result keeps public-Rust-signature revision, source route, selected build context, forensic
reference artifacts, and attestation status in separate typed fields. Signature revision 3 covers
only the exact proposed release-scope feature profiles; it excludes Python API/ABI, estimator and
estimand definitions, numerical behavior, package versions, scientific evidence, and executable
bytes. Source state is route-scoped: workspace Git and Cargo package metadata have different
meanings, while unavailable source identity carries a typed reason.

Workspace Git state is captured once when the build script executes. The probe isolates ambient
Git routing, replacement/graft, config, pathspec, and global/system attribute inputs, then scopes
status to `crates/pid-core`. Bounded conservative Cargo watches cover the package tree, required
workspace markers, root/intermediate/repository attribute locations, linked-worktree control files,
index/shared-index files, effective repository config, bounded `objects/info` metadata, and
files/reftable references. It never recursively watches the complete `.git` or object database. A
deliberately absent recovery watch keeps unavailable or unsupported routes from becoming a
permanently cached answer, and the final typed source result controls that watch even if an earlier
route probe succeeded. Re-running the build script preserves the generated file when its bytes are
unchanged. Git older than 2.45 reports workspace state as `unknown` and retains the recovery watch.
Clean/dirty assumes repository metadata and package files remain stable during the bounded probe;
repeated status/input checks and a final HEAD read detect ordinary races but are not an atomic
filesystem snapshot. Under that assumption, any effective `filter` attribute on a tracked package
path (including unset or unconfigured values), `attr.tree`, tracked symbolic links, and tracked
gitlinks are reported as `unknown`, and no external clean-filter command is executed. The cached
identity is not a live monitor for an in-place Git executable change or later object-store
loss/corruption. The build aborts when an end-of-run equality check finds that typed source state,
workspace layout, or exact bound reference bytes changed during execution.

Each reference digest is SHA-256 of one canonical repository file's exact raw bytes; verifiers must
not parse and re-serialize before hashing. A layout-matched workspace build verifies its current
files, while a packaged build carries the manifest-declared values and need not contain the
repository-relative paths. Declaration snapshots use immutable revision-scoped paths and identify
their generation environment. The append rule checks every HEAD-reachable registry-touch commit
and direct tip parent; it cannot cover an unreachable never-merged branch or externally replaced
history and is not an external transparency log. Equality of identities or digests does not prove
compatibility, authenticity, scientific or application validity,
source/archive/binary equality, data suitability, or cross-platform numerical identity. Format 1
explicitly records `attestation = none` and is not a binary fingerprint.

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

See the [repository README](https://github.com/sepahead/pid-rs) for the full feature list and
scientific cautions, and
[`METHODS.md`](https://github.com/sepahead/pid-rs/blob/main/METHODS.md) for exact paper/code
availability and the distinction between paper-defined, paper-derived, project-defined,
external-reference, and unsupported surfaces.

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
relative units and preprocessing therefore form part of the
I<sup>sx</sup><sub>∩</sub> estimand. Record every
standardization or projection and do not compare or pool atoms across different schemes.
The redundancy estimator and PID2 atom reconstruction implement the cited Ehrlich-et-al.
construction using three separately estimated KSG MI terms. pid-rs adds the structured report and
cross-fit/split-sample workflows; neither the paper-defined algebra nor those wrappers remove
finite-sample error.
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
estimate. Under positive regular branch expansions in one raw radius, finite-union bounds show
that the union has the smallest branch exponent. Higher-exponent branches then have vanishing
relative mass. This standard consequence is new limitation analysis in pid-rs. It establishes
raw-radius branch-weight collapse, not estimator inconsistency, and it supplies no corrected
estimator. `experimental::continuous::incomplete_pid3_diagnostic` is the conservative availability
surface: it returns only
dimension-compatible nodes/atoms and carries exact unavailable dependencies plus
support/dimension/warning metadata. Use `incomplete_pid3_report` to attach separate
caller-declared preprocessing descriptions for every source/target and the observation model. The
full research-gated `pid3_isx_report` attaches the same provenance to all 18 values. These
descriptions are checked only for nonemptiness.

More generally, pid-core has no practical estimator for arbitrary combinations of discrete,
continuous, singular, and mixed support.
[Barà et al. (2025)](https://doi.org/10.1103/58bg-5n9s) provide a narrower nearest-neighbour PID
method for a discrete target with continuous sources. That method is not implemented here, and its
restricted orientation does not make the full-dimensional KSG or research PID3 paths applicable
to general mixed support.

The continuous KSG/PID path also requires finite mutual information. An exact deterministic map
between continuous variables has a singular joint law and infinite MI. An explicit
observation-noise model defines a different noisy population law. Finite mutual information
remains a separate population assumption. Otherwise, use an estimator for discrete or mixed data.

It also requires a unique positive k-th-neighbor boundary: collapsed radii and positive shell ties
are rejected rather than resolved by an undocumented rank convention. Jitter changes the estimated
distribution and is appropriate only under an explicit observation-noise model or as a seeded,
reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support
estimator.

The `experimental::pipelines::GaussianNoiseTransform` API is the report-first path for software-
added Gaussian noise. `GaussianNoiseSpecification` identifies the ideal kernel and excludes the
seed and finite matrices. `GaussianNoiseDeclaration` adds the purpose, exact input binding, and
rationale. `GaussianNoiseStream` binds all stream inputs to one logical matrix and workflow role.
The generated report binds the exact input and output matrices. It also binds a declared
row-resampling context as a separate fact. It does not prove that the declared indices produced the
input matrix.

The transform rejects σ = 0 and a positive scale that causes no bitwise output change. It
records the generator revision and the non-cryptographic replay limit. Separate pseudodraw streams
do not prove probabilistic independence.

For the ideal model Y = X + Z, with independent Z ∼ N(0, σ²I) and σ > 0, the
noisy population law has a smooth, strictly positive density with full ambient support. This
result does not apply to the fixed binary64 matrix as a probability law. It does not establish
finite MI, i.i.d. rows, KSG consistency, calibrated uncertainty, or monotonic PID atoms.

One declaration covers one matrix. Separate source and target reports do not establish one joint
population-noise model. The full-support conclusion for a joint KSG or PID input needs that joint
model across all coordinates. pid-rs does not yet provide this higher-level report.

The contract is project-defined software work that is new in pid-rs. It is not a new statistical
method. `Jitter` remains available as an experimental compatibility type, but it drops this
provenance.

KSG preserves signed finite-sample estimates by default; clamping to zero is an explicit
presentation transform and must not precede identities or inference. Same-sample supervised PLS
wrappers are exploratory and require explicit acknowledgement; fit projectors and choose
hyperparameters on training rows before estimating PID on a separate evaluation set.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.
