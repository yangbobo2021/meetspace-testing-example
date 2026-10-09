"""Diagnostic: real changeRole session200 held across native logout and new login."""
import asyncio,json,traceback
import coverage_cycle_ui_identity as h
from playwright.async_api import async_playwright
E=h.AUDIT/'change-role-identity-race';E.mkdir(exist_ok=True)
async def one(e,target,newwho):
 await e.nav('manage');held=[];armed=True
 async def barrier(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;response=await route.fetch();body=await response.json();assert response.status==200;held.append((route,response));e.events.append({'event':'changeRole_session_real200_held','status':response.status,'body':body,'committed_roles':e.roles(),'UI':await e.observe(),'generation':await e.p.evaluate('state.identityGeneration')})
 await e.p.route('**/api/session',barrier);await e.p.locator(f'[data-member="{target}"]').select_option('member' if target==1 else 'admin')
 for _ in range(1000):
  if held:break
  await asyncio.sleep(.01)
 assert held,'held session not reached'
 await e.p.locator('[data-logout]:visible').first.click();await e.p.locator('#login-form').wait_for();await e.login(newwho);await e.p.wait_for_function('state.user && !state.loading && !state.identityPending && !state.loadError');before=await e.observe();generation=await e.p.evaluate('state.identityGeneration');status,direct,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());assert status==200 and direct['user']['email']==newwho+'@meetspace.test';before_snapshot=e.snapshot();idx=len(e.events)
 route,response=held[0];await route.fulfill(response=response);await e.p.wait_for_function('!state.loading');await e.p.wait_for_timeout(300);after=await e.observe();status,after_direct,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());after_generation=await e.p.evaluate('state.identityGeneration')
 e.check('新的实际会话和角色不被延迟changeRole200覆盖',after['user']==after_direct['user']==before['user'] and after['page']==before['page'] and after['scope']==before['scope'] and after['manage']==before['manage'] and after['toast']!='成员角色已更新',{'before_UI':before,'after_UI':after,'new_session_before':direct,'new_session_after':after_direct,'generation_before':generation,'generation_after':after_generation,'events_after_release':e.events[idx:],'business_snapshot_before':before_snapshot,'business_snapshot_after':e.snapshot()});await e.shot('old200-released')
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for name,target,who in [('self-demote-then-login-other',1,'other'),('other-promote-then-login-bob',2,'bob')]:
   e=h.Env();o={'name':name,'revision':h.REV,'source_hashes':h.HASHES,'scope':'diagnostic actual identity-state combination, not formal ledger result','scenario_ids':['WB-ui-role-demotion-reload','WB-ui-load-token-races'],'status':'unproven'}
   try:
    await e.start(browser,'changeRole-'+name,'admin',True);await one(e,target,who);o['status']='passed' if all(c['passed'] for c in e.checks) else 'failed'
   except Exception as ex:o['error']=str(ex);o['traceback']=traceback.format_exc()
   finally:
    o.update({'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[]),'fixture_source_hashes':getattr(e,'fixture_hashes',{})})
    (E/(name+'.json')).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');results.append({'name':name,'status':o['status'],'evidence':'change-role-identity-race/'+name+'.json'});print(name,o['status'],o.get('error',''),flush=True)
    try:await e.close()
    except Exception:pass
  await browser.close()
 (h.AUDIT/'change-role-identity-race-results.json').write_text(json.dumps({'revision':h.REV,'source_hashes':h.HASHES,'results':results,'no_formal_ledger_modified':True},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':asyncio.run(main())
