from pathlib import Path
import sys
from datetime import date
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
app=AppTest.from_file(str(root/'app.py'),default_timeout=60)
for page in ['Overview','Machines','Guests','Scenarios']:
    app.query_params['page']=page
    app.run()
    assert not app.exception, [x.message for x in app.exception]
    print('PASS page:',page)
    if page=='Guests':
        app.selectbox(key='guest_region').set_value('Domestic').run()
        assert not app.exception
    if page=='Scenarios':
        app.number_input(key='budget').set_value(0).run()
        assert not app.exception
        assert any('Keep budget' in str(x.value) for x in app.markdown)
app.query_params['page']='Machines';app.run()
app.date_input(key='evidence_dates').set_value((date(2025,6,1),)).run()
assert not app.exception
assert len(app.info)>0
app.date_input(key='evidence_dates').set_value((date(2025,6,1),date(2025,6,30))).run()
assert not app.exception
print('PASS: complete and incomplete date selections, guest region, zero-budget keep option')

# Inspect the actual rendered bar coordinates, not just the absence of errors.
import json
import base64
import numpy as np
from dashboard.data_bundle import load_bundle
from dashboard.analytics import machine_summary
data=load_bundle()
full=machine_summary(data['daily'],data['machines'])
app=AppTest.from_file(str(root/'app.py'),default_timeout=60).run()
for label,column in [('Total actual earnings','actual_house_win'),('Actual earnings per active day','actual_per_active_day'),('Expected earnings per available hour','expected_per_available_hour')]:
    app.selectbox(key='bottom_ranking').set_value(label).run()
    assert not app.exception
    spec=json.loads(next(x.proto.spec for x in app.get('plotly_chart') if x.proto.id.endswith('-bottom_ten')))
    assert set(spec['data'][0]['y'])==set(full.sort_values([column,'machine_id']).head(10).machine_id)
app.button(key='evidence_claw').click().run()
assert app.session_state['claw_pick'] in set(full.sort_values(['actual_house_win','machine_id']).head(10).machine_id)
assert not app.exception
day=data['daily'].sort_values('house_win_usd').iloc[0].gaming_date.date()
app.selectbox(key='bottom_ranking').set_value('Total actual earnings').run()
app.date_input(key='evidence_dates').set_value((day,day)).run()
assert not app.exception
spec=json.loads(next(x.proto.spec for x in app.get('plotly_chart') if x.proto.id.endswith('-bottom_ten')))
encoded=spec['data'][0]['x']
xs=np.frombuffer(base64.b64decode(encoded['bdata']),dtype=encoded['dtype']) if isinstance(encoded,dict) else np.asarray(encoded)
assert xs.min()<0
assert spec['layout']['xaxis']['range'][0]<=xs.min()
try:
    app.session_state['claw_pick']
    raise AssertionError('Date change retained a stale claw selection')
except KeyError:
    pass
print('PASS: three ranking modes, reference claw pool, date reset and visible negative chart values')
