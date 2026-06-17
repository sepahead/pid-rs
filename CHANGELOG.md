# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

## [Unreleased]

## [0.1.0] - 2026-06-17

Initial public release.

### Added

- **`pid-core`** — continuous and discrete information-decomposition estimators:
  - KSG mutual information (Kraskov et al. 2004), L∞ joint metric, strict-radius marginal
    counting, optional bit-identical `parallel` (rayon) path.
  - Continuous shared-exclusions redundancy `I^sx_∩` (Ehrlich et al. 2024), disjunction
    neighbourhoods.
  - 2- and 3-source PID atoms (`pid2_isx`, `pid3_isx`) whose Möbius identities hold by
    construction; discrete `I_min` PID over the full 18-antichain lattice.
  - Shannon invariants: co-information, O-information, average degrees of redundancy/vulnerability.
  - Geometry diagnostics (intrinsic dimension, distance concentration, Gromov hyperbolicity),
    preprocessing (standardisation, PCA, PLS, hash projection, seeded jitter), block bootstrap
    and permutation tests, and the `exp0` estimator-validation harness.
- **`pid-runlog`** — versioned, hash-chained run-log schema with a `pid-runlog-replay`
  validation CLI.
- Worked example (`cargo run --example ksg_and_pid`), CI (fmt / clippy `-D warnings` / tests /
  docs / MSRV / smoke), and an analytic-reference test suite (Gaussian-channel MI, XOR/COPY PID
  structure, PID identities to `1e-10`).

### Notes

This release incorporates fixes from an internal soundness audit: the default 2-source/
co-information paths no longer clamp MI terms before the algebraic identities; discrete-PID and
Shannon-invariant summation is now order-deterministic (`BTreeMap`); the permutation p-value uses
the add-one correction; and the public bootstrap/permutation helpers return `Err` instead of
panicking on invalid configuration. See [Known limitations](README.md#known-limitations) for the
tracked follow-ups.

[Unreleased]: https://github.com/sepehrmn/pid-rs/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sepehrmn/pid-rs/releases/tag/v0.1.0
