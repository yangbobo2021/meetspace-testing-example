"""Prepared native regression suite. Runs only the project's already-applied source.
Never loads the proposal. Network barriers only; all business commits and actual401
are verified through the real HTTP server. No formal ledger writes.
"""
import argparse,asyncio,datetime,hashlib,json,os,subprocess,traceback
from pathlib import Path

async def arrived(items,count=1):
 for _ in range(1500):
  if len(items)>=count:return
  await asyncio.sleep(.01)
 raise TimeoutError('route barrier did not arrive')
async def observe(e):
 o=await e.observe();o.update({'identityGeneration':await e.p.evaluate('state.identityGeneration'),'loadToken':await e.p.evaluate('state.loadToken'),'identityPending':await e.p.evaluate('state.identityPending'),'roleRefreshToken':await e.p.evaluate('state.roleRefreshToken ?? null')});return o
async def revoke(e):
 st,b,_=h.req(e.url,'/api/logout','POST',{},await e.cookie());assert st==200,(st,b);e.events.append({'event':'actual_HTTP_logout_revocation','status':st,'body':b})
async def release(route,response,kind):
 if kind=='200' or kind=='401':await route.fulfill(response=response)
 elif kind=='503':await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'过时操作受控503','code':'test_old_operation'}))
 else:await route.abort('failed')
async def new_identity(e,who='other'):
 await e.p.locator('[data-logout]:visible').first.click();await e.p.locator('#login-form').wait_for();await e.login(who);await e.p.wait_for_function('() => state.user && !state.loading && !state.loadError && !state.identityPending && !!document.querySelector("#filter-date")');st,b,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());assert st==200 and b['user']['email']==who+'@meetspace.test';return await observe(e)
async def no_old_effects(e,before,idx,label):
 await e.p.wait_for_timeout(200);after=await observe(e);st,direct,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());later=e.events[idx:];sql_roles=e.snapshot()['roles'];sql_identity=[after['user']['id'],after['user']['team_id'],after['user']['role']]
 e.check(label,st==200 and after==before and after['user']==direct['user'] and sql_identity in sql_roles and not any(x['event']=='request' for x in later),{'before':before,'after':after,'actual_session':direct,'sql_roles':sql_roles,'expected_sql_identity':sql_identity,'events_after_release':later})
