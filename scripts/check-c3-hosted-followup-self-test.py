#!/usr/bin/env python3
from __future__ import annotations

import sys

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    print(
        "ERROR: check-c3-hosted-followup-self-test.py requires Python -I -S",
        file=sys.stderr,
    )
    raise SystemExit(2)
if sys.flags.optimize not in {0, 1}:
    print(
        "ERROR: check-c3-hosted-followup-self-test.py supports only normal or -O mode",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
from collections import Counter
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import shutil
import signal
import stat
import subprocess
import tempfile
import threading
import time
from typing import Any
import zlib


class SelfTestError(RuntimeError):
    pass


class HarnessProcessFailure(SelfTestError):
    pass


class HarnessLaunchFailure(HarnessProcessFailure):
    pass


class HarnessTimeoutFailure(HarnessProcessFailure):
    pass


class HarnessOutputLimitFailure(HarnessProcessFailure):
    pass


class HarnessSignalFailure(HarnessProcessFailure):
    pass


class HarnessDescendantFailure(HarnessProcessFailure):
    pass


class HarnessCleanupFailure(HarnessProcessFailure):
    pass


class HarnessIoFailure(HarnessProcessFailure):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


OWNED_CHILD_SIGNAL_MASK_DEPTH = 0
VERIFIER_SIGNAL_RUNTIME_ACTIVE = False
VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE = False
DEFERRED_VERIFIER_SIGNAL_FLAGS: list[bool] = [False, False]


def add_exception_note_preserving_primary(
    primary: BaseException, note: str
) -> None:
    try:
        primary.add_note(note)
    except BaseException:
        # Note construction/attachment is non-authoritative.  Cleanup and the
        # initiating exception remain primary under exceptional memory pressure.
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
        "self-test requires POSIX thread-directed signal masking",
    )
    return frozenset((signal.SIGALRM, signal.SIGINT))


def require_dedicated_main_python_thread() -> None:
    require(
        threading.current_thread() is threading.main_thread(),
        "self-test child lifecycle requires the Python main thread",
    )
    require(
        threading.active_count() == 1 and len(threading.enumerate()) == 1,
        "self-test child lifecycle requires one enumerated Python thread",
    )


def current_thread_signal_mask() -> frozenset[signal.Signals]:
    try:
        return frozenset(signal.pthread_sigmask(signal.SIG_BLOCK, set()))
    except (OSError, RuntimeError, ValueError) as error:
        raise SelfTestError(
            f"cannot inspect the self-test Python-thread signal mask: {error}"
        ) from error


def child_unblock_owned_exception_signals() -> None:
    signal.pthread_sigmask(signal.SIG_UNBLOCK, (signal.SIGALRM, signal.SIGINT))


def verifier_signal_handler(signal_number: int, _frame: Any) -> None:
    # Never raise or explicitly allocate here: delivery can queue past the mask.
    # Safe points adjudicate these preallocated bool slots before/after custody.
    if signal_number == signal.SIGALRM:
        DEFERRED_VERIFIER_SIGNAL_FLAGS[0] = True
    elif signal_number == signal.SIGINT:
        DEFERRED_VERIFIER_SIGNAL_FLAGS[1] = True


def deferred_verifier_signals() -> tuple[signal.Signals, ...]:
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
        "self-test requires CPython signal-checkpoint semantics",
    )
    require(
        (3, 11) <= sys.version_info[:2] < (3, 15)
        and (
            not hasattr(sys, "_is_gil_enabled")
            or bool(sys._is_gil_enabled())
        ),
        "self-test requires reviewed GIL-enabled CPython 3.11-3.14",
    )
    require(
        not VERIFIER_SIGNAL_RUNTIME_ACTIVE
        and not VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE
        and OWNED_CHILD_SIGNAL_MASK_DEPTH == 0,
        "self-test verifier signal runtime is already active",
    )
    selected = owned_child_exception_signals()
    require(
        selected.isdisjoint(current_thread_signal_mask()),
        "self-test inherited a blocked SIGALRM or SIGINT",
    )
    require(
        selected.isdisjoint(frozenset(signal.sigpending())),
        "self-test inherited a pending SIGALRM or SIGINT",
    )
    previous_alarm = signal.getsignal(signal.SIGALRM)
    previous_interrupt = signal.getsignal(signal.SIGINT)
    require(
        previous_interrupt == signal.default_int_handler,
        "self-test requires Python's default SIGINT handler at entry",
    )
    DEFERRED_VERIFIER_SIGNAL_FLAGS[0] = False
    DEFERRED_VERIFIER_SIGNAL_FLAGS[1] = False
    try:
        signal.signal(signal.SIGALRM, verifier_signal_handler)
        signal.signal(signal.SIGINT, verifier_signal_handler)
    except BaseException as error:
        for selected, previous in (
            (signal.SIGALRM, previous_alarm),
            (signal.SIGINT, previous_interrupt),
        ):
            try:
                signal.signal(selected, previous)
            except BaseException as restore_error:
                add_secondary_exception_note(
                    error,
                    "partial self-test signal-runtime installation rollback failed",
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
        "self-test signal runtime ended with an owned child scope",
    )
    restoration_error: BaseException | None = None
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
                label="self-test signal-handler restoration",
            )
    if restoration_error is None:
        VERIFIER_SIGNAL_RUNTIME_ACTIVE = False
    else:
        for selected in (signal.SIGALRM, signal.SIGINT):
            try:
                signal.signal(selected, verifier_signal_handler)
            except BaseException as rollback_error:
                add_secondary_exception_note(
                    restoration_error,
                    "self-test signal-handler restoration rollback also failed",
                    rollback_error,
                )
        if primary_error is not None:
            add_secondary_exception_note(
                primary_error,
                "self-test signal-handler restoration also failed",
                restoration_error,
            )
    effective_error = primary_error or restoration_error
    deferred = deferred_verifier_signals()
    if deferred:
        detail = ", ".join(item.name for item in deferred)
        if effective_error is not None:
            add_exception_note_preserving_primary(
                effective_error,
                f"deferred self-test signals observed after child cleanup: {detail}"
            )
        elif signal.SIGINT in deferred:
            return KeyboardInterrupt()
        else:
            return SelfTestError(f"self-test received deferred signals: {detail}")
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
            f"deferred self-test signals observed after child cleanup: {detail}"
        )
        return
    if signal.SIGINT in deferred:
        raise KeyboardInterrupt
    raise SelfTestError(f"self-test received deferred signals: {detail}")


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
            f"{label} has no active self-test signal runtime",
        )
        require(
            not VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE,
            f"{label} self-test signal mask is indeterminate",
        )
        require(
            signal.getsignal(signal.SIGALRM) == verifier_signal_handler
            and signal.getsignal(signal.SIGINT) == verifier_signal_handler,
            f"{label} self-test signal handlers changed",
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
            raise SelfTestError(
                f"{self.label} could not restore the prior signal mask: {error}"
            ) from error
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
        "self-test requires POSIX SIGCHLD child ownership",
    )
    try:
        # Active sigaction replacement clears inherited SIG_IGN/SA_NOCLDWAIT;
        # merely inspecting getsignal() would not establish that reset.
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    except (OSError, RuntimeError, ValueError) as error:
        raise SelfTestError(f"cannot reset SIGCHLD to SIG_DFL: {error}") from error
    require_sigchld_default()


def require_sigchld_default() -> None:
    try:
        disposition = signal.getsignal(signal.SIGCHLD)
    except (OSError, RuntimeError, ValueError) as error:
        raise SelfTestError(f"cannot inspect SIGCHLD disposition: {error}") from error
    require(
        disposition == signal.SIG_DFL,
        "SIGCHLD disposition changed after explicit SIG_DFL reset",
    )


# This exact-source interpreter is dedicated to the self-test.  Reset before
# any Popen and require the invariant again at the centralized launch site.
reset_sigchld_for_owned_children()


SCRIPT_PATH = Path(__file__).resolve(strict=True)
ROOT = SCRIPT_PATH.parent.parent.resolve(strict=True)
CHECKER_RELATIVE = "scripts/check-c3-hosted-followup.py"
SELF_TEST_RELATIVE = "scripts/check-c3-hosted-followup-self-test.py"
RUNNER_RELATIVE = "scripts/check-c3-hosted-followup.sh"
CERTIFIED_CLAIM_CHECKER_RELATIVE = "scripts/check-certified-sxpid2-claim.py"
HISTORICAL_WRAPPER_RELATIVE = "scripts/check-ksg-c3-checkpoint.sh"
RECEIPT_RELATIVE = "audit/evidence/c3-hosted-followup-correction-2026-08-01.md"
ANCHOR = "8fa6e992d9124229c7a175c4508bf10df336675a"
ANCHOR_TREE = "059dc980d4a86066c07687188a452cf2459899eb"
ANCHOR_PROJECTION_SHA256 = (
    "54e26259d4d974ed6eaa530e042367479c9fac188bde936568aca364e583f917"
)
EXPECTED_PROTECTED_PROJECTION_SHA256 = (
    "38b56b93fc6f8c3873574237c7a23684d0481357f80d17e1c1e5474caa82962a"
)
EXPECTED_MESSAGE = "fix: repair C3 hosted portability gates\n"
EXPECTED_NAME = "Sepehr Mahmoudian"
EXPECTED_EMAIL = "sepmhn@gmail.com"
FIXED_DATE = "2000000000 +0000"
EXPECTED_FILESYSTEM_DIRECTORY_COUNT = 78

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
    HISTORICAL_WRAPPER_RELATIVE: "A",
    RUNNER_RELATIVE: "A",
}
EXPECTED_NON_IMPLICATIONS = (
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
)
EXPECTED_RESOURCE_BOUNDS = {
    "application_visible": {
        "maximum_bytes": 1_073_741_824,
        "scope": "checker reads and captured subprocess I/O after exact-source entry",
    },
    "filesystem": {
        "component_bytes": 255,
        "directory_entries": 4_096,
        "exact_source_bytes": 262_144,
        "index_bytes": 8_388_608,
        "path_bytes": 4_096,
        "snapshot_logical_bytes": 50_331_648,
        "tool_file_bytes": 67_108_864,
        "worktree_file_bytes": 4_194_304,
        "worktree_nodes": 4_096,
    },
    "git_objects": {
        "blob_logical_bytes_per_tree": 50_331_648,
        "blob_per_object_bytes": 4_194_304,
        "commit_per_object_bytes": 65_536,
        "tree_depth": 64,
        "tree_logical_bytes_per_traversal": 524_288,
        "tree_object_visits": 2_048,
        "tree_per_object_bytes": 524_288,
    },
    "processes": {
        "cat_file_header_bytes": 128,
        "git_command_timeout_seconds": 60,
        "git_config_stdout_bytes": 262_144,
        "git_inventory_stdout_bytes": 4_194_304,
        "git_stderr_bytes": 65_536,
        "git_stdin_bytes": 65_536,
        "git_text_stdout_bytes": 65_536,
        "child_preexec_unmasks_owned_signals": True,
        "external_waiter_premise": "no-external-or-native-direct-waiter",
        "owned_child_exception_signals": ["SIGALRM", "SIGINT"],
        "owned_child_signal_custody": (
            "nonraising-recorder-plus-pthread_sigmask-before-Popen-through-"
            "reap-ESRCH-local-close"
        ),
        "post_reap_process_group_signaling": False,
        "process_group_grace_seconds": 1.0,
        "process_group_probe_interval_seconds": 0.01,
        "receipt_bytes": 65_536,
        "python_thread_premise": "main-thread-and-one-enumerated-Python-thread",
        "sigchld_child_ownership": (
            "explicit-SIG_DFL-reset-before-first-Popen-and-"
            "verified-before-each-Popen;requires-no-external-or-native-waiter"
        ),
        "validation_timeout_seconds": 300,
    },
    "scope": (
        "premise-explicit application-visible limits; not a hard RSS or "
        "child-process allocation bound"
    ),
}

HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
RUNNER_CHECKER_HASH = re.compile(
    rb'^readonly CHECKER_SHA256="([0-9a-f]{64})"$', re.MULTILINE
)
RUNNER_SELF_TEST_HASH = re.compile(
    rb'^readonly SELF_TEST_SHA256="([0-9a-f]{64})"$', re.MULTILINE
)
RUNNER_CHECKER_SIZE = re.compile(
    rb'^readonly CHECKER_SIZE="([0-9]+)"$', re.MULTILINE
)
RUNNER_SELF_TEST_SIZE = re.compile(
    rb'^readonly SELF_TEST_SIZE="([0-9]+)"$', re.MULTILINE
)
RUNNER_MAX_SOURCE_SIZE = re.compile(
    rb'^readonly MAX_SOURCE_SIZE="([0-9]+)"$', re.MULTILINE
)
CHECKER_CERTIFIED_CLAIM_BLOB = re.compile(
    rb'(?P<prefix>    CERTIFIED_CLAIM_CHECKER_RELATIVE: \(\n'
    rb'        "100644",\n'
    rb'        )(?P<size>[0-9_]+)'
    rb'(?P<middle>,\n        ")'
    rb'(?P<sha256>[0-9a-f]{64})'
    rb'(?P<suffix>",\n    \),)'
)
CHECKER_PINNED_CHANGED_PROJECTION = re.compile(
    rb'(?P<prefix>EXPECTED_PINNED_CHANGED_PROJECTION_SHA256 = \(\n    ")'
    rb'(?P<sha256>[0-9a-f]{64})'
    rb'(?P<suffix>"\n\))'
)
ZERO_HASH = "0" * 64
GIT_PROCESS_TIMEOUT_SECONDS = 60
TARGET_PROCESS_TIMEOUT_SECONDS = 180
SUPERVISOR_SELF_TEST_TIMEOUT_SECONDS = 3_600
MAX_PROCESS_OUTPUT_BYTES = 8 * 1024 * 1024
MAX_SUPERVISOR_RECEIPT_BYTES = 2 * 1024 * 1024
PROCESS_TERMINATION_GRACE_SECONDS = 1.0
PROCESS_GROUP_PROBE_INTERVAL_SECONDS = 0.01
MAX_EXACT_SOURCE_BYTES = 256 * 1024
MAX_SELF_TEST_PACK_BYTES = 64 * 1024 * 1024

SIGCHLD_OWNERSHIP_BOOTSTRAP = r"""
from __future__ import annotations
import hashlib
import os
import signal
import subprocess
import sys
import time

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    raise SystemExit("SIGCHLD ownership control requires Python -I -S")
if len(sys.argv) != 5:
    raise SystemExit("SIGCHLD ownership control arguments are incomplete")
root, relative, expected_size_raw, expected_sha256 = sys.argv[1:]
try:
    expected_size = int(expected_size_raw, 10)
except ValueError:
    raise SystemExit("SIGCHLD ownership control size is malformed") from None
body = sys.stdin.buffer.read(expected_size + 1)
if (
    expected_size <= 0
    or str(expected_size) != expected_size_raw
    or len(body) != expected_size
    or hashlib.sha256(body).hexdigest() != expected_sha256
):
    raise SystemExit("SIGCHLD ownership control source capture changed")

# Retain the exact counterexample: with inherited SIG_IGN, the kernel can reap
# the child while Popen.returncode remains None.  Probe only with signal zero.
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
real_popen = subprocess.Popen
pre_reset = real_popen(
    [sys.executable, "-I", "-S", "-c", "pass"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)
counterexample_deadline = time.monotonic() + 5.0
while True:
    try:
        os.killpg(pre_reset.pid, 0)
    except ProcessLookupError:
        break
    except PermissionError:
        # Darwin can report transient EPERM while dismantling the auto-reaped
        # group.  This is indeterminate; continue only to explicit ESRCH.
        pass
    if time.monotonic() >= counterexample_deadline:
        raise SystemExit("SIGCHLD=SIG_IGN counterexample did not auto-reap")
    time.sleep(0.001)
if pre_reset.returncode is not None:
    raise SystemExit("SIGCHLD=SIG_IGN counterexample lost stale returncode")
pre_reset.wait(timeout=1.0)

def disposition_guarded_popen(*arguments, **keywords):
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise RuntimeError("exact source attempted Popen before SIGCHLD reset")
    return real_popen(*arguments, **keywords)

subprocess.Popen = disposition_guarded_popen

module_name = "_pid_rs_sigchld_" + relative.replace("/", "_").replace(".", "_")
module = type(sys)(module_name)
module.__file__ = os.path.join(root, relative)
module.__loader__ = None
module.__spec__ = None
module.__cached__ = None
sys.modules[module_name] = module
exec(compile(body, module.__file__, "exec"), module.__dict__)
if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
    raise SystemExit("exact source did not reset SIGCHLD to SIG_DFL")
module.require_sigchld_default()

post_reset = subprocess.Popen(
    [sys.executable, "-I", "-S", "-c", "pass"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)
try:
    waited_pid, waited_status = os.waitpid(post_reset.pid, 0)
except ChildProcessError as error:
    raise SystemExit(
        "SIGCHLD reset did not restore waitable-child ownership"
    ) from error
if waited_pid != post_reset.pid:
    raise SystemExit("SIGCHLD reset waitpid returned the wrong child")
if post_reset.returncode is not None:
    raise SystemExit("direct-waitpid counterexample lost stale Popen returncode")
# A direct waiter can reap despite stale Popen.returncode; production excludes
# external/native waiters as a premise rather than inferring ownership from it.
post_reset.returncode = os.waitstatus_to_exitcode(waited_status)
if post_reset.returncode != 0:
    raise SystemExit("SIGCHLD reset child did not exit successfully")
if relative.endswith("self-test.py"):
    module.require_process_group_absent_after_reap(
        post_reset,
        operation="SIGCHLD ownership control",
    )
else:
    module.require_process_group_absent_after_reap(
        post_reset,
        label="SIGCHLD ownership control",
    )
sys.stdout.write("SIGCHLD_OWNERSHIP_OK:" + relative + "\n")
"""

CHECKER_SIGNAL_CUSTODY_BOOTSTRAP = r"""
from __future__ import annotations
import hashlib
import os
import signal
import subprocess
import sys
import time

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    raise SystemExit("checker signal-custody control requires Python -I -S")
if len(sys.argv) != 6:
    raise SystemExit("checker signal-custody control arguments are incomplete")
root, relative, expected_size_raw, expected_sha256, control = sys.argv[1:]
try:
    expected_size = int(expected_size_raw, 10)
except ValueError:
    raise SystemExit("checker signal-custody control size is malformed") from None
body = sys.stdin.buffer.read(expected_size + 1)
if (
    expected_size <= 0
    or str(expected_size) != expected_size_raw
    or len(body) != expected_size
    or hashlib.sha256(body).hexdigest() != expected_sha256
):
    raise SystemExit("checker signal-custody control source capture changed")
if not all(
    hasattr(signal, name)
    for name in ("raise_signal", "setitimer", "ITIMER_REAL", "pthread_sigmask")
):
    raise SystemExit("checker signal-custody control requires POSIX signals")

module_name = "_pid_rs_checker_signal_custody_" + control
module = type(sys)(module_name)
module.__file__ = os.path.join(root, relative)
module.__loader__ = None
module.__spec__ = None
module.__cached__ = None
sys.modules[module_name] = module
exec(compile(body, module.__file__, "exec"), module.__dict__)

real_popen = subprocess.Popen
real_selector_factory = module.selectors.DefaultSelector
captured = []
tracked_selectors = []
timer_armed = False

class TrackingSelector:
    def __init__(self):
        self.inner = real_selector_factory()
        self.closed = False
        tracked_selectors.append(self)

    def register(self, *arguments, **keywords):
        return self.inner.register(*arguments, **keywords)

    def unregister(self, *arguments, **keywords):
        return self.inner.unregister(*arguments, **keywords)

    def select(self, *arguments, **keywords):
        return self.inner.select(*arguments, **keywords)

    def get_map(self):
        return self.inner.get_map()

    def close(self):
        try:
            return self.inner.close()
        finally:
            self.closed = True

module.selectors.DefaultSelector = TrackingSelector

def assert_complete_cleanup(child):
    if child.returncode is None:
        raise SystemExit("signal-custody control child leader was not reaped")
    for stream in (child.stdin, child.stdout, child.stderr):
        if stream is not None and not stream.closed:
            raise SystemExit("signal-custody control retained an open child pipe")
    deadline = time.monotonic() + 2.0
    while True:
        try:
            os.killpg(child.pid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            pass
        if time.monotonic() >= deadline:
            raise SystemExit(
                "signal-custody control could not prove process-group ESRCH"
            )
        time.sleep(0.001)

def launch_then_raise(selected_signal):
    def injected(*arguments, **keywords):
        child = real_popen(*arguments, **keywords)
        captured.append(child)
        signal.raise_signal(selected_signal)
        return child
    return injected

def launch_sleeper_then_arm(*_arguments, **keywords):
    global timer_armed
    child = real_popen(
        [sys.executable, "-I", "-S", "-c", "import time; time.sleep(0.1)"],
        **keywords,
    )
    captured.append(child)
    signal.setitimer(signal.ITIMER_REAL, 0.02)
    timer_armed = True
    return child

def complete_preactive_control():
    sys.stdout.write("CHECKER_SIGNAL_CUSTODY_OK:" + control + "\n")
    raise SystemExit(0)

if control == "activation_partial_install":
    original_handlers = (
        signal.getsignal(signal.SIGALRM),
        signal.getsignal(signal.SIGINT),
    )
    real_signal = module.signal.signal
    tripped = [False]
    calls = []
    def partial_install(selected, handler):
        calls.append((selected, handler))
        result = real_signal(selected, handler)
        if (
            selected == signal.SIGINT
            and handler is module.verifier_signal_handler
            and not tripped[0]
        ):
            tripped[0] = True
            raise OSError("injected partial handler installation")
        return result
    module.signal.signal = partial_install
    try:
        try:
            module.activate_verifier_signal_runtime()
        except OSError as error:
            if str(error) != "injected partial handler installation":
                raise
        else:
            raise SystemExit("partial handler installation did not fail")
    finally:
        module.signal.signal = real_signal
    if (
        not tripped[0]
        or len(calls) != 4
        or signal.getsignal(signal.SIGALRM) != original_handlers[0]
        or signal.getsignal(signal.SIGINT) != original_handlers[1]
        or module.VERIFIER_SIGNAL_RUNTIME_ACTIVE
        or module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 0
    ):
        raise SystemExit("partial handler installation did not restore both dispositions")
    complete_preactive_control()

if control == "deactivation_independent_restore":
    previous = module.activate_verifier_signal_runtime()
    real_signal = module.signal.signal
    tripped = [False]
    calls = []
    def fail_first_restore(selected, handler):
        calls.append((selected, handler))
        result = real_signal(selected, handler)
        if selected == signal.SIGALRM and handler == previous[0] and not tripped[0]:
            tripped[0] = True
            raise OSError("injected first handler restoration failure")
        return result
    module.signal.signal = fail_first_restore
    try:
        observed_restore = module.deactivate_verifier_signal_runtime(
            previous, primary_error=None
        )
    finally:
        module.signal.signal = real_signal
    if (
        not isinstance(observed_restore, OSError)
        or len(calls) != 4
        or signal.getsignal(signal.SIGALRM) is not module.verifier_signal_handler
        or signal.getsignal(signal.SIGINT) is not module.verifier_signal_handler
        or not module.VERIFIER_SIGNAL_RUNTIME_ACTIVE
    ):
        raise SystemExit("handler deactivation did not attempt both and roll back")
    if module.deactivate_verifier_signal_runtime(previous, primary_error=None) is not None:
        raise SystemExit("handler deactivation recovery failed")
    complete_preactive_control()

if control == "timer_disarm_failure":
    original_handlers = (
        signal.getsignal(signal.SIGALRM),
        signal.getsignal(signal.SIGINT),
    )
    real_setitimer = module.signal.setitimer
    real_run_validation = module.run_validation
    disarm_failed = [False]
    calls = []
    def setitimer_then_fail(which, seconds, interval=0.0):
        result = real_setitimer(which, seconds, interval)
        calls.append(seconds)
        if seconds == 0 and not disarm_failed[0]:
            disarm_failed[0] = True
            raise OSError("injected timer disarm failure after zeroing")
        return result
    module.signal.setitimer = setitimer_then_fail
    module.run_validation = lambda _resources: 0
    try:
        try:
            module.main()
        except OSError as error:
            if str(error) != "injected timer disarm failure after zeroing":
                raise
        else:
            raise SystemExit("timer disarm failure control did not fail")
    finally:
        module.signal.setitimer = real_setitimer
        module.run_validation = real_run_validation
    if (
        calls != [module.VALIDATION_TIMEOUT_SECONDS, 0]
        or signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0)
        or signal.getsignal(signal.SIGALRM) is not module.verifier_signal_handler
        or signal.getsignal(signal.SIGINT) is not module.verifier_signal_handler
        or not module.VERIFIER_SIGNAL_RUNTIME_ACTIVE
    ):
        raise SystemExit("timer disarm failure restored a raising handler prematurely")
    if module.deactivate_verifier_signal_runtime(original_handlers, primary_error=None) is not None:
        raise SystemExit("timer disarm control handler recovery failed")
    complete_preactive_control()

previous_handlers = module.activate_verifier_signal_runtime()
observed = None
primary = None
expected_signals = frozenset()
expected_selector_count = None
try:
    resources = module.ResourceLedger.start()
    if control == "mask_side_effect_raise":
        real_pthread_sigmask = module.signal.pthread_sigmask
        tripped = [False]
        def block_then_raise(operation, selected):
            result = real_pthread_sigmask(operation, selected)
            if (
                operation == signal.SIG_BLOCK
                and set(selected) == {signal.SIGALRM, signal.SIGINT}
                and not tripped[0]
            ):
                tripped[0] = True
                raise OSError("injected block side effect")
            return result
        module.signal.pthread_sigmask = block_then_raise
        try:
            try:
                module.OwnedChildSignalMask.acquire(
                    label="checker side-effect-then-raise mask control"
                )
            except OSError as error:
                if str(error) != "injected block side effect":
                    raise
            else:
                raise SystemExit("mask side-effect control did not fail")
        finally:
            module.signal.pthread_sigmask = real_pthread_sigmask
        if (
            not tripped[0]
            or module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 0
            or module.VERIFIER_SIGNAL_MASK_STATE_INDETERMINATE
            or module.owned_child_exception_signals().intersection(
                module.current_thread_signal_mask()
            )
        ):
            raise SystemExit("mask side-effect control did not roll back exactly")
        expected_signals = frozenset()
        expected_selector_count = 0
    elif control == "nested_mask_lifo":
        outer = module.OwnedChildSignalMask.acquire(label="checker outer mask control")
        inner = module.OwnedChildSignalMask.acquire(label="checker inner mask control")
        try:
            outer.restore()
        except module.FollowupError as error:
            if "not LIFO" not in str(error):
                raise
        else:
            raise SystemExit("out-of-order mask restoration was accepted")
        if (
            not outer.held
            or not inner.held
            or module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 2
        ):
            raise SystemExit("out-of-order mask restoration changed live ownership")
        inner.restore()
        outer.restore()
        if module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 0:
            raise SystemExit("nested LIFO mask restoration retained ownership")
        expected_signals = frozenset()
        expected_selector_count = 0
    elif control == "cat_constructor_sigalrm":
        subprocess.Popen = launch_then_raise(signal.SIGALRM)
        try:
            with module.GitCatFileSession(resources, cwd=module.Path(root)):
                pass
        except module.FollowupError as error:
            observed = error
        else:
            raise SystemExit("cat constructor SIGALRM control did not fail safely")
        if str(observed) != (
            "validation exceeded the "
            + str(module.VALIDATION_TIMEOUT_SECONDS)
            + "-second deadline"
        ):
            raise SystemExit("cat constructor SIGALRM control raised the wrong error")
        expected_signals = frozenset((signal.SIGALRM,))
        expected_selector_count = 1
    elif control == "git_process_sigint":
        subprocess.Popen = launch_then_raise(signal.SIGINT)
        try:
            module.git_process(
                "version",
                resources=resources,
                stdout_limit=4096,
                stderr_limit=4096,
                input_limit=0,
                timeout_seconds=5,
                cwd=module.Path(root),
            )
        except KeyboardInterrupt as error:
            observed = error
        else:
            raise SystemExit("git_process SIGINT control did not fail safely")
        expected_signals = frozenset((signal.SIGINT,))
        expected_selector_count = 1
    elif control == "pending_timer_cleanup":
        subprocess.Popen = launch_sleeper_then_arm
        try:
            module.git_process(
                "version",
                resources=resources,
                stdout_limit=4096,
                stderr_limit=4096,
                input_limit=0,
                timeout_seconds=5,
                cwd=module.Path(root),
            )
        except module.FollowupError as error:
            observed = error
        else:
            raise SystemExit("pending timer control did not fail safely")
        if str(observed) != (
            "validation exceeded the "
            + str(module.VALIDATION_TIMEOUT_SECONDS)
            + "-second deadline"
        ):
            raise SystemExit("pending timer control raised the wrong error")
        expected_signals = frozenset((signal.SIGALRM,))
        expected_selector_count = 1
    elif control == "pre_acquire_sigalrm":
        def forbidden_popen(*_arguments, **_keywords):
            raise SystemExit("pre-acquire SIGALRM control reached Popen")
        subprocess.Popen = forbidden_popen
        signal.raise_signal(signal.SIGALRM)
        try:
            module.git_process(
                "version",
                resources=resources,
                stdout_limit=4096,
                stderr_limit=4096,
                input_limit=0,
                timeout_seconds=5,
                cwd=module.Path(root),
            )
        except module.FollowupError as error:
            observed = error
        else:
            raise SystemExit("pre-acquire SIGALRM control launched a child")
        if str(observed) != (
            "validation exceeded the "
            + str(module.VALIDATION_TIMEOUT_SECONDS)
            + "-second deadline"
        ):
            raise SystemExit("pre-acquire SIGALRM control raised the wrong error")
        expected_signals = frozenset((signal.SIGALRM,))
        expected_selector_count = 0
    elif control == "multiple_signal_priority":
        def forbidden_popen(*_arguments, **_keywords):
            raise SystemExit("multiple-signal control reached Popen")
        subprocess.Popen = forbidden_popen
        for selected_signal in (
            signal.SIGALRM,
            signal.SIGALRM,
            signal.SIGINT,
            signal.SIGALRM,
            signal.SIGINT,
        ):
            signal.raise_signal(selected_signal)
        try:
            module.git_process(
                "version",
                resources=resources,
                stdout_limit=4096,
                stderr_limit=4096,
                input_limit=0,
                timeout_seconds=5,
                cwd=module.Path(root),
            )
        except KeyboardInterrupt as error:
            observed = error
        else:
            raise SystemExit("multiple-signal control did not prefer SIGINT")
        expected_signals = frozenset((signal.SIGALRM, signal.SIGINT))
        expected_selector_count = 0
    elif control == "selector_primary_sigalrm":
        subprocess.Popen = launch_then_raise(signal.SIGALRM)

        def failing_selector_factory():
            raise RuntimeError("injected selector construction failure")

        module.selectors.DefaultSelector = failing_selector_factory
        try:
            module.GitCatFileSession(resources, cwd=module.Path(root))
        except module.FollowupError as error:
            observed = error
        else:
            raise SystemExit("selector-primary control did not retain its error")
        if str(observed) != (
            "Git cat-file --batch-command selector setup failed: "
            "injected selector construction failure"
        ):
            raise SystemExit("selector-primary control raised the wrong error")
        expected_note = (
            "deferred verifier signals observed after child cleanup: SIGALRM"
        )
        if expected_note not in getattr(observed, "__notes__", ()):
            raise SystemExit("selector-primary control lost its signal note")
        expected_signals = frozenset((signal.SIGALRM,))
        expected_selector_count = 0
    else:
        raise SystemExit("unknown checker signal-custody control")
    expected_child_count = (
        0
        if control in {
            "mask_side_effect_raise",
            "nested_mask_lifo",
            "pre_acquire_sigalrm",
            "multiple_signal_priority",
        }
        else 1
    )
    if len(captured) != expected_child_count:
        raise SystemExit("signal-custody control launched the wrong child count")
    if captured:
        assert_complete_cleanup(captured[0])
    if module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 0:
        raise SystemExit("signal-custody control retained a mask scope")
    if module.owned_child_exception_signals().intersection(
        module.current_thread_signal_mask()
    ):
        raise SystemExit("signal-custody control retained a blocked signal")
    if expected_selector_count is None or len(tracked_selectors) != expected_selector_count:
        raise SystemExit("signal-custody control created the wrong selector count")
    if any(not tracked.closed for tracked in tracked_selectors):
        raise SystemExit("signal-custody control retained an open selector")
    if frozenset(module.deferred_verifier_signals()) != expected_signals:
        raise SystemExit("signal-custody control changed terminal signal coalescing")
except BaseException as error:
    primary = error
    raise
finally:
    subprocess.Popen = real_popen
    module.selectors.DefaultSelector = real_selector_factory
    if timer_armed:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
            if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
                raise RuntimeError("signal-control timer did not disarm")
        except BaseException as timer_error:
            initiating = primary or observed
            if initiating is not None:
                module.add_secondary_exception_note(
                    initiating, "signal-control timer disarm failed", timer_error
                )
                raise initiating
            raise
    deferred_error = module.deactivate_verifier_signal_runtime(
        previous_handlers,
        primary_error=primary or observed,
    )
    if deferred_error is not None and primary is None and observed is None:
        raise deferred_error

sys.stdout.write("CHECKER_SIGNAL_CUSTODY_OK:" + control + "\n")
"""

