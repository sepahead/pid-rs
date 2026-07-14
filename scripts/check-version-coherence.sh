#!/usr/bin/env bash
# Verify every public release-version/MSRV/author source in pid-rs.
#
# This script is read-only. Final-source mode validates an extracted release archive without
# requiring Git metadata. In tag mode it reads the tagged Git tree rather than trusting the current
# checkout. Tags are deliberately unsigned by repository policy, but releases must use an
# annotated, protected tag; artifact identity is provided by checksums and GitHub attestations.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/check-version-coherence.sh
  scripts/check-version-coherence.sh final-source vMAJOR.MINOR.PATCH
  scripts/check-version-coherence.sh vMAJOR.MINOR.PATCH

Without an argument, validate candidate working-tree and locked Cargo metadata. Final-source mode
validates finalized files and locked Cargo metadata in an extracted archive without `.git`. With a
tag, validate the annotated tag and all release metadata stored in its tree. Exit 0 means coherent;
1 means mismatch; 2 means invalid usage.
EOF
}

MODE=candidate
TAG=""
case "$#" in
  0) ;;
  1)
    case "$1" in
      -h|--help) usage; exit 0 ;;
      -*) usage >&2; exit 2 ;;
      *) MODE=tagged; TAG="$1" ;;
    esac
    ;;
  2)
    if [[ "$1" == final-source ]]; then
      MODE=final-source
      TAG="$2"
    else
      usage >&2
      exit 2
    fi
    ;;
  *) usage >&2; exit 2 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPECTED_AUTHOR="Sepehr Mahmoudian"

