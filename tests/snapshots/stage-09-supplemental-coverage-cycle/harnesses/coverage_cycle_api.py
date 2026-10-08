"""Real HTTP/SQLite/CLI supplemental acceptance; faults only at dependency boundaries."""
import argparse
import ast
import contextlib
import hashlib
import http.client
import importlib.util
import inspect
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import socketserver
import sqlite3
import subprocess
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'tests/delivery-acceptance/coverage-audits/coverage-20261009-stage08-r1'
PROJECTS = BASE / 'api-projects'
ARTIFACTS = BASE / 'api-evidence'
FIXED = datetime.fromisoformat('2030-04-10T09:00:00+08:00')
REAL_CONNECT = sqlite3.connect
REAL_WRITE = socketserver._SocketWriter.write
ARMED = {}


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED.astimezone(tz) if tz else FIXED.replace(tzinfo=None)


def writer(self, payload):
    port = self._sock.getsockname()[1]
    fixture = ARMED.get(port)
    if fixture and fixture.fault and payload.startswith(b'{'):
        kind = fixture.fault
        fixture.fault = None
        fixture.events.append({'event': 'response_write_fault', 'kind': kind,
                               'stack': [{'function': x.function, 'line': x.lineno,
                                          'file': str(Path(x.filename).relative_to(ROOT)) if str(x.filename).startswith(str(ROOT)) else x.filename}
                                         for x in inspect.stack()[1:7]],
                               'business_snapshot_at_fault': fixture.snapshot(), 'monotonic': time.monotonic()})
        raise {'BrokenPipeError': BrokenPipeError, 'ConnectionResetError': ConnectionResetError}[kind]('synthetic dependency fault')
    return REAL_WRITE(self, payload)


socketserver._SocketWriter.write = writer


def dependency_profile(frame, event, arg):
    if event not in ['call', 'return'] or frame.f_code.co_name not in ['handle_one_request', 'dispatch', 'send_error']:
        return
    handler = frame.f_locals.get('self')
    port = getattr(getattr(handler, 'server', None), 'server_port', None)
    fixture = ARMED.get(port)
    if fixture:
        fixture.calls.append({'event': event, 'function': frame.f_code.co_name, 'line': frame.f_lineno, 'file': frame.f_code.co_filename,
                              'method': getattr(handler, 'command', None),
                              'path': getattr(handler, 'path', None),
                              'error_code': frame.f_locals.get('code'),
                              'error_message': frame.f_locals.get('message')})


threading.setprofile(dependency_profile)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def snapshot(path):
    with REAL_CONNECT(path) as db:
        db.row_factory = sqlite3.Row
        return {name: [dict(x) for x in db.execute(sql)] for name, sql in {
            'teams': 'SELECT * FROM teams ORDER BY id',
            'users': 'SELECT id,team_id,email,name,role FROM users ORDER BY id',
            'rooms': 'SELECT * FROM rooms ORDER BY id',
            'bookings': 'SELECT * FROM bookings ORDER BY id',
            'notifications': 'SELECT * FROM notifications ORDER BY id'}.items()}


def request(port, method, path, data=None, cookie=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=6)
    headers = {'Content-Type': 'application/json', 'X-Meeting-App': '1', 'Origin': f'http://127.0.0.1:{port}'}
    if cookie:
        headers['Cookie'] = cookie
    body = json.dumps(data).encode() if data is not None else None
    try:
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        raw = response.read()
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            parsed = None
        result = {'status': response.status, 'content_type': response.getheader('Content-Type'),
                  'json': parsed, 'body_excerpt': raw.decode(errors='replace')[:500] if parsed is None else None}
        new_cookie = response.getheader('Set-Cookie')
        return result, new_cookie.split(';', 1)[0] if new_cookie else None
    except (http.client.HTTPException, OSError) as exc:
        return {'status': None, 'transport_error': type(exc).__name__}, None
    finally:
        connection.close()


