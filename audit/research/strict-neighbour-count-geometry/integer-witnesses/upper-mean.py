"""Construct one exact sample for each extremum and size. Each sample serves every rank."""
import json


def sample(n,kind):
    scale=1 << (n+2)
    multiplier=scale+int(kind=='open')
    return [[scale*(1<<i),2*scale*(1<<i),multiplier*(1<<i)] for i in range(n)]


print(json.dumps([dict(n=n,kind=kind,rows=sample(n,kind))
                  for n in range(2,16) for kind in ('open','corner')],separators=(',',':')))
