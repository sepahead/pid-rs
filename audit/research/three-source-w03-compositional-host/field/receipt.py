"""Fixed readback. Require source expansion, actual receiving term, ownership and printed axiom lists."""
import re
from common import HERE,canonical,decode,require,same
from expressions import expression,literal_const
from modules import PRE
from observer import refs
from terms import STAGES
ALLOWED={'Classical.choice','propext','Quot.sound'}
def names(x):
    return type(x) is list and all(type(y) is str for y in x) and x==sorted(set(x))
def read(raw,axraw,science,authority,baseline=None):
    tags=[];owner={};records={}
    allowed_compiler=decode((HERE/'compiler_roster.json').read_bytes())['W02Semantics']
    lines=raw.splitlines(keepends=True)
    for line in lines:
        require(line.endswith(b'\n'),'unfinished observer line'); tag,sep,payload=line.partition(b' ')
        require(sep and tag in (b'W03_OWNER',b'W03_EXPR'),'unrecognized native observer output')
        r=decode(payload);tags.append(tag)
        if tag==b'W03_OWNER':
            require(set(r)=={'owner','kernel','extra','compiler'} and r['owner'] not in owner and names(r['kernel']) and names(r['extra']) and r['compiler']==(allowed_compiler if r['owner']=='W02Semantics' else []) and set(r['compiler'])<=set(r['kernel']) and not set(r['kernel'])&set(r['extra']),'module inventory');owner[r['owner']]=r
        else:
            require(set(r)=={'name','owner','trust','kind','levels','type','value','type_deps','value_deps','axioms','formal_closure'},'expression schema')
            require(r['name'] not in records and names(r['axioms']) and set(r['axioms'])<=ALLOWED and r['levels']==[] and r['trust']==1025 and names(r['type_deps']) and names(r['value_deps']) and names(r['formal_closure']) and set(r['type_deps']+r['value_deps']+r['axioms']+[r['name']])<=set(r['formal_closure']) and not set(allowed_compiler)&set(r['formal_closure']),'ordinary trust or actual dependencies')
            expression(r['type']);expression(r['value']);records[r['name']]=r
    group=(list(PRE) if science else ['W03Scope'])+['W03Authority'];basegroup=list(group)
    if not authority:group+=['W03'+k for k in STAGES]+['W03Consumer']
    expected=refs(science,authority)
    require(list(owner)==group and list(records)==expected and tags==[b'W03_OWNER']*len(group)+[b'W03_EXPR']*len(expected),'exact native roster')
    axlines=axraw.decode().splitlines(keepends=True);require(len(axlines)==len(expected),'axiom count')
    for n,ln in zip(expected,axlines,strict=True):
        m=re.fullmatch(r"'([^']+)' (?:depends on axioms: \[([^\]\n]+)\]|does not depend on any axioms)\n",ln)
        require(m is not None and m[1]==n,'separate axiom print identity')
        observed=sorted(m[2].split(', ')) if m[2] else []
        require(observed==records[n]['axioms'],'separate axiom print actual set')
        r=records[n];expected_owner=n.split('.')[0]
        require(r['owner']==expected_owner and n in owner[expected_owner]['kernel'],'physical declaration owner')
    if authority:
        for k in STAGES:
            l,r=records['W03Scope.'+k],records['W03Authority.'+k]
            require(l['kind']==r['kind']=='definition' and l['type']==r['type'] and l['value']==r['value'],'two protected raw expansions '+k)
        return {'owners':owner,'records':records}
    require(baseline is not None and same({n:owner[n] for n in basegroup},baseline['owners']),'prequalified fixed owner identities')
    for k in STAGES:
        n='W03'+k+'.result'; cn='W03Consumer.accept'+k
        a,c=records[n],records[cn]; target=baseline['records']['W03Authority.'+k]
        require(a['kind']==c['kind']=='theorem' and literal_const(a['type'],'W03Scope.'+k,[]),'exact submitted theorem type')
        require(c['type']==target['value'] and literal_const(c['value'],n,[]) and c['value_deps']==[n],'exact expanded consumer and term use')
        require(owner['W03'+k]['kernel']==[n] and owner['W03'+k]['extra']==[],'one declaration per candidate module')
    require(owner['W03Consumer']['kernel']==sorted('W03Consumer.accept'+k for k in STAGES) and owner['W03Consumer']['extra']==[],'receiving module inventory')
    return {'owners':owner,'records':records}
def trace_read(raw):
    vals=raw.splitlines(keepends=True); require(len(vals)==128,'all source codes')
    required=[]
    for a in range(128):
        members=[index+1 for index in range(7) if a&(1<<index)]
        valid=bool(members) and all(not(u!=v and u&v==u) for u in members for v in members)
        required.append(b'2\n' if valid else b'0\n')
    require(vals==required,'actual source result on each registered representative')
    return {'coordinates':'0 to 127 inclusive','two_assertions_by_code':[[v==b'2\n',False] for v in vals]}
