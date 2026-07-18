use pid_core::{
    software_identity, AttestationStatus, PublicRustApiSignatureScope,
    PublicRustApiSignatureStatus, ReferenceArtifactKind, ReferenceArtifactRole, SourceIdentity,
    WorkingTreeScope, WorkingTreeState,
};
use std::collections::BTreeSet;
use std::path::Path;
use std::process::Command;

fn is_lower_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn object_keys(value: &serde_json::Value) -> BTreeSet<&str> {
    value
        .as_object()
        .expect("identity component must be an object")
        .keys()
        .map(String::as_str)
        .collect()
}

#[test]
fn software_identity_separates_api_signatures_source_build_and_attestation() {
    let identity = software_identity();
    assert_eq!(identity.identity_format(), 1);
    assert_eq!(identity.package_name(), "pid-core");
    assert_eq!(identity.package_version(), env!("CARGO_PKG_VERSION"));
    assert_eq!(identity.public_rust_api_signature_identity().epoch(), 0);
    assert_eq!(identity.public_rust_api_signature_identity().revision(), 1);
    assert_eq!(
        identity.public_rust_api_signature_identity().scope(),
        PublicRustApiSignatureScope::ProposedReleaseScopeProfiles
    );
    assert_eq!(
        identity.public_rust_api_signature_identity().status(),
        PublicRustApiSignatureStatus::PreOneReview
    );
    assert_eq!(identity.attestation(), AttestationStatus::None);

    let build = identity.build();
    assert!(build
        .rustc_version()
        .is_some_and(|version| !version.is_empty()));
    assert!(!build.target_triple().is_empty());
    assert!(!build.profile().is_empty());
    assert!(!build.opt_level().is_empty());
    assert!(build
        .enabled_features()
        .windows(2)
        .all(|pair| pair[0] < pair[1]));

    match identity.source() {
        SourceIdentity::WorkspaceGit {
            commit_sha1,
            working_tree_scope,
            working_tree,
            ..
        } => {
            assert!(is_lower_hex(commit_sha1, 40));
            assert_eq!(*working_tree_scope, WorkingTreeScope::PidCorePackagePath);
            assert!(matches!(
                working_tree,
                WorkingTreeState::Clean | WorkingTreeState::Dirty | WorkingTreeState::Unknown
            ));
        }
        SourceIdentity::CargoPackage {
            commit_sha1,
            working_tree_scope,
            working_tree,
            ..
        } => {
            assert!(is_lower_hex(commit_sha1, 40));
            assert_eq!(*working_tree_scope, WorkingTreeScope::CargoVcsInfoDirtyFlag);
            assert!(matches!(
                working_tree,
                WorkingTreeState::Clean | WorkingTreeState::Dirty | WorkingTreeState::Unknown
            ));
        }
        SourceIdentity::Unavailable { reason, .. } => assert!(!reason.as_str().is_empty()),
        unexpected => panic!("unexpected future source identity variant: {unexpected:?}"),
    }
}

#[test]
fn enabled_features_match_compile_time_configuration_exactly() {
    let identity = software_identity();
    let mut expected = [
        ("default", cfg!(feature = "default")),
        ("experimental-all", cfg!(feature = "experimental-all")),
        (
            "experimental-continuous",
            cfg!(feature = "experimental-continuous"),
        ),
        (
            "experimental-heuristics",
            cfg!(feature = "experimental-heuristics"),
        ),
        (
            "experimental-hierarchy",
            cfg!(feature = "experimental-hierarchy"),
        ),
        (
            "experimental-hyperbolic",
            cfg!(feature = "experimental-hyperbolic"),
        ),
        (
            "experimental-pipelines",
            cfg!(feature = "experimental-pipelines"),
        ),
        ("parallel", cfg!(feature = "parallel")),
        (
            "research-mixed-dimension-pid3",
            cfg!(feature = "research-mixed-dimension-pid3"),
        ),
    ]
    .into_iter()
    .filter_map(|(name, enabled)| enabled.then_some(name))
    .collect::<Vec<_>>();
    expected.sort_unstable();

    assert_eq!(identity.build().enabled_features(), expected);
}

#[test]
fn forensic_artifacts_are_typed_and_never_attest_validity() {
    let identity = software_identity();
    let artifacts = identity.reference_artifacts();
    assert_eq!(artifacts.len(), 2);
    assert_eq!(artifacts[0].kind(), ReferenceArtifactKind::MethodCatalog);
    assert_eq!(
        artifacts[1].kind(),
        ReferenceArtifactKind::ProposedReleaseScope
    );
    for artifact in artifacts {
        assert!(!artifact.repository_path().starts_with('/'));
        assert!(!artifact.repository_path().contains(".."));
        assert!(!artifact.schema().is_empty());
        assert_eq!(artifact.schema_revision(), 1);
        assert_eq!(artifact.digest_scope(), "sha256_of_canonical_file_bytes");
        assert!(is_lower_hex(artifact.canonical_json_sha256(), 64));
        assert_eq!(
            artifact.role(),
            ReferenceArtifactRole::ForensicReferenceOnly
        );
    }
}

