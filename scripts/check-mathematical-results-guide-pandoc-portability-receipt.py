#!/usr/bin/env python3
"""Validate the historical Pandoc observation and its retained replay adjudication.

The receipt records two guide-dispatch sources at the exact bytes used for the
legacy adjudication.  Those digests are historical facts, not pins on the
later producer-profile dispatcher.  Reading the current files at those paths
would make the legacy checker and the current wrapper hash-pin each other.

Later producer profiles are outside this check.  They must validate their own
artifacts and cannot transfer evidence to this Pandoc 3.1.3 record.
"""

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
RECEIPT_SHA256 = "7ea2acf89c8a33f5666ab9798a594c24febdad609bd1b5e650b87d8a98ca4581"
MAX_RECEIPT_BYTES = 65_536
MAX_TRACKED_INPUT_BYTES = 16 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

EXPECTED_REPOSITORY_INPUTS = {
    "MATHEMATICAL_RESULTS_GUIDE.md": "769b8adae80efa379b3502af9f5edfed839e5a6ac59d08d85e343809e5cf285b",
    "output/pdf/mathematical-results-guide.pdf": "3f8e8196f3dc510eb122926322829f111c1b745fbbf27c920e9606f9a212c200",
    "scripts/build-mathematical-results-guide-pdf.sh": "798f1113a5cc23c24c81412eb8449d8c02023ff3c80a98c698909bcedce2eec1",
    "scripts/check-mathematical-results-guide-pdf.sh": "f7b1cc563e8a8212f6ddcf1c9066f03f83b3705f82779497e22e80e2a5927c23",
    "scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py": "8c477e48db326c60fcde63bfc61ba5be8a903fc4dea329725d96594bde74029e",
    "scripts/check-mathematical-results-guide-pdf-id-variance.py": "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
    "scripts/check-mathematical-results-guide-pdf-id-variance-self-test.py": "757c85a55a8209fb3587e130daf36ab51aac210e87f5604bea40213c62e51c5a",
    "scripts/normalize-mathematical-results-guide-pandoc-tex.py": "401271a933917833e7eca8654bd24e23f42fe19dfeab85c28165815bf55554bf",
    "scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py": "337ffc66888fb8f8f75f8e41429beea7b65fa7370a84695487f81dea4de4d3a0",
    "scripts/check-mathematical-results-guide-builder-self-test.sh": "d7b00e46d982c9a8fdcf2baaa8db54bf51d37d03798b870edd043c590dd5f414",
    "scripts/check-mathematical-results-guide-pdf-structure.py": "50a5ba491a299750af65c14488be478481fbd1a9c779a9c4506a4029d9c4c0b2",
    "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py": "5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997",
    "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence-self-test.py": "07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be",
    "audit/evidence/mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf": "08b0ae8b8c7094cd2a5165563a4e3bd00b22e1d6fdeb658393268cd06525e443",
    "THIRD_PARTY_NOTICES.md": "844a0c542d0ed3ce6af7eb0b0d4560e302963ced6d62da778203c1b953224427",
    "audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt": "cf5b70694cf50403b51f3315f98d010de6435022ff984911819219034a088180",
}

# These two values remain part of the exact capture-time receipt ledger.  They
# are deliberately not read from their current paths: the current wrapper
# binds this legacy package, so a reverse live hash edge would be circular.
HISTORICAL_ROUTING_SNAPSHOT_INPUTS = {
    "scripts/check-mathematical-results-guide-pdf.sh": "f7b1cc563e8a8212f6ddcf1c9066f03f83b3705f82779497e22e80e2a5927c23",
    "scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py": "8c477e48db326c60fcde63bfc61ba5be8a903fc4dea329725d96594bde74029e",
}

