"""Actual HTTP counterexamples from existing scenarios; partial execution only."""
import datetime as dt
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
L = ROOT / 'tests/delivery-acceptance'
R = L / 'runs/independent-covered-probes-20261008'
sys.path.insert(0, '/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts')
import playbook as pb

run = pb.read_json(R / 'run.json')
assert not run['results'], 'Do not overwrite an executed run'
assert all(pb.digest(L / name) == value for name, value in run['ledger_hashes'].items())
evidence = R / 'evidence'
evidence.mkdir(exist_ok=True)
trace = []
client = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

def request(path, method='GET', data=None):
    req = Request(base + path, method=method,
                  data=None if data is None else json.dumps(data).encode(),
                  headers={'Content-Type': 'application/json', 'X-Meeting-App': '1', 'Origin': base})
    try:
        response = client.open(req, timeout=10)
    except HTTPError as err:
        response = err
    with response:
        status, body = response.status, json.load(response)
    # Never save input credentials or Cookie / Set-Cookie headers.
    trace.append({'path': path, 'method': method, 'status': status, 'body': body})
    return status, body

def snapshot(db):
    with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as conn:
        return {'bookings': conn.execute('SELECT id,room_id,user_id,title,start,end,attendees,status,cancelled_at FROM bookings ORDER BY id').fetchall(),
                'notifications': conn.execute('SELECT id,user_id,booking_id,message,read FROM notifications ORDER BY id').fetchall()}

with tempfile.TemporaryDirectory(dir=R, prefix='isolated-') as tmp:
    copy = Path(tmp)
    shutil.copytree(ROOT / 'app', copy / 'app', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT / 'web', copy / 'web')
    source_hashes = {f: pb.digest(copy / f) for f in ('app/server.py', 'app/__init__.py', 'web/app.js', 'web/index.html', 'web/style.css')}
    assert all(v == pb.digest(ROOT / f) for f, v in source_hashes.items())
    db = copy / 'probe.sqlite'
    with (evidence / 'server.log').open('w') as log:
        proc = subprocess.Popen([sys.executable, '-m', 'app.server', '--host', '127.0.0.1', '--port', '0', '--db', str(db)],
                                cwd=copy, stdout=subprocess.PIPE, stderr=log, text=True,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        try:
            line = proc.stdout.readline()
            match = re.search(r'http://127.0.0.1:\d+', line)
            if not match:
                raise RuntimeError('Isolated server failed to start')
            base = match.group()
            assert request('/api/health')[1]['status'] == 'ok'
            assert request('/api/login', 'POST', {'email': 'admin@meetspace.test', 'password': 'MeetSpace!2026'})[0] == 200
            identity = request('/api/session')[1]['user']
            assert identity['role'] == 'admin' and identity['team_id'] == 1

            empty_status, empty = request('/api/rooms?date=')
            default_status, default = request('/api/rooms')
            malformed_status, _ = request('/api/rooms?date=not-a-date')
            date_finding = {'scenario_id': 'BB-room-discovery-2', 'method_id': 'AI-room-discovery-2',
                            'sub_branch': '显式空日期与省略参数/非法日期对照',
                            'expected': '显式空字符串拒绝，只有参数省略才回退今天',
                            'actual': {'empty_status': empty_status, 'default_status': default_status,
                                       'empty_date': empty.get('date'), 'default_date': default.get('date'),
                                       'same_result': empty == default, 'malformed_status': malformed_status},
                            'failed': empty_status < 400}

            room_status, room = request('/api/rooms', 'POST', {'name': '独立审查精度探针', 'location': '隔离测试', 'capacity': 8, 'equipment': [], 'active': True})
            assert room_status == 201
            shanghai = ZoneInfo('Asia/Shanghai')
            start = dt.datetime.combine(dt.datetime.now(shanghai).date() + dt.timedelta(days=1), dt.time(10), shanghai)
            end = start + dt.timedelta(hours=1)
            payload = {'room_id': room['room']['id'], 'title': '精度反例', 'attendees': 2,
                       'idempotency_key': 'independent-precision', 'start': start.isoformat(), 'end': end.isoformat()}
            status, created = request('/api/bookings', 'POST', payload)
            assert status == 201 and created['booking']['replayed'] is False
            before = snapshot(db)
            precision = []
            for field, value in [('start', start), ('end', end)]:
                for delta in [1, -1]:
                    changed = {**payload, field: (value + dt.timedelta(microseconds=delta)).isoformat()}
                    status, body = request('/api/bookings', 'POST', changed)
                    precision.append({'field': field, 'delta_microseconds': delta,
                                      'input': changed[field], 'status': status, 'response': body,
                                      'failed': status < 400, 'persistent_state_unchanged': snapshot(db) == before})
            equal_payload = {**payload, 'start': start.astimezone(dt.timezone.utc).isoformat(), 'end': end.astimezone(dt.timezone.utc).isoformat()}
            eq_status, eq = request('/api/bookings', 'POST', equal_payload)
            assert eq_status == 201 and eq['booking']['replayed'] and eq['booking']['id'] == created['booking']['id']
            precision_finding = {'scenario_id': 'WB-idempotency-absolute-precision', 'method_id': 'AI-WB-idempotency-absolute-precision',
                                 'sub_branch': '已确认且未开始预约，起止各±1微秒；等价UTC对照',
                                 'expected': '每次不同绝对时刻必须拒绝，不返回replayed成功；等价绝对时刻仍重放',
                                 'probes': precision, 'equivalent_control': {'status': eq_status, 'body': eq},
                                 'failed': any(x['failed'] for x in precision)}
        finally:
            proc.terminate()
            proc.wait(timeout=10)

report = {'revision': run['revision'], 'ledger_hashes': run['ledger_hashes'], 'source_sha256': source_hashes,
          'executed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'python': sys.version, 'platform': platform.platform(),
          'scope': '两个既有场景的实际HTTP子分支；实时服务钟而非固定2030时钟。未执行午夜/到期/已开始/取消状态矩阵及浏览器交互，不声称完整方法通过。当前反例不依赖精确时钟边界。',
          'fixtures': '台账内源码隔离副本与新数据库，原文件哈希相同；进程已终止，临时库已清理；会话值仅在内存。',
          'findings': [date_finding, precision_finding], 'http_trace': trace}
pb.write_json(evidence / 'covered-probes.json', report)
findings = {x['scenario_id']: x for x in report['findings']}
run['results'] = []
for s in pb.read_json(L / 'scenarios.json')['items']:
    f = findings.get(s['id'])
    run['results'].append({'scenario_id': s['id'], 'status': 'failed' if f and f['failed'] else 'unproven',
                           'method_ids': [f['method_id']] if f else s['method_ids'],
                           'actual': ('已执行子分支发现反例，见证据；其余矩阵未执行。' if f and f['failed'] else '本轮未执行完整方法，保持未证实。'),
                           'evidence': ['evidence/covered-probes.json', 'evidence/server.log'] if f else []})
run['execution_scope'] = report['scope']
run['dependency_checks'] = []  # Full per-run resource checks and independent evidence review remain pending.
pb.write_json(R / 'run.json', run)
print(json.dumps({'executed_subbranches': len(precision) + 1, 'failed_scenarios': [k for k, v in findings.items() if v['failed']], 'full_acceptance': 'not_established'}, ensure_ascii=False))
