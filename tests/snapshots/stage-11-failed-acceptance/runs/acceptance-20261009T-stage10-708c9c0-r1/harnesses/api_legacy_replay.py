"""Independent old-database replay regression over actual HTTP processes."""
import hashlib
import http.cookiejar
import importlib.util
import json
import subprocess
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError

ROOT = Path('/Users/boboyang/work/sublang.ai/meeting-room-booking')
OUT = Path(__file__).resolve().parents[1] / 'evidence/api-legacy-replay.json'

def load(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def request(client, base, path, method='GET', payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(base + path, data=data, method=method,
                  headers={'Content-Type': 'application/json', 'X-Meeting-App': '1'})
    try:
        response = client.open(req, timeout=10)
    except HTTPError as exc:
        response = exc
    with response:
        return {'status': response.status, 'body': json.loads(response.read())}

def start(module, db):
    server = module.ApplicationServer(('127.0.0.1', 0), module.Store(db))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, 'http://127.0.0.1:' + str(server.server_port)

def stop(server, thread):
    server.shutdown(); server.server_close(); thread.join()

old = subprocess.check_output(['git', 'show', '87b578b:app/server.py'], cwd=ROOT)
new = (ROOT / 'app/server.py').read_bytes()
evidence = {'scope': 'current run old-database compatibility supplement; old source solely migration fixture',
            'old_revision': '87b578b', 'source_sha256': {'old': hashlib.sha256(old).hexdigest(), 'new': hashlib.sha256(new).hexdigest()}, 'checks': []}
def check(name, passed, actual):
    evidence['checks'].append({'assertion': name, 'passed': bool(passed), 'actual': actual})

with tempfile.TemporaryDirectory(dir=OUT.parent) as tmp:
    tmp = Path(tmp); old_file = tmp / 'old_server.py'; old_file.write_bytes(old)
    previous = load('old_server_review', old_file); current = load('new_server_review', ROOT / 'app/server.py')
    db = tmp / 'persisted.sqlite'
    client = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
    day = (datetime.now(previous.SHANGHAI).date() + timedelta(days=2)).isoformat()
    payload = {'room_id': 4, 'title': '旧库重放兼容', 'attendees': 2,
               'start': day+'T10:00:00+08:00', 'end': day+'T11:00:00+08:00', 'idempotency_key': 'reviewer-old-db'}
    server, thread, base = start(previous, db)
    try:
        login = request(client, base, '/api/login', 'POST', {'email': 'alice@meetspace.test', 'password': 'MeetSpace!2026'})
        created = request(client, base, '/api/bookings', 'POST', payload)
        check('旧版本真实HTTP创建成功', login['status'] == 200 and created['status'] == 201, created)
        with server.store.connect() as conn:
            before = [list(row) for row in conn.execute('SELECT id, status, request_hash FROM bookings ORDER BY id')]
            notice_before = conn.execute('SELECT count(*) FROM notifications').fetchone()[0]
    finally:
        stop(server, thread)
    server, thread, base = start(current, db)
    try:
        observed = []
        equivalents = [payload, {**payload, 'title': '  '+payload['title']+'  '},
                       {**payload, 'start': day+'T02:00:00Z', 'end': day+'T03:00:00+00:00'},
                       {**payload, 'start': day+'T10:00:00.000000+08:00', 'end': day+'T11:00:00.000000+08:00'}]
        for body in equivalents:
            response = request(client, base, '/api/bookings', 'POST', body); observed.append(response)
        check('新版本同数据库既有session及四种等价重放', all(r['status']==201 and r['body']['booking']['id']==created['body']['booking']['id'] and r['body']['booking']['replayed'] for r in observed), observed)
        for field in ('start', 'end'):
            response = request(client, base, '/api/bookings', 'POST', {**payload, field: payload[field].replace(':00+08:00', ':00.000001+08:00')})
            check('旧记录'+field+'微秒变化被拒绝', response['status']==409 and response['body']['code']=='idempotency_conflict', response)
        with server.store.connect() as conn:
            after = [list(row) for row in conn.execute('SELECT id, status, request_hash FROM bookings ORDER BY id')]
            notice_after = conn.execute('SELECT count(*) FROM notifications').fetchone()[0]
        check('既有记录哈希未迁移且无重复通知', before==after and notice_before==notice_after, {'before': before, 'after': after, 'notification_counts': [notice_before, notice_after]})
    finally:
        stop(server, thread)
evidence['status'] = 'passed' if all(c['passed'] for c in evidence['checks']) else 'failed'
OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'status': evidence['status'], 'checks': len(evidence['checks']), 'evidence': str(OUT)}))
