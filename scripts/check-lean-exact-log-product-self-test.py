#!/usr/bin/env python3
"""Isolated hostile and scope tests for the frozen Lean exact-log-product gate."""

# ruff: noqa: E402 -- isolation must be checked before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-lean-exact-log-product-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import types
from typing import Any, Callable, NoReturn


class MutationError(RuntimeError):
    """The baseline, a hostile case, or a declared scope probe behaved incorrectly."""


def fail(message: str) -> NoReturn:
    raise MutationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def metadata_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def parent_identities(path: Path, role: str) -> tuple[tuple[str, int, int, int], ...]:
    """Inspect every lexical parent without following symbolic links."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    identities: list[tuple[str, int, int, int]] = []
    for parent in reversed(absolute.parents):
        metadata = parent.lstat()
        require(
            stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
            f"{role} traverses a symbolic-link or non-directory parent",
        )
        identities.append(
            (str(parent), metadata.st_dev, metadata.st_ino, metadata.st_mode)
        )
    return tuple(identities)


def stable_read(path: Path, role: str) -> bytes:
    """Double-read one single-linked regular file through a no-follow descriptor."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    parents_before = parent_identities(absolute, role)
    before = absolute.lstat()
    require(not stat.S_ISLNK(before.st_mode), f"{role} must not be a symbolic link")
    require(stat.S_ISREG(before.st_mode), f"{role} must be a regular file")
    require(before.st_nlink == 1, f"{role} must have exactly one hard link")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute, flags)
    try:
        opened = os.fstat(descriptor)
        require(
            stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
            f"{role} descriptor is not a single-linked regular file",
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
        descriptor_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = absolute.lstat()
    identities = (
        metadata_identity(before),
        metadata_identity(opened),
        metadata_identity(middle),
        metadata_identity(descriptor_after),
        metadata_identity(after),
    )
    require(
        all(identity == identities[0] for identity in identities[1:]),
        f"{role} identity or metadata changed while it was read",
    )
    require(first == second, f"{role} bytes changed between descriptor reads")
    require(len(first) == before.st_size, f"{role} byte length changed")
    require(
        parent_identities(absolute, role) == parents_before,
        f"{role} parent identity changed while it was read",
    )
    return first


def load_exact_module(
    path: Path,
    role: str,
    expected_sha256: str,
) -> tuple[types.ModuleType, bytes]:
    """Compile and execute only the stable, digest-bound source bytes."""

    require(
        len(expected_sha256) == 64
        and all(character in "0123456789abcdef" for character in expected_sha256),
        f"{role} expected digest is not canonical lowercase SHA-256",
    )
    raw = stable_read(path, role)
    digest = sha256_bytes(raw)
    require(digest == expected_sha256, f"{role} exact source digest differs")
    module_name = f"_pid_rs_{role}_{digest}_{sys.flags.optimize}"
    require(module_name not in sys.modules, f"{role} module name already exists")
    code = compile(
        raw,
        os.fspath(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(path)
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
    return module, raw


SELF_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SELF_PATH.parent.parent
CHECKER_PATH = ROOT / "scripts/check-lean-exact-log-product.py"
SOURCE_PATH = ROOT / "audit/formal/lean-exact-log-product/PidExactLogProduct.lean"
EVIDENCE_PATH = ROOT / "audit/evidence/sxpid2-exact-log-product-hostile-4.33.0.json"
EXPECTED_CHECKER_SHA256 = (
    "52510a18ac5fa8b94113bfeba84f61cb28bdbe56be278fc76fb4d55407cb2dcd"
)
EXPECTED_SOURCE_SHA256 = (
    "f0727ea3061d561ba89ba49edebece971ce03bdecf03e0c32774a1c080dc07bf"
)
EXPECTED_THEOREMS = (
    "PidExactLogProduct.log_finset_zpow_product",
    "PidExactLogProduct.scaled_log_sum_eq_log_product",
    "PidExactLogProduct.scaled_log_pos_iff",
    "PidExactLogProduct.scaled_log_neg_iff",
    "PidExactLogProduct.scaled_log_eq_zero_iff",
    "PidExactLogProduct.two_nontrivial_logs_cancel",
    "PidExactLogProduct.retained_five_term_product_eq_one",
)
EXPECTED_CHECKER_OUTPUT_KEYS = frozenset(
    {
        "boundary",
        "checker_source_sha256",
        "lake_manifest_sha256",
        "lean_toolchain",
        "lean_version",
        "permitted_axioms",
        "schema",
        "source_sha256",
        "status",
        "theorems_kernel_checked",
    }
)
EXPECTED_BOUNDARY = (
    "Generic log/product/sign algebra only; concrete SxPID event extraction, lattice "
    "binding, executable refinement, sampling, and scientific validity remain separate "
    "obligations."
)

checker, CHECKER_BYTES = load_exact_module(
    CHECKER_PATH,
    "lean_exact_log_product_checker",
    EXPECTED_CHECKER_SHA256,
)


def reject_constant(token: str) -> NoReturn:
    fail(f"non-finite JSON token: {token}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key!r}")
        value[key] = item
    return value


def parse_one_json_object(raw: str, role: str) -> dict[str, Any]:
    require(raw.endswith("\n"), f"{role} lacks one final newline")
    require("\r" not in raw, f"{role} contains a carriage return")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, MutationError) as error:
        fail(f"{role} is not strict JSON: {error}")
    require(isinstance(value, dict), f"{role} is not a JSON object")
    require(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" == raw,
        f"{role} is not compact canonical JSON",
    )
    return value


def run_checker(
    source: Path,
    expected_digest: str,
    *,
    theorem_inventory: tuple[str, ...] | None = None,
) -> tuple[int, str, str]:
    """Invoke the captured checker and restore every mutable production global."""

    original_source = checker.SOURCE
    original_digest = checker.EXPECTED_SOURCE_SHA256
    original_theorems = checker.THEOREMS
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        checker.SOURCE = source
        checker.EXPECTED_SOURCE_SHA256 = expected_digest
        if theorem_inventory is not None:
            checker.THEOREMS = theorem_inventory
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = checker.main()
    finally:
        checker.SOURCE = original_source
        checker.EXPECTED_SOURCE_SHA256 = original_digest
        checker.THEOREMS = original_theorems
    require(checker.SOURCE == original_source, "checker source global was not restored")
    require(
        checker.EXPECTED_SOURCE_SHA256 == original_digest,
        "checker digest global was not restored",
    )
    require(
        checker.THEOREMS == original_theorems,
        "checker theorem inventory was not restored",
    )
    require(isinstance(result, int), "checker returned a non-integer status")
    return result, stdout.getvalue(), stderr.getvalue()


def replace_once(text: str, before: str, after: str, name: str) -> str:
    require(text.count(before) == 1, f"mutation anchor is absent or ambiguous: {name}")
    return text.replace(before, after, 1)


def introduce_unpermitted_axiom_dependency(text: str) -> str:
    changed = replace_once(
        text,
        "/-- The retained five-term empirical witness",
        "set_option warningAsError false in\n"
        "/-- The retained five-term empirical witness",
        "unpermitted_axiom_warning_scope",
    )
    return replace_once(
        changed,
        "  norm_num\n\nend PidExactLogProduct",
        "  exact sorryAx _ true\n\nend PidExactLogProduct",
        "unpermitted_axiom_dependency",
    )


def append_before_namespace_end(text: str, addition: str, name: str) -> str:
    return replace_once(
        text,
        "\nend PidExactLogProduct",
        addition + "\nend PidExactLogProduct",
        name,
    )


def require_rejection(
    *,
    name: str,
    status: int,
    stdout: str,
    stderr: str,
    expected_fragment: str,
) -> dict[str, object]:
    require(status == 1, f"{name} returned {status}, not exact rejection status 1")
    require(stdout == "", f"{name} emitted unexpected stdout: {stdout!r}")
    require(
        stderr.startswith("Lean exact-log-product check failed: ")
        and stderr.endswith("\n")
        and expected_fragment in stderr,
        f"{name} was rejected for the wrong reason: {stderr!r}",
    )
    return {
        "name": name,
        "rejected": True,
        "rejection_fragment": expected_fragment,
    }


def validate_checker_output(
    value: dict[str, Any],
    *,
    role: str,
    expected_source_sha256: str,
    expected_theorem_count: int,
) -> None:
    require(set(value) == EXPECTED_CHECKER_OUTPUT_KEYS, f"{role} key inventory")
    require(
        value.get("schema") == "pid-rs/lean-exact-log-product-check/v1",
        f"{role} schema",
    )
    require(value.get("status") == "passed", f"{role} status")
    require(
        value.get("source_sha256") == expected_source_sha256,
        f"{role} source digest",
    )
    require(
        value.get("checker_source_sha256") == EXPECTED_CHECKER_SHA256,
        f"{role} checker digest",
    )
    require(
        value.get("lake_manifest_sha256")
        == "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af",
        f"{role} Lake manifest digest",
    )
    require(
        value.get("lean_toolchain") == "leanprover/lean4:v4.33.0",
        f"{role} toolchain",
    )
    lean_version = value.get("lean_version")
    require(isinstance(lean_version, str), f"{role} Lean version type")
    require("version 4.33.0" in lean_version, f"{role} Lean version")
    require(
        "commit d8b18978322de05a8f3dba51ef03cf5461676c17" in lean_version,
        f"{role} Lean commit",
    )
    require(lean_version.endswith(", Release)"), f"{role} Lean build")
    require(
        value.get("theorems_kernel_checked") == expected_theorem_count,
        f"{role} theorem count",
    )
    require(
        value.get("permitted_axioms") == ["propext", "Classical.choice", "Quot.sound"],
        f"{role} permitted axiom inventory",
    )
    require(
        value.get("boundary") == EXPECTED_BOUNDARY,
        f"{role} boundary",
    )


def main() -> int:
    loaded_module_name = checker.__name__
    try:
        require(
            checker.THEOREMS == EXPECTED_THEOREMS, "production theorem list drifted"
        )
        source_bytes = stable_read(SOURCE_PATH, "Lean exact-log-product source")
        require(
            sha256_bytes(source_bytes) == EXPECTED_SOURCE_SHA256, "Lean source drifted"
        )
        source_text = source_bytes.decode("utf-8", errors="strict")
        baseline_status, baseline_stdout, baseline_stderr = run_checker(
            SOURCE_PATH,
            EXPECTED_SOURCE_SHA256,
        )
        require(baseline_status == 0, f"baseline checker failed: {baseline_stderr}")
        require(baseline_stderr == "", f"baseline checker stderr: {baseline_stderr!r}")
        baseline_value = parse_one_json_object(
            baseline_stdout,
            "baseline checker output",
        )
        validate_checker_output(
            baseline_value,
            role="baseline",
            expected_source_sha256=EXPECTED_SOURCE_SHA256,
            expected_theorem_count=7,
        )

        semantic_mutations: tuple[tuple[str, Callable[[str], str], str], ...] = (
            (
                "replace_log_zpow_with_log_pow",
                lambda text: replace_once(
                    text,
                    "Real.log_zpow (argument i) (exponent i)",
                    "Real.log_pow (argument i) (exponent i)",
                    "replace_log_zpow_with_log_pow",
                ),
                "Lean kernel check failed",
            ),
            (
                "reverse_positive_product_order",
                lambda text: replace_once(
                    text,
                    "0 < (1 / (n : ℝ)) * Real.log product ↔ 1 < product := by",
                    "0 < (1 / (n : ℝ)) * Real.log product ↔ product < 1 := by",
                    "reverse_positive_product_order",
                ),
                "Lean kernel check failed",
            ),
            (
                "reverse_negative_product_order",
                lambda text: replace_once(
                    text,
                    "(1 / (n : ℝ)) * Real.log product < 0 ↔ product < 1 := by",
                    "(1 / (n : ℝ)) * Real.log product < 0 ↔ 1 < product := by",
                    "reverse_negative_product_order",
                ),
                "Lean kernel check failed",
            ),
            (
                "remove_negative_one_exclusion",
                lambda text: replace_once(
                    text,
                    "    · exact hproduct_one\n    · linarith\n",
                    "    · exact hproduct_one\n    · exact hproduct_neg_one\n",
                    "remove_negative_one_exclusion",
                ),
                "Lean kernel check failed",
            ),
            (
                "negate_nonsyntactic_cancellation",
                lambda text: replace_once(
                    text,
                    "Real.log x + Real.log x⁻¹ = 0 ∧ 0 < x⁻¹ ∧ x ≠ 1 ∧ x⁻¹ ≠ 1 := by",
                    "Real.log x + Real.log x⁻¹ ≠ 0 ∧ 0 < x⁻¹ ∧ x ≠ 1 ∧ x⁻¹ ≠ 1 := by",
                    "negate_nonsyntactic_cancellation",
                ),
                "Lean kernel check failed",
            ),
            (
                "falsify_retained_product",
                lambda text: replace_once(
                    text,
                    "(8 / 15 : ℚ)⁻¹ * (4 / 5 : ℚ) * (8 / 9 : ℚ) * (4 / 3 : ℚ) * (16 / 9 : ℚ)⁻¹ = 1 := by",
                    "(8 / 15 : ℚ)⁻¹ * (4 / 5 : ℚ) * (8 / 9 : ℚ) * (4 / 3 : ℚ) * (16 / 9 : ℚ)⁻¹ = 2 := by",
                    "falsify_retained_product",
                ),
                "Lean kernel check failed",
            ),
            (
                "remove_zero_product_positivity_premise",
                lambda text: replace_once(
                    text,
                    "theorem scaled_log_eq_zero_iff {product : ℝ} {n : ℕ}\n"
                    "    (hproduct : 0 < product) (hn : 0 < n) :",
                    "theorem scaled_log_eq_zero_iff {product : ℝ} {n : ℕ}\n"
                    "    (hn : 0 < n) :",
                    "remove_zero_product_positivity_premise",
                ),
                "Lean kernel check failed",
            ),
            (
                "rename_checked_theorem",
                lambda text: replace_once(
                    text,
                    "theorem scaled_log_neg_iff",
                    "theorem scaled_log_negative_iff",
                    "rename_checked_theorem",
                ),
                "Lean kernel check failed",
            ),
            (
                "unpermitted_axiom_dependency",
                introduce_unpermitted_axiom_dependency,
                "Lean theorem axiom inventory changed",
            ),
        )
        raw_policy_mutations: tuple[tuple[str, Callable[[str], str], str], ...] = (
            (
                "inject_sorry",
                lambda text: replace_once(
                    text,
                    "  norm_num\n\nend PidExactLogProduct",
                    "  sorry\n\nend PidExactLogProduct",
                    "inject_sorry",
                ),
                "prohibited proof escape",
            ),
            (
                "inject_axiom",
                lambda text: replace_once(
                    text,
                    "theorem retained_five_term_product_eq_one :",
                    "axiom retained_five_term_product_eq_one :",
                    "inject_axiom",
                ),
                "prohibited proof escape",
            ),
            (
                "character_literal_masker_live_axiom_regression",
                lambda text: append_before_namespace_end(
                    text,
                    "\ndef quoteCharOne : Char := '\"'\n"
                    "axiom unexpected_unqueried_axiom : False\n"
                    'def emptyString : String := ""\n'
                    "def quoteCharTwo : Char := '\"'\n",
                    "character_literal_masker_live_axiom_regression",
                ),
                "prohibited proof escape",
            ),
        )
        results: list[dict[str, object]] = []
        raw_results: list[dict[str, object]] = []
        scope_probes: list[dict[str, object]] = []
        limitations: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(
            prefix="pid-exact-log-product-hostile-"
        ) as raw_directory:
            directory = Path(raw_directory)
            for index, (name, mutate, expected_fragment) in enumerate(
                semantic_mutations
            ):
                mutant_text = mutate(source_text)
                mutant = directory / f"SemanticMutation{index}.lean"
                mutant.write_text(mutant_text, encoding="utf-8")
                mutant_digest = sha256_bytes(mutant_text.encode("utf-8"))
                status, stdout, stderr = run_checker(mutant, mutant_digest)
                result = require_rejection(
                    name=name,
                    status=status,
                    stdout=stdout,
                    stderr=stderr,
                    expected_fragment=expected_fragment,
                )
                result["mutant_sha256"] = mutant_digest
                results.append(result)

            for index, (name, mutate, expected_fragment) in enumerate(
                raw_policy_mutations
            ):
                mutant_text = mutate(source_text)
                mutant = directory / f"RawPolicyMutation{index}.lean"
                mutant.write_text(mutant_text, encoding="utf-8")
                mutant_digest = sha256_bytes(mutant_text.encode("utf-8"))
                status, stdout, stderr = run_checker(mutant, mutant_digest)
                result = require_rejection(
                    name=name,
                    status=status,
                    stdout=stdout,
                    stderr=stderr,
                    expected_fragment=expected_fragment,
                )
                result["mutant_sha256"] = mutant_digest
                raw_results.append(result)

            extra_lemma_text = append_before_namespace_end(
                source_text,
                "\nlemma unexpected_extra_lemma : True := by trivial\n",
                "extra_lemma_scope_probe",
            )
            extra_lemma = directory / "ExtraLemma.lean"
            extra_lemma.write_text(extra_lemma_text, encoding="utf-8")
            extra_lemma_digest = sha256_bytes(extra_lemma_text.encode("utf-8"))
            status, stdout, stderr = run_checker(
                extra_lemma,
                EXPECTED_SOURCE_SHA256,
            )
            digest_result = require_rejection(
                name="extra_lemma_without_digest_rebind",
                status=status,
                stdout=stdout,
                stderr=stderr,
                expected_fragment="source digest drifted",
            )
            digest_result["mutant_sha256"] = extra_lemma_digest
            raw_results.append(digest_result)

            status, stdout, stderr = run_checker(extra_lemma, extra_lemma_digest)
            require(status == 0, "rebound extra-lemma scope probe was not accepted")
            require(stderr == "", f"rebound extra-lemma stderr: {stderr!r}")
            extra_value = parse_one_json_object(stdout, "rebound extra-lemma output")
            validate_checker_output(
                extra_value,
                role="rebound extra-lemma",
                expected_source_sha256=extra_lemma_digest,
                expected_theorem_count=7,
            )
            scope_probes.append(
                {
                    "accepted": True,
                    "meaning": (
                        "After a deliberate test-only digest rebind, an unrelated lemma is "
                        "outside the seven-name axiom audit. Production acceptance remains "
                        "closed by the immutable source digest."
                    ),
                    "mutant_sha256": extra_lemma_digest,
                    "name": "extra_lemma_with_digest_rebind",
                }
            )

            private_theorem_text = append_before_namespace_end(
                source_text,
                "\nprivate theorem unexpected_private_theorem : True := by trivial\n",
                "private_theorem_scope_probe",
            )
            private_theorem = directory / "PrivateTheorem.lean"
            private_theorem.write_text(private_theorem_text, encoding="utf-8")
            private_theorem_digest = sha256_bytes(private_theorem_text.encode("utf-8"))
            status, stdout, stderr = run_checker(
                private_theorem,
                EXPECTED_SOURCE_SHA256,
            )
            digest_result = require_rejection(
                name="private_theorem_without_digest_rebind",
                status=status,
                stdout=stdout,
                stderr=stderr,
                expected_fragment="source digest drifted",
            )
            digest_result["mutant_sha256"] = private_theorem_digest
            raw_results.append(digest_result)

            status, stdout, stderr = run_checker(
                private_theorem,
                private_theorem_digest,
            )
            require(status == 0, "rebound private-theorem scope probe was not accepted")
            require(stderr == "", f"rebound private-theorem stderr: {stderr!r}")
            private_value = parse_one_json_object(
                stdout,
                "rebound private-theorem output",
            )
            validate_checker_output(
                private_value,
                role="rebound private-theorem",
                expected_source_sha256=private_theorem_digest,
                expected_theorem_count=7,
            )
            scope_probes.append(
                {
                    "accepted": True,
                    "meaning": (
                        "After a deliberate test-only digest rebind, an unrelated private "
                        "theorem is outside the seven-name axiom audit. Production acceptance "
                        "remains closed by the immutable source digest."
                    ),
                    "mutant_sha256": private_theorem_digest,
                    "name": "private_theorem_with_digest_rebind",
                }
            )

            comment_decoy_text = (
                source_text
                + r"""

/- A nested comment /- sorry -/ containing admit, axiom, and unsafe is not live Lean code. -/
def exactLogProductProofEscapeDecoy : String :=
  "sorry admit axiom unsafe with an escaped quote: \""
"""
            )
            comment_decoy = directory / "CommentStringDecoy.lean"
            comment_decoy.write_text(comment_decoy_text, encoding="utf-8")
            comment_decoy_digest = sha256_bytes(comment_decoy_text.encode("utf-8"))
            status, stdout, stderr = run_checker(comment_decoy, comment_decoy_digest)
            decoy_result = require_rejection(
                name="comment_string_decoy_raw_fail_closed_policy",
                status=status,
                stdout=stdout,
                stderr=stderr,
                expected_fragment="prohibited proof escape",
            )
            decoy_result["mutant_sha256"] = comment_decoy_digest
            raw_results.append(decoy_result)

            shortened = EXPECTED_THEOREMS[:-1]
            status, stdout, stderr = run_checker(
                SOURCE_PATH,
                EXPECTED_SOURCE_SHA256,
                theorem_inventory=shortened,
            )
            require(status == 0, "shortened inventory limitation probe changed")
            require(stderr == "", f"shortened inventory stderr: {stderr!r}")
            shortened_value = parse_one_json_object(
                stdout,
                "shortened theorem-inventory limitation output",
            )
            validate_checker_output(
                shortened_value,
                role="shortened theorem-inventory limitation",
                expected_source_sha256=EXPECTED_SOURCE_SHA256,
                expected_theorem_count=6,
            )
            limitations.append(
                {
                    "accepted": True,
                    "meaning": (
                        "The frozen checker has no internal immutable copy of its theorem list. "
                        "Its exact checker-byte custody is therefore a separate required guard."
                    ),
                    "name": "same_process_theorem_inventory_removal",
                    "theorem_count_observed": 6,
                }
            )

        require(len(results) == 9, "semantic mutation inventory changed")
        require(len(raw_results) == 6, "raw/digest policy inventory changed")
        require(len(scope_probes) == 2, "scope-probe inventory changed")
        require(len(limitations) == 1, "known-limitation inventory changed")
        require(
            checker.THEOREMS == EXPECTED_THEOREMS,
            "production theorem inventory changed after hostile replay",
        )
        require(
            stable_read(CHECKER_PATH, "post-replay exact-log checker") == CHECKER_BYTES,
            "production checker bytes changed during hostile replay",
        )
        require(
            stable_read(SOURCE_PATH, "post-replay exact-log source") == source_bytes,
            "Lean source bytes changed during hostile replay",
        )
        self_bytes = stable_read(SELF_PATH, "exact-log hostile self-test")
        evidence = {
            "baseline_checker_passed": True,
            "boundary": (
                "This isolated suite establishes bounded sensitivity of the frozen checker to "
                "nine theorem/premise mutations, six separately counted raw-source or digest "
                "controls, two explicit scope probes, and one retained checker-custody "
                "limitation. It does not prove checker correctness, complete Lean syntax "
                "classification, concrete SxPID event extraction, Rust or binary64 refinement, "
                "sampling validity, calibration, or scientific validity."
            ),
            "case_accounting": {
                "accepted_known_limitations": len(limitations),
                "accepted_positive_cases": 1 + len(scope_probes),
                "accepted_scope_probes": len(scope_probes),
                "baseline_cases": 1,
                "rejected_raw_or_digest_policy_cases": len(raw_results),
                "rejected_semantic_mutations": len(results),
                "total_cases": (
                    1
                    + len(results)
                    + len(raw_results)
                    + len(scope_probes)
                    + len(limitations)
                ),
            },
            "checker_source_sha256": EXPECTED_CHECKER_SHA256,
            "known_limitations": limitations,
            "known_limitations_observed": len(limitations),
            "lake_manifest_sha256": baseline_value["lake_manifest_sha256"],
            "lean_toolchain": baseline_value["lean_toolchain"],
            "lean_version": baseline_value["lean_version"],
            "positive_cases_accepted": 1 + len(scope_probes),
            "mutations": results,
            "mutations_killed": len(results),
            "python_isolated": True,
            "raw_and_digest_policy_cases": raw_results,
            "raw_and_digest_policy_cases_rejected": len(raw_results),
            "schema": "pid-rs/lean-exact-log-product-hostile/v1",
            "scope_probes": scope_probes,
            "scope_probes_accepted": len(scope_probes),
            "self_test_source_sha256": sha256_bytes(self_bytes),
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "status": "passed",
        }
        evidence_bytes = (
            json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        require(
            stable_read(EVIDENCE_PATH, "tracked hostile evidence") == evidence_bytes,
            "tracked hostile evidence differs from the complete canonical run record",
        )
        sys.stdout.write(evidence_bytes.decode("utf-8"))
        return 0
    except (OSError, UnicodeError, ValueError, MutationError) as error:
        print(f"Lean exact-log-product self-test failed: {error}", file=sys.stderr)
        return 1
    finally:
        sys.modules.pop(loaded_module_name, None)


if __name__ == "__main__":
    raise SystemExit(main())
