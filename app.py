"""Compact local AceIQ dashboard. Source exports and shared models are unchanged."""
from pathlib import Path
import html
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dashboard.data_bundle import load_bundle
from dashboard.analytics import machine_summary, machine_category
from dashboard.forecast import aggregate_predictions
from dashboard.decisions import rank_portfolios

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='The Gilded Ace · ACEIQ',page_icon='♠',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>'+(ROOT/'assets/dashboard.css').read_text()+'</style>',unsafe_allow_html=True)

@st.cache_resource
def bundle(): return load_bundle()
b=bundle();report=b['report'];daily=b['daily'];prop=b['property'];machines=b['machines']
money=lambda v: f'-${abs(v):,.0f}' if v<0 else f'${v:,.0f}'
pages=['Overview','Machines','Guests','Scenarios','Floor lab']
page=st.query_params.get('page','Overview')
if page not in pages:page='Overview'

st.markdown('<div class="brandline"><div><span class="suit">♠</span> THE GILDED ACE <small>ACEIQ / DECISION INTELLIGENCE</small></div><span class="synthetic">LOCAL · SYNTHETIC DATA</span></div>',unsafe_allow_html=True)
nav=''.join(f'<a class="{"active" if p==page else ""}" href="'+('http://127.0.0.1:8502/floor-lab' if p=='Floor lab' else '?page='+p)+f'" target="_self">{p}{" ↗" if p=="Floor lab" else ""}</a>' for p in pages)
st.markdown('<nav aria-label="Dashboard destinations">'+nav+'</nav>',unsafe_allow_html=True)
if page=='Floor lab':
    st.link_button('Open the full-window floor lab ↗','http://127.0.0.1:8502/floor-lab',type='primary')
    st.caption('Run python run_local.py to start both local services. The floor opens separately from Streamlit.')
    st.stop()

f1,f2,f3=st.columns([1.6,1.2,2.2])
dates=f1.date_input('Historical evidence period',(pd.Timestamp('2025-01-01').date(),pd.Timestamp('2025-06-30').date()),min_value=pd.Timestamp('2025-01-01').date(),max_value=pd.Timestamp('2025-06-30').date(),key='evidence_dates')
if not isinstance(dates,(list,tuple)) or len(dates)!=2:
    st.info('Choose the end date to complete your evidence period.');st.stop()
start,end=map(pd.Timestamp,dates)
selected=daily[daily.gaming_date.between(start,end)]
period_prop=prop[prop.gaming_date.between(start,end)]
if selected.empty:st.info('No historical evidence in this period.');st.stop()
scope=f2.selectbox('Evidence scope',['Whole floor']+sorted(daily.zone_name.unique()),key='zone_scope',disabled=page in ['Guests','Scenarios'])
if page not in ['Guests','Scenarios'] and scope!='Whole floor':selected=selected[selected.zone_name==scope]
with f3:
    st.caption({'Overview':'Read the floor. Question the odds.','Machines':'Separate demand, downtime and payout variation.','Guests':'Tracked play is a partial view of all visitors.','Scenarios':'Choose a test, not a guaranteed return.'}[page])
summary=machine_summary(selected,machines)
summary['screen']=summary.apply(machine_category,axis=1)

def metrics(items):
    for col,(label,value) in zip(st.columns(4),items):
        with col.container(border=True):st.metric(label,value)

