"""Cross-check exported facts and action feasibility. No credentials required."""
from pathlib import Path
import json
import unittest
import numpy as np
import pandas as pd

ROOT=Path(__file__).parents[1]/'data'

class ResultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((ROOT/'analysis_results.json').read_text())
        cls.d=pd.read_parquet(ROOT/'machine_daily.parquet')
        cls.m=pd.read_parquet(ROOT/'machines.parquet')

    def test_aggregates_reconcile(self):
        r,d,m=self.r,self.d,self.m
        self.assertEqual(len(d),r['validation']['active_rows'])
        self.assertFalse(d.duplicated(['machine_id','gaming_date']).any())
        for field,monthly in [('house_win_usd','actual'),('theo_usd','expected'),('coin_in_usd','wagers')]:
            self.assertAlmostEqual(d[field].sum(),m[field].sum(),places=5)
            self.assertAlmostEqual(d[field].sum(),sum(row[monthly] for row in r['monthly']),places=5)
        self.assertAlmostEqual(d.down_hours.sum(),r['downtime']['hours'],places=5)
        self.assertTrue((d.missed_wagers_low<=d.missed_wagers_mid).all())
        self.assertTrue((d.missed_wagers_mid<=d.missed_wagers_high).all())

    def test_every_portfolio_is_feasible(self):
        s=self.r['simulation'];cs={c['id']:c for c in s['candidates']}
        cat={c['action_type_id']:c for c in self.r['action_catalog']}
        eligible=set(self.m.loc[self.m.eligible_july,'machine_id'])
        for c in cs.values():
            rule=cat[c['action_type']]
            self.assertLessEqual(c['quantity'],rule['quantity_limit'])
            self.assertAlmostEqual(c['cost'],c['quantity']*(rule['unit_cost_cents']+rule['recurring_cost_cents_per_day']*max(0,30-rule['lead_days']))/100)
            if c['action_type'] in ['A-INSPECT','A-MOVE-MACHINE','A-REPLACE-LEASE']:
                self.assertIn(c['target'],eligible)
        for p in s['portfolios']:
            selected=[cs[i] for i in p['actions']]
            self.assertLessEqual(p['cost'],100000)
            self.assertLessEqual(len({c['action_type'] for c in selected}),3)
            self.assertAlmostEqual(p['cost'],sum(c['cost'] for c in selected))
            targets=[t for c in selected for t in c['targets']]
            self.assertEqual(len(targets),len(set(targets)))
            self.assertFalse({'comp_policy','comp_pilot'}<=set(p['actions']))

    def test_scenarios_match_exported_rankings(self):
        s=self.r['simulation'];arr=np.load(ROOT/'scenario_net.npz')['net']
        self.assertTrue(np.isfinite(arr).all())
        ids=[c['id'] for c in s['candidates']]
        self.assertEqual(arr.shape,(len(ids),s['scenarios']))
        for p in s['portfolios']:
            net=arr[[ids.index(i) for i in p['actions']]].sum(axis=0) if p['actions'] else np.zeros(s['scenarios'])
            self.assertAlmostEqual(net.mean(),p['mean_net'],places=5)
            self.assertAlmostEqual(np.quantile(net,.1),p['p10'],places=5)
        self.assertEqual(s['recommended']['mean_net'],max(p['mean_net'] for p in s['portfolios']))

if __name__=='__main__':unittest.main()
