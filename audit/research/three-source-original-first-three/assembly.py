"""Read immutable source structures and assemble fixed consumers without evaluating a script."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
PACKAGE="audit/research/three-source-original-first-three"
SHARED="audit/research/three-source-w02"
SYNTHETIC="audit/research/three-source-synthetic-projection"
WORKFLOW=".github/workflows/three-source-original-first-three.yml"
PAYLOAD="audit/research/three-source-original-first-three-proofs"
ATTEMPT="audit/research/three-source-original-first-three-attempt.json"
CASES=("W01","W03","W15")

def require(test, why):
    if not test: raise ValueError(why)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def digest(path):
    with Path(path).open("rb") as file:
        return hashlib.file_digest(file,"sha256").hexdigest()

def pairs(pairs_):
    out={}
    for k,v in pairs_:
        require(k not in out,"duplicate JSON member "+k)
        out[k]=v
    return out

def read(path): return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs)

def encoded(value): return json.dumps(value,ensure_ascii=True,separators=(",",":")).encode()+b"\n"

def write(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")

def module(path):
    source=Path(path).resolve()
    spec=importlib.util.spec_from_file_location(source.stem,source)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def git(repo,*args):
    return subprocess.check_output(["git","-C",str(repo),*args],stderr=subprocess.STDOUT)

def check_bytes(path, row):
    require(path.resolve()==path and path.is_file() and path.stat().st_size==row["bytes"]
            and digest(path)==row["sha256"],"source identity "+str(path))

def bind(repo):
    table=read(HERE/"bindings.json")
    for row in [*(v["input"] for v in table["cases"].values()),*table["registered_shared"].values()]:
        path=repo/row["relative_path"]
        check_bytes(path,row)
        require(git(repo,"rev-parse",table["source_commit"]+":"+row["relative_path"]).decode().strip()==row["git_blob"],
                "original tracked blob "+row["relative_path"])
    synth_manifest=read(repo/SYNTHETIC/"manifest.json")
    for name in table["synthetic_reuse"]:
        check_bytes(repo/SYNTHETIC/name, synth_manifest["package_files"][name])
    return table

def tree_hashes(src):
    return {p.name:digest(p) for p in sorted(src.iterdir()) if p.is_file()}

def collect(repo,target):
    bindings=bind(repo)
    common=repo/SHARED
    writer=module(common/"source_writer.py")
    reader=module(common/"source_reader.py")
    literals=module(common/"lean_literals.py")
    design=module(HERE/"statements.py")
    trace=module(HERE/"finite_trace.py")
    observer=(common/"lean/W02Inspect.lean").read_text()
    result={}
    for key in CASES:
        case=bindings["cases"][key]
        bounds=case["structure"]
        raw=(repo/case["input"]["relative_path"]).read_bytes()
        require(len(raw)==bounds["raw_bytes"] and sha(raw)==bounds["sha256"],"raw identity")
        tree,spans=writer.neutral(raw)
        tree2,spans2=reader.read(raw)
        require(encoded(tree)==encoded(tree2) and encoded(spans)==encoded(spans2),"dual source readers")
        cursor=0
        for _,start,end in spans:
            require(start==cursor and end>start and end<=len(raw),"source byte span partition")
            cursor=end
        require(cursor==len(raw) and len(spans)==bounds["full_spans"],"full byte and span count")
        ast=writer.typed_script(tree)
        require(encoded(ast)==encoded(reader.checked_script(tree2)),"typed reader agreement")
        for value,name in ((tree,"tree_sha256"),(spans,"spans_sha256"),(ast,"annotated_sha256")):
            require(sha(encoded(value))==bounds[name],"source structure "+name)
        kinds=["logic","option"]+["constant"]*25+["define"]*57+["echo","assertion","assertion","check","exit"]
        require(len(ast)==bounds["commands"]==89 and [c[0] for c in ast]==kinds,"exact command order")
        free=[[c[1],c[2]] for c in ast if c[0]=="constant"]
        require(free==bindings["declarations"] and [x for x in free if x[1]==["int"]]==
                [["w"+str(i),["int"]] for i in range(16)],"all 25 typed free bindings")
        require([c[1] for c in ast[27:84]]==bindings["defined_names"],"all 57 source definitions")
        assertions=tree[-4:-2]
        require(assertions==case["assertions"],"literal order of both assertions")
        literal=(literals.prefix.decode().split("def originalScript")[0]+writer.lean_definition("originalScript",ast)
                 +"\nend SmtW02\n").encode()
        require(literals.matches(literal,encoded(ast))==(len(ast),bounds["annotated_sha256"]) and
                sha(literal)==bounds["lean_sha256"],"complete original byte-identical Lean literal")
        fixed,templates,roster,uses,slots=design.modules(key,ast,writer,observer)
        fixed.update(TraceCode=trace.CODE, OriginalTrace=trace.source(key))
        out=target/key
        out.mkdir(); src=out/"sources";src.mkdir(); tm=out/"templates";tm.mkdir()
        (src/"OriginalLiteral.lean").write_bytes(literal)
        for n,file in [("W02Semantics",common/"lean/W02Semantics.lean"),
                       ("ProjectionCore",repo/SYNTHETIC/"lean/ProjectionCore.lean"),
                       ("ProjectionReification",repo/SYNTHETIC/"lean/ProjectionReification.lean")]:
            (src/(n+".lean")).write_bytes(file.read_bytes())
        for name,s in fixed.items(): (src/(name+".lean")).write_text(s)
        for name,s in templates.items(): (tm/(name+".lean.in")).write_text(s)
        record={"raw_sha256":sha(raw),"commands":len(ast),"partition_bytes":cursor,
                "spans":len(spans),"typed_sha256":sha(encoded(ast)),"declarations":free,
                "definition_count":57,"source_assertions":assertions,"projected_slots":case["slots"],
                "finite_combinations":case["combinations"],"sources":tree_hashes(src),
                "templates":tree_hashes(tm),"targets":roster,"consumer_uses":uses,"slots":slots}
        write(out/"source-structure.json",record)
        result[key]=record
    return result

def preparation_identity(result):
    return {k:{name:sha(encoded(row[name])) for name in ("sources","templates","targets","consumer_uses","slots")}
            | {"source_record_sha256":sha(encoded(row))} for k,row in result.items()}

def materialize_controls(repo,target):
    """Only the three small artificial fixtures and four qualified refusal sources enter this stage."""
    s=repo/SYNTHETIC; shared=repo/SHARED
    maker=module(s/"make_sources.py")
    writer,reader,literals=[module(shared/(n+".py")) for n in ("source_writer","source_reader","lean_literals")]
    expected=read(s/"generated.json"); fixtures=read(s/"fixtures.json")
    (target/"W02Semantics.lean").write_bytes((shared/"lean/W02Semantics.lean").read_bytes())
    for n in ("Unary","Pair","Sat"):
        raw,_=maker.read_fixture(n,writer,reader,literals,fixtures[n])
        (target/("Synthetic"+n+"Data.lean")).write_bytes(raw)
    plan=read(s/"plan.json")
    needed=set(plan["stages"][0]["compile"])|set(plan["stages"][1]["refuse"])
    for name in sorted(needed):
        f=target/(name+".lean")
        if not f.is_file(): f.write_bytes((s/"lean"/f.name).read_bytes())
    found=tree_hashes(target)
    require(set(found)=={n+".lean" for n in needed} and all(h==expected[n] for n,h in found.items()),
            "every synthetic control source must match the hosted small-stage bytes")
    return plan,found

