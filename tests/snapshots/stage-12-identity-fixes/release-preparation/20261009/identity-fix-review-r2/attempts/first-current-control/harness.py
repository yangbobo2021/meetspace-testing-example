"""Native current-failure feedback and a genuine later successful commit control."""
import asyncio, importlib.util, json, os, traceback
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).resolve().parent; OUT = HERE.parent
os.environ['MEETSPACE_COVERAGE_AUDIT'] = str(OUT / 'current-control-data')
spec = importlib.util.spec_from_file_location('current_control_env', HERE / 'isolated_env.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
manifest = json.loads((OUT / 'source-manifest.json').read_text())
assert all(h.HASHES[n] == manifest['source_sha256'][n] for n in h.HASHES)

async def current_failure(e, mode):
    await e.nav('manage')
    expected = '当前角色PATCH不可用' if mode == '503' else 'Failed to fetch'
    if mode == 'real403':
        cookie = e.api_login('bob')
        status, body, _ = h.req(e.url, '/api/members/1', 'PATCH', {'role': 'member'}, cookie)
        assert status == 200
        expected = '仅管理员可以执行此操作'
        e.events.append({'event': 'second_admin_real_role_change_before_current_action', 'roles': e.roles(), 'status': status})
    else:
        async def fault(route):
            if mode == '503':
                await route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': expected, 'code': 'test_current_patch'}))
            else:
                await route.abort('failed')
        await e.p.route('**/api/members/2', fault)
    snapshot = e.snapshot()
    token = await e.p.evaluate('state.roleRefreshToken')
    await e.p.locator('[data-member="2"]').select_option('admin')
    await e.p.wait_for_function('(message) => !state.loading && document.querySelector("#toast").textContent===message', arg=expected)
    observed = await e.observe()
    e.check('当前PATCH失败仍准确显示反馈，不被起始序号守卫抑制', observed['toast'] == expected and
            not await e.p.evaluate('state.identityPending') and await e.p.evaluate('state.roleRefreshToken') == token,
            {'UI': observed, 'roleRefreshToken_before': token, 'roleRefreshToken_after': await e.p.evaluate('state.roleRefreshToken')})
    e.check('当前失败目标角色与所有业务行无修改', e.snapshot() == snapshot, {'before': snapshot, 'after': e.snapshot()})
    if mode == 'real403':
        e.check('权限失败确实来自真实HTTP403', any(r['path'] == '/api/members/2' and r['status'] == 403 for r in e.responses), e.responses)
    await e.shot('current-error-visible')

async def late_success(e):
    await e.nav('manage'); held = []; armed = True
    async def first_patch(route):
        held.append(route)
        e.events.append({'event': 'first_alice_patch_held_before_send', 'roles': e.roles(),
                         'roleRefreshToken': await e.p.evaluate('state.roleRefreshToken')})
    async def first_followup_failure(route):
        nonlocal armed
        if not armed: return await route.continue_()
        armed = False
        e.events.append({'event': 'bob_commit_before_followup503', 'roles': e.roles()})
        await route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': 'Bob提交后身份读取故障', 'code': 'test_intermediate_query'}))
    await e.p.route('**/api/members/2', first_patch)
    await e.p.route('**/api/session', first_followup_failure)
    await e.p.locator('[data-member="2"]').select_option('admin')
    for _ in range(1000):
        if held: break
        await asyncio.sleep(.01)
    assert held and await e.p.locator('[data-member="3"]').is_enabled()
    await e.p.locator('[data-member="3"]').select_option('admin')
    await e.p.wait_for_function('() => state.identityPending && state.loadError==="Bob提交后身份读取故障" && !state.loading')
    before = e.snapshot(); before_token = await e.p.evaluate('state.roleRefreshToken'); index = len(e.responses)
    assert e.roles()[1][-1] == 'member' and e.roles()[2][-1] == 'admin' and before_token == 1
    response = await held[0].fetch(); assert response.status == 200
    await held[0].fulfill(response=response)
    await e.p.wait_for_function('() => !state.identityPending && !state.loading && !state.loadError && document.querySelector("#toast").textContent==="成员角色已更新" && document.querySelector("[data-member=\"2\"]")?.value==="admin" && document.querySelector("[data-member=\"3\"]")?.value==="admin"')
    observed = await e.observe(); expected = json.loads(json.dumps(before)); expected['roles'][1][-1] = 'admin'
    e.check('较早点击但真实较晚提交的成功不会按起始token丢弃',
            e.snapshot() == expected and await e.p.evaluate('state.roleRefreshToken') == 2 and
            observed['user']['role'] == 'admin' and observed['manage'] and
            any(r['path'] == '/api/members/2' and r['status'] == 200 for r in e.responses[index:]) and
            any(r['path'] == '/api/session' and r['status'] == 200 for r in e.responses[index:]),
            {'before_snapshot': before, 'after_snapshot': e.snapshot(), 'UI': observed,
             'refresh_before': before_token, 'refresh_after': await e.p.evaluate('state.roleRefreshToken'), 'responses': e.responses[index:]})
    await e.shot('late-real-success-applied')

async def main():
    rows = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        cases = [('current-patch-' + mode, current_failure, (mode,), True) for mode in ('503', 'network', 'real403')]
        cases.append(('earlier-click-later-commit-success', late_success, (), False))
        for name, function, arguments, second_admin in cases:
            e = h.Env(); row = {'name': name, 'status': 'unproven', 'scope': 'independent developer control'}
            try:
                await e.start(browser, name, 'admin', second_admin)
                assert 'instrumented_web/app.js' not in e.fixture_hashes
                await function(e, *arguments)
                row['status'] = 'passed' if e.checks and all(c['passed'] for c in e.checks) else 'failed'
            except Exception as error:
                row['error'] = str(error); row['traceback'] = traceback.format_exc()
            finally:
                row.update({'fixture_source_sha256': getattr(e, 'fixture_hashes', {}), 'checks': getattr(e, 'checks', []),
                            'events': getattr(e, 'events', []), 'responses': getattr(e, 'responses', []), 'screenshots': getattr(e, 'shots', [])})
                path = OUT / 'current-control-data' / (name + '.json')
                path.write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
                rows.append({'name': name, 'status': row['status'], 'evidence': str(path.relative_to(OUT))})
                print(name, row['status'], row.get('error', ''), flush=True)
                try: await e.close()
                except Exception: pass
        await browser.close()
    (OUT / 'independent-current-control-results.json').write_text(json.dumps({'source_sha256': manifest['source_sha256'],
        'results': rows, 'formal_verdict': None}, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    asyncio.run(main())
