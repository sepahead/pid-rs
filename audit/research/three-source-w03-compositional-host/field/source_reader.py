"""Lossless S-expression reader and independent structural sort checker for the registered fragment."""
from pathlib import Path
import re

class Unsupported(ValueError):
    pass

def demand(ok, message):
    if not ok:
        raise Unsupported(message)

def natural(token):
    demand(isinstance(token, str) and re.fullmatch(r'0|[1-9][0-9]*', token), 'expected decimal numeral')
    return int(token)

def read(payload):
    demand(len(payload) <= 1 << 17 and payload.isascii(), 'source size or alphabet')
    record, stack, top = [], [], []
    pos = 0
    while pos < len(payload):
        begin, first = pos, payload[pos]
        pos += 1
        if first in b' \t\r\n':
            kind = 'space'
            while pos < len(payload) and payload[pos] in b' \t\r\n': pos += 1
        elif first == ord(';'):
            kind = 'comment'
            while pos < len(payload) and payload[pos] not in b'\n\r': pos += 1
        elif first == ord('('):
            kind = 'open'
            demand(len(stack) < 150, 'nesting')
            stack.append([])
        elif first == ord(')'):
            kind = 'close'
            demand(stack, 'stray close')
            form = stack.pop()
            (stack[-1] if stack else top).append(form)
        else:
            kind = 'atom'
            if first == ord('"'):
                while True:
                    demand(pos < len(payload), 'unclosed string')
                    ch = payload[pos]
                    pos += 1
                    if ch == ord('"'):
                        if payload[pos:pos+1] == b'"':
                            pos += 1
                        else:break
            else:
                demand(first not in b'|\\' and 32 < first < 127, 'unsupported atom')
                while pos < len(payload) and payload[pos] not in b'() \t\n\r;"':
                    demand(payload[pos] not in b'\\|' and 32 < payload[pos] < 127,'unsupported atom')
                    pos += 1
            demand(stack, 'top-level atom')
            stack[-1].append(payload[begin:pos].decode('ascii'))
        record.append([kind,begin,pos])
        demand(len(record)<100000,'token budget')
    demand(not stack and top and b''.join(payload[a:b] for _,a,b in record)==payload,'incomplete source')
    return top,record

def atom_name(v):
    demand(isinstance(v,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',v), 'identifier')
    return v

def ty(node):
    if node == 'Bool':return ('bool',)
    if node == 'Int':return ('int',)
    demand(isinstance(node,list) and len(node)==3 and node[:2]==['_','BitVec'],'sort')
    size=natural(node[2]);demand(0<size<=256,'unsupported bit width')
    return ('bv',size)

B, I = ('bool',), ('int',)
def term(node,globals_,local):
    if isinstance(node,str):
        if node in ('true','false'):return B,('boolean',node=='true')
        if re.fullmatch(r'[0-9]+',node):return I,('numeral',natural(node))
        if node in local:return local[node],('name',local[node],node)
        demand(node in globals_ and not globals_[node][0], 'unbound or nonatomic name')
        t=globals_[node][1];return t,('name',t,node)
    demand(isinstance(node,list) and node,'term')
    op,*args=node
    if op=='_':
        demand(len(args)==2 and isinstance(args[0],str) and re.fullmatch(r'bv(?:0|[1-9][0-9]*)',args[0]),'bv')
        x=natural(args[0][2:]);k=natural(args[1]);demand(0<k<=256 and x<(1<<k),'literal width or range')
        return ('bv',k),('bits',k,x)
    if isinstance(op,list):
        demand(len(op)>=3 and op[0]=='_' and len(args)==1,'indexed form')
        indices=list(map(natural,op[2:]));arg_t,arg=term(args[0],globals_,local)
        demand(arg_t[0]=='bv','indexed operand type')
        if op[1]=='extract':
            demand(len(indices)==2 and 0<=indices[1]<=indices[0]<arg_t[1],'extraction interval')
            t=('bv',indices[0]-indices[1]+1)
        else:
            demand(op[1]=='zero_extend' and len(indices)==1 and arg_t[1]+indices[0]<=256,'indexed operation')
            t=('bv',arg_t[1]+indices[0])
        return t,('indexed',t,op[1],tuple(indices),arg)
    parsed=[term(v,globals_,local) for v in args]
    types=[p[0] for p in parsed];argc=len(types)
    equal=bool(types) and all(t==types[0] for t in types)
    if op in globals_:
        pars,t=globals_[op];demand(types==pars and argc>0,'defined function arity or type')
    elif op=='ite':
        demand(argc==3 and types[0]==B and types[1]==types[2],'ite');t=types[1]
    elif op in ('=','distinct'):
        demand(argc>=2 and equal, 'comparison arity or type');t=B
    elif op in ('and','or','=>','not'):
        demand((argc==1 if op=='not' else argc>=2) and equal and types[0]==B,'Boolean arity or type');t=B
    elif op in ('+','-','<','<=','>','>='):
        demand((argc>=1 if op=='-' else argc>=2) and equal and types[0]==I,'integer operation')
        t=I if op in ('+','-') else B
    elif op in ('bvsub','bvand','bvor','bvshl'):
        demand(argc==2 and equal and types[0][0]=='bv','bitvector type or arity');t=types[0]
    else:raise Unsupported('unknown operator')
    return t,('app',t,op,tuple(p[1] for p in parsed))

def checked_script(forms):
    demand(len(forms)>=6 and forms[:2]==[['set-logic','ALL'],['set-option',':produce-models','true']]
           and forms[-2:]==[['check-sat'],['exit']],'header and terminal forms')
    globals_,checked={},[('logic','ALL'),('option',':produce-models','true')]
    nassert=necho=0
    for cmd in forms[2:-2]:
        demand(isinstance(cmd,list) and cmd,'command')
        op,*fields=cmd
        if op=='echo':
            demand(len(fields)==1 and isinstance(fields[0],str) and fields[0].startswith('"')
                   and fields[0].endswith('"') and necho==0,'echo')
            checked.append(('echo',fields[0]));necho+=1
        elif op in ('declare-const','define-fun'):
            demand(len(fields)==(2 if op=='declare-const' else 4),'declaration')
            name=atom_name(fields[0]);demand(name not in globals_ and nassert==0,'definition outside signature')
            if op=='declare-const':
                result=ty(fields[1]);globals_[name]=([],result);checked.append(('constant',name,result));continue
            params=fields[1];demand(isinstance(params,list),'binder list')
            local={}
            for p in params:
                demand(isinstance(p,list) and len(p)==2,'binder pair')
                v=atom_name(p[0]);demand(v not in local,'duplicate binder');local[v]=ty(p[1])
            result=ty(fields[2]);t,body=term(fields[3],globals_,local)
            demand(t==result,'definition result sort')
            globals_[name]=(list(local.values()),result);checked.append(('define',name,tuple(local.items()),result,body))
        elif op=='assert':
            demand(len(fields)==1,'assert argument')
            t,body=term(fields[0],globals_,{})
            demand(t==B,'assert requires Bool')
            checked.append(('assertion',body));nassert+=1
        else:raise Unsupported('unexpected command in context')
    demand(nassert==2 and necho==1,'registered assertion or echo count')
    return checked+[('check',),('exit',)]

