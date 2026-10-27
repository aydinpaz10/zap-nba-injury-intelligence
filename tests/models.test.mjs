import {test} from 'node:test';
import assert from 'node:assert/strict';
import {ratingMap,productionLoss,simulateMatchup,logisticProbability} from '../models/predictor.mjs';
import {forecastScores} from '../models/score-model.mjs';

test('rating thresholds and no future player history',()=>{
 const s={players:{a:{name:'A',team:'H',last_day:'2025-01-01',history:[{day:'2025-01-01',minutes:100,gmsc:30},{day:'2025-01-06',minutes:100,gmsc:999}]},b:{name:'B',team:'A',last_day:'2025-01-01',history:[{day:'2025-01-01',minutes:99,gmsc:30}]}}};
 const r=ratingMap(s,'2025-01-05');assert.equal(r.ratings.a.minutes,100);assert.equal(r.ratings.b,undefined);assert.ok(Math.abs(r.ratings.a.rate-10.8)<1e-12);
});
test('minutes are capped and loss changes probability with absences',()=>{
 const pool=Array.from({length:10},(_,i)=>({id:String(i),rate:i===0?30:10,minutes:24,missing_probability:0}));
 const sim={home_pool:pool,away_pool:pool.map(p=>({...p,id:'a'+p.id})),replacement:8,base_features:[1,0,0,0,0],adjusted_coefficients:[.2,0,0,0,0,.5],default_overrides:{}};
 const result=productionLoss(pool,8,{'0':0});assert.equal(result.minutes[0],0);assert.ok(result.minutes.every(m=>m<=48));
 const full=simulateMatchup(sim,{'0':1}),out=simulateMatchup(sim,{'0':0});assert.ok(out.home_probability<full.home_probability);assert.equal(out.home_probability+out.away_probability,1);
 assert.equal(logisticProbability([0],[1]),.5);
});
test('score inference rejects same-day state and rounds scores',()=>{
 const g={date:'2025-01-05T23:00:00Z',home:'H',away:'A'};const e={version:'example',coefficients:[110.5,0,0,0,0,0,0,0],state:{latest_day:'2025-01-04',teams:{},league:[]}};
 assert.equal(forecastScores(e,g,null).display_home,111);e.state.latest_day='2025-01-05';assert.equal(forecastScores(e,g,null).available,false);
});
