#!/usr/bin/env python3
"""Baseline-first mutation suite for the bounded KSG modular certificate."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts/generate-ksg-harmonic-modular-certificate.py"
CHECKER = ROOT / "scripts/check-ksg-harmonic-modular-certificate.py"
FIXTURE = ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
CERTIFICATE = (
    ROOT
    / "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    / "ksg-harmonic-modular-certificate-v1.json"
)
SIDECAR = CERTIFICATE.with_suffix(CERTIFICATE.suffix + ".sha256")

EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
EXPECTED_CERTIFICATE_SHA256 = (
    "5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f"
)


class SelfTestError(RuntimeError):
    """The baseline failed or a load-bearing mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(
        count == 1,
        f"{label}: expected exactly one source replacement target, found {count}",
    )
    return text.replace(old, new, 1)


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def child_optimization_arguments() -> list[str]:
    require(
        sys.flags.optimize in (0, 1, 2),
        f"unsupported parent optimization level: {sys.flags.optimize}",
    )
    if sys.flags.optimize == 0:
        return []
    return ["-" + "O" * sys.flags.optimize]


def child_python_command(script: Path, *arguments: str) -> list[str]:
    return [
        sys.executable,
        *child_optimization_arguments(),
        str(script),
        *arguments,
    ]


def child_optimization_preflight() -> None:
    probe = run_command(
        [
            sys.executable,
            *child_optimization_arguments(),
            "-c",
            "import sys; print(sys.flags.optimize)",
        ]
    )
    require(
        probe.returncode == 0,
        "child-optimization preflight process failed:\n"
        + probe.stdout
        + probe.stderr,
    )
    require(
        probe.stdout == f"{sys.flags.optimize}\n",
        "child-optimization preflight did not preserve the parent level: "
        f"parent={sys.flags.optimize}, child={probe.stdout!r}",
    )


def baseline_first(fixture: Path) -> None:
    child_optimization_preflight()
    generator = run_command(
        child_python_command(
            GENERATOR,
            "--fixture",
            str(fixture),
        )
    )
    require(
        generator.returncode == 0,
        "generator baseline failed before mutation testing:\n"
        + generator.stdout
        + generator.stderr,
    )
    checker = run_command(
        child_python_command(
            CHECKER,
            "--fixture",
            str(fixture),
        )
    )
    require(
        checker.returncode == 0,
        "checker baseline failed before mutation testing:\n"
        + checker.stdout
        + checker.stderr,
    )
    require(
        "8198 rows" in checker.stdout
        and "endpoints 354 (240/114)" in checker.stdout
        and "nonendpoints 7844 nonzero in each of 3 selected fields"
        in checker.stdout
        and "rejected collisions 4" in checker.stdout,
        "baseline checker summary drifted",
    )


class CaseFiles:
    def __init__(self, root: Path, fixture_source: Path) -> None:
        self.root = root
        self.scripts = root / "scripts"
        self.certificates = root / "certificates"
        self.scripts.mkdir(parents=True)
        self.certificates.mkdir(parents=True)
        self.fixture = root / "ksg_local_arithmetic_oracle.json"
        self.generator = self.scripts / GENERATOR.name
        self.checker = self.scripts / CHECKER.name
        self.certificate = self.certificates / CERTIFICATE.name
        self.sidecar = self.certificates / SIDECAR.name
        shutil.copyfile(fixture_source, self.fixture)
        shutil.copyfile(GENERATOR, self.generator)
        shutil.copyfile(CHECKER, self.checker)
        shutil.copyfile(CERTIFICATE, self.certificate)
        shutil.copyfile(SIDECAR, self.sidecar)

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return run_command(
            child_python_command(
                self.checker,
                "--fixture",
                str(self.fixture),
                "--generator",
                str(self.generator),
                "--certificate",
                str(self.certificate),
                "--sidecar",
                str(self.sidecar),
            )
        )

    def patch_checker(self, old: str, new: str, label: str) -> None:
        source = self.checker.read_text(encoding="utf-8")
        self.checker.write_text(
            replace_once(source, old, new, label),
            encoding="utf-8",
            newline="",
        )

    def write_certificate_raw(
        self, raw: bytes, *, rebase_checker_digest: bool
    ) -> str:
        digest = hashlib.sha256(raw).hexdigest()
        self.certificate.write_bytes(raw)
        self.sidecar.write_text(
            f"{digest}  {self.certificate.name}\n",
            encoding="utf-8",
            newline="",
        )
        if rebase_checker_digest:
            self.patch_checker(
                EXPECTED_CERTIFICATE_SHA256,
                digest,
                "certificate digest rebase",
            )
        return digest

    def write_certificate_value(
        self, value: dict[str, Any], *, rebase_checker_digest: bool = True
    ) -> str:
        return self.write_certificate_raw(
            canonical_json_bytes(value),
            rebase_checker_digest=rebase_checker_digest,
        )


