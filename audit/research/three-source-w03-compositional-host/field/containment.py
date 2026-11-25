"""Start stock Lean with separated Linux namespaces and read-only, explicit mounts."""
from pathlib import Path
import os
import shutil
from common import require

DROP=['/usr/bin/setpriv','--reuid=65534','--regid=65534','--clear-groups','--no-new-privs','--inh-caps=-all','--ambient-caps=-all','--bounding-set=-all','--']

GUEST_CHECK = '''import errno,json,os,socket
from pathlib import Path
st=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
if os.getuid()!=65534 or os.getgid()!=65534 or any(int(st[k].strip(),16) for k in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb')) or st['NoNewPrivs'].strip()!='1': raise RuntimeError('identity')
if set(os.environ)!={'PATH','LC_ALL','HOME','TMPDIR','LEAN_PATH','LEAN_NUM_THREADS'}: raise RuntimeError('environment')
if any(Path(p).exists() for p in ('/root','/run/credentials','/github','/checkout','/.git','/etc/shadow')): raise RuntimeError('host exposure')
for p in ('/src','/objects','/stock/bin','/libraries','/'):
 try: (Path(p)/'.field_mount_control').write_bytes(b'readonly')
 except OSError as e:
  if e.errno not in (errno.EROFS,errno.EACCES,errno.EPERM): raise
 else: raise RuntimeError('write to '+p)
q=Path('/out/field_write_control');q.write_text('ok');q.unlink()
interfaces=[name for _,name in socket.if_nameindex()]
if any(name!='lo' for name in interfaces): raise RuntimeError('network interfaces')
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
try: s.connect(('192.0.2.1',9))
except OSError as e:
 if e.errno not in (errno.ENETUNREACH,errno.EHOSTUNREACH): raise
else: raise RuntimeError('unexpected route')
print(json.dumps({'uid':os.getuid(),'gid':os.getgid(),'caps':int(st['CapEff'].strip(),16),'no_new_privs':int(st['NoNewPrivs'].strip()),'net':os.readlink('/proc/self/ns/net'),'pid':os.readlink('/proc/self/ns/pid'),'interfaces':interfaces,'read_only':True,'write_control':True}, sort_keys=True))'''

def box(store, src, products, output, args):
    require(os.getuid()==0 and Path('/proc/self/status').is_file(), 'root host supervisor on Linux required')
    bw=shutil.which('bwrap'); require(bw is not None,'bubblewrap unavailable')
    return recipe(bw,Path('/usr/lib64').is_dir(),Path('/etc/ld.so.cache').is_file(),store,src,products,output,args)

def recipe(bw,lib64,ldcache,store,src,products,output,args):
    cmd=[bw,'--unshare-net','--unshare-pid','--unshare-ipc','--unshare-uts','--die-with-parent','--cap-drop','ALL','--cap-add','CAP_SETUID','--cap-add','CAP_SETGID','--cap-add','CAP_SETPCAP','--clearenv','--proc','/proc','--dev','/dev','--dir','/usr','--dir','/usr/bin','--ro-bind','/usr/lib','/usr/lib','--symlink','usr/lib','/lib']
    if lib64:
        cmd+=['--ro-bind','/usr/lib64','/usr/lib64','--symlink','usr/lib64','/lib64']
    cmd+=['--ro-bind','/usr/bin/python3','/usr/bin/python3','--ro-bind','/usr/bin/setpriv','/usr/bin/setpriv','--dir','/etc']
    if ldcache:
        cmd+=['--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache']
    cmd+=['--ro-bind',str(store/'lean-4.34.1-linux'),'/stock','--ro-bind',str(store/'libraries'),'/libraries','--ro-bind',str(src),'/src','--ro-bind',str(products),'/objects','--bind',str(output),'/out','--size',str(32*1024*1024),'--tmpfs','/tmp','--remount-ro','/','--chdir','/src']
    roots=['/objects']
    for k,v in {'PATH':'/stock/bin','LC_ALL':'C.UTF-8','HOME':'/tmp','TMPDIR':'/tmp','LEAN_NUM_THREADS':'1','LEAN_PATH':':'.join(roots)}.items():
        cmd+=['--setenv',k,v]
    return cmd+['--',*DROP,*args]
