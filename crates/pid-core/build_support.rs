use std::collections::BTreeSet;
use std::ffi::OsStr;
use std::io::{ErrorKind, Write as _};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use serde::{Deserialize, Deserializer};

const EXPECTED_PATH_IN_VCS: &str = "crates/pid-core";
const MINIMUM_GIT_MAJOR: u64 = 2;
const MINIMUM_GIT_MINOR: u64 = 45;
const SHA1_HEX_LEN: usize = 40;
const WORKSPACE_MARKERS: [&str; 4] = [
    ".gitattributes",
    "Cargo.toml",
    "method-catalog.json",
    "release-scope-1.0.json",
];

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

enum WorkspaceLayoutProbe {
    Matched(PathBuf),
    Mismatch,
    Unavailable,
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
    probe_source_identity_with_git(manifest_dir, OsStr::new("git"))
}

pub(crate) fn probe_source_identity_with_git(
    manifest_dir: &Path,
    git_program: &OsStr,
) -> SourceProbe {
    let root = match workspace_root_probe_with_git(manifest_dir, git_program) {
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
    let Some(commit_sha1) = command_output(git_command_with_program(&root, git_program).args([
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
    ])) else {
        return SourceProbe::Unavailable {
            reason: "git_unavailable",
        };
    };
    if !is_sha1_hex(&commit_sha1) {
        return SourceProbe::Unavailable {
            reason: "invalid_git_commit",
        };
    }

    let working_tree = if git_version_is_supported(&root, git_program) {
        probe_working_tree_with_git(&root, git_program)
    } else {
        WorkingTreeProbe::Unknown
    };
    let Some(final_commit_sha1) =
        command_output(git_command_with_program(&root, git_program).args([
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
        ]))
    else {
        return SourceProbe::Unavailable {
            reason: "git_unavailable",
        };
    };
    if !is_sha1_hex(&final_commit_sha1) {
        return SourceProbe::Unavailable {
            reason: "invalid_git_commit",
        };
    }
    if final_commit_sha1 != commit_sha1 {
        return SourceProbe::WorkspaceGit {
            commit_sha1: final_commit_sha1,
            working_tree: WorkingTreeProbe::Unknown,
        };
    }

    SourceProbe::WorkspaceGit {
        commit_sha1,
        working_tree,
    }
}

pub(crate) fn probe_working_tree_with_git(root: &Path, git_program: &OsStr) -> WorkingTreeProbe {
    probe_working_tree_with_git_after_first_status(root, git_program, || {})
}

fn probe_working_tree_with_git_after_first_status(
    root: &Path,
    git_program: &OsStr,
    after_first_status: impl FnOnce(),
) -> WorkingTreeProbe {
    if !working_tree_inputs_are_safe(root, git_program) {
        return WorkingTreeProbe::Unknown;
    }
    let first_status = probe_status_with_git(root, git_program);
    after_first_status();
    let index_probe = probe_index_visibility_with_git(root, git_program);
    let final_status = probe_status_with_git(root, git_program);
    if !working_tree_inputs_are_safe(root, git_program) {
        return WorkingTreeProbe::Unknown;
    }
    combine_working_tree_probes(
        combine_working_tree_probes(first_status, index_probe),
        final_status,
    )
}

#[cfg(test)]
pub(crate) fn probe_working_tree_with_git_after_first_status_for_test(
    root: &Path,
    git_program: &OsStr,
    after_first_status: impl FnOnce(),
) -> WorkingTreeProbe {
    probe_working_tree_with_git_after_first_status(root, git_program, after_first_status)
}

fn working_tree_inputs_are_safe(root: &Path, git_program: &OsStr) -> bool {
    repository_git_config_value_with_git(root, "attr.tree", git_program) == Some(None)
        && tracked_path_has_external_filter(root, git_program) == Some(false)
        && tracked_path_has_symlink_or_gitlink(root, git_program) == Some(false)
}

fn probe_status_with_git(root: &Path, git_program: &OsStr) -> WorkingTreeProbe {
    match git_command_with_program(root, git_program)
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
    }
}

fn probe_index_visibility_with_git(root: &Path, git_program: &OsStr) -> WorkingTreeProbe {
    match git_command_with_program(root, git_program)
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
    }
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

