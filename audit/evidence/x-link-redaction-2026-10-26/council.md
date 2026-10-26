# Route comparison and council: removing links to posts on X

Decision record for [the redaction](../x-link-redaction-2026-10-26.md), 26 October 2026. The
review was carried out by one AI agent at the owner's request; every lens below is an advisory,
same-system pass, not human or independent review. The checks named in the evidence column were
run and inspected.

## Routes

| Route | Assessment |
|---|---|
| R0 No action | Rejected: contradicts the owner's instruction that public repositories cite no posts on X. |
| R1 Policy only, keep existing links | Rejected as a full answer: the owner also asked for removal from dated custody where possible. Kept as the rule for new text. |
| R2 Edit the workflow Markdown only | Rejected: the exact gate requires the Markdown, the embedded TeX copy and the PDF to agree. |
| R3 Edit Markdown and TeX without a new PDF | Rejected: the exact PDF gate and its link inventory would fail. |
| R4 Replace links with web-archive copies | Rejected: still cites the posts. |
| R5 Move the records to private storage, keep digests only | Rejected: the observed bytes would leave public custody, and a digest alone gives no recovery. |
| R6 Rewrite Git history | Rejected: breaks every recorded commit, receipt and remote reference. |
| R7 Delete the case studies that cite posts | Rejected: loses retained process evidence and negative results. |
| R8 Redact current files, keep observed bytes in history, re-pin only current registries | **Selected** for files whose pins live in editable current records. |
| R9 Same as R8 for files bound by the current exact visual review | **Deferred** to the workflow republication: the 5 September review and the authorship check bind those bytes. |
| R10 Defer everything to the next complete workflow publication | Rejected as a full answer: delays removal that can be done safely now. |

## Council lenses

| # | Lens | Finding and disposition |
|---:|---|---|
| 1 | Owner intent | Links removed where no check depends on them; remaining files are listed with the reason. |
| 2 | Self-containedness | Each removed link is replaced by its date and what the post was; primary sources stay cited. |
| 3 | Preservation of observed bytes | All observed bytes remain at commit `acf561c0`; the record gives the retrieval command. |
| 4 | No history rewrite | Only the current tree changes. |
| 5 | Pin completeness | Every exact-digest pin of each changed file was searched; each is updated or recorded as historical. |
| 6 | Preserved r14 map | Unchanged; current overrides only, as AGENTS.md requires. |
| 7 | Current-map rebind | Freeze check passes in normal and optimized Python. |
| 8 | Reviewed-documentation pin | The certified-claim pin of the scripts guide moves for one changed paragraph, named in the record. |
| 9 | Typed equality | Schema and previous-revision checks compare exact type and value; Boolean and float coercions are tested. |
| 10 | Causal controls | The four new mutations must fail with the message of their own check. |
| 11 | Documentation coherence | The scripts guide states the new control count and schema. |
| 12 | Render fidelity | Every page of both PDFs renders pixel-identically at 60 dpi before and after. |
| 13 | Metadata fidelity | PDF header, producer and document information unchanged. |
| 14 | Text fidelity | `pdftotext` output identical for every page. |
| 15 | Annotation inventory | All non-X annotations preserved in order. |
| 16 | File size | Larger without object streams; no reader-visible effect. Accepted. |
| 17 | Markdown exactness | Reversing every replacement reproduces the observed bytes. |
| 18 | Time decoding | Post identifiers decode with the published epoch offset; the times match the narrated order of the exchange. |
| 19 | Attribution | The authors of posts appear by role only: no names, handles or links. |
| 20 | No new content claims | The text says what kind of post each was, not more than the retained record. |
| 21 | Personal data | No new names or handles are introduced; handles were removed. |
| 22 | Platform naming | "X (formerly Twitter)" once, then "X". |
| 23 | Packet retrieval | The packet's immutable commit URLs keep serving the reviewed bytes. |
| 24 | Packet manifest | `shasum -c` passes for all ten entries; the README copy matches. |
| 25 | Adjudication coherence | Table keeps observed digests; a dated note points to the record. |
| 26 | Derived view | The typed assurance view was regenerated, not edited; its self-test passes. |
| 27 | Ordering | The source-state manifest is regenerated last. |
| 28 | Hosted preflight | CI is dispatched on the side branch before `main` moves. |
| 29 | Cross-toolchain scope | No formal-PDF-set member changes in this step. |
| 30 | Link graph | The publication-link check runs on the changed Markdown. |
| 31 | Math exemption | The external audit keeps its observed math syntax under the new digest. |
| 32 | Scope | The workflow publication is deferred with a stated reason, not silently skipped. |
| 33 | Reversibility | One revert restores every changed file. |
| 34 | Reproducibility | The redaction script and pypdf version are retained; the script derives the current files from the observed bytes and reproduces them exactly. |
| 35 | Tool trust | pypdf 6.16.1 is installed from the repository's hash-pinned requirement. |
| 36 | Negative evidence | The schema-1 manifest stays retrievable through `previous_revision`. |
| 37 | Reader comprehension | The record explains the change without assuming knowledge of PDF internals. |
| 38 | Tone | Professional and claim-centered; no evaluation of the posts' authors. |
| 39 | AI-process honesty | The record states that an AI agent made and reviewed the change. |
| 40 | Independence | All checks share one system and one session; agreement is correlated. |
| 41 | Dissent: immutability | Preserved evidence is meant to stay byte-for-byte. Retained objection; the owner's instruction and history-preserving redaction outweigh it, and the observed bytes stay retrievable. |
| 42 | Dissent: falsification | A changed dated PDF could look like an altered record. Mitigated: the record, the note and the digests state exactly what changed. |
| 43 | Third-party material | Only link annotations of repository-held copies change; no content is rewritten. |
| 44 | Accessibility | Navigation links to X are gone; the dates make each post findable by other means. |
| 45 | Future policy | New text cites no social-media posts, because posts can be deleted or edited and can present opinions as facts that bias readers and AI agents; AGENTS.md states the rule. |
| 46 | Thesis separation | The policy applies to public repositories; other documents are unaffected. |
| 47 | Shallow clones | Verifying observed bytes needs a clone with history; the record says how. |
| 48 | Inventory completeness | Text files were scanned for links to X, and all 115 tracked PDFs at object level, including decoded streams. |
| 49 | Remaining work | The workflow publication and its pre-authorship copies are listed. |
| 50 | Failure handling | Any failed gate stops the step before `main`; nothing is forced. |
| 51 | Byte-level completeness | Removing an annotation from a page kept its object in the file, so the first version left the link targets in the bytes. Found by an object-level scan before `main` moved; the corrected script drops unreferenced objects and fails if any object or decoded stream still holds a locator of X. |
