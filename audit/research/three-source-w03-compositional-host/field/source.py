"""Bind all source bytes, every sort and every prerequisite of the smaller lexical environment."""
import hashlib
import json
import re
from common import HERE,canonical,decode,hash_bytes,require,same
import lean_literals
import source_reader
import source_writer

TARGETS=('sub','has','incomparable','valid','leq')
EXPECTED={'sub':[], 'has':[], 'incomparable':['has','sub'],'valid':['incomparable'],'leq':['has','sub']}
def encoded(x):return json.dumps(x,ensure_ascii=True,separators=(',',':')).encode()+b'\n'
def bind(raw=None):
    baseline=decode((HERE/'inputs/W03-source.json').read_bytes()); limits=baseline['structure']
    raw=(HERE/'inputs/W03.smt2').read_bytes() if raw is None else raw
    require(len(raw)==39272 and hash_bytes(raw)==limits['sha256'],'original bytes')
    tree,spans=source_writer.neutral(raw); tree2,spans2=source_reader.read(raw)
    require(same(tree,tree2) and same(spans,spans2),'dual source parsing')
    ast=source_writer.typed_script(tree);other=source_reader.checked_script(tree2)
    require(same(ast,other),'dual term sorting')
    for obj,k in ((tree,'tree_sha256'),(spans,'spans_sha256'),(ast,'annotated_sha256')):
        require(hash_bytes(encoded(obj))==limits[k],'historical '+k)
    require(len(ast)==89 and len(spans)==27085 and spans[0][1]==0 and spans[-1][2]==len(raw) and all(x[2]==y[1] for x,y in zip(spans,spans[1:])),'complete span coverage')
    require(tree[85:87]==[['assert',['valid','a']],['assert',['not',['leq','a','a']]]],'ordered assertions')
    require([v[0] for v in ast]==['logic','option']+['constant']*25+['define']*57+['echo','assertion','assertion','check','exit'],'all commands')
    def gather(x,ops,refs):
        if not isinstance(x,(list,tuple)):return
        if x and x[0]=='name': refs.add(x[2])
        if x and x[0]=='app':ops.add(x[2])
        for child in x:gather(child,ops,refs)
    defs=set(c[1] for c in ast[27:84]); edges={}; indices=[]; bodies={}
    for i,c in enumerate(ast):
        if c[0]!='define' or c[1] not in TARGETS:continue
        _,name,bindings,_,body=c; op=set();refs=set();gather(body,op,refs)
        require(refs<=set(f[0] for f in bindings),'no original constant read by '+name)
        edges[name]=sorted(op&defs);indices.append(i);bodies[name]=hash_bytes(encoded(body))
    require(edges==EXPECTED and indices==[27,28,29,30,32],'lexical closure')
    require(tree[2:27]==[['declare-const',n,['_' ,'BitVec',w]] for n,w in [('a','7'),('b','7'),('c','7'),('q','3'),('h','3'),('x','3'),('k','4'),('r','4')]]+[['declare-const','tau','Bool']]+[['declare-const','w'+str(i),'Int'] for i in range(16)],'all typed constants')
    literal=(lean_literals.prefix.decode().split('def originalScript')[0]+source_writer.lean_definition('originalScript',ast)+'\nend SmtW02\n').encode()
    require(lean_literals.matches(literal,encoded(ast))==(89,limits['annotated_sha256']) and hash_bytes(literal)==limits['lean_sha256'],'complete literal readback')
    return literal,{'bytes':len(raw),'source_sha256':hash_bytes(raw),'typed_sha256':limits['annotated_sha256'],'spans':len(spans),'commands':len(ast),'constants':25,'unrestricted_ints':16,'source_indices':indices,'dependencies':edges,'body_sha256':bodies,'literal_sha256':hash_bytes(literal)}
