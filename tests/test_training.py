"""Synthetic fitting checks: do not reproduce or retrain the historical NBA evaluation."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'models'))
from engine_math import initial_state, apply_games, ratings

class TestChronology(unittest.TestCase):
    def test_rating_from_synthetic_games(self):
        state=initial_state()
        for day in range(1, 6):
            players=[{'id':str(i),'name':f'Fake {i}','team':'H' if i<6 else 'A','minutes':24,'participation':'played','stats':{'PTS':'12','FG':'5-10','FT':'2-2','OREB':'1','DREB':'3','AST':'2','STL':'1','BLK':'0','PF':'2','TO':'2'}} for i in range(12)]
            game={'id':str(day),'season':2025,'date':f'2025-01-0{day}T23:00:00Z','home':'H','away':'A','home_score':100,'away_score':90,'players':players}
            apply_games(state,[game])
        out, replacement, mean=ratings(state,'2025-01-06')
        self.assertEqual(len(out),12)
        self.assertEqual(out['0']['minutes'],120)
        self.assertAlmostEqual(out['0']['rate'],replacement)
        before, _, _=ratings(state,'2025-01-05')
        self.assertEqual(len(before),0)

class TestFitting(unittest.TestCase):
    def test_synthetic_optimizers_obey_constraints(self):
        import numpy as np
        from fit import fit_win, fit_score
        x=np.array([[1,-2],[1,-1],[1,1],[1,2]],dtype=float)
        w=fit_win(x,np.array([0,0,1,1]),0.1,True)
        self.assertGreaterEqual(w[-1],0)
        rows=[]
        for i in range(12):
            h=[1,i/10,0,0,.5,0,i/20,0]; a=[1,-i/10,0,0,-.5,0,0,i/20]
            rows.append({'home_features':h,'away_features':a,'actual_home':110+i,'actual_away':102-i})
        score=fit_score(rows,10)
        self.assertLessEqual(score[6],0)
        self.assertGreaterEqual(score[7],0)

class TestExclusionConfig(unittest.TestCase):
    def test_config_requires_unique_string_ids(self):
        import importlib.util, json, tempfile
        path=Path(__file__).resolve().parents[1] / 'validation' / 'train_engine.py'
        spec=importlib.util.spec_from_file_location('train_engine',path)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'ids.json'
            config.write_text(json.dumps(['fictional-event-a','fictional-event-b']))
            self.assertEqual(module.load_exclusions(config),{'fictional-event-a','fictional-event-b'})
            config.write_text(json.dumps([])); self.assertEqual(module.load_exclusions(config),set())
            for bad in [['x','x'],[''],[1],{'id':'x'}]:
                config.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): module.load_exclusions(config)
