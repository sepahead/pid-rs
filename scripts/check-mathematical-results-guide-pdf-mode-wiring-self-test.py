#!/usr/bin/env python3
"""Fail-closed tests for results-guide PDF producer-profile routing.

The renderer is tested elsewhere. This suite binds the wrapper's producer
selector and dispatch fragments, executes them in isolation, and rejects
mutations that could choose a relation from candidate bytes or use fallback.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import os
import pathlib
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
WRAPPER = ROOT / "scripts/check-mathematical-results-guide-pdf.sh"
GUIDE_BUILDER = ROOT / "scripts/build-mathematical-results-guide-pdf.sh"
SXPID3_WRAPPER = ROOT / "scripts/check-sxpid3-source-marginal-audit-pdf.sh"
SXPID3_BUILDER = ROOT / "scripts/build-sxpid3-source-marginal-audit-pdf.sh"
HOSTED_BASENAME = "check-mathematical-results-guide-pdf-hosted-raw-profile-v2.py"
HOSTED_SELF_TEST_BASENAME = (
    "check-mathematical-results-guide-pdf-hosted-raw-profile-v2-self-test.py"
)
HOSTED_FIXTURE_BASENAME = (
    "mathematical-results-guide-pandoc-3.10.2-ubuntu-24.04-texlive-2023-hosted-raw-v2.pdf"
)
HOSTED_RECEIPT_BASENAME = (
    "mathematical-results-guide-pandoc-3.10.2-hosted-raw-profile-v2.json"
)
ALPHA_BASENAME = "check-mathematical-results-guide-pdf-font-alpha-equivalence.py"
ALPHA_SELF_TEST_BASENAME = (
    "check-mathematical-results-guide-pdf-font-alpha-equivalence-self-test.py"
)
LEGACY_FIXTURE_BASENAME = (
    "mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf"
)
LEGACY_PORTABILITY_CHECK_BASENAME = (
    "check-mathematical-results-guide-pandoc-portability-receipt.py"
)
LEGACY_PORTABILITY_SELF_TEST_BASENAME = (
    "check-mathematical-results-guide-pandoc-portability-receipt-self-test.py"
)
LEGACY_PORTABILITY_RECEIPT_BASENAME = (
    "mathematical-results-guide-pandoc-3.1.3-portability-v1.json"
)
LEGACY_TRAILER_CHECK_BASENAME = (
    "check-mathematical-results-guide-trailer-id-observation.py"
)
LEGACY_TRAILER_SELF_TEST_BASENAME = (
    "check-mathematical-results-guide-trailer-id-observation-self-test.py"
)
LEGACY_TRAILER_RECEIPT_BASENAME = (
    "mathematical-results-guide-old-toolchain-trailer-id-observation-v1.json"
)
EXPECTED_WRAPPER_SHA256 = (
    "0ac49e36111c7a1d8f24a4acd0f7b1b0755fd6273d804873563b1343c7edb145"
)
EXPECTED_CAPTURE_FUNCTION_SHA256 = (
    "a9a7d694fd43cd9888605fc48db5e5dc67bccb59d1a1b9c328de25aff751a088"
)
EXPECTED_SELECTOR_FUNCTION_SHA256 = (
    "ffe4b0d2e2d2b39063a3296be0f97b9012eb261506fad993ccddfbeb068bd695"
)
EXPECTED_GATE_DIGEST_FUNCTION_SHA256 = (
    "0a25b0ad943f80383bcfa6c9dd6493285c64522e29aeb3337a6c3b57a6e224fc"
)
EXPECTED_POSTBUILD_GUARD_SHA256 = (
    "780888e827401e035c384205e1e4ace2fc3582e0091ea7d16f1749eb493a6961"
)
HOSTED_CHECKER = ROOT / "scripts" / HOSTED_BASENAME
HOSTED_SELF_TEST = ROOT / "scripts" / HOSTED_SELF_TEST_BASENAME
LEGACY_ALPHA_CHECKER = ROOT / "scripts" / ALPHA_BASENAME
LEGACY_ALPHA_SELF_TEST = ROOT / "scripts" / ALPHA_SELF_TEST_BASENAME
LEGACY_CHECKER = ROOT / "scripts" / LEGACY_PORTABILITY_CHECK_BASENAME
LEGACY_SELF_TEST = ROOT / "scripts" / LEGACY_PORTABILITY_SELF_TEST_BASENAME
LEGACY_TRAILER_CHECKER = ROOT / "scripts" / LEGACY_TRAILER_CHECK_BASENAME
LEGACY_TRAILER_SELF_TEST = ROOT / "scripts" / LEGACY_TRAILER_SELF_TEST_BASENAME
SELECTED_SOURCE_SHA256 = {
    HOSTED_CHECKER: "29837b202ad3e5afa59e10f0ef4848b876fb6ef2b6aa3a996f78d7aac2752fcc",
    HOSTED_SELF_TEST: "f24a3a3013ccf4f5964f947f26798ad00a01f47b7453a75ce9e29946d28f89f9",
    LEGACY_ALPHA_CHECKER: "5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997",
    LEGACY_ALPHA_SELF_TEST: "07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be",
    LEGACY_CHECKER: "5e59e9fb997098656039db1a60c1e8694a451432618ac2ecd192b402e7a8c319",
    LEGACY_SELF_TEST: "bdb53c0b8a20e48df73b22aeeabc223855c2ce797444808e6de495baf6ab2473",
    LEGACY_TRAILER_CHECKER: "e531d58620ff41275b741666a119a1245d5ec2a08fa943fc12a297d56317106f",
    LEGACY_TRAILER_SELF_TEST: "9b1d0da3dffc87e9d46a4986b9c54c457c036ff0cd0a0966f08155aad7b5b65b",
}


class WiringError(Exception):
    """A deterministic mode-wiring policy failure."""


@dataclass(frozen=True)
class WiringFragments:
    mode_guard: str
    digest_function: str
    capture_function: str
    selector_function: str
    prebuild_dispatch: str
    postbuild_guard: str
    relation_dispatch: str
    command_dispatch: str
    artifact_dispatch: str


def fail(message: str) -> NoReturn:
    raise SystemExit(
        "Mathematical results guide PDF mode-wiring self-test failed: " + message
    )


def read_direct(path: pathlib.Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise WiringError(f"{label} is absent, non-regular, or symbolic: {path}")
    return path.read_text(encoding="utf-8")


def read_selected_source(path: pathlib.Path, label: str) -> str:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise WiringError(
            "platform lacks no-follow, nonblocking selected-source custody"
        )
    try:
        before = path.lstat()
        resolved = path.resolve(strict=True)
        descriptor = os.open(
            path,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
        )
    except (OSError, RuntimeError) as error:
        raise WiringError(
            f"cannot open {label} under stable custody: {error}"
        ) from error
    identity_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_uid",
        "st_gid",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )

    def identity(status: os.stat_result) -> tuple[int, ...]:
        return tuple(getattr(status, field) for field in identity_fields)

    try:
        opened = os.fstat(descriptor)
        if (
            resolved != path
            or not pathlib.Path(path).is_absolute()
            or not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_size <= 0
            or opened.st_size > 512 * 1024
            or identity(before) != identity(opened)
        ):
            raise WiringError(
                f"{label} is noncanonical, non-regular, linked, or oversized"
            )
        chunks = []
        remaining = 512 * 1024 + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after_descriptor = os.fstat(descriptor)
        after_path = path.lstat()
        after_resolved = path.resolve(strict=True)
    except OSError as error:
        raise WiringError(
            f"cannot read {label} under stable custody: {error}"
        ) from error
    finally:
        os.close(descriptor)
    if (
        len(payload) != opened.st_size
        or after_resolved != resolved
        or identity(opened) != identity(after_descriptor)
        or identity(opened) != identity(after_path)
    ):
        raise WiringError(f"{label} changed while read")
    expected = SELECTED_SOURCE_SHA256[path]
    observed = hashlib.sha256(payload).hexdigest()
    if observed != expected:
        raise WiringError(
            f"{label} digest changed: observed={observed} expected={expected}"
        )
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise WiringError(f"{label} is not UTF-8") from error


def require_profile_source_separation(
    profile: str,
    label: str,
    source: str,
    *,
    allowed_denylist: str | None = None,
    allowed_literals: tuple[str | bytes, ...] = (),
) -> None:
    if profile == "hosted":
        forbidden = (
            ALPHA_BASENAME,
            ALPHA_SELF_TEST_BASENAME,
            LEGACY_FIXTURE_BASENAME,
            LEGACY_PORTABILITY_CHECK_BASENAME,
            LEGACY_PORTABILITY_SELF_TEST_BASENAME,
            LEGACY_PORTABILITY_RECEIPT_BASENAME,
            LEGACY_TRAILER_CHECK_BASENAME,
            LEGACY_TRAILER_SELF_TEST_BASENAME,
            LEGACY_TRAILER_RECEIPT_BASENAME,
            ALPHA_BASENAME.removesuffix(".py"),
            ALPHA_SELF_TEST_BASENAME.removesuffix(".py"),
            LEGACY_PORTABILITY_CHECK_BASENAME.removesuffix(".py"),
            LEGACY_PORTABILITY_SELF_TEST_BASENAME.removesuffix(".py"),
            LEGACY_TRAILER_CHECK_BASENAME.removesuffix(".py"),
            LEGACY_TRAILER_SELF_TEST_BASENAME.removesuffix(".py"),
            "FONT_ALPHA_CHECK",
            "FONT_ALPHA_SELF_TEST",
            "RETAINED_FONT_ALPHA_FIXTURE",
            "PANDOC_PORTABILITY_RECEIPT_CHECK",
            "PANDOC_PORTABILITY_RECEIPT_SELF_TEST",
            "LEGACY_PANDOC_PORTABILITY_RECEIPT",
            "TRAILER_ID_OBSERVATION_CHECK",
            "TRAILER_ID_OBSERVATION_SELF_TEST",
            "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT",
        )
    elif profile == "legacy":
        forbidden = (
            HOSTED_BASENAME,
            HOSTED_SELF_TEST_BASENAME,
            HOSTED_FIXTURE_BASENAME,
            HOSTED_RECEIPT_BASENAME,
            HOSTED_BASENAME.removesuffix(".py"),
            HOSTED_SELF_TEST_BASENAME.removesuffix(".py"),
            "HOSTED_RAW_CHECK",
            "HOSTED_RAW_SELF_TEST",
            "RETAINED_HOSTED_RAW_FIXTURE",
            "HOSTED_RAW_PROFILE_RECEIPT",
        )
    else:
        raise WiringError(f"unknown selected profile source: {profile}")
    try:
        tree = ast.parse(source, filename=label)
    except SyntaxError as error:
        raise WiringError(f"cannot parse selected {label}: {error}") from error
    parents = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    allowed_constants: set[int] = set()
    if allowed_denylist is not None:
        assignments = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == allowed_denylist
        ]
        if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Tuple):
            raise WiringError(
                f"{profile} {label} denylist assignment is not one literal tuple"
            )
        assignment = assignments[0]
        if not all(
            isinstance(item, ast.Constant) and isinstance(item.value, str)
            for item in assignment.value.elts
        ):
            raise WiringError(f"{profile} {label} denylist has a dynamic value")
        allowed_constants.update(id(item) for item in assignment.value.elts)
        expected_loop = (
            "for fragment in forbidden_fragments:\n"
            "    if fragment.lower() in lowered:\n"
            "        errors.append(f'forbidden relaxation or dependency is present: {fragment}')"
            if allowed_denylist == "forbidden_fragments"
            else "for token in FORBIDDEN_CURRENT_PROFILE_TOKENS:\n"
            "    require(token not in source, "
            "f'legacy checker contains a current-profile dependency: {token}')"
        )
        reviewed_loops = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Name)
            and node.iter.id == allowed_denylist
            and ast.unparse(node) == expected_loop
        ]
        if len(reviewed_loops) != 1:
            raise WiringError(
                f"{profile} {label} denylist does not have one reviewed iteration"
            )
        reviewed_loop = reviewed_loops[0]
        expected_len_uses = (
            2 if allowed_denylist == "FORBIDDEN_CURRENT_PROFILE_TOKENS" else 0
        )
        observed_len_uses = 0
        for name_node in (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id == allowed_denylist
        ):
            parent = parents.get(id(name_node))
            if (
                isinstance(name_node.ctx, ast.Store)
                and parent is assignment
                and assignment.targets[0] is name_node
            ):
                continue
            if (
                isinstance(name_node.ctx, ast.Load)
                and parent is reviewed_loop
                and reviewed_loop.iter is name_node
            ):
                continue
            if (
                isinstance(name_node.ctx, ast.Load)
                and isinstance(parent, ast.Call)
                and isinstance(parent.func, ast.Name)
                and parent.func.id == "len"
                and parent.args == [name_node]
                and not parent.keywords
                and expected_len_uses
            ):
                observed_len_uses += 1
                continue
            raise WiringError(
                f"{profile} {label} uses its denylist outside reviewed guards"
            )
        if observed_len_uses != expected_len_uses:
            raise WiringError(
                f"{profile} {label} denylist len-use count is {observed_len_uses}, "
                f"expected {expected_len_uses}"
            )

    def reviewed_hostile_literal(node: ast.Constant) -> bool:
        parent = parents.get(id(node))
        call = parents.get(id(parent)) if isinstance(parent, ast.BinOp) else None
        if (
            not isinstance(parent, ast.BinOp)
            or not isinstance(parent.op, ast.Add)
            or parent.right is not node
            or not isinstance(parent.left, ast.Name)
            or parent.left.id != "source"
            or not isinstance(call, ast.Call)
            or not isinstance(call.func, ast.Name)
            or call.func.id != "require_source_mutation_rejected"
            or not call.args
            or call.args[0] is not parent
        ):
            return False
        ancestor = parents.get(id(call))
        while ancestor is not None and not isinstance(ancestor, ast.FunctionDef):
            ancestor = parents.get(id(ancestor))
        return (
            isinstance(ancestor, ast.FunctionDef)
            and ancestor.name == "audit_source_mutations"
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
            if id(node) in allowed_constants or (
                node.value in allowed_literals and reviewed_hostile_literal(node)
            ):
                continue
            value = (
                node.value
                if isinstance(node.value, str)
                else node.value.decode("utf-8", errors="replace")
            )
            for token in forbidden:
                if token in value:
                    raise WiringError(
                        f"{profile} {label} has an opposite-profile path dependency: {token}"
                    )
        elif isinstance(node, ast.Name) and node.id in forbidden:
            raise WiringError(
                f"{profile} {label} has an opposite-profile name dependency: {node.id}"
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for module in modules:
                for token in forbidden:
                    if token.removesuffix(".py") in module:
                        raise WiringError(
                            f"{profile} {label} imports opposite-profile code: {module}"
                        )


def exercise_profile_source_separation_logic(profile: str) -> int:
    if profile == "hosted":
        mutations = (
            (
                "hosted raw checker",
                'import importlib\nimportlib.import_module("'
                + ALPHA_BASENAME.removesuffix(".py")
                + '")\n',
            ),
            (
                "hosted raw checker self-test",
                f"OPERATIONAL_DEPENDENCY = {ALPHA_BASENAME!r}\n",
            ),
        )
    elif profile == "legacy":
        mutations = tuple(
            (label, f"OPERATIONAL_DEPENDENCY = {HOSTED_BASENAME!r}\n")
            for label in (
                "legacy font-alpha checker",
                "legacy font-alpha checker self-test",
                "legacy portability checker",
                "legacy portability checker self-test",
                "legacy trailer checker",
                "legacy trailer checker self-test",
            )
        )
    else:
        raise WiringError(f"unknown selected profile source: {profile}")
    controls = 0
    for label, mutation in mutations:
        try:
            require_profile_source_separation(profile, label, mutation)
        except WiringError:
            controls += 1
        else:
            raise WiringError(
                f"{profile} {label} opposite-profile dependency mutation passed"
            )
    opposite_document = HOSTED_BASENAME if profile == "legacy" else ALPHA_BASENAME
    neutral_document = '"""Profile-isolation audit fixture."""\nVALUE = 1\n'
    require_profile_source_separation(
        profile,
        f"{profile} neutral docstring control",
        neutral_document,
    )
    for label, source in (
        (
            "executable opposite-profile docstring",
            f'"""{opposite_document}"""\nexec(__doc__)\n',
        ),
        (
            "opposite-profile docstring",
            f'"""{opposite_document}"""\nVALUE = 1\n',
        ),
    ):
        try:
            require_profile_source_separation(profile, label, source)
        except WiringError:
            controls += 1
        else:
            raise WiringError(f"{profile} {label} mutation passed")

    if profile == "hosted":
        denylist = "forbidden_fragments"
        reviewed = (
            'forbidden_fragments = ("font-alpha-equivalence",)\n'
            'lowered = ""\nerrors = []\n'
            "for fragment in forbidden_fragments:\n"
            "    if fragment.lower() in lowered:\n"
            "        errors.append(f'forbidden relaxation or dependency is present: {fragment}')\n"
        )
    else:
        denylist = "FORBIDDEN_CURRENT_PROFILE_TOKENS"
        reviewed = (
            'FORBIDDEN_CURRENT_PROFILE_TOKENS = ("hosted-raw-profile",)\n'
            'source = ""\n'
            "def require(condition, message):\n"
            "    pass\n"
            "for token in FORBIDDEN_CURRENT_PROFILE_TOKENS:\n"
            "    require(token not in source, "
            "f'legacy checker contains a current-profile dependency: {token}')\n"
            "require(len(FORBIDDEN_CURRENT_PROFILE_TOKENS) == 1, 'length')\n"
            "COUNT = len(FORBIDDEN_CURRENT_PROFILE_TOKENS)\n"
        )
    require_profile_source_separation(
        profile,
        f"{profile} reviewed denylist control",
        reviewed,
        allowed_denylist=denylist,
    )
    controls += 2
    denylist_hostiles = (
        f"\n__import__({denylist}[0])\n",
        f"\nalias = {denylist}\n__import__(alias[0])\n",
        f"\nexec({denylist}[0])\n",
    )
    for index, suffix in enumerate(denylist_hostiles, start=1):
        try:
            require_profile_source_separation(
                profile,
                f"{profile} dynamic denylist hostile {index}",
                reviewed + suffix,
                allowed_denylist=denylist,
            )
        except WiringError:
            controls += 1
        else:
            raise WiringError(
                f"{profile} dynamic denylist hostile {index} mutation passed"
            )
    return controls


def audit_selected_profile_source(profile: str) -> int:
    if profile == "hosted":
        selected = (
            (HOSTED_CHECKER, "hosted raw checker", None, ()),
            (
                HOSTED_SELF_TEST,
                "hosted raw checker self-test",
                "forbidden_fragments",
                (
                    b'\nimport importlib\nimportlib.import_module("check-mathematical-results-guide-pdf-font-alpha-equivalence")\n',
                ),
            ),
        )
    elif profile == "legacy":
        selected = (
            (LEGACY_ALPHA_CHECKER, "legacy font-alpha checker", None, ()),
            (LEGACY_ALPHA_SELF_TEST, "legacy font-alpha checker self-test", None, ()),
            (LEGACY_CHECKER, "legacy portability checker", None, ()),
            (
                LEGACY_SELF_TEST,
                "legacy portability checker self-test",
                "FORBIDDEN_CURRENT_PROFILE_TOKENS",
                (),
            ),
            (LEGACY_TRAILER_CHECKER, "legacy trailer checker", None, ()),
            (LEGACY_TRAILER_SELF_TEST, "legacy trailer checker self-test", None, ()),
        )
    else:
        raise WiringError(f"unknown selected profile source: {profile}")
    for path, label, allowed_denylist, allowed_literals in selected:
        source = read_selected_source(path, label)
        require_profile_source_separation(
            profile,
            label,
            source,
            allowed_denylist=allowed_denylist,
            allowed_literals=allowed_literals,
        )
    hostile_controls = exercise_profile_source_separation_logic(profile)
    print(
        f"OK: digest-pinned selected {profile} sources contain no unapproved literal "
        "opposite-profile path/name dependency outside AST-confined negative controls "
        f"(sources={len(selected)}; source_controls={hostile_controls}); "
        "this is not a data-flow or noninterference proof"
    )
    return 0


def require_count(source: str, token: str, count: int, label: str) -> None:
    observed = source.count(token)
    if observed != count:
        raise WiringError(f"{label} count is {observed}, expected {count}")


def extract_unique(source: str, start: str, end: str, label: str) -> str:
    require_count(source, start, 1, f"{label} start anchor")
    start_index = source.index(start)
    end_index = source.find(end, start_index + len(start))
    if end_index < 0:
        raise WiringError(f"{label} end anchor is absent after its start")
    if source.find(end, end_index + len(end)) >= 0:
        raise WiringError(f"{label} end anchor is not unique")
    return source[start_index : end_index + len(end)]


def extract_assignment(source: str, name: str) -> str:
    matches = re.findall(rf"^{re.escape(name)}=(.*)$", source, flags=re.MULTILINE)
    if len(matches) != 1:
        raise WiringError(f"{name} assignment count is {len(matches)}, expected 1")
    return matches[0]


def audit_auxiliary_sources(
    guide_builder: str, sxpid3_wrapper: str, sxpid3_builder: str
) -> None:
    forbidden = (
        HOSTED_BASENAME,
        "HOSTED_RAW_CHECK",
        HOSTED_SELF_TEST_BASENAME,
        HOSTED_FIXTURE_BASENAME,
        "RETAINED_HOSTED_RAW_FIXTURE",
        HOSTED_RECEIPT_BASENAME,
        "HOSTED_RAW_PROFILE_RECEIPT",
        ALPHA_BASENAME,
        "FONT_ALPHA_CHECK",
        ALPHA_SELF_TEST_BASENAME,
        LEGACY_FIXTURE_BASENAME,
        "RETAINED_FONT_ALPHA_FIXTURE",
        LEGACY_PORTABILITY_CHECK_BASENAME,
        "PANDOC_PORTABILITY_RECEIPT_CHECK",
        LEGACY_PORTABILITY_SELF_TEST_BASENAME,
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST",
        LEGACY_PORTABILITY_RECEIPT_BASENAME,
        "LEGACY_PANDOC_PORTABILITY_RECEIPT",
        LEGACY_TRAILER_CHECK_BASENAME,
        "TRAILER_ID_OBSERVATION_CHECK",
        LEGACY_TRAILER_SELF_TEST_BASENAME,
        "TRAILER_ID_OBSERVATION_SELF_TEST",
        LEGACY_TRAILER_RECEIPT_BASENAME,
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT",
    )
    for source, label in (
        (guide_builder, "guide builder"),
        (sxpid3_wrapper, "SxPID3 wrapper"),
        (sxpid3_builder, "SxPID3 builder"),
    ):
        for token in forbidden:
            if token in source:
                raise WiringError(f"{label} contains profile comparator state: {token}")


def sha256_text(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def require_region_digest(source: str, expected: str, label: str) -> None:
    observed = sha256_text(source)
    if expected.startswith("__PID_RS_"):
        raise WiringError(f"{label} digest integration placeholder remains")
    if observed != expected:
        raise WiringError(f"{label} digest changed: {observed}")


def audit_wrapper(
    source: str, *, enforce_wrapper_digest: bool = True
) -> WiringFragments:
    if enforce_wrapper_digest:
        require_region_digest(source, EXPECTED_WRAPPER_SHA256, "complete wrapper")
    exact_assignments = {
        "HOSTED_RAW_CHECK": (
            '"$ROOT/scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-v2.py"'
        ),
        "HOSTED_RAW_SELF_TEST": (
            '"$ROOT/scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-v2-self-test.py"'
        ),
        "FONT_ALPHA_CHECK": (
            '"$ROOT/scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py"'
        ),
        "FONT_ALPHA_SELF_TEST": (
            '"$ROOT/scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence-self-test.py"'
        ),
        "HOSTED_RAW_PROFILE_RECEIPT": (
            '"$ROOT/audit/evidence/' + HOSTED_RECEIPT_BASENAME + '"'
        ),
        "PANDOC_PORTABILITY_RECEIPT_CHECK": (
            '"$ROOT/scripts/' + LEGACY_PORTABILITY_CHECK_BASENAME + '"'
        ),
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST": (
            '"$ROOT/scripts/' + LEGACY_PORTABILITY_SELF_TEST_BASENAME + '"'
        ),
        "LEGACY_PANDOC_PORTABILITY_RECEIPT": (
            '"$ROOT/audit/evidence/' + LEGACY_PORTABILITY_RECEIPT_BASENAME + '"'
        ),
        "TRAILER_ID_OBSERVATION_CHECK": (
            '"$ROOT/scripts/' + LEGACY_TRAILER_CHECK_BASENAME + '"'
        ),
        "TRAILER_ID_OBSERVATION_SELF_TEST": (
            '"$ROOT/scripts/' + LEGACY_TRAILER_SELF_TEST_BASENAME + '"'
        ),
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT": (
            '"$ROOT/audit/evidence/' + LEGACY_TRAILER_RECEIPT_BASENAME + '"'
        ),
        "HOSTED_PROFILE_ID": "hosted-pandoc-3.10.2-ubuntu-24.04-raw-v2-bound",
        "HOSTED_PANDOC_VERSION": "'pandoc 3.10.2'",
        "HOSTED_PANDOC_SHA256": (
            "867c5fc83e6b18991d1880e040867d31d09a0d5e68b0bfae362d2fbc71cf25ce"
        ),
        "HOSTED_RENDERER_VERSION": (
            "'This is LuaHBTeX, Version 1.17.0 (TeX Live 2023/Debian)'"
        ),
        "HOSTED_RENDERER_REALPATH": "/usr/bin/luahbtex",
        "HOSTED_RENDERER_SHA256": (
            "cc74da0d993e503321f9dd65b8cc5ddf103f2620c4bdbc41798841f253c46e02"
        ),
        "HOSTED_TEXMFSYSVAR": "/var/lib/texmf",
        "HOSTED_FORMAT_PATH": "/var/lib/texmf/web2c/luahbtex/lualatex.fmt",
        "LEGACY_PROFILE_ID": "legacy-pandoc-3.1.3-ubuntu-24.04-font-alpha",
        "LEGACY_PANDOC_VERSION": "'pandoc 3.1.3'",
        "LEGACY_PANDOC_REALPATH": "/usr/bin/pandoc",
        "LEGACY_PANDOC_SHA256": (
            "3dd273647f0265cb439f22976d5366a54b071a3783f6fec50838b47fb53d701b"
        ),
        "LEGACY_RENDERER_VERSION": (
            "'This is LuaHBTeX, Version 1.17.0 (TeX Live 2023/Debian)'"
        ),
        "LEGACY_RENDERER_REALPATH": "/usr/bin/luahbtex",
        "LEGACY_RENDERER_SHA256": (
            "cc74da0d993e503321f9dd65b8cc5ddf103f2620c4bdbc41798841f253c46e02"
        ),
        "LEGACY_TEXMFSYSVAR": "/var/lib/texmf",
        "LEGACY_FORMAT_PATH": "/var/lib/texmf/web2c/luahbtex/lualatex.fmt",
        "LEGACY_FORMAT_BYTES": "''",
        "LEGACY_FORMAT_SHA256": "''",
        "STRUCTURE_CHECK_SHA256": (
            "a70d3c78da7040774c5976f2316480501713eed1e9c865822e3024724a0ccf8d"
        ),
        "STRUCTURE_SELF_TEST_SHA256": (
            "aa8fd64c627884d64b18c2e8cb2565c06678f2c5f55be182723541d026c56229"
        ),
        "ID_VARIANCE_CHECK_SHA256": (
            "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7"
        ),
        "HOSTED_RAW_CHECK_SHA256": (
            "29837b202ad3e5afa59e10f0ef4848b876fb6ef2b6aa3a996f78d7aac2752fcc"
        ),
        "HOSTED_RAW_SELF_TEST_SHA256": (
            "f24a3a3013ccf4f5964f947f26798ad00a01f47b7453a75ce9e29946d28f89f9"
        ),
        "HOSTED_RAW_PROFILE_RECEIPT_SHA256": (
            "56e599a1f879418c8d2cce85f61b0a51cb1210f915462ff4aa6f0af8b2334be8"
        ),
        "FONT_ALPHA_CHECK_SHA256": (
            "5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997"
        ),
        "FONT_ALPHA_SELF_TEST_SHA256": (
            "07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be"
        ),
        "PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256": (
            "5e59e9fb997098656039db1a60c1e8694a451432618ac2ecd192b402e7a8c319"
        ),
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256": (
            "bdb53c0b8a20e48df73b22aeeabc223855c2ce797444808e6de495baf6ab2473"
        ),
        "LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256": (
            "7ea2acf89c8a33f5666ab9798a594c24febdad609bd1b5e650b87d8a98ca4581"
        ),
        "TRAILER_ID_OBSERVATION_CHECK_SHA256": (
            "e531d58620ff41275b741666a119a1245d5ec2a08fa943fc12a297d56317106f"
        ),
        "TRAILER_ID_OBSERVATION_SELF_TEST_SHA256": (
            "9b1d0da3dffc87e9d46a4986b9c54c457c036ff0cd0a0966f08155aad7b5b65b"
        ),
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256": (
            "cd5602bb28dce0780c4bac5f70097e496d2afe9141a8210f249332b5e6d93596"
        ),
    }
    for name, expected in exact_assignments.items():
        observed = extract_assignment(source, name)
        if observed != expected:
            raise WiringError(f"{name} changed: {observed!r}")
    for basename, label in (
        (HOSTED_BASENAME, "hosted checker basename"),
        (HOSTED_SELF_TEST_BASENAME, "hosted self-test basename"),
        (ALPHA_BASENAME, "font-alpha checker basename"),
        (ALPHA_SELF_TEST_BASENAME, "font-alpha self-test basename"),
        (HOSTED_RECEIPT_BASENAME, "hosted provenance receipt basename"),
        (LEGACY_PORTABILITY_CHECK_BASENAME, "historical receipt checker basename"),
        (
            LEGACY_PORTABILITY_SELF_TEST_BASENAME,
            "historical receipt self-test basename",
        ),
        (LEGACY_PORTABILITY_RECEIPT_BASENAME, "historical receipt basename"),
        (LEGACY_TRAILER_CHECK_BASENAME, "historical trailer checker basename"),
        (
            LEGACY_TRAILER_SELF_TEST_BASENAME,
            "historical trailer self-test basename",
        ),
        (LEGACY_TRAILER_RECEIPT_BASENAME, "historical trailer receipt basename"),
    ):
        require_count(source, basename, 1, label)

    for forbidden_assignment in ("HOSTED_FORMAT_BYTES", "HOSTED_FORMAT_SHA256"):
        if re.search(rf"^{forbidden_assignment}=", source, flags=re.MULTILINE):
            raise WiringError(
                f"{forbidden_assignment} must not profile-shop generated format bytes"
            )

    required_once = (
        ('MODE="${1:---exact}"', "MODE assignment"),
        (
            'if (( $# > 1 )) || [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then',
            "closed public mode and arity guard",
        ),
        (
            'RETAINED_HOSTED_RAW_FIXTURE="$ROOT/audit/evidence/'
            + HOSTED_FIXTURE_BASENAME
            + '"',
            "hosted fixture assignment",
        ),
        (
            'RETAINED_FONT_ALPHA_FIXTURE="$ROOT/audit/evidence/'
            + LEGACY_FIXTURE_BASENAME
            + '"',
            "legacy fixture assignment",
        ),
        ('BUILT="$BUILD_ROOT/built.pdf"', "built artifact assignment"),
        ("CROSS_PROFILE=''", "empty profile initialization"),
        (
            'capture_cross_producer_tuple before "$PRODUCER_TUPLE_BEFORE"',
            "pre-build producer capture",
        ),
        (
            'capture_cross_producer_tuple after "$PRODUCER_TUPLE_AFTER"',
            "post-build producer capture",
        ),
        (
            '"$CROSS_TUPLE_BASE64_AFTER" != "$CROSS_TUPLE_BASE64"',
            "pre/post exact held-byte evidence comparison",
        ),
        ('validate_pdf committed "$COMMITTED" strict', "strict committed validation"),
        ('validate_pdf built "$BUILT" strict', "strict exact validation"),
        (
            'validate_pdf built "$BUILT" hosted-raw-and-strict',
            "hosted current validation",
        ),
        (
            'validate_pdf built "$BUILT" legacy-typed-font-alpha-from-committed',
            "legacy font-alpha validation",
        ),
        ('cmp -s "$BUILT" "$COMMITTED" || {', "raw exact artifact comparison"),
    )
    for token, label in required_once:
        require_count(source, token, 1, label)

    mode_guard = 'MODE="${1:---exact}"\n' + extract_unique(
        source,
        'if (( $# > 1 )) || [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then\n',
        "fi\ncommand -v python3",
        "public mode and arity guard",
    ).removesuffix("\ncommand -v python3")
    expected_mode_guard = (
        'MODE="${1:---exact}"\n'
        'if (( $# > 1 )) || [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then\n'
        '  echo "usage: $0 [--exact|--cross-toolchain]" >&2\n'
        "  exit 2\n"
        "fi"
    )
    if mode_guard != expected_mode_guard:
        raise WiringError("public mode and arity guard changed")

    common_gate_loop = extract_unique(
        source,
        'for guide_gate in "$PROSE_CHECK"',
        "done\nfor command_name in",
        "common gate availability loop",
    )[: -len("\nfor command_name in")]
    common_input_loop = extract_unique(
        source,
        "for path in \\\n",
        "done\n\nrequire_gate_digest() {",
        "common input availability loop",
    )[: -len("\n\nrequire_gate_digest() {")]
    for forbidden_cross_input in (
        "HOSTED_RAW_CHECK",
        "HOSTED_RAW_SELF_TEST",
        "FONT_ALPHA_CHECK",
        "FONT_ALPHA_SELF_TEST",
        "RETAINED_HOSTED_RAW_FIXTURE",
        "HOSTED_RAW_PROFILE_RECEIPT",
        "RETAINED_FONT_ALPHA_FIXTURE",
        "PANDOC_PORTABILITY_RECEIPT_CHECK",
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST",
        "LEGACY_PANDOC_PORTABILITY_RECEIPT",
        "TRAILER_ID_OBSERVATION_CHECK",
        "TRAILER_ID_OBSERVATION_SELF_TEST",
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT",
    ):
        if (
            forbidden_cross_input in common_gate_loop
            or forbidden_cross_input in common_input_loop
        ):
            raise WiringError(
                f"exact/common availability depends on cross input: {forbidden_cross_input}"
            )

    if "tuple_has" in source:
        raise WiringError("line-oriented tuple_has matching must not reappear")
    if re.search(r"PID_RS_[A-Z0-9_]*PROFILE", source):
        raise WiringError("profile selection accepts an environment override")
    for forbidden_indirection in ("eval ", "declare -n", "${!"):
        if forbidden_indirection in source:
            raise WiringError(
                f"checker/profile indirection is forbidden: {forbidden_indirection}"
            )

    digest_function = extract_unique(
        source,
        "require_gate_digest() {\n",
        "}\nrequire_profile_input() {",
        "gate digest function",
    )[: -len("\nrequire_profile_input() {")]
    require_region_digest(
        digest_function,
        EXPECTED_GATE_DIGEST_FUNCTION_SHA256,
        "stable gate digest function",
    )
    for token in (
        'nofollow = getattr(os, "O_NOFOLLOW", None)',
        'nonblock = getattr(os, "O_NONBLOCK", None)',
        "def digest_stable_gate(path):",
        "opened.st_nlink != 1",
        "opened.st_size > 4 * 1024 * 1024",
        "not same_identity(path_before, opened)",
        "not same_identity(opened, descriptor_after)",
        "not same_identity(opened, path_after)",
        'if [[ "$observed" != "$expected" ]]; then',
    ):
        if token not in digest_function:
            raise WiringError(f"stable gate digest lost custody anchor: {token}")
    if "shasum" in digest_function or ".read_bytes()" in digest_function:
        raise WiringError("gate digest reverted to an unbounded pathname reader")
    profile_input_function = extract_unique(
        source,
        "require_profile_input() {\n",
        '}\nrequire_gate_digest "$STRUCTURE_CHECK"',
        "selected profile input function",
    )[: -len('\nrequire_gate_digest "$STRUCTURE_CHECK"')]
    expected_profile_input_function = (
        "require_profile_input() {\n"
        '  local profile_path="$1" label="$2"\n'
        '  if [[ ! -f "$profile_path" || -L "$profile_path" ]]; then\n'
        '    echo "$CHECK_NAME: selected $label absent, non-regular, or symbolic: $profile_path" >&2\n'
        "    exit 1\n"
        "  fi\n"
        "}"
    )
    if profile_input_function != expected_profile_input_function:
        raise WiringError("selected profile input check changed")
    startup_digest_with_anchor = extract_unique(
        source,
        '}\nrequire_gate_digest "$STRUCTURE_CHECK" "$STRUCTURE_CHECK_SHA256" "strict structure checker"\n',
        'python3 -I -S -B "$PANDOC_TEX_NORMALIZER_SELF_TEST"',
        "startup digest dispatch",
    )
    startup_digest_dispatch = startup_digest_with_anchor[
        len("}\n") : -len('\npython3 -I -S -B "$PANDOC_TEX_NORMALIZER_SELF_TEST"')
    ]
    for forbidden_cross_input in (
        "HOSTED_RAW",
        "FONT_ALPHA",
        "RETAINED_HOSTED",
        "RETAINED_FONT",
        "PANDOC_PORTABILITY_RECEIPT",
        "TRAILER_ID_OBSERVATION",
        "LEGACY_PANDOC_PORTABILITY",
        "LEGACY_TRAILER_ID_OBSERVATION",
    ):
        if forbidden_cross_input in startup_digest_dispatch:
            raise WiringError(
                f"exact startup digests a cross input: {forbidden_cross_input}"
            )

    capture_function = extract_unique(
        source,
        "capture_cross_producer_tuple() {\n",
        "}\n\nselect_cross_profile_from_tuple() {",
        "producer capture function",
    )[: -len("\n\nselect_cross_profile_from_tuple() {")]
    require_region_digest(
        capture_function, EXPECTED_CAPTURE_FUNCTION_SHA256, "producer capture function"
    )
    for token in (
        'nofollow = getattr(os, "O_NOFOLLOW", None)',
        'nonblock = getattr(os, "O_NONBLOCK", None)',
        "def terminate_probe(process):",
        "os.killpg(process.pid, signal.SIGKILL)",
        "def run_probe(command, arguments, label, path_value, *",
        "os.set_blocking(stream.fileno(), False)",
        "selector.select(remaining)",
        'env={"PATH": path_value, "LC_ALL": "C", "LANG": "C"}',
        "start_new_session=True",
        "close_fds=True",
        "if len(buffers[stream_name]) > maximum:",
        'reject(f"{label} exceeded its time bound")',
        '("-var-value=TEXMFSYSVAR",)',
        '"--engine=luahbtex",',
        '"--progname=lualatex",',
        '"--must-exist",',
        '"--format=fmt",',
        '"lualatex.fmt",',
        "not same_identity(resolved_before, opened)",
        "not same_identity(opened, resolved_after)",
        "not same_identity(command_before, command_after)",
        "def require_same_snapshot(label, first, second):",
        'reject(f"{label} changed across its probe")',
        "def publish_tuple(output, payload):",
        'directory = getattr(os, "O_DIRECTORY", None)',
        "parent_descriptor = os.open(parent, parent_flags)",
        "dir_fd=parent_descriptor",
        "os.fsync(descriptor)",
        "reread != payload",
        "not same_object(parent_after, parent_path_after)",
        "not same_object(output_stat, output_absolute_after)",
        "created_stat = os.fstat(descriptor)",
        "if not published and created_stat is not None:",
        "if same_object(created_stat, rollback_stat):",
        "format_path != expected_format_path",
        "format_mode & (stat.S_IWGRP | stat.S_IWOTH)",
        "format_stat.st_uid == os.geteuid() and format_mode & stat.S_IWUSR",
        "os.access(format_real, os.W_OK)",
        '("format_kind", "regular")',
        '("format_mode", format(format_mode, "04o"))',
        '("format_nlink", str(format_stat.st_nlink))',
        '("format_uid", str(format_stat.st_uid))',
        '("format_gid", str(format_stat.st_gid))',
        '("format_writable", "no")',
        '("pandoc_sha256", pandoc_sha)',
        '("renderer_sha256", lualatex_sha)',
        '("format_sha256", format_sha)',
    ):
        if token not in capture_function:
            raise WiringError(f"producer capture lost required closure: {token}")
    if capture_function.count("require_same_snapshot(") != 5:
        raise WiringError(
            "producer commands/formats lack exact pre/post snapshot checks"
        )
    for forbidden_capture in (
        ".read_bytes()",
        "probe_root",
        '.stdout"',
        '.stderr"',
    ):
        if forbidden_capture in capture_function:
            raise WiringError(
                f"producer capture restored an unbounded probe file: {forbidden_capture}"
            )
    for forbidden in ("BUILT", "COMMITTED", "HOSTED_RAW_CHECK", "FONT_ALPHA_CHECK"):
        if forbidden in capture_function:
            raise WiringError(
                f"producer capture depends on artifact relation state: {forbidden}"
            )

    selector_function = extract_unique(
        source,
        "select_cross_profile_from_tuple() {\n",
        "}\n\nTMP_BASE=",
        "profile selector function",
    )[: -len("\n\nTMP_BASE=")]
    require_region_digest(
        selector_function,
        EXPECTED_SELECTOR_FUNCTION_SHA256,
        "producer selector function",
    )
    for token in (
        'nofollow = getattr(os, "O_NOFOLLOW", None)',
        'nonblock = getattr(os, "O_NONBLOCK", None)',
        "def read_stable_tuple(tuple_path):",
        "raw, before = read_stable_tuple(tuple_path)",
        "opened = os.fstat(descriptor)",
        "path_after = tuple_path.lstat()",
        'expected_keys = (\n    "pandoc_command",',
        "if len(lines) != len(expected_keys):",
        "for index, (line, expected_key) in enumerate(",
        'records["format_kind"] == "regular"',
        'records["format_nlink"] == "1"',
        'records["format_writable"] == "no"',
        "matches = []",
        'matches.append(hosted["profile"])',
        'matches.append(legacy["profile"])',
        "if len(matches) != 1 or not matches[0]:",
        'reject(f"tuple matched {len(matches)} supported profiles")',
        "print(f\"{matches[0]}\\t{base64.b64encode(raw).decode('ascii')}\")",
    ):
        if token not in selector_function:
            raise WiringError(f"selector lost a fail-closed anchor: {token}")
    if selector_function.count("matches.append(") != 2:
        raise WiringError("selector does not have exactly two closed predicates")
    if ".read_bytes()" in selector_function:
        raise WiringError("producer custody reverted to pathname read_bytes")
    if "hashlib.sha256(raw)" in selector_function:
        raise WiringError("exact tuple evidence was weakened to digest-only equality")
    for forbidden in (
        "BUILT",
        "COMMITTED",
        "HOSTED_RAW_CHECK",
        "FONT_ALPHA_CHECK",
        "RETAINED_HOSTED",
        "RETAINED_FONT",
        "cmp -s",
        "|| true",
        "fallback",
        "HOSTED_FORMAT_BYTES",
        "HOSTED_FORMAT_SHA256",
    ):
        if forbidden in selector_function:
            raise WiringError(
                f"profile selection depends on forbidden state: {forbidden}"
            )

    prebuild_dispatch = extract_unique(
        source,
        "# CROSS_PROFILE_SELECTION_BEGIN\n",
        "# CROSS_PROFILE_SELECTION_END",
        "pre-build profile dispatch",
    )
    for token, label in (
        (
            'python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted',
            "hosted normal source-separation check",
        ),
        (
            'python3 -O -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted',
            "hosted optimized source-separation check",
        ),
        (
            'python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy',
            "legacy normal source-separation check",
        ),
        (
            'python3 -O -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy',
            "legacy optimized source-separation check",
        ),
        ('python3 -I -B "$HOSTED_RAW_SELF_TEST"', "hosted normal self-test"),
        ('python3 -O -I -B "$HOSTED_RAW_SELF_TEST"', "hosted optimized self-test"),
        ('python3 -I -B "$FONT_ALPHA_SELF_TEST"', "legacy normal self-test"),
        ('python3 -O -I -B "$FONT_ALPHA_SELF_TEST"', "legacy optimized self-test"),
    ):
        if prebuild_dispatch.count(token) != 1:
            raise WiringError(f"{label} count changed")
    if "BUILT" in prebuild_dispatch:
        raise WiringError("pre-build selector inspects a candidate")
    hosted_prebuild = extract_unique(
        prebuild_dispatch,
        '    "$HOSTED_PROFILE_ID")\n',
        '      ;;\n    "$LEGACY_PROFILE_ID")',
        "hosted pre-build route",
    )
    legacy_prebuild = extract_unique(
        prebuild_dispatch,
        '    "$LEGACY_PROFILE_ID")\n',
        "      ;;\n    *)",
        "legacy pre-build route",
    )
    for forbidden in (
        "FONT_ALPHA",
        "RETAINED_FONT_ALPHA",
        "PANDOC_PORTABILITY_RECEIPT",
        "TRAILER_ID_OBSERVATION",
        "LEGACY_PANDOC_PORTABILITY",
        "LEGACY_TRAILER_ID_OBSERVATION",
    ):
        if forbidden in hosted_prebuild:
            raise WiringError(f"hosted pre-build route uses legacy state: {forbidden}")
    for forbidden in ("HOSTED_RAW", "RETAINED_HOSTED"):
        if forbidden in legacy_prebuild:
            raise WiringError(f"legacy pre-build route uses hosted state: {forbidden}")
    selected_source_calls = Counter(
        line
        for line in source.splitlines()
        if '"$MODE_WIRING_SELF_TEST" --selected-profile-source' in line
    )
    expected_selected_source_calls = Counter(
        (
            '      python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted',
            '      python3 -O -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted',
            '      python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy',
            '      python3 -O -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy',
        )
    )
    if selected_source_calls != expected_selected_source_calls:
        raise WiringError("selected profile source-check call inventory changed")

    postbuild_guard = extract_unique(
        source,
        'if [[ "$MODE" == "--cross-toolchain" ]]; then\n'
        '  capture_cross_producer_tuple after "$PRODUCER_TUPLE_AFTER"',
        'fi\nif [[ -s "$BUILD_ROOT/build.stderr" ]]; then',
        "post-build producer guard",
    )[: -len('\nif [[ -s "$BUILD_ROOT/build.stderr" ]]; then')]
    require_region_digest(
        postbuild_guard, EXPECTED_POSTBUILD_GUARD_SHA256, "post-build tuple guard"
    )
    if postbuild_guard.count("select_cross_profile_from_tuple") != 1:
        raise WiringError("post-build guard does not reselect exactly once")
    for token in (
        'CROSS_SELECTION_AFTER="$(select_cross_profile_from_tuple "$PRODUCER_TUPLE_AFTER")"',
        '"$CROSS_TUPLE_BASE64_AFTER" != "$CROSS_TUPLE_BASE64"',
        '-n "$CROSS_EXTRA_AFTER"',
    ):
        if token not in postbuild_guard:
            raise WiringError(f"post-build guard lost held-read evidence: {token}")
    if (
        "cmp -s" in postbuild_guard
        or "! -f" in postbuild_guard
        or "-L" in postbuild_guard
    ):
        raise WiringError("post-build guard reopens tuple pathnames")
    if "BUILT" in postbuild_guard or "COMMITTED" in postbuild_guard:
        raise WiringError("post-build producer guard inspects PDF bytes")

    relation_dispatch = extract_unique(
        source,
        'validate_pdf committed "$COMMITTED" strict\n',
        'esac\n\nif ! cmp -s "$BUILD_ROOT/built.font-roster"',
        "relation dispatch",
    )[: -len('\n\nif ! cmp -s "$BUILD_ROOT/built.font-roster"')]
    expected_relation = (
        'validate_pdf committed "$COMMITTED" strict\n'
        'case "$MODE:$CROSS_PROFILE" in\n'
        "  --exact:)\n"
        '    validate_pdf built "$BUILT" strict\n'
        "    ;;\n"
        '  --cross-toolchain:"$HOSTED_PROFILE_ID")\n'
        "    # The hosted checker raw-binds its current-format fixture before strict validation.\n"
        '    validate_pdf built "$BUILT" hosted-raw-and-strict\n'
        "    ;;\n"
        '  --cross-toolchain:"$LEGACY_PROFILE_ID")\n'
        "    # The legacy checker raw-binds both references before its typed font-key proof.\n"
        '    validate_pdf built "$BUILT" legacy-typed-font-alpha-from-committed\n'
        "    ;;\n"
        "  *)\n"
        '    echo "$CHECK_NAME: mode/profile dispatch is empty, unknown, or inconsistent" >&2\n'
        "    exit 1\n"
        "    ;;\n"
        "esac"
    )
    if relation_dispatch != expected_relation:
        raise WiringError("relation dispatch changed")

    command_with_anchor = extract_unique(
        source,
        '  case "$structure_relation" in\n',
        '  esac\n  if ! "${structure_command[@]}"',
        "checker-command dispatch",
    )
    command_dispatch = command_with_anchor[: -len('\n  if ! "${structure_command[@]}"')]
    for token, count, label in (
        ('"$STRUCTURE_CHECK"', 2, "strict checker"),
        ('"$HOSTED_RAW_CHECK"', 2, "hosted checker"),
        ('"$FONT_ALPHA_CHECK"', 2, "alpha checker"),
        ('"$RETAINED_HOSTED_RAW_FIXTURE"', 2, "hosted fixture"),
        ('"$RETAINED_FONT_ALPHA_FIXTURE"', 2, "legacy fixture"),
    ):
        if command_dispatch.count(token) != count:
            raise WiringError(f"{label} command count changed")
    hosted_case = extract_unique(
        command_dispatch,
        "    hosted-raw-and-strict)\n",
        "      ;;\n    legacy-typed-font-alpha-from-committed)",
        "hosted checker case",
    )
    if "FONT_ALPHA" in hosted_case or "COMMITTED" in hosted_case:
        raise WiringError("hosted route invokes or depends on legacy comparator")
    legacy_case = extract_unique(
        command_dispatch,
        "    legacy-typed-font-alpha-from-committed)\n",
        "      ;;\n    *)",
        "legacy checker case",
    )
    if "HOSTED_RAW" in legacy_case:
        raise WiringError("legacy route invokes hosted checker")

    artifact_with_anchor = extract_unique(
        source,
        'if [[ "$MODE" == "--exact" ]]; then\n  cmp -s "$BUILT" "$COMMITTED" || {',
        'fi\n\nif ! cmp -s "$BUILD_ROOT/built.observed-urls"',
        "artifact dispatch",
    )
    artifact_dispatch = artifact_with_anchor[
        : -len('\n\nif ! cmp -s "$BUILD_ROOT/built.observed-urls"')
    ]
    for forbidden in (
        "HOSTED_RAW",
        "FONT_ALPHA",
        "PANDOC_PORTABILITY_RECEIPT",
        "TRAILER_ID_OBSERVATION",
        "LEGACY_PANDOC_PORTABILITY",
        "LEGACY_TRAILER_ID_OBSERVATION",
        HOSTED_BASENAME,
        ALPHA_BASENAME,
        LEGACY_PORTABILITY_CHECK_BASENAME,
        LEGACY_PORTABILITY_SELF_TEST_BASENAME,
        LEGACY_PORTABILITY_RECEIPT_BASENAME,
        LEGACY_TRAILER_CHECK_BASENAME,
        LEGACY_TRAILER_SELF_TEST_BASENAME,
        LEGACY_TRAILER_RECEIPT_BASENAME,
    ):
        if forbidden in artifact_dispatch:
            raise WiringError(
                f"exact artifact dispatch invokes cross checker: {forbidden}"
            )
    if (
        "committed PDF is stale or not same-toolchain reproducible"
        not in artifact_dispatch
    ):
        raise WiringError("exact raw-comparison diagnostic is absent")

    order = (
        source.index("# CROSS_PROFILE_SELECTION_BEGIN"),
        source.index('PID_RS_PDF_TMPDIR="$BUILD_ROOT" bash'),
        source.index('capture_cross_producer_tuple after "$PRODUCER_TUPLE_AFTER"'),
        source.index('validate_pdf committed "$COMMITTED" strict'),
        source.index('cmp -s "$BUILT" "$COMMITTED" || {'),
    )
    if tuple(sorted(order)) != order:
        raise WiringError("selection/build/reprobe/relation/exact order changed")

    final_digest_dispatch = extract_unique(
        source,
        'case "$MODE:$CROSS_PROFILE" in\n  --exact:) ;;\n',
        "esac\n\nRENDER_PREFIX=",
        "final profile digest dispatch",
    )[: -len("\n\nRENDER_PREFIX=")]
    expected_final_digest_dispatch = (
        'case "$MODE:$CROSS_PROFILE" in\n'
        "  --exact:) ;;\n"
        '  --cross-toolchain:"$HOSTED_PROFILE_ID")\n'
        '    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \\\n'
        '      "hosted raw-profile checker"\n'
        '    require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \\\n'
        '      "hosted raw-profile checker self-test"\n'
        '    require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \\\n'
        '      "$HOSTED_RAW_PROFILE_RECEIPT_SHA256" "hosted raw-profile provenance receipt"\n'
        "    ;;\n"
        '  --cross-toolchain:"$LEGACY_PROFILE_ID")\n'
        '    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \\\n'
        '      "typed font-alpha comparator"\n'
        '    require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \\\n'
        '      "typed font-alpha comparator self-test"\n'
        '    require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \\\n'
        '      "$PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256" \\\n'
        '      "historical Pandoc portability receipt checker"\n'
        '    require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \\\n'
        '      "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256" \\\n'
        '      "historical Pandoc portability receipt checker self-test"\n'
        '    require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \\\n'
        '      "$LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256" \\\n'
        '      "historical Pandoc portability receipt"\n'
        '    require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \\\n'
        '      "$TRAILER_ID_OBSERVATION_CHECK_SHA256" \\\n'
        '      "historical trailer-ID observation checker"\n'
        '    require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \\\n'
        '      "$TRAILER_ID_OBSERVATION_SELF_TEST_SHA256" \\\n'
        '      "historical trailer-ID observation checker self-test"\n'
        '    require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \\\n'
        '      "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256" \\\n'
        '      "historical trailer-ID observation receipt"\n'
        "    ;;\n"
        "  *)\n"
        '    echo "$CHECK_NAME: final mode/profile digest dispatch is inconsistent" >&2\n'
        "    exit 1\n"
        "    ;;\n"
        "esac"
    )
    if final_digest_dispatch != expected_final_digest_dispatch:
        raise WiringError("final selected-profile digest dispatch changed")

    routed_variables = (
        "HOSTED_RAW_CHECK",
        "HOSTED_RAW_SELF_TEST",
        "FONT_ALPHA_CHECK",
        "FONT_ALPHA_SELF_TEST",
        "HOSTED_RAW_PROFILE_RECEIPT",
        "PANDOC_PORTABILITY_RECEIPT_CHECK",
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST",
        "LEGACY_PANDOC_PORTABILITY_RECEIPT",
        "TRAILER_ID_OBSERVATION_CHECK",
        "TRAILER_ID_OBSERVATION_SELF_TEST",
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT",
    )
    routed_names = "|".join(map(re.escape, routed_variables))
    routed_expansion = re.compile(
        r"\$(?:\{(?:" + routed_names + r")\}|(?:" + routed_names + r")(?![A-Z0-9_]))"
    )
    observed_inventory = Counter(
        line for line in source.splitlines() if routed_expansion.search(line)
    )
    expected_inventory = Counter(
        (
            '      require_profile_input "$HOSTED_RAW_CHECK" "hosted raw-profile checker"',
            '      require_profile_input "$HOSTED_RAW_SELF_TEST" "hosted raw-profile checker self-test"',
            '      require_profile_input "$HOSTED_RAW_PROFILE_RECEIPT" "hosted raw-profile provenance receipt"',
            '      require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \\',
            '      require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \\',
            '      require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \\',
            '      python3 -I -B "$HOSTED_RAW_SELF_TEST" "$RETAINED_HOSTED_RAW_FIXTURE"',
            '      python3 -O -I -B "$HOSTED_RAW_SELF_TEST" "$RETAINED_HOSTED_RAW_FIXTURE"',
            '      require_profile_input "$FONT_ALPHA_CHECK" "typed font-alpha comparator"',
            '      require_profile_input "$FONT_ALPHA_SELF_TEST" "typed font-alpha comparator self-test"',
            '      require_profile_input "$PANDOC_PORTABILITY_RECEIPT_CHECK" \\',
            '      require_profile_input "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \\',
            '      require_profile_input "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \\',
            '      require_profile_input "$TRAILER_ID_OBSERVATION_CHECK" \\',
            '      require_profile_input "$TRAILER_ID_OBSERVATION_SELF_TEST" \\',
            '      require_profile_input "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \\',
            '      require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \\',
            '      require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \\',
            '      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \\',
            '      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \\',
            '      require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \\',
            '      require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \\',
            '      require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \\',
            '      require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \\',
            '      python3 -I -B "$PANDOC_PORTABILITY_RECEIPT_CHECK"',
            '      python3 -O -I -B "$PANDOC_PORTABILITY_RECEIPT_CHECK"',
            '      python3 -I -B "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST"',
            '      python3 -O -I -B "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST"',
            '      python3 -I -B "$TRAILER_ID_OBSERVATION_CHECK"',
            '      python3 -O -I -B "$TRAILER_ID_OBSERVATION_CHECK"',
            '      python3 -I -B "$TRAILER_ID_OBSERVATION_SELF_TEST"',
            '      python3 -O -I -B "$TRAILER_ID_OBSERVATION_SELF_TEST"',
            '      python3 -I -B "$FONT_ALPHA_SELF_TEST" "$COMMITTED" \\',
            '      python3 -O -I -B "$FONT_ALPHA_SELF_TEST" "$COMMITTED" \\',
            '    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \\',
            '    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \\',
            '      structure_command=(python3 -I -B "$HOSTED_RAW_CHECK" \\',
            '      optimized_structure_command=(python3 -O -I -B "$HOSTED_RAW_CHECK" \\',
            '      structure_command=(python3 -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf" \\',
            '      optimized_structure_command=(python3 -O -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf" \\',
            '    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \\',
            '    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \\',
            '    require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \\',
            '    require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \\',
            '    require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \\',
            '    require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \\',
            '    require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \\',
            '    require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \\',
            '    require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \\',
            '    require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \\',
            '    require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \\',
            '    require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \\',
            '    require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \\',
            '      require_gate_digest "$HOSTED_RAW_CHECK" "$HOSTED_RAW_CHECK_SHA256" \\',
            '      require_gate_digest "$HOSTED_RAW_SELF_TEST" "$HOSTED_RAW_SELF_TEST_SHA256" \\',
            '      require_gate_digest "$HOSTED_RAW_PROFILE_RECEIPT" \\',
            '      require_gate_digest "$FONT_ALPHA_CHECK" "$FONT_ALPHA_CHECK_SHA256" \\',
            '      require_gate_digest "$FONT_ALPHA_SELF_TEST" "$FONT_ALPHA_SELF_TEST_SHA256" \\',
            '      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_CHECK" \\',
            '      require_gate_digest "$PANDOC_PORTABILITY_RECEIPT_SELF_TEST" \\',
            '      require_gate_digest "$LEGACY_PANDOC_PORTABILITY_RECEIPT" \\',
            '      require_gate_digest "$TRAILER_ID_OBSERVATION_CHECK" \\',
            '      require_gate_digest "$TRAILER_ID_OBSERVATION_SELF_TEST" \\',
            '      require_gate_digest "$LEGACY_TRAILER_ID_OBSERVATION_RECEIPT" \\',
        )
    )
    if observed_inventory != expected_inventory:
        extra = observed_inventory - expected_inventory
        missing = expected_inventory - observed_inventory
        raise WiringError(
            f"global cross-checker call/reference inventory changed: "
            f"extra={dict(extra)!r}; missing={dict(missing)!r}"
        )
    return WiringFragments(
        mode_guard,
        digest_function,
        capture_function,
        selector_function,
        prebuild_dispatch,
        postbuild_guard,
        relation_dispatch,
        command_dispatch,
        artifact_dispatch,
    )


def run_bash(script: pathlib.Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["bash", "--noprofile", "--norc", str(script), *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as error:
        raise WiringError(f"shell harness exceeded its time bound: {script}") from error


def exercise_mode_guard(root: pathlib.Path, fragment: str) -> int:
    harness = root / "mode-guard.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "CHECK_NAME='Mathematical results guide PDF check'\n"
        + fragment
        + "\n",
        encoding="utf-8",
    )
    controls = 0
    for arguments in ((), ("--exact",)):
        require_clean_success(
            run_bash(harness, *arguments), f"mode guard {arguments!r}"
        )
        controls += 1
    require_clean_success(
        run_bash(harness, "--cross-toolchain"), "mode guard cross-toolchain"
    )
    controls += 1
    for arguments in (
        ("unknown",),
        ("--exact", "junk"),
        ("--cross-toolchain", "junk"),
        ("--exact", "junk", "more"),
    ):
        result = run_bash(harness, *arguments)
        if (
            result.returncode != 2
            or result.stdout
            or result.stderr != f"usage: {harness} [--exact|--cross-toolchain]\n"
        ):
            raise WiringError(
                f"mode guard did not reject {arguments!r} exactly: "
                f"rc={result.returncode}, stdout={result.stdout!r}, "
                f"stderr={result.stderr!r}"
            )
        controls += 1
    return controls


def require_clean_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0 or result.stdout or result.stderr:
        raise WiringError(
            f"{label} failed or emitted diagnostics: rc={result.returncode}; "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )


def require_closed_failure(
    result: subprocess.CompletedProcess[str], diagnostic: str, label: str
) -> None:
    if result.returncode == 0 or result.stdout or diagnostic not in result.stderr:
        raise WiringError(
            f"{label} did not fail closed: rc={result.returncode}; "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )


def extract_embedded_python(fragment: str, label: str) -> str:
    matches = re.findall(r"<<'PY'\n(.*?)\nPY", fragment, flags=re.DOTALL)
    if len(matches) != 1:
        raise WiringError(f"{label} embedded Python block count is {len(matches)}")
    return matches[0]


def extract_python_bindings(source: str, names: tuple[str, ...], label: str) -> str:
    tree = ast.parse(source, filename=label)
    bindings: dict[str, ast.stmt] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bindings[node.name] = node
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                bindings[target.id] = node
    missing = [name for name in names if name not in bindings]
    if missing:
        raise WiringError(f"{label} lacks extracted bindings: {missing}")
    return "\n\n".join(ast.unparse(bindings[name]) for name in names)


def exercise_capture_custody_hostiles(
    root: pathlib.Path,
    digest_fragment: str,
    capture_fragment: str,
    selector_fragment: str,
) -> int:
    digest_python = extract_embedded_python(digest_fragment, "stable gate digest")
    capture_python = extract_embedded_python(capture_fragment, "producer capture")
    selector_python = extract_embedded_python(selector_fragment, "producer selector")
    digest_bindings = extract_python_bindings(
        digest_python,
        ("reject", "STABLE_FIELDS", "same_identity", "digest_stable_gate"),
        "stable gate digest custody",
    )
    digest_root = root / "gate-digest-custody"
    digest_root.mkdir(mode=0o700)
    digest_harness = digest_root / "digest.py"
    digest_harness.write_text(
        "import hashlib\nimport os\nimport pathlib\nimport stat\nimport sys\n\n"
        + digest_bindings
        + "\n\nREAL_OS = os\n"
        + "class RaceOs:\n"
        + "    def __init__(self, target):\n"
        + "        self.target = target\n        self.raced = False\n\n"
        + "    def __getattr__(self, name):\n"
        + "        return getattr(REAL_OS, name)\n\n"
        + "    def open(self, path, flags, *arguments, **keywords):\n"
        + "        if not self.raced and pathlib.Path(path) == self.target:\n"
        + "            self.target.unlink()\n"
        + "            REAL_OS.mkfifo(self.target, 0o600)\n"
        + "            self.raced = True\n"
        + "        return REAL_OS.open(path, flags, *arguments, **keywords)\n\n"
        + "target = pathlib.Path(sys.argv[1])\nmode = sys.argv[2]\n"
        + "race_os = RaceOs(target)\n"
        + "if mode == 'race':\n    os = race_os\n"
        + "try:\n    observed = digest_stable_gate(target)\n"
        + "except SystemExit:\n"
        + "    raise SystemExit(0 if mode != 'regular' and (mode != 'race' or race_os.raced) else 12)\n"
        + "if mode != 'regular':\n    raise SystemExit(13)\n"
        + "raise SystemExit(0 if observed == sys.argv[3] else 14)\n",
        encoding="utf-8",
    )
    regular = digest_root / "regular"
    regular.write_bytes(b"stable gate digest control\n")
    regular.chmod(0o444)
    regular_digest = hashlib.sha256(regular.read_bytes()).hexdigest()
    hard_source = digest_root / "hard-source"
    hard_source.write_bytes(b"hard link hostile\n")
    hard_source.chmod(0o444)
    hard_link = digest_root / "hard-link"
    os.link(hard_source, hard_link)
    symbolic = digest_root / "symbolic"
    symbolic.symlink_to(regular)
    race = digest_root / "race"
    race.write_bytes(b"regular before FIFO race\n")
    race.chmod(0o444)
    digest_cases = (
        (regular, "regular", regular_digest),
        (hard_link, "hardlink", "unused"),
        (symbolic, "symlink", "unused"),
        (race, "race", "unused"),
    )
    controls = 0
    for target, mode, expected in digest_cases:
        for optimized in (False, True):
            if mode == "race" and optimized:
                target.unlink()
                target.write_bytes(b"regular before FIFO race\n")
                target.chmod(0o444)
            command = [sys.executable]
            if optimized:
                command.append("-O")
            command.extend(
                ["-I", "-B", str(digest_harness), str(target), mode, expected]
            )
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
            except subprocess.TimeoutExpired as error:
                raise WiringError(f"{mode} gate-digest custody case blocked") from error
            require_clean_success(
                result,
                f"{mode} gate-digest custody ({'optimized' if optimized else 'normal'})",
            )
            controls += 1
    cases = (
        (
            "snapshot",
            extract_python_bindings(
                capture_python,
                (
                    "reject",
                    "STABLE_FIELDS",
                    "same_identity",
                    "nonblocking_read_flags",
                    "snapshot",
                ),
                "snapshot custody",
            ),
            'snapshot(str(target), "race snapshot", direct=True, '
            "executable=False, maximum=8192)",
        ),
        (
            "tuple",
            extract_python_bindings(
                selector_python,
                ("reject", "STABLE_FIELDS", "same_identity", "read_stable_tuple"),
                "tuple custody",
            ),
            "read_stable_tuple(target)",
        ),
    )
    for name, bindings, invocation in cases:
        case_root = root / f"fifo-race-{name}"
        case_root.mkdir(mode=0o700)
        target = case_root / "initially-regular"
        target.write_bytes(b"regular before the deterministic open race\n")
        target.chmod(0o444)
        harness = case_root / "race.py"
        harness.write_text(
            "import hashlib\nimport os\nimport pathlib\nimport stat\nimport sys\n\n"
            + bindings
            + "\n\nREAL_OS = os\n"
            + "class RaceOs:\n"
            + "    def __init__(self, race_target):\n"
            + "        self.target = race_target\n"
            + "        self.raced = False\n\n"
            + "    def __getattr__(self, name):\n"
            + "        return getattr(REAL_OS, name)\n\n"
            + "    def open(self, path, flags, *arguments, **keywords):\n"
            + "        if not self.raced and pathlib.Path(path) == self.target:\n"
            + "            self.target.unlink()\n"
            + "            REAL_OS.mkfifo(self.target, 0o600)\n"
            + "            self.raced = True\n"
            + "        return REAL_OS.open(path, flags, *arguments, **keywords)\n\n"
            + "target = pathlib.Path(sys.argv[1]).resolve(strict=True)\n"
            + "race_os = RaceOs(target)\nos = race_os\n"
            + "try:\n"
            + f"    {invocation}\n"
            + "except SystemExit:\n"
            + "    raise SystemExit(0 if race_os.raced else 4)\n"
            + "raise SystemExit(5)\n",
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(harness), str(target)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except subprocess.TimeoutExpired as error:
            raise WiringError(f"{name} regular-to-FIFO race blocked") from error
        require_clean_success(result, f"{name} regular-to-FIFO race")
        controls += 1

    probe_bindings = extract_python_bindings(
        capture_python,
        ("reject", "terminate_probe", "run_probe"),
        "bounded probe execution",
    )
    probe_harness = root / "bounded-probe.py"
    probe_harness.write_text(
        "import os\nimport selectors\nimport signal\nimport subprocess\nimport sys\nimport time\n\n"
        + probe_bindings
        + "\n\nmode = sys.argv[1]\n"
        + "if mode == 'flood':\n"
        + "    arguments = ('-c', \"import os; os.write(1, b'x' * 9000)\")\n"
        + "    timeout_seconds = 1.0\n"
        + "    expected = 'exceeded its output bound'\n"
        + "elif mode == 'hang':\n"
        + "    arguments = ('-c', 'import time; time.sleep(30)')\n"
        + "    timeout_seconds = 0.15\n"
        + "    expected = 'exceeded its time bound'\n"
        + "else:\n"
        + "    raise SystemExit(7)\n"
        + "try:\n"
        + "    run_probe(sys.executable, arguments, mode, os.environ.get('PATH', ''), "
        + "timeout_seconds=timeout_seconds, maximum=8192)\n"
        + "except SystemExit as error:\n"
        + "    raise SystemExit(0 if expected in str(error) else 8)\n"
        + "raise SystemExit(9)\n",
        encoding="utf-8",
    )
    for mode in ("flood", "hang"):
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(probe_harness), mode],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except subprocess.TimeoutExpired as error:
            raise WiringError(
                f"{mode} probe hostile escaped its outer bound"
            ) from error
        require_clean_success(result, f"{mode} probe hostile")
        controls += 1

    publication_bindings = extract_python_bindings(
        capture_python,
        ("reject", "same_object", "private_parent", "publish_tuple"),
        "tuple publication custody",
    )
    publication_root = root / "publication-parent"
    publication_root.mkdir(mode=0o700)
    publication_output = publication_root / "tuple.tsv"
    publication_harness = root / "publication-parent-swap.py"
    publication_harness.write_text(
        "import os\nimport pathlib\nimport stat\nimport sys\n\n"
        + publication_bindings
        + "\n\nREAL_OS = os\n"
        + "class RaceOs:\n"
        + "    def __init__(self, output):\n"
        + "        self.output = output\n"
        + "        self.parent = output.parent\n"
        + "        self.moved = output.parent.with_name(output.parent.name + '-held')\n"
        + "        self.raced = False\n\n"
        + "    def __getattr__(self, name):\n"
        + "        return getattr(REAL_OS, name)\n\n"
        + "    def open(self, path, flags, *arguments, **keywords):\n"
        + "        if (not self.raced and keywords.get('dir_fd') is not None "
        + "and path == self.output.name):\n"
        + "            REAL_OS.rename(self.parent, self.moved)\n"
        + "            REAL_OS.mkdir(self.parent, 0o700)\n"
        + "            self.raced = True\n"
        + "        return REAL_OS.open(path, flags, *arguments, **keywords)\n\n"
        + "output = pathlib.Path(sys.argv[1])\n"
        + "race_os = RaceOs(output)\nos = race_os\n"
        + "try:\n"
        + "    publish_tuple(output, b'field\\tvalue\\n')\n"
        + "except SystemExit:\n"
        + "    raise SystemExit(0 if race_os.raced else 10)\n"
        + "raise SystemExit(11)\n",
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(publication_harness),
                str(publication_output),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except subprocess.TimeoutExpired as error:
        raise WiringError("tuple parent-swap hostile blocked") from error
    require_clean_success(result, "tuple parent-swap hostile")
    controls += 1

    preservation_harness = root / "publication-leaf-preservation.py"
    preservation_harness.write_text(
        "import os\nimport pathlib\nimport stat\nimport sys\n\n"
        + publication_bindings
        + "\n\nREAL_OS = os\n"
        + "class ReplacementOs:\n"
        + "    def __init__(self, output):\n"
        + "        self.output = output\n"
        + "        self.leaf_descriptor = None\n"
        + "        self.parent_descriptor = None\n"
        + "        self.raced = False\n\n"
        + "    def __getattr__(self, name):\n"
        + "        return getattr(REAL_OS, name)\n\n"
        + "    def open(self, path, flags, *arguments, **keywords):\n"
        + "        descriptor = REAL_OS.open(path, flags, *arguments, **keywords)\n"
        + "        if (keywords.get('dir_fd') is not None and path == self.output.name "
        + "and flags & REAL_OS.O_CREAT):\n"
        + "            self.leaf_descriptor = descriptor\n"
        + "            self.parent_descriptor = keywords['dir_fd']\n"
        + "        return descriptor\n\n"
        + "    def fsync(self, descriptor):\n"
        + "        if not self.raced and descriptor == self.leaf_descriptor:\n"
        + "            REAL_OS.rename(self.output.name, 'created-moved', "
        + "src_dir_fd=self.parent_descriptor, dst_dir_fd=self.parent_descriptor)\n"
        + "            foreign = REAL_OS.open(self.output.name, REAL_OS.O_WRONLY | "
        + "REAL_OS.O_CREAT | REAL_OS.O_EXCL, 0o600, dir_fd=self.parent_descriptor)\n"
        + "            REAL_OS.write(foreign, b'foreign\\n')\n"
        + "            REAL_OS.close(foreign)\n"
        + "            self.raced = True\n"
        + "        return REAL_OS.fsync(descriptor)\n\n"
        + "output = pathlib.Path(sys.argv[1])\nmode = sys.argv[2]\n"
        + "if mode == 'existing':\n"
        + "    output.write_bytes(b'existing\\n')\n"
        + "    output.chmod(0o600)\n"
        + "    expected = b'existing\\n'\n"
        + "    race_os = None\n"
        + "elif mode == 'replacement':\n"
        + "    race_os = ReplacementOs(output)\n"
        + "    os = race_os\n"
        + "    expected = b'foreign\\n'\n"
        + "else:\n    raise SystemExit(15)\n"
        + "try:\n    publish_tuple(output, b'ours\\n')\n"
        + "except SystemExit:\n"
        + "    if not output.exists() or output.read_bytes() != expected:\n"
        + "        raise SystemExit(16)\n"
        + "    if mode == 'replacement' and not race_os.raced:\n"
        + "        raise SystemExit(17)\n"
        + "    raise SystemExit(0)\n"
        + "raise SystemExit(18)\n",
        encoding="utf-8",
    )
    for mode in ("existing", "replacement"):
        for optimized in (False, True):
            case_parent = root / f"publication-{mode}-{'o' if optimized else 'n'}"
            case_parent.mkdir(mode=0o700)
            case_output = case_parent / "tuple.tsv"
            command = [sys.executable]
            if optimized:
                command.append("-O")
            command.extend(
                [
                    "-I",
                    "-B",
                    str(preservation_harness),
                    str(case_output),
                    mode,
                ]
            )
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
            except subprocess.TimeoutExpired as error:
                raise WiringError(f"{mode} tuple-leaf preservation blocked") from error
            require_clean_success(
                result,
                f"{mode} tuple-leaf preservation ({'optimized' if optimized else 'normal'})",
            )
            controls += 1
    return controls


def exercise_capture_function(root: pathlib.Path, fragment: str) -> int:
    tools = root / "capture-tools"
    tex_root = root / "texmf"
    format_parent = tex_root / "web2c" / "luahbtex"
    tools.mkdir(mode=0o700)
    format_parent.mkdir(parents=True)
    format_path = format_parent / "lualatex.fmt"

    def write_executable(name: str, body: str) -> pathlib.Path:
        path = tools / name
        path.write_text("#!/bin/sh\nset -eu\n" + body, encoding="utf-8")
        path.chmod(0o555)
        return path

    poison_guard = '[ -z "${PID_RS_CAPTURE_POISON+x}" ] || exit 41\n'
    pandoc = write_executable(
        "pandoc",
        poison_guard
        + '[ "$#" -eq 1 ] && [ "$1" = "--version" ] || exit 42\n'
        + "printf '%s\\n' 'pandoc 3.10.2' 'feature line intentionally ignored'\n",
    )
    lualatex = write_executable(
        "lualatex",
        poison_guard
        + '[ "$#" -eq 1 ] && [ "$1" = "--version" ] || exit 42\n'
        + "printf '%s\\n' 'fixture LuaHBTeX banner'\n",
    )
    kpsewhich = write_executable(
        "kpsewhich",
        poison_guard
        + 'if [ "$#" -eq 1 ] && [ "$1" = "-var-value=TEXMFSYSVAR" ]; then\n'
        + f"  printf '%s\\n' {shlex.quote(str(tex_root))}\n"
        + 'elif [ "$#" -eq 5 ] && [ "$1" = "--engine=luahbtex" ] '
        + '&& [ "$2" = "--progname=lualatex" ] && [ "$3" = "--must-exist" ] '
        + '&& [ "$4" = "--format=fmt" ] && [ "$5" = "lualatex.fmt" ]; then\n'
        + f"  printf '%s\\n' {shlex.quote(str(format_path))}\n"
        + "else\n  exit 42\nfi\n",
    )
    harness = root / "capture.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'BUILD_ROOT="$1"\nPATH="$2"\nexport PATH\n'
        "PID_RS_CAPTURE_POISON=present\nexport PID_RS_CAPTURE_POISON\n"
        "CHECK_NAME=fixture\n"
        + fragment
        + '\ncapture_cross_producer_tuple "$3" "$4"\n',
        encoding="utf-8",
    )
    capture_path = str(tools) + os.pathsep + os.environ.get("PATH", "")
    expected_keys = (
        "pandoc_command",
        "pandoc_realpath",
        "pandoc_version",
        "pandoc_bytes",
        "pandoc_sha256",
        "lualatex_command",
        "renderer_realpath",
        "renderer_version",
        "renderer_bytes",
        "renderer_sha256",
        "kpsewhich_command",
        "kpsewhich_realpath",
        "kpsewhich_bytes",
        "kpsewhich_sha256",
        "texmfsysvar",
        "format_path",
        "format_kind",
        "format_mode",
        "format_nlink",
        "format_uid",
        "format_gid",
        "format_writable",
        "format_bytes",
        "format_sha256",
    )

    def new_build(name: str, mode: int = 0o700) -> tuple[pathlib.Path, pathlib.Path]:
        build = root / name
        build.mkdir(mode=mode)
        build.chmod(mode)
        return build, build / "tuple.tsv"

    def capture(
        name: str, *, build_mode: int = 0o700
    ) -> tuple[subprocess.CompletedProcess[str], pathlib.Path]:
        build, output = new_build(name, build_mode)
        return (
            run_bash(harness, str(build), capture_path, "before", str(output)),
            output,
        )

    def parse_tuple(path: pathlib.Path) -> dict[str, str]:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) != len(expected_keys):
            raise WiringError("captured tuple row count changed")
        records: dict[str, str] = {}
        for expected, line in zip(expected_keys, lines, strict=True):
            key, separator, value = line.partition("\t")
            if key != expected or separator != "\t" or not value or key in records:
                raise WiringError("captured tuple schema or ordering changed")
            records[key] = value
        return records

    format_path.write_bytes(b"fixture-format-observation-A\n")
    format_path.chmod(0o444)
    first_result, first_output = capture("capture-a")
    require_clean_success(first_result, "producer capture observation A")
    first = parse_tuple(first_output)
    expected_stable = {
        "pandoc_command": str(pandoc),
        "pandoc_realpath": str(pandoc),
        "pandoc_version": "pandoc 3.10.2",
        "pandoc_sha256": hashlib.sha256(pandoc.read_bytes()).hexdigest(),
        "lualatex_command": str(lualatex),
        "renderer_realpath": str(lualatex),
        "renderer_version": "fixture LuaHBTeX banner",
        "renderer_sha256": hashlib.sha256(lualatex.read_bytes()).hexdigest(),
        "kpsewhich_command": str(kpsewhich),
        "kpsewhich_realpath": str(kpsewhich),
        "kpsewhich_sha256": hashlib.sha256(kpsewhich.read_bytes()).hexdigest(),
        "texmfsysvar": str(tex_root),
        "format_path": str(format_path),
        "format_kind": "regular",
        "format_mode": "0444",
        "format_nlink": "1",
        "format_uid": str(os.geteuid()),
        "format_gid": str(os.getegid()),
        "format_writable": "no",
    }
    for key, expected in expected_stable.items():
        if first[key] != expected:
            raise WiringError(
                f"producer capture field {key} changed: {first[key]!r} != {expected!r}"
            )
    if first["format_bytes"] != str(format_path.stat().st_size):
        raise WiringError("captured format size is not the actual file size")
    if first["format_sha256"] != hashlib.sha256(format_path.read_bytes()).hexdigest():
        raise WiringError("captured format digest is not the actual file digest")
    controls = 1

    format_path.chmod(0o644)
    format_path.write_bytes(b"fixture-format-observation-B-with-new-size\n")
    format_path.chmod(0o444)
    second_result, second_output = capture("capture-b")
    require_clean_success(second_result, "producer capture observation B")
    second = parse_tuple(second_output)
    for key in expected_stable:
        if second[key] != first[key]:
            raise WiringError(f"stable producer field drifted across captures: {key}")
    if (
        second["format_bytes"] == first["format_bytes"]
        or second["format_sha256"] == first["format_sha256"]
    ):
        raise WiringError("distinct secure format observations were collapsed")
    controls += 1

    format_path.chmod(0o644)
    writable_result, _ = capture("capture-writable")
    require_closed_failure(
        writable_result,
        "LuaLaTeX format is writable by the invoking identity or a broad class",
        "writable format capture",
    )
    controls += 1

    format_path.unlink()
    hard_source = format_parent / "hard-source.fmt"
    hard_source.write_bytes(b"hard-linked format\n")
    hard_source.chmod(0o444)
    os.link(hard_source, format_path)
    hard_result, _ = capture("capture-hardlink")
    require_closed_failure(
        hard_result, "not a singly linked regular file", "hard-linked format capture"
    )
    controls += 1
    format_path.unlink()
    hard_source.unlink()

    symbolic_target = format_parent / "symbolic-target.fmt"
    symbolic_target.write_bytes(b"symbolic format\n")
    symbolic_target.chmod(0o444)
    format_path.symlink_to(symbolic_target)
    symbolic_result, _ = capture("capture-symbolic")
    require_closed_failure(
        symbolic_result,
        "has a symbolic or noncanonical component",
        "symbolic format capture",
    )
    controls += 1
    format_path.unlink()
    symbolic_target.unlink()

    format_path.write_bytes(b"private-parent test\n")
    format_path.chmod(0o444)
    public_result, _ = capture("capture-public-parent", build_mode=0o755)
    require_closed_failure(
        public_result,
        "tuple output parent is noncanonical or not private to this identity",
        "public tuple parent",
    )
    return controls + 1


def exercise_profile_selector(root: pathlib.Path, fragment: str) -> int:
    harness = root / "selector.sh"
    hosted_writer = "1" * 64
    hosted_renderer = "2" * 64
    kpsewhich_digest = "3" * 64
    hosted_format_a = "4" * 64
    hosted_format_b = "5" * 64
    legacy_renderer = "6" * 64
    legacy_format = "7" * 64
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "CHECK_NAME=fixture\nHOSTED_PROFILE_ID=hosted\n"
        "HOSTED_PANDOC_VERSION='pandoc 3.10.2'\n"
        f"HOSTED_PANDOC_SHA256={hosted_writer}\n"
        "HOSTED_RENDERER_REALPATH=/usr/bin/luahbtex\n"
        "HOSTED_RENDERER_VERSION='hosted renderer'\n"
        f"HOSTED_RENDERER_SHA256={hosted_renderer}\n"
        "HOSTED_TEXMFSYSVAR=/var/lib/texmf\n"
        "HOSTED_FORMAT_PATH=/var/lib/texmf/web2c/luahbtex/lualatex.fmt\n"
        "LEGACY_PROFILE_ID=legacy\nLEGACY_PANDOC_REALPATH=/usr/bin/pandoc\n"
        "LEGACY_PANDOC_VERSION='pandoc 3.1.3'\n"
        f"LEGACY_PANDOC_SHA256={'8' * 64}\n"
        "LEGACY_RENDERER_REALPATH=/usr/bin/luahbtex\n"
        "LEGACY_RENDERER_VERSION='legacy renderer'\n"
        f"LEGACY_RENDERER_SHA256={legacy_renderer}\n"
        "LEGACY_TEXMFSYSVAR=/var/lib/texmf\n"
        "LEGACY_FORMAT_PATH=/var/lib/texmf/web2c/luahbtex/lualatex.fmt\n"
        f"LEGACY_FORMAT_BYTES=211\nLEGACY_FORMAT_SHA256={legacy_format}\n"
        'if [[ "${2:-}" == duplicate ]]; then\n'
        "  LEGACY_PANDOC_REALPATH=/fixture/pandoc\n"
        '  LEGACY_PANDOC_VERSION="$HOSTED_PANDOC_VERSION"\n'
        '  LEGACY_PANDOC_SHA256="$HOSTED_PANDOC_SHA256"\n'
        '  LEGACY_RENDERER_VERSION="$HOSTED_RENDERER_VERSION"\n'
        '  LEGACY_RENDERER_SHA256="$HOSTED_RENDERER_SHA256"\n'
        "  LEGACY_FORMAT_BYTES=100\n"
        f"  LEGACY_FORMAT_SHA256={hosted_format_a}\n"
        "fi\n"
        "if [[ \"${2:-}\" == empty-id ]]; then HOSTED_PROFILE_ID=''; fi\n"
        + fragment
        + '\nselect_cross_profile_from_tuple "$1"\n',
        encoding="utf-8",
    )

    expected_keys = (
        "pandoc_command",
        "pandoc_realpath",
        "pandoc_version",
        "pandoc_bytes",
        "pandoc_sha256",
        "lualatex_command",
        "renderer_realpath",
        "renderer_version",
        "renderer_bytes",
        "renderer_sha256",
        "kpsewhich_command",
        "kpsewhich_realpath",
        "kpsewhich_bytes",
        "kpsewhich_sha256",
        "texmfsysvar",
        "format_path",
        "format_kind",
        "format_mode",
        "format_nlink",
        "format_uid",
        "format_gid",
        "format_writable",
        "format_bytes",
        "format_sha256",
    )
    hosted_records = {
        "pandoc_command": "/fixture/pandoc",
        "pandoc_realpath": "/fixture/pandoc",
        "pandoc_version": "pandoc 3.10.2",
        "pandoc_bytes": "101",
        "pandoc_sha256": hosted_writer,
        "lualatex_command": "/usr/bin/lualatex",
        "renderer_realpath": "/usr/bin/luahbtex",
        "renderer_version": "hosted renderer",
        "renderer_bytes": "202",
        "renderer_sha256": hosted_renderer,
        "kpsewhich_command": "/usr/bin/kpsewhich",
        "kpsewhich_realpath": "/usr/bin/kpsewhich",
        "kpsewhich_bytes": "303",
        "kpsewhich_sha256": kpsewhich_digest,
        "texmfsysvar": "/var/lib/texmf",
        "format_path": "/var/lib/texmf/web2c/luahbtex/lualatex.fmt",
        "format_kind": "regular",
        "format_mode": "0444",
        "format_nlink": "1",
        "format_uid": str(os.geteuid()),
        "format_gid": str(os.getegid()),
        "format_writable": "no",
        "format_bytes": "100",
        "format_sha256": hosted_format_a,
    }

    def write_tuple(
        path: pathlib.Path,
        records: dict[str, str],
        *,
        keys: tuple[str, ...] = expected_keys,
    ) -> None:
        path.write_text(
            "".join(f"{key}\t{records[key]}\n" for key in keys),
            encoding="utf-8",
        )

    hosted = root / "hosted-a.tsv"
    write_tuple(hosted, hosted_records)
    hosted_b_records = dict(hosted_records)
    hosted_b_records.update(format_bytes="222", format_sha256=hosted_format_b)
    hosted_b = root / "hosted-b.tsv"
    write_tuple(hosted_b, hosted_b_records)
    legacy_records = dict(hosted_records)
    legacy_records.update(
        pandoc_command="/usr/bin/pandoc",
        pandoc_realpath="/usr/bin/pandoc",
        pandoc_version="pandoc 3.1.3",
        pandoc_sha256="8" * 64,
        renderer_version="legacy renderer",
        renderer_sha256=legacy_renderer,
        format_bytes="211",
        format_sha256=legacy_format,
    )
    legacy = root / "legacy.tsv"
    write_tuple(legacy, legacy_records)
    controls = 0
    for path, expected_profile, label in (
        (hosted, "hosted", "hosted tuple with format observation A"),
        (hosted_b, "hosted", "hosted tuple with format observation B"),
        (legacy, "legacy", "legacy complete tuple"),
    ):
        result = run_bash(harness, str(path))
        payload = path.read_bytes()
        expected = f"{expected_profile}\t{base64.b64encode(payload).decode('ascii')}\n"
        if result.returncode != 0 or result.stdout != expected or result.stderr:
            raise WiringError(f"{label} selection changed: {result}")
        controls += 1

    hostile_paths: list[tuple[pathlib.Path, str]] = []
    empty = root / "empty.tsv"
    empty.write_text("", encoding="utf-8")
    hostile_paths.append((empty, "empty tuple"))
    for field, value, label in (
        ("pandoc_sha256", "9" * 64, "writer drift"),
        ("renderer_sha256", "9" * 64, "renderer drift"),
        ("kpsewhich_realpath", "/fixture/kpsewhich", "kpsewhich path drift"),
        ("format_path", "/fixture/lualatex.fmt", "format path drift"),
        ("format_kind", "directory", "format type drift"),
        ("format_mode", "0644", "owner-writable format mode"),
        ("format_mode", "0464", "group-writable format mode"),
        ("format_nlink", "2", "multiply linked format"),
        ("format_writable", "yes", "writable format observation"),
        ("format_sha256", "bad", "malformed format digest"),
    ):
        records = dict(hosted_records)
        records[field] = value
        path = root / (label.replace(" ", "-") + ".tsv")
        write_tuple(path, records)
        hostile_paths.append((path, label))
    missing = root / "missing.tsv"
    write_tuple(missing, hosted_records, keys=expected_keys[:-1])
    hostile_paths.append((missing, "missing tuple row"))
    reordered = root / "reordered.tsv"
    reordered_keys = (expected_keys[1], expected_keys[0], *expected_keys[2:])
    write_tuple(reordered, hosted_records, keys=reordered_keys)
    hostile_paths.append((reordered, "reordered tuple rows"))
    extra = root / "extra.tsv"
    extra.write_text(
        hosted.read_text(encoding="utf-8") + "extra\trow\n", encoding="utf-8"
    )
    hostile_paths.append((extra, "extra tuple row"))
    duplicate_row = root / "duplicate-row.tsv"
    duplicate_row.write_text(
        hosted.read_text(encoding="utf-8") + f"format_sha256\t{hosted_format_a}\n",
        encoding="utf-8",
    )
    hostile_paths.append((duplicate_row, "duplicate tuple row"))
    symbolic = root / "symbolic.tsv"
    symbolic.symlink_to(hosted)
    hostile_paths.append((symbolic, "symbolic tuple"))
    hard_source = root / "hard-source.tsv"
    hard_source.write_bytes(hosted.read_bytes())
    hard_link = root / "hard-link.tsv"
    os.link(hard_source, hard_link)
    hostile_paths.append((hard_link, "multiply linked tuple"))
    for path, label in hostile_paths:
        require_closed_failure(
            run_bash(harness, str(path)), "producer profile rejected:", label
        )
        controls += 1
    require_closed_failure(
        run_bash(harness, str(hosted), "duplicate"),
        "tuple matched 2 supported profiles",
        "duplicate tuple",
    )
    require_closed_failure(
        run_bash(harness, str(hosted), "empty-id"),
        "tuple matched 0 supported profiles",
        "empty profile ID",
    )
    return controls + 2


def exercise_prebuild_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "prebuild.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'MODE="$1"\nREQUESTED_PROFILE="$2"\nTRACE="$3"\n'
        "BUILD_ROOT=/fixture/build\nPRODUCER_TUPLE_BEFORE=/fixture/before.tsv\n"
        "HOSTED_PROFILE_ID=hosted\nLEGACY_PROFILE_ID=legacy\n"
        "MODE_WIRING_SELF_TEST=/fixture/mode-self.py\n"
        "HOSTED_RAW_SELF_TEST=/fixture/hosted-self.py\n"
        "HOSTED_RAW_CHECK=/fixture/hosted.py\nHOSTED_RAW_CHECK_SHA256=hosted-check-sha\n"
        "HOSTED_RAW_SELF_TEST_SHA256=hosted-self-sha\n"
        "HOSTED_RAW_PROFILE_RECEIPT=/fixture/hosted-receipt.json\n"
        "HOSTED_RAW_PROFILE_RECEIPT_SHA256=hosted-receipt-sha\n"
        "RETAINED_HOSTED_RAW_FIXTURE=/fixture/hosted.pdf\n"
        "FONT_ALPHA_CHECK=/fixture/alpha.py\nFONT_ALPHA_CHECK_SHA256=alpha-check-sha\n"
        "FONT_ALPHA_SELF_TEST=/fixture/alpha-self.py\nFONT_ALPHA_SELF_TEST_SHA256=alpha-self-sha\n"
        "PANDOC_PORTABILITY_RECEIPT_CHECK=/fixture/legacy-receipt-check.py\n"
        "PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256=legacy-receipt-check-sha\n"
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST=/fixture/legacy-receipt-self.py\n"
        "PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256=legacy-receipt-self-sha\n"
        "LEGACY_PANDOC_PORTABILITY_RECEIPT=/fixture/legacy-receipt.json\n"
        "LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256=legacy-receipt-sha\n"
        "TRAILER_ID_OBSERVATION_CHECK=/fixture/legacy-trailer-check.py\n"
        "TRAILER_ID_OBSERVATION_CHECK_SHA256=legacy-trailer-check-sha\n"
        "TRAILER_ID_OBSERVATION_SELF_TEST=/fixture/legacy-trailer-self.py\n"
        "TRAILER_ID_OBSERVATION_SELF_TEST_SHA256=legacy-trailer-self-sha\n"
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT=/fixture/legacy-trailer.json\n"
        "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256=legacy-trailer-sha\n"
        "COMMITTED=/fixture/committed.pdf\n"
        "RETAINED_FONT_ALPHA_FIXTURE=/fixture/legacy.pdf\nCHECK_NAME=fixture\n"
        'capture_cross_producer_tuple() { printf "capture\\t%s\\n" "$1" >>"$TRACE"; }\n'
        'select_cross_profile_from_tuple() { printf "%s\\t%s\\n" '
        '"$REQUESTED_PROFILE" "ZmFrZQo="; }\n'
        'require_profile_input() { printf "input\\t%s\\t%s\\n" "$1" "$2" >>"$TRACE"; }\n'
        'require_gate_digest() { printf "digest\\t%s\\t%s\\t%s\\n" "$1" "$2" "$3" >>"$TRACE"; }\n'
        'python3() { printf "python3" >>"$TRACE"; printf "\\t%s" "$@" >>"$TRACE"; printf "\\n" >>"$TRACE"; }\n'
        + fragment
        + "\n",
        encoding="utf-8",
    )
    cases = (
        ("--exact", "", ""),
        (
            "--cross-toolchain",
            "hosted",
            "capture\tbefore\n"
            "input\t/fixture/hosted.py\thosted raw-profile checker\n"
            "input\t/fixture/hosted-self.py\thosted raw-profile checker self-test\n"
            "input\t/fixture/hosted.pdf\thosted raw-profile fixture\n"
            "input\t/fixture/hosted-receipt.json\thosted raw-profile provenance receipt\n"
            "digest\t/fixture/hosted.py\thosted-check-sha\thosted raw-profile checker\n"
            "digest\t/fixture/hosted-self.py\thosted-self-sha\thosted raw-profile checker self-test\n"
            "digest\t/fixture/hosted-receipt.json\thosted-receipt-sha\thosted raw-profile provenance receipt\n"
            "python3\t-I\t-B\t/fixture/mode-self.py\t--selected-profile-source\thosted\n"
            "python3\t-O\t-I\t-B\t/fixture/mode-self.py\t--selected-profile-source\thosted\n"
            "python3\t-I\t-B\t/fixture/hosted-self.py\t/fixture/hosted.pdf\n"
            "python3\t-O\t-I\t-B\t/fixture/hosted-self.py\t/fixture/hosted.pdf\n"
            "digest\t/fixture/hosted.py\thosted-check-sha\thosted raw-profile checker after selected execution\n"
            "digest\t/fixture/hosted-self.py\thosted-self-sha\thosted raw-profile checker self-test after selected execution\n"
            "digest\t/fixture/hosted-receipt.json\thosted-receipt-sha\thosted raw-profile provenance receipt after selected execution\n",
        ),
        (
            "--cross-toolchain",
            "legacy",
            "capture\tbefore\n"
            "input\t/fixture/alpha.py\ttyped font-alpha comparator\n"
            "input\t/fixture/alpha-self.py\ttyped font-alpha comparator self-test\n"
            "input\t/fixture/legacy.pdf\tlegacy font-alpha fixture\n"
            "input\t/fixture/legacy-receipt-check.py\thistorical Pandoc portability receipt checker\n"
            "input\t/fixture/legacy-receipt-self.py\thistorical Pandoc portability receipt checker self-test\n"
            "input\t/fixture/legacy-receipt.json\thistorical Pandoc portability receipt\n"
            "input\t/fixture/legacy-trailer-check.py\thistorical trailer-ID observation checker\n"
            "input\t/fixture/legacy-trailer-self.py\thistorical trailer-ID observation checker self-test\n"
            "input\t/fixture/legacy-trailer.json\thistorical trailer-ID observation receipt\n"
            "digest\t/fixture/alpha.py\talpha-check-sha\ttyped font-alpha comparator\n"
            "digest\t/fixture/alpha-self.py\talpha-self-sha\ttyped font-alpha comparator self-test\n"
            "digest\t/fixture/legacy-receipt-check.py\tlegacy-receipt-check-sha\thistorical Pandoc portability receipt checker\n"
            "digest\t/fixture/legacy-receipt-self.py\tlegacy-receipt-self-sha\thistorical Pandoc portability receipt checker self-test\n"
            "digest\t/fixture/legacy-receipt.json\tlegacy-receipt-sha\thistorical Pandoc portability receipt\n"
            "digest\t/fixture/legacy-trailer-check.py\tlegacy-trailer-check-sha\thistorical trailer-ID observation checker\n"
            "digest\t/fixture/legacy-trailer-self.py\tlegacy-trailer-self-sha\thistorical trailer-ID observation checker self-test\n"
            "digest\t/fixture/legacy-trailer.json\tlegacy-trailer-sha\thistorical trailer-ID observation receipt\n"
            "python3\t-I\t-B\t/fixture/mode-self.py\t--selected-profile-source\tlegacy\n"
            "python3\t-O\t-I\t-B\t/fixture/mode-self.py\t--selected-profile-source\tlegacy\n"
            "python3\t-I\t-B\t/fixture/legacy-receipt-check.py\n"
            "python3\t-O\t-I\t-B\t/fixture/legacy-receipt-check.py\n"
            "python3\t-I\t-B\t/fixture/legacy-receipt-self.py\n"
            "python3\t-O\t-I\t-B\t/fixture/legacy-receipt-self.py\n"
            "python3\t-I\t-B\t/fixture/legacy-trailer-check.py\n"
            "python3\t-O\t-I\t-B\t/fixture/legacy-trailer-check.py\n"
            "python3\t-I\t-B\t/fixture/legacy-trailer-self.py\n"
            "python3\t-O\t-I\t-B\t/fixture/legacy-trailer-self.py\n"
            "python3\t-I\t-B\t/fixture/alpha-self.py\t/fixture/committed.pdf\t/fixture/legacy.pdf\n"
            "python3\t-O\t-I\t-B\t/fixture/alpha-self.py\t/fixture/committed.pdf\t/fixture/legacy.pdf\n"
            "digest\t/fixture/alpha.py\talpha-check-sha\ttyped font-alpha comparator after selected execution\n"
            "digest\t/fixture/alpha-self.py\talpha-self-sha\ttyped font-alpha comparator self-test after selected execution\n"
            "digest\t/fixture/legacy-receipt-check.py\tlegacy-receipt-check-sha\thistorical Pandoc portability receipt checker after selected execution\n"
            "digest\t/fixture/legacy-receipt-self.py\tlegacy-receipt-self-sha\thistorical Pandoc portability receipt checker self-test after selected execution\n"
            "digest\t/fixture/legacy-receipt.json\tlegacy-receipt-sha\thistorical Pandoc portability receipt after selected execution\n"
            "digest\t/fixture/legacy-trailer-check.py\tlegacy-trailer-check-sha\thistorical trailer-ID observation checker after selected execution\n"
            "digest\t/fixture/legacy-trailer-self.py\tlegacy-trailer-self-sha\thistorical trailer-ID observation checker self-test after selected execution\n"
            "digest\t/fixture/legacy-trailer.json\tlegacy-trailer-sha\thistorical trailer-ID observation receipt after selected execution\n",
        ),
    )
    controls = 0
    for index, (mode, profile, expected) in enumerate(cases):
        trace = root / f"prebuild-{index}.trace"
        trace.write_text("", encoding="utf-8")
        result = run_bash(harness, mode, profile, str(trace))
        require_clean_success(result, f"{mode}/{profile or 'empty'} pre-build route")
        if trace.read_text(encoding="utf-8") != expected:
            raise WiringError(f"{mode}/{profile or 'empty'} pre-build trace changed")
        controls += 1
    for profile, diagnostic in (
        ("", "cross-toolchain producer evidence is malformed"),
        ("unknown", "internal unsupported cross-toolchain profile"),
        ("hosted legacy", "internal unsupported cross-toolchain profile"),
    ):
        trace = root / ("prebuild-hostile-" + (profile or "empty"))
        trace.write_text("", encoding="utf-8")
        require_closed_failure(
            run_bash(harness, "--cross-toolchain", profile, str(trace)),
            diagnostic,
            f"pre-build profile {profile!r}",
        )
        controls += 1
    return controls


def exercise_postbuild_guard(root: pathlib.Path, fragment: str) -> int:
    harness = root / "postbuild.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'MODE="$1"\nCROSS_PROFILE="$2"\nPRODUCER_TUPLE_BEFORE="$3"\n'
        'PRODUCER_TUPLE_AFTER="$4"\nAFTER_SOURCE="$5"\nSCENARIO="$6"\n'
        "CHECK_NAME=fixture\n"
        'CROSS_TUPLE_BASE64="$(base64 <"$PRODUCER_TUPLE_BEFORE" | tr -d "\\n")"\n'
        'capture_cross_producer_tuple() { cp "$AFTER_SOURCE" "$2"; }\n'
        "select_cross_profile_from_tuple() {\n"
        '  local selected payload\n  selected="$(sed -n "1s/^profile[[:space:]]//p" "$1")"\n'
        '  payload="$(base64 <"$1" | tr -d "\\n")"\n'
        '  printf "%s\\t%s\\n" "$selected" "$payload"\n'
        '  if [[ "$1" == "$PRODUCER_TUPLE_AFTER" && "$SCENARIO" == fifo-window ]]; then\n'
        '    rm -f "$PRODUCER_TUPLE_BEFORE" "$PRODUCER_TUPLE_AFTER"\n'
        '    mkfifo "$PRODUCER_TUPLE_BEFORE" "$PRODUCER_TUPLE_AFTER"\n'
        '  elif [[ "$1" == "$PRODUCER_TUPLE_AFTER" && "$SCENARIO" == double-swap ]]; then\n'
        '    printf "substituted\\n" >"$PRODUCER_TUPLE_BEFORE"\n'
        '    printf "substituted\\n" >"$PRODUCER_TUPLE_AFTER"\n'
        "  fi\n}\n" + fragment + "\n",
        encoding="utf-8",
    )

    def run_case(
        name: str,
        mode: str,
        profile: str,
        before_payload: str,
        after_payload: str,
        scenario: str = "none",
    ) -> subprocess.CompletedProcess[str]:
        before = root / f"{name}.before"
        after = root / f"{name}.after"
        source = root / f"{name}.source"
        before.write_text(before_payload, encoding="utf-8")
        source.write_text(after_payload, encoding="utf-8")
        return run_bash(
            harness,
            mode,
            profile,
            str(before),
            str(after),
            str(source),
            scenario,
        )

    payload = "profile\thosted\nformat_sha256\tstable\n"
    require_clean_success(
        run_case("same", "--cross-toolchain", "hosted", payload, payload),
        "identical pre/post tuple",
    )
    require_clean_success(
        run_case(
            "fifo-window",
            "--cross-toolchain",
            "hosted",
            payload,
            payload,
            "fifo-window",
        ),
        "post-selection regular-to-FIFO tuple substitution",
    )
    require_clean_success(
        run_case("exact", "--exact", "", payload, "profile\tlegacy\n"),
        "exact route skips cross reprobe",
    )
    require_closed_failure(
        run_case(
            "tuple-drift",
            "--cross-toolchain",
            "hosted",
            payload,
            "profile\thosted\nformat_sha256\tdrift\n",
        ),
        "producer tuple changed during the build",
        "same-profile tuple drift",
    )
    require_closed_failure(
        run_case(
            "profile-drift",
            "--cross-toolchain",
            "hosted",
            payload,
            "profile\tlegacy\nformat_sha256\tstable\n",
        ),
        "producer tuple changed during the build",
        "before/after profile drift",
    )
    require_closed_failure(
        run_case(
            "double-swap",
            "--cross-toolchain",
            "hosted",
            payload,
            "profile\thosted\nformat_sha256\tdrift\n",
            "double-swap",
        ),
        "producer tuple changed during the build",
        "both-leaf substitution after distinct held reads",
    )
    return 6


def exercise_relation_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "relation.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'MODE="$1"\nCROSS_PROFILE="$2"\nTRACE="$3"\n'
        "HOSTED_PROFILE_ID=hosted\nLEGACY_PROFILE_ID=legacy\n"
        "CHECK_NAME=fixture\nCOMMITTED=/fixture/committed.pdf\nBUILT=/fixture/built.pdf\n"
        'validate_pdf() { printf "%s\\t%s\\t%s\\n" "$1" "$2" "$3" >>"$TRACE"; }\n'
        + fragment
        + "\n",
        encoding="utf-8",
    )
    expected = {
        (
            "--exact",
            "",
        ): "committed\t/fixture/committed.pdf\tstrict\nbuilt\t/fixture/built.pdf\tstrict\n",
        ("--cross-toolchain", "hosted"): (
            "committed\t/fixture/committed.pdf\tstrict\n"
            "built\t/fixture/built.pdf\thosted-raw-and-strict\n"
        ),
        ("--cross-toolchain", "legacy"): (
            "committed\t/fixture/committed.pdf\tstrict\n"
            "built\t/fixture/built.pdf\tlegacy-typed-font-alpha-from-committed\n"
        ),
    }
    controls = 0
    for index, ((mode, profile), expected_trace) in enumerate(expected.items()):
        trace = root / f"relation-{index}.trace"
        trace.write_text("", encoding="utf-8")
        result = run_bash(harness, mode, profile, str(trace))
        require_clean_success(result, f"{mode}/{profile or 'empty'} relation")
        if trace.read_text(encoding="utf-8") != expected_trace:
            raise WiringError(f"{mode}/{profile or 'empty'} relation trace changed")
        controls += 1
    for profile in ("", "unknown", "hosted legacy"):
        trace = root / ("relation-hostile-" + (profile or "empty"))
        trace.write_text("", encoding="utf-8")
        require_closed_failure(
            run_bash(harness, "--cross-toolchain", profile, str(trace)),
            "mode/profile dispatch is empty, unknown, or inconsistent",
            f"relation profile {profile!r}",
        )
        controls += 1
    return controls


def read_null_vector(path: pathlib.Path) -> list[str]:
    data = path.read_bytes()
    if not data.endswith(b"\0"):
        raise WiringError(f"command trace is not NUL terminated: {path}")
    return [item.decode("utf-8") for item in data[:-1].split(b"\0")]


def exercise_command_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "commands.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'structure_relation="$1"\nNORMAL_TRACE="$2"\nOPTIMIZED_TRACE="$3"\n'
        "CHECK_NAME=fixture\nSTRUCTURE_CHECK=/fixture/strict.py\n"
        "HOSTED_RAW_CHECK=/fixture/hosted.py\n"
        "RETAINED_HOSTED_RAW_FIXTURE=/fixture/hosted.pdf\n"
        "FONT_ALPHA_CHECK=/fixture/alpha.py\n"
        "RETAINED_FONT_ALPHA_FIXTURE=/fixture/legacy.pdf\n"
        "COMMITTED=/fixture/committed.pdf\npdf=/fixture/built.pdf\n"
        "observed_urls=/out/normal.urls\nobserved_navigation=/out/normal.nav\n"
        "optimized_urls=/out/optimized.urls\noptimized_navigation=/out/optimized.nav\n"
        "dispatch() {\n  local -a structure_command optimized_structure_command\n"
        + fragment
        + '\n  printf \'%s\\0\' "${structure_command[@]}" >"$NORMAL_TRACE"\n'
        + '  printf \'%s\\0\' "${optimized_structure_command[@]}" >"$OPTIMIZED_TRACE"\n}\n'
        + "dispatch\n",
        encoding="utf-8",
    )
    expected = {
        "strict": ("/fixture/strict.py", ["/fixture/built.pdf"]),
        "hosted-raw-and-strict": (
            "/fixture/hosted.py",
            ["/fixture/hosted.pdf", "/fixture/built.pdf"],
        ),
        "legacy-typed-font-alpha-from-committed": (
            "/fixture/alpha.py",
            ["/fixture/committed.pdf", "/fixture/built.pdf", "/fixture/legacy.pdf"],
        ),
    }
    controls = 0
    for relation, (checker, arguments) in expected.items():
        normal = root / f"{relation}.normal"
        optimized = root / f"{relation}.optimized"
        result = run_bash(harness, relation, str(normal), str(optimized))
        require_clean_success(result, f"{relation} command")
        expected_normal = [
            "python3",
            "-I",
            "-B",
            checker,
            *arguments,
            "/out/normal.urls",
            "/out/normal.nav",
        ]
        expected_optimized = [
            "python3",
            "-O",
            "-I",
            "-B",
            checker,
            *arguments,
            "/out/optimized.urls",
            "/out/optimized.nav",
        ]
        if read_null_vector(normal) != expected_normal:
            raise WiringError(f"{relation} normal command vector changed")
        if read_null_vector(optimized) != expected_optimized:
            raise WiringError(f"{relation} optimized command vector changed")
        controls += 1
    unknown = run_bash(
        harness,
        "unknown",
        str(root / "unknown.normal"),
        str(root / "unknown.optimized"),
    )
    require_closed_failure(
        unknown, "internal unknown structure relation", "unknown relation"
    )
    return controls + 1


def exercise_artifact_dispatch(root: pathlib.Path, fragment: str) -> int:
    harness = root / "artifact.sh"
    harness.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\nMODE=--exact\n"
        'BUILT="$1"\nCOMMITTED="$2"\nCHECK_NAME=fixture\n' + fragment + "\n",
        encoding="utf-8",
    )
    committed = root / "committed.pdf"
    equal = root / "equal.pdf"
    different = root / "different.pdf"
    committed.write_bytes(b"exact\n")
    equal.write_bytes(committed.read_bytes())
    different.write_bytes(b"different\n")
    require_clean_success(
        run_bash(harness, str(equal), str(committed)), "raw-equal exact"
    )
    require_closed_failure(
        run_bash(harness, str(different), str(committed)),
        "committed PDF is stale or not same-toolchain reproducible",
        "raw-different exact",
    )
    return 2


def expect_mutation_rejected(source: str, old: str, new: str, label: str) -> None:
    if source.count(old) != 1:
        raise WiringError(f"mutation anchor is not unique for {label}")
    try:
        audit_wrapper(source.replace(old, new, 1), enforce_wrapper_digest=False)
    except WiringError:
        return
    raise WiringError(f"hostile wrapper mutation passed: {label}")


def run_mutation_suite(source: str) -> int:
    mutations = (
        (
            'if (( $# > 1 )) || [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then',
            'if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then',
            "trailing public arguments accepted",
        ),
        (
            'if (( $# > 1 )) || [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then',
            'if [[ "$MODE" != "--exact" ]]; then',
            "widened public mode",
        ),
        (
            "HOSTED_PANDOC_SHA256=867c5fc83e6b18991d1880e040867d31d09a0d5e68b0bfae362d2fbc71cf25ce",
            "HOSTED_PANDOC_SHA256=" + "0" * 64,
            "hosted writer drift",
        ),
        (
            "HOSTED_RENDERER_SHA256=cc74da0d993e503321f9dd65b8cc5ddf103f2620c4bdbc41798841f253c46e02",
            "HOSTED_RENDERER_SHA256=" + "0" * 64,
            "hosted renderer digest zeroed",
        ),
        (
            "STRUCTURE_CHECK_SHA256=a70d3c78da7040774c5976f2316480501713eed1e9c865822e3024724a0ccf8d",
            "STRUCTURE_CHECK_SHA256=" + "0" * 64,
            "structure checker digest zeroed",
        ),
        (
            "STRUCTURE_SELF_TEST_SHA256=aa8fd64c627884d64b18c2e8cb2565c06678f2c5f55be182723541d026c56229",
            "STRUCTURE_SELF_TEST_SHA256=" + "0" * 64,
            "structure checker self-test digest zeroed",
        ),
        (
            "ID_VARIANCE_CHECK_SHA256=d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
            "ID_VARIANCE_CHECK_SHA256=" + "0" * 64,
            "trailer-ID checker digest zeroed",
        ),
        (
            "HOSTED_RAW_CHECK_SHA256=29837b202ad3e5afa59e10f0ef4848b876fb6ef2b6aa3a996f78d7aac2752fcc",
            "HOSTED_RAW_CHECK_SHA256=" + "0" * 64,
            "hosted checker digest zeroed",
        ),
        (
            "HOSTED_RAW_SELF_TEST_SHA256=f24a3a3013ccf4f5964f947f26798ad00a01f47b7453a75ce9e29946d28f89f9",
            "HOSTED_RAW_SELF_TEST_SHA256=" + "0" * 64,
            "hosted self-test digest zeroed",
        ),
        (
            "HOSTED_RAW_PROFILE_RECEIPT_SHA256=56e599a1f879418c8d2cce85f61b0a51cb1210f915462ff4aa6f0af8b2334be8",
            "HOSTED_RAW_PROFILE_RECEIPT_SHA256=" + "0" * 64,
            "hosted provenance receipt digest zeroed",
        ),
        (
            "FONT_ALPHA_CHECK_SHA256=5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997",
            "FONT_ALPHA_CHECK_SHA256=" + "0" * 64,
            "font-alpha checker digest zeroed",
        ),
        (
            "FONT_ALPHA_SELF_TEST_SHA256=07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be",
            "FONT_ALPHA_SELF_TEST_SHA256=" + "0" * 64,
            "font-alpha self-test digest zeroed",
        ),
        (
            "PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256=5e59e9fb997098656039db1a60c1e8694a451432618ac2ecd192b402e7a8c319",
            "PANDOC_PORTABILITY_RECEIPT_CHECK_SHA256=" + "0" * 64,
            "legacy portability checker digest zeroed",
        ),
        (
            "PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256=bdb53c0b8a20e48df73b22aeeabc223855c2ce797444808e6de495baf6ab2473",
            "PANDOC_PORTABILITY_RECEIPT_SELF_TEST_SHA256=" + "0" * 64,
            "legacy portability self-test digest zeroed",
        ),
        (
            "LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256=7ea2acf89c8a33f5666ab9798a594c24febdad609bd1b5e650b87d8a98ca4581",
            "LEGACY_PANDOC_PORTABILITY_RECEIPT_SHA256=" + "0" * 64,
            "legacy portability receipt digest zeroed",
        ),
        (
            "TRAILER_ID_OBSERVATION_CHECK_SHA256=e531d58620ff41275b741666a119a1245d5ec2a08fa943fc12a297d56317106f",
            "TRAILER_ID_OBSERVATION_CHECK_SHA256=" + "0" * 64,
            "legacy trailer checker digest zeroed",
        ),
        (
            "TRAILER_ID_OBSERVATION_SELF_TEST_SHA256=9b1d0da3dffc87e9d46a4986b9c54c457c036ff0cd0a0966f08155aad7b5b65b",
            "TRAILER_ID_OBSERVATION_SELF_TEST_SHA256=" + "0" * 64,
            "legacy trailer self-test digest zeroed",
        ),
        (
            "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256=cd5602bb28dce0780c4bac5f70097e496d2afe9141a8210f249332b5e6d93596",
            "LEGACY_TRAILER_ID_OBSERVATION_RECEIPT_SHA256=" + "0" * 64,
            "legacy trailer receipt digest zeroed",
        ),
        (
            "HOSTED_FORMAT_PATH=/var/lib/texmf/web2c/luahbtex/lualatex.fmt\n\n"
            "LEGACY_PROFILE_ID=legacy-pandoc-3.1.3-ubuntu-24.04-font-alpha",
            "HOSTED_FORMAT_PATH=/var/lib/texmf/web2c/luahbtex/lualatex.fmt\n"
            + "HOSTED_FORMAT_SHA256="
            + "0" * 64
            + "\n\nLEGACY_PROFILE_ID=legacy-pandoc-3.1.3-ubuntu-24.04-font-alpha",
            "fixed current format selector reintroduced",
        ),
        (
            "LEGACY_FORMAT_BYTES=''",
            "LEGACY_FORMAT_BYTES=12231787",
            "unsupported legacy format promoted",
        ),
        (
            'RETAINED_HOSTED_RAW_FIXTURE="$ROOT/audit/evidence/'
            + HOSTED_FIXTURE_BASENAME
            + '"',
            'RETAINED_HOSTED_RAW_FIXTURE="$ROOT/audit/evidence/'
            + LEGACY_FIXTURE_BASENAME
            + '"',
            "cross-profile hosted fixture",
        ),
        (
            'RETAINED_FONT_ALPHA_FIXTURE="$ROOT/audit/evidence/'
            + LEGACY_FIXTURE_BASENAME
            + '"',
            'RETAINED_FONT_ALPHA_FIXTURE="$ROOT/audit/evidence/'
            + HOSTED_FIXTURE_BASENAME
            + '"',
            "cross-profile legacy fixture",
        ),
        (
            '    "$STRUCTURE_CHECK" "$STRUCTURE_SELF_TEST" \\\n'
            '    "$MODE_WIRING_SELF_TEST" \\',
            '    "$STRUCTURE_CHECK" "$STRUCTURE_SELF_TEST" \\\n'
            '    "$HOSTED_RAW_CHECK" "$MODE_WIRING_SELF_TEST" \\',
            "exact availability made dependent on hosted checker",
        ),
        (
            'if [[ ! -f "$profile_path" || -L "$profile_path" ]]; then',
            "if false; then",
            "selected profile input guard made dead",
        ),
        (
            "select_cross_profile_from_tuple() {",
            "tuple_has() { return 0; }\n\nselect_cross_profile_from_tuple() {",
            "unconditional tuple_has helper reintroduced",
        ),
        (
            "def digest_stable_gate(path):\n",
            "def digest_stable_gate(path):\n    os.O_NONBLOCK = 0\n",
            "stable gate nonblocking custody bypassed",
        ),
        (
            'return os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)',
            'return os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)',
            "producer snapshot nonblocking custody removed",
        ),
        (
            "def read_stable_tuple(tuple_path):\n",
            "def read_stable_tuple(tuple_path):\n    os.O_NONBLOCK = 0\n",
            "tuple reader nonblocking custody bypassed",
        ),
        (
            "os.killpg(process.pid, signal.SIGKILL)",
            "process.kill()",
            "probe process-group termination removed",
        ),
        (
            "if len(buffers[stream_name]) > maximum:",
            "if False:",
            "probe output bound bypassed",
        ),
        (
            "deadline = time.monotonic() + timeout_seconds",
            "deadline = time.monotonic() + 1000000000",
            "probe time bound bypassed",
        ),
        (
            "if format_path != expected_format_path:",
            "if False and format_path != expected_format_path:",
            "format path relation made dead",
        ),
        (
            "or stat.S_ISLNK(path_before.st_mode)\n"
            "            or not stat.S_ISREG(opened.st_mode)\n"
            "            or opened.st_nlink != 1\n"
            "            or opened.st_size <= 0\n"
            "            or opened.st_size > 16384",
            "or stat.S_ISLNK(path_before.st_mode)\n"
            "            or not stat.S_ISREG(opened.st_mode)\n"
            "            or False\n"
            "            or opened.st_size <= 0\n"
            "            or opened.st_size > 16384",
            "tuple link guard made dead",
        ),
        (
            "format_mode & (stat.S_IWGRP | stat.S_IWOTH)",
            "False and format_mode & (stat.S_IWGRP | stat.S_IWOTH)",
            "format permission guard made dead",
        ),
        (
            "if not published and created_stat is not None:",
            "if not published:",
            "tuple rollback ownership guard weakened",
        ),
        (
            "if same_object(created_stat, rollback_stat):",
            "if True:",
            "tuple rollback replacement guard bypassed",
        ),
        (
            'reject(f"tuple matched {len(matches)} supported profiles")',
            'print(hosted["profile"]); raise SystemExit(0)',
            "selector unknown fallback",
        ),
        (
            'CROSS_SELECTION="$(select_cross_profile_from_tuple "$PRODUCER_TUPLE_BEFORE")"',
            'CROSS_SELECTION="$(select_cross_profile_from_tuple "$BUILT")"',
            "candidate-based selection",
        ),
        (
            "CROSS_PROFILE=''\nPRODUCER_TUPLE_BEFORE=",
            'CROSS_PROFILE="${PID_RS_CROSS_PROFILE:-}"\nPRODUCER_TUPLE_BEFORE=',
            "profile environment override",
        ),
        (
            'python3 -I -B "$HOSTED_RAW_SELF_TEST" "$RETAINED_HOSTED_RAW_FIXTURE"',
            'python3 -I -B "$FONT_ALPHA_SELF_TEST" "$RETAINED_HOSTED_RAW_FIXTURE"',
            "current alpha self-test",
        ),
        (
            'python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted',
            'python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy',
            "hosted source audit routed to legacy",
        ),
        (
            'python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy',
            'python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source hosted',
            "legacy source audit routed to hosted",
        ),
        (
            'python3 -I -B "$FONT_ALPHA_SELF_TEST" "$COMMITTED"',
            'python3 -I -B "$HOSTED_RAW_SELF_TEST" "$COMMITTED"',
            "legacy alpha self-test bypass",
        ),
        (
            'CROSS_SELECTION_AFTER="$(select_cross_profile_from_tuple "$PRODUCER_TUPLE_AFTER")"',
            'CROSS_SELECTION_AFTER="$CROSS_SELECTION"',
            "post-build reselection removed",
        ),
        (
            '|| "$CROSS_TUPLE_BASE64_AFTER" != "$CROSS_TUPLE_BASE64" \\\n',
            "|| false \\\n",
            "pre/post held-byte comparison removed",
        ),
        (
            'if [[ "$observed" != "$expected" ]]; then',
            'if false && [[ "$observed" != "$expected" ]]; then',
            "gate digest comparison made dead",
        ),
        (
            'validate_pdf built "$BUILT" strict',
            'validate_pdf built "$BUILT" hosted-raw-and-strict',
            "exact cross invocation",
        ),
        (
            'validate_pdf built "$BUILT" hosted-raw-and-strict',
            'validate_pdf built "$BUILT" legacy-typed-font-alpha-from-committed',
            "cross-profile current candidate route",
        ),
        (
            'validate_pdf built "$BUILT" legacy-typed-font-alpha-from-committed',
            'validate_pdf built "$BUILT" hosted-raw-and-strict',
            "cross-profile legacy candidate route",
        ),
        (
            'structure_command=(python3 -I -B "$HOSTED_RAW_CHECK"',
            'structure_command=(python3 -I -B "$FONT_ALPHA_CHECK"',
            "current alpha call",
        ),
        (
            'structure_command=(python3 -I -B "$FONT_ALPHA_CHECK" "$COMMITTED" "$pdf"',
            'structure_command=(python3 -I -B "$HOSTED_RAW_CHECK" "$COMMITTED" "$pdf"',
            "legacy alpha bypass",
        ),
        (
            'if [[ "$MODE" == "--exact" ]]; then\n  cmp -s "$BUILT" "$COMMITTED" || {',
            'if [[ "$MODE" == "--exact" ]]; then\n'
            '  python3 -I -B "$HOSTED_RAW_CHECK" "$COMMITTED" "$BUILT"\n'
            '  cmp -s "$BUILT" "$COMMITTED" || {',
            "out-of-band exact hosted checker call",
        ),
        (
            'if [[ "$MODE" == "--exact" ]]; then\n  cmp -s "$BUILT" "$COMMITTED" || {',
            'if [[ "$MODE" == "--exact" ]]; then\n'
            '  python3 -I -B "$MODE_WIRING_SELF_TEST" --selected-profile-source legacy\n'
            '  cmp -s "$BUILT" "$COMMITTED" || {',
            "out-of-band exact selected legacy source audit",
        ),
        (
            'PAGES="$(awk \'/^Pages:/ {print $2}\' "$BUILD_ROOT/committed.info")"',
            'PAGES="$(awk \'/^Pages:/ {print $2}\' "$BUILD_ROOT/committed.info")"\n'
            'python3 -I -B "$PANDOC_PORTABILITY_RECEIPT_CHECK"',
            "out-of-band legacy checker invocation",
        ),
        (
            'PAGES="$(awk \'/^Pages:/ {print $2}\' "$BUILD_ROOT/committed.info")"',
            'PAGES="$(awk \'/^Pages:/ {print $2}\' "$BUILD_ROOT/committed.info")"\n'
            'checker_alias=$HOSTED_RAW_CHECK\npython3 "$checker_alias" "$COMMITTED"',
            "unquoted out-of-band checker alias",
        ),
        (
            'PAGES="$(awk \'/^Pages:/ {print $2}\' "$BUILD_ROOT/committed.info")"',
            'PAGES="$(awk \'/^Pages:/ {print $2}\' "$BUILD_ROOT/committed.info")"\n'
            'python3 "$ROOT/scripts/' + HOSTED_BASENAME + '" "$COMMITTED"',
            "literal out-of-band checker path",
        ),
        (
            'cmp -s "$BUILT" "$COMMITTED" || {',
            "true || {",
            "raw exact comparison removed",
        ),
    )
    for old, new, label in mutations:
        expect_mutation_rejected(source, old, new, label)
    return len(mutations)


def main() -> int:
    try:
        wrapper = read_direct(WRAPPER, "guide PDF wrapper")
        guide_builder = read_direct(GUIDE_BUILDER, "guide PDF builder")
        sxpid3_wrapper = read_direct(SXPID3_WRAPPER, "SxPID3 PDF wrapper")
        sxpid3_builder = read_direct(SXPID3_BUILDER, "SxPID3 PDF builder")
        for path in (WRAPPER, GUIDE_BUILDER, SXPID3_WRAPPER, SXPID3_BUILDER):
            syntax = subprocess.run(
                ["bash", "--noprofile", "--norc", "-n", str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if syntax.returncode != 0 or syntax.stdout or syntax.stderr:
                raise WiringError(
                    f"shell syntax check failed for {path}: {syntax.stdout}{syntax.stderr}"
                )
        audit_auxiliary_sources(guide_builder, sxpid3_wrapper, sxpid3_builder)
        fragments = audit_wrapper(wrapper)
        hostile_count = run_mutation_suite(wrapper)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-guide-mode-wiring-self-test."
        ) as raw:
            temporary_root = pathlib.Path(raw).resolve(strict=True)
            controls = 4
            controls += exercise_mode_guard(temporary_root, fragments.mode_guard)
            controls += exercise_capture_custody_hostiles(
                temporary_root,
                fragments.digest_function,
                fragments.capture_function,
                fragments.selector_function,
            )
            controls += exercise_capture_function(
                temporary_root, fragments.capture_function
            )
            controls += exercise_profile_selector(
                temporary_root, fragments.selector_function
            )
            controls += exercise_prebuild_dispatch(
                temporary_root, fragments.prebuild_dispatch
            )
            controls += exercise_postbuild_guard(
                temporary_root, fragments.postbuild_guard
            )
            controls += exercise_relation_dispatch(
                temporary_root, fragments.relation_dispatch
            )
            controls += exercise_command_dispatch(
                temporary_root, fragments.command_dispatch
            )
            controls += exercise_artifact_dispatch(
                temporary_root, fragments.artifact_dispatch
            )
    except (OSError, UnicodeError, WiringError) as error:
        fail(str(error))
    print(
        "OK: guide PDF producer-profile mode wiring "
        f"(controls={controls}; hostile_mutations={hostile_count}; "
        "exact_cross_checker_invocations=0; current_alpha_invocations=0; "
        "legacy_hosted_checker_invocations=0)"
    )
    print(
        "Boundary: source-extracted producer capture, selection, and dispatch; "
        "current v2 hosted admission is raw-fixture bound, while frozen v1 routes remain "
        "historical and exact mode invokes no cross-profile relation."
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise SystemExit(main())
    if (
        len(sys.argv) == 3
        and sys.argv[1] == "--selected-profile-source"
        and sys.argv[2] in ("hosted", "legacy")
    ):
        try:
            raise SystemExit(audit_selected_profile_source(sys.argv[2]))
        except (OSError, UnicodeError, WiringError) as error:
            fail(str(error))
    print(
        "usage: check-mathematical-results-guide-pdf-mode-wiring-self-test.py "
        "[--selected-profile-source {hosted,legacy}]",
        file=sys.stderr,
    )
    raise SystemExit(2)
