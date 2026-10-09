import asyncio, datetime, hashlib, json, platform, sqlite3, sys, threading, types
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path.cwd(); L=ROOT/'tests/delivery-acceptance'; R=L/'runs/dev-fix-races-r2'; E=R/'evidence/ui-races'; E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT)); import app.server as app
REAL=datetime.datetime; T=REAL.fromisoformat('2030-04-10T09:00:00+08:00'); NOW=T
class Clock(REAL):
 @classmethod
 def now(cls,tz=None): return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)
app.datetime=Clock; app.time=types.SimpleNamespace(time=lambda: NOW.timestamp())
BRANCHES=[]
class Env:
 async def start(self,browser,name):
  global NOW
  NOW=T; self.name=name; self.db=E/(name+'.sqlite'); self.db.unlink(missing_ok=True)
  self.server=app.ApplicationServer(('127.0.0.1',0),app.Store(self.db)); threading.Thread(target=self.server.serve_forever,daemon=True).start(); self.url=f'http://127.0.0.1:{self.server.server_port}'
  self.ctx=await browser.new_context(viewport={'width':1280,'height':900},timezone_id='Asia/Shanghai'); self.p=await self.ctx.new_page(); await self.p.clock.set_fixed_time(T); self.p.set_default_timeout(8000); self.events=[]; self.holds=[]
  await self.p.goto(self.url); await self.login('alice')
  # Both dates have distinct real data; create the second using the running UI.
  await self.p.locator('[data-book-room="1"]').click()
  for k,v in {'title':'新日期独有主题','date':'2030-04-12','start':'10:00','end':'11:00','attendees':'2'}.items(): await self.p.locator(f'#booking-form [name={k}]').fill(v)
  await self.p.locator('#booking-form button[type=submit]').click(); await self.p.locator('#booking-dialog').wait_for(state='hidden'); await self.ready()
  await self.p.evaluate("""() => {window.raceChanges=[]; new MutationObserver(()=>window.raceChanges.push({at:performance.now(),text:document.querySelector('#app').innerText})).observe(document.querySelector('#app'),{childList:true,subtree:true,characterData:true});}""")
  self.queue=[]
  async def dispatcher(route):
   if not self.queue: return await route.continue_()
   h=self.queue.pop(0); label=h['label']; outcome=h['outcome']
   response=await route.fetch(); h['status']=response.status; h['body']=await response.json(); self.events.append({'event':'captured','label':label,'path':route.request.url.replace(self.url,''),'real_status':response.status}); h['got'].set()
   await h['release'].wait()
   if outcome=='network-failure': await route.abort('failed')
   else: await route.fulfill(response=response)
   self.events.append({'event':'released','label':label,'outcome':outcome,'real_status':response.status}); h['done'].set()
  await self.p.route('**/api/rooms?*',dispatcher)
  return self
 async def login(self,who):
  await self.p.locator(f'[data-account={who}]').click(); await self.p.locator('#login-form button[type=submit]').click(); await self.ready()
 async def ready(self): await self.p.locator('#filter-date').wait_for() if False else await self.p.wait_for_function('() => typeof state!=="undefined" && state.user && !state.loading && !state.loadError')
 async def nav(self,page): await self.p.locator(f'nav [data-page={page}]').click()
 async def date(self,value): await self.p.locator('#filter-date').fill(value)
 async def hold_next(self,label,outcome='success'):
  h={'label':label,'outcome':outcome,'got':asyncio.Event(),'release':asyncio.Event(),'done':asyncio.Event()}; self.holds.append(h)
  self.queue.append(h)
  return h
 async def release(self,h): h['release'].set(); await asyncio.wait_for(h['done'].wait(),8); await self.p.wait_for_timeout(80)
 async def shot(self,label):
  p=E/(self.name+'-'+label+'.png'); await self.p.screenshot(path=str(p),full_page=True); return str(p.relative_to(R))
 async def observe(self):
  return await self.p.evaluate("""() => ({text:document.querySelector('#app').innerText,selected:document.querySelector('nav [aria-current]')?.dataset.page,date:document.querySelector('#filter-date')?.value,loading:document.querySelector('#app').innerText.includes('正在同步工作空间'),error:document.querySelector('.retry-panel')?.innerText,login:!!document.querySelector('#login-form'),openDialogs:document.querySelectorAll('dialog[open]').length,whiteBox:{token:state.loadToken,page:state.page,date:state.date,user:state.user?.email,loading:state.loading,error:state.loadError}})""")
 def snapshot(self):
  with sqlite3.connect(self.db) as c:
   return {t:c.execute(q).fetchall() for t,q in {'bookings':'select id,room_id,user_id,title,start,end,status from bookings','notifications':'select id,user_id,booking_id,read from notifications','rooms':'select id,name,active from rooms','users':'select id,team_id,role from users'}.items()}
 async def close(self):
  for h in self.holds: h['release'].set()
  await self.ctx.close(); self.server.shutdown(); self.server.server_close()

