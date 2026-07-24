# Formal tool adoption audit

> **Record status:** Adoption decision record, dated 24 July 2026.
>
> **Evidence status:** No tool evaluated in this record has verified `pid-rs`. This record does not
> report a proof run, a model-checking result, a certified numerical result, or an independent
> certificate check. It selects bounded pilot work and states the conditions that must apply before
> a result can become repository evidence.

## 1. Purpose

This record evaluates five proposed assurance layers for `pid-rs`:

1. Verus;
2. Kani;
3. Aeneas with Charon;
4. MPFR through Rug; and
5. Rocq with the Interval package.

The audit uses primary project sources and release metadata. The cut-off date is 24 July 2026.
Upstream state can change after that date. A pilot must repeat the upstream release check before
installation.

The decision is:

1. Pilot a Rug and MPFR categorical reference backend first.
2. Pilot Kani on bounded categorical integer and lattice obligations.
3. Pilot Verus on the same small, pure categorical kernel.
4. Evaluate Rocq Interval after the executable interval format is stable.
5. Defer Aeneas production adoption. Permit one isolated translation experiment.

No one tool replaces Lean. The tools cover different failure classes. Evidence from one layer does
not imply evidence from another layer.

## 2. Scope and exclusions

This record covers tool fit, versions, licenses, toolchains, installation pins, reproducible
commands, trust boundaries, and permitted claim language.

This record does not:

- add a dependency;
- change CI;
- change a public API;
- change a method or estimator;
- change the method catalog;
- prove Rust-to-specification refinement;
- prove floating-point correctness;
- prove statistical calibration;
- prove a theorem about continuous PID;
- approve a license for distribution; or
- claim that the current local installation is a release environment.

License identifiers in this record come from upstream metadata. They are not legal advice. A
distribution review is mandatory before code that links to an LGPL or CeCILL-C component is
released.

## 3. Terms

**Upstream fact** means a fact in an official project repository, release page, manual, or package
record.

**Local fact** means an observation from the workstation on 24 July 2026.

**Trust boundary** means code, data, assumptions, or tools that a proof result does not verify. This
record also uses the common term **trusted computing base (TCB)**.

**Pilot** means a bounded evaluation. It does not mean that the tool is part of the build, CI, or
release process.

**Certified backend** means a new backend that returns an outward interval under a stated rounding
contract. It does not mean that an existing binary64 result is certified.

## 4. Current repository and local state

### 4.1 Repository pins

The repository currently declares:

| Item | Repository pin | Source |
|---|---:|---|
| Minimum supported Rust version | 1.89 | [`Cargo.toml`](Cargo.toml) |
| Lean | 4.32.0 | [`audit/formal/lean/lean-toolchain`](audit/formal/lean/lean-toolchain) |
| mathlib | `v4.32.0` | [`audit/formal/lean/lakefile.toml`](audit/formal/lean/lakefile.toml) |
| Z3 for the existing algebra checker | 4.16.0, 64 bit | [`scripts/check-z3-pid2-algebra.py`](scripts/check-z3-pid2-algebra.py) |

These pins do not apply automatically to a new verifier. Each verifier can have a different
compiler and solver pin.

### 4.2 Local observations

The following commands were run from the repository worktree on 24 July 2026:

```text
rustc --version
cargo --version
(cd audit/formal/lean && lake env lean --version)
z3 --version
pkg-config --modversion mpfr
pkg-config --modversion gmp
command -v <tool>
```

Observed versions:

| Local item | Observation |
|---|---|
| `rustc` | `rustc 1.96.0 (ac68faa20 2026-05-25)` |
| `cargo` | `cargo 1.96.0 (30a34c682 2026-05-25)` |
| Lean | `4.32.0`, `arm64-apple-darwin24.6.0`, commit `8c9756b28d64dab099da31a4c09229a9e6a2ef35` |
| Z3 | `4.16.0 - 64 bit` |
| MPFR found by `pkg-config` | `4.2.2` |
| GMP found by `pkg-config` | `6.3.0` |
| FLINT found by `pkg-config` | Not found |
| `rug` or `gmp-mpfr-sys` in `Cargo.lock` | Not present |

The following commands were not found:

- `verus`;
- `cargo-verus`;
- `kani`;
- `cargo-kani`;
- `charon`;
- `aeneas`;
- `opam`;
- `rocq`;
- `rocqchk`;
- `coqc`;
- `coqchk`; and
- `nix`.

