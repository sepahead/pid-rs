#!/usr/bin/env python3
"""Hostile controls for the no-clobber SxPID3 audit-expression capture command."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import time
import types
from typing import Any


if not (
    sys.implementation.name == "cpython"
    and sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.no_site == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: capture self-test requires CPython 3.11+ with -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_PATH = (
    ROOT
    / "scripts"
    / "capture-sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1.py"
)


class SelfTestError(RuntimeError):
    """A required positive or negative control failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def load_capture() -> Any:
    before = CAPTURE_PATH.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not CAPTURE_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o755
        and 0 < before.st_size <= 4 * 1024 * 1024,
        "capture source metadata rejected",
    )
    descriptor = os.open(
        CAPTURE_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    )
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", "capture source short read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", "capture source grew during read")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = CAPTURE_PATH.lstat()
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "capture source changed during read",
        )
    raw = b"".join(chunks)
    name = "pid_rs_sxpid3_audit_expression_capture_v1"
    module = types.ModuleType(name)
    module.__file__ = os.fspath(CAPTURE_PATH)
    module.__package__ = ""
    sys.modules[name] = module
    exec(
        compile(
            raw,
            os.fspath(CAPTURE_PATH),
            "exec",
            flags=0,
            dont_inherit=True,
            optimize=sys.flags.optimize,
        ),
        module.__dict__,
    )
    return module


def expect_rejected(
    function: Any,
    label: str,
    expected: type[BaseException] | tuple[type[BaseException], ...],
) -> BaseException:
    try:
        function()
    except expected as error:
        return error
    except BaseException as error:
        raise SelfTestError(
            f"hostile control raised the wrong exception for {label}: {type(error).__name__}"
        ) from error
    raise SelfTestError(f"hostile control escaped: {label}")


