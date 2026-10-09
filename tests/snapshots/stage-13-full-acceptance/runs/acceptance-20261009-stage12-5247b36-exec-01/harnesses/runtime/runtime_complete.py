import runtime_execute as h
import json,sqlite3,socket,types,subprocess,threading,time,hashlib
from pathlib import Path
h.OUT=h.OUT/'completion';h.OUT.mkdir(exist_ok=True)
original_conn=h.Conn
class TraceConn(original_conn):
 def execute(self,sql,*a):
  f=h.fault[0]
  if f and f.get('before') and f.get('match') in sql:h.fault[0]=None;raise f['exc']('synthetic dependency fault')
  return super().execute(sql,*a)
 def commit(self):
  f=h.fault[0]
  if f and f.get('seed_commit') and self.c.in_transaction and self.c.execute('SELECT count(*) FROM teams').fetchone()[0]>0:h.fault[0]=None;raise sqlite3.OperationalError('synthetic seed commit fault')
  h.sql_events.append('COMMIT');return super().commit()
 def rollback(self):h.sql_events.append('ROLLBACK');return self.c.rollback()
 def close(self):h.sql_events.append('CLOSE');return self.c.close()
h.Conn=TraceConn

def restart_target():
 port=h.server.server_port;h.server.shutdown();h.server.server_close();h.thread.join();h.server=h.app.ApplicationServer(('127.0.0.1',port),h.app.Store(h.db));h.thread=threading.Thread(target=h.server.serve_forever,daemon=True);h.thread.start()
def probe_reads(a,u):
 for path,t in [('/api/rooms',a),('/api/bookings?scope=team',a),('/api/members',a),('/api/notifications',u)]:h.request(path,cookie=t)

def missing_formats():
 h.fresh()
 for f in ['email','password']:
  d={'email':'admin@meetspace.test','password':h.PW};del d[f];h.mark('missing-'+f,h.request('/api/login','POST',d)[0]==400)
 h.server.login_attempts.clear()
 for i in range(10):h.request('/api/login','POST',{'email':None,'password':'x'})
 for i in range(8):h.mark('invalid-not-counted-'+str(i),h.request('/api/login','POST',{'email':'admin@meetspace.test','password':h.PW})[0]==200)
 h.mark('ninth-limited',h.request('/api/login','POST',{'email':'none','password':'x'})[0]==429)
 for f,size in [('email',1),('email',160),('password',1),('password',256)]:
  h.server.login_attempts.clear();email='z'*size if f=='email' else 'boundary@test';pw='z'*size if f=='password' else h.PW
  with sqlite3.connect(h.db) as c:c.execute('INSERT OR REPLACE INTO users VALUES(9,1,?,?,?,?)',(email,'边界','member',h.app.password_hash(pw)))
  h.mark('matching-boundary-'+f+str(size),h.request('/api/login','POST',{'email':email,'password':pw})[0]==200)

def full_rates():
 for seq in ['success','failure','mixed-format','minute-crossing']:
  h.fresh();base=h.T+50 if seq=='minute-crossing' else h.T
  for i in range(8):
   h.clock[0]=base+i*5
   if seq=='mixed-format':h.request('/api/login','POST',{'email':None,'password':None})
   status=h.request('/api/login','POST',{'email':'admin@meetspace.test','password':'wrong' if seq=='failure' else h.PW})[0];h.mark(seq+'-'+str(i),status==(401 if seq=='failure' else 200))
  h.mark(seq+'-ninth',h.request('/api/login','POST',{'email':'other@meetspace.test','password':h.PW})[0]==429)
 h.fresh()
 for i in range(8):h.clock[0]=h.T+i;h.request('/api/login','POST',{'email':'missing','password':'x'})
 for second in [60,61]:
  h.clock[0]=h.T+second;h.mark('staggered-'+str(second),h.request('/api/login','POST',{'email':'missing','password':'x'})[0]==401);h.mark('staggered-full-'+str(second),h.request('/api/login','POST',{'email':'missing','password':'x'})[0]==429)
 for ip in ['127.0.0.2','127.0.0.3']:
  try:
   s=socket.socket();s.bind((ip,0));s.close();h.mark('second-ip-bind',True,ip)
  except OSError as e:h.current.append({'branch':'second-ip-bind','status':'blocked','actual':str(e),'ip':ip})

