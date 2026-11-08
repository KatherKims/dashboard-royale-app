"""Regression checks for date consistency, forecasting, placements and action scope."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard.analytics import machine_summary, floor_snapshot
from dashboard.forecast import build_forecasts
from dashboard.decisions import DecisionEngine, rank_portfolios

data = ROOT / 'data'
daily = pd.read_parquet(data/'machine_daily.parquet')
daily.gaming_date = pd.to_datetime(daily.gaming_date)
variance = pd.read_parquet(data/'daily_variance.parquet')
variance.gaming_date = pd.to_datetime(variance.gaming_date)
daily = daily.merge(variance, validate='one_to_one')
machines = pd.read_parquet(data/'machines.parquet')
prop = pd.read_parquet(data/'property_daily.parquet')
report = json.loads((data/'analysis_results.json').read_text())
predictions = pd.read_parquet(data/'demand_predictions.parquet')
predictions.gaming_date = pd.to_datetime(predictions.gaming_date)
full = machine_summary(daily, machines).set_index('machine_id')
np.testing.assert_allclose(full.loc['M-1158','standardized_gap'], machines.set_index('machine_id').loc['M-1158','standardized_gap'])
june = machine_summary(daily[daily.gaming_date.dt.month == 6], machines).set_index('machine_id')
assert june.loc['M-1158','standardized_gap'] != full.loc['M-1158','standardized_gap']

placements = pd.read_parquet(data/'placements.parquet')
locations = pd.read_parquet(data/'floor_locations.parquet')
july = floor_snapshot(placements, locations, machines, '2025-07-01')
assert not july.machine_id.dropna().duplicated().any()
assert not july.location_id.duplicated().any()
assert july.machine_id.notna().sum() == int(machines.eligible_july.sum())
assert not {'M-1118','M-1120'} & set(july.machine_id)
assert july[['x_m','y_m']].notna().all().all()

# Held-out targets must not change predictions or the April model-selection result.
changed = daily.copy()
changed.loc[changed.gaming_date >= '2025-05-01','coin_in_usd'] *= 9
original, original_meta = build_forecasts(daily, machines)
modified, modified_meta = build_forecasts(changed, machines)
hold = original.phase == 'May–June holdout'
np.testing.assert_allclose(original.loc[hold,'prediction'], modified.loc[hold,'prediction'])
assert original_meta['model'] == modified_meta['model']
assert original_meta['selection_mae'] == modified_meta['selection_mae']
assert original.loc[original.phase == 'July forecast','coin_in_usd'].isna().all()

engine = DecisionEngine(daily, machines, prop, report, predictions)
maintenance = engine.evaluate('A-PREVENTIVE','Ridgeline')
assert len(maintenance['targets']) > 1
expected = engine.eligible[engine.eligible.manufacturer == 'Ridgeline']
assert set(maintenance['targets']) == set(expected.index)
np.testing.assert_allclose(maintenance['additional_theo_cost'], 1.5 * expected.expected_per_available_hour.sum())
assert maintenance['benefit_days'] == 23
move = engine.evaluate('A-MOVE-MACHINE','M-5076')
assert move['benefit_days'] == 28
assert move['cost'] == 1800
try:
    engine.evaluate('A-MOVE-MACHINE','M-1118')
    raise AssertionError('Retired action was allowed')
except ValueError:
    pass
np.testing.assert_array_equal(move['net'], engine.evaluate('A-MOVE-MACHINE','M-5076')['net'])
candidates = engine.shortlist(report['simulation']['candidates'])
matching = next(c for c in candidates if c['id'] == 'move_weak')
np.testing.assert_array_equal(move['net'], matching['net'])
plans = rank_portfolios(candidates)
assert (plans.Cost <= 100000).all()
assert len(rank_portfolios(candidates, 0)) == 1
assert rank_portfolios(candidates, 0).iloc[0]['Expected net benefit'] == 0
print('PASS: period-specific variance, July occupancy, no holdout-target leakage, shared action math, catalog scope and budget.')
print('July occupied / empty:', int(july.machine_id.notna().sum()), int(july.machine_id.isna().sum()))
print('Candidate plans:', len(plans))
