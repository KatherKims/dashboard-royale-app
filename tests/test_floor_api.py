"""Exercise the real HTTP boundary on a temporary localhost port."""
import json
from pathlib import Path
import socket
import sys
import threading
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.floor_server import create_server

class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
        cls.server=create_server(cls.port);threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url=f'http://127.0.0.1:{cls.port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def post(self,path,data,origin=None):
        request=Request(self.url+path,json.dumps(data).encode(),{'Content-Type':'application/json','Origin':origin or self.url})
        try:
            with urlopen(request) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def test_stateless_preview_confirm(self):
        bootstrap=json.load(urlopen(self.url+'/api/bootstrap'))
        vacant=next(s['location_id'] for s in bootstrap['slots'] if not s['machine_id'])
        action={'id':'api-move','kind':'move','target':bootstrap['eligible'][0],'destination':vacant}
        status,p=self.post('/api/preview',{'plan':[],'action':action});self.assertEqual(status,200)
        self.assertEqual(json.load(urlopen(self.url+'/api/bootstrap'))['result']['plan'],[])
        status,c=self.post('/api/confirm',{'plan':[],'action':action,'estimate_id':p['estimate_id']})
        self.assertEqual(status,200);self.assertEqual(c['plan'],p['plan'])
        self.assertEqual(self.post('/api/confirm',{'plan':[],'action':action,'estimate_id':'stale'})[0],400)
    def test_boundary(self):
        self.assertEqual(self.post('/api/evaluate',{'plan':[]},'https://example.com')[0],403)
        self.assertEqual(self.post('/api/evaluate',{'plan':[],'extra':1})[0],400)
        self.assertEqual(self.post('/api/evaluate',{'plan':{}})[0],400)
        self.assertEqual(self.post('/api/unknown',{'plan':[]})[0],404)
        req=Request(self.url+'/api/evaluate',b'{}',{'Content-Type':'text/plain','Origin':self.url})
        with self.assertRaises(HTTPError) as exc:urlopen(req)
        self.assertEqual(exc.exception.code,415)
        req=Request(self.url+'/api/bootstrap',headers={'Host':'malicious.example'})
        with self.assertRaises(HTTPError) as exc:urlopen(req)
        self.assertEqual(exc.exception.code,403)

if __name__=='__main__':unittest.main()
