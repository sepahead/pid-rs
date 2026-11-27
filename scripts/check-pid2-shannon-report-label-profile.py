#!/usr/bin/env python3
"""Check five exact rustdoc changes above the qualified two-paragraph source profile."""

import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess
from types import ModuleType


PREDECESSOR = "9411667f972af0547d391a0be6d95b011b515171"
EARLIER_CHECKER = "scripts/check-pid2-shannon-rustdoc-profile.py"
EARLIER_CHECKER_SHA256 = "7200b92c6773b0be1a5bac530c4d13eff7f62aaf961ea43cbb525cb9d9eaeb5a"
DOCUMENTATION_EDITS = (
    (
        "source-only-identity",
        (
            "//! **PROJECT-DEFINED ANALOGUES.** `red_degree_discrete` and `vul_degree_discrete` are target-free\n"
            "//! entropy-ratio screening summaries inspired by those invariants. They are not the published\n"
            "//! target-based quantities and have no dedicated paper claim.\n"
        ).encode("utf-8"),
        (
            "//! **PROJECT-DEFINED ANALOGUES.** `red_degree_discrete` and `vul_degree_discrete` take only\n"
            "//! categorical source columns. For a finite source tuple `S` with `H(S) > 0`, choosing\n"
            "//! `T = S` in the published target-based degrees gives `I(T;S_i) = H(S_i)` and `I(T;S) = H(S)`.\n"
            "//! Removing source `i` then loses `H(S) - H(S_-i)`. The exact degrees for this target equal\n"
            "//! the two source-only entropy ratios. A separately specified target can give different values.\n"
            "//! These APIs directly estimate empirical entropies and reject zero joint entropy.\n"
        ).encode("utf-8"),
    ),
    (
        "threshold-and-sampling",
        (
            "//! For the target-based report policy, convergence guarantees eventual `Defined` status when the\n"
            "//! population denominator is strictly larger than the policy threshold. Equality at the threshold\n"
            "//! gives no eventual status guarantee. The argument does not prove binary64 asymptotics,\n"
            "//! dependent-window validity, or a new Shannon quantity. The method catalog records this evidence\n"
            "//! under `validation.finite-alphabet-plugin-convergence`.\n"
        ).encode("utf-8"),
        (
            "//! For the exact-real threshold rule, a limit strictly above the floor eventually passes.\n"
            "//! Equality alone gives no eventual status guarantee. The Rust policy compares the supplied\n"
            "//! binary64 denominator. For example, let `c` be the default floor and choose a binary source\n"
            "//! whose entropy lies strictly between `c` and the midpoint to the next larger binary64 value.\n"
            "//! With a copy of the source as target, empirical mutual information converging to this entropy\n"
            "//! eventually exceeds `c` in exact arithmetic but rounds to `c` on a single nearest rounding.\n"
            "//! The Rust report then returns `DenominatorBelowPolicyThreshold`.\n"
            "//! On a fixed finite alphabet, cumulative prefix frequencies converge almost surely for i.i.d.\n"
            "//! rows or strictly stationary ergodic rows with the specified one-time marginal distribution.\n"
            "//! The ergodic result supplies no generic finite-sample rate or moving-window guarantee.\n"
            "//! Binary64 estimator convergence requires separate evidence. See the method catalog entry\n"
            "//! `validation.finite-alphabet-plugin-convergence`.\n"
        ).encode("utf-8"),
    ),
    (
        "source-only-redundancy",
        (
            "/// Degree of Redundancy (Red°), computed on discrete variables — a **target-free\n"
            "/// entropy-ratio analogue** of the degree-of-redundancy invariant of Gutknecht et al.\n"
            "/// (2025) (their `r̄` is stated in the MI-to-a-target form; this applies the same\n"
            "/// Shannon-invariants framework to the joint entropy, with no target `Y`):\n"
        ).encode("utf-8"),
        (
            "/// Target-free degree of redundancy (Red°) from categorical source columns.\n"
            "/// With positive joint entropy, its exact formula equals Gutknecht et al.'s average degree\n"
            "/// of redundancy when the target is a copy of the full source tuple.\n"
        ).encode("utf-8"),
    ),
    (
        "source-only-vulnerability",
        (
            "/// Degree of Vulnerability (Vul°), computed on discrete variables — a **target-free\n"
            "/// entropy-ratio analogue** of the degree-of-vulnerability invariant of Gutknecht et al.\n"
            "/// (2025) (their `v̄` is stated in the MI-to-a-target form; this applies the same\n"
            "/// Shannon-invariants framework to the joint entropy, with no target `Y`):\n"
        ).encode("utf-8"),
        (
            "/// Target-free degree of vulnerability (Vul°) from categorical source columns.\n"
            "/// With positive joint entropy, its exact formula equals Gutknecht et al.'s average degree\n"
            "/// of vulnerability when the target is a copy of the full source tuple.\n"
        ).encode("utf-8"),
    ),
    (
        "report-label",
        (
            "/// Typed result for a normalized Shannon-invariant analogue.\n"
        ).encode("utf-8"),
        (
            "/// Typed result for a target-based average degree of redundancy or vulnerability.\n"
        ).encode("utf-8"),
    ),
)
SOURCE = "crates/pid-core/src/invariants.rs"
OLD_SHA256 = "99cfbc6b26ae86964e305bdf7aa81f842220044f1c833fe9ad7e7df76fd86589"
NEW_SHA256 = "4d5dbd90163a9f219236eaed74e2346fd1629c5d7f45c64454c9102cf4b0f21b"
OLD_BLOB = "ae02058b5d172b691d74838d37357f30762d7f14"
NEW_BLOB = "348c591d7d4d89e92b3d8108f3d504a656976f0d"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", root, *arguments], timeout=20)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def predecessor(root):
    raw = git(root, "cat-file", "blob", f"{PREDECESSOR}:{EARLIER_CHECKER}")
    require(sha(raw) == EARLIER_CHECKER_SHA256, "predecessor checker digest differs")
    module = ModuleType("recorded_pid2_rustdoc_profile")
    module.__file__ = str(root / EARLIER_CHECKER)
    exec(compile(raw, EARLIER_CHECKER, "exec", dont_inherit=True), module.__dict__)
    return module, raw


