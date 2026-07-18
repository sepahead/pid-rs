# Proposed pid-rs 1.0 known limitations (0.9 review surface)

The published 0.9 GitHub-only source-review prerelease presents these proposed 1.0 limitations for reviewer feedback.
They are not an assertion that 1.0 has shipped or that 1.x compatibility has begun. A green test
suite establishes implemented software behavior on its covered cases; it does not prove that a
statistical estimator is valid for an arbitrary dataset. All information quantities are in nats
and signed estimates/atoms are preserved.

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** [`METHODS.md`](METHODS.md), generated
from [`method-catalog.json`](method-catalog.json), is the authoritative map of paper-defined,
paper-derived, project-defined, externally compared, and unsupported surfaces. A feature gate,
test fixture, Python binding, or stable API label does not change that origin or prove a population
theorem.

The published 0.9 prerelease is a GitHub-only source prerelease containing source, scope records,
review provenance, and checksums. It does not publish crates, wheels, binaries, docs.rs
documentation, SBOMs, or separate build-provenance attestations, and it has no software DOI or
Zenodo record. GitHub release immutability automatically supplies a signed release attestation;
that integrity record is not independent scientific review. Earlier release commits remain
reachable through immutable changelog links after obsolete tag refs were retired. The later
registry and signed-review qualification process is outside the 0.9 release boundary.

## Stable empirical estimators

Categorical SxPID directly evaluates the empirical PMF in binary64. It is deterministic and
invariant to bijective relabeling of complete categorical states, but it is not exact population
PID and inherits finite-sample plug-in bias. Sparse or unobserved states remain unobserved.

Williams–Beer `I_min` is a different redundancy definition. Its atoms cannot be pooled with or
interpreted as shared-exclusions atoms.