fn tracked_path_has_external_filter(root: &Path, git_program: &OsStr) -> Option<bool> {
    let tracked = git_command_with_program(root, git_program)
        .args(["ls-files", "-z", "--", EXPECTED_PATH_IN_VCS])
        .output()
        .ok()
        .filter(|output| output.status.success())?
        .stdout;
    if tracked.is_empty() {
        return Some(false);
    }

    let mut child = git_command_with_program(root, git_program)
        .args(["check-attr", "-z", "--stdin", "--all"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .ok()?;
    let mut stdin = child.stdin.take()?;
    let writer = std::thread::spawn(move || stdin.write_all(&tracked));
    let output = child.wait_with_output().ok()?;
    writer.join().ok()?.ok()?;
    if !output.status.success() {
        return None;
    }
    let mut fields = output.stdout.split(|byte| *byte == 0).collect::<Vec<_>>();
    if fields.last() == Some(&&[][..]) {
        fields.pop();
    }
    let (records, remainder) = fields.as_chunks::<3>();
    if !remainder.is_empty() {
        return None;
    }
    Some(records.iter().any(|record| record[1] == b"filter"))
}

fn tracked_path_has_symlink_or_gitlink(root: &Path, git_program: &OsStr) -> Option<bool> {
    let output = git_command_with_program(root, git_program)
        .args(["ls-files", "--stage", "-z", "--", EXPECTED_PATH_IN_VCS])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let mut has_external_entry = false;
    for record in output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|record| !record.is_empty())
    {
        let mode_end = record.iter().position(|byte| *byte == b' ')?;
        has_external_entry |= matches!(&record[..mode_end], b"120000" | b"160000");
    }
    Some(has_external_entry)
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

fn workspace_shape_root(manifest_dir: &Path) -> Option<PathBuf> {
    if manifest_dir.file_name().and_then(OsStr::to_str) != Some("pid-core") {
        return None;
    }
    let crates_dir = manifest_dir.parent()?;
    if crates_dir.file_name().and_then(OsStr::to_str) != Some("crates") {
        return None;
    }
    let root = crates_dir.parent()?;
    Some(root.to_owned())
}

fn probe_workspace_candidate(manifest_dir: &Path) -> WorkspaceLayoutProbe {
    let Some(root) = workspace_shape_root(manifest_dir) else {
        return WorkspaceLayoutProbe::Mismatch;
    };
    let Ok(canonical_root) = root.canonicalize() else {
        return WorkspaceLayoutProbe::Unavailable;
    };
    let Ok(canonical_manifest) = manifest_dir.canonicalize() else {
        return WorkspaceLayoutProbe::Unavailable;
    };
    let Ok(canonical_member) = canonical_root.join(EXPECTED_PATH_IN_VCS).canonicalize() else {
        return WorkspaceLayoutProbe::Unavailable;
    };
    if canonical_manifest == canonical_member && canonical_manifest.starts_with(&canonical_root) {
        WorkspaceLayoutProbe::Matched(canonical_root)
    } else {
        WorkspaceLayoutProbe::Mismatch
    }
}

#[cfg(test)]
pub(crate) fn workspace_candidate_root(manifest_dir: &Path) -> Option<PathBuf> {
    match probe_workspace_candidate(manifest_dir) {
        WorkspaceLayoutProbe::Matched(root) => Some(root),
        WorkspaceLayoutProbe::Mismatch | WorkspaceLayoutProbe::Unavailable => None,
    }
}

fn probe_workspace_structure(manifest_dir: &Path) -> WorkspaceLayoutProbe {
    let canonical_root = match probe_workspace_candidate(manifest_dir) {
        WorkspaceLayoutProbe::Matched(root) => root,
        WorkspaceLayoutProbe::Mismatch => return WorkspaceLayoutProbe::Mismatch,
        WorkspaceLayoutProbe::Unavailable => return WorkspaceLayoutProbe::Unavailable,
    };
    for marker in WORKSPACE_MARKERS {
        match std::fs::symlink_metadata(canonical_root.join(marker)) {
            Ok(metadata) if metadata.file_type().is_file() => {}
            Ok(_) => return WorkspaceLayoutProbe::Mismatch,
            Err(error) if error.kind() == ErrorKind::NotFound => {
                return WorkspaceLayoutProbe::Mismatch;
            }
            Err(_) => return WorkspaceLayoutProbe::Unavailable,
        }
    }
    WorkspaceLayoutProbe::Matched(canonical_root)
}

fn probe_workspace_layout(manifest_dir: &Path) -> WorkspaceLayoutProbe {
    let root = match probe_workspace_structure(manifest_dir) {
        WorkspaceLayoutProbe::Matched(root) => root,
        WorkspaceLayoutProbe::Mismatch => return WorkspaceLayoutProbe::Mismatch,
        WorkspaceLayoutProbe::Unavailable => return WorkspaceLayoutProbe::Unavailable,
    };
    match std::fs::symlink_metadata(root.join(".git")) {
        Ok(_) => WorkspaceLayoutProbe::Matched(root),
        Err(error) if error.kind() == ErrorKind::NotFound => WorkspaceLayoutProbe::Mismatch,
        Err(_) => WorkspaceLayoutProbe::Unavailable,
    }
}

pub(crate) fn layout_matched_workspace_root(manifest_dir: &Path) -> Option<PathBuf> {
    match probe_workspace_layout(manifest_dir) {
        WorkspaceLayoutProbe::Matched(root) => Some(root),
        WorkspaceLayoutProbe::Mismatch | WorkspaceLayoutProbe::Unavailable => None,
    }
}

#[cfg(test)]
pub(crate) fn workspace_root_probe(manifest_dir: &Path) -> WorkspaceRootProbe {
    workspace_root_probe_with_git(manifest_dir, OsStr::new("git"))
}

pub(crate) fn workspace_root_probe_with_git(
    manifest_dir: &Path,
    git_program: &OsStr,
) -> WorkspaceRootProbe {
    let root = match probe_workspace_layout(manifest_dir) {
        WorkspaceLayoutProbe::Matched(root) => root,
        WorkspaceLayoutProbe::Mismatch => return WorkspaceRootProbe::LayoutMismatch,
        WorkspaceLayoutProbe::Unavailable => return WorkspaceRootProbe::GitUnavailable,
    };
    let Some(reported_root) = command_output(
        git_command_with_program(&root, git_program).args(["rev-parse", "--show-toplevel"]),
    ) else {
        return WorkspaceRootProbe::GitUnavailable;
    };
    let Ok(canonical_reported) = PathBuf::from(reported_root).canonicalize() else {
        return WorkspaceRootProbe::GitUnavailable;
    };
    if canonical_reported == root {
        WorkspaceRootProbe::GitMatched(root)
    } else {
        WorkspaceRootProbe::GitUnavailable
    }
}

#[cfg(all(test, unix))]
pub(crate) fn git_matched_workspace_root(manifest_dir: &Path) -> Option<PathBuf> {
    match workspace_root_probe(manifest_dir) {
        WorkspaceRootProbe::GitMatched(root) => Some(root),
        WorkspaceRootProbe::LayoutMismatch | WorkspaceRootProbe::GitUnavailable => None,
    }
}

pub(crate) fn workspace_rerun_paths(manifest_dir: &Path) -> Vec<PathBuf> {
    let Some(shape_root) = workspace_shape_root(manifest_dir) else {
        return Vec::new();
    };
    let root = match probe_workspace_candidate(manifest_dir) {
        WorkspaceLayoutProbe::Matched(root) => root,
        WorkspaceLayoutProbe::Mismatch | WorkspaceLayoutProbe::Unavailable => shape_root,
    };
    let mut paths = WORKSPACE_MARKERS
        .into_iter()
        .map(|marker| root.join(marker))
        .collect::<BTreeSet<_>>();
    paths.insert(root.join("crates"));
    paths.extend(git_rerun_paths(&root));
    paths.into_iter().collect()
}

pub(crate) fn workspace_rerun_paths_for_source(
    manifest_dir: &Path,
    source: &SourceProbe,
) -> Vec<PathBuf> {
    let mut paths = workspace_rerun_paths(manifest_dir)
        .into_iter()
        .collect::<BTreeSet<_>>();
    let source_is_complete = matches!(
        source,
        SourceProbe::WorkspaceGit {
            working_tree: WorkingTreeProbe::Clean | WorkingTreeProbe::Dirty,
            ..
        }
    );
    if !source_is_complete {
        let root = match probe_workspace_candidate(manifest_dir) {
            WorkspaceLayoutProbe::Matched(root) => Some(root),
            WorkspaceLayoutProbe::Mismatch | WorkspaceLayoutProbe::Unavailable => {
                workspace_shape_root(manifest_dir)
            }
        };
        if let Some(root) = root {
            add_absent_rerun_sentinel(&mut paths, &root);
        }
    }
    paths.into_iter().collect()
}

pub(crate) fn git_rerun_paths(root: &Path) -> Vec<PathBuf> {
    let mut paths = BTreeSet::new();
    let git_entry = root.join(".git");
    let mut force_rerun = match std::fs::symlink_metadata(&git_entry) {
        Ok(metadata) if !metadata.file_type().is_dir() => {
            paths.insert(git_entry);
            !metadata.file_type().is_file()
        }
        Ok(_) => false,
        Err(_) => {
            paths.insert(git_entry);
            true
        }
    };

    if !git_route_matches_root(root) {
        add_absent_rerun_sentinel(&mut paths, root);
        return paths.into_iter().collect();
    }
    if !git_version_is_supported(root, OsStr::new("git")) {
        add_absent_rerun_sentinel(&mut paths, root);
        return paths.into_iter().collect();
    }

    force_rerun |= !git_identity_probe_is_complete(root);

    for required in ["HEAD", "index", "config"] {
        match resolved_git_path(root, required) {
            Some(path) => add_required_file(&mut paths, path, &mut force_rerun),
            None => force_rerun = true,
        }
    }
    match resolved_git_path(root, "info") {
        Some(path) => add_required_directory(&mut paths, path, &mut force_rerun),
        None => force_rerun = true,
    }
    match resolved_git_path(root, "objects/info") {
        Some(path) => add_required_directory(&mut paths, path, &mut force_rerun),
        None => force_rerun = true,
    }
    for optional in ["commondir", "packed-refs", "config.worktree"] {
        if let Some(path) = resolved_git_path(root, optional) {
            add_existing_file(&mut paths, path, &mut force_rerun);
        }
    }

    if command_output(git_command(root).args([
        "config",
        "--type=bool",
        "--get",
        "extensions.worktreeConfig",
    ]))
    .as_deref()
        == Some("true")
    {
        match resolved_git_path(root, "config.worktree") {
            Some(path) => add_required_file(&mut paths, path, &mut force_rerun),
            None => force_rerun = true,
        }
    }

    if let Some(shared_index) =
        command_output(git_command(root).args(["rev-parse", "--shared-index-path"]))
    {
        let path = resolve_git_output_path(root, &shared_index);
        add_required_file(&mut paths, path, &mut force_rerun);
    }

    match git_config_origins(root) {
        Some((origins, has_include_directive)) => {
            for origin in origins {
                add_required_file(&mut paths, origin, &mut force_rerun);
            }
            force_rerun |= has_include_directive;
        }
        None => force_rerun = true,
    }

    match git_ref_format(root) {
        Some("files") => add_files_reference_watches(root, &mut paths, &mut force_rerun),
        Some("reftable") => add_reftable_watches(root, &mut paths, &mut force_rerun),
        _ => force_rerun = true,
    }

    if force_rerun {
        add_absent_rerun_sentinel(&mut paths, root);
    }
    paths.into_iter().collect()
}

fn git_route_matches_root(root: &Path) -> bool {
    let Some(reported) = command_output(git_command(root).args(["rev-parse", "--show-toplevel"]))
    else {
        return false;
    };
    let (Ok(expected), Ok(observed)) =
        (root.canonicalize(), PathBuf::from(reported).canonicalize())
    else {
        return false;
    };
    expected == observed
}

fn git_version_is_supported(root: &Path, git_program: &OsStr) -> bool {
    command_output(git_command_with_program(root, git_program).arg("--version"))
        .and_then(|version| parse_git_version(&version))
        .is_some_and(|(major, minor)| {
            major > MINIMUM_GIT_MAJOR || (major == MINIMUM_GIT_MAJOR && minor >= MINIMUM_GIT_MINOR)
        })
}

fn parse_git_version(value: &str) -> Option<(u64, u64)> {
    let version = value
        .strip_prefix("git version ")?
        .split_whitespace()
        .next()?;
    let mut components = version.split('.');
    let major = components.next()?.parse().ok()?;
    let minor = components.next()?.parse().ok()?;
    Some((major, minor))
}

fn git_identity_probe_is_complete(root: &Path) -> bool {
    command_output(git_command(root).args(["rev-parse", "--verify", "HEAD^{commit}"]))
        .is_some_and(|commit| is_sha1_hex(&commit))
        && probe_working_tree_with_git(root, OsStr::new("git")) != WorkingTreeProbe::Unknown
}

fn add_absent_rerun_sentinel(paths: &mut BTreeSet<PathBuf>, root: &Path) {
    let name = absent_rerun_sentinel_name(root, ".pid-rs-source-identity-route-unavailable");
    paths.insert(root.join(name));
}

pub(crate) fn absent_rerun_sentinel_name(root: &Path, prefix: &str) -> String {
    for suffix in 0_u64.. {
        let name = if suffix == 0 {
            prefix.to_owned()
        } else {
            format!("{prefix}-{suffix}")
        };
        let candidate = root.join(name);
        match std::fs::symlink_metadata(&candidate) {
            Err(error) if error.kind() == ErrorKind::NotFound => {
                return candidate
                    .file_name()
                    .and_then(OsStr::to_str)
                    .expect("ASCII sentinel name must remain representable")
                    .to_owned();
            }
            Ok(_) => {}
            Err(_) => {
                return candidate
                    .file_name()
                    .and_then(OsStr::to_str)
                    .expect("ASCII sentinel name must remain representable")
                    .to_owned();
            }
        }
    }
    unreachable!("the finite filesystem cannot contain every u64-suffixed sentinel")
}

pub(crate) fn cargo_rerun_path(path: &Path) -> Option<&str> {
    path.to_str().filter(|path| !path.contains(['\r', '\n']))
}

fn resolve_git_output_path(root: &Path, value: &str) -> PathBuf {
    let path = PathBuf::from(value);
    if path.is_absolute() {
        path
    } else {
        root.join(path)
    }
}

fn resolved_git_path(root: &Path, name: &str) -> Option<PathBuf> {
    command_output(git_command(root).args(["rev-parse", "--git-path", name]))
        .map(|path| resolve_git_output_path(root, &path))
}

fn add_required_file(paths: &mut BTreeSet<PathBuf>, path: PathBuf, force_rerun: &mut bool) {
    match std::fs::symlink_metadata(&path) {
        Ok(metadata) if metadata.file_type().is_file() => {
            paths.insert(path);
        }
        Ok(_) => *force_rerun = true,
        Err(error) if error.kind() == ErrorKind::NotFound => {
            paths.insert(path);
        }
        Err(_) => *force_rerun = true,
    }
}

fn add_existing_file(paths: &mut BTreeSet<PathBuf>, path: PathBuf, force_rerun: &mut bool) {
    match std::fs::symlink_metadata(&path) {
        Ok(metadata) if metadata.file_type().is_file() => {
            paths.insert(path);
        }
        Ok(_) => *force_rerun = true,
        Err(error) if error.kind() == ErrorKind::NotFound => {}
        Err(_) => *force_rerun = true,
    }
}

fn add_required_directory(paths: &mut BTreeSet<PathBuf>, path: PathBuf, force_rerun: &mut bool) {
    match std::fs::symlink_metadata(&path) {
        Ok(metadata) if metadata.file_type().is_dir() => {
            paths.insert(path);
        }
        Ok(_) => *force_rerun = true,
        Err(error) if error.kind() == ErrorKind::NotFound => {
            paths.insert(path);
        }
        Err(_) => *force_rerun = true,
    }
}

fn git_config_origins(root: &Path) -> Option<(Vec<PathBuf>, bool)> {
    let output = git_command(root)
        .args(["config", "--includes", "--show-origin", "--null", "--list"])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let fields = output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|field| !field.is_empty())
        .collect::<Vec<_>>();
    let (records, remainder) = fields.as_chunks::<2>();
    if !remainder.is_empty() {
        return None;
    }

    let mut origins = BTreeSet::new();
    let mut has_include_directive = false;
    for record in records {
        let origin = std::str::from_utf8(record[0]).ok()?;
        let setting = std::str::from_utf8(record[1]).ok()?;
        if let Some(path) = origin.strip_prefix("file:") {
            origins.insert(resolve_git_output_path(root, path));
        }
        let key = setting.split_once('\n').map_or(setting, |(key, _)| key);
        let key = key.to_ascii_lowercase();
        if key == "include.path" || (key.starts_with("includeif.") && key.ends_with(".path")) {
            has_include_directive = true;
        }
    }
    Some((origins.into_iter().collect(), has_include_directive))
}

fn git_ref_format(root: &Path) -> Option<&'static str> {
    let output = git_command(root)
        .args(["rev-parse", "--show-ref-format"])
        .output()
        .ok()?;
    let reported = if output.status.success() {
        let value = String::from_utf8(output.stdout).ok()?;
        match strip_git_record_terminator(&value) {
            "files" => Some("files"),
            "reftable" => Some("reftable"),
            // Older Git releases can treat the unknown option as an argument and echo it.
            "--show-ref-format" => None,
            _ => return None,
        }
    } else {
        None
    };

    let configured = local_git_config_value(root, "extensions.refStorage")?;
    select_ref_format(reported, configured.as_deref())
}

