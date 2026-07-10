<h1 align="center">pid-rs</h1>

<p align="center">
  <strong>The Wibral-group shared-exclusions Partial Information Decomposition — and the continuous mutual-information estimators under it — in safe, reproducible Rust.</strong>
</p>

<p align="center">
  <a href="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml"><img src="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg" alt="License: MIT OR Apache-2.0"></a>
  <img src="https://img.shields.io/badge/rustc-1.80%2B-orange.svg" alt="MSRV 1.80">
  <img src="https://img.shields.io/badge/pid--core-unsafe%20forbidden-success.svg" alt="pid-core: unsafe forbidden">
</p>

---

**pid-rs** implements the **shared-exclusions partial information decomposition** (`I^sx_∩`;
Makkeh–Gutknecht–Wibral 2021) with **one measure across both regimes**: the exact discrete
SxPID (pointwise, signed atoms) and the continuous `I^sx_∩` kNN estimator (Ehrlich et al.
2024), on top of KSG mutual information (Kraskov et al. 2004). Around the estimator core sit
the layers a defensible analysis needs: Shannon-invariant screening, discrete `I_min` PID for
cross-measure comparison, geometry diagnostics that tell you whether the kNN regime is even
valid, dependence-aware uncertainty quantification (moving-block bootstrap; exchangeable *and*
dependence-preserving permutation nulls; Benjamini–Hochberg FDR), and content-addressed
run-logs so every number is replayable.

It was built to diagnose how information from different sources (e.g. **vision** and
**language**) is integrated in multimodal policies, and now also powers cross-sensor
consistency monitoring in a sibling project — but every estimator here is **domain-agnostic**:
give it samples of sources `S1, S2, …` and a target `T` and it estimates how much of the
information about `T` is **redundant**, **unique**, or **synergistic**.

```text
                I(S1,S2; T)
              ┌──────┴───────┐
   Redundancy ·  Unique(S1) ·  Unique(S2) ·  Synergy
```

## Highlights

- **KSG mutual information** for continuous variables — L∞ joint metric, strict-radius marginal
  counting, digamma reference table.
- **Continuous `I^sx_∩`** (shared-exclusions redundancy) via the Ehrlich et al. 2024
  disjunction-neighbourhood kNN estimator — *not* a min-of-pointwise heuristic.
- **2- and 3-source PID atoms** whose Möbius identities (`Red + Unq₁ + Unq₂ + Syn = I(S1,S2;T)`)
  **hold by construction** and are asserted in tests.
- **Discrete shared-exclusions PID `i^sx_∩`** (Makkeh–Gutknecht–Wibral 2021) — pointwise *and*
  averaged signed atoms with informative/misinformative split, **bit-faithful to the reference
  IDTxl wraps** (Abzinger/SxPID) for 2- and 3-source, plus a general `discrete_sxpid_n` for
  2–4 sources (the 166-antichain 4-source lattice). The discrete counterpart of the continuous
  `I^sx_∩`, so the library decomposes information with one measure across regimes.
- **Discrete `I_min` PID** over the full 18-antichain 3-source lattice (Williams & Beer 2010),
  for cross-measure comparison — never pool its atoms with `I^sx_∩` atoms.
- **Shannon invariants** — co-information, O-information (Rosas et al. 2019), and the average
  degrees of redundancy (`r̄`) and vulnerability (`v̄`) (Gutknecht et al. 2025) — as cheap
  screening statistics.
- **Geometry diagnostics** — intrinsic dimension (Levina–Bickel), distance concentration, Gromov
  hyperbolicity — to decide whether a continuous-kNN regime is even valid.
- **Preprocessing** — standardisation, PCA, hash (CountSketch) projection, seeded jitter, and PLS.
- **Honest uncertainty** — a moving-block bootstrap that respects sample dependence, and
  permutation tests with an explicit null **scheme**: `FullShuffle` for exchangeable (i.i.d.)
  rows, or `CircularShift` rotations that preserve a trajectory's own autocorrelation while
  breaking cross-alignment — plus **Benjamini–Hochberg FDR** (`benjamini_hochberg`) for the
  many-atoms × sources × windows testing PID invites.
