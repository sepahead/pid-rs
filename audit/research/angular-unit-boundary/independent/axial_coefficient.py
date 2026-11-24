"""A separate bounded integer calculation on the unit first axis."""
from fractions import Fraction as F
from math import comb
from pathlib import Path
import json
def need(check,reason):
 if not check:raise ArithmeticError(reason)
def ceildiv(a,b):return -((-a)//b)
scale=10**32
def floor_scaled(x):return (x.numerator*scale)//x.denominator
def ceil_scaled(x):return ceildiv(x.numerator*scale,x.denominator)
def linear_tail(z,start,a,b):
 return z**start*((a*start+b)/(1-z)+a*z/(1-z)**2)
z=F(1,3);terms=48
lnlo=2*sum(z**(2*i+1)/(2*i+1) for i in range(terms))
lnhi=lnlo+2*z**(2*terms+1)/((2*terms+1)*(1-z*z))
Jlo=floor_scaled(1-lnhi);Jhi=ceil_scaled(1-lnlo)
n=96;H=F(0)
for j in range(1,n+1):
 c=F(comb(2*j,j),4**j)
 h=F(2*(2*j+1),4**j)-(j+1)*F(4,9)**j
 H+=c*h/(2*j*(2*j-1))
delta=linear_tail(F(1,4),n+1,4,2)+linear_tail(F(4,9),n+1,1,1)
Hlo=floor_scaled(H-delta);Hhi=ceil_scaled(H+delta)
need(0<Hlo<=Hhi and 0<Jlo<=Jhi<scale,'enclosures')
c_lo=c_hi=scale; sum_lo=sum_hi=0
last=None
for j in range(1,24001):
 c_lo=c_lo*(2*j-1)//(2*j); c_hi=ceildiv(c_hi*(2*j-1),2*j)
 den=2*j*(2*j-1);sum_lo+=c_lo//den;sum_hi+=ceildiv(c_hi,den)
 residual=[10**6*(Jlo-sum_hi)-Hhi,10**6*(Jhi-sum_lo)-Hlo]
 need(residual[0]<=residual[1],j)
 if residual[1]<0:
  need(last and last['order']==j-1 and last['F_scaled'][0]>0,'missing strict preceding failure')
  print(json.dumps(dict(least=j,previous=last,current={'order':j,'F_scaled':residual},scaled_residual_denominator=10**6*scale,h_unit=[Hlo,Hhi],j_unit=[Jlo,Jhi],scale=scale,spec='6d57c8b4be16f883375f7d9ecc8b83351645d7e6d52c4c7c317603a0d4a7056f'),sort_keys=True,indent=2));break
 need(residual[0]>0,('enclosure contains threshold',j))
 last={'order':j,'F_scaled':residual}
else:raise ArithmeticError('integer maximum exhausted')
