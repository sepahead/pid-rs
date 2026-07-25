# Source and schema bindings for SX-CERTIFIED-AVERAGED-PID2-001

## Binding status

The independently hardened verifier and its qualification harness are committed unchanged at
`b8b9a48b88cb28d812d8cbd70b8f999a3bac5a8e`. The commit is on the public `main` history. The
two file digests below were recomputed from both the checked-out files and `git show` of that
commit; the pairs were identical.

The producer source-manifest digest below includes the current tool README and is bound by its
exact digest rather than by a self-referential packet commit. After the enclosing Git commit is
created and pushed, that first commit containing this packet and manifest value is recoverable
from history. Embedding the enclosing commit inside the bytes that determine the commit would be
circular.

These bindings establish repository source identity for the named bytes. They are not an external
transparency-log entry, authorship statement, binary attestation, independent review, or
independent-custody record.

## Version identifiers

| Object | Exact identifier |
|---|---|
| Input schema | `pid-rs/categorical-sxpid2-count-table/v1` |
| Definition revision | `makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1` |
| Resource policy | `sxpid2-certification-default-v1` |
| Producer report schema | `pid-rs/certified-sxpid-report/v1` |
| Exact-expression schema | `pid-rs/exact-log-linear/v1` |
| Independent-verification schema | `pid-rs/certified-sxpid-independent-verification/v1` |
| Units | `nats` |

Unknown schema fields, duplicate JSON keys, noncanonical integer strings, and unsupported
identifiers are fail-closed errors.

## Embedded producer claim-boundary binding

The producer report and independent verifier pin this exact permitted-claim string:

> For this canonical exact two-source empirical count table, pinned SxPID definition and lattice,
> precision policy, and locked dependency versions, each emitted dyadic interval encloses the
> tool-encoded exact-real averaged categorical SxPID coordinate, conditional on the recorded
> source wrapper, explicitly non-exhaustive build context, and unverified effective
> dependency-feature resolution, native-library, compiler, effective-build-flags, and data-meaning
> trust boundary. Manifest-requested Rug features and locked crate versions are reported; compiled
> native version constants, native archive digests, and executable digests are absent and are not
> claimed.

The exact excluded-claim identifiers are:

1. `pid-core_binary64_correctness`
2. `population_or_sampling_assumptions`
3. `estimator_consistency_or_calibration`
4. `continuous_ksg_isx_or_pid`
5. `three_or_four_source_sxpid`
6. `imin`
7. `pointwise_sxpid`
8. `quantization_equivalence`
9. `input_data_authenticity_or_provenance`
10. `mpfr_gmp_rug_or_compiler_correctness`
11. `downstream_application_validity`
12. `formal_verification_of_all_pid_rs`

The independent verifier rejects any altered or broadened claim-boundary field, even when the
certificate payload is resealed.

## Frozen source digests

| Artifact | SHA-256 |
|---|---|
| `audit/tools/certified-sxpid/scripts/verify_certificate.py` | `788d0461b21d0cf7d934e149c55aca9f2f5e19e7456d62cb8b738037b366262f` |
| `audit/tools/certified-sxpid/scripts/check-independent-verifier.py` | `d40ec1f960fb8edce71f5e60cf56f09a25a83ef365ada5b93ba33f737b2721c6` |
| `audit/tools/certified-sxpid/Cargo.lock` | `130555748aff0a0bf78a1421b0163922d2315fbb3f27c20eedd245ede4d250e6` |
| Current 16-member certifier source-manifest encoding | `069c3a14f50aacf6b11833357865dff20bc151400c4f9faf02f943fa869bae14` |

The source-manifest value is computed with domain
`pid-certified-sxpid-source-manifest-v1` plus a zero byte, followed by unsigned 64-bit big-endian
path and content lengths, path bytes, and content bytes for each member in fixed order.

The manifest members are:

1. `build.rs`
2. `Cargo.lock`
3. `Cargo.toml`
4. `README.md`
5. `src/digest.rs`
6. `src/directed.rs`
7. `src/error.rs`
8. `src/evaluate.rs`
9. `src/exact.rs`
10. `src/extract.rs`
11. `src/lattice2.rs`
12. `src/lib.rs`
13. `src/main.rs`
14. `src/report.rs`
15. `src/resource.rs`
16. `src/schema.rs`

The independent verifier rejects symlinked or nonregular manifest members, bounds member and total
bytes, checks stable file identity while reading, recomputes the producer's manifest encoding, and
checks it both before and after verification.

## Producer resource-policy binding

The producer and verifier agree on:

| Limit | Value |
|---|---:|
| Input bytes | 4 MiB |
| Rows | 4096 |
| State width per source or target | 32 tokens |
| Token bytes | 128 |
| Count digits | 1024 |
| Total-count bits | 8192 |
| Terms per exact expression | 4096 |
| Total exact terms | 8192 |
| Cumulative extraction terms | 1638 |
| Estimated exact-term JSON bytes | 8 MiB |
| Canonical certificate payload bytes | 10 MiB |

The cumulative limit is checked during extraction. It is not deferred until final terms are
materialized.

## Independent-verifier resource-policy binding

The independent verifier additionally enforces:

| Limit | Value |
|---|---:|
| Accepted input bytes | 4 MiB |
| Producer-certificate bytes | 11 MiB |
| Token bytes | 128 |
| Total-count bits | 8192 |
| Absolute dyadic exponent | 65,536 |
| Fixed-point bits | 2048 |
| Fixed-point schedule | 256, 384, 512, 768, 1024, 1536, 2048 |
| Decimal digits per report integer string | 4096 |
| Decimal digits per JSON numeric integer token | 24 |
| Canonical payload bytes | 10 MiB |
| One source-manifest member | 4 MiB |
| Complete source manifest | 32 MiB |
| Verifier source bytes | 2 MiB |

It also re-enforces the applicable producer structural limits during independent reconstruction.
Exhausting the fixed schedule without proving subset containment is a rejection.

## Replay environment

The recorded local replay used:

- Python 3.14.6;
- rustc 1.96.0 (`ac68faa20c58cbccd01ee7208bf3b6e93a7d7f96`);
- Cargo 1.96.0;
- host `aarch64-apple-darwin`.

These strings describe the local replay. They do not attest to binary identity, toolchain
correctness, or reproducibility on another machine.

## Primary semantic source

The SxPID event semantics are attributed to:

Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral, “Introducing a differentiable measure of
pointwise shared information,” *Physical Review E* 103, 032149 (2021),
[DOI](https://doi.org/10.1103/PhysRevE.103.032149),
[arXiv v5](https://arxiv.org/pdf/2002.03356v5).

The existing provenance audit records the audited arXiv PDF SHA-256 as
`5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6`.
A citation establishes provenance; it does not prove that either implementation transcribes the
paper correctly.

## Remaining binding obligations

1. If binaries are distributed, add a separately reviewed LGPL-compliant distribution route and
   artifact/native-archive digests.
2. For external assurance, have a reviewer obtain the source independently and replay the bound
   commands under retained custody records.
3. Add a transparency-log or independently timestamped packet digest if assurance beyond ordinary
   public Git history is required.
