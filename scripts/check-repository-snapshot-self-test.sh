#!/usr/bin/env bash
# Failure-injection tests for the immutable repository-snapshot collector.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR="$SCRIPT_DIR/collect-repository-snapshot.py"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-repository-snapshot.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/legacy"
for artifact in \
  repository-snapshot.json \
  repository-snapshot.json.sha256 \
  repository-snapshot-envelope.json \
  repository-snapshot-command-log.json; do
  cp "$SCRIPT_DIR/../audit/evidence/$artifact" "$TMP/legacy/$artifact"
done
python3 "$COLLECTOR" --validate "$TMP/legacy/repository-snapshot.json" >/dev/null
printf '\n' >>"$TMP/legacy/repository-snapshot-command-log.json"
if python3 "$COLLECTOR" \
  --validate "$TMP/legacy/repository-snapshot.json" >/dev/null 2>&1; then
  echo "mutated historical v1 command log was accepted" >&2
  exit 1
fi

git init -q -b main "$TMP/origin"
git -C "$TMP/origin" config user.name "Repository Snapshot Self Test"
git -C "$TMP/origin" config user.email "snapshot-self-test.invalid"
touch "$TMP/origin/Cargo.lock"
git -C "$TMP/origin" add Cargo.lock
git -C "$TMP/origin" commit -qm initial
git -C "$TMP/origin" tag lightweight
git -C "$TMP/origin" tag -a annotated -m annotated

git clone -q "$TMP/origin" "$TMP/pid-rs"
git -C "$TMP/pid-rs" remote set-url origin https://github.com/test.invalid/pid-rs.git
git -C "$TMP/pid-rs" remote set-head origin main

# Keep the configured and resolved URL canonical. Only the test's git wrapper redirects the
# transport for ls-remote; production collection rejects Git's url.*.insteadOf rewriting.
REAL_GIT="$(command -v git)"
mkdir -p "$TMP/bin"
cat >"$TMP/bin/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == ls-remote || "${1:-}" == fetch ]]; then
  args=("$@")
  for index in "${!args[@]}"; do
    if [[ "${args[$index]}" == origin ]]; then
      case "$(basename "$PWD")" in
        pid-rs) args[$index]="$SNAPSHOT_TEST_ROOT/origin" ;;
        parent) args[$index]="$SNAPSHOT_TEST_ROOT/parent-origin" ;;
      esac
    fi
  done
  exec "$REAL_GIT" "${args[@]}"
fi
exec "$REAL_GIT" "$@"
EOF
chmod +x "$TMP/bin/git"
export REAL_GIT SNAPSHOT_TEST_ROOT="$TMP" PATH="$TMP/bin:$PATH"

python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github \
  --output-dir "$TMP/evidence" \
  --collected-at 2000-01-01T00:00:00Z
if python3 "$COLLECTOR" --validate "$TMP/evidence/repository-snapshot.json" \
  >/dev/null 2>&1; then
  echo "skipped GitHub release state was accepted without explicit opt-in" >&2
  exit 1
fi
python3 "$COLLECTOR" --skip-github --validate "$TMP/evidence/repository-snapshot.json"
python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github \
  --compare "$TMP/evidence/repository-snapshot.json"

# Detailed file projections come from the recorded HEAD tree, not a worktree edit hidden behind
# Git's assume-unchanged bit. The same tree must therefore reproduce the exact snapshot bytes.
git -C "$TMP/pid-rs" update-index --assume-unchanged Cargo.lock
printf 'concealed worktree edit\n' >"$TMP/pid-rs/Cargo.lock"
python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github \
  --compare "$TMP/evidence/repository-snapshot.json"
git -C "$TMP/pid-rs" update-index --no-assume-unchanged Cargo.lock
git -C "$TMP/pid-rs" show HEAD:Cargo.lock >"$TMP/pid-rs/Cargo.lock"

