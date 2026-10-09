import sys,json,threading,datetime,sqlite3,traceback,uuid,hashlib,types,time,platform
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path.cwd(); L=ROOT/'tests/delivery-acceptance'; RUN=L/'runs/acceptance-20261008T-full-0b386b4-r1'; E=RUN/'evidence/ui'; E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT)); import app.server as srv
real_dt=datetime.datetime; FIX=real_dt.fromisoformat('2030-04-10T09:00:00+08:00')
class Clock(real_dt):
 @classmethod
 def now(cls,tz=None):return FIX.astimezone(tz) if tz else FIX.replace(tzinfo=None)
srv.datetime=Clock;srv.time=types.SimpleNamespace(time=lambda:FIX.timestamp())
sc=json.load(open(L/'scenarios.json'))['items']; methods={m['id']:m for m in json.load(open(L/'methods.json'))['items']}
extra=['BB-room-discovery-'+str(i) for i in [5,6,7,8,9]]+['BB-reservation-management-'+str(i) for i in [3,4,10]]+['BB-notification-center-'+str(i) for i in [6,7]]+['BB-team-administration-7']
assigned=[s for s in sc if s['id'].startswith(('BB-interface-experience-','WB-ui-')) or s['id'] in extra]
results={}; groups=[]; serial=100
# Read every complete method, including supplements, into memory; execution scope tracked explicitly.
for s in assigned:
 for m in s['method_ids']:assert methods[m]['actions'] and methods[m]['preconditions']
def save():
 mr=[]
 for s in assigned:
  for mid in s['method_ids']:
   if mid in [x['method_id'] for x in mr]:continue
   r=results.get(mid,{'status':'unproven','actual':'尚未完成此方法的全部矩阵；不得据其他方法成功推定通过。','evidence':['evidence/ui/progress.json']})
   mr.append({'method_id':mid,**r})
 rr=[]
 for s in assigned:
  rs=[next(x for x in mr if x['method_id']==mid) for mid in s['method_ids']]
  status='failed' if any(x['status']=='failed' for x in rs) else ('passed' if all(x['status']=='passed' for x in rs) else 'unproven')
  rr.append({'scenario_id':s['id'],'method_ids':s['method_ids'],'status':status,'actual':'；'.join(x['method_id']+': '+x['actual'] for x in rs),'evidence':sorted(set(z for x in rs for z in x['evidence']))})
 (E/'progress.json').write_text(json.dumps({'groups':groups},ensure_ascii=False,indent=2));(RUN/'ui-results.json').write_text(json.dumps({'revision':'0b386b4bd37b01eb996c5e74215ab1a4463a9487','environment':{'browser':browser.version if 'browser' in globals() else '', 'python':sys.version,'platform':platform.platform(),'server_clock':FIX.isoformat(),'timezone':'Asia/Shanghai unless matrix specifies','target':'unmodified app/server.py + web assets, real localhost HTTP and SQLite; frontend fault routing explicitly labelled'},'method_results':mr,'results':rr},ensure_ascii=False,indent=2))
class Env:
 def __init__(self,label,width=1440,tz='Asia/Shanghai'):
  global serial;serial+=1;self.label=f'{serial:03}-{label}';self.db=E/(self.label+'.sqlite');self.server=srv.ApplicationServer(('127.0.0.1',0),srv.Store(self.db));threading.Thread(target=self.server.serve_forever,daemon=True).start();self.url=f'http://127.0.0.1:{self.server.server_port}';self.ctx=browser.new_context(viewport={'width':width,'height':900 if width>600 else 844},timezone_id=tz,device_scale_factor=1);self.page=self.ctx.new_page();self.page.clock.set_fixed_time(FIX);self.requests=[];self.page.on('request',lambda r:self.requests.append({'method':r.method,'path':r.url.replace(self.url,''),'time':len(self.requests)}));self.page.goto(self.url);self.page.locator('#login-form').wait_for();self.obs=[]
 def login(self,who='alice'):
  self.page.locator(f'[data-account={who}]').click();self.page.locator('#login-form button[type=submit]').click();self.page.locator('#filter-date').wait_for();self.page.wait_for_function('() => !state.loading')
 def nav(self,name):self.page.locator(f'nav [data-page={name}]').click();self.page.wait_for_function('() => !state.loading')
 def shot(self,name):
  path=E/(self.label+'-'+name+'.png');self.page.screenshot(path=str(path),full_page=True);return str(path.relative_to(RUN))
 def api(self,path,method='GET',data=None):
  r=self.ctx.request.fetch(self.url+'/api'+path,method=method,data=data,headers={'X-Meeting-App':'1','Origin':self.url});return r.status,r.json()
 def snap(self):
  with sqlite3.connect(self.db) as c:return {t:[list(x) for x in c.execute(q)] for t,q in {'rooms':'select id,team_id,name,location,capacity,equipment,active from rooms','bookings':'select id,room_id,user_id,title,start,end,attendees,status from bookings','notifications':'select id,user_id,booking_id,message,read from notifications','users':'select id,team_id,name,role from users'}.items()}
 def close(self):self.ctx.close();self.server.shutdown();self.server.server_close()