async def pair(e,kind,old_out,new_out,order):
 before=e.snapshot(); p=e.p
 old=await e.hold_next('O',old_out)
 if kind=='date': await e.date('2030-04-11')
 else: await e.nav('bookings')
 await asyncio.wait_for(old['got'].wait(),8)
 if kind=='date':
  # Loading removes the date control. Navigate through rendered pages before
  # selecting the second date; O remains pending throughout these real clicks.
  await e.nav('inbox'); await e.ready(); await e.nav('spaces'); await e.ready()
 new=await e.hold_next('N',new_out)
 if kind=='date': await e.date('2030-04-12')
 else: await e.nav('spaces')
 await asyncio.wait_for(new['got'].wait(),8)
 snapshots=[]; checks=[]
 def check(name,ok,actual): checks.append({'assertion':name,'passed':bool(ok),'actual':actual})
 current=await e.observe(); check('最新请求等待显示加载',current['loading'],current); snapshots.append(await e.shot('both-pending'))
 if order=='old-first':
  await e.release(old)
  samples=[]
  for _ in range(5): samples.append(await e.observe()); await p.wait_for_timeout(25)
  check('旧完成不改变新目标/错误/加载',all(x['loading'] and not x['error'] and x['whiteBox']['page']=='spaces' and x['whiteBox']['date']=='2030-04-12' for x in samples),samples)
  check('N仍被真实暂存',not new['done'].is_set(),e.events.copy()); snapshots.append(await e.shot('old-done-new-pending')); await e.release(new)
 else:
  await e.release(new); prior=await e.observe(); snapshots.append(await e.shot('new-done-old-pending')); await e.release(old); after=await e.observe(); check('旧响应晚到保持最新结果',prior==after,{'before':prior,'after':after})
 final=await e.observe(); check('最新结果结束加载且成功/错误匹配',not final['loading'] and bool(final['error'])==(new_out=='network-failure'),final)
 if new_out=='success':
  await p.locator('.room-agenda summary').first.click(); final=await e.observe()
  check('显示新日期/页面真实结果',final['selected']=='spaces' and final['date']=='2030-04-12' and '新日期独有主题' in final['text'] and '品牌方向讨论' not in final['text'],final)
 else:
  await p.locator('[data-refresh]').click(); await e.ready(); await p.locator('.room-agenda summary').first.click(); recovered=await e.observe(); check('用户重载恢复最新日期数据',recovered['date']=='2030-04-12' and '新日期独有主题' in recovered['text'],recovered)
 check('独立只读业务快照无副作用',before==e.snapshot(),{'before':before,'after':e.snapshot()}); snapshots.append(await e.shot('final'))
 return {'checks':checks,'screenshots':snapshots,'events':e.events,'dom_mutations':await p.evaluate('window.raceChanges')}

