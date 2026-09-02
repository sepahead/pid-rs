# Post-publication custody PDF visual-review receipt

schema: `pid-rs/post-publication-custody-visual-review/v1`
subject: `output/pdf/post-publication-custody-2026-09-02.pdf`
pdf_sha256: `d122cec2e2f77cf613a00d28601161cc75a28a93f777700e7919afb4f5fb8550`
pages: `6`
color_144_dpi_pages_rendered: `1-6`
color_144_dpi_pages_reviewed: `1-6`
grayscale_120_dpi_pages_rendered: `1-6`
grayscale_120_dpi_pages_reviewed: `1-6`
lens_count: `20`
status: `passed`
review_date_utc: `2026-09-02`
reviewer_kind: `agent-visual-inspection`

All six pages of the exact PDF identified above were rendered and reviewed in page order: color at
144 dpi and grayscale at 120 dpi. The review covered the patterned title page and custody state
machine, the publication anchor, direct remote-head snapshot, nine named retired refs, hosted-run
census, three retired worktrees, local reconciliation, private dirty-lane preservation boundary,
retained state, nonclaims, and the disposition tied to the blueprint's named 70-row council. Long Git object IDs and SHA-256
values wrap without clipping. Page 6 intentionally retains open space after the bounded conclusion;
it is not a blank or orphan-only page.

## Named review lenses and outcomes

| # | Lens | Outcome |
|---:|---|---|
| 1 | Hierarchy | Passed: title, section, table, note, warning, and conclusion levels remain distinct |
| 2 | Typography | Passed: no missing glyph, replacement character, black square, or unreadable identifier was observed |
| 3 | Grid | Passed: page margins, table rules, panels, and text columns do not collide or overflow |
| 4 | Spacing and rhythm | Passed: dense evidence tables remain scannable; no accidental void or isolated heading was observed |
| 5 | Narrative order | Passed: scope precedes observations, actions, retained state, review, and nonclaims |
| 6 | State-machine clarity | Passed: discover, freeze, classify, preserve, integrate, verify, and retire are ordered and text-labeled |
| 7 | Custody/status separation | Passed: reachability, byte custody, mainline publication, and scientific acceptance are not merged visually |
| 8 | Palette identity | Passed: lapis, turquoise, ivory, saffron, and pomegranate retain stable roles |
| 9 | Pattern redundancy | Passed: patterns supplement, but never replace, text labels and borders |
| 10 | Ornamental restraint | Passed: the title motif and figure texture do not obscure evidence or imply magnitude |
| 11 | Grayscale legibility | Passed: every heading, panel, table, warning, and identifier remains distinguishable without color |
| 12 | Identifier integrity | Passed: 40-hex Git IDs and 64-hex SHA-256 values remain complete and visibly wrapped |
| 13 | Table legibility | Passed: row ownership, values, boundaries, and notes remain aligned and readable |
| 14 | Searchability | Passed within the untagged-PDF boundary: text extraction is coherent; no PDF/UA claim is made |
| 15 | Print-preview fidelity | Passed as a digital preview: fine rules and text remain legible in color and grayscale |
| 16 | PDF/font profile | Passed by the exact gate: six A4 PDF 1.7 pages with embedded Unicode-mapped fonts |
| 17 | Action safety | Passed by the builder and aggregate publication-link gates for the declared bounded HTTPS action profile |
| 18 | Reproduction | Passed for two isolated same-toolchain builds equal to the committed bytes; no cross-toolchain claim is made |
| 19 | Source/derivative separation | Passed: Markdown, header, filter, SVG, figure PDF, and receipt PDF retain explicit roles |
| 20 | Complete rendered inspection | Passed: no blank, clipped, overlapping, corrupt, or misordered page remains |

## Bounded conclusion

No visual defect remains in the exact six-page subject. This receipt is visual evidence only. It
does not prove the Git observations, command transcript, recovery routes, PDF/UA conformance,
external-link availability, mathematical correctness, estimator validity, scientific acceptance,
publisher authenticity, independent review, or cross-toolchain equivalence. Rendered page images
are disposable inspection intermediates and are not evidence artifacts.