def group(name,mids,fn,complete=False):
 e=Env(name);obs={'name':name,'methods':mids,'mode':'real application UI unless fault branch marked','server_clock':FIX.isoformat(),'before':e.snap()};status='unproven'
 try:
  fn(e,obs);status='passed' if complete else 'unproven';obs['assertions_completed']=True
 except Exception as ex:obs['error']=str(ex);obs['traceback']=traceback.format_exc();status='failed' if isinstance(ex,AssertionError) else 'unproven'
 finally:
  try:obs['screenshot']=e.shot('outcome');obs['visible_text']=e.page.locator('body').inner_text();obs['after']=e.snap();obs['network']=e.requests
  except Exception as ex:obs['capture_error']=str(ex)
  p=E/(e.label+'.json');p.write_text(json.dumps(obs,ensure_ascii=False,indent=2));ev=[str(p.relative_to(RUN))]+([obs['screenshot']] if 'screenshot' in obs else [])
  for mid in mids:
   prior=results.get(mid); st='failed' if status=='failed' or (prior and prior['status']=='failed') else status
   results[mid]={'status':st,'actual':('执行断言失败：'+obs['error']) if status=='failed' else ('已执行本方法完整矩阵，断言通过。' if complete and status=='passed' else '已执行 '+name+' 实际 UI 分支；完整矩阵尚未证明。'+obs.get('error','')),'evidence':sorted(set(ev+(prior['evidence'] if prior else [])))}
  groups.append({'name':name,'status':status,'evidence':ev});save();e.close();print(name,status,flush=True)
def book_ui(e,title='UI验证',day='2030-04-12',start='10:00',end='11:00'):
 p=e.page;p.locator('[data-book-room]').first.click();f=p.locator('#booking-form')
 for k,v in {'title':title,'date':day,'start':start,'end':end,'attendees':'2'}.items():f.locator('[name='+k+']').fill(v)
 f.locator('[type=submit]').click();p.locator('#booking-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');return e.api('/bookings')[1]['bookings'][0]
def create(e,room=1,day='2030-04-12',start='10:00',end='11:00',title='API合成预约'):
 code,data=e.api('/bookings','POST',{'room_id':room,'title':title,'attendees':2,'start':day+'T'+start+':00+08:00','end':day+'T'+end+':00+08:00','idempotency_key':str(uuid.uuid4())});assert code in (200,201),(code,data);return data['booking']['id']
def navigation(e,o):
 p=e.page;out=[]
 for who,role in [('admin','admin'),('alice','member'),('bob','member'),('other','admin')]:
  n=len([x for x in e.requests if x['path']=='/api/login']);p.locator(f'[data-account={who}]').click();assert p.locator('[name=email]').input_value()==who+'@meetspace.test';assert p.locator('[name=password]').input_value()=='MeetSpace!2026';assert len([x for x in e.requests if x['path']=='/api/login'])==n
  p.locator('#login-form button[type=submit]').click();p.wait_for_function('() => state.user && !state.loading');assert p.locator('nav [data-page=manage]').count()==(role=='admin')
  for name in ['spaces','bookings','inbox']+(['manage'] if role=='admin' else []):e.nav(name);assert p.locator(f'nav [data-page={name}][aria-current=page]').count()==1
  p.reload();p.wait_for_function('() => state.user && !state.loading');assert e.api('/session')[1]['user']['email']==who+'@meetspace.test';out.append({'who':who,'nav':p.locator('nav').inner_text(),'shot':e.shot(who)})
  p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for()
 o['roles']=out

