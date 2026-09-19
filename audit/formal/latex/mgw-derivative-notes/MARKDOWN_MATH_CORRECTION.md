# Markdown math rendering correction

**Status: current v2 exact reproduction accepted locally.** The retained full publication
aggregate failed the repository Markdown math gate with 490 findings on the two new manuscripts,
the gradient overview and its theorem map. A successful PDF build cannot establish that Markdown
renders correctly on GitHub. The existing linter and its required checks remain unchanged.

The repair uses `$` for inline math and `$$` for display math, as documented by
[GitHub's mathematical-expression guide](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions).
It also changes the upright variance and sign operator spellings from `\operatorname` to
`\mathrm` to satisfy this repository's existing linter, preserving their symbols and arguments.
That linter rule is not a claim that GitHub universally rejects `\operatorname`. The short gradient
overview separately defines the scalar path derivative, cell score and harmonic sum. No other
formula or scientific statement changes. The
[structured record](MARKDOWN_MATH_CORRECTION.json) binds the exact failure, source identities and six-command Pandoc comparison.
It separates current v2 reproduction, historical v1 observations and the full aggregate outcome.

The [version-2 input profile](publication-inputs-v2.json) changes the two manuscript pins and
two generated TeX references. Its version-1 schema is unchanged; the filename distinguishes the
successor source profile. The nine other inputs, PDFs, observations and vector figure remain fixed.
The builder and its control harness select version 2 explicitly. The original
[version-1 profile](publication-inputs-v1.json) and dated
[publication observation](PUBLICATION_OBSERVATION.json) remain historical evidence for their
original inputs. Updating a source pointer must not retarget an earlier execution receipt.

The reader already enables both `tex_math_dollars` and `tex_math_single_backslash`, so it needs no
new parser flag or math-rewrite filter. A separately admitted six-command Pandoc comparison parsed both old and new manuscripts and
produced both successor TeX files. The parsed structures match after exactly the two operator
spelling substitutions. Each actual TeX file has one changed line and no other delta. Root
reviewed those complete diffs before binding the new references. The old TeX files remain in the
inert archive. The PDF, observation and figure targets are unchanged. Four complete exact checks, covering
both notes in normal and optimized Python, made eight fresh PDFs with 152 native commands.
All outputs matched the current v2 references; every PDF matched its previously reviewed v1
artifact bytes. The existing visual review therefore applies to those identical artifacts;
no new visual inspection is claimed.

Markdown checks, their controls and the derivative controls passed in both Python modes.
The structured record separates the full aggregate outcome from final source-state, publication-link
and hosted/mainline evidence. Earlier failed aggregate attempts remain failed and preserved.

The [inert preimages](negative-markdown-math-v1/DISPOSITION.md) retain all four old Markdown files,
both expected TeX files, and the builder/control sources. They remain evidence of the previous
syntax and execution route, not current rendering inputs or an accepted replay route. Their
mathematical content is not rejected by the rendering-policy failure. Raw original stderr and
historical native results remain in ignored local custody with their own archival obligations.

These artifact checks add no theorem, estimator implementation, calibration or application evidence.
The [gradient result](../../lean-prefix-mgw-gradient/PUBLICATION.md) retains fixed finite categorical
alphabets, common support on an open scalar-parameter neighborhood, differentiability, IID complete
rows and a bounded base-point score. The atom-derivative bound also assumes zero target-fiber
tangents and the complete local inverse row. Information is in nats; atom derivatives are in nats
per scalar-parameter unit. The eleven local formal families and the handwritten cusp's open
formal status are unchanged.