async def identity_race(e,mode):
 global NOW
 p=e.p; before=e.snapshot(); checks=[]; shots=[]
 def check(name,ok,actual):checks.append({'assertion':name,'passed':bool(ok),'actual':actual})
 if mode=='old401-new-session':
  NOW=T+datetime.timedelta(hours=8); old=await e.hold_next('O-expired-actual-401'); await e.nav('bookings'); await asyncio.wait_for(old['got'].wait(),8)
  check('旧请求实际服务401',old['status']==401,{'status':old['status'],'body':old['body']})
  # Other requests from the expired generation deliver 401 and expose login UI.
  await p.locator('#login-form').wait_for(); await e.login('bob'); proof=await e.ctx.request.get(e.url+'/api/session'); business=await e.ctx.request.get(e.url+'/api/bookings?scope=mine'); proof_json=await proof.json()
  check('N新身份与业务确实有效',proof.status==200 and proof_json['user']['email']=='bob@meetspace.test' and business.status==200,{'identity':proof_json,'business_status':business.status})
  shots.append(await e.shot('N-valid-before-O401')); await e.release(old); actual=await e.observe(); shots.append(await e.shot('after-O401'))
  still=await e.ctx.request.get(e.url+'/api/session'); check('旧O的401不得撤销仍有效N界面',not actual['login'] and actual['whiteBox']['user']=='bob@meetspace.test',{'UI':actual,'N_server_status':still.status,'N_server_identity':await still.json()})
 elif mode=='current401-old-token':
  # Hold every expired response; release one older load only after a newer
  # real UI navigation has incremented loadToken.
  NOW=T+datetime.timedelta(hours=8); held=[]
  async def capture(route):
   response=await route.fetch(); body=await response.body(); h={'label':'current-N-'+str(len(held)),'status':response.status,'release':asyncio.Event(),'done':asyncio.Event()}; held.append(h); e.holds.append(h)
   e.events.append({'event':'captured','label':h['label'],'path':route.request.url.replace(e.url,''),'real_status':response.status})
   await h['release'].wait(); await route.fulfill(status=response.status,headers=response.headers,body=body); h['done'].set()
  await p.route('**/api/**',capture); await e.nav('bookings')
  for _ in range(160):
   if len(held)>=3: break
   await p.wait_for_timeout(25)
  old_state=await e.observe(); await e.nav('spaces')
  for _ in range(160):
   if len(held)>=6: break
   await p.wait_for_timeout(25)
  new_state=await e.observe(); check('同身份较新loadToken已发起且所有响应暂存',len(held)>=6 and new_state['whiteBox']['token']>old_state['whiteBox']['token'],{'old':old_state,'new':new_state,'response_statuses':[h['status'] for h in held]})
  shots.append(await e.shot('expired-N-newer-load-pending')); await e.release(held[0]); await p.locator('#login-form').wait_for(); actual=await e.observe()
  check('当前失效N的旧token401仍清身份回登录',actual['login'] and actual['openDialogs']==0,actual); shots.append(await e.shot('expired-N-old401-login'))
 elif mode.startswith('logout-') or mode.startswith('relogin-'):
  outcome='network-failure' if mode.endswith('failure') else 'success'; old=await e.hold_next('O',outcome); await e.nav('bookings'); await asyncio.wait_for(old['got'].wait(),8)
  await p.locator('[data-logout]:visible').first.click(); await p.locator('#login-form').wait_for()
  if mode.startswith('relogin-'): await e.login('other')
  prior=await e.observe(); shots.append(await e.shot('before-old')); await e.release(old); actual=await e.observe()
  check('退出/新登录后旧成功或非401错误不可恢复旧空间',prior==actual,{'before':prior,'after':actual}); shots.append(await e.shot('after-old'))
 check('只读业务数据未改变',before==e.snapshot(),{'before':before,'after':e.snapshot()})
 return {'checks':checks,'screenshots':shots,'events':e.events,'dom_mutations':await p.evaluate('window.raceChanges')}

def save():
 bb=[b for b in BRANCHES if b['group']=='ordering']; wb=BRANCHES
 results=[]; methods=[]
 for sid,mid,branches,expected in [('BB-interface-experience-3','AI-interface-experience-3',bb,16),('WB-ui-load-token-races','AI-WB-ui-load-token-races',wb,22)]:
  fail=any(b['status']=='failed' for b in branches); complete=len(branches)==expected and all(b['status']!='unproven' for b in branches)
  status='failed' if fail else ('passed' if complete else 'unproven'); actual=f'已执行 {len(branches)}/{expected} 独立分支；失败 {sum(b["status"]=="failed" for b in branches)}；加载响应来自真实服务，仅前端网络错误分支 route.abort。'
  ev=[b['evidence'] for b in branches]; methods.append({'method_id':mid,'status':status,'actual':actual,'evidence':ev}); results.append({'scenario_id':sid,'method_ids':[mid],'status':status,'actual':actual,'evidence':ev})
 (R/'ui-races-results.json').write_text(json.dumps({'revision':'2a43bbd87897f0cd815b7762ea45137db64ebf70','environment':{'python':sys.version,'platform':platform.platform(),'clock':T.isoformat(),'browser':BROWSER_VERSION,'target':'real application/SQLite; actual UI; real delayed responses; explicitly injected frontend network failures'},'method_results':methods,'results':results},ensure_ascii=False,indent=2)+'\n')
async def main():
 global BROWSER_VERSION
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True); BROWSER_VERSION=browser.version
  cases=[(f'{kind}-{old}-{new}-{order}','ordering',(kind,old,new,order)) for kind in ['date','navigation'] for old in ['success','network-failure'] for new in ['success','network-failure'] for order in ['old-first','new-first']]
  cases += [(mode,'identity',mode) for mode in ['old401-new-session','current401-old-token','logout-success','logout-failure','relogin-success','relogin-failure']]
  for name,group,args in cases:
   e=Env(); obs={'name':name,'group':group,'clock':T.isoformat()}
   try:
    await e.start(browser,name); obs.update(await pair(e,*args) if group=='ordering' else await identity_race(e,args)); status='passed' if all(x['passed'] for x in obs['checks']) else 'failed'
   except Exception as ex:
    import traceback
    obs['harness_error']=type(ex).__name__+': '+str(ex); obs['traceback']=traceback.format_exc(); status='unproven'
   finally:
    obs['status']=status; path=E/(name+'.json'); path.write_text(json.dumps(obs,ensure_ascii=False,indent=2)+'\n'); BRANCHES.append({'group':group,'name':name,'status':status,'evidence':str(path.relative_to(R))}); save()
    try: await e.close()
    except Exception: pass
    print(name,status,flush=True)
  await browser.close()
if __name__=='__main__':asyncio.run(main())
