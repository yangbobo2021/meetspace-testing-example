"""Real UI/HTTP pending identity guards; only network routes hold/inject dependencies."""
import asyncio,json,traceback
from pathlib import Path
import coverage_cycle_ui_identity as h
from playwright.async_api import async_playwright
E=h.AUDIT/'pending-guards';E.mkdir(exist_ok=True)
async def arrived(items):
 for _ in range(1000):
  if items:return
  await asyncio.sleep(.01)
 raise TimeoutError('route barrier did not arrive')
async def patch_fault(e,target=2):
 await e.nav('manage');before=e.roles();held=[];calls=0
 async def session(route):
  nonlocal calls
  calls+=1
  if calls==1:
   e.events.append({'event':'initial_session_fault_after_patch','roles':e.roles()})
   await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'初次身份查询受控503','code':'test_pending_identity'}))
  elif calls==2:
   response=await route.fetch();body=await response.json();held.append((route,response));e.events.append({'event':'pending_session_real_response_held','status':response.status,'body':body,'UI':await e.observe(),'loadToken':await e.p.evaluate('state.loadToken')})
  else:await route.continue_()
 await e.p.route('**/api/session',session)
 await e.p.locator(f'[data-member="{target}"]').select_option('admin' if target==2 else 'member');await e.p.locator('.retry-panel').wait_for();await e.p.wait_for_function('state.identityPending && !state.loading')
 e.check('PATCH实际提交且初次session503',e.roles()[target-1][-1]==('admin' if target==2 else 'member') and any(r['path']==f'/api/members/{target}' and r['status']==200 for r in e.responses),{'before':before,'after':e.roles(),'UI':await e.observe()})
 return held
async def stale(e):
 held=await patch_fault(e);await e.p.locator('[data-refresh]').click();await arrived(held);first_token=await e.p.evaluate('state.loadToken');await e.p.locator('nav [data-page=inbox]').click();await e.ready();new_token=await e.p.evaluate('state.loadToken');before=await e.observe();index=len(e.events)
 route,response=held[0];await route.fulfill(response=response);await e.p.wait_for_timeout(150);after=await e.observe();later=e.events[index:]
 e.check('pending旧session200因stale token不能覆盖最新页',new_token>first_token and before==after and after['page']=='inbox' and after['user']['role']=='admin' and not any(x['event']=='request' for x in later),{'old_token':first_token,'new_token':new_token,'before':before,'after':after,'later_events':later});await e.shot('stale-session')
async def absent(e):
 await e.nav('spaces');early=[];count=0
 async def rooms(route):
  nonlocal count
  count+=1
  if count==1:early.append(route);e.events.append({'event':'early_rooms_held_before_backend','path':route.request.url})
  else:await route.continue_()
 await e.p.route('**/api/rooms?*',rooms);await e.p.locator('nav [data-page=bookings]').click();await arrived(early);await e.p.locator('nav [data-page=manage]').click();await e.ready()
 held=await patch_fault(e);await e.p.locator('[data-refresh]').click();await arrived(held);token=await e.p.evaluate('state.loadToken');cookie=await e.cookie();st,body,_=h.req(e.url,'/api/logout','POST',{},cookie);e.events.append({'event':'real_HTTP_logout_revokes_current_cookie','status':st,'body':body});assert st==200
 response=await early[0].fetch();assert response.status==401;await early[0].fulfill(response=response);await e.p.locator('#login-form').wait_for();await e.p.wait_for_function('state.user===null');before=await e.observe();idx=len(e.events);token_before=await e.p.evaluate('state.loadToken');r,resp=held[0];await r.fulfill(response=resp);await e.p.wait_for_timeout(150);after=await e.observe();token_after=await e.p.evaluate('state.loadToken');later=e.events[idx:]
 e.check('token相同但!user独立阻止pending200复活',token==token_before==token_after and before['user'] is None and after['user'] is None and after['login'] and after['openDialogs']==0 and not any(x['event']=='request' for x in later),{'held200_token':token,'token_before':token_before,'token_after':token_after,'before':before,'after':after,'later_events':later,'rooms_real_status':response.status});await e.shot('user-absent')