def subprocess_result(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        env={
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )


def main() -> int:
    capture = load_capture()
    require(
        capture.STATUS_ARGUMENTS
        == [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignore-submodules=all",
            "--no-renames",
        ],
        "exact status subcommand arguments drifted",
    )

    status_controls = 0
    capture.require_status(b"", b"", "positive")
    for observed, expected, label in (
        (b" M tracked\0", b"", "tracked-dirty"),
        (b"?? stray\0", b"", "untracked-dirty"),
        (
            b"?? " + capture.RECEIPT_RELATIVE.encode("utf-8") + b"\0?? extra\0",
            b"?? " + capture.RECEIPT_RELATIVE.encode("utf-8") + b"\0",
            "postwrite-extra-untracked",
        ),
        (
            b" M CHANGELOG.md\0?? "
            + capture.RECEIPT_RELATIVE.encode("utf-8")
            + b"\0",
            b"?? " + capture.RECEIPT_RELATIVE.encode("utf-8") + b"\0",
            "postwrite-tracked-dirty",
        ),
    ):
        expect_rejected(
            lambda observed=observed, expected=expected, label=label: capture.require_status(
                observed, expected, label
            ),
            label,
            capture.ReceiptError,
        )
        status_controls += 1

    original_git_bytes = capture.git_bytes
    original_bootstrap_head_oid = capture.bootstrap_head_oid
    original_require_supported_git_version = capture.require_supported_git_version
    original_require_status_attribute_closure = capture.require_status_attribute_closure
    index_state: dict[str, bytes] = {
        "rows": b"H tracked\0",
        "sparse": b"100644 " + b"0" * 40 + b" 0\ttracked\0",
        "status": b"",
    }

    fake_head = "f" * 40

    def fake_git_bytes(
        arguments: list[str],
        *,
        stdin_bytes: bytes | None = None,
        attribute_source: str | None = None,
        pin_attributes: bool = True,
    ) -> bytes:
        require(stdin_bytes is None, "index-state mock received unexpected stdin")
        require(
            pin_attributes and attribute_source == fake_head,
            "index-state mock was not bound to the exact HEAD OID",
        )
        if arguments[:3] == ["ls-files", "-v", "-z"]:
            return index_state["rows"]
        if arguments == ["ls-files", "--sparse", "--stage", "-z"]:
            return index_state["sparse"]
        if arguments == capture.STATUS_ARGUMENTS:
            return index_state["status"]
        raise SelfTestError("unexpected fake Git invocation")

    capture.git_bytes = fake_git_bytes
    capture.bootstrap_head_oid = lambda: fake_head
    capture.require_supported_git_version = lambda head: require(
        head == fake_head, "version guard received the wrong exact HEAD"
    )
    capture.require_status_attribute_closure = lambda head: require(
        head == fake_head, "attribute guard received the wrong exact HEAD"
    )
    try:
        require(capture.status_bytes() == b"", "ordinary index state was rejected")
        for rows, label in ((b"h tracked\0", "assume-unchanged"), (b"S tracked\0", "skip-worktree")):
            index_state["rows"] = rows
            expect_rejected(capture.status_bytes, label, capture.ReceiptError)
            status_controls += 1
        index_state["rows"] = b"H tracked\0"
        for mode, path, label in (
            (b"040000", b"sparse-directory", "sparse-directory-index-entry"),
            (b"160000", b"nested-repository", "gitlink-index-entry"),
        ):
            index_state["sparse"] = (
                mode + b" " + b"0" * 40 + b" 0\t" + path + b"\0"
            )
            expect_rejected(
                capture.status_bytes,
                label,
                capture.ReceiptError,
            )
            status_controls += 1
        index_state["rows"] = b"H ordinary-link\0"
        index_state["sparse"] = (
            b"120000 " + b"0" * 40 + b" 0\tordinary-link\0"
        )
        require(
            capture.status_bytes() == b"",
            "ordinary stage-0 symlink was incorrectly rejected",
        )
        status_controls += 1
    finally:
        capture.git_bytes = original_git_bytes
        capture.bootstrap_head_oid = original_bootstrap_head_oid
        capture.require_supported_git_version = original_require_supported_git_version
        capture.require_status_attribute_closure = original_require_status_attribute_closure

    git_topology_controls = 0

    def run_temp_git(repository: Path, arguments: list[str]) -> bytes:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            env={
                "GIT_ATTR_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_SYSTEM": os.devnull,
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": os.environ.get("PATH", ""),
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        require(
            completed.returncode == 0 and completed.stderr == b"",
            f"temporary Git fixture command failed: {' '.join(arguments)}",
        )
        return completed.stdout

    def exercise_git_topology_threat(
        label: str, expected_message: str, mutation: Any
    ) -> None:
        nonlocal git_topology_controls
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-sxpid3-git-topology-self-test-"
        ) as raw_repository:
            repository = Path(raw_repository)
            run_temp_git(repository, ["init", "-q"])
            run_temp_git(repository, ["config", "user.name", "P5 fixture"])
            run_temp_git(repository, ["config", "user.email", "p5@example.invalid"])
            (repository / "tracked").write_bytes(b"fixture\n")
            run_temp_git(repository, ["add", "--", "tracked"])
            run_temp_git(repository, ["commit", "-q", "-m", "fixture"])
            original_root = capture.ROOT
            original_base_commit = capture.BASE_COMMIT
            original_base_tree = capture.BASE_TREE
            fixture_head = run_temp_git(repository, ["rev-parse", "HEAD"]).decode(
                "ascii"
            ).strip()
            fixture_tree = run_temp_git(
                repository, ["rev-parse", "HEAD^{tree}"]
            ).decode("ascii").strip()
            capture.ROOT = repository.resolve()
            capture.BASE_COMMIT = fixture_head
            capture.BASE_TREE = fixture_tree
            try:
                capture.canonical_repository()
                mutation(repository)
                error = expect_rejected(
                    capture.canonical_repository,
                    label,
                    capture.ReceiptError,
                )
                require(
                    expected_message in str(error),
                    f"Git topology control rejected for the wrong reason: {label}",
                )
            finally:
                capture.ROOT = original_root
                capture.BASE_COMMIT = original_base_commit
                capture.BASE_TREE = original_base_tree
        git_topology_controls += 1

    def write_graft(repository: Path) -> None:
        head = run_temp_git(repository, ["rev-parse", "HEAD"]).decode("ascii").strip()
        (repository / ".git" / "info" / "grafts").write_text(
            f"{head}\n", encoding="ascii"
        )

    def write_alternate(repository: Path) -> None:
        (repository / ".git" / "objects" / "info" / "alternates").write_text(
            "/nonexistent/object/store\n", encoding="utf-8"
        )

    def write_sparse_state(repository: Path) -> None:
        (repository / ".git" / "info" / "sparse-checkout").write_text(
            "/*\n", encoding="utf-8"
        )

    def write_promisor_pack(repository: Path) -> None:
        (repository / ".git" / "objects" / "pack" / "fixture.promisor").write_bytes(
            b""
        )

    def write_shallow_boundary(repository: Path) -> None:
        head = run_temp_git(repository, ["rev-parse", "HEAD"])
        (repository / ".git" / "shallow").write_bytes(head)

    def configure_partial_clone(repository: Path) -> None:
        run_temp_git(repository, ["config", "extensions.partialClone", "origin"])

    def configure_include(repository: Path) -> None:
        run_temp_git(repository, ["config", "include.path", "/nonexistent/config"])

    def write_replace_ref(repository: Path) -> None:
        head = run_temp_git(repository, ["rev-parse", "HEAD"])
        replacement = repository / ".git" / "refs" / "replace" / head.decode(
            "ascii"
        ).strip()
        replacement.parent.mkdir(parents=True)
        replacement.write_bytes(head)

    def symlink_object_directory(repository: Path, component: str) -> None:
        directory = repository / ".git" / "objects" / component if component else repository / ".git" / "objects"
        moved = directory.with_name(directory.name + "-real")
        directory.rename(moved)
        directory.symlink_to(moved.name, target_is_directory=True)

    for threat_label, threat_message, threat_mutation in (
        ("Git-graft-state", "exact HEAD bootstrap failed closed", write_graft),
        ("Git-object-alternate", "exact HEAD bootstrap failed closed", write_alternate),
        ("Git-sparse-state", "sparse-checkout state", write_sparse_state),
        ("Git-promisor-pack", "promisor object packs", write_promisor_pack),
        ("Git-shallow-state", "shallow Git history", write_shallow_boundary),
        ("Git-partial-clone-config", "partial-clone, promisor, or sparse", configure_partial_clone),
        ("Git-include-config", "partial-clone, promisor, or sparse", configure_include),
        ("Git-replacement-ref", "replacement refs", write_replace_ref),
        ("Git-symlinked-objects-root", "object storage directories", lambda repo: symlink_object_directory(repo, "")),
        ("Git-symlinked-objects-info", "object storage directories", lambda repo: symlink_object_directory(repo, "info")),
        ("Git-symlinked-objects-pack", "object storage directories", lambda repo: symlink_object_directory(repo, "pack")),
    ):
        exercise_git_topology_threat(
            threat_label, threat_message, threat_mutation
        )

    def initialize_attribute_repository(repository: Path) -> None:
        run_temp_git(repository, ["init", "-q"])
        run_temp_git(repository, ["config", "user.name", "P5 attr fixture"])
        run_temp_git(
            repository, ["config", "user.email", "p5-attr@example.invalid"]
        )
        (repository / "tracked").write_bytes(b"baseline\n")
        run_temp_git(repository, ["add", "--", "tracked"])
        run_temp_git(repository, ["commit", "-q", "-m", "base"])

    def exercise_attribute_threat(
        label: str,
        setup: Any,
        expected_fragment: str,
    ) -> None:
        nonlocal git_topology_controls
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-sxpid3-attribute-self-test-"
        ) as raw_repository:
            repository = Path(raw_repository)
            initialize_attribute_repository(repository)
            setup(repository)
            original_root = capture.ROOT
            capture.ROOT = repository.resolve()
            try:
                error = expect_rejected(
                    capture.status_bytes, label, capture.ReceiptError
                )
                require(
                    expected_fragment in str(error),
                    f"attribute control rejected for the wrong reason: {label}",
                )
            finally:
                capture.ROOT = original_root
        git_topology_controls += 1

    def commit_attributes(repository: Path, contents: bytes) -> None:
        (repository / ".gitattributes").write_bytes(contents)
        run_temp_git(repository, ["add", "--", ".gitattributes"])
        run_temp_git(repository, ["commit", "-q", "-m", "attributes"])

    exercise_attribute_threat(
        "exact-HEAD-filter-attribute",
        lambda repository: commit_attributes(
            repository, b"tracked filter=fixture\n"
        ),
        "exact HEAD attributes",
    )
    exercise_attribute_threat(
        "effective-dirty-filter-addition",
        lambda repository: (repository / ".gitattributes").write_bytes(
            b"tracked filter=fixture\n"
        ),
        "effective worktree/index attributes",
    )

    def remove_committed_filter(repository: Path) -> None:
        commit_attributes(repository, b"tracked filter=fixture\n")
        (repository / ".gitattributes").write_bytes(b"tracked text\n")

    exercise_attribute_threat(
        "dirty-removal-cannot-hide-HEAD-filter",
        remove_committed_filter,
        "exact HEAD attributes",
    )
    exercise_attribute_threat(
        "literal-unspecified-driver-name",
        lambda repository: commit_attributes(
            repository, b"tracked filter=unspecified\n"
        ),
        "exact HEAD attributes",
    )
    exercise_attribute_threat(
        "explicit-unset-filter",
        lambda repository: commit_attributes(repository, b"tracked -filter\n"),
        "exact HEAD attributes",
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-sxpid3-attribute-unspecified-positive-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_attribute_repository(repository)
        commit_attributes(repository, b"tracked !filter\n")
        original_root = capture.ROOT
        capture.ROOT = repository.resolve()
        try:
            require(
                capture.status_bytes() == b"",
                "safe explicitly-unspecified filter attribute changed clean status",
            )
        finally:
            capture.ROOT = original_root
        git_topology_controls += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-sxpid3-attribute-potency-self-test-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_attribute_repository(repository)
        marker = repository / "ordinary-status-filter-executed"
        (repository / ".gitattributes").write_bytes(b"tracked filter=sentinel\n")
        (repository / "tracked").write_bytes(b"changed!\n")
        run_temp_git(
            repository,
            [
                "config",
                "filter.sentinel.clean",
                f"touch {shlex.quote(os.fspath(marker))}; cat",
            ],
        )
        run_temp_git(
            repository,
            [
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--ignore-submodules=all",
            ],
        )
        require(
            marker.exists(),
            "ordinary unpinned status did not execute the hostile control filter",
        )
        git_topology_controls += 1

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-sxpid3-attribute-gap-self-test-"
    ) as raw_repository:
        repository = Path(raw_repository)
        initialize_attribute_repository(repository)
        marker = repository / "filter-executed"
        original_root = capture.ROOT
        original_attribute_closure = capture.require_status_attribute_closure
        closure_calls = 0

        def mutate_after_first_attribute_probe(head_oid: str) -> None:
            nonlocal closure_calls
            closure_calls += 1
            original_attribute_closure(head_oid)
            if closure_calls == 1:
                (repository / ".gitattributes").write_bytes(
                    b"tracked filter=sentinel\n"
                )
                (repository / "tracked").write_bytes(b"changed!\n")
                run_temp_git(
                    repository,
                    [
                        "config",
                        "filter.sentinel.clean",
                        f"touch {shlex.quote(os.fspath(marker))}; cat",
                    ],
                )

        capture.ROOT = repository.resolve()
        capture.require_status_attribute_closure = mutate_after_first_attribute_probe
        try:
            error = expect_rejected(
                capture.status_bytes,
                "attribute-mutation-after-preprobe",
                capture.ReceiptError,
            )
            require(
                "filter, attribute, or include configuration" in str(error)
                and closure_calls >= 2
                and not marker.exists(),
                "exact-OID status pin failed to suppress a gap-inserted clean filter",
            )
        finally:
            capture.require_status_attribute_closure = original_attribute_closure
            capture.ROOT = original_root
        git_topology_controls += 1

    guarded_calls: list[tuple[list[str], dict[str, str]]] = []
    original_run_capped = capture.run_capped

    def record_guarded_call(*arguments: Any, **keywords: Any) -> Any:
        guarded_calls.append((list(arguments[0]), dict(keywords["environment"])))
        return original_run_capped(*arguments, **keywords)

    capture.run_capped = record_guarded_call
    try:
        guarded_status, guarded_stdout, guarded_stderr = capture.git_result(
            ["version"]
        )
    finally:
        capture.run_capped = original_run_capped
    require(
        guarded_status == 0
        and guarded_stdout.startswith(b"git version ")
        and guarded_stderr == b""
        and len(guarded_calls) >= 2,
        "capture guarded Git positive control failed",
    )
    for argv, environment in guarded_calls:
        for required in (
            "core.commitGraph=false",
            f"core.attributesFile={os.devnull}",
            "core.filemode=true",
            "core.symlinks=true",
            "core.checkStat=default",
            "core.trustctime=true",
        ):
            require(required in argv, f"capture guarded Git omitted {required}")
        require(
            environment.get("GIT_ATTR_NOSYSTEM") == "1"
            and environment.get("GIT_CONFIG_GLOBAL") == os.devnull
            and environment.get("GIT_CONFIG_SYSTEM") == os.devnull,
            "capture guarded Git environment isolation drifted",
        )
    ordinary_calls = [
        environment
        for argv, environment in guarded_calls
        if argv[-1] == "version"
    ]
    require(
        len(ordinary_calls) == 1
        and ordinary_calls[0].get("GIT_ATTR_SOURCE")
        == capture.bootstrap_head_oid(),
        "capture ordinary Git call was not pinned to the exact HEAD OID",
    )
    git_topology_controls += 1

    exclusive_controls = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-sxpid3-capture-self-test-") as raw:
        directory = Path(raw)
        created = directory / "receipt.json"
        payload = b"{\"status\":\"test\"}\n"
        created_custody = capture.create_pending_receipt_exclusive(created)
        require(
            capture.read_receipt_through_custody(created_custody)
            == capture.PENDING_RECEIPT_TOMBSTONE,
            "pending marker control drifted",
        )
        capture.rewrite_retained_receipt(created_custody, payload)
        require(
            capture.read_receipt_through_custody(created_custody) == payload
            and stat.S_IMODE(created.stat().st_mode) == 0o600,
            "exclusive-create positive control drifted",
        )
        capture.close_receipt_custody(created_custody)
        exclusive_controls += 1
        sentinel = directory / "sentinel.json"
        sentinel.write_bytes(b"preserve-me")
        expect_rejected(
            lambda: capture.create_pending_receipt_exclusive(sentinel),
            "O_EXCL-existing-path",
            (OSError, capture.ReceiptError),
        )
        require(sentinel.read_bytes() == b"preserve-me", "preexisting sentinel was modified")
        exclusive_controls += 1
        symlink_target = directory / "symlink-target"
        symlink_target.write_bytes(b"symlink-target-bytes")
        preexisting_symlink = directory / "preexisting-symlink"
        preexisting_symlink.symlink_to(symlink_target.name)
        preexisting_fifo = directory / "preexisting-fifo"
        os.mkfifo(preexisting_fifo, 0o600)
        preexisting_directory = directory / "preexisting-directory"
        preexisting_directory.mkdir()
        for path, label in (
            (preexisting_symlink, "O_EXCL-preexisting-symlink"),
            (preexisting_fifo, "O_EXCL-preexisting-FIFO"),
            (preexisting_directory, "O_EXCL-preexisting-directory"),
        ):
            expect_rejected(
                lambda path=path: capture.create_pending_receipt_exclusive(path),
                label,
                (OSError, capture.ReceiptError),
            )
            exclusive_controls += 1
        require(
            preexisting_symlink.is_symlink()
            and symlink_target.read_bytes() == b"symlink-target-bytes"
            and stat.S_ISFIFO(preexisting_fifo.lstat().st_mode)
            and preexisting_directory.is_dir(),
            "preexisting nonregular path was modified",
        )
        rollback = directory / "rollback.json"
        rollback_payload = b"{\"rollback\":true}\n"
        rollback_custody = capture.create_pending_receipt_exclusive(rollback)
        capture.rewrite_retained_receipt(rollback_custody, rollback_payload)
        capture.invalidate_failed_receipt(rollback_custody)
        require(
            rollback.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE,
            "failed-write policy did not invalidate the retained inode",
        )
        expect_rejected(
            lambda: capture.strict_json(rollback.read_bytes(), "failure tombstone"),
            "failure-tombstone-JSON",
            capture.ReceiptError,
        )
        exclusive_controls += 1
        hardlinked = directory / "hardlinked.json"
        hardlinked_peer = directory / "hardlinked-peer.json"
        hardlinked_custody = capture.create_pending_receipt_exclusive(hardlinked)
        capture.rewrite_retained_receipt(hardlinked_custody, rollback_payload)
        os.link(hardlinked, hardlinked_peer)
        expect_rejected(
            lambda: capture.read_receipt_through_custody(hardlinked_custody),
            "hardlink-drift-read",
            capture.ReceiptError,
        )
        expect_rejected(
            lambda: capture.require_receipt_leaf_identity(
                hardlinked_custody, expected_size=len(rollback_payload)
            ),
            "hardlink-drift-final-leaf",
            capture.ReceiptError,
        )
        capture.invalidate_failed_receipt(hardlinked_custody)
        require(
            hardlinked.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE
            and hardlinked_peer.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE,
            "hardlinked retained inode was not invalidated",
        )
        exclusive_controls += 2
        replaced_leaf = directory / "replaced-leaf.json"
        moved_leaf = directory / "moved-retained-inode.json"
        replaced_custody = capture.create_pending_receipt_exclusive(replaced_leaf)
        capture.rewrite_retained_receipt(replaced_custody, rollback_payload)
        replaced_leaf.rename(moved_leaf)
        replaced_leaf.write_bytes(b"replacement-must-survive")
        expect_rejected(
            lambda: capture.read_receipt_through_custody(replaced_custody),
            "leaf-rename-and-replacement",
            capture.ReceiptError,
        )
        capture.invalidate_failed_receipt(replaced_custody)
        require(
            moved_leaf.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE
            and replaced_leaf.read_bytes() == b"replacement-must-survive",
            "leaf replacement was clobbered or retained inode stayed valid",
        )
        exclusive_controls += 1
        short_write = directory / "short-write.json"
        short_write_custody = capture.create_pending_receipt_exclusive(short_write)
        original_os_write = capture.os.write
        write_calls = 0

        def fail_after_partial_write(descriptor: int, payload_bytes: bytes) -> int:
            nonlocal write_calls
            write_calls += 1
            if write_calls == 1:
                return original_os_write(descriptor, payload_bytes[:1])
            return 0

        capture.os.write = fail_after_partial_write
        try:
            expect_rejected(
                lambda: capture.rewrite_retained_receipt(
                    short_write_custody, rollback_payload
                ),
                "short-write-failure",
                capture.ReceiptError,
            )
        finally:
            capture.os.write = original_os_write
        capture.invalidate_failed_receipt(short_write_custody)
        require(
            short_write.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE,
            "partial write left schema-capable bytes",
        )
        exclusive_controls += 1
        fsync_failure = directory / "fsync-failure.json"
        fsync_custody = capture.create_pending_receipt_exclusive(fsync_failure)
        original_os_fsync = capture.os.fsync

        def fail_file_fsync(_descriptor: int) -> None:
            raise OSError("injected fsync failure")

        capture.os.fsync = fail_file_fsync
        try:
            expect_rejected(
                lambda: capture.rewrite_retained_receipt(
                    fsync_custody, rollback_payload
                ),
                "fsync-failure",
                OSError,
            )
        finally:
            capture.os.fsync = original_os_fsync
        capture.invalidate_failed_receipt(fsync_custody)
        require(
            fsync_failure.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE,
            "fsync failure left schema-capable bytes",
        )
        exclusive_controls += 1
        changed = directory / "changed.json"
        changed_custody = capture.create_pending_receipt_exclusive(changed)
        capture.rewrite_retained_receipt(changed_custody, rollback_payload)
        changed.chmod(0o644)
        changed.write_bytes(b"hostile-change")
        capture.invalidate_failed_receipt(changed_custody)
        require(
            changed.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE
            and stat.S_IMODE(changed.stat().st_mode) == 0o600,
            "exact retained changed inode was not invalidated in mode 0600",
        )
        exclusive_controls += 1

        release_payload = b'{"finalized":true}\n'

        def exercise_release_failure(fail_slot: str) -> None:
            nonlocal exclusive_controls
            release_failure = directory / f"release-{fail_slot}-failure.json"
            release_custody = capture.create_pending_receipt_exclusive(
                release_failure
            )
            capture.rewrite_retained_receipt(release_custody, release_payload)
            require(
                capture.read_receipt_through_custody(release_custody)
                == release_payload,
                "finalized-release fixture bytes drifted",
            )
            file_descriptor = release_custody["file_fd"]
            parent_descriptor = release_custody["parent_fd"]
            failed_descriptor = (
                file_descriptor if fail_slot == "file" else parent_descriptor
            )
            close_attempts: list[int] = []
            original_os_close = capture.os.close

            def report_failure_before_close(descriptor: int) -> None:
                close_attempts.append(descriptor)
                if descriptor == failed_descriptor:
                    raise OSError(
                        f"injected finalized {fail_slot}-descriptor release failure"
                    )
                original_os_close(descriptor)

            capture.os.close = report_failure_before_close
            try:
                release_error = expect_rejected(
                    lambda: capture.release_finalized_receipt_custody(
                        release_custody
                    ),
                    f"finalized-{fail_slot}-release",
                    capture.FinalizedDescriptorReleaseError,
                )
            finally:
                capture.os.close = original_os_close
                original_os_close(failed_descriptor)
            require(
                close_attempts == [file_descriptor, parent_descriptor]
                and release_custody["file_fd"] == -1
                and release_custody["parent_fd"] == -1
                and release_failure.read_bytes() == release_payload
                and stat.S_IMODE(release_failure.stat().st_mode) == 0o600
                and "do not rerun capture" in str(release_error),
                "finalized descriptor-release policy drifted or tombstoned valid bytes",
            )
            exclusive_controls += 1

        exercise_release_failure("file")
        exercise_release_failure("parent")

        same_size = directory / "same-size-post-reverify.json"
        expected_final = b'{"finalized":true}\n'
        hostile_final = b'{"finalized":null}\n'
        require(
            len(expected_final) == len(hostile_final),
            "same-size finalization fixture lengths drifted",
        )
        same_size_custody = capture.create_pending_receipt_exclusive(same_size)
        capture.rewrite_retained_receipt(same_size_custody, expected_final)
        same_size.write_bytes(hostile_final)
        same_size.chmod(0o600)
        expect_rejected(
            lambda: capture.require(
                capture.read_receipt_through_custody(same_size_custody)
                == expected_final,
                "final post-reverification receipt bytes differ from canonical bytes",
            ),
            "same-size-post-reverification-mutation",
            capture.ReceiptError,
        )
        capture.invalidate_failed_receipt(same_size_custody)
        require(
            same_size.read_bytes() == capture.FAILED_RECEIPT_TOMBSTONE,
            "same-size finalization mutation was not tombstoned",
        )
        exclusive_controls += 1

        original_parse_arguments = capture.parse_arguments
        original_build_and_write_receipt = capture.build_and_write_receipt

        def raise_release_error() -> tuple[str, str]:
            raise capture.FinalizedDescriptorReleaseError(
                "verified finalized receipt bytes were retained but descriptor release failed; "
                "do not rerun capture, validate the retained file prospectively"
            )

        capture.parse_arguments = lambda: None
        capture.build_and_write_receipt = raise_release_error
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(
                captured_stderr
            ):
                main_status = capture.main()
        finally:
            capture.parse_arguments = original_parse_arguments
            capture.build_and_write_receipt = original_build_and_write_receipt
        require(
            main_status == 1
            and captured_stdout.getvalue() == ""
            and "retained verified finalized bytes after descriptor-release failure"
            in captured_stderr.getvalue()
            and "WROTE" not in captured_stderr.getvalue(),
            "finalized descriptor-release CLI classification drifted",
        )
        exclusive_controls += 1
        original_parent = directory / "original-parent"
        moved_parent = directory / "moved-parent"
        original_parent.mkdir()
        parent_swap_path = original_parent / "receipt.json"
        parent_swap_custody = capture.create_pending_receipt_exclusive(parent_swap_path)
        capture.rewrite_retained_receipt(parent_swap_custody, rollback_payload)
        original_parent.rename(moved_parent)
        original_parent.mkdir()
        (original_parent / "sentinel").write_bytes(b"replacement-parent")
        expect_rejected(
            lambda: capture.require_receipt_parent_identity(parent_swap_custody),
            "parent-directory-swap",
            capture.ReceiptError,
        )
        capture.invalidate_failed_receipt(parent_swap_custody)
        require(
            (moved_parent / "receipt.json").read_bytes()
            == capture.FAILED_RECEIPT_TOMBSTONE
            and (original_parent / "sentinel").read_bytes() == b"replacement-parent",
            "parent-swap control altered the wrong directory entry",
        )
        exclusive_controls += 1

    source = {
        "source_commit": "1" * 40,
        "source_tree": "2" * 40,
        "source_delta": [{"path": "source", "source_sha256": "3" * 64}],
    }
    inputs = [
        {
            "path": "input",
            "git_mode": "100755",
            "live_mode": "0755",
            "sha256": "4" * 64,
        }
    ]
    p1 = {"paths": [{"path": "p1", "sha256": "5" * 64}]}
    scenario = {
        "head": source["source_commit"],
        "tree": source["source_tree"],
        "source": source,
        "inputs": inputs,
        "p1": p1,
        "status": b"",
    }
    originals = (
        capture.canonical_repository,
        capture.status_bytes,
        capture.git_line,
        capture.source_package,
        capture.execution_inputs,
        capture.p1_binding,
        capture.host_boundary,
    )

    def fake_git_line(arguments: list[str]) -> str:
        return scenario["tree"] if arguments[-1] == "HEAD^{tree}" else scenario["head"]

    capture.git_line = fake_git_line
    capture.canonical_repository = lambda: None
    capture.status_bytes = lambda: scenario["status"]
    capture.source_package = lambda _commit, require_live: scenario["source"]
    capture.execution_inputs = lambda _commit: scenario["inputs"]
    capture.p1_binding = lambda _commit: scenario["p1"]
    expected_host = {"python": "bound", "git": "bound"}
    scenario["host"] = expected_host
    capture.host_boundary = lambda: scenario["host"]
    race_controls = 0
    try:
        capture.reverify(source, inputs, p1, expected_host, b"")
        mutations = (
            ("head", "6" * 40, "HEAD-race"),
            ("tree", "7" * 40, "tree-race"),
            (
                "source",
                source | {"source_delta": [{"path": "source", "source_sha256": "8" * 64}]},
                "source-blob-race",
            ),
            (
                "inputs",
                [inputs[0] | {"sha256": "9" * 64}],
                "input-byte-race",
            ),
            (
                "inputs",
                [inputs[0] | {"git_mode": "100644", "live_mode": "0644"}],
                "input-mode-race",
            ),
            (
                "p1",
                {"paths": [{"path": "p1", "sha256": "a" * 64}]},
                "P1-race",
            ),
            (
                "host",
                {"python": "changed", "git": "bound"},
                "host-tool-race",
            ),
            ("status", b"?? hostile\0", "status-race"),
        )
        for key, value, label in mutations:
            baseline = scenario[key]
            scenario[key] = value
            expect_rejected(
                lambda: capture.reverify(source, inputs, p1, expected_host, b""),
                label,
                capture.ReceiptError,
            )
            scenario[key] = baseline
            race_controls += 1
    finally:
        (
            capture.canonical_repository,
            capture.status_bytes,
            capture.git_line,
            capture.source_package,
            capture.execution_inputs,
            capture.p1_binding,
            capture.host_boundary,
        ) = originals

    python = os.fspath(Path(sys.executable).resolve())
    exact_lane_controls = 0
    historical_paths = {
        "scripts/check-sxpid3-bounded-full-coordinates-self-test.py": "100755",
        "scripts/check-sxpid3-bounded-full-coordinates.py": "100755",
        "crates/pid-core/src/discrete_pid.rs": "100644",
    }
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-sxpid3-historical-exact-lane-"
    ) as raw_historical:
        historical_root = Path(raw_historical)
        for relative, expected_mode in historical_paths.items():
            entry = capture.ls_tree_entry(capture.BASE_COMMIT, relative)
            require(
                entry is not None and entry[0] == expected_mode,
                f"historical exact-lane blob or mode drifted: {relative}",
            )
            destination = historical_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(entry[2])
            destination.chmod(0o755 if expected_mode == "100755" else 0o644)
        primary_self_test = (
            historical_root
            / "scripts"
            / "check-sxpid3-bounded-full-coordinates-self-test.py"
        )
        primary_source = primary_self_test.read_bytes()
        require(
            len(primary_source) == 34_513
            and capture.sha256_bytes(primary_source)
            == "2f51c83502c3dc89952f04a9d046a472e76dae1b11a322173ef353be6976df5d",
            "historical primary self-test source pin drifted",
        )
        lane_status, lane_stdout, lane_stderr, lane_timed_out = capture.run_capped(
            [python, "-I", "-S", "-B", os.fspath(primary_self_test)],
            cwd=historical_root,
            timeout_seconds=300,
            stdout_cap=4 * 1024 * 1024,
            stderr_cap=1024 * 1024,
        )
    require(
        lane_status == 0
        and not lane_timed_out
        and lane_stderr == b""
        and len(lane_stdout) == 1_106
        and capture.sha256_bytes(lane_stdout)
        == "971aaca8d31230b775f69d0f5f1e91e5f9ef9579dc853cff1b6d1c845dfa7e10",
        "primary self-test exact stdout pin drifted",
    )
    exact_lane_controls += 1
    help_run = subprocess_result([python, "-I", "-S", "-B", os.fspath(CAPTURE_PATH), "--help"])
    require(
        help_run.returncode == 0
        and help_run.stderr == b""
        and b"--write-receipt" in help_run.stdout
        and b"--self-test" not in help_run.stdout,
        "production CLI help contract drifted",
    )
    missing_flag = subprocess_result([python, "-I", "-S", "-B", os.fspath(CAPTURE_PATH)])
    require(missing_flag.returncode == 2 and missing_flag.stdout == b"", "explicit write flag is not required")
    optimized = subprocess_result(
        [
            python,
            "-O",
            "-I",
            "-S",
            "-B",
            os.fspath(CAPTURE_PATH),
            "--write-receipt",
        ]
    )
    require(
        optimized.returncode == 1
        and optimized.stdout == b""
        and b"capture rejects optimized Python" in optimized.stderr,
        "optimized production capture did not fail closed",
    )

    process_controls = 0
    residual_program = (
        "import subprocess,sys;"
        "subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],"
        "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)"
    )
    started = time.monotonic()
    expect_rejected(
        lambda: capture.run_capped(
            [python, "-I", "-S", "-B", "-c", residual_program],
            cwd=ROOT,
            timeout_seconds=5,
            stdout_cap=1024,
            stderr_cap=1024,
        ),
        "residual-process-group-member",
        capture.ReceiptError,
    )
    require(time.monotonic() - started < 5, "residual group control reached timeout")
    process_controls += 1
    inherited_pipe_program = (
        "import subprocess,sys;"
        "subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])"
    )
    started = time.monotonic()
    expect_rejected(
        lambda: capture.run_capped(
            [python, "-I", "-S", "-B", "-c", inherited_pipe_program],
            cwd=ROOT,
            timeout_seconds=5,
            stdout_cap=1024,
            stderr_cap=1024,
        ),
        "residual-process-group-member-holding-pipes",
        capture.ReceiptError,
    )
    require(
        time.monotonic() - started < 5,
        "inherited-pipe residual group control reached timeout",
    )
    process_controls += 1

    def require_group_absent(process_group_id: int, label: str) -> None:
        try:
            os.killpg(process_group_id, 0)
        except ProcessLookupError:
            return
        except PermissionError as error:
            raise SelfTestError(
                f"cannot establish process-group absence after {label}"
            ) from error
        raise SelfTestError(f"process group survived injected {label} failure")

    def exercise_injected_process_failure(
        label: str,
        *,
        selector_factory: Any | None = None,
        fail_read: bool = False,
    ) -> None:
        nonlocal process_controls
        original_popen = capture.subprocess.Popen
        original_selector_factory = capture.selectors.DefaultSelector
        original_read_process_pipe = capture.read_process_pipe
        spawned: list[int] = []

        def recording_popen(*arguments: Any, **keywords: Any) -> Any:
            process = original_popen(*arguments, **keywords)
            spawned.append(process.pid)
            return process

        def injected_read(_descriptor: int, _size: int) -> bytes:
            raise OSError("injected pipe-read failure")

        capture.subprocess.Popen = recording_popen
        if selector_factory is not None:
            capture.selectors.DefaultSelector = selector_factory
        if fail_read:
            capture.read_process_pipe = injected_read
        try:
            expect_rejected(
                lambda: capture.run_capped(
                    [
                        python,
                        "-I",
                        "-S",
                        "-B",
                        "-c",
                        "import sys,time;sys.stdout.write('x');sys.stdout.flush();time.sleep(30)",
                    ],
                    cwd=ROOT,
                    timeout_seconds=5,
                    stdout_cap=1024,
                    stderr_cap=1024,
                ),
                label,
                (OSError, capture.ReceiptError),
            )
        finally:
            capture.read_process_pipe = original_read_process_pipe
            capture.selectors.DefaultSelector = original_selector_factory
            capture.subprocess.Popen = original_popen
        require(len(spawned) == 1, f"{label} did not record exactly one child")
        require_group_absent(spawned[0], label)
        process_controls += 1

    def selector_construction_failure() -> Any:
        raise OSError("injected selector construction failure")

    class RegisterFailureSelector:
        def register(self, _descriptor: int, _events: int) -> None:
            raise OSError("injected selector register failure")

        def close(self) -> None:
            return None

    class SelectFailureSelector:
        def __init__(self) -> None:
            self.inner = capture.selectors.DefaultSelector_original_for_test()

        def register(self, descriptor: int, events: int) -> Any:
            return self.inner.register(descriptor, events)

        def get_map(self) -> Any:
            return self.inner.get_map()

        def select(self, _timeout: float) -> Any:
            raise OSError("injected selector select failure")

        def unregister(self, descriptor: int) -> Any:
            return self.inner.unregister(descriptor)

        def close(self) -> None:
            self.inner.close()

    capture.selectors.DefaultSelector_original_for_test = (
        capture.selectors.DefaultSelector
    )
    try:
        exercise_injected_process_failure(
            "selector-construction", selector_factory=selector_construction_failure
        )
        exercise_injected_process_failure(
            "selector-register", selector_factory=RegisterFailureSelector
        )
        exercise_injected_process_failure(
            "selector-select", selector_factory=SelectFailureSelector
        )
        exercise_injected_process_failure("pipe-read", fail_read=True)
    finally:
        del capture.selectors.DefaultSelector_original_for_test

    try:
        status, _stdout, _stderr, timed_out = capture.run_capped(
            [python, "-I", "-S", "-B", "-c", "import time;time.sleep(30)"],
            cwd=ROOT,
            timeout_seconds=1,
            stdout_cap=1024,
            stderr_cap=1024,
        )
    except capture.ReceiptError:
        timed_out = True
        status = -1
    require(timed_out and status != 0, "process timeout control did not fail closed")
    process_controls += 1
    expect_rejected(
        lambda: capture.run_capped(
            [python, "-I", "-S", "-B", "-c", "print('x'*2048)"],
            cwd=ROOT,
            timeout_seconds=5,
            stdout_cap=64,
            stderr_cap=64,
        ),
        "stdout-cap",
        capture.ReceiptError,
    )
    process_controls += 1
    for token in (b"NaN", b"Infinity", b"-Infinity"):
        expect_rejected(
            lambda token=token: capture.strict_json(
                b'{"value":' + token + b"}\n", "non-finite-number"
            ),
            f"non-finite-{token.decode('ascii')}",
            capture.ReceiptError,
        )
        process_controls += 1

    result = {
        "cli_controls": 3,
        "exclusive_create_controls": exclusive_controls,
        "exact_committed_lane_controls": exact_lane_controls,
        "format": "/pid-rs/sxpid3-bounded-keyed-scalar-audit-expressions-capture-self-test/v1",
        "git_topology_controls": git_topology_controls,
        "normal_optimized_self_test_contract": True,
        "process_group_and_cap_controls": process_controls,
        "race_controls": race_controls,
        "status_and_index_controls": status_controls,
        "status": "GO",
        "total_hostile_controls": 3 + exact_lane_controls + exclusive_controls + git_topology_controls + process_controls + race_controls + status_controls,
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, SelfTestError) as error:
        print(f"ERROR: capture self-test failed closed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