On the two-bit COPY of independent fair sources, `T = (S1, S2)`, categorical SxPID assigns
`ln(4/3)` nats of redundancy and `I_min` assigns `ln 2` nats. The identity axiom of
[Harder, Salge & Polani (2013)](https://doi.org/10.1103/PhysRevE.87.012130) instead requires
redundancy equal to `I(S1;S2)`, which is zero for these independent sources. This comparison is
against that named axiom, not every PID axiom: properties proved for a functional in its defining
paper and broader PID desiderata must be reported separately.

Fitted quantized SxPID and fitted quantized `I_min` estimate their respective PIDs of the declared
quantized variables. Results depend on fitted edges, scaling, bin count, training sample, and
empty/sparse occupancy. Quantization does not solve the curse of dimensionality and cannot silently
turn a mixed or singular law into a continuous estimand.

## Conditional KSG MI

The stable Euclidean/Chebyshev KSG reporting API requires an explicit assertion of regular,
full-dimensional, absolutely continuous marginal and joint population laws with finite mutual
information. A finite sample cannot prove that assertion.

- Exact ties, duplicate rows, zero radii, and ambiguous positive k-th shells are incompatible with
  the implemented continuous rank formulas and fail closed.
- All-unique observations do not prove continuity, a common reference measure, or finite MI.
- A deterministic continuous map has singular joint support and can have infinite MI.
- Bias and variance grow in high dimension, under strong dependence, and when neighbourhood radii
  are nonlocal. Passing a one-dimensional Gaussian oracle is not universal validation.
- Finite-sample KSG values can be negative. Clamping changes downstream algebra and is presentation
  only.
- The kd-tree backend has exact output parity with brute force but retains worst-case quadratic
  query behavior.

Use k/sample-size trajectories, shell/radius/count reports, geometry diagnostics, representation
sensitivity, and a matched synthetic oracle. These diagnostics can falsify some assumptions but do
not certify them.

Normalized average redundancy/vulnerability quantities are unitless screening ratios, not PID
atoms or universal validation scores. Their denominator is an estimated joint MI: a non-positive
or policy-small denominator makes the ratio explicitly undefined. `NormalizedInvariantReport`
records that status and the caller-selectable threshold in nats; choosing a smaller threshold does
not make a noise-dominated ratio scientifically stable.

The target-conditioned `average_degree_of_redundancy` (`r̄`) and
`average_degree_of_vulnerability` (`v̄`) follow the cited Shannon-invariants formulation.
`red_degree_discrete` (`Red°`) and `vul_degree_discrete` (`Vul°`) are project-defined, target-free
entropy-ratio analogues. Their notation and bounds do not make them the published target
quantities, PID atoms, or substitutes for a target-conditioned analysis.

## Continuous shared exclusions and PID

Continuous two-source shared exclusions and PID2 are default-off experimental estimators. The
implementation follows the cited finite-sample construction in its restricted domain, but no claim
of unbiasedness or universal consistency is made. The disjunctive common-radius gauge depends on
relative source units and preprocessing. Equal ambient source dimensions are necessary for the
implemented comparison; they do not establish equal intrinsic dimensions or compatible measures.

PID2 atoms are algebraically reconstructed from separately estimated MI/redundancy terms. Exact
reconstruction of those represented terms does not eliminate their different finite-sample biases.
The atom reconstruction is defined in Ehrlich et al.; pid-rs's structured report, split-sample, and
cross-fit workflows are project-defined additions.
The complete PID2 report's covariance matrices describe aligned local estimator contributions; they
are not calibrated sampling covariance, standard errors, or confidence intervals. Cross-fit reports
keep fold-specific gauges and neighborhood coordinates separate and deliberately do not pool them.

Partial continuous PID3 is an incomplete diagnostic. An available node or atom means its exact
implemented dependencies were dimension-compatible, not that a complete PID exists. Full
continuous PID3 contains mixed-dimensional singleton-versus-pair branches whose required measure
theory is unresolved here; it is research-only reference reproduction.
Schick-Poland et al. define a measure-theoretic shared-exclusions PID functional for arbitrary
discrete, continuous, and mixed variable types. pid-rs does not implement a practical general
estimator for that functional; the paper-defined quantity does not make the full-dimensional KSG
or research PID3 code applicable to mixed support.
[Barà et al. (2025)](https://doi.org/10.1103/58bg-5n9s) provide a narrower nearest-neighbour PID
method for a discrete target with continuous sources. That orientation is not implemented here and
does not close the broader arbitrary-support, arbitrary-orientation estimator gap.

For three and four sources, enumerating and inverting a chosen categorical redundancy lattice is a
computability statement. [Lyu, Clark & Raviv (2026)](https://doi.org/10.1103/8rzp-w5z1) establish
incompatibilities among universal cross-subsystem consistency requirements for multivariate
lattice PID. Their result motivates reporting lattice computability, properties proved for a
chosen redundancy functional, and broader consistency desiderata separately; it is not by itself
evidence of a pid-rs code defect or a direct refutation of categorical SxPID.

Heuristic shared-exclusions methods are research-only. Their presence behind a feature is not a
consistency or calibration claim.

## Geometry and hyperbolic paths

Intrinsic-dimension and distance-concentration outputs are sample diagnostics, not population
certificates. Local dimension can vary across a dataset, and nonlocal radii invalidate small-ball
interpretations.

Lorentz-hyperbolic distance conversion is numerically guarded, but pairwise hyperbolic KSG remains
research-only because correct distance computation does not prove an entropy/MI estimator on that
manifold. Hyperbolic shared exclusions and PID are unsupported.

## Preprocessing, uncertainty, and testing

Target-adaptive preprocessing fitted on evaluation rows leaks target information. Fit and select
standardization/PCA/PLS/quantization on training data, freeze it, and estimate on held-out rows.
Same-sample supervised PLS→PID is exploratory only. Constant columns require an explicit fitted
policy; fitted parameter/training hashes establish identity but do not prove train/evaluation
separation or scientific suitability.

Moving-block bootstrap and permutation procedures are valid only under their stated dependence or
exchangeability assumptions. Restricted circular shifts are approximate surrogate scores, not
exact randomization p-values. Random-origin circular-grid kNN subsample percentile ranges are sensitivity
diagnostics, not calibrated confidence intervals for the full-sample estimate. BH requires its
dependence conditions; BY is more conservative but still assumes valid input p-values.
Typed declarations and complete failure retention prevent silent reinterpretation, but they do not
establish the caller's sampling assumptions or calibrate a generic statistic. Cooperative
cancellation returns no partial estimate and does not make an intrinsically expensive procedure
cheap.

The cited moving-block, permutation, add-one p-value, and BH/BY procedures remain distinct from
pid-rs's project-defined typed assumption records, scheduling, failure-retention, and report
schemas. Those engineering additions do not create a generic confidence-interval or
randomization-test theorem for an arbitrary callback statistic.

Known-failure fixtures intentionally cover mixed-dimensional collapse, atom/continuous mixtures,
singular maps, tied shells, local dimension heterogeneity, high-dimensional concentration,
hyperbolic nonlocal radii, same-sample PLS optimism, and invalid permutation nulls. A deliberate
failure is evidence that an unsupported regime is rejected or exposed, not that it became valid.

## Software identity

`software_identity()` is project-defined infrastructure with local Rust/Python code and no defining
method paper. It is an inspectable record, not authentication, an estimator-validity certificate,
or a binary fingerprint. Its public Rust API revision covers only the exact proposed release-scope
feature profiles; it does not version Python API/ABI, numerical behavior, method definitions,
scientific evidence, package-version compatibility, or executable bytes.

Workspace source state is limited to `crates/pid-core`: repository-root files, `Cargo.lock`, and
sibling crates are outside its clean/dirty flag. In a layout-matched workspace, the Git route is
authoritative: a Git failure produces a typed unavailable state and does not fall back to a stray
`.cargo_vcs_info.json`. Here, layout-matched includes the expected canonical directory structure,
repository markers, and a `.git` entry at the root. A source archive without `.git` is an
unrecognized layout, not a layout-matched Git failure. Other layouts use Cargo package metadata
when valid. Its `dirty` field is a version-dependent, best-effort archive-creation observation, not
the current extracted tree; an omitted flag is reported as `unknown`, not inferred clean. Either
route may be unavailable, and a named commit does not prove authorship, authenticity, or equality
between that commit, a source archive, and an executable. Format 1 accepts only full lowercase
40-hex SHA-1 commit identifiers; Git SHA-256 object identifiers are rejected as unsupported rather
than truncated or reinterpreted.

The workspace result is a build-script-time snapshot, not a live Git monitor. Ambient Git routing,
replacement/graft, config, pathspec, ref-backend, and global/system attribute overrides are
neutralized. Bounded Cargo watches cover ordinary package, marker, attribute, linked-worktree,
index, config, and files/reftable-ref transitions; unavailable states retain an absent recovery
watch. The bounded `objects/info` metadata directory is watched, including repository-local
alternate-store routing, but the referenced external object stores are not live-monitored. Any
effective `filter` attribute on a tracked package path (including unset or unconfigured values),
`attr.tree`, tracked symbolic links, and tracked gitlinks yield `unknown`. Deliberate manual
repository-layout rewrites that create a previously absent `commondir`, in-place replacement of the
Git executable, and later loss/corruption of an otherwise unchanged object database are outside
that invalidation contract. The cached observation remains the state captured by the earlier build;
it does not claim current tool or object-store availability. Config includes and unsupported
ref-storage payloads intentionally make Cargo re-run the probe conservatively.

Workspace clean/dirty probing requires Git 2.45 or newer. Older versions yield `unknown` because
the isolation contract depends on versioned Git behavior for global configuration, fsmonitor, and
lazy fetching. A clean/dirty result also assumes repository metadata and package files do not change
concurrently during the bounded probe. Repeated status/input checks and a final HEAD read catch
ordinary mid-probe changes, but no finite reread is an atomic filesystem snapshot; ABA mutation and
hostile concurrent rewriting remain outside the claim.

The build script repeats the typed source, workspace-layout, and exact reference-byte checks at the
end and aborts when those claimed inputs changed during execution. This closes the ordinary Cargo
mtime window but does not turn the filesystem into a transaction: a change after the final check or
an ABA rewrite remains governed by the stable-input assumption.

Build context records only the compiler version when discoverable, target, Cargo profile,
optimization level, debug-information flag (not debug assertions), and enabled `pid-core`
features. It omits dependency artifacts, linker inputs, arbitrary compiler flags, environment, and
output bytes. Two different executables can therefore share the recorded fields, and legitimate
builds can differ without implying a scientific change.

Reference SHA-256 values identify the exact raw bytes of canonical repository files, not necessarily
the Git blob at the source commit. Verification depends on the layout in which `pid-core` is
compiled, not on the final artifact type: an exact layout-matched workspace verifies the current
root files against the manifest, while other layouts carry the manifest-declared values without
re-verifying those files. Consequently, a source archive without `.git` does not re-verify root
reference files even if the archive contains them. Published crate archives and wheels need not
contain the repository-root paths; `repository_path` is routing metadata, not a package-local
availability promise. Matching hashes does not establish API compatibility, data quality,
scientific or application validity, source/archive/binary equality, or cross-platform numerical
identity. Format 1 explicitly reports `attestation = none`; no source, dependency-graph,
supply-chain, or executable attestation should be inferred.

Public Rust declaration snapshots are retained under immutable revision-scoped paths with their
generation context. A registry entry names the preceding source commit whose declarations were
captured; the following evidence commit contains the snapshot bytes. Append preservation checks
every HEAD-reachable commit that touched the registry, each direct tip parent, and monotone source
ancestry. Once a committed registry binding is an ancestor, the exact snapshot bytes are also
checked at binding states, direct tip boundaries, and every reachable commit in that snapshot
path's full history. Pre-binding states remain outside that interval. An unreachable never-merged
branch, force-push, complete repository rollback, or coordinated replacement of code and internal
hashes cannot be detected without an external monotonic trust anchor; the registry is not a
transparency log, timestamp, or attestation. The local checker removes ambient Git routing and
configuration, disables replacement/graft overlays, and requires the canonical Git worktree root
to match the files being checked, but those controls cannot recover objects or references absent
from the presented repository.

## Resources, Python, and run logs

Some exact pairwise and lattice operations remain quadratic or combinatorial. Use the resource
preflight/budget APIs; a successful estimate at one size is not a runtime guarantee at a larger
size. Allocation and parser budgets reject oversized work rather than overcommit memory.
Generic resampling/permutation estimates cannot see allocations or complexity inside a caller's
opaque statistic callback. Experimental PLS/logistic QR and dense-factorization paths conservatively
preflight and hard-cap solver dimensions, but nalgebra still owns internal infallible allocations;
those quarantined research backends therefore cannot promise recovery from operating-system
allocator exhaustion below the declared ceiling.
Run-log byte/event/container limits are enforced before or during decoding and aggregate replay,
and destination vectors reserve fallibly. Serde-owned nested strings/JSON values and deterministic
`BTreeMap` nodes still use Rust's infallible allocator within those finite ceilings; like nalgebra,
they cannot convert process-wide allocator exhaustion below the chosen ceiling into a recoverable
error. Choose limits comfortably below the process memory boundary.

The Python extension uses native code through PyO3. Stable calls validate/copy or otherwise own
inputs before GIL release; callers must still avoid assuming that concurrently mutated arrays have
snapshot semantics unless the specific API documents it.

Run-log hashes and colocated sidecars detect internal inconsistency; they do not authenticate a log
that an attacker can replace together with its digest. Store the release/run digest in a trusted
external signed anchor when tamper evidence is required. Atomic sidecar replacement flushes the
new file on every supported desktop target and additionally flushes the parent directory on Unix.
Rust exposes no portable Windows directory-flush operation, so an immediate power loss can lose a
just-renamed Windows directory entry even though readers never observe a truncated sidecar.

For reproducible release verification, see [RELEASE_REPRODUCTION.md](RELEASE_REPRODUCTION.md).
