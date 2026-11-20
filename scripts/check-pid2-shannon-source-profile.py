#!/usr/bin/env python3
"""Check the source transition and native test partitions for represented PID2 arithmetic."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


C4 = "0f3122a96e48a099581ad4faf3e3d5d9138367f6"
PRODUCTION = "03325745f64becf437b9b3042b51a9d925450579"
CHECKER = "scripts/check-pid2-represented-coordinate-v4.py"
CONTROL = "scripts/check-pid2-represented-coordinate-v4-self-test.py"
EXACT = "crates/pid-core/src/exact_binary64.rs"
OLD_EXACT = "6e7d6be525878638e4be253aff9bd74d25dd94afb53f1b520fb8e4e1a0a8cdfb"
OLD_CHECKER = "47b77161b41ff94da2ce47b83adc7d3a5e5604a4e2a5cd8822e86129fa6f8051"
NEW_CHECKER = "452a954ab7301d860ea7fdc63cffc5efaa2b39ea1f74c211fc0d8c10f95639cb"
FIXTURE = "crates/pid-core/tests/fixtures/"
PINS = {
    EXACT: "c3d047917b9f1c5d162c325e3128183787f0f874205fe80ba0bb6c2dd68042c5",
    "crates/pid-core/src/invariants.rs": "00e57e312888783928ce967aa44b3d2769f4c39e3f4ae377b3cbd8c1f6b390d5",
    "crates/pid-core/src/pid2.rs": "f8cce5ece132a54df30a19f3b867c1296b5325e725408f628143c619ac814146",
    "crates/pid-core/tests/pid2.rs": "967a26dac7633841ac14670e5f4d3362e0a4cfcf35beed72ef264d8b9d5b70bf",
    "crates/pid-core/src/bin/exp0.rs": "c2a28c24442f850fa033a8f89ae889ae22c818efddfccbaff75e8b026164924e",
    FIXTURE + "exact_binary64_sum_oracle.json": "bd4d672730a69f654d96e18a1f81cfc31f8b301b6fa6ac7450a6d277a3a903ed",
    FIXTURE + "exact_binary64_sum_oracle.json.sha256": "6c2cad127ed36f7189fbfc8a3053607ebb9d057d16d8d6edd01db8ca9d17fe58",
    FIXTURE + "generate-exact-binary64-sum-oracle.py.snapshot": "05f0a45113132028f691ecaf5e1de4994626931cd46c6f1f2ebeec68a985fe81",
    "scripts/generate-exact-binary64-sum-oracle.py": "05f0a45113132028f691ecaf5e1de4994626931cd46c6f1f2ebeec68a985fe81",
    CONTROL: "b5c913e80866b5b20abc8d46b84db1cdaf18d8f1ba0aebaf1684b10fec84bfb5",
    "Cargo.lock": "2a390c1a3f468ed938e8c2e6597e78b26b933761c6200b0bf5e01d4b75f3c81d",
    "Cargo.toml": "e4011f053cb49a0378b2118bce9c50cd440eb603ac7efe8011a6f16dc344eea4",
    "crates/pid-core/Cargo.toml": "da8c4f5f4b32954df5c654ecf40cddc69b4367403f01a2b87e81c1bab9723063",
}
PARTITIONS = {
    "sum": (EXACT, "exact_binary64::tests::", 3, ["--lib", "exact_binary64::tests::"]),
    "pid2-unit": ("crates/pid-core/src/pid2.rs", "pid2::tests::", 17,
                  ["--features", "experimental-continuous", "--lib", "pid2::tests::"]),
    "pid2-integration": ("crates/pid-core/tests/pid2.rs", "", 18,
                         ["--all-features", "--test", "pid2"]),
    "exp0": ("crates/pid-core/src/bin/exp0.rs", "tests::", 34,
             ["--all-features", "--bin", "exp0"]),
}
ACTIVE = Path(__file__).resolve().with_name(Path(CHECKER).name)
PY = [sys.executable, *(["-O"] if sys.flags.optimize else []), "-I", "-S", "-B"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", root, *args], timeout=20)


def regular(root, relative):
    path = root
    for part in Path(relative).parts:
        path = path / part
        require(not path.is_symlink(), f"symbolic link in {relative}")
    require(path.is_file(), f"missing regular file {relative}")
    return path.read_bytes()


def check_sources(root):
    git(root, "merge-base", "--is-ancestor", C4, PRODUCTION)
    git(root, "merge-base", "--is-ancestor", PRODUCTION, "HEAD")
    original = git(root, "cat-file", "blob", f"{C4}:{CHECKER}")
    current = ACTIVE.read_bytes()
    require(sha(original) == OLD_CHECKER and original.count(OLD_EXACT.encode()) == 1,
            "historical checker identity differs")
    expected = original.replace(OLD_EXACT.encode(), PINS[EXACT].encode())
    require(current == expected and sha(current) == NEW_CHECKER,
            "current checker differs outside the single selected complete-file digest")
    for path, digest in PINS.items():
        require(sha(regular(root, path)) == digest, f"working source differs: {path}")
        historical = git(root, "cat-file", "blob", f"{PRODUCTION}:{path}")
        require(sha(historical) == digest, f"production commit source differs: {path}")
    corpus = json.loads(regular(root, FIXTURE + "exact_binary64_sum_oracle.json"))
    require(len(corpus["cases"]) == corpus["bounds"]["total_case_count"] == 561,
            "original corpus size differs")
    return original


def source_execution(script, root, success):
    p = subprocess.run([*PY, script, "--scope", "model-source", "--repo-root", root],
                       capture_output=True, timeout=90, check=False)
    if success:
        require(p.returncode == 0 and p.stderr == b"" and p.stdout.startswith(b"OK: scope=model-source;")
                and b"source=4 exact files; compiled=not-run;" in p.stdout,
                f"source execution failed: {p.stderr!r}")
    else:
        require(p.returncode == 1 and p.stdout == b""
                and p.stderr.startswith(f"ERROR: source digest mismatch for {EXACT}:".encode()),
                f"profile crossover did not reject the exact-file mismatch: {p.stderr!r}")
    return sha(p.stdout if success else p.stderr)


def source_checks(root):
    original = check_sources(root)
    with tempfile.TemporaryDirectory(prefix="pid2-sum-history-") as tmp:
        old = Path(tmp)
        old_checker = old / CHECKER
        old_checker.parent.mkdir(parents=True)
        old_checker.write_bytes(original)
        for path in (EXACT, *(p[0] for name, p in PARTITIONS.items() if name != "sum")):
            target = old / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git(root, "cat-file", "blob", f"{C4}:{path}"))
        return {
            "historical_on_historical": source_execution(old_checker, old, True),
            "historical_rejects_production": source_execution(old_checker, root, False),
            "current_on_production": source_execution(ACTIVE, root, True),
            "current_rejects_historical": source_execution(ACTIVE, old, False),
        }


def test_names(root, part):
    path, prefix, count, _ = PARTITIONS[part]
    raw = regular(root, path).decode("utf-8")
    names = re.findall(r"(?m)^\s*#\[test\]\s*(?:#\[[^\n]+\]\s*)*fn\s+(\w+)\s*\(", raw)
    require(len(names) == len(set(names)) == count, f"{part} test sources differ")
    return {prefix + name for name in names}


def check_log(raw, names):
    lines = raw.decode("utf-8").splitlines()
    n = len(names)
    require(lines.count(f"running {n} tests") == 1, "test count differs")
    results = [line for line in lines if line.startswith("test ") and not line.startswith("test result:")]
    require(len(results) == n and set(results) == {f"test {name} ... ok" for name in names},
            "native test names, status or multiplicity differ")
    summaries = [line for line in lines if line.startswith("test result:")]
    pattern = (rf"test result: ok\. {n} passed; 0 failed; 0 ignored; 0 measured; "
               r"[0-9]+ filtered out; finished in [0-9]+(?:\.[0-9]+)?s")
    require(len(summaries) == 1 and re.fullmatch(pattern, summaries[0]), "native summary differs")


def observer_controls():
    names = {"fixture::one", "fixture::two"}
    raw = (b"running 2 tests\ntest fixture::one ... ok\ntest fixture::two ... ok\n"
           b"test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 4 filtered out; finished in 0.00s\n")
    check_log(raw, names)
    controls = {
        "count": raw.replace(b"running 2", b"running 0"),
        "duplicate": raw.replace(b"fixture::one", b"fixture::two"),
        "wrong-name": raw.replace(b"fixture::one", b"fixture::other"),
        "failed": raw.replace(b"fixture::two ... ok", b"fixture::two ... FAILED"),
        "ignored": raw.replace(b"0 ignored", b"1 ignored"),
        "extra": raw + b"test fixture::three ... ok\n",
        "no-summary": raw.split(b"test result:")[0],
        "two-summaries": raw + raw[raw.index(b"test result:"):],
    }
    for name, data in controls.items():
        try:
            check_log(data, names)
        except ValueError:
            continue
        raise ValueError(f"native observation control passed: {name}")
    return sorted(controls)


def checked_native(root, out):
    require(git(root, "rev-parse", "HEAD").decode().strip() == PRODUCTION,
            "native checkout is not the fixed production object")
    require(not git(root, "status", "--porcelain", "--untracked-files=all"), "native checkout is dirty")
    check_sources(root)
    tools = {}
    for tool in ("rustc", "cargo"):
        version = subprocess.check_output([tool, "--version", "--verbose"], cwd=root, timeout=20)
        require(version.startswith(f"{tool} 1.99.1 ".encode()), f"unexpected {tool} release")
        tools[tool] = version.decode()
    out.mkdir()
    (out / "toolchain.json").write_text(json.dumps(tools, sort_keys=True, indent=2) + "\n")
    rows = []
    for profile in ("debug", "release"):
        for part, (_, _, count, options) in PARTITIONS.items():
            cmd = ["cargo", "test", "--locked"]
            if profile == "release":
                cmd.append("--release")
            cmd.extend(["-p", "pid-core", *options, "--", "--test-threads=1"])
            stem = out / f"{profile}-{part}"
            log = stem.with_suffix(".stdout")
            errors = stem.with_suffix(".stderr")
            with log.open("xb") as stdout, errors.open("xb") as stderr:
                result = subprocess.run(cmd, cwd=root, stdout=stdout, stderr=stderr,
                                        check=False, timeout=900)
            require(result.returncode == 0, f"{profile}/{part} cargo exit {result.returncode}")
            require(log.stat().st_size < 2**21 and errors.stat().st_size < 2**21,
                    f"{profile}/{part} log size exceeds the limit")
            raw = log.read_bytes()
            names = test_names(root, part)
            check_log(raw, names)
            rows.append({"profile": profile, "partition": part, "command": cmd, "count": count,
                         "named_tests": sorted(names), "stdout_sha256": sha(raw),
                         "stderr_sha256": sha(errors.read_bytes())})
    check_sources(root)
    require(not git(root, "status", "--porcelain", "--untracked-files=all"),
            "native checkout changed during qualification")
    return {"production_commit": PRODUCTION, "source_sha256": PINS,
            "corpus_cases": 561, "profiles": rows}


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("operation", choices=("source", "controls", "native"))
    args.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args.add_argument("--output", type=Path)
    a = args.parse_args()
    root = a.repo_root.resolve(strict=True)
    if a.operation == "native":
        require(a.output is not None and "CARGO_TARGET_DIR" in os.environ,
                "native requires a fresh output and an external Cargo target directory")
        target = Path(os.environ["CARGO_TARGET_DIR"]).resolve()
        require(not target.is_relative_to(root), "Cargo target directory must be outside the checkout")
        data = checked_native(root, a.output)
    else:
        require(a.output is None, "--output is only valid for native")
        data = source_checks(root) if a.operation == "source" else observer_controls()
    print(json.dumps(data, sort_keys=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"PID2 source qualification failed: {exc}") from exc
