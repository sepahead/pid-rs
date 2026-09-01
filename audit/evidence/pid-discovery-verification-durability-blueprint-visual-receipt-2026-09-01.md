# PID discovery, verification, and durability blueprint visual-review receipt

schema: `pid-rs/pid-discovery-verification-durability-blueprint-visual-review/v1`
subject: `PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf`
pdf_sha256: `51a5d399cdcddbdf0ae4aea13a0d5726b79c8e81b417f845e0968b7e310e3d27`
pages: `28`
color_120_dpi_pages_rendered: `1-28`
color_120_dpi_pages_reviewed: `1-28`
grayscale_120_dpi_pages_rendered: `1-28`
grayscale_120_dpi_pages_reviewed: `1-28`
spot_300_dpi_pages_reviewed: `1,4,10-13,15-17,19,24,26-28`
delta_reference_pdf_sha256: `42cc33bb8d3f12128fc8c8f56e07b31d2817a709389c27bc9871376b1a1ea116`
delta_reference_pages: `27`
delta_120_dpi_raster_identical_pages: `9`
delta_120_dpi_changed_or_added_pages_reviewed: `1-8,10-28`
lens_count: `20`
status: `passed`
review_date_utc: `2026-09-01`
reviewer_kind: `agent-visual-inspection`

All 28 color pages and all 28 grayscale pages were rendered at 120 dpi and reviewed in page order.
Against the earlier accepted 27-page byte string identified above, page 9 was byte-identical as a
120 dpi color raster and as a 120 dpi grayscale raster. Pages 1-8 and 10-28 changed or were added;
each was inspected in both render modes. Pages 1, 4, 10-13, 15-17, 19, 24, 26, 27, and 28 were also
rendered and reviewed at 300 dpi. This spot set covers the title, publication contract, the complete
20-row mandatory-core and 50-row additional-lens matrices, the separate 10-route comparison, both
transfer-firewall figures, the mathematical target and negative witness, the layered assurance/D1
boundary, both durable-promotion figures, the remote-state wording, the roadmap, final
recommendation, source-anchored claim register, and references.

The first current-source render exposed one semantic wording defect in Figure 2: `source-blind`
could be read as dispensing with the primary source, while the method actually excludes generated
answer tables. The SVG was corrected to `Generated-answer-blind`. A deterministic corrective rebuild
changed only page 15 in both 120 dpi raster modes; that page was rerendered, reviewed in color and
grayscale, and included in the 300 dpi set. No remaining visual defect was observed.

## Named review lenses and outcomes

