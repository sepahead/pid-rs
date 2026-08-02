#!/usr/bin/env python3
from __future__ import annotations

import sys

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    print(
        "ERROR: check-c3-hosted-followup.py requires Python -I -S",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
from collections.abc import Iterator
from enum import Enum
import hashlib
import json
import os
import selectors
import signal
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import threading
import time
from typing import Any


class FollowupError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FollowupError(message)


OWNED_CHILD_SIGNAL_MASK_DEPTH = 0
VERIFIER_SIGNAL_RUNTIME_ACTIVE = False
VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE = False
DEFERRED_VERIFIER_SIGNAL_FLAGS: list[bool] = [False, False]


def add_exception_note_preserving_primary(
    primary: BaseException, note: str
) -> None:
    # Notes are evidence, not cleanup authority.  Formatting/allocation failure
    # under exceptional memory pressure must not replace the initiating error or
    # prevent the remaining child/local-resource teardown.
    try:
        primary.add_note(note)
    except BaseException:
        pass


def add_secondary_exception_note(
    primary: BaseException, label: str, secondary: BaseException
) -> None:
    try:
        note = f"{label}: {type(secondary).__name__}: {secondary}"
    except BaseException:
        return
    add_exception_note_preserving_primary(primary, note)


def retain_cleanup_exception(
    primary: BaseException | None,
    secondary: BaseException,
    *,
    label: str,
) -> BaseException:
    if primary is None:
        return secondary
    add_secondary_exception_note(primary, label, secondary)
    return primary


def close_descriptor_preserving_error(
    descriptor: int | None,
    primary: BaseException | None,
    *,
    label: str,
) -> BaseException | None:
    if descriptor is None:
        return primary
    try:
        os.close(descriptor)
    except BaseException as error:
        return retain_cleanup_exception(primary, error, label=label)
    return primary


def owned_child_exception_signals() -> frozenset[signal.Signals]:
    require(
        all(
            hasattr(signal, name)
            for name in (
                "SIGALRM",
                "SIGINT",
                "SIG_BLOCK",
                "SIG_SETMASK",
                "SIG_UNBLOCK",
                "pthread_sigmask",
                "sigpending",
            )
        ),
        "follow-up gate requires POSIX thread-directed signal masking",
    )
    return frozenset((signal.SIGALRM, signal.SIGINT))


def require_dedicated_main_python_thread() -> None:
    require(
        threading.current_thread() is threading.main_thread(),
        "owned-child lifecycle requires the Python main thread",
    )
    require(
        threading.active_count() == 1 and len(threading.enumerate()) == 1,
        "owned-child lifecycle requires one enumerated Python thread",
    )


def verifier_signal_handler(signal_number: int, _frame: Any) -> None:
    # Never raise from CPython's asynchronous signal checkpoint.  A signal can
    # reach the low-level handler immediately before pthread_sigmask() and the
    # queued Python callback can run after the mask is installed; sigpending()
    # cannot distinguish that already-consumed case.  Record only.  Explicit
    # safe points either precede Popen, run inside a known cleanup scope, or
    # follow complete child/resource teardown.
    # Both list slots and both bool singletons are allocated before handler
    # installation.  Under the exact-source, single-enumerated-thread runtime,
    # this path only replaces an existing reference; it performs no container
    # growth, enum construction, formatting, or explicit allocation.
    if signal_number == signal.SIGALRM:
        DEFERRED_VERIFIER_SIGNAL_FLAGS[0] = True
    elif signal_number == signal.SIGINT:
        DEFERRED_VERIFIER_SIGNAL_FLAGS[1] = True


def deferred_verifier_signals() -> tuple[signal.Signals, ...]:
    # Allocation and presentation happen only at explicit safe points.
    return tuple(
        sorted(
            (
                selected
                for selected, observed in zip(
                    (signal.SIGALRM, signal.SIGINT),
                    DEFERRED_VERIFIER_SIGNAL_FLAGS,
                )
                if observed
            ),
            key=int,
        )
    )


def activate_verifier_signal_runtime() -> tuple[Any, Any]:
    global VERIFIER_SIGNAL_RUNTIME_ACTIVE
    require_dedicated_main_python_thread()
    require_sigchld_default()
    require(
        sys.implementation.name == "cpython",
        "follow-up gate requires CPython signal-checkpoint semantics",
    )
    require(
        (3, 11) <= sys.version_info[:2] < (3, 15)
        and (
            not hasattr(sys, "_is_gil_enabled")
            or bool(sys._is_gil_enabled())
        ),
        "follow-up gate requires reviewed GIL-enabled CPython 3.11-3.14",
    )
    require(
        not VERIFIER_SIGNAL_RUNTIME_ACTIVE
        and not VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE
        and OWNED_CHILD_SIGNAL_MASK_DEPTH == 0,
        "verifier signal runtime is already active",
    )
    selected = owned_child_exception_signals()
    require(
        selected.isdisjoint(current_thread_signal_mask()),
        "verifier inherited a blocked SIGALRM or SIGINT",
    )
    require(
        selected.isdisjoint(frozenset(signal.sigpending())),
        "verifier inherited a pending SIGALRM or SIGINT",
    )
    previous_alarm = signal.getsignal(signal.SIGALRM)
    previous_interrupt = signal.getsignal(signal.SIGINT)
    require(
        previous_interrupt == signal.default_int_handler,
        "follow-up gate requires Python's default SIGINT handler at entry",
    )
    DEFERRED_VERIFIER_SIGNAL_FLAGS[0] = False
    DEFERRED_VERIFIER_SIGNAL_FLAGS[1] = False
    try:
        signal.signal(signal.SIGALRM, verifier_signal_handler)
        signal.signal(signal.SIGINT, verifier_signal_handler)
    except BaseException as error:
        # Either signal.signal call can side-effect before its Python wrapper
        # raises.  Restore both dispositions independently; failure of the first
        # rollback must not skip the second.
        for selected, previous in (
            (signal.SIGALRM, previous_alarm),
            (signal.SIGINT, previous_interrupt),
        ):
            try:
                signal.signal(selected, previous)
            except BaseException as restore_error:
                add_secondary_exception_note(
                    error,
                    "partial signal-runtime installation rollback failed",
                    restore_error,
                )
        raise
    VERIFIER_SIGNAL_RUNTIME_ACTIVE = True
    return previous_alarm, previous_interrupt


def deactivate_verifier_signal_runtime(
    previous_handlers: tuple[Any, Any],
    *,
    primary_error: BaseException | None,
) -> BaseException | None:
    global VERIFIER_SIGNAL_RUNTIME_ACTIVE
    require(
        OWNED_CHILD_SIGNAL_MASK_DEPTH == 0
        and not VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE,
        "verifier signal runtime ended with an owned child scope",
    )
    restoration_error: BaseException | None = None
    # CPython checks queued callbacks before signal.signal replaces each Python
    # handler.  With no child/mask scope and the timer already disarmed, this is
    # a child-free per-signal handoff: queued recorder callbacks are materialized
    # before their disposition changes.  Restore both independently.
    for selected, previous in (
        (signal.SIGALRM, previous_handlers[0]),
        (signal.SIGINT, previous_handlers[1]),
    ):
        try:
            signal.signal(selected, previous)
        except BaseException as error:
            restoration_error = retain_cleanup_exception(
                restoration_error,
                error,
                label="verifier signal-handler restoration",
            )
    if restoration_error is None:
        VERIFIER_SIGNAL_RUNTIME_ACTIVE = False
    else:
        # A wrapper can side-effect and then raise.  Reinstall both recorders so
        # ACTIVE never falsely describes a partially restored disposition.
        for selected in (signal.SIGALRM, signal.SIGINT):
            try:
                signal.signal(selected, verifier_signal_handler)
            except BaseException as rollback_error:
                add_secondary_exception_note(
                    restoration_error,
                    "signal-handler restoration rollback also failed",
                    rollback_error,
                )
        if primary_error is not None:
            add_secondary_exception_note(
                primary_error,
                "verifier signal-handler restoration also failed",
                restoration_error,
            )
    effective_error = primary_error or restoration_error
    deferred = deferred_verifier_signals()
    if deferred:
        detail = ", ".join(item.name for item in deferred)
        if effective_error is not None:
            add_exception_note_preserving_primary(
                effective_error,
                f"deferred verifier signals observed after child cleanup: {detail}"
            )
        elif signal.SIGINT in deferred:
            return KeyboardInterrupt()
        else:
            return FollowupError(
                f"validation exceeded the {VALIDATION_TIMEOUT_SECONDS}-second deadline"
            )
    return restoration_error


def raise_deferred_verifier_signal_if_safe(
    primary_error: BaseException | None,
) -> None:
    deferred = deferred_verifier_signals()
    if not deferred:
        return
    detail = ", ".join(item.name for item in deferred)
    if primary_error is not None:
        add_exception_note_preserving_primary(
            primary_error,
            f"deferred verifier signals observed after child cleanup: {detail}"
        )
        return
    if signal.SIGINT in deferred:
        raise KeyboardInterrupt
    raise FollowupError(
        f"validation exceeded the {VALIDATION_TIMEOUT_SECONDS}-second deadline"
    )


def current_thread_signal_mask() -> frozenset[signal.Signals]:
    try:
        return frozenset(signal.pthread_sigmask(signal.SIG_BLOCK, set()))
    except (OSError, RuntimeError, ValueError) as error:
        raise FollowupError(f"cannot inspect the Python-thread signal mask: {error}") from error


def child_unblock_owned_exception_signals() -> None:
    # Popen invokes this only after a fork from the authenticated single Python
    # thread.  The parent-specific critical-section mask must not escape through
    # exec into Git or an exact-source Python child.
    signal.pthread_sigmask(signal.SIG_UNBLOCK, (signal.SIGALRM, signal.SIGINT))


class OwnedChildSignalMask:
    def __init__(
        self,
        *,
        label: str,
        previous_mask: frozenset[signal.Signals],
        depth: int,
    ) -> None:
        self.label = label
        self.previous_mask = previous_mask
        self.depth = depth
        self.held = True

    @classmethod
    def acquire(cls, *, label: str) -> OwnedChildSignalMask:
        global OWNED_CHILD_SIGNAL_MASK_DEPTH, VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE
        require_dedicated_main_python_thread()
        require_sigchld_default()
        require(
            VERIFIER_SIGNAL_RUNTIME_ACTIVE,
            f"{label} has no active verifier signal runtime",
        )
        require(
            not VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE,
            f"{label} verifier signal mask is indeterminate",
        )
        require(
            signal.getsignal(signal.SIGALRM) == verifier_signal_handler
            and signal.getsignal(signal.SIGINT) == verifier_signal_handler,
            f"{label} verifier signal handlers changed",
        )
        selected = owned_child_exception_signals()
        before = current_thread_signal_mask()
        if OWNED_CHILD_SIGNAL_MASK_DEPTH == 0:
            require(
                selected.isdisjoint(before),
                f"{label} inherited a blocked verifier signal outside nesting",
            )
        else:
            require(
                selected.issubset(before),
                f"{label} nested verifier signal mask is incomplete",
            )
        raise_deferred_verifier_signal_if_safe(None)
        # Increase the depth before changing the kernel mask.  Keep the exact
        # pre-call mask as the recovery authority: pthread_sigmask() can change
        # the mask before constructing/returning its Python set, and converting
        # that set or constructing the capability can fail afterwards.
        OWNED_CHILD_SIGNAL_MASK_DEPTH += 1
        mask_call_started = False
        try:
            mask_call_started = True
            returned_previous = signal.pthread_sigmask(signal.SIG_BLOCK, selected)
            previous = frozenset(returned_previous)
            require(
                previous == before,
                f"{label} pthread_sigmask returned an unexpected prior mask",
            )
            after = current_thread_signal_mask()
            require(
                selected.issubset(after),
                f"{label} could not block verifier exception signals",
            )
            return cls(
                label=label,
                previous_mask=before,
                depth=OWNED_CHILD_SIGNAL_MASK_DEPTH,
            )
        except BaseException as error:
            restore_error: BaseException | None = None
            if mask_call_started:
                try:
                    signal.pthread_sigmask(signal.SIG_SETMASK, before)
                except BaseException as observed_restore_error:
                    restore_error = observed_restore_error
            if restore_error is None:
                OWNED_CHILD_SIGNAL_MASK_DEPTH -= 1
            else:
                VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE = True
            if restore_error is not None:
                add_secondary_exception_note(
                    error,
                    f"{label} failed-acquisition mask restoration also failed",
                    restore_error,
                )
            raise

    def require_held(self, *, operation: str) -> None:
        require(self.held, f"{operation} lost its owned-child signal mask")
        require(
            OWNED_CHILD_SIGNAL_MASK_DEPTH == self.depth,
            f"{operation} signal-mask scopes are not LIFO",
        )
        require(
            owned_child_exception_signals().issubset(current_thread_signal_mask()),
            f"{operation} verifier exception signals are not blocked",
        )

    def restore(self) -> None:
        global OWNED_CHILD_SIGNAL_MASK_DEPTH
        self.require_held(operation=self.label)
        try:
            signal.pthread_sigmask(signal.SIG_SETMASK, self.previous_mask)
        except BaseException as error:
            raise FollowupError(
                f"{self.label} could not restore the prior signal mask: {error}"
            ) from error
        # A failed restoration keeps the capability and depth live.  That makes
        # verifier-runtime deactivation fail closed instead of restoring raising
        # handlers while SIGALRM/SIGINT may remain kernel-blocked.
        self.held = False
        OWNED_CHILD_SIGNAL_MASK_DEPTH -= 1


def restore_signal_mask_preserving_error(
    ownership: OwnedChildSignalMask,
    primary: BaseException | None,
    *,
    label: str,
) -> None:
    stored_restore_error: BaseException | None = None
    try:
        ownership.restore()
    except BaseException as error:
        if primary is None:
            stored_restore_error = error
        else:
            add_secondary_exception_note(primary, label, error)
    effective_error = primary or stored_restore_error
    raise_deferred_verifier_signal_if_safe(effective_error)
    if primary is None and stored_restore_error is not None:
        raise stored_restore_error


def reset_sigchld_for_owned_children() -> None:
    require(
        hasattr(signal, "SIGCHLD"),
        "follow-up gate requires POSIX SIGCHLD child ownership",
    )
    try:
        # This is an active reset, not an inspection: sigaction replacement via
        # signal.signal clears an inherited SIG_IGN/SA_NOCLDWAIT disposition.
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    except (OSError, RuntimeError, ValueError) as error:
        raise FollowupError(f"cannot reset SIGCHLD to SIG_DFL: {error}") from error
    require_sigchld_default()


def require_sigchld_default() -> None:
    try:
        disposition = signal.getsignal(signal.SIGCHLD)
    except (OSError, RuntimeError, ValueError) as error:
        raise FollowupError(f"cannot inspect SIGCHLD disposition: {error}") from error
    require(
        disposition == signal.SIG_DFL,
        "SIGCHLD disposition changed after explicit SIG_DFL reset",
    )


# The exact-source Python process is dedicated to this gate.  Normalize before
# the first possible Popen; every launch site also rechecks the invariant.
reset_sigchld_for_owned_children()


SCRIPT_PATH = Path(__file__).resolve(strict=True)
ROOT = SCRIPT_PATH.parent.parent.resolve(strict=True)
RECEIPT_RELATIVE = "audit/evidence/c3-hosted-followup-correction-2026-08-01.md"
SELF_TEST_RELATIVE = "scripts/check-c3-hosted-followup-self-test.py"
CHECKER_RELATIVE = "scripts/check-c3-hosted-followup.py"
WRAPPER_RELATIVE = "scripts/check-ksg-c3-checkpoint.sh"
RUNNER_RELATIVE = "scripts/check-c3-hosted-followup.sh"
CERTIFIED_CLAIM_CHECKER_RELATIVE = "scripts/check-certified-sxpid2-claim.py"
ANCHOR = "8fa6e992d9124229c7a175c4508bf10df336675a"
ANCHOR_TREE = "059dc980d4a86066c07687188a452cf2459899eb"
ANCHOR_PATH_COUNT = 560
CANDIDATE_PATH_COUNT = 565
MAX_TREE_DEPTH = 64
MAX_TREE_OBJECT_VISITS = 2_048
MAX_COMMIT_OBJECT_BYTES = 64 * 1024
MAX_TREE_OBJECT_BYTES = 512 * 1024
MAX_TREE_RAW_BYTES = 512 * 1024
MAX_BLOB_OBJECT_BYTES = 4 * 1024 * 1024
MAX_BLOB_LOGICAL_BYTES = 48 * 1024 * 1024
MAX_INDEX_BYTES = 8 * 1024 * 1024
GIT_COMMAND_TIMEOUT_SECONDS = 60
VALIDATION_TIMEOUT_SECONDS = 300
PROCESS_GROUP_GRACE_SECONDS = 1.0
PROCESS_GROUP_PROBE_INTERVAL_SECONDS = 0.01
MAX_WORKTREE_NODES = 4_096
MAX_DIRECTORY_ENTRIES = 4_096
MAX_PATH_BYTES = 4_096
MAX_COMPONENT_BYTES = 255
MAX_EXACT_SOURCE_BYTES = 256 * 1024
MAX_WORKTREE_FILE_BYTES = 4 * 1024 * 1024
MAX_WORKTREE_LOGICAL_BYTES = 48 * 1024 * 1024
MAX_TOOL_FILE_BYTES = 64 * 1024 * 1024
MAX_GIT_TEXT_STDOUT_BYTES = 64 * 1024
MAX_GIT_CONFIG_STDOUT_BYTES = 256 * 1024
MAX_GIT_INVENTORY_STDOUT_BYTES = 4 * 1024 * 1024
MAX_GIT_STDERR_BYTES = 64 * 1024
MAX_GIT_STDIN_BYTES = 64 * 1024
MAX_CAT_FILE_HEADER_BYTES = 128
MAX_RECEIPT_BYTES = 64 * 1024
MAX_APPLICATION_VISIBLE_BYTES = 1024 * 1024 * 1024
IO_CHUNK_BYTES = 1024 * 1024
ANCHOR_PROJECTION_SHA256 = (
    "54e26259d4d974ed6eaa530e042367479c9fac188bde936568aca364e583f917"
)
EXPECTED_COMMIT_MESSAGE = "fix: repair C3 hosted portability gates\n"
EXPECTED_DISPLAY_NAME = "Sepehr Mahmoudian"
EXPECTED_EMAIL = "sepmhn@gmail.com"
EXPECTED_PATH_STATUS = {
    ".github/workflows/ci.yml": "M",
    "AGENTS.md": "M",
    "CHANGELOG.md": "M",
    RECEIPT_RELATIVE: "A",
    "crates/pid-core/build_support.rs": "M",
    "crates/pid-core/tests/software_identity_build.rs": "M",
    "justfile": "M",
    "scripts/README.md": "M",
    CERTIFIED_CLAIM_CHECKER_RELATIVE: "M",
    CHECKER_RELATIVE: "A",
    SELF_TEST_RELATIVE: "A",
    WRAPPER_RELATIVE: "A",
    RUNNER_RELATIVE: "A",
}
SELF_UNHASHED_PATHS = frozenset({CHECKER_RELATIVE, RUNNER_RELATIVE})

# Generated only after every allowed byte settles. The outer runner hashes this checker and the
# self-test; this checker hashes the self-test and every other allowed blob while leaving itself
# and the runner to the independently supplied candidate-tree/checkpoint pair.
EXPECTED_ALLOWED_BLOBS: dict[str, tuple[str, int, str]] = {
    ".github/workflows/ci.yml": (
        "100644",
        49_648,
        "dc420ee70075fe3eb4359c84241b9bb8146c281ea912a6a9ede5aa96d96e6650",
    ),
    "AGENTS.md": (
        "100644",
        31_471,
        "a7aec1f9e0f1adbc4e178576cd08daf993b7e49883d6dd2bcc523968d6e16a3a",
    ),
    "CHANGELOG.md": (
        "100644",
        119_653,
        "05b0d2ff0d1016b11596a9b912fb7500fc193df16bedf6d9d0d508d2519f29e5",
    ),
    RECEIPT_RELATIVE: (
        "100644",
        44_532,
        "2c02dbdbcfb4b84f399a71ae93a1dd42a3163b483c3285589dead2d84cc51398",
    ),
    "crates/pid-core/build_support.rs": (
        "100644",
        40_478,
        "49d0a5668c7f5d3e9f2c18b415e055f075bc9a6ba547517b52b3b4917f213169",
    ),
    "crates/pid-core/tests/software_identity_build.rs": (
        "100644",
        53_197,
        "dd2444b786ba873bc6ac06b4c9f65dcd84bcc5b2275d3220a27c79875ad7c34f",
    ),
    "justfile": (
        "100644",
        16_522,
        "3bf14879c131504386903f7d932364b035151677fbc8d992804272115511d49b",
    ),
    "scripts/README.md": (
        "100644",
        70_149,
        "9117706fec217a2aa0433dc3faa4827f90798f885396bf41564edbf0784008fa",
    ),
    CERTIFIED_CLAIM_CHECKER_RELATIVE: (
        "100644",
        67_251,
        "ad03d0eeeab6d9a9b10c73619d4c03311cdfe1183695609c3355ac636e6fe9a4",
    ),
    SELF_TEST_RELATIVE: (
        "100755",
        261_793,
        "a169c038c0735c1da9f10fd0a990cfe3be79c716a34fe9db834348bcd79e4ec5",
    ),
    WRAPPER_RELATIVE: (
        "100755",
        12_444,
        "41877ce3ca7c73d6972db757c936e1a14ca89d02104f542b30714126e2ccc29d",
    ),
}
EXPECTED_ALLOWLIST_SHA256 = (
    "35457cf852d16e9a11ec817f08532b2f32a3eb976370c39d29778af4aa7310fb"
)
EXPECTED_PINNED_CHANGED_PROJECTION_SHA256 = (
    "862dc18845d842d2d85eca2e3a2526d669db0ec455a8a545ffae541185b18c3b"
)
EXPECTED_PROTECTED_PROJECTION_SHA256 = (
    "38b56b93fc6f8c3873574237c7a23684d0481357f80d17e1c1e5474caa82962a"
)
EXPECTED_SCIENCE_SOURCE_PROJECTION = (
    35,
    "20f7213ce25e58384c023a04e30958e1fb17940d1ea7fc841cde248a1eaecb84",
)
EXPECTED_FORMAL_CLAIM_PROJECTION = (
    129,
    "9455571d5f4b8190149d642d8835557da4f82c0f1987c3475e0c271148a93f2f",
)
EXPECTED_CARGO_PROJECTION = (
    9,
    "b62fc18a2d46dc1675f71d70da1097231b0f58c0e4bf514239637bc822c47dd6",
)

HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
TIMEZONE = re.compile(r"(?:[+-](?:0[0-9]|1[0-3])[0-5][0-9]|[+-]1400)")
GIT_VERSION = re.compile(
    r"git version (?P<major>[0-9]+)\.(?P<minor>[0-9]+)(?:\.(?P<patch>[0-9]+))?"
    r"(?:[ .()0-9A-Za-z_+\-]*)"
)


class ProcessGroupState(Enum):
    ABSENT = "absent"
    PRESENT = "present"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class Entry:
    mode: str
    oid: str
    sha256: str


@dataclass(frozen=True)
class Snapshot:
    head: str
    entries: dict[str, Entry]
    filesystem_directories: tuple[str, ...]
    index_mode: int
    index_sha256: str
    index_size: int
    index_version: int
    tracked_modifications: tuple[str, ...]
    untracked: tuple[str, ...]
    ignored: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryContext:
    common_dir: str
    git_dir: str
    git_version: str
    index_path: str
    local_config_record_count: int
    local_config_sha256: str
    local_config_size: int
    object_pack_inventory_count: int
    object_pack_inventory_sha256: str


@dataclass(frozen=True)
class IndexObservation:
    body: bytes
    entry_count: int
    identity: tuple[int, ...]
    permissions: int
    version: int


@dataclass
class ResourceLedger:
    deadline: float
    application_visible_bytes: int = 0

    @classmethod
    def start(cls) -> ResourceLedger:
        return cls(deadline=time.monotonic() + VALIDATION_TIMEOUT_SECONDS)

    def check_deadline(self) -> None:
        require(
            time.monotonic() < self.deadline,
            f"validation exceeded the {VALIDATION_TIMEOUT_SECONDS}-second deadline",
        )
        # Outside child scopes this is a cooperative signal safe point. Inside
        # an owned child scope SIGALRM/SIGINT are kernel-blocked, and any callback
        # queued just before acquisition was already checked before Popen.
        raise_deferred_verifier_signal_if_safe(None)

    def remaining_seconds(self, maximum: float) -> float:
        self.check_deadline()
        remaining = self.deadline - time.monotonic()
        return min(maximum, max(remaining, 0.001))

    def ensure_capacity(self, amount: int) -> None:
        require(amount >= 0, "internal application-visible byte charge is negative")
        require(
            amount <= MAX_APPLICATION_VISIBLE_BYTES - self.application_visible_bytes,
            "validation exceeds the application-visible byte bound",
        )

    def charge(self, amount: int) -> None:
        self.ensure_capacity(amount)
        self.application_visible_bytes += amount
        self.check_deadline()


def resource_bounds_receipt() -> dict[str, Any]:
    return {
        "application_visible": {
            "maximum_bytes": MAX_APPLICATION_VISIBLE_BYTES,
            "scope": (
                "checker reads and captured subprocess I/O after exact-source entry"
            ),
        },
        "filesystem": {
            "component_bytes": MAX_COMPONENT_BYTES,
            "directory_entries": MAX_DIRECTORY_ENTRIES,
            "exact_source_bytes": MAX_EXACT_SOURCE_BYTES,
            "index_bytes": MAX_INDEX_BYTES,
            "path_bytes": MAX_PATH_BYTES,
            "snapshot_logical_bytes": MAX_WORKTREE_LOGICAL_BYTES,
            "tool_file_bytes": MAX_TOOL_FILE_BYTES,
            "worktree_file_bytes": MAX_WORKTREE_FILE_BYTES,
            "worktree_nodes": MAX_WORKTREE_NODES,
        },
        "git_objects": {
            "blob_logical_bytes_per_tree": MAX_BLOB_LOGICAL_BYTES,
            "blob_per_object_bytes": MAX_BLOB_OBJECT_BYTES,
            "commit_per_object_bytes": MAX_COMMIT_OBJECT_BYTES,
            "tree_depth": MAX_TREE_DEPTH,
            "tree_logical_bytes_per_traversal": MAX_TREE_RAW_BYTES,
            "tree_object_visits": MAX_TREE_OBJECT_VISITS,
            "tree_per_object_bytes": MAX_TREE_OBJECT_BYTES,
        },
        "processes": {
            "cat_file_header_bytes": MAX_CAT_FILE_HEADER_BYTES,
            "git_command_timeout_seconds": GIT_COMMAND_TIMEOUT_SECONDS,
            "git_config_stdout_bytes": MAX_GIT_CONFIG_STDOUT_BYTES,
            "git_inventory_stdout_bytes": MAX_GIT_INVENTORY_STDOUT_BYTES,
            "git_stderr_bytes": MAX_GIT_STDERR_BYTES,
            "git_stdin_bytes": MAX_GIT_STDIN_BYTES,
            "git_text_stdout_bytes": MAX_GIT_TEXT_STDOUT_BYTES,
            "child_preexec_unmasks_owned_signals": True,
            "external_waiter_premise": "no-external-or-native-direct-waiter",
            "owned_child_exception_signals": ["SIGALRM", "SIGINT"],
            "owned_child_signal_custody": (
                "nonraising-recorder-plus-pthread_sigmask-before-Popen-through-"
                "reap-ESRCH-local-close"
            ),
            "post_reap_process_group_signaling": False,
            "process_group_grace_seconds": PROCESS_GROUP_GRACE_SECONDS,
            "process_group_probe_interval_seconds": (
                PROCESS_GROUP_PROBE_INTERVAL_SECONDS
            ),
            "receipt_bytes": MAX_RECEIPT_BYTES,
            "python_thread_premise": (
                "main-thread-and-one-enumerated-Python-thread"
            ),
            "sigchld_child_ownership": (
                "explicit-SIG_DFL-reset-before-first-Popen-and-"
                "verified-before-each-Popen;requires-no-external-or-native-waiter"
            ),
            "validation_timeout_seconds": VALIDATION_TIMEOUT_SECONDS,
        },
        "scope": (
            "premise-explicit application-visible limits; not a hard RSS or "
            "child-process allocation bound"
        ),
    }


def nul_records(raw: bytes) -> Iterator[bytes]:
    offset = 0
    while offset < len(raw):
        end = raw.find(b"\0", offset)
        if end < 0:
            end = len(raw)
        record = raw[offset:end]
        if record:
            yield record
        offset = end + 1


def canonical_path(raw: bytes, *, label: str) -> str:
    require(
        0 < len(raw) <= MAX_PATH_BYTES,
        f"{label}: path exceeds the byte bound",
    )
    try:
        value = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise FollowupError(f"{label}: path is not UTF-8") from error
    path = PurePosixPath(value)
    require(
        bool(value)
        and not path.is_absolute()
        and value == path.as_posix()
        and all(part not in {"", ".", ".."} for part in path.parts)
        and all(len(part.encode("utf-8")) <= MAX_COMPONENT_BYTES for part in path.parts)
        and len(path.parts) <= MAX_TREE_DEPTH
        and "\n" not in value
        and "\r" not in value,
        f"{label}: path is not canonical: {value!r}",
    )
    return value


def canonical_inventory_path(raw: bytes, *, label: str) -> str:
    directory_marker = raw.endswith(b"/")
    normalized = raw[:-1] if directory_marker else raw
    value = canonical_path(normalized, label=label)
    return f"{value}/" if directory_marker else value


def descriptor_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return tuple(
        getattr(metadata, name)
        for name in (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_nlink",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
    )


def directory_descriptor_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
    )


def read_exact_bytes(
    file_descriptor: int,
    expected_size: int,
    resources: ResourceLedger,
    *,
    label: str,
) -> bytes:
    require(expected_size >= 0, f"{label}: declared byte size is negative")
    resources.ensure_capacity(expected_size + 1)
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    body = bytearray()
    remaining = expected_size
    while remaining:
        resources.check_deadline()
        requested = min(IO_CHUNK_BYTES, remaining)
        resources.ensure_capacity(requested)
        chunk = os.read(file_descriptor, requested)
        require(bool(chunk), f"{label}: file is shorter than its declared size")
        resources.charge(len(chunk))
        body.extend(chunk)
        remaining -= len(chunk)
    resources.ensure_capacity(1)
    extra = os.read(file_descriptor, 1)
    if extra:
        resources.charge(len(extra))
        raise FollowupError(f"{label}: file is longer than its declared size")
    return bytes(body)


def compare_exact_bytes(
    file_descriptor: int,
    expected: bytes,
    resources: ResourceLedger,
    *,
    label: str,
) -> None:
    resources.ensure_capacity(len(expected) + 1)
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    offset = 0
    while offset < len(expected):
        resources.check_deadline()
        requested = min(IO_CHUNK_BYTES, len(expected) - offset)
        resources.ensure_capacity(requested)
        chunk = os.read(
            file_descriptor,
            requested,
        )
        require(bool(chunk), f"{label}: second read is shorter than its declared size")
        resources.charge(len(chunk))
        require(
            chunk == expected[offset : offset + len(chunk)],
            f"{label}: bytes changed during descriptor observation",
        )
        offset += len(chunk)
    resources.ensure_capacity(1)
    extra = os.read(file_descriptor, 1)
    if extra:
        resources.charge(len(extra))
        raise FollowupError(f"{label}: second read is longer than its declared size")


def stable_file(
    root: Path,
    relative: str,
    resources: ResourceLedger,
    *,
    maximum_bytes: int = MAX_WORKTREE_FILE_BYTES,
    aggregate_remaining: int | None = None,
) -> tuple[str, bytes]:
    canonical_path(relative.encode("utf-8"), label="filesystem")
    require(
        all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")),
        "follow-up gate requires POSIX no-follow descriptors",
    )
    components = PurePosixPath(relative).parts
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | os.O_NONBLOCK
    )
    directory_descriptor: int | None = None
    next_descriptor: int | None = None
    leaf_descriptor: int | None = None
    primary_error: BaseException | None = None
    phase = "open"
    try:
        directory_descriptor = os.open(root, directory_flags)
        require(
            stat.S_ISDIR(os.fstat(directory_descriptor).st_mode),
            "repository root descriptor is not a directory",
        )
        for component in components[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=directory_descriptor,
            )
            require(
                stat.S_ISDIR(os.fstat(next_descriptor).st_mode),
                f"{relative!r}: parent descriptor is not a directory",
            )
            previous_descriptor = directory_descriptor
            directory_descriptor = next_descriptor
            next_descriptor = None
            close_error = close_descriptor_preserving_error(
                previous_descriptor,
                None,
                label="stable-file superseded directory descriptor",
            )
            if close_error is not None:
                raise FollowupError(
                    f"{relative!r}: cannot close a superseded directory descriptor"
                ) from close_error
        leaf_descriptor = os.open(
            components[-1],
            leaf_flags,
            dir_fd=directory_descriptor,
        )
        phase = "read"
        before = os.fstat(leaf_descriptor)
        require(
            stat.S_ISREG(before.st_mode),
            f"{relative!r}: path must be a regular non-symlink file",
        )
        require(
            before.st_nlink == 1,
            f"{relative!r}: hard-linked files are forbidden",
        )
        require(
            0 <= before.st_size <= maximum_bytes,
            f"{relative!r}: file exceeds the per-file byte bound",
        )
        if aggregate_remaining is not None:
            require(
                0 <= aggregate_remaining
                and before.st_size <= aggregate_remaining,
                "worktree snapshot exceeds the aggregate byte bound",
            )
        permissions = stat.S_IMODE(before.st_mode)
        require(
            permissions in {0o644, 0o755},
            f"{relative!r}: noncanonical permissions {permissions:#o}",
        )
        first = read_exact_bytes(
            leaf_descriptor,
            before.st_size,
            resources,
            label=relative,
        )
        middle = os.fstat(leaf_descriptor)
        compare_exact_bytes(
            leaf_descriptor,
            first,
            resources,
            label=relative,
        )
        after = os.fstat(leaf_descriptor)
        require(
            descriptor_identity(before) == descriptor_identity(middle)
            and descriptor_identity(middle) == descriptor_identity(after)
            and len(first) == before.st_size,
            f"{relative!r}: bytes changed during descriptor observation",
        )
        return ("100755" if permissions == 0o755 else "100644"), first
    except (OSError, ValueError) as error:
        if phase == "open":
            converted = FollowupError(
                f"{relative!r}: cannot open the no-follow descriptor path: {error}"
            )
        else:
            converted = FollowupError(
                f"{relative!r}: cannot read stable descriptor bytes: {error}"
            )
        primary_error = converted
        raise converted from error
    except BaseException as error:
        primary_error = error
        raise
    finally:
        cleanup_error = primary_error
        cleanup_error = close_descriptor_preserving_error(
            leaf_descriptor,
            cleanup_error,
            label="stable-file leaf descriptor",
        )
        cleanup_error = close_descriptor_preserving_error(
            next_descriptor,
            cleanup_error,
            label="stable-file pending directory descriptor",
        )
        cleanup_error = close_descriptor_preserving_error(
            directory_descriptor,
            cleanup_error,
            label="stable-file directory descriptor",
        )
        if primary_error is None and cleanup_error is not None:
            try:
                detail = str(cleanup_error)
            except BaseException:
                detail = "unprintable descriptor-close exception"
            raise FollowupError(
                f"{relative!r}: descriptor cleanup failed: {detail}"
            ) from cleanup_error


