import asyncio,json
import identity_env as h
async def cross_session200(e,target,newwho):
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

async def same_identity_session200(e):
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
