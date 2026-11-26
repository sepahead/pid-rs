"""Stock replay of the fixed finite logarithm recurrence and a false upper power."""
from hashlib import file_digest
import importlib.util,json,os,re,shutil,subprocess,sys
from pathlib import Path
REG=Path(__file__).resolve().parent
TC=Path(sys.argv[3]).resolve(strict=True)
spec=importlib.util.spec_from_file_location("restricted_natural_proof",REG/"interface.py")
restrict=importlib.util.module_from_spec(spec);spec.loader.exec_module(restrict)
need=restrict.need
names=('ceil_upper', 'signed_ceiling', 'initial_interval', 'product_lower', 'product_upper', 'product_interval', 'term_interval', 'add_interval', 'square_steps', 'odd_power_step', 'all_prefixes', 'returned_finite', 'scheduled')
allowed={"Classical.choice","propext","Quot.sound"}
def h(p):
    with p.open("rb") as f:return file_digest(f,"sha256").hexdigest()
def check_tree(path,pins):
    for n,hexdigest in pins.items():
        f=path/n
        need(f.is_file() and not f.is_symlink() and h(f)==hexdigest,n)
def main():
    candidate=Path(sys.argv[1]).resolve()
    dest=Path(sys.argv[2]).resolve()
    dest.mkdir(parents=False,mode=0o700,exist_ok=False)
    records=[];axioms={}
    frozen=json.loads((REG/"FROZEN.json").read_bytes())
    runtime=json.loads((REG/"RUNTIME.json").read_bytes())
    src=dest/"sources";objects=dest/"objects"
    def save(ok,reason):
        j=dict(success=ok,reason=reason,payload=h(candidate),fixed=h(REG/"FROZEN.json"),commands=records,
               axioms=axioms,sources={f.name:h(f) for f in sorted(src.glob("*")) if f.is_file()},
               objects={f.name:h(f) for f in sorted(objects.glob("*")) if f.is_file()})
        (dest/"RESULT.json").write_text(json.dumps(j,indent=2,sort_keys=True)+"\n")
    try:
        check_tree(REG,frozen);check_tree(TC,runtime)
        need(candidate.is_file() and not candidate.is_symlink() and candidate.stat().st_size<262144,"payload")
        src.mkdir();objects.mkdir()
        for n in ("Model.lean","Observer.lean","Contradiction.lean"):
            shutil.copyfile(REG/n,src/n)
        import runpy
        source=runpy.run_path(str(REG/"arithmetic.py"))
        cases=json.loads((REG/"fixtures.json").read_bytes())
        for n,d,s,l,u in cases:
            need(source["atanh_log_bounds"](n,d,s)==(l,u),("actual Python control",n,d,s))
        l,u=source["atanh_log_bounds"](1,3,280)
        need(u-l==106,"tail allowance and interval width")
        template=(REG/"Proof.template").read_text()
        safe={slot:["rfl"] for slot in restrict.SLOTS}
        cases=[{"upper":["sorry"]},{"upper":["native_decide"]},{"upper":["axiom extra : False"]},
               {"upper":["run_tac pure ()"]},{"upper":["import Extra"]},{"upper":["unsafe def counterfeit := 0"]},
               {"upper":["exact False.elim sorryAx"]},{"upper":["rfl\n#print axioms bogus"]}]
        for form in cases:
            try:restrict.render(restrict.canonical(dict(safe,**form)),template)
            except restrict.Refusal:pass
            else:raise ValueError("proof-grammar control")
        image=restrict.render(candidate.read_bytes(),(REG/"Proof.template").read_text())
        (src/"Proof.lean").write_text(image)
        env={"HOME":str(dest),"PATH":str(TC/"bin")+":/usr/bin:/bin","LEAN_PATH":str(objects),"LC_ALL":"C","TZ":"UTC"}
        def run(name,args,wrong=False):
            cp=subprocess.run(list(map(str,args)),cwd=src,env=env,capture_output=True,timeout=80)
            for suffix,data in (("stdout",cp.stdout),("stderr",cp.stderr)):
                (dest/(name+"."+suffix)).write_bytes(data)
            records.append(dict(label=name,argv=[str(a) for a in args],exit=cp.returncode,stdout=h(dest/(name+".stdout")),stderr=h(dest/(name+".stderr"))))
            need(cp.returncode>0 if wrong else cp.returncode==0,name)
            return (cp.stdout+cp.stderr).decode()
        version=run("version",[TC/"bin/lean","--version"])
        need("4.34.1" in version and "5045d005" in version,"stock version")
        compiler=[TC/"bin/lean","-j","1","-DwarningAsError=true","-R",src]
        for name in ("Model","Proof","Observer"):
            report=run(name+"-compile",[*compiler,"-o",objects/(name+".olean"),name+".lean"])
            need((objects/(name+".olean")).is_file(),"missing object")
            if name=="Observer":
                need("sorry" not in report and "⋯" not in report and "..." not in report,"unapproved or elided term")
                for ident in names:
                    key="N2Round."+ident
                    e=re.findall(r"'"+re.escape(key)+r"' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)",report)
                    need(len(e)==1,("axiom record",key))
                    vals=set(e[0].split(", ")) if e[0] else set()
                    need(vals<=allowed,(key,vals));axioms[key]=sorted(vals)
                    need(re.search(r"(?:^|\n)theorem "+re.escape(key)+r"\b",report) is not None,("term",key))
            else:need(not report.strip(),("ordinary compiler output",name))
            fresh=run(name+"-fresh",[TC/"bin/leanchecker","--fresh",name])
            need(not fresh.strip(),("fresh replay",name))
        bad=run("negative",[*compiler,"Contradiction.lean"],True)
        need(re.fullmatch(r"Contradiction\.lean:4:[0-9]+: error: Tactic \x60decide\x60 proved that the proposition\n\s*\(loopState 1 3 2 1\)\.hi = 0\nis false\n",bad) is not None,("intended false proposition",bad))
        check_tree(REG,frozen);check_tree(TC,runtime)
        save(True,None);print("PASS fixed finite prefix, signed ceiling, general recurrence and wrong-direction control")
    except BaseException as e:
        save(False,str(e));raise
if __name__=="__main__":main()
