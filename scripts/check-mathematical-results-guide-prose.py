#!/usr/bin/env python3
"""Check a narrow controlled-language subset for the mathematical results guide.

This checker applies local editorial rules inspired by selected descriptive-writing
rules in ASD-STE100 Issue 9. It is not an ASD-STE100 conformance, compliance, or
certification test. It does not check vocabulary, active voice, one-topic semantics,
technical truth, or mathematical correctness.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import stat
import sys
from typing import NamedTuple


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "MATHEMATICAL_RESULTS_GUIDE.md"
BOUNDARY = (
    "selected pid-rs editorial checks only; "
    "not ASD-STE100 conformance, compliance, or certification"
)
MAX_SENTENCE_WORDS = 25
MAX_PARAGRAPH_SENTENCES = 6

# Method catalog: validation.analytic-common-radius-manifold-sx-bridge
# These exact source sentinels bind the narrow theorem and its stopping boundary.
# They do not prove the theorem. They prevent an editorial rewrite from silently
# dropping a premise, counterexample, gauge qualification, or explicit nonclaim.
COMMON_RADIUS_BRIDGE_SENTINELS = (
    (
        "project-defined catalog status",
        "repository-derived conditional lemma, catalogued as project-defined **[R]**",
    ),
    (
        "project-defined contribution status",
        "repository-derived contribution, catalogued as project-defined",
    ),
    (
        "Ehrlich algebraic-form boundary",
        "expression with the algebraic form of Ehrlich et al.'s bivariate analytic formula",
    ),
    (
        "no Ehrlich manifold-lemma attribution",
        "Ehrlich et al. define the analytic formula and relative precision, but they do not prove this manifold small-ball lemma.",
    ),
    (
        "manifold-only implementation gap",
        "Manifold estimator and manifold PID implementation remain open **[O]**",
    ),
    (
        "boundary-counterexample status",
        "Conditional population lemma **[R]** and boundary counterexamples **[X]**.",
    ),
    (
        "pointwise joint-law premise",
        r"Assume the joint law of $(T,S_1,S_2)$ is absolutely continuous with respect to $\nu\otimes\mu\otimes\mu$.",
    ),
    (
        "pointwise source-marginal continuity",
        r"Each $f_{S_i}$ is continuous at $s_i$.",
    ),
    (
        "pointwise target-marginal continuity",
        r"$f_T$ is continuous at $t$.",
    ),
    (
        "pointwise source-target continuity",
        r"Each $f_{T,S_i}$ is continuous at $(t,s_i)$.",
    ),
    (
        "pointwise pair-overlap control",
        r"A version of $f_{S_1,S_2}$ is essentially bounded on a neighbourhood of $(s_1,s_2)$.",
    ),
    (
        "pointwise triple-overlap control",
        r"A version of $f_{T,S_1,S_2}$ is essentially bounded on a neighbourhood of $(t,s_1,s_2)$.",
    ),
    (
        "pointwise logarithm positivity",
        r"$f_T(t)$ and both density sums in the following ratio are strictly positive.",
    ),
    (
        "no-estimator boundary",
        "It is not a new PID functional, an estimator, or a scientific-priority claim.",
    ),
    (
        "overlap-only proof premise",
        "The proof needs only the two displayed little-$o$ overlap conditions.",
    ),
    (
        "boundedness is sufficient not necessary",
        "Local essential boundedness is a convenient sufficient condition, not a necessary one.",
    ),
    (
        "discarded overlap orders",
        r"The discarded overlap terms are $O(r^{2d})$ and $O(r^{q+2d})$.",
    ),
    (
        "retained union scales",
        r"Positivity makes the retained union scales $\Theta(r^d)$ and $\Theta(r^{q+d})$.",
    ),
    (
        "modern Clayton parameterization",
        r"modern positive-parameter Clayton form at a fixed parameter $\theta>0$.",
    ),
    (
        "Clayton provenance boundary",
        "This form is equivalent to a reparameterization of Clayton's 1978 survival-association model:",
    ),
    (
        "ordinary-copula semantic boundary",
        "It is used here as an ordinary copula, with no survival-time semantics.",
    ),
    (
        "Clayton density",
        r"c_\theta(u,v)&=(1+\theta)(uv)^{-1-\theta} (u^{-\theta}+v^{-\theta}-1)^{-2-1/\theta}",
    ),
    (
        "Clayton density normalization",
        r"=1-2\varepsilon+C_\theta(\varepsilon,\varepsilon)\longrightarrow1.",
    ),
    (
        "signed-mixture density",
        r"f_{T,S_1,S_2}(t,x,y)= \frac{\alpha}{4}g_0(t)\mathbf 1_{\{|x|,|y|<1\}} +\frac{1-\alpha}{4}g_1(t)c_\theta(|x|,|y|)",
    ),
    (
        "source-pair support indicators",
        r"f_{S_1,S_2}(x,y) &=\tfrac{\alpha}{4}\mathbf 1_{\{|x|,|y|<1\}} +\tfrac{1-\alpha}{4}c_\theta(|x|,|y|) \mathbf 1_{\{0<|x|,|y|<1\}}",
    ),
    (
        "essential-unboundedness inference",
        "Its diagonal blow-up therefore persists on positive-measure open sets in every neighbourhood.",
    ),
    (
        "source-pair singularity",
        r"c_\theta(r,r)\sim(1+\theta)2^{-2-1/\theta}r^{-1}",
    ),
    (
        "Clayton first-order overlap",
        r"C_\theta(r,r)\sim\lambda r,\quad \lambda=2^{-1/\theta}>0.",
    ),
    (
        "Clayton counterexample conclusion",
        "The example does not prove that pair local boundedness is necessary.",
    ),
    (
        "replacement overlap conclusion",
        "It proves that some replacement condition must control the overlap.",
    ),
    (
        "smooth-marginal insufficiency boundary",
        "Why the displayed smooth marginals do not suffice.",
    ),
    (
        "fixed-dimension gauge weights",
        r"Radii $a_1r,a_2r$ in dimension $d$ produce weights $a_1^d,a_2^d$.",
    ),
    (
        "gauge asymptotic weights",
        r"$v_i(r)/a(r)\to\lambda_i\in(0,\infty)$.",
    ),
    (
        "gauge overlap conditions",
        r"$\Pr(E_{1,r}\cap E_{2,r})=o(a(r))$ and $\Pr(C_r\cap E_{1,r}\cap E_{2,r})=o(w_r a(r))$.",
    ),
    (
        "unequal-dimension boundary",
        "If $d_1<d_2$ and both branch-one coefficients are positive, branch one dominates.",
    ),
    (
        "vanishing-coefficient boundary",
        "If either coefficient vanishes, continuity alone does not determine which branch dominates or its replacement rate.",
    ),
    (
        "equal-radius gauge boundary",
        "Equal numeric source radii are therefore a gauge choice.",
    ),
    (
        "global and PID nontransfer",
        "global expectation interchange, PID-atom property, mixed-support result, or software refinement.",
    ),
    (
        "generic metric-theorem nontransfer",
        r"The source-union operation $\min(d_1,d_2)$ is not itself a metric, so a generic metric-kNN theorem does not transfer.",
    ),
)

# This source-specific census prevents a parser change from silently shrinking the
# checked surface. It supplements the limits above; it never replaces them.
EXPECTED_CENSUS = {
    "direct_paragraphs": 152,
    "direct_sentences": 472,
    "list_items": 129,
    "list_sentences": 182,
    "headings": 23,
    "tables": 4,
    "table_cells": 90,
    "display_math": 28,
    "fenced_code": 0,
    "media": 2,
}

EVIDENCE_RE = re.compile(
    r"(?:\*\*)?\[(?:[PXBREO](?:,[PXBREO])*)\](?:\*\*)?"
)
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^#{1,6}(?:\s|$)")
LIST_RE = re.compile(r"^(\s*)(?:[-+*]|\d{1,9}[.)])\s+(.*)$")
TABLE_DELIMITER_RE = re.compile(r":?-{3,}:?")
MEDIA_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
WORD_RE = re.compile(
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|"
    r"[^\W_]+(?:['’][^\W_]+)*(?:-[^\W_]+)*",
    re.UNICODE,
)
TERMINATOR_RE = re.compile(r"[.!?]+(?=(?:[\]\)\"”’*_]*)(?:\s|$))")


class ProseCheckError(Exception):
    """A deterministic prose-check failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class Line(NamedTuple):
    number: int
    text: str


