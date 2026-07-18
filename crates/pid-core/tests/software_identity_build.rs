#[path = "../build_support.rs"]
mod build_support;

use std::ffi::OsStr;
use std::io::ErrorKind;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use build_support::{SourceProbe, WorkingTreeProbe, WorkspaceRootProbe};

static NEXT_TEMP_ID: AtomicU64 = AtomicU64::new(0);
const SHA1: &str = "0123456789abcdef0123456789abcdef01234567";

fn is_lower_sha1(value: &str) -> bool {
    value.len() == SHA1.len()
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

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
        "GIT_CONFIG",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CEILING_DIRECTORIES",
        "GIT_ATTR_NOSYSTEM",
        "GIT_ATTR_SOURCE",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_EXEC_PATH",
        "GIT_GRAFT_FILE",
        "GIT_GLOB_PATHSPECS",
        "GIT_ICASE_PATHSPECS",
        "GIT_LITERAL_PATHSPECS",
        "GIT_NOGLOB_PATHSPECS",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_PREFIX",
        "GIT_QUARANTINE_PATH",
        "GIT_REFERENCE_BACKEND",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
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
        .env("GIT_ATTR_NOSYSTEM", "1")
        .env("GIT_CONFIG_GLOBAL", null_device)
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_GRAFT_FILE", null_device)
        .env("GIT_LITERAL_PATHSPECS", "1")
        .env("GIT_NO_LAZY_FETCH", "1")
        .env("GIT_NO_REPLACE_OBJECTS", "1")
        .env("GIT_OPTIONAL_LOCKS", "0")
        .env("GIT_TERMINAL_PROMPT", "0")
        .arg("-c")
        .arg("advice.graftFileDeprecated=false")
        .arg("-c")
        .arg(format!("core.attributesFile={null_device}"))
        .arg("-c")
        .arg("core.fsmonitor=false")
        .arg("-c")
        .arg("core.untrackedCache=false")
        .arg("-C")
        .arg(root);
    command
}

fn replacement_aware_git_at(root: &Path) -> Command {
    let mut command = isolated_git_at(root);
    command.env_remove("GIT_NO_REPLACE_OBJECTS");
    command
}

fn fixture_git_output(root: &Path, args: &[&str]) -> String {
    let output = isolated_git_at(root)
        .args(args)
        .output()
        .expect("fixture Git command must run");
    assert!(
        output.status.success(),
        "fixture Git command failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let value = String::from_utf8(output.stdout).expect("fixture Git output must be UTF-8");
    value
        .strip_suffix("\r\n")
        .or_else(|| value.strip_suffix('\n'))
        .unwrap_or(&value)
        .to_owned()
}

fn fixture_git_path(root: &Path, name: &str) -> PathBuf {
    resolve_fixture_git_path(
        root,
        &fixture_git_output(root, &["rev-parse", "--git-path", name]),
    )
}

fn resolve_fixture_git_path(root: &Path, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        path
    } else {
        root.join(path)
    }
}

#[cfg(unix)]
fn write_executable(path: &Path, source: &str) {
    use std::os::unix::fs::PermissionsExt;

    std::fs::write(path, source).expect("wrapper script must be writable");
    let mut permissions = std::fs::metadata(path)
        .expect("wrapper metadata must be readable")
        .permissions();
    permissions.set_mode(0o755);
    std::fs::set_permissions(path, permissions).expect("wrapper must be executable");
}

fn create_workspace_with_init_args(
    temp: &TempDir,
    init_args: &[&str],
) -> Option<(PathBuf, PathBuf)> {
    let root = temp.path().join("repository");
    let package = root.join("crates/pid-core");
    std::fs::create_dir_all(&package).expect("workspace member must be creatable");
    for marker in [
        ".gitattributes",
        "Cargo.toml",
        "method-catalog.json",
        "release-scope-1.0.json",
    ] {
        let contents = if marker == ".gitattributes" {
            "\n"
        } else {
            "{}\n"
        };
        std::fs::write(root.join(marker), contents).expect("workspace marker must be writable");
    }
    let status = isolated_git_at(&root)
        .arg("init")
        .args(init_args)
        .status()
        .expect("git must be runnable for the workspace test");
    status.success().then_some((root, package))
}

