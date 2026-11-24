"""Reproduce the five robot tables from the certificate or from the five original UCI members."""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import io
import json
from pathlib import Path
import stat
import sys
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from calculation import calculate, from_counts, fractional, need, summary

SCHEMA="uci138-axial-signs-v1"
CERT_SHA="94ba9611a6fb38c8df5c1e3aa8ff798149649e729bc4b9b02ecd960ba45c219c"
RESULT_SHA="0f328136c8acebd081cc3f7254bfc1887ed3c20ec12f741c5eaca2e26826de5e"
ARCHIVE_LIMIT=1024*1024

def sha(b):
    return sha256(b).hexdigest()

def canonical(x):
    return (json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)+"\n").encode()

def study_product(source,doc):
    report={"schema":"robot-wrist-slope-results-v1","data_doi":source["doi"],"certificate_sha256":sha(canonical(doc)),
            "interval_units":"nanonats per recorded episode; inclusive integers","sign":"exact comparison of exp(n V) with one",
            "correct_order":["prior","force","torque","both"],"source_level_order":[-1,0,1],"tasks":[]}
    for meta,task in zip(source["tasks"],doc["tasks"],strict=True):
        report["tasks"].append(dict(summary(task,len(meta["labels"])),donor_task=meta["donor_task"],label_order=meta["labels"]))
    return report

def read_members(source,local,fetch):
    """Return the checked task metadata and original bytes for each of the five UCI files."""
    if fetch:
        with urlopen(Request(source["archive_url"],headers={"User-Agent":"pid-rs-robot-study/1"}),timeout=30) as response:
            final=urlparse(response.geturl())
            need(response.status==200 and final.scheme=="https" and final.hostname=="archive.ics.uci.edu","official UCI source")
            raw=response.read(ARCHIVE_LIMIT+1)
    else:
        need(local.is_file() and local.stat().st_size<=ARCHIVE_LIMIT,"bounded local UCI archive")
        raw=local.read_bytes()
    need(0<len(raw)==source["archive_bytes"]<=ARCHIVE_LIMIT and sha(raw)==source["archive_sha256"],"official zip commitment")
    output=[]
    with ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        for task in source["tasks"]:
            name=task["name"]
            need(name in {f"lp{i}.data" for i in range(1,6)} and names.count(name)==1,"one direct data member")
            info=archive.getinfo(name)
            mode=(info.external_attr>>16)&0xffff
            need(not info.is_dir() and not stat.S_ISLNK(mode) and info.file_size==task["bytes"]<=131072,"regular input member")
            with archive.open(info) as member: data=member.read(131073)
            need(len(data)==task["bytes"] and sha(data)==task["sha256"],"fixed data-member bytes")
            output.append((task,data))
    return output

def load_source(source,local,fetch):
    return {"schema":SCHEMA,"tasks":[calculate(data,task) for task,data in read_members(source,local,fetch)]}

def replay_table(source,cert):
    need(cert["schema"]==SCHEMA and len(cert["tasks"])==len(source["tasks"])==5,"full registered field")
    result=[]
    for task,meta in zip(cert["tasks"],source["tasks"],strict=True):
        k=len(meta["labels"])
        cells=task["counts"]
        need(task["id"]==meta["id"] and len(cells)==9*k and all(type(x) is int and x>=0 for x in cells),"dense count extent")
        counts=Counter({(i//(3*k)-1,(i//k)%3-1,i%k):x for i,x in enumerate(cells) if x})
        result.append(from_counts(counts,meta))
    return {"schema":SCHEMA,"tasks":result}

def self_test():
    m={"id":"artificial","n":4,"labels":["a","b"]}
    def lines(entries):
        groups=[]
        for f,q,y in entries:
            row=[m["labels"][y]]
            for j in range(-7,8):
                row.append(f"0 {j} {42+j*f+j*j} {-j} 0 {13+j*q-j*j}")
            groups.append("\n".join(row))
        return "\n".join(groups).encode()
    pairs=[(-1,-1),(-1,1),(1,-1),(1,1)]
    for description,labels,unique in (("force",[0,0,1,1],(Fraction(3,2)**4,Fraction(3,4)**4)),
                                      ("torque",[0,1,0,1],(Fraction(3,4)**4,Fraction(3,2)**4))):
        x=calculate(lines([(f,q,y) for (f,q),y in zip(pairs,labels)]),m)
        need(tuple(fractional(x["log_products"][key]) for key in ("unique_f","unique_q"))==unique,description+" signed unique atoms")
    xor=[(f,q,int(f!=q)) for f,q in pairs]
    a=calculate(lines(xor),m)
    need(fractional(a["log_products"]["redundant"])==Fraction(2,3)**4 and a["correct"]==[2,2,2,4],"XOR law and modal ties")
    need(a==calculate(lines(xor[::-1]),m),"whole episode permutation")
    constant=calculate(lines([(0,q,0) for f,q in pairs]),m)
    need(all(x==[] for x in constant["log_products"].values()) and constant["correct"]==[4]*4 and
         summary(constant,2)["zero_force"]==4,"one class and nonconstant zero trend")
    damaged=lines(xor).replace(b"0 -7",b"invalid",1)
    try:calculate(damaged,m)
    except ValueError:return
    raise ValueError("malformed episode was accepted")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group()
    g.add_argument("--archive",type=Path,help="verify and use a locally saved original UCI ZIP")
    g.add_argument("--fetch",action="store_true",help="fetch the official bounded ZIP over HTTPS")
    p.add_argument("--self-test",action="store_true",help="also exercise known synthetic laws and a malformed input")
    a=p.parse_args()
    src=json.loads((HERE/"sources.json").read_bytes())
    cert_bytes=(HERE/"certificate.json").read_bytes()
    need(sha(cert_bytes)==CERT_SHA,"published exact certificate identity")
    if a.self_test:self_test()
    mode="published counts"
    if a.archive or a.fetch:
        mode="five original data members"
        restored=load_source(src,a.archive,a.fetch)
    else:
        restored=replay_table(src,json.loads(cert_bytes))
    need(canonical(restored)==cert_bytes,"complete exact certificate mismatch")
    calculated=study_product(src,restored)
    published=(HERE/"results.json").read_bytes()
    need(sha(published)==RESULT_SHA and json.loads(published)==calculated,"all signs, decimal intervals and descriptive outputs")
    print(canonical({"mode":mode,"tasks":5,"cells":189,"log_products":65,"modal_counts":20,"certificate_sha256":CERT_SHA,
                     "results_sha256":RESULT_SHA,"self_test":a.self_test,"status":"pass"}).decode(),end="")

if __name__=="__main__":main()
