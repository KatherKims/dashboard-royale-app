"""Streamlit-hosted floor controls using the unchanged shared simulation engine."""
import json
import uuid
import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.floor_simulation import FloorSimulation


def render_floor(bundle):
    st.header('Floor Lab')
    st.caption('Public edition: use the controls to plan changes on the supplied floor coordinates. The local SVG edition also supports drag-and-drop and decorative walking guests.')
    sim = FloorSimulation(bundle)
    st.session_state.setdefault('public_floor_plan', [])
    plan = st.session_state.public_floor_plan
    result = sim.evaluate(plan)
    day = st.slider('July simulation day', 1, 30, 30, key='floor_day')
    row = result['days'][day-1]
    for col, label, value in zip(st.columns(3), ['Committed cash', 'Day 30 expected incremental net', 'Day 30 10th–90th percentile'],
            [f"${result['cash_committed']:,.0f}", f"${result['summary']['mean']:,.0f}", f"${result['summary']['p10']:,.0f} to ${result['summary']['p90']:,.0f}"]):
        col.metric(label, value)
    mode = st.radio('Map layout', ['Proposed', 'Baseline'], horizontal=True)
    layout = row['layout'] if mode == 'Proposed' else sim.initial
    slots = bundle['slots'].copy()
    slots['machine'] = slots.location_id.map(layout).fillna('Vacant')
    slots['status'] = ['Vacant' if m == 'Vacant' else 'Changed' if sim.initial.get(s) != m else 'Original'
                       for s,m in zip(slots.location_id, slots.machine)]
    fig = px.scatter(slots, x='x_m', y='y_m', color='status', symbol_sequence=['square'],
                     hover_data=['location_id','machine','bank_id','zone_id'],
                     color_discrete_map={'Original':'#e4bd75','Changed':'#75c9b9','Vacant':'#687b73'})
    fig.update_traces(marker=dict(size=11, symbol='square', line=dict(width=1,color='#0b231f')))
    fig.update_layout(height=500, paper_bgcolor='#0b231f', plot_bgcolor='#0b231f',font_color='#f6eacb')
    fig.update_yaxes(scaleanchor='x',scaleratio=1)
    st.plotly_chart(fig, width='stretch', key='public_floor_map')
    st.caption('Colors show occupancy/placement changes. Inspection, lease and maintenance actions are listed in the plan below. These estimates are conditional assumptions, not guaranteed returns or destination-specific causal effects.')
    eligible = sorted(sim.eligible)
    kind = st.selectbox('Action', ['move','swap','inspect','lease','maintenance','add','remove'],key='floor_kind')
    action = {'id':'public-preview','kind':kind}
    if kind == 'maintenance':
        action['target'] = st.selectbox('Manufacturer',sorted(sim.engine.eligible.manufacturer.unique()))
    else:
        action['proxy' if kind == 'add' else 'target'] = st.selectbox('Performance proxy' if kind == 'add' else 'Machine',eligible,key='floor_target')
    if kind == 'swap':
        action['other'] = st.selectbox('Swap with',[m for m in eligible if m != action['target']])
    if kind in ['move','add']:
        action['destination'] = st.selectbox('Destination slot',sorted(sim.slots.index, key=lambda slot: (slot in sim.initial, slot)))
        st.caption('Choose a vacant slot, or one freed by a removal before activation. The engine validates your selection.')
    if kind in ['add','remove']:
        st.warning('What-if extension: enter assumptions; these effects are not learned from intervention outcomes.')
        action['cash'] = st.number_input('July cash cost',0.0,100000.0,0.0)
        action['day'] = st.number_input('Activation day',1,30,3)
        action['share'] = st.slider('Incremental play share' if kind == 'add' else 'Play retained elsewhere',0.0,1.0,0.5)
    else:
        action['retained'] = st.slider('Play retained during planned downtime',0.1,1.0,0.5)
    try:
        preview = sim.preview(plan,action)
        st.info(f"Preview: additional cash ${preview['additional_cash']:,.0f}; marginal expected net ${preview['marginal']['mean']:,.0f}; 10th–90th percentile ${preview['marginal']['p10']:,.0f} to ${preview['marginal']['p90']:,.0f}.")
        if st.button('Confirm action',key='floor_confirm'):
            confirmed = sim.confirm(plan,action,preview['estimate_id'])
            updated = confirmed['plan']
            updated[-1]['id'] = 'public-'+uuid.uuid4().hex[:12]
            sim.validate(updated)
            st.session_state.public_floor_plan = updated
            st.rerun()
    except ValueError as exc:
        st.info(str(exc))
    if plan:
        st.dataframe(pd.DataFrame(result['actions']).drop(columns=['targets'],errors='ignore'),width='stretch')
        if st.button('Undo last action',key='floor_undo'):
            st.session_state.public_floor_plan = sim.undo(plan,plan[-1]['id'])['plan']
            st.rerun()
    if st.button('Find suggested changes',key='floor_suggest'):
        suggestions = sim.suggestions(plan)
        st.dataframe(pd.json_normalize(suggestions['suggestions']),width='stretch')
        st.caption(suggestions['scope'])
    daily = pd.DataFrame([{k:v for k,v in r.items() if k not in ['layout','activated']} for r in result['days']])
    st.line_chart(daily.set_index('day')[['mean','p10','p90']], x_label='July day', y_label='Cumulative incremental net ($)')
    st.download_button('Download plan JSON',json.dumps(plan,indent=2),'floor-plan.json','application/json')
    st.download_button('Download July estimates',daily.to_csv(index=False),'floor-july.csv','text/csv')
    st.caption('Plans are session-only. Download before closing or refreshing. $100,000 cash limit, catalog quantities, action-type limits and target conflicts use the same shared validator as the local floor.')
