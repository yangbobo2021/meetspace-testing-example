"""Copied native Reviewer counterexample sequence; original remains frozen."""
import asyncio,json
LATEST="最新自身降权身份查询不可用"
async def observe(e):
 return {**await e.observe(), "identityPending":await e.p.evaluate("state.identityPending"),"roleRefreshToken":await e.p.evaluate("state.roleRefreshToken"),"identityGeneration":await e.p.evaluate("state.identityGeneration")}
async def one(e, mode):
    await e.nav('manage')
    held = []; armed = True
    async def first_patch(route):
        held.append(route)
        e.events.append({'event': 'old_patch_native_request_held', 'payload': route.request.post_data_json,
                         'UI': await observe(e), 'roles': e.roles()})
    async def current_session_fault(route):
        nonlocal armed
        if not armed: return await route.continue_()
        armed = False
        e.events.append({'event': 'new_role_commit_before_session503', 'roles': e.roles(), 'UI': await observe(e)})
        await route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': LATEST, 'code': 'test_new_role_session'}))
    await e.p.route('**/api/members/2', first_patch)
    await e.p.route('**/api/session', current_session_fault)
    await e.p.locator('[data-member="2"]').select_option('admin')
    for _ in range(1000):
        if held: break
        await asyncio.sleep(.01)
    assert held
    assert await e.p.locator('[data-member="2"]').is_disabled()
    assert await e.p.locator('[data-member="1"]').is_enabled()
    await e.p.locator('[data-member="1"]').select_option('member')
    await e.p.wait_for_function('(message) => state.user?.role==="member" && state.identityPending && !state.loading && state.loadError===message && document.querySelector("#toast").textContent===message', arg=LATEST)
    before = await observe(e); snapshot = e.snapshot()
    status, identity, _ = h.req(e.url, '/api/session', cookie=await e.cookie())
    assert status == 200 and identity['user']['role'] == 'member'
    e.check('较新角色真实提交后当前身份查询故障与pending成立',
            e.roles()[0][-1] == 'member' and e.roles()[1][-1] == 'member' and e.roles()[2][-1] == 'admin' and
            any(r['path'] == '/api/members/1' and r['status'] == 200 for r in e.responses) and
            before['identityPending'] and before['loadError'] == LATEST,
            {'UI': before, 'roles': e.roles(), 'backend_identity': identity})
    route = held[0]
    if mode == '503':
        old = {'status': 503, 'body': {'error': '较旧他人角色PATCH503', 'code': 'test_old_patch'}}
        await route.fulfill(status=503, content_type='application/json', body=json.dumps(old['body']))
    elif mode == 'network':
        old = {'transport': 'failed'}
        await route.abort('failed')
    else:
        # The held native request now reaches the real server under its unchanged
        # cookie, whose role has really become member. This is actual 403, not fake.
        response = await route.fetch(); body = await response.json()
        assert response.status == 403 and body['code'] == 'forbidden'
        old = {'status': response.status, 'body': body, 'source': 'actual_role_permission_response'}
        await route.fulfill(response=response)
    e.events.append({'event': 'old_patch_failure_released', 'mode': mode, 'actual': old})
    await e.p.wait_for_timeout(350)
    after = await observe(e)
    e.check('同身份旧PATCH失败不得覆盖较新pending的错误与反馈',
            after['loadError'] == before['loadError'] and after['toast'] == before['toast'] and
            after['identityPending'] and after['user'] == before['user'] and
            after['identityGeneration'] == before['identityGeneration'] and
            after['roleRefreshToken'] == before['roleRefreshToken'],
            {'before': before, 'after': after, 'old_failure': old})
    status, actual, _ = h.req(e.url, '/api/session', cookie=await e.cookie())
    member_status, body, _ = h.req(e.url, '/api/members', cookie=await e.cookie())
    e.check('晚失败后真实member及403授权与业务不变',
            status == 200 and actual['user']['role'] == 'member' and member_status == 403 and e.snapshot() == snapshot,
            {'identity': actual, 'members_status': member_status, 'before': snapshot, 'after': e.snapshot()})
    await e.shot('late-patch-failure')
    await e.p.locator('[data-refresh]').click()
    await e.p.wait_for_function('() => state.user?.role==="member" && !state.identityPending && !state.loading && !state.loadError && !document.querySelector("nav [data-page=manage]")')
    final = await observe(e)
    e.check('原生重试仍可读取真实member并完成恢复',
            not final['identityPending'] and not final['loadError'] and e.snapshot() == snapshot,
            {'UI': final, 'snapshot': e.snapshot()})
