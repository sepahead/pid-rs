"""Phase-gated official field judge. A score requires an independent ticket and receipt."""
import argparse
import os
from pathlib import Path
import re
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import HERE,canonical,decode,digest,hash_bytes,require,same,seal,write
from controls import check as source_controls
from containment import box,GUEST_CHECK
from modules import files
from native_resources import Campaign,retained_bytes
from observer import axioms,native,trace
from receipt import read,trace_read
from stock import provision
from terms import STAGES,mock_raw,admit

PLAN={'campaign_seconds':5400,'subprocess_seconds':900,'group_rss_bytes':4*1024**3,'retained_bytes':1024**3}
def snapshots(folder):
    require(all(x.is_file() and not x.is_symlink() for x in folder.iterdir()),'unexpected native output type')
    return {x.name:[x.stat().st_size,digest(x)] for x in folder.iterdir()}
def fixed_sources(mode,payload):
    sci=mode=='science';auth=payload is None
    fs=files(mode,payload); fs['AuditRecords']=native(sci,auth); fs['AuditAxioms']=axioms(sci,auth)
    if sci and not auth:fs['AuditTrace']=trace()
    return fs
def run_stage(camp,store,evidence,stage,mode,payload,baseline=None):
    work=evidence/stage;work.mkdir();src=work/'sources';products=work/'objects';out=work/'new'
    for p in (src,products,out):p.mkdir()
    out.chmod(0o777)
    def retain_products(manifest):
        require(snapshots(products)==manifest,'unchanged compiled objects')
        write(work/'products.json',manifest)
    sci=mode=='science';auth=payload is None; fs=fixed_sources(mode,payload)
    for n,s in fs.items():(src/(n+'.lean')).write_text(s)
    src_state=snapshots(src);known={};camp.stage=stage
    def run(label,argv,kind='silent',rc=0):
        require(snapshots(src)==src_state and snapshots(products)==known and not list(out.iterdir()),'inputs or object store changed')
        return camp.run(stage+'-'+label,box(store,src,products,out,argv),src,kind,rc)
    h=decode(run('containment',['/usr/bin/python3','-I','-S','-B','-c',GUEST_CHECK],'stdout').read_bytes())
    require(h['net']!=os.readlink('/proc/self/ns/net') and h['pid']!=os.readlink('/proc/self/ns/pid') and h['uid']==65534 and h['gid']==65534 and h['caps']==0 and h['no_new_privs']==1 and h['read_only'] is True and h['write_control'] is True,'guest protection')
    for name in files(mode,payload):
        expect_failure=(mode=='negative' and name=='W03Complete')
        args=['/stock/bin/lean','-j1','-DwarningAsError=true','-o','/out/'+name+'.olean',name+'.lean']
        streams=run('compile-'+name,args,'stdout' if expect_failure else 'silent',1 if expect_failure else 0)
        if expect_failure:
            text=streams.read_bytes().lower()
            require((b'type mismatch' in text or b'has type' in text) and (b'false' in text or b'w03scope.complete' in text) and not list(out.iterdir()),'toy mathematical refusal absent')
            retain_products(known)
            return {'mode':'negative','rejected_at':'W03Complete','stdout_sha256':digest(streams)}
        names=snapshots(out)
        require(name+'.olean' in names and set(names)<=set(name+s for s in ('.olean','.olean.private','.olean.server','.ir')),'stock compiler output roster')
        for f in out.iterdir():
            dst=products/f.name;require(not dst.exists(),'prior module overwrite');f.rename(dst);dst.chmod(0o444)
        known.update(names)
        # Stock LeanChecker reconstructs the safe declarations in a new kernel environment.
        run('fresh-'+name,['/stock/bin/leanchecker','--fresh',name])
    def query(n):return run(n,['/stock/bin/lean','-j1','-DwarningAsError=true',n+'.lean'],'stdout').read_bytes()
    received=read(query('AuditRecords'),query('AuditAxioms'),sci,auth,baseline)
    if sci and not auth:received['trace']=trace_read(query('AuditTrace'))
    require(snapshots(src)==src_state and snapshots(products)==known and not list(out.iterdir()),'terminal source and object identity')
    retain_products(known)
    write(work/'readback.json',received)
    return received

def input_file(p,expected,limit=64*1024**2):
    require(p.is_file() and 0<p.stat().st_size<=limit and not p.is_symlink() and re.fullmatch(r'[0-9a-f]{64}',expected) and digest(p)==expected,'externally committed input')
    b=p.read_bytes();require(hash_bytes(b)==expected,'input changed while reading');return b
def validate_ticket(ticket,field,qualified):
    required={'id','schema','field','qualification_sha256','qualification_recipient_sha256','purpose','candidate_authority','judge_authority','recipient_authority','terminal_rule','allow_one','frozen_plan'}
    require(set(ticket)==required and ticket['schema']=='w03-compositional-issue-v2' and ticket['field']==field and ticket['qualification_sha256']==qualified and ticket['purpose']=='one prospective original W03 proof' and ticket['terminal_rule']=='one submission, no retry' and ticket['allow_one'] is True and same(ticket['frozen_plan'],PLAN),'wrong registered score fields')
    require(ticket['id']=='W03-compositional-v2-01' and re.fullmatch(r'[0-9a-f]{64}',ticket['qualification_recipient_sha256']) and all(type(ticket[k]) is str and bool(ticket[k].strip()) for k in ('candidate_authority','judge_authority','recipient_authority')) and len({ticket[k] for k in ('candidate_authority','judge_authority','recipient_authority')})==3,'distinct declared writers')
