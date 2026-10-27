"""Direct score-model features from strictly prior games."""
from engine_math import game_day,days

def initial_score_state():return {'teams':{},'league':[],'processed_ids':[],'latest_day':None}
def score_features(state,g,loss_home=0.,loss_away=0.):
 day=game_day(g);league=state['league'][-600:];poss=sum(r['poss'] for r in league);rating=sum(r['points'] for r in league)/poss*100 if poss else 110.;pace=sum(r['pace'] for r in league)/len(league) if league else 100.
 def team(t):
  h=state['teams'].get(t,[])[-20:];p=sum(r['poss'] for r in h)+5*pace
  return {'off':(sum(r['points'] for r in h)+5*pace*rating/100)/p*100,'def':(sum(r['opp_points'] for r in h)+5*pace*rating/100)/p*100,'pace':(sum(r['pace'] for r in h)+5*pace)/(len(h)+5),'rest':min(7,days(day,h[-1]['day'])) if h else 7}
 h=team(g['home']);a=team(g['away']);expected=(h['pace']+a['pace'])/2
 def x(own,opp,home,loss,opp_loss):return [1.,(own['off']-rating)*expected/100,(opp['def']-rating)*expected/100,expected-100,0. if g.get('neutral') else home,(own['rest']-opp['rest'])/7,loss/10,opp_loss/10]
 return x(h,a,.5,loss_home,loss_away),x(a,h,-.5,loss_away,loss_home),{'home_baseline':expected*(h['off']+a['def'])/200,'away_baseline':expected*(a['off']+h['def'])/200,'expected_pace':expected,'home':h,'away':a,'league_efficiency':rating,'cutoff_day':state['latest_day']}
def apply_score_games(state,games):
 for g in games:
  if g['id'] in state['processed_ids']:continue
  team_stats=[]
  for team in [g['home'],g['away']]:
   rows=[r for r in g['players'] if r['team']==team];fga=fta=orb=turn=minutes=0.
   for r in rows:
    if r.get('participation')!='played':continue
    s=r.get('stats',{})
    pair=lambda k:float(str(s.get(k,'0-0')).split('-')[-1] or 0)
    fga+=pair('FG');fta+=pair('FT');orb+=float(s.get('OREB') or 0);turn+=float(s.get('TO') or 0);minutes+=r.get('minutes') or 0
   team_stats.append({'poss':fga+.44*fta-orb+turn,'elapsed':max(48.,minutes/5)})
  possession=sum(r['poss'] for r in team_stats)/2
  if possession<=0:raise ValueError('No usable possession estimate for '+g['id'])
  pace=possession*48/(sum(r['elapsed'] for r in team_stats)/2);day=game_day(g)
  for team,points,opponent in [(g['home'],g['home_score'],g['away_score']),(g['away'],g['away_score'],g['home_score'])]:
   row={'day':day,'points':points,'opp_points':opponent,'poss':possession,'pace':pace,'game_id':g['id']};state['teams'][team]=(state['teams'].get(team,[])+[row])[-20:];state['league']=(state['league']+[row])[-600:]
  state['processed_ids'].append(g['id']);state['latest_day']=max(state['latest_day'] or day,day)
