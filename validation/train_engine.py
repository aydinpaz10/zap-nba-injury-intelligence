"""Frozen chronological experiment. Test metrics are generated only after validation selection is saved."""
import argparse,json,sqlite3,hashlib,gzip,csv,sys,math,statistics
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.metrics import accuracy_score,log_loss,brier_score_loss
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'models'))
from engine_math import initial_state,game_day,ratings,features,apply_games
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';PROTOCOL=ROOT/'validation/validation-protocol.json'
def load_exclusions(path):
 """Read user-supplied JSON array of event IDs; never assume an empty list."""
 try:
  value=json.loads(Path(path).read_text())
 except (OSError, ValueError) as exc:
  raise ValueError(f'Cannot read event exclusions: {exc}') from exc
 if not isinstance(value,list) or any(not isinstance(v,str) or not v.strip() for v in value) or len(set(value))!=len(value):
  raise ValueError('Exclusions must be a JSON array of unique nonempty string IDs.')
 return set(value)
def fit(x,y,C,adjusted):
 n=len(y);penalty=np.ones(x.shape[1]);penalty[0]=0
 def obj(w):
  z=x@w;p=expit(z);return np.mean(np.logaddexp(0,z)-y*z)+np.sum(penalty*w*w)/(2*C*n),x.T@(p-y)/n+penalty*w/(C*n)
 bounds=[(None,None)]*x.shape[1]
 if adjusted:bounds[-1]=(0,None)
 result=minimize(obj,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':2000,'ftol':1e-12,'gtol':1e-8})
 if not result.success:raise RuntimeError(result.message)
 return result.x

def metrics(y,p):
 bins=[]
 for i in range(10):
  mask=(p>=i/10)&(p<(i+1)/10 if i<9 else p<=1);n=int(mask.sum())
  bins.append({'lower':i/10,'upper':(i+1)/10,'n':n,'mean_probability':float(p[mask].mean()) if n else None,'observed_home_win_rate':float(y[mask].mean()) if n else None})
 ece=sum(b['n']/len(y)*abs(b['mean_probability']-b['observed_home_win_rate']) for b in bins if b['n'])
 return {'n':len(y),'accuracy':float(accuracy_score(y,p>=.5)),'log_loss':float(log_loss(y,p,labels=[0,1])),'brier':float(brier_score_loss(y,p)),'ece_10_bins':ece,'calibration':bins,'mean_probability':float(p.mean()),'actual_home_win_rate':float(y.mean())}

def main():
 parser=argparse.ArgumentParser(description='Train the chronological win model in an isolated workspace.')
 parser.add_argument('--exclude-events', required=True, help='Path to a JSON array of event ID strings to exclude; use [] only if none apply.')
 parser.add_argument('--reproduce', action='store_true')
 args=parser.parse_args()
 try: CUP_FINALS=load_exclusions(args.exclude_events)
 except ValueError as exc: parser.error(str(exc))
 protocol_hash=hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
 if (DATA/'model-metrics.json').exists() and not args.reproduce:raise SystemExit('Evaluation already exists. Use --reproduce solely to reproduce the frozen method, never tune on test results.')
 db=sqlite3.connect(DATA/'historical.sqlite');raw=list(db.execute('select id,season,date,data,source_hash,fetched_at from games order by date,id'))
 counts=Counter(r[1] for r in raw if r[0] not in CUP_FINALS)
 expected={2023:1230,2024:1230,2025:1230,2026:1230}
 if any(counts[y]!=n for y,n in expected.items()):raise SystemExit('Refusing incomplete evaluation: '+str(dict(counts)))
 games=[json.loads(r[3]) for r in raw if r[0] not in CUP_FINALS];data_hash=hashlib.sha256(''.join(sorted(r[0]+r[4] for r in raw if r[0] not in CUP_FINALS)).encode()).hexdigest()
 quality={'games_by_season':dict(counts),'excluded_cup_championships':sorted(CUP_FINALS),'participation_records':dict(Counter(p['participation'] for g in games for p in g['players'])),'unidentified_participation_rows':sum(not p['id'] for g in games for p in g['players']),'missing_player_records':'A player absent from a box score is NOT automatically DNP/inactive. Current rosters are not used to infer historical membership.','source':'ESPN per-event summary box scores','data_hash':data_hash,'protocol_hash':protocol_hash}
 state=initial_state();byday=defaultdict(list)
 for g in games:byday[game_day(g)].append(g)
 rows=[];min_coverage=[]
 for day,group in sorted(byday.items()):
  rate_map,replacement,mean=ratings(state,day)
  for g in group:
   base,adjusted,audit=features(state,g,rate_map,replacement)
   assert audit['max_feature_day'] is None or audit['max_feature_day']<day
   rows.append({'id':g['id'],'season':g['season'],'day':day,'home':g['home'],'away':g['away'],'y':int(g['home_score']>g['away_score']),'baseline':base,'adjusted':adjusted,'coverage':audit['covered_minutes']/480,'max_feature_day':audit['max_feature_day']})
  apply_games(state,group)
 print('FEATURES BUILT',len(rows),flush=True)
 train=np.array([r['season'] in [2023,2024] for r in rows]);validation=np.array([r['season']==2025 for r in rows]);test=np.array([r['season']==2026 for r in rows]);y=np.array([r['y'] for r in rows]);combined=train|validation
 selections={};models={}
 for name in ['baseline','adjusted']:
  x=np.array([r[name] for r in rows]);scores=[]
  for C in [.1,1,10]:
   w=fit(x[train],y[train],C,name=='adjusted');score=float(log_loss(y[validation],expit(x[validation]@w),labels=[0,1]));scores.append({'C':C,'validation_log_loss':score})
  chosen=min(scores,key=lambda s:(s['validation_log_loss'],s['C']));selections[name]={'selected_C':chosen['C'],'validation_candidates':scores}
 # Persist the parameter decision before any test probabilities or metrics are calculated.
 selection={'protocol_hash':protocol_hash,'data_hash':data_hash,'selection':selections,'test_used_for_selection':False}
 if (DATA/'model-selection.json').exists() and args.reproduce:
  old=json.loads((DATA/'model-selection.json').read_text())
  if old!=selection:raise RuntimeError('Reproduction changed selection or source data; test results cannot be reused as a development target.')
 (DATA/'model-selection.json').write_text(json.dumps(selection,indent=2))
 for name in ['baseline','adjusted']:
  x=np.array([r[name] for r in rows]);w=fit(x[combined],y[combined],selections[name]['selected_C'],name=='adjusted');pred=expit(x[test]@w);models[name]={'coefficients':w.tolist(),'selected_C':selections[name]['selected_C'],'features':['home_court','elo_diff/400','margin_diff/10','rest_diff/7','b2b_diff']+(['availability_production_diff/10'] if name=='adjusted' else []),'test_metrics':metrics(y[test],pred)}
  for r,p in zip([r for r in rows if r['season']==2026],pred):r[name+'_probability']=float(p)
 quality['test_rating_minute_coverage_mean']=float(np.mean([r['coverage'] for r in rows if r['season']==2026]));quality['test_below_70_percent_coverage']=sum(r['coverage']<.7 for r in rows if r['season']==2026)
 summary={'version':'zap-pregame-v1','generated_at':datetime.now(timezone.utc).isoformat(),'split':{'training':['2022-23','2023-24'],'validation':'2024-25','final_fit':['2022-23','2023-24','2024-25'],'test':'2025-26'},'models':models,'quality':quality,'protocol':json.loads(PROTOCOL.read_text()),'evaluation_scope':'Pregame lagged participation-proxy model. NOT a validation of live official injury status adjustments.','test_tuning_performed':False,'calibration_fitted_on_test':False}
 (DATA/'model-metrics.json').write_text(json.dumps(summary,indent=2))
 snapshot={'version':'zap-pregame-v1','models':{k:{key:value for key,value in m.items() if key!='test_metrics'} for k,m in models.items()},'state':state,'generated_at':summary['generated_at'],'training_cutoff':'2025-06-30','state_cutoff_day':state['latest_day'],'protocol_hash':protocol_hash,'data_hash':data_hash}
 (DATA/'engine.json').write_text(json.dumps(snapshot,separators=(',',':')))
 with gzip.open(DATA/'backtest-predictions.jsonl.gz','wt') as out:
  for r in rows:out.write(json.dumps(r,separators=(',',':'))+'\n')
 with gzip.open(DATA/'historical-boxscores.jsonl.gz','wt') as out:
  for ident,season,date,data,source_hash,fetched_at in raw:out.write(json.dumps({'id':ident,'season':season,'date':date,'game':json.loads(data),'source_hash':source_hash,'fetched_at':fetched_at},separators=(',',':'))+'\n')
 print(json.dumps({k:m['test_metrics'] for k,m in models.items()},indent=2),flush=True);print('QUALITY',json.dumps(quality),flush=True)
if __name__=='__main__':main()
