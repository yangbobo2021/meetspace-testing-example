"""Coverage-cycle UI identity matrix; all product sources are isolated copies.
Faults affect time, sessions via real HTTP, or browser network dependency only.
"""
import asyncio, datetime, hashlib, importlib.util, json, os, platform, shutil, sqlite3, subprocess, sys, threading, time, types, urllib.request, urllib.error
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path.cwd()
L=ROOT/'tests/delivery-acceptance'; AUDIT=Path(os.environ.get('MEETSPACE_COVERAGE_AUDIT',str(L/'coverage-audits/coverage-20261009-stage08-r1')))
E=AUDIT/'ui-identity'; E.mkdir(parents=True,exist_ok=True)
T=datetime.datetime.fromisoformat('2030-04-10T09:00:00+08:00'); RESULTS=[]
REV=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
HASHES={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['app/server.py','app/__init__.py','web/app.js','web/index.html','web/style.css','tests/test_smoke.py']}
LEDGER_HASHES={f:hashlib.sha256((L/f).read_bytes()).hexdigest() for f in ['requirements.json','scenarios.json','methods.json']}

def req(url,path,method='GET',data=None,cookie=''):
 headers={'Content-Type':'application/json','Origin':url,'X-Meeting-App':'1'}
 if cookie: headers['Cookie']=cookie
 r=urllib.request.Request(url+path,data=None if data is None else json.dumps(data).encode(),headers=headers,method=method)
 try: resp=urllib.request.urlopen(r,timeout=8)
 except urllib.error.HTTPError as ex:resp=ex
 with resp:
  body=resp.read(); status=resp.status; cookies=resp.headers.get('Set-Cookie','').split(';')[0]
  try: value=json.loads(body)
  except ValueError:value={'non_json':body.decode(errors='replace')[:200]}
  return status,value,cookies

class TimedEvents(list):
 def append(self,event):
  event={**event,"monotonic_seconds":time.monotonic()}; super().append(event)

