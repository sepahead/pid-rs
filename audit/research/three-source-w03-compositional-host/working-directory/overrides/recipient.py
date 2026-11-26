"""Reconstruct exact official source, stage schedule and judgments from the independently held directory."""
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import HERE,decode,digest,hash_bytes,require,same,seal
from controls import check as source_controls
from environment import require_environment
from containment import DROP,GUEST_CHECK,recipe
from judge import PLAN,fixed_sources,input_file,snapshots,validate_ticket
from modules import files
from observer import refs
from receipt import read,trace_read
from terms import STAGES,mock_raw

def verify(root,field,mode,run,qualified=None,ticket=None,payload_sha=None,qualified_readback=None):
    seal(field)
    terminal=decode((root/'terminal.json').read_bytes())
    require(terminal['pass'] is True and terminal['mode']==mode and terminal['run']==run and terminal['field']==field and same(terminal['plan'],PLAN) and 0<terminal['elapsed_seconds']<=5400,'terminal identity and budget')
    require(terminal['reader_controls']==digest(root/'reader-controls.json') and same(source_controls(),decode((root/'reader-controls.json').read_bytes())),'fixed source/control readback')
    provider=terminal['provider'];stock=decode((HERE/'stock.json').read_bytes())
    require(provider['archive_sha256']==stock['archive_sha256'] and provider['lean']==stock['lean_sha256'] and provider['leanchecker']==stock['leanchecker_sha256'] and provider['revision']==stock['lean_revision'] and provider['single_cpu'] is True,'known released provider')
    require(0<provider['hard_cgroup_bytes']<=PLAN['group_rss_bytes'] and type(provider['lib64']) is bool and type(provider['ldcache']) is bool,'hard resource and system closure')
    external=terminal['native_paths'];native_root=Path(external['root']);store=Path(external['store'])
    require(native_root.is_absolute() and store.is_absolute() and not native_root.is_relative_to(store) and not store.is_relative_to(native_root),'independent native paths')
    rows=terminal['commands']; cursor=0
    def runrow(tag,stage,args,rc,verbose):
        nonlocal cursor
        require(cursor<len(rows),'missing scheduled call');r=rows[cursor];cursor+=1
        require(r['tag']==stage+'-'+tag and r['stage']==stage and r['exit']==rc and r['stop'] is None and r['post_group_absent'] is True,'native command status')
        path=native_root/stage
        frozen=recipe(provider['bubblewrap_path'],provider['lib64'],provider['ldcache'],store,path/'sources',path/'objects',path/'new',args)
        require(r['argv']==frozen,'entire frozen command and mount graph')
        words=r['argv'];cut=max(i for i,x in enumerate(words) if x=='--')
        require(words[cut+1:]==args and words[cut-len(DROP)+1:cut+1]==DROP,'native command or lowered identity')
        require(all(x in words[:cut] for x in ('--unshare-net','--unshare-pid','--unshare-uts','--clearenv','--remount-ro','--die-with-parent')),'native namespaces')
        require(0<r['elapsed_seconds']<=900 and r['max_observed_group_rss_bytes']<=PLAN['group_rss_bytes'] and r['direct_wait4_maxrss_bytes']<=PLAN['group_rss_bytes'] and r['retained_before_receipt_bytes']<=PLAN['retained_bytes'],'command resources')
        dirname=root/'commands'/r['tag']
        require(same(decode((dirname/'result.json').read_bytes()),r),'per-command receipt equality')
        for stream in ('stdout','stderr'):
            p=dirname/stream
            require(p.stat().st_size==r[stream+'_bytes'] and digest(p)==r[stream+'_sha256'],'native stream identity')
        require(r['stderr_bytes']==0 and (r['stdout_bytes']>0)==verbose,'native stream conditions')
        return (dirname/'stdout').read_bytes()
    def stage(label,mode,payload,base=None):
        sci=mode=='science';auth=payload is None; path=root/label;src=fixed_sources(mode,payload)
        require({p.name for p in (path/'sources').iterdir()}=={k+'.lean' for k in src} and all((path/'sources'/(k+'.lean')).read_text()==s for k,s in src.items()),'frozen sources')
        h=decode(runrow('containment',label,['/usr/bin/python3','-I','-S','-B','-c',GUEST_CHECK],0,True))
        require_environment(h.get('environment'),h.get('working_directory'))
        require(h['uid']==h['gid']==65534 and h['caps']==0 and h['no_new_privs']==1 and h['read_only'] is True and h['write_control'] is True,'guest')
        built=[]
        def objects():
            roster=snapshots(path/'objects')
            require(same(roster,decode((path/'products.json').read_bytes())) and {n+'.olean' for n in built}<=set(roster) and set(roster)<={n+s for n in built for s in ('.olean','.olean.private','.olean.server','.ir')} and not list((path/'new').iterdir()),'retained immutable module bytes')
        for n in files(mode,payload):
            neg=mode=='negative' and n=='W03Complete'
            msg=runrow('compile-'+n,label,['/stock/bin/lean','-j1','-DwarningAsError=true','-o','/out/'+n+'.olean',n+'.lean'],1 if neg else 0,neg)
            if neg:
                require((b'type mismatch' in msg.lower() or b'has type' in msg.lower()) and b'true' in msg.lower() and (b'false' in msg.lower() or b'w03scope.complete' in msg.lower()) and not (path/'objects'/(n+'.olean')).exists(),'false control causal refusal')
                objects();return {'mode':'negative','rejected_at':'W03Complete','stdout_sha256':hash_bytes(msg)}
            built.append(n)
            require((path/'objects'/(n+'.olean')).is_file(),'missing compiled module')
            runrow('fresh-'+n,label,['/stock/bin/leanchecker','--fresh',n],0,False)
        objects()
        def query(n):return runrow(n,label,['/stock/bin/lean','-j1','-DwarningAsError=true',n+'.lean'],0,True)
        value=read(query('AuditRecords'),query('AuditAxioms'),sci,auth,base)
        if sci and not auth:value['trace']=trace_read(query('AuditTrace'))
        require(same(value,decode((path/'readback.json').read_bytes())),'reconstructed observation')
        return value
    if mode=='qualify':
        a=stage('original-authority','science',None);m=stage('toy-authority','positive',None)
        stage('toy-accept','positive',mock_raw(),m);negative=stage('toy-reject','negative',mock_raw())
        require(same(a,terminal['scientific_authority']) and terminal['source_qualified_only'] is True and same(negative,terminal['negative']),'qualified full input, no scientific proof')
    else:
        q,qs=qualified;t,ts=ticket
        rec,rs=qualified_readback
        require(t['qualification_recipient_sha256']==rs==terminal['qualification_recipient_sha256'] and rec['verified'] is True and rec['field']==field and rec['mode']=='qualify' and rec['terminal_sha256']==qs and rec['run']==q['run'],'external qualification readback')
        validate_ticket(t,field,qs);require(q['pass'] is True and q['mode']=='qualify' and q['field']==field and same(q['provider'],provider) and (ts,qs,payload_sha)==(terminal['ticket_sha256'],terminal['qualification_sha256'],terminal['payload_sha256']),'issued proof, delivery and official qualification bindings')
        raw=input_file(root/'submitted.json',payload_sha);a=stage('original-authority','science',None)
        require(same(a,q['scientific_authority']),'scientific authority drift');stage('original-submission','science',raw,a)
    require(cursor==len(rows) and {p.name for p in (root/'commands').iterdir()}=={x['tag'] for x in rows},'no missing or extra command')
    return {'field':field,'mode':mode,'run':run,'verified':True,'commands':cursor,'terminal_sha256':digest(root/'terminal.json')}
def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('qualify','score'));p.add_argument('--root',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--field-sha',required=True)
    for k in ('qualified','qualified-readback','ticket'):p.add_argument('--'+k,type=Path);p.add_argument('--'+k+'-sha')
    p.add_argument('--payload-sha');a=p.parse_args()
    if a.mode=='score':
        require(all((a.qualified,a.qualified_sha,a.ticket,a.ticket_sha,a.qualified_readback,a.qualified_readback_sha,a.payload_sha)),'separate anchors for score')
    def meta(p,h):return (decode(input_file(p,h)),h) if p else None
    x=verify(a.root,a.field_sha,a.mode,a.run_id,meta(a.qualified,a.qualified_sha),meta(a.ticket,a.ticket_sha),a.payload_sha,meta(a.qualified_readback,a.qualified_readback_sha))
    import json
    print(json.dumps(x,sort_keys=True))
if __name__=='__main__':main()
