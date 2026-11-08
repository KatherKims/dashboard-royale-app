"""One scenario engine for both portfolio ranking and the floor simulator.

Demand forecasts supply a July baseline. Intervention effects remain assumptions.
Shared seeded draws make comparisons repeatable without introducing slider noise.
"""
from itertools import combinations
import hashlib
import numpy as np
import pandas as pd
from dashboard.analytics import machine_summary


def triangular(channel, low, mode, high, n=1000):
    seed = int(hashlib.sha256(('aceiq-v2-' + channel).encode()).hexdigest()[:8], 16)
    return np.random.default_rng(seed).triangular(low, mode, high, n)


class DecisionEngine:
    def __init__(self, daily, machines, property_daily, report, predictions):
        self.daily = daily
        self.summary = machine_summary(daily, machines).set_index('machine_id')
        self.catalog = {r['action_type_id']: r for r in report['action_catalog']}
        self.eligible = self.summary[self.summary.eligible_july & (self.summary.active_days >= 28)]
        self.days = (daily.gaming_date.max() - daily.gaming_date.min()).days + 1
        self.property = property_daily
        self.predictions = predictions[predictions.phase == 'July forecast'].copy()
        ratios = self.summary.expected_house_win / self.summary.total_wagers.replace(0, np.nan)
        self.predictions['theo_prediction'] = self.predictions.prediction * self.predictions.machine_id.map(ratios)
        self.demand = triangular('demand', .85, 1., 1.15)
        self.latest = daily.sort_values('gaming_date').drop_duplicates('machine_id', keep='last').set_index('machine_id')

    def baseline(self, targets, lead):
        future = self.predictions[self.predictions.machine_id.isin(targets)]
        return float(future.loc[future.gaming_date >= pd.Timestamp('2025-07-01') + pd.Timedelta(days=lead), 'theo_prediction'].sum())

    def evaluate(self, aid, target, retained=.5, move_mode=.2, lease_mode=.5, recovery_mode=.5):
        """Evaluate one catalog unit; a manufacturer sweep is never a single machine."""
        rule = self.catalog[aid]
        lead = int(rule['lead_days']); days = max(0, 30 - lead)
        cost = (float(rule['unit_cost_cents']) + float(rule['recurring_cost_cents_per_day']) * days) / 100
        retention = triangular('retention', max(.1, retained - .25), retained, min(1., retained + .5))
        targets = []
        machine_actions = ['A-INSPECT', 'A-MOVE-MACHINE', 'A-REPLACE-LEASE']
        if aid in machine_actions:
            if target not in self.eligible.index:
                raise ValueError('July actions require an eligible machine with at least 28 observed active days.')
            targets = [target]
        elif aid == 'A-PREVENTIVE':
            targets = self.eligible[self.eligible.manufacturer == target].index.tolist()
        elif aid == 'A-TECH-SHIFT':
            targets = self.eligible.index.tolist()
        elif aid == 'A-WAYFINDING':
            targets = self.latest[self.latest.zone_name == target].index.intersection(self.eligible.index).tolist()
        if aid in ['A-PREVENTIVE', 'A-WAYFINDING'] and not targets:
            raise ValueError('No eligible machines in this action scope.')
        hourly = self.summary.loc[targets, 'expected_per_available_hour'].sum() if targets else 0.
        downtime = float(rule['downtime_minutes']) / 60 * hourly
        benefits = np.zeros(1000); stress_benefit = 0.
        baseline = self.baseline(targets, lead)
        if aid == 'A-MOVE-MACHINE':
            effect = triangular('move', -.1, move_mode, max(.6, move_mode + .4))
            benefits = baseline * effect * retention * self.demand
            stress_benefit = -.1 * baseline
            assumption = f'Move uplift triangular(-10%, {move_mode:.0%}, {max(.6, move_mode + .4):.0%}); destination demand is context, not a causal uplift estimate.'
        elif aid == 'A-REPLACE-LEASE':
            effect = triangular('lease', -.1, lease_mode, max(1.5, lease_mode + .65))
            benefits = baseline * effect * retention * self.demand
            stress_benefit = -.1 * baseline
            assumption = f'New-title uplift mode {lease_mode:.0%}, range -10% to {max(1.5, lease_mode + .65):.0%}; no observed treatment effect.'
        elif aid in ['A-PREVENTIVE', 'A-TECH-SHIFT']:
            mode = .3 if aid == 'A-TECH-SHIFT' else recovery_mode
            effect = triangular('recovery-' + aid, max(.05, mode - .3), mode, min(.95, mode + .3))
            opportunity = self.summary.loc[targets, 'estimated_downtime_opportunity'].sum() / self.days * days
            benefits = opportunity * effect * retention * self.demand
            assumption = f'Recover a share of historical downtime opportunity (mode {mode:.0%}) across {len(targets)} eligible machines; evidence denominator {self.days} calendar days.'
        elif aid == 'A-WAYFINDING':
            benefits = baseline * triangular('signage', 0, .025, .08) * retention * self.demand
            assumption = 'Signage uplift triangular(0%, 2.5%, 8%) across the zone; no causal effect established.'
        elif aid == 'A-COMP-CHANGE':
            comp_base = self.property.comp_cost_usd.sum() / self.days * days
            floor_base = self.baseline(self.eligible.index, lead)
            benefits = comp_base * triangular('comp-saving', 0, .1, .25) - floor_base * triangular('comp-demand-loss', 0, .0005, .002) * self.demand
            stress_benefit = -.002 * floor_base
            assumption = '12 points per face-value dollar; assumed savings 0–25% and expected gaming loss 0–0.2%. Information and guest welfare require a controlled pilot.'
        else:
            assumption = 'Information-only action. No unverified corrective financial benefit is credited.'
        net = benefits - cost - downtime
        return {'action_type': aid, 'name': rule['name'], 'target': str(target), 'targets': targets,
                'cost': cost, 'additional_theo_cost': float(downtime), 'lead_days': lead,
                'benefit_days': days, 'assumption': assumption, 'net': net,
                'expected_net': float(net.mean()), 'p10': float(np.quantile(net, .1)),
                'p90': float(np.quantile(net, .9)), 'probability_positive': float((net > 0).mean()),
                'conservative_net': float(stress_benefit - cost - downtime),
                'baseline': baseline, 'retained_mode': retained}

    def shortlist(self, original):
        """Preserve the original nine targets, recompute all with this engine."""
        results = []
        for item in original:
            updated = self.evaluate(item['action_type'], item['target'])
            updated['id'] = item['id']
            results.append(updated)
        return results


