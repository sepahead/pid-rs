#!/usr/bin/env python3
"""Fail closed on KSG revision-4 Git-phase contamination.

This checker binds a bounded Git ancestry envelope and compares the
Git-visible candidate filesystem with the declared scientific baseline.  It is
deliberately a provenance/firewall check, not a numerical or scientific proof.
"""

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
):
    print(
        "ERROR: check-ksg-phase-isolation.py requires Python -I -S",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import argparse
import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, cast


_EXACT_SOURCE_BYTES: bytes | None = globals().pop(
    "__pid_rs_exact_source_bytes__",
    None,
)
SCRIPT_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT_PATH.parent.parent

SCIENTIFIC_BASELINE = "e96122b56c15e895c081379210103d1a26eac25f"
SCIENTIFIC_BASELINE_TREE = "fee2346732da20af0cde32844fcab527ec2d6c4a"
DELIVERY_PARENT = "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"
DELIVERY_PARENT_TREE = "13b15a7564fdd52df16e2e4380f6293db4ea4367"
FORMAL_ANCHOR = "118e1de6a2d6d2ae33fe7bdc224736257e42a83f"
FORMAL_ANCHOR_TREE = "d02ffc69a7045984c1cf58f3adbd39b7e3af0e89"
RECOVERY_ANCHOR = "ca24ab8ebade81a94ffc001531abaf5a5579d5e9"
RECOVERY_ANCHOR_TREE = "82b0aec08c5fd71b6f67d653f05a32f097745a03"
INTEGRATION_ANCHOR = "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c"
INTEGRATION_ANCHOR_TREE = "88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e6f"
M1A_SCIENTIFIC_COMMIT = "dc7b8de0a87443ef2bcde71b19938642f1af2197"
M1A_SCIENTIFIC_TREE = "88b24c0ba4fcad4bd749b9146486143397b6a6eb"
CORRECTIVE_PARENT = "af50935be9ecf9a81aeb30c56b45059652468746"
CORRECTIVE_PARENT_TREE = "ada3860eb696c9a5d634728365acdb5958e7c4e6"
C2_TOOLING_CORRECTION = "8b792bc143fff2d84f2d8e7817d1de7850741223"
C2_TOOLING_CORRECTION_TREE = "8e247b9a6c46fd6266fe4fc02fbe9c3142268215"
CURRENT_ANCHOR = C2_TOOLING_CORRECTION
CURRENT_ANCHOR_TREE = C2_TOOLING_CORRECTION_TREE
PRIOR_PHASE_PATH_POLICY = (
    "audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json"
)
PRIOR_PHASE_PATH_POLICY_SHA256 = (
    "61a54281b492604bdf12bf7ef9b53ab44a773a4fd9dbe9081beb48643a8e07ad"
)
PHASE_PATH_POLICY = (
    "audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json"
)
PHASE_PATH_POLICY_SHA256 = (
    "ffd763b2701c897ed3df75f3f97fe15933c37bf80adcadb0466e9a02113e6359"
)
PACKAGE_STATS_SHA256 = (
    "204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e"
)
PACKAGE_ARCHIVE_SCRIPT_SHA256 = (
    "13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256"
)
PACKAGE_GENERATOR_SHA256 = (
    "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b"
)
HISTORICAL_ECOSYSTEM_METHOD_CATALOG_SHA256 = (
    "1d1f1765209062b8fdc31faed1870de960c53f50ac8d3925a8ac27198aeab313"
)
CURRENT_METHOD_CATALOG_SHA256 = (
    "637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"
)
MAX_POST_ANCHOR_COMMITS = 1
EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256 = (
    "3c092be3206ebdac36f7ca3bac9ae2fb83840cff836dcc79a62602450ab18df3"
)

CORRECTIVE_EVIDENCE = (
    "audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md"
)
PORTABILITY_CORRECTIVE_EVIDENCE = (
    "audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md"
)
PORTABILITY_CORRECTIVE_EVIDENCE_SHA256 = (
    "8c28b1c8bceed4ca5fe9eb66871b9b33db34cf86750cc9eae54058381edb9541"
)
EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256 = (
    "cb4e83dc9ad4f296f1c310f7468e57d84bd6963f86e39d2f1bb1ab259ea19736"
)
C3_REVIEW_BEGIN = "C3_PRECOMMIT_REVIEW_PARITY_BEGIN\n"
C3_REVIEW_END = "\nC3_PRECOMMIT_REVIEW_PARITY_END"
C3_LOCAL_ARTIFACT_BEGIN = "C3_LOCAL_ARTIFACT_PARITY_BEGIN\n"
C3_LOCAL_ARTIFACT_END = "\nC3_LOCAL_ARTIFACT_PARITY_END"
EXPECTED_C3_PRECOMMIT_REVIEW: dict[str, object] = json.loads(
    r"""
{
  "bounded_positive_observations": [
    {
      "candidate_commit": "524a1c6af46698f872dce1a04aa0a281ec025a5e",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN0_PARSER_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "51fbdafb0a24e5763b2842f558bd5dde3bb4aed110a53ed5a5dea26d81ccaea8",
      "stdout_size_bytes": 7063
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN3_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "dacb78d6e533a36ee7fd3a0029ae382ca09e5ea103400a6a67511a450d054633",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": null,
      "candidate_tree": null,
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "normal_stdout_sha256": "22219398cfd1570894009f3a167fce11aa458f5a4b2f5372d3b2806c4099ef9b",
      "normal_stdout_size_bytes": 59,
      "observation_code": "GEN4_ROOT_FOCUSED_NORMAL_OPTIMIZED_34_CASES",
      "optimized_stdout_sha256": "d44046c5f910dad8148a67b3336f733267d45d8303ae02d9ce219cb69c2f246b",
      "optimized_stdout_size_bytes": 62
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN4_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "95b6f8a4a1e88df582a31561ca25199228409c5e1134fc24c1e8c4b0f3f8d46d",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN4_STANDARD_AND_RAW_ALTERNATE_INDEX_TREE_EQUAL",
      "raw_index_sha256": "e62b876f7f674606accea88943e002e7ce223206a948caa162813d0d9ab133c0",
      "standard_index_sha256": "ba6598c187836bb3aaa171ed6df01c238d0e8e2642a684df238d601c751f48c0"
    },
    {
      "case_family": "python_entry_isolation",
      "cases_completed": 18,
      "checker_sha256": "cbb08b17ff09c967a6ac9e49ba071b279e22fb903fe1a75b501973b779edebc8",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "SESSION_56745_ENTRY_ISOLATION_18_CASES_COMPLETE",
      "restoration": "byte_exact_both_sources",
      "self_test_sha256": "0cfd0480721ddce0df533b97ec28082a94202c2a67fd9c0121382466904ebaec",
      "session_id": 56745
    },
    {
      "cases_completed": 34,
      "checker_sha256": "4ccb393e1089faf2f747c8469bc642b00e2323f7e4fd17dc976b1d90289b65c8",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "9a4ec4b7ee663875039fbd996e48732cdae5c1f56592eb9d15ed627ba41b58ca",
      "observation_code": "SESSION_84056_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "receipt_sha256": "73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20",
      "restoration": "byte_exact_five_targets",
      "self_test_sha256": "f2464399e6a497e2fcf1924e63c26c1016f2b49f06cc3392ae7666d8dd7fbad9",
      "session_id": 84056
    },
    {
      "cases_completed": 34,
      "checker_sha256": "b09c842b0c2ac2eb29087ff2581a2a384f28702b14cbbbc0331775c7fbc16cc6",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "ca4c6c29fecbbb2c53fb6366cf9122008e8db16aba1018645b936d6b94508025",
      "observation_code": "SESSION_97473_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE",
      "overlay_path_count": 187,
      "restoration": "five_targets_and_overlay_status",
      "self_test_sha256": "f76c79cd4ea86ff6012c30f6f92d473f04dd0c88a475499cb86e01ada84b2e1c",
      "session_id": 97473
    },
    {
      "candidate_commit": "266760007b59642a6b9e12ad47ce0dffda54be26",
      "candidate_tree": "601f2681bdd88673e658d1b9a6e96de1936c8215",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "FINAL003_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "5d95f7b57b61f82bb1155a85417c46d86a3cf9d1dabc4a5d8427df519c5da9b5",
      "stdout_size_bytes": 645
    },
    {
      "cases_completed": 17,
      "checker_sha256": "710a6124b23ec08bfb492d1c0fbdd1a4ce2d0a5744bccc7dfaa7ac7b51738fd4",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "3984f9438f9b1560db826b03d005d363f94fe619cbff1c290cbe52750f361dc3",
      "modes": [
        "normal",
        "optimized"
      ],
      "observation_code": "FINAL003_LEAN_PORTABILITY_NORMAL_OPTIMIZED_17_CASES",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "restoration": "green_baseline_final_and_candidate_removed",
      "self_test_sha256": "a4d5152f752c8773f9fbceea0d4737a60a22a67696423a9cd709a0fec2c9e120"
    },
    {
      "candidate_commit": "f0515e455d969eafe9a4f260f50341b0a120dc73",
      "candidate_tree": "eac26211c4d76989253ce78ae2e4936d370932e1",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "FINAL004_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stderr_size_bytes": 0,
      "stdout_sha256": "a5e0e7644066968be42a1ee502c3d52fd1338680fcda13390ff41c129fee29c7",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": "f0515e455d969eafe9a4f260f50341b0a120dc73",
      "candidate_tree": "eac26211c4d76989253ce78ae2e4936d370932e1",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "monitor_sha256": "5d093695331e1965c9855f22b5cc26da1ca5820ae0c5c53a78029935c7aa1aa0",
      "monitor_supervisor_lens_count": 47,
      "observation_code": "FINAL004_COMPONENT_REVIEWS_BOUNDED_GO",
      "supervisor_sha256": "498372124947ef06c1d4661b8bf0405d1fcfbb9014448e6dcd300b8fadbf6811",
      "verifier_lens_count": 46,
      "verifier_sha256": "e8e1df74b4c17d665a202ad00a778c2e19a7c011017d1c6fe4231a46eab41576"
    },
    {
      "checker_sha256": "919d1d778d7e805bf1b515ee5f95d21026ce873695d25ac194d2a1d19a084fc5",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "facb2ddaef514536215d9f1e747a1885534ff696bf6ed18145a991b2db4783b6",
      "modes": [
        "normal",
        "optimized"
      ],
      "observation_code": "FINAL004_TARGETED_LAKE_PREFLIGHT_NORMAL_OPTIMIZED",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "restoration": "green_baseline_final_and_candidate_removed",
      "self_test_sha256": "015203dc260a6b845ee0ed11eb5a0edb4a22b9d7c337bde5f3f4072d2550aaa9"
    },
    {
      "checker_sha256": "09d7816ccd2a245c12ac4db99c0e2502e905193208639abc8248a567da82f339",
      "contracted_total": 350,
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "ced18c5406491daccb490be8c1f83a9dc2067035412887810d7569e078acf9b1",
      "normal": {
        "exit_code": 0,
        "pid": 36409,
        "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "stderr_size_bytes": 0,
        "stdout_sha256": "b5c3d3d1eef00b68b90fb3d0f0002b9871d0389ee46f8f8974d4483982f933a3",
        "stdout_size_bytes": 726
      },
      "object_association": "post_hoc_not_atomic",
      "observation_code": "GEN0_FULL_NORMAL_OPTIMIZED_350_CASES_COMPLETE",
      "optimized": {
        "exit_code": 0,
        "pid": 36922,
        "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "stderr_size_bytes": 0,
        "stdout_sha256": "5f6c320dd6391ec6ef9c815fc09362059fdc02e99ade230c294f1d16ae6b77a4",
        "stdout_size_bytes": 729
      },
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "self_test_sha256": "015203dc260a6b845ee0ed11eb5a0edb4a22b9d7c337bde5f3f4072d2550aaa9"
    },
    {
      "additions": 3,
      "cache_info_index_sha256": "e495746989cb1300f4eabdad595bebdf237d48a8901b92c938960901830075cf",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "executable_path_count": 3,
      "explicit_root_index_sha256": "1f50af9e3eba8d7a01025e029c8320dd34fc267403f2377accffb28e2b891c39",
      "modifications": 16,
      "observation_code": "GEN0_THREE_ALTERNATE_INDEX_RECONSTRUCTIONS_EQUAL",
      "path_count": 19,
      "route_count": 3
    },
    {
      "candidate_commit": "524a1c6af46698f872dce1a04aa0a281ec025a5e",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "normal_exit_code": 0,
      "observation_code": "GEN0_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "optimized_exit_code": 0,
      "stderr_size_bytes": 0,
      "stdout_sha256": "20b5845d1442c8317c027a41d48af128ae79b569bb1f2d769e74d1bf782901a4",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
      "candidate_tree": "75efda476f15da6a82b3e006d0989196436d1a4f",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "normal_exit_code": 0,
      "observation_code": "GEN1_DIRECT_NORMAL_OPTIMIZED_ACCEPTED",
      "optimized_exit_code": 0
    },
    {
      "credit": "bounded_design_only",
      "event_class": "bounded_design_positive_no_runtime_credit",
      "live_process_families": [
        "crlf_stdout",
        "cr_stderr",
        "invalid_utf8_stdout",
        "invalid_utf8_stderr",
        "invalid_utf8_plus_cr_stdout_cr_before_decode"
      ],
      "observation_code": "RAW_TRANSPORT_FIVE_FAMILY_STATIC_DESIGN_GO",
      "phase_subcontrols": [
        "evidence_count_corruption",
        "text_mode_reintroduction",
        "cr_rejection_deletion",
        "permissive_decoding",
        "precedence_reversal_with_repaired_inner_custody",
        "declared_observed_payload_divergence"
      ],
      "review_sha256": "5771a95476c881c9550eedad8f996a71bc5d7783a20d84905bf5b3d33dde82b2",
      "review_size_bytes": 7904,
      "runtime_credit": false
    }
  ],
  "negative_observations": [
    {
      "candidate_commit": "524a1c6af46698f872dce1a04aa0a281ec025a5e",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "claimed_parser_sha256": "51fbdafb0a24d979695c8fa22ccb9c7e4e444273866635424c378e3041c06c42",
      "credit": "none",
      "event_class": "repository_custody_defect",
      "executed_parser_sha256": "51fbdafb0a24e5763b2842f558bd5dde3bb4aed110a53ed5a5dea26d81ccaea8",
      "reason_code": "GEN0_FALSE_PARSER_DIGEST_AND_ABSENT_FULL_STDOUT_BINDING"
    },
    {
      "actual_inventory": [
        296,
        40,
        331
      ],
      "candidate_commit": "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
      "candidate_tree": "75efda476f15da6a82b3e006d0989196436d1a4f",
      "claimed_inventory": [
        294,
        40,
        329
      ],
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "reason_code": "GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED",
      "stderr_sha256": "7829719b5026a2130c0cbf20ce40c14ed0c3f5f7af91a1b0212a3b55aeef72a9",
      "stderr_size_bytes": 99
    },
    {
      "candidate_commit": "0a2d7c6519ab3d16f8a5dee335409611b53ec574",
      "candidate_tree": "94ebbfc74f98e6899771907a042579a39416b615",
      "credit": "none",
      "event_class": "repository_custody_defect",
      "exit_code": 1,
      "memo_sha256": "dd5bd7a6c29bc158721617628fccfe1d5046b02bec49f9a7e369ec5cc74d98bd",
      "reason_code": "GEN2_TOP_LEVEL_MEMO_PIN_STALE_AFTER_BLOB_REPIN",
      "stale_top_level_sha256": "e25873fa9d3330adac390686a00e76aad57640b7dc19b9c51e98ada7077ad179",
      "stderr_sha256": "40bb691745229ea18fb2ad97f5e486add99a0e476c9ab09d1db6980c32c14fc7",
      "stderr_size_bytes": 91
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "reason_code": "GEN3_CORRELATED_MEMO_INVENTORY_MUTANT_INADEQUATE"
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "reason_code": "GEN3_NORMAL_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION",
      "session_id": 76847,
      "terminal_stage": "policy_authority"
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "reason_code": "GEN3_OPTIMIZED_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION",
      "session_id": 1091,
      "terminal_stage": "policy_authority"
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "GEN4_INDEPENDENT_OPTIMIZED_FOCUSED_RUN_ABORTED_FOR_SERIALIZATION",
      "temporary_clone_recoverable_from_trash": true,
      "terminal_receipt_retained": false
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "reason_code": "GEN4_ROOT_NORMAL_FULL_SUITE_OVERLAPPED_FOCUSED_REVIEW",
      "session_id": 15609,
      "terminal_stage": "python_entry_attacks"
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 1,
      "reason_code": "GEN3_CONCURRENT_PDF_LEAN_VERSION_TIMEOUT_NO_CREDIT",
      "stderr_sha256": "168c1cd6c29375235f849b65770ee33cc8d3e01ada4f3426492273f5216ee203",
      "stderr_size_bytes": 136
    },
    {
      "candidate_commit": "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
      "candidate_tree": "75efda476f15da6a82b3e006d0989196436d1a4f",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "path": "/private/tmp/pid-rs-c3-corrected.XXXXXX.index",
      "reason_code": "GEN1_PREDICTABLE_BSD_MKTEMP_TEMPLATE_REJECTED"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "GEN1_RUFF_MECHANICAL_REFLOW_RESTORED_BEFORE_CANDIDATE"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "V8_REVIEW_TRACKED_RESUME_APPEND_RESTORED_BEFORE_CANDIDATE",
      "restored_sha256": "5c21a28fe935a689b445004fcacb22395f6cc783e422d290fb157fe0906f3911",
      "transient_append_sha256": "f902596b2d8276c09fe0f1f5479fc2ea7735b480587079c6d6bc9edcb4e88f55"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 1,
      "reason_code": "PRE_OBJECT_REVIEW_LEDGER_NONCANONICAL_PRETTY_JSON",
      "stderr_sha256": "a4e63b5d3c482acf4331e27e24f78398fbbef9a21718f80b40fdc1f68ac16296",
      "stderr_size_bytes": 118
    },
    {
      "checker_sha256": "2359ecade1447da49fd3e809de36191c4f285d1faad65dc084df77a18cae18b8",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "Python isolation preamble changed: scripts/check-ksg-phase-isolation.py",
      "reason_code": "SESSION_86029_ENTRY_ISOLATION_EXPECTATION_ORDER",
      "self_test_sha256": "37c067f931bcbc38e89a281a36a2b7b1c9d2b07f2d86fa065eee093d632337a2",
      "session_id": 86029,
      "terminal_result": "stopped_on_first_mutation"
    },
    {
      "checker_sha256": "b337be07077b9567ea313b428f76aaec38d2481d94336d2b894bef90eebf5375",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "precursor_result": "missing_sys_modules_registration_attribute_error_before_mutation",
      "reason_code": "SESSION_56566_ENTRY_MUTATION_DELIMITER_AMBIGUOUS",
      "self_test_sha256": "2c5e22ff98aafcbbec8e4ab219057058d95a470a1a6472387c067a9e457b666b",
      "session_id": 56566,
      "terminal_result": "stopped_before_second_mutation_nonunique_if_not_delimiter"
    },
    {
      "checker_sha256": "67c5598284712b46df5d7c705f0474b282b672c8a40b40b96b21afcc25ce068d",
      "completed_preamble_mutations": 4,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "child Python command lacks exact -I -S prefix: scripts/check-ksg-phase-isolation.py",
      "reason_code": "SESSION_3174_CHILD_COMMAND_EXPECTATION_ORDER",
      "self_test_sha256": "3fde8666956ec4cca29987e461a7362560dff9e87b927277b413dea1832b4ebd",
      "session_id": 3174,
      "terminal_result": "stopped_on_first_child_command_mutation"
    },
    {
      "checker_sha256": "2714d37d374eb94f54cd0c358f633ec6e7fa29a8ed9d7a40befa015c3915c655",
      "completed_entry_mutations": 16,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "candidate anchor delta differs from the separately reviewed A/M path policy",
      "reason_code": "SESSION_27678_TOOL_README_ANCHOR_ORDER",
      "self_test_sha256": "674642ab33e838babc1f8e2f86716590f86a85318e3c29b52acfdd65c31698d1",
      "session_id": 27678,
      "terminal_result": "stopped_on_seventeenth_tool_readme_mutation"
    },
    {
      "checker_sha256": "0151ff6813ed359ec850df2c83dc1f21ceebb485d9f8291262b2e7f5f5e5faf5",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "phase path policy historical remediation supersession value changed at $/historical_receipt_sha256",
      "reason_code": "SESSION_62196_PORTABILITY_DUPLICATE_KEY_STALE_POLICY",
      "self_test_sha256": "0cfd0480721ddce0df533b97ec28082a94202c2a67fd9c0121382466904ebaec",
      "session_id": 62196,
      "terminal_result": "stopped_at_portability_receipt_duplicate_key"
    },
    {
      "contaminating_command": "git -C /var/folders/5w/54mv55g13yq4x_7w3ld2csb40000gn/T/pid-rs-ksg-phase-self-test.rwuan5k5/candidate status --short",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "last_pre_failure_elapsed": "01:07:26",
      "observed_detail": "Git executable, configuration, metadata, or visibility context changed during replay",
      "parent_pid": 92493,
      "reason_code": "SESSION_55661_CONTAMINATED_BY_IN_CLONE_GIT_PROBE",
      "session_id": 55661,
      "terminal_elapsed_retained": false
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "parent_pid": 22724,
      "reason_code": "SESSION_74678_PRIOR_SNAPSHOT_INVALIDATED_AND_STOPPED",
      "session_id": 74678,
      "stop_signal": "SIGINT",
      "terminal_stage": "run_public_ci_portability_evidence_attacks",
      "terminal_time_retained": false
    },
    {
      "checker_sha256": "741a2ceb0f7924784a8b24005c065d0d0b8f42142c9e49a99008c6d9d6ac0ab8",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "memo_sha256": "6da138c09e79191d565e9092dc6429561095da82899d5b567e82fabceb83b12f",
      "observed_detail": "mutation anchor count is not 2",
      "reason_code": "SESSION_54874_MEMO_ANCHOR_CARDINALITY_STALE",
      "restoration_green_replay_reached": false,
      "self_test_sha256": "f2464399e6a497e2fcf1924e63c26c1016f2b49f06cc3392ae7666d8dd7fbad9",
      "session_id": 54874,
      "terminal_stage": "portability_receipt_duplicate_key"
    },
    {
      "actual_attribute": "SELF_RELATIVE",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "hostile_family_executed": false,
      "invocation": "python3 -B -I -S -",
      "reason_code": "SESSION_51446_WRONG_SELF_TEST_ATTRIBUTE",
      "requested_attribute": "SELF_TEST_RELATIVE",
      "session_id": 51446,
      "terminal_result": "exited_before_disposable_clone"
    },
    {
      "checker_sha256": "b6648e836cb9fea805c2f7892107c4abc790db092e2df7b9ab242c58366e6fa8",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exact_elapsed_retained": false,
      "memo_sha256": "42541915305928006faa54facd5d7964f7e8e074e5819d97dcc78e60a10c3406",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "reason_code": "SESSION_8070_TERMINAL_RECEIPT_UNRECOVERED",
      "self_test_sha256": "f76c79cd4ea86ff6012c30f6f92d473f04dd0c88a475499cb86e01ada84b2e1c",
      "session_id": 8070,
      "terminal_exit_code_retained": false,
      "terminal_result": "unknown",
      "terminal_stderr_retained": false,
      "terminal_stdout_retained": false
    },
    {
      "candidate_commit": "ffbd24e668a57e8c8c20714998aa27c27085b3c2",
      "candidate_tree": "fbcc8b68cf04caa44555313eb2ecda252a47a7e5",
      "credit": "none",
      "event_class": "candidate_supersession",
      "pushed": false,
      "reason_code": "TREE_FBCC_CHECKPOINT_FFBD_INVALIDATED_AFTER_WRITER",
      "result": "invalidated_after_writer_update"
    },
    {
      "candidate_commit": "7e2812bd6d0b14234325b3ecd065017bec487d2a",
      "candidate_tree": "229e24f3614b9e7fdd28d90cc291c6e6be2ce5f2",
      "credit": "none",
      "event_class": "candidate_supersession",
      "pushed": false,
      "reason_code": "TREE_229E_CHECKPOINT_7E_TRAILING_WHITESPACE",
      "result": "git_diff_check_rejected",
      "trailing_space_count": 2
    },
    {
      "candidate_commit": "c896731c74534417e2de8636d6faa58ab2a54f70",
      "candidate_tree": "6f6ea30c77b6cb92cbcd01770a167b467a6b546b",
      "credit": "none",
      "event_class": "candidate_supersession",
      "observed_detail": "candidate changed-byte projection digest mismatch",
      "reason_code": "TREE_6F6E_CHECKPOINT_C896_CHANGED_PROJECTION_STALE",
      "result": "rejected_before_projection_regeneration"
    },
    {
      "candidate_tree": "f306fd04b0c2ac19ed06f513ed0e183af4fe688f",
      "commit_reported": false,
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "TREE_F306_EXECUTABLE_MODES_STRIPPED",
      "stripped_executable_path_count": 3
    },
    {
      "candidate_commit": "266760007b59642a6b9e12ad47ce0dffda54be26",
      "candidate_tree": "601f2681bdd88673e658d1b9a6e96de1936c8215",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "expected_pairwise_hash_cardinality": 20,
      "final_directory_created": false,
      "mutation": "lean-portability-self-test-hostile-inventory-reduced",
      "observed_pairwise_hash_cardinality": 21,
      "reason_code": "FINAL003_SELFTEST_WRONG_REASON",
      "stderr_sha256": "04f4450c545184139f7b3cdbfd1a8cbd7832f7285262f39a0ef13a1b2ac3d5c0",
      "stderr_size_bytes": 423,
      "stdout_size_bytes": 0
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "hostile_cases_executed": 0,
      "reason_code": "FINAL004_PRELIMINARY_CLONE_MODES_0600",
      "result": "checker_rejected_immediately_and_clones_discarded",
      "substituted_mode": "0600"
    },
    {
      "candidate_commit": "f0515e455d969eafe9a4f260f50341b0a120dc73",
      "candidate_tree": "eac26211c4d76989253ce78ae2e4936d370932e1",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "mutation": "foundational-paper-lake-preflight-removal",
      "reason_code": "FINAL004_SELFTEST_WRONG_REASON",
      "stderr_sha256": "7e5863cc8c11510e700af440b487b83e712b3d5ed9740677877e0998838ede2d",
      "stderr_size_bytes": 304,
      "stdout_size_bytes": 0
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "none",
      "event_class": "candidate_supersession",
      "promotion_prohibited": [
        "tree",
        "commit",
        "direct_run",
        "focused_run",
        "interrupted_full_run"
      ],
      "reason_code": "GEN4_SUPERSEDED_BEFORE_PUSH",
      "result": "superseded_and_rejected_before_push"
    },
    {
      "accepted_advertising_variant_count": 4,
      "accepted_false_green_count": 2,
      "candidate_entry": false,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "pushed": false,
      "reason_code": "COMMIT_ENVELOPE_CLASSIFIER_FALSE_GREEN_FALSE_POSITIVE_SEQUENCE",
      "rejected_legitimate_control_count": 3
    },
    {
      "concurrent_custody_invalidated": true,
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "initial_cache_file_count": 6,
      "reason_code": "LOCAL_PRESEAL_SIDE_EFFECTS_INVALIDATED_CUSTODY",
      "recorder_attack_count": 2,
      "recreated_phase_cache_count": 2,
      "restoration": "bytes_and_modes_restored_but_mtimes_changed"
    },
    {
      "audit_snapshot": {
        "descriptor_checker": {
          "sha256": "6f99ea81c8860e379a4b4e839900dd79d67b3f0cb7db8982ac54ee3ac1c9badb",
          "size_bytes": 40131
        },
        "descriptor_self_test": {
          "checker_pinned_sha256": "30a845e0142375c460142b7895a582029fc62d691561b60297fcdd2693e66f91",
          "sha256": "0ad1b86311bebaaf595a9d7f4eb4925b31f1ca53ca2657b3cd928d73c9389745",
          "size_bytes": 75984
        },
        "direct_evidence": {
          "internal_checker_sha256": "ec76cc1967ee86bb97be580ee7720b217111811602143ed4518a13fe90ecb0be",
          "schema_revision": 3,
          "sha256": "1b72971ba5343fce8e7d08b7a766515ef208a4643905ae2602c16161efa5f50d",
          "size_bytes": 2812
        },
        "memo": {
          "sha256": "ba75bb108327bc59e932417fdfec3b1de1ffa2d24c71c17d84545023a6dab06a",
          "size_bytes": 78065
        },
        "mutation_evidence": {
          "internal_checker_sha256": "ec76cc1967ee86bb97be580ee7720b217111811602143ed4518a13fe90ecb0be",
          "internal_self_test_sha256": "2bfdeba054e95f326e52a2b413f1485c4f1fea04abae6240501224b522e1c1f3",
          "schema_revision": 3,
          "sha256": "637e3748f2ce3f9f6572337f82cdc629d45c7b4046d56ff69255554b2c571f00",
          "size_bytes": 7992
        },
        "parser_pair": {
          "bound_self_test_sha256": "30a845e0142375c460142b7895a582029fc62d691561b60297fcdd2693e66f91",
          "sha256": "20a0ca2966488ba6539e2a80a98164586d907086555e55f7847f95dfe939cd7f",
          "size_bytes_each": 7968
        },
        "policy": {
          "checker_pinned_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
          "sha256": "45583edafc24b0bad291ff25dc380bb995e1898bbef7516799dda918e9fb75d3",
          "size_bytes": 13180
        }
      },
      "credit": "none",
      "event_class": "repository_custody_defect",
      "reason_code": "C3_SOURCE_GENERATION_SPLIT"
    },
    {
      "credit": "none",
      "event_class": "repository_custody_defect",
      "previous_run_credit": false,
      "reason_code": "LOCAL_ARTIFACT_MEMO_PARITY_UNBOUND",
      "unbound_claim_fields": [
        "direct_evidence_size",
        "direct_evidence_sha256",
        "mutation_evidence_size",
        "mutation_evidence_sha256",
        "current_pdf_size",
        "current_pdf_sha256"
      ]
    },
    {
      "actual_code_substitution_count": 18,
      "base_negative_count": 13,
      "base_positive_count": 5,
      "base_projection_sha256": "2f18fbf1fda9cfdec1dd9ab58289bafe3d95293111f30174fdfd39098ef045fb",
      "base_projection_size_bytes": 5935,
      "base_total_count": 18,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "missing_named_session_ids": [
        3174,
        8070,
        27678,
        51446,
        54874,
        55661,
        56566,
        56745,
        62196,
        74678,
        84056,
        86029,
        97473
      ],
      "missing_object_ids": [
        "229e24f3614b9e7fdd28d90cc291c6e6be2ce5f2",
        "266760007b59642a6b9e12ad47ce0dffda54be26",
        "601f2681bdd88673e658d1b9a6e96de1936c8215",
        "6f6ea30c77b6cb92cbcd01770a167b467a6b546b",
        "7e2812bd6d0b14234325b3ecd065017bec487d2a",
        "c896731c74534417e2de8636d6faa58ab2a54f70",
        "eac26211c4d76989253ce78ae2e4936d370932e1",
        "f0515e455d969eafe9a4f260f50341b0a120dc73",
        "f306fd04b0c2ac19ed06f513ed0e183af4fe688f",
        "fbcc8b68cf04caa44555313eb2ecda252a47a7e5",
        "ffbd24e668a57e8c8c20714998aa27c27085b3c2"
      ],
      "reason_code": "REVIEW_LEDGER_COMPLETENESS_AND_TYPED_VALIDATION_GAP",
      "self_test_comment_claimed_row_count": 17
    },
    {
      "credit": "none",
      "event_class": "repository_custody_defect",
      "live_copy_route": "clone_candidate_shutil_copy2_after_fact_emission",
      "path_loaded_routes": [
        "run_checker",
        "current_facts",
        "generated_block"
      ],
      "reason_code": "CANDIDATE_EXACT_SOURCE_AND_OVERLAY_CAPTURE_GAP",
      "top_level_loader_closed": false
    },
    {
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "pre_repair_report_sha256": "233ffd12855e08c4e43d041bf28393141f53c05980451df34b5426aa6b68bdf5",
      "reason_code": "RAW_TRANSPORT_TEXT_MODE_NORMALIZATION_GAP",
      "subprocess_text_mode": true,
      "universal_newline_transformations": [
        "crlf_to_lf",
        "cr_to_lf"
      ]
    },
    {
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "reason_code": "RAW_TRANSPORT_FOUR_CASE_STATIC_REVIEW_NO_GO",
      "review_disposition": "NO_GO",
      "review_sha256": "0f962513e6ae650de165b4205aada4f74c93b1cd1954b76a3936013ffd45ca62"
    },
    {
      "credit": "none",
      "event_class": "repository_publication_defect",
      "findings": [
        "page_11_splits_PidDescriptorFactorization.lean",
        "page_12_splits_witness.py",
        "json_path_73_characters_protrudes_about_2.1_pt",
        "rust_regression_digest_orphaned_ed_semicolon_suffix"
      ],
      "no_observed_clipping_or_overlap": true,
      "pdf_pages": 16,
      "pdf_sha256": "56551da7dd2d72ca01502d20384021329732fea10ec6ab7ac43cfaa651552502",
      "pdf_size_bytes": 358685,
      "reason_code": "PDF_FOUR_CONFIRMED_TYPOGRAPHY_FINDINGS",
      "review_sha256": "54cbbea456e54376781b0c9d0d44eb634ec8d22d27a3e8fd66499b43916d983e",
      "review_size_bytes": 8814
    },
    {
      "approximate_clearance_pt": 144.5,
      "credit": "none",
      "event_class": "review_hypothesis_falsified",
      "is_defect": false,
      "reason_code": "PDF_TOC_CROWDING_SUSPICION_FALSIFIED"
    },
    {
      "credit": "none",
      "e402_finding_count": 53,
      "event_class": "reviewer_tool_process_negative",
      "formatter_file_change_count": 5,
      "reason_code": "RUFF_E402_CUSTODY_GUARD_POLICY_MISMATCH",
      "repository_c3_gate": false,
      "ruff_version": "0.15.18"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exact_refetch_sha256": "f197b00e992f58f00695b68315e1864937f886e47f1823208d3ca177a716f087",
      "exact_refetch_size_bytes": 78318,
      "job_id": 90509073372,
      "partial_sha256_retained": false,
      "partial_size_retained": false,
      "reason_code": "GITHUB_JOB_LOG_PARTIAL_FETCH_TIMEOUT_THEN_EXACT_REFETCH"
    },
    {
      "corrected_parse_completed": true,
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exception_type": "KeyError",
      "parser_receipts_affected": false,
      "reason_code": "LEAN_JSON_NONEXISTENT_KEY_THEN_CORRECT_PARSE",
      "wrong_key_spelling_retained": false
    },
    {
      "command": "/opt/homebrew/bin/lake env lean --version",
      "credit": "none",
      "descriptor_theorem_credit": false,
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "DESCRIPTOR_HELP_LAKE_VERSION_TIMEOUT",
      "timeout_seconds": 60
    },
    {
      "credit": "none",
      "download_rate_kib_per_second_range": [
        50,
        100
      ],
      "elan_download_stopped_near_mib": 75,
      "elan_download_total_mib": 524.6,
      "event_class": "reviewer_tool_process_negative",
      "lake_version_line_produced": false,
      "lake_version_route_terminated_seconds": 2521.35,
      "lean_failure": false,
      "orphaned_lake_pid": 59119,
      "reason_code": "LOCAL_LAKE_ROUTING_STALL_AND_ABORTED_ELAN_DOWNLOAD"
    }
  ],
  "parent": "8b792bc143fff2d84f2d8e7817d1de7850741223",
  "schema": "pid-rs/c3-precommit-review-ledger",
  "schema_revision": 2
}
"""
)
EXPECTED_C3_POSITIVE_CODES = (
    "GEN0_PARSER_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
    "GEN3_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
    "GEN4_ROOT_FOCUSED_NORMAL_OPTIMIZED_34_CASES",
    "GEN4_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
    "GEN4_STANDARD_AND_RAW_ALTERNATE_INDEX_TREE_EQUAL",
    "SESSION_56745_ENTRY_ISOLATION_18_CASES_COMPLETE",
    "SESSION_84056_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE",
    "SESSION_97473_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE",
    "FINAL003_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
    "FINAL003_LEAN_PORTABILITY_NORMAL_OPTIMIZED_17_CASES",
    "FINAL004_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
    "FINAL004_COMPONENT_REVIEWS_BOUNDED_GO",
    "FINAL004_TARGETED_LAKE_PREFLIGHT_NORMAL_OPTIMIZED",
    "GEN0_FULL_NORMAL_OPTIMIZED_350_CASES_COMPLETE",
    "GEN0_THREE_ALTERNATE_INDEX_RECONSTRUCTIONS_EQUAL",
    "GEN0_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
    "GEN1_DIRECT_NORMAL_OPTIMIZED_ACCEPTED",
    "RAW_TRANSPORT_FIVE_FAMILY_STATIC_DESIGN_GO",
)
EXPECTED_C3_NEGATIVE_CODES = (
    "GEN0_FALSE_PARSER_DIGEST_AND_ABSENT_FULL_STDOUT_BINDING",
    "GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED",
    "GEN2_TOP_LEVEL_MEMO_PIN_STALE_AFTER_BLOB_REPIN",
    "GEN3_CORRELATED_MEMO_INVENTORY_MUTANT_INADEQUATE",
    "GEN3_NORMAL_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION",
    "GEN3_OPTIMIZED_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION",
    "GEN4_INDEPENDENT_OPTIMIZED_FOCUSED_RUN_ABORTED_FOR_SERIALIZATION",
    "GEN4_ROOT_NORMAL_FULL_SUITE_OVERLAPPED_FOCUSED_REVIEW",
    "GEN3_CONCURRENT_PDF_LEAN_VERSION_TIMEOUT_NO_CREDIT",
    "GEN1_PREDICTABLE_BSD_MKTEMP_TEMPLATE_REJECTED",
    "GEN1_RUFF_MECHANICAL_REFLOW_RESTORED_BEFORE_CANDIDATE",
    "V8_REVIEW_TRACKED_RESUME_APPEND_RESTORED_BEFORE_CANDIDATE",
    "PRE_OBJECT_REVIEW_LEDGER_NONCANONICAL_PRETTY_JSON",
    "SESSION_86029_ENTRY_ISOLATION_EXPECTATION_ORDER",
    "SESSION_56566_ENTRY_MUTATION_DELIMITER_AMBIGUOUS",
    "SESSION_3174_CHILD_COMMAND_EXPECTATION_ORDER",
    "SESSION_27678_TOOL_README_ANCHOR_ORDER",
    "SESSION_62196_PORTABILITY_DUPLICATE_KEY_STALE_POLICY",
    "SESSION_55661_CONTAMINATED_BY_IN_CLONE_GIT_PROBE",
    "SESSION_74678_PRIOR_SNAPSHOT_INVALIDATED_AND_STOPPED",
    "SESSION_54874_MEMO_ANCHOR_CARDINALITY_STALE",
    "SESSION_51446_WRONG_SELF_TEST_ATTRIBUTE",
    "SESSION_8070_TERMINAL_RECEIPT_UNRECOVERED",
    "TREE_FBCC_CHECKPOINT_FFBD_INVALIDATED_AFTER_WRITER",
    "TREE_229E_CHECKPOINT_7E_TRAILING_WHITESPACE",
    "TREE_6F6E_CHECKPOINT_C896_CHANGED_PROJECTION_STALE",
    "TREE_F306_EXECUTABLE_MODES_STRIPPED",
    "FINAL003_SELFTEST_WRONG_REASON",
    "FINAL004_PRELIMINARY_CLONE_MODES_0600",
    "FINAL004_SELFTEST_WRONG_REASON",
    "GEN4_SUPERSEDED_BEFORE_PUSH",
    "COMMIT_ENVELOPE_CLASSIFIER_FALSE_GREEN_FALSE_POSITIVE_SEQUENCE",
    "LOCAL_PRESEAL_SIDE_EFFECTS_INVALIDATED_CUSTODY",
    "C3_SOURCE_GENERATION_SPLIT",
    "LOCAL_ARTIFACT_MEMO_PARITY_UNBOUND",
    "REVIEW_LEDGER_COMPLETENESS_AND_TYPED_VALIDATION_GAP",
    "CANDIDATE_EXACT_SOURCE_AND_OVERLAY_CAPTURE_GAP",
    "RAW_TRANSPORT_TEXT_MODE_NORMALIZATION_GAP",
    "RAW_TRANSPORT_FOUR_CASE_STATIC_REVIEW_NO_GO",
    "PDF_FOUR_CONFIRMED_TYPOGRAPHY_FINDINGS",
    "PDF_TOC_CROWDING_SUSPICION_FALSIFIED",
    "RUFF_E402_CUSTODY_GUARD_POLICY_MISMATCH",
    "GITHUB_JOB_LOG_PARTIAL_FETCH_TIMEOUT_THEN_EXACT_REFETCH",
    "LEAN_JSON_NONEXISTENT_KEY_THEN_CORRECT_PARSE",
    "DESCRIPTOR_HELP_LAKE_VERSION_TIMEOUT",
    "LOCAL_LAKE_ROUTING_STALL_AND_ABORTED_ELAN_DOWNLOAD",
)
EXPECTED_C3_SESSION_IDS = (
    1091,
    3174,
    8070,
    15609,
    27678,
    51446,
    54874,
    55661,
    56566,
    56745,
    62196,
    74678,
    76847,
    84056,
    86029,
    97473,
)
EXPECTED_C3_CANDIDATE_TREES = (
    "229e24f3614b9e7fdd28d90cc291c6e6be2ce5f2",
    "40d288360b1b36e4276daff0f69361738fb4f029",
    "601f2681bdd88673e658d1b9a6e96de1936c8215",
    "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
    "6f6ea30c77b6cb92cbcd01770a167b467a6b546b",
    "75efda476f15da6a82b3e006d0989196436d1a4f",
    "94ebbfc74f98e6899771907a042579a39416b615",
    "b66da0309727876a04fad05a332bda30265fe7f3",
    "eac26211c4d76989253ce78ae2e4936d370932e1",
    "f306fd04b0c2ac19ed06f513ed0e183af4fe688f",
    "fbcc8b68cf04caa44555313eb2ecda252a47a7e5",
)
EXPECTED_C3_COMMITS_OR_CHECKPOINTS = (
    "0a2d7c6519ab3d16f8a5dee335409611b53ec574",
    "266760007b59642a6b9e12ad47ce0dffda54be26",
    "524a1c6af46698f872dce1a04aa0a281ec025a5e",
    "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
    "7e2812bd6d0b14234325b3ecd065017bec487d2a",
    "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
    "c896731c74534417e2de8636d6faa58ab2a54f70",
    "f0515e455d969eafe9a4f260f50341b0a120dc73",
    "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
    "ffbd24e668a57e8c8c20714998aa27c27085b3c2",
)
FOUNDATIONAL_SXPID_DIRECT_EVIDENCE = (
    "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json"
)
FOUNDATIONAL_SXPID_MUTATION_EVIDENCE = (
    "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json"
)
FOUNDATIONAL_SXPID_AUDIT_PDF = (
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf"
)
EXPECTED_FOUNDATIONAL_C3_WRAPPER_SHA256 = (
    "bf473bf654565b616ec2d73703ace2b7ad1ecfe64d3d4c9879bd427e0fd8d3e4"
)
EXPECTED_C3_LOCAL_ARTIFACT_CANDIDATE_PINS = {
    FOUNDATIONAL_SXPID_DIRECT_EVIDENCE: (
        "63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6",
        3421,
    ),
    FOUNDATIONAL_SXPID_MUTATION_EVIDENCE: (
        "b644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9",
        13428,
    ),
    FOUNDATIONAL_SXPID_AUDIT_PDF: (
        "ee715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b",
        358668,
    ),
}
EXPECTED_C3_PARENT_PDF_SHA256 = (
    "5904626fe91f4d606a09f0b842fcecad102d7585e6654a16e2bbb952ed0882df"
)
EXPECTED_C3_PARENT_PDF_SIZE_BYTES = 358292
EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256 = (
    "e339a45df06939c6719a16219ba2288208b9476287a893bf6c84562657238e5c"
)
PUBLIC_CI_FAILURE_RECEIPT = (
    "audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json"
)
PUBLIC_CI_FAILURE_RECEIPT_SHA256 = (
    "9aefa3bd484d55747a2d6887f35311e5f39f3b8eeb9408c3f17cf4cc8db2fa87"
)
PUBLIC_CI_PORTABILITY_RECEIPT = (
    "audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json"
)
PUBLIC_CI_PORTABILITY_RECEIPT_SHA256 = (
    "73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20"
)
EXPECTED_C2_TOOLING_DELTA = (
    (".github/workflows/ci.yml", "M"),
    ("CHANGELOG.md", "M"),
    (PRIOR_PHASE_PATH_POLICY, "A"),
    (PUBLIC_CI_FAILURE_RECEIPT, "A"),
    (CORRECTIVE_EVIDENCE, "A"),
    ("scripts/check-certified-sxpid2-claim.py", "M"),
    ("scripts/check-foundational-sxpid-audit-pdf.sh", "M"),
    ("scripts/check-ksg-phase-isolation-self-test.py", "M"),
    ("scripts/check-ksg-phase-isolation.py", "M"),
)
EXPECTED_C2_TOOLING_POLICY_ENTRIES = (
    (".github/workflows/ci.yml", "M", "verification_wiring"),
    ("CHANGELOG.md", "M", "documentation_release"),
    (PRIOR_PHASE_PATH_POLICY, "A", "phase_authority"),
    (PUBLIC_CI_FAILURE_RECEIPT, "A", "corrective_evidence"),
    (CORRECTIVE_EVIDENCE, "A", "corrective_evidence"),
    ("scripts/check-certified-sxpid2-claim.py", "M", "claim_adjudication"),
    (
        "scripts/check-foundational-sxpid-audit-pdf.sh",
        "M",
        "verification_wiring",
    ),
    (
        "scripts/check-ksg-phase-isolation-self-test.py",
        "M",
        "verification_tool",
    ),
    ("scripts/check-ksg-phase-isolation.py", "M", "verification_tool"),
)
EXPECTED_CORRECTIVE_POLICY_ENTRIES = (
    (".github/workflows/ci.yml", "M", "verification_wiring"),
    ("AGENTS.md", "M", "verification_wiring"),
    ("CHANGELOG.md", "M", "documentation_release"),
    (
        "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md",
        "M",
        "publication_regeneration",
    ),
    (
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
        "M",
        "portable_evidence",
    ),
    (
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "M",
        "portable_evidence",
    ),
    (
        PHASE_PATH_POLICY,
        "A",
        "phase_authority",
    ),
    (
        PORTABILITY_CORRECTIVE_EVIDENCE,
        "A",
        "corrective_evidence",
    ),
    (
        PUBLIC_CI_PORTABILITY_RECEIPT,
        "A",
        "corrective_evidence",
    ),
    (
        "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex",
        "M",
        "publication_regeneration",
    ),
    (
        "audit/tools/foundational_sxpid/README.md",
        "M",
        "publication_regeneration",
    ),
    ("justfile", "M", "verification_wiring"),
    (
        "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
        "M",
        "publication_regeneration",
    ),
    (
        "scripts/check-certified-sxpid2-claim.py",
        "M",
        "dependent_digest_rebind",
    ),
    (
        "scripts/check-foundational-sxpid-audit-pdf.sh",
        "M",
        "verification_wiring",
    ),
    (
        "scripts/check-ksg-phase-isolation-self-test.py",
        "M",
        "verification_tool",
    ),
    (
        "scripts/check-ksg-phase-isolation.py",
        "M",
        "verification_tool",
    ),
    (
        "scripts/check-lean-descriptor-factorization-self-test.py",
        "M",
        "portable_verification_tool",
    ),
    (
        "scripts/check-lean-descriptor-factorization.py",
        "M",
        "portable_verification_tool",
    ),
)
EXPECTED_CORRECTIVE_REVIEW_CLASS_CONTRACTS = {
    "corrective_evidence": (
        "Preserve the exact failed hosted run and the later hostile-review correction without rewriting history.",
        (
            "Keep the terminal CI and CodeQL execution facts, job and step counts, logs, routes, and then-selected four-file v2 remediation byte-for-byte historical.",
            "State that hostile review superseded only the remediation choice as final authority; it did not alter the run, theorem, failure, or CodeQL observations.",
            "Retain 85 open CodeQL alerts as unadjudicated security debt and require a fresh whole-run C3 execution after push.",
        ),
    ),
    "dependent_digest_rebind": (
        "Rebind only downstream verifier digests affected by exact workflow and justfile command bytes.",
        (
            "Change no certified-SxPID2 scientific rule, evidence, count, method boundary, or claim; update only its exact workflow and justfile digest constants.",
        ),
    ),
    "documentation_release": (
        "Keep operator-visible history aligned with the expanded v4 correction and its nonclaims.",
        (
            "Describe isolated entry, digest-bound source loading, descriptor-pinned private tracked configuration, retained HOME, cache, and endpoint negatives, and PDF regeneration without claiming a release, scientific advance, security, authenticity, or general cross-platform equivalence.",
        ),
    ),
    "phase_authority": (
        "Make the expanded C3 authority finite, acyclic, single-commit, and explicit about superseded remediation.",
        (
            "Require exactly nineteen paths in one unsigned, attribution-free, single-parent direct child of commit 8b792bc143fff2d84f2d8e7817d1de7850741223 and tree 8e247b9a6c46fd6266fe4fc02fbe9c3142268215.",
            "Bind the exact UTF-8 message and human author and committer identities; reject every gpgsig and gpgsig-* header while retaining bounded attribution-detector negatives.",
            "Require candidate-tree and checkpoint custody together for credit; label no-pair local replay NO-CREDIT and freeze every hostile-family count plus the separately typed controls.",
        ),
    ),
    "portable_evidence": (
        "Encode a host-independent reported Lean release projection plus premise-explicit POSIX custody evidence.",
        (
            "Regenerate compact canonical v4 receipts with exact version, source commit, and Release build while validating but not serializing the macOS or Linux platform token.",
            "Preserve three kernel-checked theorems, no axioms, three killed proof mutations, three semantic countermodels, and all frozen scientific digests.",
            "Count four exact-source controls, six snapshot attacks, three private-materialization controls, four retained negatives, two platform controls, nineteen hostile version probes, five raw-child transport families, one stdin-isolation subcontrol, and one completed-buffer cross-stream validation-order subcontrol separately from scientific mutations; these inventory labels do not imply evidentiary independence or child-stream emission chronology.",
        ),
    ),
    "portable_verification_tool": (
        "Strengthen macOS and Linux replay inputs while keeping native Windows custody explicitly unsupported.",
        (
            "Require Python -I -S, digest-before-compile exact-source loading, POSIX openat-style parent traversal, single-linked tracked leaves, double reads, and endpoint replay; retain generic endpoint swap/use/restore as an unauthenticated negative boundary and do not claim atomic history.",
            "Launch Lake from a descriptor-pinned private project with finite relative query paths, scrub explicit Python, Lean, Lake, Elan, and loader overrides, and retain the query-subtree swap, HOME-influenced launcher state, live dependency cache, and selected executable provenance as unauthenticated negative boundaries.",
            "Give the direct child stdin=subprocess.DEVNULL; after subprocess completion, capture stdout and stderr as raw completed buffers and validate the entire stdout buffer before the stderr buffer, rejecting raw carriage returns before strict UTF-8 decoding of each selected buffer and invalid UTF-8 before semantic parsing. This is exact completed-buffer validation precedence, not child-stream emission chronology.",
            "Impose no explicit regular-input or captured-output byte cap; timeout and wait cover only the direct child and provide no process-tree cleanup. Keep the passed project-CWD descriptor inherited by the direct child and potentially its descendants while closing unrelated ambient inheritable descriptors. These are residual capability, denial-of-service, and process-lifetime nonclaims, not independent custody evidence.",
            "Exercise normal and optimized byte-identical macOS/Linux parser projections; fail closed for full custody without POSIX directory descriptors, make no native Windows handle claim, and do not claim general cross-platform kernel equivalence.",
        ),
    ),
    "publication_regeneration": (
        "Keep human and generated foundational-publication command bytes synchronized with the executable entry contract and make the observed unnumbered-heading navigation regression fail closed.",
        (
            "Change the displayed isolated Python commands in Markdown, TeX, and the tool README; apply only bounded claim-neutral typography repairs plus the fresh Primary sources navigation anchor required by independent review; regenerate the foundational PDF deterministically and verify its text, bookmark/TOC association, built and committed destinations with a 72-point minimum separation, geometry, fonts, and rendered pages.",
            "Do not change scientific prose, theorem statements, numerical evidence, estimator claims, or the other eight complete-detail PDFs.",
        ),
    ),
    "verification_tool": (
        "Make C3 source, policy, evidence, history, and external-tree custody fail closed under mutation.",
        (
            "Execute descriptor self-test bytes through isolated stdin with a fixed digest-bound bootstrap and private exact checker copy rather than the live pathname.",
            "Run normal and optimized hostile suites over policy, receipts, startup contamination, parser and evidence schemas, Git history and context, external trees, science freezes, and self-reference.",
            "Require external tree and checkpoint together, scrubbed full-delta whitespace checks, clean-worktree parity, and exact one-child commit metadata for closure credit.",
            "Admit nonempty typed diagnostic tails on exactly three live routes: Git cat-file status 128, a deleted candidate path, and external-tree whitespace. Explicitly reject the retired Lean-parser child route; caller-bound prefixes and canonical tail transport do not establish operating-system or Git diagnostic truth.",
        ),
    ),
    "verification_wiring": (
        "Make every official C3 entry use the exact isolated interpreter and distinguish local diagnostics from credited custody.",
        (
            "Use Python -I -S in CI, the foundational wrapper, AGENTS, and justfile; retain optimized -O coverage after -I -S.",
            "Pass exact HEAD tree and checkpoint in hosted CI; mark local AGENTS and justfile phase runs with --diagnostic-without-external-custody.",
            "Set the sequential KSG assurance job to a finite 240-minute timeout derived from retained C2 and invalidated C3 timing observations without removing, merging, or weakening a hostile case.",
            "Preserve the wrapper's exact rational, Lean kernel, mutation, LaTeX, text, geometry, font, and cross-toolchain checks, and add an isolated source-to-TOC-to-bookmark-to-both-built-and-committed-PDF destination gate for Primary sources.",
        ),
    ),
}

# The complete single-parent chain between the delivery commit and the
# corrective anchor. Tree pins preserve the earlier integration exactly and
# prevent a same-message or same-path substitute from entering the envelope.
DECLARED_COMMIT_CHAIN = (
    (
        "8bcf33fb0e755727386aff69c8e703b96de87809",
        DELIVERY_PARENT,
        "a5778ae827f126676745e1a56984fd1dfa439fd9",
    ),
    (
        "afc45ff27e5af7fe04e44f2bb9f4147fb472c81e",
        "8bcf33fb0e755727386aff69c8e703b96de87809",
        "8278a4321da607554ff840a97fabbb57578b7f37",
    ),
    (
        FORMAL_ANCHOR,
        "afc45ff27e5af7fe04e44f2bb9f4147fb472c81e",
        FORMAL_ANCHOR_TREE,
    ),
    (
        RECOVERY_ANCHOR,
        FORMAL_ANCHOR,
        RECOVERY_ANCHOR_TREE,
    ),
    (
        INTEGRATION_ANCHOR,
        RECOVERY_ANCHOR,
        INTEGRATION_ANCHOR_TREE,
    ),
    (
        M1A_SCIENTIFIC_COMMIT,
        INTEGRATION_ANCHOR,
        M1A_SCIENTIFIC_TREE,
    ),
    (
        CORRECTIVE_PARENT,
        M1A_SCIENTIFIC_COMMIT,
        CORRECTIVE_PARENT_TREE,
    ),
    (
        C2_TOOLING_CORRECTION,
        CORRECTIVE_PARENT,
        C2_TOOLING_CORRECTION_TREE,
    ),
)

DELIVERY_CHANGED_BLOBS = {
    "audit/evidence/codex-goal-prompt-2026-07-26.md": (
        "100644",
        "dc984b2586970c71a6eafe262604dd9e8d6b988723a8aa6b46df8ae7d58adab2",
    ),
    "audit/evidence/completion-active-resume.md": (
        "100644",
        "3ce82abc139316ec511c7e920fb7dddebf5a38e5402be1b7e022fbcc2a773846",
    ),
    "audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md": (
        "100644",
        "61ba9897f7323a88bccc9f683d752cbb0a1408e1ec71268615c5619d9aeacf29",
    ),
    "audit/evidence/completion-run-ledger-2026-07-25.md": (
        "100644",
        "86881ba4deaa1be0ada75925dc6f739f6f0385612590989f9519d020453addce",
    ),
}

# These paths remain full scientific-baseline controls even if a checker edit
# tries to relabel one as allowed.  The global protected projection covers all
# other non-allowlisted paths.
PINNED_PROTECTED_BLOBS = {
    ".gitignore": (
        "100644",
        "918f4cf153cfa4a0f6e5b4d07bd647e417c06e383e4b580946acbede783873d1",
    ),
    "crates/pid-core/src/bin/exp0.rs": (
        "100644",
        "b9b19ec42ce129246c1bdcc044501843eba5e405f19c090180b9ad5f32a34409",
    ),
    "crates/pid-core/src/discrete_pid.rs": (
        "100644",
        "fa62dfec9e142cb4b1cc1266ab9837d07ba8869bfd739ec25cebea40f37d90e4",
    ),
    "crates/pid-core/src/pid2.rs": (
        "100644",
        "a1b34699b57105cb9da6aeb176efe6d0bfbb3342af4f28584f31675a26798d20",
    ),
    "crates/pid-core/tests/imin.rs": (
        "100644",
        "9ddd08c8ce736b5c7f539c4ace1d271336fe7bfe879dabe3155fef737b2cc2a0",
    ),
    "crates/pid-core/tests/pid2.rs": (
        "100644",
        "72a3949ff68227fe9cf20085fdc75bab9a4307574bcf1e782cba9c61c104c101",
    ),
    "crates/pid-python/src/lib.rs": (
        "100644",
        "b434c47bc3179cedd2c4d90321f3b07bf737ca0160736febc0569460849ab229",
    ),
    "crates/pid-python/tests/test_experimental_migration.py": (
        "100644",
        "758d5c01e3f93cba5afdc505ec4229abbd911418d4ce28559e048efd9379d239",
    ),
    "crates/pid-python/tests/test_v1.py": (
        "100644",
        "eb6b2d48a7d92143a71ae34e136b0d03cdfad266955ff8a02e7aa7bec4298939",
    ),
}

# Review-selected files whose complete candidate bytes are additionally
# visible as individual SHA-256 pins.  The generated block below supplies the
# expected mode/hash values; changing this reviewed path inventory is a manual
# review action, not part of mechanical fact rebasing.
BOUND_ALLOWED_PATHS = (
    ".github/workflows/ci.yml",
    ".gitleaks.toml",
    "AGENTS.md",
    "CHANGELOG.md",
    "ECOSYSTEM_CAPABILITIES.md",
    "FORMAL_TOOL_ADOPTION_AUDIT.md",
    "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md",
    "METHODS.md",
    "audit/evidence/assurance-registry.json",
    "audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json",
    "audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md",
    "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
    "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
    "audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json",
    "audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json",
    "audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md",
    "audit/evidence/ksg-rev4-phase-path-policy.json",
    "audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md",
    "audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json",
    "audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json",
    "audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md",
    "audit/evidence/sxpid2-exact-product-mutation-suite.json",
    "audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json",
    "audit/evidence/task-dispositions.json",
    "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
    "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
    "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
    "audit/formal/latex/formal-tool-adoption-audit.tex",
    "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex",
    "audit/tools/certified-sxpid/README.md",
    "audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py",
    "audit/tools/certified-sxpid/scripts/check-independent-verifier.py",
    "audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py",
    "audit/tools/certified-sxpid/scripts/verify_certificate.py",
    "audit/tools/foundational_sxpid/README.md",
    "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md",
    "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
    "crates/pid-core/identity/software-identity-reference-v1.json",
    "crates/pid-core/src/isx.rs",
    "crates/pid-core/src/ksg.rs",
    "crates/pid-core/src/pid3.rs",
    "crates/pid-core/src/stats.rs",
    "crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256",
    "crates/pid-core/tests/isx.rs",
    "crates/pid-core/tests/ksg.rs",
    "crates/pid-core/tests/ksg_report.rs",
    "crates/pid-core/tests/parallel_bit_identity.rs",
    "ecosystem-capabilities.json",
    "justfile",
    "method-catalog.json",
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    "release-scope-1.0.json",
    "scripts/README.md",
    "scripts/check-certified-sxpid2-claim-self-test.py",
    "scripts/check-certified-sxpid2-claim.py",
    "scripts/check-ecosystem-capabilities-self-test.py",
    "scripts/check-ecosystem-capabilities.py",
    "scripts/check-foundational-sxpid-audit-pdf.sh",
    "scripts/check-ksg-harmonic-exact-enclosure-self-test.py",
    "scripts/check-ksg-harmonic-exact-enclosure.py",
    "scripts/check-ksg-harmonic-modular-certificate-self-test.py",
    "scripts/check-ksg-harmonic-modular-certificate.py",
    "scripts/check-ksg-harmonic-revision-self-test.py",
    "scripts/check-ksg-harmonic-revision.py",
    "scripts/check-lean-descriptor-factorization-self-test.py",
    "scripts/check-lean-descriptor-factorization.py",
    "scripts/check-review-evidence-self-test.py",
    "scripts/check-review-evidence.py",
    "scripts/generate-ksg-harmonic-modular-certificate.py",
    "scripts/generate-ksg-local-arithmetic-oracle.py",
    "scripts/verify-package-archives.sh",
)

# These two files necessarily cannot be included in a digest stored inside the
# checker itself.  Their paths and modes remain part of the exact delta.  Their
# bytes acquire custody only when an independently pre-pinned Git tree/commit
# anchors them.  A tree derived after a coordinated checker/policy mutation is
# post-hoc consistency, not an external trust anchor.
SELF_UNHASHED_PATHS = frozenset(
    {
        "scripts/check-ksg-phase-isolation-self-test.py",
        "scripts/check-ksg-phase-isolation.py",
    }
)

# BEGIN GENERATED PHASE FACTS
EXPECTED_CHANGED_PATHS: tuple[str, ...] = (
    '.github/workflows/ci.yml',
    '.gitleaks.toml',
    'AGENTS.md',
    'CHANGELOG.md',
    'ECOSYSTEM_CAPABILITIES.md',
    'FORMAL_TOOL_ADOPTION_AUDIT.md',
    'FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md',
    'KNOWN_LIMITATIONS.md',
    'METHODS.md',
    'MIGRATION.md',
    'README.md',
    'RELEASE_SCOPE_1_0.md',
    'audit/evidence/assurance-registry.json',
    'audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json',
    'audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md',
    'audit/evidence/codex-goal-prompt-2026-07-26.md',
    'audit/evidence/completion-active-resume.md',
    'audit/evidence/completion-execution-plan-2026-07-26.md',
    'audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md',
    'audit/evidence/completion-run-ledger-2026-07-25.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-prompt.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-receipt.json',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-response-1.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-response-2.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-response-4.md',
    'audit/evidence/fable5-formal-methods-recovery-20260727T062149Z-responses.md',
    'audit/evidence/fable5-formal-methods-recovery-runner-20260727T062149Z.mjs',
    'audit/evidence/fable5-ksg-rev4-adjudication-20260727.json',
    'audit/evidence/fable5-ksg-rev4-adjudication-20260727.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-20260726T160252Z-context.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-20260726T160252Z-receipt.json',
    'audit/evidence/fable5-ksg-rev4-preclosure-20260726T160252Z-response.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-prompt-20260726T160252Z.md',
    'audit/evidence/fable5-ksg-rev4-preclosure-recovery-manifest-20260727.json',
    'audit/evidence/fable5-ksg-rev4-preclosure-runner-20260726T160252Z.mjs',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-adjudication.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-adjudication.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-completion-receipt.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-context.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-oversize-negative-receipt.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-prompt.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-receipt.json',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r1-a1.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r1-a2.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r2-a1.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r2-a2.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-response-r3-a2.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-responses.md',
    'audit/evidence/fable5-ksg-rev4-settled-hostile-20260727T120200Z-runner.mjs',
    'audit/evidence/foundational-sxpid-descriptor-factorization-lean.json',
    'audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json',
    'audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json',
    'audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json',
    'audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md',
    'audit/evidence/ksg-rev4-integration-reconstruction-map-2026-07-26.md',
    'audit/evidence/ksg-rev4-phase-path-policy.json',
    'audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md',
    'audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json',
    'audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json',
    'audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md',
    'audit/evidence/ksg-rev4-recovery-ledger-20260727.json',
    'audit/evidence/ksg-rev4-recovery-ledger-20260727.md',
    'audit/evidence/recover-fable5-ksg-rev4-preclosure-20260727.py',
    'audit/evidence/sxpid2-exact-product-mutation-suite.json',
    'audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json',
    'audit/evidence/task-dispositions.json',
    'audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md',
    'audit/formal/latex/certified-sxpid2-executable-assurance.tex',
    'audit/formal/latex/exact-log-product-sxpid2-assurance.tex',
    'audit/formal/latex/formal-tool-adoption-audit.tex',
    'audit/formal/latex/foundational-shared-exclusions-pid-audit.tex',
    'audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean',
    'audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean',
    'audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean',
    'audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2',
    'audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2',
    'audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2',
    'audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2',
    'audit/tools/certified-sxpid/README.md',
    'audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py',
    'audit/tools/certified-sxpid/scripts/check-independent-verifier.py',
    'audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py',
    'audit/tools/certified-sxpid/scripts/verify_certificate.py',
    'audit/tools/foundational_sxpid/README.md',
    'claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json',
    'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/call-site-map.md',
    'claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json',
    'claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json.sha256',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v1.md',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/claim-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/decision-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/decision.md',
    'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/decimal-reference-metric-conflation-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.json',
    'claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md',
    'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md',
    'claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/obligations.md',
    'claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/revision-index.md',
    'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md',
    'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes-v2.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes-v3.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes-v4.md',
    'claims/KSG-INTEGER-HARMONIC-001/routes.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md',
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md',
    'crates/pid-core/README.md',
    'crates/pid-core/identity/software-identity-reference-v1.json',
    'crates/pid-core/src/isx.rs',
    'crates/pid-core/src/ksg.rs',
    'crates/pid-core/src/pid3.rs',
    'crates/pid-core/src/stats.rs',
    'crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot',
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json',
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256',
    'crates/pid-core/tests/isx.rs',
    'crates/pid-core/tests/ksg.rs',
    'crates/pid-core/tests/ksg_report.rs',
    'crates/pid-core/tests/parallel_bit_identity.rs',
    'ecosystem-capabilities.json',
    'justfile',
    'method-catalog.json',
    'output/pdf/certified-sxpid2-executable-assurance.pdf',
    'output/pdf/exact-log-product-sxpid2-assurance.pdf',
    'output/pdf/formal-tool-adoption-audit.pdf',
    'output/pdf/foundational-shared-exclusions-pid-audit.pdf',
    'release-scope-1.0.json',
    'scripts/README.md',
    'scripts/check-certified-sxpid2-claim-self-test.py',
    'scripts/check-certified-sxpid2-claim.py',
    'scripts/check-ecosystem-capabilities-self-test.py',
    'scripts/check-ecosystem-capabilities.py',
    'scripts/check-foundational-sxpid-audit-pdf.sh',
    'scripts/check-ksg-harmonic-exact-enclosure-self-test.py',
    'scripts/check-ksg-harmonic-exact-enclosure.py',
    'scripts/check-ksg-harmonic-modular-certificate-self-test.py',
    'scripts/check-ksg-harmonic-modular-certificate.py',
    'scripts/check-ksg-harmonic-revision-self-test.py',
    'scripts/check-ksg-harmonic-revision.py',
    'scripts/check-ksg-phase-isolation-self-test.py',
    'scripts/check-ksg-phase-isolation.py',
    'scripts/check-lean-descriptor-factorization-self-test.py',
    'scripts/check-lean-descriptor-factorization.py',
    'scripts/check-lean-ksg-integer-harmonic-self-test.py',
    'scripts/check-lean-ksg-integer-harmonic.py',
    'scripts/check-review-evidence-self-test.py',
    'scripts/check-review-evidence.py',
    'scripts/check-z3-ksg-integer-harmonic-self-test.py',
    'scripts/check-z3-ksg-integer-harmonic.py',
    'scripts/generate-ksg-harmonic-modular-certificate.py',
    'scripts/generate-ksg-local-arithmetic-oracle.py',
    'scripts/verify-package-archives.sh',
)
EXPECTED_PRECOMMIT_TRACKED_MODIFICATIONS: tuple[str, ...] = (
    '.github/workflows/ci.yml',
    'AGENTS.md',
    'CHANGELOG.md',
    'FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md',
    'audit/evidence/foundational-sxpid-descriptor-factorization-lean.json',
    'audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json',
    'audit/formal/latex/foundational-shared-exclusions-pid-audit.tex',
    'audit/tools/foundational_sxpid/README.md',
    'justfile',
    'output/pdf/foundational-shared-exclusions-pid-audit.pdf',
    'scripts/check-certified-sxpid2-claim.py',
    'scripts/check-foundational-sxpid-audit-pdf.sh',
    'scripts/check-ksg-phase-isolation-self-test.py',
    'scripts/check-ksg-phase-isolation.py',
    'scripts/check-lean-descriptor-factorization-self-test.py',
    'scripts/check-lean-descriptor-factorization.py',
)
EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES: tuple[str, ...] = (
    'audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json',
    'audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md',
    'audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json',
)
EXPECTED_ALLOWLIST_SHA256 = 'bc706d2bec5ae3eb226ab465506b78c9ca243cf43b0f59f358a683e8702b61ee'
EXPECTED_CHANGED_PROJECTION_SHA256 = 'b8749f3bd06593b4a9584a34aef822a17cdc6077111678576caee5dd3ca47a03'
EXPECTED_PROTECTED_PROJECTION_SHA256 = 'cdd4a33542e5e46972e676690ae868f3b60abd736a66c51172290fc7b948218c'
EXPECTED_BASELINE_PATH_COUNT = 437
EXPECTED_PROTECTED_PATH_COUNT = 373
EXPECTED_BOUND_ALLOWED_BLOBS: dict[str, tuple[str, str]] = {
    '.github/workflows/ci.yml': ('100644', '02f3a8598683766cdba4cb75413783dca9c9a73ff87b833c2b5e8b21799d2220'),
    '.gitleaks.toml': ('100644', '6dfc7f6c79218afc873db40963cee0b73340558648d4c191db82d31d277b891b'),
    'AGENTS.md': ('100644', 'f2bdc8576559e8ab6ea155fd60cea330f0cc1eccd143448d7cb4bbf3d571795b'),
    'CHANGELOG.md': ('100644', '7fa92b9396c1b17b53a44ca7fbfeec025b195a4c2fd7f139561bfc4c24a8f2e6'),
    'ECOSYSTEM_CAPABILITIES.md': ('100644', '1c6a822b25642ab870e44444d7e48cddb26056be82225eb308d06ca66d0cd702'),
    'FORMAL_TOOL_ADOPTION_AUDIT.md': ('100644', '2151a865d5fe503bb50a42a578c747be64104228c519efeb6ad7000d3b827b25'),
    'FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md': ('100644', 'adb7e5e7288ec64c79b73ab7e179adbebbfcb196c60ba213759b085c2f532025'),
    'METHODS.md': ('100644', '3512e829502dbacb67977a1c808fc59af0461568989e00b363800444fea4ab19'),
    'audit/evidence/assurance-registry.json': ('100644', '5ceb2e47469dda5b8750ba8627014a7b634596ea4ae74c0b52873e19fe8d8a9a'),
    'audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json': ('100644', 'f9f0156abd4370857099f215a313b95621510d591e5726d52c856670324eb8d3'),
    'audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md': ('100644', 'aee278366f2bf990a5333dbaace7f190cb3191dfd2c2d972d8cf8ce33abe5004'),
    'audit/evidence/foundational-sxpid-descriptor-factorization-lean.json': ('100644', '63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6'),
    'audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json': ('100644', 'b644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9'),
    'audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json': ('100644', 'ffd763b2701c897ed3df75f3f97fe15933c37bf80adcadb0466e9a02113e6359'),
    'audit/evidence/ksg-rev4-af509-ci-tooling-path-policy.json': ('100644', '61a54281b492604bdf12bf7ef9b53ab44a773a4fd9dbe9081beb48643a8e07ad'),
    'audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md': ('100644', '2f673ced6cff152060e8830cc0320fc08d02b3c00feabef0200e0a4e9fe780c0'),
    'audit/evidence/ksg-rev4-phase-path-policy.json': ('100644', '297b4cb3fc60422796d64b2b5a23763d5c9d46f09ad3abe049e5a01c1330d5b2'),
    'audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md': ('100644', '8c28b1c8bceed4ca5fe9eb66871b9b33db34cf86750cc9eae54058381edb9541'),
    'audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json': ('100644', '9aefa3bd484d55747a2d6887f35311e5f39f3b8eeb9408c3f17cf4cc8db2fa87'),
    'audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json': ('100644', '73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20'),
    'audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md': ('100644', '87b7c5cc8927e0d5a0675057acf68b9bcea7348d55950578a134bacca898662a'),
    'audit/evidence/sxpid2-exact-product-mutation-suite.json': ('100644', '031a449c4239d74d0584c5f244ca18c852555d442ae7a880c2d750a02d5bcb0a'),
    'audit/evidence/sxpid2-exact-product-nonsyntactic-zero-boundary.json': ('100644', 'c36da6d5c55d553a6a647818cf15e6143a7914409370b096e6f6492f5731131d'),
    'audit/evidence/task-dispositions.json': ('100644', 'a99d28238ef8b1e210c8a4835e5d9fbfc272a6b774f32439eb78f72092a6c4c1'),
    'audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md': ('100644', '987c9fd759db8532f3f405c5604c13fd111b55ae5e4cb110a934a692e6aea98c'),
    'audit/formal/latex/certified-sxpid2-executable-assurance.tex': ('100644', '297c9fdfae897b2136a3eb870a81c0ab0b3553d1056c1c87492dd0e6fbafdf61'),
    'audit/formal/latex/exact-log-product-sxpid2-assurance.tex': ('100644', 'da4c75446de4e16e8414b8ec137d122c43a4e50eb0c7d7d976c4f3f621f9bccd'),
    'audit/formal/latex/formal-tool-adoption-audit.tex': ('100644', 'bf01b6c2f56b07cd1e379bb7d778923abb39e96b422130d4ab4814071ed6809c'),
    'audit/formal/latex/foundational-shared-exclusions-pid-audit.tex': ('100644', '10d1d5123376d8f4ec7363171b6f203ea2e38453d779142eb753364f9a1a33f9'),
    'audit/tools/certified-sxpid/README.md': ('100644', '61171ae73138570ecede4b1607b04f576807b6e92af1538539b38a0fca21f063'),
    'audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py': ('100644', '274de5313301b7f9ea671f817698f321852aa8a3c542d73c1e31d22f876a7fb8'),
    'audit/tools/certified-sxpid/scripts/check-independent-verifier.py': ('100644', '4327afdcce04421544481e0af9abf15dd3709ea75c5df994cb33b3ce3de91c17'),
    'audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py': ('100644', '04dc49e0ad42cd7b931aa51a3602f58dc789483c23d4aff4de5de8d25716efbf'),
    'audit/tools/certified-sxpid/scripts/verify_certificate.py': ('100644', 'c90572571eac9b5cd5cd11d526a211dd0dfa7ab45274f6c038c0f8338cd2958e'),
    'audit/tools/foundational_sxpid/README.md': ('100644', '1c352ff3bbcb5bd6c9df459b7a2a37c5c49454db152fc85e7419260c4d33d856'),
    'claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json': ('100644', '898414abc5bed5af483a966399bf68cbad8892a3c67da241555947d565c55585'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md': ('100644', '5eed715b409ce52271aa33dfba9466d566b78ef878438fdf7948f9a0135a9f7d'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md': ('100644', '31313a2069af8a02409aa466176c2c2105915344842be965983182ae236c1dc9'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md': ('100644', '8907de510080c53ef19de8e80f131f409588d88441205b11e34e6de59f7aa52f'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md': ('100644', '35aa45ed5cea6b0671a7012f048269e2970a5d39c50724fe1090c6fce0466fd7'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/retained-negative-controls-v3.md': ('100644', 'dcbdf594796dd9559a8882ff47599b1045f9671801e7f5ef26cd3edcbe355bf2'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/theorem-evidence-map-v3.md': ('100644', '9a9ec2894bf69513f04260bdeb991d454c65be693179868691513f69b7d7a346'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md': ('100644', 'ab2974c309e40e36eba1c7e9fbe1d71e7a36aaf25eb91ec4d63d65e819c04f69'),
    'claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md': ('100644', '7feba281c710a34e98cb75665b8a1e1adb63bbd31b972812945895faedb33046'),
    'crates/pid-core/identity/software-identity-reference-v1.json': ('100644', '517ddcce5f101675cd2cb3b718e3b132dedf928460624aae9b94d22fafe97032'),
    'crates/pid-core/src/isx.rs': ('100644', '7a3577a0148cafaf93c2d6a982bd3b04b3499b917a1f59b63bdbca30b68a809d'),
    'crates/pid-core/src/ksg.rs': ('100644', '0f5109dda054a0222ed796209b10d22196348eddac76d8d53dd78b4e03a95250'),
    'crates/pid-core/src/pid3.rs': ('100644', 'f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd'),
    'crates/pid-core/src/stats.rs': ('100644', '204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e'),
    'crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot': ('100644', 'a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b'),
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json': ('100644', '560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c'),
    'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256': ('100644', 'fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7'),
    'crates/pid-core/tests/isx.rs': ('100644', 'ce041e8e27900ac3d76b97526e43f56057d071cb987d8a53de3a7b51dd16b3ee'),
    'crates/pid-core/tests/ksg.rs': ('100644', '544192cac6c00957e1e05a4cc320c069453060eb1fe676131f83b155c1ee6daa'),
    'crates/pid-core/tests/ksg_report.rs': ('100644', '724c1fad3ce11ce14b789efda0edccfe96a6f3334d077cad075dd667683b0f44'),
    'crates/pid-core/tests/parallel_bit_identity.rs': ('100644', '611a31e1b76536b1b1b712cdbd7713dc5caad24f354b0c507e2779bbf8f3cb28'),
    'ecosystem-capabilities.json': ('100644', 'd6070882c9a9b380dac568c38685a79f45bc7bfe08d0622e5525d72fd16e67e5'),
    'justfile': ('100644', '384ca61cd1f4f1c7eafbe71f6b39e71f4edd8822038feaa4ad07dc072bbb38cc'),
    'method-catalog.json': ('100644', '637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f'),
    'output/pdf/certified-sxpid2-executable-assurance.pdf': ('100644', '2370637b750578fc1818279f6001f4143dd8e1e3d48136077a6953ceb2ee795c'),
    'output/pdf/formal-tool-adoption-audit.pdf': ('100644', 'e7d4fa04700b9cbe8d9a4701525341f1743a4a28e624c31a2e8726b69fc9147c'),
    'output/pdf/foundational-shared-exclusions-pid-audit.pdf': ('100644', 'ee715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b'),
    'release-scope-1.0.json': ('100644', '4fe9e5e4ba7b31a609b73127ee7c34ffcd33765e87363c1b50f3d26145c4319d'),
    'scripts/README.md': ('100644', '4ea701794c455021aff8c991aac8a127fde1bcabed390e2dc0b5037f475b3a83'),
    'scripts/check-certified-sxpid2-claim-self-test.py': ('100644', 'cac22cb1af20e8b020d67ec1124515179db4cc93ddc4885d43d83a49dd46a24f'),
    'scripts/check-certified-sxpid2-claim.py': ('100644', '18d5df94924b34d51bbe25c5ee503fd1cb009838bf6ed6741a66c8b675470faa'),
    'scripts/check-ecosystem-capabilities-self-test.py': ('100644', 'ea85fa013af2136a16850583459be4c2fd9fb0b736e1852f619a125cacd2b0a3'),
    'scripts/check-ecosystem-capabilities.py': ('100644', '42ac86f8899928c79646eb03aafc747ebef59185d7f09579a07b7efd4ecf5120'),
    'scripts/check-foundational-sxpid-audit-pdf.sh': ('100755', 'bf473bf654565b616ec2d73703ace2b7ad1ecfe64d3d4c9879bd427e0fd8d3e4'),
    'scripts/check-ksg-harmonic-exact-enclosure-self-test.py': ('100755', 'afc2ca44795f86b3dd9c74d2c07234ae9e0372737cdae7d718ec2db2e5204782'),
    'scripts/check-ksg-harmonic-exact-enclosure.py': ('100755', 'b7c4df526703adc3dd8f5f04471b027decb256bfaaaa2d32ff9f918253546468'),
    'scripts/check-ksg-harmonic-modular-certificate-self-test.py': ('100755', '1eebc0d575b730753d98659baee5e1f76f17c783e112a9610b731d5f07618c65'),
    'scripts/check-ksg-harmonic-modular-certificate.py': ('100755', '201b046957cee263ad4864acd84ab18095db4bbfc5a23bf90c2bb836b986afec'),
    'scripts/check-ksg-harmonic-revision-self-test.py': ('100644', '6212bca982da4e5d4c1affa945c7ac8fed254fbc4f5d775798427549c0b837cc'),
    'scripts/check-ksg-harmonic-revision.py': ('100644', '083aee3ba1cb59b8a5cfc921ac6558fd7e347ef6a0deddb6b81ef07f78e2d950'),
    'scripts/check-lean-descriptor-factorization-self-test.py': ('100755', 'd357c9ddf1dbf2b83b46cc426da063c29ccf9dba925e6ad20c35f56c85cd606c'),
    'scripts/check-lean-descriptor-factorization.py': ('100755', 'd2eda588a204966e3e5b3f33f70b5a263bfc49c3100e444d4fc27c3e428c8cf6'),
    'scripts/check-review-evidence-self-test.py': ('100755', '9830fbd2ee837f0f592bfc1d5461bdeefb3f7a0d95f9536b987b3a5226af5538'),
    'scripts/check-review-evidence.py': ('100755', '6f5c34a8bcfcb3b1b3cb666f955c6ef35b024cc4073214fbe677aa1b61140ade'),
    'scripts/generate-ksg-harmonic-modular-certificate.py': ('100755', '969c4a5a5a8f6a9054de0154a331824bf2034223c30cb3a76f5e975f6f68a1c3'),
    'scripts/generate-ksg-local-arithmetic-oracle.py': ('100755', 'a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b'),
    'scripts/verify-package-archives.sh': ('100755', '13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256'),
}
# END GENERATED PHASE FACTS




EXPECTED_PARALLEL_U64_CONSTANTS = {
    "ISX_REDUNDANCY_BITS": 4608069949341512143,
    "KSG_LOCAL_TERMS_CHECKSUM": 13714940533915299,
    "KSG_LOCAL_TERM_0": 4611372573292626839,
    "KSG_LOCAL_TERM_LAST": 4609053335123176929,
    "KSG_LOCAL_TERM_MID": 4608683422432580648,
    "PID2_RED_BITS": 4608069949341512143,
    "PID2_SYN_BITS": 4591732782175321776,
    "PID2_UNQ1_BITS": 4590324628665003600,
    "PID2_UNQ2_BITS": 13821388618758275492,
    "PID3_ATOM_001_BITS": 13803885910316517056,
    "PID3_ATOM_111_BITS": 4587721666143603408,
    "PID3_ATOM_CHECKSUM": 9260367673031411424,
    "PID3_RED_CHECKSUM": 12358916445650220,
}
FORBIDDEN_PID2_SYN_BITS = 4591732782175321784

EXPECTED_PARALLEL_TESTS = (
    "block_bootstrap_matches_serial_reference",
    "bootstrap_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "discrete_pid2_is_bit_identical_across_repeated_calls",
    "isx_redundancy_matches_serial_reference",
    "ksg_local_mi_terms_match_serial_reference",
    "ksg_report_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "pid2_atoms_match_serial_reference",
    "pid2_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "pid3_atoms_match_serial_reference",
    "pid3_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum",
    "red_degree_discrete_is_bit_identical_across_repeated_calls",
    "vul_degree_discrete_is_bit_identical_across_repeated_calls",
)

EXPECTED_RELEASE_REVISIONS = {
    "pid-core.experimental.continuous.pid2": (
        "separate-biased-term-pid2-integer-harmonic-v2"
    ),
    "pid-core.experimental.hierarchy": (
        "hierarchy-screening-with-integer-harmonic-ksg-v2"
    ),
    "pid-core.experimental.pipelines.pid2-screening": (
        "deterministic-pair-enumeration-with-integer-harmonic-pid2-v2"
    ),
    "pid-core.experimental.pipelines.same-sample-quantization": (
        "equal-width-same-sample-v1"
    ),
    "pid-core.research.isx-heuristics": (
        "heuristic-baselines-with-integer-harmonic-ksg-v2"
    ),
    "pid-core.stable.imin": (
        "empirical-specific-information-minimum-with-quantized-provenance-v1"
    ),
}

FORBIDDEN_COMBINED_RELEASE_REVISIONS = frozenset(
    {
        (
            "deterministic-pair-enumeration-with-integer-harmonic-and-"
            "represented-input-exact-pid2-synergy-sum-v2"
        ),
        (
            "empirical-specific-information-minimum-with-quantized-provenance-"
            "and-represented-input-exact-synergy-sum-v2"
        ),
        "equal-width-same-sample-with-represented-input-exact-imin-synergy-sum-v2",
        (
            "heuristic-baselines-with-integer-harmonic-ksg-and-"
            "represented-input-exact-pid2-synergy-sum-v2"
        ),
        (
            "hierarchy-screening-with-integer-harmonic-ksg-and-"
            "represented-input-exact-pid2-synergy-sum-v2"
        ),
        (
            "separate-biased-term-pid2-with-integer-harmonic-inputs-and-"
            "represented-input-exact-synergy-sum-v2"
        ),
    }
)

FORBIDDEN_CHANGED_PATH_PREFIXES = (
    "claims/IMIN-TIE-SWAP-001/",
    "claims/PID2-REPRESENTED-SUM-001/",
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/",
    "claims/SX-COUNT-EVENT-BRIDGE-001/",
    "crates/pid-python/",
)
FORBIDDEN_CHANGED_PATH_FRAGMENTS = (
    "exact_binary64_sum",
    "finite-convergence",
    "finite_convergence",
    "frontier",
    "imin-tie",
    "pid2-represented-sum",
    "sx-certified-averaged-pid3",
    "sx-count-event-bridge",
)
FORBIDDEN_EXACT_CHANGED_PATHS = frozenset(
    {
        "crates/pid-core/src/bin/exp0.rs",
        "crates/pid-core/src/discrete_pid.rs",
        "crates/pid-core/src/pid2.rs",
        "crates/pid-core/tests/imin.rs",
        "crates/pid-core/tests/imin_numerical_boundary.rs",
        "crates/pid-core/tests/pid2.rs",
        "scripts/check-imin-tie-boundary-self-test.py",
        "scripts/check-imin-tie-boundary.py",
        "scripts/check-pid2-represented-sum-self-test.py",
        "scripts/check-pid2-represented-sum.py",
        "scripts/generate-exact-binary64-sum-oracle.py",
    }
)
CORRECTIVE_PUBLICATION_PATHS = frozenset(
    {
        "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex",
        "audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md",
        "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
        "audit/formal/latex/exact-log-product-sxpid2-assurance.tex",
        "audit/formal/latex/formal-tool-adoption-audit.tex",
        "output/pdf/certified-sxpid2-executable-assurance.pdf",
        "output/pdf/exact-log-product-sxpid2-assurance.pdf",
        "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
        "output/pdf/formal-tool-adoption-audit.pdf",
    }
)

C3_AUTHORIZED_PUBLICATION_PATHS = frozenset(
    {
        "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex",
        "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    }
)
C3_PYTHON_ENTRYPOINTS = (
    "scripts/check-ksg-phase-isolation-self-test.py",
    "scripts/check-ksg-phase-isolation.py",
    "scripts/check-lean-descriptor-factorization-self-test.py",
    "scripts/check-lean-descriptor-factorization.py",
)

C3_SCIENCE_FREEZE_PREFIXES = (
    "audit/formal/",
    "claims/",
    "crates/",
    "output/pdf/",
)
C3_EXPLICIT_FROZEN_PATHS = (
    "ECOSYSTEM_CAPABILITIES.md",
    "METHODS.md",
    "audit/evidence/assurance-registry.json",
    "audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean",
    "audit/formal/lean/lake-manifest.json",
    "audit/formal/lean/lakefile.toml",
    "audit/formal/lean/lean-toolchain",
    "ecosystem-capabilities.json",
    "method-catalog.json",
    "release-scope-1.0.json",
)

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_LEAN_VERSION_CONTROL_PROBES = (
    (
        "macos_arm64",
        "3255b9f61344ad50ba048b78065f1ebe2d238455af4b2c887237ee28b4482ae8",
    ),
    (
        "ubuntu_x86_64",
        "b3f203eff6e59b2f28b90ee7019ed0ae5630482a3b239c72c150093764a98ae0",
    ),
)
EXPECTED_LEAN_VERSION_HOSTILE_PROBES = (
    (
        "nonzero_exit",
        "68c50388d8f7fe05b818b299679d5ee6b665fdf87263f568c7615a623b3d9380",
    ),
    (
        "unexpected_stderr",
        "fa9bd609971e1dea951dcf61a0cb18693b4b1eddfddae3701401ee2c32aaf36a",
    ),
    (
        "empty_stdout",
        "a6c98c765596257989a33b495dbdc844f14662a966071e00f819825d43b23cae",
    ),
    (
        "missing_final_newline",
        "01fe42c7ccbb2b56d0ee83f0e95e04deed30ab46e3a3e4a608c1b4636c4be192",
    ),
    (
        "extra_stdout_line",
        "deba91a97cbcb491a8cbe8343b9f76d39b47c2400c7cf83ca2e49b31e9bd8bdf",
    ),
    (
        "extra_blank_line",
        "3d47ad04104dfa7b88a3e73af12c1f8affcb5cd7115dbe8c79125a06054f44ea",
    ),
    (
        "leading_whitespace",
        "5afbcb8f5a24357391ee3df06f5c0673efeab7d30a6df7f3e3deea3e0f48d686",
    ),
    (
        "trailing_payload",
        "57f591a5443003fe2a0d6a857e6e0f244cf05b969b7548b003ac2eee1f1d8826",
    ),
    (
        "wrong_version",
        "c439991296dcc6473f1320e26ed0a2ac2dd14bd1446ae446070ecf708cb78903",
    ),
    (
        "malformed_version",
        "929e75a2b6c7917a3d845ee1fe65202b8345b092e18a5fab32025791f35879d5",
    ),
    (
        "missing_platform",
        "7608546a23a92202e01e4185065f2ea7f321113f9dcb154d8b835b42ea4c3ce4",
    ),
    (
        "platform_with_whitespace",
        "8038fc38c9f8f3c041f1efe9940114b80186edfd06610ffde8d0519405ca3fc8",
    ),
    (
        "platform_with_too_few_components",
        "093a598bb2852d48ed82d26fe1eecc84273b3bbe1656574c24f97e526fe80889",
    ),
    (
        "missing_commit_label",
        "fecf2091342619d1a5b4d90bb63a7853009d405f640a06e7fcb60342c42f7cbb",
    ),
    (
        "wrong_commit",
        "a760598ec55dc19568b40145fc3e2d97ba41a8c593fbbda2cf1b013670b21a3a",
    ),
    (
        "short_commit",
        "46fea678c579259b8cc4c591e6c7b7b42470711c3f117c3da60af54b61e6a274",
    ),
    (
        "uppercase_commit",
        "fa6a81e1f5f268f8ad7e520d8ae8f18e7afe599bd2c63b48101c3b58ef3c71e5",
    ),
    (
        "wrong_build",
        "4ecce51ae2e154cea524cc3f96b67ed40af8c7f4de527cbc76fe1b5fdddba0e7",
    ),
    (
        "missing_closing_delimiter",
        "95a7601553b2705fc1ddfe9c1d44fcdefa841307c9b501dfc0bb8fcbfcb8913b",
    ),
)
EXPECTED_LEAN_VERSION_HOSTILE_REJECTION_REASONS = (
    "Lean version probe exited unsuccessfully: 1",
    "Lean version probe emitted unexpected stderr: 'unexpected diagnostic\\n'",
    "Lean version probe stdout lacks its final newline",
    "Lean version probe stdout lacks its final newline",
    "Lean version probe did not emit exactly one line",
    "Lean version probe did not emit exactly one line",
    "unexpected Lean version output: ' Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)\\n'",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release) trailing\\n'",
    "unexpected Lean portable identity: LeanPortableIdentity(version='4.31.0', commit='8c9756b28d64dab099da31a4c09229a9e6a2ef35', build='Release')",
    "unexpected Lean version output: 'Lean (version 4.32, x86_64-unknown-linux-gnu, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)\\n'",
    "unexpected Lean version output: 'Lean (version 4.32.0, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)\\n'",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64 unknown linux gnu, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)\\n'",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64-linux, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)\\n'",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64-unknown-linux-gnu, 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)\\n'",
    "unexpected Lean portable identity: LeanPortableIdentity(version='4.32.0', commit='9c9756b28d64dab099da31a4c09229a9e6a2ef35', build='Release')",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef3, Release)\\n'",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit 8C9756B28D64DAB099DA31A4C09229A9E6A2EF35, Release)\\n'",
    "unexpected Lean portable identity: LeanPortableIdentity(version='4.32.0', commit='8c9756b28d64dab099da31a4c09229a9e6a2ef35', build='Debug')",
    "unexpected Lean version output: 'Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release\\n'",
)
EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS = (
    "snapshot fixture identity changed after initial snapshot",
    "symlink fixture must be a regular, non-symbolic-link file",
    "unstable fixture metadata or identity changed during snapshot",
    "symlink-parent fixture must not be reached through a symbolic-link parent",
    "hard-link fixture must have exactly one hard link",
    "parent-replacement fixture metadata or identity changed during snapshot",
)
EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_REJECTION_REASONS = (
    "Lean process raw stdout contains a carriage return",
    "Lean process raw stderr contains a carriage return",
    "Lean process raw stdout is not strict UTF-8",
    "Lean process raw stderr is not strict UTF-8",
    "Lean process raw stdout contains a carriage return",
)
EXPECTED_EXACT_SOURCE_REJECTION_REASON = (
    "parent_substitution_control exact source digest differs before compilation"
)


EXPECTED_PROCESS_STDIN_ISOLATION_SUBCONTROL_PROBES = (
    (
        "devnull_child_stdin_rejects_parent_fd0_contamination",
        "65174fc6fd7bfb6c9ab0fcaa7ee9038726a6597084b34f17dd7c42939e1ada75",
    ),
)
EXPECTED_RAW_PROCESS_TRANSPORT_ORDER_SUBCONTROL_PROBES = (
    (
        "raw_subprocess_stdout_precedes_stderr_mixed_fault",
        "c30ef33a2390f923bc204c5d03cb2a10dc46c6bdbb41b97cddb93a26114909cd",
    ),
)


EXPECTED_EXACT_SOURCE_CONTROL_PROBES = (
    (
        "sourcefileloader_unchecked_hash_pyc_substitution",
        "02f2bcaf45a5fc7de1fb1463860a96d5d860c29ac9b23306f6b8e3f5c6a4cc79",
    ),
    (
        "parent_directory_swap_use_restore_live_path_execution",
        "d6bc1ca0f1f600de4e58708c01460ef8c03305052350ee464e946b7fa6891bee",
    ),
    (
        "digest_bound_double_read_compile_exec_exact_source",
        "0fa132f7f63ea7be0353f142747cfe7402e6b2c4a988689ede2fabe2d0f3f307",
    ),
    (
        "digest_bound_rejects_parent_substitution_before_exec",
        "2b73687ca48d27de8bac8f10cd864a913dd792137af208656a1d333596a49e3c",
    ),
)
EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES = (
    (
        "mutation_between_snapshot_and_replay",
        "19006bc971462c36e4f1aac5bb69c4ddce5e7a321d7b826e0dc5466a813a3c36",
    ),
    (
        "symbolic_link_input",
        "7e7c30d59a2d2c3c45604cd1515808b5579f648b541e97b7f6236e846464764a",
    ),
    (
        "mutation_during_double_read",
        "cb7765555394ba2e6790e0947be2cb3b6226dacebf7fa045a9c566a964893d13",
    ),
    (
        "symbolic_link_parent_component",
        "2ec4e5692084b2f99aef80fe0b8bae3d188393623bef508b6552145af5398ebe",
    ),
    (
        "multiply_linked_leaf",
        "b0091596d2b5904bdabbdb2e78305eae5cb43f2122512a0c9c2938742ed7e3aa",
    ),
    (
        "parent_replacement_during_snapshot",
        "492a278c6c4687b402dc49b0c1c73b674a8d09692440d838076d82237a5afeb3",
    ),
)
EXPECTED_PRIVATE_MATERIALIZATION_CONTROL_PROBES = (
    (
        "private_project_retains_prevalidated_tracked_copies",
        "cbc2e3bf55f3ccecf70bd4688bdc5285ae621d06123d137c79da6b9586374794",
    ),
    (
        "lean_lake_python_loader_environment_overrides_scrubbed",
        "8b20e741bee6d8978d0fbb05c3917a04a2dbfb1c2329889c193e6b86fe6f11df",
    ),
    (
        "descriptor_pinned_private_cwd_relative_query_and_lake_proxy_launch",
        "97573c9ec8d4439a83943f29746fc38454f7b40a2073328ee3775db52715b19a",
    ),
)
EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_PROBES = (
    (
        "raw_subprocess_crlf_stdout_before_decode",
        "e354201ec06123bfee42dda9d3d71266223d46766dfdcdbc4202505388bded41",
    ),
    (
        "raw_subprocess_cr_stderr_before_decode",
        "2e1d5f2c08d1d3b7a3063e036815bcfe2b2635ac1fad345c7bf498280af0274c",
    ),
    (
        "raw_subprocess_non_utf8_stdout_before_decode",
        "49de6c6ead76e9eae7810ba66e20d0f3d294b7722647928b539e4e88508c4f5d",
    ),
    (
        "raw_subprocess_non_utf8_stderr_before_decode",
        "033755491c7342d20d7e2e8eeb5b793cc66ea7fb7f667769e7e8aa5302ddbaff",
    ),
    (
        "raw_subprocess_cr_precedes_non_utf8_stdout",
        "4c327e2ba7ab8c56dd37b567d815887c6b710b1c05b2141e6851bb0fe31c7134",
    ),
)
EXPECTED_RETAINED_NEGATIVE_PROBES = (
    (
        "endpoint_replay_misses_parent_swap_use_restore",
        "3a20104b95bf289affbf28226ef7eea0d17b5007249c9eb7636e7109796592cb",
    ),
    (
        "descriptor_pinned_project_does_not_pin_query_subtree_entry",
        "6c227582cd26c7e778a52a9981d67951136743c9c068b53bb1c7663d19288fa2",
    ),
    (
        "retained_home_can_influence_live_launcher_state",
        "978ae4e307f5136fed65e52b2610339fc09fd2d2b8863e7e636eae3f8d51a409",
    ),
    (
        "private_project_dependency_cache_remains_live",
        "2fa5b404f4e520905bbc2b24ae433cbfec2f2ea3548a64249bb2bc272de82cdc",
    ),
)
EXPECTED_C3_COMMIT_MESSAGE = "fix: harden Lean evidence portability and replay\n"
EXPECTED_C3_COMMIT_DISPLAY_NAME = "Sepehr Mahmoudian"
EXPECTED_C3_COMMIT_EMAIL = "sepmhn@gmail.com"
EXPECTED_C3_COMMIT_MESSAGE_SHA256 = (
    "35c9db2d9db534a6cff91f2581b970fe543d808509214243999d94c9f3b3f8de"
)
EXPECTED_HISTORICAL_REMEDIATION_SUPERSESSION = {
    "final_authority": (
        "This schema-revision-6 nineteen-path C3 policy supersedes only the "
        "historical receipt's chosen correction as final remediation authority."
    ),
    "historical_chosen_correction": {
        "description": (
            "Strictly parse the complete Lean version process result, require exact "
            "version 4.32.0, exact 40-hex source commit, Release build, zero exit, "
            "empty stderr, and one complete line; validate but omit the host platform "
            "token from the reproducible v2 evidence projection."
        ),
        "hostile_version_probes_required": 19,
        "portable_controls_required": 2,
        "scope": (
            "descriptor checker, its self-test, and their two generated evidence "
            "files only"
        ),
    },
    "historical_receipt_sha256": PUBLIC_CI_PORTABILITY_RECEIPT_SHA256,
    "historical_workflow_changed": False,
    "preserved_historical_facts": [
        "claim_boundary",
        "codeql",
        "head",
        "jobs",
        "remediation",
        "run",
        "status",
    ],
    "retroactive_run_facts_changed": False,
}
EXPECTED_HOSTILE_SUITE_CONTRACT = {
    "contracted_total": 351,
    "families": {
        "checker_model": 44,
        "entry_isolation": 5,
        "external_tree": 9,
        "failure_receipt_oracle": 18,
        "git_context": 16,
        "lean_portability": 17,
        "lifecycle_history": 30,
        "path_custody": 8,
        "policy_authority": 44,
        "prior_public_ci_evidence": 21,
        "public_ci_portability_evidence": 34,
        "python_entry_attacks": 18,
        "rebased_semantic_firewall": 76,
        "success_receipt_oracle": 11,
    },
    "semantics": (
        "Counts are contracted case inventories within named families; only a "
        "completed suite executes them. They are not claims of statistical or "
        "evidentiary independence, completeness, mutation adequacy, authenticity, "
        "security, or scientific correctness."
    ),
    "separate_controls": {
        "json_type_firewall": 2,
        "phase_lean_raw_transport_subcontrols": 6,
        "retained_self_reference_boundary": 1,
    },
}
COMMIT_TIMEZONE_RE = re.compile(
    r"^[+-](?:(?:0[0-9]|1[0-3])[0-5][0-9]|1400)$"
)
_RESOLVED_GIT_EXECUTABLE: Path | None = None

FORBIDDEN_LOCAL_CONFIG_KEYS = frozenset(
    {
        "attr.tree",
        "core.attributesfile",
        "core.excludesfile",
        "core.fsmonitor",
        "core.sparsecheckout",
        "core.sparsecheckoutcone",
        "extensions.worktreeconfig",
        "index.sparse",
    }
)
FORBIDDEN_LOCAL_CONFIG_PREFIXES = (
    "filter.",
    "include.",
    "includeif.",
)

EXPECTED_CRITICAL_GATE_SEQUENCE = (
    "validate_checker_source_model",
    "validate_repository_context",
    "collect_candidate_snapshot",
    "validate_commit_envelope",
    "validate_prior_c2_history",
    "validate_phase_path_policy",
    "validate_staged_tree_custody",
    "validate_effective_attributes",
    "validate_changed_path_firewall",
    "validate_public_ci_failure_evidence",
    "validate_public_ci_portability_failure_evidence",
    "validate_ci_corrective_firewall",
    "validate_claim_checker_workflow_rebind",
    "validate_python_entry_isolation",
    "validate_foundational_pdf_lake_preflight",
    "validate_lean_evidence_portability",
    "validate_c3_local_artifact_parity",
    "validate_package_archive_corrective_firewall",
    "validate_ecosystem_corrective_firewall",
    "validate_stats_firewall",
    "validate_parallel_semantics",
    "validate_release_firewall",
    "validate_identity_firewall",
    "validate_c3_science_and_publication_isolation",
    "validate_repository_context",
    "collect_candidate_snapshot",
    "validate_staged_tree_custody",
)


class PhaseIsolationError(RuntimeError):
    """A bounded ancestry, tree, custody, or phase-firewall check failed."""


@dataclass(frozen=True)
class GitEntry:
    mode: str
    kind: str
    oid: str
    sha256: str


@dataclass(frozen=True)
class CandidateSnapshot:
    entries: dict[str, GitEntry]
    head: str
    head_entries: dict[str, GitEntry]
    tracked_modifications: tuple[str, ...]
    untracked: tuple[str, ...]


@dataclass(frozen=True)
class FileEvidence:
    path: str
    mode: int
    size: int
    mtime_ns: int
    sha256: str


@dataclass(frozen=True)
class LeanPortabilityArtifacts:
    parser_normal: bytes
    parser_optimized: bytes
    direct_evidence: bytes
    mutation_evidence: bytes


@dataclass(frozen=True)
class GitBinaryIdentity:
    executable: FileEvidence
    version: str


@dataclass(frozen=True)
class RepositoryContext:
    git_binary: GitBinaryIdentity
    root: str
    git_boundary: FileEvidence
    git_dir: str
    common_git_dir: str
    local_config: FileEvidence
    local_config_semantics_sha256: str
    info_attributes_absent: bool
    worktree_config_absent: bool
    replacement_refs_sha256: str


@dataclass(frozen=True)
class PhasePolicyEntry:
    path: str
    status: str
    review_class: str
    rationale: str
    obligations: tuple[str, ...]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PhaseIsolationError(message)


def require_strict_json_equal(
    actual: object,
    expected: object,
    label: str,
    *,
    path: str = "$",
) -> None:
    """Compare JSON values without Python's bool/int/float coercions."""

    require(
        type(actual) is type(expected),
        f"{label} has the wrong JSON type at {path}: "
        f"expected {type(expected).__name__}, observed {type(actual).__name__}",
    )
    if isinstance(expected, dict):
        actual_dict = cast(dict[str, object], actual)
        expected_dict = cast(dict[str, object], expected)
        require(
            set(actual_dict) == set(expected_dict),
            f"{label} object keys changed at {path}",
        )
        for key, expected_value in expected_dict.items():
            require_strict_json_equal(
                actual_dict[key],
                expected_value,
                label,
                path=f"{path}/{key}",
            )
        return
    if isinstance(expected, list):
        actual_list = cast(list[object], actual)
        expected_list = cast(list[object], expected)
        require(
            len(actual_list) == len(expected_list),
            f"{label} array length changed at {path}",
        )
        for index, (actual_value, expected_value) in enumerate(
            zip(actual_list, expected_list, strict=True)
        ):
            require_strict_json_equal(
                actual_value,
                expected_value,
                label,
                path=f"{path}/{index}",
            )
        return
    require(actual == expected, f"{label} value changed at {path}")


def stable_external_regular_file(
    path: Path, *, label: str
) -> tuple[FileEvidence, bytes]:
    try:
        before = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(f"{label}: cannot inspect {path}: {error}") from error
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"{label}: {path} must resolve to a regular non-symlink file",
    )
    try:
        first = path.read_bytes()
        middle = path.lstat()
        second = path.read_bytes()
        after = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(
            f"{label}: cannot read stable bytes: {error}"
        ) from error
    identity_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
    )
    require(
        all(getattr(before, name) == getattr(middle, name) for name in identity_fields)
        and all(
            getattr(middle, name) == getattr(after, name) for name in identity_fields
        )
        and first == second,
        f"{label}: bytes or metadata changed during observation",
    )
    evidence = FileEvidence(
        path=str(path),
        mode=stat.S_IMODE(after.st_mode),
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        sha256=hashlib.sha256(first).hexdigest(),
    )
    return evidence, first


def resolved_git_executable() -> Path:
    global _RESOLVED_GIT_EXECUTABLE
    if _RESOLVED_GIT_EXECUTABLE is not None:
        return _RESOLVED_GIT_EXECUTABLE
    discovered = shutil.which("git")
    require(discovered is not None, "cannot locate Git executable")
    candidate = Path(discovered)
    require(candidate.is_absolute(), "Git executable lookup was not absolute")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise PhaseIsolationError(f"cannot resolve Git executable: {error}") from error
    require(resolved.is_absolute(), "resolved Git executable is not absolute")
    _RESOLVED_GIT_EXECUTABLE = resolved
    return resolved


def scrubbed_git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name)
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_GRAFT_FILE": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
            "PAGER": "cat",
            "TZ": "UTC",
        }
    )
    return environment


def git_process(
    *arguments: str,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    git = resolved_git_executable()
    process = subprocess.run(
        [
            str(git),
            "-c",
            "core.replaceRefs=false",
            "-c",
            "advice.detachedHead=false",
            "-c",
            f"core.attributesFile={os.devnull}",
            "-c",
            f"core.excludesFile={os.devnull}",
            *arguments,
        ],
        cwd=ROOT,
        env=scrubbed_git_environment(),
        input=input_bytes,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        if not detail:
            detail = process.stdout.decode("utf-8", errors="replace").strip()
        raise PhaseIsolationError(
            f"git {' '.join(arguments)} failed with {process.returncode}: {detail}"
        )
    return process


def git_text(*arguments: str) -> str:
    raw = git_process(*arguments).stdout
    try:
        return raw.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            f"git {' '.join(arguments)} returned non-UTF-8 text"
        ) from error


def canonical_relative_path(raw: bytes, *, label: str) -> str:
    try:
        value = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{label}: non-UTF-8 repository path") from error
    path = PurePosixPath(value)
    require(
        bool(value)
        and not path.is_absolute()
        and str(path) == value
        and "." not in path.parts
        and ".." not in path.parts
        and "\\" not in value
        and "\n" not in value
        and "\r" not in value,
        f"{label}: non-canonical repository path {value!r}",
    )
    return value


def parse_tree(commit: str) -> dict[str, GitEntry]:
    raw = git_process("ls-tree", "-r", "-z", "--full-tree", commit).stdout
    entries: dict[str, GitEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode_raw, kind_raw, oid_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            kind = kind_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise PhaseIsolationError(
                f"cannot parse canonical Git tree entry at {commit}"
            ) from error
        path = canonical_relative_path(raw_path, label=f"tree {commit}")
        require(path not in entries, f"tree {commit}: duplicate path {path!r}")
        require(mode in {"100644", "100755"}, f"tree {commit}: forbidden mode {mode}")
        require(kind == "blob", f"tree {commit}: forbidden object type {kind}")
        require(bool(HEX40_RE.fullmatch(oid)), f"tree {commit}: invalid object id")
        entries[path] = GitEntry(mode=mode, kind=kind, oid=oid, sha256="")
    return entries


def parse_index() -> dict[str, GitEntry]:
    raw = git_process("ls-files", "--stage", "-z").stdout
    entries: dict[str, GitEntry] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode_raw, oid_raw, stage_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
            stage = stage_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError) as error:
            raise PhaseIsolationError(
                "cannot parse canonical Git index entry"
            ) from error
        path = canonical_relative_path(raw_path, label="Git index")
        require(path not in entries, f"Git index: duplicate path {path!r}")
        require(stage == "0", f"Git index: nonzero merge stage at {path!r}")
        require(mode in {"100644", "100755"}, f"Git index: forbidden mode at {path!r}")
        require(bool(HEX40_RE.fullmatch(oid)), "Git index: invalid object id")
        entries[path] = GitEntry(mode=mode, kind="blob", oid=oid, sha256="")
    return entries


def sha256_blobs(object_ids: Iterable[str]) -> dict[str, str]:
    ordered = tuple(sorted(set(object_ids)))
    if not ordered:
        return {}
    payload = "".join(f"{oid}\n" for oid in ordered).encode("ascii")
    raw = git_process("cat-file", "--batch", input_bytes=payload).stdout
    cursor = 0
    result: dict[str, str] = {}
    for expected_oid in ordered:
        newline = raw.find(b"\n", cursor)
        require(newline >= 0, "truncated git cat-file batch header")
        header = raw[cursor:newline]
        cursor = newline + 1
        fields = header.split(b" ")
        require(len(fields) == 3, "invalid git cat-file batch header")
        oid = fields[0].decode("ascii", errors="strict")
        kind = fields[1].decode("ascii", errors="strict")
        try:
            size = int(fields[2].decode("ascii", errors="strict"))
        except ValueError as error:
            raise PhaseIsolationError("invalid git cat-file object size") from error
        require(oid == expected_oid, "git cat-file batch order/object mismatch")
        require(kind == "blob" and size >= 0, f"{oid}: expected a nonnegative blob")
        end = cursor + size
        require(end < len(raw), f"{oid}: truncated git cat-file blob")
        blob = raw[cursor:end]
        cursor = end
        require(raw[cursor : cursor + 1] == b"\n", f"{oid}: missing batch delimiter")
        cursor += 1
        result[oid] = hashlib.sha256(blob).hexdigest()
    require(cursor == len(raw), "git cat-file batch returned trailing bytes")
    return result


def hydrate_tree(entries: dict[str, GitEntry]) -> dict[str, GitEntry]:
    hashes = sha256_blobs(entry.oid for entry in entries.values())
    return {
        path: GitEntry(
            mode=entry.mode,
            kind=entry.kind,
            oid=entry.oid,
            sha256=hashes[entry.oid],
        )
        for path, entry in entries.items()
    }


def stable_regular_file(relative: str) -> tuple[str, bytes]:
    candidate = ROOT / relative
    current = ROOT
    for component in PurePosixPath(relative).parts[:-1]:
        current = current / component
        try:
            metadata = current.lstat()
        except OSError as error:
            raise PhaseIsolationError(
                f"{relative!r}: cannot inspect parent directory: {error}"
            ) from error
        require(
            stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
            f"{relative!r}: parent path is not a real directory",
        )
    try:
        before = candidate.lstat()
    except OSError as error:
        raise PhaseIsolationError(
            f"{relative!r}: candidate path is missing: {error}"
        ) from error
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"{relative!r}: candidate must be a regular non-symlink file",
    )
    require(
        before.st_nlink == 1, f"{relative!r}: hard-linked candidate file is forbidden"
    )
    permissions = stat.S_IMODE(before.st_mode)
    require(
        permissions in {0o644, 0o755},
        f"{relative!r}: non-canonical permissions {permissions:#o}",
    )
    try:
        first = candidate.read_bytes()
        middle = candidate.lstat()
        second = candidate.read_bytes()
        after = candidate.lstat()
    except OSError as error:
        raise PhaseIsolationError(
            f"{relative!r}: cannot read stable bytes: {error}"
        ) from error
    identity_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
    )
    require(
        all(getattr(before, name) == getattr(middle, name) for name in identity_fields)
        and all(
            getattr(middle, name) == getattr(after, name) for name in identity_fields
        )
        and first == second,
        f"{relative!r}: candidate bytes changed during observation",
    )
    mode = "100755" if permissions == 0o755 else "100644"
    return mode, first


def git_blob_oid(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def parse_untracked() -> tuple[str, ...]:
    # Deliberately do not use --exclude-standard: workstation-local info/exclude bytes are not
    # portable to a fresh clone and therefore cannot be a semantic candidate-enumeration input.
    # The only ignore grammar is the exact tracked and protected root .gitignore.
    raw = git_process(
        "ls-files",
        "--others",
        "--exclude-from=.gitignore",
        "-z",
    ).stdout
    paths = [
        canonical_relative_path(item, label="untracked candidate")
        for item in raw.split(b"\0")
        if item
    ]
    require(paths == sorted(paths), "Git returned non-canonical untracked path order")
    require(len(paths) == len(set(paths)), "Git returned duplicate untracked paths")
    return tuple(paths)


def collect_candidate_snapshot() -> CandidateSnapshot:
    head = git_text("rev-parse", "HEAD^{commit}")
    require(bool(HEX40_RE.fullmatch(head)), "HEAD did not resolve to an exact commit")
    head_entries = parse_tree(head)
    index_entries = parse_index()
    require(
        {
            path: (entry.mode, entry.kind, entry.oid)
            for path, entry in index_entries.items()
        }
        == {
            path: (entry.mode, entry.kind, entry.oid)
            for path, entry in head_entries.items()
        },
        "Git index differs from HEAD; phase input requires an unstaged index",
    )
    untracked = parse_untracked()
    require(
        not set(untracked).intersection(index_entries),
        "candidate path is both tracked and untracked",
    )

    entries: dict[str, GitEntry] = {}
    tracked_modifications: list[str] = []
    for path in sorted((*index_entries.keys(), *untracked)):
        mode, raw = stable_regular_file(path)
        entry = GitEntry(
            mode=mode,
            kind="blob",
            oid=git_blob_oid(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
        )
        entries[path] = entry
        head_entry = head_entries.get(path)
        if head_entry is not None and (
            mode != head_entry.mode or entry.oid != head_entry.oid
        ):
            tracked_modifications.append(path)
    return CandidateSnapshot(
        entries=entries,
        head=head,
        head_entries=head_entries,
        tracked_modifications=tuple(tracked_modifications),
        untracked=untracked,
    )


def changed_paths(
    baseline: dict[str, GitEntry], candidate: dict[str, GitEntry]
) -> tuple[str, ...]:
    result: list[str] = []
    for path in sorted(set(baseline).union(candidate)):
        left = baseline.get(path)
        right = candidate.get(path)
        if (
            left is None
            or right is None
            or (left.mode, left.kind, left.sha256)
            != (right.mode, right.kind, right.sha256)
        ):
            result.append(path)
    return tuple(result)


def classified_delta(
    base: dict[str, GitEntry], candidate: dict[str, GitEntry]
) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for path in changed_paths(base, candidate):
        left = base.get(path)
        right = candidate.get(path)
        status = "A" if left is None else "D" if right is None else "M"
        result.append((path, status))
    return tuple(result)


def changed_projection(
    baseline: dict[str, GitEntry],
    candidate: dict[str, GitEntry],
    paths: Iterable[str],
) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths).difference(SELF_UNHASHED_PATHS)):
        left = baseline.get(path)
        right = candidate.get(path)
        status = "A" if left is None else "D" if right is None else "M"
        if right is None:
            line = f"{status}\0{path}\0-\0-\n"
        else:
            line = f"{status}\0{path}\0{right.mode}\0{right.sha256}\n"
        digest.update(line.encode("utf-8"))
    return digest.hexdigest()


def path_projection(entries: dict[str, GitEntry], paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        entry = entries[path]
        digest.update(
            f"{path}\0{entry.mode}\0{entry.kind}\0{entry.sha256}\n".encode("utf-8")
        )
    return digest.hexdigest()


def allowlist_digest(paths: Iterable[str]) -> str:
    ordered = tuple(paths)
    payload = "".join(f"{path}\n" for path in ordered).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def commit_identity(commit: str) -> tuple[str, tuple[str, ...]]:
    raw = git_process("cat-file", "-p", commit).stdout
    try:
        header = raw.split(b"\n\n", 1)[0].decode("ascii")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{commit}: non-ASCII commit header") from error
    tree_values = [line[5:] for line in header.splitlines() if line.startswith("tree ")]
    parent_values = [
        line[7:] for line in header.splitlines() if line.startswith("parent ")
    ]
    require(
        len(tree_values) == 1 and bool(HEX40_RE.fullmatch(tree_values[0])),
        f"{commit}: invalid tree header",
    )
    require(
        all(bool(HEX40_RE.fullmatch(parent)) for parent in parent_values),
        f"{commit}: invalid parent header",
    )
    return tree_values[0], tuple(parent_values)


def validate_unsigned_attribution_free_commit(
    commit: str,
    *,
    label: str,
    require_exact_c3_identity_and_message: bool,
) -> None:
    raw = git_process("cat-file", "-p", commit).stdout
    require(
        b"\n\n" in raw,
        f"{label}: commit object has no header/message separator",
    )
    header_raw, message_raw = raw.split(b"\n\n", 1)
    try:
        header = header_raw.decode("utf-8")
        message = message_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            f"{label}: commit header/message is not valid UTF-8"
        ) from error
    header_keys: list[str] = []
    author_values: list[str] = []
    committer_values: list[str] = []
    continuation_count = 0
    for index, line in enumerate(header.splitlines()):
        if line.startswith(" "):
            require(
                bool(header_keys),
                f"{label}: orphan commit-header continuation at line {index + 1}",
            )
            continuation_count += 1
            continue
        key, separator, value = line.partition(" ")
        require(
            bool(separator) and bool(re.fullmatch(r"[a-z][a-z0-9-]*", key)),
            f"{label}: malformed commit header at line {index + 1}",
        )
        header_keys.append(key)
        if key == "author":
            author_values.append(value)
        elif key == "committer":
            committer_values.append(value)
    forbidden_signature_headers = tuple(
        key for key in header_keys if key == "gpgsig" or key.startswith("gpgsig-")
    )
    require(
        not forbidden_signature_headers,
        f"{label}: signed commit header is forbidden: "
        + ",".join(forbidden_signature_headers),
    )
    if require_exact_c3_identity_and_message:
        require(
            header_keys == ["tree", "parent", "author", "committer"]
            and continuation_count == 0,
            f"{label}: final C3 commit headers differ from the exact unsigned "
            "single-parent Git envelope",
        )
    require(
        len(author_values) == 1 and len(committer_values) == 1,
        f"{label}: commit must contain exactly one author and one committer header",
    )
    for identity_label, value in (
        ("author", author_values[0]),
        ("committer", committer_values[0]),
    ):
        identity_and_epoch, timezone_separator, timezone = value.rpartition(" ")
        identity, epoch_separator, epoch = identity_and_epoch.rpartition(" ")
        require(
            bool(timezone_separator)
            and bool(epoch_separator)
            and bool(identity.strip()),
            f"{label}: malformed {identity_label} identity/timestamp",
        )
        require(
            bool(re.fullmatch(r"[0-9]+", epoch))
            and bool(COMMIT_TIMEZONE_RE.fullmatch(timezone)),
            f"{label}: malformed {identity_label} epoch/timezone",
        )
        identity_match = re.fullmatch(
            r"(?P<display_name>.+)[ \t]+<(?P<email>[^<>\s]+)>",
            identity,
        )
        require(
            identity_match is not None,
            f"{label}: malformed {identity_label} name/email",
        )
        display_name = cast(re.Match[str], identity_match).group("display_name")
        email = cast(re.Match[str], identity_match).group("email")
        if require_exact_c3_identity_and_message:
            require(
                display_name == EXPECTED_C3_COMMIT_DISPLAY_NAME
                and email == EXPECTED_C3_COMMIT_EMAIL,
                f"{label}: final C3 {identity_label} identity differs from "
                "the exact reviewed human identity",
            )
    require(
        message.endswith("\n") and "\r" not in message and "\x00" not in message,
        f"{label}: commit message must be LF-terminated UTF-8 without CR/NUL",
    )
    if require_exact_c3_identity_and_message:
        require(
            message_raw == EXPECTED_C3_COMMIT_MESSAGE.encode("utf-8"),
            f"{label}: final C3 commit message differs from exact reviewed bytes",
        )


def is_ancestor(ancestor: str, descendant: str) -> bool:
    process = git_process(
        "merge-base", "--is-ancestor", ancestor, descendant, check=False
    )
    if process.returncode == 0:
        return True
    if process.returncode == 1:
        return False
    detail = process.stderr.decode("utf-8", errors="replace").strip()
    raise PhaseIsolationError(
        f"cannot resolve ancestry {ancestor}..{descendant}: {detail}"
    )


def git_boundary_evidence(path: Path) -> FileEvidence:
    try:
        before = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(f"cannot inspect .git boundary: {error}") from error
    require(not stat.S_ISLNK(before.st_mode), "symlinked .git boundary is forbidden")
    if stat.S_ISREG(before.st_mode):
        require(before.st_nlink == 1, "hard-linked .git file is forbidden")
        evidence, _raw = stable_external_regular_file(path, label=".git boundary")
        return evidence
    require(stat.S_ISDIR(before.st_mode), ".git must be a file or directory")
    try:
        after = path.lstat()
    except OSError as error:
        raise PhaseIsolationError(f"cannot replay .git boundary: {error}") from error
    fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")
    require(
        all(getattr(before, name) == getattr(after, name) for name in fields),
        ".git directory metadata changed during observation",
    )
    descriptor = (
        f"directory\0{before.st_dev}\0{before.st_ino}\0"
        f"{before.st_mode}\0{before.st_nlink}\0{before.st_size}\0"
        f"{before.st_mtime_ns}\n"
    ).encode("ascii")
    return FileEvidence(
        path=str(path),
        mode=stat.S_IMODE(before.st_mode),
        size=before.st_size,
        mtime_ns=before.st_mtime_ns,
        sha256=hashlib.sha256(descriptor).hexdigest(),
    )


def parse_local_config(raw: bytes) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            raw_key, raw_value = record.split(b"\n", 1)
            key = raw_key.decode("utf-8").lower()
            value = raw_value.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            raise PhaseIsolationError(
                "cannot parse isolated local Git configuration"
            ) from error
        require(key and "\n" not in key and "\0" not in value, "invalid local Git key")
        result.append((key, value))
    for key, _value in result:
        require(
            key not in FORBIDDEN_LOCAL_CONFIG_KEYS
            and not any(
                key.startswith(prefix) for prefix in FORBIDDEN_LOCAL_CONFIG_PREFIXES
            ),
            f"forbidden local Git configuration key: {key}",
        )
    return tuple(result)


def validate_absent_git_path(path: Path, *, label: str) -> None:
    require(
        not path.exists() and not path.is_symlink(),
        f"Git overlay file is forbidden: {label}",
    )


def validate_repository_context() -> RepositoryContext:
    require(not SCRIPT_PATH.is_symlink(), "phase checker itself must not be a symlink")
    git = resolved_git_executable()
    git_evidence, _git_raw = stable_external_regular_file(
        git, label="resolved Git executable"
    )
    require(
        bool(HEX64_RE.fullmatch(git_evidence.sha256)),
        "resolved Git executable digest is not canonical SHA-256",
    )
    version_raw = git_process("--version").stdout
    try:
        version = version_raw.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise PhaseIsolationError("Git version output is not UTF-8") from error
    require(
        version.startswith("git version ") and "\n" not in version,
        "Git version output has an unexpected shape",
    )
    git_identity = GitBinaryIdentity(executable=git_evidence, version=version)

    try:
        expected_root = ROOT.resolve(strict=True)
        reported_root = Path(git_text("rev-parse", "--show-toplevel")).resolve(
            strict=True
        )
    except OSError as error:
        raise PhaseIsolationError(
            f"cannot resolve canonical repository root: {error}"
        ) from error
    require(
        reported_root == expected_root, "Git worktree root does not match checker root"
    )
    require(
        git_text("rev-parse", "--show-object-format=storage") == "sha1",
        "phase checker is pinned to this repository's SHA-1 Git object format",
    )
    require(
        git_text("rev-parse", "--is-shallow-repository") == "false",
        "shallow repositories are outside the ancestry claim",
    )

    dot_git = ROOT / ".git"
    boundary_evidence = git_boundary_evidence(dot_git)

    git_dir = Path(git_text("rev-parse", "--git-dir"))
    if not git_dir.is_absolute():
        git_dir = ROOT / git_dir
    common_git_dir = Path(git_text("rev-parse", "--git-common-dir"))
    if not common_git_dir.is_absolute():
        common_git_dir = ROOT / common_git_dir
    try:
        resolved_git_dir = git_dir.resolve(strict=True)
        resolved_common_git_dir = common_git_dir.resolve(strict=True)
    except OSError as error:
        raise PhaseIsolationError(
            f"cannot resolve Git metadata directories: {error}"
        ) from error
    require(
        resolved_git_dir.is_dir() and resolved_common_git_dir.is_dir(),
        "Git metadata roots must resolve to directories",
    )

    for relative in ("info/grafts", "objects/info/alternates"):
        validate_absent_git_path(
            resolved_common_git_dir / relative,
            label=relative,
        )
    validate_absent_git_path(
        resolved_common_git_dir / "info/attributes",
        label="info/attributes",
    )
    validate_absent_git_path(
        resolved_git_dir / "config.worktree",
        label="config.worktree",
    )

    local_config, _local_config_raw = stable_external_regular_file(
        resolved_common_git_dir / "config",
        label="local Git configuration",
    )
    config_process = git_process(
        "config",
        "--no-includes",
        "--local",
        "--null",
        "--list",
    )
    config_semantics = parse_local_config(config_process.stdout)
    config_semantics_sha256 = hashlib.sha256(
        json.dumps(
            config_semantics,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()

    replacement_refs = git_process(
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace",
    ).stdout
    require(
        not replacement_refs,
        "Git replacement references are forbidden",
    )
    return RepositoryContext(
        git_binary=git_identity,
        root=str(expected_root),
        git_boundary=boundary_evidence,
        git_dir=str(resolved_git_dir),
        common_git_dir=str(resolved_common_git_dir),
        local_config=local_config,
        local_config_semantics_sha256=config_semantics_sha256,
        info_attributes_absent=True,
        worktree_config_absent=True,
        replacement_refs_sha256=hashlib.sha256(replacement_refs).hexdigest(),
    )


def validate_commit_envelope(head: str) -> None:
    require(
        (CURRENT_ANCHOR, CURRENT_ANCHOR_TREE)
        == (C2_TOOLING_CORRECTION, C2_TOOLING_CORRECTION_TREE),
        "current phase anchor is not the exact pushed C2 tooling correction",
    )
    baseline_tree, _baseline_parents = commit_identity(SCIENTIFIC_BASELINE)
    require(
        baseline_tree == SCIENTIFIC_BASELINE_TREE,
        "scientific baseline tree pin mismatch",
    )
    delivery_tree, delivery_parents = commit_identity(DELIVERY_PARENT)
    require(
        delivery_tree == DELIVERY_PARENT_TREE,
        "delivery parent tree pin mismatch",
    )
    require(
        delivery_parents == (SCIENTIFIC_BASELINE,),
        "delivery commit is not the exact direct child of the scientific baseline",
    )
    for commit, expected_parent, expected_tree in DECLARED_COMMIT_CHAIN:
        tree, parents = commit_identity(commit)
        require(tree == expected_tree, f"{commit}: declared tree pin mismatch")
        require(
            parents == (expected_parent,),
            f"{commit}: declared single-parent pin mismatch",
        )
    require(
        is_ancestor(CURRENT_ANCHOR, head),
        "HEAD does not descend from the exact current KSG anchor",
    )

    previous = CURRENT_ANCHOR
    later_raw = git_text(
        "rev-list", "--first-parent", "--reverse", f"{CURRENT_ANCHOR}..{head}"
    )
    later = tuple(later_raw.splitlines()) if later_raw else ()
    require(
        len(later) <= MAX_POST_ANCHOR_COMMITS,
        "post-anchor history exceeds the bounded commit count",
    )
    for commit in later:
        require(bool(HEX40_RE.fullmatch(commit)), "invalid post-anchor commit id")
        _tree, parents = commit_identity(commit)
        validate_unsigned_attribution_free_commit(
            commit,
            label=f"post-anchor commit {commit}",
            require_exact_c3_identity_and_message=True,
        )
        require(
            parents == (previous,),
            f"{commit}: post-anchor history must be a single-parent fast-forward",
        )
        previous = commit


def parse_name_status(raw: bytes, *, label: str) -> tuple[tuple[str, str], ...]:
    fields = raw.split(b"\0")
    if fields and not fields[-1]:
        fields.pop()
    require(len(fields) % 2 == 0, f"{label}: malformed Git name-status stream")
    result: list[tuple[str, str]] = []
    for index in range(0, len(fields), 2):
        try:
            status_value = fields[index].decode("ascii")
        except UnicodeDecodeError as error:
            raise PhaseIsolationError(f"{label}: non-ASCII Git status") from error
        require(
            status_value in {"A", "M", "D"},
            f"{label}: forbidden Git delta status {status_value!r}",
        )
        path = canonical_relative_path(fields[index + 1], label=label)
        result.append((path, status_value))
    require(
        tuple(path for path, _status in result)
        == tuple(sorted(path for path, _status in result)),
        f"{label}: Git delta paths are not canonical and sorted",
    )
    require(
        len(result) == len({path for path, _status in result}),
        f"{label}: duplicate Git delta path",
    )
    return tuple(result)


def post_anchor_history(
    head: str,
) -> tuple[
    tuple[str, tuple[tuple[str, str], ...], dict[str, GitEntry]],
    ...,
]:
    commits_raw = git_text(
        "rev-list",
        "--first-parent",
        "--reverse",
        f"{CURRENT_ANCHOR}..{head}",
    )
    commits = tuple(commits_raw.splitlines()) if commits_raw else ()
    require(
        len(commits) <= MAX_POST_ANCHOR_COMMITS,
        "post-anchor history exceeds the bounded commit count",
    )
    previous = CURRENT_ANCHOR
    result: list[tuple[str, tuple[tuple[str, str], ...], dict[str, GitEntry]]] = []
    for commit in commits:
        raw = git_process(
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "--no-renames",
            "-r",
            "-z",
            previous,
            commit,
        ).stdout
        result.append(
            (
                commit,
                parse_name_status(raw, label=f"post-anchor commit {commit}"),
                hydrate_tree(parse_tree(commit)),
            )
        )
        previous = commit
    return tuple(result)


def validate_phase_path_policy(
    snapshot: CandidateSnapshot,
    anchor: dict[str, GitEntry],
) -> tuple[PhasePolicyEntry, ...]:
    raw = read_candidate_bytes(PHASE_PATH_POLICY)
    require(
        hashlib.sha256(raw).hexdigest() == PHASE_PATH_POLICY_SHA256,
        "phase path policy digest differs from the manually reviewed authority",
    )
    policy = canonical_json_from_bytes(raw, label=PHASE_PATH_POLICY)
    require(isinstance(policy, dict), "phase path policy root must be an object")
    require(
        set(policy)
        == {
            "anchor",
            "authority",
            "candidate_commit",
            "commit_envelope_hostile_review",
            "deletions_permitted",
            "entries",
            "historical_remediation_supersession",
            "hostile_suite_contract",
            "review_classes",
            "schema",
            "schema_revision",
        },
        "phase path policy has an unexpected top-level shape",
    )
    require(
        policy.get("schema") == "pid-rs/ksg-phase-path-policy",
        "phase path policy schema identifier is invalid",
    )
    require_strict_json_equal(
        policy.get("schema_revision"),
        6,
        "phase path policy schema revision",
    )
    require_strict_json_equal(
        policy.get("anchor"),
        {
            "commit": CURRENT_ANCHOR,
            "tree": CURRENT_ANCHOR_TREE,
        },
        "phase path policy anchor",
    )
    require(
        policy.get("deletions_permitted") is False,
        "phase path policy must forbid every deletion",
    )
    require_strict_json_equal(
        policy.get("authority"),
        {
            "authoritative": True,
            "mechanical_resealing_permitted": False,
            "scope": (
                "KSG revision-4 8b792-anchored C3 POSIX Lean replay, isolated "
                "Python-entry, evidence, and foundational-publication correction only"
            ),
        },
        "phase path policy authority contract",
    )
    expected_identity = {
        "display_name": EXPECTED_C3_COMMIT_DISPLAY_NAME,
        "email": EXPECTED_C3_COMMIT_EMAIL,
    }
    require_strict_json_equal(
        policy.get("candidate_commit"),
        {
            "author": expected_identity,
            "committer": expected_identity,
            "message": {
                "encoding": "UTF-8",
                "exact_text": EXPECTED_C3_COMMIT_MESSAGE,
                "sha256": EXPECTED_C3_COMMIT_MESSAGE_SHA256,
                "size_bytes": len(EXPECTED_C3_COMMIT_MESSAGE.encode("utf-8")),
            },
            "signature_headers_permitted": False,
        },
        "phase path policy exact candidate commit envelope",
    )
    require(
        hashlib.sha256(EXPECTED_C3_COMMIT_MESSAGE.encode("utf-8")).hexdigest()
        == EXPECTED_C3_COMMIT_MESSAGE_SHA256,
        "exact C3 commit message digest constant is internally inconsistent",
    )
    require_strict_json_equal(
        policy.get("commit_envelope_hostile_review"),
        {
            "demonstrated_intermediate_false_greens": [
                "Co-Authored-By: Codex Agent <agent@example.invalid>",
                "commit object with a gpgsig header",
                "Generated-With: Claude Code",
                "Generated with GitHub Copilot",
                "Authored by an artificial intelligence agent",
                "Tool: Codex",
            ],
            "demonstrated_intermediate_false_positives": [
                "Document papers authored by AI researchers.",
                "Test data generated by an AI benchmark fixture.",
                "human display name Ai Weiwei",
            ],
            "fixture_boundary": (
                "All hostile commits were temporary, isolated self-test or review "
                "fixtures; none was staged in the C3 worktree/index, entered the "
                "real candidate, pushed, or credited as the C3 candidate."
            ),
            "resolution": (
                "For the single permitted direct child, validate the exact finite "
                "commit message and human author/committer identities from "
                "candidate_commit, independently reject every gpgsig or gpgsig-* "
                "header, and retain hostile mutations in the executable self-test."
            ),
        },
        "phase path policy commit-envelope hostile-review record",
    )
    require_strict_json_equal(
        policy.get("historical_remediation_supersession"),
        EXPECTED_HISTORICAL_REMEDIATION_SUPERSESSION,
        "phase path policy historical remediation supersession",
    )
    require_strict_json_equal(
        policy.get("hostile_suite_contract"),
        EXPECTED_HOSTILE_SUITE_CONTRACT,
        "phase path policy hostile-suite contract",
    )
    raw_entries = policy.get("entries")
    raw_classes = policy.get("review_classes")
    require(
        isinstance(raw_entries, list) and raw_entries,
        "phase path policy entries must be a nonempty array",
    )
    require(
        isinstance(raw_classes, dict) and raw_classes,
        "phase path policy review classes must be a nonempty object",
    )
    review_classes: dict[str, tuple[str, tuple[str, ...]]] = {}
    for class_name, class_value in raw_classes.items():
        require(
            isinstance(class_name, str)
            and class_name
            and isinstance(class_value, dict)
            and set(class_value) == {"obligations", "rationale"},
            f"phase path policy review class {class_name!r} has an unexpected shape",
        )
        rationale = class_value.get("rationale")
        obligations = class_value.get("obligations")
        require(
            isinstance(rationale, str)
            and len(rationale.strip()) >= 12
            and "\n" not in rationale,
            f"phase path policy review class {class_name!r} lacks a rationale",
        )
        require(
            isinstance(obligations, list)
            and obligations
            and all(
                isinstance(item, str) and item.strip() and "\n" not in item
                for item in obligations
            )
            and len(obligations) == len(set(obligations)),
            f"phase path policy review class {class_name!r} has invalid obligations",
        )
        review_classes[class_name] = (rationale, tuple(obligations))
    require(
        review_classes == EXPECTED_CORRECTIVE_REVIEW_CLASS_CONTRACTS,
        "corrective review-class rationale/obligation contracts changed",
    )
    entries: list[PhasePolicyEntry] = []
    for index, value in enumerate(raw_entries):
        require(
            isinstance(value, dict)
            and set(value) == {"path", "review_class", "status"},
            f"phase path policy entry {index} has an unexpected shape",
        )
        raw_path = value.get("path")
        require(
            isinstance(raw_path, str),
            f"phase path policy entry {index} has a non-string path",
        )
        path = canonical_relative_path(
            raw_path.encode("utf-8"),
            label=f"phase path policy entry {index}",
        )
        status_value = value.get("status")
        review_class = value.get("review_class")
        require(
            type(status_value) is str and status_value in {"A", "M"},
            f"phase path policy entry {path!r} is not classified A or M",
        )
        require(
            isinstance(review_class, str) and review_class in review_classes,
            f"phase path policy entry {path!r} references an unknown review class",
        )
        rationale, obligations = review_classes[review_class]
        entries.append(
            PhasePolicyEntry(
                path=path,
                status=status_value,
                review_class=review_class,
                rationale=rationale,
                obligations=obligations,
            )
        )
    require(
        tuple(entry.path for entry in entries)
        == tuple(sorted(entry.path for entry in entries))
        and len(entries) == len({entry.path for entry in entries}),
        "phase path policy entries are not sorted and duplicate-free",
    )
    observed_entries = tuple(
        (entry.path, entry.status, entry.review_class) for entry in entries
    )
    require(
        observed_entries == EXPECTED_CORRECTIVE_POLICY_ENTRIES,
        "corrective phase path/status/review-class inventory changed",
    )
    policy_delta = tuple((entry.path, entry.status) for entry in entries)
    actual_delta = classified_delta(anchor, snapshot.entries)
    require(
        all(status_value != "D" for _path, status_value in actual_delta),
        "candidate delta from current anchor contains a forbidden deletion",
    )
    require(
        actual_delta == policy_delta,
        "candidate anchor delta differs from the separately reviewed A/M path policy",
    )
    require(
        (PHASE_PATH_POLICY, "A") in policy_delta,
        "C3 phase path policy must classify itself as added",
    )

    policy_by_path = {entry.path: entry.status for entry in entries}
    expected_tree = dict(anchor)
    transitioned: set[str] = set()
    for commit, changes, commit_tree in post_anchor_history(snapshot.head):
        for path, status_value in changes:
            require(
                status_value != "D",
                f"{commit}: post-anchor history contains forbidden deletion of {path}",
            )
            require(
                path in policy_by_path,
                f"{commit}: post-anchor history touched non-policy path {path}",
            )
            require(
                path not in transitioned,
                f"{commit}: policy path changed after its exact final transition: {path}",
            )
            expected_status = policy_by_path[path]
            require(
                status_value == expected_status,
                (
                    f"{commit}: policy path {path} has invalid {status_value} "
                    f"transition; expected one exact {expected_status}"
                ),
            )
            final_entry = snapshot.entries.get(path)
            require(
                final_entry is not None,
                f"{commit}: final reviewed candidate path is absent: {path}",
            )
            expected_tree[path] = final_entry
            transitioned.add(path)
        require(
            commit_tree == expected_tree,
            (
                f"{commit}: post-anchor tree is not a monotone composition of "
                "exact anchor/absent and exact final reviewed path states"
            ),
        )
    if snapshot.head != CURRENT_ANCHOR:
        require(
            transitioned == set(policy_by_path),
            "committed-descendant history did not transition every policy path exactly once",
        )
    return tuple(entries)


def validate_staged_tree_custody(
    snapshot: CandidateSnapshot,
    expected_tree: str | None,
    checkpoint_commit: str | None,
) -> tuple[str | None, str | None]:
    require(
        (expected_tree is None) == (checkpoint_commit is None),
        "--expected-candidate-tree and --checkpoint-commit must be supplied together",
    )
    if expected_tree is None:
        return None, None
    require(
        bool(HEX40_RE.fullmatch(expected_tree)),
        "expected candidate tree is not a canonical SHA-1 object id",
    )
    resolved_tree = git_text("rev-parse", f"{expected_tree}^{{tree}}")
    require(
        resolved_tree == expected_tree,
        "expected candidate tree does not resolve to the exact supplied tree id",
    )
    staged_entries = hydrate_tree(parse_tree(expected_tree))
    require(
        staged_entries == snapshot.entries,
        "external staged/checkpoint tree differs from the candidate snapshot",
    )
    whitespace_check = git_process(
        "-c",
        "advice.graftFileDeprecated=false",
        "-c",
        "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab",
        "diff-tree",
        "-r",
        "--check",
        "--no-ext-diff",
        "--no-renames",
        "--no-textconv",
        CURRENT_ANCHOR,
        expected_tree,
        "--",
        check=False,
    )
    whitespace_diagnostics = whitespace_check.stdout + whitespace_check.stderr
    require(
        whitespace_check.returncode == 0 and not whitespace_diagnostics,
        "external candidate tree failed the scrubbed anchor-to-tree Git "
        "whitespace check"
        + (
            ": "
            + whitespace_diagnostics.decode("utf-8", errors="replace").strip()
            if whitespace_diagnostics
            else ""
        ),
    )
    if checkpoint_commit is not None:
        require(
            bool(HEX40_RE.fullmatch(checkpoint_commit)),
            "checkpoint commit is not a canonical SHA-1 object id",
        )
        commit_tree, parents = commit_identity(checkpoint_commit)
        validate_unsigned_attribution_free_commit(
            checkpoint_commit,
            label=f"checkpoint commit {checkpoint_commit}",
            require_exact_c3_identity_and_message=True,
        )
        require(
            commit_tree == expected_tree,
            "checkpoint commit tree differs from the externally supplied tree",
        )
        if checkpoint_commit != snapshot.head:
            require(
                parents == (snapshot.head,),
                "detached checkpoint commit is not the exact child of snapshot HEAD",
            )
    return expected_tree, checkpoint_commit


def canonical_json_from_bytes(raw: bytes, *, label: str) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PhaseIsolationError(f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> None:
        raise PhaseIsolationError(f"{label}: non-finite JSON token {token!r}")

    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PhaseIsolationError(
            f"{label}: invalid canonical JSON: {error}"
        ) from error
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    require(
        text == rendered,
        f"{label}: JSON is not sorted two-space ASCII form with one final LF",
    )
    return value


def canonical_compact_json_from_bytes(raw: bytes, *, label: str) -> Any:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PhaseIsolationError(f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> None:
        raise PhaseIsolationError(f"{label}: non-finite JSON token {token!r}")

    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PhaseIsolationError(
            f"{label}: invalid compact canonical JSON: {error}"
        ) from error
    rendered = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    )
    require(
        text == rendered,
        f"{label}: JSON is not sorted compact ASCII form with one final LF",
    )
    return value


def canonical_fenced_json_from_memo(
    memo: str,
    *,
    begin: str,
    end: str,
    label: str,
) -> dict[str, object]:
    require(
        memo.count(begin) == 1 and memo.count(end) == 1,
        f"{label}: fenced JSON sentinels are not unique",
    )
    prefix, remainder = memo.split(begin, 1)
    payload, suffix = remainder.split(end, 1)
    require(
        prefix.endswith("```text\n") and suffix.startswith("\n```\n"),
        f"{label}: fenced JSON is not immediately bounded by a text fence",
    )
    try:
        raw = (payload + "\n").encode("ascii")
    except UnicodeEncodeError as error:
        raise PhaseIsolationError(f"{label}: fenced JSON is not ASCII") from error
    value = canonical_json_from_bytes(raw, label=label)
    require(
        type(value) is dict,
        f"{label}: fenced JSON root must have type object",
    )
    return cast(dict[str, object], value)


def canonical_compact_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def validate_c3_event_markers(
    memo: str,
    *,
    positive_codes: tuple[str, ...],
    negative_codes: tuple[str, ...],
) -> None:
    marker_re = re.compile(r"\[C3 event: ([^\]\r\n]+)\]")
    markers = tuple(match.group(1) for match in marker_re.finditer(memo))
    expected = EXPECTED_C3_POSITIVE_CODES + EXPECTED_C3_NEGATIVE_CODES
    observed_row_codes = positive_codes + negative_codes
    require(
        memo.count("[C3 event:") == 64,
        "C3 event marker prefix cardinality changed",
    )
    require(len(markers) == 64, "C3 event marker parse cardinality changed")
    require(markers == expected, "C3 event marker value or order changed")
    require(len(set(markers)) == 64, "C3 event markers are not unique")
    require(
        markers == observed_row_codes,
        "C3 event markers no longer correspond one-to-one with ledger rows",
    )


def validate_c3_precommit_review_ledger(memo: str) -> None:
    review = canonical_fenced_json_from_memo(
        memo,
        begin=C3_REVIEW_BEGIN,
        end=C3_REVIEW_END,
        label="C3 precommit review ledger",
    )
    require_strict_json_equal(
        review,
        EXPECTED_C3_PRECOMMIT_REVIEW,
        "C3 precommit review ledger",
    )
    require(
        tuple(review)
        == (
            "bounded_positive_observations",
            "negative_observations",
            "parent",
            "schema",
            "schema_revision",
        ),
        "C3 precommit review ledger root keys or canonical order changed",
    )
    require_strict_json_equal(
        review["schema"],
        "pid-rs/c3-precommit-review-ledger",
        "C3 precommit review ledger schema",
    )
    require_strict_json_equal(
        review["schema_revision"],
        2,
        "C3 precommit review ledger schema revision",
    )
    require_strict_json_equal(
        review["parent"],
        C2_TOOLING_CORRECTION,
        "C3 precommit review ledger parent",
    )

    positive_raw = review["bounded_positive_observations"]
    negative_raw = review["negative_observations"]
    require(
        type(positive_raw) is list and len(positive_raw) == 18,
        "C3 precommit review ledger must contain exactly 18 positive rows",
    )
    require(
        type(negative_raw) is list and len(negative_raw) == 46,
        "C3 precommit review ledger must contain exactly 46 negative rows",
    )
    positive = cast(list[object], positive_raw)
    negative = cast(list[object], negative_raw)
    require(
        len(positive) + len(negative) == 64,
        "C3 precommit review ledger must contain exactly 64 rows",
    )
    require(
        all(type(row) is dict for row in (*positive, *negative)),
        "C3 precommit review ledger rows must have type object",
    )
    positive_rows = cast(list[dict[str, object]], positive)
    negative_rows = cast(list[dict[str, object]], negative)

    positive_codes = tuple(row["observation_code"] for row in positive_rows)
    negative_codes = tuple(row["reason_code"] for row in negative_rows)
    require(
        all(type(code) is str and cast(str, code).isascii() for code in positive_codes),
        "C3 positive observation codes must be ASCII strings",
    )
    require(
        all(type(code) is str and cast(str, code).isascii() for code in negative_codes),
        "C3 negative reason codes must be ASCII strings",
    )
    observed_positive_codes = cast(tuple[str, ...], positive_codes)
    observed_negative_codes = cast(tuple[str, ...], negative_codes)
    require(
        observed_positive_codes == EXPECTED_C3_POSITIVE_CODES,
        "C3 positive observation code inventory or order changed",
    )
    require(
        observed_negative_codes == EXPECTED_C3_NEGATIVE_CODES,
        "C3 negative reason code inventory or order changed",
    )
    require(
        len(set(observed_positive_codes)) == 18
        and len(set(observed_negative_codes)) == 46
        and set(observed_positive_codes).isdisjoint(observed_negative_codes),
        "C3 ledger codes are not globally unique and bucket-disjoint",
    )

    positive_classes = tuple(row["event_class"] for row in positive_rows)
    negative_classes = tuple(row["event_class"] for row in negative_rows)
    positive_credits = tuple(row["credit"] for row in positive_rows)
    negative_credits = tuple(row["credit"] for row in negative_rows)
    require(
        all(type(value) is str for value in positive_classes)
        and set(positive_classes)
        == {
            "bounded_design_positive_no_runtime_credit",
            "superseded_bounded_positive",
        },
        "C3 positive event classes changed",
    )
    require(
        all(type(value) is str for value in negative_classes)
        and set(negative_classes)
        == {
            "candidate_supersession",
            "repository_custody_defect",
            "repository_publication_defect",
            "repository_verifier_defect",
            "review_hypothesis_falsified",
            "reviewer_tool_process_negative",
        },
        "C3 negative event classes changed",
    )
    require(
        all(type(value) is str for value in positive_credits)
        and set(positive_credits) == {"bounded_design_only", "superseded_bounded_only"},
        "C3 positive credit classes changed",
    )
    require(
        all(type(value) is str and value == "none" for value in negative_credits),
        "C3 negative observations must receive no credit",
    )

    session_ids: list[int] = []
    candidate_trees: list[str] = []
    commits_or_checkpoints: list[str] = []
    for row in (*positive_rows, *negative_rows):
        if "session_id" in row and row["session_id"] is not None:
            session_id = row["session_id"]
            require(
                type(session_id) is int,
                "C3 ledger session_id values must have type integer",
            )
            session_ids.append(cast(int, session_id))
        if "candidate_tree" in row and row["candidate_tree"] is not None:
            candidate_tree = row["candidate_tree"]
            require(
                type(candidate_tree) is str
                and HEX40_RE.fullmatch(cast(str, candidate_tree)) is not None,
                "C3 ledger candidate_tree values must be lowercase SHA-1 ids",
            )
            candidate_trees.append(cast(str, candidate_tree))
        if "candidate_commit" in row and row["candidate_commit"] is not None:
            candidate_commit = row["candidate_commit"]
            require(
                type(candidate_commit) is str
                and HEX40_RE.fullmatch(cast(str, candidate_commit)) is not None,
                "C3 ledger candidate_commit values must be lowercase SHA-1 ids",
            )
            commits_or_checkpoints.append(cast(str, candidate_commit))
    require(
        tuple(sorted(set(session_ids))) == EXPECTED_C3_SESSION_IDS,
        "C3 ledger session-id inventory changed",
    )
    require(
        tuple(sorted(set(candidate_trees))) == EXPECTED_C3_CANDIDATE_TREES,
        "C3 ledger candidate-tree inventory changed",
    )
    require(
        tuple(sorted(set(commits_or_checkpoints)))
        == EXPECTED_C3_COMMITS_OR_CHECKPOINTS,
        "C3 ledger commit/checkpoint inventory changed",
    )
    v8_codes = tuple(
        code
        for code in observed_positive_codes + observed_negative_codes
        if code.startswith("V8_")
    )
    require(
        v8_codes
        == ("V8_REVIEW_TRACKED_RESUME_APPEND_RESTORED_BEFORE_CANDIDATE",),
        "C3 ledger must retain exactly the reviewed V8 negative",
    )
    validate_c3_event_markers(
        memo,
        positive_codes=observed_positive_codes,
        negative_codes=observed_negative_codes,
    )
    require(
        hashlib.sha256(canonical_compact_json_bytes(review)).hexdigest()
        == EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256,
        "C3 precommit review compact projection digest changed",
    )


def expected_c3_local_artifact_parity(
    artifacts: LeanPortabilityArtifacts,
) -> dict[str, object]:
    direct_raw = artifacts.direct_evidence
    mutation_raw = artifacts.mutation_evidence
    candidate_pdf_raw = read_candidate_bytes(FOUNDATIONAL_SXPID_AUDIT_PDF)
    candidate_artifacts = (
        (FOUNDATIONAL_SXPID_DIRECT_EVIDENCE, direct_raw),
        (FOUNDATIONAL_SXPID_MUTATION_EVIDENCE, mutation_raw),
        (FOUNDATIONAL_SXPID_AUDIT_PDF, candidate_pdf_raw),
    )
    for path, raw in candidate_artifacts:
        require(
            path in EXPECTED_BOUND_ALLOWED_BLOBS,
            f"C3 local artifact parity path is absent from the bound inventory: {path}",
        )
        require(
            (hashlib.sha256(raw).hexdigest(), len(raw))
            == EXPECTED_C3_LOCAL_ARTIFACT_CANDIDATE_PINS[path],
            f"C3 local artifact parity candidate pin changed: {path}",
        )

    direct = canonical_compact_json_from_bytes(
        direct_raw,
        label="C3 local artifact parity direct Lean evidence",
    )
    mutation = canonical_compact_json_from_bytes(
        mutation_raw,
        label="C3 local artifact parity mutation evidence",
    )
    require(
        type(direct) is dict and type(mutation) is dict,
        "C3 local artifact parity Lean evidence roots must have type object",
    )
    require_strict_json_equal(
        cast(dict[str, object], direct).get("schema"),
        "pid-rs/lean-descriptor-factorization-check/v4",
        "C3 local artifact parity direct evidence schema",
    )
    require_strict_json_equal(
        cast(dict[str, object], mutation).get("schema"),
        "pid-rs/lean-descriptor-factorization-mutations/v4",
        "C3 local artifact parity mutation evidence schema",
    )

    require(
        artifacts.parser_normal == artifacts.parser_optimized,
        "C3 local artifact parity normal and optimized parser bytes differ",
    )
    parser_normal = canonical_compact_json_from_bytes(
        artifacts.parser_normal,
        label="C3 local artifact parity normal parser evidence",
    )
    parser_optimized = canonical_compact_json_from_bytes(
        artifacts.parser_optimized,
        label="C3 local artifact parity optimized parser evidence",
    )
    require(
        type(parser_normal) is dict and type(parser_optimized) is dict,
        "C3 local artifact parity parser roots must have type object",
    )
    parser_schema = (
        "pid-rs/lean-descriptor-factorization-"
        "version-parser-posix-custody-self-test/v4"
    )
    require_strict_json_equal(
        cast(dict[str, object], parser_normal).get("schema"),
        parser_schema,
        "C3 local artifact parity normal parser schema",
    )
    require_strict_json_equal(
        cast(dict[str, object], parser_optimized).get("schema"),
        parser_schema,
        "C3 local artifact parity optimized parser schema",
    )
    normal_sha256 = hashlib.sha256(artifacts.parser_normal).hexdigest()
    optimized_sha256 = hashlib.sha256(artifacts.parser_optimized).hexdigest()
    require(
        normal_sha256
        == optimized_sha256
        == EXPECTED_LEAN_PORTABILITY_PARSER_RECEIPT_SHA256,
        "C3 local artifact parity parser receipt digest changed",
    )

    parent_pdf_raw = git_blob_at(C2_TOOLING_CORRECTION, FOUNDATIONAL_SXPID_AUDIT_PDF)
    require(
        len(parent_pdf_raw) == EXPECTED_C3_PARENT_PDF_SIZE_BYTES
        and hashlib.sha256(parent_pdf_raw).hexdigest()
        == EXPECTED_C3_PARENT_PDF_SHA256,
        "C3 local artifact parity exact-parent PDF blob changed",
    )

    return {
        "candidate_repository_artifacts": [
            {
                "evidence_schema": "pid-rs/lean-descriptor-factorization-check/v4",
                "path": FOUNDATIONAL_SXPID_DIRECT_EVIDENCE,
                "retention_class": "candidate_repository_artifact",
                "sha256": hashlib.sha256(direct_raw).hexdigest(),
                "size_bytes": len(direct_raw),
            },
            {
                "evidence_schema": "pid-rs/lean-descriptor-factorization-mutations/v4",
                "path": FOUNDATIONAL_SXPID_MUTATION_EVIDENCE,
                "retention_class": "candidate_repository_artifact",
                "sha256": hashlib.sha256(mutation_raw).hexdigest(),
                "size_bytes": len(mutation_raw),
            },
            {
                "path": FOUNDATIONAL_SXPID_AUDIT_PDF,
                "retention_class": "candidate_repository_artifact",
                "sha256": hashlib.sha256(candidate_pdf_raw).hexdigest(),
                "size_bytes": len(candidate_pdf_raw),
            },
        ],
        "local_review_artifacts": [
            {
                "evidence_schema": parser_schema,
                "execution_mode": "normal",
                "retention_class": "local_review_artifact",
                "sha256": normal_sha256,
                "size_bytes": len(artifacts.parser_normal),
            },
            {
                "evidence_schema": parser_schema,
                "execution_mode": "optimized",
                "retention_class": "local_review_artifact",
                "sha256": optimized_sha256,
                "size_bytes": len(artifacts.parser_optimized),
            },
        ],
        "normal_optimized_parser_bytes_equal": True,
        "parent": C2_TOOLING_CORRECTION,
        "parent_repository_artifacts": [
            {
                "commit": C2_TOOLING_CORRECTION,
                "path": FOUNDATIONAL_SXPID_AUDIT_PDF,
                "retention_class": "exact_parent_git_blob",
                "sha256": hashlib.sha256(parent_pdf_raw).hexdigest(),
                "size_bytes": len(parent_pdf_raw),
            }
        ],
        "schema": "pid-rs/c3-local-artifact-parity",
        "schema_revision": 1,
    }


def validate_c3_local_artifact_parity(
    memo_raw: bytes,
    artifacts: LeanPortabilityArtifacts,
) -> None:
    try:
        memo = memo_raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            "C3 local artifact parity memo is not UTF-8"
        ) from error
    parity = canonical_fenced_json_from_memo(
        memo,
        begin=C3_LOCAL_ARTIFACT_BEGIN,
        end=C3_LOCAL_ARTIFACT_END,
        label="C3 local artifact parity",
    )

    forbidden_normalized_keys = {
        "candidatecommit",
        "candidatehead",
        "candidatetree",
        "checkerdigest",
        "checkerhash",
        "checkersha",
        "checkersha256",
        "checkersize",
        "checkersizebytes",
        "checkpointcommit",
        "checkpointhead",
        "checkpointtree",
        "currentcandidatecommit",
        "currentcandidatehead",
        "currentcandidatetree",
        "currentcommit",
        "currenttree",
        "finalcandidatecommit",
        "finalcandidatetree",
        "memodigest",
        "memohash",
        "memosha",
        "memosha256",
        "memosize",
        "memosizebytes",
        "selftestdigest",
        "selftesthash",
        "selftestsha",
        "selftestsha256",
        "selftestsize",
        "selftestsizebytes",
    }

    def reject_forbidden_keys(value: object, path: str) -> None:
        if type(value) is dict:
            for key, nested in cast(dict[str, object], value).items():
                normalized = re.sub(r"[^a-z0-9]", "", key.lower())
                require(
                    normalized not in forbidden_normalized_keys,
                    f"C3 local artifact parity contains forbidden self-reference key at {path}.{key}",
                )
                reject_forbidden_keys(nested, f"{path}.{key}")
        elif type(value) is list:
            for index, nested in enumerate(cast(list[object], value)):
                reject_forbidden_keys(nested, f"{path}[{index}]")

    reject_forbidden_keys(parity, "$")
    expected = expected_c3_local_artifact_parity(artifacts)
    require_strict_json_equal(parity, expected, "C3 local artifact parity")
    require(
        hashlib.sha256(canonical_compact_json_bytes(parity)).hexdigest()
        == EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256,
        "C3 local artifact parity compact projection digest changed",
    )


def read_candidate_bytes(relative: str) -> bytes:
    _mode, raw = stable_regular_file(relative)
    return raw


def git_blob_at(commit: str, relative: str) -> bytes:
    process = git_process("show", f"{commit}:{relative}")
    return process.stdout


def validate_prior_c2_history() -> None:
    raw_delta = git_process(
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "--no-renames",
        "-r",
        "-z",
        CORRECTIVE_PARENT,
        C2_TOOLING_CORRECTION,
    ).stdout
    require(
        parse_name_status(raw_delta, label="af509-to-C2 tooling correction")
        == EXPECTED_C2_TOOLING_DELTA,
        "af509-to-C2 nine-path history changed",
    )

    raw_policy = git_blob_at(C2_TOOLING_CORRECTION, PRIOR_PHASE_PATH_POLICY)
    require(
        hashlib.sha256(raw_policy).hexdigest() == PRIOR_PHASE_PATH_POLICY_SHA256,
        "C2 phase policy differs from its preserved reviewed bytes",
    )
    require(
        read_candidate_bytes(PRIOR_PHASE_PATH_POLICY) == raw_policy,
        "candidate changed the preserved C2 phase policy",
    )
    prior_policy = canonical_json_from_bytes(
        raw_policy,
        label="preserved C2 phase path policy",
    )
    require(
        isinstance(prior_policy, dict)
        and set(prior_policy)
        == {
            "anchor",
            "authority",
            "deletions_permitted",
            "entries",
            "review_classes",
            "schema",
            "schema_revision",
        },
        "preserved C2 phase policy shape changed",
    )
    require_strict_json_equal(
        {
            "anchor": prior_policy.get("anchor"),
            "deletions_permitted": prior_policy.get("deletions_permitted"),
            "schema": prior_policy.get("schema"),
            "schema_revision": prior_policy.get("schema_revision"),
        },
        {
            "anchor": {
                "commit": CORRECTIVE_PARENT,
                "tree": CORRECTIVE_PARENT_TREE,
            },
            "deletions_permitted": False,
            "schema": "pid-rs/ksg-phase-path-policy",
            "schema_revision": 3,
        },
        "preserved C2 phase policy identity",
    )
    raw_entries = prior_policy.get("entries")
    require(
        isinstance(raw_entries, list),
        "preserved C2 phase policy entries are not an array",
    )
    observed_entries: list[tuple[str, str, str]] = []
    for index, raw_entry in enumerate(raw_entries):
        require(
            isinstance(raw_entry, dict)
            and set(raw_entry) == {"path", "review_class", "status"},
            f"preserved C2 policy entry {index} has an unexpected shape",
        )
        path = raw_entry.get("path")
        status_value = raw_entry.get("status")
        review_class = raw_entry.get("review_class")
        require(
            isinstance(path, str)
            and isinstance(status_value, str)
            and isinstance(review_class, str),
            f"preserved C2 policy entry {index} has an invalid type",
        )
        observed_entries.append((path, status_value, review_class))
    require(
        tuple(observed_entries) == EXPECTED_C2_TOOLING_POLICY_ENTRIES,
        "preserved C2 nine-path policy inventory changed",
    )

    for relative in (
        CORRECTIVE_EVIDENCE,
        PRIOR_PHASE_PATH_POLICY,
        PUBLIC_CI_FAILURE_RECEIPT,
    ):
        require(
            read_candidate_bytes(relative)
            == git_blob_at(C2_TOOLING_CORRECTION, relative),
            f"candidate changed preserved C2 evidence: {relative}",
        )


EXACT_STDIN_BOOTSTRAP = (
    "import sys\n"
    "logical_file = sys.argv[1]\n"
    "sys.argv = [logical_file, *sys.argv[2:]]\n"
    "source = sys.stdin.buffer.read()\n"
    "namespace = {\n"
    "    '__name__': '__main__',\n"
    "    '__file__': logical_file,\n"
    "    '__package__': None,\n"
    "    '__cached__': None,\n"
    "}\n"
    "code = compile(\n"
    "    source,\n"
    "    logical_file,\n"
    "    'exec',\n"
    "    dont_inherit=True,\n"
    "    optimize=sys.flags.optimize,\n"
    ")\n"
    "exec(code, namespace)\n"
)
EXPECTED_EXACT_STDIN_BOOTSTRAP_SHA256 = (
    "6f1a7bf46ea6c40749092b0944107dd07dafb86b549399749cfa988f169f9620"
)
EXPECTED_LEAN_PORTABILITY_PARSER_RECEIPT_SHA256 = (
    "b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6"
)


def _minimal_python_child_environment(private_root: Path) -> dict[str, str]:
    """Project only neutral host necessities into an isolated child."""

    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "TMPDIR": str(private_root / "tmp"),
        "TZ": "UTC",
    }
    for name in ("COMSPEC", "HOME", "SystemRoot", "USERPROFILE", "WINDIR"):
        value = os.environ.get(name)
        if value is not None:
            environment[name] = value
    return environment


def run_lean_portability_parser(*, optimized: bool) -> bytes:
    """Execute digest-bound candidate bytes, never the live source pathname."""

    self_relative = "scripts/check-lean-descriptor-factorization-self-test.py"
    checker_relative = "scripts/check-lean-descriptor-factorization.py"
    self_raw = read_candidate_bytes(self_relative)
    checker_raw = read_candidate_bytes(checker_relative)
    require(
        hashlib.sha256(self_raw).hexdigest()
        == EXPECTED_BOUND_ALLOWED_BLOBS[self_relative][1],
        "Lean portability self-test bytes differ from the reviewed candidate pin",
    )
    require(
        hashlib.sha256(checker_raw).hexdigest()
        == EXPECTED_BOUND_ALLOWED_BLOBS[checker_relative][1],
        "Lean portability checker bytes differ from the reviewed candidate pin",
    )
    try:
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-lean-portability-exact-child-"
        ) as directory:
            private_root = Path(directory).resolve()
            scripts = private_root / "scripts"
            child_tmp = private_root / "tmp"
            scripts.mkdir(mode=0o700)
            child_tmp.mkdir(mode=0o700)
            self_path = scripts / PurePosixPath(self_relative).name
            checker_path = scripts / PurePosixPath(checker_relative).name
            self_path.write_bytes(self_raw)
            checker_path.write_bytes(checker_raw)
            self_path.chmod(0o600)
            checker_path.chmod(0o600)

            command = [sys.executable, "-I", "-S"]
            if optimized:
                command.append("-O")
            command.extend(
                (
                    "-c",
                    EXACT_STDIN_BOOTSTRAP,
                    str(self_path),
                    "--parser-only",
                )
            )
            process = subprocess.run(
                command,
                cwd=private_root,
                env=_minimal_python_child_environment(private_root),
                input=self_raw,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )
            require(
                self_path.read_bytes() == self_raw
                and checker_path.read_bytes() == checker_raw,
                "private Lean portability child source bytes changed during execution",
            )
    except (OSError, subprocess.SubprocessError) as error:
        raise PhaseIsolationError(
            f"cannot execute {'optimized' if optimized else 'normal'} "
            f"Lean portability parser controls: {error}"
        ) from error
    require(
        process.returncode == 0,
        (
            f"{'optimized' if optimized else 'normal'} Lean portability parser "
            "controls failed: "
            f"{process.stderr.decode('utf-8', errors='replace').strip()}"
        ),
    )
    require(
        process.stderr == b"",
        (
            f"{'optimized' if optimized else 'normal'} Lean portability parser "
            "controls emitted stderr"
        ),
    )
    canonical_compact_json_from_bytes(
        process.stdout,
        label=(
            f"{'optimized' if optimized else 'normal'} Lean portability "
            "parser evidence"
        ),
    )
    return process.stdout


def validate_lean_evidence_portability() -> LeanPortabilityArtifacts:
    checker_path = "scripts/check-lean-descriptor-factorization.py"
    self_test_path = "scripts/check-lean-descriptor-factorization-self-test.py"
    evidence_path = (
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json"
    )
    mutation_path = (
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json"
    )
    checker_sha256 = hashlib.sha256(read_candidate_bytes(checker_path)).hexdigest()
    self_test_sha256 = hashlib.sha256(
        read_candidate_bytes(self_test_path)
    ).hexdigest()
    source_models: dict[str, ast.Module] = {}
    for relative in (checker_path, self_test_path):
        try:
            source_text = read_candidate_bytes(relative).decode("utf-8")
            source_tree = ast.parse(source_text, filename=relative)
        except (UnicodeDecodeError, SyntaxError) as error:
            raise PhaseIsolationError(
                f"cannot inspect Lean portability source model {relative}: {error}"
            ) from error
        require(
            not any(isinstance(node, ast.Assert) for node in ast.walk(source_tree)),
            f"Lean portability source contains optimization-removable assert: {relative}",
        )
        source_models[relative] = source_tree

    checker_model = source_models[checker_path]
    checker_functions = {
        node.name: node
        for node in checker_model.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    require(
        {
            "decode_raw_lean_process",
            "_run_lean_process",
            "run_lean_text",
            "verify_post_execution_custody",
        }.issubset(checker_functions),
        "Lean portability descriptor-bound child source model is incomplete",
    )
    decode_model = checker_functions["decode_raw_lean_process"]
    raw_cr_rejections = [
        node
        for node in ast.walk(decode_model)
        if isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Constant)
        and node.left.value == b"\r"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.NotIn)
    ]
    strict_utf8_decode_calls = [
        node
        for node in ast.walk(decode_model)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "decode"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "utf-8"
        and any(
            keyword.arg == "errors"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "strict"
            for keyword in node.keywords
        )
    ]
    decode_loops = [
        statement
        for statement in decode_model.body
        if isinstance(statement, ast.For)
    ]
    decode_loop = decode_loops[0] if len(decode_loops) == 1 else None
    decode_loop_target = (
        decode_loop.target if isinstance(decode_loop, ast.For) else None
    )
    decode_loop_iter = decode_loop.iter if isinstance(decode_loop, ast.For) else None
    completed_buffer_loop_order_is_exact = (
        isinstance(decode_loop_target, ast.Tuple)
        and len(decode_loop_target.elts) == 2
        and all(isinstance(item, ast.Name) for item in decode_loop_target.elts)
        and tuple(cast(ast.Name, item).id for item in decode_loop_target.elts)
        == ("stream_name", "raw")
        and isinstance(decode_loop_iter, ast.Tuple)
        and len(decode_loop_iter.elts) == 2
        and all(
            isinstance(item, ast.Tuple) and len(item.elts) == 2
            for item in decode_loop_iter.elts
        )
        and all(
            isinstance(cast(ast.Tuple, item).elts[0], ast.Constant)
            and isinstance(cast(ast.Tuple, item).elts[1], ast.Attribute)
            and isinstance(cast(ast.Attribute, cast(ast.Tuple, item).elts[1]).value, ast.Name)
            and cast(ast.Name, cast(ast.Attribute, cast(ast.Tuple, item).elts[1]).value).id
            == "probe"
            for item in decode_loop_iter.elts
        )
        and tuple(
            (
                cast(ast.Constant, cast(ast.Tuple, item).elts[0]).value,
                cast(ast.Attribute, cast(ast.Tuple, item).elts[1]).attr,
            )
            for item in decode_loop_iter.elts
        )
        == (("stdout", "stdout"), ("stderr", "stderr"))
    )
    cr_rejection_precedes_strict_decode = (
        isinstance(decode_loop, ast.For)
        and len(decode_loop.body) == 2
        and not decode_loop.orelse
        and len(raw_cr_rejections) == 1
        and isinstance(decode_loop.body[0], ast.Expr)
        and isinstance(decode_loop.body[0].value, ast.Call)
        and isinstance(decode_loop.body[0].value.func, ast.Name)
        and decode_loop.body[0].value.func.id == "require"
        and bool(decode_loop.body[0].value.args)
        and decode_loop.body[0].value.args[0] is raw_cr_rejections[0]
        and len(strict_utf8_decode_calls) == 1
        and isinstance(decode_loop.body[1], ast.Try)
        and len(decode_loop.body[1].body) == 1
        and strict_utf8_decode_calls[0] in tuple(ast.walk(decode_loop.body[1]))
    )
    run_process_model = checker_functions["_run_lean_process"]
    fchdir_calls = [
        node
        for node in ast.walk(run_process_model)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "fchdir"
    ]
    subprocess_calls = [
        node
        for node in ast.walk(run_process_model)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    raw_decode_returns = [
        node
        for node in ast.walk(run_process_model)
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "decode_raw_lean_process"
    ]
    subprocess_keywords = (
        {keyword.arg for keyword in subprocess_calls[0].keywords}
        if len(subprocess_calls) == 1
        else set()
    )
    subprocess_stdin_keywords = (
        [
            keyword
            for keyword in subprocess_calls[0].keywords
            if keyword.arg == "stdin"
        ]
        if len(subprocess_calls) == 1
        else []
    )
    stdin_is_exact_devnull = (
        len(subprocess_stdin_keywords) == 1
        and isinstance(subprocess_stdin_keywords[0].value, ast.Attribute)
        and isinstance(subprocess_stdin_keywords[0].value.value, ast.Name)
        and subprocess_stdin_keywords[0].value.value.id == "subprocess"
        and subprocess_stdin_keywords[0].value.attr == "DEVNULL"
    )
    require(
        len(raw_cr_rejections) == 1
        and len(strict_utf8_decode_calls) == 1
        and completed_buffer_loop_order_is_exact
        and cr_rejection_precedes_strict_decode
        and len(fchdir_calls) == 1
        and len(subprocess_calls) == 1
        and subprocess_keywords
        >= {"pass_fds", "preexec_fn", "stderr", "stdin", "stdout"}
        and stdin_is_exact_devnull
        and not subprocess_keywords.intersection(
            {"cwd", "encoding", "errors", "text", "universal_newlines"}
        )
        and len(raw_decode_returns) == 1,
        "Lean portability descriptor-pinned child source model changed",
    )
    post_custody_model = checker_functions["verify_post_execution_custody"]
    require(
        len(post_custody_model.body) >= 4
        and isinstance(post_custody_model.body[1], ast.Assign)
        and isinstance(post_custody_model.body[1].value, ast.Call)
        and isinstance(post_custody_model.body[1].value.func, ast.Name)
        and post_custody_model.body[1].value.func.id == "_run_lean_process"
        and len(post_custody_model.body[1].value.args) == 2
        and isinstance(post_custody_model.body[1].value.args[1], ast.List)
        and len(post_custody_model.body[1].value.args[1].elts) == 1
        and isinstance(
            post_custody_model.body[1].value.args[1].elts[0],
            ast.Constant,
        )
        and post_custody_model.body[1].value.args[1].elts[0].value == "--version"
        and isinstance(post_custody_model.body[2], ast.Expr)
        and isinstance(post_custody_model.body[3], ast.For),
        "Lean portability terminal version-probe/replay ordering changed",
    )

    normal_raw = run_lean_portability_parser(optimized=False)
    optimized_raw = run_lean_portability_parser(optimized=True)
    require(
        normal_raw == optimized_raw,
        "normal and optimized Lean portability parser evidence differs byte-for-byte",
    )
    require(
        hashlib.sha256(normal_raw).hexdigest()
        == EXPECTED_LEAN_PORTABILITY_PARSER_RECEIPT_SHA256,
        "Lean portability parser receipt digest changed",
    )
    parsed_output = canonical_compact_json_from_bytes(
        normal_raw,
        label="Lean portability parser replay",
    )
    require(
        isinstance(parsed_output, dict)
        and set(parsed_output)
        == {
            "boundary",
            "descriptor_checker_source_sha256",
            "exact_source_loader_controls",
            "exact_source_loader_controls_passed",
            "input_snapshot_hostile_cases",
            "input_snapshot_hostile_cases_rejected",
            "lean_version_hostile_cases",
            "lean_version_hostile_cases_rejected",
            "lean_version_portability_controls",
            "lean_version_portability_controls_accepted",
            "lean_version_portable_identity",
            "private_materialization_controls",
            "private_materialization_controls_passed",
            "process_stdin_isolation_subcontrols",
            "process_stdin_isolation_subcontrols_passed",
            "raw_process_transport_hostile_cases",
            "raw_process_transport_hostile_cases_rejected",
            "raw_process_transport_order_subcontrols",
            "raw_process_transport_order_subcontrols_rejected",
            "retained_negative_controls",
            "retained_negative_controls_demonstrated",
            "schema",
            "self_test_source_sha256",
            "status",
        },
        "Lean portability parser replay has an unexpected shape",
    )
    parser_output = cast(dict[str, Any], parsed_output)
    portable_identity = {
        "build": "Release",
        "commit": "8c9756b28d64dab099da31a4c09229a9e6a2ef35",
        "version": "4.32.0",
    }
    parser_boundary = (
        "These POSIX no-kernel controls exercise strict parsing, the cross-platform "
        "macOS/Linux evidence projection, pre-execution source digest binding, "
        "tracked-input private materialization, descriptor-pinned child CWD, "
        "environment scrubbing, DEVNULL child stdin, raw-byte subprocess capture "
        "before strict UTF-8 decoding, explicit stdout-before-stderr mixed-fault "
        "precedence, and bounded snapshot rejection. Retained negatives "
        "show generic endpoint replay missing swap/use/restore, a query-subtree swap "
        "surviving project-FD pinning, HOME influencing live launcher state, and "
        "dependency-cache bytes remaining live. These controls do not execute Lean, "
        "kernel-check a theorem, support native Windows handle custody, authenticate "
        "executable or dependency bytes, establish cross-platform kernel equivalence, "
        "cap captured-output memory, or terminate descendants when the direct child "
        "times out. "
        "PYTHONDONTWRITEBYTECODE alone would not prevent consumption of a pre-existing "
        "unchecked-hash pyc."
    )
    require_strict_json_equal(
        {
            "boundary": parser_output.get("boundary"),
            "descriptor_checker_source_sha256": parser_output.get(
                "descriptor_checker_source_sha256"
            ),
            "exact_source_loader_controls_passed": parser_output.get(
                "exact_source_loader_controls_passed"
            ),
            "input_snapshot_hostile_cases_rejected": parser_output.get(
                "input_snapshot_hostile_cases_rejected"
            ),
            "lean_version_hostile_cases_rejected": parser_output.get(
                "lean_version_hostile_cases_rejected"
            ),
            "lean_version_portability_controls_accepted": parser_output.get(
                "lean_version_portability_controls_accepted"
            ),
            "lean_version_portable_identity": parser_output.get(
                "lean_version_portable_identity"
            ),
            "private_materialization_controls_passed": parser_output.get(
                "private_materialization_controls_passed"
            ),
            "process_stdin_isolation_subcontrols_passed": parser_output.get(
                "process_stdin_isolation_subcontrols_passed"
            ),
            "raw_process_transport_hostile_cases_rejected": parser_output.get(
                "raw_process_transport_hostile_cases_rejected"
            ),
            "raw_process_transport_order_subcontrols_rejected": parser_output.get(
                "raw_process_transport_order_subcontrols_rejected"
            ),
            "retained_negative_controls_demonstrated": parser_output.get(
                "retained_negative_controls_demonstrated"
            ),
            "schema": parser_output.get("schema"),
            "self_test_source_sha256": parser_output.get(
                "self_test_source_sha256"
            ),
            "status": parser_output.get("status"),
        },
        {
            "boundary": parser_boundary,
            "descriptor_checker_source_sha256": checker_sha256,
            "exact_source_loader_controls_passed": 4,
            "input_snapshot_hostile_cases_rejected": 6,
            "lean_version_hostile_cases_rejected": 19,
            "lean_version_portability_controls_accepted": 2,
            "lean_version_portable_identity": portable_identity,
            "private_materialization_controls_passed": 3,
            "process_stdin_isolation_subcontrols_passed": 1,
            "raw_process_transport_hostile_cases_rejected": 5,
            "raw_process_transport_order_subcontrols_rejected": 1,
            "retained_negative_controls_demonstrated": 4,
            "schema": (
                "pid-rs/lean-descriptor-factorization-"
                "version-parser-posix-custody-self-test/v4"
            ),
            "self_test_source_sha256": self_test_sha256,
            "status": "passed",
        },
        "Lean portability parser replay identity",
    )

    controls = parser_output.get("lean_version_portability_controls")
    hostile = parser_output.get("lean_version_hostile_cases")
    exact_source_controls = parser_output.get("exact_source_loader_controls")
    snapshot_hostile = parser_output.get("input_snapshot_hostile_cases")
    private_controls = parser_output.get("private_materialization_controls")
    process_stdin_controls = parser_output.get(
        "process_stdin_isolation_subcontrols"
    )
    raw_transport_hostile = parser_output.get(
        "raw_process_transport_hostile_cases"
    )
    raw_transport_order_controls = parser_output.get(
        "raw_process_transport_order_subcontrols"
    )
    retained_negatives = parser_output.get("retained_negative_controls")
    require_strict_json_equal(
        exact_source_controls,
        [
            {
                "demonstrated": True,
                "name": "sourcefileloader_unchecked_hash_pyc_substitution",
                "observed": "malicious-cache",
                "probe_sha256": EXPECTED_EXACT_SOURCE_CONTROL_PROBES[0][1],
            },
            {
                "demonstrated": True,
                "name": "parent_directory_swap_use_restore_live_path_execution",
                "observed": "malicious-parent",
                "probe_sha256": EXPECTED_EXACT_SOURCE_CONTROL_PROBES[1][1],
            },
            {
                "accepted": True,
                "name": "digest_bound_double_read_compile_exec_exact_source",
                "observed": "reviewed-source-and-lexical-root",
                "probe_sha256": EXPECTED_EXACT_SOURCE_CONTROL_PROBES[2][1],
            },
            {
                "name": (
                    "digest_bound_rejects_parent_substitution_before_exec"
                ),
                "probe_sha256": EXPECTED_EXACT_SOURCE_CONTROL_PROBES[3][1],
                "rejected": True,
                "rejection_reason": EXPECTED_EXACT_SOURCE_REJECTION_REASON,
            },
        ],
        "exact-source loader exploit/control inventory",
    )
    require_strict_json_equal(
        snapshot_hostile,
        [
            {
                "name": "mutation_between_snapshot_and_replay",
                "probe_sha256": EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES[0][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS[0]
                ),
            },
            {
                "name": "symbolic_link_input",
                "probe_sha256": EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES[1][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS[1]
                ),
            },
            {
                "name": "mutation_during_double_read",
                "probe_sha256": EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES[2][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS[2]
                ),
            },
            {
                "name": "symbolic_link_parent_component",
                "probe_sha256": EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES[3][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS[3]
                ),
            },
            {
                "name": "multiply_linked_leaf",
                "probe_sha256": EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES[4][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS[4]
                ),
            },
            {
                "name": "parent_replacement_during_snapshot",
                "probe_sha256": EXPECTED_INPUT_SNAPSHOT_HOSTILE_PROBES[5][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_INPUT_SNAPSHOT_HOSTILE_REJECTION_REASONS[5]
                ),
            },
        ],
        "input-snapshot hostile-control inventory",
    )
    require_strict_json_equal(
        private_controls,
        [
            {
                "accepted": True,
                "name": "private_project_retains_prevalidated_tracked_copies",
                "probe_sha256": EXPECTED_PRIVATE_MATERIALIZATION_CONTROL_PROBES[0][1],
            },
            {
                "accepted": True,
                "name": "lean_lake_python_loader_environment_overrides_scrubbed",
                "probe_sha256": EXPECTED_PRIVATE_MATERIALIZATION_CONTROL_PROBES[1][1],
            },
            {
                "accepted": True,
                "name": (
                    "descriptor_pinned_private_cwd_relative_query_and_"
                    "lake_proxy_launch"
                ),
                "probe_sha256": EXPECTED_PRIVATE_MATERIALIZATION_CONTROL_PROBES[2][1],
            },
        ],
        "private-materialization control inventory",
    )
    require_strict_json_equal(
        process_stdin_controls,
        [
            {
                "accepted": True,
                "name": EXPECTED_PROCESS_STDIN_ISOLATION_SUBCONTROL_PROBES[0][0],
                "probe_sha256": (
                    EXPECTED_PROCESS_STDIN_ISOLATION_SUBCONTROL_PROBES[0][1]
                ),
            }
        ],
        "process-stdin isolation subcontrol inventory",
    )
    require_strict_json_equal(
        raw_transport_hostile,
        [
            {
                "name": "raw_subprocess_crlf_stdout_before_decode",
                "probe_sha256": EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_PROBES[0][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_REJECTION_REASONS[0]
                ),
            },
            {
                "name": "raw_subprocess_cr_stderr_before_decode",
                "probe_sha256": EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_PROBES[1][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_REJECTION_REASONS[1]
                ),
            },
            {
                "name": "raw_subprocess_non_utf8_stdout_before_decode",
                "probe_sha256": EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_PROBES[2][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_REJECTION_REASONS[2]
                ),
            },
            {
                "name": "raw_subprocess_non_utf8_stderr_before_decode",
                "probe_sha256": EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_PROBES[3][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_REJECTION_REASONS[3]
                ),
            },
            {
                "name": "raw_subprocess_cr_precedes_non_utf8_stdout",
                "probe_sha256": EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_PROBES[4][1],
                "rejected": True,
                "rejection_reason": (
                    EXPECTED_RAW_PROCESS_TRANSPORT_HOSTILE_REJECTION_REASONS[4]
                ),
            },
        ],
        "raw-process transport hostile-control inventory",
    )
    require_strict_json_equal(
        raw_transport_order_controls,
        [
            {
                "name": EXPECTED_RAW_PROCESS_TRANSPORT_ORDER_SUBCONTROL_PROBES[0][0],
                "probe_sha256": (
                    EXPECTED_RAW_PROCESS_TRANSPORT_ORDER_SUBCONTROL_PROBES[0][1]
                ),
                "rejected": True,
                "rejection_reason": "Lean process raw stdout is not strict UTF-8",
            }
        ],
        "raw-process completed-buffer order subcontrol inventory",
    )
    require_strict_json_equal(
        retained_negatives,
        [
            {
                "demonstrated": True,
                "name": "endpoint_replay_misses_parent_swap_use_restore",
                "probe_sha256": EXPECTED_RETAINED_NEGATIVE_PROBES[0][1],
            },
            {
                "demonstrated": True,
                "name": (
                    "descriptor_pinned_project_does_not_pin_query_subtree_entry"
                ),
                "probe_sha256": EXPECTED_RETAINED_NEGATIVE_PROBES[1][1],
            },
            {
                "demonstrated": True,
                "name": "retained_home_can_influence_live_launcher_state",
                "probe_sha256": EXPECTED_RETAINED_NEGATIVE_PROBES[2][1],
            },
            {
                "demonstrated": True,
                "name": "private_project_dependency_cache_remains_live",
                "probe_sha256": EXPECTED_RETAINED_NEGATIVE_PROBES[3][1],
            },
        ],
        "Lean portability retained-negative inventory",
    )
    require(
        isinstance(controls, list) and len(controls) == 2,
        "Lean portability parser must retain exactly two positive controls",
    )
    require(
        isinstance(hostile, list) and len(hostile) == 19,
        "Lean portability parser must retain exactly nineteen hostile controls",
    )
    expected_control_names = ("macos_arm64", "ubuntu_x86_64")
    observed_control_names: list[str] = []
    for index, item in enumerate(controls):
        require(
            isinstance(item, dict)
            and set(item) == {"accepted", "name", "probe_sha256"}
            and item.get("accepted") is True
            and isinstance(item.get("name"), str)
            and isinstance(item.get("probe_sha256"), str)
            and HEX64_RE.fullmatch(cast(str, item["probe_sha256"])) is not None,
            f"Lean portability positive control {index} is invalid",
        )
        observed_control_names.append(cast(str, item["name"]))
    require(
        tuple(observed_control_names) == expected_control_names,
        "Lean portability positive-control inventory changed",
    )
    require(
        tuple(
            (cast(str, item["name"]), cast(str, item["probe_sha256"]))
            for item in controls
        )
        == EXPECTED_LEAN_VERSION_CONTROL_PROBES,
        "Lean portability positive-control hashes changed",
    )

    expected_hostile_names = (
        "nonzero_exit",
        "unexpected_stderr",
        "empty_stdout",
        "missing_final_newline",
        "extra_stdout_line",
        "extra_blank_line",
        "leading_whitespace",
        "trailing_payload",
        "wrong_version",
        "malformed_version",
        "missing_platform",
        "platform_with_whitespace",
        "platform_with_too_few_components",
        "missing_commit_label",
        "wrong_commit",
        "short_commit",
        "uppercase_commit",
        "wrong_build",
        "missing_closing_delimiter",
    )
    observed_hostile_names: list[str] = []
    for index, item in enumerate(hostile):
        require(
            isinstance(item, dict)
            and set(item)
            == {"name", "probe_sha256", "rejected", "rejection_reason"}
            and item.get("rejected") is True
            and isinstance(item.get("name"), str)
            and isinstance(item.get("probe_sha256"), str)
            and isinstance(item.get("rejection_reason"), str)
            and HEX64_RE.fullmatch(cast(str, item["probe_sha256"])) is not None,
            f"Lean portability hostile control {index} is invalid",
        )
        observed_hostile_names.append(cast(str, item["name"]))
    require(
        tuple(observed_hostile_names) == expected_hostile_names,
        "Lean portability hostile-control inventory changed",
    )
    require(
        tuple(
            (cast(str, item["name"]), cast(str, item["probe_sha256"]))
            for item in hostile
        )
        == EXPECTED_LEAN_VERSION_HOSTILE_PROBES,
        "Lean portability hostile-control hashes changed",
    )
    require(
        tuple(cast(str, item["rejection_reason"]) for item in hostile)
        == EXPECTED_LEAN_VERSION_HOSTILE_REJECTION_REASONS,
        "Lean portability hostile-control rejection reasons changed",
    )

    evidence_raw = read_candidate_bytes(evidence_path)
    mutation_raw = read_candidate_bytes(mutation_path)
    evidence = canonical_compact_json_from_bytes(
        evidence_raw,
        label="descriptor-factorization Lean evidence",
    )
    mutations = canonical_compact_json_from_bytes(
        mutation_raw,
        label="descriptor-factorization mutation evidence",
    )
    require(
        isinstance(evidence, dict),
        "descriptor-factorization Lean evidence root must be an object",
    )
    require(
        isinstance(mutations, dict),
        "descriptor-factorization mutation evidence root must be an object",
    )
    lean_evidence = cast(dict[str, Any], evidence)
    mutation_evidence = cast(dict[str, Any], mutations)
    expected_identity_boundary = (
        "The normalized version, source commit, and build flavor are "
        "cross-platform release provenance only. The syntactically validated host "
        "platform token is deliberately excluded from reproducible evidence. Exact "
        "subprocess stdout and stderr are captured as raw bytes, reject carriage "
        "returns, and decode as strict UTF-8 before any version grammar is applied; "
        "child stdin is /dev/null and cannot consume parent input. Captured stdout "
        "and stderr have no explicit byte ceiling, and a timeout terminates and waits "
        "for only the direct child rather than guaranteeing descendant-process "
        "cleanup. The Lake proxy resolution plus terminal target bytes and metadata "
        "are observed and replayed at bounded endpoints; transient swap/restore "
        "remains possible. "
        "Neither Lake nor Lean, the dynamic loader, libraries, or dependencies is "
        "authenticated; no cross-platform kernel-equivalence theorem follows."
    )
    expected_evidence_boundary = (
        "Generic descriptor-factorization logic only. The concrete "
        "Lyu--Clark--Raviv descriptor collision and the nonfactorization of SxPID "
        "are bound separately by exact-rational and Rust witnesses; this check does "
        "not formalize SxPID."
    )
    expected_snapshot_boundary = (
        "Frozen digests bind the theorem and three tracked project files before use; "
        "Lake is launched with a descriptor-pinned private POSIX working directory "
        "and finite relative query path. Component, leaf, metadata, and byte endpoint "
        "checks reject unresolved replacement, while descriptor pinning contains a "
        "private-project pathname swap after launch preparation. It does not pin the "
        "project's query-directory entry; the self-test retains a concrete query-"
        "subtree swap/use/restore negative. Endpoint checks are not an atomic history, "
        "so a settled query subtree and no concurrent privileged or same-UID writer "
        "remain explicit premises. The already-running script predates its first "
        "observation. Retained HOME may influence selected launcher state, and "
        "dependency package/cache contents remain live and unauthenticated. Regular "
        "input bytes are accumulated without an explicit size ceiling."
    )
    require_strict_json_equal(
        lean_evidence,
        {
            "axioms": [],
            "boundary": expected_evidence_boundary,
            "checker_source_sha256": checker_sha256,
            "input_snapshot_boundary": expected_snapshot_boundary,
            "input_snapshot_files_checked": 6,
            "input_snapshot_method": (
                "posix_component_descriptor_double_read_with_single_link_"
                "tracked_inputs_and_separate_proxy_target_replay"
            ),
            "input_snapshot_replays_unchanged": 6,
            "launcher_target_files_observed": 1,
            "lake_manifest_sha256": (
                "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd"
            ),
            "lakefile_sha256": (
                "1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1"
            ),
            "lean_executable_identity": portable_identity,
            "lean_executable_identity_boundary": expected_identity_boundary,
            "lean_platform_handling": "parsed_and_validated_but_not_serialized",
            "process_stdin_transport": "devnull_eof_no_parent_input",
            "process_stream_transport": (
                "stdout_then_stderr_each_reject_carriage_return_then_"
                "strict_utf8_decode"
            ),
            "lean_toolchain": "leanprover/lean4:v4.32.0",
            "lean_toolchain_sha256": (
                "2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e"
            ),
            "private_project_files_checked": 3,
            "private_project_replays_unchanged": 3,
            "private_query_files_checked": 1,
            "private_query_replays_unchanged": 1,
            "single_link_input_files_checked": 5,
            "schema": "pid-rs/lean-descriptor-factorization-check/v4",
            "source_sha256": (
                "7e1e71d76d63137ae055f17b1b771fdd2eb01935c7210bca79142691f7f06034"
            ),
            "status": "passed",
            "theorems_kernel_checked": 3,
        },
        "descriptor-factorization Lean portable evidence",
    )
    require(
        b"arm64-apple-" not in evidence_raw
        and b"x86_64-unknown-linux-" not in evidence_raw
        and b'"lean_version"' not in evidence_raw,
        "host-specific or legacy raw Lean version leaked into portable evidence",
    )

    expected_mutation_boundary = (
        "The three scientific proof mutations and three kernel-checked finite "
        "countermodels separately exercise the factorization and distinctness "
        "premises. Separately counted parser, digest-bound-source, private-"
        "materialization, environment, and snapshot controls exercise portable "
        "evidence and bounded process-input custody. Five live binary-pipe attacks "
        "show that each stream rejects raw carriage returns before strict decoding "
        "and that strict decoding rejects invalid UTF-8 before semantic parsing. A "
        "separately typed live mixed-stream subcontrol proves stdout is rejected "
        "before stderr, while the frozen five-family count and same-stdout precedence "
        "witness remain unchanged. A live parent-fd-0 contamination probe proves "
        "child stdin is DEVNULL. Descriptor-pinned child CWD contains private-project "
        "pathname substitution after pinning, but does not pin the query-subtree "
        "entry; the concrete query swap and generic endpoint replay show "
        "swap/use/restore limits. HOME-influenced launcher state and dependency-"
        "package/cache bytes remain live. The direct-child timeout does not guarantee "
        "descendant termination, and captured stdout/stderr have no explicit byte "
        "ceiling. The stability window starts at the first in-process observation; no "
        "route binds abstract descriptors or atoms to a concrete PID implementation, "
        "authenticates selected Python/Lean or dependency bytes, or proves cross-"
        "platform kernel equivalence."
    )
    require(
        set(mutation_evidence)
        == {
            "boundary",
            "descriptor_checker_source_sha256",
            "exact_source_loader_controls",
            "exact_source_loader_controls_passed",
            "input_snapshot_files_checked",
            "input_snapshot_hostile_cases",
            "input_snapshot_hostile_cases_rejected",
            "input_snapshot_replays_unchanged",
            "lean_version_hostile_cases",
            "lean_version_hostile_cases_rejected",
            "lean_version_portability_controls",
            "lean_version_portability_controls_accepted",
            "lean_version_portable_identity",
            "private_materialization_controls",
            "private_materialization_controls_passed",
            "private_query_files_checked",
            "private_query_replays_unchanged",
            "process_stdin_isolation_subcontrols",
            "process_stdin_isolation_subcontrols_passed",
            "raw_process_transport_hostile_cases",
            "raw_process_transport_hostile_cases_rejected",
            "raw_process_transport_order_subcontrols",
            "raw_process_transport_order_subcontrols_rejected",
            "retained_negative_controls",
            "retained_negative_controls_demonstrated",
            "schema",
            "scientific_proof_mutations",
            "scientific_proof_mutations_killed",
            "self_test_source_sha256",
            "semantic_countermodels_kernel_checked",
            "semantic_countermodels_sha256",
            "source_sha256",
            "status",
        },
        "descriptor-factorization mutation evidence has an unexpected shape",
    )
    require_strict_json_equal(
        {
            "boundary": mutation_evidence.get("boundary"),
            "self_test_source_sha256": mutation_evidence.get(
                "self_test_source_sha256"
            ),
            "descriptor_checker_source_sha256": mutation_evidence.get(
                "descriptor_checker_source_sha256"
            ),
            "exact_source_loader_controls_passed": mutation_evidence.get(
                "exact_source_loader_controls_passed"
            ),
            "input_snapshot_files_checked": mutation_evidence.get(
                "input_snapshot_files_checked"
            ),
            "input_snapshot_hostile_cases_rejected": mutation_evidence.get(
                "input_snapshot_hostile_cases_rejected"
            ),
            "input_snapshot_replays_unchanged": mutation_evidence.get(
                "input_snapshot_replays_unchanged"
            ),
            "private_materialization_controls_passed": mutation_evidence.get(
                "private_materialization_controls_passed"
            ),
            "private_query_files_checked": mutation_evidence.get(
                "private_query_files_checked"
            ),
            "private_query_replays_unchanged": mutation_evidence.get(
                "private_query_replays_unchanged"
            ),
            "process_stdin_isolation_subcontrols_passed": mutation_evidence.get(
                "process_stdin_isolation_subcontrols_passed"
            ),
            "raw_process_transport_hostile_cases_rejected": mutation_evidence.get(
                "raw_process_transport_hostile_cases_rejected"
            ),
            "raw_process_transport_order_subcontrols_rejected": mutation_evidence.get(
                "raw_process_transport_order_subcontrols_rejected"
            ),
            "retained_negative_controls_demonstrated": mutation_evidence.get(
                "retained_negative_controls_demonstrated"
            ),
            "schema": mutation_evidence.get("schema"),
            "scientific_proof_mutations_killed": mutation_evidence.get(
                "scientific_proof_mutations_killed"
            ),
            "semantic_countermodels_kernel_checked": mutation_evidence.get(
                "semantic_countermodels_kernel_checked"
            ),
            "semantic_countermodels_sha256": mutation_evidence.get(
                "semantic_countermodels_sha256"
            ),
            "source_sha256": mutation_evidence.get("source_sha256"),
            "status": mutation_evidence.get("status"),
        },
        {
            "boundary": expected_mutation_boundary,
            "self_test_source_sha256": self_test_sha256,
            "descriptor_checker_source_sha256": checker_sha256,
            "exact_source_loader_controls_passed": 4,
            "input_snapshot_files_checked": 10,
            "input_snapshot_hostile_cases_rejected": 6,
            "input_snapshot_replays_unchanged": 10,
            "private_materialization_controls_passed": 3,
            "private_query_files_checked": 5,
            "private_query_replays_unchanged": 5,
            "process_stdin_isolation_subcontrols_passed": 1,
            "raw_process_transport_hostile_cases_rejected": 5,
            "raw_process_transport_order_subcontrols_rejected": 1,
            "retained_negative_controls_demonstrated": 4,
            "schema": "pid-rs/lean-descriptor-factorization-mutations/v4",
            "scientific_proof_mutations_killed": 3,
            "semantic_countermodels_kernel_checked": 3,
            "semantic_countermodels_sha256": (
                "b72943d568729c87c2dbb56427676360f6fa37e812fd687993563b776f09dd30"
            ),
            "source_sha256": (
                "7e1e71d76d63137ae055f17b1b771fdd2eb01935c7210bca79142691f7f06034"
            ),
            "status": "passed",
        },
        "descriptor-factorization mutation evidence identity",
    )
    require_strict_json_equal(
        mutation_evidence.get("scientific_proof_mutations"),
        [
            {
                "killed": True,
                "mutant_sha256": (
                    "af414eba03932111c0bd2218988e197745de00fad7433c263fc40581f9c94b73"
                ),
                "name": "remove_factorization_premise",
            },
            {
                "killed": True,
                "mutant_sha256": (
                    "2db764d18b4d4be1a56d27625ff95af131a0dc739ede205adbe91b458e672b01"
                ),
                "name": "replace_quantity_difference_with_equality",
            },
            {
                "killed": True,
                "mutant_sha256": (
                    "d7c2ea1431d33788bd7a412f65341de4a844261e3edf4f1322382a9ef14b244e"
                ),
                "name": "replace_atom_difference_with_equality",
            },
        ],
        "descriptor-factorization scientific mutation inventory",
    )
    for field in (
        "exact_source_loader_controls",
        "exact_source_loader_controls_passed",
        "input_snapshot_hostile_cases",
        "input_snapshot_hostile_cases_rejected",
        "lean_version_hostile_cases",
        "lean_version_hostile_cases_rejected",
        "lean_version_portability_controls",
        "lean_version_portability_controls_accepted",
        "lean_version_portable_identity",
        "private_materialization_controls",
        "private_materialization_controls_passed",
        "process_stdin_isolation_subcontrols",
        "process_stdin_isolation_subcontrols_passed",
        "raw_process_transport_hostile_cases",
        "raw_process_transport_hostile_cases_rejected",
        "raw_process_transport_order_subcontrols",
        "raw_process_transport_order_subcontrols_rejected",
        "retained_negative_controls",
        "retained_negative_controls_demonstrated",
    ):
        require_strict_json_equal(
            mutation_evidence.get(field),
            parser_output.get(field),
            f"descriptor-factorization parser/mutation parity field {field}",
        )
    require(
        b'"lean_version"' not in mutation_raw
        and b'"platform"' not in mutation_raw,
        "host platform leaked into descriptor-factorization mutation evidence",
    )
    return LeanPortabilityArtifacts(
        parser_normal=normal_raw,
        parser_optimized=optimized_raw,
        direct_evidence=evidence_raw,
        mutation_evidence=mutation_raw,
    )


def validate_c3_science_and_publication_isolation(
    snapshot: CandidateSnapshot,
    anchor: dict[str, GitEntry],
) -> None:
    scoped = tuple(
        sorted(
            path
            for path in set(anchor).union(snapshot.entries)
            if path.startswith(C3_SCIENCE_FREEZE_PREFIXES)
            and path not in C3_AUTHORIZED_PUBLICATION_PATHS
        )
    )
    require(scoped, "C3 science/publication freeze projection is empty")
    for path in scoped:
        require(
            snapshot.entries.get(path) == anchor.get(path),
            f"C3 changed science/formal/PDF bytes outside evidence metadata: {path}",
        )
    for path in C3_EXPLICIT_FROZEN_PATHS:
        require(
            snapshot.entries.get(path) == anchor.get(path),
            f"C3 changed an explicitly frozen workflow/catalog/theorem path: {path}",
        )
    pdf_paths = tuple(
        path
        for path in set(anchor).union(snapshot.entries)
        if path.startswith("output/pdf/")
    )
    require(
        len(pdf_paths) == 9 and all(path.endswith(".pdf") for path in pdf_paths),
        "C3 frozen complete-detail PDF inventory changed",
    )


def replace_unique_workflow_fragment(
    raw: bytes,
    before: bytes,
    after: bytes,
    *,
    label: str,
) -> bytes:
    require(
        raw.count(before) == 1,
        f"source workflow does not contain one exact {label} edit anchor",
    )
    return raw.replace(before, after, 1)


def pinned_lean_setup_and_cache() -> bytes:
    return (
        b"      - name: Install pinned Elan\n"
        b"        shell: bash\n"
        b"        env:\n"
        b"          ELAN_ARCHIVE_SHA256: "
        b"df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2\n"
        b"          ELAN_ARCHIVE_URL: "
        b"https://github.com/leanprover/elan/releases/download/v4.2.3/"
        b"elan-x86_64-unknown-linux-gnu.tar.gz\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          archive="$RUNNER_TEMP/elan-x86_64-unknown-linux-gnu.tar.gz"\n'
        b'          install_root="$RUNNER_TEMP/elan-v4.2.3"\n'
        b"          curl --fail --location --proto '=https' --retry 5 --show-error \\\n"
        b'            --tlsv1.2 --output "$archive" "$ELAN_ARCHIVE_URL"\n'
        b"          printf '%s  %s\\n' \"$ELAN_ARCHIVE_SHA256\" \"$archive\" \\\n"
        b"            | sha256sum --check --strict\n"
        b'          mkdir -p "$install_root"\n'
        b'          tar -xzf "$archive" -C "$install_root"\n'
        b'          "$install_root/elan-init" -y --default-toolchain none '
        b"--no-modify-path\n"
        b'          echo "$HOME/.elan/bin" >> "$GITHUB_PATH"\n'
        b"      - uses: actions/cache@"
        b"27d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5\n"
        b"        with:\n"
        b"          path: audit/formal/lean/.lake\n"
        b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
        b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
        b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
        b"${{ github.sha }}\n"
        b"          restore-keys: lake-${{ runner.os }}-${{ runner.arch }}-"
        b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
        b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}\n"
    )


def pinned_mathlib_build() -> bytes:
    return (
        b"      - name: Fetch the Mathlib cache and build\n"
        b"        working-directory: audit/formal/lean\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b"          lake exe cache get\n"
        b"          lake build\n"
    )


def validate_public_ci_failure_evidence() -> None:
    raw = read_candidate_bytes(PUBLIC_CI_FAILURE_RECEIPT)
    require(
        hashlib.sha256(raw).hexdigest() == PUBLIC_CI_FAILURE_RECEIPT_SHA256,
        "public CI failure receipt differs from the independently reviewed bytes",
    )
    parsed = canonical_json_from_bytes(raw, label=PUBLIC_CI_FAILURE_RECEIPT)
    require(
        isinstance(parsed, dict),
        "public CI failure receipt root must be an object",
    )
    receipt = cast(dict[str, Any], parsed)
    require(
        set(receipt)
        == {
            "claim_boundary",
            "head",
            "jobs",
            "remediation",
            "run",
            "schema",
            "schema_revision",
            "status",
        },
        "public CI failure receipt top-level shape changed",
    )
    require_strict_json_equal(
        {
            "claim_boundary": receipt.get("claim_boundary"),
            "schema": receipt.get("schema"),
            "schema_revision": receipt.get("schema_revision"),
            "status": receipt.get("status"),
        },
        {
            "claim_boundary": (
                "Hosted CI execution and custody receipt for exact commit "
                "af50935be9ecf9a81aeb30c56b45059652468746 only. It records two "
                "missing-tool provisioning failures and 43 successful jobs. It "
                "gives no credit to skipped steps, does not settle full CI, and "
                "does not prove mathematical correctness, authenticity, "
                "portability, release readiness, publication acceptance, or "
                "downstream validity."
            ),
            "schema": "pid-rs/public-ci-failure-receipt",
            "schema_revision": 1,
            "status": "terminal_failure_retained",
        },
        "public CI failure receipt identity",
    )
    expected_head = {
        "branch": "main",
        "commit": CORRECTIVE_PARENT,
        "tree": CORRECTIVE_PARENT_TREE,
    }
    require_strict_json_equal(
        receipt.get("head"),
        expected_head,
        "public CI failure receipt head",
    )
    expected_run = {
        "attempt": 1,
        "conclusion": "failure",
        "created_at": "2026-07-28T23:49:13Z",
        "event": "push",
        "head_branch": "main",
        "head_sha": CORRECTIVE_PARENT,
        "html_url": "https://github.com/sepahead/pid-rs/actions/runs/30409192059",
        "id": 30409192059,
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "run_number": 146,
        "status": "completed",
        "updated_at": "2026-07-29T00:09:24Z",
        "workflow_id": 297369773,
    }
    require_strict_json_equal(
        receipt.get("run"),
        expected_run,
        "public CI failure receipt run",
    )
    jobs_raw = receipt.get("jobs")
    require(isinstance(jobs_raw, dict), "public CI failure jobs must be an object")
    jobs = cast(dict[str, Any], jobs_raw)
    require(
        set(jobs)
        == {
            "failed",
            "ksg_phase_job",
            "lean_environment_control_job",
            "success_count",
            "total_count",
        },
        "public CI failure job inventory changed",
    )
    failed_raw = jobs.get("failed")
    require(
        isinstance(failed_raw, list) and len(failed_raw) == 2,
        "public CI failure receipt must contain exactly two failed jobs",
    )
    failed_jobs = cast(list[dict[str, Any]], failed_raw)
    require(
        all(isinstance(job, dict) for job in failed_jobs),
        "public CI failed-job entries must be objects",
    )
    require(
        set(failed_jobs[0])
        == {
            "completed_at",
            "conclusion",
            "failure",
            "id",
            "name",
            "skipped_actions_steps",
            "started_at",
            "status",
        },
        "public CI certified-SxPID2 failed-job shape changed",
    )
    require(
        set(failed_jobs[1])
        == {
            "completed_at",
            "completed_intra_step_routes",
            "conclusion",
            "credit_boundary",
            "failure",
            "id",
            "name",
            "skipped_actions_steps",
            "started_at",
            "status",
            "unreached_intra_step_routes",
        },
        "public CI formal-PDF failed-job shape changed",
    )
    failed_summaries = [
        {
            "completed_at": job.get("completed_at"),
            "conclusion": job.get("conclusion"),
            "failure": job.get("failure"),
            "id": job.get("id"),
            "name": job.get("name"),
            "started_at": job.get("started_at"),
            "status": job.get("status"),
        }
        for job in failed_jobs
    ]
    require_strict_json_equal(
        failed_summaries,
        [
            {
                "completed_at": "2026-07-28T23:53:12Z",
                "conclusion": "failure",
                "failure": {
                    "classification": "ci_tool_provisioning",
                    "exact_error": (
                        "Lean exact-log-product check failed: lake is not available"
                    ),
                    "log_digest_domain": (
                        "decoded bytes returned by the GitHub Actions job-logs "
                        "REST endpoint"
                    ),
                    "log_sha256": (
                        "4c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10"
                    ),
                    "log_size_bytes": 108775,
                    "scientific_counterexample": False,
                    "step_name": (
                        "Run python3 scripts/check-lean-exact-log-product.py"
                    ),
                    "step_number": 18,
                },
                "id": 90441337083,
                "name": "Exact-count directed-rounding SxPID2 reference",
                "started_at": "2026-07-28T23:49:22Z",
                "status": "completed",
            },
            {
                "completed_at": "2026-07-28T23:50:38Z",
                "conclusion": "failure",
                "failure": {
                    "classification": "ci_tool_provisioning",
                    "exact_error": (
                        "ecosystem compatibility audit PDF check: missing command: "
                        "chktex"
                    ),
                    "first_failed_intra_step_route": (
                        "scripts/check-ecosystem-compatibility-audit-pdf.sh "
                        "--cross-toolchain"
                    ),
                    "log_digest_domain": (
                        "decoded bytes returned by the GitHub Actions job-logs "
                        "REST endpoint"
                    ),
                    "log_sha256": (
                        "4889d459eaf1c52f394612a593e4bf27718145169025d314f078f718f5cc932c"
                    ),
                    "log_size_bytes": 43692,
                    "scientific_counterexample": False,
                    "step_name": (
                        "Rebuild warning-free papers and compare text, page geometry, "
                        "and embedded fonts"
                    ),
                    "step_number": 5,
                },
                "id": 90441337159,
                "name": "Formal LaTeX / PDF inventory and cross-toolchain structure",
                "started_at": "2026-07-28T23:49:22Z",
                "status": "completed",
            },
        ],
        "public CI failed-job summaries",
    )
    failed_ids = tuple(cast(int, job.get("id")) for job in failed_jobs)
    require(
        failed_ids == tuple(sorted(set(failed_ids))),
        "public CI failed-job ids must be ordered and unique",
    )
    expected_skipped_actions = [
        {
            "conclusion": "skipped",
            "name": "Run python3 scripts/check-certified-sxpid2-claim.py",
            "number": 19,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": "Run python3 scripts/check-certified-sxpid2-claim-self-test.py",
            "number": 20,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": "Run cargo install cargo-deny --locked --version 0.20.2",
            "number": 21,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": (
                "Run cargo deny --manifest-path "
                "audit/tools/certified-sxpid/Cargo.toml --config "
                "audit/tools/certified-sxpid/deny.toml check"
            ),
            "number": 22,
            "status": "completed",
        },
        {
            "conclusion": "skipped",
            "name": (
                "Post Run actions/setup-python@"
                "ece7cb06caefa5fff74198d8649806c4678c61a1"
            ),
            "number": 43,
            "status": "completed",
        },
    ]
    require_strict_json_equal(
        failed_jobs[0].get("skipped_actions_steps"),
        expected_skipped_actions,
        "public CI skipped Actions steps",
    )
    completed_pdf_routes = [
        "python3 scripts/check-formal-pdf-style.py",
        "python3 scripts/check-formal-pdf-style-self-test.py",
        "scripts/check-certified-sxpid2-assurance-pdf.sh --cross-toolchain",
        "scripts/check-dependency-colored-sxpid-pdf.sh --cross-toolchain",
    ]
    unreached_pdf_routes = [
        "scripts/check-exact-log-product-sxpid2-pdf.sh --cross-toolchain",
        "scripts/check-finite-alphabet-convergence-pdf.sh --cross-toolchain",
        "scripts/check-formal-tool-adoption-pdf.sh --cross-toolchain",
        "scripts/check-foundational-sxpid-audit-pdf.sh --cross-toolchain",
        "scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
        "scripts/check-support-change-tolerant-sxpid-pdf.sh --cross-toolchain",
    ]
    require_strict_json_equal(
        {
            "completed_intra_step_routes": failed_jobs[1].get(
                "completed_intra_step_routes"
            ),
            "credit_boundary": failed_jobs[1].get("credit_boundary"),
            "skipped_actions_steps": failed_jobs[1].get("skipped_actions_steps"),
            "unreached_intra_step_routes": failed_jobs[1].get(
                "unreached_intra_step_routes"
            ),
        },
        {
            "completed_intra_step_routes": completed_pdf_routes,
            "credit_boundary": (
                "GitHub Actions reports only the containing step as failed. This "
                "receipt gives no independent pass credit to any in-step paper "
                "route and no execution credit to routes after the first reported "
                "chktex error."
            ),
            "skipped_actions_steps": [],
            "unreached_intra_step_routes": unreached_pdf_routes,
        },
        "public CI formal-PDF composite-step credit boundary",
    )
    require_strict_json_equal(
        jobs.get("ksg_phase_job"),
        {
            "completed_at": "2026-07-29T00:09:23Z",
            "conclusion": "success",
            "id": 90441337099,
            "name": "KSG integer-harmonic arithmetic and phase isolation",
            "started_at": "2026-07-28T23:49:15Z",
            "status": "completed",
        },
        "public CI KSG control job",
    )
    require_strict_json_equal(
        jobs.get("lean_environment_control_job"),
        {
            "claim_boundary": (
                "This same-run success shows that the existing checksum-pinned "
                "Elan/cache/Mathlib-build route executed successfully in its own "
                "job. It is a tooling-pattern control, not evidence that another "
                "job inherited tools or that skipped SxPID2/PDF routes passed."
            ),
            "completed_at": "2026-07-28T23:53:42Z",
            "conclusion": "success",
            "id": 90441337145,
            "name": (
                "Finite-alphabet, dependency-color, support-change, and KSG "
                "harmonic proof cores"
            ),
            "provisioning_steps": [
                {
                    "conclusion": "success",
                    "name": "Install pinned Elan",
                    "number": 3,
                    "status": "completed",
                },
                {
                    "conclusion": "success",
                    "name": (
                        "Run actions/cache@"
                        "27d5ce7f107fe9357f9df03efb73ab90386fccae"
                    ),
                    "number": 4,
                    "status": "completed",
                },
                {
                    "conclusion": "success",
                    "name": "Fetch the Mathlib cache and build",
                    "number": 5,
                    "status": "completed",
                },
            ],
            "started_at": "2026-07-28T23:49:15Z",
            "status": "completed",
        },
        "public CI Lean-environment control job",
    )
    require_strict_json_equal(
        {
            "success_count": jobs.get("success_count"),
            "total_count": jobs.get("total_count"),
        },
        {"success_count": 43, "total_count": 45},
        "public CI job counts",
    )
    require(
        cast(int, jobs["success_count"]) + len(failed_jobs)
        == cast(int, jobs["total_count"]),
        "public CI success and failure counts do not close the job total",
    )
    expected_remediation = {
        "formal_pdf_job": [
            (
                "Install chktex in the fresh Ubuntu TeX toolchain before the "
                "unchanged cross-toolchain paper gate."
            ),
            (
                "Provision the pinned Lean and Mathlib environment for the "
                "statically reachable descriptor-factorization checker; this lake "
                "dependency was latent because the earlier chktex failure stopped "
                "the run first."
            ),
            (
                "Make the directly invocable foundational-paper route preflight "
                "lake."
            ),
        ],
        "scientific_claims_changed": False,
        "settled_full_ci": False,
        "sxpid2_job": [
            "Provision checksum-pinned Elan 4.2.3 inside the certified SxPID2 job.",
            (
                "Restore the pinned Lean and Mathlib environment before the "
                "unchanged exact-log-product kernel checker."
            ),
        ],
        "whole_run_rerun_required": True,
    }
    require_strict_json_equal(
        receipt.get("remediation"),
        expected_remediation,
        "public CI remediation and no-credit state",
    )
    require(
        commit_identity(CORRECTIVE_PARENT)[0] == CORRECTIVE_PARENT_TREE,
        "public CI receipt subject commit does not resolve to the pinned tree",
    )
    require(
        expected_head["commit"] == expected_run["head_sha"] == CORRECTIVE_PARENT,
        "public CI receipt commit bindings diverged",
    )

    memo_raw = read_candidate_bytes(CORRECTIVE_EVIDENCE)
    try:
        memo = memo_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            "public CI corrective memo is not UTF-8"
        ) from error
    begin = "PUBLIC_CI_FAILURE_PARITY_BEGIN\n"
    end = "\nPUBLIC_CI_FAILURE_PARITY_END"
    require(
        memo.count(begin) == 1 and memo.count(end) == 1,
        "public CI corrective memo parity sentinels are not unique",
    )
    prefix, remainder = memo.split(begin, 1)
    parity_text, suffix = remainder.split(end, 1)
    require(
        prefix.endswith("```text\n") and suffix.startswith("\n```"),
        "public CI corrective memo parity block lost its exact code-fence boundary",
    )
    parity = canonical_json_from_bytes(
        (parity_text + "\n").encode("utf-8"),
        label="public CI corrective memo parity block",
    )
    first_failure = cast(dict[str, Any], failed_jobs[0]["failure"])
    second_failure = cast(dict[str, Any], failed_jobs[1]["failure"])
    expected_parity = {
        "failed_jobs": [
            {
                "conclusion": failed_jobs[0]["conclusion"],
                "exact_error": first_failure["exact_error"],
                "id": failed_jobs[0]["id"],
                "log_sha256": first_failure["log_sha256"],
                "log_size_bytes": first_failure["log_size_bytes"],
                "scientific_counterexample": first_failure[
                    "scientific_counterexample"
                ],
                "step_number": first_failure["step_number"],
            },
            {
                "conclusion": failed_jobs[1]["conclusion"],
                "exact_error": second_failure["exact_error"],
                "id": failed_jobs[1]["id"],
                "log_sha256": second_failure["log_sha256"],
                "log_size_bytes": second_failure["log_size_bytes"],
                "scientific_counterexample": second_failure[
                    "scientific_counterexample"
                ],
                "step_number": second_failure["step_number"],
            },
        ],
        "formal_pdf_intra_step": {
            "completed_routes": completed_pdf_routes,
            "failed_route": second_failure["first_failed_intra_step_route"],
            "unreached_routes": unreached_pdf_routes,
        },
        "head": {
            "commit": expected_head["commit"],
            "tree": expected_head["tree"],
        },
        "integration_disposition": (
            "NO-GO pending a fresh complete public rerun"
        ),
        "job_counts": {
            "failed": len(failed_jobs),
            "success": jobs["success_count"],
            "total": jobs["total_count"],
        },
        "ksg_job": {
            "conclusion": cast(dict[str, Any], jobs["ksg_phase_job"])[
                "conclusion"
            ],
            "id": cast(dict[str, Any], jobs["ksg_phase_job"])["id"],
            "status": cast(dict[str, Any], jobs["ksg_phase_job"])["status"],
        },
        "latent_dependencies": [
            {
                "classification": "statically discovered latent dependency",
                "missing_tool": "lake",
                "route": (
                    "scripts/check-foundational-sxpid-audit-pdf.sh "
                    "--cross-toolchain"
                ),
            }
        ],
        "observed_missing_tools": ["lake", "chktex"],
        "receipt_path": PUBLIC_CI_FAILURE_RECEIPT,
        "receipt_sha256": PUBLIC_CI_FAILURE_RECEIPT_SHA256,
        "remediation": {
            "settled_full_ci": expected_remediation["settled_full_ci"],
            "whole_run_rerun_required": expected_remediation[
                "whole_run_rerun_required"
            ],
        },
        "run": {
            "attempt": expected_run["attempt"],
            "conclusion": expected_run["conclusion"],
            "id": expected_run["id"],
            "number": expected_run["run_number"],
            "status": expected_run["status"],
        },
        "schema": "pid-rs/public-ci-failure-human-parity",
        "schema_revision": 1,
        "skipped_actions_steps": expected_skipped_actions,
    }
    require_strict_json_equal(
        parity,
        expected_parity,
        "public CI human/machine parity projection",
    )


def validate_public_ci_portability_failure_evidence() -> bytes:
    raw = read_candidate_bytes(PUBLIC_CI_PORTABILITY_RECEIPT)
    require(
        hashlib.sha256(raw).hexdigest() == PUBLIC_CI_PORTABILITY_RECEIPT_SHA256,
        "C2 portability failure receipt differs from its reviewed bytes",
    )
    parsed = canonical_json_from_bytes(
        raw,
        label=PUBLIC_CI_PORTABILITY_RECEIPT,
    )
    require(
        isinstance(parsed, dict),
        "C2 portability failure receipt root must be an object",
    )
    receipt = cast(dict[str, Any], parsed)
    require(
        set(receipt)
        == {
            "claim_boundary",
            "codeql",
            "head",
            "jobs",
            "remediation",
            "run",
            "schema",
            "schema_revision",
            "status",
        },
        "C2 portability failure receipt top-level shape changed",
    )
    expected_claim_boundary = (
        "Hosted CI and CodeQL execution/custody receipt for exact commit "
        "8b792bc143fff2d84f2d8e7817d1de7850741223 only. It records one "
        "cross-host evidence-serialization failure in a run with 44 successful "
        "CI jobs. "
        "It gives no independent Actions-step credit to commands inside the "
        "failed composite step, no credit to skipped or unreached routes, and "
        "does not prove mathematical correctness, binary authenticity, general "
        "cross-platform kernel equivalence, security, release readiness, "
        "publication acceptance, or downstream validity."
    )
    require_strict_json_equal(
        {
            "claim_boundary": receipt.get("claim_boundary"),
            "schema": receipt.get("schema"),
            "schema_revision": receipt.get("schema_revision"),
            "status": receipt.get("status"),
        },
        {
            "claim_boundary": expected_claim_boundary,
            "schema": "pid-rs/public-ci-failure-receipt",
            "schema_revision": 2,
            "status": "terminal_failure_retained",
        },
        "C2 portability failure receipt identity",
    )
    expected_head = {
        "branch": "main",
        "commit": C2_TOOLING_CORRECTION,
        "tree": C2_TOOLING_CORRECTION_TREE,
    }
    expected_run = {
        "attempt": 1,
        "conclusion": "failure",
        "created_at": "2026-07-29T07:21:26Z",
        "event": "push",
        "head_branch": "main",
        "head_sha": C2_TOOLING_CORRECTION,
        "html_url": "https://github.com/sepahead/pid-rs/actions/runs/30431352389",
        "id": 30431352389,
        "name": "CI",
        "path": ".github/workflows/ci.yml",
        "run_number": 147,
        "status": "completed",
        "updated_at": "2026-07-29T07:48:21Z",
        "workflow_id": 297369773,
    }
    require_strict_json_equal(
        receipt.get("head"),
        expected_head,
        "C2 portability failure receipt head",
    )
    require_strict_json_equal(
        receipt.get("run"),
        expected_run,
        "C2 portability failure receipt run",
    )

    jobs_raw = receipt.get("jobs")
    require(
        isinstance(jobs_raw, dict)
        and set(jobs_raw)
        == {
            "actions_step_counts",
            "certified_sxpid2_job",
            "failed",
            "failed_count",
            "ksg_phase_job",
            "lean_environment_control_job",
            "success_count",
            "total_count",
        },
        "C2 portability failure job inventory changed",
    )
    jobs = cast(dict[str, Any], jobs_raw)
    require_strict_json_equal(
        {
            "actions_step_counts": jobs.get("actions_step_counts"),
            "failed_count": jobs.get("failed_count"),
            "success_count": jobs.get("success_count"),
            "total_count": jobs.get("total_count"),
        },
        {
            "actions_step_counts": {
                "failure": 1,
                "skipped": 1,
                "success": 532,
                "total": 534,
            },
            "failed_count": 1,
            "success_count": 44,
            "total_count": 45,
        },
        "C2 portability failure counts",
    )
    require(
        cast(int, jobs["success_count"]) + cast(int, jobs["failed_count"])
        == cast(int, jobs["total_count"]),
        "C2 portability CI success/failure counts do not close the total",
    )

    failed_raw = jobs.get("failed")
    require(
        isinstance(failed_raw, list) and len(failed_raw) == 1,
        "C2 portability receipt must retain exactly one failed job",
    )
    failed_job = cast(dict[str, Any], failed_raw[0])
    require(
        isinstance(failed_job, dict)
        and set(failed_job)
        == {
            "completed_at",
            "conclusion",
            "failure",
            "id",
            "intra_step_routes",
            "name",
            "skipped_actions_steps",
            "started_at",
            "status",
        },
        "C2 portability failed-job shape changed",
    )
    require_strict_json_equal(
        {
            "completed_at": failed_job.get("completed_at"),
            "conclusion": failed_job.get("conclusion"),
            "id": failed_job.get("id"),
            "name": failed_job.get("name"),
            "started_at": failed_job.get("started_at"),
            "status": failed_job.get("status"),
        },
        {
            "completed_at": "2026-07-29T07:24:02Z",
            "conclusion": "failure",
            "id": 90509073390,
            "name": "Formal LaTeX / PDF inventory and cross-toolchain structure",
            "started_at": "2026-07-29T07:21:28Z",
            "status": "completed",
        },
        "C2 portability failed-job identity",
    )
    failure_raw = failed_job.get("failure")
    require(
        isinstance(failure_raw, dict),
        "C2 portability failure detail must be an object",
    )
    failure = cast(dict[str, Any], failure_raw)
    expected_control_flow = {
        "axioms": [],
        "checker_returned_success_before_comparison": True,
        "inference_basis": (
            "The committed wrapper uses set -e, runs the descriptor checker into "
            "a temporary file, and emits the observed stale-evidence message only "
            "after the checker has returned zero and cmp has found unequal bytes."
        ),
        "inference_boundary": (
            "This is a deterministic control-flow inference from the committed "
            "wrapper and hosted log, not an independently retained runner receipt. "
            "It does not authenticate the runner or prove cross-platform kernel "
            "equivalence."
        ),
        "kernel_failure": False,
        "theorems_kernel_checked": 3,
    }
    expected_cross_host = {
        "committed_macos": {
            "lean_version": (
                "Lean (version 4.32.0, arm64-apple-darwin24.6.0, commit "
                "8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)"
            ),
            "sha256": (
                "8c0d7e055acf4982854ce708e7b8c10ef7ef56fab12819e0831bf769363bd1e2"
            ),
            "size_bytes": 788,
        },
        "diagnosed_component": "lean_version platform token",
        "hosted_linux_observation_control": {
            "boundary": (
                "This exact Linux version line is retained from a different "
                "same-run checker and supports the platform diagnosis. It is not "
                "the deleted descriptor-checker stdout or temporary JSON from the "
                "failed formal-PDF job."
            ),
            "checker": "scripts/check-lean-exact-log-product.py",
            "job_id": 90509073386,
            "lean_version": (
                "Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit "
                "8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)"
            ),
            "log_sha256": (
                "a9415c629d36100514be65a193d2d30e7bc0e5188f42fd3c7d3ba5d37f4a206a"
            ),
            "log_size_bytes": 155426,
            "step_number": 21,
        },
        "hosted_ubuntu_reconstruction": {
            "lean_version": (
                "Lean (version 4.32.0, x86_64-unknown-linux-gnu, commit "
                "8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)"
            ),
            "retention": (
                "Deterministically reconstructed from the exact descriptor "
                "checker, committed receipt, and different same-run Linux "
                "observation control; the failed job's stdout and temporary JSON "
                "were deleted and are not claimed as directly retained."
            ),
            "sha256": (
                "5bfa5e4204c96ea96f719475944604692aaa372dc8ee5f9e729dbe5817d26184"
            ),
            "size_bytes": 788,
        },
        "stable_reported_identity": {
            "build": "Release",
            "commit": "8c9756b28d64dab099da31a4c09229a9e6a2ef35",
            "version": "4.32.0",
        },
    }
    require_strict_json_equal(
        failure,
        {
            "classification": "evidence_portability",
            "control_flow_diagnosis": expected_control_flow,
            "cross_host_receipts": expected_cross_host,
            "evidence_reproducibility_failure": True,
            "exact_error": (
                "foundational shared-exclusions PID audit PDF check: Lean "
                "factorization evidence is stale or not reproducible"
            ),
            "first_failed_intra_step_route": (
                "scripts/check-foundational-sxpid-audit-pdf.sh --cross-toolchain"
            ),
            "kernel_failure": False,
            "log_digest_domain": (
                "decoded bytes returned by the GitHub Actions per-job logs REST "
                "endpoint"
            ),
            "log_sha256": (
                "06c612a30cd02dc9f9a3957b47cdf96cd2d2e75ff08cf050272bcb518d49b234"
            ),
            "log_size_bytes": 58025,
            "scientific_counterexample": False,
            "step_name": (
                "Rebuild warning-free papers and compare text, page geometry, "
                "and embedded fonts"
            ),
            "step_number": 8,
            "theorem_failure": False,
            "tool_provisioning_failure": False,
        },
        "C2 portability failure diagnosis",
    )
    completed_routes = [
        "python3 scripts/check-formal-pdf-style.py",
        "python3 scripts/check-formal-pdf-style-self-test.py",
        "scripts/check-certified-sxpid2-assurance-pdf.sh --cross-toolchain",
        "scripts/check-dependency-colored-sxpid-pdf.sh --cross-toolchain",
        "scripts/check-ecosystem-compatibility-audit-pdf.sh --cross-toolchain",
        "scripts/check-exact-log-product-sxpid2-pdf.sh --cross-toolchain",
        "scripts/check-finite-alphabet-convergence-pdf.sh --cross-toolchain",
        "scripts/check-formal-tool-adoption-pdf.sh --cross-toolchain",
    ]
    failed_routes = [
        "scripts/check-foundational-sxpid-audit-pdf.sh --cross-toolchain"
    ]
    unreached_routes = [
        "scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
        "scripts/check-support-change-tolerant-sxpid-pdf.sh --cross-toolchain",
    ]
    route_credit_boundary = (
        "GitHub reports the containing shell step as failed. The completion "
        "markers are retained as command-level observations but receive no "
        "independent Actions-step success conclusion."
    )
    require_strict_json_equal(
        failed_job.get("intra_step_routes"),
        {
            "completed_before_failure_without_independent_actions_step_credit": (
                completed_routes
            ),
            "credit_boundary": route_credit_boundary,
            "failed": failed_routes,
            "unreached": unreached_routes,
        },
        "C2 portability formal-PDF route credit",
    )
    skipped_actions = [
        {
            "conclusion": "skipped",
            "name": (
                "Post Run actions/cache@"
                "27d5ce7f107fe9357f9df03efb73ab90386fccae"
            ),
            "number": 15,
            "status": "completed",
        }
    ]
    require_strict_json_equal(
        failed_job.get("skipped_actions_steps"),
        skipped_actions,
        "C2 portability skipped Actions steps",
    )

    expected_certified_steps = [
        {
            "conclusion": "success",
            "name": "Run python3 scripts/check-lean-exact-log-product.py",
            "number": 21,
        },
        {
            "conclusion": "success",
            "name": "Run python3 scripts/check-certified-sxpid2-claim.py",
            "number": 22,
        },
        {
            "conclusion": "success",
            "name": (
                "Run python3 scripts/check-certified-sxpid2-claim-self-test.py"
            ),
            "number": 23,
        },
        {
            "conclusion": "success",
            "name": "Run cargo install cargo-deny --locked --version 0.20.2",
            "number": 24,
        },
        {
            "conclusion": "success",
            "name": (
                "Run cargo deny --manifest-path "
                "audit/tools/certified-sxpid/Cargo.toml --config "
                "audit/tools/certified-sxpid/deny.toml check"
            ),
            "number": 25,
        },
        {
            "conclusion": "success",
            "name": (
                "Post Run actions/setup-python@"
                "ece7cb06caefa5fff74198d8649806c4678c61a1"
            ),
            "number": 49,
        },
    ]
    certified = jobs.get("certified_sxpid2_job")
    require(
        isinstance(certified, dict),
        "C2 certified-SxPID2 control job must be an object",
    )
    require_strict_json_equal(
        certified,
        {
            "claim_boundary": (
                "This hosted job executed the previously failed or skipped "
                "exact-log-product, certified-claim, mutation, cargo-deny "
                "installation, and dependency-audit steps successfully. That is "
                "bounded execution evidence for those commands on this commit, "
                "not a universal mathematical or security proof."
            ),
            "completed_at": "2026-07-29T07:29:17Z",
            "conclusion": "success",
            "id": 90509073386,
            "log_sha256": (
                "a9415c629d36100514be65a193d2d30e7bc0e5188f42fd3c7d3ba5d37f4a206a"
            ),
            "log_size_bytes": 155426,
            "name": "Exact-count directed-rounding SxPID2 reference",
            "restored_steps": expected_certified_steps,
            "started_at": "2026-07-29T07:21:55Z",
            "status": "completed",
        },
        "C2 certified-SxPID2 control job",
    )
    ksg = jobs.get("ksg_phase_job")
    require_strict_json_equal(
        ksg,
        {
            "claim_boundary": (
                "This same-run success covers the scoped arithmetic, modular, "
                "mutation, phase-isolation, production-path, and serial/parallel "
                "commands executed by this job. It does not override the "
                "complete-run failure or close KSG integration."
            ),
            "completed_at": "2026-07-29T07:48:21Z",
            "conclusion": "success",
            "id": 90509073372,
            "log_sha256": (
                "f197b00e992f58f00695b68315e1864937f886e47f1823208d3ca177a716f087"
            ),
            "log_size_bytes": 78318,
            "name": "KSG integer-harmonic arithmetic and phase isolation",
            "started_at": "2026-07-29T07:22:16Z",
            "status": "completed",
        },
        "C2 KSG phase control job",
    )
    require_strict_json_equal(
        jobs.get("lean_environment_control_job"),
        {
            "claim_boundary": (
                "This same-run job supplies a successful pinned Lean/Mathlib "
                "environment control and separate formal-route execution. It does "
                "not make the failed composite PDF step successful."
            ),
            "completed_at": "2026-07-29T07:25:32Z",
            "conclusion": "success",
            "id": 90509073344,
            "log_sha256": (
                "544857550631cd4079db2aabc6ff5d534ae90767caa3a3c4011363ea515c2c41"
            ),
            "log_size_bytes": 44565,
            "name": (
                "Finite-alphabet, dependency-color, support-change, and KSG "
                "harmonic proof cores"
            ),
            "started_at": "2026-07-29T07:21:30Z",
            "status": "completed",
        },
        "C2 Lean-environment control job",
    )

    codeql_raw = receipt.get("codeql")
    require(
        isinstance(codeql_raw, dict)
        and set(codeql_raw) == {"alert_snapshot", "execution"},
        "C2 CodeQL evidence shape changed",
    )
    codeql = cast(dict[str, Any], codeql_raw)
    execution = codeql.get("execution")
    require(
        isinstance(execution, dict)
        and set(execution)
        == {
            "jobs",
            "log_digest_domain",
            "run",
            "scan_clean",
            "step_success_count",
            "step_total_count",
        },
        "C2 CodeQL execution shape changed",
    )
    execution_dict = cast(dict[str, Any], execution)
    codeql_run = {
        "attempt": 1,
        "conclusion": "success",
        "created_at": "2026-07-29T07:21:24Z",
        "event": "dynamic",
        "head_branch": "main",
        "head_sha": C2_TOOLING_CORRECTION,
        "html_url": "https://github.com/sepahead/pid-rs/actions/runs/30431351202",
        "id": 30431351202,
        "job_success_count": 4,
        "job_total_count": 4,
        "name": "Push on main",
        "run_number": 84,
        "status": "completed",
        "updated_at": "2026-07-29T07:23:33Z",
        "workflow_id": 310582096,
    }
    require_strict_json_equal(
        {
            "log_digest_domain": execution_dict.get("log_digest_domain"),
            "run": execution_dict.get("run"),
            "scan_clean": execution_dict.get("scan_clean"),
            "step_success_count": execution_dict.get("step_success_count"),
            "step_total_count": execution_dict.get("step_total_count"),
        },
        {
            "log_digest_domain": (
                "decoded bytes returned by the GitHub Actions per-job logs REST "
                "endpoint"
            ),
            "run": codeql_run,
            "scan_clean": False,
            "step_success_count": 40,
            "step_total_count": 40,
        },
        "C2 CodeQL execution identity",
    )
    expected_codeql_jobs = [
        (
            90509073496,
            "Analyze (actions)",
            "2026-07-29T07:21:29Z",
            "2026-07-29T07:22:14Z",
            "5a015f9e27d03d0ad4dc302927d64f5cc974fdaca1094f083649392292d21925",
            119150,
        ),
        (
            90509073504,
            "Analyze (javascript-typescript)",
            "2026-07-29T07:21:29Z",
            "2026-07-29T07:22:37Z",
            "0b6e5e85ecc45d85b54e13a93d5c17f0079797e46876a3d0a383a6577fa221c6",
            206602,
        ),
        (
            90509073555,
            "Analyze (python)",
            "2026-07-29T07:21:41Z",
            "2026-07-29T07:23:06Z",
            "134336f522489511bf64e243127de1d384745dbaa9c04fd7a72efcc8ba873ee7",
            139423,
        ),
        (
            90509073558,
            "Analyze (rust)",
            "2026-07-29T07:21:29Z",
            "2026-07-29T07:23:32Z",
            "600ee675fffaf788cfdfa0644905d1f2f43348db35d90950584eb3493bebf9f6",
            669818,
        ),
    ]
    require_strict_json_equal(
        execution_dict.get("jobs"),
        [
            {
                "completed_at": completed_at,
                "conclusion": "success",
                "id": job_id,
                "log_sha256": digest,
                "log_size_bytes": size,
                "name": name,
                "started_at": started_at,
            }
            for job_id, name, started_at, completed_at, digest, size in (
                expected_codeql_jobs
            )
        ],
        "C2 CodeQL job/log inventory",
    )
    expected_alert_snapshot = {
        "all_open_alert_records_predate_run": True,
        "causal_introduction_adjudicated": False,
        "claim_boundary": (
            "This is a point-in-time API projection of alert records, not an "
            "adjudication that any alert is exploitable or a false positive. "
            "Creation before this run shows only that the alert records predate "
            "the run; it does not prove when an underlying defect was introduced."
        ),
        "created_at_max": "2026-07-27T21:06:15Z",
        "created_at_min": "2026-07-15T17:49:51Z",
        "dismissed_count": 46,
        "fixed_count": 0,
        "open_by_language": {"python": 19, "rust": 66},
        "open_by_rule": {
            "py/command-line-injection": 4,
            "py/path-injection": 14,
            "py/redos": 1,
            "rust/hard-coded-cryptographic-value": 15,
            "rust/path-injection": 51,
        },
        "open_by_security_severity": {"critical": 19, "high": 66},
        "open_count": 85,
        "open_projected_on_head_count": 85,
        "open_projection": {
            "canonicalization": (
                "UTF-8 compact sorted-key JSON plus LF; alert objects sorted by "
                "number with exactly created_at, most_recent_commit, number, "
                "rule_id, security_severity, and state"
            ),
            "retrieved_at": "2026-07-29T08:04:23Z",
            "sha256": (
                "69fb93eb779a87cbc639193b00521877dc07f83568ff5de04b1c0aedcfc2ad7e"
            ),
            "size_bytes": 16315,
            "source": (
                "GitHub code-scanning alerts REST endpoint, state=open, all pages"
            ),
        },
        "scan_clean": False,
        "security_adjudication": "not_adjudicated",
    }
    require_strict_json_equal(
        codeql.get("alert_snapshot"),
        expected_alert_snapshot,
        "C2 CodeQL open-alert snapshot",
    )
    require(
        sum(
            cast(dict[str, int], expected_alert_snapshot["open_by_language"]).values()
        )
        == expected_alert_snapshot["open_count"]
        and sum(
            cast(
                dict[str, int],
                expected_alert_snapshot["open_by_security_severity"],
            ).values()
        )
        == expected_alert_snapshot["open_count"],
        "C2 CodeQL alert projections do not close the open total",
    )

    expected_remediation = {
        "chosen_correction": {
            "description": (
                "Strictly parse the complete Lean version process result, require "
                "exact version 4.32.0, exact 40-hex source commit, Release build, "
                "zero exit, empty stderr, and one complete line; validate but omit "
                "the host platform token from the reproducible v2 evidence projection."
            ),
            "hostile_version_probes_required": 19,
            "portable_controls_required": 2,
            "scope": (
                "descriptor checker, its self-test, and their two generated "
                "evidence files only"
            ),
        },
        "rejected_alternative": {
            "description": (
                "Keep platform-bearing v1 evidence and make only the wrapper's "
                "cross-toolchain comparison ignore the platform substring."
            ),
            "reason": (
                "That approach would preserve two comparison semantics for the "
                "same evidence schema and move trust into a shell comparator with "
                "a larger bypass surface. The selected v2 schema instead separates "
                "a validated host observation from an explicitly portable identity "
                "projection; the failure receipt retains both observed platform "
                "strings and raw/reconstructed v1 digests."
            ),
        },
        "scientific_claims_changed": False,
        "settled_full_ci": False,
        "whole_run_rerun_required": True,
        "workflow_changed": False,
    }
    require_strict_json_equal(
        receipt.get("remediation"),
        expected_remediation,
        "C2 portability remediation and no-credit state",
    )
    require_strict_json_equal(
        {
            "historical_chosen_correction": expected_remediation["chosen_correction"],
            "historical_receipt_sha256": hashlib.sha256(raw).hexdigest(),
            "historical_workflow_changed": expected_remediation["workflow_changed"],
        },
        {
            "historical_chosen_correction": (
                EXPECTED_HISTORICAL_REMEDIATION_SUPERSESSION[
                    "historical_chosen_correction"
                ]
            ),
            "historical_receipt_sha256": (
                EXPECTED_HISTORICAL_REMEDIATION_SUPERSESSION[
                    "historical_receipt_sha256"
                ]
            ),
            "historical_workflow_changed": (
                EXPECTED_HISTORICAL_REMEDIATION_SUPERSESSION[
                    "historical_workflow_changed"
                ]
            ),
        },
        "historical receipt/remediation supersession cross-binding",
    )
    require(
        expected_head["commit"]
        == expected_run["head_sha"]
        == cast(dict[str, Any], codeql_run)["head_sha"]
        == C2_TOOLING_CORRECTION,
        "C2 portability CI/CodeQL commit bindings diverged",
    )
    require(
        commit_identity(C2_TOOLING_CORRECTION)[0] == C2_TOOLING_CORRECTION_TREE,
        "C2 portability receipt subject does not resolve to its pinned tree",
    )

    memo_raw = read_candidate_bytes(PORTABILITY_CORRECTIVE_EVIDENCE)
    require(
        hashlib.sha256(memo_raw).hexdigest()
        == PORTABILITY_CORRECTIVE_EVIDENCE_SHA256,
        "C2 portability corrective memo differs from its reviewed bytes",
    )
    try:
        memo = memo_raw.decode("utf-8")
        changelog = read_candidate_bytes("CHANGELOG.md").decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            "C2 portability corrective memo or changelog is not UTF-8"
        ) from error
    parser_receipt_prefix = (
        "Parser-only normal and optimized outputs are each `12166` bytes, "
        "byte-identical,\nand SHA-256\n"
    )
    parser_receipt_claim = (
        parser_receipt_prefix
        + f"`{EXPECTED_LEAN_PORTABILITY_PARSER_RECEIPT_SHA256}`."
    )
    require(
        memo.count(parser_receipt_prefix) == 1
        and memo.count(parser_receipt_claim) == 1,
        "C3 portability memo parser-only digest differs from executed parser receipt",
    )
    begin = "PUBLIC_CI_PORTABILITY_FAILURE_PARITY_BEGIN\n"
    end = "\nPUBLIC_CI_PORTABILITY_FAILURE_PARITY_END"
    require(
        memo.count(begin) == 1 and memo.count(end) == 1,
        "C2 portability memo parity sentinels are not unique",
    )
    prefix, remainder = memo.split(begin, 1)
    parity_text, suffix = remainder.split(end, 1)
    require(
        prefix.endswith("```text\n") and suffix.startswith("\n```"),
        "C2 portability memo parity block lost its exact code-fence boundary",
    )
    parity = canonical_json_from_bytes(
        (parity_text + "\n").encode("utf-8"),
        label="C2 portability human parity block",
    )
    expected_parity = {
        "certified_job": {
            "conclusion": "success",
            "id": 90509073386,
            "restored_step_numbers": [21, 22, 23, 24, 25, 49],
        },
        "codeql": {
            "execution": {
                "conclusion": "success",
                "job_success_count": 4,
                "job_total_count": 4,
                "run_id": 30431351202,
            },
            "open_alert_snapshot": {
                "critical": 19,
                "high": 66,
                "open_count": 85,
                "python": 19,
                "rust": 66,
                "scan_clean": False,
                "security_adjudication": "not_adjudicated",
            },
        },
        "failure": {
            "classification": "evidence_portability",
            "exact_error": failure["exact_error"],
            "job_id": failed_job["id"],
            "kernel_failure": False,
            "log_sha256": failure["log_sha256"],
            "log_size_bytes": failure["log_size_bytes"],
            "scientific_counterexample": False,
            "step_number": 8,
            "theorem_failure": False,
            "tool_provisioning_failure": False,
        },
        "head": {
            "commit": C2_TOOLING_CORRECTION,
            "tree": C2_TOOLING_CORRECTION_TREE,
        },
        "integration_disposition": (
            "NO-GO pending a fresh complete public rerun"
        ),
        "job_counts": {"failed": 1, "success": 44, "total": 45},
        "ksg_job": {"conclusion": "success", "id": 90509073372},
        "receipt_path": PUBLIC_CI_PORTABILITY_RECEIPT,
        "receipt_sha256": PUBLIC_CI_PORTABILITY_RECEIPT_SHA256,
        "remediation": {
            "scientific_claims_changed": False,
            "settled_full_ci": False,
            "whole_run_rerun_required": True,
            "workflow_changed": False,
        },
        "run": {
            "attempt": 1,
            "conclusion": "failure",
            "id": 30431352389,
            "number": 147,
            "status": "completed",
        },
        "schema": "pid-rs/public-ci-portability-failure-human-parity",
        "schema_revision": 1,
    }
    require_strict_json_equal(
        parity,
        expected_parity,
        "C2 portability human/machine parity projection",
    )
    require(
        "That route was not selected." in memo
        and "A fresh\nhosted C3 run must then complete all CI jobs successfully."
        in memo
        and "Execution success is not scan cleanliness." in memo
        and (
            "premise-bound source model freezes 383 `require` call sites, "
            "43 direct\nmessage-producing `PhaseIsolationError` sites, and "
            "408 distinct full-message\ntemplates."
        )
        in memo
        and (
            "Per-observed-detail normalized-template uniqueness does not "
            "prove that all 408\nregular-expression languages are globally "
            "pairwise disjoint"
        )
        in memo
        and memo.count(C3_REVIEW_BEGIN) == 1
        and memo.count(C3_REVIEW_END) == 1
        and memo.split(C3_REVIEW_BEGIN, 1)[0].endswith("```text\n")
        and memo.split(C3_REVIEW_END, 1)[1].startswith("\n```\n"),
        "C2 portability memo lost correction-status or security boundaries",
    )
    validate_c3_precommit_review_ledger(memo)
    require(
        (
            "launched as\n"
            "`python3 scripts/check-ksg-phase-isolation-self-test.py` in "
            "unified-exec\nsession `55661` with parent PID `92493`"
        )
        in memo
        and (
            "ERROR: KSG phase isolation: Git executable, configuration, "
            "metadata, or visibility context changed during replay"
        )
        in memo
        and (
            "the exact terminal elapsed time was not captured and is not "
            "reconstructed."
        )
        in memo
        and (
            "The evidence does not identify a particular changed byte or "
            "metadata field,\nand no such claim is made."
        )
        in memo
        and (
            "never invoke Git or inspect filesystem metadata inside an active\n"
            "custody temporary clone. Monitor only process IDs and process "
            "state from\noutside the clone"
        )
        in memo
        and (
            "optimized aggregate in unified-exec session `74678`\n"
            "with parent PID `22724` also receives no credit, regardless of "
            "its terminal\nresult"
        )
        in memo
        and (
            "deliberately stopped with `SIGINT`\nand exited `130` with "
            "`KeyboardInterrupt` while executing\n"
            "`run_public_ci_portability_evidence_attacks`"
        )
        in memo
        and (
            "That controlled stop is neither\n"
            "a checker failure nor a passed subpartition."
        )
        in memo
        and (
            "Its exact terminal wall time was\nnot captured and is not "
            "reconstructed."
        )
        in memo,
        "C2 portability memo lost the orchestration-contamination no-credit boundary",
    )
    require(
        (
            "Every directly path-invoked C3 Python script is still initially "
            "loaded from\nits requested pathname"
        )
        in memo
        and "not an atomic loader guarantee." in memo
        and (
            "Only the explicitly nested\n"
            "  standard-input and exact-source loader routes bind source bytes "
            "before\n"
            "  execution."
        )
        in changelog,
        "C3 portability memo lost the top-level loader premise",
    )
    require(
        (
            "retained `HOME` reaches and can influence selected launcher state."
            in memo
        ),
        "C3 portability memo lost the HOME/launcher negative boundary",
    )
    require(
        (
            "contracted aggregate is 351 cases; credit\n"
            "requires settled final-byte normal and optimized replays:"
        )
        in memo,
        "C3 portability memo falsely credits unsettled hostile counts",
    )
    require(
        "not evidence that the suite passed or a weakening of any case." in memo,
        "C3 portability memo lost the timeout nonclaim",
    )
    return memo_raw


def validate_ci_corrective_firewall() -> None:
    relative = ".github/workflows/ci.yml"
    prior_expected = git_blob_at(M1A_SCIENTIFIC_COMMIT, relative)
    phase_prefix = (
        b"      - name: Verify the exact KSG-only Git phase envelope\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          checkpoint="$(git rev-parse --verify HEAD)"\n'
    )
    normalized_phase_prefix = (
        b"      - name: Verify the exact KSG-only Git phase envelope\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b'          worktree_config=".git/config.worktree"\n'
        b'          expected_worktree_config_sha256="443a5f645c23c3d0c0aa09f634b2ad111d46ef61946b598a2fb311678ab47454"\n'
        b"          if [[ ! -d .git || -L .git ]]; then\n"
        b"            printf 'expected a real .git directory at the Actions checkout root\\n' >&2\n"
        b"            exit 1\n"
        b"          fi\n"
        b'          if [[ -e "$worktree_config" || -L "$worktree_config" ]]; then\n'
        b'            if [[ ! -f "$worktree_config" || -L "$worktree_config" ]]; then\n'
        b"              printf 'refusing non-regular checkout worktree config: %s\\n' \\\n"
        b'                "$worktree_config" >&2\n'
        b"              exit 1\n"
        b"            fi\n"
        b'            if [[ "$(stat -c \'%h\' "$worktree_config")" != "1" ]]; then\n'
        b"              printf 'refusing hard-linked checkout worktree config: %s\\n' \\\n"
        b'                "$worktree_config" >&2\n'
        b"              exit 1\n"
        b"            fi\n"
        b"            if ! printf '%s  %s\\n' \\\n"
        b'              "$expected_worktree_config_sha256" "$worktree_config" \\\n'
        b"              | sha256sum --check --strict --status\n"
        b"            then\n"
        b"              printf 'checkout worktree config bytes are not the reviewed inert residue\\n' >&2\n"
        b"              exit 1\n"
        b"            fi\n"
        b'            unlink -- "$worktree_config"\n'
        b"          fi\n"
        b'          if [[ -e "$worktree_config" || -L "$worktree_config" ]]; then\n'
        b"            printf 'checkout worktree config survived exact normalization\\n' >&2\n"
        b"            exit 1\n"
        b"          fi\n"
        b'          checkpoint="$(git rev-parse --verify HEAD)"\n'
    )
    prior_expected = replace_unique_workflow_fragment(
        prior_expected,
        phase_prefix,
        normalized_phase_prefix,
        label="prior checkout residue normalization",
    )
    prior_expected = replace_unique_workflow_fragment(
        prior_expected,
        b"            latexmk \\\n            lmodern \\\n",
        (
            b"            latexmk \\\n"
            b"            lacheck \\\n"
            b"            lmodern \\\n"
        ),
        label="prior lacheck package",
    )
    prior_expected = replace_unique_workflow_fragment(
        prior_expected,
        (
            b"          cargo deny --manifest-path "
            b"audit/tools/certified-sxpid/Cargo.toml check\n"
            b"          --config audit/tools/certified-sxpid/deny.toml\n"
        ),
        (
            b"          cargo deny --manifest-path "
            b"audit/tools/certified-sxpid/Cargo.toml\n"
            b"          --config audit/tools/certified-sxpid/deny.toml check\n"
        ),
        label="prior cargo-deny 0.20.2 common-option order",
    )
    corrective_parent = git_blob_at(CORRECTIVE_PARENT, relative)
    require(
        prior_expected == corrective_parent,
        "af509 workflow differs from the exact prior three-edit dc7 transform",
    )

    expected = corrective_parent
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"  ksg-harmonic-assurance:\n"
            b"    name: KSG integer-harmonic arithmetic and phase isolation\n"
            b"    runs-on: ubuntu-latest\n"
            b"    timeout-minutes: 45\n"
        ),
        (
            b"  ksg-harmonic-assurance:\n"
            b"    name: KSG integer-harmonic arithmetic and phase isolation\n"
            b"    runs-on: ubuntu-latest\n"
            b"    # The normal and optimized 351-case custody suites run sequentially and\n"
            b"    # intentionally create isolated Git histories for every hostile family.\n"
            b"    timeout-minutes: 240\n"
        ),
        label="KSG hostile-suite measured runtime budget",
    )
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"            latexmk \\\n"
            b"            lacheck \\\n"
            b"            lmodern \\\n"
        ),
        (
            b"            chktex \\\n"
            b"            latexmk \\\n"
            b"            lacheck \\\n"
            b"            lmodern \\\n"
        ),
        label="formal PDF chktex package",
    )
    lean_setup = pinned_lean_setup_and_cache()
    mathlib_build = pinned_mathlib_build()
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"      - uses: actions/setup-python@"
            b"ece7cb06caefa5fff74198d8649806c4678c61a1 # v6\n"
            b"        with:\n"
            b'          python-version: "3.11"\n'
            b"      - run: >-\n"
            b"          cargo fetch --locked\n"
        ),
        (
            b"      - uses: actions/setup-python@"
            b"ece7cb06caefa5fff74198d8649806c4678c61a1 # v6\n"
            b"        with:\n"
            b'          python-version: "3.11"\n'
            + lean_setup
            + b"      - run: >-\n"
            b"          cargo fetch --locked\n"
        ),
        label="certified SxPID2 pinned Lean provisioning",
    )
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"      - run: python3 "
            b"audit/tools/certified-sxpid/scripts/challenge-exact-products.py\n"
            b"      - run: python3 scripts/check-lean-exact-log-product.py\n"
        ),
        (
            b"      - run: python3 "
            b"audit/tools/certified-sxpid/scripts/challenge-exact-products.py\n"
            + mathlib_build
            + b"      - run: python3 scripts/check-lean-exact-log-product.py\n"
        ),
        label="certified SxPID2 Mathlib build",
    )
    formal_checkout = (
        b"      - uses: actions/checkout@"
        b"9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
        b"        with:\n"
        b"          persist-credentials: false\n"
        b"      - name: Check the typed citation edge and adjacent-arrow countermodel\n"
    )
    expected = replace_unique_workflow_fragment(
        expected,
        formal_checkout,
        (
            b"      - uses: actions/checkout@"
            b"9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7\n"
            b"        with:\n"
            b"          persist-credentials: false\n"
            + lean_setup
            + mathlib_build
            + b"      - name: Check the typed citation edge and adjacent-arrow countermodel\n"
        ),
        label="formal PDF pinned Lean and Mathlib provisioning",
    )
    for before, after, label in (
        (
            b"          python3 scripts/check-ksg-phase-isolation.py \\\n",
            b"          python3 -I -S scripts/check-ksg-phase-isolation.py \\\n",
            "normal KSG phase safe startup",
        ),
        (
            b"          python3 -O scripts/check-ksg-phase-isolation.py \\\n",
            b"          python3 -I -S -O scripts/check-ksg-phase-isolation.py \\\n",
            "optimized KSG phase safe startup",
        ),
        (
            b"          python3 scripts/check-ksg-phase-isolation-self-test.py\n",
            b"          python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            "normal KSG phase hostile-suite safe startup",
        ),
        (
            b"          python3 -O scripts/check-ksg-phase-isolation-self-test.py\n",
            b"          python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
            "optimized KSG phase hostile-suite safe startup",
        ),
    ):
        expected = replace_unique_workflow_fragment(
            expected,
            before,
            after,
            label=label,
        )
    require(
        read_candidate_bytes(relative) == expected,
        "CI corrective workflow differs from the exact af509 tooling transform",
    )


def validate_claim_checker_workflow_rebind() -> None:
    checker_path = "scripts/check-certified-sxpid2-claim.py"
    expected = git_blob_at(CORRECTIVE_PARENT, checker_path)
    workflow = read_candidate_bytes(".github/workflows/ci.yml")
    workflow_lines = workflow.splitlines(keepends=True)
    starts = [
        index
        for index, line in enumerate(workflow_lines)
        if line == b"  certified-sxpid-reference:\n"
    ]
    require(
        len(starts) == 1,
        "corrected workflow does not contain one certified-SxPID2 job",
    )
    start = starts[0]
    end = next(
        (
            index
            for index in range(start + 1, len(workflow_lines))
            if re.fullmatch(rb"  [A-Za-z0-9_-]+:\n", workflow_lines[index])
            is not None
        ),
        len(workflow_lines),
    )
    job_digest = hashlib.sha256(b"".join(workflow_lines[start:end])).hexdigest()
    workflow_digest = hashlib.sha256(workflow).hexdigest()
    justfile_digest = hashlib.sha256(read_candidate_bytes("justfile")).hexdigest()
    expected = replace_unique_workflow_fragment(
        expected,
        b"32670cfac1bcd508b2658db2950bbce4689ca695b29367b08b6f71c1010a30e2",
        job_digest.encode("ascii"),
        label="certified job digest rebind",
    )
    expected = replace_unique_workflow_fragment(
        expected,
        b"b3cfb2be2bb310545faf8abc662333167745f863aab29f074d25a60b223ba02c",
        workflow_digest.encode("ascii"),
        label="complete workflow digest rebind",
    )
    expected = replace_unique_workflow_fragment(
        expected,
        b"8dc0c452b1b95a080e93091fd4c18d32864daed903c415bf422f366c4edb91b2",
        justfile_digest.encode("ascii"),
        label="complete justfile digest rebind",
    )
    require(
        read_candidate_bytes(checker_path) == expected,
        "certified-SxPID2 claim checker differs from its exact three-digest rebind",
    )


def _expected_isolated_entry_preamble(script_name: str) -> str:
    return (
        "from __future__ import annotations\n"
        "\n"
        "import sys as _bootstrap_sys\n"
        "\n"
        "if not (\n"
        "    _bootstrap_sys.flags.isolated == 1\n"
        "    and _bootstrap_sys.flags.safe_path\n"
        "    and _bootstrap_sys.flags.no_site == 1\n"
        "    and _bootstrap_sys.flags.ignore_environment == 1\n"
        "):\n"
        f'    print(\n        "ERROR: {script_name} requires Python -I -S",\n'
        "        file=_bootstrap_sys.stderr,\n"
        "    )\n"
        "    raise SystemExit(2)\n"
        "del _bootstrap_sys\n"
        "\n"
    )


def _validate_isolated_entry_ast(
    source: str,
    *,
    relative: str,
    expected_preamble: str,
) -> ast.Module:
    require(
        source.count(expected_preamble) == 1
        and source.find(expected_preamble) >= 0,
        f"Python isolation preamble changed: {relative}",
    )
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as error:
        raise PhaseIsolationError(
            f"cannot parse isolated Python entry point {relative}: {error}"
        ) from error
    body = tree.body
    require(
        len(body) >= 6
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
        and isinstance(body[1], ast.ImportFrom)
        and body[1].module == "__future__"
        and [(alias.name, alias.asname) for alias in body[1].names]
        == [("annotations", None)]
        and isinstance(body[2], ast.Import)
        and [(alias.name, alias.asname) for alias in body[2].names]
        == [("sys", "_bootstrap_sys")]
        and isinstance(body[3], ast.If)
        and isinstance(body[4], ast.Delete)
        and len(body[4].targets) == 1
        and isinstance(body[4].targets[0], ast.Name)
        and body[4].targets[0].id == "_bootstrap_sys"
        and isinstance(body[5], (ast.Import, ast.ImportFrom)),
        (
            f"Python entry bootstrap ordering changed: {relative}; only the "
            "module docstring/future import may precede builtin sys, and the "
            "guard/delete must precede the first non-builtin import"
        ),
    )
    preamble_start = source.find("from __future__ import annotations\n")
    first_nonbuiltin = body[5]
    require(
        first_nonbuiltin.lineno is not None
        and preamble_start >= 0
        and source[preamble_start:].startswith(expected_preamble),
        f"Python entry preamble is not contiguous before imports: {relative}",
    )
    return tree


def _require_exact_child_python_command(
    tree: ast.Module,
    *,
    relative: str,
    function_name: str,
) -> None:
    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    require(
        len(functions) == 1,
        f"isolated child-command function inventory changed: {relative}",
    )
    command_assignments = [
        node
        for node in ast.walk(functions[0])
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "command"
    ]
    require(
        len(command_assignments) == 1,
        f"isolated child-command assignment inventory changed: {relative}",
    )
    value = command_assignments[0].value
    require(
        isinstance(value, ast.List)
        and len(value.elts) == 3
        and isinstance(value.elts[0], ast.Attribute)
        and isinstance(value.elts[0].value, ast.Name)
        and value.elts[0].value.id == "sys"
        and value.elts[0].attr == "executable"
        and all(
            isinstance(element, ast.Constant) and element.value == expected
            for element, expected in zip(value.elts[1:], ("-I", "-S"), strict=True)
        ),
        f"child Python command lacks exact -I -S prefix: {relative}",
    )


def _require_exact_stdin_child_model(tree: ast.Module) -> None:
    """Bind private materialization, stdin execution, and minimal child inputs."""

    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "run_lean_portability_parser"
    ]
    require(
        len(functions) == 1,
        "exact-stdin child execution function inventory changed",
    )
    function = functions[0]
    run_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    require(
        len(run_calls) == 1,
        "exact-stdin child subprocess inventory changed",
    )
    keywords = {keyword.arg: keyword.value for keyword in run_calls[0].keywords}
    environment_value = keywords.get("env")
    require(
        isinstance(keywords.get("input"), ast.Name)
        and cast(ast.Name, keywords["input"]).id == "self_raw"
        and isinstance(keywords.get("cwd"), ast.Name)
        and cast(ast.Name, keywords["cwd"]).id == "private_root"
        and isinstance(environment_value, ast.Call)
        and isinstance(environment_value.func, ast.Name)
        and environment_value.func.id == "_minimal_python_child_environment"
        and len(environment_value.args) == 1
        and isinstance(environment_value.args[0], ast.Name)
        and environment_value.args[0].id == "private_root",
        "exact-stdin child process inputs changed",
    )
    extend_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "command"
        and node.func.attr == "extend"
    ]
    require(
        len(extend_calls) == 1
        and len(extend_calls[0].args) == 1
        and isinstance(extend_calls[0].args[0], ast.Tuple)
        and len(extend_calls[0].args[0].elts) == 4,
        "exact-stdin child command extension changed",
    )
    extension = cast(ast.Tuple, extend_calls[0].args[0]).elts
    require(
        isinstance(extension[0], ast.Constant)
        and extension[0].value == "-c"
        and isinstance(extension[1], ast.Name)
        and extension[1].id == "EXACT_STDIN_BOOTSTRAP"
        and isinstance(extension[2], ast.Call)
        and isinstance(extension[2].func, ast.Name)
        and extension[2].func.id == "str"
        and len(extension[2].args) == 1
        and isinstance(extension[2].args[0], ast.Name)
        and extension[2].args[0].id == "self_path"
        and isinstance(extension[3], ast.Constant)
        and extension[3].value == "--parser-only",
        "exact-stdin child command payload changed",
    )
    writes = [
        (
            cast(ast.Name, node.func.value).id,
            cast(ast.Name, node.args[0]).id,
        )
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_bytes"
        and isinstance(node.func.value, ast.Name)
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Name)
    ]
    require(
        sorted(writes)
        == [
            ("checker_path", "checker_raw"),
            ("self_path", "self_raw"),
        ],
        "private exact-child materialization inventory changed",
    )
    require(
        hashlib.sha256(EXACT_STDIN_BOOTSTRAP.encode("utf-8")).hexdigest()
        == EXPECTED_EXACT_STDIN_BOOTSTRAP_SHA256,
        "exact-stdin bootstrap digest changed",
    )


def _source_model_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(
        len(functions) == 1,
        f"candidate self-test function inventory changed: {name}",
    )
    return functions[0]


def _source_model_constant(tree: ast.Module, name: str) -> object:
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    require(
        len(assignments) == 1
        and isinstance(assignments[0].value, ast.Constant),
        f"candidate self-test constant inventory changed: {name}",
    )
    return cast(ast.Constant, assignments[0].value).value


def _require_candidate_checker_bootstrap(tree: ast.Module) -> None:
    bootstrap = _source_model_constant(
        tree,
        "CANDIDATE_CHECKER_STDIN_BOOTSTRAP",
    )
    declared_digest = _source_model_constant(
        tree,
        "EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256",
    )
    require(
        isinstance(bootstrap, str)
        and declared_digest == EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256
        and hashlib.sha256(bootstrap.encode("utf-8")).hexdigest()
        == EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256,
        "candidate-checker stdin bootstrap digest changed",
    )
    try:
        bootstrap_tree = ast.parse(bootstrap, filename="<candidate-checker-stdin>")
    except SyntaxError as error:
        raise PhaseIsolationError(
            f"candidate-checker stdin bootstrap AST changed: {error}"
        ) from error
    body = bootstrap_tree.body
    require(
        len(body) == 7
        and isinstance(body[0], ast.Import)
        and [(alias.name, alias.asname) for alias in body[0].names]
        == [("sys", None)]
        and all(isinstance(statement, ast.Assign) for statement in body[1:6])
        and isinstance(body[6], ast.Expr),
        "candidate-checker stdin bootstrap AST changed",
    )


def _require_candidate_checker_bootstrap_ast(tree: ast.Module) -> None:
    """Require every semantic edge of the already digest-bound bootstrap."""

    bootstrap = cast(
        str,
        _source_model_constant(tree, "CANDIDATE_CHECKER_STDIN_BOOTSTRAP"),
    )
    module = ast.parse(bootstrap, filename="<candidate-checker-stdin>")
    body = module.body
    require(
        len(body) == 7
        and isinstance(body[1], ast.Assign)
        and len(body[1].targets) == 1
        and isinstance(body[1].targets[0], ast.Name)
        and body[1].targets[0].id == "logical_file"
        and isinstance(body[1].value, ast.Subscript)
        and isinstance(body[1].value.value, ast.Attribute)
        and isinstance(body[1].value.value.value, ast.Name)
        and body[1].value.value.value.id == "sys"
        and body[1].value.value.attr == "argv"
        and isinstance(body[1].value.slice, ast.Constant)
        and body[1].value.slice.value == 1
        and isinstance(body[2], ast.Assign)
        and len(body[2].targets) == 1
        and isinstance(body[2].targets[0], ast.Attribute)
        and isinstance(body[2].targets[0].value, ast.Name)
        and body[2].targets[0].value.id == "sys"
        and body[2].targets[0].attr == "argv"
        and isinstance(body[2].value, ast.List)
        and len(body[2].value.elts) == 2
        and isinstance(body[2].value.elts[0], ast.Name)
        and body[2].value.elts[0].id == "logical_file"
        and isinstance(body[2].value.elts[1], ast.Starred)
        and isinstance(body[2].value.elts[1].value, ast.Subscript)
        and isinstance(body[2].value.elts[1].value.value, ast.Attribute)
        and isinstance(body[2].value.elts[1].value.value.value, ast.Name)
        and body[2].value.elts[1].value.value.value.id == "sys"
        and body[2].value.elts[1].value.value.attr == "argv"
        and isinstance(body[2].value.elts[1].value.slice, ast.Slice)
        and isinstance(body[2].value.elts[1].value.slice.lower, ast.Constant)
        and body[2].value.elts[1].value.slice.lower.value == 2
        and body[2].value.elts[1].value.slice.upper is None
        and body[2].value.elts[1].value.slice.step is None
        and isinstance(body[3], ast.Assign)
        and len(body[3].targets) == 1
        and isinstance(body[3].targets[0], ast.Name)
        and body[3].targets[0].id == "source"
        and isinstance(body[3].value, ast.Call)
        and isinstance(body[3].value.func, ast.Attribute)
        and body[3].value.func.attr == "read"
        and isinstance(body[3].value.func.value, ast.Attribute)
        and body[3].value.func.value.attr == "buffer"
        and isinstance(body[3].value.func.value.value, ast.Attribute)
        and body[3].value.func.value.value.attr == "stdin"
        and isinstance(body[3].value.func.value.value.value, ast.Name)
        and body[3].value.func.value.value.value.id == "sys"
        and not body[3].value.args
        and not body[3].value.keywords,
        "candidate-checker stdin bootstrap AST changed",
    )
    namespace_assignment = cast(ast.Assign, body[4])
    require(
        len(namespace_assignment.targets) == 1
        and isinstance(namespace_assignment.targets[0], ast.Name)
        and namespace_assignment.targets[0].id == "namespace"
        and isinstance(namespace_assignment.value, ast.Dict)
        and [
            cast(ast.Constant, key).value
            for key in namespace_assignment.value.keys
            if isinstance(key, ast.Constant)
        ]
        == [
            "__name__",
            "__file__",
            "__package__",
            "__cached__",
            "__pid_rs_exact_source_bytes__",
        ]
        and len(namespace_assignment.value.values) == 5
        and isinstance(namespace_assignment.value.values[0], ast.Constant)
        and namespace_assignment.value.values[0].value == "__main__"
        and isinstance(namespace_assignment.value.values[1], ast.Name)
        and namespace_assignment.value.values[1].id == "logical_file"
        and all(
            isinstance(value, ast.Constant) and value.value is None
            for value in namespace_assignment.value.values[2:4]
        )
        and isinstance(namespace_assignment.value.values[4], ast.Name)
        and namespace_assignment.value.values[4].id == "source",
        "candidate-checker stdin bootstrap AST changed",
    )
    code_assignment = cast(ast.Assign, body[5])
    compile_call = code_assignment.value
    require(
        len(code_assignment.targets) == 1
        and isinstance(code_assignment.targets[0], ast.Name)
        and code_assignment.targets[0].id == "code"
        and isinstance(compile_call, ast.Call)
        and isinstance(compile_call.func, ast.Name)
        and compile_call.func.id == "compile"
        and len(compile_call.args) == 3
        and isinstance(compile_call.args[0], ast.Name)
        and compile_call.args[0].id == "source"
        and isinstance(compile_call.args[1], ast.Name)
        and compile_call.args[1].id == "logical_file"
        and isinstance(compile_call.args[2], ast.Constant)
        and compile_call.args[2].value == "exec"
        and [keyword.arg for keyword in compile_call.keywords]
        == ["dont_inherit", "optimize"]
        and isinstance(compile_call.keywords[0].value, ast.Constant)
        and compile_call.keywords[0].value.value is True
        and isinstance(compile_call.keywords[1].value, ast.Attribute)
        and isinstance(compile_call.keywords[1].value.value, ast.Attribute)
        and isinstance(compile_call.keywords[1].value.value.value, ast.Name)
        and compile_call.keywords[1].value.value.value.id == "sys"
        and compile_call.keywords[1].value.value.attr == "flags"
        and compile_call.keywords[1].value.attr == "optimize",
        "candidate-checker stdin bootstrap AST changed",
    )
    exec_call = cast(ast.Expr, body[6]).value
    require(
        isinstance(exec_call, ast.Call)
        and isinstance(exec_call.func, ast.Name)
        and exec_call.func.id == "exec"
        and len(exec_call.args) == 2
        and isinstance(exec_call.args[0], ast.Name)
        and exec_call.args[0].id == "code"
        and isinstance(exec_call.args[1], ast.Name)
        and exec_call.args[1].id == "namespace"
        and not exec_call.keywords,
        "candidate-checker stdin bootstrap AST changed",
    )


def _require_candidate_checker_invocation_model(tree: ast.Module) -> None:
    function = _source_model_function(tree, "invoke_exact_checker")
    run_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    require(
        len(run_calls) == 1,
        "candidate-checker exact-source subprocess inventory changed",
    )
    require(
        len(run_calls[0].args) == 1
        and isinstance(run_calls[0].args[0], ast.Name)
        and run_calls[0].args[0].id == "command",
        "candidate-checker exact-source subprocess inputs changed",
    )
    keywords = {keyword.arg: keyword.value for keyword in run_calls[0].keywords}
    require(
        set(keywords)
        == {"check", "cwd", "env", "input", "stderr", "stdout"}
        and isinstance(keywords["input"], ast.Attribute)
        and isinstance(keywords["input"].value, ast.Name)
        and keywords["input"].value.id == "entry"
        and keywords["input"].attr == "raw"
        and isinstance(keywords["cwd"], ast.Name)
        and keywords["cwd"].id == "root"
        and isinstance(keywords["env"], ast.Name)
        and keywords["env"].id == "environment"
        and isinstance(keywords["check"], ast.Constant)
        and keywords["check"].value is False
        and all(
            isinstance(keywords[name], ast.Attribute)
            and isinstance(cast(ast.Attribute, keywords[name]).value, ast.Name)
            and cast(ast.Attribute, keywords[name]).value.id == "subprocess"
            and cast(ast.Attribute, keywords[name]).attr == "PIPE"
            for name in ("stdout", "stderr")
        ),
        "candidate-checker exact-source subprocess inputs changed",
    )
    command_assignments = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "command"
    ]
    require(
        len(command_assignments) == 1
        and isinstance(command_assignments[0].value, ast.List)
        and len(command_assignments[0].value.elts) == 3
        and isinstance(command_assignments[0].value.elts[0], ast.Attribute)
        and isinstance(command_assignments[0].value.elts[0].value, ast.Name)
        and command_assignments[0].value.elts[0].value.id == "sys"
        and command_assignments[0].value.elts[0].attr == "executable"
        and all(
            isinstance(element, ast.Constant) and element.value == expected
            for element, expected in zip(
                command_assignments[0].value.elts[1:],
                ("-I", "-S"),
                strict=True,
            )
        ),
        "candidate-checker exact-source command prefix changed",
    )
    append_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "command"
        and node.func.attr == "append"
    ]
    require(
        len(append_calls) == 1
        and len(append_calls[0].args) == 1
        and isinstance(append_calls[0].args[0], ast.Constant)
        and append_calls[0].args[0].value == "-O"
        and not append_calls[0].keywords,
        "candidate-checker exact-source command prefix changed",
    )
    extend_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "command"
        and node.func.attr == "extend"
    ]
    extension = (
        cast(ast.Tuple, extend_calls[0].args[0]).elts
        if len(extend_calls) == 1
        and len(extend_calls[0].args) == 1
        and isinstance(extend_calls[0].args[0], ast.Tuple)
        else []
    )
    require(
        len(extension) == 4
        and isinstance(extension[0], ast.Constant)
        and extension[0].value == "-c"
        and isinstance(extension[1], ast.Name)
        and extension[1].id == "CANDIDATE_CHECKER_STDIN_BOOTSTRAP"
        and isinstance(extension[2], ast.Name)
        and extension[2].id == "logical_file"
        and isinstance(extension[3], ast.Starred)
        and isinstance(extension[3].value, ast.Name)
        and extension[3].value.id == "arguments",
        "candidate-checker exact-source command payload changed",
    )
    environment_assignments = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "environment"
    ]
    require(
        len(environment_assignments) == 1
        and isinstance(environment_assignments[0].value, ast.Call)
        and isinstance(environment_assignments[0].value.func, ast.Name)
        and environment_assignments[0].value.func.id
        == "_exact_checker_child_environment"
        and len(environment_assignments[0].value.args) == 1
        and isinstance(environment_assignments[0].value.args[0], ast.Name)
        and environment_assignments[0].value.args[0].id == "private_root",
        "candidate-checker exact-source child environment changed",
    )


def _require_frozen_overlay_source_model(tree: ast.Module) -> None:
    require(
        _source_model_constant(tree, "EXPECTED_CHANGED_PATH_COUNT") == 187
        and _source_model_constant(
            tree,
            "EXPECTED_ANCHOR_DELTA_PATH_COUNT",
        )
        == 19
        and _source_model_constant(tree, "EXPECTED_SELF_UNHASHED_COUNT") == 2,
        "frozen candidate-overlay runtime construction counts changed",
    )
    for class_name, expected_fields in (
        (
            "FrozenOverlayEntry",
            ("relative", "raw", "mode", "size", "sha256"),
        ),
        ("FrozenOverlay", ("entries", "projection_sha256")),
        ("ExactCheckerInvocation", ("process", "source_entry")),
    ):
        classes = [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ]
        decorators = classes[0].decorator_list if len(classes) == 1 else []
        fields = (
            tuple(
                statement.target.id
                for statement in classes[0].body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
            )
            if len(classes) == 1
            else ()
        )
        require(
            len(decorators) == 1
            and isinstance(decorators[0], ast.Call)
            and isinstance(decorators[0].func, ast.Name)
            and decorators[0].func.id == "dataclass"
            and len(decorators[0].keywords) == 1
            and decorators[0].keywords[0].arg == "frozen"
            and isinstance(decorators[0].keywords[0].value, ast.Constant)
            and decorators[0].keywords[0].value.value is True
            and fields == expected_fields,
            f"frozen candidate-overlay data model changed: {class_name}",
        )
    stable = _source_model_function(tree, "stable_regular_file")
    leaf_lstats = [
        node
        for node in ast.walk(stable)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "path"
        and node.func.attr == "lstat"
    ]
    byte_reads = [
        node
        for node in ast.walk(stable)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "path"
        and node.func.attr == "read_bytes"
    ]
    identity = _source_model_function(tree, "_stable_file_identity")
    return_values = [
        node.value
        for node in identity.body
        if isinstance(node, ast.Return) and node.value is not None
    ]
    identity_attributes = (
        [
            element.attr
            for element in cast(ast.Tuple, return_values[0]).elts
            if isinstance(element, ast.Attribute)
            and isinstance(element.value, ast.Name)
            and element.value.id == "metadata"
        ]
        if len(return_values) == 1 and isinstance(return_values[0], ast.Tuple)
        else []
    )
    require(
        len(leaf_lstats) == 3
        and len(byte_reads) == 2
        and identity_attributes
        == ["st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns"],
        "frozen candidate-overlay stable capture model changed",
    )
    clone = _source_model_function(tree, "clone_candidate")
    copy_calls = [
        node
        for node in ast.walk(clone)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "shutil"
        and node.func.attr.startswith("copy")
    ]
    require(
        not copy_calls,
        "frozen candidate-overlay writer reads a live source path",
    )
    overlay_loops = [
        node
        for node in ast.walk(clone)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "entry"
        and isinstance(node.iter, ast.Attribute)
        and isinstance(node.iter.value, ast.Name)
        and node.iter.value.id == "overlay"
        and node.iter.attr == "entries"
    ]
    require(
        len(overlay_loops) == 1,
        "frozen candidate-overlay writer loop changed",
    )
    require(
        not any(
            isinstance(node, ast.Name) and node.id == "source"
            for node in ast.walk(overlay_loops[0])
        ),
        "frozen candidate-overlay writer reads a live source path",
    )
    loop_calls = [
        node
        for node in ast.walk(overlay_loops[0])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    writes = [
        node
        for node in loop_calls
        if node.func.attr == "write_bytes"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Attribute)
        and isinstance(node.args[0].value, ast.Name)
        and node.args[0].value.id == "entry"
        and node.args[0].attr == "raw"
    ]
    modes = [
        node
        for node in loop_calls
        if node.func.attr == "chmod"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Attribute)
        and isinstance(node.args[0].value, ast.Name)
        and node.args[0].value.id == "entry"
        and node.args[0].attr == "mode"
    ]
    require(
        len(writes) == 1 and len(modes) == 1,
        "frozen candidate-overlay writer no longer uses captured bytes and mode",
    )
    verifier_calls = []
    for statement in clone.body:
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "verify_frozen_overlay"
        ):
            continue
        call = statement.value
        if len(call.args) == 2 and all(
            isinstance(argument, ast.Name)
            and argument.id == expected
            for argument, expected in zip(
                call.args,
                ("destination", "overlay"),
                strict=True,
            )
        ):
            verifier_calls.append(call)
    require(
        len(verifier_calls) == 1,
        "frozen candidate-overlay post-write verification changed",
    )


def _require_candidate_checker_call_integration(tree: ast.Module) -> None:
    for function_name in ("run_checker", "current_facts", "generated_block"):
        function = _source_model_function(tree, function_name)
        exact_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "invoke_exact_checker"
        ]
        path_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "python_command"
        ]
        require(
            len(exact_calls) == 1 and not path_calls,
            f"candidate-checker exact-source caller integration changed: {function_name}",
        )
    rebase = _source_model_function(tree, "rebase_checker")
    generated_calls = [
        node
        for node in ast.walk(rebase)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "generated_block"
    ]
    require(
        len(generated_calls) == 1
        and any(
            keyword.arg == "source_entry"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "entry"
            for keyword in generated_calls[0].keywords
        ),
        "candidate-checker rebase exact-source binding changed",
    )
    require(
        sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "stable_regular_file"
            for node in ast.walk(rebase)
        )
        == 3
        and not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"read_bytes", "read_text"}
            for node in ast.walk(rebase)
        ),
        "candidate-checker rebase source/write verification changed",
    )


def _require_exact_checker_environment_model(tree: ast.Module) -> None:
    override_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "EXACT_CHECKER_ENVIRONMENT_OVERRIDE_KEYS"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "frozenset"
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Set)
    ]
    override_keys = (
        {
            cast(ast.Constant, element).value
            for element in cast(ast.Set, override_assignments[0].value.args[0]).elts
            if isinstance(element, ast.Constant)
        }
        if len(override_assignments) == 1
        else set()
    )
    require(
        override_keys
        == {
            "GIT_ATTR_SOURCE",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_KEY_0",
            "GIT_CONFIG_VALUE_0",
            "GIT_DIR",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
        },
        "candidate-checker exact-source override key set changed",
    )
    function = _source_model_function(tree, "_exact_checker_child_environment")
    assignments = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "environment"
    ]
    dictionary = (
        assignments[0].value
        if len(assignments) == 1 and isinstance(assignments[0].value, ast.Dict)
        else None
    )
    require(
        isinstance(dictionary, ast.Dict)
        and [
            cast(ast.Constant, key).value
            for key in dictionary.keys
            if isinstance(key, ast.Constant)
        ]
        == ["LANG", "LC_ALL", "PATH", "TEMP", "TMP", "TMPDIR", "TZ"],
        "candidate-checker exact-source child environment changed",
    )
    dictionary_values = cast(ast.Dict, dictionary).values
    require(
        len(dictionary_values) == 7
        and isinstance(dictionary_values[0], ast.Constant)
        and dictionary_values[0].value == "C"
        and isinstance(dictionary_values[1], ast.Constant)
        and dictionary_values[1].value == "C"
        and isinstance(dictionary_values[2], ast.Call)
        and isinstance(dictionary_values[2].func, ast.Name)
        and dictionary_values[2].func.id == "str"
        and len(dictionary_values[2].args) == 1
        and isinstance(dictionary_values[2].args[0], ast.Attribute)
        and dictionary_values[2].args[0].attr == "parent"
        and all(
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "str"
            and len(value.args) == 1
            and isinstance(value.args[0], ast.Name)
            and value.args[0].id == "private_root"
            for value in dictionary_values[3:6]
        )
        and isinstance(dictionary_values[6], ast.Constant)
        and dictionary_values[6].value == "UTC",
        "candidate-checker exact-source child environment changed",
    )
    loops = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "name"
        and isinstance(node.iter, ast.Tuple)
    ]
    retained_names = (
        [
            cast(ast.Constant, element).value
            for element in loops[0].iter.elts
            if isinstance(element, ast.Constant)
        ]
        if len(loops) == 1
        else []
    )
    require(
        retained_names
        == [
            "COMSPEC",
            "HOME",
            "PATHEXT",
            "SystemRoot",
            "SYSTEMROOT",
            "USERPROFILE",
            "WINDIR",
        ]
        and not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "dict"
            and node.args
            and isinstance(node.args[0], ast.Attribute)
            and isinstance(node.args[0].value, ast.Name)
            and node.args[0].value.id == "os"
            and node.args[0].attr == "environ"
            for node in ast.walk(function)
        ),
        "candidate-checker exact-source child environment changed",
    )
    environ_get_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Attribute)
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "os"
        and node.func.value.attr == "environ"
        and node.func.attr == "get"
    ]
    returns = [
        statement
        for statement in function.body
        if isinstance(statement, ast.Return)
    ]
    require(
        len(environ_get_calls) == 1
        and len(environ_get_calls[0].args) == 1
        and isinstance(environ_get_calls[0].args[0], ast.Name)
        and environ_get_calls[0].args[0].id == "name"
        and len(returns) == 1
        and isinstance(returns[0].value, ast.Name)
        and returns[0].value.id == "environment",
        "candidate-checker exact-source child environment changed",
    )


def _require_candidate_checker_preparation_model(tree: ast.Module) -> None:
    main = _source_model_function(tree, "main")
    main_calls = [
        node
        for node in ast.walk(main)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    counts = {
        name: sum(call.func.id == name for call in main_calls)
        for name in (
            "bind_failure_detail_source",
            "freeze_candidate_overlay",
            "frozen_overlay_entry",
        )
    }
    require(
        counts
        == {
            "bind_failure_detail_source": 1,
            "freeze_candidate_overlay": 1,
            "frozen_overlay_entry": 1,
        },
        "candidate facts-to-frozen-overlay preparation inventory changed",
    )
    current_facts_calls = [
        call for call in main_calls if call.func.id == "current_facts"
    ]
    preparation_calls = {
        name: [
            call
            for call in main_calls
            if call.func.id == name
        ]
        for name in (
            "bind_failure_detail_source",
            "clone_candidate",
            "freeze_candidate_overlay",
            "frozen_overlay_entry",
            "static_source_preflight",
        )
    }
    initial_captures = [
        call
        for call in main_calls
        if call.func.id == "stable_regular_file"
        and len(call.args) == 2
        and isinstance(call.args[1], ast.Name)
        and call.args[1].id == "CHECKER_RELATIVE"
    ]
    require(
        len(initial_captures) == 1
        and all(len(calls) == 1 for calls in preparation_calls.values())
        and initial_captures[0].lineno
        < current_facts_calls[0].lineno
        < preparation_calls["freeze_candidate_overlay"][0].lineno
        < preparation_calls["frozen_overlay_entry"][0].lineno
        < current_facts_calls[1].lineno
        < preparation_calls["bind_failure_detail_source"][0].lineno
        < preparation_calls["static_source_preflight"][0].lineno
        < preparation_calls["clone_candidate"][0].lineno,
        "candidate facts-to-frozen-overlay preparation order changed",
    )
    require(
        len(current_facts_calls) == 2
        and len(current_facts_calls[0].keywords) == 1
        and current_facts_calls[0].keywords[0].arg == "source_entry"
        and isinstance(current_facts_calls[0].keywords[0].value, ast.Name)
        and current_facts_calls[0].keywords[0].value.id
        == "initial_checker_entry"
        and len(current_facts_calls[1].keywords) == 1
        and current_facts_calls[1].keywords[0].arg == "source_entry"
        and isinstance(current_facts_calls[1].keywords[0].value, ast.Name)
        and current_facts_calls[1].keywords[0].value.id
        == "overlay_checker_entry",
        "candidate facts source-to-overlay checker replay binding changed",
    )
    required_main_details = {
        "source facts were not emitted by the initial stable checker capture",
        "source facts were not emitted by the frozen overlay checker",
        "frozen overlay checker did not replay the source semantic facts",
    }
    observed_main_details = {
        cast(ast.Constant, call.args[1]).value
        for call in main_calls
        if call.func.id == "require"
        and len(call.args) >= 2
        and isinstance(call.args[1], ast.Constant)
        and call.args[1].value in required_main_details
    }
    require(
        observed_main_details == required_main_details,
        "candidate facts source-to-overlay equality gates changed",
    )
    all_clone_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "clone_candidate"
    ]
    require(
        all_clone_calls
        and all(
            len(call.args) == 4
            and isinstance(call.args[3], ast.Name)
            and call.args[3].id in {"frozen_overlay", "overlay"}
            for call in all_clone_calls
        ),
        "candidate lifecycle clone lost the shared frozen overlay object",
    )
    templates = _source_model_function(tree, "failure_detail_templates")
    require(
        not any(
            isinstance(node, ast.Attribute)
            and node.attr in {"read_text", "read_bytes"}
            and isinstance(node.value, ast.BinOp)
            for node in ast.walk(templates)
        )
        and any(
            isinstance(node, ast.Attribute)
            and node.attr == "raw"
            and isinstance(node.value, ast.Name)
            and node.value.id == "_FAILURE_DETAIL_SOURCE_ENTRY"
            for node in ast.walk(templates)
        ),
        "failure-detail templates are not bound to the frozen checker entry",
    )


def _source_model_string_frozenset(
    tree: ast.Module,
    name: str,
) -> frozenset[str]:
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "frozenset"
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Set)
        and not node.value.keywords
    ]
    if len(assignments) != 1:
        return frozenset()
    values = cast(ast.Set, assignments[0].value.args[0]).elts
    if not all(
        isinstance(value, ast.Constant) and isinstance(value.value, str)
        for value in values
    ):
        return frozenset()
    return frozenset(cast(str, cast(ast.Constant, value).value) for value in values)


def _require_clone_semantic_projection_model(tree: ast.Module) -> None:
    expected_context_keys = frozenset(
        {
            "common_git_dir",
            "git_dir",
            "info_attributes_absent",
            "local_config_semantics_sha256",
            "local_config_sha256",
            "replacement_refs_sha256",
            "worktree_config_absent",
        }
    )
    clone_variant_keys = frozenset(
        {
            "common_git_dir",
            "git_dir",
            "local_config_semantics_sha256",
            "local_config_sha256",
        }
    )
    clone_invariant_keys = frozenset(
        {
            "info_attributes_absent",
            "replacement_refs_sha256",
            "worktree_config_absent",
        }
    )
    observed_constants = (
        _source_model_string_frozenset(tree, "EXPECTED_GIT_CONTEXT_KEYS"),
        _source_model_string_frozenset(
            tree,
            "CLONE_VARIANT_GIT_CONTEXT_KEYS",
        ),
        _source_model_string_frozenset(
            tree,
            "CLONE_INVARIANT_GIT_CONTEXT_KEYS",
        ),
    )

    projection = _source_model_function(tree, "semantic_facts_projection")
    exact_shape_gates = [
        node
        for node in ast.walk(projection)
        if isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Call)
        and isinstance(node.left.func, ast.Name)
        and node.left.func.id == "set"
        and len(node.left.args) == 1
        and isinstance(node.left.args[0], ast.Name)
        and node.left.args[0].id == "git_context"
        and isinstance(node.comparators[0], ast.Name)
        and node.comparators[0].id == "EXPECTED_GIT_CONTEXT_KEYS"
    ]
    normalized_assignments = [
        node
        for node in ast.walk(projection)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "normalized_context"
        and isinstance(node.value, ast.DictComp)
    ]
    normalized = (
        cast(ast.DictComp, normalized_assignments[0].value)
        if len(normalized_assignments) == 1
        else None
    )
    normalized_shape_is_exact = False
    if isinstance(normalized, ast.DictComp) and len(normalized.generators) == 1:
        generator = normalized.generators[0]
        normalized_shape_is_exact = (
            isinstance(normalized.key, ast.Name)
            and normalized.key.id == "key"
            and isinstance(normalized.value, ast.Subscript)
            and isinstance(normalized.value.value, ast.Name)
            and normalized.value.value.id == "git_context"
            and isinstance(normalized.value.slice, ast.Name)
            and normalized.value.slice.id == "key"
            and isinstance(generator.target, ast.Name)
            and generator.target.id == "key"
            and isinstance(generator.iter, ast.Call)
            and isinstance(generator.iter.func, ast.Name)
            and generator.iter.func.id == "sorted"
            and len(generator.iter.args) == 1
            and isinstance(generator.iter.args[0], ast.Name)
            and generator.iter.args[0].id
            == "CLONE_INVARIANT_GIT_CONTEXT_KEYS"
            and not generator.iter.keywords
            and not generator.ifs
            and generator.is_async == 0
        )
    returned_contexts = [
        value
        for node in projection.body
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
        for key, value in zip(node.value.keys, node.value.values, strict=True)
        if isinstance(key, ast.Constant) and key.value == "git_context"
    ]

    control = _source_model_function(tree, "clone_semantic_projection_preflight")
    control_projection_calls = [
        node
        for node in ast.walk(control)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "semantic_facts_projection"
    ]
    invariant_loops = [
        node
        for node in ast.walk(control)
        if isinstance(node, ast.For)
        and isinstance(node.target, ast.Name)
        and node.target.id == "key"
        and isinstance(node.iter, ast.Call)
        and isinstance(node.iter.func, ast.Name)
        and node.iter.func.id == "sorted"
        and len(node.iter.args) == 1
        and isinstance(node.iter.args[0], ast.Name)
        and node.iter.args[0].id == "CLONE_INVARIANT_GIT_CONTEXT_KEYS"
    ]
    control_literals = {
        node.value
        for node in ast.walk(control)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    static_preflight = _source_model_function(tree, "static_source_preflight")
    direct_control_calls = [
        statement.value
        for statement in static_preflight.body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "clone_semantic_projection_preflight"
        and not statement.value.args
        and not statement.value.keywords
    ]

    clone = _source_model_function(tree, "clone_candidate")
    clone_projection_equalities = [
        node
        for node in ast.walk(clone)
        if isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
        and len(node.comparators) == 1
        and isinstance(node.left, ast.Call)
        and isinstance(node.left.func, ast.Name)
        and node.left.func.id == "semantic_facts_projection"
        and len(node.left.args) == 1
        and isinstance(node.left.args[0], ast.Name)
        and node.left.args[0].id == "clone_facts"
        and isinstance(node.comparators[0], ast.Call)
        and isinstance(node.comparators[0].func, ast.Name)
        and node.comparators[0].func.id == "semantic_facts_projection"
        and len(node.comparators[0].args) == 1
        and isinstance(node.comparators[0].args[0], ast.Name)
        and node.comparators[0].args[0].id == "facts"
    ]

    require(
        observed_constants
        == (
            expected_context_keys,
            clone_variant_keys,
            clone_invariant_keys,
        )
        and clone_variant_keys.isdisjoint(clone_invariant_keys)
        and clone_variant_keys | clone_invariant_keys == expected_context_keys
        and len(exact_shape_gates) == 1
        and normalized_shape_is_exact
        and len(returned_contexts) == 1
        and isinstance(returned_contexts[0], ast.Name)
        and returned_contexts[0].id == "normalized_context"
        and len(control_projection_calls) == 4
        and len(invariant_loops) == 1
        and {
            "clone semantic projection retained a clone-variant Git context field",
            "clone semantic projection accepted a ",
            "clone semantic projection discarded invariant Git context field: ",
            "diagnostic phase facts Git context has an unexpected exact shape",
            "git_dir",
            "unexpected_context_field",
        }.issubset(control_literals)
        and len(direct_control_calls) == 1
        and len(clone_projection_equalities) == 1,
        "clone semantic facts projection source model changed",
    )


def _require_exact_loader_subcontrol_model(tree: ast.Module) -> None:
    require(
        _source_model_constant(
            tree,
            "EXACT_CANDIDATE_LOADER_SUBCONTROL_COUNT",
        )
        == 8,
        "exact candidate-loader uncounted nested subcontrol constant changed",
    )
    require(
        _source_model_constant(tree, "FROZEN_MODE_SUBCONTROL_RELATIVE")
        == "scripts/check-lean-descriptor-factorization.py",
        "frozen-overlay executable-mode subcontrol path changed",
    )
    controls = _source_model_function(
        tree,
        "run_exact_candidate_loader_subcontrols",
    )
    static_assignments = [
        node
        for node in ast.walk(controls)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "static_controls"
        and isinstance(node.value, ast.Tuple)
    ]
    increments = [
        node
        for node in ast.walk(controls)
        if isinstance(node, ast.AugAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "subcontrols"
        and isinstance(node.op, ast.Add)
        and isinstance(node.value, ast.Constant)
        and node.value.value == 1
    ]
    require(
        len(static_assignments) == 1
        and len(cast(ast.Tuple, static_assignments[0].value).elts) == 6
        and len(increments) == 3,
        "exact candidate-loader uncounted nested subcontrol inventory changed",
    )
    owner = _source_model_function(tree, "run_checker_model_attacks")
    owner_calls = [
        node
        for node in ast.walk(owner)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_exact_candidate_loader_subcontrols"
    ]
    require(
        len(owner_calls) == 1
        and any(
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == "exact_candidate_loader_subcontrols"
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.Eq)
            and len(node.comparators) == 1
            and isinstance(node.comparators[0], ast.Constant)
            and node.comparators[0].value == 8
            for node in ast.walk(owner)
        )
        and not any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "attacks"
            and isinstance(node.value, ast.Name)
            and node.value.id == "exact_candidate_loader_subcontrols"
            for node in ast.walk(owner)
        ),
        "exact candidate-loader subcontrols entered the hostile family count",
    )


def _require_candidate_checker_self_test_model(tree: ast.Module) -> None:
    _require_candidate_checker_bootstrap(tree)
    _require_candidate_checker_bootstrap_ast(tree)
    _require_candidate_checker_invocation_model(tree)
    _require_exact_checker_environment_model(tree)
    _require_frozen_overlay_source_model(tree)
    _require_candidate_checker_call_integration(tree)
    _require_candidate_checker_preparation_model(tree)
    _require_clone_semantic_projection_model(tree)
    _require_exact_loader_subcontrol_model(tree)


def validate_python_entry_isolation() -> None:
    """Bind safe startup, child propagation, and every official C3 invocation."""

    trees: dict[str, ast.Module] = {}
    for relative in C3_PYTHON_ENTRYPOINTS:
        raw = read_candidate_bytes(relative)
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise PhaseIsolationError(
                f"isolated Python entry point is not UTF-8: {relative}"
            ) from error
        trees[relative] = _validate_isolated_entry_ast(
            source,
            relative=relative,
            expected_preamble=_expected_isolated_entry_preamble(
                PurePosixPath(relative).name
            ),
        )

    _require_exact_child_python_command(
        trees["scripts/check-ksg-phase-isolation.py"],
        relative="scripts/check-ksg-phase-isolation.py",
        function_name="run_lean_portability_parser",
    )
    _require_exact_stdin_child_model(
        trees["scripts/check-ksg-phase-isolation.py"],
    )
    _require_exact_child_python_command(
        trees["scripts/check-ksg-phase-isolation-self-test.py"],
        relative="scripts/check-ksg-phase-isolation-self-test.py",
        function_name="python_command",
    )
    _require_candidate_checker_self_test_model(
        trees["scripts/check-ksg-phase-isolation-self-test.py"],
    )

    official_fragments = {
        ".github/workflows/ci.yml": (
            b"          python3 -I -S scripts/check-ksg-phase-isolation.py \\\n",
            b"          python3 -I -S -O scripts/check-ksg-phase-isolation.py \\\n",
            b"          python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            b"          python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
        ),
        "AGENTS.md": (
            b"python3 -I -S scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody  # NO-CREDIT local replay\n",
            b"python3 -I -S -O scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            b"python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            b"python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
        ),
        "justfile": (
            b"    python3 -I -S scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            b"    python3 -I -S -O scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            b"    python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            b"    python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
        ),
        "scripts/check-foundational-sxpid-audit-pdf.sh": (
            b'python3 -I -S "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \\\n',
            b'python3 -I -S "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
            b'python3 -I -S "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"\n',
        ),
        "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md": (
            b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py \\\n",
            b"python3 -I -S scripts/check-lean-descriptor-factorization.py\n",
            b"python3 -I -S scripts/check-lean-descriptor-factorization-self-test.py\n",
        ),
        "audit/tools/foundational_sxpid/README.md": (
            b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py\n",
        ),
        "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex": (
            b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py \\\n",
            b"python3 -I -S scripts/check-lean-descriptor-factorization.py\n",
            b"python3 -I -S scripts/check-lean-descriptor-factorization-self-test.py\n",
        ),
    }
    for relative, fragments in official_fragments.items():
        raw = read_candidate_bytes(relative)
        for fragment in fragments:
            require(
                raw.count(fragment) == 1,
                f"official isolated Python invocation changed: {relative}",
            )

    finite_text_transforms = {
        ".github/workflows/ci.yml": (
            (
                (
                    b"  ksg-harmonic-assurance:\n"
                    b"    name: KSG integer-harmonic arithmetic and phase isolation\n"
                    b"    runs-on: ubuntu-latest\n"
                    b"    timeout-minutes: 45\n"
                ),
                (
                    b"  ksg-harmonic-assurance:\n"
                    b"    name: KSG integer-harmonic arithmetic and phase isolation\n"
                    b"    runs-on: ubuntu-latest\n"
                    b"    # The normal and optimized 351-case custody suites run sequentially and\n"
                    b"    # intentionally create isolated Git histories for every hostile family.\n"
                    b"    timeout-minutes: 240\n"
                ),
            ),
            (
                b"          python3 scripts/check-ksg-phase-isolation.py \\\n",
                b"          python3 -I -S scripts/check-ksg-phase-isolation.py \\\n",
            ),
            (
                b"          python3 -O scripts/check-ksg-phase-isolation.py \\\n",
                b"          python3 -I -S -O scripts/check-ksg-phase-isolation.py \\\n",
            ),
            (
                b"          python3 scripts/check-ksg-phase-isolation-self-test.py\n",
                b"          python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            ),
            (
                b"          python3 -O scripts/check-ksg-phase-isolation-self-test.py\n",
                b"          python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
            ),
        ),
        "AGENTS.md": (
            (
                b"python3 scripts/check-ksg-phase-isolation.py             # exact KSG-only Git phase envelope\n",
                b"python3 -I -S scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody  # NO-CREDIT local replay\n",
            ),
            (
                b"python3 -O scripts/check-ksg-phase-isolation.py\n",
                b"python3 -I -S -O scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            ),
            (
                b"python3 scripts/check-ksg-phase-isolation-self-test.py\n",
                b"python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            ),
            (
                b"python3 -O scripts/check-ksg-phase-isolation-self-test.py\n",
                b"python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
            ),
        ),
        "justfile": (
            (
                b"    python3 scripts/check-ksg-phase-isolation.py\n",
                b"    python3 -I -S scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            ),
            (
                b"    python3 -O scripts/check-ksg-phase-isolation.py\n",
                b"    python3 -I -S -O scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            ),
            (
                b"    python3 scripts/check-ksg-phase-isolation-self-test.py\n",
                b"    python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            ),
            (
                b"    python3 -O scripts/check-ksg-phase-isolation-self-test.py\n",
                b"    python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py\n",
            ),
        ),
        "scripts/check-foundational-sxpid-audit-pdf.sh": (
            (
                b'python3 "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \\\n',
                b'python3 -I -S "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \\\n',
            ),
            (
                b'python3 "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
                b'python3 -I -S "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
            ),
            (
                b'python3 "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"\n',
                b'python3 -I -S "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"\n',
            ),
        ),
        "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md": (
            (
                b"python3 audit/tools/foundational_sxpid/check_lcr_relation_witness.py \\\n",
                b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py \\\n",
            ),
            (
                b"python3 scripts/check-lean-descriptor-factorization.py\n",
                b"python3 -I -S scripts/check-lean-descriptor-factorization.py\n",
            ),
            (
                b"python3 scripts/check-lean-descriptor-factorization-self-test.py\n",
                b"python3 -I -S scripts/check-lean-descriptor-factorization-self-test.py\n",
            ),
        ),
        "audit/tools/foundational_sxpid/README.md": (
            (
                b"python3 audit/tools/foundational_sxpid/check_lcr_relation_witness.py\n",
                b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py\n",
            ),
        ),
        "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex": (
            (
                b"python3 audit/tools/foundational_sxpid/check_lcr_relation_witness.py \\\n",
                b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py \\\n",
            ),
            (
                b"python3 scripts/check-lean-descriptor-factorization.py\n",
                b"python3 -I -S scripts/check-lean-descriptor-factorization.py\n",
            ),
            (
                b"python3 scripts/check-lean-descriptor-factorization-self-test.py\n",
                b"python3 -I -S scripts/check-lean-descriptor-factorization-self-test.py\n",
            ),
            (
                (
                    b"The generic firewall is kernel-checked in\n"
                    b"\\path{audit/formal/lean-foundational-sxpid/"
                    b"PidDescriptorFactorization.lean}.\n"
                ),
                (
                    b"The generic firewall is kernel-checked in\n"
                    b"\\path{audit/formal/lean-foundational-sxpid/}\\newline\n"
                    b"\\mbox{\\path{PidDescriptorFactorization.lean}}.\n"
                ),
            ),
            (
                (
                    b"countermodels.  Their deterministic outputs are\n"
                    b"\\path{audit/evidence/foundational-sxpid-descriptor-"
                    b"factorization-lean.json} and\n"
                    b"\\path{audit/evidence/foundational-sxpid-descriptor-"
                    b"factorization-mutations.json}.\n"
                ),
                (
                    b"countermodels.  Their deterministic outputs are\n"
                    b"{\\small\\path{audit/evidence/foundational-sxpid-"
                    b"descriptor-factorization-lean.json}} and\n"
                    b"{\\small\\path{audit/evidence/foundational-sxpid-"
                    b"descriptor-factorization-mutations.json}}.\n"
                ),
            ),
            (
                (
                    b"The standard-library checker\n"
                    b"\\path{audit/tools/foundational_sxpid/"
                    b"check_lcr_relation_witness.py}\n"
                    b"does not import \\texttt{pid-rs}.  It:\n"
                ),
                (
                    b"The standard-library checker\n"
                    b"\\path{audit/tools/foundational_sxpid/"
                    b"check_lcr_relation_}\\newline\n"
                    b"\\mbox{\\path{witness.py}}\n"
                    b"does not import \\texttt{pid-rs}.  It:\n"
                ),
            ),
            (
                (
                    b"At generation, the bound SHA-256 values were:\n"
                    b"\\begin{itemize}\n"
                ),
                (
                    b"At generation, the bound SHA-256 values were:\n"
                    b"\\begin{itemize}\n"
                    b"\\small\n"
                ),
            ),
            (
                (
                    b"\\section*{Primary sources}\n"
                    b"\\addcontentsline{toc}{section}{Primary sources}\n"
                ),
                (
                    b"\\phantomsection\n"
                    b"\\section*{Primary sources}\n"
                    b"\\addcontentsline{toc}{section}{Primary sources}\n"
                ),
            ),
        ),
    }
    for relative, replacements in finite_text_transforms.items():
        expected = git_blob_at(C2_TOOLING_CORRECTION, relative)
        for index, (before, after) in enumerate(replacements):
            expected = replace_unique_workflow_fragment(
                expected,
                before,
                after,
                label=f"{relative} isolated invocation {index}",
            )
        if relative == "scripts/check-foundational-sxpid-audit-pdf.sh":
            require(
                hashlib.sha256(read_candidate_bytes(relative)).hexdigest()
                == EXPECTED_FOUNDATIONAL_C3_WRAPPER_SHA256,
                "foundational-paper checker differs from the exact lake-preflight transform",
            )
            continue
        require(
            read_candidate_bytes(relative) == expected,
            f"authorized text path differs outside finite C2 transform: {relative}",
        )

    certified_checker = "scripts/check-certified-sxpid2-claim.py"
    expected_checker = git_blob_at(C2_TOOLING_CORRECTION, certified_checker)
    for before, after, label in (
        (
            b"5bca9f1af50b2441e6c3363c372f47097441d783702ce858e0b8f03b964eb357",
            hashlib.sha256(read_candidate_bytes(".github/workflows/ci.yml"))
            .hexdigest()
            .encode("ascii"),
            "certified checker workflow-container digest",
        ),
        (
            b"8dc0c452b1b95a080e93091fd4c18d32864daed903c415bf422f366c4edb91b2",
            hashlib.sha256(read_candidate_bytes("justfile"))
            .hexdigest()
            .encode("ascii"),
            "certified checker just-container digest",
        ),
    ):
        expected_checker = replace_unique_workflow_fragment(
            expected_checker,
            before,
            after,
            label=label,
        )
    require(
        read_candidate_bytes(certified_checker) == expected_checker,
        "certified checker changed outside its two exact container-digest rebinds",
    )


def validate_foundational_pdf_lake_preflight() -> None:
    relative = "scripts/check-foundational-sxpid-audit-pdf.sh"
    expected = git_blob_at(CORRECTIVE_PARENT, relative)
    expected = replace_unique_workflow_fragment(
        expected,
        (
            b"commands=(latexmk cmp pdffonts pdfinfo pdftotext pdftoppm "
            b"chktex lacheck python3)\n"
        ),
        (
            b"commands=(latexmk cmp pdffonts pdfinfo pdftotext pdftoppm "
            b"chktex lacheck lake python3)\n"
        ),
        label="foundational PDF lake preflight",
    )
    for before, after, label in (
        (
            b'python3 "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \\\n',
            b'python3 -I -S "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \\\n',
            "exact-rational evidence safe startup",
        ),
        (
            b'python3 "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
            b'python3 -I -S "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
            "Lean evidence safe startup",
        ),
        (
            b'python3 "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"\n',
            b'python3 -I -S "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"\n',
            "Lean mutation evidence safe startup",
        ),
    ):
        expected = replace_unique_workflow_fragment(
            expected,
            before,
            after,
            label=label,
        )

    candidate = read_candidate_bytes(relative)
    require(
        hashlib.sha256(candidate).hexdigest()
        == EXPECTED_FOUNDATIONAL_C3_WRAPPER_SHA256,
        "foundational-paper checker differs from the exact lake-preflight transform",
    )
    candidate_without_navigation = replace_unique_workflow_fragment(
        candidate,
        (
            b'TOC="$BUILD_DIR/foundational-shared-exclusions-pid-audit.toc"\n'
            b'OUT="$BUILD_DIR/foundational-shared-exclusions-pid-audit.out"\n'
        ),
        b"",
        label="foundational PDF navigation auxiliary declarations",
    )
    navigation_begin = (
        b'python3 -I -S - "$SOURCE" "$TOC" "$OUT" "$BUILT" '
        b'"$ROOT/$COMMITTED" <<\'PY\'\n'
    )
    navigation_end = b'PY\n\npdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"\n'
    require(
        candidate_without_navigation.count(navigation_begin) == 1
        and candidate_without_navigation.count(navigation_end) == 1,
        "foundational-paper checker navigation gate is not uniquely delimited",
    )
    begin_index = candidate_without_navigation.index(navigation_begin)
    end_index = candidate_without_navigation.index(
        navigation_end,
        begin_index + len(navigation_begin),
    )
    candidate_without_navigation = (
        candidate_without_navigation[:begin_index]
        + b'pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"\n'
        + candidate_without_navigation[end_index + len(navigation_end) :]
    )
    require(
        candidate_without_navigation == expected,
        "foundational-paper checker differs from the exact lake-preflight transform",
    )


def validate_package_archive_corrective_firewall() -> None:
    stats_path = "crates/pid-core/src/stats.rs"
    archive_script_path = "scripts/verify-package-archives.sh"
    snapshot_path = (
        "crates/pid-core/tests/fixtures/"
        "generate-ksg-local-arithmetic-oracle.py.snapshot"
    )
    generator_path = "scripts/generate-ksg-local-arithmetic-oracle.py"
    stats = read_candidate_bytes(stats_path)
    snapshot = read_candidate_bytes(snapshot_path)
    canonical_generator = git_blob_at(CURRENT_ANCHOR, generator_path)
    require(
        hashlib.sha256(stats).hexdigest() == PACKAGE_STATS_SHA256,
        "package corrective stats.rs differs from its manually reviewed full blob",
    )
    require(
        hashlib.sha256(canonical_generator).hexdigest()
        == PACKAGE_GENERATOR_SHA256,
        "af509 canonical KSG generator differs from its reviewed digest",
    )
    require(
        read_candidate_bytes(generator_path) == canonical_generator,
        "canonical KSG generator changed in the corrective phase",
    )
    require(
        snapshot == canonical_generator,
        "packaged KSG generator snapshot differs from the exact af509 source bytes",
    )
    archive_script = read_candidate_bytes(archive_script_path)
    require(
        hashlib.sha256(archive_script).hexdigest()
        == PACKAGE_ARCHIVE_SCRIPT_SHA256,
        "package archive verifier differs from its manually reviewed full blob",
    )
    try:
        archive_script_text = archive_script.decode("utf-8")
        stats_text = stats.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(
            "package corrective source is not UTF-8"
        ) from error
    for token, expected_count, label in (
        (
            "packaged_ksg_generator_snapshot_matches_workspace_source_when_available",
            1,
            "exact extracted-package test name",
        ),
        ("--exact", 1, "exact libtest filter"),
        ("--color never", 1, "deterministic libtest color"),
        ("running 1 test", 1, "one-test receipt"),
        ("test $archive_test_name ... ok", 1, "named-test receipt"),
        (
            "^test result: ok\\. 1 passed; 0 failed; 0 ignored; "
            "0 measured; [0-9]+ filtered out; finished in .+s$",
            1,
            "exact one-pass summary parser",
        ),
        ("absent-workspace branch", 1, "absent-generator precondition"),
    ):
        require(
            archive_script_text.count(token) == expected_count,
            f"package archive verifier changed {label}",
        )
    for token, label in (
        ("struct CargoPackageContext", "typed package-context marker"),
        (
            "cargo_package_context_rejects_duplicate_path_bindings",
            "duplicate package-context binding control",
        ),
        (
            "serde_json::from_slice::<CargoPackageContext>(ambiguous).is_err()",
            "duplicate marker rejection",
        ),
    ):
        require(
            stats_text.count(token) == 1,
            f"package stats corrective changed {label}",
        )


def validate_ecosystem_corrective_firewall() -> None:
    catalog_digest = hashlib.sha256(
        read_candidate_bytes("method-catalog.json")
    ).hexdigest()
    require(
        catalog_digest == CURRENT_METHOD_CATALOG_SHA256,
        "current method catalog differs from the manually reviewed corrective digest",
    )
    old = HISTORICAL_ECOSYSTEM_METHOD_CATALOG_SHA256.encode("ascii")
    new = CURRENT_METHOD_CATALOG_SHA256.encode("ascii")
    for relative in (
        "ECOSYSTEM_CAPABILITIES.md",
        "ecosystem-capabilities.json",
        "scripts/check-ecosystem-capabilities.py",
    ):
        historical = git_blob_at(M1A_SCIENTIFIC_COMMIT, relative)
        require(
            historical.count(old) == 1 and new not in historical,
            f"{relative}@dc7 lacks the unique historical catalog binding",
        )
        expected = historical.replace(old, new, 1)
        corrective_parent = git_blob_at(CORRECTIVE_PARENT, relative)
        require(
            corrective_parent == expected,
            f"{relative}@af509 differs from the exact one-digest dc7 transform",
        )
        require(
            read_candidate_bytes(relative) == corrective_parent,
            f"{relative} changed after the exact af509 ecosystem transform",
        )


def sanitize_rust(source: str) -> str:
    output = list(source)
    length = len(source)
    cursor = 0

    def blank(start: int, end: int) -> None:
        for index in range(start, end):
            if output[index] != "\n":
                output[index] = " "

    while cursor < length:
        if source.startswith("//", cursor):
            end = source.find("\n", cursor + 2)
            end = length if end < 0 else end
            blank(cursor, end)
            cursor = end
            continue
        if source.startswith("/*", cursor):
            start = cursor
            depth = 1
            cursor += 2
            while cursor < length and depth:
                if source.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif source.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            require(depth == 0, "Rust source contains an unterminated block comment")
            blank(start, cursor)
            continue
        raw_match = re.match(r'(?:br|r)(#{0,255})"', source[cursor:])
        if raw_match is not None:
            start = cursor
            hashes = raw_match.group(1)
            cursor += raw_match.end()
            terminator = '"' + hashes
            end = source.find(terminator, cursor)
            require(end >= 0, "Rust source contains an unterminated raw string")
            cursor = end + len(terminator)
            blank(start, cursor)
            continue
        if source[cursor] == '"' or source.startswith('b"', cursor):
            start = cursor
            if source[cursor] == "b":
                cursor += 1
            cursor += 1
            escaped = False
            while cursor < length:
                character = source[cursor]
                cursor += 1
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    break
            else:
                raise PhaseIsolationError("Rust source contains an unterminated string")
            blank(start, cursor)
            continue
        cursor += 1
    return "".join(output)


def validate_parallel_semantics() -> None:
    relative = "crates/pid-core/tests/parallel_bit_identity.rs"
    raw = read_candidate_bytes(relative)
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{relative}: non-UTF-8 Rust source") from error
    expected_gate = '#![cfg(feature = "experimental-pipelines")]'
    require(
        source.startswith(expected_gate + "\n\n"),
        "parallel bit-identity test has a zero-test-capable crate gate",
    )
    require(
        '#![cfg(all(feature = "experimental-pipelines", feature = "parallel"))]'
        not in source,
        "parallel bit-identity test restored the false-zero serial gate",
    )
    sanitized = sanitize_rust(source)
    conditional_attributes = tuple(
        re.findall(
            r"#\s*(!?)\s*\[\s*(cfg(?:_attr)?|ignore)\b",
            sanitized,
        )
    )
    require(
        conditional_attributes == (("!", "cfg"),),
        "parallel bit-identity conditional/ignore attribute inventory changed",
    )
    require(
        not re.search(r"\bcfg\s*!\s*\(", sanitized),
        "parallel bit-identity target contains a runtime cfg! gate",
    )
    require(
        not re.search(r"\breturn\b", sanitized),
        "parallel bit-identity target contains an early-return bypass",
    )

    observed_constants: dict[str, list[int]] = {}
    for match in re.finditer(
        r"(?m)^\s*const\s+([A-Z][A-Z0-9_]*)\s*:\s*u64\s*=\s*([0-9_]+)\s*;",
        sanitized,
    ):
        observed_constants.setdefault(match.group(1), []).append(
            int(match.group(2).replace("_", ""))
        )
    for name, expected in EXPECTED_PARALLEL_U64_CONSTANTS.items():
        require(
            observed_constants.get(name) == [expected],
            f"parallel bit-identity constant {name} is not the unique KSG-only value",
        )
    require(
        observed_constants.get("PID2_SYN_BITS") != [FORBIDDEN_PID2_SYN_BITS],
        "later PID2 represented-sum synergy bits contaminated the KSG phase",
    )

    tests = tuple(
        sorted(
            re.findall(
                r"(?m)^\s*#\s*\[\s*test\s*\]\s*\n\s*fn\s+"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                sanitized,
            )
        )
    )
    require(
        tests == EXPECTED_PARALLEL_TESTS,
        "parallel bit-identity test inventory no longer proves 12 nonzero serial tests",
    )


def validate_stats_firewall() -> None:
    relative = "crates/pid-core/src/stats.rs"
    try:
        source = read_candidate_bytes(relative).decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError(f"{relative}: non-UTF-8 Rust source") from error
    sanitized = sanitize_rust(source)
    for token in (
        "FINITE_SUM_LIMBS",
        "exact_binary64_sum",
        "round_finite_sum",
    ):
        require(
            not re.search(rf"\b{re.escape(token)}\b", sanitized),
            f"stats.rs contains forbidden later-wave exact-sum token {token}",
        )


def validate_release_firewall() -> None:
    relative = "release-scope-1.0.json"
    raw = read_candidate_bytes(relative)
    scope = canonical_json_from_bytes(raw, label=relative)
    require(isinstance(scope, dict), "release scope root must be an object")
    families = scope.get("families")
    require(
        isinstance(families, list) and len(families) == 35,
        "release scope must retain exactly 35 family objects",
    )
    by_id: dict[str, dict[str, Any]] = {}
    revisions: list[str] = []
    for index, family in enumerate(families):
        require(isinstance(family, dict), f"release family {index} must be an object")
        family_id = family.get("id")
        revision = family.get("estimator_revision")
        require(
            isinstance(family_id, str)
            and family_id
            and family_id not in by_id
            and isinstance(revision, str)
            and revision,
            f"release family {index} has invalid typed identity/revision",
        )
        by_id[family_id] = family
        revisions.append(revision)
    for family_id, expected in EXPECTED_RELEASE_REVISIONS.items():
        require(family_id in by_id, f"release family {family_id!r} is missing")
        require(
            by_id[family_id]["estimator_revision"] == expected,
            f"release family {family_id!r} is not at the KSG-only bridge revision",
        )
    for revision in revisions:
        lower = revision.lower()
        require(
            revision not in FORBIDDEN_COMBINED_RELEASE_REVISIONS
            and "represented-input" not in lower
            and "represented_input" not in lower
            and "exact-synergy-sum" not in lower,
            f"release scope contains later combined revision {revision!r}",
        )

    markdown = read_candidate_bytes("RELEASE_SCOPE_1_0.md")
    try:
        markdown_text = markdown.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PhaseIsolationError("RELEASE_SCOPE_1_0.md is not UTF-8") from error
    for forbidden in FORBIDDEN_COMBINED_RELEASE_REVISIONS:
        require(
            forbidden not in markdown_text,
            "rendered release scope contains a later combined revision",
        )
    for expected in EXPECTED_RELEASE_REVISIONS.values():
        require(
            markdown_text.count(expected) == 1,
            f"rendered release scope does not uniquely contain {expected!r}",
        )


def validate_identity_firewall() -> None:
    relative = "crates/pid-core/identity/software-identity-reference-v1.json"
    candidate = canonical_json_from_bytes(
        read_candidate_bytes(relative), label=relative
    )
    baseline = canonical_json_from_bytes(
        git_blob_at(SCIENTIFIC_BASELINE, relative),
        label=f"{relative}@scientific-baseline",
    )
    require(
        isinstance(candidate, dict) and isinstance(baseline, dict),
        "software identity roots must be objects",
    )
    candidate_artifacts = candidate.get("reference_artifacts")
    baseline_artifacts = baseline.get("reference_artifacts")
    require(
        isinstance(candidate_artifacts, list)
        and isinstance(baseline_artifacts, list)
        and len(candidate_artifacts) == len(baseline_artifacts) == 2,
        "software identity must retain exactly two reference artifacts",
    )
    normalized = json.loads(json.dumps(candidate))
    expected_digests = {
        "method_catalog": hashlib.sha256(
            read_candidate_bytes("method-catalog.json")
        ).hexdigest(),
        "proposed_release_scope": hashlib.sha256(
            read_candidate_bytes("release-scope-1.0.json")
        ).hexdigest(),
    }
    for index, (actual, historical) in enumerate(
        zip(candidate_artifacts, baseline_artifacts, strict=True)
    ):
        require(
            isinstance(actual, dict) and isinstance(historical, dict),
            f"software identity artifact {index} must be an object",
        )
        kind = actual.get("kind")
        require(
            isinstance(kind, str) and kind in expected_digests,
            f"software identity artifact {index} has an unauthorized kind",
        )
        require(
            actual.get("canonical_json_sha256") == expected_digests[kind],
            f"software identity artifact {kind!r} does not bind current canonical bytes",
        )
        normalized["reference_artifacts"][index]["canonical_json_sha256"] = (
            historical.get("canonical_json_sha256")
        )
    require(
        normalized == baseline,
        "software identity changed outside the two authorized forensic digests",
    )


def validate_changed_path_firewall(paths: Iterable[str]) -> None:
    for path in paths:
        lower = path.lower()
        require(
            path not in FORBIDDEN_EXACT_CHANGED_PATHS,
            f"forbidden later-wave path entered KSG phase: {path}",
        )
        require(
            not any(
                path.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PATH_PREFIXES
            ),
            f"forbidden later-wave path prefix entered KSG phase: {path}",
        )
        require(
            not any(fragment in lower for fragment in FORBIDDEN_CHANGED_PATH_FRAGMENTS),
            f"forbidden later-wave path token entered KSG phase: {path}",
        )
        if lower.endswith((".pdf", ".tex")):
            require(
                path in CORRECTIVE_PUBLICATION_PATHS,
                f"unrelated PDF/TeX path entered KSG phase: {path}",
            )
        if path.startswith("audit/formal/"):
            require(
                path.startswith("audit/formal/lean-ksg-harmonic/")
                or path.startswith("audit/formal/z3-ksg-harmonic/")
                or path in CORRECTIVE_PUBLICATION_PATHS,
                f"unrelated formal path entered KSG phase: {path}",
            )


def validate_checker_source_model() -> None:
    try:
        logical_raw = SCRIPT_PATH.read_bytes()
        if _EXACT_SOURCE_BYTES is not None:
            require(
                logical_raw == _EXACT_SOURCE_BYTES,
                "logical phase-checker path bytes differ from captured stdin source",
            )
        source = logical_raw.decode("utf-8", errors="strict")
        tree = ast.parse(source, filename=str(SCRIPT_PATH))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise PhaseIsolationError(
            f"cannot inspect checker source model: {error}"
        ) from error
    assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    require(
        not assert_nodes,
        "checker source contains an optimization-removable assert statement",
    )
    marker_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "_EXACT_SOURCE_BYTES"
    ]
    marker_value = (
        marker_assignments[0].value if len(marker_assignments) == 1 else None
    )
    exact_source_require_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value
        == "logical phase-checker path bytes differ from captured stdin source"
    ]
    require(
        isinstance(marker_value, ast.Call)
        and isinstance(marker_value.func, ast.Attribute)
        and isinstance(marker_value.func.value, ast.Call)
        and isinstance(marker_value.func.value.func, ast.Name)
        and marker_value.func.value.func.id == "globals"
        and not marker_value.func.value.args
        and not marker_value.func.value.keywords
        and marker_value.func.attr == "pop"
        and len(marker_value.args) == 2
        and isinstance(marker_value.args[0], ast.Constant)
        and marker_value.args[0].value == "__pid_rs_exact_source_bytes__"
        and isinstance(marker_value.args[1], ast.Constant)
        and marker_value.args[1].value is None
        and len(exact_source_require_calls) == 1
        and isinstance(exact_source_require_calls[0].args[0], ast.Compare)
        and isinstance(exact_source_require_calls[0].args[0].left, ast.Name)
        and exact_source_require_calls[0].args[0].left.id == "logical_raw"
        and len(exact_source_require_calls[0].args[0].comparators) == 1
        and isinstance(
            exact_source_require_calls[0].args[0].comparators[0],
            ast.Name,
        )
        and exact_source_require_calls[0].args[0].comparators[0].id
        == "_EXACT_SOURCE_BYTES",
        "phase-checker optional exact-source marker model changed",
    )
    for fragment in (
        "normal_raw = run_lean_portability_parser(optimized=False)",
        "optimized_raw = run_lean_portability_parser(optimized=True)",
        "normal_raw == optimized_raw",
        'command.append("-O")',
    ):
        require(
            source.count(fragment) == 2,
            f"Lean portability parser replay source model changed: {fragment}",
        )
    commit_policy_definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "validate_unsigned_attribution_free_commit"
    ]
    commit_policy_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "validate_unsigned_attribution_free_commit"
    ]
    require(
        len(commit_policy_definitions) == 1
        and len(commit_policy_calls) == 2
        and all(
            any(
                keyword.arg == "require_exact_c3_identity_and_message"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in call.keywords
            )
            for call in commit_policy_calls
        ),
        "unsigned/attribution-free commit metadata gate inventory changed",
    )
    staged_custody_definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "validate_staged_tree_custody"
    ]
    whitespace_diff_calls = [
        node
        for node in ast.walk(staged_custody_definitions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "git_process"
        and any(
            isinstance(argument, ast.Constant)
            and argument.value == "diff-tree"
            for argument in node.args
        )
    ] if len(staged_custody_definitions) == 1 else []
    whitespace_call_shape_is_exact = False
    if len(whitespace_diff_calls) == 1:
        whitespace_call = whitespace_diff_calls[0]
        whitespace_call_shape_is_exact = (
            len(whitespace_call.args) == 13
            and all(
                isinstance(argument, ast.Constant)
                for argument in (
                    *whitespace_call.args[:10],
                    whitespace_call.args[12],
                )
            )
            and tuple(
                cast(ast.Constant, argument).value
                for argument in whitespace_call.args[:10]
            )
            == (
                "-c",
                "advice.graftFileDeprecated=false",
                "-c",
                "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab",
                "diff-tree",
                "-r",
                "--check",
                "--no-ext-diff",
                "--no-renames",
                "--no-textconv",
            )
            and cast(ast.Constant, whitespace_call.args[12]).value == "--"
            and isinstance(whitespace_call.args[10], ast.Name)
            and whitespace_call.args[10].id == "CURRENT_ANCHOR"
            and isinstance(whitespace_call.args[11], ast.Name)
            and whitespace_call.args[11].id == "expected_tree"
            and len(whitespace_call.keywords) == 1
            and whitespace_call.keywords[0].arg == "check"
            and isinstance(whitespace_call.keywords[0].value, ast.Constant)
            and whitespace_call.keywords[0].value.value is False
        )
    require(
        len(staged_custody_definitions) == 1
        and len(whitespace_diff_calls) == 1
        and whitespace_call_shape_is_exact,
        "external candidate-tree whitespace gate inventory changed",
    )
    require(
        tuple(sorted(EXPECTED_CHANGED_PATHS)) == EXPECTED_CHANGED_PATHS
        and len(EXPECTED_CHANGED_PATHS) == len(set(EXPECTED_CHANGED_PATHS)),
        "generated changed-path allowlist is not sorted and duplicate-free",
    )
    require(
        MAX_POST_ANCHOR_COMMITS == 1,
        "post-anchor commit bound is not exactly one direct child",
    )
    require(
        tuple(sorted(BOUND_ALLOWED_PATHS)) == BOUND_ALLOWED_PATHS
        and len(BOUND_ALLOWED_PATHS) == len(set(BOUND_ALLOWED_PATHS)),
        "reviewed full-blob path inventory is not sorted and duplicate-free",
    )
    require(
        SELF_UNHASHED_PATHS
        == frozenset(
            {
                "scripts/check-ksg-phase-isolation-self-test.py",
                "scripts/check-ksg-phase-isolation.py",
            }
        ),
        "cyclic self-unhashed inventory changed",
    )
    phase_functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "validate_phase"
    ]
    require(
        len(phase_functions) == 1, "checker does not uniquely define validate_phase"
    )
    critical_names = set(EXPECTED_CRITICAL_GATE_SEQUENCE)

    def direct_statement_call(statement: ast.stmt) -> str | None:
        value: ast.expr | None = None
        if isinstance(statement, ast.Expr):
            value = statement.value
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in critical_names
        ):
            return value.func.id
        return None

    observed_direct = tuple(
        name
        for statement in phase_functions[0].body
        if (name := direct_statement_call(statement)) is not None
    )
    require(
        observed_direct == EXPECTED_CRITICAL_GATE_SEQUENCE,
        "checker direct top-level critical gate sequence changed",
    )
    observed_recursive = [
        node.func.id
        for node in ast.walk(phase_functions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in critical_names
    ]
    for critical in critical_names:
        require(
            observed_recursive.count(critical)
            == EXPECTED_CRITICAL_GATE_SEQUENCE.count(critical),
            f"checker recursive critical gate inventory changed: {critical}",
        )


def validate_effective_attributes(paths: Iterable[str]) -> None:
    ordered = tuple(sorted(paths))
    if not ordered:
        return
    payload = b"".join(path.encode("utf-8") + b"\0" for path in ordered)
    process = git_process(
        "check-attr",
        "-z",
        "--stdin",
        "filter",
        "working-tree-encoding",
        input_bytes=payload,
    )
    fields = process.stdout.split(b"\0")
    if fields and not fields[-1]:
        fields.pop()
    require(
        len(fields) == len(ordered) * 2 * 3,
        "cannot parse effective Git attributes for candidate delta",
    )
    for index in range(0, len(fields), 3):
        path = canonical_relative_path(fields[index], label="Git attribute path")
        attribute = fields[index + 1].decode("ascii", errors="strict")
        value = fields[index + 2].decode("utf-8", errors="strict")
        require(
            value == "unspecified",
            f"{path!r}: effective {attribute} attribute is forbidden ({value!r})",
        )


def current_facts(
    baseline: dict[str, GitEntry],
    anchor: dict[str, GitEntry],
    snapshot: CandidateSnapshot,
    context: RepositoryContext,
) -> dict[str, Any]:
    actual_changed = changed_paths(baseline, snapshot.entries)
    anchor_delta = classified_delta(anchor, snapshot.entries)
    protected = tuple(sorted(set(baseline).difference(actual_changed)))
    bound: dict[str, list[str]] = {}
    for path in BOUND_ALLOWED_PATHS:
        entry = snapshot.entries.get(path)
        require(entry is not None, f"reviewed full-blob path is missing: {path}")
        bound[path] = [entry.mode, entry.sha256]
    return {
        "allowlist_sha256": allowlist_digest(actual_changed),
        "baseline_path_count": len(baseline),
        "bound_allowed_blobs": bound,
        "anchor_delta": [
            {"path": path, "status": status_value}
            for path, status_value in anchor_delta
        ],
        "anchor_delta_path_count": len(anchor_delta),
        "changed_paths": list(actual_changed),
        "changed_projection_sha256": changed_projection(
            baseline, snapshot.entries, actual_changed
        ),
        "current_anchor": CURRENT_ANCHOR,
        "current_anchor_tree": CURRENT_ANCHOR_TREE,
        "current_head": snapshot.head,
        "diagnostic_only": True,
        "git_tcb": {
            "executable": context.git_binary.executable.path,
            "executable_sha256": context.git_binary.executable.sha256,
            "version": context.git_binary.version,
        },
        "git_context": {
            "common_git_dir": context.common_git_dir,
            "git_dir": context.git_dir,
            "info_attributes_absent": context.info_attributes_absent,
            "local_config_semantics_sha256": (context.local_config_semantics_sha256),
            "local_config_sha256": context.local_config.sha256,
            "replacement_refs_sha256": context.replacement_refs_sha256,
            "worktree_config_absent": context.worktree_config_absent,
        },
        "lifecycle": (
            "precommit-worktree"
            if snapshot.head == CURRENT_ANCHOR
            else "committed-descendant"
        ),
        "phase_path_policy": PHASE_PATH_POLICY,
        "phase_path_policy_sha256": hashlib.sha256(
            read_candidate_bytes(PHASE_PATH_POLICY)
        ).hexdigest(),
        "precommit_tracked_modifications": list(snapshot.tracked_modifications),
        "precommit_untracked_deliverables": list(snapshot.untracked),
        "protected_path_count": len(protected),
        "protected_projection_sha256": path_projection(baseline, protected),
        "schema": "pid-rs/ksg-phase-current-facts",
        "schema_revision": 1,
        "self_unhashed_paths": sorted(SELF_UNHASHED_PATHS),
    }


def render_tuple(name: str, values: list[str]) -> list[str]:
    lines = [f"{name} = ("]
    lines.extend(f"    {value!r}," for value in values)
    lines.append(")")
    return lines


def render_generated_block(facts: dict[str, Any]) -> str:
    lines = ["# BEGIN GENERATED PHASE FACTS"]
    lines.extend(
        render_tuple("EXPECTED_CHANGED_PATHS: tuple[str, ...]", facts["changed_paths"])
    )
    lines.extend(
        render_tuple(
            "EXPECTED_PRECOMMIT_TRACKED_MODIFICATIONS: tuple[str, ...]",
            facts["precommit_tracked_modifications"],
        )
    )
    lines.extend(
        render_tuple(
            "EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES: tuple[str, ...]",
            facts["precommit_untracked_deliverables"],
        )
    )
    lines.append(f"EXPECTED_ALLOWLIST_SHA256 = {facts['allowlist_sha256']!r}")
    lines.append(
        f"EXPECTED_CHANGED_PROJECTION_SHA256 = {facts['changed_projection_sha256']!r}"
    )
    lines.append(
        "EXPECTED_PROTECTED_PROJECTION_SHA256 = "
        f"{facts['protected_projection_sha256']!r}"
    )
    lines.append(f"EXPECTED_BASELINE_PATH_COUNT = {facts['baseline_path_count']}")
    lines.append(f"EXPECTED_PROTECTED_PATH_COUNT = {facts['protected_path_count']}")
    lines.append("EXPECTED_BOUND_ALLOWED_BLOBS: dict[str, tuple[str, str]] = {")
    for path, (mode, digest) in facts["bound_allowed_blobs"].items():
        lines.append(f"    {path!r}: ({mode!r}, {digest!r}),")
    lines.append("}")
    lines.append("# END GENERATED PHASE FACTS")
    return "\n".join(lines)


def validate_phase(
    *,
    expected_candidate_tree: str | None,
    checkpoint_commit: str | None,
    diagnostic_without_external_custody: bool,
) -> tuple[str, int, int, int, int, str | None, GitBinaryIdentity]:
    validate_checker_source_model()
    repository_context = validate_repository_context()
    snapshot = collect_candidate_snapshot()
    validate_commit_envelope(snapshot.head)
    baseline = hydrate_tree(parse_tree(SCIENTIFIC_BASELINE))
    anchor = hydrate_tree(parse_tree(CURRENT_ANCHOR))
    validate_prior_c2_history()
    policy_entries = validate_phase_path_policy(snapshot, anchor)
    custody = validate_staged_tree_custody(
        snapshot,
        expected_candidate_tree,
        checkpoint_commit,
    )
    require(
        custody[0] is not None or diagnostic_without_external_custody,
        "creditable validation requires the external candidate-tree/checkpoint pair; "
        "use --diagnostic-without-external-custody only for explicit NO-CREDIT replay",
    )
    require(
        not diagnostic_without_external_custody or custody == (None, None),
        "--diagnostic-without-external-custody cannot accompany external custody",
    )
    if snapshot.head != CURRENT_ANCHOR:
        require(
            expected_candidate_tree is not None and checkpoint_commit == snapshot.head,
            (
                "committed lifecycle requires --expected-candidate-tree and "
                "--checkpoint-commit equal to exact HEAD"
            ),
        )
    delivery = hydrate_tree(parse_tree(DELIVERY_PARENT))
    require(
        len(baseline) == EXPECTED_BASELINE_PATH_COUNT,
        "scientific baseline path count changed",
    )
    tracked_ignore_sources = tuple(
        path
        for path in sorted(snapshot.entries)
        if path == ".gitignore" or path.endswith("/.gitignore")
    )
    require(
        tracked_ignore_sources == (".gitignore",),
        "candidate must contain exactly one root .gitignore visibility source",
    )

    delivery_changed = changed_paths(baseline, delivery)
    require(
        delivery_changed == tuple(sorted(DELIVERY_CHANGED_BLOBS)),
        "delivery commit changed-path envelope mismatch",
    )
    for path, (mode, digest) in DELIVERY_CHANGED_BLOBS.items():
        entry = delivery.get(path)
        require(
            entry is not None and (entry.mode, entry.sha256) == (mode, digest),
            f"delivery commit blob pin mismatch: {path}",
        )

    actual_changed = changed_paths(baseline, snapshot.entries)
    require(
        allowlist_digest(EXPECTED_CHANGED_PATHS) == EXPECTED_ALLOWLIST_SHA256,
        "reviewed allowlist digest does not match checker constants",
    )
    require(
        actual_changed == EXPECTED_CHANGED_PATHS,
        "candidate changed-path set differs from the exact KSG allowlist",
    )
    require(
        changed_projection(baseline, snapshot.entries, actual_changed)
        == EXPECTED_CHANGED_PROJECTION_SHA256,
        "candidate changed-byte projection digest mismatch",
    )

    protected = tuple(sorted(set(baseline).difference(EXPECTED_CHANGED_PATHS)))
    require(
        len(protected) == EXPECTED_PROTECTED_PATH_COUNT,
        "protected path count changed",
    )
    require(
        path_projection(baseline, protected) == EXPECTED_PROTECTED_PROJECTION_SHA256,
        "scientific-baseline protected projection pin mismatch",
    )
    for path in protected:
        left = baseline[path]
        right = snapshot.entries.get(path)
        require(
            right is not None
            and (right.mode, right.kind, right.sha256)
            == (left.mode, left.kind, left.sha256),
            f"protected path mode/type/blob changed: {path}",
        )
    for path, (mode, digest) in PINNED_PROTECTED_BLOBS.items():
        baseline_entry = baseline.get(path)
        candidate_entry = snapshot.entries.get(path)
        require(
            baseline_entry is not None
            and (baseline_entry.mode, baseline_entry.sha256) == (mode, digest),
            f"pinned protected baseline fact mismatch: {path}",
        )
        require(
            candidate_entry is not None
            and (candidate_entry.mode, candidate_entry.sha256) == (mode, digest),
            f"pinned protected candidate blob changed: {path}",
        )

    require(
        set(EXPECTED_BOUND_ALLOWED_BLOBS) == set(BOUND_ALLOWED_PATHS),
        "reviewed full-blob pin inventory does not match its path inventory",
    )
    for path, expected in EXPECTED_BOUND_ALLOWED_BLOBS.items():
        entry = snapshot.entries.get(path)
        require(
            entry is not None and (entry.mode, entry.sha256) == expected,
            f"reviewed full candidate blob changed: {path}",
        )

    if snapshot.head == CURRENT_ANCHOR:
        lifecycle = "precommit-worktree"
        require(
            snapshot.tracked_modifications == EXPECTED_PRECOMMIT_TRACKED_MODIFICATIONS,
            "precommit tracked-modification partition changed",
        )
        require(
            snapshot.untracked == EXPECTED_PRECOMMIT_UNTRACKED_DELIVERABLES,
            "precommit untracked-deliverable partition changed",
        )
    else:
        lifecycle = "committed-descendant"
        require(
            not snapshot.tracked_modifications and not snapshot.untracked,
            "committed phase requires a clean tracked/untracked worktree",
        )

    validate_effective_attributes(entry.path for entry in policy_entries)
    validate_changed_path_firewall(actual_changed)
    validate_public_ci_failure_evidence()
    portability_memo_raw = validate_public_ci_portability_failure_evidence()
    validate_ci_corrective_firewall()
    validate_claim_checker_workflow_rebind()
    validate_python_entry_isolation()
    validate_foundational_pdf_lake_preflight()
    lean_artifacts = validate_lean_evidence_portability()
    validate_c3_local_artifact_parity(portability_memo_raw, lean_artifacts)
    validate_package_archive_corrective_firewall()
    validate_ecosystem_corrective_firewall()
    validate_stats_firewall()
    validate_parallel_semantics()
    validate_release_firewall()
    validate_identity_firewall()
    validate_c3_science_and_publication_isolation(snapshot, anchor)

    replay_context = validate_repository_context()
    replay = collect_candidate_snapshot()
    replay_custody = validate_staged_tree_custody(
        replay,
        expected_candidate_tree,
        checkpoint_commit,
    )
    require(
        replay_context == repository_context,
        "Git executable, configuration, metadata, or visibility context changed during replay",
    )
    require(
        replay == snapshot, "candidate filesystem or Git inputs changed during replay"
    )
    require(
        replay_custody == custody, "external staged-tree custody changed during replay"
    )
    return (
        lifecycle,
        len(actual_changed),
        len(protected),
        len(snapshot.tracked_modifications),
        len(snapshot.untracked),
        custody[0],
        repository_context.git_binary,
    )


DESCRIPTION = """\
Validate KSG revision-4 Git phase provenance on the Git-visible candidate
snapshot (HEAD-tracked files plus untracked deliverables not excluded by the
exact protected root .gitignore).

On success this proves only the pinned baseline -> delivery -> formal-anchor
single-parent envelope, the exact reviewed candidate delta, byte/mode/type
identity of protected paths, complete-byte pins for reviewed high-risk paths,
exact anchor/absent -> final-byte monotonicity of every reachable post-anchor
tree, and the bounded KSG-vs-later-wave firewall encoded here.

It does NOT prove arithmetic, formal-statement adequacy, Rust/compiler
conformance, estimator accuracy, support assumptions, PID validity,
statistical calibration, publication quality, remote/push state,
authenticity, trustworthiness of the identified Git executable, or absence of
hash collisions. Every path ignored by the protected root .gitignore,
including credentials, secrets, build products, caches, and editor state, is
outside the candidate snapshot; local info/exclude bytes are deliberately not
an input. No gate may silently depend on an ignored path. The checker and
self-test bytes are intentionally outside the self-stored digest projection.
Use the external tree/commit hooks to bind them to an independently pre-pinned,
separately reviewed staged tree.  A tree computed after checker mutation does
not close the self-reference cut; even pre-pinned custody is not an
authenticity proof.

Inside the phase self-test, disposable candidate-checker initial source is
stable-captured and executed over standard input with this lexical __file__,
and all candidate overlays are materialized from one frozen byte/mode map.
Official top-level checker/self-test entries remain initially path-loaded.
Runtime candidate reads, Git objects/configuration, Python/stdlib/loader state,
and the destination filesystem remain external premises. Stable double reads
and post-child/post-write endpoint replay do not provide an atomic filesystem
history or protection from a concurrent same-UID or privileged writer.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--emit-current-facts-json",
        action="store_true",
        help=(
            "print canonical diagnostic facts for the current snapshot; this "
            "does not validate the reviewed constants"
        ),
    )
    group.add_argument(
        "--emit-current-facts-python",
        action="store_true",
        help=(
            "print a mechanically replaceable generated-constant block; this "
            "is diagnostic input requiring human review, not validation"
        ),
    )
    parser.add_argument(
        "--expected-candidate-tree",
        metavar="TREE",
        help=(
            "require the complete candidate snapshot, including the two "
            "self-unhashed scripts, to equal this externally created Git tree"
        ),
    )
    parser.add_argument(
        "--checkpoint-commit",
        metavar="COMMIT",
        help=(
            "additionally require this detached checkpoint commit to carry "
            "the supplied candidate tree and be HEAD or an exact child of HEAD"
        ),
    )
    parser.add_argument(
        "--diagnostic-without-external-custody",
        action="store_true",
        help=(
            "permit an explicit NO-CREDIT precommit replay without an external "
            "candidate-tree/checkpoint pair"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.emit_current_facts_json or args.emit_current_facts_python:
            require(
                not args.diagnostic_without_external_custody,
                "fact emission is already diagnostic and must not combine with "
                "--diagnostic-without-external-custody",
            )
            validate_checker_source_model()
            context = validate_repository_context()
            snapshot = collect_candidate_snapshot()
            validate_commit_envelope(snapshot.head)
            baseline = hydrate_tree(parse_tree(SCIENTIFIC_BASELINE))
            anchor = hydrate_tree(parse_tree(CURRENT_ANCHOR))
            validate_phase_path_policy(snapshot, anchor)
            validate_staged_tree_custody(
                snapshot,
                args.expected_candidate_tree,
                args.checkpoint_commit,
            )
            facts = current_facts(baseline, anchor, snapshot, context)
            if args.emit_current_facts_json:
                print(json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=True))
            else:
                print(render_generated_block(facts))
            return 0
        (
            lifecycle,
            changed,
            protected,
            tracked,
            untracked,
            candidate_tree,
            git_binary,
        ) = validate_phase(
            expected_candidate_tree=args.expected_candidate_tree,
            checkpoint_commit=args.checkpoint_commit,
            diagnostic_without_external_custody=(
                args.diagnostic_without_external_custody
            ),
        )
    except PhaseIsolationError as error:
        detail = json.dumps(str(error), ensure_ascii=True)[1:-1]
        print(f"ERROR: KSG phase isolation: {detail}", file=sys.stderr)
        return 1
    prefix = (
        "OK: KSG phase provenance only"
        if candidate_tree is not None
        else "NO-CREDIT: KSG phase provenance diagnostic only"
    )
    print(
        f"{prefix}; "
        f"lifecycle={lifecycle}; changed={changed}; protected={protected}; "
        f"tracked-worktree={tracked}; untracked-deliverables={untracked}; "
        f"baseline={SCIENTIFIC_BASELINE}; delivery={DELIVERY_PARENT}; "
        f"anchor={CURRENT_ANCHOR}; self-unhashed={len(SELF_UNHASHED_PATHS)}; "
        f"candidate-tree={candidate_tree or 'not-requested'}; "
        f"checkpoint={args.checkpoint_commit or 'not-requested'}; "
        f"git={git_binary.executable.path}; "
        f"git-sha256={git_binary.executable.sha256}; "
        f"git-version={git_binary.version!r}. "
        "No arithmetic, estimator, PID, statistical, remote, or authenticity "
        "claim is implied."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
