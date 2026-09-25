from pathlib import Path
import json, math, hashlib, datetime
base=Path(__file__).resolve().parent
repo=base.parents[1]
data_path=repo/'audit/evidence/real-occupancy-sensors-example-2026-09-08/descriptive-comparisons.json'
protocol=json.loads((base/'PROTOCOL.json').read_text())
if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(protocol['deadline_utc']):
 raise SystemExit('original window expired')
if hashlib.sha256(data_path.read_bytes()).hexdigest()!=protocol['data_sha256']:
 raise SystemExit('source changed')
data=json.loads(data_path.read_text())
previous=json.loads((base/'reference/RESULTS.json').read_text())
def dense(record):
 table=[[[0,0] for b in range(4)] for a in range(4)]
 for r in record['shannon']['joint_counts']:
  table[r['light_bin']][r['co2_bin']][r['occupancy']]=r['count']
 return table
train=dense(data['files']['datatraining.txt'])
left=[[sum(train[a][b][y] for b in range(4)) for y in range(2)] for a in range(4)]
right=[[sum(train[a][b][y] for a in range(4)) for y in range(2)] for b in range(4)]
total=[sum(left[a][y] for a in range(4)) for y in range(2)]
forecasts={}
for model in ['constant','light','co2','joint','or']:
 forecasts[model]={}
 for a in range(4):
  for b in range(4):
   counts={'constant':total,'light':left[a],'co2':right[b],'joint':train[a][b],
    'or':[left[a][y]+right[b][y]-train[a][b][y] for y in range(2)]}[model]
   forecasts[model][a,b]=[(counts[y]+1)/(sum(counts)+2) for y in range(2)]
results={};maxdelta=0
for name,record in data['files'].items():
 table=dense(record);n=sum(table[a][b][y] for a in range(4) for b in range(4) for y in range(2));results[name]={}
 for model,ps in forecasts.items():
  loss=math.fsum(-table[a][b][y]*math.log(ps[a,b][y]) for a in range(4) for b in range(4) for y in range(2))/n
  brier=math.fsum(table[a][b][y]*(ps[a,b][1]-y)**2 for a in range(4) for b in range(4) for y in range(2))/n
  results[name][model]={'log_loss_nats':loss,'brier_score':brier}
  for k,v in results[name][model].items():
   delta=abs(v-previous['results'][name][model][k]);maxdelta=max(delta,maxdelta)
   if delta>1e-12: raise SystemExit('reference mismatch')
output={'read_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reference_results_sha256':hashlib.sha256((base/'reference/RESULTS.json').read_bytes()).hexdigest(),'results':results,'max_abs_difference':maxdelta,'status':'PASS_ALTERNATE_DENSE_MARGINAL_RECOMPUTATION','limits':'Same exposed counts, model family and floating-point logarithm implementation; implementation arithmetic differs, no independent data or raw-Rust rerun.'}
(base/'ROOT_RECOMPUTATION.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
