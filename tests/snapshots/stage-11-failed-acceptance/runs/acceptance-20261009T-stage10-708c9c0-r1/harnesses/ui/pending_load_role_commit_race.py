"""Native original stage10: old pending load session held across a later self role commit."""
import asyncio,hashlib,json,traceback
import coverage_cycle_ui_identity as h
from playwright.async_api import async_playwright
PIN='708c9c057b5c9014f4ff975fdc5774093a687abe';JS='f06c17c249d27e16ccdba83511f0d3c18534358a238a0f08c79eaec7ff0e8322';SERVER='5f1b056d791a452e842c35bff6bccbb50389a9e882bd1127d436aecdb103c5b5'
assert h.REV==PIN and h.HASHES['web/app.js']==JS and h.HASHES['app/server.py']==SERVER
assert not (h.AUDIT/'instrumented-app.js').exists()
async def arrived(items):
 for _ in range(1000):
  if items:return
  await asyncio.sleep(.01)
 raise TimeoutError('expected route did not reach barrier')
async def state(e):return {**await e.observe(),'generation':await e.p.evaluate('state.identityGeneration'),'loadToken':await e.p.evaluate('state.loadToken'),'identityPending':await e.p.evaluate('state.identityPending')}
async def one(e):
 await e.nav('manage');sessions=[];selfpatch=[];count=0
 async def session(route):
  nonlocal count
  count+=1
  if count<=2:
   response=await route.fetch();body=await response.json();assert response.status==200 and body['user']['role']=='admin';sessions.append((route,response));e.events.append({'event':'real_admin_session200_held','order':count,'body':body,'roles':e.roles(),'UI':await state(e)})
  elif count==3:
   e.events.append({'event':'self_commit_session503','roles':e.roles(),'UI':await state(e)});await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'新角色提交后身份查询503','code':'test_late_role_query'}))
  else:await route.continue_()
 async def patch(route):
  selfpatch.append(route);e.events.append({'event':'self_patch_held_before_backend','payload':route.request.post_data_json,'roles':e.roles(),'UI':await state(e)})
 await e.p.route('**/api/session',session);await e.p.route('**/api/members/1',patch)
 await e.p.locator('[data-member="3"]').select_option('admin');await arrived(sessions);assert len(sessions)==1 and e.roles()[2][-1]=='admin'
 assert await e.p.locator('[data-member="3"]').is_disabled() and await e.p.locator('[data-member="1"]').is_enabled();await e.p.locator('[data-member="1"]').select_option('member');await arrived(selfpatch);assert e.roles()[0][-1]=='admin'
 await e.p.locator('nav [data-page=bookings]').click()
 for _ in range(1000):
  if len(sessions)>=2:break
  await asyncio.sleep(.01)
 assert len(sessions)==2;old_pending=await state(e);assert old_pending['loading'] and old_pending['identityPending'] and old_pending['user']['role']=='admin'
 response=await selfpatch[0].fetch();assert response.status==200;await selfpatch[0].fulfill(response=response);await e.p.locator('.retry-panel').wait_for();await e.p.wait_for_function('() => state.user?.role==="member" && state.identityPending && state.loadError==="新角色提交后身份查询503"')
 before=await state(e);cookie=await e.cookie();st,direct,_=h.req(e.url,'/api/session','GET',cookie=cookie);ms,mb,_=h.req(e.url,'/api/members','GET',cookie=cookie);assert st==200 and direct['user']['role']=='member' and ms==403;assert len(sessions)==2 and count==3
 snapshot=e.snapshot();idx=len(e.events);route,old_response=sessions[1];await route.fulfill(response=old_response);await e.p.wait_for_timeout(300);await e.p.wait_for_function('() => !state.loading');after=await state(e);st,actual,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());ms,mb,_=h.req(e.url,'/api/members','GET',cookie=await e.cookie())
 e.check('交叉故障顺序与真实角色提交成立',count==3 and before['user']['role']=='member' and before['identityPending'] and before['loadError']=='新角色提交后身份查询503' and e.roles()[0][-1]=='member' and e.roles()[2][-1]=='admin',{'session_interceptions':count,'old_pending_load':old_pending,'before_release':before,'actual_session_after_commit':direct,'responses':e.responses})
 e.check('旧pending admin200不得覆盖后提交member或清新pending',after['user']['role']=='member' and not after['manage'] and after['identityPending'],{'first_changeRole_response_still_held':True,'old_pending_load':old_pending,'before_release':before,'after_release':after,'actual_session':actual,'new_events':e.events[idx:]})
 e.check('后台member与管理403及其他业务保持',st==200 and actual['user']['role']=='member' and ms==403 and snapshot==e.snapshot(),{'session_status':st,'members_status':ms,'members_body':mb,'snapshot_before':snapshot,'snapshot_after':e.snapshot()});await e.shot('older-pending-admin200-after-new-commit')
async def main():
 e=h.Env();o={'name':'pending-load-admin200-after-new-self-role-commit503','revision':PIN,'source_hashes':h.HASHES,'scenario_ids':['WB-ui-role-demotion-reload','WB-ui-load-token-races','WB-ui-self-demotion-session-failure'],'method_ids':['AI-WB-ui-role-demotion-reload','AI-WB-ui-load-token-races','AI-WB-ui-self-demotion-session-failure'],'scope':'Native exact source crossed role operation/pending load control; first changeRole response remains held during observation; not formal ledger result','status':'unproven'}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  try:
   await e.start(browser,'pending-role-commit-race','admin',False);assert hashlib.sha256((e.dir/'web/app.js').read_bytes()).hexdigest()==JS;await one(e);o['status']='passed' if all(x['passed'] for x in e.checks) else 'failed'
  except Exception as ex:o['error']=str(ex);o['traceback']=traceback.format_exc()
  finally:
   o.update({'browser':browser.version,'fixture_source_hashes':getattr(e,'fixture_hashes',{}),'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[]),'product_or_formal_ledger_modified':False})
   (h.AUDIT/'pending-load-role-commit-race.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':o['status'],'error':o.get('error'),'checks':[(x['assertion'],x['passed']) for x in o['checks']]},ensure_ascii=False),flush=True)
   try:await e.close()
   except Exception:pass
  await browser.close()
if __name__=='__main__':asyncio.run(main())
