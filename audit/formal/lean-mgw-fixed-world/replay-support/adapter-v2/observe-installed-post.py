from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import stat
import time

stage = Path(__file__).resolve().parent
reg = json.loads((stage / 'REGISTRATION.json').read_bytes())
pins = json.loads((stage / 'INSTALLED_BYTE_PINS.json').read_bytes())
def metadata(s):
    return dict(device=s.st_dev, inode=s.st_ino, mode=oct(stat.S_IMODE(s.st_mode)),
                nlink=s.st_nlink, uid=s.st_uid, gid=s.st_gid, bytes=s.st_size,
                mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)
def require(ok, message):
    if not ok:
        raise RuntimeError(message)
for i, pin in enumerate(pins):
    p=Path(pin['path']);a=p.lstat()
    require(stat.S_ISREG(a.st_mode) and metadata(a)==pin['metadata'], 'metadata drift '+str(p))
    h=hashlib.sha256()
    with p.open('rb') as f:
        require(metadata(os.fstat(f.fileno()))==pin['metadata'], 'descriptor drift')
        remaining=a.st_size
        while remaining:
            b=f.read(min(1048576,remaining));require(bool(b),'truncation')
            h.update(b);remaining-=len(b)
        require(f.read(1)==b'', 'growth')
        require(metadata(os.fstat(f.fileno()))==pin['metadata'], 'descriptor changed')
    require(metadata(p.lstat())==pin['metadata'] and h.hexdigest()==pin['sha256'], 'byte/path drift '+str(p))
    if i%10000==0:
        require(time.monotonic_ns()<reg['custody_end_monotonic_ns'],'original custody clock ended')
result={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'monotonic_ns':time.monotonic_ns(),
        'full_byte_and_metadata_observations':len(pins),'failures':[],
        'source_manifest_sha256':hashlib.sha256((stage/'INSTALLED_BYTE_PINS.json').read_bytes()).hexdigest(),
        'scope':'Sequential full installed-byte final post-observation after this campaign actual completed prefix; four Lake configuration cache files remain excluded. No atomic or loader-trace claim.'}
out=stage/'preparation/INSTALLED_FINAL_POST.json'
require(not out.exists(),'refuse overwrite')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
