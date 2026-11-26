"""Recheck the LP4 experiment. Optionally cold-build from the exact original Git blobs offline."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SRC = HERE / "portable"
OBS = HERE / "observed"
STAMP = "6a9f087be84bc21a89ff51e7da8e626e6883d73e"


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(command, **kwargs):
    r = subprocess.run(command, capture_output=True, timeout=300, check=False, **kwargs)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors="replace"))
    return r


def build(repository, destination, cargo):
    # The measured host reused this exact library build. This path provides
    # a cold Cargo alternative on a host that has its locked crates cached.
    source = json.loads((SRC / "original-shai-source.json").read_bytes())
    need(source["git"] == STAMP, "original repository commit")
    root = destination / "work"
    root.mkdir()
    git = ["git", "--no-optional-locks", "-C", str(repository)]
    tree = run(git + ["rev-parse", STAMP + "^{tree}"]).stdout.decode().strip()
    need(tree == source["tree"], "original repository source tree")
    queries = "".join(STAMP + ":" + name + "\n" for name in source["files"]).encode()
    stream = io.BytesIO(run(git + ["cat-file", "--batch"], input=queries).stdout)
    for name, expected in source["files"].items():
        _, kind, size = stream.readline().split()
        data = stream.read(int(size))
        need(kind == b"blob" and sha(data) == expected and stream.read(1) == b"\n", "source " + name)
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
    need(not stream.read(1), "all source blobs consumed")
    client = root / "crates/pid-core/src/bin/lp4_categorical_client.rs"
    client.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "measurement.rs", client)
    target = destination / "build"
    env = os.environ.copy()
    env.update(CARGO_TARGET_DIR=str(target), CARGO_NET_OFFLINE="true", CARGO_INCREMENTAL="0",
               CARGO_PROFILE_DEV_DEBUG="0", LLVM_PARALLEL_LINK_JOBS="1", CARGO_BUILD_JOBS="1")
    run([cargo, "build", "--locked", "--offline", "--no-default-features", "--jobs", "1",
         "--package", "pid-core", "--bin", "lp4_categorical_client"], cwd=root, env=env)
    return target / "debug/lp4_categorical_client"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--binary", type=Path, help="already built LP4 measurement executable")
    options.add_argument("--repository", type=Path, help="Git checkout containing the pinned source")
    options.add_argument("--recorded", action="store_true", help="recheck the retained original native response")
    parser.add_argument("--cargo", default="cargo")
    args = parser.parse_args()
    archive = args.archive.resolve()
    prefix = [sys.executable, *(["-O"] if not __debug__ else []), "-I", "-S", "-B"]
    with tempfile.TemporaryDirectory(prefix="lp4-ten-rust-") as temp:
        work = Path(temp)
        rows = run(prefix + [str(SRC / "compare.py"), str(archive)]).stdout
        need(rows == (OBS / "episode-signs.json").read_bytes(), "all original episode signs")
        (work / "rows.json").write_bytes(rows)
        if args.recorded:
            raw = (OBS / "native-words.json").read_bytes()
        else:
            binary = args.binary.resolve() if args.binary else build(args.repository.resolve(), work, args.cargo)
            native = run([str(binary)], input=rows)
            need(not native.stderr, "unexpected native diagnostics")
            raw = native.stdout
        (work / "native.json").write_bytes(raw)
        result = run(prefix + [str(SRC / "compare.py"), str(archive), "--rows", str(work / "rows.json"),
                               "--native", str(work / "native.json")]).stdout
        controls = run(prefix + [str(SRC / "controls.py"), str(work / "native.json"), str(archive)]).stdout
        need(controls == (OBS / "hostile-comparisons.json").read_bytes(), "all original opposed cases")
        output = {"raw_sha256":sha(raw), "source_rows_sha256":sha(rows), "numerical_result_sha256":sha(result),
                  "matches_original_native_bytes":raw == (OBS / "native-words.json").read_bytes(),
                  "matches_original_measured_results":result == (OBS / "ten-results.json").read_bytes(),
                  "absolute_tolerance_nats":"1/1000000000000", "coordinates":len(json.loads(result)["measurements"]),
                  "origin":"retained original output" if args.recorded else "new native execution"}
        sys.stdout.write(json.dumps(output, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
