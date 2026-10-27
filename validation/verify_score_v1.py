"""Read-only verification of score metrics and frozen winner hashes."""
import gzip,json,hashlib,math
from pathlib import Path
p=Path(__file__).resolve().parents[1];r=json.load(open(p/'data/score-model-report-v1.json'));rows=[json.loads(x) for x in gzip.open(p/'data/score-features-v1.jsonl.gz','rt')];test=[x for x in rows if x['season']==2026];assert len(test)==1230
for x in rows:assert x['cutoff_day']is None or x['cutoff_day']<x['day']
for name,digest in r['winner_file_hashes'].items():assert hashlib.sha256((p/'data'/name).read_bytes()).hexdigest()==digest
for which in ['model','baseline']:
 absolute=[];squares=[];margins=[]
 for x in test:
  h=x['predicted_home']if which=='model'else max(0,math.floor(x['baseline_home']+.5));a=x['predicted_away']if which=='model'else max(0,math.floor(x['baseline_away']+.5));absolute.extend([abs(h-x['actual_home']),abs(a-x['actual_away'])]);squares.extend([(h-x['actual_home'])**2,(a-x['actual_away'])**2]);margins.append(abs(h-a-(x['actual_home']-x['actual_away'])))
 m=r['evaluation'][which];assert abs(sum(absolute)/len(absolute)-m['team_score_mae'])<1e-12;assert abs((sum(squares)/len(squares))**.5-m['team_score_rmse'])<1e-12;assert abs(sum(margins)/len(margins)-m['winning_margin_mae'])<1e-12
print(json.dumps({'evaluation':r['evaluation'],'prior_only_dates_verified':len(rows),'winner_hashes_unchanged':True},indent=2))