class Env:
 async def start(self,browser,name,who='admin',second_admin=False):
  self.name=name; self.dir=AUDIT/('isolated-ui-identity-'+name)
  if self.dir.exists(): shutil.rmtree(self.dir)
  for folder in ['app','web']:shutil.copytree(ROOT/folder,self.dir/folder,ignore=shutil.ignore_patterns('__pycache__'))
  self.fixture_hashes={f:hashlib.sha256((self.dir/f).read_bytes()).hexdigest() for f in HASHES if f.startswith(('app/','web/'))}
  assert all(self.fixture_hashes[f]==HASHES[f] for f in self.fixture_hashes),'隔离原源码SHA不匹配'
  instrument=AUDIT/'instrumented-app.js'
  if instrument.exists():
   shutil.copyfile(instrument,self.dir/'web/app.js')
   self.fixture_hashes['instrumented_web/app.js']=hashlib.sha256((self.dir/'web/app.js').read_bytes()).hexdigest()
  spec=importlib.util.spec_from_file_location('ui_identity_'+name.replace('-','_'),self.dir/'app/server.py'); self.mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
  self.now=T
  env=self
  class Clock(datetime.datetime):
   @classmethod
   def now(cls,tz=None):return env.now.astimezone(tz) if tz else env.now.replace(tzinfo=None)
  self.mod.datetime=Clock; self.mod.time=types.SimpleNamespace(time=lambda:self.now.timestamp())
  self.db=self.dir/'test.sqlite'; self.server=self.mod.ApplicationServer(('127.0.0.1',0),self.mod.Store(self.db)); threading.Thread(target=self.server.serve_forever,daemon=True).start(); self.url=f'http://127.0.0.1:{self.server.server_port}'
  self.events=TimedEvents(); self.responses=TimedEvents(); self.checks=[]; self.shots=[]
  if second_admin:
   c=self.api_login('admin'); st,body,_=req(self.url,'/api/members/3','PATCH',{'role':'admin'},c); assert st==200,(st,body)
   self.events.append({'event':'second_admin_real_patch','status':st,'roles':self.roles()})
  self.ctx=await browser.new_context(viewport={'width':1280,'height':900},timezone_id='Asia/Shanghai'); self.p=await self.ctx.new_page(); self.p.set_default_timeout(10000); await self.p.clock.set_fixed_time(T)
  self.p.on('request',lambda r:self.events.append({'event':'request','method':r.method,'path':r.url.replace(self.url,'')}))
  self.p.on('response',lambda r:self.responses.append({'method':r.request.method,'path':r.url.replace(self.url,''),'status':r.status}))
  await self.p.goto(self.url); await self.login(who); return self
 def api_login(self,who,cookie=''):
  st,b,c=req(self.url,'/api/login','POST',{'email':who+'@meetspace.test','password':'MeetSpace!2026'},cookie); assert st==200,(st,b);return c
 async def login(self,who):
  await self.p.locator('[data-account='+who+']').click(); await self.p.locator('#login-form button[type=submit]').click(); await self.ready()
 async def ready(self):await self.p.wait_for_function('() => state.user && !state.loading && !state.loadError')
 async def settled(self):await self.p.wait_for_function('() => !state.user || !state.loading')
 async def nav(self,where):await self.p.locator('nav [data-page='+where+']').click();await self.ready()
 async def cookie(self):return '; '.join(c['name']+'='+c['value'] for c in await self.ctx.cookies(self.url))
 def roles(self):
  with sqlite3.connect(self.db) as c:return [list(row) for row in c.execute('select id,role from users order by id')]
 def snapshot(self):
  with sqlite3.connect(self.db) as c:return {tab:[list(row) for row in c.execute(sql)] for tab,sql in {'roles':'select id,team_id,role from users order by id','rooms':'select id,team_id,name,location,capacity,equipment,active from rooms order by id','bookings':'select id,room_id,user_id,title,start,end,status from bookings order by id','notifications':'select id,user_id,booking_id,message,read from notifications order by id'}.items()}
 async def observe(self):return await self.p.evaluate('() => ({user:state.user,page:state.page,scope:state.scope,date:state.date,loading:state.loading,loadError:state.loadError,login:!!document.querySelector("#login-form"),manage:!!document.querySelector("nav [data-page=manage]"),openDialogs:document.querySelectorAll("dialog[open]").length,toast:document.querySelector("#toast").textContent,text:document.querySelector("#app").innerText,retry:!!document.querySelector("[data-refresh]")})')
 def check(self,label,condition,actual):self.checks.append({'assertion':label,'passed':bool(condition),'actual':actual})
 async def shot(self,label):
  path=E/(self.name+'-'+label+'.png');await self.p.screenshot(path=str(path),full_page=True);self.shots.append(str(path.relative_to(AUDIT)))
 async def invalidate(self,kind='revocation'):
  cookie=await self.cookie(); token=dict(part.split('=',1) for part in cookie.split('; ') if '=' in part).get('meetspace_session',''); digest=hashlib.sha256(token.encode()).hexdigest()
  with sqlite3.connect(self.db) as c:row=c.execute('select user_id,expires from sessions where token_hash=?',(digest,)).fetchone()
  assert row,'目标旧会话不存在'
  if kind=='expiry':self.now=datetime.datetime.fromtimestamp(row[1],T.tzinfo); after={'exists':True,'usable':row[1]>self.now.timestamp()}
  else:
   st,b,newcookie=req(self.url,'/api/login','POST',{'email':'admin@meetspace.test' if row[0]==1 else 'alice@meetspace.test','password':'MeetSpace!2026'},cookie);assert st==200,(st,b)
   with sqlite3.connect(self.db) as c:old=c.execute('select 1 from sessions where token_hash=?',(digest,)).fetchone()
   assert not old,'重新登录没有撤销旧摘要'; assert newcookie!=cookie,'未生成新会话'
   assert await self.cookie()==cookie,'新cookie错误进入目标浏览器';after={'exists':False,'usable':False,'new_cookie_remained_separate':True}
  self.events.append({'event':'real_session_'+kind,'user_id':row[0],'expires':row[1],'server_time':self.now.timestamp(),'old_session':after,'cookie_values_recorded':False})
 async def close(self):
  await self.ctx.close();self.server.shutdown();self.server.server_close()
 def seed_booking(self,who,title,day,room=4,hour='10'):
  cookie=self.api_login(who); st,b,_=req(self.url,'/api/bookings','POST',{'room_id':room,'title':title,'attendees':2,'start':day+'T'+hour+':00:00+08:00','end':day+'T'+str(int(hour)+1)+':00:00+08:00','idempotency_key':'coverage-cycle-'+who+'-'+title},cookie);assert st==201,(st,b)
  self.events.append({'event':'fixture_real_booking','who':who,'date':day,'status':st,'booking':b})

