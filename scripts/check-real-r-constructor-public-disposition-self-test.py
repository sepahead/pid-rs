#!/usr/bin/env python3
"""Hostile tests for the Real-R constructor public-disposition boundary."""

from __future__ import annotations

import copy
from pathlib import Path
import shutil
import sys
import tempfile
import types
from typing import Any, Callable


if sys.version_info < (3, 11):
    raise SystemExit(
        "check-real-r-constructor-public-disposition-self-test.py requires Python 3.11+"
    )


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-real-r-constructor-public-disposition.py"
module = types.ModuleType("check_real_r_constructor_public_disposition")
module.__file__ = str(CHECKER)
sys.modules[module.__name__] = module
exec(compile(CHECKER.read_bytes(), str(CHECKER), "exec"), module.__dict__)

archive = ROOT / module.ARCHIVE_RELATIVE
index = module.parse_json((archive / "INDEX.json").read_bytes(), label="INDEX")
schema = module.parse_json((archive / "INDEX.schema.json").read_bytes(), label="SCHEMA")
if type(index) is not dict or type(schema) is not dict:
    raise SystemExit("baseline index/schema shape changed")
module.validate_index_semantics(index, schema)
module.validate_public_disposition(ROOT)

mutations_rejected = 0
mutation_codes: dict[str, str] = {}


def record(label: str, error: BaseException) -> None:
    global mutations_rejected
    mutations_rejected += 1
    mutation_codes[label] = str(error).split(":", 1)[0]


def expect_semantic_rejected(
    label: str, mutate: Callable[[dict[str, Any]], None]
) -> None:
    value = copy.deepcopy(index)
    mutate(value)
    try:
        module.validate_index_semantics(value, schema)
    except (module.PublicDispositionError, module.SchemaValidationError) as error:
        record(label, error)
        return
    raise SystemExit(f"{label}: semantic mutation unexpectedly passed")


def expect_parse_rejected(label: str, raw: bytes) -> None:
    try:
        module.parse_json(raw, label="MUTATION")
    except module.PublicDispositionError as error:
        record(label, error)
        return
    raise SystemExit(f"{label}: JSON mutation unexpectedly passed")


def expect_full_rejected(label: str, mutate: Callable[[Path], None]) -> None:
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-real-r-public-disposition-"
    ) as temporary:
        root = Path(temporary)
        target = root / module.ARCHIVE_RELATIVE
        target.parent.mkdir(parents=True)
        shutil.copytree(archive, target)
        mutate(target)
        try:
            module.validate_public_disposition(root)
        except (module.PublicDispositionError, module.SchemaValidationError) as error:
            record(label, error)
            return
    raise SystemExit(f"{label}: filesystem mutation unexpectedly passed")


def expect_noncanonical_index_rejected() -> None:
    label = "noncanonical_index_json"
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-real-r-public-disposition-"
    ) as temporary:
        root = Path(temporary)
        target = root / module.ARCHIVE_RELATIVE
        target.parent.mkdir(parents=True)
        shutil.copytree(archive, target)
        path = target / "INDEX.json"
        raw = (module.json.dumps(index, indent=2, ensure_ascii=True) + "\n").encode(
            "ascii"
        )
        path.write_bytes(raw)
        original_identity = module.EXPECTED_IDENTITIES["INDEX.json"]
        module.EXPECTED_IDENTITIES["INDEX.json"] = (
            len(raw),
            module.hashlib.sha256(raw).hexdigest(),
        )
        try:
            module.validate_public_disposition(root)
        except module.PublicDispositionError as error:
            if not str(error).startswith("INDEX.canonical:"):
                raise SystemExit(f"{label}: wrong rejection: {error}") from error
            record(label, error)
            return
        finally:
            module.EXPECTED_IDENTITIES["INDEX.json"] = original_identity
    raise SystemExit(f"{label}: canonicality mutation unexpectedly passed")


