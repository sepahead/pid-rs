# PID discovery, verification, and durability blueprint visual-review receipt

schema: `pid-rs/pid-discovery-verification-durability-blueprint-visual-review/v1`
subject: `PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf`
source: `PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md`
source_bytes: `115793`
source_sha256: `8b446accb257531dbf219670a39c8f1e4b794671bb85ff06f3992bdcdfd5e9c1`
pdf_sha256: `b82c5a0a400ccb129195c3db6e765c7861605f84710226cedd01246967cca7d7`
pages: `31`
color_120_dpi_pages_rendered: `1-31`
color_120_dpi_pages_reviewed: `1-31`
grayscale_120_dpi_pages_rendered: `1-31`
grayscale_120_dpi_pages_reviewed: `1-31`
spot_300_dpi_pages_reviewed: `1,3,9,12,14-20,22-24,26-28,30-31`
delta_reference_pdf_sha256: `18d034deb7f131e8e93170f4dd064980ab9f40cbdda208b512dbf68a58af3a0a`
delta_reference_pages: `29`
delta_120_dpi_raster_identical_pages: `none`
delta_120_dpi_changed_or_added_pages_reviewed: `1-31`
lens_count: `20`
status: `passed`
review_date_utc: `2026-09-05`
reviewer_kind: `agent-visual-inspection`

The current receipt supersedes the [preserved 30-page receipt](../archive/blueprint-visual-receipt-20260905/DISPOSITION.md).
The prior bytes remain available with their limitations. This record reports fresh observations.

All 31 pages of the exact PDF above were rendered at 120 dpi. The primary reviewer inspected
six contact sheets in page order for color and six for grayscale. The 300-dpi inspection used
individual images for physical pages `1,3,9,12,14-20,22-24,26-28,30-31` (19 pages). A second
reviewer inspected pages `1,3,9,12,14-20,22`; the primary reviewer inspected pages
`23,24,26-28,30-31`. These reviewers share the environment and model system. Their divided
inspection gives no external or dependency-disjoint review credit. All page scopes use physical
PDF page numbers, including the cover.

The high-resolution set covers the title and contents, historical review tables, the current
Program-A evidence, transfer figures, equations and assumptions, the 108-expression taxonomy,
proposed semantic representation, attack matrix, council controls, retirement process, roadmap,
and references. The all-page review used contact sheets, not a claim of individual full-size
inspection of every page. The second reviewer also inspected individual 120-dpi color and
grayscale images of pages 9 and 22 after a high-resolution display suggested text collisions.

Those suspected collisions were false visual alarms. PDF word coordinates show positive gaps:
page 9 has about 16.82 pt and 14.96 pt between the questioned columns; page 22 has about 24.43 pt
and 16.44 pt. The questioned sentence space measures 4.42 pt. The individual 120-dpi images also
show the gaps. No layout edit was made on that basis. The [verifier review](verifier-publication-council-2026-09-05.md)
retains the observations, the retraction, and its evidence. The cover's stretched title spacing
was judged cosmetic; no clipping or unreadable text was found.

The accepted 29-page PDF above is the comparison reference recovered from main at
`e1a6648ccace699e41b4ffa48c6acd79209a7418`. It is not the interrupted 30-page working edition.
Both the reference and current PDF were rendered with the same 120-dpi renderer. None of the
first 29 page rasters is byte-identical; pages 30 and 31 are added. Every current page therefore
received the fresh contact-sheet review. The current edition adds the Program-A correspondence,
finite reconstruction, typed-equality failure account, and checkout-integrity incident. Reflow
adds two pages relative to the accepted reference. The visible edition date remains 3 September.

The current builder completed two isolated same-toolchain builds on 5 September. Both produced
31-page PDFs with SHA-256 `b82c5a0a400ccb129195c3db6e765c7861605f84710226cedd01246967cca7d7`,
identical to the inspected committed-path PDF. This is bounded deterministic reproduction on the
available toolchain. The exact publication gate separately checks annotations, actions, fonts,
metadata, page count, source identities, and byte equality. Its execution result belongs to the
[milestone record](documentation-verifier-milestone-2026-09-05.md), not to visual inspection.

The inherited repairs remain scientific nonpromotions. The [typed-equality failure record](../../claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/python-status-type-coercion.md)
preserves four numerical-type false positives. The [checkout-integrity incident](sxpid3-pdf-checkout-integrity-incident-2026-09-04.md)
retains an unresolved cause and the limits of the resulting builder defenses. Program A remains
partial/open, and Programs A--E closed remains 0 of 5. The PDF maps declared repository links to
canonical main targets. Remote destination availability requires a separate post-publication
observation and receives no credit from this receipt.

## Named review lenses and outcomes