async def cross_phase(e,phase,kind):
 await e.nav('manage');held=[];armed=True;target=2
 async def barrier(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False
  if kind=='401':await revoke(e)
  response=await route.fetch();body=await response.json();assert response.status==(401 if kind=='401' else 200)
  held.append((route,response));e.events.append({'event':'actual_'+phase+'_response_held','status':response.status,'body':body,'roles':e.roles(),'UI':await observe(e)})
 pattern='**/api/members/2' if phase=='PATCH' else '**/api/session'
 await e.p.route(pattern,barrier);await e.p.locator(f'[data-member="{target}"]').select_option('admin');await arrived(held)
 before=await new_identity(e);idx=len(e.events);route,response=held[0];await release(route,response,kind);await no_old_effects(e,before,idx,'过时'+phase+'/'+kind+'跨原生logout/newlogin不改新身份、pending、错误或toast');await e.shot('released')
async def same_identity_old_error(e,kind):
 await e.nav('manage');held=[];armed=True
 async def session(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;response=await route.fetch();assert response.status==200;held.append((route,response));e.events.append({'event':'older_role_session_response_held','roles':e.roles(),'body':await response.json()})
 await e.p.route('**/api/session',session);await e.p.locator('[data-member="3"]').select_option('admin');await arrived(held);await e.p.locator('[data-member="1"]').select_option('member');await e.p.wait_for_function('() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")');before=await observe(e);idx=len(e.events);route,response=held[0];await release(route,response,kind);await no_old_effects(e,before,idx,'同身份过时role session/'+kind+'不污染已完成较新member操作');await e.shot('older-error-released')
async def same_identity_late_patch(e,mode):
 await e.nav('manage');held=[];armed=True;target=1 if mode=='actual-late-commit' else 3
 async def patch(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False
  if mode=='actual-late-commit':held.append((route,None));e.events.append({'event':'earlier_click_PATCH_held_before_actual_commit','roles':e.roles()})
  else:
   response=await route.fetch();assert response.status==200;held.append((route,response));e.events.append({'event':'earlier_actual_PATCH200_response_held','roles':e.roles()})
 await e.p.route('**/api/members/'+str(target),patch);await e.p.locator('[data-member="'+str(target)+'"]').select_option('member' if target==1 else 'admin');await arrived(held)
 later_target=2 if mode=='actual-late-commit' else 1;await e.p.locator('[data-member="'+str(later_target)+'"]').select_option('admin' if later_target==2 else 'member');await e.p.wait_for_function('() => state.user && !state.loading && !state.identityPending && !state.loadError && document.querySelector("#toast").textContent==="成员角色已更新"');before=await observe(e)
 route,response=held[0]
 if response is None:response=await route.fetch();assert response.status==200;e.events.append({'event':'earlier_click_PATCH_actually_commits_after_later_operation','roles':e.roles(),'before_UI':before})
 await route.fulfill(response=response);await e.p.wait_for_function('() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")');after=await observe(e);st,actual,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());ms,mb,_=h.req(e.url,'/api/members','GET',cookie=await e.cookie())
 e.check('同身份迟到PATCH成功确认必须读取实际最新角色，不能按click先后丢弃有效commit',st==200 and after['user']==actual['user'] and after['user']['role']=='member' and ms==403 and not after['manage'] and not after['identityPending'] and not after['loading'] and not after['loadError'],{'mode':mode,'before_UI':before,'after_UI':after,'roles':e.roles(),'actual_session':actual,'members_status':ms});await e.shot('late-PATCH-'+mode)

async def current401(e,phase):
 await e.nav('manage');before=e.snapshot();armed=True;target=2
 async def fault(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;await revoke(e);response=await route.fetch();body=await response.json();assert response.status==401;e.events.append({'event':'current_role_'+phase+'_actual401','body':body,'roles':e.roles()});await route.fulfill(response=response)
 await e.p.route('**/api/'+('members/2' if phase=='PATCH' else 'session'),fault);await e.p.locator('[data-member="2"]').select_option('admin');await e.p.locator('#login-form').wait_for();await e.p.wait_for_function('() => document.querySelector("#toast").textContent.length>0');o=await observe(e);expected_role='member' if phase=='PATCH' else 'admin'
 e.check('当前真实401回登录且错误反馈可见',o['user'] is None and o['login'] and not o['manage'] and o['openDialogs']==0 and not o['identityPending'] and bool(o['toast']) and o['toast']!='成员角色已更新',o)
 e.check('401时点角色拒绝或commit符合实际',e.roles()[1][-1]==expected_role,{'before':before,'after':e.snapshot(),'phase':phase})
 await e.p.unroute('**/api/'+('members/2' if phase=='PATCH' else 'session'));await e.login('admin');await e.shot('401-recovered')
async def current401_older_operation(e):
 await e.nav('manage');held=[];armed=True
 async def barrier(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;held.append(route);e.events.append({'event':'older_role_session_held_before_backend','roles':e.roles()})
 await e.p.route('**/api/session',barrier);await e.p.locator('[data-member="3"]').select_option('admin');await arrived(held);await e.p.locator('[data-member="1"]').select_option('member');await e.p.wait_for_function('() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date")');await revoke(e);response=await held[0].fetch();body=await response.json();assert response.status==401;await held[0].fulfill(response=response);await e.p.locator('#login-form').wait_for();await e.p.wait_for_function('() => document.querySelector("#toast").textContent.length>0 && document.querySelector("#toast").textContent!=="成员角色已更新"');o=await observe(e)
 e.check('同代较早操作收到当前有效401仍撤销身份并保留反馈',o['user'] is None and o['login'] and bool(o['toast']) and not o['identityPending'] and e.roles()[0][-1]=='member',{'response':body,'UI':o,'roles':e.roles()});await e.shot('authoritative401')
async def stale_success_toast(e):
 await e.nav('manage');held=[];armed=True
 async def rooms(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;response=await route.fetch();assert response.status==200;held.append((route,response));e.events.append({'event':'changeRole_loadPage_actual_rooms200_held','body':await response.json(),'UI':await observe(e)})
 await e.p.route('**/api/rooms?*',rooms);await e.p.locator('[data-member="2"]').select_option('admin');await arrived(held);before=await new_identity(e);idx=len(e.events);route,response=held[0];await route.fulfill(response=response);await no_old_effects(e,before,idx,'changeRole已开始loadPage但跨身份后不显示旧成功toast');await e.shot('stale-success-suppressed')
async def pending_cross(e,kind):
 await e.nav('manage');sessions=[];patches=[];count=0
 async def session(route):
  nonlocal count
  count+=1
  if count<=2:
   response=await route.fetch();assert response.status==200 and (await response.json())['user']['role']=='admin';sessions.append((route,response));e.events.append({'event':'old_admin200_session_held','order':count,'roles':e.roles(),'UI':await observe(e)})
  elif count==3:await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'新角色提交后身份查询503','code':'test_new_pending'}))
  else:await route.continue_()
 async def patch(route):patches.append(route);e.events.append({'event':'new_self_patch_held_before_backend','roles':e.roles()})
 await e.p.route('**/api/session',session);await e.p.route('**/api/members/1',patch);await e.p.locator('[data-member="3"]').select_option('admin');await arrived(sessions);await e.p.locator('[data-member="1"]').select_option('member');await arrived(patches);await e.p.locator('nav [data-page=bookings]').click();await arrived(sessions,2);old=await observe(e);response=await patches[0].fetch();assert response.status==200;await patches[0].fulfill(response=response);await e.p.locator('.retry-panel').wait_for();await e.p.wait_for_function('() => state.user?.role==="member" && state.identityPending && state.loadError==="新角色提交后身份查询503"');before=await observe(e);idx=len(e.events);route,response=sessions[1];await release(route,response,kind);await e.p.wait_for_timeout(200);after=await observe(e);st,direct,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());ms,mb,_=h.req(e.url,'/api/members','GET',cookie=await e.cookie())
 e.check('旧pending '+kind+'跨新commit不能动新pending/loading/error',before==after and after['user']['role']=='member' and after['identityPending'] and not after['loading'] and after['loadError']=='新角色提交后身份查询503' and st==200 and direct['user']['role']=='member' and ms==403,{'old_pending_load':old,'before':before,'after':after,'first_changeRole_response_still_held':True,'later_events':e.events[idx:],'actual_session':direct,'members_status':ms})
 await e.p.locator('[data-refresh]').click();await e.p.wait_for_function('() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")');o=await observe(e);e.check('最新pending错误可通过真实原生retry完成',o['page']=='spaces' and o['scope']=='mine' and o['user']['role']=='member' and not o['identityPending'] and not o['loadError'] and not o['manage'],o);await e.shot('new-pending-recovered')
async def current_nonself(e):
 await e.nav('manage');await e.p.locator('[data-member="2"]').select_option('admin')
 await e.p.wait_for_function('() => state.user?.role === "admin" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("[data-member]") && document.querySelector("#toast").textContent === "成员角色已更新"')
 assert await e.p.locator('[data-member="2"]').input_value()=='admin'
 o=await observe(e);st,d,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());e.check('普通nonself成功身份admin管理页及toast完成',st==200 and o['user']==d['user'] and o['manage'] and o['page']=='manage' and e.roles()[1][-1]=='admin',o);await e.shot('normal-nonself')


