#!/usr/bin/env bash
# Mutation tests: every direct public-item form must fail release-scope coherence.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-release-scope.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

python3 "$SCRIPT_DIR/check-release-scope.py" --print-markdown >/dev/null

for mutation in \
  reexport static union async_fn extern_fn inline_module out_of_line_module \
  parent_reexport extern_crate macro_export
do
  cp "$REPO_ROOT/crates/pid-core/src/lib.rs" "$TMP/lib.rs"
  python3 - "$TMP/lib.rs" "$mutation" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
mutation = sys.argv[2]
source = path.read_text(encoding="utf-8")
categorical_needle = "    pub mod categorical {\n"
stable_needle = "pub mod stable {\n"
declarations = {
    "reexport": "        pub use crate::error::PidError as UnscopedReleaseExport;\n",
    "static": "        pub static UnscopedReleaseStatic: usize = 0;\n",
    "union": "        pub union UnscopedReleaseUnion { pub value: usize }\n",
    "async_fn": "        pub async fn unscoped_release_async() {}\n",
    "extern_fn": '        pub extern "C" fn unscoped_release_extern() {}\n',
    "inline_module": "        pub mod unscoped_release_module {}\n",
    "out_of_line_module": "        pub mod unscoped_release_module;\n",
}
if mutation in declarations:
    if source.count(categorical_needle) != 1:
        raise SystemExit("stable categorical injection point changed")
    source = source.replace(categorical_needle, categorical_needle + declarations[mutation], 1)
elif mutation == "parent_reexport":
    if source.count(stable_needle) != 1:
        raise SystemExit("stable parent injection point changed")
    source = source.replace(
        stable_needle,
        stable_needle + "    pub use crate::PidError as UnscopedParentExport;\n",
        1,
    )
elif mutation == "extern_crate":
    source = source.replace(
        stable_needle,
        "pub extern crate serde as unscoped_serde;\n\n" + stable_needle,
        1,
    )
elif mutation == "macro_export":
    source = source.replace(
        stable_needle,
        "#[macro_export]\nmacro_rules! unscoped_release_macro { () => {} }\n\n" + stable_needle,
        1,
    )
else:
    raise SystemExit(f"unknown source mutation: {mutation}")
path.write_text(source, encoding="utf-8")
PY

  if python3 "$SCRIPT_DIR/check-release-scope.py" \
    --lib-rs "$TMP/lib.rs" --print-markdown >"$TMP/stdout" 2>"$TMP/stderr"
  then
    echo "unscoped stable $mutation was accepted" >&2
    exit 1
  fi
  if [[ "$mutation" == "inline_module" || "$mutation" == "out_of_line_module" ]]; then
    expected="unscoped public modules: unscoped_release_module"
  else
    expected="unscoped exports:"
  fi
  if ! grep -F "$expected" "$TMP/stderr" >/dev/null; then
    echo "stable $mutation failed for the wrong reason" >&2
    sed -n '1,20p' "$TMP/stderr" >&2
    exit 1
  fi
done

for mutation in \
  wrong_feature fabricated_leak bad_state remove_parallel bad_semver bad_path duplicate_key \
  fabricated_tool old_snapshot_source partial_approval wrong_approval_commit \
  missing_conflict missing_evidence
do
  python3 - "$REPO_ROOT/release-scope-1.0.json" "$TMP/scope.json" "$mutation" <<'PY'
import json
from pathlib import Path
import sys

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
mutation = sys.argv[3]
scope = json.loads(source.read_text(encoding="utf-8"))
if mutation == "wrong_feature":
    next(item for item in scope["families"] if item["id"] == "pid-core.experimental.continuous.isx")["cargo_feature"] = "experimental-hyperbolic"
elif mutation == "fabricated_leak":
    scope["conditional_members"].append(
        {
            "added_api_line": "pub pid_core::Metric::Fabricated",
            "feature": "experimental-hyperbolic",
            "kind": "enum variant",
            "public_path": "pid_core::Metric::Fabricated",
            "removed_api_line": None,
            "semver_1x": False,
            "stable_namespace_leak": True,
        }
    )
elif mutation == "bad_state":
    scope["scope_state"] = "complete"
elif mutation == "remove_parallel":
    scope["feature_profiles"] = [item for item in scope["feature_profiles"] if item["id"] != "pid-core-parallel"]
elif mutation == "bad_semver":
    next(item for item in scope["families"] if item["id"] == "pid-core.stable.continuous")["semver_1x"] = False
elif mutation == "bad_path":
    scope["feature_profiles"][0]["public_api_snapshot"] = "../outside.txt"
elif mutation == "fabricated_tool":
    scope["api_snapshot_source"]["tool"] = "cargo-public-api 99.99.99"
elif mutation == "old_snapshot_source":
    scope["api_snapshot_source"]["commit_sha"] = "ad489f5bf5e15c164c599d069a6bee0f338c0e48"
    scope["api_snapshot_source"]["tree_sha"] = "058a70399c461b02b913b0a9924ffd048fe8c18b"
elif mutation == "partial_approval":
    scope["review_approvals"][0]["reviewer"] = "Sepehr Mahmoudian"
elif mutation in {"wrong_approval_commit", "missing_conflict", "missing_evidence"}:
    approval = scope["review_approvals"][0]
    approval.update(
        {
            "status": "approved",
            "reviewer": "Sepehr Mahmoudian",
            "commit_sha": scope["api_snapshot_source"]["commit_sha"],
            "evidence": "README.md",
            "conflict_disclosure": "Maintainer and author.",
        }
    )
    if mutation == "wrong_approval_commit":
        approval["commit_sha"] = "ad489f5bf5e15c164c599d069a6bee0f338c0e48"
    elif mutation == "missing_conflict":
        approval["conflict_disclosure"] = None
    else:
        approval["evidence"] = "audit/reviews/does-not-exist.md"
elif mutation == "duplicate_key":
    raw = source.read_text(encoding="utf-8")
    destination.write_text(raw.replace("{\n", '{\n  "release": "1.0.0",\n', 1), encoding="utf-8")
    raise SystemExit(0)
else:
    raise SystemExit(f"unknown mutation: {mutation}")
