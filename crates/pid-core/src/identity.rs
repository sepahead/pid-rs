//! Typed software and source identity for reproducible estimator records.
//!
//! Method catalog: software.software-identity-contract
//!
//! **PROJECT-DEFINED SOFTWARE CONTRACT.** This infrastructure implements no estimator and claims
//! no new mathematics or paper-defined method. It keeps public Rust API signature identity, source identity,
//! selected build context, forensic reference-artifact digests, and binary-attestation status
//! separate. Equality of the envelope or any digest does not establish API compatibility,
//! scientific or application validity, data quality, source/archive/executable equality, or
//! cross-platform numerical identity.

use serde::Serialize;

#[derive(Debug, Clone, Copy)]
pub(crate) struct EmbeddedReferenceArtifact {
    pub(crate) canonical_json_sha256: &'static str,
    pub(crate) digest_scope: &'static str,
    pub(crate) kind: &'static str,
    pub(crate) repository_path: &'static str,
    pub(crate) role: &'static str,
    pub(crate) schema: &'static str,
    pub(crate) schema_revision: u32,
}

mod generated {
    include!(concat!(env!("OUT_DIR"), "/software_identity_build.rs"));
}

/// Review status of the public Rust API signature surface.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum PublicRustApiSignatureStatus {
    /// The 0.x API remains under review and makes no 1.x compatibility promise.
    #[serde(rename = "pre_1_0_review")]
    PreOneReview,
}

impl PublicRustApiSignatureStatus {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PreOneReview => "pre_1_0_review",
        }
    }
}

/// Public Rust API signature profile set covered by a signature revision.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum PublicRustApiSignatureScope {
    /// Exact feature profiles enumerated by the proposed release-scope artifact.
    ///
    /// This excludes the Python API/ABI, method or estimand definitions, numerical behavior,
    /// package versions, scientific evidence, and executable bytes.
    #[serde(rename = "proposed_release_scope_profiles")]
    ProposedReleaseScopeProfiles,
}

impl PublicRustApiSignatureScope {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ProposedReleaseScopeProfiles => "proposed_release_scope_profiles",
        }
    }
}

/// Explicit binary-attestation state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum AttestationStatus {
    /// No executable, dependency graph, linker input, or binary digest is attested.
    #[serde(rename = "none")]
    None,
}

impl AttestationStatus {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::None => "none",
        }
    }
}

/// Public Rust API signature identity, separate from behavior, package version, and build context.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct PublicRustApiSignatureIdentity {
    epoch: u32,
    revision: u32,
    scope: PublicRustApiSignatureScope,
    status: PublicRustApiSignatureStatus,
}

impl PublicRustApiSignatureIdentity {
    /// Compatibility epoch. Pre-1.0 review builds deliberately remain in epoch zero.
    pub const fn epoch(&self) -> u32 {
        self.epoch
    }

    /// Repository-declared public Rust API signature revision.
    ///
    /// This advances whenever a public Rust signature in one of the exact proposed release-scope
    /// profiles changes. It may also advance when the governed scope, review status, or epoch
    /// changes even if the declaration snapshots do not. The forensic release-scope reference
    /// binds the profile list and snapshot evidence. Within epoch zero, a change means downstreams
    /// should review compatibility; it does not create a 1.x promise. It does not version Python
    /// API/ABI, estimator definitions, numerical behavior, or scientific validity. The separate
    /// `identity_format` field versions this serialized envelope.
    pub const fn revision(&self) -> u32 {
        self.revision
    }

    /// Exact public-Rust-API surface governed by `revision`.
    pub const fn scope(&self) -> PublicRustApiSignatureScope {
        self.scope
    }

    /// Current review/compatibility status.
    pub const fn status(&self) -> PublicRustApiSignatureStatus {
        self.status
    }
}

