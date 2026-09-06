# Mathematical results guide: current v3 and historical v2

The current 24-page guide passed the complete local exact-mode wrapper on 5 September 2026.
The rebuilt PDF equals the committed candidate byte for byte, with SHA-256
`39db599dca0e33b5f0380417f3faaad4fd1067d592141416728f0931e9016b51`.
The [successful result](local-exact-attempt02.json) and [complete output](local-exact-attempt02.stdout)
record the actual run. Its 62 captured input files remained unchanged during that bounded check.
Current hosted admission remains pending; no old fixture supplies that result.

## Profile and source separation

The current [v3 structure checker](../../../scripts/check-mathematical-results-guide-pdf-structure-v3.py)
binds 24 pages, 57 external targets, 220 navigation records, 67 named destinations, 18 outlines,
1,069 structure elements, 122 ParentTree mappings and 2,278 semantic structure records.
The exact wrapper checks both the retained current PDF and a fresh build, including embedded
fonts, text, link targets, page renders and byte equality. Its normal and optimized self-tests
passed, including 79 structural mutation/control cases and 80 mode controls with 61 hostile
mutations. These counts describe this version of the tests.

The historical hosted-v2 fixture needs the exact older structure source. A later local-v2 source
had replaced that dependency while the hosted checker retained its earlier hash. That mismatch
caused the prior hosted PDF failure; updating only the hash would not restore the old predicates.
The explicit [historical replay adapter](../../../scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-v2-replay.py)
therefore selects the recovered, byte-identical
[hosted-v2 structure source](../../../scripts/check-mathematical-results-guide-pdf-structure-hosted-v2.py).
The original historical checker files and receipts are retained. The old local PDF is separately
preserved as [b5-local-v2.pdf](b5-local-v2.pdf). Neither historical artifact admits the current v3
build. The selected hosted route performs its historical controls, then stops before the current
build with an explicit pending-profile result.

## Corrections and negative evidence

Independent source review found an outer navigation check still expecting 217 records. The current
v3 inventory requires 220. The corrected mode suite includes a causal stale-count mutation.

The first full local exact-mode run then failed because the wrapper still required the obsolete
figure heading “FIRST-ORDER OVERLAP TEST.” Its [failure](local-exact-attempt01.json) and
[diagnostic](local-exact-attempt01.stderr) are retained. An exhaustive text check found that one
missing marker among 55. A preparation assertion initially expected two missing markers and
failed before any tracked edit; the second marker was present and was retained.

The correction replaces the one absent heading with three exact labels already present in the
reviewed figure: its common-radius title, first-order-overlap failure boundary, and explicit
absence of a finite-sample guarantee. All other 54 markers remain unchanged. The preceding
[wrapper source](wrapper-before-current-sentinel-repair.sh) and
[mode suite](mode-suite-before-current-sentinel-repair.py) remain available. Only the current
wrapper binding changed. The successful second run retains all structure and artifact predicates.

## Visual review and limits

Two complementary review passes cover all 24 physical pages in color and grayscale at 120 dpi.
One reviewer inspected pages 1–8 and page 6 at 300 dpi; the coordinator inspected pages 9–24 and
pages 12, 17 and 21 at 300 dpi, with an earlier original-resolution review of page 20. Exact image
bytes and per-review scopes remain in local custody. The coordinator verified all 23 files in the
complementary review manifest. The reviewers share project context and the render producer; this
is not institutional independence.

No blocking clipping, overlap, missing glyph or unreadable equation/table was found. The complete
20-lens visual account separately records hierarchy, typography, grid, spacing, narrative order,
motif provenance and coherence, restraint, palette, pattern semantics, color-independent labels,
grayscale, text extraction, print limits, PDF/fonts, actions, reproduction, source/derived separation,
portable dependencies and declared render scales. Raster observations do not prove machine
properties; the exact wrapper supplies its separately scoped checks. No physical-printer,
PDF/UA-conformance or general viewer-safety claim is made.

This is publication-artifact evidence. It adds no mathematical theorem, estimator calibration,
scientific-novelty or consumer-readiness credit. The workflow publication, current operational
bindings, source-state manifest, commit and exact hosted-main procedure remain separate tasks.