destination.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
  case "$mutation" in
    wrong_feature) expected="feature label disagrees" ;;
    fabricated_leak) expected="exact added API line disagrees" ;;
    bad_state) expected="JSON Schema validation failed" ;;
    remove_parallel) expected="feature profile set mismatch" ;;
    bad_semver) expected="stable families must enter the proposed 1.x SemVer scope" ;;
    bad_path) expected="JSON Schema validation failed" ;;
    duplicate_key) expected="duplicate JSON object key" ;;
    fabricated_tool|old_snapshot_source) expected="JSON Schema validation failed" ;;
    partial_approval) expected="pending review fields must all remain null" ;;
    wrong_approval_commit) expected="review commit must equal the frozen api_snapshot_source commit" ;;
    missing_conflict) expected="a decided review requires reviewer, commit, evidence, and conflict disclosure" ;;
    missing_evidence) expected="review evidence: file is missing or escapes the repository" ;;
  esac
  if python3 "$SCRIPT_DIR/check-release-scope.py" \
    --scope "$TMP/scope.json" --print-markdown >"$TMP/stdout" 2>"$TMP/stderr"
  then
    echo "scope mutation $mutation was accepted" >&2
    exit 1
  fi
  if ! grep -F "$expected" "$TMP/stderr" >/dev/null; then
    echo "scope mutation $mutation failed for the wrong reason" >&2
    sed -n '1,20p' "$TMP/stderr" >&2
    exit 1
  fi
done

for mutation in \
  registry_digest_mismatch registry_revision_gap registry_negative_epoch registry_bool_epoch \
  registry_profile_digest registry_source_tree_mismatch registry_generation_mismatch \
  registry_revision_path_mismatch \
  registry_identity_mismatch registry_source_mismatch registry_unsorted_profiles \
  registry_trailing_newline registry_non_finite registry_duplicate_key registry_noncanonical
do
  python3 - \
    "$REPO_ROOT/release-scope-1.0.json" \
    "$REPO_ROOT/audit/api/public-api/pid-core-signature-revisions.json" \
    "$TMP/scope.json" "$TMP/signature-registry.json" "$mutation" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

scope_source = Path(sys.argv[1])
registry_source = Path(sys.argv[2])
scope_destination = Path(sys.argv[3])
registry_destination = Path(sys.argv[4])
mutation = sys.argv[5]
scope = json.loads(scope_source.read_text(encoding="utf-8"))
registry = json.loads(registry_source.read_text(encoding="utf-8"))

if mutation in {"registry_digest_mismatch", "registry_profile_digest"}:
    registry["entries"][-1]["profiles"][0]["public_api_snapshot_sha256"] = "0" * 64
elif mutation == "registry_revision_gap":
    registry["entries"][0]["revision"] = 2
elif mutation == "registry_negative_epoch":
    registry["entries"][0]["epoch"] = -1
elif mutation == "registry_bool_epoch":
    registry["entries"][0]["epoch"] = True
elif mutation == "registry_source_tree_mismatch":
    registry["entries"][-1]["snapshot_source_tree_sha"] = "0" * 40
elif mutation == "registry_generation_mismatch":
    registry["entries"][-1]["generation"]["tool"] = "cargo-public-api 0.52.1"
elif mutation == "registry_revision_path_mismatch":
    registry["entries"][-1]["profiles"][0]["public_api_snapshot"] = (
        registry["entries"][-1]["profiles"][0]["public_api_snapshot"].replace(
            "/revisions/0-1/", "/revisions/0-2/"
        )
    )
elif mutation == "registry_identity_mismatch":
    registry["entries"][-1]["status"] = "candidate"
elif mutation == "registry_source_mismatch":
    registry["entries"][-1]["snapshot_source_commit_sha"] = (
        "736dac547b1cd9213ebc42d822f138bb59cbfc26"
    )
    registry["entries"][-1]["snapshot_source_tree_sha"] = (
        "1ba78ac12ad657e32c0c315813314edcaee88b7b"
    )
elif mutation == "registry_unsorted_profiles":
    registry["entries"][-1]["profiles"].reverse()
elif mutation == "registry_trailing_newline":
    registry["entries"][-1]["scope"] += "\n"
elif mutation == "registry_non_finite":
    registry["entries"][-1]["revision"] = float("nan")
elif mutation == "registry_duplicate_key":
    raw = registry_source.read_text(encoding="utf-8")
    registry_destination.write_text(
        raw.replace("{\n", '{\n  "package": "pid-core",\n', 1),
        encoding="utf-8",
    )
elif mutation == "registry_noncanonical":
    registry_destination.write_text(
        registry_source.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )
else:
    raise SystemExit(f"unknown registry mutation: {mutation}")

if mutation not in {"registry_duplicate_key", "registry_noncanonical"}:
    registry_destination.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

if mutation != "registry_digest_mismatch":
    scope["public_rust_api_signature_revision_registry"]["canonical_json_sha256"] = (
        hashlib.sha256(registry_destination.read_bytes()).hexdigest()
    )
scope_destination.write_text(
    json.dumps(scope, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
  case "$mutation" in
    registry_digest_mismatch) expected="signature revision registry digest mismatch" ;;
    registry_revision_gap) expected="must begin at epoch 0 revision 1" ;;
    registry_negative_epoch) expected="epoch must be non-negative and revision positive integers" ;;
    registry_bool_epoch) expected="signature registry JSON Schema validation failed" ;;
    registry_profile_digest) expected="retained snapshot digest mismatch" ;;
    registry_source_tree_mismatch) expected="source tree does not match its commit" ;;
    registry_generation_mismatch) expected="generation metadata does not equal api_snapshot_source" ;;
    registry_revision_path_mismatch) expected="snapshot path must be in audit/api/public-api/revisions/0-1" ;;
    registry_identity_mismatch) expected="does not equal the latest signature revision entry" ;;
    registry_source_mismatch) expected="does not equal api_snapshot_source" ;;
    registry_unsorted_profiles) expected="profiles must have sorted unique ids" ;;
    registry_trailing_newline) expected="signature registry JSON Schema validation failed" ;;
    registry_non_finite) expected="non-finite JSON number is forbidden" ;;
    registry_duplicate_key) expected="duplicate JSON object key" ;;
    registry_noncanonical) expected="is not canonical sorted two-space JSON" ;;
  esac
  if python3 "$SCRIPT_DIR/check-release-scope.py" \
    --scope "$TMP/scope.json" \
    --signature-registry "$TMP/signature-registry.json" \
    --print-markdown >"$TMP/stdout" 2>"$TMP/stderr"
  then
    echo "signature registry mutation $mutation was accepted" >&2
    exit 1
  fi
  if ! grep -F "$expected" "$TMP/stderr" >/dev/null; then
    echo "signature registry mutation $mutation failed for the wrong reason" >&2
    sed -n '1,20p' "$TMP/stderr" >&2
    exit 1
  fi
done

# The shared schema subset treats every pattern as a complete-string constraint, and all three
# release-scope JSON loading paths reject Python's otherwise accepted NaN/Infinity spellings.
python3 - "$SCRIPT_DIR/check-release-scope.py" "$TMP" <<'PY'
import importlib.util
from pathlib import Path
import sys

script = Path(sys.argv[1])
tmp = Path(sys.argv[2])
sys.path.insert(0, str(script.parent))
spec = importlib.util.spec_from_file_location("check_release_scope_json", script)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

from json_schema_subset import (
    InstanceValidationError,
    SchemaDefinitionError,
    SchemaValidationError,
    validate,
)


