# Publication record for the November mathematical results guide

**Sepehr Mahmoudian · 19 November 2026**

The [current guide](../../MATHEMATICAL_RESULTS_GUIDE_CURRENT.md) and its [four-page PDF](../../output/pdf/mathematical-results-guide-current.pdf) connect six results about categorical data and their finite encodings. Page 1 calculates exact coverage in the specified four-row bootstrap example. Page 2 distinguishes the conditional law for a fitted map from its mixture and derives the sign-constant condition for a finite optimization. Page 3 gives the decoding argument for integer count tables. Page 4 gives the mathematical scope of the 22 checked declarations, the later proof of the archived eighteen-family formula and the software costs. Each study supplies its own assumptions and evidence.

The [foundation guide](../../MATHEMATICAL_RESULTS_GUIDE.md) and its [28-page PDF](../../output/pdf/mathematical-results-guide.pdf) give the longer account of nine result families and six prior companion packages. Existing links into that account retain their original targets. The foundation edition retains its own v5 structure and cross-toolchain profiles. Its recorded PDF has 75 distinct HTTPS targets and 285 ordered navigation records.

## Reproducing the current edition

The [edition profile](../formal/latex/mathematical-results-guide-current/edition.json) binds the guide, shared style files, template, Pandoc filter and earlier publication to their precise bytes. The first four-page edition had SHA-256 `e81a9cb8d3c9e1ed07ba39c12b37588bbbf24db8d0ca6b2bdea26ede12405274` and 63,682 bytes. It predates the separate proof of the eighteen-family formula. Two more builds in separate empty directories produced the updated 63,794 bytes with SHA-256 `0556d73ae891eb5dbeaadf219433a057bf22b66b23a593b323937be66a619d3f` using Pandoc 3.10.2 and LuaHBTeX 1.18.0 from TeX Live 2024. The final LaTeX passes reported zero warnings, undefined commands, missing glyphs or rejected boxes. [Build and inspection commands](../../scripts/README.md)

Run the following from the checkout. The first command typesets in a fresh directory and compares both the regenerated and shipped file to the measured profile. The second checks the source and shipped PDF and requires Poppler.

```sh
python3 -I -S -B scripts/build-current-mathematical-results-guide.py --check
python3 -I -S -B scripts/build-current-mathematical-results-guide.py --check-committed
```

Both commands also passed under optimized Python. A separate set of checks exercised the intact object and nine changes to its inputs or expected metadata in each Python mode. The controls included a false Cargo feature name, an incorrect author, altered or missing files, and changes to the expected font and link records. The aggregate publication gate dispatches the native or shipped check according to its mode. The complete indexed checkout has a separate link-portability gate.

## Page inspection and limits

The rendered guide has four A4 pages with searchable text, nine embedded subset font entries with Unicode maps, 16 distinct HTTPS targets and the author recorded in both the byline and PDF metadata. Its text is untagged. This edition makes no PDF/UA or cross-platform reproduction claim. The review used page images, including grayscale views. Physical print output and individual assistive-technology sessions have no associated measurement.

| Publication lens | Observation |
| --- | --- |
| Hierarchy | The title and byline precede the question. Subject headings precede each example. |
| Typography | Serif body text, distinct headings and a monospaced identifier separate mathematical prose from Rust symbols. |
| Grid | The four pages share the same measure, running-head locations and page-number positions. |
| Spacing and rhythm | The displayed count identities have breathing room. The longest first page clears the footer. |
| Narrative order | The guide proceeds from coverage and conditioning to optimization, encoding, checked counts and software scope. |
| Motif provenance | The renderer uses the existing repository publication package. |
| Motif coherence | Corner rosettes and the fine-grain background use the same pattern throughout. |
| Ornamental restraint | Rules and corner marks leave the mathematical displays clear. |
| Palette identity | The shared lapis title, turquoise subordinate headings, ink body and ivory background match the source style. |
| Pattern and data | Every count, bound and status is written explicitly in text or mathematics. |
| Color-redundant labels | Section names, numerals and descriptive link labels carry the meaning in grayscale as well. |
| Grayscale | The four grayscale pages preserve text hierarchy and visibility. |
| Search and reading order | The source-derived page text reads in a single column. The coverage fraction, finite count and Rust identifiers are searchable. |
| Print | A4 rasterization preserved margins and content on all four pages. No physical sheet was inspected. |
| Page and font profile | Poppler reported A4 and nine embedded, subsetted font entries with Unicode maps. |
| Links and actions | The clickable HTTPS target set matches the rendered Markdown destinations. Local target resolution belongs to the repository's staged publication check. |
| Reproduction | Two local builds matched the released byte digest. The shipped-file check can run without a typesetting engine. |
| Source and derived files | The Markdown provides the body, the TeX and Lua files render it, and the PDF is the derived artifact. |
| Portability | The checked-in filter and style use repository-relative source locations. The typesetter, fonts, Pandoc and Poppler are external dependencies. |
| Normal and high resolution | All four pages were inspected at 105 dpi. At 200 dpi the reviewed details included the coverage arithmetic, optimization bound, table enumeration and literal Rust feature and API names. The updated fourth page also gives both truth values and the missing list-membership condition. |

Model assistance supported the source comparisons and page review. These reviewer and rendering checks share the same publication sources. No independent human mathematical or accessibility disposition is recorded. Cite Sepehr Mahmoudian (2026), *Mathematical results guide for November 2026*, and include the exact repository commit or release. [Software citation](../../CITATION.cff)
