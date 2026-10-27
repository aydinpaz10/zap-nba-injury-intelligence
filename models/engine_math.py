"""Chronological production-proxy features; no current-game participation enters a prediction."""
import math,statistics,copy
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict
ET=ZoneInfo('America/New_York')
def game_day(g):return datetime.fromisoformat(g['date'].replace('Z','+00:00')).astimezone(ET).date().isoformat()
def days(a,b):return (datetime.fromisoformat(a)-datetime.fromisoformat(b)).days

def gmsc(row):
 s=row.get('stats',{})
 def n(k):
  try:return float(s.get(k,0))
  except:return 0.
 def pair(k):
  try:return [float(x) for x in s[k].split('-')]
  except:return [0.,0.]
 fg,fga=pair('FG');ft,fta=pair('FT')
 return n('PTS')+.4*fg-.7*fga-.4*(fta-ft)+.7*n('OREB')+.3*n('DREB')+n('STL')+.7*n('AST')+.7*n('BLK')-.4*n('PF')-n('TO')

def initial_state():return {'teams':{},'players':{},'transitions':{'played':[1.,1.],'absent':[1.,1.]},'processed_ids':[],'latest_day':None}
def team_state(state,t):return state['teams'].setdefault(t,{'elo':1500.,'margins':[],'last_day':None,'season':None,'rosters':[]})
def effective_elo(t,season):return 1500+.75*(t['elo']-1500) if t['season'] and t['season']!=season else t['elo']
def ratings(state,day):
 totals={}
 for ident,p in state['players'].items():
  h=[r for r in p['history'] if r['day']<day and days(day,r['day'])<=365]
  minutes=sum(r['minutes'] for r in h)
  if minutes>=100:totals[ident]=(minutes,sum(r['gmsc'] for r in h),h)
 total_min=sum(t[0] for t in totals.values());mean=sum(t[1] for t in totals.values())/total_min*36 if total_min else None
 result={}
 for ident,(m,gs,h) in totals.items():
  rate=(gs+200*mean/36)/(m+200)*36
  result[ident]={'id':ident,'name':state['players'][ident]['name'],'rate':rate,'observed_rate':gs/m*36,'minutes':m,'appearances':len(h),'last_game_day':h[-1]['day'],'through_day':state['players'][ident]['last_day'],'expected_minutes':sum(r['minutes'] for r in h[-10:])/len(h[-10:]),'team':state['players'][ident]['team']}
 values=sorted(x['rate'] for x in result.values());replacement=values[int((len(values)-1)*.25)] if values else None
 return result,replacement,mean

def lineup(state,team,rate_map,day,current_roster=None):
 t=team_state(state,team);ids=set(current_roster) if current_roster is not None else {i for r in t['rosters'][-5:] for i in r['ids']}
 pool=[]
 for ident in ids:
  p=state['players'].get(ident);r=rate_map.get(ident)
  if current_roster is None and p and p['team']!=team:continue
  # Missing rating is preserved. Minutes may still be estimated from observed prior games.
  history=[h for h in p['history'] if h['day']<day] if p else []
  em=sum(h['minutes'] for h in history[-10:])/len(history[-10:]) if history else 0.
  if em<=0:continue
  absent=p['last_participation'] in ['dnp','inactive','zero_minutes'] and p['team']==team
  transition=state['transitions']['absent' if absent else 'played'];missing=transition[0]/sum(transition)
  pool.append({'id':ident,'name':p['name'],'rate':r['rate'] if r else None,'minutes':em,'missing_probability':missing,'last_participation':p['last_participation'],'last_reason':p.get('last_reason',''),'last_seen':p['last_day'],'rating_minutes':r['minutes'] if r else 0})
 total=sum(p['minutes'] for p in pool)
 if total: 
  for p in pool:p['minutes']=p['minutes']/total*240
 return sorted(pool,key=lambda p:-p['minutes'])