fn create_workspace(temp: &TempDir) -> (PathBuf, PathBuf) {
    create_workspace_with_init_args(temp, &["-q"])
        .expect("standard Git repository fixture must initialize")
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

fn configure_git_worktree(root: &Path, worktree: &Path) {
    let status = isolated_git_at(root)
        .args(["config", "core.worktree"])
        .arg(worktree)
        .status()
        .expect("git config must run");
    assert!(status.success());
}

fn identity_rerun_sentinel(root: &Path) -> PathBuf {
    root.join(".pid-rs-source-identity-route-unavailable")
}

fn assert_git_watch_plan_is_bounded(root: &Path, paths: &[PathBuf]) {
    let git_entry = root.join(".git");
    assert!(!paths.iter().any(|path| path == &git_entry && path.is_dir()));
    assert!(paths.iter().all(|path| {
        !path
            .components()
            .any(|component| component.as_os_str() == OsStr::new("objects"))
            || path.ends_with(Path::new("objects/info"))
    }));
}

#[test]
fn generated_build_identity_is_not_rewritten_when_unchanged() {
    let temp = TempDir::new("generated-write-if-changed");
    let path = temp.path().join("generated.rs");

    assert!(build_support::write_if_changed(&path, b"first\n")
        .expect("initial generated file write must succeed"));
    assert!(!build_support::write_if_changed(&path, b"first\n")
        .expect("equal generated bytes must remain untouched"));
    assert!(build_support::write_if_changed(&path, b"second\n")
        .expect("changed generated bytes must be written"));
    assert_eq!(
        std::fs::read(&path).expect("generated file must remain readable"),
        b"second\n"
    );
}

#[cfg(unix)]
#[test]
fn non_utf8_watch_paths_require_conservative_recovery() {
    use std::os::unix::ffi::OsStrExt;

    let path = Path::new(OsStr::from_bytes(b"non-utf8-\xff"));
    assert_eq!(build_support::cargo_rerun_path(path), None);
}

#[cfg(unix)]
#[test]
fn tracked_symlink_is_unknown_even_when_its_index_entry_is_clean() {
    use std::os::unix::fs::symlink;

    let temp = TempDir::new("tracked-symlink");
    let (root, package) = create_workspace(&temp);
    let outside = temp.path().join("outside.rs");
    std::fs::write(&outside, "pub const VALUE: u8 = 1;\n")
        .expect("external symlink target must be writable");
    symlink(&outside, package.join("linked.rs")).expect("fixture symlink must be creatable");
    commit_workspace(&root);

    assert!(matches!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            working_tree: WorkingTreeProbe::Unknown,
            ..
        }
    ));
}

fn assert_package_working_tree(label: &str, git_fields: &str, expected: WorkingTreeProbe) {
    let temp = TempDir::new(label);
    let package = package_dir(&temp);
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}"{git_fields}}},"path_in_vcs":"crates/pid-core"}}"#),
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::CargoPackage {
            commit_sha1: SHA1.to_owned(),
            working_tree: expected,
        }
    );
}

#[test]
fn absent_cargo_dirty_flag_is_unknown() {
    assert_eq!(WorkingTreeProbe::Unknown.as_str(), "unknown");
    assert_package_working_tree("unknown-package", "", WorkingTreeProbe::Unknown);
}

#[test]
fn explicit_false_cargo_dirty_flag_is_clean() {
    assert_eq!(WorkingTreeProbe::Clean.as_str(), "clean");
    assert_package_working_tree(
        "clean-package",
        r#","dirty":false"#,
        WorkingTreeProbe::Clean,
    );
}

#[test]
fn explicit_true_cargo_dirty_flag_is_dirty() {
    assert_eq!(WorkingTreeProbe::Dirty.as_str(), "dirty");
    assert_package_working_tree("dirty-package", r#","dirty":true"#, WorkingTreeProbe::Dirty);
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
            working_tree: WorkingTreeProbe::Unknown,
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
fn source_archive_layout_without_git_or_package_metadata_is_unavailable() {
    let temp = TempDir::new("source-archive");
    let (root, package) = create_workspace(&temp);
    std::fs::remove_dir_all(root.join(".git")).expect("fixture Git metadata must be removable");

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "unrecognized_workspace_layout",
        }
    );
    let root = root.canonicalize().expect("fixture root must canonicalize");
    assert_eq!(
        build_support::workspace_candidate_root(&package),
        Some(root.clone())
    );
    let paths = build_support::git_rerun_paths(&root);
    assert!(paths.contains(&root.join(".git")));
    assert!(paths.contains(&identity_rerun_sentinel(&root)));
}

#[test]
fn candidate_workspace_watches_missing_markers_and_git_route() {
    let temp = TempDir::new("candidate-workspace-recovery");
    let (root, package) = create_workspace(&temp);
    commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let missing_marker = root.join("method-catalog.json");
    std::fs::remove_file(&missing_marker).expect("workspace marker must be removable");
    std::fs::remove_dir_all(root.join(".git")).expect("fixture Git metadata must be removable");

    assert_eq!(
        build_support::workspace_candidate_root(&package),
        Some(root.clone())
    );
    assert_eq!(build_support::layout_matched_workspace_root(&package), None);
    let paths = build_support::workspace_rerun_paths(&package);
    assert!(paths.contains(&missing_marker));
    assert!(paths.contains(&root.join(".git")));
    assert!(paths.contains(&identity_rerun_sentinel(&root)));
}

#[test]
fn unborn_layout_matched_repository_is_git_unavailable() {
    let temp = TempDir::new("unborn-git-head");
    let (_root, package) = create_workspace(&temp);

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "git_unavailable",
        }
    );
}