| # | Lens | Inspected evidence | Outcome |
|---:|---|---|---|
| 1 | Hierarchy | Title, running heads, sections 1-22, subordinate headings, captions, tables, and warnings | Passed: title, section, subsection, body, caption, and boundary levels remain distinct and consistently ordered |
| 2 | Typography | Body, heading, monospaced, and mathematical faces at 120 and 300 dpi | Passed: no missing glyph, replacement character, black square, unintended fallback, damaged symbol, or unreadable small label was observed |
| 3 | Grid | Page edges, text columns, full-width tables, mathematical displays, code blocks, and Figures 1-4 | Passed: columns, rules, wraps, panels, captions, and aligned displays remain on a consistent page grid without collision |
| 4 | Spacing/rhythm | Dense prose, lists, equations, captions, section transitions, and the intentionally open reference close | Passed: measure, leading, paragraph gaps, and transition space support reading; no isolated heading or accidental void was observed |
| 5 | Narrative order | Two-page contents, executive decision, source audit, historical transfer council, current 70-lens closure, separate 10-route comparison, SxPID3 target, assurance architecture, durability process, roadmap, recommendation, and references | Passed: the page sequence moves from scope and source meaning to bounded transfer and implementation; no missing, duplicated, or transposed page was observed |
| 6 | Motif provenance | Repository-local publication header and four declared SVG source panels | Passed at the public repository boundary: the rendered motifs correspond to the reviewed repository-local assets; no private locator or external design-runtime dependency appears in the artifact |
| 7 | Motif coherence | Title rosette field, figure paper grain, hatch/dot cards, numbered circles, arrows, and warning bands | Passed: geometric and material motifs use one restrained grammar across the title and four figures |
| 8 | Ornamental restraint | Page 1 pattern/fade and the patterned figure backgrounds/cards | Passed: ornament stays below text and diagram structure, does not obscure labels, and does not compete with the mathematical narrative |
| 9 | Palette identity | Lapis, turquoise, ink, mineral, ivory, saffron, and pomegranate roles | Passed: the declared publication colors keep stable roles across title, headings, rules, diagrams, and warning bands |
| 10 | Pattern/data-semantic separation | Rosette, grain, hatch, dot, and line patterns against all status, count, and claim statements | Passed: decoration carries no mathematical status, table value, probability, or graph magnitude; every load-bearing distinction is textual or structural |
| 11 | Color-redundant labels | Numbered stages, arrows, panel titles, captions, borders, hatch/dot patterns, and explicit warning text | Passed: source/target, stage, path, and warning distinctions remain identified without relying on hue alone |
| 12 | Grayscale legibility | All 28 grayscale pages, including all four figures and the dense lens, route, and failure tables | Passed: hierarchy, labels, patterns, mathematical notation, and warning bands remain distinguishable in grayscale |
| 13 | Real-text searchability and logical extraction order | Poppler extraction, contents, headings, prose, tables, equations, code blocks, figure captions, and references | Passed within the declared untagged-PDF boundary: searchable text and page-order extraction remain coherent and expose no raw TeX or replacement glyph; no PDF/UA or assistive-technology reading-order claim is made |
| 14 | Print fidelity | A4 color and grayscale page renders, fine rules, body text, mathematical notation, and figure labels | Passed as a digital print-preview check: all pages retain readable contrast and line weight at 120 dpi, with high-risk pages confirmed at 300 dpi; no physical press or device calibration is claimed |
| 15 | A4/PDF profile and embedded fonts | PDF metadata/profile plus every rendered page and font roster | Passed: 28 A4 pages, PDF 1.7, no forms, JavaScript, encryption, or tagged-structure claim, with all used fonts embedded and Unicode-mapped |
| 16 | Link/action safety | Catalog opening view, outline and internal navigation, declared HTTPS annotations, and deep reachable objects | Passed by the exact structural gate: only the intended first-page catalog GoTo, registered named internal GoTo owners, and declared HTTPS link-annotation URIs are admitted; this does not prove external availability or destination content |
| 17 | Deterministic reproduction | Two isolated builder runs and the exact committed-PDF rebuild comparison | Passed for the declared same-toolchain relation: both builds and the committed artifact have SHA-256 `51a5d399cdcddbdf0ae4aea13a0d5726b79c8e81b417f845e0968b7e310e3d27`; no cross-toolchain equivalence is claimed |
| 18 | Source/derived-asset separation | Canonical Markdown, header, Lua filter, four SVG sources, their rendered intermediates, and the final PDF | Passed: human-editable sources remain distinct from disposable renderer products and the derived PDF; the exact gate rebuilds from the declared source roster |
| 19 | Portable repository-local dependencies | Relative Markdown evidence links, declared main-branch PDF navigation mappings, repository-local TeX/SVG assets, and absence of private locators | Passed at the repository layer: publication assets and evidence paths are portable within a checkout; separately installed build tools remain a declared same-toolchain dependency, not a portability theorem |
| 20 | Normal-size plus high-resolution rendered inspection | Every page at 120 dpi in color and grayscale plus pages 1, 4, 10-13, 15-17, 19, 24, and 26-28 at 300 dpi | Passed after one source correction and rerender: no clipped line, overlap, occluded caption, broken table, doubled suffix, blank interior page, visibly corrupt raster, or figure-scaling defect remains |

## Bounded conclusion

No blank, clipped, overlapping, misordered, or visibly corrupt page remains. The title, tables,
mathematical displays, code blocks, captions, and all four handcrafted SVG panels remained legible in
the declared color, grayscale, and high-resolution inspections. The generated-answer-blind wording
correction above was the only source change caused by this visual review.

This receipt binds one exact 28-page PDF byte string to one bounded visual inspection. It is not a
proof of mathematical correctness, source correspondence, semantic completeness, PDF/UA or other
accessibility conformance, external-link availability, publisher authenticity, cross-toolchain
equivalence, or independent review. The page renders are disposable inspection intermediates and are
not evidence artifacts. No dependency-disjoint second-review credit is claimed.