PYTHONPATH="$SCRIPT_DIR" python3 - "$COLLECTOR" <<'PY'
import importlib.util
import json
import pathlib
import sys
import urllib.parse
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("snapshot_collector", pathlib.Path(sys.argv[1]))
if spec is None or spec.loader is None:
    raise SystemExit("cannot load collector")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
items = [
    {"draft": False, "id": 2, "immutable": False, "prerelease": False,
     "published_at": "2000-01-02T00:00:00Z", "tag_name": "v2.0.0"},
    {"draft": False, "id": 1, "immutable": False, "prerelease": False,
     "published_at": "2000-01-01T00:00:00Z", "tag_name": "v1.0.0"},
]

class Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(items).encode("utf-8")

with patch.object(collector.urllib.request, "urlopen", return_value=Response()):
    record = collector.github_releases("test.invalid", "pid-rs")
if [item["id"] for item in record["releases"]] != [1, 2]:
    raise SystemExit("unsorted release input was not canonicalized")
expected = collector.sha256_bytes(collector.canonical_json_bytes(record["releases"]))
if record["api_projection_sha256"] != expected:
    raise SystemExit("release projection was hashed before canonical sorting")

page_one = [
    {"draft": False, "id": index, "immutable": False, "prerelease": False,
     "published_at": "2000-01-01T00:00:00Z", "tag_name": f"v{index:04d}"}
    for index in range(100, 0, -1)
]
page_two = [
    {"draft": False, "id": 101, "immutable": True, "prerelease": True,
     "published_at": "2000-01-02T00:00:00Z", "tag_name": "v0101"},
    {"draft": True, "id": 102, "immutable": False, "prerelease": True,
     "published_at": None, "tag_name": "private-draft"},
]
requested_pages = []

class PagedResponse(Response):
    def __init__(self, value):
        self.value = value

    def read(self):
        return json.dumps(self.value).encode("utf-8")

def paged_urlopen(request, timeout):
    del timeout
    page = int(urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)["page"][0])
    requested_pages.append(page)
    return PagedResponse({1: page_one, 2: page_two}.get(page, []))

with patch.object(collector.urllib.request, "urlopen", side_effect=paged_urlopen):
    paged_record = collector.github_releases("test.invalid", "pid-rs")
if requested_pages != [1, 2] or len(paged_record["releases"]) != 101:
    raise SystemExit("GitHub release pagination did not collect every public page")
if any(item["draft"] for item in paged_record["releases"]):
    raise SystemExit("authenticated draft release leaked into the public projection")

duplicate_page = [dict(page_two[0], id=100, tag_name="different-tag", immutable=False)]
def duplicate_urlopen(request, timeout):
    del timeout
    page = int(urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)["page"][0])
    return PagedResponse({1: page_one, 2: duplicate_page}.get(page, []))

try:
    with patch.object(collector.urllib.request, "urlopen", side_effect=duplicate_urlopen):
        collector.github_releases("test.invalid", "pid-rs")
except collector.SnapshotError:
    pass
else:
    raise SystemExit("duplicate release identity across pages was accepted")
PY

PYTHONPATH="$SCRIPT_DIR" python3 - "$COLLECTOR" "$TMP/pid-rs" "$TMP/origin" <<'PY'
import importlib.util
import pathlib
import subprocess
import sys
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("snapshot_collector", pathlib.Path(sys.argv[1]))
if spec is None or spec.loader is None:
    raise SystemExit("cannot load collector")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
repo = pathlib.Path(sys.argv[2])
origin = pathlib.Path(sys.argv[3])
raced = repo / "concurrent-untracked-file"
original = collector.collect_submodules

def mutate_after_submodules(*args, **kwargs):
    result = original(*args, **kwargs)
    raced.write_text("changed during collection\n", encoding="utf-8")
    return result

