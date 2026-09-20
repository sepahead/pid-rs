# Foundation audit: preserved source binding

This archive keeps the exact evidence record from before the categorical SxPID3 lookup repair.
It is historical evidence, not the current Rust-source binding. Use the
[current record](../../evidence/foundational-sxpid-lcr-exact-audit.json) with the
[foundation audit](../../../FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md).

## Why the record changed

The exact-rational checker computes the categorical shared-exclusions witness independently of
the Rust implementation. It also records the full `sxpid.rs` digest. The safe-lookup repair changed
that file, so the PDF check correctly rejected the old evidence at its byte comparison. This
failure occurred before the foundation Lean checks and PDF build. It does not establish a
mathematical error.

On 20 September 2026, the unchanged checker was run in normal and optimized Python modes against
the repaired Rust source. The two generated records were byte-identical. A complete comparison
with the predecessor found exactly one changed field: `bindings.rust_kernel_sha256`. All exact
atoms, event counts, witness premises, mutation outcomes, checker and regression bindings, schema,
and original audit date were unchanged. The original date describes the audit's context; it is
not the date of this replay.

| Record | SHA-256 |
|---|---|
| [Preserved evidence](evidence.json), 37,558 bytes | `5e4c6d59d658381502456e7a3c0c09b77e9ccaf3a41e17ae95a04888d148c0b9` |
| Regenerated current evidence, 37,558 bytes | `8654938507b5fcb75f217e25b2cec5e221c0eb3a11a7006c2c1b29a3eb49e114` |
| Previous Rust source | `ea51e92b5f23bd627f21dd239fb4dba63f9c1067be3ca3294c58d72b00ec0771` |
| Repaired Rust source | `748a3ead55f247db341cf687d5ec29be2fd7e935cd0c627433c4667ce7ef18d5` |

The current record comes from the actual generator output. The PDF comparison remains exact.
Other dated receipts that cite the previous Rust digest remain unchanged. The rejected PDF run
remains a failed run; the successful evidence replay does not make the full PDF suite pass.

This is a provenance repair for an existing finite categorical witness. It introduces no new PID,
theorem, estimator, calibration guarantee, or application result. The separate Lean proofs and
full publication checks retain their own verification requirements.
