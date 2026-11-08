"""Local-only, stateless floor API. No files, plans or credentials are written."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
import json
from urllib.parse import urlsplit
from dashboard.data_bundle import load_bundle
from dashboard.floor_simulation import FloorSimulation, public

ROOT = Path(__file__).resolve().parents[1]

def create_server(port=8502):
    simulation = FloorSimulation(load_bundle())
    lock = RLock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, body, mime='application/json'):
            if not isinstance(body,bytes):
                body=json.dumps(body,allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers(); self.wfile.write(body)

        def trusted_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{port}',f'localhost:{port}'}

        def do_GET(self):
            if not self.trusted_host():
                return self.send(403,{'error':'Localhost only.'})
            path=urlsplit(self.path).path
            files={'/floor-lab':('floor-world.html','text/html'),
                   '/floor-motion.js':('floor-motion.js','text/javascript'),
                   '/floor-world.js':('floor-world.js','text/javascript'),
                   '/floor-world.css':('floor-world.css','text/css')}
            if path in files:
                filename,mime=files[path]
                return self.send(200,(ROOT/'assets'/filename).read_bytes(),mime)
            if path=='/api/bootstrap':
                with lock: return self.send(200,simulation.bootstrap())
            if path=='/health': return self.send(200,{'ok':True,'service':'aceiq-floor'})
            return self.send(404,{'error':'Not found'})

        def do_POST(self):
            if not self.trusted_host() or self.headers.get('Origin') not in {f'http://127.0.0.1:{port}',f'http://localhost:{port}'}:
                return self.send(403,{'error':'Same-origin local requests only.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.send(415,{'error':'Use application/json.'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536: raise ValueError('Payload must be 1–65,536 bytes.')
                def invalid_constant(value): raise ValueError('Non-finite JSON is not allowed.')
                data=json.loads(self.rfile.read(length),parse_constant=invalid_constant)
                if not isinstance(data,dict): raise ValueError('Request must be an object.')
                route=urlsplit(self.path).path
                fields={'/api/evaluate':{'plan'},'/api/preview':{'plan','action'},
                        '/api/confirm':{'plan','action','estimate_id'},'/api/undo':{'plan','action_id'},
                        '/api/suggestions':{'plan'}}
                if route not in fields: return self.send(404,{'error':'Not found'})
                if set(data)!=fields[route]: raise ValueError('Missing or unexpected request fields.')
                with lock:
                    method={'/api/evaluate':simulation.evaluate,'/api/preview':simulation.preview,
                            '/api/confirm':simulation.confirm,'/api/undo':simulation.undo,
                            '/api/suggestions':simulation.suggestions}[route]
                    result=method(**data)
                return self.send(200,public(result))
            except (ValueError,KeyError,TypeError) as exc:
                return self.send(400,{'error':str(exc)})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)

if __name__=='__main__':
    print('The Gilded Ace floor: http://127.0.0.1:8502/floor-lab',flush=True)
    create_server().serve_forever()