fn select_ref_format(reported: Option<&str>, configured: Option<&str>) -> Option<&'static str> {
    match (reported, configured) {
        (Some("files"), None | Some("files")) | (None, None | Some("files")) => Some("files"),
        (Some("reftable"), Some("reftable")) | (None, Some("reftable")) => Some("reftable"),
        _ => None,
    }
}

fn local_git_config_value(root: &Path, key: &str) -> Option<Option<String>> {
    let output = git_command(root)
        .args(["config", "--local", "--get", key])
        .output()
        .ok()?;
    if output.status.success() {
        let value = String::from_utf8(output.stdout).ok()?;
        let value = strip_git_record_terminator(&value).to_owned();
        return (!value.is_empty()).then_some(Some(value));
    }
    (output.status.code() == Some(1) && output.stdout.is_empty()).then_some(None)
}

fn repository_git_config_value_with_git(
    root: &Path,
    key: &str,
    git_program: &OsStr,
) -> Option<Option<String>> {
    let output = git_command_with_program(root, git_program)
        .args(["config", "--includes", "--get", key])
        .output()
        .ok()?;
    if output.status.success() {
        let value = String::from_utf8(output.stdout).ok()?;
        let value = strip_git_record_terminator(&value).to_owned();
        return (!value.is_empty()).then_some(Some(value));
    }
    (output.status.code() == Some(1) && output.stdout.is_empty()).then_some(None)
}

