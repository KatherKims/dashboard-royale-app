# Databricks notebook source
# MAGIC %md
# MAGIC # Dashboard Royale: original analysis and final product evidence
# MAGIC Original checks and historical results are retained below. **For the current dashboard, scroll to “FINAL PRODUCT — revision 2a124ca” near the end**, or open `Dashboard_Royale/05_Final_Product_Evidence`.
# MAGIC
# MAGIC Earlier sections describe the original property forecast/version-1 simulation. The final section uses the current machine-level forecast, shared floor simulator, current charts, source snapshot and cloud verification. Do not mix the historical 68.5% property-level score with the final 16.6% machine-day improvement.
# MAGIC
# MAGIC Final section: [successful Databricks run](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#job/796646835901211/run/1115290540544965). The original work was backed up in `Dashboard_Royale/01_data_checks_backup_before_final_2a124ca`.

# COMMAND ----------

daily = spark.table("workspace.default.prepared_daily_view")

print(f"Rows: {daily.count():,}")
print(f"Columns: {len(daily.columns)}")

display(daily.limit(5))

# COMMAND ----------

from pyspark.sql import functions as F

# Check dates and number of machines
display(daily.agg(
    F.min("gaming_date").alias("first_date"),
    F.max("gaming_date").alias("last_date"),
    F.countDistinct("gaming_date").alias("days"),
    F.countDistinct("machine_id").alias("machines")
))

# Each machine should have only one row per day
duplicates = (
    daily.groupBy("machine_id", "gaming_date")
    .count()
    .filter(F.col("count") > 1)
)
print("Duplicate machine-day groups:", duplicates.count())

# Check days when machines were active or inactive
display(daily.groupBy("active").count())

# COMMAND ----------

from pyspark.sql import functions as F

# Keep active machine-days; the original table stays intact.
active_daily = daily.filter(F.col("active") == True)

# Identify rows with missing inputs or results.
required = [
    "coin_in_usd", "payout_usd", "house_win_usd",
    "configured_rtp", "theo_usd"
]

missing = F.lit(False)
for column in required:
    missing = missing | F.col(column).isNull()

# Recalculate the two money figures.
expected_house_win = F.col("coin_in_usd") - F.col("payout_usd")

# Theo is stored to four decimal places.
expected_theo = F.round(
    F.col("coin_in_usd") * (1 - F.col("configured_rtp")), 4
)

checks = {
    "Rows with missing values": missing,
    "House win mismatches":
        F.col("house_win_usd") != expected_house_win,
    "Theo mismatches":
        F.col("theo_usd") != expected_theo
}

# Count rows flagged by each check.
results = active_daily.agg(*[
    F.sum(F.when(condition, 1).otherwise(0)).alias(name)
    for name, condition in checks.items()
]).first()

for name, count in results.asDict().items():
    print(f"{name}: {count:,}")

# COMMAND ----------

totals = active_daily.agg(
    F.sum("coin_in_usd").alias("wagers"),
    F.sum("payout_usd").alias("payouts"),
    F.sum("house_win_usd").alias("house_win"),
    F.sum("theo_usd").alias("theo")
).first()

for label, column in [
    ("Total wagers", "wagers"),
    ("Total payouts", "payouts"),
    ("Actual casino earnings before costs", "house_win"),
    ("Expected casino earnings before costs", "theo")
]:
    print(f"{label}: ${totals[column]:,.2f}")

if totals["wagers"] > 0:
    hold = totals["house_win"] / totals["wagers"]
    print(f"Overall hold: {hold:.2%}")

# COMMAND ----------

# Add up earnings for each machine, then select the lowest 10.
bottom10 = (
    active_daily
    .groupBy("machine_id")
    .agg(
        F.sum("house_win_usd").alias("total_house_win_usd")
    )
    .orderBy(F.col("total_house_win_usd").asc(), "machine_id")
    .limit(10)
)

display(bottom10)

# COMMAND ----------

# MAGIC %md
# MAGIC # Verified investigation results
# MAGIC These two charts were generated in Databricks by the successful `Luck and Downtime Lab` run. They are embedded here so the results are visible together with the original checks.
# MAGIC
# MAGIC - **M-1158:** $15,796.25 actual versus $51,961 expected; only 3.01 hours of downtime. The payout pattern deserves review, not a diagnosis of malfunction or wrongdoing.
# MAGIC - **M-1118 and M-1120:** retired before June ended, so exclude them from July replacement targets.
# MAGIC - **M-1065:** approximately 81.11 hours unavailable, the largest downtime among machines present at period end.
# MAGIC
# MAGIC These are saved results. The machine and scenario controls apply to the reproducible analysis below when you select **Run all**; the two saved overview images retain their original context.

# COMMAND ----------

from IPython.display import Image, display as show_image
show_image(Image(filename='/Volumes/workspace/default/dashboard_royale_source/analysis_exports/luck_vs_downtime.png'))


# COMMAND ----------

from IPython.display import Image, display as show_image
show_image(Image(filename='/Volumes/workspace/default/dashboard_royale_source/analysis_exports/M-1158_cumulative_earnings.png'))


# COMMAND ----------

# MAGIC %md
# MAGIC # The Gilded Ace — Luck & Downtime Lab
# MAGIC Investigate before replacing. Compare actual earnings, expected earnings and unavailable time, then explore a historical downtime-recovery scenario.
# MAGIC
# MAGIC **Learning guide:** Actual earnings = wagers minus payouts. Expected earnings (theo) use the configured payout rate. Their difference is a payout deviation, not proof that luck alone caused it. Downtime is scheduled time minus available time. Inactive days are excluded.
# MAGIC
# MAGIC All casino data is synthetic. Period: January 1–June 30, 2025. Change the machine and scenario controls, then **Run all** to refresh this notebook.

# COMMAND ----------

from pyspark.sql import functions as F
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from pathlib import Path
import json
import html