pattern_schema = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
validate("a" * 40, pattern_schema, name="exact digest")
for invalid in ("a" * 40 + "\n", "prefix" + "a" * 40):
    try:
        validate(invalid, pattern_schema, name="mutated digest")
    except SchemaValidationError as error:
        if "does not match pattern" not in str(error):
            raise SystemExit(f"full-match pattern failed for the wrong reason: {error}")
    else:
        raise SystemExit("non-full schema pattern match was accepted")


def expect_schema_definition_error(label, schema, expected):
    try:
        validate("accepted", schema, name=label)
    except SchemaDefinitionError as error:
        if expected not in str(error):
            raise SystemExit(f"{label} failed for the wrong reason: {error}")
    except SchemaValidationError as error:
        raise SystemExit(f"{label} was not typed as a schema-definition error: {error}")
    else:
        raise SystemExit(f"{label} invalid schema was accepted")


# Schema-definition failures are evaluated independently of the instance. In particular, oneOf
# must never swallow an unsupported branch just because another branch matches.
expect_schema_definition_error(
    "invalid oneOf branch",
    {"oneOf": [{"type": "string"}, {"unsupported_keyword": True}]},
    "unsupported schema keyword",
)
expect_schema_definition_error(
    "non-boolean uniqueItems",
    {"type": "array", "uniqueItems": "true"},
    "uniqueItems must be a boolean",
)
expect_schema_definition_error(
    "non-schema additionalProperties",
    {"type": "object", "additionalProperties": "false"},
    "additionalProperties must be a boolean or object",
)

validate(
    "accepted",
    {"oneOf": [{"type": "string"}, {"type": "integer"}]},
    name="valid oneOf",
)
try:
    validate(
        True,
        {"oneOf": [{"type": "string"}, {"type": "integer"}]},
        name="ordinary oneOf mismatch",
    )
except InstanceValidationError as error:
    if "expected exactly one oneOf match" not in str(error):
        raise SystemExit(f"ordinary oneOf mismatch failed for the wrong reason: {error}")
except SchemaValidationError as error:
    raise SystemExit(f"ordinary oneOf mismatch was misclassified: {error}")
else:
    raise SystemExit("ordinary oneOf mismatch was accepted")

non_finite = tmp / "non-finite.json"
for spelling in ("NaN", "Infinity", "-Infinity"):
    non_finite.write_text(spelling + "\n", encoding="utf-8")
    operations = (
        lambda: module.load_json(non_finite, canonical=True),
        lambda: module.load_json_with_sha256(non_finite, canonical=True),
        lambda: module.load_canonical_json_text(
            non_finite.read_text(encoding="utf-8"), label="non-finite fixture"
        ),
    )
    for operation in operations:
        try:
            operation()
        except module.ScopeError as error:
            if "non-finite JSON number is forbidden" not in str(error):
                raise SystemExit(f"non-finite JSON failed for the wrong reason: {error}")
        else:
            raise SystemExit(f"non-finite JSON spelling was accepted: {spelling}")
    try:
        validate(float(spelling), {"type": "number"}, name="non-finite instance")
    except SchemaValidationError as error:
        if "non-finite JSON numbers are forbidden" not in str(error):
            raise SystemExit(f"non-finite instance failed for the wrong reason: {error}")
    else:
        raise SystemExit(f"non-finite in-memory instance was accepted: {spelling}")
PY

# A stable item that exists only when features are combined must be rejected by the complete
# activation-profile comparison, even if every individual feature profile looks unchanged.
python3 - "$SCRIPT_DIR/check-release-scope.py" <<'PY'
import importlib.util
from pathlib import Path
import sys

script = Path(sys.argv[1])
sys.path.insert(0, str(script.parent))
spec = importlib.util.spec_from_file_location("check_release_scope", script)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

default = "pub struct pid_core::Stable\n"
combined = default + "pub fn pid_core::Stable::interaction_only()\n"
members = [
    {
        "feature": "feature-a",
        "added_api_line": "pub fn pid_core::Stable::listed()",
        "removed_api_line": None,
    }
]
try:
    module.validate_stable_profile_diff(
        "combined-profile",
        {"feature-a", "feature-b"},
        default,
        combined,
        members,
    )
except module.ScopeError as error:
    if "unlisted added" not in str(error):
        raise SystemExit(f"combined-feature mutation failed for the wrong reason: {error}")
else:
    raise SystemExit("combined-feature stable API mutation was accepted")

# Generic impls are impl records too. An impl belongs to the stable comparison when either its
# implemented trait or self type names a non-experimental pid-core path.
generic_impl_mutations = (
    "impl<T> pid_core::stable::Marker for pid_core::experimental::Thing<T>",
    "impl<T> pid_core::experimental::Marker for pid_core::stable::Thing<T>",
    "impl<'a> pid_core::stable::Thing<'a>",
)
for api_line in generic_impl_mutations:
    try:
        module.validate_stable_profile_diff(
            "generic-impl-profile",
            set(),
            default,
            default + api_line + "\n",
            [],
        )
    except module.ScopeError as error:
        if "unlisted added" not in str(error):
            raise SystemExit(f"generic impl mutation failed for the wrong reason: {error}")
    else:
        raise SystemExit(f"stable generic impl mutation was accepted: {api_line}")

experimental_impl = (
    "impl<T: pid_core::stable::Marker> pid_core::experimental::Marker "
    "for pid_core::experimental::Thing<T>"
)
if experimental_impl in module.stable_namespace_lines(experimental_impl + "\n"):
    raise SystemExit("a stable generic bound misclassified an experimental trait/self impl")
PY

# Exercise the future-update path even though revision 1 is the first checked-in registry entry.
python3 - \
  "$SCRIPT_DIR/check-release-scope.py" \
  "$REPO_ROOT/audit/api/public-api/pid-core-signature-revisions.json" <<'PY'
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

script = Path(sys.argv[1])
registry_path = Path(sys.argv[2])
sys.path.insert(0, str(script.parent))
spec = importlib.util.spec_from_file_location("check_release_scope", script)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

original = json.loads(registry_path.read_text(encoding="utf-8"))["entries"]
historical = deepcopy(original)

genesis_source = {
    "commit_sha": historical[0]["snapshot_source_commit_sha"],
    "tree_sha": historical[0]["snapshot_source_tree_sha"],
}
module.validate_signature_registry_genesis(
    genesis_source,
    historical_registry_present=False,
)
future_source = {"commit_sha": "0" * 40, "tree_sha": "1" * 40}
try:
    module.validate_signature_registry_genesis(
        future_source,
        historical_registry_present=False,
    )
except module.ScopeError as error:
    if "immutable genesis source" not in str(error):
        raise SystemExit(f"registry genesis failed for the wrong reason: {error}")
else:
    raise SystemExit("a later source without registry history was accepted as genesis")
module.validate_signature_registry_genesis(
    future_source,
    historical_registry_present=True,
)


