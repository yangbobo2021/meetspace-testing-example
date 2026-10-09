import sys, json, sqlite3, threading, datetime as dt, time as realtime, types, hashlib, platform, subprocess, traceback, shutil, concurrent.futures
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from playwright.sync_api import sync_playwright
ROOT=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking'); L=ROOT/'tests/delivery-acceptance'; R=L/'runs/acceptance-20261009T-stage10-708c9c0-r1'; E=R/'evidence/api-r2'; E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT)); import app.server as app
REV='708c9c057b5c9014f4ff975fdc5774093a687abe'; assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==REV
clock=dt.datetime.fromisoformat('2030-04-10T09:00:00+08:00')
class Clock(dt.datetime):
 @classmethod
 def now(cls,tz=None): return clock.astimezone(tz) if tz else clock.replace(tzinfo=None)
app.datetime=Clock; app.time=types.SimpleNamespace(time=lambda:clock.timestamp())
DB=R/'api-working.sqlite'; DB.unlink(missing_ok=True); store=app.Store(DB)
server=app.ApplicationServer(('127.0.0.1',0),store); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start(); base=f'http://127.0.0.1:{server.server_port}'
methods={x['id']:x for x in json.load(open(L/'methods.json'))['items']}; scenarios=json.load(open(L/'scenarios.json'))['items']; groups={}; current=None; cookies={}; pages={}; seq=0; network=[]; trace_lines=set()
def tracer(frame,event,arg):
 if event=='line' and frame.f_code.co_filename==app.__file__: trace_lines.add(frame.f_lineno)
 return tracer
threading.settrace(tracer)
sql_trace=[]
original_connect=sqlite3.connect
class TracedConnection(sqlite3.Connection):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.set_trace_callback(self.capture)
 def capture(self,statement):
  if any(x in statement.lower() for x in ['sessions','password_hash','insert into users','select * from users']):return
  sql_trace.append({'connection':id(self),'thread':threading.get_ident(),'time_ns':realtime.monotonic_ns(),'sql':statement})
def connect_traced(*a,**kw):return original_connect(*a,factory=TracedConnection,**kw)
app.sqlite3=types.SimpleNamespace(connect=connect_traced,Row=sqlite3.Row,IntegrityError=sqlite3.IntegrityError,OperationalError=sqlite3.OperationalError)

def snap():
 with sqlite3.connect(DB) as db:
  db.row_factory=sqlite3.Row
  return {t:[dict(r) for r in db.execute(q)] for t,q in {'bookings':'SELECT id,team_id,room_id,user_id,title,start,end,attendees,status,created_at,cancelled_at FROM bookings ORDER BY id','notifications':'SELECT * FROM notifications ORDER BY id','rooms':'SELECT * FROM rooms ORDER BY id','roles':'SELECT id,team_id,role FROM users ORDER BY id'}.items()}
def emit(label,ok,actual):
 if current is not None: groups[current]['checks'].append({'label':label,'passed':bool(ok),'actual':actual})
