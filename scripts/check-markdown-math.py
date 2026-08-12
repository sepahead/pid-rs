#!/usr/bin/env python3
"""Reject Markdown math syntax that does not render reliably on GitHub."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PRESERVED_EXTERNAL_MARKDOWN_SHA256 = {
    "audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.md": (
        "c289373b23aeb521952101e9143d924b60316ccece6ab9be84c2ff2b9b0ebe71"
    ),
}
LEGACY_DELIMITERS = (r"\[", r"\]", r"\(", r"\)")
FENCE = re.compile(r"^[ \t]*(?P<run>`{3,}|~{3,})")
BARE_TEX_COMMAND = re.compile(r"(?<!\\)\\[A-Za-z]+")
INLINE_DISPLAY_COMMANDS = (
    (re.compile(r"\\begin(?:\s|\{)"), r"\begin"),
    (re.compile(r"\\tag\*?(?:\s|\{)"), r"\tag"),
)
FORBIDDEN_GITHUB_MATH_COMMANDS = (
    (
        r"\operatorname",
        r"GitHub Markdown does not allow \operatorname; use \mathrm{...} "
        "or a built-in operator",
    ),
)
INLINE_MATH_LIMIT = 72
STRICT_THEORY_DOCS = frozenset(
    {
        "DEPENDENCY_COLORED_SXPID_CONCENTRATION.md",
        "FINITE_ALPHABET_PLUGIN_CONVERGENCE.md",
        "KNOWN_LIMITATIONS.md",
    }
)
RUSTDOC_INCLUDED_READMES = frozenset(
    {
        "crates/pid-core/README.md",
        "crates/pid-runlog/README.md",
    }
)
MATH_CODE_EXACT = frozenset(
    {
        "E",
        "I_min",
        "L1",
        "M",
        "Red°",
        "U",
        "Vul°",
        "alpha",
        "d",
        "delta",
        "epsilon",
        "m",
        "p",
        "p_min",
        "q",
        "r̄",
        "rho",
        "v̄",
    }
)
MATH_CODE_NOTATION = re.compile(
    r"""
    (?:<=|>=|->|[=+*^|])
    |(?:^|[^A-Za-z])-(?:[A-Za-z]|\d)
    |\b(?:exp|ln|log)\s*(?:\(|\d)
    |\b(?:Pr|supp)\s*\(
    |\bI\s*\(
    |\b(?:alpha|delta|epsilon|rho)\b
    |\b(?:D|F|I|P|V|p|r)_[A-Za-z0-9*]+
    |\b(?:Lambda)\s*\(
    |\b(?:dot)\b
    |\d\s*/\s*\d
    |\d+\.\d+
    |\[[A-Za-z_]+\s*,\s*[A-Za-z_]+\]
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


@dataclass(frozen=True)
class CodeSpan:
    start: int
    end: int
    content: str


@dataclass(frozen=True)
class InlineMath:
    start: int
    end: int
    content: str


def markdown_paths() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "*.md",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = []
    for raw in result.stdout.split(b"\0"):
        if raw:
            paths.append(ROOT / raw.decode("utf-8"))
    return sorted(paths)


def _backtick_run_end(line: str, start: int) -> int:
    end = start
    while end < len(line) and line[end] == "`":
        end += 1
    return end


def code_spans(line: str) -> list[CodeSpan]:
    """Return closed CommonMark-style backtick spans on one line."""
    spans: list[CodeSpan] = []
    index = 0
    while index < len(line):
        if line[index] != "`":
            index += 1
            continue
        opener_end = _backtick_run_end(line, index)
        opener_length = opener_end - index
        search = opener_end
        while search < len(line):
            next_run = line.find("`", search)
            if next_run < 0:
                index = opener_end
                break
            next_end = _backtick_run_end(line, next_run)
            if next_end - next_run == opener_length:
                spans.append(
                    CodeSpan(
                        start=index,
                        end=next_end,
                        content=line[opener_end:next_run],
                    )
                )
                index = next_end
                break
            search = next_end
        else:
            index = opener_end
    return spans


def mask_ranges(line: str, ranges: list[CodeSpan] | list[InlineMath]) -> str:
    output = list(line)
    for item in ranges:
        for position in range(item.start, item.end):
            output[position] = " "
    return "".join(output)


def without_code_spans(line: str) -> str:
    """Replace closed CommonMark backtick spans with spaces."""
    return mask_ranges(line, code_spans(line))


def _is_escaped(line: str, position: int) -> bool:
    slash_count = 0
    position -= 1
    while position >= 0 and line[position] == "\\":
        slash_count += 1
        position -= 1
    return slash_count % 2 == 1


def is_rustdoc_included_readme(path: Path) -> bool:
    """Return whether rustdoc includes this Markdown file as crate documentation."""
    normalized = path.as_posix()
    return any(
        normalized == relative or normalized.endswith(f"/{relative}")
        for relative in RUSTDOC_INCLUDED_READMES
    )


def inline_math_spans(line: str) -> tuple[list[InlineMath], int | None]:
    """Return same-line single-dollar spans and an unmatched opener, if any."""
    spans: list[InlineMath] = []
    opener: int | None = None
    index = 0
    while index < len(line):
        if line[index] != "$" or _is_escaped(line, index):
            index += 1
            continue
        if index + 1 < len(line) and line[index + 1] == "$":
            index += 2
            continue
        if index > 0 and line[index - 1] == "$":
            index += 1
            continue
        if opener is None:
            opener = index
        else:
            spans.append(
                InlineMath(
                    start=opener,
                    end=index + 1,
                    content=line[opener + 1 : index],
                )
            )
            opener = None
        index += 1
    return spans, opener


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    cells = stripped.strip("|").split("|")
    return len(cells) >= 2 and all(
        re.fullmatch(r"\s*:?-{3,}:?\s*", cell) is not None for cell in cells
    )


def table_line_numbers(lines: list[str]) -> set[int]:
    """Recognize pipe tables, including tables without outside pipes."""
    table_lines: set[int] = set()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|") or stripped.endswith("|"):
            table_lines.add(index + 1)
        if not _is_table_separator(without_code_spans(line)):
            continue
        table_lines.add(index + 1)
        if index > 0:
            table_lines.add(index)
        cursor = index + 1
        while cursor < len(lines):
            candidate = without_code_spans(lines[cursor])
            if not candidate.strip() or "|" not in candidate:
                break
            table_lines.add(cursor + 1)
            cursor += 1
    return table_lines


def looks_like_math_code(content: str) -> bool:
    """Identify formulas that were incorrectly formatted as code."""
    value = content.strip()
    if value in MATH_CODE_EXACT:
        return True
    if (
        "::" in value
        or "/" in value
        and re.search(r"[A-Za-z]\.[A-Za-z0-9]+$", value)
        or re.fullmatch(r"[a-z][a-z0-9_.-]*\s*=\s*[a-z][a-z0-9_.-]*", value)
    ):
        return False
    return MATH_CODE_NOTATION.search(value) is not None


def reject_forbidden_math_commands(
    findings: list[Finding],
    path: Path,
    line: int,
    content: str,
) -> None:
    """Reject TeX commands that GitHub's safe MathJax configuration blocks."""
    for command, message in FORBIDDEN_GITHUB_MATH_COMMANDS:
        if command in content:
            findings.append(Finding(path, line, message))


def inspect(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    fence_character: str | None = None
    fence_length = 0
    display_open_line: int | None = None
    display_has_content = False
    lines = path.read_text(encoding="utf-8").splitlines()
    table_lines = table_line_numbers(lines)
    strict_code_spans = path.name in STRICT_THEORY_DOCS
    rustdoc_readme = is_rustdoc_included_readme(path)

    for number, line in enumerate(lines, start=1):
        fence_match = FENCE.match(line)
        if fence_match:
            run = fence_match.group("run")
            if fence_character is None:
                fence_character = run[0]
                fence_length = len(run)
            elif (
                run[0] == fence_character
                and len(run) >= fence_length
                and not line[fence_match.end() :].strip()
            ):
                fence_character = None
                fence_length = 0
            continue
        if fence_character is not None:
            continue

        spans = code_spans(line)
        if strict_code_spans:
            for span in spans:
                if looks_like_math_code(span.content):
                    findings.append(
                        Finding(
                            path,
                            number,
                            "format mathematical notation as math, not as a code span",
                        )
                    )

        prose = mask_ranges(line, spans)
        if rustdoc_readme and any(
            character == "$" and not _is_escaped(prose, position)
            for position, character in enumerate(prose)
        ):
            findings.append(
                Finding(
                    path,
                    number,
                    "rustdoc-included README cannot use dollar-delimited math; "
                    "use Unicode, HTML, or code notation",
                )
            )
        for delimiter in LEGACY_DELIMITERS:
            if delimiter in prose:
                findings.append(
                    Finding(
                        path,
                        number,
                        f"use GitHub math delimiters instead of {delimiter!r}",
                    )
                )

        if "$$" in prose:
            if prose.strip() != "$$":
                findings.append(
                    Finding(
                        path,
                        number,
                        "put each display-math delimiter on a line by itself",
                    )
                )
                continue
            if display_open_line is None:
                display_open_line = number
                display_has_content = False
            else:
                if not display_has_content:
                    findings.append(
                        Finding(
                            path,
                            display_open_line,
                            "display-math block is empty",
                        )
                    )
                display_open_line = None
                display_has_content = False
            continue

        if display_open_line is not None:
            reject_forbidden_math_commands(findings, path, number, prose)
            if prose.strip():
                display_has_content = True
            continue

        math_spans, unmatched = inline_math_spans(prose)
        if unmatched is not None:
            findings.append(
                Finding(
                    path,
                    number,
                    "single-dollar inline-math delimiter is not balanced on this line",
                )
            )

        for math_span in math_spans:
            reject_forbidden_math_commands(
                findings,
                path,
                number,
                math_span.content,
            )
            if len(math_span.content.strip()) > INLINE_MATH_LIMIT:
                findings.append(
                    Finding(
                        path,
                        number,
                        f"inline math exceeds {INLINE_MATH_LIMIT} characters; use display math",
                    )
                )
            for pattern, command in INLINE_DISPLAY_COMMANDS:
                if pattern.search(math_span.content):
                    findings.append(
                        Finding(
                            path,
                            number,
                            f"{command} is display-only; use a display-math block",
                        )
                    )
            if r"\\" in math_span.content:
                findings.append(
                    Finding(
                        path,
                        number,
                        "a TeX line break is display-only; use a display-math block",
                    )
                )
            if number in table_lines and "|" in math_span.content:
                findings.append(
                    Finding(
                        path,
                        number,
                        r"use \lvert, \rvert, or \mid instead of a raw pipe in table math",
                    )
                )

        outside_math = mask_ranges(prose, math_spans)
        if unmatched is not None:
            outside_math = outside_math[:unmatched] + " " * (
                len(outside_math) - unmatched
            )
        bare_command = BARE_TEX_COMMAND.search(outside_math)
        if bare_command is not None:
            findings.append(
                Finding(
                    path,
                    number,
                    f"put bare TeX command {bare_command.group(0)!r} inside math delimiters",
                )
            )

    if fence_character is not None:
        findings.append(Finding(path, len(lines), "Markdown code fence is not closed"))
    if display_open_line is not None:
        findings.append(
            Finding(path, display_open_line, "display-math block is not closed")
        )
    return findings


def inspect_repository_path(path: Path, *, root: Path = ROOT) -> list[Finding]:
    """Inspect repository prose or exact-bind a preserved external submission.

    The external-model audit is retained byte-for-byte as advisory evidence. Its embedded TeX
    preamble is not repository-authored GitHub Markdown and must not be silently rewritten to pass
    this style gate. Only the exact submitted bytes are exempt; any drift fails closed.
    """
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return [Finding(path, 1, "Markdown path is outside the repository root")]
    expected = PRESERVED_EXTERNAL_MARKDOWN_SHA256.get(relative)
    if expected is None:
        return inspect(path)
    try:
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        return [Finding(path, 1, f"cannot read preserved external Markdown: {error}")]
    if observed != expected:
        return [
            Finding(
                path,
                1,
                "preserved external Markdown exact-byte custody drifted: "
                f"expected {expected}, observed {observed}",
            )
        ]
    return []


def main() -> int:
    findings = [
        finding
        for path in markdown_paths()
        for finding in inspect_repository_path(path)
    ]
    if findings:
        for finding in findings:
            relative = finding.path.relative_to(ROOT)
            print(f"{relative}:{finding.line}: {finding.message}", file=sys.stderr)
        print(
            f"Markdown math check failed with {len(findings)} finding(s)",
            file=sys.stderr,
        )
        return 1
    print(
        "OK: Markdown math uses portable GitHub delimiters, commands, "
        "and bounded inline math"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