def blob_oid(raw: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {len(raw)}\0".encode("ascii"))
    digest.update(raw)
    return digest.hexdigest()


def object_oid(kind: str, raw: bytes) -> str:
    digest = hashlib.sha1()
    digest.update(f"{kind} {len(raw)}\0".encode("ascii"))
    digest.update(raw)
    return digest.hexdigest()


def isolated_environment() -> dict[str, str]:
    environment = {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_GRAFT_FILE": "/dev/null",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", ""),
    }
    if "SYSTEMROOT" in os.environ:
        environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return environment


git_candidate = shutil.which("git")
if git_candidate is None:
    raise FollowupError("Git executable is unavailable")
GIT = str(Path(git_candidate).resolve(strict=True))
python_candidate = sys.executable
if python_candidate is None:
    raise FollowupError("Python executable path is unavailable")
PYTHON_EXECUTABLE = str(Path(python_candidate).resolve(strict=True))


def git_command(arguments: tuple[str, ...]) -> list[str]:
    return [
        GIT,
        "-c",
        "advice.graftFileDeprecated=false",
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.ignoreCase=false",
        "-c",
        "core.precomposeUnicode=false",
        "-c",
        "core.untrackedCache=false",
        *arguments,
    ]


def process_group_state(group_id: int, *, label: str) -> ProcessGroupState:
    try:
        os.killpg(group_id, 0)
    except ProcessLookupError:
        return ProcessGroupState.ABSENT
    except PermissionError:
        # Darwin can transiently report EPERM after the session leader has been
        # reaped while the empty group is being dismantled.  EPERM is neither
        # presence nor absence evidence; only a later ESRCH proves absence.
        return ProcessGroupState.INDETERMINATE
    except OSError as error:
        raise FollowupError(
            f"{label} process-group survival check failed: {error}"
        ) from error
    return ProcessGroupState.PRESENT