/// Whether a Git working tree or Cargo package was clean when source identity was captured.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum WorkingTreeState {
    /// Workspace probes reported no scoped change or visibility mask, or Cargo explicitly
    /// recorded `dirty: false` in package metadata.
    #[serde(rename = "clean")]
    Clean,
    /// A relevant change or route-recognized visibility mask was observed.
    #[serde(rename = "dirty")]
    Dirty,
    /// The commit was available but the scoped state could not be established completely. The
    /// workspace route uses this for unsupported Git versions, command failures, concurrent-change
    /// evidence, any effective `filter` attribute on a tracked package path (including unset or
    /// unconfigured values), `attr.tree`, tracked symbolic links, and tracked gitlinks rather than
    /// executing or recursively inspecting external state. A clean/dirty result assumes repository
    /// metadata and package files remain stable during the bounded, non-atomic probe.
    #[serde(rename = "unknown")]
    Unknown,
}

impl WorkingTreeState {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Clean => "clean",
            Self::Dirty => "dirty",
            Self::Unknown => "unknown",
        }
    }
}

/// Scope over which a source route observed working-tree state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum WorkingTreeScope {
    /// The `crates/pid-core` path in a layout-matched workspace.
    #[serde(rename = "crates/pid-core")]
    PidCorePackagePath,
    /// Cargo's version-dependent, best-effort `.cargo_vcs_info.json` dirty observation. An absent
    /// `dirty` field is unknown rather than clean.
    #[serde(rename = "cargo_vcs_info_dirty_flag")]
    CargoVcsInfoDirtyFlag,
}

impl WorkingTreeScope {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PidCorePackagePath => "crates/pid-core",
            Self::CargoVcsInfoDirtyFlag => "cargo_vcs_info_dirty_flag",
        }
    }
}

/// Why no source commit could be embedded through a recognized route.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum SourceUnavailableReason {
    /// Cargo package metadata existed, was unreadable or unverifiable, was malformed, or
    /// described another package path.
    #[serde(rename = "invalid_cargo_vcs_info")]
    InvalidCargoVcsInfo,
    /// The crate was not in the exact canonical pid-rs workspace layout.
    #[serde(rename = "unrecognized_workspace_layout")]
    UnrecognizedWorkspaceLayout,
    /// The exact workspace layout matched, but Git could not establish the expected repository
    /// root or resolve its current commit.
    #[serde(rename = "git_unavailable")]
    GitUnavailable,
    /// Git returned a value other than the lowercase 40-hex SHA-1 object identity accepted by
    /// format 1. Git repositories using SHA-256 object identities are intentionally unsupported.
    #[serde(rename = "invalid_git_commit")]
    InvalidGitCommit,
}

impl SourceUnavailableReason {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::InvalidCargoVcsInfo => "invalid_cargo_vcs_info",
            Self::UnrecognizedWorkspaceLayout => "unrecognized_workspace_layout",
            Self::GitUnavailable => "git_unavailable",
            Self::InvalidGitCommit => "invalid_git_commit",
        }
    }
}

/// Package-safe source identity.
///
/// Git is the only source route when the crate is in the exact layout-matched pid-rs workspace;
/// any Git failure there yields [`SourceIdentity::Unavailable`] and never falls through to Cargo
/// metadata. Cargo package metadata is consulted only for non-layout-matched packages, preventing
/// an extracted package from inheriting an enclosing, unrelated repository identity.
/// "Layout-matched" is not an integrity or authenticity claim. Format 1 accepts commit identifiers
/// only as lowercase 40-hex SHA-1 strings.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
#[non_exhaustive]
pub enum SourceIdentity {
    /// Identity obtained from the exact layout-matched workspace. `working_tree` describes tracked,
    /// untracked, and ignored entries plus skip-worktree or assume-unchanged index masks under
    /// `crates/pid-core` at build-script execution time. Workspace files (including `Cargo.lock`)
    /// and sibling crates are outside this flag. Root reference-artifact bytes are checked
    /// separately against their embedded digests. The value is a cached build snapshot, not a
    /// live Git-tool or object-store availability monitor.
    #[non_exhaustive]
    WorkspaceGit {
        /// Lowercase 40-hex SHA-1 identity of the workspace commit.
        commit_sha1: &'static str,
        /// Machine-readable scope of the working-tree observation.
        working_tree_scope: WorkingTreeScope,
        /// Observed state under the `crates/pid-core` workspace pathspec.
        working_tree: WorkingTreeState,
    },
    /// Identity read from Cargo's best-effort package metadata. This describes the checkout when
    /// the archive was created, does not imply registry publication, and does not prove that the
    /// archive bytes equal the named commit.
    #[non_exhaustive]
    CargoPackage {
        /// Lowercase 40-hex SHA-1 copied from Cargo package metadata.
        commit_sha1: &'static str,
        /// Machine-readable scope of Cargo's archive-creation observation.
        working_tree_scope: WorkingTreeScope,
        /// Cargo's version-dependent, best-effort archive-creation observation. Explicit `true`
        /// is dirty, explicit `false` is clean, and an absent field is unknown. This is not the
        /// extracted tree's current state, and pid-rs does not reinterpret it as a complete
        /// whole-repository observation.
        working_tree: WorkingTreeState,
    },
    /// No source commit could be obtained through either recognized route.
    #[non_exhaustive]
    Unavailable {
        /// Typed reason that source identity is unavailable.
        reason: SourceUnavailableReason,
    },
}