def expectation(root):
    previous, checker = predecessor(root)
    _, prior = previous.projection(root)
    prior[EARLIER_CHECKER] = checker
    previous.compare(prior, {p: previous.blob(root, PREDECESSOR, p) for p in prior},
                     "immutable documentation predecessor")
    before = prior[SOURCE]
    require(sha(before) == OLD_SHA256, "predecessor invariants source differs")
    after = before
    for name, old_doc, new_doc in DOCUMENTATION_EDITS:
        require(all(row.startswith((b"///", b"//!")) for row in (old_doc + new_doc).splitlines()),
                f"non-documentation row in {name}")
        require(after.count(old_doc) == 1 and new_doc not in after,
                f"missing or duplicated documentation anchor: {name}")
        after = after.replace(old_doc, new_doc, 1)
    require(sha(after) == NEW_SHA256, "derived report-label source differs")
    return previous, prior, prior | {SOURCE: after}


def source(root):
    previous, _, expected = expectation(root)
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    require(head != PREDECESSOR, "report-label profile requires a descendant")
    git(root, "merge-base", "--is-ancestor", PREDECESSOR, head)
    paths = sorted(expected)
    previous.compare(expected, {p: previous.blob(root, head, p) for p in paths}, "committed source")
    delta = git(root, "diff-tree", "--no-commit-id", "--no-abbrev", "--no-renames", "-r",
                "--raw", "-z", PREDECESSOR, head, "--", *paths)
    wanted = f":100644 100644 {OLD_BLOB} {NEW_BLOB} M\0{SOURCE}\0".encode("ascii")
    require(delta == wanted, "committed report-label path, mode or blob differs")
    previous.compare(expected, {p: previous.regular(root, p) for p in paths}, "working source")
    tree = git(root, "ls-tree", "-rz", "--full-tree", head, "--", *paths)
    for row in tree.rstrip(b"\0").split(b"\0"):
        meta, path = row.split(b"\t", 1)
        mode = meta.split(b" ", 1)[0]
        file_mode = (root / path.decode("ascii")).stat().st_mode
        require(stat.S_ISREG(file_mode) and mode in (b"100644", b"100755")
                and bool(file_mode & 0o111) == (mode == b"100755"),
                f"working file mode differs: {path!r}")
    return {"documentation_commit": head, "predecessor": PREDECESSOR,
            "production_commit": previous.PRODUCTION, "protected_files": paths,
            "predecessor_checker_sha256": EARLIER_CHECKER_SHA256,
            "old_invariants_sha256": OLD_SHA256, "new_invariants_sha256": NEW_SHA256,
            "registered_rustdoc_regions": [entry[0] for entry in DOCUMENTATION_EDITS]}


