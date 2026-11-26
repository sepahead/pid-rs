"""Reopen the original default-free Rust library and compile the LP4 client once."""
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

parent = Path(__file__).resolve().parent
pub = parent/"portable"
frozen = json.loads((parent/"FROZEN.json").read_bytes())
def need(value, msg):
    if not value: raise RuntimeError(msg)
def digest(data): return hashlib.sha256(data).hexdigest()
def filehash(file):
    with file.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()
for name, sha in frozen["frozen_files"].items():
    need(filehash(parent/name)==sha, "altered frozen file " + name)
repo, original, archive, compiler, out = [Path(t).resolve() for t in sys.argv[1:]]
out.mkdir(exist_ok=False)
source=json.loads((pub/"original-shai-source.json").read_bytes())
oldbuild=original/"builds/01"
compilelog=oldbuild/"compile.stdout"
need(filehash(compilelog)==frozen["original_compile_stdout"],"original Cargo stream")
need(filehash(compiler)==frozen["compiler_sha"],"original pinned compiler")
args=["git","--no-optional-locks","-C",str(repo)]
need(subprocess.check_output(args+["rev-parse",source["git"]+"^{tree}"]).decode().strip()==source["tree"],"source original")
raw=subprocess.check_output(args+["cat-file","--batch"],input="".join(source["git"]+":"+k+"\n" for k in source["files"]).encode())
stream=io.BytesIO(raw)
for path,sha in source["files"].items():
    _,kind,length=stream.readline().split()
    content=stream.read(int(length))
    need(kind==b"blob" and digest(content)==sha==filehash(oldbuild/"work"/path) and stream.read(1)==b"\n","source bytes "+path)
need(not stream.read(1),"Git byte stream completely consumed")
deps=oldbuild/"target/debug/deps"
for name,sha in frozen["native_dependency_bytes"].items():
    need(filehash(deps/name)==sha,"initial dependency byte "+name)
libs={}
for line in compilelog.read_text().splitlines():
    j=json.loads(line)
    if j.get("reason")=="compiler-artifact" and j["target"]["name"] in ("pid_core","serde_json"):
        need(j["features"]==([] if j["target"]["name"]=="pid_core" else ["default","std"]),"actual original features")
        chosen=[Path(s) for s in j["filenames"] if s.endswith(".rlib")]
        need(len(chosen)==1 and chosen[0].parent==deps,"actual original library artifact")
        libs[j["target"]["name"]]=chosen[0]
need(set(libs)=={"pid_core","serde_json"},"two actual library artifacts")
env={k:os.environ[k] for k in ("HOME","PATH","TMPDIR","SDKROOT","DEVELOPER_DIR") if k in os.environ}
env.update(CARGO_NET_OFFLINE="true",LLVM_PARALLEL_LINK_JOBS="1",LC_ALL="C",TZ="UTC")
ops={}
def command(label,words,stdin=None,negative=False):
    t=time.monotonic()
    r=subprocess.run(words,input=stdin,capture_output=True,timeout=90,env=env,check=False)
    (out/(label+".stdout")).write_bytes(r.stdout)
    (out/(label+".stderr")).write_bytes(r.stderr)
    ops[label]={"seconds":time.monotonic()-t,"status":r.returncode,"stdout":digest(r.stdout),"stderr":digest(r.stderr)}
    (out/"OPERATIONS.json").write_text(json.dumps(ops,indent=2,sort_keys=True)+"\n")
    need((r.returncode!=0)==negative,label)
    if not negative: need(not r.stderr,label+" unexpected stderr")
    return r

client=out/"lp4-categorical-client"
command("compile",[str(compiler),"--edition=2021","--crate-name","lp4_categorical_client",
    "-C","debuginfo=0","-L","dependency="+str(deps),"--extern","pid_core="+str(libs["pid_core"]),
    "--extern","serde_json="+str(libs["serde_json"]),str(pub/"measurement.rs"),"-o",str(client)])
previous=json.loads((oldbuild/"BUILT.json").read_bytes())
oldbin=next(p for p in (oldbuild/"target/debug").iterdir() if p.is_file() and p.suffix=="" and filehash(p)==previous["binary_sha256"])
for name,flags in (("ordinary",[]),("optimized",["-O"])):
    row=command(name+"-rows",[sys.executable,*flags,"-I","-S","-B",str(pub/"compare.py"),str(archive)])
    args0=[sys.executable,*flags,"-I","-S","-B",str(pub/"compare.py"),str(archive),
           "--rows",str(out/(name+"-rows.stdout")),"--native",str(out/(name+"-native.stdout"))]
    command(name+"-native",[str(client)],row.stdout)
    command(name+"-scientific",args0)
    command(name+"-controls",[sys.executable,*flags,"-I","-S","-B",str(pub/"controls.py"),
            str(out/(name+"-native.stdout")),str(archive)])
    if name=="ordinary":
        rows=json.loads(row.stdout)
        base=command("previous-native-fixed-width-refusal",[str(oldbin)],json.dumps({"10":rows,"50":rows,"100":rows}).encode(),True)
        need(b"expected one row per measured stimulus setting" in base.stderr,"original 651 cutoff")
        wrong=[r.copy() for r in rows]; wrong[0][3]=1-wrong[0][3]
        need(b"copied force target" in command("actual-native-wrong-target",[str(client)],json.dumps(wrong).encode(),True).stderr,"native copied-target refusal")
        need(b"117 source episodes" in command("actual-native-116",[str(client)],json.dumps(rows[:-1]).encode(),True).stderr,"native 117 cutoff")
for suffix in ("rows","native","scientific","controls"):
    need((out/("ordinary-"+suffix+".stdout")).read_bytes()==(out/("optimized-"+suffix+".stdout")).read_bytes(),suffix)
receipt={"frozen":filehash(parent/"FROZEN.json"),"client_binary_sha256":filehash(client),"original_closure_files":len(source["files"]),
         "verified_old_objects":len(frozen["native_dependency_bytes"]), "original_shai_binary":previous["binary_sha256"],
         "positive_roster":[source["git"],source["tree"],filehash(pub/"measurement.rs")],
         "scientific":filehash(out/"ordinary-scientific.stdout"),"native":filehash(out/"ordinary-native.stdout"),
         "source_rows":filehash(out/"ordinary-rows.stdout"),"controls":filehash(out/"ordinary-controls.stdout"),
         "operations":ops}
(out/"RETURN.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