try:
    with patch.object(collector, "collect_submodules", side_effect=mutate_after_submodules):
        collector.collect_repository(
            "pid-rs",
            repo,
            "test.invalid",
            "claimed_core",
            collector.CommandLog(),
            skip_github=True,
        )
except collector.SnapshotError:
    pass
else:
    raise SystemExit("checkout mutation during collection was accepted")
finally:
    raced.unlink(missing_ok=True)

before_remote = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=origin, text=True
).strip()
remote_raced = origin / "advanced-during-collection"

def advance_remote_after_submodules(*args, **kwargs):
    result = original(*args, **kwargs)
    remote_raced.write_text("advanced during collection\n", encoding="utf-8")
    subprocess.run(["git", "add", remote_raced.name], cwd=origin, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "advanced-during-collection"], cwd=origin, check=True
    )
    return result

try:
    with patch.object(collector, "collect_submodules", side_effect=advance_remote_after_submodules):
        collector.collect_repository(
            "pid-rs",
            repo,
            "test.invalid",
            "claimed_core",
            collector.CommandLog(),
            skip_github=True,
        )
except collector.SnapshotError:
    pass
else:
    raise SystemExit("live remote mutation during collection was accepted")
finally:
    subprocess.run(["git", "reset", "--hard", "-q", before_remote], cwd=origin, check=True)
PY

touch "$TMP/pid-rs/dirty"
if python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github >/dev/null 2>&1; then
  echo "dirty checkout was accepted" >&2
  exit 1
fi
rm "$TMP/pid-rs/dirty"

git -C "$TMP/pid-rs" config \
  "url.file://$TMP/origin.insteadOf" \
  https://github.com/test.invalid/pid-rs.git
if python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github >/dev/null 2>&1; then
  echo "url.*.insteadOf remote substitution was accepted" >&2
  exit 1
fi
git -C "$TMP/pid-rs" config --unset-all \
  "url.file://$TMP/origin.insteadOf"

blob_sha="$(printf 'not a commit\n' | git -C "$TMP/origin" hash-object -w --stdin)"
git -C "$TMP/origin" update-ref refs/tags/blob-target "$blob_sha"
if python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github >/dev/null 2>&1; then
  echo "lightweight blob tag was accepted as a commit tag" >&2
  exit 1
fi
git -C "$TMP/origin" update-ref -d refs/tags/blob-target

python3 - "$TMP/evidence/repository-snapshot.json" "$TMP/short-sha.json" <<'PY'
import json
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))
data["repositories"][0]["commit_sha"] = data["repositories"][0]["commit_sha"][:7]
target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
if python3 "$COLLECTOR" --skip-github --validate "$TMP/short-sha.json" >/dev/null 2>&1; then
  echo "short commit SHA was accepted" >&2
  exit 1
fi

python3 - "$TMP/evidence/repository-snapshot.json" "$TMP" <<'PY'
import copy
import hashlib
import json
import pathlib
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))

commit = data["repositories"][0]["commit_sha"]
submodule_pid = {
    "checked_out_sha": commit,
    "gitlink_sha": commit,
    "matches_gitlink": True,
    "path": "pid-rs",
    "status_prefix": " ",
}
submodule_other = dict(submodule_pid, path="other")
dependency_one = {
    "declaration_path": "dependencies.pid_core",
    "features": [],
    "git": "https://github.com/sepahead/pid-rs",
    "manifest": "Cargo.toml",
    "package": "pid-core",
    "pin_kind": "rev",
    "pin_value": commit,
    "version": None,
}
dependency_two = dict(
    dependency_one,
    declaration_path="dependencies.pid_runlog",
    package="pid-runlog",
)
cross_one = {
    "declaration_path": dependency_one["declaration_path"],
    "manifest": dependency_one["manifest"],
    "pin_sha": commit,
    "reachable_from_v1_0_0": False,
    "resolves_in_pid_rs": True,
    "v1_0_0_tag_exists": False,
}
cross_two = dict(cross_one, declaration_path=dependency_two["declaration_path"])

