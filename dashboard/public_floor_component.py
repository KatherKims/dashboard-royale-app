"""Serve the original SVG simulator through Streamlit's component channel."""
from pathlib import Path
import json
import tempfile
import streamlit as st
import streamlit.components.v1 as components
from dashboard.floor_simulation import FloorSimulation, public

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
STATIC = Path(tempfile.mkdtemp(prefix='aceiq-component-'))
for name in ['floor-world.js','floor-world.css','floor-motion.js','floor-streamlit.js']:
    (STATIC/name).write_bytes((ASSETS/name).read_bytes())
# Fit the same physical map into narrow public browser frames.
js = (STATIC/'floor-world.js').read_text(encoding='utf-8').replace(',.35,6)',',.12,6)')
(STATIC/'floor-world.js').write_text(js,encoding='utf-8')
html = (ASSETS/'floor-world.html').read_text(encoding='utf-8')
for name in ['floor-world.css','floor-motion.js','floor-world.js']:
    html = html.replace('/'+name, './'+name)
html = html.replace('<script defer src="./floor-motion.js">', '<script src="./floor-streamlit.js"></script><script defer src="./floor-motion.js">')
html = html.replace('href="http://127.0.0.1:8501/"', 'href="/?page=Overview" target="_top"')
(STATIC/'index.html').write_text(html,encoding='utf-8')
floor_component = components.declare_component('aceiq_public_simulator', path=str(STATIC))


def dispatch(simulation, request):
    if not isinstance(request,dict) or len(json.dumps(request)) > 65536:
        raise ValueError('Invalid or oversized request.')
    route, payload = request.get('route'), request.get('payload')
    fields={'evaluate':{'plan'},'preview':{'plan','action'},'confirm':{'plan','action','estimate_id'},
            'undo':{'plan','action_id'},'suggestions':{'plan'}}
    if route not in fields or not isinstance(payload,dict) or set(payload)!=fields[route]:
        raise ValueError('Unsupported request fields.')
    return public(getattr(simulation,route)(**payload))


def render_public_floor(bundle):
    st.caption('Public interactive simulation · Drag machines to move or swap; Manage opens actions, suggestions and exports. Press Play to advance July. Walking guests and rooms are decorative; financial outcomes use the shared model.')
    if 'svg_floor_engine' not in st.session_state:
        st.session_state.svg_floor_engine=FloorSimulation(bundle)
        st.session_state.svg_floor_bootstrap=st.session_state.svg_floor_engine.bootstrap()
    request=floor_component(bootstrap=st.session_state.svg_floor_bootstrap,
                            response=st.session_state.get('svg_floor_response'),
                            key='public_svg_floor',default=None)
    previous=st.session_state.get('svg_floor_response') or {}
    if request and request.get('id')!=previous.get('id'):
        response={'id':request.get('id')}
        try:
            response.update(ok=True,data=dispatch(st.session_state.svg_floor_engine,request))
        except (ValueError,KeyError,TypeError) as exc:
            response.update(ok=False,data={'error':str(exc)})
        st.session_state.svg_floor_response=response
        st.rerun()
    st.caption('Synthetic data. July outcomes are modeled, not observed. Plans reset on reload; export from Manage → Plan. The same budget, action limits, uncertainty and activation rules apply as in the local simulator.')
