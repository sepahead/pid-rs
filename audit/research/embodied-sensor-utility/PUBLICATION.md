# Publication sources and reviewed references

Author: **Sepehr Mahmoudian**. Use the [software citation metadata](../../../CITATION.cff) and the paper-specific citation paragraphs in the [full manuscript](EXPOSITION.md) and [overview](OVERVIEW.md). Cite the defining method papers separately.

The two reports connect categorical Makkeh–Gutknecht–Wibral shared exclusions, sensor availability and predictive utility. They state the assumptions, give complete finite examples, and explain the current Rust implementation and computational cost. Four classical finite-PMF foundations now have local Lean checks and a fresh replay; their [exact scope and source snapshots](../../formal/lean-finite-logscore/PUBLICATION.md) remain separate from the handwritten conditional sensor argument. The reports contain no new timing measurement, implemented learning loop or sensor benchmark. The availability objective is determined by subset mutual information; a full PID needs a separately tested explanatory benefit.

## Current references and retained prior observation

The current [input profile](../../formal/latex/embodied-sensor-utility/publication-inputs-v1.json) binds the selected PDF, generated TeX, figures and reader observations. The dated [initial reproduction record](REPRODUCTION.json) and the table below describe the earlier report revision, before the finite-PMF proof was added. They are historical evidence, not a check of the revised pages. The proof package carries its own formal evidence; a PDF build does not establish a theorem.

### Current offline sensor workflow revision

The detailed report now specifies the RGB/grayscale and pressure-audio input paths, separate feature maps, declared bins, reference labels and multisensor fusion evaluation. Its revised vector diagram distinguishes available, partial, distorted and missing observations. Shared context and pretrained weights have explicit attribution and data-leakage boundaries. The office example supplies a real negative result: added empirical information can coexist with worse fixed-model loss. The report maps offline analysis to preparation, labeling, representation, training, placement, tuning and integrity review without claiming an implemented camera/audio adapter or learner.

The [offline workflow reproduction record](REPRODUCTION_OFFLINE_SENSOR_USE.json) identifies the selected page counts, source profile, output bytes, normal and optimized controls, exact replay, and actual rendered-review coverage. It also records shared tools and custody, missing physical-print/accessibility evidence, and retained production failures. The current profile binds the selected sources and derived outputs. The two earlier reproduction records below keep their original identities and scope.

Source review corrected two premises before selection: common context can carry target information into several feature groups, and frozen pretrained weights can still contain evaluation overlap. The overview heading was moved with its explanatory paragraph. Repeated verification prose was shortened, and the closing citation was made a compact paragraph. These layout edits retain the mathematical statements and verification limits.

### Prior finite-PMF revision

The prior finite-PMF full paper has 20 pages; its overview has three. Both visible bylines and all four discovery metadata observations name Sepehr Mahmoudian. Two fresh builds per report matched PDF, generated TeX, vector figures and typed reader observations before selection. The retained [finite-PMF production record](REPRODUCTION_FINITE_LOGSCORE.json) separates discovery, review and exact replay.

All 23 pages of that prior revision have rendered review coverage. Full pages 1–10 were inspected directly; a separate reviewer inspected pages 11–20. After the cost correction, page 17 was inspected again; the other 19 raster pages matched the reviewed version exactly. The final overview's three pages were inspected directly. The added proof and boundary examples on full pages 4–5 received larger renders. The 20 review lenses below apply with the same stated limits. No new physical print or accessibility test is claimed; the unchanged vector figures retain the prior grayscale review.

An unqualified comparison between dense log-score cost and occupied-state PID cost was removed because the input sizes need not match. The report retains each cost separately. Two earlier overview layouts left sparse fourth pages and were not selected. A later wording revision triggered the existing strict underfull-line check; its failed output was retained, then the sentence was rephrased without weakening the check. No mathematical statement changed during these layout corrections.

### Previous reference revision

The previous 23 September 2026 profile selected a 17-page [full paper](../../../output/pdf/embodied-sensor-utility.pdf) and a three-page [overview](../../../output/pdf/embodied-sensor-overview.pdf). Two fresh builds of each yielded identical PDF, generated TeX, vector figures and typed reader observations before reference selection. Both visible bylines and all four retained PDF metadata observations name Sepehr Mahmoudian.

| Reference | Bytes | SHA-256 |
|---|---:|---|
| Full PDF | 298938 | `b02d8fb6f7a9aa7ce3d4c0380326e21aad6acee4792f2690ac6302ba60c15339` |
| Overview PDF | 91502 | `24bf1e90c85622de9688260a041b28caf7ffcfea458ff290e4f710d1a7606ecd` |
| Full generated TeX | 59376 | `6ef7a0bf73022abffd7f0cc98ff5db1279a222a8e37ef2ea6a4b6b284af04cb4` |
| Overview generated TeX | 10908 | `8b22f54f9b155f90445008d616decf7f5c3cc61b62f57b73411d9d8bd19c2090` |

The [input profile](../../formal/latex/embodied-sensor-utility/publication-inputs-v1.json) records every source pin and the complete output observations. Reference selection is a publication decision, not proof of the scientific claims. Exact replay, repository integration and hosted checks have separate execution records.

