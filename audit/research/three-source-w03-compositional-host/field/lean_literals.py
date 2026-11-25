"""Parse the entire literal-only Lean data declaration and compare its typed constructor tree."""
import hashlib, json, re
h=lambda v:hashlib.sha256(v).hexdigest()
def need(ok,what):
    if not ok:raise ValueError(what)
prefix=b'import W02Semantics\n\nset_option maxRecDepth 8192\nnamespace SmtW02\n\ndef originalScript : List Cmd := '
suffix=b'\n\nend SmtW02\n'
token=re.compile(rb'[ \n\t\r]+|"(?:\\["\\]|[^"\\\n\r])*"|[()[\],]|(?:Cmd|Term|Ty)\.[A-Za-z]+|[0-9]+|true|false')
arity={'Cmd.logic':1,'Cmd.option':2,'Cmd.constant':2,'Cmd.define':4,'Cmd.echo':1,'Cmd.assertion':1,'Cmd.check':0,'Cmd.exit':0,
       'Term.boolean':1,'Term.numeral':1,'Term.bits':2,'Term.name':2,'Term.app':3,'Term.indexed':4,
       'Ty.bv':1,'Ty.int':0,'Ty.bool':0}

def parse(blob):
    need(blob.startswith(prefix) and blob.endswith(suffix),'declaration header or trailer')
    part=blob[len(prefix):-len(suffix)]
    idx=0;words=[]
    while idx<len(part):
        m=token.match(part,idx);need(m,'unsupported token')
        idx=m.end();w=m.group()
        if not w.isspace(): words.append(w.decode('ascii'))
    stream=iter(words);at=next(stream,None)
    def take(expected=None):
        nonlocal at
        need(at is not None and (expected is None or expected==at),'expected '+str(expected))
        w=at;at=next(stream,None);return w
    def expr(depth=0):
        need(depth<=255,'depth')
        if at=='[':
            take('[');values=[]
            if at!=']':
                values.append(expr(depth+1))
                while at==',':take(',');values.append(expr(depth+1))
            take(']');return values
        if at=='(':
            take('(')
            if at in arity:
                name=take()
                result=[name.partition('.')[2]]+[expr(depth+1) for _ in range(arity[name])]
            else:
                left=expr(depth+1);take(',');result=[left,expr(depth+1)]
            take(')');return result
        if at in ('true','false'):return take()=='true'
        if at and at[0]=='"':return json.loads(take())
        if at and re.fullmatch('0|[1-9][0-9]*',at):return int(take())
        raise ValueError('unexpected value')
    result=expr();need(at is None,'trailing tokens')
    return result

def matches(blob,baseline):
    tree=parse(blob)
    # JSON leaves distinguish Boolean true from the integer 1.
    raw=json.dumps(tree,ensure_ascii=True,separators=(',',':')).encode()+b'\n'
    need(raw==baseline,'typed AST differs from independently read original')
    return len(tree),h(raw)

