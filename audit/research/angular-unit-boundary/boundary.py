"""Finite scalar observations at a zero-density boundary of the fixed angular family."""
import hashlib,json,runpy
from fractions import Fraction as Q
from math import comb
from pathlib import Path


def require(ok,why):
    if not ok:raise ValueError(why)


def log2_odd():
    x=Q(1,3);s=sum((2*x**(2*i+1)/(2*i+1) for i in range(64)),Q(0))
    return s,s+2*x**129/(129*(1-x*x))


def log2_ordinary():
    x=Q(1,2);s=sum((x**i/i for i in range(1,181)),Q(0));return s,s+x**181/(181*(1-x))


def joint_from_log(bounds):return 1-bounds[1],1-bounds[0]

def axial_series():
    def k(j):return Q(comb(2*j,j),4**j*2*j*(2*j-1))
    def linear_tail(q,n,a,b):return q**n*((a*n+b)/(1-q)+a*q/(1-q)**2)
    total=Q(0)
    for j in range(1,129):total+=k(j)*(2*(2*j+1)*Q(1,4)**j-(j+1)*Q(4,9)**j)
    remainder=k(129)*(2*linear_tail(Q(1,4),129,2,1)+linear_tail(Q(4,9),129,1,1));return total-remainder,total+remainder


def observed(h,j):
    four=sum([Q(1,4),Q(1,32),Q(1,96),Q(5,1024)]);t=j[0]-four,j[1]-four
    require(h[0]>0 and t[0]>0,'denominators and tail')
    vals={'H1':h,'J1':j,'T4':t,'Q4':(t[0]/h[1],t[1]/h[0])}
    return {k:[(lo*10**18).__floor__(),(hi*10**18).__ceil__()] for k,(lo,hi) in vals.items()}


def mul(a,b):
    out=[Q(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return out


def main():
    path=Path(__file__).resolve().parent/'judge.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest()=='a3d21f5da2a8676ff6ed8ab07610623de049659bc6af0fa3a09dd82fe2852421','frozen finite radical reader')
    first=observed(runpy.run_path(str(path))['atom'](),joint_from_log(log2_odd()));second=observed(axial_series(),joint_from_log(log2_ordinary()));require(first==second,'two independent scalar outputs')
    c5=Q(comb(10,5),4**5);k5=c5/90;lo1=2*k5/6;lo2=3*k5*c5;vals=[lo1,lo1*Q(1,2)**8,lo2,lo2*Q(2,5)**8]
    require(vals==[Q(7,7680),Q(7,1966080),Q(1323,655360),Q(1323,10**9)] and min(vals)>Q(1,10**6),'all-direction lower bounds')
    lhs=mul([6],mul([1,1],mul([-Q(11,10),1],[-Q(1,10),1])));base=mul([0,1],mul([-1,2],[Q(9,10),3]));delta=[-Q(33,50),Q(282,50),0,0];require([b-l for b,l in zip(base,lhs,strict=True)]==delta,'polynomial coefficients')
    print(json.dumps({'scaled_by':10**18,'scalar_intervals':first,'all_direction_lower_factors':[[q.numerator,q.denominator] for q in vals],'telescoping_polynomial_difference':[[Q(q).numerator,Q(q).denominator] for q in delta]},sort_keys=True))

if __name__=='__main__':main()