expect_semantic_rejected(
    "current_authority_true", lambda value: value.__setitem__("current_authority", True)
)
expect_semantic_rejected(
    "runtime_scope_promoted",
    lambda value: value["execution"].__setitem__(
        "full_runtime_replayed_for_public_disposition", True
    ),
)
expect_semantic_rejected(
    "privacy_approval_promoted",
    lambda value: value["privacy"].__setitem__(
        "explicit_owner_public_disclosure_approval_recorded", True
    ),
)
expect_semantic_rejected(
    "publication_rights_promoted",
    lambda value: value["licensing"].__setitem__(
        "payload_publication_rights_confirmed", True
    ),
)
expect_semantic_rejected(
    "payload_not_withheld",
    lambda value: value["privacy"].__setitem__("payload_withheld", False),
)
expect_semantic_rejected(
    "raw_paths_claimed_public",
    lambda value: value["privacy"].__setitem__(
        "raw_paths_repeated_in_public_metadata", True
    ),
)
expect_semantic_rejected(
    "source_claimed_included",
    lambda value: value["source_identities"][0].__setitem__(
        "included_in_public_branch", True
    ),
)
expect_semantic_rejected(
    "source_records_reordered", lambda value: value["source_identities"].reverse()
)
expect_semantic_rejected(
    "r10_control_count",
    lambda value: value["architecture"].__setitem__("r10_controls", 63),
)
expect_semantic_rejected(
    "combined_event_count",
    lambda value: value["architecture"].__setitem__("combined_authority_events", 211),
)
expect_semantic_rejected("nonclaim_removed", lambda value: value["nonclaims"].pop())
expect_semantic_rejected(
    "domain_nonclaim_rewritten",
    lambda value: value["nonclaims"].__setitem__(
        4, "project_domain_classification_claimed"
    ),
)
expect_semantic_rejected("support_removed", lambda value: value["support_files"].pop())
expect_semantic_rejected(
    "support_role",
    lambda value: value["support_files"][0].__setitem__("role", "human_disposition"),
)
expect_semantic_rejected(
    "support_bool_for_bytes",
    lambda value: value["support_files"][0].__setitem__("bytes", True),
)
expect_semantic_rejected(
    "source_byte_identity",
    lambda value: value["source_identities"][0].__setitem__("bytes", 348608),
)
expect_semantic_rejected(
    "source_role",
    lambda value: value["source_identities"][1].__setitem__(
        "role", "third_party_auditor"
    ),
)
expect_semantic_rejected(
    "extra_top_key", lambda value: value.__setitem__("active", True)
)

expect_parse_rejected(
    "duplicate_json_key",
    b'{"current_authority":false,"current_authority":true}\n',
)
expect_parse_rejected("float_json_value", b'{"value":1.0}\n')
expect_parse_rejected("nonfinite_json_value", b'{"value":NaN}\n')
expect_parse_rejected("non_ascii_json", b'{"value":"\xff"}\n')
expect_noncanonical_index_rejected()


def add_extra(target: Path) -> None:
    (target / "EXTRA.txt").write_text("stale\n", encoding="ascii")


def change_document(target: Path) -> None:
    path = target / "ARCHITECTURE.md"
    path.write_bytes(path.read_bytes() + b"stale\n")


def expose_private_path(target: Path) -> None:
    path = target / "DISPOSITION.md"
    path.write_bytes(path.read_bytes() + b"/" + b"Users/example/private\n")


def expose_withheld_name(target: Path) -> None:
    path = target / "DISPOSITION.md"
    path.write_bytes(path.read_bytes() + b"construct_validate_real_r.py\n")


def make_document_executable(target: Path) -> None:
    (target / "ARCHITECTURE.md").chmod(0o755)


def replace_document_with_symlink(target: Path) -> None:
    path = target / "ARCHITECTURE.md"
    path.unlink()
    path.symlink_to("DISPOSITION.md")


expect_full_rejected("extra_archive_file", add_extra)
expect_full_rejected("document_byte_drift", change_document)
expect_full_rejected("personal_path_disclosure", expose_private_path)
expect_full_rejected("withheld_source_name", expose_withheld_name)
expect_full_rejected("document_mode", make_document_executable)
expect_full_rejected("document_symlink", replace_document_with_symlink)

expected_mutations = 29
if mutations_rejected != expected_mutations:
    raise SystemExit(
        f"mutation accounting changed: {mutations_rejected} != {expected_mutations}"
    )
if len(mutation_codes) != expected_mutations:
    raise SystemExit("mutation labels are not unique")

result = {
    "format": "pid-rs/real-r-constructor-public-disposition-self-test/v1",
    "mutation_codes": mutation_codes,
    "mutations_rejected": mutations_rejected,
    "status": "real_r_constructor_public_disposition_self_test_passed",
}
sys.stdout.buffer.write(module.canonical_json_bytes(result))