def wait_for_process_group_absence(
    group_id: int, *, label: str, deadline: float
) -> ProcessGroupState:
    while True:
        state = process_group_state(group_id, label=label)
        if state is ProcessGroupState.ABSENT or time.monotonic() >= deadline:
            return state
        time.sleep(PROCESS_GROUP_PROBE_INTERVAL_SECONDS)


def require_process_group_absent_after_reap(
    process: subprocess.Popen[bytes],
    *,
    label: str,
    grace_seconds: float = PROCESS_GROUP_GRACE_SECONDS,
) -> None:
    require(grace_seconds >= 0, f"{label} process-group grace is negative")
    require(
        process.returncode is not None,
        f"{label} leader has not been reaped before the observe-only group check",
    )
    state = wait_for_process_group_absence(
        process.pid,
        label=label,
        deadline=time.monotonic() + grace_seconds,
    )
    require(
        state is ProcessGroupState.ABSENT,
        f"{label} cannot prove process-group absence after reaping its leader "
        f"(final state: {state.value}); no post-reap signal was sent",
    )


def signal_owned_process_group_before_reap(
    process: subprocess.Popen[bytes],
    selected_signal: signal.Signals,
    *,
    ownership: OwnedChildSignalMask,
    label: str,
) -> OSError | None:
    ownership.require_held(operation=label)
    require(
        process.returncode is None,
        f"{label} refused {selected_signal.name} after its local handle reaped the leader",
    )
    try:
        os.killpg(process.pid, selected_signal)
    except ProcessLookupError:
        return None
    except OSError as error:
        return error
    return None


def terminate_owned_process_group(
    process: subprocess.Popen[bytes],
    *,
    ownership: OwnedChildSignalMask,
    label: str,
    grace_seconds: float = PROCESS_GROUP_GRACE_SECONDS,
) -> None:
    ownership.require_held(operation=label)
    require(grace_seconds >= 0, f"{label} process-group grace is negative")
    observed_error: BaseException | None = None

    # The held signal-mask capability, dedicated single-thread runtime, explicit
    # SIGCHLD reset, and no-external-waiter premise establish local ownership.
    # returncode=None is only this handle's local pre-reap state; it is not a
    # general ownership token against an external waitpid()/wait() actor.
    # Signal before this handle reaps; afterwards observation is signal-free
    # because the numeric PGID may be reused.
    if process.returncode is None:
        try:
            signal_error = signal_owned_process_group_before_reap(
                process, signal.SIGTERM, ownership=ownership, label=label
            )
            if signal_error is not None:
                observed_error = retain_cleanup_exception(
                    observed_error,
                    signal_error,
                    label="owned process-group SIGTERM",
                )
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="owned process-group SIGTERM",
            )
        try:
            state = wait_for_process_group_absence(
                process.pid,
                label=label,
                deadline=time.monotonic() + grace_seconds,
            )
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="owned process-group pre-reap probe",
            )
            state = ProcessGroupState.INDETERMINATE
        if state is not ProcessGroupState.ABSENT:
            try:
                signal_error = signal_owned_process_group_before_reap(
                    process, signal.SIGKILL, ownership=ownership, label=label
                )
                if signal_error is not None:
                    observed_error = retain_cleanup_exception(
                        observed_error,
                        signal_error,
                        label="owned process-group SIGKILL",
                    )
            except BaseException as error:
                observed_error = retain_cleanup_exception(
                    observed_error,
                    error,
                    label="owned process-group SIGKILL",
                )

    # Two idempotent bounded attempts cover an exception raised after waitpid
    # side effects but before Popen publishes returncode.  No external waiter is
    # permitted; if both attempts leave returncode unknown, custody fails closed.
    for _attempt in range(2):
        if process.returncode is not None:
            break
        try:
            process.wait(timeout=max(grace_seconds, 0.001))
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="owned process-group leader reap",
            )
    if process.returncode is not None:
        try:
            require_process_group_absent_after_reap(
                process,
                label=label,
                grace_seconds=grace_seconds,
            )
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="owned process-group post-reap observation",
            )
    else:
        unreaped = FollowupError(f"{label} leader could not be proven reaped")
        observed_error = retain_cleanup_exception(
            observed_error,
            unreaped,
            label="owned process-group leader reap",
        )
    if process.returncode is None or observed_error is not None:
        # A fully reaped, absent group makes earlier transient signal/probe/wait
        # diagnostics non-authoritative.  Otherwise retain them in the cause.
        if process.returncode is not None:
            try:
                require_process_group_absent_after_reap(
                    process,
                    label=label,
                    grace_seconds=0.0,
                )
            except BaseException:
                pass
            else:
                return
        try:
            detail = str(observed_error)
        except BaseException:
            detail = "unprintable cleanup exception"
        raise FollowupError(
            f"{label} process-group cleanup failed: {detail}"
        ) from observed_error