def invalid_sessions():
 h.fresh();a=h.login();old=h.login('alice');h.request('/api/logout','POST',{},old);expired=h.login('alice');h.clock[0]=h.T+28800;h.server.login_attempts.clear();a=h.login()
 routes=[('/api/session','GET',None),('/api/rooms','GET',None),('/api/bookings','GET',None),('/api/bookings','POST',h.booking),('/api/bookings/1/cancel','POST',{}),('/api/notifications','GET',None),('/api/notifications/read','POST',{}),('/api/members','GET',None),('/api/members/3','PATCH',{'role':'admin'}),('/api/rooms','POST',h.room),('/api/rooms/1','PATCH',h.room),('/api/logout','POST',{})]
 before=h.snap()
 for label,token in [('none',None),('invalid','synthetic-invalid'),('revoked',old),('expired',expired)]:
  for path,method,data in routes:h.mark(label+method+path,h.request(path,method,data,token)[0]==401 and before==h.snap())
 probe_reads(a,a)

def two_expiries():
 for delta in [28799,28800,28801]:
  h.fresh();one=h.login('alice');two=h.login('alice');before=h.snap()['sessions']
  for advance in [10,1000,20000]:h.clock[0]=h.T+advance;h.request('/api/rooms',cookie=one)
  restart_target();h.clock[0]=h.T+delta
  for token in [one,two]:
   for p in ['/api/session','/api/rooms']:h.mark('two-expiry-'+str(delta)+p,h.request(p,cookie=token)[0]==(200 if delta<28800 else 401))
   if delta>=28800:h.mark('expired-booking',h.request('/api/bookings','POST',h.booking,token)[0]==401)
  h.mark('expiry-fixed-after-restart',before==h.snap()['sessions'])

def storage_errors():
 for kind in ['add','create']:
  for exc,code,status in [(sqlite3.IntegrityError,'data_conflict',409),(sqlite3.OperationalError,'storage_unavailable',503),(RuntimeError,'internal_error',500)]:
   for repeat in range(2):
    path,method,data,token=h.setup_route(kind);before=h.snap();h.fault[0]={'before':True,'match':'INSERT INTO rooms' if kind=='add' else 'INSERT INTO bookings','exc':exc};s,r,rh=h.request(path,method,data,token);h.mark(kind+code+str(repeat),s==status and r.get('code')==code and before==h.snap());h.mark('recovery',h.request(path,method,data,token)[0]==201)
 path,method,data,token=h.setup_route('add');before=h.snap();lock=sqlite3.connect(h.db,isolation_level=None);lock.execute('BEGIN IMMEDIATE')
 s,r,rh=h.request(path,method,data,token);h.mark('real-sqlite-write-lock',s==503 and r.get('code')=='storage_unavailable');lock.rollback();lock.close();h.mark('real-lock-no-write',before==h.snap());h.mark('real-lock-recovered',h.request(path,method,data,token)[0]==201)

def seed_final():
 p=h.OUT/'seed-final.sqlite';h.fault[0]={'seed_commit':True}
 try:h.app.Store(p);h.mark('seed-final-commit-failed',False)
 except sqlite3.OperationalError:h.mark('seed-final-commit-failed',True)
 with sqlite3.connect(p) as c:counts=[c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['teams','users','rooms','bookings']]
 h.mark('seed-final-rolled-back',counts==[0,0,0,0],counts);h.fault[0]=None;h.app.Store(p)
 with sqlite3.connect(p) as c:counts=[c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['teams','users','rooms','bookings']]
 h.mark('seed-final-retry',counts==[2,4,5,3],counts)
 p=h.OUT/'existing-team.sqlite';c=sqlite3.connect(p);c.executescript(h.app.SCHEMA);c.execute("INSERT INTO teams VALUES(99,'existing fixture')");c.commit();c.close();h.app.Store(p)
 with sqlite3.connect(p) as c:counts=[c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['teams','users','rooms','bookings']]
 h.mark('existing-team-no-seed',counts==[1,0,0,0],counts)