async def current_patch_error(e,mode):
 await e.nav('manage');before=e.snapshot();held_error={};armed=True
 async def fault(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False
  if mode=='503':
   held_error.update({'status':503,'body':{'error':'当前角色PATCH不可用','code':'test_current_patch'}})
   await route.fulfill(status=503,content_type='application/json',body=json.dumps(held_error['body']))
  elif mode=='network':
   held_error.update({'transport':'failed'});await route.abort('failed')
  else:
   bob=e.api_login('bob');status,body,_=h.req(e.url,'/api/members/1','PATCH',{'role':'member'},bob);assert status==200,(status,body)
   e.events.append({'event':'actual_second_admin_revokes_current_admin_role','status':status,'roles':e.roles()})
   response=await route.fetch();body=await response.json();assert response.status==403 and body['code']=='forbidden';held_error.update({'status':403,'body':body,'source':'actual_role_permission_response'});await route.fulfill(response=response)
  e.events.append({'event':'current_PATCH_failure_delivered','mode':mode,'actual':held_error})
 await e.p.route('**/api/members/2',fault);await e.p.locator('[data-member="2"]').select_option('admin')
 await e.p.wait_for_function('() => state.user && !state.loading && !state.identityPending && document.querySelector("#toast").textContent.length>0 && document.querySelector("#toast").textContent!=="成员角色已更新"')
 o=await observe(e);status,identity,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie());after=e.snapshot()
 expected_message=held_error.get('body',{}).get('error')
 e.check('当前PATCH错误必须保留正常反馈而不误当成旧操作吞掉',status==200 and not o['login'] and not o['identityPending'] and o['roleRefreshToken']==0 and o['toast']!='成员角色已更新' and bool(o['toast']) and (not expected_message or o['toast']==expected_message),{'mode':mode,'UI':o,'actual_failure':held_error,'backend_identity':identity})
 if mode=='real403':
  e.check('实际403未越权修改目标且当前拒绝有可见反馈',identity['user']['role']=='member' and e.roles()[1][-1]=='member' and o['retry'] and o['loadError']==expected_message,{'before':before,'after':after,'UI':o,'actual403':held_error})
 else:
  e.check('当前未提交PATCH故障保留admin业务且可继续管理',before==after and identity['user']['role']=='admin' and o['manage'] and o['page']=='manage' and not o['loadError'] and await e.p.locator('[data-member="2"]').input_value()=='member',{'before':before,'after':after,'UI':o})
 await e.shot('current-PATCH-'+mode)
 await e.p.unroute('**/api/members/2')
 if mode=='real403':
  await e.p.locator('[data-logout]:visible').first.click();await e.p.locator('#login-form').wait_for();await e.login('admin');await e.p.wait_for_function('() => state.user?.role==="member" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("#filter-date")')
  final=await observe(e);e.check('当前真实403后重新登录可读取实际member',final['user']['role']=='member' and not final['manage'] and not final['loadError'] and final['page']=='spaces',final)
 else:
  await e.p.locator('[data-member="2"]').select_option('admin');await e.p.wait_for_function('() => !state.loading && !state.identityPending && !state.loadError && document.querySelector("#toast").textContent==="成员角色已更新"');final=await observe(e)
  e.check('当前PATCH故障后正常原生重试可实际成功',e.roles()[1][-1]=='admin' and final['user']['role']=='admin' and final['manage'],{'UI':final,'roles':e.roles()})
