# Source and schema bindings for SX-CERTIFIED-AVERAGED-PID2-001, revision 2

## Binding status

Revision 2 re-adjudicates the exact source manifest, certificate, input, lockfile, verifier source,
and semantic constants bound during an accepted run. The packet deliberately does not embed a
self-referential Git identifier. Retrieval by a full Git commit hash whose tree contains these
exact bytes supplies an ordinary repository-source binding for that retrieval. It does not supply
an external transparency-log entry, independent custody, authorship proof, or binary/native-
archive attestation. Those absences are explicit and must not be filled with revision-1 bindings.

## Version identifiers

| Object | Exact identifier |
|---|---|
| Input schema | `pid-rs/categorical-sxpid2-count-table/v1` |
| Definition revision | `makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1` |
| Resource policy | `sxpid2-certification-default-v2` |
| Producer report schema | `pid-rs/certified-sxpid-report/v2` |
| Exact-expression schema | `pid-rs/exact-log-linear/v1` |
| Independent-verification schema | `pid-rs/certified-sxpid-independent-verification/v2` |
| Units | `nats` |

Revision-1 report, verifier, or resource-policy objects are not revision-2 inputs. Unknown fields,
duplicate JSON keys, noncanonical integer strings, unsupported identifiers, and claim-boundary
drift are fail-closed errors.

## Exact-product resource binding

The producer and independent verifier agree on the following additional revision-2 limits:

| Limit | Value |
|---|---:|
| Terms in one exact-product comparison | 256 |
| Maximum absolute denominator-cleared exponent | 16,384 |
| Projected rational-product bits per expression | 262,144 |
| Aggregate projected rational-product bits | 1,048,576 |

These are admission ceilings, not performance promises. Planning computes exponent and bit-growth
evidence before powering. A per-expression or aggregate rejection records an unavailable product
decision while leaving the separately verified dyadic interval route intact.
The exact-product mutation receipt separately records two sentinel controls that replace the
auxiliary checker's powering primitive and observe zero calls for local and aggregate rejection.
Those controls bind reviewed ordering behavior; they are not a verified resource-cost theorem.

All revision-1 structural and independent-verifier bounds continue unless replaced by the exact
revision-2 resource-policy object. The parser's 8,192-bit total-count ceiling does not authorize
an 8,192-bit exponentiation.

## Revision-2 producer source manifest

The length-delimited source manifest has 17 fixed members:

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
14. `src/product.rs`
15. `src/report.rs`
16. `src/resource.rs`
17. `src/schema.rs`

The independent verifier rejects symlinked or nonregular members, bounds member and aggregate
bytes, uses stable bounded reads, recomputes the manifest encoding before and after verification,
and requires the report binding to match. This establishes local drift detection for the named
bytes, not authorship or external authenticity.

## Product decision vocabulary

For status `compared`, the only decisions are:

- `certified_negative`;
- `certified_exact_zero`; and
- `certified_positive`.

The exact-zero witness is `exact_multiplicative_product_equals_one` and is present only for the
zero decision. For `not_compared_per_expression_preflight_limit` and
`not_compared_total_preflight_limit`, decision and witness are absent. The independent verifier
recomputes this state rather than trusting certificate text.

## Formal and executable bindings

- Six generic exact log/product/sign theorems and the retained witness's exact five-factor rational
  identity are checked by the pinned Lean project under `audit/formal/lean-exact-log-product/` and
  its deterministic repository checker. The separate exact-rational and Rust routes bind those
  five factors to the SxPID coordinate.
- Concrete event/product reconstruction is exercised by the independent Python checker and
  exact-product qualification scripts.
- The exact product paper, Markdown note, rendered PDF, and deterministic PDF checker state the
  proof and boundaries.
- Evidence JSON binds deterministic checker configurations and observed results. It is local
  evidence, not a signature or external attestation.

The specific artifact inventory is authoritative in `method-catalog.json` and is checked by the
revision-2 claim-packet gate.

## Remaining binding obligations

1. Preserve and communicate the full immutable Git commit that contains the revision-2 packet and
   exact source bytes; a branch or abbreviated hash is insufficient.
2. Record exact final source and evidence digests after all files settle; do not reuse historical
   revision-1 digests.
3. Have an independent reviewer acquire and replay the source under separate custody.
4. If binaries are distributed, add a reviewed LGPL-compliant distribution route plus executable
   and native-archive identity evidence.
5. Add an external timestamp/transparency record if assurance beyond ordinary Git history is
   required.