def defaults(e,o):
 e.login();p=e.page;rows=[]
 for tz in ['Asia/Shanghai','America/Los_Angeles']:
  # Separate actual browser context for timezone, same authenticated session via in-memory storage only.
  ctx=browser.new_context(storage_state=e.ctx.storage_state(),timezone_id=tz);q=ctx.new_page();q.clock.set_fixed_time(FIX);q.goto(e.url);q.locator('#filter-date').wait_for()
  for hh in ['07:00','07:50','08:00','09:00','09:07','09:14:59','19:44','19:45','19:59','20:00','23:59']:
   q.clock.set_fixed_time(real_dt.fromisoformat('2030-04-10T'+hh+'+08:00'))
   for day in ['2030-04-09','2030-04-10','2030-04-11','2030-05-10']:
    q.locator('#filter-date').fill(day);q.locator('#filter-date').dispatch_event('change');q.wait_for_function('() => !state.loading');q.locator('[data-book-room]').first.click();v={k:q.locator('#booking-form [name='+k+']').input_value() for k in ['date','start','end','attendees']};a,b=[int(x[:2])*60+int(x[3:]) for x in [v['start'],v['end']]];assert 480<=a<b<=1200 and a%15==b%15==0
    if day<'2030-04-10' or (day=='2030-04-10' and hh>='19:45'):assert v['date']=='2030-04-11'
    assert q.locator('#booking-form [name=date]').get_attribute('min')=='2030-04-10';assert q.locator('#booking-form [name=date]').get_attribute('max')=='2030-05-10';rows.append({'tz':tz,'clock':hh,'selected':day,**v});q.keyboard.press('Escape')
  ctx.close()
 o['matrix']=rows

def dialogs(e,o):
 e.login('admin');p=e.page;create(e);o['branches']=[]
 for kind in ['booking','room','confirm']:
  for action in ['close','escape','backdrop']:
   if kind=='booking':e.nav('spaces');p.locator('[data-book-room]').first.click();p.locator('#booking-form [name=title]').fill('未提交标题')
   elif kind=='room':e.nav('manage');p.locator('#add-room').click();p.locator('#room-form [name=name]').fill('未提交空间')
   else:e.nav('bookings');p.locator('[data-cancel]').first.click()
   d=p.locator('#'+kind+'-dialog');before=e.snap();n=len([r for r in e.requests if r['method'] in ['POST','PATCH']]);d.locator('h2').click();assert d.is_visible();rect=d.bounding_box()
   if action=='close':d.locator('[data-close]').first.click()
   elif action=='escape':p.keyboard.press('Escape')
   else:p.mouse.click(2,2)
   assert not d.is_visible();assert e.snap()==before;assert len([r for r in e.requests if r['method'] in ['POST','PATCH']])==n;o['branches'].append({'dialog':kind,'gesture':action,'rect':rect,'writes':0,'unchanged':True})