SELFTEST_SIGNAL_CUSTODY_BOOTSTRAP = r"""
from __future__ import annotations
import hashlib
import os
import signal
import subprocess
import sys
import time

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    raise SystemExit("self-test signal-custody control requires Python -I -S")
if len(sys.argv) != 5:
    raise SystemExit("self-test signal-custody control arguments are incomplete")
root, relative, expected_size_raw, expected_sha256 = sys.argv[1:]
try:
    expected_size = int(expected_size_raw, 10)
except ValueError:
    raise SystemExit("self-test signal-custody control size is malformed") from None
body = sys.stdin.buffer.read(expected_size + 1)
if (
    expected_size <= 0
    or str(expected_size) != expected_size_raw
    or len(body) != expected_size
    or hashlib.sha256(body).hexdigest() != expected_sha256
):
    raise SystemExit("self-test signal-custody control source capture changed")
if not all(
    hasattr(signal, name)
    for name in ("raise_signal", "pthread_sigmask", "SIGALRM", "SIGINT")
):
    raise SystemExit("self-test signal-custody control requires POSIX signals")

module_name = "_pid_rs_selftest_signal_custody"
module = type(sys)(module_name)
module.__file__ = os.path.join(root, relative)
module.__loader__ = None
module.__spec__ = None
module.__cached__ = None
sys.modules[module_name] = module
exec(compile(body, module.__file__, "exec"), module.__dict__)

real_popen = module.subprocess.Popen
real_selector_factory = module.selectors.DefaultSelector
real_temporary_file = module.tempfile.TemporaryFile
real_pthread_sigmask = module.signal.pthread_sigmask
captured = []
tracked_selectors = []
tracked_input_files = []

class TrackingSelector:
    def __init__(self):
        self.inner = real_selector_factory()
        self.closed = False
        tracked_selectors.append(self)

    def register(self, *arguments, **keywords):
        return self.inner.register(*arguments, **keywords)

    def unregister(self, *arguments, **keywords):
        return self.inner.unregister(*arguments, **keywords)

    def select(self, *arguments, **keywords):
        return self.inner.select(*arguments, **keywords)

    def get_map(self):
        return self.inner.get_map()

    def close(self):
        try:
            return self.inner.close()
        finally:
            self.closed = True

def assert_unowned_runtime_state(label):
    if module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 0:
        raise SystemExit(label + " retained a mask scope")
    if module.owned_child_exception_signals().intersection(
        module.current_thread_signal_mask()
    ):
        raise SystemExit(label + " retained a blocked signal")

def assert_complete_cleanup(child):
    if child.returncode is None:
        raise SystemExit("self-test signal control child leader was not reaped")
    for stream in (child.stdin, child.stdout, child.stderr):
        if stream is not None and not stream.closed:
            raise SystemExit("self-test signal control retained an open child pipe")
    deadline = time.monotonic() + 2.0
    while True:
        try:
            os.killpg(child.pid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            pass
        if time.monotonic() >= deadline:
            raise SystemExit("self-test signal control could not prove group ESRCH")
        time.sleep(0.001)

previous_handlers = module.activate_verifier_signal_runtime()
observed = None
primary = None
try:
    original_init = module.OwnedChildSignalMask.__init__

    def fail_capability_construction(self, **_keywords):
        raise MemoryError("injected capability construction failure")

    module.OwnedChildSignalMask.__init__ = fail_capability_construction
    try:
        module.OwnedChildSignalMask.acquire(
            label="self-test injected capability-construction control"
        )
    except MemoryError as error:
        if str(error) != "injected capability construction failure":
            raise
    else:
        raise SystemExit("capability-construction control did not fail")
    finally:
        module.OwnedChildSignalMask.__init__ = original_init
    assert_unowned_runtime_state("capability-construction control")

    retained_ownership = module.OwnedChildSignalMask.acquire(
        label="self-test injected mask-restoration control"
    )

    def fail_setmask(operation, selected):
        if operation == signal.SIG_SETMASK:
            raise OSError("injected mask restoration failure")
        return real_pthread_sigmask(operation, selected)

    module.signal.pthread_sigmask = fail_setmask
    try:
        retained_ownership.restore()
    except module.SelfTestError as error:
        if "injected mask restoration failure" not in str(error):
            raise
    else:
        raise SystemExit("mask-restoration control did not fail")
    finally:
        module.signal.pthread_sigmask = real_pthread_sigmask
    if (
        not retained_ownership.held
        or module.OWNED_CHILD_SIGNAL_MASK_DEPTH != 1
        or not module.owned_child_exception_signals().issubset(
            module.current_thread_signal_mask()
        )
    ):
        raise SystemExit("failed restoration discarded its live capability")
    retained_ownership.restore()
    assert_unowned_runtime_state("mask-restoration recovery control")

    def fail_input_fixture_allocation(*_arguments, **_keywords):
        raise MemoryError("injected input fixture allocation failure")

    module.tempfile.TemporaryFile = fail_input_fixture_allocation
    try:
        module.process(
            [sys.executable, "-I", "-S", "-c", "pass"],
            cwd=module.Path(root),
            input_bytes=b"fixture",
            timeout_seconds=5.0,
            maximum_output_bytes=4096,
        )
    except MemoryError as error:
        if str(error) != "injected input fixture allocation failure":
            raise
    else:
        raise SystemExit("input-allocation control did not fail")
    finally:
        module.tempfile.TemporaryFile = real_temporary_file
    assert_unowned_runtime_state("input-allocation control")

    def tracking_temporary_file(*arguments, **keywords):
        handle = real_temporary_file(*arguments, **keywords)
        tracked_input_files.append(handle)
        return handle

    def launch_then_raise(*arguments, **keywords):
        child = real_popen(*arguments, **keywords)
        captured.append(child)
        signal.raise_signal(signal.SIGALRM)
        return child

    module.tempfile.TemporaryFile = tracking_temporary_file
    module.selectors.DefaultSelector = TrackingSelector
    module.subprocess.Popen = launch_then_raise
    try:
        module.process(
            [
                sys.executable,
                "-I",
                "-S",
                "-c",
                (
                    "import sys; data = sys.stdin.buffer.read(); "
                    "raise SystemExit(data != b'fixture')"
                ),
            ],
            cwd=module.Path(root),
            input_bytes=b"fixture",
            timeout_seconds=5.0,
            maximum_output_bytes=4096,
        )
    except module.SelfTestError as error:
        observed = error
    else:
        raise SystemExit("self-test constructor-gap control did not fail safely")
    if str(observed) != "self-test received deferred signals: SIGALRM":
        raise SystemExit("self-test constructor-gap control raised the wrong error")
    if len(captured) != 1:
        raise SystemExit("self-test constructor-gap control launched the wrong count")
    assert_complete_cleanup(captured[0])
    if len(tracked_selectors) != 1 or not tracked_selectors[0].closed:
        raise SystemExit("self-test constructor-gap control retained its selector")
    if len(tracked_input_files) != 1 or not tracked_input_files[0].closed:
        raise SystemExit("self-test constructor-gap control retained its input file")
    assert_unowned_runtime_state("self-test constructor-gap control")
    if module.deferred_verifier_signals() != (signal.SIGALRM,):
        raise SystemExit("self-test constructor-gap control lost its signal")
except BaseException as error:
    primary = error
    raise
finally:
    module.subprocess.Popen = real_popen
    module.selectors.DefaultSelector = real_selector_factory
    module.tempfile.TemporaryFile = real_temporary_file
    module.signal.pthread_sigmask = real_pthread_sigmask
    deferred_error = module.deactivate_verifier_signal_runtime(
        previous_handlers,
        primary_error=primary or observed,
    )
    if deferred_error is not None and primary is None and observed is None:
        raise deferred_error

sys.stdout.write("SELFTEST_SIGNAL_CUSTODY_OK\n")
"""

DIRECT_EXACT_BOOTSTRAP = r"""
from __future__ import annotations
import hashlib
import os
import stat
import sys

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    raise SystemExit("direct exact-source bootstrap requires Python -I -S")
if len(sys.argv) < 6:
    raise SystemExit("direct exact-source bootstrap arguments are incomplete")
root, relative, expected_sha256, expected_size_raw, maximum_size_raw, *target_arguments = sys.argv[1:]
parts = relative.split("/")
try:
    expected_size = int(expected_size_raw)
    maximum_size = int(maximum_size_raw)
except ValueError:
    raise SystemExit("direct exact-source bootstrap size arguments are invalid") from None
if (
    not relative
    or relative.startswith("/")
    or any(part in {"", ".", ".."} for part in parts)
    or len(expected_sha256) != 64
    or any(character not in "0123456789abcdef" for character in expected_sha256)
    or str(expected_size) != expected_size_raw
    or str(maximum_size) != maximum_size_raw
    or expected_size <= 0
    or maximum_size <= 0
    or expected_size > maximum_size
):
    raise SystemExit("direct exact-source bootstrap arguments are invalid")
if not all(
    hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
):
    raise SystemExit(
        "direct exact-source bootstrap requires POSIX no-follow/nonblocking descriptors"
    )

directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
leaf_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK

def close_one(file_descriptor, primary):
    if file_descriptor is None:
        return primary
    try:
        os.close(file_descriptor)
    except BaseException as error:
        if primary is None:
            return error
        try:
            primary.add_note("additional direct exact-source close failed")
        except BaseException:
            pass
    return primary

def read_declared(file_descriptor, expected_bytes):
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    chunks = []
    remaining = expected_bytes
    while remaining:
        chunk = os.read(file_descriptor, min(1024 * 1024, remaining))
        if not chunk:
            raise RuntimeError("direct exact-source leaf is shorter than its exact bound")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(file_descriptor, 1):
        raise RuntimeError("direct exact-source leaf size is outside its exact bound")
    return b"".join(chunks)

def identity(metadata):
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )

descriptor = None
following = None
leaf = None
primary_error = None
try:
    descriptor = os.open(root, directory_flags)
    for component in parts[:-1]:
        following = os.open(component, directory_flags, dir_fd=descriptor)
        previous_descriptor = descriptor
        descriptor = following
        following = None
        close_error = close_one(previous_descriptor, None)
        if close_error is not None:
            raise RuntimeError("direct exact-source directory close failed") from close_error
    leaf = os.open(parts[-1], leaf_flags, dir_fd=descriptor)
    before = os.fstat(leaf)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise RuntimeError("direct exact-source leaf is not a single-linked regular file")
    if stat.S_IMODE(before.st_mode) not in {0o644, 0o755}:
        raise RuntimeError("direct exact-source leaf mode is noncanonical")
    if before.st_size != expected_size or before.st_size > maximum_size:
        raise RuntimeError("direct exact-source leaf size is outside its exact bound")
    first = read_declared(leaf, expected_size)
    middle = os.fstat(leaf)
    second = read_declared(leaf, expected_size)
    after = os.fstat(leaf)
    if (
        identity(before) != identity(middle)
        or identity(middle) != identity(after)
        or len(first) != expected_size
        or first != second
    ):
        raise RuntimeError("direct exact-source leaf changed during capture")
    if hashlib.sha256(first).hexdigest() != expected_sha256:
        raise RuntimeError("direct exact-source leaf digest mismatch")
    source_name = os.path.join(root, relative)
    code = compile(first, source_name, "exec", dont_inherit=True, optimize=sys.flags.optimize)
    namespace = {
        "__builtins__": __builtins__,
        "__cached__": None,
        "__file__": source_name,
        "__loader__": None,
        "__name__": "__main__",
        "__package__": None,
        "__pid_rs_exact_source_context__": {
            "optimize": sys.flags.optimize,
            "relative": relative,
            "sha256": expected_sha256,
            "size": expected_size,
        },
        "__spec__": None,
    }
    sys.argv = [source_name, *target_arguments]
    pending = None
    try:
        exec(code, namespace, namespace)
    except BaseException:
        pending = sys.exc_info()
    endpoint_metadata = os.fstat(leaf)
    endpoint = read_declared(leaf, expected_size)
    if (
        identity(endpoint_metadata) != identity(after)
        or len(endpoint) != expected_size
        or endpoint != first
    ):
        raise RuntimeError("direct exact-source leaf changed before execution returned")
    if pending is not None:
        _kind, value, traceback = pending
        raise value.with_traceback(traceback)
except BaseException as error:
    primary_error = error
    raise
finally:
    cleanup_error = primary_error
    cleanup_error = close_one(leaf, cleanup_error)
    cleanup_error = close_one(following, cleanup_error)
    cleanup_error = close_one(descriptor, cleanup_error)
    if primary_error is None and cleanup_error is not None:
        raise RuntimeError("direct exact-source descriptor cleanup failed") from cleanup_error
"""


class PythonMode(Enum):
    NORMAL = "normal"
    OPTIMIZED = "optimized"

    @property
    def interpreter_arguments(self) -> tuple[str, ...]:
        return () if self is PythonMode.NORMAL else ("-O",)


class ExpectedBoundary(Enum):
    CHECKER = "checker-rejected"
    ARGUMENT_PARSER = "argument-parser-rejected"
    PYTHON_PRECONDITION = "python-precondition-rejected"
    EXACT_SOURCE_SIZE = "exact-source-size-rejected"
    EXACT_SOURCE_DIGEST = "exact-source-digest-rejected"
    EXACT_SOURCE_ENDPOINT = "exact-source-endpoint-rejected"
    EXACT_SOURCE_PATH = "exact-source-path-rejected"
    RECEIPT_VALIDATOR = "receipt-validator-rejected"
    ISOLATED_EQUIVALENT = "isolated-and-equivalent"


class ProcessGroupState(Enum):
    ABSENT = "absent"
    PRESENT = "present"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class MutationCase:
    name: str
    mutation_target_family: str
    expected_boundary: ExpectedBoundary = ExpectedBoundary.CHECKER


