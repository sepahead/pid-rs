#!/usr/bin/env python3
"""Validate the closed Pandoc 3.1.3 operator-observation receipt and repository inputs."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
import sys
from typing import Any, NoReturn


ROOT = pathlib.Path(__file__).resolve().parent.parent
RECEIPT = (
    ROOT
    / "audit/evidence/"
    "mathematical-results-guide-pandoc-3.1.3-portability-v1.json"
)
RECEIPT_SHA256 = "4bdaa6f62f1cd8baa9814b1ff0b8ec8b8cbc4d4607f34ac0e38f658f31840af4"
MAX_RECEIPT_BYTES = 65_536
MAX_TRACKED_INPUT_BYTES = 16 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

EXPECTED_REPOSITORY_INPUTS = {
    "MATHEMATICAL_RESULTS_GUIDE.md": "769b8adae80efa379b3502af9f5edfed839e5a6ac59d08d85e343809e5cf285b",
    "output/pdf/mathematical-results-guide.pdf": "3f8e8196f3dc510eb122926322829f111c1b745fbbf27c920e9606f9a212c200",
    "scripts/build-mathematical-results-guide-pdf.sh": "b7c49c411782b8a8b7a60d37567543a8b5a463adfa8f321a534b1c94783085a1",
    "scripts/check-mathematical-results-guide-pdf-id-variance.py": "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
    "scripts/check-mathematical-results-guide-pdf-id-variance-self-test.py": "757c85a55a8209fb3587e130daf36ab51aac210e87f5604bea40213c62e51c5a",
    "scripts/normalize-mathematical-results-guide-pandoc-tex.py": "401271a933917833e7eca8654bd24e23f42fe19dfeab85c28165815bf55554bf",
    "scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py": "337ffc66888fb8f8f75f8e41429beea7b65fa7370a84695487f81dea4de4d3a0",
    "scripts/check-mathematical-results-guide-builder-self-test.sh": "c1dc31e97716126c9be137ea8374360968f4138925e93d7e82c756785483b8ab",
    "scripts/check-mathematical-results-guide-pdf-structure.py": "b513404846cdd02048f2e9133ddae927609049fb202956a7cd072ddaff1edf6c",
    "THIRD_PARTY_NOTICES.md": "4279f2628c79bfdc9c226d05c55bf7c643e70b14fa3b03033290f5d91d54ff0d",
    "audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt": "cf5b70694cf50403b51f3315f98d010de6435022ff984911819219034a088180",
}

EXPECTED_TOP_LEVEL_KEYS = {
    "schema",
    "captured_at_utc",
    "status",
    "evidence_class",
    "subject",
    "source_state",
    "current_selected_repository_input_digests",
    "post_observation_source_delta",
    "execution_environment",
    "normalization_observation",
    "pre_normalization_observation",
    "final_run_observation",
    "operator_reported_complete_gate_run",
    "operator_reported_poppler_comparison",
    "negative_execution_evidence",
    "artifact_retention",
    "recorded_observations",
    "does_not_establish",
}

EXPECTED_RECORDED_OBSERVATIONS = [
    "the operator recorded that the selected /usr/bin/pandoc path matched the recorded Pandoc 3.1.3 executable hash at the builder custody check in the declared translated Ubuntu environment",
    "the operator recorded the audited legacy compatibility transform with the declared exact delta counts",
    "the operator recorded passing results for the unchanged source-specific final PDF structure, navigation, text, geometry, font, and active-content policies",
    "the current canonical Pandoc 3.10.2 exact route remains independently replayable and byte-identical to the committed PDF",
    "the operator recorded two old-toolchain builds that differed only in their strict duplicated trailer-ID payloads",
]

EXPECTED_NONCLAIMS = [
    "native x86_64-hardware execution",
    "general equivalence between Pandoc 3.1.3 and 3.10.2 or arbitrary Markdown and TeX inputs",
    "raw TeX or raw PDF byte identity across toolchains",
    "cross-host, cross-platform, cross-renderer, or future-version reproducibility",
    "PDF/UA conformance, figure Alt entries, or assistive-technology accessibility",
    "independently replayable custody of the recorded old-toolchain execution, because its raw TeX, PDFs, and complete execution logs were not retained",
    "an atomic binding from the executable path-hash observation to the bytes that the operating system ran, or renderer, container-image, package, or upstream supply-chain authenticity beyond the recorded locators and hashes",
    "mathematical correctness, estimator validity, or scientific novelty",
    "a cause for trailer-ID variation beyond the measured strict relation",
]


def fail(message: str) -> NoReturn:
    raise SystemExit(f"Pandoc portability receipt check failed: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def identity(status: os.stat_result) -> tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def read_regular(path: pathlib.Path, maximum: int, label: str) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"{label} cannot be opened without following links: {error}")
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode), f"{label} is not regular")
        require(before.st_nlink == 1, f"{label} must have one hard link")
        require(0 < before.st_size <= maximum, f"{label} byte count is out of bounds")
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    require(identity(before) == identity(after), f"{label} changed while it was read")
    require(len(data) == before.st_size, f"{label} size changed while it was read")
    try:
        path_status = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        fail(f"{label} disappeared after it was read")
    require(identity(path_status) == identity(before), f"{label} path changed while it was read")
    return data


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"receipt contains a duplicate JSON key: {key}")
        result[key] = value
    return result


def require_sha(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None, f"{label} is not lowercase SHA-256")
    return value


def validate_document(document: Any) -> None:
    require(isinstance(document, dict), "receipt root is not an object")
    require(set(document) == EXPECTED_TOP_LEVEL_KEYS, "receipt top-level key set changed")
    require(document["schema"] == "pid-rs.mathematical-results-guide-pandoc-portability-receipt.v1", "schema changed")
    require(
        document["status"]
        == "closed_operator_observation_without_retained_raw_execution_artifacts",
        "status changed",
    )
    require(
        document["evidence_class"]
        == "operator observation plus current selected repository-input digest replay; not independently replayable custody of the recorded old-toolchain execution",
        "evidence class changed",
    )
    require(document["subject"] == "MATHEMATICAL_RESULTS_GUIDE.md", "subject changed")
    require(document["captured_at_utc"] == "2026-08-29T11:21:04Z", "capture time changed")
    require(
        document["current_selected_repository_input_digests"]
        == EXPECTED_REPOSITORY_INPUTS,
        "repository-input ledger changed",
    )
    require(
        document["post_observation_source_delta"]
        == {
            "classification": "lint-only typing/import correction plus the corresponding builder digest rebind",
            "changed_paths": [
                {
                    "path": "scripts/check-mathematical-results-guide-pdf-id-variance.py",
                    "operator_observed_sha256": "e34d8163c639cb61e5355c59645eb52ca49718260e93eea3ba56a861277377ab",
                    "current_sha256": "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
                    "change": "import typing.NoReturn and use the resolved annotation",
                },
                {
                    "path": "scripts/check-mathematical-results-guide-pdf-id-variance-self-test.py",
                    "operator_observed_sha256": "9a12beaf4de5ceae6aca00910d528a0b87d218f2a78cdf692cf8771a9c169a34",
                    "current_sha256": "757c85a55a8209fb3587e130daf36ab51aac210e87f5604bea40213c62e51c5a",
                    "change": "remove an unused import, import typing.NoReturn, and use the resolved annotation",
                },
                {
                    "path": "scripts/build-mathematical-results-guide-pdf.sh",
                    "operator_observed_sha256": "65b60188b086cb3e6aaeb0a3c5fa9ca889ace4d4a02a9aed00e0f585dd3e7218",
                    "current_sha256": "b7c49c411782b8a8b7a60d37567543a8b5a463adfa8f321a534b1c94783085a1",
                    "change": "rebind the exact trailer-ID checker digest; no build behavior changed",
                },
            ],
            "credit_boundary": "the earlier operator observation remains associated with the before-digests and is not transferred to the corrected sources; the current exact and cross-toolchain gates must be rerun separately",
        },
        "post-observation source-delta record changed",
    )

    source = document["source_state"]
    require(source["parent_commit"] == "9ed6831d20de43467b1cff8adc8ee421a484f7fd", "PDF parent changed")
    require(source["historical_ksg_c3_parent"] == "8b792bc143fff2d84f2d8e7817d1de7850741223", "historical C3 parent changed")
    require(source["historical_ksg_c3_child"] == "8fa6e992d9124229c7a175c4508bf10df336675a", "historical C3 child changed")
    require(source["working_tree_was_uncommitted"] is True, "capture-state boundary changed")

    environment = document["execution_environment"]
    container = environment["container"]
    require(
        container
        == {
            "image_reference": "ubuntu:24.04",
            "oci_image_index_digest": "sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea",
            "linux_amd64_manifest_digest": "sha256:019e8eb29a85e74d64925745884f2ec79aa27e3feab36353d24656f4d6b89467",
            "linux_amd64_config_digest": "sha256:045183670ef29ce21bc22a8d4f62511ce472679ca8fc9774f04181f7f383ca62",
            "image_locator_boundary": "the immutable OCI index was resolved after the run to the declared linux/amd64 manifest and config locators; raw registry responses, local rootfs bytes, and download/authentication custody were not retained",
            "userspace_architecture": "x86_64",
            "kernel": "Linux 6.8.0-50-generic",
            "execution_route": "Rosetta binfmt interpreter /mnt/lima-rosetta/rosetta",
            "native_x86_64_hardware": False,
        },
        "container observation changed",
    )
    old_pandoc = environment["old_tools"]["pandoc"]
    require(old_pandoc["version"] == "3.1.3", "old Pandoc version changed")
    require(old_pandoc["path"] == "/usr/bin/pandoc", "old Pandoc path changed")
    require_sha(old_pandoc["sha256"], "old Pandoc digest")
    require(old_pandoc["sha256"] == "3dd273647f0265cb439f22976d5366a54b071a3783f6fec50838b47fb53d701b", "old Pandoc digest changed")

    normalization = document["normalization_observation"]
    require(normalization["mode"] == "legacy-3.1.3", "normalization mode changed")
    require(normalization["byte_identity"] is False, "normalization byte-identity boundary changed")
    expected_deltas = {
        "heading_wrappers_removed": 17,
        "table_wrappers_inserted": 4,
        "none_counter_inserted": 1,
        "table_preamble_replaced": 1,
        "image_preamble_replaced": 1,
        "crosswalk_projection_replaced": 1,
    }
    for key, expected in expected_deltas.items():
        require(normalization[key] == expected, f"normalization delta changed: {key}")
    require(normalization["legacy_raw_tex"] == {"bytes": 51669, "sha256": "96e003b0061c1cdf8f33d2275a6fd16f2d8dfc608dccc2441063620234bff5ca"}, "legacy raw-TeX observation changed")
    require(normalization["normalized_tex"] == {"bytes": 51093, "sha256": "9a9131b66b627613016311f1f9e5f6a2571ee0f89a3c973af44322b7f30adb87"}, "normalized-TeX observation changed")

    negative = document["pre_normalization_observation"]
    require(negative["destination_count"] == 56 and negative["unique_destination_count"] == 56, "pre-normalization destination census changed")
    require(negative["heading_alias_count"] == 17, "pre-normalization heading-alias census changed")
    require(negative["table_destinations"] == ["table.1", "table.2", "table.3", "table.4"], "pre-normalization table names changed")
    require(negative["none_destinations"] == [], "pre-normalization none-name census changed")
    require("valid PDF syntax" in negative["interpretation"] and "not empty, malformed" in negative["interpretation"], "negative-result interpretation changed")

    final = document["final_run_observation"]
    require(final["pages"] == 16 and final["tagged"] is True, "final page/tag status changed")
    require(final["suspects"] is False and final["javascript"] is False and final["form"] == "none", "final active-content status changed")
    require(final["destination_count"] == 39 and final["unique_destination_count"] == 39, "final destination census changed")
    require(final["heading_alias_count"] == 0 and final["table_destinations"] == [], "final obsolete-name census changed")
    require(final["none_destinations"] == ["none.1", "none.2", "none.3", "none.4"], "final none-name census changed")
    require(final["navigation_records"] == 167, "navigation count changed")
    require(final["repeated_build_relation"] == "byte_equal_outside_the_two_duplicated_16_byte_trailer_ID_payloads", "repeated-build relation changed")
    for field in ("target_manifest_sha256", "navigation_sha256", "structure_sha256", "extracted_text_sha256", "normalized_font_roster_sha256"):
        require_sha(final[field], f"final {field}")

    gate = document["operator_reported_complete_gate_run"]
    require(
        gate
        == {
            "command": "scripts/check-mathematical-results-guide-pdf.sh --cross-toolchain",
            "status": "operator_reported_passed",
            "builder_sha256": "65b60188b086cb3e6aaeb0a3c5fa9ca889ace4d4a02a9aed00e0f585dd3e7218",
            "id_variance_checker_sha256": "e34d8163c639cb61e5355c59645eb52ca49718260e93eea3ba56a861277377ab",
            "id_variance_self_test_sha256": "9a12beaf4de5ceae6aca00910d528a0b87d218f2a78cdf692cf8771a9c169a34",
            "receipt_checker_sha256": "6d4cfecc87a271410ad9fde876b63060d0e13000fc2388e02f98ec424609b783",
            "receipt_self_test_sha256": "4d902e73cca4e637aebe53c7e5739a39662d0a2f7399ead84820c2959dccbfee",
            "first_pdf_sha256": "c3df50d0ee566902ae035ae2cef92782ec47b87705c4385d41b733fc70031bd7",
            "second_pdf_sha256": "e37a773bfd055023779c0378272aa73a38b72a593b93b347def65e1304a67cfe",
            "first_trailer_id": "670ABFBAD1E2057D7AEE1487BA172DBC",
            "second_trailer_id": "352B47D452257045FE46EC7BB262B7FC",
            "normalizer_self_test": "4 positive processes and 214 rejected processes in each of normal and optimized Python",
            "builder_self_test": "69 hostile/control cases",
            "structure_self_test": "74 object-graph mutations, 1 raw-parser mutation, 4 name-tree diagnostic controls, and 4 output-path controls in each Python mode",
            "receipt_self_test": "2 controls, 26 semantic mutations, and 7 custody mutations in each Python mode",
        },
        "operator-reported complete-gate record changed",
    )
    render = document["operator_reported_poppler_comparison"]
    require(render["old_pages"] == 16 and render["canonical_pages"] == 16, "render page census changed")
    require(render["all_page_png_bytes_equal"] is True, "render equality changed")
    require("one rasterizer" in render["boundary"], "render boundary changed")

    qemu = document["negative_execution_evidence"]
    require(qemu["qemu_signal"] == "SIGSEGV_139" and qemu["credit"] == "none", "QEMU negative evidence changed")
    require_sha(qemu["qemu_core_sha256"], "QEMU core digest")
    retention = document["artifact_retention"]
    require(all(retention[key] is False for key in ("raw_tex_tracked", "normalized_tex_tracked", "pre_normalization_pdf_tracked", "final_old_toolchain_pdf_tracked")), "artifact-retention boundary changed")

    require(
        document["recorded_observations"] == EXPECTED_RECORDED_OBSERVATIONS,
        "recorded-observation ledger changed",
    )
    require(document["does_not_establish"] == EXPECTED_NONCLAIMS, "nonclaim ledger changed")


def main() -> None:
    require(len(sys.argv) == 1, f"usage: {sys.argv[0]}")
    receipt_bytes = read_regular(RECEIPT, MAX_RECEIPT_BYTES, "receipt")
    require(hashlib.sha256(receipt_bytes).hexdigest() == RECEIPT_SHA256, "receipt digest changed")
    require(not receipt_bytes.startswith(b"\xef\xbb\xbf"), "receipt has a UTF-8 byte-order mark")
    require(b"\x00" not in receipt_bytes and b"\r" not in receipt_bytes, "receipt encoding or line endings changed")
    require(receipt_bytes.endswith(b"\n"), "receipt lacks final LF")
    try:
        document = json.loads(receipt_bytes.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"receipt is not canonical UTF-8 JSON: {error}")
    validate_document(document)

    for relative, expected in EXPECTED_REPOSITORY_INPUTS.items():
        path = ROOT / relative
        observed = hashlib.sha256(read_regular(path, MAX_TRACKED_INPUT_BYTES, relative)).hexdigest()
        require(observed == expected, f"repository input digest changed: {relative}")

    print(
        "OK: closed Pandoc 3.1.3 guide-portability operator-observation receipt "
        "(translated_x86_64=yes; native_x86_64=no; normalization_deltas=25; "
        "final_destinations=39; navigation=167; raw_artifacts=not_tracked)"
    )


if __name__ == "__main__":
    main()