async def mark(e,mode):
 e.seed_booking('alice','U未读确认','2030-04-11');e.seed_booking('bob','V未读确认','2030-04-11',3,'09');await e.nav('inbox');before=e.snapshot();assert any(n[1]==2 and n[-1]==0 for n in before['notifications']);assert any(n[1]==3 and n[-1]==0 for n in before['notifications'])
 await e.invalidate(mode);idx=len(e.responses);await e.p.locator('#mark-read').click();await e.p.locator('#login-form').wait_for();await e.shot('real401-login');obs=await e.observe();new=e.responses[idx:]
 e.check('真实标已读401',any(x['path']=='/api/notifications/read' and x['status']==401 for x in new),new)
 e.check('失效回登录无旧workspace与成功提示',obs['login'] and obs['user'] is None and not obs['manage'] and obs['openDialogs']==0 and '通知已标为已读' not in obs['toast'],obs)
 e.check('U及另用户未读业务快照不变',e.snapshot()==before,{'before':before,'after':e.snapshot()})
 await e.login('alice');await e.nav('inbox');idx=len(e.responses);await e.p.locator('#mark-read').click();await e.ready();await e.p.wait_for_function('() => document.querySelector("#toast").textContent==="通知已标为已读"');after=e.snapshot()
 e.check('重新登录后真实已读恢复且另用户不变',any(x['path']=='/api/notifications/read' and x['status']==200 for x in e.responses[idx:]) and all(n[-1]==1 for n in after['notifications'] if n[1]==2) and [n for n in before['notifications'] if n[1]!=2]==[n for n in after['notifications'] if n[1]!=2],{'responses':e.responses[idx:],'after':after});await e.shot('recovered')

async def role_expiry(e,obj,phase):
 await e.nav('manage');target=1 if obj=='self' else 2;role='member' if obj=='self' else 'admin';before=e.snapshot();idx=len(e.responses);evstart=len(e.events)
 if phase=='before-patch':await e.invalidate()
 else:
  async def session_barrier(route):
   # This session fetch only starts after the real PATCH response completed.
   e.events.append({'event':'session_barrier_before_real_fetch','roles':e.roles()});await e.invalidate();response=await route.fetch();e.events.append({'event':'session_real_fetch','status':response.status});await route.fulfill(response=response)
  await e.p.route('**/api/session',session_barrier)
 await e.p.locator('[data-member="'+str(target)+'"]').select_option(role);await e.p.locator('#login-form').wait_for();await e.shot('expired-login');obs=await e.observe();rs=e.responses[idx:];after=e.snapshot()
 expected_role=(before['roles'][target-1][-1] if phase=='before-patch' else role)
 e.check('目标真实401位于指定阶段',any(x['status']==401 and x['path']==('/api/members/'+str(target) if phase=='before-patch' else '/api/session') for x in rs),rs)
 e.check('角色commit或拒绝状态符合故障时点',after['roles'][target-1][-1]==expected_role,{'before':before,'after':after,'expected_role':expected_role})
 expected_snapshot=json.loads(json.dumps(before));expected_snapshot['roles'][target-1][-1]=expected_role
 e.check('仅目标角色可能提交且其他业务记录不变',after==expected_snapshot,{'expected':expected_snapshot,'actual':after})
 e.check('清user回登录且catch无旧workspace加载',obs['user'] is None and obs['login'] and not any(x['event']=='request' and x['path'].startswith(('/api/rooms','/api/bookings','/api/notifications','/api/members?')) for x in e.events[evstart:]),{'UI':obs,'events':e.events[evstart:]})
 old_cookie=await e.cookie();st,b,_=req(e.url,'/api/members','GET',cookie=old_cookie);e.check('旧失效管理员会话真实拒绝',st==401,{'status':st,'body':b})
 await e.p.unroute('**/api/session');await e.login('admin');obs=await e.observe();currentrole=e.roles()[0][-1]
 e.check('重新登录身份导航数据符合实际角色',obs['user']['role']==currentrole and obs['manage']==(currentrole=='admin') and obs['page']=='spaces' and obs['scope']=='mine',obs)
 if currentrole=='member':
  st,b,_=req(e.url,'/api/members','GET',cookie=await e.cookie());e.check('合法降权会话管理员接口403',st==403,{'status':st,'body':b})
 await e.shot('recovered')

