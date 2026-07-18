#[path = "../build_support.rs"]
mod build_support;

use std::ffi::OsStr;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use build_support::{SourceProbe, WorkingTreeProbe, WorkspaceRootProbe};

static NEXT_TEMP_ID: AtomicU64 = AtomicU64::new(0);
const SHA1: &str = "0123456789abcdef0123456789abcdef01234567";

struct TempDir(PathBuf);

impl TempDir {
    fn new(label: &str) -> Self {
        let unique = NEXT_TEMP_ID.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "pid-rs-software-identity-{label}-{}-{unique}",
            std::process::id()
        ));
        std::fs::create_dir_all(&path).expect("temporary directory must be creatable");
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn package_dir(temp: &TempDir) -> PathBuf {
    let path = temp.path().join("vendor/pid-core");
    std::fs::create_dir_all(&path).expect("package directory must be creatable");
    path
}

fn write_vcs_info(package: &Path, body: &str) {
    std::fs::write(package.join(".cargo_vcs_info.json"), body)
        .expect("package metadata must be writable");
}

fn isolated_git_at(root: &Path) -> Command {
    // Fixture behavior must not depend on a developer's signing, hook, ignore, fsmonitor, or
    // alternate-object configuration. Keep this isolation aligned with the production probe.
    let mut command = Command::new("git");
    for name in [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CEILING_DIRECTORIES",
        "GIT_TEMPLATE_DIR",
    ] {
        command.env_remove(name);
    }
    for index in 0..256 {
        command.env_remove(format!("GIT_CONFIG_KEY_{index}"));
        command.env_remove(format!("GIT_CONFIG_VALUE_{index}"));
    }
    let null_device = if cfg!(windows) { "NUL" } else { "/dev/null" };
    command
        .env("GIT_CONFIG_GLOBAL", null_device)
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_OPTIONAL_LOCKS", "0")
        .arg("-c")
        .arg("core.fsmonitor=false")
        .arg("-c")
        .arg("core.untrackedCache=false")
        .arg("-C")
        .arg(root);
    command
}

fn create_workspace(temp: &TempDir) -> (PathBuf, PathBuf) {
    let root = temp.path().join("repository");
    let package = root.join("crates/pid-core");
    std::fs::create_dir_all(&package).expect("workspace member must be creatable");
    for marker in [
        "Cargo.toml",
        "method-catalog.json",
        "release-scope-1.0.json",
    ] {
        std::fs::write(root.join(marker), "{}\n").expect("workspace marker must be writable");
    }
    let status = isolated_git_at(&root)
        .args(["init", "-q"])
        .status()
        .expect("git must be runnable for the workspace test");
    assert!(status.success());
    (root, package)
}

fn commit_workspace(root: &Path) -> String {
    std::fs::write(root.join("crates/pid-core/tracked.txt"), "tracked\n")
        .expect("tracked fixture must be writable");
    let add = isolated_git_at(root)
        .args(["add", "--force", "."])
        .status()
        .expect("git add must run");
    assert!(add.success());
    let commit = isolated_git_at(root)
        .args([
            "-c",
            "user.name=pid-rs tests",
            "-c",
            "user.email=tests@example.invalid",
            "commit",
            "-q",
            "--no-gpg-sign",
            "--no-verify",
            "-m",
            "fixture",
        ])
        .status()
        .expect("git commit must run");
    assert!(commit.success());
    let output = isolated_git_at(root)
        .args(["rev-parse", "HEAD"])
        .output()
        .expect("git rev-parse must run");
    assert!(output.status.success());
    String::from_utf8(output.stdout)
        .expect("fixture commit must be UTF-8")
        .trim()
        .to_owned()
}

#[test]
fn cargo_package_metadata_is_first_class_and_dirty_defaults_false() {
    assert_eq!(WorkingTreeProbe::Clean.as_str(), "clean");
    let temp = TempDir::new("clean-package");
    let package = package_dir(&temp);
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}"}},"path_in_vcs":"crates/pid-core"}}"#),
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::CargoPackage {
            commit_sha1: SHA1.to_owned(),
            working_tree: WorkingTreeProbe::Clean,
        }
    );

    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}","dirty":true}},"path_in_vcs":"crates/pid-core"}}"#),
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::CargoPackage {
            commit_sha1: SHA1.to_owned(),
            working_tree: WorkingTreeProbe::Dirty,
        }
    );
}

