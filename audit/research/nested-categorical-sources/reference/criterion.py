"""Small exact reference for a direction between the row and column variables."""
from fractions import Fraction

def minimum(n):
    if type(n) is not int or n<1:raise ValueError("positive total required")
    if n==1:return None
    a,b=n//2,n-n//2
    return Fraction((a+1)*(b+1),a*b)

def witness(n):
    if type(n) is not int or n<2:raise ValueError("ambiguous map needs two observations")
    a,b=n//2,n-n//2
    return [[1,a-1,0],[1,0,b-1]]

def certificate(grid):
    if not isinstance(grid,(list,tuple)) or not grid or not isinstance(grid[0],(list,tuple)) or not grid[0]:
        raise ValueError("empty or invalid grid")
    h=len(grid[0])
    if any(not isinstance(row,(list,tuple)) or len(row)!=h or any(type(c) is not int or c<0 for c in row) for row in grid):
        raise ValueError("malformed counts")
    sums=list(map(sum,grid))
    if not sum(sums):raise ValueError("zero total")
    col=[sum(column) for column in zip(*grid)]
    deterministic=all(sum(c>0 for c in column)<=1 for column in zip(*grid))
    result=Fraction(1)
    for i,row in enumerate(grid):
        for j,c in enumerate(row):
            if c:
                result*=Fraction(sums[i]+col[j]-c,sums[i])**c
    return result,deterministic
