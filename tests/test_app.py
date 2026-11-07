from pathlib import Path
import faulthandler
faulthandler.dump_traceback_later(50,exit=True)
from streamlit.testing.v1 import AppTest
app=Path(__file__).parents[1]/'app.py'
at=AppTest.from_file(str(app),default_timeout=60).run()
print('Overview rendered',flush=True)
assert not at.exception,at.exception
for page in ['Machine investigation','$100,000 decision lab']:
    at.sidebar.radio[0].set_value(page).run()
    print(page,flush=True)
    assert not at.exception,at.exception
    if page=='Machine investigation':
        for ranking in ['Actual earnings per active day','Expected earnings per available hour']:
            at.radio[0].set_value(ranking).run()
            assert not at.exception,at.exception
        at.selectbox[0].set_value('M-5076').run()
        assert not at.exception,at.exception
    else:
        for goal in ['10th-percentile outcome','Conservative assumptions']:
            at.radio[0].set_value(goal).run()
            assert not at.exception,at.exception
        at.slider[0].set_value(0).run()
        assert not at.exception,at.exception
        at.slider[0].set_value(100000).run()
        at.slider[1].set_value(2.0).run()
        assert not at.exception,at.exception
        for option_index in range(min(3,len(at.selectbox[0].options))):
            at.selectbox[0].select_index(option_index).run()
            assert not at.exception,at.exception
print('PASS: all pages, rankings, machine selection, objectives, zero budget and sensitivity.')
faulthandler.cancel_dump_traceback_later()

