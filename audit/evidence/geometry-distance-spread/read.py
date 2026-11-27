from decimal import Decimal,localcontext
from fractions import Fraction as F
from pathlib import Path
import sys,struct,json,hashlib
lo=lambda b:struct.unpack('>d',bytes.fromhex(b))[0]
ub=lambda x:int.from_bytes(struct.pack('>d',x),'big')
fields='pair_min pair_max pair_mean pair_sd pair_cv nn_min nn_max nn_mean nn_sd nn_cv nn_mean_over_pair_mean'.split()
def de(q):return Decimal(q.numerator)/Decimal(q.denominator)
def moments(v):
 n=len(v);m=sum(v)/n; var=(n*sum(o*o for o in v)-sum(v)**2)/(n*n)
 with localcontext() as c:
  c.prec=140;c.Emin=-99999;c.Emax=99999
  sd=de(var).sqrt();return [float(min(v)),float(max(v)),float(m),float(sd),float(sd/de(m))],m
def rows(cases,native):
 batch={z.split('\t')[0]:z.split('\t')[1:] for z in native.splitlines()};r={};fault=[]
 for s in cases.splitlines():
  key,*bits=s.split();a=[F(lo(v))for v in bits];pts=list(zip(a[0::2],a[1::2]));v=batch[key]
  if key.startswith(('zero-','unrepresentable-')):
   good=v[0]=='err';r[key]={'typed_refusal_observed':good,'actual':v};fault.extend([] if good else [(key,'failure route')]);continue
  pair={(i,j):max(abs(a-b) for a,b in zip(pts[i],pts[j])) for i in range(3) for j in range(i+1,3)}
  near=[min(z for pp,z in pair.items() if i in pp) for i in range(3)]
  p,pm=moments(list(pair.values()));n,nm=moments(near);vals=p+n+[float(nm/pm)];wanted=[ub(a)for a in vals]
  if v[0]!='ok' or v[1]!='3':
   fault.append([key,'genuine positive inputs returned '+str(v)]);r[key]={'actual':v};continue
  got=[int(z,16) for z in v[2].split()];err=[abs(x-y)for x,y in zip(got,wanted,strict=True)]
  bad=[(h,k) for h,k in zip(fields,err) if k>(0 if h in ('pair_min','pair_max','nn_min','nn_max') else 6)]
  r[key]={'actual_words':[f'{x:016x}' for x in got],'independent_words':[f'{x:016x}' for x in wanted],'absolute_ulp_distances':dict(zip(fields,err)),'outside':dict(bad)};fault.extend((key,h,k)for h,k in bad)
 if set(batch)!=set(r) or len(r)!=102:raise ValueError('all 17 source designs × 6 permutations')
 return {'total':len(r),'admitted_inputs':90,'expected_domain_refusals':12,'field_names':fields,'success':not fault,'failed_fields':len(fault),'failure_examples':fault,'inputs':r}
if __name__=='__main__':
 case,word=map(Path,sys.argv[1:]);print(json.dumps(rows(case.read_text(),word.read_text()),sort_keys=True,indent=2))
