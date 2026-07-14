# Proposed pid-rs 1.0 known limitations (0.9 review surface)

The 0.9 candidate will publish these proposed 1.0 limitations for reviewer feedback if the review
release proceeds. They are not an assertion that 1.0 has shipped or that 1.x compatibility has
begun. A green test suite establishes implemented software
behavior on its covered cases; it does not prove that a statistical estimator is valid for an
arbitrary dataset. All information quantities are in nats and signed estimates/atoms are preserved.

## Stable empirical estimators

Categorical SxPID directly evaluates the empirical PMF in binary64. It is deterministic and
invariant to bijective relabeling of complete categorical states, but it is not exact population
PID and inherits finite-sample plug-in bias. Sparse or unobserved states remain unobserved.

Williams–Beer `I_min` is a different redundancy definition. Its atoms cannot be pooled with or
interpreted as shared-exclusions atoms.

Fitted quantized SxPID estimates PID of the declared quantized variables. Results depend on fitted
edges, scaling, bin count, training sample, and empty/sparse occupancy. Quantization does not solve
the curse of dimensionality and cannot silently turn a mixed or singular law into the continuous
estimand.

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

## Continuous shared exclusions and PID

Continuous two-source shared exclusions and PID2 are default-off experimental estimators. The
implementation follows the cited finite-sample construction in its restricted domain, but no claim
of unbiasedness or universal consistency is made. The disjunctive common-radius gauge depends on
relative source units and preprocessing. Equal ambient source dimensions are necessary for the
implemented comparison; they do not establish equal intrinsic dimensions or compatible measures.

PID2 atoms are algebraically reconstructed from separately estimated MI/redundancy terms. Exact
reconstruction of those represented terms does not eliminate their different finite-sample biases.
The complete PID2 report's covariance matrices describe aligned local estimator contributions; they
are not calibrated sampling covariance, standard errors, or confidence intervals. Cross-fit reports
keep fold-specific gauges and neighborhood coordinates separate and deliberately do not pool them.

Partial continuous PID3 is an incomplete diagnostic. An available node or atom means its exact
implemented dependencies were dimension-compatible, not that a complete PID exists. Full
continuous PID3 contains mixed-dimensional singleton-versus-pair branches whose required measure
theory is unresolved here; it is research-only reference reproduction.

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

Known-failure fixtures intentionally cover mixed-dimensional collapse, atom/continuous mixtures,
singular maps, tied shells, local dimension heterogeneity, high-dimensional concentration,
hyperbolic nonlocal radii, same-sample PLS optimism, and invalid permutation nulls. A deliberate
failure is evidence that an unsupported regime is rejected or exposed, not that it became valid.

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