def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mode',choices=('qualify','score'))
    for k in ('archive','store','out'):cli.add_argument('--'+k,type=Path,required=True)
    cli.add_argument('--field-sha',required=True)
    for k in ('ticket','qualified','qualified-readback','payload','once-store'):cli.add_argument('--'+k,type=Path)
    for k in ('ticket-sha','qualified-sha','qualified-readback-sha','payload-sha','run-id'):cli.add_argument('--'+k)
    a=cli.parse_args();seal(a.field_sha)
    os.environ['PATH']='/usr/bin:/bin'
    require(a.store.is_absolute() and a.out.is_absolute(),'absolute fresh host paths')
    require(a.run_id and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',a.run_id),'externally identifiable native run')
    require(os.geteuid()==0 and not a.store.exists() and not a.out.exists(),'operator-only fresh directories')
    roots=[a.store,a.out,HERE]+([a.once_store] if a.once_store else [])
    pairs=[(p.resolve(),q.resolve()) for i,p in enumerate(roots) for q in roots[:i]]
    require(all(not p.is_relative_to(q) and not q.is_relative_to(p) for p,q in pairs),'separate provider, receipt, ledger and field paths')
    for p in (a.archive,a.ticket,a.qualified,a.qualified_readback,a.payload):
        if p is not None:
            require(not any(p.resolve().is_relative_to(x.resolve()) for x in roots),'external supplied files outside fresh roots')
    if a.mode=='score':
        require(all((a.ticket,a.ticket_sha,a.qualified,a.qualified_sha,a.qualified_readback,a.qualified_readback_sha,a.payload,a.payload_sha,a.once_store)),'pre-bound issuance and terminal delivery')
        ticket=decode(input_file(a.ticket,a.ticket_sha)); qualified=decode(input_file(a.qualified,a.qualified_sha))
        validate_ticket(ticket,a.field_sha,a.qualified_sha)
        rec=decode(input_file(a.qualified_readback,a.qualified_readback_sha))
        require(ticket['qualification_recipient_sha256']==a.qualified_readback_sha and rec['verified'] is True and rec['mode']=='qualify' and rec['field']==a.field_sha and rec['terminal_sha256']==a.qualified_sha and rec['run']==qualified['run'],'external recipient qualification')
        require(qualified.get('pass') is True and qualified.get('mode')=='qualify' and qualified.get('field')==a.field_sha,'successful official qualification')
        require(a.once_store.is_dir() and not a.once_store.is_symlink() and a.once_store.stat().st_uid==0 and a.once_store.stat().st_mode&0o022==0,'persistent separate operator-owned attempt ledger')
        # The custodian creates the immutable registration before candidate access; its one-shot receipt is consumed even on failure.
        write(a.once_store/ticket['id'],{'ticket_sha256':a.ticket_sha,'payload_sha256':a.payload_sha,'run':a.run_id})
    else:require(not any((a.ticket,a.ticket_sha,a.qualified,a.qualified_sha,a.qualified_readback,a.qualified_readback_sha,a.payload,a.payload_sha,a.once_store)),'qualification must be candidate-free')
    a.out.mkdir(mode=0o755);clock=time.monotonic();receipt={'mode':a.mode,'run':a.run_id,'field':a.field_sha,'pass':False,'plan':PLAN,'native_paths':{'store':str(a.store.resolve()),'root':str(a.out.resolve())}};camp=None
    try:
        checks=source_controls();write(a.out/'reader-controls.json',checks);receipt['reader_controls']=digest(a.out/'reader-controls.json')
        provider=provision(a.archive,a.store);receipt['provider']=provider
        camp=Campaign(a.out,clock,dict(PLAN),{'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8'},digest)
        if a.mode=='qualify':
            fixed=run_stage(camp,a.store,a.out,'original-authority','science',None)
            mock=run_stage(camp,a.store,a.out,'toy-authority','positive',None)
            run_stage(camp,a.store,a.out,'toy-accept','positive',mock_raw(),mock)
            refusal=run_stage(camp,a.store,a.out,'toy-reject','negative',mock_raw())
            receipt.update(scientific_authority=fixed,source_qualified_only=True,negative=refusal)
        else:
            payload=input_file(a.payload,a.payload_sha,8*1024**2);admit(payload);(a.out/'submitted.json').write_bytes(payload)
            require(same(provider,qualified['provider']),'provider or runtime identity differs from qualification')
            refreshed=run_stage(camp,a.store,a.out,'original-authority','science',None)
            require(same(refreshed,qualified['scientific_authority']),'qualified source readback drift')
            run_stage(camp,a.store,a.out,'original-submission','science',payload,refreshed)
            receipt.update(ticket_sha256=a.ticket_sha,qualification_sha256=a.qualified_sha,qualification_recipient_sha256=a.qualified_readback_sha,payload_sha256=a.payload_sha)
        require(time.monotonic()-clock<=PLAN['campaign_seconds'] and retained_bytes(a.out)<PLAN['retained_bytes'],'aggregate limit')
        receipt['pass']=True
    except BaseException as ex:
        receipt['failure']=str(ex) or type(ex).__name__;raise
    finally:
        receipt['elapsed_seconds']=time.monotonic()-clock
        if camp:receipt['commands']=camp.commands
        write(a.out/'terminal.json',receipt)
if __name__=='__main__':main()
