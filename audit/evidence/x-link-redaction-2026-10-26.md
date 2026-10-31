# Removal of links to posts on X: 26 October 2026

Status: dated custody record. First step 26 October 2026; second step 28 October 2026.

## Purpose

pid-rs does not cite posts on social media, such as X (formerly Twitter), as sources. A post can
be deleted or edited after it is cited, and it can state an opinion as if it were a fact; a reader
or an AI agent that takes such a post as a source can be biased by it, which weakens scientific
rigour. A document therefore states the substance in its own words, says that it came from a
public post and when, and cites the primary source if one exists; it neither links the post nor
names its author. On 26 October 2026 the project owner asked that the existing links be removed
accordingly, including from dated custody records where removal does not break a check. Wording
written by an external reviewer is otherwise preserved.

History is not rewritten. Every observed byte sequence listed below remains in Git at commit
`acf561c0e2bd6724614019acd65c8830246ac5fb`, an ancestor of `main`, so
`git show acf561c0e2bd6724614019acd65c8830246ac5fb:<path> | shasum -a 256` reproduces each observed
digest.

## Files changed in the first step

| Path | Links removed | Observed bytes and SHA-256 | Bytes and SHA-256 after the first step |
|---|---:|---|---|
| `audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.md` | 15 | 97,481; `c289373b23aeb521952101e9143d924b60316ccece6ab9be84c2ff2b9b0ebe71` | 97,725; `1e9bd270df74f8b92991e8cb0b548d5c4677b4e55ee7662b9889a37b06ca6c20` |
| `audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.pdf` | 15 | 185,287; `3cf7457232eb4ba71ac93a1007fea003d61033a2f0caddab2963fa2175bf3fd2` | 303,676; `f1e5bd727dca62086d42e525b402d52385b0ebcc506e59c9ef236198be6c07f8` |
| `audit/review-packets/2026-07-25/mathematical-problem-solving-workflow.pdf` | 10 | 553,199; `b2ec5bed40e5c018aa49ef0c42710d554af55f604193d5c730b424a49af80ac8` | 627,900; `87c75bdfc00fac762f65ef8c39992d911a1dfe39cdc13d35543e96265b38b1d8` |
| `audit/evidence/x-thread-citation-source-manifest.json` | 4 | schema 1; `bc6db3d1d5c5dd8c2b0059280881d041ea1b07b5fd8aabd2d20c953ebed0b907` | schema 2; `1a771a026a7bf86f46cba8f1654e3ab3578347d625c3d12b3cd3de4b52914e1d` |

How each file changed:

- **Audit Markdown.** Each link `[label](URL of a post on X)` became
  `label (public post on X, <day month year, hh:mm UTC>; link removed on 2026-10-26)`. The time is
  decoded from the post identifier, whose upper bits encode its creation time in milliseconds. The
  one link to an image hosted by X became `label (image attached to a post on X on 10 August 2026;
  link removed on 2026-10-26)`. Reversing every replacement reproduces the observed bytes exactly;
  no other byte changed.
- **Audit PDF and review-packet PDF.** The link annotations whose target was a post on X were
  removed with pypdf 6.16.1, and then every object that no other object referenced was dropped:
  the removed annotations; the 13 page annotation arrays of the audit PDF, which the script wrote
  again as direct arrays (4 of those pages lost their links to X, and the other 9 kept the same
  annotations in the same order); and six page-tree nodes of the review-packet PDF that were
  already unreferenced after pypdf copied the file. A scan of every object and every decoded stream of each result finds no
  locator of X, and no reference points to a missing object. The PDF version header, page count,
  page text, document metadata, outline, named destinations, page boxes, content streams and
  every other annotation are unchanged, and every page renders pixel-identically at 60 dpi before
  and after. The files are larger because pypdf writes the objects without object streams.
