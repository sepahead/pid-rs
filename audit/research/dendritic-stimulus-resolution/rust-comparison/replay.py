"""Build the frozen Rust API and compare its returned binary64 atoms to the exact products."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
NAME = "shai_grid_pid_receiver"
FORMAT = "json-render-diagnostics"


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def need(ok, name):
    if not ok:
        raise ValueError(name)


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def frozen():
    seal = json.loads((HERE / "FROZEN.json").read_bytes())
    for name, expected in seal["files"].items():
        need(digest(HERE / name) == expected, "changed original comparison file: " + name)
    return json.loads((HERE / "SOURCE.json").read_bytes())


def original_sources(repository, destination, source):
    original = source["git"]
    command = ["git", "-C", str(repository)]
    tree = subprocess.check_output(command + ["rev-parse", original + "^{tree}"], text=True).strip()
    need(source["tree"] == tree, "pinned tree")
    names = list(source["files"])
    queries = "".join(f"{original}:{name}\n" for name in names).encode("ascii")
    raw = subprocess.check_output(command + ["cat-file", "--batch"], input=queries)
    stream = BytesIO(raw)
    for name in names:
        oid, kind, length = stream.readline().split()
        need(kind == b"blob", "source is not a regular blob")
        content = stream.read(int(length))
        need(sha256(content).hexdigest() == source["files"][name], "wrong source " + name)
        need(stream.read(1) == b"\n", "git framing")
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    need(stream.read(1) == b"", "extra original source")


def source_identity(work, source):
    adapter = Path("crates/pid-core/src/bin") / (NAME + ".rs")
    current = {p.relative_to(work).as_posix() for p in work.rglob("*") if p.is_file()}
    need(current == set(source["files"]) | {adapter.as_posix()}, "undeclared source in build input")
    for name, sha in source["files"].items():
        need(digest(work/name) == sha, "source altered: " + name)
    need(digest(work/adapter) == digest(HERE/"measurement.rs"), "native client identity")


def captured(command, out, name, *, stdin=None, cwd=None, env=None, timeout=90):
    start = time.monotonic()
    proc = subprocess.run(command, cwd=cwd, input=stdin, env=env,
                          capture_output=True, timeout=timeout, check=False)
    duration = time.monotonic() - start
    (out/(name + ".stdout")).write_bytes(proc.stdout)
    (out/(name + ".stderr")).write_bytes(proc.stderr)
    write(out/(name + ".process.json"), {"returncode":proc.returncode, "elapsed_seconds":duration,
          "stdout_sha256":sha256(proc.stdout).hexdigest(), "stderr_sha256":sha256(proc.stderr).hexdigest()})
    return proc


def build(args):
    source = frozen()
    dest = args.build.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    work = dest/"work"
    original_sources(args.repository, work, source)
    adapter = work/"crates/pid-core/src/bin"/(NAME + ".rs")
    shutil.copyfile(HERE/"measurement.rs", adapter)
    source_identity(work, source)
    cargo, rustc = args.cargo.resolve(), args.rustc.resolve()
    tools = {"cargo": {"version":subprocess.check_output([cargo,"-V"], text=True).strip(),"sha256":digest(cargo)},
             "rustc": {"version":subprocess.check_output([rustc,"-vV"], text=True).strip(),"sha256":digest(rustc)}}
    recorded = json.loads((HERE/"TOOLCHAIN.json").read_bytes())
    if args.original_tools:
        need(tools == recorded, "pinned compiler and Cargo")
    env = {key:os.environ[key] for key in ("HOME","PATH","TMPDIR","CARGO_HOME","SDKROOT","DEVELOPER_DIR")
           if key in os.environ}
    env.update({"LLVM_PARALLEL_LINK_JOBS":"1","CARGO_BUILD_JOBS":"1","CARGO_INCREMENTAL":"0",
                "CARGO_PROFILE_DEV_DEBUG":"0","CARGO_NET_OFFLINE":"true","CARGO_TARGET_DIR":str(dest/"target"),
                "RUSTC":str(rustc),"LC_ALL":"C","TZ":"UTC"})
    proc = captured([cargo,"build","--locked","--offline","--no-default-features","--jobs","1",
                    "-p","pid-core","--bin",NAME,"--message-format",FORMAT],
                    dest, "compile", cwd=work, env=env, timeout=540)
    need(proc.returncode == 0, "offline Cargo build; inspect compile.stderr/stdout")
    artifacts = [json.loads(line) for line in proc.stdout.splitlines()]
    scientific = [a for a in artifacts if a.get("reason") == "compiler-artifact"
                  and a.get("target",{}).get("name") in ("pid_core",NAME)]
    need(len(scientific) == 2 and all(a["features"] == [] for a in scientific),
         "genuine default-free library and client artifacts")
    executable = dest/"target"/"debug"/NAME
    need(any(a["executable"] == str(executable) for a in scientific), "Cargo-selected client")
    source_identity(work, source)
    return {"git":source["git"],"tree":source["tree"],"original_source_files":len(source["files"]),
            "measurement_sha256":digest(HERE/"measurement.rs"),"compiler":tools,
            "binary_sha256":digest(executable),"features":[], "profile":"dev, debug information off"}


def evaluate(args):
    source = frozen()
    compare = runpy.run_path(str(HERE/"compare.py"))
    def require_identity(p, value):
        need(digest(p) == value, "original input identity: " + p.name)
    for path, key in ((args.grid,"input"),(args.reference,"exact"),(args.arithmetic,"trusted_arithmetic")):
        require_identity(path, source[key])
    registration = json.loads(args.registration.read_bytes())
    need(registration["field"] == digest(HERE/"FROZEN.json"), "registered scientific field")
    require_identity(args.prepare, registration["source"])
    raw_grid = args.grid.read_bytes()
    inputs = compare["expected_rows"](raw_grid)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    command = [sys.executable,"-I","-S","-B"]
    if not __debug__:
        command += ["-O"]
    command += ["-c",args.prepare.read_text()]
    env = {"PATH":"/usr/bin:/bin","LC_ALL":"C","TZ":"UTC"}
    if args.sandbox_macos:
        profile = '(version 1)(allow default)(deny network*)(deny file-write*)(deny file-read* (subpath "/Users"))(deny process-fork)'
        command = ["/usr/bin/sandbox-exec","-p",profile,*command]
    calc = captured(command, out, "prepare", stdin=raw_grid, cwd="/", env=env, timeout=25)
    need(calc.returncode == 0 and not calc.stderr and len(calc.stdout) <= 100000, "prepared scientific rows")
    proposal = compare["load_json"](calc.stdout)
    compare["validate_rows"](proposal, inputs)
    built = json.loads((args.build/"BUILT.json").read_bytes())
    binary = (args.build/"target"/"debug"/NAME).resolve()
    require_identity(binary, built["binary_sha256"])
    need(built["git"] == source["git"] and built["tree"] == source["tree"]
         and built["measurement_sha256"] == digest(HERE/"measurement.rs") and built["features"] == [],
         "original native source and features")
    source_identity(args.build/"work", source)
    native_call = [str(binary)]
    if args.sandbox_macos:
        profile = '(version 1)(allow default)(deny network*)(deny file-write*)(deny process-fork)'
        native_call = ["/usr/bin/sandbox-exec","-p",profile,*native_call]
    native = captured(native_call,out,"native",stdin=calc.stdout,cwd="/",env=env,timeout=120)
    need(native.returncode == 0 and not native.stderr and len(native.stdout) < 100000,
         "original bounded native result")
    actual = compare["load_json"](native.stdout)
    exact = compare["load_json"](args.reference.read_bytes())
    arithmetic = runpy.run_path(str(args.arithmetic))
    targets = compare["build_targets"](exact, arithmetic["log_interval"])
    result = compare["check"](actual, inputs, targets)
    controls = runpy.run_path(str(HERE/"controls.py"))["exercise"](compare, proposal, inputs, actual, targets)
    bad = dict(proposal)
    bad["10"] = bad["10"][:-1]
    for name, word in (("short-input",json.dumps(bad).encode()),("overlong-input",b" " * 100001)):
        refused = captured(native_call, out, name, stdin=word, cwd="/", env=env, timeout=10)
        need(refused.returncode != 0 and not refused.stdout and refused.stderr,"native " + name + " rejection")
    controls["native_rejections"] = ["650 direct rows", "100001 input bytes"]
    result.update({"controls":controls, "raw_native_sha256":digest(out/"native.stdout"),
                  "row_source_sha256":digest(args.prepare),"data_sha256":source["input"],
                  "reference_sha256":source["exact"],"measured_source":source["git"]})
    require_identity(binary, built["binary_sha256"])
    frozen()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation",required=True)
    b = sub.add_parser("build")
    b.add_argument("--repository",type=Path,required=True)
    b.add_argument("--build",type=Path,required=True)
    b.add_argument("--cargo",type=Path,required=True)
    b.add_argument("--rustc",type=Path,required=True)
    b.add_argument("--original-tools",action="store_true")
    e = sub.add_parser("compare")
    for name in ("build","grid","reference","arithmetic","registration","prepare","output"):
        e.add_argument("--"+name,type=Path,required=True)
    e.add_argument("--sandbox-macos",action="store_true")
    args = parser.parse_args()
    if args.operation == "build":
        obj = build(args)
        path = args.build/"BUILT.json"
    else:
        obj = evaluate(args)
        path = args.output/"RESULT.json"
    write(path, obj)
    print(digest(path))


if __name__ == "__main__":
    main()