def expect_failure(expected, current):
    try:
        module.validate_signature_registry_extension(current, historical)
    except module.ScopeError as error:
        if expected not in str(error):
            raise SystemExit(f"registry extension failed for the wrong reason: {error}")
    else:
        raise SystemExit(f"registry extension unexpectedly accepted: {expected}")


rewritten = deepcopy(historical)
rewritten[0]["status"] = "rewritten"
expect_failure("does not preserve", rewritten)

same_signature = deepcopy(historical)
same_signature.append(deepcopy(historical[-1]))
same_signature[-1]["revision"] += 1
expect_failure("pure signature revision-number bump", same_signature)

path_only = deepcopy(same_signature)
path_only[-1]["profiles"][0]["public_api_snapshot"] = (
    "audit/api/public-api/revisions/0-2/path-only.txt"
)
expect_failure("pure signature revision-number bump", path_only)

status_transition = deepcopy(same_signature)
status_transition[-1]["status"] = "candidate"
module.validate_signature_registry_extension(status_transition, historical)

scope_transition = deepcopy(same_signature)
scope_transition[-1]["scope"] = "candidate_profiles"
module.validate_signature_registry_extension(scope_transition, historical)

epoch_transition = deepcopy(historical)
epoch_transition.append(deepcopy(historical[-1]))
epoch_transition[-1]["epoch"] += 1
epoch_transition[-1]["revision"] = 1
module.validate_signature_registry_extension(epoch_transition, historical)

multiple = deepcopy(same_signature)
multiple[-1]["profiles"][0]["public_api_snapshot_sha256"] = "0" * 64
multiple.append(deepcopy(multiple[-1]))
multiple[-1]["revision"] += 1
expect_failure("at most one contiguous", multiple)

first_update_with_history = deepcopy(historical)
first_update_with_history.append(deepcopy(historical[-1]))
try:
    module.validate_signature_registry_extension(first_update_with_history, [])
except module.ScopeError as error:
    if "first signature registry update" not in str(error):
        raise SystemExit(f"first-update extension failed for the wrong reason: {error}")
else:
    raise SystemExit("first registry update accepted fabricated history")

expect_failure("does not preserve", [])

valid = deepcopy(same_signature)
valid[-1]["profiles"][0]["public_api_snapshot_sha256"] = "0" * 64
module.validate_signature_registry_extension(valid, historical)
PY

# Exercise ancestry, retained-byte, and checkout-history invariants in an isolated Git graph.
python3 - \
  "$SCRIPT_DIR/check-release-scope.py" \
  "$REPO_ROOT/audit/schemas/public-rust-api-signature-revisions.schema.json" \
  "$TMP" <<'PY'
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

