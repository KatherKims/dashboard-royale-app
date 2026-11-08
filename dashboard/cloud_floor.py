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
    zone = st.selectbox('Focus area', ['Entire floor'] + sorted(slots.zone_id.unique()),key='floor_zone')
    visible = slots if zone == 'Entire floor' else slots[slots.zone_id == zone]
    map_col, guide_col = st.columns([3,1])
    with map_col:
        fig = px.scatter(visible, x='x_m', y='y_m', color='status',
                         hover_name='machine', hover_data={'location_id':True,'bank_id':True,'zone_id':True,'x_m':False,'y_m':False},
                         color_discrete_map={'Original':'#e4bd75','Changed':'#75c9b9','Vacant':'#d2919e'})
        fig.update_traces(marker=dict(size=7 if zone == 'Entire floor' else 13, symbol='square', line=dict(width=1,color='#0b231f')))
        # Bounds follow the supplied coordinates. Constrain the domains, rather
        # than letting equal-aspect scaling inflate the x range on wide screens.
        for bank, group in visible.groupby('bank_id'):
            x0,x1=group.x_m.min()-1.4,group.x_m.max()+1.4
            y0,y1=group.y_m.min()-1.4,group.y_m.max()+1.4
            fig.add_shape(type='rect',x0=x0,x1=x1,y0=y0,y1=y1,
                          fillcolor='rgba(228,189,117,0.08)',line=dict(color='#426457',width=1),layer='below')
            fig.add_annotation(x=(x0+x1)/2,y=y1+1.2,text=str(bank),showarrow=False,
                               font=dict(size=9,color='#a8bdb2'),yanchor='bottom')
        fig.update_layout(height=650 if zone == 'Entire floor' else 480,
                          margin=dict(l=12,r=12,t=35,b=15),paper_bgcolor='#0b231f',plot_bgcolor='#0b231f',
                          font=dict(color='#f6eacb',family='Consolas, monospace',size=13),
                          legend=dict(title_text='',orientation='h',x=0,y=1.06),dragmode='pan',
                          title=dict(text=f'JULY {day:02d} · {mode.upper()}',font=dict(size=13),x=0.98,xanchor='right'))
        fig.update_xaxes(range=[visible.x_m.min()-7,visible.x_m.max()+7],visible=False,constrain='domain')
        fig.update_yaxes(range=[visible.y_m.min()-7,visible.y_m.max()+7],visible=False,scaleanchor='x',scaleratio=1,constrain='domain')
        st.plotly_chart(fig, width='stretch', key='public_floor_map',config={'displaylogo':False,'scrollZoom':True})
    with guide_col:
        st.subheader('Read the floor')
        st.metric('Occupied slots', int((visible.machine != 'Vacant').sum()))
        st.metric('Vacant slots', int((visible.machine == 'Vacant').sum()))
        st.caption('Gold: original placement. Teal: moved, swapped or added. Pink: vacant.')
        st.markdown('**Explore:** hover over a machine for its ID. Choose a focus area for a closer view. Drag to pan; double-click to reset.')
        st.markdown('**Plan:** use the action controls below. Confirm a preview, then move the July slider to see when the change activates.')
        st.caption('Bank outlines group supplied slots; they are not surveyed walls. Physical coordinates and relative distances are preserved.')
        if not plan:
            st.info('No actions yet. $0 incremental net means no change from the baseline—not zero casino earnings.')
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
