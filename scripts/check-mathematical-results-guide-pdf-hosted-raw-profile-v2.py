#!/usr/bin/env python3
"""Check the v2 raw hosted profile for the 23-page mathematical-results guide PDF.

This comparator is deliberately source-specific.  It binds one retained
CI-matched Ubuntu/x86 candidate fixture by exact byte length and SHA-256.  The
fixture was produced in translated local container execution; it is not itself
a GitHub-hosted capture.  A distinct hosted candidate is admitted only
when it is byte-exact to that fixture or has the same length and differs solely
in the two duplicated 16-byte payloads of the final trailer ``/ID`` array.  The
exceptional relation is delegated to the separately digest-pinned strict
trailer-ID checker; no bytes are normalized, ignored, rewritten, or tolerated.

Both the fixture and candidate are then validated from the captured bytes by
the separately digest-pinned strict structure checker with both canonical
manifest digests enforced.  Their complete typed reports must be equal.  The
target and navigation reports must be fresh paths.  They are staged beside the
destinations and published with no-clobber hard links.  The stage descriptors
remain open and identity-checked through publication; a later pair failure
rolls back an earlier published member before the checker returns failure.

The strict checkers use pypdf.  This program binds the imported package's exact
version, canonical external initializer bytes, and stable path for the duration
of the comparison.  The complete installed pypdf distribution remains an
explicit outer-runner trust boundary: hosted CI installs its hash-pinned wheel
from ``audit/formal/requirements-pdf.txt`` before invoking this checker.

The result is a bounded raw-profile comparison.  A hosted pass is the separate
evidence that the retained candidate replays on that hosted producer.  This is
not general PDF equivalence, raw-byte reproducibility across arbitrary
producers, authenticity, or permission to weaken the repository's exact-mode
comparison.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import secrets
import stat
import sys
import types
from dataclasses import dataclass
from typing import Any, NoReturn


CHECK_NAME = "Mathematical results guide hosted raw-profile v2 check"
CHECKER_SOURCE = pathlib.Path(__file__).resolve(strict=True)
ROOT = CHECKER_SOURCE.parent.parent
STRUCTURE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-structure-v2.py"
ID_VARIANCE_CHECK = ROOT / "scripts/check-mathematical-results-guide-pdf-id-variance.py"

# This is one frozen 23-page producer observation, not a generic toolchain family.
EXPECTED_HOSTED_FIXTURE_BYTES = 744_745
EXPECTED_HOSTED_FIXTURE_SHA256 = (
    "b879555d87f696be870483326e2e3158c1f95330d51291d80017c016830907b6"
)
EXPECTED_STRUCTURE_CHECK_SHA256 = (
    "a70d3c78da7040774c5976f2316480501713eed1e9c865822e3024724a0ccf8d"
)
EXPECTED_ID_VARIANCE_CHECK_SHA256 = (
    "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7"
)
EXPECTED_PYPDF_VERSION = "6.15.0"

MAX_PDF_BYTES = 16 * 1024 * 1024
MAX_DEPENDENCY_BYTES = 2 * 1024 * 1024
MAX_REPORT_BYTES = 4 * 1024 * 1024
STABLE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)
PARENT_IDENTITY_FIELDS = ("st_dev", "st_ino", "st_mode")
STAGE_IDENTITY_FIELDS = ("st_dev", "st_ino", "st_mode", "st_size")


class HostedRawProfileError(Exception):
    """A deterministic failure of the closed hosted raw-profile relation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class InputSnapshot:
    """One stable, no-follow input descriptor and the exact captured bytes."""

    label: str
    path: pathlib.Path
    descriptor: int
    before: os.stat_result
    data: bytes


@dataclass(frozen=True)
class DependencySnapshot:
    """Exact source bytes and identity for one executable checker dependency."""

    label: str
    path: pathlib.Path
    before: os.stat_result
    data: bytes
    sha256: str


@dataclass
class OutputPlan:
    """Descriptor-pinned parent and preflight state for one report output."""

    label: str
    path: pathlib.Path
    parent: pathlib.Path
    basename: str
    parent_descriptor: int
    parent_before: os.stat_result
    destination_before: os.stat_result | None


