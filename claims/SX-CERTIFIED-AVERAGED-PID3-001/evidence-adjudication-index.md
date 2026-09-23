# Evidence-adjudication index for SX-CERTIFIED-AVERAGED-PID3-001

This file is the current pointer for evidence decisions about the frozen revision-1 claim. It does
not define a claim revision, replace [revision-index.md](revision-index.md), or change any
acceptance rule. The historical revision index remains byte-pinned as part of the original packet
intake. This separate index makes later evidence decisions discoverable without rewriting that
record.

| Claim revision | Decision record | Claim | Decision | Evidence matrix | Complete-target status |
|---:|---:|---|---|---|---|
| 1 | 1 | [claim-v1.md](claim-v1.md) | [decision.md](decision.md) | [evidence-matrix.md](evidence-matrix.md) | Historical proposed specification; no accepted complete-target evidence |
| 1 | 2 | [claim-v1.md](claim-v1.md) | [decision-v2.md](decision-v2.md) | [evidence-matrix-v2.md](evidence-matrix-v2.md) | Historical proposed/open decision; two scoped sub-results receive credit, but Programs A--E remain open |
| 1 | 3 | [claim-v1.md](claim-v1.md) | [decision-v3.md](decision-v3.md) | [evidence-matrix-v3.md](evidence-matrix-v3.md) | Current proposed/open decision; owner-controlled revision-5 source correspondence and exact Fin-3 semantic reconstruction receive scoped credit, two v4 typed-equality false greens are corrected and retained, and Programs A--E remain open |

Decision records 2 and 3 do not create claim revision 2. A change to the frozen mathematical object,
coordinate registry, schema, resource policy, acceptance implication, or permitted complete-target
wording still requires `claim-v2.md` and a new claim revision. Later evidence that instantiates the
unchanged target can receive another numbered decision record without retroactively changing the
historical files.

The `validation.sxpid3-source-marginal-bounded-audit` entry in `method-catalog.json` is the
machine-readable provenance inventory that includes the current record. Its schema does not encode
which numbered decision is current; this evidence-adjudication index is the unambiguous current
pointer. The catalog and its generated `METHODS.md` view do not upgrade the proposed certificate
target or substitute for the claim and evidence records linked above.

## Reviewer identity and current evidence scope — 23 September 2026

The retained [matrix](evidence-matrix-v3.md) calls one source-map entry “owner-controlled human
source correspondence.” That label does **not** establish an identified human reviewer or
independent human review. The [source map](source-correspondence-v4.md) records an integrator-owned
council, disclaims reviewer authentication, and leaves H1 open. The current credit is an
**owner-controlled source-correspondence record plus the stated finite executable checks**.
The inspected records do not establish the reviewer's identity or mode. This clarification does
not assert that no human read the source. Wording such as “human transcription” must likewise not
be used as reviewer-authentication evidence. The historical matrix and decision retain their bytes.

Agents can perform substantive technical review; formal kernels and independently implemented
checks supply evidence for their exact statements and domains. Shared definitions, code, tools
and custody remain shared dependencies. The separate H1 requirement in [the route registry](routes.md)
requires external human custody before claiming independently reproduced public assurance. It is
an assurance condition, not a mathematical premise or a reason to stop technical work. No human
review, external reproduction, new theorem or program closure is granted by this clarification.
