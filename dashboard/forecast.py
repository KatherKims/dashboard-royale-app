"""Transparent daily machine-demand forecasting with an untouched final test.

Jan-Mar fits candidates; April selects one and supplies illustrative error bands.
Jan-Apr refits the selected specification; May-Jun is the final holdout.
No realized holdout wagers, uptime, weather, or event outcomes are predictors.
"""
import numpy as np
import pandas as pd


def fit_predict(train, target, machines):
    train = train.copy()
    target = target.copy()
    train['weekday'] = pd.to_datetime(train.gaming_date).dt.dayofweek
    target['weekday'] = pd.to_datetime(target.gaming_date).dt.dayofweek
    means = train.groupby('machine_id').coin_in_usd.mean()
    themes = machines.set_index('machine_id').theme
    theme_means = train.assign(theme=train.machine_id.map(themes)).groupby('theme').coin_in_usd.mean()
    target['constant'] = target.machine_id.map(means).fillna(target.machine_id.map(themes).map(theme_means)).fillna(train.coin_in_usd.mean())
    # Shrink sparse machine/weekday estimates toward its mean × floor weekday shape.
    floor = train.groupby(['gaming_date', 'weekday']).coin_in_usd.mean().reset_index()
    weekday_factor = floor.groupby('weekday').coin_in_usd.mean() / floor.coin_in_usd.mean()
    by_day = train.groupby(['machine_id', 'weekday']).coin_in_usd.agg(['sum', 'count'])
    target = target.join(by_day, on=['machine_id', 'weekday'])
    prior = target.constant * target.weekday.map(weekday_factor).fillna(1)
    target['weekday'] = (target['sum'].fillna(0) + 10 * prior) / (target['count'].fillna(0) + 10)
    target['unseen_machine'] = ~target.machine_id.isin(means.index)
    return target.drop(columns=['sum', 'count'])


def build_forecasts(daily, machines):
    daily = daily.copy()
    daily['gaming_date'] = pd.to_datetime(daily.gaming_date)
    cols = ['machine_id', 'gaming_date', 'zone_name', 'bank_id', 'coin_in_usd', 'house_win_usd', 'theo_usd']
    before_april = daily[daily.gaming_date < '2025-04-01']
    april = daily[daily.gaming_date.between('2025-04-01', '2025-04-30')]
    calibration = fit_predict(before_april, april[cols], machines)
    scores = {m: float((calibration[m] - calibration.coin_in_usd).abs().mean()) for m in ['constant', 'weekday']}
    winner = min(scores, key=scores.get)
    training = daily[daily.gaming_date < '2025-05-01']
    test = daily[daily.gaming_date >= '2025-05-01']
    holdout = fit_predict(training, test[cols], machines)
    # June 30 machine/zone metadata is used only for the future July scenario.
    eligible = machines.loc[machines.eligible_july, ['machine_id']]
    future = eligible.merge(pd.DataFrame({'gaming_date': pd.date_range('2025-07-01', '2025-07-30')}), how='cross')
    recent = daily.sort_values('gaming_date').drop_duplicates('machine_id', keep='last')
    future = future.merge(recent[['machine_id', 'zone_name', 'bank_id']], on='machine_id', validate='many_to_one')
    future['coin_in_usd'] = np.nan
    future['house_win_usd'] = np.nan
    future['theo_usd'] = np.nan
    future = fit_predict(daily, future, machines)
    for frame, phase in [(calibration, 'April calibration'), (holdout, 'May–June holdout'), (future, 'July forecast')]:
        frame['prediction'] = frame[winner]
        frame['phase'] = phase
    result = pd.concat([calibration, holdout, future], ignore_index=True)
    observed = holdout.coin_in_usd
    metadata = {
        'model': winner, 'selection_mae': scores,
        'holdout_mae': float((holdout[winner] - observed).abs().mean()),
        'baseline_mae': float((holdout.constant - observed).abs().mean()),
        'holdout_wape': float((holdout[winner] - observed).abs().sum() / observed.sum()),
        'unseen_holdout_machines': int(holdout.loc[holdout.unseen_machine, 'machine_id'].nunique()),
        'selection': 'Fit January–March, choose by machine-day MAE on April; shrinkage weight fixed at 10.',
        'test': 'Refit January–April, freeze predictions for May–June. Active roster is supplied; no observed test-day usage or availability enters features.',
        'future': 'Refit January–June for July 1–30 on the July-eligible roster. No July actuals exist.',
        'interval': 'April 10th/90th percentiles of aggregate relative residuals, scaled by predicted demand; illustrative daily bands, not guaranteed coverage or causal uncertainty.',
    }
    return result, metadata


def aggregate_predictions(rows, calibration):
    """Preserve cross-machine correlation by summing residuals on each date."""
    cols = ['coin_in_usd', 'prediction', 'constant', 'weekday']
    result = rows.groupby('gaming_date')[cols].sum(min_count=1).reset_index()
    cal = calibration.groupby('gaming_date')[['coin_in_usd', 'prediction']].sum(min_count=1)
    residual = (cal.coin_in_usd - cal.prediction) / cal.prediction.replace(0, np.nan)
    residual = residual.dropna()
    if len(residual) < 14:
        result['low'] = np.nan
        result['high'] = np.nan
    else:
        lo, hi = residual.quantile([.1, .9])
        result['low'] = np.maximum(0, result.prediction * (1 + lo))
        result['high'] = np.maximum(result.low, result.prediction * (1 + hi))
    return result