fn add_files_reference_watches(root: &Path, paths: &mut BTreeSet<PathBuf>, force_rerun: &mut bool) {
    if let Some(path) = resolved_git_path(root, "packed-refs") {
        add_existing_file(paths, path, force_rerun);
    }
    let Some(refs_root) = resolved_git_path(root, "refs") else {
        *force_rerun = true;
        return;
    };

    let mut current = "HEAD".to_owned();
    let mut seen = BTreeSet::new();
    for _ in 0..32 {
        let next = match symbolic_ref_target(root, &current) {
            SymbolicRefTarget::Target(next) => next,
            SymbolicRefTarget::Direct => return,
            SymbolicRefTarget::Unknown => {
                *force_rerun = true;
                return;
            }
        };
        if !seen.insert(next.clone()) {
            *force_rerun = true;
            return;
        }
        let Some(path) = resolved_git_path(root, &next) else {
            *force_rerun = true;
            return;
        };
        match std::fs::symlink_metadata(&path) {
            Ok(metadata) if metadata.file_type().is_file() => {
                paths.insert(path);
            }
            Ok(_) => {
                *force_rerun = true;
                return;
            }
            Err(error) if error.kind() == ErrorKind::NotFound => {
                let resolves = command_output(git_command(root).args([
                    "rev-parse",
                    "--verify",
                    &format!("{next}^{{commit}}"),
                ]))
                .is_some();
                if resolves {
                    if !add_nearest_ref_namespace(paths, &path, &refs_root) {
                        *force_rerun = true;
                    }
                } else {
                    paths.insert(path);
                }
                return;
            }
            Err(_) => {
                *force_rerun = true;
                return;
            }
        }
        current = next;
    }
    *force_rerun = true;
}

