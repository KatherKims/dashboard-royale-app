"""Three-page casino decision dashboard. Run: python -m streamlit run app.py."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
GOLD, TEAL, WHITE = '#D9B66F', '#65C6BD', '#F4F1E9'
st.set_page_config(page_title='The Gilded Ace | Decision Lab', page_icon='♠', layout='wide')
st.markdown('''<style>
@media (max-width: 1100px) {
  [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {min-width: 180px; flex: 1 1 40%;}
}
</style>''', unsafe_allow_html=True)


@st.cache_data
def load_data():
    path = ROOT / 'data'
    report = json.loads((path / 'analysis_results.json').read_text(encoding='utf-8'))
    return (report, pd.read_parquet(path/'machines.parquet'),
            pd.read_parquet(path/'machine_daily.parquet'),
            pd.read_parquet(path/'guest_groups.parquet'), np.load(path/'scenario_net.npz')['net'])


def money(x):
    return f'-${abs(x):,.0f}' if x < 0 else f'${x:,.0f}'


def chart(fig, title, key):
    fig.update_layout(title=title, paper_bgcolor='#101419', plot_bgcolor='#101419',
                      font=dict(color=WHITE, size=15), colorway=[GOLD, TEAL],
                      margin=dict(l=20, r=30, t=65, b=35), legend_title_text='')
    fig.update_xaxes(gridcolor='#2B333B', zerolinecolor='#47515B')
    fig.update_yaxes(gridcolor='#2B333B', zerolinecolor='#47515B')
    st.plotly_chart(fig, width='stretch', key=key,
                    config={'displaylogo':False, 'toImageButtonOptions':{'format':'svg','filename':key,'width':1600,'height':900}})


def download_table(df, name):
    st.download_button('Download this table', df.to_csv(index=False).encode(), name+'.csv', 'text/csv', key='download_'+name)


report, machines, daily, guests, samples = load_data()
st.sidebar.markdown('## ♠ THE GILDED ACE')
st.sidebar.caption('DASHBOARD ROYALE · SYNTHETIC CASINO')
page = st.sidebar.radio('Explore', ['Casino overview', 'Machine investigation', '$100,000 decision lab'])
st.sidebar.divider()
st.sidebar.caption('Evidence: Jan 1–Jun 30, 2025\n\nDecision horizon: Jul 1–30, 2025')
st.sidebar.caption('Gold = actual earnings · Teal = expected earnings')
with st.sidebar.expander('What does “expected” mean?'):
    st.write('Expected casino earnings = wagers × (1 − configured return to player). Actual earnings = wagers − payouts. Both are before operating costs.')
st.caption('THE GILDED ACE / ANALYTICS & DECISIONS')

if page == 'Casino overview':
    st.title('Read the floor. Question the ranking.')
    st.write('A six-month view of earnings, demand and guest economics.')
    monthly = pd.DataFrame(report['monthly'])
    wager, actual, expected = monthly.wagers.sum(), monthly.actual.sum(), monthly.expected.sum()
    for col, label, value in zip(st.columns(4), ['Wagers', 'Actual earnings · before costs', 'Expected earnings · before costs', 'Actual hold'],
                                  [money(wager), money(actual), money(expected), f'{actual/wager:.2%}']):
        col.metric(label, value)
    st.info(f'Actual earnings are {money(actual-expected)} above expected ({(actual/expected-1):.2%}). That floor-wide result can hide very different machine stories.')
    demand_tab, guest_tab, comp_tab, forecast_tab = st.tabs(['Demand', 'Tracked guests', 'Comps', 'Forecast check'])
    with demand_tab:
        metric = st.radio('Compare demand using', ['Wagers per available machine-hour', 'Wagers per day', 'Total wagers'], horizontal=True)
        y = {'Wagers per available machine-hour':'wagers_per_available_hour','Wagers per day':'wagers_per_day','Total wagers':'wagers'}[metric]
        fig = px.bar(monthly, x='month', y=y, color_discrete_sequence=[GOLD], labels={'month':'Month',y:metric+' ($)'})
        fig.update_yaxes(tickprefix='$', rangemode='tozero')
        chart(fig, metric+' by month', 'monthly_demand')
        st.caption('Per-day comparisons remove unequal month lengths. Per-hour comparisons also account for the number of operating machines. These are associations, not proof of causes.')
        a, b = st.columns(2)
        with a:
            zone = pd.DataFrame(report['zone_monthly']).groupby('zone_name',as_index=False)[['wagers','available_hours']].sum()
            zone['wagers_per_hour']=zone.wagers/zone.available_hours
            chart(px.bar(zone.sort_values('wagers_per_hour'),x='wagers_per_hour',y='zone_name',orientation='h',labels={'wagers_per_hour':'Wagers per available hour ($)','zone_name':'Zone'},color_discrete_sequence=[TEAL]),'Demand by location','zone_demand')
        with b:
            ev = pd.DataFrame(report['event_associations'])
            chart(px.bar(ev,x='event',y='difference_pct',color_discrete_sequence=[GOLD],labels={'event':'Event','difference_pct':'Difference from weekday baseline'}).update_yaxes(tickformat='.0%'),'Event-day associations','events')
            st.caption('Baseline: non-event days with the same weekday. Seasonality, tourism and event overlap can confound this comparison.')
        with st.expander('Sensor coverage and detailed monthly data'):
            st.write('Sensors count entries, not unique visitors. Missing intervals are excluded; rates use covered hours.')
            st.dataframe(pd.DataFrame(report['traffic']),hide_index=True)
            st.dataframe(monthly,hide_index=True)
            download_table(monthly,'monthly_demand')
    with guest_tab:
        p=report['players']
        for col,label,value in zip(st.columns(3),['Tracked players','Share of floor wagers tracked','Player net · payouts less wagers'],[f"{p['tracked_players']:,}",f"{p['tracked_wager_coverage']:.1%}",money(p['player_net'])]):
            col.metric(label,value)
        st.write(f"Tracked guests wagered **{money(p['tracked_wagers'])}** and received **{money(p['tracked_payouts'])}** in payouts. **{p['players_ahead_share']:.1%}** finished ahead across their recorded six-month play.")
        concentration=pd.DataFrame({'Group':['Top 1% of tracked players','Other 99%'],'Share of tracked wagers':[p['top1pct_wager_share'],1-p['top1pct_wager_share']]})
        chart(px.bar(concentration,x='Group',y='Share of tracked wagers',color_discrete_sequence=[GOLD]).update_yaxes(tickformat='.0%'),'Wager concentration','guest_concentration')
        st.caption(f"Top 1% = {p['top1pct_count']:,} players, ranked after summing all six months. A separately ranked top 1% accounts for {p['top1pct_positive_loss_share']:.1%} of positive player losses. Untracked play is excluded; guest groups are descriptive.")
        group=st.selectbox('Compare guest groups',['home_region','age_band'],format_func=lambda s:s.replace('_',' ').title())
        grouped=guests.groupby(group,as_index=False)[['wagers','payouts','player_net','comp_cost']].sum()
        st.dataframe(grouped,hide_index=True)
        download_table(grouped,'guest_groups')
    with comp_tab:
        loyalty=pd.DataFrame(report['loyalty'])
        st.metric('Economic cost of comps · six months',money(monthly.comps.sum()))
        st.write('Economic cost is the cost of providing the benefit. Face value is the price shown to the guest; they are different amounts.')
        chart(px.bar(loyalty,x='gaming_month',y='points_per_face_dollar',labels={'gaming_month':'Month','points_per_face_dollar':'Redeemed points per $1 face value'},color_discrete_sequence=[GOLD]),'Redemption pricing changed sharply in May','comp_points')
        st.caption('This is the observed weighted redemption ratio, not proof of a single uniform posted policy. Ledger timestamps use Las Vegas time and the 6 a.m. gaming-day boundary.')
        fig=go.Figure()
        fig.add_bar(x=monthly.month,y=monthly.comps,name='Economic cost',marker_color=GOLD)
        fig.add_bar(x=monthly.month,y=monthly.comp_face,name='Face value',marker_color=TEAL)
        fig.update_layout(barmode='group');fig.update_yaxes(title='Dollars',tickprefix='$')
        chart(fig,'Comp face value versus economic cost','comp_cost')
        st.dataframe(loyalty,hide_index=True)
    with forecast_tab:
        f=report['forecast']
        st.write('A simple model learns typical wagers for each weekday from January–April, then predicts May–June without using those months for training.')
        a,b=st.columns(2)
        a.metric('Weekday model · daily absolute error',money(f['weekday_mae']))
        b.metric('Constant-average model · daily absolute error',money(f['constant_mae']))
        st.success(f"Weekday model reduced mean absolute error by {f['improvement_pct']:.1%} on the held-out months.")
        test=pd.DataFrame(f['test_rows']);test['gaming_date']=pd.to_datetime(test.gaming_date)
        fig=go.Figure()
        for col,label,color in [('coin_in_usd','Observed wagers',GOLD),('weekday_prediction','Weekday prediction',TEAL)]:
            fig.add_scatter(x=test.gaming_date,y=test[col],name=label,line_color=color)
        fig.update_yaxes(title='Daily wagers ($)',tickprefix='$')
        chart(fig,'Out-of-sample demand check','forecast')
        st.caption(f"Refitting the selected model on January–June gives a July 1–30 baseline of {money(f['july_refit_baseline_wagers'])} wagers. July has no observed outcomes here; it is a planning scenario.")

elif page == 'Machine investigation':
    st.title('Low earnings are a clue, not a verdict.')
    st.write('Separate time on the floor, payout variation, location and downtime before buying replacements.')
    basis=st.radio('Rank the bottom ten by',['Total actual earnings','Actual earnings per active day','Expected earnings per available hour'],horizontal=True)
    key={'Total actual earnings':'house_win_usd','Actual earnings per active day':'actual_per_day','Expected earnings per available hour':'theo_per_hour'}[basis]
    bottom=machines.sort_values([key,'machine_id']).head(10).copy()
    denom = bottom.active_days if key=='actual_per_day' else bottom.available_hours if key=='theo_per_hour' else 1
    fig=go.Figure()
    fig.add_bar(y=bottom.machine_id,x=bottom.house_win_usd/denom,orientation='h',name='Actual',marker_color=GOLD)
    fig.add_bar(y=bottom.machine_id,x=bottom.theo_usd/denom,orientation='h',name='Expected',marker_color=TEAL)
    fig.update_layout(barmode='group',height=540)
    fig.update_yaxes(autorange='reversed',title='Machine')
    unit=' per active day' if key=='actual_per_day' else ' per available hour' if key=='theo_per_hour' else ''
    fig.update_xaxes(title='Casino earnings'+unit+' ($), before costs',tickprefix='$',rangemode='tozero')
    chart(fig,'Bottom 10 · '+basis.lower(),'bottom_ten')
    st.caption('All 310 machine identities are included; some were installed or retired during the period. Total-earnings rankings penalize shorter exposure.')
    download_table(bottom[['machine_id','house_win_usd','theo_usd','active_days','down_hours','eligible_july']],'bottom_ten')
    options=machines.machine_id.tolist()
    selected=st.selectbox('Investigate a machine',options,index=options.index('M-1158'))
    r=machines.set_index('machine_id').loc[selected]
    for col,label,value in zip(st.columns(4),['Active days','Downtime hours','Actual minus expected','Payout gap / modeled SD'],[str(r.active_days),f'{r.down_hours:.1f}',money(r.payout_gap),f'{r.standardized_gap:.2f}']):
        col.metric(label,value)
    st.write(f"**{selected} · {r['theme']} · {r.manufacturer}** — {'eligible for July actions' if r.eligible_july else 'not on the July floor'}. Expected earnings per available hour: **{money(r.theo_per_hour)}**; **{r.peer_ratio:.2f}×** the same-theme median.")
    if abs(r.standardized_gap)>3:
        st.warning('This payout gap deserves inspection of configuration and meters. It does not prove malfunction or deliberate leakage. The variance model assumes independent plays and correct game math; screening many machines also creates extreme observations.')
    sub=daily[daily.machine_id==selected].sort_values('gaming_date')
    fig=go.Figure()
    for field,label,color in [('house_win_usd','Actual',GOLD),('theo_usd','Expected',TEAL)]:
        fig.add_scatter(x=sub.gaming_date,y=sub[field].cumsum(),name=label,line_color=color)
    fig.update_yaxes(title='Cumulative earnings before costs ($)',tickprefix='$')
    chart(fig,selected+' · earnings over time','machine_cumulative')
    st.subheader('What could downtime have cost?')
    down=report['downtime']
    a,b,c=st.columns(3)
    a.metric('Floor downtime · Jan–Jun',f"{down['hours']:,.0f} hours")
    b.metric('Historical wager opportunity · middle case',money(down['missed_wagers_mid']))
    c.metric('Expected earnings opportunity · middle case',money(down['missed_theo_mid']))
    st.caption(f"Historical wager sensitivity range: {money(down['missed_wagers_low'])}–{money(down['missed_wagers_high'])}. Uses same-machine, same-weekday operating rates. This is machine-level opportunity, not proven lost floor revenue: guests may have played elsewhere. The range is not a confidence interval.")
    bymonth=daily.groupby('month',as_index=False)[['down_hours','missed_theo_mid']].sum()
    chart(px.bar(bymonth,x='month',y='down_hours',labels={'month':'Month','down_hours':'Downtime hours'},color_discrete_sequence=[GOLD]),'When downtime occurred','monthly_downtime')
    st.write(f"For **{selected}**, the middle-case historical expected-earnings opportunity is **{money(r.missed_theo_mid)}**. Compare this with its payout gap before proposing a repair.")
    with st.expander('Methods and full machine results'):
        st.write('Modeled payout SD = sqrt(sum(squared bet amounts × payout-multiplier variance)), converted from cents. Peer rates are descriptive, not adjusted causal comparisons. Inactive days are excluded. Downtime comes from raw scheduled and available seconds, preserving daylight-saving day lengths.')
        st.dataframe(machines,hide_index=True)
        download_table(machines,'machine_diagnostics')

else:
    st.title('Put the $100,000 on evidence.')
    st.write('Compare incremental expected contribution over July 1–30, after action costs and planned downtime.')
    sim=report['simulation']; candidates=sim['candidates']; byid={c['id']:c for c in candidates}
    st.info('Default objective: maximize expected 30-day benefit. Action effects below are assumptions; this is a decision model, not a proven return forecast.')
    goal=st.radio('Rank plans by',['Expected 30-day benefit','10th-percentile outcome','Conservative assumptions'],horizontal=True)
    budget=st.slider('Maximum spend',0,100000,100000,1000,format='$%d')
    scale=st.slider('Assumed net operating benefit multiplier',0.0,2.0,1.0,.1)
    st.caption('1.0 = documented assumptions. This scales modeled operating gains and losses together; action costs and planned downtime stay fixed. It is a sensitivity check, not a calibrated probability.')
    fixed=np.array([c['cost']+c['additional_theo_cost'] for c in candidates])
    adjusted=(samples+fixed[:,None])*scale-fixed[:,None]
    ids=[c['id'] for c in candidates]
    rows=[]
    distributions={}
    for idx,p in enumerate(sim['portfolios']):
        if p['cost']>budget: continue
        indices=[ids.index(k) for k in p['actions']]
        net=adjusted[indices].sum(axis=0) if indices else np.zeros(samples.shape[1])
        constant=fixed[indices].sum() if indices else 0
        rows.append({'plan':idx,'Actions':' + '.join(p['actions']) or 'Keep budget','Cost':p['cost'],
                     'Expected benefit':float(net.mean()),'10th percentile':float(np.quantile(net,.1)),
                     '90th percentile':float(np.quantile(net,.9)), 'Chance of positive benefit':float((net>0).mean()),
                     'Conservative case':(p['conservative_net']+constant)*scale-constant})
        distributions[idx]=net
    plans=pd.DataFrame(rows)
    score={'Expected 30-day benefit':'Expected benefit','10th-percentile outcome':'10th percentile','Conservative assumptions':'Conservative case'}[goal]
    plans=plans.sort_values([score,'Cost'],ascending=[False,True]);best=plans.iloc[0]
    st.subheader('Highest-ranked plan: '+best.Actions)
    a,b,c=st.columns(3)
    a.metric('Budget committed',money(best.Cost));b.metric('Expected incremental benefit',money(best['Expected benefit']));c.metric('Budget retained',money(100000-best.Cost))
    if best.Actions=='Keep budget':
        st.write('Under these assumptions, none of the shortlisted spending plans beats retaining the budget over 30 days. A targeted inspection can still buy useful information; that value has not been priced.')
    st.caption(f"{sim['scenarios']:,} shared scenarios · seed {sim['seed']} · {len(plans)} plans within the selected budget. Maximum three action types. Overlapping machine targets are excluded conservatively. One unit per shortlisted candidate; this is not a search of every catalogue quantity and location.")
    top=plans.head(10).sort_values('Expected benefit')
    fig=px.bar(top,x='Expected benefit',y='Actions',orientation='h',color_discrete_sequence=[GOLD])
    fig.update_xaxes(tickprefix='$'); chart(fig,'Shortlisted plans · expected net benefit','plans')
    st.subheader('Compare all three goals')
    compare=[]
    for score_name in ['Expected benefit','10th percentile','Conservative case']:
        row=plans.sort_values([score_name,'Cost'],ascending=[False,True]).iloc[0]
        compare.append({'Goal':score_name,'Highest-ranked plan':row.Actions,'Score':row[score_name],'Cost':row.Cost})
    st.dataframe(pd.DataFrame(compare),hide_index=True)
    labels={int(row.plan):row.Actions for row in plans.itertuples()}
    chosen_label=st.selectbox('Inspect a feasible plan',list(labels.values()))
    chosen=next(k for k,v in labels.items() if v==chosen_label)
    chosen_plan=sim['portfolios'][chosen];net=distributions[chosen]
    if chosen_plan['actions']:
        chart(px.histogram(x=net,nbins=35,color_discrete_sequence=[TEAL],labels={'x':'Incremental contribution after costs ($)','y':'Scenarios'}),'Assumed outcome distribution','plan_distribution')
        st.dataframe(pd.DataFrame([byid[i] for i in chosen_plan['actions']])[['id','target','quantity','cost','lead_days','benefit_days','additional_theo_cost','assumption']],hide_index=True)
    else:
        st.write('Keep-budget baseline: $0 incremental cost and $0 incremental benefit. The casino continues its existing operations.')
    with st.expander('All assumptions, catalogue prices and limitations'):
        st.dataframe(pd.DataFrame(candidates)[['id','target','cost','lead_days','expected_net','assumption']],hide_index=True)
        st.dataframe(pd.DataFrame(report['action_catalog']),hide_index=True)
        for note in sim['limitations']: st.write('• '+note)
    st.subheader('How would we know an action worked?')
    st.write('Inspect M-1158 against its configured payout settings and meter history. For a move or signage trial, preselect comparable control machines or zones and compare changes in expected earnings per available hour, while checking total floor play for displacement. For comps, randomize eligible participants and measure incremental contribution after comp cost; monitor guest retention. Keep payout luck separate from operational improvement.')
    download_table(plans.drop(columns='plan'),'decision_plans')

st.divider()
st.caption('Synthetic challenge data · Earnings are before operating costs unless explicitly labeled incremental contribution. Charts can be exported as SVG using the camera icon. The Databricks notebook contains the reproducible calculations.')
