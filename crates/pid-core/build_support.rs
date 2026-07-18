use std::ffi::OsStr;
use std::io::ErrorKind;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Deserialize;

const EXPECTED_PATH_IN_VCS: &str = "crates/pid-core";
const SHA1_HEX_LEN: usize = 40;

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum SourceProbe {
    WorkspaceGit {
        commit_sha1: String,
        working_tree: WorkingTreeProbe,
    },
    CargoPackage {
        commit_sha1: String,
        working_tree: WorkingTreeProbe,
    },
    Unavailable {
        reason: &'static str,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum WorkingTreeProbe {
    Clean,
    Dirty,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum WorkspaceRootProbe {
    GitMatched(PathBuf),
    LayoutMismatch,
    GitUnavailable,
}

impl WorkingTreeProbe {
    pub(crate) const fn as_str(self) -> &'static str {
        match self {
            Self::Clean => "clean",
            Self::Dirty => "dirty",
            Self::Unknown => "unknown",
        }
    }
}

pub(crate) fn probe_source_identity(manifest_dir: &Path) -> SourceProbe {
    let root = match workspace_root_probe(manifest_dir) {
        WorkspaceRootProbe::GitMatched(root) => root,
        WorkspaceRootProbe::GitUnavailable => {
            return SourceProbe::Unavailable {
                reason: "git_unavailable",
            };
        }
        WorkspaceRootProbe::LayoutMismatch => {
            return probe_package_or_layout_mismatch(manifest_dir);
        }
    };
    let Some(commit_sha1) =
        command_output(git_command(&root).args(["rev-parse", "--verify", "HEAD^{commit}"]))
    else {
        return SourceProbe::Unavailable {
            reason: "git_unavailable",
        };
    };
    if !is_sha1_hex(&commit_sha1) {
        return SourceProbe::Unavailable {
            reason: "invalid_git_commit",
        };
    }

    let working_tree = probe_working_tree_with_git(&root, OsStr::new("git"));

    SourceProbe::WorkspaceGit {
        commit_sha1,
        working_tree,
    }
}

pub(crate) fn probe_working_tree_with_git(root: &Path, git_program: &OsStr) -> WorkingTreeProbe {
    let status_probe = match git_command_with_program(root, git_program)
        .args([
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
            "--ignored=matching",
            "--",
            EXPECTED_PATH_IN_VCS,
        ])
        .output()
    {
        Ok(output) if output.status.success() => {
            if output.stdout.is_empty() {
                WorkingTreeProbe::Clean
            } else {
                WorkingTreeProbe::Dirty
            }
        }
        _ => WorkingTreeProbe::Unknown,
    };

    let index_probe = match git_command_with_program(root, git_program)
        .args(["ls-files", "-v", "--", EXPECTED_PATH_IN_VCS])
        .output()
    {
        Ok(output) if output.status.success() => {
            // `git ls-files -v` emits `S` for skip-worktree and lowercases any status tag for
            // assume-unchanged. Treat either visibility mask as dirty even before a hidden file
            // differs, because a later status probe is not entitled to infer cleanliness.
            let masked = output.stdout.split(|byte| *byte == b'\n').any(|line| {
                line.first()
                    .is_some_and(|tag| *tag == b'S' || tag.is_ascii_lowercase())
            });
            if masked {
                WorkingTreeProbe::Dirty
            } else {
                WorkingTreeProbe::Clean
            }
        }
        _ => WorkingTreeProbe::Unknown,
    };

    combine_working_tree_probes(status_probe, index_probe)
}

fn combine_working_tree_probes(
    status_probe: WorkingTreeProbe,
    index_probe: WorkingTreeProbe,
) -> WorkingTreeProbe {
    match (status_probe, index_probe) {
        (WorkingTreeProbe::Dirty, _) | (_, WorkingTreeProbe::Dirty) => WorkingTreeProbe::Dirty,
        (WorkingTreeProbe::Unknown, _) | (_, WorkingTreeProbe::Unknown) => {
            WorkingTreeProbe::Unknown
        }
        (WorkingTreeProbe::Clean, WorkingTreeProbe::Clean) => WorkingTreeProbe::Clean,
    }
}

fn probe_package_or_layout_mismatch(manifest_dir: &Path) -> SourceProbe {
    let cargo_vcs_info = manifest_dir.join(".cargo_vcs_info.json");
    match std::fs::symlink_metadata(&cargo_vcs_info) {
        Ok(metadata) => {
            if !metadata.file_type().is_file() {
                return invalid_cargo_vcs_info();
            }
            probe_cargo_vcs_info(&cargo_vcs_info)
        }
        Err(error) if error.kind() == ErrorKind::NotFound => SourceProbe::Unavailable {
            reason: "unrecognized_workspace_layout",
        },
        Err(_) => invalid_cargo_vcs_info(),
    }
}

pub(crate) fn layout_matched_workspace_root(manifest_dir: &Path) -> Option<PathBuf> {
    if manifest_dir.file_name()?.to_str()? != "pid-core" {
        return None;
    }
    let crates_dir = manifest_dir.parent()?;
    if crates_dir.file_name()?.to_str()? != "crates" {
        return None;
    }
    let root = crates_dir.parent()?;
    for marker in [
        "Cargo.toml",
        "method-catalog.json",
        "release-scope-1.0.json",
    ] {
        if !root.join(marker).is_file() {
            return None;
        }
    }
    if !root.join(".git").exists() {
        return None;
    }

    let canonical_root = root.canonicalize().ok()?;
    let canonical_manifest = manifest_dir.canonicalize().ok()?;
    let canonical_member = canonical_root
        .join(EXPECTED_PATH_IN_VCS)
        .canonicalize()
        .ok()?;
    (canonical_manifest == canonical_member && canonical_manifest.starts_with(&canonical_root))
        .then_some(canonical_root)
}

pub(crate) fn workspace_root_probe(manifest_dir: &Path) -> WorkspaceRootProbe {
    workspace_root_probe_with_git(manifest_dir, OsStr::new("git"))
}

pub(crate) fn workspace_root_probe_with_git(
    manifest_dir: &Path,
    git_program: &OsStr,
) -> WorkspaceRootProbe {
    let Some(root) = layout_matched_workspace_root(manifest_dir) else {
        return WorkspaceRootProbe::LayoutMismatch;
    };
    let Some(reported_root) = command_output(
        git_command_with_program(&root, git_program).args(["rev-parse", "--show-toplevel"]),
    ) else {
        return WorkspaceRootProbe::GitUnavailable;
    };
    let Ok(canonical_reported) = PathBuf::from(reported_root).canonicalize() else {
        return WorkspaceRootProbe::LayoutMismatch;
    };
    if canonical_reported == root {
        WorkspaceRootProbe::GitMatched(root)
    } else {
        WorkspaceRootProbe::LayoutMismatch
    }
}

pub(crate) fn git_matched_workspace_root(manifest_dir: &Path) -> Option<PathBuf> {
    match workspace_root_probe(manifest_dir) {
        WorkspaceRootProbe::GitMatched(root) => Some(root),
        WorkspaceRootProbe::LayoutMismatch | WorkspaceRootProbe::GitUnavailable => None,
    }
}

pub(crate) fn git_rerun_paths(root: &Path) -> Vec<PathBuf> {
    let mut git_paths = vec![
        "HEAD".to_owned(),
        "packed-refs".to_owned(),
        "index".to_owned(),
    ];
    if let Some(symbolic_ref) =
        command_output(git_command(root).args(["symbolic-ref", "-q", "HEAD"]))
    {
        git_paths.push(symbolic_ref);
    }

    let mut paths = Vec::new();
    for git_path in git_paths {
        let Some(path) =
            command_output(git_command(root).args(["rev-parse", "--git-path", &git_path]))
        else {
            continue;
        };
        let path = PathBuf::from(path);
        let path = if path.is_absolute() {
            path
        } else {
            root.join(path)
        };
        if path.exists() {
            paths.push(path);
        } else if let Some(parent) = path.parent().filter(|parent| parent.exists()) {
            paths.push(parent.to_owned());
        }
    }
    paths.sort();
    paths.dedup();
    paths
}

fn probe_cargo_vcs_info(path: &Path) -> SourceProbe {
    let Ok(raw) = std::fs::read_to_string(path) else {
        return invalid_cargo_vcs_info();
    };
    let Ok(value) = serde_json::from_str::<CargoVcsInfo>(&raw) else {
        return invalid_cargo_vcs_info();
    };
    if value.path_in_vcs != EXPECTED_PATH_IN_VCS {
        return invalid_cargo_vcs_info();
    }
    if !is_sha1_hex(&value.git.sha1) {
        return invalid_cargo_vcs_info();
    }
    let working_tree = if value.git.dirty {
        WorkingTreeProbe::Dirty
    } else {
        WorkingTreeProbe::Clean
    };
    SourceProbe::CargoPackage {
        commit_sha1: value.git.sha1,
        working_tree,
    }
}

#[derive(Debug, Deserialize)]
struct CargoVcsInfo {
    git: CargoGit,
    path_in_vcs: String,
}

#[derive(Debug, Deserialize)]
struct CargoGit {
    sha1: String,
    #[serde(default)]
    dirty: bool,
}

fn invalid_cargo_vcs_info() -> SourceProbe {
    SourceProbe::Unavailable {
        reason: "invalid_cargo_vcs_info",
    }
}

fn git_command(root: &Path) -> Command {
    git_command_with_program(root, OsStr::new("git"))
}

fn git_command_with_program(root: &Path, program: &OsStr) -> Command {
    let mut command = Command::new(program);
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
    ] {
        command.env_remove(name);
    }
    // Indexed GIT_CONFIG_KEY_n / GIT_CONFIG_VALUE_n values are inert without COUNT, but removing
    // a bounded prefix makes the isolation explicit and protects against future Git behavior.
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

fn command_output(command: &mut Command) -> Option<String> {
    command
        .output()
        .ok()
        .filter(|output| output.status.success())
        .and_then(|output| String::from_utf8(output.stdout).ok())
        .map(|output| output.trim().to_owned())
        .filter(|output| !output.is_empty())
}

fn is_sha1_hex(value: &str) -> bool {
    value.len() == SHA1_HEX_LEN
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha1_validation_is_exact_and_lowercase() {
        assert!(is_sha1_hex("0123456789abcdef0123456789abcdef01234567"));
        assert!(!is_sha1_hex("0123456789ABCDEF0123456789ABCDEF01234567"));
        assert!(!is_sha1_hex("0123456789abcdef"));
    }

    #[test]
    fn working_tree_probe_combination_is_a_fail_closed_lattice() {
        use WorkingTreeProbe::{Clean, Dirty, Unknown};

        for (status, index, expected) in [
            (Clean, Clean, Clean),
            (Clean, Unknown, Unknown),
            (Unknown, Clean, Unknown),
            (Unknown, Unknown, Unknown),
            (Dirty, Clean, Dirty),
            (Clean, Dirty, Dirty),
            (Dirty, Unknown, Dirty),
            (Unknown, Dirty, Dirty),
            (Dirty, Dirty, Dirty),
        ] {
            assert_eq!(combine_working_tree_probes(status, index), expected);
        }
    }
}
