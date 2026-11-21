"""Test only the source boundaries and invented adverse records. Do not execute original mathematics."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(repo,out,source,manifest):
    a=load(HERE/"assembly.py")
    route=load(HERE/"route.py")
    read=load(HERE/"readback.py")
    driver=load(HERE/"run.py")
    proof=load(repo/a.OLD/"proof_interface.py")
    common=load(repo/a.SYNTHETIC/"readback.py")
    a.require(not out.exists(),"fresh synthetic control directory")
    out.mkdir()
    statuses={}

    def negative(name,fn,fragment):
        try:
            fn()
        except (ValueError,RuntimeError) as exc:
            a.require(fragment in str(exc),"wrong refusal "+name+" / "+str(exc))
            statuses[name]={"result":"refused for intended predicate","diagnostic":str(exc)}
        else:
            raise ValueError("unchecked negative control "+name)

    def changed(value,mut):
        new=copy.deepcopy(value);mut(new);return new

    a.require(driver.integrity(manifest),"exact bound member set")
    table=a.read(HERE/"generated.json")
    summary={}
    for case in a.CASES:
        row=a.read(source/case/"source-structure.json")
        old=a.read(source/case/"historical-source-structure.json")
        a.validate_graph(row,old["targets"])
        a.require(a.preparation_identity({case:row})[case]==table[case],"exact source structure")
        targets=row["targets"]
        for q, prop in row["independently_declared_signature_checks"].items():
            term=(source/case/"sources/OriginalTerms.lean").read_text()
            a.require(term.count("example : "+prop+" := "+q+"\n")==1,"registered typed scientific term")
        for mod,items in row["individual_lemma_templates"].items():
            ordinary=(source/case/"templates"/(mod+".lean.in")).read_text()
            singled=route.isolated_statements(ordinary)
            a.require(list(singled)==list(items),"isolated slot order")
            for slot,identity in items.items():
                f=source/case/"isolated-templates"/mod/(slot+".lean.in")
                a.require(a.digest(f)==identity and singled[slot]==f.read_text(),"one frozen complete proof proposition")
        a.require(len(old["targets"])==132 and set(old["targets"])<=set(targets) and
                  len(row["ordinary_order"])==len(set(row["ordinary_order"])) and
                  row["ordinary_order"].index("ReachSpec")<row["ordinary_order"].index("OriginalStaticGroup00"),
                  "fixed original receipts and candidate-free signature front")
        # The authorities after source collection are byte records; no source assertions have been evaluated.
        intervals=row["source_plan"]["intervals"]
        pop=lambda d:d["targets"].pop("OriginalProof.bodyAgreement")
        negative(case+"-missing-old-public",lambda:a.validate_graph(changed(row,pop),old["targets"]),"historical targets")
        own=lambda d:d["targets"].update({"OriginalProof.reifies":"ReachReifies"})
        negative(case+"-moved-old-owner",lambda:a.validate_graph(changed(row,own),old["targets"]),"historical targets")
        bad=lambda d:d["required_uses"].update({"OriginalProof.preserves":["OriginalReach.fullEvaluation"]})
        negative(case+"-bypassed-dynamic-helper",lambda:a.validate_graph(changed(row,bad),old["targets"]),"distinct dynamic helper")
        orphan=lambda d:d["targets"].update({"Injected.orphan":"ReachCalls"})
        negative(case+"-unconsumed-helper",lambda:a.validate_graph(changed(row,orphan),old["targets"]),"unconnected")
        def cycle(d):
            d["required_uses"]["OriginalReach.covered"].append("OriginalReach.covered")
        negative(case+"-circular-coverage",lambda:a.validate_graph(changed(row,cycle),old["targets"]),"cycle")
        gap=copy.deepcopy(intervals);gap[1][0]+=1
        overlap=copy.deepcopy(intervals);overlap[1][0]-=1
        for label,bad_intervals in (("gap",gap),("overlap",overlap),("reverse",list(reversed(intervals)))):
            negative(case+"-"+label,lambda b=bad_intervals:route.check_intervals(b,row["source_plan"]["count"]),"interval cover")
        negative(case+"-missing-terminal-interval",lambda:route.check_intervals(intervals[:-1],row["source_plan"]["count"]),"complete interval")
        negative(case+"-no-native-trace",lambda:read.finite_rows(case,{"rows":[]}),"one native record")
        summary[case]={"old_targets":len(old["targets"]),"new_and_original_targets":len(targets),
                      "public_types_reused":len(row["old_public_type_sha256"]),"fixed_term_type_checks":len(row["independently_declared_signature_checks"]),
                      "isolated_propositions":sum(len(v) for v in row["individual_lemma_templates"].values()),
                      "ordinary_fresh_modules":len(row["ordinary_order"]),"original_evaluations":0}

    # Synthetic sources and observations for the exact new checker paths.
    artificial=out/"artificial";artificial.mkdir()
    (artificial/"Common.lean").write_text("def tiny : Bool := true\n")
    (artificial/"Unit.lean").write_text("import Common\nexample : True := True.intro\n")
    sources=a.tree_hashes(artificial);objects={"Common.olean":"a"*64}
    incoming=read.inputs(a,artificial,"Unit",objects,sources,"synthetic")
    a.require(incoming["direct_local_imports"]==objects,"synthetic direct import positive")
    negative("missing-compiled-input",lambda:read.inputs(a,artificial,"Unit",{},sources,"synthetic"),"missing local import")
    negative("changed-saved-source",lambda:read.inputs(a,artificial,"Unit",objects,{"Unit.lean":"0"*64},"synthetic"),"source changed")
    example="import Base\n\ntheorem Toy.A : True := by\n@@PROOF Toy.A@@\n\n#print axioms Toy.A\n"
    isolated=route.isolated_statements(example)
    a.require(list(isolated)==["Toy.A"] and isolated["Toy.A"]==example,"single-lemma exact fixture")
    negative("wrong-isolated-name",lambda:route.isolated_statements(example.replace("@@PROOF Toy.A","@@PROOF Toy.B")),"named proof slot")
    negative("duplicate-isolated-name",lambda:route.isolated_statements(example+example),"named proof slot")
    a.require(proof.fill({"Toy":example},{"Toy.A":["trivial"]},["Toy.A"]).get("Toy") is not None,"inert proof-fill control")
    negative("unsafe-proof",lambda:proof.script(["exact sorryAx"]),"unregistered proof language")
    negative("unsound-native-proof",lambda:proof.script(["exact native_decide"]),"unregistered proof language")
    negative("extra-proof-slot",lambda:proof.fill({"Toy":example},{"Toy.A":["trivial"],"Extra":["rfl"]},["Toy.A"]),"exact roster")
    negative("missing-proof-slot",lambda:proof.fill({"Toy":example},{},["Toy.A"]),"exact roster")
    f=out/"invented-kernel-record.jsonl"
    def fake(constants):
        f.write_text(common.PREFIX+json.dumps({"name":"Toy.use","value_constants":constants})+"\n")
    fake(["Toy.result","Toy.method"])
    row={"targets":{"Toy.use":"Toy"},"required_uses":{"Toy.use":["Toy.result","Toy.method"]}}
    a.require(read.dependency_rows(f,row,common,{"checked":1})["Toy.use"]["required"]==["Toy.result","Toy.method"],
              "invented positive direct-edge record")
    fake(["Toy.method"])
    negative("accepted-type-with-missing-body-edge",lambda:read.dependency_rows(f,row,common,{"checked":1}),"missing direct proof")
    negative("source-axioms-differ",lambda:read.checkpoints_against_final({"M":{"Toy.q":["propext"]}},
             {"declarations":{"Toy.q":{"axioms":[]}}}),"axiom disagreement")
    negative("forged-transitive-axiom",lambda:common.verify_axioms(artificial/"Unit.lean",["Toy.use"],set(driver.ALLOWED)),
             "unexpected compiler diagnostic")
    ax=out/"invented-unapproved-axiom.txt";ax.write_text("'Toy.q' depends on axioms: [Toy.bad]\n")
    negative("unapproved-registered-format-axiom",lambda:common.verify_axioms(ax,["Toy.q"],set(driver.ALLOWED)),"unexpected transitive axiom")
    parent="d"*40;child="e"*40;digest="f"*64
    ref="refs/heads/review/original-reachable-v3/"+parent+"-"+digest
    event={"before":"0"*40,"after":child,"ref":ref,"created":True,"deleted":False}
    driver.trigger("push",ref,child,parent,digest,event)
    for label,k,v in (("old-ref","created",False),("wrong-before","before","1"*40),
                      ("wrong-after","after","0"*40),("deleted","deleted",True)):
        negative("host-"+label,lambda k=k,v=v:driver.trigger("push",ref,child,parent,digest,{**event,k:v}),"first creation")
    negative("manual-dispatch",lambda:driver.trigger("workflow_dispatch",ref,child,parent,digest,event),"first reserved push")
    negative("short-branch",lambda:driver.trigger("push",ref[:-1],child,parent,digest,event),"registration identities")
    negative("duplicate-json-member",lambda:a.pairs([("a",1),("a",2)]),"duplicate JSON key")
    native_template=HERE/"run.py"
    for f in (HERE/"assembly.py", HERE/"route.py", HERE/"readback.py",native_template,HERE/"qualification.py"):
        compile(f.read_text(),str(f),"exec")
    limits=driver.LIMITS
    a.require(limits=={"campaign_seconds":18000,"subprocess_seconds":900,"retained_bytes":1073741824,"group_rss_bytes":4294967296}
              and driver.schedule.SCHEDULE["case_seconds"]==5400 and driver.ALLOWED==["Classical.choice","Quot.sound","propext"],"unchanged original resource and axiom contracts")
    new=load(HERE/"schedule_controls.py").check(driver.schedule,a,out)
    a.write(out/"schedule-RESULT.json",new)
    a.write(out/"RESULT.json",{"schema":1,"status":"source and invented operational controls accepted",
                               "cases":summary,"negative_count":len(statuses),"controls":statuses,
                               "native_original_runs":0,"original_outputs_evaluated":0,"candidate_files_opened":0,
                               "manifest_sha256":manifest,"python_optimization":sys.flags.optimize})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("repo","output","source_output"):
        parser.add_argument(name,type=Path)
    parser.add_argument("manifest")
    args=parser.parse_args()
    main(args.repo.resolve(),args.output.resolve(),args.source_output.resolve(),args.manifest)
