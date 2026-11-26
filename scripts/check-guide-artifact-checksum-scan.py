#!/usr/bin/env python3
"""Check three published guide checksums and the full-history scanner's narrow policy."""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ORIGIN = "45c4ef6f037f4b826230a065aab563119a744df1"
GUIDE = "audit/formal/latex/mathematical-results-guide-current/"
PROFILES = (
    GUIDE + "edition.json",
    GUIDE + "edition-2026-11-25-categorical-inputs-angular-decisions-and-neighbour-counts.json",
    GUIDE + "edition-2026-11-25-nested-categorical-and-signed-logarithm-bounds.json",
    GUIDE + "edition-2026-11-25-logarithm-library-and-numerical-checks.json",
)
FIGURES = "audit/research/categorical-state-token/figures/"
# The first review commit contains these three published files and their first guide profile.
FILE_ROWS = (
    (FIGURES + "quoted-token-boundaries.pdf", 110),
    (FIGURES + "quoted-token-boundaries.svg", 111),
    ("output/pdf/categorical-state-token.pdf", 171),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "repeated key in a publication profile")
        result[key] = value
    return result


def git(repository, *words):
    return subprocess.check_output(["git", "-C", repository, *words])


def original_blob(repository, path):
    tree = git(repository, "ls-tree", "-z", ORIGIN, "--", path)
    mode, kind, rest = tree.split(b" ", 2)
    oid, returned_path = rest.split(b"\t", 1)
    require((mode, kind, returned_path) == (b"100644", b"blob", path.encode() + b"\0"),
            "original public regular file " + path)
    return git(repository, "cat-file", "blob", oid.decode())


def line_for(key, value):
    return "    " + json.dumps(key) + ": " + json.dumps(value) + ",\n"


def read_published_fields(repository):
    profile = original_blob(repository, PROFILES[0])
    originals = json.loads(profile, object_pairs_hook=unique_fields)["inputs"]
    result = {}
    for key, line_number in FILE_ROWS:
        value = hashlib.sha256(original_blob(repository, key)).hexdigest()
        require(originals[key] == value, "original guide value differs from the public file")
        require(profile.splitlines(keepends=True)[line_number - 1] == line_for(key, value).encode(),
                "original alert moved from its reviewed complete field")
        result[key] = value
    return result


def check_profiles(repository, originals):
    available = 0
    for name in PROFILES:
        path = repository / name
        if not path.exists() and name != PROFILES[0]:
            continue
        require(path.is_file() and not path.is_symlink(), "guide profile must be a regular file")
        inputs = json.loads(path.read_bytes(), object_pairs_hook=unique_fields)["inputs"]
        for key, value in originals.items():
            if name == PROFILES[0] and key in inputs:
                item = repository / key
                require(item.is_file() and not item.is_symlink(), "current guide input: " + key)
                require(hashlib.sha256(item.read_bytes()).hexdigest() == inputs[key],
                        "current guide checksum differs from the file: " + key)
            if inputs.get(key) == value:
                available += 1
    return available


def native(binary, policy, root, report):
    report.unlink(missing_ok=True)
    run = subprocess.run(
        [binary, "dir", ".", "--config", policy, "--gitleaks-ignore-path", "/dev/null",
         "--redact", "--no-banner", "--report-format", "json", "--report-path", report],
        cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False,
    )
    require(run.returncode in (0, 1) and report.is_file(), "native scanner did not return a report")
    rows = json.loads(report.read_bytes())
    require(isinstance(rows, list) and (run.returncode == 1) == bool(rows),
            "native status disagrees with its redacted report")
    require(all(isinstance(row, dict) and row["RuleID"] == "generic-api-key" for row in rows),
            "unexpected scanner rule in the public checksum control")
    return Counter((row["File"], row["StartLine"], row["EndLine"]) for row in rows)


@dataclass(frozen=True)
class Case:
    label: str
    path: str
    content: str
    before: tuple
    after: tuple


def cases(key, value, replacement):
    original = line_for(key, value)
    altered = ("0" if value[0] != "0" else "1") + value[1:]
    other = line_for("test_access_" + "token", "fixture" + "0123456789abcdef" * 3)
    for name in PROFILES:
        yield Case("exact", name, original, (1,), ())
        yield Case("altered value", name, line_for(key, altered), (1,), (1,))
        yield Case("other published file value", name, line_for(key, replacement), (1,), (1,))
        yield Case("different full key", name, line_for("other/" + key, value), (1,), (1,))
        yield Case("other field before", name, other + original, (1, 2), (1,))
        yield Case("other field after", name, original + other, (1, 2), (2,))
        yield Case("other field on same line", name, original.rstrip() + other, (1, 1), (1, 1))
        yield Case("separate unknown extended value", name, original + line_for(key, value + "af"),
                   (1, 2), (2,))
    yield Case("other profile", GUIDE + "edition-other.json", original, (1,), (1,))
    yield Case("other directory", "other/" + PROFILES[0], original, (1,), (1,))


def run_checks(repository, binary, policy):
    version = subprocess.check_output([binary, "version"], text=True).strip()
    require(version == "8.30.1", "these finite checks require Gitleaks 8.30.1")
    originals = read_published_fields(repository)
    present = check_profiles(repository, originals)
    with tempfile.TemporaryDirectory(prefix="pid-rs-guide-checksums-") as tmp:
        base = Path(tmp)
        root = base / "source"
        root.mkdir()
        former = base / "original.toml"
        former.write_bytes(original_blob(repository, ".gitleaks.toml"))
        count = 0
        fields = list(originals)
        for index, key in enumerate(fields):
            replacement = originals[fields[(index + 1) % len(fields)]]
            for case in cases(key, originals[key], replacement):
                item = root / case.path
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_text(case.content, encoding="utf-8")
                for rules, expected in ((former, case.before), (policy, case.after)):
                    got = native(binary, rules, root, base / "findings.json")
                    wanted = Counter((case.path, n, n) for n in expected)
                    require(got == wanted, "native result differs for " + case.label + " at " + case.path)
                item.unlink()
                count += 1
        (root / ".gitleaks.toml").write_bytes(policy.read_bytes())
        require(not native(binary, policy, root, base / "findings.json"), "policy text produced a finding")
    print(f"Verified 3 immutable public files, {present} matching profile entries and {count} paired native cases.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scanner", type=Path, required=True)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve()
    policy = args.config.resolve() if args.config else repository / ".gitleaks.toml"
    run_checks(repository, args.scanner.resolve(), policy)


if __name__ == "__main__":
    main()