valid_cross = copy.deepcopy(data)
prisoma_record = copy.deepcopy(data["repositories"][0])
prisoma_record["name"] = "prisoma"
prisoma_record["remote_url"] = "https://github.com/test.invalid/prisoma.git"
prisoma_record["release_claim_status"] = "not_claimed"
prisoma_record["submodules"] = [submodule_other, submodule_pid]
galadriel_record = copy.deepcopy(data["repositories"][0])
galadriel_record["name"] = "galadriel"
galadriel_record["remote_url"] = "https://github.com/test.invalid/galadriel.git"
galadriel_record["release_claim_status"] = "not_claimed"
galadriel_record["git_dependencies"] = [dependency_one, dependency_two]
valid_cross["repositories"].extend([prisoma_record, galadriel_record])
valid_cross["cross_repository_checks"] = {
    "galadriel_pid_rs_dependency": [cross_one, cross_two],
    "prisoma_pid_rs_submodule": submodule_pid,
}
(target / "valid-cross.json").write_text(
    json.dumps(valid_cross, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

mutations = {}
unknown_root = copy.deepcopy(data)
unknown_root["unmodelled"] = True
mutations["unknown-root.json"] = unknown_root

unknown_repository = copy.deepcopy(data)
unknown_repository["repositories"][0]["unmodelled"] = True
mutations["unknown-repository.json"] = unknown_repository

wrong_projection = copy.deepcopy(data)
wrong_projection["repositories"][0]["github_releases"] = {
    "api_projection_sha256": "0" * 64,
    "collection_status": "queried",
    "releases": [],
}
mutations["wrong-release-projection.json"] = wrong_projection

wrong_head_tags = copy.deepcopy(data)
wrong_head_tags["repositories"][0]["head_tags"] = ["v9.9.9"]
mutations["wrong-head-tags.json"] = wrong_head_tags

wrong_claim = copy.deepcopy(data)
wrong_claim["repositories"][0]["release_claim_status"] = "not_claimed"
mutations["wrong-claim.json"] = wrong_claim

unknown_cross_check = copy.deepcopy(data)
unknown_cross_check["cross_repository_checks"]["unmodelled"] = {}
mutations["unknown-cross-check.json"] = unknown_cross_check

missing_cross_check = copy.deepcopy(data)
prisoma = copy.deepcopy(missing_cross_check["repositories"][0])
prisoma["name"] = "prisoma"
prisoma["remote_url"] = "https://github.com/test.invalid/prisoma.git"
prisoma["release_claim_status"] = "not_claimed"
missing_cross_check["repositories"].append(prisoma)
mutations["missing-cross-check.json"] = missing_cross_check

downstream_claim = copy.deepcopy(missing_cross_check)
downstream_claim["repositories"][1]["release_claim_status"] = "claimed_core"
mutations["downstream-claim.json"] = downstream_claim

wrong_remote_name = copy.deepcopy(data)
wrong_remote_name["repositories"][0]["remote_url"] = (
    "https://github.com/test.invalid/not-pid-rs.git"
)
mutations["wrong-remote-name.json"] = wrong_remote_name

wrong_prisoma_target = copy.deepcopy(valid_cross)
wrong_prisoma_target["cross_repository_checks"]["prisoma_pid_rs_submodule"] = (
    submodule_other
)
mutations["wrong-prisoma-target.json"] = wrong_prisoma_target

incomplete_dependency_checks = copy.deepcopy(valid_cross)
incomplete_dependency_checks["cross_repository_checks"][
    "galadriel_pid_rs_dependency"
].pop()
mutations["incomplete-dependency-checks.json"] = incomplete_dependency_checks

duplicate_release_id = copy.deepcopy(data)
duplicate_releases = [
    {"draft": False, "id": 7, "immutable": False, "prerelease": False,
     "published_at": "2000-01-01T00:00:00Z", "tag_name": "v1.0.0"},
    {"draft": False, "id": 7, "immutable": False, "prerelease": False,
     "published_at": "2000-01-02T00:00:00Z", "tag_name": "v2.0.0"},
]
projection = (json.dumps(duplicate_releases, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
duplicate_release_id["repositories"][0]["github_releases"] = {
    "api_projection_sha256": hashlib.sha256(projection).hexdigest(),
    "collection_status": "queried",
    "releases": duplicate_releases,
}
mutations["duplicate-release-id.json"] = duplicate_release_id

draft_projection = copy.deepcopy(data)
draft_releases = [
    {"draft": True, "id": 8, "immutable": False, "prerelease": True,
     "published_at": None, "tag_name": "draft"},
]
projection = (json.dumps(draft_releases, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
draft_projection["repositories"][0]["github_releases"] = {
    "api_projection_sha256": hashlib.sha256(projection).hexdigest(),
    "collection_status": "queried",
    "releases": draft_releases,
}
mutations["draft-release-projection.json"] = draft_projection

for name, value in mutations.items():
    (target / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
PY
python3 "$COLLECTOR" --skip-github --validate "$TMP/valid-cross.json" >/dev/null
for mutation in \
  unknown-root.json \
  unknown-repository.json \
  wrong-release-projection.json \
  wrong-head-tags.json \
  wrong-claim.json \
  unknown-cross-check.json \
  missing-cross-check.json \
  downstream-claim.json \
  wrong-remote-name.json \
  wrong-prisoma-target.json \
  incomplete-dependency-checks.json \
  duplicate-release-id.json \
  draft-release-projection.json; do
  if python3 "$COLLECTOR" --skip-github --validate "$TMP/$mutation" >/dev/null 2>&1; then
    echo "repository snapshot mutation was accepted: $mutation" >&2
    exit 1
  fi
done

# A cached origin/main ref must not conceal a live remote advance.
touch "$TMP/origin/remote-advanced"
git -C "$TMP/origin" add remote-advanced
git -C "$TMP/origin" commit -qm remote-advanced
if python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories pid-rs \
  --skip-github >/dev/null 2>&1; then
  echo "stale local tracking ref concealed a live remote advance" >&2
  exit 1
fi

git init -q -b main "$TMP/sub-origin"
git -C "$TMP/sub-origin" config user.name "Repository Snapshot Self Test"
git -C "$TMP/sub-origin" config user.email "snapshot-self-test.invalid"
touch "$TMP/sub-origin/one"
git -C "$TMP/sub-origin" add one
git -C "$TMP/sub-origin" commit -qm one
git -C "$TMP/sub-origin" tag first
touch "$TMP/sub-origin/two"
git -C "$TMP/sub-origin" add two
git -C "$TMP/sub-origin" commit -qm two

git init -q -b main "$TMP/parent-origin"
git -C "$TMP/parent-origin" config user.name "Repository Snapshot Self Test"
git -C "$TMP/parent-origin" config user.email "snapshot-self-test.invalid"
git -C "$TMP/parent-origin" -c protocol.file.allow=always submodule add -q "$TMP/sub-origin" child
git -C "$TMP/parent-origin/child" checkout -q first
git -C "$TMP/parent-origin" add child
git -C "$TMP/parent-origin" commit -qm parent

git -c protocol.file.allow=always clone -q --recurse-submodules \
  "$TMP/parent-origin" "$TMP/parent"
git -C "$TMP/parent" remote set-url origin https://github.com/test.invalid/parent.git
git -C "$TMP/parent" remote set-head origin main
git -C "$TMP/parent/child" checkout -q main
if python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories parent \
  --skip-github >/dev/null 2>&1; then
  echo "submodule checkout mismatch was accepted" >&2
  exit 1
fi

echo "OK: repository-snapshot determinism and failure injections passed"
