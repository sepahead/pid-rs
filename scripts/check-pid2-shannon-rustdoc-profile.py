#!/usr/bin/env python3
"""Check the two exact Rust documentation changes above the fixed PID2 source profile."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


PRODUCTION = "03325745f64becf437b9b3042b51a9d925450579"
PREVIOUS_PROFILE = "54b6c186aedacbba046cdd6ee81886d5ace43764"
INVARIANTS = "crates/pid-core/src/invariants.rs"
OLD_INVARIANTS = "00e57e312888783928ce967aa44b3d2769f4c39e3f4ae377b3cbd8c1f6b390d5"
NEW_INVARIANTS = "99cfbc6b26ae86964e305bdf7aa81f842220044f1c833fe9ad7e7df76fd86589"
CORPUS = "crates/pid-core/tests/fixtures/exact_binary64_sum_oracle.json"
PRODUCTION_FILES = (
    "Cargo.lock", "Cargo.toml", "crates/pid-core/Cargo.toml", "crates/pid-core/src/bin/exp0.rs",
    "crates/pid-core/src/exact_binary64.rs", INVARIANTS, "crates/pid-core/src/pid2.rs",
    CORPUS, CORPUS + ".sha256", "crates/pid-core/tests/fixtures/generate-exact-binary64-sum-oracle.py.snapshot",
    "crates/pid-core/tests/pid2.rs", "scripts/check-pid2-represented-coordinate-v4-self-test.py",
    "scripts/generate-exact-binary64-sum-oracle.py",
)
# SHA-256 of the previous checker's PINS, as sorted compact ASCII JSON.
PRODUCTION_MANIFEST = "0f1d56dc91ea8452b0ce413d0fc4949e6a6b8e33bdb7110140f262057fffe570"
FROZEN_CHECKERS = {
    "scripts/check-pid2-shannon-source-profile.py": "0c16e4da9c6a09278bfbda510f00169501a2c38d5ced1e803c511d29115a6935",
    "scripts/check-pid2-represented-coordinate-v4.py": "452a954ab7301d860ea7fdc63cffc5efaa2b39ea1f74c211fc0d8c10f95639cb",
}
PARAGRAPHS = (
    (
        b"/// - Exact mutual informations of one empirical distribution satisfy the Shannon inequalities.\n"
        b"///   Separately estimated or rounded inputs can violate them and can be signed. The report\n"
        b"///   evaluates the supplied numbers without testing their statistical coherence.\n",
        b"/// - On one empirical distribution each exact marginal MI lies between zero and the joint MI.\n"
        b"///   Rounding each exact value once to nearest preserves this order. Separate estimates or\n"
        b"///   numerical errors in their computation can violate it. The report accepts signed inputs.\n",
    ),
    (
        b"/// - On one empirical distribution, an exact leave-one-out mutual information cannot exceed\n"
        b"///   the joint mutual information. Separately estimated or rounded inputs can violate this\n"
        b"///   bound and can be signed. The report evaluates their differences without clamping them.\n",
        b"/// - On one empirical distribution each exact leave-one-out MI lies between zero and the joint\n"
        b"///   MI. Rounding each exact value once to nearest preserves this order. Separate estimates or\n"
        b"///   numerical errors in their computation can violate it. The report accepts signed inputs.\n",
    ),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", root, *args], timeout=20)


def blob(root, commit, path):
    return git(root, "cat-file", "blob", f"{commit}:{path}")


def regular(root, path):
    entry = root
    for part in Path(path).parts:
        entry /= part
        require(not entry.is_symlink(), f"symbolic link in {path}")
    require(entry.is_file(), f"missing regular file {path}")
    return entry.read_bytes()


def projection(root):
    git(root, "merge-base", "--is-ancestor", PRODUCTION, PREVIOUS_PROFILE)
    old = {p: blob(root, PRODUCTION, p) for p in PRODUCTION_FILES}
    hashes = {p: sha(data) for p, data in old.items()}
    encoded = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("ascii")
    require(sha(encoded) == PRODUCTION_MANIFEST, "original thirteen-file manifest differs")
    for path, data in old.items():
        require(blob(root, PREVIOUS_PROFILE, path) == data, f"previous profile differs: {path}")
    docs = old[INVARIANTS]
    require(sha(docs) == OLD_INVARIANTS, "original invariants source differs")
    for before, after in PARAGRAPHS:
        require(docs.count(before) == 1 and after not in docs, "rustdoc block is missing or duplicated")
        docs = docs.replace(before, after, 1)
    require(sha(docs) == NEW_INVARIANTS, "derived rustdoc source differs")
    expected = old | {INVARIANTS: docs}
    for path, digest in FROZEN_CHECKERS.items():
        data = blob(root, PREVIOUS_PROFILE, path)
        require(sha(data) == digest, f"historical observer differs: {path}")
        expected[path] = data
    return old, expected


def compare(expected, supplied, label):
    require(expected.keys() == supplied.keys(), f"{label} membership differs")
    for path, data in expected.items():
        require(supplied[path] == data, f"{label} differs: {path}")


def source(root):
    old, expected = projection(root)
    head = git(root, "rev-parse", "HEAD").decode("ascii").strip()
    require(head != PREVIOUS_PROFILE, "documentation profile requires a descendant of the previous profile")
    try:
        git(root, "merge-base", "--is-ancestor", PREVIOUS_PROFILE, head)
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 1:
            raise ValueError("documentation commit does not descend from the previous profile") from exc
        raise
    compare(expected, {p: blob(root, head, p) for p in expected}, "committed source")
    original_blob = "6fdbec6d1285b541d4c7584ddac73fa2d462ba27"
    revised_blob = "ae02058b5d172b691d74838d37357f30762d7f14"
    delta = git(root, "diff-tree", "--no-commit-id", "--no-abbrev", "--no-renames", "-r",
                "--raw", "-z", PREVIOUS_PROFILE, head, "--", *sorted(expected))
    expected_delta = f":100644 100644 {original_blob} {revised_blob} M\0{INVARIANTS}\0".encode("ascii")
    require(delta == expected_delta, "registered Git path or file mode differs")
    compare(expected, {p: regular(root, p) for p in expected}, "working source")
    return {
        "documentation_commit": head,
        "previous_profile": PREVIOUS_PROFILE,
        "native_production_commit": PRODUCTION,
        "original_thirteen_file_manifest_sha256": PRODUCTION_MANIFEST,
        "changed_production_files": sorted(p for p in old if old[p] != expected[p]),
        "registered_rustdoc_paragraphs": len(PARAGRAPHS),
        "original_invariants_sha256": OLD_INVARIANTS,
        "documented_invariants_sha256": NEW_INVARIANTS,
        "unchanged_observers_sha256": FROZEN_CHECKERS,
    }


def controls(root):
    old, expected = projection(root)
    compare(expected, expected.copy(), "control")
    restored = old[INVARIANTS]
    first_before, first_after = PARAGRAPHS[0]
    only_one = restored.replace(first_before, first_after, 1)
    actual = expected[INVARIANTS]
    changed_code = actual.replace(b"if denominator <= 0.0 {", b"if denominator < 0.0 {")
    require(changed_code != actual, "missing implementation control target")
    cases = {
        "original-source": (INVARIANTS, restored),
        "one-paragraph": (INVARIANTS, only_one),
        "unregistered-third-rustdoc": (INVARIANTS, actual + b"/// extra\n"),
        "changed-rust-expression": (INVARIANTS, changed_code),
        "changed-accumulator-file": ("crates/pid-core/src/exact_binary64.rs", b"changed\n"),
        "changed-pid2-file": ("crates/pid-core/src/pid2.rs", b"changed\n"),
        "changed-original-corpus": (CORPUS, b"{}\n"),
        "changed-native-observer": ("scripts/check-pid2-shannon-source-profile.py", b"changed\n"),
        "changed-revision-four-checker": ("scripts/check-pid2-represented-coordinate-v4.py", b"changed\n"),
    }
    rejected = {}
    for name, (path, altered) in cases.items():
        supplied = expected | {path: altered}
        rejected[name] = must_reject(expected, supplied, f"control differs: {path}")
    missing = dict(expected)
    del missing[CORPUS]
    rejected["omitted-file"] = must_reject(expected, missing, "control membership differs")
    extra = expected | {"unregistered.rs": b"// additional claimed input\n"}
    rejected["additional-claimed-file"] = must_reject(expected, extra, "control membership differs")
    return {"positive_projections": 1, "rejected": rejected}


def must_reject(expected, supplied, diagnostic):
    try:
        compare(expected, supplied, "control")
    except ValueError as exc:
        require(str(exc) == diagnostic, f"unexpected refusal: {exc}")
        return str(exc)
    raise ValueError(f"expected a refusal: {diagnostic}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("source", "controls"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.repo_root.resolve(strict=True)
    result = source(root) if args.operation == "source" else controls(root)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"PID2 rustdoc profile failed: {exc}") from exc
