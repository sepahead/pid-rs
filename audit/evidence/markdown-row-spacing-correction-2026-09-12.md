# Preserve TeX row spacing in Markdown checks

The 12 September 2026 publication check rejected four valid row breaks: two in the
[current bias exposition](../formal/lean-prefix-mgw-bias/EXPOSITION.md) and two in its
[preserved predecessor](../formal/lean-prefix-mgw-bias/archive/predecessor-package-2026-09-08/EXPOSITION.md).
Each uses `\\[0.35em]` inside a dollar-delimited `gathered` display. The checker found
the substring `\[` starting at the second backslash and misclassified it as a legacy
display delimiter. Both normal and optimized Python reported the same four failures.

This is valid TeX syntax: the two backslashes form a row-break command, and the bracketed
argument specifies extra line spacing. GitHub documents its dollar-delimited math and
MathJax renderer; MathJax documents the optional spacing argument.
See [GitHub math syntax](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions)
and [MathJax line-spacing support](https://docs.mathjax.org/en/latest/upgrading/earlier/whats-new-2.0.html#many-new-tex-additions-and-enhancements).

The correction scans delimiter occurrences inside an established display and counts the
preceding backslashes. Even runs form pairs; odd runs leave an active delimiter, which
still fails. The rule covers all four legacy delimiter tokens. Outside display math,
the existing conservative source check remains because Markdown has its own
[backslash processing](https://github.github.com/gfm/#backslash-escapes).

The equations, proof inputs and PDF bytes are unchanged. Rewriting the equations,
exempting whole documents, skipping display checks or matching only the observed spacing
literal would leave the lexical defect or suppress valid checks. A one-character
lookbehind would also misclassify longer odd backslash runs. A complete renderer is
unnecessary for this token distinction.

The production checker and self-test passed in both normal and optimized Python on
12 September 2026, using Python 3.14.6 with `-I -S -B`. Each self-test rejected
46 negative cases and accepted 23 lexical fixtures, including the complete valid
spacing example. All four commands returned zero with empty stderr. The tracked
source, index and HEAD stayed unchanged during these checks. The
[original four findings](markdown-row-spacing-correction-2026-09-12.before.stderr.txt)
remain as exact negative evidence.

| Checked source | SHA-256 |
|---|---|
| `scripts/check-markdown-math.py` | `89f2126faed9bcde53a24b467ebb57278483318d28e5f488cf77955ea523bb95` |
| `scripts/check-markdown-math-self-test.py` | `01d802c18991b81b694ca51e6efc937af52ef185f4410f73ef08c0c70fb284f7` |

The pre-correction sources remain in Git at commit
`f8c1be62c09741e4317417f7d3b9d6253935518d`. Historical DNF execution records keep
their original source hashes; they do not identify this new checker revision.

The regression fixtures cover runs of one through six backslashes before each delimiter,
the motivating `gathered` display and unchanged conservative prose behavior. Existing
code-span, fenced-code, inline-math and exact historical-byte controls remain in place.
These checks establish the specified lexical behavior. They do not prove arbitrary TeX
rendering or add mathematical, statistical or formal acceptance.
