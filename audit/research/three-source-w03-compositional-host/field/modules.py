from common import HERE,require
from source import bind
from terms import STAGES,admit

OPTIONS='set_option autoImplicit false\nset_option warningAsError true\nset_option maxRecDepth 65536\nset_option maxHeartbeats 20000000\n'
PRE=('W02Semantics','ProjectionCore','W03Literal','W03Scope')
def body(scope,field):
    import re
    hit=re.search(r'^def '+field+r' : Prop :=\n(.*?)(?=\n\n(?:def |end ))',scope,re.M|re.S)
    require(hit is not None,'exact protected scientific predicate '+field)
    return hit[1].strip()
def files(mode='science',payload=None):
    require(mode in ('science','positive','negative'),'module mode')
    actual=(HERE/'lean/W03Scope.lean').read_text()
    if mode=='science':
        lit,_=bind()
        require(lit==(HERE/'lean/W03Literal.lean').read_bytes(),'shipped literal equality')
        result={k:(HERE/'lean'/(k+'.lean')).read_text() for k in PRE}
        rhs={k:body(actual,k) for k in STAGES}
    else:
        # All four mock predicates are True except for the targeted negative's final False.
        rhs={k:('False' if k=='Complete' and mode=='negative' else 'True') for k in STAGES}
        result={'W03Scope':'namespace W03Scope\n'+'\n\n'.join('def '+k+' : Prop :=\n  '+rhs[k] for k in STAGES)+'\n\nend W03Scope\n'}
    result['W03Authority']='import W03Scope\n'+OPTIONS+'namespace W03Authority\n'+('open SmtW02 W03Scope\n' if mode=='science' else '')+'\n\n'.join('def '+k+' : Prop :=\n  '+rhs[k] for k in STAGES)+'\nend W03Authority\n'
    if payload is not None:
        vals=admit(payload)
        for i,k in enumerate(STAGES):
            imports='import '+('W03Scope' if i==0 else 'W03'+STAGES[i-1])+'\n'
            result['W03'+k]=imports+OPTIONS+'namespace W03'+k+'\ntheorem result : W03Scope.'+k+' :=\n  '+vals[k]+'\nend W03'+k+'\n'
        result['W03Consumer']='import W03Complete\nimport W03Authority\n'+OPTIONS+'namespace W03Consumer\n'+('open SmtW02 W03Scope\n' if mode=='science' else '')+'\n\n'.join('theorem accept'+k+' :\n  '+rhs[k]+' := W03'+k+'.result' for k in STAGES)+'\nend W03Consumer\n'
    return result