class Fixture:
    def __init__(self, name):
        self.name = name
        self.directory = PROJECTS / (name + '-' + str(time.time_ns()))
        self.directory.mkdir(parents=True, exist_ok=False)
        shutil.copytree(ROOT / 'app', self.directory / 'app', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT / 'web', self.directory / 'web')
        self.db = self.directory / 'fixture.sqlite'
        self.events = []
        self.calls = []
        self.fault = None
        self.storage_fault = False
        spec = importlib.util.spec_from_file_location('acceptance_' + name.replace('-', '_'), self.directory / 'app/server.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.module.datetime = Clock
        owner = self

        class Connection(sqlite3.Connection):
            def execute(self, sql, parameters=()):
                cursor = super().execute(sql, parameters)
                if owner.storage_fault and sql.lstrip().startswith('INSERT INTO notifications'):
                    owner.storage_fault = False
                    owner.events.append({'event': 'notification_DML_returned_then_dependency_failure',
                                         'booking_count_in_transaction': super().execute('SELECT count(*) FROM bookings').fetchone()[0],
                                         'notification_count_in_transaction': super().execute('SELECT count(*) FROM notifications').fetchone()[0],
                                         'monotonic': time.monotonic()})
                    raise sqlite3.OperationalError('verified synthetic storage dependency failure after DML')
                return cursor

            def commit(self):
                super().commit()
                owner.events.append({'event': 'actual_commit_returned', 'monotonic': time.monotonic()})

            def rollback(self):
                super().rollback()
                owner.events.append({'event': 'actual_rollback_returned', 'monotonic': time.monotonic()})

        def connect(*args, **kwargs):
            kwargs['factory'] = Connection
            return REAL_CONNECT(*args, **kwargs)

        self.module.sqlite3 = SimpleNamespace(connect=connect, Row=sqlite3.Row,
                                              IntegrityError=sqlite3.IntegrityError,
                                              OperationalError=sqlite3.OperationalError)
        self.server = self.module.ApplicationServer(('127.0.0.1', 0), self.module.Store(self.db))
        self.port = self.server.server_port
        self.server_errors = []
        def handle_error(req, addr):
            self.server_errors.append({'event': 'request_thread_error', 'type': __import__('sys').exc_info()[0].__name__,
                                       'traceback': traceback.format_exc()})
        self.server.handle_error = handle_error
        ARMED[self.port] = self
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.02), daemon=True)
        self.thread.start()

    def login(self, email='alice@meetspace.test'):
        reply, cookie = self.req('POST', '/api/login', {'email': email, 'password': 'MeetSpace!2026'})
        if reply['status'] != 200 or not cookie:
            raise AssertionError({'login_status': reply['status']})
        return cookie

    def req(self, method, path, data=None, cookie=None):
        return request(self.port, method, path, data, cookie)

    def snapshot(self):
        return snapshot(self.db)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        ARMED.pop(self.port, None)


def room_payload(name='补测专用'):
    return {'name': name, 'location': '隔离测试', 'capacity': 8, 'equipment': ['白板'], 'active': True}


def booking_payload(key):
    return {'room_id': 4, 'title': '补测预约', 'start': '2030-04-11T10:00:00+08:00',
            'end': '2030-04-11T11:00:00+08:00', 'attendees': 3, 'idempotency_key': key}


def add_item(items, name, checks, actual):
    items.append({'item': name, 'status': 'passed' if all(checks.values()) else 'failed',
                  'checks': checks, 'actual': actual})


