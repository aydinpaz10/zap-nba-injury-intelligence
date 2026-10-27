"""Independent standard-library check of held-out probabilities, chronology and reported metrics."""
from pathlib import Path
import json,gzip,math,hashlib
root=Path(__file__).resolve().parents[1];report=json.loads((root/'data/model-metrics.json').read_text());selection=json.loads((root/'data/model-selection.json').read_text())
with gzip.open(root/'data/backtest-predictions.jsonl.gz','rt')as f:rows=[json.loads(s)for s in f]
assert all(not r['max_feature_day']or r['max_feature_day']<r['day']for r in rows)
assert report['quality']['protocol_hash']==hashlib.sha256((root/'validation/validation-protocol.json').read_bytes()).hexdigest()
assert not selection['test_used_for_selection'];test=[r for r in rows if r['season']==2026];assert len(test)==1230
for name in ['baseline','adjusted']:
 probs=[r[name+'_probability']for r in test];accuracy=sum((p>=.5)==bool(r['y'])for r,p in zip(test,probs))/len(test);ll=-sum(r['y']*math.log(p)+(1-r['y'])*math.log1p(-p)for r,p in zip(test,probs))/len(test);brier=sum((p-r['y'])**2 for r,p in zip(test,probs))/len(test);metrics=report['models'][name]['test_metrics']
 for k,v in [('accuracy',accuracy),('log_loss',ll),('brier',brier)]:assert abs(metrics[k]-v)<1e-12,(name,k,v)
 print(name,'accuracy',accuracy,'log_loss',ll,'Brier',brier)
print('Chronology, protocol hash, selection boundary and independent metrics passed.')
