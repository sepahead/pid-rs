from itertools import permutations
from math import ldexp,nextafter,inf
from struct import pack
from pathlib import Path
rows=[]
def add(name,points):
 for order in permutations(range(len(points))):
  fields=[name+'-'+''.join(map(str,order))]
  fields.extend(pack('>d',v).hex() for i in order for v in points[i]);rows.append(' '.join(fields))
for e in [-1022,-900,0,600,1023]:
 s=ldexp(1.,e);add(f'down{e}',[(0.,0.),(nextafter(s,0.),0.),(0.,s)])
 add(f'up{e}',[(0.,0.),(s,0.),(0.,nextafter(s,inf))])
add('constant',[(0.,0.),(1.,0.),(0.,1.)]);add('maximum',[(0.,0.),(float.fromhex('0x1.fffffffffffffp1023'),0.),(0.,float.fromhex('0x1.fffffffffffffp1023'))])
add('one-dimension',[(0.,0.),(1.,0.),(nextafter(2.,inf),0.)]);add('duplicate',[(0.,0.),(0.,0.),(8.,0.)])
n=ldexp(1.,-1074);add('subnormal',[(0.,0.),(n,0.),(2*n,0.)]);add('zero',[(0.,0.)]*3)
add('unrepresentable',[(float.fromhex('-0x1.fffffffffffffp1023'),0.),(0.,0.),(float.fromhex('0x1.fffffffffffffp1023'),0.)])
print('\n'.join(rows))