script = Path(sys.argv[1])
schema_path = Path(sys.argv[2])
root = Path(sys.argv[3]) / "signature-history-repo"
root.mkdir()
sys.path.insert(0, str(script.parent))
spec = importlib.util.spec_from_file_location("check_release_scope_history", script)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def fixture_git(repo, *args, input_text=None):
    environment = module.scrubbed_git_environment()
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
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    process = subprocess.run(
        [
            "git",
            "-c",
            "advice.graftFileDeprecated=false",
            "-c",
            "commit.gpgsign=false",
            "-c",
            f"core.attributesFile={os.devnull}",
            "-c",
            "core.fsmonitor=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        cwd=repo,
        env=environment,
        check=False,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if process.returncode != 0:
        raise SystemExit(
            f"scratch Git {' '.join(args)} failed: "
            f"{process.stderr.strip() or process.stdout.strip()}"
        )
    return process.stdout.strip()


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def expect_failure(expected, operation):
    try:
        operation()
    except module.ScopeError as error:
        if expected not in str(error):
            raise SystemExit(f"history invariant failed for the wrong reason: {error}")
    else:
        raise SystemExit(f"history invariant unexpectedly accepted: {expected}")


poison_hooks = root.parent / "poison-hooks"
poison_hooks.mkdir()
(poison_hooks / "pre-commit").write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
(poison_hooks / "pre-commit").chmod(0o700)
poison_worktree = root.parent / "poison-worktree"
poison_worktree.mkdir()
poison_config = root.parent / "poison.gitconfig"
poison_config.write_text(
    "[commit]\n"
    "\tgpgSign = true\n"
    "[core]\n"
    f"\thooksPath = {poison_hooks.as_posix()}\n"
    f"\tworktree = {poison_worktree.as_posix()}\n",
    encoding="utf-8",
)
poisoned_fixture_environment = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(root.parent / "ambient-alternate-objects"),
    "GIT_AUTHOR_EMAIL": "ambient-author@example.invalid",
    "GIT_AUTHOR_NAME": "Ambient Author",
    "GIT_ATTR_NOSYSTEM": "0",
    "GIT_ATTR_SOURCE": "refs/heads/ambient-attributes",
    "GIT_CEILING_DIRECTORIES": str(root.parent),
    "GIT_COMMON_DIR": str(root.parent / "ambient-common.git"),
    "GIT_CONFIG": str(poison_config),
    "GIT_CONFIG_COUNT": "3",
    "GIT_CONFIG_GLOBAL": str(poison_config),
    "GIT_CONFIG_KEY_0": "commit.gpgsign",
    "GIT_CONFIG_KEY_1": "core.hooksPath",
    "GIT_CONFIG_KEY_2": "core.worktree",
    "GIT_CONFIG_SYSTEM": str(poison_config),
    "GIT_CONFIG_VALUE_0": "true",
    "GIT_CONFIG_VALUE_1": str(poison_hooks),
    "GIT_CONFIG_VALUE_2": str(poison_worktree),
    "GIT_CONFIG_PARAMETERS": f"'core.worktree={poison_worktree.as_posix()}'",
    "GIT_DIR": str(root.parent / "ambient.git"),
    "GIT_DISCOVERY_ACROSS_FILESYSTEM": "1",
    "GIT_EXEC_PATH": str(root.parent / "ambient-git-exec-path"),
    "GIT_GLOB_PATHSPECS": "1",
    "GIT_GRAFT_FILE": str(root.parent / "ambient-grafts"),
    "GIT_INDEX_FILE": str(root.parent / "ambient-index"),
    "GIT_COMMITTER_EMAIL": "ambient-committer@example.invalid",
    "GIT_COMMITTER_NAME": "Ambient Committer",
    "GIT_NAMESPACE": "ambient-namespace",
    "GIT_NO_LAZY_FETCH": "0",
    "GIT_NO_REPLACE_OBJECTS": "0",
    "GIT_OBJECT_DIRECTORY": str(root.parent / "ambient-objects"),
    "GIT_QUARANTINE_PATH": str(root.parent / "ambient-quarantine"),
    "GIT_REFERENCE_BACKEND": "ambient-reference-backend",
    "GIT_REPLACE_REF_BASE": "refs/ambient-replacements/",
    "GIT_SHALLOW_FILE": str(root.parent / "ambient-shallow"),
    "GIT_TEMPLATE_DIR": str(poison_hooks),
    "GIT_WORK_TREE": str(poison_worktree),
}
prior_fixture_environment = {
    name: os.environ.get(name) for name in poisoned_fixture_environment
}
try:
    os.environ.update(poisoned_fixture_environment)
    fixture_git(root, "init", "-q", "-b", "main")
    fixture_git(root, "config", "user.name", "PID Test")
    fixture_git(root, "config", "user.email", "pid-test@example.invalid")
finally:
    for name, prior in prior_fixture_environment.items():
        if prior is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = prior
revision_one = root / "audit/api/public-api/revisions/0-1/pid-core-default.txt"
revision_one.parent.mkdir(parents=True)
revision_one.write_text("pub struct pid_core::Stable\n", encoding="utf-8")
fixture_git(root, "add", ".")
try:
    os.environ.update(poisoned_fixture_environment)
    fixture_git(
        root,
        "commit",
        "-q",
        "--no-gpg-sign",
        "--no-verify",
        "-m",
        "source one",
    )
finally:
    for name, prior in prior_fixture_environment.items():
        if prior is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = prior
source_one = fixture_git(root, "rev-parse", "HEAD")
tree_one = fixture_git(root, "rev-parse", "HEAD^{tree}")
source_one_object = fixture_git(root, "cat-file", "-p", source_one)
source_one_headers = source_one_object.split("\n\n", 1)[0].splitlines()
if any(line.startswith("gpgsig ") for line in source_one_headers):
    raise SystemExit("fixture Git wrapper allowed commit signing")
if not any(
    line.startswith("author PID Test <pid-test@example.invalid> ")
    for line in source_one_headers
) or not any(
    line.startswith("committer PID Test <pid-test@example.invalid> ")
    for line in source_one_headers
):
    raise SystemExit("fixture Git wrapper accepted ambient author identity")

revision_two = root / "audit/api/public-api/revisions/0-2/pid-core-default.txt"
revision_two.parent.mkdir(parents=True)
revision_two.write_bytes(revision_one.read_bytes())
fixture_git(root, "add", ".")
fixture_git(root, "commit", "-q", "--no-gpg-sign", "--no-verify", "-m", "source two")
source_two = fixture_git(root, "rev-parse", "HEAD")
tree_two = fixture_git(root, "rev-parse", "HEAD^{tree}")
snapshot_digest = hashlib.sha256(revision_one.read_bytes()).hexdigest()
generation = {
    "host_triple": "test-host",
    "rustdoc_target_triple": "test-target",
    "snapshot_format": "test-format",
    "tool": "test-tool",
    "toolchain": "test-toolchain",
}


def entry(epoch, revision, status, commit, tree, relative, digest=snapshot_digest):
    return {
        "epoch": epoch,
        "generation": deepcopy(generation),
        "profiles": [
            {
                "id": "pid-core-default",
                "public_api_snapshot": relative,
                "public_api_snapshot_sha256": digest,
            }
        ],
        "revision": revision,
        "scope": "test_profiles",
        "snapshot_source_commit_sha": commit,
        "snapshot_source_tree_sha": tree,
        "status": status,
    }


entry_one = entry(
    0,
    1,
    "review",
    source_one,
    tree_one,
    "audit/api/public-api/revisions/0-1/pid-core-default.txt",
)
entry_two = entry(
    0,
    2,
    "candidate",
    source_two,
    tree_two,
    "audit/api/public-api/revisions/0-2/pid-core-default.txt",
)
module.validate_signature_registry_entries(
    [entry_one, entry_two], root=root, observations={}
)

boolean_epoch = deepcopy(entry_one)
boolean_epoch["epoch"] = True
expect_failure(
    "epoch must be non-negative and revision positive integers",
    lambda: module.validate_signature_registry_entries(
        [boolean_epoch], root=root, observations={}
    ),
)

reversed_sources = [deepcopy(entry_one), deepcopy(entry_two)]
reversed_sources[0]["snapshot_source_commit_sha"] = source_two
reversed_sources[0]["snapshot_source_tree_sha"] = tree_two
reversed_sources[1]["snapshot_source_commit_sha"] = source_one
reversed_sources[1]["snapshot_source_tree_sha"] = tree_one
expect_failure(
    "source commits are not monotone by ancestry",
    lambda: module.validate_signature_registry_entries(
        reversed_sources, root=root, observations={}
    ),
)

unrelated = fixture_git(root, "commit-tree", tree_two, input_text="unrelated source\n")
unrelated_source = [deepcopy(entry_one), deepcopy(entry_two)]
unrelated_source[1]["snapshot_source_commit_sha"] = unrelated
expect_failure(
    "source commit is not an ancestor of HEAD",
    lambda: module.validate_signature_registry_entries(
        unrelated_source, root=root, observations={}
    ),
)

original_one = revision_one.read_bytes()
revision_one.write_bytes(b"tampered retained bytes\n")
expect_failure(
    "retained snapshot digest mismatch",
    lambda: module.validate_signature_registry_entries(
        [entry_one], root=root, observations={}
    ),
)
revision_one.write_bytes(original_one)

original_two = revision_two.read_bytes()
revision_two.write_bytes(b"different declaration bytes\n")
different_digest = hashlib.sha256(revision_two.read_bytes()).hexdigest()
same_source_change = [deepcopy(entry_one), deepcopy(entry_two)]
same_source_change[1]["snapshot_source_commit_sha"] = source_one
same_source_change[1]["snapshot_source_tree_sha"] = tree_one
same_source_change[1]["profiles"][0]["public_api_snapshot_sha256"] = different_digest
expect_failure(
    "unchanged source and generation cannot produce a different declaration signature",
    lambda: module.validate_signature_registry_entries(
        same_source_change, root=root, observations={}
    ),
)
revision_two.write_bytes(original_two)

registry_one = {
    "append_policy": "strict_prefix_by_epoch_revision",
    "entries": [entry_one],
    "genesis_source_commit_sha": module.SIGNATURE_REGISTRY_GENESIS_SOURCE_COMMIT,
    "genesis_source_tree_sha": module.SIGNATURE_REGISTRY_GENESIS_SOURCE_TREE,
    "package": "pid-core",
    "schema": module.SIGNATURE_REGISTRY_SCHEMA,
    "schema_revision": module.SIGNATURE_REGISTRY_SCHEMA_REVISION,
}
registry_path = root / module.SIGNATURE_REGISTRY_PATH
registry_path.parent.mkdir(parents=True, exist_ok=True)
registry_path.write_text(canonical(registry_one), encoding="utf-8")
fixture_git(root, "add", ".")
fixture_git(root, "commit", "-q", "--no-gpg-sign", "--no-verify", "-m", "evidence one")
evidence_commit = fixture_git(root, "rev-parse", "HEAD")

rewritten_registry = deepcopy(registry_one)
rewritten_registry["entries"][0]["status"] = "rewritten"
registry_path.write_text(canonical(rewritten_registry), encoding="utf-8")
fixture_git(root, "add", str(registry_path.relative_to(root)))
fixture_git(root, "commit", "-q", "--no-gpg-sign", "--no-verify", "-m", "rewrite evidence")
rewrite_commit = fixture_git(root, "rev-parse", "HEAD")
history = module.checkout_history_commits(root)
if history != [("HEAD", rewrite_commit), ("HEAD^1", evidence_commit)]:
    raise SystemExit(f"checkout history boundary mismatch: {history!r}")

schema = module.load_json(schema_path)
parent_raw = module.git_file_at_commit(
    root, evidence_commit, module.SIGNATURE_REGISTRY_PATH
)
assert parent_raw is not None
expect_failure(
    "does not preserve",
    lambda: module.validate_signature_registry_history_text(
        rewritten_registry,
        parent_raw,
        registry_schema=schema,
        history_label="HEAD^1 fixture",
    ),
)
expect_failure(
    "truncation or rewrite",
    lambda: module.validate_signature_registry_historical_lineage(
        {
            evidence_commit: ("HEAD^1", registry_one),
            rewrite_commit: ("HEAD", rewritten_registry),
        },
        root=root,
    ),
)

registry_two = deepcopy(registry_one)
registry_two["entries"].append(entry_two)
expect_failure(
    "truncation or rewrite",
    lambda: module.validate_signature_registry_historical_lineage(
        {
            evidence_commit: ("older", registry_two),
            rewrite_commit: ("newer", registry_one),
        },
        root=root,
    ),
)


def initialize_history_repo(name):
    repo = root.parent / name
    repo.mkdir()
    fixture_git(repo, "init", "-q", "-b", "main")
    fixture_git(repo, "config", "user.name", "PID Test")
    fixture_git(repo, "config", "user.email", "pid-test@example.invalid")
    return repo


def commit_registry(repo, value, message):
    path = repo / module.SIGNATURE_REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value), encoding="utf-8")
    fixture_git(repo, "add", str(path.relative_to(repo)))
    fixture_git(repo, "commit", "-q", "--no-gpg-sign", "--no-verify", "-m", message)
    return fixture_git(repo, "rev-parse", "HEAD")


