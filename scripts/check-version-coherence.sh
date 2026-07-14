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
  scripts/check-version-coherence.sh review-source vMAJOR.MINOR.PATCH
  scripts/check-version-coherence.sh review-tagged vMAJOR.MINOR.PATCH
  scripts/check-version-coherence.sh final-source vMAJOR.MINOR.PATCH
  scripts/check-version-coherence.sh vMAJOR.MINOR.PATCH

Without an argument, validate candidate working-tree and locked Cargo metadata. Review-source
validates the exact dated 0.9.0 GitHub-only review-prerelease files and locked Cargo metadata in an
extracted archive without `.git`; review-tagged validates the exact annotated, unsigned tag tree.
Final-source validates finalized registry-release files in an extracted archive without `.git`.
With a tag as the sole argument, validate the annotated final-release tag and all metadata stored
in its tree. Exit 0 means coherent; 1 means mismatch; 2 means invalid usage.
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
    case "$1" in
      review-source|review-tagged|final-source)
        MODE="$1"
        TAG="$2"
        ;;
      *)
        usage >&2
        exit 2
        ;;
    esac
    ;;
  *) usage >&2; exit 2 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPECTED_AUTHOR="Sepehr Mahmoudian"
REVIEW_VERSION="0.9.0"
REVIEW_STATUS_MARKER="Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE."
REVIEW_MIGRATION_MARKER="pid-rs 0.9 is the published GitHub-only source-review prerelease for a proposed 1.0 API."
REVIEW_LIMITATIONS_MARKER="The published 0.9 GitHub-only source-review prerelease presents these proposed 1.0 limitations for reviewer feedback."
REVIEW_SECURITY_MARKER=$'| Latest 0.x source-review prerelease (`v0.9.0`) | ✅ |'
REVIEW_AUDIT_MARKER="The published 0.9 source-review prerelease is a GitHub-only source prerelease containing"
FINAL_STATUS_MARKER="Release status: FINAL REGISTRY RELEASE."

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

cff_top_level_author_count() {
  awk '
    /^[[:alnum:]_-]+[[:space:]]*:/ {
      key=$0
      sub(/[[:space:]]*:.*/, "", key)
      in_authors=(key == "authors")
      next
    }
    in_authors && /^[[:space:]][[:space:]]-[[:space:]]/ { count++ }
    END { print count + 0 }
  '
}

