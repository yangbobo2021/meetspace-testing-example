import asyncio,json
from playwright.async_api import async_playwright
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
 await e.p.locator('[data-logout]:visible').first.click();await e.p.locator('#login-form').wait_for();await e.login(newwho);await e.p.wait_for_function('() => state.user && !state.loading && !state.identityPending && !state.loadError');before=await e.observe();generation=await e.p.evaluate('state.identityGeneration');status,direct,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());assert status==200 and direct['user']['email']==newwho+'@meetspace.test';before_snapshot=e.snapshot();idx=len(e.events)
 route,response=held[0];await route.fulfill(response=response);await e.p.wait_for_function('() => !state.loading');await e.p.wait_for_timeout(300);after=await e.observe();status,after_direct,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());after_generation=await e.p.evaluate('state.identityGeneration')
 e.check('新的实际会话和角色不被延迟changeRole200覆盖',after['user']==after_direct['user']==before['user'] and after['page']==before['page'] and after['scope']==before['scope'] and after['manage']==before['manage'] and after['toast']!='成员角色已更新',{'before_UI':before,'after_UI':after,'new_session_before':direct,'new_session_after':after_direct,'generation_before':generation,'generation_after':after_generation,'events_after_release':e.events[idx:],'business_snapshot_before':before_snapshot,'business_snapshot_after':e.snapshot()});await e.shot('old200-released')

