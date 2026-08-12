#!/usr/bin/env python3
"""Mutation-test the Lean descriptor-factorization firewall."""

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
):
    print(
        "ERROR: check-lean-descriptor-factorization-self-test.py requires Python -I -S",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import argparse
import builtins
import errno
import hashlib
import importlib.util
import json
import os
import py_compile
import stat
import subprocess
import sys
import tempfile
import types
from pathlib import Path


class MutationError(RuntimeError):
    """The baseline or mutation experiment did not fail closed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def _source_parent_identities(path: Path, role: str) -> tuple[
    tuple[str, int, int, int], ...
]:
    """Inspect lexical source parents without following symbolic links."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    identities: list[tuple[str, int, int, int]] = []
    for parent in reversed(absolute.parents):
        metadata = parent.lstat()
        require(
            not stat.S_ISLNK(metadata.st_mode) and stat.S_ISDIR(metadata.st_mode),
            f"{role} must not traverse a symbolic-link or non-directory parent",
        )
        identities.append(
            (str(parent), metadata.st_dev, metadata.st_ino, metadata.st_mode)
        )
    return tuple(identities)


def _read_exact_source_bytes(path: Path, role: str) -> bytes:
    """Double-read one single-linked source leaf with parent endpoint checks."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    parents_before = _source_parent_identities(absolute, role)
    before = absolute.lstat()
    require(not stat.S_ISLNK(before.st_mode), f"{role} must not be a symbolic link")
    require(stat.S_ISREG(before.st_mode), f"{role} must be a regular file")
    require(before.st_nlink == 1, f"{role} must have exactly one hard link")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute, flags)
    try:
        descriptor_before = os.fstat(descriptor)
        require(
            stat.S_ISREG(descriptor_before.st_mode)
            and descriptor_before.st_nlink == 1,
            f"{role} open descriptor is not a single-linked regular file",
        )

        def read_all() -> bytes:
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    return b"".join(chunks)
                chunks.append(chunk)

        first = read_all()
        middle = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = read_all()
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = absolute.lstat()
    identities = (
        (before.st_dev, before.st_ino, before.st_mode, before.st_nlink, before.st_size,
         before.st_mtime_ns, before.st_ctime_ns),
        (
            descriptor_before.st_dev,
            descriptor_before.st_ino,
            descriptor_before.st_mode,
            descriptor_before.st_nlink,
            descriptor_before.st_size,
            descriptor_before.st_mtime_ns,
            descriptor_before.st_ctime_ns,
        ),
        (middle.st_dev, middle.st_ino, middle.st_mode, middle.st_nlink, middle.st_size,
         middle.st_mtime_ns, middle.st_ctime_ns),
        (
            after_descriptor.st_dev,
            after_descriptor.st_ino,
            after_descriptor.st_mode,
            after_descriptor.st_nlink,
            after_descriptor.st_size,
            after_descriptor.st_mtime_ns,
            after_descriptor.st_ctime_ns,
        ),
        (after.st_dev, after.st_ino, after.st_mode, after.st_nlink, after.st_size,
         after.st_mtime_ns, after.st_ctime_ns),
    )
    require(
        all(identity == identities[0] for identity in identities[1:]),
        f"{role} identity or metadata changed during exact-source read",
    )
    require(first == second, f"{role} bytes changed during exact-source double read")
    require(len(first) == before.st_size, f"{role} byte length changed")
    require(
        _source_parent_identities(absolute, role) == parents_before,
        f"{role} parent identity changed during exact-source read",
    )
    return first


def load_module_from_exact_source(
    path: Path,
    role: str,
    *,
    expected_sha256: str,
) -> tuple[types.ModuleType, bytes]:
    """Digest-bind exact source bytes before compiling or executing them."""

    require(
        len(expected_sha256) == 64
        and all(character in "0123456789abcdef" for character in expected_sha256),
        f"{role} expected source digest is not canonical lowercase SHA-256",
    )
    source_bytes = _read_exact_source_bytes(path, role)
    digest = hashlib.sha256(source_bytes).hexdigest()
    require(
        digest == expected_sha256,
        f"{role} exact source digest differs before compilation",
    )

    stem = "".join(character if character.isalnum() else "_" for character in role)
    base_name = f"_pid_rs_exact_{stem}_{digest}"
    module_name = base_name
    suffix = 0
    while module_name in sys.modules:
        suffix += 1
        module_name = f"{base_name}_{suffix}"
    code = compile(
        source_bytes,
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module, source_bytes


SELF_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SELF_PATH.parent.parent
CHECKER = ROOT / "scripts/check-lean-descriptor-factorization.py"
EXPECTED_CHECKER_SOURCE_SHA256 = (
    "7d1c4e4942d4430c6732c9b25492afa847c06aac371ce3dbbd648ba9cfde2bd0"
)
checker, CHECKER_SOURCE_BYTES = load_module_from_exact_source(
    CHECKER,
    "check_lean_descriptor_factorization",
    expected_sha256=EXPECTED_CHECKER_SOURCE_SHA256,
)
CHECKER_SOURCE_SHA256 = hashlib.sha256(CHECKER_SOURCE_BYTES).hexdigest()

PROJECT = checker.PROJECT
SOURCE = checker.SOURCE
EXPECTED_SOURCE_SHA256 = checker.EXPECTED_SOURCE_SHA256

MACOS_VERSION_OUTPUT = (
    "Lean (version 4.33.0, arm64-apple-darwin24.6.0, "
    "commit d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\n"
)
LINUX_VERSION_OUTPUT = (
    "Lean (version 4.33.0, x86_64-unknown-linux-gnu, "
    "commit d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\n"
)

MUTATIONS = (
    (
        "remove_factorization_premise",
        "theorem equal_descriptors_and_factorization_force_equal_atoms\n"
        "    {sys desc atm : Type*}\n"
        "    (descriptor : sys → desc)\n"
        "    (atom : sys → atm)\n"
        "    (factor : desc → atm)\n"
        "    (hfactor : ∀ system, atom system = factor (descriptor system))\n"
        "    {left right : sys}\n",
        "theorem equal_descriptors_and_factorization_force_equal_atoms\n"
        "    {sys desc atm : Type*}\n"
        "    (descriptor : sys → desc)\n"
        "    (atom : sys → atm)\n"
        "    (factor : desc → atm)\n"
        "    {left right : sys}\n",
    ),
    (
        "replace_quantity_difference_with_equality",
        "    (hquantity : quantity left ≠ quantity right) :\n",
        "    (hquantity : quantity left = quantity right) :\n",
    ),
    (
        "replace_atom_difference_with_equality",
        "    (hatom : atom left ≠ atom right) :\n",
        "    (hatom : atom left = atom right) :\n",
    ),
)

SEMANTIC_COUNTERMODELS = r"""

namespace PidDescriptorFactorizationCountermodels

/-- Equal descriptors do not force equal atoms without a factorization premise. -/
example :
    let descriptor : Bool → Unit := fun _ => ()
    let atom : Bool → Bool := fun value => value
    descriptor false = descriptor true ∧ atom false ≠ atom true := by
  decide

/-- If the two quantities are equal, a universal reconstruction can exist. -/
example :
    let descriptor : Bool → Unit := fun _ => ()
    let atom : Bool → Unit := fun _ => ()
    let quantity : Bool → Unit := fun _ => ()
    descriptor false = descriptor true ∧
      quantity false = quantity true ∧
      ∃ reconstruct : Unit → Unit,
        ∀ system, reconstruct (atom system) = quantity system := by
  dsimp
  constructor
  · rfl
  constructor
  · rfl
  · exact ⟨fun _ => (), fun _ => rfl⟩

/-- If the two atoms are equal, descriptor factorization can exist. -/
example :
    let descriptor : Bool → Unit := fun _ => ()
    let atom : Bool → Unit := fun _ => ()
    descriptor false = descriptor true ∧
      atom false = atom true ∧
      ∃ factor : Unit → Unit,
        ∀ system, atom system = factor (descriptor system) := by
  dsimp
  constructor
  · rfl
  constructor
  · rfl
  · exact ⟨fun _ => (), fun _ => rfl⟩

end PidDescriptorFactorizationCountermodels
"""


def version_probe(
    stdout: str,
    *,
    returncode: int = 0,
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    """Construct a deterministic `lean --version` probe fixture."""

    return subprocess.CompletedProcess(
        args=["lake", "env", "lean", "--version"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def version_probe_sha256(probe: subprocess.CompletedProcess[str]) -> str:
    """Hash the typed probe fixture without relying on field concatenation."""

    encoded = json.dumps(
        {
            "returncode": probe.returncode,
            "stderr": probe.stderr,
            "stdout": probe.stdout,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def contract_probe_sha256(payload: dict[str, object]) -> str:
    """Hash one canonical, path-independent hostile/control fixture."""

    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def check_version_probe_contract() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    """Check portable controls and hostile full-probe mutations."""

    controls = (
        (
            "macos_arm64",
            "arm64-apple-darwin24.6.0",
            version_probe(MACOS_VERSION_OUTPUT),
        ),
        (
            "ubuntu_x86_64",
            "x86_64-unknown-linux-gnu",
            version_probe(LINUX_VERSION_OUTPUT),
        ),
    )
    control_results: list[dict[str, object]] = []
    observations: list[checker.LeanExecutableObservation] = []
    for name, expected_platform, probe in controls:
        observation = checker.parse_lean_version_probe(probe)
        require(
            observation.portable_identity == checker.EXPECTED_LEAN_IDENTITY,
            f"portable identity control changed: {name}",
        )
        require(
            observation.platform == expected_platform,
            f"platform control changed: {name}",
        )
        observations.append(observation)
        control_results.append(
            {
                "accepted": True,
                "name": name,
                "probe_sha256": version_probe_sha256(probe),
            }
        )

    require(
        len(observations) == 2,
        "portable identity control inventory changed",
    )
    require(
        observations[0].platform != observations[1].platform,
        "portable identity controls no longer exercise distinct platforms",
    )
    require(
        observations[0].portable_identity == observations[1].portable_identity,
        "host platform leaked into the portable Lean identity",
    )
    portable_json = json.dumps(
        observations[0].portable_identity.evidence(),
        sort_keys=True,
        separators=(",", ":"),
    )
    for observation in observations:
        require(
            observation.platform not in portable_json,
            "host platform leaked into serialized portable evidence",
        )

    commit = checker.EXPECTED_LEAN_COMMIT
    hostile = (
        ("nonzero_exit", version_probe(LINUX_VERSION_OUTPUT, returncode=1)),
        (
            "unexpected_stderr",
            version_probe(LINUX_VERSION_OUTPUT, stderr="unexpected diagnostic\n"),
        ),
        ("empty_stdout", version_probe("")),
        ("missing_final_newline", version_probe(LINUX_VERSION_OUTPUT[:-1])),
        ("extra_stdout_line", version_probe(LINUX_VERSION_OUTPUT + "extra\n")),
        ("extra_blank_line", version_probe(LINUX_VERSION_OUTPUT + "\n")),
        ("leading_whitespace", version_probe(" " + LINUX_VERSION_OUTPUT)),
        (
            "trailing_payload",
            version_probe(LINUX_VERSION_OUTPUT[:-1] + " trailing\n"),
        ),
        (
            "wrong_version",
            version_probe(
                LINUX_VERSION_OUTPUT.replace("version 4.33.0", "version 4.31.0", 1)
            ),
        ),
        (
            "malformed_version",
            version_probe(
                LINUX_VERSION_OUTPUT.replace("version 4.33.0", "version 4.33", 1)
            ),
        ),
        (
            "missing_platform",
            version_probe(
                LINUX_VERSION_OUTPUT.replace("x86_64-unknown-linux-gnu, ", "", 1)
            ),
        ),
        (
            "platform_with_whitespace",
            version_probe(
                LINUX_VERSION_OUTPUT.replace(
                    "x86_64-unknown-linux-gnu",
                    "x86_64 unknown linux gnu",
                    1,
                )
            ),
        ),
        (
            "platform_with_too_few_components",
            version_probe(
                LINUX_VERSION_OUTPUT.replace(
                    "x86_64-unknown-linux-gnu", "x86_64-linux", 1
                )
            ),
        ),
        (
            "missing_commit_label",
            version_probe(LINUX_VERSION_OUTPUT.replace("commit ", "", 1)),
        ),
        (
            "wrong_commit",
            version_probe(LINUX_VERSION_OUTPUT.replace(commit, "9" + commit[1:], 1)),
        ),
        (
            "short_commit",
            version_probe(LINUX_VERSION_OUTPUT.replace(commit, commit[:-1], 1)),
        ),
        (
            "uppercase_commit",
            version_probe(LINUX_VERSION_OUTPUT.replace(commit, commit.upper(), 1)),
        ),
        (
            "wrong_build",
            version_probe(LINUX_VERSION_OUTPUT.replace(", Release)", ", Debug)", 1)),
        ),
        (
            "missing_closing_delimiter",
            version_probe(LINUX_VERSION_OUTPUT.replace(")\n", "\n", 1)),
        ),
    )
    expected_errors = {
        "nonzero_exit": "Lean version probe exited unsuccessfully: 1",
        "unexpected_stderr": (
            "Lean version probe emitted unexpected stderr: "
            "'unexpected diagnostic\\n'"
        ),
        "empty_stdout": "Lean version probe stdout lacks its final newline",
        "missing_final_newline": (
            "Lean version probe stdout lacks its final newline"
        ),
        "extra_stdout_line": "Lean version probe did not emit exactly one line",
        "extra_blank_line": "Lean version probe did not emit exactly one line",
        "leading_whitespace": (
            "unexpected Lean version output: ' Lean (version 4.33.0, "
            "x86_64-unknown-linux-gnu, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\n'"
        ),
        "trailing_payload": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64-unknown-linux-gnu, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release) trailing\\n'"
        ),
        "wrong_version": (
            "unexpected Lean portable identity: LeanPortableIdentity("
            "version='4.31.0', commit="
            "'d8b18978322de05a8f3dba51ef03cf5461676c17', build='Release')"
        ),
        "malformed_version": (
            "unexpected Lean version output: 'Lean (version 4.33, "
            "x86_64-unknown-linux-gnu, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\n'"
        ),
        "missing_platform": (
            "unexpected Lean version output: 'Lean (version 4.33.0, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\n'"
        ),
        "platform_with_whitespace": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64 unknown linux gnu, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\n'"
        ),
        "platform_with_too_few_components": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64-linux, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\n'"
        ),
        "missing_commit_label": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64-unknown-linux-gnu, "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\n'"
        ),
        "wrong_commit": (
            "unexpected Lean portable identity: LeanPortableIdentity("
            "version='4.33.0', commit="
            "'98b18978322de05a8f3dba51ef03cf5461676c17', build='Release')"
        ),
        "short_commit": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64-unknown-linux-gnu, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c1, Release)\\n'"
        ),
        "uppercase_commit": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64-unknown-linux-gnu, commit "
            "D8B18978322DE05A8F3DBA51EF03CF5461676C17, Release)\\n'"
        ),
        "wrong_build": (
            "unexpected Lean portable identity: LeanPortableIdentity("
            "version='4.33.0', commit="
            "'d8b18978322de05a8f3dba51ef03cf5461676c17', build='Debug')"
        ),
        "missing_closing_delimiter": (
            "unexpected Lean version output: 'Lean (version 4.33.0, "
            "x86_64-unknown-linux-gnu, commit "
            "d8b18978322de05a8f3dba51ef03cf5461676c17, Release\\n'"
        ),
    }
    require(
        tuple(expected_errors) == tuple(name for name, _probe in hostile),
        "hostile Lean version expected-error inventory changed",
    )
    hostile_results: list[dict[str, object]] = []
    for name, probe in hostile:
        try:
            checker.parse_lean_version_probe(probe)
        except checker.LeanDescriptorFactorizationError as error:
            require(
                str(error) == expected_errors[name],
                f"hostile Lean version probe rejected for the wrong reason: {name}",
            )
            hostile_results.append(
                {
                    "name": name,
                    "probe_sha256": version_probe_sha256(probe),
                    "rejection_reason": expected_errors[name],
                    "rejected": True,
                }
            )
        else:
            require(False, f"hostile Lean version probe survived: {name}")

    require(
        len(hostile_results) == 19,
        "hostile Lean version probe inventory changed",
    )
    all_probe_hashes = [
        str(item["probe_sha256"]) for item in control_results + hostile_results
    ]
    require(
        len(set(all_probe_hashes)) == 21,
        "Lean version positive/hostile probe hashes are not pairwise distinct",
    )
    return control_results, hostile_results


def version_contract_evidence(
    controls: list[dict[str, object]],
    hostile: list[dict[str, object]],
) -> dict[str, object]:
    """Build separately counted evidence for the portability contract."""

    return {
        "lean_version_portability_controls": controls,
        "lean_version_portability_controls_accepted": len(controls),
        "lean_version_portable_identity": (checker.EXPECTED_LEAN_IDENTITY.evidence()),
        "lean_version_hostile_cases": hostile,
        "lean_version_hostile_cases_rejected": len(hostile),
    }


def check_exact_source_loader_contract() -> list[dict[str, object]]:
    """Retain two execution negatives and test pre-execution digest binding."""

    with tempfile.TemporaryDirectory(
        prefix="pid-descriptor-exact-source-loader-"
    ) as directory:
        root = Path(directory).resolve()
        reviewed = root / "reviewed.py"
        malicious = root / "malicious.py"
        reviewed.write_text('VALUE = "reviewed-source"\n', encoding="utf-8")
        malicious.write_text('VALUE = "malicious-cache"\n', encoding="utf-8")
        cache = Path(importlib.util.cache_from_source(str(reviewed)))
        cache.parent.mkdir(parents=True, exist_ok=True)
        py_compile.compile(
            str(malicious),
            cfile=str(cache),
            dfile=str(reviewed),
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )

        vulnerable_name = "_pid_rs_unchecked_hash_pyc_negative_control"
        vulnerable_spec = importlib.util.spec_from_file_location(
            vulnerable_name, reviewed
        )
        require(
            vulnerable_spec is not None and vulnerable_spec.loader is not None,
            "cannot construct unchecked-hash bytecode negative control",
        )
        vulnerable = importlib.util.module_from_spec(vulnerable_spec)
        sys.modules[vulnerable_name] = vulnerable
        try:
            vulnerable_spec.loader.exec_module(vulnerable)
            vulnerable_value = getattr(vulnerable, "VALUE", None)
        finally:
            sys.modules.pop(vulnerable_name, None)
        require(
            vulnerable_value == "malicious-cache",
            "unchecked-hash bytecode negative control did not reproduce substitution",
        )

        reviewed_digest = hashlib.sha256(reviewed.read_bytes()).hexdigest()
        exact, exact_bytes = load_module_from_exact_source(
            reviewed,
            "reviewed_cache_control",
            expected_sha256=reviewed_digest,
        )
        try:
            exact_value = getattr(exact, "VALUE", None)
        finally:
            sys.modules.pop(exact.__name__, None)
        require(
            exact_value == "reviewed-source",
            "exact-source loader did not execute the reviewed source bytes",
        )
        require(
            exact_bytes == b'VALUE = "reviewed-source"\n',
            "exact-source loader returned unexpected bytes",
        )

        lexical_root = root / "lexical-root"
        lexical_scripts = lexical_root / "scripts"
        attacker_root = root / "attacker-root"
        held_root = root / "held-root"
        lexical_scripts.mkdir(parents=True)
        attacker_root.mkdir()
        checker_copy = lexical_scripts / "checker.py"
        checker_copy.write_bytes(CHECKER_SOURCE_BYTES)
        real_compile = builtins.compile
        compile_calls = 0
        loaded_checker: types.ModuleType | None = None

        def compile_after_parent_substitution(
            *arguments: object,
            **keywords: object,
        ) -> object:
            nonlocal compile_calls
            compile_calls += 1
            if compile_calls == 1:
                lexical_root.rename(held_root)
                lexical_root.symlink_to(attacker_root, target_is_directory=True)
            return real_compile(*arguments, **keywords)

        builtins.compile = compile_after_parent_substitution
        try:
            loaded_checker, loaded_checker_bytes = load_module_from_exact_source(
                checker_copy,
                "post_digest_parent_substitution_control",
                expected_sha256=CHECKER_SOURCE_SHA256,
            )
            require(
                loaded_checker_bytes == CHECKER_SOURCE_BYTES,
                "post-digest parent control changed exact checker source bytes",
            )
            require(
                loaded_checker.SCRIPT_PATH == checker_copy
                and loaded_checker.ROOT == lexical_root,
                "post-digest parent substitution redirected checker path semantics",
            )
        finally:
            builtins.compile = real_compile
            if lexical_root.is_symlink():
                lexical_root.unlink()
            if held_root.exists():
                held_root.rename(lexical_root)
            if loaded_checker is not None:
                sys.modules.pop(loaded_checker.__name__, None)
        require(
            compile_calls == 1,
            "post-digest parent substitution compile inventory changed",
        )

        live = root / "live"
        attacker = root / "attacker"
        held = root / "held"
        live.mkdir()
        attacker.mkdir()
        live_source = live / "reviewed.py"
        attacker_source = attacker / "reviewed.py"
        live_bytes = b'VALUE = "reviewed-parent"\n'
        attacker_bytes = (
            "import builtins\n"
            "builtins._PID_RS_PARENT_SUBSTITUTION_EXECUTED = True\n"
            'VALUE = "malicious-parent"\n'
        ).encode("utf-8")
        live_source.write_bytes(live_bytes)
        attacker_source.write_bytes(attacker_bytes)

        before = live_source.lstat()
        live.rename(held)
        attacker.rename(live)
        substituted_bytes = live_source.read_bytes()
        live.rename(attacker)
        held.rename(live)
        after = live_source.lstat()
        require(
            (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino),
            "parent swap/use/restore negative did not restore the reviewed leaf",
        )
        namespace: dict[str, object] = {}
        exec(
            compile(
                substituted_bytes,
                str(live_source),
                "exec",
                dont_inherit=True,
            ),
            namespace,
        )
        require(
            namespace.get("VALUE") == "malicious-parent"
            and getattr(
                builtins,
                "_PID_RS_PARENT_SUBSTITUTION_EXECUTED",
                False,
            )
            is True,
            "parent swap/use/restore negative did not execute substituted bytes",
        )
        delattr(builtins, "_PID_RS_PARENT_SUBSTITUTION_EXECUTED")

        live.rename(held)
        attacker.rename(live)
        try:
            try:
                load_module_from_exact_source(
                    live_source,
                    "parent_substitution_control",
                    expected_sha256=hashlib.sha256(live_bytes).hexdigest(),
                )
            except MutationError as error:
                require(
                    str(error)
                    == (
                        "parent_substitution_control exact source digest differs "
                        "before compilation"
                    ),
                    "parent-substituted source was rejected for the wrong reason",
                )
            else:
                require(False, "parent-substituted source survived digest gate")
        finally:
            live.rename(attacker)
            held.rename(live)
        require(
            not hasattr(builtins, "_PID_RS_PARENT_SUBSTITUTION_EXECUTED"),
            "parent-substituted source executed before digest rejection",
        )
    controls = [
        {
            "demonstrated": True,
            "name": "sourcefileloader_unchecked_hash_pyc_substitution",
            "observed": "malicious-cache",
            "probe_sha256": contract_probe_sha256(
                {
                    "expected_observation": "malicious-cache",
                    "loader": "SourceFileLoader",
                    "malicious_source_sha256": hashlib.sha256(
                        b'VALUE = "malicious-cache"\n'
                    ).hexdigest(),
                    "pyc_invalidation": "UNCHECKED_HASH",
                    "reviewed_source_sha256": hashlib.sha256(
                        b'VALUE = "reviewed-source"\n'
                    ).hexdigest(),
                }
            ),
        },
        {
            "demonstrated": True,
            "name": "parent_directory_swap_use_restore_live_path_execution",
            "observed": "malicious-parent",
            "probe_sha256": contract_probe_sha256(
                {
                    "attacker_source_sha256": hashlib.sha256(
                        attacker_bytes
                    ).hexdigest(),
                    "expected_observation": "malicious-parent",
                    "reviewed_source_sha256": hashlib.sha256(live_bytes).hexdigest(),
                    "route": "lstat_read_live_path_restore_lstat_compile_exec",
                }
            ),
        },
        {
            "accepted": True,
            "name": "digest_bound_double_read_compile_exec_exact_source",
            "observed": "reviewed-source-and-lexical-root",
            "probe_sha256": contract_probe_sha256(
                {
                    "compile": "digest_bound_exact_double_read_source_bytes",
                    "expected_observation": "reviewed-source",
                    "malicious_source_sha256": hashlib.sha256(
                        b'VALUE = "malicious-cache"\n'
                    ).hexdigest(),
                    "post_digest_parent_symlink_swap": (
                        "lexical_checker_root_retained"
                    ),
                    "reviewed_source_sha256": hashlib.sha256(
                        b'VALUE = "reviewed-source"\n'
                    ).hexdigest(),
                }
            ),
        },
        {
            "name": "digest_bound_rejects_parent_substitution_before_exec",
            "probe_sha256": contract_probe_sha256(
                {
                    "attacker_source_sha256": hashlib.sha256(
                        attacker_bytes
                    ).hexdigest(),
                    "expected_source_sha256": hashlib.sha256(live_bytes).hexdigest(),
                    "marker_absent": True,
                    "route": "digest_before_compile_exec",
                }
            ),
            "rejection_reason": (
                "parent_substitution_control exact source digest differs before "
                "compilation"
            ),
            "rejected": True,
        },
    ]
    require(
        len(controls) == 4,
        "exact-source loader control inventory changed",
    )
    require(
        len({str(item["probe_sha256"]) for item in controls}) == len(controls),
        "exact-source loader control digests are not distinct",
    )
    return controls


def check_input_snapshot_contract() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    """Reject six attacks and retain one endpoint-replay false negative."""

    results: list[dict[str, object]] = []
    retained_negatives: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-descriptor-input-snapshot-"
    ) as directory:
        root = Path(directory).resolve()
        fixture = root / "fixture.txt"
        fixture.write_bytes(b"first\n")
        initial = checker.read_stable_regular_file(fixture, "snapshot fixture")
        fixture.write_bytes(b"second\n")
        try:
            checker.require_snapshot_unchanged(initial)
        except checker.LeanDescriptorFactorizationError as error:
            require(
                str(error)
                == "snapshot fixture identity changed after initial snapshot",
                "post-snapshot mutation was rejected for the wrong reason",
            )
            results.append(
                {
                    "name": "mutation_between_snapshot_and_replay",
                    "rejection_reason": (
                        "snapshot fixture identity changed after initial snapshot"
                    ),
                    "probe_sha256": contract_probe_sha256(
                        {
                            "after": hashlib.sha256(b"second\n").hexdigest(),
                            "before": hashlib.sha256(b"first\n").hexdigest(),
                            "route": "post_snapshot_replay",
                        }
                    ),
                    "rejected": True,
                }
            )
        else:
            require(False, "mutation between snapshot and replay survived")

        target = root / "target.txt"
        target.write_bytes(b"target\n")
        link = root / "link.txt"
        link.symlink_to(target)
        try:
            checker.read_stable_regular_file(link, "symlink fixture")
        except checker.LeanDescriptorFactorizationError as error:
            require(
                str(error)
                == (
                    "symlink fixture must be a regular, non-symbolic-link file"
                ),
                "symbolic-link input was rejected for the wrong reason",
            )
            results.append(
                {
                    "name": "symbolic_link_input",
                    "rejection_reason": (
                        "symlink fixture must be a regular, non-symbolic-link file"
                    ),
                    "probe_sha256": contract_probe_sha256(
                        {
                            "link_target_sha256": hashlib.sha256(
                                b"target\n"
                            ).hexdigest(),
                            "route": "symbolic_link_input",
                        }
                    ),
                    "rejected": True,
                }
            )
        else:
            require(False, "symbolic-link input survived")

        unstable = root / "unstable.txt"
        unstable.write_bytes(b"before\n")
        original_read = checker.os.read
        changed = False

        def mutate_after_first_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            chunk = original_read(descriptor, size)
            if chunk == b"" and not changed:
                unstable.write_bytes(b"during\n")
                changed = True
            return chunk

        checker.os.read = mutate_after_first_read
        try:
            try:
                checker.read_stable_regular_file(unstable, "unstable fixture")
            except checker.LeanDescriptorFactorizationError as error:
                require(
                    str(error)
                    == "unstable fixture metadata or identity changed during snapshot",
                    "double-read mutation was rejected for the wrong reason",
                )
                results.append(
                    {
                        "name": "mutation_during_double_read",
                        "rejection_reason": (
                            "unstable fixture metadata or identity changed during "
                            "snapshot"
                        ),
                        "probe_sha256": contract_probe_sha256(
                            {
                                "after": hashlib.sha256(b"during\n").hexdigest(),
                                "before": hashlib.sha256(b"before\n").hexdigest(),
                                "route": "open_descriptor_double_read",
                            }
                        ),
                        "rejected": True,
                    }
                )
            else:
                require(False, "mutation during double-read survived")
        finally:
            checker.os.read = original_read
        require(changed, "unstable-file control did not reach its mutation point")

        real_parent = root / "real-parent"
        real_parent.mkdir()
        parent_target = real_parent / "target.txt"
        parent_target.write_bytes(b"parent-target\n")
        linked_parent = root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        try:
            checker.read_stable_regular_file(
                linked_parent / "target.txt",
                "symlink-parent fixture",
            )
        except checker.LeanDescriptorFactorizationError as error:
            require(
                str(error)
                == (
                    "symlink-parent fixture must not be reached through a "
                    "symbolic-link parent"
                ),
                "symbolic-link parent was rejected for the wrong reason",
            )
            results.append(
                {
                    "name": "symbolic_link_parent_component",
                    "rejection_reason": (
                        "symlink-parent fixture must not be reached through a "
                        "symbolic-link parent"
                    ),
                    "probe_sha256": contract_probe_sha256(
                        {
                            "route": "symbolic_link_parent_component",
                            "target_sha256": hashlib.sha256(
                                b"parent-target\n"
                            ).hexdigest(),
                        }
                    ),
                    "rejected": True,
                }
            )
        else:
            require(False, "symbolic-link parent component survived")

        hardlink_source = root / "hardlink-source.txt"
        hardlink_alias = root / "hardlink-alias.txt"
        hardlink_source.write_bytes(b"multiply-linked\n")
        os.link(hardlink_source, hardlink_alias)
        try:
            checker.read_stable_regular_file(
                hardlink_alias,
                "hard-link fixture",
            )
        except checker.LeanDescriptorFactorizationError as error:
            require(
                str(error) == "hard-link fixture must have exactly one hard link",
                "multiply-linked leaf was rejected for the wrong reason",
            )
            results.append(
                {
                    "name": "multiply_linked_leaf",
                    "rejection_reason": (
                        "hard-link fixture must have exactly one hard link"
                    ),
                    "probe_sha256": contract_probe_sha256(
                        {
                            "link_count": 2,
                            "route": "hard_link_leaf",
                            "target_sha256": hashlib.sha256(
                                b"multiply-linked\n"
                            ).hexdigest(),
                        }
                    ),
                    "rejected": True,
                }
            )
        else:
            require(False, "multiply-linked leaf survived")

        observed = root / "observed-parent"
        attacker_parent = root / "attacker-parent"
        held_parent = root / "held-parent"
        observed.mkdir()
        attacker_parent.mkdir()
        observed_file = observed / "fixture.txt"
        observed_file.write_bytes(b"reviewed-parent\n")
        (attacker_parent / "fixture.txt").write_bytes(b"attacker-parent\n")
        original_descriptor_read = checker._read_descriptor_bytes
        descriptor_reads = 0

        def replace_parent_after_first_descriptor_read(descriptor: int) -> bytes:
            nonlocal descriptor_reads
            raw = original_descriptor_read(descriptor)
            descriptor_reads += 1
            if descriptor_reads == 1:
                observed.rename(held_parent)
                attacker_parent.rename(observed)
            return raw

        checker._read_descriptor_bytes = replace_parent_after_first_descriptor_read
        try:
            try:
                checker.read_stable_regular_file(
                    observed_file,
                    "parent-replacement fixture",
                )
            except checker.LeanDescriptorFactorizationError as error:
                require(
                    str(error)
                    == (
                        "parent-replacement fixture metadata or identity changed "
                        "during snapshot"
                    ),
                    "parent replacement was rejected for the wrong reason",
                )
                results.append(
                    {
                        "name": "parent_replacement_during_snapshot",
                        "rejection_reason": (
                            "parent-replacement fixture metadata or identity changed "
                            "during snapshot"
                        ),
                        "probe_sha256": contract_probe_sha256(
                            {
                                "attacker_sha256": hashlib.sha256(
                                    b"attacker-parent\n"
                                ).hexdigest(),
                                "reviewed_sha256": hashlib.sha256(
                                    b"reviewed-parent\n"
                                ).hexdigest(),
                                "routes": [
                                    "replace_parent_after_first_descriptor_read",
                                    (
                                        "parent_identity_mismatch_closes_leaf_"
                                        "descriptor"
                                    ),
                                ],
                            }
                        ),
                        "rejected": True,
                    }
                )
            else:
                require(False, "parent replacement during snapshot survived")
        finally:
            checker._read_descriptor_bytes = original_descriptor_read
            if observed.exists():
                observed.rename(attacker_parent)
            if held_parent.exists():
                held_parent.rename(observed)
        require(
            descriptor_reads >= 1,
            "parent-replacement control did not reach its mutation point",
        )

        cleanup_file = root / "parent-mismatch-fd-cleanup.txt"
        cleanup_file.write_bytes(b"fd-cleanup\n")
        original_open_regular = checker._open_regular_via_parent_descriptor
        opened_descriptor = -1

        def open_with_mismatched_parent_identity(
            path: Path,
            role: str,
        ) -> tuple[
            int,
            os.stat_result,
            tuple[checker.PathComponentIdentity, ...],
        ]:
            nonlocal opened_descriptor
            descriptor, metadata, parents = original_open_regular(path, role)
            opened_descriptor = descriptor
            require(bool(parents), "fd-cleanup control has no parent identities")
            last = parents[-1]
            mismatched_last = checker.PathComponentIdentity(
                path=last.path,
                identity=checker.DirectoryIdentity(
                    device=last.identity.device,
                    inode=last.identity.inode + 1,
                    mode=last.identity.mode,
                ),
            )
            return descriptor, metadata, (*parents[:-1], mismatched_last)

        checker._open_regular_via_parent_descriptor = (
            open_with_mismatched_parent_identity
        )
        try:
            try:
                checker.read_stable_regular_file(
                    cleanup_file,
                    "parent-mismatch fd-cleanup fixture",
                )
            except checker.LeanDescriptorFactorizationError as error:
                require(
                    str(error)
                    == (
                        "parent-mismatch fd-cleanup fixture parent identities changed "
                        "before descriptor traversal"
                    ),
                    "parent-identity mismatch was rejected for the wrong reason",
                )
            else:
                require(False, "mismatched walked parent identity survived")
        finally:
            checker._open_regular_via_parent_descriptor = original_open_regular
        require(
            opened_descriptor >= 0,
            "fd-cleanup control did not obtain a leaf descriptor",
        )
        try:
            os.fstat(opened_descriptor)
        except OSError as error:
            require(
                error.errno == errno.EBADF,
                "fd-cleanup control failed with an unexpected descriptor error",
            )
        else:
            os.close(opened_descriptor)
            require(False, "parent-identity rejection leaked the leaf descriptor")

        endpoint_parent = root / "endpoint-parent"
        endpoint_attacker = root / "endpoint-attacker"
        endpoint_held = root / "endpoint-held"
        endpoint_parent.mkdir()
        endpoint_attacker.mkdir()
        endpoint_file = endpoint_parent / "fixture.txt"
        endpoint_file.write_bytes(b"endpoint-reviewed\n")
        (endpoint_attacker / "fixture.txt").write_bytes(b"endpoint-attacker\n")
        endpoint_snapshot = checker.read_stable_regular_file(
            endpoint_file,
            "endpoint replay fixture",
        )
        endpoint_parent.rename(endpoint_held)
        endpoint_attacker.rename(endpoint_parent)
        consumed = endpoint_file.read_bytes()
        endpoint_parent.rename(endpoint_attacker)
        endpoint_held.rename(endpoint_parent)
        require(
            consumed == b"endpoint-attacker\n",
            "endpoint swap/use/restore negative did not consume attacker bytes",
        )
        legacy_leaf = endpoint_file.lstat()
        legacy_raw = endpoint_file.read_bytes()
        require(
            checker._file_identity(legacy_leaf) == endpoint_snapshot.identity
            and legacy_raw == endpoint_snapshot.raw,
            "legacy leaf-only replay negative did not restore its endpoints",
        )
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": "endpoint_replay_misses_parent_swap_use_restore",
                "probe_sha256": contract_probe_sha256(
                    {
                        "attacker_sha256": hashlib.sha256(
                            b"endpoint-attacker\n"
                        ).hexdigest(),
                        "replay": "legacy_leaf_identity_and_bytes_accept_after_restore",
                        "reviewed_sha256": hashlib.sha256(
                            b"endpoint-reviewed\n"
                        ).hexdigest(),
                        "route": "snapshot_swap_consume_restore_replay",
                    }
                ),
            }
        )
        checker.require_snapshot_unchanged(endpoint_snapshot)

    require(len(results) == 6, "input snapshot hostile-control inventory changed")
    require(
        len({str(item["probe_sha256"]) for item in results}) == len(results),
        "input snapshot hostile-control digests are not distinct",
    )
    require(
        len(retained_negatives) == 1,
        "input snapshot retained-negative inventory changed",
    )
    return results, retained_negatives


def check_private_materialization_contract() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Check isolation, raw transport, and retained launcher limitations."""

    accepted: list[dict[str, object]] = []
    retained_negatives: list[dict[str, object]] = []
    raw_transport_hostile: list[dict[str, object]] = []
    stdin_isolation_subcontrols: list[dict[str, object]] = []
    raw_transport_order_subcontrols: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-descriptor-private-project-controls-"
    ) as directory:
        root = Path(directory).resolve()
        tracked = root / "tracked"
        tracked.mkdir()
        tracked_payloads = {
            "lake-manifest.json": b'{"packagesDir":".lake/packages"}\n',
            "lean-toolchain": b"leanprover/lean4:v4.33.0\n",
            "lakefile.toml": b'name = "fixture"\n',
        }
        for name, raw in tracked_payloads.items():
            path = tracked / name
            path.write_bytes(raw)
        tracked_snapshots: list[checker.StableFileSnapshot] = []
        for name in tracked_payloads:
            path = tracked / name
            tracked_snapshots.append(
                checker.read_stable_regular_file(path, f"tracked fixture {name}")
            )
        dependency_packages = root / "dependency-packages"
        dependency_packages.mkdir()
        dependency_leaf = dependency_packages / "dependency.txt"
        dependency_leaf.write_bytes(b"cache-before\n")
        private_root = root / "private-root"
        private_root.mkdir(mode=0o700)
        (
            private_project,
            private_project_identity,
            query_directory_identity,
            materialized,
            routed_dependency_packages,
            _dependency_identity,
        ) = checker._prepare_private_lean_project(
            private_root,
            tuple(tracked_snapshots),
            dependency_packages=dependency_packages,
        )
        tracked_attacker = root / "tracked-attacker"
        tracked_held = root / "tracked-held"
        tracked_attacker.mkdir()
        for name in tracked_payloads:
            (tracked_attacker / name).write_bytes(
                b"parent-substituted-after-materialization\n"
            )
        tracked.rename(tracked_held)
        tracked_attacker.rename(tracked)
        for snapshot, expected in zip(
            materialized,
            tracked_payloads.values(),
            strict=True,
        ):
            require(
                snapshot.path.read_bytes() == expected,
                "private tracked configuration followed a later source mutation",
            )
            checker.require_snapshot_unchanged(snapshot)
        tracked.rename(tracked_attacker)
        tracked_held.rename(tracked)
        accepted.append(
            {
                "accepted": True,
                "name": "private_project_retains_prevalidated_tracked_copies",
                "probe_sha256": contract_probe_sha256(
                    {
                        "materialized_sha256": [
                            hashlib.sha256(raw).hexdigest()
                            for raw in tracked_payloads.values()
                        ],
                        "route": (
                            "digest_bind_materialize_parent_substitute_source_"
                            "replay_private"
                        ),
                    }
                ),
            }
        )

        hostile_environment = {
            "DYLD_INSERT_LIBRARIES": "/attacker/dylib",
            "ELAN_TOOLCHAIN": "attacker",
            "HOME": "/retained/home",
            "LAKE_HOME": "/attacker/lake",
            "LD_PRELOAD": "/attacker/loader",
            "LEAN_PATH": "/attacker/lean",
            "PATH": "/attacker/bin",
            "PYTHONPATH": "/attacker/python",
            "SystemRoot": r"C:\Windows",
        }
        scrubbed = dict(
            checker.build_lean_environment(
                "/reviewed/bin/lake",
                ambient=hostile_environment,
            )
        )
        require(
            scrubbed.get("HOME") == "/retained/home"
            and scrubbed.get("SystemRoot") == r"C:\Windows",
            "environment scrub removed required neutral host variables",
        )
        require(
            not any(
                key in scrubbed
                for key in (
                    "DYLD_INSERT_LIBRARIES",
                    "ELAN_TOOLCHAIN",
                    "LAKE_HOME",
                    "LD_PRELOAD",
                    "LEAN_PATH",
                    "PYTHONPATH",
                )
            ),
            "environment scrub retained a forbidden override",
        )
        require(
            scrubbed.get("PATH", "").split(os.pathsep)[0] == "/reviewed/bin",
            "environment scrub did not bind the selected Lake parent first",
        )
        accepted.append(
            {
                "accepted": True,
                "name": "lean_lake_python_loader_environment_overrides_scrubbed",
                "probe_sha256": contract_probe_sha256(
                    {
                        "forbidden_keys": sorted(
                            set(hostile_environment).difference(scrubbed)
                        ),
                        "path_prefix": "/reviewed/bin",
                        "route": "explicit_environment_projection",
                    }
                ),
            }
        )

        fake_inputs = checker.VerifiedInputs(
            lake="/reviewed/bin/lake",
            lake_target=Path("/reviewed/bin/lake-target"),
            execution_project=private_project,
            execution_project_identity=private_project_identity,
            query_directory_identity=query_directory_identity,
            environment=tuple(sorted(scrubbed.items())),
            source_text="",
            lean_observation=checker.LeanExecutableObservation(
                portable_identity=checker.EXPECTED_LEAN_IDENTITY,
                platform="fixture-posix-platform",
            ),
            snapshots=tuple(tracked_snapshots),
            materialized_snapshots=materialized,
            dependency_packages=dependency_packages,
            dependency_packages_identity=_dependency_identity,
        )
        fake_bin = root / "fake-bin"
        fake_bin.mkdir()
        fake_lake = fake_bin / "lake"
        fake_lake.write_bytes(
            b"#!/bin/sh\n"
            b"/bin/pwd -P\n"
            b'/usr/bin/printf "%s|%s|%s\\n" "$1" "$2" "$3"\n'
            b"/bin/cat lean-toolchain \"$3\"\n"
        )
        fake_lake.chmod(0o700)
        reviewed_query = private_project / "queries/Fixture.lean"
        checker._write_exclusive_file_in_directory(
            reviewed_query.parent,
            query_directory_identity,
            reviewed_query.name,
            b"reviewed-query\n",
            "private launch fixture",
        )
        reviewed_query_snapshot = checker.read_stable_regular_file(
            reviewed_query,
            "private launch reviewed-query fixture",
        )
        attacker_project = root / "attacker-project"
        attacker_project.mkdir()
        (attacker_project / "queries").mkdir()
        (attacker_project / "lean-toolchain").write_bytes(b"attacker-toolchain\n")
        (attacker_project / "queries/Fixture.lean").write_bytes(
            b"attacker-query\n"
        )
        held_project = root / "held-private-project"
        descriptor_inputs = checker.VerifiedInputs(
            lake=str(fake_lake),
            lake_target=fake_lake,
            execution_project=private_project,
            execution_project_identity=private_project_identity,
            query_directory_identity=query_directory_identity,
            environment=tuple(
                sorted(
                    {
                        "HOME": "/retained/home",
                        "LANG": "C",
                        "LC_ALL": "C",
                        "PATH": "/usr/bin:/bin",
                        "TZ": "UTC",
                    }.items()
                )
            ),
            source_text="",
            lean_observation=fake_inputs.lean_observation,
            snapshots=tuple(tracked_snapshots),
            materialized_snapshots=materialized,
            dependency_packages=dependency_packages,
            dependency_packages_identity=_dependency_identity,
        )
        observed_launch: dict[str, object] = {}
        original_subprocess_run = checker.subprocess.run

        def swap_project_during_private_launch(
            command: list[str],
            **kwargs: object,
        ) -> subprocess.CompletedProcess[bytes]:
            observed_launch["command"] = command
            observed_launch["cwd"] = kwargs.get("cwd")
            observed_launch["env"] = kwargs.get("env")
            observed_launch["stdin"] = kwargs.get("stdin")
            observed_launch["timeout"] = kwargs.get("timeout")
            pass_fds = kwargs.get("pass_fds", ())
            require(
                isinstance(pass_fds, tuple),
                "private launch pass_fds is not a tuple",
            )
            observed_launch["pass_fds_count"] = len(pass_fds)
            observed_launch["preexec_fn_callable"] = callable(
                kwargs.get("preexec_fn")
            )
            observed_launch["text_mode_keywords"] = sorted(
                key
                for key in ("encoding", "errors", "text", "universal_newlines")
                if key in kwargs
            )
            private_project.rename(held_project)
            attacker_project.rename(private_project)
            try:
                return original_subprocess_run(command, **kwargs)
            finally:
                private_project.rename(attacker_project)
                held_project.rename(private_project)

        checker.subprocess.run = swap_project_during_private_launch
        try:
            descriptor_checked = checker._run_lean_process(
                descriptor_inputs,
                ["queries/Fixture.lean"],
                timeout=37,
            )
        finally:
            checker.subprocess.run = original_subprocess_run
        require(
            observed_launch
            == {
                "command": [
                    str(fake_lake),
                    "env",
                    "lean",
                    "queries/Fixture.lean",
                ],
                "cwd": None,
                "env": dict(descriptor_inputs.environment),
                "pass_fds_count": 1,
                "preexec_fn_callable": True,
                "stdin": subprocess.DEVNULL,
                "text_mode_keywords": [],
                "timeout": 37,
            },
            "private Lean subprocess wiring changed",
        )
        launch_lines = descriptor_checked.stdout.splitlines()
        require(
            descriptor_checked.returncode == 0
            and descriptor_checked.stderr == ""
            and launch_lines[-3:]
            == [
                "env|lean|queries/Fixture.lean",
                "leanprover/lean4:v4.33.0",
                "reviewed-query",
            ],
            "descriptor-pinned private launch consumed substituted project bytes",
        )
        require(
            all(
                snapshot.path.read_bytes() == expected
                for snapshot, expected in zip(
                    materialized,
                    tracked_payloads.values(),
                    strict=True,
                )
            ),
            "private config bytes changed before captured subprocess launch",
        )
        checker.require_snapshot_unchanged(reviewed_query_snapshot)
        accepted.append(
            {
                "accepted": True,
                "name": (
                    "descriptor_pinned_private_cwd_relative_query_and_"
                    "lake_proxy_launch"
                ),
                "probe_sha256": contract_probe_sha256(
                    {
                        "arguments": [
                            "env",
                            "lean",
                            "queries/Fixture.lean",
                        ],
                        "cwd": "descriptor_pinned_private_project",
                        "lake_basename": "lake",
                        "path_swap": "attacker_project_not_consumed",
                        "stdin": "DEVNULL",
                        "timeout": 37,
                    }
                ),
            }
        )

        stdin_probe = fake_bin / "stdin-probe"
        stdin_probe.write_bytes(
            b"#!/bin/sh\n"
            b"if IFS= read -r line; then\n"
            b'  /usr/bin/printf "consumed:%s\\n" "$line"\n'
            b"else\n"
            b"  /usr/bin/printf 'stdin-eof\\n'\n"
            b"fi\n"
        )
        stdin_probe.chmod(0o700)
        stdin_inputs = checker.VerifiedInputs(
            lake=str(stdin_probe),
            lake_target=stdin_probe,
            execution_project=private_project,
            execution_project_identity=private_project_identity,
            query_directory_identity=query_directory_identity,
            environment=descriptor_inputs.environment,
            source_text="",
            lean_observation=fake_inputs.lean_observation,
            snapshots=tuple(tracked_snapshots),
            materialized_snapshots=materialized,
            dependency_packages=dependency_packages,
            dependency_packages_identity=_dependency_identity,
        )
        ambient_stdin = b"ambient-parent-stdin-must-not-be-consumed\n"
        try:
            os.fstat(0)
        except OSError as error:
            require(
                error.errno == errno.EBADF,
                "stdin isolation control found an unexpected fd-0 error",
            )
            parent_stdin_was_open = False
            saved_parent_stdin = -1
        else:
            parent_stdin_was_open = True
            saved_parent_stdin = os.dup(0)
        ambient_read = -1
        ambient_write = -1
        try:
            ambient_read, ambient_write = os.pipe()
            try:
                require(
                    os.write(ambient_write, ambient_stdin) == len(ambient_stdin),
                    "stdin isolation control could not seed its ambient pipe",
                )
            finally:
                os.close(ambient_write)
                ambient_write = -1
            if ambient_read != 0:
                os.dup2(ambient_read, 0)
                os.close(ambient_read)
            ambient_read = -1
            stdin_checked = checker._run_lean_process(
                stdin_inputs,
                ["probe"],
                timeout=37,
            )
            remaining_ambient_stdin = os.read(0, len(ambient_stdin) + 1)
        finally:
            for open_descriptor in (ambient_write, ambient_read):
                if open_descriptor >= 0:
                    os.close(open_descriptor)
            if parent_stdin_was_open:
                os.dup2(saved_parent_stdin, 0)
                os.close(saved_parent_stdin)
            else:
                try:
                    os.close(0)
                except OSError as error:
                    require(
                        error.errno == errno.EBADF,
                        "stdin isolation control could not restore closed fd 0",
                    )
        require(
            stdin_checked.returncode == 0
            and stdin_checked.stderr == ""
            and stdin_checked.stdout == "stdin-eof\n",
            "DEVNULL child stdin did not produce exact EOF",
        )
        require(
            remaining_ambient_stdin == ambient_stdin,
            "child process consumed parent fd-0 contamination",
        )
        stdin_isolation_subcontrols.append(
            {
                "accepted": True,
                "name": "devnull_child_stdin_rejects_parent_fd0_contamination",
                "probe_sha256": contract_probe_sha256(
                    {
                        "ambient_stdin_sha256": hashlib.sha256(
                            ambient_stdin
                        ).hexdigest(),
                        "child_observation_sha256": hashlib.sha256(
                            b"stdin-eof\n"
                        ).hexdigest(),
                        "parent_pipe_replayed_unchanged": True,
                        "route": "live_parent_fd0_pipe_to_child_devnull",
                    }
                ),
            }
        )

        raw_transport_lake = fake_bin / "raw-transport-lake"
        raw_transport_lake.write_bytes(
            b"#!/bin/sh\n"
            b'case "$3" in\n'
            b"  crlf_stdout) printf 'Lean (version 4.33.0, "
            b"x86_64-unknown-linux-gnu, commit "
            b"d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\\r\\n' ;;\n"
            b"  cr_stderr) printf 'unexpected\\rdiagnostic\\n' >&2 ;;\n"
            b"  non_utf8_stdout) printf '\\377\\n' ;;\n"
            b"  non_utf8_stderr) printf '\\377\\n' >&2 ;;\n"
            b"  mixed_cr_non_utf8_stdout) printf '\\377\\r\\n' ;;\n"
            b"  mixed_stdout_invalid_stderr_cr) printf '\\377\\n'; "
            b"printf 'unexpected\\rdiagnostic\\n' >&2 ;;\n"
            b"  *) exit 97 ;;\n"
            b"esac\n"
        )
        raw_transport_lake.chmod(0o700)
        raw_transport_inputs = checker.VerifiedInputs(
            lake=str(raw_transport_lake),
            lake_target=raw_transport_lake,
            execution_project=private_project,
            execution_project_identity=private_project_identity,
            query_directory_identity=query_directory_identity,
            environment=descriptor_inputs.environment,
            source_text="",
            lean_observation=fake_inputs.lean_observation,
            snapshots=tuple(tracked_snapshots),
            materialized_snapshots=materialized,
            dependency_packages=dependency_packages,
            dependency_packages_identity=_dependency_identity,
        )
        raw_transport_cases = (
            (
                "raw_subprocess_crlf_stdout_before_decode",
                "crlf_stdout",
                "Lean process raw stdout contains a carriage return",
                (
                    b"Lean (version 4.33.0, x86_64-unknown-linux-gnu, commit "
                    b"d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\r\n"
                ),
                b"",
            ),
            (
                "raw_subprocess_cr_stderr_before_decode",
                "cr_stderr",
                "Lean process raw stderr contains a carriage return",
                b"",
                b"unexpected\rdiagnostic\n",
            ),
            (
                "raw_subprocess_non_utf8_stdout_before_decode",
                "non_utf8_stdout",
                "Lean process raw stdout is not strict UTF-8",
                b"\xff\n",
                b"",
            ),
            (
                "raw_subprocess_non_utf8_stderr_before_decode",
                "non_utf8_stderr",
                "Lean process raw stderr is not strict UTF-8",
                b"",
                b"\xff\n",
            ),
            (
                "raw_subprocess_cr_precedes_non_utf8_stdout",
                "mixed_cr_non_utf8_stdout",
                "Lean process raw stdout contains a carriage return",
                b"\xff\r\n",
                b"",
            ),
        )

        def exercise_raw_transport_case(
            name: str,
            argument: str,
            expected_error: str,
            raw_stdout: bytes,
            raw_stderr: bytes,
        ) -> subprocess.CompletedProcess[bytes]:
            observed_process: list[subprocess.CompletedProcess[bytes]] = []

            def capture_raw_process(
                command: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[bytes]:
                process = original_subprocess_run(command, **kwargs)
                require(
                    isinstance(process.stdout, bytes)
                    and isinstance(process.stderr, bytes),
                    f"raw Lean transport child was not captured as bytes: {name}",
                )
                observed_process.append(process)
                return process

            checker.subprocess.run = capture_raw_process
            try:
                checker._run_lean_process(
                    raw_transport_inputs,
                    [argument],
                    timeout=37,
                )
            except checker.LeanDescriptorFactorizationError as error:
                require(
                    str(error) == expected_error,
                    f"raw Lean transport rejected for the wrong reason: {name}",
                )
            else:
                require(False, f"raw Lean transport hostile case survived: {name}")
            finally:
                checker.subprocess.run = original_subprocess_run
            require(
                len(observed_process) == 1
                and observed_process[0].returncode == 0
                and observed_process[0].stdout == raw_stdout
                and observed_process[0].stderr == raw_stderr,
                f"raw Lean transport child bytes differ from fixture: {name}",
            )
            return observed_process[0]

        for name, argument, expected_error, raw_stdout, raw_stderr in (
            raw_transport_cases
        ):
            observed = exercise_raw_transport_case(
                name,
                argument,
                expected_error,
                raw_stdout,
                raw_stderr,
            )
            raw_transport_hostile.append(
                {
                    "name": name,
                    "probe_sha256": contract_probe_sha256(
                        {
                            "argument": argument,
                            "expected_error": expected_error,
                            "raw_stderr_sha256": hashlib.sha256(
                                observed.stderr
                            ).hexdigest(),
                            "raw_stdout_sha256": hashlib.sha256(
                                observed.stdout
                            ).hexdigest(),
                            "route": "live_subprocess_binary_pipe_before_decode",
                        }
                    ),
                    "rejection_reason": expected_error,
                    "rejected": True,
                }
            )

        cross_stream_name = "raw_subprocess_stdout_precedes_stderr_mixed_fault"
        cross_stream_argument = "mixed_stdout_invalid_stderr_cr"
        cross_stream_error = "Lean process raw stdout is not strict UTF-8"
        cross_stream_observed = exercise_raw_transport_case(
            cross_stream_name,
            cross_stream_argument,
            cross_stream_error,
            b"\xff\n",
            b"unexpected\rdiagnostic\n",
        )
        raw_transport_order_subcontrols.append(
            {
                "name": cross_stream_name,
                "probe_sha256": contract_probe_sha256(
                    {
                        "argument": cross_stream_argument,
                        "expected_error": cross_stream_error,
                        "raw_stderr_sha256": hashlib.sha256(
                            cross_stream_observed.stderr
                        ).hexdigest(),
                        "raw_stdout_sha256": hashlib.sha256(
                            cross_stream_observed.stdout
                        ).hexdigest(),
                        "route": (
                            "live_binary_pipe_mixed_stream_fault_proves_stdout_first"
                        ),
                    }
                ),
                "rejection_reason": cross_stream_error,
                "rejected": True,
            }
        )

        attacker_query_directory = root / "attacker-query-directory"
        attacker_query_directory.mkdir()
        (attacker_query_directory / "Fixture.lean").write_bytes(
            b"attacker-query-subtree\n"
        )
        held_query_directory = root / "held-query-directory"
        reviewed_query_directory = private_project / "queries"

        def swap_query_subtree_during_private_launch(
            command: list[str],
            **kwargs: object,
        ) -> subprocess.CompletedProcess[bytes]:
            reviewed_query_directory.rename(held_query_directory)
            attacker_query_directory.rename(reviewed_query_directory)
            try:
                return original_subprocess_run(command, **kwargs)
            finally:
                reviewed_query_directory.rename(attacker_query_directory)
                held_query_directory.rename(reviewed_query_directory)

        checker.subprocess.run = swap_query_subtree_during_private_launch
        try:
            query_subtree_checked = checker._run_lean_process(
                descriptor_inputs,
                ["queries/Fixture.lean"],
                timeout=37,
            )
        finally:
            checker.subprocess.run = original_subprocess_run
        require(
            query_subtree_checked.returncode == 0
            and query_subtree_checked.stderr == ""
            and query_subtree_checked.stdout.splitlines()[-1]
            == "attacker-query-subtree",
            "query-subtree swap/use/restore negative did not consume attacker bytes",
        )
        checker.require_snapshot_unchanged(reviewed_query_snapshot)
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": (
                    "descriptor_pinned_project_does_not_pin_query_subtree_entry"
                ),
                "probe_sha256": contract_probe_sha256(
                    {
                        "attacker_sha256": hashlib.sha256(
                            b"attacker-query-subtree\n"
                        ).hexdigest(),
                        "replay": "reviewed_query_identity_and_bytes_accept_after_restore",
                        "reviewed_sha256": hashlib.sha256(
                            b"reviewed-query\n"
                        ).hexdigest(),
                        "route": (
                            "project_fd_pinned_query_subtree_swap_consume_restore"
                        ),
                    }
                ),
            }
        )

        home_a = root / "home-a"
        home_b = root / "home-b"
        home_a.mkdir()
        home_b.mkdir()
        (home_a / "elan-state").write_bytes(b"reviewed-home-state\n")
        (home_b / "elan-state").write_bytes(b"attacker-home-state\n")
        home_probe = fake_bin / "home-probe"
        home_probe.write_bytes(b"#!/bin/sh\n/bin/cat \"$HOME/elan-state\"\n")
        home_probe.chmod(0o700)
        home_inputs = checker.VerifiedInputs(
            lake=str(home_probe),
            lake_target=home_probe,
            execution_project=private_project,
            execution_project_identity=private_project_identity,
            query_directory_identity=query_directory_identity,
            environment=tuple(
                sorted(
                    {
                        "HOME": str(home_b),
                        "LANG": "C",
                        "LC_ALL": "C",
                        "PATH": "/usr/bin:/bin",
                        "TZ": "UTC",
                    }.items()
                )
            ),
            source_text="",
            lean_observation=fake_inputs.lean_observation,
            snapshots=tuple(tracked_snapshots),
            materialized_snapshots=materialized,
            dependency_packages=dependency_packages,
            dependency_packages_identity=_dependency_identity,
        )
        home_checked = checker._run_lean_process(home_inputs, [], timeout=37)
        require(
            home_checked.returncode == 0
            and home_checked.stderr == ""
            and home_checked.stdout == "attacker-home-state\n",
            "retained HOME control did not influence child launcher state",
        )
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": "retained_home_can_influence_live_launcher_state",
                "probe_sha256": contract_probe_sha256(
                    {
                        "observed_sha256": hashlib.sha256(
                            b"attacker-home-state\n"
                        ).hexdigest(),
                        "reviewed_sha256": hashlib.sha256(
                            b"reviewed-home-state\n"
                        ).hexdigest(),
                        "route": "retained_HOME_visible_to_selected_launcher",
                    }
                ),
            }
        )

        dependency_leaf.write_bytes(b"cache-after\n")
        routed_leaf = private_project / ".lake/packages/dependency.txt"
        require(
            routed_dependency_packages == dependency_packages
            and routed_leaf.read_bytes() == b"cache-after\n",
            "live dependency-cache negative did not remain observable",
        )
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": "private_project_dependency_cache_remains_live",
                "probe_sha256": contract_probe_sha256(
                    {
                        "after_sha256": hashlib.sha256(
                            b"cache-after\n"
                        ).hexdigest(),
                        "before_sha256": hashlib.sha256(
                            b"cache-before\n"
                        ).hexdigest(),
                        "route": "private_lake_packages_symbolic_route",
                    }
                ),
            }
        )
    require(
        len(accepted) == 3
        and len(retained_negatives) == 3
        and len(raw_transport_hostile) == 5
        and len(stdin_isolation_subcontrols) == 1
        and len(raw_transport_order_subcontrols) == 1,
        "private materialization control inventory changed",
    )
    return (
        accepted,
        retained_negatives,
        raw_transport_hostile,
        stdin_isolation_subcontrols,
        raw_transport_order_subcontrols,
    )


