"""Independent reconciliation of the PDF's formulas against included exports.

The PDF contains source code, not the underlying data; this checks compatible
definitions and reconciled local exports rather than claiming PDF byte identity.
"""
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.data_bundle import load_bundle
from dashboard.analytics import machine_summary

class ReferenceConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=load_bundle()

    def test_money_and_daily_property_rollups(self):
        d,p=self.b['daily'],self.b['property'].set_index('gaming_date')
        self.assertAlmostEqual(d.coin_in_usd.sum(),248905219.25,places=2)
        self.assertAlmostEqual(d.house_win_usd.sum(),23638155.10,places=2)
        self.assertAlmostEqual(d.theo_usd.sum(),23545364.48,places=2)
        for src,dst in [('coin_in_usd','coin_in_usd'),('house_win_usd','house_win_usd'),('theo_usd','theo_usd'),('available_hours','available_machine_hours')]:
            np.testing.assert_allclose(d.groupby('gaming_date')[src].sum(),p[dst],rtol=1e-10,atol=1e-6)
        np.testing.assert_allclose(p.coin_in_usd-p.house_win_usd,p.payout_usd,atol=1e-6)

    def test_monthly_exposure_and_selected_variance(self):
        d=self.b['daily'];p=self.b['property']
        dm=d.assign(month=d.gaming_date.dt.strftime('%Y-%m')).groupby('month').agg(wagers=('coin_in_usd','sum'),hours=('available_hours','sum'))
        pm=p.assign(month=p.gaming_date.dt.strftime('%Y-%m')).groupby('month').agg(wagers=('coin_in_usd','sum'),hours=('available_machine_hours','sum'))
        np.testing.assert_allclose(dm.wagers/dm.hours,pm.wagers/pm.hours)
        for part in [d,d[d.gaming_date.dt.month==6],d[d.gaming_date==d.gaming_date.min()]]:
            summary=machine_summary(part,self.b['machines']).set_index('machine_id')
            grouped=part.groupby('machine_id')
            expected=(grouped.house_win_usd.sum()-grouped.theo_usd.sum())/np.sqrt(grouped.variance_usd2.sum())
            np.testing.assert_allclose(summary.standardized_gap,expected,equal_nan=True)

    def test_guests_comp_and_event_units(self):
        b=self.b;g=b['guests'];r=b['report'];p=b['property'];loyalty=pd.DataFrame(r['loyalty'])
        np.testing.assert_allclose(g.player_net,g.payouts-g.wagers,atol=1e-6)
        self.assertAlmostEqual(g.wagers.sum(),163804869.65,places=2)
        self.assertAlmostEqual(g.payouts.sum(),148219409.05,places=2)
        self.assertAlmostEqual(loyalty.cost_cents.sum()/100,p.comp_cost_usd.sum(),places=2)
        self.assertAlmostEqual(loyalty.face_cents.sum()/100,p.comp_face_value_usd.sum(),places=2)
        np.testing.assert_allclose(loyalty.points_per_face_dollar,-loyalty.points_delta/(loyalty.face_cents/100))
        events=pd.DataFrame(r['event_associations'])
        np.testing.assert_allclose(events.difference_pct,events.wagers/events.weekday_baseline-1)
        traffic=pd.DataFrame(r['traffic'])
        np.testing.assert_allclose(traffic.entries_per_covered_hour,traffic.observed_entries/(traffic.covered_minutes/60))

    def test_forecast_scores_and_no_july_actuals(self):
        b=self.b;pred=b['predictions'];hold=pred[pred.phase=='May–June holdout'];meta=b['metadata']
        self.assertAlmostEqual((hold.prediction-hold.coin_in_usd).abs().mean(),meta['holdout_mae'],places=6)
        self.assertAlmostEqual((hold.constant-hold.coin_in_usd).abs().mean(),meta['baseline_mae'],places=6)
        self.assertTrue(pred.loc[pred.phase=='July forecast','coin_in_usd'].isna().all())
        self.assertNotAlmostEqual(1-meta['holdout_mae']/meta['baseline_mae'],b['report']['forecast']['improvement_pct'],places=2)

if __name__=='__main__':unittest.main()
