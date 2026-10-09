"""Native uninstrumented stage10 UI: same identity, two actual role operations reordered."""
import asyncio,hashlib,json,traceback
from pathlib import Path
import coverage_cycle_ui_identity as h
from playwright.async_api import async_playwright
PIN='708c9c057b5c9014f4ff975fdc5774093a687abe';JS='f06c17c249d27e16ccdba83511f0d3c18534358a238a0f08c79eaec7ff0e8322';SERVER='5f1b056d791a452e842c35bff6bccbb50389a9e882bd1127d436aecdb103c5b5'
assert h.REV==PIN and h.HASHES['web/app.js']==JS and h.HASHES['app/server.py']==SERVER
assert not (h.AUDIT/'instrumented-app.js').exists(), 'Native control must not instrument frontend'
async def one(e):
 await e.nav('manage');held=[];armed=True
 async def session_barrier(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;response=await route.fetch();body=await response.json();assert response.status==200 and body['user']['role']=='admin';held.append((route,response));e.events.append({'event':'first_role_session_actual_admin200_held','status':response.status,'body':body,'roles':e.roles(),'generation':await e.p.evaluate('state.identityGeneration'),'loadToken':await e.p.evaluate('state.loadToken')})
 await e.p.route('**/api/session',session_barrier)
 first=e.p.locator('[data-member="3"]');second=e.p.locator('[data-member="1"]');await first.select_option('admin')
 for _ in range(1000):
  if held:break
  await asyncio.sleep(.01)
 assert held,'first actual session response not held';assert await first.is_disabled() and await second.is_enabled();e.events.append({'event':'native_second_select_operable_while_first_disabled','first_disabled':await first.is_disabled(),'second_enabled':await second.is_enabled(),'roles':e.roles()})
 await second.select_option('member');await e.p.wait_for_function('() => state.user?.role === "member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]") && document.querySelector("#toast").textContent==="成员角色已更新"')
 before=await e.observe();cookie=await e.cookie();st,direct,_=h.req(e.url,'/api/session','GET',cookie=cookie);ms,mb,_=h.req(e.url,'/api/members','GET',cookie=cookie);assert st==200 and direct['user']['role']=='member' and ms==403
 generation=await e.p.evaluate('state.identityGeneration');token=await e.p.evaluate('state.loadToken');snapshot=e.snapshot();idx=len(e.events);route,response=held[0];await route.fulfill(response=response);await e.p.wait_for_timeout(350);await e.p.wait_for_function('() => !state.loading');after=await e.observe();st,latest,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());ms,mb,_=h.req(e.url,'/api/members','GET',cookie=await e.cookie())
 e.check('先真实提升Bob再真实自降提交',e.roles()[0][-1]=='member' and e.roles()[2][-1]=='admin' and any(x['path']=='/api/members/3' and x['status']==200 for x in e.responses) and any(x['path']=='/api/members/1' and x['status']==200 for x in e.responses),{'roles':e.roles(),'responses':e.responses})
 e.check('同身份迟到首轮admin200不得撤回新member界面身份',after['user']==before['user']==latest['user'] and not after['manage'] and after['page']=='spaces' and after['scope']=='mine',{'before_UI':before,'after_UI':after,'actual_session_before':direct,'actual_session_after':latest,'same_generation_before':generation,'same_generation_after':await e.p.evaluate('state.identityGeneration'),'loadToken_before_release':token,'loadToken_after_release':await e.p.evaluate('state.loadToken'),'events_after_release':e.events[idx:]})
 e.check('后台仍member且管理403、业务无后续写入',st==200 and latest['user']['role']=='member' and ms==403 and snapshot==e.snapshot(),{'session_status':st,'members_status':ms,'members_body':mb,'before_snapshot':snapshot,'after_snapshot':e.snapshot()});await e.shot('late-admin200-released')
async def main():
 e=h.Env();o={'name':'same-identity-other-promote-then-self-demote','revision':PIN,'source_hashes':h.HASHES,'scenario_ids':['WB-ui-role-demotion-reload','WB-ui-load-token-races'],'method_ids':['AI-WB-ui-role-demotion-reload','AI-WB-ui-load-token-races'],'scope':'Native exact source control; same identity generation, different actual role operations; not formal ledger result','status':'unproven'}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  try:
   await e.start(browser,'same-identity-role-race','admin',False);assert hashlib.sha256((e.dir/'web/app.js').read_bytes()).hexdigest()==JS;await one(e);o['status']='passed' if all(x['passed'] for x in e.checks) else 'failed'
  except Exception as ex:o['error']=str(ex);o['traceback']=traceback.format_exc()
  finally:
   o.update({'browser':browser.version,'fixture_source_hashes':getattr(e,'fixture_hashes',{}),'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[]),'product_or_formal_ledger_modified':False})
   (h.AUDIT/'same-identity-role-race.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':o['status'],'error':o.get('error'),'checks':[(x['assertion'],x['passed']) for x in o['checks']]},ensure_ascii=False),flush=True)
   try:await e.close()
   except Exception:pass
  await browser.close()
if __name__=='__main__':asyncio.run(main())