VOLUME = '/Volumes/workspace/default/dashboard_royale_source'
EXPORT = Path(VOLUME) / 'analysis_exports'
EXPORT.mkdir(exist_ok=True)
daily = spark.table('workspace.default.prepared_daily_view')
meters = spark.read.parquet(f'{VOLUME}/machine_day.parquet')
machines = spark.read.parquet(f'{VOLUME}/machines.parquet')
math = spark.read.parquet(f'{VOLUME}/game_math.parquet')
operations = spark.read.parquet(f'{VOLUME}/operations.parquet')
for name, data in [('royale_daily',daily), ('royale_meters',meters),
                   ('royale_machines',machines), ('royale_math',math)]:
    data.createOrReplaceTempView(name)


# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Build a fairer comparison
# MAGIC Raw meters supply actual scheduled seconds, including shortened days and partial periods. We retain all 310 machines so we can compare the manager's bottom ten with machines that had more downtime.
# MAGIC
# MAGIC **Checks:** one row per machine-day, valid scheduled/available seconds, unique game configurations, and reconciliation with your prepared table.

# COMMAND ----------

assert meters.groupBy('machine_id','gaming_date').count().filter('count > 1').count() == 0
assert math.groupBy('config_id').count().filter('count > 1').count() == 0
assert machines.groupBy('machine_id').count().filter('count > 1').count() == 0
assert meters.filter('active AND (available_seconds < 0 OR available_seconds > scheduled_seconds)').count() == 0
assert meters.filter('active').join(math, 'config_id', 'left_anti').count() == 0
prepared_total = daily.filter('active').agg(F.sum('house_win_usd')).first()[0]
raw_total = meters.filter('active').agg(F.sum('house_win_cents')).first()[0]
assert abs(float(prepared_total) - raw_total / 100) < 0.001

diagnostics = spark.sql('''
WITH a AS (
 SELECT d.machine_id, count(*) AS active_days,
        min(d.gaming_date) AS first_active_date, max(d.gaming_date) AS last_active_date,
        sum(d.house_win_cents)/100.0 AS actual_usd,
        sum(d.theo_cents)/100.0 AS expected_usd,
        sum(d.coin_in_cents)/100.0 AS wagers_usd,
        sum(d.scheduled_seconds)/3600.0 AS scheduled_hours,
        sum(d.available_seconds)/3600.0 AS available_hours,
        sum(d.scheduled_seconds-d.available_seconds)/3600.0 AS downtime_hours,
        sqrt(sum(d.sum_bet_squared * g.payout_multiplier_variance))/100.0 AS payout_sd_usd
 FROM royale_meters d JOIN royale_math g USING(config_id)
 WHERE d.active AND d.gaming_date BETWEEN DATE '2025-01-01' AND DATE '2025-06-30'
 GROUP BY d.machine_id
)
SELECT a.*, m.manufacturer, m.theme, m.install_date, m.retire_date,
       (m.install_date <= DATE '2025-06-30' AND
        (m.retire_date IS NULL OR m.retire_date > DATE '2025-06-30')) AS on_floor_at_period_end,
       actual_usd / active_days AS actual_per_active_day,
       expected_usd / active_days AS expected_per_active_day,
       actual_usd - expected_usd AS payout_deviation_usd,
       available_hours / nullif(scheduled_hours,0) AS availability,
       expected_usd / nullif(available_hours,0) AS expected_per_available_hour,
       (actual_usd-expected_usd) / nullif(payout_sd_usd,0) AS standardized_payout_deviation,
       downtime_hours * expected_usd / nullif(available_hours,0) AS historical_downtime_theo_proxy_usd
FROM a JOIN royale_machines m USING(machine_id)
''')

pdf = diagnostics.toPandas()
numeric = ['actual_usd','expected_usd','wagers_usd','scheduled_hours','available_hours',
           'downtime_hours','payout_sd_usd','actual_per_active_day','expected_per_active_day',
           'payout_deviation_usd','availability','expected_per_available_hour',
           'standardized_payout_deviation','historical_downtime_theo_proxy_usd']
for col in numeric:
    pdf[col] = pd.to_numeric(pdf[col])
pdf = pdf.sort_values(['actual_usd','machine_id']).reset_index(drop=True)
bottom = pdf.head(10).copy()
diagnostics.write.mode('overwrite').saveAsTable('workspace.default.dashboard_royale_machine_diagnostics')
print(f'Checks passed. {len(pdf)} machines; prepared and raw earnings agree: ${float(prepared_total):,.2f}.')


# COMMAND ----------

dbutils.widgets.dropdown('machine', 'M-1158', bottom.machine_id.tolist(), '1. Machine to investigate')
dbutils.widgets.dropdown('downtime_recovery_pct', '50', ['0','25','50','75','100'], '2. Downtime recovered (%) — assumption')
dbutils.widgets.dropdown('retained_incremental_play_pct', '50', ['0','25','50','75','100'], '3. Additional floor play retained (%) — assumption')
selected = dbutils.widgets.get('machine')
recovery = float(dbutils.widgets.get('downtime_recovery_pct')) / 100
retention = float(dbutils.widgets.get('retained_incremental_play_pct')) / 100


# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Is low earnings mainly a payout gap or unavailable time?
# MAGIC The left panel compares actual and expected earnings for the same observed wagers. The right panel shows measured downtime, including faults, repairs, moves and installation downtime. A retired machine is not a July replacement target.

# COMMAND ----------

BG, FG, GOLD, MUTED, CYAN = '#11151B', '#F5F3ED', '#D4AF37', '#A9AFB8', '#55C4D1'
plt.rcParams.update({'font.size': 11, 'font.family':'DejaVu Sans'})
fig, axes = plt.subplots(1,2,figsize=(16,8), gridspec_kw={'width_ratios':[1.7,1]}, facecolor=BG)
fig.subplots_adjust(left=.11, right=.95, top=.77, bottom=.18, wspace=.26)
y=np.arange(len(bottom))
labels=[f"{r.machine_id}{' *' if not r.on_floor_at_period_end else ''}" for r in bottom.itertuples()]
axes[0].barh(y-.17, bottom.actual_usd, height=.30, color=GOLD, label='Actual earnings')
axes[0].barh(y+.17, bottom.expected_usd, height=.30, color=CYAN, label='Expected earnings (theo)')
axes[0].set_yticks(y,labels)
axes[0].xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'${x/1000:,.0f}k'))
axes[0].set_xlabel('Earnings before costs (USD)',color=MUTED)
axes[0].legend(facecolor=BG, edgecolor='none', labelcolor=FG, loc='lower right')
axes[0].set_title('ACTUAL VS EXPECTED',color=GOLD,loc='left',pad=16)
axes[1].barh(y,bottom.downtime_hours,height=.58,color=GOLD)
axes[1].set_yticks(y,['']*10)
axes[1].set_xlim(0,max(bottom.downtime_hours)*1.25)
for i,v in enumerate(bottom.downtime_hours):
    axes[1].text(v+.35,i,f'{v:.1f} h',color=FG,va='center')
