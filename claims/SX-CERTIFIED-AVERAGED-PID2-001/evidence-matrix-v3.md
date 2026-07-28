# Revision-3 evidence matrix for SX-CERTIFIED-AVERAGED-PID2-001

Revision-1 interval evidence and revision-2 exact-product evidence remain in
[evidence-matrix.md](evidence-matrix.md) and [evidence-matrix-v2.md](evidence-matrix-v2.md). The
rows below adjudicate only the loaded-execution cache normalization and revision boundary.

| Statement | Evidence | Status | Boundary |
|---|---|---|---|
| The revision-2 integrity route produced a fail-closed false rejection on CPython 3.11.15. | Actions run `30305288762`, job `90107923447`, exact commit/tree/source hashes, error, and retrieved log digest in the incident memo | Observed and retained | The complete CI run had unrelated failures; this is not a green-run receipt |
| The observed drift can arise from nonsemantic lazy string-intern cache state in marshalled code objects. | Minimal dynamic-string qualification probe and source-level diagnosis | Executably targeted; local CPython 3.11/3.14 normal and optimized replay passed | Does not characterize every CPython cache, marshal, or code-object transition |
| Revision 3 primes every declared string-bearing code-object field before hashing. | Recursive `_stabilize_code_string_cache` source path | Reviewed implementation claim | No checked refinement from Python semantics to digest bytes |
| The loaded-execution digest is stable across the named cache transition. | `check_loaded_execution_cache_stability` compares isolated cold and explicitly interned copies | One new cache control passed in four local replays | Named fault sensitivity only |
| A live post-import function-code replacement still fails through the integrity guard. | `check_post_import_execution_mutation`, including restoration/recovery check | One new integrity control passed in four local replays | Does not prove complete process immutability |
| Every declared uppercase semantic/configuration global affects the loaded-execution digest. | Typed all-uppercase inventory plus `check_post_import_semantic_constant_mutations` | All 51 named mutations rejected and recovered in four local replays | Imported runtime objects, underscored/lowercase state, and mutate-use-restore races remain trusted or excluded |
| Removing the normalization call exposes the original affected integrity path. | `check_cache_normalization_source_mutation` | One source mutant killed in both local CPython 3.11 modes; correctly not exercised on 3.14 | Version-conditioned named mutant, not a universal implementation proof |
| Old and new digest semantics cannot share one report identity. | Independent-verification schema v2 to v3 and loaded-execution domain v1 to v3 | Source and packet bound; catalog replay open | A schema label is not implementation proof |
| Producer report/resource/product behavior is unchanged. | Exact identifiers and unchanged source-contract inventory | Contractually retained | The tool README is a source-manifest member, so its byte update changes the runtime manifest digest |
| Mathematical/exhaustive/formal evidence counts are unchanged. | Revision-2 evidence records and theorem map | Retained, not rerun or promoted here | Two added runtime controls, 51 semantic-constant mutations, and one affected-runtime source mutant are not new SxPID mathematics |
| Revision 3 is distinct from revisions 1 and 2. | Separate claim, decision, binding, obligations, evidence, theorem map, failure controls, and revision-index row | Repository packet implemented; final governance replay open | No full containing commit, external archive, or independent review yet |
| CPython, `sys.intern`, `marshal`, or the verifier is formally verified. | No evidence | Unsupported | Remains in the trusted computing base |
| Digests are portable semantic hashes across runtimes. | No evidence; explicitly excluded | Unsupported | Runtime implementation/version and marshal format can matter |

## Retained artifact

- `audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md`
- `audit/tools/certified-sxpid/scripts/verify_certificate.py`
- `audit/tools/certified-sxpid/scripts/check-independent-verifier.py`
- `claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md`

Local source hashes and a hosted-job-log digest detect drift in named bytes. They are not
signatures, authorship records, independent custody, or executable attestations.