toml_workspace_value() {
  local key="$1"
  awk -v key="$key" '
    /^\[workspace\.package\][[:space:]]*$/ { in_section=1; next }
    /^\[/ { in_section=0 }
    in_section && $0 ~ "^[[:space:]]*" key "[[:space:]]*=" {
      line=$0
      sub(/^[^=]*=[[:space:]]*/, "", line)
      gsub(/["\x27]/, "", line)
      sub(/[[:space:]]*#.*/, "", line)
      sub(/[[:space:]]+$/, "", line)
      print line
      exit
    }
  '
}

cff_value() {
  local key="$1"
  awk -v key="$key" '$0 ~ "^" key "[[:space:]]*:" {
    line=$0
    sub(/^[^:]*:[[:space:]]*/, "", line)
    gsub(/["\x27]/, "", line)
    sub(/[[:space:]]*#.*/, "", line)
    sub(/[[:space:]]+$/, "", line)
    print line
    exit
  }'
}

dependency_version() {
  local dependency="$1"
  awk -v dependency="$dependency" '
    /^\[workspace\.dependencies\][[:space:]]*$/ || /^\[dependencies\][[:space:]]*$/ {
      in_section=1
      next
    }
    /^\[/ { in_section=0 }
    in_section && $0 ~ "^[[:space:]]*" dependency "[[:space:]]*=" {
      line=$0
      if (match(line, /version[[:space:]]*=[[:space:]]*"[^"]+"/)) {
        value=substr(line, RSTART, RLENGTH)
        sub(/^[^=]*=[[:space:]]*"/, "", value)
        sub(/"$/, "", value)
        print value
      }
      exit
    }
  '
}

lock_has_package_version() {
  local package="$1"
  local version="$2"
  awk -v package="$package" -v version="$version" '
    /^\[\[package\]\]/ { name=""; package_version="" }
    /^name = / {
      name=$0
      sub(/^name = "/, "", name)
      sub(/"$/, "", name)
    }
    /^version = / {
      package_version=$0
      sub(/^version = "/, "", package_version)
      sub(/"$/, "", package_version)
      if (name == package && package_version == version) found=1
    }
    END { exit(found ? 0 : 1) }
  '
}

require_contains() {
  local label="$1"
  local needle="$2"
  local content="$3"
  if [[ "$content" != *"$needle"* ]]; then
    PROBLEMS+=("$label does not contain required release text: $needle")
  fi
}

validate_streams() {
  local cargo_text="$1"
  local lock_text="$2"
  local cff_text="$3"
  local readme_text="$4"
  local changelog_text="$5"
  local security_text="$6"
  local migration_text="$7"
  local reproduction_text="$8"
  local scripts_readme_text="$9"
  local python_cargo_text="${10}"
  local python_project_text="${11}"
  local release_notes_text="${12}"
  local release_audit_text="${13}"
  local known_limitations_text="${14}"
  local core_cargo_text="${15}"
  local runlog_cargo_text="${16}"
  local release_workflow_text="${17}"

  VERSION="$(toml_workspace_value version <<<"$cargo_text")"
  RUST_VERSION="$(toml_workspace_value rust-version <<<"$cargo_text")"
  local cargo_authors cff_version cff_date cff_software_doi cff_lower changelog_date runlog_req python_core_req
  cargo_authors="$(toml_workspace_value authors <<<"$cargo_text")"
  cff_version="$(cff_value version <<<"$cff_text")"
  cff_date="$(cff_value date-released <<<"$cff_text")"
  cff_software_doi="$(cff_value doi <<<"$cff_text")"
  cff_lower="$(tr '[:upper:]' '[:lower:]' <<<"$cff_text")"
  changelog_date="$(awk -v version="$VERSION" '
    index($0, "## [" version "] - ") == 1 {
      sub("^## \\[" version "\\] - ", "")
      print
      exit
    }
  ' <<<"$changelog_text")"
  runlog_req="$(dependency_version pid-runlog <<<"$cargo_text")"
  python_core_req="$(dependency_version pid-core <<<"$python_cargo_text")"

  [[ -n "$VERSION" ]] || PROBLEMS+=("Cargo.toml has no workspace version")
  [[ -n "$RUST_VERSION" ]] || PROBLEMS+=("Cargo.toml has no workspace rust-version")
  [[ "$cff_version" == "$VERSION" ]] \
    || PROBLEMS+=("CITATION.cff version '$cff_version' != Cargo version '$VERSION'")
  [[ -z "$cff_software_doi" ]] \
    || PROBLEMS+=("0.9 review CITATION.cff must not declare a software DOI")
  [[ "$cff_lower" != *"zenodo"* ]] \
    || PROBLEMS+=("0.9 review CITATION.cff must not claim a Zenodo record")
  if [[ -n "$TAG" ]]; then
    [[ -n "$cff_date" && "$cff_date" == "$changelog_date" ]] \
      || PROBLEMS+=("CITATION.cff date '$cff_date' != CHANGELOG date '$changelog_date'")
  else
    [[ -z "$cff_date" ]] \
      || PROBLEMS+=("candidate CITATION.cff must omit date-released; found '$cff_date'")
    [[ "$changelog_date" == Unreleased ]] \
      || PROBLEMS+=("candidate CHANGELOG entry must be marked Unreleased")
  fi
  [[ "$runlog_req" == "$VERSION" ]] \
    || PROBLEMS+=("workspace pid-runlog requirement '$runlog_req' != '$VERSION'")
  [[ "$python_core_req" == "$VERSION" ]] \
    || PROBLEMS+=("pid-python pid-core requirement '$python_core_req' != '$VERSION'")
  [[ "$cargo_authors" == "[$EXPECTED_AUTHOR]" ]] \
    || PROBLEMS+=("Cargo author '$cargo_authors' != '[$EXPECTED_AUTHOR]'")

  require_contains "CITATION.cff" "given-names: Sepehr" "$cff_text"
  require_contains "CITATION.cff" "family-names: Mahmoudian" "$cff_text"
  require_contains "pid-python pyproject.toml" "authors = [{ name = \"$EXPECTED_AUTHOR\" }]" "$python_project_text"
  for field in version rust-version authors; do
    require_contains "pid-core Cargo.toml" "$field.workspace = true" "$core_cargo_text"
    require_contains "pid-runlog Cargo.toml" "$field.workspace = true" "$runlog_cargo_text"
    require_contains "pid-python Cargo.toml" "$field.workspace = true" "$python_cargo_text"
  done
  require_contains "README.md" "pid-core@$VERSION" "$readme_text"
  require_contains "README.md" "pid-core-rs==$VERSION" "$readme_text"
  require_contains "README.md" "MSRV $RUST_VERSION" "$readme_text"
  require_contains "CHANGELOG.md" "## [$VERSION]" "$changelog_text"
  require_contains "SECURITY.md" "Latest 0.x review release" "$security_text"
  require_contains "MIGRATION.md" "version $VERSION" "$migration_text"
  require_contains "RELEASE_REPRODUCTION.md" "v$VERSION" "$reproduction_text"
  require_contains "RELEASE_REPRODUCTION.md" "release immutability" "$reproduction_text"
  require_contains "RELEASE_NOTES.md" "pid-rs $VERSION" "$release_notes_text"
  require_contains "RELEASE_NOTES.md" "$EXPECTED_AUTHOR" "$release_notes_text"
  require_contains "RELEASE_AUDIT.md" "pid-rs 1.0" "$release_audit_text"
  require_contains "KNOWN_LIMITATIONS.md" "pid-rs 1.0" "$known_limitations_text"
  require_contains "scripts/README.md" "v$VERSION" "$scripts_readme_text"
  require_contains "release workflow" 'tags: ["v*.*.*"]' "$release_workflow_text"
  require_contains "release workflow" "scripts/check-version-coherence.sh" "$release_workflow_text"
  require_contains "release workflow" "name: release" "$release_workflow_text"
  require_contains "release workflow" "publish-runlog-seed" "$release_workflow_text"
  require_contains "release workflow" "REPRODUCTION_REPORT_URL" "$release_workflow_text"
  require_contains "release workflow" "FINAL_REVIEW_REPORT_URL" "$release_workflow_text"
  require_contains "release workflow" "draft: true" "$release_workflow_text"

  for package in pid-core pid-runlog pid-python; do
    if ! lock_has_package_version "$package" "$VERSION" <<<"$lock_text"; then
      PROBLEMS+=("Cargo.lock has no $package $VERSION entry")
    fi
  done
}

PROBLEMS=()
VERSION=""
RUST_VERSION=""

if [[ "$MODE" != candidate ]]; then
  if [[ ! "$TAG" =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    echo "ERROR: release reference must match vMAJOR.MINOR.PATCH; got '$TAG'" >&2
    exit 1
  fi
  TAG_VERSION="${BASH_REMATCH[1]}"
fi

if [[ "$MODE" == tagged ]]; then
  TAG_REF="refs/tags/$TAG"
  git -C "$REPO_ROOT" show-ref --verify --quiet "$TAG_REF" \
    || { echo "ERROR: missing exact tag $TAG_REF" >&2; exit 1; }
  [[ "$(git -C "$REPO_ROOT" cat-file -t "$TAG_REF")" == tag ]] \
    || { echo "ERROR: $TAG_REF must be an annotated tag (repository policy leaves it unsigned)" >&2; exit 1; }
  COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify "$TAG_REF^{commit}")"

  files=(Cargo.toml Cargo.lock CITATION.cff README.md CHANGELOG.md SECURITY.md MIGRATION.md \
    RELEASE_REPRODUCTION.md scripts/README.md crates/pid-python/Cargo.toml \
    crates/pid-python/pyproject.toml RELEASE_NOTES.md RELEASE_AUDIT.md KNOWN_LIMITATIONS.md \
    crates/pid-core/Cargo.toml crates/pid-runlog/Cargo.toml .github/workflows/release.yml)
  contents=()
  for file in "${files[@]}"; do
    contents+=("$(git -C "$REPO_ROOT" show "$COMMIT:$file")") \
      || { echo "ERROR: tagged tree is missing $file" >&2; exit 1; }
  done
  validate_streams "${contents[0]}" "${contents[1]}" "${contents[2]}" "${contents[3]}" \
    "${contents[4]}" "${contents[5]}" "${contents[6]}" "${contents[7]}" "${contents[8]}" \
    "${contents[9]}" "${contents[10]}" "${contents[11]}" "${contents[12]}" "${contents[13]}" \
    "${contents[14]}" "${contents[15]}" "${contents[16]}"
  [[ "$VERSION" == "$TAG_VERSION" ]] \
    || PROBLEMS+=("tag '$TAG' encodes '$TAG_VERSION' but tree records '$VERSION'")

  echo "Version coherence (annotated unsigned tag policy)"
  printf '  %-24s %s\n' tag "$TAG"
  printf '  %-24s %s\n' "peeled commit" "$COMMIT"
else
  required=(Cargo.toml Cargo.lock CITATION.cff README.md CHANGELOG.md SECURITY.md MIGRATION.md \
    RELEASE_REPRODUCTION.md scripts/README.md crates/pid-python/Cargo.toml \
    crates/pid-python/pyproject.toml RELEASE_NOTES.md RELEASE_AUDIT.md KNOWN_LIMITATIONS.md \
    crates/pid-core/Cargo.toml crates/pid-runlog/Cargo.toml .github/workflows/release.yml)
  for file in "${required[@]}"; do
    [[ -f "$REPO_ROOT/$file" ]] || PROBLEMS+=("missing required file $file")
  done
  if ((${#PROBLEMS[@]} == 0)); then
    validate_streams "$(<"$REPO_ROOT/Cargo.toml")" "$(<"$REPO_ROOT/Cargo.lock")" \
      "$(<"$REPO_ROOT/CITATION.cff")" "$(<"$REPO_ROOT/README.md")" \
      "$(<"$REPO_ROOT/CHANGELOG.md")" "$(<"$REPO_ROOT/SECURITY.md")" \
      "$(<"$REPO_ROOT/MIGRATION.md")" "$(<"$REPO_ROOT/RELEASE_REPRODUCTION.md")" \
      "$(<"$REPO_ROOT/scripts/README.md")" "$(<"$REPO_ROOT/crates/pid-python/Cargo.toml")" \
      "$(<"$REPO_ROOT/crates/pid-python/pyproject.toml")" "$(<"$REPO_ROOT/RELEASE_NOTES.md")" \
      "$(<"$REPO_ROOT/RELEASE_AUDIT.md")" "$(<"$REPO_ROOT/KNOWN_LIMITATIONS.md")" \
      "$(<"$REPO_ROOT/crates/pid-core/Cargo.toml")" \
      "$(<"$REPO_ROOT/crates/pid-runlog/Cargo.toml")" \
      "$(<"$REPO_ROOT/.github/workflows/release.yml")"
  fi

  if [[ "$MODE" == final-source && "$VERSION" != "$TAG_VERSION" ]]; then
    PROBLEMS+=("release reference '$TAG' encodes '$TAG_VERSION' but source records '$VERSION'")
  fi

  if ! metadata="$(cargo metadata --locked --format-version 1 --no-deps 2>&1)"; then
    PROBLEMS+=("cargo metadata --locked failed: $metadata")
  elif command -v python3 >/dev/null 2>&1; then
    if ! METADATA="$metadata" EXPECTED_VERSION="$VERSION" EXPECTED_AUTHOR="$EXPECTED_AUTHOR" \
      python3 - <<'PY'
import json
import os

metadata = json.loads(os.environ["METADATA"])
version = os.environ["EXPECTED_VERSION"]
author = os.environ["EXPECTED_AUTHOR"]
for package in metadata["packages"]:
    if package["version"] != version:
        raise SystemExit(f"{package['name']} version {package['version']} != {version}")
    if package["authors"] != [author]:
        raise SystemExit(f"{package['name']} authors {package['authors']!r} != {[author]!r}")
    for dependency in package["dependencies"]:
        if dependency.get("path") and dependency["name"] in {"pid-core", "pid-runlog"}:
            if dependency["req"] not in {version, f"^{version}", f"={version}"}:
                raise SystemExit(
                    f"{package['name']} -> {dependency['name']} requirement "
                    f"{dependency['req']} != {version}"
                )
PY
    then
      PROBLEMS+=("locked Cargo package/version/author/dependency metadata is incoherent")
    fi
  else
    PROBLEMS+=("python3 is required to validate locked Cargo metadata")
  fi

  if [[ "$MODE" == final-source ]]; then
    echo "Version coherence (finalized source archive)"
    printf '  %-24s %s\n' "release reference" "$TAG"
  else
    echo "Version coherence (working tree)"
  fi
fi

printf '  %-24s %s\n' version "${VERSION:-<missing>}"
printf '  %-24s %s\n' MSRV "${RUST_VERSION:-<missing>}"
printf '  %-24s %s\n' author "$EXPECTED_AUTHOR"

if ((${#PROBLEMS[@]} != 0)); then
  echo "MISMATCH:" >&2
  printf '  - %s\n' "${PROBLEMS[@]}" >&2
  exit 1
fi

if [[ "$MODE" == tagged ]]; then
  "$REPO_ROOT/scripts/check-release-state.sh" tagged "$TAG"
elif [[ "$MODE" == final-source ]]; then
  "$REPO_ROOT/scripts/check-release-state.sh" final-source "$TAG"
else
  "$REPO_ROOT/scripts/check-release-state.sh" candidate
fi

echo "OK: release metadata, locked packages, documentation, and author are coherent"
