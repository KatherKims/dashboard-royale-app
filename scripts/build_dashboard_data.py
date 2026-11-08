"""Build small portable map/forecast exports from the supplied challenge files.

Local: python scripts/build_dashboard_data.py --source PATH_TO_CHALLENGE_DATA
Databricks: call build(source_volume, app_export_volume) after the main pipeline.
No API credentials or player-level exports are needed by the app.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard.forecast import build_forecasts


def build(source, output):
    source, output = Path(source), Path(output)
    hashes = {}
    def read(name):
        direct = source / (name + '.parquet')
        paths = [direct] if direct.is_file() else list(source.rglob(name + '.parquet'))
        if len(paths) != 1:
            raise ValueError(f'Expected one source for {name}, found {len(paths)}')
        hashes[name] = hashlib.sha256(paths[0].read_bytes()).hexdigest()
        return pd.read_parquet(paths[0])
    base = pd.read_parquet(output / 'machine_daily.parquet')
    machines = pd.read_parquet(output / 'machines.parquet')
    meters, game = read('machine_day'), read('game_math')
    configs = base[['machine_id', 'gaming_date', 'config_id']].copy()
    configs.gaming_date = pd.to_datetime(configs.gaming_date)
    meters.gaming_date = pd.to_datetime(meters.gaming_date)
    joined = configs.merge(meters[['machine_id', 'gaming_date', 'sum_bet_squared']], validate='one_to_one')
    joined = joined.merge(game[['config_id', 'payout_multiplier_variance']], validate='many_to_one')
    joined['variance_usd2'] = joined.sum_bet_squared.astype(float) * joined.payout_multiplier_variance.astype(float) / 10000
    assert len(joined) == len(base) and joined.variance_usd2.notna().all()
    joined[['machine_id', 'gaming_date', 'variance_usd2']].to_parquet(output / 'daily_variance.parquet', index=False)
    for name in ['floor_locations', 'floor_walkways', 'placements']:
        read(name).to_parquet(output / (name + '.parquet'), index=False)
    forecasts, metadata = build_forecasts(base, machines)
    forecasts.to_parquet(output / 'demand_predictions.parquet', index=False)
    metadata['source_hashes'] = hashes
    metadata['base_daily_sha256'] = hashlib.sha256((output / 'machine_daily.parquet').read_bytes()).hexdigest()
    (output / 'forecast_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', default=str(ROOT / 'data'))
    args = parser.parse_args()
    build(args.source, args.output)
