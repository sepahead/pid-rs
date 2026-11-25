import hashlib
import os
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def require(x,message):
    if not x: raise ValueError(message)
def hash_bytes(x):return hashlib.sha256(x).hexdigest()
def digest(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
def same(a,b):return canonical(a)==canonical(b)
def decode(raw):
    def unique(pairs):
        out={}
        for k,v in pairs:
            require(k not in out,'duplicate key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
def write(p,x):
    destination=Path(p)
    with destination.open('xb') as f:
        f.write(canonical(x));f.flush();os.fsync(f.fileno())
    fd=os.open(destination.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def field_files():
    out={}
    for p in sorted(HERE.rglob('*')):
        require(not p.is_symlink(),'unexpected package link')
        if p.is_file() and p!=HERE/'FIELD.json':
            require('__pycache__' not in p.parts,'unregistered package bytecode')
            out[p.relative_to(HERE).as_posix()]=[p.stat().st_size,digest(p)]
    return out
def seal(expected):
    q=HERE/'FIELD.json'; require(digest(q)==expected and same(decode(q.read_bytes()),field_files()),'external package commitment')