LIVE_LEGACY_REPLAY_INPUTS = {
    path: digest
    for path, digest in EXPECTED_REPOSITORY_INPUTS.items()
    if path not in HISTORICAL_ROUTING_SNAPSHOT_INPUTS
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
    "retained_replay_adjudication",
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
    "that the retained replay PDF is either earlier unretained output or an exact reconstruction of the bytes executed in the earlier run",
    "raw strict-structure or raw navigation-digest equality between the retained old-toolchain PDF and the canonical PDF",
    "a generic font-resource alpha-equivalence rule for arbitrary PDFs, sources, fonts, or toolchains",
    "a renderer-equivalence result for the retained replay PDF",
    "a causal explanation for the observed font-resource-name allocation difference",
    "that typed or object-graph equality alone establishes serialized-byte identity, byte ownership, or absence of unreachable bytes",
    "permission to discard or ignore any serialized PDF byte outside the parsed object graph",
    "a generic trailer-ID normalization rule beyond the digest-pinned equal-length strict duplicated final-trailer relation",
    "positive verification credit for the superseded comparator or either witness it incorrectly accepted",
    "independent replay of the superseded comparator's exit-zero acceptances from this receipt alone, because its source bytes and complete execution logs are not retained",
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
        == "historical_unretained_observation_and_superseded_pair_checker_adjudicated_by_a_raw_bound_retained_replay",
        "status changed",
    )
    require(
        document["evidence_class"]
        == "historical operator observation preserved without promotion, one retained replay fixture, two reconstructible pre-commit false-positive witnesses, and a corrected raw-bound then typed source-profile adjudication; the retained PDF is not either earlier unretained output",
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
            "classification": "three disjoint post-observation phases: lint-only typing/import changes, fail-closed shared publication-asset custody wiring, and a later retained old-toolchain replay whose initially typed-only comparator was rejected after adversarial false positives and replaced by a raw-bound then typed source-profile adjudication",
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
                    "current_sha256": "798f1113a5cc23c24c81412eb8449d8c02023ff3c80a98c698909bcedce2eec1",
                    "change": "first rebind the exact trailer-ID checker digest, then stage and verify the shared four-figure publication asset bundle and rebind its exact contract, checker, regenerator, and notice digests; the old execution receives no credit for either source state",
                },
                {
                    "path": "scripts/check-mathematical-results-guide-builder-self-test.sh",
                    "operator_observed_sha256": "c1dc31e97716126c9be137ea8374360968f4138925e93d7e82c756785483b8ab",
                    "current_sha256": "d7b00e46d982c9a8fdcf2baaa8db54bf51d37d03798b870edd043c590dd5f414",
                    "change": "extend the fail-closed builder fixture and staged-input checks to the fourth static publication figure without transferring execution credit from the earlier operator observation",
                },
                {
                    "path": "THIRD_PARTY_NOTICES.md",
                    "operator_observed_sha256": "4279f2628c79bfdc9c226d05c55bf7c643e70b14fa3b03033290f5d91d54ff0d",
                    "current_sha256": "844a0c542d0ed3ce6af7eb0b0d4560e302963ced6d62da778203c1b953224427",
                    "change": "state that the same embedded open-font subset inventory is used by the guide and by the separate SxPID3 source-marginal audit; this is shared rendering custody, not a scientific claim transfer",
                },
            ],
            "retained_replay_adjudication_changes": [
                {
                    "path": "scripts/check-mathematical-results-guide-pdf-structure.py",
                    "pre_adjudication_sha256": "b513404846cdd02048f2e9133ddae927609049fb202956a7cd072ddaff1edf6c",
                    "current_sha256": "50a5ba491a299750af65c14488be478481fbd1a9c779a9c4506a4029d9c4c0b2",
                    "change": "expose the byte-oriented validation result and allow only the two terminal raw manifest-digest comparisons to be deferred by an explicit pair checker; the default command-line and single-PDF strict policy remain unchanged",
                },
                {
                    "path": "scripts/check-mathematical-results-guide-pdf.sh",
                    "pre_adjudication_sha256": "e732b3193b29b5790c9f7b9b43d98752bcf932f18cf123a3477ad9d8530e7f40",
                    "pre_raw_binding_sha256": "e6a506eb21c6759288807c22c6c8e46d7541ea88871687266abf38685fb00dbb",
                    "current_sha256": "f7b1cc563e8a8212f6ddcf1c9066f03f83b3705f82779497e22e80e2a5927c23",
                    "change": "wire the corrected raw-bound then typed pair relation and its hostile suite into the cross-toolchain route while leaving exact mode byte-strict; the earliest before-hash is the C3 pre-adjudication guide-wrapper baseline, not an asserted operator-run input",
                },
                {
                    "path": "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py",
                    "pre_adjudication_state": "absent",
                    "superseded_sha256": "49c768083c2e9e1ff0904da54860e172676098a06249d63812b981495fe5179e",
                    "current_sha256": "5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997",
                    "change": "supersede the typed-only outer gate after exact trailing-byte false positives, then require raw canonical and fixture pins plus exact candidate-to-fixture bytes or the digest-pinned strict duplicated final-trailer ID projection before the source-profiled typed relation",
                    "superseded_disposition": "zero credit; rejected before commit and hosted CI",
                },
                {
                    "path": "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence-self-test.py",
                    "pre_adjudication_state": "absent",
                    "pre_raw_binding_sha256": "76c29b8e80b87bb085be5bd014eaae811633ed31932fafcd97abdaad0a778932",
                    "current_sha256": "07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be",
                    "change": "expand to 134 cases per mode, including permanent raw-boundary trailing-byte hostiles and stronger candidate, dependency, custody, and static wiring controls",
                },
                {
                    "path": "scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py",
                    "pre_adjudication_state": "absent",
                    "pre_raw_binding_sha256": "6eeeebc0c9a07d7a8eb1a60163cbed91410b1a00480d8ad0fb27369a68f70cd5",
                    "current_sha256": "8c477e48db326c60fcde63bfc61ba5be8a903fc4dea329725d96594bde74029e",
                    "change": "expand source-extracted raw-fixture argument and dispatch checks to 11 controls and 15 hostiles while preserving zero alpha-artifact invocations in exact mode and two Python-mode invocations in cross mode",
                },
                {
                    "path": "audit/evidence/mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf",
                    "pre_adjudication_state": "absent",
                    "current_sha256": "08b0ae8b8c7094cd2a5165563a4e3bd00b22e1d6fdeb658393268cd06525e443",
                    "bytes": 581294,
                    "change": "retain one later replay fixture for reproducible adjudication without identifying it as either earlier unretained random-ID output",
                },
            ],
            "credit_boundary": "the earlier operator observation remains bound to its before-digests and receives no transferred credit; the superseded typed-only comparator receives zero verification credit; the corrected retained replay receives only the exact raw-bound then typed PDF-engineering findings in this receipt, and no phase transfers mathematical, statistical, PID, SxPID3, renderer-equivalence, or scientific-novelty credit",
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

    replay = document["retained_replay_adjudication"]
    require(
        replay
        == {
            "scope": "a later old-toolchain replay produced one new retained PDF for adjudication; it does not recover, identify, or authenticate either earlier random-trailer-ID output",
            "retained_pdf": {
                "path": "audit/evidence/mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf",
                "bytes": 581294,
                "sha256": "08b0ae8b8c7094cd2a5165563a4e3bd00b22e1d6fdeb658393268cd06525e443",
                "pages": 16,
                "page_size": "595.276 x 841.89 pt A4",
                "tagged": True,
            },
            "canonical_reference": {
                "path": "output/pdf/mathematical-results-guide.pdf",
                "bytes": 581314,
                "sha256": "3f8e8196f3dc510eb122926322829f111c1b745fbbf27c920e9606f9a212c200",
                "strict_structure_sha256": "e9adba3097ffc38de2f7723e448d2bb54265ee201e010c0857e1a7a40db9d99b",
            },
            "raw_strict_structure_replay": {
                "status": "failed_the_unchanged_strict_structure_digest",
                "retained_structure_sha256": "f7c9ccce59a51f035a474632c8ab2ef21aa7beea76d809bfe5d542ddb21e7dd3",
                "canonical_structure_sha256": "e9adba3097ffc38de2f7723e448d2bb54265ee201e010c0857e1a7a40db9d99b",
                "retained_navigation_sha256": "1699fe16fe5aea765f7fdbffb493158f12da0a06e38d23245f70985b86869103",
                "canonical_navigation_sha256": "95ca1981ffb665ad4f0b9cb72d2ae508f76ae90814669ca910bc41de55aadcf8",
                "navigation_records": 167,
                "differing_navigation_records": 1,
                "navigation_difference": "the sole differing navigation record embeds the unequal raw structure digest",
                "manifest_records": 1699,
                "invariant_records": 1667,
                "differing_records": 32,
                "difference_partition": {
                    "page_content_records": 16,
                    "page_resource_records": 16,
                    "other_records": 0,
                },
                "historical_claim_adjudication": "the retained replay contradicts and supersedes the earlier unretained raw strict-structure pass and raw navigation-digest subclaims; the sole raw navigation difference embeds the structure digest, all other navigation records agree, and the earlier statement remains recorded as operator testimony without replay credit",
            },
            "typed_font_resource_alpha_equivalence": {
                "status": "passed_only_after_raw_candidate_fixture_binding_then_the_source_profiled_typed_pair_check",
                "checker": "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py",
                "reference_precondition": "the canonical PDF first matched the exact pinned raw size and SHA-256 and then passed the unchanged strict single-PDF structure policy",
                "retained_fixture_precondition": "the retained old-toolchain PDF matched its exact pinned raw size and SHA-256 before it could define the exceptional source profile",
                "candidate_precondition": "a noncanonical candidate first matched the retained fixture byte-for-byte or differed only under the digest-pinned strict duplicated final-trailer ID projection on captured equal-length bytes; it then passed the object-graph policy with only the terminal raw structure digest and its embedded navigation record deferred to the exact typed pair check",
                "operational_relation_composition": {
                    "ordered_obligations": [
                        "bind the canonical reference to exactly 581314 raw bytes and SHA-256 3f8e8196f3dc510eb122926322829f111c1b745fbbf27c920e9606f9a212c200",
                        "bind the retained fixture to exactly 581294 raw bytes and SHA-256 08b0ae8b8c7094cd2a5165563a4e3bd00b22e1d6fdeb658393268cd06525e443",
                        "for an exceptional candidate, require exact retained-fixture bytes or equal-length equality after erasing only the strict duplicated 16-byte final-trailer ID payloads with the digest-pinned ID checker",
                        "validate the candidate object graph with only its two terminal source-manifest digest comparisons deferred",
                        "compare every source-profiled typed font-resource, decoded content operation, non-font resource, structure record, and navigation record under the one admitted font-key rename",
                    ],
                    "strict_trailer_id_checker": "scripts/check-mathematical-results-guide-pdf-id-variance.py",
                    "strict_trailer_id_checker_sha256": "d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7",
                    "candidate_raw_relations": [
                        "byte-exact retained fixture",
                        "equal-length strict retained-fixture trailer-ID projection",
                    ],
                    "typed_core_boundary": "the typed font-resource core is a lower-layer relation only; by itself it says nothing about serialized-byte ownership, unreachable trailing bytes, exact source-fixture identity, or trailer-ID scope",
                },
                "pages": 16,
                "parsed_content_operations": 16362,
                "Tf_uses": 1373,
                "page_font_bindings": 122,
                "document_font_mappings": 13,
                "font_name_relation": "each retained-candidate /Fn maps bijectively to canonical /F(n+8)",
                "mapping_manifest_sha256": "364091c0d0e4a023f1335b58c833383569d0b1968bbec26bd77fa26c4a116488",
                "current_pair_check_modes": ["normal Python", "optimized Python"],
                "current_pair_check_mode_relation": "both corrected comparator modes returned success with identical source-profile counts and hashes for a separate byte-exact candidate copy of the retained fixture; raw_relation was byte-exact retained fixture",
                "fail_closed_self_test": {
                    "path": "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence-self-test.py",
                    "modes": ["normal Python", "optimized Python"],
                    "total_cases_per_mode": 134,
                    "controls": 11,
                    "semantic_hostiles": 36,
                    "source_profile_hostiles": 9,
                    "raw_boundary_hostiles": 10,
                    "structure_hostiles": 10,
                    "custody_hostiles": 28,
                    "dependency_hostiles": 10,
                    "static_guards": 20,
                },
                "wrapper_mode_wiring_self_test": {
                    "wrapper": "scripts/check-mathematical-results-guide-pdf.sh",
                    "path": "scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py",
                    "modes": ["normal Python", "optimized Python"],
                    "controls": 11,
                    "hostile_mutations": 15,
                    "exact_mode_alpha_artifact_invocations": 0,
                    "cross_mode_alpha_python_invocations": 2,
                    "boundary": "source-extracted dispatch and wrapper custody only; the renderer and typed PDF relation remain obligations of separate gates",
                },
                "typed_object_graph_admitted_difference_after_raw_precondition": "after the separate candidate-to-retained raw-byte precondition passes, the only admitted canonical-to-candidate typed/object-graph difference is the font resource-key rename used as Tf operands and as keys in page Font dictionaries; the serialized trailer-ID relation belongs only to the preceding raw lane",
                "exactly_preserved": [
                    "before typed comparison, every serialized candidate byte equals the retained fixture except the two strict duplicated 16-byte final-trailer ID payloads when that explicit projection is used; candidate length cannot change",
                    "the complete typed font-resource closure for every mapped font, including embedded font bytes, BaseFont identity, ToUnicode data, and object topology",
                    "every decoded page-content byte after substituting only independently parsed Tf font-name operands",
                    "every content operation, operation order, non-font operand, and Tf size",
                    "every non-font resource and all 1667 nonvariant structure-manifest records",
                    "all navigation records except the one record that embeds the raw structure digest; the canonical navigation record is emitted only after the pair passes",
                ],
                "scope_boundary": "one exact canonical-reference hash, one exact retained-fixture hash, and captured exceptional candidate bytes satisfying one of two exact raw relations before the typed relation; not a generic PDF normalization or toolchain-equivalence rule",
            },
            "superseded_comparator_negative_evidence": {
                "disposition": "zero credit; discovered and rejected before commit and hosted CI",
                "superseded_checker_sha256": "49c768083c2e9e1ff0904da54860e172676098a06249d63812b981495fe5179e",
                "failure_mode": "the operational CLI enforced the typed and object-graph relation without first binding the complete serialized candidate bytes to the retained fixture; the PDF parser ignored unreachable trailing bytes, so typed-core success alone produced false positives",
                "exact_mode_impact": "none; exact mode remained raw byte-strict and did not invoke the alpha-artifact route",
                "evidence_custody_boundary": "the predecessor SHA and role, exact reconstructible witness bytes, resulting sizes and hashes, and independently observed exit-zero success dispositions are recorded; the predecessor source bytes and complete execution logs are not retained, so this receipt alone cannot replay the old acceptance",
                "witness_base": {
                    "path": "audit/evidence/mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf",
                    "bytes": 581294,
                    "sha256": "08b0ae8b8c7094cd2a5165563a4e3bd00b22e1d6fdeb658393268cd06525e443",
                },
                "reconstruction": "concatenate each exact suffix byte string to the exact witness-base bytes; separate witness files are unnecessary and are not tracked",
                "actual_cli_false_positives": [
                    {
                        "label": "one trailing line-feed byte",
                        "suffix_hex": "0a",
                        "suffix_bytes": 1,
                        "witness_bytes": 581295,
                        "witness_sha256": "cf26eceac81872d9564d8655ce0837bec823e551d03235d5595349ac0d4ece93",
                        "superseded_cli_exit_code": 0,
                        "superseded_cli_stdout_disposition": "emitted the comparator's normal OK success disposition",
                        "observed_disposition": "incorrectly accepted through the actual operational CLI",
                    },
                    {
                        "label": "trailing unreachable PDF comment",
                        "suffix_utf8": "\n% adversarial unreachable trailing comment\n",
                        "suffix_hex": "0a2520616476657273617269616c20756e726561636861626c6520747261696c696e6720636f6d6d656e740a",
                        "suffix_bytes": 44,
                        "witness_bytes": 581338,
                        "witness_sha256": "5e54b2e03dc5427248818474c2d6dbfd2b49c4ab5c23c24cf20d80eed6acde7c",
                        "superseded_cli_exit_code": 0,
                        "superseded_cli_stdout_disposition": "emitted the comparator's normal OK success disposition",
                        "observed_disposition": "incorrectly accepted through the actual operational CLI",
                    },
                ],
                "correction": {
                    "current_checker_sha256": "5a07012129960b8db96d77f292fa21a5ff67cdc79103bef23c0826bf00e2e997",
                    "current_result_for_both_witnesses": "rejected at the candidate raw-profile boundary before typed comparison",
                    "permanent_raw_boundary_hostiles": [
                        "candidate trailing newline",
                        "candidate trailing comment",
                    ],
                    "regression_scope": "the corrected suite reconstructs the exact one-line-feed witness and an analogous unreachable trailing-comment witness and requires current CLI rejection; it cannot replay the predecessor acceptance without the absent predecessor source",
                    "self_test_sha256": "07f73bf9e2b027f5d50bcb3bd7c4ff5f8a7a4c1fb81f807af79387e3f962c5be",
                },
            },
            "historical_record_preserved": [
                "final_run_observation, operator_reported_complete_gate_run, and operator_reported_poppler_comparison remain the exact earlier unretained claims and measurements rather than being silently rewritten as retained evidence",
                "the retained PDF is a later replay fixture and is not claimed to equal, recreate, or descend byte-for-byte from either historical output",
                "the earlier ID-only repeated-build relation and raster comparison remain operator-reported observations; this retained replay neither promotes nor disproves them",
                "the superseded typed-only comparator and both actual-CLI false positives remain reconstructible zero-credit negative evidence rather than being hidden by the correction",
            ],
            "current_engineering_boundary": "this adjudication concerns source-specific PDF build and verification engineering only; it establishes no PID identity, estimator property, mathematical theorem, statistical result, or scientific novelty",
        },
        "retained-replay adjudication changed",
    )
    retained = replay["retained_pdf"]
    canonical = replay["canonical_reference"]
    require(
        EXPECTED_REPOSITORY_INPUTS[retained["path"]] == retained["sha256"],
        "retained-PDF ledger binding changed",
    )
    require(
        EXPECTED_REPOSITORY_INPUTS[canonical["path"]] == canonical["sha256"],
        "canonical-PDF ledger binding changed",
    )
    raw = replay["raw_strict_structure_replay"]
    partition = raw["difference_partition"]
    require(
        raw["manifest_records"] == raw["invariant_records"] + raw["differing_records"]
        and raw["differing_records"] == sum(partition.values()),
        "retained structure census is arithmetically inconsistent",
    )
    require(
        raw["retained_structure_sha256"] != raw["canonical_structure_sha256"],
        "retained raw structure mismatch was erased",
    )
    require(
        raw["retained_navigation_sha256"] != raw["canonical_navigation_sha256"]
        and raw["differing_navigation_records"] == 1,
        "retained raw navigation mismatch was erased or widened",
    )
    require(
        raw["canonical_structure_sha256"]
        == canonical["strict_structure_sha256"]
        == final["structure_sha256"]
        and raw["canonical_navigation_sha256"] == final["navigation_sha256"],
        "canonical structure/navigation cross-binding changed",
    )
    alpha = replay["typed_font_resource_alpha_equivalence"]
    composition = alpha["operational_relation_composition"]
    require(
        EXPECTED_REPOSITORY_INPUTS[composition["strict_trailer_id_checker"]]
        == composition["strict_trailer_id_checker_sha256"],
        "strict trailer-ID dependency binding changed",
    )
    alpha_test = alpha["fail_closed_self_test"]
    require(
        alpha_test["total_cases_per_mode"]
        == sum(
            alpha_test[key]
            for key in (
                "controls",
                "semantic_hostiles",
                "source_profile_hostiles",
                "raw_boundary_hostiles",
                "structure_hostiles",
                "custody_hostiles",
                "dependency_hostiles",
                "static_guards",
            )
        ),
        "font-alpha self-test census is arithmetically inconsistent",
    )
    wiring = alpha["wrapper_mode_wiring_self_test"]
    require(
        wiring["exact_mode_alpha_artifact_invocations"] == 0
        and wiring["cross_mode_alpha_python_invocations"] == 2,
        "exact/cross font-alpha dispatch boundary changed",
    )
    require(
        all(
            path in EXPECTED_REPOSITORY_INPUTS
            for path in (
                alpha["checker"],
                alpha_test["path"],
                wiring["wrapper"],
                wiring["path"],
            )
        ),
        "font-alpha validation input binding changed",
    )
    negative = replay["superseded_comparator_negative_evidence"]
    correction = negative["correction"]
    require(
        negative["superseded_checker_sha256"]
        != correction["current_checker_sha256"]
        == EXPECTED_REPOSITORY_INPUTS[alpha["checker"]],
        "superseded/current comparator identity boundary changed",
    )
    require(
        correction["self_test_sha256"]
        == EXPECTED_REPOSITORY_INPUTS[alpha_test["path"]],
        "corrected comparator self-test binding changed",
    )
    require(
        negative["witness_base"]
        == {key: retained[key] for key in ("path", "bytes", "sha256")},
        "negative-evidence witness base differs from the retained fixture",
    )
    require(
        len(negative["actual_cli_false_positives"]) == 2
        and all(
            witness["superseded_cli_exit_code"] == 0
            for witness in negative["actual_cli_false_positives"]
        ),
        "superseded actual-CLI false-positive ledger changed",
    )

    qemu = document["negative_execution_evidence"]
    require(qemu["qemu_signal"] == "SIGSEGV_139" and qemu["credit"] == "none", "QEMU negative evidence changed")
    require_sha(qemu["qemu_core_sha256"], "QEMU core digest")
    retention = document["artifact_retention"]
    require(
        retention
        == {
            "raw_tex_tracked": False,
            "normalized_tex_tracked": False,
            "pre_normalization_pdf_tracked": False,
            "historical_final_old_toolchain_pdf_tracked": False,
            "reason": "the receipt preserves exact reported measurements and hashes while the reproducible source, transform, and gates remain tracked; the historical raw execution artifacts were intentionally not retained, and trailer-ID variance prevents treating either observed PDF as canonical; the separately tracked later replay is not either observed PDF",
        },
        "historical artifact-retention boundary changed",
    )

    require(
        document["recorded_observations"] == EXPECTED_RECORDED_OBSERVATIONS,
        "recorded-observation ledger changed",
    )
    require(document["does_not_establish"] == EXPECTED_NONCLAIMS, "nonclaim ledger changed")


