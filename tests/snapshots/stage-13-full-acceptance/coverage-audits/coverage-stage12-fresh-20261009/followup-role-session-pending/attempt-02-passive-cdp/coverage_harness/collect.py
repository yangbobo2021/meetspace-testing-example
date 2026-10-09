"""Approved six state combinations, raw native sequence. Coverage variant separate.
No product/ledger writes; no mutation of state or internal JS business calls.
"""
import argparse,asyncio,hashlib,json,os,subprocess,traceback
from pathlib import Path
REV='5247b360276f2900d20fdeab96bd75bb3ece73fa'
SERVER_SHA='a17a6d939f65252b41998b28022f254af5a6fc745b7264e130ad069489984f73'
JS_SHA='c3347cfe766836d5bc5c776ee9ed03ea01c648847a76c12d19eaba8b830a7798'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
async def observe(e):
 return {**await e.observe(),'identityGeneration':await e.p.evaluate('state.identityGeneration'),'loadToken':await e.p.evaluate('state.loadToken'),'roleRefreshToken':await e.p.evaluate('state.roleRefreshToken'),'identityPending':await e.p.evaluate('state.identityPending')}
async def arrived(items):
 for _ in range(1000):
  if items:return
  await asyncio.sleep(.01)
 raise TimeoutError('old changeRole/session200 barrier never arrived')
