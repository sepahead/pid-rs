"""Read the original September generator independently of its decimal comparisons.

The public file specified on the command line must have the exact original hash.
This program runs its unchanged random-draw and premise-check prefix, including
the original finite cell layout. It observes the generated integer vectors at
the point where the original code would start taking logarithms.
"""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path

ORIGINAL_SHA256 = '9567d9c221fcf44dfb7ac2468c2b591517c30a28efb8a7fa528b62dd1a2a9fa8'
def require(ok, explanation):
    if not ok:
        raise ValueError(explanation)

def inspect(source, independent):
    raw=source.read_bytes()
    require(sha256(raw).hexdigest()==ORIGINAL_SHA256,'wrong original scientific script')
    text=raw.decode()
    cut='    lam_exact = dlog_ratio(w_min, w_min - move)\n'
    require(text.count(cut)==1,'original boundary for decimal arithmetic')
    original=text.split(cut,1)[0]
    expected=json.loads(independent.read_bytes()); running=sha256(); seen=0
    def observe(trial,shape,move,w,v):
        nonlocal seen
        b=(json.dumps([trial,shape,move,w,v],separators=(',',':'))+'\n').encode()
        running.update(b);seen+=1
    env={'observe':observe}
    exec(compile(original+'    observe(trial, alphabet, move, w, v)\n',str(source),'exec'),env)
    require(seen==env['used']==expected['used'] and running.hexdigest()==expected['panel_sha256'],'independent and original generated tables')
    tree=ast.parse(text)
    assertions=sorted((n for n in ast.walk(tree) if isinstance(n,ast.Assert)),key=lambda n:n.lineno)
    require(len(assertions)==3,'three original asserted statements')
    unit=ast.Module(body=[n for n in assertions],type_ignores=[])
    def predicate(mode):
        # Different totals, an impossible nonzero shift, and an absent strict minimum.
        state={'v':[2,1],'w':[1,1],'supp':[0,1],'cells':[0,1],'move':1,'w_min':1,'delta_twice_d':1}
        try:exec(compile(unit,str(source),'exec',optimize=mode),state)
        except AssertionError:return 'rejected'
        return 'accepted'
    results=[predicate(i) for i in (0,1,2)]
    require(results==['rejected','accepted','accepted'],'original premise-control behavior')
    return {'source_sha256':ORIGINAL_SHA256,'prefix_sha256':sha256(original.encode()).hexdigest(),'actual_original_tables':seen,
      'ordered_original_panel_sha256':running.hexdigest(),'matches_independent_exact_program':True,
      'raw_original_assertions_under_false_premise':dict(zip(('ordinary','optimized','double_optimized'),results)),
      'statement':'The unchanged prefix and independently generated complete vectors agree before the first logarithm. This is source-correspondence evidence, separate from running the original full decimal test.'}

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('original',type=Path);a.add_argument('independent_result',type=Path)
    o=a.parse_args();print(json.dumps(inspect(o.original,o.independent_result),indent=2,sort_keys=True))
