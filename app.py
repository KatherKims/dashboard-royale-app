"""Compact local AceIQ dashboard. Source exports and shared models are unchanged."""
from pathlib import Path
import html
import base64
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
font_data=base64.b64encode((ROOT/'assets/fonts/Silkscreen-Regular.ttf').read_bytes()).decode('ascii')
st.markdown('<style>@font-face{font-family:Silkscreen;src:url(data:font/ttf;base64,'+font_data+") format('truetype');font-display:swap;}"+(ROOT/'assets/dashboard.css').read_text()+'</style>',unsafe_allow_html=True)

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
if selected.empty:st.info('No active machine records for this zone and date range.');st.stop()
with f3:
    st.caption({'Overview':'Read the floor. Question the odds.','Machines':'Separate demand, downtime and payout variation.','Guests':'Tracked play is a partial view of all visitors.','Scenarios':'Choose a test, not a guaranteed return.'}[page])
summary=machine_summary(selected,machines)
summary['screen']=summary.apply(machine_category,axis=1)

def metrics(items):
    for col,(label,value) in zip(st.columns(4),items):
        with col.container(border=True):st.metric(label,value)

def chart(fig,key,height=300):
    fig.update_layout(height=max(height,300),margin=dict(l=25,r=25,t=55,b=55),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Consolas, monospace',color='#f6eacb',size=14),legend=dict(orientation='h',y=1.19,x=0,font=dict(size=12),title_text=''),hoverlabel=dict(font_size=14),hovermode='closest')
    fig.update_xaxes(gridcolor='#35574b',zeroline=False,automargin=True,title_font_size=13,tickfont_size=12)
    fig.update_yaxes(gridcolor='#35574b',zeroline=False,automargin=True,title_font_size=13,tickfont_size=12)
    if key in ['overview_demand','machine_cumulative','guest_trend','scenario_holdout','loyalty_trend']:
        fig.update_yaxes(title_text='US dollars',tickprefix='$',tickformat='~s')
        fig.update_xaxes(title_text='',nticks=5,tickformat='%b %d' if key in ['machine_cumulative','scenario_holdout'] else '%b %Y')
        fig.update_layout(hovermode='x unified')
    if key in ['guest_trend','loyalty_trend','normalized_demand','monthly_downtime','traffic_context','comp_ratio','points_conversion']:
        fig.update_xaxes(type='category',tickformat=None,title_text='Month',tickangle=0)
    if key=='traffic_context':
        fig.update_layout(legend=dict(y=-.25),margin=dict(l=25,r=25,t=25,b=130))
    st.plotly_chart(fig,width='stretch',key=key,config={'displayModeBar':False,'displaylogo':False,'modeBarButtonsToRemove':['lasso2d','select2d']})

def takeaway(text,detail):
    st.markdown('<div class="chart-takeaway"><strong>TAKEAWAY</strong><br>'+html.escape(text)+'</div>',unsafe_allow_html=True)
    st.caption(detail)

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
    with left.container(border=True):
        st.subheader('Play observed / forecast')
        history=selected.groupby('gaming_date',as_index=False).coin_in_usd.sum()
        future=b['predictions'];future=future[(future.phase=='July forecast') & future.machine_id.isin(summary.machine_id)]
        forecast=future.groupby('gaming_date',as_index=False).prediction.sum()
        fig=go.Figure();fig.add_scatter(x=history.gaming_date,y=history.coin_in_usd,name='Observed wagers',line_color='#e4bd75')
        fig.add_scatter(x=forecast.gaming_date,y=forecast.prediction,name='July forecast · no actuals',line=dict(color='#70cabe',dash='dot'));chart(fig,'overview_demand',165)
        takeaway(f'The selected history contains {money(history.coin_in_usd.sum())} in wagers. The dashed line is a July planning forecast, not observed play.', 'Daily totals vary with exposure and weekday mix. Source: machine_daily + demand_predictions; the forecast is fixed rather than refitted by this filter.')
        st.caption('Event and traffic context is available below the demand summary.')
    with right.container(border=True):
        st.subheader('The floor · July 1 placement')
        slots=b['slots'].merge(machines[['machine_id','theme','theo_per_hour']],on='machine_id',how='left')
        if scope!='Whole floor':
            ids=set(selected.machine_id);slots=slots[slots.machine_id.isin(ids)]
        fig=px.scatter(slots,x='x_m',y='y_m',color='theo_per_hour',hover_name='machine_id',hover_data=['theme','location_id'],color_continuous_scale=['#31554f','#75c9b9','#e4bd75'])
        fig.update_traces(marker=dict(symbol='square',size=8));fig.update_layout(coloraxis_colorbar=dict(title='Expected $/hr',tickprefix='$',thickness=12));fig.update_xaxes(title='Floor x (metres)');fig.update_yaxes(title='Floor y (metres)',scaleanchor='x',constrain='domain',range=[slots.y_m.min()-10,slots.y_m.max()+10]);fig.update_xaxes(range=[slots.x_m.min()-10,slots.x_m.max()+10],tickangle=0,nticks=4,constrain='domain');chart(fig,'overview_floor',340)
        takeaway('Gold marks higher historical expected earnings per available hour; teal marks lower rates.', 'July 1 placements; colors use full-history rates. Location associations do not establish that moving a machine will improve demand.')
        st.link_button('Enter interactive floor lab ↗','http://127.0.0.1:8502/floor-lab')
    left,right=st.columns([1.4,1])
    with left.container(border=True):
        st.subheader('Machines to investigate')
        ranking=st.selectbox('Choose the bottom ten by',['Total actual earnings','Actual earnings per active day','Expected earnings per available hour'],key='bottom_ranking')
        rank_column={'Total actual earnings':'actual_house_win','Actual earnings per active day':'actual_per_active_day','Expected earnings per available hour':'expected_per_available_hour'}[ranking]
        pool=summary.sort_values([rank_column,'machine_id']).head(10).copy()
        columns=['machine_id','actual_house_win','expected_house_win','active_days','availability_rate','screen']
        display=pool[columns].rename(columns={'machine_id':'Machine','actual_house_win':'Actual $','expected_house_win':'Expected $','active_days':'Active days','availability_rate':'Availability','screen':'Investigation lead'})
        bottom=pool.copy()
        bottom['Actual / expected (%)']=100*bottom.actual_house_win/bottom.expected_house_win.replace(0,np.nan)
        bottom=bottom.sort_values('Actual / expected (%)')
        fig=px.bar(bottom,x='Actual / expected (%)',y='machine_id',orientation='h',color_discrete_sequence=['#e4bd75'],text='Actual / expected (%)',labels={'machine_id':'Machine'},hover_data={'actual_house_win':':,.2f','expected_house_win':':,.2f','active_days':True})
        fig.update_traces(texttemplate='%{x:.0f}%',textposition='outside',cliponaxis=False)
        fig.update_xaxes(range=[min(0,bottom['Actual / expected (%)'].min()*1.25),max(120,bottom['Actual / expected (%)'].max()*1.2)],ticksuffix='%')
        fig.add_vline(x=100,line_dash='dash',line_color='#75c9b9',annotation_text='Expected = 100%',annotation_position='top left')
        fig.update_annotations(y=1.05,yref='paper')
        chart(fig,'bottom_ten',420)
        weak=bottom.iloc[0]
        takeaway(f"{weak.machine_id} earned {weak['Actual / expected (%)']:.1f}% of expected earnings over {int(weak.active_days)} active days in this selection.", f'Ten candidates selected by {ranking.lower()}, then ordered by actual/expected. Negative values are retained. A low ratio can reflect payout variation; investigate exposure and variance before replacement.')
        with st.expander('Exact dollars, exposure and availability'):
            st.dataframe(display,hide_index=True,width='stretch',column_config={'Availability':st.column_config.NumberColumn(format='percent'),'Actual $':st.column_config.NumberColumn(format='dollar'),'Expected $':st.column_config.NumberColumn(format='dollar')})
    with right.container(border=True):
        st.subheader('Decision: evidence before replacement')
        st.markdown('**Do not automatically replace the raw bottom ten.** Inspect suspicious payout gaps; compare expected earnings per available hour and downtime first.')
        candidates=b['engine'].shortlist(report['simulation']['candidates']);ranked=rank_portfolios(candidates).sort_values('Expected net benefit',ascending=False)
        best=ranked.iloc[0]
        st.markdown(f'**Default shortlist recommendation:** {best.Actions}. Expected 30-day incremental net: **{money(best["Expected net benefit"])}**.')
        st.caption('Limited candidate search; effects are assumptions. Inspection may have unpriced information value.')
        if st.button('Methods & evidence',key='overview_evidence'):evidence()

        with st.expander('Evidence Claw · draw a machine to investigate',expanded=bool(st.session_state.get('claw_pick'))):
            st.caption('An optional random draw from the ten lowest actual totals. This is an investigation shortcut, not a recommendation or model output.')
            claw_pool=summary.sort_values(['actual_house_win','machine_id']).head(10).machine_id.tolist()
            signature=(str(start),str(end),scope)
            if st.session_state.get('claw_scope')!=signature:
                st.session_state.pop('claw_pick',None);st.session_state.claw_scope=signature
            if st.button('Drop the claw',key='evidence_claw'):
                st.session_state.claw_pick=str(np.random.default_rng().choice(claw_pool))
            picked=st.session_state.get('claw_pick')
            st.markdown('<div class="evidence-claw" aria-hidden="true"><div class="claw-arm">╥<br>╲╱</div><div class="claw-prize">'+html.escape(picked or '♠  ♣  ♦  ♥')+'</div></div>',unsafe_allow_html=True)
            if picked in claw_pool:
                evidence_row=summary.set_index('machine_id').loc[picked]
                st.write(f'{picked}: {money(evidence_row.actual_house_win)} actual / {money(evidence_row.expected_house_win)} expected; {int(evidence_row.active_days)} active days; {evidence_row.availability_rate:.2%} availability.')
                st.caption(evidence_row.screen+' · modeled payout gap '+f'{evidence_row.standardized_gap:.2f} SD. A screening flag is not a diagnosis.')
                st.markdown(f'[Investigate {picked} →](?page=Machines&machine={picked})')


    with st.container(border=True):
        st.subheader('Demand after accounting for available hours')
        month=selected.assign(month=selected.gaming_date.dt.strftime('%Y-%m')).groupby('month',as_index=False).agg(wagers=('coin_in_usd','sum'),hours=('available_hours','sum'))
        month['Wagers / available hour']=month.wagers/month.hours.replace(0,np.nan)
        fig=px.line(month,x='month',y='Wagers / available hour',markers=True,color_discrete_sequence=['#75c9b9'],labels={'month':'Month'})
        fig.update_yaxes(tickprefix='$',rangemode='tozero');chart(fig,'normalized_demand')
        peak=month.loc[month['Wagers / available hour'].idxmax()];last=month.iloc[-1]
        takeaway(f"Demand peaked in {peak.month} at ${peak['Wagers / available hour']:,.2f} per available hour; the latest selected month was ${last['Wagers / available hour']:,.2f}.", 'Wagers divided by available machine-hours separates changing exposure from play intensity. Partial date selections produce partial-month summaries; event timing and floor mix can still matter.')

    with st.expander('Payout variation · residual uncertainty screen',expanded=False):
        residual=summary.dropna(subset=['standardized_gap','expected_house_win','actual_minus_expected'])
        fig=px.scatter(residual,x='expected_house_win',y='actual_minus_expected',color='standardized_gap',hover_name='machine_id',color_continuous_scale=['#d2919e','#f6eacb','#75c9b9'],color_continuous_midpoint=0,labels={'expected_house_win':'Expected earnings ($)','actual_minus_expected':'Actual minus expected ($)','standardized_gap':'Gap / SD'})
        fig.add_hline(y=0,line_dash='dash',line_color='#e4bd75');fig.update_xaxes(tickprefix='$',tickformat='~s');fig.update_yaxes(tickprefix='$',tickformat='~s');chart(fig,'residual_screen',420)
        flags=int((residual.standardized_gap<=-3).sum())
        takeaway(f'{flags} machines have a selected-period payout gap at or below −3 modeled standard deviations.', 'Color scales the dollar gap by modeled payout variability. This is not a multiple-testing-adjusted significance test or proof of malfunction.')
    with st.expander('Event and zone traffic context · fixed January–June evidence'):
        events=pd.DataFrame(report['event_associations']).sort_values('difference_pct')
        events['Difference (%)']=events.difference_pct*100
        fig=px.bar(events,x='Difference (%)',y='event',orientation='h',color_discrete_sequence=['#e4bd75'],labels={'event':'Event'},hover_data=['days'])
        fig.update_yaxes(tickfont_size=11);fig.update_xaxes(ticksuffix='%');chart(fig,'event_context',450)
        peak_event=events.iloc[-1]
        takeaway(f"{peak_event.event} had the largest displayed difference: {peak_event['Difference (%)']:.1f}% above its weekday baseline.", 'Full-property fixed event windows, independent of date/zone filters. These are associations, not estimates that events caused extra play.')
        traffic=pd.DataFrame(report['traffic']);zone_lookup=b['slots'][['zone_id','bank_id']].drop_duplicates().merge(daily[['bank_id','zone_name']].drop_duplicates(),on='bank_id');zone_names=zone_lookup.drop_duplicates('zone_id').set_index('zone_id').zone_name.to_dict()
        traffic['Zone']=traffic.zone_id.map(zone_names).fillna(traffic.zone_id)
        fig=px.line(traffic,x='month',y='entries_per_covered_hour',color='Zone',markers=True,color_discrete_sequence=['#e4bd75','#75c9b9','#d2919e','#9ecbff','#c7a1ff','#f6eacb','#f0a86b'],labels={'entries_per_covered_hour':'Entries per covered hour'})
        fig.update_layout(legend=dict(orientation='h',y=-.3));chart(fig,'traffic_context',430)
        takeaway(f'Minimum valid-interval share in these counter summaries is {traffic.valid_interval_share.min():.1%}.', 'Entries are not unique visitors. Rates use covered hours; missing intervals are not zero traffic. Fixed six-month context, not the current zone/date selection.')
    with st.expander('Downtime opportunity by zone'):
        zone_loss=selected.groupby('zone_name',as_index=False).agg(opportunity=('missed_theo_mid','sum'),hours=('down_hours','sum')).sort_values('opportunity')
        fig=px.bar(zone_loss,x='opportunity',y='zone_name',orientation='h',color_discrete_sequence=['#d2919e'],labels={'zone_name':'Zone','opportunity':'Expected-earnings opportunity'},hover_data={'hours':':,.1f'})
        fig.update_xaxes(tickprefix='$',tickformat='~s');chart(fig,'zone_downtime',350)
        takeaway(f'The current selection contains {zone_loss.hours.sum():,.1f} unavailable hours and {money(zone_loss.opportunity.sum())} of estimated expected-earnings opportunity.', 'Same-machine/weekday operating-rate assumptions; players may switch machines, so this is not proven net floor loss.')

elif page=='Machines':
    selector,bankcol=st.columns([2,1])
    latest=selected.sort_values('gaming_date').drop_duplicates('machine_id',keep='last')
    bank=bankcol.selectbox('Bank',['All banks']+sorted(latest.bank_id.dropna().unique()),key='machine_bank')
    ids=latest.machine_id if bank=='All banks' else latest.loc[latest.bank_id==bank,'machine_id']
    choices=summary[summary.machine_id.isin(ids)].sort_values('actual_house_win')
    if choices.empty:st.info('No machines in this selection.');st.stop()
    linked=st.query_params.get('machine')
    if linked in choices.machine_id.values and st.session_state.get('_linked_machine')!=linked:
        st.session_state.machine_id=linked;st.session_state._linked_machine=linked
    mid=selector.selectbox('Find a machine',choices.machine_id.tolist(),format_func=lambda m:m+' · '+machines.set_index('machine_id').loc[m,'theme'],key='machine_id')
    row=summary.set_index('machine_id').loc[mid];md=selected[selected.machine_id==mid].sort_values('gaming_date')
    metrics([('Actual / expected',f'{money(row.actual_house_win)} / {money(row.expected_house_win)}'),('Expected / available hour',money(row.expected_per_available_hour)),('Availability',f'{row.availability_rate:.2%}'),('Payout gap / SD',f'{row.standardized_gap:.2f}')])
    left,right=st.columns([1.4,1])
    with left.container(border=True):
        st.subheader('Cumulative actual versus expected')
        fig=go.Figure();fig.add_scatter(x=md.gaming_date,y=md.house_win_usd.cumsum(),name='Actual',line_color='#e4bd75');fig.add_scatter(x=md.gaming_date,y=md.theo_usd.cumsum(),name='Expected',line_color='#75c9b9');chart(fig,'machine_cumulative',175)
        takeaway(f'{mid} finished {money(row.actual_minus_expected)} versus expected earnings across {int(row.active_days)} active days.', f'Selected-period payout gap: {row.standardized_gap:.2f} modeled standard deviations. This screens unusual results; it does not diagnose a defect.')
    with right.container(border=True):
        st.subheader('Availability · monthly first')
        monthly=md.assign(month=md.gaming_date.dt.strftime('%Y-%m')).groupby('month',as_index=False).agg(down_hours=('down_hours','sum'),scheduled=('scheduled_hours','sum'),available=('available_hours','sum'))
        monthly['Availability %']=monthly.available/monthly.scheduled*100
        fig=px.bar(monthly,x='month',y='down_hours',text='down_hours',color_discrete_sequence=['#d2919e'],labels={'month':'Month','down_hours':'Unavailable hours'})
        fig.update_traces(texttemplate='%{y:.1f} h',textposition='outside',cliponaxis=False);fig.update_yaxes(rangemode='tozero');chart(fig,'monthly_downtime')
        worst=monthly.loc[monthly.down_hours.idxmax()]
        takeaway(f'{mid} had {md.down_hours.sum():.1f} unavailable hours; {worst.month} had the most ({worst.down_hours:.1f} hours).', f'Overall availability in this selection: {row.availability_rate:.2%}. Estimated expected-earnings opportunity: {money(row.estimated_downtime_opportunity)}; displaced play may be retained elsewhere.')
        with st.expander('Monthly availability details'):
            st.dataframe(monthly[['month','down_hours','Availability %']].rename(columns={'month':'Month','down_hours':'Unavailable hours'}),hide_index=True,width='stretch')
        with st.expander('Daily outages'):st.dataframe(md[['gaming_date','down_hours','missed_theo_mid']],hide_index=True)
    left,right=st.columns([1.4,1])
    with left.container(border=True):
        st.subheader('Demand versus theme peers')
        peers=summary[summary.theme==row.theme].sort_values('expected_per_available_hour')
        fig=go.Figure();fig.add_scatter(x=peers.expected_per_available_hour,y=peers.availability_rate,mode='markers',text=peers.machine_id,name='Same theme',marker=dict(color='#75c9b9',size=10),hovertemplate='%{text}<br>Expected / hour: $%{x:.2f}<br>Availability: %{y:.2%}<extra></extra>')
        fig.add_scatter(x=[row.expected_per_available_hour],y=[row.availability_rate],mode='markers',name=mid,marker=dict(symbol='circle-open',size=19,color='#e4bd75',line_width=3))
        fig.update_xaxes(title='Expected earnings / available hour',tickprefix='$');fig.update_yaxes(title='Availability',tickformat='.1%');chart(fig,'machine_peers')
        median=peers.expected_per_available_hour.median()
        takeaway(f'{mid} generates ${row.expected_per_available_hour:,.2f} expected earnings per available hour; the same-theme median is ${median:,.2f}.', 'The gold ring identifies the selected machine. This descriptive comparison does not fully control location, denomination or guest mix.')
    with right.container(border=True):
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
    if guests.empty:st.info('No guest groups in this selection.');st.stop()
    st.caption('Guest evidence includes complete months touched by the dates above. Counts are player-months, not distinct visitors. Region filters apply to grouped guest metrics only.')
    metrics([('Tracked wagers',money(guests.wagers.sum())),('Tracked payouts',money(guests.payouts.sum())),('Player net',money(guests.player_net.sum())),('Tracked comp cost',money(guests.comp_cost.sum()))])
    left,right=st.columns([1.4,1])
    with left.container(border=True):
        st.subheader('Tracked play by month')
        trend=guests.groupby('period_month',as_index=False)[['wagers','payouts','expected']].sum().rename(columns={'wagers':'Wagers','payouts':'Payouts','expected':'Expected player loss'})
        chart(px.line(trend,x='period_month',y=['Wagers','Payouts','Expected player loss'],markers=True,color_discrete_sequence=['#e4bd75','#75c9b9','#d2919e']),'guest_trend')
        takeaway(f'Tracked guests wagered {money(guests.wagers.sum())} and received {money(guests.payouts.sum())}; player net was {money(guests.player_net.sum())}.', 'Player net = payouts minus wagers. Expected player loss is a different measure, based on configured game math. Carded activity is only part of casino play.')
    with right.container(border=True):
        st.subheader('Cohort context')
        cohorts=guests.groupby('age_band',as_index=False)[['wagers','player_net','player_months','comp_cost']].sum()
        fig=px.bar(cohorts.sort_values('wagers'),x='wagers',y='age_band',orientation='h',color_discrete_sequence=['#e4bd75'],labels={'wagers':'Tracked wagers','age_band':'Age band'})
        fig.update_xaxes(tickprefix='$',tickformat='~s');chart(fig,'guest_cohorts')
        top=cohorts.loc[cohorts.wagers.idxmax()]
        takeaway(f'{top.age_band} accounts for {top.wagers/guests.wagers.sum():.1%} of displayed tracked wagers.', 'Grouped carded play, not all visitors or a recommendation to target guests by gambling losses. Group counts are player-months, not unique visitors.')
        with st.expander('Cohort totals'):st.dataframe(cohorts,hide_index=True,width='stretch')
    left,right=st.columns([1.4,1])
    with left.container(border=True):
        st.subheader('Property comp economics · all regions')
        loyalty=pd.DataFrame(report['loyalty']);loyalty=loyalty[loyalty.gaming_month.isin(months)]
        loyalty['Economic cost $']=loyalty.cost_cents/100;loyalty['Face value $']=loyalty.face_cents/100
        fig=px.bar(loyalty,x='gaming_month',y=['Economic cost $','Face value $'],barmode='group',color_discrete_sequence=['#e4bd75','#75c9b9'],labels={'gaming_month':'Month'})
        chart(fig,'loyalty_trend')
        takeaway(f"Comps cost {money(loyalty['Economic cost $'].sum())} economically versus {money(loyalty['Face value $'].sum())} in face value for the included months.", 'Both bars use the same dollar axis. Property-wide, all regions. Face value is not economic cost; changing redemption mix can affect the relationship.')
        with st.expander('Comp detail and points conversion'):
            st.dataframe(loyalty[['gaming_month','Economic cost $','Face value $','points_per_face_dollar']],hide_index=True,width='stretch')
    with right.container(border=True):
        st.subheader('Concentration · fixed January–June cohort')
        p=report['players'];st.markdown(f'**{p["tracked_players"]:,} distinct tracked players** accounted for **{p["tracked_wager_coverage"]:.2%}** of machine wagers. The top 1% by wagers contributed **{p["top1pct_wager_share"]:.2%}** of tracked play.')
        st.caption(f'A separate ranking of positive player losses gives {p["top1pct_positive_loss_share"]:.2%} for the top 1%. These groups need not be the same people. Fixed full-cohort results do not change with region/date filters. No targeting heavy losers.')
        csv(guests,'guest-group-evidence.csv')
    with st.expander('What changed in loyalty economics?',expanded=True):
        left,right=st.columns(2)
        with left:
            fig=px.line(loyalty,x='gaming_month',y='points_per_face_dollar',markers=True,color_discrete_sequence=['#e4bd75'],labels={'points_per_face_dollar':'Points per face-value dollar'})
            chart(fig,'points_conversion')
            first,last=loyalty.iloc[0],loyalty.iloc[-1]
            takeaway(f'Redemption intensity changed from {first.points_per_face_dollar:.2f} to {last.points_per_face_dollar:.2f} points per face-value dollar.', 'Complete included months, all regions. This reflects observed redemptions; it does not prove a uniform policy change or its causal effect. Comp cost is included in linked POS COGS: do not subtract both twice.')
        with right:
            comp=period_prop.assign(month=period_prop.gaming_date.dt.strftime('%Y-%m')).groupby('month',as_index=False).agg(cost=('comp_cost_usd','sum'),theo=('theo_usd','sum'))
            comp['Comp cost / expected earnings']=comp.cost/comp.theo.replace(0,np.nan)
            fig=px.line(comp,x='month',y='Comp cost / expected earnings',markers=True,color_discrete_sequence=['#75c9b9']);fig.update_yaxes(tickformat='.2%');chart(fig,'comp_ratio')
            takeaway(f'Comp cost was {comp.cost.sum()/comp.theo.sum():.2%} of expected gaming earnings over the exact selected dates.', 'Property-wide regardless of guest region. Unlike grouped guest and redemption data, this daily property calculation follows the exact date range.')

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
    with left.container(border=True):
        st.subheader('Ranked feasible portfolios')
        st.dataframe(ranks,hide_index=True,height=165,width='stretch');st.caption('Same shared DecisionEngine as the floor. At most three types; nonoverlapping targets; keep-budget always included.')
    with right.container(border=True):
        st.subheader('Recommended within this shortlist')
        st.markdown('**'+best.Actions+'**');st.write(f'10th–90th net: {money(best["10th percentile"])} to {money(best["90th percentile"])}')
        st.caption('Conditional assumptions, not measured action effects. Monte Carlo spans 1,000 shared seeded draws. The nine original targets are a limited search, not global optimization. Cash excludes planned downtime opportunity; net subtracts both.')
        st.link_button('Build a custom plan on the floor ↗','http://127.0.0.1:8502/floor-lab')
    left,right=st.columns([1.4,1])
    with left.container(border=True):
        st.subheader('Forecast evidence · independent May–June holdout')
        pred=b['predictions'];agg=aggregate_predictions(pred[pred.phase=='May–June holdout'],pred[pred.phase=='April calibration'])
        fig=go.Figure();fig.add_scatter(x=agg.gaming_date,y=agg.coin_in_usd,name='Observed',line_color='#e4bd75');fig.add_scatter(x=agg.gaming_date,y=agg.prediction,name='Prediction',line_color='#75c9b9');fig.add_scatter(x=agg.gaming_date,y=agg.constant,name='Constant baseline',line=dict(color='#d2919e',dash='dot'));chart(fig,'scenario_holdout',320)
        takeaway(f"Machine-day forecast error was ${b['metadata']['holdout_mae']:,.2f}, versus ${b['metadata']['baseline_mae']:,.2f} for the constant baseline ({1-b['metadata']['holdout_mae']/b['metadata']['baseline_mae']:.1%} lower).", 'Lines aggregate machine forecasts to daily property totals; error above is measured per machine-day. January–March fit, April selection, January–April refit, frozen May–June test. July has no actual outcomes.')
    with right.container(border=True):
        st.subheader('How would we know it worked?')
        st.markdown('Record targets, activation dates and costs. Compare with untreated peers over the same dates. Track availability and contribution per scheduled hour; check whole-floor play for displacement.')
        with st.expander('Assumptions, source catalogue & uncertainty'):
            st.dataframe(pd.DataFrame([{k:c[k] for k in ['id','target','cost','lead_days','additional_theo_cost','assumption']} for c in candidates]),hide_index=True)
            st.write(b['metadata']['interval']);st.caption('April both selects the model and calibrates approximate bands. The original property-level 68.5% comparison is a separate historical model, not this validation.')
            csv(ranks,'ranked-portfolios.csv')
        if st.button('Methods & evidence',key='scenario_evidence'):evidence()