async def one(e,new_fault,old_result):
 await e.nav('manage');cdp=await e.ctx.new_cdp_session(e.p);await cdp.send('Network.enable');await cdp.send('Debugger.enable');initiators=[];pauses=[]
 cdp.on('Network.requestWillBeSent',lambda x:initiators.append({'request_id':x['requestId'],'path':x['request']['url'].replace(e.url,''),'initiator':x.get('initiator',{})}) if '/api/' in x['request']['url'] else None)
 cdp.on('Debugger.paused',lambda x:pauses.append(x))
 held=[];session_count=0;latest_message='较新自身降权身份查询503：保留当前错误';new_faults=[]
 async def session(route):
  nonlocal session_count
  session_count+=1
  if session_count==1:
   response=await route.fetch();body=await response.json();assert response.status==200 and body['user']['id']==1 and body['user']['role']=='admin'
   held.append((route,response));e.events.append({'event':'old_changeRole_session_actual_admin200_held','actual_status':response.status,'body':body,'roles':e.roles(),'UI':await observe(e),'not_loadPage_response':True})
  elif session_count==2:
   new_faults.append(new_fault);e.events.append({'event':'new_self_changeRole_session_front_dependency_fault','mode':new_fault,'roles':e.roles(),'UI':await observe(e)})
   if new_fault=='503':await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':latest_message,'code':'test_current_role_pending'}))
   else:await route.abort('failed')
  else:
   response=await route.fetch();body=await response.json();e.events.append({'event':'recovery_session_actual_response','status':response.status,'body':body});await route.fulfill(response=response)
 await e.p.route('**/api/session',session)
 await e.p.locator('[data-member="2"]').select_option('admin');await arrived(held)
 initial=await observe(e);assert await e.p.locator('[data-member="1"]').is_enabled()
 e.check('旧他人角色PATCH实际已提交，扣留的是changeRole首轮真实admin session200',session_count==1 and e.roles()[1][-1]=='admin' and initial['roleRefreshToken']==1 and initial['identityPending'] and any(r['path']=='/api/members/2' and r['status']==200 for r in e.responses),{'UI':initial,'roles':e.roles(),'actual_old_response_source':'first session directly after successful native role PATCH; no navigation/loadPage trigger'})
 await e.p.locator('[data-member="1"]').select_option('member')
 await e.p.locator('.retry-panel').wait_for();await e.p.wait_for_function('() => state.user?.role==="member" && state.identityPending && !state.loading && !!state.loadError && document.querySelector("#toast").textContent===state.loadError')
 before=await observe(e);snapshot=e.snapshot();status,actual,_=h.req(e.url,'/api/session',cookie=await e.cookie());ms,mb,_=h.req(e.url,'/api/members',cookie=await e.cookie())
 e.check('较新自降真实commit及当前故障形成member/pending/最新错误，无管理入口',new_faults==[new_fault] and session_count==2 and any(r['path']=='/api/members/1' and r['status']==200 for r in e.responses) and e.roles()[0][-1]=='member' and before['roleRefreshToken']==2 and before['identityGeneration']==initial['identityGeneration'] and before['user']==actual['user'] and status==200 and ms==403 and before['page']=='spaces' and before['scope']=='mine' and not before['manage'] and before['identityPending'] and not before['loading'] and before['retry'] and before['toast']==before['loadError'] and bool(before['loadError']) and before['toast']!='成员角色已更新' and (new_fault!='503' or before['loadError']==latest_message),{'before_release_UI':before,'server_identity':actual,'members_status':ms,'roles':e.roles(),'snapshot':snapshot,'new_fault':new_fault})
 await e.shot('new-pending-before-old-role-session-release');index=len(e.events);route,response=held[0]
 loc=LOCATIONS['success' if old_result=='200' else 'error']
 bp=await cdp.send('Debugger.setBreakpointByUrl',{'url':e.url+'/app.js','lineNumber':loc['lineNumber'],'columnNumber':loc['columnNumber'],'condition':'roleRefreshToken !== state.roleRefreshToken'})
 if old_result=='200':await route.fulfill(response=response)
 elif old_result=='503':await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'旧角色身份查询503，不得覆盖最新错误','code':'test_old_role_session'}))
 else:await route.abort('failed')
 e.events.append({'event':'actual_old_changeRole_session_released_after_new_pending','mode':old_result,'current_role_refresh_token':before['roleRefreshToken'],'old_role_refresh_token':initial['roleRefreshToken'],'old_actual_200_user':(await response.json())['user'],'new_fault':new_fault,'no_old_loadPage_session_held':True})
 await arrived(pauses);pause=pauses[-1];frame=pause['callFrames'][0];assert frame['functionName']=='changeRole'
 locals_result=await cdp.send('Debugger.evaluateOnCallFrame',{'callFrameId':frame['callFrameId'],'expression':'({old:roleRefreshToken,current:state.roleRefreshToken,identity:identityGeneration,currentIdentity:state.identityGeneration,pending:state.identityPending})','returnByValue':True});values=locals_result['result']['value'];assert values['old']<values['current'] and values['identity']==values['currentIdentity'] and values['pending']
 await cdp.send('Debugger.removeBreakpoint',{'breakpointId':bp['breakpointId']});n=len(pauses);await cdp.send('Debugger.stepOut')
 for _ in range(1500):
  if len(pauses)>n:break
  await asyncio.sleep(.01)
 assert len(pauses)>n,'Old changeRole continuation did not prove stepOut completion';exit_pause=pauses[-1];assert exit_pause['callFrames'][0]['functionName']!='changeRole';await cdp.send('Debugger.resume');await e.p.evaluate('() => Promise.resolve()')
 stack_calls=[z for z in initiators if z['path']=='/api/session'];assert len(stack_calls)==2
 e.check('旧响应发起栈归属changeRole且被消费后stepOut离开函数，恢复后微任务完成',all('changeRole' in json.dumps(z['initiator']) for z in stack_calls),{'session_initiators':stack_calls,'read_only_guard_locals':values,'guard_location':frame['location'],'expected_generated_location':loc,'completion_location':exit_pause['callFrames'][0]['location'],'completion_function':exit_pause['callFrames'][0]['functionName'],'completion_reason':exit_pause.get('reason'),'completion_proof':'Debugger.paused on old guard return; localtoken<current in sameidentity/currentpending; stepOut paused in nonchangeRole frame; resume ACK and Promise.resolve execution-turn fence; no fixed sleep used'})
 after=await observe(e);later=e.events[index:];requests=[x for x in later if x['event']=='request'];st,latest,_=h.req(e.url,'/api/session',cookie=await e.cookie());member_status,member_body,_=h.req(e.url,'/api/members',cookie=await e.cookie())
 e.check('释放真正旧role session不能覆盖新pending身份/菜单/错误/toast或再发业务请求',after==before and not requests and session_count==2 and after['user']==latest['user'] and after['user']['role']=='member' and after['identityPending'] and not after['manage'] and after['page']=='spaces' and after['scope']=='mine' and after['loadError']==before['loadError'] and after['toast']==before['toast'] and st==200 and member_status==403 and e.snapshot()==snapshot,{'before':before,'after':after,'browser_requests_after_release':requests,'events_after_release':later,'actual_latest_session':latest,'members_status':member_status,'business_before':snapshot,'business_after':e.snapshot()})
 await e.shot('old-role-session-released-still-latest-pending');retry_index=len(e.events);await e.p.locator('[data-refresh]').click()
 await e.p.wait_for_function('() => state.user?.role==="member" && !state.identityPending && !state.loading && !state.loadError && !!document.querySelector("#filter-date") && !document.querySelector("nav [data-page=manage]")')
 final=await observe(e);current_status,current,_=h.req(e.url,'/api/session',cookie=await e.cookie());current_ms,current_mb,_=h.req(e.url,'/api/members',cookie=await e.cookie());recovery=[x for x in e.events[retry_index:] if x['event']=='recovery_session_actual_response'];retry_requests=[x for x in e.events[retry_index:] if x['event']=='request']
 e.check('原生retry确实重新读当前session及业务，清pending/错误且member无管理权限',current_status==200 and current_ms==403 and final['user']==current['user'] and final['user']['id']==1 and final['user']['role']=='member' and final['page']=='spaces' and final['scope']=='mine' and not final['manage'] and not final['identityPending'] and not final['loading'] and not final['loadError'] and final['openDialogs']==0 and len(recovery)==1 and recovery[0]['status']==200 and recovery[0]['body']['user']==current['user'] and any(x['path']=='/api/session' for x in retry_requests) and any(x['path'].startswith('/api/rooms?') for x in retry_requests) and any(x['path']=='/api/bookings?scope=mine' for x in retry_requests) and any(x['path']=='/api/notifications' for x in retry_requests) and not any(x['path']=='/api/members' for x in retry_requests) and e.snapshot()==snapshot,{'UI':final,'actual_session':current,'members_status':current_ms,'recovery':recovery,'browser_requests':retry_requests,'before':snapshot,'after':e.snapshot()})
 await e.shot('native-retry-complete');await cdp.detach()
