#!/usr/bin/env python3
"""Qualification and fail-closed mutation suite for the independent certificate verifier."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, cast

SCRIPT_DIR = Path(__file__).resolve().parent
CERTIFIER_ROOT = SCRIPT_DIR.parent
REPOSITORY_ROOT = CERTIFIER_ROOT.parents[2]
VERIFIER_PATH = SCRIPT_DIR / "verify_certificate.py"


def load_verifier_source(path: Path, module_name: str) -> Any:
    """Compile and execute the exact source bytes without consulting a bytecode cache."""

    source = path.read_bytes()
    code = compile(
        source,
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    module.__loader__ = None
    module.__package__ = ""
    module.__spec__ = importlib.util.spec_from_loader(
        module_name, loader=None, origin=str(path)
    )
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_verifier() -> Any:
    return load_verifier_source(
        VERIFIER_PATH, "pid_certified_sxpid_independent_verifier"
    )


VERIFIER = load_verifier()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_verification_error(
    name: str, action: Callable[[], Any], message_fragment: str | None = None
) -> None:
    try:
        action()
    except VERIFIER.VerificationError as error:
        if message_fragment is not None and message_fragment not in str(error):
            raise AssertionError(
                f"invalid case {name!r} failed for the wrong reason: {error}"
            ) from error
        return
    raise AssertionError(f"independent verifier accepted invalid case {name!r}")


def canonical_input(rows: list[dict[str, Any]]) -> bytes:
    document = {
        "schema": VERIFIER.INPUT_SCHEMA,
        "definition_revision": VERIFIER.DEFINITION_REVISION,
        "units": VERIFIER.UNITS,
        "resource_policy_id": VERIFIER.RESOURCE_POLICY_ID,
        "rows": rows,
    }
    return cast(bytes, VERIFIER.canonical_json_bytes(document))


def row(source_one: str, source_two: str, target: str, count: int) -> dict[str, Any]:
    return {
        "source_states": [[source_one], [source_two]],
        "target_state": [target],
        "count": str(count),
    }


def run_certifier(input_raw: bytes) -> bytes:
    environment = dict(os.environ)
    environment.setdefault(
        "CARGO_TARGET_DIR", str(REPOSITORY_ROOT / "target" / "certified-sxpid")
    )
    command = [
        "cargo",
        "run",
        "--quiet",
        "--locked",
        "--manifest-path",
        str(CERTIFIER_ROOT / "Cargo.toml"),
        "--",
        "-",
    ]
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        input=input_raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "certifier failed during independent-verifier qualification: "
            + completed.stderr.decode("utf-8", errors="replace")
        )
    return bytes(completed.stdout)


def run_verifier_cli(
    input_raw: bytes,
    certificate_raw: bytes,
    *,
    environment_overrides: dict[str, str] | None = None,
) -> tuple[int, bytes, bytes]:
    environment = dict(os.environ)
    if environment_overrides:
        environment.update(environment_overrides)
    with tempfile.TemporaryDirectory(prefix="pid-sxpid-verifier-") as directory:
        root = Path(directory)
        input_path = root / "input.json"
        certificate_path = root / "certificate.json"
        input_path.write_bytes(input_raw)
        certificate_path.write_bytes(certificate_raw)
        completed = subprocess.run(
            [
                sys.executable,
                str(VERIFIER_PATH),
                str(input_path),
                str(certificate_path),
                "--certifier-root",
                str(CERTIFIER_ROOT),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    return completed.returncode, bytes(completed.stdout), bytes(completed.stderr)


def parse_certificate(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("certifier output is not an object")
    return cast(dict[str, Any], value)


def reseal(certificate: dict[str, Any]) -> bytes:
    certificate["payload_sha256"] = VERIFIER.canonical_digest(certificate["payload"])
    return cast(bytes, VERIFIER.canonical_json_bytes(certificate))


def expect_rejection(
    name: str,
    input_raw: bytes,
    certificate: dict[str, Any],
    mutation: Callable[[dict[str, Any]], None],
    intended_error: str | Callable[[str], bool],
) -> None:
    mutant = copy.deepcopy(certificate)
    mutation(mutant)
    mutant_raw = reseal(mutant)
    try:
        VERIFIER.verify_certificate(input_raw, mutant_raw, CERTIFIER_ROOT)
    except VERIFIER.VerificationError as error:
        message = str(error)
        if isinstance(intended_error, str):
            accepted_failure = intended_error in message
        else:
            accepted_failure = intended_error(message)
        require(
            accepted_failure,
            f"mutation {name!r} failed outside its intended path: {message}",
        )
        return
    raise AssertionError(f"independent verifier accepted mutation {name!r}")


def find_nonzero_coordinate(certificate: dict[str, Any]) -> dict[str, Any]:
    for coordinate in certificate["payload"]["coordinates"]:
        if coordinate["exact_terms"]:
            return cast(dict[str, Any], coordinate)
    raise AssertionError("qualification certificate has no nonzero coordinate")


def find_certified_positive_coordinate(certificate: dict[str, Any]) -> dict[str, Any]:
    for coordinate in certificate["payload"]["coordinates"]:
        if coordinate["interval"]["decision"] == "certified_positive":
            return cast(dict[str, Any], coordinate)
    raise AssertionError("qualification certificate has no certified-positive coordinate")


def mutation_interval_collapses_to_false_zero(certificate: dict[str, Any]) -> None:
    coordinate = find_nonzero_coordinate(certificate)
    coordinate["interval"]["lower"] = {"significand": "0", "exponent2": 0}
    coordinate["interval"]["upper"] = {"significand": "0", "exponent2": 0}
    coordinate["interval"]["decision"] = "unresolved_sign"
    coordinate["interval"]["exact_zero_witness"] = None


def mutation_interval_collapses_to_own_lower_endpoint(
    certificate: dict[str, Any],
) -> None:
    coordinate = find_certified_positive_coordinate(certificate)
    coordinate["interval"]["upper"] = copy.deepcopy(coordinate["interval"]["lower"])


def mutation_reported_expression_changes(certificate: dict[str, Any]) -> None:
    coordinate = find_nonzero_coordinate(certificate)
    coordinate["exact_terms"][0]["coefficient"]["numerator"] = "37"
    coordinate["expression_sha256"] = VERIFIER.canonical_digest(
        coordinate["exact_terms"]
    )
    digest_items = [
        {"identity": item["identity"], "exact_terms": item["exact_terms"]}
        for item in certificate["payload"]["coordinates"]
    ]
    certificate["payload"]["exact_expression"]["coordinates_sha256"] = (
        VERIFIER.canonical_digest(digest_items)
    )


def mutation_redundancy_union_becomes_joint(certificate: dict[str, Any]) -> None:
    lattice = certificate["payload"]["lattice"]
    lattice["value"]["cumulative_node_order"][3]["source_collection_masks"] = [3]
    lattice["sha256"] = VERIFIER.canonical_digest(lattice["value"])


def mutation_noncanonical_dyadic(certificate: dict[str, Any]) -> None:
    coordinate = certificate["payload"]["coordinates"][0]
    coordinate["interval"]["lower"] = {"significand": "0", "exponent2": -7}


def mutation_sign_decision(certificate: dict[str, Any]) -> None:
    coordinate = find_nonzero_coordinate(certificate)
    coordinate["interval"]["decision"] = "certified_exact_zero"


def mutation_coordinate_identity(certificate: dict[str, Any]) -> None:
    certificate["payload"]["coordinates"][0]["identity"]["node"] = "joint_sources"


def mutation_source_manifest(certificate: dict[str, Any]) -> None:
    certificate["payload"]["tool_binding"]["runtime_source_manifest_sha256"] = "0" * 64


def mutation_target_width_flag(certificate: dict[str, Any]) -> None:
    certificate["payload"]["coordinates"][0]["interval"]["target_width_met"] = False


def mutation_precision_trace(certificate: dict[str, Any]) -> None:
    certificate["payload"]["coordinates"][0]["interval"]["precision_iterations"] = 1


def mutation_extreme_dyadic_exponent(certificate: dict[str, Any]) -> None:
    coordinate = find_nonzero_coordinate(certificate)
    coordinate["interval"]["lower"] = {"significand": "-1", "exponent2": -65_537}


def mutation_exact_term_resource_count(certificate: dict[str, Any]) -> None:
    resource_use = certificate["payload"]["exact_expression"]["resource_use"]
    resource_use["total_exact_terms"] += 1


def mutation_exact_term_estimated_bytes(certificate: dict[str, Any]) -> None:
    resource_use = certificate["payload"]["exact_expression"]["resource_use"]
    resource_use["estimated_exact_term_json_bytes_upper_bound"] += 1


def mutation_numeric_evidence_bool(certificate: dict[str, Any]) -> None:
    certificate["payload"]["input"]["target_state_width"] = True


def mutation_lattice_integer_bool(certificate: dict[str, Any]) -> None:
    lattice = certificate["payload"]["lattice"]
    lattice["value"]["mobius_atom_from_cumulative"][0][0] = True
    lattice["sha256"] = VERIFIER.canonical_digest(lattice["value"])


def mutation_permitted_claim(certificate: dict[str, Any]) -> None:
    certificate["payload"]["claim_boundary"]["permitted_claim"] += " Broader."


def mutation_arithmetic_status(certificate: dict[str, Any]) -> None:
    certificate["payload"]["arithmetic"]["runtime_native_version_probe"] = "performed"


def mutation_build_context_scope(certificate: dict[str, Any]) -> None:
    certificate["payload"]["tool_binding"]["build_context"]["context_scope"] = (
        "exhaustive_build_context"
    )


def mutation_distribution_route(certificate: dict[str, Any]) -> None:
    certificate["payload"]["tool_binding"]["project_distribution_route"] = (
        "verified_binary_distribution"
    )


def mutation_build_host(certificate: dict[str, Any]) -> None:
    certificate["payload"]["tool_binding"]["build_context"]["build_host"] = (
        "forged-qualification-host"
    )


def exact_atanh_reference_enclosure(
    reduced: Fraction, bits: int
) -> tuple[Fraction, Fraction]:
    """Return an exact-Fraction enclosure independent of the fixed-point implementation."""

    require(
        Fraction(1) <= reduced <= Fraction(2),
        "exact atanh reference requires a reduced argument in [1,2]",
    )
    if reduced == 1:
        return (Fraction(0), Fraction(0))

    z = (reduced - 1) / (reduced + 1)
    z_squared = z * z
    power = z
    partial = Fraction(0)
    target_tail_width = Fraction(1, 1 << (bits + 32))
    for index in range(1024):
        odd = 2 * index + 1
        partial += Fraction(2, odd) * power
        power *= z_squared
        next_odd = odd + 2
        # For 0 <= z <= 1/3, the omitted positive series is bounded by
        #
        #   2 z^(2m+1) / ((2m+1)(1-z^2))
        #       <= 9 z^(2m+1) / (4(2m+1)).
        #
        # Every operation here is exact Fraction arithmetic and independent of
        # the verifier's fixed-point rounding implementation.
        tail_upper = Fraction(9, 4 * next_odd) * power
        if tail_upper <= target_tail_width:
            return (partial, partial + tail_upper)
    raise AssertionError(
        "exact-Fraction atanh reference did not reach its target width"
    )


def check_exact_fraction_log_enclosures(verifier: Any) -> int:
    """Require fixed-point intervals to contain a separately evaluated rational enclosure."""

    reduced_grid = sorted(
        {
            Fraction(numerator, denominator)
            for denominator in range(1, 33)
            for numerator in range(denominator, 2 * denominator + 1)
        }
    )
    cases = 0
    for bits in (64, 128, 256):
        scale = 1 << bits
        for reduced in reduced_grid:
            lower_units, upper_units = verifier._atanh_log_reduced_interval(
                reduced, bits
            )
            reference_lower, reference_upper = exact_atanh_reference_enclosure(
                reduced, bits
            )
            require(
                Fraction(lower_units, scale) <= reference_lower,
                "fixed-point atanh lower endpoint exceeds the exact-Fraction "
                f"partial sum at reduced={reduced}, bits={bits}",
            )
            require(
                reference_upper <= Fraction(upper_units, scale),
                "fixed-point atanh upper endpoint misses the exact-Fraction "
                f"series-and-tail enclosure at reduced={reduced}, bits={bits}",
            )
            cases += 1
    return cases


def check_unsound_log_source_mutation() -> int:
    """Prove that a small source-level erosion of the ln(2) upper bound is detected."""

    original = VERIFIER_PATH.read_text(encoding="utf-8")
    sound_fragment = (
        "    upper += _ceil_fraction_units(9 * power_upper, 4 * next_odd)\n"
        "    return (lower, upper)\n"
    )
    unsound_fragment = (
        "    upper += _ceil_fraction_units(9 * power_upper, 4 * next_odd)\n"
        "    if reduced == 2:\n"
        "        upper -= 70\n"
        "    return (lower, upper)\n"
    )
    require(
        original.count(sound_fragment) == 1,
        "cannot locate the unique fixed-point atanh return site for mutation",
    )

    with tempfile.TemporaryDirectory(
        prefix="pid-sxpid-log-verifier-mutation-"
    ) as directory:
        mutant_path = Path(directory) / "verify_certificate.py"
        mutant_path.write_text(
            original.replace(sound_fragment, unsound_fragment),
            encoding="utf-8",
        )
        module_name = "pid_certified_sxpid_unsound_log_mutant"
        mutant = load_verifier_source(mutant_path, module_name)
        try:
            try:
                check_exact_fraction_log_enclosures(mutant)
            except AssertionError as error:
                require(
                    "upper endpoint misses the exact-Fraction series-and-tail enclosure"
                    in str(error),
                    f"unsound log mutant failed for the wrong reason: {error}",
                )
            else:
                raise AssertionError(
                    "exact-Fraction qualification accepted the unsound log mutant"
                )
        finally:
            sys.modules.pop(module_name, None)
    return 1


def load_verifier_copy(path: Path, module_name: str) -> Any:
    return load_verifier_source(path, module_name)


def check_post_import_source_mutation(input_raw: bytes, certificate_raw: bytes) -> int:
    """Require the live verifier to reject replacement of its source after import."""

    with tempfile.TemporaryDirectory(
        prefix="pid-sxpid-verifier-source-drift-"
    ) as directory:
        verifier_copy = Path(directory) / "verify_certificate.py"
        original = VERIFIER_PATH.read_bytes()
        verifier_copy.write_bytes(original)
        module_name = "pid_certified_sxpid_post_import_source_mutant"
        mutant = load_verifier_copy(verifier_copy, module_name)
        try:
            verifier_copy.write_bytes(
                original + b"\n# qualification-only post-import source replacement\n"
            )
            try:
                mutant.verify_certificate(input_raw, certificate_raw, CERTIFIER_ROOT)
            except mutant.VerificationError as error:
                require(
                    str(error)
                    == "independent verifier source changed after the module was loaded",
                    "post-import source mutation failed outside the intended "
                    f"integrity path: {error}",
                )
            else:
                raise AssertionError(
                    "verifier accepted source replacement after module import"
                )
        finally:
            sys.modules.pop(module_name, None)
    return 1


def check_cargo_semantic_binding_mutation(
    input_raw: bytes, certificate: dict[str, Any]
) -> int:
    """Require reviewed Cargo semantics, not only recomputed file hashes."""

    with tempfile.TemporaryDirectory(
        prefix="pid-sxpid-cargo-binding-mutation-"
    ) as directory:
        mutant_root = Path(directory)
        for relative in VERIFIER.SOURCE_MANIFEST_FILES:
            source = CERTIFIER_ROOT / relative
            destination = mutant_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())

        cargo_toml = mutant_root / "Cargo.toml"
        manifest_text = cargo_toml.read_text(encoding="utf-8")
        sound_version = 'version = "=1.30.0"'
        forged_version = 'version = "=9.99.9"'
        require(
            manifest_text.count(sound_version) == 1,
            "cannot locate the unique pinned Rug manifest version",
        )
        cargo_toml.write_text(
            manifest_text.replace(sound_version, forged_version),
            encoding="utf-8",
        )

        mutant = copy.deepcopy(certificate)
        tool_binding = mutant["payload"]["tool_binding"]
        tool_binding["runtime_source_manifest_sha256"] = (
            VERIFIER.source_manifest_digest(mutant_root)
        )
        tool_binding["cargo_lock_sha256"] = VERIFIER.sha256_hex(
            (mutant_root / "Cargo.lock").read_bytes()
        )
        mutant_raw = reseal(mutant)
        try:
            VERIFIER.verify_certificate(input_raw, mutant_raw, mutant_root)
        except VERIFIER.VerificationError as error:
            require(
                str(error)
                == "Cargo.toml Rug dependency against arithmetic evidence mismatch",
                "Cargo semantic-binding mutation failed outside the intended "
                f"manifest path: {error}",
            )
        else:
            raise AssertionError(
                "verifier accepted a rehashed Cargo manifest with a forged Rug version"
            )
    return 1


def _copy_certifier_manifest_files(destination_root: Path) -> None:
    for relative in VERIFIER.SOURCE_MANIFEST_FILES:
        source = CERTIFIER_ROOT / relative
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())


def _expect_rehashed_certifier_root_rejection(
    name: str,
    input_raw: bytes,
    certificate: dict[str, Any],
    mutate_root: Callable[[Path], None],
    intended_error: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"pid-sxpid-{name}-") as directory:
        mutant_root = Path(directory)
        _copy_certifier_manifest_files(mutant_root)
        mutate_root(mutant_root)
        mutant = copy.deepcopy(certificate)
        tool_binding = mutant["payload"]["tool_binding"]
        tool_binding["runtime_source_manifest_sha256"] = (
            VERIFIER.source_manifest_digest(mutant_root)
        )
        tool_binding["cargo_lock_sha256"] = VERIFIER.sha256_hex(
            (mutant_root / "Cargo.lock").read_bytes()
        )
        mutant_raw = reseal(mutant)
        try:
            VERIFIER.verify_certificate(input_raw, mutant_raw, mutant_root)
        except VERIFIER.VerificationError as error:
            require(
                intended_error in str(error),
                f"{name} failed outside its intended binding path: {error}",
            )
        else:
            raise AssertionError(f"verifier accepted {name}")


def check_cargo_patch_binding_mutation(
    input_raw: bytes, certificate: dict[str, Any]
) -> int:
    """Reject a source replacement even when report digests are self-consistently resealed."""

    def mutate(root: Path) -> None:
        manifest = root / "Cargo.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8")
            + '\n[patch.crates-io]\nrug = { path = "../qualification-only-rug" }\n',
            encoding="utf-8",
            newline="",
        )

    _expect_rehashed_certifier_root_rejection(
        "rehashed Cargo patch substitution",
        input_raw,
        certificate,
        mutate,
        "Cargo.toml [patch] source substitution is outside the reviewed arithmetic binding",
    )
    return 1


def check_cargo_lock_checksum_binding_mutation(
    input_raw: bytes, certificate: dict[str, Any]
) -> int:
    """Reject a forged locked package checksum after all outer digests are resealed."""

    expected = "07a8857882aec59d27254b02481c709327c13de6fad1da60bfc4f9783eaaa61e"

    def mutate(root: Path) -> None:
        lockfile = root / "Cargo.lock"
        text = lockfile.read_text(encoding="utf-8")
        require(
            text.count(expected) == 1,
            "cannot locate the unique locked Rug checksum",
        )
        lockfile.write_text(
            text.replace(expected, "0" * 64),
            encoding="utf-8",
            newline="",
        )

    _expect_rehashed_certifier_root_rejection(
        "rehashed Cargo.lock checksum substitution",
        input_raw,
        certificate,
        mutate,
        "Cargo.lock rug checksum against reviewed binding mismatch",
    )
    return 1


def check_posix_invalid_filename_cli() -> int:
    """Require invalid POSIX filename bytes to use the canonical rejection channel."""

    if os.name != "posix":
        return 0
    with tempfile.TemporaryDirectory(prefix="pid-sxpid-invalid-filename-") as directory:
        root = Path(directory)
        certificate_path = root / "certificate.json"
        certificate_path.write_bytes(b"{}")
        invalid_input_path = (
            os.fsencode(str(root)) + b"/missing-input-" + bytes((0xFF,)) + b".json"
        )
        completed = subprocess.run(
            [
                os.fsencode(sys.executable),
                os.fsencode(str(VERIFIER_PATH)),
                invalid_input_path,
                os.fsencode(str(certificate_path)),
                b"--certifier-root",
                os.fsencode(str(CERTIFIER_ROOT)),
            ],
            cwd=os.fsencode(str(REPOSITORY_ROOT)),
            env=dict(os.environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    require(
        completed.returncode == 2,
        "invalid POSIX filename byte did not return verifier rejection code 2",
    )
    require(
        completed.stderr == b"",
        "invalid POSIX filename byte leaked a traceback or stderr diagnostic",
    )
    rejection = VERIFIER.parse_json(
        bytes(completed.stdout), "invalid-filename CLI rejection"
    )
    require(
        set(rejection) == {"schema", "status", "message"}
        and rejection["schema"] == VERIFIER.VERIFICATION_SCHEMA
        and rejection["status"] == "rejected",
        "invalid POSIX filename byte did not produce the canonical rejection shape",
    )
    message = rejection["message"]
    require(
        isinstance(message, str)
        and "cannot read count table" in message
        and "\\udcff" in message,
        "invalid POSIX filename rejection did not preserve its intended escaped path",
    )
    require(
        completed.stdout == VERIFIER.canonical_json_bytes(rejection) + b"\n",
        "invalid POSIX filename rejection was not canonical JSON plus one newline",
    )
    return 1


def check_posix_symlink_invocation_cli(
    input_raw: bytes, certificate_raw: bytes
) -> int:
    """Require a symlinked script invocation to bind and execute the real source bytes."""

    if os.name != "posix":
        return 0
    with tempfile.TemporaryDirectory(prefix="pid-sxpid-symlink-cli-") as directory:
        root = Path(directory)
        verifier_link = root / "verify-certificate-link.py"
        verifier_link.symlink_to(VERIFIER_PATH)
        input_path = root / "input.json"
        certificate_path = root / "certificate.json"
        input_path.write_bytes(input_raw)
        certificate_path.write_bytes(certificate_raw)
        completed = subprocess.run(
            [
                sys.executable,
                str(verifier_link),
                str(input_path),
                str(certificate_path),
                "--certifier-root",
                str(CERTIFIER_ROOT),
            ],
            cwd=REPOSITORY_ROOT,
            env=dict(os.environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    require(
        completed.returncode == 0 and completed.stderr == b"",
        "symlinked verifier invocation did not use the normal success channel",
    )
    report = VERIFIER.parse_json(completed.stdout, "symlinked CLI result")
    require(
        report.get("status") == "verified",
        "symlinked verifier invocation did not produce a verified report",
    )
    return 1


def check_closed_stdout_cli(input_raw: bytes, certificate_raw: bytes) -> int:
    """Require a failed stdout write to return status 1 without a traceback."""

    if os.name != "posix":
        return 0
    with tempfile.TemporaryDirectory(prefix="pid-sxpid-closed-stdout-") as directory:
        root = Path(directory)
        input_path = root / "input.json"
        certificate_path = root / "certificate.json"
        input_path.write_bytes(input_raw)
        certificate_path.write_bytes(certificate_raw)
        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(VERIFIER_PATH),
                    str(input_path),
                    str(certificate_path),
                    "--certifier-root",
                    str(CERTIFIER_ROOT),
                ],
                cwd=REPOSITORY_ROOT,
                env=dict(os.environ),
                stdout=write_fd,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
        finally:
            os.close(write_fd)
    require(
        completed.returncode == 1,
        "closed verifier stdout did not return transport-failure status 1",
    )
    require(
        completed.stderr == b"",
        "closed verifier stdout leaked a traceback or stderr diagnostic",
    )
    return 1


def check_log_arithmetic() -> int:
    for numerator in range(1, 97):
        for denominator in range(1, 97):
            value = Fraction(numerator, denominator)
            exponent = VERIFIER._floor_log2_fraction(value)
            reduced = VERIFIER._scale_by_power_of_two(value, exponent)
            require(
                Fraction(1) <= reduced < Fraction(2),
                "log range reduction escaped [1,2)",
            )

    for bits in (64, 128, 256):
        ln2 = VERIFIER._atanh_log_reduced_interval(Fraction(2), bits)
        half = VERIFIER._log_unit_interval(Fraction(1, 2), bits, ln2)
        eight = VERIFIER._log_unit_interval(Fraction(8), bits, ln2)
        require(half == (-ln2[1], -ln2[0]), "ln(1/2) symmetry failed")
        require(eight == (3 * ln2[0], 3 * ln2[1]), "ln(8) scaling failed")
        scale = 1 << bits
        require(
            Fraction(69, 100) < Fraction(ln2[0], scale),
            "ln(2) lower enclosure is implausible",
        )
        require(
            Fraction(ln2[1], scale) < Fraction(7, 10),
            "ln(2) upper enclosure is implausible",
        )
    return check_exact_fraction_log_enclosures(VERIFIER)


def check_independent_extraction() -> None:
    singleton = canonical_input([row("a", "b", "t", 1)])
    singleton_coordinates = VERIFIER.reconstruct_coordinates(
        VERIFIER.validate_input(singleton)
    )
    require(
        len(singleton_coordinates) == 24,
        "singleton extraction did not produce 24 coordinates",
    )
    require(
        all(not coordinate.expression for coordinate in singleton_coordinates),
        "singleton extraction did not produce exact zero expressions",
    )

    xor = canonical_input(
        [
            row("0", "0", "0", 1),
            row("0", "1", "1", 1),
            row("1", "0", "1", 1),
            row("1", "1", "0", 1),
        ]
    )
    coordinates = VERIFIER.reconstruct_coordinates(VERIFIER.validate_input(xor))
    by_identity = {
        (coordinate.kind, coordinate.node, coordinate.component): coordinate.expression
        for coordinate in coordinates
    }
    require(
        by_identity[("cumulative", "joint_sources", "net")]
        == {Fraction(2): Fraction(1)},
        "XOR joint-source cumulative expression is wrong",
    )
    require(
        by_identity[("cumulative", "source_one", "net")] == {},
        "XOR source-one self-redundancy expression is not zero",
    )
    require(
        by_identity[("cumulative", "source_two", "net")] == {},
        "XOR source-two self-redundancy expression is not zero",
    )
    require(
        by_identity[("cumulative", "redundancy", "net")]
        == {Fraction(2, 3): Fraction(1)},
        "XOR redundancy-union expression is wrong",
    )
    require(
        by_identity[("cumulative", "joint_sources", "net")]
        != by_identity[("cumulative", "redundancy", "net")],
        "joint and redundancy events collapsed",
    )


def check_structural_rejections() -> int:
    executed = 0
    expect_verification_error(
        "duplicate_json_key",
        lambda: VERIFIER.parse_json(b'{"a":1,"a":2}', "duplicate-key fixture"),
        "duplicate JSON object key",
    )
    executed += 1
    surrogate_document = {
        "schema": VERIFIER.INPUT_SCHEMA,
        "definition_revision": VERIFIER.DEFINITION_REVISION,
        "units": VERIFIER.UNITS,
        "resource_policy_id": VERIFIER.RESOURCE_POLICY_ID,
        "rows": [
            {
                "source_states": [["\ud800"], ["b"]],
                "target_state": ["t"],
                "count": "1",
            }
        ],
    }
    surrogate_raw = json.dumps(
        surrogate_document, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    expect_verification_error(
        "lone_unicode_surrogate",
        lambda: VERIFIER.validate_input(surrogate_raw),
        "canonical ASCII state token",
    )
    executed += 1

    # This table previously reconstructed 1,640 cumulative terms even though the Rust certifier
    # rejects it at the pinned 1,638-term extraction ceiling.
    growth_rows = [
        row(f"s{index:04d}", "constant", "constant", index + 1) for index in range(410)
    ]
    growth_input = canonical_input(growth_rows)
    expect_verification_error(
        "cumulative_extraction_term_limit",
        lambda: VERIFIER.reconstruct_coordinates(VERIFIER.validate_input(growth_input)),
        "cumulative extraction reached 1640 terms; maximum is 1638",
    )
    executed += 1

    getter = getattr(sys, "get_int_max_str_digits", None)
    setter = getattr(sys, "set_int_max_str_digits", None)
    if getter is not None and setter is not None:
        prior_limit = getter()
        try:
            setter(640)
            large_count_input = canonical_input([row("a", "b", "t", int("9" * 600))])
            # Replace the constructed 600-digit count text with a producer-valid 1,000-digit
            # count without converting it under the deliberately restrictive runtime setting.
            large_count_document = json.loads(large_count_input)
            large_count_document["rows"][0]["count"] = "9" * 1000
            large_count_raw = json.dumps(
                large_count_document,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
            expect_verification_error(
                "insufficient_python_integer_text_capacity",
                lambda: VERIFIER.validate_input(large_count_raw),
                "requires 0 (unlimited) or at least 4096",
            )
            executed += 1
        finally:
            setter(prior_limit)
    return executed


def compositions(total: int, slots: int) -> Any:
    if slots == 1:
        yield (total,)
        return
    for head in range(total + 1):
        for tail in compositions(total - head, slots - 1):
            yield (head, *tail)


def _add_bruteforce_term(
    expression: dict[Fraction, Fraction],
    coefficient: Fraction,
    argument: Fraction,
) -> None:
    if coefficient == 0 or argument == 1:
        return
    updated = expression.get(argument, Fraction(0)) + coefficient
    if updated == 0:
        expression.pop(argument, None)
    else:
        expression[argument] = updated


def brute_force_cumulative_expressions(
    input_raw: bytes,
) -> dict[tuple[str, str], dict[Fraction, Fraction]]:
    """Scan rows against the four event predicates without inclusion-exclusion."""

    document = json.loads(input_raw)
    rows = document["rows"]
    total = sum(int(item["count"]) for item in rows)
    expected = {
        (node, component): {}
        for node in VERIFIER.NODE_IDS
        for component in VERIFIER.COMPONENT_IDS
    }
    predicates: tuple[Callable[[dict[str, Any], dict[str, Any]], bool], ...] = (
        lambda candidate, keyed: (
            candidate["source_states"][0] == keyed["source_states"][0]
        ),
        lambda candidate, keyed: (
            candidate["source_states"][1] == keyed["source_states"][1]
        ),
        lambda candidate, keyed: (
            candidate["source_states"][0] == keyed["source_states"][0]
            and candidate["source_states"][1] == keyed["source_states"][1]
        ),
        lambda candidate, keyed: (
            candidate["source_states"][0] == keyed["source_states"][0]
            or candidate["source_states"][1] == keyed["source_states"][1]
        ),
    )
    for keyed in rows:
        keyed_count = int(keyed["count"])
        weight = Fraction(keyed_count, total)
        target_mass = sum(
            int(candidate["count"])
            for candidate in rows
            if candidate["target_state"] == keyed["target_state"]
        )
        for node, predicate in zip(VERIFIER.NODE_IDS, predicates):
            union = sum(
                int(candidate["count"])
                for candidate in rows
                if predicate(candidate, keyed)
            )
            target_union = sum(
                int(candidate["count"])
                for candidate in rows
                if predicate(candidate, keyed)
                and candidate["target_state"] == keyed["target_state"]
            )
            _add_bruteforce_term(
                expected[(node, "informative")],
                weight,
                Fraction(total, union),
            )
            _add_bruteforce_term(
                expected[(node, "misinformative")],
                weight,
                Fraction(target_mass, target_union),
            )
            _add_bruteforce_term(
                expected[(node, "net")],
                weight,
                Fraction(total * target_union, union * target_mass),
            )
    return expected


def check_bruteforce_event_expressions(
    input_raw: bytes, coordinates: list[Any]
) -> int:
    expected = brute_force_cumulative_expressions(input_raw)
    actual = {
        (coordinate.node, coordinate.component): coordinate.expression
        for coordinate in coordinates
        if coordinate.kind == "cumulative"
    }
    require(
        set(actual) == set(expected),
        "independent extraction did not expose the twelve cumulative identities",
    )
    checked = 0
    for identity, expression in expected.items():
        require(
            actual[identity] == expression,
            "inclusion-exclusion extraction disagrees with a direct row scan at "
            f"node/component={identity}",
        )
        checked += 1
    return checked


def check_exhaustive_small_tables(verifier: Any = VERIFIER) -> tuple[int, int]:
    states = [
        (source_one, source_two, target)
        for source_one in ("0", "1")
        for source_two in ("0", "1")
        for target in ("0", "1")
    ]
    cases = 0
    event_checks = 0
    for total in range(1, 5):
        for counts in compositions(total, len(states)):
            rows = [
                row(source_one, source_two, target, count)
                for (source_one, source_two, target), count in zip(states, counts)
                if count > 0
            ]
            input_raw = canonical_input(rows)
            coordinates = verifier.reconstruct_coordinates(
                verifier.validate_input(input_raw)
            )
            require(
                len(coordinates) == 24,
                "exhaustive table extraction did not produce 24 coordinates",
            )
            event_checks += check_bruteforce_event_expressions(input_raw, coordinates)
            cases += 1
    require(cases == 494, "unexpected exhaustive-table case count")
    require(
        event_checks == cases * 12,
        "unexpected brute-force event-expression check count",
    )
    return cases, event_checks


def check_target_union_source_mutation() -> int:
    """Require direct row scans to kill the tempting target-union max shortcut."""

    original = VERIFIER_PATH.read_text(encoding="utf-8")
    sound = (
        "        target_union_redundancy = "
        "source_one_target + source_two_target - count\n"
    )
    mutant_line = (
        "        target_union_redundancy = "
        "max(source_one_target, source_two_target)\n"
    )
    require(
        original.count(sound) == 1,
        "cannot locate the unique target-union inclusion-exclusion assignment",
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-sxpid-target-union-verifier-mutation-"
    ) as directory:
        mutant_path = Path(directory) / "verify_certificate.py"
        mutant_path.write_text(
            original.replace(sound, mutant_line),
            encoding="utf-8",
        )
        module_name = "pid_certified_sxpid_target_union_mutant"
        mutant = load_verifier_source(mutant_path, module_name)
        try:
            try:
                check_exhaustive_small_tables(mutant)
            except AssertionError as error:
                require(
                    "direct row scan" in str(error),
                    f"target-union source mutant failed for the wrong reason: {error}",
                )
            else:
                raise AssertionError(
                    "direct event qualification accepted the target-union max mutant"
                )
        finally:
            sys.modules.pop(module_name, None)
    return 1


def main() -> int:
    exact_fraction_log_cases = check_log_arithmetic()
    log_source_mutations = check_unsound_log_source_mutation()
    event_source_mutations = check_target_union_source_mutation()
    check_independent_extraction()
    structural_adversaries = check_structural_rejections()
    structural_adversaries += check_posix_invalid_filename_cli()
    exhaustive_cases, event_expression_checks = check_exhaustive_small_tables()

    inputs = [
        canonical_input([row("a", "b", "t", 1)]),
        canonical_input(
            [
                row("0", "0", "0", 1),
                row("0", "1", "1", 1),
                row("1", "0", "1", 1),
                row("1", "1", "0", 1),
            ]
        ),
        canonical_input(
            [
                row("0", "0", "0", 3),
                row("0", "1", "0", 1),
                row("0", "1", "1", 4),
                row("1", "0", "0", 2),
                row("1", "0", "1", 5),
                row("1", "1", "0", 7),
                row("1", "1", "1", 11),
            ]
        ),
    ]
    certificate_raws: list[bytes] = []
    certificates: list[dict[str, Any]] = []
    for input_raw in inputs:
        certificate_raw = run_certifier(input_raw)
        result = VERIFIER.verify_certificate(input_raw, certificate_raw, CERTIFIER_ROOT)
        require(
            result.report["status"] == "verified", "live certificate was not verified"
        )
        require(
            result.report["dyadic_containments_proved"] == 24,
            "live certificate did not prove all 24 containments",
        )
        certificate_raws.append(certificate_raw)
        certificates.append(parse_certificate(certificate_raw))

    deterministic_outputs: list[bytes] = []
    for hash_seed in ("1", "9173"):
        code, stdout, stderr = run_verifier_cli(
            inputs[-1],
            certificate_raws[-1],
            environment_overrides={"PYTHONHASHSEED": hash_seed},
        )
        require(
            code == 0,
            "independent verifier CLI rejected a live certificate under "
            f"PYTHONHASHSEED={hash_seed}: {stderr.decode(errors='replace')}",
        )
        deterministic_outputs.append(stdout)
    require(
        deterministic_outputs[0] == deterministic_outputs[1],
        "independent verifier CLI output depends on PYTHONHASHSEED",
    )

    code, stdout, stderr = run_verifier_cli(
        inputs[-1],
        certificate_raws[-1],
        environment_overrides={"PYTHONINTMAXSTRDIGITS": "640"},
    )
    require(
        code == 2 and not stderr,
        "insufficient Python integer-text capacity did not fail through the canonical CLI path",
    )
    low_limit_report = VERIFIER.parse_json(stdout, "low-limit CLI rejection")
    require(
        low_limit_report.get("status") == "rejected"
        and "requires 0 (unlimited) or at least 4096"
        in str(low_limit_report.get("message")),
        "low-limit CLI rejection did not state the required capacity",
    )
    structural_adversaries += 1

    nontrivial_input = inputs[-1]
    nontrivial_certificate = certificates[-1]
    transport_controls = check_posix_symlink_invocation_cli(
        nontrivial_input, certificate_raws[-1]
    )
    transport_controls += check_closed_stdout_cli(
        nontrivial_input, certificate_raws[-1]
    )
    cross_artifact_adversaries = check_post_import_source_mutation(
        nontrivial_input, certificate_raws[-1]
    )
    cross_artifact_adversaries += check_cargo_semantic_binding_mutation(
        nontrivial_input, nontrivial_certificate
    )
    cross_artifact_adversaries += check_cargo_patch_binding_mutation(
        nontrivial_input, nontrivial_certificate
    )
    cross_artifact_adversaries += check_cargo_lock_checksum_binding_mutation(
        nontrivial_input, nontrivial_certificate
    )
    mutations = [
        (
            "false_zero_interval",
            mutation_interval_collapses_to_false_zero,
            "independent bounded-log enclosure could not prove containment",
        ),
        (
            "positive_interval_collapsed_to_own_lower_endpoint",
            mutation_interval_collapses_to_own_lower_endpoint,
            "independent bounded-log enclosure could not prove containment",
        ),
        (
            "self_consistent_forged_expression",
            mutation_reported_expression_changes,
            "coordinate 0 exact terms mismatch",
        ),
        (
            "redundancy_union_replaced_by_joint",
            mutation_redundancy_union_becomes_joint,
            "pinned lattice evidence mismatch",
        ),
        (
            "noncanonical_dyadic",
            mutation_noncanonical_dyadic,
            "coordinate 0 lower zero is not normalized",
        ),
        (
            "forged_sign_decision",
            mutation_sign_decision,
            "coordinate 0 sign decision mismatch",
        ),
        (
            "duplicate_coordinate_identity",
            mutation_coordinate_identity,
            "coordinate 0 identity mismatch",
        ),
        (
            "forged_source_manifest_binding",
            mutation_source_manifest,
            "runtime source-manifest digest against local reviewed source mismatch",
        ),
        (
            "false_target_width_flag",
            mutation_target_width_flag,
            "coordinate 0 target-width result mismatch",
        ),
        (
            "inconsistent_precision_trace",
            mutation_precision_trace,
            "coordinate 0 precision and iteration evidence disagree",
        ),
        (
            "extreme_dyadic_exponent",
            mutation_extreme_dyadic_exponent,
            "coordinate 0 lower.exponent2 exceeds the independent verifier resource bound",
        ),
        (
            "false_exact_term_resource_count",
            mutation_exact_term_resource_count,
            "total exact-term resource evidence mismatch",
        ),
        (
            "false_exact_term_estimated_bytes",
            mutation_exact_term_estimated_bytes,
            "estimated exact-term JSON-byte resource evidence mismatch",
        ),
        (
            "numeric_evidence_bool_substitution",
            mutation_numeric_evidence_bool,
            "target width evidence mismatch",
        ),
        (
            "lattice_integer_bool_substitution",
            mutation_lattice_integer_bool,
            "pinned lattice evidence mismatch",
        ),
        (
            "broadened_permitted_claim",
            mutation_permitted_claim,
            "permitted claim mismatch",
        ),
        (
            "forged_arithmetic_status",
            mutation_arithmetic_status,
            "arithmetic evidence mismatch",
        ),
        (
            "forged_build_context_scope",
            mutation_build_context_scope,
            "build-context scope mismatch",
        ),
        (
            "forged_distribution_route",
            mutation_distribution_route,
            "tool binding project_distribution_route mismatch",
        ),
        (
            "forged_build_host",
            mutation_build_host,
            "build host against rustc verbose-version evidence mismatch",
        ),
    ]
    for name, mutation, intended_error in mutations:
        expect_rejection(
            name,
            nontrivial_input,
            nontrivial_certificate,
            mutation,
            intended_error,
        )

    # A changed input with a perfectly self-consistent original report must also fail closed.
    changed_input = canonical_input(
        [
            row("0", "0", "0", 4),
            row("0", "1", "0", 1),
            row("0", "1", "1", 4),
            row("1", "0", "0", 2),
            row("1", "0", "1", 5),
            row("1", "1", "0", 7),
            row("1", "1", "1", 11),
        ]
    )
    expect_verification_error(
        "certificate_for_changed_input",
        lambda: VERIFIER.verify_certificate(
            changed_input,
            VERIFIER.canonical_json_bytes(nontrivial_certificate),
            CERTIFIER_ROOT,
        ),
        "raw input digest mismatch",
    )

    print(
        "OK: independent integer/rational-log verifier reconstructed "
        f"{exhaustive_cases * 24:,} coordinates and {exhaustive_cases * 3:,} direct-MI "
        f"identities plus {event_expression_checks:,} direct event-expression identities "
        "over 494 exhaustive tables, proved 72 live-certificate containments, and "
        f"checked {exact_fraction_log_cases:,} exact-Fraction log enclosures; killed all "
        f"{len(mutations) + 1} semantic mutations, {log_source_mutations} fixed-point "
        f"source mutation, {event_source_mutations} event-extraction source mutation, and "
        f"{cross_artifact_adversaries} cross-artifact binding adversaries; "
        f"{structural_adversaries} structural adversaries failed for their intended reasons, "
        f"{transport_controls} transport/invocation controls passed, and CLI output was "
        "hash-seed invariant"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