/// Compiler and Cargo configuration captured at build time.
///
/// This context intentionally omits dependency artifacts, linker inputs, environment, arbitrary
/// compiler flags, and executable bytes. It must not be interpreted as a binary fingerprint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct BuildContext {
    rustc_version: Option<&'static str>,
    target_triple: &'static str,
    profile: &'static str,
    opt_level: &'static str,
    debug_information: bool,
    enabled_features: &'static [&'static str],
}

impl BuildContext {
    /// Compiler version, or `None` if the compiler version probe failed.
    pub const fn rustc_version(&self) -> Option<&'static str> {
        self.rustc_version
    }

    /// Cargo target triple compiled by this pid-core instance.
    pub const fn target_triple(&self) -> &'static str {
        self.target_triple
    }

    /// Cargo profile value reported to the build script; it is not a complete custom-profile
    /// identity. `opt_level` and `debug_information` preserve two material settings separately.
    pub const fn profile(&self) -> &'static str {
        self.profile
    }

    /// Cargo optimization-level value reported to the build script.
    pub const fn opt_level(&self) -> &'static str {
        self.opt_level
    }

    /// Whether Cargo requested compiler debug information; this is not `debug_assertions`.
    pub const fn debug_information(&self) -> bool {
        self.debug_information
    }

    /// Exact enabled pid-core Cargo feature names, in lexical order.
    pub const fn enabled_features(&self) -> &'static [&'static str] {
        self.enabled_features
    }
}

/// Kind of repository artifact referenced by a forensic digest.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum ReferenceArtifactKind {
    /// Fine-grained paper/code/method provenance catalog.
    #[serde(rename = "method_catalog")]
    MethodCatalog,
    /// Proposed, not-yet-qualified 1.0 public capability scope.
    #[serde(rename = "proposed_release_scope")]
    ProposedReleaseScope,
}

impl ReferenceArtifactKind {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::MethodCatalog => "method_catalog",
            Self::ProposedReleaseScope => "proposed_release_scope",
        }
    }
}

/// Interpretation boundary for an embedded reference-artifact digest.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum ReferenceArtifactRole {
    /// Identifies canonical repository-file bytes; does not certify compatibility or validity.
    #[serde(rename = "forensic_reference_only")]
    ForensicReferenceOnly,
}

impl ReferenceArtifactRole {
    /// Machine spelling fixed for identity format 1; changing it requires a format bump.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ForensicReferenceOnly => "forensic_reference_only",
        }
    }
}

/// Digest identity of one canonical repository metadata artifact.
///
/// In a layout-matched workspace build, pid-rs verifies the current file at `repository_path`
/// against this value. A packaged build carries the manifest-declared value and need not have the
/// repository-relative file available locally. Neither route claims the bytes are a checked-in Git
/// blob.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct ReferenceArtifactIdentity {
    kind: ReferenceArtifactKind,
    repository_path: &'static str,
    schema: &'static str,
    schema_revision: u32,
    digest_scope: &'static str,
    canonical_json_sha256: &'static str,
    role: ReferenceArtifactRole,
}