- **Reproducible by construction** — content-addressed run-logs ([`pid-runlog`](crates/pid-runlog);
  SHA-256 payload digests on action/intervention/bridge records + a whole-trace replay hash and
  whole-file manifest covering every record), seeded RNG, and
  an optional `parallel` feature whose results are **bit-identical** to the serial path.
- The estimator core (`pid-core`) is `#![forbid(unsafe_code)]`, returns errors rather than
  `panic!`-ing on valid-but-degenerate input, and keeps a dependency-light tree. (`pid-runlog`
  is also unsafe-free; `pid-python` necessarily uses PyO3's `unsafe` internals.)

## How pid-rs compares

A high-level orientation for readers who already know the established toolboxes (not a feature-parity
scorecard — each tool leads in its own niche):

| | **pid-rs** | [IDTxl](https://github.com/pwollstadt/IDTxl) | [dit](https://github.com/dit/dit) | [JIDT](https://github.com/jlizier/jidt) |
|---|:---:|:---:|:---:|:---:|
| Language | Rust (+ Python) | Python | Python | Java (+ wrappers) |
| KSG continuous MI | ✅ | ✅ | — *(discrete-only)* | ✅ |
| **Continuous `I^sx_∩`** (Ehrlich 2024) | ✅ | — | — | — |
| **Discrete SxPID `i^sx_∩`** | ✅ *(bit-faithful to IDTxl)* | ✅ *(reference impl.)* | ✅ *(shared-exclusions measure)* | — |
| Discrete `I_min` PID | ✅ | — *(BROJA + SxPID only)* | ✅ | — |
| Broad discrete PID/measure zoo | — | some | ✅ | — |
| Transfer entropy / network inference | — | ✅ | — | ✅ |
| Content-addressed, replayable run-logs | ✅ | — | — | — |
| Memory-safe, `unsafe`-free core | ✅ | n/a | n/a | n/a |
| Bit-identical serial↔parallel results | ✅ | — | — | — |

**Where the others lead:** IDTxl for transfer entropy, full network inference, and its mature
ecosystem (and it is the reference SxPID implementation this crate is validated against); dit for the
sheer breadth of discrete information/PID measures; JIDT for its established JVM estimator suite.
**pid-rs's niche** is a fast, memory-safe, *reproducible* implementation of the Wibral-group
shared-exclusions PID unified across the continuous and discrete regimes.

## Project status

`pid-rs` is at `0.4.0`, plus unreleased additions tracked in the
[CHANGELOG](CHANGELOG.md). The estimator **core** is validated against analytic ground truth
(see [Validation](#validation)); the surrounding statistics, performance, and tooling layers are
usable but have tracked follow-ups. This section is a quick honest map of where things stand — it
does not repeat the per-claim detail in [Conventions](#conventions),
[Scientific cautions](#-scientific-cautions-read-before-trusting-results), or
[Known limitations](#known-limitations).

### What works today

| Capability | Notes |
|---|---|
| **KSG mutual information** | Continuous variables, L∞ joint metric, strict-radius marginal counting; checked vs the closed-form Gaussian-channel MI. |
| **Continuous `I^sx_∩`** | Ehrlich et al. 2024 disjunction-neighbourhood kNN redundancy (`IsxMethod::EhrlichKsg`); checked against a closed-form additive-Gaussian oracle (`tests/sxpid_gaussian_oracle.rs`) and pinned by frozen fixed-data regression values. |
| **2- & 3-source PID atoms** | `pid2_isx` / `pid3_isx`; Möbius identities (`Red + Unq₁ + Unq₂ + Syn = I(S1,S2;T)`) hold by construction and are asserted in tests within `1e-10`. |
| **Discrete SxPID `i^sx_∩`** | `discrete_sxpid2` / `discrete_sxpid3` + general `discrete_sxpid_n` (2–4 sources; Makkeh–Gutknecht–Wibral 2021); pointwise + averaged signed atoms with informative/misinformative split, **bit-faithful** to the Abzinger/SxPID + IDTxl reference values to `1e-12`; MGW Theorem IV.2/IV.3 axiom tests. |
| **Discrete `I_min` PID** | `discrete_pid2` / `discrete_pid3` over the full 18-antichain 3-source lattice (Williams & Beer 2010), with equal-width quantisation. |
| **Shannon invariants** | Co-information, O-information (Rosas et al. 2019), and `r̄`/`v̄` (Gutknecht et al. 2025) as cheap screening statistics. |
| **Geometry diagnostics** | Intrinsic dimension (Levina–Bickel), distance concentration, Gromov hyperbolicity — to decide whether a continuous-kNN regime is even valid. |
| **Preprocessing / PLS** | Standardisation, PCA, hash (CountSketch) projection, seeded jitter, and supervised PLS with CV component selection. |
| **Uncertainty quantification** | Moving-block bootstrap; permutation tests with an explicit `PermutationScheme` (`FullShuffle` for i.i.d. rows, `CircularShift` for autocorrelated trajectories); `benjamini_hochberg` FDR adjustment for atom-level multiple testing. |
| **Run-logs** | `pid-runlog`: versioned, content-addressed JSONL schema (SHA-256 payload hashes on action/intervention/bridge records; every record covered by the whole-trace replay hash + whole-file manifest) and replay/validate/compare/sidecar CLIs. |
| **Python bindings** | `pid_core_rs` (PyO3 + maturin, `abi3` ≥ CPython 3.11) — 18 functions over C-contiguous `float64` NumPy arrays. Bindings shipped in `0.2.0`; discrete SxPID exports added in `0.3.0`. |
| **Reproducibility** | Seeded RNG; the optional `parallel` feature is **bit-identical** to the serial path; `#![forbid(unsafe_code)]`; errors (not panics) on degenerate input. |

### What needs further work

- **kNN is `O(n log n)` only on the standard configuration.** The KSG/`i^sx` hot loops use an
  exact Chebyshev kd-tree (bit-identical to the brute scan, enforced by parity tests) when
  `metric = Chebyshev`, `n ≥ 128`, and joint dimensionality ≤ 16 — ~19× at `n = 4000` on 1-D
  pairs. Outside that envelope (hyperbolic metric, high-dimensional joints where axis-aligned
  pruning degenerates, tiny `n`) the brute `O(n²)` scan still runs; the standalone
  `kth_neighbor_distance_*` / `count_neighbors_within` helpers remain brute-force.
- **`runlog --validate` is per-record, not whole-trace integrity.** It checks per-event invariants
  (payload/config-hash matches, monotone timestamps/steps, single `run_started`/`run_ended`, bridge
  causality, finite values). Whole-trace integrity is a separate path: the order-sensitive
  `replay_trace_hash` (`--compare`) and `--verify-sidecars`.
- **`exp0` is a diagnostic gate, not a pass/fail build step.** It emits a GO/PIVOT/NO-GO verdict
  from monotonicity / invariant / geometry counters and **exits 0 by default** (its default sweep
  deliberately enters regimes where kNN MI is known to break down). `--strict-gate` does **not**
  gate that default sweep; it enforces `GO` (exit 3 otherwise) only on a curated, analytically
  grounded low-dimension band (see the `exp0` section below).
- **No crates.io release yet.** Depend on the Git repository (pinned — see [Install](#install));
  the Python crate is `publish = false` by design (shipped as a wheel via maturin). The
  `pid-core` name is unclaimed on crates.io as of July 2026.
- **External cross-validation of the continuous `I^sx_∩` pending.** The discrete SxPID is
  validated bit-faithfully against IDTxl/Abzinger reference values, and the continuous estimator
  against a closed-form Gaussian oracle — but no *reproducible* external `csxpid` cross-check
  exists yet: the fixed-data constants in `tests/isx.rs` / `tests/pid3.rs` are frozen regression
  pins of this implementation (their historical csxpid attribution left no dataset or invocation
  artifacts, so they must not be read as external validation).

### Caveats

- **kNN failure modes are real.** Estimators assume **i.i.d.** samples (trajectory autocorrelation
  biases them — subsample or block-bootstrap); high ambient/intrinsic dimension causes **distance
  concentration** that degrades kNN geometry; and **strong (near-deterministic) dependence** can
  require prohibitive sample sizes (Gao et al. 2015). Run the geometry diagnostics and the `exp0`
  gate before interpreting results.
- **Negative atoms are real, not bugs.** `I^sx_∩` trades all-atom non-negativity for the target
  chain rule, so atoms (including redundancy) can be negative; atoms and the MI terms feeding
  them are never clamped (`Allow` is forced inside `pid2_isx`/`pid3_isx`/co-information). Note
  the standalone `ksg_mi` defaults to `ClampToZero` as a reporting convenience — set
  `NegativeHandling::Allow` when you need raw (possibly negative) MI estimates.
- **Match the permutation null to your data.** `FullShuffle` simulates exchangeable rows; on
  autocorrelated trajectories it is anti-conservative — use
  `PermutationScheme::CircularShift { min_shift }` with `min_shift` at least the dependence
  length (the same order as your bootstrap block size), and mind its p-value resolution bound
  (`n − 2·min_shift + 1` distinct offsets).
- **Cross-estimator PID2 mixing.** In `pid2_isx`, `Unq`/`Syn` combine KSG MI with Ehrlich `I^sx`
  redundancy (different bias profiles), so small near-zero atoms can be an estimator artefact rather
  than structure. Likewise, do not pool continuous `I^sx_∩` atoms with discrete `I_min` atoms — they
  are different PID measures.

## Install

> **Access note:** this repository is currently **private**; the Git dependency and the CI badge
> require read access. A public crates.io release is planned (the `pid-core` name is reserved-free
> as of July 2026); until then, pin the Git tag:

```toml
[dependencies]
pid-core = { git = "https://github.com/sepahead/pid-rs", tag = "v0.4.0" }
```

> Pinning a tag keeps builds reproducible — an unpinned Git dependency floats with the default
> branch, which is at odds with everything else this crate promises about reproducibility.
>
> Using Python? See the [Python bindings](#python) below for `pip install maturin` and `maturin develop`.

## Quickstart

```rust
use pid_core::{ksg_mi, pid2_isx, IsxConfig, KsgConfig, MatRef, NegativeHandling, Pid2Config};

fn main() -> Result<(), pid_core::PidError> {
    // Columns are dimensions, rows are samples. Toy system: T depends on both
    // scalar sources (swap in your own `&[f64]` buffers; real analyses want far
    // more than 8 samples — see examples/ksg_and_pid.rs for a full run).
    let s1_data = [0.0, 1.0, 0.0, 1.0, 0.2, 0.8, 0.1, 0.9];
    let s2_data = [0.0, 0.0, 1.0, 1.0, 0.1, 0.9, 0.8, 0.2];
    let t_data: Vec<f64> = s1_data.iter().zip(&s2_data).map(|(a, b)| a + b).collect();
    let s1 = MatRef::new(&s1_data, 8, 1)?;
    let s2 = MatRef::new(&s2_data, 8, 1)?;
    let t = MatRef::new(&t_data, 8, 1)?;

    // Mutual information (nats).
    let ksg = KsgConfig { negative_handling: NegativeHandling::Allow, ..Default::default() };
    let mi = ksg_mi(s1, t, &ksg)?;

    // 2-source PID atoms via I^sx_∩.
    let pid = pid2_isx(s1, s2, t, &Pid2Config { ksg, isx: IsxConfig::default() })?;
    println!("MI={mi:.3}  Red={:.3}  Unq1={:.3}  Unq2={:.3}  Syn={:.3}",
             pid.redundancy, pid.unique_s1, pid.unique_s2, pid.synergy);
    Ok(())
}
```

Run the worked examples end-to-end:

```bash
cargo run --release --example ksg_and_pid       # continuous KSG MI + I^sx_∩ PID
cargo run --release --example discrete_sxpid     # discrete shared-exclusions PID on logic gates
```

A [Criterion](https://github.com/bheisler/criterion.rs) benchmark suite tracks the cost of the
kNN backend (kd-tree on the standard Chebyshev configuration, brute-force elsewhere) and the
discrete SxPID lattice across sample sizes (KSG MI, continuous `I^sx_∩`, 2-source PID, discrete
SxPID):

```bash
cargo bench -p pid-core
```

(Common dev tasks are also codified as [`just`](https://github.com/casey/just) recipes — run `just`
to list them.)

## Conventions

- **Units:** all information quantities are in **nats** (natural log).
- **Co-information sign:** for 2 sources `CI₂ = Red − Syn`, so *negative ⇒ synergy-dominant*. This
  **does not** carry over to 3 sources — `CI₃` is parity-flipped (a pure 3-way synergy gives
  `CI₃ > 0`) and conflates atoms, so it is only a coarse screen.
- **Negative atoms are real:** `I^sx_∩` trades all-atom non-negativity for the target chain rule, so
  atoms (including redundancy) can be negative. Atoms and the MI terms feeding them are never
  clamped (`NegativeHandling::Allow` is forced inside the PID/co-information paths); only the
  standalone `ksg_mi` defaults to `ClampToZero`, and that is a reporting choice you can override.
- **Permutation nulls are explicit:** `PermutationScheme::FullShuffle` assumes exchangeable rows;
  `PermutationScheme::CircularShift` preserves within-series autocorrelation. The legacy
  entry points (`permutation_pid3`, `permutation_rows_pvalue`) delegate to `FullShuffle` and are
  bit-identical to pre-scheme releases at the same seed.

## ⚠️ Scientific cautions (read before trusting results)

kNN information estimators are powerful but have well-known failure modes. **Validate before you
interpret.**

- **i.i.d. assumption** — trajectory/time-series autocorrelation biases kNN MI. Subsample or use the
  block bootstrap; for permutation nulls use `CircularShift`, not `FullShuffle`.
- **Distance concentration** — in high ambient/intrinsic dimension, kNN geometry degrades; check the
  geometry diagnostics first.
- **Strong dependence** — near-deterministic relationships (very large true MI) can need prohibitive
  sample sizes (Gao et al. 2015).
- **Many tests need correction** — atoms × sources × windows multiply; adjust the pooled p-values
  with `benjamini_hochberg` (or your own FWER control) before reporting discoveries.
- **Estimator ≠ truth** — do not interpret a downstream result without passing a validation gate on
  synthetic systems whose information quantities are known analytically.

The `exp0` binary is that diagnostic gate (synthetic systems with known MI, noise-dimension
invariance, strong-dependence sweeps). It sweeps dimensions up to 256 at n=500 — a range that
*deliberately* includes regimes where kNN MI is known to break down — so a `PIVOT`/`NO-GO` verdict on
the full default sweep is the expected, informative outcome, not a build failure. It reports
per-check counters (Monotonicity / Invariant / Geometry), and exits 0 by default.

`--strict-gate` is deliberately *not* allowed to gate that full sweep (a non-`GO` verdict there is
expected, not a failure). Instead it enforces `GO` — exiting with code 3 otherwise — on a **curated
band** where `GO` is legitimately expected and is checked against an **analytic closed form**: a
small grid of jointly-Gaussian systems at `d=1`, `n=4000` (the KSG estimator's validated regime),
where the three mutual-information terms `I(S1;T)`, `I(S2;T)`, `I(S1,S2;T)` must match their
Cover–Thomas Gaussian values within the scale-aware tolerance. `--strict-gate` implies
`--strict-band` (run + report the band without enforcing). The four synthetic scenarios are still
exercised at `d ∈ {2,4,8}` as a non-gating diagnostic alongside the band.

```bash
cargo run -p pid-core --bin exp0 -- --seeds 4 --summary-json summary.json --runlog run.jsonl
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate run.jsonl
```

## Validation

Correctness is checked against **analytically known ground truth**, not just self-consistency:

- KSG MI vs the closed-form Gaussian-channel MI `I = −½ ln(1 − ρ²)`.
- Continuous `I^sx_∩` against a **closed-form additive-Gaussian oracle** (the analytic continuous
  limit of the discrete `i^sx`; `tests/sxpid_gaussian_oracle.rs`), plus frozen fixed-data
  regression pins.
- Discrete SxPID **bit-faithfully** against the IDTxl/Abzinger reference values (to `1e-12`),
  including its axioms (MGW Theorems IV.2/IV.3 in `tests/sxpid_axioms.rs`).
- Discrete PID against the **independently re-derived** `I_min` and the known structure of canonical
  gates (XOR = pure synergy `ln 2`; a redundant copy `S1 = S2` = pure redundancy; AND's exact
  closed-form atoms; …).
- 2-/3-source PID identities (atoms reconstruct total MI) within `1e-10`.
- `parallel` feature results are **bit-identical** to the serial path; the legacy permutation
  entry points are **bit-identical** to their `_with(FullShuffle)` forms at the same seed.
- `benjamini_hochberg` against hand-computed step-up q-values, clamping/monotonicity, and NaN
  pass-through fixtures; `CircularShift` nulls verified to produce only bounded rotations.

See [`crates/pid-core/tests`](crates/pid-core/tests) for the suite.

## Known limitations

The estimator **core** (KSG, continuous `I^sx_∩`, discrete `I_min`, and
the PID identities) is validated against analytic ground truth, but the surrounding
statistics/convenience layer has tracked follow-ups (see the issue tracker):

- **Bootstrap caveats for kNN statistics.** The block bootstraps are true
  moving-block (Künsch) resamplers, but with-replacement resampling necessarily duplicates rows,
  which distorts kNN local-density statistics even with tie-breaking jitter — prefer
  `RowResampleScheme::Subsample` for KSG-based statistics.
- **Circular-shift nulls have finite resolution.** A `CircularShift` permutation null has at most
  `n − 2·min_shift + 1` distinct offsets, which bounds how small its p-values can meaningfully
  get (the add-one correction keeps them valid); and rotation surrogates assume stationarity.
- **Cross-estimator PID2 atoms.** `Unq`/`Syn` combine KSG MI with Ehrlich `I^sx` redundancy
  (different bias profiles); small near-zero atoms can be an estimator artefact rather than
  structure.
- **External cross-validation provenance.** The discrete SxPID is validated against the
  IDTxl/Abzinger reference values; the continuous `I^sx_∩` against a closed-form Gaussian oracle.
  A reproducible external `csxpid` cross-check of the continuous estimator (committed dataset +
  recorded invocation) is still pending; the fixed-data constants in `tests/isx.rs` /
  `tests/pid3.rs` are frozen regression pins, not external validation.

None of these affects a single point estimate of MI or a PID atom — they concern *uncertainty
quantification* and *convenience-API ergonomics*.

## Estimators &amp; references

| Component | Reference |
|---|---|
| KSG mutual information | Kraskov, Stögbauer &amp; Grassberger (2004), *Phys. Rev. E* **69**, 066138 |
| Shared-exclusions redundancy `i^sx_∩` (discrete `discrete_sxpid2/3`) | Makkeh, Gutknecht &amp; Wibral (2021), *Phys. Rev. E* **103**, 032149; reference impl. IDTxl / Abzinger/SxPID |
| Parthood / formal-logic foundation of PID | Gutknecht, Wibral &amp; Makkeh (2021), [arXiv:2008.09535](https://arxiv.org/abs/2008.09535) |
| Continuous `I^sx_∩` kNN estimator | Ehrlich, Schick-Poland, Makkeh, Lanfermann, Wollstadt &amp; Wibral (2024), [Phys. Rev. E 110, 014115](https://doi.org/10.1103/PhysRevE.110.014115) ([arXiv:2311.06373](https://arxiv.org/abs/2311.06373)) |
| `I_min` redundancy &amp; the PID lattice | Williams &amp; Beer (2010), [arXiv:1004.2515](https://arxiv.org/abs/1004.2515) |
| Shannon invariants (`r̄`, `v̄`) | Gutknecht, Rosas, Ehrlich, Makkeh, Mediano &amp; Wibral (2025), [arXiv:2504.15779](https://arxiv.org/abs/2504.15779) |
| O-information | Rosas, Mediano, Gastpar &amp; Jensen (2019), [Phys. Rev. E **100**, 032305](https://doi.org/10.1103/PhysRevE.100.032305) ([arXiv:1902.11239](https://arxiv.org/abs/1902.11239)) |
| PID non-negativity / chain-rule / invariance trilemma | Matthias, Makkeh, Wibral &amp; Gutknecht (2025), [arXiv:2512.16662](https://arxiv.org/abs/2512.16662) |
| kNN MI sample-complexity caveat | Gao, Ver Steeg &amp; Galstyan (2015), [arXiv:1411.2003](https://arxiv.org/abs/1411.2003) |
| FDR step-up adjustment | Benjamini &amp; Hochberg (1995), *J. R. Stat. Soc. B* **57**(1), 289–300 |
| Add-one Monte-Carlo p-values | Phipson &amp; Smyth (2010), *Stat. Appl. Genet. Mol. Biol.* **9**(1), Art. 39 |

## Workspace

| Crate | Description |
|---|---|
| [`pid-core`](crates/pid-core) | The estimators, PID atoms, invariants, geometry, preprocessing, and the `exp0` validation harness. |
| [`pid-runlog`](crates/pid-runlog) | Versioned, content-addressed run-log schema + replay/validation CLI for reproducible pipelines. |
| [`pid-python`](crates/pid-python) | Python bindings (PyO3 + maturin); the `pid_core_rs` module — 18 functions over NumPy arrays. |

### Python

The `pid_core_rs` bindings (added in `0.2.0`) are built as a
stable-ABI (`abi3`, CPython ≥ 3.11) wheel with maturin. Arrays are passed as **C-contiguous**
`float64` NumPy arrays (wrap transposed/`order='F'` arrays in `np.ascontiguousarray` first):

```bash
pip install maturin && maturin develop --release -m crates/pid-python/Cargo.toml
python -c "import numpy as np, pid_core_rs as p; print(p.compute_mi(np.random.randn(400,1), np.random.randn(400,1)))"
```

## Minimum supported Rust version

**1.80**. The MSRV is treated as a semver-relevant property and is exercised in CI.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). For anything security-sensitive, see [SECURITY.md](SECURITY.md).

## Citation

If you use pid-rs in academic work, please cite it via [`CITATION.cff`](CITATION.cff) (GitHub
renders a “Cite this repository” button for users with repository access) and cite the underlying
estimator papers above.

## License

Licensed under either of

- **MIT** license ([LICENSE-MIT](LICENSE-MIT)), or
- **Apache License, Version 2.0** ([LICENSE-APACHE](LICENSE-APACHE))

at your option. Unless you explicitly state otherwise, any contribution intentionally submitted for
inclusion in the work by you, as defined in the Apache-2.0 license, shall be dual licensed as above,
without any additional terms or conditions.

## Acknowledgements

The `I^sx_∩` measure and its continuous estimator are due to the Wibral group (Göttingen); this is
an independent, from-the-papers Rust implementation. Any errors are the maintainer's own.
