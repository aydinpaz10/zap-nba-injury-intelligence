import fs from 'node:fs';
import { ratingMap, baselineFeatures, logisticProbability, simulateMatchup } from '../models/predictor.mjs';
import { forecastScores } from '../models/score-model.mjs';
const coeff = JSON.parse(fs.readFileSync(new URL('./synthetic-coefficients.json', import.meta.url)));
const players = {}, roster = [];
for (const team of ['HOME','AWAY']) for (let i=0;i<10;i++) {
  const id=team+i; roster.push(id);
  players[id]={name:'Synthetic '+id,team,last_day:'2025-01-04',last_participation:'played',history:Array.from({length:4},(_,j)=>({day:`2025-01-0${j+1}`,minutes:30,gmsc:8+i}))};
}
const state={players,teams:Object.fromEntries(['HOME','AWAY'].map((t,i)=>[t,{elo:1500+i*20,margins:[2,-1,5],last_day:'2025-01-04',season:2025,rosters:[]}])),transitions:{played:[1,9],absent:[1,1]},latest_day:'2025-01-04'};
const game={id:'synthetic-1',date:'2025-01-06T00:00:00Z',season:2025,home:'HOME',away:'AWAY'};
const rating=ratingMap(state,'2025-01-05');
const pool=t=>roster.filter(id=>id.startsWith(t)).map(id=>({id,rate:rating.ratings[id]?.rate??null,minutes:24,missing_probability:0.1}));
const simulation={home_pool:pool('HOME'),away_pool:pool('AWAY'),replacement:rating.replacement,base_features:baselineFeatures(state,game),adjusted_coefficients:coeff.win.adjusted.coefficients,default_overrides:{}};
const scoreEngine={version:coeff.score_model,coefficients:coeff.score_coefficients,rounding:'max(0, floor(raw + 0.5))',state:{teams:{},league:[],latest_day:'2025-01-04'}};
const score=forecastScores(scoreEngine,game,simulation);
score.evaluation_scope='Synthetic example only; no historical evaluation';
console.log(JSON.stringify({synthetic:true,coefficient_notice:coeff.notice,rating_example:rating.ratings.HOME0.rate,baseline_home_probability:logisticProbability(coeff.win.baseline.coefficients,simulation.base_features),adjusted:simulateMatchup(simulation),score},null,2));
