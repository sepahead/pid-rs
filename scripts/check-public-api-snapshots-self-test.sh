#!/usr/bin/env bash
# Mutation test: a public method added without touching lib.rs must change the compiled snapshot.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TOOLCHAIN="${PID_RS_PUBLIC_API_TOOLCHAIN:-nightly-2026-06-16}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-public-api-mutation.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

if ! API_PYTHON_EXECUTABLE="$(type -P python3)" \
  || [[ "$API_PYTHON_EXECUTABLE" != /* || ! -f "$API_PYTHON_EXECUTABLE" \
    || ! -x "$API_PYTHON_EXECUTABLE" ]]
then
  echo "public API self-test requires an absolute executable python3 route" >&2
  exit 2
fi
API_PYTHON_EXECUTABLE="$(
  cd "$(dirname "$API_PYTHON_EXECUTABLE")"
  printf '%s/%s\n' "$(pwd -P)" "$(basename "$API_PYTHON_EXECUTABLE")"
)"
if ! "$API_PYTHON_EXECUTABLE" -I -S -B -c '
import sys
raise SystemExit(
    0
    if sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize == 0
    else 1
)
'; then
  echo "public API self-test requires Python 3.11+ -I -S -B without -O" >&2
  exit 2
fi
readonly API_PYTHON_EXECUTABLE

mkdir "$TMP/fixture-home"

# Scratch repositories are test data, not extensions of the caller's Git session. Keep one
# allowlisted execution boundary so routing variables, replacement/graft namespaces, config,
# attributes, hooks, and signing defaults cannot redirect or decorate fixture commits.
fixture_git() (
  local root="$1"
  shift
  command env -i \
    "GIT_ATTR_NOSYSTEM=1" \
    "GIT_CONFIG_GLOBAL=/dev/null" \
    "GIT_CONFIG_NOSYSTEM=1" \
    "GIT_CONFIG_SYSTEM=/dev/null" \
    "GIT_GRAFT_FILE=/dev/null" \
    "GIT_LITERAL_PATHSPECS=1" \
    "GIT_NO_LAZY_FETCH=1" \
    "GIT_NO_REPLACE_OBJECTS=1" \
    "GIT_OPTIONAL_LOCKS=0" \
    "GIT_TERMINAL_PROMPT=0" \
    "HOME=$TMP/fixture-home" \
    "LANG=C" \
    "LC_ALL=C" \
    "PATH=${PATH:?PATH is required to locate Git}" \
    "TMPDIR=$TMP" \
    git \
      -c advice.graftFileDeprecated=false \
      -c commit.gpgsign=false \
      -c core.attributesFile=/dev/null \
      -c core.fsmonitor=false \
      -c core.hooksPath=/dev/null \
      -c core.untrackedCache=false \
      -c tag.gpgsign=false \
      -C "$root" "$@"
)

mkdir "$TMP/poison-hooks" "$TMP/poison-worktree"
printf '#!/usr/bin/env bash\nexit 97\n' >"$TMP/poison-hooks/pre-commit"
chmod 700 "$TMP/poison-hooks/pre-commit"
printf '[commit]\n\tgpgSign = true\n[core]\n\thooksPath = %s\n\tworktree = %s\n' \
  "$TMP/poison-hooks" "$TMP/poison-worktree" >"$TMP/poison.gitconfig"

mkdir "$TMP/replacement-fixture"
GIT_ATTR_SOURCE=refs/heads/ambient-attributes \
GIT_ALTERNATE_OBJECT_DIRECTORIES="$TMP/ambient-alternate-objects" \
GIT_CEILING_DIRECTORIES="$TMP" \
GIT_COMMON_DIR="$TMP/ambient-common.git" \
GIT_CONFIG="$TMP/poison.gitconfig" \
GIT_CONFIG_COUNT=3 \
GIT_CONFIG_GLOBAL="$TMP/poison.gitconfig" \
GIT_CONFIG_KEY_0=commit.gpgsign \
GIT_CONFIG_KEY_1=core.hooksPath \
GIT_CONFIG_KEY_2=core.worktree \
GIT_CONFIG_SYSTEM="$TMP/poison.gitconfig" \
GIT_CONFIG_VALUE_0=true \
GIT_CONFIG_VALUE_1="$TMP/poison-hooks" \
GIT_CONFIG_VALUE_2="$TMP/poison-worktree" \
GIT_CONFIG_PARAMETERS="'core.worktree=$TMP/poison-worktree'" \
GIT_DIR="$TMP/ambient.git" \
GIT_DISCOVERY_ACROSS_FILESYSTEM=1 \
GIT_EXEC_PATH="$TMP/ambient-git-exec-path" \
GIT_GLOB_PATHSPECS=1 \
GIT_GRAFT_FILE="$TMP/ambient-grafts" \
GIT_INDEX_FILE="$TMP/ambient-index" \
GIT_NAMESPACE=ambient-namespace \
GIT_NO_LAZY_FETCH=0 \
GIT_NO_REPLACE_OBJECTS=0 \
GIT_OBJECT_DIRECTORY="$TMP/ambient-objects" \
GIT_QUARANTINE_PATH="$TMP/ambient-quarantine" \
GIT_REFERENCE_BACKEND=ambient-reference-backend \
GIT_REPLACE_REF_BASE=refs/ambient-replacements/ \
GIT_SHALLOW_FILE="$TMP/ambient-shallow" \
GIT_TEMPLATE_DIR="$TMP/poison-hooks" \
GIT_WORK_TREE="$TMP/poison-worktree" \
  fixture_git "$TMP/replacement-fixture" init -q
printf 'literal source\n' >"$TMP/replacement-fixture/value.txt"
fixture_git "$TMP/replacement-fixture" add value.txt
GIT_CONFIG_COUNT=2 \
GIT_CONFIG_GLOBAL="$TMP/poison.gitconfig" \
GIT_CONFIG_KEY_0=commit.gpgsign \
GIT_CONFIG_KEY_1=core.hooksPath \
GIT_CONFIG_VALUE_0=true \
GIT_CONFIG_VALUE_1="$TMP/poison-hooks" \
GIT_AUTHOR_EMAIL=ambient-author@example.invalid \
GIT_AUTHOR_NAME='Ambient Author' \
GIT_COMMITTER_EMAIL=ambient-committer@example.invalid \
GIT_COMMITTER_NAME='Ambient Committer' \
  fixture_git "$TMP/replacement-fixture" \
  -c user.name=pid-rs-tests -c user.email=tests@example.invalid \
  commit -q --no-gpg-sign --no-verify -m literal-source
literal_commit="$(fixture_git "$TMP/replacement-fixture" rev-parse HEAD)"
literal_tree="$(fixture_git "$TMP/replacement-fixture" rev-parse 'HEAD^{tree}')"
literal_headers="$(
  fixture_git "$TMP/replacement-fixture" cat-file -p "$literal_commit" | sed -n '1,/^$/p'
)"
if grep -q '^gpgsig ' <<<"$literal_headers"; then
  echo "fixture Git wrapper allowed commit signing" >&2
  exit 1
fi
if ! grep -q '^author pid-rs-tests <tests@example.invalid> ' <<<"$literal_headers" \
  || ! grep -q '^committer pid-rs-tests <tests@example.invalid> ' <<<"$literal_headers"
then
  echo "fixture Git wrapper accepted ambient author identity" >&2
  exit 1
fi
printf 'replacement source\n' >"$TMP/replacement-fixture/value.txt"
fixture_git "$TMP/replacement-fixture" add value.txt
fixture_git "$TMP/replacement-fixture" \
  -c user.name=pid-rs-tests -c user.email=tests@example.invalid \
  commit -q --no-gpg-sign --no-verify -m replacement-source
replacement_commit="$(fixture_git "$TMP/replacement-fixture" rev-parse HEAD)"
GIT_NO_REPLACE_OBJECTS=0 \
GIT_REPLACE_REF_BASE=refs/ambient-replacements/ \
  fixture_git "$TMP/replacement-fixture" replace "$literal_commit" "$replacement_commit"
if ! fixture_git "$TMP/replacement-fixture" show-ref --verify \
  "refs/replace/$literal_commit" >/dev/null
then
  echo "fixture Git wrapper accepted an ambient replacement namespace" >&2
  exit 1
fi
"$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$TMP/replacement-fixture" "$literal_commit" "$literal_tree" \
  "$TMP/materialized-source" "$API_PYTHON_EXECUTABLE"
if [[ "$(cat "$TMP/materialized-source/value.txt")" != "literal source" ]]; then
  echo "public API source materialization followed a replacement ref" >&2
  exit 1
fi
mkdir "$TMP/hostile-path"
printf '%s\n' \
  '#!/bin/sh' \
  'printf "executed\\n" >"$PID_RS_HOSTILE_PATH_MARKER"' \
  'exit 99' \
  >"$TMP/hostile-path/python3"
chmod 700 "$TMP/hostile-path/python3"
PATH="$TMP/hostile-path:$PATH" \
PID_RS_HOSTILE_PATH_MARKER="$TMP/hostile-path-python-executed" \
  "$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$TMP/replacement-fixture" "$literal_commit" "$literal_tree" \
  "$TMP/materialized-hostile-path-source" "$API_PYTHON_EXECUTABLE"
if [[ -e "$TMP/hostile-path-python-executed" ]]; then
  echo "public API materializer re-resolved Python from hostile PATH" >&2
  exit 1
fi
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'arguments=()' \
  'for argument in "$@"; do' \
  '  if [[ "$argument" != "-I" ]]; then arguments+=("$argument"); fi' \
  'done' \
  "exec $(printf '%q' "$API_PYTHON_EXECUTABLE") \"\${arguments[@]}\"" \
  >"$TMP/nonisolated-python"
chmod 700 "$TMP/nonisolated-python"
if "$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$TMP/replacement-fixture" "$literal_commit" "$literal_tree" \
  "$TMP/materialized-nonisolated-source" "$TMP/nonisolated-python" \
  >"$TMP/nonisolated-stdout" 2>"$TMP/nonisolated-stderr"
then
  echo "public API source materialization accepted a non-isolated Python helper" >&2
  exit 1
fi
if ! grep -F "requires Python 3.11+ -I -S -B without -O" \
  "$TMP/nonisolated-stderr" >/dev/null
then
  echo "non-isolated Python helper failed for the wrong reason" >&2
  sed -n '1,20p' "$TMP/nonisolated-stderr" >&2
  exit 1
fi
printf 'value.txt export-ignore\n' >"$TMP/replacement-fixture/.git/info/attributes"
if "$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$TMP/replacement-fixture" "$literal_commit" "$literal_tree" \
  "$TMP/materialized-attribute-source" "$API_PYTHON_EXECUTABLE" \
  >"$TMP/attribute-stdout" 2>"$TMP/attribute-stderr"
then
  echo "public API source materialization accepted an archive-altering info attribute" >&2
  exit 1
fi
if ! grep -F "rejects export-ignore" "$TMP/attribute-stderr" >/dev/null; then
  echo "archive-altering info attribute failed for the wrong reason" >&2
  sed -n '1,20p' "$TMP/attribute-stderr" >&2
  exit 1
fi

mkdir "$TMP/symbolic-link-fixture"
fixture_git "$TMP/symbolic-link-fixture" init -q
printf 'outside source\n' >"$TMP/outside-source.rs"
ln -s "$TMP/outside-source.rs" "$TMP/symbolic-link-fixture/escaping-link.rs"
fixture_git "$TMP/symbolic-link-fixture" add escaping-link.rs
fixture_git "$TMP/symbolic-link-fixture" \
  -c user.name=pid-rs-tests -c user.email=tests@example.invalid \
  commit -q --no-gpg-sign --no-verify -m symbolic-link-source
symbolic_link_commit="$(fixture_git "$TMP/symbolic-link-fixture" rev-parse HEAD)"
symbolic_link_tree="$(fixture_git "$TMP/symbolic-link-fixture" rev-parse 'HEAD^{tree}')"
if "$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$TMP/symbolic-link-fixture" "$symbolic_link_commit" "$symbolic_link_tree" \
  "$TMP/materialized-symbolic-link-source" "$API_PYTHON_EXECUTABLE" \
  >"$TMP/symbolic-link-stdout" 2>"$TMP/symbolic-link-stderr"
then
  echo "public API source materialization accepted a tracked symbolic link" >&2
  exit 1
fi
if ! grep -F "rejects tracked symbolic-link entry" "$TMP/symbolic-link-stderr" >/dev/null; then
  echo "tracked symbolic-link fixture failed for the wrong reason" >&2
  sed -n '1,20p' "$TMP/symbolic-link-stderr" >&2
  exit 1
fi

mkdir "$TMP/gitlink-fixture"
fixture_git "$TMP/gitlink-fixture" init -q
printf 'gitlink target\n' >"$TMP/gitlink-fixture/anchor.txt"
fixture_git "$TMP/gitlink-fixture" add anchor.txt
fixture_git "$TMP/gitlink-fixture" \
  -c user.name=pid-rs-tests -c user.email=tests@example.invalid \
  commit -q --no-gpg-sign --no-verify -m gitlink-target
gitlink_target="$(fixture_git "$TMP/gitlink-fixture" rev-parse HEAD)"
"$API_PYTHON_EXECUTABLE" -I -S -B - "$TMP/gitlink-fixture/zzz" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
root.mkdir()
for index in range(4096):
    (root / f"trailing-{index:04}.txt").write_text("trailing source\n", encoding="utf-8")
PY
fixture_git "$TMP/gitlink-fixture" add zzz
fixture_git "$TMP/gitlink-fixture" update-index --add \
  --cacheinfo "160000,$gitlink_target,aaa-gitlink"
fixture_git "$TMP/gitlink-fixture" \
  -c user.name=pid-rs-tests -c user.email=tests@example.invalid \
  commit -q --no-gpg-sign --no-verify -m gitlink-source
gitlink_commit="$(fixture_git "$TMP/gitlink-fixture" rev-parse HEAD)"
gitlink_tree="$(fixture_git "$TMP/gitlink-fixture" rev-parse 'HEAD^{tree}')"
if "$SCRIPT_DIR/materialize-public-api-source-v2.sh" \
  "$TMP/gitlink-fixture" "$gitlink_commit" "$gitlink_tree" \
  "$TMP/materialized-gitlink-source" "$API_PYTHON_EXECUTABLE" \
  >"$TMP/gitlink-stdout" 2>"$TMP/gitlink-stderr"
then
  echo "public API source materialization accepted a Git submodule entry" >&2
  exit 1
fi
if ! grep -F "rejects Git submodule entry" "$TMP/gitlink-stderr" >/dev/null; then
  echo "Git submodule fixture failed for the wrong reason" >&2
  sed -n '1,20p' "$TMP/gitlink-stderr" >&2
  exit 1
fi

mkdir -p "$TMP/configured-parent/.cargo"
printf '[build]\nrustflags = ["--definitely-invalid-parent-flag"]\n' \
  >"$TMP/configured-parent/.cargo/config.toml"
if TMPDIR="$TMP/configured-parent" \
  "$SCRIPT_DIR/check-public-api-snapshots.sh" \
  >"$TMP/parent-config-stdout" 2>"$TMP/parent-config-stderr"
then
  echo "public API evidence accepted Cargo config in source ancestry" >&2
  exit 1
fi
if ! grep -F "rejects Cargo config in source ancestry" \
  "$TMP/parent-config-stderr" >/dev/null
then
  echo "source-ancestry Cargo config fixture failed for the wrong reason" >&2
  sed -n '1,20p' "$TMP/parent-config-stderr" >&2
  exit 1
fi

# Prevent a false-positive self-test caused by unrelated baseline drift, while proving that
# ambient compiler/Cargo/Git routing cannot influence evidence generation.
mkdir "$TMP/ambient-cargo-home"
printf '[build]\nrustflags = ["--definitely-invalid-ambient-flag"]\n' \
  >"$TMP/ambient-cargo-home/config.toml"
mkdir "$TMP/ambient-python-path"
printf 'raise RuntimeError("ambient Python path was imported")\n' \
  >"$TMP/ambient-python-path/json.py"
printf '%s\n' \
  'import os' \
  'from pathlib import Path' \
  'Path(os.environ["PID_RS_HOSTILE_SITE_MARKER"]).write_text("executed\\n")' \
  'raise RuntimeError("ambient sitecustomize was imported")' \
  >"$TMP/ambient-python-path/sitecustomize.py"
CARGO_BUILD_TARGET=pid-rs-invalid-ambient-target \
CARGO_BUILD_RUSTC="$TMP/nonexistent-cargo-build-rustc" \
CARGO_BUILD_RUSTC_WRAPPER="$TMP/nonexistent-cargo-build-rustc-wrapper" \
CARGO_BUILD_RUSTDOC="$TMP/nonexistent-cargo-build-rustdoc" \
CARGO_BUILD_RUSTFLAGS=--definitely-invalid-cargo-build-rust-flag \
CARGO_ALIAS_PUBLIC_API='run --bin definitely-invalid-ambient-public-api' \
CARGO_HOME="$TMP/ambient-cargo-home" \
CARGO_ENCODED_RUSTDOCFLAGS=--definitely-invalid-ambient-encoded-rustdoc-flag \
CARGO_ENCODED_RUSTFLAGS=--definitely-invalid-ambient-encoded-flag \
CARGO_FEATURE_DEFINITELY_INVALID_AMBIENT=1 \
CARGO_REGISTRY_DEFAULT=definitely-invalid-ambient-registry \
GIT_DIR="$TMP/nonexistent-ambient-git-dir" \
PID_RS_HOSTILE_SITE_MARKER="$TMP/sitecustomize-executed" \
PYTHONPATH="$TMP/ambient-python-path" \
PYTHONOPTIMIZE=2 \
PYTHONSTARTUP="$TMP/ambient-python-path/sitecustomize.py" \
PYTHONUSERBASE="$TMP/ambient-python-path" \
RUSTC="$TMP/nonexistent-ambient-rustc" \
RUSTDOC="$TMP/nonexistent-ambient-rustdoc" \
RUSTDOCFLAGS=--definitely-invalid-ambient-rustdoc-flag \
RUSTFLAGS=--definitely-invalid-ambient-rust-flag \
TAR_OPTIONS=--definitely-invalid-ambient-tar-option \
  TAR_READER_OPTIONS=definitely-invalid-ambient-tar-reader-option \
  "$SCRIPT_DIR/check-public-api-snapshots.sh"
if [[ -e "$TMP/sitecustomize-executed" ]]; then
  echo "isolated public API Python route executed hostile sitecustomize" >&2
  exit 1
fi

mkdir "$TMP/repo"
tar --exclude './.git' --exclude './target' -cf - -C "$REPO_ROOT" . \
  | tar -xf - -C "$TMP/repo"
"$API_PYTHON_EXECUTABLE" -I -S -B - \
  "$TMP/repo/crates/pid-core/src/report.rs" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = "pub enum InformationUnit {\n    Nats,\n}\n"
addition = needle + "\nimpl InformationUnit {\n    pub fn unscoped_release_method(&self) {}\n}\n"
if source.count(needle) != 1:
    raise SystemExit("compiled API injection point changed")
path.write_text(source.replace(needle, addition), encoding="utf-8")
PY

generated="$TMP/mutated-api.txt"
rustdoc_target="$("$API_PYTHON_EXECUTABLE" -I -S -B - \
  "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["api_snapshot_source"]["rustdoc_target_triple"])
PY
)"
(
  cd "$TMP/repo"
  CARGO_TARGET_DIR="$TMP/cargo-target" \
    rustup run "$TOOLCHAIN" cargo public-api -p pid-core --no-default-features \
      --target "$rustdoc_target" -sss --color never >"$generated"
)

committed_relative="$("$API_PYTHON_EXECUTABLE" -I -S -B - \
  "$REPO_ROOT/release-scope-1.0.json" <<'PY'
import json
from pathlib import Path
import sys

scope = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(next(item for item in scope["feature_profiles"] if item["id"] == "pid-core-default")["public_api_snapshot"])
PY
)"
committed="$REPO_ROOT/$committed_relative"
if cmp -s "$committed" "$generated"; then
  echo "compiled public method mutation did not change the API snapshot" >&2
  exit 1
fi
if ! grep -F \
  "pub fn pid_core::stable::continuous::InformationUnit::unscoped_release_method(&self)" \
  "$generated" >/dev/null
then
  echo "compiled mutation changed the snapshot for an unexpected reason" >&2
  exit 1
fi

echo "OK: compiled public method mutation changed the frozen API snapshot"