impl ReferenceArtifactIdentity {
    /// Artifact kind with a stable cross-language spelling.
    pub const fn kind(&self) -> ReferenceArtifactKind {
        self.kind
    }

    /// Canonical repository-relative path; never an absolute build-host path. The referenced file
    /// need not exist beside an extracted package.
    pub const fn repository_path(&self) -> &'static str {
        self.repository_path
    }

    /// Machine schema identity declared by the referenced JSON artifact.
    pub const fn schema(&self) -> &'static str {
        self.schema
    }

    /// Machine schema revision declared by the referenced JSON artifact.
    pub const fn schema_revision(&self) -> u32 {
        self.schema_revision
    }

    /// Exact byte domain hashed by `canonical_json_sha256`.
    ///
    /// Format 1 hashes the canonical repository file's exact raw bytes. Verifiers must not parse
    /// and re-serialize the JSON before hashing; the bytes need not be a checked-in Git blob.
    pub const fn digest_scope(&self) -> &'static str {
        self.digest_scope
    }

    /// Lowercase SHA-256 of the exact raw canonical repository-file bytes. Layout-matched workspace
    /// builds verify the current file; packaged builds carry the manifest-declared digest.
    pub const fn canonical_json_sha256(&self) -> &'static str {
        self.canonical_json_sha256
    }

    /// Interpretation boundary for this digest.
    pub const fn role(&self) -> ReferenceArtifactRole {
        self.role
    }
}

/// Typed software identity for the compiled pid-core instance.
///
/// This identifies public Rust API signature revision, source context, selected build configuration, and
/// canonical repository references. It does not establish API compatibility, that an estimator's
/// assumptions hold, that an application or input data are suitable, that source/archive/binary
/// bytes agree, or that numerical results are cross-platform identical.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct SoftwareIdentity {
    identity_format: u32,
    package_name: &'static str,
    package_version: &'static str,
    public_rust_api_signature_identity: PublicRustApiSignatureIdentity,
    source: SourceIdentity,
    build: BuildContext,
    reference_artifacts: [ReferenceArtifactIdentity; 2],
    attestation: AttestationStatus,
}

impl SoftwareIdentity {
    /// Version of this serialized identity envelope.
    pub const fn identity_format(&self) -> u32 {
        self.identity_format
    }

    /// Cargo package name, which may differ from the Rust crate identifier.
    pub const fn package_name(&self) -> &'static str {
        self.package_name
    }

    /// Cargo package version; independent from public Rust API signature revision.
    pub const fn package_version(&self) -> &'static str {
        self.package_version
    }

    /// Repository-declared public Rust API signature identity.
    pub const fn public_rust_api_signature_identity(&self) -> &PublicRustApiSignatureIdentity {
        &self.public_rust_api_signature_identity
    }

    /// Package-safe source context.
    pub const fn source(&self) -> &SourceIdentity {
        &self.source
    }

    /// Selected build configuration, explicitly incomplete as a binary identity.
    pub const fn build(&self) -> &BuildContext {
        &self.build
    }

    /// Forensic metadata references; their digests do not certify validity or compatibility.
    pub const fn reference_artifacts(&self) -> &[ReferenceArtifactIdentity] {
        &self.reference_artifacts
    }

    /// Explicit executable-attestation status.
    pub const fn attestation(&self) -> AttestationStatus {
        self.attestation
    }
}

/// Return the identity embedded in this compiled pid-core instance.
pub fn software_identity() -> SoftwareIdentity {
    SoftwareIdentity {
        identity_format: generated::IDENTITY_FORMAT,
        package_name: env!("CARGO_PKG_NAME"),
        package_version: env!("CARGO_PKG_VERSION"),
        public_rust_api_signature_identity: PublicRustApiSignatureIdentity {
            epoch: generated::PUBLIC_RUST_API_EPOCH,
            revision: generated::PUBLIC_RUST_API_REVISION,
            scope: public_rust_api_signature_scope(),
            status: api_status(),
        },
        source: source_identity(),
        build: BuildContext {
            rustc_version: generated::RUSTC_VERSION,
            target_triple: generated::TARGET_TRIPLE,
            profile: generated::PROFILE,
            opt_level: generated::OPT_LEVEL,
            debug_information: generated::DEBUG_INFORMATION,
            enabled_features: generated::ENABLED_FEATURES,
        },
        reference_artifacts: [
            reference_artifact(generated::REFERENCE_ARTIFACTS[0]),
            reference_artifact(generated::REFERENCE_ARTIFACTS[1]),
        ],
        attestation: attestation_status(),
    }
}

