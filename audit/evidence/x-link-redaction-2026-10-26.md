# Removal of links to posts on X: 26 October 2026

Status: dated custody record.

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

| Path | Links removed | Observed bytes and SHA-256 | Current bytes and SHA-256 |
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
  the removed annotations, the page annotation arrays that had listed them (13 in the audit PDF),
  and six page-tree nodes of the review-packet PDF that were already unreferenced after pypdf
  copied the file. A scan of every object and every decoded stream of each result finds no
  locator of X, and no reference points to a missing object. The PDF version header, page count,
  page text, document metadata, outline, named destinations, page boxes, content streams and
  every other annotation are unchanged, and every page renders pixel-identically at 60 dpi before
  and after. The files are larger because pypdf writes the objects without object streams.
- **Source manifest.** Schema 2 replaces the `web_locators` entries, each a URL and a post
  identifier, with `public_statements` entries: role, the author's role, platform and posting
  time in UTC. The four statements are, on 24 July 2026: the draft author's original claim
  (14:21:43 UTC), an independent reader's specific objection (20:50:12 UTC), the draft author's
  acknowledgement (21:27:52 UTC) and correction (21:31:15 UTC). The new field `previous_revision` names the schema-1
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
annotations for 17 distinct links.

## Boundaries

This record changes no theorem, estimator, numerical result or evidence class. Removing a link does
not correct, endorse or dispute the content of the post. A digest identifies bytes; it does not
authenticate them.
