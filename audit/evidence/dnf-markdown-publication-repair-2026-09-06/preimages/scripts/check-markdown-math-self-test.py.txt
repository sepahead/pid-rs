#!/usr/bin/env python3
"""Failure-injection tests for check-markdown-math.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-markdown-math.py"


def load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_markdown_math", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker()
MUTATION_COUNT = 0
PASSING_FIXTURE_COUNT = 0


def findings(source: str, name: str = "fixture.md") -> list[object]:
    with tempfile.TemporaryDirectory(prefix="pid-rs-markdown-math-") as raw:
        path = Path(raw) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return CHECKER.inspect(path)


def expect_failure(
    name: str,
    source: str,
    expected: str,
    *,
    filename: str = "fixture.md",
) -> None:
    global MUTATION_COUNT
    actual = findings(source, filename)
    messages = [item.message for item in actual]
    if expected not in messages:
        raise RuntimeError(f"{name}: expected {expected!r}, got {messages!r}")
    MUTATION_COUNT += 1


def expect_success(name: str, source: str, *, filename: str = "fixture.md") -> None:
    global PASSING_FIXTURE_COUNT
    actual = findings(source, filename)
    if actual:
        messages = [f"{item.line}: {item.message}" for item in actual]
        raise RuntimeError(f"{name}: expected success, got {messages!r}")
    PASSING_FIXTURE_COUNT += 1


def main() -> int:
    expect_failure(
        "legacy-delimiter",
        r"Use \[x\] here." + "\n",
        r"use GitHub math delimiters instead of '\\['",
    )
    expect_failure(
        "display-delimiter-placement",
        "Prefix $$\n",
        "put each display-math delimiter on a line by itself",
    )
    expect_failure(
        "empty-display",
        "$$\n$$\n",
        "display-math block is empty",
    )
    expect_failure(
        "unclosed-display",
        "$$\nx+y\n",
        "display-math block is not closed",
    )
    expect_failure(
        "unclosed-fence",
        "```text\n$x$\n",
        "Markdown code fence is not closed",
    )
    expect_failure(
        "unbalanced-inline",
        "Use $x here.\n",
        "single-dollar inline-math delimiter is not balanced on this line",
    )
    expect_failure(
        "bare-tex",
        r"Use \alpha without delimiters." + "\n",
        r"put bare TeX command '\\alpha' inside math delimiters",
    )
    expect_failure(
        "raw-table-pipe",
        "| Value |\n| --- |\n| $|x|$ |\n",
        r"use \lvert, \rvert, or \mid instead of a raw pipe in table math",
    )
    expect_failure(
        "raw-table-pipe-without-outside-pipes",
        "Quantity | Value\n--- | ---\nNorm | $|x|$\n",
        r"use \lvert, \rvert, or \mid instead of a raw pipe in table math",
    )
    expect_failure(
        "long-inline",
        "$" + "x" * 73 + "$\n",
        "inline math exceeds 72 characters; use display math",
    )
    expect_failure(
        "inline-begin",
        r"$\begin{aligned}x\end{aligned}$" + "\n",
        r"\begin is display-only; use a display-math block",
    )
    expect_failure(
        "inline-tag",
        r"$x\tag{1}$" + "\n",
        r"\tag is display-only; use a display-math block",
    )
    expect_failure(
        "inline-line-break",
        r"$x \\ y$" + "\n",
        "a TeX line break is display-only; use a display-math block",
    )
    forbidden_operator_message = (
        r"GitHub Markdown does not allow \operatorname; use \mathrm{...} "
        "or a built-in operator"
    )
    expect_failure(
        "forbidden-operator-inline",
        r"Use $\operatorname{supp}(P)$." + "\n",
        forbidden_operator_message,
    )
    expect_failure(
        "forbidden-operator-display",
        "$$\n" + r"\operatorname{supp}(P)" + "\n$$\n",
        forbidden_operator_message,
    )
    expect_failure(
        "math-as-code",
        "Assume `delta <= p_min/2`.\n",
        "format mathematical notation as math, not as a code span",
        filename="DEPENDENCY_COLORED_SXPID_CONCENTRATION.md",
    )
    expect_failure(
        "rustdoc-readme-dollar-math",
        "Mutual information is $I(X;Y)$.\n",
        (
            "rustdoc-included README cannot use dollar-delimited math; "
            "use Unicode, HTML, or code notation"
        ),
        filename="crates/pid-core/README.md",
    )

    expect_success(
        "aligned-display",
        (
            "The inline value is $x+y$.\n"
            "\n"
            "$$\n"
            r"\begin{aligned}" + "\n"
            r"x &= y + z \\" + "\n"
            r"  &= 2z." + "\n"
            r"\end{aligned}" + "\n"
            "$$\n"
            "\n"
            "| Quantity | Value |\n"
            "| --- | --- |\n"
            r"| Norm | $\lvert x\rvert$ |" + "\n"
        ),
    )
    expect_success(
        "literal-code",
        (
            "`stable::categorical::discrete_sxpid2` is an API.\n"
            "`scripts/check-markdown-math.py` is a path.\n"
            "```text\n"
            r"\[not parsed as math\]" + "\n"
            "$not-parsed\n"
            "```\n"
        ),
        filename="KNOWN_LIMITATIONS.md",
    )
    expect_success(
        "escaped-dollar",
        r"The literal price marker is \$5." + "\n",
    )
    expect_success(
        "portable-upright-name",
        r"Use $\mathrm{supp}(P)$." + "\n",
    )
    expect_success(
        "rustdoc-readme-code-dollar",
        "`$NAME` is a literal environment-variable token.\n",
        filename="crates/pid-runlog/README.md",
    )

    external_relative = next(iter(CHECKER.PRESERVED_EXTERNAL_MARKDOWN_SHA256))
    external_source = ROOT / external_relative
    with tempfile.TemporaryDirectory(prefix="pid-rs-preserved-markdown-") as raw:
        fixture_root = Path(raw)
        fixture = fixture_root / external_relative
        fixture.parent.mkdir(parents=True, exist_ok=True)
        exact = external_source.read_bytes()
        fixture.write_bytes(exact)
        exact_findings = CHECKER.inspect_repository_path(fixture, root=fixture_root)
        if exact_findings:
            raise RuntimeError(
                "preserved-external-exact: expected success, got "
                f"{[item.message for item in exact_findings]!r}"
            )
        global PASSING_FIXTURE_COUNT
        PASSING_FIXTURE_COUNT += 1

        fixture.write_bytes(exact + b"\n")
        drift_findings = CHECKER.inspect_repository_path(fixture, root=fixture_root)
        drift_messages = [item.message for item in drift_findings]
        if not any(
            message.startswith("preserved external Markdown exact-byte custody drifted:")
            for message in drift_messages
        ):
            raise RuntimeError(
                "preserved-external-drift: expected exact-byte rejection, got "
                f"{drift_messages!r}"
            )
        global MUTATION_COUNT
        MUTATION_COUNT += 1

    print(
        "OK: Markdown math checker rejected "
        f"{MUTATION_COUNT} mutations and accepted "
        f"{PASSING_FIXTURE_COUNT} valid fixtures"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
