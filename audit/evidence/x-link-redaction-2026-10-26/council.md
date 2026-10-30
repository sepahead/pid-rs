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
| 46 | Policy scope | The policy applies to public repositories; other documents are unaffected. |
| 47 | Shallow clones | Verifying observed bytes needs a clone with history; the record says how. |
| 48 | Inventory completeness | Text files were scanned for links to X, and all 115 tracked PDFs at object level, including decoded streams. |
| 49 | Remaining work | The workflow publication and its pre-authorship copies are listed. |
| 50 | Failure handling | Any failed gate stops the step before `main`; nothing is forced. |
| 51 | Byte-level completeness | Removing an annotation from a page kept its object in the file, so the first version left the link targets in the bytes. Found by an object-level scan before `main` moved; the corrected script drops unreferenced objects and fails if any object or decoded stream still holds a locator of X. |

## Second step: 28 October 2026

The second step removed the links from the workflow publication and its two pre-authorship
copies. One AI agent made and adjudicated the change. A coding agent of another vendor (OpenAI
Codex) reviewed the plan as one advisory council member and wrote three candidate implementations
of the new receipt validation from the same written specification. Every lens below is advisory;
the checks named in it were run and inspected.

### Routes

| Route | Assessment |
|---|---|
| S0 No action | Rejected: a current publication would keep 17 links to posts. |
| S1 New PDF; keep the 5 September review through a delta check | Rejected: the content changed, so a delta check would have to judge content; a new review is the direct evidence. |
| S2 Review only the changed pages; transfer the old review for the others | Rejected: one review would then cover two PDFs. The receipt binds one review to one PDF. |
| S3 New PDF, new complete review bound to it, Git-bound check of the retired chain | **Selected.** |
| S4 Keep the pre-authorship copies unchanged | Rejected: once the gate no longer reads them, link removal breaks no check, and the owner asked for it. |
| S5 Delete the pre-authorship copies | Rejected: removes retained custody that nobody asked to remove. |
| S6 Reword the copies to role-only text, as in the new publication | Rejected, dissent retained: it would change the historical wording, not only the links. Link-only redaction matches the first step. |
| S7 Add retrieval notices next to the redacted copies | Rejected: the record already gives the commit and the retrieval command. |
| S8 Keep the authorship-only check, pinned to the redacted copies | Rejected: the check would then attest bytes that were never the published predecessor. |
| S9 Rewrite Git history | Rejected: as in the first step. |

### Validator candidates

The three candidates differ in design, not in their written contract. Each passed its own full
self-test on this host (572, 529 and 541 controls). Candidate 1 was selected: it requires the
complete receipt to be canonical bytes, renders the 22 detail targets in both modes (so a failing
or noisy renderer fails in both), runs the validation in the same clean environment as the page
renders, and has the widest set of controls. Candidate 2 builds a local copy whose digests are
bound to new renders, so the exact comparison is tested on every toolchain; this is retained as a
possible improvement. Candidate 3 has explicit type controls for each integer field. The two
unselected candidates are not retained in the repository; the selection carries no scientific or
selection credit.

### Council lenses

| # | Lens | Finding and disposition |
|---:|---|---|
| 1 | Owner intent | All remaining links to posts are removed; the scans find none. |
| 2 | Self-containedness | The workflow describes each post by date and role and cites the primary sources. |
| 3 | Subject binding | The receipt binds the review to the exact PDF and rendering-receipt digests. |
| 4 | Review honesty | One AI agent, two sittings, self-reported times; no independent or human review is claimed. |
| 5 | Single-page views | Each page view must carry the digest of its own render in the rendering receipt. |
| 6 | Detail targets | A closed roster of 22 boxes; the exact mode renders them again and compares digests. |
| 7 | Portability | The cross-toolchain mode skips only the crop-digest comparison. |
| 8 | Outcomes | A view is clear or advisory; a blocker outcome fails the gate. |
| 9 | Typed records | Exact types; Boolean and floating-point values fail where an integer is required. |
| 10 | Causal controls | Each mutation must fail with the message of its own rule, in normal and optimized Python. |
| 11 | Fixture drift | The candidates were written against a one-sitting fixture. Five mutations assumed it and were rewritten for the final records: overlapping sittings, sitting count, undeclared sitting, the review-date shift, and decreasing times, where several records share one second. |
| 12 | False positive | The selected drive-letter rule matched `https://`. A drive letter must now start a token; two controls cover a URL and a Windows path. |
| 13 | Record versus image | The exact comparison found that the page-59 record named a box that had been computed again after the last rebuild, while the image had not been rendered again. The record now names the rendered box. |
| 14 | Retired chain | The history check reads Git blobs; the two receipt files in the tree are unchanged. |
| 15 | Copy fidelity | The first-step checks pass for both redacted copies; an object-level scan finds no locator of X. |
| 16 | Array disclosure | The script writes every page annotation array again. The first-step description of the dropped arrays is corrected. |
| 17 | Role label | `independent reader` became `other reader`; nothing retained establishes independence. |
| 18 | Date label | The PDF says `revised 26 October 2026`, when the revision began; the receipt gives the review date. Accepted. |
| 19 | Environment | Under `HOME=/nonexistent`, the self-test fails on this host before and after the change, because LuaTeX's font loader needs a writable cache. The dedicated recipe sets no `HOME` and passes. The historical recipe that sets it is closed and unchanged. |
| 20 | Independence | The candidates share one model and one specification, and the adjudicator wrote that specification; agreement among them is correlated. |
| 21 | Ordering | Pins are rebound after every byte is final; the source-state manifest is generated last. |
| 22 | Hosted preflight | CI runs on the side branch before `main` moves. |
