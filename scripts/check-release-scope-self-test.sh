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
  wrong_feature missing_leak bad_state remove_parallel bad_semver bad_path duplicate_key \
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
elif mutation == "missing_leak":
    scope["conditional_members"].pop(0)
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
    missing_leak) expected="stable-namespace diff disagrees" ;;
    bad_state) expected="JSON Schema validation failed" ;;
    remove_parallel) expected="feature profile set mismatch" ;;
    bad_semver) expected="stable families require an explicit 1.x SemVer promise" ;;
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
PY

echo "OK: source and machine-scope mutations were rejected for the expected reasons"