def validate_presented_history(repo, current):
    histories = {}
    for label, commit in module.checkout_history_commits(repo):
        raw = module.git_file_at_commit(repo, commit, module.SIGNATURE_REGISTRY_PATH)
        if raw is None:
            histories[commit] = (label, None)
            continue
        historical = module.validate_signature_registry_history_text(
            current,
            raw,
            registry_schema=schema,
            history_label=f"{label} fixture",
        )
        histories[commit] = (label, historical)
    module.validate_signature_registry_historical_lineage(histories, root=repo)


# A truncation hidden below HEAD followed by a different reissue of the same epoch/revision must
# remain visible because every registry-touch commit reachable from HEAD is examined.
linear_repo = initialize_history_repo("signature-linear-buried-rewrite")
linear_one = commit_registry(linear_repo, registry_one, "linear evidence one")
linear_two = commit_registry(linear_repo, registry_two, "linear evidence two")
linear_truncation = commit_registry(
    linear_repo, registry_one, "linear buried truncation"
)
linear_reissue = deepcopy(registry_two)
linear_head = commit_registry(linear_repo, linear_reissue, "linear reissue")
linear_witnesses = {commit for _, commit in module.checkout_history_commits(linear_repo)}
if not {linear_one, linear_two, linear_truncation, linear_head}.issubset(
    linear_witnesses
):
    raise SystemExit("full linear registry-touch history was not enumerated")
expect_failure(
    "truncation or rewrite",
    lambda: validate_presented_history(linear_repo, linear_reissue),
)

# A merge cannot drop an entry from its second parent, nor can a later commit conceal that drop by
# reissuing the same epoch/revision with different content.
merge_repo = initialize_history_repo("signature-merge-side-rewrite")
commit_registry(merge_repo, registry_one, "merge base evidence")
fixture_git(merge_repo, "branch", "side")
unrelated = merge_repo / "main-only.txt"
unrelated.write_text("main\n", encoding="utf-8")
fixture_git(merge_repo, "add", "main-only.txt")
fixture_git(
    merge_repo,
    "commit",
    "-q",
    "--no-gpg-sign",
    "--no-verify",
    "-m",
    "main-only change",
)
main_parent = fixture_git(merge_repo, "rev-parse", "HEAD")
fixture_git(merge_repo, "switch", "-q", "side")
side_entry = commit_registry(merge_repo, registry_two, "side evidence two")
fixture_git(merge_repo, "switch", "-q", "main")
fixture_git(
    merge_repo,
    "merge",
    "-q",
    "--no-ff",
    "--no-gpg-sign",
    "--no-verify",
    "-s",
    "ours",
    "side",
    "-m",
    "drop side evidence",
)
merge_commit = fixture_git(merge_repo, "rev-parse", "HEAD")
merge_witnesses = module.checkout_history_commits(merge_repo)
if merge_witnesses[:3] != [
    ("HEAD", merge_commit),
    ("HEAD^1", main_parent),
    ("HEAD^2", side_entry),
]:
    raise SystemExit(f"all direct merge parents were not enumerated: {merge_witnesses!r}")
expect_failure(
    "does not preserve",
    lambda: validate_presented_history(merge_repo, registry_one),
)

merge_reissue = deepcopy(registry_two)
commit_registry(merge_repo, merge_reissue, "reissue dropped side evidence")
merge_witness_ids = {commit for _, commit in module.checkout_history_commits(merge_repo)}
if not {side_entry, merge_commit}.issubset(merge_witness_ids):
    raise SystemExit("merge-side registry states disappeared from full path history")
expect_failure(
    "truncation or rewrite",
    lambda: validate_presented_history(merge_repo, merge_reissue),
)


snapshot_relative = entry_one["profiles"][0]["public_api_snapshot"]
snapshot_bytes = revision_one.read_bytes()
changed_snapshot_bytes = b"pub struct pid_core::Changed;\n"


def commit_all(repo, message):
    fixture_git(repo, "add", "-A")
    fixture_git(repo, "commit", "-q", "--no-gpg-sign", "--no-verify", "-m", message)
    return fixture_git(repo, "rev-parse", "HEAD")


def write_snapshot(repo, content):
    path = repo / snapshot_relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def write_registry(repo, value):
    path = repo / module.SIGNATURE_REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value), encoding="utf-8")
    return path


def commit_marker(repo, message):
    marker = repo / f"marker-{message.replace(' ', '-')}.txt"
    marker.write_text(f"{message}\n", encoding="utf-8")
    return commit_all(repo, message)


