#!/usr/bin/env python3
"""Exercise the canonical v4 Pandoc projection and its file-custody contract.

The retained raw-TeX fixture is an exact producer observation. These tests do
not compile TeX, execute fixture commands, validate mathematics, or establish
PDF accessibility. The historical normalizer and self-test stay independent.
Run this file under normal Python and under ``python3 -O``.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
NORMALIZER = ROOT / "scripts/normalize-mathematical-results-guide-pandoc-tex-v4.py"
FIXTURE = ROOT / "audit/evidence/mathematical-results-guide-pandoc-3.10.2-v4-normalizer-input.tex"
FIXTURE_SHA256 = "d17cd98eb82ab69cd43e53377a4da1def4dd36d3c2d8bff84a609a9e42a74aee"
VERSION = "pandoc 3.10.2"
FAILURE_PREFIX = "Pandoc TeX normalization failed: "


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("Pandoc v4 normalizer self-test failed: " + message)


def load_normalizer():
    require(NORMALIZER.is_file() and not NORMALIZER.is_symlink(), "normalizer is not regular")
    spec = importlib.util.spec_from_file_location("guide_v4_normalizer", NORMALIZER)
    require(spec is not None and spec.loader is not None, "cannot load normalizer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(call, name: str) -> None:
    try:
        call()
    except SystemExit as error:
        require(str(error).startswith(FAILURE_PREFIX), name + ": wrong rejection")
    except OSError:
        # The CLI also rejects native filesystem errors rather than overwriting.
        pass
    else:
        require(False, name + ": unexpectedly accepted")


def main() -> None:
    require(FIXTURE.is_file() and not FIXTURE.is_symlink(), "fixture is not regular")
    raw = FIXTURE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, "fixture identity changed")
    normalizer_bytes = NORMALIZER.read_bytes()
    module = load_normalizer()
    text = raw.decode("utf-8")
    heading_pattern = re.compile(
        r"\\(section|subsection|subsubsection)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
        r"\\label\{([^{}]+)\}\n"
    )
    headings = list(heading_pattern.finditer(text))
    require(len(headings) == 30, "retained fixture lost its 30 headings")
    require(tuple(m.group(3) for m in headings) == module.EXPECTED_HEADING_IDS,
            "declared heading IDs differ from the retained producer observation")
    require({m.group(3): m.group(1) for m in headings} == module.EXPECTED_HEADING_COMMANDS,
            "declared heading classes differ from the retained producer observation")
    require(text.count(module.LONGTABLE_BEGIN) == text.count(module.LONGTABLE_END) == 5,
            "retained fixture lost its five complete tables")
    mode, normalized = module.normalize(text, VERSION)
    require(mode == "canonical" and normalized.encode() == raw, "canonical bytes changed")
    names = ["canonical_exact_fixture"]

    def content(name: str, altered: str, version: str = VERSION) -> None:
        require(altered != text or version != VERSION, name + ": inert mutation")
        reject(lambda: module.normalize(altered, version), name)
        names.append(name)

    for index, match in enumerate(headings):
        token = match.group(0)
        content(f"missing_heading_{index:02d}", text.replace(token, "", 1))
        content(f"duplicate_heading_{index:02d}", text.replace(token, token + token, 1))
        replacement = "subsection" if match.group(1) != "subsection" else "section"
        content(f"wrong_heading_class_{index:02d}",
                text[:match.start()] + token.replace("\\" + match.group(1), "\\" + replacement, 1)
                + text[match.end():])
        content(f"unknown_heading_id_{index:02d}",
                text.replace("\\label{" + match.group(3) + "}", "\\label{unreviewed-heading}", 1))
    first, second = (headings[i].group(0) for i in (0, 1))
    content("reordered_heading_blocks", text.replace(first, "__SWAP__", 1)
            .replace(second, first, 1).replace("__SWAP__", second, 1))
    for command in ("section", "subsection", "subsubsection", "paragraph", "chapter", "part"):
        extra = "\\" + command + "{Unexpected}\\label{unreviewed-extra-heading}\n"
        content("additional_" + command, text.replace(module.DOCUMENT_END, extra + module.DOCUMENT_END, 1))
    content("additional_spaced_section", text.replace(module.DOCUMENT_END,
            "\\section {Unexpected}\\label{extra-spaced}\n" + module.DOCUMENT_END, 1))
    content("starred_existing_section", text.replace("\\section{", "\\section*{", 1))
    content("missing_table_wrapper", text.replace(module.TABLE_WRAPPER, "", 1))
    content("extra_table_wrapper", text.replace(module.TABLE_WRAPPER, module.TABLE_WRAPPER * 2, 1))
    content("table_begin_drift", text.replace(module.LONGTABLE_BEGIN, "\\begin{longtable}{l}\n", 1))
    content("missing_table_end", text.replace(module.LONGTABLE_END, "", 1))
    content("table_nesting", text.replace(module.LONGTABLE_BEGIN,
            module.LONGTABLE_BEGIN + module.LONGTABLE_BEGIN, 1))
    content("missing_closing_wrapper", text.replace(module.LONGTABLE_END + "}\n", module.LONGTABLE_END, 1))
    content("moved_opening_wrapper", text.replace(module.TABLE_WRAPPER,
            module.TABLE_WRAPPER + "% separation\n", 1))
    for label, token in (("counter", module.NONE_COUNTER), ("table_preamble", module.CANONICAL_TABLE_PREAMBLE),
                         ("image_preamble", module.CANONICAL_IMAGE_PREAMBLE),
                         ("crosswalk_prefix", module.CROSSWALK_FRAME_PREFIX),
                         ("crosswalk_suffix", module.CROSSWALK_FRAME_SUFFIX),
                         ("crosswalk", module.CANONICAL_CROSSWALK),
                         ("document_begin", module.DOCUMENT_BEGIN), ("document_end", module.DOCUMENT_END)):
        content("missing_" + label, text.replace(token, "", 1))
        content("duplicate_" + label, text.replace(token, token * 2, 1))
    content("trailing_document_bytes", text + "% after end\n")
    content("missing_final_lf", text.rstrip("\n"))
    content("legacy_version_refusal", text, "pandoc 3.1.3")
    content("unknown_version_refusal", text, "pandoc 3.10.3")
    content("invalid_version_refusal", text, "pandoc 3.10.2\n")

    physical_temp = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="pid-rs-guide-normalizer-v4-", dir=physical_temp) as temporary:
        base = Path(temporary)

        def invoke(source: Path, destination: Path) -> str:
            previous = sys.argv
            output = io.StringIO()
            try:
                sys.argv = [str(NORMALIZER), VERSION, str(source), str(destination)]
                with contextlib.redirect_stdout(output):
                    module.main()
            finally:
                sys.argv = previous
            return output.getvalue()

        source = base / "input.tex"
        source.write_bytes(raw)
        destination = base / "output.tex"
        output = invoke(source, destination)
        require(destination.read_bytes() == raw and source.read_bytes() == raw,
                "canonical filesystem pass changed bytes")
        require("byte_identity=yes" in output and destination.stat().st_nlink == 1,
                "canonical receipt or output identity changed")
        names.append("canonical_filesystem_identity")
        reject(lambda: invoke(source, destination), "existing_output")
        require(destination.read_bytes() == raw, "existing output was overwritten")
        names.append("existing_output")
        reject(lambda: invoke(source, source), "same_path")
        names.append("same_path")
        for name in ("symlink_input", "hardlink_input", "fifo_input", "directory_input", "absent_input"):
            bad = base / name
            if name == "symlink_input": bad.symlink_to(source)
            elif name == "hardlink_input": os.link(source, bad)
            elif name == "fifo_input": os.mkfifo(bad)
            elif name == "directory_input": bad.mkdir()
            target = base / (name + "-output")
            reject(lambda: invoke(bad, target), name)
            require(not target.exists() and not target.is_symlink(), name + ": output appeared")
            if name == "hardlink_input": bad.unlink()
            names.append(name)
        for name in ("symlink_output", "fifo_output", "directory_output", "symlink_parent"):
            bad = base / name
            if name == "symlink_output": bad.symlink_to(source)
            elif name == "fifo_output": os.mkfifo(bad)
            elif name == "directory_output": bad.mkdir()
            else:
                parent = base / "physical-parent"; parent.mkdir(); bad.symlink_to(parent, target_is_directory=True)
                bad = bad / "out.tex"
            reject(lambda: invoke(source, bad), name)
            require(source.read_bytes() == raw, name + ": source changed")
            if name == "symlink_parent": require(not bad.exists(), "symlink parent wrote output")
            names.append(name)
        original_write = module.write_exclusive
        def write_then_mutate(*args):
            result = original_write(*args)
            source.write_bytes(raw + b"\n% concurrent mutation\n")
            return result
        module.write_exclusive = write_then_mutate
        target = base / "mutated-source-output.tex"
        try: reject(lambda: invoke(source, target), "source_mutation_after_write")
        finally: module.write_exclusive = original_write; source.write_bytes(raw)
        require(not target.exists(), "source mutation did not remove owned output")
        names.append("source_mutation_after_write")
        def write_then_corrupt(*args):
            result = original_write(*args)
            Path(args[0]).write_bytes(b"corrupted output\n")
            return result
        module.write_exclusive = write_then_corrupt
        target = base / "corrupted-output.tex"
        try: reject(lambda: invoke(source, target), "published_output_corruption")
        finally: module.write_exclusive = original_write
        require(not target.exists(), "corrupt owned output was retained")
        names.append("published_output_corruption")

    require(FIXTURE.read_bytes() == raw and NORMALIZER.read_bytes() == normalizer_bytes,
            "fixture or normalizer changed during controls")
    require(len(names) == len(set(names)), "duplicate control names")
    print(json.dumps({"status": "passed", "controls": names, "count": len(names),
                      "fixture_sha256": FIXTURE_SHA256,
                      "normalizer_sha256": hashlib.sha256(normalizer_bytes).hexdigest(),
                      "python_optimized": bool(sys.flags.optimize),
                      "scope": "canonical projection and bounded file-custody controls"}, sort_keys=True))


if __name__ == "__main__":
    main()