async def demotion(e,fault,recovery):
 await e.nav('manage');before=e.roles();idx=len(e.responses);armed=True
 async def fault_session(route):
  nonlocal armed
  if not armed:return await route.continue_()
  armed=False;e.events.append({'event':'frontend_session_fault_after_real_patch','fault':fault,'roles':e.roles()})
  if fault=='503':await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'注入身份查询不可用','code':'test_session_unavailable'}))
  else:await route.abort('failed')
 await e.p.route('**/api/session',fault_session);await e.p.locator('[data-member="1"]').select_option('member');await e.p.locator('.retry-panel').wait_for();obs=await e.observe();await e.shot('failure')
 e.check('真实自身PATCH提交且前端session故障',e.roles()[0][-1]=='member' and any(x['path']=='/api/members/1' and x['status']==200 for x in e.responses[idx:]) and not armed,{'before':before,'after':e.roles(),'responses':e.responses[idx:],'UI':obs})
 e.check('失败有反馈且没有修改成功或假回滚',bool(obs['toast']) and obs['toast']!='成员角色已更新' and e.roles()[0][-1]=='member' and obs['user']['role'] in ['admin','member'],obs)
 st,b,_=req(e.url,'/api/members','GET',cookie=await e.cookie());e.check('直连后台立即按member拒绝管理员操作',st==403,{'status':st,'body':b})
 await e.p.unroute('**/api/session');recovery_idx=len(e.events)
 if recovery=='data-retry':
  e.check('恢复按钮在实际DOM可操作',await e.p.locator('[data-refresh]').is_visible() and await e.p.locator('[data-refresh]').is_enabled(),obs);await e.p.locator('[data-refresh]').click();await e.ready()
 else:await e.p.reload();await e.ready()
 recovered=await e.observe();events=e.events[recovery_idx:]
 e.check('指定恢复读取session并恢复最新member导航数据',any(x['event']=='request' and x['path']=='/api/session' for x in events) and recovered['user']['role']=='member' and not recovered['manage'] and recovered['page']=='spaces' and recovered['scope']=='mine' and not recovered['loadError'],{'events':events,'UI':recovered});await e.shot('specified-recovery')
 if recovery=='data-retry':await e.p.reload();await e.ready();e.events.append({'event':'cleanup_reload_after_specified_data_retry','UI':await e.observe()})

async def success_control(e):
 await e.nav('manage');await e.p.locator('[data-member="1"]').select_option('member');await e.ready();await e.p.wait_for_function('() => state.user.role==="member"');obs=await e.observe();e.check('正常自降对照真实提交并撤管理员菜单',e.roles()[0][-1]=='member' and obs['user']['role']=='member' and not obs['manage'] and obs['page']=='spaces',obs);await e.shot('normal-self-demotion')

async def other_fail_control(e):
 await e.nav('manage');before=e.snapshot()
 async def reject_patch(route):await route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'注入他人角色PATCH不可用','code':'test_other_patch_unavailable'}))
 await e.p.route('**/api/members/2',reject_patch);await e.p.locator('[data-member="2"]').select_option('admin');await e.ready();await e.p.wait_for_function('() => document.querySelector("#toast").textContent==="注入他人角色PATCH不可用"');obs=await e.observe();e.check('他人修改失败对照保留本人admin和角色不变',e.snapshot()==before and obs['user']['role']=='admin' and obs['manage'] and obs['toast']!='成员角色已更新',{'before':before,'after':e.snapshot(),'UI':obs});await e.p.unroute('**/api/members/2');await e.shot('other-patch-failure-control')

async def date_filter(e):
 e.seed_booking('alice','D加一独有预约','2030-04-12');await e.p.locator('#filter-date').fill('2030-04-11');await e.p.locator('#filter-date').press('Tab');await e.ready();await e.p.locator('.room-agenda summary').first.click();before=e.snapshot();obs=await e.observe();e.check('正常D预约对照','品牌方向讨论' in obs['text'],obs)
 await e.p.evaluate('() => {window.dateChanges=[]; document.addEventListener("change",ev=>{if(ev.target.id==="filter-date")window.dateChanges.push({value:ev.target.value,trusted:ev.isTrusted,date:state.date})},true)}');idx=len(e.events);await e.p.locator('#filter-date').fill('');await e.p.locator('#filter-date').press('Tab');await e.p.wait_for_timeout(150);obs=await e.observe();events=e.events[idx:];changes=await e.p.evaluate('window.dateChanges');value=await e.p.locator('#filter-date').input_value()
 e.check('真实空值change且guard不更新日期或查询',any(x['value']=='' for x in changes) and value=='' and obs['date']=='2030-04-11' and not any(x['event']=='request' and x['path'].startswith('/api/rooms?') for x in events),{'value':value,'changes':changes,'UI':obs,'events':events});await e.shot('date-empty')
 idx=len(e.responses);await e.p.locator('#filter-date').fill('2030-04-12');await e.p.locator('#filter-date').press('Tab');await e.ready();await e.p.locator('.room-agenda summary').first.click();obs=await e.observe();st,b,_=req(e.url,'/api/rooms?date=2030-04-12','GET',cookie=await e.cookie())
 e.check('有效D加一真实查询日程一致且业务无写',obs['date']=='2030-04-12' and await e.p.locator('#filter-date').input_value()=='2030-04-12' and 'D加一独有预约' in obs['text'] and '品牌方向讨论' not in obs['text'] and any(x['path']=='/api/rooms?date=2030-04-12' and x['status']==200 for x in e.responses[idx:]) and st==200 and b['date']=='2030-04-12' and before==e.snapshot(),{'UI':obs,'direct_api':b,'responses':e.responses[idx:],'before':before,'after':e.snapshot()});await e.shot('date-recovered')