async def admin(e):
 held=await patch_fault(e);await e.p.locator('[data-refresh]').click();await arrived(held);r,response=held[0];await r.fulfill(response=response);await e.ready();o=await e.observe();e.check('非self角色提交后pending恢复admin并保留manage',o['user']['role']=='admin' and o['manage'] and o['page']=='manage' and not o['loadError'] and not await e.p.evaluate('state.identityPending') and await e.p.locator('[data-member="2"]').input_value()=='admin',o);await e.shot('admin-recovery')
async def retry_fault(e,kind):
 held=await patch_fault(e,target=1);await e.p.unroute('**/api/session');armed=True
 async def fault(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False
  if kind=='401':
   st,body,_=h.req(e.url,'/api/logout','POST',{},await e.cookie());assert st==200;response=await route.fetch();e.events.append({'event':'pending_retry_real401','status':response.status});assert response.status==401;await route.fulfill(response=response)
  elif kind=='503':await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'重试身份查询受控503','code':'test_pending_retry'}))
  else:await route.abort('failed')
 await e.p.route('**/api/session',fault);await e.p.locator('[data-refresh]').click()
 if kind=='401':
  await e.p.locator('#login-form').wait_for();o=await e.observe();e.check('pending retry当前真实401清身份回登录',o['user'] is None and o['login'] and not o['manage'] and o['openDialogs']==0 and not await e.p.evaluate('state.identityPending'),o)
  await e.p.unroute('**/api/session');await e.login('admin')
 else:
  await e.p.locator('.retry-panel').wait_for();await e.p.wait_for_function('state.identityPending && !state.loading && !!state.loadError');o=await e.observe();e.check('pending retry故障保持明确错误可再重试',bool(o['loadError']) and o['user']['role']=='member' and not o['manage'] and o['toast']!='成员角色已更新',o)
  await e.p.unroute('**/api/session');await e.p.locator('[data-refresh]').click();await e.ready()
 o=await e.observe();e.check('故障恢复真实session成员无管理入口',o['user']['role']=='member' and not o['manage'] and o['page']=='spaces' and o['scope']=='mine' and not o['loadError'] and not await e.p.evaluate('state.identityPending'),o);await e.shot('retry-'+kind)
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  cases=[('stale-token',stale,()),('same-token-user-absent',absent,()),('nonself-admin-recovery',admin,())]+[('pending-retry-'+x,retry_fault,(x,)) for x in ['401','503','network']]
  for name,fn,args in cases:
   e=h.Env();o={'name':name,'revision':h.REV,'source_hashes':h.HASHES,'scenario_ids':['WB-ui-load-token-races','WB-ui-self-demotion-session-failure','WB-ui-role-demotion-reload'],'scope':'actual branches from existing scenarios; not a formal ledger result'};status='unproven'
   try:
    await e.start(browser,'pending-'+name,'admin',True);await fn(e,*args);status='passed' if all(c['passed'] for c in e.checks) else 'failed'
   except Exception as ex:o['error']=str(ex);o['traceback']=traceback.format_exc()
   finally:
    o.update({'status':status,'fixture_source_hashes':getattr(e,'fixture_hashes',{}),'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[])})
    (E/(name+'.json')).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');results.append({'name':name,'status':status,'evidence':'pending-guards/'+name+'.json'})
    print(name,status,o.get('error',''),flush=True)
    try:await e.close()
    except Exception:pass
  await browser.close()
 (h.AUDIT/'pending-guard-results.json').write_text(json.dumps({'revision':h.REV,'source_hashes':h.HASHES,'browser':browser.version,'results':results,'no_formal_ledger_modified':True},ensure_ascii=False,indent=2))
if __name__=='__main__':asyncio.run(main())
