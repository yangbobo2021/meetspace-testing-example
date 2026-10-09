"""Execute stage08 native-dialog and logout matrices; no production source edits."""
import asyncio, datetime, hashlib, importlib.util, json, os, shutil, sqlite3, threading, traceback
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path.cwd(); LEDGER=ROOT/'tests/delivery-acceptance'
BASE=Path(os.environ['MEETSPACE_COVERAGE_AUDIT']); E=BASE/'evidence/ui-dialogs'; E.mkdir(parents=True,exist_ok=True)
T=datetime.datetime.fromisoformat('2030-04-10T09:00:00+08:00')
class Clock(datetime.datetime):
 @classmethod
 def now(cls,tz=None): return T.astimezone(tz) if tz else T.replace(tzinfo=None)

def check(o,name,ok,actual): o.setdefault('checks',[]).append({'assertion':name,'passed':bool(ok),'actual':actual})
def snap(db):
 with sqlite3.connect(db) as c:
  return {t:c.execute(('SELECT id,team_id,email,name,role FROM users' if t=='users' else 'SELECT * FROM '+t)+' ORDER BY id').fetchall() for t in ['rooms','bookings','notifications','users']}

class Env:
 async def start(self,browser,name,width=1280,height=900):
  self.name=name; self.dir=BASE/('isolated-dialog-'+name); self.dir.mkdir(exist_ok=True)
  shutil.copytree(ROOT/'app',self.dir/'app',dirs_exist_ok=True); shutil.copytree(ROOT/'web',self.dir/'web',dirs_exist_ok=True)
  assert hashlib.sha256((ROOT/'web/app.js').read_bytes()).digest()==hashlib.sha256((self.dir/'web/app.js').read_bytes()).digest()
  spec=importlib.util.spec_from_file_location('dialog_'+name.replace('-','_'),self.dir/'app/server.py'); self.app=importlib.util.module_from_spec(spec); spec.loader.exec_module(self.app)
  self.app.datetime=Clock
  import types
  self.app.time=types.SimpleNamespace(time=lambda:T.timestamp())
  self.db=self.dir/'fixture.sqlite'; self.db.unlink(missing_ok=True)
  self.server=self.app.ApplicationServer(('127.0.0.1',0),self.app.Store(self.db)); threading.Thread(target=self.server.serve_forever,daemon=True).start()
  self.url=f'http://127.0.0.1:{self.server.server_port}'
  self.ctx=await browser.new_context(viewport={'width':width,'height':height},timezone_id='Asia/Shanghai'); self.p=await self.ctx.new_page(); self.p.set_default_timeout(7000); await self.p.clock.set_fixed_time(T)
  self.requests=[]; self.holds=[]
  self.p.on('request',lambda r:self.requests.append({'method':r.method,'path':r.url.replace(self.url,'')}))
  await self.p.goto(self.url); await self.login('admin')
  headers={'X-Meeting-App':'1','Origin':self.url}
  response=await self.ctx.request.post(self.url+'/api/bookings',headers=headers,data={'room_id':1,'title':'关闭确认用预约','start':'2030-04-12T10:00:00+08:00','end':'2030-04-12T11:00:00+08:00','attendees':2,'idempotency_key':'dialog-fixture-'+name})
  assert response.status==201,(response.status,await response.text()); self.bid=(await response.json())['booking']['id']
  await self.p.locator('nav [data-page=spaces]').click(); await self.ready()
  await self.p.evaluate("""() => {window.pointerEvidence=[];document.addEventListener('click',e=>{let d=e.target.closest('dialog'); if(d)window.pointerEvidence.push({target:e.target.tagName,targetId:e.target.id,dialog:d.id,isDialog:e.target===d,x:e.clientX,y:e.clientY,trusted:e.isTrusted,rect:d.getBoundingClientRect().toJSON()});},true)}""")
  return self
 async def ready(self): await self.p.wait_for_function('() => state.user && !state.loading && !state.loadError')
 async def login(self,who):
  await self.p.locator('[data-account='+who+']').click(); await self.p.locator('#login-form [type=submit]').click(); await self.ready()
 async def nav(self,target): await self.p.locator('nav [data-page='+target+']').click(); await self.ready()
 async def open(self,kind,navigate=True):
  target={'booking':'spaces','room':'manage','confirm':'bookings'}[kind]
  if navigate: await self.nav(target)
  selector={'booking':'[data-book-room="1"]','room':'#add-room','confirm':f'[data-cancel="{self.bid}"]'}[kind]
  await self.p.locator(selector).click(); await self.p.locator('#'+kind+'-dialog').wait_for(state='visible')
  if kind in ['booking','room']: await self.p.locator('#'+kind+'-form [name='+('title' if kind=='booking' else 'name')+']').fill('未提交修改')
 async def observe(self):
  return await self.p.evaluate("""() => ({user:state.user?.email||null,role:state.user?.role||null,page:state.page,scope:state.scope,token:state.loadToken,loading:state.loading,error:state.loadError,login:!!document.querySelector('#login-form'),open:[...document.querySelectorAll('dialog[open]')].map(d=>d.id),text:document.querySelector('#app').innerText,toast:document.querySelector('#toast').textContent})""")
 async def shot(self,name):
  f=E/(self.name+'-'+name+'.png'); await self.p.screenshot(path=str(f),full_page=True); return str(f.relative_to(BASE))
 async def close(self):
  for h in self.holds:h.set()
  await self.ctx.close(); self.server.shutdown(); self.server.server_close()

