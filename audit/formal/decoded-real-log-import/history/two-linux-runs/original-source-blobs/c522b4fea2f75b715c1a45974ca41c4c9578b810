"""Local controls on the unchanged source packets and their terminal readers."""
import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe
from bounded import require

def rejected(function, *args):
    try:
        function(*args)
    except (ValueError, FileExistsError):
        return
    raise ValueError("unaccepted alteration: " + function.__name__)

def main():
    pins = json.loads((HERE/"origins.json").read_bytes())
    with tempfile.TemporaryDirectory() as name:
        root = Path(name)
        probe.unpack_stock(HERE/"stock-sources.tar.gz",root,pins)
        require(len(list(root.iterdir()))==30, "all original stock bytes")
        for name in ("JoinAudit","JoinControl","WrongSignedValue"):
            require((root/(name+".lean")).is_file(),name)
        require((root/"JoinControl.lean").read_text().count("#guard")==7,"original guards")
        require((root/"compile-JoinAudit.stdout").read_text().count("depends on axioms:")==7,"original declaration rows")
        rejected(probe.unpack_stock,HERE/"stock-sources.tar.gz",root,pins|{"stock_bundle_sha256":"0"*64})
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode="w:gz") as a:
            bad=tarfile.TarInfo("../Wrong.lean")
            a.addfile(bad,io.BytesIO())
        path=root/"altered.tgz";path.write_bytes(stream.getvalue())
        rejected(probe.unpack_stock,path,root,pins|{"stock_bundle_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        require(not (root.parent/"Wrong.lean").exists(),"no outside file")
    names=probe.REAL_NAMES
    typed="\n".join(n+" : some type" for n in names)
    rows="\n".join("'"+n+"' depends on axioms: [propext, Classical.choice, Quot.sound]" for n in names)
    good=(typed+"\n"+rows+"\n").encode()
    require(len(probe.read_axioms(good,names))==9,"nine independently named diagnostics")
    rejected(probe.read_axioms,good.replace(b"Classical.choice",b"sorryAx",1),names)
    rejected(probe.read_axioms,good.replace(names[0].encode(),b"renamed",1),names)
    rejected(probe.read_axioms,good+rows.splitlines()[0].encode(),names)
    wrong=b"WrongRealValue.lean:3:8: error: Type mismatch\n  Real.log_one\nhas type\n  Real.log 1 = 0\nbut is expected to have type\n  Real.log 1 = 1\n"
    wrong_type="WrongResultType.lean:5:3: error: Type mismatch\n Real.log (A2.make rs l c i).2.2.2\nhas type ℝ but is expected to have type ℕ\n".encode()
    for name,b in (("WrongRealValue",wrong),("WrongResultType",wrong_type)):
        probe.rejected_real(name,b);rejected(probe.rejected_real,name,b.replace(b"Type mismatch",b"unknown constant"))
        rejected(probe.rejected_real,name,b+b)
    rejected(probe.rejected_real,"WrongRealValue",wrong.replace(b"1 = 0",b"1 = 2"))
    rejected(probe.rejected_real,"WrongResultType",wrong_type.replace("ℕ".encode(),b"Bool"))
    # The original hosted negative stopped before the marked expression on line five.
    first_error=":1:0: error: cannot import non-`module` JoinProof from `module`\n"
    for stopped in ("JointRead","WrongResultType"):
        rejected(probe.rejected_real,"WrongResultType",(stopped+".lean"+first_error).encode())

    cached=json.loads(gzip.decompress((HERE/"basic-cache-identities.json.gz").read_bytes()))
    require(len(cached)==9715 and cached["mathlib/Mathlib/Analysis/SpecialFunctions/Log/Basic.olean"]==
            [270064,"b5e6f29c201a62428e3acdeee42aa5292a431d7c01f4c5e8e0f77f3b313ad5fc"],"actual prior object")
    for name in ("BasicRead","JointRead","WrongRealValue","WrongResultType"):
        text=(HERE/(name+".lean")).read_text()
        lines=text.splitlines()
        if name in ("JointRead","WrongResultType"):
            expected_header=["prelude","import JoinProof","import "+probe.BASIC]
        else:
            expected_header=["module","public import "+probe.BASIC]
        require(lines[:len(expected_header)]==expected_header,"exact header and module import order")
        require(all(not re.match(r"(?:public |private |meta )?import ", line)
                    for line in lines[len(expected_header):]),"no later import")
        require(not re.search(r"\b(?:axiom|theorem|def|sorry|unsafe|partial|run_tac|native_decide)\b",text),
                "import-only observer")
    print("Retained 30 original objects, the 9,715 scoped Linux identities, 4 import observers and positive and adverse parser controls.")

if __name__=="__main__":
    main()