def chart(fig,key,height=190):
    fig.update_layout(height=height,margin=dict(l=8,r=8,t=10,b=24),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#e8dfc5',size=10),legend=dict(orientation='h',y=1.15,font=dict(size=9)),hovermode='closest')
    fig.update_xaxes(gridcolor='#294c43',zeroline=False);fig.update_yaxes(gridcolor='#294c43',zeroline=False)
    st.plotly_chart(fig,width='stretch',key=key,config={'displayModeBar':False,'displaylogo':False})

def csv(frame,name): st.download_button('Download evidence CSV',frame.to_csv(index=False),name,'text/csv',key='download_'+name)

@st.dialog('Methods & evidence',width='large')
def evidence():
    st.markdown('**Synthetic history:** January–June 2025. **Planning:** July 1–30, 2025. Theo is expected house win before operating costs, not net business profit.')
    st.markdown('Exposure uses active machine-days. Availability = available / scheduled hours. Payout scores use the variance for the selected period. Low raw totals are not replacement proof. Downtime opportunity uses same-machine/weekday rate quantiles; it is not measured net floor loss.')
    st.write(b['metadata'])
    st.markdown('The new floor and Scenarios reuse `dashboard/decisions.py`: 1,000 seeded draws, conditional assumed effects, July forecast baselines. Original `analysis_results.json` simulation results remain historical and are not mixed into the new ranking.')
    st.dataframe(pd.DataFrame([{'Check':'Historical active rows','Result':len(daily)},{'Check':'Duplicate machine/day','Result':int(daily.duplicated(['machine_id','gaming_date']).sum())}]),hide_index=True)
    st.markdown('No live Databricks connection or Gemini chat. Databricks notebooks preserve original analysis; this UI reads local exports.')
    for filename in ['CLAIMS_AND_EVIDENCE.md','AI_DISCLOSURE.md']:
        path=ROOT/'docs'/filename
        if path.exists():st.download_button('Download '+filename,path.read_bytes(),filename,'text/markdown')
    with st.expander('Original saved simulation · version 1'):
        st.json({k:report['simulation'][k] for k in ['seed','scenarios','candidate_count','feasible_portfolios','recommended','limitations']})

if page=='Overview':
    metrics([('Actual house win',money(selected.house_win_usd.sum())),('Expected house win',money(selected.theo_usd.sum())),('Availability',f'{selected.available_hours.sum()/selected.scheduled_hours.sum():.2%}'),('Downtime opportunity',money(selected.missed_theo_mid.sum()))])
    left,right=st.columns([1.4,1])
    with left.container(height=255,border=True):
        st.subheader('Play observed / forecast')
        history=selected.groupby('gaming_date',as_index=False).coin_in_usd.sum()
        future=b['predictions'];future=future[(future.phase=='July forecast') & future.machine_id.isin(summary.machine_id)]
        forecast=future.groupby('gaming_date',as_index=False).prediction.sum()
        fig=go.Figure();fig.add_scatter(x=history.gaming_date,y=history.coin_in_usd,name='Observed wagers',line_color='#e4bd75')
        fig.add_scatter(x=forecast.gaming_date,y=forecast.prediction,name='July forecast · no actuals',line=dict(color='#70cabe',dash='dot'));chart(fig,'overview_demand',165)
        st.caption('Source: machine_daily + demand_predictions. Fixed July forecast; not July actuals.')
        with st.expander('Demand context · events and zone traffic'):
            st.dataframe(pd.DataFrame(report['event_associations']),hide_index=True)
            st.write(report['traffic'])
            st.caption('Fixed six-month context from the original analysis. Counters have partial coverage; event associations are not causal effects.')
    with right.container(height=255,border=True):
        st.subheader('The floor · July 1 placement')
        slots=b['slots'].merge(machines[['machine_id','theme','theo_per_hour']],on='machine_id',how='left')
        if scope!='Whole floor':
            ids=set(selected.machine_id);slots=slots[slots.machine_id.isin(ids)]
        fig=px.scatter(slots,x='x_m',y='y_m',color='theo_per_hour',hover_name='machine_id',hover_data=['theme','location_id'],color_continuous_scale=['#31554f','#75c9b9','#e4bd75'])
        fig.update_traces(marker=dict(symbol='square',size=5));fig.update_layout(coloraxis_showscale=False);fig.update_yaxes(scaleanchor='x');chart(fig,'overview_floor',165)
        st.link_button('Enter interactive floor lab ↗','http://127.0.0.1:8502/floor-lab')
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Machines to investigate')
        columns=['machine_id','actual_house_win','expected_house_win','active_days','availability_rate','screen']
        display=summary.sort_values('actual_house_win').head(10)[columns].rename(columns={'machine_id':'Machine','actual_house_win':'Actual $','expected_house_win':'Expected $','active_days':'Active days','availability_rate':'Availability','screen':'Investigation lead'})
        st.dataframe(display,hide_index=True,height=153,width='stretch',column_config={'Availability':st.column_config.NumberColumn(format='percent'),'Actual $':st.column_config.NumberColumn(format='dollar'),'Expected $':st.column_config.NumberColumn(format='dollar')})
        st.caption('Selected-period screen, not a defect diagnosis. Short exposure and low demand differ from bad luck.')
    with right.container(height=245,border=True):
        st.subheader('Decision: evidence before replacement')
        st.markdown('**Do not automatically replace the raw bottom ten.** Inspect suspicious payout gaps; compare expected earnings per available hour and downtime first.')
        candidates=b['engine'].shortlist(report['simulation']['candidates']);ranked=rank_portfolios(candidates).sort_values('Expected net benefit',ascending=False)
        best=ranked.iloc[0]
        st.markdown(f'**Default shortlist recommendation:** {best.Actions}. Expected 30-day incremental net: **{money(best["Expected net benefit"])}**.')
        st.caption('Limited candidate search; effects are assumptions. Inspection may have unpriced information value.')
        if st.button('Methods & evidence',key='overview_evidence'):evidence()

elif page=='Machines':
    selector,bankcol=st.columns([2,1])
    latest=selected.sort_values('gaming_date').drop_duplicates('machine_id',keep='last')
    bank=bankcol.selectbox('Bank',['All banks']+sorted(latest.bank_id.dropna().unique()),key='machine_bank')
    ids=latest.machine_id if bank=='All banks' else latest.loc[latest.bank_id==bank,'machine_id']
    choices=summary[summary.machine_id.isin(ids)].sort_values('actual_house_win')
    if choices.empty:st.info('No machines in this selection.');st.stop()
    mid=selector.selectbox('Find a machine',choices.machine_id.tolist(),format_func=lambda m:m+' · '+machines.set_index('machine_id').loc[m,'theme'],key='machine_id')
    row=summary.set_index('machine_id').loc[mid];md=selected[selected.machine_id==mid].sort_values('gaming_date')
    metrics([('Actual / expected',f'{money(row.actual_house_win)} / {money(row.expected_house_win)}'),('Expected / available hour',money(row.expected_per_available_hour)),('Availability',f'{row.availability_rate:.2%}'),('Payout gap / SD',f'{row.standardized_gap:.2f}')])
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Cumulative actual versus expected')
        fig=go.Figure();fig.add_scatter(x=md.gaming_date,y=md.house_win_usd.cumsum(),name='Actual',line_color='#e4bd75');fig.add_scatter(x=md.gaming_date,y=md.theo_usd.cumsum(),name='Expected',line_color='#75c9b9');chart(fig,'machine_cumulative',175)
        st.caption('Meter house win and configured game math. Payout variation is not a causal defect test.')
    with right.container(height=245,border=True):
        st.subheader('Availability · monthly first')
        monthly=md.assign(month=md.gaming_date.dt.strftime('%Y-%m')).groupby('month',as_index=False).agg(down_hours=('down_hours','sum'),scheduled=('scheduled_hours','sum'),available=('available_hours','sum'))
        monthly['Availability %']=monthly.available/monthly.scheduled*100
        st.dataframe(monthly[['month','down_hours','Availability %']].rename(columns={'month':'Month','down_hours':'Unavailable hours'}),hide_index=True,height=155,width='stretch')
        with st.expander('Daily outages'):st.dataframe(md[['gaming_date','down_hours','missed_theo_mid']],hide_index=True)
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Demand versus theme peers')
        peers=summary[summary.theme==row.theme].sort_values('expected_per_available_hour')
        fig=px.scatter(peers,x='expected_per_available_hour',y='availability_rate',hover_name='machine_id',color='actual_minus_expected',color_continuous_scale=['#db8c91','#75c9b9','#e4bd75'])
        fig.add_scatter(x=[row.expected_per_available_hour],y=[row.availability_rate],mode='markers',name=mid,marker=dict(symbol='circle-open',size=15,color='#fff5c5'));fig.update_layout(coloraxis_showscale=False);chart(fig,'machine_peers',170)
        st.caption('Expected $/available hour versus availability. Peers do not fully control location or guest mix.')
    with right.container(height=245,border=True):
        st.subheader(row.screen)
        st.write(f'{int(row.active_days)} active days · {row.theme} · {row.manufacturer} · {row.lease_class}')
        st.caption('Check configuration and meters for unusual payout gaps. Investigate demand and location before assuming replacement will help. Recompute this screen when dates change.')
        with st.expander('Placement, action context & source evidence'):
            st.dataframe(b['placements'][b['placements'].machine_id==mid],hide_index=True)
            st.caption('Effective-dated placement history. Before/after changes can reflect timing and demand, not the move itself.')
            st.write('July eligible:',bool(row.eligible_july));csv(md,'machine-'+mid+'.csv')
            st.dataframe(pd.DataFrame([r for r in report['action_catalog'] if r['action_type_id'] in ['A-INSPECT','A-MOVE-MACHINE','A-REPLACE-LEASE']]),hide_index=True)
        st.link_button('Review actions on floor ↗','http://127.0.0.1:8502/floor-lab')

elif page=='Guests':
    guests=b['guests'].copy();months=pd.period_range(start,end,freq='M').astype(str)
    region=st.selectbox('Guest region',['All regions']+sorted(guests.home_region.unique()),key='guest_region')
    guests=guests[guests.period_month.isin(months)]
    if region!='All regions':guests=guests[guests.home_region==region]
    st.caption('Guest evidence includes complete months touched by the dates above. Counts are player-months, not distinct visitors. Region filters apply to grouped guest metrics only.')
    metrics([('Tracked wagers',money(guests.wagers.sum())),('Tracked payouts',money(guests.payouts.sum())),('Player net',money(guests.player_net.sum())),('Tracked comp cost',money(guests.comp_cost.sum()))])
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Tracked play by month')
        trend=guests.groupby('period_month',as_index=False)[['wagers','payouts','expected']].sum();chart(px.line(trend,x='period_month',y=['wagers','payouts','expected'],color_discrete_sequence=['#e4bd75','#75c9b9','#d2919e']),'guest_trend',180)
    with right.container(height=245,border=True):
        st.subheader('Cohort context')
        cohorts=guests.groupby('age_band',as_index=False)[['wagers','player_net','player_months','comp_cost']].sum()
        st.dataframe(cohorts,hide_index=True,height=150,width='stretch');st.caption('Player net = payouts − wagers. Expected column means expected player loss; no individual identifiers exported.')
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Property comp economics · all regions')
        loyalty=pd.DataFrame(report['loyalty']);loyalty=loyalty[loyalty.gaming_month.isin(months)]
        loyalty['Economic cost $']=loyalty.cost_cents/100;loyalty['Face value $']=loyalty.face_cents/100
        st.dataframe(loyalty[['gaming_month','Economic cost $','Face value $','points_per_face_dollar']],hide_index=True,height=160,width='stretch');st.caption('Complete included months, property-wide. Face value is not economic cost; changes may reflect redemption mix.')
    with right.container(height=245,border=True):
        st.subheader('Concentration · fixed January–June cohort')
        p=report['players'];st.markdown(f'**{p["tracked_players"]:,} distinct tracked players** accounted for **{p["tracked_wager_coverage"]:.2%}** of machine wagers. The top 1% by wagers contributed **{p["top1pct_wager_share"]:.2%}** of tracked play.')
        st.caption(f'A separate ranking of positive player losses gives {p["top1pct_positive_loss_share"]:.2%} for the top 1%. These groups need not be the same people. Fixed full-cohort results do not change with region/date filters. No targeting heavy losers.')
        csv(guests,'guest-group-evidence.csv')

elif page=='Scenarios':
    c1,c2,c3=st.columns([1,1,2]);budget=c1.number_input('Cash ceiling ($)',0,100000,100000,1000,key='budget')
    retained=c2.slider('Retained play · mode',.1,1.,.5,.05,key='retained')
    names={c['id']:c['name']+' · '+c['target'] for c in report['simulation']['candidates']}
    picked=c3.multiselect('Candidate shortlist',list(names),default=list(names),format_func=names.get,key='candidate_ids')
    candidates=[]
    for original in report['simulation']['candidates']:
        if original['id'] in picked:
            c=b['engine'].evaluate(original['action_type'],original['target'],retained=retained);c['id']=original['id'];candidates.append(c)
    ranks=rank_portfolios(candidates,budget=budget).sort_values(['Expected net benefit','Cost'],ascending=[False,True]);best=ranks.iloc[0]
    metrics([('Available cash',money(budget)),('Recommended cash',money(best.Cost)),('Expected incremental net',money(best['Expected net benefit'])),('Conditional chance positive',f'{best["Chance positive"]:.1%}')])
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Ranked feasible portfolios')
        st.dataframe(ranks,hide_index=True,height=165,width='stretch');st.caption('Same shared DecisionEngine as the floor. At most three types; nonoverlapping targets; keep-budget always included.')
    with right.container(height=245,border=True):
        st.subheader('Recommended within this shortlist')
        st.markdown('**'+best.Actions+'**');st.write(f'10th–90th net: {money(best["10th percentile"])} to {money(best["90th percentile"])}')
        st.caption('Conditional assumptions, not measured action effects. Monte Carlo spans 1,000 shared seeded draws. The nine original targets are a limited search, not global optimization. Cash excludes planned downtime opportunity; net subtracts both.')
        st.link_button('Build a custom plan on the floor ↗','http://127.0.0.1:8502/floor-lab')
    left,right=st.columns([1.4,1])
    with left.container(height=245,border=True):
        st.subheader('Forecast evidence · independent May–June holdout')
        pred=b['predictions'];agg=aggregate_predictions(pred[pred.phase=='May–June holdout'],pred[pred.phase=='April calibration'])
        fig=go.Figure();fig.add_scatter(x=agg.gaming_date,y=agg.coin_in_usd,name='Observed',line_color='#e4bd75');fig.add_scatter(x=agg.gaming_date,y=agg.prediction,name='Prediction',line_color='#75c9b9');chart(fig,'scenario_holdout',145)
        st.caption(f'Machine-day MAE ${b["metadata"]["holdout_mae"]:,.2f} vs ${b["metadata"]["baseline_mae"]:,.2f}. January–March fit → April selection → January–April refit → May–June test.')
    with right.container(height=245,border=True):
        st.subheader('How would we know it worked?')
        st.markdown('Record targets, activation dates and costs. Compare with untreated peers over the same dates. Track availability and contribution per scheduled hour; check whole-floor play for displacement.')
        with st.expander('Assumptions, source catalogue & uncertainty'):
            st.dataframe(pd.DataFrame([{k:c[k] for k in ['id','target','cost','lead_days','additional_theo_cost','assumption']} for c in candidates]),hide_index=True)
            st.write(b['metadata']['interval']);st.caption('April both selects the model and calibrates approximate bands. The original property-level 68.5% comparison is a separate historical model, not this validation.')
            csv(ranks,'ranked-portfolios.csv')
        if st.button('Methods & evidence',key='scenario_evidence'):evidence()