def validate_negative_witness_reconstruction(
    document: dict[str, Any], retained_bytes: bytes
) -> None:
    negative = document["retained_replay_adjudication"][
        "superseded_comparator_negative_evidence"
    ]
    base = negative["witness_base"]
    require(len(retained_bytes) == base["bytes"], "negative-evidence base size changed")
    require(
        hashlib.sha256(retained_bytes).hexdigest() == base["sha256"],
        "negative-evidence base digest changed",
    )
    observed_digests: set[str] = set()
    for index, witness in enumerate(negative["actual_cli_false_positives"]):
        suffix_hex = witness["suffix_hex"]
        require(
            isinstance(suffix_hex, str)
            and suffix_hex == suffix_hex.lower()
            and len(suffix_hex) % 2 == 0,
            f"negative witness {index} suffix hex is not canonical",
        )
        try:
            suffix = bytes.fromhex(suffix_hex)
        except ValueError:
            fail(f"negative witness {index} suffix hex is malformed")
        require(
            suffix.hex() == suffix_hex and len(suffix) == witness["suffix_bytes"],
            f"negative witness {index} suffix binding changed",
        )
        if "suffix_utf8" in witness:
            require(
                witness["suffix_utf8"].encode("utf-8") == suffix,
                f"negative witness {index} UTF-8/hex suffix relation changed",
            )
        reconstructed = retained_bytes + suffix
        digest = hashlib.sha256(reconstructed).hexdigest()
        require(
            len(reconstructed) == witness["witness_bytes"]
            and digest == witness["witness_sha256"],
            f"negative witness {index} reconstruction changed",
        )
        require(digest not in observed_digests, "negative witness digests are not unique")
        observed_digests.add(digest)


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

    require(
        len(EXPECTED_REPOSITORY_INPUTS) == 16
        and len(HISTORICAL_ROUTING_SNAPSHOT_INPUTS) == 2
        and len(LIVE_LEGACY_REPLAY_INPUTS) == 14,
        "legacy snapshot/live input partition changed",
    )
    require(
        all(
            EXPECTED_REPOSITORY_INPUTS.get(path) == digest
            for path, digest in HISTORICAL_ROUTING_SNAPSHOT_INPUTS.items()
        )
        and set(LIVE_LEGACY_REPLAY_INPUTS).isdisjoint(
            HISTORICAL_ROUTING_SNAPSHOT_INPUTS
        )
        and set(EXPECTED_REPOSITORY_INPUTS)
        == set(LIVE_LEGACY_REPLAY_INPUTS)
        | set(HISTORICAL_ROUTING_SNAPSHOT_INPUTS),
        "legacy routing snapshot was changed, promoted, or dropped",
    )
    retained_bytes: bytes | None = None
    for relative, expected in LIVE_LEGACY_REPLAY_INPUTS.items():
        path = ROOT / relative
        data = read_regular(path, MAX_TRACKED_INPUT_BYTES, relative)
        observed = hashlib.sha256(data).hexdigest()
        require(observed == expected, f"repository input digest changed: {relative}")
        if relative == document["retained_replay_adjudication"]["retained_pdf"]["path"]:
            retained_bytes = data
    require(retained_bytes is not None, "retained replay artifact was not checked")
    validate_negative_witness_reconstruction(document, retained_bytes)

    print(
        "OK: historical Pandoc 3.1.3 observation plus raw-bound retained replay adjudication "
        "(translated_x86_64=yes; native_x86_64=no; normalization_deltas=25; "
        "historical_destinations=39; retained_relation=raw-then-typed; "
        "superseded_false_positives=2; retained_pdf=tracked; "
        "legacy_routing_snapshot=closed)"
    )


if __name__ == "__main__":
    main()
