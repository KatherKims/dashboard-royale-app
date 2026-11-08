"""Read immutable local exports without regenerating source analysis."""
from pathlib import Path
import json
import pandas as pd
from dashboard.decisions import DecisionEngine
from dashboard.analytics import floor_snapshot

ROOT = Path(__file__).resolve().parents[1]

def load_bundle():
    data = ROOT / 'data'
    def read(name):
        return pd.read_parquet(data / (name + '.parquet'))
    daily = read('machine_daily')
    daily.gaming_date = pd.to_datetime(daily.gaming_date)
    variance = read('daily_variance')
    variance.gaming_date = pd.to_datetime(variance.gaming_date)
    daily = daily.merge(variance, on=['machine_id', 'gaming_date'], validate='one_to_one')
    machines, prop, predictions = read('machines'), read('property_daily'), read('demand_predictions')
    prop.gaming_date = pd.to_datetime(prop.gaming_date)
    predictions.gaming_date = pd.to_datetime(predictions.gaming_date)
    report = json.loads((data / 'analysis_results.json').read_text())
    locations, placements = read('floor_locations'), read('placements')
    return dict(daily=daily, machines=machines, property=prop, predictions=predictions,
                report=report, metadata=json.loads((data/'forecast_metadata.json').read_text()),
                guests=read('guest_groups'), locations=locations, placements=placements,
                slots=floor_snapshot(placements, locations, machines, '2025-07-01'),
                engine=DecisionEngine(daily, machines, prop, report, predictions))
