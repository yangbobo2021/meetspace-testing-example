import sys, os, json, sqlite3, threading, http.client, datetime as dt, time, hashlib, subprocess, importlib.util, concurrent.futures
from pathlib import Path
ROOT=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking'); RUN=ROOT/'tests/delivery-acceptance/runs/acceptance-20261009-stage12-5247b36-exec-01'; OUT=RUN/'evidence/runtime'; OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('target',ROOT/'app/server.py'); app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
T=dt.datetime.fromisoformat('2030-04-10T09:00:00+08:00').timestamp(); clock=[T]
class Date(dt.datetime):
 @classmethod
 def now(cls,tz=None):return cls.fromtimestamp(clock[0],tz)
class Time:
 @staticmethod
 def time():return clock[0]
app.datetime=Date;app.time=Time
trace=set()
def tracer(frame,event,arg):
 if frame.f_code.co_filename==str(ROOT/'app/server.py') and event=='line':trace.add(frame.f_lineno)
 return tracer
threading.settrace(tracer);sys.settrace(tracer)
records=[]; current=[]; counter=int(time.time())
PW='MeetSpace!2026'; tokens={}; conn_orig=sqlite3.connect; fault=[None];sql_events=[]
class Conn:
 def __init__(self,c):object.__setattr__(self,'c',c)
 def __getattr__(self,k):return getattr(self.c,k)
 def __setattr__(self,k,v):setattr(self.c,k,v)
 def execute(self,sql,*a):
  r=self.c.execute(sql,*a); sql_events.append(sql.split()[0]);f=fault[0]
  if f and f.get('match') and f['match'] in sql:
   f['seen']=f.get('seen',0)+1
   if f['seen']==f.get('nth',1):fault[0]=None;raise f['exc']('synthetic dependency fault')
  return r
 def executemany(self,sql,rows):
  for row in rows:self.execute(sql,row)
 def commit(self):
  if fault[0] and fault[0].get('commit'): f=fault[0];fault[0]=None;raise f['exc']('synthetic commit fault')
  return self.c.commit()
 def __enter__(self):return self
 def __exit__(self,*a):return self.c.__exit__(*a)
class SQLite:
 OperationalError=sqlite3.OperationalError;IntegrityError=sqlite3.IntegrityError;Row=sqlite3.Row
 @staticmethod
 def connect(*a,**k):return Conn(conn_orig(*a,**k))
app.sqlite3=SQLite

def mark(label,ok,detail=None):
 r={'branch':label,'passed':bool(ok),'actual':detail};current.append(r);return ok

def request(path,method='GET',data=None,cookie=None,headers=None,raw=None):
 body=raw if raw is not None else (json.dumps(data,ensure_ascii=False).encode() if data is not None else None)
 h={'Content-Type':'application/json','X-Meeting-App':'1','Origin':base}
 if cookie:h['Cookie']='meetspace_session='+cookie
 if headers:
  for k,v in headers.items():
   if v is None:h.pop(k,None)
   else:h[k]=v
 c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=15);c.request(method,path,body,h);r=c.getresponse();b=r.read();rh=dict(r.getheaders());c.close()
 try:b=json.loads(b)
 except Exception:b={'bytes':len(b)}
 current.append({'request':method+' '+path,'status':r.status,'body':b,'cookie_attributes':rh.get('Set-Cookie','').split(';')[1:]})
 return r.status,b,rh

def login(user='admin',old=None,password=PW):
 s,b,h=request('/api/login','POST',{'email':user+'@meetspace.test','password':password},old)
 return h.get('Set-Cookie','').split(';')[0].partition('=')[2] if s==200 else None

def snap():
 with conn_orig(db) as c:
  return {t:c.execute('SELECT '+cols+' FROM '+t+' ORDER BY 1').fetchall() for t,cols in [('teams','*'),('users','id,team_id,email,name,role'),('rooms','*'),('bookings','*'),('notifications','*'),('sessions','user_id,expires')]}