- **Source manifest.** Schema 2 replaces the `web_locators` entries, each a URL and a post
  identifier, with `public_statements` entries: role, the author's role, platform and posting
  time in UTC. The four statements are, on 24 July 2026: the draft author's original claim
  (14:21:43 UTC), another reader's specific objection (20:50:12 UTC), the draft author's
  acknowledgement (21:27:52 UTC) and correction (21:31:15 UTC). The first step labelled the
  author of the objection `independent reader`; the second step changed the label. The new field `previous_revision` names the schema-1
  digest and the commit that keeps it. The application record names the new manifest digest.

The routes considered and the council lenses are recorded in
[`council.md`](x-link-redaction-2026-10-26/council.md).

The script that derives the first three changes from the observed bytes, with its verification,
is retained as [`redact-milestone-1.py.txt`](x-link-redaction-2026-10-26/redact-milestone-1.py.txt)
(11,759 bytes, SHA-256 `adedf7abfc44909a6caff1ceeb378a40aae5281465c6666dcfd540912e768e7e`). It
reads the observed bytes from commit `acf561c0e2bd6724614019acd65c8830246ac5fb`; with `--check`
it compares its output with the working tree and writes nothing. Two runs give identical bytes.
It is an inert record, not a repository command.

## Correction before integration

The first version of this step, commit `f6f4892e7c2fe0ed9286a0d7d64c638e15821051`, removed the X
link annotations from the pages of both PDFs but kept the annotation objects themselves. No viewer
displayed them, but the link targets stayed in the file bytes: 15 in the audit PDF and 10 in the
review-packet PDF. A scan of every PDF object found this before the step reached `main`. The
corrected script drops the unreferenced objects and runs that scan on its own output; the scan
fails on the first-version files. Those files had 309,419 bytes with SHA-256
`c1514aa745a5d2badd19f820306d5d270c56dc435e9d5d3a6ea1e4586af5d2b1` (audit PDF) and 630,979 bytes
with SHA-256 `4388f44695fa93ea262167c372de41de6c737487aa2cf1e1c43a4f2fb9bfa8fc` (review-packet
PDF), and commit `f6f4892e7c2fe0ed9286a0d7d64c638e15821051` keeps them. The Markdown and the source
manifest were not affected.

## Checks and pins updated with these files

- `scripts/check-citation-edge-countermodel.py` validates schema 2: the closed key sets, the four
  statements by time, role and the author's role, their posting order, and the typed
  `previous_revision`.
  Its self-test adds four controls to the earlier sixteen: a floating-point schema, a Boolean in
  the previous-revision pointer, a reintroduced link field and swapped statement order. Each must
  fail with the message of the check that it targets.
- `scripts/check-markdown-math.py` exempts the audit Markdown by its current digest.
- The review packet's `manifest.sha256` and README list the current PDF digest; the README states
  the change.
- The adjudication record keeps the observed digests in its table and adds a dated note.
- The derived assurance-registry view and the current source-state manifest are regenerated. The
  Lean-freeze map receives current overrides for the changed operational files; the preserved r14
  map is unchanged.

## Files not changed in the first step

- `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`, its embedded copy in
  `audit/formal/latex/mathematical-problem-solving-workflow.tex`, and
  `output/pdf/mathematical-problem-solving-workflow.pdf` (17 links). Changing them requires a new
  publication build and a new page-by-page visual review.
- `audit/evidence/mathematical-workflow-authorship-2026-09-23/previous-source.tex.txt` (17 links)
  and `previous.pdf.bin` (19 link annotations). The current exact gate binds them through the
  5 September 2026 visual review and the authorship check, so they can change only together with
  the workflow publication.

A scan of every object and decoded stream of all 115 tracked PDFs finds locators of X only in
`output/pdf/mathematical-problem-solving-workflow.pdf` and `previous.pdf.bin`: in each, 19 link
annotations for 17 distinct links. The second step, below, removed them.

## Second step: 28 October 2026

The second step removed the remaining links: from the workflow publication and from its two
retained pre-authorship copies. Every observed byte sequence in the table below remains in Git at
commit `6aad6ad020260e57a5e3de18f8b3594cafc67293`, an ancestor of `main`.

