//! Build script for typed software identity.
//!
//! The generated constants distinguish layout-matched workspace Git state, Cargo package metadata, and
//! unavailable source identity. They also capture the compiler, target, profile, optimization
//! level, debug-information setting, and exact enabled Cargo features. These fields are
//! diagnostic build context, not binary attestation.

mod build_support;

use std::collections::BTreeMap;
use std::fmt::Write as _;
use std::path::{Path, PathBuf};
use std::process::Command;

use build_support::{SourceProbe, WorkingTreeProbe};
use serde::Deserialize;
use sha2::{Digest, Sha256};

const IDENTITY_MANIFEST: &str = "identity/software-identity-reference-v1.json";

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct IdentityManifest {
    api_signature_identity: ApiSignatureIdentityManifest,
    artifact_digest_scope: String,
    attestation: String,
    identity_format: u32,
    package: String,
    recognized_cargo_features: Vec<String>,
    reference_artifact_use: String,
    reference_artifacts: Vec<ReferenceArtifact>,
    schema: String,
    schema_revision: u32,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ApiSignatureIdentityManifest {
    epoch: u32,
    revision: u32,
    scope: String,
    status: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReferenceArtifact {
    canonical_json_sha256: String,
    digest_scope: String,
    kind: String,
    repository_path: String,
    role: String,
    schema: String,
    schema_revision: u32,
}

struct CompilationContext<'a> {
    rustc_version: Option<&'a str>,
    target: &'a str,
    profile: &'a str,
    opt_level: &'a str,
    debug_information: bool,
}

fn main() {
    let manifest_dir = PathBuf::from(
        std::env::var_os("CARGO_MANIFEST_DIR")
            .expect("Cargo must provide CARGO_MANIFEST_DIR to build scripts"),
    );
    let identity = load_identity_manifest(&manifest_dir.join(IDENTITY_MANIFEST));
    validate_active_cargo_features(&identity);
    let layout_root = build_support::layout_matched_workspace_root(&manifest_dir);
    if let Some(root) = &layout_root {
        verify_workspace_reference_artifacts(&identity, root);
    }
    let source = build_support::probe_source_identity(&manifest_dir);
    emit_rerun_directives(&manifest_dir, &source);
    let rustc_version = rustc_version();
    let target = required_env("TARGET");
    let profile = required_env("PROFILE");
    let opt_level = required_env("OPT_LEVEL");
    let debug_information = match required_env("DEBUG").as_str() {
        "true" => true,
        "false" => false,
        other => panic!("Cargo supplied invalid DEBUG value {other:?}"),
    };
    let compilation = CompilationContext {
        rustc_version: rustc_version.as_deref(),
        target: &target,
        profile: &profile,
        opt_level: &opt_level,
        debug_information,
    };
    let rendered = render_generated_identity(&identity, &source, &compilation);
    let out_dir = PathBuf::from(
        std::env::var_os("OUT_DIR").expect("Cargo must provide OUT_DIR to build scripts"),
    );
    build_support::write_if_changed(
        &out_dir.join("software_identity_build.rs"),
        rendered.as_bytes(),
    )
    .expect("cannot write generated software identity constants");

    // Cargo timestamps the captured build-script output after this process exits. A repository
    // change during the probe can therefore be older than that output and escape the next
    // fingerprint comparison even though its paths were watched. Fail this build instead of
    // emitting a source/reference mixture; a subsequent stable invocation will recompute it.
    let final_source = build_support::probe_source_identity(&manifest_dir);
    assert_eq!(
        final_source, source,
        "pid-core source identity changed while its build script was running"
    );
    let final_layout_root = build_support::layout_matched_workspace_root(&manifest_dir);
    assert_eq!(
        final_layout_root, layout_root,
        "pid-core workspace layout changed while its build script was running"
    );
    if let Some(root) = &final_layout_root {
        verify_workspace_reference_artifacts(&identity, root);
    }
}

fn emit_rerun_directives(manifest_dir: &Path, source: &SourceProbe) {
    for variable in [
        "RUSTC",
        "PATH",
        "HOME",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
    ] {
        println!("cargo:rerun-if-env-changed={variable}");
    }
    println!("cargo:rerun-if-changed={IDENTITY_MANIFEST}");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=build_support.rs");
    let layout_root = build_support::layout_matched_workspace_root(manifest_dir);
    if layout_root.is_none() {
        // Cargo reruns a build script whenever a named path is missing. That conservative behavior
        // lets an extracted/source-archive layout recover if package metadata appears later.
        println!("cargo:rerun-if-changed=.cargo_vcs_info.json");
    }

    if matches!(source, SourceProbe::WorkspaceGit { .. }) {
        // In the canonical workspace, target/ is at the repository root and outside this package
        // directory. Do not use this recursive watch for standalone/extracted package layouts,
        // where an in-package target/ would otherwise retrigger every build.
        println!("cargo:rerun-if-changed=.");
    }
    // Emit the recovery plan even when markers are missing or Git is currently unavailable or
    // misrouted. Healthy routes watch only exact metadata inputs; fail-closed routes add a
    // deliberately absent sentinel so a later Cargo invocation cannot reuse the stale identity.
    let mut needs_unrepresentable_path_recovery = false;
    for path in build_support::workspace_rerun_paths_for_source(manifest_dir, source) {
        if let Some(path) = build_support::cargo_rerun_path(&path) {
            println!("cargo:rerun-if-changed={path}");
        } else {
            needs_unrepresentable_path_recovery = true;
        }
    }
    if needs_unrepresentable_path_recovery {
        let sentinel = build_support::absent_rerun_sentinel_name(
            manifest_dir,
            ".pid-rs-source-identity-unrepresentable-watch",
        );
        println!("cargo:rerun-if-changed={sentinel}");
    }
}

fn load_identity_manifest(path: &Path) -> IdentityManifest {
    let raw = std::fs::read_to_string(path)
        .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
    let identity: IdentityManifest = serde_json::from_str(&raw)
        .unwrap_or_else(|error| panic!("cannot parse {}: {error}", path.display()));

    assert_eq!(
        identity.schema, "pid-rs/software-identity-reference",
        "unsupported software-identity schema"
    );
    assert_eq!(
        identity.schema_revision, 1,
        "unsupported software-identity schema revision"
    );
    assert_eq!(
        identity.identity_format, 1,
        "unsupported software-identity format"
    );
    assert_eq!(
        identity.package, "pid-core",
        "software identity must describe pid-core"
    );
    assert_eq!(
        identity.api_signature_identity.epoch, 0,
        "pre-1.0 identity must remain in API epoch zero"
    );
    assert_eq!(
        identity.api_signature_identity.revision, 4,
        "unsupported public Rust API signature revision"
    );
    assert_eq!(
        identity.api_signature_identity.scope, "proposed_release_scope_profiles",
        "unsupported public Rust API signature scope"
    );
    assert_eq!(
        identity.api_signature_identity.status, "pre_1_0_review",
        "unsupported public Rust API signature status"
    );
    assert_eq!(
        identity.artifact_digest_scope, "sha256_of_canonical_file_bytes",
        "unsupported artifact digest scope"
    );
    assert_eq!(
        identity.reference_artifact_use, "forensic_reference_only",
        "reference artifacts must remain forensic-only"
    );
    assert_eq!(
        identity.attestation, "none",
        "software identity must not claim binary attestation"
    );

    let mut previous = None;
    let mut env_names = BTreeMap::new();
    for feature in &identity.recognized_cargo_features {
        assert!(
            is_cargo_feature_name(feature),
            "recognized Cargo features must use lowercase ASCII Cargo-name syntax"
        );
        if let Some(previous) = previous {
            assert!(
                previous < feature,
                "recognized Cargo features must be sorted and unique"
            );
        }
        previous = Some(feature);
        let env_name = format!(
            "CARGO_FEATURE_{}",
            feature.to_ascii_uppercase().replace('-', "_")
        );
        assert!(
            env_names.insert(env_name, feature).is_none(),
            "recognized Cargo feature names collide after Cargo environment normalization"
        );
    }

    let expected_artifacts = [
        (
            "method_catalog",
            "method-catalog.json",
            "pid-rs/method-catalog",
        ),
        (
            "proposed_release_scope",
            "release-scope-1.0.json",
            "pid-rs/release-scope",
        ),
    ];
    assert_eq!(
        identity.reference_artifacts.len(),
        expected_artifacts.len(),
        "identity manifest must contain exactly two reference artifacts"
    );
    for (artifact, (kind, repository_path, schema)) in
        identity.reference_artifacts.iter().zip(expected_artifacts)
    {
        validate_reference_artifact(artifact);
        assert_eq!(artifact.kind, kind, "unexpected reference artifact kind");
        assert_eq!(
            artifact.repository_path, repository_path,
            "unexpected reference artifact path"
        );
        assert_eq!(
            artifact.schema, schema,
            "unexpected reference artifact schema"
        );
        assert_eq!(
            artifact.schema_revision, 1,
            "unexpected reference artifact schema revision"
        );
    }
    identity
}

fn validate_reference_artifact(artifact: &ReferenceArtifact) {
    assert!(
        is_lower_hex(&artifact.canonical_json_sha256, 64),
        "reference artifact SHA-256 must be 64 lowercase hexadecimal characters"
    );
    assert_eq!(
        artifact.digest_scope, "sha256_of_canonical_file_bytes",
        "unsupported identity digest scope"
    );
    assert_eq!(
        artifact.role, "forensic_reference_only",
        "reference artifact role must remain forensic-only"
    );
}

fn validate_active_cargo_features(identity: &IdentityManifest) {
    // Cargo's aggregate cfg list is authoritative for this compilation. Feature-shaped variables
    // inherited from the process environment are ambient input, not evidence that Cargo activated
    // those features. The repository checker independently binds the recognized inventory to
    // Cargo.toml. Do not treat a missing aggregate as an empty set: that could under-report a build
    // on a future or nonconforming Cargo implementation.
    let active = std::env::var("CARGO_CFG_FEATURE")
        .expect("Cargo must provide CARGO_CFG_FEATURE to the pid-core build script");
    for feature in active.split(',').filter(|feature| !feature.is_empty()) {
        assert!(
            identity
                .recognized_cargo_features
                .binary_search_by(|known| known.as_str().cmp(feature))
                .is_ok(),
            "Cargo activated feature {feature:?} outside the recognized identity inventory"
        );
    }
}

fn verify_workspace_reference_artifacts(identity: &IdentityManifest, root: &Path) {
    for artifact in &identity.reference_artifacts {
        let path = root.join(&artifact.repository_path);
        let bytes = std::fs::read(&path)
            .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
        let actual = lower_hex(&Sha256::digest(bytes));
        assert_eq!(
            actual, artifact.canonical_json_sha256,
            "{} does not match the embedded forensic digest; run the software-identity checker",
            artifact.repository_path
        );
    }
}

fn render_generated_identity(
    identity: &IdentityManifest,
    source: &SourceProbe,
    compilation: &CompilationContext<'_>,
) -> String {
    let mut output = String::new();
    writeln!(
        output,
        "pub(crate) const IDENTITY_FORMAT: u32 = {};",
        identity.identity_format
    )
    .expect("writing to String cannot fail");
    writeln!(
        output,
        "pub(crate) const PUBLIC_RUST_API_EPOCH: u32 = {};",
        identity.api_signature_identity.epoch
    )
    .expect("writing to String cannot fail");
    writeln!(
        output,
        "pub(crate) const PUBLIC_RUST_API_REVISION: u32 = {};",
        identity.api_signature_identity.revision
    )
    .expect("writing to String cannot fail");
    emit_string(
        &mut output,
        "PUBLIC_RUST_API_SCOPE",
        &identity.api_signature_identity.scope,
    );
    emit_string(
        &mut output,
        "PUBLIC_RUST_API_STATUS",
        &identity.api_signature_identity.status,
    );
    emit_string(&mut output, "ATTESTATION", &identity.attestation);

    let (source_kind, commit_sha1, working_tree, unavailable_reason) = match source {
        SourceProbe::WorkspaceGit {
            commit_sha1,
            working_tree,
        } => ("workspace_git", commit_sha1.as_str(), *working_tree, ""),
        SourceProbe::CargoPackage {
            commit_sha1,
            working_tree,
        } => ("cargo_package", commit_sha1.as_str(), *working_tree, ""),
        SourceProbe::Unavailable { reason } => {
            ("unavailable", "", WorkingTreeProbe::Unknown, *reason)
        }
    };
    emit_string(&mut output, "SOURCE_KIND", source_kind);
    emit_string(&mut output, "SOURCE_COMMIT_SHA1", commit_sha1);
    emit_string(&mut output, "WORKING_TREE", working_tree.as_str());
    emit_string(&mut output, "SOURCE_UNAVAILABLE_REASON", unavailable_reason);
    emit_optional_string(&mut output, "RUSTC_VERSION", compilation.rustc_version);
    emit_string(&mut output, "TARGET_TRIPLE", compilation.target);
    emit_string(&mut output, "PROFILE", compilation.profile);
    emit_string(&mut output, "OPT_LEVEL", compilation.opt_level);
    writeln!(
        output,
        "pub(crate) const DEBUG_INFORMATION: bool = {};",
        compilation.debug_information
    )
    .expect("writing to String cannot fail");

    output.push_str("pub(crate) const ENABLED_FEATURES: &[&str] = &[\n");
    for feature in &identity.recognized_cargo_features {
        writeln!(output, "    #[cfg(feature = {feature:?})]")
            .expect("writing to String cannot fail");
        writeln!(output, "    {feature:?},").expect("writing to String cannot fail");
    }
    output.push_str("];\n");

    output.push_str(
        "pub(crate) const REFERENCE_ARTIFACTS: &[super::EmbeddedReferenceArtifact] = &[\n",
    );
    for artifact in &identity.reference_artifacts {
        output.push_str("    super::EmbeddedReferenceArtifact {\n");
        writeln!(
            output,
            "        canonical_json_sha256: {:?},",
            artifact.canonical_json_sha256
        )
        .expect("writing to String cannot fail");
        writeln!(output, "        digest_scope: {:?},", artifact.digest_scope)
            .expect("writing to String cannot fail");
        writeln!(output, "        kind: {:?},", artifact.kind)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "        repository_path: {:?},",
            artifact.repository_path
        )
        .expect("writing to String cannot fail");
        writeln!(output, "        role: {:?},", artifact.role)
            .expect("writing to String cannot fail");
        writeln!(output, "        schema: {:?},", artifact.schema)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "        schema_revision: {},",
            artifact.schema_revision
        )
        .expect("writing to String cannot fail");
        output.push_str("    },\n");
    }
    output.push_str("];\n");
    output
}