axes[1].set_xlabel('Scheduled hours unavailable',color=MUTED)
axes[1].set_title('MEASURED DOWNTIME',color=GOLD,loc='left',pad=16)
for ax in axes:
    ax.set_facecolor(BG); ax.invert_yaxis(); ax.set_axisbelow(True)
    ax.grid(axis='x',color='#313740',linewidth=.6)
    ax.tick_params(colors=FG,length=0)
    for spine in ax.spines.values(): spine.set_visible(False)
fig.text(.06,.93,'THE GILDED ACE / LUCK & DOWNTIME LAB',color=GOLD,weight='bold',fontsize=11)
fig.text(.06,.86,'Low earnings can have different explanations',color=FG,weight='bold',fontsize=25)
fig.text(.06,.075,'* Retired before period end. Expected earnings do not adjust for location or demand; a payout gap is not proof of malfunction.',color=MUTED,fontsize=10)
fig.text(.06,.035,'Jan–Jun 2025 · Original bottom 10 by total earnings · Synthetic challenge data · Databricks computation',color=MUTED,fontsize=9)
fig.savefig(EXPORT/'luck_vs_downtime.png',dpi=200,facecolor=BG)
display(fig)
plt.close(fig)


# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Interactive “repair first?” scenario
# MAGIC **Historical counterfactual, not a July forecast:** downtime hours × observed theo per available hour × recovery fraction × retained additional play fraction.
# MAGIC
# MAGIC This assumes unavailable hours would have had the same play intensity as available hours. It may overstate or understate missed demand. Guests may have switched machines; the retention control reduces that assumed floor-wide benefit. Zero is a valid scenario. Costs have not been deducted, so this is not profit or ROI.

# COMMAND ----------

row = bottom[bottom.machine_id==selected].iloc[0]
scenario = row.historical_downtime_theo_proxy_usd * recovery * retention
cards = [
    ('Actual earnings',f'${row.actual_usd:,.2f}'),
    ('Expected earnings',f'${row.expected_usd:,.2f}'),
    ('Actual minus expected',f'${row.payout_deviation_usd:,.2f}'),
    ('Downtime / availability',f'{row.downtime_hours:.2f} h / {row.availability:.2%}'),
    ('Historical recovery scenario',f'${scenario:,.2f} before costs'),
]
card_html=''.join(f'<div style="flex:1;min-width:170px;padding:18px;background:#1d232c;border-top:3px solid {GOLD}"><div style="font-size:12px;color:{MUTED}">{html.escape(k)}</div><div style="font-size:22px;margin-top:10px">{html.escape(v)}</div></div>' for k,v in cards)
state='On floor at June 30' if row.on_floor_at_period_end else 'Retired — exclude from July replacement candidates'
displayHTML(f'<div style="background:{BG};color:{FG};padding:26px;font-family:Arial"><h2 style="color:{GOLD}">{selected}: investigate before replacing</h2><p>{state}. Active {int(row.active_days)} days.</p><div style="display:flex;gap:12px;flex-wrap:wrap">{card_html}</div><p style="color:{MUTED}">Scenario: recover {recovery:.0%} of downtime; retain {retention:.0%} as additional floor play. This is an assumption-driven historical estimate.</p></div>')

display(bottom[['machine_id','active_days','on_floor_at_period_end','actual_usd','expected_usd',
                'payout_deviation_usd','downtime_hours','availability','expected_per_available_hour',
                'historical_downtime_theo_proxy_usd','standardized_payout_deviation']])


# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Test the alternative explanation
# MAGIC A large payout gap can reflect random variation, configuration problems or meter/reporting issues. For context we calculate a standardized deviation using the supplied per-spin payout variance and sum of squared bets:
# MAGIC
# MAGIC `standard deviation = sqrt(sum(payout variance × squared bets)) / 100`
# MAGIC
# MAGIC This assumes independent spins and correct game settings. The result is a screening signal, **not a calibrated probability or proof of wrongdoing**. We selected these machines for low earnings, so negative deviations are expected in this group. We should inspect time patterns and comparable machines before recommending replacement or inspection.

# COMMAND ----------

timeline = (daily.filter((F.col('machine_id')==selected)&F.col('active'))
            .select('gaming_date','house_win_usd','theo_usd').orderBy('gaming_date').toPandas())
timeline['gaming_date']=pd.to_datetime(timeline['gaming_date'])
for c in ['house_win_usd','theo_usd']: timeline[c]=pd.to_numeric(timeline[c])
fig,ax=plt.subplots(figsize=(14,5),facecolor=BG)
ax.set_facecolor(BG)
ax.plot(timeline.gaming_date,timeline.house_win_usd.cumsum(),color=GOLD,label='Cumulative actual')
ax.plot(timeline.gaming_date,timeline.theo_usd.cumsum(),color=CYAN,label='Cumulative expected')
ax.set_title(f'{selected}: how the payout gap developed',color=FG,loc='left',pad=15)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'${x/1000:,.0f}k'))
ax.tick_params(colors=FG); ax.grid(color='#313740',linewidth=.5)
ax.legend(facecolor=BG,labelcolor=FG,edgecolor='none')
for spine in ax.spines.values(): spine.set_visible(False)
fig.tight_layout()
fig.savefig(EXPORT/f'{selected}_cumulative_earnings.png',dpi=200,facecolor=BG)
display(fig); plt.close(fig)
display(operations.filter(F.col('machine_id')==selected).orderBy('opened_at_utc'))


# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. A creative solution: triage before replacement
# MAGIC Use an evidence-driven decision board:
# MAGIC - **Payout review:** actual earnings far below expectation with little downtime → inspect settings and payout history before replacing.
# MAGIC - **Repair opportunity:** substantial downtime and healthy expected earnings per available hour → evaluate maintenance and recoverable demand.
# MAGIC - **Demand/location review:** low expected earnings per available hour despite good availability → compare similar games and locations.
# MAGIC - **Lifecycle check:** retired machines cannot be replaced again; new machines require fair exposure comparisons.
# MAGIC
# MAGIC These are investigation routes, not automatic spending recommendations. Costs and effects must be validated against the action catalogue before allocating the $100,000.
# MAGIC
# MAGIC **Useful contrast:** the original bottom ten may not contain the largest repair opportunities. The next table searches the whole floor for downtime among machines still present at period end.

# COMMAND ----------

display(pdf[pdf.on_floor_at_period_end].sort_values('downtime_hours',ascending=False).head(10)[
    ['machine_id','actual_usd','expected_usd','downtime_hours','availability','historical_downtime_theo_proxy_usd']])
summary = {'rows_checked':daily.count(),'machines':len(pdf),'selected_machine':selected,
           'recovery_assumption':recovery,'retained_play_assumption':retention,
           'selected_historical_recovered_theo_usd':float(scenario),
           'bottom10':json.loads(bottom.to_json(orient='records',date_format='iso')),
           'largest_downtime':json.loads(pdf[pdf.on_floor_at_period_end].sort_values('downtime_hours',ascending=False).head(10).to_json(orient='records',date_format='iso'))}
(EXPORT/'luck_downtime_results.json').write_text(json.dumps(summary,indent=2))
print(f'Analysis complete. Results saved to {EXPORT}.')


# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC # 6. Complete analysis: demand, players, comps and the decision lab
# MAGIC
# MAGIC This reusable function validates source tables, estimates historical downtime opportunity, summarizes guests and loyalty, evaluates a time-split demand forecast, and searches a disclosed action shortlist using 1,000 shared scenarios. Source hashes and assumptions are exported for reproducibility.
# MAGIC
# MAGIC **Important limits:** event/location comparisons are associations; missed machine play need not be lost floor play; comp and intervention effects are assumptions. Information value is unpriced. The search is exhaustive only within this shortlist, not every possible catalogue quantity and target.
# MAGIC
# MAGIC Saved results below come from the successful [full Databricks run](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#job/1101185085183547/run/614558976320488). They are embedded so judges can read them without rerunning.

# COMMAND ----------

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




# COMMAND ----------

report = run('/Volumes/workspace/default/dashboard_royale_source', '/Volumes/workspace/default/dashboard_royale_source/app_exports', execution='Databricks')
print('Validated and exported:', report['validation'])


# COMMAND ----------

# MAGIC %md
# MAGIC ## Demand and downtime
# MAGIC Use per-day and per-available-hour demand to avoid month-length and exposure bias. Historical downtime opportunity is a sensitivity estimate, not proven lost floor revenue.

# COMMAND ----------

