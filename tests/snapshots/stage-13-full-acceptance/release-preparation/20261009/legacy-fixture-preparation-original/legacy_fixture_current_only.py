"""Prepared synthetic legacy-record reader probe; only execute a newly pinned target.

No old application is imported, executed, or used to create a database here.
Fixture SQL and the old seconds canonical oracle are independent test inputs.
This is not a substitute for a formally reviewed method revision.
"""
import argparse
import ast
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
from datetime import datetime, timezone, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE teams(id INTEGER PRIMARY KEY,name TEXT NOT NULL);
CREATE TABLE users(id INTEGER PRIMARY KEY,team_id INTEGER NOT NULL REFERENCES teams(id),email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL);
CREATE TABLE sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),expires REAL NOT NULL);
CREATE TABLE rooms(id INTEGER PRIMARY KEY,team_id INTEGER NOT NULL REFERENCES teams(id),name TEXT NOT NULL,location TEXT NOT NULL,capacity INTEGER NOT NULL,equipment TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,UNIQUE(team_id,name));
CREATE TABLE bookings(id INTEGER PRIMARY KEY,team_id INTEGER NOT NULL REFERENCES teams(id),room_id INTEGER NOT NULL REFERENCES rooms(id),user_id INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,start TEXT NOT NULL,end TEXT NOT NULL,attendees INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'confirmed',created_at TEXT NOT NULL,cancelled_at TEXT,idempotency_key TEXT NOT NULL,request_hash TEXT NOT NULL,UNIQUE(user_id,idempotency_key));
CREATE INDEX booking_room_time ON bookings(room_id,status,start,end);
CREATE TABLE notifications(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),booking_id INTEGER NOT NULL REFERENCES bookings(id),message TEXT NOT NULL,created_at TEXT NOT NULL,read INTEGER NOT NULL DEFAULT 0);
"""
BASE_REVISION = '708c9c057b5c9014f4ff975fdc5774093a687abe'
HISTORIC_HASH = 'af2fc7db282738d398bc75ba4620c8c4f9870d8c1a58ad38eb03dfda4d70fa2c'
T = datetime(2030, 4, 10, 1, tzinfo=timezone.utc)


def old_seconds_oracle(body):
    start = datetime.fromisoformat(body['start']).astimezone(timezone.utc)
    end = datetime.fromisoformat(body['end']).astimezone(timezone.utc)
    assert start.microsecond == end.microsecond == 0
    canonical = [body['room_id'], body['title'].strip(), start.isoformat(timespec='seconds'),
                 end.isoformat(timespec='seconds'), body['attendees']]
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False).encode()).hexdigest(), canonical


def snapshot(db):
    with sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True) as connection:
        tables = ('teams', 'users', 'sessions', 'rooms', 'bookings', 'notifications')
        rows = {table: connection.execute('SELECT * FROM ' + table + ' ORDER BY 1').fetchall() for table in tables}
    # Never persist raw credentials or session rows. Compare full rows in memory.
    digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()
    return rows, {'row_counts': {name: len(value) for name, value in rows.items()}, 'state_sha256': digest}


def prepare_fixture(db, body, status, cookie_token):
    fingerprint, canonical = old_seconds_oracle(body)
    salt = '11' * 16
    credential = salt + ':' + hashlib.scrypt(b'MeetSpace!2026', salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    with sqlite3.connect(db) as connection:
        connection.executescript(SCHEMA)
        connection.execute('INSERT INTO teams VALUES(1,?)', ('见山设计',))
        connection.execute('INSERT INTO users VALUES(2,1,?,?,?,?)', ('alice@meetspace.test', '陈悦', 'member', credential))
        connection.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(cookie_token.encode()).hexdigest(), 2, (T + timedelta(hours=8)).timestamp()))
        connection.execute('INSERT INTO rooms VALUES(4,1,?,?,6,?,1)', ('青松', '2F · 北侧', '["白板", "电话会议"]'))
        connection.execute('INSERT INTO bookings VALUES(4,1,4,2,?,?,?,?,?,?,?,?,?)',
                           (body['title'], canonical[2], canonical[3], 2, status, '2026-10-09T01:00:00+00:00',
                            '2030-04-10T01:00:00+00:00' if status == 'cancelled' else None,
                            body['idempotency_key'], fingerprint))
        connection.execute('INSERT INTO notifications VALUES(1,2,4,?,?,0)', ('合成旧记录原通知', '2026-10-09T01:00:00+00:00'))
    return fingerprint, canonical


def request(base, token, path, method='GET', body=None):
    headers = {'Content-Type': 'application/json', 'X-Meeting-App': '1', 'Origin': base,
               'Cookie': 'meetspace_session=' + token}
    req = Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    try:
        response = urlopen(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return {'status': response.status, 'body': json.loads(response.read()),
                'set_cookie_present': response.headers.get('Set-Cookie') is not None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--source-sha256-file', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute or args.revision == BASE_REVISION:
        raise SystemExit('Prepared only; execution requires --execute and the new fixed repair revision.')
    root = Path(args.project).resolve()
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if actual != args.revision:
        raise SystemExit('Target revision differs from the explicit execution pin.')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', 'app', 'web'], cwd=root, check=True, capture_output=True)
    expected = json.loads(Path(args.source_sha256_file).read_text())
    expected = expected.get('source_sha256', expected)
    source_hashes = {str(file.relative_to(root)): hashlib.sha256(file.read_bytes()).hexdigest()
                     for folder in ('app', 'web') for file in (root / folder).rglob('*')
                     if file.is_file() and '__pycache__' not in file.parts}
    if any(expected.get(name) != value for name, value in source_hashes.items()):
        raise SystemExit('Source hashes differ from the independently reviewed execution manifest.')
    # Parse only the pinned current source for schema-shape validation before fixture use.
    tree = ast.parse((root / 'app/server.py').read_text())
    source_schema = next(ast.literal_eval(node.value) for node in tree.body
                         if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCHEMA' for t in node.targets))
    def schema_shape(schema):
        with sqlite3.connect(':memory:') as connection:
            connection.executescript(schema)
            return sorted(connection.execute('SELECT type,name,tbl_name FROM sqlite_schema').fetchall()), {
                table: connection.execute('PRAGMA table_info(' + table + ')').fetchall()
                for table in ('teams', 'users', 'sessions', 'rooms', 'bookings', 'notifications')}
    assert schema_shape(SCHEMA) == schema_shape(source_schema), 'Fixture schema shape must match the fixed target contract.'
    isolated_source = tempfile.TemporaryDirectory(prefix='meetspace-fixed-current-source-')
    isolated_root = Path(isolated_source.name)
    for folder in ('app', 'web'):
        shutil.copytree(root / folder, isolated_root / folder, ignore=shutil.ignore_patterns('__pycache__'))
    fixture_hashes = {name: hashlib.sha256((isolated_root / name).read_bytes()).hexdigest() for name in source_hashes}
    assert fixture_hashes == source_hashes
    spec = importlib.util.spec_from_file_location('fixed_current_fixture_target', isolated_root / 'app/server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # The only imported application version.
    original_datetime, original_time = module.datetime, module.time.time
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return T.astimezone(tz) if tz is not None else T.replace(tzinfo=None)
    module.datetime = FixedDateTime
    module.time.time = lambda: T.timestamp()
    evidence = {'scope': 'prepared synthetic old seconds-format fixture; only pinned current application executes',
                'revision': actual, 'source_sha256': source_hashes, 'fixture_application_source_sha256': fixture_hashes,
                'fixture_origin': 'synthetic SQL, not newly generated by an old application',
                'clock': {'datetime_now_utc': module.datetime.now(timezone.utc).isoformat(), 'time_time': module.time.time()},
                'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'formal_verdict': None, 'cases': []}
    try:
        for name, day, status in [('historic-started', '2026-10-11', 'confirmed'),
                                  ('future-confirmed', '2030-04-11', 'confirmed'),
                                  ('future-cancelled', '2030-04-11', 'cancelled')]:
            checks = []
            def check(label, passed, actual):
                checks.append({'assertion': label, 'passed': bool(passed), 'actual': actual})
            with tempfile.TemporaryDirectory(prefix='meetspace-synthetic-legacy-') as directory:
                db = Path(directory) / 'fixture.sqlite'
                token = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode()
                payload = {'room_id': 4, 'title': '旧库重放兼容', 'start': day + 'T10:00:00+08:00',
                           'end': day + 'T11:00:00+08:00', 'attendees': 2, 'idempotency_key': 'reviewer-old-db'}
                fingerprint, canonical = prepare_fixture(db, payload, status, token)
                if name == 'historic-started':
                    assert fingerprint == HISTORIC_HASH
                before, safe_before = snapshot(db)
                server = module.ApplicationServer(('127.0.0.1', 0), module.Store(db))
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = 'http://127.0.0.1:' + str(server.server_port)
                try:
                    opened, safe_opened = snapshot(db)
                    check('startup preserves every pre-existing row', before == opened, safe_opened)
                    identity = request(base, token, '/api/session')
                    rooms = request(base, token, '/api/rooms')
                    check('fixture existing cookie authenticates without new login', identity['status'] == 200 and
                          identity['body'].get('user', {}).get('id') == 2 and rooms['status'] == 200 and
                          not identity['set_cookie_present'], {'session': identity, 'protected_rooms_status': rooms['status']})
                    equivalents = [payload, {**payload, 'title': '  ' + payload['title'] + '  '},
                                   {**payload, 'start': day + 'T02:00:00Z', 'end': day + 'T03:00:00+00:00'},
                                   {**payload, 'start': day + 'T10:00:00.000000+08:00', 'end': day + 'T11:00:00.000000+08:00'}]
                    for index, body in enumerate(equivalents):
                        response = request(base, token, '/api/bookings', 'POST', body)
                        booking = response['body'].get('booking', {})
                        check('equivalent legacy replay ' + str(index), response['status'] == 201 and booking ==
                              {'id': 4, 'status': status, 'replayed': True}, response)
                        after, safe_after = snapshot(db)
                        check('equivalent replay leaves all rows unchanged ' + str(index), after == before, safe_after)
                    for field in ('start', 'end'):
                        for delta in (-1, 1):
                            changed = datetime.fromisoformat(payload[field]) + timedelta(microseconds=delta)
                            body = {**payload, field: changed.isoformat()}
                            response = request(base, token, '/api/bookings', 'POST', body)
                            check(field + ' microsecond ' + str(delta) + ' conflicts for existing K', response['status'] == 409 and
                                  response['body'].get('code') == 'idempotency_conflict' and 'booking' not in response['body'], response)
                            after, safe_after = snapshot(db)
                            check('precision conflict leaves all rows unchanged', after == before, safe_after)
                            if name == 'future-confirmed':
                                new_body = {**body, 'idempotency_key': 'new-granularity-' + field + str(delta)}
                                response = request(base, token, '/api/bookings', 'POST', new_body)
                                check('new key nonzero microseconds still returns exact 400 invalid_interval', response['status'] == 400 and
                                      response['body'].get('code') == 'invalid_interval', response)
                                after, safe_after = snapshot(db)
                                check('new key invalid interval leaves all rows unchanged', after == before, safe_after)
                    if name == 'future-confirmed':
                        normal = {**payload, 'title': '合成fixture正常对照', 'start': day + 'T14:00:00.000000+08:00',
                                  'end': day + 'T15:00:00.000000+08:00', 'idempotency_key': 'normal-new-zero-microseconds'}
                        response = request(base, token, '/api/bookings', 'POST', normal)
                        normal_booking = response['body'].get('booking', {})
                        check('new key aligned explicit zero microseconds creates normally', response['status'] == 201 and
                              normal_booking.get('id') == 5 and normal_booking.get('status') == 'confirmed' and
                              normal_booking.get('replayed') is False, response)
                        created, safe_created = snapshot(db)
                        check('normal creation writes one booking and notice, preserving every original row',
                              all(created[table] == before[table] for table in ('teams', 'users', 'sessions', 'rooms')) and
                              len(created['bookings']) == len(before['bookings']) + 1 and
                              created['bookings'][:len(before['bookings'])] == before['bookings'] and
                              len(created['notifications']) == len(before['notifications']) + 1 and
                              created['notifications'][:len(before['notifications'])] == before['notifications'], safe_created)
                        repeated = request(base, token, '/api/bookings', 'POST', normal)
                        check('normal new record also supports real replay', repeated['status'] == 201 and
                              repeated['body'].get('booking') == {'id': 5, 'status': 'confirmed', 'replayed': True}, repeated)
                        replayed, safe_replayed = snapshot(db)
                        check('normal replay creates no additional rows', created == replayed, safe_replayed)
                finally:
                    server.shutdown(); server.server_close(); thread.join()
                evidence['cases'].append({'name': name, 'fixture_request_hash': fingerprint, 'canonical_seconds': canonical,
                                          'fixture_state': safe_before, 'checks': checks,
                                          'observation_status': 'passed' if all(c['passed'] for c in checks) else 'failed'})
    finally:
        module.datetime, module.time.time = original_datetime, original_time
        isolated_source.cleanup()
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'cases': len(evidence['cases']), 'formal_verdict': None,
                      'observation_status': 'passed' if len(evidence['cases']) == 3 and all(c['observation_status'] == 'passed' for c in evidence['cases']) else 'unproven_or_failed'}))


if __name__ == '__main__':
    main()
