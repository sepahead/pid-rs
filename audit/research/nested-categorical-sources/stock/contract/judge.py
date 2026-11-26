"""Stock replay of the pre-bound nested event statements and a real wrong evaluation."""
from hashlib import file_digest
import importlib.util,json,os,re,shutil,subprocess,sys
from pathlib import Path
REG=Path(__file__).resolve().parent
TC=Path(sys.argv[3]).resolve(strict=True)
spec=importlib.util.spec_from_file_location("restricted_nested_proof",REG/"interface.py")
restrict=importlib.util.module_from_spec(spec);spec.loader.exec_module(restrict)
need=restrict.require
names=("branch_reaches","suffix_incidence","branch_matches","node_matches","event_extensional","cumulative_sum")
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
        image=restrict.build((REG/"Proof.template").read_text(),json.loads(candidate.read_bytes()))
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
                    key="Nested."+ident
                    e=re.findall(r"'"+re.escape(key)+r"' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)",report)
                    need(len(e)==1,("axiom record",key))
                    vals=set(e[0].split(", ")) if e[0] else set()
                    need(vals<=allowed,(key,vals));axioms[key]=sorted(vals)
                    need(re.search(r"(?:^|\n)theorem "+re.escape(key)+r"\b",report) is not None,("term",key))
            else:need(not report.strip(),("ordinary compiler output",name))
            fresh=run(name+"-fresh",[TC/"bin/leanchecker","--fresh",name])
            need(not fresh.strip(),("fresh replay",name))
        bad=run("negative",[*compiler,"Contradiction.lean"],True)
        need(re.fullmatch(r"Contradiction\.lean:4:[0-9]+: error: Tactic \x60decide\x60 proved that the proposition\n\s*mixed\.level = 3\nis false\n",bad) is not None,("intended false proposition",bad))
        check_tree(REG,frozen);check_tree(TC,runtime)
        save(True,None);print("PASS six named nested event and integer telescoping declarations plus stock negative control")
    except BaseException as e:
        save(False,str(e));raise
if __name__=="__main__":main()
