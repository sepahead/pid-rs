"""A closed, bounded data language for ordinary Lean expressions. Input supplies no commands."""
import re
from common import decode,require

STAGES=('Meaning','Transport','Diagonal','Complete')
SEG=re.compile(r"[A-Za-z][A-Za-z0-9_']{0,95}\Z")
USER_ROOTS={'W03Scope','W03Meaning','W03Transport','W03Diagonal','SmtW02','ArchivedProjection'}
STOCK_ROOTS={'And','Array','BEq','BitVec','Bool','Classical','Decidable','Eq','Exists','False','Fin','Function','HEq','Iff','Int','List','Nat','Ne','Nonempty','Not','OfNat','Option','Or','PLift','PProd','PUnit','Prod','Quot','Quotient','Sigma','String','Subtype','Sum','True','ULift','Unit',
 'congr','congrArg','congrFun','decide','False.elim','id','propext','ite','dite','cast','instDecidableEqBool','isFalse','isTrue','not_false','of_decide_eq_true','rfl','trivial'}
def nat(x,hi,m):require(type(x) is int and 0<=x<=hi,m);return x
def term(obj,stage):
    count=0
    def go(z,depth,names):
        nonlocal count
        count+=1
        require(count<=200000 and depth<=160 and type(z) is list and z and type(z[0]) is str,'term bounds')
        tag,*xs=z
        if tag=='const':
            require(len(xs)==2 and type(xs[0]) is str and type(xs[1]) is list and len(xs[1])<=16,'constant shape')
            segments=xs[0].split('.');require(1<=len(segments)<=16 and all(SEG.fullmatch(s) for s in segments),'constant name')
            require(segments[0] in USER_ROOTS|STOCK_ROOTS,'unadmitted constant root')
            for m in STAGES:
                if segments[0]=='W03'+m:require(STAGES.index(m)<STAGES.index(stage) and segments[1:]==['result'],'forward reference')
            levels=[str(nat(n,16,'universe')) for n in xs[1]]
            path='.'.join('«'+seg+'»' for seg in segments)
            return '(@_root_.'+path+('.{'+', '.join(levels)+'}' if levels else '')+')'
        if tag=='var':
            require(len(xs)==1 and names,'unbound variable')
            return names[-1-nat(xs[0],len(names)-1,'variable index')]
        if tag in ('nat','sort'):
            require(len(xs)==1,'literal arity')
            n=nat(xs[0],65535 if tag=='nat' else 16,'literal')
            return str(n) if tag=='nat' else '(Sort '+str(n)+')'
        if tag=='str':
            require(len(xs)==1 and type(xs[0]) is str and re.fullmatch(r'[A-Za-z0-9_.-]{0,96}',xs[0]) is not None,'string')
            return '"'+xs[0]+'"'
        if tag=='app':
            require(2<=len(xs)<=64,'application arity')
            return '('+' '.join(go(x,depth+1,names) for x in xs)+')'
        if tag in ('lam','forall','let'):
            require(len(xs)==(3 if tag=='let' else 2),'binding arity')
            binder='w'+str(len(names));ty=go(xs[0],depth+1,names)
            body=go(xs[-1],depth+1,names+(binder,))
            if tag=='let':return '(let '+binder+' : '+ty+' := '+go(xs[1],depth+1,names)+'; '+body+')'
            return ('(fun ('+binder+' : '+ty+') => '+body+')' if tag=='lam' else '(∀ ('+binder+' : '+ty+'), '+body+')')
        raise ValueError('unknown term constructor')
    s=go(obj,0,())
    require(len(s.encode())<=16*1024**2,'rendered term extent')
    return s
def admit(raw):
    require(1<=len(raw)<=8*1024**2 and raw.endswith(b'\n') and raw.isascii(),'payload extent and encoding')
    d=decode(raw);require(type(d) is dict and set(d)==set(STAGES),'all four fixed stages')
    return {k:term(d[k],k) for k in STAGES}
def simple(name):return ['const',name,[]]
def mock_raw(negative=False):
    import json
    # These terms typecheck only under the separate toy definitions.
    vals={k:simple('True.intro') for k in STAGES}
    return (json.dumps(vals,separators=(',',':'))+'\n').encode()