MUTATION_CASES = (
    MutationCase("cli_no_external_custody", "cli_external_pair"),
    MutationCase("cli_tree_without_checkpoint", "cli_external_pair"),
    MutationCase("cli_checkpoint_without_tree", "cli_external_pair"),
    MutationCase("cli_pair_with_diagnostic", "cli_external_pair"),
    MutationCase("cli_malformed_tree", "cli_external_pair"),
    MutationCase("cli_malformed_checkpoint", "cli_external_pair"),
    MutationCase(
        "cli_unknown_argument",
        "cli_external_pair",
        ExpectedBoundary.ARGUMENT_PARSER,
    ),
    MutationCase("path_extra_untracked", "path_allowlist"),
    MutationCase("path_ignored_python_cache", "path_allowlist"),
    MutationCase("path_missing_added_receipt", "path_allowlist"),
    MutationCase("path_reverted_modified_agents", "path_allowlist"),
    MutationCase("protected_science_source", "protected_projection"),
    MutationCase("protected_formal_claim", "protected_projection"),
    MutationCase("protected_cargo_manifest", "protected_projection"),
    MutationCase("blob_agents", "allowed_blob"),
    MutationCase("blob_changelog", "allowed_blob"),
    MutationCase("blob_justfile", "allowed_blob"),
    MutationCase("blob_scripts_readme", "allowed_blob"),
    MutationCase("blob_correction_receipt", "allowed_blob"),
    MutationCase("blob_certified_claim_checker", "allowed_blob"),
    MutationCase("certified_claim_rebind_semantic", "claim_checker_rebind"),
    MutationCase("workflow_remove_libertinus_package", "workflow_semantics"),
    MutationCase("workflow_bypass_exact_source_runner", "workflow_semantics"),
    MutationCase("rust_remove_final_status_seam", "rust_regression"),
    MutationCase("rust_restore_shell_wrapper_route", "rust_regression"),
    MutationCase("historical_change_parent_pin", "historical_replay"),
    MutationCase("historical_change_status_digest", "historical_replay"),
    MutationCase("historical_remove_optimized_self_test", "historical_replay"),
    MutationCase(
        "source_checker_bytes",
        "exact_source_isolation",
        ExpectedBoundary.EXACT_SOURCE_SIZE,
    ),
    MutationCase(
        "source_self_test_bytes",
        "exact_source_isolation",
        ExpectedBoundary.EXACT_SOURCE_SIZE,
    ),
    MutationCase("source_runner_bytes", "candidate_tree_consistency"),
    MutationCase(
        "source_runner_checker_digest",
        "exact_source_isolation",
        ExpectedBoundary.EXACT_SOURCE_DIGEST,
    ),
    MutationCase(
        "source_runner_self_test_digest",
        "exact_source_isolation",
        ExpectedBoundary.EXACT_SOURCE_DIGEST,
    ),
    MutationCase(
        "source_checker_mid_execution_append",
        "exact_source_isolation",
        ExpectedBoundary.EXACT_SOURCE_ENDPOINT,
    ),
    MutationCase(
        "source_python_not_isolated",
        "exact_source_isolation",
        ExpectedBoundary.PYTHON_PRECONDITION,
    ),
    MutationCase(
        "source_python_site_enabled",
        "exact_source_isolation",
        ExpectedBoundary.PYTHON_PRECONDITION,
    ),
    MutationCase(
        "source_pythonpath_shadow",
        "exact_source_isolation",
        ExpectedBoundary.ISOLATED_EQUIVALENT,
    ),
    MutationCase("topology_checker_mode", "filesystem_topology"),
    MutationCase("topology_self_test_mode", "filesystem_topology"),
    MutationCase("topology_runner_mode", "filesystem_topology"),
    MutationCase(
        "topology_checker_symlink",
        "filesystem_topology",
        ExpectedBoundary.EXACT_SOURCE_PATH,
    ),
    MutationCase("topology_runner_hardlink", "filesystem_topology"),
    MutationCase("topology_untracked_fifo", "filesystem_topology"),
    MutationCase("topology_extra_empty_directory", "filesystem_topology"),
    MutationCase("index_assume_unchanged", "index_metadata_custody"),
    MutationCase("index_skip_worktree", "index_metadata_custody"),
    MutationCase("index_fsmonitor_extension", "index_metadata_custody"),
    MutationCase("index_split", "index_metadata_custody"),
    MutationCase("index_symlink", "index_metadata_custody"),
    MutationCase("index_hardlink", "index_metadata_custody"),
    MutationCase("lifecycle_full_candidate_index", "index_worktree_lifecycle"),
    MutationCase("lifecycle_single_staged_path", "index_worktree_lifecycle"),
    MutationCase("lifecycle_missing_worktree_path", "index_worktree_lifecycle"),
    MutationCase("lifecycle_committed_dirty", "index_worktree_lifecycle"),
    MutationCase("lifecycle_committed_untracked", "index_worktree_lifecycle"),
    MutationCase("lifecycle_committed_descendant", "index_worktree_lifecycle"),
    MutationCase("commit_wrong_parent", "commit_envelope"),
    MutationCase("commit_wrong_tree", "commit_envelope"),
    MutationCase("commit_wrong_message", "commit_envelope"),
    MutationCase("commit_wrong_identity", "commit_envelope"),
    MutationCase("commit_signature_header", "commit_envelope"),
    MutationCase("commit_merge_parents", "commit_envelope"),
    MutationCase("commit_descendant_checkpoint", "commit_envelope"),
    MutationCase("object_recursive_tree_hash_corruption", "git_object_integrity"),
    MutationCase("object_recursive_empty_tree", "git_object_integrity"),
    MutationCase("git_info_grafts", "git_context_overlay"),
    MutationCase("git_object_alternates", "git_context_overlay"),
    MutationCase("git_info_attributes", "git_context_overlay"),
    MutationCase("git_config_worktree", "git_context_overlay"),
    MutationCase("git_replacement_ref", "git_context_overlay"),
    MutationCase("git_local_include", "git_context_overlay"),
    MutationCase("git_local_filter", "git_context_overlay"),
    MutationCase("git_sparse_checkout_config", "git_context_overlay"),
    MutationCase("git_split_index_config", "git_context_overlay"),
    MutationCase("git_fsmonitor_config", "git_context_overlay"),
    MutationCase("git_untracked_cache_config", "git_context_overlay"),
    MutationCase("git_remote_promisor_config", "git_context_overlay"),
    MutationCase("git_promisor_pack_marker", "git_context_overlay"),
    MutationCase("resource_commit_object_bytes", "resource_bounds"),
    MutationCase("resource_tree_object_bytes", "resource_bounds"),
    MutationCase("resource_tree_aggregate_bytes", "resource_bounds"),
    MutationCase("resource_blob_object_bytes", "resource_bounds"),
    MutationCase("resource_blob_aggregate_bytes", "resource_bounds"),
    MutationCase("resource_worktree_file_bytes", "resource_bounds"),
    MutationCase("resource_worktree_aggregate_bytes", "resource_bounds"),
    MutationCase("resource_worktree_nodes", "resource_bounds"),
    MutationCase("resource_git_config_stdout", "resource_bounds"),
    MutationCase(
        "receipt_schema", "receipt_contract", ExpectedBoundary.RECEIPT_VALIDATOR
    ),
    MutationCase(
        "receipt_non_implications",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_path_count",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_anchor_projection",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_candidate_projection",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_allowlist_projection",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_full_candidate_projection",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_pinned_changed_projection",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_protected_projection",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_custody", "receipt_contract", ExpectedBoundary.RECEIPT_VALIDATOR
    ),
    MutationCase(
        "receipt_validation_class",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_repository_context",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_repository_index_type",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_repository_config_type",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_runtime_boundaries",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_git_tool_path",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_git_tool_version",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_python_tool_path",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_python_tool_version",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_external_status",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_diagnostic_identity",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
    MutationCase(
        "receipt_resource_bounds",
        "receipt_contract",
        ExpectedBoundary.RECEIPT_VALIDATOR,
    ),
)
EXPECTED_FAMILY_COUNTS = {
    "allowed_blob": 6,
    "candidate_tree_consistency": 1,
    "claim_checker_rebind": 1,
    "cli_external_pair": 7,
    "commit_envelope": 7,
    "exact_source_isolation": 8,
    "filesystem_topology": 7,
    "git_context_overlay": 13,
    "git_object_integrity": 2,
    "historical_replay": 3,
    "index_worktree_lifecycle": 6,
    "index_metadata_custody": 6,
    "path_allowlist": 4,
    "protected_projection": 3,
    "receipt_contract": 22,
    "resource_bounds": 9,
    "rust_regression": 2,
    "workflow_semantics": 2,
}
EXPECTED_MUTATION_COUNT = 109
EXPECTED_MUTATION_VERIFIER_TARGET_LAUNCHES = 88
EXPECTED_CHECKER_TARGET_LAUNCHES = 86
EXPECTED_SELF_TEST_TARGET_LAUNCHES = 2
EXPECTED_LOCAL_RECEIPT_CASES = 22
CHECKER_ERROR_PREFIX = b"ERROR: C3 hosted follow-up gate: "
PYTHON_PRECONDITION_ERROR = (
    b"ERROR: check-c3-hosted-followup.py requires Python -I -S\n"
)
ARGUMENT_PARSER_ERROR = (
    b"usage: check-c3-hosted-followup.py [-h]\n"
    b"                                   [--expected-candidate-tree "
    b"EXPECTED_CANDIDATE_TREE]\n"
    b"                                   [--checkpoint-commit CHECKPOINT_COMMIT]\n"
    b"                                   [--diagnostic-without-external-custody]\n"
    b"                                   [--maintenance-current-facts]\n"
    b"check-c3-hosted-followup.py: error: unrecognized arguments: "
    b"--hostile-unknown-option\n"
)
EXACT_SOURCE_DIGEST_ERROR_SUFFIXES = (
    b"RuntimeError: exact-source leaf digest mismatch\n",
    b"RuntimeError: direct exact-source leaf digest mismatch\n",
)
EXACT_SOURCE_SIZE_ERROR_SUFFIXES = (
    b"RuntimeError: exact-source leaf size differs from its frozen bound\n",
    b"RuntimeError: direct exact-source leaf size is outside its exact bound\n",
)
EXACT_SOURCE_ENDPOINT_ERROR_SUFFIXES = (
    b"RuntimeError: exact-source leaf changed before execution returned\n",
)

CHECKER_MARKER_GROUPS: tuple[tuple[bytes, frozenset[str]], ...] = (
    (
        b"creditable follow-up validation requires external tree/checkpoint custody",
        frozenset({"cli_no_external_custody"}),
    ),
    (
        b"external tree and checkpoint must be paired",
        frozenset({"cli_tree_without_checkpoint", "cli_checkpoint_without_tree"}),
    ),
    (
        b"diagnostic mode cannot accompany external custody",
        frozenset({"cli_pair_with_diagnostic"}),
    ),
    (b"external tree id is invalid", frozenset({"cli_malformed_tree"})),
    (b"checkpoint commit id is invalid", frozenset({"cli_malformed_checkpoint"})),
    (
        b"precommit follow-up partition differs from exact policy",
        frozenset(
            {
                "path_missing_added_receipt",
                "path_reverted_modified_agents",
                "protected_science_source",
                "protected_formal_claim",
                "protected_cargo_manifest",
            }
        ),
    ),
    (
        b"worktree contains ignored filesystem contamination",
        frozenset({"path_ignored_python_cache"}),
    ),
    (
        b"candidate inventory exceeds the path-count bound",
        frozenset({"path_extra_untracked", "lifecycle_committed_untracked"}),
    ),
    (
        b"follow-up full allowed-blob projection changed",
        frozenset(
            {
                "blob_agents",
                "blob_changelog",
                "blob_justfile",
                "blob_scripts_readme",
                "blob_correction_receipt",
                "blob_certified_claim_checker",
                "workflow_remove_libertinus_package",
                "workflow_bypass_exact_source_runner",
                "rust_remove_final_status_seam",
                "rust_restore_shell_wrapper_route",
                "historical_change_parent_pin",
                "historical_change_status_digest",
                "historical_remove_optimized_self_test",
                "topology_self_test_mode",
            }
        ),
    ),
    (
        b"certified claim checker rebind differs from three reviewed digest substitutions",
        frozenset({"certified_claim_rebind_semantic"}),
    ),
    (
        b"external tree differs from follow-up snapshot",
        frozenset({"source_runner_bytes"}),
    ),
    (
        b"follow-up checker is not executable",
        frozenset({"topology_checker_mode"}),
    ),
    (
        b"follow-up allowlist projection changed",
        frozenset({"topology_runner_mode"}),
    ),
    (
        b"worktree has a symlink, hardlink, or special node",
        frozenset({"topology_runner_hardlink", "topology_untracked_fifo"}),
    ),
    (
        b"worktree has an extra or empty directory",
        frozenset({"topology_extra_empty_directory"}),
    ),
    (
        b"Git index has a skip-worktree or assume-unchanged flag",
        frozenset({"index_assume_unchanged", "index_skip_worktree"}),
    ),
    (
        b"Git index contains fsmonitor, split-index, or sparse-index state",
        frozenset({"index_fsmonitor_extension", "index_split"}),
    ),
    (
        b"cannot observe the private Git index",
        frozenset({"index_symlink"}),
    ),
    (
        b"Git index must be a single-linked regular non-symlink file",
        frozenset({"index_hardlink"}),
    ),
    (
        b"Git index differs from HEAD",
        frozenset({"lifecycle_full_candidate_index", "lifecycle_single_staged_path"}),
    ),
    (
        b"filesystem and Git file inventories differ",
        frozenset({"lifecycle_missing_worktree_path"}),
    ),
    (
        b"committed follow-up filesystem has tracked, untracked, or ignored contamination",
        frozenset({"lifecycle_committed_dirty"}),
    ),
    (
        b"follow-up history is not one direct child",
        frozenset({"lifecycle_committed_descendant"}),
    ),
    (
        b"checkpoint parent differs from C3",
        frozenset({"commit_wrong_parent", "commit_descendant_checkpoint"}),
    ),
    (b"checkpoint commit tree differs", frozenset({"commit_wrong_tree"})),
    (b"checkpoint commit message differs", frozenset({"commit_wrong_message"})),
    (
        b"checkpoint author identity differs from reviewed human identity",
        frozenset({"commit_wrong_identity"}),
    ),
    (
        b"checkpoint commit header count changed",
        frozenset({"commit_signature_header", "commit_merge_parents"}),
    ),
    (
        b"Git tree object hash is inconsistent",
        frozenset({"object_recursive_tree_hash_corruption"}),
    ),
    (b"empty tree paths are forbidden", frozenset({"object_recursive_empty_tree"})),
    (
        b"Git overlay file is forbidden:",
        frozenset(
            {
                "git_info_grafts",
                "git_object_alternates",
                "git_info_attributes",
                "git_config_worktree",
            }
        ),
    ),
    (
        b"Git replacement references are forbidden",
        frozenset({"git_replacement_ref"}),
    ),
    (
        b"local Git configuration key is forbidden:",
        frozenset(
            {
                "git_local_include",
                "git_local_filter",
                "git_sparse_checkout_config",
                "git_split_index_config",
                "git_fsmonitor_config",
                "git_untracked_cache_config",
                "git_remote_promisor_config",
            }
        ),
    ),
    (
        b"Git promisor marker is forbidden:",
        frozenset({"git_promisor_pack_marker"}),
    ),
    (
        b"Git commit object exceeds the per-object byte bound",
        frozenset({"resource_commit_object_bytes"}),
    ),
    (
        b"Git tree object exceeds the per-object byte bound",
        frozenset({"resource_tree_object_bytes"}),
    ),
    (
        b"Git tree graph exceeds the aggregate byte bound",
        frozenset({"resource_tree_aggregate_bytes"}),
    ),
    (
        b"Git blob exceeds the per-object byte bound",
        frozenset({"resource_blob_object_bytes"}),
    ),
    (
        b"Git blob projection exceeds the aggregate byte bound",
        frozenset({"resource_blob_aggregate_bytes"}),
    ),
    (
        b"file exceeds the per-file byte bound",
        frozenset({"resource_worktree_file_bytes"}),
    ),
    (
        b"worktree snapshot exceeds the aggregate byte bound",
        frozenset({"resource_worktree_aggregate_bytes"}),
    ),
    (
        b"worktree topology exceeds the node bound",
        frozenset({"resource_worktree_nodes"}),
    ),
    (
        b"stdout exceeds the byte bound",
        frozenset({"resource_git_config_stdout"}),
    ),
)

EXPECTED_RECEIPT_REJECTION_MESSAGES = {
    "receipt_schema": "receipt authority fields changed",
    "receipt_non_implications": "receipt non-implications changed",
    "receipt_path_count": "receipt path counts or self-unhashed boundary changed",
    "receipt_anchor_projection": (
        "receipt anchor projection differs from immutable C3"
    ),
    "receipt_candidate_projection": (
        "receipt candidate projection differs from observed worktree"
    ),
    "receipt_allowlist_projection": (
        "receipt allowlist projection differs from observed worktree"
    ),
    "receipt_full_candidate_projection": (
        "receipt full-candidate projection differs from observed worktree"
    ),
    "receipt_pinned_changed_projection": (
        "receipt pinned-changed projection differs from observed worktree"
    ),
    "receipt_protected_projection": (
        "receipt protected projection differs from observed worktree"
    ),
    "receipt_custody": "receipt authority fields changed",
    "receipt_validation_class": "receipt authority fields changed",
    "receipt_repository_context": (
        "repository endpoint, Git version, non-shallow, promisor-routing, or object-scope claim changed"
    ),
    "receipt_repository_index_type": (
        "repository index receipt differs from exact index bytes"
    ),
    "receipt_repository_config_type": (
        "repository local config receipt differs from the effective local config record stream"
    ),
    "receipt_runtime_boundaries": "runtime boundary claims changed",
    "receipt_git_tool_path": "git receipt executable path changed",
    "receipt_git_tool_version": "git receipt version changed",
    "receipt_python_tool_path": "python receipt executable path changed",
    "receipt_python_tool_version": "python receipt version changed",
    "receipt_external_status": "receipt authority fields changed",
    "receipt_diagnostic_identity": (
        "diagnostic receipt must not declare reviewed human identity metadata"
    ),
    "receipt_resource_bounds": "receipt resource bounds changed",
}

HARNESS_CONTROL_NAMES = (
    "launch_failure_is_typed",
    "signal_failure_is_typed",
    "timeout_cleans_descendant_group",
    "output_overflow_cleans_process_group",
    "selftest_inherited_sigchld_ignore_is_normalized_before_spawn",
    "checker_inherited_sigchld_ignore_is_normalized_before_spawn",
    "selftest_transient_eperm_then_esrch_passes",
    "selftest_post_reap_present_fails_without_signal",
    "selftest_post_reap_indeterminate_fails_without_signal",
    "selftest_pre_reap_cleanup_signals_then_reaps",
    "checker_transient_eperm_then_esrch_passes",
    "checker_post_reap_present_fails_without_signal",
    "checker_post_reap_indeterminate_fails_without_signal",
    "checker_pre_reap_cleanup_signals_then_reaps",
    "checker_cat_file_abort_after_reap_is_signal_free",
    "checker_partial_signal_activation_restores_both_handlers",
    "checker_signal_deactivation_attempts_both_then_reinstalls_recorders",
    "checker_mask_side_effect_raise_rolls_back_kernel_mask",
    "checker_nested_mask_out_of_order_rejected_then_lifo_restores",
    "checker_timer_disarm_failure_retains_recorders",
    "checker_real_sigalrm_cat_constructor_deferred_until_cleanup",
    "checker_real_sigint_git_process_launch_deferred_until_cleanup",
    "checker_real_timer_pending_until_cleanup",
    "checker_real_sigalrm_before_acquire_refuses_launch",
    "selftest_mask_capability_construction_failure_rolls_back",
    "selftest_mask_restore_failure_retains_live_capability",
    "selftest_input_fixture_allocation_failure_restores_mask",
    "selftest_post_popen_sigalrm_cleans_child_selector_input",
    "checker_repeated_mixed_signals_coalesce_with_sigint_priority",
    "checker_primary_selector_error_retained_with_sigalrm_note",
    "arbitrary_nonzero_is_not_a_rejection",
    "malformed_zero_is_not_a_rejection",
    "same_line_checker_injection_is_not_a_rejection",
    "multiline_checker_injection_is_not_a_rejection",
    "argument_parser_injection_is_not_a_rejection",
    "exact_source_size_suffix_is_not_a_rejection",
    "exact_source_path_suffix_is_not_a_rejection",
    "cleanup_failure_cannot_earn_primary_failure_credit",
)
EXPECTED_BOUNDARY_COUNTS = {
    ExpectedBoundary.ARGUMENT_PARSER: 1,
    ExpectedBoundary.CHECKER: 77,
    ExpectedBoundary.EXACT_SOURCE_DIGEST: 2,
    ExpectedBoundary.EXACT_SOURCE_ENDPOINT: 1,
    ExpectedBoundary.EXACT_SOURCE_PATH: 1,
    ExpectedBoundary.EXACT_SOURCE_SIZE: 2,
    ExpectedBoundary.ISOLATED_EQUIVALENT: 1,
    ExpectedBoundary.PYTHON_PRECONDITION: 2,
    ExpectedBoundary.RECEIPT_VALIDATOR: 22,
}


@dataclass(frozen=True)
class Observation:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class Candidate:
    root: Path
    tree: str
    checkpoint: str


@dataclass(frozen=True)
class RunnerState:
    ready: bool
    checker_sha256: str
    checker_size: int
    self_test_sha256: str
    self_test_size: int
    maximum_source_size: int


GIT_RAW = shutil.which("git")
PYTHON_RAW = sys.executable
if GIT_RAW is None:
    raise SelfTestError("Git executable is unavailable")
GIT = str(Path(GIT_RAW).resolve(strict=True))
PYTHON = str(Path(PYTHON_RAW).resolve(strict=True))


def isolated_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
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
    if extra is not None:
        environment.update(extra)
    return environment


def process_group_state(process_group: int) -> ProcessGroupState:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return ProcessGroupState.ABSENT
    except PermissionError:
        # Darwin can transiently return EPERM for a just-reaped session leader
        # while the empty process group is being dismantled.  This is not absence
        # evidence: callers retry to ESRCH or fail closed at their deadline.
        return ProcessGroupState.INDETERMINATE
    except OSError as error:
        raise HarnessCleanupFailure(
            f"cannot inspect subprocess group {process_group}: {error}"
        ) from error
    return ProcessGroupState.PRESENT


def signal_process_group(
    child: subprocess.Popen[bytes],
    selected_signal: signal.Signals,
    *,
    ownership: OwnedChildSignalMask,
) -> PermissionError | None:
    ownership.require_held(operation="self-test process-group signal")
    if child.returncode is not None:
        raise HarnessCleanupFailure(
            f"refused {selected_signal.name} for subprocess group {child.pid} "
            "after reaping its leader"
        )
    try:
        os.killpg(child.pid, selected_signal)
    except ProcessLookupError:
        return None
    except PermissionError as error:
        # A concurrent group teardown can race the signal.  The caller must still
        # obtain subsequent ESRCH evidence; a persistent EPERM remains an error.
        return error
    except OSError as error:
        raise HarnessCleanupFailure(
            f"cannot signal subprocess group {child.pid} with "
            f"{selected_signal.name}: {error}"
        ) from error
    return None


def wait_for_process_group_absence(
    process_group: int, deadline: float
) -> ProcessGroupState:
    while True:
        state = process_group_state(process_group)
        if state is ProcessGroupState.ABSENT or time.monotonic() >= deadline:
            return state
        time.sleep(PROCESS_GROUP_PROBE_INTERVAL_SECONDS)


def require_process_group_absent_after_reap(
    child: subprocess.Popen[bytes],
    *,
    operation: str,
    grace_seconds: float = PROCESS_TERMINATION_GRACE_SECONDS,
) -> None:
    if grace_seconds < 0:
        raise HarnessCleanupFailure(
            f"{operation}: process-group grace is negative"
        )
    if child.returncode is None:
        raise HarnessCleanupFailure(
            f"{operation}: subprocess leader was not reaped before the "
            "observe-only group check"
        )
    state = wait_for_process_group_absence(
        child.pid,
        time.monotonic() + grace_seconds,
    )
    if state is not ProcessGroupState.ABSENT:
        raise HarnessCleanupFailure(
            f"{operation}: cannot prove subprocess group {child.pid} absent "
            f"after reaping its leader (final state: {state.value}); no "
            "post-reap signal was sent"
        )


def terminate_process_group(
    child: subprocess.Popen[bytes],
    *,
    ownership: OwnedChildSignalMask,
    operation: str,
    grace_seconds: float = PROCESS_TERMINATION_GRACE_SECONDS,
) -> None:
    ownership.require_held(operation=operation)
    if grace_seconds < 0:
        raise HarnessCleanupFailure(
            f"{operation}: process-group grace is negative"
        )
    process_group = child.pid
    observed_error: BaseException | None = None

    # Custody also requires the SIGCHLD/thread/no-waiter premises; a local
    # returncode=None is not a generic ownership token.
    if child.returncode is None:
        try:
            term_error = signal_process_group(
                child, signal.SIGTERM, ownership=ownership
            )
            if term_error is not None:
                observed_error = retain_cleanup_exception(
                    observed_error,
                    term_error,
                    label="self-test process-group SIGTERM",
                )
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="self-test process-group SIGTERM",
            )
        try:
            state = wait_for_process_group_absence(
                process_group,
                time.monotonic() + grace_seconds,
            )
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="self-test process-group pre-reap probe",
            )
            state = ProcessGroupState.INDETERMINATE
        if state is not ProcessGroupState.ABSENT:
            try:
                kill_error = signal_process_group(
                    child, signal.SIGKILL, ownership=ownership
                )
                if kill_error is not None:
                    observed_error = retain_cleanup_exception(
                        observed_error,
                        kill_error,
                        label="self-test process-group SIGKILL",
                    )
            except BaseException as error:
                observed_error = retain_cleanup_exception(
                    observed_error,
                    error,
                    label="self-test process-group SIGKILL",
                )

    for _attempt in range(2):
        if child.returncode is not None:
            break
        try:
            child.wait(timeout=max(grace_seconds, 0.001))
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="self-test process-group leader reap",
            )
    if child.returncode is not None:
        try:
            require_process_group_absent_after_reap(
                child,
                operation=operation,
                grace_seconds=grace_seconds,
            )
        except BaseException as error:
            observed_error = retain_cleanup_exception(
                observed_error,
                error,
                label="self-test process-group post-reap observation",
            )
    else:
        observed_error = retain_cleanup_exception(
            observed_error,
            HarnessCleanupFailure(
                f"{operation}: subprocess leader could not be proven reaped"
            ),
            label="self-test process-group leader reap",
        )
    if child.returncode is None or observed_error is not None:
        if child.returncode is not None:
            try:
                require_process_group_absent_after_reap(
                    child,
                    operation=operation,
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
        raise HarnessCleanupFailure(
            f"{operation}: process-group cleanup failed: {detail}"
        ) from observed_error


def process(
    command: list[str],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
    environment_extra: dict[str, str] | None = None,
    timeout_seconds: float,
    maximum_output_bytes: int = MAX_PROCESS_OUTPUT_BYTES,
) -> Observation:
    require(bool(command), "attempted to execute an empty command")
    require(timeout_seconds > 0, "subprocess timeout must be positive")
    require(maximum_output_bytes > 0, "subprocess output bound must be positive")
    operation = command[0]
    input_stream: Any = None
    child: subprocess.Popen[bytes] | None = None
    selector: selectors.BaseSelector | None = None
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    deadline = time.monotonic() + timeout_seconds
    returncode: int | None = None
    primary_error: BaseException | None = None
    ownership = OwnedChildSignalMask.acquire(
        label=f"{operation} self-test child lifecycle"
    )
    try:
        if input_bytes is not None:
            input_stream = tempfile.TemporaryFile()
            input_stream.write(input_bytes)
            input_stream.flush()
            input_stream.seek(0)
        raise_deferred_verifier_signal_if_safe(None)
        require_sigchld_default()
        try:
            child = subprocess.Popen(
                command,
                cwd=cwd,
                env=isolated_environment(environment_extra),
                stdin=(
                    input_stream
                    if input_stream is not None
                    else subprocess.DEVNULL
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                preexec_fn=child_unblock_owned_exception_signals,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise HarnessLaunchFailure(
                f"{operation}: execution failed: {error}"
            ) from error
        require(
            child.stdout is not None and child.stderr is not None,
            f"{operation}: capture pipes are absent",
        )
        selector = selectors.DefaultSelector()
        for stream, label in (
            (child.stdout, "stdout"),
            (child.stderr, "stderr"),
        ):
            try:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)
            except OSError as error:
                raise HarnessIoFailure(
                    f"{operation}: cannot configure the {label} capture pipe: {error}"
                ) from error

        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise HarnessTimeoutFailure(
                    f"{operation}: exceeded {timeout_seconds:g} seconds"
                )
            events = selector.select(remaining)
            if not events:
                if time.monotonic() >= deadline:
                    raise HarnessTimeoutFailure(
                        f"{operation}: exceeded {timeout_seconds:g} seconds"
                    )
                continue
            for key, _mask in events:
                stream = key.fileobj
                label = key.data
                remaining_output = maximum_output_bytes - (
                    len(stdout_buffer) + len(stderr_buffer)
                )
                try:
                    chunk = os.read(
                        stream.fileno(),
                        min(64 * 1024, remaining_output + 1),
                    )
                except BlockingIOError:
                    continue
                except OSError as error:
                    raise HarnessIoFailure(
                        f"{operation}: cannot read the {label} capture pipe: {error}"
                    ) from error
                if not chunk:
                    selector.unregister(stream)
                    continue
                if len(chunk) > remaining_output:
                    retained = chunk[:remaining_output]
                    if label == "stdout":
                        stdout_buffer.extend(retained)
                    else:
                        stderr_buffer.extend(retained)
                    raise HarnessOutputLimitFailure(
                        f"{operation}: combined output exceeded "
                        f"{maximum_output_bytes} bytes"
                    )
                if label == "stdout":
                    stdout_buffer.extend(chunk)
                else:
                    stderr_buffer.extend(chunk)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise HarnessTimeoutFailure(
                f"{operation}: exceeded {timeout_seconds:g} seconds"
            )
        try:
            returncode = child.wait(timeout=max(0.001, remaining))
        except subprocess.TimeoutExpired as error:
            raise HarnessTimeoutFailure(
                f"{operation}: exceeded {timeout_seconds:g} seconds"
            ) from error
        try:
            require_process_group_absent_after_reap(child, operation=operation)
        except HarnessCleanupFailure as error:
            raise HarnessDescendantFailure(str(error)) from error
        if returncode < 0:
            raise HarnessSignalFailure(
                f"{operation}: terminated by signal {-returncode}"
            )
    except BaseException as error:
        primary_error = error
        if child is not None:
            try:
                terminate_process_group(
                    child,
                    ownership=ownership,
                    operation=operation,
                )
            except BaseException as cleanup_error:
                add_secondary_exception_note(
                    cleanup_error,
                    f"{operation} initiating failure",
                    error,
                )
                primary_error = cleanup_error
                raise cleanup_error from error
        raise
    finally:
        local_close_error: BaseException | None = None
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                local_close_error = error
        if child is not None:
            for _pipe_name, pipe in (
                ("stdout", child.stdout),
                ("stderr", child.stderr),
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
                            operation,
                            error,
                        )
        if input_stream is not None and not input_stream.closed:
            try:
                input_stream.close()
            except BaseException as error:
                if local_close_error is None:
                    local_close_error = error
                else:
                    add_secondary_exception_note(
                        local_close_error,
                        operation,
                        error,
                    )
        effective_error = primary_error or local_close_error
        if primary_error is not None and local_close_error is not None:
            add_secondary_exception_note(
                primary_error,
                operation,
                local_close_error,
            )
        restore_signal_mask_preserving_error(
            ownership,
            effective_error,
            label=operation,
        )
        if primary_error is None and local_close_error is not None:
            try:
                detail = str(local_close_error)
            except BaseException:
                detail = "unprintable cleanup exception"
            raise HarnessIoFailure(
                f"{operation}: local-resource closure failed: {detail}"
            ) from local_close_error

    require(child is not None, f"{operation}: lost its child handle")
    require(returncode is not None, f"{operation}: lost its child return code")
    return Observation(returncode, bytes(stdout_buffer), bytes(stderr_buffer))


def git_process(
    root: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
    check: bool = True,
    environment_extra: dict[str, str] | None = None,
) -> Observation:
    result = process(
        [
            GIT,
            "-c",
            "advice.graftFileDeprecated=false",
            "-c",
            "commit.gpgsign=false",
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
        ],
        cwd=root,
        input_bytes=input_bytes,
        environment_extra=environment_extra,
        timeout_seconds=GIT_PROCESS_TIMEOUT_SECONDS,
    )
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SelfTestError(
            f"Git {' '.join(arguments)} failed with {result.returncode}: {detail}"
        )
    return result


def git_text(
    root: Path,
    *arguments: str,
    environment_extra: dict[str, str] | None = None,
) -> str:
    raw = git_process(root, *arguments, environment_extra=environment_extra).stdout
    try:
        return raw.decode("utf-8", errors="strict").removesuffix("\n")
    except UnicodeDecodeError as error:
        raise SelfTestError(f"Git {' '.join(arguments)} output is not UTF-8") from error


def canonical_relative(relative: str) -> tuple[str, ...]:
    path = PurePosixPath(relative)
    require(
        bool(relative)
        and not path.is_absolute()
        and path.as_posix() == relative
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"noncanonical self-test path: {relative!r}",
    )
    return path.parts


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


def read_declared_bytes(file_descriptor: int, expected_size: int, label: str) -> bytes:
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = expected_size
    while remaining:
        chunk = os.read(file_descriptor, min(1024 * 1024, remaining))
        if not chunk:
            raise SelfTestError(f"{label}: source is shorter than its declared size")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(file_descriptor, 1):
        raise SelfTestError(f"{label}: source exceeds its declared size")
    return b"".join(chunks)


def stable_file(
    root: Path,
    relative: str,
    *,
    maximum_bytes: int = MAX_PROCESS_OUTPUT_BYTES,
) -> tuple[str, bytes]:
    components = canonical_relative(relative)
    require(maximum_bytes > 0, f"{relative}: source byte bound is not positive")
    require(
        all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")),
        "self-test requires POSIX no-follow/nonblocking descriptors",
    )
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    )
    leaf_flags = (
        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    )
    directory_descriptor: int | None = None
    following: int | None = None
    leaf_descriptor: int | None = None
    primary_error: BaseException | None = None
    phase = "open"
    try:
        directory_descriptor = os.open(root, directory_flags)
        for component in components[:-1]:
            following = os.open(
                component,
                directory_flags,
                dir_fd=directory_descriptor,
            )
            previous_descriptor = directory_descriptor
            directory_descriptor = following
            following = None
            close_error = close_descriptor_preserving_error(
                previous_descriptor,
                None,
                label="self-test stable-file superseded directory",
            )
            if close_error is not None:
                raise SelfTestError(
                    f"{relative}: cannot close a superseded directory descriptor"
                ) from close_error
        leaf_descriptor = os.open(
            components[-1],
            leaf_flags,
            dir_fd=directory_descriptor,
        )
        phase = "read"
        before = os.fstat(leaf_descriptor)
        require(stat.S_ISREG(before.st_mode), f"{relative}: source is not regular")
        require(before.st_nlink == 1, f"{relative}: source is hard-linked")
        permissions = stat.S_IMODE(before.st_mode)
        require(
            permissions in {0o644, 0o755},
            f"{relative}: source mode is noncanonical",
        )
        require(
            0 <= before.st_size <= maximum_bytes,
            f"{relative}: source exceeds the byte bound",
        )
        first = read_declared_bytes(leaf_descriptor, before.st_size, relative)
        middle = os.fstat(leaf_descriptor)
        second = read_declared_bytes(leaf_descriptor, before.st_size, relative)
        after = os.fstat(leaf_descriptor)
        require(
            descriptor_identity(before) == descriptor_identity(middle)
            and descriptor_identity(middle) == descriptor_identity(after)
            and len(first) == before.st_size
            and first == second,
            f"{relative}: source changed during capture",
        )
        return ("100755" if permissions == 0o755 else "100644"), first
    except (OSError, ValueError) as error:
        if phase == "open":
            converted = SelfTestError(
                f"{relative}: cannot open the no-follow descriptor path: {error}"
            )
        else:
            converted = SelfTestError(
                f"{relative}: cannot read source descriptor: {error}"
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
            label="self-test stable-file leaf",
        )
        cleanup_error = close_descriptor_preserving_error(
            following,
            cleanup_error,
            label="self-test stable-file pending directory",
        )
        cleanup_error = close_descriptor_preserving_error(
            directory_descriptor,
            cleanup_error,
            label="self-test stable-file directory",
        )
        if primary_error is None and cleanup_error is not None:
            raise SelfTestError(
                f"{relative}: descriptor cleanup failed"
            ) from cleanup_error


def stable_absolute_file(path: Path, maximum_bytes: int, label: str) -> bytes:
    require(
        path.is_absolute() and maximum_bytes > 0,
        f"{label}: absolute bounded-file arguments are invalid",
    )
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise SelfTestError(f"{label}: cannot open no-follow descriptor: {error}") from error
    try:
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode)
            and 0 < before.st_size <= maximum_bytes,
            f"{label}: file is non-regular, empty, or exceeds its byte bound",
        )
        first = read_declared_bytes(descriptor, before.st_size, label)
        middle = os.fstat(descriptor)
        second = read_declared_bytes(descriptor, before.st_size, label)
        after = os.fstat(descriptor)
        require(
            descriptor_identity(before) == descriptor_identity(middle)
            and descriptor_identity(middle) == descriptor_identity(after)
            and len(first) == before.st_size
            and first == second,
            f"{label}: file changed during bounded capture",
        )
        return first
    except OSError as error:
        raise SelfTestError(f"{label}: cannot read descriptor: {error}") from error
    finally:
        primary = sys.exception()
        close_error = close_descriptor_preserving_error(
            descriptor, primary, label=f"{label} descriptor"
        )
        if primary is None and close_error is not None:
            raise SelfTestError(f"{label}: descriptor close failed") from close_error


