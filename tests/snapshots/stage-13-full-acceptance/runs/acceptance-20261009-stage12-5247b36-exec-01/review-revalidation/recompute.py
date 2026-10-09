"""Read-only independent calculations over saved execution observations."""
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import Counter

R = Path(__file__).resolve().parents[1]
rows = []

def read(name):
    return json.loads((R / name).read_text())

def record(name, condition, details):
    rows.append(dict(check=name, passed=bool(condition), details=details))

for f in (R / 'evidence/api-r2').glob('*.json'):
    d = json.loads(f.read_text())
    if not isinstance(d, dict):
        continue
    for i, c in enumerate(d.get('checks', [])):
        a = c.get('actual', {})
        label = c.get('label', '')
        if isinstance(a, dict) and 'before' in a and 'after' in a and any(t in label for t in ['不变量', '不变']):
            record(f'{f.name}:{i}:snapshot', a['before'] == a['after'], label)

d = read('evidence/api-r2/horizon.json')
for i, q in enumerate(d['http']):
    if q['method'] == 'POST' and q['path'] == '/api/bookings':
        delta = datetime.fromisoformat(q['input']['start']) - datetime.fromisoformat(q['server_clock'])
        expected = 201 if timedelta(0) < delta <= timedelta(days=30) else 400
        record(f'horizon:{i}', q['status'] == expected, dict(seconds=delta.total_seconds(), status=q['status'], expected=expected))

d = read('evidence/api-r2/duration.json')
for i, q in enumerate(d['http']):
    a, b = (datetime.fromisoformat(q['input'][k]) for k in ('start','end'))
    seconds = (b-a).total_seconds()
    expected = 'invalid_duration' if not 900 <= seconds <= 28800 else ('invalid_interval' if any(x.minute % 15 or x.second or x.microsecond for x in (a,b)) else None)
    record(f'duration:{i}', q['body'].get('code') == expected and q['status'] == (400 if expected else 201), dict(seconds=seconds, expected=expected, response=q['body']))

d = read('evidence/ui/201-filters-all-controls.json')
for i, q in enumerate(d['matrix']):
    wanted = sorted(a['id'] for a in d['rooms'] if a['active'] and a['capacity'] >= int(q['capacity'] or 0) and (not q['equipment'] or q['equipment'] in a['equipment']))
    record(f'filter:{i}', sorted(q['actual']) == wanted, dict(capacity=q['capacity'], equipment=q['equipment'], actual=q['actual'], recomputed=wanted))

d = read('evidence/ui/941-stats-real-zero-per-day-and-identity.json')
for i, q in enumerate(d['legacy']):
    start = datetime.fromisoformat(q['date'] + 'T00:00:00+08:00')
    end = start + timedelta(days=1)
    user = {'alice@meetspace.test':2, 'bob@meetspace.test':3, 'admin@meetspace.test':1, 'other@meetspace.test':4}[q['identity']]
    team = 2 if user == 4 else 1
    selected = [a for a in d['legacy_rows'] if a['team'] == team and a['status'] != 'cancelled' and datetime.fromisoformat(a['start']) < end and datetime.fromisoformat(a['end']) > start]
    own = [a for a in selected if a['user'] == user and start <= datetime.fromisoformat(a['start']) < end]
    expected = [1 if team == 2 else 4, len(selected), len(own)]
    record(f'midnight-statistics:{i}', q['stats'] == q['filtered'] == expected and q['zero_matches'] == 0, dict(date=q['date'], identity=q['identity'], actual=q['stats'], expected=expected))

