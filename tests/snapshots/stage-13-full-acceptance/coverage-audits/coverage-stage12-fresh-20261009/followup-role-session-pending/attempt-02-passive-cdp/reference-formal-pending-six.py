import asyncio,json,os,traceback
from pathlib import Path
OUT=Path(__file__).resolve().parents[2]/'evidence/pending-six';OUT.mkdir(exist_ok=True);os.environ['MEETSPACE_COVERAGE_AUDIT']=str(OUT)
import identity_env as h
from playwright.async_api import async_playwright
async def wait(predicate):
 for _ in range(1500):
  if predicate():return
  await asyncio.sleep(.01)
 raise TimeoutError('barrier missing')
async def obs(e):
 o=await e.observe();o.update(await e.p.evaluate('() => ({identityPending:state.identityPending,identityGeneration:state.identityGeneration,roleRefreshToken:state.roleRefreshToken,loadToken:state.loadToken})'));return o
async def one(e,new,old):
 await e.nav('manage');cdp=await e.ctx.new_cdp_session(e.p);await cdp.send('Network.enable');await cdp.send('Debugger.enable');initiators=[];pauses=[]
 cdp.on('Network.requestWillBeSent',lambda x:initiators.append({'request_id':x['requestId'],'path':x['request']['url'].replace(e.url,''),'initiator':x.get('initiator',{})}) if '/api/' in x['request']['url'] else None)
 cdp.on('Debugger.paused',lambda x:pauses.append(x))
 held=[];count=0
 async def route(r):
  nonlocal count
  count+=1
  if count==1:
   response=await r.fetch();assert response.status==200 and (await response.json())['user']['role']=='admin';held.append((r,response));e.events.append({'event':'S_old_actual_admin200_held','roles':e.roles(),'body':await response.json()})
  elif count==2:
   e.events.append({'event':'S_new_current_self_session_fault','fault':new,'roles':e.roles()})
   if new=='503':await r.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'LATEST_PENDING_SELF_503'}))
   else:await r.abort('failed')
  else:await r.continue_()
 await e.p.route('**/api/session',route);await e.p.locator('[data-member="2"]').select_option('admin');await wait(lambda:len(held)==1);assert not await e.p.locator('[data-member="1"]').is_disabled();await e.p.locator('[data-member="1"]').select_option('member');await e.p.wait_for_function('() => state.user?.role === "member" && state.identityPending && !!state.loadError && !state.loading && !!document.querySelector(".retry-panel")');before=await obs(e);before_db=e.snapshot();idx=len(e.events);await e.shot('before-old-release')
 # Conditional read-only debugger pause identifies the actual old changeRole continuation.
 line=273 if old=='200' else 281
 bp=await cdp.send('Debugger.setBreakpointByUrl',{'url':e.url+'/app.js','lineNumber':line,'condition':'roleRefreshToken !== state.roleRefreshToken'})
 r,response=held[0]
 if old=='200':await r.fulfill(response=response)
 elif old=='503':await r.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'OLDER_ROLE_SESSION_503'}))
 else:await r.abort('failed')
 await wait(lambda:len(pauses)>0);p=pauses[-1];frame=p['callFrames'][0];assert frame['functionName']=='changeRole';vals=await cdp.send('Debugger.evaluateOnCallFrame',{'callFrameId':frame['callFrameId'],'expression':'({old:roleRefreshToken,current:state.roleRefreshToken,identity:identityGeneration,currentIdentity:state.identityGeneration})','returnByValue':True});assert vals['result']['value']['old']<vals['result']['value']['current'];assert vals['result']['value']['identity']==vals['result']['value']['currentIdentity'];await cdp.send('Debugger.removeBreakpoint',{'breakpointId':bp['breakpointId']});n=len(pauses);await cdp.send('Debugger.stepOut');await wait(lambda:len(pauses)>n);exit_pause=pauses[-1];assert exit_pause['callFrames'][0]['functionName']!='changeRole';await cdp.send('Debugger.resume');await e.p.evaluate('() => Promise.resolve()');after=await obs(e);later=e.events[idx:];st,s,_=h.req(e.url,'/api/session',cookie=await e.cookie());ms,mb,_=h.req(e.url,'/api/members',cookie=await e.cookie());stack_calls=[z for z in initiators if z['path']=='/api/session'];assert len(stack_calls)==2
 e.check('两个session发起栈均为changeRole而非loadPage',all('changeRole' in json.dumps(z['initiator']) for z in stack_calls),stack_calls)
 e.check('旧continuation已返回且pending最新UI与数据库不变',before==after and before_db==e.snapshot() and not later and st==200 and s['user']['role']=='member' and ms==403 and mb.get('code')=='forbidden',{'before':before,'after':after,'old_guard_locals':vals['result']['value'],'guard_location':frame['location'],'completion_location':exit_pause['callFrames'][0]['location'],'completion_function':exit_pause['callFrames'][0]['functionName'],'events_after_release':later,'session':s,'members_status':ms,'members_body':mb,'database_before':before_db,'database_after':e.snapshot()});await e.shot('after-old-consumed')
 await e.p.locator('[data-refresh]').click();await e.p.wait_for_function('() => state.user?.role === "member" && !state.identityPending && !state.loading && !state.loadError && !!document.querySelector("#filter-date")');after=await obs(e);e.check('原生重试重新session恢复member且无业务变化',count==3 and not after['manage'] and after['page']=='spaces' and after['scope']=='mine' and before_db==e.snapshot(),{'after':after,'session_requests':count,'events':e.events});await e.shot('recovered');await cdp.detach()
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for new in ['503','network']:
   for old in ['200','503','network']:
    name=f'old-changeRole-session-{old}-after-new-self-session-{new}-pending';e=h.Env();o={'name':name,'revision':h.REV,'source_sha256':h.HASHES,'mode':'real local app with separately labelled frontend 503/abort fault injection','status':'unproven'}
    try:
     await e.start(browser,name,'admin',False);await one(e,new,old);o['status']='passed' if all(x['passed'] for x in e.checks) else 'failed'
    except Exception as ex:o.update(error=str(ex),traceback=traceback.format_exc())
    finally:
     o.update(checks=e.checks,events=e.events,screenshots=e.shots);(OUT/(name+'.json')).write_text(json.dumps(o,ensure_ascii=False,indent=2));results.append({'name':name,'status':o['status'],'evidence':name+'.json'});(OUT/'results.json').write_text(json.dumps({'results':results},indent=2));print(name,o['status'],o.get('error',''),flush=True)
     try:await e.close()
     except Exception:pass
  await browser.close()
asyncio.run(main())
