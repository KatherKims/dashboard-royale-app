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
