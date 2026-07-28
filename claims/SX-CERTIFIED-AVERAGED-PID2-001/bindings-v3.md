# Source and schema bindings for SX-CERTIFIED-AVERAGED-PID2-001, revision 3

## Binding status

Revision 3 binds the independent verifier's schema-v3 source and qualification harness while
retaining the revision-2 producer, mathematical, report, resource, and exact-product contracts.
It deliberately does not embed a self-referential Git identifier. A full containing Git commit
and tree can provide ordinary repository-source retrieval only after these bytes settle and are
committed. No such future identifier is asserted here.

The packet has no independent human custody, external transparency record, authorship proof,
binary/native-archive attestation, or fresh public green CI rerun.

## Version identifiers

| Object | Exact identifier |
|---|---|
| Input schema | `pid-rs/categorical-sxpid2-count-table/v1` |
| Definition revision | `makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1` |
| Resource policy | `sxpid2-certification-default-v2` |
| Producer report schema | `pid-rs/certified-sxpid-report/v2` |
| Exact-expression schema | `pid-rs/exact-log-linear/v1` |
| Independent-verification schema | `pid-rs/certified-sxpid-independent-verification/v3` |
| Loaded-execution digest domain | `pid-certified-sxpid-independent-loaded-execution-v3\0` |
| Units | `nats` |

A version-2 independent-verification report is historical input, not a revision-3 report.
Unsupported identifiers, unknown fields, duplicate JSON keys, noncanonical integer strings, and
claim-boundary drift remain fail-closed errors.

## Revision-3 source digests

The final-byte checker must recompute these values rather than trusting this table:

| Artifact | SHA-256 |
|---|---|
| `audit/tools/certified-sxpid/scripts/verify_certificate.py` | `c90572571eac9b5cd5cd11d526a211dd0dfa7ab45274f6c038c0f8338cd2958e` |
| `audit/tools/certified-sxpid/scripts/check-independent-verifier.py` | `4327afdcce04421544481e0af9abf15dd3709ea75c5df994cb33b3ce3de91c17` |

The source digest identifies exact source bytes. The report's
`verifier_loaded_execution_sha256` identifies the project-defined live-code/constant digest under
the reported Python runtime. Neither is an executable digest, semantic-equivalence proof,
authorship statement, or external attestation.

## Loaded-execution normalization binding

Before marshalling the inspected code objects, revision 3 recursively primes string-intern state
for:

- `co_name` and `co_qualname`;
- `co_names`, `co_varnames`, `co_freevars`, and `co_cellvars`;
- string and code-object entries reached through `co_consts`;
- tuple and frozenset members reached through those constants; and
- slice start, stop, and step values reached through those constants.

It then uses the existing filename-normalized code-object representation and the revision-3
digest domain above. A deterministic typed encoding binds by name all 51 declared uppercase
semantic/configuration globals, including the four active exact-product admission ceilings that
the earlier positional inventory omitted. The change is intended to remove the observed
nonsemantic lazy-cache dependence and close that semantic-state omission. It is not a general
Python canonicalizer or a proof that every behavior-affecting runtime object is enumerated.

The qualification harness binds two cache/code controls, a 51-constant mutation sweep, and one
source-mutation control:

1. `check_loaded_execution_cache_stability` must give the same digest for isolated cold and
   explicitly interned copies of identical probe code;
2. `check_post_import_execution_mutation` must reject a live `__code__` replacement through the
   intended integrity error and accept again only after restoration;
3. `check_post_import_semantic_constant_mutations` must mutate each of the exact 51-name
   configuration inventory, reject each mutation through the intended integrity path, and recover
   only after restoration; and
4. `check_cache_normalization_source_mutation` must, on CPython 3.11, remove the normalization call
   in an isolated verifier source mutant and observe the intended loaded-execution rejection. It
   reports zero on other Python versions rather than claiming that the affected path was exercised.

## Producer and product bindings retained from revision 2

The producer source-manifest membership remains the same 17 paths listed in
[bindings-v2.md](bindings-v2.md), including the standalone tool README and `src/product.rs`.
Updating a manifest member changes the runtime manifest digest, but it does not by itself change
the v2 manifest encoding, report schema, mathematical functional, or resource policy. An accepted
verification recomputes the complete manifest from the local bounded regular files.

The exact-product ceilings, admission ordering, statuses, decisions, witness vocabulary, interval
consistency, finite-domain evidence, and seven Lean theorems remain those adjudicated in revision
2. No revision-2 count is silently relabelled as new revision-3 mathematical evidence.

## Observed failure binding

[`audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md`](../../audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md)
binds:

- Actions run `30305288762`;
- job `90107923447`;
- commit `dc7b8de0a87443ef2bcde71b19938642f1af2197`;
- tree `88b24c0ba4fcad4bd749b9146486143397b6a6eb`;
- CPython 3.11.15;
- the exact failing verifier and harness source hashes; and
- the retrieved job-log byte-stream digest.

That is retained process evidence for a fail-closed false rejection. It is not a green-run receipt
or evidence that the full CI run had no other failures.

## Remaining binding obligations

1. Recompute the two revision-3 source digests after every writer stops.
2. Update the machine-readable catalog and every generated/reference-hash projection that binds
   it.
3. Rebuild and visually inspect the human assurance papers and committed PDFs that state the
   verification schema.
4. Run normal and optimized qualification, claim-packet mutation checks, and all ordinary gates
   on final bytes.
5. Record the first full containing Git commit and tree without inserting a circular identifier
   into this packet.
6. Obtain and retain a fresh public CI rerun; do not infer it from the candidate correction.
7. Obtain independent source acquisition, review, execution, and external custody for any stronger
   assurance claim.
