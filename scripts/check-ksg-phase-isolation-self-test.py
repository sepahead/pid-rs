#!/usr/bin/env python3
"""Baseline-first hostile tests for the KSG Git phase-isolation checker."""

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
):
    print(
        "ERROR: check-ksg-phase-isolation-self-test.py requires Python -I -S",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import ast
import copy
from functools import wraps
from dataclasses import dataclass, replace as dataclass_replace
from enum import Enum
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import pickle
import py_compile
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
from typing import Callable, Iterable


SELF_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SELF_PATH.parent.parent
CHECKER_RELATIVE = "scripts/check-ksg-phase-isolation.py"
SELF_RELATIVE = "scripts/check-ksg-phase-isolation-self-test.py"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json"
CORRECTIVE_EVIDENCE = (
    "audit/evidence/ksg-rev4-public-ci-tooling-correction-2026-07-29.md"
)
PORTABILITY_CORRECTIVE_EVIDENCE = (
    "audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md"
)
LEAN_DESCRIPTOR_SELF_TEST_RELATIVE = (
    "scripts/check-lean-descriptor-factorization-self-test.py"
)
PUBLIC_CI_FAILURE_RECEIPT = (
    "audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json"
)
PUBLIC_CI_PORTABILITY_RECEIPT = (
    "audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json"
)
INTEGRATION_ANCHOR = "dc7b8de0a87443ef2bcde71b19938642f1af2197"
CURRENT_ANCHOR = "8b792bc143fff2d84f2d8e7817d1de7850741223"
SCIENTIFIC_BASELINE = "e96122b56c15e895c081379210103d1a26eac25f"
DELIVERY_PARENT = "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"
EXPECTED_CHANGED_PATH_COUNT = 187
EXPECTED_PROTECTED_PATH_COUNT = 373
EXPECTED_PRECOMMIT_TRACKED_COUNT = 16
EXPECTED_PRECOMMIT_UNTRACKED_COUNT = 3
EXPECTED_SELF_UNHASHED_COUNT = 2
EXPECTED_ANCHOR_DELTA_PATH_COUNT = 19
PHASE_LEAN_RAW_TRANSPORT_SUBCONTROL_COUNT = 6
C3_REVIEW_LEDGER_EXECUTION_COUNT = 85
C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT = 19
C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT = 21
DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT = 14
DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT = 2
DESCRIPTOR_V4_PARSER_SUBCONTROL_COUNT = 2
DESCRIPTOR_V4_NESTED_EXECUTION_COUNT = 18
EXECUTION_RECEIPT_STATIC_MODEL_PROBE_COUNT = 13
EXECUTION_RECEIPT_RUNTIME_HOSTILE_SHAPE_COUNT = 94
EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT = 107
EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256 = (
    "05225efda45bf9b2e6929c200a0816111bd0bb9c76019c1bfd274b329c2d09b8"
)
EXPECTED_RUN_LEAN_PORTABILITY_ATTACKS_PORTABLE_AST_SHA256 = (
    "d6f416aeac09f221f1f4ec01af0f70c6370e97553f85cfbc559b95ea42fc2d87"
)
EXPECTED_RECEIPT_LIFECYCLE_PORTABLE_AST_SHA256 = (
    "f17ef79559e2f86ea9488e1abaf5392f1dfbc6725def2f512c21241c6d6a8b53"
)
EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC_SHA256 = (
    "c3c1b19f2580bba4a8d1ee75b02c87aab1cab587f928c58ff574e3164b292a61"
)
EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC_SHA256 = (
    "a01d1db6da0fb7b43f3ab58bcb59f14b71b64b90242a0f83ad92c5e5a7256c3b"
)
EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC = (
    (
        "artifact",
        "lean-portability-v4-direct-stdin-transport-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
        "direct_process_stdin_transport",
        (
            "descriptor-factorization Lean portable evidence value changed at "
            "$/process_stdin_transport"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-stdin-count-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "stdin_count",
        (
            "descriptor-factorization mutation evidence identity value changed at "
            "$/process_stdin_isolation_subcontrols_passed"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-order-count-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "order_count",
        (
            "descriptor-factorization mutation evidence identity value changed at "
            "$/raw_process_transport_order_subcontrols_rejected"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-stdin-inventory-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "stdin_inventory_identity",
        (
            "descriptor-factorization parser/mutation parity field "
            "process_stdin_isolation_subcontrols value changed at $/0/probe_sha256"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-order-inventory-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "order_inventory_identity",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_order_subcontrols value changed at "
            "$/0/probe_sha256"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-mixed-stream-reason-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "mixed_stream_reason",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_order_subcontrols value changed at "
            "$/0/rejection_reason"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-executable-identity-boundary-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
        "direct_identity_boundary",
        (
            "descriptor-factorization Lean portable evidence value changed at "
            "$/lean_executable_identity_boundary"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-input-snapshot-boundary-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
        "direct_snapshot_boundary",
        (
            "descriptor-factorization Lean portable evidence value changed at "
            "$/input_snapshot_boundary"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-mutation-boundary-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "mutation_boundary",
        (
            "descriptor-factorization mutation evidence identity value changed at "
            "$/boundary"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-raw-reason-0-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "raw_reason_0",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_hostile_cases value changed at "
            "$/0/rejection_reason"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-raw-reason-1-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "raw_reason_1",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_hostile_cases value changed at "
            "$/1/rejection_reason"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-raw-reason-2-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "raw_reason_2",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_hostile_cases value changed at "
            "$/2/rejection_reason"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-raw-reason-3-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "raw_reason_3",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_hostile_cases value changed at "
            "$/3/rejection_reason"
        ),
    ),
    (
        "artifact",
        "lean-portability-v4-raw-reason-4-subcontrol",
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
        "raw_reason_4",
        (
            "descriptor-factorization parser/mutation parity field "
            "raw_process_transport_hostile_cases value changed at "
            "$/4/rejection_reason"
        ),
    ),
    (
        "parser",
        "lean-portability-v4-parser-boundary-subcontrol",
        "scripts/check-ksg-phase-isolation.py",
        "parser_boundary",
        "Lean portability parser replay identity value changed at $/boundary",
    ),
    (
        "parser",
        "lean-portability-v4-parser-receipt-pin-subcontrol",
        "scripts/check-ksg-phase-isolation.py",
        "parser_receipt_pin",
        ("C3 portability memo parser-only digest differs from executed parser receipt"),
    ),
    (
        "source",
        "lean-portability-v4-devnull-stdin-source-subcontrol",
        "scripts/check-lean-descriptor-factorization.py",
        "devnull_stdin_source",
        "Lean portability descriptor-pinned child source model changed",
    ),
    (
        "source",
        "lean-portability-v4-completed-buffer-loop-order-subcontrol",
        "scripts/check-lean-descriptor-factorization.py",
        "completed_buffer_loop_order",
        "Lean portability descriptor-pinned child source model changed",
    ),
)
EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC = (
    ("static_model", "complete_module_baseline", "accepted"),
    (
        "static_model",
        "baseline_helper_early_return",
        "self-test complete-module portable AST projection changed",
    ),
    (
        "static_model",
        "ledger_code_call_unreachable",
        "self-test complete-module portable AST projection changed",
    ),
    (
        "static_model",
        "ledger_structural_call_unreachable",
        "self-test complete-module portable AST projection changed",
    ),
    (
        "static_model",
        "parity_call_unreachable",
        "self-test complete-module portable AST projection changed",
    ),
    (
        "static_model",
        "module_digest_wrong_literal",
        "self-test complete-module digest literal does not match runtime pin",
    ),
    (
        "static_model",
        "module_digest_duplicate_binding",
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    ),
    (
        "static_model",
        "module_digest_computed_binding",
        "self-test complete-module digest assignment is not one exact literal pin",
    ),
    (
        "static_model",
        "module_digest_delete_binding",
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    ),
    (
        "static_model",
        "module_digest_globals_setitem",
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    ),
    (
        "static_model",
        "module_digest_globals_update",
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    ),
    (
        "static_model",
        "module_digest_exec_writer",
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    ),
    (
        "static_model",
        "module_digest_module_setattr",
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_none",
        "baseline attack execution receipt has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_type_dict",
        "baseline attack execution receipt has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_subclass",
        "baseline attack execution receipt has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_issuer",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_unissued_exact_lookalike",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_shallow_copy",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_deepcopy",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_dataclasses_replace",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_dry_to_real_replay",
        "baseline attack execution receipt was issued in the wrong lane",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_label",
        "baseline attack execution receipt label changed",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_path",
        "baseline attack execution receipt ordered paths changed",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_first_detail",
        "baseline attack execution receipt first rejection detail changed",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_semantic_detail",
        "baseline attack execution receipt semantic rejection detail changed",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_receipt_wrong_state",
        "baseline attack execution receipt has the wrong completion state",
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_reused_capability",
        (
            "baseline attack execution receipt capability was already issued for "
            "baseline attack execution receipt"
        ),
    ),
    (
        "runtime_hostile",
        "descriptor_baseline_reused_object",
        "baseline attack execution receipt was already collected",
    ),
    (
        "runtime_hostile",
        "descriptor_receipt_unissued_wrapper_around_registered_baseline",
        "descriptor-v4 execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_receipt_dry_to_real_replay",
        "descriptor-v4 execution receipt was issued in the wrong lane",
    ),
    (
        "runtime_hostile",
        "descriptor_receipts_reaggregated",
        "descriptor-v4 execution receipt was already collected",
    ),
    (
        "runtime_hostile",
        "descriptor_receipts_unreachable",
        "descriptor-v4 validated execution receipt inventory changed",
    ),
    (
        "runtime_hostile",
        "descriptor_receipts_reordered",
        "descriptor-v4 ordered execution receipt projection changed",
    ),
    (
        "runtime_hostile",
        "descriptor_receipts_duplicate",
        "descriptor-v4 ordered execution receipt projection changed",
    ),
    (
        "runtime_hostile",
        "sealed_primary_system_exit_none",
        (
            "sealed_primary_system_exit_none: primary BaseException("
            "type=builtins.SystemExit, code_type=builtins.NoneType, code=None, "
            "repr=SystemExit(None))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_primary_system_exit_zero",
        (
            "sealed_primary_system_exit_zero: primary BaseException("
            "type=builtins.SystemExit, code_type=builtins.int, code=0, "
            "repr=SystemExit(0))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_primary_system_exit_false",
        (
            "sealed_primary_system_exit_false: primary BaseException("
            "type=builtins.SystemExit, code_type=builtins.bool, code=False, "
            "repr=SystemExit(False))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_primary_system_exit_nonzero_with_cleanup",
        (
            "sealed_primary_system_exit_nonzero_with_cleanup: primary "
            "BaseException(type=builtins.SystemExit, code_type=builtins.int, "
            "code=7, repr=SystemExit(7)); cleanup BaseExceptions=restore("
            "type=builtins.KeyboardInterrupt, "
            "repr=KeyboardInterrupt('cleanup-interrupt'))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_primary_keyboard_interrupt",
        (
            "sealed_primary_keyboard_interrupt: primary BaseException("
            "type=builtins.KeyboardInterrupt, "
            "repr=KeyboardInterrupt('primary-interrupt'))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_primary_generator_exit",
        (
            "sealed_primary_generator_exit: primary BaseException("
            "type=builtins.GeneratorExit, "
            "repr=GeneratorExit('primary-generator-exit'))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_cleanup_system_exit_zero",
        (
            "sealed_cleanup_system_exit_zero: cleanup BaseExceptions=restore("
            "type=builtins.SystemExit, code_type=builtins.int, code=0, "
            "repr=SystemExit(0))"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_receipt_none",
        "sealed nested operation receipt has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_unissued_exact_lookalike",
        "sealed nested operation receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_dry_to_real_replay",
        "sealed nested operation receipt was issued in the wrong lane",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_reused_object",
        "sealed nested operation receipt was already collected",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_wrong_status",
        "sealed nested operation receipt status equality changed",
    ),
    (
        "runtime_hostile",
        "nested_receipt_none",
        "C3 nested memo attack execution receipt has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "nested_receipt_wrong_issuer",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_unissued_exact_lookalike",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_shallow_copy",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_deepcopy",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_dataclasses_replace",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_dry_to_real_replay",
        "C3 nested memo attack execution receipt was issued in the wrong lane",
    ),
    (
        "runtime_hostile",
        "nested_receipt_wrong_role",
        "C3 nested memo attack execution receipt role changed",
    ),
    (
        "runtime_hostile",
        "nested_receipt_wrong_detail",
        "C3 nested memo attack execution receipt projection changed",
    ),
    (
        "runtime_hostile",
        "nested_receipts_reused_capability",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipts_reaggregated",
        "C3 nested memo attack execution receipt was already collected",
    ),
    (
        "runtime_hostile",
        "ledger_receipts_unreachable",
        "C3 review-ledger nested execution receipt inventory is incomplete",
    ),
    (
        "runtime_hostile",
        "parity_receipts_unreachable",
        "C3 local-artifact-parity nested execution receipt inventory is incomplete",
    ),
    (
        "runtime_hostile",
        "nested_receipts_reordered",
        "C3 nested memo attack execution receipt projection changed",
    ),
    (
        "runtime_hostile",
        "nested_receipts_duplicate",
        "C3 nested memo attack execution receipt projection changed",
    ),
    (
        "runtime_hostile",
        "baseline_direct_completed_mint_without_lifecycle",
        "baseline lifecycle capability has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "cross_kind_capability_reuse",
        (
            "sealed nested operation receipt capability was already issued for "
            "baseline attack execution receipt"
        ),
    ),
    (
        "runtime_hostile",
        "descriptor_registry_prepopulation_without_child_linkage",
        "descriptor-v4 execution receipt requires atomic child linkage",
    ),
    (
        "runtime_hostile",
        "nested_registry_prepopulation_without_child_linkage",
        "C3 nested memo attack execution receipt requires atomic child linkage",
    ),
    (
        "runtime_hostile",
        "registry_route_record_not_exposed",
        "baseline attack execution receipt was issued in the wrong lane",
    ),
    (
        "runtime_hostile",
        "descriptor_issuer_callable_substitution",
        "descriptor-v4 issuer callable changed before receipt linkage",
    ),
    (
        "runtime_hostile",
        "descriptor_returned_receipt_wrong_baseline",
        "descriptor-v4 issuer returned a receipt linked to a different baseline",
    ),
    (
        "runtime_hostile",
        "baseline_receipt_pickle_roundtrip",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_pickle_roundtrip",
        "sealed nested operation receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_pickle_roundtrip",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_receipt_pickle_roundtrip",
        "descriptor-v4 execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "baseline_receipt_object_new",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_object_new",
        "sealed nested operation receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "nested_receipt_object_new",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_receipt_object_new",
        "descriptor-v4 execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "baseline_lifecycle_permit_object_new",
        "baseline lifecycle capability was not issued by its authority",
    ),
    (
        "runtime_hostile",
        "descriptor_parent_atomic_rollback",
        "baseline attack execution receipt was already collected",
    ),
    (
        "runtime_hostile",
        "c3_parent_atomic_rollback",
        "sealed nested operation receipt was already collected",
    ),
    (
        "runtime_hostile",
        "descriptor_copied_linked_child",
        "baseline attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "c3_copied_linked_child",
        "sealed nested operation receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_post_collection_substitution",
        "descriptor-v4 execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "c3_post_collection_substitution",
        "C3 nested memo attack execution receipt was not issued by its registry",
    ),
    (
        "runtime_hostile",
        "descriptor_post_collection_reissue",
        "baseline attack execution receipt was already collected",
    ),
    (
        "runtime_hostile",
        "c3_post_collection_reissue",
        "sealed nested operation receipt was already collected",
    ),
    (
        "runtime_hostile",
        "c3_issuer_callable_substitution",
        "C3 nested issuer callable changed before receipt linkage",
    ),
    (
        "runtime_hostile",
        "c3_returned_receipt_wrong_sealed_child",
        "C3 nested issuer returned a receipt linked to a different sealed child",
    ),
    (
        "runtime_hostile",
        "c3_independent_edge_substitution",
        "C3 nested memo attack execution receipt exact parent-child edge changed",
    ),
    (
        "runtime_hostile",
        "sealed_receipt_issuer_callable_substitution",
        "sealed nested operation receipt issuer callable changed before lifecycle",
    ),
    (
        "runtime_hostile",
        "outer_sealed_primary_system_exit_none",
        "outer sealed SystemExit(None) exact status/stdout/stderr grammar accepted",
    ),
    (
        "runtime_hostile",
        "outer_sealed_primary_system_exit_zero",
        "outer sealed SystemExit(0) exact status/stdout/stderr grammar accepted",
    ),
    (
        "runtime_hostile",
        "outer_sealed_primary_system_exit_false",
        "outer sealed SystemExit(False) exact status/stdout/stderr grammar accepted",
    ),
    (
        "runtime_hostile",
        "baseline_permit_before_observations",
        "baseline lifecycle causal observation inventory changed",
    ),
    (
        "runtime_hostile",
        "sealed_declarative_issuer_without_permit",
        "sealed lifecycle capability has the wrong exact type",
    ),
    (
        "runtime_hostile",
        "baseline_real_generic_leaf_issue",
        (
            "baseline attack execution receipt real leaf issue requires a "
            "completed lifecycle permit"
        ),
    ),
    (
        "runtime_hostile",
        "sealed_real_generic_leaf_issue",
        (
            "sealed nested operation receipt real leaf issue requires a "
            "completed lifecycle permit"
        ),
    ),
    (
        "runtime_hostile",
        "baseline_leaf_arbitrary_collection",
        "baseline attack execution receipt collection label changed",
    ),
    (
        "runtime_hostile",
        "sealed_leaf_arbitrary_collection",
        "sealed nested operation receipt collection label changed",
    ),
    (
        "runtime_hostile",
        "descriptor_parent_arbitrary_collection",
        "descriptor-v4 execution receipt collection label changed",
    ),
    (
        "runtime_hostile",
        "sealed_foreign_thread_issue",
        "_SealedLifecycleAuthority.issue_completed rejected foreign-thread entry",
    ),
    (
        "runtime_hostile",
        "sealed_reentrant_begin",
        "_SealedLifecycleAuthority.begin rejected reentrant entry",
    ),
    (
        "runtime_hostile",
        "sealed_noop_body",
        "sealed lifecycle body did not create a nonempty exact file delta",
    ),
    (
        "runtime_hostile",
        "authority_record_edge_route_mismatch",
        "receipt authority parent-edge bijection changed",
    ),
    (
        "runtime_hostile",
        "authority_orphan_capability_owner",
        "receipt authority reverse capability ownership changed",
    ),
    (
        "runtime_hostile",
        "authority_unregistered_parent_edge",
        "receipt authority receipt-record bijection changed",
    ),
    (
        "runtime_hostile",
        "authority_malformed_baseline_observation",
        "receipt authority baseline observation provenance changed",
    ),
)
C3_REVIEW_BEGIN_BYTES = b"C3_PRECOMMIT_REVIEW_PARITY_BEGIN\n"
C3_REVIEW_END_BYTES = b"\nC3_PRECOMMIT_REVIEW_PARITY_END"
C3_LOCAL_ARTIFACT_BEGIN_BYTES = b"C3_LOCAL_ARTIFACT_PARITY_BEGIN\n"
C3_LOCAL_ARTIFACT_END_BYTES = b"\nC3_LOCAL_ARTIFACT_PARITY_END"
EXACT_CANDIDATE_LOADER_SUBCONTROL_COUNT = 8
EXPECTED_GIT_CONTEXT_KEYS = frozenset(
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
CLONE_VARIANT_GIT_CONTEXT_KEYS = frozenset(
    {
        "common_git_dir",
        "git_dir",
        "local_config_semantics_sha256",
        "local_config_sha256",
    }
)
CLONE_INVARIANT_GIT_CONTEXT_KEYS = frozenset(
    {
        "info_attributes_absent",
        "replacement_refs_sha256",
        "worktree_config_absent",
    }
)
FROZEN_MODE_SUBCONTROL_RELATIVE = "scripts/check-lean-descriptor-factorization.py"
SUCCESS_NONCLAIM = (
    "No arithmetic, estimator, PID, statistical, remote, or authenticity "
    "claim is implied."
)
EXPECTED_C3_COMMIT_MESSAGE = "fix: harden Lean evidence portability and replay\n"
EXPECTED_C3_COMMIT_SUBJECT = EXPECTED_C3_COMMIT_MESSAGE.removesuffix("\n")
EXPECTED_C3_COMMIT_DISPLAY_NAME = "Sepehr Mahmoudian"
EXPECTED_C3_COMMIT_EMAIL = "sepmhn@gmail.com"
CORRECTIVE_PATHS = frozenset(
    {
        ".github/workflows/ci.yml",
        "AGENTS.md",
        "CHANGELOG.md",
        "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md",
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
        ("audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json"),
        PORTABILITY_CORRECTIVE_EVIDENCE,
        PUBLIC_CI_PORTABILITY_RECEIPT,
        POLICY_RELATIVE,
        "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex",
        "audit/tools/foundational_sxpid/README.md",
        "justfile",
        "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
        CHECKER_RELATIVE,
        SELF_RELATIVE,
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-foundational-sxpid-audit-pdf.sh",
        "scripts/check-lean-descriptor-factorization-self-test.py",
        "scripts/check-lean-descriptor-factorization.py",
    }
)
GENERATED_BEGIN = "# BEGIN GENERATED PHASE FACTS"
GENERATED_END = "# END GENERATED PHASE FACTS"
CANDIDATE_CHECKER_STDIN_BOOTSTRAP = (
    "import sys\n"
    "logical_file = sys.argv[1]\n"
    "sys.argv = [logical_file, *sys.argv[2:]]\n"
    "source = sys.stdin.buffer.read()\n"
    "namespace = {\n"
    "    '__name__': '__main__',\n"
    "    '__file__': logical_file,\n"
    "    '__package__': None,\n"
    "    '__cached__': None,\n"
    "    '__pid_rs_exact_source_bytes__': source,\n"
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
EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256 = (
    "3c092be3206ebdac36f7ca3bac9ae2fb83840cff836dcc79a62602450ab18df3"
)
EXACT_CHECKER_ENVIRONMENT_OVERRIDE_KEYS = frozenset(
    {
        "GIT_ATTR_SOURCE",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
    }
)
_RESOLVED_GIT_EXECUTABLE: str | None = None
_RESOLVED_GIT_EVIDENCE: tuple[str, str, str] | None = None
_FAILURE_DETAIL_TEMPLATES: tuple[FailureTemplate, ...] | None = None
_FAILURE_DETAIL_SOURCE_ENTRY: FrozenOverlayEntry | None = None


class SelfTestError(RuntimeError):
    """The checker accepted a mutation or the self-test lost custody."""


def _serial_authority_method(method: Callable[..., object]) -> Callable[..., object]:
    """Reject foreign-thread and recursive authority entry without blocking."""

    @wraps(method)
    def guarded(self: object, *args: object, **kwargs: object) -> object:
        context = f"{type(self).__name__}.{method.__name__}"
        require(
            threading.get_ident() == self._authority_owner_thread,
            f"{context} rejected foreign-thread entry",
        )
        require(
            self._authority_active is False,
            f"{context} rejected reentrant entry",
        )
        self._authority_active = True
        try:
            return method(self, *args, **kwargs)
        finally:
            self._authority_active = False

    return guarded


@dataclass(frozen=True)
class Backup:
    exists: bool
    raw: bytes
    mode: int


@dataclass(frozen=True)
class FrozenOverlayEntry:
    """One stable-captured regular file in the candidate overlay."""

    relative: str
    raw: bytes
    mode: int
    size: int
    sha256: str


@dataclass(frozen=True)
class FrozenOverlay:
    """Immutable ordered authority for all 187 candidate overlay files."""

    entries: tuple[FrozenOverlayEntry, ...]
    projection_sha256: str


@dataclass(frozen=True)
class ExactCheckerInvocation:
    """One completed exact-source checker child and its captured source."""

    process: subprocess.CompletedProcess[bytes]
    source_entry: FrozenOverlayEntry


@dataclass(frozen=True)
class FailureTemplate:
    """One normalized checker error-message shape."""

    pattern: re.Pattern[str]
    static_fragments: tuple[str, ...]
    dynamic_fields: int


@dataclass(frozen=True)
class FailureExpectation:
    """Caller-held exact detail or explicitly typed diagnostic-tail route."""

    fragment: str
    exact_detail: str | None
    diagnostic_prefix: str | None


@dataclass(frozen=True, slots=True, eq=False)
class BaselineAttackExecutionReceipt:
    """Capability-tagged receipt issued after rejection, restore, and green replay."""

    label: str
    paths: tuple[str, ...]
    first_detail: str
    semantic_detail: str
    state: str
    issuer: object
    capability: object
    lifecycle_permit: object | None = None


@dataclass(frozen=True, slots=True, eq=False)
class SealedNestedCandidateOperationReceipt:
    """Capability-tagged receipt issued after sealed nested cleanup completes."""

    label: str
    pre_status_sha256: str
    post_status_sha256: str
    status_equal: bool
    state: str
    issuer: object
    capability: object
    lifecycle_permit: object | None = None


@dataclass(frozen=True, slots=True, eq=False)
class C3NestedMemoAttackExecutionReceipt:
    """Validated nested C3 execution linked to its sealed cleanup receipt."""

    label: str
    expected_detail: str
    role: str
    inner_projection_constant: str | None
    begin: bytes | None
    end: bytes | None
    object_label: str | None
    sealed_receipt: SealedNestedCandidateOperationReceipt
    state: str
    issuer: object
    edge_capability: object
    capability: object


@dataclass(frozen=True, slots=True, eq=False)
class DescriptorV4ExecutionReceipt:
    """One descriptor control linked to its completed baseline attack receipt."""

    control: tuple[str, str, str, str, str]
    attack_receipt: BaselineAttackExecutionReceipt
    state: str
    issuer: object
    edge_capability: object
    capability: object


@dataclass(frozen=True, slots=True, eq=False)
class _ReceiptParentEdge:
    """Exact registry-owned parent/capability to child/capability linkage."""

    edge_capability: object
    parent_receipt: object
    parent_capability: object
    child_receipt: object
    child_capability: object
    kind: str
    route: str


@dataclass(frozen=True, slots=True, eq=False)
class _IssuedReceiptRecord:
    """Strong identity custody for one in-process receipt and its capability."""

    receipt: object
    capability: object
    kind: str
    route: str
    parent_edge: _ReceiptParentEdge | None = None
    child_edge: _ReceiptParentEdge | None = None
    aggregate_collection: tuple[str, int] | None = None
    aggregate_index: int | None = None


@dataclass(frozen=True, slots=True, eq=False)
class _CapabilityOwner:
    capability: object
    owner: object
    kind: str


@dataclass(frozen=True, slots=True, eq=False)
class _ReceiptAuthorityState:
    version: int
    receipt_records: tuple[_IssuedReceiptRecord, ...]
    lifecycle_records: tuple[_BaselineLifecycleRecord, ...]
    parent_edges: tuple[_ReceiptParentEdge, ...]
    permit_receipt_edges: tuple[_BaselinePermitReceiptEdge, ...]
    sealed_lifecycle_records: tuple[_SealedLifecycleRecord, ...]
    sealed_permit_receipt_edges: tuple[_SealedPermitReceiptEdge, ...]
    capability_owners: tuple[_CapabilityOwner, ...]


class _ReceiptFailPoint(Enum):
    AFTER_CHILD_VALIDATION = "after_child_validation"
    AFTER_PARENT_ALLOCATION = "after_parent_allocation"
    AFTER_EDGE_ALLOCATION = "after_edge_allocation"
    AFTER_STATE_STAGING = "after_state_staging"
    BEFORE_COMMIT = "before_commit"


class _ReceiptInjectedExceptionKind(Enum):
    PROJECT = "project"
    MEMORY = "memory"
    KEYBOARD = "keyboard"
    SYSTEM_EXIT_ZERO = "system_exit_zero"


class _InjectedReceiptFailure(SelfTestError):
    pass


def _inject_receipt_transaction_failure(
    fail_at: _ReceiptFailPoint | None,
    point: _ReceiptFailPoint,
    fail_kind: _ReceiptInjectedExceptionKind,
) -> None:
    if fail_at is not point:
        return
    detail = f"receipt transaction injected at {point.value}"
    if fail_kind is _ReceiptInjectedExceptionKind.PROJECT:
        raise _InjectedReceiptFailure(detail)
    if fail_kind is _ReceiptInjectedExceptionKind.MEMORY:
        raise MemoryError(detail)
    if fail_kind is _ReceiptInjectedExceptionKind.KEYBOARD:
        raise KeyboardInterrupt(detail)
    require(
        fail_kind is _ReceiptInjectedExceptionKind.SYSTEM_EXIT_ZERO,
        "receipt injected exception kind changed",
    )
    raise SystemExit(0)


class _ReceiptIssuanceRegistry:
    """A kind-specific facade over the one immutable run-authority root."""

    def __init__(
        self,
        *,
        kind: str,
        receipt_type: type[object],
        issuer: object,
        child_registry: _ReceiptIssuanceRegistry | None = None,
        child_attribute: str | None = None,
        edge_kind: str | None = None,
    ):
        linked_configuration = (child_registry, child_attribute, edge_kind)
        if not (
            all(value is None for value in linked_configuration)
            or (
                type(child_registry) is _ReceiptIssuanceRegistry
                and type(child_attribute) is str
                and child_attribute != ""
                and type(edge_kind) is str
                and edge_kind != ""
            )
        ):
            raise SelfTestError(f"{kind} linked-registry configuration changed")
        self.kind = kind
        self.receipt_type = receipt_type
        self.issuer = issuer
        self.child_registry = child_registry
        self.child_attribute = child_attribute
        self.edge_kind = edge_kind

    def issue(self, receipt: object, *, route: str) -> object:
        require(
            self.child_registry is None,
            f"{self.kind} requires atomic child linkage",
        )
        return _RECEIPT_RUN_AUTHORITY.issue_leaf(self, receipt, route=route)

    def issue_parent(
        self,
        *,
        child_receipt: object,
        parent_payload: object,
        route: str,
        fail_at: _ReceiptFailPoint | None = None,
        fail_kind: _ReceiptInjectedExceptionKind = (
            _ReceiptInjectedExceptionKind.PROJECT
        ),
    ) -> object:
        return _RECEIPT_RUN_AUTHORITY.issue_parent(
            self,
            child_receipt=child_receipt,
            parent_payload=parent_payload,
            route=route,
            fail_at=fail_at,
            fail_kind=fail_kind,
        )

    def validate(self, receipt: object, *, expected_route: str) -> None:
        _RECEIPT_RUN_AUTHORITY.validate(self, receipt, expected_route=expected_route)

    def require_exact_child_edge(
        self,
        parent_receipt: object,
        *,
        child_receipt: object,
        expected_route: str,
    ) -> None:
        _RECEIPT_RUN_AUTHORITY.require_exact_child_edge(
            self,
            parent_receipt,
            child_receipt=child_receipt,
            expected_route=expected_route,
        )

    def require_unlinked(self, receipt: object, *, expected_route: str) -> None:
        _RECEIPT_RUN_AUTHORITY.require_unlinked(
            self,
            receipt,
            expected_route=expected_route,
        )

    def collect_many_once(
        self,
        receipts: tuple[object, ...],
        *,
        collection: str,
        expected_route: str,
    ) -> None:
        _RECEIPT_RUN_AUTHORITY.collect_many_once(
            self,
            receipts,
            collection=collection,
            expected_route=expected_route,
        )


class _ReceiptRunAuthority:
    """One tuple-backed immutable root for receipts, edges, and lifecycles."""

    def __init__(self) -> None:
        self._authority_owner_thread = threading.get_ident()
        self._authority_active = False
        self.__state = _ReceiptAuthorityState(
            version=0,
            receipt_records=(),
            lifecycle_records=(),
            parent_edges=(),
            permit_receipt_edges=(),
            sealed_lifecycle_records=(),
            sealed_permit_receipt_edges=(),
            capability_owners=(),
        )

    @staticmethod
    def __route(route: object, *, context: str) -> str:
        require(
            type(route) is str and route in {"real_lifecycle", "dry_probe"},
            f"{context} route changed",
        )
        return route

    @staticmethod
    def __record_for(
        state: _ReceiptAuthorityState,
        registry: _ReceiptIssuanceRegistry,
        receipt: object,
    ) -> _IssuedReceiptRecord:
        require(
            type(receipt) is registry.receipt_type,
            f"{registry.kind} has the wrong exact type",
        )
        matches = tuple(
            record for record in state.receipt_records if record.receipt is receipt
        )
        require(
            len(matches) == 1,
            f"{registry.kind} was not issued by its registry",
        )
        record = matches[0]
        require(
            type(record) is _IssuedReceiptRecord
            and record.kind == registry.kind
            and record.receipt is receipt,
            f"{registry.kind} registry kind changed",
        )
        require(
            record.capability is getattr(receipt, "capability", None),
            f"{registry.kind} capability registry changed",
        )
        owners = tuple(
            owner
            for owner in state.capability_owners
            if owner.capability is record.capability
        )
        require(
            len(owners) == 1
            and owners[0].owner is receipt
            and owners[0].kind == registry.kind,
            f"{registry.kind} capability registry changed",
        )
        return record

    @staticmethod
    def __require_fresh_capability(
        state: _ReceiptAuthorityState,
        capability: object,
        *,
        kind: str,
    ) -> None:
        require(
            type(capability) is object,
            f"{kind} issuance capability has the wrong type",
        )
        prior = next(
            (
                owner
                for owner in state.capability_owners
                if owner.capability is capability
            ),
            None,
        )
        require(
            prior is None,
            f"{kind} capability was already issued for "
            + (prior.kind if prior is not None else "an unknown receipt kind"),
        )

    @staticmethod
    def __replace_receipt_record(
        records: tuple[_IssuedReceiptRecord, ...],
        old: _IssuedReceiptRecord,
        new: _IssuedReceiptRecord,
    ) -> tuple[_IssuedReceiptRecord, ...]:
        replaced = tuple(new if record is old else record for record in records)
        require(
            sum(record is new for record in replaced) == 1,
            "receipt authority replacement cardinality changed",
        )
        return replaced

    @staticmethod
    def __inject(
        fail_at: _ReceiptFailPoint | None,
        point: _ReceiptFailPoint,
        fail_kind: _ReceiptInjectedExceptionKind,
    ) -> None:
        _inject_receipt_transaction_failure(fail_at, point, fail_kind)

    @staticmethod
    def __require_parent_seal(
        registry: _ReceiptIssuanceRegistry,
        *,
        route: str,
    ) -> None:
        if registry.receipt_type is DescriptorV4ExecutionReceipt:
            current = (
                _issue_descriptor_v4_execution_receipt
                if route == "real_lifecycle"
                else _issue_dry_descriptor_v4_execution_receipt
            )
            sealed = (
                _SEALED_DESCRIPTOR_V4_REAL_ISSUER_CALLABLE
                if route == "real_lifecycle"
                else _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE
            )
        else:
            require(
                registry.receipt_type is C3NestedMemoAttackExecutionReceipt,
                f"{registry.kind} parent type seal changed",
            )
            current = (
                _issue_c3_nested_memo_attack_execution_receipt
                if route == "real_lifecycle"
                else _dry_c3_nested_memo_attack_execution_receipt
            )
            sealed = (
                _SEALED_C3_NESTED_REAL_ISSUER_CALLABLE
                if route == "real_lifecycle"
                else _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE
            )
        require(
            current is sealed,
            f"{registry.kind} transaction callable seal changed",
        )

    @staticmethod
    def __audit(state: _ReceiptAuthorityState) -> None:
        require(
            type(state) is _ReceiptAuthorityState
            and type(state.version) is int
            and state.version >= 0
            and type(state.receipt_records) is tuple
            and type(state.lifecycle_records) is tuple
            and type(state.sealed_lifecycle_records) is tuple
            and type(state.parent_edges) is tuple
            and type(state.permit_receipt_edges) is tuple
            and type(state.sealed_permit_receipt_edges) is tuple
            and type(state.capability_owners) is tuple
            and all(type(record) is _IssuedReceiptRecord for record in state.receipt_records)
            and all(type(record) is _BaselineLifecycleRecord for record in state.lifecycle_records)
            and all(
                type(record) is _SealedLifecycleRecord
                for record in state.sealed_lifecycle_records
            )
            and all(type(edge) is _ReceiptParentEdge for edge in state.parent_edges)
            and all(type(edge) is _BaselinePermitReceiptEdge for edge in state.permit_receipt_edges)
            and all(
                type(edge) is _SealedPermitReceiptEdge
                for edge in state.sealed_permit_receipt_edges
            )
            and all(type(owner) is _CapabilityOwner for owner in state.capability_owners),
            "receipt authority immutable root shape changed",
        )

        receipt_identities = tuple(id(record.receipt) for record in state.receipt_records)
        owner_capabilities = tuple(id(owner.capability) for owner in state.capability_owners)
        all_lifecycle_observations = tuple(
            observation
            for record in (*state.lifecycle_records, *state.sealed_lifecycle_records)
            for observation in record.observations
        )
        require(
            len(receipt_identities) == len(set(receipt_identities))
            and len(owner_capabilities) == len(set(owner_capabilities))
            and len(state.parent_edges) == len({id(edge) for edge in state.parent_edges})
            and len(state.permit_receipt_edges)
            == len({id(edge) for edge in state.permit_receipt_edges})
            and len(state.sealed_permit_receipt_edges)
            == len({id(edge) for edge in state.sealed_permit_receipt_edges})
            and len(
                {observation.event_ordinal for observation in all_lifecycle_observations}
            )
            == len(all_lifecycle_observations),
            "receipt authority identity ownership changed",
        )

        receipt_kinds = {
            BaselineAttackExecutionReceipt: _BASELINE_ATTACK_EXECUTION_REGISTRY.kind,
            SealedNestedCandidateOperationReceipt: (
                _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.kind
            ),
            DescriptorV4ExecutionReceipt: _DESCRIPTOR_V4_EXECUTION_REGISTRY.kind,
            C3NestedMemoAttackExecutionReceipt: (
                _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.kind
            ),
        }
        wrapper_types = {
            DescriptorV4ExecutionReceipt,
            C3NestedMemoAttackExecutionReceipt,
        }
        leaf_types = {
            BaselineAttackExecutionReceipt,
            SealedNestedCandidateOperationReceipt,
        }
        for record in state.receipt_records:
            receipt_type = type(record.receipt)
            owners = tuple(
                owner
                for owner in state.capability_owners
                if owner.capability is record.capability
            )
            require(
                receipt_type in receipt_kinds
                and record.kind == receipt_kinds[receipt_type]
                and record.route in {"real_lifecycle", "dry_probe"}
                and type(record.capability) is object
                and record.capability is getattr(record.receipt, "capability", None)
                and len(owners) == 1
                and owners[0].owner is record.receipt
                and owners[0].kind == record.kind
                and not (record.parent_edge is not None and record.child_edge is not None)
                and (
                    receipt_type in leaf_types and record.child_edge is None
                    or receipt_type in wrapper_types
                    and record.parent_edge is None
                    and type(record.child_edge) is _ReceiptParentEdge
                )
                and (
                    record.parent_edge is None
                    or any(record.parent_edge is edge for edge in state.parent_edges)
                )
                and (
                    record.child_edge is None
                    or any(record.child_edge is edge for edge in state.parent_edges)
                )
                and (
                    record.aggregate_collection is None
                    and record.aggregate_index is None
                    or receipt_type in wrapper_types
                    and type(record.aggregate_collection) is tuple
                    and len(record.aggregate_collection) == 2
                    and type(record.aggregate_collection[0]) is str
                    and type(record.aggregate_collection[1]) is int
                    and 0 < record.aggregate_collection[1] <= state.version
                    and type(record.aggregate_index) is int
                    and record.aggregate_index >= 0
                ),
                "receipt authority receipt-record bijection changed",
            )

        for edge in state.parent_edges:
            parent_records = tuple(
                record for record in state.receipt_records if record.receipt is edge.parent_receipt
            )
            child_records = tuple(
                record for record in state.receipt_records if record.receipt is edge.child_receipt
            )
            edge_owners = tuple(
                owner
                for owner in state.capability_owners
                if owner.capability is edge.edge_capability
            )
            require(
                len(parent_records) == len(child_records) == len(edge_owners) == 1
                and type(edge.edge_capability) is object
                and parent_records[0].child_edge is edge
                and child_records[0].parent_edge is edge
                and parent_records[0].route == child_records[0].route == edge.route
                and parent_records[0].capability is edge.parent_capability
                and child_records[0].capability is edge.child_capability
                and edge_owners[0].owner is edge
                and edge_owners[0].kind == edge.kind
                and (
                    type(edge.parent_receipt) is DescriptorV4ExecutionReceipt
                    and type(edge.child_receipt) is BaselineAttackExecutionReceipt
                    and edge.kind == DESCRIPTOR_V4_BASELINE_RECEIPT_LINKAGE
                    and edge.parent_receipt.attack_receipt is edge.child_receipt
                    or type(edge.parent_receipt) is C3NestedMemoAttackExecutionReceipt
                    and type(edge.child_receipt) is SealedNestedCandidateOperationReceipt
                    and edge.kind == C3_NESTED_SEALED_RECEIPT_LINKAGE
                    and edge.parent_receipt.sealed_receipt is edge.child_receipt
                ),
                "receipt authority parent-edge bijection changed",
            )

        collected_records = tuple(
            record for record in state.receipt_records if record.aggregate_collection is not None
        )
        for record in collected_records:
            collection = record.aggregate_collection
            group = tuple(
                candidate
                for candidate in collected_records
                if candidate.aggregate_collection == collection
                and type(candidate.receipt) is type(record.receipt)
                and candidate.route == record.route
            )
            allowed = (
                {"descriptor-v4 aggregate"}
                if type(record.receipt) is DescriptorV4ExecutionReceipt
                else (
                    {
                        "C3 review-ledger aggregate",
                        "C3 local-artifact-parity aggregate",
                    }
                    if record.route == "real_lifecycle"
                    else {
                        "C3 dry aggregate",
                        "C3 dry reaggregate aggregate",
                    }
                )
            )
            require(
                collection[0] in allowed
                and tuple(sorted(candidate.aggregate_index for candidate in group))
                == tuple(range(len(group))),
                "receipt authority aggregate collection coordinates changed",
            )

        baseline_states = (
            "pending_baseline",
            "pending_mutation",
            "pending_first_rejection",
            "pending_rebase",
            "pending_semantic_rejection",
            "pending_restoration",
            "pending_green_replay",
            POST_RESTORE_GREEN_REPLAY_COMPLETED,
        )
        baseline_operations = (
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            _SEALED_BASELINE_LIFECYCLE_MUTATION_PRODUCER,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            _SEALED_BASELINE_LIFECYCLE_REBASE_CHECKER_CALLABLE,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            _SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
        )
        for record in state.lifecycle_records:
            observation_count = len(record.observations)
            expected_relatives = tuple(dict.fromkeys((*record.paths, CHECKER_RELATIVE)))
            permit_owners = tuple(
                owner
                for owner in state.capability_owners
                if owner.capability is record.permit.capability
            )
            require(
                type(record.permit) is _BaselineLifecycleCapability
                and type(record.label) is str
                and record.label != ""
                and type(record.paths) is tuple
                and record.paths
                and all(type(path) is str for path in record.paths)
                and 0 <= observation_count <= len(BASELINE_LIFECYCLE_EVENTS)
                and tuple(type(observation) for observation in record.observations)
                == BASELINE_LIFECYCLE_OBSERVATION_TYPES[:observation_count]
                and tuple(observation.ordinal for observation in record.observations)
                == tuple(range(observation_count))
                and tuple(observation.event for observation in record.observations)
                == BASELINE_LIFECYCLE_EVENTS[:observation_count]
                and len(permit_owners) == 1
                and permit_owners[0].owner is record.permit
                and permit_owners[0].kind == "baseline lifecycle permit",
                "receipt authority baseline lifecycle record shape changed",
            )
            for index, observation in enumerate(record.observations):
                observation_owners = tuple(
                    owner
                    for owner in state.capability_owners
                    if owner.capability is observation.capability
                )
                require(
                    observation.permit is record.permit
                    and observation.issuer is _BASELINE_LIFECYCLE_OBSERVATION_ISSUER
                    and observation.predecessor
                    is (None if index == 0 else record.observations[index - 1])
                    and observation.operation is baseline_operations[index]
                    and observation.subject is record.root
                    and type(observation.snapshot) is tuple
                    and tuple(item[0] for item in observation.snapshot) == expected_relatives
                    and all(
                        type(item) is tuple
                        and len(item) == 3
                        and type(item[0]) is str
                        and type(item[1]) is int
                        and type(item[2]) is str
                        and re.fullmatch(r"[0-9a-f]{64}", item[2]) is not None
                        for item in observation.snapshot
                    )
                    and (
                        index in {0, 2, 4, 6}
                        and type(observation.artifact) is subprocess.CompletedProcess
                        or index in {1, 3, 5} and observation.artifact is None
                    )
                    and (
                        index in {2, 4}
                        and type(observation.detail) is str
                        and observation.detail != ""
                        or index not in {2, 4} and observation.detail is None
                    )
                    and len(observation_owners) == 1
                    and observation_owners[0].owner is observation
                    and observation_owners[0].kind
                    == f"baseline lifecycle observation {observation.event}",
                    "receipt authority baseline observation provenance changed",
                )
            require(
                (
                    record.state == "aborted"
                    and type(record.abort) is _LifecycleAbortRecord
                    and record.receipt_edge is None
                )
                or (
                    record.abort is None
                    and observation_count < len(BASELINE_LIFECYCLE_EVENTS)
                    and record.state == baseline_states[observation_count]
                    and record.receipt_edge is None
                )
                or (
                    record.abort is None
                    and observation_count == len(BASELINE_LIFECYCLE_EVENTS)
                    and (
                        record.state == POST_RESTORE_GREEN_REPLAY_COMPLETED
                        and record.receipt_edge is None
                        or record.state == "consumed_by_baseline_attack_execution_receipt"
                        and type(record.receipt_edge) is _BaselinePermitReceiptEdge
                    )
                ),
                "receipt authority baseline lifecycle terminal state changed",
            )

        sealed_states = (
            "pending_body",
            "pending_restoration",
            "pending_green_replay",
            POST_RESTORE_GREEN_REPLAY_COMPLETED,
        )
        sealed_operations = (
            _SEALED_OPERATION_BODY_PRODUCER,
            _SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
        )
        sealed_relatives = (PORTABILITY_CORRECTIVE_EVIDENCE, CHECKER_RELATIVE)
        for record in state.sealed_lifecycle_records:
            observation_count = len(record.observations)
            permit_owners = tuple(
                owner
                for owner in state.capability_owners
                if owner.capability is record.permit.capability
            )
            require(
                type(record.permit) is _SealedLifecycleCapability
                and type(record.label) is str
                and record.label != ""
                and type(record.expected_detail) is str
                and record.expected_detail != ""
                and isinstance(record.root, Path)
                and type(record.baseline_status) is bytes
                and type(record.baseline_snapshot) is tuple
                and 0 <= observation_count <= len(SEALED_LIFECYCLE_EVENTS)
                and tuple(type(observation) for observation in record.observations)
                == SEALED_LIFECYCLE_OBSERVATION_TYPES[:observation_count]
                and tuple(observation.ordinal for observation in record.observations)
                == tuple(range(observation_count))
                and tuple(observation.event for observation in record.observations)
                == SEALED_LIFECYCLE_EVENTS[:observation_count]
                and len(permit_owners) == 1
                and permit_owners[0].owner is record.permit
                and permit_owners[0].kind == "sealed lifecycle permit",
                "receipt authority sealed lifecycle record shape changed",
            )
            for index, observation in enumerate(record.observations):
                observation_owners = tuple(
                    owner
                    for owner in state.capability_owners
                    if owner.capability is observation.capability
                )
                require(
                    observation.permit is record.permit
                    and observation.issuer is _SEALED_LIFECYCLE_OBSERVATION_ISSUER
                    and observation.predecessor
                    is (None if index == 0 else record.observations[index - 1])
                    and observation.operation is sealed_operations[index]
                    and observation.subject is record.root
                    and type(observation.snapshot) is tuple
                    and tuple(item[0] for item in observation.snapshot) == sealed_relatives
                    and all(
                        type(item) is tuple
                        and len(item) == 3
                        and type(item[0]) is str
                        and type(item[1]) is int
                        and type(item[2]) is str
                        and re.fullmatch(r"[0-9a-f]{64}", item[2]) is not None
                        for item in observation.snapshot
                    )
                    and re.fullmatch(r"[0-9a-f]{64}", observation.status_sha256)
                    is not None
                    and (
                        index in {0, 2}
                        and type(observation.artifact) is subprocess.CompletedProcess
                        or index == 1 and observation.artifact is None
                    )
                    and (
                        index == 0
                        and type(observation.detail) is str
                        and observation.detail == record.expected_detail
                        or index in {1, 2} and observation.detail is None
                    )
                    and len(observation_owners) == 1
                    and observation_owners[0].owner is observation
                    and observation_owners[0].kind
                    == f"sealed lifecycle observation {observation.event}",
                    "receipt authority sealed observation provenance changed",
                )
            require(
                (
                    record.state == "aborted"
                    and type(record.abort) is _LifecycleAbortRecord
                    and record.receipt_edge is None
                )
                or (
                    record.abort is None
                    and observation_count < len(SEALED_LIFECYCLE_EVENTS)
                    and record.state == sealed_states[observation_count]
                    and record.receipt_edge is None
                )
                or (
                    record.abort is None
                    and observation_count == len(SEALED_LIFECYCLE_EVENTS)
                    and (
                        record.state == POST_RESTORE_GREEN_REPLAY_COMPLETED
                        and record.receipt_edge is None
                        or record.state == "consumed_by_sealed_nested_operation_receipt"
                        and type(record.receipt_edge) is _SealedPermitReceiptEdge
                    )
                ),
                "receipt authority sealed lifecycle terminal state changed",
            )

        for edge in state.permit_receipt_edges:
            permit_records = tuple(
                record for record in state.lifecycle_records if record.permit is edge.permit
            )
            receipt_records = tuple(
                record for record in state.receipt_records if record.receipt is edge.receipt
            )
            require(
                len(permit_records) == len(receipt_records) == 1
                and permit_records[0].receipt_edge is edge
                and permit_records[0].state == "consumed_by_baseline_attack_execution_receipt"
                and receipt_records[0].route == edge.route == "real_lifecycle"
                and receipt_records[0].capability is edge.receipt_capability
                and edge.permit.capability is edge.permit_capability
                and edge.receipt.lifecycle_permit is edge.permit
                and edge.kind == BASELINE_PERMIT_RECEIPT_LINKAGE,
                "receipt authority baseline permit-receipt bijection changed",
            )
        for record in state.lifecycle_records:
            matches = tuple(
                edge for edge in state.permit_receipt_edges if edge.permit is record.permit
            )
            require(
                record.state == "consumed_by_baseline_attack_execution_receipt"
                and len(matches) == 1
                and record.receipt_edge is matches[0]
                or record.state != "consumed_by_baseline_attack_execution_receipt"
                and not matches
                and record.receipt_edge is None,
                "receipt authority reverse baseline permit edge changed",
            )

        for edge in state.sealed_permit_receipt_edges:
            permit_records = tuple(
                record
                for record in state.sealed_lifecycle_records
                if record.permit is edge.permit
            )
            receipt_records = tuple(
                record for record in state.receipt_records if record.receipt is edge.receipt
            )
            require(
                len(permit_records) == len(receipt_records) == 1
                and permit_records[0].receipt_edge is edge
                and permit_records[0].state == "consumed_by_sealed_nested_operation_receipt"
                and receipt_records[0].route == edge.route == "real_lifecycle"
                and receipt_records[0].capability is edge.receipt_capability
                and edge.permit.capability is edge.permit_capability
                and edge.receipt.lifecycle_permit is edge.permit
                and edge.kind == SEALED_PERMIT_RECEIPT_LINKAGE,
                "receipt authority sealed permit-receipt bijection changed",
            )
        for record in state.sealed_lifecycle_records:
            matches = tuple(
                edge
                for edge in state.sealed_permit_receipt_edges
                if edge.permit is record.permit
            )
            require(
                record.state == "consumed_by_sealed_nested_operation_receipt"
                and len(matches) == 1
                and record.receipt_edge is matches[0]
                or record.state != "consumed_by_sealed_nested_operation_receipt"
                and not matches
                and record.receipt_edge is None,
                "receipt authority reverse sealed permit edge changed",
            )

        for record in state.receipt_records:
            receipt = record.receipt
            if type(receipt) is BaselineAttackExecutionReceipt:
                matches = tuple(
                    edge for edge in state.permit_receipt_edges if edge.receipt is receipt
                )
                require(
                    record.route == "dry_probe"
                    and receipt.lifecycle_permit is None
                    and not matches
                    or record.route == "real_lifecycle"
                    and type(receipt.lifecycle_permit) is _BaselineLifecycleCapability
                    and len(matches) == 1,
                    "receipt authority reverse baseline receipt edge changed",
                )
            if type(receipt) is SealedNestedCandidateOperationReceipt:
                matches = tuple(
                    edge
                    for edge in state.sealed_permit_receipt_edges
                    if edge.receipt is receipt
                )
                require(
                    record.route == "dry_probe"
                    and receipt.lifecycle_permit is None
                    and not matches
                    or record.route == "real_lifecycle"
                    and type(receipt.lifecycle_permit) is _SealedLifecycleCapability
                    and len(matches) == 1,
                    "receipt authority reverse sealed receipt edge changed",
                )

        expected_owners = tuple(
            (record.capability, record.receipt, record.kind)
            for record in state.receipt_records
        ) + tuple(
            (edge.edge_capability, edge, edge.kind) for edge in state.parent_edges
        ) + tuple(
            (record.permit.capability, record.permit, "baseline lifecycle permit")
            for record in state.lifecycle_records
        ) + tuple(
            (
                observation.capability,
                observation,
                f"baseline lifecycle observation {observation.event}",
            )
            for record in state.lifecycle_records
            for observation in record.observations
        ) + tuple(
            (record.permit.capability, record.permit, "sealed lifecycle permit")
            for record in state.sealed_lifecycle_records
        ) + tuple(
            (
                observation.capability,
                observation,
                f"sealed lifecycle observation {observation.event}",
            )
            for record in state.sealed_lifecycle_records
            for observation in record.observations
        )
        require(
            len(expected_owners) == len(state.capability_owners)
            and all(
                sum(
                    owner.capability is capability
                    and owner.owner is owner_object
                    and owner.kind == kind
                    for owner in state.capability_owners
                )
                == 1
                for capability, owner_object, kind in expected_owners
            ),
            "receipt authority reverse capability ownership changed",
        )

    @_serial_authority_method
    def require_terminal_success_state(self) -> None:
        state = self.__state
        self.__audit(state)
        require(
            all(
                record.state
                in {"aborted", "consumed_by_baseline_attack_execution_receipt"}
                for record in state.lifecycle_records
            )
            and all(
                record.state
                in {"aborted", "consumed_by_sealed_nested_operation_receipt"}
                for record in state.sealed_lifecycle_records
            )
            and all(
                record.route != "real_lifecycle"
                or type(record.receipt)
                not in {
                    DescriptorV4ExecutionReceipt,
                    C3NestedMemoAttackExecutionReceipt,
                }
                or record.aggregate_collection is not None
                and type(record.aggregate_index) is int
                for record in state.receipt_records
            )
            and all(
                record.route != "real_lifecycle"
                or type(record.receipt) is not SealedNestedCandidateOperationReceipt
                or type(record.parent_edge) is _ReceiptParentEdge
                for record in state.receipt_records
            ),
            "receipt authority retained a nonterminal credited state",
        )

    @_serial_authority_method
    def _probe_root(self) -> _ReceiptAuthorityState:
        return self.__state

    @_serial_authority_method
    def audit_projection(self) -> tuple[object, ...]:
        state = self.__state
        self.__audit(state)
        return (
            state.version,
            tuple(
                (
                    id(record.receipt),
                    id(record.capability),
                    record.kind,
                    record.route,
                    id(record.parent_edge) if record.parent_edge is not None else None,
                    id(record.child_edge) if record.child_edge is not None else None,
                    record.aggregate_collection,
                    record.aggregate_index,
                )
                for record in state.receipt_records
            ),
            tuple(
                (
                    id(edge),
                    id(edge.edge_capability),
                    id(edge.parent_receipt),
                    id(edge.parent_capability),
                    id(edge.child_receipt),
                    id(edge.child_capability),
                    edge.kind,
                    edge.route,
                )
                for edge in state.parent_edges
            ),
            tuple(
                (id(owner.capability), id(owner.owner), owner.kind)
                for owner in state.capability_owners
            ),
            len(state.lifecycle_records),
            len(state.permit_receipt_edges),
            len(state.sealed_lifecycle_records),
            len(state.sealed_permit_receipt_edges),
        )

    @_serial_authority_method
    def commit_lifecycle_components(
        self,
        *,
        expected_root: _ReceiptAuthorityState,
        lifecycle_records: tuple[_BaselineLifecycleRecord, ...] | None = None,
        permit_receipt_edges: tuple[_BaselinePermitReceiptEdge, ...] | None = None,
        sealed_lifecycle_records: tuple[_SealedLifecycleRecord, ...] | None = None,
        sealed_permit_receipt_edges: tuple[_SealedPermitReceiptEdge, ...]
        | None = None,
        receipt_records: tuple[_IssuedReceiptRecord, ...] | None = None,
        capability_owners: tuple[_CapabilityOwner, ...] | None = None,
        fail_at: _ReceiptFailPoint | None = None,
        fail_kind: _ReceiptInjectedExceptionKind = (
            _ReceiptInjectedExceptionKind.PROJECT
        ),
    ) -> None:
        require(
            fail_at is None or type(fail_at) is _ReceiptFailPoint,
            "lifecycle commit failure injection changed",
        )
        require(
            type(fail_kind) is _ReceiptInjectedExceptionKind
            and (
                fail_at is not None
                or fail_kind is _ReceiptInjectedExceptionKind.PROJECT
            ),
            "lifecycle commit injected exception kind changed",
        )
        require(
            self.__state is expected_root,
            "receipt authority root changed during lifecycle staging",
        )
        staged = dataclass_replace(
            expected_root,
            version=expected_root.version + 1,
            lifecycle_records=(
                expected_root.lifecycle_records
                if lifecycle_records is None
                else lifecycle_records
            ),
            permit_receipt_edges=(
                expected_root.permit_receipt_edges
                if permit_receipt_edges is None
                else permit_receipt_edges
            ),
            sealed_lifecycle_records=(
                expected_root.sealed_lifecycle_records
                if sealed_lifecycle_records is None
                else sealed_lifecycle_records
            ),
            sealed_permit_receipt_edges=(
                expected_root.sealed_permit_receipt_edges
                if sealed_permit_receipt_edges is None
                else sealed_permit_receipt_edges
            ),
            receipt_records=(
                expected_root.receipt_records
                if receipt_records is None
                else receipt_records
            ),
            capability_owners=(
                expected_root.capability_owners
                if capability_owners is None
                else capability_owners
            ),
        )
        self.__audit(staged)
        self.__inject(
            fail_at,
            _ReceiptFailPoint.AFTER_STATE_STAGING,
            fail_kind,
        )
        require(
            self.__state is expected_root,
            "receipt authority root changed before lifecycle commit",
        )
        self.__inject(
            fail_at,
            _ReceiptFailPoint.BEFORE_COMMIT,
            fail_kind,
        )
        self.__state = staged

    @_serial_authority_method
    def issue_leaf(
        self,
        registry: _ReceiptIssuanceRegistry,
        receipt: object,
        *,
        route: str,
    ) -> object:
        route = self.__route(route, context=registry.kind)
        require(
            route == "dry_probe",
            f"{registry.kind} real leaf issue requires a completed lifecycle permit",
        )
        old = self.__state
        require(
            type(receipt) is registry.receipt_type,
            f"{registry.kind} issuance received the wrong exact type",
        )
        require(
            not any(record.receipt is receipt for record in old.receipt_records),
            f"{registry.kind} object was already issued",
        )
        require(
            getattr(receipt, "issuer", None) is registry.issuer,
            f"{registry.kind} issuance received the wrong issuer",
        )
        capability = getattr(receipt, "capability", None)
        self.__require_fresh_capability(old, capability, kind=registry.kind)
        record = _IssuedReceiptRecord(
            receipt=receipt,
            capability=capability,
            kind=registry.kind,
            route=route,
        )
        owner = _CapabilityOwner(
            capability=capability,
            owner=receipt,
            kind=registry.kind,
        )
        staged = dataclass_replace(
            old,
            version=old.version + 1,
            receipt_records=(*old.receipt_records, record),
            capability_owners=(*old.capability_owners, owner),
        )
        self.__audit(staged)
        require(self.__state is old, "receipt authority root changed before leaf commit")
        self.__state = staged
        return receipt

    @_serial_authority_method
    def issue_parent(
        self,
        registry: _ReceiptIssuanceRegistry,
        *,
        child_receipt: object,
        parent_payload: object,
        route: str,
        fail_at: _ReceiptFailPoint | None,
        fail_kind: _ReceiptInjectedExceptionKind,
    ) -> object:
        route = self.__route(route, context=registry.kind)
        require(
            registry.child_registry is not None
            and type(registry.child_attribute) is str
            and type(registry.edge_kind) is str,
            f"{registry.kind} has no configured child linkage",
        )
        require(
            fail_at is None
            or (route == "dry_probe" and type(fail_at) is _ReceiptFailPoint),
            f"{registry.kind} failure injection changed",
        )
        require(
            type(fail_kind) is _ReceiptInjectedExceptionKind
            and (
                fail_at is not None
                or fail_kind is _ReceiptInjectedExceptionKind.PROJECT
            ),
            f"{registry.kind} injected exception kind changed",
        )
        self.__require_parent_seal(registry, route=route)
        old = self.__state
        child_record = self.__record_for(
            old,
            registry.child_registry,
            child_receipt,
        )
        require(
            child_record.route == route,
            f"{registry.child_registry.kind} was issued in the wrong lane",
        )
        require(
            child_record.parent_edge is None
            and child_record.aggregate_collection is None
            and child_record.aggregate_index is None,
            f"{registry.child_registry.kind} was already collected",
        )
        self.__inject(
            fail_at,
            _ReceiptFailPoint.AFTER_CHILD_VALIDATION,
            fail_kind,
        )

        parent_capability = object()
        edge_capability = object()
        self.__require_fresh_capability(old, parent_capability, kind=registry.kind)
        self.__require_fresh_capability(
            old,
            edge_capability,
            kind=registry.edge_kind,
        )
        if registry.receipt_type is DescriptorV4ExecutionReceipt:
            require(
                type(parent_payload) is tuple
                and len(parent_payload) == 5
                and all(type(field) is str for field in parent_payload),
                "descriptor-v4 parent payload changed",
            )
            parent = DescriptorV4ExecutionReceipt(
                control=parent_payload,
                attack_receipt=child_receipt,
                state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
                issuer=registry.issuer,
                edge_capability=edge_capability,
                capability=parent_capability,
            )
        else:
            require(
                registry.receipt_type is C3NestedMemoAttackExecutionReceipt
                and type(parent_payload) is tuple
                and len(parent_payload) == 3
                and type(parent_payload[0]) is str
                and type(parent_payload[1]) is str
                and type(parent_payload[2]) is tuple
                and len(parent_payload[2]) == 5,
                "C3 nested parent payload changed",
            )
            role_projection = parent_payload[2]
            parent = C3NestedMemoAttackExecutionReceipt(
                label=parent_payload[0],
                expected_detail=parent_payload[1],
                role=role_projection[0],
                inner_projection_constant=role_projection[1],
                begin=role_projection[2],
                end=role_projection[3],
                object_label=role_projection[4],
                sealed_receipt=child_receipt,
                state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
                issuer=registry.issuer,
                edge_capability=edge_capability,
                capability=parent_capability,
            )
        self.__inject(
            fail_at,
            _ReceiptFailPoint.AFTER_PARENT_ALLOCATION,
            fail_kind,
        )
        edge = _ReceiptParentEdge(
            edge_capability=edge_capability,
            parent_receipt=parent,
            parent_capability=parent_capability,
            child_receipt=child_receipt,
            child_capability=child_record.capability,
            kind=registry.edge_kind,
            route=route,
        )
        self.__inject(
            fail_at,
            _ReceiptFailPoint.AFTER_EDGE_ALLOCATION,
            fail_kind,
        )
        parent_record = _IssuedReceiptRecord(
            receipt=parent,
            capability=parent_capability,
            kind=registry.kind,
            route=route,
            child_edge=edge,
        )
        child_updated = dataclass_replace(child_record, parent_edge=edge)
        records = self.__replace_receipt_record(
            old.receipt_records,
            child_record,
            child_updated,
        )
        parent_owner = _CapabilityOwner(
            capability=parent_capability,
            owner=parent,
            kind=registry.kind,
        )
        edge_owner = _CapabilityOwner(
            capability=edge_capability,
            owner=edge,
            kind=registry.edge_kind,
        )
        staged = dataclass_replace(
            old,
            version=old.version + 1,
            receipt_records=(*records, parent_record),
            parent_edges=(*old.parent_edges, edge),
            capability_owners=(
                *old.capability_owners,
                parent_owner,
                edge_owner,
            ),
        )
        self.__inject(
            fail_at,
            _ReceiptFailPoint.AFTER_STATE_STAGING,
            fail_kind,
        )
        self.__audit(staged)
        require(
            self.__state is old,
            "receipt authority root changed during parent transaction",
        )
        self.__require_parent_seal(registry, route=route)
        self.__inject(
            fail_at,
            _ReceiptFailPoint.BEFORE_COMMIT,
            fail_kind,
        )
        self.__state = staged
        return parent

    @_serial_authority_method
    def validate(
        self,
        registry: _ReceiptIssuanceRegistry,
        receipt: object,
        *,
        expected_route: str,
    ) -> None:
        expected_route = self.__route(expected_route, context=registry.kind)
        record = self.__record_for(self.__state, registry, receipt)
        require(
            record.route == expected_route,
            f"{registry.kind} was issued in the wrong lane",
        )

    @_serial_authority_method
    def require_exact_child_edge(
        self,
        registry: _ReceiptIssuanceRegistry,
        parent_receipt: object,
        *,
        child_receipt: object,
        expected_route: str,
    ) -> None:
        expected_route = self.__route(expected_route, context=registry.kind)
        require(
            registry.child_registry is not None
            and type(registry.child_attribute) is str
            and type(registry.edge_kind) is str,
            f"{registry.kind} has no configured child linkage",
        )
        state = self.__state
        parent_record = self.__record_for(state, registry, parent_receipt)
        child_record = self.__record_for(
            state,
            registry.child_registry,
            child_receipt,
        )
        edge = parent_record.child_edge
        require(
            parent_record.route == expected_route
            and child_record.route == expected_route
            and type(edge) is _ReceiptParentEdge
            and child_record.parent_edge is edge
            and any(candidate is edge for candidate in state.parent_edges)
            and edge.parent_receipt is parent_receipt
            and edge.parent_capability is parent_record.capability
            and edge.child_receipt is child_receipt
            and edge.child_capability is child_record.capability
            and edge.edge_capability
            is getattr(parent_receipt, "edge_capability", None)
            and edge.kind == registry.edge_kind
            and edge.route == expected_route
            and getattr(parent_receipt, registry.child_attribute, None)
            is child_receipt,
            f"{registry.kind} exact parent-child edge changed",
        )

    @_serial_authority_method
    def require_unlinked(
        self,
        registry: _ReceiptIssuanceRegistry,
        receipt: object,
        *,
        expected_route: str,
    ) -> None:
        expected_route = self.__route(expected_route, context=registry.kind)
        record = self.__record_for(self.__state, registry, receipt)
        require(
            record.route == expected_route
            and record.parent_edge is None
            and record.aggregate_collection is None
            and record.aggregate_index is None,
            f"{registry.kind} was already collected",
        )

    @_serial_authority_method
    def collect_many_once(
        self,
        registry: _ReceiptIssuanceRegistry,
        receipts: tuple[object, ...],
        *,
        collection: str,
        expected_route: str,
    ) -> None:
        expected_route = self.__route(expected_route, context=registry.kind)
        allowed_collections = (
            {"descriptor-v4 aggregate"}
            if registry.receipt_type is DescriptorV4ExecutionReceipt
            else (
                {
                    "C3 review-ledger aggregate",
                    "C3 local-artifact-parity aggregate",
                }
                if expected_route == "real_lifecycle"
                else {
                    "C3 dry aggregate",
                    "C3 dry reaggregate aggregate",
                }
            )
        )
        require(
            type(receipts) is tuple
            and receipts
            and registry.child_registry is not None
            and type(collection) is str
            and collection in allowed_collections,
            f"{registry.kind} collection label changed",
        )
        old = self.__state
        records = tuple(self.__record_for(old, registry, receipt) for receipt in receipts)
        require(
            len({id(record.receipt) for record in records}) == len(records),
            f"{registry.kind} collection repeats a receipt object",
        )
        require(
            all(
                record.route == expected_route
                and record.aggregate_collection is None
                and record.aggregate_index is None
                for record in records
            ),
            f"{registry.kind} was already collected",
        )
        staged_records = old.receipt_records
        collection_identity = (collection, old.version + 1)
        for index, record in enumerate(records):
            staged_records = self.__replace_receipt_record(
                staged_records,
                record,
                dataclass_replace(
                    record,
                    aggregate_collection=collection_identity,
                    aggregate_index=index,
                ),
            )
        staged = dataclass_replace(
            old,
            version=old.version + 1,
            receipt_records=staged_records,
        )
        self.__audit(staged)
        require(
            self.__state is old,
            "receipt authority root changed before aggregate commit",
        )
        self.__state = staged


_RECEIPT_RUN_AUTHORITY = _ReceiptRunAuthority()


POST_RESTORE_GREEN_REPLAY_COMPLETED = "post_restore_green_replay_completed"
_BASELINE_ATTACK_EXECUTION_ISSUER = object()
_SEALED_NESTED_CANDIDATE_OPERATION_ISSUER = object()
_C3_NESTED_MEMO_ATTACK_EXECUTION_ISSUER = object()
_DESCRIPTOR_V4_EXECUTION_ISSUER = object()
C3_NESTED_SEALED_RECEIPT_LINKAGE = "C3 nested memo attack receipt linkage"
DESCRIPTOR_V4_BASELINE_RECEIPT_LINKAGE = "descriptor-v4 execution receipt linkage"
_BASELINE_ATTACK_EXECUTION_REGISTRY = _ReceiptIssuanceRegistry(
    kind="baseline attack execution receipt",
    receipt_type=BaselineAttackExecutionReceipt,
    issuer=_BASELINE_ATTACK_EXECUTION_ISSUER,
)
_SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY = _ReceiptIssuanceRegistry(
    kind="sealed nested operation receipt",
    receipt_type=SealedNestedCandidateOperationReceipt,
    issuer=_SEALED_NESTED_CANDIDATE_OPERATION_ISSUER,
)
_C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY = _ReceiptIssuanceRegistry(
    kind="C3 nested memo attack execution receipt",
    receipt_type=C3NestedMemoAttackExecutionReceipt,
    issuer=_C3_NESTED_MEMO_ATTACK_EXECUTION_ISSUER,
    child_registry=_SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY,
    child_attribute="sealed_receipt",
    edge_kind=C3_NESTED_SEALED_RECEIPT_LINKAGE,
)
_DESCRIPTOR_V4_EXECUTION_REGISTRY = _ReceiptIssuanceRegistry(
    kind="descriptor-v4 execution receipt",
    receipt_type=DescriptorV4ExecutionReceipt,
    issuer=_DESCRIPTOR_V4_EXECUTION_ISSUER,
    child_registry=_BASELINE_ATTACK_EXECUTION_REGISTRY,
    child_attribute="attack_receipt",
    edge_kind=DESCRIPTOR_V4_BASELINE_RECEIPT_LINKAGE,
)
# These kind facades share one immutable authority root. Its one-assignment commits are
# reviewed-process exception atomic, not crash durable or an authenticity boundary against
# coordinated same-process mutation.


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


@dataclass(frozen=True, slots=True, eq=False)
class _BaselineLifecycleCapability:
    issuer: object
    capability: object


@dataclass(frozen=True, slots=True, eq=False)
class _BaselineLifecycleObservation:
    """One ordinal, identity-bound observation made by the lifecycle authority."""

    permit: _BaselineLifecycleCapability
    ordinal: int
    event_ordinal: int
    event: str
    operation: object
    subject: object
    artifact: object
    snapshot: tuple[tuple[str, int, str], ...]
    detail: str | None
    predecessor: _BaselineLifecycleObservation | None
    issuer: object
    capability: object


@dataclass(frozen=True, slots=True, eq=False)
class _BaselineGreenObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _MutationAdequateObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _FirstRejectionObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _RebaseAdequateObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _SemanticRejectionObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _RestoredObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _ReplayGreenObservation(_BaselineLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _BaselinePermitReceiptEdge:
    """Exact authority-owned permit/capability to receipt/capability edge."""

    permit: _BaselineLifecycleCapability
    permit_capability: object
    receipt: BaselineAttackExecutionReceipt
    receipt_capability: object
    transcript_sha256: str
    kind: str
    route: str


@dataclass(frozen=True, slots=True, eq=False)
class _LifecycleAbortRecord:
    reason: str
    cleanup_failures: tuple[str, ...]
    restored: bool


@dataclass(frozen=True, slots=True, eq=False)
class _BaselineLifecycleRecord:
    permit: _BaselineLifecycleCapability
    label: str
    paths: tuple[str, ...]
    state: str
    root: Path | None
    baseline_snapshot: tuple[tuple[str, int, str], ...] | None
    observations: tuple[_BaselineLifecycleObservation, ...]
    receipt_edge: _BaselinePermitReceiptEdge | None
    abort: _LifecycleAbortRecord | None = None


BASELINE_LIFECYCLE_EVENTS = (
    "baseline",
    "mutation",
    "first_rejection",
    "rebase",
    "semantic_rejection",
    "restoration",
    "green_replay",
)
BASELINE_LIFECYCLE_OBSERVATION_TYPES = (
    _BaselineGreenObservation,
    _MutationAdequateObservation,
    _FirstRejectionObservation,
    _RebaseAdequateObservation,
    _SemanticRejectionObservation,
    _RestoredObservation,
    _ReplayGreenObservation,
)
BASELINE_PERMIT_RECEIPT_LINKAGE = "baseline lifecycle permit receipt linkage"
_BASELINE_LIFECYCLE_OBSERVATION_ISSUER = object()


def _execute_baseline_mutation(
    mutate: Callable[[Path], object],
    root: Path,
) -> object:
    return mutate(root)


_SEALED_BASELINE_LIFECYCLE_MUTATION_PRODUCER = _execute_baseline_mutation


class _BaselineLifecycleAuthority:
    """Execute and retain the causal observations required for a real receipt."""

    def __init__(self) -> None:
        self.__issuer = object()
        self._authority_owner_thread = threading.get_ident()
        self._authority_active = False
        self.__issue_rollback_probe_completed = False

    @_serial_authority_method
    def is_ready_for_issue(self, permit: object) -> bool:
        return self.__record(permit).state == POST_RESTORE_GREEN_REPLAY_COMPLETED

    @_serial_authority_method
    def state_name(self, permit: object) -> str:
        return self.__record(permit).state

    @_serial_authority_method
    def issue_rollback_probe_completed(self) -> bool:
        return self.__issue_rollback_probe_completed

    @_serial_authority_method
    def mark_issue_rollback_probe_completed(self) -> None:
        require(
            self.__issue_rollback_probe_completed is False,
            "baseline receipt rollback probe was already completed",
        )
        self.__issue_rollback_probe_completed = True

    @_serial_authority_method
    def begin(
        self,
        *,
        label: str,
        paths: tuple[str, ...],
    ) -> _BaselineLifecycleCapability:
        require(
            type(label) is str
            and type(paths) is tuple
            and paths
            and all(type(path) is str for path in paths),
            "baseline lifecycle opening transcript changed",
        )
        permit = _BaselineLifecycleCapability(
            issuer=self.__issuer,
            capability=object(),
        )
        record = _BaselineLifecycleRecord(
            permit=permit,
            label=label,
            paths=paths,
            state="pending_baseline",
            root=None,
            baseline_snapshot=None,
            observations=(),
            receipt_edge=None,
        )
        old = _RECEIPT_RUN_AUTHORITY._probe_root()
        owner = _CapabilityOwner(
            capability=permit.capability,
            owner=permit,
            kind="baseline lifecycle permit",
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=old,
            lifecycle_records=(*old.lifecycle_records, record),
            capability_owners=(*old.capability_owners, owner),
        )
        return permit

    def __record(self, permit: object) -> _BaselineLifecycleRecord:
        require(
            type(permit) is _BaselineLifecycleCapability,
            "baseline lifecycle capability has the wrong exact type",
        )
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        matches = tuple(
            record
            for record in state.lifecycle_records
            if type(record) is _BaselineLifecycleRecord and record.permit is permit
        )
        require(
            len(matches) == 1,
            "baseline lifecycle capability was not issued by its authority",
        )
        record = matches[0]
        require(
            record.permit is permit
            and permit.issuer is self.__issuer
            and type(permit.capability) is object,
            "baseline lifecycle capability was not issued by its authority",
        )
        owners = tuple(
            owner
            for owner in state.capability_owners
            if owner.capability is permit.capability
        )
        require(
            len(owners) == 1
            and owners[0].owner is permit
            and owners[0].kind == "baseline lifecycle permit",
            "baseline lifecycle permit capability ownership changed",
        )
        return record

    @staticmethod
    def __replace_record(
        records: tuple[_BaselineLifecycleRecord, ...],
        old: _BaselineLifecycleRecord,
        new: _BaselineLifecycleRecord,
    ) -> tuple[_BaselineLifecycleRecord, ...]:
        replaced = tuple(new if record is old else record for record in records)
        require(
            sum(record is new for record in replaced) == 1,
            "baseline lifecycle record replacement cardinality changed",
        )
        return replaced

    @staticmethod
    def __snapshot(
        root: Path,
        paths: tuple[str, ...],
    ) -> tuple[tuple[str, int, str], ...]:
        require(
            isinstance(root, Path),
            "baseline lifecycle root has the wrong exact type",
        )
        snapshot = []
        for relative in tuple(dict.fromkeys((*paths, CHECKER_RELATIVE))):
            path = root / relative
            raw = path.read_bytes()
            mode = stat.S_IMODE(path.stat().st_mode)
            snapshot.append((relative, mode, hashlib.sha256(raw).hexdigest()))
        return tuple(snapshot)

    def __append_observation(
        self,
        record: _BaselineLifecycleRecord,
        *,
        event: str,
        operation: object,
        subject: object,
        artifact: object,
        snapshot: tuple[tuple[str, int, str], ...],
        detail: str | None,
        next_state: str,
        root: Path | None = None,
        baseline_snapshot: tuple[tuple[str, int, str], ...] | None = None,
    ) -> _BaselineLifecycleObservation:
        old = _RECEIPT_RUN_AUTHORITY._probe_root()
        ordinal = len(record.observations)
        require(
            ordinal < len(BASELINE_LIFECYCLE_EVENTS)
            and event == BASELINE_LIFECYCLE_EVENTS[ordinal]
            and callable(operation)
            and type(snapshot) is tuple
            and (detail is None or type(detail) is str),
            "baseline lifecycle typed observation changed",
        )
        observation_type = BASELINE_LIFECYCLE_OBSERVATION_TYPES[ordinal]
        observation = observation_type(
            permit=record.permit,
            ordinal=ordinal,
            event_ordinal=old.version + 1,
            event=event,
            operation=operation,
            subject=subject,
            artifact=artifact,
            snapshot=snapshot,
            detail=detail,
            predecessor=(record.observations[-1] if record.observations else None),
            issuer=_BASELINE_LIFECYCLE_OBSERVATION_ISSUER,
            capability=object(),
        )
        updated = dataclass_replace(
            record,
            state=next_state,
            root=record.root if root is None else root,
            baseline_snapshot=(
                record.baseline_snapshot
                if baseline_snapshot is None
                else baseline_snapshot
            ),
            observations=(*record.observations, observation),
        )
        owner = _CapabilityOwner(
            capability=observation.capability,
            owner=observation,
            kind=f"baseline lifecycle observation {event}",
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=old,
            lifecycle_records=self.__replace_record(
                old.lifecycle_records,
                record,
                updated,
            ),
            capability_owners=(*old.capability_owners, owner),
        )
        return observation

    @staticmethod
    def __require_callable(current: object, sealed: object, *, label: str) -> None:
        require(
            callable(current) and current is sealed,
            f"baseline lifecycle {label} callable changed",
        )

    @_serial_authority_method
    def observe_baseline(self, permit: object, *, root: Path) -> None:
        record = self.__record(permit)
        require(
            record.state == "pending_baseline" and record.root is None,
            "baseline lifecycle baseline transition changed",
        )
        checker = run_checker
        self.__require_callable(
            checker,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            label="checker",
        )
        process = checker(root, expect_success=True)
        snapshot = self.__snapshot(root, record.paths)
        self.__append_observation(
            record,
            event="baseline",
            operation=checker,
            subject=root,
            artifact=process,
            snapshot=snapshot,
            detail=None,
            next_state="pending_mutation",
            root=root,
            baseline_snapshot=snapshot,
        )

    @_serial_authority_method
    def observe_mutation(
        self,
        permit: object,
        *,
        root: Path,
        mutate: Callable[[Path], object],
    ) -> None:
        record = self.__record(permit)
        require(
            record.state == "pending_mutation"
            and record.root is root
            and type(record.baseline_snapshot) is tuple
            and callable(mutate)
            and self.__snapshot(root, record.paths) == record.baseline_snapshot,
            "baseline lifecycle mutation transition changed",
        )
        producer = _execute_baseline_mutation
        self.__require_callable(
            producer,
            _SEALED_BASELINE_LIFECYCLE_MUTATION_PRODUCER,
            label="mutation producer",
        )
        producer(mutate, root)
        snapshot = self.__snapshot(root, record.paths)
        require(
            snapshot != record.baseline_snapshot,
            "baseline lifecycle mutation did not change the observed paths",
        )
        self.__append_observation(
            record,
            event="mutation",
            operation=producer,
            subject=root,
            artifact=None,
            snapshot=snapshot,
            detail=None,
            next_state="pending_first_rejection",
        )

    @_serial_authority_method
    def observe_first_rejection(
        self,
        permit: object,
        *,
        root: Path,
        expected_fragment: str,
        failure_expectation: FailureExpectation | None,
    ) -> str:
        record = self.__record(permit)
        require(
            record.state == "pending_first_rejection" and record.root is root,
            "baseline lifecycle first-rejection transition changed",
        )
        checker = run_checker
        self.__require_callable(
            checker,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            label="checker",
        )
        process = checker(
            root,
            expect_success=False,
            expected_fragment=expected_fragment,
            failure_expectation=failure_expectation,
        )
        detail = _canonical_checker_failure_detail(process)
        self.__append_observation(
            record,
            event="first_rejection",
            operation=checker,
            subject=root,
            artifact=process,
            snapshot=self.__snapshot(root, record.paths),
            detail=detail,
            next_state="pending_rebase",
        )
        return detail

    @_serial_authority_method
    def observe_rebase(
        self,
        permit: object,
        *,
        root: Path,
        prepare: Callable[[], None],
    ) -> None:
        record = self.__record(permit)
        require(
            record.state == "pending_rebase"
            and record.root is root
            and callable(prepare),
            "baseline lifecycle rebase transition changed",
        )
        rebase = rebase_checker
        self.__require_callable(
            rebase,
            _SEALED_BASELINE_LIFECYCLE_REBASE_CHECKER_CALLABLE,
            label="rebase",
        )
        prepare()
        rebase(root)
        self.__append_observation(
            record,
            event="rebase",
            operation=rebase,
            subject=root,
            artifact=None,
            snapshot=self.__snapshot(root, record.paths),
            detail=None,
            next_state="pending_semantic_rejection",
        )

    @_serial_authority_method
    def observe_semantic_rejection(
        self,
        permit: object,
        *,
        root: Path,
        expected_fragment: str,
        failure_expectation: FailureExpectation | None,
    ) -> str:
        record = self.__record(permit)
        require(
            record.state == "pending_semantic_rejection" and record.root is root,
            "baseline lifecycle semantic-rejection transition changed",
        )
        checker = run_checker
        self.__require_callable(
            checker,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            label="checker",
        )
        process = checker(
            root,
            expect_success=False,
            expected_fragment=expected_fragment,
            failure_expectation=failure_expectation,
        )
        detail = _canonical_checker_failure_detail(process)
        self.__append_observation(
            record,
            event="semantic_rejection",
            operation=checker,
            subject=root,
            artifact=process,
            snapshot=self.__snapshot(root, record.paths),
            detail=detail,
            next_state="pending_restoration",
        )
        return detail

    @_serial_authority_method
    def restore_after_attempt(
        self,
        permit: object,
        *,
        root: Path,
        saved: dict[str, Backup],
    ) -> None:
        record = self.__record(permit)
        restoration = restore
        self.__require_callable(
            restoration,
            _SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE,
            label="restoration",
        )
        restoration(root, saved)
        if record.state != "pending_restoration":
            self.__abort_record(
                record,
                reason="restoration requested before the normal restoration phase",
                cleanup_failures=(),
                restored=True,
            )
            return
        snapshot = self.__snapshot(root, record.paths)
        require(
            record.root is root
            and type(record.baseline_snapshot) is tuple
            and snapshot == record.baseline_snapshot,
            "baseline lifecycle restoration did not recover the baseline snapshot",
        )
        self.__append_observation(
            record,
            event="restoration",
            operation=restoration,
            subject=root,
            artifact=None,
            snapshot=snapshot,
            detail=None,
            next_state="pending_green_replay",
        )

    def __abort_record(
        self,
        record: _BaselineLifecycleRecord,
        *,
        reason: str,
        cleanup_failures: tuple[str, ...],
        restored: bool,
    ) -> None:
        require(
            record.state
            not in {
                "aborted",
                "consumed_by_baseline_attack_execution_receipt",
            }
            and record.receipt_edge is None
            and type(reason) is str
            and reason != ""
            and type(cleanup_failures) is tuple
            and all(type(detail) is str and detail != "" for detail in cleanup_failures)
            and type(restored) is bool,
            "baseline lifecycle abort transition changed",
        )
        old = _RECEIPT_RUN_AUTHORITY._probe_root()
        updated = dataclass_replace(
            record,
            state="aborted",
            abort=_LifecycleAbortRecord(
                reason=reason,
                cleanup_failures=cleanup_failures,
                restored=restored,
            ),
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=old,
            lifecycle_records=self.__replace_record(
                old.lifecycle_records,
                record,
                updated,
            ),
        )

    @_serial_authority_method
    def abort_after_cleanup(
        self,
        permit: object,
        *,
        reason: str,
        cleanup_failures: tuple[str, ...],
        restored: bool,
    ) -> None:
        self.__abort_record(
            self.__record(permit),
            reason=reason,
            cleanup_failures=cleanup_failures,
            restored=restored,
        )

    @_serial_authority_method
    def observe_green_replay(self, permit: object, *, root: Path) -> None:
        record = self.__record(permit)
        require(
            record.state == "pending_green_replay" and record.root is root,
            "baseline lifecycle green-replay transition changed",
        )
        checker = run_checker
        self.__require_callable(
            checker,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            label="checker",
        )
        process = checker(root, expect_success=True)
        prior_processes = tuple(
            observation.artifact
            for observation in record.observations
            if observation.event
            in {"baseline", "first_rejection", "semantic_rejection"}
        )
        require(
            all(process is not prior for prior in prior_processes),
            "baseline lifecycle green replay was not a distinct observation",
        )
        snapshot = self.__snapshot(root, record.paths)
        require(
            snapshot == record.baseline_snapshot,
            "baseline lifecycle green replay did not use the restored snapshot",
        )
        self.__append_observation(
            record,
            event="green_replay",
            operation=checker,
            subject=root,
            artifact=process,
            snapshot=snapshot,
            detail=None,
            next_state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
        )

    @_serial_authority_method
    def issue_completed(
        self,
        permit: object,
        *,
        fail_at: _ReceiptFailPoint | None = None,
        fail_kind: _ReceiptInjectedExceptionKind = (
            _ReceiptInjectedExceptionKind.PROJECT
        ),
    ) -> BaselineAttackExecutionReceipt:
        require(
            fail_at is None or type(fail_at) is _ReceiptFailPoint,
            "baseline receipt failure injection changed",
        )
        require(
            type(fail_kind) is _ReceiptInjectedExceptionKind
            and (
                fail_at is not None
                or fail_kind is _ReceiptInjectedExceptionKind.PROJECT
            ),
            "baseline receipt injected exception kind changed",
        )
        record = self.__record(permit)
        observations = record.observations
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        observation_processes = tuple(
            observations[index].artifact for index in (0, 2, 4, 6)
        ) if len(observations) == 7 else ()
        require(
            record.state == POST_RESTORE_GREEN_REPLAY_COMPLETED
            and len(observations) == len(BASELINE_LIFECYCLE_EVENTS)
            and tuple(type(observation) for observation in observations)
            == BASELINE_LIFECYCLE_OBSERVATION_TYPES
            and tuple(observation.event for observation in observations)
            == BASELINE_LIFECYCLE_EVENTS
            and tuple(observation.ordinal for observation in observations)
            == tuple(range(len(BASELINE_LIFECYCLE_EVENTS)))
            and all(type(observation.event_ordinal) is int for observation in observations)
            and tuple(observation.event_ordinal for observation in observations)
            == tuple(sorted(observation.event_ordinal for observation in observations))
            and len({observation.event_ordinal for observation in observations})
            == len(observations)
            and all(observation.permit is record.permit for observation in observations)
            and all(observation.subject is record.root for observation in observations)
            and observations[0].predecessor is None
            and all(
                observations[index].predecessor is observations[index - 1]
                for index in range(1, len(observations))
            )
            and all(
                observation.issuer is _BASELINE_LIFECYCLE_OBSERVATION_ISSUER
                and type(observation.capability) is object
                and sum(
                    owner.capability is observation.capability
                    and owner.owner is observation
                    for owner in state.capability_owners
                )
                == 1
                for observation in observations
            )
            and len({id(process) for process in observation_processes}) == 4
            and observations[0].operation
            is _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE
            and observations[1].operation
            is _SEALED_BASELINE_LIFECYCLE_MUTATION_PRODUCER
            and observations[2].operation
            is _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE
            and observations[3].operation
            is _SEALED_BASELINE_LIFECYCLE_REBASE_CHECKER_CALLABLE
            and observations[4].operation
            is _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE
            and observations[5].operation
            is _SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE
            and observations[6].operation
            is _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE
            and observations[1].artifact is None
            and observations[3].artifact is None
            and observations[5].artifact is None
            and record.abort is None
            and type(observations[2].detail) is str
            and type(observations[4].detail) is str,
            "baseline lifecycle causal observation inventory changed",
        )
        _inject_receipt_transaction_failure(
            fail_at,
            _ReceiptFailPoint.AFTER_CHILD_VALIDATION,
            fail_kind,
        )
        transcript_raw = (
            json.dumps(
                (
                    record.label,
                    record.paths,
                    tuple(
                        (
                            observation.ordinal,
                            observation.event_ordinal,
                            observation.event,
                            observation.snapshot,
                            observation.detail,
                        )
                        for observation in observations
                    ),
                ),
                ensure_ascii=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
        transcript_sha256 = hashlib.sha256(transcript_raw).hexdigest()
        receipt = BaselineAttackExecutionReceipt(
            label=record.label,
            paths=record.paths,
            first_detail=observations[2].detail,
            semantic_detail=observations[4].detail,
            state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
            issuer=_BASELINE_ATTACK_EXECUTION_ISSUER,
            capability=object(),
            lifecycle_permit=record.permit,
        )
        _inject_receipt_transaction_failure(
            fail_at,
            _ReceiptFailPoint.AFTER_PARENT_ALLOCATION,
            fail_kind,
        )
        edge = _BaselinePermitReceiptEdge(
            permit=record.permit,
            permit_capability=record.permit.capability,
            receipt=receipt,
            receipt_capability=receipt.capability,
            transcript_sha256=transcript_sha256,
            kind=BASELINE_PERMIT_RECEIPT_LINKAGE,
            route="real_lifecycle",
        )
        _inject_receipt_transaction_failure(
            fail_at,
            _ReceiptFailPoint.AFTER_EDGE_ALLOCATION,
            fail_kind,
        )
        receipt_record = _IssuedReceiptRecord(
            receipt=receipt,
            capability=receipt.capability,
            kind=_BASELINE_ATTACK_EXECUTION_REGISTRY.kind,
            route="real_lifecycle",
        )
        receipt_owner = _CapabilityOwner(
            capability=receipt.capability,
            owner=receipt,
            kind=_BASELINE_ATTACK_EXECUTION_REGISTRY.kind,
        )
        updated = dataclass_replace(
            record,
            state="consumed_by_baseline_attack_execution_receipt",
            receipt_edge=edge,
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=state,
            lifecycle_records=self.__replace_record(
                state.lifecycle_records,
                record,
                updated,
            ),
            permit_receipt_edges=(*state.permit_receipt_edges, edge),
            receipt_records=(*state.receipt_records, receipt_record),
            capability_owners=(*state.capability_owners, receipt_owner),
            fail_at=fail_at,
            fail_kind=fail_kind,
        )
        return receipt

    @_serial_authority_method
    def require_exact_receipt_edge(
        self,
        permit: object,
        receipt: BaselineAttackExecutionReceipt,
    ) -> None:
        record = self.__record(permit)
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        edge = record.receipt_edge
        _BASELINE_ATTACK_EXECUTION_REGISTRY.validate(
            receipt,
            expected_route="real_lifecycle",
        )
        require(
            record.state == "consumed_by_baseline_attack_execution_receipt"
            and type(edge) is _BaselinePermitReceiptEdge
            and edge.permit is permit
            and edge.permit_capability is permit.capability
            and edge.receipt is receipt
            and edge.receipt_capability is receipt.capability
            and type(edge.transcript_sha256) is str
            and re.fullmatch(r"[0-9a-f]{64}", edge.transcript_sha256) is not None
            and edge.kind == BASELINE_PERMIT_RECEIPT_LINKAGE
            and edge.route == "real_lifecycle"
            and receipt.lifecycle_permit is permit
            and sum(candidate is edge for candidate in state.permit_receipt_edges) == 1,
            "baseline lifecycle exact permit-to-receipt edge changed",
        )


_BASELINE_LIFECYCLE_AUTHORITY = _BaselineLifecycleAuthority()


def _require_exact_injected_receipt_failure(
    error: BaseException,
    *,
    fail_at: _ReceiptFailPoint,
    fail_kind: _ReceiptInjectedExceptionKind,
) -> None:
    detail = f"receipt transaction injected at {fail_at.value}"
    if fail_kind is _ReceiptInjectedExceptionKind.PROJECT:
        require(
            type(error) is _InjectedReceiptFailure and str(error) == detail,
            "project receipt injection reached the wrong failure",
        )
        return
    if fail_kind is _ReceiptInjectedExceptionKind.MEMORY:
        require(
            type(error) is MemoryError and str(error) == detail,
            "memory receipt injection reached the wrong failure",
        )
        return
    if fail_kind is _ReceiptInjectedExceptionKind.KEYBOARD:
        require(
            type(error) is KeyboardInterrupt and str(error) == detail,
            "keyboard receipt injection reached the wrong failure",
        )
        return
    require(
        fail_kind is _ReceiptInjectedExceptionKind.SYSTEM_EXIT_ZERO
        and type(error) is SystemExit
        and type(error.code) is int
        and error.code == 0,
        "zero-exit receipt injection reached the wrong failure",
    )


def _probe_baseline_receipt_atomic_rollback(
    permit: _BaselineLifecycleCapability,
) -> None:
    if _BASELINE_LIFECYCLE_AUTHORITY.issue_rollback_probe_completed():
        return
    for fail_at in _ReceiptFailPoint:
        for fail_kind in _ReceiptInjectedExceptionKind:
            old_root = _RECEIPT_RUN_AUTHORITY._probe_root()
            old_projection = _RECEIPT_RUN_AUTHORITY.audit_projection()
            try:
                _BASELINE_LIFECYCLE_AUTHORITY.issue_completed(
                    permit,
                    fail_at=fail_at,
                    fail_kind=fail_kind,
                )
            except BaseException as error:
                _require_exact_injected_receipt_failure(
                    error,
                    fail_at=fail_at,
                    fail_kind=fail_kind,
                )
            else:
                raise SelfTestError(
                    "baseline receipt rollback injection survived: "
                    f"{fail_at.value}/{fail_kind.value}"
                )
            require(
                _RECEIPT_RUN_AUTHORITY._probe_root() is old_root
                and _RECEIPT_RUN_AUTHORITY.audit_projection() == old_projection
                and _BASELINE_LIFECYCLE_AUTHORITY.is_ready_for_issue(permit),
                "baseline receipt rollback changed the immutable authority root",
            )
    _BASELINE_LIFECYCLE_AUTHORITY.mark_issue_rollback_probe_completed()


def _issue_baseline_attack_execution_receipt(
    *,
    lifecycle_capability: object = None,
) -> BaselineAttackExecutionReceipt:
    if (
        type(lifecycle_capability) is _BaselineLifecycleCapability
        and _BASELINE_LIFECYCLE_AUTHORITY.is_ready_for_issue(lifecycle_capability)
    ):
        _probe_baseline_receipt_atomic_rollback(lifecycle_capability)
    return _BASELINE_LIFECYCLE_AUTHORITY.issue_completed(lifecycle_capability)


_SEALED_BASELINE_ATTACK_EXECUTION_RECEIPT_ISSUER = (
    _issue_baseline_attack_execution_receipt
)


@dataclass(frozen=True, slots=True, eq=False)
class _SealedLifecycleCapability:
    issuer: object
    capability: object


@dataclass(frozen=True, slots=True, eq=False)
class _SealedLifecycleObservation:
    permit: _SealedLifecycleCapability
    ordinal: int
    event_ordinal: int
    event: str
    operation: object
    subject: Path
    artifact: object
    snapshot: tuple[tuple[str, int, str], ...]
    status_sha256: str
    detail: str | None
    predecessor: _SealedLifecycleObservation | None
    issuer: object
    capability: object


@dataclass(frozen=True, slots=True, eq=False)
class _SealedBodyRejectionObservation(_SealedLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _SealedRestoredObservation(_SealedLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _SealedReplayGreenObservation(_SealedLifecycleObservation):
    pass


@dataclass(frozen=True, slots=True, eq=False)
class _SealedPermitReceiptEdge:
    permit: _SealedLifecycleCapability
    permit_capability: object
    receipt: SealedNestedCandidateOperationReceipt
    receipt_capability: object
    transcript_sha256: str
    kind: str
    route: str


@dataclass(frozen=True, slots=True, eq=False)
class _SealedLifecycleRecord:
    permit: _SealedLifecycleCapability
    label: str
    expected_detail: str
    state: str
    root: Path
    baseline_status: bytes
    baseline_snapshot: tuple[tuple[str, int, str], ...]
    observations: tuple[_SealedLifecycleObservation, ...]
    receipt_edge: _SealedPermitReceiptEdge | None
    abort: _LifecycleAbortRecord | None = None


SEALED_LIFECYCLE_EVENTS = (
    "body_rejection",
    "restoration",
    "green_replay",
)
SEALED_LIFECYCLE_OBSERVATION_TYPES = (
    _SealedBodyRejectionObservation,
    _SealedRestoredObservation,
    _SealedReplayGreenObservation,
)
SEALED_PERMIT_RECEIPT_LINKAGE = "sealed lifecycle permit receipt linkage"
_SEALED_LIFECYCLE_OBSERVATION_ISSUER = object()


def _execute_sealed_operation_body(body: Callable[[], None]) -> None:
    body()


_SEALED_OPERATION_BODY_PRODUCER = _execute_sealed_operation_body


class _SealedLifecycleAuthority:
    """Bind a real sealed receipt to operation, restoration, and replay facts."""

    def __init__(self) -> None:
        self.__issuer = object()
        self._authority_owner_thread = threading.get_ident()
        self._authority_active = False
        self.__issue_rollback_probe_completed = False

    @staticmethod
    def __snapshot(root: Path) -> tuple[tuple[str, int, str], ...]:
        require(
            isinstance(root, Path),
            "sealed lifecycle root has the wrong exact type",
        )
        snapshot = []
        for relative in (PORTABILITY_CORRECTIVE_EVIDENCE, CHECKER_RELATIVE):
            path = root / relative
            raw = path.read_bytes()
            snapshot.append(
                (
                    relative,
                    stat.S_IMODE(path.stat().st_mode),
                    hashlib.sha256(raw).hexdigest(),
                )
            )
        return tuple(snapshot)

    @staticmethod
    def __replace_record(
        records: tuple[_SealedLifecycleRecord, ...],
        old: _SealedLifecycleRecord,
        new: _SealedLifecycleRecord,
    ) -> tuple[_SealedLifecycleRecord, ...]:
        replaced = tuple(new if record is old else record for record in records)
        require(
            sum(record is new for record in replaced) == 1,
            "sealed lifecycle record replacement cardinality changed",
        )
        return replaced

    def __record(self, permit: object) -> _SealedLifecycleRecord:
        require(
            type(permit) is _SealedLifecycleCapability,
            "sealed lifecycle capability has the wrong exact type",
        )
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        matches = tuple(
            record
            for record in state.sealed_lifecycle_records
            if type(record) is _SealedLifecycleRecord and record.permit is permit
        )
        require(
            len(matches) == 1,
            "sealed lifecycle capability was not issued by its authority",
        )
        record = matches[0]
        owners = tuple(
            owner
            for owner in state.capability_owners
            if owner.capability is permit.capability
        )
        require(
            permit.issuer is self.__issuer
            and type(permit.capability) is object
            and len(owners) == 1
            and owners[0].owner is permit
            and owners[0].kind == "sealed lifecycle permit",
            "sealed lifecycle permit capability ownership changed",
        )
        return record

    @staticmethod
    def __require_callable(current: object, sealed: object, *, label: str) -> None:
        require(
            callable(current) and current is sealed,
            f"sealed lifecycle {label} callable changed",
        )

    def __append_observation(
        self,
        record: _SealedLifecycleRecord,
        *,
        event: str,
        operation: object,
        artifact: object,
        snapshot: tuple[tuple[str, int, str], ...],
        status: bytes,
        detail: str | None,
        next_state: str,
    ) -> _SealedLifecycleObservation:
        old = _RECEIPT_RUN_AUTHORITY._probe_root()
        ordinal = len(record.observations)
        require(
            ordinal < len(SEALED_LIFECYCLE_EVENTS)
            and event == SEALED_LIFECYCLE_EVENTS[ordinal]
            and callable(operation)
            and type(snapshot) is tuple
            and type(status) is bytes
            and (detail is None or type(detail) is str),
            "sealed lifecycle typed observation changed",
        )
        observation_type = SEALED_LIFECYCLE_OBSERVATION_TYPES[ordinal]
        observation = observation_type(
            permit=record.permit,
            ordinal=ordinal,
            event_ordinal=old.version + 1,
            event=event,
            operation=operation,
            subject=record.root,
            artifact=artifact,
            snapshot=snapshot,
            status_sha256=hashlib.sha256(status).hexdigest(),
            detail=detail,
            predecessor=(record.observations[-1] if record.observations else None),
            issuer=_SEALED_LIFECYCLE_OBSERVATION_ISSUER,
            capability=object(),
        )
        updated = dataclass_replace(
            record,
            state=next_state,
            observations=(*record.observations, observation),
        )
        owner = _CapabilityOwner(
            capability=observation.capability,
            owner=observation,
            kind=f"sealed lifecycle observation {event}",
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=old,
            sealed_lifecycle_records=self.__replace_record(
                old.sealed_lifecycle_records,
                record,
                updated,
            ),
            capability_owners=(*old.capability_owners, owner),
        )
        return observation

    @_serial_authority_method
    def begin(
        self,
        *,
        label: str,
        expected_detail: str,
        root: Path,
    ) -> _SealedLifecycleCapability:
        require(
            type(label) is str
            and label != ""
            and type(expected_detail) is str
            and expected_detail != ""
            and isinstance(root, Path),
            "sealed lifecycle opening transcript changed",
        )
        permit = _SealedLifecycleCapability(
            issuer=self.__issuer,
            capability=object(),
        )
        record = _SealedLifecycleRecord(
            permit=permit,
            label=label,
            expected_detail=expected_detail,
            state="pending_body",
            root=root,
            baseline_status=_exact_git_status(root),
            baseline_snapshot=self.__snapshot(root),
            observations=(),
            receipt_edge=None,
        )
        old = _RECEIPT_RUN_AUTHORITY._probe_root()
        owner = _CapabilityOwner(
            capability=permit.capability,
            owner=permit,
            kind="sealed lifecycle permit",
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=old,
            sealed_lifecycle_records=(*old.sealed_lifecycle_records, record),
            capability_owners=(*old.capability_owners, owner),
        )
        return permit

    @_serial_authority_method
    def observe_body_rejection(
        self,
        permit: object,
        *,
        body: Callable[[], None],
    ) -> str:
        record = self.__record(permit)
        require(
            record.state == "pending_body" and callable(body),
            "sealed lifecycle body transition changed",
        )
        producer = _execute_sealed_operation_body
        self.__require_callable(
            producer,
            _SEALED_OPERATION_BODY_PRODUCER,
            label="body producer",
        )
        producer(body)
        snapshot = self.__snapshot(record.root)
        status = _exact_git_status(record.root)
        require(
            snapshot != record.baseline_snapshot and type(status) is bytes,
            "sealed lifecycle body did not create a nonempty exact file delta",
        )
        checker = run_checker
        self.__require_callable(
            checker,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            label="checker",
        )
        process = checker(
            record.root,
            expect_success=False,
            expected_fragment=record.expected_detail,
            failure_expectation=caller_held_exact_failure_expectation(
                record.expected_detail
            ),
        )
        detail = _canonical_checker_failure_detail(process)
        self.__append_observation(
            record,
            event="body_rejection",
            operation=producer,
            artifact=process,
            snapshot=snapshot,
            status=status,
            detail=detail,
            next_state="pending_restoration",
        )
        return detail

    @_serial_authority_method
    def observe_restoration(
        self,
        permit: object,
        *,
        saved: dict[str, Backup],
    ) -> None:
        record = self.__record(permit)
        require(
            record.state == "pending_restoration",
            "sealed lifecycle restoration transition changed",
        )
        restoration = restore
        self.__require_callable(
            restoration,
            _SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE,
            label="restoration",
        )
        restoration(record.root, saved)
        require_backup_restored(record.root, saved)
        status = _exact_git_status(record.root)
        snapshot = self.__snapshot(record.root)
        require(
            status == record.baseline_status
            and snapshot == record.baseline_snapshot,
            "sealed lifecycle restoration did not recover the baseline endpoint",
        )
        self.__append_observation(
            record,
            event="restoration",
            operation=restoration,
            artifact=None,
            snapshot=snapshot,
            status=status,
            detail=None,
            next_state="pending_green_replay",
        )

    @_serial_authority_method
    def observe_green_replay(self, permit: object) -> None:
        record = self.__record(permit)
        require(
            record.state == "pending_green_replay",
            "sealed lifecycle green-replay transition changed",
        )
        checker = run_checker
        self.__require_callable(
            checker,
            _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE,
            label="checker",
        )
        process = checker(record.root, expect_success=True)
        first_process = record.observations[0].artifact
        status = _exact_git_status(record.root)
        snapshot = self.__snapshot(record.root)
        require(
            process is not first_process
            and status == record.baseline_status
            and snapshot == record.baseline_snapshot,
            "sealed lifecycle green replay was not fresh at the restored endpoint",
        )
        self.__append_observation(
            record,
            event="green_replay",
            operation=checker,
            artifact=process,
            snapshot=snapshot,
            status=status,
            detail=None,
            next_state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
        )

    @_serial_authority_method
    def abort_after_cleanup(
        self,
        permit: object,
        *,
        reason: str,
        cleanup_failures: tuple[str, ...],
        restored: bool,
    ) -> None:
        record = self.__record(permit)
        require(
            record.state
            not in {
                "aborted",
                "consumed_by_sealed_nested_operation_receipt",
            }
            and record.receipt_edge is None
            and type(reason) is str
            and reason != ""
            and type(cleanup_failures) is tuple
            and all(type(detail) is str and detail != "" for detail in cleanup_failures)
            and type(restored) is bool,
            "sealed lifecycle abort transition changed",
        )
        old = _RECEIPT_RUN_AUTHORITY._probe_root()
        updated = dataclass_replace(
            record,
            state="aborted",
            abort=_LifecycleAbortRecord(
                reason=reason,
                cleanup_failures=cleanup_failures,
                restored=restored,
            ),
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=old,
            sealed_lifecycle_records=self.__replace_record(
                old.sealed_lifecycle_records,
                record,
                updated,
            ),
        )

    @_serial_authority_method
    def is_ready_for_issue(self, permit: object) -> bool:
        return self.__record(permit).state == POST_RESTORE_GREEN_REPLAY_COMPLETED

    @_serial_authority_method
    def issue_rollback_probe_completed(self) -> bool:
        return self.__issue_rollback_probe_completed

    @_serial_authority_method
    def mark_issue_rollback_probe_completed(self) -> None:
        require(
            self.__issue_rollback_probe_completed is False,
            "sealed receipt rollback probe was already completed",
        )
        self.__issue_rollback_probe_completed = True

    @_serial_authority_method
    def issue_completed(
        self,
        permit: object,
        *,
        fail_at: _ReceiptFailPoint | None = None,
        fail_kind: _ReceiptInjectedExceptionKind = (
            _ReceiptInjectedExceptionKind.PROJECT
        ),
    ) -> SealedNestedCandidateOperationReceipt:
        require(
            fail_at is None or type(fail_at) is _ReceiptFailPoint,
            "sealed receipt failure injection changed",
        )
        require(
            type(fail_kind) is _ReceiptInjectedExceptionKind
            and (
                fail_at is not None
                or fail_kind is _ReceiptInjectedExceptionKind.PROJECT
            ),
            "sealed receipt injected exception kind changed",
        )
        record = self.__record(permit)
        observations = record.observations
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        require(
            record.state == POST_RESTORE_GREEN_REPLAY_COMPLETED
            and record.abort is None
            and len(observations) == len(SEALED_LIFECYCLE_EVENTS)
            and tuple(type(observation) for observation in observations)
            == SEALED_LIFECYCLE_OBSERVATION_TYPES
            and tuple(observation.event for observation in observations)
            == SEALED_LIFECYCLE_EVENTS
            and tuple(observation.ordinal for observation in observations)
            == tuple(range(len(SEALED_LIFECYCLE_EVENTS)))
            and observations[0].operation is _SEALED_OPERATION_BODY_PRODUCER
            and observations[1].operation
            is _SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE
            and observations[2].operation
            is _SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE
            and type(observations[0].artifact) is subprocess.CompletedProcess
            and observations[1].artifact is None
            and type(observations[2].artifact) is subprocess.CompletedProcess
            and observations[0].artifact is not observations[2].artifact
            and type(observations[0].detail) is str
            and observations[1].detail is None
            and observations[2].detail is None
            and observations[1].snapshot == record.baseline_snapshot
            and observations[2].snapshot == record.baseline_snapshot
            and observations[1].status_sha256
            == hashlib.sha256(record.baseline_status).hexdigest()
            and observations[2].status_sha256
            == hashlib.sha256(record.baseline_status).hexdigest(),
            "sealed lifecycle causal observation inventory changed",
        )
        _inject_receipt_transaction_failure(
            fail_at,
            _ReceiptFailPoint.AFTER_CHILD_VALIDATION,
            fail_kind,
        )
        transcript_raw = (
            json.dumps(
                (
                    record.label,
                    record.expected_detail,
                    tuple(
                        (
                            observation.ordinal,
                            observation.event_ordinal,
                            observation.event,
                            observation.snapshot,
                            observation.status_sha256,
                            observation.detail,
                        )
                        for observation in observations
                    ),
                ),
                ensure_ascii=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
        transcript_sha256 = hashlib.sha256(transcript_raw).hexdigest()
        baseline_status_sha256 = hashlib.sha256(record.baseline_status).hexdigest()
        receipt = SealedNestedCandidateOperationReceipt(
            label=record.label,
            pre_status_sha256=baseline_status_sha256,
            post_status_sha256=observations[2].status_sha256,
            status_equal=True,
            state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
            issuer=_SEALED_NESTED_CANDIDATE_OPERATION_ISSUER,
            capability=object(),
            lifecycle_permit=record.permit,
        )
        _inject_receipt_transaction_failure(
            fail_at,
            _ReceiptFailPoint.AFTER_PARENT_ALLOCATION,
            fail_kind,
        )
        edge = _SealedPermitReceiptEdge(
            permit=record.permit,
            permit_capability=record.permit.capability,
            receipt=receipt,
            receipt_capability=receipt.capability,
            transcript_sha256=transcript_sha256,
            kind=SEALED_PERMIT_RECEIPT_LINKAGE,
            route="real_lifecycle",
        )
        _inject_receipt_transaction_failure(
            fail_at,
            _ReceiptFailPoint.AFTER_EDGE_ALLOCATION,
            fail_kind,
        )
        receipt_record = _IssuedReceiptRecord(
            receipt=receipt,
            capability=receipt.capability,
            kind=_SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.kind,
            route="real_lifecycle",
        )
        receipt_owner = _CapabilityOwner(
            capability=receipt.capability,
            owner=receipt,
            kind=_SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.kind,
        )
        updated = dataclass_replace(
            record,
            state="consumed_by_sealed_nested_operation_receipt",
            receipt_edge=edge,
        )
        _RECEIPT_RUN_AUTHORITY.commit_lifecycle_components(
            expected_root=state,
            sealed_lifecycle_records=self.__replace_record(
                state.sealed_lifecycle_records,
                record,
                updated,
            ),
            sealed_permit_receipt_edges=(
                *state.sealed_permit_receipt_edges,
                edge,
            ),
            receipt_records=(*state.receipt_records, receipt_record),
            capability_owners=(*state.capability_owners, receipt_owner),
            fail_at=fail_at,
            fail_kind=fail_kind,
        )
        return receipt

    @_serial_authority_method
    def require_exact_receipt_edge(
        self,
        permit: object,
        receipt: SealedNestedCandidateOperationReceipt,
    ) -> None:
        record = self.__record(permit)
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        edge = record.receipt_edge
        _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.validate(
            receipt,
            expected_route="real_lifecycle",
        )
        require(
            record.state == "consumed_by_sealed_nested_operation_receipt"
            and type(edge) is _SealedPermitReceiptEdge
            and edge.permit is permit
            and edge.permit_capability is permit.capability
            and edge.receipt is receipt
            and edge.receipt_capability is receipt.capability
            and re.fullmatch(r"[0-9a-f]{64}", edge.transcript_sha256) is not None
            and edge.kind == SEALED_PERMIT_RECEIPT_LINKAGE
            and edge.route == "real_lifecycle"
            and receipt.lifecycle_permit is permit
            and sum(
                candidate is edge
                for candidate in state.sealed_permit_receipt_edges
            )
            == 1,
            "sealed lifecycle exact permit-to-receipt edge changed",
        )


_SEALED_LIFECYCLE_AUTHORITY = _SealedLifecycleAuthority()


def _probe_sealed_receipt_atomic_rollback(
    permit: _SealedLifecycleCapability,
) -> None:
    if _SEALED_LIFECYCLE_AUTHORITY.issue_rollback_probe_completed():
        return
    for fail_at in _ReceiptFailPoint:
        for fail_kind in _ReceiptInjectedExceptionKind:
            old_root = _RECEIPT_RUN_AUTHORITY._probe_root()
            old_projection = _RECEIPT_RUN_AUTHORITY.audit_projection()
            try:
                _SEALED_LIFECYCLE_AUTHORITY.issue_completed(
                    permit,
                    fail_at=fail_at,
                    fail_kind=fail_kind,
                )
            except BaseException as error:
                _require_exact_injected_receipt_failure(
                    error,
                    fail_at=fail_at,
                    fail_kind=fail_kind,
                )
            else:
                raise SelfTestError(
                    "sealed receipt rollback injection survived: "
                    f"{fail_at.value}/{fail_kind.value}"
                )
            require(
                _RECEIPT_RUN_AUTHORITY._probe_root() is old_root
                and _RECEIPT_RUN_AUTHORITY.audit_projection() == old_projection
                and _SEALED_LIFECYCLE_AUTHORITY.is_ready_for_issue(permit),
                "sealed receipt rollback changed the immutable authority root",
            )
    _SEALED_LIFECYCLE_AUTHORITY.mark_issue_rollback_probe_completed()


def _issue_sealed_nested_candidate_operation_receipt(
    *,
    lifecycle_capability: object = None,
) -> SealedNestedCandidateOperationReceipt:
    if (
        type(lifecycle_capability) is _SealedLifecycleCapability
        and _SEALED_LIFECYCLE_AUTHORITY.is_ready_for_issue(lifecycle_capability)
    ):
        _probe_sealed_receipt_atomic_rollback(lifecycle_capability)
    return _SEALED_LIFECYCLE_AUTHORITY.issue_completed(lifecycle_capability)


_SEALED_NESTED_OPERATION_RECEIPT_ISSUER_CALLABLE = (
    _issue_sealed_nested_candidate_operation_receipt
)


def _issue_c3_nested_memo_attack_execution_receipt(
    *,
    label: str,
    expected_detail: str,
    role_projection: tuple[
        str,
        str | None,
        bytes | None,
        bytes | None,
        str | None,
    ],
    sealed_receipt: SealedNestedCandidateOperationReceipt,
) -> C3NestedMemoAttackExecutionReceipt:
    _validate_sealed_nested_candidate_operation_receipt(
        sealed_receipt,
        expected_label=label,
    )
    receipt = _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue_parent(
        child_receipt=sealed_receipt,
        parent_payload=(label, expected_detail, role_projection),
        route="real_lifecycle",
    )
    require(
        type(receipt) is C3NestedMemoAttackExecutionReceipt,
        "C3 nested issuer returned the wrong exact type",
    )
    return receipt


_SEALED_C3_NESTED_REAL_ISSUER_CALLABLE = (
    _issue_c3_nested_memo_attack_execution_receipt
)


def _issue_descriptor_v4_execution_receipt(
    *,
    control: tuple[str, str, str, str, str],
    attack_receipt: BaselineAttackExecutionReceipt,
) -> DescriptorV4ExecutionReceipt:
    receipt = _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue_parent(
        child_receipt=attack_receipt,
        parent_payload=control,
        route="real_lifecycle",
    )
    require(
        type(receipt) is DescriptorV4ExecutionReceipt,
        "descriptor-v4 issuer returned the wrong exact type",
    )
    return receipt


_SEALED_DESCRIPTOR_V4_REAL_ISSUER_CALLABLE = _issue_descriptor_v4_execution_receipt


def _validate_baseline_attack_execution_receipt(
    receipt: object,
    *,
    expected_label: str,
    expected_paths: tuple[str, ...],
    expected_first_detail: str,
    expected_semantic_detail: str,
    _expected_route: str = "real_lifecycle",
) -> BaselineAttackExecutionReceipt:
    require(
        type(receipt) is BaselineAttackExecutionReceipt,
        "baseline attack execution receipt has the wrong exact type",
    )
    _BASELINE_ATTACK_EXECUTION_REGISTRY.validate(
        receipt,
        expected_route=_expected_route,
    )
    require(
        getattr(receipt, "issuer", None) is _BASELINE_ATTACK_EXECUTION_ISSUER,
        "baseline attack execution receipt has the wrong issuer",
    )
    require(
        type(getattr(receipt, "capability", None)) is object,
        "baseline attack execution receipt capability has the wrong type",
    )
    require(
        type(getattr(receipt, "state", None)) is str
        and receipt.state == POST_RESTORE_GREEN_REPLAY_COMPLETED,
        "baseline attack execution receipt has the wrong completion state",
    )
    require(
        type(getattr(receipt, "label", None)) is str
        and receipt.label == expected_label,
        "baseline attack execution receipt label changed",
    )
    require(
        type(getattr(receipt, "paths", None)) is tuple
        and all(type(path) is str for path in receipt.paths)
        and receipt.paths == expected_paths,
        "baseline attack execution receipt ordered paths changed",
    )
    require(
        type(getattr(receipt, "first_detail", None)) is str
        and receipt.first_detail == expected_first_detail,
        "baseline attack execution receipt first rejection detail changed",
    )
    require(
        type(getattr(receipt, "semantic_detail", None)) is str
        and receipt.semantic_detail == expected_semantic_detail,
        "baseline attack execution receipt semantic rejection detail changed",
    )
    if _expected_route == "real_lifecycle":
        _BASELINE_LIFECYCLE_AUTHORITY.require_exact_receipt_edge(
            getattr(receipt, "lifecycle_permit", None),
            receipt,
        )
    else:
        require(
            getattr(receipt, "lifecycle_permit", None) is None,
            "dry baseline receipt unexpectedly has a lifecycle permit",
        )
    return receipt


def _validate_sealed_nested_candidate_operation_receipt(
    receipt: object,
    *,
    expected_label: str,
    _expected_route: str = "real_lifecycle",
) -> SealedNestedCandidateOperationReceipt:
    require(
        type(receipt) is SealedNestedCandidateOperationReceipt,
        "sealed nested operation receipt has the wrong exact type",
    )
    _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.validate(
        receipt,
        expected_route=_expected_route,
    )
    require(
        getattr(receipt, "issuer", None)
        is _SEALED_NESTED_CANDIDATE_OPERATION_ISSUER,
        "sealed nested operation receipt has the wrong issuer",
    )
    require(
        type(getattr(receipt, "capability", None)) is object,
        "sealed nested operation receipt capability has the wrong type",
    )
    require(
        type(getattr(receipt, "state", None)) is str
        and receipt.state == POST_RESTORE_GREEN_REPLAY_COMPLETED,
        "sealed nested operation receipt has the wrong completion state",
    )
    require(
        type(getattr(receipt, "label", None)) is str
        and receipt.label == expected_label,
        "sealed nested operation receipt label changed",
    )
    require(
        type(getattr(receipt, "pre_status_sha256", None)) is str
        and re.fullmatch(r"[0-9a-f]{64}", receipt.pre_status_sha256) is not None
        and type(getattr(receipt, "post_status_sha256", None)) is str
        and re.fullmatch(r"[0-9a-f]{64}", receipt.post_status_sha256) is not None,
        "sealed nested operation receipt status digest changed",
    )
    require(
        type(getattr(receipt, "status_equal", None)) is bool
        and receipt.status_equal is True
        and receipt.pre_status_sha256 == receipt.post_status_sha256,
        "sealed nested operation receipt status equality changed",
    )
    if _expected_route == "real_lifecycle":
        _SEALED_LIFECYCLE_AUTHORITY.require_exact_receipt_edge(
            getattr(receipt, "lifecycle_permit", None),
            receipt,
        )
    else:
        require(
            getattr(receipt, "lifecycle_permit", None) is None,
            "dry sealed receipt unexpectedly has a lifecycle permit",
        )
    return receipt


def _c3_nested_role_projection(
    *,
    inner_projection_constant: str | None,
    begin: bytes | None,
    end: bytes | None,
    object_label: str | None,
) -> tuple[str, str | None, bytes | None, bytes | None, str | None]:
    if inner_projection_constant is None:
        require(
            begin is None and end is None and object_label is None,
            "C3 nested outer-only receipt has an inner role",
        )
        return ("outer_only", None, None, None, None)
    require(
        type(inner_projection_constant) is str
        and type(begin) is bytes
        and type(end) is bytes
        and type(object_label) is str,
        "C3 nested inner receipt role has the wrong exact type",
    )
    return (
        "inner_projection",
        inner_projection_constant,
        begin,
        end,
        object_label,
    )


def _c3_nested_expected_projection(
    *,
    label: str,
    expected_detail: str,
    inner_projection_constant: str | None,
    begin: bytes | None,
    end: bytes | None,
    object_label: str | None,
) -> tuple[
    str,
    str,
    tuple[str, str | None, bytes | None, bytes | None, str | None],
]:
    require(
        type(label) is str and type(expected_detail) is str,
        "C3 nested expected projection has the wrong exact type",
    )
    return (
        label,
        expected_detail,
        _c3_nested_role_projection(
            inner_projection_constant=inner_projection_constant,
            begin=begin,
            end=end,
            object_label=object_label,
        ),
    )


def _validate_c3_nested_expected_projection_shape(
    projection: object,
    *,
    context: str,
) -> tuple[
    str,
    str,
    tuple[str, str | None, bytes | None, bytes | None, str | None],
]:
    require(
        type(projection) is tuple
        and len(projection) == 3
        and type(projection[0]) is str
        and type(projection[1]) is str
        and type(projection[2]) is tuple
        and len(projection[2]) == 5,
        f"{context} expected nested execution projection has the wrong shape",
    )
    canonical = _c3_nested_expected_projection(
        label=projection[0],
        expected_detail=projection[1],
        inner_projection_constant=projection[2][1],
        begin=projection[2][2],
        end=projection[2][3],
        object_label=projection[2][4],
    )
    require(
        canonical == projection and projection[2][0] == canonical[2][0],
        f"{context} expected nested execution projection is not canonical",
    )
    return canonical


def _validate_c3_nested_memo_attack_execution_receipt(
    receipt: object,
    *,
    expected_projection: tuple[
        str,
        str,
        tuple[str, str | None, bytes | None, bytes | None, str | None],
    ],
    _expected_route: str = "real_lifecycle",
) -> C3NestedMemoAttackExecutionReceipt:
    expected_projection = _validate_c3_nested_expected_projection_shape(
        expected_projection,
        context="C3 nested memo attack receipt",
    )
    require(
        type(receipt) is C3NestedMemoAttackExecutionReceipt,
        "C3 nested memo attack execution receipt has the wrong exact type",
    )
    _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.validate(
        receipt,
        expected_route=_expected_route,
    )
    require(
        getattr(receipt, "issuer", None)
        is _C3_NESTED_MEMO_ATTACK_EXECUTION_ISSUER,
        "C3 nested memo attack execution receipt has the wrong issuer",
    )
    require(
        type(getattr(receipt, "capability", None)) is object,
        "C3 nested memo attack execution receipt capability has the wrong type",
    )
    require(
        type(getattr(receipt, "state", None)) is str
        and receipt.state == POST_RESTORE_GREEN_REPLAY_COMPLETED,
        "C3 nested memo attack execution receipt has the wrong completion state",
    )
    actual_projection = _c3_nested_expected_projection(
        label=receipt.label,
        expected_detail=receipt.expected_detail,
        inner_projection_constant=receipt.inner_projection_constant,
        begin=receipt.begin,
        end=receipt.end,
        object_label=receipt.object_label,
    )
    require(
        type(getattr(receipt, "role", None)) is str
        and receipt.role == actual_projection[2][0],
        "C3 nested memo attack execution receipt role changed",
    )
    require(
        actual_projection == expected_projection,
        "C3 nested memo attack execution receipt projection changed",
    )
    _validate_sealed_nested_candidate_operation_receipt(
        receipt.sealed_receipt,
        expected_label=expected_projection[0],
        _expected_route=_expected_route,
    )
    _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.require_exact_child_edge(
        receipt,
        child_receipt=receipt.sealed_receipt,
        expected_route=_expected_route,
    )
    return receipt


def _validated_c3_nested_execution_projection(
    receipts: object,
    *,
    expected_projection: object,
    context: str,
    _expected_route: str = "real_lifecycle",
) -> tuple[
    tuple[
        str,
        str,
        tuple[str, str | None, bytes | None, bytes | None, str | None],
    ],
    ...,
]:
    require(
        type(receipts) is list,
        f"{context} nested execution receipts are not an exact list",
    )
    require(
        type(expected_projection) is tuple,
        f"{context} expected nested execution projection is not an exact tuple",
    )
    actual_projection = []
    for index, expected in enumerate(expected_projection):
        expected = _validate_c3_nested_expected_projection_shape(
            expected,
            context=f"{context} row {index}",
        )
        require(
            index < len(receipts),
            f"{context} nested execution receipt inventory is incomplete",
        )
        receipt = receipts[index]
        require(
            type(receipt) is C3NestedMemoAttackExecutionReceipt,
            f"{context} nested execution receipt {index} has the wrong type",
        )
        validated = _validate_c3_nested_memo_attack_execution_receipt(
            receipt,
            expected_projection=expected,
            _expected_route=_expected_route,
        )
        actual_projection.append(
            _c3_nested_expected_projection(
                label=validated.label,
                expected_detail=validated.expected_detail,
                inner_projection_constant=validated.inner_projection_constant,
                begin=validated.begin,
                end=validated.end,
                object_label=validated.object_label,
            )
        )
    require(
        len(receipts) == len(expected_projection),
        f"{context} validated nested execution receipt inventory changed",
    )
    require(
        len(set(actual_projection)) == len(actual_projection),
        f"{context} nested execution projection repeats a control",
    )
    identity_sets = (
        {id(receipt) for receipt in receipts},
        {id(receipt.capability) for receipt in receipts},
        {id(receipt.sealed_receipt) for receipt in receipts},
        {id(receipt.sealed_receipt.capability) for receipt in receipts},
    )
    aggregate_identities = {
        identity
        for receipt in receipts
        for identity in (
            id(receipt),
            id(receipt.capability),
            id(receipt.sealed_receipt),
            id(receipt.sealed_receipt.capability),
        )
    }
    require(
        all(len(identities) == len(receipts) for identities in identity_sets)
        and len(aggregate_identities) == 4 * len(receipts),
        f"{context} nested execution receipt capability was reused",
    )
    projection = tuple(actual_projection)
    require(
        projection == expected_projection,
        f"{context} ordered nested execution receipt projection changed",
    )
    _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.collect_many_once(
        tuple(receipts),
        collection=f"{context} aggregate",
        expected_route=_expected_route,
    )
    return projection


def _reject_duplicate_json_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"hostile-suite policy repeats JSON key {key!r}")
        result[key] = value
    return result


def load_hostile_suite_contract(root: Path) -> dict[str, object]:
    """Load the separately reviewed exact-count contract without coercion."""

    policy_path = root / POLICY_RELATIVE
    try:
        raw = policy_path.read_bytes()
        policy = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                SelfTestError(
                    f"hostile-suite policy contains non-finite JSON token {token!r}"
                )
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelfTestError(
            f"cannot load hostile-suite policy contract: {error}"
        ) from error
    require(isinstance(policy, dict), "hostile-suite policy root is not an object")
    canonical = (
        json.dumps(policy, ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8")
        + b"\n"
    )
    require(
        canonical == raw,
        "hostile-suite policy is not sorted two-space ASCII JSON",
    )
    contract = policy.get("hostile_suite_contract")
    require(
        isinstance(contract, dict)
        and set(contract)
        == {"contracted_total", "families", "semantics", "separate_controls"},
        "hostile-suite policy contract has an unexpected shape",
    )
    return contract


def validate_hostile_suite_counts(
    contract: dict[str, object],
    *,
    observed_families: dict[str, int],
    observed_separate_controls: dict[str, int],
) -> int:
    """Cross-bind every executed family to the reviewed policy inventory."""

    expected_families = contract.get("families")
    expected_separate_controls = contract.get("separate_controls")
    contracted_total = contract.get("contracted_total")
    require(
        isinstance(expected_families, dict)
        and set(expected_families) == set(observed_families),
        "hostile-suite family keys differ from the reviewed policy",
    )
    require(
        isinstance(expected_separate_controls, dict)
        and set(expected_separate_controls) == set(observed_separate_controls),
        "hostile-suite separate-control keys differ from the reviewed policy",
    )
    for family, observed in observed_families.items():
        expected = expected_families.get(family)
        require(
            type(expected) is int and expected == observed,
            f"hostile-suite family {family!r} executed {observed}, "
            f"policy requires {expected!r}",
        )
    for control, observed in observed_separate_controls.items():
        expected = expected_separate_controls.get(control)
        require(
            type(expected) is int and expected == observed,
            f"hostile-suite separate control {control!r} executed {observed}, "
            f"policy requires {expected!r}",
        )
    independently_summed_total = sum(observed_families.values())
    require(
        type(contracted_total) is int
        and contracted_total == independently_summed_total,
        "hostile-suite contracted total differs from the independent family sum",
    )
    return independently_summed_total


def resolved_git_executable() -> str:
    """Resolve one canonical Git program for every fixture command."""

    global _RESOLVED_GIT_EXECUTABLE
    if _RESOLVED_GIT_EXECUTABLE is None:
        found = shutil.which("git")
        require(found is not None, "git is unavailable")
        path = Path(found).resolve(strict=True)
        metadata = path.stat()
        require(
            path.is_file() and not path.is_symlink() and stat.S_ISREG(metadata.st_mode),
            "resolved Git executable is not a regular file",
        )
        _RESOLVED_GIT_EXECUTABLE = str(path)
    return _RESOLVED_GIT_EXECUTABLE


def git_command(*arguments: str) -> list[str]:
    return [resolved_git_executable(), *arguments]


def _canonical_overlay_relative(relative: str) -> PurePosixPath:
    """Validate one exact, lexical repository-relative overlay spelling."""

    require(
        type(relative) is str
        and relative != ""
        and "\\" not in relative
        and "\r" not in relative
        and "\n" not in relative,
        "frozen candidate overlay contains an invalid relative path",
    )
    parsed = PurePosixPath(relative)
    require(
        not parsed.is_absolute()
        and bool(parsed.parts)
        and str(parsed) == relative
        and all(part not in {"", ".", ".."} for part in parsed.parts),
        f"frozen candidate overlay path is not canonical: {relative!r}",
    )
    return parsed


def _stable_file_identity(
    metadata: os.stat_result,
) -> tuple[int, int, int, int, int, int]:
    """Return every endpoint field bound by the stable-file capture."""

    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def stable_regular_file(root: Path, relative: str) -> FrozenOverlayEntry:
    """Capture one canonical regular file with double reads and stable endpoints."""

    parsed = _canonical_overlay_relative(relative)
    parent = root
    for part in parsed.parts[:-1]:
        parent_metadata = os.lstat(parent)
        require(
            stat.S_ISDIR(parent_metadata.st_mode)
            and not stat.S_ISLNK(parent_metadata.st_mode),
            f"frozen candidate overlay parent is not a real directory: {relative}",
        )
        parent = parent / part
    parent_metadata = os.lstat(parent)
    require(
        stat.S_ISDIR(parent_metadata.st_mode)
        and not stat.S_ISLNK(parent_metadata.st_mode),
        f"frozen candidate overlay parent is not a real directory: {relative}",
    )
    path = parent / parsed.name

    first = path.lstat()
    require(
        stat.S_ISREG(first.st_mode)
        and not stat.S_ISLNK(first.st_mode)
        and first.st_nlink == 1,
        f"frozen candidate overlay entry is not a single-link regular file: {relative}",
    )
    mode = stat.S_IMODE(first.st_mode)
    require(
        mode in {0o644, 0o755},
        f"frozen candidate overlay entry has a noncanonical mode: {relative}",
    )
    first_raw = path.read_bytes()
    second = path.lstat()
    second_raw = path.read_bytes()
    third = path.lstat()
    require(
        _stable_file_identity(first)
        == _stable_file_identity(second)
        == _stable_file_identity(third)
        and first_raw == second_raw,
        f"frozen candidate overlay entry changed during stable capture: {relative}",
    )
    require(
        len(first_raw) == first.st_size,
        f"frozen candidate overlay entry size changed during capture: {relative}",
    )
    return FrozenOverlayEntry(
        relative=relative,
        raw=first_raw,
        mode=mode,
        size=len(first_raw),
        sha256=hashlib.sha256(first_raw).hexdigest(),
    )


def _overlay_projection(entries: tuple[FrozenOverlayEntry, ...]) -> str:
    payload = bytearray()
    for entry in entries:
        git_mode = "100755" if entry.mode == 0o755 else "100644"
        payload.extend(entry.relative.encode("utf-8"))
        payload.extend(b"\0")
        payload.extend(git_mode.encode("ascii"))
        payload.extend(b"\0")
        payload.extend(str(entry.size).encode("ascii"))
        payload.extend(b"\0")
        payload.extend(entry.sha256.encode("ascii"))
        payload.extend(b"\n")
    return hashlib.sha256(payload).hexdigest()


def frozen_overlay_entry(
    overlay: FrozenOverlay,
    relative: str,
) -> FrozenOverlayEntry:
    matches = tuple(entry for entry in overlay.entries if entry.relative == relative)
    require(
        len(matches) == 1,
        f"frozen candidate overlay lost one exact entry: {relative}",
    )
    return matches[0]


def freeze_candidate_overlay(
    root: Path,
    facts: dict[str, object],
) -> FrozenOverlay:
    """Stable-capture the exact 187-entry overlay once from the source root."""

    changed = facts.get("changed_paths")
    require(
        isinstance(changed, list)
        and len(changed) == EXPECTED_CHANGED_PATH_COUNT
        and all(type(relative) is str for relative in changed),
        "diagnostic changed-path inventory is invalid",
    )
    relatives = tuple(changed)
    require(
        relatives == tuple(sorted(relatives))
        and len(relatives) == len(set(relatives))
        and all(
            str(_canonical_overlay_relative(relative)) == relative
            for relative in relatives
        ),
        "frozen candidate overlay path inventory is not sorted and unique",
    )
    require(
        sum(relative in {CHECKER_RELATIVE, SELF_RELATIVE} for relative in relatives)
        == EXPECTED_SELF_UNHASHED_COUNT
        and CHECKER_RELATIVE in relatives
        and SELF_RELATIVE in relatives,
        "frozen candidate overlay self-unhashed inventory changed",
    )
    require(
        len(anchor_delta_paths(facts)) == EXPECTED_ANCHOR_DELTA_PATH_COUNT,
        "frozen candidate overlay anchor-delta count changed",
    )
    entries = tuple(stable_regular_file(root, relative) for relative in relatives)
    return FrozenOverlay(
        entries=entries,
        projection_sha256=_overlay_projection(entries),
    )


def verify_frozen_overlay(root: Path, overlay: FrozenOverlay) -> None:
    """Require every materialized destination byte and mode to match the freeze."""

    require(
        len(overlay.entries) == EXPECTED_CHANGED_PATH_COUNT,
        "frozen candidate overlay entry count changed",
    )
    require(
        tuple(entry.relative for entry in overlay.entries)
        == tuple(sorted(entry.relative for entry in overlay.entries))
        and len({entry.relative for entry in overlay.entries})
        == EXPECTED_CHANGED_PATH_COUNT,
        "frozen candidate overlay verification inventory changed",
    )
    observed_entries: list[FrozenOverlayEntry] = []
    for entry in overlay.entries:
        observed = stable_regular_file(root, entry.relative)
        require(
            observed.mode == entry.mode,
            f"frozen candidate overlay mode mismatch: {entry.relative}",
        )
        require(
            observed.raw == entry.raw,
            f"frozen candidate overlay bytes mismatch: {entry.relative}",
        )
        require(
            observed.size == entry.size and observed.sha256 == entry.sha256,
            f"frozen candidate overlay metadata mismatch: {entry.relative}",
        )
        observed_entries.append(observed)
    require(
        _overlay_projection(tuple(observed_entries)) == overlay.projection_sha256,
        "frozen candidate overlay projection mismatch",
    )


def _exact_checker_child_environment(private_root: Path) -> dict[str, str]:
    """Build the finite environment for a captured candidate-checker child."""

    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": str(Path(resolved_git_executable()).parent),
        "TEMP": str(private_root),
        "TMP": str(private_root),
        "TMPDIR": str(private_root),
        "TZ": "UTC",
    }
    for name in (
        "COMSPEC",
        "HOME",
        "PATHEXT",
        "SystemRoot",
        "SYSTEMROOT",
        "USERPROFILE",
        "WINDIR",
    ):
        value = os.environ.get(name)
        if value is not None:
            environment[name] = value
    return environment


def invoke_exact_checker(
    root: Path,
    *arguments: str,
    force_optimized: bool | None = None,
    environment_overrides: dict[str, str] | None = None,
    source_entry: FrozenOverlayEntry | None = None,
    after_child: Callable[[], None] | None = None,
) -> ExactCheckerInvocation:
    """Execute one stable-captured checker over stdin under a lexical __file__.

    This narrows only the disposable candidate-checker loader. The already
    running top-level self-test remains path-loaded, and the double-read plus
    post-child endpoint checks are deliberately not an atomic filesystem
    history or protection from a concurrent same-UID/privileged writer.
    """

    entry = (
        stable_regular_file(root, CHECKER_RELATIVE)
        if source_entry is None
        else source_entry
    )
    require(
        entry.relative == CHECKER_RELATIVE
        and entry.mode in {0o644, 0o755}
        and entry.size == len(entry.raw)
        and entry.sha256 == hashlib.sha256(entry.raw).hexdigest(),
        "exact checker invocation received the wrong captured source entry",
    )
    require(
        hashlib.sha256(CANDIDATE_CHECKER_STDIN_BOOTSTRAP.encode("utf-8")).hexdigest()
        == EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256,
        "candidate-checker stdin bootstrap digest changed",
    )
    optimized = sys.flags.optimize > 0 if force_optimized is None else force_optimized
    logical_file = os.path.abspath(os.fspath(root / CHECKER_RELATIVE))
    command = [sys.executable, "-I", "-S"]
    if optimized:
        command.append("-O")
    command.extend(
        (
            "-c",
            CANDIDATE_CHECKER_STDIN_BOOTSTRAP,
            logical_file,
            *arguments,
        )
    )
    overrides = {} if environment_overrides is None else environment_overrides
    require(
        set(overrides).issubset(EXACT_CHECKER_ENVIRONMENT_OVERRIDE_KEYS)
        and all(
            type(key) is str and type(value) is str for key, value in overrides.items()
        ),
        "candidate checker received an unreviewed environment override",
    )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-exact-phase-checker."
    ) as private_raw:
        private_root = Path(private_raw)
        environment = _exact_checker_child_environment(private_root)
        environment.update(overrides)
        try:
            process = subprocess.run(
                command,
                cwd=root,
                env=environment,
                input=entry.raw,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        finally:
            if after_child is not None:
                after_child()
        observed = stable_regular_file(root, CHECKER_RELATIVE)
    require(
        observed.raw == entry.raw
        and observed.mode == entry.mode
        and observed.size == entry.size
        and observed.sha256 == entry.sha256,
        "candidate checker logical path changed during exact-source invocation",
    )
    return ExactCheckerInvocation(process=process, source_entry=entry)


def python_command(
    script: Path, *arguments: str, force_optimized: bool | None = None
) -> list[str]:
    optimized = sys.flags.optimize > 0 if force_optimized is None else force_optimized
    command = [sys.executable, "-I", "-S"]
    if optimized:
        command.append("-O")
    command.extend((str(script), *arguments))
    return command


def run(
    command: list[str],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
    environment_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
    )
    if environment_overrides is not None:
        environment.update(environment_overrides)
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        input=input_bytes,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _argument_value(arguments: tuple[str, ...], option: str) -> str:
    """Return one exact option value from a successful checker invocation."""

    positions = tuple(
        index for index, argument in enumerate(arguments) if argument == option
    )
    require(
        len(positions) == 1 and positions[0] + 1 < len(arguments),
        f"successful checker arguments lost one exact {option} value",
    )
    return arguments[positions[0] + 1]


def validate_checker_success_receipt(
    process: subprocess.CompletedProcess[bytes],
    *,
    credited: bool,
    expected_lifecycle: str,
    arguments: tuple[str, ...],
    git_path: str,
    git_digest: str,
    git_version: str,
) -> None:
    """Require one exact typed success line rather than substring evidence."""

    require(
        process.returncode == 0,
        "successful phase checker returned nonzero",
    )
    require(
        process.stderr == b"",
        "successful phase checker emitted stderr",
    )
    require(
        process.stdout.endswith(b"\n")
        and b"\n" not in process.stdout[:-1]
        and b"\r" not in process.stdout,
        "successful phase checker did not emit exactly one LF-terminated line",
    )
    try:
        line = process.stdout[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SelfTestError(
            "successful phase checker receipt is not strict UTF-8"
        ) from error

    suffix = ". " + SUCCESS_NONCLAIM
    require(
        line.endswith(suffix),
        "successful phase checker lost its exact nonclaim suffix",
    )
    fields = line[: -len(suffix)].split("; ")
    require(
        len(fields) == 15,
        "successful phase checker receipt field inventory changed",
    )
    expected_prefix = (
        "OK: KSG phase provenance only"
        if credited
        else "NO-CREDIT: KSG phase provenance diagnostic only"
    )
    require(
        fields[0] == expected_prefix,
        "successful phase checker receipt prefix changed",
    )
    expected_keys = (
        "lifecycle",
        "changed",
        "protected",
        "tracked-worktree",
        "untracked-deliverables",
        "baseline",
        "delivery",
        "anchor",
        "self-unhashed",
        "candidate-tree",
        "checkpoint",
        "git",
        "git-sha256",
        "git-version",
    )
    values: dict[str, str] = {}
    for field, expected_key in zip(fields[1:], expected_keys, strict=True):
        key, separator, value = field.partition("=")
        require(
            bool(separator) and key == expected_key and value != "",
            "successful phase checker receipt field order or shape changed",
        )
        values[key] = value

    for key in (
        "changed",
        "protected",
        "tracked-worktree",
        "untracked-deliverables",
        "self-unhashed",
    ):
        value = values[key]
        require(
            value.isascii() and value.isdigit() and str(int(value)) == value,
            f"successful phase checker receipt {key} is not canonical decimal",
        )
    require(
        int(values["changed"]) == EXPECTED_CHANGED_PATH_COUNT
        and int(values["protected"]) == EXPECTED_PROTECTED_PATH_COUNT
        and int(values["self-unhashed"]) == EXPECTED_SELF_UNHASHED_COUNT,
        "successful phase checker receipt path counts changed",
    )
    require(
        expected_lifecycle in {"precommit-worktree", "committed-descendant"},
        "success-receipt oracle received an untyped expected lifecycle",
    )
    require(
        values["lifecycle"] == expected_lifecycle,
        "successful phase checker receipt lifecycle differs from caller custody",
    )
    expected_worktree_counts = (
        (EXPECTED_PRECOMMIT_TRACKED_COUNT, EXPECTED_PRECOMMIT_UNTRACKED_COUNT)
        if expected_lifecycle == "precommit-worktree"
        else (0, 0)
    )
    require(
        (
            int(values["tracked-worktree"]),
            int(values["untracked-deliverables"]),
        )
        == expected_worktree_counts,
        "successful phase checker receipt worktree counts changed",
    )
    require(
        values["baseline"] == SCIENTIFIC_BASELINE
        and values["delivery"] == DELIVERY_PARENT
        and values["anchor"] == CURRENT_ANCHOR,
        "successful phase checker receipt ancestry changed",
    )
    expected_tree = (
        _argument_value(arguments, "--expected-candidate-tree")
        if credited
        else "not-requested"
    )
    expected_checkpoint = (
        _argument_value(arguments, "--checkpoint-commit")
        if credited
        else "not-requested"
    )
    require(
        values["candidate-tree"] == expected_tree
        and values["checkpoint"] == expected_checkpoint,
        "successful phase checker receipt external custody changed",
    )
    require(
        values["git"] == git_path
        and values["git-sha256"] == git_digest
        and values["git-version"] == repr(git_version),
        "successful phase checker receipt Git identity changed",
    )


def _canonical_checker_failure_detail(
    process: subprocess.CompletedProcess[bytes],
) -> str:
    """Extract the exact detail from an already captured canonical failure line."""

    require(
        process.stderr.endswith(b"\n")
        and b"\n" not in process.stderr[:-1]
        and b"\r" not in process.stderr,
        "failing phase checker did not emit exactly one LF-terminated line",
    )
    try:
        line = process.stderr[:-1].decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SelfTestError(
            "failing phase checker receipt is not strict UTF-8"
        ) from error

    prefix = "ERROR: KSG phase isolation: "
    require(
        line.startswith(prefix),
        "failing phase checker receipt lost its exact typed prefix",
    )
    escaped_detail = line.removeprefix(prefix)
    require(
        escaped_detail != ""
        and all(character.isprintable() for character in escaped_detail),
        "failing phase checker receipt detail is empty or nonprintable",
    )
    try:
        detail = json.loads(f'"{escaped_detail}"')
    except json.JSONDecodeError as error:
        raise SelfTestError(
            "failing phase checker detail is not canonical JSON string content"
        ) from error
    require(
        isinstance(detail, str)
        and json.dumps(detail, ensure_ascii=True)[1:-1] == escaped_detail,
        "failing phase checker detail is not canonical JSON string content",
    )
    return detail


def validate_checker_failure_receipt(
    process: subprocess.CompletedProcess[bytes],
    *,
    expectation: FailureExpectation,
) -> None:
    """Require exact process grammar and one whole source-declared reason template."""

    require(
        expectation.fragment != "",
        "failure-receipt oracle requires an independently expected reason",
    )
    require(
        process.returncode == 1,
        "failing phase checker returned a noncanonical status",
    )
    require(
        process.stdout == b"",
        "failing phase checker emitted stdout",
    )
    detail = _canonical_checker_failure_detail(process)
    require(
        expectation.fragment in detail,
        (
            "phase checker rejected a mutation for the wrong reason; "
            f"missing {expectation.fragment!r} in {detail!r}"
        ),
    )
    if expectation.exact_detail is not None:
        require(
            expectation.diagnostic_prefix is None
            and detail == expectation.exact_detail,
            "failing phase checker detail differs from caller-held exact bytes",
        )
    else:
        prefix = expectation.diagnostic_prefix
        require(
            prefix is not None and detail.startswith(prefix),
            "failing phase checker lost its caller-bound diagnostic route",
        )
        tail = detail[len(prefix) :]
        require(
            tail != "",
            "failing phase checker diagnostic tail is empty",
        )
        require(
            tail == tail.strip(),
            "failing phase checker diagnostic tail has boundary whitespace",
        )
    matching_templates = tuple(
        template.pattern.pattern
        for template in failure_detail_templates()
        if template.pattern.fullmatch(detail) is not None
    )
    require(
        len(set(matching_templates)) == 1,
        (
            "failing phase checker detail did not consume exactly one "
            "independently source-declared reason template"
        ),
    )


def _failure_message_pattern(
    expression: ast.expr,
) -> tuple[str, tuple[str, ...], int]:
    """Compile one require-message AST into a full-consumption receipt pattern."""

    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return re.escape(expression.value), (expression.value,), 0
    if isinstance(expression, ast.JoinedStr):
        parts: list[str] = []
        static: list[str] = []
        dynamic_fields = 0
        for value in expression.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(re.escape(value.value))
                static.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append(r"[\s\S]*?")
                dynamic_fields += 1
            else:
                raise SelfTestError("checker failure-message f-string AST changed")
        return "".join(parts), tuple(static), dynamic_fields
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        (
            left_pattern,
            left_static,
            left_dynamic,
        ) = _failure_message_pattern(expression.left)
        (
            right_pattern,
            right_static,
            right_dynamic,
        ) = _failure_message_pattern(expression.right)
        return (
            left_pattern + right_pattern,
            left_static + right_static,
            left_dynamic + right_dynamic,
        )
    if isinstance(expression, ast.IfExp):
        (
            body_pattern,
            body_static,
            body_dynamic,
        ) = _failure_message_pattern(expression.body)
        (
            else_pattern,
            else_static,
            else_dynamic,
        ) = _failure_message_pattern(expression.orelse)
        return (
            f"(?:{body_pattern}|{else_pattern})",
            body_static + else_static,
            max(body_dynamic, else_dynamic),
        )
    # Calls and other runtime expressions are allowed only as bounded dynamic
    # fields inside one source-declared top-level concatenation.
    return r"[\s\S]*?", (), 1


def bind_failure_detail_source(overlay: FrozenOverlay) -> None:
    """Bind failure-template parsing to the initial frozen checker bytes."""

    global _FAILURE_DETAIL_SOURCE_ENTRY
    entry = frozen_overlay_entry(overlay, CHECKER_RELATIVE)
    require(
        _FAILURE_DETAIL_SOURCE_ENTRY is None or _FAILURE_DETAIL_SOURCE_ENTRY == entry,
        "failure-detail source entry was rebound",
    )
    _FAILURE_DETAIL_SOURCE_ENTRY = entry


def failure_detail_templates() -> tuple[FailureTemplate, ...]:
    """Freeze full-message templates from pristine checker require call sites."""

    global _FAILURE_DETAIL_TEMPLATES
    if _FAILURE_DETAIL_TEMPLATES is None:
        require(
            _FAILURE_DETAIL_SOURCE_ENTRY is not None,
            "failure-detail templates lack the frozen checker source entry",
        )
        try:
            source = _FAILURE_DETAIL_SOURCE_ENTRY.raw.decode("utf-8", errors="strict")
            module = _parse_unoptimized_module(source, filename=CHECKER_RELATIVE)
        except (OSError, UnicodeError, SyntaxError) as error:
            raise SelfTestError(
                "cannot parse pristine checker failure-message templates"
            ) from error
        templates: dict[str, tuple[tuple[str, ...], int]] = {}
        require_calls = 0
        direct_error_calls = 0
        for node in ast.walk(module):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id == "require" and len(node.args) >= 2:
                require_calls += 1
                message_expression = node.args[1]
            elif (
                node.func.id == "PhaseIsolationError"
                and node.args
                and not isinstance(node.args[0], ast.Name)
            ):
                direct_error_calls += 1
                message_expression = node.args[0]
            else:
                continue
            pattern, static_fragments, dynamic_fields = _failure_message_pattern(
                message_expression
            )
            require(
                static_fragments,
                "checker require message lost every static source fragment",
            )
            prior = templates.get(pattern)
            if prior is None:
                templates[pattern] = (static_fragments, dynamic_fields)
            else:
                prior_static, prior_dynamic = prior
                templates[pattern] = (
                    tuple(dict.fromkeys((*prior_static, *static_fragments))),
                    max(prior_dynamic, dynamic_fields),
                )
        require(
            require_calls == 383 and direct_error_calls == 43 and len(templates) == 408,
            "checker failure-message call-site/template inventory changed",
        )
        _FAILURE_DETAIL_TEMPLATES = tuple(
            FailureTemplate(
                pattern=re.compile(pattern),
                static_fragments=templates[pattern][0],
                dynamic_fields=templates[pattern][1],
            )
            for pattern in sorted(templates)
        )
    return _FAILURE_DETAIL_TEMPLATES


def exact_failure_expectation(fragment: str) -> FailureExpectation:
    """Resolve only a unique constant source reason from a legacy fragment."""

    require(fragment != "", "empty failure expectation is forbidden")
    constant_candidates = tuple(
        "".join(template.static_fragments)
        for template in failure_detail_templates()
        if template.dynamic_fields == 0
        and fragment in "".join(template.static_fragments)
    )
    distinct_constants = tuple(dict.fromkeys(constant_candidates))
    require(
        len(distinct_constants) == 1,
        (
            "failure expectation is not one unique constant source detail; "
            f"construct an explicit caller-held expectation for {fragment!r}"
        ),
    )
    detail = distinct_constants[0]
    matching_templates = {
        template.pattern.pattern
        for template in failure_detail_templates()
        if template.pattern.fullmatch(detail) is not None
    }
    require(
        len(matching_templates) == 1,
        "constant failure detail does not select one source-declared route",
    )
    return FailureExpectation(
        fragment=fragment,
        exact_detail=detail,
        diagnostic_prefix=None,
    )


def caller_held_exact_failure_expectation(
    detail: str,
    *,
    fragment: str | None = None,
) -> FailureExpectation:
    """Bind every dynamic field to one complete detail constructed by the caller."""

    expected_fragment = detail if fragment is None else fragment
    require(
        detail != "" and expected_fragment != "" and expected_fragment in detail,
        "caller-held failure detail or fragment is empty or inconsistent",
    )
    matching_templates = {
        template.pattern.pattern
        for template in failure_detail_templates()
        if template.pattern.fullmatch(detail) is not None
    }
    require(
        len(matching_templates) == 1,
        "caller-held exact failure detail does not select one source-declared route",
    )
    return FailureExpectation(
        fragment=expected_fragment,
        exact_detail=detail,
        diagnostic_prefix=None,
    )


def diagnostic_failure_expectation(
    *,
    route: str,
    fragment: str,
    exact_prefix: str,
) -> FailureExpectation:
    """Allow a nonempty, untrusted tail on one of three closed diagnostic routes."""

    require(
        fragment != "" and exact_prefix != "" and fragment in exact_prefix,
        "diagnostic failure expectation lost its exact route prefix",
    )
    route_matches = {
        "git-cat-file": re.fullmatch(
            r"git cat-file -p [0-9a-f]{40} failed with 128: ",
            exact_prefix,
        )
        is not None,
        "deleted-candidate-path": exact_prefix
        == f"{SELF_RELATIVE!r}: candidate path is missing: ",
        "external-tree-whitespace": exact_prefix
        == (
            "external candidate tree failed the scrubbed anchor-to-tree "
            "Git whitespace check: "
        ),
    }
    require(
        route in route_matches and route_matches[route],
        "diagnostic failure expectation is not one of three closed routes",
    )
    sentinel = exact_prefix + "DIAGNOSTIC-TAIL"
    matching_templates = {
        template.pattern.pattern
        for template in failure_detail_templates()
        if template.pattern.fullmatch(sentinel) is not None
    }
    require(
        len(matching_templates) == 1,
        "diagnostic failure prefix does not select one source-declared route",
    )
    return FailureExpectation(
        fragment=fragment,
        exact_detail=None,
        diagnostic_prefix=exact_prefix,
    )


def run_checker(
    root: Path,
    *,
    expect_success: bool,
    expected_fragment: str = "",
    failure_expectation: FailureExpectation | None = None,
    expected_lifecycle: str = "precommit-worktree",
    force_optimized: bool | None = None,
    arguments: tuple[str, ...] = (),
    environment_overrides: dict[str, str] | None = None,
    auto_diagnostic: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    effective_arguments = arguments
    has_tree = "--expected-candidate-tree" in arguments
    has_checkpoint = "--checkpoint-commit" in arguments
    if auto_diagnostic and not has_tree and not has_checkpoint:
        effective_arguments = (
            "--diagnostic-without-external-custody",
            *arguments,
        )
    invocation = invoke_exact_checker(
        root,
        *effective_arguments,
        force_optimized=force_optimized,
        environment_overrides=environment_overrides,
    )
    process = invocation.process
    if expect_success:
        require(
            expected_fragment == "" and failure_expectation is None,
            "successful checker invocation received a failure expectation",
        )
        credited = has_tree and has_checkpoint
        git_path, git_digest, git_version = resolved_git_evidence(root)
        validate_checker_success_receipt(
            process,
            credited=credited,
            expected_lifecycle=expected_lifecycle,
            arguments=arguments,
            git_path=git_path,
            git_digest=git_digest,
            git_version=git_version,
        )
    else:
        expectation = (
            exact_failure_expectation(expected_fragment)
            if failure_expectation is None
            else failure_expectation
        )
        require(
            expected_fragment in {"", expectation.fragment},
            "failure expectation and legacy reason fragment disagree",
        )
        validate_checker_failure_receipt(
            process,
            expectation=expectation,
        )
    return process


def resolved_git_evidence(root: Path) -> tuple[str, str, str]:
    """Return exact path/digest/version for the one self-test Git executable."""

    global _RESOLVED_GIT_EVIDENCE
    if _RESOLVED_GIT_EVIDENCE is None:
        path = resolved_git_executable()
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        version = run(git_command("--version"), cwd=root)
        require(
            version.returncode == 0
            and version.stderr == b""
            and version.stdout.endswith(b"\n")
            and b"\n" not in version.stdout[:-1]
            and b"\r" not in version.stdout,
            "cannot obtain one exact Git version line",
        )
        _RESOLVED_GIT_EVIDENCE = (
            path,
            digest,
            version.stdout[:-1].decode("ascii", errors="strict"),
        )
    return _RESOLVED_GIT_EVIDENCE


def run_success_receipt_oracle_attacks() -> int:
    """Reject eleven false-green process, grammar, custody, and nonclaim shapes."""

    fixture_git_path = "/usr/bin/git-fixture"
    fixture_git_digest = "a" * 64
    fixture_git_version = "git version 2.50.1"
    valid_line = (
        "NO-CREDIT: KSG phase provenance diagnostic only; "
        "lifecycle=precommit-worktree; "
        f"changed={EXPECTED_CHANGED_PATH_COUNT}; "
        f"protected={EXPECTED_PROTECTED_PATH_COUNT}; "
        f"tracked-worktree={EXPECTED_PRECOMMIT_TRACKED_COUNT}; "
        f"untracked-deliverables={EXPECTED_PRECOMMIT_UNTRACKED_COUNT}; "
        f"baseline={SCIENTIFIC_BASELINE}; "
        f"delivery={DELIVERY_PARENT}; "
        f"anchor={CURRENT_ANCHOR}; "
        f"self-unhashed={EXPECTED_SELF_UNHASHED_COUNT}; "
        "candidate-tree=not-requested; checkpoint=not-requested; "
        f"git={fixture_git_path}; git-sha256={fixture_git_digest}; "
        f"git-version={fixture_git_version!r}. {SUCCESS_NONCLAIM}\n"
    ).encode("utf-8")

    def validate(
        *,
        returncode: int = 0,
        stdout: bytes = valid_line,
        stderr: bytes = b"",
    ) -> None:
        validate_checker_success_receipt(
            subprocess.CompletedProcess(
                args=("synthetic-phase-checker",),
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            ),
            credited=False,
            expected_lifecycle="precommit-worktree",
            arguments=(),
            git_path=fixture_git_path,
            git_digest=fixture_git_digest,
            git_version=fixture_git_version,
        )

    validate()
    attacks: tuple[tuple[str, dict[str, object]], ...] = (
        ("nonzero_process", {"returncode": 1}),
        ("nonempty_stderr", {"stderr": b"forged warning\n"}),
        ("missing_final_newline", {"stdout": valid_line[:-1]}),
        ("extra_stdout_line", {"stdout": valid_line + b"forged second line\n"}),
        (
            "carriage_return_injection",
            {"stdout": valid_line.replace(b"; changed=", b"\r; changed=", 1)},
        ),
        (
            "expected_prefix_embedded_midline",
            {"stdout": b"ARITHMETIC-PROVED " + valid_line},
        ),
        (
            "candidate_tree_forgery",
            {
                "stdout": valid_line.replace(
                    b"candidate-tree=not-requested",
                    b"candidate-tree=" + b"0" * 40,
                    1,
                )
            },
        ),
        (
            "checkpoint_forgery",
            {
                "stdout": valid_line.replace(
                    b"checkpoint=not-requested",
                    b"checkpoint=" + b"1" * 40,
                    1,
                )
            },
        ),
        (
            "arbitrary_trailing_text",
            {"stdout": valid_line[:-1] + b" FORGED\n"},
        ),
        (
            "nonclaim_promotion",
            {
                "stdout": valid_line.replace(
                    b"No arithmetic, estimator, PID, statistical, remote, or "
                    b"authenticity claim is implied.",
                    b"Arithmetic and authenticity are proved.",
                    1,
                )
            },
        ),
        (
            "coordinated_lifecycle_and_worktree_counts_forgery",
            {
                "stdout": valid_line.replace(
                    (
                        "lifecycle=precommit-worktree; "
                        f"changed={EXPECTED_CHANGED_PATH_COUNT}; "
                        f"protected={EXPECTED_PROTECTED_PATH_COUNT}; "
                        f"tracked-worktree={EXPECTED_PRECOMMIT_TRACKED_COUNT}; "
                        "untracked-deliverables="
                        f"{EXPECTED_PRECOMMIT_UNTRACKED_COUNT}"
                    ).encode("ascii"),
                    (
                        "lifecycle=committed-descendant; "
                        f"changed={EXPECTED_CHANGED_PATH_COUNT}; "
                        f"protected={EXPECTED_PROTECTED_PATH_COUNT}; "
                        "tracked-worktree=0; untracked-deliverables=0"
                    ).encode("ascii"),
                    1,
                )
            },
        ),
    )
    for name, keywords in attacks:
        try:
            validate(**keywords)
        except SelfTestError:
            pass
        else:
            require(False, f"success-receipt hostile shape survived: {name}")
    return len(attacks)


def run_failure_receipt_oracle_attacks() -> int:
    """Reject eighteen false-red process, grammar, route, and reason shapes."""

    expected_fragment = "scientific baseline path count changed"
    valid_line = (
        "ERROR: KSG phase isolation: scientific baseline path count changed\n"
    ).encode("utf-8")

    def receipt_line(detail: str) -> bytes:
        escaped = json.dumps(detail, ensure_ascii=True)[1:-1]
        return f"ERROR: KSG phase isolation: {escaped}\n".encode("ascii")

    def validate(
        *,
        returncode: int = 1,
        stdout: bytes = b"",
        stderr: bytes = valid_line,
        fragment: str = expected_fragment,
    ) -> None:
        validate_checker_failure_receipt(
            subprocess.CompletedProcess(
                args=("synthetic-phase-checker",),
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            ),
            expectation=exact_failure_expectation(fragment),
        )

    validate()
    attacks: tuple[tuple[str, dict[str, object], str], ...] = (
        (
            "wrong_process_status",
            {"returncode": 99},
            "failing phase checker returned a noncanonical status",
        ),
        (
            "forged_stdout",
            {"stdout": b"scientific baseline path count changed\n"},
            "failing phase checker emitted stdout",
        ),
        (
            "missing_final_newline",
            {"stderr": valid_line[:-1]},
            "failing phase checker did not emit exactly one LF-terminated line",
        ),
        (
            "traceback_multiline",
            {
                "stderr": (
                    b"Traceback (most recent call last):\n"
                    b"ERROR: KSG phase isolation: "
                    b"scientific baseline path count changed\n"
                )
            },
            "failing phase checker did not emit exactly one LF-terminated line",
        ),
        (
            "carriage_return_injection",
            {
                "stderr": valid_line.replace(
                    b": scientific",
                    b":\r scientific",
                    1,
                )
            },
            "failing phase checker did not emit exactly one LF-terminated line",
        ),
        (
            "expected_reason_without_typed_prefix",
            {"stderr": b"scientific baseline path count changed\n"},
            "failing phase checker receipt lost its exact typed prefix",
        ),
        (
            "wrong_reason",
            {"stderr": b"ERROR: KSG phase isolation: unrelated reason\n"},
            "phase checker rejected a mutation for the wrong reason;",
        ),
        (
            "invalid_utf8",
            {
                "stderr": (
                    b"ERROR: KSG phase isolation: expected semantic reason \xff\n"
                )
            },
            "failing phase checker receipt is not strict UTF-8",
        ),
        (
            "unrelated_prefix_before_expected_reason",
            {
                "stderr": (
                    b"ERROR: KSG phase isolation: unrelated failure; "
                    b"scientific baseline path count changed\n"
                )
            },
            "failing phase checker detail differs from caller-held exact bytes",
        ),
        (
            "forged_suffix_after_expected_reason",
            {
                "stderr": (
                    b"ERROR: KSG phase isolation: "
                    b"scientific baseline path count changed; forged claim\n"
                )
            },
            "failing phase checker detail differs from caller-held exact bytes",
        ),
        (
            "unrelated_prefix_and_forged_suffix",
            {
                "stderr": (
                    b"ERROR: KSG phase isolation: unrelated failure; "
                    b"scientific baseline path count changed; forged claim\n"
                )
            },
            "failing phase checker detail differs from caller-held exact bytes",
        ),
        (
            "raw_quote_in_json_string_content",
            {"stderr": valid_line[:-1] + b'"\n'},
            "failing phase checker detail is not canonical JSON string content",
        ),
        (
            "invalid_json_escape",
            {"stderr": valid_line[:-1] + b"\\q\n"},
            "failing phase checker detail is not canonical JSON string content",
        ),
        (
            "valid_but_noncanonical_json_escape",
            {
                "stderr": valid_line.replace(
                    b"scientific",
                    b"\\u0073cientific",
                    1,
                )
            },
            "failing phase checker detail is not canonical JSON string content",
        ),
    )
    for name, keywords, expected_error_prefix in attacks:
        try:
            validate(**keywords)
        except SelfTestError as error:
            require(
                str(error).startswith(expected_error_prefix),
                (
                    f"failure-receipt hostile shape {name} reached the wrong "
                    f"rejection branch: {error}"
                ),
            )
        else:
            require(False, f"failure-receipt hostile shape survived: {name}")

    dynamic_detail = (
        f"candidate changed preserved C2 evidence: {PUBLIC_CI_FAILURE_RECEIPT}"
    )
    dynamic_expectation = caller_held_exact_failure_expectation(
        dynamic_detail,
        fragment="candidate changed preserved C2 evidence",
    )
    validate_checker_failure_receipt(
        subprocess.CompletedProcess(
            args=("synthetic-phase-checker",),
            returncode=1,
            stdout=b"",
            stderr=receipt_line(dynamic_detail),
        ),
        expectation=dynamic_expectation,
    )
    try:
        validate_checker_failure_receipt(
            subprocess.CompletedProcess(
                args=("synthetic-phase-checker",),
                returncode=1,
                stdout=b"",
                stderr=receipt_line(
                    "candidate changed preserved C2 evidence: "
                    f"{PUBLIC_CI_PORTABILITY_RECEIPT}"
                ),
            ),
            expectation=dynamic_expectation,
        )
    except SelfTestError as error:
        require(
            str(error)
            == "failing phase checker detail differs from caller-held exact bytes",
            f"failure-receipt dynamic-field forgery reached the wrong branch: {error}",
        )
    else:
        require(False, "failure-receipt dynamic-field forgery survived")

    diagnostic_prefix = f"git cat-file -p {'e' * 40} failed with 128: "
    diagnostic_expectation = diagnostic_failure_expectation(
        route="git-cat-file",
        fragment=diagnostic_prefix,
        exact_prefix=diagnostic_prefix,
    )
    diagnostic_tail = "fatal: fixture object is absent\nsecond diagnostic line"
    validate_checker_failure_receipt(
        subprocess.CompletedProcess(
            args=("synthetic-phase-checker",),
            returncode=1,
            stdout=b"",
            stderr=receipt_line(diagnostic_prefix + diagnostic_tail),
        ),
        expectation=diagnostic_expectation,
    )
    try:
        validate_checker_failure_receipt(
            subprocess.CompletedProcess(
                args=("synthetic-phase-checker",),
                returncode=1,
                stdout=b"",
                stderr=receipt_line(diagnostic_prefix),
            ),
            expectation=diagnostic_expectation,
        )
    except SelfTestError as error:
        require(
            str(error) == "failing phase checker diagnostic tail is empty",
            f"failure-receipt empty tail reached the wrong branch: {error}",
        )
    else:
        require(False, "failure-receipt empty diagnostic tail survived")
    try:
        validate_checker_failure_receipt(
            subprocess.CompletedProcess(
                args=("synthetic-phase-checker",),
                returncode=1,
                stdout=b"",
                stderr=receipt_line(diagnostic_prefix + "boundary-tail "),
            ),
            expectation=diagnostic_expectation,
        )
    except SelfTestError as error:
        require(
            str(error)
            == "failing phase checker diagnostic tail has boundary whitespace",
            (
                "failure-receipt diagnostic boundary whitespace reached the "
                f"wrong branch: {error}"
            ),
        )
    else:
        require(False, "failure-receipt diagnostic boundary whitespace survived")
    try:
        validate_checker_failure_receipt(
            subprocess.CompletedProcess(
                args=("synthetic-phase-checker",),
                returncode=1,
                stdout=b"",
                stderr=receipt_line(
                    f"git cat-file -p {'f' * 40} failed with 128: "
                    + diagnostic_tail
                    + "; echoed expected route "
                    + diagnostic_prefix
                    + "echoed-tail"
                ),
            ),
            expectation=diagnostic_expectation,
        )
    except SelfTestError as error:
        require(
            str(error)
            == "failing phase checker lost its caller-bound diagnostic route",
            f"failure-receipt route forgery reached the wrong branch: {error}",
        )
    else:
        require(False, "failure-receipt diagnostic-route forgery survived")

    return len(attacks) + 4


def current_facts(
    root: Path,
    *,
    source_entry: FrozenOverlayEntry | None = None,
) -> tuple[dict[str, object], FrozenOverlayEntry]:
    invocation = invoke_exact_checker(
        root,
        "--emit-current-facts-json",
        force_optimized=False,
        source_entry=source_entry,
    )
    process = invocation.process
    require(
        process.returncode == 0,
        "cannot collect diagnostic phase facts:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    try:
        facts = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise SelfTestError("diagnostic phase facts are not JSON") from error
    require(
        isinstance(facts, dict)
        and facts.get("schema") == "pid-rs/ksg-phase-current-facts"
        and facts.get("diagnostic_only") is True,
        "diagnostic phase facts have the wrong typed envelope",
    )
    return facts, invocation.source_entry


def generated_block(
    root: Path,
    *,
    source_entry: FrozenOverlayEntry | None = None,
) -> str:
    invocation = invoke_exact_checker(
        root,
        "--emit-current-facts-python",
        force_optimized=False,
        source_entry=source_entry,
    )
    process = invocation.process
    require(
        process.returncode == 0,
        "cannot generate rebased phase facts:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    try:
        block = process.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise SelfTestError("generated phase block is not UTF-8") from error
    require(
        block.startswith(GENERATED_BEGIN)
        and block.endswith(GENERATED_END)
        and block.count(GENERATED_BEGIN) == 1
        and block.count(GENERATED_END) == 1,
        "generated phase block has invalid boundaries",
    )
    return block


def rebase_checker(root: Path) -> None:
    checker = root / CHECKER_RELATIVE
    entry = stable_regular_file(root, CHECKER_RELATIVE)
    try:
        source = entry.raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SelfTestError("checker source is not UTF-8 during rebase") from error
    begin_marker = GENERATED_BEGIN + "\n"
    end_marker = GENERATED_END + "\n"
    begin = source.find(begin_marker)
    end_start = source.find(end_marker, begin + len(begin_marker))
    require(
        begin >= 0
        and end_start > begin
        and source.find(begin_marker, begin + len(begin_marker)) < 0
        and source.find(end_marker, end_start + len(end_marker)) < 0,
        "checker generated phase boundaries are not unique",
    )
    end = end_start + len(GENERATED_END)
    replacement = generated_block(root, source_entry=entry)
    observed = stable_regular_file(root, CHECKER_RELATIVE)
    require(
        observed == entry,
        "checker source changed between exact generated-block execution and rebase",
    )
    replacement_raw = (source[:begin] + replacement + source[end:]).encode("utf-8")
    checker.write_bytes(replacement_raw)
    checker.chmod(entry.mode)
    rebased = stable_regular_file(root, CHECKER_RELATIVE)
    require(
        rebased.raw == replacement_raw and rebased.mode == entry.mode,
        "rebased checker bytes or mode differ from the exact replacement",
    )


def backup(root: Path, relatives: Iterable[str]) -> dict[str, Backup]:
    result: dict[str, Backup] = {}
    for relative in relatives:
        path = root / relative
        if path.is_symlink():
            raise SelfTestError(f"pristine mutation target is a symlink: {relative}")
        if path.exists():
            metadata = path.stat()
            require(
                stat.S_ISREG(metadata.st_mode),
                f"mutation target is not regular: {relative}",
            )
            result[relative] = Backup(
                exists=True,
                raw=path.read_bytes(),
                mode=stat.S_IMODE(metadata.st_mode),
            )
        else:
            result[relative] = Backup(exists=False, raw=b"", mode=0)
    return result


def restore(root: Path, saved: dict[str, Backup]) -> None:
    for relative, item in saved.items():
        path = root / relative
        if path.is_symlink() or path.exists():
            if path.is_dir() and not path.is_symlink():
                raise SelfTestError(
                    f"mutation unexpectedly created a directory: {relative}"
                )
            path.unlink()
        if item.exists:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.raw)
            path.chmod(item.mode)


_SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE = run_checker
_SEALED_BASELINE_LIFECYCLE_REBASE_CHECKER_CALLABLE = rebase_checker
_SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE = restore


def require_backup_restored(root: Path, saved: dict[str, Backup]) -> None:
    """Require exact existence, bytes, and canonical mode after restoration."""

    for relative, item in saved.items():
        path = root / relative
        if not item.exists:
            require(
                not path.exists() and not path.is_symlink(),
                f"restored mutation target unexpectedly exists: {relative}",
            )
            continue
        observed = stable_regular_file(root, relative)
        require(
            observed.raw == item.raw and observed.mode == item.mode,
            f"restored mutation target bytes or mode changed: {relative}",
        )


def replace_once(path: Path, old: bytes, new: bytes) -> None:
    raw = path.read_bytes()
    require(raw.count(old) == 1, f"mutation anchor is not unique in {path}")
    path.write_bytes(raw.replace(old, new, 1))


def replace_exact_count(
    path: Path,
    old: bytes,
    new: bytes,
    *,
    expected_count: int,
) -> None:
    raw = path.read_bytes()
    require(
        raw.count(old) == expected_count,
        f"mutation anchor count is not {expected_count} in {path}",
    )
    path.write_bytes(raw.replace(old, new))


def replace_once_after(path: Path, marker: bytes, old: bytes, new: bytes) -> None:
    raw = path.read_bytes()
    require(raw.count(marker) == 1, f"mutation marker is not unique in {path}")
    prefix, suffix = raw.split(marker, 1)
    require(
        suffix.count(old) == 1,
        f"post-marker mutation anchor is not unique in {path}",
    )
    path.write_bytes(prefix + marker + suffix.replace(old, new, 1))


def replace_once_between(
    path: Path,
    start_marker: bytes,
    end_marker: bytes,
    old: bytes,
    new: bytes,
) -> None:
    raw = path.read_bytes()
    require(
        raw.count(start_marker) == 1 and raw.count(end_marker) == 1,
        f"mutation job markers are not unique in {path}",
    )
    prefix, remainder = raw.split(start_marker, 1)
    require(
        remainder.count(end_marker) == 1,
        f"mutation end marker does not follow its start marker in {path}",
    )
    middle, suffix = remainder.split(end_marker, 1)
    require(
        middle.count(old) == 1,
        f"between-marker mutation anchor is not unique in {path}",
    )
    path.write_bytes(
        prefix + start_marker + middle.replace(old, new, 1) + end_marker + suffix
    )


def append_bytes(path: Path, raw: bytes) -> None:
    path.write_bytes(path.read_bytes() + raw)


def _extract_canonical_memo_object(
    path: Path,
    *,
    begin: bytes,
    end: bytes,
    label: str,
) -> dict[str, object]:
    """Read one canonical pretty-JSON object from an exact fenced memo block."""

    raw = path.read_bytes()
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise SelfTestError(f"{label}: memo is not UTF-8") from error
    require(
        raw.count(begin) == 1 and raw.count(end) == 1,
        f"{label}: fenced JSON sentinels are not unique",
    )
    prefix, remainder = raw.split(begin, 1)
    middle, suffix = remainder.split(end, 1)
    require(
        prefix.endswith(b"```text\n") and suffix.startswith(b"\n```\n"),
        f"{label}: fenced JSON is not immediately bounded by a text fence",
    )
    json_raw = middle + b"\n"
    try:
        text = json_raw.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise SelfTestError(f"{label}: fenced JSON is not ASCII") from error

    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            require(key not in result, f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> object:
        raise SelfTestError(f"{label}: non-finite JSON token {token!r}")

    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite,
        )
    except json.JSONDecodeError as error:
        raise SelfTestError(f"{label}: invalid fenced JSON: {error}") from error
    require(type(value) is dict, f"{label}: fenced JSON root must have type object")
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    require(
        canonical == json_raw,
        f"{label}: JSON is not sorted two-space ASCII form with one final LF",
    )
    return value


def mutate_canonical_memo_object(
    path: Path,
    *,
    begin: bytes,
    end: bytes,
    label: str,
    mutate: Callable[[dict[str, object]], None],
) -> None:
    """Mutate only one named memo payload and preserve its exact canonical form."""

    value = _extract_canonical_memo_object(
        path,
        begin=begin,
        end=end,
        label=label,
    )
    require(mutate(value) is None, f"{label}: mutation callback returned a value")
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    raw = path.read_bytes()
    prefix, remainder = raw.split(begin, 1)
    _old_middle, suffix = remainder.split(end, 1)
    path.write_bytes(prefix + begin + canonical[:-1] + end + suffix)
    require(
        _extract_canonical_memo_object(
            path,
            begin=begin,
            end=end,
            label=label,
        )
        == value,
        f"{label}: canonical mutation did not round-trip exactly",
    )


def mutate_canonical_compact_json_object(
    path: Path,
    *,
    label: str,
    mutate: Callable[[dict[str, object]], None],
) -> None:
    """Mutate one compact canonical JSON artifact without raw-anchor ambiguity."""

    raw = path.read_bytes()

    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            require(key not in result, f"{label}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_nonfinite(token: str) -> object:
        raise SelfTestError(f"{label}: non-finite JSON token {token!r}")

    try:
        value = json.loads(
            raw.decode("ascii", errors="strict"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SelfTestError(f"{label}: invalid compact canonical JSON") from error
    require(type(value) is dict, f"{label}: JSON root must have type object")
    canonical = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    require(raw == canonical, f"{label}: input is not compact canonical JSON")
    require(mutate(value) is None, f"{label}: mutation callback returned a value")
    mutated = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    path.write_bytes(mutated)


def duplicate_complete_c3_fenced_block(
    path: Path,
    *,
    begin: bytes,
    end: bytes,
    label: str,
) -> None:
    """Duplicate one complete text fence rather than only its JSON payload."""

    raw = path.read_bytes()
    opening = b"```text\n" + begin
    closing = end + b"\n```\n"
    require(
        raw.count(opening) == 1 and raw.count(closing) == 1,
        f"{label}: complete fenced block boundaries are not unique",
    )
    block_start = raw.index(opening)
    block_end = raw.index(closing, block_start) + len(closing)
    block = raw[block_start:block_end]
    require(raw.count(block) == 1, f"{label}: complete fenced block is not unique")
    path.write_bytes(raw[:block_end] + b"\n" + block + raw[block_end:])


def common_git_dir(root: Path) -> Path:
    process = run(git_command("rev-parse", "--git-common-dir"), cwd=root)
    require(process.returncode == 0, "cannot resolve temporary Git common directory")
    try:
        value = process.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise SelfTestError("temporary Git common directory is not UTF-8") from error
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=True)


def backup_absolute(paths: Iterable[Path]) -> dict[Path, Backup]:
    result: dict[Path, Backup] = {}
    for path in paths:
        if path.is_symlink():
            raise SelfTestError(f"pristine metadata target is a symlink: {path}")
        if path.exists():
            metadata = path.stat()
            require(
                stat.S_ISREG(metadata.st_mode),
                f"metadata target is not regular: {path}",
            )
            result[path] = Backup(
                exists=True,
                raw=path.read_bytes(),
                mode=stat.S_IMODE(metadata.st_mode),
            )
        else:
            result[path] = Backup(exists=False, raw=b"", mode=0)
    return result


def restore_absolute(saved: dict[Path, Backup]) -> None:
    for path, item in saved.items():
        if path.is_symlink() or path.exists():
            require(not path.is_dir(), f"metadata mutation created a directory: {path}")
            path.unlink()
        if item.exists:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.raw)
            path.chmod(item.mode)


def metadata_attack(
    root: Path,
    *,
    label: str,
    paths: Iterable[Path],
    mutate: Callable[[], None],
    expected_fragment: str,
    failure_expectation: FailureExpectation | None = None,
) -> None:
    saved = backup_absolute(paths)
    try:
        mutate()
        run_checker(
            root,
            expect_success=False,
            expected_fragment=expected_fragment,
            failure_expectation=failure_expectation,
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore_absolute(saved)
    run_checker(root, expect_success=True)


def metadata_invariance(
    root: Path,
    *,
    label: str,
    paths: Iterable[Path],
    mutate: Callable[[], None],
) -> None:
    saved = backup_absolute(paths)
    try:
        before, _ = current_facts(root)
        mutate()
        run_checker(root, expect_success=True)
        after, _ = current_facts(root)
        require(
            after == before,
            "irrelevant local metadata changed emitted candidate facts",
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore_absolute(saved)
    run_checker(root, expect_success=True)


def baseline_first_rebased_attack(
    root: Path,
    *,
    label: str,
    paths: Iterable[str],
    mutate: Callable[[Path], object],
    first_fragment: str,
    semantic_fragment: str,
    first_expectation: FailureExpectation | None = None,
    semantic_expectation: FailureExpectation | None = None,
    repin_stats_for_downstream: bool = False,
    repin_package_script_for_downstream: bool = False,
    restores_tool_readme_anchor_for_downstream: bool = False,
) -> BaselineAttackExecutionReceipt:
    path_tuple = tuple(paths)
    receipt_issuer = _issue_baseline_attack_execution_receipt
    require(
        receipt_issuer is _SEALED_BASELINE_ATTACK_EXECUTION_RECEIPT_ISSUER,
        "baseline attack execution receipt issuer callable changed before lifecycle",
    )
    touched = tuple(dict.fromkeys((*path_tuple, CHECKER_RELATIVE)))
    bypass_corrective_policy = not set(path_tuple).issubset(CORRECTIVE_PATHS)
    bypass_prior_c2_custody = bool(
        set(path_tuple).intersection(
            {
                CORRECTIVE_EVIDENCE,
                PUBLIC_CI_FAILURE_RECEIPT,
            }
        )
    )
    preserved_c2_mutations = tuple(
        relative
        for relative in path_tuple
        if relative in {CORRECTIVE_EVIDENCE, PUBLIC_CI_FAILURE_RECEIPT}
    )
    require(
        not bypass_prior_c2_custody or len(preserved_c2_mutations) == 1,
        "C2 preserved-evidence attack must bind one exact relative path",
    )
    if restores_tool_readme_anchor_for_downstream:
        require(
            path_tuple == ("audit/tools/foundational_sxpid/README.md",)
            and first_fragment
            == (
                "candidate anchor delta differs from the separately reviewed A/M "
                "path policy"
            ),
            "anchor-restoring semantic seam is limited to the exact tool README",
        )
    lifecycle_capability = _BASELINE_LIFECYCLE_AUTHORITY.begin(
        label=label,
        paths=path_tuple,
    )
    observed_first_detail: str | None = None
    observed_semantic_detail: str | None = None
    saved: dict[str, Backup] = {}
    primary: BaseException | None = None
    try:
        _BASELINE_LIFECYCLE_AUTHORITY.observe_baseline(
            lifecycle_capability,
            root=root,
        )
        saved = backup(root, touched)
        _BASELINE_LIFECYCLE_AUTHORITY.observe_mutation(
            lifecycle_capability,
            root=root,
            mutate=mutate,
        )
        if restores_tool_readme_anchor_for_downstream:
            relative = path_tuple[0]
            anchor_blob = run(
                git_command("cat-file", "blob", f"{CURRENT_ANCHOR}:{relative}"),
                cwd=root,
            )
            require(
                anchor_blob.returncode == 0 and anchor_blob.stderr == b"",
                "cannot load the exact anchor tool-README blob",
            )
            require(
                (root / relative).read_bytes() == anchor_blob.stdout,
                "tool-README mutation does not restore the exact anchor bytes",
            )
        expected_first_detail = (
            (f"candidate changed preserved C2 evidence: {preserved_c2_mutations[0]}")
            if bypass_prior_c2_custody
            else (
                "candidate anchor delta differs from the separately reviewed A/M "
                "path policy"
                if bypass_corrective_policy
                else first_fragment
            )
        )
        observed_first_detail = _BASELINE_LIFECYCLE_AUTHORITY.observe_first_rejection(
            lifecycle_capability,
            root=root,
            expected_fragment=expected_first_detail,
            failure_expectation=(
                caller_held_exact_failure_expectation(expected_first_detail)
                if bypass_prior_c2_custody
                else first_expectation
            ),
        )
        if bypass_prior_c2_custody:
            replace_once(
                root / CHECKER_RELATIVE,
                (
                    b"            read_candidate_bytes(relative)\n"
                    b"            == git_blob_at(C2_TOOLING_CORRECTION, relative),\n"
                ),
                b"            True,\n",
            )
        if bypass_corrective_policy or restores_tool_readme_anchor_for_downstream:
            replace_once(
                root / CHECKER_RELATIVE,
                b"        actual_delta == policy_delta,\n",
                b"        True,\n",
            )
        if repin_stats_for_downstream:
            require(
                "crates/pid-core/src/stats.rs" in path_tuple,
                "stats digest repin requested without the stats.rs mutation path",
            )
            mutated_digest = hashlib.sha256(
                (root / "crates/pid-core/src/stats.rs").read_bytes()
            ).hexdigest()
            replace_once(
                root / CHECKER_RELATIVE,
                (
                    b"PACKAGE_STATS_SHA256 = (\n"
                    b'    "204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e"\n'
                    b")"
                ),
                (
                    b"PACKAGE_STATS_SHA256 = (\n"
                    + f'    "{mutated_digest}"\n'.encode("ascii")
                    + b")"
                ),
            )
        if repin_package_script_for_downstream:
            require(
                "scripts/verify-package-archives.sh" in path_tuple,
                "package-script digest repin requested without its mutation path",
            )
            mutated_digest = hashlib.sha256(
                (root / "scripts/verify-package-archives.sh").read_bytes()
            ).hexdigest()
            replace_once(
                root / CHECKER_RELATIVE,
                (
                    b"PACKAGE_ARCHIVE_SCRIPT_SHA256 = (\n"
                    b'    "13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256"\n'
                    b")"
                ),
                (
                    b"PACKAGE_ARCHIVE_SCRIPT_SHA256 = (\n"
                    + f'    "{mutated_digest}"\n'.encode("ascii")
                    + b")"
                ),
            )
        _BASELINE_LIFECYCLE_AUTHORITY.observe_rebase(
            lifecycle_capability,
            root=root,
            prepare=lambda: None,
        )
        observed_semantic_detail = (
            _BASELINE_LIFECYCLE_AUTHORITY.observe_semantic_rejection(
                lifecycle_capability,
                root=root,
                expected_fragment=semantic_fragment,
                failure_expectation=semantic_expectation,
            )
        )
    except BaseException as error:
        primary = error

    cleanup_failures: list[tuple[str, BaseException]] = []
    try:
        _BASELINE_LIFECYCLE_AUTHORITY.restore_after_attempt(
            lifecycle_capability,
            root=root,
            saved=saved,
        )
    except BaseException as error:
        cleanup_failures.append(("baseline restoration", error))

    if primary is not None or cleanup_failures:
        restored = False
        try:
            require_backup_restored(root, saved)
            restored = True
        except BaseException as error:
            cleanup_failures.append(("baseline backup verification", error))
        try:
            run_checker(root, expect_success=True)
        except BaseException as error:
            cleanup_failures.append(("baseline cleanup green replay", error))
        try:
            state_name = _BASELINE_LIFECYCLE_AUTHORITY.state_name(
                lifecycle_capability
            )
            if state_name not in {
                "aborted",
                "consumed_by_baseline_attack_execution_receipt",
            }:
                _BASELINE_LIFECYCLE_AUTHORITY.abort_after_cleanup(
                    lifecycle_capability,
                    reason=(
                        _base_exception_diagnostic(primary)
                        if primary is not None
                        else "baseline cleanup failure"
                    ),
                    cleanup_failures=tuple(
                        f"{cleanup_label}:{_base_exception_diagnostic(error)}"
                        for cleanup_label, error in cleanup_failures
                    ),
                    restored=restored,
                )
        except BaseException as error:
            cleanup_failures.append(("baseline lifecycle abort", error))
        _raise_normalized_sealed_failure(
            label=label,
            primary=primary,
            cleanup_failures=cleanup_failures,
        )

    terminal_primary: BaseException | None = None
    try:
        _BASELINE_LIFECYCLE_AUTHORITY.observe_green_replay(
            lifecycle_capability,
            root=root,
        )
        require(
            type(observed_first_detail) is str
            and type(observed_semantic_detail) is str,
            f"{label}: observed rejection details are unavailable",
        )
        require(
            _issue_baseline_attack_execution_receipt is receipt_issuer
            and receipt_issuer is _SEALED_BASELINE_ATTACK_EXECUTION_RECEIPT_ISSUER,
            "baseline attack execution receipt issuer callable changed after lifecycle",
        )
        return receipt_issuer(lifecycle_capability=lifecycle_capability)
    except BaseException as error:
        terminal_primary = error

    terminal_cleanup_failures: list[tuple[str, BaseException]] = []
    try:
        run_checker(root, expect_success=True)
    except BaseException as error:
        terminal_cleanup_failures.append(("baseline terminal green replay", error))
    try:
        state_name = _BASELINE_LIFECYCLE_AUTHORITY.state_name(lifecycle_capability)
        if state_name not in {
            "aborted",
            "consumed_by_baseline_attack_execution_receipt",
        }:
            _BASELINE_LIFECYCLE_AUTHORITY.abort_after_cleanup(
                lifecycle_capability,
                reason=_base_exception_diagnostic(terminal_primary),
                cleanup_failures=tuple(
                    f"{cleanup_label}:{_base_exception_diagnostic(error)}"
                    for cleanup_label, error in terminal_cleanup_failures
                ),
                restored=True,
            )
    except BaseException as error:
        terminal_cleanup_failures.append(("baseline terminal abort", error))
    _raise_normalized_sealed_failure(
        label=label,
        primary=terminal_primary,
        cleanup_failures=terminal_cleanup_failures,
    )


def hostile_policy_repin_attack(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], object],
    semantic_fragment: str,
) -> None:
    saved = backup(root, (POLICY_RELATIVE, CHECKER_RELATIVE))
    checker = root / CHECKER_RELATIVE
    policy = root / POLICY_RELATIVE
    try:
        old_digest = hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment="policy digest differs",
        )
        new_digest = hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        replace_exact_count(
            checker,
            old_digest,
            new_digest,
            expected_count=2,
        )
        detail = policy_failure_detail(label, semantic_fragment)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=detail,
            failure_expectation=caller_held_exact_failure_expectation(detail),
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def policy_failure_detail(label: str, fragment: str) -> str:
    """Construct one exact post-repin policy rejection from attack context."""

    exact_by_label = {
        "policy-mechanical-resealing": (
            "phase path policy authority contract value changed at "
            "$/mechanical_resealing_permitted"
        ),
        "policy-authorizes-deletions": ("phase path policy must forbid every deletion"),
        "policy-deletion-status": (
            "phase path policy entry 'CHANGELOG.md' is not classified A or M"
        ),
        "policy-unknown-review-class": (
            "phase path policy entry "
            "'audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json' "
            "references an unknown review class"
        ),
        "policy-authority-scope-drift": (
            "phase path policy authority contract value changed at $/scope"
        ),
        "policy-exact-commit-message-drift": (
            "phase path policy exact candidate commit envelope value changed at "
            "$/message/exact_text"
        ),
        "policy-exact-author-identity-drift": (
            "phase path policy exact candidate commit envelope value changed at "
            "$/author/display_name"
        ),
        "policy-exact-committer-identity-drift": (
            "phase path policy exact candidate commit envelope value changed at "
            "$/committer/display_name"
        ),
        "policy-signature-permission-drift": (
            "phase path policy exact candidate commit envelope value changed at "
            "$/signature_headers_permitted"
        ),
        "policy-commit-envelope-negative-record-erasure": (
            "phase path policy commit-envelope hostile-review record value changed "
            "at $/demonstrated_intermediate_false_greens/1"
        ),
        "policy-schema-revision-drift": (
            "phase path policy schema revision value changed at $"
        ),
        "json-type-firewall-schema-revision-boolean": (
            "phase path policy schema revision has the wrong JSON type at $: "
            "expected int, observed bool"
        ),
        "json-type-firewall-authoritative-integer": (
            "phase path policy authority contract has the wrong JSON type at "
            "$/authoritative: expected bool, observed int"
        ),
        "policy-hostile-contracted-total": (
            "phase path policy hostile-suite contract value changed at "
            "$/contracted_total"
        ),
        "policy-hostile-json-type-control-count": (
            "phase path policy hostile-suite contract value changed at "
            "$/separate_controls/json_type_firewall"
        ),
        "policy-hostile-phase-lean-raw-transport-subcontrol-count": (
            "phase path policy hostile-suite contract value changed at "
            "$/separate_controls/phase_lean_raw_transport_subcontrols"
        ),
        "policy-hostile-self-reference-control-count": (
            "phase path policy hostile-suite contract value changed at "
            "$/separate_controls/retained_self_reference_boundary"
        ),
        "policy-supersession-final-authority-weakened": (
            "phase path policy historical remediation supersession value changed "
            "at $/final_authority"
        ),
        "policy-supersession-receipt-digest-drift": (
            "phase path policy historical remediation supersession value changed "
            "at $/historical_receipt_sha256"
        ),
        "policy-supersession-historical-scope-drift": (
            "phase path policy historical remediation supersession value changed "
            "at $/historical_chosen_correction/scope"
        ),
        "policy-supersession-workflow-history-rewritten": (
            "phase path policy historical remediation supersession value changed "
            "at $/historical_workflow_changed"
        ),
        "policy-supersession-retroactive-facts-permitted": (
            "phase path policy historical remediation supersession value changed "
            "at $/retroactive_run_facts_changed"
        ),
    }
    if label in {
        "policy-receipt-obligation-erasure",
        "policy-exact-commit-envelope-obligation-erasure",
        "policy-external-tree-whitespace-obligation-erasure",
        "policy-active-clone-probe-obligation-erasure",
        "policy-portable-parser-obligation-erasure",
        "policy-nineteen-path-obligation-erasure",
    }:
        return "corrective review-class rationale/obligation contracts changed"
    if label.startswith("policy-hostile-family-count-"):
        family = label.removeprefix("policy-hostile-family-count-")
        return (
            "phase path policy hostile-suite contract value changed at "
            f"$/families/{family}"
        )
    return exact_by_label.get(label, fragment)


def public_ci_receipt_failure_detail(label: str, fragment: str) -> str:
    """Construct exact prior public-CI receipt rejection details."""

    exact_by_label = {
        "receipt-duplicate-key": (
            f"{PUBLIC_CI_FAILURE_RECEIPT}: duplicate JSON key 'schema'"
        ),
        "receipt-noncanonical-trailing-whitespace": (
            f"{PUBLIC_CI_FAILURE_RECEIPT}: JSON is not sorted two-space "
            "ASCII form with one final LF"
        ),
        "receipt-schema-revision-boolean": (
            "public CI failure receipt identity has the wrong JSON type at "
            "$/schema_revision: expected int, observed bool"
        ),
        "receipt-skipped-action-omission": (
            "public CI skipped Actions steps array length changed at $"
        ),
        "receipt-skipped-post-action-omission": (
            "public CI skipped Actions steps array length changed at $"
        ),
    }
    return exact_by_label.get(label, fragment)


def portability_receipt_failure_detail(label: str, fragment: str) -> str:
    """Construct exact C2 portability receipt rejection details."""

    exact_by_label = {
        "portability-receipt-duplicate-key": (
            f"{PUBLIC_CI_PORTABILITY_RECEIPT}: duplicate JSON key 'schema'"
        ),
        "portability-receipt-schema-revision-boolean": (
            "C2 portability failure receipt identity has the wrong JSON type at "
            "$/schema_revision: expected int, observed bool"
        ),
        "portability-receipt-skipped-action-omission": (
            "C2 portability skipped Actions steps array length changed at $"
        ),
    }
    return exact_by_label.get(label, fragment)


def hostile_receipt_repin_attack(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], object],
    semantic_fragment: str,
) -> None:
    saved = backup(
        root,
        (
            PUBLIC_CI_FAILURE_RECEIPT,
            CORRECTIVE_EVIDENCE,
            CHECKER_RELATIVE,
        ),
    )
    receipt = root / PUBLIC_CI_FAILURE_RECEIPT
    memo = root / CORRECTIVE_EVIDENCE
    checker = root / CHECKER_RELATIVE
    try:
        old_digest = hashlib.sha256(receipt.read_bytes()).hexdigest().encode("ascii")
        mutate(root)
        preserved_detail = (
            f"candidate changed preserved C2 evidence: {PUBLIC_CI_FAILURE_RECEIPT}"
        )
        run_checker(
            root,
            expect_success=False,
            expected_fragment=preserved_detail,
            failure_expectation=caller_held_exact_failure_expectation(preserved_detail),
        )
        replace_once(
            checker,
            b"        actual_delta == policy_delta,\n",
            b"        True,\n",
        )
        replace_once(
            checker,
            (
                b"            read_candidate_bytes(relative)\n"
                b"            == git_blob_at(C2_TOOLING_CORRECTION, relative),\n"
            ),
            b"            True,\n",
        )
        new_digest = hashlib.sha256(receipt.read_bytes()).hexdigest().encode("ascii")
        replace_exact_count(
            checker,
            old_digest,
            new_digest,
            expected_count=2,
        )
        replace_exact_count(
            memo,
            old_digest,
            new_digest,
            expected_count=2,
        )
        rebase_checker(root)
        detail = public_ci_receipt_failure_detail(label, semantic_fragment)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=detail,
            failure_expectation=caller_held_exact_failure_expectation(detail),
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def hostile_portability_receipt_repin_attack(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], object],
    semantic_fragment: str,
) -> None:
    saved = backup(
        root,
        (
            PUBLIC_CI_PORTABILITY_RECEIPT,
            PORTABILITY_CORRECTIVE_EVIDENCE,
            POLICY_RELATIVE,
            CHECKER_RELATIVE,
        ),
    )
    receipt = root / PUBLIC_CI_PORTABILITY_RECEIPT
    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    policy = root / POLICY_RELATIVE
    checker = root / CHECKER_RELATIVE
    try:
        old_receipt_digest = (
            hashlib.sha256(receipt.read_bytes()).hexdigest().encode("ascii")
        )
        old_memo_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        old_policy_digest = (
            hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        )
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment="changed-byte projection digest mismatch",
        )
        new_receipt_digest = (
            hashlib.sha256(receipt.read_bytes()).hexdigest().encode("ascii")
        )
        replace_once_between(
            checker,
            b"PUBLIC_CI_PORTABILITY_RECEIPT_SHA256 = (\n",
            b"\n)\nEXPECTED_C2_TOOLING_DELTA = (",
            old_receipt_digest,
            new_receipt_digest,
        )
        receipt_blob_anchor = (
            b"    '"
            + PUBLIC_CI_PORTABILITY_RECEIPT.encode("utf-8")
            + b"': ('100644', '"
            + old_receipt_digest
            + b"'),"
        )
        replace_once(
            checker,
            receipt_blob_anchor,
            receipt_blob_anchor.replace(old_receipt_digest, new_receipt_digest),
        )
        replace_once_between(
            memo,
            b"The canonical machine receipt is\n",
            b"\n\n## Frozen ancestry and scope",
            old_receipt_digest,
            new_receipt_digest,
        )
        replace_once_between(
            memo,
            b"PUBLIC_CI_PORTABILITY_FAILURE_PARITY_BEGIN\n",
            b"\nPUBLIC_CI_PORTABILITY_FAILURE_PARITY_END",
            old_receipt_digest,
            new_receipt_digest,
        )
        historical_observation = (
            b"terminal hashes were\nreceipt `" + old_receipt_digest + b"`,"
        )
        replace_once(memo, historical_observation, historical_observation)
        policy_receipt_anchor = (
            b'"historical_receipt_sha256": "' + old_receipt_digest + b'"'
        )
        replace_once(
            policy,
            policy_receipt_anchor,
            policy_receipt_anchor.replace(old_receipt_digest, new_receipt_digest),
        )
        new_memo_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        replace_once_between(
            checker,
            b"PORTABILITY_CORRECTIVE_EVIDENCE_SHA256 = (\n",
            b"\n)\nPUBLIC_CI_FAILURE_RECEIPT = (",
            old_memo_digest,
            new_memo_digest,
        )
        memo_blob_anchor = (
            b"    '"
            + PORTABILITY_CORRECTIVE_EVIDENCE.encode("utf-8")
            + b"': ('100644', '"
            + old_memo_digest
            + b"'),"
        )
        replace_once(
            checker,
            memo_blob_anchor,
            memo_blob_anchor.replace(old_memo_digest, new_memo_digest),
        )
        new_policy_digest = (
            hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        )
        replace_once_between(
            checker,
            b"\nPHASE_PATH_POLICY_SHA256 = (\n",
            b"\n)\nPACKAGE_STATS_SHA256 = (",
            old_policy_digest,
            new_policy_digest,
        )
        policy_blob_anchor = (
            b"    '"
            + POLICY_RELATIVE.encode("utf-8")
            + b"': ('100644', '"
            + old_policy_digest
            + b"'),"
        )
        replace_once(
            checker,
            policy_blob_anchor,
            policy_blob_anchor.replace(old_policy_digest, new_policy_digest),
        )
        rebase_checker(root)
        detail = portability_receipt_failure_detail(label, semantic_fragment)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=detail,
            failure_expectation=caller_held_exact_failure_expectation(detail),
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def _replace_digest_in_named_constant(
    checker: Path,
    *,
    constant_name: str,
    old_digest: bytes,
    new_digest: bytes,
) -> None:
    require(
        old_digest != new_digest,
        f"{constant_name} digest repin did not change the digest",
    )
    start = b"\n" + constant_name.encode("ascii") + b" = (\n"
    end = b"\n)\n"
    raw = checker.read_bytes()
    require(
        raw.count(start) == 1,
        f"{constant_name} declaration is absent or ambiguous",
    )
    prefix, remainder = raw.split(start, 1)
    declaration, suffix = remainder.split(end, 1)
    require(
        declaration.count(old_digest) == 1,
        f"{constant_name} old digest is absent or ambiguous in its declaration",
    )
    rewritten = declaration.replace(old_digest, new_digest, 1)
    checker.write_bytes(prefix + start + rewritten + end + suffix)


def repin_portability_memo_outer_roles(
    checker: Path,
    *,
    old_digest: bytes,
    new_digest: bytes,
) -> None:
    """Repin the memo digest in its named constant and generated blob role."""

    _replace_digest_in_named_constant(
        checker,
        constant_name="PORTABILITY_CORRECTIVE_EVIDENCE_SHA256",
        old_digest=old_digest,
        new_digest=new_digest,
    )
    blob_anchor = (
        b"    '"
        + PORTABILITY_CORRECTIVE_EVIDENCE.encode("utf-8")
        + b"': ('100644', '"
        + old_digest
        + b"'),"
    )
    replace_once(
        checker,
        blob_anchor,
        blob_anchor.replace(old_digest, new_digest),
    )


def _compact_canonical_json_bytes(value: object) -> bytes:
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


def repin_inner_projection(
    checker: Path,
    *,
    constant_name: str,
    old_value: dict[str, object],
    new_value: dict[str, object],
) -> None:
    """Repin only one allowlisted C3 compact-projection declaration."""

    allowed = {
        "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256",
        "EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256",
    }
    require(
        constant_name in allowed,
        "C3 inner projection repin requested a non-allowlisted constant",
    )
    old_digest = hashlib.sha256(_compact_canonical_json_bytes(old_value)).hexdigest()
    new_digest = hashlib.sha256(_compact_canonical_json_bytes(new_value)).hexdigest()
    require(
        old_digest != new_digest,
        "C3 inner compact projection did not change",
    )
    before = checker.read_bytes()
    _replace_digest_in_named_constant(
        checker,
        constant_name=constant_name,
        old_digest=old_digest.encode("ascii"),
        new_digest=new_digest.encode("ascii"),
    )
    after = checker.read_bytes()
    require(
        before != after
        and before.count(old_digest.encode("ascii")) >= 1
        and after.count(new_digest.encode("ascii")) >= 1,
        "C3 inner projection repin did not alter its exact declaration",
    )


def _qualified_exact_type(value: object) -> str:
    exact_type = type(value)
    return f"{exact_type.__module__}.{exact_type.__qualname__}"


def _nonthrowing_failure_repr(value: object) -> str:
    try:
        return repr(value)
    except BaseException as error:
        return f"<repr raised {_qualified_exact_type(error)}>"


def _base_exception_diagnostic(error: BaseException) -> str:
    fields = [f"type={_qualified_exact_type(error)}"]
    if isinstance(error, SystemExit):
        fields.extend(
            (
                f"code_type={_qualified_exact_type(error.code)}",
                f"code={_nonthrowing_failure_repr(error.code)}",
            )
        )
    fields.append(f"repr={_nonthrowing_failure_repr(error)}")
    return ", ".join(fields)


def _cleanup_base_exception_diagnostic(
    failures: list[tuple[str, BaseException]],
) -> str:
    return " | ".join(
        f"{cleanup_label}({_base_exception_diagnostic(error)})"
        for cleanup_label, error in failures
    )


def _raise_normalized_sealed_failure(
    *,
    label: str,
    primary: BaseException | None,
    cleanup_failures: list[tuple[str, BaseException]],
) -> None:
    """Convert every failed sealed path to a caught, nonzero self-test failure."""

    require(
        primary is not None or cleanup_failures,
        "sealed failure normalization lacks a primary or cleanup failure",
    )
    cleanup_detail = _cleanup_base_exception_diagnostic(cleanup_failures)
    if primary is not None:
        message = (
            f"{label}: primary BaseException({_base_exception_diagnostic(primary)})"
        )
        if cleanup_failures:
            message += f"; cleanup BaseExceptions={cleanup_detail}"
        cause = primary
    else:
        message = f"{label}: cleanup BaseExceptions={cleanup_detail}"
        cause = cleanup_failures[0][1]
    raise SelfTestError(message) from cause


def _sealed_nested_candidate_operation(
    root: Path,
    *,
    label: str,
    body: Callable[[], None],
    expected_detail: str | None = None,
) -> SealedNestedCandidateOperationReceipt | None:
    """Always restore memo/checker bytes, modes, status, and a green replay."""

    receipt_issuer = _issue_sealed_nested_candidate_operation_receipt
    require(
        receipt_issuer is _SEALED_NESTED_OPERATION_RECEIPT_ISSUER_CALLABLE,
        "sealed nested operation receipt issuer callable changed before lifecycle",
    )
    require(
        expected_detail is None or type(expected_detail) is str,
        "sealed nested operation expected detail has the wrong exact type",
    )
    before_status = _exact_git_status(root)
    permit = (
        None
        if expected_detail is None
        else _SEALED_LIFECYCLE_AUTHORITY.begin(
            label=label,
            expected_detail=expected_detail,
            root=root,
        )
    )
    saved: dict[str, Backup] = {}
    primary: BaseException | None = None
    try:
        saved = backup(root, (PORTABILITY_CORRECTIVE_EVIDENCE, CHECKER_RELATIVE))
        if permit is None:
            body()
        else:
            observed_detail = _SEALED_LIFECYCLE_AUTHORITY.observe_body_rejection(
                permit,
                body=body,
            )
            require(
                observed_detail == expected_detail,
                "sealed lifecycle observed the wrong semantic rejection",
            )
    except BaseException as error:
        # SystemExit, KeyboardInterrupt, and GeneratorExit still cross the cleanup cut.
        primary = error

    cleanup_failures: list[tuple[str, BaseException]] = []
    post_status: bytes | None = None
    restoration_observed = False
    backup_verified = False

    def verify_status() -> None:
        nonlocal post_status
        post_status = _exact_git_status(root)
        require(
            post_status == before_status,
            "source mutation did not restore exact Git status bytes",
        )

    def restore_or_observe() -> None:
        nonlocal restoration_observed
        if permit is not None and primary is None:
            _SEALED_LIFECYCLE_AUTHORITY.observe_restoration(
                permit,
                saved=saved,
            )
            restoration_observed = True
        else:
            restore(root, saved)

    def verify_backup() -> None:
        nonlocal backup_verified
        require_backup_restored(root, saved)
        backup_verified = True

    for cleanup_label, cleanup in (
        ("restore", restore_or_observe),
        ("exact backup verification", verify_backup),
        ("porcelain-v2 status verification", verify_status),
    ):
        try:
            cleanup()
        except BaseException as error:
            # Continue the remaining cleanup steps even after a control-flow exception.
            cleanup_failures.append((cleanup_label, error))
    try:
        if (
            permit is not None
            and primary is None
            and not cleanup_failures
            and restoration_observed
        ):
            _SEALED_LIFECYCLE_AUTHORITY.observe_green_replay(permit)
        else:
            run_checker(root, expect_success=True)
    except BaseException as error:
        cleanup_failures.append(("green baseline replay", error))
        try:
            run_checker(root, expect_success=True)
        except BaseException as fallback_error:
            cleanup_failures.append(("fallback green baseline replay", fallback_error))
    if primary is not None or cleanup_failures:
        if permit is not None:
            abort_reason = (
                _base_exception_diagnostic(primary)
                if primary is not None
                else "sealed cleanup failure"
            )
            abort_cleanup = tuple(
                f"{cleanup_label}:{_base_exception_diagnostic(error)}"
                for cleanup_label, error in cleanup_failures
            )
            try:
                _SEALED_LIFECYCLE_AUTHORITY.abort_after_cleanup(
                    permit,
                    reason=abort_reason,
                    cleanup_failures=abort_cleanup,
                    restored=(
                        backup_verified
                        and type(post_status) is bytes
                        and post_status == before_status
                    ),
                )
            except BaseException as abort_error:
                cleanup_failures.append(("sealed lifecycle abort", abort_error))
        _raise_normalized_sealed_failure(
            label=label,
            primary=primary,
            cleanup_failures=cleanup_failures,
        )
    require(
        type(post_status) is bytes and post_status == before_status,
        f"{label}: post-cleanup status receipt is unavailable",
    )
    if permit is None:
        return None
    require(
        _issue_sealed_nested_candidate_operation_receipt is receipt_issuer
        and receipt_issuer is _SEALED_NESTED_OPERATION_RECEIPT_ISSUER_CALLABLE,
        "sealed nested operation receipt issuer callable changed after lifecycle",
    )
    receipt = receipt_issuer(
        lifecycle_capability=permit,
    )
    _SEALED_LIFECYCLE_AUTHORITY.require_exact_receipt_edge(permit, receipt)
    validated = _validate_sealed_nested_candidate_operation_receipt(
        receipt,
        expected_label=label,
    )
    require(
        validated is receipt,
        "sealed nested operation issuer returned a substituted receipt",
    )
    return validated


_SEALED_NESTED_CANDIDATE_OPERATION_CALLABLE = _sealed_nested_candidate_operation


def _sealed_base_exception_normalization_probe(
    *,
    control: tuple[str, str, str],
    primary: BaseException | None,
    cleanup_failure: BaseException | None,
) -> None:
    """Exercise the sealed failure cut without touching repository state."""

    global _exact_git_status
    global backup
    global require_backup_restored
    global restore
    global run_checker

    original_helpers = (
        _exact_git_status,
        backup,
        restore,
        require_backup_restored,
        run_checker,
    )
    events: list[str] = []
    status_count = 0
    saved = object()

    def probe_status(_root: Path) -> bytes:
        nonlocal status_count
        status_count += 1
        events.append(f"status-{status_count}")
        return b"exact-probe-status"

    def probe_backup(_root: Path, _paths: Iterable[str]) -> object:
        events.append("backup")
        return saved

    def probe_restore(_root: Path, observed_saved: object) -> None:
        require(observed_saved is saved, "sealed normalization restore token changed")
        events.append("restore")
        if cleanup_failure is not None:
            raise cleanup_failure

    def probe_backup_verification(_root: Path, observed_saved: object) -> None:
        require(observed_saved is saved, "sealed normalization backup token changed")
        events.append("verify")

    def probe_green_replay(_root: Path, *, expect_success: bool) -> None:
        require(expect_success is True, "sealed normalization green replay changed")
        events.append("green")

    def probe_body() -> None:
        events.append("body")
        if primary is not None:
            raise primary

    normalized: SelfTestError | None = None
    try:
        _exact_git_status = probe_status
        backup = probe_backup
        restore = probe_restore
        require_backup_restored = probe_backup_verification
        run_checker = probe_green_replay
        try:
            _sealed_nested_candidate_operation(
                Path("."),
                label=control[1],
                body=probe_body,
            )
        except SelfTestError as error:
            normalized = error
        except BaseException as error:
            raise SelfTestError(
                "sealed normalization probe leaked a control-flow exception: "
                + _base_exception_diagnostic(error)
            ) from error
    finally:
        (
            _exact_git_status,
            backup,
            restore,
            require_backup_restored,
            run_checker,
        ) = original_helpers

    expected_cause = primary if primary is not None else cleanup_failure
    require(
        normalized is not None
        and type(normalized) is SelfTestError
        and str(normalized) == control[2]
        and normalized.__cause__ is expected_cause,
        f"sealed BaseException normalization changed: {control[1]}",
    )
    require(
        tuple(events)
        == (
            "status-1",
            "backup",
            "body",
            "restore",
            "verify",
            "status-2",
            "green",
        ),
        f"sealed BaseException cleanup order changed: {control[1]}",
    )
    raise normalized


_SEALED_ZERO_EXIT_OUTER_PROCESS_BOOTSTRAP = r'''
import hashlib
from pathlib import Path
import sys
import types

source_path = Path(sys.argv[1])
expected_sha256 = sys.argv[2]
tag = sys.argv[3]
raw = source_path.read_bytes()
if hashlib.sha256(raw).hexdigest() != expected_sha256 or source_path.read_bytes() != raw:
    raise SystemExit(97)
module = types.ModuleType("_sealed_outer_probe")
module.__file__ = str(source_path)
sys.modules[module.__name__] = module
namespace = module.__dict__
exec(compile(raw, str(source_path), "exec", dont_inherit=True, optimize=sys.flags.optimize), namespace)
values = {"none": None, "zero": 0, "false": False}
control_names = {
    "none": "sealed_primary_system_exit_none",
    "zero": "sealed_primary_system_exit_zero",
    "false": "sealed_primary_system_exit_false",
}
lines = {
    "none": b'{"error":"SEALED_BASE_EXCEPTION","exception":"SystemExit","exit_value":{"type":"none"}}\n',
    "zero": b'{"error":"SEALED_BASE_EXCEPTION","exception":"SystemExit","exit_value":{"type":"int","value":0}}\n',
    "false": b'{"error":"SEALED_BASE_EXCEPTION","exception":"SystemExit","exit_value":{"type":"bool","value":false}}\n',
}
control = next(
    row
    for row in namespace["EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC"]
    if row[1] == control_names[tag]
)
try:
    namespace["_sealed_base_exception_normalization_probe"](
        control=control,
        primary=SystemExit(values[tag]),
        cleanup_failure=None,
    )
except namespace["SelfTestError"] as error:
    if str(error) != control[2]:
        raise SystemExit(98)
    if source_path.read_bytes() != raw:
        raise SystemExit(99)
    sys.stderr.buffer.write(lines[tag])
    sys.stderr.buffer.flush()
    raise SystemExit(2)
raise SystemExit(96)
'''


def _outer_zero_exit_process_probe(*, tag: str, completion_detail: str) -> None:
    require(
        tag in {"none", "zero", "false"} and type(completion_detail) is str,
        "sealed outer-process probe selector changed",
    )
    raw = SELF_PATH.read_bytes()
    source_sha256 = hashlib.sha256(raw).hexdigest()
    optimize_flag = ("-OO",) if sys.flags.optimize >= 2 else (("-O",) if sys.flags.optimize else ())
    process = subprocess.run(
        (
            sys.executable,
            "-I",
            "-S",
            *optimize_flag,
            "-c",
            _SEALED_ZERO_EXIT_OUTER_PROCESS_BOOTSTRAP,
            os.fspath(SELF_PATH),
            source_sha256,
            tag,
        ),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LANG": "C", "LC_ALL": "C"},
        timeout=30,
    )
    expected_stderr = {
        "none": b'{"error":"SEALED_BASE_EXCEPTION","exception":"SystemExit","exit_value":{"type":"none"}}\n',
        "zero": b'{"error":"SEALED_BASE_EXCEPTION","exception":"SystemExit","exit_value":{"type":"int","value":0}}\n',
        "false": b'{"error":"SEALED_BASE_EXCEPTION","exception":"SystemExit","exit_value":{"type":"bool","value":false}}\n',
    }[tag]
    require(
        type(process.returncode) is int
        and process.returncode == 2
        and process.stdout == b""
        and process.stderr == expected_stderr
        and len(process.stdout) + len(process.stderr) <= 4096
        and SELF_PATH.read_bytes() == raw
        and hashlib.sha256(raw).hexdigest() == source_sha256,
        f"sealed outer-process SystemExit({tag}) status/stream grammar changed",
    )
    raise SelfTestError(completion_detail)


def _record_c3_nested_memo_execution(
    *,
    sealed_receipt: object,
    expected_projection: tuple[
        str,
        str,
        tuple[str, str | None, bytes | None, bytes | None, str | None],
    ],
    _expected_route: str = "real_lifecycle",
) -> C3NestedMemoAttackExecutionReceipt:
    expected_projection = _validate_c3_nested_expected_projection_shape(
        expected_projection,
        context="C3 nested recorder",
    )
    real_issuer = _issue_c3_nested_memo_attack_execution_receipt
    dry_issuer = _dry_c3_nested_memo_attack_execution_receipt
    require(
        real_issuer is _SEALED_C3_NESTED_REAL_ISSUER_CALLABLE
        and dry_issuer is _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE,
        "C3 nested issuer callable changed before receipt linkage",
    )
    validated_child = _validate_sealed_nested_candidate_operation_receipt(
        sealed_receipt,
        expected_label=expected_projection[0],
        _expected_route=_expected_route,
    )
    if _expected_route == "real_lifecycle":
        issued = real_issuer(
            label=expected_projection[0],
            expected_detail=expected_projection[1],
            role_projection=expected_projection[2],
            sealed_receipt=validated_child,
        )
    else:
        issued = dry_issuer(
            expected_projection,
            sealed_receipt=validated_child,
        )
    require(
        _issue_c3_nested_memo_attack_execution_receipt is real_issuer
        and real_issuer is _SEALED_C3_NESTED_REAL_ISSUER_CALLABLE
        and _dry_c3_nested_memo_attack_execution_receipt is dry_issuer
        and dry_issuer is _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE,
        "C3 nested issuer callable changed after receipt linkage",
    )
    require(
        type(issued) is C3NestedMemoAttackExecutionReceipt
        and issued.sealed_receipt is validated_child,
        "C3 nested issuer returned a receipt linked to a different sealed child",
    )
    _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.validate(
        issued,
        expected_route=_expected_route,
    )
    _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.require_exact_child_edge(
        issued,
        child_receipt=validated_child,
        expected_route=_expected_route,
    )
    return issued


def _run_c3_nested_memo_attack(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], object],
    expected_detail: str,
    inner_projection_constant: str | None,
    begin: bytes | None = None,
    end: bytes | None = None,
    object_label: str | None = None,
) -> C3NestedMemoAttackExecutionReceipt:
    """Exercise outer-only rejection, scoped repins, and one exact semantic cut."""

    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    checker = root / CHECKER_RELATIVE
    role_projection = _c3_nested_role_projection(
        inner_projection_constant=inner_projection_constant,
        begin=begin,
        end=end,
        object_label=object_label,
    )
    observed_semantic_detail: str | None = None

    def body() -> None:
        nonlocal observed_semantic_detail
        old_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        if inner_projection_constant is None:
            require(
                begin is None and end is None and object_label is None,
                "outer-only C3 memo attack unexpectedly requested an inner object",
            )
            old_value = None
        else:
            require(
                begin is not None and end is not None and object_label is not None,
                "inner C3 memo attack lacks exact fenced-object boundaries",
            )
            old_value = _extract_canonical_memo_object(
                memo,
                begin=begin,
                end=end,
                label=object_label,
            )
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment="candidate changed-byte projection digest mismatch",
            failure_expectation=caller_held_exact_failure_expectation(
                "candidate changed-byte projection digest mismatch"
            ),
        )
        new_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        repin_portability_memo_outer_roles(
            checker,
            old_digest=old_digest,
            new_digest=new_digest,
        )
        if inner_projection_constant is not None:
            require(
                old_value is not None
                and begin is not None
                and end is not None
                and object_label is not None,
                "inner C3 memo attack lost its original object",
            )
            new_value = _extract_canonical_memo_object(
                memo,
                begin=begin,
                end=end,
                label=object_label,
            )
            repin_inner_projection(
                checker,
                constant_name=inner_projection_constant,
                old_value=old_value,
                new_value=new_value,
            )
        rebase_checker(root)
        semantic_process = run_checker(
            root,
            expect_success=False,
            expected_fragment=expected_detail,
            failure_expectation=caller_held_exact_failure_expectation(expected_detail),
        )
        observed_semantic_detail = _canonical_checker_failure_detail(semantic_process)

    sealed_operation = _sealed_nested_candidate_operation
    require(
        sealed_operation is _SEALED_NESTED_CANDIDATE_OPERATION_CALLABLE,
        "sealed nested operation callable changed before C3 lifecycle",
    )
    sealed_receipt = sealed_operation(
        root,
        label=label,
        body=body,
        expected_detail=expected_detail,
    )
    require(
        _sealed_nested_candidate_operation is sealed_operation
        and sealed_operation is _SEALED_NESTED_CANDIDATE_OPERATION_CALLABLE,
        "sealed nested operation callable changed after C3 lifecycle",
    )
    validated_sealed_receipt = _validate_sealed_nested_candidate_operation_receipt(
        sealed_receipt,
        expected_label=label,
    )
    require(
        type(observed_semantic_detail) is str,
        f"{label}: nested semantic rejection detail is unavailable",
    )
    return _record_c3_nested_memo_execution(
        sealed_receipt=validated_sealed_receipt,
        expected_projection=(label, observed_semantic_detail, role_projection),
    )


def hostile_portability_memo_repin_attack(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], object],
    semantic_fragment: str,
    semantic_expectation: FailureExpectation | None = None,
) -> None:
    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    checker = root / CHECKER_RELATIVE

    def body() -> None:
        old_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment="candidate changed-byte projection digest mismatch",
            failure_expectation=caller_held_exact_failure_expectation(
                "candidate changed-byte projection digest mismatch"
            ),
        )
        new_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        repin_portability_memo_outer_roles(
            checker,
            old_digest=old_digest,
            new_digest=new_digest,
        )
        rebase_checker(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=semantic_fragment,
            failure_expectation=semantic_expectation,
        )

    _sealed_nested_candidate_operation(root, label=label, body=body)


def simple_attack(
    root: Path,
    *,
    label: str,
    paths: Iterable[str],
    mutate: Callable[[Path], object],
    expected_fragment: str,
    failure_expectation: FailureExpectation | None = None,
    force_optimized: bool | None = None,
) -> None:
    saved = backup(root, paths)
    try:
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=expected_fragment,
            failure_expectation=failure_expectation,
            force_optimized=force_optimized,
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def optimization_preflight(temporary: Path) -> None:
    sentinel = temporary / "optimization-sentinel.py"
    sentinel.write_text(
        "assert False, 'optimization sentinel was not removed'\n",
        encoding="utf-8",
        newline="\n",
    )
    normal = run(python_command(sentinel, force_optimized=False), cwd=temporary)
    optimized = run(python_command(sentinel, force_optimized=True), cwd=temporary)
    require(
        normal.returncode != 0 and optimized.returncode == 0,
        "child interpreter does not distinguish normal and optimized assertions",
    )


def entry_isolation_preflight(temporary: Path) -> int:
    """Separate unsafe-startup detection from normal/optimized containment."""

    root = temporary / "entry-isolation"
    root.mkdir()
    shadow_source = root / "json.py"
    shadow_cache = root / "json.pyc"
    shadow_source.write_text(
        'PID_RS_SOURCeless_SHADOW = "sourceless-shadow"\n',
        encoding="utf-8",
        newline="\n",
    )
    py_compile.compile(
        str(shadow_source),
        cfile=str(shadow_cache),
        dfile=str(shadow_source),
        doraise=True,
    )
    shadow_source.unlink()

    vulnerable = root / "vulnerable.py"
    vulnerable.write_text(
        "import json\n"
        "print(getattr(json, 'PID_RS_SOURCeless_SHADOW', 'stdlib-json'))\n",
        encoding="utf-8",
        newline="\n",
    )
    vulnerable_result = run([sys.executable, str(vulnerable)], cwd=root)
    require(
        vulnerable_result.returncode == 0
        and vulnerable_result.stdout == b"sourceless-shadow\n"
        and vulnerable_result.stderr == b"",
        "ordinary Python did not reproduce sourceless stdlib-name shadowing",
    )

    guarded = root / "guarded.py"
    guarded.write_text(
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
        '    print("ERROR: guarded.py requires Python -I -S", '
        "file=_bootstrap_sys.stderr)\n"
        "    raise SystemExit(2)\n"
        "del _bootstrap_sys\n"
        "\n"
        "import json\n"
        "print(getattr(json, 'PID_RS_SOURCeless_SHADOW', 'stdlib-json'))\n",
        encoding="utf-8",
        newline="\n",
    )
    site_marker = root / "sitecustomize-executed"
    user_marker = root / "usercustomize-executed"
    (root / "sitecustomize.py").write_text(
        f"open({str(site_marker)!r}, 'wb').write(b'executed')\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "usercustomize.py").write_text(
        f"open({str(user_marker)!r}, 'wb').write(b'executed')\n",
        encoding="utf-8",
        newline="\n",
    )
    hostile_environment = {
        "PYTHONHOME": str(root / "missing-python-home"),
        "PYTHONPATH": str(root),
        "PYTHONSTARTUP": str(root / "sitecustomize.py"),
    }
    unsafe_environment = dict(hostile_environment)
    unsafe_environment.pop("PYTHONHOME")
    unsafe_result = run(
        [sys.executable, str(guarded)],
        cwd=root,
        environment_overrides=unsafe_environment,
    )
    require(
        unsafe_result.returncode == 2
        and unsafe_result.stdout == b""
        and unsafe_result.stderr == b"ERROR: guarded.py requires Python -I -S\n",
        "guarded entry point did not reject an unsafe interpreter invocation",
    )
    require(
        site_marker.is_file() and user_marker.is_file(),
        "unsafe startup did not reproduce pre-guard customization side effects",
    )
    site_marker.unlink()
    user_marker.unlink()

    isolated_result = run(
        python_command(guarded, force_optimized=False),
        cwd=root,
        environment_overrides=hostile_environment,
    )
    require(
        isolated_result.returncode == 0
        and isolated_result.stdout == b"stdlib-json\n"
        and isolated_result.stderr == b"",
        "isolated safe-path invocation consumed the adjacent sourceless shadow",
    )
    require(
        not site_marker.exists() and not user_marker.exists(),
        "isolated normal startup executed a customization hook",
    )
    optimized_result = run(
        python_command(guarded, force_optimized=True),
        cwd=root,
        environment_overrides=hostile_environment,
    )
    require(
        optimized_result.returncode == 0
        and optimized_result.stdout == b"stdlib-json\n"
        and optimized_result.stderr == b"",
        "isolated optimized startup consumed hostile adjacent or environment state",
    )
    require(
        not site_marker.exists() and not user_marker.exists(),
        "isolated optimized startup executed a customization hook",
    )
    require(
        isolated_result.stdout == optimized_result.stdout
        and isolated_result.stderr == optimized_result.stderr,
        "isolated normal and optimized startup controls differ byte-for-byte",
    )
    return 5


def _static_model_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    require(
        len(functions) == 1,
        f"self-test exact-source function inventory changed: {name}",
    )
    return functions[0]


def _parse_unoptimized_module(source: str, *, filename: str) -> ast.Module:
    tree = compile(
        source,
        filename,
        "exec",
        flags=ast.PyCF_ONLY_AST,
        dont_inherit=True,
        optimize=0,
    )
    require(
        isinstance(tree, ast.Module),
        f"unoptimized semantic parser returned a non-module AST: {filename}",
    )
    return tree


def _static_model_literal_assignment(tree: ast.Module, name: str) -> object:
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    require(
        len(assignments) == 1,
        f"self-test exact-source assignment inventory changed: {name}",
    )
    try:
        return ast.literal_eval(assignments[0].value)
    except (TypeError, ValueError) as error:
        raise SelfTestError(
            f"self-test exact-source assignment is not literal: {name}"
        ) from error


def _portable_ast_projection(value: object) -> object:
    """Project an AST without Python-version-added generic type-parameter fields."""

    if isinstance(value, ast.AST):
        fields = []
        for field in value._fields:
            field_value = getattr(value, field)
            if field == "type_params" and field_value == []:
                continue
            fields.append((field, _portable_ast_projection(field_value)))
        return ("ast", type(value).__name__, tuple(fields))
    if type(value) is list:
        return ("list", tuple(_portable_ast_projection(item) for item in value))
    if type(value) is tuple:
        return ("tuple", tuple(_portable_ast_projection(item) for item in value))
    if value is None:
        return ("none",)
    if value is Ellipsis:
        return ("ellipsis",)
    if type(value) is bool:
        return ("bool", value)
    if type(value) is int:
        return ("int", str(value))
    if type(value) is float:
        return ("float", value.hex())
    if type(value) is complex:
        return ("complex", value.real.hex(), value.imag.hex())
    if type(value) is str:
        return ("str", value)
    if type(value) is bytes:
        return ("bytes", value.hex())
    raise SelfTestError(
        "portable AST projection encountered an unsupported value: "
        f"{type(value).__name__}"
    )


def _portable_function_ast_sha256(function: ast.FunctionDef) -> str:
    raw = (
        json.dumps(
            _portable_ast_projection(function),
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _receipt_lifecycle_portable_ast_sha256(tree: ast.Module) -> str:
    class_names = {
        "BaselineAttackExecutionReceipt",
        "SealedNestedCandidateOperationReceipt",
        "C3NestedMemoAttackExecutionReceipt",
        "DescriptorV4ExecutionReceipt",
        "_ReceiptParentEdge",
        "_IssuedReceiptRecord",
        "_CapabilityOwner",
        "_ReceiptAuthorityState",
        "_ReceiptFailPoint",
        "_ReceiptInjectedExceptionKind",
        "_InjectedReceiptFailure",
        "_ReceiptIssuanceRegistry",
        "_ReceiptRunAuthority",
        "_BaselineLifecycleCapability",
        "_BaselineLifecycleObservation",
        "_BaselineGreenObservation",
        "_MutationAdequateObservation",
        "_FirstRejectionObservation",
        "_RebaseAdequateObservation",
        "_SemanticRejectionObservation",
        "_RestoredObservation",
        "_ReplayGreenObservation",
        "_BaselinePermitReceiptEdge",
        "_LifecycleAbortRecord",
        "_BaselineLifecycleRecord",
        "_BaselineLifecycleAuthority",
        "_SealedLifecycleCapability",
        "_SealedLifecycleObservation",
        "_SealedBodyRejectionObservation",
        "_SealedRestoredObservation",
        "_SealedReplayGreenObservation",
        "_SealedPermitReceiptEdge",
        "_SealedLifecycleRecord",
        "_SealedLifecycleAuthority",
    }
    function_names = {
        "_serial_authority_method",
        "_inject_receipt_transaction_failure",
        "_execute_baseline_mutation",
        "_require_exact_injected_receipt_failure",
        "_probe_baseline_receipt_atomic_rollback",
        "_execute_sealed_operation_body",
        "_probe_sealed_receipt_atomic_rollback",
        "_issue_baseline_attack_execution_receipt",
        "_issue_sealed_nested_candidate_operation_receipt",
        "_issue_c3_nested_memo_attack_execution_receipt",
        "_issue_descriptor_v4_execution_receipt",
        "_validate_baseline_attack_execution_receipt",
        "_validate_sealed_nested_candidate_operation_receipt",
        "_validate_c3_nested_memo_attack_execution_receipt",
        "_validated_c3_nested_execution_projection",
        "baseline_first_rebased_attack",
        "_qualified_exact_type",
        "_nonthrowing_failure_repr",
        "_base_exception_diagnostic",
        "_cleanup_base_exception_diagnostic",
        "_raise_normalized_sealed_failure",
        "_sealed_nested_candidate_operation",
        "_sealed_base_exception_normalization_probe",
        "_outer_zero_exit_process_probe",
        "_record_c3_nested_memo_execution",
        "_run_c3_nested_memo_attack",
        "_record_descriptor_v4_nested_execution",
        "_validated_descriptor_v4_execution_projection",
        "_descriptor_v4_expected_first_detail",
        "_descriptor_v4_expected_paths",
        "_dry_baseline_attack_execution_receipt",
        "_dry_sealed_nested_candidate_operation_receipt",
        "_dry_c3_nested_memo_attack_execution_receipt",
        "_issue_dry_descriptor_v4_execution_receipt",
        "_execution_receipt_runtime_hostile_shape_preflight",
        "_normalized_main_entry",
    }
    assignment_names = {
        "_RECEIPT_RUN_AUTHORITY",
        "_BASELINE_ATTACK_EXECUTION_REGISTRY",
        "_SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY",
        "_C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY",
        "_DESCRIPTOR_V4_EXECUTION_REGISTRY",
        "_BASELINE_LIFECYCLE_AUTHORITY",
        "LEAN_DESCRIPTOR_SELF_TEST_RELATIVE",
        "C3_NESTED_SEALED_RECEIPT_LINKAGE",
        "DESCRIPTOR_V4_BASELINE_RECEIPT_LINKAGE",
        "BASELINE_LIFECYCLE_EVENTS",
        "BASELINE_LIFECYCLE_OBSERVATION_TYPES",
        "BASELINE_PERMIT_RECEIPT_LINKAGE",
        "_BASELINE_LIFECYCLE_OBSERVATION_ISSUER",
        "_SEALED_BASELINE_ATTACK_EXECUTION_RECEIPT_ISSUER",
        "_SEALED_BASELINE_LIFECYCLE_RUN_CHECKER_CALLABLE",
        "_SEALED_BASELINE_LIFECYCLE_REBASE_CHECKER_CALLABLE",
        "_SEALED_BASELINE_LIFECYCLE_RESTORE_CALLABLE",
        "_SEALED_NESTED_OPERATION_RECEIPT_ISSUER_CALLABLE",
        "_SEALED_NESTED_CANDIDATE_OPERATION_CALLABLE",
        "_SEALED_C3_NESTED_REAL_ISSUER_CALLABLE",
        "_SEALED_C3_NESTED_DRY_ISSUER_CALLABLE",
        "_SEALED_DESCRIPTOR_V4_REAL_ISSUER_CALLABLE",
        "_SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE",
        "_SEALED_ZERO_EXIT_OUTER_PROCESS_BOOTSTRAP",
    }
    selected: list[ast.AST] = []
    observed: set[tuple[str, str]] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            selected.append(node)
            observed.add(("class", node.name))
        elif isinstance(node, ast.FunctionDef) and node.name in function_names:
            selected.append(node)
            observed.add(("function", node.name))
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in assignment_names
        ):
            selected.append(node)
            observed.add(("assignment", node.targets[0].id))
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in assignment_names
        ):
            selected.append(node)
            observed.add(("assignment", node.target.id))
    expected = {
        *(("class", name) for name in class_names),
        *(("function", name) for name in function_names),
        *(("assignment", name) for name in assignment_names),
    }
    require(
        observed == expected and len(selected) == len(expected),
        "receipt lifecycle portable AST inventory changed",
    )
    raw = (
        json.dumps(
            _portable_ast_projection(tuple(selected)),
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _complete_module_digest_binding_sites(tree: ast.Module) -> tuple[ast.AST, ...]:
    """Find direct pin writes/deletes and the reviewed dynamic-writer syntax."""

    target = "EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"
    sites: list[ast.AST] = []

    class ModuleBindingVisitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)) and node.id == target:
                sites.append(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)) and node.attr == target:
                sites.append(node)
            self.generic_visit(node)

        def visit_Subscript(self, node: ast.Subscript) -> None:
            if (
                isinstance(node.ctx, (ast.Store, ast.Del))
                and isinstance(node.slice, ast.Constant)
                and node.slice.value == target
            ):
                sites.append(node)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id in {
                "delattr",
                "eval",
                "exec",
                "globals",
                "locals",
                "setattr",
                "vars",
            }:
                sites.append(node)
            elif isinstance(node.func, ast.Attribute) and (
                node.func.attr == "__setattr__"
                or (
                    node.func.attr in {"__setitem__", "update"}
                    and (
                        isinstance(node.func.value, ast.Call)
                        and isinstance(node.func.value.func, ast.Name)
                        and node.func.value.func.id in {"globals", "locals", "vars"}
                        or isinstance(node.func.value, ast.Attribute)
                        and node.func.value.attr == "__dict__"
                    )
                )
            ):
                sites.append(node)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name == target:
                sites.append(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node.name == target:
                sites.append(node)
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            if node.name == target:
                sites.append(node)
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                if bound == target:
                    sites.append(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for alias in node.names:
                if (alias.asname or alias.name) == target:
                    sites.append(node)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name == target:
                sites.append(node)
            self.generic_visit(node)

        def visit_MatchAs(self, node: ast.MatchAs) -> None:
            if node.name == target:
                sites.append(node)
            self.generic_visit(node)

        def visit_MatchStar(self, node: ast.MatchStar) -> None:
            if node.name == target:
                sites.append(node)

    ModuleBindingVisitor().visit(tree)
    return tuple(sites)


def _portable_module_ast_sha256(tree: ast.Module) -> str:
    normalized = copy.deepcopy(tree)
    binding_sites = _complete_module_digest_binding_sites(normalized)
    require(
        len(binding_sites) == 1,
        (
            "self-test complete-module digest has repeated, deleted, or "
            "reviewed dynamic-writer bindings"
        ),
    )
    assignments = [
        node
        for node in normalized.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"
    ]
    require(
        len(assignments) == 1
        and binding_sites[0] is assignments[0].targets[0]
        and isinstance(assignments[0].value, ast.Constant)
        and type(assignments[0].value.value) is str
        and re.fullmatch(r"[0-9a-f]{64}", assignments[0].value.value) is not None,
        "self-test complete-module digest assignment is not one exact literal pin",
    )
    require(
        assignments[0].value.value == EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256,
        "self-test complete-module digest literal does not match runtime pin",
    )
    assignments[0].value = ast.Constant(
        value="<normalized-self-test-module-portable-ast-sha256>"
    )
    raw = (
        json.dumps(
            _portable_ast_projection(normalized),
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _require_complete_module_portable_ast(tree: ast.Module) -> None:
    require(
        _portable_module_ast_sha256(tree)
        == EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256,
        "self-test complete-module portable AST projection changed",
    )


def _wrap_named_call_statement_in_if_false(
    tree: ast.Module,
    *,
    function_name: str,
    callee_name: str,
    call_index: int,
    expected_call_count: int,
) -> None:
    function = _static_model_function(tree, function_name)
    matches: list[tuple[list[ast.stmt], int]] = []

    def visit(node: ast.AST) -> None:
        for _field, value in ast.iter_fields(node):
            if type(value) is list:
                for index, item in enumerate(value):
                    if not isinstance(item, ast.AST):
                        continue
                    if isinstance(item, ast.stmt):
                        expression: ast.AST | None = None
                        if isinstance(item, ast.Expr):
                            expression = item.value
                        elif isinstance(item, ast.Assign):
                            expression = item.value
                        elif isinstance(item, ast.AnnAssign):
                            expression = item.value
                        if (
                            isinstance(expression, ast.Call)
                            and isinstance(expression.func, ast.Name)
                            and expression.func.id == callee_name
                        ):
                            matches.append((value, index))
                    visit(item)
            elif isinstance(value, ast.AST):
                visit(value)

    visit(function)
    require(
        len(matches) == expected_call_count and 0 <= call_index < len(matches),
        f"unreachable-call mutation probe inventory changed: {function_name}",
    )
    statements, index = matches[call_index]
    statements[index] = ast.If(
        test=ast.Constant(value=False),
        body=[statements[index]],
        orelse=[],
    )


def _complete_module_execution_integrity_preflight(
    tree: ast.Module,
) -> tuple[tuple[str, str, str], ...]:
    expected = tuple(
        row
        for row in EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC
        if row[0] == "static_model"
    )
    observed: list[tuple[str, str, str]] = []
    _require_complete_module_portable_ast(tree)
    observed.append(expected[0])

    helper_mutant = copy.deepcopy(tree)
    baseline_helper = _static_model_function(
        helper_mutant,
        "baseline_first_rebased_attack",
    )
    baseline_helper.body.insert(0, ast.Return(value=ast.Constant(value=None)))
    observed.append(
        _expect_execution_receipt_probe_rejection(
            control=expected[1],
            probe=lambda: _require_complete_module_portable_ast(helper_mutant),
        )
    )

    unreachable_specs = (
        (
            "ledger_code_call_unreachable",
            "run_c3_review_ledger_nested_controls",
            0,
            2,
        ),
        (
            "ledger_structural_call_unreachable",
            "run_c3_review_ledger_nested_controls",
            1,
            2,
        ),
        (
            "parity_call_unreachable",
            "run_c3_local_artifact_parity_nested_controls",
            0,
            1,
        ),
    )
    for offset, (_label, function_name, call_index, expected_call_count) in enumerate(
        unreachable_specs,
        start=2,
    ):
        mutant = copy.deepcopy(tree)
        _wrap_named_call_statement_in_if_false(
            mutant,
            function_name=function_name,
            callee_name="_run_c3_nested_memo_attack",
            call_index=call_index,
            expected_call_count=expected_call_count,
        )
        observed.append(
            _expect_execution_receipt_probe_rejection(
                control=expected[offset],
                probe=lambda mutant=mutant: _require_complete_module_portable_ast(
                    mutant
                ),
            )
        )

    digest_assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"
    ]
    require(
        len(digest_assignments) == 1,
        "complete-module digest static probe assignment inventory changed",
    )

    wrong_literal_mutant = copy.deepcopy(tree)
    wrong_literal_assignment = next(
        node
        for node in wrong_literal_mutant.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"
    )
    wrong_literal_assignment.value = ast.Constant(value="0" * 64)
    observed.append(
        _expect_execution_receipt_probe_rejection(
            control=expected[5],
            probe=lambda: _require_complete_module_portable_ast(wrong_literal_mutant),
        )
    )

    duplicate_binding_mutant = copy.deepcopy(tree)
    duplicate_binding_mutant.body.append(copy.deepcopy(digest_assignments[0]))
    observed.append(
        _expect_execution_receipt_probe_rejection(
            control=expected[6],
            probe=lambda: _require_complete_module_portable_ast(
                duplicate_binding_mutant
            ),
        )
    )

    computed_binding_mutant = copy.deepcopy(tree)
    computed_assignment = next(
        node
        for node in computed_binding_mutant.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"
    )
    computed_assignment.value = ast.Call(
        func=ast.Name(id="str", ctx=ast.Load()),
        args=[ast.Constant(value=EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256)],
        keywords=[],
    )
    observed.append(
        _expect_execution_receipt_probe_rejection(
            control=expected[7],
            probe=lambda: _require_complete_module_portable_ast(
                computed_binding_mutant
            ),
        )
    )

    dynamic_binding_mutants: list[ast.Module] = []

    delete_binding_mutant = copy.deepcopy(tree)
    delete_binding_mutant.body.append(
        ast.Delete(
            targets=[
                ast.Name(
                    id="EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256",
                    ctx=ast.Del(),
                )
            ]
        )
    )
    dynamic_binding_mutants.append(delete_binding_mutant)

    globals_setitem_mutant = copy.deepcopy(tree)
    globals_setitem_mutant.body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Call(
                        func=ast.Name(id="globals", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    ),
                    attr="__setitem__",
                    ctx=ast.Load(),
                ),
                args=[
                    ast.Constant(value="EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"),
                    ast.Constant(value="0" * 64),
                ],
                keywords=[],
            )
        )
    )
    dynamic_binding_mutants.append(globals_setitem_mutant)

    globals_update_mutant = copy.deepcopy(tree)
    globals_update_mutant.body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Call(
                        func=ast.Name(id="globals", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    ),
                    attr="update",
                    ctx=ast.Load(),
                ),
                args=[
                    ast.Dict(
                        keys=[
                            ast.Constant(
                                value=("EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256")
                            )
                        ],
                        values=[ast.Constant(value="0" * 64)],
                    )
                ],
                keywords=[],
            )
        )
    )
    dynamic_binding_mutants.append(globals_update_mutant)

    exec_binding_mutant = copy.deepcopy(tree)
    exec_binding_mutant.body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Name(id="exec", ctx=ast.Load()),
                args=[
                    ast.Constant(
                        value=(
                            "EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256 = "
                            + repr("0" * 64)
                        )
                    )
                ],
                keywords=[],
            )
        )
    )
    dynamic_binding_mutants.append(exec_binding_mutant)

    module_setattr_mutant = copy.deepcopy(tree)
    module_setattr_mutant.body.append(
        ast.Expr(
            value=ast.Call(
                func=ast.Name(id="setattr", ctx=ast.Load()),
                args=[
                    ast.Subscript(
                        value=ast.Attribute(
                            value=ast.Name(id="sys", ctx=ast.Load()),
                            attr="modules",
                            ctx=ast.Load(),
                        ),
                        slice=ast.Name(id="__name__", ctx=ast.Load()),
                        ctx=ast.Load(),
                    ),
                    ast.Constant(value="EXPECTED_SELF_TEST_MODULE_PORTABLE_AST_SHA256"),
                    ast.Constant(value="0" * 64),
                ],
                keywords=[],
            )
        )
    )
    dynamic_binding_mutants.append(module_setattr_mutant)

    for offset, mutant in enumerate(dynamic_binding_mutants, start=8):
        observed.append(
            _expect_execution_receipt_probe_rejection(
                control=expected[offset],
                probe=lambda mutant=mutant: _require_complete_module_portable_ast(
                    mutant
                ),
            )
        )

    require(
        type(expected) is tuple
        and tuple(observed) == expected
        and len(observed) == EXECUTION_RECEIPT_STATIC_MODEL_PROBE_COUNT,
        "execution-receipt static/model preflight inventory changed",
    )
    return tuple(observed)


def _descriptor_v4_boundary_substitution_ast_mutant(
    function: ast.FunctionDef,
) -> ast.FunctionDef:
    """Reproduce the duplicate-stdin substitution that motivated the exact seal."""

    replacements = {
        "direct_identity_boundary": "direct_process_stdin_transport",
        (
            "descriptor-factorization Lean portable evidence value changed at "
            "$/lean_executable_identity_boundary"
        ): (
            "descriptor-factorization Lean portable evidence value changed at "
            "$/process_stdin_transport"
        ),
    }
    mutated = copy.deepcopy(function)
    replacement_counts = {old: 0 for old in replacements}
    for node in ast.walk(mutated):
        if not isinstance(node, ast.Constant) or node.value not in replacements:
            continue
        replacement_counts[node.value] += 1
        node.value = replacements[node.value]
    require(
        tuple(replacement_counts.values()) == (1, 1),
        "descriptor-v4 boundary-substitution mutation probe anchors changed",
    )
    return mutated


def _record_descriptor_v4_nested_execution(
    executed: list[DescriptorV4ExecutionReceipt],
    *,
    attack_receipt: object,
    _expected_route: str = "real_lifecycle",
) -> None:
    real_issuer = _issue_descriptor_v4_execution_receipt
    dry_issuer = _issue_dry_descriptor_v4_execution_receipt
    require(
        real_issuer is _SEALED_DESCRIPTOR_V4_REAL_ISSUER_CALLABLE
        and dry_issuer is _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE,
        "descriptor-v4 issuer callable changed before receipt linkage",
    )
    index = len(executed)
    require(
        index < len(EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC),
        "descriptor-v4 execution receipt exceeds the frozen specification",
    )
    expected_control = EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC[index]
    expected_first_detail = _descriptor_v4_expected_first_detail(expected_control)
    validated_attack_receipt = _validate_baseline_attack_execution_receipt(
        attack_receipt,
        expected_label=expected_control[1],
        expected_paths=_descriptor_v4_expected_paths(expected_control),
        expected_first_detail=expected_first_detail,
        expected_semantic_detail=expected_control[4],
        _expected_route=_expected_route,
    )
    require(
        all(
            prior.attack_receipt.capability is not validated_attack_receipt.capability
            for prior in executed
        ),
        "descriptor-v4 baseline attack receipt capability was reused",
    )
    selected_issuer = real_issuer if _expected_route == "real_lifecycle" else dry_issuer
    issued_receipt = selected_issuer(
        control=expected_control,
        attack_receipt=validated_attack_receipt,
    )
    require(
        _issue_descriptor_v4_execution_receipt is real_issuer
        and real_issuer is _SEALED_DESCRIPTOR_V4_REAL_ISSUER_CALLABLE
        and _issue_dry_descriptor_v4_execution_receipt is dry_issuer
        and dry_issuer is _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE,
        "descriptor-v4 issuer callable changed after receipt linkage",
    )
    require(
        type(issued_receipt) is DescriptorV4ExecutionReceipt
        and issued_receipt.attack_receipt is validated_attack_receipt,
        "descriptor-v4 issuer returned a receipt linked to a different baseline",
    )
    _DESCRIPTOR_V4_EXECUTION_REGISTRY.validate(
        issued_receipt,
        expected_route=_expected_route,
    )
    _DESCRIPTOR_V4_EXECUTION_REGISTRY.require_exact_child_edge(
        issued_receipt,
        child_receipt=validated_attack_receipt,
        expected_route=_expected_route,
    )
    executed.append(issued_receipt)


def _validated_descriptor_v4_execution_projection(
    receipts: object,
    *,
    _expected_route: str = "real_lifecycle",
) -> tuple[tuple[str, str, str, str, str], ...]:
    require(
        type(receipts) is list,
        "descriptor-v4 execution receipts are not an exact list",
    )
    controls: list[tuple[str, str, str, str, str]] = []
    for index, receipt in enumerate(receipts):
        require(
            type(receipt) is DescriptorV4ExecutionReceipt,
            f"descriptor-v4 execution receipt {index} has the wrong exact type",
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.validate(
            receipt,
            expected_route=_expected_route,
        )
        require(
            getattr(receipt, "issuer", None) is _DESCRIPTOR_V4_EXECUTION_ISSUER,
            f"descriptor-v4 execution receipt {index} has the wrong issuer",
        )
        require(
            type(getattr(receipt, "capability", None)) is object,
            f"descriptor-v4 execution receipt {index} capability has the wrong type",
        )
        require(
            type(getattr(receipt, "state", None)) is str
            and receipt.state == POST_RESTORE_GREEN_REPLAY_COMPLETED,
            f"descriptor-v4 execution receipt {index} has the wrong completion state",
        )
        require(
            type(receipt.control) is tuple
            and len(receipt.control) == 5
            and all(type(field) is str for field in receipt.control),
            f"descriptor-v4 execution receipt {index} has an invalid control",
        )
        require(
            index < len(EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC)
            and receipt.control == EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC[index],
            "descriptor-v4 ordered execution receipt projection changed",
        )
        expected_first_detail = _descriptor_v4_expected_first_detail(receipt.control)
        _validate_baseline_attack_execution_receipt(
            receipt.attack_receipt,
            expected_label=receipt.control[1],
            expected_paths=_descriptor_v4_expected_paths(receipt.control),
            expected_first_detail=expected_first_detail,
            expected_semantic_detail=receipt.control[4],
            _expected_route=_expected_route,
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.require_exact_child_edge(
            receipt,
            child_receipt=receipt.attack_receipt,
            expected_route=_expected_route,
        )
        controls.append(receipt.control)
    identity_sets = (
        {id(receipt) for receipt in receipts},
        {id(receipt.capability) for receipt in receipts},
        {id(receipt.attack_receipt) for receipt in receipts},
        {id(receipt.attack_receipt.capability) for receipt in receipts},
    )
    aggregate_identities = {
        identity
        for receipt in receipts
        for identity in (
            id(receipt),
            id(receipt.capability),
            id(receipt.attack_receipt),
            id(receipt.attack_receipt.capability),
        )
    }
    require(
        all(len(identities) == len(receipts) for identities in identity_sets)
        and len(aggregate_identities) == 4 * len(receipts),
        "descriptor-v4 execution receipt capability was reused",
    )
    projection = tuple(controls)
    require(
        projection == EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC,
        "descriptor-v4 validated execution receipt inventory changed",
    )
    _DESCRIPTOR_V4_EXECUTION_REGISTRY.collect_many_once(
        tuple(receipts),
        collection="descriptor-v4 aggregate",
        expected_route=_expected_route,
    )
    return projection


def _expect_execution_receipt_probe_rejection(
    *,
    control: tuple[str, str, str],
    probe: Callable[[], object],
) -> tuple[str, str, str]:
    require(
        type(control) is tuple
        and len(control) == 3
        and all(type(field) is str and field != "" for field in control),
        "execution-receipt anti-fraud probe control has the wrong shape",
    )
    try:
        probe()
    except SelfTestError as error:
        require(
            str(error) == control[2],
            f"execution-receipt anti-fraud probe rejected incorrectly: {control[1]}",
        )
        return control
    raise SelfTestError(f"execution-receipt anti-fraud probe survived: {control[1]}")


def _descriptor_v4_expected_first_detail(
    control: tuple[str, str, str, str, str],
) -> str:
    require(
        control[0] in {"artifact", "parser", "source"},
        "descriptor-v4 control has an unknown execution category",
    )
    return (
        control[4]
        if control[0] == "parser"
        else "candidate changed-byte projection digest mismatch"
    )


def _descriptor_v4_expected_paths(
    control: tuple[str, str, str, str, str],
) -> tuple[str, ...]:
    require(
        control[0] in {"artifact", "parser", "source"}
        and type(control[2]) is str,
        "descriptor-v4 control path category changed",
    )
    return (
        (control[2], LEAN_DESCRIPTOR_SELF_TEST_RELATIVE)
        if control[0] == "source"
        else (control[2],)
    )


def _dry_baseline_attack_execution_receipt(
    control: tuple[str, str, str, str, str],
    *,
    label: str | None = None,
    paths: tuple[str, ...] | None = None,
    first_detail: str | None = None,
    semantic_detail: str | None = None,
    state: str = POST_RESTORE_GREEN_REPLAY_COMPLETED,
    issuer: object = _BASELINE_ATTACK_EXECUTION_ISSUER,
    capability: object | None = None,
) -> BaselineAttackExecutionReceipt:
    # Keep this derivation separate from _descriptor_v4_expected_first_detail:
    # the dry producer and validator must not self-confirm one wrong helper.
    independently_derived_first_detail = (
        control[4]
        if control[0] == "parser"
        else "candidate changed-byte projection digest mismatch"
    )
    independently_derived_paths = (
        (control[2], LEAN_DESCRIPTOR_SELF_TEST_RELATIVE)
        if control[0] == "source"
        else (control[2],)
    )
    receipt = BaselineAttackExecutionReceipt(
        label=control[1] if label is None else label,
        paths=independently_derived_paths if paths is None else paths,
        first_detail=(
            independently_derived_first_detail
            if first_detail is None
            else first_detail
        ),
        semantic_detail=control[4] if semantic_detail is None else semantic_detail,
        state=state,
        issuer=issuer,
        capability=object() if capability is None else capability,
    )
    _BASELINE_ATTACK_EXECUTION_REGISTRY.issue(
        receipt,
        route="dry_probe",
    )
    return receipt


def _dry_sealed_nested_candidate_operation_receipt(
    label: str,
    *,
    pre_status_sha256: str = "a" * 64,
    post_status_sha256: str | None = None,
    status_equal: bool = True,
    state: str = POST_RESTORE_GREEN_REPLAY_COMPLETED,
    issuer: object = _SEALED_NESTED_CANDIDATE_OPERATION_ISSUER,
    capability: object | None = None,
) -> SealedNestedCandidateOperationReceipt:
    receipt = SealedNestedCandidateOperationReceipt(
        label=label,
        pre_status_sha256=pre_status_sha256,
        post_status_sha256=(
            pre_status_sha256 if post_status_sha256 is None else post_status_sha256
        ),
        status_equal=status_equal,
        state=state,
        issuer=issuer,
        capability=object() if capability is None else capability,
    )
    _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.issue(
        receipt,
        route="dry_probe",
    )
    return receipt


def _dry_c3_nested_memo_attack_execution_receipt(
    projection: tuple[
        str,
        str,
        tuple[str, str | None, bytes | None, bytes | None, str | None],
    ],
    *,
    expected_detail: str | None = None,
    role: str | None = None,
    state: str = POST_RESTORE_GREEN_REPLAY_COMPLETED,
    issuer: object = _C3_NESTED_MEMO_ATTACK_EXECUTION_ISSUER,
    capability: object | None = None,
    sealed_receipt: SealedNestedCandidateOperationReceipt | None = None,
) -> C3NestedMemoAttackExecutionReceipt:
    projection = _validate_c3_nested_expected_projection_shape(
        projection,
        context="C3 dry constructor",
    )
    role_projection = projection[2]
    linked_sealed_receipt = (
        _dry_sealed_nested_candidate_operation_receipt(projection[0])
        if sealed_receipt is None
        else sealed_receipt
    )
    _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.validate(
        linked_sealed_receipt,
        expected_route="dry_probe",
    )
    if (
        state != POST_RESTORE_GREEN_REPLAY_COMPLETED
        or issuer is not _C3_NESTED_MEMO_ATTACK_EXECUTION_ISSUER
        or capability is not None
    ):
        return C3NestedMemoAttackExecutionReceipt(
            label=projection[0],
            expected_detail=(
                projection[1] if expected_detail is None else expected_detail
            ),
            role=role_projection[0] if role is None else role,
            inner_projection_constant=role_projection[1],
            begin=role_projection[2],
            end=role_projection[3],
            object_label=role_projection[4],
            sealed_receipt=linked_sealed_receipt,
            state=state,
            issuer=issuer,
            edge_capability=object(),
            capability=object() if capability is None else capability,
        )
    receipt = _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue_parent(
        child_receipt=linked_sealed_receipt,
        parent_payload=(
            projection[0],
            projection[1] if expected_detail is None else expected_detail,
            (
                role_projection[0] if role is None else role,
                role_projection[1],
                role_projection[2],
                role_projection[3],
                role_projection[4],
            ),
        ),
        route="dry_probe",
    )
    require(
        type(receipt) is C3NestedMemoAttackExecutionReceipt,
        "C3 dry issuer returned the wrong exact type",
    )
    return receipt


_SEALED_C3_NESTED_DRY_ISSUER_CALLABLE = (
    _dry_c3_nested_memo_attack_execution_receipt
)


def _issue_dry_descriptor_v4_execution_receipt(
    *,
    control: tuple[str, str, str, str, str],
    attack_receipt: BaselineAttackExecutionReceipt,
) -> DescriptorV4ExecutionReceipt:
    receipt = _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue_parent(
        child_receipt=attack_receipt,
        parent_payload=control,
        route="dry_probe",
    )
    require(
        type(receipt) is DescriptorV4ExecutionReceipt,
        "descriptor-v4 dry issuer returned the wrong exact type",
    )
    return receipt


_SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE = _issue_dry_descriptor_v4_execution_receipt


def _dry_descriptor_v4_execution_receipts() -> list[DescriptorV4ExecutionReceipt]:
    receipts = []
    for control in EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC:
        attack_receipt = _dry_baseline_attack_execution_receipt(control)
        receipt = _issue_dry_descriptor_v4_execution_receipt(
            control=control,
            attack_receipt=attack_receipt,
        )
        receipts.append(receipt)
    return receipts


def _execution_receipt_runtime_hostile_shape_preflight() -> tuple[
    tuple[str, str, str], ...
]:
    expected = tuple(
        row
        for row in EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC
        if row[0] == "runtime_hostile"
    )
    expected_by_name = {row[1]: row for row in expected}
    require(
        len(expected_by_name) == EXECUTION_RECEIPT_RUNTIME_HOSTILE_SHAPE_COUNT,
        "execution-receipt runtime hostile control keys changed",
    )
    first_control = EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC[0]

    class BaselineReceiptSubclass(BaselineAttackExecutionReceipt):
        pass

    valid_first_baseline = _dry_baseline_attack_execution_receipt(first_control)
    subclass_baseline = BaselineReceiptSubclass(
        label=valid_first_baseline.label,
        paths=valid_first_baseline.paths,
        first_detail=valid_first_baseline.first_detail,
        semantic_detail=valid_first_baseline.semantic_detail,
        state=valid_first_baseline.state,
        issuer=valid_first_baseline.issuer,
        capability=object(),
    )

    dry_projection_a = _c3_nested_expected_projection(
        label="dry-nested-a",
        expected_detail="dry semantic detail a",
        inner_projection_constant=None,
        begin=None,
        end=None,
        object_label=None,
    )
    dry_projection_b = _c3_nested_expected_projection(
        label="dry-nested-b",
        expected_detail="dry semantic detail b",
        inner_projection_constant="EXPECTED_DRY_PROJECTION_SHA256",
        begin=b"DRY_BEGIN\n",
        end=b"\nDRY_END",
        object_label="dry nested object",
    )
    dry_expected_projection = (dry_projection_a, dry_projection_b)

    def reused_descriptor_baseline_capability() -> None:
        shared_capability = object()
        executed: list[DescriptorV4ExecutionReceipt] = []
        _record_descriptor_v4_nested_execution(
            executed,
            attack_receipt=_dry_baseline_attack_execution_receipt(
                EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC[0],
                capability=shared_capability,
            ),
            _expected_route="dry_probe",
        )
        _record_descriptor_v4_nested_execution(
            executed,
            attack_receipt=_dry_baseline_attack_execution_receipt(
                EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC[1],
                capability=shared_capability,
            ),
            _expected_route="dry_probe",
        )

    def reused_nested_capability() -> None:
        shared_capability = object()
        receipts = [
            _dry_c3_nested_memo_attack_execution_receipt(
                projection,
                capability=shared_capability,
            )
            for projection in dry_expected_projection
        ]
        _validated_c3_nested_execution_projection(
            receipts,
            expected_projection=dry_expected_projection,
            context="C3 dry",
            _expected_route="dry_probe",
        )

    def reused_descriptor_baseline_object() -> None:
        attack_receipt = _dry_baseline_attack_execution_receipt(first_control)
        _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=attack_receipt,
            _expected_route="dry_probe",
        )
        _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=attack_receipt,
            _expected_route="dry_probe",
        )

    def reaggregated_descriptor_receipts() -> None:
        receipts = _dry_descriptor_v4_execution_receipts()
        _validated_descriptor_v4_execution_projection(
            receipts,
            _expected_route="dry_probe",
        )
        _validated_descriptor_v4_execution_projection(
            receipts,
            _expected_route="dry_probe",
        )

    def reused_sealed_receipt_object() -> None:
        sealed_receipt = _dry_sealed_nested_candidate_operation_receipt(
            dry_projection_a[0]
        )
        _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=sealed_receipt,
        )
        _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=sealed_receipt,
        )

    def reaggregated_nested_receipts() -> None:
        receipts = [
            _dry_c3_nested_memo_attack_execution_receipt(projection)
            for projection in dry_expected_projection
        ]
        _validated_c3_nested_execution_projection(
            receipts,
            expected_projection=dry_expected_projection,
            context="C3 dry reaggregate",
            _expected_route="dry_probe",
        )
        _validated_c3_nested_execution_projection(
            receipts,
            expected_projection=dry_expected_projection,
            context="C3 dry reaggregate",
            _expected_route="dry_probe",
        )

    valid_descriptor_receipts = _dry_descriptor_v4_execution_receipts()
    valid_nested_receipts = [
        _dry_c3_nested_memo_attack_execution_receipt(projection)
        for projection in dry_expected_projection
    ]
    unissued_exact_baseline = BaselineAttackExecutionReceipt(
        label=valid_first_baseline.label,
        paths=valid_first_baseline.paths,
        first_detail=valid_first_baseline.first_detail,
        semantic_detail=valid_first_baseline.semantic_detail,
        state=valid_first_baseline.state,
        issuer=valid_first_baseline.issuer,
        capability=object(),
    )
    wrong_issuer_baseline = dataclass_replace(
        valid_first_baseline,
        issuer=object(),
        capability=object(),
    )
    shallow_copy_baseline = copy.copy(valid_first_baseline)
    deepcopy_baseline = copy.deepcopy(
        valid_first_baseline,
        {
            id(valid_first_baseline.issuer): valid_first_baseline.issuer,
            id(valid_first_baseline.capability): valid_first_baseline.capability,
        },
    )
    replaced_baseline = dataclass_replace(valid_first_baseline)

    valid_first_nested = valid_nested_receipts[0]
    unissued_exact_nested = C3NestedMemoAttackExecutionReceipt(
        label=valid_first_nested.label,
        expected_detail=valid_first_nested.expected_detail,
        role=valid_first_nested.role,
        inner_projection_constant=valid_first_nested.inner_projection_constant,
        begin=valid_first_nested.begin,
        end=valid_first_nested.end,
        object_label=valid_first_nested.object_label,
        sealed_receipt=valid_first_nested.sealed_receipt,
        state=valid_first_nested.state,
        issuer=valid_first_nested.issuer,
        edge_capability=object(),
        capability=object(),
    )
    wrong_issuer_nested = dataclass_replace(
        valid_first_nested,
        issuer=object(),
        capability=object(),
    )
    shallow_copy_nested = copy.copy(valid_first_nested)
    deepcopy_nested = copy.deepcopy(
        valid_first_nested,
        {
            id(valid_first_nested.issuer): valid_first_nested.issuer,
            id(valid_first_nested.capability): valid_first_nested.capability,
            id(valid_first_nested.sealed_receipt): valid_first_nested.sealed_receipt,
        },
    )
    replaced_nested = dataclass_replace(valid_first_nested)
    unissued_exact_sealed = dataclass_replace(
        valid_first_nested.sealed_receipt,
        capability=object(),
    )
    unissued_descriptor_wrapper = DescriptorV4ExecutionReceipt(
        control=first_control,
        attack_receipt=valid_first_baseline,
        state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
        issuer=_DESCRIPTOR_V4_EXECUTION_ISSUER,
        edge_capability=object(),
        capability=object(),
    )

    def cross_kind_capability_reuse() -> None:
        baseline = _dry_baseline_attack_execution_receipt(first_control)
        _dry_sealed_nested_candidate_operation_receipt(
            "cross-kind-capability",
            capability=baseline.capability,
        )

    def descriptor_registry_prepopulation() -> None:
        baseline = _dry_baseline_attack_execution_receipt(first_control)
        fake_descriptor = DescriptorV4ExecutionReceipt(
            control=first_control,
            attack_receipt=baseline,
            state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
            issuer=_DESCRIPTOR_V4_EXECUTION_ISSUER,
            edge_capability=object(),
            capability=object(),
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue(
            fake_descriptor,
            route="dry_probe",
        )
        _validated_descriptor_v4_execution_projection(
            [fake_descriptor],
            _expected_route="dry_probe",
        )

    def nested_registry_prepopulation() -> None:
        sealed = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        fake_nested = C3NestedMemoAttackExecutionReceipt(
            label=dry_projection_a[0],
            expected_detail=dry_projection_a[1],
            role=dry_projection_a[2][0],
            inner_projection_constant=dry_projection_a[2][1],
            begin=dry_projection_a[2][2],
            end=dry_projection_a[2][3],
            object_label=dry_projection_a[2][4],
            sealed_receipt=sealed,
            state=POST_RESTORE_GREEN_REPLAY_COMPLETED,
            issuer=_C3_NESTED_MEMO_ATTACK_EXECUTION_ISSUER,
            edge_capability=object(),
            capability=object(),
        )
        _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue(
            fake_nested,
            route="dry_probe",
        )
        _validated_c3_nested_execution_projection(
            [fake_nested],
            expected_projection=(dry_projection_a,),
            context="C3 dry prepopulation",
            _expected_route="dry_probe",
        )

    def registry_route_record_not_exposed() -> None:
        baseline = _dry_baseline_attack_execution_receipt(first_control)
        exposed = _BASELINE_ATTACK_EXECUTION_REGISTRY.validate(
            baseline,
            expected_route="dry_probe",
        )
        require(exposed is None, "receipt registry exposed its internal record")
        _validate_baseline_attack_execution_receipt(
            baseline,
            expected_label=first_control[1],
            expected_paths=(first_control[2],),
            expected_first_detail=_descriptor_v4_expected_first_detail(first_control),
            expected_semantic_detail=first_control[4],
        )

    def descriptor_issuer_callable_substitution() -> None:
        global _issue_dry_descriptor_v4_execution_receipt

        original_issuer = _issue_dry_descriptor_v4_execution_receipt
        baseline = _dry_baseline_attack_execution_receipt(first_control)

        def substituted_issuer(**_kwargs: object) -> None:
            return None

        try:
            _issue_dry_descriptor_v4_execution_receipt = substituted_issuer
            _record_descriptor_v4_nested_execution(
                [],
                attack_receipt=baseline,
                _expected_route="dry_probe",
            )
        finally:
            _issue_dry_descriptor_v4_execution_receipt = original_issuer

    def descriptor_returned_receipt_wrong_baseline() -> None:
        global _issue_dry_descriptor_v4_execution_receipt
        global _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE

        original_issuer = _issue_dry_descriptor_v4_execution_receipt
        original_seal = _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE
        baseline_b = _dry_baseline_attack_execution_receipt(first_control)
        descriptor_b = original_issuer(
            control=first_control,
            attack_receipt=baseline_b,
        )
        baseline_a = _dry_baseline_attack_execution_receipt(first_control)

        def substituted_issuer(**_kwargs: object) -> DescriptorV4ExecutionReceipt:
            return descriptor_b

        try:
            _issue_dry_descriptor_v4_execution_receipt = substituted_issuer
            _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE = substituted_issuer
            _record_descriptor_v4_nested_execution(
                [],
                attack_receipt=baseline_a,
                _expected_route="dry_probe",
            )
        finally:
            _issue_dry_descriptor_v4_execution_receipt = original_issuer
            _SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE = original_seal

    def descriptor_parent_atomic_rollback() -> None:
        child = _dry_baseline_attack_execution_receipt(first_control)
        for fail_at in _ReceiptFailPoint:
            for fail_kind in _ReceiptInjectedExceptionKind:
                old_root = _RECEIPT_RUN_AUTHORITY._probe_root()
                old_projection = _RECEIPT_RUN_AUTHORITY.audit_projection()
                try:
                    _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue_parent(
                        child_receipt=child,
                        parent_payload=first_control,
                        route="dry_probe",
                        fail_at=fail_at,
                        fail_kind=fail_kind,
                    )
                except BaseException as error:
                    _require_exact_injected_receipt_failure(
                        error,
                        fail_at=fail_at,
                        fail_kind=fail_kind,
                    )
                else:
                    raise SelfTestError(
                        "descriptor atomic rollback failpoint survived: "
                        f"{fail_at.value}/{fail_kind.value}"
                    )
                require(
                    _RECEIPT_RUN_AUTHORITY._probe_root() is old_root
                    and _RECEIPT_RUN_AUTHORITY.audit_projection() == old_projection,
                    "descriptor atomic rollback changed the immutable authority root",
                )
                _BASELINE_ATTACK_EXECUTION_REGISTRY.require_unlinked(
                    child,
                    expected_route="dry_probe",
                )
        parent = _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue_parent(
            child_receipt=child,
            parent_payload=first_control,
            route="dry_probe",
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.require_exact_child_edge(
            parent,
            child_receipt=child,
            expected_route="dry_probe",
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue_parent(
            child_receipt=child,
            parent_payload=first_control,
            route="dry_probe",
        )

    def c3_parent_atomic_rollback() -> None:
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        for fail_at in _ReceiptFailPoint:
            for fail_kind in _ReceiptInjectedExceptionKind:
                old_root = _RECEIPT_RUN_AUTHORITY._probe_root()
                old_projection = _RECEIPT_RUN_AUTHORITY.audit_projection()
                try:
                    _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue_parent(
                        child_receipt=child,
                        parent_payload=dry_projection_a,
                        route="dry_probe",
                        fail_at=fail_at,
                        fail_kind=fail_kind,
                    )
                except BaseException as error:
                    _require_exact_injected_receipt_failure(
                        error,
                        fail_at=fail_at,
                        fail_kind=fail_kind,
                    )
                else:
                    raise SelfTestError(
                        "C3 atomic rollback failpoint survived: "
                        f"{fail_at.value}/{fail_kind.value}"
                    )
                require(
                    _RECEIPT_RUN_AUTHORITY._probe_root() is old_root
                    and _RECEIPT_RUN_AUTHORITY.audit_projection() == old_projection,
                    "C3 atomic rollback changed the immutable authority root",
                )
                _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.require_unlinked(
                    child,
                    expected_route="dry_probe",
                )
        parent = _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue_parent(
            child_receipt=child,
            parent_payload=dry_projection_a,
            route="dry_probe",
        )
        _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.require_exact_child_edge(
            parent,
            child_receipt=child,
            expected_route="dry_probe",
        )
        _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue_parent(
            child_receipt=child,
            parent_payload=dry_projection_a,
            route="dry_probe",
        )

    def descriptor_copied_linked_child() -> None:
        child = _dry_baseline_attack_execution_receipt(first_control)
        copied_child = copy.copy(child)
        require(copied_child is not child, "descriptor linked-child copy reused identity")
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.issue_parent(
            child_receipt=copied_child,
            parent_payload=first_control,
            route="dry_probe",
        )

    def c3_copied_linked_child() -> None:
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        copied_child = copy.copy(child)
        require(copied_child is not child, "C3 linked-child copy reused identity")
        _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.issue_parent(
            child_receipt=copied_child,
            parent_payload=dry_projection_a,
            route="dry_probe",
        )

    def descriptor_post_collection_substitution() -> None:
        child = _dry_baseline_attack_execution_receipt(first_control)
        parent = _issue_dry_descriptor_v4_execution_receipt(
            control=first_control,
            attack_receipt=child,
        )
        substituted = dataclass_replace(
            parent,
            edge_capability=object(),
            capability=object(),
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.validate(
            substituted,
            expected_route="dry_probe",
        )

    def c3_post_collection_substitution() -> None:
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        parent = _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=child,
        )
        substituted = dataclass_replace(
            parent,
            edge_capability=object(),
            capability=object(),
        )
        _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.validate(
            substituted,
            expected_route="dry_probe",
        )

    def descriptor_post_collection_reissue() -> None:
        child = _dry_baseline_attack_execution_receipt(first_control)
        _issue_dry_descriptor_v4_execution_receipt(
            control=first_control,
            attack_receipt=child,
        )
        _issue_dry_descriptor_v4_execution_receipt(
            control=first_control,
            attack_receipt=child,
        )

    def c3_post_collection_reissue() -> None:
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=child,
        )
        _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=child,
        )

    def c3_issuer_callable_substitution() -> None:
        global _dry_c3_nested_memo_attack_execution_receipt

        original = _dry_c3_nested_memo_attack_execution_receipt
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])

        def substituted(*_args: object, **_kwargs: object) -> None:
            return None

        try:
            _dry_c3_nested_memo_attack_execution_receipt = substituted
            try:
                _record_c3_nested_memo_execution(
                    sealed_receipt=child,
                    expected_projection=dry_projection_a,
                    _expected_route="dry_probe",
                )
            except SelfTestError:
                _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.require_unlinked(
                    child,
                    expected_route="dry_probe",
                )
                raise
        finally:
            _dry_c3_nested_memo_attack_execution_receipt = original

    def c3_returned_receipt_wrong_sealed_child() -> None:
        global _dry_c3_nested_memo_attack_execution_receipt
        global _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE

        original = _dry_c3_nested_memo_attack_execution_receipt
        original_seal = _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE
        child_b = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        parent_b = original(dry_projection_a, sealed_receipt=child_b)
        child_a = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])

        def substituted(*_args: object, **_kwargs: object) -> C3NestedMemoAttackExecutionReceipt:
            return parent_b

        try:
            _dry_c3_nested_memo_attack_execution_receipt = substituted
            _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE = substituted
            try:
                _record_c3_nested_memo_execution(
                    sealed_receipt=child_a,
                    expected_projection=dry_projection_a,
                    _expected_route="dry_probe",
                )
            except SelfTestError:
                _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.require_unlinked(
                    child_a,
                    expected_route="dry_probe",
                )
                raise
        finally:
            _dry_c3_nested_memo_attack_execution_receipt = original
            _SEALED_C3_NESTED_DRY_ISSUER_CALLABLE = original_seal

    def c3_independent_edge_substitution() -> None:
        child_b = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        parent_b = _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=child_b,
        )
        child_a = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        _C3_NESTED_MEMO_ATTACK_EXECUTION_REGISTRY.require_exact_child_edge(
            parent_b,
            child_receipt=child_a,
            expected_route="dry_probe",
        )

    def sealed_receipt_issuer_callable_substitution() -> None:
        global _issue_sealed_nested_candidate_operation_receipt

        original = _issue_sealed_nested_candidate_operation_receipt

        def substituted(**_kwargs: object) -> None:
            return None

        try:
            _issue_sealed_nested_candidate_operation_receipt = substituted
            _sealed_nested_candidate_operation(
                Path("."),
                label="sealed-issuer-substitution",
                body=lambda: None,
            )
        finally:
            _issue_sealed_nested_candidate_operation_receipt = original

    def baseline_permit_before_observations() -> None:
        permit = _BASELINE_LIFECYCLE_AUTHORITY.begin(
            label="dry-premature-permit",
            paths=(first_control[2],),
        )
        try:
            _issue_baseline_attack_execution_receipt(lifecycle_capability=permit)
        finally:
            _BASELINE_LIFECYCLE_AUTHORITY.restore_after_attempt(
                permit,
                root=ROOT,
                saved={},
            )
            require(
                _BASELINE_LIFECYCLE_AUTHORITY.state_name(permit) == "aborted",
                "premature baseline permit did not become terminal",
            )

    def sealed_declarative_issuer_without_permit() -> None:
        _issue_sealed_nested_candidate_operation_receipt(
            lifecycle_capability=None,
        )

    def baseline_real_generic_leaf_issue() -> None:
        _BASELINE_ATTACK_EXECUTION_REGISTRY.issue(
            valid_first_baseline,
            route="real_lifecycle",
        )

    def sealed_real_generic_leaf_issue() -> None:
        _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.issue(
            valid_first_nested.sealed_receipt,
            route="real_lifecycle",
        )

    def baseline_leaf_arbitrary_collection() -> None:
        leaf = _dry_baseline_attack_execution_receipt(first_control)
        _BASELINE_ATTACK_EXECUTION_REGISTRY.collect_many_once(
            (leaf,),
            collection="caller-selected-baseline-leaf",
            expected_route="dry_probe",
        )

    def sealed_leaf_arbitrary_collection() -> None:
        leaf = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        _SEALED_NESTED_CANDIDATE_OPERATION_REGISTRY.collect_many_once(
            (leaf,),
            collection="caller-selected-sealed-leaf",
            expected_route="dry_probe",
        )

    def descriptor_parent_arbitrary_collection() -> None:
        child = _dry_baseline_attack_execution_receipt(first_control)
        parent = _issue_dry_descriptor_v4_execution_receipt(
            control=first_control,
            attack_receipt=child,
        )
        _DESCRIPTOR_V4_EXECUTION_REGISTRY.collect_many_once(
            (parent,),
            collection="caller-selected-descriptor-parent",
            expected_route="dry_probe",
        )

    def sealed_foreign_thread_issue() -> None:
        errors: list[BaseException] = []

        def issue() -> None:
            try:
                _SEALED_LIFECYCLE_AUTHORITY.issue_completed(None)
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=issue, name="sealed-foreign-thread-probe")
        thread.start()
        thread.join(timeout=10)
        require(
            not thread.is_alive() and len(errors) == 1,
            "sealed foreign-thread probe did not terminate exactly once",
        )
        raise errors[0]

    def sealed_reentrant_begin() -> None:
        permit = _SEALED_LIFECYCLE_AUTHORITY.begin(
            label="sealed-reentrant-probe",
            expected_detail="sealed reentrant probe detail",
            root=ROOT,
        )
        try:
            _SEALED_LIFECYCLE_AUTHORITY.observe_body_rejection(
                permit,
                body=lambda: _SEALED_LIFECYCLE_AUTHORITY.begin(
                    label="sealed-recursive-child",
                    expected_detail="sealed recursive child detail",
                    root=ROOT,
                ),
            )
        finally:
            _SEALED_LIFECYCLE_AUTHORITY.abort_after_cleanup(
                permit,
                reason="expected reentrant rejection",
                cleanup_failures=(),
                restored=True,
            )

    def sealed_noop_body() -> None:
        permit = _SEALED_LIFECYCLE_AUTHORITY.begin(
            label="sealed-noop-probe",
            expected_detail="sealed no-op probe detail",
            root=ROOT,
        )
        try:
            _SEALED_LIFECYCLE_AUTHORITY.observe_body_rejection(
                permit,
                body=lambda: None,
            )
        finally:
            _SEALED_LIFECYCLE_AUTHORITY.abort_after_cleanup(
                permit,
                reason="expected no-op rejection",
                cleanup_failures=(),
                restored=True,
            )

    def authority_record_edge_route_mismatch() -> None:
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        _dry_c3_nested_memo_attack_execution_receipt(
            dry_projection_a,
            sealed_receipt=child,
        )
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        child_record = next(
            record for record in state.receipt_records if record.receipt is child
        )
        changed_child = dataclass_replace(child_record, route="real_lifecycle")
        staged = dataclass_replace(
            state,
            receipt_records=tuple(
                changed_child if record is child_record else record
                for record in state.receipt_records
            ),
        )
        _ReceiptRunAuthority._ReceiptRunAuthority__audit(staged)

    def authority_orphan_capability_owner() -> None:
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        staged = dataclass_replace(
            state,
            capability_owners=(
                *state.capability_owners,
                _CapabilityOwner(
                    capability=object(),
                    owner=object(),
                    kind="orphan capability owner probe",
                ),
            ),
        )
        _ReceiptRunAuthority._ReceiptRunAuthority__audit(staged)

    def authority_unregistered_parent_edge() -> None:
        child = _dry_sealed_nested_candidate_operation_receipt(dry_projection_a[0])
        state = _RECEIPT_RUN_AUTHORITY._probe_root()
        child_record = next(
            record for record in state.receipt_records if record.receipt is child
        )
        fake_edge = _ReceiptParentEdge(
            edge_capability=object(),
            parent_receipt=object(),
            parent_capability=object(),
            child_receipt=child,
            child_capability=child.capability,
            kind=C3_NESTED_SEALED_RECEIPT_LINKAGE,
            route="dry_probe",
        )
        staged_child = dataclass_replace(child_record, parent_edge=fake_edge)
        staged = dataclass_replace(
            state,
            receipt_records=tuple(
                staged_child if record is child_record else record
                for record in state.receipt_records
            ),
        )
        _ReceiptRunAuthority._ReceiptRunAuthority__audit(staged)

    def authority_malformed_baseline_observation() -> None:
        permit = _BASELINE_LIFECYCLE_AUTHORITY.begin(
            label="malformed-baseline-observation-probe",
            paths=(first_control[2],),
        )
        try:
            state = _RECEIPT_RUN_AUTHORITY._probe_root()
            record = next(
                record
                for record in state.lifecycle_records
                if record.permit is permit
            )
            observation = _BaselineGreenObservation(
                permit=permit,
                ordinal=0,
                event_ordinal=state.version + 1,
                event="baseline",
                operation=lambda: None,
                subject=[],
                artifact={},
                snapshot=(),
                detail=None,
                predecessor=None,
                issuer=_BASELINE_LIFECYCLE_OBSERVATION_ISSUER,
                capability=object(),
            )
            staged_record = dataclass_replace(
                record,
                state="pending_mutation",
                root=ROOT,
                baseline_snapshot=(),
                observations=(observation,),
            )
            staged = dataclass_replace(
                state,
                lifecycle_records=tuple(
                    staged_record if candidate is record else candidate
                    for candidate in state.lifecycle_records
                ),
                capability_owners=(
                    *state.capability_owners,
                    _CapabilityOwner(
                        capability=observation.capability,
                        owner=observation,
                        kind="baseline lifecycle observation baseline",
                    ),
                ),
            )
            _ReceiptRunAuthority._ReceiptRunAuthority__audit(staged)
        finally:
            _BASELINE_LIFECYCLE_AUTHORITY.restore_after_attempt(
                permit,
                root=ROOT,
                saved={},
            )

    probes: tuple[Callable[[], object], ...] = (
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=None,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt={},
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=subclass_baseline,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=wrong_issuer_baseline,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=unissued_exact_baseline,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=shallow_copy_baseline,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=deepcopy_baseline,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=replaced_baseline,
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=valid_first_baseline,
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=_dry_baseline_attack_execution_receipt(
                first_control,
                label="wrong-label",
            ),
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=_dry_baseline_attack_execution_receipt(
                first_control,
                paths=("wrong/path",),
            ),
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=_dry_baseline_attack_execution_receipt(
                first_control,
                first_detail="wrong first detail",
            ),
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=_dry_baseline_attack_execution_receipt(
                first_control,
                semantic_detail="wrong semantic detail",
            ),
            _expected_route="dry_probe",
        ),
        lambda: _record_descriptor_v4_nested_execution(
            [],
            attack_receipt=_dry_baseline_attack_execution_receipt(
                first_control,
                state="before_green_replay",
            ),
            _expected_route="dry_probe",
        ),
        reused_descriptor_baseline_capability,
        reused_descriptor_baseline_object,
        lambda: _validated_descriptor_v4_execution_projection(
            [unissued_descriptor_wrapper, *valid_descriptor_receipts[1:]],
            _expected_route="dry_probe",
        ),
        lambda: _validated_descriptor_v4_execution_projection(
            valid_descriptor_receipts,
        ),
        reaggregated_descriptor_receipts,
        lambda: _validated_descriptor_v4_execution_projection(
            [],
            _expected_route="dry_probe",
        ),
        lambda: _validated_descriptor_v4_execution_projection(
            [
                valid_descriptor_receipts[1],
                valid_descriptor_receipts[0],
                *valid_descriptor_receipts[2:],
            ],
            _expected_route="dry_probe",
        ),
        lambda: _validated_descriptor_v4_execution_projection(
            [
                valid_descriptor_receipts[0],
                valid_descriptor_receipts[0],
                *valid_descriptor_receipts[2:],
            ],
            _expected_route="dry_probe",
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_primary_system_exit_none"],
            primary=SystemExit(None),
            cleanup_failure=None,
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_primary_system_exit_zero"],
            primary=SystemExit(0),
            cleanup_failure=None,
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_primary_system_exit_false"],
            primary=SystemExit(False),
            cleanup_failure=None,
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_primary_system_exit_nonzero_with_cleanup"],
            primary=SystemExit(7),
            cleanup_failure=KeyboardInterrupt("cleanup-interrupt"),
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_primary_keyboard_interrupt"],
            primary=KeyboardInterrupt("primary-interrupt"),
            cleanup_failure=None,
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_primary_generator_exit"],
            primary=GeneratorExit("primary-generator-exit"),
            cleanup_failure=None,
        ),
        lambda: _sealed_base_exception_normalization_probe(
            control=expected_by_name["sealed_cleanup_system_exit_zero"],
            primary=None,
            cleanup_failure=SystemExit(0),
        ),
        lambda: _validate_sealed_nested_candidate_operation_receipt(
            None,
            expected_label=dry_projection_a[0],
            _expected_route="dry_probe",
        ),
        lambda: _validate_sealed_nested_candidate_operation_receipt(
            unissued_exact_sealed,
            expected_label=dry_projection_a[0],
            _expected_route="dry_probe",
        ),
        lambda: _validate_sealed_nested_candidate_operation_receipt(
            valid_first_nested.sealed_receipt,
            expected_label=dry_projection_a[0],
        ),
        reused_sealed_receipt_object,
        lambda: _validate_sealed_nested_candidate_operation_receipt(
            _dry_sealed_nested_candidate_operation_receipt(
                dry_projection_a[0],
                post_status_sha256="b" * 64,
                status_equal=False,
            ),
            expected_label=dry_projection_a[0],
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            None,
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            wrong_issuer_nested,
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            unissued_exact_nested,
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            shallow_copy_nested,
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            deepcopy_nested,
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            replaced_nested,
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            valid_first_nested,
            expected_projection=dry_projection_a,
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            _dry_c3_nested_memo_attack_execution_receipt(
                dry_projection_a,
                role="inner_projection",
            ),
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            _dry_c3_nested_memo_attack_execution_receipt(
                dry_projection_a,
                expected_detail="wrong nested detail",
            ),
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        reused_nested_capability,
        reaggregated_nested_receipts,
        lambda: _validated_c3_nested_execution_projection(
            [],
            expected_projection=(dry_projection_a,),
            context="C3 review-ledger",
            _expected_route="dry_probe",
        ),
        lambda: _validated_c3_nested_execution_projection(
            [],
            expected_projection=(dry_projection_a,),
            context="C3 local-artifact-parity",
            _expected_route="dry_probe",
        ),
        lambda: _validated_c3_nested_execution_projection(
            [valid_nested_receipts[1], valid_nested_receipts[0]],
            expected_projection=dry_expected_projection,
            context="C3 dry",
            _expected_route="dry_probe",
        ),
        lambda: _validated_c3_nested_execution_projection(
            [valid_nested_receipts[0], valid_nested_receipts[0]],
            expected_projection=dry_expected_projection,
            context="C3 dry",
            _expected_route="dry_probe",
        ),
        lambda: _issue_baseline_attack_execution_receipt(
            lifecycle_capability=None,
        ),
        cross_kind_capability_reuse,
        descriptor_registry_prepopulation,
        nested_registry_prepopulation,
        registry_route_record_not_exposed,
        descriptor_issuer_callable_substitution,
        descriptor_returned_receipt_wrong_baseline,
        lambda: _validate_baseline_attack_execution_receipt(
            pickle.loads(pickle.dumps(valid_first_baseline)),
            expected_label=first_control[1],
            expected_paths=(first_control[2],),
            expected_first_detail=_descriptor_v4_expected_first_detail(first_control),
            expected_semantic_detail=first_control[4],
            _expected_route="dry_probe",
        ),
        lambda: _validate_sealed_nested_candidate_operation_receipt(
            pickle.loads(pickle.dumps(valid_first_nested.sealed_receipt)),
            expected_label=dry_projection_a[0],
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            pickle.loads(pickle.dumps(valid_first_nested)),
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validated_descriptor_v4_execution_projection(
            [pickle.loads(pickle.dumps(valid_descriptor_receipts[0]))],
            _expected_route="dry_probe",
        ),
        lambda: _validate_baseline_attack_execution_receipt(
            object.__new__(BaselineAttackExecutionReceipt),
            expected_label=first_control[1],
            expected_paths=(first_control[2],),
            expected_first_detail=_descriptor_v4_expected_first_detail(first_control),
            expected_semantic_detail=first_control[4],
            _expected_route="dry_probe",
        ),
        lambda: _validate_sealed_nested_candidate_operation_receipt(
            object.__new__(SealedNestedCandidateOperationReceipt),
            expected_label=dry_projection_a[0],
            _expected_route="dry_probe",
        ),
        lambda: _validate_c3_nested_memo_attack_execution_receipt(
            object.__new__(C3NestedMemoAttackExecutionReceipt),
            expected_projection=dry_projection_a,
            _expected_route="dry_probe",
        ),
        lambda: _validated_descriptor_v4_execution_projection(
            [object.__new__(DescriptorV4ExecutionReceipt)],
            _expected_route="dry_probe",
        ),
        lambda: _issue_baseline_attack_execution_receipt(
            lifecycle_capability=object.__new__(_BaselineLifecycleCapability),
        ),
        descriptor_parent_atomic_rollback,
        c3_parent_atomic_rollback,
        descriptor_copied_linked_child,
        c3_copied_linked_child,
        descriptor_post_collection_substitution,
        c3_post_collection_substitution,
        descriptor_post_collection_reissue,
        c3_post_collection_reissue,
        c3_issuer_callable_substitution,
        c3_returned_receipt_wrong_sealed_child,
        c3_independent_edge_substitution,
        sealed_receipt_issuer_callable_substitution,
        lambda: _outer_zero_exit_process_probe(
            tag="none",
            completion_detail=expected_by_name[
                "outer_sealed_primary_system_exit_none"
            ][2],
        ),
        lambda: _outer_zero_exit_process_probe(
            tag="zero",
            completion_detail=expected_by_name[
                "outer_sealed_primary_system_exit_zero"
            ][2],
        ),
        lambda: _outer_zero_exit_process_probe(
            tag="false",
            completion_detail=expected_by_name[
                "outer_sealed_primary_system_exit_false"
            ][2],
        ),
        baseline_permit_before_observations,
        sealed_declarative_issuer_without_permit,
        baseline_real_generic_leaf_issue,
        sealed_real_generic_leaf_issue,
        baseline_leaf_arbitrary_collection,
        sealed_leaf_arbitrary_collection,
        descriptor_parent_arbitrary_collection,
        sealed_foreign_thread_issue,
        sealed_reentrant_begin,
        sealed_noop_body,
        authority_record_edge_route_mismatch,
        authority_orphan_capability_owner,
        authority_unregistered_parent_edge,
        authority_malformed_baseline_observation,
    )
    require(
        len(probes) == len(expected) == EXECUTION_RECEIPT_RUNTIME_HOSTILE_SHAPE_COUNT,
        "execution-receipt runtime hostile-shape probe table changed",
    )
    observed = tuple(
        _expect_execution_receipt_probe_rejection(control=control, probe=probe)
        for control, probe in zip(expected, probes, strict=True)
    )
    require(
        observed == expected,
        "execution-receipt runtime hostile-shape preflight inventory changed",
    )
    return observed


def _static_c3_nested_control_source_model(tree: ast.Module) -> None:
    """Bind the uncounted C3 ledger/parity and descriptor-v4 control design."""

    require(
        type(EXPECTED_RECEIPT_LIFECYCLE_PORTABLE_AST_SHA256) is str
        and re.fullmatch(
            r"[0-9a-f]{64}",
            EXPECTED_RECEIPT_LIFECYCLE_PORTABLE_AST_SHA256,
        )
        is not None
        and _receipt_lifecycle_portable_ast_sha256(tree)
        == EXPECTED_RECEIPT_LIFECYCLE_PORTABLE_AST_SHA256,
        "receipt lifecycle portable AST projection changed",
    )
    require(
        type(C3_REVIEW_LEDGER_EXECUTION_COUNT) is int
        and C3_REVIEW_LEDGER_EXECUTION_COUNT == 85
        and type(C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT) is int
        and C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT == 19
        and type(C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT) is int
        and C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT == 21
        and type(DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT) is int
        and DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT == 14
        and type(DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT) is int
        and DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT == 2
        and type(DESCRIPTOR_V4_PARSER_SUBCONTROL_COUNT) is int
        and DESCRIPTOR_V4_PARSER_SUBCONTROL_COUNT == 2
        and type(DESCRIPTOR_V4_NESTED_EXECUTION_COUNT) is int
        and DESCRIPTOR_V4_NESTED_EXECUTION_COUNT == 18
        and DESCRIPTOR_V4_NESTED_EXECUTION_COUNT
        == (
            DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT
            + DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT
            + DESCRIPTOR_V4_PARSER_SUBCONTROL_COUNT
        ),
        "C3 nested-control count constants changed",
    )

    descriptor_v4_spec = _static_model_literal_assignment(
        tree,
        "EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC",
    )
    descriptor_v4_spec_raw = (
        json.dumps(
            descriptor_v4_spec,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    require(
        type(descriptor_v4_spec) is tuple
        and len(descriptor_v4_spec) == DESCRIPTOR_V4_NESTED_EXECUTION_COUNT
        and all(
            type(row) is tuple
            and len(row) == 5
            and all(type(field) is str for field in row)
            for row in descriptor_v4_spec
        ),
        "descriptor-v4 nested-control specification shape changed",
    )
    descriptor_v4_categories = tuple(row[0] for row in descriptor_v4_spec)
    descriptor_v4_labels = tuple(row[1] for row in descriptor_v4_spec)
    descriptor_v4_keys = tuple(row[:4] for row in descriptor_v4_spec)
    require(
        descriptor_v4_categories
        == (
            ("artifact",) * DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT
            + ("parser",) * DESCRIPTOR_V4_PARSER_SUBCONTROL_COUNT
            + ("source",) * DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT
        )
        and len(set(descriptor_v4_labels)) == DESCRIPTOR_V4_NESTED_EXECUTION_COUNT
        and len(set(descriptor_v4_keys)) == DESCRIPTOR_V4_NESTED_EXECUTION_COUNT
        and descriptor_v4_spec == EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC
        and hashlib.sha256(descriptor_v4_spec_raw).hexdigest()
        == EXPECTED_DESCRIPTOR_V4_NESTED_CONTROL_SPEC_SHA256,
        "descriptor-v4 exact 14+2+2 nested-control specification changed",
    )

    portability_runner = _static_model_function(
        tree,
        "run_public_ci_portability_evidence_attacks",
    )
    nested_runner_names = {
        "run_c3_review_ledger_nested_controls",
        "run_c3_local_artifact_parity_nested_controls",
    }
    nested_calls = [
        node
        for node in ast.walk(portability_runner)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in nested_runner_names
    ]
    exact_label_branches = [
        node
        for node in ast.walk(portability_runner)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "label"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "portability-memo-stale-optimized-credit"
    ]
    branch_calls = (
        [
            node.func.id
            for node in ast.walk(exact_label_branches[0])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in nested_runner_names
        ]
        if len(exact_label_branches) == 1
        else []
    )
    require(
        len(nested_calls) == 2
        and sorted(branch_calls) == sorted(nested_runner_names)
        and not any(
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "attacks"
            for node in ast.walk(exact_label_branches[0])
        ),
        "C3 nested runners moved outside their one counted stale-memo branch",
    )
    require(
        not any(
            isinstance(node, ast.Name) and node.id == "review_projection_mutations"
            for node in ast.walk(tree)
        ),
        "obsolete raw C3 review-projection mutation loop remains",
    )

    def literal_assignment(function_name: str, assignment_name: str) -> object:
        function = _static_model_function(tree, function_name)
        assignments = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == assignment_name
        ]
        require(
            len(assignments) == 1,
            f"C3 static assignment inventory changed: {assignment_name}",
        )
        try:
            return ast.literal_eval(assignments[0].value)
        except (TypeError, ValueError) as error:
            raise SelfTestError(
                f"C3 static assignment is not literal: {assignment_name}"
            ) from error

    positive_codes = literal_assignment(
        "run_c3_review_ledger_nested_controls",
        "positive_codes",
    )
    negative_codes = literal_assignment(
        "run_c3_review_ledger_nested_controls",
        "negative_codes",
    )
    structural_specs = literal_assignment(
        "run_c3_review_ledger_nested_controls",
        "structural_specs",
    )
    families = literal_assignment(
        "run_c3_local_artifact_parity_nested_controls",
        "families",
    )

    def literal_projection_sha256(value: object) -> str:
        raw = (
            json.dumps(
                value,
                ensure_ascii=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
        return hashlib.sha256(raw).hexdigest()

    require(
        type(positive_codes) is tuple
        and len(positive_codes) == 18
        and literal_projection_sha256(positive_codes)
        == "0e59f2762819f019c82c099c28b4d2bcf07e79d139f8dcdaacb51e6a6a828daa"
        and type(negative_codes) is tuple
        and len(negative_codes) == 46
        and literal_projection_sha256(negative_codes)
        == "d499a58b0ea03e24f4d632f69c08081a5c7d0f4575afa35e334a06f49a404314",
        "C3 exact 18-positive/46-negative code specification changed",
    )
    require(
        type(structural_specs) is tuple
        and len(structural_specs) == 21
        and literal_projection_sha256(structural_specs)
        == "1a0a76093b57d2ec8ac67fd0a19181f5ebe4f8b0d8b8b604fead6671b6294722",
        "C3 exact 21-entry ledger structural specification changed",
    )
    require(
        type(families) is tuple and len(families) == 19,
        "C3 parity family count changed",
    )
    family_variant_counts = tuple(len(family[1]) for family in families)
    flattened_variants = tuple(variant for family in families for variant in family[1])
    require(
        family_variant_counts == (1,) * 13 + (2, 2) + (1,) * 4
        and len(flattened_variants) == 21
        and sum(variant[2] is True for variant in flattened_variants) == 19
        and sum(variant[2] is False for variant in flattened_variants) == 2
        and tuple(variant[0] for variant in flattened_variants[:2])
        == ("sentinel_delete", "block_duplicate")
        and literal_projection_sha256(families)
        == "77b822dcd920ff9e8f1e97eb86078c974ad2f4c7e0cf2e464fec98ee0cd92465",
        "C3 exact 19-family/21-execution parity specification changed",
    )

    ledger_runner = _static_model_function(
        tree,
        "run_c3_review_ledger_nested_controls",
    )
    ledger_attack_calls = [
        node
        for node in ast.walk(ledger_runner)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_c3_nested_memo_attack"
    ]
    ledger_inner_keywords = [
        keyword.value
        for call in ledger_attack_calls
        for keyword in call.keywords
        if keyword.arg == "inner_projection_constant"
    ]
    require(
        len(ledger_attack_calls) == 2
        and len(ledger_inner_keywords) == 2
        and all(
            isinstance(value, ast.Constant)
            and value.value == "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256"
            for value in ledger_inner_keywords
        ),
        "C3 ledger controls no longer always request the one inner repin",
    )
    parity_runner = _static_model_function(
        tree,
        "run_c3_local_artifact_parity_nested_controls",
    )
    parity_attack_calls = [
        node
        for node in ast.walk(parity_runner)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_run_c3_nested_memo_attack"
    ]
    parity_inner_keywords = [
        keyword.value
        for call in parity_attack_calls
        for keyword in call.keywords
        if keyword.arg == "inner_projection_constant"
    ]
    require(
        len(parity_attack_calls) == 1
        and len(parity_inner_keywords) == 1
        and isinstance(parity_inner_keywords[0], ast.IfExp)
        and isinstance(parity_inner_keywords[0].test, ast.Name)
        and parity_inner_keywords[0].test.id == "inner_repin"
        and isinstance(parity_inner_keywords[0].body, ast.Constant)
        and parity_inner_keywords[0].body.value
        == "EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256"
        and isinstance(parity_inner_keywords[0].orelse, ast.Constant)
        and parity_inner_keywords[0].orelse.value is None,
        "C3 parity inner-versus-outer-only repin selection changed",
    )

    extractor = _static_model_function(tree, "_extract_canonical_memo_object")
    extractor_source = ast.unparse(extractor)
    require(
        "object_pairs_hook=reject_duplicate_keys" in extractor_source
        and "parse_constant=reject_nonfinite" in extractor_source
        and ".decode('utf-8', errors='strict')" in extractor_source
        and ".decode('ascii', errors='strict')" in extractor_source
        and "type(value) is dict" in extractor_source
        and "sort_keys=True" in extractor_source
        and "indent=2" in extractor_source
        and "ensure_ascii=True" in extractor_source
        and "allow_nan=False" in extractor_source
        and "prefix.endswith(b'```text\\n')" in extractor_source
        and "suffix.startswith(b'\\n```\\n')" in extractor_source,
        "C3 canonical fenced-JSON extractor protections changed",
    )
    memo_mutator_source = ast.unparse(
        _static_model_function(tree, "mutate_canonical_memo_object")
    )
    require(
        "canonical[:-1] + end" in memo_mutator_source
        and "_extract_canonical_memo_object" in memo_mutator_source,
        "C3 fenced-JSON mutation reconstruction changed",
    )

    repin = _static_model_function(tree, "repin_inner_projection")
    allowed_assignments = [
        node
        for node in ast.walk(repin)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "allowed"
    ]
    require(
        len(allowed_assignments) == 1
        and ast.literal_eval(allowed_assignments[0].value)
        == {
            "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256",
            "EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256",
        },
        "C3 inner projection repin allowlist changed",
    )
    repin_literals = {
        node.value
        for node in ast.walk(repin)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    require(
        "EXPECTED_C3_PRECOMMIT_REVIEW" not in repin_literals
        and "EXPECTED_C3_LOCAL_ARTIFACT_PARITY" not in repin_literals,
        "C3 inner repin can rewrite an expected object rather than its digest",
    )
    outer_repin = _static_model_function(
        tree,
        "repin_portability_memo_outer_roles",
    )
    outer_repin_source = ast.unparse(outer_repin)
    require(
        outer_repin_source.count("PORTABILITY_CORRECTIVE_EVIDENCE_SHA256") == 1
        and outer_repin_source.count("PORTABILITY_CORRECTIVE_EVIDENCE") == 2
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_replace_digest_in_named_constant"
            for node in ast.walk(outer_repin)
        )
        == 1
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "replace_once"
            for node in ast.walk(outer_repin)
        )
        == 1,
        "C3 outer memo digest semantic-role repins changed",
    )

    nested_attack = _static_model_function(tree, "_run_c3_nested_memo_attack")
    ordered_calls = sorted(
        (
            node.lineno,
            node.func.id,
        )
        for node in ast.walk(nested_attack)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id
        in {
            "repin_portability_memo_outer_roles",
            "repin_inner_projection",
            "rebase_checker",
        }
    )
    require(
        tuple(name for _line, name in ordered_calls)
        == (
            "repin_portability_memo_outer_roles",
            "repin_inner_projection",
            "rebase_checker",
        )
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "caller_held_exact_failure_expectation"
            for node in ast.walk(nested_attack)
        )
        == 2,
        "C3 outer/inner/rebase ordering or exact semantic oracle changed",
    )
    sealed_source = ast.unparse(
        _static_model_function(tree, "_sealed_nested_candidate_operation")
    )
    require(
        "_exact_git_status(root)" in sealed_source
        and "backup(root, (PORTABILITY_CORRECTIVE_EVIDENCE, CHECKER_RELATIVE))"
        in sealed_source
        and "require_backup_restored(root, saved)" in sealed_source
        and "run_checker(root, expect_success=True)" in sealed_source
        and "except BaseException as error" in sealed_source
        and "cleanup_failures.append((cleanup_label, error))" in sealed_source
        and "_raise_normalized_sealed_failure" in sealed_source
        and "raise primary" not in sealed_source,
        "C3 sealed restore/status/green replay source model changed",
    )
    normalizer_source = ast.unparse(
        _static_model_function(tree, "_raise_normalized_sealed_failure")
    )
    exception_diagnostic_source = ast.unparse(
        _static_model_function(tree, "_base_exception_diagnostic")
    )
    normalization_probe_source = ast.unparse(
        _static_model_function(tree, "_sealed_base_exception_normalization_probe")
    )
    require(
        "raise SelfTestError(message) from cause" in normalizer_source
        and "primary BaseException(" in normalizer_source
        and "cleanup BaseExceptions=" in normalizer_source
        and "isinstance(error, SystemExit)" in exception_diagnostic_source
        and "code_type=" in exception_diagnostic_source
        and "code=" in exception_diagnostic_source
        and "repr=" in exception_diagnostic_source
        and "normalized.__cause__ is expected_cause" in normalization_probe_source
        and "except BaseException as error" in normalization_probe_source,
        "sealed BaseException normalization source model changed",
    )

    baseline_source = ast.unparse(
        _static_model_function(tree, "baseline_first_rebased_attack")
    )
    baseline_issuer_source = ast.unparse(
        _static_model_function(tree, "_issue_baseline_attack_execution_receipt")
    )
    descriptor_recorder_source = ast.unparse(
        _static_model_function(tree, "_record_descriptor_v4_nested_execution")
    )
    nested_validator_source = ast.unparse(
        _static_model_function(
            tree,
            "_validate_c3_nested_memo_attack_execution_receipt",
        )
    )
    descriptor_validator_source = ast.unparse(
        _static_model_function(tree, "_validated_descriptor_v4_execution_projection")
    )
    require(
        "_BASELINE_LIFECYCLE_AUTHORITY.begin" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.observe_baseline" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.observe_mutation" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.observe_first_rejection" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.observe_rebase" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.observe_semantic_rejection"
        in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.restore_after_attempt" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.observe_green_replay" in baseline_source
        and "_SEALED_BASELINE_ATTACK_EXECUTION_RECEIPT_ISSUER" in baseline_source
        and "_BASELINE_LIFECYCLE_AUTHORITY.issue_completed" in baseline_issuer_source,
        "baseline receipt lifecycle capability source model changed",
    )
    c3_recorder_source = ast.unparse(
        _static_model_function(tree, "_record_c3_nested_memo_execution")
    )
    require(
        "_SEALED_DESCRIPTOR_V4_REAL_ISSUER_CALLABLE" in descriptor_recorder_source
        and "_SEALED_DESCRIPTOR_V4_DRY_ISSUER_CALLABLE" in descriptor_recorder_source
        and "issued_receipt.attack_receipt is validated_attack_receipt"
        in descriptor_recorder_source
        and "require_exact_child_edge" in nested_validator_source
        and "require_exact_child_edge" in descriptor_validator_source
        and "_SEALED_C3_NESTED_REAL_ISSUER_CALLABLE" in c3_recorder_source
        and "_SEALED_C3_NESTED_DRY_ISSUER_CALLABLE" in c3_recorder_source
        and "issued.sealed_receipt is validated_child" in c3_recorder_source
        and c3_recorder_source.count("require_exact_child_edge") == 1,
        "parent/child receipt linkage source model changed",
    )
    receipt_classes = {
        node.name: ast.unparse(node)
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name
        in {
            "_IssuedReceiptRecord",
            "_ReceiptIssuanceRegistry",
            "_ReceiptRunAuthority",
            "_ReceiptAuthorityState",
            "_BaselineLifecycleAuthority",
            "_SealedLifecycleAuthority",
        }
    }
    require(
        set(receipt_classes)
        == {
            "_IssuedReceiptRecord",
            "_ReceiptIssuanceRegistry",
            "_ReceiptRunAuthority",
            "_ReceiptAuthorityState",
            "_BaselineLifecycleAuthority",
            "_SealedLifecycleAuthority",
        }
        and "@dataclass(frozen=True, slots=True, eq=False)"
        in receipt_classes["_IssuedReceiptRecord"]
        and "def validate" in receipt_classes["_ReceiptIssuanceRegistry"]
        and "-> None" in receipt_classes["_ReceiptIssuanceRegistry"]
        and "_RECEIPT_RUN_AUTHORITY.issue_parent"
        in receipt_classes["_ReceiptIssuanceRegistry"]
        and "self.__state = staged" in receipt_classes["_ReceiptRunAuthority"]
        and "_ReceiptFailPoint.BEFORE_COMMIT"
        in receipt_classes["_ReceiptRunAuthority"]
        and "def __record_for" in receipt_classes["_ReceiptRunAuthority"]
        and "receipt_records: tuple[_IssuedReceiptRecord, ...]"
        in receipt_classes["_ReceiptAuthorityState"]
        and "sealed_lifecycle_records: tuple[_SealedLifecycleRecord, ...]"
        in receipt_classes["_ReceiptAuthorityState"]
        and "sealed_permit_receipt_edges: tuple[_SealedPermitReceiptEdge, ...]"
        in receipt_classes["_ReceiptAuthorityState"]
        and "@_serial_authority_method" in receipt_classes["_ReceiptRunAuthority"]
        and "real leaf issue requires a completed lifecycle permit"
        in receipt_classes["_ReceiptRunAuthority"]
        and "reverse capability ownership changed"
        in receipt_classes["_ReceiptRunAuthority"]
        and "aggregate_index" in receipt_classes["_ReceiptRunAuthority"]
        and "require_terminal_success_state" in receipt_classes["_ReceiptRunAuthority"]
        and "pending_baseline" in receipt_classes["_BaselineLifecycleAuthority"]
        and "BASELINE_LIFECYCLE_OBSERVATION_TYPES"
        in receipt_classes["_BaselineLifecycleAuthority"]
        and "consumed_by_baseline_attack_execution_receipt"
        in receipt_classes["_BaselineLifecycleAuthority"]
        and "state='aborted'" in receipt_classes["_BaselineLifecycleAuthority"]
        and "_ReceiptInjectedExceptionKind" in receipt_classes["_BaselineLifecycleAuthority"]
        and "pending_body" in receipt_classes["_SealedLifecycleAuthority"]
        and "observe_body_rejection" in receipt_classes["_SealedLifecycleAuthority"]
        and "observe_restoration" in receipt_classes["_SealedLifecycleAuthority"]
        and "observe_green_replay" in receipt_classes["_SealedLifecycleAuthority"]
        and "consumed_by_sealed_nested_operation_receipt"
        in receipt_classes["_SealedLifecycleAuthority"]
        and "state='aborted'" in receipt_classes["_SealedLifecycleAuthority"],
        "receipt registry immutability/cross-kind custody source model changed",
    )
    sealed_issuer_source = ast.unparse(
        _static_model_function(
            tree,
            "_issue_sealed_nested_candidate_operation_receipt",
        )
    )
    normalized_entry_source = ast.unparse(
        _static_model_function(tree, "_normalized_main_entry")
    )
    require(
        "lifecycle_capability" in sealed_issuer_source
        and "pre_status_sha256" not in sealed_issuer_source
        and "post_status_sha256" not in sealed_issuer_source
        and "_probe_sealed_receipt_atomic_rollback" in sealed_issuer_source
        and "except BaseException as error" in normalized_entry_source
        and "type(result) is not int" in normalized_entry_source,
        "sealed permit issuer or outer entry closure source model changed",
    )
    require(
        "_SEALED_NESTED_CANDIDATE_OPERATION_CALLABLE"
        in ast.unparse(_static_model_function(tree, "_run_c3_nested_memo_attack"))
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_sealed_nested_candidate_operation"
            for node in ast.walk(
                _static_model_function(tree, "hostile_portability_memo_repin_attack")
            )
        )
        == 1,
        "C3 hostile wrappers lost sealed cleanup/callable custody",
    )

    lean_runner = _static_model_function(tree, "run_lean_portability_attacks")
    require(
        type(EXPECTED_RUN_LEAN_PORTABILITY_ATTACKS_PORTABLE_AST_SHA256) is str
        and re.fullmatch(
            r"[0-9a-f]{64}",
            EXPECTED_RUN_LEAN_PORTABILITY_ATTACKS_PORTABLE_AST_SHA256,
        )
        is not None
        and _portable_function_ast_sha256(lean_runner)
        == EXPECTED_RUN_LEAN_PORTABILITY_ATTACKS_PORTABLE_AST_SHA256,
        "Lean portability attack-function portable AST projection changed",
    )
    boundary_substitution_probe = _descriptor_v4_boundary_substitution_ast_mutant(
        lean_runner
    )
    require(
        _portable_function_ast_sha256(boundary_substitution_probe)
        != EXPECTED_RUN_LEAN_PORTABILITY_ATTACKS_PORTABLE_AST_SHA256,
        "descriptor-v4 boundary substitution was not rejected by the portable AST seal",
    )


def _execution_receipt_anti_fraud_projection_sha256(
    projection: object,
) -> str:
    require(
        type(projection) is tuple
        and len(projection) == EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT
        and all(
            type(row) is tuple
            and len(row) == 3
            and all(type(field) is str and field != "" for field in row)
            for row in projection
        ),
        "execution-receipt anti-fraud specification shape changed",
    )
    raw = (
        json.dumps(
            projection,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _static_exact_candidate_source_model(
    tree: ast.Module,
) -> tuple[tuple[str, str, str], ...]:
    """Mirror the checker-side exact-source and frozen-overlay contracts."""

    static_model_receipts = _complete_module_execution_integrity_preflight(tree)
    runtime_hostile_shape_receipts = (
        _execution_receipt_runtime_hostile_shape_preflight()
    )
    anti_fraud_spec = _static_model_literal_assignment(
        tree,
        "EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC",
    )
    anti_fraud_spec_digest = _static_model_literal_assignment(
        tree,
        "EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC_SHA256",
    )
    observed = (*static_model_receipts, *runtime_hostile_shape_receipts)
    control_keys = tuple(row[:2] for row in anti_fraud_spec)
    require(
        anti_fraud_spec == EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC
        and type(anti_fraud_spec) is tuple
        and len(anti_fraud_spec) == EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT
        and tuple(row[0] for row in anti_fraud_spec)
        == (
            ("static_model",) * EXECUTION_RECEIPT_STATIC_MODEL_PROBE_COUNT
            + ("runtime_hostile",) * EXECUTION_RECEIPT_RUNTIME_HOSTILE_SHAPE_COUNT
        )
        and len(set(control_keys)) == EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT
        and type(anti_fraud_spec_digest) is str
        and anti_fraud_spec_digest
        == EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC_SHA256
        and re.fullmatch(r"[0-9a-f]{64}", anti_fraud_spec_digest) is not None
        and _execution_receipt_anti_fraud_projection_sha256(anti_fraud_spec)
        == anti_fraud_spec_digest
        and len(static_model_receipts) == EXECUTION_RECEIPT_STATIC_MODEL_PROBE_COUNT
        and len(runtime_hostile_shape_receipts)
        == EXECUTION_RECEIPT_RUNTIME_HOSTILE_SHAPE_COUNT
        and len(observed) == EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT
        and observed == anti_fraud_spec,
        "execution-receipt anti-fraud control split changed",
    )
    require(
        hashlib.sha256(CANDIDATE_CHECKER_STDIN_BOOTSTRAP.encode("utf-8")).hexdigest()
        == EXPECTED_CANDIDATE_CHECKER_STDIN_BOOTSTRAP_SHA256,
        "candidate-checker stdin bootstrap digest changed",
    )
    bootstrap = _parse_unoptimized_module(
        CANDIDATE_CHECKER_STDIN_BOOTSTRAP,
        filename="<candidate-checker-stdin>",
    )
    require(
        len(bootstrap.body) == 7
        and any(
            isinstance(node, ast.Constant)
            and node.value == "__pid_rs_exact_source_bytes__"
            for node in ast.walk(bootstrap)
        )
        and any(
            isinstance(node, ast.keyword)
            and node.arg == "dont_inherit"
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
            for node in ast.walk(bootstrap)
        )
        and any(
            isinstance(node, ast.keyword)
            and node.arg == "optimize"
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "optimize"
            for node in ast.walk(bootstrap)
        ),
        "candidate-checker stdin bootstrap AST changed",
    )

    invocation = _static_model_function(tree, "invoke_exact_checker")
    run_calls = [
        node
        for node in ast.walk(invocation)
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
    keywords = {keyword.arg: keyword.value for keyword in run_calls[0].keywords}
    require(
        set(keywords) == {"check", "cwd", "env", "input", "stderr", "stdout"}
        and isinstance(keywords["input"], ast.Attribute)
        and isinstance(keywords["input"].value, ast.Name)
        and keywords["input"].value.id == "entry"
        and keywords["input"].attr == "raw"
        and isinstance(keywords["cwd"], ast.Name)
        and keywords["cwd"].id == "root"
        and isinstance(keywords["env"], ast.Name)
        and keywords["env"].id == "environment"
        and isinstance(keywords["check"], ast.Constant)
        and keywords["check"].value is False,
        "candidate-checker exact-source subprocess inputs changed",
    )
    extend_calls = [
        node
        for node in ast.walk(invocation)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "command"
        and node.func.attr == "extend"
    ]
    extension = (
        extend_calls[0].args[0].elts
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
        and isinstance(extension[3], ast.Starred),
        "candidate-checker exact-source command payload changed",
    )
    environment = _static_model_function(
        tree,
        "_exact_checker_child_environment",
    )
    require(
        not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "dict"
            and node.args
            and isinstance(node.args[0], ast.Attribute)
            and isinstance(node.args[0].value, ast.Name)
            and node.args[0].value.id == "os"
            and node.args[0].attr == "environ"
            for node in ast.walk(environment)
        ),
        "candidate-checker exact-source child environment changed",
    )

    stable = _static_model_function(tree, "stable_regular_file")
    require(
        sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "path"
            and node.func.attr == "lstat"
            for node in ast.walk(stable)
        )
        == 3
        and sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "path"
            and node.func.attr == "read_bytes"
            for node in ast.walk(stable)
        )
        == 2,
        "frozen candidate-overlay stable capture model changed",
    )
    clone = _static_model_function(tree, "clone_candidate")
    require(
        not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "shutil"
            and node.func.attr.startswith("copy")
            for node in ast.walk(clone)
        ),
        "frozen candidate-overlay writer reads a live source path",
    )
    require(
        sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "verify_frozen_overlay"
            for node in ast.walk(clone)
        )
        == 1,
        "frozen candidate-overlay post-write verification changed",
    )
    for caller_name in ("run_checker", "current_facts", "generated_block"):
        caller = _static_model_function(tree, caller_name)
        require(
            sum(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "invoke_exact_checker"
                for node in ast.walk(caller)
            )
            == 1
            and not any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "python_command"
                for node in ast.walk(caller)
            ),
            f"candidate-checker exact-source caller integration changed: {caller_name}",
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
            and call.args[3].id in {"overlay", "frozen_overlay"}
            for call in all_clone_calls
        ),
        "candidate lifecycle clone lost the shared frozen overlay object",
    )
    loader_controls = _static_model_function(
        tree,
        "run_exact_candidate_loader_subcontrols",
    )
    static_control_tuples = [
        node.value
        for node in ast.walk(loader_controls)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "static_controls"
        and isinstance(node.value, ast.Tuple)
    ]
    require(
        EXACT_CANDIDATE_LOADER_SUBCONTROL_COUNT == 8
        and len(static_control_tuples) == 1
        and len(static_control_tuples[0].elts) == 6,
        "exact candidate-loader uncounted nested subcontrol inventory changed",
    )
    _static_c3_nested_control_source_model(tree)
    return observed


def static_source_preflight(
    overlay: FrozenOverlay,
) -> tuple[tuple[str, str, str], ...]:
    clone_semantic_projection_preflight()
    execution_receipt_anti_fraud: tuple[tuple[str, str, str], ...] = ()
    for relative in (CHECKER_RELATIVE, SELF_RELATIVE):
        entry = frozen_overlay_entry(overlay, relative)
        try:
            source = entry.raw.decode("utf-8", errors="strict")
            tree = _parse_unoptimized_module(source, filename=relative)
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            raise SelfTestError(
                f"cannot parse source model {relative}: {error}"
            ) from error
        assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        require(
            not assert_nodes,
            f"{relative} contains an optimization-removable assert statement",
        )
        literal_git_argv = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.List, ast.Tuple))
            and node.elts
            and isinstance(node.elts[0], ast.Constant)
            and node.elts[0].value == "git"
        ]
        require(
            not literal_git_argv,
            f"{relative} contains a literal ambient Git argv instead of git_command",
        )
        if relative == SELF_RELATIVE:
            execution_receipt_anti_fraud = _static_exact_candidate_source_model(tree)
            diagnostic_routes: list[str] = []
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "diagnostic_failure_expectation"
                ):
                    continue
                route_values = [
                    keyword.value for keyword in node.keywords if keyword.arg == "route"
                ]
                require(
                    len(route_values) == 1
                    and isinstance(route_values[0], ast.Constant)
                    and isinstance(route_values[0].value, str),
                    "diagnostic failure route must be one literal closed-route name",
                )
                diagnostic_routes.append(route_values[0].value)
            require(
                {
                    route: diagnostic_routes.count(route)
                    for route in set(diagnostic_routes)
                }
                == {
                    "git-cat-file": 3,
                    "deleted-candidate-path": 1,
                    "external-tree-whitespace": 1,
                },
                "diagnostic failure call-site/route inventory changed",
            )
            route_builder = diagnostic_failure_expectation
            try:
                route_builder(
                    route="lean-parser-child",
                    fragment="normal Lean portability parser controls failed",
                    exact_prefix="normal Lean portability parser controls failed: ",
                )
            except SelfTestError as error:
                require(
                    str(error)
                    == (
                        "diagnostic failure expectation is not one of three "
                        "closed routes"
                    ),
                    "retired parser-tail route reached the wrong rejection",
                )
            else:
                require(False, "retired parser-tail diagnostic route survived")
    require(
        len(execution_receipt_anti_fraud) == EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT
        and execution_receipt_anti_fraud
        == EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC,
        "execution-receipt anti-fraud preflight did not complete",
    )
    return execution_receipt_anti_fraud


def semantic_facts_projection(facts: dict[str, object]) -> dict[str, object]:
    """Discard exactly the reviewed source-versus-clone Git context fields."""

    keys = (
        "allowlist_sha256",
        "anchor_delta",
        "anchor_delta_path_count",
        "baseline_path_count",
        "bound_allowed_blobs",
        "changed_paths",
        "changed_projection_sha256",
        "current_anchor",
        "current_anchor_tree",
        "current_head",
        "diagnostic_only",
        "git_tcb",
        "lifecycle",
        "phase_path_policy",
        "phase_path_policy_sha256",
        "precommit_tracked_modifications",
        "precommit_untracked_deliverables",
        "protected_path_count",
        "protected_projection_sha256",
        "schema",
        "schema_revision",
        "self_unhashed_paths",
    )
    require(
        all(key in facts for key in keys),
        "diagnostic phase facts lost a semantic custody field",
    )
    git_context = facts.get("git_context")
    require(
        isinstance(git_context, dict) and set(git_context) == EXPECTED_GIT_CONTEXT_KEYS,
        "diagnostic phase facts Git context has an unexpected exact shape",
    )
    require(
        CLONE_VARIANT_GIT_CONTEXT_KEYS.isdisjoint(CLONE_INVARIANT_GIT_CONTEXT_KEYS)
        and CLONE_VARIANT_GIT_CONTEXT_KEYS | CLONE_INVARIANT_GIT_CONTEXT_KEYS
        == EXPECTED_GIT_CONTEXT_KEYS,
        "clone-variant and clone-invariant Git context fields do not partition",
    )
    normalized_context = {
        key: git_context[key] for key in sorted(CLONE_INVARIANT_GIT_CONTEXT_KEYS)
    }
    require(
        set(normalized_context) == CLONE_INVARIANT_GIT_CONTEXT_KEYS,
        "clone semantic projection lost an invariant Git context field",
    )
    return {
        **{key: facts[key] for key in keys},
        "git_context": normalized_context,
    }


def clone_semantic_projection_preflight() -> None:
    """Exercise exact under-/over-projection without entering hostile counts."""

    fact_keys = (
        "allowlist_sha256",
        "anchor_delta",
        "anchor_delta_path_count",
        "baseline_path_count",
        "bound_allowed_blobs",
        "changed_paths",
        "changed_projection_sha256",
        "current_anchor",
        "current_anchor_tree",
        "current_head",
        "diagnostic_only",
        "git_tcb",
        "lifecycle",
        "phase_path_policy",
        "phase_path_policy_sha256",
        "precommit_tracked_modifications",
        "precommit_untracked_deliverables",
        "protected_path_count",
        "protected_projection_sha256",
        "schema",
        "schema_revision",
        "self_unhashed_paths",
    )
    shared = {key: f"fixture:{key}" for key in fact_keys}
    source_context: dict[str, object] = {
        "common_git_dir": "/source/common",
        "git_dir": "/source/git",
        "info_attributes_absent": True,
        "local_config_semantics_sha256": "a" * 64,
        "local_config_sha256": "b" * 64,
        "replacement_refs_sha256": "c" * 64,
        "worktree_config_absent": True,
    }
    clone_context: dict[str, object] = {
        **source_context,
        "common_git_dir": "/clone/common",
        "git_dir": "/clone/git",
        "local_config_semantics_sha256": "d" * 64,
        "local_config_sha256": "e" * 64,
    }
    source_facts = {**shared, "git_context": source_context}
    clone_facts = {**shared, "git_context": clone_context}
    source_projection = semantic_facts_projection(source_facts)
    clone_projection = semantic_facts_projection(clone_facts)
    require(
        source_projection == clone_projection,
        "clone semantic projection retained a clone-variant Git context field",
    )

    for key in sorted(CLONE_INVARIANT_GIT_CONTEXT_KEYS):
        mutated_context = dict(clone_context)
        original = mutated_context[key]
        mutated_context[key] = not original if type(original) is bool else "f" * 64
        require(
            semantic_facts_projection({**shared, "git_context": mutated_context})
            != source_projection,
            f"clone semantic projection discarded invariant Git context field: {key}",
        )

    for label, malformed_context in (
        (
            "missing",
            {key: value for key, value in clone_context.items() if key != "git_dir"},
        ),
        ("extra", {**clone_context, "unexpected_context_field": True}),
    ):
        try:
            semantic_facts_projection({**shared, "git_context": malformed_context})
        except SelfTestError as error:
            require(
                str(error)
                == "diagnostic phase facts Git context has an unexpected exact shape",
                f"clone semantic projection {label}-key control reached the wrong route",
            )
        else:
            require(
                False,
                f"clone semantic projection accepted a {label} Git context key",
            )


def clone_candidate(
    source: Path,
    destination: Path,
    facts: dict[str, object],
    overlay: FrozenOverlay,
) -> None:
    process = run(
        git_command(
            "clone",
            "--no-local",
            "--quiet",
            "--no-checkout",
            str(source),
            str(destination),
        ),
        cwd=source,
    )
    require(
        process.returncode == 0,
        "cannot create isolated self-test clone:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    checkout = run(
        git_command("checkout", "--quiet", "--detach", CURRENT_ANCHOR),
        cwd=destination,
    )
    require(
        checkout.returncode == 0,
        "cannot check out exact self-test anchor:\n"
        + checkout.stderr.decode("utf-8", errors="replace"),
    )
    require(
        len(overlay.entries) == EXPECTED_CHANGED_PATH_COUNT
        and tuple(entry.relative for entry in overlay.entries)
        == tuple(facts.get("changed_paths", ())),
        "frozen candidate overlay differs from the diagnostic path inventory",
    )
    for entry in overlay.entries:
        destination_path = destination / entry.relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(entry.raw)
        destination_path.chmod(entry.mode)
    verify_frozen_overlay(destination, overlay)

    clone_facts, clone_source_entry = current_facts(destination)
    require(
        clone_source_entry == frozen_overlay_entry(overlay, CHECKER_RELATIVE),
        "clone checker source differs from the frozen overlay entry",
    )
    require(
        semantic_facts_projection(clone_facts) == semantic_facts_projection(facts),
        "clone semantic facts differ from the frozen source facts",
    )


def anchor_delta_paths(facts: dict[str, object]) -> tuple[str, ...]:
    raw_delta = facts.get("anchor_delta")
    require(isinstance(raw_delta, list) and raw_delta, "anchor delta facts are invalid")
    result: list[str] = []
    for item in raw_delta:
        require(
            isinstance(item, dict)
            and set(item) == {"path", "status"}
            and isinstance(item.get("path"), str)
            and item.get("status") in {"A", "M"},
            "anchor delta fact has an invalid shape",
        )
        result.append(item["path"])
    require(
        tuple(result) == tuple(sorted(result)) and len(result) == len(set(result)),
        "anchor delta facts are not sorted and duplicate-free",
    )
    return tuple(result)


def write_candidate_tree(root: Path, facts: dict[str, object]) -> str:
    with tempfile.TemporaryDirectory(prefix="pid-rs-phase-index.") as temporary_raw:
        index_path = Path(temporary_raw) / "index"
        environment = {"GIT_INDEX_FILE": str(index_path)}
        read_tree = run(
            git_command("read-tree", CURRENT_ANCHOR),
            cwd=root,
            environment_overrides=environment,
        )
        require(read_tree.returncode == 0, "cannot seed external candidate index")
        paths = anchor_delta_paths(facts)
        stage = run(
            git_command("add", "--", *paths),
            cwd=root,
            environment_overrides=environment,
        )
        require(
            stage.returncode == 0,
            "cannot stage exact policy paths in external candidate index:\n"
            + stage.stderr.decode("utf-8", errors="replace"),
        )
        write_tree = run(
            git_command("write-tree"),
            cwd=root,
            environment_overrides=environment,
        )
        require(write_tree.returncode == 0, "cannot write external candidate tree")
        tree = write_tree.stdout.decode("ascii", errors="strict").strip()
        require(len(tree) == 40, "external candidate tree id has the wrong shape")
        return tree


def write_checkpoint_commit(root: Path, tree: str, parent: str) -> str:
    process = run(
        git_command("commit-tree", tree, "-p", parent),
        cwd=root,
        input_bytes=EXPECTED_C3_COMMIT_MESSAGE.encode("utf-8"),
        environment_overrides={
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_AUTHOR_EMAIL": EXPECTED_C3_COMMIT_EMAIL,
            "GIT_AUTHOR_NAME": EXPECTED_C3_COMMIT_DISPLAY_NAME,
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_COMMITTER_EMAIL": EXPECTED_C3_COMMIT_EMAIL,
            "GIT_COMMITTER_NAME": EXPECTED_C3_COMMIT_DISPLAY_NAME,
        },
    )
    require(
        process.returncode == 0,
        "cannot create detached self-test checkpoint:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    commit = process.stdout.decode("ascii", errors="strict").strip()
    require(len(commit) == 40, "checkpoint commit id has the wrong shape")
    return commit


def commit_exact_paths(
    root: Path,
    paths: Iterable[str],
    *,
    message: str,
    author_name: str = EXPECTED_C3_COMMIT_DISPLAY_NAME,
    author_email: str = EXPECTED_C3_COMMIT_EMAIL,
    committer_name: str = EXPECTED_C3_COMMIT_DISPLAY_NAME,
    committer_email: str = EXPECTED_C3_COMMIT_EMAIL,
) -> str:
    ordered = tuple(paths)
    require(
        ordered and len(ordered) == len(set(ordered)),
        "commit path inventory must be nonempty and duplicate-free",
    )
    stage = run(git_command("add", "--", *ordered), cwd=root)
    require(
        stage.returncode == 0,
        "cannot stage exact lifecycle paths:\n"
        + stage.stderr.decode("utf-8", errors="replace"),
    )
    staged = run(
        git_command("diff", "--cached", "--name-only", "-z"),
        cwd=root,
    )
    require(staged.returncode == 0, "cannot inspect staged lifecycle paths")
    observed = tuple(
        item.decode("utf-8", errors="strict")
        for item in staged.stdout.split(b"\0")
        if item
    )
    require(
        set(observed) == set(ordered),
        "staged lifecycle path inventory differs from the exact request",
    )
    commit = run(
        git_command(
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--no-gpg-sign",
            "--no-verify",
            "--quiet",
            "-m",
            message,
        ),
        cwd=root,
        environment_overrides={
            "GIT_AUTHOR_DATE": "2000-01-02T00:00:00+00:00",
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_NAME": author_name,
            "GIT_COMMITTER_DATE": "2000-01-02T00:00:00+00:00",
            "GIT_COMMITTER_EMAIL": committer_email,
            "GIT_COMMITTER_NAME": committer_name,
        },
    )
    require(
        commit.returncode == 0,
        "cannot commit exact lifecycle paths:\n"
        + commit.stderr.decode("utf-8", errors="replace"),
    )
    head = run(git_command("rev-parse", "HEAD"), cwd=root)
    require(head.returncode == 0, "cannot resolve lifecycle commit")
    return head.stdout.decode("ascii", errors="strict").strip()


def commit_empty(root: Path, *, message: str) -> str:
    commit = run(
        git_command(
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "--no-gpg-sign",
            "--no-verify",
            "--quiet",
            "-m",
            message,
        ),
        cwd=root,
        environment_overrides={
            "GIT_AUTHOR_DATE": "2000-01-03T00:00:00+00:00",
            "GIT_AUTHOR_EMAIL": "phase-self-test@example.invalid",
            "GIT_AUTHOR_NAME": "Phase Self Test",
            "GIT_COMMITTER_DATE": "2000-01-03T00:00:00+00:00",
            "GIT_COMMITTER_EMAIL": "phase-self-test@example.invalid",
            "GIT_COMMITTER_NAME": "Phase Self Test",
        },
    )
    require(
        commit.returncode == 0,
        "cannot create empty lifecycle commit:\n"
        + commit.stderr.decode("utf-8", errors="replace"),
    )
    head = run(git_command("rev-parse", "HEAD"), cwd=root)
    require(head.returncode == 0, "cannot resolve empty lifecycle commit")
    return head.stdout.decode("ascii", errors="strict").strip()


def commit_raw_candidate(
    root: Path,
    facts: dict[str, object],
    *,
    author_header: str = ("Sepehr Mahmoudian <sepmhn@gmail.com> 946684800 +0000"),
    committer_header: str = ("Sepehr Mahmoudian <sepmhn@gmail.com> 946684800 +0000"),
    additional_header_lines: tuple[str, ...] = (),
    message_raw: bytes = EXPECTED_C3_COMMIT_MESSAGE.encode("utf-8"),
) -> str:
    require(
        "\n" not in author_header
        and "\r" not in author_header
        and "\n" not in committer_header
        and "\r" not in committer_header,
        "raw candidate identity header contains a line break",
    )
    paths = anchor_delta_paths(facts)
    stage = run(git_command("add", "--", *paths), cwd=root)
    require(stage.returncode == 0, "cannot stage raw candidate paths")
    tree_process = run(git_command("write-tree"), cwd=root)
    require(tree_process.returncode == 0, "cannot write raw candidate tree")
    tree = tree_process.stdout.decode("ascii", errors="strict").strip()
    header = (
        f"tree {tree}\n"
        f"parent {CURRENT_ANCHOR}\n"
        f"author {author_header}\n"
        f"committer {committer_header}\n"
        + "".join(line + "\n" for line in additional_header_lines)
        + "\n"
    ).encode("utf-8")
    raw_commit = header + message_raw
    write_object = run(
        git_command(
            "hash-object",
            "--literally",
            "-t",
            "commit",
            "-w",
            "--stdin",
        ),
        cwd=root,
        input_bytes=raw_commit,
    )
    require(
        write_object.returncode == 0,
        "cannot write raw candidate commit object",
    )
    commit = write_object.stdout.decode("ascii", errors="strict").strip()
    update_ref = run(
        git_command("update-ref", "HEAD", commit, CURRENT_ANCHOR),
        cwd=root,
    )
    require(update_ref.returncode == 0, "cannot install raw candidate HEAD")
    read_tree = run(git_command("read-tree", commit), cwd=root)
    require(read_tree.returncode == 0, "cannot align raw candidate index")
    return commit


def commit_raw_signed_candidate(
    root: Path,
    facts: dict[str, object],
    *,
    signature_header: str,
) -> str:
    require(
        signature_header in {"gpgsig", "gpgsig-sha256", "gpgsig-v2"},
        "raw signed fixture header is not reviewed",
    )
    return commit_raw_candidate(
        root,
        facts,
        additional_header_lines=(
            f"{signature_header} -----BEGIN TEST SIGNATURE-----",
            " fake-signature-body",
            " -----END TEST SIGNATURE-----",
        ),
    )


def _exact_git_status(root: Path) -> bytes:
    process = run(
        git_command(
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
        ),
        cwd=root,
    )
    require(
        process.returncode == 0 and process.stderr == b"",
        "cannot capture exact candidate status for nested loader control",
    )
    return process.stdout


def _static_exact_loader_subcontrol(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], None],
    expected_detail: str,
) -> None:
    before_status = _exact_git_status(root)
    saved = backup(root, (SELF_RELATIVE,))
    try:
        mutate(root / SELF_RELATIVE)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=expected_detail,
            failure_expectation=caller_held_exact_failure_expectation(expected_detail),
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    require_backup_restored(root, saved)
    require(
        _exact_git_status(root) == before_status,
        f"{label}: source mutation did not restore exact Git status bytes",
    )
    run_checker(root, expect_success=True)


def run_exact_candidate_loader_subcontrols(
    root: Path,
    overlay: FrozenOverlay,
) -> int:
    """Exercise eight correlated, explicitly uncounted loader/overlay controls."""

    subcontrols = 0
    static_controls = (
        (
            "candidate-checker-empty-captured-input",
            b"                input=entry.raw,\n",
            b'                input=b"",\n',
            "candidate-checker exact-source subprocess inputs changed",
        ),
        (
            "candidate-checker-live-path-command",
            (
                b'            "-c",\n'
                b"            CANDIDATE_CHECKER_STDIN_BOOTSTRAP,\n"
                b"            logical_file,\n"
                b"            *arguments,\n"
            ),
            (b"            logical_file,\n            *arguments,\n"),
            "candidate-checker exact-source command payload changed",
        ),
        (
            "candidate-checker-bootstrap-inheritance",
            b'    "    dont_inherit=True,\\n"\n',
            b'    "    dont_inherit=False,\\n"\n',
            "candidate-checker stdin bootstrap digest changed",
        ),
        (
            "candidate-overlay-live-copy2",
            b"        destination_path.write_bytes(entry.raw)\n",
            (
                b"        shutil.copy2(\n"
                b"            source / entry.relative,\n"
                b"            destination_path,\n"
                b"        )\n"
            ),
            "frozen candidate-overlay writer reads a live source path",
        ),
        (
            "candidate-overlay-post-write-verifier-removal",
            b"    verify_frozen_overlay(destination, overlay)\n",
            b"",
            "frozen candidate-overlay post-write verification changed",
        ),
        (
            "candidate-checker-ambient-child-environment",
            (b"        environment = _exact_checker_child_environment(private_root)\n"),
            b"        environment = dict(os.environ)\n",
            "candidate-checker exact-source child environment changed",
        ),
    )
    for label, before, after, expected_detail in static_controls:
        _static_exact_loader_subcontrol(
            root,
            label=label,
            mutate=lambda path, before=before, after=after: replace_once(
                path,
                before,
                after,
            ),
            expected_detail=expected_detail,
        )
        subcontrols += 1

    before_status = _exact_git_status(root)
    saved_checker = backup(root, (CHECKER_RELATIVE,))
    marker = root / ".candidate-checker-sentinel-executed"
    require(
        not marker.exists() and not marker.is_symlink(),
        "candidate-checker sentinel marker already exists",
    )
    captured_checker = stable_regular_file(root, CHECKER_RELATIVE)
    sentinel = (
        b"from pathlib import Path\n"
        + f"Path({os.fspath(marker)!r}).write_bytes(b'executed')\n".encode("utf-8")
    )
    checker_path = root / CHECKER_RELATIVE
    try:
        checker_path.write_bytes(sentinel)
        checker_path.chmod(captured_checker.mode)
        invocation = invoke_exact_checker(
            root,
            "--diagnostic-without-external-custody",
            force_optimized=False,
            source_entry=captured_checker,
            after_child=lambda: restore(root, saved_checker),
        )
        detail = "logical phase-checker path bytes differ from captured stdin source"
        validate_checker_failure_receipt(
            invocation.process,
            expectation=caller_held_exact_failure_expectation(detail),
        )
        require(
            not marker.exists() and not marker.is_symlink(),
            "live-path sentinel executed instead of captured checker bytes",
        )
    except SelfTestError as error:
        raise SelfTestError(f"candidate-checker-logical-path-swap: {error}") from error
    finally:
        restore(root, saved_checker)
        if marker.is_symlink() or marker.exists():
            marker.unlink()
    require_backup_restored(root, saved_checker)
    require(
        _exact_git_status(root) == before_status,
        "candidate-checker-logical-path-swap: Git status was not restored",
    )
    run_checker(root, expect_success=True)
    subcontrols += 1

    executable_entry = frozen_overlay_entry(
        overlay,
        FROZEN_MODE_SUBCONTROL_RELATIVE,
    )
    require(
        executable_entry.mode == 0o755,
        "frozen overlay lacks the reviewed executable-mode subcontrol path",
    )
    mode_path = root / executable_entry.relative
    before_status = _exact_git_status(root)
    saved_mode = backup(root, (executable_entry.relative,))
    expected_mode_detail = (
        f"frozen candidate overlay mode mismatch: {executable_entry.relative}"
    )
    try:
        mode_path.chmod(0o644)
        try:
            verify_frozen_overlay(root, overlay)
        except SelfTestError as error:
            require(
                str(error) == expected_mode_detail,
                "frozen-overlay mode control reached the wrong local route",
            )
        else:
            require(False, "frozen-overlay mode mismatch survived local verification")
    finally:
        restore(root, saved_mode)
    require_backup_restored(root, saved_mode)
    require(
        _exact_git_status(root) == before_status,
        "frozen-overlay mode control did not restore exact Git status bytes",
    )
    verify_frozen_overlay(root, overlay)
    run_checker(root, expect_success=True)
    subcontrols += 1

    require(
        subcontrols == EXACT_CANDIDATE_LOADER_SUBCONTROL_COUNT,
        "exact candidate-loader uncounted nested subcontrol inventory changed",
    )
    return subcontrols


def run_checker_model_attacks(root: Path, overlay: FrozenOverlay) -> int:
    attacks = 0
    checker = root / CHECKER_RELATIVE
    declared_tree_commits = {
        "formal-anchor-tree-pin": "118e1de6a2d6d2ae33fe7bdc224736257e42a83f",
        "recovery-anchor-tree-pin": "ca24ab8ebade81a94ffc001531abaf5a5579d5e9",
        "integration-anchor-tree-pin": "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c",
        "m1a-scientific-tree-pin": "dc7b8de0a87443ef2bcde71b19938642f1af2197",
        "corrective-parent-tree-pin": "af50935be9ecf9a81aeb30c56b45059652468746",
        "c2-tooling-correction-tree-pin": CURRENT_ANCHOR,
    }

    mutations = (
        (
            "scientific-baseline-commit-pin",
            b'e96122b56c15e895c081379210103d1a26eac25f"',
            b'e96122b56c15e895c081379210103d1a26eac250"',
            "git cat-file",
        ),
        (
            "scientific-baseline-tree-pin",
            b'fee2346732da20af0cde32844fcab527ec2d6c4a"',
            b'fee2346732da20af0cde32844fcab527ec2d6c40"',
            "scientific baseline tree pin mismatch",
        ),
        (
            "delivery-commit-pin",
            b'9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"',
            b'e96122b56c15e895c081379210103d1a26eac25f"',
            "delivery parent tree pin mismatch",
        ),
        (
            "delivery-tree-pin",
            b'13b15a7564fdd52df16e2e4380f6293db4ea4367"',
            b'13b15a7564fdd52df16e2e4380f6293db4ea4360"',
            "delivery parent tree pin mismatch",
        ),
        (
            "formal-anchor-commit-pin",
            b'118e1de6a2d6d2ae33fe7bdc224736257e42a83f"',
            b'118e1de6a2d6d2ae33fe7bdc224736257e42a830"',
            "git cat-file",
        ),
        (
            "formal-anchor-tree-pin",
            b'd02ffc69a7045984c1cf58f3adbd39b7e3af0e89"',
            b'd02ffc69a7045984c1cf58f3adbd39b7e3af0e80"',
            "declared tree pin mismatch",
        ),
        (
            "recovery-anchor-commit-pin",
            b'ca24ab8ebade81a94ffc001531abaf5a5579d5e9"',
            b'ca24ab8ebade81a94ffc001531abaf5a5579d5e0"',
            "git cat-file",
        ),
        (
            "recovery-anchor-tree-pin",
            b'82b0aec08c5fd71b6f67d653f05a32f097745a03"',
            b'82b0aec08c5fd71b6f67d653f05a32f097745a00"',
            "declared tree pin mismatch",
        ),
        (
            "integration-anchor-commit-pin",
            b'a9aa60c962261a6e0e6698b05551fbcdbf7bf41c"',
            b'a9aa60c962261a6e0e6698b05551fbcdbf7bf410"',
            "git cat-file",
        ),
        (
            "integration-anchor-tree-pin",
            b'88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e6f"',
            b'88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e60"',
            "declared tree pin mismatch",
        ),
        (
            "m1a-scientific-commit-pin",
            b'dc7b8de0a87443ef2bcde71b19938642f1af2197"',
            b'dc7b8de0a87443ef2bcde71b19938642f1af2190"',
            "git cat-file",
        ),
        (
            "m1a-scientific-tree-pin",
            b'88b24c0ba4fcad4bd749b9146486143397b6a6eb"',
            b'88b24c0ba4fcad4bd749b9146486143397b6a6e0"',
            "declared tree pin mismatch",
        ),
        (
            "root-gitignore-protected-blob-pin",
            b"918f4cf153cfa4a0f6e5b4d07bd647e417c06e383e4b580946acbede783873d1",
            b"018f4cf153cfa4a0f6e5b4d07bd647e417c06e383e4b580946acbede783873d1",
            "pinned protected baseline fact mismatch: .gitignore",
        ),
    )
    for label, old, new, fragment in mutations:
        expected_detail = (
            f"{declared_tree_commits[label]}: declared tree pin mismatch"
            if fragment == "declared tree pin mismatch"
            else fragment
        )
        failure_expectation = None
        if fragment == "git cat-file":
            bad_commit_matches = re.findall(rb"[0-9a-f]{40}", new)
            require(
                len(bad_commit_matches) == 1,
                "bad commit-pin mutation lost its unique exact SHA",
            )
            bad_commit = bad_commit_matches[0].decode("ascii")
            failure_expectation = diagnostic_failure_expectation(
                route="git-cat-file",
                fragment=fragment,
                exact_prefix=f"git cat-file -p {bad_commit} failed with 128: ",
            )
        elif fragment in {
            "declared tree pin mismatch",
            "pinned protected baseline fact mismatch: .gitignore",
        }:
            failure_expectation = caller_held_exact_failure_expectation(expected_detail)
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, old=old, new=new: replace_once(checker, old, new),
            expected_fragment=expected_detail,
            failure_expectation=failure_expectation,
        )
        attacks += 1

    assignment_mutations = (
        (
            "post-anchor-direct-child-bound",
            b"MAX_POST_ANCHOR_COMMITS = 1\n",
            b"MAX_POST_ANCHOR_COMMITS = 3\n",
            "post-anchor commit bound is not exactly one direct child",
        ),
        (
            "corrective-parent-commit-pin",
            (b'CORRECTIVE_PARENT = "af50935be9ecf9a81aeb30c56b45059652468746"\n'),
            (b'CORRECTIVE_PARENT = "0f50935be9ecf9a81aeb30c56b45059652468746"\n'),
            "git cat-file",
        ),
        (
            "corrective-parent-tree-pin",
            (b'CORRECTIVE_PARENT_TREE = "ada3860eb696c9a5d634728365acdb5958e7c4e6"\n'),
            (b'CORRECTIVE_PARENT_TREE = "0da3860eb696c9a5d634728365acdb5958e7c4e6"\n'),
            "declared tree pin mismatch",
        ),
        (
            "c2-tooling-correction-commit-pin",
            (b'C2_TOOLING_CORRECTION = "8b792bc143fff2d84f2d8e7817d1de7850741223"\n'),
            (b'C2_TOOLING_CORRECTION = "0b792bc143fff2d84f2d8e7817d1de7850741223"\n'),
            "git cat-file",
        ),
        (
            "c2-tooling-correction-tree-pin",
            (
                b"C2_TOOLING_CORRECTION_TREE = "
                b'"8e247b9a6c46fd6266fe4fc02fbe9c3142268215"\n'
            ),
            (
                b"C2_TOOLING_CORRECTION_TREE = "
                b'"0e247b9a6c46fd6266fe4fc02fbe9c3142268215"\n'
            ),
            "declared tree pin mismatch",
        ),
        (
            "current-anchor-commit-pin",
            b"CURRENT_ANCHOR = C2_TOOLING_CORRECTION\n",
            b"CURRENT_ANCHOR = CORRECTIVE_PARENT\n",
            "current phase anchor is not the exact pushed C2 tooling correction",
        ),
        (
            "current-anchor-tree-pin",
            b"CURRENT_ANCHOR_TREE = C2_TOOLING_CORRECTION_TREE\n",
            b"CURRENT_ANCHOR_TREE = CORRECTIVE_PARENT_TREE\n",
            "current phase anchor is not the exact pushed C2 tooling correction",
        ),
    )
    for label, old, new, fragment in assignment_mutations:
        expected_detail = (
            f"{declared_tree_commits[label]}: declared tree pin mismatch"
            if fragment == "declared tree pin mismatch"
            else fragment
        )
        bad_commit_match = re.search(rb'"([0-9a-f]{40})"', new)
        failure_expectation = None
        if fragment == "git cat-file":
            require(
                bad_commit_match is not None,
                "bad commit-pin mutation lost its exact SHA",
            )
            bad_commit = bad_commit_match.group(1).decode("ascii")
            failure_expectation = diagnostic_failure_expectation(
                route="git-cat-file",
                fragment=fragment,
                exact_prefix=f"git cat-file -p {bad_commit} failed with 128: ",
            )
        elif fragment == "declared tree pin mismatch":
            failure_expectation = caller_held_exact_failure_expectation(expected_detail)
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, old=old, new=new: replace_once(checker, old, new),
            expected_fragment=expected_detail,
            failure_expectation=failure_expectation,
        )
        attacks += 1

    simple_attack(
        root,
        label="optimized-assert-source",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b") -> tuple[str, int, int, int, int, str | None, GitBinaryIdentity]:\n",
            (
                b") -> tuple[str, int, int, int, int, str | None, GitBinaryIdentity]:\n"
                b"    assert True\n"
            ),
        ),
        expected_fragment="optimization-removable assert",
        force_optimized=True,
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-parallel-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_parallel_semantics()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-ci-corrective-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_ci_corrective_firewall()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    for label, call in (
        (
            "critical-prior-c2-history-gate-removal",
            b"    validate_prior_c2_history()\n",
        ),
        (
            "critical-public-ci-failure-evidence-gate-removal",
            b"    validate_public_ci_failure_evidence()\n",
        ),
        (
            "critical-public-ci-portability-evidence-gate-removal",
            (
                b"    portability_memo_raw = "
                b"validate_public_ci_portability_failure_evidence()\n"
            ),
        ),
        (
            "critical-claim-rebind-gate-removal",
            b"    validate_claim_checker_workflow_rebind()\n",
        ),
        (
            "critical-python-entry-isolation-gate-removal",
            b"    validate_python_entry_isolation()\n",
        ),
        (
            "critical-foundational-lake-gate-removal",
            b"    validate_foundational_pdf_lake_preflight()\n",
        ),
        (
            "critical-lean-portability-gate-removal",
            b"    lean_artifacts = validate_lean_evidence_portability()\n",
        ),
        (
            "critical-c3-local-artifact-parity-gate-removal",
            (
                b"    validate_c3_local_artifact_parity("
                b"portability_memo_raw, lean_artifacts)\n"
            ),
        ),
        (
            "critical-c3-science-isolation-gate-removal",
            b"    validate_c3_science_and_publication_isolation(snapshot, anchor)\n",
        ),
    ):
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, call=call: replace_once(checker, call, b""),
            expected_fragment="direct top-level critical gate sequence changed",
        )
        attacks += 1

    for label, call in (
        (
            "post-anchor-commit-metadata-gate-removal",
            (
                b"        validate_unsigned_attribution_free_commit(\n"
                b"            commit,\n"
                b'            label=f"post-anchor commit {commit}",\n'
                b"            require_exact_c3_identity_and_message=True,\n"
                b"        )\n"
            ),
        ),
        (
            "checkpoint-commit-metadata-gate-removal",
            (
                b"        validate_unsigned_attribution_free_commit(\n"
                b"            checkpoint_commit,\n"
                b'            label=f"checkpoint commit {checkpoint_commit}",\n'
                b"            require_exact_c3_identity_and_message=True,\n"
                b"        )\n"
            ),
        ),
    ):
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, call=call: replace_once(checker, call, b""),
            expected_fragment=(
                "unsigned/attribution-free commit metadata gate inventory changed"
            ),
        )
        attacks += 1

    simple_attack(
        root,
        label="external-tree-whitespace-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            (
                b"    whitespace_check = git_process(\n"
                b'        "-c",\n'
                b'        "advice.graftFileDeprecated=false",\n'
                b'        "-c",\n'
                b'        "core.whitespace=blank-at-eol,blank-at-eof,'
                b'space-before-tab",\n'
                b'        "diff-tree",\n'
            ),
            (
                b"    whitespace_check = git_process(\n"
                b'        "-c",\n'
                b'        "advice.graftFileDeprecated=false",\n'
                b'        "-c",\n'
                b'        "core.whitespace=blank-at-eol,blank-at-eof,'
                b'space-before-tab",\n'
                b'        "diff-index",\n'
            ),
        ),
        expected_fragment="external candidate-tree whitespace gate inventory changed",
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-package-corrective-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_package_archive_corrective_firewall()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-ecosystem-corrective-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_ecosystem_corrective_firewall()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    direct_gate_mutations = (
        (
            "critical-gate-dead-branch",
            b"    validate_parallel_semantics()\n",
            b"    if False:\n        validate_parallel_semantics()\n",
        ),
        (
            "critical-gate-nested-helper",
            b"    validate_parallel_semantics()\n",
            (
                b"    def hidden_parallel_gate() -> None:\n"
                b"        validate_parallel_semantics()\n"
                b"    hidden_parallel_gate()\n"
            ),
        ),
        (
            "critical-gate-try-swallow",
            b"    validate_parallel_semantics()\n",
            (
                b"    try:\n"
                b"        validate_parallel_semantics()\n"
                b"    except PhaseIsolationError:\n"
                b"        pass\n"
            ),
        ),
        (
            "critical-gate-reorder",
            (b"    validate_stats_firewall()\n    validate_parallel_semantics()\n"),
            (b"    validate_parallel_semantics()\n    validate_stats_firewall()\n"),
        ),
        (
            "repository-context-replay-removal",
            b"    replay_context = validate_repository_context()\n",
            b"    replay_context = repository_context\n",
        ),
    )
    for label, old, new in direct_gate_mutations:
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, old=old, new=new: replace_once(checker, old, new),
            expected_fragment="direct top-level critical gate sequence changed",
        )
        attacks += 1

    parser_model_mutations = (
        (
            "lean-portability-optimized-replay-disabled",
            b"optimized_raw = run_lean_portability_parser(optimized=True)",
            b"optimized_raw = run_lean_portability_parser(optimized=False)",
            b"def validate_lean_evidence_portability() -> LeanPortabilityArtifacts:\n",
            b"def validate_c3_science_and_publication_isolation(\n",
            (
                "Lean portability parser replay source model changed: "
                "optimized_raw = run_lean_portability_parser(optimized=True)"
            ),
        ),
        (
            "lean-portability-optimized-flag-removed",
            b'        command.append("-O")\n',
            b"        pass\n",
            b"def run_lean_portability_parser(*, optimized: bool) -> bytes:\n",
            b"def validate_lean_evidence_portability() -> LeanPortabilityArtifacts:\n",
            (
                "Lean portability parser replay source model changed: "
                'command.append("-O")'
            ),
        ),
    )
    for (
        label,
        old,
        new,
        start_marker,
        end_marker,
        expected_detail,
    ) in parser_model_mutations:
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, old=old, new=new, start_marker=start_marker, end_marker=end_marker: (
                replace_once_between(
                    checker,
                    start_marker,
                    end_marker,
                    old,
                    new,
                )
            ),
            expected_fragment=expected_detail,
            failure_expectation=caller_held_exact_failure_expectation(expected_detail),
        )
        attacks += 1
    exact_candidate_loader_subcontrols = run_exact_candidate_loader_subcontrols(
        root,
        overlay,
    )
    require(
        exact_candidate_loader_subcontrols == 8,
        "checker-model exact loader subcontrol count changed",
    )
    return attacks


def run_python_entry_isolation_attacks(root: Path) -> int:
    """Attack each real bootstrap plus child and official invocation custody."""

    attacks = 0
    preamble_attacks = (
        (
            "phase-checker-isolated-flag-bypass",
            CHECKER_RELATIVE,
            b"_bootstrap_sys.flags.isolated == 1",
            b"True",
        ),
        (
            "phase-selftest-safe-path-bypass",
            SELF_RELATIVE,
            b"_bootstrap_sys.flags.safe_path",
            b"True",
        ),
        (
            "descriptor-checker-no-site-bypass",
            "scripts/check-lean-descriptor-factorization.py",
            b"_bootstrap_sys.flags.no_site == 1",
            b"True",
        ),
        (
            "descriptor-selftest-environment-bypass",
            "scripts/check-lean-descriptor-factorization-self-test.py",
            b"_bootstrap_sys.flags.ignore_environment == 1",
            b"True",
        ),
    )
    for label, relative, before, after in preamble_attacks:
        semantic_detail = f"Python isolation preamble changed: {relative}"
        self_unhashed = relative in {CHECKER_RELATIVE, SELF_RELATIVE}
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(relative,),
            mutate=lambda candidate, relative=relative, before=before, after=after: (
                replace_once_between(
                    candidate / relative,
                    b"import sys as _bootstrap_sys\n\nif not (\n",
                    b"del _bootstrap_sys\n\n",
                    before,
                    after,
                )
            ),
            first_fragment=(
                semantic_detail
                if self_unhashed
                else "changed-byte projection digest mismatch"
            ),
            first_expectation=(
                caller_held_exact_failure_expectation(semantic_detail)
                if self_unhashed
                else None
            ),
            semantic_fragment=semantic_detail,
            semantic_expectation=caller_held_exact_failure_expectation(semantic_detail),
        )
        attacks += 1

    child_attacks = (
        (
            "phase-checker-child-safe-flags-removed",
            CHECKER_RELATIVE,
            b'command = [sys.executable, "-I", "-S"]',
            b"command = [sys.executable]",
            b"def run_lean_portability_parser(*, optimized: bool) -> bytes:\n",
            b"def validate_lean_evidence_portability() -> LeanPortabilityArtifacts:\n",
        ),
        (
            "phase-selftest-child-safe-flags-reordered",
            SELF_RELATIVE,
            b'command = [sys.executable, "-I", "-S"]',
            b'command = [sys.executable, "-S", "-I"]',
            b"def python_command(\n",
            b"def run(\n",
        ),
    )
    for label, relative, before, after, start_marker, end_marker in child_attacks:
        semantic_detail = f"child Python command lacks exact -I -S prefix: {relative}"
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(relative,),
            mutate=lambda candidate, relative=relative, before=before, after=after, start_marker=start_marker, end_marker=end_marker: (
                replace_once_between(
                    candidate / relative,
                    start_marker,
                    end_marker,
                    before,
                    after,
                )
            ),
            first_fragment=semantic_detail,
            first_expectation=caller_held_exact_failure_expectation(semantic_detail),
            semantic_fragment=semantic_detail,
            semantic_expectation=caller_held_exact_failure_expectation(semantic_detail),
        )
        attacks += 1

    exact_stdin_attacks = (
        (
            "phase-checker-exact-stdin-removed",
            b"                input=self_raw,\n",
            b'                input=b"",\n',
            "exact-stdin child process inputs changed",
        ),
        (
            "phase-checker-live-path-child-substitution",
            b"                    EXACT_STDIN_BOOTSTRAP,\n",
            b"                    str(self_path),\n",
            "exact-stdin child command payload changed",
        ),
        (
            "phase-checker-child-environment-widened",
            b"                env=_minimal_python_child_environment(private_root),\n",
            b"                env=dict(os.environ),\n",
            "exact-stdin child process inputs changed",
        ),
        (
            "phase-checker-stdin-bootstrap-inheritance-weakened",
            b'    "    dont_inherit=True,\\n"\n',
            b'    "    dont_inherit=False,\\n"\n',
            "exact-stdin bootstrap digest changed",
        ),
        (
            "phase-checker-private-checker-materialization-removed",
            b"            checker_path.write_bytes(checker_raw)\n",
            b"            pass\n",
            "private exact-child materialization inventory changed",
        ),
    )
    for label, before, after, semantic_fragment in exact_stdin_attacks:
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda candidate, before=before, after=after: replace_once(
                candidate / CHECKER_RELATIVE,
                before,
                after,
            ),
            first_fragment=semantic_fragment,
            semantic_fragment=semantic_fragment,
        )
        attacks += 1

    official_attacks = (
        (
            "workflow-safe-invocation-removed",
            ".github/workflows/ci.yml",
            b"          python3 -I -S scripts/check-ksg-phase-isolation.py \\\n",
            b"          python3 scripts/check-ksg-phase-isolation.py \\\n",
            "CI corrective workflow differs from the exact af509 tooling transform",
        ),
        (
            "agents-safe-invocation-removed",
            "AGENTS.md",
            b"python3 -I -S scripts/check-ksg-phase-isolation-self-test.py\n",
            b"python3 scripts/check-ksg-phase-isolation-self-test.py\n",
            "official isolated Python invocation changed",
        ),
        (
            "just-safe-invocation-removed",
            "justfile",
            b"    python3 -I -S scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            b"    python3 scripts/check-ksg-phase-isolation.py --diagnostic-without-external-custody\n",
            "certified-SxPID2 claim checker differs from its exact three-digest rebind",
        ),
        (
            "foundational-wrapper-safe-invocation-removed",
            "scripts/check-foundational-sxpid-audit-pdf.sh",
            b'python3 -I -S "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
            b'python3 "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"\n',
            "official isolated Python invocation changed",
        ),
        (
            "foundational-markdown-safe-invocation-removed",
            "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md",
            b"python3 -I -S scripts/check-lean-descriptor-factorization.py\n",
            b"python3 scripts/check-lean-descriptor-factorization.py\n",
            "official isolated Python invocation changed",
        ),
        (
            "foundational-tool-readme-safe-invocation-removed",
            "audit/tools/foundational_sxpid/README.md",
            b"python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py\n",
            b"python3 audit/tools/foundational_sxpid/check_lcr_relation_witness.py\n",
            "official isolated Python invocation changed",
        ),
        (
            "foundational-tex-safe-invocation-removed",
            "audit/formal/latex/foundational-shared-exclusions-pid-audit.tex",
            b"python3 -I -S scripts/check-lean-descriptor-factorization-self-test.py\n",
            b"python3 scripts/check-lean-descriptor-factorization-self-test.py\n",
            "official isolated Python invocation changed",
        ),
    )
    for label, relative, before, after, semantic_fragment in official_attacks:
        restores_anchor_entry = relative == "audit/tools/foundational_sxpid/README.md"
        semantic_detail = (
            f"official isolated Python invocation changed: {relative}"
            if semantic_fragment == "official isolated Python invocation changed"
            else semantic_fragment
        )
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(relative,),
            mutate=lambda candidate, relative=relative, before=before, after=after: (
                replace_once(candidate / relative, before, after)
            ),
            first_fragment=(
                "candidate anchor delta differs from the separately reviewed A/M "
                "path policy"
                if restores_anchor_entry
                else "changed-byte projection digest mismatch"
            ),
            semantic_fragment=semantic_detail,
            semantic_expectation=(
                caller_held_exact_failure_expectation(semantic_detail)
                if semantic_fragment == "official isolated Python invocation changed"
                else None
            ),
            restores_tool_readme_anchor_for_downstream=restores_anchor_entry,
        )
        attacks += 1
    require(attacks == 18, "Python entry-isolation attack inventory changed")
    return attacks


def run_policy_authority_attacks(root: Path) -> int:
    attacks = 0
    policy = root / POLICY_RELATIVE

    hostile_policy_repin_attack(
        root,
        label="policy-authorizes-deletions",
        mutate=lambda _root: replace_once(
            policy,
            b'"deletions_permitted": false',
            b'"deletions_permitted": true',
        ),
        semantic_fragment="must forbid every deletion",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-mechanical-resealing",
        mutate=lambda _root: replace_once(
            policy,
            b'"mechanical_resealing_permitted": false',
            b'"mechanical_resealing_permitted": true',
        ),
        semantic_fragment="phase path policy authority contract",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-deletion-status",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": "CHANGELOG.md",\n'
                b'      "review_class": "documentation_release",\n'
                b'      "status": "M"'
            ),
            (
                b'"path": "CHANGELOG.md",\n'
                b'      "review_class": "documentation_release",\n'
                b'      "status": "D"'
            ),
        ),
        semantic_fragment="not classified A or M",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-unknown-review-class",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": "audit/evidence/ksg-rev4-public-ci-run-'
                b'30431352389-failure.json",\n'
                b'      "review_class": "corrective_evidence"'
            ),
            (
                b'"path": "audit/evidence/ksg-rev4-public-ci-run-'
                b'30431352389-failure.json",\n'
                b'      "review_class": "not_reviewed"'
            ),
        ),
        semantic_fragment="unknown review class",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-changelog-review-class-drift",
        mutate=lambda _root: replace_once(
            policy,
            (b'"path": "CHANGELOG.md",\n      "review_class": "documentation_release"'),
            (b'"path": "CHANGELOG.md",\n      "review_class": "verification_tool"'),
        ),
        semantic_fragment="corrective phase path/status/review-class inventory changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-authority-scope-drift",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"KSG revision-4 8b792-anchored C3 POSIX Lean replay, isolated "
                b"Python-entry, evidence, and foundational-publication correction only"
            ),
            b"KSG revision-4 unbounded correction",
        ),
        semantic_fragment="phase path policy authority contract value changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-exact-commit-message-drift",
        mutate=lambda _root: replace_once(
            policy,
            b'"exact_text": "fix: harden Lean evidence portability and replay\\n"',
            b'"exact_text": "fix: weaken Lean evidence portability and replay\\n"',
        ),
        semantic_fragment="phase path policy exact candidate commit envelope",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-exact-author-identity-drift",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"author": {\n'
                b'      "display_name": "Sepehr Mahmoudian",\n'
                b'      "email": "sepmhn@gmail.com"\n'
                b"    }"
            ),
            (
                b'"author": {\n'
                b'      "display_name": "Another Human",\n'
                b'      "email": "other@example.invalid"\n'
                b"    }"
            ),
        ),
        semantic_fragment="phase path policy exact candidate commit envelope",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-exact-committer-identity-drift",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"committer": {\n'
                b'      "display_name": "Sepehr Mahmoudian",\n'
                b'      "email": "sepmhn@gmail.com"\n'
                b"    }"
            ),
            (
                b'"committer": {\n'
                b'      "display_name": "Another Human",\n'
                b'      "email": "other@example.invalid"\n'
                b"    }"
            ),
        ),
        semantic_fragment="phase path policy exact candidate commit envelope",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-signature-permission-drift",
        mutate=lambda _root: replace_once(
            policy,
            b'"signature_headers_permitted": false',
            b'"signature_headers_permitted": true',
        ),
        semantic_fragment="phase path policy exact candidate commit envelope",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-commit-envelope-negative-record-erasure",
        mutate=lambda _root: replace_once(
            policy,
            b'"commit object with a gpgsig header"',
            b'"an unspecified negative fixture"',
        ),
        semantic_fragment="phase path policy commit-envelope hostile-review record",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-receipt-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Keep the terminal CI and CodeQL execution facts, job and step "
                b"counts, logs, routes, and then-selected four-file v2 remediation "
                b"byte-for-byte historical."
            ),
            b"Record a generic CI failure.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-exact-commit-envelope-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Bind the exact UTF-8 message and human author and committer "
                b"identities; reject every gpgsig and gpgsig-* header while "
                b"retaining bounded attribution-detector negatives."
            ),
            b"Inspect commit metadata.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-external-tree-whitespace-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Require external tree and checkpoint together, scrubbed full-"
                b"delta whitespace checks, clean-worktree parity, and exact "
                b"one-child commit metadata for closure credit."
            ),
            b"Optionally inspect tracked whitespace.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-active-clone-probe-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Run normal and optimized hostile suites over policy, receipts, "
                b"startup contamination, parser and evidence schemas, Git history "
                b"and context, external trees, science freezes, and self-reference."
            ),
            b"Permit Git progress probes inside active custody clones.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-portable-parser-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Require Python -I -S, digest-before-compile exact-source loading, "
                b"POSIX openat-style parent traversal, single-linked tracked leaves, "
                b"double reads, and endpoint replay; retain generic endpoint "
                b"swap/use/restore as an unauthenticated negative boundary and do "
                b"not claim atomic history."
            ),
            b"Parse some Lean output.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-nineteen-path-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Require exactly nineteen paths in one unsigned, attribution-free, "
                b"single-parent direct child of commit "
                b"8b792bc143fff2d84f2d8e7817d1de7850741223 and tree "
                b"8e247b9a6c46fd6266fe4fc02fbe9c3142268215."
            ),
            b"Permit any corrective path.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-self-entry-reclassified-modified",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": "audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json",\n'
                b'      "review_class": "phase_authority",\n'
                b'      "status": "A"'
            ),
            (
                b'"path": "audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json",\n'
                b'      "review_class": "phase_authority",\n'
                b'      "status": "M"'
            ),
        ),
        semantic_fragment="corrective phase path/status/review-class inventory changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-receipt-entry-omission",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"    {\n"
                b'      "path": "audit/evidence/ksg-rev4-public-ci-run-'
                b'30431352389-failure.json",\n'
                b'      "review_class": "corrective_evidence",\n'
                b'      "status": "A"\n'
                b"    },\n"
            ),
            b"",
        ),
        semantic_fragment="corrective phase path/status/review-class inventory changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-schema-revision-drift",
        mutate=lambda _root: replace_once(
            policy,
            b'"schema_revision": 6',
            b'"schema_revision": 7',
        ),
        semantic_fragment="phase path policy schema revision value changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-anchor-tree-drift",
        mutate=lambda _root: replace_once(
            policy,
            b'"tree": "8e247b9a6c46fd6266fe4fc02fbe9c3142268215"',
            b'"tree": "0e247b9a6c46fd6266fe4fc02fbe9c3142268215"',
        ),
        semantic_fragment="phase path policy anchor value changed at $/tree",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-anchor-rollback",
        mutate=lambda _root: replace_once(
            policy,
            b'"commit": "8b792bc143fff2d84f2d8e7817d1de7850741223"',
            b'"commit": "af50935be9ecf9a81aeb30c56b45059652468746"',
        ),
        semantic_fragment="phase path policy anchor value changed at $/commit",
    )
    attacks += 1
    hostile_family_counts = {
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
    }
    for family, expected in hostile_family_counts.items():
        hostile_policy_repin_attack(
            root,
            label=f"policy-hostile-family-count-{family}",
            mutate=lambda _root, family=family, expected=expected: replace_once(
                policy,
                f'"{family}": {expected}'.encode("ascii"),
                f'"{family}": {expected + 1}'.encode("ascii"),
            ),
            semantic_fragment="phase path policy hostile-suite contract",
        )
        attacks += 1
    for label, before, after in (
        (
            "policy-hostile-contracted-total",
            b'"contracted_total": 351',
            b'"contracted_total": 352',
        ),
        (
            "policy-hostile-json-type-control-count",
            b'"json_type_firewall": 2',
            b'"json_type_firewall": 3',
        ),
        (
            "policy-hostile-self-reference-control-count",
            b'"retained_self_reference_boundary": 1',
            b'"retained_self_reference_boundary": 2',
        ),
    ):
        hostile_policy_repin_attack(
            root,
            label=label,
            mutate=lambda _root, before=before, after=after: replace_once(
                policy,
                before,
                after,
            ),
            semantic_fragment="phase path policy hostile-suite contract",
        )
        if label == "policy-hostile-self-reference-control-count":
            # Independently mutate the newly typed raw-transport subcontrol field
            # inside this counted policy case; do not inflate the 44-case family.
            hostile_policy_repin_attack(
                root,
                label=("policy-hostile-phase-lean-raw-transport-subcontrol-count"),
                mutate=lambda _root: replace_once(
                    policy,
                    b'"phase_lean_raw_transport_subcontrols": 6',
                    b'"phase_lean_raw_transport_subcontrols": 7',
                ),
                semantic_fragment="phase path policy hostile-suite contract",
            )
        attacks += 1
    for label, before, after in (
        (
            "policy-supersession-final-authority-weakened",
            b"supersedes only the historical receipt's chosen correction",
            b"preserves the historical receipt's chosen correction",
        ),
        (
            "policy-supersession-receipt-digest-drift",
            b'"historical_receipt_sha256": "73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20"',
            b'"historical_receipt_sha256": "03c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20"',
        ),
        (
            "policy-supersession-historical-scope-drift",
            b"descriptor checker, its self-test, and their two generated evidence files only",
            b"descriptor tooling and any generated evidence",
        ),
        (
            "policy-supersession-workflow-history-rewritten",
            b'"historical_workflow_changed": false',
            b'"historical_workflow_changed": true',
        ),
        (
            "policy-supersession-retroactive-facts-permitted",
            b'"retroactive_run_facts_changed": false',
            b'"retroactive_run_facts_changed": true',
        ),
    ):
        hostile_policy_repin_attack(
            root,
            label=label,
            mutate=lambda _root, before=before, after=after: replace_once(
                policy,
                before,
                after,
            ),
            semantic_fragment="phase path policy historical remediation supersession",
        )
        attacks += 1
    require(attacks == 44, "policy-authority attack inventory changed")
    return attacks


def run_json_type_firewall_controls(root: Path) -> int:
    """Exercise type-confusion controls separately from the hostile attacks."""

    controls = 0
    policy = root / POLICY_RELATIVE

    hostile_policy_repin_attack(
        root,
        label="json-type-firewall-schema-revision-boolean",
        mutate=lambda _root: replace_once(
            policy,
            b'"schema_revision": 6',
            b'"schema_revision": true',
        ),
        semantic_fragment="wrong JSON type at $",
    )
    controls += 1

    hostile_policy_repin_attack(
        root,
        label="json-type-firewall-authoritative-integer",
        mutate=lambda _root: replace_once(
            policy,
            b'"authoritative": true',
            b'"authoritative": 1',
        ),
        semantic_fragment="wrong JSON type at $/authoritative",
    )
    controls += 1
    return controls


def run_path_and_custody_attacks(root: Path) -> int:
    attacks = 0
    added_path = PORTABILITY_CORRECTIVE_EVIDENCE

    simple_attack(
        root,
        label="unreviewed-path-addition",
        paths=("phase-stray.txt",),
        mutate=lambda candidate: (candidate / "phase-stray.txt").write_text(
            "not reviewed\n", encoding="utf-8", newline="\n"
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="allowed-path-removal",
        paths=(added_path,),
        mutate=lambda candidate: (candidate / added_path).unlink(),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="self-test-path-removal",
        paths=(SELF_RELATIVE,),
        mutate=lambda candidate: (candidate / SELF_RELATIVE).unlink(),
        expected_fragment="candidate path is missing",
        failure_expectation=diagnostic_failure_expectation(
            route="deleted-candidate-path",
            fragment="candidate path is missing",
            exact_prefix=f"{SELF_RELATIVE!r}: candidate path is missing: ",
        ),
    )
    attacks += 1

    simple_attack(
        root,
        label="protected-pid2-blob",
        paths=("crates/pid-core/src/pid2.rs",),
        mutate=lambda candidate: append_bytes(
            candidate / "crates/pid-core/src/pid2.rs",
            b"\n// forbidden KSG-phase mutation\n",
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="protected-pid2-mode",
        paths=("crates/pid-core/src/pid2.rs",),
        mutate=lambda candidate: (candidate / "crates/pid-core/src/pid2.rs").chmod(
            0o755
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    forbidden_claim = "claims/PID2-REPRESENTED-SUM-001/phase-injection.md"
    simple_attack(
        root,
        label="forbidden-later-claim",
        paths=(forbidden_claim,),
        mutate=lambda candidate: (
            (candidate / forbidden_claim).parent.mkdir(parents=True, exist_ok=True),
            (candidate / forbidden_claim).write_text(
                "later wave\n", encoding="utf-8", newline="\n"
            ),
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="allowed-file-symlink",
        paths=(".github/workflows/ci.yml",),
        mutate=lambda candidate: (
            (candidate / ".github/workflows/ci.yml").unlink(),
            (candidate / ".github/workflows/ci.yml").symlink_to(
                "../../scripts/check-ksg-phase-isolation.py"
            ),
        ),
        expected_fragment=(
            "'.github/workflows/ci.yml': candidate must be a regular non-symlink file"
        ),
        failure_expectation=caller_held_exact_failure_expectation(
            "'.github/workflows/ci.yml': candidate must be a regular non-symlink file"
        ),
    )
    attacks += 1

    def hardlink_mutation(candidate: Path) -> None:
        target = candidate / ".github/workflows/ci.yml"
        donor = candidate / PORTABILITY_CORRECTIVE_EVIDENCE
        target.unlink()
        os.link(donor, target)

    simple_attack(
        root,
        label="allowed-file-hardlink",
        paths=(".github/workflows/ci.yml", PORTABILITY_CORRECTIVE_EVIDENCE),
        mutate=hardlink_mutation,
        expected_fragment=(
            "'.github/workflows/ci.yml': hard-linked candidate file is forbidden"
        ),
        failure_expectation=caller_held_exact_failure_expectation(
            "'.github/workflows/ci.yml': hard-linked candidate file is forbidden"
        ),
    )
    attacks += 1
    return attacks


def run_external_tree_custody_tests(
    root: Path,
    facts: dict[str, object],
) -> int:
    tests = 0
    candidate_tree = write_candidate_tree(root, facts)
    checkpoint = write_checkpoint_commit(root, candidate_tree, CURRENT_ANCHOR)
    run_checker(
        root,
        expect_success=True,
        arguments=(
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            checkpoint,
        ),
    )
    tests += 1

    head_tree_process = run(git_command("rev-parse", "HEAD^{tree}"), cwd=root)
    require(head_tree_process.returncode == 0, "cannot resolve hostile HEAD tree")
    head_tree = head_tree_process.stdout.decode("ascii", errors="strict").strip()
    wrong_tree_commit = write_checkpoint_commit(root, head_tree, CURRENT_ANCHOR)
    run_checker(
        root,
        expect_success=False,
        expected_fragment="staged/checkpoint tree differs",
        arguments=(
            "--expected-candidate-tree",
            head_tree,
            "--checkpoint-commit",
            wrong_tree_commit,
        ),
    )
    tests += 1

    run_checker(
        root,
        expect_success=False,
        expected_fragment=(
            "creditable validation requires the external candidate-tree/checkpoint pair"
        ),
        auto_diagnostic=False,
    )
    tests += 1

    run_checker(
        root,
        expect_success=False,
        expected_fragment=(
            "--diagnostic-without-external-custody cannot accompany external custody"
        ),
        arguments=(
            "--diagnostic-without-external-custody",
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            checkpoint,
        ),
    )
    tests += 1

    run_checker(
        root,
        expect_success=False,
        expected_fragment="checkpoint commit tree differs",
        arguments=(
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            wrong_tree_commit,
        ),
    )
    tests += 1

    parent_process = run(git_command("rev-parse", f"{CURRENT_ANCHOR}^"), cwd=root)
    require(parent_process.returncode == 0, "cannot resolve hostile checkpoint parent")
    wrong_parent = parent_process.stdout.decode("ascii", errors="strict").strip()
    wrong_parent_commit = write_checkpoint_commit(root, candidate_tree, wrong_parent)
    run_checker(
        root,
        expect_success=False,
        expected_fragment="not the exact child of snapshot HEAD",
        arguments=(
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            wrong_parent_commit,
        ),
    )
    tests += 1

    run_checker(
        root,
        expect_success=False,
        expected_fragment=(
            "--expected-candidate-tree and --checkpoint-commit must be supplied together"
        ),
        arguments=("--checkpoint-commit", checkpoint),
    )
    tests += 1

    run_checker(
        root,
        expect_success=False,
        expected_fragment=(
            "--expected-candidate-tree and --checkpoint-commit must be supplied together"
        ),
        arguments=("--expected-candidate-tree", candidate_tree),
    )
    tests += 1

    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    checker = root / CHECKER_RELATIVE
    saved = backup(root, (PORTABILITY_CORRECTIVE_EVIDENCE, CHECKER_RELATIVE))
    local_whitespace_override_installed = False
    try:
        old_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        append_bytes(
            memo,
            b"\n<!-- added-path external-tree whitespace control -->  \n",
        )
        run_checker(
            root,
            expect_success=False,
            expected_fragment="changed-byte projection digest mismatch",
        )
        new_digest = hashlib.sha256(memo.read_bytes()).hexdigest().encode("ascii")
        replace_exact_count(
            checker,
            old_digest,
            new_digest,
            expected_count=2,
        )
        local_config = run(
            git_command("config", "--local", "core.whitespace", "-trailing-space"),
            cwd=root,
        )
        require(
            local_config.returncode == 0,
            "cannot install hostile local core.whitespace override",
        )
        local_whitespace_override_installed = True
        rebase_checker(root)

        # Retain the exact false-green boundary: without an external tree,
        # the tracked-worktree-only route cannot see whitespace in this added
        # policy-authorized file after a coordinated fact rebind.
        run_checker(root, expect_success=True)
        whitespace_tree = write_candidate_tree(root, facts)
        whitespace_checkpoint = write_checkpoint_commit(
            root,
            whitespace_tree,
            CURRENT_ANCHOR,
        )
        run_checker(
            root,
            expect_success=False,
            expected_fragment=(
                "external candidate tree failed the scrubbed anchor-to-tree "
                "Git whitespace check"
            ),
            failure_expectation=diagnostic_failure_expectation(
                route="external-tree-whitespace",
                fragment=(
                    "external candidate tree failed the scrubbed anchor-to-tree "
                    "Git whitespace check"
                ),
                exact_prefix=(
                    "external candidate tree failed the scrubbed anchor-to-tree "
                    "Git whitespace check: "
                ),
            ),
            arguments=(
                "--expected-candidate-tree",
                whitespace_tree,
                "--checkpoint-commit",
                whitespace_checkpoint,
            ),
        )
        tests += 1
    except SelfTestError as error:
        raise SelfTestError(f"external-tree-added-path-whitespace: {error}") from error
    finally:
        restore(root, saved)
        if local_whitespace_override_installed:
            unset = run(
                git_command(
                    "config",
                    "--local",
                    "--unset-all",
                    "core.whitespace",
                ),
                cwd=root,
            )
            require(
                unset.returncode == 0,
                "cannot remove hostile local core.whitespace override",
            )
    run_checker(root, expect_success=True)
    return tests


def run_retained_self_reference_boundary(
    root: Path,
    facts: dict[str, object],
) -> int:
    """Retain the coordinated-rebase cut and prove only a pre-pinned tree rejects it."""

    pristine_tree = write_candidate_tree(root, facts)
    pristine_checkpoint = write_checkpoint_commit(root, pristine_tree, CURRENT_ANCHOR)
    saved = backup(root, (POLICY_RELATIVE, CHECKER_RELATIVE))
    checker = root / CHECKER_RELATIVE
    policy = root / POLICY_RELATIVE
    try:
        old_policy_digest = (
            hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        )
        replace_once(
            policy,
            (
                b'"path": "audit/evidence/ksg-rev4-public-ci-portability-'
                b'correction-2026-07-29.md",\n'
                b'      "review_class": "corrective_evidence"'
            ),
            (
                b'"path": "audit/evidence/ksg-rev4-public-ci-portability-'
                b'correction-2026-07-29.md",\n'
                b'      "review_class": "phase_authority"'
            ),
        )
        new_policy_digest = (
            hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        )
        replace_exact_count(
            checker,
            old_policy_digest,
            new_policy_digest,
            expected_count=2,
        )
        replace_once(
            checker,
            (
                b"    (\n"
                b"        PORTABILITY_CORRECTIVE_EVIDENCE,\n"
                b'        "A",\n'
                b'        "corrective_evidence",\n'
                b"    ),"
            ),
            (
                b"    (\n"
                b"        PORTABILITY_CORRECTIVE_EVIDENCE,\n"
                b'        "A",\n'
                b'        "phase_authority",\n'
                b"    ),"
            ),
        )
        rebase_checker(root)

        # This acceptance is the retained negative result: the checker cannot
        # authenticate a coordinated mutation of its own source and policy.
        run_checker(root, expect_success=True)
        attacker_tree = write_candidate_tree(root, facts)
        attacker_checkpoint = write_checkpoint_commit(
            root,
            attacker_tree,
            CURRENT_ANCHOR,
        )
        run_checker(
            root,
            expect_success=True,
            arguments=(
                "--expected-candidate-tree",
                attacker_tree,
                "--checkpoint-commit",
                attacker_checkpoint,
            ),
        )
        run_checker(
            root,
            expect_success=False,
            expected_fragment="staged/checkpoint tree differs",
            arguments=(
                "--expected-candidate-tree",
                pristine_tree,
                "--checkpoint-commit",
                pristine_checkpoint,
            ),
        )
    except SelfTestError as error:
        raise SelfTestError(f"retained-self-reference-boundary: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)
    return 1


def run_repository_context_attacks(root: Path) -> int:
    attacks = 0
    common = common_git_dir(root)
    config = common / "config"

    config_attacks = (
        (
            "local-attr-tree",
            git_command("config", "--local", "attr.tree", CURRENT_ANCHOR),
            "forbidden local Git configuration key: attr.tree",
        ),
        (
            "local-clean-filter",
            git_command("config", "--local", "filter.phase.clean", "/usr/bin/true"),
            "forbidden local Git configuration key: filter.phase.clean",
        ),
        (
            "local-include",
            git_command("config", "--local", "include.path", "/tmp/phase-include"),
            "forbidden local Git configuration key: include.path",
        ),
        (
            "local-attributes-file",
            git_command("config", "--local", "core.attributesFile", "/tmp/phase-attrs"),
            "forbidden local Git configuration key: core.attributesfile",
        ),
        (
            "local-excludes-file",
            git_command("config", "--local", "core.excludesFile", "/tmp/phase-ignore"),
            "forbidden local Git configuration key: core.excludesfile",
        ),
        (
            "local-fsmonitor",
            git_command("config", "--local", "core.fsmonitor", "/tmp/phase-fsmonitor"),
            "forbidden local Git configuration key: core.fsmonitor",
        ),
        (
            "local-sparse-index",
            git_command("config", "--local", "index.sparse", "true"),
            "forbidden local Git configuration key: index.sparse",
        ),
    )
    for label, command, fragment in config_attacks:

        def mutate_config(command: list[str] = command) -> None:
            process = run(command, cwd=root)
            require(process.returncode == 0, f"{label}: cannot mutate local config")

        metadata_attack(
            root,
            label=label,
            paths=(config,),
            mutate=mutate_config,
            expected_fragment=fragment,
            failure_expectation=caller_held_exact_failure_expectation(fragment),
        )
        attacks += 1

    info_exclude = common / "info/exclude"
    metadata_invariance(
        root,
        label="info-exclude-match-all-is-irrelevant",
        paths=(info_exclude,),
        mutate=lambda: info_exclude.write_text(
            "*\n",
            encoding="utf-8",
            newline="\n",
        ),
    )
    attacks += 1
    metadata_invariance(
        root,
        label="info-exclude-appended-rule-is-irrelevant",
        paths=(info_exclude,),
        mutate=lambda: append_bytes(info_exclude, b"\nphase-hidden\n"),
    )
    attacks += 1

    simple_attack(
        root,
        label="second-nested-gitignore-source",
        paths=("claims/KSG-INTEGER-HARMONIC-001/.gitignore",),
        mutate=lambda candidate: (
            candidate / "claims/KSG-INTEGER-HARMONIC-001/.gitignore"
        ).write_text(
            "claim-v4.md\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="candidate anchor delta differs",
    )
    attacks += 1

    info_attributes = common / "info/attributes"
    metadata_attack(
        root,
        label="info-attributes-overlay",
        paths=(info_attributes,),
        mutate=lambda: info_attributes.write_text(
            "* filter=phase\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="Git overlay file is forbidden: info/attributes",
        failure_expectation=caller_held_exact_failure_expectation(
            "Git overlay file is forbidden: info/attributes"
        ),
    )
    attacks += 1

    worktree_config = common / "config.worktree"
    metadata_attack(
        root,
        label="worktree-config-overlay",
        paths=(worktree_config,),
        mutate=lambda: worktree_config.write_text(
            "[attr]\n\ttree = HEAD\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="Git overlay file is forbidden: config.worktree",
        failure_expectation=caller_held_exact_failure_expectation(
            "Git overlay file is forbidden: config.worktree"
        ),
    )
    attacks += 1

    grafts = common / "info/grafts"
    metadata_attack(
        root,
        label="legacy-grafts-overlay",
        paths=(grafts,),
        mutate=lambda: grafts.write_text(
            f"{CURRENT_ANCHOR}\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="Git overlay file is forbidden: info/grafts",
        failure_expectation=caller_held_exact_failure_expectation(
            "Git overlay file is forbidden: info/grafts"
        ),
    )
    attacks += 1

    with tempfile.TemporaryDirectory(prefix="pid-rs-empty-alternate.") as alternate_raw:
        alternates = common / "objects/info/alternates"
        metadata_attack(
            root,
            label="alternate-object-overlay",
            paths=(alternates,),
            mutate=lambda: alternates.write_text(
                str(Path(alternate_raw).resolve(strict=True)) + "\n",
                encoding="utf-8",
                newline="\n",
            ),
            expected_fragment="Git overlay file is forbidden: objects/info/alternates",
            failure_expectation=caller_held_exact_failure_expectation(
                "Git overlay file is forbidden: objects/info/alternates"
            ),
        )
    attacks += 1

    replace_ref = common / f"refs/replace/{CURRENT_ANCHOR}"
    parent = run(git_command("rev-parse", f"{CURRENT_ANCHOR}^"), cwd=root)
    require(parent.returncode == 0, "cannot resolve replacement-ref negative control")
    parent_oid = parent.stdout.decode("ascii", errors="strict").strip()
    metadata_attack(
        root,
        label="replacement-ref-overlay",
        paths=(replace_ref,),
        mutate=lambda: (
            replace_ref.parent.mkdir(parents=True, exist_ok=True),
            replace_ref.write_text(
                parent_oid + "\n",
                encoding="ascii",
                newline="\n",
            ),
        ),
        expected_fragment="Git replacement references are forbidden",
    )
    attacks += 1

    run_checker(
        root,
        expect_success=True,
        environment_overrides={
            "GIT_ATTR_SOURCE": "refs/heads/not-real",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.attributesFile",
            "GIT_CONFIG_VALUE_0": "/tmp/hostile-attributes",
            "GIT_DIR": "/tmp/not-a-repository",
            "GIT_INDEX_FILE": "/tmp/hostile-index",
            "GIT_OBJECT_DIRECTORY": "/tmp/hostile-objects",
        },
    )
    attacks += 1
    return attacks


def committed_candidate(
    source: Path,
    destination: Path,
    facts: dict[str, object],
    overlay: FrozenOverlay,
) -> str:
    clone_candidate(source, destination, facts, overlay)
    return commit_exact_paths(
        destination,
        anchor_delta_paths(facts),
        message=EXPECTED_C3_COMMIT_SUBJECT,
    )


def run_committed_checker(root: Path) -> subprocess.CompletedProcess[bytes]:
    head_process = run(git_command("rev-parse", "HEAD"), cwd=root)
    tree_process = run(git_command("rev-parse", "HEAD^{tree}"), cwd=root)
    require(
        head_process.returncode == 0 and tree_process.returncode == 0,
        "cannot resolve committed lifecycle HEAD/tree",
    )
    head = head_process.stdout.decode("ascii", errors="strict").strip()
    tree = tree_process.stdout.decode("ascii", errors="strict").strip()
    return run_checker(
        root,
        expect_success=True,
        expected_lifecycle="committed-descendant",
        arguments=(
            "--expected-candidate-tree",
            tree,
            "--checkpoint-commit",
            head,
        ),
    )


def run_committed_checker_failure(root: Path, *, expected_fragment: str) -> None:
    head_process = run(git_command("rev-parse", "HEAD"), cwd=root)
    tree_process = run(git_command("rev-parse", "HEAD^{tree}"), cwd=root)
    require(
        head_process.returncode == 0 and tree_process.returncode == 0,
        "cannot resolve hostile committed lifecycle HEAD/tree",
    )
    head = head_process.stdout.decode("ascii", errors="strict").strip()
    tree = tree_process.stdout.decode("ascii", errors="strict").strip()
    expected_detail = f"post-anchor commit {head}: {expected_fragment}"
    run_checker(
        root,
        expect_success=False,
        expected_fragment=expected_detail,
        failure_expectation=caller_held_exact_failure_expectation(expected_detail),
        arguments=(
            "--expected-candidate-tree",
            tree,
            "--checkpoint-commit",
            head,
        ),
    )


def run_lifecycle_history_tests(
    source: Path,
    temporary: Path,
    facts: dict[str, object],
    overlay: FrozenOverlay,
) -> int:
    tests = 0

    clean = temporary / "committed-clean"
    committed_candidate(source, clean, facts, overlay)
    process = run_committed_checker(clean)
    require(
        b"lifecycle=committed-descendant" in process.stdout,
        "clean descendant did not report the committed lifecycle",
    )
    tests += 1
    run_checker(
        clean,
        expect_success=False,
        expected_fragment="committed lifecycle requires --expected-candidate-tree",
    )
    tests += 1

    coauthor = temporary / "committed-coauthor-attribution"
    clone_candidate(source, coauthor, facts, overlay)
    commit_exact_paths(
        coauthor,
        anchor_delta_paths(facts),
        message=(
            "phase isolation forbidden coauthor fixture\n\n"
            "Co-Authored-By: Codex Agent <agent@example.invalid>"
        ),
    )
    run_committed_checker_failure(
        coauthor,
        expected_fragment="final C3 commit message differs from exact reviewed bytes",
    )
    tests += 1

    coauthor_prose = temporary / "committed-coauthor-prose"
    clone_candidate(source, coauthor_prose, facts, overlay)
    commit_exact_paths(
        coauthor_prose,
        anchor_delta_paths(facts),
        message=(
            "phase isolation forbidden attribution fixture\n\n"
            "Co-authored with an AI agent"
        ),
    )
    run_committed_checker_failure(
        coauthor_prose,
        expected_fragment="final C3 commit message differs from exact reviewed bytes",
    )
    tests += 1

    ai_author = temporary / "committed-ai-author-identity"
    clone_candidate(source, ai_author, facts, overlay)
    commit_exact_paths(
        ai_author,
        anchor_delta_paths(facts),
        message=EXPECTED_C3_COMMIT_SUBJECT,
        author_name="Codex Agent",
        author_email="agent@example.invalid",
    )
    run_committed_checker_failure(
        ai_author,
        expected_fragment=(
            "final C3 author identity differs from the exact reviewed human identity"
        ),
    )
    tests += 1

    committer_drift = temporary / "committed-committer-identity-drift"
    clone_candidate(source, committer_drift, facts, overlay)
    commit_exact_paths(
        committer_drift,
        anchor_delta_paths(facts),
        message=EXPECTED_C3_COMMIT_SUBJECT,
        committer_name="Another Human",
        committer_email="another-human@example.invalid",
    )
    run_committed_checker_failure(
        committer_drift,
        expected_fragment=(
            "final C3 committer identity differs from the exact reviewed human identity"
        ),
    )
    tests += 1

    malformed_epoch = temporary / "committed-malformed-author-epoch"
    clone_candidate(source, malformed_epoch, facts, overlay)
    commit_raw_candidate(
        malformed_epoch,
        facts,
        author_header=("Sepehr Mahmoudian <sepmhn@gmail.com> not-an-epoch +0000"),
    )
    run_committed_checker_failure(
        malformed_epoch,
        expected_fragment="malformed author epoch/timezone",
    )
    tests += 1

    for label, timezone in (
        ("text", "UTC"),
        ("hour-overflow", "+9999"),
        ("minute-overflow", "+1460"),
        ("fourteen-hour-minute", "+1401"),
        ("missing-sign", "0000"),
    ):
        malformed_timezone = temporary / f"committed-malformed-timezone-{label}"
        clone_candidate(source, malformed_timezone, facts, overlay)
        commit_raw_candidate(
            malformed_timezone,
            facts,
            committer_header=(
                f"Sepehr Mahmoudian <sepmhn@gmail.com> 946684800 {timezone}"
            ),
        )
        run_committed_checker_failure(
            malformed_timezone,
            expected_fragment="malformed committer epoch/timezone",
        )
        tests += 1

    extra_header = temporary / "committed-extra-header"
    clone_candidate(source, extra_header, facts, overlay)
    commit_raw_candidate(
        extra_header,
        facts,
        additional_header_lines=("encoding UTF-8",),
    )
    run_committed_checker_failure(
        extra_header,
        expected_fragment=(
            "final C3 commit headers differ from the exact unsigned "
            "single-parent Git envelope"
        ),
    )
    tests += 1

    unterminated_message = temporary / "committed-unterminated-message"
    clone_candidate(source, unterminated_message, facts, overlay)
    commit_raw_candidate(
        unterminated_message,
        facts,
        message_raw=EXPECTED_C3_COMMIT_SUBJECT.encode("utf-8"),
    )
    run_committed_checker_failure(
        unterminated_message,
        expected_fragment=("commit message must be LF-terminated UTF-8 without CR/NUL"),
    )
    tests += 1

    generated_advertising = temporary / "committed-generated-advertising"
    clone_candidate(source, generated_advertising, facts, overlay)
    commit_exact_paths(
        generated_advertising,
        anchor_delta_paths(facts),
        message=(
            "phase isolation forbidden advertising fixture\n\n"
            "- Generated with Claude Code"
        ),
    )
    run_committed_checker_failure(
        generated_advertising,
        expected_fragment="final C3 commit message differs from exact reviewed bytes",
    )
    tests += 1

    generated_key = temporary / "committed-generated-attribution-key"
    clone_candidate(source, generated_key, facts, overlay)
    commit_exact_paths(
        generated_key,
        anchor_delta_paths(facts),
        message=(
            "phase isolation forbidden attribution key fixture\n\n"
            "Generated-With: Claude Code"
        ),
    )
    run_committed_checker_failure(
        generated_key,
        expected_fragment="final C3 commit message differs from exact reviewed bytes",
    )
    tests += 1

    ai_review_trailer = temporary / "committed-ai-review-trailer"
    clone_candidate(source, ai_review_trailer, facts, overlay)
    commit_exact_paths(
        ai_review_trailer,
        anchor_delta_paths(facts),
        message=(
            "phase isolation forbidden review trailer fixture\n\nReviewed-By: LLM"
        ),
    )
    run_committed_checker_failure(
        ai_review_trailer,
        expected_fragment="final C3 commit message differs from exact reviewed bytes",
    )
    tests += 1

    arbitrary_message = temporary / "committed-arbitrary-message"
    clone_candidate(source, arbitrary_message, facts, overlay)
    commit_exact_paths(
        arbitrary_message,
        anchor_delta_paths(facts),
        message="document evidence generated by the exact deterministic oracle",
    )
    run_committed_checker_failure(
        arbitrary_message,
        expected_fragment="final C3 commit message differs from exact reviewed bytes",
    )
    tests += 1

    for signature_header in ("gpgsig", "gpgsig-sha256", "gpgsig-v2"):
        signed = temporary / f"committed-{signature_header}"
        clone_candidate(source, signed, facts, overlay)
        commit_raw_signed_candidate(
            signed,
            facts,
            signature_header=signature_header,
        )
        run_committed_checker_failure(
            signed,
            expected_fragment=(
                f"signed commit header is forbidden: {signature_header}"
            ),
        )
        tests += 1

    split = temporary / "committed-split-descendant"
    clone_candidate(source, split, facts, overlay)
    delta = facts.get("anchor_delta")
    require(isinstance(delta, list), "anchor delta facts are unavailable")
    modified_paths = tuple(
        item["path"]
        for item in delta
        if isinstance(item, dict) and item.get("status") == "M"
    )
    added_paths = tuple(
        item["path"]
        for item in delta
        if isinstance(item, dict) and item.get("status") == "A"
    )
    require(
        modified_paths and added_paths,
        "split-descendant lifecycle requires both M and A policy paths",
    )
    commit_exact_paths(
        split,
        modified_paths,
        message="phase isolation exact modified subset",
    )
    commit_exact_paths(
        split,
        added_paths,
        message="phase isolation exact delayed added subset",
    )
    run_checker(
        split,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    empty_prefix = temporary / "committed-empty-prefix"
    clone_candidate(source, empty_prefix, facts, overlay)
    commit_empty(
        empty_prefix,
        message="phase isolation forbidden empty prefix",
    )
    commit_exact_paths(
        empty_prefix,
        anchor_delta_paths(facts),
        message="phase isolation exact candidate after empty prefix",
    )
    run_checker(
        empty_prefix,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    hostile_allowed = temporary / "committed-allowed-hostile-restore"
    allowed_base = committed_candidate(source, hostile_allowed, facts, overlay)
    allowed_path = "CHANGELOG.md"
    append_bytes(
        hostile_allowed / allowed_path,
        b"\n# transient fourth workflow edit\n",
    )
    commit_exact_paths(
        hostile_allowed,
        (allowed_path,),
        message="phase isolation allowed-path hostile blob",
    )
    restore_allowed = run(
        git_command("checkout", allowed_base, "--", allowed_path),
        cwd=hostile_allowed,
    )
    require(restore_allowed.returncode == 0, "cannot restore allowed lifecycle path")
    commit_exact_paths(
        hostile_allowed,
        (allowed_path,),
        message="phase isolation allowed-path exact restoration",
    )
    run_checker(
        hostile_allowed,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    draft_added = temporary / "committed-added-draft-restore"
    clone_candidate(source, draft_added, facts, overlay)
    draft_path = PORTABILITY_CORRECTIVE_EVIDENCE
    final_draft_bytes = (draft_added / draft_path).read_bytes()
    (draft_added / draft_path).write_bytes(b"# transient draft claim\n")
    commit_exact_paths(
        draft_added,
        anchor_delta_paths(facts),
        message="phase isolation draft added-path negative control",
    )
    (draft_added / draft_path).write_bytes(final_draft_bytes)
    commit_exact_paths(
        draft_added,
        (draft_path,),
        message="phase isolation final added-path restoration",
    )
    run_checker(
        draft_added,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    reverted = temporary / "committed-final-anchor-final"
    final_base = committed_candidate(source, reverted, facts, overlay)
    reverted_path = "CHANGELOG.md"
    checkout_anchor = run(
        git_command("checkout", CURRENT_ANCHOR, "--", reverted_path),
        cwd=reverted,
    )
    require(checkout_anchor.returncode == 0, "cannot restore anchor lifecycle bytes")
    commit_exact_paths(
        reverted,
        (reverted_path,),
        message="phase isolation forbidden return to anchor",
    )
    checkout_final = run(
        git_command("checkout", final_base, "--", reverted_path),
        cwd=reverted,
    )
    require(checkout_final.returncode == 0, "cannot restore final lifecycle bytes")
    commit_exact_paths(
        reverted,
        (reverted_path,),
        message="phase isolation second final transition",
    )
    run_checker(
        reverted,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    mode_change = temporary / "committed-mode-change-restore"
    mode_base = committed_candidate(source, mode_change, facts, overlay)
    mode_path = "CHANGELOG.md"
    (mode_change / mode_path).chmod(0o755)
    commit_exact_paths(
        mode_change,
        (mode_path,),
        message="phase isolation forbidden mode transition",
    )
    restore_mode = run(
        git_command("checkout", mode_base, "--", mode_path),
        cwd=mode_change,
    )
    require(restore_mode.returncode == 0, "cannot restore final lifecycle mode")
    commit_exact_paths(
        mode_change,
        (mode_path,),
        message="phase isolation exact mode restoration",
    )
    run_checker(
        mode_change,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    symlink_change = temporary / "committed-symlink-restore"
    symlink_base = committed_candidate(source, symlink_change, facts, overlay)
    symlink_path = "CHANGELOG.md"
    (symlink_change / symlink_path).unlink()
    (symlink_change / symlink_path).symlink_to("scripts/check-ksg-phase-isolation.py")
    commit_exact_paths(
        symlink_change,
        (symlink_path,),
        message="phase isolation forbidden symlink transition",
    )
    restore_symlink = run(
        git_command("checkout", symlink_base, "--", symlink_path),
        cwd=symlink_change,
    )
    require(restore_symlink.returncode == 0, "cannot restore final symlink path")
    commit_exact_paths(
        symlink_change,
        (symlink_path,),
        message="phase isolation exact symlink restoration",
    )
    run_checker(
        symlink_change,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    deletion = temporary / "committed-delete-restore"
    base_commit = committed_candidate(source, deletion, facts, overlay)
    added_path = PORTABILITY_CORRECTIVE_EVIDENCE
    (deletion / added_path).unlink()
    commit_exact_paths(
        deletion,
        (added_path,),
        message="phase isolation deletion negative control",
    )
    restore_path = run(
        git_command("checkout", base_commit, "--", added_path),
        cwd=deletion,
    )
    require(restore_path.returncode == 0, "cannot restore deleted lifecycle path")
    commit_exact_paths(
        deletion,
        (added_path,),
        message="phase isolation deletion restoration",
    )
    run_checker(
        deletion,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1

    protected = temporary / "committed-protected-restore"
    protected_base = committed_candidate(source, protected, facts, overlay)
    protected_path = "crates/pid-core/src/pid2.rs"
    append_bytes(
        protected / protected_path,
        b"\n// transient forbidden history touch\n",
    )
    commit_exact_paths(
        protected,
        (protected_path,),
        message="phase isolation protected touch negative control",
    )
    restore_protected = run(
        git_command("checkout", protected_base, "--", protected_path),
        cwd=protected,
    )
    require(
        restore_protected.returncode == 0,
        "cannot restore protected lifecycle path",
    )
    commit_exact_paths(
        protected,
        (protected_path,),
        message="phase isolation protected restoration",
    )
    run_checker(
        protected,
        expect_success=False,
        expected_fragment="post-anchor history exceeds the bounded commit count",
    )
    tests += 1
    return tests


def run_public_ci_evidence_attacks(root: Path) -> int:
    attacks = 0
    receipt = root / PUBLIC_CI_FAILURE_RECEIPT

    receipt_mutations = (
        (
            "receipt-duplicate-key",
            lambda _root: replace_once(
                receipt,
                b'  "schema": "pid-rs/public-ci-failure-receipt",\n',
                (
                    b'  "schema": "pid-rs/public-ci-failure-receipt",\n'
                    b'  "schema": "pid-rs/public-ci-failure-receipt",\n'
                ),
            ),
            "duplicate JSON key",
        ),
        (
            "receipt-noncanonical-trailing-whitespace",
            lambda _root: append_bytes(receipt, b" \n"),
            "JSON is not sorted two-space ASCII form",
        ),
        (
            "receipt-schema-revision-boolean",
            lambda _root: replace_once(
                receipt,
                b'  "schema_revision": 1,\n',
                b'  "schema_revision": true,\n',
            ),
            "public CI failure receipt identity has the wrong JSON type",
        ),
        (
            "receipt-run-id-drift",
            lambda _root: replace_once(
                receipt,
                b'    "id": 30409192059,\n',
                b'    "id": 30409192058,\n',
            ),
            "public CI failure receipt run value changed at $/id",
        ),
        (
            "receipt-head-tree-drift",
            lambda _root: replace_once(
                receipt,
                b'    "tree": "ada3860eb696c9a5d634728365acdb5958e7c4e6"\n',
                b'    "tree": "0da3860eb696c9a5d634728365acdb5958e7c4e6"\n',
            ),
            "public CI failure receipt head value changed at $/tree",
        ),
        (
            "receipt-success-count-drift",
            lambda _root: replace_once(
                receipt,
                b'    "success_count": 43,\n',
                b'    "success_count": 42,\n',
            ),
            "public CI job counts value changed at $/success_count",
        ),
        (
            "receipt-first-log-digest-drift",
            lambda _root: replace_once(
                receipt,
                (
                    b'          "log_sha256": '
                    b'"4c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10",\n'
                ),
                (
                    b'          "log_sha256": '
                    b'"0c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10",\n'
                ),
            ),
            "public CI failed-job summaries value changed at $/0/failure/log_sha256",
        ),
        (
            "receipt-first-log-size-drift",
            lambda _root: replace_once(
                receipt,
                b'          "log_size_bytes": 108775,\n',
                b'          "log_size_bytes": 108774,\n',
            ),
            "public CI failed-job summaries value changed at $/0/failure/log_size_bytes",
        ),
        (
            "receipt-first-step-number-drift",
            lambda _root: replace_once(
                receipt,
                b'          "step_number": 18\n',
                b'          "step_number": 17\n',
            ),
            "public CI failed-job summaries value changed at $/0/failure/step_number",
        ),
        (
            "receipt-first-job-conclusion-false-green",
            lambda _root: replace_once(
                receipt,
                (
                    b'        "completed_at": "2026-07-28T23:53:12Z",\n'
                    b'        "conclusion": "failure",\n'
                ),
                (
                    b'        "completed_at": "2026-07-28T23:53:12Z",\n'
                    b'        "conclusion": "success",\n'
                ),
            ),
            "public CI failed-job summaries value changed at $/0/conclusion",
        ),
        (
            "receipt-skipped-action-omission",
            lambda _root: replace_once(
                receipt,
                (
                    b"          {\n"
                    b'            "conclusion": "skipped",\n'
                    b'            "name": "Run cargo install cargo-deny --locked '
                    b'--version 0.20.2",\n'
                    b'            "number": 21,\n'
                    b'            "status": "completed"\n'
                    b"          },\n"
                ),
                b"",
            ),
            "public CI skipped Actions steps array length changed",
        ),
        (
            "receipt-skipped-post-action-omission",
            lambda _root: replace_once(
                receipt,
                (
                    b"          },\n"
                    b"          {\n"
                    b'            "conclusion": "skipped",\n'
                    b'            "name": "Post Run actions/setup-python@'
                    b'ece7cb06caefa5fff74198d8649806c4678c61a1",\n'
                    b'            "number": 43,\n'
                    b'            "status": "completed"\n'
                    b"          }\n"
                ),
                b"          }\n",
            ),
            "public CI skipped Actions steps array length changed",
        ),
        (
            "receipt-formal-completed-unreached-swap",
            lambda _root: replace_once(
                receipt,
                (
                    b'          "scripts/check-dependency-colored-sxpid-pdf.sh '
                    b'--cross-toolchain"\n'
                ),
                (
                    b'          "scripts/check-support-change-tolerant-sxpid-pdf.sh '
                    b'--cross-toolchain"\n'
                ),
            ),
            (
                "public CI formal-PDF composite-step credit boundary value changed "
                "at $/completed_intra_step_routes/3"
            ),
        ),
        (
            "receipt-scientific-counterexample-promotion",
            lambda _root: replace_exact_count(
                receipt,
                b'          "scientific_counterexample": false,\n',
                b'          "scientific_counterexample": true,\n',
                expected_count=2,
            ),
            (
                "public CI failed-job summaries value changed at "
                "$/0/failure/scientific_counterexample"
            ),
        ),
        (
            "receipt-ksg-success-drift",
            lambda _root: replace_once(
                receipt,
                (
                    b'      "completed_at": "2026-07-29T00:09:23Z",\n'
                    b'      "conclusion": "success",\n'
                    b'      "id": 90441337099,\n'
                ),
                (
                    b'      "completed_at": "2026-07-29T00:09:23Z",\n'
                    b'      "conclusion": "failure",\n'
                    b'      "id": 90441337099,\n'
                ),
            ),
            "public CI KSG control job value changed at $/conclusion",
        ),
        (
            "receipt-settled-full-ci-false-green",
            lambda _root: replace_once(
                receipt,
                b'    "settled_full_ci": false,\n',
                b'    "settled_full_ci": true,\n',
            ),
            (
                "public CI remediation and no-credit state value changed at "
                "$/settled_full_ci"
            ),
        ),
        (
            "receipt-whole-run-rerun-erasure",
            lambda _root: replace_once(
                receipt,
                b'    "whole_run_rerun_required": true\n',
                b'    "whole_run_rerun_required": false\n',
            ),
            (
                "public CI remediation and no-credit state value changed at "
                "$/whole_run_rerun_required"
            ),
        ),
        (
            "receipt-latent-dependency-relabelled-observed",
            lambda _root: replace_once(
                receipt,
                b"this lake dependency was latent",
                b"this lake dependency was observed",
            ),
            (
                "public CI remediation and no-credit state value changed at "
                "$/formal_pdf_job/1"
            ),
        ),
    )
    for label, mutate, semantic_fragment in receipt_mutations:
        hostile_receipt_repin_attack(
            root,
            label=label,
            mutate=mutate,
            semantic_fragment=semantic_fragment,
        )
        attacks += 1

    baseline_first_rebased_attack(
        root,
        label="memo-parity-sentinel-deletion",
        paths=(CORRECTIVE_EVIDENCE,),
        mutate=lambda candidate: replace_once(
            candidate / CORRECTIVE_EVIDENCE,
            b"PUBLIC_CI_FAILURE_PARITY_BEGIN\n",
            b"PUBLIC_CI_FAILURE_PARITY_REMOVED\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=("public CI corrective memo parity sentinels are not unique"),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="memo-no-go-parity-promotion",
        paths=(CORRECTIVE_EVIDENCE,),
        mutate=lambda candidate: replace_once(
            candidate / CORRECTIVE_EVIDENCE,
            b'"integration_disposition": "NO-GO pending a fresh complete public rerun"',
            b'"integration_disposition": "GO"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "public CI human/machine parity projection value changed at "
            "$/integration_disposition"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "public CI human/machine parity projection value changed at "
            "$/integration_disposition"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="memo-log-digest-drift",
        paths=(CORRECTIVE_EVIDENCE,),
        mutate=lambda candidate: replace_exact_count(
            candidate / CORRECTIVE_EVIDENCE,
            b"4c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10",
            b"0c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10",
            expected_count=2,
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "public CI human/machine parity projection value changed at "
            "$/failed_jobs/0/log_sha256"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "public CI human/machine parity projection value changed at "
            "$/failed_jobs/0/log_sha256"
        ),
    )
    attacks += 1
    return attacks


def _c3_ledger_row(
    value: dict[str, object],
    *,
    bucket: str,
    index: int,
    code: str,
) -> dict[str, object]:
    rows = value.get(bucket)
    require(type(rows) is list, f"C3 ledger bucket is not an array: {bucket}")
    require(0 <= index < len(rows), f"C3 ledger row index is absent: {bucket}/{index}")
    row = rows[index]
    require(type(row) is dict, f"C3 ledger row is not an object: {bucket}/{index}")
    field = (
        "observation_code"
        if bucket == "bounded_positive_observations"
        else "reason_code"
    )
    require(
        row.get(field) == code,
        f"C3 ledger row code changed before mutation: {bucket}/{index}",
    )
    return row


def _mutate_c3_ledger_code(
    value: dict[str, object],
    *,
    bucket: str,
    index: int,
    field: str,
    code: str,
) -> None:
    row = _c3_ledger_row(value, bucket=bucket, index=index, code=code)
    require(row.get(field) == code, "C3 ledger code field changed before mutation")
    row[field] = code + "_FORGED"


def _mutate_c3_ledger_structure(
    value: dict[str, object],
    *,
    control: str,
) -> None:
    positive = value.get("bounded_positive_observations")
    negative = value.get("negative_observations")
    require(
        type(positive) is list and type(negative) is list,
        "C3 ledger structural mutation lacks both row arrays",
    )
    positive_zero = "GEN0_PARSER_NORMAL_OPTIMIZED_BYTE_IDENTICAL"
    if control == "LEDGER_DELETE_POSITIVE_ROW":
        _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=17,
            code="RAW_TRANSPORT_FIVE_FAMILY_STATIC_DESIGN_GO",
        )
        del positive[17]
    elif control == "LEDGER_DELETE_NEGATIVE_ROW":
        _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=45,
            code="LOCAL_LAKE_ROUTING_STALL_AND_ABORTED_ELAN_DOWNLOAD",
        )
        del negative[45]
    elif control == "LEDGER_DUPLICATE_ROW_AND_CODE":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        duplicate = json.loads(
            json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False)
        )
        require(type(duplicate) is dict, "C3 ledger deep row copy changed type")
        positive.insert(1, duplicate)
    elif control == "LEDGER_REORDER_ROWS":
        _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=1,
            code="GEN3_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
        )
        positive[0], positive[1] = positive[1], positive[0]
    elif control == "LEDGER_PROMOTE_CREDIT":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        require(
            row.get("credit") == "superseded_bounded_only", "C3 ledger credit changed"
        )
        row["credit"] = "full"
    elif control == "LEDGER_DRIFT_CANDIDATE_COMMIT":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        require(
            row.get("candidate_commit") == "524a1c6af46698f872dce1a04aa0a281ec025a5e",
            "C3 ledger candidate commit changed",
        )
        row["candidate_commit"] = "024a1c6af46698f872dce1a04aa0a281ec025a5e"
    elif control == "LEDGER_DRIFT_CANDIDATE_TREE":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        require(
            row.get("candidate_tree") == "40d288360b1b36e4276daff0f69361738fb4f029",
            "C3 ledger candidate tree changed",
        )
        row["candidate_tree"] = "00d288360b1b36e4276daff0f69361738fb4f029"
    elif control == "LEDGER_DRIFT_SESSION_ID":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=5,
            code="SESSION_56745_ENTRY_ISOLATION_18_CASES_COMPLETE",
        )
        require(row.get("session_id") == 56745, "C3 ledger session id changed")
        row["session_id"] = 56746
    elif control == "LEDGER_DRIFT_RESULT":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=23,
            code="TREE_FBCC_CHECKPOINT_FFBD_INVALIDATED_AFTER_WRITER",
        )
        require(
            row.get("result") == "invalidated_after_writer_update",
            "C3 ledger result changed",
        )
        row["result"] = "accepted"
    elif control == "LEDGER_DRIFT_EXIT_CODE":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=1,
            code="GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED",
        )
        require(row.get("exit_code") == 1, "C3 ledger exit code changed")
        row["exit_code"] = 0
    elif control == "LEDGER_DRIFT_STDOUT_SHA256":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        require(
            row.get("stdout_sha256")
            == "51fbdafb0a24e5763b2842f558bd5dde3bb4aed110a53ed5a5dea26d81ccaea8",
            "C3 ledger stdout digest changed",
        )
        row["stdout_sha256"] = (
            "01fbdafb0a24e5763b2842f558bd5dde3bb4aed110a53ed5a5dea26d81ccaea8"
        )
    elif control == "LEDGER_DRIFT_STDERR_SHA256":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=1,
            code="GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED",
        )
        require(
            row.get("stderr_sha256")
            == "7829719b5026a2130c0cbf20ce40c14ed0c3f5f7af91a1b0212a3b55aeef72a9",
            "C3 ledger stderr digest changed",
        )
        row["stderr_sha256"] = (
            "0829719b5026a2130c0cbf20ce40c14ed0c3f5f7af91a1b0212a3b55aeef72a9"
        )
    elif control == "LEDGER_DRIFT_STDOUT_SIZE":
        row = _c3_ledger_row(
            value,
            bucket="bounded_positive_observations",
            index=0,
            code=positive_zero,
        )
        require(row.get("stdout_size_bytes") == 7063, "C3 ledger stdout size changed")
        row["stdout_size_bytes"] = 7064
    elif control == "LEDGER_DRIFT_STDERR_SIZE":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=1,
            code="GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED",
        )
        require(row.get("stderr_size_bytes") == 99, "C3 ledger stderr size changed")
        row["stderr_size_bytes"] = 100
    elif control == "LEDGER_FLIP_TERMINAL_RECEIPT_STATE":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=6,
            code="GEN4_INDEPENDENT_OPTIMIZED_FOCUSED_RUN_ABORTED_FOR_SERIALIZATION",
        )
        require(
            row.get("terminal_receipt_retained") is False,
            "C3 ledger terminal receipt state changed",
        )
        row["terminal_receipt_retained"] = True
    elif control == "LEDGER_FLIP_RESTORATION_OR_CLEANUP_STATE":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=20,
            code="SESSION_54874_MEMO_ANCHOR_CARDINALITY_STALE",
        )
        require(
            row.get("restoration_green_replay_reached") is False,
            "C3 ledger restoration state changed",
        )
        row["restoration_green_replay_reached"] = True
    elif control == "LEDGER_DRIFT_PARENT":
        require(
            value.get("parent") == "8b792bc143fff2d84f2d8e7817d1de7850741223",
            "C3 ledger parent changed",
        )
        value["parent"] = "0b792bc143fff2d84f2d8e7817d1de7850741223"
    elif control == "LEDGER_DRIFT_SCHEMA":
        require(
            value.get("schema") == "pid-rs/c3-precommit-review-ledger",
            "C3 ledger schema changed",
        )
        value["schema"] = "pid-rs/c3-precommit-review-ledger-forged"
    elif control == "LEDGER_DRIFT_SCHEMA_REVISION_TYPE":
        require(
            type(value.get("schema_revision")) is int
            and value.get("schema_revision") == 2,
            "C3 ledger schema revision changed",
        )
        value["schema_revision"] = True
    elif control == "LEDGER_OMIT_SESSION_INVENTORY_ENTRY":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=35,
            code="REVIEW_LEDGER_COMPLETENESS_AND_TYPED_VALIDATION_GAP",
        )
        inventory = row.get("missing_named_session_ids")
        require(
            type(inventory) is list and inventory.count(8070) == 1,
            "C3 ledger named-session inventory changed",
        )
        inventory.remove(8070)
    elif control == "LEDGER_OMIT_OBJECT_INVENTORY_ENTRY":
        row = _c3_ledger_row(
            value,
            bucket="negative_observations",
            index=35,
            code="REVIEW_LEDGER_COMPLETENESS_AND_TYPED_VALIDATION_GAP",
        )
        inventory = row.get("missing_object_ids")
        object_id = "c896731c74534417e2de8636d6faa58ab2a54f70"
        require(
            type(inventory) is list and inventory.count(object_id) == 1,
            "C3 ledger object inventory changed",
        )
        inventory.remove(object_id)
    else:
        raise SelfTestError(f"unknown C3 ledger structural control: {control}")


def run_c3_review_ledger_nested_controls(root: Path) -> int:
    """Run exactly 64 field and 21 structural ledger executions."""

    positive_codes = (
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
    negative_codes = (
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
    row_specs = tuple(
        ("bounded_positive_observations", index, "observation_code", code)
        for index, code in enumerate(positive_codes)
    ) + tuple(
        ("negative_observations", index, "reason_code", code)
        for index, code in enumerate(negative_codes)
    )
    require(
        len(positive_codes) == 18
        and len(negative_codes) == 46
        and len(row_specs) == 64,
        "C3 review-ledger code-mutant specification changed",
    )
    execution_receipts: list[C3NestedMemoAttackExecutionReceipt] = []
    expected_receipt_projection: list[
        tuple[
            str,
            str,
            tuple[str, str | None, bytes | None, bytes | None, str | None],
        ]
    ] = []
    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    for bucket, index, field, code in row_specs:
        detail = (
            f"C3 precommit review ledger value changed at $/{bucket}/{index}/{field}"
        )
        attack_label = (
            f"portability-memo-review-ledger-code-{len(execution_receipts) + 1:02d}"
        )
        expected_projection = _c3_nested_expected_projection(
            label=attack_label,
            expected_detail=detail,
            inner_projection_constant=(
                "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256"
            ),
            begin=C3_REVIEW_BEGIN_BYTES,
            end=C3_REVIEW_END_BYTES,
            object_label="C3 precommit review ledger",
        )
        expected_receipt_projection.append(expected_projection)
        receipt = _run_c3_nested_memo_attack(
            root,
            label=attack_label,
            mutate=lambda _root, bucket=bucket, index=index, field=field, code=code: (
                mutate_canonical_memo_object(
                    memo,
                    begin=C3_REVIEW_BEGIN_BYTES,
                    end=C3_REVIEW_END_BYTES,
                    label="C3 precommit review ledger",
                    mutate=lambda value: _mutate_c3_ledger_code(
                        value,
                        bucket=bucket,
                        index=index,
                        field=field,
                        code=code,
                    ),
                )
            ),
            expected_detail=detail,
            inner_projection_constant=(
                "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256"
            ),
            begin=C3_REVIEW_BEGIN_BYTES,
            end=C3_REVIEW_END_BYTES,
            object_label="C3 precommit review ledger",
        )
        execution_receipts.append(
            _validate_c3_nested_memo_attack_execution_receipt(
                receipt,
                expected_projection=expected_projection,
            )
        )

    structural_specs = (
        (
            "LEDGER_DELETE_POSITIVE_ROW",
            "C3 precommit review ledger array length changed at $/bounded_positive_observations",
        ),
        (
            "LEDGER_DELETE_NEGATIVE_ROW",
            "C3 precommit review ledger array length changed at $/negative_observations",
        ),
        (
            "LEDGER_DUPLICATE_ROW_AND_CODE",
            "C3 precommit review ledger array length changed at $/bounded_positive_observations",
        ),
        (
            "LEDGER_REORDER_ROWS",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/0/candidate_commit",
        ),
        (
            "LEDGER_PROMOTE_CREDIT",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/0/credit",
        ),
        (
            "LEDGER_DRIFT_CANDIDATE_COMMIT",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/0/candidate_commit",
        ),
        (
            "LEDGER_DRIFT_CANDIDATE_TREE",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/0/candidate_tree",
        ),
        (
            "LEDGER_DRIFT_SESSION_ID",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/5/session_id",
        ),
        (
            "LEDGER_DRIFT_RESULT",
            "C3 precommit review ledger value changed at $/negative_observations/23/result",
        ),
        (
            "LEDGER_DRIFT_EXIT_CODE",
            "C3 precommit review ledger value changed at $/negative_observations/1/exit_code",
        ),
        (
            "LEDGER_DRIFT_STDOUT_SHA256",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/0/stdout_sha256",
        ),
        (
            "LEDGER_DRIFT_STDERR_SHA256",
            "C3 precommit review ledger value changed at $/negative_observations/1/stderr_sha256",
        ),
        (
            "LEDGER_DRIFT_STDOUT_SIZE",
            "C3 precommit review ledger value changed at $/bounded_positive_observations/0/stdout_size_bytes",
        ),
        (
            "LEDGER_DRIFT_STDERR_SIZE",
            "C3 precommit review ledger value changed at $/negative_observations/1/stderr_size_bytes",
        ),
        (
            "LEDGER_FLIP_TERMINAL_RECEIPT_STATE",
            "C3 precommit review ledger value changed at $/negative_observations/6/terminal_receipt_retained",
        ),
        (
            "LEDGER_FLIP_RESTORATION_OR_CLEANUP_STATE",
            "C3 precommit review ledger value changed at $/negative_observations/20/restoration_green_replay_reached",
        ),
        ("LEDGER_DRIFT_PARENT", "C3 precommit review ledger value changed at $/parent"),
        ("LEDGER_DRIFT_SCHEMA", "C3 precommit review ledger value changed at $/schema"),
        (
            "LEDGER_DRIFT_SCHEMA_REVISION_TYPE",
            "C3 precommit review ledger has the wrong JSON type at $/schema_revision: expected int, observed bool",
        ),
        (
            "LEDGER_OMIT_SESSION_INVENTORY_ENTRY",
            "C3 precommit review ledger array length changed at $/negative_observations/35/missing_named_session_ids",
        ),
        (
            "LEDGER_OMIT_OBJECT_INVENTORY_ENTRY",
            "C3 precommit review ledger array length changed at $/negative_observations/35/missing_object_ids",
        ),
    )
    require(len(structural_specs) == 21, "C3 ledger structural specification changed")
    for control, detail in structural_specs:
        attack_label = f"portability-memo-review-ledger-{control.lower()}"
        expected_projection = _c3_nested_expected_projection(
            label=attack_label,
            expected_detail=detail,
            inner_projection_constant=(
                "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256"
            ),
            begin=C3_REVIEW_BEGIN_BYTES,
            end=C3_REVIEW_END_BYTES,
            object_label="C3 precommit review ledger",
        )
        expected_receipt_projection.append(expected_projection)
        receipt = _run_c3_nested_memo_attack(
            root,
            label=attack_label,
            mutate=lambda _root, control=control: mutate_canonical_memo_object(
                memo,
                begin=C3_REVIEW_BEGIN_BYTES,
                end=C3_REVIEW_END_BYTES,
                label="C3 precommit review ledger",
                mutate=lambda value: _mutate_c3_ledger_structure(
                    value,
                    control=control,
                ),
            ),
            expected_detail=detail,
            inner_projection_constant=(
                "EXPECTED_C3_PRECOMMIT_REVIEW_PROJECTION_SHA256"
            ),
            begin=C3_REVIEW_BEGIN_BYTES,
            end=C3_REVIEW_END_BYTES,
            object_label="C3 precommit review ledger",
        )
        execution_receipts.append(
            _validate_c3_nested_memo_attack_execution_receipt(
                receipt,
                expected_projection=expected_projection,
            )
        )
    validated_projection = _validated_c3_nested_execution_projection(
        execution_receipts,
        expected_projection=tuple(expected_receipt_projection),
        context="C3 review-ledger",
    )
    require(
        len(validated_projection) == C3_REVIEW_LEDGER_EXECUTION_COUNT,
        "C3 review-ledger validated execution projection count changed",
    )
    return len(validated_projection)


def _c3_parity_row(
    value: dict[str, object],
    *,
    bucket: str,
    index: int,
) -> dict[str, object]:
    rows = value.get(bucket)
    require(type(rows) is list, f"C3 parity bucket is not an array: {bucket}")
    require(0 <= index < len(rows), f"C3 parity row index is absent: {bucket}/{index}")
    row = rows[index]
    require(type(row) is dict, f"C3 parity row is not an object: {bucket}/{index}")
    return row


def _mutate_c3_local_artifact_parity(
    value: dict[str, object],
    *,
    operation: str,
) -> None:
    candidate_zero = _c3_parity_row(
        value,
        bucket="candidate_repository_artifacts",
        index=0,
    )
    if operation == "schema_revision_type":
        require(
            type(value.get("schema_revision")) is int
            and value.get("schema_revision") == 1,
            "C3 parity schema revision changed",
        )
        value["schema_revision"] = True
    elif operation == "direct_path":
        require(
            candidate_zero.get("path")
            == "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
            "C3 parity direct path changed",
        )
        candidate_zero["path"] = (
            "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json"
        )
    elif operation == "direct_sha":
        require(
            candidate_zero.get("sha256")
            == "63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6",
            "C3 parity direct digest changed",
        )
        candidate_zero["sha256"] = (
            "03c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6"
        )
    elif operation == "direct_size":
        require(
            candidate_zero.get("size_bytes") == 3421, "C3 parity direct size changed"
        )
        candidate_zero["size_bytes"] = 3422
    elif operation == "mutation_sha":
        row = _c3_parity_row(value, bucket="candidate_repository_artifacts", index=1)
        require(
            row.get("sha256")
            == "b644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9",
            "C3 parity mutation digest changed",
        )
        row["sha256"] = (
            "0644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9"
        )
    elif operation == "mutation_size":
        row = _c3_parity_row(value, bucket="candidate_repository_artifacts", index=1)
        require(row.get("size_bytes") == 13428, "C3 parity mutation size changed")
        row["size_bytes"] = 13429
    elif operation == "current_pdf_sha":
        row = _c3_parity_row(value, bucket="candidate_repository_artifacts", index=2)
        require(
            row.get("sha256")
            == "ee715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b",
            "C3 parity current PDF digest changed",
        )
        row["sha256"] = (
            "0e715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b"
        )
    elif operation == "current_pdf_size":
        row = _c3_parity_row(value, bucket="candidate_repository_artifacts", index=2)
        require(row.get("size_bytes") == 358668, "C3 parity current PDF size changed")
        row["size_bytes"] = 358669
    elif operation == "parser_normal_sha":
        row = _c3_parity_row(value, bucket="local_review_artifacts", index=0)
        require(
            row.get("sha256")
            == "b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
            "C3 parity normal parser digest changed",
        )
        row["sha256"] = (
            "008bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6"
        )
    elif operation == "parser_optimized_sha":
        row = _c3_parity_row(value, bucket="local_review_artifacts", index=1)
        require(
            row.get("sha256")
            == "b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
            "C3 parity optimized parser digest changed",
        )
        row["sha256"] = (
            "008bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6"
        )
    elif operation == "parser_size":
        row = _c3_parity_row(value, bucket="local_review_artifacts", index=0)
        require(row.get("size_bytes") == 12166, "C3 parity parser size changed")
        row["size_bytes"] = 12167
    elif operation == "false_mode_equality":
        require(
            value.get("normal_optimized_parser_bytes_equal") is True,
            "C3 parity mode-equality state changed",
        )
        value["normal_optimized_parser_bytes_equal"] = False
    elif operation == "cross_object_sha_swap":
        local_zero = _c3_parity_row(value, bucket="local_review_artifacts", index=0)
        direct_sha = candidate_zero.get("sha256")
        local_sha = local_zero.get("sha256")
        require(
            direct_sha
            == "63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6"
            and local_sha
            == "b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
            "C3 parity cross-object digests changed",
        )
        candidate_zero["sha256"], local_zero["sha256"] = local_sha, direct_sha
    elif operation == "parent_commit":
        row = _c3_parity_row(value, bucket="parent_repository_artifacts", index=0)
        require(
            row.get("commit") == "8b792bc143fff2d84f2d8e7817d1de7850741223",
            "C3 parity parent artifact commit changed",
        )
        row["commit"] = "0b792bc143fff2d84f2d8e7817d1de7850741223"
    elif operation == "parent_path":
        row = _c3_parity_row(value, bucket="parent_repository_artifacts", index=0)
        require(
            row.get("path")
            == "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
            "C3 parity parent artifact path changed",
        )
        row["path"] = "output/pdf/foundational-shared-exclusions-pid-audit-forged.pdf"
    elif operation == "parent_pdf_sha":
        row = _c3_parity_row(value, bucket="parent_repository_artifacts", index=0)
        require(
            row.get("sha256")
            == "5904626fe91f4d606a09f0b842fcecad102d7585e6654a16e2bbb952ed0882df",
            "C3 parity parent PDF digest changed",
        )
        row["sha256"] = (
            "0904626fe91f4d606a09f0b842fcecad102d7585e6654a16e2bbb952ed0882df"
        )
    elif operation == "parent_pdf_size":
        row = _c3_parity_row(value, bucket="parent_repository_artifacts", index=0)
        require(row.get("size_bytes") == 358292, "C3 parity parent PDF size changed")
        row["size_bytes"] = 358293
    elif operation == "local_credit_promotion":
        row = _c3_parity_row(value, bucket="local_review_artifacts", index=0)
        require(
            row.get("retention_class") == "local_review_artifact",
            "C3 parity local retention class changed",
        )
        row["retention_class"] = "candidate_repository_artifact"
    elif operation == "forbidden_self_reference":
        require("memo_sha256" not in value, "C3 parity self-reference already exists")
        value["memo_sha256"] = "0" * 64
    else:
        raise SelfTestError(f"unknown C3 local-artifact-parity operation: {operation}")


def run_c3_local_artifact_parity_nested_controls(root: Path) -> tuple[int, int]:
    """Run exactly nineteen parity families flattened to twenty-one executions."""

    families = (
        (
            "PARITY_SENTINEL_DELETE",
            (
                (
                    "sentinel_delete",
                    "C3 local artifact parity: fenced JSON sentinels are not unique",
                    False,
                ),
            ),
        ),
        (
            "PARITY_BLOCK_DUPLICATE",
            (
                (
                    "block_duplicate",
                    "C3 local artifact parity: fenced JSON sentinels are not unique",
                    False,
                ),
            ),
        ),
        (
            "PARITY_SCHEMA_REVISION_TYPE_DRIFT",
            (
                (
                    "schema_revision_type",
                    "C3 local artifact parity has the wrong JSON type at $/schema_revision: expected int, observed bool",
                    True,
                ),
            ),
        ),
        (
            "PARITY_DIRECT_PATH_SUBSTITUTE",
            (
                (
                    "direct_path",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/0/path",
                    True,
                ),
            ),
        ),
        (
            "PARITY_DIRECT_SHA_DRIFT",
            (
                (
                    "direct_sha",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/0/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_DIRECT_SIZE_DRIFT",
            (
                (
                    "direct_size",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/0/size_bytes",
                    True,
                ),
            ),
        ),
        (
            "PARITY_MUTATION_SHA_DRIFT",
            (
                (
                    "mutation_sha",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/1/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_MUTATION_SIZE_DRIFT",
            (
                (
                    "mutation_size",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/1/size_bytes",
                    True,
                ),
            ),
        ),
        (
            "PARITY_CURRENT_PDF_SHA_DRIFT",
            (
                (
                    "current_pdf_sha",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/2/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_CURRENT_PDF_SIZE_DRIFT",
            (
                (
                    "current_pdf_size",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/2/size_bytes",
                    True,
                ),
            ),
        ),
        (
            "PARITY_PARSER_NORMAL_SHA_DRIFT",
            (
                (
                    "parser_normal_sha",
                    "C3 local artifact parity value changed at $/local_review_artifacts/0/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_PARSER_OPTIMIZED_SHA_DRIFT",
            (
                (
                    "parser_optimized_sha",
                    "C3 local artifact parity value changed at $/local_review_artifacts/1/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_PARSER_SIZE_DRIFT",
            (
                (
                    "parser_size",
                    "C3 local artifact parity value changed at $/local_review_artifacts/0/size_bytes",
                    True,
                ),
            ),
        ),
        (
            "PARITY_FALSE_MODE_EQUALITY_OR_CROSS_OBJECT_SWAP",
            (
                (
                    "false_mode_equality",
                    "C3 local artifact parity value changed at $/normal_optimized_parser_bytes_equal",
                    True,
                ),
                (
                    "cross_object_sha_swap",
                    "C3 local artifact parity value changed at $/candidate_repository_artifacts/0/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_PARENT_COMMIT_OR_PATH_SUBSTITUTE",
            (
                (
                    "parent_commit",
                    "C3 local artifact parity value changed at $/parent_repository_artifacts/0/commit",
                    True,
                ),
                (
                    "parent_path",
                    "C3 local artifact parity value changed at $/parent_repository_artifacts/0/path",
                    True,
                ),
            ),
        ),
        (
            "PARITY_PARENT_PDF_SHA_DRIFT",
            (
                (
                    "parent_pdf_sha",
                    "C3 local artifact parity value changed at $/parent_repository_artifacts/0/sha256",
                    True,
                ),
            ),
        ),
        (
            "PARITY_PARENT_PDF_SIZE_DRIFT",
            (
                (
                    "parent_pdf_size",
                    "C3 local artifact parity value changed at $/parent_repository_artifacts/0/size_bytes",
                    True,
                ),
            ),
        ),
        (
            "PARITY_LOCAL_ARTIFACT_CREDIT_PROMOTION",
            (
                (
                    "local_credit_promotion",
                    "C3 local artifact parity value changed at $/local_review_artifacts/0/retention_class",
                    True,
                ),
            ),
        ),
        (
            "PARITY_FORBIDDEN_SELF_REFERENCE_FIELD",
            (
                (
                    "forbidden_self_reference",
                    "C3 local artifact parity contains forbidden self-reference key at $.memo_sha256",
                    True,
                ),
            ),
        ),
    )
    require(
        len(families) == C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT
        and tuple(len(variants) for _family, variants in families)
        == (1,) * 13 + (2, 2) + (1,) * 4,
        "C3 local-artifact-parity family structure changed",
    )
    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    family_receipt_groups: list[
        tuple[str, tuple[C3NestedMemoAttackExecutionReceipt, ...]]
    ] = []
    family_expected_projection_groups: list[
        tuple[
            str,
            tuple[
                tuple[
                    str,
                    str,
                    tuple[
                        str,
                        str | None,
                        bytes | None,
                        bytes | None,
                        str | None,
                    ],
                ],
                ...,
            ],
        ]
    ] = []
    execution_receipts: list[C3NestedMemoAttackExecutionReceipt] = []
    expected_receipt_projection: list[
        tuple[
            str,
            str,
            tuple[str, str | None, bytes | None, bytes | None, str | None],
        ]
    ] = []

    def parity_mutation(operation: str) -> Callable[[Path], object]:
        def mutate(_root: Path) -> object:
            if operation == "sentinel_delete":
                return replace_once(
                    memo,
                    C3_LOCAL_ARTIFACT_BEGIN_BYTES,
                    b"C3_LOCAL_ARTIFACT_PARITY_REMOVED\n",
                )
            if operation == "block_duplicate":
                return duplicate_complete_c3_fenced_block(
                    memo,
                    begin=C3_LOCAL_ARTIFACT_BEGIN_BYTES,
                    end=C3_LOCAL_ARTIFACT_END_BYTES,
                    label="C3 local artifact parity",
                )
            return mutate_canonical_memo_object(
                memo,
                begin=C3_LOCAL_ARTIFACT_BEGIN_BYTES,
                end=C3_LOCAL_ARTIFACT_END_BYTES,
                label="C3 local artifact parity",
                mutate=lambda value: _mutate_c3_local_artifact_parity(
                    value,
                    operation=operation,
                ),
            )

        return mutate

    for family, variants in families:
        variant_receipts: list[C3NestedMemoAttackExecutionReceipt] = []
        variant_expected_projection: list[
            tuple[
                str,
                str,
                tuple[str, str | None, bytes | None, bytes | None, str | None],
            ]
        ] = []
        for operation, detail, inner_repin in variants:
            attack_label = (
                f"portability-memo-local-artifact-{family.lower()}-"
                f"{len(execution_receipts) + 1:02d}"
            )
            expected_projection = _c3_nested_expected_projection(
                label=attack_label,
                expected_detail=detail,
                inner_projection_constant=(
                    "EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256"
                    if inner_repin
                    else None
                ),
                begin=C3_LOCAL_ARTIFACT_BEGIN_BYTES if inner_repin else None,
                end=C3_LOCAL_ARTIFACT_END_BYTES if inner_repin else None,
                object_label="C3 local artifact parity" if inner_repin else None,
            )
            expected_receipt_projection.append(expected_projection)
            variant_expected_projection.append(expected_projection)
            receipt = _run_c3_nested_memo_attack(
                root,
                label=attack_label,
                mutate=parity_mutation(operation),
                expected_detail=detail,
                inner_projection_constant=(
                    "EXPECTED_C3_LOCAL_ARTIFACT_PARITY_PROJECTION_SHA256"
                    if inner_repin
                    else None
                ),
                begin=C3_LOCAL_ARTIFACT_BEGIN_BYTES if inner_repin else None,
                end=C3_LOCAL_ARTIFACT_END_BYTES if inner_repin else None,
                object_label="C3 local artifact parity" if inner_repin else None,
            )
            validated_receipt = _validate_c3_nested_memo_attack_execution_receipt(
                receipt,
                expected_projection=expected_projection,
            )
            execution_receipts.append(validated_receipt)
            variant_receipts.append(validated_receipt)
        require(
            len(variant_receipts) == len(variants),
            f"C3 local-artifact-parity family receipt inventory changed: {family}",
        )
        family_receipt_groups.append((family, tuple(variant_receipts)))
        family_expected_projection_groups.append(
            (family, tuple(variant_expected_projection))
        )
    validated_execution_projection = _validated_c3_nested_execution_projection(
        execution_receipts,
        expected_projection=tuple(expected_receipt_projection),
        context="C3 local-artifact-parity",
    )
    observed_family_receipt_projection = tuple(
        (
            family,
            tuple(
                _c3_nested_expected_projection(
                    label=receipt.label,
                    expected_detail=receipt.expected_detail,
                    inner_projection_constant=receipt.inner_projection_constant,
                    begin=receipt.begin,
                    end=receipt.end,
                    object_label=receipt.object_label,
                )
                for receipt in receipts
            ),
        )
        for family, receipts in family_receipt_groups
    )
    require(
        observed_family_receipt_projection == tuple(family_expected_projection_groups)
        and len(observed_family_receipt_projection)
        == C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT
        and len(validated_execution_projection)
        == C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT,
        "C3 local-artifact-parity nested inventory changed",
    )
    return (
        len(observed_family_receipt_projection),
        len(validated_execution_projection),
    )


def run_public_ci_portability_evidence_attacks(
    root: Path,
) -> tuple[int, int, int, int]:
    attacks = 0
    review_ledger_nested_executions = 0
    local_artifact_parity_nested_families = 0
    local_artifact_parity_nested_executions = 0
    receipt = root / PUBLIC_CI_PORTABILITY_RECEIPT

    receipt_mutations = (
        (
            "portability-receipt-duplicate-key",
            lambda _root: replace_once(
                receipt,
                b'  "schema": "pid-rs/public-ci-failure-receipt",\n',
                (
                    b'  "schema": "pid-rs/public-ci-failure-receipt",\n'
                    b'  "schema": "pid-rs/public-ci-failure-receipt",\n'
                ),
            ),
            "duplicate JSON key",
        ),
        (
            "portability-receipt-schema-revision-boolean",
            lambda _root: replace_once(
                receipt,
                b'  "schema_revision": 2,\n',
                b'  "schema_revision": true,\n',
            ),
            "C2 portability failure receipt identity has the wrong JSON type",
        ),
        (
            "portability-receipt-run-id-drift",
            lambda _root: replace_once(
                receipt,
                b'    "id": 30431352389,\n',
                b'    "id": 30431352388,\n',
            ),
            "C2 portability failure receipt run value changed at $/id",
        ),
        (
            "portability-receipt-head-tree-drift",
            lambda _root: replace_once(
                receipt,
                b'    "tree": "8e247b9a6c46fd6266fe4fc02fbe9c3142268215"\n',
                b'    "tree": "0e247b9a6c46fd6266fe4fc02fbe9c3142268215"\n',
            ),
            "C2 portability failure receipt head value changed at $/tree",
        ),
        (
            "portability-receipt-success-count-drift",
            lambda _root: replace_once(
                receipt,
                b'    "success_count": 44,\n',
                b'    "success_count": 43,\n',
            ),
            "C2 portability failure counts value changed at $/success_count",
        ),
        (
            "portability-receipt-classification-drift",
            lambda _root: replace_once(
                receipt,
                b'          "classification": "evidence_portability",\n',
                b'          "classification": "theorem_failure",\n',
            ),
            "C2 portability failure diagnosis value changed at $/classification",
        ),
        (
            "portability-receipt-control-flow-inference-erasure",
            lambda _root: replace_once(
                receipt,
                b'            "checker_returned_success_before_comparison": true,\n',
                b'            "checker_returned_success_before_comparison": false,\n',
            ),
            (
                "C2 portability failure diagnosis value changed at "
                "$/control_flow_diagnosis/checker_returned_success_before_comparison"
            ),
        ),
        (
            "portability-receipt-theorem-failure-promotion",
            lambda _root: replace_once(
                receipt,
                b'          "theorem_failure": false,\n',
                b'          "theorem_failure": true,\n',
            ),
            "C2 portability failure diagnosis value changed at $/theorem_failure",
        ),
        (
            "portability-receipt-scientific-counterexample-promotion",
            lambda _root: replace_once(
                receipt,
                b'          "scientific_counterexample": false,\n',
                b'          "scientific_counterexample": true,\n',
            ),
            (
                "C2 portability failure diagnosis value changed at "
                "$/scientific_counterexample"
            ),
        ),
        (
            "portability-receipt-log-digest-drift",
            lambda _root: replace_once(
                receipt,
                (
                    b'          "log_sha256": '
                    b'"06c612a30cd02dc9f9a3957b47cdf96cd2d2e75ff08cf050272bcb518d49b234",\n'
                ),
                (
                    b'          "log_sha256": '
                    b'"16c612a30cd02dc9f9a3957b47cdf96cd2d2e75ff08cf050272bcb518d49b234",\n'
                ),
            ),
            "C2 portability failure diagnosis value changed at $/log_sha256",
        ),
        (
            "portability-receipt-diagnosed-component-drift",
            lambda _root: replace_once(
                receipt,
                b'            "diagnosed_component": "lean_version platform token",\n',
                b'            "diagnosed_component": "kernel theorem",\n',
            ),
            (
                "C2 portability failure diagnosis value changed at "
                "$/cross_host_receipts/diagnosed_component"
            ),
        ),
        (
            "portability-receipt-linux-control-job-drift",
            lambda _root: replace_once(
                receipt,
                (
                    b'              "job_id": 90509073386,\n'
                    b'              "lean_version": "Lean (version 4.32.0, '
                ),
                (
                    b'              "job_id": 90509073385,\n'
                    b'              "lean_version": "Lean (version 4.32.0, '
                ),
            ),
            (
                "C2 portability failure diagnosis value changed at "
                "$/cross_host_receipts/hosted_linux_observation_control/job_id"
            ),
        ),
        (
            "portability-receipt-linux-control-boundary-overclaim",
            lambda _root: replace_once(
                receipt,
                (
                    b"This exact Linux version line is retained from a different "
                    b"same-run checker and supports the platform diagnosis. It is "
                    b"not the deleted descriptor-checker stdout or temporary JSON "
                    b"from the failed formal-PDF job."
                ),
                b"This is the directly retained failed-job descriptor output.",
            ),
            (
                "C2 portability failure diagnosis value changed at "
                "$/cross_host_receipts/hosted_linux_observation_control/boundary"
            ),
        ),
        (
            "portability-receipt-reconstruction-overclaim",
            lambda _root: replace_once(
                receipt,
                (
                    b"Deterministically reconstructed from the exact descriptor "
                    b"checker, committed receipt, and different same-run Linux "
                    b"observation control; the failed job's stdout and temporary "
                    b"JSON were deleted and are not claimed as directly retained."
                ),
                b"Directly retained from the failed job.",
            ),
            (
                "C2 portability failure diagnosis value changed at "
                "$/cross_host_receipts/hosted_ubuntu_reconstruction/retention"
            ),
        ),
        (
            "portability-receipt-paper-route-credit-promotion",
            lambda _root: replace_once(
                receipt,
                (
                    b'          "scripts/check-mathematical-workflow-pdf.sh '
                    b'--cross-toolchain",\n'
                ),
                (
                    b'          "scripts/check-foundational-sxpid-audit-pdf.sh '
                    b'--cross-toolchain",\n'
                ),
            ),
            "C2 portability formal-PDF route credit value changed at $/unreached/0",
        ),
        (
            "portability-receipt-skipped-action-omission",
            lambda _root: replace_once(
                receipt,
                (
                    b'        "skipped_actions_steps": [\n'
                    b"          {\n"
                    b'            "conclusion": "skipped",\n'
                    b'            "name": "Post Run actions/cache@'
                    b'27d5ce7f107fe9357f9df03efb73ab90386fccae",\n'
                    b'            "number": 15,\n'
                    b'            "status": "completed"\n'
                    b"          }\n"
                    b"        ],\n"
                ),
                b'        "skipped_actions_steps": [],\n',
            ),
            "C2 portability skipped Actions steps array length changed",
        ),
        (
            "portability-receipt-codeql-run-false-failure",
            lambda _root: replace_once(
                receipt,
                (
                    b'        "attempt": 1,\n'
                    b'        "conclusion": "success",\n'
                    b'        "created_at": "2026-07-29T07:21:24Z",\n'
                ),
                (
                    b'        "attempt": 1,\n'
                    b'        "conclusion": "failure",\n'
                    b'        "created_at": "2026-07-29T07:21:24Z",\n'
                ),
            ),
            "C2 CodeQL execution identity value changed at $/run/conclusion",
        ),
        (
            "portability-receipt-codeql-false-clean",
            lambda _root: replace_once(
                receipt,
                (
                    b'      "open_projected_on_head_count": 85,\n'
                    b'      "open_projection": {\n'
                ),
                (
                    b'      "open_projected_on_head_count": 0,\n'
                    b'      "open_projection": {\n'
                ),
            ),
            (
                "C2 CodeQL open-alert snapshot value changed at "
                "$/open_projected_on_head_count"
            ),
        ),
        (
            "portability-receipt-codeql-open-count-drift",
            lambda _root: replace_once(
                receipt,
                b'      "open_count": 85,\n',
                b'      "open_count": 84,\n',
            ),
            "C2 CodeQL open-alert snapshot value changed at $/open_count",
        ),
        (
            "portability-receipt-codeql-false-adjudication",
            lambda _root: replace_once(
                receipt,
                b'      "security_adjudication": "not_adjudicated"\n',
                b'      "security_adjudication": "passed"\n',
            ),
            ("C2 CodeQL open-alert snapshot value changed at $/security_adjudication"),
        ),
        (
            "portability-receipt-hostile-probe-count-drift",
            lambda _root: replace_once(
                receipt,
                b'      "hostile_version_probes_required": 19,\n',
                b'      "hostile_version_probes_required": 18,\n',
            ),
            (
                "C2 portability remediation and no-credit state value changed at "
                "$/chosen_correction/hostile_version_probes_required"
            ),
        ),
        (
            "portability-receipt-settled-full-ci-false-green",
            lambda _root: replace_once(
                receipt,
                b'    "settled_full_ci": false,\n',
                b'    "settled_full_ci": true,\n',
            ),
            (
                "C2 portability remediation and no-credit state value changed at "
                "$/settled_full_ci"
            ),
        ),
        (
            "portability-receipt-wrapper-only-alternative-selected",
            lambda _root: replace_once(
                receipt,
                (
                    b"That approach would preserve two comparison semantics for "
                    b"the same evidence schema and move trust into a shell "
                    b"comparator with a larger bypass surface."
                ),
                b"That approach is equivalent and selected.",
            ),
            (
                "C2 portability remediation and no-credit state value changed at "
                "$/rejected_alternative/reason"
            ),
        ),
    )
    for label, mutate, semantic_fragment in receipt_mutations:
        hostile_portability_receipt_repin_attack(
            root,
            label=label,
            mutate=mutate,
            semantic_fragment=semantic_fragment,
        )
        attacks += 1

    memo = root / PORTABILITY_CORRECTIVE_EVIDENCE
    memo_mutations = (
        (
            "portability-memo-parity-sentinel-deletion",
            lambda _root: replace_once(
                memo,
                b"PUBLIC_CI_PORTABILITY_FAILURE_PARITY_BEGIN\n",
                b"PUBLIC_CI_PORTABILITY_FAILURE_PARITY_REMOVED\n",
            ),
            "C2 portability memo parity sentinels are not unique",
        ),
        (
            "portability-memo-no-go-promotion",
            lambda _root: replace_once(
                memo,
                (
                    b'"integration_disposition": "NO-GO pending a fresh complete '
                    b'public rerun"'
                ),
                b'"integration_disposition": "GO"',
            ),
            (
                "C2 portability human/machine parity projection value changed at "
                "$/integration_disposition"
            ),
        ),
        (
            "portability-memo-codeql-false-clean",
            lambda _root: replace_once_after(
                memo,
                b"PUBLIC_CI_PORTABILITY_FAILURE_PARITY_BEGIN\n",
                b'      "scan_clean": false,\n',
                b'      "scan_clean": true,\n',
            ),
            (
                "C2 portability human/machine parity projection value changed at "
                "$/codeql/open_alert_snapshot/scan_clean"
            ),
        ),
        (
            "portability-memo-rerun-requirement-erasure",
            lambda _root: replace_once(
                memo,
                (
                    b"A fresh\nhosted C3 run must then complete all CI jobs "
                    b"successfully."
                ),
                b"C3 is complete without a hosted rerun.",
            ),
            "memo lost correction-status or security boundaries",
        ),
        (
            "portability-memo-rejected-alternative-reversal",
            lambda _root: replace_once(
                memo,
                b"That route was not selected.",
                b"That route was selected.",
            ),
            "memo lost correction-status or security boundaries",
        ),
        (
            "portability-memo-orchestration-prevention-erasure",
            lambda _root: replace_once(
                memo,
                (b"Monitor only process IDs and process state from\noutside the clone"),
                b"Monitor the clone with Git status",
            ),
            "memo lost the orchestration-contamination no-credit boundary",
        ),
        (
            "portability-memo-stale-optimized-credit",
            lambda _root: replace_once(
                memo,
                (b"also receives no credit, regardless of its terminal\nresult"),
                b"is accepted regardless of its prior-byte snapshot",
            ),
            "memo lost the orchestration-contamination no-credit boundary",
        ),
        (
            "portability-memo-top-level-loader-overclaim",
            lambda _root: replace_once(
                memo,
                b"not an atomic loader guarantee.",
                b"an atomic loader guarantee.",
            ),
            "C3 portability memo lost the top-level loader premise",
        ),
        (
            "portability-memo-home-launcher-negative-erasure",
            lambda _root: replace_once(
                memo,
                (b"retained `HOME` reaches and can influence selected launcher state."),
                b"`HOME` cannot influence selected launcher state.",
            ),
            "C3 portability memo lost the HOME/launcher negative boundary",
        ),
        (
            "portability-memo-unsettled-count-credit-promotion",
            lambda _root: replace_once(
                memo,
                (
                    b"contracted aggregate is 351 cases; credit\n"
                    b"requires settled final-byte normal and optimized replays:"
                ),
                (
                    b"credited aggregate is 351 cases;\n"
                    b"settled final-byte replays are optional:"
                ),
            ),
            "C3 portability memo falsely credits unsettled hostile counts",
        ),
        (
            "portability-memo-timeout-evidence-promotion",
            lambda _root: replace_once(
                memo,
                b"not evidence that the suite passed or a weakening of any case.",
                b"evidence that the suite passed without running every case.",
            ),
            "C3 portability memo lost the timeout nonclaim",
        ),
    )
    for label, mutate, semantic_fragment in memo_mutations:
        semantic_expectation = (
            caller_held_exact_failure_expectation(semantic_fragment)
            if label
            in {
                "portability-memo-no-go-promotion",
                "portability-memo-codeql-false-clean",
            }
            else None
        )
        hostile_portability_memo_repin_attack(
            root,
            label=label,
            mutate=mutate,
            semantic_fragment=semantic_fragment,
            semantic_expectation=semantic_expectation,
        )
        # The frozen stale-evidence case owns independently executed nested
        # diagnostics. Its contracted family cardinality remains one case;
        # nested mutation executions are not contracted cases.
        if label == "portability-memo-stale-optimized-credit":
            hostile_portability_memo_repin_attack(
                root,
                label="portability-memo-parser-receipt-digest-drift",
                mutate=lambda _root: replace_once_between(
                    memo,
                    (
                        b"Parser-only normal and optimized outputs are each `12166` "
                        b"bytes, byte-identical,\nand SHA-256\n"
                    ),
                    b".\nAn independent review",
                    b"b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
                    b"008bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
                ),
                semantic_fragment=(
                    "C3 portability memo parser-only digest differs from executed "
                    "parser receipt"
                ),
            )
            inventory_mutations = (
                (
                    "require-call-count",
                    b"freezes 383 `require` call sites",
                    b"freezes 382 `require` call sites",
                ),
                (
                    "direct-error-count",
                    b"call sites, 43 direct\nmessage-producing",
                    b"call sites, 42 direct\nmessage-producing",
                ),
                (
                    "distinct-template-count",
                    b"and 408 distinct full-message\ntemplates.",
                    b"and 407 distinct full-message\ntemplates.",
                ),
                (
                    "nonclaim-template-count",
                    b"prove that all 408\nregular-expression",
                    b"prove that all 407\nregular-expression",
                ),
            )
            for inventory_label, old, new in inventory_mutations:
                hostile_portability_memo_repin_attack(
                    root,
                    label=(
                        f"portability-memo-failure-inventory-{inventory_label}-drift"
                    ),
                    mutate=lambda _root, old=old, new=new: replace_once(
                        memo,
                        old,
                        new,
                    ),
                    semantic_fragment=(
                        "C2 portability memo lost correction-status or security "
                        "boundaries"
                    ),
                )
            review_ledger_nested_executions = run_c3_review_ledger_nested_controls(root)
            require(
                review_ledger_nested_executions == C3_REVIEW_LEDGER_EXECUTION_COUNT,
                "C3 review-ledger nested execution inventory changed",
            )
            (
                local_artifact_parity_nested_families,
                local_artifact_parity_nested_executions,
            ) = run_c3_local_artifact_parity_nested_controls(root)
            require(
                local_artifact_parity_nested_families
                == C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT
                and local_artifact_parity_nested_executions
                == C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT,
                "C3 local-artifact-parity nested inventory changed",
            )
        attacks += 1
    require(
        review_ledger_nested_executions == C3_REVIEW_LEDGER_EXECUTION_COUNT
        and local_artifact_parity_nested_families
        == C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT
        and local_artifact_parity_nested_executions
        == C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT,
        "C3 portability nested execution accounting did not complete",
    )
    return (
        attacks,
        review_ledger_nested_executions,
        local_artifact_parity_nested_families,
        local_artifact_parity_nested_executions,
    )


def _mutate_descriptor_v4_artifact(
    value: dict[str, object],
    *,
    operation: str,
) -> None:
    """Apply one field-addressed descriptor-v4 evidence mutation."""

    def row(bucket: str, index: int) -> dict[str, object]:
        items = value.get(bucket)
        require(type(items) is list, f"descriptor-v4 bucket is not an array: {bucket}")
        require(
            0 <= index < len(items),
            f"descriptor-v4 row index is absent: {bucket}/{index}",
        )
        item = items[index]
        require(
            type(item) is dict, f"descriptor-v4 row is not an object: {bucket}/{index}"
        )
        return item

    if operation == "direct_process_stdin_transport":
        require(
            value.get("process_stdin_transport") == "devnull_eof_no_parent_input",
            "descriptor-v4 direct stdin transport changed",
        )
        value["process_stdin_transport"] = "inherited_parent_input"
    elif operation == "stdin_count":
        require(
            type(value.get("process_stdin_isolation_subcontrols_passed")) is int
            and value.get("process_stdin_isolation_subcontrols_passed") == 1,
            "descriptor-v4 stdin subcontrol count changed",
        )
        value["process_stdin_isolation_subcontrols_passed"] = 0
    elif operation == "order_count":
        require(
            type(value.get("raw_process_transport_order_subcontrols_rejected")) is int
            and value.get("raw_process_transport_order_subcontrols_rejected") == 1,
            "descriptor-v4 order subcontrol count changed",
        )
        value["raw_process_transport_order_subcontrols_rejected"] = 0
    elif operation == "stdin_inventory_identity":
        item = row("process_stdin_isolation_subcontrols", 0)
        require(
            item.get("probe_sha256")
            == "65174fc6fd7bfb6c9ab0fcaa7ee9038726a6597084b34f17dd7c42939e1ada75",
            "descriptor-v4 stdin subcontrol probe changed",
        )
        item["probe_sha256"] = (
            "05174fc6fd7bfb6c9ab0fcaa7ee9038726a6597084b34f17dd7c42939e1ada75"
        )
    elif operation == "order_inventory_identity":
        item = row("raw_process_transport_order_subcontrols", 0)
        require(
            item.get("probe_sha256")
            == "c30ef33a2390f923bc204c5d03cb2a10dc46c6bdbb41b97cddb93a26114909cd",
            "descriptor-v4 order subcontrol probe changed",
        )
        item["probe_sha256"] = (
            "030ef33a2390f923bc204c5d03cb2a10dc46c6bdbb41b97cddb93a26114909cd"
        )
    elif operation == "mixed_stream_reason":
        item = row("raw_process_transport_order_subcontrols", 0)
        require(
            item.get("rejection_reason")
            == "Lean process raw stdout is not strict UTF-8",
            "descriptor-v4 mixed-stream rejection reason changed",
        )
        item["rejection_reason"] = "Lean process raw stderr contains a carriage return"
    elif operation == "direct_identity_boundary":
        boundary = value.get("lean_executable_identity_boundary")
        old = "child stdin is /dev/null and cannot consume parent input"
        require(
            type(boundary) is str and boundary.count(old) == 1,
            "descriptor-v4 executable-identity boundary anchor changed",
        )
        value["lean_executable_identity_boundary"] = boundary.replace(
            old,
            "child stdin may consume parent input",
            1,
        )
    elif operation == "direct_snapshot_boundary":
        boundary = value.get("input_snapshot_boundary")
        old = "Regular input bytes are accumulated without an explicit size ceiling."
        require(
            type(boundary) is str and boundary.count(old) == 1,
            "descriptor-v4 input-snapshot boundary anchor changed",
        )
        value["input_snapshot_boundary"] = boundary.replace(
            old,
            "Regular input bytes are fully bounded.",
            1,
        )
    elif operation == "mutation_boundary":
        boundary = value.get("boundary")
        old = "A live parent-fd-0 contamination probe proves child stdin is DEVNULL."
        require(
            type(boundary) is str and boundary.count(old) == 1,
            "descriptor-v4 mutation boundary anchor changed",
        )
        value["boundary"] = boundary.replace(
            old,
            "Child stdin may be inherited.",
            1,
        )
    elif operation.startswith("raw_reason_"):
        index = int(operation.removeprefix("raw_reason_"))
        expected_reasons = (
            "Lean process raw stdout contains a carriage return",
            "Lean process raw stderr contains a carriage return",
            "Lean process raw stdout is not strict UTF-8",
            "Lean process raw stderr is not strict UTF-8",
            "Lean process raw stdout contains a carriage return",
        )
        item = row("raw_process_transport_hostile_cases", index)
        require(
            item.get("rejection_reason") == expected_reasons[index],
            f"descriptor-v4 raw rejection reason changed at index {index}",
        )
        item["rejection_reason"] = expected_reasons[index] + " FORGED"
    else:
        raise SelfTestError(f"unknown descriptor-v4 artifact operation: {operation}")


def run_lean_portability_attacks(root: Path) -> tuple[int, int, int]:
    attacks = 0
    raw_transport_subcontrols = 0
    descriptor_v4_execution_receipts: list[DescriptorV4ExecutionReceipt] = []
    checker_relative = "scripts/check-lean-descriptor-factorization.py"
    self_test_relative = LEAN_DESCRIPTOR_SELF_TEST_RELATIVE
    evidence_relative = (
        "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json"
    )
    mutations_relative = (
        "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json"
    )

    evidence_attacks = (
        (
            "lean-portability-evidence-schema-rollback",
            evidence_relative,
            lambda candidate: replace_once(
                candidate / evidence_relative,
                b'"schema":"pid-rs/lean-descriptor-factorization-check/v4"',
                b'"schema":"pid-rs/lean-descriptor-factorization-check/v3"',
            ),
            (
                "descriptor-factorization Lean portable evidence value changed "
                "at $/schema"
            ),
        ),
        (
            "lean-portability-evidence-raw-platform-leak",
            evidence_relative,
            lambda candidate: replace_once(
                candidate / evidence_relative,
                b'"lean_platform_handling":"parsed_and_validated_but_not_serialized"',
                (b'"lean_platform_handling":"serialized_arm64-apple-darwin24.6.0"'),
            ),
            (
                "descriptor-factorization Lean portable evidence value changed "
                "at $/lean_platform_handling"
            ),
        ),
        (
            "lean-portability-evidence-commit-drift",
            evidence_relative,
            lambda candidate: replace_once(
                candidate / evidence_relative,
                b"8c9756b28d64dab099da31a4c09229a9e6a2ef35",
                b"9c9756b28d64dab099da31a4c09229a9e6a2ef35",
            ),
            (
                "descriptor-factorization Lean portable evidence value changed "
                "at $/lean_executable_identity/commit"
            ),
        ),
        (
            "lean-portability-evidence-toolchain-digest-drift",
            evidence_relative,
            lambda candidate: replace_once(
                candidate / evidence_relative,
                b'"lean_toolchain_sha256":"2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e"',
                b'"lean_toolchain_sha256":"0773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e"',
            ),
            (
                "descriptor-factorization Lean portable evidence value changed "
                "at $/lean_toolchain_sha256"
            ),
        ),
        (
            "lean-portability-scientific-count-conflation",
            mutations_relative,
            lambda candidate: replace_once(
                candidate / mutations_relative,
                b'"scientific_proof_mutations_killed":3',
                b'"scientific_proof_mutations_killed":5',
            ),
            (
                "descriptor-factorization mutation evidence identity value "
                "changed at $/scientific_proof_mutations_killed"
            ),
        ),
        (
            "lean-portability-control-count-drift",
            mutations_relative,
            lambda candidate: replace_once(
                candidate / mutations_relative,
                b'"lean_version_portability_controls_accepted":2',
                b'"lean_version_portability_controls_accepted":3',
            ),
            (
                "descriptor-factorization parser/mutation parity field "
                "lean_version_portability_controls_accepted value changed at $"
            ),
        ),
        (
            "lean-portability-hostile-count-drift",
            mutations_relative,
            lambda candidate: replace_once(
                candidate / mutations_relative,
                b'"lean_version_hostile_cases_rejected":19',
                b'"lean_version_hostile_cases_rejected":18',
            ),
            (
                "descriptor-factorization parser/mutation parity field "
                "lean_version_hostile_cases_rejected value changed at $"
            ),
        ),
        (
            "lean-portability-countermodel-count-drift",
            mutations_relative,
            lambda candidate: replace_once(
                candidate / mutations_relative,
                b'"semantic_countermodels_kernel_checked":3',
                b'"semantic_countermodels_kernel_checked":2',
            ),
            (
                "descriptor-factorization mutation evidence identity value "
                "changed at $/semantic_countermodels_kernel_checked"
            ),
        ),
        (
            "lean-portability-retained-negative-count-drift",
            mutations_relative,
            lambda candidate: replace_once(
                candidate / mutations_relative,
                b'"retained_negative_controls_demonstrated":4',
                b'"retained_negative_controls_demonstrated":3',
            ),
            (
                "descriptor-factorization mutation evidence identity value changed "
                "at $/retained_negative_controls_demonstrated"
            ),
        ),
    )
    descriptor_v4_artifact_subcontrols = (
        (
            "lean-portability-v4-direct-stdin-transport-subcontrol",
            evidence_relative,
            "direct_process_stdin_transport",
            (
                "descriptor-factorization Lean portable evidence value changed "
                "at $/process_stdin_transport"
            ),
        ),
        (
            "lean-portability-v4-stdin-count-subcontrol",
            mutations_relative,
            "stdin_count",
            (
                "descriptor-factorization mutation evidence identity value changed "
                "at $/process_stdin_isolation_subcontrols_passed"
            ),
        ),
        (
            "lean-portability-v4-order-count-subcontrol",
            mutations_relative,
            "order_count",
            (
                "descriptor-factorization mutation evidence identity value changed "
                "at $/raw_process_transport_order_subcontrols_rejected"
            ),
        ),
        (
            "lean-portability-v4-stdin-inventory-subcontrol",
            mutations_relative,
            "stdin_inventory_identity",
            (
                "descriptor-factorization parser/mutation parity field "
                "process_stdin_isolation_subcontrols value changed at "
                "$/0/probe_sha256"
            ),
        ),
        (
            "lean-portability-v4-order-inventory-subcontrol",
            mutations_relative,
            "order_inventory_identity",
            (
                "descriptor-factorization parser/mutation parity field "
                "raw_process_transport_order_subcontrols value changed at "
                "$/0/probe_sha256"
            ),
        ),
        (
            "lean-portability-v4-mixed-stream-reason-subcontrol",
            mutations_relative,
            "mixed_stream_reason",
            (
                "descriptor-factorization parser/mutation parity field "
                "raw_process_transport_order_subcontrols value changed at "
                "$/0/rejection_reason"
            ),
        ),
        (
            "lean-portability-v4-executable-identity-boundary-subcontrol",
            evidence_relative,
            "direct_identity_boundary",
            (
                "descriptor-factorization Lean portable evidence value changed at "
                "$/lean_executable_identity_boundary"
            ),
        ),
        (
            "lean-portability-v4-input-snapshot-boundary-subcontrol",
            evidence_relative,
            "direct_snapshot_boundary",
            (
                "descriptor-factorization Lean portable evidence value changed at "
                "$/input_snapshot_boundary"
            ),
        ),
        (
            "lean-portability-v4-mutation-boundary-subcontrol",
            mutations_relative,
            "mutation_boundary",
            (
                "descriptor-factorization mutation evidence identity value changed "
                "at $/boundary"
            ),
        ),
        *tuple(
            (
                f"lean-portability-v4-raw-reason-{index}-subcontrol",
                mutations_relative,
                f"raw_reason_{index}",
                (
                    "descriptor-factorization parser/mutation parity field "
                    "raw_process_transport_hostile_cases value changed at "
                    f"$/{index}/rejection_reason"
                ),
            )
            for index in range(5)
        ),
    )
    require(
        len(descriptor_v4_artifact_subcontrols)
        == DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT,
        "descriptor-v4 artifact nested subcontrol inventory changed",
    )
    for label, relative, mutate, semantic_fragment in evidence_attacks:
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(relative,),
            mutate=mutate,
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment=semantic_fragment,
            semantic_expectation=caller_held_exact_failure_expectation(
                semantic_fragment
            ),
        )
        if label == "lean-portability-retained-negative-count-drift":
            # This is an independently executed subcontrol of the counted evidence
            # case above; it does not create an eighteenth family case.
            baseline_first_rebased_attack(
                root,
                label="lean-portability-raw-transport-count-drift-subcontrol",
                paths=(mutations_relative,),
                mutate=lambda candidate: replace_once(
                    candidate / mutations_relative,
                    b'"raw_process_transport_hostile_cases_rejected":5',
                    b'"raw_process_transport_hostile_cases_rejected":4',
                ),
                first_fragment="changed-byte projection digest mismatch",
                semantic_fragment=(
                    "descriptor-factorization mutation evidence identity value "
                    "changed at $/raw_process_transport_hostile_cases_rejected"
                ),
                semantic_expectation=caller_held_exact_failure_expectation(
                    "descriptor-factorization mutation evidence identity value "
                    "changed at $/raw_process_transport_hostile_cases_rejected"
                ),
            )
            raw_transport_subcontrols += 1
            for (
                sublabel,
                subrelative,
                operation,
                subdetail,
            ) in descriptor_v4_artifact_subcontrols:
                attack_receipt = baseline_first_rebased_attack(
                    root,
                    label=sublabel,
                    paths=(subrelative,),
                    mutate=lambda candidate, subrelative=subrelative, operation=operation, sublabel=sublabel: (
                        mutate_canonical_compact_json_object(
                            candidate / subrelative,
                            label=sublabel,
                            mutate=lambda value: _mutate_descriptor_v4_artifact(
                                value,
                                operation=operation,
                            ),
                        )
                    ),
                    first_fragment="changed-byte projection digest mismatch",
                    semantic_fragment=subdetail,
                    semantic_expectation=caller_held_exact_failure_expectation(
                        subdetail
                    ),
                )
                _record_descriptor_v4_nested_execution(
                    descriptor_v4_execution_receipts,
                    attack_receipt=attack_receipt,
                )
            parser_boundary_detail = (
                "Lean portability parser replay identity value changed at $/boundary"
            )
            attack_receipt = baseline_first_rebased_attack(
                root,
                label="lean-portability-v4-parser-boundary-subcontrol",
                paths=(CHECKER_RELATIVE,),
                mutate=lambda candidate: replace_once(
                    candidate / CHECKER_RELATIVE,
                    (
                        b"environment scrubbing, DEVNULL child stdin, raw-byte "
                        b"subprocess capture"
                    ),
                    (
                        b"environment scrubbing, inherited child stdin, raw-byte "
                        b"subprocess capture"
                    ),
                ),
                first_fragment=parser_boundary_detail,
                semantic_fragment=parser_boundary_detail,
                first_expectation=caller_held_exact_failure_expectation(
                    parser_boundary_detail
                ),
                semantic_expectation=caller_held_exact_failure_expectation(
                    parser_boundary_detail
                ),
            )
            _record_descriptor_v4_nested_execution(
                descriptor_v4_execution_receipts,
                attack_receipt=attack_receipt,
            )
            parser_pin_detail = (
                "C3 portability memo parser-only digest differs from executed "
                "parser receipt"
            )
            attack_receipt = baseline_first_rebased_attack(
                root,
                label="lean-portability-v4-parser-receipt-pin-subcontrol",
                paths=(CHECKER_RELATIVE,),
                mutate=lambda candidate: replace_once(
                    candidate / CHECKER_RELATIVE,
                    b"b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
                    b"008bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
                ),
                first_fragment=parser_pin_detail,
                semantic_fragment=parser_pin_detail,
                first_expectation=caller_held_exact_failure_expectation(
                    parser_pin_detail
                ),
                semantic_expectation=caller_held_exact_failure_expectation(
                    parser_pin_detail
                ),
            )
            _record_descriptor_v4_nested_execution(
                descriptor_v4_execution_receipts,
                attack_receipt=attack_receipt,
            )
        attacks += 1

    def repin_descriptor_checker_source(candidate: Path) -> None:
        checker_path = candidate / checker_relative
        self_test_path = candidate / self_test_relative
        digest_matches = re.findall(
            rb'EXPECTED_CHECKER_SOURCE_SHA256 = \(\n    "([0-9a-f]{64})"\n\)',
            self_test_path.read_bytes(),
        )
        require(
            len(digest_matches) == 1
            and digest_matches[0]
            == b"d2eda588a204966e3e5b3f33f70b5a263bfc49c3100e444d4fc27c3e428c8cf6",
            "descriptor self-test checker digest pin is absent or ambiguous",
        )
        replace_once(
            self_test_path,
            digest_matches[0],
            hashlib.sha256(checker_path.read_bytes()).hexdigest().encode("ascii"),
        )

    def mutate_descriptor_checker_and_repin(
        candidate: Path,
        mutate_checker: Callable[[Path], object],
    ) -> None:
        require(
            callable(mutate_checker),
            "descriptor checker coordinated mutation is not callable",
        )
        mutate_checker(candidate)
        repin_descriptor_checker_source(candidate)

    def reverse_raw_transport_validation_order(candidate: Path) -> None:
        replace_once(
            candidate / checker_relative,
            (
                b"        require(\n"
                b'            b"\\r" not in raw,\n'
                b'            f"Lean process raw {stream_name} contains a carriage return",\n'
                b"        )\n"
                b"        try:\n"
                b'            decoded[stream_name] = raw.decode("utf-8", errors="strict")\n'
                b"        except UnicodeDecodeError as error:\n"
                b"            raise LeanDescriptorFactorizationError(\n"
                b'                f"Lean process raw {stream_name} is not strict UTF-8"\n'
                b"            ) from error\n"
            ),
            (
                b"        try:\n"
                b'            decoded[stream_name] = raw.decode("utf-8", errors="strict")\n'
                b"        except UnicodeDecodeError as error:\n"
                b"            raise LeanDescriptorFactorizationError(\n"
                b'                f"Lean process raw {stream_name} is not strict UTF-8"\n'
                b"            ) from error\n"
                b"        require(\n"
                b'            b"\\r" not in raw,\n'
                b'            f"Lean process raw {stream_name} contains a carriage return",\n'
                b"        )\n"
            ),
        )

    def reverse_completed_buffer_loop_order(candidate: Path) -> None:
        replace_once(
            candidate / checker_relative,
            (
                b'    for stream_name, raw in (("stdout", probe.stdout), '
                b'("stderr", probe.stderr)):\n'
            ),
            (
                b'    for stream_name, raw in (("stderr", probe.stderr), '
                b'("stdout", probe.stdout)):\n'
            ),
        )

    descriptor_v4_source_subcontrols = (
        (
            "lean-portability-v4-devnull-stdin-source-subcontrol",
            (checker_relative, self_test_relative),
            "devnull_stdin_source",
            lambda candidate: replace_once(
                candidate / checker_relative,
                b"            stdin=subprocess.DEVNULL,\n",
                b"            stdin=None,\n",
            ),
            "Lean portability descriptor-pinned child source model changed",
        ),
        (
            "lean-portability-v4-completed-buffer-loop-order-subcontrol",
            (checker_relative, self_test_relative),
            "completed_buffer_loop_order",
            reverse_completed_buffer_loop_order,
            "Lean portability descriptor-pinned child source model changed",
        ),
    )
    require(
        len(descriptor_v4_source_subcontrols) == DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT,
        "descriptor-v4 source nested subcontrol inventory changed",
    )

    raw_transport_source_subcontrols = (
        (
            "lean-portability-raw-transport-text-mode-subcontrol",
            (checker_relative, self_test_relative),
            lambda candidate: replace_once(
                candidate / checker_relative,
                b"            stderr=subprocess.PIPE,\n            check=False,\n",
                (
                    b"            stderr=subprocess.PIPE,\n"
                    b"            text=True,\n"
                    b"            check=False,\n"
                ),
            ),
            "Lean portability descriptor-pinned child source model changed",
            caller_held_exact_failure_expectation(
                "Lean portability descriptor-pinned child source model changed"
            ),
        ),
        (
            "lean-portability-raw-cr-rejection-removed-subcontrol",
            (checker_relative, self_test_relative),
            lambda candidate: replace_once(
                candidate / checker_relative,
                b'            b"\\r" not in raw,\n',
                b"            True,\n",
            ),
            "Lean portability descriptor-pinned child source model changed",
            caller_held_exact_failure_expectation(
                "Lean portability descriptor-pinned child source model changed"
            ),
        ),
        (
            "lean-portability-strict-utf8-weakened-subcontrol",
            (checker_relative, self_test_relative),
            lambda candidate: replace_once(
                candidate / checker_relative,
                b'raw.decode("utf-8", errors="strict")',
                b'raw.decode("utf-8", errors="replace")',
            ),
            "Lean portability descriptor-pinned child source model changed",
            caller_held_exact_failure_expectation(
                "Lean portability descriptor-pinned child source model changed"
            ),
        ),
        (
            "lean-portability-cr-before-utf8-order-reversed-subcontrol",
            (checker_relative, self_test_relative),
            reverse_raw_transport_validation_order,
            "Lean portability descriptor-pinned child source model changed",
            caller_held_exact_failure_expectation(
                "Lean portability descriptor-pinned child source model changed"
            ),
        ),
    )

    checker_attacks = (
        (
            "lean-portability-parser-stderr-bypass",
            checker_relative,
            lambda candidate: replace_once(
                candidate / checker_relative,
                b'        probe.stderr == "",\n',
                b"        True,\n",
            ),
            "normal Lean portability parser controls failed",
        ),
        (
            "lean-portability-parser-prefix-match",
            checker_relative,
            lambda candidate: replace_once(
                candidate / checker_relative,
                b"matched = LEAN_VERSION_LINE.fullmatch(line)\n",
                b"matched = LEAN_VERSION_LINE.match(line)\n",
            ),
            "normal Lean portability parser controls failed",
        ),
        (
            "lean-portability-parser-platform-grammar-weakened",
            checker_relative,
            lambda candidate: replace_once(
                candidate / checker_relative,
                b"(?:-[A-Za-z0-9_.+]+){2,}",
                b"(?:-[A-Za-z0-9_.+]+){1,}",
            ),
            "normal Lean portability parser controls failed",
        ),
        (
            "lean-portability-checker-assert-injection",
            checker_relative,
            lambda candidate: replace_once(
                candidate / checker_relative,
                b"def main() -> int:\n",
                b"def main() -> int:\n    assert True\n",
            ),
            "Lean portability source contains optimization-removable assert",
        ),
        (
            "lean-portability-descriptor-fchdir-bypass",
            checker_relative,
            lambda candidate: replace_once(
                candidate / checker_relative,
                b"            os.fchdir(descriptor)\n",
                b"            os.chdir(inputs.execution_project)\n",
            ),
            "Lean portability descriptor-pinned child source model changed",
        ),
        (
            "lean-portability-terminal-version-replay-weakened",
            checker_relative,
            lambda candidate: replace_once(
                candidate / checker_relative,
                b'    replay = _run_lean_process(inputs, ["--version"], timeout=60)\n',
                b"    replay = _run_lean_process(inputs, [], timeout=60)\n",
            ),
            "Lean portability terminal version-probe/replay ordering changed",
        ),
        (
            "lean-portability-self-test-hostile-inventory-reduced",
            self_test_relative,
            lambda candidate: (
                replace_once(
                    candidate / self_test_relative,
                    (
                        b"        (\n"
                        b'            "missing_closing_delimiter",\n'
                        b"            version_probe(LINUX_VERSION_OUTPUT.replace("
                        b'")\\n", "\\n", 1)),\n'
                        b"        ),\n"
                    ),
                    b"",
                ),
                replace_once(
                    candidate / self_test_relative,
                    (
                        b'        "missing_closing_delimiter": (\n'
                        b'            "unexpected Lean version output: \'Lean '
                        b'(version 4.32.0, "\n'
                        b'            "x86_64-unknown-linux-gnu, commit "\n'
                        b'            "8c9756b28d64dab099da31a4c09229a9e6a2ef35, '
                        b'Release\\\\n\'"\n'
                        b"        ),\n"
                    ),
                    b"",
                ),
                replace_once(
                    candidate / self_test_relative,
                    b"        len(hostile_results) == 19,\n",
                    b"        len(hostile_results) == 18,\n",
                ),
                replace_once(
                    candidate / self_test_relative,
                    b"        len(set(all_probe_hashes)) == 21,\n",
                    b"        len(set(all_probe_hashes)) == 20,\n",
                ),
                # Pierce only the live digest layer with the independently
                # derived 11,868-byte mutant receipt. The historical/global
                # b08... receipt and its publication memo remain unchanged.
                replace_once(
                    candidate / CHECKER_RELATIVE,
                    (
                        b"        hashlib.sha256(normal_raw).hexdigest()\n"
                        b"        == "
                        b"EXPECTED_LEAN_PORTABILITY_PARSER_RECEIPT_SHA256,\n"
                    ),
                    (
                        b"        hashlib.sha256(normal_raw).hexdigest()\n"
                        b'        == "533e7ef11149b3366bd0f51d09e4a617'
                        b'f1ca8136e93a5d4f7f5a7af43cd6a025",\n'
                    ),
                ),
            ),
            (
                "Lean portability parser replay identity value changed at "
                "$/lean_version_hostile_cases_rejected"
            ),
        ),
        (
            "lean-portability-self-test-assert-injection",
            self_test_relative,
            lambda candidate: replace_once(
                candidate / self_test_relative,
                b"def main() -> int:\n",
                b"def main() -> int:\n    assert True\n",
            ),
            "Lean portability source contains optimization-removable assert",
        ),
    )
    exact_parser_failure_details = {
        "lean-portability-parser-stderr-bypass": (
            "normal Lean portability parser controls failed: Lean descriptor-"
            "factorization self-test failed: hostile Lean version probe survived: "
            "unexpected_stderr"
        ),
        "lean-portability-parser-prefix-match": (
            "normal Lean portability parser controls failed: Lean descriptor-"
            "factorization self-test failed: hostile Lean version probe survived: "
            "trailing_payload"
        ),
        "lean-portability-parser-platform-grammar-weakened": (
            "normal Lean portability parser controls failed: Lean descriptor-"
            "factorization self-test failed: hostile Lean version probe survived: "
            "platform_with_too_few_components"
        ),
    }
    for label, relative, mutate, semantic_fragment in checker_attacks:
        require(
            relative in {checker_relative, self_test_relative},
            "Lean portability checker attack has an unknown source path",
        )
        attack_paths = (
            (CHECKER_RELATIVE, self_test_relative)
            if label == "lean-portability-self-test-hostile-inventory-reduced"
            else (
                (checker_relative, self_test_relative)
                if relative == checker_relative
                else (self_test_relative,)
            )
        )
        attack_mutate = (
            (
                lambda candidate, mutate=mutate: (
                    mutate_descriptor_checker_and_repin(candidate, mutate)
                )
            )
            if relative == checker_relative
            else mutate
        )
        if label in exact_parser_failure_details:
            semantic_detail = exact_parser_failure_details[label]
        elif (
            semantic_fragment
            == "Lean portability source contains optimization-removable assert"
        ):
            semantic_detail = (
                "Lean portability source contains optimization-removable assert: "
                f"{relative}"
            )
        else:
            semantic_detail = semantic_fragment
        semantic_expectation = (
            caller_held_exact_failure_expectation(semantic_detail)
            if label in exact_parser_failure_details
            else (
                caller_held_exact_failure_expectation(semantic_detail)
                if (
                    semantic_fragment
                    == "Lean portability source contains optimization-removable assert"
                    or label == "lean-portability-self-test-hostile-inventory-reduced"
                )
                else None
            )
        )
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=attack_paths,
            mutate=attack_mutate,
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment=semantic_detail,
            semantic_expectation=semantic_expectation,
        )
        if label == "lean-portability-self-test-assert-injection":
            for (
                sublabel,
                subpaths,
                suboperation,
                submutate,
                subdetail,
            ) in descriptor_v4_source_subcontrols:
                attack_receipt = baseline_first_rebased_attack(
                    root,
                    label=sublabel,
                    paths=subpaths,
                    mutate=lambda candidate, submutate=submutate: (
                        mutate_descriptor_checker_and_repin(
                            candidate,
                            submutate,
                        )
                    ),
                    first_fragment="changed-byte projection digest mismatch",
                    semantic_fragment=subdetail,
                    semantic_expectation=caller_held_exact_failure_expectation(
                        subdetail
                    ),
                )
                require(
                    subpaths == (checker_relative, self_test_relative),
                    "descriptor-v4 source subcontrol path inventory changed",
                )
                _record_descriptor_v4_nested_execution(
                    descriptor_v4_execution_receipts,
                    attack_receipt=attack_receipt,
                )
            # These five independently executed source/fixture checks are
            # subcontrols of this counted checker case; the evidence-count check
            # above is the sixth. They do not create additional family cases.
            for (
                sublabel,
                subpaths,
                submutate,
                subfragment,
                subexpectation,
            ) in raw_transport_source_subcontrols:
                baseline_first_rebased_attack(
                    root,
                    label=sublabel,
                    paths=subpaths,
                    mutate=lambda candidate, submutate=submutate: (
                        mutate_descriptor_checker_and_repin(
                            candidate,
                            submutate,
                        )
                    ),
                    first_fragment="changed-byte projection digest mismatch",
                    semantic_fragment=subfragment,
                    semantic_expectation=subexpectation,
                )
                raw_transport_subcontrols += 1
            baseline_first_rebased_attack(
                root,
                label="lean-portability-observed-child-bytes-binding-subcontrol",
                paths=(self_test_relative,),
                mutate=lambda candidate: replace_once(
                    candidate / self_test_relative,
                    (
                        b"8c9756b28d64dab099da31a4c09229a9e6a2ef35, "
                        b"Release)\\\\r\\\\n' ;;\\n"
                    ),
                    (
                        b"8c9756b28d64dab099da31a4c09229a9e6a2ef35, "
                        b"Release)forged\\\\r\\\\n' ;;\\n"
                    ),
                ),
                first_fragment="changed-byte projection digest mismatch",
                semantic_fragment=(
                    "normal Lean portability parser controls failed: Lean descriptor-"
                    "factorization self-test failed: raw Lean transport child bytes "
                    "differ from fixture: "
                    "raw_subprocess_crlf_stdout_before_decode"
                ),
                semantic_expectation=caller_held_exact_failure_expectation(
                    "normal Lean portability parser controls failed: Lean descriptor-"
                    "factorization self-test failed: raw Lean transport child bytes "
                    "differ from fixture: raw_subprocess_crlf_stdout_before_decode"
                ),
            )
            raw_transport_subcontrols += 1
            require(
                raw_transport_subcontrols == PHASE_LEAN_RAW_TRANSPORT_SUBCONTROL_COUNT,
                "phase Lean raw-transport subcontrol inventory changed",
            )
        attacks += 1
    descriptor_v4_projection = _validated_descriptor_v4_execution_projection(
        descriptor_v4_execution_receipts
    )
    descriptor_v4_artifact_executions = sum(
        control[0] == "artifact" for control in descriptor_v4_projection
    )
    descriptor_v4_parser_executions = sum(
        control[0] == "parser" for control in descriptor_v4_projection
    )
    descriptor_v4_source_executions = sum(
        control[0] == "source" for control in descriptor_v4_projection
    )
    descriptor_v4_nested_executions = len(descriptor_v4_projection)
    require(
        descriptor_v4_artifact_executions == DESCRIPTOR_V4_ARTIFACT_SUBCONTROL_COUNT
        and descriptor_v4_parser_executions == DESCRIPTOR_V4_PARSER_SUBCONTROL_COUNT
        and descriptor_v4_source_executions == DESCRIPTOR_V4_SOURCE_SUBCONTROL_COUNT
        and descriptor_v4_nested_executions == DESCRIPTOR_V4_NESTED_EXECUTION_COUNT,
        "descriptor-v4 exact 14+2+2 nested execution accounting changed",
    )
    return attacks, raw_transport_subcontrols, descriptor_v4_nested_executions


def run_rebased_semantic_attacks(root: Path) -> int:
    attacks = 0

    package_stats = "crates/pid-core/src/stats.rs"
    package_snapshot = (
        "crates/pid-core/tests/fixtures/"
        "generate-ksg-local-arithmetic-oracle.py.snapshot"
    )
    canonical_generator = "scripts/generate-ksg-local-arithmetic-oracle.py"
    baseline_first_rebased_attack(
        root,
        label="package-stats-full-blob-drift",
        paths=(package_stats,),
        mutate=lambda candidate: append_bytes(
            candidate / package_stats,
            b"\n// unauthorized package corrective drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "package corrective stats.rs differs from its manually reviewed full blob"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-generator-snapshot-drift",
        paths=(package_snapshot,),
        mutate=lambda candidate: append_bytes(
            candidate / package_snapshot,
            b"\n# unauthorized snapshot drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="snapshot differs from the exact af509 source bytes",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-canonical-generator-drift",
        paths=(canonical_generator,),
        mutate=lambda candidate: append_bytes(
            candidate / canonical_generator,
            b"\n# unauthorized canonical generator drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="canonical KSG generator changed",
    )
    attacks += 1

    package_script = "scripts/verify-package-archives.sh"
    baseline_first_rebased_attack(
        root,
        label="package-archive-test-name-drift",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"stats::tests::packaged_ksg_generator_snapshot_matches_workspace_source_when_available",
            b"stats::tests::unreviewed_archive_branch",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "package archive verifier changed exact extracted-package test name"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "package archive verifier changed exact extracted-package test name"
        ),
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-exact-filter-removal",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"    --exact \\\n",
            b"    --nocapture \\\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier changed exact libtest filter",
        semantic_expectation=caller_held_exact_failure_expectation(
            "package archive verifier changed exact libtest filter"
        ),
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-color-control-removal",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"    --color never 2>&1",
            b"    --nocapture 2>&1",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "package archive verifier changed deterministic libtest color"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "package archive verifier changed deterministic libtest color"
        ),
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-one-test-receipt-weakened",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"'running 1 test'",
            b"'running 0 tests'",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier changed one-test receipt",
        semantic_expectation=caller_held_exact_failure_expectation(
            "package archive verifier changed one-test receipt"
        ),
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-named-pass-receipt-weakened",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b'"test $archive_test_name ... ok"',
            b'"test result: ok"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier changed named-test receipt",
        semantic_expectation=caller_held_exact_failure_expectation(
            "package archive verifier changed named-test receipt"
        ),
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-summary-regex-escape-drift",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"^test result: ok\\. 1 passed;",
            b"^test result: ok\\\\. 1 passed;",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "package archive verifier changed exact one-pass summary parser"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "package archive verifier changed exact one-pass summary parser"
        ),
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-absent-generator-precondition-removed",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b'if [[ -e "$archive_workspace_generator" || -L "$archive_workspace_generator" ]]; then',
            b"if false; then",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier differs from its manually reviewed full blob",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-unrelated-script-drift",
        paths=(package_script,),
        mutate=lambda candidate: append_bytes(
            candidate / package_script,
            b"\n# unrelated unreviewed package drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier differs from its manually reviewed full blob",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-marker-duplicate-rejection-weakened",
        paths=(package_stats,),
        mutate=lambda candidate: replace_once(
            candidate / package_stats,
            b"serde_json::from_slice::<CargoPackageContext>(ambiguous).is_err()",
            b"serde_json::from_slice::<CargoPackageContext>(ambiguous).is_ok()",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "package stats corrective changed duplicate marker rejection"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "package stats corrective changed duplicate marker rejection"
        ),
        repin_stats_for_downstream=True,
    )
    attacks += 1

    workflow = ".github/workflows/ci.yml"
    workflow_mutations = (
        (
            "workflow-ksg-hostile-timeout-budget-weakened",
            (
                b"    # The normal and optimized 351-case custody suites run "
                b"sequentially and\n"
                b"    # intentionally create isolated Git histories for every "
                b"hostile family.\n"
                b"    timeout-minutes: 240\n"
            ),
            b"    timeout-minutes: 45\n",
        ),
        (
            "workflow-checkout-residue-digest-drift",
            (
                b'expected_worktree_config_sha256="443a5f645c23c3d0c0aa09f634b2ad'
                b'111d46ef61946b598a2fb311678ab47454"'
            ),
            (
                b'expected_worktree_config_sha256="043a5f645c23c3d0c0aa09f634b2ad'
                b'111d46ef61946b598a2fb311678ab47454"'
            ),
        ),
        (
            "workflow-checkout-symlink-guard-removal",
            b'if [[ ! -f "$worktree_config" || -L "$worktree_config" ]]; then',
            b'if [[ ! -f "$worktree_config" ]]; then',
        ),
        (
            "workflow-checkout-broad-removal",
            b'            unlink -- "$worktree_config"',
            b'            rm -f -- "$worktree_config"',
        ),
        (
            "workflow-chktex-removal",
            (
                b"            chktex \\\n"
                b"            latexmk \\\n"
                b"            lacheck \\\n"
                b"            lmodern \\\n"
            ),
            (
                b"            latexmk \\\n"
                b"            lacheck \\\n"
                b"            lmodern \\\n"
            ),
        ),
        (
            "workflow-chktex-duplicate",
            b"            chktex \\\n",
            b"            chktex \\\n            chktex \\\n",
        ),
        (
            "workflow-lacheck-removal",
            b"            latexmk \\\n            lacheck \\\n            lmodern \\\n",
            b"            latexmk \\\n            lmodern \\\n",
        ),
        (
            "workflow-cargo-deny-order-regression",
            (
                b"          cargo deny --manifest-path "
                b"audit/tools/certified-sxpid/Cargo.toml\n"
                b"          --config audit/tools/certified-sxpid/deny.toml check\n"
            ),
            (
                b"          cargo deny --manifest-path "
                b"audit/tools/certified-sxpid/Cargo.toml check\n"
                b"          --config audit/tools/certified-sxpid/deny.toml\n"
            ),
        ),
    )
    for label, before, after in workflow_mutations:
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(workflow,),
            mutate=lambda candidate, before=before, after=after: replace_once(
                candidate / workflow,
                before,
                after,
            ),
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment="exact af509 tooling transform",
        )
        attacks += 1

    def move_chktex_after_paper_gate(candidate: Path) -> None:
        workflow_path = candidate / workflow
        replace_once(
            workflow_path,
            b"            chktex \\\n",
            b"",
        )
        replace_once(
            workflow_path,
            b"        run: scripts/check-formal-pdf-set.sh --cross-toolchain\n",
            (
                b"        run: scripts/check-formal-pdf-set.sh --cross-toolchain\n"
                b"      - run: sudo apt-get install --yes chktex\n"
            ),
        )

    baseline_first_rebased_attack(
        root,
        label="workflow-chktex-moved-after-paper-gate",
        paths=(workflow,),
        mutate=move_chktex_after_paper_gate,
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="exact af509 tooling transform",
    )
    attacks += 1

    certified_job_marker = b"  certified-sxpid-reference:\n"
    certified_job_end = b"  certified-sxpid-msrv:\n"
    certified_workflow_mutations = (
        (
            "workflow-certified-elan-step-name-drift",
            b"      - name: Install pinned Elan\n",
            b"      - name: Certified Lean installer removed\n",
        ),
        (
            "workflow-certified-elan-installer-duplicate",
            b"      - name: Install pinned Elan\n",
            (b"      - name: Install pinned Elan\n      - name: Install pinned Elan\n"),
        ),
        (
            "workflow-certified-elan-archive-digest-drift",
            (
                b"          ELAN_ARCHIVE_SHA256: "
                b"df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2\n"
            ),
            (
                b"          ELAN_ARCHIVE_SHA256: "
                b"0f0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2\n"
            ),
        ),
        (
            "workflow-certified-elan-url-drift",
            (
                b"          ELAN_ARCHIVE_URL: "
                b"https://github.com/leanprover/elan/releases/download/v4.2.3/"
                b"elan-x86_64-unknown-linux-gnu.tar.gz\n"
            ),
            (
                b"          ELAN_ARCHIVE_URL: "
                b"https://github.com/leanprover/elan/releases/download/v4.2.4/"
                b"elan-x86_64-unknown-linux-gnu.tar.gz\n"
            ),
        ),
        (
            "workflow-certified-elan-tls-floor-removal",
            b'            --tlsv1.2 --output "$archive" "$ELAN_ARCHIVE_URL"\n',
            b'            --output "$archive" "$ELAN_ARCHIVE_URL"\n',
        ),
        (
            "workflow-certified-elan-hash-check-weakened",
            b"            | sha256sum --check --strict\n",
            b"            | sha256sum --check\n",
        ),
        (
            "workflow-certified-elan-path-export-removal",
            b'          echo "$HOME/.elan/bin" >> "$GITHUB_PATH"\n',
            b"          true # GITHUB_PATH export removed\n",
        ),
        (
            "workflow-certified-elan-init-command-removal",
            (
                b'          "$install_root/elan-init" -y '
                b"--default-toolchain none --no-modify-path\n"
            ),
            b"          true # elan-init execution removed\n",
        ),
        (
            "workflow-certified-cache-action-drift",
            (
                b"      - uses: actions/cache@"
                b"27d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5\n"
            ),
            (
                b"      - uses: actions/cache@"
                b"07d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5\n"
            ),
        ),
        (
            "workflow-certified-cache-path-drift",
            b"          path: audit/formal/lean/.lake\n",
            b"          path: .lake\n",
        ),
        (
            "workflow-certified-cache-key-toolchain-binding-removal",
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
                b"${{ github.sha }}\n"
            ),
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"unbound-toolchain-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
                b"${{ github.sha }}\n"
            ),
        ),
        (
            "workflow-certified-cache-key-manifest-binding-removal",
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
                b"${{ github.sha }}\n"
            ),
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"unbound-manifest-${{ github.sha }}\n"
            ),
        ),
        (
            "workflow-certified-cache-restore-key-widened",
            (
                b"          restore-keys: lake-${{ runner.os }}-"
                b"${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}\n"
            ),
            (b"          restore-keys: lake-${{ runner.os }}-${{ runner.arch }}-\n"),
        ),
        (
            "workflow-certified-mathlib-cache-fetch-removal",
            b"          lake exe cache get\n",
            b"          true # lake cache fetch removed\n",
        ),
        (
            "workflow-certified-mathlib-build-removal",
            b"          lake build\n",
            b"          true # lake build removed\n",
        ),
    )
    for label, before, after in certified_workflow_mutations:
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(workflow,),
            mutate=lambda candidate, before=before, after=after: replace_once_between(
                candidate / workflow,
                certified_job_marker,
                certified_job_end,
                before,
                after,
            ),
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment="exact af509 tooling transform",
        )
        attacks += 1

    formal_job_marker = b"  formal-pdf-structure:\n"
    formal_job_end = certified_job_marker
    formal_workflow_mutations = (
        (
            "workflow-formal-elan-step-name-drift",
            b"      - name: Install pinned Elan\n",
            b"      - name: Formal PDF Lean installer removed\n",
        ),
        (
            "workflow-formal-elan-installer-duplicate",
            b"      - name: Install pinned Elan\n",
            (b"      - name: Install pinned Elan\n      - name: Install pinned Elan\n"),
        ),
        (
            "workflow-formal-elan-archive-digest-drift",
            (
                b"          ELAN_ARCHIVE_SHA256: "
                b"df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2\n"
            ),
            (
                b"          ELAN_ARCHIVE_SHA256: "
                b"0f0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2\n"
            ),
        ),
        (
            "workflow-formal-elan-url-drift",
            (
                b"          ELAN_ARCHIVE_URL: "
                b"https://github.com/leanprover/elan/releases/download/v4.2.3/"
                b"elan-x86_64-unknown-linux-gnu.tar.gz\n"
            ),
            (
                b"          ELAN_ARCHIVE_URL: "
                b"https://github.com/leanprover/elan/releases/download/v4.2.4/"
                b"elan-x86_64-unknown-linux-gnu.tar.gz\n"
            ),
        ),
        (
            "workflow-formal-elan-hash-check-weakened",
            b"            | sha256sum --check --strict\n",
            b"            | sha256sum --check\n",
        ),
        (
            "workflow-formal-elan-tls-floor-removal",
            b'            --tlsv1.2 --output "$archive" "$ELAN_ARCHIVE_URL"\n',
            b'            --output "$archive" "$ELAN_ARCHIVE_URL"\n',
        ),
        (
            "workflow-formal-elan-path-export-removal",
            b'          echo "$HOME/.elan/bin" >> "$GITHUB_PATH"\n',
            b"          true # GITHUB_PATH export removed\n",
        ),
        (
            "workflow-formal-elan-init-command-removal",
            (
                b'          "$install_root/elan-init" -y '
                b"--default-toolchain none --no-modify-path\n"
            ),
            b"          true # elan-init execution removed\n",
        ),
        (
            "workflow-formal-cache-action-drift",
            (
                b"      - uses: actions/cache@"
                b"27d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5\n"
            ),
            (
                b"      - uses: actions/cache@"
                b"07d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5\n"
            ),
        ),
        (
            "workflow-formal-cache-path-drift",
            b"          path: audit/formal/lean/.lake\n",
            b"          path: .lake\n",
        ),
        (
            "workflow-formal-cache-key-toolchain-binding-removal",
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
                b"${{ github.sha }}\n"
            ),
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"unbound-toolchain-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
                b"${{ github.sha }}\n"
            ),
        ),
        (
            "workflow-formal-cache-key-manifest-binding-removal",
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}-"
                b"${{ github.sha }}\n"
            ),
            (
                b"          key: lake-${{ runner.os }}-${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"unbound-manifest-${{ github.sha }}\n"
            ),
        ),
        (
            "workflow-formal-cache-restore-key-widened",
            (
                b"          restore-keys: lake-${{ runner.os }}-"
                b"${{ runner.arch }}-"
                b"${{ hashFiles('audit/formal/lean/lean-toolchain') }}-"
                b"${{ hashFiles('audit/formal/lean/lake-manifest.json') }}\n"
            ),
            (b"          restore-keys: lake-${{ runner.os }}-${{ runner.arch }}-\n"),
        ),
        (
            "workflow-formal-mathlib-cache-fetch-removal",
            b"          lake exe cache get\n",
            b"          true # lake cache fetch removed\n",
        ),
        (
            "workflow-formal-mathlib-build-removal",
            b"          lake build\n",
            b"          true # lake build removed\n",
        ),
    )
    for label, before, after in formal_workflow_mutations:
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(workflow,),
            mutate=lambda candidate, before=before, after=after: replace_once_between(
                candidate / workflow,
                formal_job_marker,
                formal_job_end,
                before,
                after,
            ),
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment="exact af509 tooling transform",
        )
        attacks += 1

    mathlib_build_block = (
        b"      - name: Fetch the Mathlib cache and build\n"
        b"        working-directory: audit/formal/lean\n"
        b"        run: |\n"
        b"          set -euo pipefail\n"
        b"          lake exe cache get\n"
        b"          lake build\n"
    )

    def move_certified_build_after_consumer(candidate: Path) -> None:
        workflow_path = candidate / workflow
        replace_once_between(
            workflow_path,
            certified_job_marker,
            certified_job_end,
            mathlib_build_block,
            b"",
        )
        replace_once_between(
            workflow_path,
            certified_job_marker,
            certified_job_end,
            b"      - run: python3 scripts/check-lean-exact-log-product.py\n",
            (
                b"      - run: python3 scripts/check-lean-exact-log-product.py\n"
                + mathlib_build_block
            ),
        )

    baseline_first_rebased_attack(
        root,
        label="workflow-certified-build-after-lean-consumer",
        paths=(workflow,),
        mutate=move_certified_build_after_consumer,
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="exact af509 tooling transform",
    )
    attacks += 1

    def move_formal_build_after_paper_consumer(candidate: Path) -> None:
        workflow_path = candidate / workflow
        replace_once_between(
            workflow_path,
            formal_job_marker,
            formal_job_end,
            mathlib_build_block,
            b"",
        )
        replace_once_between(
            workflow_path,
            formal_job_marker,
            formal_job_end,
            b"        run: scripts/check-formal-pdf-set.sh --cross-toolchain\n",
            (
                b"        run: scripts/check-formal-pdf-set.sh --cross-toolchain\n"
                + mathlib_build_block
            ),
        )

    baseline_first_rebased_attack(
        root,
        label="workflow-formal-build-after-paper-consumer",
        paths=(workflow,),
        mutate=move_formal_build_after_paper_consumer,
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="exact af509 tooling transform",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="workflow-unrelated-sixth-edit",
        paths=(workflow,),
        mutate=lambda candidate: append_bytes(
            candidate / workflow,
            b"\n# unauthorized sixth corrective edit\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="exact af509 tooling transform",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="foundational-paper-lake-preflight-removal",
        paths=("scripts/check-foundational-sxpid-audit-pdf.sh",),
        mutate=lambda candidate: (
            replace_once(
                candidate / "scripts/check-foundational-sxpid-audit-pdf.sh",
                b"chktex lacheck lake python3",
                b"chktex lacheck python3 python3",
            ),
            replace_once(
                candidate / CHECKER_RELATIVE,
                (
                    b"            (\n"
                    b'                b\'python3 "$MUTATION_CHECKER" '
                    b'>"$BUILD_DIR/mutation-evidence.json"\\n\',\n'
                    b'                b\'python3 -I -S "$MUTATION_CHECKER" '
                    b'>"$BUILD_DIR/mutation-evidence.json"\\n\',\n'
                    b"            ),\n"
                    b"        ),\n"
                    b'        "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md": (\n'
                ),
                (
                    b"            (\n"
                    b'                b\'python3 "$MUTATION_CHECKER" '
                    b'>"$BUILD_DIR/mutation-evidence.json"\\n\',\n'
                    b'                b\'python3 -I -S "$MUTATION_CHECKER" '
                    b'>"$BUILD_DIR/mutation-evidence.json"\\n\',\n'
                    b"            ),\n"
                    b"            (\n"
                    b'                b"commands=(latexmk cmp pdffonts pdfinfo '
                    b'pdftotext pdftoppm "\n'
                    b'                b"chktex lacheck lake python3)\\n",\n'
                    b'                b"commands=(latexmk cmp pdffonts pdfinfo '
                    b'pdftotext pdftoppm "\n'
                    b'                b"chktex lacheck python3 python3)\\n",\n'
                    b"            ),\n"
                    b"        ),\n"
                    b'        "FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md": (\n'
                ),
            ),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="differs from the exact lake-preflight transform",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="claim-checker-nondigest-drift",
        paths=("scripts/check-certified-sxpid2-claim.py",),
        mutate=lambda candidate: append_bytes(
            candidate / "scripts/check-certified-sxpid2-claim.py",
            b"\n# unauthorized claim-checker drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "certified-SxPID2 claim checker differs from its exact three-digest rebind"
        ),
    )
    attacks += 1

    ecosystem_surfaces = (
        "ECOSYSTEM_CAPABILITIES.md",
        "ecosystem-capabilities.json",
        "scripts/check-ecosystem-capabilities.py",
    )
    current_catalog_digest = (
        b"637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"
    )
    for ecosystem_surface in ecosystem_surfaces:
        semantic_detail = (
            f"{ecosystem_surface} changed after the exact af509 ecosystem transform"
        )
        baseline_first_rebased_attack(
            root,
            label=f"ecosystem-transform-drift-{ecosystem_surface}",
            paths=(ecosystem_surface,),
            mutate=lambda candidate, relative=ecosystem_surface: replace_once(
                candidate / relative,
                current_catalog_digest,
                b"01a305873716117b540b26113560d4693eb9d9e356718fbee01713618bee3383",
            ),
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment=semantic_detail,
            semantic_expectation=caller_held_exact_failure_expectation(semantic_detail),
        )
        attacks += 1

    def mutate_coordinated_ecosystem(candidate: Path) -> None:
        append_bytes(
            candidate / "method-catalog.json",
            b" ",
        )
        alternate_digest = (
            hashlib.sha256((candidate / "method-catalog.json").read_bytes())
            .hexdigest()
            .encode("ascii")
        )
        for relative in ecosystem_surfaces:
            replace_once(
                candidate / relative,
                current_catalog_digest,
                alternate_digest,
            )

    baseline_first_rebased_attack(
        root,
        label="coordinated-alternate-catalog-and-ecosystem-surfaces",
        paths=("method-catalog.json", *ecosystem_surfaces),
        mutate=mutate_coordinated_ecosystem,
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "current method catalog differs from the manually reviewed "
            "corrective digest"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="stats-forbidden-exact-sum-token",
        paths=("crates/pid-core/src/stats.rs",),
        mutate=lambda candidate: append_bytes(
            candidate / "crates/pid-core/src/stats.rs",
            b"\nfn exact_binary64_sum() {}\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "stats.rs contains forbidden later-wave exact-sum token exact_binary64_sum"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "stats.rs contains forbidden later-wave exact-sum token exact_binary64_sum"
        ),
        repin_stats_for_downstream=True,
    )
    attacks += 1

    parallel = "crates/pid-core/tests/parallel_bit_identity.rs"
    baseline_first_rebased_attack(
        root,
        label="ambient-pid2-synergy-bits",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b"const PID2_SYN_BITS: u64 = 4591732782175321776;",
            b"const PID2_SYN_BITS: u64 = 4591732782175321784;",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "parallel bit-identity constant PID2_SYN_BITS is not the unique "
            "KSG-only value"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "parallel bit-identity constant PID2_SYN_BITS is not the unique "
            "KSG-only value"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-false-zero-crate-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b'#![cfg(feature = "experimental-pipelines")]',
            (b'#![cfg(all(feature = "experimental-pipelines", feature = "parallel"))]'),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="zero-test-capable crate gate",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-second-crate-cfg-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b'#![cfg(feature = "experimental-pipelines")]\n\n',
            (
                b'#![cfg(feature = "experimental-pipelines")]\n\n'
                b'#![cfg(feature = "parallel")]\n'
            ),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-module-cfg-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b"mod common;\n",
            b'#[cfg(feature = "parallel")]\nmod common;\n',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    first_parallel_test = (
        b"#[test]\n"
        b"fn ksg_report_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {"
    )
    baseline_first_rebased_attack(
        root,
        label="serial-individual-test-cfg-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            (b'#[cfg(feature = "parallel")]\n' + first_parallel_test),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-cfg-attr-ignore",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            (b'#[cfg_attr(not(feature = "parallel"), ignore)]\n' + first_parallel_test),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-unconditional-ignore",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            b"#[ignore]\n" + first_parallel_test,
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-runtime-cfg-macro",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            (first_parallel_test + b'\n    if cfg!(feature = "parallel") { return; }'),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="runtime cfg! gate",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-early-return-bypass",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            first_parallel_test + b"\n    return;",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="early-return bypass",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-test-inventory-removal",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b"#[test]\nfn ksg_local_mi_terms_match_serial_reference(",
            b"fn ksg_local_mi_terms_match_serial_reference(",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="12 nonzero serial tests",
    )
    attacks += 1

    release = "release-scope-1.0.json"
    baseline_first_rebased_attack(
        root,
        label="combined-pid2-release-revision",
        paths=(release,),
        mutate=lambda candidate: replace_once(
            candidate / release,
            b"separate-biased-term-pid2-integer-harmonic-v2",
            (
                b"separate-biased-term-pid2-with-integer-harmonic-inputs-and-"
                b"represented-input-exact-synergy-sum-v2"
            ),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "release family 'pid-core.experimental.continuous.pid2' is not at "
            "the KSG-only bridge revision"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "release family 'pid-core.experimental.continuous.pid2' is not at "
            "the KSG-only bridge revision"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="release-revision-type-confusion",
        paths=(release,),
        mutate=lambda candidate: replace_once(
            candidate / release,
            b'"estimator_revision": "separate-biased-term-pid2-integer-harmonic-v2"',
            b'"estimator_revision": 17',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=("release family 13 has invalid typed identity/revision"),
        semantic_expectation=caller_held_exact_failure_expectation(
            "release family 13 has invalid typed identity/revision"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="release-duplicate-key",
        paths=(release,),
        mutate=lambda candidate: replace_once(
            candidate / release,
            b'{\n  "acceptance_blockers"',
            b'{\n  "schema": "pid-rs/release-scope",\n  "acceptance_blockers"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=("release-scope-1.0.json: duplicate JSON key 'schema'"),
        semantic_expectation=caller_held_exact_failure_expectation(
            "release-scope-1.0.json: duplicate JSON key 'schema'"
        ),
    )
    attacks += 1

    identity = "crates/pid-core/identity/software-identity-reference-v1.json"
    baseline_first_rebased_attack(
        root,
        label="combined-identity-field",
        paths=(identity,),
        mutate=lambda candidate: replace_once(
            candidate / identity,
            b'"attestation": "none"',
            b'"attestation": "local"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed outside the two authorized forensic digests",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="identity-catalog-digest-drift",
        paths=(identity,),
        mutate=lambda candidate: replace_once(
            candidate / identity,
            b'"canonical_json_sha256": "637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"',
            b'"canonical_json_sha256": "037719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "software identity artifact 'method_catalog' does not bind current "
            "canonical bytes"
        ),
        semantic_expectation=caller_held_exact_failure_expectation(
            "software identity artifact 'method_catalog' does not bind current "
            "canonical bytes"
        ),
    )
    attacks += 1
    return attacks


def main() -> int:
    try:
        initial_checker_entry = stable_regular_file(ROOT, CHECKER_RELATIVE)
        source_facts, facts_source_entry = current_facts(
            ROOT,
            source_entry=initial_checker_entry,
        )
        require(
            facts_source_entry == initial_checker_entry,
            "source facts were not emitted by the initial stable checker capture",
        )
        frozen_overlay = freeze_candidate_overlay(ROOT, source_facts)
        overlay_checker_entry = frozen_overlay_entry(
            frozen_overlay,
            CHECKER_RELATIVE,
        )
        require(
            facts_source_entry == overlay_checker_entry,
            "source facts were not emitted by the frozen overlay checker",
        )
        replayed_facts, replayed_source_entry = current_facts(
            ROOT,
            source_entry=overlay_checker_entry,
        )
        require(
            replayed_source_entry == overlay_checker_entry
            and semantic_facts_projection(replayed_facts)
            == semantic_facts_projection(source_facts),
            "frozen overlay checker did not replay the source semantic facts",
        )
        bind_failure_detail_source(frozen_overlay)
        execution_receipt_anti_fraud_rows = static_source_preflight(frozen_overlay)
        execution_receipt_anti_fraud = len(execution_receipt_anti_fraud_rows)
        execution_receipt_anti_fraud_projection_sha256 = (
            _execution_receipt_anti_fraud_projection_sha256(
                execution_receipt_anti_fraud_rows
            )
        )
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-ksg-phase-self-test."
        ) as temporary_raw:
            temporary = Path(temporary_raw)
            optimization_preflight(temporary)
            entry_isolation = entry_isolation_preflight(temporary)
            success_receipt_oracle = run_success_receipt_oracle_attacks()
            failure_receipt_oracle = run_failure_receipt_oracle_attacks()
            candidate = temporary / "candidate"
            clone_candidate(ROOT, candidate, source_facts, frozen_overlay)
            run_checker(candidate, expect_success=True)

            checker_model = run_checker_model_attacks(candidate, frozen_overlay)
            python_entry_attacks = run_python_entry_isolation_attacks(candidate)
            policy_attacks = run_policy_authority_attacks(candidate)
            json_type_firewall = run_json_type_firewall_controls(candidate)
            path_custody = run_path_and_custody_attacks(candidate)
            tree_custody = run_external_tree_custody_tests(candidate, source_facts)
            retained_self_reference = run_retained_self_reference_boundary(
                candidate,
                source_facts,
            )
            repository_context = run_repository_context_attacks(candidate)
            public_ci_evidence = run_public_ci_evidence_attacks(candidate)
            (
                public_ci_portability_evidence,
                c3_review_ledger_nested_executions,
                c3_local_artifact_parity_nested_families,
                c3_local_artifact_parity_nested_executions,
            ) = run_public_ci_portability_evidence_attacks(candidate)
            (
                lean_portability,
                phase_lean_raw_transport_subcontrols,
                descriptor_v4_nested_executions,
            ) = run_lean_portability_attacks(candidate)
            semantic = run_rebased_semantic_attacks(candidate)
            lifecycle = run_lifecycle_history_tests(
                ROOT,
                temporary,
                source_facts,
                frozen_overlay,
            )
            run_checker(candidate, expect_success=True)
            require(
                json_type_firewall == 2,
                "JSON type-firewall control inventory changed",
            )
            require(
                retained_self_reference == 1,
                "retained self-reference boundary inventory changed",
            )
            require(
                entry_isolation == 5,
                "entry-isolation control inventory changed",
            )
            require(
                success_receipt_oracle == 11,
                "success-receipt oracle hostile inventory changed",
            )
            require(
                failure_receipt_oracle == 18,
                "failure-receipt oracle hostile inventory changed",
            )
            require(
                c3_review_ledger_nested_executions == C3_REVIEW_LEDGER_EXECUTION_COUNT
                and c3_local_artifact_parity_nested_families
                == C3_LOCAL_ARTIFACT_PARITY_FAMILY_COUNT
                and c3_local_artifact_parity_nested_executions
                == C3_LOCAL_ARTIFACT_PARITY_EXECUTION_COUNT
                and descriptor_v4_nested_executions
                == DESCRIPTOR_V4_NESTED_EXECUTION_COUNT
                and execution_receipt_anti_fraud
                == EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT,
                "uncounted nested-control receipt accounting changed",
            )
            observed_families = {
                "checker_model": checker_model,
                "entry_isolation": entry_isolation,
                "external_tree": tree_custody,
                "failure_receipt_oracle": failure_receipt_oracle,
                "git_context": repository_context,
                "lean_portability": lean_portability,
                "lifecycle_history": lifecycle,
                "path_custody": path_custody,
                "policy_authority": policy_attacks,
                "prior_public_ci_evidence": public_ci_evidence,
                "public_ci_portability_evidence": (public_ci_portability_evidence),
                "python_entry_attacks": python_entry_attacks,
                "rebased_semantic_firewall": semantic,
                "success_receipt_oracle": success_receipt_oracle,
            }
            observed_separate_controls = {
                "json_type_firewall": json_type_firewall,
                "phase_lean_raw_transport_subcontrols": (
                    phase_lean_raw_transport_subcontrols
                ),
                "retained_self_reference_boundary": retained_self_reference,
            }
            total = validate_hostile_suite_counts(
                load_hostile_suite_contract(candidate),
                observed_families=observed_families,
                observed_separate_controls=observed_separate_controls,
            )
            require(
                _BASELINE_LIFECYCLE_AUTHORITY.issue_rollback_probe_completed()
                and _SEALED_LIFECYCLE_AUTHORITY.issue_rollback_probe_completed(),
                "permit-to-receipt rollback probes did not complete",
            )
            _RECEIPT_RUN_AUTHORITY.require_terminal_success_state()
    except (OSError, SelfTestError) as error:
        print(f"ERROR: KSG phase-isolation self-test: {error}", file=sys.stderr)
        return 1

    print(
        "OK: KSG phase-isolation hostile suite; "
        f"checker-model={checker_model}; "
        f"python-entry-attacks={python_entry_attacks}; "
        f"policy-authority={policy_attacks}; "
        f"path-custody={path_custody}; external-tree={tree_custody}; "
        f"git-context={repository_context}; "
        f"public-ci-evidence={public_ci_evidence}; "
        f"public-ci-portability-evidence={public_ci_portability_evidence}; "
        f"lean-portability={lean_portability}; "
        f"entry-isolation={entry_isolation}; "
        f"success-receipt-oracle={success_receipt_oracle}; "
        f"failure-receipt-oracle={failure_receipt_oracle}; "
        f"hash-rebased-semantics={semantic}; "
        f"fixed-pin-first-rejections={semantic}; "
        f"deliberately-repinned-semantic-rejections={semantic}; "
        f"lifecycle-history={lifecycle}; "
        f"total={total} integer-return/source-sealed hostile-family aggregate "
        f"(not {total} causal lifecycle receipts); "
        f"exact-candidate-loader-subcontrols={EXACT_CANDIDATE_LOADER_SUBCONTROL_COUNT}/8 "
        "(uncounted nested subcontrols); "
        f"execution-receipt-anti-fraud={execution_receipt_anti_fraud}/"
        f"{EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_COUNT} executions "
        f"({EXECUTION_RECEIPT_STATIC_MODEL_PROBE_COUNT} static/model controls + "
        f"{EXECUTION_RECEIPT_RUNTIME_HOSTILE_SHAPE_COUNT} runtime receipt, "
        "lifecycle, concurrency, and invariant controls; "
        "uncounted; excluded from the 351 integer-return/source-sealed aggregate); "
        "execution-receipt-anti-fraud-spec-sha256="
        f"{EXPECTED_EXECUTION_RECEIPT_ANTI_FRAUD_CONTROL_SPEC_SHA256}; "
        "execution-receipt-anti-fraud-observed-sha256="
        f"{execution_receipt_anti_fraud_projection_sha256}; "
        f"c3-review-ledger-nested={c3_review_ledger_nested_executions}/85 "
        "executions (uncounted nested controls); "
        f"c3-local-artifact-parity-nested="
        f"{c3_local_artifact_parity_nested_families}/19 families,"
        f"{c3_local_artifact_parity_nested_executions}/21 executions "
        "(uncounted nested controls); "
        f"descriptor-v4-nested={descriptor_v4_nested_executions}/18 executions "
        "(14 artifact + 2 parser + 2 source; uncounted inside lean-portability); "
        f"json-type-firewall={json_type_firewall}/2 (separate from total); "
        f"phase-lean-raw-transport-subcontrols={phase_lean_raw_transport_subcontrols}/6 "
        "(separate from total; "
        "one evidence-count, three static source-model, one live precedence, "
        "and one live observed-byte binding control); "
        f"retained-self-reference={retained_self_reference}/1 "
        "(accepted coordinated rebase; pre-pinned tree rejection; separate from total); "
        f"mode={'optimized' if sys.flags.optimize else 'normal'}. "
        "Mechanical fact rebasing never edited the separately reviewed path policy; "
        "disposable candidate checkers used captured stdin bytes and one frozen "
        "overlay, while official top-level entries remained initially path-loaded; "
        "endpoint replay was not an atomic filesystem history; "
        "receipt-root commits were reviewed-process exception-atomic reference "
        "assignments, not crash-durable, cross-process, filesystem-atomic, "
        "cryptographic, or remote attestations; "
        "authority methods enforce creating-thread, non-reentrant execution; "
        "this does not make "
        "post-commit return delivery atomic against tracing, signals, or "
        "asynchronous exceptions; callable identity seals do not seal rebound "
        "globals or helper dependencies against coordinated same-process mutation; "
        "the checker cannot authenticate coordinated mutation of its own bytes; "
        "the module semantic pin is integrity-only and independently trusted "
        "whole-file custody remains the authenticity root; "
        "this tests bounded custody cuts, not KSG science."
    )
    return 0


def _normalized_main_entry() -> int:
    try:
        result = main()
    except BaseException as error:
        print(
            "ERROR: KSG phase-isolation outer boundary: "
            + _base_exception_diagnostic(error),
            file=sys.stderr,
        )
        return 2
    if type(result) is not int or result not in {0, 1}:
        print(
            "ERROR: KSG phase-isolation outer boundary: invalid main return",
            file=sys.stderr,
        )
        return 2
    return result


if __name__ == "__main__":
    raise SystemExit(_normalized_main_entry())