async def dialog_case(e,o,kind,gesture,width,height):
 await e.open(kind); p=e.p; d=p.locator('#'+kind+'-dialog'); before=snap(e.db); n=len(e.requests); rect=await d.bounding_box(); o['rect']=rect
 x=rect['x'];y=rect['y'];w=rect['width'];h=rect['height']; coords={'left':(x-3,y+h/2),'right':(x+w+3,y+h/2),'top':(x+w/2,y-3),'bottom':(x+w/2,y+h+3),'padding':(x+2,y+2)}
 if gesture in coords:
  cx,cy=coords[gesture];o['coordinates']=[cx,cy]
  if not (0<=cx<width and 0<=cy<height):
   o['viewport_unreachable']='该原生视口中此方向无可点击的屏幕区域；桌面同项另行实测。';o['status']='not_reachable_in_viewport';return
  await p.mouse.click(cx,cy)
 elif gesture=='X':await d.locator('[data-close]').first.click()
 elif gesture=='Escape':await p.keyboard.press('Escape')
 elif gesture=='retain':await d.get_by_role('button',name='保留预约').click()
 else:await d.locator('h2').click()
 should_close=gesture not in ['padding','child']; opened=await d.evaluate('(d)=>d.open')
 check(o,'关闭/内部不误关',opened!=should_close,{'open':opened,'expected_closed':should_close})
 events=await p.evaluate('window.pointerEvidence');o['pointer_events']=events
 if gesture in coords:
  check(o,'真实鼠标事件到达dialog自身',bool(events) and events[-1]['isDialog'] and events[-1]['trusted'],events[-1] if events else [])
 writes=[r for r in e.requests[n:] if r['method'] in ['POST','PATCH']]
 check(o,'未发送业务写请求',not writes,writes);check(o,'独立业务快照保持不变',snap(e.db)==before,{'before':before,'after':snap(e.db)})
 o['screenshots']=[await e.shot('after-action')]
 if opened:await p.keyboard.press('Escape')
 await e.open(kind);check(o,'再次原生打开可编辑',await d.is_visible(),await e.observe());await p.keyboard.press('Escape')