def write_regular(path: Path, body: bytes, mode: int = 0o644) -> None:
    require(mode in {0o644, 0o755}, "attempted to write a noncanonical mode")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        path.unlink()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        view = memoryview(body)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            require(count > 0, f"short write for {path}")
            written += count
        os.fchmod(descriptor, mode)
    finally:
        primary = sys.exception()
        close_error = close_descriptor_preserving_error(
            descriptor, primary, label="self-test fixture descriptor"
        )
        if primary is None and close_error is not None:
            raise SelfTestError(f"close failed for {path}") from close_error


def copy_candidate_overlay(destination: Path) -> None:
    for relative in sorted(EXPECTED_PATH_STATUS):
        mode, body = stable_file(ROOT, relative)
        write_regular(
            destination / relative, body, 0o755 if mode == "100755" else 0o644
        )


def clone_no_local(source: Path, destination: Path, branch: str | None = None) -> None:
    arguments = [
        "-c",
        "protocol.file.allow=always",
        "clone",
        "--no-local",
        "--quiet",
        "--no-checkout",
    ]
    if branch is not None:
        arguments.extend(("--branch", branch, "--single-branch"))
    arguments.extend((str(source), str(destination)))
    git_process(destination.parent, *arguments)
    common = Path(git_text(destination, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = destination / common
    alternates = common.resolve(strict=True) / "objects/info/alternates"
    require(
        not alternates.exists() and not alternates.is_symlink(),
        "--no-local clone unexpectedly uses an object alternate",
    )
    require(
        git_text(destination, "rev-parse", "--is-shallow-repository") == "false",
        "self-test clone is shallow",
    )


def checkout_anchor(root: Path) -> None:
    git_process(root, "checkout", "--quiet", "--detach", ANCHOR)
    require(
        git_text(root, "rev-parse", "--verify", "HEAD") == ANCHOR,
        "clone HEAD is not C3",
    )
    require(
        git_text(root, "rev-parse", "--verify", "HEAD^{tree}") == ANCHOR_TREE,
        "clone anchor tree is not immutable C3",
    )
    require(
        not git_process(
            root, "status", "--porcelain=v2", "--untracked-files=all"
        ).stdout,
        "fresh anchor clone is dirty",
    )


def build_tree_with_path_add_index(root: Path, index_path: Path) -> str:
    environment = {"GIT_INDEX_FILE": str(index_path.resolve())}
    git_process(root, "read-tree", ANCHOR, environment_extra=environment)
    git_process(
        root,
        "add",
        "--all",
        "--",
        *sorted(EXPECTED_PATH_STATUS),
        environment_extra=environment,
    )
    tree = git_text(root, "write-tree", environment_extra=environment)
    require(
        HEX40.fullmatch(tree) is not None,
        "path-add alternate index produced an invalid tree",
    )
    return tree


def build_tree_with_captured_blobs(root: Path, index_path: Path) -> str:
    environment = {"GIT_INDEX_FILE": str(index_path.resolve())}
    git_process(root, "read-tree", ANCHOR, environment_extra=environment)
    for relative in sorted(EXPECTED_PATH_STATUS):
        mode, body = stable_file(root, relative)
        # hash-object reads the exact captured bytes, not the live path.
        oid_observation = git_process(
            root,
            "hash-object",
            "-w",
            "--stdin",
            input_bytes=body,
            environment_extra=environment,
        )
        oid = oid_observation.stdout.decode("ascii", errors="strict").strip()
        require(HEX40.fullmatch(oid) is not None, f"{relative}: invalid blob object id")
        git_process(
            root,
            "update-index",
            "--add",
            "--cacheinfo",
            f"{mode},{oid},{relative}",
            environment_extra=environment,
        )
    tree = git_text(root, "write-tree", environment_extra=environment)
    require(
        HEX40.fullmatch(tree) is not None,
        "captured-blob alternate index produced an invalid tree",
    )
    return tree


def commit_environment(
    name: str = EXPECTED_NAME, email: str = EXPECTED_EMAIL
) -> dict[str, str]:
    return {
        "GIT_AUTHOR_DATE": FIXED_DATE,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_AUTHOR_NAME": name,
        "GIT_COMMITTER_DATE": FIXED_DATE,
        "GIT_COMMITTER_EMAIL": email,
        "GIT_COMMITTER_NAME": name,
    }


def create_commit(
    root: Path,
    tree: str,
    parents: tuple[str, ...],
    *,
    message: str = EXPECTED_MESSAGE,
    name: str = EXPECTED_NAME,
    email: str = EXPECTED_EMAIL,
) -> str:
    arguments = ["commit-tree", tree]
    for parent in parents:
        arguments.extend(("-p", parent))
    result = git_process(
        root,
        *arguments,
        input_bytes=message.encode("utf-8"),
        environment_extra=commit_environment(name, email),
    )
    commit = result.stdout.decode("ascii", errors="strict").strip()
    require(
        HEX40.fullmatch(commit) is not None, "commit-tree returned an invalid object id"
    )
    return commit


def tree_inventory_counts(root: Path, tree: str) -> tuple[int, int]:
    raw = git_process(root, "ls-tree", "-r", "--name-only", "-z", tree).stdout
    try:
        paths = tuple(
            record.decode("utf-8", errors="strict")
            for record in raw.split(b"\0")
            if record
        )
    except UnicodeDecodeError as error:
        raise SelfTestError("candidate tree inventory is not strict UTF-8") from error
    require(
        paths == tuple(sorted(set(paths))),
        "candidate tree inventory is duplicate or noncanonical",
    )
    directories: set[str] = set()
    for path in paths:
        canonical_relative(path)
        parent = PurePosixPath(path).parent
        while parent != PurePosixPath("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return len(paths), len(directories)


def build_template(scratch: Path) -> Candidate:
    root = scratch / "template"
    clone_no_local(ROOT, root)
    checkout_anchor(root)
    copy_candidate_overlay(root)
    first_tree = build_tree_with_path_add_index(root, scratch / "candidate-a.index")
    second_tree = build_tree_with_captured_blobs(
        root, scratch / "candidate-b.index"
    )
    require(
        first_tree == second_tree,
        "failure-diverse alternate-index constructions disagree",
    )
    require(
        tree_inventory_counts(root, first_tree)
        == (565, EXPECTED_FILESYSTEM_DIRECTORY_COUNT),
        "candidate file or implied-directory count changed",
    )
    require(
        git_text(root, "write-tree") == ANCHOR_TREE,
        "candidate construction changed the real anchor index",
    )
    checkpoint = create_commit(root, first_tree, (ANCHOR,))
    git_process(root, "branch", "--force", "selftest-candidate-object", checkpoint)
    return Candidate(root=root, tree=first_tree, checkpoint=checkpoint)


def clone_case(template: Candidate, scratch: Path, name: str) -> Candidate:
    root = scratch / f"case-{name}"
    clone_no_local(template.root, root, "selftest-candidate-object")
    checkout_anchor(root)
    copy_candidate_overlay(root)
    require(
        git_process(
            root, "cat-file", "-e", f"{template.checkpoint}^{{commit}}"
        ).returncode
        == 0,
        f"{name}: candidate checkpoint object was not transferred",
    )
    require(
        git_text(root, "rev-parse", f"{template.checkpoint}^{{tree}}") == template.tree,
        f"{name}: candidate checkpoint tree changed in clone",
    )
    return Candidate(root=root, tree=template.tree, checkpoint=template.checkpoint)


def remove_case(candidate: Candidate, scratch: Path) -> None:
    require(
        candidate.root.parent == scratch
        and candidate.root.name.startswith("case-")
        and candidate.root != scratch,
        "refusing to remove a path outside the self-test case boundary",
    )
    shutil.rmtree(candidate.root)


def runner_hash_state(root: Path) -> RunnerState:
    _mode, runner = stable_file(
        root,
        RUNNER_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    checker_matches = RUNNER_CHECKER_HASH.findall(runner)
    self_test_matches = RUNNER_SELF_TEST_HASH.findall(runner)
    checker_size_matches = RUNNER_CHECKER_SIZE.findall(runner)
    self_test_size_matches = RUNNER_SELF_TEST_SIZE.findall(runner)
    maximum_size_matches = RUNNER_MAX_SOURCE_SIZE.findall(runner)
    require(
        len(checker_matches) == 1
        and len(self_test_matches) == 1
        and len(checker_size_matches) == 1
        and len(self_test_size_matches) == 1
        and len(maximum_size_matches) == 1,
        "runner source declarations are not unique",
    )
    checker_declared = checker_matches[0].decode("ascii")
    self_test_declared = self_test_matches[0].decode("ascii")
    checker_size_raw = checker_size_matches[0]
    self_test_size_raw = self_test_size_matches[0]
    maximum_source_size_raw = maximum_size_matches[0]
    checker_size = int(checker_size_raw.decode("ascii"))
    self_test_size = int(self_test_size_raw.decode("ascii"))
    maximum_source_size = int(maximum_source_size_raw.decode("ascii"))
    require(
        checker_size_raw == str(checker_size).encode("ascii")
        and self_test_size_raw == str(self_test_size).encode("ascii")
        and maximum_source_size_raw == str(maximum_source_size).encode("ascii"),
        "runner source size declarations are not canonical decimal",
    )
    checker_body = stable_file(
        root,
        CHECKER_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )[1]
    self_test_body = stable_file(
        root,
        SELF_TEST_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )[1]
    checker_actual = hashlib.sha256(checker_body).hexdigest()
    self_test_actual = hashlib.sha256(self_test_body).hexdigest()
    require(
        0 <= checker_size <= maximum_source_size == MAX_EXACT_SOURCE_BYTES
        and 0 <= self_test_size <= maximum_source_size,
        "runner source size declarations are outside the exact cap",
    )
    bootstrap_direct = (
        checker_declared == ZERO_HASH
        and self_test_declared == ZERO_HASH
        and checker_size == 0
        and self_test_size == 0
    )
    frozen = (
        checker_declared != ZERO_HASH
        and self_test_declared != ZERO_HASH
        and checker_declared == checker_actual
        and self_test_declared == self_test_actual
        and checker_size > 0
        and self_test_size > 0
        and checker_size == len(checker_body)
        and self_test_size == len(self_test_body)
    )
    require(
        bootstrap_direct or frozen,
        "runner source declarations are neither exact zero-bootstrap nor frozen state",
    )
    return RunnerState(
        ready=frozen,
        checker_sha256=checker_declared,
        checker_size=checker_size,
        self_test_sha256=self_test_declared,
        self_test_size=self_test_size,
        maximum_source_size=maximum_source_size,
    )


def validate_self_exact_source_entry(expected_sha256: str, expected_size: int) -> None:
    context = globals().get("__pid_rs_exact_source_context__")
    if not isinstance(context, dict):
        raise SelfTestError("self-test exact-source bootstrap context is absent")
    require(
        set(context) == {"optimize", "relative", "sha256", "size"},
        "self-test exact-source context fields changed",
    )
    require(
        type(context["optimize"]) is int
        and context["optimize"] == sys.flags.optimize
        and context["optimize"] in {0, 1}
        and context["relative"] == SELF_TEST_RELATIVE
        and context["sha256"] == expected_sha256
        and type(context["size"]) is int
        and context["size"] == expected_size,
        "self-test exact-source identity changed",
    )
    require(
        globals().get("__loader__") is None
        and globals().get("__spec__") is None
        and globals().get("__cached__") is None,
        "self-test was not compiled through the exact-source namespace",
    )
    mode, body = stable_file(
        ROOT,
        SELF_TEST_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    require(
        mode == "100755"
        and len(body) == expected_size
        and expected_size <= MAX_EXACT_SOURCE_BYTES
        and hashlib.sha256(body).hexdigest() == expected_sha256,
        "self-test live source differs from its exact-source capture",
    )


def external_arguments(candidate: Candidate) -> list[str]:
    return [
        "--expected-candidate-tree",
        candidate.tree,
        "--checkpoint-commit",
        candidate.checkpoint,
    ]


def invoke_checker(
    candidate: Candidate,
    arguments: list[str],
    *,
    python_mode: PythonMode,
    exact_runner: bool,
    python_flags: tuple[str, ...] | None = None,
    environment_extra: dict[str, str] | None = None,
) -> Observation:
    if python_flags is not None:
        require(
            "-O" not in python_flags and "-OO" not in python_flags,
            "special Python flags must not encode optimization mode",
        )
        command = [
            PYTHON,
            *python_flags,
            *python_mode.interpreter_arguments,
            str(candidate.root / CHECKER_RELATIVE),
            *arguments,
        ]
    elif exact_runner:
        command = [
            str(candidate.root / RUNNER_RELATIVE),
            python_mode.value,
            "checker",
            *arguments,
        ]
    else:
        source_body = stable_file(
            ROOT,
            CHECKER_RELATIVE,
            maximum_bytes=MAX_EXACT_SOURCE_BYTES,
        )[1]
        require(
            0 < len(source_body) <= MAX_EXACT_SOURCE_BYTES,
            "direct checker source exceeds the exact-source cap",
        )
        source_sha256 = hashlib.sha256(source_body).hexdigest()
        command = [PYTHON, "-I", "-S", *python_mode.interpreter_arguments]
        command.extend(
            (
                "-c",
                DIRECT_EXACT_BOOTSTRAP,
                str(candidate.root),
                CHECKER_RELATIVE,
                source_sha256,
                str(len(source_body)),
                str(MAX_EXACT_SOURCE_BYTES),
                *arguments,
            )
        )
    return process(
        command,
        cwd=candidate.root,
        environment_extra=environment_extra,
        timeout_seconds=TARGET_PROCESS_TIMEOUT_SECONDS,
    )


def require_exact_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    require(set(value) == keys, f"{label} keys differ from the typed receipt schema")


def require_hex(value: Any, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str):
        raise SelfTestError(f"{label} is not a string")
    require(pattern.fullmatch(value) is not None, f"{label} is malformed")
    return value


def reject_json_constant(value: str) -> Any:
    raise SelfTestError(f"non-finite JSON constant is forbidden: {value}")


def unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def parse_json_document(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=unique_json_object,
            parse_constant=reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelfTestError("receipt is not strict UTF-8 JSON") from error


def git_index_path(root: Path) -> Path:
    raw = Path(git_text(root, "rev-parse", "--git-path", "index"))
    unresolved = raw if raw.is_absolute() else root / raw
    return unresolved.parent.resolve(strict=True) / unresolved.name


def observed_index_receipt(root: Path) -> dict[str, Any]:
    path = git_index_path(root)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise SelfTestError(
            f"receipt-validation index cannot be opened no-follow: {error}"
        ) from error
    try:
        before = os.fstat(descriptor)
        require(
            stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            "receipt-validation index is not a single-linked regular file",
        )
        require(
            32 <= before.st_size <= 8 * 1024 * 1024,
            "receipt-validation index exceeds its exact size bound",
        )
        permissions = stat.S_IMODE(before.st_mode)
        require(
            bool(permissions & stat.S_IRUSR)
            and not permissions & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            and not permissions & (stat.S_IWGRP | stat.S_IWOTH),
            "receipt-validation index permissions are unsafe",
        )
        first = read_declared_bytes(descriptor, before.st_size, "Git index")
        middle = os.fstat(descriptor)
        second = read_declared_bytes(descriptor, before.st_size, "Git index")
        after = os.fstat(descriptor)
        require(
            descriptor_identity(before) == descriptor_identity(middle)
            and descriptor_identity(middle) == descriptor_identity(after)
            and len(first) == before.st_size
            and first == second,
            "receipt-validation index changed during observation",
        )
    except OSError as error:
        raise SelfTestError(f"receipt-validation index read failed: {error}") from error
    finally:
        primary = sys.exception()
        close_error = close_descriptor_preserving_error(
            descriptor, primary, label="receipt-validation index descriptor"
        )
        if primary is None and close_error is not None:
            raise SelfTestError("receipt-validation index close failed") from close_error
    require(
        len(first) >= 32 and first[:4] == b"DIRC",
        "receipt-validation index header is malformed",
    )
    version = int.from_bytes(first[4:8], byteorder="big")
    entry_count = int.from_bytes(first[8:12], byteorder="big")
    require(version in {2, 3, 4}, "receipt-validation index version is unsupported")
    require(
        entry_count <= 565,
        "receipt-validation index exceeds the candidate path-count bound",
    )
    require(
        hashlib.sha1(first[:-20]).digest() == first[-20:],
        "receipt-validation index checksum is inconsistent",
    )
    require(
        all(signature not in first for signature in (b"FSMN", b"link", b"sdir")),
        "receipt-validation index contains a forbidden extension signature",
    )
    return {
        "entry_count": entry_count,
        "forbidden_extension_signatures_absent": ["FSMN", "link", "sdir"],
        "maximum_size": 8 * 1024 * 1024,
        "mode": f"{permissions:04o}",
        "sha256": hashlib.sha256(first).hexdigest(),
        "sha1_trailing_checksum_verified": True,
        "single_link_regular_no_split_index": True,
        "size": len(first),
        "stage_zero_v_flags": "all-H",
        "version": version,
    }


def observed_local_config_receipt(root: Path) -> dict[str, Any]:
    body = git_process(
        root, "config", "--no-includes", "--local", "--null", "--list"
    ).stdout
    records = tuple(record for record in body.split(b"\0") if record)
    return {
        "record_count": len(records),
        "sha256": hashlib.sha256(body).hexdigest(),
        "size": len(body),
    }


def observed_object_pack_inventory_receipt(root: Path) -> dict[str, Any]:
    common_raw = Path(git_text(root, "rev-parse", "--git-common-dir"))
    common = common_raw if common_raw.is_absolute() else root / common_raw
    common = common.resolve(strict=True)
    require(
        os.stat in os.supports_dir_fd
        and os.open in os.supports_dir_fd
        and os.scandir in os.supports_fd
        and all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")),
        "receipt pack validation requires descriptor-relative no-follow custody",
    )
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    records: list[list[Any]] = []
    common_descriptor: int | None = None
    objects_descriptor: int | None = None
    pack_descriptor: int | None = None
    primary_error: BaseException | None = None
    try:
        common_descriptor = os.open(common, directory_flags)
        objects_descriptor = os.open(
            "objects", directory_flags, dir_fd=common_descriptor
        )
        pack_descriptor = os.open(
            "pack", directory_flags, dir_fd=objects_descriptor
        )
        before = descriptor_identity(os.fstat(pack_descriptor))
        seen: set[str] = set()
        with os.scandir(pack_descriptor) as iterator:
            for entry in iterator:
                require(
                    len(records) < 4_096,
                    "receipt Git object pack directory exceeds the entry bound",
                )
                name = entry.name
                try:
                    name_raw = name.encode("utf-8", errors="strict")
                except UnicodeEncodeError as error:
                    raise SelfTestError(
                        "receipt Git object pack name is not strict UTF-8"
                    ) from error
                require(
                    bool(name)
                    and name not in {".", ".."}
                    and "/" not in name
                    and "\n" not in name
                    and "\r" not in name
                    and len(name_raw) <= 255
                    and name not in seen,
                    "receipt Git object pack name is noncanonical or duplicated",
                )
                seen.add(name)
                require(
                    not name.endswith(".promisor"),
                    "receipt Git promisor marker contradicts the absence claim",
                )
                metadata = os.stat(
                    name, dir_fd=pack_descriptor, follow_symlinks=False
                )
                require(
                    stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1,
                    "receipt Git object pack entry has unsupported topology",
                )
                records.append([name, *descriptor_identity(metadata)])
        require(
            descriptor_identity(os.fstat(pack_descriptor)) == before,
            "receipt Git object pack directory changed during inventory",
        )
    except OSError as error:
        converted = SelfTestError(
            f"receipt cannot observe no-follow Git object pack inventory: {error}"
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
            label="receipt pack directory",
        )
        cleanup_error = close_descriptor_preserving_error(
            objects_descriptor,
            cleanup_error,
            label="receipt objects directory",
        )
        cleanup_error = close_descriptor_preserving_error(
            common_descriptor,
            cleanup_error,
            label="receipt common directory",
        )
        if primary_error is None and cleanup_error is not None:
            raise SelfTestError(
                "receipt pack descriptor cleanup failed"
            ) from cleanup_error
    records.sort(key=lambda record: record[0])
    encoded = json.dumps(records, separators=(",", ":")).encode("utf-8")
    return {
        "entry_count": len(records),
        "promisor_markers_absent": True,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def observed_worktree_projections(root: Path) -> dict[str, str]:
    raw = git_process(
        root,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ).stdout
    try:
        observed_paths = tuple(
            record.decode("utf-8", errors="strict")
            for record in raw.split(b"\0")
            if record
        )
    except UnicodeDecodeError as error:
        raise SelfTestError(
            "receipt projection inventory is not strict UTF-8"
        ) from error
    require(
        len(observed_paths) == len(set(observed_paths)) == 565,
        "receipt projection inventory changed",
    )
    paths = tuple(sorted(observed_paths))
    entries: dict[str, tuple[str, str]] = {}
    for path in paths:
        mode, body = stable_file(root, path)
        entries[path] = (mode, hashlib.sha256(body).hexdigest())

    def projected(selected: tuple[str, ...]) -> str:
        digest = hashlib.sha256()
        for path in selected:
            mode, sha256 = entries[path]
            digest.update(path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(mode.encode("ascii"))
            digest.update(b"\0blob\0")
            digest.update(sha256.encode("ascii"))
            digest.update(b"\n")
        return digest.hexdigest()

    allowlist = hashlib.sha256()
    for path in sorted(EXPECTED_PATH_STATUS):
        mode, _sha256 = entries[path]
        allowlist.update(path.encode("utf-8"))
        allowlist.update(b"\0")
        allowlist.update(EXPECTED_PATH_STATUS[path].encode("ascii"))
        allowlist.update(b"\0")
        allowlist.update(mode.encode("ascii"))
        allowlist.update(b"\n")
    pinned_changed = tuple(
        sorted(
            set(EXPECTED_PATH_STATUS).difference(
                {CHECKER_RELATIVE, RUNNER_RELATIVE}
            )
        )
    )
    protected = tuple(sorted(set(paths).difference(EXPECTED_PATH_STATUS)))
    require(len(protected) == 552, "receipt protected path count changed")
    protected_projection = projected(protected)
    require(
        protected_projection == EXPECTED_PROTECTED_PROJECTION_SHA256,
        "receipt observed protected projection differs from immutable C3",
    )
    return {
        "allowlist": allowlist.hexdigest(),
        "full_candidate": projected(paths),
        "pinned_changed": projected(pinned_changed),
        "protected": protected_projection,
    }


def validate_receipt(
    raw: bytes,
    *,
    tree: str | None,
    checkpoint: str | None,
    lifecycle: str | None,
    repository_root: Path,
) -> dict[str, Any]:
    require(
        raw.endswith(b"\n") and raw.count(b"\n") == 1, "receipt is not one JSON line"
    )
    parsed = parse_json_document(raw)
    require(type(parsed) is dict, "receipt root is not an object")
    receipt: dict[str, Any] = parsed
    canonical = (
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    require(raw == canonical, "receipt is not canonical JSON")
    require_exact_keys(
        receipt,
        {
            "anchor",
            "bounded_historical_replay",
            "candidate",
            "credit",
            "custody",
            "environmental_premises",
            "exact_source",
            "lifecycle",
            "non_implications",
            "path_custody",
            "repository_context",
            "resource_bounds",
            "schema",
            "status",
            "validation_class",
        },
        "receipt",
    )
    require(
        (tree is None) == (checkpoint is None),
        "receipt-validation external tree/checkpoint expectation is not paired",
    )
    creditable = tree is not None
    require(
        receipt["schema"] == "pid-rs/c3-hosted-followup-custody/v2"
        and receipt["status"] == ("pass" if creditable else "diagnostic_pass_no_credit")
        and receipt["credit"]
        == ("caller_supplied_tree_checkpoint_match" if creditable else "none")
        and receipt["custody"]
        == ("external-tree-and-checkpoint" if creditable else "diagnostic-no-credit")
        and receipt["validation_class"]
        == (
            "creditable_external_tree_checkpoint"
            if creditable
            else "diagnostic_only_without_external_custody"
        )
        and receipt["bounded_historical_replay"]
        == "separate_not_adjudicated_by_this_gate",
        "receipt authority fields changed",
    )
    require(
        typed_json_equal(receipt["resource_bounds"], EXPECTED_RESOURCE_BOUNDS),
        "receipt resource bounds changed",
    )
    if lifecycle is None:
        require(
            receipt["lifecycle"] in {"precommit-worktree", "committed-direct-child"},
            "receipt lifecycle is invalid",
        )
    else:
        require(receipt["lifecycle"] == lifecycle, "receipt lifecycle differs")
    require(
        type(receipt["non_implications"]) is list
        and tuple(receipt["non_implications"]) == EXPECTED_NON_IMPLICATIONS,
        "receipt non-implications changed",
    )
    anchor = receipt["anchor"]
    require(type(anchor) is dict, "receipt anchor is not typed")
    require_exact_keys(
        anchor, {"commit", "path_count", "projection_sha256", "tree"}, "anchor"
    )
    require(
        anchor["commit"] == ANCHOR
        and anchor["tree"] == ANCHOR_TREE
        and type(anchor["path_count"]) is int
        and anchor["path_count"] == 560,
        "receipt anchor changed",
    )
    require(
        require_hex(anchor["projection_sha256"], HEX64, "anchor projection")
        == ANCHOR_PROJECTION_SHA256,
        "receipt anchor projection differs from immutable C3",
    )
    candidate = receipt["candidate"]
    require(type(candidate) is dict, "receipt candidate is not typed")
    require_exact_keys(
        candidate,
        {
            "checkpoint_commit",
            "declared_identity_metadata",
            "parent",
            "projection_sha256",
            "tree",
        },
        "candidate",
    )
    require(
        candidate["checkpoint_commit"] == checkpoint
        and candidate["parent"] == ANCHOR
        and candidate["tree"] == tree,
        "receipt external candidate pair changed",
    )
    projections = observed_worktree_projections(repository_root)
    require(
        require_hex(candidate["projection_sha256"], HEX64, "candidate projection")
        == projections["full_candidate"],
        "receipt candidate projection differs from observed worktree",
    )
    declared_identity = candidate["declared_identity_metadata"]
    if creditable:
        require(
            type(declared_identity) is dict,
            "creditable declared identity metadata is not typed",
        )
        require_exact_keys(
            declared_identity, {"email", "name"}, "declared identity metadata"
        )
        require(
            declared_identity == {"email": EXPECTED_EMAIL, "name": EXPECTED_NAME},
            "declared human identity metadata changed",
        )
    else:
        require(
            declared_identity is None,
            "diagnostic receipt must not declare reviewed human identity metadata",
        )
    exact_source = receipt["exact_source"]
    require(type(exact_source) is dict, "receipt exact-source evidence is not typed")
    require_exact_keys(
        exact_source,
        {"checker_sha256", "checker_size", "loader"},
        "exact-source evidence",
    )
    checker_digest = require_hex(
        exact_source["checker_sha256"], HEX64, "exact-source checker digest"
    )
    checker_body = stable_file(
        repository_root,
        CHECKER_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )[1]
    require(
        checker_digest == hashlib.sha256(checker_body).hexdigest()
        and type(exact_source["checker_size"]) is int
        and 0 < exact_source["checker_size"] <= MAX_EXACT_SOURCE_BYTES
        and exact_source["checker_size"] == len(checker_body)
        and exact_source["loader"]
        == "size-and-digest-bound-no-follow-descriptor-compare",
        "receipt exact-source evidence changed",
    )
    custody = receipt["path_custody"]
    require(type(custody) is dict, "receipt path custody is not typed")
    require_exact_keys(
        custody,
        {
            "added",
            "allowlist_sha256",
            "candidate_path_count",
            "changed",
            "filesystem_directory_count",
            "filesystem_inventory",
            "full_candidate_projection_sha256",
            "modified",
            "pinned_changed_projection_sha256",
            "protected",
            "protected_projection_sha256",
            "self_unhashed_paths",
        },
        "path custody",
    )
    require(
        type(custody["added"]) is int
        and custody["added"] == 5
        and type(custody["modified"]) is int
        and custody["modified"] == 8
        and type(custody["changed"]) is int
        and custody["changed"] == 13
        and type(custody["candidate_path_count"]) is int
        and custody["candidate_path_count"] == 565
        and type(custody["filesystem_directory_count"]) is int
        and custody["filesystem_directory_count"] == EXPECTED_FILESYSTEM_DIRECTORY_COUNT
        and custody["filesystem_inventory"] == "bounded-no-follow-descriptor-walk"
        and type(custody["protected"]) is int
        and custody["protected"] == 552
        and custody["self_unhashed_paths"] == [CHECKER_RELATIVE, RUNNER_RELATIVE],
        "receipt path counts or self-unhashed boundary changed",
    )
    custody_projection_expectations = {
        "allowlist_sha256": (
            projections["allowlist"],
            "receipt allowlist projection differs from observed worktree",
        ),
        "full_candidate_projection_sha256": (
            projections["full_candidate"],
            "receipt full-candidate projection differs from observed worktree",
        ),
        "pinned_changed_projection_sha256": (
            projections["pinned_changed"],
            "receipt pinned-changed projection differs from observed worktree",
        ),
        "protected_projection_sha256": (
            projections["protected"],
            "receipt protected projection differs from observed worktree",
        ),
    }
    for key, (expected_projection, rejection) in custody_projection_expectations.items():
        require(
            require_hex(custody[key], HEX64, f"path custody {key}")
            == expected_projection,
            rejection,
        )
    premises = receipt["environmental_premises"]
    require(type(premises) is dict, "receipt environmental premises are not typed")
    require_exact_keys(
        premises, {"git", "python", "runtime_boundaries"}, "environmental premises"
    )
    expected_tool_paths = {"git": GIT, "python": PYTHON}
    expected_tool_versions = {
        "git": git_text(repository_root, "--version"),
        "python": sys.version.splitlines()[0],
    }
    for label in ("git", "python"):
        tool = premises[label]
        require(type(tool) is dict, f"{label} premise is not typed")
        require_exact_keys(tool, {"path", "sha256", "version"}, f"{label} premise")
        require(
            type(tool["path"]) is str
            and tool["path"] == expected_tool_paths[label],
            f"{label} receipt executable path changed",
        )
        require(
            type(tool["version"]) is str
            and tool["version"] == expected_tool_versions[label],
            f"{label} receipt version changed",
        )
        expected_digest = require_hex(tool["sha256"], HEX64, f"{label} digest")
        require(
            hashlib.sha256(
                stable_absolute_file(
                    Path(expected_tool_paths[label]),
                    EXPECTED_RESOURCE_BOUNDS["filesystem"]["tool_file_bytes"],
                    f"{label} executable",
                )
            ).hexdigest()
            == expected_digest,
            f"{label} receipt digest does not match the executable bytes",
        )
    runtime_boundaries = premises["runtime_boundaries"]
    require(type(runtime_boundaries) is dict, "runtime boundaries are not typed")
    require_exact_keys(
        runtime_boundaries,
        {
            "absolute_python_path_required_by_runner",
            "bash_and_path_provenance_authenticated",
            "child_preexec_unmasks_sigalrm_sigint",
            "default_action_sigterm_sighup_sigkill_cleanup",
            "dynamic_loader_authenticated",
            "external_or_native_waiters_authenticated",
            "hard_async_deadline_preemption_during_child_lifecycle",
            "one_enumerated_python_thread_required",
            "other_signal_dispositions_or_masks_authenticated",
            "owned_child_pthread_sigmask",
            "python_main_thread_required",
            "python_stdlib_and_extensions_authenticated",
            "sigalrm_sigint_handlers_are_nonraising_recorders",
            "sigchld_explicitly_reset_before_children",
        },
        "runtime boundaries",
    )
    require(
        typed_json_equal(
            runtime_boundaries,
            {
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
        ),
        "runtime boundary claims changed",
    )
    repository_context = receipt["repository_context"]
    require(type(repository_context) is dict, "repository context is not typed")
    require_exact_keys(
        repository_context,
        {
            "endpoint_equal",
            "git_command_timeout_seconds",
            "index",
            "local_config",
            "minimum_git_version",
            "object_pack_inventory",
            "object_verification_scope",
            "path_semantics_overrides",
            "promisor_routing_absent",
            "shallow",
        },
        "repository context",
    )
    require(
        repository_context["endpoint_equal"] is True
        and type(repository_context["git_command_timeout_seconds"]) is int
        and repository_context["git_command_timeout_seconds"] == 60
        and repository_context["minimum_git_version"] == "2.45.0"
        and repository_context["shallow"] is False
        and repository_context["promisor_routing_absent"] is True
        and repository_context["object_verification_scope"]
        == "exact anchor, candidate, and checkpoint objects actually traversed, framed, and rehashed",
        "repository endpoint, Git version, non-shallow, promisor-routing, or object-scope claim changed",
    )
    require(
        typed_json_equal(
            repository_context["object_pack_inventory"],
            observed_object_pack_inventory_receipt(repository_root),
        ),
        "repository object-pack inventory receipt differs from bounded metadata",
    )
    index_receipt = repository_context["index"]
    require(type(index_receipt) is dict, "repository index receipt is not typed")
    require_exact_keys(
        index_receipt,
        {
            "entry_count",
            "forbidden_extension_signatures_absent",
            "maximum_size",
            "mode",
            "sha256",
            "sha1_trailing_checksum_verified",
            "single_link_regular_no_split_index",
            "size",
            "stage_zero_v_flags",
            "version",
        },
        "repository index receipt",
    )
    require(
        typed_json_equal(index_receipt, observed_index_receipt(repository_root)),
        "repository index receipt differs from exact index bytes",
    )
    local_config = repository_context["local_config"]
    require(type(local_config) is dict, "repository local config receipt is not typed")
    require_exact_keys(
        local_config, {"record_count", "sha256", "size"}, "local config receipt"
    )
    require(
        typed_json_equal(local_config, observed_local_config_receipt(repository_root)),
        "repository local config receipt differs from the effective local config record stream",
    )
    require(
        repository_context["path_semantics_overrides"]
        == ["core.ignoreCase=false", "core.precomposeUnicode=false"],
        "repository path-semantics overrides changed",
    )
    return receipt


def require_success(
    observation: Observation,
    candidate: Candidate,
    lifecycle: str,
) -> bytes:
    require(
        observation.returncode == 0,
        "checker failed unexpectedly: "
        + observation.stderr.decode("utf-8", errors="replace").strip(),
    )
    require(not observation.stderr, "successful checker emitted stderr")
    validate_receipt(
        observation.stdout,
        tree=candidate.tree,
        checkpoint=candidate.checkpoint,
        lifecycle=lifecycle,
        repository_root=candidate.root,
    )
    return observation.stdout


def require_diagnostic_success(
    observation: Observation,
    candidate: Candidate,
    lifecycle: str,
) -> bytes:
    require(
        observation.returncode == 0,
        "diagnostic checker failed unexpectedly: "
        + observation.stderr.decode("utf-8", errors="replace").strip(),
    )
    require(not observation.stderr, "successful diagnostic checker emitted stderr")
    validate_receipt(
        observation.stdout,
        tree=None,
        checkpoint=None,
        lifecycle=lifecycle,
        repository_root=candidate.root,
    )
    return observation.stdout


def checker_rejection_marker(case_name: str) -> bytes:
    matches = [
        marker for marker, names in CHECKER_MARKER_GROUPS if case_name in names
    ]
    require(
        len(matches) == 1,
        f"checker rejection marker is not unique for {case_name}",
    )
    return matches[0]


def checker_rejection_payload(case: MutationCase, marker: bytes) -> bytes | None:
    exact_dynamic = {
        "topology_runner_hardlink": (
            b"worktree has a symlink, hardlink, or special node: "
            b"'scripts/check-c3-hosted-followup.sh'"
        ),
        "topology_untracked_fifo": (
            b"worktree has a symlink, hardlink, or special node: "
            b"'hostile-untracked.fifo'"
        ),
        "topology_extra_empty_directory": (
            b"worktree has an extra or empty directory: "
            b"'hostile-empty-directory'"
        ),
        "object_recursive_empty_tree": (
            b"'crates/zz-empty': empty tree paths are forbidden"
        ),
        "git_info_grafts": b"Git overlay file is forbidden: info/grafts",
        "git_object_alternates": (
            b"Git overlay file is forbidden: objects/info/alternates"
        ),
        "git_info_attributes": b"Git overlay file is forbidden: info/attributes",
        "git_config_worktree": b"Git overlay file is forbidden: config.worktree",
        "git_local_include": (
            b"local Git configuration key is forbidden: include.path"
        ),
        "git_local_filter": (
            b"local Git configuration key is forbidden: filter.hostile.clean"
        ),
        "git_sparse_checkout_config": (
            b"local Git configuration key is forbidden: core.sparsecheckout"
        ),
        "git_split_index_config": (
            b"local Git configuration key is forbidden: core.splitindex"
        ),
        "git_fsmonitor_config": (
            b"local Git configuration key is forbidden: core.fsmonitor"
        ),
        "git_untracked_cache_config": (
            b"local Git configuration key is forbidden: core.untrackedcache"
        ),
        "git_remote_promisor_config": (
            b"local Git configuration key is forbidden: remote.origin.promisor"
        ),
        "git_promisor_pack_marker": (
            b"Git promisor marker is forbidden: selftest-hostile.promisor"
        ),
        "resource_worktree_file_bytes": (
            b"'audit/evidence/c3-hosted-followup-correction-2026-08-01.md': "
            b"file exceeds the per-file byte bound"
        ),
        "resource_git_config_stdout": (
            b"Git config --no-includes --local --null --list stdout exceeds "
            b"the byte bound"
        ),
    }
    if case.name == "index_symlink":
        return None
    return exact_dynamic.get(case.name, marker)


def checker_rejection_is_exact(case: MutationCase, marker: bytes, raw: bytes) -> bool:
    expected_payload = checker_rejection_payload(case, marker)
    if expected_payload is not None:
        return raw == CHECKER_ERROR_PREFIX + expected_payload + b"\n"
    return (
        re.fullmatch(
            rb"ERROR: C3 hosted follow-up gate: cannot observe the private Git "
            rb"index: \[Errno [1-9][0-9]*\] [A-Za-z][A-Za-z ]*: "
            rb"'[^'\r\n]+/\.git/index'\n",
            raw,
        )
        is not None
    )


def exact_bootstrap_traceback(
    raw: bytes,
    *,
    exception_name: bytes,
    terminal_messages: tuple[bytes, ...],
) -> bool:
    lines = raw.splitlines(keepends=True)
    if not (
        len(lines) in {3, 4}
        and lines[0] == b"Traceback (most recent call last):\n"
        and re.fullmatch(
            rb'  File "<(?:stdin|string)>", line [1-9][0-9]*, in <module>\n',
            lines[1],
        )
        is not None
    ):
        return False
    for message in terminal_messages:
        terminal = exception_name + b": " + message
        if len(lines) == 3 and lines[2] == terminal:
            return True
        source = (
            b"    raise "
            + exception_name
            + b'(\"'
            + message.removesuffix(b"\n")
            + b'\")\n'
        )
        if len(lines) == 4 and lines[2] == source and lines[3] == terminal:
            return True
    return False


def exact_bootstrap_no_follow_traceback(raw: bytes) -> bool:
    lines = raw.splitlines(keepends=True)
    if not (
        len(lines) in {3, 4}
        and lines[0] == b"Traceback (most recent call last):\n"
        and re.fullmatch(
            rb'  File "<(?:stdin|string)>", line [1-9][0-9]*, in <module>\n',
            lines[1],
        )
        is not None
    ):
        return False
    if len(lines) == 4 and lines[2] != (
        b"    leaf = os.open(parts[-1], leaf_flags, dir_fd=descriptor)\n"
    ):
        return False
    return (
        re.fullmatch(
            rb"OSError: \[Errno [1-9][0-9]*\] [A-Za-z][A-Za-z ]*: "
            rb"'check-c3-hosted-followup\.py'\n",
            lines[-1],
        )
        is not None
    )


def require_rejected(observation: Observation, case: MutationCase) -> str:
    boundary = case.expected_boundary
    require(
        boundary
        not in {
            ExpectedBoundary.RECEIPT_VALIDATOR,
            ExpectedBoundary.ISOLATED_EQUIVALENT,
        },
        f"{case.name}: non-process boundary reached process rejection classifier",
    )
    require(not observation.stdout, f"{case.name}: rejected process emitted stdout")
    if boundary is ExpectedBoundary.CHECKER:
        marker = checker_rejection_marker(case.name)
        require(
            observation.returncode == 1
            and checker_rejection_is_exact(case, marker, observation.stderr),
            f"{case.name}: checker rejected at the wrong boundary: "
            + observation.stderr.decode("utf-8", errors="replace").strip(),
        )
    elif boundary is ExpectedBoundary.ARGUMENT_PARSER:
        require(
            observation.returncode == 2
            and observation.stderr == ARGUMENT_PARSER_ERROR,
            f"{case.name}: argument parser rejection changed",
        )
    elif boundary is ExpectedBoundary.PYTHON_PRECONDITION:
        require(
            observation.returncode == 2
            and observation.stderr == PYTHON_PRECONDITION_ERROR,
            f"{case.name}: Python precondition rejection changed",
        )
    elif boundary is ExpectedBoundary.EXACT_SOURCE_SIZE:
        require(
            observation.returncode == 1
            and exact_bootstrap_traceback(
                observation.stderr,
                exception_name=b"RuntimeError",
                terminal_messages=tuple(
                    suffix.removeprefix(b"RuntimeError: ")
                    for suffix in EXACT_SOURCE_SIZE_ERROR_SUFFIXES
                ),
            ),
            f"{case.name}: exact-source size rejection changed",
        )
    elif boundary is ExpectedBoundary.EXACT_SOURCE_DIGEST:
        require(
            observation.returncode == 1
            and exact_bootstrap_traceback(
                observation.stderr,
                exception_name=b"RuntimeError",
                terminal_messages=tuple(
                    suffix.removeprefix(b"RuntimeError: ")
                    for suffix in EXACT_SOURCE_DIGEST_ERROR_SUFFIXES
                ),
            ),
            f"{case.name}: exact-source digest rejection changed",
        )
    elif boundary is ExpectedBoundary.EXACT_SOURCE_ENDPOINT:
        require(
            observation.returncode == 1
            and exact_bootstrap_traceback(
                observation.stderr,
                exception_name=b"RuntimeError",
                terminal_messages=tuple(
                    suffix.removeprefix(b"RuntimeError: ")
                    for suffix in EXACT_SOURCE_ENDPOINT_ERROR_SUFFIXES
                ),
            ),
            f"{case.name}: exact-source endpoint rejection changed",
        )
    elif boundary is ExpectedBoundary.EXACT_SOURCE_PATH:
        require(
            observation.returncode == 1
            and exact_bootstrap_no_follow_traceback(observation.stderr),
            f"{case.name}: exact-source no-follow rejection changed",
        )
    else:
        raise SelfTestError(f"{case.name}: unsupported rejection boundary")
    return boundary.value


def append_marker(root: Path, relative: str, marker: bytes) -> None:
    path = root / relative
    mode = stat.S_IMODE(path.lstat().st_mode)
    write_regular(path, path.read_bytes() + marker, mode)


def replace_once(root: Path, relative: str, old: bytes, new: bytes) -> None:
    path = root / relative
    before = path.read_bytes()
    require(
        before.count(old) == 1, f"{relative}: mutation token is not unique: {old!r}"
    )
    mode = stat.S_IMODE(path.lstat().st_mode)
    write_regular(path, before.replace(old, new, 1), mode)


def set_runner_declared_size(
    root: Path,
    pattern: re.Pattern[bytes],
    declaration: bytes,
    expected_size: int,
) -> None:
    require(
        declaration in {b"CHECKER_SIZE", b"SELF_TEST_SIZE"}
        and 0 < expected_size <= MAX_EXACT_SOURCE_BYTES,
        "runner-size fixture arguments are invalid",
    )
    path = root / RUNNER_RELATIVE
    before = path.read_bytes()
    require(len(pattern.findall(before)) == 1, "runner size declaration is not unique")
    replacement = (
        b"readonly " + declaration + b'="' + str(expected_size).encode("ascii") + b'"'
    )
    after = pattern.sub(replacement, before, count=1)
    write_regular(path, after, stat.S_IMODE(path.lstat().st_mode))


def anchor_blob(root: Path, relative: str) -> bytes:
    result = git_process(root, "show", f"{ANCHOR}:{relative}")
    return result.stdout


def git_common_dir(root: Path) -> Path:
    raw = Path(git_text(root, "rev-parse", "--git-common-dir"))
    if not raw.is_absolute():
        raw = root / raw
    return raw.resolve(strict=True)


def set_committed(candidate: Candidate) -> None:
    git_process(
        candidate.root, "update-ref", "--no-deref", "HEAD", candidate.checkpoint, ANCHOR
    )
    git_process(candidate.root, "read-tree", candidate.tree)
    require(
        git_text(candidate.root, "rev-parse", "HEAD") == candidate.checkpoint,
        "failed to install committed lifecycle HEAD",
    )
    require(
        not git_process(
            candidate.root, "status", "--porcelain=v2", "--untracked-files=all"
        ).stdout,
        "installed committed lifecycle is dirty",
    )


def signed_checkpoint(root: Path, checkpoint: str) -> str:
    raw = git_process(root, "cat-file", "commit", checkpoint).stdout
    header, separator, message = raw.partition(b"\n\n")
    require(separator == b"\n\n", "baseline checkpoint is malformed")
    lines = header.splitlines()
    require(len(lines) == 4, "baseline checkpoint envelope changed")
    hostile_header = b"\n".join(
        (
            lines[0],
            lines[1],
            lines[2],
            lines[3],
            b"gpgsig -----BEGIN PGP SIGNATURE-----",
            b" hostile",
            b" -----END PGP SIGNATURE-----",
        )
    )
    result = git_process(
        root,
        "hash-object",
        "-t",
        "commit",
        "-w",
        "--stdin",
        input_bytes=hostile_header + b"\n\n" + message,
    )
    commit = result.stdout.decode("ascii", errors="strict").strip()
    require(HEX40.fullmatch(commit) is not None, "signed mutation object id is invalid")
    return commit


def corrupt_recursive_tree_object(candidate: Candidate) -> None:
    subtree = git_text(candidate.root, "rev-parse", f"{candidate.tree}:crates")
    require(HEX40.fullmatch(subtree) is not None, "recursive subtree id is malformed")
    common = git_common_dir(candidate.root)
    objects = common / "objects"
    alternates = objects / "info/alternates"
    require(
        not alternates.exists() and not alternates.is_symlink(),
        "recursive corruption fixture unexpectedly has object alternates",
    )
    pack_directory = objects / "pack"
    disabled_packs = objects / "selftest-disabled-packs"
    require(
        pack_directory.is_dir()
        and not disabled_packs.exists()
        and not disabled_packs.is_symlink(),
        "recursive corruption fixture pack topology changed",
    )
    saved_packs = tuple(sorted(pack_directory.glob("*.pack")))
    require(bool(saved_packs), "recursive corruption fixture has no saved pack")
    pack_directory.rename(disabled_packs)
    pack_directory.mkdir(mode=0o755)
    for saved_pack in saved_packs:
        relocated = disabled_packs / saved_pack.name
        body = stable_absolute_file(
            relocated,
            MAX_SELF_TEST_PACK_BYTES,
            "saved pack during loose-object materialization",
        )
        git_process(candidate.root, "unpack-objects", "-r", input_bytes=body)
    require(
        not any(pack_directory.iterdir()),
        "unpack-objects unexpectedly repopulated the active pack directory",
    )
    git_process(candidate.root, "fsck", "--full", "--no-dangling")
    body = git_process(candidate.root, "cat-file", "tree", subtree).stdout
    require(bool(body), "selected recursive subtree is unexpectedly empty")
    corrupted = bytearray(body)
    corrupted[-1] ^= 1
    loose = zlib.compress(f"tree {len(corrupted)}\0".encode("ascii") + bytes(corrupted))
    object_path = objects / subtree[:2] / subtree[2:]
    require(object_path.is_file(), "recursive subtree was not materialized loose")
    write_regular(object_path, loose, 0o644)
    corrupted_observation = git_process(
        candidate.root,
        "cat-file",
        "tree",
        subtree,
        check=False,
    )
    require(
        corrupted_observation.returncode == 0
        and corrupted_observation.stdout == bytes(corrupted)
        and hashlib.sha1(
            f"tree {len(corrupted)}\0".encode("ascii") + bytes(corrupted)
        ).hexdigest()
        != subtree,
        "corrupted recursive tree was not selected as the mismatched object bytes",
    )


def immediate_tree_records(root: Path, tree: str) -> list[bytes]:
    raw = git_process(root, "ls-tree", "-z", tree).stdout
    records = [record for record in raw.split(b"\0") if record]
    require(bool(records), "tree mutation selected an empty parent")
    return records


def tree_record_sort_key(record: bytes) -> bytes:
    metadata, separator, name = record.partition(b"\t")
    require(separator == b"\t" and bool(name), "mktree record is malformed")
    mode = metadata.partition(b" ")[0]
    return name + (b"/" if mode == b"040000" else b"")


def mktree(root: Path, records: list[bytes]) -> str:
    ordered = sorted(records, key=tree_record_sort_key)
    body = b"\0".join(ordered) + (b"\0" if ordered else b"")
    result = git_process(root, "mktree", "-z", input_bytes=body)
    tree = result.stdout.decode("ascii", errors="strict").strip()
    require(HEX40.fullmatch(tree) is not None, "mktree returned an invalid tree id")
    return tree


def hash_object(root: Path, kind: str, body: bytes, *, literally: bool = False) -> str:
    require(kind in {"blob", "commit", "tree"}, "invalid hostile object kind")
    arguments = ["hash-object", "-t", kind, "-w"]
    if literally:
        arguments.append("--literally")
    arguments.append("--stdin")
    result = git_process(root, *arguments, input_bytes=body)
    object_id = result.stdout.decode("ascii", errors="strict").strip()
    require(
        HEX40.fullmatch(object_id) is not None,
        f"hash-object returned an invalid {kind} id",
    )
    return object_id


def one_blob_tree(root: Path, body: bytes = b"resource fixture\n") -> str:
    blob = hash_object(root, "blob", body)
    return mktree(root, [f"100644 blob {blob}\tleaf".encode("ascii")])


def long_tree_component(index: int) -> str:
    prefix = f"d{index:04d}-"
    require(len(prefix) < 255, "long tree component prefix is too large")
    return prefix + ("x" * (255 - len(prefix)))


def wide_directory_tree(root: Path, child: str, count: int) -> str:
    require(0 < count < 10_000, "wide-tree fixture count is outside its bound")
    records = [
        f"040000 tree {child}\t{long_tree_component(index)}".encode("ascii")
        for index in range(count)
    ]
    return mktree(root, records)


def resource_tree_aggregate_fixture(root: Path) -> str:
    # The 565-entry root repeatedly references one cached three-tree chain.
    # Logical visits charge 637,885 raw bytes while remaining below the path,
    # object-visit, component, path-length, depth, and per-tree bounds.
    long_name = long_tree_component(9_999)
    blob = hash_object(root, "blob", b"resource fixture\n")
    leaf = mktree(
        root, [f"100644 blob {blob}\t{long_name}".encode("ascii")]
    )
    middle = mktree(
        root, [f"040000 tree {leaf}\t{long_name}".encode("ascii")]
    )
    top = mktree(
        root, [f"040000 tree {middle}\t{long_name}".encode("ascii")]
    )
    return wide_directory_tree(root, top, 565)


def resource_blob_tree(root: Path, body: bytes, references: int) -> str:
    require(0 < references <= 565, "blob resource fixture reference count changed")
    blob = hash_object(root, "blob", body)
    records = [
        f"100644 blob {blob}\tresource-{index:03d}".encode("ascii")
        for index in range(references)
    ]
    return mktree(root, records)


def install_worktree_aggregate_fixture(root: Path) -> None:
    raw = git_process(root, "ls-files", "-z").stdout
    paths = [
        record.decode("utf-8", errors="strict")
        for record in raw.split(b"\0")
        if record
    ]
    selected = [
        path
        for path in paths
        if path not in {CHECKER_RELATIVE, SELF_TEST_RELATIVE, RUNNER_RELATIVE}
    ][:13]
    require(len(selected) == 13, "worktree aggregate fixture lacks regular files")
    body = b"x" * (EXPECTED_RESOURCE_BOUNDS["filesystem"]["worktree_file_bytes"] - 1)
    for relative in selected:
        mode = stat.S_IMODE((root / relative).lstat().st_mode)
        write_regular(root / relative, body, mode)


def install_worktree_node_fixture(root: Path) -> None:
    parent = root / ".github"
    require(parent.is_dir() and not parent.is_symlink(), "node fixture root changed")
    with os.scandir(parent) as iterator:
        existing = sum(1 for _entry in iterator)
    maximum_entries = EXPECTED_RESOURCE_BOUNDS["filesystem"]["directory_entries"]
    require(0 < existing < maximum_entries, "node fixture baseline is outside bounds")
    for index in range(maximum_entries - existing):
        (parent / f"selftest-node-{index:04d}").mkdir()


def install_large_local_config(root: Path) -> None:
    config = git_common_dir(root) / "config"
    before = config.read_bytes()
    hostile = bytearray(before)
    hostile.extend(b"\n[selftest-resource]\n")
    for index in range(3_000):
        hostile.extend(f"\tkey{index:04d} = ".encode("ascii"))
        hostile.extend(b"x" * 96)
        hostile.extend(b"\n")
    require(
        len(hostile)
        > EXPECTED_RESOURCE_BOUNDS["processes"]["git_config_stdout_bytes"],
        "local-config fixture is not oversized",
    )
    write_regular(config, bytes(hostile), stat.S_IMODE(config.lstat().st_mode))


def candidate_with_recursive_empty_tree(candidate: Candidate) -> tuple[str, str]:
    empty_tree = (
        git_process(candidate.root, "mktree", "-z", input_bytes=b"")
        .stdout.decode("ascii", errors="strict")
        .strip()
    )
    require(HEX40.fullmatch(empty_tree) is not None, "empty-tree id is malformed")
    crates_tree = git_text(candidate.root, "rev-parse", f"{candidate.tree}:crates")
    crates_records = immediate_tree_records(candidate.root, crates_tree)
    crates_records.append(f"040000 tree {empty_tree}\tzz-empty".encode("ascii"))
    hostile_crates = mktree(candidate.root, crates_records)
    root_records = immediate_tree_records(candidate.root, candidate.tree)
    replacement = f"040000 tree {hostile_crates}\tcrates".encode("ascii")
    replaced = False
    for index, record in enumerate(root_records):
        if record.partition(b"\t")[2] == b"crates":
            root_records[index] = replacement
            replaced = True
            break
    require(replaced, "candidate root tree has no crates subtree")
    hostile_tree = mktree(candidate.root, root_records)
    checkpoint = create_commit(candidate.root, hostile_tree, (ANCHOR,))
    return hostile_tree, checkpoint


def mutate_case(
    case: MutationCase,
    candidate: Candidate,
    *,
    template: Candidate,
    exact_runner: bool,
    python_mode: PythonMode,
) -> Observation:
    name = case.name
    arguments = external_arguments(candidate)
    force_runner = False
    force_direct = False

    if name == "cli_no_external_custody":
        arguments = []
    elif name == "cli_tree_without_checkpoint":
        arguments = ["--expected-candidate-tree", candidate.tree]
    elif name == "cli_checkpoint_without_tree":
        arguments = ["--checkpoint-commit", candidate.checkpoint]
    elif name == "cli_pair_with_diagnostic":
        arguments.append("--diagnostic-without-external-custody")
    elif name == "cli_malformed_tree":
        arguments[1] = "f" * 39
    elif name == "cli_malformed_checkpoint":
        arguments[3] = "g" * 40
    elif name == "cli_unknown_argument":
        arguments.append("--hostile-unknown-option")
    elif name == "path_extra_untracked":
        write_regular(candidate.root / "hostile-extra.txt", b"unexpected\n")
    elif name == "path_ignored_python_cache":
        write_regular(
            candidate.root / "__pycache__/hostile.cpython-314.pyc", b"hostile cache\n"
        )
    elif name == "path_missing_added_receipt":
        (candidate.root / RECEIPT_RELATIVE).unlink()
    elif name == "path_reverted_modified_agents":
        write_regular(
            candidate.root / "AGENTS.md", anchor_blob(candidate.root, "AGENTS.md")
        )
    elif name == "protected_science_source":
        append_marker(
            candidate.root,
            "crates/pid-core/src/lib.rs",
            b"\n// hostile science mutation\n",
        )
    elif name == "protected_formal_claim":
        append_marker(
            candidate.root,
            "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
            b"\nHostile formal mutation.\n",
        )
    elif name == "protected_cargo_manifest":
        append_marker(candidate.root, "Cargo.toml", b"\n# hostile manifest mutation\n")
    elif name == "blob_agents":
        append_marker(
            candidate.root, "AGENTS.md", b"\nHostile allowed-blob mutation.\n"
        )
    elif name == "blob_changelog":
        append_marker(
            candidate.root, "CHANGELOG.md", b"\nHostile allowed-blob mutation.\n"
        )
    elif name == "blob_justfile":
        append_marker(
            candidate.root, "justfile", b"\n# hostile allowed-blob mutation\n"
        )
    elif name == "blob_scripts_readme":
        append_marker(
            candidate.root, "scripts/README.md", b"\nHostile allowed-blob mutation.\n"
        )
    elif name == "blob_correction_receipt":
        append_marker(
            candidate.root, RECEIPT_RELATIVE, b"\nHostile receipt mutation.\n"
        )
    elif name == "blob_certified_claim_checker":
        append_marker(
            candidate.root,
            CERTIFIED_CLAIM_CHECKER_RELATIVE,
            b"\n# hostile allowed-blob mutation\n",
        )
    elif name == "certified_claim_rebind_semantic":
        claim_path = candidate.root / CERTIFIED_CLAIM_CHECKER_RELATIVE
        claim_mode = stat.S_IMODE(claim_path.lstat().st_mode)
        hostile_claim = claim_path.read_bytes() + b"\n# hostile semantic mutation\n"
        write_regular(claim_path, hostile_claim, claim_mode)

        projections = observed_worktree_projections(candidate.root)
        hostile_pinned_projection = projections["pinned_changed"].encode("ascii")
        checker_path = candidate.root / CHECKER_RELATIVE
        checker = checker_path.read_bytes()
        require(
            len(CHECKER_CERTIFIED_CLAIM_BLOB.findall(checker)) == 1,
            "checker certified-claim blob binding is not unique",
        )
        hostile_claim_size = f"{len(hostile_claim):_}".encode("ascii")
        hostile_claim_sha256 = hashlib.sha256(hostile_claim).hexdigest().encode(
            "ascii"
        )
        checker = CHECKER_CERTIFIED_CLAIM_BLOB.sub(
            lambda match: (
                match.group("prefix")
                + hostile_claim_size
                + match.group("middle")
                + hostile_claim_sha256
                + match.group("suffix")
            ),
            checker,
            count=1,
        )
        require(
            len(CHECKER_PINNED_CHANGED_PROJECTION.findall(checker)) == 1,
            "checker pinned-changed projection binding is not unique",
        )
        checker = CHECKER_PINNED_CHANGED_PROJECTION.sub(
            lambda match: (
                match.group("prefix")
                + hostile_pinned_projection
                + match.group("suffix")
            ),
            checker,
            count=1,
        )
        write_regular(
            checker_path,
            checker,
            stat.S_IMODE(checker_path.lstat().st_mode),
        )

        runner_path = candidate.root / RUNNER_RELATIVE
        set_runner_declared_size(
            candidate.root,
            RUNNER_CHECKER_SIZE,
            b"CHECKER_SIZE",
            len(checker),
        )
        runner = runner_path.read_bytes()
        require(
            len(RUNNER_CHECKER_HASH.findall(runner)) == 1,
            "runner checker digest is not unique",
        )
        runner = RUNNER_CHECKER_HASH.sub(
            b'readonly CHECKER_SHA256="'
            + hashlib.sha256(checker).hexdigest().encode("ascii")
            + b'"',
            runner,
            count=1,
        )
        write_regular(runner_path, runner, 0o755)

        hostile_tree = build_tree_with_captured_blobs(
            candidate.root,
            candidate.root.parent / "claim-semantic.index",
        )
        hostile_checkpoint = create_commit(
            candidate.root, hostile_tree, (ANCHOR,)
        )
        candidate = Candidate(
            root=candidate.root,
            tree=hostile_tree,
            checkpoint=hostile_checkpoint,
        )
        arguments = external_arguments(candidate)
        force_runner = True
    elif name == "workflow_remove_libertinus_package":
        replace_once(
            candidate.root,
            ".github/workflows/ci.yml",
            b"            texlive-fonts-extra \\\n",
            b"            # texlive-fonts-extra removed by mutation\n",
        )
    elif name == "workflow_bypass_exact_source_runner":
        replace_once(
            candidate.root,
            ".github/workflows/ci.yml",
            (
                b"          scripts/check-c3-hosted-followup.sh normal self-test \\\n"
                b"            --compare-runner-modes \\\n"
                b'            --expected-candidate-tree "$candidate_tree" \\\n'
                b'            --checkpoint-commit "$checkpoint"\n'
            ),
            (
                b"          python3 -I -S "
                b"scripts/check-c3-hosted-followup-self-test.py \\\n"
                b"            --compare-runner-modes \\\n"
                b'            --expected-candidate-tree "$candidate_tree" \\\n'
                b'            --checkpoint-commit "$checkpoint"\n'
            ),
        )
    elif name == "rust_remove_final_status_seam":
        replace_once(
            candidate.root,
            "crates/pid-core/build_support.rs",
            b"after_first_status();",
            b"/* after_first_status removed */",
        )
    elif name == "rust_restore_shell_wrapper_route":
        replace_once(
            candidate.root,
            "crates/pid-core/tests/software_identity_build.rs",
            b"changed after first status\\n",
            b"change-after-status-git",
        )
    elif name == "historical_change_parent_pin":
        replace_once(
            candidate.root,
            HISTORICAL_WRAPPER_RELATIVE,
            b"8b792bc143fff2d84f2d8e7817d1de7850741223",
            b"8b792bc143fff2d84f2d8e7817d1de7850741222",
        )
    elif name == "historical_change_status_digest":
        replace_once(
            candidate.root,
            HISTORICAL_WRAPPER_RELATIVE,
            b"1e1dc75985155d2a1ae3caff43fa8b09767cddaebd58f087266c335819619a85",
            b"0e1dc75985155d2a1ae3caff43fa8b09767cddaebd58f087266c335819619a85",
        )
    elif name == "historical_remove_optimized_self_test":
        replace_once(
            candidate.root,
            HISTORICAL_WRAPPER_RELATIVE,
            b"python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py",
            b"python3 -I -S scripts/check-ksg-phase-isolation-self-test.py",
        )
    elif name == "source_checker_bytes":
        append_marker(candidate.root, CHECKER_RELATIVE, b"\n# hostile checker source\n")
    elif name == "source_self_test_bytes":
        self_test_path = candidate.root / SELF_TEST_RELATIVE
        baseline = self_test_path.read_bytes()
        require(len(baseline) > 1, "self-test source fixture is unexpectedly empty")
        set_runner_declared_size(
            candidate.root,
            RUNNER_SELF_TEST_SIZE,
            b"SELF_TEST_SIZE",
            len(baseline),
        )
        write_regular(
            self_test_path,
            baseline[:-1],
            stat.S_IMODE(self_test_path.lstat().st_mode),
        )
        return process(
            [
                str(candidate.root / RUNNER_RELATIVE),
                python_mode.value,
                "self-test",
            ],
            cwd=candidate.root,
            timeout_seconds=TARGET_PROCESS_TIMEOUT_SECONDS,
        )
    elif name == "source_runner_bytes":
        append_marker(candidate.root, RUNNER_RELATIVE, b"\n# hostile runner source\n")
    elif name == "source_runner_checker_digest":
        runner_path = candidate.root / RUNNER_RELATIVE
        checker_size = len(
            stable_file(
                candidate.root,
                CHECKER_RELATIVE,
                maximum_bytes=MAX_EXACT_SOURCE_BYTES,
            )[1]
        )
        set_runner_declared_size(
            candidate.root,
            RUNNER_CHECKER_SIZE,
            b"CHECKER_SIZE",
            checker_size,
        )
        before = runner_path.read_bytes()
        require(
            len(RUNNER_CHECKER_HASH.findall(before)) == 1,
            "runner checker digest is not unique",
        )
        after = RUNNER_CHECKER_HASH.sub(
            b'readonly CHECKER_SHA256="' + b"1" * 64 + b'"', before, count=1
        )
        write_regular(runner_path, after, 0o755)
        force_runner = True
    elif name == "source_runner_self_test_digest":
        runner_path = candidate.root / RUNNER_RELATIVE
        self_test_size = len(
            stable_file(
                candidate.root,
                SELF_TEST_RELATIVE,
                maximum_bytes=MAX_EXACT_SOURCE_BYTES,
            )[1]
        )
        set_runner_declared_size(
            candidate.root,
            RUNNER_SELF_TEST_SIZE,
            b"SELF_TEST_SIZE",
            self_test_size,
        )
        before = runner_path.read_bytes()
        require(
            len(RUNNER_SELF_TEST_HASH.findall(before)) == 1,
            "runner self-test digest is not unique",
        )
        after = RUNNER_SELF_TEST_HASH.sub(
            b'readonly SELF_TEST_SHA256="' + b"1" * 64 + b'"', before, count=1
        )
        write_regular(runner_path, after, 0o755)
        return process(
            [str(runner_path), python_mode.value, "self-test"],
            cwd=candidate.root,
            timeout_seconds=TARGET_PROCESS_TIMEOUT_SECONDS,
        )
    elif name == "source_checker_mid_execution_append":
        checker_path = candidate.root / CHECKER_RELATIVE
        before = checker_path.read_bytes()
        insertion_point = b"import time\nfrom typing import Any\n"
        require(
            before.count(insertion_point) == 1,
            "checker race insertion point is not unique",
        )
        hostile = before.replace(
            insertion_point,
            insertion_point
            + b"\nif globals().get('__pid_rs_exact_source_context__') is not None:\n"
            + b"    with open(__file__, 'ab') as _endpoint_race_file:\n"
            + b"        _endpoint_race_file.write(b'\\n# deterministic endpoint race\\n')\n"
            + b"    raise SystemExit(0)\n",
            1,
        )
        require(
            0 < len(hostile) <= MAX_EXACT_SOURCE_BYTES,
            "checker race source exceeds the exact-source cap",
        )
        write_regular(checker_path, hostile, stat.S_IMODE(checker_path.lstat().st_mode))
        runner_path = candidate.root / RUNNER_RELATIVE
        set_runner_declared_size(
            candidate.root,
            RUNNER_CHECKER_SIZE,
            b"CHECKER_SIZE",
            len(hostile),
        )
        runner = runner_path.read_bytes()
        require(
            len(RUNNER_CHECKER_HASH.findall(runner)) == 1,
            "runner checker digest is not unique",
        )
        runner = RUNNER_CHECKER_HASH.sub(
            b'readonly CHECKER_SHA256="'
            + hashlib.sha256(hostile).hexdigest().encode("ascii")
            + b'"',
            runner,
            count=1,
        )
        write_regular(runner_path, runner, 0o755)
        force_runner = True
    elif name == "source_python_not_isolated":
        return invoke_checker(
            candidate,
            arguments,
            python_mode=python_mode,
            exact_runner=False,
            python_flags=("-S",),
        )
    elif name == "source_python_site_enabled":
        return invoke_checker(
            candidate,
            arguments,
            python_mode=python_mode,
            exact_runner=False,
            python_flags=("-I",),
        )
    elif name == "source_pythonpath_shadow":
        attacker = candidate.root.parent / f"pythonpath-{name}"
        attacker.mkdir()
        write_regular(
            attacker / "hashlib.py", b"raise RuntimeError('PYTHONPATH was imported')\n"
        )
        control = invoke_checker(
            candidate,
            arguments,
            python_mode=python_mode,
            exact_runner=exact_runner,
        )
        require_success(control, candidate, "precommit-worktree")
        observation = invoke_checker(
            candidate,
            arguments,
            python_mode=python_mode,
            exact_runner=exact_runner,
            environment_extra={"PYTHONPATH": str(attacker)},
        )
        require_success(observation, candidate, "precommit-worktree")
        require(
            observation.stdout == control.stdout,
            "PYTHONPATH isolation changed the canonical receipt",
        )
        return observation
    elif name == "topology_checker_mode":
        (candidate.root / CHECKER_RELATIVE).chmod(0o644)
    elif name == "topology_self_test_mode":
        (candidate.root / SELF_TEST_RELATIVE).chmod(0o644)
    elif name == "topology_runner_mode":
        (candidate.root / RUNNER_RELATIVE).chmod(0o644)
        force_direct = True
    elif name == "topology_checker_symlink":
        path = candidate.root / CHECKER_RELATIVE
        path.unlink()
        path.symlink_to("check-c3-hosted-followup.sh")
    elif name == "topology_runner_hardlink":
        os.link(
            candidate.root / RUNNER_RELATIVE,
            candidate.root.parent / "runner-hardlink-target",
        )
    elif name == "topology_untracked_fifo":
        require(hasattr(os, "mkfifo"), "platform cannot construct the FIFO mutation")
        os.mkfifo(candidate.root / "hostile-untracked.fifo", 0o600)
    elif name == "topology_extra_empty_directory":
        (candidate.root / "hostile-empty-directory").mkdir()
    elif name == "index_assume_unchanged":
        git_process(
            candidate.root, "update-index", "--assume-unchanged", "--", "AGENTS.md"
        )
    elif name == "index_skip_worktree":
        git_process(
            candidate.root, "update-index", "--skip-worktree", "--", "AGENTS.md"
        )
    elif name == "index_fsmonitor_extension":
        git_process(candidate.root, "update-index", "--fsmonitor")
        require(
            b"FSMN" in git_index_path(candidate.root).read_bytes(),
            "Git did not deterministically construct the FSMN index extension",
        )
    elif name == "index_split":
        git_process(candidate.root, "update-index", "--split-index")
        require(
            bool(git_text(candidate.root, "rev-parse", "--shared-index-path")),
            "Git did not deterministically construct a split index",
        )
    elif name == "index_symlink":
        index_path = git_index_path(candidate.root)
        target = candidate.root.parent / f"{candidate.root.name}-index-target"
        write_regular(target, index_path.read_bytes(), 0o644)
        index_path.unlink()
        index_path.symlink_to(target)
    elif name == "index_hardlink":
        os.link(
            git_index_path(candidate.root),
            candidate.root.parent / f"{candidate.root.name}-index-hardlink",
        )
    elif name == "lifecycle_full_candidate_index":
        git_process(candidate.root, "read-tree", candidate.tree)
    elif name == "lifecycle_single_staged_path":
        git_process(candidate.root, "add", "--", "AGENTS.md")
    elif name == "lifecycle_missing_worktree_path":
        (candidate.root / ".github/workflows/ci.yml").unlink()
    elif name == "lifecycle_committed_dirty":
        set_committed(candidate)
        append_marker(candidate.root, "AGENTS.md", b"\nHostile committed dirt.\n")
    elif name == "lifecycle_committed_untracked":
        set_committed(candidate)
        write_regular(candidate.root / "committed-untracked.txt", b"hostile\n")
    elif name == "lifecycle_committed_descendant":
        descendant = create_commit(
            candidate.root, candidate.tree, (candidate.checkpoint,)
        )
        git_process(
            candidate.root, "update-ref", "--no-deref", "HEAD", descendant, ANCHOR
        )
        git_process(candidate.root, "read-tree", candidate.tree)
    elif name == "commit_wrong_parent":
        parent = git_text(candidate.root, "rev-parse", f"{ANCHOR}^")
        arguments[3] = create_commit(candidate.root, candidate.tree, (parent,))
    elif name == "commit_wrong_tree":
        arguments[3] = create_commit(candidate.root, ANCHOR_TREE, (ANCHOR,))
    elif name == "commit_wrong_message":
        arguments[3] = create_commit(
            candidate.root, candidate.tree, (ANCHOR,), message="fix: weakened C3 gate\n"
        )
    elif name == "commit_wrong_identity":
        arguments[3] = create_commit(
            candidate.root, candidate.tree, (ANCHOR,), name="Hostile Identity"
        )
    elif name == "commit_signature_header":
        arguments[3] = signed_checkpoint(candidate.root, candidate.checkpoint)
    elif name == "commit_merge_parents":
        other_parent = git_text(candidate.root, "rev-parse", f"{ANCHOR}^")
        arguments[3] = create_commit(
            candidate.root, candidate.tree, (ANCHOR, other_parent)
        )
    elif name == "commit_descendant_checkpoint":
        arguments[3] = create_commit(
            candidate.root, candidate.tree, (candidate.checkpoint,)
        )
    elif name == "object_recursive_tree_hash_corruption":
        corrupt_recursive_tree_object(candidate)
    elif name == "object_recursive_empty_tree":
        arguments[1], arguments[3] = candidate_with_recursive_empty_tree(candidate)
    elif name == "git_info_grafts":
        write_regular(
            git_common_dir(candidate.root) / "info/grafts",
            f"{ANCHOR} {ANCHOR}^\n".encode(),
        )
    elif name == "git_object_alternates":
        template_common = git_common_dir(template.root)
        write_regular(
            git_common_dir(candidate.root) / "objects/info/alternates",
            (str(template_common / "objects") + "\n").encode("utf-8"),
        )
    elif name == "git_info_attributes":
        write_regular(
            git_common_dir(candidate.root) / "info/attributes", b"* filter=hostile\n"
        )
    elif name == "git_config_worktree":
        write_regular(
            git_common_dir(candidate.root) / "config.worktree",
            b"[core]\n\tbare = false\n",
        )
    elif name == "git_replacement_ref":
        parent = git_text(candidate.root, "rev-parse", f"{ANCHOR}^")
        git_process(candidate.root, "update-ref", f"refs/replace/{ANCHOR}", parent)
    elif name == "git_local_include":
        git_process(candidate.root, "config", "--local", "include.path", "/dev/null")
    elif name == "git_local_filter":
        git_process(
            candidate.root, "config", "--local", "filter.hostile.clean", "false"
        )
    elif name == "git_sparse_checkout_config":
        git_process(candidate.root, "config", "--local", "core.sparseCheckout", "true")
    elif name == "git_split_index_config":
        git_process(candidate.root, "config", "--local", "core.splitIndex", "true")
    elif name == "git_fsmonitor_config":
        git_process(candidate.root, "config", "--local", "core.fsmonitor", "true")
    elif name == "git_untracked_cache_config":
        git_process(candidate.root, "config", "--local", "core.untrackedCache", "true")
    elif name == "git_remote_promisor_config":
        git_process(candidate.root, "config", "--local", "remote.origin.promisor", "true")
    elif name == "git_promisor_pack_marker":
        write_regular(
            git_common_dir(candidate.root)
            / "objects/pack/selftest-hostile.promisor",
            b"hostile promisor marker\n",
            0o644,
        )
    elif name == "resource_commit_object_bytes":
        baseline = git_process(
            candidate.root, "cat-file", "commit", candidate.checkpoint
        ).stdout
        minimum = EXPECTED_RESOURCE_BOUNDS["git_objects"]["commit_per_object_bytes"] + 1
        require(len(baseline) < minimum, "baseline checkpoint already exceeds its bound")
        arguments[3] = hash_object(
            candidate.root,
            "commit",
            baseline + (b"x" * (minimum - len(baseline))),
        )
    elif name == "resource_tree_object_bytes":
        minimum = EXPECTED_RESOURCE_BOUNDS["git_objects"]["tree_per_object_bytes"] + 1
        hostile_tree = hash_object(
            candidate.root, "tree", b"x" * minimum, literally=True
        )
        arguments[1] = hostile_tree
        arguments[3] = create_commit(candidate.root, hostile_tree, (ANCHOR,))
    elif name == "resource_tree_aggregate_bytes":
        hostile_tree = resource_tree_aggregate_fixture(candidate.root)
        arguments[1] = hostile_tree
        arguments[3] = create_commit(candidate.root, hostile_tree, (ANCHOR,))
    elif name == "resource_blob_object_bytes":
        hostile_tree = resource_blob_tree(
            candidate.root,
            b"x"
            * (EXPECTED_RESOURCE_BOUNDS["git_objects"]["blob_per_object_bytes"] + 1),
            1,
        )
        arguments[1] = hostile_tree
        arguments[3] = create_commit(candidate.root, hostile_tree, (ANCHOR,))
    elif name == "resource_blob_aggregate_bytes":
        hostile_tree = resource_blob_tree(
            candidate.root,
            b"x"
            * (EXPECTED_RESOURCE_BOUNDS["git_objects"]["blob_per_object_bytes"] - 1),
            13,
        )
        arguments[1] = hostile_tree
        arguments[3] = create_commit(candidate.root, hostile_tree, (ANCHOR,))
    elif name == "resource_worktree_file_bytes":
        path = candidate.root / RECEIPT_RELATIVE
        write_regular(
            path,
            b"x"
            * (EXPECTED_RESOURCE_BOUNDS["filesystem"]["worktree_file_bytes"] + 1),
            stat.S_IMODE(path.lstat().st_mode),
        )
    elif name == "resource_worktree_aggregate_bytes":
        install_worktree_aggregate_fixture(candidate.root)
    elif name == "resource_worktree_nodes":
        install_worktree_node_fixture(candidate.root)
    elif name == "resource_git_config_stdout":
        install_large_local_config(candidate.root)
    else:
        raise SelfTestError(f"mutation implementation is absent: {name}")

    observation = invoke_checker(
        candidate,
        arguments,
        python_mode=python_mode,
        exact_runner=force_runner or (exact_runner and not force_direct),
    )
    if name == "object_recursive_tree_hash_corruption":
        require(
            observation.returncode != 0
            and b"Git tree object hash is inconsistent" in observation.stderr,
            "recursive corruption did not reach the checker's exact tree rehash",
        )
    return observation


def receipt_mutations(baseline: bytes, diagnostic: bytes) -> dict[str, bytes]:
    original = json.loads(baseline)
    diagnostic_original = json.loads(diagnostic)
    results: dict[str, bytes] = {}
    for name in (
        "receipt_schema",
        "receipt_non_implications",
        "receipt_path_count",
        "receipt_anchor_projection",
        "receipt_candidate_projection",
        "receipt_allowlist_projection",
        "receipt_full_candidate_projection",
        "receipt_pinned_changed_projection",
        "receipt_protected_projection",
        "receipt_custody",
        "receipt_validation_class",
        "receipt_repository_context",
        "receipt_repository_index_type",
        "receipt_repository_config_type",
        "receipt_runtime_boundaries",
        "receipt_git_tool_path",
        "receipt_git_tool_version",
        "receipt_python_tool_path",
        "receipt_python_tool_version",
        "receipt_external_status",
        "receipt_diagnostic_identity",
        "receipt_resource_bounds",
    ):
        source = (
            diagnostic_original if name == "receipt_diagnostic_identity" else original
        )
        mutated = json.loads(json.dumps(source))
        if name == "receipt_schema":
            mutated["schema"] = "pid-rs/c3-hosted-followup-custody/v0"
        elif name == "receipt_non_implications":
            mutated["non_implications"].pop()
        elif name == "receipt_path_count":
            mutated["path_custody"]["changed"] = 11
        elif name == "receipt_anchor_projection":
            mutated["anchor"]["projection_sha256"] = "1" * 64
        elif name == "receipt_candidate_projection":
            mutated["candidate"]["projection_sha256"] = "1" * 64
        elif name == "receipt_allowlist_projection":
            mutated["path_custody"]["allowlist_sha256"] = "1" * 64
        elif name == "receipt_full_candidate_projection":
            mutated["path_custody"]["full_candidate_projection_sha256"] = "1" * 64
        elif name == "receipt_pinned_changed_projection":
            mutated["path_custody"]["pinned_changed_projection_sha256"] = "1" * 64
        elif name == "receipt_protected_projection":
            mutated["path_custody"]["protected_projection_sha256"] = "1" * 64
        elif name == "receipt_custody":
            mutated["custody"] = "diagnostic-no-credit"
        elif name == "receipt_validation_class":
            mutated["validation_class"] = "diagnostic_only_without_external_custody"
        elif name == "receipt_repository_context":
            mutated["repository_context"]["git_command_timeout_seconds"] = 60.0
        elif name == "receipt_repository_index_type":
            mutated["repository_context"]["index"]["entry_count"] = float(
                mutated["repository_context"]["index"]["entry_count"]
            )
            mutated["repository_context"]["index"][
                "sha1_trailing_checksum_verified"
            ] = 1
        elif name == "receipt_repository_config_type":
            mutated["repository_context"]["local_config"]["record_count"] = float(
                mutated["repository_context"]["local_config"]["record_count"]
            )
            mutated["repository_context"]["local_config"]["size"] = float(
                mutated["repository_context"]["local_config"]["size"]
            )
        elif name == "receipt_runtime_boundaries":
            mutated["environmental_premises"]["runtime_boundaries"][
                "dynamic_loader_authenticated"
            ] = 0
        elif name == "receipt_git_tool_path":
            mutated["environmental_premises"]["git"]["path"] = source[
                "environmental_premises"
            ]["python"]["path"]
            mutated["environmental_premises"]["git"]["sha256"] = source[
                "environmental_premises"
            ]["python"]["sha256"]
        elif name == "receipt_git_tool_version":
            mutated["environmental_premises"]["git"]["version"] = "git version 0.0.0"
        elif name == "receipt_python_tool_path":
            mutated["environmental_premises"]["python"]["path"] = source[
                "environmental_premises"
            ]["git"]["path"]
            mutated["environmental_premises"]["python"]["sha256"] = source[
                "environmental_premises"
            ]["git"]["sha256"]
        elif name == "receipt_python_tool_version":
            mutated["environmental_premises"]["python"]["version"] = "Python 0.0.0"
        elif name == "receipt_external_status":
            mutated["status"] = "diagnostic_pass_no_credit"
        elif name == "receipt_diagnostic_identity":
            mutated["candidate"]["declared_identity_metadata"] = {
                "email": EXPECTED_EMAIL,
                "name": EXPECTED_NAME,
            }
        else:
            mutated["resource_bounds"]["filesystem"]["worktree_nodes"] = 4_096.0
        results[name] = (
            json.dumps(mutated, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    return results


def validate_frozen_inventory() -> None:
    require(
        len(MUTATION_CASES) == EXPECTED_MUTATION_COUNT, "frozen mutation count changed"
    )
    names = [case.name for case in MUTATION_CASES]
    require(len(names) == len(set(names)), "mutation names are not unique")
    actual = dict(
        sorted(Counter(case.mutation_target_family for case in MUTATION_CASES).items())
    )
    require(
        actual == EXPECTED_FAMILY_COUNTS,
        "frozen mutation-target-family counts changed",
    )
    require(
        sum(EXPECTED_FAMILY_COUNTS.values()) == EXPECTED_MUTATION_COUNT,
        "mutation-target-family sum changed",
    )
    boundary_counts = Counter(case.expected_boundary for case in MUTATION_CASES)
    require(
        boundary_counts == Counter(EXPECTED_BOUNDARY_COUNTS),
        "expected rejection-boundary counts changed",
    )
    checker_names = {
        case.name
        for case in MUTATION_CASES
        if case.expected_boundary is ExpectedBoundary.CHECKER
    }
    grouped_names = [
        name for _marker, case_names in CHECKER_MARKER_GROUPS for name in case_names
    ]
    require(
        len(grouped_names) == len(set(grouped_names))
        and set(grouped_names) == checker_names,
        "checker rejection-marker coverage changed",
    )
    receipt_names = {
        case.name
        for case in MUTATION_CASES
        if case.expected_boundary is ExpectedBoundary.RECEIPT_VALIDATOR
    }
    require(
        set(EXPECTED_RECEIPT_REJECTION_MESSAGES) == receipt_names
        and len(receipt_names) == EXPECTED_LOCAL_RECEIPT_CASES,
        "receipt rejection-message coverage changed",
    )
    equivalent_count = sum(
        case.expected_boundary is ExpectedBoundary.ISOLATED_EQUIVALENT
        for case in MUTATION_CASES
    )
    non_receipt_count = len(MUTATION_CASES) - len(receipt_names)
    self_test_target_count = sum(
        case.name in {"source_self_test_bytes", "source_runner_self_test_digest"}
        for case in MUTATION_CASES
    )
    require(
        non_receipt_count + equivalent_count
        == EXPECTED_MUTATION_VERIFIER_TARGET_LAUNCHES
        and self_test_target_count == EXPECTED_SELF_TEST_TARGET_LAUNCHES
        and non_receipt_count - self_test_target_count + equivalent_count
        == EXPECTED_CHECKER_TARGET_LAUNCHES,
        "mutation subprocess-attempt accounting changed",
    )
    validate_mode_comparison_classifier()


def require_typed_harness_failure(
    expected: type[HarnessProcessFailure],
    callback: Any,
    label: str,
) -> None:
    try:
        callback()
    except expected as error:
        require(
            not getattr(error, "__notes__", ()),
            f"{label}: expected failure retained cleanup diagnostics",
        )
        return
    except HarnessProcessFailure as error:
        raise SelfTestError(
            f"{label}: expected {expected.__name__}, got {type(error).__name__}: {error}"
        ) from error
    raise SelfTestError(f"{label}: expected {expected.__name__}, but the process returned")


def require_cleanup_failure_supersedes(callback: Any, label: str) -> None:
    global terminate_process_group
    original = terminate_process_group
    marker = "injected post-cleanup failure"

    def cleanup_then_fail(*args: Any, **kwargs: Any) -> None:
        original(*args, **kwargs)
        raise HarnessCleanupFailure(marker)

    terminate_process_group = cleanup_then_fail
    try:
        try:
            callback()
        except HarnessCleanupFailure as observed:
            require(str(observed) == marker, f"{label}: wrong cleanup failure")
        except HarnessProcessFailure as error:
            raise SelfTestError(
                f"{label}: cleanup masked by {type(error).__name__}"
            ) from error
        else:
            raise SelfTestError(f"{label}: injected cleanup failure returned")
    finally:
        terminate_process_group = original


def require_classifier_failure(
    observation: Observation,
    case: MutationCase,
    label: str,
) -> None:
    try:
        require_rejected(observation, case)
    except SelfTestError:
        return
    raise SelfTestError(f"{label}: hostile observation earned rejection credit")


def load_checker_process_group_helpers() -> dict[str, Any]:
    mode, body = stable_file(
        ROOT,
        CHECKER_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    require(mode == "100755", "checker control source is not executable")
    module_name = "_pid_rs_c3_checker_process_group_control"
    require(module_name not in sys.modules, "checker control module name is occupied")
    module = type(sys)(module_name)
    module.__file__ = str(ROOT / CHECKER_RELATIVE)
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    namespace = module.__dict__
    sys.modules[module_name] = module
    try:
        exec(compile(body, namespace["__file__"], "exec"), namespace)
    except BaseException as error:
        del sys.modules[module_name]
        raise SelfTestError(
            f"exact checker source could not load for process-group controls: {error}"
        ) from error
    required_names = {
        "OwnedChildSignalMask",
        "FollowupError",
        "GitCatFileSession",
        "restore_signal_mask_preserving_error",
        "verifier_signal_handler",
        "require_process_group_absent_after_reap",
        "terminate_owned_process_group",
    }
    require(
        required_names.issubset(namespace),
        "checker process-group control surface is incomplete",
    )
    return namespace


def run_sigchld_ownership_control(
    relative: str, python_mode: PythonMode
) -> str:
    mode, body = stable_file(
        ROOT,
        relative,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    require(mode == "100755", f"{relative}: SIGCHLD control source is not executable")
    expected_stdout = f"SIGCHLD_OWNERSHIP_OK:{relative}\n".encode("utf-8")
    observation = process(
        [
            PYTHON,
            "-I",
            "-S",
            *python_mode.interpreter_arguments,
            "-c",
            SIGCHLD_OWNERSHIP_BOOTSTRAP,
            str(ROOT),
            relative,
            str(len(body)),
            hashlib.sha256(body).hexdigest(),
        ],
        cwd=ROOT,
        input_bytes=body,
        timeout_seconds=15.0,
        maximum_output_bytes=4_096,
    )
    require(
        observation.returncode == 0
        and observation.stdout == expected_stdout
        and not observation.stderr,
        f"{relative}: inherited-SIGCHLD ownership control failed: "
        + observation.stderr.decode("utf-8", errors="replace"),
    )
    prefix = "selftest" if relative == SELF_TEST_RELATIVE else "checker"
    return f"{prefix}_inherited_sigchld_ignore_is_normalized_before_spawn"


def run_checker_signal_custody_control(
    control: str,
    expected_name: str,
    python_mode: PythonMode,
) -> str:
    mode, body = stable_file(
        ROOT,
        CHECKER_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    require(mode == "100755", "checker signal-custody source is not executable")
    expected_stdout = f"CHECKER_SIGNAL_CUSTODY_OK:{control}\n".encode("utf-8")
    observation = process(
        [
            PYTHON,
            "-I",
            "-S",
            *python_mode.interpreter_arguments,
            "-c",
            CHECKER_SIGNAL_CUSTODY_BOOTSTRAP,
            str(ROOT),
            CHECKER_RELATIVE,
            str(len(body)),
            hashlib.sha256(body).hexdigest(),
            control,
        ],
        cwd=ROOT,
        input_bytes=body,
        timeout_seconds=15.0,
        maximum_output_bytes=8_192,
    )
    require(
        observation.returncode == 0
        and observation.stdout == expected_stdout
        and not observation.stderr,
        f"checker {control} signal-custody control failed: "
        + observation.stderr.decode("utf-8", errors="replace"),
    )
    return expected_name


def run_selftest_signal_custody_control(python_mode: PythonMode) -> list[str]:
    mode, body = stable_file(
        ROOT,
        SELF_TEST_RELATIVE,
        maximum_bytes=MAX_EXACT_SOURCE_BYTES,
    )
    require(mode == "100755", "self-test signal-custody source is not executable")
    observation = process(
        [
            PYTHON,
            "-I",
            "-S",
            *python_mode.interpreter_arguments,
            "-c",
            SELFTEST_SIGNAL_CUSTODY_BOOTSTRAP,
            str(ROOT),
            SELF_TEST_RELATIVE,
            str(len(body)),
            hashlib.sha256(body).hexdigest(),
        ],
        cwd=ROOT,
        input_bytes=body,
        timeout_seconds=15.0,
        maximum_output_bytes=8_192,
    )
    require(
        observation.returncode == 0
        and observation.stdout == b"SELFTEST_SIGNAL_CUSTODY_OK\n"
        and not observation.stderr,
        "self-test signal-custody control failed: "
        + observation.stderr.decode("utf-8", errors="replace"),
    )
    return [
        "selftest_mask_capability_construction_failure_rolls_back",
        "selftest_mask_restore_failure_retains_live_capability",
        "selftest_input_fixture_allocation_failure_restores_mask",
        "selftest_post_popen_sigalrm_cleans_child_selector_input",
    ]


def run_process_group_state_machine_controls(
    *,
    prefix: str,
    failure_type: type[BaseException],
    terminate_before_reap: Any,
) -> list[str]:
    class ControlledProcess:
        def __init__(
            self,
            returncode: int | None,
            expected_before_wait: list[int | signal.Signals],
        ) -> None:
            self.pid = 424_242
            self.returncode = returncode
            self.wait_calls = 0
            self.expected_before_wait = expected_before_wait

        def wait(self, timeout: float) -> int:
            require(timeout > 0, f"{prefix}: cleanup wait was not bounded")
            require(
                signal_calls == self.expected_before_wait,
                f"{prefix}: signal/probe ordering before leader reap changed",
            )
            self.wait_calls += 1
            if self.returncode is None:
                self.returncode = -signal.SIGKILL
            return self.returncode

    original_killpg = os.killpg
    completed: list[str] = []
    signal_calls: list[int | signal.Signals] = []
    try:
        transient_events: list[BaseException] = [
            PermissionError("injected transient EPERM"),
            ProcessLookupError("injected ESRCH"),
        ]

        def transient_killpg(_group: int, selected_signal: int) -> None:
            signal_calls.append(selected_signal)
            require(
                selected_signal == 0,
                f"{prefix}: transient post-reap control attempted a signal",
            )
            raise transient_events.pop(0)

        os.killpg = transient_killpg
        transient_process = ControlledProcess(0, [])
        terminate_before_reap(transient_process, 0.25)
        require(
            signal_calls == [0, 0]
            and transient_process.wait_calls == 0
            and not transient_events,
            f"{prefix}: transient EPERM-to-ESRCH control did not retry exactly",
        )
        completed.append(f"{prefix}_transient_eperm_then_esrch_passes")

        signal_calls = []

        def present_killpg(_group: int, selected_signal: int) -> None:
            signal_calls.append(selected_signal)
            require(
                selected_signal == 0,
                f"{prefix}: persistent-present control attempted a signal",
            )

        os.killpg = present_killpg
        try:
            terminate_before_reap(ControlledProcess(0, []), 0.0)
        except failure_type:
            pass
        else:
            raise SelfTestError(
                f"{prefix}: persistent post-reap presence did not fail closed"
            )
        require(
            signal_calls == [0, 0],
            f"{prefix}: persistent post-reap presence was not observe-only",
        )
        completed.append(f"{prefix}_post_reap_present_fails_without_signal")

        signal_calls = []

        def indeterminate_killpg(_group: int, selected_signal: int) -> None:
            signal_calls.append(selected_signal)
            require(
                selected_signal == 0,
                f"{prefix}: persistent-indeterminate control attempted a signal",
            )
            raise PermissionError("injected persistent EPERM")

        os.killpg = indeterminate_killpg
        try:
            terminate_before_reap(ControlledProcess(0, []), 0.0)
        except failure_type:
            pass
        else:
            raise SelfTestError(
                f"{prefix}: persistent post-reap EPERM did not fail closed"
            )
        require(
            signal_calls == [0, 0],
            f"{prefix}: persistent post-reap EPERM was not observe-only",
        )
        completed.append(
            f"{prefix}_post_reap_indeterminate_fails_without_signal"
        )

        signal_calls = []
        probe_count = 0

        def cleanup_killpg(_group: int, selected_signal: int) -> None:
            nonlocal probe_count
            signal_calls.append(selected_signal)
            if selected_signal in {signal.SIGTERM, signal.SIGKILL}:
                return
            require(
                selected_signal == 0,
                f"{prefix}: cleanup control used an unexpected signal",
            )
            probe_count += 1
            if probe_count == 1:
                return
            if probe_count == 2:
                raise ProcessLookupError("injected post-reap ESRCH")
            raise SelfTestError(f"{prefix}: cleanup made an extra group probe")

        os.killpg = cleanup_killpg
        controlled = ControlledProcess(
            None,
            [signal.SIGTERM, 0, signal.SIGKILL],
        )
        terminate_before_reap(controlled, 0.0)
        require(
            signal_calls == [signal.SIGTERM, 0, signal.SIGKILL, 0]
            and controlled.wait_calls == 1
            and controlled.returncode == -signal.SIGKILL,
            f"{prefix}: pre-reap cleanup ordering changed",
        )
        completed.append(f"{prefix}_pre_reap_cleanup_signals_then_reaps")
    finally:
        os.killpg = original_killpg
    return completed


def run_checker_cat_file_abort_control(namespace: dict[str, Any]) -> str:
    class ControlledPipe:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class ControlledSelector:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class ReapedProcess:
        def __init__(self) -> None:
            self.pid = 424_243
            self.returncode = 0
            self.wait_calls = 0
            self.stdin = ControlledPipe()
            self.stdout = ControlledPipe()
            self.stderr = ControlledPipe()

        def wait(self, timeout: float) -> int:
            require(timeout > 0, "checker cat-file abort wait was not bounded")
            self.wait_calls += 1
            return self.returncode

    original_killpg = os.killpg
    killpg_calls: list[int] = []

    def observe_only_killpg(_group: int, selected_signal: int) -> None:
        killpg_calls.append(selected_signal)
        require(
            selected_signal == 0,
            "checker cat-file abort signaled after leader reap",
        )
        raise ProcessLookupError("injected cat-file abort ESRCH")

    os.killpg = observe_only_killpg
    try:
        session = namespace["GitCatFileSession"].__new__(
            namespace["GitCatFileSession"]
        )
        session.process = ReapedProcess()
        session.label = "checker cat-file abort deterministic control"
        session.finished = False
        session.selector = ControlledSelector()
        session.ownership = namespace["OwnedChildSignalMask"].acquire(
            label="checker cat-file abort deterministic control"
        )
        finish_error = namespace["FollowupError"](
            "injected cat-file finish failure after leader reap"
        )

        def fail_finish(_session: Any) -> None:
            raise finish_error

        session_type = namespace["GitCatFileSession"]
        original_finish = session_type.finish
        session_type.finish = fail_finish
        try:
            try:
                session.__exit__(None, None, None)
            except namespace["FollowupError"] as observed_error:
                require(
                    observed_error is finish_error,
                    "checker cat-file cleanup masked the initiating finish failure",
                )
            else:
                raise SelfTestError(
                    "checker cat-file finish control did not retain its failure"
                )
        finally:
            session_type.finish = original_finish
        require(
            session.finished
            and session.selector.closed
            and not session.ownership.held
            and session.process.wait_calls == 0
            and killpg_calls == [0]
            and all(
                pipe.closed
                for pipe in (
                    session.process.stdin,
                    session.process.stdout,
                    session.process.stderr,
                )
            ),
            "checker cat-file post-reap abort did not close its local resources",
        )
    finally:
        os.killpg = original_killpg
    return "checker_cat_file_abort_after_reap_is_signal_free"


def run_harness_controls(scratch: Path, python_mode: PythonMode) -> list[dict[str, str]]:
    absent = scratch / "absent-harness-control-executable"
    require(not absent.exists() and not absent.is_symlink(), "launch control exists")
    require_typed_harness_failure(
        HarnessLaunchFailure,
        lambda: process(
            [str(absent)],
            cwd=scratch,
            timeout_seconds=0.5,
            maximum_output_bytes=4_096,
        ),
        "launch harness control",
    )
    require_typed_harness_failure(
        HarnessSignalFailure,
        lambda: process(
            [
                PYTHON,
                "-I",
                "-S",
                *python_mode.interpreter_arguments,
                "-c",
                "import os, signal; os.kill(os.getpid(), signal.SIGTERM)",
            ],
            cwd=scratch,
            timeout_seconds=2.0,
            maximum_output_bytes=4_096,
        ),
        "signal harness control",
    )
    timeout_control = lambda: process(
        [
            PYTHON,
            "-I",
            "-S",
            *python_mode.interpreter_arguments,
            "-c",
            (
                "import os, signal, time\n"
                "child = -1\n"
                "def terminate(_signal, _frame):\n"
                "    os.waitpid(child, 0)\n"
                "    raise SystemExit(0)\n"
                "signal.signal(signal.SIGTERM, terminate)\n"
                "child = os.fork()\n"
                "if child == 0:\n"
                "    signal.signal(signal.SIGTERM, signal.SIG_DFL)\n"
                "    time.sleep(30)\n"
                "time.sleep(30)\n"
            ),
        ],
        cwd=scratch,
        timeout_seconds=0.25,
        maximum_output_bytes=4_096,
    )
    require_typed_harness_failure(
        HarnessTimeoutFailure,
        timeout_control,
        "timeout descendant harness control",
    )
    require_cleanup_failure_supersedes(
        timeout_control, "timeout descendant cleanup precedence control"
    )
    output_control = lambda: process(
        [
            PYTHON,
            "-I",
            "-S",
            *python_mode.interpreter_arguments,
            "-c",
            "import os, time; os.write(1, b'x' * 8192); time.sleep(30)",
        ],
        cwd=scratch,
        timeout_seconds=2.0,
        maximum_output_bytes=4_096,
    )
    require_typed_harness_failure(
        HarnessOutputLimitFailure,
        output_control,
        "output-overflow harness control",
    )
    require_cleanup_failure_supersedes(
        output_control, "output-overflow cleanup precedence control"
    )
    state_machine_controls = [
        run_sigchld_ownership_control(SELF_TEST_RELATIVE, python_mode),
        run_sigchld_ownership_control(CHECKER_RELATIVE, python_mode),
    ]

    def terminate_selftest_control(child: Any, grace: float) -> None:
        ownership = OwnedChildSignalMask.acquire(
            label="self-test deterministic process-group control"
        )
        primary: BaseException | None = None
        try:
            terminate_process_group(
                child,
                ownership=ownership,
                operation="self-test deterministic control",
                grace_seconds=grace,
            )
        except BaseException as error:
            primary = error
            raise
        finally:
            restore_signal_mask_preserving_error(
                ownership,
                primary,
                label="self-test deterministic control mask restoration failed",
            )

    state_machine_controls.extend(run_process_group_state_machine_controls(
        prefix="selftest",
        failure_type=HarnessCleanupFailure,
        terminate_before_reap=terminate_selftest_control,
    ))
    checker_namespace = load_checker_process_group_helpers()

    def terminate_checker_control(child: Any, grace: float) -> None:
        ownership = checker_namespace["OwnedChildSignalMask"].acquire(
            label="checker deterministic process-group control"
        )
        primary: BaseException | None = None
        try:
            checker_namespace["terminate_owned_process_group"](
                child,
                ownership=ownership,
                label="checker deterministic control",
                grace_seconds=grace,
            )
        except BaseException as error:
            primary = error
            raise
        finally:
            checker_namespace["restore_signal_mask_preserving_error"](
                ownership,
                primary,
                label="checker deterministic control mask restoration failed",
            )

    require(
        (signal.getsignal(signal.SIGALRM), signal.getsignal(signal.SIGINT))
        == (verifier_signal_handler, verifier_signal_handler),
        "self-test signal runtime changed before checker controls",
    )
    original_checker_handler = checker_namespace["verifier_signal_handler"]
    checker_namespace["DEFERRED_VERIFIER_SIGNAL_FLAGS"] = (
        DEFERRED_VERIFIER_SIGNAL_FLAGS
    )
    require(
        checker_namespace["DEFERRED_VERIFIER_SIGNAL_FLAGS"]
        is DEFERRED_VERIFIER_SIGNAL_FLAGS,
        "checker-control signal bridge is not identity-shared",
    )
    try:
        # Share the installed outer recorder; do not mutate OS dispositions.
        checker_namespace["verifier_signal_handler"] = verifier_signal_handler
        checker_namespace["VERIFIER_SIGNAL_RUNTIME_ACTIVE"] = True
        state_machine_controls.extend(
            run_process_group_state_machine_controls(
                prefix="checker",
                failure_type=checker_namespace["FollowupError"],
                terminate_before_reap=terminate_checker_control,
            )
        )
        state_machine_controls.append(
            run_checker_cat_file_abort_control(checker_namespace)
        )
    finally:
        checker_namespace["VERIFIER_SIGNAL_RUNTIME_ACTIVE"] = False
        checker_namespace["verifier_signal_handler"] = original_checker_handler
    state_machine_controls.extend(
        run_checker_signal_custody_control(control, name, python_mode)
        for control, name in (
            ("activation_partial_install", "checker_partial_signal_activation_restores_both_handlers"),
            ("deactivation_independent_restore", "checker_signal_deactivation_attempts_both_then_reinstalls_recorders"),
            ("mask_side_effect_raise", "checker_mask_side_effect_raise_rolls_back_kernel_mask"),
            ("nested_mask_lifo", "checker_nested_mask_out_of_order_rejected_then_lifo_restores"),
            ("timer_disarm_failure", "checker_timer_disarm_failure_retains_recorders"),
            ("cat_constructor_sigalrm", "checker_real_sigalrm_cat_constructor_deferred_until_cleanup"),
            ("git_process_sigint", "checker_real_sigint_git_process_launch_deferred_until_cleanup"),
            ("pending_timer_cleanup", "checker_real_timer_pending_until_cleanup"),
            ("pre_acquire_sigalrm", "checker_real_sigalrm_before_acquire_refuses_launch"),
        )
    )
    state_machine_controls.extend(run_selftest_signal_custody_control(python_mode))
    state_machine_controls.extend(
        run_checker_signal_custody_control(control, name, python_mode)
        for control, name in (
            ("multiple_signal_priority", "checker_repeated_mixed_signals_coalesce_with_sigint_priority"),
            ("selector_primary_sigalrm", "checker_primary_selector_error_retained_with_sigalrm_note"),
        )
    )
    require(
        state_machine_controls == list(HARNESS_CONTROL_NAMES[4:30]),
        "process-group state-machine controls differ from their frozen inventory",
    )
    classifier_case = next(
        case for case in MUTATION_CASES if case.name == "cli_no_external_custody"
    )
    correct_marker = checker_rejection_marker(classifier_case.name)
    require_classifier_failure(
        Observation(
            7,
            b"",
            CHECKER_ERROR_PREFIX + correct_marker + b"\n",
        ),
        classifier_case,
        "arbitrary nonzero classifier control",
    )
    require_classifier_failure(
        Observation(0, b"not-json\n", b""),
        classifier_case,
        "malformed zero classifier control",
    )
    valid_checker_error = CHECKER_ERROR_PREFIX + correct_marker + b"\n"
    require_classifier_failure(
        Observation(1, b"", valid_checker_error[:-1] + b" unrelated\n"),
        classifier_case,
        "same-line checker injection control",
    )
    require_classifier_failure(
        Observation(1, b"", valid_checker_error + b"unrelated traceback\n"),
        classifier_case,
        "multiline checker injection control",
    )
    argument_case = next(
        case for case in MUTATION_CASES if case.name == "cli_unknown_argument"
    )
    require_classifier_failure(
        Observation(
            2,
            b"",
            ARGUMENT_PARSER_ERROR.replace(
                b"check-c3-hosted-followup.py: error:",
                b"unrelated text\ncheck-c3-hosted-followup.py: error:",
                1,
            ),
        ),
        argument_case,
        "argument-parser injection control",
    )
    size_case = next(
        case for case in MUTATION_CASES if case.name == "source_checker_bytes"
    )
    require_classifier_failure(
        Observation(
            1,
            b"",
            b"unrelated traceback\n" + EXACT_SOURCE_SIZE_ERROR_SUFFIXES[0],
        ),
        size_case,
        "exact-source suffix-only control",
    )
    path_case = next(
        case for case in MUTATION_CASES if case.name == "topology_checker_symlink"
    )
    require_classifier_failure(
        Observation(
            1,
            b"",
            b"unrelated traceback\n"
            b"OSError: [Errno 1] hostile: 'check-c3-hosted-followup.py'\n",
        ),
        path_case,
        "exact-source path suffix-only control",
    )
    return [{"name": name, "status": "pass"} for name in HARNESS_CONTROL_NAMES]


SELF_TEST_RECEIPT_KEYS = {
    "anchor",
    "candidate",
    "counting_rule",
    "credit",
    "exact_source",
    "harness_bounds",
    "harness_controls",
    "limitations",
    "mutation_target_python_mode",
    "mutations",
    "positive_lifecycles",
    "schema",
    "status",
}


SELF_TEST_COUNTING_RULE = (
    "each deterministic hostile case has exactly one bookkeeping mutation-target "
    "family; families group what was mutated and do not denote distinct defenses, "
    "independent mechanisms, or statistically independent evidence; "
    "mutation_verifier_target_launches counts only checker or self-test verifier "
    "target launches attributable to mutation cases, including the second "
    "isolated-equivalence launch, and excludes Git fixture commands, positive "
    "lifecycle launches, harness controls, and local receipt validation"
)
SELF_TEST_LIMITATIONS = (
    "finite deterministic mutations do not prove the absence of unmodeled attacks",
    "this gate does not execute or adjudicate the separate immutable historical C3 hostile suite",
    "this gate does not imply arithmetic, estimator, PID, statistical, PDF-content, remote-authenticity, security-cleanliness, or cross-platform validity",
    "the diagnostic positive has null external tree/checkpoint and identity metadata and earns no custody credit",
    "raw forbidden-index-signature absence is one-sided and the SHA-1 trailer establishes internal consistency rather than authenticity",
    "tool-file hashes do not authenticate the Python standard library or extensions, dynamic loader, shell, PATH resolution, or concurrent repository state",
    "no mutation count is represented as a count of independent scientific replications",
    "exception-path cleanup signals only the owned original process group while its session leader remains unreaped; post-reap checks are observe-only and fail closed without reclamation; deliberate process-group or session escape is not contained",
    "the dedicated verifier resets SIGCHLD to SIG_DFL, requires the main and only enumerated Python thread, records SIGALRM/SIGINT without asynchronous exceptions, and masks them from before each Popen through reap, explicit ESRCH, and local-resource closure; it does not authenticate unenumerated native threads",
    "an external or native direct waitpid/wait actor can reap a leader while Popen.returncode remains None; excluding every such waiter is an explicit premise rather than an enforced property",
    "the fork child unblocks SIGALRM/SIGINT in preexec under the single-enumerated-thread premise; safety in the presence of unenumerated native threads is not established",
    "SIGTERM/SIGHUP inherited dispositions are unauthenticated and are not converted into cleanup exceptions; SIGKILL is uncatchable; hard asynchronous deadline preemption is not claimed while an owned child lifecycle is masked",
    "a same-user transient source swap, use, and restore during target execution can evade bracketing endpoint comparisons (ABA), because target code retains a live __file__ and repository path",
)


def typed_json_equal(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            typed_json_equal(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            typed_json_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def expected_harness_bounds_receipt() -> dict[str, Any]:
    return {
        "git_process_timeout_seconds": GIT_PROCESS_TIMEOUT_SECONDS,
        "maximum_combined_output_bytes": MAX_PROCESS_OUTPUT_BYTES,
        "child_preexec_unmasks_owned_signals": True,
        "external_waiter_premise": "no-external-or-native-direct-waiter",
        "owned_child_exception_signals": ["SIGALRM", "SIGINT"],
        "owned_child_signal_custody": (
            "nonraising-recorder-plus-pthread_sigmask-before-Popen-through-"
            "reap-ESRCH-local-close"
        ),
        "process_group_cleanup": (
            "pre-reap-owned-original-process-group-SIGTERM-then-SIGKILL;"
            "post-reap-observe-only-to-ESRCH"
        ),
        "post_reap_process_group_signaling": False,
        "process_group_probe_interval_seconds": (
            PROCESS_GROUP_PROBE_INTERVAL_SECONDS
        ),
        "python_thread_premise": "main-thread-and-one-enumerated-Python-thread",
        "sigchld_child_ownership": (
            "explicit-SIG_DFL-reset-before-first-Popen-and-"
            "verified-before-each-Popen;requires-no-external-or-native-waiter"
        ),
        "supervisor_self_test_timeout_seconds": SUPERVISOR_SELF_TEST_TIMEOUT_SECONDS,
        "target_process_timeout_seconds": TARGET_PROCESS_TIMEOUT_SECONDS,
        "termination_grace_seconds": PROCESS_TERMINATION_GRACE_SECONDS,
    }


def expected_harness_controls_receipt() -> dict[str, Any]:
    return {
        "cases": [
            {"name": name, "status": "pass"} for name in HARNESS_CONTROL_NAMES
        ],
        "count": len(HARNESS_CONTROL_NAMES),
        "counted_as_mutation_targets": False,
    }


def expected_mutation_cases_receipt() -> list[dict[str, str]]:
    return [
        {
            "name": case.name,
            "outcome": case.expected_boundary.value,
            "mutation_target_family": case.mutation_target_family,
        }
        for case in MUTATION_CASES
    ]


def expected_mutations_receipt() -> dict[str, Any]:
    return {
        "cases": expected_mutation_cases_receipt(),
        "count": EXPECTED_MUTATION_COUNT,
        "checker_target_launches": EXPECTED_CHECKER_TARGET_LAUNCHES,
        "local_receipt_cases": EXPECTED_LOCAL_RECEIPT_CASES,
        "mutation_verifier_target_launches": (
            EXPECTED_MUTATION_VERIFIER_TARGET_LAUNCHES
        ),
        "mutation_target_family_count": len(EXPECTED_FAMILY_COUNTS),
        "mutation_target_family_counts": dict(EXPECTED_FAMILY_COUNTS),
        "self_test_target_launches": EXPECTED_SELF_TEST_TARGET_LAUNCHES,
    }


def expected_positive_lifecycles_receipt() -> dict[str, list[str]]:
    return {
        "committed_direct_child": ["normal", "optimized", "byte_identical_receipt"],
        "diagnostic_no_credit": [
            "normal",
            "optimized",
            "byte_identical_receipt",
            "null_declared_identity",
        ],
        "precommit_worktree": ["normal", "optimized", "byte_identical_receipt"],
    }


def normalized_child_self_test_receipt(
    raw: bytes,
    expected_mode: PythonMode,
    expected_outer_candidate: Candidate,
    expected_runner_state: RunnerState,
) -> bytes:
    require(
        raw.endswith(b"\n") and raw.count(b"\n") == 1,
        f"{expected_mode.value} child self-test receipt is not one JSON line",
    )
    parsed = parse_json_document(raw)
    require(type(parsed) is dict, "child self-test receipt root is not an object")
    receipt: dict[str, Any] = parsed
    canonical = (
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    require(raw == canonical, "child self-test receipt is not canonical JSON")
    require_exact_keys(receipt, SELF_TEST_RECEIPT_KEYS, "child self-test receipt")
    child_candidate = receipt["candidate"]
    require(
        type(child_candidate) is dict,
        f"{expected_mode.value} child self-test candidate authority changed",
    )
    require_exact_keys(
        child_candidate,
        {"checkpoint_commit", "parent", "tree"},
        "child self-test candidate",
    )
    child_fixture_checkpoint = child_candidate["checkpoint_commit"]
    require(
        receipt["anchor"] == {"commit": ANCHOR, "tree": ANCHOR_TREE}
        and child_candidate["tree"] == expected_outer_candidate.tree
        and child_candidate["parent"] == ANCHOR
        and type(child_fixture_checkpoint) is str
        and HEX40.fullmatch(child_fixture_checkpoint) is not None,
        f"{expected_mode.value} child self-test candidate authority changed",
    )
    exact_source = receipt["exact_source"]
    expected_exact_source = {
        "checker_declared_sha256": expected_runner_state.checker_sha256,
        "checker_declared_size": expected_runner_state.checker_size,
        "maximum_source_size": MAX_EXACT_SOURCE_BYTES,
        "runner_frozen": True,
        "self_test_declared_sha256": expected_runner_state.self_test_sha256,
        "self_test_declared_size": expected_runner_state.self_test_size,
    }
    require(
        expected_runner_state.ready
        and expected_runner_state.maximum_source_size == MAX_EXACT_SOURCE_BYTES
        and type(exact_source) is dict
        and exact_source == expected_exact_source
        and exact_source.get("runner_frozen") is True
        and type(exact_source.get("checker_declared_size")) is int
        and type(exact_source.get("self_test_declared_size")) is int
        and type(exact_source.get("maximum_source_size")) is int,
        f"{expected_mode.value} child self-test exact-source authority changed",
    )
    require(
        receipt["schema"] == "pid-rs/c3-hosted-followup-self-test/v2"
        and receipt["status"] == "pass"
        and receipt["credit"] == "exact_source_runner"
        and receipt["mutation_target_python_mode"] == expected_mode.value,
        f"{expected_mode.value} child self-test authority fields changed",
    )
    require(
        receipt["counting_rule"] == SELF_TEST_COUNTING_RULE
        and typed_json_equal(
            receipt["harness_bounds"], expected_harness_bounds_receipt()
        )
        and typed_json_equal(
            receipt["harness_controls"], expected_harness_controls_receipt()
        )
        and typed_json_equal(receipt["limitations"], list(SELF_TEST_LIMITATIONS))
        and typed_json_equal(receipt["mutations"], expected_mutations_receipt())
        and typed_json_equal(
            receipt["positive_lifecycles"],
            expected_positive_lifecycles_receipt(),
        ),
        f"{expected_mode.value} child self-test nested evidence changed",
    )
    normalized = dict(receipt)
    del normalized["mutation_target_python_mode"]
    return (
        json.dumps(normalized, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def validate_mode_comparison_classifier() -> None:
    outer_candidate = Candidate(root=ROOT, tree="1" * 40, checkpoint="2" * 40)
    child_fixture_checkpoint = "8" * 40
    require(
        child_fixture_checkpoint != outer_candidate.checkpoint,
        "mode comparator control conflated outer and child checkpoints",
    )
    runner_state = RunnerState(
        ready=True,
        checker_sha256="3" * 64,
        checker_size=101,
        self_test_sha256="4" * 64,
        self_test_size=202,
        maximum_source_size=MAX_EXACT_SOURCE_BYTES,
    )
    sample: dict[str, Any] = {
        "anchor": {"commit": ANCHOR, "tree": ANCHOR_TREE},
        "candidate": {
            "checkpoint_commit": child_fixture_checkpoint,
            "parent": ANCHOR,
            "tree": outer_candidate.tree,
        },
        "counting_rule": SELF_TEST_COUNTING_RULE,
        "credit": "exact_source_runner",
        "exact_source": {
            "checker_declared_sha256": runner_state.checker_sha256,
            "checker_declared_size": runner_state.checker_size,
            "maximum_source_size": MAX_EXACT_SOURCE_BYTES,
            "runner_frozen": True,
            "self_test_declared_sha256": runner_state.self_test_sha256,
            "self_test_declared_size": runner_state.self_test_size,
        },
        "harness_bounds": expected_harness_bounds_receipt(),
        "harness_controls": expected_harness_controls_receipt(),
        "limitations": list(SELF_TEST_LIMITATIONS),
        "mutation_target_python_mode": PythonMode.NORMAL.value,
        "mutations": expected_mutations_receipt(),
        "positive_lifecycles": expected_positive_lifecycles_receipt(),
        "schema": "pid-rs/c3-hosted-followup-self-test/v2",
        "status": "pass",
    }

    def encode(value: dict[str, Any]) -> bytes:
        return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
            "utf-8"
        )

    normal = normalized_child_self_test_receipt(
        encode(sample), PythonMode.NORMAL, outer_candidate, runner_state
    )
    optimized_sample = json.loads(json.dumps(sample))
    optimized_sample["mutation_target_python_mode"] = PythonMode.OPTIMIZED.value
    optimized = normalized_child_self_test_receipt(
        encode(optimized_sample), PythonMode.OPTIMIZED, outer_candidate, runner_state
    )
    require(normal == optimized, "mode comparator positive control changed")

    def require_authority_rejection(
        hostile_sample: dict[str, Any], marker: str, label: str
    ) -> None:
        try:
            normalized_child_self_test_receipt(
                encode(hostile_sample),
                PythonMode.NORMAL,
                outer_candidate,
                runner_state,
            )
        except SelfTestError as error:
            require(
                str(error) == marker,
                f"{label} rejected at the wrong authority boundary: {error}",
            )
            return
        raise SelfTestError(f"{label} escaped child receipt authority validation")

    candidate_marker = "normal child self-test candidate authority changed"
    exact_source_marker = "normal child self-test exact-source authority changed"
    hostile_tree = json.loads(json.dumps(sample))
    hostile_tree["candidate"]["tree"] = "5" * 40
    require_authority_rejection(hostile_tree, candidate_marker, "wrong-tree control")
    hostile_parent = json.loads(json.dumps(sample))
    hostile_parent["candidate"]["parent"] = "6" * 40
    require_authority_rejection(
        hostile_parent, candidate_marker, "wrong-parent control"
    )
    malformed_checkpoint = json.loads(json.dumps(sample))
    malformed_checkpoint["candidate"]["checkpoint_commit"] = "not-a-checkpoint"
    require_authority_rejection(
        malformed_checkpoint, candidate_marker, "malformed-checkpoint control"
    )
    hostile_digest = json.loads(json.dumps(sample))
    hostile_digest["exact_source"]["checker_declared_sha256"] = "7" * 64
    require_authority_rejection(
        hostile_digest, exact_source_marker, "wrong-digest control"
    )
    hostile_size = json.loads(json.dumps(sample))
    hostile_size["exact_source"]["self_test_declared_size"] += 1
    require_authority_rejection(
        hostile_size, exact_source_marker, "wrong-size control"
    )
    nested_marker = "normal child self-test nested evidence changed"
    hostile_counting = json.loads(json.dumps(sample))
    hostile_counting["counting_rule"] += "; hostile"
    require_authority_rejection(
        hostile_counting, nested_marker, "counting-rule control"
    )
    hostile_bounds = json.loads(json.dumps(sample))
    hostile_bounds["harness_bounds"]["maximum_combined_output_bytes"] += 1
    require_authority_rejection(
        hostile_bounds, nested_marker, "harness-bounds control"
    )
    hostile_controls = json.loads(json.dumps(sample))
    hostile_controls["harness_controls"]["cases"].pop()
    require_authority_rejection(
        hostile_controls, nested_marker, "harness-controls control"
    )
    hostile_limitations = json.loads(json.dumps(sample))
    hostile_limitations["limitations"].pop()
    require_authority_rejection(
        hostile_limitations, nested_marker, "limitations control"
    )
    hostile_mutations = json.loads(json.dumps(sample))
    hostile_mutations["mutations"]["cases"][0]["outcome"] = "hostile"
    require_authority_rejection(
        hostile_mutations, nested_marker, "mutation-outcomes control"
    )
    hostile_lifecycles = json.loads(json.dumps(sample))
    hostile_lifecycles["positive_lifecycles"]["precommit_worktree"].pop()
    require_authority_rejection(
        hostile_lifecycles, nested_marker, "positive-lifecycles control"
    )


def supervisor_success(observation: Observation, label: str) -> bytes:
    require(
        observation.returncode == 0,
        f"{label} failed with {observation.returncode}: "
        + observation.stderr.decode("utf-8", errors="replace").strip(),
    )
    require(not observation.stderr, f"{label} emitted stderr")
    return observation.stdout


def run_mode_comparison_supervisor(
    tree: str, checkpoint: str, runner_state: RunnerState
) -> int:
    require(HEX40.fullmatch(tree) is not None, "supervisor candidate tree is malformed")
    require(
        HEX40.fullmatch(checkpoint) is not None,
        "supervisor checkpoint commit is malformed",
    )
    require(
        runner_state.ready
        and runner_state.maximum_source_size == MAX_EXACT_SOURCE_BYTES,
        "mode-comparison supervisor requires exact frozen runner state",
    )
    outer_candidate = Candidate(root=ROOT, tree=tree, checkpoint=checkpoint)
    checker_receipts: dict[PythonMode, bytes] = {}
    checker_evidence: dict[PythonMode, dict[str, Any]] = {}
    child_receipts: dict[PythonMode, bytes] = {}
    normalized_receipts: dict[PythonMode, bytes] = {}
    runner = str(ROOT / RUNNER_RELATIVE)
    for mode in (PythonMode.NORMAL, PythonMode.OPTIMIZED):
        checker_receipts[mode] = supervisor_success(
            process(
                [runner, mode.value, "checker", *external_arguments(outer_candidate)],
                cwd=ROOT,
                timeout_seconds=TARGET_PROCESS_TIMEOUT_SECONDS,
            ),
            f"{mode.value} supervisor checker",
        )
        checker_evidence[mode] = validate_receipt(
            checker_receipts[mode],
            tree=tree,
            checkpoint=checkpoint,
            lifecycle=None,
            repository_root=ROOT,
        )
    require(
        checker_receipts[PythonMode.NORMAL]
        == checker_receipts[PythonMode.OPTIMIZED],
        "supervisor checker receipts differ across Python modes",
    )

    for mode in (PythonMode.NORMAL, PythonMode.OPTIMIZED):
        child_receipts[mode] = supervisor_success(
            process(
                [runner, mode.value, "self-test"],
                cwd=ROOT,
                timeout_seconds=SUPERVISOR_SELF_TEST_TIMEOUT_SECONDS,
            ),
            f"{mode.value} supervisor child self-test",
        )
        normalized_receipts[mode] = normalized_child_self_test_receipt(
            child_receipts[mode], mode, outer_candidate, runner_state
        )
    require(
        normalized_receipts[PythonMode.NORMAL]
        == normalized_receipts[PythonMode.OPTIMIZED],
        "child self-test receipts differ after deleting only mutation_target_python_mode",
    )
    require(
        child_receipts[PythonMode.NORMAL] != child_receipts[PythonMode.OPTIMIZED],
        "child self-test receipts did not retain their distinct mode fields",
    )
    evidence = {
        "candidate": {"checkpoint_commit": checkpoint, "tree": tree},
        "checker": {
            "byte_identical_across_modes": True,
            "normal_receipt_sha256": hashlib.sha256(
                checker_receipts[PythonMode.NORMAL]
            ).hexdigest(),
            "optimized_receipt_sha256": hashlib.sha256(
                checker_receipts[PythonMode.OPTIMIZED]
            ).hexdigest(),
            "receipt": checker_evidence[PythonMode.NORMAL],
        },
        "output_bound": {"maximum_bytes": MAX_SUPERVISOR_RECEIPT_BYTES},
        "schema": "pid-rs/c3-hosted-followup-mode-comparison/v2",
        "self_test": {
            "byte_identical_after_deleting_only_mutation_target_python_mode": True,
            "child_arguments": [],
            "normal_receipt_sha256": hashlib.sha256(
                child_receipts[PythonMode.NORMAL]
            ).hexdigest(),
            "normalized_receipt_sha256": hashlib.sha256(
                normalized_receipts[PythonMode.NORMAL]
            ).hexdigest(),
            "optimized_receipt_sha256": hashlib.sha256(
                child_receipts[PythonMode.OPTIMIZED]
            ).hexdigest(),
            "receipt_without_mutation_target_python_mode": parse_json_document(
                normalized_receipts[PythonMode.NORMAL]
            ),
        },
        "status": "pass",
    }
    encoded = (
        json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    require(
        len(encoded) <= MAX_SUPERVISOR_RECEIPT_BYTES,
        "mode-comparison supervisor receipt exceeds its byte bound",
    )
    sys.stdout.buffer.write(encoded)
    return 0


def run_self_test() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bootstrap-direct",
        action="store_true",
        help="non-creditable development mode before exact-source runner hashes are frozen",
    )
    parser.add_argument(
        "--compare-runner-modes",
        action="store_true",
        help="exact-source supervisor for in-memory normal/optimized runner comparison",
    )
    parser.add_argument("--expected-candidate-tree")
    parser.add_argument("--checkpoint-commit")
    arguments = parser.parse_args()
    require(
        SCRIPT_PATH == ROOT / SELF_TEST_RELATIVE and not Path(__file__).is_symlink(),
        "self-test source is outside its canonical repository path",
    )
    mutation_target_python_mode = (
        PythonMode.NORMAL if sys.flags.optimize == 0 else PythonMode.OPTIMIZED
    )
    validate_frozen_inventory()
    runner_state = runner_hash_state(ROOT)
    require(
        (arguments.expected_candidate_tree is None)
        == (arguments.checkpoint_commit is None),
        "supervisor candidate tree and checkpoint must be paired",
    )
    require(
        arguments.compare_runner_modes
        == (arguments.expected_candidate_tree is not None),
        "supervisor custody arguments require --compare-runner-modes and vice versa",
    )
    if not runner_state.ready:
        require(
            arguments.bootstrap_direct and not arguments.compare_runner_modes,
            "exact-source runner hashes are not frozen; only --bootstrap-direct is available and it earns no credit",
        )
    else:
        require(
            not arguments.bootstrap_direct,
            "bootstrap-direct mode is forbidden after exact-source runner hashes settle",
        )
        validate_self_exact_source_entry(
            runner_state.self_test_sha256,
            runner_state.self_test_size,
        )
    if arguments.compare_runner_modes:
        require(
            not arguments.bootstrap_direct,
            "mode-comparison supervisor is forbidden in bootstrap-direct mode",
        )
        if arguments.expected_candidate_tree is None or arguments.checkpoint_commit is None:
            raise SelfTestError("mode-comparison supervisor custody pair is absent")
        return run_mode_comparison_supervisor(
            arguments.expected_candidate_tree,
            arguments.checkpoint_commit,
            runner_state,
        )

    outcomes: list[dict[str, str]] = []
    harness_controls: list[dict[str, str]] = []
    scratch_parent = os.environ.get("RUNNER_TEMP") or os.environ.get("TMPDIR")
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-c3-followup-selftest-",
        dir=scratch_parent,
    ) as scratch_raw:
        scratch = Path(scratch_raw).resolve(strict=True)
        harness_controls = run_harness_controls(
            scratch,
            mutation_target_python_mode,
        )
        template = build_template(scratch)

        precommit_normal = require_success(
            invoke_checker(
                template,
                external_arguments(template),
                python_mode=PythonMode.NORMAL,
                exact_runner=runner_state.ready,
            ),
            template,
            "precommit-worktree",
        )
        precommit_optimized = require_success(
            invoke_checker(
                template,
                external_arguments(template),
                python_mode=PythonMode.OPTIMIZED,
                exact_runner=runner_state.ready,
            ),
            template,
            "precommit-worktree",
        )
        require(
            precommit_normal == precommit_optimized,
            "normal and optimized precommit receipts differ",
        )

        diagnostic_arguments = ["--diagnostic-without-external-custody"]
        diagnostic_normal = require_diagnostic_success(
            invoke_checker(
                template,
                diagnostic_arguments,
                python_mode=PythonMode.NORMAL,
                exact_runner=runner_state.ready,
            ),
            template,
            "precommit-worktree",
        )
        diagnostic_optimized = require_diagnostic_success(
            invoke_checker(
                template,
                diagnostic_arguments,
                python_mode=PythonMode.OPTIMIZED,
                exact_runner=runner_state.ready,
            ),
            template,
            "precommit-worktree",
        )
        require(
            diagnostic_normal == diagnostic_optimized,
            "normal and optimized diagnostic receipts differ",
        )

        committed = clone_case(template, scratch, "positive-committed")
        try:
            set_committed(committed)
            committed_normal = require_success(
                invoke_checker(
                    committed,
                    external_arguments(committed),
                    python_mode=PythonMode.NORMAL,
                    exact_runner=runner_state.ready,
                ),
                committed,
                "committed-direct-child",
            )
            committed_optimized = require_success(
                invoke_checker(
                    committed,
                    external_arguments(committed),
                    python_mode=PythonMode.OPTIMIZED,
                    exact_runner=runner_state.ready,
                ),
                committed,
                "committed-direct-child",
            )
            require(
                committed_normal == committed_optimized,
                "normal and optimized committed receipts differ",
            )
        finally:
            remove_case(committed, scratch)

        synthetic_receipts = receipt_mutations(precommit_normal, diagnostic_normal)
        for case in MUTATION_CASES:
            if case.expected_boundary is ExpectedBoundary.RECEIPT_VALIDATOR:
                diagnostic_receipt = case.name == "receipt_diagnostic_identity"
                try:
                    validate_receipt(
                        synthetic_receipts[case.name],
                        tree=None if diagnostic_receipt else template.tree,
                        checkpoint=(
                            None if diagnostic_receipt else template.checkpoint
                        ),
                        lifecycle="precommit-worktree",
                        repository_root=template.root,
                    )
                except SelfTestError as error:
                    require(
                        str(error) == EXPECTED_RECEIPT_REJECTION_MESSAGES[case.name],
                        f"{case.name}: receipt rejected at the wrong boundary: {error}",
                    )
                    outcome = case.expected_boundary.value
                else:
                    raise SelfTestError(
                        f"hostile receipt mutation escaped: {case.name}"
                    )
            else:
                candidate = clone_case(template, scratch, case.name)
                try:
                    observation = mutate_case(
                        case,
                        candidate,
                        template=template,
                        exact_runner=runner_state.ready,
                        python_mode=mutation_target_python_mode,
                    )
                    if case.expected_boundary is ExpectedBoundary.ISOLATED_EQUIVALENT:
                        outcome = case.expected_boundary.value
                    else:
                        outcome = require_rejected(observation, case)
                finally:
                    remove_case(candidate, scratch)
            outcomes.append(
                {
                    "name": case.name,
                    "outcome": outcome,
                    "mutation_target_family": case.mutation_target_family,
                }
            )

    observed_counts = dict(
        sorted(Counter(item["mutation_target_family"] for item in outcomes).items())
    )
    require(
        observed_counts == EXPECTED_FAMILY_COUNTS,
        "executed mutation-target-family counts differ",
    )
    require(
        len(outcomes) == EXPECTED_MUTATION_COUNT, "not every frozen mutation executed"
    )
    require(
        typed_json_equal(outcomes, expected_mutation_cases_receipt()),
        "executed mutation outcomes differ from the frozen ordered inventory",
    )
    require(
        typed_json_equal(
            {
                "cases": harness_controls,
                "count": len(harness_controls),
                "counted_as_mutation_targets": False,
            },
            expected_harness_controls_receipt(),
        ),
        "executed harness controls differ from their explicit receipt inventory",
    )
    receipt = {
        "anchor": {"commit": ANCHOR, "tree": ANCHOR_TREE},
        "candidate": {
            "checkpoint_commit": template.checkpoint,
            "parent": ANCHOR,
            "tree": template.tree,
        },
        "counting_rule": SELF_TEST_COUNTING_RULE,
        "credit": (
            "exact_source_runner"
            if runner_state.ready
            else "none_bootstrap_direct"
        ),
        "exact_source": {
            "checker_declared_sha256": runner_state.checker_sha256,
            "checker_declared_size": runner_state.checker_size,
            "maximum_source_size": runner_state.maximum_source_size,
            "runner_frozen": runner_state.ready,
            "self_test_declared_sha256": runner_state.self_test_sha256,
            "self_test_declared_size": runner_state.self_test_size,
        },
        "harness_bounds": expected_harness_bounds_receipt(),
        "harness_controls": expected_harness_controls_receipt(),
        "limitations": list(SELF_TEST_LIMITATIONS),
        "mutation_target_python_mode": mutation_target_python_mode.value,
        "mutations": expected_mutations_receipt(),
        "positive_lifecycles": expected_positive_lifecycles_receipt(),
        "schema": "pid-rs/c3-hosted-followup-self-test/v2",
        "status": "pass",
    }
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


def main() -> int:
    previous_handlers: tuple[Any, Any] | None = None
    primary_error: BaseException | None = None
    primary_traceback: Any = None
    result: int | None = None
    try:
        previous_handlers = activate_verifier_signal_runtime()
        result = run_self_test()
    except BaseException as error:
        primary_error = error
        primary_traceback = error.__traceback__
    if previous_handlers is not None:
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
                    "self-test signal-runtime teardown also failed",
                    error,
                )
        else:
            if deferred_error is not None and primary_error is None:
                primary_error = deferred_error
                primary_traceback = deferred_error.__traceback__
    if primary_error is not None:
        raise primary_error.with_traceback(primary_traceback)
    require(result is not None, "self-test produced no result")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SelfTestError as error:
        print(f"ERROR: C3 hosted follow-up self-test: {error}", file=sys.stderr)
        raise SystemExit(1) from None