| # | Lens | Inspected evidence | Outcome |
|---:|---|---|---|
| 1 | Hierarchy | Title, contents, sections 1-23, subordinate headings, captions, tables, warnings | Passed: current status, dated history, proposal, and evidence boundaries remain visibly distinct |
| 2 | Typography | Body, headings, monospaced text, symbols, formulas, and SVG labels | Passed: no missing glyph, black square, unintended fallback, or unreadable label was observed |
| 3 | Grid | Margins, columns, tables, displays, code blocks, and Figures 1-4 | Passed: no rule, label, equation, table, or figure crosses its layout boundary |
| 4 | Spacing and rhythm | Dense review tables, equations, lists, section transitions, and references | Passed: no orphan heading, collision, clipped line, or accidental blank interior page was observed |
| 5 | Narrative order | Scope, dated audits, evidence delta, transfer rules, PID target, assurance, process, roadmap, references | Passed: the 31-page sequence is coherent and contains no duplicated or transposed page |
| 6 | Edition chronology | Title date, dated reviews, decision pointers, safety boundary, and every footer | Passed: 3 September is current; 19 August, 1 September, and 2 September material stays explicitly historical |
| 7 | Current-status truth | Opening, evidence delta, figure text, roadmap, and final recommendation | Passed after correction: decision-v3 is current, Program A is partial/open, and Programs closed is 0/5 |
| 8 | Semantic nonconflation | PrimeGaps/PID firewall, PID-family exclusions, categorical/continuous boundary, and baseline/DAG split | Passed: structure transfers are separated from mathematical conclusions and from other PID estimands |
| 9 | Assumption visibility | Categorical alphabets, positive counts, support, units, empirical estimand, and bounded binary domain | Passed: equations and bounded claims retain their declared domains and nonclaims |
| 10 | Coordinate ontology | 18 carrier positions, 54 cumulative, 54 atom, 108 keyed expressions, and separate 166-node carrier | Passed: expressions are not relabeled as atoms, nodes, laws, or independent parameters |
| 11 | Motif coherence and restraint | Rosette field, paper grain, hatch/dot cards, numbered stages, arrows, and warning bands | Passed: one restrained grammar is used and decoration carries no claim or magnitude |
| 12 | Color-redundant labeling | Panel titles, stages, paths, borders, patterns, captions, and warning text | Passed: every stage, path, distinction, and warning remains identifiable without hue |
| 13 | Grayscale legibility | All 31 grayscale pages, including all figures and dense tables | Passed: hierarchy, labels, patterns, formulas, and warnings remain distinguishable |
| 14 | Searchability and extraction | Contents, headings, prose, tables, equations, code, captions, and references | Passed within the untagged-PDF boundary; no PDF/UA or assistive-technology claim is made |
| 15 | Print-preview fidelity | A4 color/grayscale renders, fine rules, formulas, tables, and figure labels | Passed as a digital preview; no physical press or device calibration is claimed |
| 16 | Durability chronology | Mainline/archive split, removal eligibility, bounded removal, post-removal inventory, retrieval, and later GC | Passed after correction: no postcondition is presented as a precondition and no archive path inherits false mainline credit |
| 17 | Link/action safety | Canonical source links, PDF annotations, internal navigation, and declared HTTPS mappings | Separate exact-gate evidence is required; remote destination availability remains explicitly unclaimed |
| 18 | Deterministic reproduction | Two isolated builder runs, metadata epoch, page count, and byte comparison | Passed for one same-toolchain relation; no cross-toolchain equivalence is claimed |
| 19 | Source/derivative separation | Markdown, header, filter, SVG sources, derived PDF, relative Markdown links, and declared PDF mappings | Passed: editable sources remain separate from derivatives and no private filesystem locator is embedded |
| 20 | Normal-size and high-resolution inspection | All-page 120-dpi color/grayscale contact sheets plus the declared individual 300-dpi spot set | Passed: no clipping, overlap, occluded caption, broken table, corrupt raster, or figure-scaling defect remains |

## Bounded conclusion

No blank, clipped, overlapping, misordered, or visibly corrupt page remains. The title, dense
review tables, formulas, code blocks, captions, and four handcrafted SVG panels are legible in the
declared color, grayscale, and high-resolution inspections. The current-state separation,
baseline-versus-DAG distinction, and retirement chronology were corrected before this receipt.

This receipt binds one exact 31-page PDF byte string to one bounded visual inspection. It is not a
proof of mathematical correctness, source correspondence, semantic completeness, PDF/UA or other
accessibility conformance, external-link availability, publisher authenticity, cross-toolchain
equivalence, or independent review. The page renders and contact sheets are disposable inspection
intermediates and are not evidence artifacts. No dependency-disjoint second-review credit is
claimed.