This local list is an environment observation only. It is not an installation attestation.
Homebrew MPFR availability does not establish a Rust binding, directed-rounding wrapper, or
certificate path.

## 5. Decision matrix

| Layer | Decision | First permitted scope | Main reason | Main blocker |
|---|---|---|---|---|
| Rug with MPFR | Pilot 1 | Offline or optional categorical exact-count interval oracle | Directly controls log rounding and atom cancellation | Native C and FFI trust, wrapper review, and LGPL obligations |
| Kani | Pilot 2 | Bounded integer, mask, event, lattice, overflow, and rejection harnesses | Exhaustive bit-precise checks inside declared bounds | Bounds do not generalize; concurrency and transcendental accuracy are out of scope |
| Verus | Pilot 3 | Small pure categorical kernel with explicit contracts | Closest fit for unbounded functional contracts over Rust-like code | Verus uses Rust 1.96 while `pid-rs` supports Rust 1.89; unsupported code and assumptions expand the TCB |
| Rocq Interval | Conditional pilot 4 | Independent checks of fixed emitted interval inequalities | Small kernel checker and analytic interval tactics give a second proof route | Separate ecosystem; the certificate generator and runtime binding remain trusted |
| Aeneas and Charon | Defer; allow one isolated experiment | Translation of the same small pure kernel to Lean | Can connect accepted safe Rust to a theorem-prover model | No stable Aeneas release, Lean 4.31 mismatch, supported-subset limits, and handwritten external models |

The order is deliberate. The first pilot gives a numerical oracle that the other pilots can use.
Kani and Verus then target the same integer semantics with different proof models. Rocq must not
precede a stable certificate schema. Aeneas must not become a release dependency during this
evaluation.

## 6. Verus adoption record

### 6.1 Upstream pin and license

