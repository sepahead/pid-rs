"""Verify two previously executed import checks. This process does not compile Lean."""
from hashlib import sha1, sha256
from pathlib import Path
import json
import sys

BASE=Path(__file__).resolve().parent
FIRST='2d74ed32aa6e76fb5b0942d11457b9a061527e26'
SECOND='8c7b04add45b0fa4a4f065e090b9371769c52498'
FIXED={
    FIRST: (45927419805,140271925258,15167541404,'c9d20f9ddb40a72737153b5843d09d188ccb29921c62d10cf76ea81dbeb4b34b','7e4d1177f5b840e55b1716d96c87eea1e75ccc7921ca493d2c581baa17a89caf'),
    SECOND: (45931621691,140285325959,15169141467,'0a5edcb071156bdfb497d234774fc1700488e46b0479b29ae30ea9dbb9757422','b06d55945c9892e9404a610031ce398afffd6afdf002ab07db2a1288d3e3d56f')}
STREAMS=('compile-BasicRead','compile-JoinAudit','compile-JointRead','compile-WrongRealValue','compile-WrongResultType','compile-WrongSignedValue')
def check(value,message):
    if not value:raise ValueError(message)
def digest(data): return sha256(data).hexdigest()
def json_at(path): return json.loads(path.read_bytes())
def verify(root):
    fixed_records={
        'SOURCE-MAP.json':'6661e91b5c2703dc75f43ca421c8eaaddb2a7770a26d8b64831a12fea9c14d90',
        'native/2d74ed32/OUTCOME.json':'51876de0437d7784cb9a3ee109636d682af8b5056120a900393e025e579f3904',
        'native/8c7b04ad/OUTCOME.json':'205a5a775a7fefb7e53e9d3a3239fd683ba1f55aae5c21a156ad6b50de880a60'}
    for name,wanted in fixed_records.items():
        check(digest((root/name).read_bytes())==wanted,name+' identity')
    source=json_at(root/'SOURCE-MAP.json')['source_roles']
    check(set(source)==set(FIXED),'source revisions')
    unique=set()
    for case,meta in source.items():
        paths=meta['paths'];check(len(paths)==13,'source coverage')
        for name,row in paths.items():
            raw=(root/'original-source-blobs'/row['git_blob']).read_bytes()
            check(len(raw)==row['bytes'] and digest(raw)==row['sha256'],name)
            check(sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob'],name)
            unique.add(row['git_blob'])
    check(len(unique)==19 and set(p.name for p in (root/'original-source-blobs').iterdir())==unique,'distinct source blobs')
    check(set(source[FIRST]['paths'])==set(source[SECOND]['paths']) and source[SECOND]['parent']==FIRST,'original direct source relationship')
    changes={p for p,a in source[FIRST]['paths'].items() if a!=source[SECOND]['paths'][p]}
    check(changes=={'.github/workflows/decoded-real-log-import.yml',*('audit/formal/decoded-real-log-import/'+f for f in ('BINDINGS.json','JointRead.lean','README.md','WrongResultType.lean','self_test.py'))},'six original source changes')
    records={}
    for case,expected in FIXED.items():
        where=root/'native'/case[:8];report=json_at(where/'OUTCOME.json');records[case]=report
        found=tuple(report[k] for k in ('run','job','provider_artifact_id','original_provider_archive_sha256','original_result_sha256'))
        check(found==expected and report['source_commit']==case and report['original_provider_members']==114,'original provider identity')
        passed=case==SECOND
        check(report['outcome']==('passed' if passed else 'failed'),'original terminal state')
        commands=report['commands']
        check(len(commands)==report['command_count']==(53 if passed else 52),'native command count')
        for row in commands.values():
            check(set(row)=={'returncode','status','stderr_sha256','stdout_sha256'} and all(len(row[k])==64 for k in ('stderr_sha256','stdout_sha256')),'command record')
        states={k:v['status'] for k,v in report['stages'].items()}
        adverse={k:v for k,v in states.items() if v!='passed'}
        check(len(states)==15 and adverse==({} if passed else {'joint-read':'failed','joint-negative':'failed','joint-fresh':'blocked'}),'native stages')
        check(all(commands[n]['returncode']==0 for n in ('fresh-BasicRead','fresh-JoinAudit')),'separate fresh checks')
        check(('fresh-JointRead' in commands)==passed and (not passed or commands['fresh-JointRead']['returncode']==0),'actual joint fresh check')
        check(commands['compile-JointRead']['returncode']==(0 if passed else 1),'joint compilation')
        check(all(commands[n]['returncode']==1 for n in ('compile-WrongResultType','compile-WrongSignedValue','compile-WrongRealValue')),'scientific controls')
        check(sorted(report['verbatim_streams'])==sorted(n+'.stdout' for n in STREAMS),'scope of native streams')
        stream={}
        for n in STREAMS:
            word=(where/(n+'.stdout')).read_bytes();stream[n]=word
            check(digest(word)==commands[n]['stdout_sha256'],n+' stdout')
        check(b'WrongSignedValue.lean:8:0' in stream['compile-WrongSignedValue'] and b'mkRat 16 9' in stream['compile-WrongSignedValue'],'actual inverted ratio refusal')
        check(b'WrongRealValue.lean:3:7' in stream['compile-WrongRealValue'] and b'Real.log 1 = 0' in stream['compile-WrongRealValue'],'actual false real value refusal')
        if passed:
            check(b'WrongResultType.lean:5:2: error: Type mismatch' in stream['compile-WrongResultType'] and 'ℝ'.encode() in stream['compile-WrongResultType'] and 'ℕ'.encode() in stream['compile-WrongResultType'],'intended type error')
            check(b'A2.Decoded.positive_value' in stream['compile-JointRead'] and b'Real.log' in stream['compile-JointRead'],'joint observer output')
        else:
            check(b'JointRead.lean:1:0: error: cannot import' in stream['compile-JointRead'] and b'WrongResultType.lean:1:0: error: cannot import' in stream['compile-WrongResultType'],'both wrong-location import refusals')
    check(set(records[SECOND]['commands'])==set(records[FIRST]['commands'])|{'fresh-JointRead'},'extra command after import repair')
    return {'original_sources':2,'distinct_git_blobs':len(unique),'original_provider_artifacts':2,'original_command_counts':[52,53],'nonpassing_original_stages':3,'corrected_stages_passed':15,'retained_verbatim_streams':12}
if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1]) if len(sys.argv)>1 else BASE),sort_keys=True))
