"""Independent developer verification, exact original JS copies and native actions."""
import asyncio, hashlib, importlib.util, json, os, sys, traceback
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
os.environ['MEETSPACE_COVERAGE_AUDIT'] = str(OUT / 'native-data')
MANIFEST = json.loads((OUT / 'source-manifest.json').read_text())

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

h = load('independent_identity_env', HERE / 'isolated_env.py')
assert h.REV == MANIFEST['base_revision']
assert all(h.HASHES[name] == MANIFEST['source_sha256'][name] for name in h.HASHES)
cross = load('native_cross', HERE / 'cross_identity.py'); cross.h = h
same = load('native_same', HERE / 'same_identity.py'); same.h = h
pending = load('native_pending', HERE / 'pending_cross_role.py'); pending.h = h

async def current401(e, obj, phase):
    await h.role_expiry(e, obj, phase)
    checkpoint = next(c['actual']['UI'] for c in e.checks
                      if c['assertion'] == '清user回登录且catch无旧workspace加载')
    e.check('当前真实401反馈仍可见且精确绑定过期提示',
            checkpoint['toast'] == '登录已过期，请重新登录' and checkpoint['login'] and checkpoint['user'] is None,
            checkpoint)

async def other_success(e):
    await e.nav('manage')
    await e.p.locator('[data-member="2"]').select_option('admin')
    await e.p.wait_for_function('() => !state.identityPending && !state.loading && !state.loadError && state.user?.role==="admin" && !!document.querySelector("nav [data-page=manage]") && document.querySelector("#toast").textContent==="成员角色已更新"')
    obs = await e.observe()
    st, identity, _ = h.req(e.url, '/api/session', cookie=await e.cookie())
    e.check('正常他人角色更新保留本人实际admin与管理入口',
            e.roles()[1][-1] == 'admin' and st == 200 and identity['user'] == obs['user'] and obs['manage'],
            {'UI': obs, 'server_identity': identity, 'roles': e.roles()})
    await e.shot('other-success')

async def pending_with_recovery(e):
    await pending.one(e)
    snapshot = e.snapshot()
    index = len(e.responses)
    await e.p.locator('[data-refresh]').click()
    await e.p.wait_for_function('() => state.user?.role==="member" && !state.identityPending && !state.loading && !state.loadError && state.page==="spaces" && state.scope==="mine" && !document.querySelector("nav [data-page=manage]") && !!document.querySelector("#filter-date")')
    obs = await e.observe()
    status, identity, _ = h.req(e.url, '/api/session', cookie=await e.cookie())
    e.check('交叉旧响应丢弃后原生重试真实读取member身份并结束',
            status == 200 and identity['user'] == obs['user'] and e.snapshot() == snapshot and
            any(r['path'] == '/api/session' and r['status'] == 200 for r in e.responses[index:]),
            {'UI': obs, 'current_identity': identity, 'responses': e.responses[index:],
             'before_snapshot': snapshot, 'after_snapshot': e.snapshot()})
    await e.shot('cross-pending-native-retry-completed')

async def main():
    rows = []
    cases = [
        ('cross-self-logout-login-other', cross.one, (1, 'other'), True),
        ('cross-other-logout-login-bob', cross.one, (2, 'bob'), False),
        ('same-identity-late-admin200', same.one, (), False),
        ('pending-load-new-role-commit503', pending.one, (), False),
        ('current401-self-before-patch', current401, ('self', 'before-patch'), True),
        ('current401-self-after-commit', current401, ('self', 'after-commit'), True),
        ('current401-other-after-commit', current401, ('other', 'after-commit'), True),
        ('normal-self-demotion', h.success_control, (), True),
        ('normal-other-role-update', other_success, (), False),
        ('self-demotion503-native-retry', h.demotion, ('503', 'data-retry'), True),
        ('self-demotion-network-native-retry', h.demotion, ('network', 'data-retry'), True),
    ]
    only_pending = '--only-pending-recovery' in sys.argv
    if only_pending:
        cases = [('pending-load-new-role-commit503-and-native-retry', pending_with_recovery, (), False)]
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        for name, function, arguments, second_admin in cases:
            e = h.Env()
            row = {'name': name, 'scope': 'independent developer regression, not formal 167 acceptance', 'status': 'unproven'}
            try:
                await e.start(browser, name, 'admin', second_admin)
                assert 'instrumented_web/app.js' not in e.fixture_hashes
                await function(e, *arguments)
                row['status'] = 'passed' if e.checks and all(c['passed'] for c in e.checks) else 'failed'
            except Exception as error:
                row['error'] = str(error); row['traceback'] = traceback.format_exc()
            finally:
                row.update({'fixture_source_sha256': getattr(e, 'fixture_hashes', {}), 'checks': getattr(e, 'checks', []),
                            'events': getattr(e, 'events', []), 'responses': getattr(e, 'responses', []),
                            'screenshots': getattr(e, 'shots', [])})
                path = OUT / 'native-data' / (name + '.json')
                path.write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
                rows.append({'name': name, 'status': row['status'], 'evidence': str(path.relative_to(OUT))})
                print(name, row['status'], row.get('error', ''), flush=True)
                try: await e.close()
                except Exception: pass
        await browser.close()
    unchanged = all(hashlib.sha256((h.ROOT / name).read_bytes()).hexdigest() == value
                    for name, value in MANIFEST['source_sha256'].items())
    summary = 'independent-native-results-pending-recovery.json' if only_pending else 'independent-native-results.json'
    (OUT / summary).write_text(json.dumps({
        'base_revision': h.REV, 'source_sha256': MANIFEST['source_sha256'], 'browser': browser.version,
        'source_unchanged_after_run': unchanged, 'results': rows, 'formal_verdict': None,
        'scope': 'developer repair verification only'}, ensure_ascii=False, indent=2) + '\n')
    assert unchanged

if __name__ == '__main__':
    asyncio.run(main())
