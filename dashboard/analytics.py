"""Period-aware evidence and time-valid placement resolution."""
import numpy as np
import pandas as pd


def machine_summary(daily, machines):
    result = daily.groupby('machine_id', as_index=False).agg(
        actual_house_win=('house_win_usd', 'sum'), expected_house_win=('theo_usd', 'sum'),
        total_wagers=('coin_in_usd', 'sum'), available_hours=('available_hours', 'sum'),
        scheduled_hours=('scheduled_hours', 'sum'), downtime_hours=('down_hours', 'sum'),
        estimated_downtime_opportunity=('missed_theo_mid', 'sum'),
        active_days=('gaming_date', 'nunique'), variance_usd2=('variance_usd2', 'sum'))
    metadata = ['machine_id', 'manufacturer', 'theme', 'install_date', 'retire_date',
                'lease_class', 'eligible_july']
    result = result.merge(machines[metadata], validate='one_to_one')
    result['availability_rate'] = result.available_hours / result.scheduled_hours.replace(0, np.nan)
    result['actual_per_active_day'] = result.actual_house_win / result.active_days
    result['expected_per_available_hour'] = result.expected_house_win / result.available_hours.replace(0, np.nan)
    result['actual_per_available_hour'] = result.actual_house_win / result.available_hours.replace(0, np.nan)
    result['actual_minus_expected'] = result.actual_house_win - result.expected_house_win
    result['payout_sd'] = np.sqrt(result.variance_usd2)
    result['standardized_gap'] = result.actual_minus_expected / result.payout_sd.replace(0, np.nan)
    result['theme_peer_expected_per_hour'] = result.groupby('theme').expected_per_available_hour.transform('median')
    result['peer_ratio_selected_period'] = result.expected_per_available_hour / result.theme_peer_expected_per_hour.replace(0, np.nan)
    return result


def machine_category(row):
    """Screening rules, not a claim about cause or a multiple-testing-adjusted test."""
    if row.get('active_days', 0) < 28:
        return 'Limited exposure'
    if row.get('standardized_gap', 0) <= -3:
        return 'Inspect configuration / meters'
    if row.get('availability_rate', 1) < .90 or row.get('estimated_downtime_opportunity', 0) > .10 * row.get('expected_house_win', np.inf):
        return 'Downtime-constrained'
    if row.get('peer_ratio_selected_period', 1) < .75:
        return 'Low expected demand'
    if row.get('actual_minus_expected', 0) < 0:
        return 'Monitor payout variance'
    return 'Monitor'


def floor_snapshot(placements, locations, machines, date):
    """Placements at 06:00 America/Los_Angeles, with end-exclusive validity."""
    local = pd.Timestamp(date).normalize() + pd.Timedelta(hours=6)
    instant = local.tz_localize('America/Los_Angeles').tz_convert('UTC')
    start = pd.to_datetime(placements.effective_from_utc, utc=True)
    end = pd.to_datetime(placements.effective_to_utc, utc=True)
    current = placements[(start <= instant) & (end.isna() | (end > instant))].copy()
    roster = machines[['machine_id', 'install_date', 'retire_date']].copy()
    installed = pd.to_datetime(roster.install_date)
    retired = pd.to_datetime(roster.retire_date)
    roster = roster[(installed <= local.normalize()) & (retired.isna() | (retired > local.normalize()))]
    current = current.merge(roster[['machine_id']], validate='many_to_one')
    if current.machine_id.duplicated().any() or current.location_id.duplicated().any():
        raise ValueError('Overlapping placements: cannot show an unambiguous floor snapshot.')
    slots = locations[locations.node_type == 'slot'].copy()
    return slots.merge(current[['machine_id', 'location_id', 'config_id']], how='left', on='location_id', validate='one_to_one')