#[test]
fn serialized_identity_has_stable_machine_spellings_and_no_host_path_or_timestamp() {
    let identity = software_identity();
    let value = serde_json::to_value(&identity).expect("software identity must serialize");
    assert_eq!(value["identity_format"], 1);
    assert_eq!(value["public_rust_api_signature_identity"]["epoch"], 0);
    assert_eq!(value["public_rust_api_signature_identity"]["revision"], 1);
    assert_eq!(
        value["public_rust_api_signature_identity"]["scope"],
        "proposed_release_scope_profiles"
    );
    assert_eq!(
        value["public_rust_api_signature_identity"]["status"],
        "pre_1_0_review"
    );
    assert_eq!(value["attestation"], "none");

    assert_eq!(
        object_keys(&value),
        BTreeSet::from([
            "attestation",
            "build",
            "identity_format",
            "package_name",
            "package_version",
            "reference_artifacts",
            "public_rust_api_signature_identity",
            "source",
        ])
    );
    assert_eq!(
        object_keys(&value["public_rust_api_signature_identity"]),
        BTreeSet::from(["epoch", "revision", "scope", "status"])
    );
    assert_eq!(
        object_keys(&value["build"]),
        BTreeSet::from([
            "debug_information",
            "enabled_features",
            "opt_level",
            "profile",
            "rustc_version",
            "target_triple",
        ])
    );
    let source_keys = object_keys(&value["source"]);
    if value["source"]["kind"] == "unavailable" {
        assert_eq!(source_keys, BTreeSet::from(["kind", "reason"]));
    } else {
        assert_eq!(
            source_keys,
            BTreeSet::from(["commit_sha1", "kind", "working_tree", "working_tree_scope"])
        );
    }
    for artifact in value["reference_artifacts"]
        .as_array()
        .expect("reference artifacts must be an array")
    {
        assert_eq!(
            object_keys(artifact),
            BTreeSet::from([
                "canonical_json_sha256",
                "digest_scope",
                "kind",
                "repository_path",
                "role",
                "schema",
                "schema_revision",
            ])
        );
    }

    let encoded = serde_json::to_string(&value).expect("software identity must serialize");
    assert!(!encoded.contains(env!("CARGO_MANIFEST_DIR")));
    assert!(!encoded.contains("timestamp"));
    assert!(!encoded.contains("built_at"));
    assert!(!encoded.contains("validity"));
}

#[test]
fn compiled_source_identity_matches_the_declared_build_context() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let identity = software_identity();
    match identity.source() {
        SourceIdentity::WorkspaceGit { commit_sha1, .. } => {
            let root = manifest_dir
                .parent()
                .and_then(Path::parent)
                .expect("workspace crate path must have a repository parent");
            let expected = Command::new("git")
                .arg("-C")
                .arg(root)
                .args(["rev-parse", "--verify", "HEAD^{commit}"])
                .output()
                .expect("git must be runnable")
                .stdout;
            let expected = String::from_utf8(expected)
                .expect("Git commit must be UTF-8")
                .trim()
                .to_owned();
            assert_eq!(*commit_sha1, expected);
        }
        SourceIdentity::CargoPackage {
            commit_sha1,
            working_tree_scope,
            working_tree,
            ..
        } => {
            let raw = std::fs::read_to_string(manifest_dir.join(".cargo_vcs_info.json"))
                .expect("Cargo package metadata must be readable");
            let value: serde_json::Value =
                serde_json::from_str(&raw).expect("Cargo package metadata must be JSON");
            let expected_commit = value["git"]["sha1"]
                .as_str()
                .expect("Cargo package metadata must contain git.sha1");
            let expected_tree = if value["git"]["dirty"].as_bool().unwrap_or(false) {
                WorkingTreeState::Dirty
            } else {
                WorkingTreeState::Clean
            };
            assert_eq!(*commit_sha1, expected_commit);
            assert_eq!(*working_tree_scope, WorkingTreeScope::CargoVcsInfoDirtyFlag);
            assert_eq!(*working_tree, expected_tree);
        }
        unexpected => panic!("expected a commit-bearing source identity, got {unexpected:?}"),
    }
}
