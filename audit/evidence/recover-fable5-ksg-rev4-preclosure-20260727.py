#!/usr/bin/env python3
"""Offline, hash-gated recovery of the KSG revision-4 Fable preclosure record.

This script reads only:
* local Git objects,
* the preserved candidate tree, and
* Codex JSONL session transcripts.

It never reads `.env`, never performs network I/O, and never writes either repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any


EXPECTED_CONTEXT = (
    662_079,
    "21a08acd99bfc5c5881a6d267382bc808075fb69bca9ae6f76b103775c5f3ee3",
)
EXPECTED_RECEIPT = (
    7_831,
    "cfdf84ba5ca1e51c215b7785d577c7378e4836d213de12230caf5449f33e010b",
)
EXPECTED_RESPONSE = (
    15_681,
    "b4cac94ca6b636d8f5433bc3e2112f5cee7c118aa60cff9a321ea1fdcaf7dd9a",
)
LAUNCH_HEAD = "118e1de6a2d6d2ae33fe7bdc224736257e42a83f"

ROOT_SESSION = (
    ".codex/sessions/2026/07/26/"
    "rollout-2026-07-26T16-16-50-019f9ec9-2763-7ae3-9532-2169a23307f0.jsonl"
)
CLAIM_SESSION = (
    ".codex/sessions/2026/07/26/"
    "rollout-2026-07-26T17-27-05-019f9f09-773a-7110-825c-d16e46a5795f.jsonl"
)
REVIEW_SESSION = (
    ".codex/sessions/2026/07/26/"
    "rollout-2026-07-26T18-00-16-019f9f27-d679-7bb0-be02-edb4e0359489.jsonl"
)
SOURCE_SESSION = (
    ".codex/sessions/2026/07/26/"
    "rollout-2026-07-26T16-51-19-019f9ee8-b76c-7060-96b6-ab30ff419d21.jsonl"
)
BLOCKER_SESSION = (
    ".codex/sessions/2026/07/26/"
    "rollout-2026-07-26T17-30-59-019f9f0d-0a85-7ea3-9e1b-bb570a03b394.jsonl"
)

PACKET_CALL = "call_usYAgL2kNrB6xfB79VJ01aq8"
CHECKER_CALLS = (
    "call_css9ovipcyeu1aXwJ7drotYP",
    "call_vBdv4JX2aLGF3L6npf1cFH31",
    "call_rBziJ06Qxzb6xBqaHwnuh8VP",
    "call_yPcDxUNXP9ic4uFWiiwsMT7E",
)
SELF_TEST_CALLS = (
    "call_svvHVpZCviheHkBDSxMdWB6Y",
    "call_AqkzQ0uLQUFUTyfNMNPdqBXC",
    "call_1LjQDobfOMOhtNNtvhwKg1mX",
)
ROOT_OUTPUT_CALL = "call_NkQxenVL9Wcqn0mF7rjcgVfg"

SOURCE_PATCH_TIMESTAMPS = (
    "2026-07-26T14:55:58.433Z",
    "2026-07-26T14:56:20.421Z",
    "2026-07-26T14:57:36.137Z",
)
BLOCKER_PATCH_TIMESTAMPS = (
    "2026-07-26T15:32:19.700Z",
    "2026-07-26T15:41:36.777Z",
)
CLAIM_ADD_TIMESTAMP = "2026-07-26T15:41:29.734Z"
RUNNER_ADD_TIMESTAMP = "2026-07-26T16:04:53.362Z"
STATS_BASE = "e96122b56c15e895c081379210103d1a26eac25f"

V4_PROSE_NAMES = {
    "claim-v4.md",
    "behavioral-witnesses-v4.md",
    "correction-ledger-v4.md",
    "implementation-v4.md",
    "integration-disposition-v4.md",
    "obligations-v4.md",
    "routes-v4.md",
}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_events(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"{path}:{line_number}: invalid JSONL") from error
            if not isinstance(value, dict):
                raise RuntimeError(f"{path}:{line_number}: event is not an object")
            result.append(value)
    return result


def apply_unified_diff(text: str, diff: str) -> str:
    """Apply one recorded update diff with exact-content fallback matching."""
    source = text.splitlines(keepends=True)
    if "".join(source) != text:
        raise RuntimeError("line splitting did not preserve input")
    output: list[str] = []
    source_position = 0
    lines = diff.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        if not lines[index].startswith("@@ "):
            index += 1
            continue
        match = re.match(
            r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",
            lines[index],
        )
        if match is None:
            raise RuntimeError(f"invalid hunk header: {lines[index]!r}")
        hint = int(match.group(1)) - 1
        index += 1
        hunk: list[str] = []
        while index < len(lines) and not lines[index].startswith("@@ "):
            line = lines[index]
            if line.startswith((" ", "+", "-")):
                hunk.append(line)
                index += 1
            elif line.startswith("\\ No newline"):
                index += 1
            else:
                break
        old = [line[1:] for line in hunk if line[0] in " -"]
        new = [line[1:] for line in hunk if line[0] in " +"]
        location = hint
        if source[location : location + len(old)] != old:
            matches = [
                candidate
                for candidate in range(
                    source_position,
                    len(source) - len(old) + 1,
                )
                if source[candidate : candidate + len(old)] == old
            ]
            if len(matches) != 1:
                raise RuntimeError(
                    f"hunk has {len(matches)} exact matches; expected one"
                )
            location = matches[0]
        if location < source_position:
            raise RuntimeError("hunks are not in source order")
        output.extend(source[source_position:location])
        output.extend(new)
        source_position = location + len(old)
    output.extend(source[source_position:])
    return "".join(output)


def payload_for_call(
    events: list[dict[str, Any]],
    call_id: str,
    payload_type: str,
) -> dict[str, Any]:
    matches = [
        event["payload"]
        for event in events
        if isinstance(event.get("payload"), dict)
        and event["payload"].get("type") == payload_type
        and event["payload"].get("call_id") == call_id
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"{call_id}/{payload_type}: found {len(matches)} payloads"
        )
    return matches[0]


def exact_output_body(events: list[dict[str, Any]], call_id: str) -> str:
    payload = payload_for_call(events, call_id, "function_call_output")
    raw = payload.get("output")
    if not isinstance(raw, str):
        raise RuntimeError(f"{call_id}: output is not text")
    if "Warning: truncated output" in raw:
        raise RuntimeError(f"{call_id}: output was truncated")
    marker = "\nOutput:\n"
    if raw.count(marker) != 1:
        raise RuntimeError(f"{call_id}: unexpected output wrapper")
    return raw.split(marker, 1)[1]


def patch_event_at(
    events: list[dict[str, Any]],
    timestamp: str,
) -> dict[str, Any]:
    matches = [
        event["payload"]
        for event in events
        if event.get("timestamp") == timestamp
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("type") == "patch_apply_end"
        and event["payload"].get("success") is True
    ]
    if len(matches) != 1:
        raise RuntimeError(f"{timestamp}: found {len(matches)} patch events")
    return matches[0]


def write_private(path: Path, value: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def verify_expected(
    label: str,
    value: bytes,
    expected: tuple[int, str],
) -> None:
    actual = (len(value), sha256(value))
    if actual != expected:
        raise RuntimeError(f"{label}: {actual!r} != {expected!r}")


def scan_for_secrets(label: str, value: bytes) -> None:
    text = value.decode("utf-8")
    literal_markers = (
        "sk-ant-",
        "sk-proj-",
        "x-api-key:",
    )
    for marker in literal_markers:
        if marker.casefold() in text.casefold():
            raise RuntimeError(f"{label}: secret-like marker {marker!r}")
    assignment = re.compile(
        r"""(?ix)
        \b(?:ANTHROPIC_API_KEY|OPENAI_API_KEY|api[_-]?key)\b
        \s*[:=]\s*
        ["']?[A-Za-z0-9_./+=-]{20,}
        """
    )
    if assignment.search(text):
        raise RuntimeError(f"{label}: secret-like key assignment")


def recover(args: argparse.Namespace) -> dict[str, Any]:
    home = args.home.resolve()
    repo = args.repo.resolve()
    candidate = args.candidate.resolve()
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    os.umask(0o077)

    root_events = read_events(home / ROOT_SESSION)
    claim_events = read_events(home / CLAIM_SESSION)
    review_events = read_events(home / REVIEW_SESSION)
    source_events = read_events(home / SOURCE_SESSION)
    blocker_events = read_events(home / BLOCKER_SESSION)

    runner_add = patch_event_at(root_events, RUNNER_ADD_TIMESTAMP)
    runner_contents = [
        change["content"]
        for path, change in runner_add["changes"].items()
        if "fable5-ksg-rev4-preclosure-runner" in path
        and change.get("type") == "add"
    ]
    if len(runner_contents) != 1 or not isinstance(runner_contents[0], str):
        raise RuntimeError("could not resolve exact runner Add content")
    artifacts = re.findall(
        r'\["([^"]+)",\s*"([0-9a-f]{64})"\]',
        runner_contents[0],
    )
    if len(artifacts) != 31:
        raise RuntimeError(f"runner artifact count is {len(artifacts)}, not 31")
    if len({relative for relative, _ in artifacts}) != len(artifacts):
        raise RuntimeError("runner artifact paths are not unique")

    artifact_bytes: dict[str, bytes] = {}
    for relative, _ in artifacts:
        source = candidate / relative
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f"unsafe or absent candidate artifact: {source}")
        artifact_bytes[relative] = source.read_bytes()

    claim_add = patch_event_at(claim_events, CLAIM_ADD_TIMESTAMP)
    for absolute, change in claim_add["changes"].items():
        relative = absolute.split("/tree/", 1)[-1]
        if (
            relative in artifact_bytes
            and change.get("type") == "add"
            and Path(relative).name in V4_PROSE_NAMES
        ):
            content = change.get("content")
            if not isinstance(content, str):
                raise RuntimeError(f"{relative}: Add content is not text")
            artifact_bytes[relative] = content.encode("utf-8")

    for event in claim_events:
        payload = event.get("payload")
        if (
            event.get("timestamp", "") <= CLAIM_ADD_TIMESTAMP
            or not isinstance(payload, dict)
            or payload.get("type") != "patch_apply_end"
            or payload.get("success") is not True
        ):
            continue
        for absolute, change in payload.get("changes", {}).items():
            relative = absolute.split("/tree/", 1)[-1]
            if (
                relative in artifact_bytes
                and Path(relative).name in V4_PROSE_NAMES
                and change.get("type") == "update"
            ):
                artifact_bytes[relative] = apply_unified_diff(
                    artifact_bytes[relative].decode("utf-8"),
                    change["unified_diff"],
                ).encode("utf-8")

    artifact_bytes[
        "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
    ] = exact_output_body(review_events, PACKET_CALL).encode("utf-8")
    artifact_bytes["scripts/check-ksg-harmonic-revision.py"] = "".join(
        exact_output_body(review_events, call_id)
        for call_id in CHECKER_CALLS
    ).encode("utf-8")
    artifact_bytes[
        "scripts/check-ksg-harmonic-revision-self-test.py"
    ] = "".join(
        exact_output_body(review_events, call_id)
        for call_id in SELF_TEST_CALLS
    ).encode("utf-8")

    stats_result = subprocess.run(
        [
            "git",
            "show",
            f"{STATS_BASE}:crates/pid-core/src/stats.rs",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    stats = stats_result.stdout
    for timestamp in SOURCE_PATCH_TIMESTAMPS:
        patch = patch_event_at(source_events, timestamp)
        changes = [
            change
            for path, change in patch["changes"].items()
            if path.endswith("/crates/pid-core/src/stats.rs")
        ]
        if len(changes) != 1:
            raise RuntimeError(f"{timestamp}: source stats patch count mismatch")
        stats = apply_unified_diff(stats, changes[0]["unified_diff"])
    with tempfile.TemporaryDirectory(prefix="pid-rs-stats-recovery-") as raw:
        stats_path = Path(raw) / "stats.rs"
        stats_path.write_text(stats, encoding="utf-8")
        subprocess.run(
            ["rustfmt", "--edition", "2021", str(stats_path)],
            check=True,
        )
        stats = stats_path.read_text(encoding="utf-8")
    exact_stats_path = (
        "/private/tmp/pid-rs-ksg-rev4.E11L9g/tree/"
        "crates/pid-core/src/stats.rs"
    )
    for timestamp in BLOCKER_PATCH_TIMESTAMPS:
        patch = patch_event_at(blocker_events, timestamp)
        change = patch["changes"].get(exact_stats_path)
        if not isinstance(change, dict):
            raise RuntimeError(f"{timestamp}: exact blocker stats patch absent")
        stats = apply_unified_diff(stats, change["unified_diff"])
    artifact_bytes["crates/pid-core/src/stats.rs"] = stats.encode("utf-8")

    artifact_manifest: list[dict[str, Any]] = []
    for relative, expected in artifacts:
        value = artifact_bytes[relative]
        actual = sha256(value)
        if actual != expected:
            raise RuntimeError(
                f"{relative}: reconstructed {actual}, expected {expected}"
            )
        text = value.decode("utf-8")
        if text.encode("utf-8") != value:
            raise RuntimeError(f"{relative}: UTF-8 round trip changed bytes")
        artifact_manifest.append(
            {
                "path": relative,
                "bytes": len(value),
                "sha256": actual,
            }
        )

    context_sections = [
        "# Exact retained context for Fable 5 Max KSG revision-4 review\n\n",
        f"HEAD and origin/main at launch: `{LAUNCH_HEAD}`.\n\n",
        (
            "The listed artifacts are exact UTF-8 bytes. "
            "Unlisted repository state is outside this review.\n"
        ),
    ]
    for relative, expected in artifacts:
        text = artifact_bytes[relative].decode("utf-8")
        context_sections.extend(
            (
                f"\n## Artifact: `{relative}`\n\n"
                f"SHA-256: `{expected}`\n\n",
                "```text\n",
                text,
                "" if text.endswith("\n") else "\n",
                "```\n",
            )
        )
    context = "".join(context_sections).encode("utf-8")
    verify_expected("context", context, EXPECTED_CONTEXT)

    root_output = payload_for_call(
        root_events,
        ROOT_OUTPUT_CALL,
        "function_call_output",
    ).get("output")
    if not isinstance(root_output, str):
        raise RuntimeError("root review output is not text")
    if root_output.count("\nOutput:\n") != 1:
        raise RuntimeError("root review output wrapper is ambiguous")
    root_body = root_output.split("\nOutput:\n", 1)[1]
    receipt_start = root_body.index(
        '{\n  "schema": "pid-rs/external-hostile-review-receipt"'
    )
    response_marker = (
        "\n# Hostile review — KSG-INTEGER-HARMONIC-001 "
        "revision 4, preclosure\n"
    )
    response_boundary = root_body.index(response_marker, receipt_start)
    receipt = root_body[receipt_start : response_boundary + 1].encode("utf-8")
    response = root_body[response_boundary + 1 :].encode("utf-8")
    verify_expected("receipt", receipt, EXPECTED_RECEIPT)
    verify_expected("response", response, EXPECTED_RESPONSE)

    for label, value in (
        ("context", context),
        ("receipt", receipt),
        ("response", response),
    ):
        scan_for_secrets(label, value)

    outputs = {
        "context": (
            output / "fable5-ksg-rev4-preclosure-context.md",
            context,
        ),
        "receipt": (
            output / "fable5-ksg-rev4-preclosure-receipt.json",
            receipt,
        ),
        "response": (
            output / "fable5-ksg-rev4-preclosure-response.md",
            response,
        ),
    }
    for _, (path, value) in outputs.items():
        write_private(path, value)

    manifest = {
        "schema": "pid-rs/fable-preclosure-offline-recovery-manifest",
        "schema_revision": 1,
        "network_used": False,
        "env_file_read": False,
        "launch_head": LAUNCH_HEAD,
        "sources": {
            "candidate": str(candidate),
            "git_repository": str(repo),
            "sessions": {
                "root": str(home / ROOT_SESSION),
                "claim_builder": str(home / CLAIM_SESSION),
                "hostile_review": str(home / REVIEW_SESSION),
                "source_builder": str(home / SOURCE_SESSION),
                "source_blocker": str(home / BLOCKER_SESSION),
            },
            "call_ids": {
                "active_packet": PACKET_CALL,
                "revision_checker_chunks": list(CHECKER_CALLS),
                "revision_self_test_chunks": list(SELF_TEST_CALLS),
                "receipt_and_response_root_output": ROOT_OUTPUT_CALL,
            },
            "patch_timestamps": {
                "runner_add": RUNNER_ADD_TIMESTAMP,
                "claim_add": CLAIM_ADD_TIMESTAMP,
                "stats_source": list(SOURCE_PATCH_TIMESTAMPS),
                "stats_blocker": list(BLOCKER_PATCH_TIMESTAMPS),
            },
            "stats_base_commit": STATS_BASE,
            "stats_formatter": "rustfmt --edition 2021",
        },
        "artifacts": artifact_manifest,
        "outputs": {
            label: {
                "path": str(path),
                "bytes": len(value),
                "sha256": sha256(value),
                "mode": "0600",
                "secret_pattern_scan": "passed",
            }
            for label, (path, value) in outputs.items()
        },
    }
    manifest_bytes = (
        json.dumps(
            manifest,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    manifest_path = output / "recovery-manifest.json"
    write_private(manifest_path, manifest_bytes)

    return {
        "directory": str(output),
        "directory_mode": "0700",
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_bytes),
        "outputs": manifest["outputs"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(
            "/Users/torusprime/Development/sepahead-github/pid-rs"
        ),
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path(
            "/Users/torusprime/Development/sepahead-github/"
            "pid-rs-ksg-rev4-candidate"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    result = recover(parse_args())
    print(
        json.dumps(
            result,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