#[test]
fn sha256_layout_matched_repository_is_typed_as_an_invalid_format_one_commit() {
    let temp = TempDir::new("sha256-git-objects");
    let root = temp.path().join("repository");
    let package = root.join("crates/pid-core");
    std::fs::create_dir_all(&package).expect("workspace member must be creatable");
    for marker in [
        ".gitattributes",
        "Cargo.toml",
        "method-catalog.json",
        "release-scope-1.0.json",
    ] {
        let contents = if marker == ".gitattributes" {
            "\n"
        } else {
            "{}\n"
        };
        std::fs::write(root.join(marker), contents).expect("workspace marker must be writable");
    }
    let status = isolated_git_at(&root)
        .args(["init", "-q", "--object-format=sha256"])
        .status()
        .expect("git must be runnable for the SHA-256 repository test");
    if !status.success() {
        eprintln!("Git does not support SHA-256 object-format fixtures; route test skipped");
        return;
    }
    let commit = commit_workspace(&root);
    assert_eq!(commit.len(), 64);

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "invalid_git_commit",
        }
    );
}

#[cfg(unix)]
#[test]
fn dangling_git_entry_never_falls_through_to_package_metadata() {
    use std::os::unix::fs::symlink;

    let temp = TempDir::new("dangling-git-entry");
    let (root, package) = create_workspace(&temp);
    std::fs::remove_dir_all(root.join(".git")).expect("fixture Git metadata must be removable");
    symlink("missing-git-target", root.join(".git")).expect("dangling Git entry must be creatable");
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}","dirty":false}},"path_in_vcs":"crates/pid-core"}}"#),
    );

    assert_eq!(
        build_support::layout_matched_workspace_root(&package),
        Some(root.canonicalize().expect("fixture root must canonicalize"))
    );
    assert_eq!(
        build_support::workspace_root_probe(&package),
        WorkspaceRootProbe::GitUnavailable
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "git_unavailable",
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

#[cfg(unix)]
#[test]
fn git_older_than_the_identity_contract_cannot_claim_cleanliness() {
    let temp = TempDir::new("old-git-version");
    let (root, package) = create_workspace(&temp);
    let commit = commit_workspace(&root);
    let wrapper = temp.path().join("old-git");
    write_executable(
        &wrapper,
        "#!/bin/sh\nfor argument in \"$@\"; do\n  if [ \"$argument\" = \"--version\" ]; then\n    echo 'git version 2.44.9'\n    exit 0\n  fi\ndone\nexec git \"$@\"\n",
    );

    assert_eq!(
        build_support::probe_source_identity_with_git(&package, wrapper.as_os_str()),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit,
            working_tree: WorkingTreeProbe::Unknown,
        }
    );
}

#[cfg(unix)]
#[test]
fn head_change_during_probe_cannot_create_a_mixed_clean_identity() {
    let temp = TempDir::new("head-change-during-probe");
    let (root, package) = create_workspace(&temp);
    let first_commit = commit_workspace(&root);
    std::fs::write(root.join("crates/pid-core/second.txt"), "second\n")
        .expect("second fixture revision must be writable");
    let second_commit = commit_workspace(&root);
    let reset = isolated_git_at(&root)
        .args(["reset", "--hard", "-q", &first_commit])
        .status()
        .expect("fixture reset must run");
    assert!(reset.success());

    let wrapper = temp.path().join("switch-head-git");
    std::fs::write(
        wrapper.with_extension("root"),
        root.as_os_str().as_encoded_bytes(),
    )
    .expect("wrapper root routing must be writable");
    std::fs::write(wrapper.with_extension("target"), second_commit.as_bytes())
        .expect("wrapper target routing must be writable");
    write_executable(
        &wrapper,
        "#!/bin/sh\nroot=$(cat \"$0.root\")\ntarget=$(cat \"$0.target\")\ncommand_name=\nhead_operand=0\nfor argument in \"$@\"; do\n  case \"$argument\" in\n    rev-parse) command_name=rev-parse ;;\n    'HEAD^{commit}') head_operand=1 ;;\n  esac\ndone\nif [ \"$command_name\" = rev-parse ] && [ \"$head_operand\" = 1 ] && [ ! -e \"$0.state\" ]; then\n  git \"$@\"\n  status=$?\n  : >\"$0.state\"\n  git -C \"$root\" reset --hard \"$target\" >/dev/null\n  exit $status\nfi\nexec git \"$@\"\n",
    );

    assert_eq!(
        build_support::probe_source_identity_with_git(&package, wrapper.as_os_str()),
        SourceProbe::WorkspaceGit {
            commit_sha1: second_commit,
            working_tree: WorkingTreeProbe::Unknown,
        }
    );
}