| Path | Links removed | Observed bytes and SHA-256 | Bytes and SHA-256 after the second step |
|---|---:|---|---|
| `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md` | 17 | 250,111; `f1cfa3c6a2af48671edce95c469984bd90862fdbb65a4fd9ae32060afaeffac9` | 251,305; `f05845157268f3b875499ea683f2371198d703a99112992d973b0db842ae42a1` |
| `audit/formal/latex/mathematical-problem-solving-workflow.tex` | 17 | 284,086; `6b1298f2b3b99be00b6e8ae8503420e01855db94fef8f30d63971ab5d7efb7b2` | 285,305; `71825f25ebdd561202078c456ec5166dd19516f74edd48bb343ab753b34f2389` |
| `output/pdf/mathematical-problem-solving-workflow.pdf` | 17 | 860,473; `24a394e979d0a9430f10e5999790c6d467c502e2ccf6553cc74e5140fbb10263` | 861,882; `446832ea439c838c6037ba7ad495294f8f07c7916162ff4ac0785bf3f50bed52` |
| `audit/evidence/mathematical-workflow-authorship-2026-09-23/previous-source.tex.txt` | 17 | 284,090; `dd59ded265b42a6854014923e0b81e49a0da79eccd9b2440835c1df0c735bb94` | 284,378; `ee2b858f2ad0f45e358abd0593baf422f4e26ad5589a7d6250571735bd7570c4` |
| `audit/evidence/mathematical-workflow-authorship-2026-09-23/previous.pdf.bin` | 17 | 860,468; `ecfc0c936def223220e6fd4eac79e6a77245c2a1005061d48e669b107774caaf` | 1,018,504; `9b153f0b0800125b283813414192e39d1c92a7b68b634a6ca9daf499e8d2eea9` |
| `audit/evidence/x-thread-citation-source-manifest.json` | 0 | 6,145; `1a771a026a7bf86f46cba8f1654e3ab3578347d625c3d12b3cd3de4b52914e1d` | 6,139; `b21a35401490a47f74c14fc2f8a442aa791311bca0f9ec9696eccb5395fec3da` |

In each PDF, the 17 links had 19 link annotations, because two labels wrapped across lines.

How each file changed:

- **Workflow publication.** The Markdown is the source; the synchronizer copies it into the TeX
  file, and the PDF is built from that file. Each link became a dated description of the post
  that names its author by role only, and a new paragraph states the source policy. The revision
  also applied the two corrections that the
  [research reader and verification contract](../../RESEARCH_READER_AND_VERIFICATION_CONTRACT.md)
  had made by precedence (explicit user pause; category-theoretic claims), added a suggested
  citation, and changed wording that claimed more than the retained record supports, for example
  `another reader` instead of `independent reader`. The new PDF has 87 pages, 91 outline entries
  and 232 named destinations.
- **New visual review.** One AI agent reviewed the new PDF page by page in two sittings on
  28 October 2026: all 87 pages in color and in grayscale at 120 dpi, and 22 detail targets at
  300 dpi, which cover every changed passage and every figure (the figures in both modes). The
  [receipt](mathematical-workflow-visual-receipt-2026-10-28.md) and its
  [actual-view records](mathematical-workflow-visual-review-2026-10-28/actual-views.json) list 196
  views and 2 superseded views of page 59. The exact gate checks each page view against the digest
  of its render in the rendering receipt, renders the 22 detail targets again from the committed
  PDF and compares their digests. Before this step was committed, that comparison found that the
  record of the page-59 target named a box that started 2 pixels further left, and was 2 pixels
  wider, than the image that had been viewed: the box had been computed again after the last
  rebuild, but the image had not been rendered again. The record was corrected to the box that was
  rendered and viewed (x 371, y 478, 1,852 by 421 pixels at 300 dpi), which contains the whole
  passage.