def transport():
    items = []
    for phase in ['success', 'AppError']:
        for kind in ['BrokenPipeError', 'ConnectionResetError']:
            fixture = Fixture(f'transport-{phase}-{kind}')
            try:
                admin = fixture.login('admin@meetspace.test')
                before = fixture.snapshot()
                fixture.events.clear()
                payload = room_payload()
                if phase == 'AppError':
                    payload['capacity'] = 0
                fixture.fault = kind
                loss, _ = fixture.req('POST', '/api/rooms', payload, admin)
                after = fixture.snapshot()
                health, _ = fixture.req('GET', '/api/health')
                session, _ = fixture.req('GET', '/api/session', cookie=admin)
                valid, _ = fixture.req('POST', '/api/rooms', room_payload('恢复对照'), admin)
                error, _ = fixture.req('POST', '/api/rooms', {'name': ''}, admin)
                fault = [e for e in fixture.events if e['event'] == 'response_write_fault']
                app_stack = next((x for x in fault[0]['stack'] if x['function'] == 'dispatch'), {}) if fault else {}
                fault_return = [x for x in fixture.calls if x['event'] == 'return' and x['function'] == 'dispatch' and x['path'] == '/api/rooms']
                add_item(items, f'{phase}/{kind}', {
                    'exact_fault_hit': len(fault) == 1 and fault[0]['kind'] == kind,
                    'send_json_write': bool(fault) and fault[0]['stack'][0]['function'] == 'send_json' and fault[0]['stack'][0]['line'] == 195,
                    'correct_dispatch_phase': app_stack.get('line') == (252 if phase == 'success' else 254),
                    'transport_catch_pass_reached': any(x['line'] == 260 for x in fault_return) if phase == 'success' else not any(x['line'] == 260 for x in fault_return),
                    'client_did_not_receive_complete_response': loss['status'] is None,
                    'commit_or_reject_state': len(after['rooms']) == len(before['rooms']) + 1 if phase == 'success' else after == before,
                    'real_commit_before_write' : any(e['event'] == 'actual_commit_returned' and e['monotonic'] < fault[0]['monotonic'] for e in fixture.events) if phase == 'success' and fault else phase == 'AppError',
                    'server_healthy': health['status'] == 200 and fixture.thread.is_alive(),
                    'session_and_business_recovery': session['status'] == 200 and valid['status'] == 201,
                    'stable_json_error': error['status'] == 400 and bool(error.get('json', {}).get('code'))},
                    {'loss': loss, 'before': before, 'after': after, 'events': fixture.events,
                     'server_errors': fixture.server_errors, 'dispatch_return_trace': fault_return, 'health': health, 'session': session, 'valid': valid, 'error': error})
            finally:
                fixture.close()
    return items


