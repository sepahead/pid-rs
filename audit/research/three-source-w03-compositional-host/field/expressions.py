"""Parse the closed stock constructor forms admitted by this field reader."""
import json
import re
from common import require

TOK=re.compile(r'\s+|[()\[\],]|"(?:[^"\\]|\\.)*"|[^\s()\[\],]+')
ARITY={'Lean.Expr.app':('expr','expr'),'Lean.Expr.bvar':('nat',),'Lean.Expr.const':('name','levels'),'Lean.Expr.lam':('name','expr','expr','binder'),'Lean.Expr.forallE':('name','expr','expr','binder'),'Lean.Expr.letE':('name','expr','expr','expr','bool'),'Lean.Expr.lit':('literal',),'Lean.Expr.proj':('name','nat','expr'),'Lean.Expr.sort':('level',),'Lean.Level.zero':(),'Lean.Level.succ':('level',),'Lean.Level.max':('level','level'),'Lean.Level.imax':('level','level'),'Lean.Level.param':('name',),'Lean.Literal.natVal':('nat',),'Lean.Literal.strVal':('str',)}
BINDERS={'Lean.BinderInfo.default','Lean.BinderInfo.implicit','Lean.BinderInfo.strictImplicit','Lean.BinderInfo.instImplicit'}

def expression(value):
    require(type(value) is str and len(value)>0 and not any(t in value for t in ('...','…','<opaque>','<unknown>')),'full constructor representation')
    tokens=[t for t in TOK.findall(value) if not t.isspace()]
    pos=0; pending=['expr']
    while pending:
        task=pending.pop();require(pos<len(tokens), 'incomplete constructor');tok=tokens[pos];pos+=1
        if task.startswith('literal-token:'):
            require(tok==task[14:],'constructor punctuation');continue
        if task=='levels-tail':
            if tok==']':continue
            require(tok==',','universe list separator');pending.extend(('levels-tail','level'));continue
        if tok=='(':
            pending.extend(('literal-token:)',task));continue
        if task=='levels':
            require(tok=='[','universe list');require(pos<len(tokens),'incomplete universe list')
            if tokens[pos]==']':pos+=1
            else:pending.extend(('levels-tail','level'))
        elif task=='nat':require(re.fullmatch('[0-9]+',tok) is not None,'natural constructor argument')
        elif task=='name':require((tok.startswith('`') and len(tok)>1) or tok=='Lean.Name.anonymous','constructor name')
        elif task=='bool':require(tok in ('true','false'),'let flag')
        elif task=='str':require(type(json.loads(tok)) is str,'string constructor argument')
        elif task=='binder':require(tok in BINDERS,'binding constructor')
        else:
            prefix={'expr':'Lean.Expr.','level':'Lean.Level.','literal':'Lean.Literal.'}[task]
            require(tok.startswith(prefix) and tok in ARITY,'unsupported, incomplete or open constructor '+tok)
            pending.extend(reversed(ARITY[tok]))
    require(pos==len(tokens),'unconsumed expression data')

def literal_const(value,name,params):
    levels=', '.join('Lean.Level.param `'+p for p in params)
    # Stock repr may reflow applications but preserves all constructor tokens.
    expected='Lean.Expr.const `'+name+' ['+levels+']'
    return [t for t in TOK.findall(value) if not t.isspace()]==[t for t in TOK.findall(expected) if not t.isspace()]