def fresh():
 global server,thread,base,db,counter
 if 'server' in globals():server.shutdown();server.server_close();thread.join()
 counter+=1;clock[0]=T;db=OUT/f'db-{counter}.sqlite';server=app.ApplicationServer(('127.0.0.1',0),app.Store(db));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)

def save(name,fn):
 global current
 current=[]
 try:fn();error=None
 except Exception as e:error=type(e).__name__+': '+str(e)
 r={'group':name,'error':error,'checks':current};records.append(r);(OUT/'branches.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print(name,len(current),error,flush=True)

room={'name':'合成空间','location':'4F','capacity':8,'equipment':['白板'],'active':True}
booking={'room_id':4,'title':'合成预约','attendees':2,'start':'2030-04-11T10:00:00+08:00','end':'2030-04-11T11:00:00+08:00','idempotency_key':'run-runtime'}
def ui():
 fresh()
 result=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python',str(Path(__file__).with_name('runtime_ui.py')),base,str(OUT)],capture_output=True,text=True)
 mark('actual-browser-four-identities',result.returncode==0,{'stdout':result.stdout,'stderr':result.stderr})

def identity():
 fresh();a=login();u=login('alice');v=login('bob');b=login('other')
 for token,uid,team,role in [(a,1,1,'admin'),(u,2,1,'member'),(v,3,1,'member'),(b,4,2,'admin')]:
  s,r,h=request('/api/session',cookie=token);mark('identity-fields',s==200 and r['user']['id']==uid and r['user']['team_id']==team and r['user']['role']==role and r['timezone']=='Asia/Shanghai' and r['version']=='1.0.0-rc.1',r)
 for role in ['admin','member']:
  request('/api/members/2','PATCH',{'role':role},a);s,r,h=request('/api/members',cookie=u);mark('next-request-role-'+role,s==(200 if role=='admin' else 403));request('/api/session',cookie=u)
 for old in [a,u]:
  for target in ['admin','alice','other','missing']:
   server.login_attempts.clear();before=snap();s,r,h=request('/api/login','POST',{'email':target+'@meetspace.test','password':'synthetic-wrong'},old);mark('existing-session-wrong-'+target,s==401 and r.get('code')=='invalid_credentials' and before==snap());request('/api/session',cookie=old)
 server.login_attempts.clear();old=a;other=login();new=login('alice',old);mark('switch-old-rejected',request('/api/session',cookie=old)[0]==401);mark('switch-other-preserved',request('/api/members',cookie=other)[0]==200);mark('switch-member-forbidden',request('/api/members',cookie=new)[0]==403)
 s,r,h=request('/api/logout','POST',{},new);mark('logout-cookie',s==200 and all(x in h.get('Set-Cookie','') for x in ['HttpOnly','SameSite=Lax','Path=/','Max-Age=0']));mark('logout-replay',request('/api/session',cookie=new)[0]==401);mark('logout-other',request('/api/session',cookie=other)[0]==200)

def formats():
 fresh();good={'email':'admin@meetspace.test','password':PW}
 for field,limit in [('email',160),('password',256)]:
  for value in [None,True,3,[],{},'',' ', 'x'*(limit+1)]:
   d={**good,field:value};s,r,h=request('/api/login','POST',d);mark(field+'-invalid-'+str(type(value)),s==400)
  for size in [1,limit]:
   server.login_attempts.clear();s,r,h=request('/api/login','POST',{**good,field:'x'*size});mark(field+'-valid-length-'+str(size),s==401)
 server.login_attempts.clear();s,r,h=request('/api/login','POST',{'email':' ADMIN@MEETSPACE.TEST ','password':' '+PW+' '});mark('trim-case',s==200)

def expiry():
 for delta in [28799,28800,28801]:
  fresh();u=login('alice');initial=snap()['sessions'];clock[0]=T+100;request('/api/rooms',cookie=u);clock[0]=T+delta
  for path in ['/api/session','/api/rooms']:
   s,r,h=request(path,cookie=u);mark('expiry-'+str(delta)+path,s==(200 if delta<28800 else 401))
  if delta>=28800:mark('expired-write',request('/api/bookings','POST',booking,u)[0]==401)
  mark('non-sliding',snap()['sessions']==initial)

def rate():
 for point in [59.999,60,60.001]:
  fresh()
  for i in range(8):
   clock[0]=T+i*5;s,r,h=request('/api/login','POST',{'email':'admin@meetspace.test','password':PW if i%2==0 else 'wrong'});mark('accepted-'+str(i),s in [200,401])
  clock[0]=T+point;s,r,h=request('/api/login','POST',{'email':'admin@meetspace.test','password':PW});mark('boundary-'+str(point),s==(429 if point<60 else 200))
  if point>=60:mark('one-slot-only',request('/api/login','POST',{'email':'admin@meetspace.test','password':PW})[0]==429)
 fresh()
 with concurrent.futures.ThreadPoolExecutor(9) as pool:out=list(pool.map(lambda _:request('/api/login','POST',{'email':'none','password':'wrong'})[0],range(9)))
 mark('concurrent-lock',sorted(out)==[401]*8+[429],out)

def setup_route(kind):
 fresh();a=login();u=login('alice')
 if kind=='login':return '/api/login','POST',{'email':'bob@meetspace.test','password':PW},None
 if kind=='logout':return '/api/logout','POST',{},u
 if kind=='create':return '/api/bookings','POST',booking,u
 if kind=='cancel':return '/api/bookings/1/cancel','POST',{},u
 if kind=='read':request('/api/bookings','POST',booking,u);return '/api/notifications/read','POST',{},u
 if kind=='add':return '/api/rooms','POST',room,a
 if kind=='edit':return '/api/rooms/1','PATCH',room,a
 return '/api/members/3','PATCH',{'role':'admin'},a

def envelopes():
 for kind in ['login','logout','create','cancel','read','add','edit','role']:
  for variant in ['valid','missing-marker','marker0','marker2','scheme','host','port','no-origin','both','text','no-type','array','string','number','true','null','broken','zero','one','empty-object','65536','65537','utf8']:
   path,method,data,token=setup_route(kind);before=snap();h={};raw=None
   if variant=='missing-marker':h={'X-Meeting-App':None}
   if variant in ['marker0','marker2']:h={'X-Meeting-App':variant[-1]}
   if variant=='scheme':h={'Origin':base.replace('http:','https:')}
   if variant=='host':h={'Origin':base.replace('127.0.0.1','localhost')}
   if variant=='port':h={'Origin':'http://127.0.0.1:1'}
   if variant=='no-origin':h={'Origin':None}
   if variant=='both':h={'Origin':'http://evil.test','X-Meeting-App':None}
   if variant=='text':h={'Content-Type':'text/plain'}
   if variant=='no-type':h={'Content-Type':None}
   raws={'array':b'[]','string':b'"x"','number':b'1','true':b'true','null':b'null','broken':b'{','zero':b'','one':b'0','empty-object':b'{}','utf8':b'{"x":"\xff"}'}
   raw=raws.get(variant)
   if variant in ['65536','65537']:
    raw=json.dumps(data,ensure_ascii=False).encode();raw+=b' '*(int(variant)-len(raw))
   s,r,rh=request(path,method,data,token,h,raw);success=variant in ['valid','no-origin','65536'] or variant=='empty-object' and kind in ['logout','cancel','read']
   mark(kind+'-'+variant,(s<300)==success,{'status':s,'bytes':len(raw) if raw is not None else None})
   if not success:mark(kind+'-'+variant+'-no-side-effect',before==snap())

def faults():
 for kind in ['create','cancel','read','add','edit','role','logout','login']:
  for stage in ['after-write','commit']:
   path,method,data,token=setup_route(kind);before=snap();matches={'create':'INSERT INTO bookings','cancel':'UPDATE bookings','read':'UPDATE notifications','add':'INSERT INTO rooms','edit':'UPDATE rooms','role':'UPDATE users','logout':'DELETE FROM sessions','login':'INSERT INTO sessions'}
   fault[0]={'commit':True,'exc':sqlite3.OperationalError} if stage=='commit' else {'match':matches[kind],'exc':sqlite3.OperationalError}
   s,r,h=request(path,method,data,token);mark(kind+'-'+stage+'-503',s==503 and r.get('code')=='storage_unavailable');mark(kind+'-'+stage+'-rollback',before==snap());fault[0]=None
 for exc,code,status in [(sqlite3.IntegrityError,'data_conflict',409),(sqlite3.OperationalError,'storage_unavailable',503),(RuntimeError,'internal_error',500)]:
  path,method,data,token=setup_route('add');before=snap();fault[0]={'match':'INSERT INTO rooms','exc':exc};s,r,h=request(path,method,data,token);mark('error-'+code,s==status and r.get('code')==code and 'synthetic' not in str(r));mark('error-rollback',before==snap())

def seed_faults():
 for table,n in [('teams',1),('teams',2),('users',1),('users',4),('rooms',1),('rooms',5),('bookings',1),('bookings',2),('bookings',3)]:
  p=OUT/f'seed-{counter}-{table}-{n}.sqlite';fault[0]={'match':'INSERT INTO '+table,'nth':n,'exc':sqlite3.OperationalError}
  try:app.Store(p);mark('seed-fault-reached',False)
  except sqlite3.OperationalError:mark('seed-fault-reached',True,table)
  with conn_orig(p) as c: counts=[c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['teams','users','rooms','bookings']]
  mark('seed-rollback-'+table+str(n),counts==[0,0,0,0],counts);fault[0]=None;app.Store(p)
  with conn_orig(p) as c: counts=[c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['teams','users','rooms','bookings']]
  mark('seed-retry-'+table+str(n),counts==[2,4,5,3],counts)

def health():
 fresh()
 for token in [None,login()]:
  s,r,h=request('/api/health',cookie=token);mark('health-contract',s==200 and r=={'status':'ok','version':'1.0.0-rc.1','timezone':'Asia/Shanghai'})
 for path in ['/','/app.js','/style.css']:
  for method in ['GET','HEAD']:
   s,r,h=request(path,method);mark('static-'+method+path,s==200 and int(h['Content-Length'])>0 and h.get('X-Content-Type-Options')=='nosniff')
 for path in ['/unknown','/../app/server.py','/api/rooms','/api/members','/api/bookings','/api/notifications']:
  s,r,h=request(path);mark('denied-'+path,s in [401,404] and 'code' in r)

def persistence():
 fresh();a=login();u=login('alice');request('/api/rooms','POST',room,a);request('/api/rooms/1','PATCH',{**room,'name':'新云杉'},a);request('/api/members/3','PATCH',{'role':'admin'},a);request('/api/bookings','POST',booking,u);request('/api/bookings/1/cancel','POST',{},u);request('/api/notifications/read','POST',{},u);before=snap()
 for jump in [0,172800]:
  clock[0]=T+jump;server.shutdown();server.server_close();thread.join();app.Store(db);mark('restart-persistence-'+str(jump),before==snap())

def password():
 fresh()
 with conn_orig(db) as c: rows=c.execute('select id,password_hash from users').fetchall()
 salts=[]
 for uid,value in rows:
  salt,digest=value.split(':');salts.append(salt);good=hashlib.scrypt(PW.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();bad=hashlib.scrypt(b'wrong',salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();mark('independent-scrypt-'+str(uid),good==digest and bad!=digest)
 mark('salt-distinct',len(set(salts))==4)

if __name__ == "__main__":
 for name,fn in [('ui',ui),('health',health),('identity',identity),('formats',formats),('expiry',expiry),('rate',rate),('envelopes',envelopes),('faults',faults),('seed-faults',seed_faults),('password',password),('persistence',persistence)]:save(name,fn)
 try:server.shutdown();server.server_close()
 except Exception:pass
 (OUT/'execution-meta.json').write_text(json.dumps({'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':sys.version,'platform':sys.platform,'fixed_clock':T,'source_sha256':hashlib.sha256((ROOT/'app/server.py').read_bytes()).hexdigest(),'executed_lines':sorted(trace),'sqlite_events':{x:sql_events.count(x) for x in set(sql_events)},'mode':'real local HTTP application; SQLite dependency fault adapter; no third-party Mock E2E'},indent=2))
