# Reproducing the four-row copy-law result

Sepehr Mahmoudian · 18 November 2026. This directory contains the recorded bytes for one finite bootstrap coverage calculation, its portable verifier, and the exact Rust driver source and dependency lock used in the release build. The study explains why the population target is entropy, why the sixteen ordered samples have unequal weights, and what the observed 64/81 covers. [Study](../../../FINITE_COPY_BOOTSTRAP_COVERAGE.md) · [PDF](../../../output/pdf/finite-copy-bootstrap-coverage.pdf)

## Check the recorded result

From the repository root, run the standard-library checker in either Python mode. Python 3.15.0 was used for the recorded checks.

```sh
python3 -I -B audit/evidence/finite-copy-bootstrap-coverage/verify.py
python3 -I -B -O audit/evidence/finite-copy-bootstrap-coverage/verify.py
```

The checker hashes the retained files, reconstructs the complete Seed 7 index schedule, rechecks each original binary64 point, replicate and percentile endpoint against rational entropy enclosures, and checks the signed-net coverage decision on every ordered sample. Its additional mask table uses the count of balanced resamples. The covered probability is 64/81, noncoverage is 17/81 and typed API failure mass is 0/81. Statistical misses and runtime errors remain distinct.

| File | Role |
|---|---|
| [observation.json](observation.json) | Exact 161,944 stdout bytes. All 3,200 categorical replicates and the 200 index-probe values are kept in their original order with hexadecimal binary64 fields. |
| [judgment.json](judgment.json) | Exact original numerical judgment on that stream. Normal and optimized Python produced the same bytes. The historical field `constant_sample_failure_mass` means statistical noncoverage on the two constant samples. |
| [record.json](record.json) | Public source, package, executable and raw identities, compiler/target, measured stage times and limits of the execution evidence. The process-group RSS field is a periodically sampled readback. It can miss the actual peak. |
| [Rust driver](driver/candidate/main.rs) | Original Cargo.toml, Cargo.lock and candidate/main.rs. The manifest deliberately resolves pid-core from a sibling checkout named source. |
| [Numerical checker](judge/observation.py) | Original finite arithmetic, status handling, and index-only V1 comparator. The files are retained unchanged so their identities can be compared. The original capture controller recorded the program execution. The portable verifier checks its published observation and numerical judgment. |

The raw observation SHA-256 is `6c34d13dc27a96400f2b4e154647e006b6d08398c5b7a49655ae0dd95fc0d8e6`. The exact Rust source SHA-256 is `bdce8611095ae2129c6cfce221b7f36df48d429209f2d3a3e7b296651b12e191`. A file digest establishes byte identity given a trusted release or commit.

## Rebuild the measured driver

The study measured pid-rs commit `1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20`, tree `e91f4dfd9715ce1a2210536442c0811ac0422171`. This source predates the report. Using the newer publication checkout as the runtime changes the study's software identity. The driver lock has 41 registry packages and two local packages. [Pinned runtime](https://github.com/sepahead/pid-rs/tree/1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20) · [Bootstrap schedule and ranks](https://github.com/sepahead/pid-rs/blob/1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20/crates/pid-core/src/bootstrap.rs) · [Categorical estimator](https://github.com/sepahead/pid-rs/blob/1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20/crates/pid-core/src/sxpid.rs)

Run these commands from a publication checkout containing the measured commit's Git object. The first Cargo command populates a missing registry cache. The release build itself runs offline.

```sh
project=$(git rev-parse --show-toplevel)
evidence="$project/audit/evidence/finite-copy-bootstrap-coverage"
replay=$(mktemp -d)
git clone --quiet --no-checkout "$project" "$replay/source"
git -C "$replay/source" checkout --quiet --detach 1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20
cp -R "$evidence/driver" "$replay/driver"
cargo fetch --locked --manifest-path "$replay/driver/Cargo.toml"
CARGO_TARGET_DIR="$replay/target" cargo build --locked --offline --release -j1 \
  --manifest-path "$replay/driver/Cargo.toml"
"$replay/target/release/pid-copy-bootstrap-calibration" > "$replay/observation.json"
python3 -I -B "$evidence/verify.py" --observation "$replay/observation.json"
```

The last command checks for byte identity with the recorded observation. Keep a differing stream with its compiler, target, flags and build provenance for investigation. Cross-platform bit identity and universal coverage remain open. The original test of the fixed numerical predicate admitted one wrapper and executed it once. Reading a saved observation or rebuilding the wrapper supplies a separate reproduction check.

## Rebuild the report

The Markdown is the single content source for the report body. The PDF build uses Pandoc, LuaLaTeX and the repository-local publication styles. Its fixed timestamp is the report date.

```sh
python3 -I -B scripts/build-finite-copy-bootstrap-pdf.py
python3 -I -B scripts/build-finite-copy-bootstrap-pdf.py --check
```

Cite Sepehr Mahmoudian (2026), *Coverage of a bootstrap percentile range on a four-row copy law*, with the exact report commit or release. Cite the paper for the categorical redundancy definition and the project for the software. [MGW defining paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Software citation](../../../CITATION.cff)
