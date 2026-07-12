#!/usr/bin/env bash
set -euo pipefail

# Verify the exact pid-core archive before pid-runlog exists on crates.io. Cargo refuses to
# package pid-core until every versioned dependency is visible in its target registry, so seed a
# temporary local registry with the exact pid-runlog archive plus the locked crates.io graph.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v cargo-local-registry >/dev/null 2>&1; then
  echo "error: cargo-local-registry 0.2.12 is required" >&2
  echo "install it with: cargo install cargo-local-registry --locked --version 0.2.12" >&2
  exit 1
fi

actual_local_registry_version="$(cargo-local-registry --version | awk '{print $2}')"
if [[ "$actual_local_registry_version" != "0.2.12" ]]; then
  echo "error: cargo-local-registry 0.2.12 is required; found $actual_local_registry_version" >&2
  exit 1
fi

version="$({ cargo metadata --locked --format-version 1 --no-deps; } | python3 -c '
import json
import sys

metadata = json.load(sys.stdin)
versions = {
    package["version"]
    for package in metadata["packages"]
    if package["name"] in {"pid-core", "pid-runlog"}
}
if len(versions) != 1:
    raise SystemExit(f"pid-core and pid-runlog versions differ: {sorted(versions)}")
print(versions.pop())
')"

package_args=(--locked)
if [[ "${PID_RS_PACKAGE_ALLOW_DIRTY:-0}" == "1" ]]; then
  package_args+=(--allow-dirty)
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-package-verification.XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT

rm -f "target/package/pid-runlog-$version.crate" "target/package/pid-core-$version.crate"

# This is a real Cargo package verification of pid-runlog, not merely a file-list check.
cargo package "${package_args[@]}" -p pid-runlog
runlog_archive="$REPO_ROOT/target/package/pid-runlog-$version.crate"
[[ -f "$runlog_archive" ]] || {
  echo "error: cargo did not create $runlog_archive" >&2
  exit 1
}

# Populate all third-party packages and index records from the checked-in lockfile. The local
# pid-runlog package is added afterwards because it intentionally is not on crates.io yet.
registry="$tmpdir/registry"
cargo local-registry sync "$REPO_ROOT/Cargo.lock" "$registry"

runlog_unpacked="$tmpdir/runlog-unpacked"
mkdir -p "$runlog_unpacked"
tar -xzf "$runlog_archive" -C "$runlog_unpacked"

python3 - "$runlog_unpacked/pid-runlog-$version/Cargo.toml" "$runlog_archive" "$registry" <<'PY'
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tomllib

manifest_path = Path(sys.argv[1])
archive_path = Path(sys.argv[2])
registry = Path(sys.argv[3])
manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
package = manifest["package"]
name = package["name"]
version = package["version"]

dependencies = []
for section, kind in (
    ("dependencies", None),
    ("build-dependencies", "build"),
    ("dev-dependencies", "dev"),
):
    for dependency_name, raw_specification in manifest.get(section, {}).items():
        specification = (
            {"version": raw_specification}
            if isinstance(raw_specification, str)
            else raw_specification
        )
        package_name = specification.get("package", dependency_name)
        renamed = package_name != dependency_name
        dependencies.append(
            {
                "name": dependency_name if renamed else package_name,
                "req": specification["version"],
                "features": sorted(specification.get("features", [])),
                "optional": specification.get("optional", False),
                "default_features": specification.get("default-features", True),
                "target": None,
                "kind": kind,
                "package": package_name if renamed else None,
            }
        )

dependencies.sort(
    key=lambda dependency: (
        dependency["name"],
        dependency["kind"] or "",
        dependency["req"],
    )
)
checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
entry = {
    "name": name,
    "vers": version,
    "deps": dependencies,
    "cksum": checksum,
    "features": {
        feature: sorted(values)
        for feature, values in manifest.get("features", {}).items()
    },
    "yanked": False,
}

lower_name = name.lower()
if len(lower_name) == 1:
    relative_index_path = Path("1") / lower_name
elif len(lower_name) == 2:
    relative_index_path = Path("2") / lower_name
elif len(lower_name) == 3:
    relative_index_path = Path("3") / lower_name[0] / lower_name
else:
    relative_index_path = Path(lower_name[:2]) / lower_name[2:4] / lower_name

index_path = registry / "index" / relative_index_path
index_path.parent.mkdir(parents=True, exist_ok=True)
index_path.write_text(
    json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
shutil.copyfile(archive_path, registry / f"{name}-{version}.crate")
PY

config="$tmpdir/cargo-config.toml"
python3 - "$registry" "$config" <<'PY'
import json
from pathlib import Path
import sys

registry = str(Path(sys.argv[1]).resolve())
Path(sys.argv[2]).write_text(
    "[source.crates-io]\n"
    'replace-with = "pid-rs-package-seed"\n\n'
    "[source.pid-rs-package-seed]\n"
    f"local-registry = {json.dumps(registry)}\n",
    encoding="utf-8",
)
PY

# Cargo now performs its normal package-content build against the temporary registry. This
# creates the same normalized archive that a registry-sequenced dry run will create later.
cargo package "${package_args[@]}" -p pid-core --config "$config"
core_archive="$REPO_ROOT/target/package/pid-core-$version.crate"
[[ -f "$core_archive" ]] || {
  echo "error: cargo did not create $core_archive" >&2
  exit 1
}

# Cargo's package verifier checks only the package's default target set. Unpack the exact archive
# and compile every shipped target with every feature, locked and offline, using only archived
# pid-runlog plus the lockfile-seeded registry. Runtime suites remain separate CI gates; `--no-run`
# keeps this check focused on whether the published contents are complete and buildable.
core_unpacked="$tmpdir/core-unpacked"
mkdir -p "$core_unpacked"
tar -xzf "$core_archive" -C "$core_unpacked"
CARGO_TARGET_DIR="$tmpdir/target" cargo test \
  --manifest-path "$core_unpacked/pid-core-$version/Cargo.toml" \
  --locked \
  --offline \
  --all-features \
  --all-targets \
  --no-run \
  --config "$config"

echo "verified pid-runlog-$version.crate and pid-core-$version.crate from packaged contents"