fn api_status() -> PublicRustApiSignatureStatus {
    match generated::PUBLIC_RUST_API_STATUS {
        "pre_1_0_review" => PublicRustApiSignatureStatus::PreOneReview,
        _ => unreachable!("build.rs validated the embedded API status"),
    }
}

fn public_rust_api_signature_scope() -> PublicRustApiSignatureScope {
    match generated::PUBLIC_RUST_API_SCOPE {
        "proposed_release_scope_profiles" => {
            PublicRustApiSignatureScope::ProposedReleaseScopeProfiles
        }
        _ => unreachable!("build.rs validated the embedded public Rust API signature scope"),
    }
}

fn attestation_status() -> AttestationStatus {
    match generated::ATTESTATION {
        "none" => AttestationStatus::None,
        _ => unreachable!("build.rs validated the embedded attestation status"),
    }
}

fn source_identity() -> SourceIdentity {
    match generated::SOURCE_KIND {
        "workspace_git" => SourceIdentity::WorkspaceGit {
            commit_sha1: generated::SOURCE_COMMIT_SHA1,
            working_tree_scope: WorkingTreeScope::PidCorePackagePath,
            working_tree: working_tree_state(),
        },
        "cargo_package" => SourceIdentity::CargoPackage {
            commit_sha1: generated::SOURCE_COMMIT_SHA1,
            working_tree_scope: WorkingTreeScope::CargoVcsInfoDirtyFlag,
            working_tree: working_tree_state(),
        },
        "unavailable" => SourceIdentity::Unavailable {
            reason: source_unavailable_reason(),
        },
        _ => unreachable!("build.rs generated an unsupported source kind"),
    }
}

fn working_tree_state() -> WorkingTreeState {
    match generated::WORKING_TREE {
        "clean" => WorkingTreeState::Clean,
        "dirty" => WorkingTreeState::Dirty,
        "unknown" => WorkingTreeState::Unknown,
        _ => unreachable!("build.rs generated an unsupported working-tree state"),
    }
}

fn source_unavailable_reason() -> SourceUnavailableReason {
    match generated::SOURCE_UNAVAILABLE_REASON {
        "invalid_cargo_vcs_info" => SourceUnavailableReason::InvalidCargoVcsInfo,
        "unrecognized_workspace_layout" => SourceUnavailableReason::UnrecognizedWorkspaceLayout,
        "git_unavailable" => SourceUnavailableReason::GitUnavailable,
        "invalid_git_commit" => SourceUnavailableReason::InvalidGitCommit,
        _ => unreachable!("build.rs generated an unsupported unavailable-source reason"),
    }
}

