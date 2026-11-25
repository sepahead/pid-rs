"""Read the two existing real-series bounds on a bounded Linux host."""

import argparse
from contextlib import suppress
from hashlib import file_digest
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
GIB = 1024 ** 3
RSS_LIMIT = 4 * GIB
WALL_LIMIT = 600
STREAM_LIMIT = 16 * 1024 ** 2
NAMES = {"PIDLogLibrary.lower": "Real.sum_range_le_log_div",
         "PIDLogLibrary.upper": "Real.log_div_le_sum_range_add"}
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def git(root, *args):
    return subprocess.check_output(["git", "-C", root, *args], timeout=30, text=True).strip()


def group_bytes(group):
    # Linux /proc/pid/stat fields 5 and 24 are process group and RSS in pages.
    pages = 0
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_bytes().rsplit(b")", 1)[1].split()
        except (ProcessLookupError, FileNotFoundError, PermissionError):
            continue
        if int(fields[2]) == group:
            pages += max(0, int(fields[21]))
    return pages * os.sysconf("SC_PAGE_SIZE")


def bounded(argv, *, cwd, env, output, label, records):
    stdout = output / (label + ".stdout")
    stderr = output / (label + ".stderr")
    started = time.monotonic()
    peak = 0
    samples = 0
    reason = None
    with stdout.open("xb") as out, stderr.open("xb") as err:
        child = subprocess.Popen(argv, env=env, cwd=cwd, start_new_session=True,
                                 stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        try:
            while child.poll() is None:
                measured = group_bytes(child.pid)
                peak = max(peak, measured)
                samples += 1
                if measured > RSS_LIMIT:
                    reason = "group RSS above four GiB"
                if time.monotonic() - started > WALL_LIMIT:
                    reason = "wall time above ten minutes"
                if max(out.tell(), err.tell()) > STREAM_LIMIT:
                    reason = "output above stream limit"
                if reason:
                    break
                time.sleep(0.1)
        finally:
            if child.poll() is None:
                with suppress(ProcessLookupError):
                    os.killpg(child.pid, signal.SIGKILL)
            code = child.wait(timeout=10)
    row = dict(label=label, argv=list(map(str, argv)), exit=code, resource_stop=reason,
               max_sampled_group_rss_bytes=peak, samples=samples,
               elapsed_seconds=round(time.monotonic()-started, 3), stdout_sha256=sha(stdout),
               stderr_sha256=sha(stderr))
    records.append(row)
    require(reason is None and max(stdout.stat().st_size,stderr.stat().st_size) <= STREAM_LIMIT,
            f"{label} exceeded resources")
    return code, stdout.read_text(), stderr.read_text()


def natural_type(text):
    # Keep the variable names, arithmetic, constants, arrows, and the two orders.
    compact = "".join(text.split())
    for name, replacement in (("Real.log", "log"), ("Finset.range", "range"),
                              ("Real", "ℝ"), ("Nat", "ℕ"), ("↑", "")):
        compact = compact.replace(name, replacement)
    return compact


def formula_tree(text):
    """Retain arithmetic grouping, exponent association, the log argument and sum scope."""
    tokens = re.findall(r"range|log|[0-9]+|[inx∑∈(),+*/^-]", text)
    require("".join(tokens)==text, "unrecognized printed expression")
    pos = 0
    precedence = {"+":1, "-":1, "*":2, "/":2, "^":3}

    def take(expected=None):
        nonlocal pos
        require(pos<len(tokens) and (expected is None or tokens[pos]==expected), "printed syntax")
        value=tokens[pos]
        pos+=1
        return value

    def atom():
        word=take()
        if word=="(":
            value=expression(0)
            take(")")
            return value
        if word=="log":
            return ("log", atom())
        if word=="∑":
            for symbol in ("i","∈","range","n",","):
                take(symbol)
            return ("sum_i_range_n", expression(0))
        require(word in {"x","i","n"} or word.isdecimal(),"printed operand")
        return word

    def expression(minimum):
        first=atom()
        while pos<len(tokens) and tokens[pos] in precedence and precedence[tokens[pos]]>=minimum:
            operator=take()
            right=expression(precedence[operator]+(0 if operator=="^" else 1))
            first=(operator,first,right)
        return first

    result=expression(0)
    require(pos==len(tokens),"additional printed expression")
    return result


def check_domain_and_body(name, whole):
    typ = natural_type(whole)
    signature = r"^∀\{x:ℝ\},0≤x→x<1→∀\(n:ℕ\),"
    match = re.match(signature, typ)
    require(match is not None, f"expected 0 ≤ x < 1 and a natural truncation index in {name}")
    body = typ[match.end():]
    require("→" not in body and body.count("≤")==1, f"unexpected additional hypothesis or conclusion {name}")
    left,right = body.split("≤")
    odd_sum="∑i∈rangen,x^(2*i+1)/(2*i+1)"
    logarithm="1/2*log((1+x)/(1-x))"
    tail="x^(2*n+1)/(1-x^2)"
    forms=(odd_sum,logarithm) if name.endswith(".lower") else (logarithm,"("+odd_sum+")+"+tail)
    require((formula_tree(left),formula_tree(right))==tuple(formula_tree(f) for f in forms),
            f"full ordered, grouped mathematical expressions in {name}")
    return typ


def positive(text):
    witnesses = {}
    all_names = set(NAMES) | set(NAMES.values())
    first_check = None
    for match in re.finditer(r"^@?([A-Za-z][A-Za-z0-9_.]*)\s*:\s*(.+)$",text,re.M):
        name=match[1]
        if name in all_names:
            require(name not in witnesses, f"repeated type observation {name}")
            witnesses[name]=match[2].strip()
            first_check = match.start() if first_check is None else min(first_check,match.start())
    require(set(witnesses)==all_names and first_check is not None, "four explicit native type observations")
    body=text[:first_check]
    marks=list(re.finditer(r"^theorem (PIDLogLibrary\.(?:lower|upper))\s*:\s*",body,re.M))
    require([m[1] for m in marks]==list(NAMES), "the two separate printed theorems")
    axioms={}
    for index, mark in enumerate(marks):
        name=mark[1]
        original=NAMES[name]
        end=marks[index+1].start() if index+1<len(marks) else len(body)
        statement, sep, proof=body[mark.end():end].partition(":=")
        require(sep and len(re.findall(r"\b"+re.escape(original)+r"\b",proof))==1,
                f"one typed use of the original declaration {name}")
        expected=check_domain_and_body(name, witnesses[original])
        require(natural_type(statement)==natural_type(witnesses[name])==expected,
                f"complete original type, observed type and printed statement {name}")
        for item in (name, original):
            ax=re.findall(r"^'"+re.escape(item)+r"' depends on axioms: \[([^\]]*)\]$",text,re.M)
            require(len(ax)==1, f"exact axiom line {item}")
            parts=ax[0].split(", ")
            require(len(parts)==len(set(parts)) and set(parts)<=ALLOWED, f"unapproved axiom {item}")
            axioms[item]=sorted(parts)
        require(axioms[name]==axioms[original], f"wrapper introduced extra trust {name}")
    require("⋯" not in text and "sorry" not in text and "..." not in text, "elided or admitted output")
    return axioms


def false_control(text):
    rows = [i for i in text.splitlines() if re.search(r":\d+:\d+: error:",i)]
    require(len(rows)==1 and re.match(r"^False\.lean:5:\d+: error: [Tt]ype mismatch",rows[0]),
            "wrong negative diagnostic")
    supplied=re.split(r"\bhas type\b",text)
    require(len(supplied)==2,"one supplied-type role")
    roles=re.split(r"\bbut is expected to have type\b",supplied[1])
    require(len(roles)==2 and re.fullmatch(r"\s*0\s*<\s*1(?:\s*:\s*Prop)?\s*",roles[0])
            and re.fullmatch(r"\s*1\s*<\s*0(?:\s*:\s*Prop)?\s*",roles[1]),
            "supplied and required propositions in their distinct diagnostic roles")


def main(args, result):
    pins = json.loads((HERE/"identities.json").read_bytes())
    lean_bin = args.lean_bin.resolve(strict=True)
    mathlib = args.mathlib.resolve(strict=True)
    out = args.out.resolve(strict=True)
    require(platform.system()=="Linux" and platform.machine()=="x86_64", "requires Linux x86_64")
    require(sha(args.archive) == pins["stock_archive_sha256"], "official stock archive")
    require(sha(mathlib/pins["module"]) == pins["module_sha256"], "original theorem source")
    require(sha(mathlib/"lake-manifest.json") == pins["manifest_sha256"], "original package manifest")
    require(git(mathlib,"rev-parse","HEAD")==pins["source_commit"], "Mathlib revision")
    lean, checker = lean_bin/"lean", lean_bin/"leanchecker"
    version=subprocess.check_output([lean,"--version"], text=True, timeout=30).strip()
    reported=subprocess.check_output([lean,"--githash"], text=True, timeout=30).strip()
    require(reported==pins["stock_commit"] and "Lean (version 4.34.1," in version, "stock release")
    cache_roots = {}
    package_list=json.loads((mathlib/"lake-manifest.json").read_bytes())["packages"]
    require({p["name"]:p["rev"] for p in package_list}==pins["package_revisions"], "locked dependencies")
    dependencies={name:(mathlib/".lake/packages"/name, revision) for name, revision in pins["package_revisions"].items()}
    dependencies["mathlib"]=(mathlib,pins["source_commit"])
    for name,(path,revision) in dependencies.items():
        require(git(path,"rev-parse","HEAD")==revision and Path(git(path,"rev-parse","--show-toplevel")).resolve()==path,
                f"dependency revision {name}")
        folder=path/".lake/build/lib/lean"
        if folder.is_dir():
            cache_roots[name]=folder.resolve(strict=True)
    target=cache_roots["mathlib"]/Path(pins["module"]).with_suffix(".olean")
    require(target.is_file() and target.stat().st_size>0, "target cache object")
    stored = {}
    for name,root in sorted(cache_roots.items()):
        for f in sorted(root.rglob("*")):
            if f.is_file() and f.name.endswith((".olean", ".olean.private", ".olean.server", ".ir", ".ir.sig")):
                require(not f.is_symlink(), "compiled dependency symlink")
                stored[name+"/"+f.relative_to(root).as_posix()] = [f.stat().st_size, sha(f)]
    save(out/"compiled-cache-files.json",stored)
    for name,digest in pins["observers"].items():
        require(sha(HERE/name)==digest, f"observer changed {name}")
    result.update(version=version, lean_commit=reported, binaries={f.name:sha(f) for f in (lean,checker)},
                  source_inputs=pins,cache_file_count=len(stored),cache_file_inventory=sha(out/"compiled-cache-files.json"),
                  cache_target_sha256=sha(target),platform=platform.platform(),
                  cpu_count=os.cpu_count(),sampled_rss_limit=RSS_LIMIT,wall_limit_seconds=WALL_LIMIT)
    objects=out/"objects"
    objects.mkdir()
    env={"HOME":str(out),"TMPDIR":str(out),"LEAN_PATH":os.pathsep.join(map(str,[objects,*cache_roots.values()])),
         "PATH":str(lean_bin)+":/usr/bin:/bin","LEAN_NUM_THREADS":"1","LC_ALL":"C.UTF-8","TZ":"UTC"}
    command=[lean,"-j","1","-DwarningAsError=true","-R",HERE]
    def call(label,argv):
        code, stdout, stderr=bounded(argv,cwd=HERE,env=env,output=out,label=label,records=result["commands"])
        require(not stderr, f"unexpected stderr {label}")
        return code,stdout
    code,stdout=call("compile",[ *command,"-o",objects/"Read.olean","Read.lean"])
    require(code==0 and (objects/"Read.olean").is_file(),"reader compile")
    result["axioms"]=positive(stdout)
    code,stdout=call("fresh",[checker,"--fresh","Read"])
    require(code==0 and not stdout.strip(),"stock fresh check")
    code,stdout=call("false",[*command,"False.lean"])
    require(code>0,"false arithmetic unexpectedly passed")
    false_control(stdout)
    result["objects"]={p.name:sha(p) for p in sorted(objects.iterdir()) if p.is_file()}
    result["success"]=True


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ("lean-bin", "mathlib", "archive", "out"):
        parser.add_argument("--"+arg, type=Path, required=True)
    args=parser.parse_args()
    args.out.mkdir(mode=0o700, parents=False, exist_ok=False)
    receipt={"success":False,"commands":[]}
    try:
        main(args,receipt)
    except Exception as exc:
        receipt["error"]=str(exc)
        raise
    finally:
        save(args.out/"RESULT.json",receipt)
