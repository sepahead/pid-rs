# Revision-3 obligations for SX-CERTIFIED-AVERAGED-PID2-001

This file records only the verifier-integrity delta. Revision-1 interval obligations and
revision-2 exact-product obligations remain historical in [obligations.md](obligations.md) and
[obligations-v2.md](obligations-v2.md); they are not retroactively rewritten.

## Obligation graph

```text
revision-2 mathematical/report/product contract
                    |
                    v
       C3 remove nonsemantic intern-cache drift
                    |
          +---------+---------+---------+
          |                   |         |
          v                   v         v
 I3 cold/warm control   M3 live-code   G3 all 51 declared
                           control      constants mutate
          |                   |         |
          +---------+---------+---------+
                    |
                    v
       N3 remove-normalization source mutant
                    |
                    v
        S3 verification schema v3
                    |
                    v
       Z3 revision-3 re-adjudication

P3 checked Python/runtime semantics + H3 independent custody
  -> stronger runtime/external assurance (open)
```

## Detailed obligations

| ID | Obligation | Status | Retained evidence | Remaining boundary |
|---|---|---|---|---|
| C3 | Remove the loaded-execution digest's dependence on the observed lazy string-intern cache state without deleting inspected executable code or semantic constants. | Implemented; local CPython 3.11/3.14 normal and optimized replay passed | `_stabilize_code_string_cache`, loaded-execution digest domain v3, typed constant encoding, source review | CPython code-object, `sys.intern`, and `marshal` correctness remain trusted |
| I3 | Require equal normalized digests for isolated cold and explicitly interned copies of the qualified dynamic string. | Named executable control passed in the four local replays | `check_loaded_execution_cache_stability` | One named cache transition is not a proof over every interpreter state |
| M3 | Preserve sensitivity to a post-import replacement of inspected live function code. | Named executable control passed in the four local replays | `check_post_import_execution_mutation` | Uninspected process state and arbitrary equivalent mutations remain outside the control |
| G3 | Bind every one of the 51 declared uppercase semantic/configuration globals and reject a post-import mutation of each. | All 51 typed mutations rejected and recovered in each of four local replays | Automatic uppercase inventory, typed encoding, `check_post_import_semantic_constant_mutations` | Imported runtime objects, lowercase/underscored state, and mutate-use-restore races remain outside the inventory/control |
| N3 | On the affected CPython 3.11 route, reject an isolated verifier source mutant that removes the normalization call. | One intended-path source mutation killed in both local CPython 3.11 modes; version-conditioned lane reports zero on 3.14 | `check_cache_normalization_source_mutation` | One source mutant does not prove normalization completeness or other-runtime behavior |
| S3 | Reject verification-schema v2 as revision 3 and emit only `pid-rs/certified-sxpid-independent-verification/v3` for the corrected route. | Closed in source; packet/catalog replay open | Verifier constant, harness assertion, claim checker | Schema identity does not prove implementation correctness |
| B3 | Bind the exact verifier and qualification-harness bytes used by revision 3. | Locally specified; final containing commit open | [bindings-v3.md](bindings-v3.md), source hashes | No external transparency, binary identity, or independent custody |
| E3 | Retain the observed CPython 3.11.15 failure without converting it into a mathematical failure or a green-run claim. | Recorded | CI incident memo, run/job/commit/tree/log digest | Hosted-log retention and a fresh public CI rerun remain external/open |
| U3 | Preserve revision-2 report, resource, expression, mathematical, product, and evidence-count semantics. | Required invariant | Explicit unchanged-object inventory and checker tokens | A future change to any retained object requires another revision |
| Z3 | Re-adjudicate revision 3 without silently rewriting revisions 1 or 2. | Conditionally supported; integration closure open | [claim-v3.md](claim-v3.md), [decision-v3.md](decision-v3.md), revision index | Catalog, assurance-paper/PDF, changelog, final CI, and commit custody remain open |
| P3 | Deductively connect source bytes, Python compilation, code objects, cache normalization, marshal bytes, and integrity acceptance. | Open | No end-to-end proof | Requires a checked runtime/refinement route |
| H3 | Obtain independent-human source acquisition, execution, review, and retained custody. | External/open | None | Requires another actor and durable external record |

## Acceptance invariant

Revision 3 may carry forward revision 2's two conditional per-input implications only when:

1. the complete verification report uses schema v3;
2. the source and loaded-execution integrity checks both pass on the same accepted run;
3. nonsemantic intern-cache state alone does not change the loaded-execution digest;
4. every one of the reviewed 51-name semantic/configuration inventory has its exact typed value;
5. the revision-2 interval and exact-product acceptance rules remain unchanged; and
6. no skipped, failed, partial, version-2, or producer-only output is treated as revision-3
   acceptance.