async def logout_case(e,o,kind,outcome):
 p=e.p; before=snap(e.db); sequence=[]; oldgot=asyncio.Event(); oldrelease=asyncio.Event(); olddone=asyncio.Event(); logoutgot=asyncio.Event(); logoutrelease=asyncio.Event(); logoutdone=asyncio.Event();e.holds += [oldrelease,logoutrelease]
 count=0
 async def rooms(route):
  nonlocal count
  count+=1
  if count!=1:return await route.continue_()
  r=await route.fetch(); sequence.append({'event':'old-real-rooms-captured','status':r.status});oldgot.set();await oldrelease.wait()
  if outcome=='success':await route.fulfill(response=r)
  else:await route.fulfill(status=503,content_type='application/json',body='{"error":"旧加载受控非401错误"}')
  sequence.append({'event':'old-response-released','outcome':outcome});olddone.set()
 await p.route('**/api/rooms?*',rooms)
 await p.locator('nav [data-page=inbox]').click();await asyncio.wait_for(oldgot.wait(),8);oldstate=await e.observe()
 await e.nav({'booking':'spaces','room':'manage','confirm':'bookings'}[kind]); latest=await e.observe()
 check(o,'第二次真实导航完成且旧加载仍被暂存',latest['token']>oldstate['token'] and not latest['loading'] and not olddone.is_set(),{'old':oldstate,'latest':latest})
 cookies=await e.ctx.cookies();oldcookie='; '.join(c['name']+'='+c['value'] for c in cookies)
 async def logout(route):
  r=await route.fetch();sequence.append({'event':'real-logout-processed-captured','status':r.status});logoutgot.set();await logoutrelease.wait();await route.fulfill(response=r);sequence.append({'event':'logout-released'});logoutdone.set()
 await p.route('**/api/logout',logout);await p.locator('[data-logout]:visible').first.click();await asyncio.wait_for(logoutgot.wait(),8)
 await e.open(kind,navigate=False);sequence.append({'event':'native-business-click-opened','state':await e.observe()});check(o,'真实退出等待期间原生点击打开弹窗',kind+'-dialog' in (await e.observe())['open'],await e.observe());o['screenshots']=[await e.shot('open-while-logout-held')]
 logoutrelease.set();await asyncio.wait_for(logoutdone.wait(),8);await p.locator('#login-form').wait_for();afterlogout=await e.observe();sequence.append({'event':'login-all-dialogs-closed','state':afterlogout})
 check(o,'成功退出关闭所有dialog并回登录',afterlogout['login'] and not afterlogout['open'] and afterlogout['user'] is None,afterlogout)
 resp=await e.ctx.request.get(e.url+'/api/session',headers={'Cookie':oldcookie});check(o,'实际旧会话被服务端撤销',resp.status==401,{'status':resp.status,'body':await resp.json()})
 oldrelease.set();await asyncio.wait_for(olddone.wait(),8);await p.wait_for_timeout(120);afterold=await e.observe();sequence.append({'event':'after-old-completed','state':afterold});check(o,'旧成功或非401错误不能恢复旧工作空间',afterold['login'] and afterold['user'] is None and not afterold['open'],afterold)
 await p.unroute('**/api/logout');await p.unroute('**/api/rooms?*');await e.login('bob');new=await e.observe();check(o,'新登录不恢复旧表单或身份',new['user']=='bob@meetspace.test' and not new['open'],new)
 check(o,'整个退出竞态无业务写入',snap(e.db)==before,{'before':before,'after':snap(e.db)});o['events']=sequence;o['screenshots'].append(await e.shot('relogin'))