#[cfg(unix)]
#[test]
fn final_status_reread_observes_a_post_status_worktree_change() {
    let temp = TempDir::new("post-status-change");
    let (root, package) = create_workspace(&temp);
    let commit = commit_workspace(&root);
    let wrapper = temp.path().join("change-after-status-git");
    std::fs::write(
        wrapper.with_extension("root"),
        root.as_os_str().as_encoded_bytes(),
    )
    .expect("wrapper root routing must be writable");
    write_executable(
        &wrapper,
        "#!/bin/sh\nroot=$(cat \"$0.root\")\ncommand_name=\nfor argument in \"$@\"; do\n  if [ \"$argument\" = status ]; then\n    command_name=status\n  fi\ndone\nif [ \"$command_name\" = status ] && [ ! -e \"$0.state\" ]; then\n  git \"$@\"\n  status=$?\n  : >\"$0.state\"\n  printf 'changed\\n' >\"$root/crates/pid-core/tracked.txt\"\n  exit $status\nfi\nexec git \"$@\"\n",
    );

    assert_eq!(
        build_support::probe_source_identity_with_git(&package, wrapper.as_os_str()),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit,
            working_tree: WorkingTreeProbe::Dirty,
        }
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

#[test]
fn layout_matched_git_failure_never_falls_through_to_package_metadata() {
    let temp = TempDir::new("git-failure-no-package-fallback");
    let (_root, package) = create_workspace(&temp);
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}","dirty":false}},"path_in_vcs":"crates/pid-core"}}"#),
    );

    assert_eq!(
        build_support::probe_source_identity_with_git(
            &package,
            OsStr::new("pid-rs-git-executable-that-does-not-exist"),
        ),
        SourceProbe::Unavailable {
            reason: "git_unavailable",
        }
    );
}

#[test]
fn layout_matched_git_existing_wrong_root_never_uses_package_metadata() {
    let temp = TempDir::new("git-existing-wrong-root");
    let (root, package) = create_workspace(&temp);
    let reported_root = temp.path().join("different-worktree");
    std::fs::create_dir_all(&reported_root).expect("reported worktree must be creatable");
    configure_git_worktree(&root, &reported_root);
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}","dirty":false}},"path_in_vcs":"crates/pid-core"}}"#),
    );

    assert_eq!(
        build_support::workspace_root_probe(&package),
        WorkspaceRootProbe::GitUnavailable
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "git_unavailable",
        }
    );
}

#[test]
fn layout_matched_git_noncanonical_root_never_uses_package_metadata() {
    let temp = TempDir::new("git-noncanonical-root");
    let (root, package) = create_workspace(&temp);
    let reported_root = temp.path().join("missing-worktree");
    configure_git_worktree(&root, &reported_root);
    write_vcs_info(
        &package,
        &format!(r#"{{"git":{{"sha1":"{SHA1}","dirty":false}},"path_in_vcs":"crates/pid-core"}}"#),
    );

    assert_eq!(
        build_support::workspace_root_probe(&package),
        WorkspaceRootProbe::GitUnavailable
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "git_unavailable",
        }
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
        ".gitattributes",
        "Cargo.toml",
        "method-catalog.json",
        "release-scope-1.0.json",
    ] {
        let contents = if marker == ".gitattributes" {
            "\n"
        } else {
            "{}\n"
        };
        std::fs::write(root.join(marker), contents).expect("workspace marker must be writable");
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
fn healthy_git_watch_plan_tracks_exact_identity_inputs() {
    let temp = TempDir::new("healthy-rerun-plan");
    let (root, package) = create_workspace(&temp);
    let commit = commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");

    assert_eq!(
        build_support::workspace_candidate_root(&package),
        Some(root.clone())
    );
    let paths = build_support::git_rerun_paths(&root);
    for required in [
        fixture_git_path(&root, "HEAD"),
        fixture_git_path(&root, "index"),
        fixture_git_path(&root, "config"),
        fixture_git_path(&root, "info"),
        fixture_git_path(&root, "objects/info"),
    ] {
        assert!(paths.contains(&required), "missing watch for {required:?}");
    }
    let current_ref = fixture_git_output(&root, &["symbolic-ref", "HEAD"]);
    assert!(paths.contains(&fixture_git_path(&root, &current_ref)));
    assert!(!paths.contains(&identity_rerun_sentinel(&root)));
    assert!(paths.iter().all(|path| path.exists()));
    assert_git_watch_plan_is_bounded(&root, &paths);

    let workspace_paths = build_support::workspace_rerun_paths(&package);
    assert!(workspace_paths.contains(&root.join(".gitattributes")));
    assert!(workspace_paths.contains(&root.join("crates")));

    let complete_source = SourceProbe::WorkspaceGit {
        commit_sha1: commit.clone(),
        working_tree: WorkingTreeProbe::Clean,
    };
    assert!(
        !build_support::workspace_rerun_paths_for_source(&package, &complete_source)
            .contains(&identity_rerun_sentinel(&root))
    );
    let incomplete_source = SourceProbe::WorkspaceGit {
        commit_sha1: commit,
        working_tree: WorkingTreeProbe::Unknown,
    };
    assert!(
        build_support::workspace_rerun_paths_for_source(&package, &incomplete_source)
            .contains(&identity_rerun_sentinel(&root))
    );
}

#[test]
fn git_route_corruption_forces_reruns_until_config_recovers() {
    let temp = TempDir::new("rerun-route-recovery");
    let (root, package) = create_workspace(&temp);
    commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let config = fixture_git_path(&root, "config");

    assert!(build_support::git_rerun_paths(&root).contains(&config));
    let wrong_root = temp.path().join("wrong-worktree");
    std::fs::create_dir_all(&wrong_root).expect("wrong worktree fixture must be creatable");
    configure_git_worktree(&root, &wrong_root);
    assert_eq!(
        build_support::workspace_root_probe(&package),
        WorkspaceRootProbe::GitUnavailable
    );
    assert!(
        build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)),
        "an invalid Git route must force Cargo to re-run the build script"
    );

    let recovered = isolated_git_at(&root)
        .args(["config", "--unset", "core.worktree"])
        .status()
        .expect("Git config recovery must run");
    assert!(recovered.success());
    assert!(matches!(
        build_support::workspace_root_probe(&package),
        WorkspaceRootProbe::GitMatched(_)
    ));
    assert!(!build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)));
}