def write_matrix():
 cases=['create','cancel','admin-cancel','read','add-active','add-inactive','edit','promote','demote','logout','login-old-delete','login-insert','create-notify','cancel-notify']
 for kind in cases:
  for stage in ['after','commit']:
   setup={'admin-cancel':'cancel','add-active':'add','add-inactive':'add','promote':'role','demote':'role','login-old-delete':'login','login-insert':'login','create-notify':'create','cancel-notify':'cancel'}.get(kind,kind)
   path,method,data,token=h.setup_route(setup)
   if kind=='admin-cancel':token=h.login()
   if kind=='add-inactive':data={**data,'active':False}
   if kind=='edit':data={**data,'name':'全部新字段','location':'9F','capacity':9,'equipment':['显示屏','电话会议'],'active':False}
   if kind=='demote':
    h.request('/api/members/3','PATCH',{'role':'admin'},token);data={'role':'member'}
   if kind=='read':
    with sqlite3.connect(h.db) as c:
     c.executemany('INSERT INTO notifications(user_id,booking_id,message,created_at,read) VALUES(2,1,?,?,0)',[(f'synthetic-{i}',h.app.now_iso()) for i in range(105)])
     c.execute("INSERT INTO notifications(user_id,booking_id,message,created_at,read) VALUES(3,2,'other',?,0)",(h.app.now_iso(),))
   if kind.startswith('login-'):token=h.login('alice')
   matches={'create':'INSERT INTO bookings','cancel':'UPDATE bookings','admin-cancel':'UPDATE bookings','read':'UPDATE notifications','add-active':'INSERT INTO rooms','add-inactive':'INSERT INTO rooms','edit':'UPDATE rooms','promote':'UPDATE users','demote':'UPDATE users','logout':'DELETE FROM sessions','login-old-delete':'DELETE FROM sessions WHERE token_hash','login-insert':'INSERT INTO sessions','create-notify':'INSERT INTO notifications','cancel-notify':'INSERT INTO notifications'}
   before=h.snap();h.fault[0]={'commit':True,'exc':sqlite3.OperationalError} if stage=='commit' else {'match':matches[kind],'exc':sqlite3.OperationalError}
   s,r,rh=h.request(path,method,data,token);h.mark(kind+stage+'-error',s==503);h.mark(kind+stage+'-rollback',before==h.snap());restart_target();h.mark(kind+stage+'-restart',before==h.snap());h.mark(kind+stage+'-retry',h.request(path,method,data,token)[0] in [200,201]);h.request('/api/rooms',cookie=h.login());h.request('/api/notifications',cookie=h.login('alice'))

def process_restart():
 if 'server' in h.__dict__:h.server.shutdown();h.server.server_close();h.thread.join()
 h.db=h.OUT/'process-persist.sqlite';proc=None
 def launch():
  nonlocal proc
  log=open(h.OUT/'process-server.log','a');proc=subprocess.Popen([h.sys.executable,str(Path(__file__).with_name('runtime_child.py')),str(h.db),str(h.T)],stdout=subprocess.PIPE,stderr=log,text=True,env={**h.os.environ,'PYTHONDONTWRITEBYTECODE':'1'});port=json.loads(proc.stdout.readline())['port'];h.server=types.SimpleNamespace(server_port=port);h.base='http://127.0.0.1:'+str(port)
 try:
  launch();a=h.login();u=h.login('alice');h.request('/api/rooms','POST',h.room,a);h.request('/api/rooms/1','PATCH',{**h.room,'name':'restart-edited'},a);h.request('/api/members/3','PATCH',{'role':'admin'},a);h.request('/api/bookings','POST',h.booking,u);h.request('/api/bookings/1/cancel','POST',{},u);h.request('/api/notifications/read','POST',{},u);h.request('/api/bookings','POST',{**h.booking,'idempotency_key':'second','start':'2030-04-11T12:00:00+08:00','end':'2030-04-11T13:00:00+08:00'},u);before=h.snap()
  for i in range(2):
   proc.terminate();proc.wait();launch();h.mark('real-process-restart-snapshot-'+str(i),before==h.snap());probe_reads(a,u);s,b,rh=h.request('/api/health');h.mark('real-process-restart-health',s==200 and b=={'status':'ok','version':'1.0.0-rc.1','timezone':'Asia/Shanghai'});h.request('/api/health',cookie=a)
   r=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python',str(Path(__file__).with_name('runtime_logout_ui.py')),h.base,str(h.OUT),str(i)],capture_output=True,text=True);h.mark('restart-ui-logout-'+str(i),r.returncode==0,{'out':r.stdout,'err':r.stderr})
   before=h.snap()
 finally:
  if proc:proc.terminate();proc.wait()
for name,fn in [('missing-formats',missing_formats),('complete-rates',full_rates),('invalid-session-matrix',invalid_sessions),('two-expiry',two_expiries),('storage-errors',storage_errors),('seed-final',seed_final),('write-matrix',write_matrix),('real-process-restarts',process_restart)]:h.save(name,fn)
(h.OUT/'trace.json').write_text(json.dumps({'lines':sorted(h.trace),'sql_events':h.sql_events,'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa'},indent=2))
