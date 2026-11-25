"""Exercise scientific input, typed-data and readback predicates with harmless examples."""
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import HERE,canonical,require,same
from receipt import trace_read
from modules import files
from terms import STAGES,admit,mock_raw,simple,term
from source import bind

def rejection(fn,reason):
    try:fn()
    except (ValueError,KeyError,RecursionError) as ex:
        require(reason in str(ex),'wrong cause for '+reason+' '+str(ex));return reason
    raise ValueError('accepted '+reason)
def check():
    trace=bind()[1];target=files()
    t=admit(mock_raw())
    require(set(t)==set(STAGES) and all(x=='(@_root_.«True».«intro»)' for x in t.values()),'toy constants only')
    require(term(['lam',['sort',0],['var',0]],'Meaning')=='(fun (w0 : (Sort 0)) => w0)','binder')
    require(term(['let',['sort',0],simple('True'),['var',0]],'Meaning').startswith('(let w0 : (Sort 0) := '),'typed let')
    fixed=files('positive',mock_raw());neg=files('negative',mock_raw())
    require(fixed['W03Complete']==neg['W03Complete'] and 'False' in neg['W03Scope'] and 'False' not in fixed['W03Scope'],'same harmless term, different type')
    failures=[]
    original=(HERE/'inputs/W03.smt2').read_bytes()
    for pat,replacement in [(b'(assert (valid a))',b'(assert (valid b))'),(b'(not (leq a a))',b'(not (leq a b))'),(b'(_ BitVec 7)',b'(_ BitVec 6)')]:
        changed=original.replace(pat,replacement,1);require(changed!=original,'bad mutation construction')
        failures.append(rejection(lambda:bind(changed),'original bytes'))
    minimal=json.loads(mock_raw())
    misleading=copy.deepcopy(minimal);del misleading['Transport']
    failures.append(rejection(lambda:admit(canonical(misleading)),'four fixed stages'))
    for obj,err in [(['const','W03Complete.result',[]],'unadmitted'),(['var',0],'unbound'),(['const','W03Transport.result',[]],'forward'),(['app',simple('True')],'arity')]:
        failures.append(rejection(lambda:term(obj,'Meaning'),err))
    # The original trace reader is checked on a fixed, independently tabulated acceptance fixture.
    valid_codes={1,2,3,4,8,9,10,11,12,16,18,20,32,33,36,48,52,64}
    fixture=b''.join(b'2\n' if i in valid_codes else b'0\n' for i in range(128))
    require(len(trace_read(fixture)['two_assertions_by_code'])==128,'fixture readback')
    for raw in (b'2\n'*128, fixture.replace(b'2\n',b'1\n',1), fixture.replace(b'0\n',b'4\n',1), fixture[2:]):
        failures.append(rejection(lambda:trace_read(raw),'all source codes' if len(raw)<len(fixture) else 'actual source result'))
    return {'structure':trace,'term_slots':list(STAGES),'harmless_control_rejections':failures,'finite_rows_are_reader_fixture_only':True,'scientific_candidates':0}
if __name__=='__main__':print(canonical(check()).decode(),end='')