#[test]
fn occupied_rerun_sentinel_cannot_disable_fail_closed_invalidation() {
    let temp = TempDir::new("occupied-rerun-sentinel");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let occupied = identity_rerun_sentinel(&root);
    std::fs::write(&occupied, "occupied\n").expect("sentinel collision must be writable");
    let wrong_root = temp.path().join("wrong-worktree");
    std::fs::create_dir_all(&wrong_root).expect("wrong worktree fixture must be creatable");
    configure_git_worktree(&root, &wrong_root);

    let paths = build_support::git_rerun_paths(&root);
    let fallback = root.join(".pid-rs-source-identity-route-unavailable-1");
    assert!(!paths.contains(&occupied));
    assert!(paths.contains(&fallback));
    assert!(!fallback.exists());
}

#[test]
fn missing_head_object_forces_reruns_until_the_object_recovers() {
    let temp = TempDir::new("missing-head-object");
    let (root, package) = create_workspace(&temp);
    let commit = commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let object = fixture_git_path(&root, "objects")
        .join(&commit[..2])
        .join(&commit[2..]);
    let bytes = std::fs::read(&object).expect("loose fixture commit object must be readable");
    std::fs::remove_file(&object).expect("fixture commit object must be removable");

    assert!(matches!(
        build_support::probe_source_identity(&package),
        SourceProbe::Unavailable {
            reason: "git_unavailable"
        }
    ));
    assert!(build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)));

    std::fs::write(&object, bytes).expect("fixture commit object must be restorable");
    assert!(matches!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            working_tree: WorkingTreeProbe::Clean,
            ..
        }
    ));
    assert!(!build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)));
}

#[test]
fn linked_worktree_watch_plan_covers_private_and_common_metadata() {
    let temp = TempDir::new("linked-worktree-rerun-plan");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let linked = temp.path().join("linked-worktree");
    let status = isolated_git_at(&root)
        .args(["worktree", "add", "-q", "-b", "identity-linked"])
        .arg(&linked)
        .status()
        .expect("linked worktree creation must run");
    assert!(status.success());
    let enabled = isolated_git_at(&root)
        .args(["config", "extensions.worktreeConfig", "true"])
        .status()
        .expect("worktree configuration enablement must run");
    assert!(enabled.success());
    let configured = isolated_git_at(&linked)
        .args(["config", "--worktree", "identity.marker", "present"])
        .status()
        .expect("per-worktree configuration must run");
    assert!(configured.success());
    let linked = linked
        .canonicalize()
        .expect("linked worktree must canonicalize");

    let paths = build_support::git_rerun_paths(&linked);
    for required in [
        linked.join(".git"),
        fixture_git_path(&linked, "HEAD"),
        fixture_git_path(&linked, "index"),
        fixture_git_path(&linked, "commondir"),
        fixture_git_path(&linked, "config"),
        fixture_git_path(&linked, "config.worktree"),
    ] {
        assert!(paths.contains(&required), "missing watch for {required:?}");
    }
    assert!(!paths.contains(&identity_rerun_sentinel(&linked)));
    assert!(paths.iter().all(|path| path.exists()));
    assert_git_watch_plan_is_bounded(&linked, &paths);
}

#[test]
fn config_includes_are_watched_and_force_conservative_reruns() {
    let temp = TempDir::new("config-include-rerun-plan");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let included = fixture_git_path(&root, "config")
        .parent()
        .expect("Git config must have a parent")
        .join("identity-include.config");
    std::fs::write(&included, "[identity]\n\tmarker = true\n")
        .expect("included Git config must be writable");
    let configured = isolated_git_at(&root)
        .args(["config", "include.path", "identity-include.config"])
        .status()
        .expect("Git include configuration must run");
    assert!(configured.success());

    let paths = build_support::git_rerun_paths(&root);
    assert!(paths.contains(&included));
    assert!(paths.contains(&identity_rerun_sentinel(&root)));
    assert_git_watch_plan_is_bounded(&root, &paths);
}