def rank_portfolios(candidates, budget=100000, multiplier=1.):
    rows = []
    for k in range(len(candidates) + 1):
        for subset in combinations(candidates, k):
            types = {c['action_type'] for c in subset}
            cost = sum(c['cost'] for c in subset)
            if len(types) > 3 or cost > budget:
                continue
            if {'A-COMP-CHANGE', 'A-COMP-PILOT'} <= types:
                continue
            if 'A-COMP-CHANGE' in types and types - {'A-COMP-CHANGE', 'A-INSPECT'}:
                continue
            if any(set(a['targets']) & set(b['targets']) for a, b in combinations(subset, 2)):
                continue
            net = np.zeros(1000)
            stress = 0.
            for c in subset:
                fixed = c['cost'] + c['additional_theo_cost']
                net += (c['net'] + fixed) * multiplier - fixed
                stress += (c['conservative_net'] + fixed) * multiplier - fixed
            rows.append({'Actions': ' + '.join(c['id'] for c in subset) or 'Keep budget',
                         'Cost': cost, 'Expected net benefit': float(net.mean()),
                         '10th percentile': float(np.quantile(net, .1)), '90th percentile': float(np.quantile(net, .9)),
                         'Chance positive': float((net > 0).mean()), 'Stress case': stress})
    return pd.DataFrame(rows)