- **Retired evidence chain.** The PDF content changed, so the 5 September 2026 visual review and
  the authorship-only check no longer bind the current PDF, and the exact gate no longer reads the
  pre-authorship copies. `scripts/check-workflow-publication-history.py` keeps the retired chain
  verifiable. It checks the 21 file entries of the authorship receipt against their Git blobs at
  the merge that introduced the receipt (`b5afd1b9580538f31b161201b80afeb12ae194cb`) and at the
  last commit before this step (`6aad6ad020260e57a5e3de18f8b3594cafc67293`), checks that the two
  receipt files in the tree are unchanged, and runs the historical visual-receipt validator,
  extracted from the pinned checker blob, on the historical blobs. With `--authorship-replay` it
  also replays the authorship-only check, which needs Poppler. The receipt `SUCCESSOR-v2.json` is
  unchanged; its entries for the two redacted copies now describe their historical blobs, not the
  current files.
- **Pre-authorship copies.** They received the treatment of the first step, with
  `link removed on 2026-10-28`. In the TeX copy, 16 links to posts and one link to an image hosted
  by X were replaced; reversing every replacement reproduces the observed bytes. In the PDF copy,
  the 19 link annotations were removed and 57 unreferenced objects were dropped: the 19
  annotations, the 29 page annotation arrays (the script writes every page annotation array again
  as a direct array; 24 of those pages kept the same annotations in the same order), and 9
  page-tree nodes that pypdf's copy no longer referenced. The fidelity checks of the first step
  pass: page count, page text, renders at 60 dpi, outline, named destinations, document
  information, PDF version header and every other annotation are unchanged. The script is retained
  as [`redact-milestone-2.py.txt`](x-link-redaction-2026-10-26/redact-milestone-2.py.txt) (11,280
  bytes, SHA-256 `d62310aec4600c90696968357e0e8f763f3d9cddc5e2edc1fe54323b437516eb`). It reads the
  observed bytes from commit `6aad6ad020260e57a5e3de18f8b3594cafc67293`; with `--check` it
  compares its output with the working tree and writes nothing. Two runs give identical bytes. It
  is an inert record, not a repository command.
- **Source manifest.** The author label of the objection changed from `independent reader` to
  `other reader`, because the retained record does not establish that reader's independence. The
  application record and `scripts/check-citation-edge-countermodel.py` name the new digest.

After the second step, a text scan of every tracked file and a scan of every object and decoded
stream of all 115 tracked PDFs find no locator of X.

## Checks and pins updated in the second step

- `scripts/check-mathematical-workflow-pdf.sh` validates the new receipt and its records in exact
  and cross-toolchain mode; only the exact mode compares the detail-target digests with new
  renders. Its self-test adds 150 controls for the new records in exact mode (148 in
  cross-toolchain mode) and retires the four split-review controls of the old receipt.
- `scripts/check-workflow-publication-history.py` and its self-test (18 controls) are new.
- `scripts/check-certified-sxpid2-claim.py` rebinds its whole-file digests of
  `.github/workflows/ci.yml`, which gains the four history-check steps in the release-scope job,
  and of `scripts/README.md`, whose workflow paragraphs change. Its digest of the certified-SxPID
  job segment is unchanged.
- `scripts/check-zeta-pid-transfer-firewall.py` binds the digest of the workflow's zeta source
  section, and its self-test binds that digest and the checker's canonical output. The section
  changed only where its four post links and one reply link became dated descriptions; every
  mathematical sentence the firewall checks is unchanged. Both pins are rebound. This pin was missed
  at first, because the search for pins looked only for whole-file digests; hosted CI on the first
  push of this step (commit `fecc938`) found it before `main` moved.
- The Lean-freeze map receives current overrides for the changed operational files, including both
  zeta firewall scripts, and binds the new receipt and records; the preserved r14 map is unchanged. The derived assurance-registry view
  needs no change. The current source-state manifest is regenerated last.
- `AGENTS.md`, `CLAUDE.md`, the session handoff and the reader contract no longer describe the
  workflow update as open.

## Boundaries

This record changes no theorem, estimator, numerical result or evidence class. Removing a link does
not correct, endorse or dispute the content of the post. A digest identifies bytes; it does not
authenticate them.