#[test]
fn repository_attribute_tree_is_typed_unknown_until_removed() {
    let temp = TempDir::new("attribute-tree-fail-closed");
    let (root, package) = create_workspace(&temp);
    let commit = commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let configured = isolated_git_at(&root)
        .args(["config", "attr.tree", "HEAD"])
        .status()
        .expect("attribute-tree configuration must run");
    assert!(configured.success());

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit.clone(),
            working_tree: WorkingTreeProbe::Unknown,
        }
    );
    assert!(build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)));

    let removed = isolated_git_at(&root)
        .args(["config", "--unset", "attr.tree"])
        .status()
        .expect("attribute-tree configuration removal must run");
    assert!(removed.success());
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit,
            working_tree: WorkingTreeProbe::Clean,
        }
    );
}

#[test]
fn external_clean_filter_is_typed_unknown_without_execution() {
    let temp = TempDir::new("external-filter-fail-closed");
    let (root, package) = create_workspace(&temp);
    commit_workspace(&root);
    std::fs::write(root.join("crates/pid-core/tracked.txt"), "TRACKED\n")
        .expect("uppercase fixture must be writable");
    let added = isolated_git_at(&root)
        .args(["add", "--force", "."])
        .status()
        .expect("uppercase fixture staging must run");
    assert!(added.success());
    let committed = isolated_git_at(&root)
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
            "uppercase fixture",
        ])
        .status()
        .expect("uppercase fixture commit must run");
    assert!(committed.success());
    let commit = fixture_git_output(&root, &["rev-parse", "HEAD"]);
    std::fs::write(root.join("crates/pid-core/tracked.txt"), "tracked\n")
        .expect("lowercase worktree fixture must be writable");
    let configured = isolated_git_at(&root)
        .args([
            "config",
            "filter.identity.clean",
            "pid-rs-filter-that-must-never-run",
        ])
        .status()
        .expect("filter configuration must run");
    assert!(configured.success());
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit.clone(),
            working_tree: WorkingTreeProbe::Dirty,
        }
    );

    let root = root.canonicalize().expect("fixture root must canonicalize");
    let info = fixture_git_path(&root, "info");
    let plan = build_support::git_rerun_paths(&root);
    assert!(plan.contains(&info));
    std::fs::write(
        info.join("attributes"),
        "crates/pid-core/tracked.txt filter=identity\n",
    )
    .expect("repository attributes fixture must be writable");
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit,
            working_tree: WorkingTreeProbe::Unknown,
        }
    );
    assert!(build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)));
}

#[cfg(unix)]
#[test]
fn literal_unspecified_filter_value_cannot_execute_a_driver() {
    let temp = TempDir::new("literal-unspecified-filter");
    let (root, package) = create_workspace(&temp);
    let commit = commit_workspace(&root);
    let side_effect = temp.path().join("filter-executed");
    let command = format!("touch '{}' && cat", side_effect.display());
    let configured = isolated_git_at(&root)
        .args(["config", "filter.unspecified.clean", &command])
        .status()
        .expect("literal filter driver configuration must run");
    assert!(configured.success());
    let info = fixture_git_path(&root, "info");
    std::fs::write(
        info.join("attributes"),
        "crates/pid-core/tracked.txt filter=unspecified\n",
    )
    .expect("literal filter attribute must be writable");

    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: commit,
            working_tree: WorkingTreeProbe::Unknown,
        }
    );
    assert!(
        !side_effect.exists(),
        "the external filter driver must not execute during the probe"
    );
}

#[test]
fn packed_current_ref_watches_packed_refs_and_loose_ref_namespace() {
    let temp = TempDir::new("packed-ref-rerun-plan");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let current_ref = fixture_git_output(&root, &["symbolic-ref", "HEAD"]);
    let loose_ref = fixture_git_path(&root, &current_ref);
    let packed = isolated_git_at(&root)
        .args(["pack-refs", "--all", "--prune"])
        .status()
        .expect("Git ref packing must run");
    assert!(packed.success());
    assert!(!loose_ref.exists());

    let paths = build_support::git_rerun_paths(&root);
    let packed_refs = fixture_git_path(&root, "packed-refs");
    let refs_root = fixture_git_path(&root, "refs");
    assert!(paths.contains(&packed_refs));
    assert!(paths.iter().any(|path| {
        path.is_dir() && loose_ref.starts_with(path) && path.starts_with(&refs_root)
    }));
    assert!(!paths.contains(&identity_rerun_sentinel(&root)));
    assert_git_watch_plan_is_bounded(&root, &paths);
}

#[test]
fn detached_head_watch_plan_needs_no_ref_namespace() {
    let temp = TempDir::new("detached-head-rerun-plan");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let detached = isolated_git_at(&root)
        .args(["switch", "--detach", "-q"])
        .status()
        .expect("detached HEAD creation must run");
    assert!(detached.success());
    let root = root.canonicalize().expect("fixture root must canonicalize");

    let paths = build_support::git_rerun_paths(&root);
    assert!(paths.contains(&fixture_git_path(&root, "HEAD")));
    assert!(!paths.contains(&identity_rerun_sentinel(&root)));
    assert_git_watch_plan_is_bounded(&root, &paths);
}

