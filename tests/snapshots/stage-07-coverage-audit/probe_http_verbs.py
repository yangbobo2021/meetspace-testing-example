"""Supplemental real HTTP probe; excluded from existing-test coverage data."""
import hashlib
import http.client
import json
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT))
from app.server import ApplicationServer, Store

def snapshot(db):
    with sqlite3.connect(db) as conn:
        return {t: conn.execute(f'SELECT * FROM {t} ORDER BY id').fetchall()
                for t in ('users', 'rooms', 'bookings', 'notifications')}

observations = []
with tempfile.TemporaryDirectory(dir=BASE, prefix='verb-probe-') as tmp:
    db = Path(tmp) / 'synthetic.sqlite'
    server = ApplicationServer(('127.0.0.1', 0), Store(db))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        for actor in ('anonymous', 'alice', 'admin'):
            cookie = ''
            if actor != 'anonymous':
                conn = http.client.HTTPConnection('127.0.0.1', port)
                conn.request('POST', '/api/login', json.dumps({'email': actor+'@meetspace.test', 'password': 'MeetSpace!2026'}),
                             {'Content-Type':'application/json', 'X-Meeting-App':'1', 'Origin':f'http://127.0.0.1:{port}'})
                response = conn.getresponse()
                assert response.status == 200
                cookie = response.getheader('Set-Cookie').split(';', 1)[0]
                response.read(); conn.close()
            for verb in ('DELETE', 'OPTIONS', 'PUT'):
                for path in ('/api/health', '/api/rooms', '/api/bookings', '/api/members', '/api/unknown'):
                    before = snapshot(db)
                    conn = http.client.HTTPConnection('127.0.0.1', port)
                    conn.request(verb, path, '{}', {'Content-Type':'application/json', 'X-Meeting-App':'1',
                                                  'Origin':f'http://127.0.0.1:{port}', 'Cookie':cookie})
                    response = conn.getresponse(); body = response.read().decode(); conn.close()
                    try:
                        data = json.loads(body)
                        stable_error = isinstance(data, dict) and 'error' in data and 'code' in data
                    except ValueError:
                        stable_error = False
                    observations.append({'actor':actor, 'verb':verb, 'path':path, 'status':response.status,
                                         'content_type':response.getheader('Content-Type'),
                                         'stable_json_error':stable_error, 'business_state_unchanged':before==snapshot(db)})
    finally:
        server.shutdown(); server.server_close(); thread.join()

report = {'scope':'新增缺口诊断探针；不进入原有测试覆盖率分子，也不构成独立验收审阅',
          'source_sha256':hashlib.sha256((ROOT/'app/server.py').read_bytes()).hexdigest(),
          'observations':observations}
(BASE/'supplemental-http-verbs.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'probes':len(observations), 'stable_json_errors':sum(x['stable_json_error'] for x in observations),
                  'unchanged':all(x['business_state_unchanged'] for x in observations)}))