def replay():
    items = []
    variants = {'same': {}, 'different_room_id': {'room_id': 2}, 'different_title': {'title': '另一合法主题'},
                'different_start': {'start': '2030-04-11T10:15:00+08:00'},
                'different_end': {'end': '2030-04-11T11:15:00+08:00'}, 'different_attendees': {'attendees': 4},
                'normalized_trim': {'title': '  补测预约  '},
                'normalized_UTC': {'start': '2030-04-11T02:00:00+00:00', 'end': '2030-04-11T03:00:00+00:00'}}
    for kind in ['BrokenPipeError', 'ConnectionResetError']:
        for label, delta in variants.items():
            fixture = Fixture('booking-loss-' + kind + '-' + label)
            try:
                user = fixture.login()
                body = booking_payload('loss-' + kind + '-' + label)
                before = fixture.snapshot()
                fixture.events.clear()
                fixture.fault = kind
                loss, _ = fixture.req('POST', '/api/bookings', body, user)
                committed = fixture.snapshot()
                existing = [x for x in committed['bookings'] if x['idempotency_key'] == body['idempotency_key']]
                expected_id = existing[0]['id'] if existing else None
                response, _ = fixture.req('POST', '/api/bookings', body, user)
                fault = [e for e in fixture.events if e['event'] == 'response_write_fault']
                checks = {
                    'response_fault_hit_and_client_incomplete': len(fault) == 1 and loss['status'] is None,
                    'commit_precedes_response_fault': bool(fault) and any(e['event'] == 'actual_commit_returned' and e['monotonic'] < fault[0]['monotonic'] for e in fixture.events),
                    'exactly_one_booking_and_notification': len(existing) == 1 and len([n for n in committed['notifications'] if n['booking_id'] == expected_id]) == 1,
                    'same_replay_id': response['status'] == 201 and response['json']['booking']['id'] == expected_id and response['json']['booking']['replayed'] is True,
                    'replay_no_extra_writes': fixture.snapshot() == committed}
                changed_reply = None
                if delta:
                    changed_reply, _ = fixture.req('POST', '/api/bookings', dict(body, **delta), user)
                    if label.startswith('different'):
                        checks['valid_single_dimension_rejected'] = changed_reply['status'] == 409 and changed_reply['json']['code'] == 'idempotency_conflict'
                    else:
                        checks['normalized_replay'] = changed_reply['status'] == 201 and changed_reply['json']['booking']['id'] == expected_id and changed_reply['json']['booking']['replayed'] is True
                    checks['unchanged_after_variation'] = fixture.snapshot() == committed
                add_item(items, kind + '/' + label, checks,
                         {'input': body, 'variation_delta': delta, 'loss': loss, 'before': before, 'committed': committed,
                          'replay': response, 'variation_response': changed_reply, 'events': fixture.events,
                          'source_copy': str(fixture.directory.relative_to(BASE))})
            finally:
                fixture.close()
    fixture = Fixture('booking-storage-before-commit')
    try:
        user = fixture.login()
        before = fixture.snapshot()
        fixture.events.clear()
        fixture.storage_fault = True
        body = booking_payload('precommit-loss')
        failed, _ = fixture.req('POST', '/api/bookings', body, user)
        rolledback = fixture.snapshot()
        initial, _ = fixture.req('POST', '/api/bookings', body, user)
        repeated, _ = fixture.req('POST', '/api/bookings', body, user)
        add_item(items, 'storage_after_DML_before_commit', {
            'actual_dml_and_fault_hit': any(e['event'] == 'notification_DML_returned_then_dependency_failure' for e in fixture.events),
            'actual_rollback_returned': any(e['event'] == 'actual_rollback_returned' for e in fixture.events),
            'no_partial_writes': rolledback == before,
            'real_503': failed['status'] == 503 and failed['json']['code'] == 'storage_unavailable',
            'restored_first_success': initial['status'] == 201 and initial['json']['booking']['replayed'] is False,
            'next_same_id_replay': repeated['status'] == 201 and repeated['json']['booking']['replayed'] is True and repeated['json']['booking']['id'] == initial['json']['booking']['id'],
            'one_notification': len(fixture.snapshot()['notifications']) == len(before['notifications']) + 1},
            {'failed': failed, 'before': before, 'rolled_back': rolledback, 'first': initial, 'replay': repeated, 'events': fixture.events})
    finally:
        fixture.close()
    return items