fn reference_artifact(value: EmbeddedReferenceArtifact) -> ReferenceArtifactIdentity {
    let kind = match value.kind {
        "method_catalog" => ReferenceArtifactKind::MethodCatalog,
        "proposed_release_scope" => ReferenceArtifactKind::ProposedReleaseScope,
        _ => unreachable!("build.rs validated reference artifact kinds"),
    };
    let role = match value.role {
        "forensic_reference_only" => ReferenceArtifactRole::ForensicReferenceOnly,
        _ => unreachable!("build.rs validated reference artifact roles"),
    };
    ReferenceArtifactIdentity {
        kind,
        repository_path: value.repository_path,
        schema: value.schema,
        schema_revision: value.schema_revision,
        digest_scope: value.digest_scope,
        canonical_json_sha256: value.canonical_json_sha256,
        role,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};

    fn assert_machine_spelling<T: Serialize + Copy>(value: T, expected: &str) {
        assert_eq!(serde_json::to_value(value).unwrap(), json!(expected));
    }

    fn assert_source_kind(source: SourceIdentity, expected: &str) {
        let serialized = serde_json::to_value(source).unwrap();
        assert_eq!(
            serialized.get("kind"),
            Some(&Value::String(expected.into()))
        );
    }

    #[test]
    fn identity_has_pre_one_epoch_and_no_attestation() {
        let identity = software_identity();
        assert_eq!(identity.identity_format(), 1);
        assert_eq!(identity.public_rust_api_signature_identity().epoch(), 0);
        assert_eq!(identity.public_rust_api_signature_identity().revision(), 2);
        assert_eq!(
            identity.public_rust_api_signature_identity().scope(),
            PublicRustApiSignatureScope::ProposedReleaseScopeProfiles
        );
        assert_eq!(
            identity.public_rust_api_signature_identity().status(),
            PublicRustApiSignatureStatus::PreOneReview
        );
        assert_eq!(identity.attestation(), AttestationStatus::None);
    }

    #[test]
    fn feature_names_are_sorted_and_unique() {
        let features = software_identity().build().enabled_features();
        assert!(features.windows(2).all(|pair| pair[0] < pair[1]));
    }

    #[test]
    fn every_format_one_enum_spelling_matches_its_accessor() {
        let statuses = [PublicRustApiSignatureStatus::PreOneReview];
        for value in statuses {
            assert_machine_spelling(value, value.as_str());
        }

        let scopes = [PublicRustApiSignatureScope::ProposedReleaseScopeProfiles];
        for value in scopes {
            assert_machine_spelling(value, value.as_str());
        }

        let attestations = [AttestationStatus::None];
        for value in attestations {
            assert_machine_spelling(value, value.as_str());
        }

        let working_tree_states = [
            WorkingTreeState::Clean,
            WorkingTreeState::Dirty,
            WorkingTreeState::Unknown,
        ];
        for value in working_tree_states {
            assert_machine_spelling(value, value.as_str());
        }

        let working_tree_scopes = [
            WorkingTreeScope::PidCorePackagePath,
            WorkingTreeScope::CargoVcsInfoDirtyFlag,
        ];
        for value in working_tree_scopes {
            assert_machine_spelling(value, value.as_str());
        }

        let unavailable_reasons = [
            SourceUnavailableReason::InvalidCargoVcsInfo,
            SourceUnavailableReason::UnrecognizedWorkspaceLayout,
            SourceUnavailableReason::GitUnavailable,
            SourceUnavailableReason::InvalidGitCommit,
        ];
        for value in unavailable_reasons {
            assert_machine_spelling(value, value.as_str());
        }

        let artifact_kinds = [
            ReferenceArtifactKind::MethodCatalog,
            ReferenceArtifactKind::ProposedReleaseScope,
        ];
        for value in artifact_kinds {
            assert_machine_spelling(value, value.as_str());
        }

        let artifact_roles = [ReferenceArtifactRole::ForensicReferenceOnly];
        for value in artifact_roles {
            assert_machine_spelling(value, value.as_str());
        }
    }

    #[test]
    fn every_source_envelope_tag_has_its_format_one_spelling() {
        assert_source_kind(
            SourceIdentity::WorkspaceGit {
                commit_sha1: "0123456789abcdef0123456789abcdef01234567",
                working_tree_scope: WorkingTreeScope::PidCorePackagePath,
                working_tree: WorkingTreeState::Clean,
            },
            "workspace_git",
        );
        assert_source_kind(
            SourceIdentity::CargoPackage {
                commit_sha1: "0123456789abcdef0123456789abcdef01234567",
                working_tree_scope: WorkingTreeScope::CargoVcsInfoDirtyFlag,
                working_tree: WorkingTreeState::Unknown,
            },
            "cargo_package",
        );
        assert_source_kind(
            SourceIdentity::Unavailable {
                reason: SourceUnavailableReason::UnrecognizedWorkspaceLayout,
            },
            "unavailable",
        );
    }
}