#[derive(Debug, PartialEq, Eq)]
enum SymbolicRefTarget {
    Target(String),
    Direct,
    Unknown,
}

fn symbolic_ref_target(root: &Path, name: &str) -> SymbolicRefTarget {
    let Ok(output) = git_command(root)
        .args(["symbolic-ref", "-q", "--no-recurse", name])
        .output()
    else {
        return SymbolicRefTarget::Unknown;
    };
    classify_symbolic_ref_output(
        output.status.success(),
        output.status.code(),
        &output.stdout,
        &output.stderr,
    )
}

fn classify_symbolic_ref_output(
    success: bool,
    status_code: Option<i32>,
    stdout: &[u8],
    stderr: &[u8],
) -> SymbolicRefTarget {
    if success {
        let Ok(value) = std::str::from_utf8(stdout) else {
            return SymbolicRefTarget::Unknown;
        };
        let value = strip_git_record_terminator(value);
        return if value.is_empty() {
            SymbolicRefTarget::Unknown
        } else {
            SymbolicRefTarget::Target(value.to_owned())
        };
    }
    if status_code == Some(1) && stdout.is_empty() && stderr.is_empty() {
        SymbolicRefTarget::Direct
    } else {
        SymbolicRefTarget::Unknown
    }
}

fn add_nearest_ref_namespace(
    paths: &mut BTreeSet<PathBuf>,
    ref_path: &Path,
    refs_root: &Path,
) -> bool {
    let mut candidate = ref_path.parent();
    while let Some(parent) = candidate {
        if !parent.starts_with(refs_root) {
            return false;
        }
        if std::fs::symlink_metadata(parent).is_ok_and(|metadata| metadata.file_type().is_dir()) {
            paths.insert(parent.to_owned());
            return true;
        }
        if parent == refs_root {
            return false;
        }
        candidate = parent.parent();
    }
    false
}