def unsupported():
    items = []
    for verb in ['DELETE', 'OPTIONS', 'PUT']:
        for identity in ['anonymous', 'member', 'admin', 'revoked']:
            for path in ['/api/health', '/api/rooms', '/api/bookings', '/api/members', '/api/unknown']:
                name = 'verbs-' + verb + '-' + identity + '-' + path.rsplit('/', 1)[-1]
                fixture = Fixture(name)
                try:
                    cookie = None if identity == 'anonymous' else fixture.login('admin@meetspace.test' if identity == 'admin' else 'alice@meetspace.test')
                    revocation = None
                    if identity == 'revoked':
                        revocation, _ = fixture.req('POST', '/api/logout', {}, cookie)
                    session, _ = fixture.req('GET', '/api/session', cookie=cookie)
                    before = fixture.snapshot()
                    fixture.calls.clear()
                    one, _ = fixture.req(verb, path, {'role': 'admin', 'title': '未经授权写入'}, cookie)
                    two, _ = fixture.req(verb, path, {'role': 'admin', 'title': '未经授权写入'}, cookie)
                    inherited_calls = list(fixture.calls)
                    after = fixture.snapshot()
                    valid_json = isinstance(one['json'], dict) and bool(one['json'].get('error')) and bool(one['json'].get('code'))
                    repeated_json = isinstance(two['json'], dict) and bool(two['json'].get('code'))
                    health, _ = fixture.req('GET', '/api/health')
                    admin = fixture.login('admin@meetspace.test')
                    read, _ = fixture.req('GET', '/api/rooms', cookie=admin)
                    write, _ = fixture.req('POST', '/api/rooms', room_payload('恢复对照'), admin)
                    anonymous, _ = fixture.req('GET', '/api/rooms')
                    add_item(items, f'{verb}/{identity}{path}', {
                        'identity_verified': session['status'] == (401 if identity in ['anonymous', 'revoked'] else 200),
                        'unsupported_rejected': one['status'] is not None and one['status'] >= 400,
                        'json_error_code_contract': valid_json,
                        'repeated_code_stable': valid_json and repeated_json and one['json']['code'] == two['json']['code'],
                        'business_unchanged': after == before,
                        'real_inherited_dispatch_trace': len([x for x in inherited_calls if x['event'] == 'call' and x['function'] == 'handle_one_request']) == 2 and len([x for x in inherited_calls if x['event'] == 'call' and x['function'] == 'send_error' and x['error_code'] == 501]) == 2 and not any(x['function'] == 'dispatch' for x in inherited_calls),
                        'no_internal_exception_or_password_leak': 'Traceback' not in (one['body_excerpt'] or '') and 'MeetSpace!2026' not in (one['body_excerpt'] or ''),
                        'supported_recovery': health['status'] == 200 and read['status'] == 200 and write['status'] == 201 and anonymous['status'] == 401},
                        {'request': {'method': verb, 'path': path, 'identity': identity}, 'identity_status': session['status'],
                         'revocation_status': revocation['status'] if revocation else None,
                         'first': one, 'repeat': two, 'snapshot_before_hash': digest(before), 'snapshot_after_hash': digest(after),
                         'before': before, 'after': after,
                         'dispatch_observation': inherited_calls,
                         'recovery': {'health': health['status'], 'read': read['status'], 'write': write['status'], 'anonymous': anonymous['status']}})
                finally:
                    fixture.close()
    return items


def listener_owner(port):
    value = subprocess.run(['/usr/sbin/lsof', '-nP', f'-iTCP:{port}', '-sTCP:LISTEN', '-t'], capture_output=True, text=True)
    return [int(x) for x in value.stdout.split() if x.isdigit()]


def resources():
    fixture = Fixture('resource-preflight')
    try:
        accounts = []
        for email in ['admin@meetspace.test', 'alice@meetspace.test', 'bob@meetspace.test', 'other@meetspace.test']:
            cookie = fixture.login(email)
            reply, _ = fixture.req('GET', '/api/session', cookie=cookie)
            accounts.append({'identity': email, 'login': 'passed', 'session_status': reply['status'], 'user': reply['json']['user']})
        health, _ = fixture.req('GET', '/api/health')
        import sys
        imports = sorted({n.module.split('.')[0] if isinstance(n, ast.ImportFrom) else alias.name.split('.')[0]
                          for n in ast.walk(ast.parse((ROOT / 'app/server.py').read_text()))
                          if isinstance(n, (ast.Import, ast.ImportFrom)) for alias in (n.names if isinstance(n, ast.Import) else [None])})
        record = {'status': 'passed', 'python_version': sys.version, 'python_executable': sys.executable,
                  'sqlite_runtime': sqlite3.sqlite_version, 'zoneinfo': {'name': str(fixture.module.SHANGHAI), 'fixed_datetime_observed': fixture.module.datetime.now(fixture.module.SHANGHAI).isoformat()},
                  'source_imports': imports, 'external_third_party_integrations': [],
                  'source_dependency_review': 'app/server.py 所有运行时 import 属于 Python 标准库；前端 app.js 无外部服务调用，后端本地SQLite，无真实第三方集成需要凭据。',
                  'source_hashes': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ['app/server.py', 'web/app.js']},
                  'resources': {'isolated_database': str(fixture.db.relative_to(BASE)), 'port': fixture.port,
                                'process_pid': os.getpid(), 'listener_owners': listener_owner(fixture.port),
                                'actual_health': health, 'public_synthetic_accounts': accounts},
                  'credential_policy': 'Cookie、令牌和密码仅在测试进程内存，证据未写入其值。SQLite为隔离合成fixture，不归档其会话或口令哈希。'}
        checks = {'Python_3_11_plus': sys.version_info >= (3, 11), 'owned_local_listener': listener_owner(fixture.port) == [os.getpid()],
                  'all_four_real_accounts_verified': all(x['session_status'] == 200 for x in accounts), 'health': health['status'] == 200,
                  'stdlib_only_source': all(x in sys.stdlib_module_names or x == '__future__' for x in imports)}
        record['checks'] = checks
        record['status'] = 'passed' if all(checks.values()) else 'failed'
        (BASE / 'resource-preflight.json').write_text(json.dumps(record, ensure_ascii=False, indent=2))
        return record
    finally:
        fixture.close()


