"""Interactive forecasts, a coordinate-based floor, and one shared decision lab."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dashboard.analytics import floor_snapshot, machine_summary, machine_category
from dashboard.forecast import aggregate_predictions
from dashboard.decisions import DecisionEngine, rank_portfolios

GOLD, TEAL, RED, MUTED = '#D9B66F', '#65C6BD', '#FF756B', '#AEB8C3'


def money(value):
    if pd.isna(value):
        return '—'
    return f'-${abs(value):,.0f}' if value < 0 else f'${value:,.0f}'


def plot(fig, key, height=400, selectable=False, on_select=None):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#101820',
                      font=dict(color='#F7F3EC', size=13), height=height,
                      margin=dict(l=18, r=18, t=45, b=25),
                      legend=dict(orientation='h', y=1.13), hovermode='closest')
    fig.update_xaxes(gridcolor='#273440')
    fig.update_yaxes(gridcolor='#273440')
    if key == 'interactive_floor':
        fig.update_layout(title=None, margin=dict(l=30, r=18, t=15, b=70),
                          legend=dict(orientation='h', y=-.14, font=dict(size=10)))
    return st.plotly_chart(fig, key=key, width='stretch',
                           on_select=on_select or ('rerun' if selectable else 'ignore'), selection_mode='points',
                           config={'displaylogo': False, 'toImageButtonOptions': {'format': 'svg', 'filename': key}})


def render_forecast(predictions, metadata):
    st.subheader('Predict demand. Compare with what happened.')
    st.caption('Target: daily wagers, not realized casino profit. This view has its own fixed validation dates; the sidebar evidence filter does not change the trained model.')
    a, b, c = st.columns([1, 1.3, 1.4])
    scope = a.selectbox('Prediction level', ['Whole floor', 'Zone', 'Bank', 'Machine'], key='forecast_level')
    column = {'Zone': 'zone_name', 'Bank': 'bank_id', 'Machine': 'machine_id'}.get(scope)
    rows = predictions
    if column:
        value = b.selectbox('Prediction target', sorted(predictions[column].dropna().unique()), key='forecast_target_' + scope)
        rows = rows[rows[column] == value]
    else:
        b.caption('All active machines in each period')
    phase = c.selectbox('Compare period', ['May–June holdout', 'July forecast'], key='forecast_phase')
    cal = rows[rows.phase == 'April calibration']
    selected = rows[rows.phase == phase]
    if selected.empty:
        st.info('This selection has no active machines in this period.')
        return
    agg = aggregate_predictions(selected, cal)
    fig = go.Figure()
    if agg.low.notna().any():
        fig.add_scatter(x=agg.gaming_date, y=agg.high, name='April-based daily error band', line=dict(width=0), showlegend=False)
        fig.add_scatter(x=agg.gaming_date, y=agg.low, fill='tonexty', fillcolor='rgba(101,198,189,.16)', line=dict(width=0), name='Illustrative 80% band')
    fig.add_scatter(x=agg.gaming_date, y=agg.prediction, name='Demand prediction', line=dict(color=TEAL, width=3))
    if phase == 'May–June holdout':
        fig.add_scatter(x=agg.gaming_date, y=agg.coin_in_usd, name='Actual wagers', line=dict(color=GOLD, width=3))
        fig.add_scatter(x=agg.gaming_date, y=agg.constant, name='Constant baseline', line=dict(color=MUTED, dash='dot'))
    fig.update_yaxes(title='Daily wagers ($)', tickprefix='$')
    fig.update_layout(hovermode='x unified')
    plot(fig, 'prediction_comparison', 450)
    metrics = st.columns(4)
    metrics[0].metric('Predicted wagers', money(agg.prediction.sum()))
    if phase == 'May–June holdout':
        errors = agg.coin_in_usd - agg.prediction
        mae = errors.abs().mean()
        base = (agg.coin_in_usd - agg.constant).abs().mean()
        metrics[1].metric('Daily prediction error · MAE', money(mae))
        metrics[2].metric('MAE change vs baseline', f'{(1-mae/base):.1%}' if base else '—', help='Positive means less error. Negative means the model is worse for this selection.')
        usable = agg.low.notna() & agg.high.notna()
        coverage = ((agg.coin_in_usd >= agg.low) & (agg.coin_in_usd <= agg.high))[usable].mean()
        metrics[3].metric('Actuals inside error band', f'{coverage:.0%}' if usable.any() else 'Not enough April data')
        if base and mae >= base:
            st.warning('The weekday model does not beat the constant baseline for this selection. Keep this limitation visible.')
        residual = px.bar(agg.assign(error=errors), x='gaming_date', y='error', labels={'gaming_date': 'Date', 'error': 'Actual − predicted wagers ($)'}, color_discrete_sequence=[GOLD])
        plot(residual, 'prediction_residuals', 220)
    else:
        metrics[1].metric('Forecast days', str(len(agg)))
        metrics[2].metric('Observed July results', 'Not available')
        metrics[3].metric('Model', metadata['model'].title())
        st.info('July is a forecast. Changing assumptions about an intervention belongs in the Decision Lab; it does not alter this validated baseline.')
    if agg.low.isna().all():
        st.caption('No error band: fewer than 14 April calibration days for this selection.')
    with st.expander('How this prediction works and where it can fail'):
        st.write('Each machine gets a historical daily wager baseline. The weekday model adjusts it for the day of week and smooths sparse machine histories toward broader patterns.')
        st.write(metadata['selection']); st.write(metadata['test']); st.write(metadata['future']); st.write(metadata['interval'])
        st.write('Machine-day MAE on the full final holdout: ' + money(metadata['holdout_mae']) + '; baseline: ' + money(metadata['baseline_mae']) + '.')
        st.write('New machines use a theme-average fallback. Demand shifts, events, moves, downtime, and new game titles can break historical patterns. Aggregation can hide individual errors. The April band is approximate, not a promise of 80% future coverage.')
        st.write('July action earnings use predicted wagers × historical configured hold. Maintenance uses historical downtime opportunity; intervention effects are still assumptions.')
    st.download_button('Download prediction comparison', agg.to_csv(index=False).encode(), 'aceiq_predictions.csv', 'text/csv', key='download_predictions')


def map_figure(snapshot, locations, walkways, metric, selected, destination=None, affected=(), date=None):
    fig = go.Figure()
    zones = locations[locations.node_type == 'zone'].set_index('location_id')
    # Connections are schematic straight lines between supplied zone coordinates.
    for row in walkways.itertuples():
        if row.zone_a not in zones.index or row.zone_b not in zones.index:
            continue
        a, b = zones.loc[row.zone_a], zones.loc[row.zone_b]
        closed = False
        if date is not None and pd.notna(row.closed_from_utc):
            instant = (pd.Timestamp(date).normalize() + pd.Timedelta(hours=6)).tz_localize('America/Los_Angeles').tz_convert('UTC')
            start = pd.Timestamp(row.closed_from_utc).tz_localize('UTC') if pd.Timestamp(row.closed_from_utc).tzinfo is None else pd.Timestamp(row.closed_from_utc)
            end = pd.Timestamp(row.closed_to_utc)
            end = end.tz_localize('UTC') if end.tzinfo is None else end
            closed = start <= instant and (pd.isna(end) or instant < end)
        fig.add_scatter(x=[a.x_m, b.x_m], y=[a.y_m, b.y_m], mode='lines',
                        line=dict(color=RED if closed else '#304352', width=3, dash='dash' if closed else 'solid'),
                        hoverinfo='skip', showlegend=False)
    empty = snapshot[snapshot.machine_id.isna()]
    fig.add_scatter(x=empty.x_m, y=empty.y_m, mode='markers', name='Empty slot',
                    marker=dict(symbol='square-open', size=10, color=MUTED),
                    customdata=np.column_stack([empty.location_id, np.repeat('', len(empty))]),
                    hovertemplate='Empty %{customdata[0]}<extra></extra>')
    occupied = snapshot[snapshot.machine_id.notna()].copy()
    values = pd.to_numeric(occupied[metric], errors='coerce')
    known = occupied[values.notna()]
    fig.add_scatter(x=known.x_m, y=known.y_m, mode='markers', name='Machine',
        customdata=known[['location_id', 'machine_id', 'bank_id']].to_numpy(),
        marker=dict(symbol='square', size=11, color=known[metric], colorscale=[[0, '#334B61'], [.5, TEAL], [1, GOLD]],
                    line=dict(color='#091017', width=1), colorbar=dict(title='Selected metric', thickness=10, len=.65)),
        hovertemplate='%{customdata[1]} · %{customdata[0]}<br>Bank %{customdata[2]}<br>Value: %{marker.color:,.2f}<extra></extra>')
    missing = occupied[values.isna()]
    fig.add_scatter(x=missing.x_m, y=missing.y_m, mode='markers', name='No evidence',
                    marker=dict(symbol='square', size=11, color='#6B727C'), customdata=missing[['location_id', 'machine_id']].to_numpy(),
                    hovertemplate='%{customdata[1]}<br>No evidence in selected period<extra></extra>')
    for ids, field, color, name, symbol in [([selected], 'machine_id', '#FFFFFF', 'Selected machine', 'square-open'),
                                           (list(affected), 'machine_id', '#B985F4', 'Action scope', 'square-open'),
                                           ([destination], 'location_id', '#FF756B', 'Proposed destination', 'diamond-open')]:
        marked = snapshot[snapshot[field].isin(ids)]
        fig.add_scatter(x=marked.x_m, y=marked.y_m, mode='markers', name=name,
                        marker=dict(symbol=symbol, size=20, color=color, line=dict(width=2)), hoverinfo='skip')
    source = snapshot[snapshot.machine_id == selected]
    dest = snapshot[snapshot.location_id == destination]
    if not source.empty and not dest.empty:
        fig.add_annotation(x=float(dest.x_m.iloc[0]), y=float(dest.y_m.iloc[0]), ax=float(source.x_m.iloc[0]), ay=float(source.y_m.iloc[0]),
                           xref='x', yref='y', axref='x', ayref='y', showarrow=True, arrowhead=3, arrowcolor=RED, arrowwidth=2)
    for zid, row in zones.iterrows():
        label = row['name'] if pd.notna(row['name']) else zid
        fig.add_annotation(x=row.x_m, y=row.y_m, text=str(label), yshift=28,
                           showarrow=False, font=dict(size=12, color=GOLD, family='monospace'), bgcolor='#101820')
    fig.update_layout(clickmode='event+select', dragmode='pan', uirevision='floor-layout-v2',
                      legend=dict(orientation='h', font=dict(size=10)), title='♠ FLOOR CONTROL · supplied coordinates')
    slots = locations[locations.node_type == 'slot']
    fig.update_xaxes(title='x (meters)', zeroline=False, dtick=20, constrain='domain',
                     range=[float(slots.x_m.min()) - 10, float(slots.x_m.max()) + 10], autorange=False)
    fig.update_yaxes(title='y (meters)', zeroline=False, scaleanchor='x', scaleratio=1, dtick=20, constrain='domain',
                     range=[float(slots.y_m.min()) - 10, float(slots.y_m.max()) + 10], autorange=False)
    return fig


def render_floor(engine, daily, machines, locations, placements, walkways, start_date, end_date):
    st.subheader('Floor control')
    st.caption('Select a machine on the map or use the controls. Positions come from the supplied placement history; connections are schematic, not measured walkway routes.')
    mode = st.radio('Floor mode', ['Explore historical floor', 'Plan July actions'], horizontal=True, key='floor_mode')
    planning = mode == 'Plan July actions'
    if planning:
        snapshot_date = pd.Timestamp('2025-07-01')
        evidence = daily
        st.caption('July 1, 06:00 Las Vegas snapshot · decisions use all January–June evidence and the July forecast, independent of the sidebar filter.')
    else:
        snapshot_date = st.date_input('Floor snapshot date', value=end_date.date(), min_value=daily.gaming_date.min().date(), max_value=daily.gaming_date.max().date(), key='floor_snapshot_date')
        evidence = daily[daily.gaming_date.between(start_date, end_date)]
        st.caption(f'Map positions: {snapshot_date}. Colors summarize {start_date:%b %d}–{end_date:%b %d}; they are not live readings.')
    snap = floor_snapshot(placements, locations, machines, snapshot_date)
    summary = machine_summary(evidence, machines)
    snap = snap.merge(summary, on='machine_id', how='left', validate='many_to_one')
    control1, control2, control3 = st.columns([1, 1, 1.3])
    zone_names = locations[locations.node_type == 'zone'].set_index('location_id')['name'].to_dict()
    zone = control1.selectbox('Map zone', ['All zones'] + sorted(snap.zone_id.dropna().unique()), format_func=lambda v: zone_names.get(v, v), key='map_zone')
    visible = snap if zone == 'All zones' else snap[snap.zone_id == zone]
    bank = control2.selectbox('Map bank', ['All banks'] + sorted(visible.bank_id.dropna().unique()), key='map_bank')
    if bank != 'All banks':
        visible = visible[visible.bank_id == bank]
    colors = {'Expected earnings / available hour ($)': 'expected_per_available_hour', 'Downtime hours': 'downtime_hours',
              'Actual − expected earnings ($)': 'actual_minus_expected', 'Availability (%)': 'availability_pct'}
    snap['availability_pct'] = snap.availability_rate * 100
    visible = snap.loc[visible.index]
    lens = control3.selectbox('Color machines by', list(colors), key='map_color')
    ids = sorted(visible.machine_id.dropna().unique())
    if not ids:
        st.info('No occupied slots in this selection.')
        return
    if st.session_state.get('floor_machine') not in ids:
        st.session_state['floor_machine'] = 'M-1158' if 'M-1158' in ids else ids[0]
    selected = st.selectbox('Selected floor machine', ids, key='floor_machine')
    m = engine.summary.loc[selected] if planning else summary.set_index('machine_id').reindex([selected]).iloc[0]
    action = 'Keep in place'; destination = None; result = None
    if planning:
        action_names = {'Keep in place': None, 'Inspect configuration & meters': 'A-INSPECT', 'Move to an empty slot': 'A-MOVE-MACHINE',
                        'Lease / replace machine': 'A-REPLACE-LEASE', 'Manufacturer maintenance sweep': 'A-PREVENTIVE'}
        eligible = selected in engine.eligible.index
        if not eligible:
            st.warning('This machine has fewer than 28 observed active days or is not July-eligible. Intervention controls are disabled.')
        action = st.selectbox('Proposed July action', list(action_names), key='floor_action', disabled=not eligible)
        if not eligible:
            action = 'Keep in place'
        if action == 'Move to an empty slot':
            slots = snap[snap.machine_id.isna()]
            if slots.empty:
                st.warning('No empty destination slots. Swaps require a separate two-machine plan.')
                action = 'Keep in place'
            else:
                dest_map = slots.set_index('location_id')
                destination = st.selectbox('Empty destination slot', slots.location_id.tolist(), key='move_destination',
                                          format_func=lambda v: f'{v} · {zone_names.get(dest_map.loc[v, "zone_id"], dest_map.loc[v, "zone_id"])}')
                st.caption('An empty slot passes the occupancy check. Power, cabinet compatibility, accessibility and operating approval still need confirmation. Zone demand differences do not automatically determine uplift.')
        with st.expander('Scenario assumptions', expanded=False):
            retain = st.slider('Share of increased play that is new to the floor (%)', 10, 100, 50, 5, key='retention_percent') / 100
            move = st.slider('Assumed move uplift · most likely (%)', -10, 100, 20, 5, key='move_percent') / 100
            lease = st.slider('Assumed replacement uplift · most likely (%)', 0, 150, 50, 5, key='lease_percent') / 100
            recovery = st.slider('Assumed downtime recovery · most likely (%)', 10, 85, 50, 5, key='recovery_percent') / 100
            st.caption('1,000 shared scenarios; demand multiplier 0.85–1.15. These probabilities are conditional on assumptions, not measured intervention success rates.')
        if action_names[action]:
            target = m.manufacturer if action == 'Manufacturer maintenance sweep' else selected
            result = engine.evaluate(action_names[action], target, retained=retain, move_mode=move, lease_mode=lease, recovery_mode=recovery)
    affected = result['targets'] if result else []
    chart_col, detail_col = st.columns([2.5, 1])
    with chart_col:
        fig = map_figure(visible, locations, walkways, colors[lens], selected, destination, affected, snapshot_date)
        if destination and destination not in visible.location_id.values:
            st.caption('Destination is outside the current zone/bank filter; choose All zones / All banks to see the move arrow.')
        def select_from_map():
            event = st.session_state.get('interactive_floor', {})
            points = event.get('selection', {}).get('points', [])
            if points:
                item = points[-1].get('customdata', [])
                clicked = item[1] if len(item) > 1 else None
                if clicked in ids:
                    st.session_state['floor_machine'] = clicked
        plot(fig, 'interactive_floor', 580, selectable=True, on_select=select_from_map)
    with detail_col:
        st.markdown(f'### ♠ {selected}')
        st.caption(str(m.get('theme', 'No evidence')))
        category = machine_category(m) if pd.notna(m.get('active_days')) else 'No evidence in period'
        st.write(category)
        st.metric('Expected / available hour', money(m.get('expected_per_available_hour', np.nan)))
        st.metric('Availability', f'{m.availability_rate:.1%}' if pd.notna(m.get('availability_rate')) else '—')
        st.metric('Payout screening score', f'{m.standardized_gap:.2f}' if pd.notna(m.get('standardized_gap')) else '—')
        st.caption('The screening score is a clue, not a confirmed fault. Peer comparisons do not prove a location effect.')
    if not planning:
        st.info('Switch to Plan July actions to highlight a move, replacement, inspection or manufacturer sweep and compare its costs and uncertainty.')
        return
    st.subheader('30-day action comparison')
    if result is None:
        st.info('Keep in place · $0 incremental cost and $0 incremental benefit. This is a neutral reference, not a negative outcome.')
        return
    metrics = st.columns(4)
    metrics[0].metric('Cash cost', money(result['cost']))
    metrics[1].metric('Expected net benefit', money(result['expected_net']))
    metrics[2].metric('10th–90th percentile', f'{money(result["p10"])} to {money(result["p90"])}')
    metrics[3].metric('Chance positive', f'{result["probability_positive"]:.0%}')
    st.caption(f'{len(affected)} machine(s) in scope · {result["lead_days"]}-day lead time · {result["benefit_days"]} benefit days · {money(result["additional_theo_cost"])} planned downtime opportunity cost.')
    st.write(result['assumption'])
    if result['action_type'] == 'A-INSPECT':
        st.info('Inspection buys information. A negative modeled cash return does not price the value of finding a verified issue.')
    elif result['expected_net'] <= 0:
        st.warning('Under these assumptions, this action does not beat keeping the budget over 30 days.')
    else:
        st.success('Positive modeled benefit under these assumptions. Test against a predefined comparison group before claiming success.')
    fig = px.histogram(x=result['net'], nbins=35, color_discrete_sequence=[TEAL], labels={'x': 'Modeled incremental net benefit ($)'})
    fig.add_vline(x=0, line_color=GOLD, line_dash='dash')
    plot(fig, 'floor_scenario_distribution', 270)
    st.write('**Measurement plan:** record the action date and planned downtime; compare expected earnings per scheduled hour and availability with matched untreated machines. Check total floor play for displacement. For inspection, verify configuration and meter reconciliation first.')
    row = {k: v for k, v in result.items() if k not in ['net', 'targets']}
    row.update(machine_id=selected, destination_slot=destination, affected_machines=';'.join(affected))
    st.download_button('Download this action and assumptions', pd.DataFrame([row]).to_csv(index=False).encode(), 'aceiq_floor_action.csv', 'text/csv', key='download_floor_action')


def render_decision(report, daily, machines, property_daily, predictions, locations, placements, walkways, start_date, end_date):
    st.title('Put the $100,000 on evidence.')
    st.write('Explore the floor, compare actions, and make the assumptions visible.')
    engine = DecisionEngine(daily, machines, property_daily, report, predictions)
    floor_tab, portfolio_tab, evidence_tab = st.tabs(['♠ Floor map & simulator', 'Portfolio ranking', 'Assumptions & evidence'])
    with floor_tab:
        render_floor(engine, daily, machines, locations, placements, walkways, start_date, end_date)
    with portfolio_tab:
        st.subheader('Compare the original nine action candidates')
        st.caption('Same scenario engine as the floor map, using default assumptions and the full evidence period. Custom map actions are exploratory and are not automatically added to this shortlist.')
        candidates = engine.shortlist(report['simulation']['candidates'])
        a, b, c = st.columns(3)
        budget = a.slider('Maximum spending limit', 0, 100000, 100000, 1000, key='portfolio_budget', format='$%d')
        goal = b.selectbox('Rank plans by', ['Expected net benefit', '10th percentile', 'Stress case'], key='portfolio_goal')
        sensitivity = c.slider('Operating-benefit multiplier', 0., 2., 1., .1, key='portfolio_multiplier')
        plans = rank_portfolios(candidates, budget, sensitivity).sort_values([goal, 'Cost'], ascending=[False, True])
        best = plans.iloc[0]
        st.markdown('### ' + best.Actions)
        cols = st.columns(3)
        cols[0].metric('Budget committed', money(best.Cost)); cols[1].metric('Expected net benefit', money(best['Expected net benefit']))
        cols[2].metric('10th-percentile outcome', money(best['10th percentile']))
        st.caption('Up to three action types; excludes overlapping machine targets and conflicting comp policies. The stress case is an assumed adverse case, not a mathematical lower bound.')
        if best.Actions == 'Keep budget':
            st.info('No shortlisted spending plan beats keeping the budget for this objective and these assumptions. Learning value and benefits beyond 30 days are not priced.')
        top = plans.head(10).sort_values(goal)
        fig = px.bar(top, x=goal, y='Actions', orientation='h', color_discrete_sequence=[TEAL])
        plot(fig, 'portfolio_rankings', 410)
        with st.expander(f'All {len(plans)} feasible plans'):
            st.dataframe(plans, hide_index=True, width='stretch')
        st.download_button('Download portfolio comparison', plans.to_csv(index=False).encode(), 'aceiq_portfolios.csv', 'text/csv', key='download_portfolios')
    with evidence_tab:
        st.subheader('What changed in this version?')
        st.write('The new demand model supplies the July baseline. Both simulator and portfolio ranking now use the same engine, prices, lead times, machine eligibility and manufacturer-wide maintenance scope. Legacy notebook results are retained as the earlier model version, not silently relabeled.')
        st.write('Move uplift is a visible assumption; observed zone demand is not treated as a causal multiplier. The map permits empty-slot moves only. The portfolio move remains exploratory until a destination is selected and operational feasibility checked.')
        table = pd.DataFrame([{k: v for k, v in c.items() if k not in ['net', 'targets']} for c in candidates])
        st.dataframe(table[['id', 'target', 'cost', 'lead_days', 'benefit_days', 'expected_net', 'assumption']], hide_index=True, width='stretch')
        st.dataframe(pd.DataFrame(report['action_catalog']), hide_index=True, width='stretch')
        st.caption('Costs are catalog costs. Expected earnings are before baseline operating costs; action net benefit subtracts action costs and planned downtime opportunity. No Gemini integration is included in this update.')