## Production contract

The fixed [producer](../../../scripts/build-embodied-sensor-pdfs.py) accepts only `full` and `overview`, with three and one SVG conversions. Each invocation makes two fresh builds in an absent destination. It checks PDF, TeX and figure identity, A4 geometry, embedded/subset Unicode fonts, internal navigation and text from two readers. The allowed actions are the first-page `GoTo`/`Fit` opener, internal navigation and enumerated HTTPS links. Discovery cannot accept references; exact mode must match the selected references. Neither mode installs public outputs.

The finite Lua and Python maps preserve repository-relative Markdown links and enumerate their public PDF targets. The [data-flow](figures/sensor-data-to-evidence.svg), [signed-atom](figures/signed-atoms-and-sensor-value.svg) and [availability](figures/availability-weighted-gain.svg) figures remain editable vector sources. Shared TeX styles and font-license records are repository-local. The producer is pinned by the caller registration, avoiding a self-hash cycle.

The native profile binds the selected tools, format, sixteen font files and reader package. It does not provide complete TeX dependency closure, cross-toolchain identity, atomic source capture, accessibility tagging, live external-link validation or an operating-system hard resource limit. The full and overview calls use 66 and 62 primary commands; sampled process-observer calls are separate. Inert controls exercise source/data predicates and reader-shaped fixtures. They do not establish native-build success or readable layout.

## Previous page review

All 20 pages of the previous reference revision have rendered-review coverage. Unchanged pages retain exact image-byte joins to previously inspected pages; changed pages were inspected directly. The full report's equations, statistical bound, cost notation and three figures received targeted larger renders across the reviewed revisions. The final title pages, verification table and citation text were inspected at 2000-pixel width. Full pages 5, 6 and 9 were also checked in grayscale. A later Markdown-portability correction preserved all 25 display bodies; its sole changed PDF page, full page 3, was inspected again at normal and large size. The other 19 rendered pages matched the previously reviewed images exactly.

| Review lens | Observation or limit |
|---|---|
| Hierarchy | Primary title, sections and subordinate headings remain distinct. |
| Typography | Mathematical symbols and prose are legible; code paths do not stretch body lines. |
| Grid | Text, tables and figures stay within the page margins. |
| Spacing and rhythm | Equations, captions and headings have visible separation. |
| Narrative order | Definitions precede loss, availability, examples, data and evaluation. |
| Motif provenance | Existing repository publication styles supply the decorative geometry. |
| Motif coherence | Title band and corner marks use the same restrained visual language. |
| Ornamental restraint | Patterns remain behind or outside content. |
| Palette identity | The established lapis, turquoise, ink and muted accent roles are retained. |
| Pattern/data separation | No mathematical value or acceptance state is encoded by decoration. |
| Color-redundant labels | Signed bars, zero dots, labels and branch text remain interpretable without color. |
| Grayscale legibility | Three figure pages retain readable labels and distinguishable structure. |
| Searchability and order | Two readers extract text; selected equations and tables were checked against the page. This is not an accessibility audit. |
| Print fidelity | Vector figures and rendered margins were inspected; no physical print test is claimed. |
| A4 and fonts | Both repeated builds record A4 geometry and embedded/subset fonts. |
| Link/action safety | The fixed action profile and enumerated targets are checked; remote availability is not. |
| Deterministic reproduction | Two builds per report match within the selected profile; exact replay remains a separate check. |
| Source/derived separation | Markdown, SVG and templates remain distinct from generated TeX/PDF references. |
| Portable source dependencies | Public sources use relative paths and local styles; execution still needs the declared native profile. |
| Normal and large renders | All final pages have direct or exact-join coverage; high-risk and grayscale pages received direct review. |

The reviews share repository sources, tools and custody. Council advice and visual agreement are not independent mathematical or application evidence.

## Failed production routes retained

| Route | Observation and disposition |
|---|---|
| Inherited five-font roster | The first controlled discovery stopped before a PDF: the shared style required additional faces. The sensor profile binds sixteen fonts; the inherited profile is unchanged. |
| Nested table writer with outer options | Pandoc inserted the complete document template into table fragments. A fragment preamble guard rejects this output. |
| Copied options with a nil template | A subsequent native run still inserted a preamble. Fresh `pandoc.WriterOptions` replaced this route; see the [Pandoc Lua API](https://pandoc.org/lua-filters.html#writeroptions-opts). |
| Justified code-heavy body | A long Rust path caused an underfull-line rejection. Ragged-right composition removes stretched spacing. |
| Ragged right with font expansion | Small overfull lines remained. Font expansion is disabled for these reports; the strict log threshold is unchanged. |

The staged Markdown check also rejected same-line display delimiters and one operator command. Standalone delimiters and upright KL notation corrected that format boundary without changing any display formula. Both reports were rebuilt; the previous reference identities above bind that corrected source.

These are production failures, not failed mathematical results. Their preimages, logs and original execution bounds remain in the retained attempt records. Passing inert controls did not detect every native dependency or layout failure. Later author, citation and verification-process additions were rebuilt and reviewed under their own source pins.