def run_lean(
    inputs: checker.VerifiedInputs,
    filename: str,
    source_text: str,
) -> subprocess.CompletedProcess[str]:
    """Delegate exact private-source execution to the reviewed checker route."""

    return checker.run_lean_text(inputs, filename, source_text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Mutation-test the Lean descriptor-factorization proof and its "
            "portable version-evidence parser."
        )
    )
    parser.add_argument(
        "--parser-only",
        action="store_true",
        help=(
            "run POSIX macOS/Linux no-kernel source, filesystem, environment, "
            "and version-probe controls"
        ),
    )
    args = parser.parse_args()

    try:
        self_snapshot = checker.read_stable_regular_file(
            SELF_PATH, "descriptor-factorization self-test"
        )
        checker_snapshot = checker.read_stable_regular_file(
            CHECKER, "descriptor-factorization checker"
        )
        require(
            checker_snapshot.raw == CHECKER_SOURCE_BYTES,
            "executed descriptor checker bytes differ from exact loaded source",
        )
        exact_source_loader_controls = check_exact_source_loader_contract()
        (
            input_snapshot_controls,
            input_snapshot_retained_negatives,
        ) = check_input_snapshot_contract()
        (
            private_materialization_controls,
            private_materialization_retained_negatives,
            raw_process_transport_hostile_cases,
            process_stdin_isolation_subcontrols,
            raw_process_transport_order_subcontrols,
        ) = check_private_materialization_contract()
        retained_negatives = (
            input_snapshot_retained_negatives
            + private_materialization_retained_negatives
        )
        portability_controls, hostile_version_probes = check_version_probe_contract()
        version_evidence = version_contract_evidence(
            portability_controls,
            hostile_version_probes,
        )
        if args.parser_only:
            checker.require_snapshot_unchanged(checker_snapshot)
            checker.require_snapshot_unchanged(self_snapshot)
            parser_evidence = {
                "schema": (
                    "pid-rs/lean-descriptor-factorization-"
                    "version-parser-posix-custody-self-test/v4"
                ),
                "status": "passed",
                "descriptor_checker_source_sha256": CHECKER_SOURCE_SHA256,
                "self_test_source_sha256": self_snapshot.sha256,
                "exact_source_loader_controls": exact_source_loader_controls,
                "exact_source_loader_controls_passed": len(
                    exact_source_loader_controls
                ),
                "input_snapshot_hostile_cases": input_snapshot_controls,
                "input_snapshot_hostile_cases_rejected": len(
                    input_snapshot_controls
                ),
                "private_materialization_controls": (
                    private_materialization_controls
                ),
                "private_materialization_controls_passed": len(
                    private_materialization_controls
                ),
                "raw_process_transport_hostile_cases": (
                    raw_process_transport_hostile_cases
                ),
                "raw_process_transport_hostile_cases_rejected": len(
                    raw_process_transport_hostile_cases
                ),
                "process_stdin_isolation_subcontrols": (
                    process_stdin_isolation_subcontrols
                ),
                "process_stdin_isolation_subcontrols_passed": len(
                    process_stdin_isolation_subcontrols
                ),
                "raw_process_transport_order_subcontrols": (
                    raw_process_transport_order_subcontrols
                ),
                "raw_process_transport_order_subcontrols_rejected": len(
                    raw_process_transport_order_subcontrols
                ),
                "retained_negative_controls": retained_negatives,
                "retained_negative_controls_demonstrated": len(retained_negatives),
                **version_evidence,
                "boundary": (
                    "These POSIX no-kernel controls exercise strict parsing, the "
                    "cross-platform "
                    "macOS/Linux evidence projection, pre-execution source digest "
                    "binding, tracked-input private materialization, descriptor-pinned "
                    "child CWD, environment scrubbing, DEVNULL child stdin, raw-byte "
                    "subprocess capture before strict UTF-8 decoding, explicit stdout-"
                    "before-stderr mixed-fault precedence, and bounded snapshot "
                    "rejection. "
                    "Retained negatives show generic endpoint replay missing "
                    "swap/use/restore, a query-subtree swap surviving project-FD "
                    "pinning, HOME influencing live launcher state, and dependency-"
                    "cache bytes remaining live. "
                    "These controls do not execute Lean, kernel-check a theorem, support "
                    "native Windows handle custody, authenticate executable or "
                    "dependency bytes, establish cross-platform kernel equivalence, "
                    "cap captured-output memory, or terminate descendants when the "
                    "direct child times out. "
                    "PYTHONDONTWRITEBYTECODE alone would not prevent consumption of a "
                    "pre-existing unchecked-hash pyc."
                ),
            }
            print(
                json.dumps(
                    parser_evidence,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            return 0

        with tempfile.TemporaryDirectory(
            prefix="pid-descriptor-factorization-private-environment-"
        ) as directory:
            inputs = checker.verify_environment_and_source(Path(directory).resolve())
            require(
                inputs.snapshots[4].raw == CHECKER_SOURCE_BYTES,
                "verified descriptor checker bytes differ from exact loaded source",
            )
            require(
                inputs.lean_observation.portable_identity
                == checker.EXPECTED_LEAN_IDENTITY,
                "live Lean portable identity differs from the parser controls",
            )
            proof_results: list[dict[str, object]] = []
            baseline = run_lean(inputs, "Baseline.lean", inputs.source_text)
            require(
                baseline.returncode == 0,
                f"baseline Lean source failed: {baseline.stderr}",
            )
            require(
                baseline.stderr == "",
                f"baseline Lean source emitted unexpected stderr: {baseline.stderr}",
            )
            require(
                baseline.stdout == "",
                f"baseline Lean source emitted unexpected stdout: {baseline.stdout}",
            )
            countermodel_text = inputs.source_text + SEMANTIC_COUNTERMODELS
            countermodel_check = run_lean(
                inputs,
                "SemanticCountermodels.lean",
                countermodel_text,
            )
            require(
                countermodel_check.returncode == 0,
                f"semantic premise countermodels failed: {countermodel_check.stderr}",
            )
            require(
                countermodel_check.stderr == "",
                "semantic premise countermodels emitted unexpected stderr: "
                f"{countermodel_check.stderr}",
            )
            require(
                countermodel_check.stdout == "",
                "semantic premise countermodels emitted unexpected stdout: "
                f"{countermodel_check.stdout}",
            )
            for index, (name, before, after) in enumerate(MUTATIONS):
                require(
                    inputs.source_text.count(before) == 1,
                    f"mutation anchor is absent or ambiguous: {name}",
                )
                mutant_text = inputs.source_text.replace(before, after, 1)
                checked = run_lean(
                    inputs,
                    f"Mutation{index}.lean",
                    mutant_text,
                )
                require(
                    checked.returncode != 0,
                    f"scientifically meaningful proof mutation survived: {name}",
                )
                proof_results.append(
                    {
                        "name": name,
                        "killed": True,
                        "mutant_sha256": hashlib.sha256(
                            mutant_text.encode("utf-8")
                        ).hexdigest(),
                    }
                )
            checker.verify_post_execution_custody(inputs)
        checker.require_snapshot_unchanged(self_snapshot)
        evidence = {
            "schema": "pid-rs/lean-descriptor-factorization-mutations/v4",
            "status": "passed",
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "self_test_source_sha256": self_snapshot.sha256,
            "descriptor_checker_source_sha256": CHECKER_SOURCE_SHA256,
            "scientific_proof_mutations_killed": len(proof_results),
            "scientific_proof_mutations": proof_results,
            "semantic_countermodels_kernel_checked": 3,
            "semantic_countermodels_sha256": hashlib.sha256(
                SEMANTIC_COUNTERMODELS.encode("utf-8")
            ).hexdigest(),
            "exact_source_loader_controls": exact_source_loader_controls,
            "exact_source_loader_controls_passed": len(exact_source_loader_controls),
            "input_snapshot_files_checked": (
                len(inputs.snapshots) + len(inputs.materialized_snapshots) + 1
            ),
            "input_snapshot_replays_unchanged": (
                len(inputs.snapshots) + len(inputs.materialized_snapshots) + 1
            ),
            "private_query_files_checked": len(MUTATIONS) + 2,
            "private_query_replays_unchanged": len(MUTATIONS) + 2,
            "input_snapshot_hostile_cases": input_snapshot_controls,
            "input_snapshot_hostile_cases_rejected": len(input_snapshot_controls),
            "private_materialization_controls": private_materialization_controls,
            "private_materialization_controls_passed": len(
                private_materialization_controls
            ),
            "raw_process_transport_hostile_cases": (
                raw_process_transport_hostile_cases
            ),
            "raw_process_transport_hostile_cases_rejected": len(
                raw_process_transport_hostile_cases
            ),
            "process_stdin_isolation_subcontrols": (
                process_stdin_isolation_subcontrols
            ),
            "process_stdin_isolation_subcontrols_passed": len(
                process_stdin_isolation_subcontrols
            ),
            "raw_process_transport_order_subcontrols": (
                raw_process_transport_order_subcontrols
            ),
            "raw_process_transport_order_subcontrols_rejected": len(
                raw_process_transport_order_subcontrols
            ),
            "retained_negative_controls": retained_negatives,
            "retained_negative_controls_demonstrated": len(retained_negatives),
            **version_evidence,
            "boundary": (
                "The three scientific proof mutations and three kernel-checked finite "
                "countermodels separately exercise the factorization and distinctness "
                "premises. Separately counted parser, digest-bound-source, private-"
                "materialization, environment, and snapshot controls exercise portable "
                "evidence and bounded process-input custody. Five live binary-pipe "
                "attacks show that each stream rejects raw carriage returns before "
                "strict decoding and that strict decoding rejects invalid UTF-8 "
                "before semantic parsing. A separately typed live mixed-stream "
                "subcontrol proves stdout is rejected before stderr, while the frozen "
                "five-family count and same-stdout precedence witness remain unchanged. "
                "A live parent-fd-0 contamination probe proves child stdin is DEVNULL. "
                "Descriptor-pinned child "
                "CWD contains private-project pathname substitution after pinning, but "
                "does not pin the query-subtree entry; the concrete query swap and "
                "generic endpoint replay show swap/use/restore limits. HOME-influenced "
                "launcher state and dependency-package/cache bytes remain live. The "
                "direct-child timeout does not guarantee descendant termination, and "
                "captured stdout/stderr have no explicit byte ceiling. The "
                "stability window starts at the "
                "first in-process observation; no route binds abstract descriptors or "
                "atoms to a concrete PID implementation, authenticates selected Python/"
                "Lean or dependency bytes, or proves cross-platform kernel equivalence."
            ),
        }
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        MutationError,
        checker.LeanDescriptorFactorizationError,
    ) as error:
        print(
            f"Lean descriptor-factorization self-test failed: {error}", file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
