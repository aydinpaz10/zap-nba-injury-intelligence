"""Post-evaluation inference only. Never fits or changes model predictions."""
import gzip,json,hashlib,math
from pathlib import Path
import numpy as np
from datetime import date,timedelta
root=Path(__file__).resolve().parents[1]
p=root/'data/backtest-predictions.jsonl.gz';raw=p.read_bytes();rows=[json.loads(x) for x in gzip.decompress(raw).decode().splitlines()];rows=[r for r in rows if r['season']==2026];assert len(rows)==1230
b=np.array([r['baseline_probability'] for r in rows]);a=np.array([r['adjusted_probability'] for r in rows]);y=np.array([r['y'] for r in rows]);loss=lambda q:-(y*np.log(q)+(1-y)*np.log1p(-q))
diff=np.column_stack([loss(a)-loss(b),(a-y)**2-(b-y)**2,((a>=.5)==y).astype(float)-((b>=.5)==y).astype(float)])
metrics=json.loads((root/'data/model-metrics.json').read_text());names=['log_loss','brier','accuracy'];start=date.fromisoformat(min(r['day'] for r in rows));end=date.fromisoformat(max(r['day'] for r in rows));D=(end-start).days+1
sums=np.zeros((D,3));counts=np.zeros(D)
for r,v in zip(rows,diff):
 i=(date.fromisoformat(r['day'])-start).days;sums[i]+=v;counts[i]+=1
B=20000
results={}
for L in [7,14]:
 rng=np.random.default_rng(20261021+L);reps=[]
 for _ in range(B):
  starts=rng.integers(0,D,size=math.ceil(D/L));idx=((starts[:,None]+np.arange(L))%D).ravel()[:D];n=counts[idx].sum();reps.append(sums[idx].sum(axis=0)/n)
 reps=np.array(reps);out={}
 for j,name in enumerate(names):
  estimate=float(diff[:,j].mean());lo,hi=np.quantile(reps[:,j],[.025,.975]);pvalue=(1+np.sum(np.abs(reps[:,j]-estimate)>=abs(estimate)))/(B+1)
  out[name]={'adjusted_minus_baseline':estimate,'ci_95':[float(lo),float(hi)],'centered_bootstrap_two_sided_p':float(pvalue)}
 results[str(L)+'_calendar_day_blocks']=out
out={'n':1230,'replicates':B,'method':'Paired circular moving-block bootstrap of calendar dates, retaining all games on each date; ratio of summed paired losses to sampled game count. Primary block length 7 days; prespecified sensitivity 14 days. Percentile 95% CIs and approximate centered two-sided bootstrap p-values. No multiplicity correction. Conditional on fitted models and this single season; shared-team and longer-term dependence may remain.','seed_rule':'20261021 + block_length','difference_direction':'Adjusted minus baseline; negative favors adjusted for log loss/Brier, positive for accuracy.','source_sha256':hashlib.sha256(raw).hexdigest(),'results':results,'frozen_metrics':{k:v['test_metrics'] for k,v in metrics['models'].items()},'conclusion':'Both block-length confidence intervals include zero for log loss and Brier differences. Evidence does not establish a statistically meaningful improvement. One held-out season and no official historical status labels limit generalization.'}
(root/'data/model-uncertainty.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(results,indent=2))
