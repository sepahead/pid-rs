#!/usr/bin/env python3
"""Source-only controls for the workflow Markdown parser preparation helper."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
ROOT = SCRIPT_DIRECTORY.parent
HELPER = SCRIPT_DIRECTORY / "prepare-mathematical-workflow-markdown-parser.py"
PROFILES = ROOT / "audit/formal/workflow-markdown-parser-profiles.json"
LOADER = ROOT / "audit/formal/latex/pid-rs-markdown-gc-loader.lua"


def audit(event: str, _arguments: tuple[object, ...]) -> None:
    forbidden = (
        "ctypes.dlopen",
        "os.exec",
        "os.posix_spawn",
        "os.spawn",
        "os.system",
        "socket.connect",
        "subprocess.",
    )
    if event.startswith(forbidden):
        raise RuntimeError(f"forbidden source-control side effect: {event}")


sys.addaudithook(audit)
spec = importlib.util.spec_from_file_location("workflow_markdown_parser_helper", HELPER)
if spec is None or spec.loader is None:
    raise SystemExit("workflow Markdown parser self-test: cannot load helper source")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

PASS_COUNT = 0


def pass_case(label: str) -> None:
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"ok {PASS_COUNT} - {label}")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise RuntimeError(detail)


def expect_failure(label: str, fragment: str, operation) -> None:
    try:
        operation()
    except helper.Failure as error:
        require(fragment in str(error), f"{label}: wrong failure: {error}")
    else:
        raise RuntimeError(f"{label}: unexpectedly accepted")
    pass_case(label)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def synthetic_source(version: str = "1.2.3-test") -> bytes:
    return (
        b"local metadata = {\n"
        + f'    version   = "{version}",\n'.encode("ascii")
        + b"}\n"
        + b"local self = { parser_functions = {} }\n"
        + helper.CREATE_PARSER
        + helper.CALLBACK
        + helper.NEXT_STATEMENT
        + b"        str = str\n"
        + b"      end\n"
        + helper.MATCH
        + b"      return res\n"
        + b"    end\n"
        + b"  end\n"
        + b"return { metadata = metadata }\n"
    )


def synthetic_document(source: bytes, version: str = "1.2.3-test") -> dict[str, object]:
    candidate = source.replace(helper.ANCHOR, helper.REPLACEMENT, 1)
    return {
        "profiles": [
            {
                "id": "synthetic-markdown-1.2.3-test",
                "metadata_version": version,
                "postimage_bytes": len(candidate),
                "postimage_sha256": hashlib.sha256(candidate).hexdigest(),
                "preimage_bytes": len(source),
                "preimage_sha256": hashlib.sha256(source).hexdigest(),
                "source": "source-only synthetic control",
            }
        ],
        "schema": helper.SCHEMA,
    }


def write(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def mutate_document(path: Path, operation) -> None:
    document = json.loads(path.read_bytes())
    operation(document)
    write(path, canonical_json(document))


def test_transform_contract(temporary: Path) -> tuple[Path, Path, Path, Path, dict[str, object]]:
    source = temporary / "markdown.lua"
    profiles = temporary / "profiles.json"
    output_root = temporary / "private"
    output_root.mkdir()
    output = output_root / helper.OUTPUT_NAME
    receipt = output_root / helper.RECEIPT_NAME
    source_bytes = synthetic_source()
    document = synthetic_document(source_bytes)
    write(source, source_bytes)
    write(profiles, canonical_json(document))
    identified = helper.identify(profiles, source, None)
    require(identified["id"] == "synthetic-markdown-1.2.3-test", "identify selected wrong profile")
    pass_case("identify admits the exact synthetic preimage")
    transformed = helper.transform(profiles, source, output, receipt, identified["id"])
    require(transformed == identified, "transform returned a different profile")
    require(output.read_bytes() == source_bytes.replace(helper.ANCHOR, helper.REPLACEMENT, 1),
            "transform bytes differ")
    require((output.stat().st_mode & 0o777) == 0o444, "candidate mode differs")
    require((receipt.stat().st_mode & 0o777) == 0o444, "receipt mode differs")
    pass_case("transform publishes only the exact read-only insertion and receipt")
    verified = helper.verify_transform(profiles, source, output, receipt, identified["id"])
    require(verified == identified, "transform replay selected a different profile")
    pass_case("transform replay binds source, candidate, and receipt")
    return source, profiles, output, receipt, document


def test_manifest_failures(temporary: Path, source: Path, base_document: dict[str, object]) -> None:
    malformed = temporary / "malformed.json"
    write(malformed, json.dumps(base_document).encode("ascii"))
    expect_failure(
        "noncanonical profile JSON is rejected",
        "not canonical JSON",
        lambda: helper.load_profiles(malformed),
    )

    wrong_schema = temporary / "wrong-schema.json"
    write(wrong_schema, canonical_json({**base_document, "schema": "wrong"}))
    expect_failure(
        "wrong profile schema is rejected",
        "schema or profile array differs",
        lambda: helper.load_profiles(wrong_schema),
    )

    extra_key = temporary / "extra-key.json"
    document = json.loads(canonical_json(base_document))
    document["unexpected"] = True
    write(extra_key, canonical_json(document))
    expect_failure(
        "unknown profile-manifest keys are rejected",
        "keys differ",
        lambda: helper.load_profiles(extra_key),
    )

    boolean_length = temporary / "boolean-length.json"
    document = json.loads(canonical_json(base_document))
    document["profiles"][0]["preimage_bytes"] = True
    write(boolean_length, canonical_json(document))
    expect_failure(
        "Boolean profile lengths are rejected",
        "preimage identity differs",
        lambda: helper.load_profiles(boolean_length),
    )

    duplicate = temporary / "duplicate.json"
    document = json.loads(canonical_json(base_document))
    document["profiles"].append(dict(document["profiles"][0]))
    write(duplicate, canonical_json(document))
    expect_failure(
        "duplicate profile IDs and identities are rejected",
        "not unique and sorted",
        lambda: helper.load_profiles(duplicate),
    )

    wrong_postimage = temporary / "wrong-postimage.json"
    document = json.loads(canonical_json(base_document))
    document["profiles"][0]["postimage_sha256"] = "0" * 64
    write(wrong_postimage, canonical_json(document))
    expect_failure(
        "wrong derived postimage identity is rejected",
        "candidate identity differs",
        lambda: helper.identify(wrong_postimage, source, None),
    )


def test_source_failures(temporary: Path, profiles: Path, source: Path) -> None:
    expect_failure(
        "requested profile mismatch is rejected",
        "does not match requested profile",
        lambda: helper.identify(profiles, source, "another-profile"),
    )

    unknown = temporary / "unknown.lua"
    write(unknown, source.read_bytes() + b"-- drift\n")
    expect_failure(
        "unknown source identity is rejected",
        "matches 0 admitted profiles",
        lambda: helper.identify(profiles, unknown, None),
    )

    linked = temporary / "linked.lua"
    os.link(source, linked)
    expect_failure(
        "multiply linked source is rejected",
        "not a single-link regular file",
        lambda: helper.identify(profiles, linked, None),
    )
    linked.unlink()

    symlink = temporary / "symlink.lua"
    symlink.symlink_to(source)
    expect_failure(
        "symbolic source is rejected",
        "cannot open Markdown module preimage",
        lambda: helper.identify(profiles, symlink, None),
    )

    source_bytes = source.read_bytes()
    for name, replacement, fragment in (
        ("duplicate-anchor", source_bytes.replace(helper.ANCHOR, helper.ANCHOR * 2),
         "parser callback occurrence count differs from one"),
        ("missing-match", source_bytes.replace(helper.MATCH, b""),
         "match expression occurrence count differs from one"),
        ("preinserted", source_bytes.replace(helper.ANCHOR, helper.REPLACEMENT),
         "callback anchor occurrence count differs from one"),
    ):
        path = temporary / f"{name}.lua"
        mutation_profiles = temporary / f"{name}.json"
        write(path, replacement)
        document = synthetic_document(replacement)
        profile = document["profiles"][0]
        profile["postimage_bytes"] = len(replacement) + len(helper.INSERTION)
        profile["postimage_sha256"] = "0" * 64
        write(mutation_profiles, canonical_json(document))
        expect_failure(
            f"{name.replace('-', ' ')} source is rejected",
            fragment,
            lambda path=path, mutation_profiles=mutation_profiles: helper.identify(
                mutation_profiles, path, None
            ),
        )


def test_destination_and_replay_failures(
    temporary: Path, source: Path, profiles: Path, output: Path, receipt: Path
) -> None:
    wrong_parent = temporary / "other"
    wrong_parent.mkdir()
    split_parent = temporary / "split"
    split_parent.mkdir()
    expect_failure(
        "split candidate and receipt parents are rejected",
        "do not share one private parent",
        lambda: helper.transform(
            profiles,
            source,
            wrong_parent / helper.OUTPUT_NAME,
            split_parent / helper.RECEIPT_NAME,
            "synthetic-markdown-1.2.3-test",
        ),
    )
    expect_failure(
        "wrong candidate leaf is rejected",
        "path or leaf differs",
        lambda: helper.transform(
            profiles,
            source,
            wrong_parent / "markdown.lua",
            wrong_parent / helper.RECEIPT_NAME,
            "synthetic-markdown-1.2.3-test",
        ),
    )
    expect_failure(
        "pre-existing candidate output is rejected",
        "cannot create candidate module",
        lambda: helper.transform(
            profiles,
            source,
            output,
            receipt,
            "synthetic-markdown-1.2.3-test",
        ),
    )

    output.chmod(0o644)
    expect_failure(
        "writable candidate mode is rejected on replay",
        "mode differs from 0444",
        lambda: helper.verify_output(profiles, output, "synthetic-markdown-1.2.3-test"),
    )
    output.chmod(0o444)

    receipt.chmod(0o644)
    receipt.write_bytes(receipt.read_bytes().replace(b"inserted_bytes\t57", b"inserted_bytes\t56"))
    receipt.chmod(0o444)
    expect_failure(
        "changed transform receipt is rejected",
        "differs from exact source/candidate binding",
        lambda: helper.verify_transform(
            profiles, source, output, receipt, "synthetic-markdown-1.2.3-test"
        ),
    )


def test_production_sources() -> None:
    profiles = helper.load_profiles(PROFILES)
    observed = [
        (
            profile["id"],
            profile["metadata_version"],
            profile["preimage_bytes"],
            profile["preimage_sha256"],
            profile["postimage_bytes"],
            profile["postimage_sha256"],
        )
        for profile in profiles
    ]
    expected = [
        (
            "texlive-2024-markdown-3.4.2-a45cf0ed",
            "3.4.2-0-ga45cf0ed",
            276148,
            "ae204b5b363a499c81e7aa6a3494eec40903a3d5a38cf95cfd04f0c037bd3837",
            276205,
            "16e0acdf0bdee428f200decf13209b584da518fc9b3472a7a7ef9d2195b18c42",
        ),
        (
            "ubuntu-noble-markdown-2.23.0-g0b22f91",
            "2.23.0-0-g0b22f91",
            188652,
            "2ac1dd75563ef09081477053231a1d472ab1230302759475dfe0a2a61337b5d3",
            188709,
            "a2e9f3be8e21ece5890b41da65439349980556b3d9cb77a67d7fe2fb762d4c01",
        ),
    ]
    require(observed == expected, "production profile roster or identity differs")
    pass_case("production profile roster binds the two reviewed module identities")

    loader = LOADER.read_text(encoding="utf-8")
    required_once = (
        "package.loaded.markdown == nil and package.preload.markdown == nil",
        'configuration.profile_id:match("^[a-z0-9][a-z0-9._-]*$")',
        "package.preload.markdown = function(module_name)",
        "#raw == configuration.module_bytes",
        "module.metadata.version == configuration.metadata_version",
        'texio.write_nl("log", "PID-RS-MARKDOWN-GC=" .. configuration.profile_id)',
    )
    for token in required_once:
        require(loader.count(token) == 1, f"loader token count differs: {token}")
    for forbidden in ("os.execute", "io.popen", "debug.", "PID-RS-PARSER", "parser_call"):
        require(forbidden not in loader, f"loader contains forbidden expansion: {forbidden}")
    pass_case("loader has one bounded preload route and no trace or subprocess feature")


def test_handoffs(paths: list[Path]) -> None:
    if not paths:
        return
    checker, checker_self_test, aggregate, aggregate_self_test, workflow, justfile = [
        path.resolve(strict=True) for path in paths
    ]
    sources = {
        "checker": checker.read_text(encoding="utf-8"),
        "checker self-test": checker_self_test.read_text(encoding="utf-8"),
        "aggregate": aggregate.read_text(encoding="utf-8"),
        "aggregate self-test": aggregate_self_test.read_text(encoding="utf-8"),
        "hosted workflow": workflow.read_text(encoding="utf-8"),
        "Just source": justfile.read_text(encoding="utf-8"),
    }
    home_assignment = re.compile(r"(?m)(?:^|[ \\t\"'])(?:export[ \\t]+)?HOME=")
    forbidden_names = (
        "PDF_BUILD_HOME",
        "PID_RS_PDF_GATE_HOME",
        "TEST_HOME",
        "WORKFLOW_GATE_HOME",
        "gate_home",
        "run_home",
    )
    for label in ("checker", "checker self-test", "aggregate", "hosted workflow"):
        source = sources[label]
        require(home_assignment.search(source) is None, f"{label} reassigns HOME")
        for name in forbidden_names:
            require(name not in source, f"{label} retains HOME surrogate {name}")
    pass_case("checker, controls, aggregate, and hosted handoffs do not reassign HOME")

    checker_tokens = (
        "prepare-mathematical-workflow-markdown-parser.py",
        "workflow-markdown-parser-profiles.json",
        "pid-rs-markdown-gc-loader.lua",
        "verify-transform",
        "PID-RS-MARKDOWN-GC=",
        "XDG_CONFIG_HOME=",
        "XDG_CACHE_HOME=",
    )
    for token in checker_tokens:
        require(token in sources["checker"], f"checker lacks source binding: {token}")
    pass_case("checker wires profile transform, loader evidence, replay, and XDG roots")

    checker_source = sources["checker"]
    require("--luadebug" not in checker_source, "checker broadened LuaTeX debug capabilities")
    identify_position = checker_source.index("  identify \\\n")
    build_position = checker_source.index("build_report() {")
    transform_position = checker_source.index("    transform \\\n", build_position)
    loader_position = checker_source.index("pid_rs_markdown_gc_loader = assert(loadfile(")
    input_position = checker_source.index(r'f"\\input{{{source_path}}}\n"', loader_position)
    compiler_position = checker_source.index("        lualatex ", transform_position)
    replay_position = checker_source.index(
        'verify_parser_transform "$parser_module" "$parser_receipt"', transform_position
    )
    marker_position = checker_source.index(
        'grep -Fxc -- "PID-RS-MARKDOWN-GC=$PARSER_PROFILE_ID"', compiler_position
    )
    require(
        identify_position < build_position < transform_position < loader_position < input_position,
        "profile identification, transform, loader, and source order differs",
    )
    require(
        transform_position < replay_position < compiler_position < marker_position,
        "transform replay, compilation, and marker order differs",
    )
    require(
        "markdown_module_source in resolved_inputs" in checker_source
        and "expected_parser_module = (run_dir / parser_module_name).resolve()" in checker_source,
        "FLS closure lacks ambient-source denial or exact private-module requirement",
    )
    pass_case("checker orders exact preload before source and keeps production LuaTeX capabilities")

    for path in (
        "scripts/prepare-mathematical-workflow-markdown-parser.py",
        "scripts/prepare-mathematical-workflow-markdown-parser-self-test.py",
        "audit/formal/workflow-markdown-parser-profiles.json",
        "audit/formal/latex/pid-rs-markdown-gc-loader.lua",
    ):
        require(path in sources["checker"], f"checker manifest lacks {path}")
        require(path in sources["checker self-test"], f"checker self-test fixture lacks {path}")
    pass_case("checker and checker self-test capture all parser intervention sources")

    self_test_name = "prepare-mathematical-workflow-markdown-parser-self-test.py"
    require(sources["aggregate"].count(self_test_name) == 2,
            "aggregate does not run both parser source-control modes")
    require(f"python3 -O -I -S -B scripts/{self_test_name}" in sources["aggregate"],
            "aggregate lacks optimized parser source control")
    for token in (
        "WORKFLOW_GATE_XDG_ROOT",
        '"XDG_CONFIG_HOME=$WORKFLOW_GATE_XDG_CONFIG"',
        '"XDG_CACHE_HOME=$WORKFLOW_GATE_XDG_CACHE"',
        "workflow environment reassigns HOME",
    ):
        require(token in sources["aggregate self-test"],
                f"aggregate self-test lacks HOME-free routing control: {token}")
    pass_case("aggregate runs normal and optimized parser source controls")

    start = sources["hosted workflow"].index("  formal-pdf-structure:")
    end = sources["hosted workflow"].index("\n  certified-sxpid-reference:", start)
    job = sources["hosted workflow"][start:end]
    for token in ("ELAN_HOME=", "XDG_CONFIG_HOME=", "XDG_CACHE_HOME=", "TMPDIR="):
        require(token in job, f"hosted formal-PDF handoff lacks {token}")
    require(home_assignment.search(job) is None, "hosted formal-PDF job reassigns HOME")
    pass_case("hosted formal-PDF job hands off tool-specific roots without HOME reassignment")

    just_source = sources["Just source"]
    start = just_source.index("formal-mathematical-workflow-pdf:\n")
    end = just_source.index("\nformal-pdfs:\n", start)
    recipe = just_source[start:end]
    require(home_assignment.search(recipe) is None, "active workflow-PDF Just recipe reassigns HOME")
    for command in (
        "scripts/check-mathematical-workflow-pdf-self-test.sh",
        "scripts/check-mathematical-workflow-pdf.sh --exact",
    ):
        require(recipe.count(command) == 1, f"active workflow-PDF Just command differs: {command}")
    pass_case("active workflow-PDF Just handoff has no HOME reassignment")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--handoff",
        nargs=6,
        type=Path,
        metavar=(
            "CHECKER",
            "CHECKER_SELF_TEST",
            "AGGREGATE",
            "AGGREGATE_SELF_TEST",
            "WORKFLOW",
            "JUSTFILE",
        ),
    )
    return parser.parse_args()


def main() -> int:
    parsed = arguments()
    with tempfile.TemporaryDirectory(prefix="workflow-markdown-parser-source-control-") as raw:
        temporary = Path(raw).resolve()
        source, profiles, output, receipt, document = test_transform_contract(temporary)
        test_manifest_failures(temporary, source, document)
        test_source_failures(temporary, profiles, source)
        test_destination_and_replay_failures(temporary, source, profiles, output, receipt)
    test_production_sources()
    test_handoffs(parsed.handoff or [])
    print(
        f"OK: {PASS_COUNT} source-only Markdown parser transform/loader controls passed; "
        "no Lua, TeX, PDF, proof, or native helper was launched"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"workflow Markdown parser self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