@dataclass
class StagedOutput:
    """One descriptor-held report staged beside its fresh destination."""

    plan: OutputPlan
    temporary_basename: str
    descriptor: int
    before: os.stat_result
    payload: bytes
    published: bool = False
    published_before: os.stat_result | None = None


def fail(code: str, message: str) -> NoReturn:
    raise HostedRawProfileError(code, message)


def same_stat(
    first: os.stat_result,
    second: os.stat_result,
    fields: tuple[str, ...] = STABLE_FIELDS,
) -> bool:
    return all(getattr(first, field) == getattr(second, field) for field in fields)


def regular_read_flags(label: str) -> int:
    """Return fail-closed flags that cannot block on a raced FIFO endpoint."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        fail(
            "platform",
            f"this platform cannot open {label} with no-follow, nonblocking custody",
        )
    return os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)


def contains_terminal_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def capture_dependency(path: pathlib.Path, label: str) -> DependencySnapshot:
    """Read one canonical single-link dependency through a no-follow descriptor."""

    try:
        path_before = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        fail("dependency", f"cannot inspect {label}: {error}")
    if (
        resolved != path
        or stat.S_ISLNK(path_before.st_mode)
        or not stat.S_ISREG(path_before.st_mode)
        or path_before.st_nlink != 1
    ):
        fail(
            "dependency",
            f"{label} is noncanonical, non-regular, symbolic, or multiply linked",
        )
    if path_before.st_size <= 0 or path_before.st_size > MAX_DEPENDENCY_BYTES:
        fail(
            "dependency",
            f"{label} size is outside 1..{MAX_DEPENDENCY_BYTES} bytes",
        )
    flags = regular_read_flags("dependencies")
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail("dependency", f"cannot open {label} without following links: {error}")
    try:
        opened = os.fstat(descriptor)
        data = os.pread(descriptor, MAX_DEPENDENCY_BYTES + 1, 0)
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        fail("dependency", f"cannot read {label}: {error}")
    finally:
        os.close(descriptor)
    if (
        not stat.S_ISREG(opened.st_mode)
        or opened.st_nlink != 1
        or (path_before.st_dev, path_before.st_ino) != (opened.st_dev, opened.st_ino)
        or not same_stat(opened, descriptor_after)
        or not same_stat(opened, path_after)
        or len(data) != opened.st_size
    ):
        fail("dependency", f"{label} changed while it was read")
    return DependencySnapshot(
        label=label,
        path=path,
        before=opened,
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def load_pinned_dependency(
    path: pathlib.Path, expected_sha256: str, module_name: str, label: str
) -> tuple[Any, DependencySnapshot]:
    """Execute only captured dependency bytes with the reviewed exact digest."""

    snapshot = capture_dependency(path, label)
    if snapshot.sha256 != expected_sha256:
        fail(
            "dependency",
            f"{label} digest changed: observed={snapshot.sha256} "
            f"expected={expected_sha256}",
        )
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        code = compile(snapshot.data, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except BaseException as error:
        sys.modules.pop(module_name, None)
        fail(
            "dependency",
            f"cannot load {label}: {type(error).__name__}: {error}",
        )
    return module, snapshot


def recheck_dependency(snapshot: DependencySnapshot) -> None:
    observed = capture_dependency(snapshot.path, snapshot.label)
    if (
        not same_stat(snapshot.before, observed.before)
        or snapshot.data != observed.data
        or snapshot.sha256 != observed.sha256
    ):
        fail("dependency", f"{snapshot.label} changed during the comparison")


def capture_pypdf_runtime() -> tuple[Any, DependencySnapshot]:
    """Bind the admitted pypdf initializer while declaring the outer trust edge."""

    module = sys.modules.get("pypdf")
    if module is None:
        fail("dependency", "strict checker dependencies did not import pypdf")
    observed_version = getattr(module, "__version__", None)
    if observed_version != EXPECTED_PYPDF_VERSION:
        fail(
            "dependency",
            f"pypdf version changed: observed={observed_version!r} "
            f"expected={EXPECTED_PYPDF_VERSION!r}",
        )
    raw_path = getattr(module, "__file__", None)
    if not isinstance(raw_path, str) or not raw_path:
        fail("dependency", "pypdf does not expose one package initializer path")
    path = pathlib.Path(raw_path)
    if not path.is_absolute():
        fail("dependency", "pypdf package initializer path is not absolute")
    snapshot = capture_dependency(path, "pypdf package initializer")
    if snapshot.path == ROOT or ROOT in snapshot.path.parents:
        fail("dependency", "pypdf must not resolve from inside the repository")
    return module, snapshot


def recheck_pypdf_runtime(module: Any, snapshot: DependencySnapshot) -> None:
    if (
        sys.modules.get("pypdf") is not module
        or getattr(module, "__version__", None) != EXPECTED_PYPDF_VERSION
        or getattr(module, "__file__", None) != str(snapshot.path)
    ):
        fail("dependency", "pypdf runtime identity changed during the comparison")
    recheck_dependency(snapshot)


try:
    SELF_SOURCE_DEPENDENCY = capture_dependency(
        CHECKER_SOURCE, "hosted raw-profile checker source"
    )
    STRUCTURE, STRUCTURE_DEPENDENCY = load_pinned_dependency(
        STRUCTURE_CHECK,
        EXPECTED_STRUCTURE_CHECK_SHA256,
        "mathematical_results_guide_pdf_structure_for_hosted_raw_profile",
        "strict structure checker",
    )
    ID_VARIANCE, ID_VARIANCE_DEPENDENCY = load_pinned_dependency(
        ID_VARIANCE_CHECK,
        EXPECTED_ID_VARIANCE_CHECK_SHA256,
        "mathematical_results_guide_pdf_id_variance_for_hosted_raw_profile",
        "strict trailer-ID variance checker",
    )
    PYPDF_MODULE, PYPDF_DEPENDENCY = capture_pypdf_runtime()
except HostedRawProfileError as error:
    if __name__ == "__main__":
        print(f"{CHECK_NAME} failed [{error.code}]: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    raise

PROTECTED_DEPENDENCIES = (
    SELF_SOURCE_DEPENDENCY,
    STRUCTURE_DEPENDENCY,
    ID_VARIANCE_DEPENDENCY,
    PYPDF_DEPENDENCY,
)


def open_input(raw: str, label: str) -> InputSnapshot:
    """Capture one canonical regular single-link input with a stable identity."""

    if not raw or contains_terminal_control(raw):
        fail("input", f"{label} input path is empty or contains a control character")
    path = pathlib.Path(raw)
    if not path.is_absolute():
        fail("input", f"{label} input must be a canonical absolute path")
    try:
        path_before = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        fail("input", f"cannot inspect {label} input: {error}")
    if (
        resolved != path
        or stat.S_ISLNK(path_before.st_mode)
        or not stat.S_ISREG(path_before.st_mode)
    ):
        fail(
            "input",
            f"{label} input is noncanonical, non-regular, or symbolic: {path}",
        )
    flags = regular_read_flags("inputs")
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
    except OSError as error:
        if descriptor is not None:
            os.close(descriptor)
        fail("input", f"cannot open {label} input without following links: {error}")
    if not stat.S_ISREG(opened.st_mode) or (path_before.st_dev, path_before.st_ino) != (
        opened.st_dev,
        opened.st_ino,
    ):
        os.close(descriptor)
        fail("input", f"{label} input identity or regular-file type changed")
    if opened.st_nlink != 1:
        os.close(descriptor)
        fail("input", f"{label} input is not singly linked")
    if opened.st_size <= 0 or opened.st_size > MAX_PDF_BYTES:
        os.close(descriptor)
        fail("input", f"{label} input size is outside 1..{MAX_PDF_BYTES} bytes")
    try:
        data = os.pread(descriptor, MAX_PDF_BYTES + 1, 0)
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        os.close(descriptor)
        fail("input", f"cannot read {label} input: {error}")
    if (
        not same_stat(opened, descriptor_after)
        or not same_stat(opened, path_after)
        or len(data) != opened.st_size
    ):
        os.close(descriptor)
        fail("input", f"{label} input changed while it was read")
    return InputSnapshot(label, path, descriptor, opened, data)


def recheck_input(snapshot: InputSnapshot) -> None:
    try:
        descriptor_after = os.fstat(snapshot.descriptor)
        path_after = snapshot.path.lstat()
    except OSError as error:
        fail("input", f"cannot recheck {snapshot.label} input: {error}")
    if not same_stat(snapshot.before, descriptor_after) or not same_stat(
        snapshot.before, path_after
    ):
        fail("input", f"{snapshot.label} input changed during the comparison")


def validate_input_identities(inputs: tuple[InputSnapshot, ...]) -> None:
    identities: dict[tuple[int, int], str] = {}
    for snapshot in inputs:
        identity = (snapshot.before.st_dev, snapshot.before.st_ino)
        previous = identities.setdefault(identity, snapshot.label)
        if previous != snapshot.label:
            fail("input", f"{previous} and {snapshot.label} inputs alias one file")


def require_exact_hosted_fixture(snapshot: InputSnapshot) -> None:
    observed_sha256 = hashlib.sha256(snapshot.data).hexdigest()
    if (
        len(snapshot.data) != EXPECTED_HOSTED_FIXTURE_BYTES
        or observed_sha256 != EXPECTED_HOSTED_FIXTURE_SHA256
    ):
        fail(
            "hosted_raw_fixture",
            f"{snapshot.label} raw bytes changed: "
            f"observed_bytes={len(snapshot.data)} observed_sha256={observed_sha256}; "
            f"expected_bytes={EXPECTED_HOSTED_FIXTURE_BYTES} "
            f"expected_sha256={EXPECTED_HOSTED_FIXTURE_SHA256}",
        )


def compare_candidate_to_fixture_raw(
    fixture: InputSnapshot, candidate: InputSnapshot
) -> tuple[str, str]:
    """Admit exact bytes or only the strict duplicated final-trailer-ID delta."""

    if candidate.data == fixture.data:
        return "byte-exact hosted fixture", "exact"
    if len(candidate.data) != len(fixture.data):
        fail(
            "hosted_raw_relation",
            f"fixture/candidate byte lengths differ: "
            f"{len(fixture.data)} != {len(candidate.data)}",
        )
    try:
        fixture_projected, fixture_id_text, fixture_id = ID_VARIANCE.erase_strict_id(
            fixture.data, "hosted fixture"
        )
        candidate_projected, candidate_id_text, candidate_id = (
            ID_VARIANCE.erase_strict_id(candidate.data, "candidate")
        )
    except SystemExit as error:
        fail("hosted_raw_relation", f"strict trailer-ID relation failed: {error}")
    except BaseException as error:
        fail(
            "hosted_raw_relation",
            f"strict trailer-ID relation raised {type(error).__name__}: {error}",
        )
    if fixture_id == candidate_id:
        fail("hosted_raw_relation", "decoded trailer /ID values are equal")
    if fixture_projected != candidate_projected:
        fail(
            "hosted_raw_relation",
            "fixture and candidate differ outside the strict duplicated final-trailer "
            "/ID payloads",
        )
    diagnostic = (
        f"bytes={len(fixture.data)}; "
        f"fixture_sha256={hashlib.sha256(fixture.data).hexdigest()}; "
        f"candidate_sha256={hashlib.sha256(candidate.data).hexdigest()}; "
        f"fixture_id={fixture_id_text}; candidate_id={candidate_id_text}"
    )
    return "strict hosted-fixture trailer-ID projection", diagnostic


def output_lstat(plan: OutputPlan) -> os.stat_result | None:
    try:
        return os.stat(
            plan.basename,
            dir_fd=plan.parent_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return None
    except OSError as error:
        fail("output", f"cannot inspect {plan.label} output: {error}")


def prepare_output(
    path: pathlib.Path,
    label: str,
    inputs: tuple[InputSnapshot, ...],
    dependencies: tuple[DependencySnapshot, ...],
) -> OutputPlan:
    if not path.is_absolute() or contains_terminal_control(str(path)):
        fail("output", f"{label} output must be a canonical absolute path")
    parent = path.parent
    if parent == pathlib.Path("/") or path.name in ("", ".", ".."):
        fail("output", f"{label} output has a forbidden root or empty parent")
    try:
        parent_before = parent.lstat()
        parent_resolved = parent.resolve(strict=True)
        path_resolved = path.resolve(strict=False)
    except OSError as error:
        fail("output", f"cannot inspect {label} output path: {error}")
    if (
        parent_resolved != parent
        or path_resolved != path
        or stat.S_ISLNK(parent_before.st_mode)
        or not stat.S_ISDIR(parent_before.st_mode)
    ):
        fail("output", f"{label} output path is symbolic or noncanonical")
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if directory_flag is None or nofollow is None:
        fail("output", "this platform lacks no-follow directory output custody")
    flags = os.O_RDONLY | directory_flag | nofollow | getattr(os, "O_CLOEXEC", 0)
    parent_descriptor: int | None = None
    try:
        parent_descriptor = os.open(parent, flags)
        opened_parent = os.fstat(parent_descriptor)
    except OSError as error:
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        fail("output", f"cannot open {label} output parent safely: {error}")
    if not stat.S_ISDIR(opened_parent.st_mode) or (
        parent_before.st_dev,
        parent_before.st_ino,
    ) != (opened_parent.st_dev, opened_parent.st_ino):
        os.close(parent_descriptor)
        fail("output", f"{label} output parent identity changed")
    plan = OutputPlan(
        label=label,
        path=path,
        parent=parent,
        basename=path.name,
        parent_descriptor=parent_descriptor,
        parent_before=opened_parent,
        destination_before=None,
    )
    destination = output_lstat(plan)
    for snapshot in inputs:
        if path == snapshot.path:
            os.close(parent_descriptor)
            fail("output", f"{label} output aliases {snapshot.label} input")
        if destination is not None and (
            destination.st_dev,
            destination.st_ino,
        ) == (snapshot.before.st_dev, snapshot.before.st_ino):
            os.close(parent_descriptor)
            fail("output", f"{label} output hard-links {snapshot.label} input")
    for snapshot in dependencies:
        if path == snapshot.path:
            os.close(parent_descriptor)
            fail("output", f"{label} output aliases {snapshot.label}")
        if destination is not None and (
            destination.st_dev,
            destination.st_ino,
        ) == (snapshot.before.st_dev, snapshot.before.st_ino):
            os.close(parent_descriptor)
            fail("output", f"{label} output hard-links {snapshot.label}")
    if destination is not None:
        os.close(parent_descriptor)
        fail("output", f"existing {label} output is forbidden; output must be fresh")
    plan.destination_before = None
    return plan


def recheck_output_parent(plan: OutputPlan) -> None:
    """Bind the held output directory to its still-canonical pathname."""

    try:
        parent_after = os.fstat(plan.parent_descriptor)
        parent_path_after = plan.parent.lstat()
    except OSError as error:
        fail("output", f"cannot recheck {plan.label} output parent: {error}")
    if not same_stat(
        plan.parent_before, parent_after, PARENT_IDENTITY_FIELDS
    ) or not same_stat(plan.parent_before, parent_path_after, PARENT_IDENTITY_FIELDS):
        fail("output", f"{plan.label} output parent identity changed")


def recheck_output_plan(plan: OutputPlan) -> None:
    """Recheck parent custody and require the fresh destination to remain absent."""

    recheck_output_parent(plan)
    observed = output_lstat(plan)
    if observed is not None:
        fail("output", f"{plan.label} output destination changed before publication")


def validate_output_pair(plans: tuple[OutputPlan, OutputPlan]) -> None:
    first, second = plans
    if first.path == second.path:
        fail("output", "target and navigation outputs must be distinct")
    if (first.parent_before.st_dev, first.parent_before.st_ino) == (
        second.parent_before.st_dev,
        second.parent_before.st_ino,
    ) and first.basename == second.basename:
        fail("output", "target and navigation outputs alias one directory entry")


def report_payload(lines: tuple[str, ...], label: str) -> bytes:
    if not isinstance(lines, tuple) or any(not isinstance(line, str) for line in lines):
        fail("report", f"{label} report is not a tuple of text records")
    if any("\n" in line or "\r" in line for line in lines):
        fail("report", f"{label} report contains an embedded line break")
    try:
        payload = "".join(f"{line}\n" for line in lines).encode("utf-8")
    except UnicodeError as error:
        fail("report", f"cannot encode {label} report: {error}")
    if not payload or len(payload) > MAX_REPORT_BYTES:
        fail("report", f"{label} report size is outside 1..{MAX_REPORT_BYTES} bytes")
    return payload


def stage_output(plan: OutputPlan, payload: bytes) -> StagedOutput:
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor: int | None = None
    temporary_basename = ""
    for _ in range(64):
        temporary_basename = f".{plan.basename}.hosted-profile.{secrets.token_hex(16)}"
        try:
            descriptor = os.open(
                temporary_basename,
                flags,
                0o600,
                dir_fd=plan.parent_descriptor,
            )
            break
        except FileExistsError:
            continue
        except OSError as error:
            fail("output", f"cannot stage {plan.label} output: {error}")
    if descriptor is None:
        fail("output", f"cannot allocate a private {plan.label} output stage")
    retained = False
    try:
        view = memoryview(payload)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            if count <= 0:
                fail("output", f"short write while staging {plan.label} output")
            written += count
        os.fsync(descriptor)
        staged = os.fstat(descriptor)
        captured = os.pread(descriptor, len(payload) + 1, 0)
        staged_path = os.stat(
            temporary_basename,
            dir_fd=plan.parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(staged.st_mode)
            or staged.st_nlink != 1
            or staged.st_size != len(payload)
            or captured != payload
            or not same_stat(staged, staged_path)
        ):
            fail("output", f"{plan.label} staged output identity or size changed")
        retained = True
        return StagedOutput(plan, temporary_basename, descriptor, staged, payload)
    finally:
        if not retained:
            os.close(descriptor)
            try:
                os.unlink(temporary_basename, dir_fd=plan.parent_descriptor)
            except FileNotFoundError:
                pass


def recheck_stage(staged: StagedOutput) -> None:
    """Bind the still-named stage to its held descriptor and complete payload."""

    if not staged.temporary_basename:
        fail("output", f"{staged.plan.label} stage lost its private name")
    try:
        opened = os.fstat(staged.descriptor)
        data = os.pread(staged.descriptor, len(staged.payload) + 1, 0)
        path_after = os.stat(
            staged.temporary_basename,
            dir_fd=staged.plan.parent_descriptor,
            follow_symlinks=False,
        )
    except OSError as error:
        fail("output", f"cannot recheck {staged.plan.label} stage: {error}")
    if (
        not stat.S_ISREG(opened.st_mode)
        or opened.st_nlink != 1
        or data != staged.payload
        or not same_stat(staged.before, opened)
        or not same_stat(opened, path_after)
    ):
        fail("output", f"{staged.plan.label} stage changed before publication")


def cleanup_stage(staged: StagedOutput) -> tuple[str, ...]:
    """Remove only the descriptor-owned temporary name and close the descriptor."""

    errors: list[str] = []
    if staged.temporary_basename:
        try:
            opened = os.fstat(staged.descriptor)
            observed = os.stat(
                staged.temporary_basename,
                dir_fd=staged.plan.parent_descriptor,
                follow_symlinks=False,
            )
            if (opened.st_dev, opened.st_ino) != (observed.st_dev, observed.st_ino):
                errors.append(
                    f"{staged.plan.label} stage name no longer owns the held inode"
                )
            else:
                os.unlink(
                    staged.temporary_basename,
                    dir_fd=staged.plan.parent_descriptor,
                )
                staged.temporary_basename = ""
        except FileNotFoundError:
            staged.temporary_basename = ""
        except OSError as error:
            errors.append(f"cannot remove {staged.plan.label} stage: {error}")
    try:
        os.close(staged.descriptor)
    except OSError as error:
        errors.append(f"cannot close {staged.plan.label} stage: {error}")
    return tuple(errors)


def verify_published_output(staged: StagedOutput) -> None:
    plan = staged.plan
    flags = regular_read_flags("published outputs")
    descriptor: int | None = None
    try:
        held = os.fstat(staged.descriptor)
        held_data = os.pread(staged.descriptor, len(staged.payload) + 1, 0)
        descriptor = os.open(plan.basename, flags, dir_fd=plan.parent_descriptor)
        opened = os.fstat(descriptor)
        data = os.pread(descriptor, len(staged.payload) + 1, 0)
        descriptor_after = os.fstat(descriptor)
        path_after = os.stat(
            plan.basename,
            dir_fd=plan.parent_descriptor,
            follow_symlinks=False,
        )
    except OSError as error:
        fail("output", f"cannot verify published {plan.label} output: {error}")
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
    if (
        not stat.S_ISREG(opened.st_mode)
        or opened.st_nlink != 1
        or not stat.S_ISREG(held.st_mode)
        or held.st_nlink != 1
        or held_data != staged.payload
        or data != staged.payload
        or (held.st_dev, held.st_ino) != (opened.st_dev, opened.st_ino)
        or not same_stat(opened, descriptor_after)
        or not same_stat(opened, path_after)
    ):
        fail("output", f"published {plan.label} output changed or is incomplete")


def publish_stage(staged: StagedOutput) -> None:
    """Create one fresh destination without replacing any existing entry."""

    recheck_stage(staged)
    recheck_output_plan(staged.plan)
    try:
        os.link(
            staged.temporary_basename,
            staged.plan.basename,
            src_dir_fd=staged.plan.parent_descriptor,
            dst_dir_fd=staged.plan.parent_descriptor,
            follow_symlinks=False,
        )
        staged.published = True
        staged.published_before = os.stat(
            staged.plan.basename,
            dir_fd=staged.plan.parent_descriptor,
            follow_symlinks=False,
        )
        opened = os.fstat(staged.descriptor)
        temporary = os.stat(
            staged.temporary_basename,
            dir_fd=staged.plan.parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(staged.published_before.st_mode)
            or staged.published_before.st_nlink != 2
            or opened.st_nlink != 2
            or not same_stat(opened, temporary)
            or not same_stat(opened, staged.published_before, STAGE_IDENTITY_FIELDS)
        ):
            fail("output", f"{staged.plan.label} publication identity changed")
        os.unlink(
            staged.temporary_basename,
            dir_fd=staged.plan.parent_descriptor,
        )
        staged.temporary_basename = ""
        os.fsync(staged.plan.parent_descriptor)
        staged.published_before = os.stat(
            staged.plan.basename,
            dir_fd=staged.plan.parent_descriptor,
            follow_symlinks=False,
        )
        verify_published_output(staged)
    except OSError as error:
        fail("output", f"cannot publish {staged.plan.label} output: {error}")


def rollback_published_output(staged: StagedOutput) -> tuple[str, ...]:
    """Remove a destination only while it retains the captured published inode."""

    if not staged.published:
        return ()
    errors: list[str] = []
    try:
        observed = output_lstat(staged.plan)
        if observed is not None:
            expected = staged.published_before
            if expected is None:
                held = os.fstat(staged.descriptor)
                expected_identity = (held.st_dev, held.st_ino)
            else:
                expected_identity = (expected.st_dev, expected.st_ino)
            if (observed.st_dev, observed.st_ino) != expected_identity:
                errors.append(
                    f"{staged.plan.label} destination changed; refusing unsafe rollback"
                )
            else:
                os.unlink(
                    staged.plan.basename,
                    dir_fd=staged.plan.parent_descriptor,
                )
                os.fsync(staged.plan.parent_descriptor)
                if output_lstat(staged.plan) is not None:
                    errors.append(
                        f"{staged.plan.label} destination remained after rollback"
                    )
        staged.published = False
    except (OSError, HostedRawProfileError) as error:
        errors.append(f"cannot roll back {staged.plan.label} output: {error}")
    return tuple(errors)


def recheck_custody(
    inputs: tuple[InputSnapshot, ...],
    dependencies: tuple[DependencySnapshot, ...],
) -> None:
    for snapshot in inputs:
        recheck_input(snapshot)
    for snapshot in dependencies:
        recheck_dependency(snapshot)
    recheck_pypdf_runtime(PYPDF_MODULE, PYPDF_DEPENDENCY)


def publish_output_pair(
    plans: tuple[OutputPlan, OutputPlan],
    payloads: tuple[bytes, bytes],
    inputs: tuple[InputSnapshot, ...],
    dependencies: tuple[DependencySnapshot, ...],
) -> None:
    """Publish two fresh complete files or remove every published pair member."""

    staged: list[StagedOutput] = []
    try:
        staged.append(stage_output(plans[0], payloads[0]))
        staged.append(stage_output(plans[1], payloads[1]))
        recheck_custody(inputs, dependencies)
        recheck_output_plan(plans[0])
        recheck_output_plan(plans[1])
        recheck_stage(staged[0])
        recheck_stage(staged[1])
        publish_stage(staged[0])
        publish_stage(staged[1])
        verify_published_output(staged[0])
        verify_published_output(staged[1])
        recheck_custody(inputs, dependencies)
        recheck_output_parent(plans[0])
        recheck_output_parent(plans[1])
    except BaseException as primary:
        rollback_errors: list[str] = []
        for item in reversed(staged):
            rollback_errors.extend(rollback_published_output(item))
        cleanup_errors: list[str] = []
        for item in reversed(staged):
            cleanup_errors.extend(cleanup_stage(item))
        secondary = rollback_errors + cleanup_errors
        if secondary:
            fail(
                "output",
                f"pair publication failed ({type(primary).__name__}: {primary}); "
                f"rollback/cleanup also failed: {'; '.join(secondary)}",
            )
        raise
    cleanup_errors = []
    for item in reversed(staged):
        cleanup_errors.extend(cleanup_stage(item))
    if cleanup_errors:
        rollback_errors = []
        for item in reversed(staged):
            rollback_errors.extend(rollback_published_output(item))
        fail(
            "output",
            "published pair descriptor cleanup failed: "
            f"{'; '.join(cleanup_errors + rollback_errors)}",
        )


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(
            f"usage: {pathlib.Path(sys.argv[0]).name} "
            "HOSTED_FIXTURE.pdf CANDIDATE.pdf targets.txt navigation.txt",
            file=sys.stderr,
        )
        return 2
    snapshots: list[InputSnapshot] = []
    output_plans: list[OutputPlan] = []
    try:
        fixture = open_input(argv[0], "hosted fixture")
        snapshots.append(fixture)
        candidate = open_input(argv[1], "candidate")
        snapshots.append(candidate)
        inputs = (fixture, candidate)
        validate_input_identities(inputs)
        require_exact_hosted_fixture(fixture)

        targets_plan = prepare_output(
            pathlib.Path(argv[2]), "targets", inputs, PROTECTED_DEPENDENCIES
        )
        output_plans.append(targets_plan)
        navigation_plan = prepare_output(
            pathlib.Path(argv[3]), "navigation", inputs, PROTECTED_DEPENDENCIES
        )
        output_plans.append(navigation_plan)
        plans = (targets_plan, navigation_plan)
        validate_output_pair(plans)

        recheck_custody(inputs, PROTECTED_DEPENDENCIES)
        raw_relation, raw_diagnostic = compare_candidate_to_fixture_raw(
            fixture, candidate
        )

        fixture_report = STRUCTURE.validate_bytes(
            fixture.data, enforce_manifest_digests=True
        )
        candidate_report = STRUCTURE.validate_bytes(
            candidate.data, enforce_manifest_digests=True
        )
        if fixture_report != candidate_report:
            fail(
                "hosted_structure_relation",
                "fixture and candidate complete strict structure reports differ",
            )

        targets_payload = report_payload(candidate_report.targets, "targets")
        navigation_payload = report_payload(candidate_report.navigation, "navigation")
        recheck_custody(inputs, PROTECTED_DEPENDENCIES)
        recheck_output_plan(targets_plan)
        recheck_output_plan(navigation_plan)
        publish_output_pair(
            plans,
            (targets_payload, navigation_payload),
            inputs,
            PROTECTED_DEPENDENCIES,
        )
    except (OSError, HostedRawProfileError, STRUCTURE.PdfStructureError) as error:
        code = getattr(error, "code", "io")
        print(f"{CHECK_NAME} failed [{code}]: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"{CHECK_NAME} failed [internal]: {error}", file=sys.stderr)
        return 1
    finally:
        for plan in reversed(output_plans):
            try:
                os.close(plan.parent_descriptor)
            except OSError:
                pass
        for snapshot in reversed(snapshots):
            try:
                os.close(snapshot.descriptor)
            except OSError:
                pass

    print(
        "OK: candidate matches the exact hosted raw profile and complete strict "
        f"canonical structure (bytes={len(fixture.data)}; "
        f"fixture_sha256={hashlib.sha256(fixture.data).hexdigest()}; "
        f"candidate_sha256={hashlib.sha256(candidate.data).hexdigest()}; "
        f"navigation_sha256={candidate_report.navigation_sha256}; "
        f"structure_sha256={candidate_report.structure_sha256}; "
        f"raw_relation={raw_relation}; raw_diagnostic={raw_diagnostic})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