class Sentence(NamedTuple):
    text: str
    word_count: int


def fail(code: str, message: str) -> None:
    raise ProseCheckError(code, message)


def require_common_radius_bridge_semantics(text: str) -> None:
    """Require the exact bounded theorem ledger in the canonical guide source."""

    normalized = " ".join(text.split())
    for label, fragment in COMMON_RADIUS_BRIDGE_SENTINELS:
        normalized_fragment = " ".join(fragment.split())
        if normalized_fragment not in normalized:
            fail(
                "semantic_contract",
                f"common-radius bridge lost its {label} sentinel",
            )


def decode_source(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        fail("encoding", "UTF-8 BOM is not permitted")
    if b"\x00" in raw:
        fail("encoding", "NUL byte is not permitted")
    if b"\r" in raw:
        fail("encoding", "CR and CRLF newlines are not permitted")
    if not raw.endswith(b"\n"):
        fail("encoding", "source must end with one LF newline")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        fail("encoding", f"source is not strict UTF-8: {error}")
    raise RuntimeError("unreachable")


def strip_one_quote_layer(lines: list[Line]) -> list[Line]:
    expanded: list[Line] = []
    for line in lines:
        if line.text == ">":
            expanded.append(Line(line.number, ""))
        elif line.text.startswith("> "):
            content = line.text[2:]
            if content.startswith(">"):
                fail("structure", f"line {line.number}: nested blockquote is unsupported")
            expanded.append(Line(line.number, content))
        elif line.text.startswith(">"):
            fail("structure", f"line {line.number}: malformed blockquote marker")
        else:
            expanded.append(line)
    return expanded


def remove_excluded_blocks(lines: list[Line]) -> tuple[list[Line], int, int]:
    visible: list[Line] = []
    fence: tuple[str, int, int] | None = None
    in_math = False
    math_open_line = 0
    display_math = 0
    fenced_code = 0

    for line in lines:
        match = FENCE_RE.match(line.text)
        if fence is not None:
            char, length, _ = fence
            if re.fullmatch(rf" {{0,3}}{re.escape(char)}{{{length},}}\s*", line.text):
                fence = None
            continue
        if match is not None:
            marker = match.group(1)
            fence = (marker[0], len(marker), line.number)
            fenced_code += 1
            visible.append(Line(line.number, ""))
            continue
        if line.text.strip() == "$$":
            in_math = not in_math
            if in_math:
                math_open_line = line.number
                display_math += 1
            visible.append(Line(line.number, ""))
            continue
        if in_math:
            continue
        visible.append(line)

    if fence is not None:
        fail("structure", f"line {fence[2]}: unclosed fenced-code block")
    if in_math:
        fail("structure", f"line {math_open_line}: unclosed display-math block")
    return visible, display_math, fenced_code


def form_blocks(lines: list[Line]) -> list[list[Line]]:
    blocks: list[list[Line]] = []
    current: list[Line] = []
    for line in lines:
        if line.text.strip():
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def is_table(block: list[Line]) -> bool:
    if len(block) < 2:
        return False
    rows = [line.text.strip() for line in block]
    if not all(row.startswith("|") and row.endswith("|") for row in rows):
        return False
    delimiter_cells = [cell.strip() for cell in rows[1].strip("|").split("|")]
    return bool(delimiter_cells) and all(
        TABLE_DELIMITER_RE.fullmatch(cell) for cell in delimiter_cells
    )


def classify_blocks(
    blocks: list[list[Line]],
) -> tuple[list[list[Line]], int, int, int, int]:
    paragraphs: list[list[Line]] = []
    headings = 0
    tables = 0
    table_cells = 0
    media = 0
    list_open = False
    list_base_indent = 0

    for block in blocks:
        raw_first = block[0].text
        first = raw_first.lstrip()
        joined = " ".join(line.text.strip() for line in block)
        table = is_table(block)

        if any(line.text.lstrip().startswith("|") for line in block) and not table:
            fail("structure", f"line {block[0].number}: malformed or mixed table block")
        if not raw_first[:1].isspace() and HEADING_RE.match(first):
            if len(block) != 1:
                fail(
                    "structure",
                    f"line {block[0].number}: a heading block must contain exactly one line",
                )
            headings += 1
            list_open = False
        elif not raw_first[:1].isspace() and (first_item := LIST_RE.match(raw_first)):
            active_indent = len(first_item.group(1))
            for line in block[1:]:
                item = LIST_RE.match(line.text)
                if item is not None:
                    active_indent = len(item.group(1))
                    continue
                indent = len(line.text) - len(line.text.lstrip())
                if indent <= active_indent:
                    fail(
                        "structure",
                        f"line {line.number}: unindented lazy-list continuation is unsupported",
                    )
            list_open = True
            list_base_indent = len(first_item.group(1))
        elif raw_first[:1].isspace() and list_open:
            # A blank-separated continuation is supported only when each prose
            # line remains indented relative to the open list item.
            active_indent = list_base_indent
            for line in block:
                item = LIST_RE.match(line.text)
                if item is not None:
                    item_indent = len(item.group(1))
                    if item_indent <= list_base_indent:
                        fail(
                            "structure",
                            f"line {line.number}: loose list item must remain indented",
                        )
                    active_indent = item_indent
                    continue
                indent = len(line.text) - len(line.text.lstrip())
                if indent <= active_indent:
                    fail(
                        "structure",
                        f"line {line.number}: unindented lazy-list continuation is unsupported",
                    )
        elif table:
            tables += 1
            list_open = False
            for row_number, row in enumerate(block):
                if row_number == 1:
                    continue
                table_cells += len(row.text.strip().strip("|").split("|"))
        elif MEDIA_RE.fullmatch(joined):
            media += 1
            list_open = False
        elif raw_first[:1].isspace():
            fail("structure", f"line {block[0].number}: unclassified indentation")
        else:
            for line in block[1:]:
                probe = line.text.lstrip()
                if HEADING_RE.match(probe) or LIST_RE.match(probe):
                    fail(
                        "structure",
                        f"line {line.number}: structural marker interrupts a paragraph",
                    )
            paragraphs.append(block)
            list_open = False
    return paragraphs, headings, tables, table_cells, media


def replace_links(text: str, keep_image_alt: bool) -> str:
    pattern = re.compile(r"!?\[([^\]]*)\]\((?:[^()]|\([^()]*\))*\)")
    for _ in range(32):
        def replacement(match: re.Match[str]) -> str:
            if match.group(0).startswith("!") and not keep_image_alt:
                return " "
            return f" {match.group(1)} "

        text, count = pattern.subn(replacement, text)
        if count == 0:
            break
    if "](" in text or "![" in text:
        fail("inline", "unsupported or unbalanced Markdown link")
    return text


def mask_inline(text: str, *, keep_image_alt: bool = True) -> str:
    text = EVIDENCE_RE.sub(" ", text)
    if text.count("`") % 2:
        fail("inline", "unbalanced inline-code delimiter")
    text = re.sub(r"`[^`]*`", " TERM ", text)
    if "`" in text:
        fail("inline", "multi-backtick inline code is unsupported")
    if text.count("$") % 2:
        fail("inline", "unbalanced inline-math delimiter")
    text = re.sub(r"\$[^$\n]*\$", " TERM ", text)
    if "$" in text:
        fail("inline", "unsupported inline-math delimiter")
    text = replace_links(text, keep_image_alt)
    text = re.sub(r"<https?://[^>]+>", " URL ", text)
    text = re.sub(r"https?://[^\s)>]+", " URL ", text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    if "<" in text or ">" in text:
        fail("inline", "raw HTML is unsupported")

    replacements = (
        (r"\bi\.i\.d\.", "iid"),
        (r"\be\.g\.", "eg"),
        (r"\bi\.e\.", "ie"),
        (r"\bet\s+al\.", "et al"),
        (r"\b(?:[A-Za-z]\.){2,}", "ABBR"),
        (r"\b([A-Za-z0-9_-]+)\.(md|pdf|json|rs|py|sh)\b", r"\1_\2"),
        (r"(?<=\d)\.(?=\d)", "DECIMALPOINT"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    if re.search(r"\b[^\W_]+\.[^\W_]+\b", text, flags=re.UNICODE):
        fail("inline", "unknown dotted token could change sentence boundaries")
    return (
        text.replace("**", "")
        .replace("__", "")
        .replace("*", "")
        .replace("_", "")
    )


def split_sentences(text: str) -> list[Sentence]:
    normalized = mask_inline(text)
    sentences: list[Sentence] = []
    start = 0
    for match in TERMINATOR_RE.finditer(normalized):
        part = normalized[start : match.end()].strip()
        start = match.end()
        if part:
            sentences.append(Sentence(part, len(WORD_RE.findall(part))))
    remainder = normalized[start:].strip()
    if remainder:
        sentences.append(Sentence(remainder, len(WORD_RE.findall(remainder))))
    return sentences


def collect_list_items(lines: list[Line]) -> list[tuple[int, str]]:
    items: list[tuple[int, str]] = []
    current_line = 0
    current_text = ""
    base_indent = 0
    separated = False

    for line in lines:
        match = LIST_RE.match(line.text)
        if match is not None:
            if current_text:
                items.append((current_line, current_text))
            current_line = line.number
            current_text = match.group(2)
            base_indent = len(match.group(1))
            separated = False
            continue
        if current_text and not line.text.strip():
            separated = True
            continue
        if current_text and line.text.strip():
            indent = len(line.text) - len(line.text.lstrip())
            if indent > base_indent:
                current_text += " " + line.text.strip()
                separated = False
                continue
            if not separated:
                fail(
                    "structure",
                    f"line {line.number}: unindented lazy-list continuation is unsupported",
                )
            items.append((current_line, current_text))
            current_line = 0
            current_text = ""
            base_indent = 0
            separated = False
    if current_text:
        items.append((current_line, current_text))
    return items


def audit_text(
    text: str, expected_census: dict[str, int] | None = None
) -> dict[str, int]:
    if "\r" in text or "\x00" in text or text.startswith("\ufeff"):
        fail("encoding", "text has a noncanonical marker or newline")
    if not text.endswith("\n"):
        fail("encoding", "text must end with one LF newline")

    require_common_radius_bridge_semantics(text)

    numbered = [Line(number, line) for number, line in enumerate(text.splitlines(), 1)]
    expanded = strip_one_quote_layer(numbered)
    visible_lines, display_math, fenced_code = remove_excluded_blocks(expanded)
    blocks = form_blocks(visible_lines)
    paragraphs, headings, tables, table_cells, media = classify_blocks(blocks)

    direct_sentences = 0
    max_sentence_words = 0
    max_paragraph_sentences = 0
    for paragraph in paragraphs:
        joined = " ".join(line.text.strip() for line in paragraph)
        sentences = split_sentences(joined)
        count = len(sentences)
        max_paragraph_sentences = max(max_paragraph_sentences, count)
        if count > MAX_PARAGRAPH_SENTENCES:
            fail(
                "paragraph_limit",
                f"lines {paragraph[0].number}-{paragraph[-1].number}: "
                f"{count} sentences exceed the limit {MAX_PARAGRAPH_SENTENCES}",
            )
        for ordinal, sentence in enumerate(sentences, 1):
            direct_sentences += 1
            max_sentence_words = max(max_sentence_words, sentence.word_count)
            if sentence.word_count > MAX_SENTENCE_WORDS:
                fail(
                    "word_limit",
                    f"lines {paragraph[0].number}-{paragraph[-1].number}, "
                    f"sentence {ordinal}: {sentence.word_count} words exceed "
                    f"the limit {MAX_SENTENCE_WORDS}: {sentence.text}",
                )

    list_items = collect_list_items(visible_lines)
    list_sentences = 0
    max_list_words = 0
    for line_number, item in list_items:
        sentences = split_sentences(item)
        for ordinal, sentence in enumerate(sentences, 1):
            list_sentences += 1
            max_list_words = max(max_list_words, sentence.word_count)
            if sentence.word_count > MAX_SENTENCE_WORDS:
                fail(
                    "word_limit",
                    f"line {line_number}, list sentence {ordinal}: "
                    f"{sentence.word_count} words exceed the limit "
                    f"{MAX_SENTENCE_WORDS}: {sentence.text}",
                )

    # Rule 8.1-inspired punctuation applies to all visible human text. Code,
    # formulas, and URL destinations were removed before this scan.
    for block in blocks:
        visible = " ".join(line.text.strip() for line in block)
        normalized = mask_inline(visible, keep_image_alt=True)
        if ";" in normalized:
            fail(
                "semicolon",
                f"lines {block[0].number}-{block[-1].number}: "
                "visible semicolon is not permitted",
            )

    census = {
        "direct_paragraphs": len(paragraphs),
        "direct_sentences": direct_sentences,
        "list_items": len(list_items),
        "list_sentences": list_sentences,
        "headings": headings,
        "tables": tables,
        "table_cells": table_cells,
        "display_math": display_math,
        "fenced_code": fenced_code,
        "media": media,
        "max_sentence_words": max_sentence_words,
        "max_paragraph_sentences": max_paragraph_sentences,
        "max_list_words": max_list_words,
    }
    if expected_census is not None:
        observed = {key: census[key] for key in expected_census}
        if observed != expected_census:
            fail(
                "census",
                f"checked-surface census changed: expected {expected_census}, "
                f"observed {observed}",
            )
    return census


def check_path(path: pathlib.Path) -> tuple[str, dict[str, int]]:
    input_stat = path.lstat()
    if stat.S_ISLNK(input_stat.st_mode) or not stat.S_ISREG(input_stat.st_mode):
        fail("input", f"source is absent, non-regular, or symbolic: {path}")
    resolved = path.resolve(strict=True)
    resolved_stat = resolved.lstat()
    if not stat.S_ISREG(resolved_stat.st_mode) or (
        input_stat.st_dev,
        input_stat.st_ino,
    ) != (resolved_stat.st_dev, resolved_stat.st_ino):
        fail("input", f"source identity changed while resolving: {path}")
    raw = resolved.read_bytes()
    text = decode_source(raw)
    census = audit_text(text, EXPECTED_CENSUS)
    return hashlib.sha256(raw).hexdigest(), census


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        print(f"usage: {pathlib.Path(sys.argv[0]).name} [source.md]", file=sys.stderr)
        return 2
    # Preserve the caller's final path component until check_path has applied
    # lstat. Resolving here would turn an optional symlink into an accepted file.
    source = pathlib.Path(argv[0]) if argv else DEFAULT_SOURCE
    try:
        digest, census = check_path(source)
    except (OSError, ProseCheckError) as error:
        code = error.code if isinstance(error, ProseCheckError) else "io"
        print(f"Mathematical results guide prose check failed [{code}]: {error}", file=sys.stderr)
        return 1
    ordered = " ".join(f"{key}={census[key]}" for key in EXPECTED_CENSUS)
    print(f"Mathematical results guide prose check passed: sha256={digest} {ordered}")
    print(
        "Observed maxima: "
        f"direct_words={census['max_sentence_words']} "
        f"paragraph_sentences={census['max_paragraph_sentences']} "
        f"list_words={census['max_list_words']}"
    )
    print(f"Boundary: {BOUNDARY}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
