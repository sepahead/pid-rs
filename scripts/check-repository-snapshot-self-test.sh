#!/usr/bin/env bash
# Failure-injection tests for the immutable repository-snapshot collector.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTOR="$SCRIPT_DIR/collect-repository-snapshot.py"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-repository-snapshot.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

git init -q -b main "$TMP/origin"
git -C "$TMP/origin" config user.name "Repository Snapshot Self Test"
git -C "$TMP/origin" config user.email "snapshot-self-test.invalid"
touch "$TMP/origin/Cargo.lock"
git -C "$TMP/origin" add Cargo.lock
git -C "$TMP/origin" commit -qm initial

git clone -q "$TMP/origin" "$TMP/example"
git -C "$TMP/example" remote set-url origin https://github.com/test.invalid/example.git
git -C "$TMP/example" remote set-head origin main

python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories example \
  --skip-github \
  --output-dir "$TMP/evidence" \
  --collected-at 2000-01-01T00:00:00Z
python3 "$COLLECTOR" --validate "$TMP/evidence/repository-snapshot.json"
python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories example \
  --skip-github \
  --compare "$TMP/evidence/repository-snapshot.json"

touch "$TMP/example/dirty"
if python3 "$COLLECTOR" \
  --workspace "$TMP" \
  --organization test.invalid \
  --repositories example \
  --skip-github >/dev/null 2>&1; then
  echo "dirty checkout was accepted" >&2
  exit 1
fi
rm "$TMP/example/dirty"

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
if python3 "$COLLECTOR" --validate "$TMP/short-sha.json" >/dev/null 2>&1; then
  echo "short commit SHA was accepted" >&2
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