cff_top_level_author_value() {
  local field="$1"
  awk -v field="$field" '
    /^[[:alnum:]_-]+[[:space:]]*:/ {
      key=$0
      sub(/[[:space:]]*:.*/, "", key)
      in_authors=(key == "authors")
      next
    }
    in_authors && $0 ~ "^[[:space:]]+(-[[:space:]]*)?" field "[[:space:]]*:" {
      line=$0
      sub("^[[:space:]]+(-[[:space:]]*)?" field "[[:space:]]*:[[:space:]]*", "", line)
      gsub(/["\x27]/, "", line)
      sub(/[[:space:]]*#.*/, "", line)
      sub(/[[:space:]]+$/, "", line)
      print line
      exit
    }
  '
}

cff_has_top_level_software_doi() {
  awk '
    /^[[:alnum:]_-]+[[:space:]]*:/ {
      key=$0
      sub(/[[:space:]]*:.*/, "", key)
      in_identifiers=(key == "identifiers")
      if (key == "doi") found=1
      next
    }
    in_identifiers {
      lower=tolower($0)
      if (lower ~ /^[[:space:]]+(-[[:space:]]*)?type[[:space:]]*:[[:space:]]*["\x27]?doi(["\x27[:space:]#]|$)/) {
        found=1
      }
    }
    END { exit(found ? 0 : 1) }
  '
}

cff_has_top_level_zenodo_identifier() {
  awk '
    /^[[:alnum:]_-]+[[:space:]]*:/ {
      key=$0
      sub(/[[:space:]]*:.*/, "", key)
      value=tolower($0)
      sub(/^[^:]*:/, "", value)
      in_identifiers=(key == "identifiers")
      if (key ~ /^(doi|repository|repository-artifact|repository-code|url)$/ && value ~ /zenodo/) {
        found=1
      }
      next
    }
    in_identifiers && tolower($0) ~ /zenodo/ { found=1 }
    END { exit(found ? 0 : 1) }
  '
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

require_absent() {
  local label="$1"
  local needle="$2"
  local content="$3"
  if [[ "$content" == *"$needle"* ]]; then
    PROBLEMS+=("$label contains stale or contradictory release text: $needle")
  fi
}

require_occurrences() {
  local label="$1"
  local needle="$2"
  local expected="$3"
  local content="$4"
  local count=0
  local remainder="$content"
  while [[ "$remainder" == *"$needle"* ]]; do
    remainder="${remainder#*"$needle"}"
    ((count += 1))
  done
  if [[ "$count" -ne "$expected" ]]; then
    PROBLEMS+=("$label must contain '$needle' exactly $expected times; found $count")
  fi
}

workflow_job_text() {
  local job_id="$1"
  awk -v header="  $job_id:" '
    $0 == header { in_job=1 }
    in_job && $0 != header && $0 ~ /^  [[:alnum:]_-]+:[[:space:]]*$/ { exit }
    in_job { print }
  '
}

workflow_named_step_text() {
  local step_name="$1"
  awk -v header="      - name: $step_name" '
    $0 == header { in_step=1 }
    in_step && $0 != header && $0 ~ /^      - (name:|uses:)/ { exit }
    in_step { print }
  '
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
  local review_workflow_text="${18}"

  VERSION="$(toml_workspace_value version <<<"$cargo_text")"
  RUST_VERSION="$(toml_workspace_value rust-version <<<"$cargo_text")"
  local cargo_authors cff_version cff_date cff_author_count cff_family_name cff_given_name
  local changelog_date runlog_req python_core_req python_authors_count python_authors_line
  cargo_authors="$(toml_workspace_value authors <<<"$cargo_text")"
  cff_version="$(cff_value version <<<"$cff_text")"
  cff_date="$(cff_value date-released <<<"$cff_text")"
  cff_author_count="$(cff_top_level_author_count <<<"$cff_text")"
  cff_family_name="$(cff_top_level_author_value family-names <<<"$cff_text")"
  cff_given_name="$(cff_top_level_author_value given-names <<<"$cff_text")"
  changelog_date="$(awk -v version="$VERSION" '
    index($0, "## [" version "] - ") == 1 {
      sub("^## \\[" version "\\] - ", "")
      print
      exit
    }
  ' <<<"$changelog_text")"
  runlog_req="$(dependency_version pid-runlog <<<"$cargo_text")"
  python_core_req="$(dependency_version pid-core <<<"$python_cargo_text")"
  python_authors_line="$(awk '/^[[:space:]]*authors[[:space:]]*=/ { print; exit }' \
    <<<"$python_project_text")"
  python_authors_count="$(awk '/^[[:space:]]*authors[[:space:]]*=/ { count++ } END { print count + 0 }' \
    <<<"$python_project_text")"

  [[ -n "$VERSION" ]] || PROBLEMS+=("Cargo.toml has no workspace version")
  [[ "$VERSION" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] \
    || PROBLEMS+=("Cargo.toml workspace version is not exact SemVer: '$VERSION'")
  [[ -n "$RUST_VERSION" ]] || PROBLEMS+=("Cargo.toml has no workspace rust-version")
  [[ "$cff_version" == "$VERSION" ]] \
    || PROBLEMS+=("CITATION.cff version '$cff_version' != Cargo version '$VERSION'")
  if [[ "$MODE" == candidate || "$MODE" == review-source || "$MODE" == review-tagged ]]; then
    if cff_has_top_level_software_doi <<<"$cff_text"; then
      PROBLEMS+=("0.9 review CITATION.cff must not declare a top-level software DOI")
    fi
    if cff_has_top_level_zenodo_identifier <<<"$cff_text"; then
      PROBLEMS+=("0.9 review CITATION.cff must not declare a top-level Zenodo identifier")
    fi
  fi
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
  [[ "$cff_author_count" == 1 ]] \
    || PROBLEMS+=("CITATION.cff must contain exactly one top-level author; found '$cff_author_count'")
  [[ "$cff_given_name $cff_family_name" == "$EXPECTED_AUTHOR" ]] \
    || PROBLEMS+=("CITATION.cff sole top-level author '$cff_given_name $cff_family_name' != '$EXPECTED_AUTHOR'")
  [[ "$python_authors_count" == 1 \
    && "$python_authors_line" == "authors = [{ name = \"$EXPECTED_AUTHOR\" }]" ]] \
    || PROBLEMS+=("pid-python pyproject.toml must name exactly one author: $EXPECTED_AUTHOR")

  if [[ "$MODE" == review-source || "$MODE" == review-tagged ]]; then
    [[ "$VERSION" == "$REVIEW_VERSION" ]] \
      || PROBLEMS+=("$MODE is reserved for exact version '$REVIEW_VERSION'; found '$VERSION'")
  elif [[ "$MODE" == final-source || "$MODE" == tagged ]]; then
    [[ "$TAG_VERSION" =~ ^[1-9][0-9]*\. ]] \
      || PROBLEMS+=("$MODE is reserved for version 1.0.0 or later; found '$TAG_VERSION'")
  fi

  for field in version rust-version authors; do
    require_contains "pid-core Cargo.toml" "$field.workspace = true" "$core_cargo_text"
    require_contains "pid-runlog Cargo.toml" "$field.workspace = true" "$runlog_cargo_text"
    require_contains "pid-python Cargo.toml" "$field.workspace = true" "$python_cargo_text"
  done
  require_contains "README.md" "MSRV $RUST_VERSION" "$readme_text"
  require_contains "CHANGELOG.md" "## [$VERSION]" "$changelog_text"
  require_contains "MIGRATION.md" "version $VERSION" "$migration_text"
  require_contains "RELEASE_REPRODUCTION.md" "v$VERSION" "$reproduction_text"
  require_contains "RELEASE_NOTES.md" "pid-rs $VERSION" "$release_notes_text"
  require_contains "RELEASE_NOTES.md" "$EXPECTED_AUTHOR" "$release_notes_text"
  if [[ "$MODE" == candidate || "$MODE" == review-source || "$MODE" == review-tagged ]]; then
    require_contains "README.md" \
      "Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease." \
      "$readme_text"
    require_contains "README.md" \
      "This 0.9.0 review prerelease makes no 1.x compatibility promise." "$readme_text"
    require_contains "SECURITY.md" "Latest 0.x source-review prerelease" "$security_text"
    require_contains "RELEASE_REPRODUCTION.md" \
      "GitHub-only source prerelease for external review" "$reproduction_text"
    require_contains "RELEASE_NOTES.md" \
      "Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease." \
      "$release_notes_text"
    require_contains "RELEASE_NOTES.md" \
      "This 0.9.0 review prerelease makes no 1.x compatibility promise." "$release_notes_text"
  fi
  if [[ "$MODE" == candidate ]]; then
    require_contains "README.md" "Release status: CANDIDATE — not yet published." "$readme_text"
    require_contains "RELEASE_NOTES.md" "Release status: **DRAFT — not yet published**." \
      "$release_notes_text"
    require_contains "RELEASE_REPRODUCTION.md" "Release status: **CANDIDATE.**" \
      "$reproduction_text"
  elif [[ "$MODE" == review-source || "$MODE" == review-tagged ]]; then
    require_contains "README.md" "$REVIEW_STATUS_MARKER" "$readme_text"
    require_contains "RELEASE_NOTES.md" "$REVIEW_STATUS_MARKER" "$release_notes_text"
    require_contains "RELEASE_REPRODUCTION.md" "$REVIEW_STATUS_MARKER" "$reproduction_text"
    require_contains "MIGRATION.md" "$REVIEW_MIGRATION_MARKER" "$migration_text"
    require_contains "KNOWN_LIMITATIONS.md" "$REVIEW_LIMITATIONS_MARKER" \
      "$known_limitations_text"
    require_contains "SECURITY.md" "$REVIEW_SECURITY_MARKER" "$security_text"
    require_contains "RELEASE_AUDIT.md" "$REVIEW_AUDIT_MARKER" "$release_audit_text"
    require_absent "README.md" "Release status: CANDIDATE" "$readme_text"
    require_absent "RELEASE_NOTES.md" "Release status: **DRAFT" "$release_notes_text"
    require_absent "RELEASE_NOTES.md" "pid-rs 0.9.0 will be the first public" \
      "$release_notes_text"
    require_absent "RELEASE_NOTES.md" "The intended 0.9.0 release is" "$release_notes_text"
    require_absent "RELEASE_NOTES.md" "When published, GitHub release" "$release_notes_text"
    require_absent "RELEASE_REPRODUCTION.md" "Release status: **CANDIDATE.**" \
      "$reproduction_text"
    require_absent "RELEASE_REPRODUCTION.md" \
      $'No `v0.9.0` tag or GitHub prerelease is claimed' "$reproduction_text"
    require_absent "MIGRATION.md" "candidate public review release" "$migration_text"
    require_absent "KNOWN_LIMITATIONS.md" "The 0.9 candidate will publish" \
      "$known_limitations_text"
    require_absent "RELEASE_AUDIT.md" "The intended 0.9 publication" "$release_audit_text"
  else
    require_contains "README.md" "pid-core@$VERSION" "$readme_text"
    require_contains "README.md" "pid-core-rs==$VERSION" "$readme_text"
    require_contains "SECURITY.md" "| Latest ${VERSION%%.*}.x release | ✅ |" "$security_text"
    require_contains "RELEASE_REPRODUCTION.md" "release immutability" "$reproduction_text"
    require_contains "README.md" "$FINAL_STATUS_MARKER" "$readme_text"
    require_contains "RELEASE_NOTES.md" "$FINAL_STATUS_MARKER" "$release_notes_text"
    require_contains "RELEASE_REPRODUCTION.md" "$FINAL_STATUS_MARKER" "$reproduction_text"
    require_contains "MIGRATION.md" \
      "pid-rs version $VERSION is the qualified stable registry release." "$migration_text"
    require_contains "KNOWN_LIMITATIONS.md" \
      "The pid-rs $VERSION limitations apply to the qualified stable registry release." \
      "$known_limitations_text"
    require_contains "RELEASE_AUDIT.md" "The qualified pid-rs $VERSION release contains" \
      "$release_audit_text"
    for review_only_marker in \
      "$REVIEW_STATUS_MARKER" \
      "Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease." \
      "This 0.9.0 review prerelease makes no 1.x compatibility promise."; do
      require_absent "README.md" "$review_only_marker" "$readme_text"
      require_absent "RELEASE_NOTES.md" "$review_only_marker" "$release_notes_text"
    done
    require_absent "RELEASE_REPRODUCTION.md" "$REVIEW_STATUS_MARKER" "$reproduction_text"
    require_absent "MIGRATION.md" "$REVIEW_MIGRATION_MARKER" "$migration_text"
    require_absent "KNOWN_LIMITATIONS.md" "$REVIEW_LIMITATIONS_MARKER" \
      "$known_limitations_text"
    require_absent "SECURITY.md" "$REVIEW_SECURITY_MARKER" "$security_text"
    require_absent "RELEASE_AUDIT.md" "$REVIEW_AUDIT_MARKER" "$release_audit_text"
  fi
  require_contains "RELEASE_AUDIT.md" "pid-rs 1.0" "$release_audit_text"
  require_contains "KNOWN_LIMITATIONS.md" "pid-rs 1.0" "$known_limitations_text"
  require_contains "scripts/README.md" "v$VERSION" "$scripts_readme_text"
  require_contains "scripts/README.md" \
    'The standard workflow `GITHUB_TOKEN` cannot' "$scripts_readme_text"
  require_contains "scripts/README.md" \
    'administrator must not disable immutability between the check and publication' \
    "$scripts_readme_text"
  require_contains "scripts/README.md" \
    'strictly earlier attempt of the same workflow run' "$scripts_readme_text"
  require_contains "scripts/README.md" \
    'server-side lineage checks prevent a writer-planted immutable release' \
    "$scripts_readme_text"
  require_contains "scripts/README.md" \
    'verification is read-only and never attempts release deletion' "$scripts_readme_text"
  require_contains "release workflow" "workflow_dispatch:" "$release_workflow_text"
  require_contains "release workflow" "Exact final-release tag" "$release_workflow_text"
  require_contains "release workflow" "scripts/check-version-coherence.sh" "$release_workflow_text"
  require_contains "release workflow" "name: release" "$release_workflow_text"
  require_contains "release workflow" "publish-runlog-seed" "$release_workflow_text"
  require_contains "release workflow" "REPRODUCTION_REPORT_URL" "$release_workflow_text"
  require_contains "release workflow" "FINAL_REVIEW_REPORT_URL" "$release_workflow_text"
  require_contains "release workflow" "draft: true" "$release_workflow_text"
  if [[ "$release_workflow_text" == *$'\n  push:'* ]]; then
    PROBLEMS+=("release workflow must be manual-only, not tag-push-triggered")
  fi

  require_contains "review-release workflow" "name: Source review prerelease" \
    "$review_workflow_text"
  require_contains "review-release workflow" "workflow_dispatch:" "$review_workflow_text"
  require_contains "review-release workflow" "immutability_preflight:" "$review_workflow_text"
  local review_job_id review_job_text
  for review_job_id in verify-review-tag build-review-assets publish-review-prerelease; do
    review_job_text="$(workflow_job_text "$review_job_id" <<<"$review_workflow_text")"
    require_contains "review-release $review_job_id job" \
      "github.actor == github.repository_owner &&" "$review_job_text"
    require_contains "review-release $review_job_id job" \
      "github.triggering_actor == github.repository_owner" "$review_job_text"
    require_contains "review-release $review_job_id job" \
      "test \"\$GITHUB_ACTOR\" = \"\$GITHUB_REPOSITORY_OWNER\"" "$review_job_text"
    require_contains "review-release $review_job_id job" \
      "test \"\$GITHUB_TRIGGERING_ACTOR\" = \"\$GITHUB_REPOSITORY_OWNER\"" \
      "$review_job_text"
  done
  local verify_review_job_text build_review_job_text publish_review_job_text
  local review_preflight_step_text immutable_retry_step_text
  verify_review_job_text="$(workflow_job_text verify-review-tag <<<"$review_workflow_text")"
  build_review_job_text="$(workflow_job_text build-review-assets <<<"$review_workflow_text")"
  publish_review_job_text="$(workflow_job_text publish-review-prerelease \
    <<<"$review_workflow_text")"
  review_preflight_step_text="$(workflow_named_step_text \
    "Preflight the exact tag and review assets" <<<"$publish_review_job_text")"
  immutable_retry_step_text="$(workflow_named_step_text \
    "Verify immutable release identity and assets" <<<"$publish_review_job_text")"
  require_contains "review-release verify-review-tag job" \
    "--json attempt,conclusion,event,headBranch,headSha,status,url" "$verify_review_job_text"
  require_contains "review-release verify-review-tag job" \
    'echo "ci_run_attempt=$ci_run_attempt"' "$verify_review_job_text"
  require_contains "review-release build-review-assets job" \
    'echo "qualified_ci_run_attempt=$CI_RUN_ATTEMPT"' "$build_review_job_text"
  require_contains "review-release build-review-assets job" \
    'echo "qualified_ci_run_attempt_url=$CI_RUN_ATTEMPT_URL"' "$build_review_job_text"
  require_contains "review-release build-review-assets job" \
    'echo "immutability_preflight=$IMMUTABILITY_PREFLIGHT"' "$build_review_job_text"
  require_contains "review-release build-review-assets job" \
    'echo "release_notes_sha256=$(sha256sum RELEASE_NOTES.md' "$build_review_job_text"
  require_occurrences "review-release build-review-assets job" \
    'echo "registry_publication=none"' 1 "$build_review_job_text"
  require_contains "review-release build-review-assets job" \
    'review_artifact_id: ${{ steps.upload.outputs.artifact-id }}' "$build_review_job_text"
  require_contains "review-release build-review-assets job" \
    'review_artifact_digest: ${{ steps.upload.outputs.artifact-digest }}' "$build_review_job_text"
  require_contains "review-release build-review-assets job" \
    'name: review-release-assets-${{ inputs.tag }}-attempt-${{ github.run_attempt }}' \
    "$build_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'artifact-ids: ${{ needs.build-review-assets.outputs.review_artifact_id }}' \
    "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'and .digest == $digest' "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'review-release-assets-$REQUESTED_TAG-attempt-$EXPECTED_ARTIFACT_RUN_ATTEMPT' \
    "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'target_commitish: ${{ needs.verify-review-tag.outputs.peeled_commit }}' \
    "$publish_review_job_text"
  require_occurrences "review-release publish-review-prerelease job" \
    'git ls-remote origin "$tag_ref" "$peeled_ref"' 4 "$publish_review_job_text"
  require_occurrences "review-release publish-review-prerelease job" \
    'and .body == $body' 5 "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    '{draft: false, prerelease: true, make_latest: "false", name: $name, body: $body}' \
    "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'Release was previously observed immutable; refusing mutation or deletion' \
    "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'trap cleanup_mutable_review_release EXIT' "$publish_review_job_text"
  require_contains "review-release publish-review-prerelease job" \
    'cleanup_required=true' "$publish_review_job_text"
  require_occurrences "review-release publish-review-prerelease job" \
    'and .target_commitish == $commit' 2 "$publish_review_job_text"
  local retry_lineage_needle
  for retry_lineage_needle in \
    '.tag_name == $tag' \
    'and .target_commitish == $commit' \
    'and .draft == false' \
    'and .immutable == true'
  do
    require_contains "review-release immutable-existing-release preflight" \
      "$retry_lineage_needle" "$review_preflight_step_text"
  done

  for retry_lineage_needle in \
    'ALREADY_PUBLISHED: ${{ steps.preflight.outputs.already_published }}' \
    'if [[ "$ALREADY_PUBLISHED" == true ]]' \
    'test "$(wc -l < "$published_provenance")" -eq 28' \
    'if (count != 1)' \
    'test "$original_workflow_attempt" -lt "$GITHUB_RUN_ATTEMPT"' \
    'require_provenance_value workflow_run_id "$GITHUB_RUN_ID"' \
    'require_provenance_value dispatch_actor "$GITHUB_REPOSITORY_OWNER"' \
    'require_provenance_value triggering_actor "$GITHUB_REPOSITORY_OWNER"' \
    'require_provenance_value repository_owner "$GITHUB_REPOSITORY_OWNER"' \
    'actions/runs/$GITHUB_RUN_ID/attempts/$original_workflow_attempt"' \
    '(.id | tostring) == $workflow_run_id' \
    '(.run_attempt | tostring) == $workflow_attempt' \
    'and .event == "workflow_dispatch"' \
    'and .head_sha == $workflow_commit' \
    '.path == ".github/workflows/review-release.yml"' \
    'and .actor.login == $workflow_owner' \
    'and .triggering_actor.login == $workflow_owner' \
    'and .repository.full_name == $workflow_repository' \
    'original_jobs="$(gh api --paginate --slurp' \
    'actions/runs/$GITHUB_RUN_ID/attempts/$original_workflow_attempt/jobs?per_page=100"' \
    '[.[]?.jobs[]? | select(.name == "Publish immutable source-review prerelease")]' \
    'test "$(jq length <<<"$publishing_jobs")" -eq 1' \
    'and (.[0].run_id | tostring) == $workflow_run_id' \
    'and .[0].head_sha == $workflow_commit' \
    'and .[0].workflow_name == "Source review prerelease"' \
    '([.[0].steps[] | select(.name == $name)] | length) == 1' \
    '[0].conclusion == "success"' \
    'actions/runs/$original_ci_run_id/attempts/$original_ci_run_attempt"' \
    '(.id | tostring) == $ci_run_id' \
    '(.run_attempt | tostring) == $ci_attempt' \
    'and .event == "push"' \
    'and .head_branch == $ci_tag' \
    'and .head_sha == $ci_commit' \
    '.path == ".github/workflows/ci.yml"' \
    'and .repository.full_name == $ci_repository' \
    'and .conclusion == "success"' \
    'and ([.[].name] | sort) == ([' \
    'cmp SHA256SUMS "$RUNNER_TEMP/published-SHA256SUMS"' \
    'cmp SHA512SUMS "$RUNNER_TEMP/published-SHA512SUMS"' \
    'cmp release/RELEASE_SCOPE_1_0.md' \
    'cmp release/release-scope-1.0.json' \
    'cmp "release/$source_archive"' \
    'for published_asset in downloaded-after-publication/*'
  do
    require_contains "review-release immutable retry verifier" \
      "$retry_lineage_needle" "$immutable_retry_step_text"
  done
  for retry_lineage_needle in \
    '"Reconfirm owner authorization"' \
    '"Preflight the exact tag and review assets"' \
    '"Revalidate the exact tag before creating the draft"' \
    '"Create the draft source-review prerelease"' \
    '"Byte-verify the draft asset set"' \
    '"Publish as a prerelease without changing latest"'
  do
    require_contains "review-release immutable retry publication-step lineage" \
      "$retry_lineage_needle" "$immutable_retry_step_text"
  done
  require_occurrences "review-release immutable retry verifier" \
    'and .status == "completed"' 2 "$immutable_retry_step_text"
  if [[ "$immutable_retry_step_text" == *'--method DELETE'* ]]; then
    PROBLEMS+=("review-release immutable retry verifier must not delete a release already observed immutable")
  fi
  require_contains "review-release workflow" \
    "echo \"dispatch_actor=\$GITHUB_ACTOR\"" "$review_workflow_text"
  require_contains "review-release workflow" \
    "echo \"triggering_actor=\$GITHUB_TRIGGERING_ACTOR\"" "$review_workflow_text"
  require_contains "review-release workflow" \
    "echo \"repository_owner=\$GITHUB_REPOSITORY_OWNER\"" "$review_workflow_text"
  require_contains "review-release workflow" "test \"\$IMMUTABILITY_PREFLIGHT\" = ENABLED" \
    "$review_workflow_text"
  require_contains "review-release workflow" "test \"\$REQUESTED_TAG\" = v0.9.0" \
    "$review_workflow_text"
  require_contains "review-release workflow" \
    "test \"\$peeled_commit\" = \"\$GITHUB_SHA\"" \
    "$review_workflow_text"
  require_contains "review-release workflow" "ref: refs/tags/\${{ inputs.tag }}" \
    "$review_workflow_text"
  require_contains "review-release workflow" \
    "scripts/check-version-coherence.sh review-tagged \"\$REQUESTED_TAG\"" \
    "$review_workflow_text"
  require_contains "review-release workflow" "prerelease: true" "$review_workflow_text"
  if [[ "$review_workflow_text" == *$'\n  push:'* ]]; then
    PROBLEMS+=("review-release workflow must be manual-only, not tag-push-triggered")
  fi
  if [[ "$review_workflow_text" == *"repos/\$GITHUB_REPOSITORY/immutable-releases"* ]]; then
    PROBLEMS+=("review-release workflow must not call the Administration-scoped immutability-settings endpoint with GITHUB_TOKEN")
  fi

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
  if [[ ! "$TAG" =~ ^v((0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*))$ ]]; then
    echo "ERROR: release reference must match vMAJOR.MINOR.PATCH; got '$TAG'" >&2
    exit 1
  fi
  TAG_VERSION="${BASH_REMATCH[1]}"
fi

if [[ "$MODE" == tagged || "$MODE" == review-tagged ]]; then
  TAG_REF="refs/tags/$TAG"
  git -C "$REPO_ROOT" show-ref --verify --quiet "$TAG_REF" \
    || { echo "ERROR: missing exact tag $TAG_REF" >&2; exit 1; }
  [[ "$(git -C "$REPO_ROOT" cat-file -t "$TAG_REF")" == tag ]] \
    || { echo "ERROR: $TAG_REF must be an annotated tag (repository policy leaves it unsigned)" >&2; exit 1; }
  tag_object="$(git -C "$REPO_ROOT" cat-file tag "$TAG_REF")"
  embedded_object_type="$(awk '/^type / { sub(/^type /, ""); print; exit }' <<<"$tag_object")"
  [[ "$embedded_object_type" == commit ]] || {
    echo "ERROR: $TAG_REF must directly annotate a commit, not '$embedded_object_type'" >&2
    exit 1
  }
  embedded_tag="$(awk '/^tag / { sub(/^tag /, ""); print; exit }' <<<"$tag_object")"
  [[ "$embedded_tag" == "$TAG" ]] || {
    echo "ERROR: $TAG_REF points to an annotated tag object named '$embedded_tag', not '$TAG'" >&2
    exit 1
  }
  if grep -Eq -- '-----BEGIN (PGP|SSH) SIGNATURE-----|-----BEGIN SIGNED MESSAGE-----' \
    <<<"$tag_object"; then
    echo "ERROR: $TAG_REF is signed; repository policy requires an unsigned annotated tag" >&2
    exit 1
  fi
  COMMIT="$(git -C "$REPO_ROOT" rev-parse --verify "$TAG_REF^{commit}")"

  files=(Cargo.toml Cargo.lock CITATION.cff README.md CHANGELOG.md SECURITY.md MIGRATION.md \
    RELEASE_REPRODUCTION.md scripts/README.md crates/pid-python/Cargo.toml \
    crates/pid-python/pyproject.toml RELEASE_NOTES.md RELEASE_AUDIT.md KNOWN_LIMITATIONS.md \
    crates/pid-core/Cargo.toml crates/pid-runlog/Cargo.toml .github/workflows/release.yml \
    .github/workflows/review-release.yml)
  contents=()
  for file in "${files[@]}"; do
    tree_entry="$(git -C "$REPO_ROOT" ls-tree "$COMMIT" -- "$file")"
    read -r tree_mode tree_type _tree_object _tree_path <<<"$tree_entry"
    if [[ "$tree_type" != blob \
      || ("$tree_mode" != 100644 && "$tree_mode" != 100755) ]]; then
      PROBLEMS+=("required tagged file must be a regular blob: $file")
      contents+=("")
    else
      contents+=("$(git -C "$REPO_ROOT" show "$COMMIT:$file")") \
        || { echo "ERROR: tagged tree is missing $file" >&2; exit 1; }
    fi
  done
  validate_streams "${contents[0]}" "${contents[1]}" "${contents[2]}" "${contents[3]}" \
    "${contents[4]}" "${contents[5]}" "${contents[6]}" "${contents[7]}" "${contents[8]}" \
    "${contents[9]}" "${contents[10]}" "${contents[11]}" "${contents[12]}" "${contents[13]}" \
    "${contents[14]}" "${contents[15]}" "${contents[16]}" "${contents[17]}"
  [[ "$VERSION" == "$TAG_VERSION" ]] \
    || PROBLEMS+=("tag '$TAG' encodes '$TAG_VERSION' but tree records '$VERSION'")

  if [[ "$MODE" == review-tagged ]]; then
    echo "Version coherence (GitHub-only review prerelease tag)"
  else
    echo "Version coherence (annotated unsigned tag policy)"
  fi
  printf '  %-24s %s\n' tag "$TAG"
  printf '  %-24s %s\n' "peeled commit" "$COMMIT"
else
  required=(Cargo.toml Cargo.lock CITATION.cff README.md CHANGELOG.md SECURITY.md MIGRATION.md \
    RELEASE_REPRODUCTION.md scripts/README.md crates/pid-python/Cargo.toml \
    crates/pid-python/pyproject.toml RELEASE_NOTES.md RELEASE_AUDIT.md KNOWN_LIMITATIONS.md \
    crates/pid-core/Cargo.toml crates/pid-runlog/Cargo.toml .github/workflows/release.yml \
    .github/workflows/review-release.yml)
  for file in "${required[@]}"; do
    [[ -f "$REPO_ROOT/$file" ]] || PROBLEMS+=("missing required file $file")
    [[ ! -L "$REPO_ROOT/$file" ]] \
      || PROBLEMS+=("required source file must not be a symlink: $file")
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
      "$(<"$REPO_ROOT/.github/workflows/release.yml")" \
      "$(<"$REPO_ROOT/.github/workflows/review-release.yml")"
  fi

  if [[ "$MODE" == final-source || "$MODE" == review-source ]]; then
    [[ "$VERSION" == "$TAG_VERSION" ]] \
      || PROBLEMS+=("release reference '$TAG' encodes '$TAG_VERSION' but source records '$VERSION'")
  fi

  if ! metadata="$(cargo metadata --manifest-path "$REPO_ROOT/Cargo.toml" --locked \
    --format-version 1 --no-deps 2>&1)"; then
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
  elif [[ "$MODE" == review-source ]]; then
    echo "Version coherence (GitHub-only review-prerelease source archive)"
    printf '  %-24s %s\n' "review reference" "$TAG"
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
elif [[ "$MODE" == review-tagged ]]; then
  "$REPO_ROOT/scripts/check-release-state.sh" review-tagged "$TAG"
elif [[ "$MODE" == review-source ]]; then
  "$REPO_ROOT/scripts/check-release-state.sh" review-source "$TAG"
elif [[ "$MODE" == final-source ]]; then
  "$REPO_ROOT/scripts/check-release-state.sh" final-source "$TAG"
else
  "$REPO_ROOT/scripts/check-release-state.sh" candidate
fi

echo "OK: release metadata, locked packages, documentation, and author are coherent"