async def logout_failure(e,o,outcome):
 p=e.p; before=snap(e.db); got=asyncio.Event(); release=asyncio.Event();e.holds.append(release);count=0
 async def fault(route):
  nonlocal count
  count+=1;got.set();await release.wait()
  if outcome=='503':await route.fulfill(status=503,content_type='application/json',body='{"error":"退出受控失败"}')
  else:await route.abort('failed')
 await p.route('**/api/logout',fault);button=p.locator('[data-logout]:visible').first;r=await button.bounding_box();await p.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2);await asyncio.wait_for(got.wait(),8);await p.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2)
 check(o,'等待期间重复原生点击不重复发送',count==1 and await button.is_disabled(),{'requests':count,'disabled':await button.is_disabled()});release.set();await p.wait_for_function('() => document.querySelector("#toast").textContent.length && [...document.querySelectorAll("[data-logout]")].filter(x=>x.offsetParent!==null).every(x=>!x.disabled)')
 a=await e.observe();resp=await e.ctx.request.get(e.url+'/api/session');check(o,'失败可见且按钮恢复会话未撤销',not a['login'] and bool(a['toast']) and resp.status==200,{'UI':a,'session_status':resp.status})
 await p.unroute('**/api/logout');cookies=await e.ctx.cookies();cookie='; '.join(c['name']+'='+c['value'] for c in cookies);await button.click();await p.locator('#login-form').wait_for();resp=await e.ctx.request.get(e.url+'/api/session',headers={'Cookie':cookie});check(o,'恢复后真实退出并拒绝旧会话',resp.status==401,{'status':resp.status,'UI':await e.observe()});check(o,'业务数据无改变',before==snap(e.db),{'before':before,'after':snap(e.db)});o['screenshots']=[await e.shot('failure-recovered')]

async def main():
 cases=[]
 for width,height in [(1280,900),(390,844),(320,740)]:
  for kind in ['booking','room','confirm']:
   for gesture in ['X','Escape','left','right','top','bottom','padding','child']+(['retain'] if kind=='confirm' else []):
    cases.append(('dialog',f'{width}-{kind}-{gesture}',(kind,gesture,width,height),width,height))
 for kind in ['booking','room','confirm']:
  for outcome in ['success','non401-error']:cases.append(('logout',kind+'-'+outcome,(kind,outcome),1280,900))
 for outcome in ['503','network']:cases.append(('logout-failure',outcome,(outcome,),1280,900))
 records=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for group,name,args,width,height in cases:
   e=Env();o={'name':name,'group':group,'clock':T.isoformat(),'viewport':{'width':width,'height':height},'checks':[]}
   try:
    await e.start(browser,name,width,height)
    await (dialog_case(e,o,*args) if group=='dialog' else logout_case(e,o,*args) if group=='logout' else logout_failure(e,o,*args))
    if o.get('status')!='not_reachable_in_viewport':o['status']='passed' if o['checks'] and all(c['passed'] for c in o['checks']) else 'failed'
   except Exception:
    o['status']='unproven';o['harness_error']=traceback.format_exc()
   finally:
    try:await e.close()
    except Exception:o['cleanup_error']=traceback.format_exc()
   f=E/(name+'.json');f.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');records.append({'name':name,'group':group,'status':o['status'],'evidence':str(f.relative_to(BASE))});print(name,o['status'],flush=True)
   results=[]
   for sid,groups in [('WB-ui-dialog-close-no-write',['dialog']),('WB-ui-logout-races',['logout','logout-failure'])]:
    rows=[r for r in records if r['group'] in groups];expected=sum(c[0] in groups for c in cases);status='failed' if any(r['status']=='failed' for r in rows) else 'unproven' if len(rows)!=expected or any(r['status']=='unproven' for r in rows) else 'passed'
    results.append({'scenario_id':sid,'method_ids':['AI-'+sid],'status':status,'actual':f'{len(rows)}/{expected} 矩阵项；视口无外部区域项单列，仍保留源码分母。','evidence':[r['evidence'] for r in rows]})
   (BASE/'ui-dialog-results.json').write_text(json.dumps({'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','browser_version':browser.version,'source_sha256':hashlib.sha256((ROOT/'web/app.js').read_bytes()).hexdigest(),'items':records,'results':results},ensure_ascii=False,indent=2)+'\n')
  await browser.close()
if __name__=='__main__':asyncio.run(main())