def initialize_snapshot_repo(name, *, prebinding_content=None):
    repo = initialize_history_repo(name)
    commit_marker(repo, "base")
    if prebinding_content is not None:
        write_snapshot(repo, prebinding_content)
        commit_all(repo, "pre-binding snapshot")
    write_snapshot(repo, snapshot_bytes)
    write_registry(repo, registry_one)
    binding = commit_all(repo, "bind snapshot")
    return repo, binding


def snapshot_registry_histories(repo, current):
    histories = {}
    for label, commit in module.checkout_history_commits(repo):
        raw = module.git_file_at_commit(repo, commit, module.SIGNATURE_REGISTRY_PATH)
        if raw is None:
            histories.setdefault(commit, (label, None))
            continue
        historical = module.validate_signature_registry_history_text(
            current,
            raw,
            registry_schema=schema,
            history_label=f"{label} snapshot fixture",
        )
        histories.setdefault(commit, (label, historical))
    return histories


def validate_presented_snapshot_history(repo, current=registry_one):
    histories = snapshot_registry_histories(repo, current)
    module.validate_signature_snapshot_history(
        current["entries"], histories=histories, root=repo
    )


# Wrong content cannot be hidden by restoring the checked-out bytes. The unrelated tip keeps the
# changed state outside the direct-HEAD-parent boundary, so the snapshot path walk must find it.
modify_repo, _ = initialize_snapshot_repo("signature-snapshot-modify-restore")
write_snapshot(modify_repo, changed_snapshot_bytes)
changed_commit = commit_all(modify_repo, "change bound snapshot")
write_snapshot(modify_repo, snapshot_bytes)
commit_all(modify_repo, "restore bound snapshot")
commit_marker(modify_repo, "after restore")
modify_witnesses = {
    commit
    for _, commit in module.checkout_path_history_commits(
        modify_repo, snapshot_relative, touch_label="snapshot-touch"
    )
}
if changed_commit not in modify_witnesses:
    raise SystemExit("full snapshot path history did not expose restored content")
expect_failure(
    "changed after registry binding",
    lambda: validate_presented_snapshot_history(modify_repo),
)

# Deletion and restoration remains a reachable absence after the binding.
delete_repo, _ = initialize_snapshot_repo("signature-snapshot-delete-restore")
(delete_repo / snapshot_relative).unlink()
deleted_commit = commit_all(delete_repo, "delete bound snapshot")
write_snapshot(delete_repo, snapshot_bytes)
commit_all(delete_repo, "restore deleted snapshot")
commit_marker(delete_repo, "after delete restore")
delete_witnesses = {
    commit
    for _, commit in module.checkout_path_history_commits(
        delete_repo, snapshot_relative, touch_label="snapshot-touch"
    )
}
if deleted_commit not in delete_witnesses:
    raise SystemExit("full snapshot path history did not expose restored deletion")
expect_failure(
    "was absent after registry binding",
    lambda: validate_presented_snapshot_history(delete_repo),
)

# A rename away is a deletion of the bound path even when a later rename restores it.
rename_repo, _ = initialize_snapshot_repo("signature-snapshot-rename-restore")
renamed_relative = f"{snapshot_relative}.moved"
fixture_git(rename_repo, "mv", snapshot_relative, renamed_relative)
renamed_commit = commit_all(rename_repo, "rename bound snapshot away")
fixture_git(rename_repo, "mv", renamed_relative, snapshot_relative)
commit_all(rename_repo, "restore renamed snapshot")
commit_marker(rename_repo, "after rename restore")
rename_witnesses = {
    commit
    for _, commit in module.checkout_path_history_commits(
        rename_repo, snapshot_relative, touch_label="snapshot-touch"
    )
}
if renamed_commit not in rename_witnesses:
    raise SystemExit("full snapshot path history did not expose restored rename")
expect_failure(
    "was absent after registry binding",
    lambda: validate_presented_snapshot_history(rename_repo),
)

# A two-parent merge cannot conceal wrong bytes retained on a merged side branch.
snapshot_merge_repo, snapshot_merge_binding = initialize_snapshot_repo(
    "signature-snapshot-merge-side"
)
fixture_git(snapshot_merge_repo, "branch", "snapshot-side")
commit_marker(snapshot_merge_repo, "main snapshot change")
snapshot_main_parent = fixture_git(snapshot_merge_repo, "rev-parse", "HEAD")
fixture_git(snapshot_merge_repo, "switch", "-q", "snapshot-side")
write_snapshot(snapshot_merge_repo, changed_snapshot_bytes)
snapshot_side_parent = commit_all(snapshot_merge_repo, "side snapshot change")
fixture_git(snapshot_merge_repo, "switch", "-q", "main")
fixture_git(
    snapshot_merge_repo,
    "merge",
    "-q",
    "--no-ff",
    "--no-gpg-sign",
    "--no-verify",
    "-s",
    "ours",
    "snapshot-side",
    "-m",
    "retain main snapshot",
)
snapshot_merge_commit = fixture_git(snapshot_merge_repo, "rev-parse", "HEAD")
snapshot_merge_witnesses = module.checkout_path_history_commits(
    snapshot_merge_repo, snapshot_relative, touch_label="snapshot-touch"
)
if snapshot_merge_witnesses[:3] != [
    ("HEAD", snapshot_merge_commit),
    ("HEAD^1", snapshot_main_parent),
    ("HEAD^2", snapshot_side_parent),
]:
    raise SystemExit(
        f"snapshot merge boundaries were not enumerated: {snapshot_merge_witnesses!r}"
    )
if not module.git_commit_is_ancestor(
    snapshot_merge_repo, snapshot_merge_binding, snapshot_side_parent
):
    raise SystemExit("snapshot binding fixture does not precede its side mutation")
expect_failure(
    "changed after registry binding",
    lambda: validate_presented_snapshot_history(snapshot_merge_repo),
)

# The path boundary walker must retain every parent of an octopus merge, including a third-parent
# mutation discarded by the merge result.
octopus_repo, _ = initialize_snapshot_repo("signature-snapshot-octopus")
fixture_git(octopus_repo, "branch", "octopus-bad")
fixture_git(octopus_repo, "branch", "octopus-clean")
commit_marker(octopus_repo, "octopus main")
octopus_main_parent = fixture_git(octopus_repo, "rev-parse", "HEAD")
fixture_git(octopus_repo, "switch", "-q", "octopus-bad")
write_snapshot(octopus_repo, changed_snapshot_bytes)
octopus_bad_parent = commit_all(octopus_repo, "octopus bad snapshot")
fixture_git(octopus_repo, "switch", "-q", "octopus-clean")
commit_marker(octopus_repo, "octopus clean")
octopus_clean_parent = fixture_git(octopus_repo, "rev-parse", "HEAD")
fixture_git(octopus_repo, "switch", "-q", "main")
fixture_git(
    octopus_repo,
    "merge",
    "-q",
    "--no-ff",
    "--no-gpg-sign",
    "--no-verify",
    "-s",
    "ours",
    "octopus-bad",
    "octopus-clean",
    "-m",
    "retain main snapshot across octopus",
)
octopus_merge = fixture_git(octopus_repo, "rev-parse", "HEAD")
octopus_witnesses = module.checkout_path_history_commits(
    octopus_repo, snapshot_relative, touch_label="snapshot-touch"
)
if octopus_witnesses[:4] != [
    ("HEAD", octopus_merge),
    ("HEAD^1", octopus_main_parent),
    ("HEAD^2", octopus_bad_parent),
    ("HEAD^3", octopus_clean_parent),
]:
    raise SystemExit(f"all octopus parents were not enumerated: {octopus_witnesses!r}")