def strength(pool,participation=None):
 if not pool:return None,0.,[]
 projected=[p['minutes']*((participation or {}).get(p['id'],1)) for p in pool]
 # Redistribute the vacated minutes over remaining observed teammates, capped at 48 per player.
 for _ in range(20):
  missing=240-sum(projected)
  if missing<1e-7:break
  eligible=[i for i,p in enumerate(pool) if (participation or {}).get(p['id'],1)>0 and projected[i]<48-1e-7]
  weights=sum(pool[i]['minutes']*(participation or {}).get(pool[i]['id'],1) for i in eligible)
  if weights<=0:break
  for i in eligible:projected[i]=min(48,projected[i]+missing*pool[i]['minutes']*(participation or {}).get(pool[i]['id'],1)/weights)
 covered=sum(m for p,m in zip(pool,projected) if p['rate'] is not None)
 value=sum(p['rate']*m/36 for p,m in zip(pool,projected) if p['rate'] is not None)
 return value,covered,projected

def expected_loss(pool,replacement,overrides=None):
 if not pool or replacement is None:return 0.,0.,[]
 healthy=sum((p['rate'] if p['rate'] is not None else replacement)*p['minutes']/36 for p in pool)
 availability={p['id']:(overrides or {}).get(p['id'],1-p['missing_probability']) for p in pool}
 value,covered,mins=strength(pool,availability)
 # Missing minutes left after all observed replacements are exhausted use the empirical replacement pool.
 missing_unknown=sum(m for p,m in zip(pool,mins) if p['rate'] is None)+max(0,240-sum(mins));adjusted=value+replacement*missing_unknown/36
 return healthy-adjusted,covered,mins

def features(state,g,rate_map,replacement,rosters=None):
 day=game_day(g);h=team_state(state,g['home']);a=team_state(state,g['away']);hr=days(day,h['last_day']) if h['last_day'] else 7;ar=days(day,a['last_day']) if a['last_day'] else 7
 hm=statistics.mean(h['margins']) if h['margins'] else 0.;am=statistics.mean(a['margins']) if a['margins'] else 0.
 base=[0. if g.get('neutral') else 1.,(effective_elo(h,g['season'])-effective_elo(a,g['season']))/400,(hm-am)/10,(min(7,hr)-min(7,ar))/7,float(ar<=1)-float(hr<=1)]
 hp=lineup(state,g['home'],rate_map,day,rosters.get(g['home']) if rosters else None);ap=lineup(state,g['away'],rate_map,day,rosters.get(g['away']) if rosters else None)
 hl,hc,_=expected_loss(hp,replacement);al,ac,_=expected_loss(ap,replacement)
 return base,base+[(al-hl)/10],{'home_loss':hl,'away_loss':al,'covered_minutes':hc+ac,'home_pool':hp,'away_pool':ap,'feature_cutoff_day':day,'max_feature_day':state['latest_day']}

def apply_games(state,games):
 # Called only after all same-day predictions are generated.
 for g in games:
  day=game_day(g);h=team_state(state,g['home']);a=team_state(state,g['away']);he=effective_elo(h,g['season']);ae=effective_elo(a,g['season']);p=1/(1+10**((ae-he-(0 if g.get('neutral') else 65))/400));actual=float(g['home_score']>g['away_score']);delta=20*(actual-p)
  h['elo']=he+delta;a['elo']=ae-delta
  for t,margin in [(h,g['home_score']-g['away_score']),(a,g['away_score']-g['home_score'])]:t['margins']=(t['margins']+[margin])[-10:];t['last_day']=day;t['season']=g['season']
  for team in [g['home'],g['away']]:
   ids=[p['id'] for p in g['players'] if p['team']==team and p['id']];t=team_state(state,team);t['rosters']=(t['rosters']+[{'day':day,'ids':ids}])[-5:]
  for row in g['players']:
   ident=row['id']
   if not ident:continue
   old=state['players'].get(ident);history=old['history'] if old else []
   observed=row['participation']!='missing_minutes'
   if old and observed and old['team']==row['team'] and sum(p['minutes'] for p in history)>=100 and old['last_participation']!='missing_minutes':
    prior='absent' if old['last_participation'] in ['dnp','inactive','zero_minutes'] else 'played';now_absent=row['participation'] in ['dnp','inactive','zero_minutes'];state['transitions'][prior][0 if now_absent else 1]+=1
   if row['participation']=='played':history=(history+[{'day':day,'minutes':row['minutes'],'gmsc':gmsc(row),'event_id':g['id']}])[-30:]
   state['players'][ident]={'name':row['name'],'team':row['team'],'history':history,'last_day':day,'last_participation':row['participation'],'last_reason':row.get('reason','')}
  state['latest_day']=max(state['latest_day'] or day,day);state['processed_ids'].append(g['id'])