The selected non-prerelease cut is
[`release/0.2026.07.18.3a4d30b`](https://github.com/verus-lang/verus/releases/tag/release/0.2026.07.18.3a4d30b).
GitHub records its publication on 20 July 2026.

The release pins:

- Rust `1.96.0`;
- `vstd` package version `0.0.0-2026-07-12-0122`.

The Z3 fetch helper in the tagged source pins Z3 `4.12.5`.

The license is MIT.

Primary pin sources:

- [release toolchain](https://raw.githubusercontent.com/verus-lang/verus/release/0.2026.07.18.3a4d30b/rust-toolchain.toml);
- [`vstd` package metadata](https://raw.githubusercontent.com/verus-lang/verus/release/0.2026.07.18.3a4d30b/source/vstd/Cargo.toml);
- [upstream Z3 fetch helper](https://raw.githubusercontent.com/verus-lang/verus/release/0.2026.07.18.3a4d30b/.github/workflows/get-z3.sh); and
- [MIT license](https://raw.githubusercontent.com/verus-lang/verus/release/0.2026.07.18.3a4d30b/LICENSE).

The release page had assets for arm64 macOS, x86-64 macOS, x86-64 Linux, and x86-64 Windows at the
audit date. This asset list is not a general platform support theorem.

### 6.2 Pin and installation rule

Do not use a rolling prerelease tag. Do not mix `vstd`, the Verus executable, and solver files from
different releases.

For a pilot:

1. Select the platform asset from the immutable release page.
2. Compute and record SHA-256 for the downloaded asset.
3. Extract it into a version-specific directory.
4. Use the `cargo-verus` executable from that release.
5. Use the solver in the release bundle, or use the exact upstream solver pin.
6. Record `verus --version`, `cargo verus --version`, solver version, asset digest, host, and target.

The upstream Cargo integration uses:

```toml
[package.metadata.verus]
verify = true
```

The required full verification command is:

```text
cargo verus verify --workspace --locked
```

The corresponding Verus build command is:

```text
cargo verus build --release --locked
```

Verus also supports `--offline`. A release evidence job must use both a lockfile and an archived
dependency set before it claims offline reproducibility.

A focused verification run is a development aid. It is not a substitute for the full verification
command.

### 6.3 First proof obligations

The pilot can cover:

- sorted and run-length-encoded rows preserve the input multiset;
- all histogram counts sum to the row count;
- an event count equals the declared event predicate;
- a supported keyed row gives a nonzero event denominator;
- source-mask and antichain orders are canonical;
- a Möbius transform reconstructs its cumulative coordinates; and
- specialized two-source and three-source kernels equal the general kernel on their shared domain.

The pilot must not start with:

- logarithms;
- binary64 error;
- the complete report API;
- parallel code;
- cancellation plumbing;
- allocators;
- Python bindings; or
- continuous KSG and shared-exclusions estimators.

### 6.4 Trust boundary and blockers

Verus documents that it does not support all Rust code and libraries. The Verus verifier, Rust
compiler, LLVM, solver, and platform remain in the trust boundary.

The following Verus features add assumptions or trusted specifications:

- `assume`;
- `external_body`;
- `external_fn_specification`; and
- `external`.

The pilot must create an assumption inventory. A result with an unreviewed assumption is not
accepted. The evidence must state each assumption and why it is necessary.

Verus uses Rust 1.96. `pid-rs` supports Rust 1.89. A successful Verus run does not prove that the
erased program builds at the minimum supported Rust version. The normal Rust 1.89 build and test
gates must remain separate.

### 6.5 Required negative controls

At minimum:

- mutate one event union to an intersection and require a failed postcondition;
- mutate one source mask and require a failed equivalence proof;
- remove one Möbius predecessor and require failed reconstruction;
- add an unapproved assumption and require the assumption-policy gate to fail; and
- run the erased source under Rust 1.89 to detect toolchain drift.

### 6.6 Permitted claim

Use:

> Verus proved the stated contracts for the opted-in functions under the recorded assumptions and
> pinned Verus, solver, and toolchain. It did not verify rustc or LLVM, unchecked specifications or
> external bodies, callers outside those contracts, or floating-point transcendental correctness.

Do not use:

- "Verus verified `pid-rs`";
- "the Rust binary is formally verified"; or
- "the result proves numerical or statistical correctness."

## 7. Kani adoption record

### 7.1 Upstream pin and license

The selected stable release is
[`kani-0.67.0`](https://github.com/model-checking/kani/releases/tag/kani-0.67.0), published on
16 January 2026.

The release pins:

- Rust nightly `nightly-2025-11-21`; and
- CBMC `6.8.0`.

Kani is dual licensed under MIT or Apache-2.0.

Primary pin sources:

- [Kani Rust toolchain](https://raw.githubusercontent.com/model-checking/kani/kani-0.67.0/rust-toolchain.toml);
- [Kani dependency pins](https://raw.githubusercontent.com/model-checking/kani/kani-0.67.0/kani-dependencies);
- [MIT license](https://raw.githubusercontent.com/model-checking/kani/kani-0.67.0/LICENSE-MIT); and
- [Apache-2.0 license](https://raw.githubusercontent.com/model-checking/kani/kani-0.67.0/LICENSE-APACHE).

The official easy-install matrix lists x86-64 Linux with GNU libc, x86-64 macOS, and arm64 macOS.
The installer requires Rust through `rustup`; the installation guide states Rust 1.58 or newer.

### 7.2 Pin and installation rule

Use a version-specific `KANI_HOME`. Install the exact verifier release with its lockfile:

```text
export KANI_HOME=/absolute/tool-cache/kani/0.67.0
cargo install --locked kani-verifier --version 0.67.0
cargo kani setup
cargo kani --version
```

Archive or hash the resulting version-specific tool directory. Record:

- the `kani-verifier` crate checksum;
- `cargo kani --version`;
- Rust nightly;
- CBMC version;
- host and target;
- harness name;
- input bounds;
- unwind bound; and
- the unwinding assertion result.

Example invocation:

```text
cargo kani --harness <HARNESS_NAME> --unwind <BOUND>
```

### 7.3 First proof obligations

Use Kani for bounded checks of:

- no panic;
- no out-of-bounds index;
- no checked integer overflow;
- resource-estimate arithmetic;
- canonical mask and lattice indexing;
- malformed-shape rejection;
- cancellation return paths;
- specialized and general categorical-kernel equivalence; and
- exact reconstruction identities for bounded tables.

Each harness must declare all shape and count bounds. A harness must retain an unwinding assertion.

### 7.4 Trust boundary and blockers

Kani proves a harness only inside its declared bounds. A result for bound `N` does not imply a
result for `N + 1`.

Kani documents that concurrency is outside its supported concurrent-semantics scope. It treats
relevant execution sequentially. Kani also documents partial or overapproximated floating-point
intrinsics. Logarithmic intrinsics are not a numerical-precision proof route.

The Kani compiler, CBMC, solver backend, harness assumptions, and environment models remain in the
trust boundary.

### 7.5 Required negative controls

At minimum:

- reduce an unwind bound and require the unwinding assertion to fail;
- introduce a bounded index error and require a counterexample;
- remove an overflow check and require a counterexample;
- change a specialized mask and require an equivalence counterexample; and
- run one valid case just outside the proved input bound and label it as not covered.

### 7.6 Permitted claim

Use:

> Kani exhaustively checked this harness within the declared input and unwind bounds using Kani
> 0.67.0 and CBMC 6.8.0. It does not establish correctness outside those bounds, concurrent
> execution semantics, or numerical precision of transcendental functions.

Do not use:

- "Kani proved the algorithm for all inputs";
- "Kani verified parallel execution"; or
- "Kani proved the accuracy of `ln` or digamma."

## 8. Aeneas and Charon adoption record

### 8.1 Upstream pin and license

Aeneas had no stable release at the audit date. Its release page contained nightly prereleases.
The audit therefore uses an immutable source cut:

- Aeneas commit
  [`6e167c9b63a4dafd66d0e0edd9d94669f957ff7b`](https://github.com/AeneasVerif/aeneas/commit/6e167c9b63a4dafd66d0e0edd9d94669f957ff7b);
- Charon commit `527ea8e3b5dcb52edd6aef0f7bc34cc09c11dd59`;
- Charon Rust nightly `nightly-2026-06-01`;
- Lean `4.31.0`;
- mathlib `v4.31.0`; and
- OCaml switch example `5.3.0`.

Aeneas and Charon are licensed under Apache-2.0.

Primary pin sources:

- [Aeneas repository and build instructions](https://github.com/AeneasVerif/aeneas);
- [Aeneas release page](https://github.com/AeneasVerif/aeneas/releases);
- [Charon pin file](https://raw.githubusercontent.com/AeneasVerif/aeneas/6e167c9b63a4dafd66d0e0edd9d94669f957ff7b/charon-pin);
- [Charon Rust toolchain](https://raw.githubusercontent.com/AeneasVerif/charon/527ea8e3b5dcb52edd6aef0f7bc34cc09c11dd59/charon/rust-toolchain);
- [Charon Apache-2.0 license](https://raw.githubusercontent.com/AeneasVerif/charon/527ea8e3b5dcb52edd6aef0f7bc34cc09c11dd59/LICENSE.md);
- [Lean backend toolchain](https://raw.githubusercontent.com/AeneasVerif/aeneas/6e167c9b63a4dafd66d0e0edd9d94669f957ff7b/backends/lean/lean-toolchain);
- [Lean backend mathlib pin](https://raw.githubusercontent.com/AeneasVerif/aeneas/6e167c9b63a4dafd66d0e0edd9d94669f957ff7b/backends/lean/lakefile.lean); and
- [Apache-2.0 license](https://raw.githubusercontent.com/AeneasVerif/aeneas/6e167c9b63a4dafd66d0e0edd9d94669f957ff7b/LICENSE.md).

### 8.2 Reproducible experiment rule

Use a detached full commit. Do not use a moving nightly name as the evidence identity.

```text
git clone https://github.com/AeneasVerif/aeneas.git
git -C aeneas checkout --detach 6e167c9b63a4dafd66d0e0edd9d94669f957ff7b
cd aeneas
opam switch create 5.3.0
eval "$(opam env)"
make setup-charon
make
```

`make setup-charon` must resolve the exact Charon commit in `charon-pin`. Before evidence is
accepted, export the complete OPAM switch and retain the Aeneas `flake.lock`, if Nix is used.

The translation commands are:

```text
charon cargo --preset=aeneas
./bin/aeneas -backend lean [OPTIONS] <LLBC_FILE>
```

Retain:

- the Aeneas and Charon commits;
- Charon nightly;
- OCaml switch export;
- Lean and mathlib pins;
- translation flags;
- source digest;
- generated LLBC digest;
- generated Lean digest; and
- the final Lean checker output.

### 8.3 Experiment scope

Translate only the same small pure kernel selected for the Verus pilot. Compare the generated
statement with the handwritten Lean specification. Do not translate the complete crate.

The experiment must answer:

1. Does Charon accept the kernel without a semantic workaround?
2. Does Aeneas generate a stable Lean model?
3. Can the generated model use the repository Lean 4.32.0 environment?
4. Which external definitions require handwritten models?
5. Does a source mutation change the generated theorem or fail the proof?

### 8.4 Trust boundary and blockers

Aeneas supports a subset of safe Rust. Unsafe code and concurrency are out of scope. Some loop
control patterns and library operations are unsupported. Handwritten models of external
definitions become trusted inputs.

The selected Aeneas backend pins Lean and mathlib 4.31.0. The repository pins 4.32.0. This mismatch
blocks direct integration until one side is upgraded and the generated proofs are rechecked.

Charon translation, Aeneas translation, handwritten models, theorem correspondence, Lean, and the
compiler path remain in the trust boundary.

### 8.5 Required negative controls

At minimum:

- supply an unsupported Rust construct and require explicit rejection;
- mutate an event predicate and require a changed model or failed theorem;
- remove one handwritten model and require a translation or proof failure;
- change the Charon checkout and require the pin check to fail; and
- test the generated source in Lean 4.31.0 and 4.32.0 without claiming equivalence.

### 8.6 Permitted claim

Use:

> Aeneas translated the accepted safe-Rust subset at the pinned Aeneas and Charon commits, and Lean
> checked the generated model's stated theorem. This does not establish translation support for
> all Rust, correctness of handwritten external models, unsafe or concurrent code, or binary
> equivalence unless those links are separately proved.

Do not use:

- "Aeneas verified the Rust implementation";
- "generated Lean proves the compiled binary"; or
- "the translation covers unsupported library code."

## 9. Rug and MPFR adoption record

### 9.1 Upstream pin and license

The selected pins are:

- Rug `1.30.0`, published on 10 July 2026;
- `gmp-mpfr-sys` `1.7.1`;
- MPFR `4.2.2`;
- GMP `6.3.0`; and
- MPC `1.4.1` only if a selected feature requires it.

Rug requires Rust 1.85 or newer. `gmp-mpfr-sys` requires Rust 1.71 or newer. Both requirements are
compatible with the repository Rust 1.89 minimum.

Rug, `gmp-mpfr-sys`, and MPFR use LGPL-3.0-or-later licensing in the cited package records. GMP
6.3.0 is available under LGPLv3 or GPLv2. A distribution review is mandatory.

Primary sources:

- [MPFR current release](https://www.mpfr.org/mpfr-current/);
- [MPFR manual](https://www.mpfr.org/mpfr-current/mpfr.html);
- [Rug 1.30.0 documentation and package metadata](https://docs.rs/rug/1.30.0/rug/);
- [Rug directed rounding modes](https://docs.rs/rug/1.30.0/rug/float/enum.Round.html);
- [`gmp-mpfr-sys` 1.7.1 metadata and bundled versions](https://docs.rs/gmp-mpfr-sys/1.7.1/gmp_mpfr_sys/); and
- [GMP copying conditions](https://gmplib.org/manual/Copying).

MPFR states that most functions are correctly rounded as if computed at infinite precision and
then rounded in the requested direction. `mpfr_log` computes the natural logarithm. `MPFR_RNDD`
rounds toward negative infinity. `MPFR_RNDU` rounds toward positive infinity. The faithful
rounding mode `MPFR_RNDF` is experimental and must not be used for a certificate.

### 9.2 Dependency pin rule for a future pilot

This record does not add the dependency. A future pilot must use an exact Rug version and the
repository lockfile:

```toml
[dependencies.rug]
version = "=1.30.0"
default-features = false
features = ["integer", "float", "std"]
```

Do not enable the experimental `use-system-libs` feature in `gmp-mpfr-sys` for reproducible
evidence. Use the bundled GMP and MPFR source versions. Record the Cargo package checksums and the
native archive digests that the build uses.

The preferred design is an optional offline oracle or a separate small crate. It must not silently
replace the stable binary64 API.

### 9.3 First numerical obligations

For categorical SxPID:

1. Keep histogram and event counts as exact integers.
2. Form exact rational count ratios.
3. Evaluate each logarithm once toward negative infinity and once toward positive infinity.
4. Apply outward rounding to all later arithmetic.
5. Apply the concrete Möbius transform to intervals.
6. Increase precision until the interval meets a declared width or stability rule.
7. Return `Unresolved` if an interval contains zero.
8. Return an ordering ambiguity if `I_min` candidate intervals overlap.
9. Retain exact input, expression-schema, precision-policy, and output digests.

The result schema must distinguish:

- certified positive;
- certified negative;
- certified zero, only when proved exactly;
- unresolved sign;
- unresolved minimizer order; and
- resource or precision limit.

A midpoint is not a certificate. A narrow interval is not proof of an estimator's statistical
validity.

This first backend does not cover continuous KSG. KSG needs separate proofs about neighbor
selection, represented distances, strict-radius semantics, estimator assumptions, and statistical
behavior.

### 9.4 Trust boundary and blockers

The following items remain trusted:

- MPFR implementation;
- GMP implementation;
- native build;
- Rust compiler;
- C ABI and FFI;
- `gmp-mpfr-sys`;
- Rug;
- wrapper code;
- interval-expression construction; and
- the statement that the count table represents the intended data.

`#![forbid(unsafe_code)]` in `pid-core` does not verify native transitive dependencies.

### 9.5 Required negative controls

At minimum:

- reverse one endpoint rounding direction and require an enclosure test to fail;
- use a near-zero atom and require `Unresolved`, not a sign claim;
- use overlapping `I_min` candidate intervals and require an ordering ambiguity;
- lower the precision ceiling and require a typed precision-limit result;
- mutate one count and require the input digest and result to change; and
- compare selected small tables with an independent high-precision implementation.

### 9.6 Permitted claim

Use:

> The certified backend returns an outward enclosure of the exact-real expression under MPFR
> 4.2.2's directed-rounding contract and the audited wrapper. It does not prove the existing
> binary64 result, the Rust compiler or FFI, or the MPFR implementation itself.

Do not use:

- "MPFR formally verified the result";
- "the current `f64` output is certified"; or
- "an interval proves estimator calibration."

## 10. Rocq Interval adoption record

### 10.1 Upstream pin and license

The selected stable pins are:

- Rocq `9.2.0`, released on 27 March 2026; and
- `coq-interval` `4.11.4`, published on 23 February 2026.

Rocq 9.3 release-candidate builds existed at the audit date. They are prereleases and are not the
selected pin.

Rocq core is licensed under LGPL-2.1-only. `coq-interval` is licensed under CeCILL-C.

The package archive SHA-512 published for `coq-interval` 4.11.4 is:

```text
5b2ccff32c3d6caa9002455dc472d6c4c8f70337581d038ca432dd92ed90b262
b203960a2a62896c12992be2ff2436bf7e6a8ffd3aec625859f47088d262ef00
```

The two displayed lines are one continuous digest.

Primary sources:

- [Rocq project site](https://rocq-prover.org/);
- [Rocq 9.2.0 release](https://github.com/rocq-prover/rocq/releases/tag/V9.2.0);
- [Rocq core package license metadata](https://raw.githubusercontent.com/rocq-prover/rocq/V9.2.0/rocq-core.opam);
- [`coq-interval` 4.11.4 package record](https://rocq-prover.org/p/coq-interval/4.11.4);
- [`coq-interval` version list](https://rocq-prover.org/p/coq-interval/latest/versions);
- [Interval documentation](https://coqinterval.gitlabpages.inria.fr/);
- [exact OPAM metadata](https://raw.githubusercontent.com/coq/opam-coq-archive/master/released/packages/coq-interval/coq-interval.4.11.4/opam);
- [Rocq OPAM instructions](https://rocq-prover.org/docs/using-opam); and
- [Rocq compile and check commands](https://docs.rocq-prover.org/master/refman/practical-tools/coq-commands.html).

The exact OPAM metadata permits the modern split `coq-core` and `coq-stdlib` dependency route. It
also requires Flocq, MathComp, Coquelicot, bignums, OCaml, and a compiler. Do not infer the actual
dependency closure from a shortened package-page summary.

### 10.2 Pin and installation rule

Use OPAM 2.1 or newer and a dedicated switch:

```text
opam switch create 4.14.2
eval "$(opam env)"
opam repo add rocq-released https://rocq-prover.org/opam/released
opam install rocq-prover=9.2.0 rocq-core=9.2.0 coq-interval=4.11.4
opam pin add rocq-core 9.2.0
opam pin add coq-interval 4.11.4
opam switch export --full rocq-9.2.0-interval-4.11.4.export
```

Also retain:

- exact OPAM version;
- exact OPAM repository commit;
- full switch export;
- package archive hashes;
- certificate source digest;
- compiled object digest; and
- checker output with assumptions.

Compile and independently check a certificate with:

```text
rocq compile -q Certificate.v
rocq check -o Certificate.vo
```

The `-o` output exposes the logical context and assumptions. The evidence gate must reject
`Admitted`, `admit`, unexpected axioms, and an incomplete check.

### 10.3 First certificate obligations

Use Rocq Interval only after the executable interval expression has a versioned schema. Candidate
theorems are:

- a rational logarithmic expression lies inside emitted endpoints;
- an atom interval is strictly positive or strictly negative;
- two `I_min` intervals are strictly ordered;
- a Möbius interval reconstruction encloses every cumulative coordinate; and
- a serialized certificate matches an exact count-table and expression-schema digest.

The theorem statement must include or bind to the exact input identity. A theorem about the wrong
count table is still a valid theorem.

### 10.4 Trust boundary and blockers

Rocq's kernel checks the proof object. It does not prove that:

- the generator encoded the intended formula;
- the generator used the intended count table;
- the file digest was bound to a runtime operation;
- `pid-rs` used the checked result; or
- the statement has statistical meaning.

The generator, statement schema, input binding, extraction or serialization code, OCaml runtime,
Rocq kernel, and platform remain in the trust boundary.

### 10.5 Required negative controls

At minimum:

- mutate one interval endpoint and require proof failure;
- mutate the bound input digest and require binding failure;
- insert `Admitted` and require the policy gate to fail;
- add an unexpected axiom and require the assumption check to fail; and
- present a valid proof for a different count table and require the identity check to reject it.

### 10.6 Permitted claim

Use:

> Rocq's kernel independently checked the emitted inequality theorem and exposed its remaining
> assumptions. It does not prove that the generator encoded the intended data and expression or
> that the `pid-rs` runtime used that certificate.

Do not use:

- "Rocq verified the Rust implementation";
- "the certificate proves the input provenance"; or
- "the theorem proves application validity."

## 11. Cross-layer evidence rules

### 11.1 A result stays inside its layer

| Evidence | What it can support | What it cannot support by itself |
|---|---|---|
| Existing Lean theorem | Exact theorem in the declared Lean model | Rust implementation, binary64 output, data assumptions |
| Verus proof | Contracts for opted-in supported functions | Compiler, external assumptions, transcendental accuracy |
| Kani harness | Exhaustive bounded property | Unbounded inputs, concurrent behavior, numerical accuracy |
| MPFR interval | Outward enclosure for one encoded expression | Existing `f64`, statistical calibration, FFI proof |
| Rocq certificate | Kernel-checked encoded theorem | Correct generator, runtime use, intended data identity |
| Hidden benchmark | Observed behavior on a frozen corpus | Universal correctness or a mathematical theorem |

Evidence can compose only when a checked bridge connects the artifacts. The bridge must bind:

- source revision;
- tool revision;
- specification revision;
- input identity;
- generated-artifact identity;
- result identity;
- assumptions; and
- claim scope.

### 11.2 Required evidence envelope

Every accepted pilot result must record:

1. tool name and exact version or commit;
2. all compiler, solver, and backend pins;
3. host, target, and installation asset digest;
4. source commit and dirty-state policy;
5. command line;
6. input bounds or theorem statement;
7. assumption inventory;
8. generated artifact hashes;
9. checker result;
10. negative-control result;
11. known unsupported cases; and
12. exact permitted claim text.

A green exit code without this envelope is a development result. It is not release evidence.

### 11.3 Fail-closed rules

The process must return a typed failure or unresolved result when:

- a tool version differs from the pin;
- an installation asset digest is absent;
- a solver or compiler version is unknown;
- an unwinding assertion does not pass;
- an assumption is not approved;
- a generated artifact does not match its digest;
- an interval does not determine the requested sign or order;
- a certificate contains an admission or unexpected axiom; or
- a supported-subset translator rejects the source.

The process must not change a failure into an approximate success.

## 12. Pilot exit criteria

### 12.1 Rug and MPFR

The pilot can advance only if:

- all endpoint operations are outward rounded;
- precision escalation terminates with a typed result;
- ambiguous signs and ties remain unresolved;
- exact count and expression identities are retained;
- independent small-table checks agree; and
- the license review defines the distribution route.

### 12.2 Kani

The pilot can advance only if:

- every harness declares bounds;
- every loop has a passing unwinding assertion;
- meaningful mutations produce counterexamples;
- no harness models transcendental accuracy; and
- the evidence report states the exact bounded domain.

### 12.3 Verus

The pilot can advance only if:

- the complete selected kernel verifies;
- the assumption inventory is empty or explicitly approved;
- semantic mutations fail;
- the erased program passes the Rust 1.89 gates; and
- ordinary Rust tests agree with the declared specification fixtures.

### 12.4 Rocq Interval

The pilot can advance only if:

- the certificate schema is versioned;
- `rocq check -o` reports no unexpected assumption;
- admitted proofs are rejected;
- identity-binding mutations fail; and
- the certificate can be regenerated from archived exact inputs.

### 12.5 Aeneas

The experiment can advance only if:

- the selected Rust subset translates without an unsound workaround;
- handwritten external models are minimal and reviewed;
- generated theorem correspondence is documented;
- Lean toolchain compatibility is resolved; and
- source mutations are visible to the generated model and proof.

## 13. Adoption conclusion

The most useful immediate addition is not another isolated exact-real lemma. It is an executable
categorical interval oracle with explicit unresolved states. Kani can then attack bounded compiled
behavior. Verus can attack unbounded functional contracts for the same small kernel.

Rocq Interval is useful only when an independent certificate has operational value and the
generator-to-statement bridge is controlled. Aeneas is a valuable research route, but its current
release and toolchain state does not justify production adoption.

This layered order improves assurance without changing the scientific claim:

> `pid-rs` is not end-to-end formally verified. Each future result must state the exact layer,
> theorem or bound, assumptions, tool pins, trust boundary, and unsupported claims.

## 14. Primary source index

### Verus

- [Release `0.2026.07.18.3a4d30b`](https://github.com/verus-lang/verus/releases/tag/release/0.2026.07.18.3a4d30b)
- [Verus guide](https://verus-lang.github.io/verus/guide/)
- [Cargo integration](https://verus-lang.github.io/verus/guide/cargo_verus.html)
- [Trusted computing base](https://verus-lang.github.io/verus/guide/tcb.html)
- [Assumption specifications](https://verus-lang.github.io/verus/guide/reference-assume-specification.html)

### Kani

- [Release `0.67.0`](https://github.com/model-checking/kani/releases/tag/kani-0.67.0)
- [Installation guide](https://model-checking.github.io/kani/install-guide.html)
- [Kani manual](https://model-checking.github.io/kani/)
- [Loop unwinding](https://model-checking.github.io/kani/tutorial-loop-unwinding.html)
- [Rust feature support](https://model-checking.github.io/kani/rust-feature-support.html)
- [Intrinsic support](https://model-checking.github.io/kani/rust-feature-support/intrinsics.html)

### Aeneas and Charon

- [Aeneas repository](https://github.com/AeneasVerif/aeneas)
- [Aeneas releases](https://github.com/AeneasVerif/aeneas/releases)
- [Pinned Aeneas commit](https://github.com/AeneasVerif/aeneas/commit/6e167c9b63a4dafd66d0e0edd9d94669f957ff7b)

### MPFR and Rug

- [MPFR](https://www.mpfr.org/)
- [MPFR 4.2.2](https://www.mpfr.org/mpfr-current/)
- [MPFR manual](https://www.mpfr.org/mpfr-current/mpfr.html)
- [Rug 1.30.0](https://docs.rs/rug/1.30.0/rug/)
- [`gmp-mpfr-sys` 1.7.1](https://docs.rs/gmp-mpfr-sys/1.7.1/gmp_mpfr_sys/)

### Rocq and Interval

- [Rocq](https://rocq-prover.org/)
- [Rocq 9.2.0](https://github.com/rocq-prover/rocq/releases/tag/V9.2.0)
- [`coq-interval` 4.11.4](https://rocq-prover.org/p/coq-interval/4.11.4)
- [Interval documentation](https://coqinterval.gitlabpages.inria.fr/)
- [Rocq OPAM instructions](https://rocq-prover.org/docs/using-opam)
- [Rocq compile and check tools](https://docs.rocq-prover.org/master/refman/practical-tools/coq-commands.html)
