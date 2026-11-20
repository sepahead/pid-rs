# The 20 November mathematical publications

Sepehr Mahmoudian, 20 November 2026

The five-page November guide adds two results to the four-page edition of 19 November. One concerns final rounding in a target-conditioned information ratio. The other concerns the shared-exclusion values of six fixed categorical count tables. Each study has its own reader, substantive checks and typeset paper. The following observations concern the published documents. [Earlier edition record](mathematical-results-guide-november-2026-11-19.md) · [Current guide](../../MATHEMATICAL_RESULTS_GUIDE_CURRENT.md)

| Publication | Pages | SHA-256 of the shipped PDF | Rendered inspection |
|---|---:|---|---|
| [November results guide](https://github.com/sepahead/pid-rs/blob/570c9c67800affde745032cd9d7296f29839f2ba/output/pdf/mathematical-results-guide-current.pdf) | 5 | `61950e12af0e45709894cbdae6cf29ee2260cfd8b34fe289ca692fe61ac24b7e` | All five pages at 105 dpi. Changed pages 1, 4 and 5 at 200 dpi. Pages 2 and 3 had the same 105 dpi raster as before. |
| [Normalized Shannon arithmetic, four-page edition](https://github.com/sepahead/pid-rs/blob/78e915e5f395f5b2d12e2722d7d547ac9efacdd4/output/pdf/normalized-shannon-arithmetic.pdf) | 4 | `c9bcc78b9ef7af19e773fad034900a419ac236a2cd6c6ef9a422eaa3e8b8645e` | All four pages at 110 dpi. Page 4 and selected equations, rounding examples, division and results table at 200 dpi. |
| [Six categorical certificates](https://github.com/sepahead/pid-rs/blob/570c9c67800affde745032cd9d7296f29839f2ba/output/pdf/three-source-six-certificate-observations.pdf) | 6 | `0c03166935e9cab223c6262e55e8465886b8057bc059ac12addfce50ffac22e0` | All six pages at 105 dpi. Eight details across the six pages at 180 dpi, including the signed atom, denominator and coordinate counts. |

## Review of the first printed editions

| Visual property | Observation |
|---|---|
| Hierarchy, typography, grid and spacing | Titles, definitions, equations and table headers were checked in reading order. Visible digits, signs, exponents and fixed-width field names were compared with the source. |
| Narrative order | Each study introduces the target, inputs and reported quantity before interpreting its numerical example. The guide directs readers to the scope of each check. |
| Motif provenance, coherence, restraint and palette | The three publications use the reviewed local styles. The heading and paper decorations keep their established colors and positions independently of the numerical values. |
| Separation of data from pattern, redundant labels and grayscale | Signs, values, units, table headers and status fields carry the distinctions in text. Grayscale renderings were examined for contrast and reading order. |
| Searchability, extraction order and print fidelity | Poppler extracted the headers, equations and numbers from real text. The page reviews checked the printed marks near tables and fractions. Two-dimensional mathematics can linearize differently during extraction. Physical printing was outside this review. |
| A4 profile, embedded fonts and link actions | The shipped A4 files passed their respective page, font and URL checks. The guide had 23 URI annotations and 20 distinct targets. A separate strict reader inspected 165 PDF objects. |
| Reproduction, source separation and portability | The unchanged underlying typesetting engines built the documents in the provisioned environment. The leaf builders checked both shipped artifacts and fresh exact builds in ordinary and optimized Python. Source Markdown, local styles and rendered PDFs can be inspected separately. |
| Normal-size and high-resolution inspection | The table lists the actual page and detail sets. On the six-table report a source permutation was applied once and compared at 108 coordinates. The table and caption were checked against this count. |

Model-assisted reviews shared the underlying Markdown, PDF and toolchain. These observations establish bounded rendering and reproduction facts. The scientific predicates, their assumptions and their independent obligations are documented in the [ratio study](../research/normalized-shannon-arithmetic/README.md) and [six-table study](../research/three-source-six-certificate-observations/README.md).

## Exact empirical inputs and signed logarithms

The revised papers distinguish a finite population law from a table of integer counts. The arithmetic paper proves why exact positive rational mutual information in nats cannot occur in such a table, and why the two examples can still be reproduced after rounding the inputs once. It also states when the source-only entropy ratios equal the target-based degrees and gives a binary example whose convergent denominator rounds back to the numerical floor. The six-table paper applies the same argument to positive and negative coordinates of the form $\ln(Q)/N$. The checked observations still comprise the original 184 report calls and six categorical tables. [Arithmetic argument](../research/normalized-shannon-arithmetic/README.md) · [Signed coordinate argument](../research/three-source-six-certificate-observations/README.md) · [Hermite, section III](https://doi.org/10.3931/e-rara-101019)

| Revised publication | Pages | SHA-256 | Rendered comparison |
|---|---:|---|---|
| [November results guide](../../output/pdf/mathematical-results-guide-current.pdf) | 5 | `2aa7434f4df0de7c6f761c6ac710b0721c330030aebb8cb862e035c3e98a660a` | All five pages compared at 105 dpi. Pages 1–4 have identical pixels. Page 5 was also inspected at 200 dpi and in grayscale. Its links bring the document to 24 URI annotations with 21 targets. |
| [Normalized Shannon arithmetic](../../output/pdf/normalized-shannon-arithmetic.pdf) | 5 | `a016d8fef5cb3082ca28bd1d182a186e7c80424f254e4b2df5f71eba0ff05c3e` | Each page was read at 90 dpi. The count proof on page 2 and threshold example on page 5 were also read at 180 and 160 dpi, respectively. |
| [Six categorical certificates](../../output/pdf/three-source-six-certificate-observations.pdf) | 6 | `082fe3edf72069dbe71172d6579ec819f5d7c07fb4227e877aa72ecef404fbd6` | All six pages compared at 90 dpi. Only page 2 changed and was also inspected at 180 dpi. Its two new links bring the document to 50 URI annotations and 31 targets. |

The revised pages use the existing fonts, page grid, palette, labels and ornamental elements. Their fraction bars, exponents, signs and second-page table were inspected in the rendered documents. Each paper rebuilt byte for byte in ordinary and optimized Python. The preceding editions remain available through the exact links above.

Cite Sepehr Mahmoudian (2026), *The 20 November mathematical publications*, with the exact repository commit or release. Cite each study and its defining papers for mathematical claims. [Software citation](../../CITATION.cff)