fn add_reftable_watches(root: &Path, paths: &mut BTreeSet<PathBuf>, force_rerun: &mut bool) {
    match resolved_git_path(root, "reftable/tables.list") {
        Some(path) => add_required_file(paths, path, force_rerun),
        None => *force_rerun = true,
    }
    let Some(common_dir) =
        command_output(git_command(root).args(["rev-parse", "--git-common-dir"]))
            .map(|path| resolve_git_output_path(root, &path))
    else {
        *force_rerun = true;
        return;
    };
    add_required_file(paths, common_dir.join("reftable/tables.list"), force_rerun);
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
    let working_tree = match value.git.dirty {
        Some(true) => WorkingTreeProbe::Dirty,
        Some(false) => WorkingTreeProbe::Clean,
        None => WorkingTreeProbe::Unknown,
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
    #[serde(default, deserialize_with = "deserialize_present_bool")]
    dirty: Option<bool>,
}

fn deserialize_present_bool<'de, D>(deserializer: D) -> Result<Option<bool>, D::Error>
where
    D: Deserializer<'de>,
{
    bool::deserialize(deserializer).map(Some)
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

fn command_output(command: &mut Command) -> Option<String> {
    command
        .output()
        .ok()
        .filter(|output| output.status.success())
        .and_then(|output| String::from_utf8(output.stdout).ok())
        .map(|output| strip_git_record_terminator(&output).to_owned())
        .filter(|output| !output.is_empty())
}

fn strip_git_record_terminator(value: &str) -> &str {
    value
        .strip_suffix("\r\n")
        .or_else(|| value.strip_suffix('\n'))
        .unwrap_or(value)
}

pub(crate) fn write_if_changed(path: &Path, contents: &[u8]) -> std::io::Result<bool> {
    match std::fs::read(path) {
        Ok(existing) if existing == contents => Ok(false),
        Ok(_) => {
            std::fs::write(path, contents)?;
            Ok(true)
        }
        Err(error) if error.kind() == ErrorKind::NotFound => {
            std::fs::write(path, contents)?;
            Ok(true)
        }
        Err(error) => Err(error),
    }
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
    fn git_record_terminator_preserves_path_characters() {
        assert_eq!(
            strip_git_record_terminator("path with space \n"),
            "path with space "
        );
        assert_eq!(
            strip_git_record_terminator("path with newline\n\n"),
            "path with newline\n"
        );
        assert_eq!(
            strip_git_record_terminator("path without terminator"),
            "path without terminator"
        );
    }

    #[test]
    fn symbolic_ref_classification_distinguishes_detached_from_failures() {
        assert_eq!(
            classify_symbolic_ref_output(true, Some(0), b"refs/heads/main\n", b""),
            SymbolicRefTarget::Target("refs/heads/main".to_owned())
        );
        assert_eq!(
            classify_symbolic_ref_output(false, Some(1), b"", b""),
            SymbolicRefTarget::Direct
        );
        assert_eq!(
            classify_symbolic_ref_output(false, Some(129), b"", b"unknown option"),
            SymbolicRefTarget::Unknown
        );
        assert_eq!(
            classify_symbolic_ref_output(true, Some(0), b"refs/heads/\xff\n", b""),
            SymbolicRefTarget::Unknown
        );
    }

    #[test]
    fn cargo_rerun_paths_reject_line_delimiters() {
        assert_eq!(
            cargo_rerun_path(Path::new("ordinary/path")),
            Some("ordinary/path")
        );
        assert_eq!(cargo_rerun_path(Path::new("line\nbreak")), None);
        assert_eq!(cargo_rerun_path(Path::new("carriage\rreturn")), None);
    }

    #[test]
    fn git_version_gate_is_explicit_and_future_compatible() {
        assert_eq!(parse_git_version("git version 2.44.9"), Some((2, 44)));
        assert_eq!(
            parse_git_version("git version 2.45.0.windows.1"),
            Some((2, 45))
        );
        assert_eq!(
            parse_git_version("git version 2.50.1 (Apple Git-155)"),
            Some((2, 50))
        );
        assert_eq!(parse_git_version("git version 3.0.0"), Some((3, 0)));
        assert_eq!(parse_git_version("unexpected"), None);
    }

    #[test]
    fn legacy_ref_format_fallback_is_closed_over_known_backends() {
        assert_eq!(select_ref_format(None, None), Some("files"));
        assert_eq!(select_ref_format(None, Some("files")), Some("files"));
        assert_eq!(select_ref_format(None, Some("reftable")), Some("reftable"));
        assert_eq!(select_ref_format(Some("files"), None), Some("files"));
        assert_eq!(
            select_ref_format(Some("reftable"), Some("reftable")),
            Some("reftable")
        );
        assert_eq!(select_ref_format(Some("files"), Some("reftable")), None);
        assert_eq!(
            select_ref_format(Some("files"), Some("files:///external")),
            None
        );
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

    #[test]
    fn git_command_isolates_routing_replacements_config_and_attributes() {
        let command = git_command(Path::new("."));
        let env_value = |name: &str| {
            command
                .get_envs()
                .find(|(key, _)| *key == OsStr::new(name))
                .map(|(_, value)| value)
        };
        for removed in [
            "GIT_ATTR_SOURCE",
            "GIT_CONFIG",
            "GIT_DIR",
            "GIT_REFERENCE_BACKEND",
            "GIT_REPLACE_REF_BASE",
            "GIT_SHALLOW_FILE",
            "GIT_WORK_TREE",
        ] {
            assert_eq!(env_value(removed), Some(None), "{removed} was not removed");
        }
        for (name, expected) in [
            ("GIT_ATTR_NOSYSTEM", "1"),
            ("GIT_NO_REPLACE_OBJECTS", "1"),
            ("GIT_LITERAL_PATHSPECS", "1"),
            ("GIT_TERMINAL_PROMPT", "0"),
        ] {
            assert_eq!(
                env_value(name),
                Some(Some(OsStr::new(expected))),
                "{name} was not pinned"
            );
        }
        let null_device = if cfg!(windows) { "NUL" } else { "/dev/null" };
        assert!(command
            .get_args()
            .any(|argument| argument == OsStr::new(&format!("core.attributesFile={null_device}"))));
    }
}