display(pd.DataFrame(report['monthly']))
display(pd.DataFrame(report['event_associations']))
print(json.dumps(report['downtime'],indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tracked guests
# MAGIC Player net means payouts less wagers. Concentration is calculated after aggregating every player across six months. Only tracked play is represented.

# COMMAND ----------

print(json.dumps(report['players'],indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Comp economics
# MAGIC Reconciled redemption economic costs with the property totals. Points per face-value dollar is an observed weighted ratio; the sharp May change does not by itself prove a causal effect on demand.

# COMMAND ----------

display(pd.DataFrame(report['loyalty']))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Forecast validation
# MAGIC Train January–April; hold out May–June. Select the better constant or weekday model, then refit for the July planning baseline. July outcomes are not available.

# COMMAND ----------

print(json.dumps({k:v for k,v in report['forecast'].items() if k!='test_rows'},indent=2))
display(pd.DataFrame(report['forecast']['test_rows']))

# COMMAND ----------

# MAGIC %md
# MAGIC ## The $100,000 decision
# MAGIC The selected objective is mean 30-day incremental contribution. All effects are explicit assumptions. Keep budget is a valid plan. Inspecting M-1158 buys information; no unsupported recovery benefit is credited.

# COMMAND ----------

display(pd.DataFrame(report['simulation']['candidates'])[['id','target','quantity','cost','lead_days','benefit_days','additional_theo_cost','expected_net','assumption']])
display(pd.DataFrame(report['simulation']['portfolios']).head(20))
print('Highest mean-benefit plan:',report['simulation']['recommended'])
print('Limitations:',*report['simulation']['limitations'],sep='\n- ')

# COMMAND ----------

# MAGIC %md
# MAGIC ## Measurement and next decisions
# MAGIC
# MAGIC - **Inspection:** verify M-1158 settings against game math and reconcile meters. Resolve discrepancies before assigning monetary benefits to a fix.
# MAGIC - **Moves/signage:** choose feasible destination/control locations before launch; compare change in expected earnings per available hour against matched controls and monitor total floor wagers for displacement.
# MAGIC - **Maintenance:** measure downtime hours, repeat faults and expected earnings per scheduled hour against comparable untreated machines.
# MAGIC - **Comp policy:** use the catalogue pilot when learning is the objective; randomize eligible participants, keep budgets explicit, track incremental contribution after economic comp cost and guest retention. Do not combine a pilot with the floor-wide change.
# MAGIC - **Decision gates:** preregister measures, targets and a minimum detectable effect; check operational feasibility before committing funds. A longer horizon or a value for learning could change the 30-day ranking.
# MAGIC
# MAGIC The Streamlit app reads the exports from `dashboard_royale_source/app_exports`. Export this notebook and those files with the project's refresh script, then review and commit changes in GitHub Desktop.

# COMMAND ----------

# MAGIC %md
# MAGIC # FINAL PRODUCT — revision 2a124ca
# MAGIC Everything above is retained historical analysis. The following cells reproduce the final product from a versioned source archive. Saved charts, tables and printed results come from the successful cloud run linked below.

# COMMAND ----------

# MAGIC %md
# MAGIC # The Gilded Ace — final product evidence
# MAGIC **Final dashboard revision:** `2a124ca0b901ab9e4c18d87f471679c0673600a1`. All casino and guest data is synthetic. Historical evidence: January–June 2025. Modeled horizon: July 1–30, 2025.
# MAGIC
# MAGIC This notebook uses the exact archived source/data snapshot of the final dashboard, including the shared forecast and floor-simulation modules. It reruns checks and presents the main evidence and planning results in Databricks. The interactive Streamlit/SVG application remains a separately launched local application; this is not a hosted floor app.
# MAGIC
# MAGIC Read the final section of this notebook for version boundaries, assumptions, source documentation and the Devpost description. The original notebook's property forecast and version-1 simulation are retained as historical evidence, not substituted for this model.
# MAGIC **Verified in Databricks:** [successful run](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#job/796646835901211/run/1115290540544965). Saved outputs below are copied from that cloud run.

# COMMAND ----------

from pathlib import Path
import sys, json, hashlib, tempfile, zipfile, io, unittest, runpy
import numpy as np
import pandas as pd
VOLUME = Path('/Volumes/workspace/default/dashboard_royale_source/final_product/2a124ca')
ARCHIVE = VOLUME / 'aceiq_final_product.zip'
EXPECTED_SHA256 = 'f8b6e0d01983c1e6a249a0cc2d4c03e9f1a8ca3e3afe0a41de14d101d7d72e99'
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == EXPECTED_SHA256, 'Source archive mismatch'
FINAL_ROOT = Path(tempfile.mkdtemp(prefix='aceiq-final-'))
with zipfile.ZipFile(ARCHIVE) as archive:
    for member in archive.infolist():
        target=(FINAL_ROOT/member.filename).resolve()
        assert target.is_relative_to(FINAL_ROOT.resolve()), 'Unsafe archive path'
    archive.extractall(FINAL_ROOT)
source_manifest=json.loads((FINAL_ROOT/'SOURCE_MANIFEST.json').read_text())
for filename,expected_hash in source_manifest['files'].items():
    assert hashlib.sha256((FINAL_ROOT/filename).read_bytes()).hexdigest()==expected_hash, filename
sys.path.insert(0,str(FINAL_ROOT))
# Remove any earlier imported project version from this Python session.
for module_name in list(sys.modules):
    if module_name=='dashboard' or module_name.startswith('dashboard.'):
        del sys.modules[module_name]
from dashboard.data_bundle import load_bundle
from dashboard.analytics import machine_summary
from dashboard.forecast import build_forecasts, aggregate_predictions
from dashboard.decisions import rank_portfolios
from dashboard.floor_simulation import FloorSimulation
final_bundle=load_bundle()
fd=final_bundle['daily']; fm=final_bundle['machines']; fp=final_bundle['property']
fr=final_bundle['report']; fg=final_bundle['guests']; predictions=final_bundle['predictions']
summary=machine_summary(fd,fm)
VERIFY=VOLUME/'verification'
VERIFY.mkdir(exist_ok=True)
print('Verified source commit:',source_manifest['git_commit'])
print('SHA-256 checked files:',len(source_manifest['files']))
print('Only versioned verification outputs are written; source tables and historical exports are unchanged.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Reconcile the final product with the cloud table
# MAGIC The snapshot contains 55,092 active machine-days; the original prepared table also contains inactive rows. Comparisons below use active rows consistently. Earnings are before operating costs. Player net is payouts minus wagers.

# COMMAND ----------

cloud = spark.sql("""SELECT count(*) AS active_rows,
    sum(coin_in_usd) AS wagers, sum(payout_usd) AS payouts,
    sum(house_win_usd) AS actual, sum(theo_usd) AS expected
    FROM workspace.default.prepared_daily_view WHERE active = true""").first().asDict()
local={'active_rows':len(fd),'wagers':float(fd.coin_in_usd.sum()),
       'payouts':float((fd.coin_in_usd-fd.house_win_usd).sum()),
       'actual':float(fd.house_win_usd.sum()),'expected':float(fd.theo_usd.sum())}
for key,value in local.items():
    np.testing.assert_allclose(float(cloud[key]),value,rtol=0,atol=.01)
display(pd.DataFrame([{'Measure':k,'Cloud active rows':float(cloud[k]),'Final local exports':v} for k,v in local.items()]))
print('PASS: final dashboard exports reconcile with the Databricks prepared table.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Focused regression checks
# MAGIC These are the same financial, source-reference, leakage, placement and floor-engine checks used locally. Browser/UI and localhost HTTP tests remain local; they are not claimed as Databricks tests.

# COMMAND ----------

test_log=io.StringIO()
suite=unittest.TestSuite()
loader=unittest.TestLoader()
for name in ['test_results.py','test_reference_consistency.py','test_floor_simulation.py']:
    suite.addTests(loader.discover(str(FINAL_ROOT/'tests'),pattern=name))
test_result=unittest.TextTestRunner(stream=test_log,verbosity=1).run(suite)
print(test_log.getvalue())
assert test_result.wasSuccessful(), 'Regression check failed'
runpy.run_path(str(FINAL_ROOT/'tests/test_upgrade.py'))
print('PASS: independent money/variance/forecast reconciliation, floor validation, atomic swaps, suggestions and leakage checks.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Chart conventions
# MAGIC Charts below use the final data definitions. They are static evidence charts in a notebook, not copies of the browser controls. The original pixel font is used for headings; axes remain readable monospace. Downloaded chart PNGs are written only to this revision's verification folder.

# COMMAND ----------

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
font_manager.fontManager.addfont(str(FINAL_ROOT/'assets/fonts/Silkscreen-Regular.ttf'))
plt.rcParams.update({'figure.facecolor':'#0b231f','axes.facecolor':'#0b231f',
    'text.color':'#f6eacb','axes.labelcolor':'#f6eacb','xtick.color':'#f6eacb','ytick.color':'#f6eacb',
    'axes.edgecolor':'#426457','font.family':'monospace','font.size':11,'figure.dpi':120,
    'axes.spines.top':False,'axes.spines.right':False})
GOLD='#e4bd75';TEAL='#75c9b9';ROSE='#d2919e'
chart_files=[]
def figure(title,size=(12,4.8)):
    fig,ax=plt.subplots(figsize=size)
    ax.set_title(title,fontfamily='Silkscreen',fontsize=13,pad=20)
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    return fig,ax
def finish(fig,name):
    fig.tight_layout()
    buffer=io.BytesIO();fig.savefig(buffer,format='png',bbox_inches='tight')
    (VERIFY/name).write_bytes(buffer.getvalue());chart_files.append(name)
    display(fig);plt.close(fig)
def dollars(ax,axis='y'):
    formatter=ticker.FuncFormatter(lambda v,p: f'${v/1e6:.1f}m' if abs(v)>=1e6 else f'${v/1000:.0f}k' if abs(v)>=1000 else f'${v:.0f}')
    (ax.yaxis if axis=='y' else ax.xaxis).set_major_formatter(formatter)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Which machines deserve investigation?
# MAGIC Raw low earnings mix exposure, availability, demand and payout variation. The index is actual house win divided by expected earnings; 100% means actual equals expected. Negative values are kept. Change `rank_by` below to mirror the dashboard's three ranking choices.

# COMMAND ----------

rank_by='actual_house_win' # alternatives: actual_per_active_day, expected_per_available_hour
bottom=summary.sort_values([rank_by,'machine_id']).head(10).copy()
bottom['actual_index']=100*bottom.actual_house_win/bottom.expected_house_win.replace(0,np.nan)
bottom=bottom.sort_values('actual_index')
fig,ax=figure('Bottom-ten candidates: actual / expected',size=(12,5.5))
ax.barh(bottom.machine_id,bottom.actual_index,color=GOLD);ax.axvline(100,color=TEAL,ls='--',label='Expected = 100%')
ax.set_xlabel('Actual / expected (%)');ax.legend();finish(fig,'01_bottom_ten.png')
display(bottom[['machine_id','actual_house_win','expected_house_win','active_days','availability_rate','standardized_gap']])
weak=bottom.iloc[0]
print(f'Takeaway: {weak.machine_id} realized {weak.actual_index:.1f}% of expected earnings over {int(weak.active_days)} active days. This is a screen, not a defect diagnosis.')
fig,ax=figure('Payout variation: residual screen')
points=ax.scatter(summary.expected_house_win,summary.actual_minus_expected,c=summary.standardized_gap,cmap='PiYG',vmin=-5,vmax=5,s=25)
fig.colorbar(points,ax=ax,label='Gap / modeled standard deviation');ax.axhline(0,color=GOLD,ls='--')
ax.set_xlabel('Expected earnings');ax.set_ylabel('Actual minus expected');dollars(ax);dollars(ax,'x');finish(fig,'02_residuals.png')
print('Guardrail: modeled payout variance and multiple-machine screening matter. This is not a multiple-testing-adjusted significance test.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Machine investigation and monthly availability
# MAGIC Select a machine below. Variance is summed for the selected evidence period, avoiding reuse of an unrelated full-period payout score. Monthly downtime is measured in hours, not a percentage.

# COMMAND ----------

machine_id='M-1158'
evidence_start=pd.Timestamp('2025-01-01'); evidence_end=pd.Timestamp('2025-06-30')
chosen=fd[(fd.machine_id==machine_id)&fd.gaming_date.between(evidence_start,evidence_end)].sort_values('gaming_date')
row=machine_summary(chosen,fm).iloc[0]
fig,ax=figure(machine_id+': actual versus expected')
ax.plot(chosen.gaming_date,chosen.house_win_usd.cumsum(),color=GOLD,label='Actual')
ax.plot(chosen.gaming_date,chosen.theo_usd.cumsum(),color=TEAL,label='Expected');ax.legend();dollars(ax);finish(fig,'03_machine_cumulative.png')
print(f'Takeaway: gap ${row.actual_minus_expected:,.2f}; modeled residual {row.standardized_gap:.2f} SD; availability {row.availability_rate:.2%}. Check configuration/meters before irreversible action.')
monthly=chosen.groupby('month',as_index=False).agg(down=('down_hours','sum'),available=('available_hours','sum'),scheduled=('scheduled_hours','sum'))
monthly['availability']=monthly.available/monthly.scheduled
fig,ax=figure(machine_id+': monthly unavailable hours');ax.bar(monthly.month,monthly.down,color=ROSE);ax.set_ylabel('Hours');finish(fig,'04_monthly_downtime.png');display(monthly)
peers=summary[summary.theme==row.theme]
fig,ax=figure(machine_id+': same-theme context');ax.scatter(peers.expected_per_available_hour,peers.availability_rate,color=TEAL)
ax.scatter([row.expected_per_available_hour],[row.availability_rate],s=180,facecolors='none',edgecolors=GOLD,linewidths=2)
ax.set_xlabel('Expected earnings / available hour');ax.set_ylabel('Availability');ax.yaxis.set_major_formatter(ticker.PercentFormatter(1));dollars(ax,'x');finish(fig,'05_theme_peers.png')
display(final_bundle['placements'][final_bundle['placements'].machine_id==machine_id])
print('Peers and placement histories are descriptive: they do not fully control denomination, guest mix or location effects.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Demand, events, traffic and downtime opportunity
# MAGIC Normalize demand by available machine-hours to distinguish play intensity from month length and exposure. Event comparisons and traffic summaries are fixed January–June context. Missing counter coverage is not zero traffic.

# COMMAND ----------

months=fd.groupby('month',as_index=False).agg(wagers=('coin_in_usd','sum'),hours=('available_hours','sum'))
months['wagers_per_hour']=months.wagers/months.hours
fig,ax=figure('Demand per available machine-hour');ax.plot(months.month,months.wagers_per_hour,'o-',color=TEAL);dollars(ax);ax.set_ylabel('Wagers / available hour');finish(fig,'06_demand_rate.png')
peak=months.loc[months.wagers_per_hour.idxmax()];last=months.iloc[-1]
print(f'Takeaway: demand peaked in {peak.month} at ${peak.wagers_per_hour:.2f}/hour; {last.month} was ${last.wagers_per_hour:.2f}/hour, {(last.wagers_per_hour/peak.wagers_per_hour-1):.1%} from peak.')
events=pd.DataFrame(fr['event_associations']).sort_values('difference_pct')
fig,ax=figure('Event associations vs weekday baseline',size=(14,6));ax.barh(events.event,events.difference_pct*100,color=GOLD);ax.set_xlabel('Difference (%)');finish(fig,'07_event_context.png')
traffic=pd.DataFrame(fr['traffic'])
fig,ax=figure('Traffic: entries per covered hour')
for zone,group in traffic.groupby('zone_id'):ax.plot(group.month,group.entries_per_covered_hour,'o-',label=zone)
ax.legend(ncol=4,fontsize=9);ax.set_ylabel('Entries / covered hour');finish(fig,'08_traffic.png')
print(f'Counter entries are not unique people. Minimum valid interval share: {traffic.valid_interval_share.min():.1%}. Events are associations, not causal estimates.')
zone_loss=fd.groupby('zone_name',as_index=False).agg(opportunity=('missed_theo_mid','sum'),hours=('down_hours','sum')).sort_values('opportunity')
fig,ax=figure('Downtime opportunity by zone');ax.barh(zone_loss.zone_name,zone_loss.opportunity,color=ROSE);dollars(ax,'x');ax.set_xlabel('Expected-earnings opportunity');finish(fig,'09_downtime_zone.png')
print(f'Takeaway: {fd.down_hours.sum():,.1f} unavailable hours and ${fd.missed_theo_mid.sum():,.2f} estimated expected-earnings opportunity. Displaced play may be retained elsewhere; this is not proven net floor loss.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Tracked guests and loyalty economics
# MAGIC Grouped guest exports contain player-months, not distinct guest counts. Six-month concentration is a separately computed fixed-cohort statistic. Guest net is payouts minus wagers. Economic comp cost differs from face value and is included in linked POS COGS: do not subtract both twice.

# COMMAND ----------

display(fg.groupby('period_month',as_index=False)[['wagers','payouts','player_net','expected','comp_cost','player_months']].sum())
cohort=fg.groupby('age_band',as_index=False).wagers.sum().sort_values('wagers')
fig,ax=figure('Tracked wagers by age group');ax.barh(cohort.age_band,cohort.wagers,color=GOLD);dollars(ax,'x');finish(fig,'10_guest_groups.png')
print(f'Tracked wagers ${fg.wagers.sum():,.2f}; payouts ${fg.payouts.sum():,.2f}; player net ${fg.player_net.sum():,.2f}. Carded play is only part of all play.')
display(pd.DataFrame([fr['players']]))
loyalty=pd.DataFrame(fr['loyalty']);x=np.arange(len(loyalty))
fig,ax=figure('Comp economic cost vs face value');ax.bar(x-.18,loyalty.cost_cents/100,width=.36,color=GOLD,label='Economic cost');ax.bar(x+.18,loyalty.face_cents/100,width=.36,color=TEAL,label='Face value');ax.set_xticks(x,loyalty.gaming_month);ax.legend();dollars(ax);finish(fig,'11_comp_economics.png')
fig,ax=figure('Observed redemption conversion');ax.plot(loyalty.gaming_month,loyalty.points_per_face_dollar,'o-',color=GOLD);ax.set_ylabel('Points / face-value dollar');finish(fig,'12_redemption_conversion.png')
comp=fp.groupby('month',as_index=False).agg(cost=('comp_cost_usd','sum'),theo=('theo_usd','sum'));comp['cost_per_theo']=comp.cost/comp.theo
fig,ax=figure('Comp cost / expected gaming earnings');ax.plot(comp.month,comp.cost_per_theo,'o-',color=TEAL);ax.yaxis.set_major_formatter(ticker.PercentFormatter(1));finish(fig,'13_comp_ratio.png')
print(f'Takeaway: comp economic cost ${loyalty.cost_cents.sum()/100:,.2f}; points per face dollar changed from {loyalty.points_per_face_dollar.iloc[0]:.2f} to {loyalty.points_per_face_dollar.iloc[-1]:.2f}. This does not prove a uniform policy change or causal demand effect.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Final forecast: reproduce it, then compare with the archived output
# MAGIC Fit January–March; select constant/weekday using April; refit January–April and freeze the May–June test. Refit January–June only for July. The archived **machine-day MAE improvement is about 16.6%**. The original notebook's **68.5% property-level comparison** is a different historical model and must not be substituted here.

# COMMAND ----------

rebuilt_predictions, rebuilt_metadata=build_forecasts(fd,fm)
keys=['phase','machine_id','gaming_date']
left=rebuilt_predictions.sort_values(keys).reset_index(drop=True)
right=predictions.sort_values(keys).reset_index(drop=True)
assert left[keys].equals(right[keys])
np.testing.assert_allclose(left.prediction,right.prediction,rtol=1e-10,atol=1e-6)
meta=final_bundle['metadata']
np.testing.assert_allclose(rebuilt_metadata['holdout_mae'],meta['holdout_mae'])
holdout=aggregate_predictions(predictions[predictions.phase=='May–June holdout'],predictions[predictions.phase=='April calibration'])
fig,ax=figure('Frozen May–June holdout: demand')
for col,label,color,ls in [('coin_in_usd','Observed',GOLD,'-'),('prediction','Prediction',TEAL,'-'),('constant','Constant baseline',ROSE,'--')]:ax.plot(holdout.gaming_date,holdout[col],label=label,color=color,ls=ls)
ax.legend();dollars(ax);finish(fig,'14_forecast_holdout.png')
print(f"Machine-day MAE ${meta['holdout_mae']:,.2f} vs ${meta['baseline_mae']:,.2f}; reduction {1-meta['holdout_mae']/meta['baseline_mae']:.1%}.")
print('Chart lines aggregate machines; MAE above is per machine-day. July actuals are absent. Approximate calibration bands are not guarantees.')
display(pd.DataFrame([{'model':meta['model'],'holdout_mae':meta['holdout_mae'],'baseline_mae':meta['baseline_mae'],'wape':meta['holdout_wape']}]))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. The final shared simulation and $100,000 decision
# MAGIC The current dashboard/floor engine uses 1,000 seeded shared draws. Benefits are assumptions, not fitted causal effects. Cash, catalog lead times, recurring costs and planned downtime are explicit. The original nine-target shortlist and the floor's broader individual-action search are different search scopes.

# COMMAND ----------

engine=final_bundle['engine']
ranked=rank_portfolios(engine.shortlist(fr['simulation']['candidates'])).sort_values(['Expected net benefit','Cost'],ascending=[False,True])
display(ranked.head(20))
best=ranked.iloc[0]
print('Limited-shortlist recommendation:',best.Actions,'| Mean incremental net:',best['Expected net benefit'])
simulation=FloorSimulation(final_bundle)
empty=simulation.evaluate([])
suggested=simulation.suggestions([])
display(pd.json_normalize(suggested['suggestions']))
print('Search candidates:', suggested['searched'])
print('Suggestions search positive individually feasible moves, lease replacements and manufacturer maintenance against the current plan; not global layout optimization.')
print('Moves use the first legal vacancy. Destination-specific causal lift is unknown. Add/remove and swaps are outside the suggestion search.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Reproduce an atomic swap and July playback
# MAGIC This example is a demonstration, not a selected recommendation. It preserves machine IDs, supplied configurations and roster size. Both moves activate July 3; the swap uses two catalog move units and $3,600 cash. Preview is stateless, confirmation is bound to the plan/action, and undo restores both original positions.

# COMMAND ----------

targets=sorted(simulation.eligible)[:2]
swap={'id':'notebook-swap','kind':'swap','target':targets[0],'other':targets[1]}
preview=simulation.preview([],swap)
confirmed=simulation.confirm([],swap,preview['estimate_id'])
assert len(simulation.initial)==308
assert all(day['machine_count']==308 for day in confirmed['days'])
assert simulation.undo(confirmed['plan'],swap['id'])['summary']['layout']==simulation.initial
display(pd.DataFrame([{k:v for k,v in day.items() if k not in ['layout','activated']} for day in confirmed['days']]))
fig,ax=figure('Example swap: conditional July net distribution');ax.hist(confirmed['_net'],bins=35,color=GOLD);ax.axvline(0,color=TEAL,ls='--');ax.set_xlabel('Incremental net after action cash and downtime');dollars(ax,'x');finish(fig,'15_swap_distribution.png')
print('Example swap marginal result:',preview['marginal'])
print('Initial machines:',len(simulation.initial),'| Empty slots:',len(simulation.slots)-len(simulation.initial),'| Swap cash:',confirmed['cash_committed'])
print('Added machines use proxy performance × triangular(0.5,1,1.5) × entered incremental share; removals retain only the entered share elsewhere. No resale or operating savings are invented.')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Final interface and methods
# MAGIC The source archive includes the five-destination application, original pixel font, readable charts, concise takeaways, the optional Evidence Claw, final floor assets, README, Claims & Evidence, AI disclosure and 363-word Devpost draft.
# MAGIC
# MAGIC - **Overview:** earnings, normalized demand, ranking choices, residual/event/traffic/downtime evidence and the optional claw.
# MAGIC - **Machines:** actual/expected, monthly availability, same-theme peers and placement history.
# MAGIC - **Guests:** tracked outcomes, concentration, comp costs, redemption conversion and comp-cost ratios.
# MAGIC - **Scenarios:** constrained shortlist, shared uncertainty, frozen forecast evidence and measurement plan.
# MAGIC - **Floor lab:** separate interactive SVG app with drag/drop, atomic swap, previews, suggestions, July playback and undo.
# MAGIC
# MAGIC Walking guests are decorative. The claw only selects a raw-bottom-ten investigation candidate; it does not change a model or recommendation. The browser UI is launched locally with `python run_local.py`; Databricks does not host those two localhost services. No Gemini integration exists. Public hosting remains separate.
# MAGIC
# MAGIC For intervention evaluation: preregister target, dates, costs and controls; compare availability and contribution per scheduled hour with unchanged peers; monitor whole-floor play for displacement. Conditional planning estimates do not establish an action's real-world benefit.

# COMMAND ----------

from IPython.display import Image, Markdown, display as ipy_display
ipy_display(Image(filename=str(FINAL_ROOT/'docs/dashboard.png')))
ipy_display(Image(filename=str(FINAL_ROOT/'docs/floor-lab.png')))
ipy_display(Markdown((FINAL_ROOT/'docs/REFERENCE_COMPARISON.md').read_text(encoding='utf-8')))
ipy_display(Markdown((FINAL_ROOT/'docs/DEVPOST.md').read_text(encoding='utf-8')))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Verification record
# MAGIC The successful end of this cell establishes which source snapshot ran. It records cloud/local reconciliation, reproduced forecasts and engine regression checks. UI/HTTP/geometry checks were performed locally and are separately documented; this cell does not claim they ran on Databricks.

# COMMAND ----------

verification={'git_commit':source_manifest['git_commit'],'archive_sha256':EXPECTED_SHA256,
 'verified_source_files':len(source_manifest['files']),'cloud_table_reconciled':True,
 'cloud_totals':{k:float(v) for k,v in cloud.items()},'local_totals':local,
 'regression_tests':test_result.testsRun,'regressions_passed':test_result.wasSuccessful(),
 'leakage_and_placement_checks_passed':True,'forecast_reproduced':True,
 'machine_day_mae':meta['holdout_mae'],'baseline_mae':meta['baseline_mae'],
 'shortlist_recommendation':best.Actions,'shortlist_mean_net':float(best['Expected net benefit']),
 'initial_machines':len(simulation.initial),'vacancies':len(simulation.slots)-len(simulation.initial),
 'swap_cash':confirmed['cash_committed'],'swap_preserved_roster':True,'charts':chart_files,
 'verified_at_utc':pd.Timestamp.now(tz='UTC').isoformat()}
(VERIFY/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps(verification,indent=2))
print('FINAL PRODUCT VERIFICATION PASSED')
