"""Regression journeys for dates, forecasts, the floor map and interventions."""
from pathlib import Path
import datetime
import sys
from streamlit.testing.v1 import AppTest
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
at = AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()

def clean(label):
    assert not at.exception, [(e.message, e.stack_trace) for e in at.exception]
    print('PASS:', label, flush=True)

clean('Overview and floor prediction')
at.selectbox(key='forecast_level').set_value('Machine').run()
at.selectbox(key='forecast_target_Machine').set_value('M-5076').run()
clean('New machine prediction fallback and missing calibration')
at.selectbox(key='forecast_phase').set_value('July forecast').run()
clean('July forecast has no fabricated actuals')
at.sidebar.date_input[0].set_value((datetime.date(2025,6,1),)).run()
clean('Incomplete date range')
at.sidebar.date_input[0].set_value((datetime.date(2025,6,1),datetime.date(2025,6,30))).run()
clean('June evidence period')
at.sidebar.radio[0].set_value('Machine investigation').run()
clean('Machine investigation')
at.selectbox(key='investigation_bank').set_value('B-01').run()
clean('Bank drilldown')
at.sidebar.radio[0].set_value('$100,000 decision lab').run()
clean('Coordinate floor map and portfolio ranking')
at.radio(key='floor_mode').set_value('Plan July actions').run()
clean('July floor occupancy')
at.selectbox(key='floor_machine').set_value('M-5076').run()
for action in ['Inspect configuration & meters','Move to an empty slot','Lease / replace machine','Manufacturer maintenance sweep','Keep in place']:
    at.selectbox(key='floor_action').set_value(action).run()
    clean(action)
at.selectbox(key='floor_action').set_value('Move to an empty slot').run()
at.slider(key='move_percent').set_value(-10).run()
clean('Boundary uplift slider')
at.slider(key='portfolio_budget').set_value(0).run()
clean('Zero-budget portfolio')
at.slider(key='portfolio_budget').set_value(100000).run()
at.slider(key='portfolio_multiplier').set_value(2.).run()
at.selectbox(key='portfolio_goal').set_value('Stress case').run()
clean('Portfolio assumptions and stress objective')
at.selectbox(key='map_zone').select_index(1).run()
at.selectbox(key='map_bank').select_index(1).run()
clean('Floor zone and bank filters')
print('All interactive regression journeys passed.', flush=True)