#[test]
fn malformed_package_metadata_never_falls_through_to_ambient_git() {
    let temp = TempDir::new("invalid-package");
    let package = package_dir(&temp);
    let status = isolated_git_at(temp.path())
        .args(["init", "-q"])
        .status()
        .expect("git must be runnable for the trust-boundary test");
    assert!(status.success());

    let invalid_cases = vec![
        "{".to_owned(),
        r#"{"git":{"sha1":"0123"},"path_in_vcs":"crates/pid-core"}"#.to_owned(),
        r#"{"git":{"sha1":"0123456789ABCDEF0123456789ABCDEF01234567"},"path_in_vcs":"crates/pid-core"}"#.to_owned(),
        format!(
            r#"{{"git":{{"sha1":"{SHA1}","dirty":"no"}},"path_in_vcs":"crates/pid-core"}}"#
        ),
        format!(
            r#"{{"git":{{"sha1":"{SHA1}","dirty":null}},"path_in_vcs":"crates/pid-core"}}"#
        ),
        format!(r#"{{"git":{{"sha1":"{SHA1}"}},"path_in_vcs":"other/pid-core"}}"#),
        format!(
            r#"{{"git":{{"sha1":"{SHA1}","sha1":"{SHA1}"}},"path_in_vcs":"crates/pid-core"}}"#
        ),
        format!(
            r#"{{"git":{{"sha1":"{SHA1}","dirty":false,"dirty":true}},"path_in_vcs":"crates/pid-core"}}"#
        ),
    ];
    for invalid in invalid_cases {
        write_vcs_info(&package, &invalid);
        assert_eq!(
            build_support::probe_source_identity(&package),
            SourceProbe::Unavailable {
                reason: "invalid_cargo_vcs_info",
            }
        );
    }
}

#[test]
fn cargo_metadata_ignores_future_fields_but_preserves_known_semantics() {
    let temp = TempDir::new("future-package-fields");
    let package = package_dir(&temp);
    write_vcs_info(
        &package,
        &format!(
            r#"{{"git":{{"sha1":"{SHA1}","unexpected":true}},"path_in_vcs":"crates/pid-core","unexpected":true}}"#
        ),
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::CargoPackage {
            commit_sha1: SHA1.to_owned(),
            working_tree: WorkingTreeProbe::Clean,
        }
    );
}

#[cfg(unix)]
#[test]
fn symlinked_package_metadata_is_rejected_without_git_fallback() {
    use std::os::unix::fs::symlink;

    let temp = TempDir::new("symlinked-package-metadata");
    let package = package_dir(&temp);
    let outside = temp.path().join("outside-vcs-info.json");
    std::fs::write(
        &outside,
        format!(r#"{{"git":{{"sha1":"{SHA1}"}},"path_in_vcs":"crates/pid-core"}}"#),
    )
    .expect("external package metadata must be writable");
    symlink(outside, package.join(".cargo_vcs_info.json"))
        .expect("package metadata symlink must be creatable");

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "invalid_cargo_vcs_info",
        }
    );
}

#[test]
fn unrelated_git_repository_without_package_metadata_is_not_recognized() {
    let temp = TempDir::new("foreign-git");
    let package = package_dir(&temp);
    let status = isolated_git_at(temp.path())
        .args(["init", "-q"])
        .status()
        .expect("git must be runnable for the trust-boundary test");
    assert!(status.success());
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "unrecognized_workspace_layout",
        }
    );
}

#[test]
fn layout_matched_workspace_git_precedes_untracked_package_metadata() {
    let temp = TempDir::new("workspace-precedence");
    let (root, package) = create_workspace(&temp);
    let expected_commit = commit_workspace(&root);
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}"}},"path_in_vcs":"crates/pid-core"}}"#),
    );

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: expected_commit,
            working_tree: WorkingTreeProbe::Dirty,
        }
    );
}

