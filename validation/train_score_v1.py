"""Separate direct-points model; winner files are read-only."""
import json,gzip,hashlib,math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'models'))
from engine_math import initial_state,game_day,ratings,features,apply_games
from score_math import initial_score_state,score_features,apply_score_games
P=Path(__file__).resolve().parents[1];protocol=json.loads((P/'validation/score-model-protocol-v1.json').read_text());target=P/'data/score-engine-v1.json'
if target.exists():raise SystemExit('Score v1 already frozen; verification uses saved features. Create a new version for methodology changes.')
winner_names=['engine.json','model-metrics.json','backtest-predictions.jsonl.gz'];before={n:hashlib.sha256((P/'data'/n).read_bytes()).hexdigest() for n in winner_names}
ids={json.loads(r)['id'] for r in gzip.open(P/'data/backtest-predictions.jsonl.gz','rt')};games=[json.loads(r)['game'] for r in gzip.open(P/'data/historical-boxscores.jsonl.gz','rt')];games=sorted([g for g in games if g['id'] in ids],key=lambda g:(game_day(g),g['date'],g['id']));state=initial_state();score=initial_score_state();rows=[]
i=0
while i<len(games):
 day=game_day(games[i]);j=i
 while j<len(games) and game_day(games[j])==day:j+=1
 rm,rep,_=ratings(state,day)
 for g in games[i:j]:
  _,_,audit=features(state,g,rm,rep);home,away,context=score_features(score,g,audit['home_loss'],audit['away_loss']);assert not score['latest_day'] or score['latest_day']<day
  rows.append({'id':g['id'],'season':g['season'],'day':day,'home':g['home'],'away':g['away'],'home_features':home,'away_features':away,'actual_home':g['home_score'],'actual_away':g['away_score'],'baseline_home':context['home_baseline'],'baseline_away':context['away_baseline'],'cutoff_day':score['latest_day']})
 apply_games(state,games[i:j]);apply_score_games(score,games[i:j]);i=j

def xy(rows):return np.array([x for r in rows for x in [r['home_features'],r['away_features']]]),np.array([y for r in rows for y in [r['actual_home'],r['actual_away']]])
def fit(rows,alpha):
 x,y=xy(rows);penalty=np.ones(x.shape[1]);penalty[0]=0
 def fn(w):
  residual=x@w-y;return (residual@residual+alpha*np.sum(penalty*w*w))/(2*len(y)),(x.T@residual+alpha*penalty*w)/len(y)
 bounds=[(None,None)]*8;bounds[6]=(None,0);bounds[7]=(0,None)
 r=minimize(fn,np.array([110.,1.,1.,1.,3.,0.,0.,0.]),jac=True,bounds=bounds,method='L-BFGS-B',options={'maxiter':3000,'ftol':1e-12,'gtol':1e-7});assert r.success,r.message;return r.x
train=[r for r in rows if r['season'] in [2023,2024]];val=[r for r in rows if r['season']==2025];test=[r for r in rows if r['season']==2026];vx,vy=xy(val);selection=[]
for alpha in protocol['ridge_grid']:
 w=fit(train,alpha);selection.append({'alpha':alpha,'validation_team_score_mae':float(np.mean(np.abs(vx@w-vy)))})
alpha=min(selection,key=lambda r:r['validation_team_score_mae'])['alpha'];weights=fit(train+val,alpha)
# Selection is persisted before evaluating 2025-26 scores; that season is explicitly previously inspected.
(P/'data/score-selection-v1.json').write_text(json.dumps({'selected_alpha':alpha,'candidates':selection,'coefficients':weights.tolist(),'evaluation_previously_inspected':True},indent=2)+'\n')
def metric(rows,baseline=False):
 errors=[];margins=[];squared=[]
 for r in rows:
  h=r['baseline_home'] if baseline else float(np.dot(weights,r['home_features']));a=r['baseline_away'] if baseline else float(np.dot(weights,r['away_features']));h=max(0,math.floor(h+.5));a=max(0,math.floor(a+.5));errors.extend([abs(h-r['actual_home']),abs(a-r['actual_away'])]);squared.extend([(h-r['actual_home'])**2,(a-r['actual_away'])**2]);margins.append(abs((h-a)-(r['actual_home']-r['actual_away'])))
 return {'games':len(rows),'team_scores':2*len(rows),'team_score_mae':float(np.mean(errors)),'team_score_rmse':float(np.sqrt(np.mean(squared))),'winning_margin_mae':float(np.mean(margins))}
for r in test:
 r['predicted_home']=max(0,math.floor(float(weights@r['home_features'])+.5));r['predicted_away']=max(0,math.floor(float(weights@r['away_features'])+.5))
report={'version':protocol['version'],'protocol':protocol,'selected_alpha':alpha,'coefficients':weights.tolist(),'evaluation':{'model':metric(test),'baseline':metric(test,True)},'source_hash':hashlib.sha256((P/'data/historical-boxscores.jsonl.gz').read_bytes()).hexdigest(),'winner_file_hashes':before,'feature_rows':len(rows),'conclusion':'Chronological exploratory evaluation on previously inspected 2025-26 data. No new untouched-validation claim. Display-rounded score errors include overtime. Official live availability overrides were not historically status-validated.'}
(P/'data/score-model-report-v1.json').write_text(json.dumps(report,indent=2)+'\n');target.write_text(json.dumps({'version':protocol['version'],'coefficients':weights.tolist(),'selected_alpha':alpha,'state':score,'rounding':'max(0, floor(raw + 0.5))','protocol':protocol},separators=(',',':'))+'\n')
with gzip.open(P/'data/score-features-v1.jsonl.gz','wt')as f:
 for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
assert before=={n:hashlib.sha256((P/'data'/n).read_bytes()).hexdigest() for n in winner_names};print(json.dumps(report['evaluation'],indent=2));print('Frozen winner artifacts unchanged.')
