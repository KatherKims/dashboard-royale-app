"""Reproducible retrospective analysis and assumption-driven July decision search.

Run locally: python analysis/pipeline.py --data PATH_TO_DATA --output data
The same run() function is executed in Databricks against the project volume.
"""
from pathlib import Path
from itertools import combinations
import argparse
import hashlib
import io
import json
import math
import numpy as np
import pandas as pd


def records(df):
    return json.loads(df.to_json(orient='records', date_format='iso'))


def run(root, output, execution='local'):
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    sources = {}
    def read(name):
        direct = root/(name+'.parquet')
        files = [direct] if direct.is_file() else list(root.rglob(name+'.parquet'))
        assert len(files) == 1, (name, files)
        p = files[0]
        sources[name] = {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'file':p.name}
        df = pd.read_parquet(p)
        for c in df.columns:
            if (c.endswith(('_usd','_cents')) and not df[c].astype(str).str.contains('|',regex=False).any()) or c in ['configured_rtp','payout_multiplier_variance']:
                df[c] = pd.to_numeric(df[c])
        return df

    d=read('prepared_daily_view'); prop=read('property_day'); players=read('player_period')
    meters=read('machine_day'); machines=read('machines'); gm=read('game_math')
    actions=read('action_catalog'); ledger=read('loyalty_ledger')
    traffic=read('zone_traffic_hourly'); events=read('events')
    for df in [d,prop,meters]: df['gaming_date']=pd.to_datetime(df.gaming_date)
    for col in ['install_date','retire_date']: machines[col]=pd.to_datetime(machines[col])
    assert not d.duplicated(['machine_id','gaming_date']).any()
    assert not meters.duplicated(['machine_id','gaming_date']).any()
    assert not prop.gaming_date.duplicated().any()
    a=d[d.active].copy()
    assert np.allclose(a.coin_in_usd-a.payout_usd,a.house_win_usd,atol=.001)
    assert np.allclose(a.coin_in_usd*(1-a.configured_rtp),a.theo_usd,atol=.0001)
    assert abs(a.house_win_usd.sum()-prop.house_win_usd.sum()) < .01
    assert np.allclose(players.tracked_payout_usd-players.tracked_coin_in_usd,players.tracked_net_usd,atol=.001)
    a=a.merge(meters[['machine_id','gaming_date','scheduled_seconds','available_seconds','sum_bet_squared']],on=['machine_id','gaming_date'],validate='one_to_one')
    a=a.merge(gm[['config_id','payout_multiplier_variance']],on='config_id',validate='many_to_one')
    assert a.available_seconds.between(0,a.scheduled_seconds).all()
    a['scheduled_hours']=a.scheduled_seconds/3600
    a['down_hours']=(a.scheduled_seconds-a.available_seconds)/3600
    a['weekday']=a.gaming_date.dt.dayofweek
    a['variance_usd2']=a.sum_bet_squared*a.payout_multiplier_variance/10000
    a['coin_per_hour']=a.coin_in_usd/a.available_hours.replace(0,np.nan)
    # Retrospective rate estimates: only days with at least 20 available hours.
    operating=a[a.available_hours>=20]
    rates=operating.groupby(['machine_id','weekday']).coin_per_hour.quantile([.25,.5,.75]).unstack()
    fallback=operating.groupby('machine_id').coin_per_hour.quantile([.25,.5,.75]).unstack()
    a=a.join(rates.rename(columns={.25:'rate_low',.5:'rate_mid',.75:'rate_high'}),on=['machine_id','weekday'])
    for q,col in [(.25,'rate_low'),(.5,'rate_mid'),(.75,'rate_high')]:
        a[col]=a[col].fillna(a.machine_id.map(fallback[q]))
        a[col]=a[col].fillna(operating.coin_per_hour.median())
        a['missed_wagers_'+col.split('_')[1]]=a.down_hours*a[col]
    a['missed_theo_mid']=a.missed_wagers_mid*(1-a.configured_rtp)
    agg={'house_win_usd':'sum','theo_usd':'sum','coin_in_usd':'sum','available_hours':'sum',
         'scheduled_hours':'sum','down_hours':'sum','variance_usd2':'sum','missed_theo_mid':'sum',
         'missed_wagers_low':'sum','missed_wagers_mid':'sum','missed_wagers_high':'sum'}
    m=a.groupby('machine_id').agg(agg).reset_index()
    m=m.merge(a.groupby('machine_id').gaming_date.agg(active_days='count',first_day='min',last_day='max'),on='machine_id')
    m=m.merge(machines,on='machine_id',validate='one_to_one')
    m['eligible_july']=(m.install_date<=pd.Timestamp('2025-07-01')) & (m.retire_date.isna() | (m.retire_date>pd.Timestamp('2025-07-01')))
    m['availability']=m.available_hours/m.scheduled_hours
    m['theo_per_hour']=m.theo_usd/m.available_hours.replace(0,np.nan)
    m['actual_per_day']=m.house_win_usd/m.active_days
    m['payout_gap']=m.house_win_usd-m.theo_usd
    m['payout_sd']=np.sqrt(m.variance_usd2)
    m['standardized_gap']=m.payout_gap/m.payout_sd.replace(0,np.nan)
    m=m.sort_values(['house_win_usd','machine_id'])
    # Same game/theme is a descriptive peer comparison, not location-adjusted causality.
    m['theme_peer_theo_per_hour']=m.groupby('theme').theo_per_hour.transform('median')
    m['peer_ratio']=m.theo_per_hour/m.theme_peer_theo_per_hour

    prop=prop.sort_values('gaming_date'); prop['month']=prop.gaming_date.dt.strftime('%Y-%m')
    prop['weekday']=prop.gaming_date.dt.dayofweek
    monthly=prop.groupby('month').agg(days=('gaming_date','count'),wagers=('coin_in_usd','sum'),actual=('house_win_usd','sum'),expected=('theo_usd','sum'),comps=('comp_cost_usd','sum'),comp_face=('comp_face_value_usd','sum'),hours=('available_machine_hours','sum')).reset_index()
    monthly['wagers_per_day']=monthly.wagers/monthly.days
    monthly['wagers_per_available_hour']=monthly.wagers/monthly.hours
    monthly['comp_cost_per_theo']=monthly.comps/monthly.expected
    zone=a.groupby(['month','zone_name','bank_id']).agg(wagers=('coin_in_usd','sum'),theo=('theo_usd','sum'),available_hours=('available_hours','sum'),downtime_hours=('down_hours','sum')).reset_index()
    zone['wagers_per_available_hour']=zone.wagers/zone.available_hours
    ev=[]
    # Weekday-adjusted associations use non-event days as the baseline. Not causal effects.
    non_event=prop[prop.events_active.isna() | prop.events_active.eq('')]
    week_baseline=non_event.groupby('weekday').coin_in_usd.mean()
    for row in events.itertuples():
        sub=prop[prop.gaming_date.between(pd.Timestamp(row.start_date),pd.Timestamp(row.end_date))]
        expected=sub.weekday.map(week_baseline).fillna(non_event.coin_in_usd.mean()).sum()
        ev.append({'event':row.name,'start':str(row.start_date),'end':str(row.end_date),'days':len(sub),
                   'wagers':float(sub.coin_in_usd.sum()),'weekday_baseline':float(expected),
                   'difference_pct':float(sub.coin_in_usd.sum()/expected-1) if expected else None})
    # Hourly sensors count entries, not people. Exclude offline/missing intervals.
    traffic['gaming_date']=(pd.to_datetime(traffic.hour_start_local)-pd.Timedelta(hours=6)).dt.normalize()
    traffic['month']=traffic.gaming_date.dt.strftime('%Y-%m')
    traffic['valid']=traffic.entries_count.notna() & (traffic.coverage_minutes>0)
    traffic['entries_count']=traffic.entries_count.where(traffic.valid)
    traffic['coverage_minutes']=traffic.coverage_minutes.where(traffic.valid,0)
    sensor=traffic.groupby(['month','zone_id']).agg(observed_entries=('entries_count',lambda x:x.sum(min_count=1)),covered_minutes=('coverage_minutes','sum'),valid_intervals=('valid','sum'),intervals=('valid','size')).reset_index()
    sensor['entries_per_covered_hour']=sensor.observed_entries/(sensor.covered_minutes/60)
    sensor['valid_interval_share']=sensor.valid_intervals/sensor.intervals

    # Player totals and concentration: sum each player over the whole six months first.
    p=players.groupby('player_id')[['tracked_coin_in_usd','tracked_payout_usd','tracked_net_usd']].sum()
    n_top=max(1,math.ceil(len(p)*.01)); losses=(-p.tracked_net_usd).clip(lower=0)
    player_summary={'tracked_players':len(p),'tracked_wagers':float(p.tracked_coin_in_usd.sum()),
                    'tracked_payouts':float(p.tracked_payout_usd.sum()),'player_net':float(p.tracked_net_usd.sum()),
                    'players_ahead_share':float((p.tracked_net_usd>0).mean()),
                    'top1pct_count':n_top,'top1pct_wager_share':float(p.tracked_coin_in_usd.nlargest(n_top).sum()/p.tracked_coin_in_usd.sum()),
                    'top1pct_positive_loss_share':float(losses.nlargest(n_top).sum()/losses.sum()),
                    'tracked_wager_coverage':float(p.tracked_coin_in_usd.sum()/prop.coin_in_usd.sum())}
    guests=players.groupby(['period_month','home_region','age_band'],dropna=False).agg(
        wagers=('tracked_coin_in_usd','sum'),payouts=('tracked_payout_usd','sum'),player_net=('tracked_net_usd','sum'),
        expected=('theo_usd','sum'),comp_cost=('comp_cost_usd','sum'),player_months=('player_id','count')).reset_index()
    # Correct local gaming day for ledger timestamps, including daylight saving.
    local_time=pd.to_datetime(ledger.event_at_utc,utc=True).dt.tz_convert('America/Los_Angeles').dt.tz_localize(None)
    ledger['gaming_month']=(local_time-pd.Timedelta(hours=6)).dt.strftime('%Y-%m')
    redeemed=ledger[(ledger.event_type=='redeem') & ledger.gaming_month.between('2025-01','2025-06')].copy()
    loyalty=redeemed.groupby('gaming_month').agg(points_delta=('points_delta','sum'),face_cents=('face_value_cents','sum'),cost_cents=('economic_cost_cents','sum'),redemptions=('loyalty_event_id','count')).reset_index()
    loyalty['points_per_face_dollar']=-loyalty.points_delta/(loyalty.face_cents/100)
    assert abs(loyalty.cost_cents.sum()/100-prop.comp_cost_usd.sum()) < .01

    # Freeze both forecasts on Jan-Apr and evaluate May-Jun without future inputs.
    train=prop[prop.gaming_date<'2025-05-01'].copy(); test=prop[prop.gaming_date>='2025-05-01'].copy()
    weekday_means=train.groupby('weekday').coin_in_usd.mean(); baseline=train.coin_in_usd.mean()
    test['weekday_prediction']=test.weekday.map(weekday_means); test['constant_prediction']=baseline
    weekday_mae=float((test.coin_in_usd-test.weekday_prediction).abs().mean())
    constant_mae=float((test.coin_in_usd-test.constant_prediction).abs().mean())
    winner='weekday' if weekday_mae<constant_mae else 'constant'
    forecast={'train_start':'2025-01-01','train_end':'2025-04-30','test_start':'2025-05-01','test_end':'2025-06-30',
              'weekday_mae':weekday_mae,'constant_mae':constant_mae,'winner':winner,
              'improvement_pct':1-min(weekday_mae,constant_mae)/constant_mae,
              'test_rows':records(test[['gaming_date','coin_in_usd','weekday_prediction','constant_prediction']])}
    july=pd.date_range('2025-07-01','2025-07-30')
    july_pred=prop.groupby('weekday').coin_in_usd.mean().reindex(july.dayofweek).to_numpy() if winner=='weekday' else np.repeat(prop.coin_in_usd.mean(),30)
    forecast['july_refit_baseline_wagers']=float(july_pred.sum())
    forecast['july_refit_note']='Winner refit on Jan-Jun after holdout evaluation; July is a scenario, not a validated forecast.'

    # Candidate set is deliberately small. Effects below are ASSUMPTIONS, not treatment estimates.
    rng=np.random.default_rng(20251107); N=1000
    fitted=train.weekday.map(weekday_means) if winner=='weekday' else pd.Series(baseline,index=train.index)
    errors=(train.coin_in_usd/fitted).to_numpy()
    demand=rng.choice(errors,size=(N,30),replace=True).mean(axis=1)
    retention=rng.triangular(.25,.5,1,size=N)
    catalog=actions.set_index('action_type_id')
    candidates=[]; samples=[]; conservative=[]
    eligible=m[m.eligible_july & (m.active_days>=28)]
    weak=eligible.sort_values('theo_per_hour').iloc[0]
    busiest_down=eligible.sort_values('missed_theo_mid',ascending=False).iloc[0]
    manuf=eligible.groupby('manufacturer').missed_theo_mid.sum().idxmax()
    zone_tot=a.groupby('zone_name').agg(theo=('theo_usd','sum'),hours=('available_hours','sum'))
    zone_name=(zone_tot.theo/zone_tot.hours).idxmin()
    def add(key,aid,target,benefit,assumption,targets=(),extra_downtime_cost=0,conservative_benefit=0):
        rule=catalog.loc[aid]; days=max(0,30-int(rule.lead_days))
        cost=float(rule.unit_cost_cents+rule.recurring_cost_cents_per_day*days)/100
        assert int(rule.quantity_limit)>=1
        b=np.broadcast_to(benefit,(N,)).astype(float)
        samples.append(b-cost-extra_downtime_cost)
        conservative.append(float(conservative_benefit)-cost-extra_downtime_cost)
        candidates.append({'id':key,'action_type':aid,'name':rule['name'],'target':str(target),'quantity':1,
                           'cost':cost,'lead_days':int(rule.lead_days),'benefit_days':days,
                           'catalogue_downtime_minutes':int(rule.downtime_minutes),'additional_theo_cost':float(extra_downtime_cost),
                           'targets':list(targets),'assumption':assumption,
                           'expected_net':float(samples[-1].mean())})
    # Inspection buys information. No unpriced correction benefit is silently credited.
    for mid in ['M-1158','M-1181']:
        r=eligible[eligible.machine_id==mid].iloc[0]
        add('inspect_'+mid,'A-INSPECT',mid,0,'Information only; no cash recovery credited without a corrective-action estimate.',[mid],2*r.theo_per_hour)
    base=float(weak.theo_usd/weak.active_days)
    move_effect=rng.triangular(-.1,.2,.6,size=N)
    add('move_weak','A-MOVE-MACHINE',weak.machine_id,base*28*move_effect*retention*demand,
        'Incremental play uplift triangular(-10%,20%,60%); floor retention triangular(25%,50%,100%). Destination not yet chosen; exploratory candidate.',[weak.machine_id],3*weak.theo_per_hour,
        conservative_benefit=base*28*(-.1))
    lease_uplift=rng.triangular(-.1,.5,1.5,size=N)
    add('lease_weak','A-REPLACE-LEASE',weak.machine_id,base*16*lease_uplift*retention*demand,
        'New title uplift triangular(-10%,50%,150%); floor retention 25%-100%; no observed replacement effect claimed.',[weak.machine_id],6*weak.theo_per_hour,conservative_benefit=-.1*base*16)
    floor_downtime=float(eligible.missed_theo_mid.sum())/181*23
    add('technician','A-TECH-SHIFT','One additional shift; roster to select',floor_downtime*rng.triangular(.1,.3,.6,N)*retention*demand,
        'Recovers 10%-60% (mode30%) of historical downtime opportunity scaled to 23 July days; assumes one shift can cover this opportunity.',eligible.machine_id.tolist())
    mf=eligible[eligible.manufacturer==manuf]
    add('preventive','A-PREVENTIVE',manuf,float(mf.missed_theo_mid.sum())/181*23*rng.triangular(.2,.5,.8,N)*retention*demand,
        'Recovers 20%-80% (mode50%) of manufacturer downtime; planned 90 minutes per machine deducted.',mf.machine_id.tolist(),1.5*mf.theo_per_hour.sum())
    zonebase=float(zone_tot.loc[zone_name,'theo'])/181*20
    add('signage','A-WAYFINDING',zone_name,zonebase*rng.triangular(0,.025,.08,N)*retention*demand,
        'Zone play uplift triangular(0%,2.5%,8%); retained incremental floor play 25%-100%. Observational location differences are not causal effects.',a[a.zone_name==zone_name].machine_id.unique().tolist())
    compbase=float(prop.comp_cost_usd.sum())/181*27
    theobase=float(prop.theo_usd.sum())/181*27
    comp_savings=rng.triangular(0,.1,.25,N); demand_loss=rng.triangular(0,.0005,.002,N)
    add('comp_policy','A-COMP-CHANGE','Floor-wide: proposed 12 points per comp face-value dollar',
        compbase*comp_savings-theobase*demand_loss*demand,
        'Proposed rate12 (catalogue range5-20); savings0%-25% (mode10%) and loss of expected gaming earnings0%-0.2% (mode0.05%) are assumptions, not proven effects.',
        conservative_benefit=-theobase*.002)
    add('comp_pilot','A-COMP-PILOT','Randomized pilot with unchanged total comp budget',0,
        'Information-only test; no immediate benefit or additional comp spend credited. Cannot combine with floor-wide change.')
    # Portfolios: <=3 action types, within budget, one unit of each explicit candidate.
    # Reject overlapping targets to avoid double-counting recovery or demand benefits.
    portfolios=[]; arr=np.vstack(samples)
    for k in range(len(candidates)+1):
        for combo in combinations(range(len(candidates)),k):
            cs=[candidates[i] for i in combo]
            if len(set(c['action_type'] for c in cs))>3 or sum(c['cost'] for c in cs)>100000: continue
            ids={c['id'] for c in cs}
            if {'comp_policy','comp_pilot'}<=ids: continue
            if any(set(candidates[i]['targets']) & set(candidates[j]['targets']) for i,j in combinations(combo,2)): continue
            # Floor-wide comp demand effects can overlap other play interventions: isolate them.
            if 'comp_policy' in ids and any(c['action_type'] not in ['A-COMP-CHANGE','A-INSPECT'] for c in cs): continue
            net=arr[list(combo)].sum(axis=0) if combo else np.zeros(N)
            portfolios.append({'actions':[c['id'] for c in cs],'cost':sum(c['cost'] for c in cs),
                'mean_net':float(net.mean()),'median_net':float(np.median(net)),
                'p10':float(np.quantile(net,.1)),'p90':float(np.quantile(net,.9)),
                'probability_positive':float((net>0).mean()),'conservative_net':sum(conservative[i] for i in combo)})
    portfolios.sort(key=lambda p:(-p['mean_net'],p['cost']))
    simulation={'seed':20251107,'scenarios':N,'objective':'Maximize expected 30-day incremental contribution',
                'horizon':'2025-07-01 to 2025-07-30','candidate_count':len(candidates),
                'feasible_portfolios':len(portfolios),'candidates':candidates,'portfolios':portfolios,
                'recommended':portfolios[0], 'learning_option':['inspect_M-1158'],
                'limitations':['Effects are assumed, not causal estimates. Probabilities are conditional on assumptions.',
                              'Simulation concerns theoretical contribution, not realized payout profit.',
                              'Common demand scenarios are used for all portfolios; shocks are bootstrapped independently by day.',
                              'Search is exhaustive only within this limited candidate list and conservative overlap exclusions.',
                              'Information value is unpriced; information-only actions may be worthwhile beyond 30 days.',
                              'Moving/replacement/signage targets require location and operational feasibility checks before implementation.']}

    # Unity Catalog volumes require sequential writes, not ZIP's random seeks.
    scenario_buffer=io.BytesIO()
    np.savez_compressed(scenario_buffer,net=arr)
    (output/'scenario_net.npz').write_bytes(scenario_buffer.getvalue())

    daily_out=a[['machine_id','gaming_date','month','zone_name','bank_id','config_id','house_win_usd','theo_usd','coin_in_usd','available_hours','scheduled_hours','down_hours','missed_wagers_low','missed_wagers_mid','missed_wagers_high','missed_theo_mid']].copy()
    daily_out.to_parquet(output/'machine_daily.parquet',index=False)
    prop.to_parquet(output/'property_daily.parquet',index=False)
    guests.to_parquet(output/'guest_groups.parquet',index=False)
    m.to_parquet(output/'machines.parquet',index=False)
    report={'execution':execution,'sources':sources,'validation':{'rows':len(d),'active_rows':len(a),'dates':[str(prop.gaming_date.min().date()),str(prop.gaming_date.max().date())],'money_and_ledger_reconciled':True},
            'monthly':records(monthly),'zone_monthly':records(zone),'event_associations':ev,'traffic':records(sensor),
            'players':player_summary,'loyalty':records(loyalty),'forecast':forecast,'simulation':simulation,
            'downtime':{'hours':float(a.down_hours.sum()),'missed_wagers_low':float(a.missed_wagers_low.sum()),
                        'missed_wagers_mid':float(a.missed_wagers_mid.sum()),'missed_wagers_high':float(a.missed_wagers_high.sum()),
                        'missed_theo_mid':float(a.missed_theo_mid.sum()),
                        'method':'Machine-by-weekday operating-day hourly wager rate, 25th/50th/75th percentiles; machine/global fallback. Historical machine opportunity, not net floor loss or confidence interval.'},
            'bottom10':records(m.head(10)), 'action_catalog':records(actions)}
    (output/'analysis_results.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--data',required=True); p.add_argument('--output',default='data')
    args=p.parse_args(); result=run(args.data,args.output)
    print(json.dumps({'forecast':{k:v for k,v in result['forecast'].items() if k!='test_rows'},
                      'players':result['players'],'downtime':result['downtime'],
                      'recommendation':result['simulation']['recommended']},indent=2))
