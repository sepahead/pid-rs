"""Exact attaining tables with two binary contexts and extra occupied source labels."""
from fractions import Fraction
from pathlib import Path
import json
import runpy

source = runpy.run_path(str(Path(__file__).resolve().with_name('check_finite_attainment.py')))
check = source['test']
require = source['require']


def construction(a, b, labels):
    require(a >= 1 and b >= 1 and labels >= 2, 'two active conflicting count slots')
    weights = {(0,0,0,0):1, (0,0,1,0):1}
    if a>1: weights[(0,1,0,1)]=a-1
    if b>1: weights[(1,0,1,1)]=b-1
    for k in range(2, labels):
        weights[(k,k,k,k)]=1
    n=a+b+labels-2
    require(sum(weights.values())==n and len({row[2] for row in weights})==labels,
            'exact N and number of occupied third-source labels')
    return weights


def main():
    splits=0; balanced=0
    for n in range(2,36):
        for a in range(1,n):
            b=n-a
            B,gap=check(construction(a,b,2))
            require(B>1 and gap==Fraction((a+1)*(b+1),a*b)**2,'exact positive gap for every allocation')
            splits+=1
    for n in range(2,17):
        for labels in range(2,n+1):
            available=n-labels+2; a=available//2; b=available-a
            B,gap=check(construction(a,b,labels))
            require(B==4 and gap==Fraction((a+1)*(b+1),a*b)**2,'attaining every pair of counts')
            balanced+=1
    return {'all_two_label_splits_between_N2_and_N35':splits,
            'all_occupied_label_counts_between_N2_and_N16':balanced,
            'conditional_product_for_balanced_construction':4,
            'basis':'The underlying checker calculates positive and negative component products from all 18 original match events at every occupied row.'}

if __name__=='__main__':print(json.dumps(main(),sort_keys=True,indent=2))
