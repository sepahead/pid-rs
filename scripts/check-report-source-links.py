"""Check that the public-report link filter changes only real prose links."""

import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "audit/formal/latex/report-source-links.lua"
BASE = "https://github.com/sepahead/pid-rs/blob/main/"
READER = "markdown-implicit_figures-smart+raw_tex+tex_math_dollars"
SOURCE = (
    "Read [the earlier proof](../previous/EXPOSITION.md#section) and "
    "[the source article](https://doi.org/10.1103/PhysRevE.110.014115).\n\n"
    "The ratio is $[3(2j+1)/(2j+2)](3/4)^{2j-1}$.\n\n"
    "$$\n[p+q](q/p)\n$$\n\n"
    "Code uses `[field](file)`.\n\n"
    "```text\n[example](code)\n```\n"
)


def parse(markdown, *, filtered):
    argv = ["pandoc", "--from", READER, "--to", "json"]
    if filtered:
        argv.extend(["--lua-filter", str(FILTER)])
    return subprocess.run(
        argv,
        input=markdown,
        text=True,
        capture_output=True,
        env={**os.environ, "PID_RS_REPORT_SOURCE_DIR": "audit/research/current"},
        timeout=30,
        check=False,
    )


def links(value):
    if isinstance(value, dict):
        if value.get("t") == "Link":
            yield value["c"][-1]
        else:
            for child in value.values():
                yield from links(child)
    elif isinstance(value, list):
        for child in value:
            yield from links(child)


def main():
    ordinary = parse(SOURCE, filtered=False)
    filtered = parse(SOURCE, filtered=True)
    if ordinary.returncode or filtered.returncode:
        raise ValueError(ordinary.stderr + filtered.stderr)
    expected = json.loads(ordinary.stdout)
    prose = list(links(expected))
    if len(prose) != 2 or prose[0][0] != "../previous/EXPOSITION.md#section":
        raise ValueError("unexpected Pandoc reference parse")
    prose[0][0] = BASE + "audit/research/previous/EXPOSITION.md#section"
    if json.loads(filtered.stdout) != expected:
        raise ValueError("a mathematical, code, or unrelated prose node changed")

    bad_targets = [
        "../../../../outside.md",
        "/absolute/file",
        "file:///outside",
        "http://example.com",
        "//example.com/file",
        "../%2e%2e/elsewhere",
    ]
    for target in bad_targets:
        if parse(f"[source]({target})", filtered=True).returncode == 0:
            raise ValueError(f"unexpectedly accepted source link {target}")
    print("Public report links passed with unchanged math and code and six rejected destinations.")


if __name__ == "__main__":
    main()