def controls(root):
    previous, prior, expected = expectation(root)
    previous.compare(expected, expected.copy(), "fixture")
    changed_expression = expected[SOURCE].replace(b"if denominator <= 0.0 {", b"if denominator < 0.0 {")
    require(changed_expression != expected[SOURCE], "missing code-expression control anchor")
    tests = {
        "predecessor": prior,
        "duplicate-label": expected | {SOURCE: expected[SOURCE] + DOCUMENTATION_EDITS[-1][2]},
        "changed-operation": expected | {SOURCE: changed_expression},
        "changed-pid2": expected | {"crates/pid-core/src/pid2.rs": b"altered"},
        "changed-exact-sum": expected | {"crates/pid-core/src/exact_binary64.rs": b"altered"},
        "changed-earlier-checker": expected | {EARLIER_CHECKER: b"altered"},
        "missing-earlier-checker": {p: v for p, v in expected.items() if p != EARLIER_CHECKER},
        "extra-file": expected | {"unexpected": b"extra"},
    }
    for name, old_doc, new_doc in DOCUMENTATION_EDITS:
        reverted = expected[SOURCE].replace(new_doc, old_doc, 1)
        require(reverted != expected[SOURCE], f"missing control anchor: {name}")
        tests["omitted-" + name] = expected | {SOURCE: reverted}
    refused = {}
    for name, sample in tests.items():
        try:
            previous.compare(expected, sample, "fixture")
        except ValueError as error:
            missing = expected.keys() != sample.keys()
            path = next((p for p in expected if p in sample and expected[p] != sample[p]), None)
            diagnostic = "fixture membership differs" if missing else f"fixture differs: {path}"
            require(str(error) == diagnostic, f"wrong refusal for {name}")
            refused[name] = str(error)
        else:
            raise ValueError(f"mutation accepted: {name}")
    return {"accepted": 1, "refused": refused}



# The report-label profile has its own historical commit. The later CLI correction
# changes two held source files. The numeric checker changes only their two digests.
REPORT_LABEL = "570c9c67800affde745032cd9d7296f29839f2ba"
CORRECTED_INPUTS = "77f93cfd5a93d613c09357c23bb488769d8bfc32"
CURRENT_SOURCES = {'crates/pid-core/src/pid2.rs': ('f8cce5ece132a54df30a19f3b867c1296b5325e725408f628143c619ac814146', '8c330ac9d2b4d74dd6938924088fd1cfeb64f958c714e279a3232ae53597aa20'), 'crates/pid-core/src/bin/exp0.rs': ('c2a28c24442f850fa033a8f89ae889ae22c818efddfccbaff75e8b026164924e', '1d6e7d9731b0b33cd3e9134707085f02342f8f6505022ad7478929196951367d')}
COORDINATE_CHECKER = "scripts/check-pid2-represented-coordinate-v4.py"
CURRENT_CHECKER_SHA256 = "c25af032b2d4fcd8234eab71ac929bd8ade830164841b7c2cd965dbd5c8f184f"


def current_files(root):
    previous, _, historic = expectation(root)
    old = {p: previous.blob(root, REPORT_LABEL, p) for p in historic}
    previous.compare(historic, old, "issued report-label files")
    required = old.copy()
    checker = old[COORDINATE_CHECKER]
    for path, (before, after) in CURRENT_SOURCES.items():
        revised = previous.blob(root, CORRECTED_INPUTS, path)
        require(sha(old[path]) == before and sha(revised) == after,
                f"original or corrected input differs: {path}")
        require(checker.count(before.encode()) == 1, f"historical checker digest is absent: {path}")
        checker = checker.replace(before.encode(), after.encode(), 1)
        required[path] = revised
    require(sha(checker) == CURRENT_CHECKER_SHA256, "corrected two-field checker differs")
    required[COORDINATE_CHECKER] = checker
    return previous, old, required


def current_source(root):
    previous, _, expected = current_files(root)
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    git(root, "merge-base", "--is-ancestor", CORRECTED_INPUTS, head)
    previous.compare(expected, {p: previous.blob(root, head, p) for p in expected},
                     "committed current files")
    previous.compare(expected, {p: previous.regular(root, p) for p in expected},
                     "working current files")
    for path in expected:
        now = git(root, "ls-tree", head, "--", path).split(None, 1)[0]
        original = git(root, "ls-tree", REPORT_LABEL, "--", path).split(None, 1)[0]
        require(now == original and now in (b"100644", b"100755")
                and bool((root / path).stat().st_mode & 0o111) == (now == b"100755"),
                f"source mode differs: {path}")
    return {"commit": head, "report_label_commit": REPORT_LABEL, "corrected_inputs": CORRECTED_INPUTS,
            "protected_files": {p: sha(data) for p, data in expected.items()}}


def current_controls(root):
    previous, old, expected = current_files(root)
    previous.compare(expected, expected.copy(), "positive control")
    changed = {p: old[p] for p in (*CURRENT_SOURCES, COORDINATE_CHECKER)}
    changed["crates/pid-core/src/exact_binary64.rs"] = expected["crates/pid-core/src/exact_binary64.rs"] + b"\n"
    diagnostics = {}
    for path, other in changed.items():
        try:
            previous.compare(expected, expected | {path: other}, "control")
        except ValueError as error:
            require(str(error) == "control differs: " + path, f"wrong diagnosis: {path}")
            diagnostics[path] = str(error)
        else:
            raise ValueError(f"accepted an altered file: {path}")
    return {"accepted": 1, "refused": diagnostics}

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("operation", choices=("source", "controls", "current", "current-controls"))
    cli.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = cli.parse_args()
    root = args.repo_root.resolve(strict=True)
    operations = {"source": source, "controls": controls, "current": current_source,
                  "current-controls": current_controls}
    result = operations[args.operation](root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"PID2 report-label profile failed: {error}") from error
