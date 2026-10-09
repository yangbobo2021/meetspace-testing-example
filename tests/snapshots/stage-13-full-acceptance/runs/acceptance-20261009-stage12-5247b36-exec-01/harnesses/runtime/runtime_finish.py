import runtime_execute as h
import json,sqlite3,subprocess,hashlib
from pathlib import Path
h.OUT=h.OUT/'finish';h.OUT.mkdir(exist_ok=True)
def extra_envelope():
 h.fresh()
 for headers,body,expected in [({'Content-Length':'-1'},b'',400),({'Content-Length':'abc'},b'',400),({'Content-Length':'0'},b'',400),({'Content-Type':'application/json; charset=utf-8'},b'{"email":"missing","password":"x"}',401),({},b'{"x":"\xff"}',400)]:
  s,b,rh=h.request('/api/login','POST',raw=body,headers=headers);h.mark('raw-envelope',s==expected,{'headers':headers,'status':s});h.mark('json-headers',rh.get('Content-Type')=='application/json; charset=utf-8' and rh.get('Cache-Control')=='no-store' and rh.get('X-Content-Type-Options')=='nosniff')
 a=h.login();before=h.snap()
 for path in ['/api/rooms/','/api/rooms/abc','/api/members/abc','/api/unknown','/api/bookings/abc/cancel']:
  for method in ['GET','POST','PATCH','HEAD']:
   s,b,rh=h.request(path,method,{} if method in ['POST','PATCH'] else None,a);h.mark('unknown-route-'+method+path,s==404 and before==h.snap())
 for path in ['/','/app.js','/style.css']:
  h.mark('static-post-refused',h.request(path,'POST',{},a)[0]==404)
 h.fault[0]={'match':'SELECT 1','exc':sqlite3.OperationalError};h.mark('health-storage-fault',h.request('/api/health')[0]==503);h.mark('health-recovered',h.request('/api/health')[0]==200)

def switching_create():
 for src,dst,room,foreign in [('alice','other',5,4),('other','alice',4,5)]:
  for rid in [room,foreign]:
   h.fresh();old=h.login(src);other=h.login(src);new=h.login(dst,old);before=h.snap();s,r,rh=h.request('/api/bookings','POST',{**h.booking,'room_id':rid},new);h.mark('first-write-'+src+dst+str(rid),s==(201 if rid==room else 404));
   if rid==foreign:h.mark('foreign-no-write',before==h.snap())
   h.mark('old-invalid',h.request('/api/session',cookie=old)[0]==401);h.mark('other-valid',h.request('/api/session',cookie=other)[0]==200);h.request('/api/bookings',cookie=new)

def ui_all():
 for src,dst in [('alice','bob'),('alice','admin'),('admin','alice'),('alice','other'),('other','alice')]:
  h.fresh();r=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python',str(Path(__file__).with_name('runtime_switch_ui.py')),h.base,str(h.OUT),src,dst],capture_output=True,text=True);h.mark('browser-switch-'+src+dst,r.returncode==0,{'stdout':r.stdout,'stderr':r.stderr})

def final_session_join():
 h.fresh();a=h.login();u=h.login('alice');b=h.login('other')
 for role in ['admin','member']:
  h.request('/api/members/2','PATCH',{'role':role},a);h.mark('direct-role-refresh',h.request('/api/members',cookie=u)[0]==(200 if role=='admin' else 403))
 with sqlite3.connect(h.db) as c:c.execute('UPDATE users SET team_id=2 WHERE id=2')
 s,r,rh=h.request('/api/rooms',cookie=u);h.mark('synthetic-team-join',s==200 and [x['id'] for x in r['rooms']]==[5]);h.request('/api/session',cookie=u)
 h.clock[0]=h.T+10;fresh=h.login('bob');h.clock[0]=h.T+28800;h.server.login_attempts.clear();h.login('admin');h.mark('unexpired-other-retained',h.request('/api/session',cookie=fresh)[0]==200);h.mark('expired-cleaned',all(x[1]>h.clock[0] for x in h.snap()['sessions']))

def repeat_seed_login():
 for hour in ['00:30:00','09:00:00']:
  for tz in ['UTC','Asia/Shanghai']:
   for empty in [False,True]:
    h.fresh();h.server.shutdown();h.server.server_close();h.thread.join();h.counter+=1;h.db=h.OUT/f'seed-login-{h.counter}.sqlite';h.os.environ['TZ']=tz;h.time.tzset();h.clock[0]=h.dt.datetime.fromisoformat('2030-04-10T'+hour+'+08:00').timestamp()
    if empty:sqlite3.connect(h.db).close()
    h.server=h.app.ApplicationServer(('127.0.0.1',0),h.app.Store(h.db));h.thread=h.threading.Thread(target=h.server.serve_forever,daemon=True);h.thread.start();h.base='http://127.0.0.1:'+str(h.server.server_port)
    for user in ['admin','alice','bob','other']:
     token=h.login(user);h.mark('seed-login-'+hour+tz+str(empty)+user,token is not None);h.request('/api/session',cookie=token);h.request('/api/rooms?date=2030-04-11',cookie=token);h.request('/api/bookings',cookie=token)
for name,fn in [('extra-envelope-dispatch',extra_envelope),('cross-team-first-write',switching_create),('ui-switch-and-errors',ui_all),('session-dynamic-join-cleanup',final_session_join),('all-seed-logins',repeat_seed_login)]:h.save(name,fn)
h.server.shutdown();h.server.server_close();(h.OUT/'trace.json').write_text(json.dumps({'lines':sorted(h.trace),'sql_operations':h.sql_events},indent=2))
