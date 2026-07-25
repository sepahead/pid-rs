#!/usr/bin/env python3
"""Fail closed when the formal-PDF visual-system contract drifts.

This checker is intentionally syntactic.  It protects the shared academic
visual system, explicit table-header bands, and the absence of vertical table
rules.  It does not establish that a table is readable after rendering and it
does not validate any mathematical or scientific claim.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


DEFAULT_ROOT = Path(__file__).resolve().parent.parent
LATEX_RELATIVE = Path("audit/formal/latex")
STYLE_NAME = "pid-rs-report-tables.sty"
WORKFLOW_NAME = "mathematical-problem-solving-workflow.tex"
EXPECTED = (
    "certified-sxpid2-executable-assurance.tex",
    "dependency-colored-sxpid-concentration.tex",
    "ecosystem-compatibility-audit.tex",
    "exact-log-product-sxpid2-assurance.tex",
    "finite-alphabet-plugin-convergence.tex",
    "formal-tool-adoption-audit.tex",
    "foundational-shared-exclusions-pid-audit.tex",
    "mathematical-problem-solving-workflow.tex",
    "support-change-tolerant-averaged-sxpid-continuity.tex",
)
REQUIRED_DOCUMENT_COMMANDS = (
    r"\usepackage{pid-rs-report-tables}",
    r"\PidConfigureSections",
    r"\PidSetRunningHeads",
    r"\PidConfigureAbstract",
    r"\PidConfigureLinksAndListings",
    r"\PidReportTitle",
    r"\PidMakeTitle",
)
REQUIRED_STYLE_MARKERS = (
    r"\definecolor{PidPrimary}{HTML}{194F7A}",
    r"\definecolor{PidTableHeader}{HTML}{CBDDE7}",
    r"\definecolor{PidTableStripe}{HTML}{E5EDF2}",
    r"\AtBeginEnvironment{tabular}{\PidTableRowBands}",
    r"\AtBeginEnvironment{tabularx}{\PidTableRowBands}",
    r"\AtBeginEnvironment{longtable}{\PidTableRowBands}",
    r"\newcommand{\PidTableHeaderRow}{\rowcolor{PidTableHeader}}",
    "PID-RS TECHNICAL REPORT SERIES",
)
TOPRULE_REDEFINITION = re.compile(
    r"\\(?:re)?newcommand\s*\{\\toprule\}"
    r"|\\providecommand\s*\{\\toprule\}"
    r"|\\def\s*\\toprule\b"
    r"|\\let\s*\\toprule\b"
)
VERTICAL_RULE = re.compile(r"\\(?:hline|cline|vline)\b")
VERTICAL_COLUMN = re.compile(
    r"\\begin\{(?:tabular|tabularx|longtable)\}"
    r"(?:\{[^{}]*\})?\{[^\n}]*\|"
)
WORKFLOW_MARKDOWN_HOOK = (
    r"\def\markdownLaTeXTopRule{\toprule\PidTableHeaderRow}%"
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int | None
    message: str


def display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def check_style(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not path.is_file():
        return [Finding(path, None, "shared visual-system package is missing")]
    text = path.read_text(encoding="utf-8")
    for marker in REQUIRED_STYLE_MARKERS:
        if text.count(marker) != 1:
            findings.append(
                Finding(path, None, f"required style marker must occur once: {marker}")
            )
    if TOPRULE_REDEFINITION.search(text):
        findings.append(
            Finding(path, None, r"the shared package must not redefine \toprule")
        )
    return findings


def check_document(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for command in REQUIRED_DOCUMENT_COMMANDS:
        count = text.count(command)
        if count != 1:
            findings.append(
                Finding(path, None, f"required command must occur once: {command} (found {count})")
            )

    for match in TOPRULE_REDEFINITION.finditer(text):
        findings.append(
            Finding(
                path,
                line_number(text, match.start()),
                r"documents must not redefine \toprule",
            )
        )
    for match in VERTICAL_RULE.finditer(text):
        findings.append(
            Finding(
                path,
                line_number(text, match.start()),
                "vertical/legacy table rule is forbidden; use booktabs and row bands",
            )
        )
    for match in VERTICAL_COLUMN.finditer(text):
        findings.append(
            Finding(
                path,
                line_number(text, match.start()),
                "vertical table-column rules are forbidden",
            )
        )

    explicit_toprules = 0
    explicit_headers = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        command = stripped[:-1].rstrip() if stripped.endswith("%") else stripped
        if command == r"\toprule":
            explicit_toprules += 1
            next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
            next_command = next_line[:-1].rstrip() if next_line.endswith("%") else next_line
            if next_command != r"\PidTableHeaderRow":
                findings.append(
                    Finding(
                        path,
                        index + 1,
                        r"every explicit \toprule must be followed immediately by "
                        r"\PidTableHeaderRow",
                    )
                )
        if command == r"\PidTableHeaderRow":
            explicit_headers += 1
            previous_line = lines[index - 1].strip() if index > 0 else ""
            previous_command = (
                previous_line[:-1].rstrip() if previous_line.endswith("%") else previous_line
            )
            if previous_command != r"\toprule":
                findings.append(
                    Finding(
                        path,
                        index + 1,
                        r"an explicit \PidTableHeaderRow must immediately follow \toprule",
                    )
                )
            next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
            next_command = next_line[:-1].rstrip() if next_line.endswith("%") else next_line
            if next_command == r"\PidTableHeaderRow":
                findings.append(
                    Finding(path, index + 2, "duplicate adjacent table-header band")
                )

    if explicit_toprules != explicit_headers:
        findings.append(
            Finding(
                path,
                None,
                "explicit top-rule/header-band counts differ: "
                f"{explicit_toprules} != {explicit_headers}",
            )
        )

    if path.name == WORKFLOW_NAME:
        if text.count(WORKFLOW_MARKDOWN_HOOK) != 1:
            findings.append(
                Finding(
                    path,
                    None,
                    "the Markdown-generated table-header hook must occur exactly once",
                )
            )
    elif r"\markdownLaTeXTopRule" in text:
        findings.append(
            Finding(path, None, "Markdown table hook is permitted only in the workflow paper")
        )

    return findings


def check(root: Path) -> list[Finding]:
    latex_dir = root / LATEX_RELATIVE
    actual = tuple(path.name for path in sorted(latex_dir.glob("*.tex")))
    findings: list[Finding] = []
    if actual != EXPECTED:
        findings.append(
            Finding(
                latex_dir,
                None,
                "formal LaTeX inventory differs from the declared visual-system set: "
                f"expected {EXPECTED!r}, found {actual!r}",
            )
        )
        return findings

    findings.extend(check_style(latex_dir / STYLE_NAME))
    for name in EXPECTED:
        findings.extend(check_document(latex_dir / name))
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    findings = check(root)
    if findings:
        for finding in findings:
            location = display_path(finding.path, root)
            if finding.line is not None:
                location = f"{location}:{finding.line}"
            print(f"{location}: {finding.message}", file=sys.stderr)
        return 1
    print(
        "OK: all nine formal papers use the shared visual system, explicit header bands, "
        "and no vertical table rules"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