def responsive(e,o):
 e.login();p=e.page;o['viewports']=[]
 for width,height in [(1440,900),(390,844),(320,740),(375,844),(599,844),(600,844),(601,844),(849,900),(850,900),(851,900),(1149,900),(1150,900),(1151,900),(1499,900),(1500,900),(1501,900)]:
  p.set_viewport_size({'width':width,'height':height});e.nav('spaces');p.locator('#filter-capacity').select_option('4');p.locator('#filter-equipment').select_option('白板');p.locator('#filter-capacity').select_option('');p.locator('#filter-equipment').select_option('');rec={'width':width,'height':height,'layout':p.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')};assert rec['layout']['scroll']<=width
  b=book_ui(e,title='长中文预约主题用于窄屏测试'+str(width),day='2030-04-12');rec['created']=b['id'];rec['created_shot']=e.shot(str(width)+'-created');e.nav('bookings');p.locator(f'[data-cancel="{b["id"]}"]').click();rec['dialog']=p.locator('#confirm-dialog').bounding_box();assert rec['dialog']['x']>=0 and rec['dialog']['width']<=width;p.locator('#confirm-cancel').click();p.locator('#confirm-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert e.api('/bookings')[1]['bookings'][0]['status']=='cancelled';e.nav('inbox');assert p.locator('.notice-row').count()>=2;rec['final_shot']=e.shot(str(width)+'-notices');o['viewports'].append(rec)

def start_errors(e,o):
 p=e.page;o['branches']=[];e.login();p.reload();p.locator('#filter-date').wait_for();o['valid_refresh']=True
 for mode in ['503','nonjson','offline']:
  def route(r):
   if mode=='offline':r.abort()
   else:r.fulfill(status=503 if mode=='503' else 200,content_type='application/json' if mode=='503' else 'text/html',body='{"error":"UI受控503"}' if mode=='503' else 'bad')
  p.route('**/api/session',route);p.reload();p.get_by_role('heading',name='暂时无法连接工作空间').wait_for();o['branches'].append({'fault':mode,'text':p.locator('.error-page').inner_text(),'shot':e.shot(mode)});p.unroute('**/api/session');p.reload();p.locator('#filter-date').wait_for()
 with sqlite3.connect(e.db) as c:c.execute('delete from sessions');c.commit()
 p.reload();p.locator('#login-form').wait_for();o['real_invalid_session']=True

def load_errors(e,o):
 e.login('admin');p=e.page;o['branches']=[]
 for endpoint in ['rooms','bookings','notifications','members']:
  e.nav('manage' if endpoint=='members' else 'spaces');pattern='**/api/'+endpoint+'*'
  p.route(pattern,lambda r:r.fulfill(status=503,content_type='application/json',body='{"error":"UI受控加载失败"}'))
  e.nav('manage' if endpoint=='members' else 'bookings');assert p.locator('.retry-panel').is_visible();assert p.locator('.booking-row').count()==0;o['branches'].append({'endpoint':endpoint,'text':p.locator('.retry-panel').inner_text(),'shot':e.shot(endpoint)});p.unroute(pattern);p.locator('[data-refresh]').click();p.wait_for_function('() => !state.loading');assert not p.locator('.retry-panel').count()

def rooms_form(e,o):
 e.login('admin');p=e.page;e.nav('manage');p.locator('[data-edit-room]').first.click();o['original']={k:p.locator('#room-form [name='+k+']').input_value() for k in ['name','location','capacity']};p.locator('#room-form [name=name]').fill('UI编辑室');p.locator('#room-form [name=location]').fill('UI位置');p.locator('#room-form [name=capacity]').fill('9');p.locator('#room-form [name=active]').uncheck();p.locator('#room-form [value=白板]').check();p.locator('#room-form [type=submit]').click();p.locator('#room-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert any(x['name']=='UI编辑室' and x['capacity']==9 and not x['active'] for x in e.api('/rooms')[1]['rooms']);p.locator('#add-room').click();assert p.locator('#room-form [name=name]').input_value()=='';assert p.locator('#room-form [name=active]').is_checked();p.locator('#room-form [name=name]').fill('UI编辑室');p.locator('#room-form [name=location]').fill('保留位置');p.locator('#room-form [type=submit]').click();p.locator('#room-error').filter(has_text='').wait_for();p.wait_for_function('() => document.querySelector("#room-error").textContent.length>0');assert p.locator('#room-form [name=location]').input_value()=='保留位置';o['error']=p.locator('#room-error').inner_text();p.locator('#room-form [name=name]').fill('UI新建室');p.locator('#room-form [type=submit]').click();p.locator('#room-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert any(x['name']=='UI新建室' for x in e.api('/rooms')[1]['rooms'])

def role(e,o):
 e.login('admin');p=e.page;e.nav('manage');me=e.api('/session')[1]['user']['id'];p.locator(f'[data-member="{me}"]').select_option('member');p.wait_for_function('() => !state.loading && !document.querySelector("[data-member]").disabled');p.wait_for_function('() => document.querySelector("#toast").textContent.length>0');assert e.api('/session')[1]['user']['role']=='admin';o['last_admin_error']=p.locator('#toast').inner_text();members=e.api('/members')[1]['members'];other=next(x['id'] for x in members if x['id']!=me);p.locator(f'[data-member="{other}"]').select_option('admin');p.wait_for_function('() => !state.loading');p.wait_for_function('() => document.querySelector("#toast").textContent==="成员角色已更新"');p.locator(f'[data-member="{me}"]').select_option('member');p.wait_for_function('() => state.user.role==="member" && !state.loading');assert p.locator('nav [data-page=manage]').count()==0;assert p.locator('#filter-date').count()==1;assert e.api('/members')[0]==403;p.reload();p.locator('#filter-date').wait_for();assert p.locator('nav [data-page=manage]').count()==0;o['demoted']=True

if __name__=="__main__":
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True)
  group('roles-navigation',['AI-interface-experience-1','AI-interface-experience-2','AI-WB-ui-login-navigation'],navigation)
  group('default-time-matrix',['AI-interface-experience-6','AI-WB-ui-default-times','AI-interface-experience-5'],defaults,True)
  group('dialog-close-matrix',['AI-interface-experience-11','AI-WB-ui-dialog-close-no-write'],dialogs,True)
  group('responsive-complete-flows',['AI-interface-experience-12','AI-WB-ui-responsive-breakpoints'],responsive)
  group('start-session-errors',['AI-WB-ui-start-session-errors'],start_errors,True)
  group('parallel-load-errors',['AI-interface-experience-4','AI-WB-ui-load-parallel-error'],load_errors)
  group('room-edit-create-retry',['AI-WB-ui-room-edit-draft','AI-interface-experience-9'],rooms_form)
  group('role-demotion',['AI-team-administration-7','AI-WB-ui-role-demotion-reload','AI-interface-experience-8'],role)
  browser.close()
