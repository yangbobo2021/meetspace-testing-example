import sys,pathlib,subprocess,socket,json,http.client,sqlite3,signal,re,datetime as dt,os
r=pathlib.Path(__file__).resolve().parents[2];out=r/'evidence/sigint-complete-r2';out.mkdir();src=r/'harnesses/runtime-source';db=out/'fresh.sqlite';rows=[]
launcher="""import sys,runpy,json,pathlib
source=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(source));sys.argv=['app.server']+sys.argv[3:];events=[]
def trace(frame,event,arg):
 if frame.f_code.co_filename==str(source/'app/server.py') and frame.f_code.co_name=='main':
  if event=='line':events.append({'line':frame.f_lineno})
  elif event=='exception':events.append({'exception':arg[0].__name__,'line':frame.f_lineno})
 return trace
sys.settrace(trace)
try:runpy.run_module('app.server',run_name='__main__')
finally:sys.settrace(None);dest.write_text(json.dumps(events))
"""
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
base='http://127.0.0.1:'+str(port)
def req(path,data=None,cookie=None):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10);h={'Content-Type':'application/json','X-Meeting-App':'1','Origin':base}
 if cookie:h['Cookie']=cookie
 c.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,h);a=c.getresponse();b=json.loads(a.read());heads=dict(a.getheaders());c.close();rows.append({'request':path,'status':a.status,'body':b});return a.status,b,heads

def snap():
 with sqlite3.connect(db) as c:return {t:c.execute('SELECT '+cols+' FROM '+t+' ORDER BY 1').fetchall() for t,cols in [('teams','*'),('users','id,team_id,email,name,role'),('rooms','*'),('bookings','*'),('notifications','*')]}
checks={};before=None
for i in range(2):
 log=(out/f'server-{i}.log').open('w');cmd=[sys.executable,'-B','-c',launcher,str(src),str(out/f'trace-{i}.json'),'--port',str(port),'--db',str(db)];p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=log,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 try:
  line=p.stdout.readline();assert str(port) in line
  if i:checks['same_database_before_login']=snap()==before
  _,_,h=req('/api/login',{'email':'admin@meetspace.test','password':'MeetSpace!2026'});a=h['Set-Cookie'].split(';')[0]
  _,_,h=req('/api/login',{'email':'alice@meetspace.test','password':'MeetSpace!2026'});u=h['Set-Cookie'].split(';')[0]
  if not i:
   status,room,_=req('/api/rooms',{'name':'SIGINT新会议室','location':'5F','capacity':8,'equipment':['白板'],'active':True},a);assert status==201
   day=(dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date()+dt.timedelta(days=1)).isoformat();status,b,_=req('/api/bookings',{'room_id':room['room']['id'],'title':'SIGINT持久化','attendees':2,'start':day+'T10:00:00+08:00','end':day+'T11:00:00+08:00','idempotency_key':'synthetic-sigint'},u);assert status==201
   assert req('/api/notifications/read',{},u)[0]==200;before=snap();checks['prepared_room_booking_notice_read']=bool(before['notifications']) and all(x[-1]==1 for x in before['notifications'])
  for path,t in [('/api/rooms',a),('/api/bookings',u),('/api/notifications',u),('/api/health',None)]:assert req(path,cookie=t)[0]==200
  if i:checks['all_business_fields_and_seed_dates_unchanged']=snap()==before
  p.send_signal(signal.SIGINT);code=p.wait(timeout=15);trace=json.loads((out/f'trace-{i}.json').read_text());checks[f'actual_keyboard_interrupt_{i}']=any(x.get('exception')=='KeyboardInterrupt' for x in trace);checks[f'exit_{i}']=code==0
  with socket.socket() as s:checks[f'listener_closed_{i}']=s.connect_ex(('127.0.0.1',port))!=0
  checks[f'persisted_after_sigint_{i}']=snap()==before
 finally:
  if p.poll() is None:p.terminate();p.wait()
  log.close()
(out/'results.json').write_text(json.dumps({'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','python':sys.version,'source':str(src.relative_to(r)),'actual_port':port,'clock':'real wall clock; tomorrow Beijing legal booking; same saved dates on restart','assertions':checks,'requests':rows,'persisted_snapshot':before,'trace_policy':'read-only Python line/exception tracer; unmodified app.server run as __main__ with real CLI arguments and actual SIGINT'},ensure_ascii=False,indent=2));print(checks)