def save(browser_version):
 groups={sid:[x for x in RESULTS if x['scenario_id']==sid] for sid in set(x['scenario_id'] for x in RESULTS)};expected={'WB-ui-mark-read-session-expiry':2,'WB-ui-role-update-session-expiry':4,'WB-ui-self-demotion-session-failure':6,'WB-ui-date-filter-empty-recovery':1}
 results=[]
 for sid,items in groups.items():
  status='failed' if any(x['status']=='failed' for x in items) else 'passed' if len(items)==expected[sid] and all(x['status']=='passed' for x in items) else 'unproven'
  results.append({'scenario_id':sid,'method_ids':['AI-'+sid],'status':status,'actual':f'独立项{len(items)}/{expected[sid]}，通过{sum(x["status"]=="passed" for x in items)}，失败{sum(x["status"]=="failed" for x in items)}，未证明{sum(x["status"]=="unproven" for x in items)}；前端故障仅证明UI；401来自实际会话撤销或精确到期。','evidence':[x['evidence'] for x in items]})
 (AUDIT/'ui-identity-results.json').write_text(json.dumps({'revision':REV,'source_hashes':HASHES,'ledger_hashes':LEDGER_HASHES,'environment':{'python':sys.version,'platform':platform.platform(),'browser':browser_version,'fixed_clock':T.isoformat(),'isolation':'each matrix item separate exact source copy/database/anonymous listener/context','front_fault':'503/abort only designated frontend network dependency; true 401 from server'},'results':results,'matrix':RESULTS},ensure_ascii=False,indent=2)+'\n')

async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True);bv=browser.version
  cases=[('mark-'+mode,'WB-ui-mark-read-session-expiry',mark,(mode,),'alice',False) for mode in ['expiry','revocation']]
  cases += [('role-'+obj+'-'+phase,'WB-ui-role-update-session-expiry',role_expiry,(obj,phase),'admin',True) for obj in ['self','other'] for phase in ['before-patch','after-commit']]
  cases += [('demote-'+fault+'-'+recovery,'WB-ui-self-demotion-session-failure',demotion,(fault,recovery),'admin',True) for fault in ['503','network'] for recovery in ['data-retry','reload']]
  cases += [('demote-normal-control','WB-ui-self-demotion-session-failure',success_control,(),'admin',True),('other-patch-failure-control','WB-ui-self-demotion-session-failure',other_fail_control,(),'admin',True),('date-empty-recovery','WB-ui-date-filter-empty-recovery',date_filter,(),'alice',False)]
  for name,sid,func,args,who,second_admin in cases:
   e=Env();obs={'name':name,'scenario_id':sid,'method_id':'AI-'+sid,'clock':T.isoformat(),'source_hashes':HASHES};status='unproven'
   try:
    await e.start(browser,name,who,second_admin);await func(e,*args);status='passed' if all(c['passed'] for c in e.checks) else 'failed'
   except Exception as ex:
    import traceback
    obs['harness_error']=type(ex).__name__+': '+str(ex);obs['traceback']=traceback.format_exc()
    if getattr(e,'p',None):
     try:obs['error_observation']=await e.observe();await e.shot('harness-error')
     except Exception:pass
   finally:
    obs.update({'status':status,'fixture_source_hashes':getattr(e,'fixture_hashes',{}),'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[])})
    path=E/(name+'.json');path.write_text(json.dumps(obs,ensure_ascii=False,indent=2)+'\n');RESULTS.append({'name':name,'scenario_id':sid,'status':status,'evidence':str(path.relative_to(AUDIT))});save(bv)
    try:await e.close()
    except Exception:pass
    print(name,status,obs.get('harness_error',''),flush=True)
  await browser.close();save(bv)
if __name__=='__main__':asyncio.run(main())