#[test]
fn multi_hop_symbolic_ref_chain_is_watched_completely() {
    let temp = TempDir::new("symbolic-ref-chain-rerun-plan");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let original_ref = fixture_git_output(&root, &["symbolic-ref", "HEAD"]);
    let alias_ref = "refs/heads/identity-alias";
    let alias = isolated_git_at(&root)
        .args(["symbolic-ref", alias_ref, &original_ref])
        .status()
        .expect("symbolic ref alias creation must run");
    assert!(alias.success());
    let redirected = isolated_git_at(&root)
        .args(["symbolic-ref", "HEAD", alias_ref])
        .status()
        .expect("HEAD redirection must run");
    assert!(redirected.success());
    let root = root.canonicalize().expect("fixture root must canonicalize");

    let paths = build_support::git_rerun_paths(&root);
    assert!(paths.contains(&fixture_git_path(&root, "HEAD")));
    assert!(paths.contains(&fixture_git_path(&root, alias_ref)));
    assert!(paths.contains(&fixture_git_path(&root, &original_ref)));
    assert!(!paths.contains(&identity_rerun_sentinel(&root)));
    assert_git_watch_plan_is_bounded(&root, &paths);
}

#[test]
fn ref_storage_payload_forces_conservative_reruns() {
    let temp = TempDir::new("ref-storage-payload");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let configured = isolated_git_at(&root)
        .args([
            "config",
            "extensions.refStorage",
            "files:///external-reference-store",
        ])
        .status()
        .expect("ref-storage payload configuration must run");
    assert!(configured.success());
    let root = root.canonicalize().expect("fixture root must canonicalize");

    assert!(build_support::git_rerun_paths(&root).contains(&identity_rerun_sentinel(&root)));
}

#[test]
fn split_index_shared_file_is_part_of_the_watch_plan() {
    let temp = TempDir::new("split-index-rerun-plan");
    let (root, _package) = create_workspace(&temp);
    commit_workspace(&root);
    let root = root.canonicalize().expect("fixture root must canonicalize");
    let enabled = isolated_git_at(&root)
        .args(["update-index", "--split-index"])
        .status()
        .expect("split-index enablement must run");
    if !enabled.success() {
        eprintln!("Git does not support split-index fixtures; watch-plan test skipped");
        return;
    }
    let shared = fixture_git_output(&root, &["rev-parse", "--shared-index-path"]);
    assert!(!shared.is_empty());
    let shared = resolve_fixture_git_path(&root, &shared);

    let paths = build_support::git_rerun_paths(&root);
    assert!(paths.contains(&shared));
    assert!(shared.exists());
    assert!(!paths.contains(&identity_rerun_sentinel(&root)));
    assert_git_watch_plan_is_bounded(&root, &paths);
}

#[test]
fn replacement_objects_cannot_change_source_identity_or_cleanliness() {
    let temp = TempDir::new("replacement-neutrality");
    let (root, package) = create_workspace(&temp);
    let expected_commit = commit_workspace(&root);
    let replacement_worktree = temp.path().join("replacement-worktree");
    let created = isolated_git_at(&root)
        .args(["worktree", "add", "-q", "-b", "replacement-source"])
        .arg(&replacement_worktree)
        .status()
        .expect("replacement worktree creation must run");
    assert!(created.success());
    std::fs::write(
        replacement_worktree.join("crates/pid-core/tracked.txt"),
        "replacement tree\n",
    )
    .expect("replacement fixture must be writable");
    let added = isolated_git_at(&replacement_worktree)
        .args(["add", "--force", "."])
        .status()
        .expect("replacement fixture staging must run");
    assert!(added.success());
    let committed = isolated_git_at(&replacement_worktree)
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
            "replacement fixture",
        ])
        .status()
        .expect("replacement fixture commit must run");
    assert!(committed.success());
    let replacement_commit = fixture_git_output(&replacement_worktree, &["rev-parse", "HEAD"]);
    let installed = isolated_git_at(&root)
        .args(["replace", &expected_commit, &replacement_commit])
        .status()
        .expect("replacement ref installation must run");
    assert!(installed.success());

    let raw_status = replacement_aware_git_at(&root)
        .args([
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
            "--",
            "crates/pid-core",
        ])
        .output()
        .expect("replacement-aware Git status must run");
    assert!(raw_status.status.success());
    assert!(
        !raw_status.stdout.is_empty(),
        "fixture must demonstrate that the replacement tree changes status"
    );
    assert_eq!(
        build_support::probe_source_identity(&package),
        SourceProbe::WorkspaceGit {
            commit_sha1: expected_commit,
            working_tree: WorkingTreeProbe::Clean,
        }
    );
}