fn emit_string(output: &mut String, name: &str, value: &str) {
    assert!(
        !value.contains('\r') && !value.contains('\n'),
        "generated identity strings cannot contain line breaks"
    );
    writeln!(output, "pub(crate) const {name}: &str = {value:?};")
        .expect("writing to String cannot fail");
}

fn emit_optional_string(output: &mut String, name: &str, value: Option<&str>) {
    if let Some(value) = value {
        assert!(
            !value.contains('\r') && !value.contains('\n'),
            "generated identity strings cannot contain line breaks"
        );
    }
    writeln!(output, "pub(crate) const {name}: Option<&str> = {value:?};")
        .expect("writing to String cannot fail");
}

fn rustc_version() -> Option<String> {
    let rustc = std::env::var_os("RUSTC").unwrap_or_else(|| "rustc".into());
    Command::new(rustc)
        .arg("--version")
        .output()
        .ok()
        .filter(|output| output.status.success())
        .and_then(|output| String::from_utf8(output.stdout).ok())
        .map(|output| output.trim().to_owned())
        .filter(|output| !output.is_empty())
}

fn required_env(name: &str) -> String {
    std::env::var(name).unwrap_or_else(|_| panic!("Cargo must provide {name} to build scripts"))
}

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn is_cargo_feature_name(value: &str) -> bool {
    !value.is_empty()
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
        && !value.starts_with('-')
        && !value.ends_with('-')
        && !value.contains("--")
}

fn lower_hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        write!(output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}
