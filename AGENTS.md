# AGENTS.md

Guidance for AI coding agents (and humans) working in **pid-rs**. Tool-agnostic; Claude Code also
reads `CLAUDE.md`, which imports this file.

This file is the operational guide (policy, commands, conventions, code map). For the *scientific*
picture — what PID is, which estimator does what, the references, and the caveats — read
[`README.md`](README.md) first; per-crate docs live in each `crates/*/README.md`.

## Contents

- [Commit & attribution policy (READ FIRST)](#commit--attribution-policy-read-first)
- [What this project is](#what-this-project-is)
- [Method provenance and novelty claims](#method-provenance-and-novelty-claims)
- [Workspace layout](#workspace-layout)
- [Where things live in `pid-core`](#where-things-live-in-pid-core)
- [Build / test / lint (mirror CI)](#build--test--lint-mirror-ci)
- [Conventions to preserve](#conventions-to-preserve)
- [Before you push](#before-you-push)

## Commit & attribution policy (READ FIRST)

- **Do not add AI/agent attribution to commits or pull requests.** Never append a
  `Co-Authored-By:` trailer that names Claude, an AI, or an agent, and never add
  "Generated with Claude Code" / "Co-authored with …" / any agent advertising to commit messages
  or PR descriptions. Commits are authored **solely by the human contributor**.
- **Do not sign commits or tags.** This repository sets `commit.gpgsign=false` and
  `tag.gpgsign=false` locally; leave them unsigned.
- This is enforced by `.claude/settings.json` (`attribution.commit` and `attribution.pr` are empty
  strings). Do not re-introduce attribution there or in any commit you author.

## What this project is

A safe-Rust workspace for **partial information decomposition** (the shared-exclusions `I^sx_∩`
measure) and the continuous **k-nearest-neighbour** estimators it builds on (KSG mutual
information), plus discrete `I_min` PID, Shannon invariants, geometry diagnostics, preprocessing/PLS,
dependence-aware uncertainty quantification (block bootstrap, permutation nulls, and
Benjamini–Hochberg/Yekutieli FDR adjustment), reproducible run-logs, typed package-safe software
identity, and Python bindings.

## Method provenance and novelty claims

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** [`method-catalog.json`](method-catalog.json)
is the machine-readable authority and [`METHODS.md`](METHODS.md) is its exhaustive human rendering.
Use the catalog's distinctions consistently:

- **paper-defined** for a quantity or estimator defined by a cited publication;
- **paper-derived** for a repository composition of published quantities or algorithms;
- **project-defined** for a repository diagnostic, contract, report, or workflow;
- **external reference code** for a separately maintained comparison implementation; and
- **no implementation** for an explicitly unsupported request.

Do not infer paper support from the existence of code, infer implementation from a paper citation,
or call a bounded fixture comparison a general validation result. Fitted quantized SxPID is a
project composition for a quantized estimand; PID2 composes separately estimated published terms;
its atom construction is defined in Ehrlich et al., while pid-rs report/cross-fit wrappers are
project-defined. Incomplete PID3 is an availability diagnostic; the full paper-defined
mixed-dimensional PID3 remains research-only here. Heuristics are project-defined baselines;
Lorentz KSG is a paper-derived research adaptation. Target-free `Red°`/`Vul°` are project-defined
analogues rather than the published target-conditioned `r̄`/`v̄`; resampling contracts and run
logs add engineering without a generic calibration theorem; Python exposure is a binding status,
not a method-origin status. The software-identity envelope is project-defined infrastructure with
local Rust/Python code, no defining method paper, and no scientific-novelty or attestation claim.

When a method, estimator, diagnostic, or binding changes, update the catalog entry, its source
marker/documentation, and any audience-specific summary that becomes inaccurate, then run:

```text
python3 scripts/check-method-catalog.py
```

## Workspace layout

| Crate | Path | Role |
|---|---|---|
| `pid-core` | `crates/pid-core` | The estimators, PID atoms, invariants, geometry, preprocessing, and the `exp0` diagnostic binary. `#![forbid(unsafe_code)]`. |
| `pid-runlog` | `crates/pid-runlog` | Versioned, content-addressed run-log schema + the `pid-runlog-replay` CLI. |
| `pid-python` | `crates/pid-python` | PyO3 + maturin bindings (the `pid_core_rs` module). Built as an `abi3` wheel, not via plain `cargo`. |

## Where things live in `pid-core`

The public API is re-exported from `crates/pid-core/src/lib.rs` under an explicit namespace split:
`stable::{categorical, quantized, imin, continuous, preprocessing}` and `diagnostics` are the
default surface (`stable::continuous` is report-first — `ksg_mi_report` + `SupportContract`; the
raw scalars are deliberately demoted to `experimental::continuous::raw_scalars`), while every
research family lives under a default-off, feature-gated `experimental::*` module (`continuous`,
`isx_heuristics`, `mixed_dimension_pid3`, `hyperbolic`, `hierarchy`, `pipelines`). `lib.rs` is the
authoritative map of what is public where; the implementation is split by topic in the modules
below. Tests live in two places. Same-stem integration files under `crates/pid-core/tests/`
cover `ksg` (+ `ksg_report`), `isx`, `pid2`, `pid3` (+ `pid3_partial`), `geometry`, `invariants`,
`preprocess`, `observation_noise`, `distance_matrix`, `hierarchy`, the `sxpid_*` family for
`sxpid.rs` (`_axioms`, `_properties`, `_nsource`, `_bootstrap`, `_interpretation`, `_reference`,
`_gaussian_oracle`,
`_exhaustive_oracle`), `imin.rs` +
`discrete_pid_properties.rs` for `discrete_pid.rs`, `fitted_quantized_sxpid.rs` for the
quantizer→sxpid path, `permutation_and_fdr.rs` for `pipeline.rs`, and the cross-cutting suites
(`cross_validation.rs`, `gaussian_pid_atoms.rs`, `hyperbolic_mi.rs`, `parallel_bit_identity.rs`,
`known_failures.rs`, `continuous_reports.rs`, `continuous_resource_contracts.rs`,
`discrete_resource_contracts.rs`, `software_identity.rs`, `software_identity_build.rs`), with shared
fixture/digest helpers in `tests/common/mod.rs`.
`bootstrap.rs`, `pls.rs`, `logistic.rs`, `discrete_pid.rs`, and the kernel modules additionally
carry in-module `#[cfg(test)]` blocks.

The gate column is the cargo feature that compiles the module in (from the `#[cfg(feature = …)]`
mod declarations in `lib.rs`); "—" means it is part of the default build. Where a module compiles
by default but re-exports some items only under a feature, the row says so.

| Module (`src/…`) | Gate | Key public items | What it covers |
|---|---|---|---|
| `ksg.rs` | — | stable `ksg_mi_report`, `KsgConfig`, `NegativeHandling`; raw `ksg_mi` / `ksg_local_mi_terms` only under `experimental::continuous::raw_scalars` | KSG continuous MI estimator; the stable surface is report-first. |
| `isx.rs` | `experimental-continuous` | `isx_redundancy_report`, `IsxConfig`, `IsxMethod`; raw `isx_redundancy` under `raw_scalars` | Continuous `I^sx_∩` redundancy (Ehrlich et al. 2024). `experimental-heuristics` additionally exposes `experimental::isx_heuristics` — formula-labelled baselines that do **not** estimate the paper functional. |
| `pid2.rs` | `experimental-continuous` | `pid2_isx`, `Pid2Config`, `Pid2Result`, cross-fit/split-sample reports | Continuous 2-source PID atoms (Red/Unq1/Unq2/Syn). |
| `pid3.rs` | `experimental-continuous`; full lattice `research-mixed-dimension-pid3` | `incomplete_pid3_*`; research `pid3_isx` | Incomplete diagnostics and research-only full 3-source continuous lattice. |
| `discrete_pid.rs` | — | `imin_pid2`, `imin_pid3` (+ `_quantized` / `_with_budget` variants), exported as `stable::imin` | Discrete `I_min` PID (Williams & Beer 2010). |
| `sxpid.rs` | — | `discrete_sxpid2/3/n`, `fitted_quantized_sxpid2/3/n`, `SxPointwiseAtom`, `SxAveragedAtom`, `SxAtomInterpretation`, `SxAtomDecompositionMeasure` | Empirical categorical shared-exclusions PID `i^sx_∩` (2–4 sources); typed pointwise/averaged atoms plus a project-defined measure/scope/claim boundary. |
| `quantizer.rs` | — | `EqualWidthQuantizer`, `QuantizerConfig` | Training-fitted reusable equal-width quantization with edge/occupancy provenance. |
| `invariants.rs` | — | `o_information_discrete`, `co_information_pairwise_discrete`, `red_degree_discrete` / `vul_degree_discrete` | Discrete co-/O-information, `r̄`, `v̄` screening stats. |
| `ci.rs` | `experimental-continuous` | `co_information_pairwise/triplet` (+ report forms) | Continuous (KSG-based) co-information. |
| `geometry.rs` | — | intrinsic-dimension, distance-concentration, four-point-delta summaries | Geometry diagnostics for kNN-validity. |
| `support.rs` | — | `SupportContract`, `continuous_input_diagnostics`, shell diagnostics | Fail-closed population-support declarations and one-sided sample diagnostics. |
| `report.rs` / `resource.rs` | — | `EstimandIdentity`, `EstimateReport`, `ResourceBudget`, `CancellationToken` | Report-first scientific status/assumptions and bounded memory/operation preflight. |
| `identity.rs` (+ crate `build.rs` / `build_support.rs`) | — | `software_identity`, `SoftwareIdentity`, typed API/source/build/reference/attestation components | Project-defined, package-safe software identity; no estimator or defining paper. |
| `preprocess.rs` | — | `Standardizer`, `PcaProjector`, `HashProjector`; legacy `Jitter` re-exported only under `experimental-pipelines` | Fitted standardization, PCA, hash projection, and the unreported jitter migration primitive. |
| `observation.rs` | `experimental-pipelines` | `GaussianNoiseSpecification`, `GaussianNoiseDeclaration`, `GaussianNoiseStream`, `GaussianNoiseTransform`, `GaussianNoiseApplicationReport` | Project-defined typed provenance for an ideal added-Gaussian kernel and its deterministic binary64 application. This is not a PID estimator or a scientific-novelty claim. |
| `pls.rs` | `experimental-pipelines` | `PlsProjector` | Partial least squares supervised projection. |
| `bootstrap.rs` | `experimental-pipelines` | `block_bootstrap`, `block_bootstrap_paired`, `BootstrapConfig` | Dependence-aware block-bootstrap uncertainty quantification. |
| `pipeline.rs` | `experimental-pipelines` | `permutation_rows_pvalue*`, `permutation_pid3*`, `benjamini_hochberg` / `benjamini_yekutieli`, `pls_cv_select_components`, `pls_project_then_pid3`, `screen_pid2_pairs`, `bootstrap_rows_stats` | Composed PLS → PID → UQ pipelines: permutation nulls, FDR adjustment, PLS component selection, pair screening — the bulk of `experimental::pipelines`. |
| `same_sample.rs` | `experimental-pipelines` | `ExploratorySameSampleQuantizedResult`, `SameSampleEqualWidthProvenance` | Feature-only provenance wrapper for same-row equal-width adapters without mutating stable categorical encoding enums. |
| `logistic.rs` | `experimental-pipelines` | `LogisticRegression`, `LogisticRegressionConfig` | L2-regularised logistic regression (Newton–IRLS); internal failure-detector primitive. |
| `hierarchy.rs` | `experimental-hierarchy` | `hierarchical_pairwise`, `hierarchical_triplet`, `HierarchicalConfig` | Fast→slow screening for many-source settings. |
| `hyperbolic.rs` | `experimental-hyperbolic` | `HyperbolicMetric`, `hyperbolic_distance_lorentz`, Poincaré ↔ Lorentz maps, typed KSG and geometry diagnostics | Hyperbolic (Lorentz-model) pairwise MI and diagnostics isolated from stable metric/config/report types. |
| `kdtree.rs` / `nn.rs` | — (internal) | — | Exact Chebyshev kd-tree and brute-force kNN backends behind KSG/`i^sx` (bit-identical to each other; parity-tested). |
| `metric.rs` / `matrix.rs` / `error.rs` | — | `Metric`, `MatRef` / `MatOwned` / `DiscreteMatRef`, `PidError` / `PidResult` | Metrics, borrowed/owned matrix views, and the error taxonomy — the types every estimator signature uses. |
| `distance_matrix.rs` | — | `symmetric_distances`, `SymmetricDistanceMatrix` | Budgeted pairwise distance matrices (under `diagnostics`). |
| `par.rs` / `stats.rs` | — (internal) | — | Index-ordered parallel map (keeps the `parallel` feature bit-identical to serial) and digamma/statistics helpers. |
| `bin/exp0.rs` | `experimental-all` | — | The `exp0` validation/diagnostic binary (see below). |

Runnable end-to-end examples live in `crates/pid-core/examples/`: `ksg_and_pid.rs` (continuous MI +
2-source `I^sx_∩` PID on a synthetic system) and `discrete_sxpid.rs` (discrete shared-exclusions PID
on canonical logic gates, with deterministic reference-matching output).

## Build / test / lint (mirror CI)

```bash
cargo test --locked --workspace --exclude pid-python        # stable workspace tests
cargo test --locked -p pid-core --no-default-features       # approved stable default surface
cargo test --locked -p pid-core --features parallel         # exact data-parallel kNN path
cargo test --locked -p pid-core --all-features              # every default-off research surface
cargo test --locked --release -p pid-core --all-features    # release-mode numerical fixtures
cargo fmt --all --check                                     # formatting
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS="-D warnings" cargo doc --locked -p pid-core --no-default-features --no-deps
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
# the docs.rs gate is cargo *rustdoc*, not cargo doc — --lib is required because --all-features
# also exposes bin/example/bench targets, and cargo forwards trailing args to only one target
RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-core --all-features --lib -- --cfg docsrs
RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-runlog --all-features --lib -- --cfg docsrs
# worked example: MI + 2-source PID on a synthetic system (fast sanity check)
cargo run --release -p pid-core --features experimental-continuous --example ksg_and_pid
# smoke: the exp0 diagnostic + a run-log round-trip
cargo run -p pid-core --all-features --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl
python3 scripts/check-software-identity.py               # identity/schema/feature/digest/package coherence
python3 scripts/check-software-identity-self-test.py     # fail-closed mutation suite
python3 scripts/check-z3-pid2-algebra.py                 # exact PID2/PID3 lattice obligations; Z3 4.16.0
python3 scripts/check-z3-pid2-algebra-self-test.py       # satisfiable proof mutations must fail closed
python3 scripts/check-lean-ksg-integer-harmonic.py       # 19 conditional exact harmonic theorems
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py  # 14 semantic proof mutations
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 scripts/check-z3-ksg-integer-harmonic.py         # 4 premise-explicit QF_UFLIRA obligations
python3 -O scripts/check-z3-ksg-integer-harmonic.py
python3 scripts/check-z3-ksg-integer-harmonic-self-test.py   # 12 semantic + 52 separate firewall controls
python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py
python3 scripts/generate-ksg-local-arithmetic-oracle.py  # no-write replay of all 8,198 rows
python3 -O scripts/generate-ksg-local-arithmetic-oracle.py
python3 scripts/check-ksg-harmonic-exact-enclosure.py    # 6,920 Fraction + directed-Decimal route
python3 -O scripts/check-ksg-harmonic-exact-enclosure.py
python3 scripts/check-ksg-harmonic-exact-enclosure-self-test.py  # 29 scientific/custody + 2 comparator controls
python3 -O scripts/check-ksg-harmonic-exact-enclosure-self-test.py
python3 scripts/generate-ksg-harmonic-modular-certificate.py
python3 -O scripts/generate-ksg-harmonic-modular-certificate.py
python3 scripts/check-ksg-harmonic-modular-certificate.py
python3 -O scripts/check-ksg-harmonic-modular-certificate.py
python3 scripts/check-ksg-harmonic-modular-certificate-self-test.py  # 28 scientific/custody + 2 JSON controls
python3 -O scripts/check-ksg-harmonic-modular-certificate-self-test.py
# The unscoped revision checker must remain nonzero with all 13 gates open at integration_no_go.
python3 scripts/check-ksg-harmonic-revision.py --claim-only
python3 -O scripts/check-ksg-harmonic-revision.py --claim-only
python3 scripts/check-ksg-harmonic-revision-self-test.py --claim-only  # 141 claim mutations
python3 -O scripts/check-ksg-harmonic-revision-self-test.py --claim-only
python3 scripts/check-ksg-harmonic-revision-self-test.py  # 175 route mutations
python3 -O scripts/check-ksg-harmonic-revision-self-test.py
python3 scripts/check-ksg-phase-isolation.py             # exact KSG-only Git phase envelope
python3 -O scripts/check-ksg-phase-isolation.py
# `candidate-tree=not-requested` is diagnostic only. M1a closure requires an independently
# recorded alternate-index tree/checkpoint; a post-hoc tree cannot close checker self-reference.
# On a committed candidate/CI checkout, both invocations require:
#   --expected-candidate-tree "$(git rev-parse 'HEAD^{tree}')" --checkpoint-commit "$(git rev-parse HEAD)"
python3 scripts/check-ksg-phase-isolation-self-test.py
python3 -O scripts/check-ksg-phase-isolation-self-test.py
just ksg-witnesses                                      # exact W1/W2/W2b summaries in debug/release
# Each command below must execute exactly 12 tests, never a feature-gated zero-test false green.
cargo test --locked -p pid-core --no-default-features --features experimental-pipelines --test parallel_bit_identity
cargo test --locked --release -p pid-core --no-default-features --features experimental-pipelines --test parallel_bit_identity
cargo test --locked -p pid-core --no-default-features --features experimental-pipelines,parallel --test parallel_bit_identity
cargo test --locked --release -p pid-core --no-default-features --features experimental-pipelines,parallel --test parallel_bit_identity
python3 scripts/check-citation-edge-countermodel.py      # exact C2 adjacent-arrow negative control
python3 scripts/check-citation-edge-countermodel-self-test.py
python3 scripts/check-lean-citation-edge-countermodel.py # same witness via pinned Lean/Mathlib
python3 scripts/check-lean-citation-edge-countermodel-self-test.py
python3 scripts/check-release-scope.py                   # scope/signature-registry coherence
scripts/check-release-scope-self-test.sh                 # fail-closed scope/history mutations
scripts/check-public-api-snapshots.sh                    # rebuild immutable declaration evidence
scripts/check-release-state.sh candidate                  # pre-tag public-metadata truth
```

For KSG revision 4, keep evidence inventories failure-diverse and numerically separate. The
compiled Rust corpus test directly classifies all 8,198 selected helper outputs as
`+0/-0/nonzero = 354/0/7844`. The exact-enclosure inventory is 29 scientific/custody mutations
plus two exact-`Fraction(Decimal)` comparator controls; the modular inventory is 28
scientific/custody mutations plus two strict JSON shape/type/value controls; and the Z3 inventory is
12 semantic countermodels plus 52 bounded parser/profile/type/snapshot/transport/result controls
(`16/25/11`). Do not sum controls into theorem or semantic-mutation counts.

The Z3 raw and token-stream pins are correlated custody views of the same proof bytes. A retained
well-typed wrong-theorem dual rebase remains a human/Git/receipt cut. The odd-prime modular lanes
share `H_(p-1-t) = H_t (mod p)`; the rejected-prime collisions are one reflected event, and the
selected fields are not independent proofs. The `1000001=101*9901` control reaches the
deterministic u32 Miller--Rabin loop after bypassing the `2..37` small-prime prefilter, but that is
path coverage only.

Treat `x+y <= n+k` only as a conditional eligible-row set lemma under the finite-positive-radius,
unique-shell, exact-count, common-row-set, and inventoried-map premises. Neither it nor the stronger
balanced lower bound is a promoted revision-4 theorem. Implementation-local purity of a row helper
does not imply statistically independent observations.

The 13-gate repository/publication disposition remains **NO-GO** throughout M1a. Commit, push, and
remotely verify the canonical unsigned M1a implementation first. Only a separate descendant M1c
may bind immutable `evidence-matrix-v4.md` and `decision-v4.md`; never use preclosure evidence to
grant final authority early. Preserve the negative paths and checker repairs in the revision-4
correction ledger and failure memos. Advisory external-model material is process evidence, never
claim evidence.

These commands track CI's core gates but are not byte-identical to `.github/workflows/ci.yml`.
CI also sets `RUSTFLAGS=-D warnings`, checks every individual feature on Ubuntu and default/all
features on macOS and Windows, verifies MSRV 1.89, runs deterministic property and fuzz corpora,
enforces coverage, reviews package/semver/unused-dependency state, generates an SBOM, scans history
for secrets, and builds/installs the Python wheel across its minimum/current matrix. `just ci`
covers the practical local subset; `just release-audit` lists the heavier release-candidate gates.

The example is the quickest "is the core working" check. Expected output (deterministic — the example
seeds its own RNG):

```text
Mutual information (nats):
  I(S1; T)     = 0.4209
  I(S2; T)     = 0.3798

2-source PID atoms (I^sx_∩), nats:
  Redundancy   = 0.1662
  Unique(S1)   = 0.2547
  Unique(S2)   = 0.2137
  Synergy      = 1.2350
  (sum of atoms = 1.8695 = I(S1,S2; T))
```

`pid-python` is a PyO3 extension module, so exclude it from the plain workspace `cargo test`: that
path can depend on a host `libpython` and has no binding coverage. The upgraded PyO3/NumPy wrapper
does participate in the workspace rustdoc gate. Exercise its actual Python API via maturin:

```bash
pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

## Conventions to preserve

- **Units:** all information quantities are in **nats** (natural log).
- **PID identities:** MI terms that feed PID atoms must be computed with `NegativeHandling::Allow` —
  clamping a term before a subtraction breaks `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`.
- **Negative atoms are real:** `I^sx_∩` (and its atoms) can be negative; never silently clamp.
- **Continuous support is declared, never inferred:** bare default continuous configs are
  intentionally non-runnable. Use the explicit absolute-continuity constructor only when every
  marginal and joint law required by that call has the stated full-dimensional population model.
  Exact ties are incompatible with ideal i.i.d., unrounded continuous-sample conditions but do not
  identify their cause or population support; all-unique samples cannot prove the model. Atomic,
  quantized, mixed, singular, or unknown support must be routed to a matching estimand.
- **Added noise changes the estimand:** never recommend it as a generic tie repair. Use the typed
  `GaussianNoiseTransform` only for an explicit observation-noise model or a seeded, reported
  noise-scale sensitivity analysis. The ideal Gaussian model gives smooth full support when its
  declaration is true. It does not prove finite MI, i.i.d. rows, estimator validity, or PID-atom
  monotonicity. Separate matrix reports do not establish a joint source-and-target noise model.
  `Jitter` is an unreported migration primitive.
- **Determinism:** accumulate over count maps with `BTreeMap`/sorted keys (not `HashMap`); the
  `parallel` feature must stay bit-identical to the serial path; seed all RNGs explicitly.
- **Software identity separates domains:** public Rust declaration-signature revision, source
  route, selected build context, forensic reference hashes, and attestation status are not
  interchangeable.
  Hash exact raw artifact bytes and retain declaration snapshots under immutable revision-scoped
  paths. Append preservation covers every HEAD-reachable registry-touch commit and direct tip
  parent; after a committed binding, exact snapshot bytes are checked through each path's reachable
  full history. The checker strips ambient Git routing/configuration, disables replacement/graft
  overlays, and binds Git's canonical worktree root. It cannot cover absent history and is not a
  transparency log.
  Never present identity equality as compatibility, authenticity, scientific/application validity,
  source/archive/binary equality, or cross-platform numerical identity. Format 1 attestation
  remains explicitly `none`.
  Preserve the build-time Git isolation and invalidation contract: do not re-enable ambient
  routing, replacement/graft, ref-backend, config, pathspec, or global/system attribute inputs; do
  not recursively watch the complete `.git` or object database (the bounded `objects/info`
  metadata watch is intentional); and keep unsupported or incomplete final source probes on an
  absent recovery watch. Preserve unchanged generated identity bytes across build-script reruns.
  Git older than 2.45 must not claim workspace cleanliness. Clean/dirty assumes repository metadata
  and package files remain stable during the bounded probe; retain the repeated input/status and
  final-HEAD checks, but do not describe them as an atomic snapshot.
  Any effective `filter` attribute on a tracked package path (including unset or unconfigured
  values), `attr.tree`, tracked symbolic links, and tracked gitlinks must remain `unknown`, without
  executing a clean-filter command under that stability assumption. This is a captured build
  snapshot, not a live Git-tool or object-store monitor.
- **`exp0` is a diagnostic gate, not a pass/fail test.** Its default sweep reports a scoped
  `GO`/`NO-GO` high-dimensional MI/coherence verdict and a separate, non-gating `GO`/`PIVOT`
  geometry disposition, and **exits 0 by default**. The sweep goes to dimension 256 at n=500,
  deliberately entering regimes where kNN MI is known to break down, so `NO-GO` MI/coherence or
  `PIVOT` geometry findings are expected, informative outcomes. Optional diagnostics use explicit
  produced/abstained/not-requested states rather than numeric sentinels. Shared-exclusions
  atom-measure validation is separately `not_adjudicated`, and atom-estimator validation is
  `blocked`; neither is inferred from the MI/coherence verdict.
  - `--strict-gate` does **not** enforce a verdict on the default high-d sweep (that would
    contradict the contract above). It enforces `GO` (exit code 3 otherwise) only on a **curated
    band** where `GO` is legitimately expected and is checked against an **analytic closed form**:
    a small grid of jointly-Gaussian systems at `d=1`, `n=4000` (an analytically checked,
    low-dimensional KSG regime), where the
    three measure-independent MI terms `I(S1;T)`, `I(S2;T)`, `I(S1,S2;T)` must match their
    Cover–Thomas Gaussian values within the scale-aware tolerance. `--strict-gate` implies
    `--strict-band` (which runs the band and reports it without enforcing). The four synthetic
    scenarios are still run at `d ∈ {2,4,8}` as a **non-gating** diagnostic alongside the band; they
    are a known non-`GO` regime because KSG underestimates the joint MI under strong dependence.
    `independent_additive` has positive shared-exclusions redundancy in the declared fixed-sample,
    fixed-gauge comparison in `tests/sxpid_gaussian_oracle.rs`; `exp0` reports it but never
    compares it with a zero target or folds it into a verdict. These are reported findings, not
    regressions, and must **not** be "fixed" by loosening the gate's tolerances.
- **Scientific changes:** a change that alters a numerical result must justify *why* the new value is
  correct (analytic ground truth or a cited paper), not merely that tests still pass.

## README-iff invariant (where READMEs may live, and how they wire in)

A directory gets a `README.md` **if and only if** it is one of:

- a **published artifact** (a crate published to crates.io, or a package published to PyPI), or
- a **directly-consumed unit** (something a human runs/imports on its own — a CLI, an example, a
  vendored tool), or
- a **browsed-asset directory** (a folder a reader lands in and expects orientation — currently
  only the repo root; `crates/` deliberately has none, since each crate README is one click away
  and the root README carries the workspace map).

No other directory should grow a stray `README.md`. If a folder is neither published, nor directly
consumed, nor browsed, it does not get one.

Wiring rules for the READMEs that do exist:

- **Rust library crates** (`pid-core`, `pid-runlog`): the crate README is the canonical crate-level
  doc and is wired into rustdoc via `#![doc = include_str!("../README.md")]` at the top of
  `src/lib.rs`. Because `include_str!` makes every ` ```rust ` and every **bare** ` ``` ` fence in
  the README a compiled-and-run doctest, audit the fences before wiring and re-fence:
  - prose / shell / commands / TOML / program output → ` ```text ` (never executed),
  - complete Rust that compiles but must not run → ` ```no_run `,
  - illustrative / incomplete / pseudocode Rust that won't compile (e.g. undefined vars like
    `s1_data` / `n`) → ` ```rust,ignore `.
  The bar is: `cargo test --doc -p <crate>` and
  `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps -p <crate>` both pass clean. Each such crate's
  `Cargo.toml` also carries `readme = "README.md"`, `documentation = "https://docs.rs/<crate>"`, and
  a `[package.metadata.docs.rs]` block (`all-features = true`, `rustdoc-args = ["--cfg", "docsrs"]`).
- **maturin / PyO3 extension crates** (`pid-python`): wire the README with the `readme = "README.md"`
  manifest key **only** — do **not** add `#![doc = include_str!(...)]`. Their rustdoc is not the
  primary documentation surface, and a standalone README plus `readme=` avoids any risk to the
  maturin/`abi3` build.

## Before you push

Run the build/test/lint block above (all must be clean), update `CHANGELOG.md` under
`[Unreleased]`, and keep PRs focused. For security issues, follow `SECURITY.md` (do not open a
public issue). See `CONTRIBUTING.md` for the full contributor guide.