#[test]
fn reftable_linked_worktree_watches_private_and_common_tables() {
    let temp = TempDir::new("reftable-rerun-plan");
    let Some((root, _package)) =
        create_workspace_with_init_args(&temp, &["-q", "--ref-format=reftable"])
    else {
        eprintln!("Git does not support reftable fixtures; watch-plan test skipped");
        return;
    };
    commit_workspace(&root);
    let linked = temp.path().join("reftable-linked-worktree");
    let created = isolated_git_at(&root)
        .args(["worktree", "add", "-q", "-b", "reftable-linked"])
        .arg(&linked)
        .status()
        .expect("reftable linked-worktree creation must run");
    if !created.success() {
        eprintln!("Git cannot create a linked worktree for reftable; watch-plan test skipped");
        return;
    }
    let linked = linked
        .canonicalize()
        .expect("reftable linked worktree must canonicalize");
    assert_eq!(
        fixture_git_output(&linked, &["rev-parse", "--show-ref-format"]),
        "reftable"
    );
    let private_tables = fixture_git_path(&linked, "reftable/tables.list");
    let common_dir = resolve_fixture_git_path(
        &linked,
        &fixture_git_output(&linked, &["rev-parse", "--git-common-dir"]),
    );
    let common_tables = common_dir.join("reftable/tables.list");
    assert_ne!(private_tables, common_tables);

    let paths = build_support::git_rerun_paths(&linked);
    assert!(paths.contains(&private_tables));
    assert!(paths.contains(&common_tables));
    assert!(private_tables.exists());
    assert!(common_tables.exists());
    assert!(!paths.contains(&identity_rerun_sentinel(&linked)));
    assert_git_watch_plan_is_bounded(&linked, &paths);
}

#[test]
fn current_build_resolves_to_its_declared_source_context() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    match build_support::workspace_root_probe(manifest_dir) {
        WorkspaceRootProbe::GitMatched(root) => {
            let output = isolated_git_at(&root)
                .args(["rev-parse", "--verify", "HEAD^{commit}"])
                .output()
                .expect("git must be runnable");
            let expected = output
                .status
                .success()
                .then(|| String::from_utf8(output.stdout).ok())
                .flatten()
                .map(|value| value.trim().to_owned())
                .filter(|value| !value.is_empty());
            let observed = build_support::probe_source_identity(manifest_dir);
            match (expected, observed) {
                (
                    Some(expected),
                    SourceProbe::WorkspaceGit { commit_sha1, .. },
                ) if is_lower_sha1(&expected) => assert_eq!(commit_sha1, expected),
                (
                    Some(expected),
                    SourceProbe::Unavailable {
                        reason: "invalid_git_commit",
                    },
                ) if !is_lower_sha1(&expected) => {}
                (
                    None,
                    SourceProbe::Unavailable {
                        reason: "git_unavailable",
                    },
                ) => {}
                (expected, other) => panic!(
                    "layout-matched Git source mismatch: command returned {expected:?}, probe returned {other:?}"
                ),
            }

            let rerun_paths = build_support::git_rerun_paths(&root);
            assert!(!rerun_paths.is_empty());
            assert_git_watch_plan_is_bounded(&root, &rerun_paths);
            return;
        }
        WorkspaceRootProbe::GitUnavailable => {
            assert_eq!(
                build_support::probe_source_identity(manifest_dir),
                SourceProbe::Unavailable {
                    reason: "git_unavailable",
                }
            );
            return;
        }
        WorkspaceRootProbe::LayoutMismatch => {}
    }

    let cargo_vcs_info = manifest_dir.join(".cargo_vcs_info.json");
    let metadata = std::fs::symlink_metadata(&cargo_vcs_info);
    match build_support::probe_source_identity(manifest_dir) {
        SourceProbe::CargoPackage {
            commit_sha1,
            working_tree,
        } => {
            assert!(metadata
                .expect("recognized Cargo package metadata must be readable")
                .file_type()
                .is_file());
            let raw = std::fs::read_to_string(cargo_vcs_info)
                .expect("recognized Cargo package metadata must be readable");
            let value: serde_json::Value = serde_json::from_str(&raw)
                .expect("recognized Cargo package metadata must be valid JSON");
            let expected_commit = value["git"]["sha1"]
                .as_str()
                .expect("recognized Cargo package metadata must contain git.sha1");
            let expected_tree = match value["git"].get("dirty").and_then(|dirty| dirty.as_bool()) {
                Some(true) => WorkingTreeProbe::Dirty,
                Some(false) => WorkingTreeProbe::Clean,
                None => WorkingTreeProbe::Unknown,
            };
            assert_eq!(commit_sha1, expected_commit);
            assert_eq!(working_tree, expected_tree);
        }
        SourceProbe::Unavailable {
            reason: "invalid_cargo_vcs_info",
        } => {
            assert!(!metadata.is_err_and(|error| error.kind() == ErrorKind::NotFound));
        }
        SourceProbe::Unavailable {
            reason: "unrecognized_workspace_layout",
        } => {
            assert!(metadata.is_err_and(|error| error.kind() == ErrorKind::NotFound));
        }
        other => panic!("layout-mismatched source probe returned an inconsistent route: {other:?}"),
    }
}
