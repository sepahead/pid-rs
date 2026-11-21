"""Check the exact earlier authorities before using their two independent source readers."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PACKAGE = "audit/research/three-source-original-reachable-v3"
PAYLOAD = PACKAGE+"-proofs"
ATTEMPT = PACKAGE+"-registration.json"
WORKFLOW = ".github/workflows/three-source-original-reachable-v3.yml"
OLD = "audit/research/three-source-original-first-three"
SYNTHETIC = "audit/research/three-source-synthetic-projection"
SHARED = "audit/research/three-source-w02"
CASES = ("W01", "W03", "W15")


def require(p, why):
    if not p:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate JSON key "+key)
        out[key] = value
    return out


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)


def encoded(item):
    return json.dumps(item, ensure_ascii=True, separators=(",",":")).encode()+b"\n"


def write(path, item):
    path.write_text(json.dumps(item, indent=2, ensure_ascii=False)+"\n")


def check_bytes(path, info):
    require(path.resolve()==path and path.is_file() and path.stat().st_size==info["bytes"] and
            digest(path)==info["sha256"], "bound source "+str(path))


def module(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(repo, *args):
    return subprocess.check_output(["git","-C",str(repo),*args], stderr=subprocess.STDOUT)


def tree_hashes(root):
    return {p.name:digest(p) for p in sorted(root.iterdir()) if p.is_file()}


def external(repo):
    authorities = read(HERE/"external.json")
    for path, record in authorities.items():
        check_bytes(repo/path,record)
        blob = git(repo,"rev-parse",record["commit"]+":"+path).decode().strip()
        require(blob == record["git_blob"] and sha(git(repo,"cat-file","blob",blob))==record["sha256"],
                "specified earlier exact Git object "+path)
    return authorities


def extend_observer(source, oldnames, newnames):
    start="  let targets : List Name := ["
    previous=start+", ".join(chr(96)+n for n in oldnames)+"]\n"
    require(source.count(previous)==1, "exact prior observer enumeration")
    return source.replace(previous, start+", ".join(chr(96)+n for n in newnames)+"]\n")


def preparation_identity(rows):
    return {k:{"source_record_sha256":sha(encoded(v)),"fixed_sources":sha(encoded(v["sources"])),
               "templates":sha(encoded(v["templates"])),"targets":sha(encoded(v["targets"])),
               "proof_slots":sha(encoded(v["slots"])),"stage_plan":sha(encoded(v["ordinary_order"])),
               "required_terms":sha(encoded(v["required_uses"]))} for k,v in rows.items()}


def collect(repo, target):
    external(repo)
    previous=module(repo/OLD/"assembly.py")
    old=module(repo/OLD/"statements.py")
    writer=module(repo/SHARED/"source_writer.py")
    routes=module(HERE/"route.py")
    original=previous.collect(repo,target)
    require(previous.preparation_identity(original)==read(repo/OLD/"generated.json"), "source matches failed original registration")
    bound=read(repo/OLD/"bindings.json")
    independently_bound=read(HERE/"bindings.json")
    require(independently_bound["cases"]==bound["cases"] and independently_bound["declarations"]==bound["declarations"]
            and independently_bound["defined_names"]==bound["defined_names"], "original case identities")
    for case,row in original.items():
        root=target/case
        src=root/"sources"
        tm=root/"templates"
        # The previous independently checked baseline is retained before superseding its proof route.
        (root/"source-structure.json").rename(root/"historical-source-structure.json")
        raw=(repo/bound["cases"][case]["input"]["relative_path"]).read_bytes()
        ast=writer.typed_script(writer.neutral(raw)[0])
        require(sha(encoded(ast))==row["typed_sha256"], "same complete typed literal")
        design=routes.plan(case,ast)
        fixed,stages,addition,direct,slots,markers,signatures=routes.build(design,writer,old)
        previous_targets=row["targets"].copy()
        oldslots=row["slots"].copy()
        for q in oldslots:
            if q.startswith("OriginalSteps.") or q in ("OriginalProof.staticFold","OriginalProof.wellFormed","OriginalProof.inhabited"):
                continue
            require(q in addition and addition[q]==previous_targets[q],"retained declaration and owner "+q)
        row["targets"].update(addition)
        row["required_uses"]={**{k:[v] for k,v in row["consumer_uses"].items()}, **direct}
        row["independently_declared_signature_checks"]=signatures
        row["source_plan"]=design
        row["compile_checkpoints"]={k:v for k,v in markers.items() if v}
        row["individual_lemma_templates"]={}
        for module_name in row["compile_checkpoints"]:
            pieces=routes.isolated_statements(stages[module_name])
            point=root/"isolated-templates"/module_name
            point.mkdir(parents=True)
            for slot,piece in pieces.items():
                (point/(slot+".lean.in")).write_text(piece)
            row["individual_lemma_templates"][module_name]={slot:sha(piece.encode()) for slot,piece in pieces.items()}
        row["old_public_type_sha256"]={name:sha(prop.encode()) for name,prop in old.types(case).items()}
        row["slots"]=[q for q in oldslots if q.startswith("OriginalSteps.") or
                      q in ("OriginalProof.staticFold","OriginalProof.wellFormed","OriginalProof.inhabited")]+slots
        term_source=extend_observer((src/"OriginalTerms.lean").read_text(),previous_targets,row["targets"])
        boundary="run_cmd do\n"
        require(term_source.count(boundary)==1,"unique stock term observer body")
        fixed["OriginalTerms"]=term_source.replace(boundary,
            "".join("example : "+prop+" := "+name+"\n" for name,prop in signatures.items())+"\n"+boundary)
        fixed["OriginalAxioms"]="import OriginalConsumer\n\n"+"".join("#print axioms "+n+"\n" for n in row["targets"])
        for name,text in fixed.items():
            (src/(name+".lean")).write_text(text)
        for name,text in stages.items():
            (tm/(name+".lean.in")).write_text(text)
        old_static=["OriginalStaticGroup"+format(i,"02d") for i in range(11)]+["OriginalStatic"]
        row["template_order"]=[*old_static,*stages]
        row["ordinary_order"]=["W02Semantics","ProjectionCore","ProjectionReification","TraceCode",
                              "OriginalLiteral","OriginalPrefix","OriginalContract","ReachSpec",*old_static,
                              *stages,"OriginalConsumer"]
        row["sources"]=tree_hashes(src)
        row["templates"]=tree_hashes(tm)
        require(set(row["templates"])=={n+".lean.in" for n in row["template_order"]}, "complete candidate template membership")
        require(set(row["ordinary_order"])|{"OriginalTerms","OriginalAxioms","OriginalTrace"}==
                {name[:-5] for name in row["sources"]}|set(row["template_order"]), "complete scientific source order")
        validate_graph(row, previous_targets)
        write(root/"source-structure.json",row)
    return original


def validate_graph(row, old):
    targets=row["targets"]
    needed=row["required_uses"]
    require(all(q in targets and targets[q]==owner for q,owner in old.items()),"all historical targets and module owners")
    require(all(q in targets and len(children)==len(set(children)) and
                all(x in targets for x in children) for q,children in needed.items()),"typed direct edges")
    for name in ("rightInverse","checkedBody","preserves","reifies","fullEvaluation","bodyAgreement"):
        require(needed["OriginalConsumer."+name]==["OriginalProof."+name] and
                needed["OriginalProof."+name]==["OriginalReach."+name] and
                targets["OriginalReach."+name]=="Reach"+name[0].upper()+name[1:],
                "unchanged consumer to original owner to distinct dynamic helper "+name)
    seen=set()
    visiting=set()
    def visit(q):
        require(q not in visiting,"cycle in proof wiring")
        if q in seen:
            return
        visiting.add(q)
        for child in needed.get(q,[]):
            visit(child)
        visiting.remove(q)
        seen.add(q)
    for q in row["consumer_uses"]:
        visit(q)
    new=set(targets)-set(old)
    require(new<=seen, "unconnected new proof declarations "+str(sorted(new-seen)))


def materialize_controls(repo,target):
    return module(repo/OLD/"assembly.py").materialize_controls(repo,target)