#[test]
fn git_index_visibility_masks_are_conservatively_dirty() {
    for (label, flag) in [
        ("skip-worktree", "--skip-worktree"),
        ("assume-unchanged", "--assume-unchanged"),
    ] {
        let temp = TempDir::new(label);
        let (root, package) = create_workspace(&temp);
        let expected_commit = commit_workspace(&root);
        assert_eq!(
            build_support::probe_source_identity(&package),
            SourceProbe::WorkspaceGit {
                commit_sha1: expected_commit.clone(),
                working_tree: WorkingTreeProbe::Clean,
            }
        );

        let update = isolated_git_at(&root)
            .args(["update-index", flag, "--", "crates/pid-core/tracked.txt"])
            .status()
            .expect("git update-index must run");
        assert!(update.success());
        assert_eq!(
            build_support::probe_source_identity(&package),
            SourceProbe::WorkspaceGit {
                commit_sha1: expected_commit,
                working_tree: WorkingTreeProbe::Dirty,
            }
        );
    }
}

#[test]
fn working_tree_command_failure_is_unknown() {
    let temp = TempDir::new("working-tree-probe-failure");
    let (root, _package) = create_workspace(&temp);
    assert_eq!(
        build_support::probe_working_tree_with_git(
            &root,
            OsStr::new("pid-rs-git-executable-that-does-not-exist"),
        ),
        WorkingTreeProbe::Unknown
    );
}

#[test]
fn git_launch_failure_has_a_distinct_typed_root_state() {
    let temp = TempDir::new("git-unavailable");
    let (_root, package) = create_workspace(&temp);
    assert_eq!(
        build_support::workspace_root_probe_with_git(
            &package,
            OsStr::new("pid-rs-git-executable-that-does-not-exist"),
        ),
        WorkspaceRootProbe::GitUnavailable
    );
}

#[cfg(unix)]
#[test]
fn symlinked_member_escaping_the_workspace_is_not_recognized() {
    use std::os::unix::fs::symlink;

    let temp = TempDir::new("symlink-escape");
    let root = temp.path().join("repository");
    let outside = temp.path().join("outside/pid-core");
    std::fs::create_dir_all(root.join("crates")).expect("crate parent must be creatable");
    std::fs::create_dir_all(&outside).expect("outside member must be creatable");
    for marker in [
        "Cargo.toml",
        "method-catalog.json",
        "release-scope-1.0.json",
    ] {
        std::fs::write(root.join(marker), "{}\n").expect("workspace marker must be writable");
    }
    let status = isolated_git_at(&root)
        .args(["init", "-q"])
        .status()
        .expect("git must be runnable for the symlink test");
    assert!(status.success());
    symlink(&outside, root.join("crates/pid-core")).expect("member symlink must be creatable");

    assert_eq!(
        build_support::git_matched_workspace_root(&root.join("crates/pid-core")),
        None
    );
}

#[test]
fn current_build_resolves_to_its_declared_source_context() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    if let Some(root) = build_support::git_matched_workspace_root(manifest_dir) {
        let expected = isolated_git_at(&root)
            .args(["rev-parse", "--verify", "HEAD^{commit}"])
            .output()
            .expect("git must be runnable")
            .stdout;
        let expected = String::from_utf8(expected)
            .expect("git commit must be UTF-8")
            .trim()
            .to_owned();
        match build_support::probe_source_identity(manifest_dir) {
            SourceProbe::WorkspaceGit { commit_sha1, .. } => assert_eq!(commit_sha1, expected),
            other => panic!("expected layout-matched workspace identity, got {other:?}"),
        }

        let rerun_paths = build_support::git_rerun_paths(&root);
        assert!(!rerun_paths.is_empty());
        assert!(rerun_paths.iter().all(|path| path.exists()));
        return;
    }

    if manifest_dir.join(".cargo_vcs_info.json").is_file() {
        let raw = std::fs::read_to_string(manifest_dir.join(".cargo_vcs_info.json"))
            .expect("Cargo package metadata must be readable");
        let value: serde_json::Value =
            serde_json::from_str(&raw).expect("Cargo package metadata must be valid JSON");
        let expected_commit = value["git"]["sha1"]
            .as_str()
            .expect("Cargo package metadata must contain git.sha1");
        let expected_tree = if value["git"]["dirty"].as_bool().unwrap_or(false) {
            WorkingTreeProbe::Dirty
        } else {
            WorkingTreeProbe::Clean
        };
        assert_eq!(
            build_support::probe_source_identity(manifest_dir),
            SourceProbe::CargoPackage {
                commit_sha1: expected_commit.to_owned(),
                working_tree: expected_tree,
            }
        );
        return;
    }
    panic!("current build has neither a layout-matched workspace nor Cargo package metadata");
}
