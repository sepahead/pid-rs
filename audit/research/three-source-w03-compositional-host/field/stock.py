"""Trusted preflight and private extraction of the one sealed official archive, before scientific input."""
import os
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
from common import HERE,decode,digest,require
from native_resources import retained_bytes

def memory_bound():
    location=Path('/proc/self/cgroup').read_text().splitlines()
    hierarchy=[x[3:] for x in location if x.startswith('0::')]
    require(len(hierarchy)==1,'private cgroup v2 memory limit required')
    base=Path('/sys/fs/cgroup')
    candidates=[base/hierarchy[0].lstrip('/'),base]
    for leaf in candidates:
        if not (leaf/'cgroup.procs').exists():continue
        if str(os.getpid()) not in (leaf/'cgroup.procs').read_text().split():continue
        maxima=[]
        for directory in [leaf,*leaf.parents]:
            if not directory.is_relative_to(base):break
            f=directory/'memory.max'
            if f.exists():
                n=f.read_text().strip()
                if n!='max':maxima.append(int(n))
        if maxima and 0<min(maxima)<=4*1024**3:return min(maxima)
    raise ValueError('no measured cgroup hard maximum at or below 4 GiB')

def provision(archive,store):
    require(platform.system()=='Linux' and platform.machine()=='x86_64' and os.geteuid()==0,'independent operator on Linux x86_64 required')
    require(shutil.which('bwrap') and shutil.which('setpriv') and shutil.which('tar') and shutil.which('zstd'),'missing declared provider tools')
    cap=memory_bound()
    cpus=os.sched_getaffinity(0);require(bool(cpus),'eligible CPU')
    os.sched_setaffinity(0,{min(cpus)});require(len(os.sched_getaffinity(0))==1,'one CPU')
    pin=decode((HERE/'stock.json').read_bytes());require(archive.is_file() and not archive.is_symlink() and archive.stat().st_size==pin['archive_bytes'],'original Linux release archive')
    require(shutil.disk_usage(store.parent).free>=12*(1024**3),'supplier free-space preflight')
    store.mkdir(mode=0o755);(store/'libraries').mkdir(mode=0o755)
    # Preserve and authenticate the same bytes that the operator extracts. Only stock enters the guest.
    copy=store/'verified-release.tar.zst'; h=hashlib.sha256();total=0
    with archive.open('rb') as inp,copy.open('xb') as dst:
        while chunk:=inp.read(1024**2):
            total+=len(chunk);require(total<=pin['archive_bytes'],'archive size during read')
            h.update(chunk);dst.write(chunk)
    require(total==pin['archive_bytes'] and h.hexdigest()==pin['archive_sha256'],'official release bytes')
    copy.chmod(0o444)
    subprocess.run(['tar','--zstd','--extract','--file',str(copy),'--directory',str(store),'--no-same-owner'],check=True,timeout=900,stdin=subprocess.DEVNULL)
    tree=store/'lean-4.34.1-linux'
    for f,h in (('lean','lean_sha256'),('leanchecker','leanchecker_sha256')):
        require(digest(tree/'bin'/f)==pin[h],'release executable '+f)
    require(retained_bytes(store)<=10*(1024**3) and set(v.name for v in store.iterdir())=={'libraries','lean-4.34.1-linux','verified-release.tar.zst'},'supplier tree and extent')
    return {'archive_sha256':pin['archive_sha256'],'lean':pin['lean_sha256'],'leanchecker':pin['leanchecker_sha256'],'revision':pin['lean_revision'],'os':platform.platform(),'single_cpu':True,'stock_bytes':retained_bytes(store),'bubblewrap':digest(shutil.which('bwrap')),'setpriv':digest(Path('/usr/bin/setpriv')),'archive_reader':digest(shutil.which('tar')),'zstd':digest(shutil.which('zstd')),'bubblewrap_path':shutil.which('bwrap'),'lib64':Path('/usr/lib64').is_dir(),'ldcache':Path('/etc/ld.so.cache').is_file(),'hard_cgroup_bytes':cap}