async def main(args):
 root=Path.cwd();out=Path(args.output).resolve();out.relative_to((root/'tests/delivery-acceptance').resolve());out.mkdir(parents=True,exist_ok=True)
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==REV
 assert sha(root/'app/server.py')==SERVER_SHA and sha(root/'web/app.js')==JS_SHA
 assert args.coverage_transparent_instrumentation and (out/'instrumented-app.js').exists(),'Explicit transparent instrumented coverage mode required'
 os.environ['MEETSPACE_COVERAGE_AUDIT']=str(out)
 global h,LOCATIONS
 LOCATIONS=json.loads((Path(__file__).resolve().parent/'locations.json').read_text())
 import identity_env as h
 binding=json.loads((Path(__file__).resolve().parents[1]/'approved-design-binding.json').read_text());names={x['key'] for x in binding['matrix_checks']};results=[]
 from playwright.async_api import async_playwright
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for new_fault in ['503','network']:
   for old_result in ['200','503','network']:
    name=f'old-changeRole-session-{old_result}-after-new-self-session-{new_fault}-pending';assert name in names;e=h.Env();row={'name':name,'source_revision':REV,'source_sha256':h.HASHES,'design_binding':binding,'scope':'transparent Istanbul collector with passive CDP continuation completion; pure/instrumented SHA verified; no formal result','status':'unproven'}
    try:
     await e.start(browser,name,'admin',True);assert e.fixture_hashes['web/app.js']==JS_SHA and sha(e.dir/'web/app.js')==sha(out/'instrumented-app.js')
     await one(e,new_fault,old_result);row['status']='passed' if e.checks and all(x['passed'] for x in e.checks) else 'failed'
    except Exception as ex:row['error']=str(ex);row['traceback']=traceback.format_exc()
    finally:
     row.update({'browser':browser.version,'fixture_source_sha256':getattr(e,'fixture_hashes',{}),'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[]),'final_business_snapshot':e.snapshot() if getattr(e,'db',None) else None});file=out/(name+'.json');file.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');results.append({'name':name,'status':row['status'],'evidence':file.name});(out/'results.json').write_text(json.dumps({'source_revision':REV,'source_sha256':h.HASHES,'execution_role':'coverage collector only, not formal Tester/Reviewer','formal_results_not_written':True,'results':results},ensure_ascii=False,indent=2)+'\n');print(name,row['status'],row.get('error',''),flush=True)
     try:await e.close()
     except Exception:pass
  await browser.close()
 assert sha(root/'web/app.js')==JS_SHA and sha(root/'app/server.py')==SERVER_SHA
 if any(x['status']!='passed' for x in results):raise SystemExit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);p.add_argument('--coverage-transparent-instrumentation',action='store_true',required=True);asyncio.run(main(p.parse_args()))