def git_process(
    *arguments: str,
    resources: ResourceLedger,
    stdout_limit: int,
    stderr_limit: int,
    input_limit: int,
    timeout_seconds: int,
    cwd: Path = ROOT,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    require(stdout_limit >= 0, "Git stdout byte bound is negative")
    require(stderr_limit >= 0, "Git stderr byte bound is negative")
    require(input_limit >= 0, "Git input byte bound is negative")
    require(timeout_seconds > 0, "Git command deadline is not positive")
    supplied_input = input_bytes or b""
    require(
        len(supplied_input) <= input_limit,
        "Git input exceeds the byte bound",
    )
    resources.ensure_capacity(len(supplied_input))
    command = git_command(arguments)
    label = f"Git {' '.join(arguments)}"
    process: subprocess.Popen[bytes] | None = None
    stdout = bytearray()
    stderr = bytearray()
    selector: selectors.BaseSelector | None = None
    local_deadline = min(
        resources.deadline,
        time.monotonic() + timeout_seconds,
    )
    input_offset = 0
    returncode: int | None = None
    primary_error: BaseException | None = None
    ownership = OwnedChildSignalMask.acquire(label=f"{label} child lifecycle")
    try:
        raise_deferred_verifier_signal_if_safe(None)
        require_sigchld_default()
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=isolated_environment(),
                stdin=(
                    subprocess.PIPE
                    if input_bytes is not None
                    else subprocess.DEVNULL
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                preexec_fn=child_unblock_owned_exception_signals,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise FollowupError(f"{label} could not start: {error}") from error
        require(
            process.stdout is not None and process.stderr is not None,
            f"{label} has incomplete process pipes",
        )
        selector = selectors.DefaultSelector()
        os.set_blocking(process.stdout.fileno(), False)
        os.set_blocking(process.stderr.fileno(), False)
        selector.register(process.stdout.fileno(), selectors.EVENT_READ, "stdout")
        selector.register(process.stderr.fileno(), selectors.EVENT_READ, "stderr")
        if process.stdin is not None:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin.fileno(), selectors.EVENT_WRITE, "stdin")

        while selector.get_map():
            resources.check_deadline()
            remaining_time = local_deadline - time.monotonic()
            if remaining_time <= 0:
                raise FollowupError(
                    f"{label} exceeded {timeout_seconds} seconds"
                )
            events = selector.select(remaining_time)
            if not events:
                raise FollowupError(
                    f"{label} exceeded {timeout_seconds} seconds"
                )
            for key, _mask in events:
                descriptor = key.fd
                stream = key.data
                if stream == "stdin":
                    if input_offset >= len(supplied_input):
                        selector.unregister(descriptor)
                        if process.stdin is not None:
                            process.stdin.close()
                        continue
                    try:
                        count = os.write(
                            descriptor,
                            supplied_input[
                                input_offset : input_offset + IO_CHUNK_BYTES
                            ],
                        )
                    except BrokenPipeError:
                        selector.unregister(descriptor)
                        if process.stdin is not None:
                            process.stdin.close()
                        continue
                    require(count > 0, f"{label} accepted no input bytes")
                    resources.charge(count)
                    input_offset += count
                    if input_offset == len(supplied_input):
                        selector.unregister(descriptor)
                        if process.stdin is not None:
                            process.stdin.close()
                    continue

                target = stdout if stream == "stdout" else stderr
                limit = stdout_limit if stream == "stdout" else stderr_limit
                remaining_output = limit - len(target)
                requested = min(IO_CHUNK_BYTES, max(1, remaining_output + 1))
                resources.ensure_capacity(requested)
                chunk = os.read(
                    descriptor,
                    requested,
                )
                if not chunk:
                    selector.unregister(descriptor)
                    if stream == "stdout":
                        process.stdout.close()
                    else:
                        process.stderr.close()
                    continue
                require(
                    len(chunk) <= remaining_output,
                    f"{label} {stream} exceeds the byte bound",
                )
                resources.charge(len(chunk))
                target.extend(chunk)

        remaining_time = local_deadline - time.monotonic()
        if remaining_time <= 0:
            raise FollowupError(f"{label} exceeded {timeout_seconds} seconds")
        try:
            returncode = process.wait(timeout=remaining_time)
        except subprocess.TimeoutExpired as error:
            raise FollowupError(
                f"{label} exceeded {timeout_seconds} seconds"
            ) from error
        require_process_group_absent_after_reap(process, label=label)
    except BaseException as error:
        primary_error = error
        if process is not None:
            try:
                terminate_owned_process_group(
                    process,
                    ownership=ownership,
                    label=label,
                )
            except BaseException as cleanup_error:
                add_secondary_exception_note(
                    error,
                    label,
                    cleanup_error,
                )
        raise
    finally:
        local_close_error: BaseException | None = None
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                local_close_error = error
        if process is not None:
            for _pipe_name, pipe in (
                ("stdin", process.stdin),
                ("stdout", process.stdout),
                ("stderr", process.stderr),
            ):
                if pipe is None or pipe.closed:
                    continue
                try:
                    pipe.close()
                except BaseException as error:
                    if local_close_error is None:
                        local_close_error = error
                    else:
                        add_secondary_exception_note(
                            local_close_error,
                            label,
                            error,
                        )
        effective_error = primary_error or local_close_error
        if primary_error is not None and local_close_error is not None:
            add_secondary_exception_note(
                primary_error,
                label,
                local_close_error,
            )
        restore_signal_mask_preserving_error(
            ownership,
            effective_error,
            label=label,
        )
        if primary_error is None and local_close_error is not None:
            try:
                detail = str(local_close_error)
            except BaseException:
                detail = "unprintable cleanup exception"
            raise FollowupError(
                f"{label} local-resource closure failed: {detail}"
            ) from local_close_error

    require(process is not None, f"{label} lost its process handle")
    require(returncode is not None, f"{label} lost its process return code")
    completed = subprocess.CompletedProcess(
        command,
        returncode,
        bytes(stdout),
        bytes(stderr),
    )
    if completed.returncode < 0:
        raise FollowupError(
            f"{label} terminated by signal {-completed.returncode}"
        )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise FollowupError(
            f"{label} failed with {completed.returncode}: {detail}"
        )
    return completed


def git_text(
    *arguments: str,
    resources: ResourceLedger,
    cwd: Path = ROOT,
    stdout_limit: int = MAX_GIT_TEXT_STDOUT_BYTES,
) -> str:
    raw = git_process(
        *arguments,
        resources=resources,
        stdout_limit=stdout_limit,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
        cwd=cwd,
    ).stdout
    try:
        value = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise FollowupError(f"Git {' '.join(arguments)} output is not UTF-8") from error
    return value.removesuffix("\n")


@dataclass(frozen=True)
class GitObjectInfo:
    oid: str
    kind: str
    size: int


class GitCatFileSession:
    __slots__ = (
        "resources",
        "label",
        "deadline",
        "process",
        "selector",
        "stdout_buffer",
        "stderr",
        "input_bytes",
        "finished",
        "ownership",
    )

    def __init__(self, resources: ResourceLedger, *, cwd: Path = ROOT) -> None:
        self.resources = resources
        self.label = "Git cat-file --batch-command"
        self.deadline = min(
            resources.deadline,
            time.monotonic() + GIT_COMMAND_TIMEOUT_SECONDS,
        )
        self.process: subprocess.Popen[bytes] | None = None
        self.selector: selectors.BaseSelector | None = None
        self.stdout_buffer = bytearray()
        self.stderr = bytearray()
        self.input_bytes = 0
        self.finished = False
        self.ownership: OwnedChildSignalMask | None = None
        process: subprocess.Popen[bytes] | None = None
        selector: selectors.BaseSelector | None = None
        ownership = OwnedChildSignalMask.acquire(
            label=f"{self.label} child lifecycle"
        )
        try:
            self.ownership = ownership
            raise_deferred_verifier_signal_if_safe(None)
            require_sigchld_default()
            try:
                process = subprocess.Popen(
                    git_command(("cat-file", "--batch-command")),
                    cwd=cwd,
                    env=isolated_environment(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                    preexec_fn=child_unblock_owned_exception_signals,
                )
            except (OSError, subprocess.SubprocessError) as error:
                raise FollowupError(
                    f"{self.label} could not start: {error}"
                ) from error
            self.process = process
            require(
                process.stdin is not None
                and process.stdout is not None
                and process.stderr is not None,
                f"{self.label} has incomplete process pipes",
            )
            try:
                selector = selectors.DefaultSelector()
            except BaseException as error:
                raise FollowupError(
                    f"{self.label} selector setup failed: {error}"
                ) from error
            self.selector = selector
            for pipe in (process.stdin, process.stdout, process.stderr):
                os.set_blocking(pipe.fileno(), False)
            selector.register(
                process.stdout.fileno(), selectors.EVENT_READ, "stdout"
            )
            selector.register(
                process.stderr.fileno(), selectors.EVENT_READ, "stderr"
            )
        except BaseException as error:
            if process is not None:
                try:
                    terminate_owned_process_group(
                        process,
                        ownership=ownership,
                        label=self.label,
                    )
                except BaseException as cleanup_error:
                    add_secondary_exception_note(
                        error,
                        "cat-file constructor process cleanup also failed",
                        cleanup_error,
                    )
            self._close_local_resources(
                primary_error=error,
                authoritative_ownership=ownership,
                authoritative_process=process,
                authoritative_selector=selector,
            )
            raise

    def __enter__(self) -> GitCatFileSession:
        try:
            require(self.ownership is not None, f"{self.label} lost its ownership")
            self.ownership.require_held(operation=self.label)
            require(not self.finished, f"{self.label} entered after closure")
            return self
        except BaseException as error:
            # Python does not call __exit__ when __enter__ raises.  Close the
            # already-live child/session here and retain the initiating failure.
            try:
                self.abort()
            except BaseException as cleanup_error:
                add_secondary_exception_note(
                    error,
                    "cat-file enter cleanup also failed",
                    cleanup_error,
                )
            raise

    def __exit__(self, kind: Any, value: Any, traceback: Any) -> None:
        if kind is not None:
            try:
                self.abort()
            except BaseException as cleanup_error:
                if isinstance(value, BaseException):
                    add_secondary_exception_note(
                        value,
                        "cat-file cleanup also failed",
                        cleanup_error,
                    )
                else:
                    raise
            return
        try:
            self.finish()
        except BaseException as finish_error:
            try:
                self.abort()
            except BaseException as cleanup_error:
                # Keep the initiating finish failure primary while retaining
                # cleanup failure as an explicit note.  abort() uses the held
                # ownership capability and remains observe-only after reap.
                add_secondary_exception_note(
                    finish_error,
                    "cat-file cleanup also failed",
                    cleanup_error,
                )
            raise

    def _close_local_resources(
        self,
        *,
        primary_error: BaseException | None = None,
        authoritative_ownership: OwnedChildSignalMask | None = None,
        authoritative_process: subprocess.Popen[bytes] | None = None,
        authoritative_selector: selectors.BaseSelector | None = None,
    ) -> None:
        ownership = (
            authoritative_ownership
            if authoritative_ownership is not None
            else self.ownership
        )
        process = (
            authoritative_process
            if authoritative_process is not None
            else self.process
        )
        selector = (
            authoritative_selector
            if authoritative_selector is not None
            else self.selector
        )
        local_close_error: BaseException | None = None
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                # Store the raw exception without formatting it.  A hostile or
                # allocation-failing __str__ must not skip pipe/mask cleanup.
                local_close_error = error
        if process is not None:
            for _pipe_name, pipe in (
                ("stdin", process.stdin),
                ("stdout", process.stdout),
                ("stderr", process.stderr),
            ):
                if pipe is None or pipe.closed:
                    continue
                try:
                    pipe.close()
                except BaseException as error:
                    if local_close_error is None:
                        local_close_error = error
                    else:
                        add_secondary_exception_note(
                            local_close_error,
                            "cat-file additional pipe closure failure",
                            error,
                        )
        self.finished = True
        effective_error = primary_error or local_close_error
        if primary_error is not None and local_close_error is not None:
            add_secondary_exception_note(
                primary_error,
                f"{self.label} local-resource cleanup also failed",
                local_close_error,
            )
        if ownership is not None and ownership.held:
            restore_signal_mask_preserving_error(
                ownership,
                effective_error,
                label="cat-file signal-mask restoration also failed",
            )
        if primary_error is None and local_close_error is not None:
            try:
                detail = str(local_close_error)
            except BaseException:
                detail = "unprintable cleanup exception"
            raise FollowupError(
                f"{self.label} local-resource closure failed: {detail}"
            ) from local_close_error

    def _remaining_seconds(self) -> float:
        self.resources.check_deadline()
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise FollowupError(
                f"{self.label} exceeded {GIT_COMMAND_TIMEOUT_SECONDS} seconds"
            )
        return remaining

    def _read_stderr(self, descriptor: int) -> None:
        remaining = MAX_GIT_STDERR_BYTES - len(self.stderr)
        requested = min(IO_CHUNK_BYTES, max(1, remaining + 1))
        self.resources.ensure_capacity(requested)
        chunk = os.read(descriptor, requested)
        if not chunk:
            try:
                self.selector.unregister(descriptor)
            except KeyError:
                pass
            if self.process.stderr is not None and not self.process.stderr.closed:
                self.process.stderr.close()
            return
        require(
            len(chunk) <= remaining,
            f"{self.label} stderr exceeds the byte bound",
        )
        self.resources.charge(len(chunk))
        self.stderr.extend(chunk)

    def _pump_stdout(self, maximum_read: int) -> None:
        require(maximum_read > 0, "internal cat-file read bound is not positive")
        while True:
            events = self.selector.select(self._remaining_seconds())
            if not events:
                raise FollowupError(
                    f"{self.label} exceeded {GIT_COMMAND_TIMEOUT_SECONDS} seconds"
                )
            stdout_seen = False
            for key, _mask in events:
                if key.data == "stderr":
                    self._read_stderr(key.fd)
                    continue
                if key.data != "stdout":
                    continue
                requested = min(IO_CHUNK_BYTES, maximum_read)
                self.resources.ensure_capacity(requested)
                chunk = os.read(key.fd, requested)
                if not chunk:
                    try:
                        self.selector.unregister(key.fd)
                    except KeyError:
                        pass
                    if self.process.stdout is not None and not self.process.stdout.closed:
                        self.process.stdout.close()
                    detail = self.stderr.decode("utf-8", errors="replace").strip()
                    raise FollowupError(
                        f"{self.label} ended before its framed output completed: {detail}"
                    )
                self.resources.charge(len(chunk))
                self.stdout_buffer.extend(chunk)
                stdout_seen = True
            if stdout_seen:
                return

    def _send(self, command: bytes) -> None:
        require(
            command.endswith(b"\n")
            and len(command) <= MAX_CAT_FILE_HEADER_BYTES
            and b"\0" not in command,
            "internal cat-file command is malformed",
        )
        require(
            len(command) <= MAX_GIT_STDIN_BYTES - self.input_bytes,
            f"{self.label} stdin exceeds the byte bound",
        )
        self.resources.ensure_capacity(len(command))
        if self.process.stdin is None or self.process.stdin.closed:
            raise FollowupError(f"{self.label} input pipe is closed")
        descriptor = self.process.stdin.fileno()
        self.selector.register(descriptor, selectors.EVENT_WRITE, "stdin")
        offset = 0
        try:
            while offset < len(command):
                events = self.selector.select(self._remaining_seconds())
                if not events:
                    raise FollowupError(
                        f"{self.label} exceeded {GIT_COMMAND_TIMEOUT_SECONDS} seconds"
                    )
                for key, _mask in events:
                    if key.data == "stderr":
                        self._read_stderr(key.fd)
                    elif key.data == "stdin":
                        try:
                            count = os.write(key.fd, command[offset:])
                        except BrokenPipeError as error:
                            detail = self.stderr.decode(
                                "utf-8", errors="replace"
                            ).strip()
                            raise FollowupError(
                                f"{self.label} rejected its command stream: {detail}"
                            ) from error
                        require(count > 0, f"{self.label} accepted no command bytes")
                        self.resources.charge(count)
                        self.input_bytes += count
                        offset += count
        finally:
            try:
                self.selector.unregister(descriptor)
            except KeyError:
                pass

    def _readline(self) -> bytes:
        while True:
            newline = self.stdout_buffer.find(b"\n")
            if newline >= 0:
                require(
                    newline < MAX_CAT_FILE_HEADER_BYTES,
                    f"{self.label} header exceeds the byte bound",
                )
                line = bytes(self.stdout_buffer[:newline])
                del self.stdout_buffer[: newline + 1]
                return line
            require(
                len(self.stdout_buffer) < MAX_CAT_FILE_HEADER_BYTES,
                f"{self.label} header exceeds the byte bound",
            )
            self._pump_stdout(MAX_CAT_FILE_HEADER_BYTES - len(self.stdout_buffer))

    def _take(self, count: int) -> bytes:
        require(count >= 0, "internal cat-file byte count is negative")
        while len(self.stdout_buffer) < count:
            self._pump_stdout(min(IO_CHUNK_BYTES, count - len(self.stdout_buffer)))
        result = bytes(self.stdout_buffer[:count])
        del self.stdout_buffer[:count]
        return result

    def _parse_header(self, line: bytes, expected_oid: str) -> GitObjectInfo:
        fields = line.split(b" ")
        require(
            len(fields) == 3,
            f"Git object {expected_oid} has a malformed cat-file header",
        )
        oid_raw, kind_raw, size_raw = fields
        try:
            oid = oid_raw.decode("ascii", errors="strict")
            kind = kind_raw.decode("ascii", errors="strict")
            size_text = size_raw.decode("ascii", errors="strict")
            size = int(size_text)
        except (UnicodeDecodeError, ValueError) as error:
            raise FollowupError(
                f"Git object {expected_oid} has a malformed cat-file header"
            ) from error
        require(
            oid == expected_oid
            and HEX40.fullmatch(oid) is not None
            and kind in {"blob", "commit", "tree"}
            and size >= 0
            and size_text == str(size),
            f"Git object {expected_oid} has a malformed cat-file header",
        )
        return GitObjectInfo(oid=oid, kind=kind, size=size)

    def info(self, object_id: str) -> GitObjectInfo:
        require(HEX40.fullmatch(object_id) is not None, "Git object id is malformed")
        self._send(f"info {object_id}\n".encode("ascii"))
        return self._parse_header(self._readline(), object_id)

    def _begin_contents(self, expected: GitObjectInfo) -> None:
        self.resources.ensure_capacity(
            MAX_CAT_FILE_HEADER_BYTES + expected.size + 1
        )
        self._send(f"contents {expected.oid}\n".encode("ascii"))
        actual = self._parse_header(self._readline(), expected.oid)
        require(
            actual == expected,
            f"Git object {expected.oid} metadata changed between info and contents",
        )

    def contents_bytes(self, expected: GitObjectInfo) -> bytes:
        self._begin_contents(expected)
        body = bytearray()
        remaining = expected.size
        while remaining:
            chunk = self._take(min(IO_CHUNK_BYTES, remaining))
            body.extend(chunk)
            remaining -= len(chunk)
        require(
            self._take(1) == b"\n",
            f"Git {expected.kind} object framing is inconsistent",
        )
        raw = bytes(body)
        require(
            object_oid(expected.kind, raw) == expected.oid,
            f"Git {expected.kind} object hash is inconsistent",
        )
        return raw

    def contents_blob_sha256(self, expected: GitObjectInfo) -> str:
        require(expected.kind == "blob", "internal Git object kind is not a blob")
        self._begin_contents(expected)
        sha1 = hashlib.sha1()
        sha1.update(f"blob {expected.size}\0".encode("ascii"))
        sha256 = hashlib.sha256()
        remaining = expected.size
        while remaining:
            chunk = self._take(min(IO_CHUNK_BYTES, remaining))
            sha1.update(chunk)
            sha256.update(chunk)
            remaining -= len(chunk)
        require(self._take(1) == b"\n", "Git blob object framing is inconsistent")
        require(sha1.hexdigest() == expected.oid, "Git blob object hash mismatch")
        return sha256.hexdigest()

    def finish(self) -> None:
        if self.finished:
            return
        self.ownership.require_held(operation=self.label)
        require(self.process is not None, f"{self.label} lost its process handle")
        require(self.selector is not None, f"{self.label} lost its selector")
        require(not self.stdout_buffer, f"{self.label} retained trailing output")
        if self.process.stdin is not None and not self.process.stdin.closed:
            self.process.stdin.close()
        stdout_extra = bytearray()
        while self.selector.get_map():
            events = self.selector.select(self._remaining_seconds())
            if not events:
                raise FollowupError(
                    f"{self.label} exceeded {GIT_COMMAND_TIMEOUT_SECONDS} seconds"
                )
            for key, _mask in events:
                if key.data == "stderr":
                    self._read_stderr(key.fd)
                    continue
                self.resources.ensure_capacity(1)
                chunk = os.read(key.fd, 1)
                if chunk:
                    self.resources.charge(len(chunk))
                    stdout_extra.extend(chunk)
                    raise FollowupError(f"{self.label} emitted trailing output")
                try:
                    self.selector.unregister(key.fd)
                except KeyError:
                    pass
                if self.process.stdout is not None and not self.process.stdout.closed:
                    self.process.stdout.close()
        try:
            returncode = self.process.wait(timeout=self._remaining_seconds())
        except subprocess.TimeoutExpired as error:
            raise FollowupError(
                f"{self.label} exceeded {GIT_COMMAND_TIMEOUT_SECONDS} seconds"
            ) from error
        require_process_group_absent_after_reap(self.process, label=self.label)
        if returncode < 0:
            raise FollowupError(
                f"{self.label} terminated by signal {-returncode}"
            )
        if returncode != 0:
            detail = self.stderr.decode("utf-8", errors="replace").strip()
            raise FollowupError(
                f"{self.label} failed with {returncode}: {detail}"
            )
        self._close_local_resources()

    def abort(self) -> None:
        if self.finished:
            if self.ownership.held:
                self._close_local_resources()
            return
        try:
            require(self.process is not None, f"{self.label} lost its process handle")
            terminate_owned_process_group(
                self.process,
                ownership=self.ownership,
                label=self.label,
            )
        except BaseException as error:
            self._close_local_resources(primary_error=error)
            raise
        self._close_local_resources()


def exact_object_bytes(
    object_id: str,
    expected_kind: str,
    resources: ResourceLedger,
) -> bytes:
    require(HEX40.fullmatch(object_id) is not None, "Git object id is malformed")
    require(
        expected_kind in {"commit", "tree"},
        "internal Git object kind is unsupported",
    )
    maximum = (
        MAX_COMMIT_OBJECT_BYTES if expected_kind == "commit" else MAX_TREE_OBJECT_BYTES
    )
    with GitCatFileSession(resources) as objects:
        info = objects.info(object_id)
        require(
            info.kind == expected_kind,
            f"Git object {object_id} is not an exact {expected_kind}",
        )
        require(
            info.size <= maximum,
            f"Git {expected_kind} object exceeds the per-object byte bound",
        )
        return objects.contents_bytes(info)


def observe_object_pack_inventory(
    common_dir: Path,
    resources: ResourceLedger,
) -> tuple[int, str]:
    require(
        os.stat in os.supports_dir_fd
        and os.open in os.supports_dir_fd
        and os.scandir in os.supports_fd
        and all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")),
        "follow-up gate requires POSIX descriptor-relative pack inventory custody",
    )
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    common_descriptor: int | None = None
    objects_descriptor: int | None = None
    pack_descriptor: int | None = None
    primary_error: BaseException | None = None
    try:
        common_descriptor = os.open(common_dir, directory_flags)
        objects_descriptor = os.open(
            "objects", directory_flags, dir_fd=common_descriptor
        )
        pack_descriptor = os.open(
            "pack", directory_flags, dir_fd=objects_descriptor
        )
        before = descriptor_identity(os.fstat(pack_descriptor))
        records: list[list[Any]] = []
        seen: set[str] = set()
        with os.scandir(pack_descriptor) as iterator:
            for entry in iterator:
                resources.check_deadline()
                require(
                    len(records) < MAX_DIRECTORY_ENTRIES,
                    "Git object pack directory exceeds the entry bound",
                )
                name = entry.name
                try:
                    name_raw = name.encode("utf-8", errors="strict")
                except UnicodeEncodeError as error:
                    raise FollowupError(
                        "Git object pack name is not strict UTF-8"
                    ) from error
                resources.charge(len(name_raw))
                canonical_path(name_raw, label="Git object pack component")
                require(name not in seen, "Git object pack names are duplicated")
                seen.add(name)
                require(
                    not name.endswith(".promisor"),
                    f"Git promisor marker is forbidden: {name}",
                )
                metadata = os.stat(
                    name, dir_fd=pack_descriptor, follow_symlinks=False
                )
                require(
                    stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1,
                    f"Git object pack entry has unsupported topology: {name}",
                )
                records.append([name, *descriptor_identity(metadata)])
        require(
            descriptor_identity(os.fstat(pack_descriptor)) == before,
            "Git object pack directory changed during inventory",
        )
    except OSError as error:
        converted = FollowupError(
            f"cannot observe the no-follow Git object pack inventory: {error}"
        )
        primary_error = converted
        raise converted from error
    except BaseException as error:
        primary_error = error
        raise
    finally:
        cleanup_error = primary_error
        cleanup_error = close_descriptor_preserving_error(
            pack_descriptor,
            cleanup_error,
            label="Git pack inventory pack directory",
        )
        cleanup_error = close_descriptor_preserving_error(
            objects_descriptor,
            cleanup_error,
            label="Git pack inventory objects directory",
        )
        cleanup_error = close_descriptor_preserving_error(
            common_descriptor,
            cleanup_error,
            label="Git pack inventory common directory",
        )
        if primary_error is None and cleanup_error is not None:
            raise FollowupError(
                "Git object pack inventory descriptor cleanup failed"
            ) from cleanup_error
    records.sort(key=lambda record: record[0])
    encoded = json.dumps(records, separators=(",", ":")).encode("utf-8")
    resources.charge(len(encoded))
    return len(records), hashlib.sha256(encoded).hexdigest()


def validate_repository_context(resources: ResourceLedger) -> RepositoryContext:
    require(not Path(__file__).is_symlink(), "follow-up checker must not be a symlink")
    git_version = git_text("--version", resources=resources)
    version_match = GIT_VERSION.fullmatch(git_version)
    require(version_match is not None, "Git version output is malformed")
    if version_match is None:
        raise FollowupError("Git version output is malformed")
    version = (
        int(version_match.group("major")),
        int(version_match.group("minor")),
        int(version_match.group("patch") or "0"),
    )
    require(version >= (2, 45, 0), "follow-up gate requires Git 2.45 or newer")
    reported = Path(
        git_text("rev-parse", "--show-toplevel", resources=resources)
    ).resolve(strict=True)
    require(reported == ROOT, "Git worktree root differs from checker root")
    require(
        git_text(
            "rev-parse", "--show-object-format=storage", resources=resources
        )
        == "sha1",
        "follow-up gate requires SHA-1 Git object storage",
    )
    require(
        git_text("rev-parse", "--is-shallow-repository", resources=resources)
        == "false",
        "follow-up gate requires a non-shallow repository",
    )
    git_dir = Path(git_text("rev-parse", "--git-dir", resources=resources))
    common_dir = Path(
        git_text("rev-parse", "--git-common-dir", resources=resources)
    )
    if not git_dir.is_absolute():
        git_dir = ROOT / git_dir
    if not common_dir.is_absolute():
        common_dir = ROOT / common_dir
    git_dir = git_dir.resolve(strict=True)
    common_dir = common_dir.resolve(strict=True)
    require(git_dir.is_dir() and common_dir.is_dir(), "Git metadata roots are invalid")
    pack_inventory_count, pack_inventory_sha256 = observe_object_pack_inventory(
        common_dir, resources
    )
    index_raw = Path(
        git_text("rev-parse", "--git-path", "index", resources=resources)
    )
    if not index_raw.is_absolute():
        index_raw = ROOT / index_raw
    index_parent = index_raw.parent.resolve(strict=True)
    index_path = index_parent / index_raw.name
    require(
        index_path == git_dir / "index",
        "Git index path differs from the private worktree index",
    )
    for path, label in (
        (common_dir / "info/grafts", "info/grafts"),
        (common_dir / "objects/info/alternates", "objects/info/alternates"),
        (common_dir / "info/attributes", "info/attributes"),
        (git_dir / "config.worktree", "config.worktree"),
        (git_dir / "index.lock", "index.lock"),
    ):
        require(
            not path.exists() and not path.is_symlink(),
            f"Git overlay file is forbidden: {label}",
        )
    replacement = git_process(
        "for-each-ref",
        "--count=1",
        "--format=%(refname)",
        "refs/replace",
        resources=resources,
        stdout_limit=MAX_GIT_TEXT_STDOUT_BYTES,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    require(not replacement, "Git replacement references are forbidden")
    config = git_process(
        "config",
        "--no-includes",
        "--local",
        "--null",
        "--list",
        resources=resources,
        stdout_limit=MAX_GIT_CONFIG_STDOUT_BYTES,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    forbidden_prefixes = (
        "credential.",
        "filter.",
        "http.",
        "include.",
        "includeif.",
        "url.",
    )
    forbidden_keys = {
        "core.attributesfile",
        "core.fsmonitor",
        "core.hookspath",
        "core.sshcommand",
        "core.sparsecheckout",
        "core.sparsecheckoutcone",
        "core.splitindex",
        "core.untrackedcache",
        "core.worktree",
        "extensions.objectformat",
        "extensions.partialclone",
        "extensions.worktreeconfig",
    }
    seen_keys: set[str] = set()
    for record in nul_records(config):
        key_raw, separator, _value = record.partition(b"\n")
        require(separator == b"\n", "local Git configuration record is malformed")
        try:
            key = key_raw.decode("utf-8", errors="strict").lower()
        except UnicodeDecodeError as error:
            raise FollowupError("local Git configuration key is not UTF-8") from error
        require(
            bool(key) and key not in seen_keys,
            "local Git configuration key is duplicated",
        )
        seen_keys.add(key)
        remote_promisor_key = key.startswith("remote.") and (
            key.endswith(".promisor") or key.endswith(".partialclonefilter")
        )
        require(
            key not in forbidden_keys
            and not any(key.startswith(prefix) for prefix in forbidden_prefixes)
            and not remote_promisor_key,
            f"local Git configuration key is forbidden: {key}",
        )
    return RepositoryContext(
        common_dir=str(common_dir),
        git_dir=str(git_dir),
        git_version=git_version,
        index_path=str(index_path),
        local_config_record_count=len(seen_keys),
        local_config_sha256=hashlib.sha256(config).hexdigest(),
        local_config_size=len(config),
        object_pack_inventory_count=pack_inventory_count,
        object_pack_inventory_sha256=pack_inventory_sha256,
    )


def parse_tree(revision: str, resources: ResourceLedger) -> dict[str, Entry]:
    entries: dict[str, tuple[str, str]] = {}
    tree_object_visits = 0
    tree_raw_bytes = 0
    tree_cache: dict[str, tuple[GitObjectInfo, bytes]] = {}

    with GitCatFileSession(resources) as objects:

        def visit(
            tree_id: str,
            prefix: bytes,
            ancestry: frozenset[str],
            depth: int,
        ) -> int:
            nonlocal tree_object_visits, tree_raw_bytes
            require(depth <= MAX_TREE_DEPTH, "Git tree graph exceeds the depth bound")
            require(tree_id not in ancestry, "Git tree graph contains a cycle")
            tree_object_visits += 1
            require(
                tree_object_visits <= MAX_TREE_OBJECT_VISITS,
                "Git tree graph exceeds the object-count bound",
            )
            cached = tree_cache.get(tree_id)
            info = cached[0] if cached is not None else objects.info(tree_id)
            require(info.kind == "tree", f"Git object {tree_id} is not an exact tree")
            require(
                info.size <= MAX_TREE_OBJECT_BYTES,
                "Git tree object exceeds the per-object byte bound",
            )
            require(
                info.size <= MAX_TREE_RAW_BYTES - tree_raw_bytes,
                "Git tree graph exceeds the aggregate byte bound",
            )
            tree_raw_bytes += info.size
            if cached is None:
                raw = objects.contents_bytes(info)
                tree_cache[tree_id] = (info, raw)
            else:
                raw = cached[1]
            offset = 0
            descendant_blobs = 0
            previous_sort_key: bytes | None = None
            component_names: set[bytes] = set()
            while offset < len(raw):
                space = raw.find(b" ", offset)
                require(space > offset, "Git tree mode record is malformed")
                nul = raw.find(b"\0", space + 1)
                require(nul > space + 1, "Git tree name record is malformed")
                object_end = nul + 21
                require(object_end <= len(raw), "Git tree object id is truncated")
                mode_raw = raw[offset:space]
                name_raw = raw[space + 1 : nul]
                object_id = raw[nul + 1 : object_end].hex()
                require(
                    name_raw not in component_names
                    and b"/" not in name_raw
                    and name_raw not in {b".", b".."},
                    "Git tree component is duplicate or noncanonical",
                )
                component_names.add(name_raw)
                is_tree = mode_raw == b"40000"
                sort_key = name_raw + (b"/" if is_tree else b"")
                require(
                    previous_sort_key is None or previous_sort_key < sort_key,
                    "Git tree entries are not in canonical order",
                )
                previous_sort_key = sort_key
                path_raw = prefix + name_raw
                path = canonical_path(path_raw, label="tree")
                require(
                    HEX40.fullmatch(object_id) is not None,
                    f"{path!r}: malformed tree object id",
                )
                if is_tree:
                    child_blobs = visit(
                        object_id,
                        path_raw + b"/",
                        ancestry | frozenset({tree_id}),
                        depth + 1,
                    )
                    require(
                        child_blobs > 0,
                        f"{path!r}: empty tree paths are forbidden",
                    )
                    descendant_blobs += child_blobs
                else:
                    try:
                        mode = mode_raw.decode("ascii", errors="strict")
                    except UnicodeDecodeError as error:
                        raise FollowupError(
                            f"{path!r}: tree mode is not ASCII"
                        ) from error
                    require(
                        mode in {"100644", "100755"},
                        f"{path!r}: unsupported tree entry",
                    )
                    require(
                        len(entries) < CANDIDATE_PATH_COUNT,
                        "Git tree exceeds the candidate path-count bound",
                    )
                    require(path not in entries, f"duplicate tree path: {path}")
                    entries[path] = (mode, object_id)
                    descendant_blobs += 1
                offset = object_end
            require(offset == len(raw), "Git tree object has trailing bytes")
            return descendant_blobs

        visit(revision, b"", frozenset(), 0)
        blob_infos: dict[str, GitObjectInfo] = {}
        for oid in sorted({oid for _mode, oid in entries.values()}):
            info = objects.info(oid)
            require(info.kind == "blob", f"Git object {oid} is not an exact blob")
            require(
                info.size <= MAX_BLOB_OBJECT_BYTES,
                "Git blob exceeds the per-object byte bound",
            )
            blob_infos[oid] = info
        blob_logical_bytes = 0
        for path in sorted(entries):
            info = blob_infos[entries[path][1]]
            require(
                info.size <= MAX_BLOB_LOGICAL_BYTES - blob_logical_bytes,
                "Git blob projection exceeds the aggregate byte bound",
            )
            blob_logical_bytes += info.size
        blob_sha256 = {
            oid: objects.contents_blob_sha256(blob_infos[oid])
            for oid in sorted(blob_infos)
        }
        return {
            path: Entry(
                mode=entries[path][0],
                oid=entries[path][1],
                sha256=blob_sha256[entries[path][1]],
            )
            for path in sorted(entries)
        }


def parse_index(resources: ResourceLedger) -> dict[str, tuple[str, str]]:
    raw = git_process(
        "ls-files",
        "--stage",
        "-z",
        resources=resources,
        stdout_limit=MAX_GIT_INVENTORY_STDOUT_BYTES,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    result: dict[str, tuple[str, str]] = {}
    for record in nul_records(raw):
        try:
            metadata, path_raw = record.split(b"\t", 1)
            mode_raw, oid_raw, stage_raw = metadata.split(b" ", 2)
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
            stage = stage_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise FollowupError("Git index record is malformed") from error
        path = canonical_path(path_raw, label="index")
        require(
            mode in {"100644", "100755"}
            and HEX40.fullmatch(oid) is not None
            and stage == "0",
            f"{path!r}: unsupported index entry",
        )
        require(
            len(result) < CANDIDATE_PATH_COUNT,
            "Git index exceeds the candidate path-count bound",
        )
        require(path not in result, f"duplicate index path: {path}")
        result[path] = (mode, oid)
    expected_paths = tuple(sorted(result))
    flagged_raw = git_process(
        "ls-files",
        "-v",
        "-z",
        "--",
        resources=resources,
        stdout_limit=MAX_GIT_INVENTORY_STDOUT_BYTES,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    flagged_paths: list[str] = []
    for record in nul_records(flagged_raw):
        require(
            record.startswith(b"H "),
            "Git index has a skip-worktree or assume-unchanged flag",
        )
        require(
            len(flagged_paths) < CANDIDATE_PATH_COUNT,
            "Git index flag inventory exceeds the candidate path-count bound",
        )
        flagged_paths.append(canonical_path(record[2:], label="index assume-unchanged"))
    require(
        tuple(flagged_paths) == expected_paths,
        "Git index flag inventory differs from stage zero",
    )
    return result


def observe_index(
    context: RepositoryContext, resources: ResourceLedger
) -> IndexObservation:
    require(
        all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_NONBLOCK")),
        "follow-up gate requires POSIX no-follow index custody",
    )
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | os.O_NONBLOCK
    descriptor: int | None = None
    try:
        descriptor = os.open(context.index_path, flags)
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            "Git index must be a single-linked regular non-symlink file",
        )
        require(
            32 <= before.st_size <= MAX_INDEX_BYTES,
            "Git index exceeds the byte-size bound",
        )
        permissions = stat.S_IMODE(before.st_mode)
        require(
            bool(permissions & stat.S_IRUSR)
            and not permissions & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            and not permissions & (stat.S_IWGRP | stat.S_IWOTH),
            f"Git index permissions are unsafe: {permissions:#o}",
        )
        first = read_exact_bytes(
            descriptor,
            before.st_size,
            resources,
            label="Git index",
        )
        middle = os.fstat(descriptor)
        compare_exact_bytes(
            descriptor,
            first,
            resources,
            label="Git index",
        )
        after = os.fstat(descriptor)
        identity = descriptor_identity(before)
        require(
            identity == descriptor_identity(middle)
            and identity == descriptor_identity(after)
            and len(first) == before.st_size,
            "Git index changed during descriptor observation",
        )
        require(bool(first), "Git index is empty")
        require(
            len(first) >= 32 and first[:4] == b"DIRC",
            "Git index header is malformed",
        )
        version = int.from_bytes(first[4:8], byteorder="big")
        entry_count = int.from_bytes(first[8:12], byteorder="big")
        require(version in {2, 3, 4}, "Git index version is unsupported")
        require(
            entry_count <= CANDIDATE_PATH_COUNT,
            "Git index exceeds the candidate path-count bound",
        )
        require(
            hashlib.sha1(first[:-20]).digest() == first[-20:],
            "Git index trailing checksum is inconsistent",
        )
        # FSMN stores the fsmonitor-valid bitmap; link and sdir identify split and
        # sparse indexes.  Raw signature absence is a one-sided fail-closed test: an
        # incidental signature elsewhere may reject a benign index, but an actual
        # forbidden extension cannot pass.  This avoids enabling a hook or built-in
        # daemon merely to ask Git to expose the fsmonitor bitmap.
        require(
            all(signature not in first for signature in (b"FSMN", b"link", b"sdir")),
            "Git index contains fsmonitor, split-index, or sparse-index state",
        )
        return IndexObservation(
            body=first,
            entry_count=entry_count,
            identity=identity,
            permissions=permissions,
            version=version,
        )
    except (OSError, ValueError) as error:
        raise FollowupError(f"cannot observe the private Git index: {error}") from error
    finally:
        primary = sys.exception()
        close_error = close_descriptor_preserving_error(
            descriptor, primary, label="Git index descriptor"
        )
        if primary is None and close_error is not None:
            raise FollowupError("cannot close the private Git index") from close_error


def collect_filesystem_topology(
    expected_files: tuple[str, ...],
    resources: ResourceLedger,
) -> tuple[str, ...]:
    require(
        os.stat in os.supports_dir_fd
        and os.open in os.supports_dir_fd
        and os.scandir in os.supports_fd
        and all(
            hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
        ),
        "follow-up gate requires POSIX descriptor-relative topology custody",
    )
    require(
        expected_files == tuple(sorted(set(expected_files)))
        and len(expected_files) <= CANDIDATE_PATH_COUNT,
        "expected filesystem inventory is duplicate or exceeds its bound",
    )
    expected_directories: set[str] = set()
    for path in expected_files:
        parent = PurePosixPath(path).parent
        while parent != PurePosixPath("."):
            value = parent.as_posix()
            if value not in expected_directories:
                require(
                    len(expected_directories) + len(expected_files) + 1
                    < MAX_WORKTREE_NODES,
                    "expected filesystem topology exceeds the node bound",
                )
                expected_directories.add(value)
            parent = parent.parent

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    regular_files: list[str] = []
    directories: list[str] = []
    observed_nodes = 0
    root_git_seen = False

    def visit(
        descriptor: int,
        prefix: str,
        depth: int,
    ) -> None:
        nonlocal observed_nodes, root_git_seen
        require(depth <= MAX_TREE_DEPTH, "worktree topology exceeds the depth bound")
        names: list[str] = []
        seen_names: set[str] = set()
        directory_entries = 0
        try:
            with os.scandir(descriptor) as iterator:
                for entry in iterator:
                    resources.check_deadline()
                    directory_entries += 1
                    require(
                        directory_entries <= MAX_DIRECTORY_ENTRIES,
                        f"worktree directory {prefix or '.'!r} exceeds the entry bound",
                    )
                    observed_nodes += 1
                    require(
                        observed_nodes <= MAX_WORKTREE_NODES,
                        "worktree topology exceeds the node bound",
                    )
                    name = entry.name
                    try:
                        name_raw = name.encode("utf-8", errors="strict")
                    except UnicodeEncodeError as error:
                        raise FollowupError(
                            "worktree name is not strict UTF-8"
                        ) from error
                    resources.charge(len(name_raw))
                    canonical_path(name_raw, label="worktree component")
                    path = f"{prefix}/{name}" if prefix else name
                    canonical_path(path.encode("utf-8"), label="worktree topology")
                    require(
                        name not in seen_names,
                        f"worktree directory {prefix or '.'!r} has duplicate names",
                    )
                    seen_names.add(name)
                    names.append(name)
        except OSError as error:
            raise FollowupError(
                f"cannot enumerate worktree directory {prefix or '.'!r}: {error}"
            ) from error
        for name in sorted(names):
            path = f"{prefix}/{name}" if prefix else name
            resources.check_deadline()
            try:
                metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except OSError as error:
                raise FollowupError(
                    f"cannot inspect worktree topology path {path!r}: {error}"
                ) from error
            if not prefix and name == ".git":
                require(
                    not root_git_seen
                    and (
                        stat.S_ISDIR(metadata.st_mode)
                        or (stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1)
                    ),
                    "root .git entry has unsupported topology",
                )
                root_git_seen = True
                continue
            if stat.S_ISDIR(metadata.st_mode):
                require(
                    path in expected_directories,
                    f"worktree has an extra or empty directory: {path!r}",
                )
                try:
                    child = os.open(name, directory_flags, dir_fd=descriptor)
                except OSError as error:
                    raise FollowupError(
                        f"cannot open no-follow worktree directory {path!r}: {error}"
                    ) from error
                try:
                    before = directory_descriptor_identity(metadata)
                    require(
                        directory_descriptor_identity(os.fstat(child)) == before,
                        f"worktree directory identity differs at {path!r}",
                    )
                    directories.append(path)
                    visit(child, path, depth + 1)
                    require(
                        directory_descriptor_identity(os.fstat(child)) == before,
                        f"worktree directory changed during traversal: {path!r}",
                    )
                finally:
                    primary = sys.exception()
                    close_error = close_descriptor_preserving_error(
                        child, primary, label="worktree child directory descriptor"
                    )
                    if primary is None and close_error is not None:
                        raise FollowupError(
                            "cannot close a worktree child directory descriptor"
                        ) from close_error
            else:
                require(
                    stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1,
                    f"worktree has a symlink, hardlink, or special node: {path!r}",
                )
                regular_files.append(path)

    root_descriptor: int | None = None
    try:
        root_descriptor = os.open(ROOT, directory_flags)
        require(
            stat.S_ISDIR(os.fstat(root_descriptor).st_mode),
            "worktree root descriptor is not a directory",
        )
        visit(root_descriptor, "", 0)
    except (OSError, ValueError) as error:
        raise FollowupError(f"cannot open worktree topology root: {error}") from error
    finally:
        primary = sys.exception()
        close_error = close_descriptor_preserving_error(
            root_descriptor, primary, label="worktree root descriptor"
        )
        if primary is None and close_error is not None:
            raise FollowupError("cannot close the worktree root descriptor") from close_error

    actual_files = tuple(sorted(regular_files))
    actual_directories = tuple(sorted(directories))
    require(root_git_seen, "worktree root has no .git entry")
    require(
        actual_files == expected_files, "filesystem and Git file inventories differ"
    )
    require(
        actual_directories == tuple(sorted(expected_directories)),
        "filesystem and implied directory inventories differ",
    )
    return actual_directories


def collect_snapshot(
    context: RepositoryContext, resources: ResourceLedger
) -> Snapshot:
    head = git_text(
        "rev-parse", "--verify", "HEAD^{commit}", resources=resources
    )
    require(HEX40.fullmatch(head) is not None, "HEAD is not an exact commit")
    head_tree = git_text(
        "rev-parse", "--verify", "HEAD^{tree}", resources=resources
    )
    require(HEX40.fullmatch(head_tree) is not None, "HEAD tree is not exact")
    head_commit = exact_object_bytes(head, "commit", resources)
    require(
        head_commit.partition(b"\n")[0] == f"tree {head_tree}".encode("ascii"),
        "HEAD raw commit/tree relation is inconsistent",
    )
    head_entries = parse_tree(head_tree, resources)
    index_before = observe_index(context, resources)
    require(
        git_text("rev-parse", "--shared-index-path", resources=resources) == "",
        "split-index indirection is forbidden",
    )
    index = parse_index(resources)
    require(
        index_before.entry_count == len(index),
        "Git index header count differs from the parsed stage-zero inventory",
    )
    require(
        index
        == {path: (entry.mode, entry.oid) for path, entry in head_entries.items()},
        "Git index differs from HEAD",
    )
    untracked_raw = git_process(
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        resources=resources,
        stdout_limit=MAX_GIT_INVENTORY_STDOUT_BYTES,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    untracked_list: list[str] = []
    for record in nul_records(untracked_raw):
        require(
            len(untracked_list) < CANDIDATE_PATH_COUNT,
            "untracked inventory exceeds the candidate path-count bound",
        )
        untracked_list.append(canonical_path(record, label="untracked"))
    untracked = tuple(untracked_list)
    require(
        untracked == tuple(sorted(set(untracked))), "untracked paths are not canonical"
    )
    ignored_raw = git_process(
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
        resources=resources,
        stdout_limit=MAX_GIT_INVENTORY_STDOUT_BYTES,
        stderr_limit=MAX_GIT_STDERR_BYTES,
        input_limit=MAX_GIT_STDIN_BYTES,
        timeout_seconds=GIT_COMMAND_TIMEOUT_SECONDS,
    ).stdout
    for record in nul_records(ignored_raw):
        canonical_inventory_path(record, label="ignored")
        raise FollowupError("worktree contains ignored filesystem contamination")
    ignored: tuple[str, ...] = ()
    require(
        not set(head_entries).intersection(untracked),
        "tracked and untracked path inventories overlap",
    )
    require(
        len(head_entries) + len(untracked) <= CANDIDATE_PATH_COUNT,
        "candidate inventory exceeds the path-count bound",
    )
    expected_files = tuple(sorted((*head_entries.keys(), *untracked)))
    filesystem_directories = collect_filesystem_topology(
        expected_files, resources
    )
    entries: dict[str, Entry] = {}
    tracked_modifications: list[str] = []
    worktree_logical_bytes = 0
    for path in expected_files:
        resources.check_deadline()
        require(path not in entries, f"candidate path appears twice: {path}")
        mode, body = stable_file(
            ROOT,
            path,
            resources,
            aggregate_remaining=(
                MAX_WORKTREE_LOGICAL_BYTES - worktree_logical_bytes
            ),
        )
        worktree_logical_bytes += len(body)
        entry = Entry(
            mode=mode,
            oid=blob_oid(body),
            sha256=hashlib.sha256(body).hexdigest(),
        )
        entries[path] = entry
        if path in head_entries and entry != head_entries[path]:
            tracked_modifications.append(path)
    index_after = observe_index(context, resources)
    require(index_after == index_before, "Git index changed during snapshot collection")
    return Snapshot(
        head=head,
        entries=entries,
        filesystem_directories=filesystem_directories,
        index_mode=index_before.permissions,
        index_sha256=hashlib.sha256(index_before.body).hexdigest(),
        index_size=len(index_before.body),
        index_version=index_before.version,
        tracked_modifications=tuple(tracked_modifications),
        untracked=untracked,
        ignored=ignored,
    )


def projection(entries: dict[str, Entry], paths: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        entry = entries[path]
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry.mode.encode("ascii"))
        digest.update(b"\0blob\0")
        digest.update(entry.sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def allowlist_digest(snapshot: Snapshot) -> str:
    digest = hashlib.sha256()
    for path in sorted(EXPECTED_PATH_STATUS):
        entry = snapshot.entries[path]
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(EXPECTED_PATH_STATUS[path].encode("ascii"))
        digest.update(b"\0")
        digest.update(entry.mode.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def named_projections(
    entries: dict[str, Entry], eligible_paths: tuple[str, ...]
) -> dict[str, tuple[int, str]]:
    science = tuple(
        path
        for path in eligible_paths
        if path.startswith("crates/pid-core/src/")
        or path.startswith("crates/pid-python/src/")
    )
    formal = tuple(
        path
        for path in eligible_paths
        if path.startswith("audit/formal/") or path.startswith("claims/")
    )
    cargo = tuple(
        path
        for path in eligible_paths
        if PurePosixPath(path).name in {"Cargo.toml", "Cargo.lock"}
    )
    return {
        "science_source": (len(science), projection(entries, science)),
        "formal_claim": (len(formal), projection(entries, formal)),
        "cargo": (len(cargo), projection(entries, cargo)),
    }


def current_binding_facts(
    snapshot: Snapshot,
    anchor: dict[str, Entry],
    resources: ResourceLedger,
) -> dict[str, Any]:
    protected = tuple(sorted(set(anchor).difference(EXPECTED_PATH_STATUS)))
    pinned_changed = tuple(
        sorted(set(EXPECTED_PATH_STATUS).difference(SELF_UNHASHED_PATHS))
    )
    allowed_blobs: dict[str, list[Any]] = {}
    for path in pinned_changed:
        mode, body = stable_file(ROOT, path, resources)
        entry = snapshot.entries[path]
        require(
            entry
            == Entry(
                mode=mode,
                oid=blob_oid(body),
                sha256=hashlib.sha256(body).hexdigest(),
            ),
            f"{path!r}: binding bytes changed after the candidate snapshot",
        )
        allowed_blobs[path] = [entry.mode, len(body), entry.sha256]
    return {
        "allowed_blobs": allowed_blobs,
        "allowlist_sha256": allowlist_digest(snapshot),
        "pinned_changed_projection_sha256": projection(
            snapshot.entries, pinned_changed
        ),
        "anchor_named_projections": {
            key: [count, digest]
            for key, (count, digest) in named_projections(anchor, protected).items()
        },
        "candidate_named_projections": {
            key: [count, digest]
            for key, (count, digest) in named_projections(
                snapshot.entries, protected
            ).items()
        },
        "protected_path_count": len(protected),
        "anchor_protected_projection_sha256": projection(anchor, protected),
        "candidate_protected_projection_sha256": projection(
            snapshot.entries, protected
        ),
        "self_unhashed_paths": sorted(SELF_UNHASHED_PATHS),
    }


def validate_bindings(
    snapshot: Snapshot,
    anchor: dict[str, Entry],
    resources: ResourceLedger,
) -> tuple[str, str]:
    actual_changed = tuple(
        path
        for path in sorted(set(anchor) | set(snapshot.entries))
        if anchor.get(path) != snapshot.entries.get(path)
    )
    require(
        actual_changed == tuple(sorted(EXPECTED_PATH_STATUS)),
        "follow-up changed-path set differs from the exact allowlist",
    )
    for path, status_value in EXPECTED_PATH_STATUS.items():
        actual_status = "A" if path not in anchor else "M"
        require(actual_status == status_value, f"{path}: follow-up status changed")
    facts = current_binding_facts(snapshot, anchor, resources)
    expected_blobs = {
        path: [mode, size, digest]
        for path, (mode, size, digest) in EXPECTED_ALLOWED_BLOBS.items()
    }
    require(
        facts["allowed_blobs"] == expected_blobs,
        "follow-up full allowed-blob projection changed",
    )
    require(
        facts["allowlist_sha256"] == EXPECTED_ALLOWLIST_SHA256,
        "follow-up allowlist projection changed",
    )
    require(
        facts["pinned_changed_projection_sha256"]
        == EXPECTED_PINNED_CHANGED_PROJECTION_SHA256,
        "follow-up acyclic pinned changed-byte projection changed",
    )
    require(
        facts["protected_path_count"] == 552
        and facts["anchor_protected_projection_sha256"]
        == EXPECTED_PROTECTED_PROJECTION_SHA256
        and facts["candidate_protected_projection_sha256"]
        == EXPECTED_PROTECTED_PROJECTION_SHA256,
        "follow-up protected projection changed",
    )
    expected_named = {
        "science_source": list(EXPECTED_SCIENCE_SOURCE_PROJECTION),
        "formal_claim": list(EXPECTED_FORMAL_CLAIM_PROJECTION),
        "cargo": list(EXPECTED_CARGO_PROJECTION),
    }
    require(
        facts["anchor_named_projections"] == expected_named
        and facts["candidate_named_projections"] == expected_named,
        "follow-up named protected projections changed",
    )
    protected = tuple(sorted(set(anchor).difference(EXPECTED_PATH_STATUS)))
    require(
        all(snapshot.entries.get(path) == anchor[path] for path in protected),
        "follow-up changed a protected path",
    )
    return (
        str(facts["candidate_protected_projection_sha256"]),
        projection(snapshot.entries, tuple(sorted(snapshot.entries))),
    )


def validate_source_semantics(
    anchor: dict[str, Entry], resources: ResourceLedger
) -> None:
    _mode, workflow = stable_file(
        ROOT, ".github/workflows/ci.yml", resources
    )
    ksg_start = workflow.find(b"  ksg-harmonic-assurance:\n")
    ksg_end = workflow.find(b"  formal-finite-convergence:\n")
    pdf_start = workflow.find(b"  formal-pdf-structure:\n")
    pdf_end = workflow.find(b"  certified-sxpid-reference:\n")
    require(
        0 <= ksg_start < ksg_end <= pdf_start < pdf_end,
        "hosted KSG/PDF job boundaries changed",
    )
    ksg_job = workflow[ksg_start:ksg_end]
    pdf_job = workflow[pdf_start:pdf_end]
    ubuntu_pin = b"    runs-on: ubuntu-24.04\n"
    require(
        workflow.count(ubuntu_pin) == 2
        and ksg_job.count(ubuntu_pin) == 1
        and pdf_job.count(ubuntu_pin) == 1
        and ksg_job.count(b"    runs-on: ") == 1
        and pdf_job.count(b"    runs-on: ") == 1,
        "hosted KSG/PDF Ubuntu runner pins changed",
    )
    require(
        ksg_job.count(b"    timeout-minutes: 360\n") == 1
        and ksg_job.count(b"    timeout-minutes: ") == 1
        and pdf_job.count(b"    timeout-minutes: 60\n") == 1
        and pdf_job.count(b"    timeout-minutes: ") == 1,
        "hosted KSG/PDF timeout envelopes changed",
    )
    checkout = (
        b"      - uses: actions/checkout@"
        b"9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
        b"        with:\n"
        b"          fetch-depth: 0\n"
        b"          persist-credentials: false\n"
        b"          # pull_request defaults to a synthetic merge; custody requires "
        b"the exact PR head.\n"
        b"          ref: \"${{ github.event_name == 'pull_request' && "
        b"github.event.pull_request.head.sha || github.sha }}\"\n"
    )
    require(
        ksg_job.count(checkout) == 1
        and ksg_job.count(b"      - uses: actions/checkout@") == 1
        and ksg_job.count(b"          fetch-depth: 0\n") == 1
        and ksg_job.count(b"          persist-credentials: false\n") == 1
        and ksg_job.count(b"          ref: ") == 1,
        "hosted KSG checkout lost exact PR-head custody",
    )
    historical = b"          scripts/check-ksg-c3-checkpoint.sh\n"
    checkpoint = b'          checkpoint="$(git rev-parse --verify HEAD)"\n'
    candidate_tree = (
        b'          candidate_tree="$(git rev-parse --verify \'HEAD^{tree}\')"\n'
    )
    supervisor = (
        b"          scripts/check-c3-hosted-followup.sh normal self-test \\\n"
        b"            --compare-runner-modes \\\n"
        b'            --expected-candidate-tree "$candidate_tree" \\\n'
        b'            --checkpoint-commit "$checkpoint"\n'
    )
    cache_action = (
        b"      - uses: Swatinem/rust-cache@"
        b"e18b497796c12c097a38f9edb9d0641fb99eee32 # v2\n"
    )
    require(
        workflow.count(historical) == 1
        and workflow.count(supervisor) == 1
        and ksg_job.count(checkpoint) == 1
        and ksg_job.count(candidate_tree) == 1
        and ksg_job.count(cache_action) == 1
        and ksg_job.index(historical)
        < ksg_job.index(checkpoint)
        < ksg_job.index(candidate_tree)
        < ksg_job.index(supervisor)
        < ksg_job.index(cache_action),
        "hosted KSG historical/supervisor/cache custody order changed",
    )
    for forbidden in (
        b'evidence_directory=',
        b'checker_normal=',
        b'checker_optimized=',
        b'self_test_normal=',
        b'self_test_optimized=',
        b'mktemp -d "$RUNNER_TEMP/pid-rs-c3-followup.',
        b'scripts/check-c3-hosted-followup.sh normal checker',
        b'scripts/check-c3-hosted-followup.sh optimized checker',
        b'scripts/check-c3-hosted-followup.sh optimized self-test',
        b'scripts/check-c3-hosted-followup.sh normal self-test\n',
        b'python3 -I -S - "$self_test_normal"',
        b'cmp --silent -- "$checker_normal"',
        b'cat -- "$checker_normal"',
        b"<<'PYTHON'",
    ):
        require(
            forbidden not in ksg_job,
            f"hosted KSG job retained rejected outer evidence: {forbidden!r}",
        )
    texlive = b"            texlive-fonts-extra \\\n"
    require(
        workflow.count(texlive) == 1 and pdf_job.count(texlive) == 1,
        "hosted PDF job lost the exact Libertinus package dependency",
    )
    _mode, support = stable_file(
        ROOT, "crates/pid-core/build_support.rs", resources
    )
    require(
        support.count(b"after_first_status();") == 1
        and support.count(b"probe_working_tree_with_git_after_first_status_for_test")
        == 1,
        "software-identity deterministic final-status seam changed",
    )
    _mode, regression = stable_file(
        ROOT,
        "crates/pid-core/tests/software_identity_build.rs",
        resources,
    )
    require(
        regression.count(b"changed after first status\\n") == 1
        and b"change-after-status-git" not in regression,
        "software-identity final-status regression route changed",
    )
    mode, wrapper = stable_file(ROOT, WRAPPER_RELATIVE, resources)
    require(mode == "100755", "immutable C3 replay wrapper is not executable")
    for token in (
        ANCHOR.encode("ascii"),
        ANCHOR_TREE.encode("ascii"),
        b"python3 -I -S scripts/check-ksg-phase-isolation.py",
        b"python3 -I -S -O scripts/check-ksg-phase-isolation.py",
        b"python3 -I -S scripts/check-ksg-phase-isolation-self-test.py",
        b"python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py",
        b'--pathspec-from-file="$DELTA_NAME_ONLY" --pathspec-file-nul',
    ):
        require(token in wrapper, f"immutable C3 replay wrapper lost token: {token!r}")
    runner_mode, runner = stable_file(ROOT, RUNNER_RELATIVE, resources)
    require(runner_mode == "100755", "follow-up exact-source runner is not executable")
    for token in (
        b"python_arguments=(-I -S -)",
        b"python_arguments=(-I -S -O -)",
        b"type -P python3",
        b"os.O_NOFOLLOW",
        b"os.O_NONBLOCK",
        b"dont_inherit=True",
        b"optimize=sys.flags.optimize",
        b"__pid_rs_exact_source_context__",
        b'"size": expected_size',
        b"directory_identity",
        b"directory_descriptors",
        b"fresh_descriptors",
        b"root_components",
    ):
        require(token in runner, f"follow-up exact-source runner lost token: {token!r}")
    self_test_mode, self_test = stable_file(
        ROOT, SELF_TEST_RELATIVE, resources
    )
    require(self_test_mode == "100755", "follow-up self-test is not executable")
    for token in (
        b"def run_mode_comparison_supervisor(\n",
        b"    tree: str, checkpoint: str, runner_state: RunnerState\n",
        b'[runner, mode.value, "checker", *external_arguments(outer_candidate)]',
        b'[runner, mode.value, "self-test"]',
        b"child self-test receipts differ after deleting only "
        b"mutation_target_python_mode",
        b'and child_candidate["tree"] == expected_outer_candidate.tree',
        b"and exact_source == expected_exact_source",
        b"expected_runner_state.maximum_source_size == MAX_EXACT_SOURCE_BYTES",
        b'"schema": "pid-rs/c3-hosted-followup-mode-comparison/v2"',
        b'"--compare-runner-modes"',
    ):
        require(
            self_test.count(token) == 1,
            f"follow-up mode-comparison supervisor lost token: {token!r}",
        )
    claim_mode, claim_checker = stable_file(
        ROOT, CERTIFIED_CLAIM_CHECKER_RELATIVE, resources
    )
    require(
        claim_mode == "100644",
        "certified claim checker has a noncanonical mode",
    )
    anchor_claim_entry = anchor[CERTIFIED_CLAIM_CHECKER_RELATIVE]
    with GitCatFileSession(resources) as objects:
        anchor_claim_info = objects.info(anchor_claim_entry.oid)
        require(
            anchor_claim_info.kind == "blob"
            and anchor_claim_info.size <= MAX_BLOB_OBJECT_BYTES,
            "immutable certified claim checker blob metadata changed",
        )
        anchor_claim_checker = objects.contents_bytes(anchor_claim_info)
    require(
        hashlib.sha256(anchor_claim_checker).hexdigest()
        == anchor_claim_entry.sha256,
        "immutable certified claim checker blob digest changed",
    )
    reviewed_digest_rebindings = (
        (
            b"02f3a8598683766cdba4cb75413783dca9c9a73ff87b833c2b5e8b21799d2220",
            b"dc420ee70075fe3eb4359c84241b9bb8146c281ea912a6a9ede5aa96d96e6650",
        ),
        (
            b"384ca61cd1f4f1c7eafbe71f6b39e71f4edd8822038feaa4ad07dc072bbb38cc",
            b"3bf14879c131504386903f7d932364b035151677fbc8d992804272115511d49b",
        ),
        (
            b"4ea701794c455021aff8c991aac8a127fde1bcabed390e2dc0b5037f475b3a83",
            b"9117706fec217a2aa0433dc3faa4827f90798f885396bf41564edbf0784008fa",
        ),
    )
    expected_claim_checker = anchor_claim_checker
    for old_digest, new_digest in reviewed_digest_rebindings:
        require(
            expected_claim_checker.count(old_digest) == 1
            and new_digest not in expected_claim_checker,
            "immutable certified claim checker rebind tokens changed",
        )
        expected_claim_checker = expected_claim_checker.replace(
            old_digest, new_digest, 1
        )
    require(
        claim_checker == expected_claim_checker,
        "certified claim checker rebind differs from three reviewed digest substitutions",
    )


def parse_commit(
    commit: str, expected_tree: str, resources: ResourceLedger
) -> None:
    raw = exact_object_bytes(commit, "commit", resources)
    require(
        b"\r" not in raw and b"\0" not in raw, "checkpoint commit contains CR or NUL"
    )
    header_raw, separator, message = raw.partition(b"\n\n")
    require(separator == b"\n\n", "checkpoint commit lacks a message separator")
    lines = header_raw.splitlines()
    require(len(lines) == 4, "checkpoint commit header count changed")
    keys = [line.partition(b" ")[0] for line in lines]
    require(
        keys == [b"tree", b"parent", b"author", b"committer"],
        "checkpoint commit is not exact unsigned single-parent form",
    )
    require(
        lines[0] == f"tree {expected_tree}".encode("ascii"),
        "checkpoint commit tree differs",
    )
    require(
        lines[1] == f"parent {ANCHOR}".encode("ascii"),
        "checkpoint parent differs from C3",
    )
    identity_pattern = re.compile(
        rb"(?P<name>.+) <(?P<email>[^<>\s]+)> (?P<epoch>[0-9]+) (?P<timezone>\S+)"
    )
    for label, line in (("author", lines[2]), ("committer", lines[3])):
        prefix, _, value = line.partition(b" ")
        require(prefix == label.encode("ascii"), f"checkpoint {label} header changed")
        match = identity_pattern.fullmatch(value)
        if match is None:
            raise FollowupError(f"checkpoint {label} identity is malformed")
        try:
            name = match.group("name").decode("utf-8", errors="strict")
            email = match.group("email").decode("ascii", errors="strict")
            timezone = match.group("timezone").decode("ascii", errors="strict")
        except UnicodeDecodeError as error:
            raise FollowupError(
                f"checkpoint {label} identity encoding is malformed"
            ) from error
        require(
            name == EXPECTED_DISPLAY_NAME
            and email == EXPECTED_EMAIL
            and TIMEZONE.fullmatch(timezone) is not None,
            f"checkpoint {label} identity differs from reviewed human identity",
        )
    require(
        message == EXPECTED_COMMIT_MESSAGE.encode("utf-8"),
        "checkpoint commit message differs",
    )


def validate_external_custody(
    snapshot: Snapshot,
    expected_tree: str | None,
    checkpoint: str | None,
    diagnostic: bool,
    resources: ResourceLedger,
) -> str:
    require(
        (expected_tree is None) == (checkpoint is None),
        "external tree and checkpoint must be paired",
    )
    if expected_tree is None:
        require(
            diagnostic,
            "creditable follow-up validation requires external tree/checkpoint custody",
        )
        return "diagnostic-no-credit"
    require(not diagnostic, "diagnostic mode cannot accompany external custody")
    if checkpoint is None:
        raise FollowupError("checkpoint commit is absent")
    require(HEX40.fullmatch(expected_tree) is not None, "external tree id is invalid")
    require(HEX40.fullmatch(checkpoint) is not None, "checkpoint commit id is invalid")
    external_entries = parse_tree(expected_tree, resources)
    require(
        external_entries == snapshot.entries,
        "external tree differs from follow-up snapshot",
    )
    parse_commit(checkpoint, expected_tree, resources)
    if snapshot.head == ANCHOR:
        parents = git_text(
            "rev-list",
            "--parents",
            "-n",
            "1",
            checkpoint,
            resources=resources,
        ).split()
        require(
            parents == [checkpoint, ANCHOR],
            "detached checkpoint is not the exact C3 child",
        )
    else:
        require(
            checkpoint == snapshot.head,
            "committed lifecycle checkpoint differs from HEAD",
        )
    return "external-tree-and-checkpoint"


def validate_lifecycle(
    snapshot: Snapshot, resources: ResourceLedger
) -> str:
    if snapshot.head == ANCHOR:
        require(
            snapshot.tracked_modifications
            == tuple(
                sorted(
                    path
                    for path, status_value in EXPECTED_PATH_STATUS.items()
                    if status_value == "M"
                )
            )
            and snapshot.untracked
            == tuple(
                sorted(
                    path
                    for path, status_value in EXPECTED_PATH_STATUS.items()
                    if status_value == "A"
                )
            )
            and not snapshot.ignored,
            "precommit follow-up partition differs from exact policy",
        )
        return "precommit-worktree"
    history = git_text(
        "rev-list",
        "--first-parent",
        "--reverse",
        f"{ANCHOR}..{snapshot.head}",
        resources=resources,
    ).splitlines()
    require(history == [snapshot.head], "follow-up history is not one direct child")
    parents = git_text(
        "rev-list",
        "--parents",
        "-n",
        "1",
        snapshot.head,
        resources=resources,
    ).split()
    require(
        parents == [snapshot.head, ANCHOR], "follow-up HEAD is not the direct C3 child"
    )
    require(
        not snapshot.tracked_modifications
        and not snapshot.untracked
        and not snapshot.ignored,
        "committed follow-up filesystem has tracked, untracked, or ignored contamination",
    )
    return "committed-direct-child"


def external_tool_evidence(
    path_raw: str, resources: ResourceLedger
) -> dict[str, Any]:
    path = Path(path_raw).resolve(strict=True)
    require(path.is_absolute(), f"tool path is not absolute: {path}")
    require(
        all(hasattr(os, name) for name in ("O_NOFOLLOW", "O_NONBLOCK")),
        "follow-up gate requires POSIX nonblocking no-follow tool custody",
    )
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | os.O_NONBLOCK
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode)
            and bool(stat.S_IMODE(before.st_mode) & stat.S_IXUSR),
            f"tool is not a regular owner-executable file: {path}",
        )
        require(
            0 < before.st_size <= MAX_TOOL_FILE_BYTES,
            f"tool exceeds the per-file byte bound: {path}",
        )
        first = read_exact_bytes(
            descriptor,
            before.st_size,
            resources,
            label=f"tool {path}",
        )
        middle = os.fstat(descriptor)
        compare_exact_bytes(
            descriptor,
            first,
            resources,
            label=f"tool {path}",
        )
        after = os.fstat(descriptor)
        require(
            descriptor_identity(before) == descriptor_identity(middle)
            and descriptor_identity(middle) == descriptor_identity(after)
            and len(first) == before.st_size,
            f"tool changed during descriptor observation: {path}",
        )
        return {
            "path": str(path),
            "sha256": hashlib.sha256(first).hexdigest(),
        }
    except (OSError, ValueError) as error:
        raise FollowupError(
            f"cannot observe tool descriptor {path}: {error}"
        ) from error
    finally:
        primary = sys.exception()
        close_error = close_descriptor_preserving_error(
            descriptor, primary, label="external tool descriptor"
        )
        if primary is None and close_error is not None:
            raise FollowupError("cannot close an external tool descriptor") from close_error


def validated_anchor(resources: ResourceLedger) -> dict[str, Entry]:
    anchor_commit = exact_object_bytes(ANCHOR, "commit", resources)
    require(
        anchor_commit.partition(b"\n")[0] == f"tree {ANCHOR_TREE}".encode("ascii")
        and git_text(
            "rev-parse", f"{ANCHOR}^{{tree}}", resources=resources
        )
        == ANCHOR_TREE,
        "immutable C3 anchor commit/tree relation changed",
    )
    anchor = parse_tree(ANCHOR_TREE, resources)
    require(
        len(anchor) == ANCHOR_PATH_COUNT
        and projection(anchor, tuple(sorted(anchor))) == ANCHOR_PROJECTION_SHA256,
        "immutable C3 anchor tree projection changed",
    )
    return anchor


def validate_exact_source_entry(
    resources: ResourceLedger,
) -> tuple[str, int]:
    context = globals().get("__pid_rs_exact_source_context__")
    if not isinstance(context, dict):
        raise FollowupError("exact-source bootstrap context is absent")
    require(
        set(context) == {"optimize", "relative", "sha256", "size"},
        "exact-source bootstrap context fields changed",
    )
    optimize = context["optimize"]
    relative = context["relative"]
    source_sha256 = context["sha256"]
    source_size = context["size"]
    require(
        type(optimize) is int and optimize in {0, 1} and optimize == sys.flags.optimize,
        "exact-source bootstrap optimization mode is unsupported",
    )
    if not isinstance(source_sha256, str):
        raise FollowupError("exact-source bootstrap digest is not text")
    require(
        type(source_size) is int
        and 0 < source_size <= MAX_EXACT_SOURCE_BYTES,
        "exact-source bootstrap size is unsupported",
    )
    require(
        relative == CHECKER_RELATIVE and HEX64.fullmatch(source_sha256) is not None,
        "exact-source bootstrap target identity changed",
    )
    require(
        globals().get("__loader__") is None
        and globals().get("__spec__") is None
        and globals().get("__cached__") is None,
        "follow-up checker was not compiled through the exact-source namespace",
    )
    mode, body = stable_file(
        ROOT,
        CHECKER_RELATIVE,
        resources,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    require(mode == "100755", "follow-up checker is not executable")
    require(
        len(body) == source_size
        and hashlib.sha256(body).hexdigest() == source_sha256,
        "captured checker source differs from the live exact path",
    )
    return source_sha256, source_size


def emit_json(value: dict[str, Any]) -> None:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    require(
        len(encoded) + 1 <= MAX_RECEIPT_BYTES,
        "receipt exceeds the byte bound",
    )
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()


def maintenance_current_facts(resources: ResourceLedger) -> int:
    context = validate_repository_context(resources)
    anchor = validated_anchor(resources)
    snapshot = collect_snapshot(context, resources)
    result = {
        **current_binding_facts(snapshot, anchor, resources),
        "lifecycle": validate_lifecycle(snapshot, resources),
        "resource_bounds": resource_bounds_receipt(),
        "schema": "pid-rs/c3-hosted-followup-maintenance-facts/v2",
    }
    emit_json(result)
    return 0


def run_validation(resources: ResourceLedger) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-candidate-tree")
    parser.add_argument("--checkpoint-commit")
    parser.add_argument("--diagnostic-without-external-custody", action="store_true")
    parser.add_argument("--maintenance-current-facts", action="store_true")
    arguments = parser.parse_args()
    if arguments.maintenance_current_facts:
        require(
            arguments.expected_candidate_tree is None
            and arguments.checkpoint_commit is None
            and not arguments.diagnostic_without_external_custody,
            "maintenance facts mode cannot accompany validation arguments",
        )
        return maintenance_current_facts(resources)
    source_sha256, source_size = validate_exact_source_entry(resources)
    context = validate_repository_context(resources)
    anchor = validated_anchor(resources)
    snapshot = collect_snapshot(context, resources)
    lifecycle = validate_lifecycle(snapshot, resources)
    protected_digest, candidate_digest = validate_bindings(
        snapshot, anchor, resources
    )
    validate_source_semantics(anchor, resources)
    custody = validate_external_custody(
        snapshot,
        arguments.expected_candidate_tree,
        arguments.checkpoint_commit,
        arguments.diagnostic_without_external_custody,
        resources,
    )
    git_evidence = external_tool_evidence(GIT, resources)
    git_evidence["version"] = context.git_version
    python_evidence = external_tool_evidence(PYTHON_EXECUTABLE, resources)
    python_evidence["version"] = sys.version.splitlines()[0]

    # This is a repeated bounded observation, not an atomic filesystem snapshot.
    endpoint_context = validate_repository_context(resources)
    require(endpoint_context == context, "repository context changed during validation")
    endpoint_anchor = validated_anchor(resources)
    endpoint_snapshot = collect_snapshot(endpoint_context, resources)
    require(endpoint_anchor == anchor, "C3 anchor changed during validation")
    require(endpoint_snapshot == snapshot, "candidate changed during validation")
    require(
        validate_lifecycle(endpoint_snapshot, resources) == lifecycle,
        "lifecycle changed",
    )
    endpoint_protected, endpoint_candidate = validate_bindings(
        endpoint_snapshot, endpoint_anchor, resources
    )
    require(
        endpoint_protected == protected_digest
        and endpoint_candidate == candidate_digest,
        "candidate projections changed during validation",
    )
    validate_source_semantics(endpoint_anchor, resources)
    require(
        validate_external_custody(
            endpoint_snapshot,
            arguments.expected_candidate_tree,
            arguments.checkpoint_commit,
            arguments.diagnostic_without_external_custody,
            resources,
        )
        == custody,
        "external custody classification changed during validation",
    )
    endpoint_git_evidence = external_tool_evidence(GIT, resources)
    endpoint_git_evidence["version"] = endpoint_context.git_version
    endpoint_python_evidence = external_tool_evidence(
        PYTHON_EXECUTABLE, resources
    )
    endpoint_python_evidence["version"] = sys.version.splitlines()[0]
    require(
        endpoint_git_evidence == git_evidence
        and endpoint_python_evidence == python_evidence,
        "tool-file evidence changed during validation",
    )
    require(
        validate_exact_source_entry(resources) == (source_sha256, source_size),
        "exact-source entry changed during validation",
    )
    creditable = custody == "external-tree-and-checkpoint"
    receipt = {
        "anchor": {
            "commit": ANCHOR,
            "path_count": ANCHOR_PATH_COUNT,
            "projection_sha256": ANCHOR_PROJECTION_SHA256,
            "tree": ANCHOR_TREE,
        },
        "bounded_historical_replay": "separate_not_adjudicated_by_this_gate",
        "candidate": {
            "checkpoint_commit": arguments.checkpoint_commit,
            "declared_identity_metadata": (
                {
                    "email": EXPECTED_EMAIL,
                    "name": EXPECTED_DISPLAY_NAME,
                }
                if creditable
                else None
            ),
            "parent": ANCHOR,
            "projection_sha256": candidate_digest,
            "tree": arguments.expected_candidate_tree,
        },
        "credit": "caller_supplied_tree_checkpoint_match" if creditable else "none",
        "custody": custody,
        "environmental_premises": {
            "git": git_evidence,
            "python": python_evidence,
            "runtime_boundaries": {
                "absolute_python_path_required_by_runner": True,
                "bash_and_path_provenance_authenticated": False,
                "child_preexec_unmasks_sigalrm_sigint": True,
                "default_action_sigterm_sighup_sigkill_cleanup": False,
                "dynamic_loader_authenticated": False,
                "external_or_native_waiters_authenticated": False,
                "hard_async_deadline_preemption_during_child_lifecycle": False,
                "one_enumerated_python_thread_required": True,
                "other_signal_dispositions_or_masks_authenticated": False,
                "owned_child_pthread_sigmask": True,
                "python_main_thread_required": True,
                "python_stdlib_and_extensions_authenticated": False,
                "sigalrm_sigint_handlers_are_nonraising_recorders": True,
                "sigchld_explicitly_reset_before_children": True,
            },
        },
        "exact_source": {
            "checker_sha256": source_sha256,
            "checker_size": source_size,
            "loader": "size-and-digest-bound-no-follow-descriptor-compare",
        },
        "lifecycle": lifecycle,
        "non_implications": [
            "arithmetic",
            "estimator_validity",
            "pid_validity",
            "statistical_validity",
            "pdf_content_validity",
            "remote_authenticity",
            "independent_external_custody",
            "human_authorship_authentication",
            "security_cleanliness",
            "cross_platform_identity",
            "historical_c3_hostile_suite_completion",
            "atomic_snapshot",
            "running_binary_identity",
            "hosted_ci_success",
            "python_stdlib_authenticity",
            "dynamic_loader_authenticity",
            "shell_and_path_authenticity",
            "concurrent_repository_metadata_stability",
            "hard_process_rss_bound",
            "git_child_internal_memory_bound",
            "filesystem_backend_liveness",
            "denial_of_service_resistance",
            "same_user_aba_resistance",
            "complete_reachable_history",
            "object_store_completeness",
            "transparency_log",
            "post_reap_process_group_reclamation",
            "deliberate_process_group_or_session_escape_containment",
            "default_action_sigterm_sighup_or_sigkill_cleanup",
            "external_or_native_waiter_exclusion",
            "hard_async_deadline_preemption_during_owned_child_lifecycle",
            "other_signal_disposition_or_mask_normalization",
            "unenumerated_native_thread_absence",
        ],
        "path_custody": {
            "added": sum(value == "A" for value in EXPECTED_PATH_STATUS.values()),
            "allowlist_sha256": EXPECTED_ALLOWLIST_SHA256,
            "changed": len(EXPECTED_PATH_STATUS),
            "candidate_path_count": len(snapshot.entries),
            "filesystem_directory_count": len(snapshot.filesystem_directories),
            "filesystem_inventory": "bounded-no-follow-descriptor-walk",
            "full_candidate_projection_sha256": candidate_digest,
            "modified": sum(value == "M" for value in EXPECTED_PATH_STATUS.values()),
            "pinned_changed_projection_sha256": (
                EXPECTED_PINNED_CHANGED_PROJECTION_SHA256
            ),
            "protected": 552,
            "protected_projection_sha256": protected_digest,
            "self_unhashed_paths": sorted(SELF_UNHASHED_PATHS),
        },
        "repository_context": {
            "endpoint_equal": True,
            "git_command_timeout_seconds": GIT_COMMAND_TIMEOUT_SECONDS,
            "minimum_git_version": "2.45.0",
            "object_pack_inventory": {
                "entry_count": context.object_pack_inventory_count,
                "promisor_markers_absent": True,
                "sha256": context.object_pack_inventory_sha256,
            },
            "object_verification_scope": (
                "exact anchor, candidate, and checkpoint objects actually "
                "traversed, framed, and rehashed"
            ),
            "promisor_routing_absent": True,
            "shallow": False,
            "index": {
                "entry_count": len(snapshot.entries) - len(snapshot.untracked),
                "forbidden_extension_signatures_absent": ["FSMN", "link", "sdir"],
                "maximum_size": MAX_INDEX_BYTES,
                "mode": f"{snapshot.index_mode:04o}",
                "sha256": snapshot.index_sha256,
                "sha1_trailing_checksum_verified": True,
                "single_link_regular_no_split_index": True,
                "size": snapshot.index_size,
                "stage_zero_v_flags": "all-H",
                "version": snapshot.index_version,
            },
            "local_config": {
                "record_count": context.local_config_record_count,
                "sha256": context.local_config_sha256,
                "size": context.local_config_size,
            },
            "path_semantics_overrides": [
                "core.ignoreCase=false",
                "core.precomposeUnicode=false",
            ],
        },
        "resource_bounds": resource_bounds_receipt(),
        "schema": "pid-rs/c3-hosted-followup-custody/v2",
        "status": "pass" if creditable else "diagnostic_pass_no_credit",
        "validation_class": (
            "creditable_external_tree_checkpoint"
            if creditable
            else "diagnostic_only_without_external_custody"
        ),
    }
    emit_json(receipt)
    return 0


def main() -> int:
    require(
        all(
            hasattr(signal, name)
            for name in (
                "SIGALRM",
                "SIGINT",
                "ITIMER_REAL",
                "getitimer",
                "setitimer",
                "pthread_sigmask",
                "sigpending",
            )
        ),
        "follow-up gate requires POSIX deadline and signal-mask custody",
    )
    previous_handlers: tuple[Any, Any] | None = None
    primary_error: BaseException | None = None
    primary_traceback: Any = None
    result: int | None = None
    timer_call_started = False
    timer_disarmed = False
    try:
        previous_handlers = activate_verifier_signal_runtime()
        require(
            signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0),
            "follow-up gate inherited an active real-time interval timer",
        )
        timer_disarmed = True
        resources = ResourceLedger.start()
        timer_call_started = True
        timer_disarmed = False
        previous_timer = signal.setitimer(
            signal.ITIMER_REAL, VALIDATION_TIMEOUT_SECONDS
        )
        require(
            previous_timer == (0.0, 0.0),
            "follow-up gate replaced an inherited real-time interval timer",
        )
        result = run_validation(resources)
    except BaseException as error:
        primary_error = error
        primary_traceback = error.__traceback__

    if timer_call_started:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
            require(
                signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0),
                "whole-verifier timer cancellation could not prove zero state",
            )
        except BaseException as error:
            if primary_error is None:
                primary_error = error
                primary_traceback = error.__traceback__
            else:
                add_secondary_exception_note(
                    primary_error,
                    "whole-verifier timer cancellation also failed",
                    error,
                )
        else:
            timer_disarmed = True
    if previous_handlers is not None and timer_disarmed:
        try:
            deferred_error = deactivate_verifier_signal_runtime(
                previous_handlers,
                primary_error=primary_error,
            )
        except BaseException as error:
            if primary_error is None:
                primary_error = error
                primary_traceback = error.__traceback__
            else:
                add_secondary_exception_note(
                    primary_error,
                    "verifier signal-runtime teardown also failed",
                    error,
                )
        else:
            if deferred_error is not None and primary_error is None:
                primary_error = deferred_error
                primary_traceback = deferred_error.__traceback__
    elif previous_handlers is not None:
        timer_error = FollowupError(
            "signal handlers retained because timer disarm was not proven"
        )
        if primary_error is None:
            primary_error = timer_error
            primary_traceback = timer_error.__traceback__
        else:
            add_secondary_exception_note(
                primary_error,
                "signal-runtime teardown intentionally withheld",
                timer_error,
            )

    if primary_error is not None:
        raise primary_error.with_traceback(primary_traceback)
    require(result is not None, "follow-up validation produced no result")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FollowupError as error:
        print(f"ERROR: C3 hosted follow-up gate: {error}", file=sys.stderr)
        raise SystemExit(1) from None