expect_failure(
    "changed after registry binding",
    lambda: validate_presented_snapshot_history(octopus_repo),
)

# Snapshot history before the binding is outside the immutability interval. Correct bytes at the
# binding and every descendant are valid even when an earlier commit held different content.
prebinding_repo, _ = initialize_snapshot_repo(
    "signature-snapshot-valid-prebinding",
    prebinding_content=changed_snapshot_bytes,
)
commit_marker(prebinding_repo, "valid bound descendant")
validate_presented_snapshot_history(prebinding_repo)

# Genesis evidence may bind its first snapshot only in the working tree. With no committed registry
# binding, current bytes are checked by entry validation and all committed path states are pre-binding.
uncommitted_repo = initialize_history_repo("signature-snapshot-uncommitted-genesis")
uncommitted_source = commit_marker(uncommitted_repo, "uncommitted source")
uncommitted_tree = fixture_git(uncommitted_repo, "rev-parse", "HEAD^{tree}")
uncommitted_entry = deepcopy(entry_one)
uncommitted_entry["snapshot_source_commit_sha"] = uncommitted_source
uncommitted_entry["snapshot_source_tree_sha"] = uncommitted_tree
uncommitted_registry = deepcopy(registry_one)
uncommitted_registry["entries"] = [uncommitted_entry]
write_snapshot(uncommitted_repo, snapshot_bytes)
write_registry(uncommitted_repo, uncommitted_registry)
module.validate_signature_registry_entries(
    uncommitted_registry["entries"], root=uncommitted_repo, observations={}
)
validate_presented_snapshot_history(uncommitted_repo, uncommitted_registry)

# Ambient Git routing, object, config, namespace, shallow, replacement, and pathspec variables must
# not redirect the repository-history evidence away from the root passed to the checker.
ambient_repo = initialize_history_repo("signature-ambient-git-redirection")
ambient_head = commit_marker(ambient_repo, "ambient decoy")
real_head = fixture_git(root, "rev-parse", "HEAD")
if ambient_head == real_head:
    raise SystemExit("ambient Git redirection fixture did not produce a distinct commit")
ambient_config = ambient_repo / "ambient.gitconfig"
ambient_config.write_text(
    f"[core]\n\tworktree = {ambient_repo.as_posix()}\n", encoding="utf-8"
)
poisoned_environment = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(ambient_repo / ".git/objects"),
    "GIT_ATTR_NOSYSTEM": "0",
    "GIT_ATTR_SOURCE": ambient_head,
    "GIT_COMMON_DIR": str(ambient_repo / ".git"),
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_GLOBAL": str(ambient_config),
    "GIT_CONFIG_KEY_0": "core.worktree",
    "GIT_CONFIG_NOSYSTEM": "0",
    "GIT_CONFIG_PARAMETERS": f"'core.worktree={ambient_repo.as_posix()}'",
    "GIT_CONFIG_SYSTEM": str(ambient_config),
    "GIT_CONFIG_VALUE_0": str(ambient_repo),
    "GIT_DIR": str(ambient_repo / ".git"),
    "GIT_GLOB_PATHSPECS": "1",
    "GIT_GRAFT_FILE": str(ambient_repo / ".git/ambient-grafts"),
    "GIT_INDEX_FILE": str(ambient_repo / ".git/index"),
    "GIT_NAMESPACE": "curated-history",
    "GIT_NO_LAZY_FETCH": "0",
    "GIT_NO_REPLACE_OBJECTS": "0",
    "GIT_OBJECT_DIRECTORY": str(ambient_repo / ".git/objects"),
    "GIT_REFERENCE_BACKEND": "files:///ambient/reference/store",
    "GIT_REPLACE_REF_BASE": "refs/curated-replacements/",
    "GIT_SHALLOW_FILE": str(ambient_repo / ".git/ambient-shallow"),
    "GIT_WORK_TREE": str(ambient_repo),
}
prior_environment = {name: os.environ.get(name) for name in poisoned_environment}
try:
    os.environ.update(poisoned_environment)
    if module.git_output(root, "rev-parse", "HEAD^{commit}") != real_head:
        raise SystemExit("ambient Git variables redirected the checked HEAD")
    module.validate_git_repository_context(root)
    if not module.git_commit_is_ancestor(root, source_one, real_head):
        raise SystemExit("ambient Git variables redirected the ancestry query")
    observed_registry = module.git_file_bytes_at_commit(
        root, evidence_commit, module.SIGNATURE_REGISTRY_PATH
    )
    if observed_registry != canonical(registry_one).encode():
        raise SystemExit("ambient Git variables redirected historical blob bytes")
finally:
    for name, prior in prior_environment.items():
        if prior is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = prior

# Repository-local route changes are part of the presented repository, but they must not let Git
# describe another worktree while the checker reads files from this one.
fixture_git(root, "config", "core.worktree", str(ambient_repo))
expect_failure(
    "Git worktree root mismatch",
    lambda: module.validate_git_repository_context(root),
)
fixture_git(root, "config", "--unset", "core.worktree")
module.validate_git_repository_context(root)

# Locally configured replacement refs and the deprecated default graft file must not rewrite the
# object graph seen by ancestry or full-history evidence queries.
replacement_tree = fixture_git(root, "rev-parse", f"{real_head}^{{tree}}")
replacement_root = fixture_git(
    root, "commit-tree", replacement_tree, "-m", "replacement root"
)
fixture_git(root, "replace", real_head, replacement_root)
if not module.git_commit_is_ancestor(root, source_one, real_head):
    raise SystemExit("local replace ref hid true reachable ancestry")
fixture_git(root, "replace", "-d", real_head)

graft_file = root / ".git/info/grafts"
graft_file.parent.mkdir(parents=True, exist_ok=True)
graft_file.write_text(f"{real_head}\n", encoding="utf-8")
try:
    if not module.git_commit_is_ancestor(root, source_one, real_head):
        raise SystemExit("local graft file hid true reachable ancestry")
finally:
    graft_file.unlink()
PY

echo "OK: source and machine-scope mutations were rejected for the expected reasons"