def request(user,path,method='GET',data=None,expect=None,invariant=False):
 before=snap() if invariant else None
 req=Request(base+path,method=method,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json','X-Meeting-App':'1','Origin':base,'Cookie':cookies.get(user,'')})
 start=realtime.monotonic_ns()
 try:r=urlopen(req,timeout=15)
 except HTTPError as e:r=e
 with r: status=r.status; body=json.load(r)
 entry={'actor':user,'path':path,'method':method,'input':data,'status':status,'body':body,'start_ns':start,'end_ns':realtime.monotonic_ns(),'server_clock':clock.isoformat()}
 if current:groups[current]['http'].append(entry)
 if expect is not None:emit(f'{method} {path} status',status in ([expect] if isinstance(expect,int) else expect),entry)
 if invariant:emit('拒绝后独立数据库不变量',before==snap(),{'before':before,'after':snap()})
 return status,body
BASE_ROOMS=None
BASE_USERS=None
def reset():
 global clock
 clock=dt.datetime.fromisoformat('2030-04-10T09:00:00+08:00')
 with sqlite3.connect(DB) as db:
  db.execute('DELETE FROM notifications');db.execute('DELETE FROM bookings');db.execute('DELETE FROM rooms');db.executemany('INSERT INTO rooms VALUES (?,?,?,?,?,?,?)',BASE_ROOMS)
  for uid,role in BASE_USERS:db.execute('UPDATE users SET role=? WHERE id=?',(role,uid))
  db.execute('UPDATE sessions SET expires=?',(clock.timestamp()+100*86400,))
 server.login_attempts.clear()
def payload(**kw):
 global seq
 seq+=1
 return dict({'room_id':1,'title':'合成矩阵会议','attendees':2,'start':'2030-04-11T10:00:00+08:00','end':'2030-04-11T11:00:00+08:00','idempotency_key':f'matrix-{seq}'},**kw)
def room(**kw):return dict({'name':'矩阵空间','location':'测试层','capacity':8,'equipment':['白板'],'active':True},**kw)
def create(user='U',**kw):
 p=payload(**kw); s,b=request(user,'/api/bookings','POST',p,201);return p,b.get('booking',{}).get('id')
def cancel(user,bid,expect=200):return request(user,f'/api/bookings/{bid}/cancel','POST',{},expect)
def view(user='U'):
 page=pages[user];page.goto(base);page.locator('#filter-date').wait_for();page.locator('#filter-date').fill('2030-04-11');page.locator('#filter-date').dispatch_event('change');page.wait_for_timeout(120);return page
def screenshot(page,name):page.screenshot(path=str(E/f'{name}.png'),full_page=True)
def mark_ui(user='U'):
 page=pages[user];page.goto(base);page.locator('[data-page=inbox]').click();page.wait_for_timeout(120)
 if page.locator('#mark-read').count() and page.locator('#mark-read').is_enabled():
  with page.expect_response(lambda r:r.url.endswith('/api/notifications/read')) as response:page.locator('#mark-read').click()
  emit('UI 全部已读响应',response.value.status==200,{'status':response.value.status});page.wait_for_timeout(80)
 else: request(user,'/api/notifications/read','POST',{},200)
def persist():
 records=[]
 for name,g in groups.items():
  path=E/f'{name}.json';path.write_text(json.dumps(g,ensure_ascii=False,indent=2))
  status='failed' if any(not x['passed'] for x in g['checks']) else 'unproven' if g.get('gap') or not g['checks'] else 'passed'
  for mid in g['method_ids']:
   effective=status
   records.append({'method_id':mid,'status':effective,'actual':f"{len(g['checks'])} assertions, {sum(not x['passed'] for x in g['checks'])} failed. "+g.get('gap',''),'evidence':[str(path.relative_to(R))]})
 (R/'api-results-r2.json').write_text(json.dumps({'revision':REV,'environment':{'platform':platform.platform(),'python':sys.version,'base_url':base,'database':'isolated synthetic SQLite','clock_adapter':'app.datetime.now + app.time.time; browser page.clock fixed separately','source_sha256':hashlib.sha256(Path(app.__file__).read_bytes()).hexdigest(),'integration_mode':'real local app, no remote integrations; clock adapter only'},'method_results':records,'results':[]},ensure_ascii=False,indent=2))
def group(name,mids,fn,gap=''):
 global current
 current=name;trace_lines.clear();groups[name]={'method_ids':mids,'checks':[],'http':[],'gap':gap}
 try: reset();fn()
 except Exception as e:
  groups[name]['gap']+=' Execution interrupted: '+repr(e);groups[name]['exception']=traceback.format_exc()
 groups[name]['executed_source_lines']=sorted(trace_lines);groups[name]['sql_trace']=list(sql_trace);sql_trace.clear();groups[name]['final_snapshot']=snap();persist();print(name,len(groups[name]['checks']),sum(not x['passed'] for x in groups[name]['checks']),flush=True);current=None
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True)
 for who,account in [('A','admin'),('U','alice'),('V','bob'),('B','other')]:
  ctx=browser.new_context(viewport={'width':1280,'height':900},timezone_id='Asia/Shanghai');page=ctx.new_page();page.clock.set_fixed_time(clock)
  page.on('request',lambda r: network.append({'method':r.method,'path':r.url.removeprefix(base),'fields': sorted((r.post_data_json or {}).keys()) if r.method in ['POST','PATCH'] else []}))
  page.goto(base);page.locator(f'[data-account={account}]').click();page.get_by_role('button',name='登录工作空间').click();page.locator('#filter-date').wait_for();cookies[who]='; '.join(f"{x['name']}={x['value']}" for x in ctx.cookies());pages[who]=page;screenshot(page,f'login-{who}')
 with sqlite3.connect(DB) as db:BASE_ROOMS=db.execute('SELECT * FROM rooms').fetchall();BASE_USERS=db.execute('SELECT id,role FROM users').fetchall()
 def discovery():
  page=view('U');page.locator('[data-book-room="1"]').click()
  for n,v in [('title','UI实际创建'),('date','2030-04-11'),('start','10:00'),('end','11:00'),('attendees','2')]:page.locator(f'#booking-form [name={n}]').fill(v)
  with page.expect_response(lambda r:r.url.endswith('/api/bookings') and r.request.method=='POST') as res:page.locator('#booking-form button[type=submit]').click()
  emit('真实UI创建201',res.value.status==201,res.value.json());page.locator('#booking-dialog').wait_for(state='hidden');screenshot(page,'ui-created')
  page.locator('[data-page=bookings]').click();page.locator('[data-cancel]').first.click();page.locator('#confirm-cancel').click();page.locator('#confirm-dialog').wait_for(state='hidden')
  mark_ui();a=pages['A'];a.locator('[data-page=manage]').click();a.locator('#add-room').click()
  for n,v in [('name','UI路由空间'),('location','L'),('capacity','8')]:a.locator(f'#room-form [name={n}]').fill(v)
  a.locator('#room-form button[type=submit]').click();a.locator('#room-dialog').wait_for(state='hidden');a.locator('[data-edit-room]').first.click();a.locator('#room-form [name=location]').fill('L2');a.locator('#room-form button[type=submit]').click();a.locator('#room-dialog').wait_for(state='hidden');a.locator('[data-member="3"]').select_option('admin');a.wait_for_timeout(200)
  emit('路由从运行UI获取',all(any(n['path'].startswith(p) for n in network) for p in ['/api/bookings','/api/rooms','/api/members','/api/notifications']),network)
 group('ui-route-discovery',[],discovery)
 def fields():
  for field,values in [('room_id',[None,True,False,1.5,'1',0,1,2147483647,2147483648]),('attendees',[None,True,False,1.5,'1',0,1,100,101]),('title',[None,1,[],{},'', ' ', '中','中'*100,'中'*101,' 中 ']),('idempotency_key',[None,1,[],{},'', ' ','中','中'*100,'中'*101,' 中 '])]:
   for value in ['MISSING']+values:
    reset()
    with sqlite3.connect(DB) as db:db.execute('UPDATE rooms SET capacity=100 WHERE id=1')
    p=payload();p.pop(field) if value=='MISSING' else p.update({field:value})
    valid=(isinstance(value,int) and not isinstance(value,bool) and 1<=value<=(2147483647 if field=='room_id' else 100)) if field in ['room_id','attendees'] else isinstance(value,str) and value!='MISSING' and 1<=len(value.strip())<=100
    expected=404 if field=='room_id' and value==2147483647 else 201 if valid else 400
    request('U','/api/bookings','POST',p,expected,invariant=expected!=201)
    if expected==201: emit('成功保存规范化字段及一通知',len(snap()['bookings'])==1 and len(snap()['notifications'])==1,snap())
 group('booking-fields',['AI-reservation-creation-2','AI-WB-booking-fields-guards'],fields)
 def datetimes():
  for f in ['start','end']:
   for v in [None,3,'','nonsense','2030-02-30T10:00:00+08:00','2030-04-11T10:00:00','99999-01-01T00:00:00Z']:
    reset();request('U','/api/bookings','POST',payload(**{f:v}),400,True)
  for start,end in [('2030-04-11T10:00:00+08:00','2030-04-11T11:00:00+08:00'),('2030-04-11T02:00:00Z','2030-04-11T03:00:00Z'),('2030-04-10T19:00:00-07:00','2030-04-10T20:00:00-07:00'),('2030-04-11T10:00:00+08:00','2030-04-11T03:00:00Z'),('2030-04-11T10:00:00+08:00','2030-04-11T09:00:00Z')]:
   reset();create(start=start,end=end);emit('UTC数据库规范化',snap()['bookings'][0]['start']=='2030-04-11T02:00:00+00:00',snap())
  reset();request('U','/api/bookings','POST',payload(start='2030-04-11T10:00:00Z',end='2030-04-11T11:00:00+08:00'),400,True)
 group('datetime',['AI-reservation-creation-3','AI-WB-datetime-parse-normalize'],datetimes)
 def durations():
  for seconds in [0,-900,899,900,901,28800,28801,29700]:
   reset();s=dt.datetime.fromisoformat('2030-04-11T08:00:00+08:00');p=payload(start=s.isoformat(),end=(s+dt.timedelta(seconds=seconds)).isoformat());request('U','/api/bookings','POST',p,201 if seconds in [900,28800] else 400,seconds not in [900,28800])
 group('duration',['AI-reservation-creation-5','AI-WB-booking-duration'],durations)
 def intervals():
  for m in [0,15,30,45]:reset();create(start=f'2030-04-11T10:{m:02}:00+08:00',end=f'2030-04-11T11:{m:02}:00+08:00')
  for f in ['start','end','both']:
   for attr,vals in [('minute',[1,14,16,59]),('second',[1,59]),('microsecond',[1,999999])]:
    for val in vals:
     reset();p=payload()
     for k in (['start','end'] if f=='both' else [f]):p[k]=dt.datetime.fromisoformat(p[k]).replace(**{attr:val}).isoformat()
     request('U','/api/bookings','POST',p,400,True)
  reset();create(start='2030-04-11T10:00:00.000000+08:00',end='2030-04-11T11:00:00.000000+08:00')
 group('intervals',['AI-reservation-creation-7'],intervals)
 def hours():
  for st,en,ok in [('08:00','08:15',True),('19:45','20:00',True),('07:45','08:00',False),('20:00','20:15',False),('19:45:00','20:00:01',False),('19:45:00','20:01:00',False),('19:45:00','20:00:00.000001',False),('07:59:59','09:00:00',False)]:
   reset();st=st+':00' if len(st)==5 else st;en=en+':00' if len(en)==5 else en;request('U','/api/bookings','POST',payload(start=f'2030-04-11T{st}+08:00',end=f'2030-04-11T{en}+08:00'),201 if ok else 400,not ok)
  reset();request('U','/api/bookings','POST',payload(start='2030-04-11T23:45:00+08:00',end='2030-04-12T00:15:00+08:00'),400,True)
  reset();create(start='2030-04-11T00:00:00Z',end='2030-04-11T01:00:00Z')
  reset();create(start='2030-04-10T23:30:00-01:00',end='2030-04-11T00:30:00-01:00')
 group('hours',['AI-reservation-creation-6','AI-WB-booking-open-hours'],hours)
 def horizon():
  global clock
  S=dt.datetime.fromisoformat('2030-04-11T10:00:00+08:00')
  for skew in [0,-86400,86400]:
   for delta,ok in [(1,True),(0,False),(-1,False),(30*86400,True),(30*86400+1,False),(30*86400-1,True)]:
    reset();clock=S-dt.timedelta(seconds=delta);p=pages['U'];p.clock.set_fixed_time(clock+dt.timedelta(seconds=skew));p.goto(base);p.locator('[data-logout]').first.click();p.locator('[data-account=alice]').click();p.get_by_role('button',name='登录工作空间').click();p.locator('#filter-date').wait_for();cookies['U']='; '.join(f"{x['name']}={x['value']}" for x in p.context.cookies());emit('浏览器与服务钟分别记录',True,{'server':clock.isoformat(),'browser':p.evaluate('new Date().toISOString()')});request('U','/api/bookings','POST',payload(),201 if ok else 400,not ok)
  pages['U'].clock.set_fixed_time(dt.datetime.fromisoformat('2030-04-10T09:00:00+08:00'))
 group('horizon',['AI-reservation-creation-4','AI-WB-booking-horizon'],horizon)
 def compete(jobs):
  barrier=threading.Barrier(len(jobs))
  def task(j):barrier.wait();return request(*j)
  with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:return list(pool.map(task,jobs))
 def conflicts():
  for st,en,ok in [('10:00','11:00',False),('10:15','10:45',False),('09:45','11:15',False),('09:45','10:15',False),('10:45','11:15',False),('09:00','10:00',True),('11:00','12:00',True)]:
   reset();create();request('V','/api/bookings','POST',payload(start=f'2030-04-11T{st}:00+08:00',end=f'2030-04-11T{en}:00+08:00'),201 if ok else 409,not ok)
  reset();_,i=create();create(room_id=2);cancel('U',i);create()
  for adjacent in [False,True]:
   reset();r=compete([('U','/api/bookings','POST',payload()),('V','/api/bookings','POST',payload(start='2030-04-11T11:00:00+08:00',end='2030-04-11T12:00:00+08:00') if adjacent else payload())]);emit('并发重叠/相邻响应与最终占用通知',sorted(x[0] for x in r)==([201,201] if adjacent else [201,409]) and len(snap()['bookings'])==(2 if adjacent else 1) and len(snap()['notifications'])==(2 if adjacent else 1),{'responses':r,'snapshot':snap()})
 group('conflicts',['AI-reservation-creation-9','AI-WB-booking-conflict-serialization'],conflicts)
 def precision():
  global clock
  for state in ['confirmed','cancelled','started']:
   reset();p,bid=create()
   if state=='cancelled':cancel('U',bid)
   if state=='started':clock=dt.datetime.fromisoformat('2030-04-11T10:30:00+08:00')
   for f in ['start','end']:
    for micro in [-1,1]:request('U','/api/bookings','POST',{**p,f:(dt.datetime.fromisoformat(p[f])+dt.timedelta(microseconds=micro)).isoformat()},409,True)
   for offset in ['+00:00','+08:00','Z','zero']:
    q=dict(p)
    for f in ['start','end']:
     val=dt.datetime.fromisoformat(p[f]);q[f]=val.isoformat(timespec='microseconds') if offset=='zero' else val.astimezone(dt.timezone.utc).isoformat().replace('+00:00',offset) if offset in ['+00:00','Z'] else val.isoformat()
    s,b=request('U','/api/bookings','POST',q,201,True);emit('等价时刻保持ID当前状态',b.get('booking',{}).get('id')==bid and b.get('booking',{}).get('status')==('cancelled' if state=='cancelled' else 'confirmed'),b)
 group('precision',['AI-WB-idempotency-absolute-precision'],precision)
 def idempotency():
  global clock
  for state in ['normal','past','disabled','capacity','cancelled']:
   reset();p,bid=create()
   if state=='past':clock=dt.datetime.fromisoformat('2030-04-12T09:00:00+08:00')
   if state=='disabled':request('A','/api/rooms/1','PATCH',room(name='云杉',active=False),200)
   if state=='capacity':request('A','/api/rooms/1','PATCH',room(name='云杉',capacity=1),200)
   if state=='cancelled':cancel('U',bid);create('V')
   for q in [p,{**p,'title':' '+p['title']+' '},{**p,'start':'2030-04-11T02:00:00Z','end':'2030-04-11T03:00:00Z'}]:
    s,b=request('U','/api/bookings','POST',q,201,True);emit('原ID与当前状态重放',b.get('booking')=={'id':bid,'status':'cancelled' if state=='cancelled' else 'confirmed','replayed':True},b)
   for field,value in [('room_id',2),('title','其他主题'),('start','2030-04-11T10:15:00+08:00'),('end','2030-04-11T11:15:00+08:00'),('attendees',3)]:request('U','/api/bookings','POST',{**p,field:value},409,True)
  for same in [True,False]:
   reset();p=payload();q=p if same else {**p,'title':'竞争另一内容'};r=compete([('U','/api/bookings','POST',p),('U','/api/bookings','POST',q)]);emit('并发同key收敛',sorted(x[0] for x in r)==([201,201] if same else [201,409]) and len(snap()['bookings'])==1 and len(snap()['notifications'])==1,r)
   for sent,response in zip([p,q],r):request('U','/api/bookings','POST',sent,response[0],True)
   if same:emit('同内容新建与重放',sorted(x[1]['booking']['replayed'] for x in r)==[False,True],r)
  reset();p,bid=create();request('V','/api/bookings','POST',{**p,'room_id':2},201)
 group('idempotency',['AI-reservation-creation-11','AI-reservation-creation-12','AI-WB-idempotency-priority','AI-WB-idempotency-user-concurrency'],idempotency)
 def room_validation():
  for method in ['POST','PATCH']:
   for field,vals in [('name',[None,1,[],{},'', ' ','中','中'*40,'中'*41,' 中 ']),('location',[None,1,[],{},'', ' ','中','中'*80,'中'*81,' 中 ']),('capacity',[None,[],{},True,False,1.0,'1',0,1,100,101]),('active',[None,[],{},True,False,0,1,'true'])]:
    for val in ['MISSING']+vals:
     reset();p=room();p.pop(field) if val=='MISSING' else p.update({field:val})
     valid=isinstance(val,str) and val!='MISSING' and 1<=len(val.strip())<=(40 if field=='name' else 80) if field in ['name','location'] else isinstance(val,int) and not isinstance(val,bool) and 1<=val<=100 if field=='capacity' else val=='MISSING' or isinstance(val,bool)
     s,b=request('A','/api/rooms'+('/1' if method=='PATCH' else ''),method,p,(201 if method=='POST' else 200) if valid else 400,not valid)
     if valid:
      row=next(x for x in snap()['rooms'] if x['id']==(b['room']['id'] if method=='POST' else 1));emit('持久化规范化room字段',row[field]==(True if val=='MISSING' else val.strip() if isinstance(val,str) else val),row)
 group('room-values',['AI-space-administration-5','AI-WB-room-text-capacity-active'],room_validation)
 def equipment():
  options=['显示屏','白板','视频会议','电话会议']
  vals=[[],*[ [v] for v in options],options,['显示屏','显示屏','白板','白板'],['unknown'],['unknown','白板'],['白板','unknown'],['白板','unknown','显示屏'],'白板',None,[1],[{}],[True],{}]
  for method in ['POST','PATCH']:
   for val in vals:
    reset();valid=isinstance(val,list) and all(isinstance(v,str) and v in options for v in val);s,b=request('A','/api/rooms'+('/1' if method=='PATCH' else ''),method,room(equipment=val),(201 if method=='POST' else 200) if valid else 400,not valid)
    if valid:
     _,rs=request('U','/api/rooms');rr=next(x for x in rs['rooms'] if x['id']==(b['room']['id'] if method=='POST' else 1));emit('设备集合规范化',rr['equipment']==sorted(set(val)),rr)
 group('equipment',['AI-space-administration-6','AI-WB-room-equipment-set'],equipment)
 def permissions():
  for user in ['U','V']:
   page=view(user);emit('普通成员没有管理入口',page.locator('[data-page=manage]').count()==0,{'actor':user})
   request(user,'/api/rooms','POST',room(),403,True);request(user,'/api/rooms/1','PATCH',room(),403,True)
  request('B','/api/rooms/1','PATCH',room(),404,True);request('A','/api/rooms/5','PATCH',room(),404,True);request('A','/api/rooms/999999','PATCH',room(),404,True)
  request('A','/api/rooms','POST',room(),201);request('A','/api/rooms/1','PATCH',room(name='edited'),200)
  request('A','/api/members/3','PATCH',{'role':'admin'},200);request('A','/api/members/3','PATCH',{'role':'member'},200);request('V','/api/rooms/1','PATCH',room(),403,True)
 group('room-permissions',['AI-space-administration-1','AI-space-administration-9'],permissions)
 def roomcrud():
  _,a=request('A','/api/rooms','POST',room(),201);_,b=request('B','/api/rooms','POST',room(),201);_,c=request('A','/api/rooms','POST',room(name='另一空间'),201);emit('跨团队同名独立id',len({a['room']['id'],b['room']['id'],c['room']['id']})==3,[a,b,c])
  for user,team in [('U',1),('B',2)]:_,rs=request(user,'/api/rooms',expect=200);emit('rooms团队完整资料',all(x['team_id']==team and isinstance(x['equipment'],list) and isinstance(x['active'],bool) for x in rs['rooms']),rs)
  p,bid=create(attendees=8);before=snap()['bookings'][0];rv=room(name='云杉')
  for k,v in [('name','改名'),('location','新位置'),('capacity',4),('equipment',[]),('active',False)]:
   rv[k]=v;request('A','/api/rooms/1','PATCH',rv,200);_,bs=request('U','/api/bookings');emit('既有预约不改且join当前资料',snap()['bookings'][0]==before and bs['bookings'][0]['room_name']==rv['name'] and bs['bookings'][0]['location']==rv['location'],bs)
  request('U','/api/bookings','POST',payload(start='2030-04-11T12:00:00+08:00',end='2030-04-11T13:00:00+08:00',attendees=4),409,True)
  rv.update(active=True);request('A','/api/rooms/1','PATCH',rv,200);request('U','/api/bookings','POST',payload(start='2030-04-11T12:00:00+08:00',end='2030-04-11T13:00:00+08:00',attendees=5),400,True);create(start='2030-04-11T12:00:00+08:00',end='2030-04-11T13:00:00+08:00',attendees=4);request('U','/api/bookings','POST',payload(attendees=4),409,True)
  rv=room(name='最终',location='最终层',capacity=1,equipment=['显示屏'],active=False);request('A','/api/rooms/1','PATCH',rv,200)
  pg=pages['A'];pg.goto(base);pg.locator('[data-logout]').first.click();pg.locator('[data-account=admin]').click();pg.get_by_role('button',name='登录工作空间').click();pg.locator('#filter-date').wait_for();cookies['A']='; '.join(f"{x['name']}={x['value']}" for x in pg.context.cookies());request('A','/api/rooms',expect=200)
 group('room-crud',['AI-space-administration-2','AI-space-administration-3','AI-space-administration-8','AI-space-administration-10','AI-reservation-management-2','AI-WB-room-write-and-return','AI-WB-room-state-existing-bookings'],roomcrud)
 def roomunique():
  request('A','/api/rooms','POST',room(name=' 云杉 '),409,True);request('A','/api/rooms/1','PATCH',room(name=' 白桦 '),409,True);request('A','/api/rooms/1','PATCH',room(name=' 云杉 '),200);request('B','/api/rooms','POST',room(name='云杉'),201)
  for mode in ['CC','EE','CE']:
   for reverse in [False,True]:
    reset();before=snap();jobs=[('A','/api/rooms'+('/1' if mode[0]=='E' else ''),'PATCH' if mode[0]=='E' else 'POST',room(name=' RACE ',location='left')),('A','/api/rooms'+('/2' if mode[1]=='E' else ''),'PATCH' if mode[1]=='E' else 'POST',room(name='RACE',location='right'))]
    if reverse:jobs.reverse()
    results=compete(jobs);after=snap();emit('名称竞争只一成功且原记录完整',sum(x[0] in [200,201] for x in results)==1 and sum(x[0]==409 for x in results)==1 and len([x for x in after['rooms'] if x['name']=='RACE'])==1,{'before':before,'after':after,'responses':results})
    for j,r in zip(jobs,results):
     if r[0]==409 and j[2]=='PATCH':rid=int(j[1].split('/')[-1]);emit('失败编辑原全字段不变',next(x for x in before['rooms'] if x['id']==rid)==next(x for x in after['rooms'] if x['id']==rid),after)
    request('A','/api/rooms',expect=200)
    server.shutdown();restart=threading.Thread(target=server.serve_forever,daemon=True);restart.start();_,rs=request('A','/api/rooms',expect=200);emit('重启后名称竞争唯一持久化',len([r for r in rs['rooms'] if r['name']=='RACE'])==1,rs)
  for edit_first in [False,True]:
   reset();jobs=[('A','/api/rooms','POST',room(name=' ORDER ',location='new')),('A','/api/rooms/1','PATCH',room(name='ORDER',location='edited'))]
   if edit_first:jobs.reverse()
   r=[]
   def first():r.append(request(*jobs[0]))
   t=threading.Thread(target=first);t.start();realtime.sleep(.03);r.append(request(*jobs[1]));t.join();emit('交换首次请求先后新增编辑竞争',sorted(x[0] for x in r)==([200,409] if edit_first else [201,409]),{'edit_first':edit_first,'responses':r,'state':snap()})
 group('room-uniqueness',['AI-space-administration-4','AI-WB-room-name-unique-concurrency'],roomunique)
 def qualification():
  for actor in ['U','A']:
   for rid,active,expect in [(1,True,201),(1,False,409),(5,True,404),(999,True,404)]:
    reset();request('A','/api/rooms/1','PATCH',room(name='云杉',active=active),200);request(actor,'/api/bookings','POST',payload(room_id=rid),expect,expect!=201)
  for mode in ['disabled','capacity']:
   reset();page=view('U');page.locator('[data-book-room="1"]').click()
   for n,v in [('title','旧弹窗'),('date','2030-04-11'),('start','10:00'),('end','11:00'),('attendees','8')]:page.locator(f'#booking-form [name={n}]').fill(v)
   request('A','/api/rooms/1','PATCH',room(name='云杉',active=mode!='disabled',capacity=4 if mode=='capacity' else 8),200);before=snap()
   with page.expect_response(lambda r:r.url.endswith('/api/bookings') and r.request.method=='POST') as res:page.locator('#booking-form button[type=submit]').click()
   emit('旧弹窗提交按现状拒绝',res.value.status==(409 if mode=='disabled' else 400) and snap()==before,{'body':res.value.json(),'before':before,'after':snap()});screenshot(page,'stale-'+mode)
   if mode=='capacity':
    page.locator('#booking-form [name=attendees]').fill('4');page.locator('#booking-form button[type=submit]').click();page.locator('#booking-dialog').wait_for(state='hidden');emit('修正容量后成功',len(snap()['bookings'])==1,snap())
   else:page.locator('[aria-label="关闭预约窗口"]').click();request('A','/api/bookings','POST',payload(),409,True)
  reset();create(attendees=8);request('A','/api/rooms/1','PATCH',room(name='云杉',active=False),200)
  request('A','/api/rooms?date=2030-04-11');request('U','/api/bookings');request('A','/api/bookings?scope=team')
  pg=view('U');emit('成员页停用空间不提供入口',pg.locator('[data-book-room="1"]').count()==0,{'text':pg.locator('.rooms-grid').inner_text()});screenshot(pg,'disabled-member')
  pg=pages['A'];pg.goto(base);pg.locator('[data-page=manage]').click();pg.locator('[data-edit-room="1"]').wait_for();screenshot(pg,'disabled-admin')
  for actor in ['U','A']:
   for n in [1,7,8,9]:reset();request(actor,'/api/bookings','POST',payload(attendees=n),201 if n<=8 else 400,n>8)
 group('qualification',['AI-reservation-creation-1','AI-reservation-creation-8','AI-space-administration-7','AI-WB-room-eligibility-capacity'],qualification)
 def cancellation():
  global clock
  for actor in ['U','A','V','B']:
   reset();p,bid=create();before=snap();s,b=cancel(actor,bid,200 if actor in ['U','A'] else 403 if actor=='V' else 404)
   if actor in ['V','B']:emit('越权取消不变量',snap()==before,snap())
  for role in ['admin','member']:
   reset();p,bid=create();request('A','/api/members/3','PATCH',{'role':role},200);cancel('V',bid,200 if role=='admin' else 403)
  for actor in ['U','A']:
   for stamp,ok in [('09:59:59',True),('10:00:00',False),('10:30:00',False),('11:00:00',False),('11:00:01',False)]:
    reset();p,bid=create();clock=dt.datetime.fromisoformat(f'2030-04-11T{stamp}+08:00');before=snap();cancel(actor,bid,200 if ok else 409)
    if not ok:emit('开始后不释放不通知',before==snap(),snap())
   reset();p,bid=create('B',room_id=5);before=snap();cancel(actor,bid,404);cancel(actor,999999,404);emit('跨队及不存在不变',before==snap(),snap());request('B','/api/bookings');request('B','/api/notifications')
 group('cancel-permission-clock',['AI-reservation-management-5','AI-reservation-management-6','AI-reservation-management-9','AI-WB-cancel-authorization-and-clock'],cancellation)
 def cancel_replay():
  global clock
  for actor in ['U','A']:
   reset();p,bid=create();original=snap()['bookings'][0];cancel(actor,bid);cancelled=snap()['bookings'][0];emit('取消保留原字段',all(original[k]==cancelled[k] for k in original if k not in ['status','cancelled_at']) and cancelled['status']=='cancelled' and bool(cancelled['cancelled_at']),cancelled)
   for who in ['U','A','V','B']:request(who,'/api/notifications');request(who,'/api/bookings'+('?scope=team' if who in ['A','B'] else ''))
   _,rs=request('U','/api/rooms?date=2030-04-11');emit('取消日程已释放',all(not x['bookings'] for x in rs['rooms']),rs);create('V');before=snap()
   for advance in [False,True]:
    if advance:clock=dt.datetime.fromisoformat('2030-04-11T12:00:00+08:00')
    for who in ['U','A']:cancel(who,bid);request('U','/api/bookings','POST',p,201,True)
    emit('重复取消和重放不改通知状态或V新单',before==snap(),snap())
  reset();p,bid=create();r=compete([('U',f'/api/bookings/{bid}/cancel','POST',{}),('A',f'/api/bookings/{bid}/cancel','POST',{})]);emit('双取消一通知',all(x[0]==200 for x in r) and len(snap()['notifications'])==2,{'responses':r,'state':snap()});create('V')
 group('cancel-replay',['AI-reservation-creation-13','AI-reservation-management-7','AI-reservation-management-8','AI-notification-center-2','AI-WB-cancel-atomic-idempotent'],cancel_replay)
 def members():
  for actor in ['A','B','U']:
   s,b=request(actor,'/api/members',expect=403 if actor=='U' else 200)
   if actor!='U':emit('成员字段与团队隔离',all(set(x)=={'id','email','name','role'} and (x['id'] in [1,2,3] if actor=='A' else x['id']==4) for x in b['members']),b)
   request(actor,'/api/members?team_id=2',expect=403 if actor=='U' else 200)
  for target,role in [(2,'admin'),(3,'admin'),(1,'member')]:request('U',f'/api/members/{target}','PATCH',{'role':role},403,True)
  request('B','/api/members/2','PATCH',{'role':'admin'},404,True)
  for role in ['admin','member']:request('A','/api/members/3','PATCH',{'role':role},200)
  for role in ['Admin','MEMBER','',' admin','owner',None,1,True,[],{},'MISSING']:
   p={} if role=='MISSING' else {'role':role};request('A','/api/members/3','PATCH',p,400,True)
  for target in [4,999999]:request('A',f'/api/members/{target}','PATCH',{'role':'member'},404,True)
  request('B','/api/session');request('B','/api/members');request('A','/api/members/2','PATCH',{'role':'admin'},200);request('A','/api/members/2','PATCH',{'role':'member'},200);request('U','/api/members',expect=403)
 group('members',['AI-team-administration-1','AI-team-administration-2','AI-team-administration-3','AI-team-administration-6','AI-WB-member-select-role-guards'],members)
 def lastadmin():
  request('A','/api/members/1','PATCH',{'role':'member'},409,True);request('A','/api/members/1','PATCH',{'role':'admin'},200);request('A','/api/members/3','PATCH',{'role':'member'},200);request('A','/api/members/3','PATCH',{'role':'admin'},200);request('A','/api/members/3','PATCH',{'role':'member'},200);request('A','/api/members/1','PATCH',{'role':'member'},409,True)
  for mutual in [False,True]:
   reset();request('A','/api/members/3','PATCH',{'role':'admin'},200);r=compete([('A','/api/members/'+('3' if mutual else '1'),'PATCH',{'role':'member'}),('V','/api/members/'+('1' if mutual else '3'),'PATCH',{'role':'member'})]);admins=[x['id'] for x in snap()['roles'] if x['team_id']==1 and x['role']=='admin'];emit('并发降权保留管理员',len(admins)>=1,{'responses':r,'roles':snap()['roles']})
   for who,uid in [('A',1),('V',3)]:request(who,'/api/members',expect=200 if uid in admins else 403)
 group('last-admin',['AI-team-administration-4','AI-WB-last-admin-lock'],lastadmin)
 def scope_roles():
  for who,rid in [('U',1),('V',2),('B',5)]:create(who,room_id=rid)
  for who in ['U','A','B']:
   for suffix in ['', '?scope=mine','?scope=team','?scope=invalid']:
    expected=400 if suffix.endswith('invalid') else 403 if who=='U' and suffix.endswith('team') else 200;s,b=request(who,'/api/bookings'+suffix,expect=expected)
    if s==200:emit('scope所有者团队隔离',all(x['user_id']=={'U':2,'A':1,'B':4}[who] if not suffix.endswith('team') else x['user_id'] in ([1,2,3] if who=='A' else [4]) for x in b['bookings']),b)
  for operation in ['members','newroom','team','editroom','role','cancel']:
   for promoted in [True,False]:
    reset();create('V',room_id=2);bid=snap()['bookings'][0]['id'];create('U');create('B',room_id=5)
    if not promoted:request('A','/api/members/2','PATCH',{'role':'admin'},200)
    request('A','/api/members/2','PATCH',{'role':'admin' if promoted else 'member'},200)
    path,method,data={'members':('/api/members','GET',None),'newroom':('/api/rooms','POST',room()),'team':('/api/bookings?scope=team','GET',None),'editroom':('/api/rooms/1','PATCH',room()),'role':('/api/members/3','PATCH',{'role':'admin'}),'cancel':(f'/api/bookings/{bid}/cancel','POST',{})}[operation]
    request('U',path,method,data,(201 if operation=='newroom' else 200) if promoted else 403,not promoted);request('U','/api/rooms',expect=200)
 group('scope-and-first-role',['AI-reservation-management-1','AI-team-administration-5','AI-role-first-request-new-room-team','AI-WB-booking-query-scope-join'],scope_roles)
 def notification_generation(N,half=False):
  bid=None
  for i in range(N):
   if i%2==0:_,bid=create()
   else:cancel('U',bid)
   if half and i+1==N//2:mark_ui()
 def notifications():
  for N in [0,1,99,100,101,105]:
   reset();notification_generation(N,True);_,ns=request('U','/api/notifications');rows=snap()['notifications'];expected=list(reversed(rows))[:100];emit('数量节点最近100倒序与已读无过滤',ns['notifications']==expected,{'N':N,'actual':ns,'expected_ids':[x['id'] for x in expected]});mark_ui();_,ns2=request('U','/api/notifications');emit('全部已读保持ID顺序', [x['id'] for x in ns2['notifications']]==[x['id'] for x in ns['notifications']] and all(x['read']==1 for x in ns2['notifications']),ns2)
  reset();create('V',room_id=2);request('U','/api/notifications/read','POST',{},200);request('U','/api/notifications/read','POST',{},200);emit('空集合已读隔离他人',snap()['notifications'][0]['read']==0,snap())
  notification_generation(105);before=snap();page=pages['U'];page.goto(base);page.locator('[data-page=inbox]').click();page.wait_for_timeout(120);emit('105未读列表徽标100',page.locator('.nav-badge').inner_text()=='100',{'badge':page.locator('.nav-badge').inner_text()});screenshot(page,'notifications-105-badge100');mark_ui();after=snap();u=[x for x in after['notifications'] if x['user_id']==2];emit('旧105含最旧5全部已读，V未变',len(u)==105 and all(x['read']==1 for x in u) and next(x for x in after['notifications'] if x['user_id']==3)['read']==0,{'before':before,'after':after,'oldest5':[x['id'] for x in u[:5]]});emit('全读徽标消失',page.locator('.nav-badge').count()==0,{});mark_ui();_,last=create(room_id=3);cancel('U',last);create(room_id=4);page.goto(base);page.locator('[data-page=inbox]').click();page.wait_for_timeout(100);_,ns=request('U','/api/notifications');emit('3新增通知徽标3且97读3未读',page.locator('.nav-badge').inner_text()=='3' and sum(x['read']==0 for x in ns['notifications'])==3 and sum(x['read']==1 for x in ns['notifications'])==97,ns);screenshot(page,'notifications-badge3')
  for who in ['U','V','A','B']:
   _,ns=request(who,'/api/notifications');_,forged=request(who,'/api/notifications?user_id=2');emit('通知只有本人且忽略越权参数',ns==forged and all(x['user_id']=={'U':2,'V':3,'A':1,'B':4}[who] for x in ns['notifications']),forged)
 group('notifications',['AI-notification-center-3','AI-notification-center-4','AI-notification-center-5','AI-notification-center-6','AI-WB-notifications-select-limit','AI-WB-notifications-mark-all'],notifications)
 def discovery_reads():
  for who,team in [('U',1),('A',1),('B',2)]:
   _,rs=request(who,'/api/rooms');_,forged=request(who,f'/api/rooms?team_id={3-team}');emit('房间团队隔离字段',rs==forged and all(x['team_id']==team and all(k in x for k in ['id','name','location','capacity','equipment','active']) for x in rs['rooms']),rs)
  for day in ['2030-04-10','2030-04-11','2030-04-12','', 'not-a-date','2030-02-30']:request('U','/api/rooms?date='+day,expect=200 if day in ['2030-04-10','2030-04-11','2030-04-12'] else 400)
  _,rs=request('U','/api/rooms');emit('省略日期为服务上海今天',rs['date']=='2030-04-10',rs)
 group('room-read-dates',['AI-room-discovery-1','AI-room-discovery-2','AI-WB-rooms-team-deserialization'],discovery_reads)
 def privacy():
  create('U',title='U私有主题');create('V',title='V私有主题',start='2030-04-11T12:00:00+08:00',end='2030-04-11T13:00:00+08:00')
  for who in ['U','V','A','B']:
   _,rs=request(who,'/api/rooms?date=2030-04-11');bs=[b for r in rs['rooms'] for b in r['bookings']];emit('API日程主题隐私',all(b['title']==('U私有主题' if b['user_id']==2 else 'V私有主题') if who=='A' or b['user_id']=={'U':2,'V':3,'A':1,'B':4}[who] else b['title']=='已预约' for b in bs) and (who!='B' or not bs),rs)
   pg=view(who)
   for d in pg.locator('details.room-agenda').all():d.locator('summary').click()
   screenshot(pg,'privacy-'+who)
   text=pg.locator('.rooms-grid').inner_text();emit('UI展开日程隐私',('V私有主题' not in text if who=='U' else 'U私有主题' not in text if who=='V' else 'U私有主题' in text and 'V私有主题' in text if who=='A' else '私有主题' not in text),{'actor':who,'text':text})
  for role in ['admin','member']:
   request('A','/api/members/3','PATCH',{'role':role},200);_,rs=request('V','/api/rooms?date=2030-04-11');bs=[b for r in rs['rooms'] for b in r['bookings']];emit('当前角色立即决定隐私',next(x for x in bs if x['user_id']==2)['title']==('U私有主题' if role=='admin' else '已预约'),rs);pg=view('V');pg.locator('details.room-agenda summary').first.click();screenshot(pg,'privacy-V-'+role)
 group('agenda-privacy',['AI-room-discovery-4','AI-WB-agenda-title-redaction'],privacy)
 def intersections():
  global clock
  clock=dt.datetime.fromisoformat('2030-04-10T00:30:00+08:00');_,today=request('U','/api/rooms');emit('UTC与上海异日默认仍上海',today['date']=='2030-04-10',today)
  p,bid=create();cancel('U',bid);create(start='2030-04-11T12:00:00+08:00',end='2030-04-11T13:00:00+08:00');create(start='2030-04-11T08:00:00+08:00',end='2030-04-11T09:00:00+08:00');create(start='2030-04-12T10:00:00+08:00',end='2030-04-12T11:00:00+08:00')
  for day in ['2030-04-11','2030-04-12']:
   _,rs=request('U','/api/rooms?date='+day);bs=rs['rooms'][0]['bookings'];emit('公开可达同日取消排除排序',all(b['id']!=bid for b in bs) and [b['start'] for b in bs]==sorted(b['start'] for b in bs),rs)
  # Stop serving while constructing a documented historical input fixture from actual legal row schema.
  server.shutdown();thread.join();template=snap()['bookings'][-1]
  fixture=[('2030-04-10T23:45','2030-04-11T00:15','confirmed'),('2030-04-10T23:45','2030-04-11T00:00','confirmed'),('2030-04-11T23:45','2030-04-12T00:15','confirmed'),('2030-04-12T00:00','2030-04-12T00:15','confirmed'),('2030-04-10T23:45','2030-04-12T00:15','confirmed'),('2030-04-10T23:45','2030-04-11T00:15','cancelled'),('2030-04-11T14:00','2030-04-11T15:00','confirmed'),('2030-04-11T12:00','2030-04-11T13:00','confirmed')]
  with sqlite3.connect(DB) as db:
   db.execute('DELETE FROM notifications');db.execute('DELETE FROM bookings')
   for i,(s,e,status) in enumerate(fixture,1):
    
    if i<=6:db.execute('INSERT INTO rooms VALUES (?,?,?, ?,?,?,?)',(100+i,1,f'历史{i}','测试',8,'[]',1))
    db.execute('INSERT INTO bookings (id,team_id,room_id,user_id,title,start,end,attendees,status,created_at,idempotency_key,request_hash) VALUES (?,1,?,2,?,?,?,?,?,?,?,?)',(i,100+i if i<=6 else 101,f'H{i}',dt.datetime.fromisoformat(s+'+08:00').astimezone(dt.timezone.utc).isoformat(),dt.datetime.fromisoformat(e+'+08:00').astimezone(dt.timezone.utc).isoformat(),2,status,clock.isoformat(),f'historical-{i}','synthetic-fixture'))
   emit('历史fixture数据库完整性',db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and db.execute('PRAGMA foreign_key_check').fetchall()==[],fixture)
  t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
  for day in ['2030-04-10','2030-04-11','2030-04-12']:
   _,rs=request('U','/api/rooms?date='+day);actual=[b['id'] for r in rs['rooms'] for b in r['bookings']];start=dt.datetime.fromisoformat(day+'T00:00:00+08:00');end=start+dt.timedelta(days=1);expected=[i for i,(s,e,status) in enumerate(fixture,1) if status=='confirmed' and dt.datetime.fromisoformat(s+'+08:00')<end and dt.datetime.fromisoformat(e+'+08:00')>start];emit('半开区间相交',sorted(actual)==sorted(expected) and all([b['start'] for b in r['bookings']]==sorted(b['start'] for b in r['bookings']) for r in rs['rooms']),{'day':day,'actual':actual,'expected':expected})
 group('day-intersection',['AI-room-discovery-3','AI-WB-day-range-intersection'],intersections)
 def reject_recover():
  for dimension in ['title','past','inactive','foreign','capacity','conflict']:
   reset();p=payload()
   if dimension=='title':p['title']=' '
   if dimension=='past':p.update(start='2030-04-09T10:00:00+08:00',end='2030-04-09T11:00:00+08:00')
   if dimension=='inactive':request('A','/api/rooms/1','PATCH',room(name='云杉',active=False),200)
   if dimension=='foreign':p['room_id']=5
   if dimension=='capacity':p['attendees']=9
   if dimension=='conflict':_,bid=create()
   status,body=request('U','/api/bookings','POST',p,[400,404,409],True);emit('具体失败说明',bool(body.get('error')) and bool(body.get('code')),body)
   if dimension=='inactive':request('A','/api/rooms/1','PATCH',room(name='云杉',active=True),200)
   if dimension=='conflict':cancel('U',bid)
   create()
 group('reject-recover',['AI-reservation-creation-14'],reject_recover)
 def creation_views():
  page=view('U');page.locator('[data-book-room="1"]').click()
  for n,v in [('title',' 完整创建主题 '),('date','2030-04-11'),('start','10:00'),('end','11:00'),('attendees','2')]:page.locator(f'#booking-form [name={n}]').fill(v)
  page.locator('#booking-form button[type=submit]').click();page.locator('#booking-dialog').wait_for(state='hidden');screenshot(page,'creation-outcome');create('V',room_id=2,start='2030-04-11T02:00:00Z',end='2030-04-11T03:00:00Z')
  for who in ['U','V','A','B']:request(who,'/api/notifications');request(who,'/api/bookings'+('?scope=team' if who in ['A','B'] else ''));request(who,'/api/rooms?date=2030-04-11')
  state=snap();emit('每次完整持久化与通知归属',len(state['bookings'])==2 and len(state['notifications'])==2 and all(next(n for n in state['notifications'] if n['booking_id']==b['id'])['user_id']==b['user_id'] and next(n for n in state['notifications'] if n['booking_id']==b['id'])['read']==0 and b['status']=='confirmed' and b['created_at']=='2030-04-10T01:00:00+00:00' for b in state['bookings']),state);request('U','/api/bookings','POST',payload(title=''),400,True)
 group('creation-views',['AI-reservation-creation-10','AI-notification-center-1','AI-WB-booking-insert-notify'],creation_views)
 (E/'ui-network-discovered.json').write_text(json.dumps(network,ensure_ascii=False,indent=2));(E/'environment.json').write_text(json.dumps({'revision':REV,'browser':browser.version,'python':sys.version,'platform':platform.platform(),'clock':'2030 controlled separately for app.datetime.now, app.time.time and page.clock','source_sha256':hashlib.sha256(Path(app.__file__).read_bytes()).hexdigest(),'database_location':str(DB),'remote_integrations':'none'},indent=2));browser.close()
server.shutdown();server.server_close()
# Session values remained in memory/application DB only; discard all ephemeral credential-bearing databases.
for p in R.glob('api-working.sqlite*'):p.unlink(missing_ok=True)
print('COMPLETE',flush=True)