def cli():
    name = 'cli-sigint'
    directory = PROJECTS / (name + '-' + str(time.time_ns()))
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT / 'app', directory / 'app', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT / 'web', directory / 'web')
    database = directory / 'fixture.sqlite'
    with socket.socket() as temporary:
        temporary.bind(('127.0.0.1', 0))
        port = temporary.getsockname()[1]
    command = ['/opt/miniconda3/bin/python', '-m', 'app.server', '--host', '127.0.0.1', '--port', str(port), '--db', str(database)]
    items = []
    processes = []
    logs = []
    def start(label):
        log_path = ARTIFACTS / ('cli-' + label + '.log')
        log = log_path.open('w')
        logs.append(log)
        process = subprocess.Popen(command, cwd=directory, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
        processes.append(process)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and process.poll() is None:
            response, _ = request(port, 'GET', '/api/health')
            if response['status'] == 200 and process.pid in listener_owner(port):
                return process
            time.sleep(.1)
        raise RuntimeError('CLI startup listener ownership not proven')
    try:
        first = start('first')
        admin_reply, admin = request(port, 'POST', '/api/login', {'email': 'admin@meetspace.test', 'password': 'MeetSpace!2026'})
        room, _ = request(port, 'POST', '/api/rooms', room_payload('SIGINT资料'), admin)
        member_reply, member = request(port, 'POST', '/api/login', {'email': 'alice@meetspace.test', 'password': 'MeetSpace!2026'})
        tomorrow = datetime.now(timezone(timedelta(hours=8))).date() + timedelta(days=1)
        body = {'room_id': room['json']['room']['id'], 'title': 'SIGINT持久化预约',
                'start': f'{tomorrow}T10:00:00+08:00', 'end': f'{tomorrow}T11:00:00+08:00', 'attendees': 3, 'idempotency_key': 'sigint-saved'}
        saved, _ = request(port, 'POST', '/api/bookings', body, member)
        read, _ = request(port, 'POST', '/api/notifications/read', {}, member)
        before = snapshot(database)
        owners_before = listener_owner(port)
        sent_at = time.monotonic()
        first.send_signal(signal.SIGINT)
        try:
            exit_code = first.wait(timeout=20)
        except subprocess.TimeoutExpired:
            return [{'item': 'CLI_SIGINT_restart', 'status': 'blocked', 'actual': {'reason': '20秒观察期内尚未结束，未新增业务超时要求', 'pid': first.pid}}]
        elapsed = time.monotonic() - sent_at
        owners_after = listener_owner(port)
        closed_response, _ = request(port, 'GET', '/api/health')
        second = start('restart')
        _, new_admin = request(port, 'POST', '/api/login', {'email': 'admin@meetspace.test', 'password': 'MeetSpace!2026'})
        _, new_member = request(port, 'POST', '/api/login', {'email': 'alice@meetspace.test', 'password': 'MeetSpace!2026'})
        rooms, _ = request(port, 'GET', '/api/rooms', cookie=new_admin)
        bookings, _ = request(port, 'GET', '/api/bookings', cookie=new_member)
        notifications, _ = request(port, 'GET', '/api/notifications', cookie=new_member)
        after = snapshot(database)
        add_item(items, 'CLI_SIGINT_restart', {
            'real_setup_all_writes_finished': admin_reply['status'] == 200 and member_reply['status'] == 200 and room['status'] == 201 and saved['status'] == 201 and read['status'] == 200,
            'pid_owned_listener_before_SIGINT': owners_before == [first.pid],
            'real_exit_and_listener_released': first.returncode is not None and owners_after == [] and closed_response['status'] is None,
            'same_port_new_pid_owns_listener': first.pid != second.pid and listener_owner(port) == [second.pid],
            'all_business_rows_identical_no_reseed': before == after,
            'API_readback_room': rooms['status'] == 200 and any(r['name'] == 'SIGINT资料' for r in rooms['json']['rooms']),
            'API_readback_booking': bookings['status'] == 200 and any(b['title'] == body['title'] for b in bookings['json']['bookings']),
            'API_readback_read_notification': notifications['status'] == 200 and len(notifications['json']['notifications']) == 1 and notifications['json']['notifications'][0]['read'] == 1},
            {'command': command, 'first_pid': first.pid, 'second_pid': second.pid, 'port': port,
             'owners_before': owners_before, 'owners_after': owners_after, 'exit_code_observed': exit_code, 'exit_elapsed_seconds': elapsed,
             'clock_mode': 'actual_system_clock_for_real_CLI; booking_next_day', 'real_clock': datetime.now(timezone.utc).isoformat(),
             'before': before, 'after': after, 'readback': {'rooms': rooms, 'bookings': bookings, 'notifications': notifications}})
    finally:
        for process in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=10)
        for log in logs:
            log.close()
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=['transport', 'replay', 'cli', 'unsupported'])
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    PROJECTS.mkdir(parents=True, exist_ok=True)
    jobs = {'transport': ('WB-response-transport-disconnect', transport),
            'replay': ('WB-booking-response-loss-replay', replay),
            'cli': ('WB-runtime-sigint-persistence', cli),
            'unsupported': ('WB-http-unsupported-methods', unsupported)}
    outputs = []
    for job, (scenario, operation) in jobs.items():
        if args.only and args.only != job:
            continue
        print('START ' + scenario, flush=True)
        try:
            items = operation()
            status = 'failed' if any(x['status'] == 'failed' for x in items) else ('blocked' if any(x['status'] == 'blocked' for x in items) else 'passed')
            record = {'scenario_id': scenario, 'status': status, 'method_ids': ['AI-' + scenario], 'items': items}
        except Exception as exc:
            record = {'scenario_id': scenario, 'status': 'unproven', 'method_ids': ['AI-' + scenario], 'error': type(exc).__name__, 'traceback': traceback.format_exc(), 'items': []}
        evidence = ARTIFACTS / (scenario + '.json')
        evidence.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        record = {**record, 'evidence': str(evidence.relative_to(ROOT))}
        outputs.append(record)
        print('END ' + scenario + ' ' + record['status'] + ' items=' + str(len(record['items'])), flush=True)
    result = {'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_hashes': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in ['app/server.py', 'app/__init__.py', 'web/app.js', 'web/index.html', 'web/style.css']},
              'ledger_hashes': {name: hashlib.sha256((ROOT / 'tests/delivery-acceptance' / (name + '.json')).read_bytes()).hexdigest() for name in ['requirements', 'scenarios', 'methods']},
              'scope': 'supplemental_four_API_runtime_scenarios_only', 'results': outputs}
    (BASE / ('api-results-' + args.only + '.json' if args.only else 'api-results.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