for platform in ('linux', 'macos'):
    d = read(f'evidence/notification-{platform}/results.json')
    for i, q in enumerate(d['rows']):
        a,b = (datetime.fromisoformat(q['input'][k]).astimezone(ZoneInfo('Asia/Shanghai')) for k in ('start','end'))
        expected = f'「{q["input"]["title"]}」预约成功：青松 · {a:%m}月{a:%d}日 {a:%H:%M}–{b:%H:%M}。'
        n = q['notifications']; booking = q['bookings']
        record(f'notification:{platform}:{i}', q['status'] == 201 and len(n) == len(booking) == 1 and n[0]['message'] == expected and n[0]['read'] == 0 and n[0]['user_id'] == booking[0]['user_id'] and n[0]['booking_id'] == booking[0]['id'], dict(timezone=q['timezone'], locale=q['locale'], actual=n[0]['message'], expected=expected))

for f in (R / 'evidence/pending-six').glob('old-*.json'):
    d = json.loads(f.read_text()); a = d['checks'][1]['actual']; z = d['checks'][2]['actual']; tokens = a['old_guard_locals']
    record(f'pending-six:{f.stem}', a['before'] == a['after'] and a['database_before'] == a['database_after'] and a['events_after_release'] == [] and tokens['old'] < tokens['current'] and tokens['identity'] == tokens['currentIdentity'] and a['before']['identityPending'] and a['completion_function'] != 'changeRole' and a['members_status'] == 403 and a['session']['user']['role'] == 'member' and not z['after']['identityPending'] and not z['after']['manage'] and z['session_requests'] == 3,
           dict(guard=a['guard_location'], completion=a['completion_location'], tokens=tokens, requests_after_old_release=a['events_after_release'], recovery_session_requests=z['session_requests']))

for f in (R / 'evidence/ui-stage10/evidence/ui-dialogs').glob('*.json'):
    d = json.loads(f.read_text())
    for i,c in enumerate(d.get('checks', [])):
        a = c.get('actual')
        if not isinstance(a,dict): continue
        if 'before' in a and 'after' in a and '快照' in c.get('assertion',''):
            record(f'dialog:{f.stem}:{i}:snapshot', a['before']==a['after'], c['assertion'])
        if 'expected_closed' in a:
            record(f'dialog:{f.stem}:{i}:open', a['open'] != a['expected_closed'], a)

d = read('evidence/ui/104-responsive-complete-flows.json')
for q in d['viewports']:
    box=q['dialog']
    record(f'viewport:{q["width"]}', q['layout']['width'] == q['layout']['scroll'] and box['x'] >= 0 and box['y'] >= 0 and box['x']+box['width'] <= q['width'] and box['y']+box['height'] <= q['height'], q)

d = read('evidence/room-full-update/results.json')
for i,c in enumerate(d['checks']):
    a=c['actual']
    actual=a.get('actual', a.get('UI'))
    record(f'room-update:{i}', actual == a['expected'], a)

d = read('evidence/ui-stage10/ui-identity/date-empty-recovery.json')
requests=[a['path'] for a in d['events'] if a.get('event')=='request']
record('empty-date:no-request-and-recovery', not any(a.endswith('date=') for a in requests) and '/api/rooms?date=2030-04-12' in requests, requests)

d = read('evidence/api-unsupported-complete-r2/api-evidence/WB-http-unsupported-methods.json')
for i,q in enumerate(d['items']):
    a=q['actual']
    if 'before' in a and 'after' in a:
        record(f'unsupported:{i}:snapshot', a['before']==a['after'], q['item'])
    if 'first' in a and 'repeat' in a and isinstance(a['first'].get('json'),dict):
        record(f'unsupported:{i}:contract', a['first']['status']>=400 and bool(a['first']['json'].get('error')) and bool(a['first']['json'].get('code')) and a['first']['json']['code']==a['repeat']['json']['code'], dict(item=q['item'], first=a['first'], repeat=a['repeat']))

report={'scope':'独立读取已保存原始观察值并重算；未运行应用，不以该辅助计算替代全部语义审阅。','counts':dict(Counter('passed' if a['passed'] else 'failed' for a in rows)), 'checks':rows}
(R/'review-revalidation/recomputed-observations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'counts':report['counts'],'failures':[a for a in rows if not a['passed']]},ensure_ascii=False))