async def late_patch_success_after_new_pending(e):
 await e.nav('manage');held=[];armed=True;message='较新角色提交后暂时无法读取身份'
 async def first(route):held.append(route);e.events.append({'event':'old_Alice_PATCH_held_before_backend','roles':e.roles(),'UI':await observe(e)})
 async def current_session(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':message,'code':'test_new_pending'}))
 await e.p.route('**/api/members/2',first);await e.p.route('**/api/session',current_session);await e.p.locator('[data-member="2"]').select_option('admin');await arrived(held);await e.p.locator('[data-member="3"]').select_option('admin')
 await e.p.wait_for_function('(message) => state.identityPending && !state.loading && state.loadError===message && document.querySelector("#toast").textContent===message',arg=message);before=await observe(e)
 e.check('较新Bob真实提交且身份查询503建立pending',e.roles()[1][-1]=='member' and e.roles()[2][-1]=='admin' and before['roleRefreshToken']==1 and before['identityPending'],{'UI':before,'roles':e.roles()})
 response=await held[0].fetch();body=await response.json();assert response.status==200;e.events.append({'event':'old_Alice_PATCH_actual_later_commit200','status':response.status,'body':body,'roles':e.roles()});await held[0].fulfill(response=response)
 await e.p.wait_for_function('() => state.user?.role==="admin" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector("[data-member]") && document.querySelector("#toast").textContent==="成员角色已更新"');after=await observe(e);status,identity,_=h.req(e.url,'/api/session','GET',cookie=await e.cookie())
 e.check('真正较晚成功PATCH不按开始token丢弃，刷新实际身份并清新pending',status==200 and after['user']==identity['user'] and after['roleRefreshToken']==2 and not after['identityPending'] and not after['loadError'] and after['toast']=='成员角色已更新' and after['manage'] and e.roles()[1][-1]=='admin' and e.roles()[2][-1]=='admin' and await e.p.locator('[data-member="2"]').input_value()=='admin' and await e.p.locator('[data-member="3"]').input_value()=='admin',{'before':before,'after':after,'roles':e.roles(),'identity':identity});await e.shot('late-success-clears-new-pending')


CASES=[
 ('original-cross-self-session200','cross-session200',(1,'other'),True),
 ('original-cross-other-session200','cross-session200',(2,'bob'),False),
 ('original-same-identity-session200','same-session200',(),False),
 ('original-pending-load-new-role200','pending-cross',('200',),False),
]+[(f'late-{phase}-{kind}-cross-identity','cross-phase',(phase,kind),False) for phase in ['PATCH','session'] for kind in ['200','503','network','401'] if not (phase=='session' and kind=='200')]+[
 ('same-identity-late-PATCH-response200','same-late-patch',('late-response',),False),('same-identity-late-PATCH-actual-commit','same-late-patch',('actual-late-commit',),True),
 ('same-identity-old-session503','same-error',('503',),False),('same-identity-old-session-network','same-error',('network',),False),
 ('current-role-PATCH401','current401',('PATCH',),False),('current-role-session401','current401',('session',),False),('current401-from-earlier-same-identity-role-query','earlier-current401',(),False),
 ('old-success-toast-after-loadPage-identity-switch','stale-toast',(),False),
 ('old-pending503-after-new-role-commit503','pending-cross',('503',),False),('old-pending-network-after-new-role-commit503','pending-cross',('network',),False),
 ('normal-nonself-success','normal-nonself',(),False),('normal-self-demotion-success','normal-self',(),True),
]+[(f'current-self-session-{fault}-{recovery}','demotion',(fault,recovery),True) for fault in ['503','network'] for recovery in ['data-retry','reload']]
CASES += [(f'same-identity-old-PATCH-{mode}-after-new-pending','late-patch-error',(mode,),True) for mode in ['503','network','real403']]
CASES += [(f'current-role-PATCH-{mode}-feedback','current-patch-error',(mode,),mode=='real403') for mode in ['503','network','real403']]
CASES += [('same-identity-late-PATCH200-after-new-pending','late-success-pending',(),False)]


async def main(args):
 root=Path.cwd();out=Path(args.output).resolve();out.relative_to((root/'tests/delivery-acceptance').resolve());out.mkdir(parents=True,exist_ok=True);js=hashlib.sha256((root/'web/app.js').read_bytes()).hexdigest();assert js==args.expected_js_sha256,'Run only after the expected source has actually been applied to project web/app.js';assert js!='f06c17c249d27e16ccdba83511f0d3c18534358a238a0f08c79eaec7ff0e8322','Original known-failing source is not an authorized development regression target';assert not (out/'instrumented-app.js').exists(),'Native suite forbids instrumentation';os.environ['MEETSPACE_COVERAGE_AUDIT']=str(out)
 git_status=subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True);diff_sha=hashlib.sha256(subprocess.check_output(['git','diff','--','app/server.py','web/app.js'],cwd=root)).hexdigest()
 global h
 import identity_env as h
 import native_original_sequences as native
 import native_late_patch_sequences as native_late
 native_late.h=h
 functions={'late-patch-error':native_late.one,'current-patch-error':current_patch_error,'late-success-pending':late_patch_success_after_new_pending,'cross-session200':native.cross_session200,'same-session200':native.same_identity_session200,'cross-phase':cross_phase,'same-error':same_identity_old_error,'same-late-patch':same_identity_late_patch,'current401':current401,'earlier-current401':current401_older_operation,'stale-toast':stale_success_toast,'pending-cross':pending_cross,'normal-nonself':current_nonself,'normal-self':h.success_control,'demotion':h.demotion}
 selected=[x for x in CASES if not args.only or x[0]==args.only];assert selected
 results=[]
 from playwright.async_api import async_playwright
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for name,kind,params,second_admin in selected:
   e=h.Env();o={'name':name,'kind':kind,'source_revision':h.REV,'source_sha256':h.HASHES,'git_worktree_status':git_status,'working_tree_source_diff_sha256':diff_sha,'expected_js_sha256':args.expected_js_sha256,'scope':'development native regression only; no formal ledger result','scenario_ids':['WB-ui-role-demotion-reload','WB-ui-load-token-races','WB-ui-self-demotion-session-failure'],'status':'unproven'}
   try:
    await e.start(browser,name,'admin',second_admin);assert hashlib.sha256((e.dir/'web/app.js').read_bytes()).hexdigest()==js;await functions[kind](e,*params);o['status']='passed' if e.checks and all(x['passed'] for x in e.checks) else 'failed'
   except Exception as ex:o['error']=str(ex);o['traceback']=traceback.format_exc()
   finally:
    o.update({'browser':browser.version,'fixture_source_hashes':getattr(e,'fixture_hashes',{}),'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[]),'final_business_snapshot':e.snapshot() if getattr(e,'db',None) else None})
    path=out/(name+'.json');path.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');results.append({'name':name,'status':o['status'],'evidence':path.name});(out/'results.json').write_text(json.dumps({'source_revision':h.REV,'source_sha256':h.HASHES,'development_only':True,'formal_ledgers_modified':False,'results':results},ensure_ascii=False,indent=2)+'\n');print(name,o['status'],o.get('error',''),flush=True)
    try:await e.close()
    except Exception:pass
  await browser.close()
 assert hashlib.sha256((root/'web/app.js').read_bytes()).hexdigest()==js,'Product source changed during regression'
 if any(x['status']!='passed' for x in results):raise SystemExit(1)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expected-js-sha256',required=True);parser.add_argument('--output',required=True);parser.add_argument('--only',choices=[x[0] for x in CASES]);args=parser.parse_args();asyncio.run(main(args))