def expect_rejection(
    root: Path,
    fixture_source: Path,
    label: str,
    mutate: Callable[[CaseFiles], None],
    *,
    diagnostic: str | None = None,
) -> None:
    case = CaseFiles(root / label, fixture_source)
    mutate(case)
    result = case.run_checker()
    require(
        result.returncode != 0,
        f"mutation survived: {label}\n{result.stdout}{result.stderr}",
    )
    if diagnostic is not None:
        require(
            diagnostic in result.stdout + result.stderr,
            f"mutation {label} failed for an unexpected reason; wanted "
            f"{diagnostic!r}\n{result.stdout}{result.stderr}",
        )


def certificate_mutation(
    baseline: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
) -> Callable[[CaseFiles], None]:
    def apply(case: CaseFiles) -> None:
        value = copy.deepcopy(baseline)
        mutate(value)
        case.write_certificate_value(value)

    return apply


def json_type_firewall_controls(
    baseline: dict[str, Any],
) -> tuple[tuple[str, Callable[[CaseFiles], None], str], ...]:
    """Controls for Python JSON scalar equalities that are not scientific mutants."""

    def certificate_revision_boolean(value: dict[str, Any]) -> None:
        value["certificate_revision"] = True

    def residue_encoding_integer(value: dict[str, Any]) -> None:
        value["residue_encoding"]["include_zero_residues"] = 1

    return (
        (
            "json-type-firewall-certificate-revision-boolean",
            certificate_mutation(baseline, certificate_revision_boolean),
            "wrong JSON type at $",
        ),
        (
            "json-type-firewall-residue-encoding-integer",
            certificate_mutation(baseline, residue_encoding_integer),
            "wrong JSON type at $/include_zero_residues",
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE,
        help="frozen schema-2 fixture; override is useful only for isolated-tree assembly",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_first(args.fixture)

    baseline_raw = CERTIFICATE.read_bytes()
    require(
        hashlib.sha256(baseline_raw).hexdigest() == EXPECTED_CERTIFICATE_SHA256,
        "self-test certificate custody constant drifted",
    )
    baseline = json.loads(baseline_raw)
    checker_source = CHECKER.read_text(encoding="utf-8")

    mutations: list[
        tuple[
            str,
            Callable[[CaseFiles], None],
            str | None,
        ]
    ] = []

    def selected_prime_mutation(
        replacement: int,
        replacement_source: str,
    ) -> Callable[[CaseFiles], None]:
        def apply(case: CaseFiles) -> None:
            value = copy.deepcopy(baseline)
            value["selected_prime_certificates"][0]["prime"] = replacement
            case.write_certificate_value(value)
            case.patch_checker(
                "SELECTED_PRIMES = (1_000_033, 1_000_037, 1_000_081)",
                replacement_source,
                "selected-prime tuple mutation",
            )

        return apply

    mutations.extend(
        [
            (
                "prime-too-small-noninvertible",
                selected_prime_mutation(
                    999_983,
                    "SELECTED_PRIMES = (999_983, 1_000_037, 1_000_081)",
                ),
                "not above every denominator",
            ),
            (
                "composite-selected-modulus",
                selected_prime_mutation(
                    # 1_000_001 = 101 * 9_901. It is not divisible by the checker's
                    # small-prime prefilter (2..37), so rejection exercises the
                    # Miller--Rabin witness loop rather than only the prefilter.
                    1_000_001,
                    "SELECTED_PRIMES = (1_000_001, 1_000_037, 1_000_081)",
                ),
                "is composite",
            ),
        ]
    )

    def promote_rejected_prime(case: CaseFiles) -> None:
        value = copy.deepcopy(baseline)
        value["selected_prime_certificates"][0] = copy.deepcopy(
            value["rejected_prime_negative_control"]
        )
        case.write_certificate_value(value)
        case.patch_checker(
            "SELECTED_PRIMES = (1_000_033, 1_000_037, 1_000_081)",
            "SELECTED_PRIMES = (1_000_003, 1_000_037, 1_000_081)",
            "rejected-prime promotion",
        )

    mutations.append(
        (
            "selected-to-rejected-prime",
            promote_rejected_prime,
            "has nonendpoint collisions",
        )
    )

    def mutate_residue(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"][0]["residue_u32be_sha256"] = "0" * 64

    mutations.append(
        (
            "selected-residue-digest",
            certificate_mutation(baseline, mutate_residue),
            "differ from independent replay",
        )
    )

    def reverse_row_replay(case: CaseFiles) -> None:
        case.patch_checker(
            "for sample_count, k, x_count, y_count in rows:",
            "for sample_count, k, x_count, y_count in reversed(rows):",
            "residue row-order mutation",
        )

    mutations.append(
        (
            "residue-row-order",
            reverse_row_replay,
            "replayed residue digest drifted",
        )
    )

    def little_endian_replay(case: CaseFiles) -> None:
        case.patch_checker(
            '4, byteorder="big", signed=False',
            '4, byteorder="little", signed=False',
            "residue endianness mutation",
        )

    mutations.append(
        (
            "residue-endianness",
            little_endian_replay,
            "replayed residue digest drifted",
        )
    )

    def asymmetric_endpoint(case: CaseFiles) -> None:
        case.patch_checker(
            "return sorted((x_count, y_count)) == [k - 1, sample_count - 1]",
            "return (x_count, y_count) == (k - 1, sample_count - 1)",
            "endpoint predicate mutation",
        )

    mutations.append(
        (
            "endpoint-predicate-source",
            asymmetric_endpoint,
            "fixture endpoint split drifted",
        )
    )

    def segment_count(value: dict[str, Any]) -> None:
        value["corpus"]["segments"][0]["endpoint_count"] = 239

    mutations.append(
        (
            "segment-split-count",
            certificate_mutation(baseline, segment_count),
            "certificate 'corpus' drifted",
        )
    )

    def split_boundary_source(case: CaseFiles) -> None:
        case.patch_checker(
            "EXHAUSTIVE_ROW_COUNT = 6_920",
            "EXHAUSTIVE_ROW_COUNT = 6_919",
            "exhaustive split-boundary mutation",
        )

    mutations.append(
        (
            "split-boundary-source",
            split_boundary_source,
            "independent exhaustive reconstruction count drifted",
        )
    )

    def stale_harmonic_denominator_name(value: dict[str, Any]) -> None:
        value["corpus"]["maximum_harmonic_denominator"] = value["corpus"].pop(
            "maximum_reciprocal_summand_index"
        )

    mutations.append(
        (
            "stale-harmonic-denominator-object-name",
            certificate_mutation(baseline, stale_harmonic_denominator_name),
            "certificate 'corpus' drifted",
        )
    )

    def remove_summand_invertibility_premise(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"][0][
            "greater_than_every_reciprocal_summand_index"
        ] = False

    mutations.append(
        (
            "summand-invertibility-premise",
            certificate_mutation(baseline, remove_summand_invertibility_premise),
            "selected-prime certificate records differ",
        )
    )

    def duplicate_selected(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"][1] = copy.deepcopy(
            value["selected_prime_certificates"][0]
        )

    mutations.append(
        (
            "duplicate-selected-prime",
            certificate_mutation(baseline, duplicate_selected),
            "selected-prime order or membership drifted",
        )
    )

    def drop_selected(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"].pop()

    mutations.append(
        (
            "drop-selected-prime",
            certificate_mutation(baseline, drop_selected),
            "selected-prime record count drifted",
        )
    )

    def fixture_byte_custody(case: CaseFiles) -> None:
        case.fixture.write_bytes(case.fixture.read_bytes() + b"\n")

    mutations.append(
        (
            "fixture-byte-custody",
            fixture_byte_custody,
            "fixture SHA-256 custody mismatch",
        )
    )

    def fixture_row_order_resealed(case: CaseFiles) -> None:
        fixture = json.loads(case.fixture.read_bytes())
        fixture["cases"][0], fixture["cases"][1] = (
            fixture["cases"][1],
            fixture["cases"][0],
        )
        fixture_raw = canonical_json_bytes(fixture)
        fixture_digest = hashlib.sha256(fixture_raw).hexdigest()
        case.fixture.write_bytes(fixture_raw)

        value = copy.deepcopy(baseline)
        value["corpus"]["fixture"]["sha256"] = fixture_digest
        case.write_certificate_value(value)
        case.patch_checker(
            EXPECTED_FIXTURE_SHA256,
            fixture_digest,
            "resealed fixture digest",
        )

    mutations.append(
        (
            "fixture-row-order-resealed",
            fixture_row_order_resealed,
            "fixture row order or argument set differs",
        )
    )

    def generator_byte_custody(case: CaseFiles) -> None:
        case.generator.write_bytes(
            case.generator.read_bytes() + b"\n# custody mutation\n"
        )

    mutations.append(
        (
            "generator-byte-custody",
            generator_byte_custody,
            "generator SHA-256 custody mismatch",
        )
    )

    def certificate_byte_custody(case: CaseFiles) -> None:
        case.certificate.write_bytes(case.certificate.read_bytes() + b"\n")

    mutations.append(
        (
            "certificate-byte-custody",
            certificate_byte_custody,
            "certificate SHA-256 custody mismatch",
        )
    )

    def stale_sidecar(case: CaseFiles) -> None:
        case.sidecar.write_text(
            "0" * 64 + f"  {case.certificate.name}\n",
            encoding="utf-8",
            newline="",
        )

    mutations.append(
        (
            "certificate-sidecar-custody",
            stale_sidecar,
            "certificate sidecar is stale or malformed",
        )
    )

    def schema_identifier(value: dict[str, Any]) -> None:
        value["schema"] = "pid-rs/ksg-harmonic-modular-certificate-mutated"

    mutations.append(
        (
            "schema-identifier",
            certificate_mutation(baseline, schema_identifier),
            "certificate 'schema' drifted",
        )
    )

    def schema_revision(value: dict[str, Any]) -> None:
        value["schema_revision"] = 2

    mutations.append(
        (
            "schema-revision",
            certificate_mutation(baseline, schema_revision),
            "certificate 'schema_revision' drifted",
        )
    )

    def noncanonical_certificate(case: CaseFiles) -> None:
        case.write_certificate_raw(
            baseline_raw + b"\n",
            rebase_checker_digest=True,
        )

    mutations.append(
        (
            "certificate-canonicality",
            noncanonical_certificate,
            "certificate is not canonical JSON",
        )
    )

    def nonfinite_certificate(case: CaseFiles) -> None:
        raw = baseline_raw.replace(
            b'  "schema_revision": 1,\n',
            b'  "schema_revision": NaN,\n',
            1,
        )
        require(raw != baseline_raw, "nonfinite JSON mutation target was absent")
        case.write_certificate_raw(raw, rebase_checker_digest=True)

    mutations.append(
        (
            "certificate-nonfinite-json",
            nonfinite_certificate,
            "certificate is not finite canonical UTF-8 JSON",
        )
    )

    def duplicate_json_key(case: CaseFiles) -> None:
        raw = baseline_raw.replace(
            b'  "schema": "pid-rs/ksg-harmonic-modular-certificate",\n',
            (
                b'  "schema": "pid-rs/ksg-harmonic-modular-certificate",\n'
                b'  "schema": "pid-rs/ksg-harmonic-modular-certificate",\n'
            ),
            1,
        )
        require(raw != baseline_raw, "duplicate-key mutation target was absent")
        case.write_certificate_raw(raw, rebase_checker_digest=True)

    mutations.append(
        (
            "certificate-duplicate-key",
            duplicate_json_key,
            "duplicate JSON key",
        )
    )

    def implication_direction(value: dict[str, Any]) -> None:
        value["statement"]["residue_implication_direction"] = (
            "zero_modular_residue_implies_exact_rational_zero"
        )
        value["statement"]["zero_residue_nonimplication"] = (
            "nonzero_modular_residue_does_not_imply_exact_rational_nonzero"
        )

    mutations.append(
        (
            "implication-direction",
            certificate_mutation(baseline, implication_direction),
            "certificate 'statement' drifted",
        )
    )

    def crt_escalation(value: dict[str, Any]) -> None:
        value["statement"]["selected_prime_set_role"] = (
            "crt_reconstruction_universal_zero_theorem"
        )

    mutations.append(
        (
            "crt-universal-escalation",
            certificate_mutation(baseline, crt_escalation),
            "certificate 'statement' drifted",
        )
    )

    def collision_sign(value: dict[str, Any]) -> None:
        collision = value["rejected_prime_negative_control"]["collisions"][0]
        collision["sign"] = "negative"
        collision["strict_nonzero_witness"]["tail_coefficient"] = -1

    mutations.append(
        (
            "rejected-collision-sign",
            certificate_mutation(baseline, collision_sign),
            "rejected-prime negative control differs",
        )
    )

    def collision_index(value: dict[str, Any]) -> None:
        collision = value["rejected_prime_negative_control"]["collisions"][0]
        collision["fixture_index_zero_based"] += 1
        collision["fixture_ordinal_one_based"] += 1

    mutations.append(
        (
            "rejected-collision-index",
            certificate_mutation(baseline, collision_index),
            "rejected-prime negative control differs",
        )
    )

    def rejected_residue(value: dict[str, Any]) -> None:
        value["rejected_prime_negative_control"]["residue_u32be_sha256"] = "f" * 64

    mutations.append(
        (
            "rejected-residue-digest",
            certificate_mutation(baseline, rejected_residue),
            "rejected-prime negative control differs",
        )
    )

    require(
        EXPECTED_CERTIFICATE_SHA256 in checker_source,
        "checker no longer contains the certificate custody pin",
    )
    killed: list[str] = []
    firewall_killed: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-modular-self-test-"
    ) as temporary:
        temporary_root = Path(temporary)
        for label, mutate, diagnostic in mutations:
            expect_rejection(
                temporary_root,
                args.fixture,
                label,
                mutate,
                diagnostic=diagnostic,
            )
            killed.append(label)
        for label, mutate, diagnostic in json_type_firewall_controls(baseline):
            expect_rejection(
                temporary_root,
                args.fixture,
                label,
                mutate,
                diagnostic=diagnostic,
            )
            firewall_killed.append(label)

    require(len(killed) == 28, f"mutation inventory drifted: {len(killed)}")
    require(
        len(firewall_killed) == 2,
        f"JSON type-firewall control inventory drifted: {len(firewall_killed)}",
    )
    print(
        "OK: KSG modular certificate baseline passed before "
        f"{len(killed)}/{len(killed)} mutations were rejected "
        f"with child optimization level {sys.flags.optimize} "
        "(prime/domain 3, residue/encoding 3, endpoint/split 3, summand-object 2, "
        "prime inventory 2, custody 5, schema/canonicality 5, "
        "claim-boundary/collision 5); separately, "
        f"{len(firewall_killed)}/{len(firewall_killed)} bool/int JSON "
        "type-firewall controls were rejected"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, SelfTestError) as error:
        print(f"KSG modular certificate self-test error: {error}", file=sys.stderr)
        raise SystemExit(1)
