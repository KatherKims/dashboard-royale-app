# Databricks notebook source
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
