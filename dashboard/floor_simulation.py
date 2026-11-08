"""Stateless validated plans. Daily cash and effects reconcile to DecisionEngine.

No destination-specific causal lift is estimated. Add/remove are explicit extensions.
The UI, API, suggestions, preview, confirmation and export use this same model.
"""
import hashlib
import json
import math
import re
from collections import Counter
import numpy as np
import pandas as pd
from dashboard.decisions import triangular

CATALOG = {'move': 'A-MOVE-MACHINE', 'inspect': 'A-INSPECT',
           'lease': 'A-REPLACE-LEASE', 'maintenance': 'A-PREVENTIVE'}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def number(value, label, low, high, integer=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number.')
    if not low <= value <= high or (integer and int(value) != value):
        raise ValueError(f'{label} must be {"an integer " if integer else ""}between {low} and {high}.')
    return int(value) if integer else float(value)

def stats(samples):
    return dict(mean=float(samples.mean()), p10=float(np.quantile(samples, .1)),
                p90=float(np.quantile(samples, .9)), probability_positive=float((samples > 0).mean()))

class FloorSimulation:
    def __init__(self, bundle):
        self.b = bundle
        self.engine = bundle['engine']
        self.slots = bundle['slots'].set_index('location_id')
        self.initial = {s: str(r.machine_id) for s, r in self.slots.iterrows() if pd.notna(r.machine_id)}
        self.original_slot = {m:s for s,m in self.initial.items()}
        self.configurations = {str(r.machine_id):str(r.config_id) for _,r in self.slots.iterrows() if pd.notna(r.machine_id)}
        self.eligible = set(self.engine.eligible.index) & set(self.original_slot)
        self.forecast = self.engine.predictions.pivot(index='gaming_date', columns='machine_id', values='theo_prediction').fillna(0)
        self.baseline = self.forecast.sum(axis=1).to_numpy()
        self.cache = {}

    def catalog_eval(self, aid, target, retained):
        key = (aid, target, retained)
        if key not in self.cache:
            self.cache[key] = self.engine.evaluate(aid, target, retained=retained)
        return self.cache[key]

    def normalize(self, raw):
        if not isinstance(raw, dict):
            raise ValueError('Each action must be an object.')
        kind = raw.get('kind')
        allowed = {'id','kind','target','destination','other','proxy','cash','day','share','retained'}
        if set(raw) - allowed or kind not in {*CATALOG, 'swap', 'add', 'remove'}:
            raise ValueError('Unsupported action or field.')
        ident = raw.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', ident):
            raise ValueError('Action ID must contain 1–48 letters, digits, hyphens or underscores.')
        a = dict(id=ident, kind=kind)
        required = {'move': {'target','destination'}, 'swap': {'target','other'},
                    'inspect': {'target'}, 'lease': {'target'}, 'maintenance': {'target'},
                    'add': {'proxy','destination','cash','day','share'},
                    'remove': {'target','cash','day','share'}}[kind]
        optional = {'retained'} if kind in {*CATALOG, 'swap'} else set()
        if set(raw) - {'id','kind'} - required - optional or not required <= set(raw):
            raise ValueError('Missing or unexpected fields for this action.')
        for k in required:
            a[k] = raw[k]
        for k in ['target','destination','other','proxy']:
            if k in a and not isinstance(a[k], str):
                raise ValueError(f'{k} must be text.')
        if 'destination' in a and a['destination'] not in self.slots.index:
            raise ValueError('Destination must be a supplied slot.')
        if kind in ['move','swap','inspect','lease','remove'] and a['target'] not in self.eligible:
            raise ValueError('Choose an unchanged July-eligible original machine with 28 observed active days.')
        if kind == 'swap' and (a['other'] not in self.eligible or a['other'] == a['target']):
            raise ValueError('Swap requires two different eligible original machines.')
        if kind == 'maintenance' and a['target'] not in set(self.engine.eligible.manufacturer):
            raise ValueError('Unknown eligible manufacturer.')
        if kind in ['add','remove']:
            if kind == 'add' and a['proxy'] not in self.eligible:
                raise ValueError('Addition requires an eligible existing performance proxy.')
            a['cash'] = number(a['cash'], 'July cash cost', 0, 100000)
            a['day'] = number(a['day'], 'Activation day', 1, 30, True)
            a['share'] = number(a['share'], 'Demand share', 0, 1)
        else:
            a['retained'] = number(raw.get('retained', .5), 'Retained play', .1, 1)
        return a

    def describe(self, a):
        kind = a['kind']
        if kind in ['add','remove']:
            return dict(day=a['day'], cost=a['cash'], targets=[] if kind == 'add' else [a['target']],
                        action_type='WHATIF-'+kind.upper(), units=1, evaluations=[],
                        assumption=('WHAT-IF extension; entered cash is paid upfront. Addition uses an existing proxy, '
                                    'triangular performance 0.5/1/1.5 and entered incremental-play share. Removal loses '
                                    'forecast earnings except the share retained elsewhere. No resale or operating savings.'))
        targets = [a['target'], a['other']] if kind == 'swap' else [a['target']]
        aid = 'A-MOVE-MACHINE' if kind == 'swap' else CATALOG[kind]
        evaluated = [self.catalog_eval(aid, t, a['retained']) for t in targets]
        return dict(day=evaluated[0]['lead_days']+1, cost=sum(e['cost'] for e in evaluated),
                    targets=[t for e in evaluated for t in e['targets']], action_type=aid,
                    units=len(evaluated), evaluations=evaluated,
                    assumption=evaluated[0]['assumption'] + ' Probabilities are conditional on these assumptions.')

    def validate(self, plan):
        if not isinstance(plan, list) or len(plan) > 80:
            raise ValueError('Plan must be a list of at most 80 actions.')
        actions = [self.normalize(a) for a in plan]
        if len({a['id'] for a in actions}) != len(actions):
            raise ValueError('Action IDs must be unique.')
        described = [self.describe(a) for a in actions]
        counts, targets, reserved = Counter(), set(), set()
        for a,d in zip(actions, described):
            if targets & set(d['targets']):
                raise ValueError('Actions overlap: each original machine may be modified only once.')
            targets.update(d['targets']); counts[d['action_type']] += d['units']
            destinations = ([a['destination']] if 'destination' in a else
                            [self.original_slot[a['target']], self.original_slot[a['other']]] if a['kind']=='swap' else [])
            if reserved & set(destinations):
                raise ValueError('Destination is already reserved.')
            reserved.update(destinations)
        if len(counts) > 3:
            raise ValueError('Maximum three action types, including what-if add/remove types.')
        if sum(d['cost'] for d in described) > 100000 + 1e-8:
            raise ValueError('Plan exceeds the $100,000 cash budget.')
        for aid, count in counts.items():
            if aid in self.engine.catalog and count > self.engine.catalog[aid]['quantity_limit']:
                raise ValueError('Catalogue quantity limit exceeded for '+aid)
        removals = {a['target']: d['day'] for a,d in zip(actions,described) if a['kind']=='remove'}
        for a,d in zip(actions,described):
            if 'destination' in a:
                occupant = self.initial.get(a['destination'])
                if occupant and not (occupant in removals and removals[occupant] <= d['day']):
                    raise ValueError('Destination must be vacant by activation. Chained moves are unsupported; queue a timely removal or use swap.')
        return actions, described

    def layout(self, actions, described, day):
        layout = self.initial.copy()
        # Removals take effect at the boundary before arrivals on the same day.
        active = [(a,d) for a,d in zip(actions,described) if d['day'] <= day]
        for a,d in active:
            if a['kind'] == 'remove':
                layout.pop(self.original_slot[a['target']])
        for a,d in active:
            if a['kind'] == 'swap':
                s,t = self.original_slot[a['target']],self.original_slot[a['other']]
                layout[s],layout[t] = a['other'],a['target']
            elif a['kind'] == 'move':
                layout.pop(self.original_slot[a['target']]); layout[a['destination']] = a['target']
            elif a['kind'] == 'add':
                layout[a['destination']] = 'NEW-'+a['id']
        return layout

    def action_daily(self, a, d):
        benefit = np.zeros((30,1000)); cash = np.zeros(30); downtime = np.zeros(30)
        start = d['day']-1
        if a['kind'] in ['add','remove']:
            proxy = a.get('proxy',a.get('target'))
            f = self.forecast[proxy].to_numpy().copy(); f[:start] = 0
            effect = (triangular('addition-performance', .5, 1, 1.5)*a['share']
                      if a['kind']=='add' else np.repeat(-(1-a['share']),1000))
            benefit = f[:,None]*effect*self.engine.demand
            cash[0] = a['cash']
        else:
            for e in d['evaluations']:
                rule = self.engine.catalog[e['action_type']]
                cash[0] += rule['unit_cost_cents']/100
                cash[start:] += rule['recurring_cost_cents_per_day']/100
                downtime[start] += e['additional_theo_cost']
                weights = self.forecast.reindex(columns=e['targets'],fill_value=0).sum(axis=1).to_numpy(copy=True)
                weights[:start] = 0
                if e['action_type'] in ['A-PREVENTIVE','A-TECH-SHIFT'] or weights.sum() == 0:
                    weights = np.zeros(30); weights[start:] = 1
                weights = weights/weights.sum()
                gains = e['net'] + e['cost'] + e['additional_theo_cost']
                benefit += weights[:,None]*gains
        return benefit, cash, downtime

    def evaluate(self, plan, include_layouts=True):
        actions, desc = self.validate(plan)
        benefits = np.zeros((30,1000)); cash = np.zeros(30); down = np.zeros(30)
        for a,d in zip(actions,desc):
            b,c,t = self.action_daily(a,d); benefits += b; cash += c; down += t
        net_daily = benefits-down[:,None]-cash[:,None]
        cumulative = net_daily.cumsum(axis=0)
        earnings = self.baseline.cumsum() + (benefits-down[:,None]).cumsum(axis=0).mean(axis=1)
        days = []
        for i in range(30):
            row = dict(day=i+1, date=f'2025-07-{i+1:02}', baseline=float(self.baseline[:i+1].sum()),
                       expected_gaming_earnings=float(earnings[i]), cash_paid=float(cash[:i+1].sum()),
                       daily_cash=float(cash[i]), downtime_opportunity=float(down[:i+1].sum()),
                       **stats(cumulative[i]), activated=[a['id'] for a,d in zip(actions,desc) if d['day']==i+1])
            if include_layouts:
                row['layout'] = self.layout(actions, desc, i+1)
                row['machine_count'] = len(row['layout'])
            days.append(row)
        public_actions = [{**a, **{k:v for k,v in d.items() if k!='evaluations'}} for a,d in zip(actions,desc)]
        return dict(plan=actions, plan_id=digest(actions), actions=public_actions, configurations=self.configurations.copy(), cash_committed=float(cash.sum()),
                    remaining_budget=float(100000-cash.sum()), days=days, summary=days[-1], _net=cumulative[-1])

    def preview(self, plan, action):
        old = self.evaluate(plan,False)
        a = self.normalize(action)
        new = self.evaluate(old['plan']+[a])
        new['marginal'] = stats(new['_net']-old['_net'])
        new['additional_cash'] = new['cash_committed']-old['cash_committed']
        new['estimate_id'] = digest({'plan': old['plan'],'action':a})
        return new

    def confirm(self, plan, action, estimate_id):
        preview = self.preview(plan,action)
        if estimate_id != preview['estimate_id']:
            raise ValueError('Preview does not match this plan and action. Review the change again.')
        return preview

    def undo(self, plan, action_id):
        actions,_ = self.validate(plan)
        if action_id not in {a['id'] for a in actions}:
            raise ValueError('Unknown action ID.')
        # Validation rejects removing a removal while an arrival depends on it.
        return self.evaluate([a for a in actions if a['id'] != action_id])

    def suggestions(self, plan):
        base = self.evaluate(plan,False)
        actions,desc = self.validate(plan)
        occupied = self.layout(actions,desc,3)
        reserved = {a['destination'] for a in actions if 'destination' in a}
        for a in actions:
            if a['kind']=='swap':
                reserved.update([self.original_slot[a['target']], self.original_slot[a['other']]])
        vacancies = sorted(set(self.slots.index)-set(occupied)-reserved)
        candidates = []
        for m in sorted(self.eligible):
            if vacancies:
                candidates.append(dict(id='suggest-move-'+m,kind='move',target=m,destination=vacancies[0]))
            candidates.append(dict(id='suggest-lease-'+m,kind='lease',target=m))
        for mf in sorted(self.engine.eligible.manufacturer.unique()):
            candidates.append(dict(id='suggest-maint-'+re.sub('[^A-Za-z0-9]','',mf),kind='maintenance',target=mf))
        results=[]
        for a in candidates:
            try:
                normalized,ds = self.validate(actions+[a])
            except ValueError:
                continue
            # Nonoverlap means marginal action samples add exactly to the current plan.
            last = normalized[-1]; d = ds[-1]
            b,c,t = self.action_daily(last,d)
            margin = stats((b-t[:,None]-c[:,None]).sum(axis=0))
            if margin['mean'] > 0:
                results.append(dict(action=last, marginal=margin,cost=d['cost'],day=d['day'],affected=len(d['targets'])))
        results.sort(key=lambda x:(-x['marginal']['mean'],x['cost'],x['action']['id']))
        return dict(plan_id=base['plan_id'], suggestions=results[:3], searched=len(candidates),
                    scope='Top individually feasible moves, leases and manufacturer maintenance only; not global layout optimization. Move destinations use the first legal slot; location-specific effects are unknown. Add/remove, swaps and combinations are excluded.')

    def bootstrap(self):
        machines=json.loads(self.b['machines'].to_json(orient='records',date_format='iso'))
        for machine in machines:
            machine['config_id'] = self.configurations.get(machine['machine_id'])
        return dict(slots=json.loads(self.b['slots'].to_json(orient='records',date_format='iso')),
                    machines=machines, eligible=sorted(self.eligible), catalog=self.b['report']['action_catalog'],
                    initial=self.initial, result=public(self.evaluate([])),
                    model='Shared DecisionEngine: 1,000 deterministic seeded draws; July machine forecasts. Synthetic data; effects are assumptions. Artwork and guests are decorative, not a surveyed building or customer simulation.')

def public(result):
    return {k:v for k,v in result.items() if not k.startswith('_')}
