"""Observe actual DML return, allow commits, then fail BEFORE second write."""
import runtime_execute as h
import json, sqlite3, subprocess, threading, types
from pathlib import Path
h.OUT=h.RUN/'evidence/runtime-write-gaps';h.OUT.mkdir(exist_ok=True)
events=[];armed=None;probe=False
class GapConnection:
 def __init__(self,c):object.__setattr__(self,'c',c)
 def __getattr__(self,k):return getattr(self.c,k)
 def __setattr__(self,k,v):setattr(self.c,k,v)
 def execute(self,sql,*args):
  global armed
  if probe and armed and armed['stage']=='between' and armed['second'] in sql:
   events.append({'event':'fault-before-second-write','statement':sql,'connection':id(self.c),'in_transaction':self.c.in_transaction});armed=None;raise sqlite3.OperationalError('synthetic pre-second-write fault')
  result=self.c.execute(sql,*args)
  if probe:
   event={'event':'execute-returned','statement':sql,'connection':id(self.c),'in_transaction':self.c.in_transaction,'rowcount':result.rowcount}
   if 'INSERT INTO bookings' in sql or 'UPDATE bookings' in sql:
    event['same_connection_readback']=[list(r) for r in self.c.execute('SELECT id,status,cancelled_at FROM bookings ORDER BY id')]
   elif 'INSERT INTO notifications' in sql:event['same_connection_readback']=[list(r) for r in self.c.execute('SELECT id,user_id,booking_id,read FROM notifications ORDER BY id')]
   elif 'DELETE FROM sessions WHERE token_hash' in sql:event['same_connection_readback']={'session_count':self.c.execute('SELECT count(*) FROM sessions').fetchone()[0]}
   events.append(event)
  return result
 def executemany(self,sql,rows):return self.c.executemany(sql,rows)
 def commit(self):
  global armed
  if probe and armed and armed['stage']=='commit':events.append({'event':'fault-before-final-commit','connection':id(self.c),'in_transaction':self.c.in_transaction});armed=None;raise sqlite3.OperationalError('synthetic final commit fault')
  result=self.c.commit()
  if probe:events.append({'event':'real-commit-returned','connection':id(self.c)})
  return result
 def rollback(self):
  result=self.c.rollback()
  if probe:events.append({'event':'application-rollback-returned','connection':id(self.c)})
  return result
 def close(self):return self.c.close()
 def __enter__(self):return self
 def __exit__(self,*args):return self.c.__exit__(*args)
h.Conn=GapConnection
def business(snapshot):return {k:v for k,v in snapshot.items() if k!='sessions'}
def case(kind,stage):
 global armed,probe,events
 h.fresh();a=h.login();u=h.login('alice'); token=a if kind=='admin-cancel' else u
 if kind=='create':path,method,data='/api/bookings','POST',h.booking
 elif kind in ['cancel','admin-cancel']:path,method,data='/api/bookings/1/cancel','POST',{}
 else:path,method,data='/api/login','POST',{'email':'bob@meetspace.test','password':h.PW}
 before=h.snap();events=[];probe=True;armed={'stage':stage,'second':'INSERT INTO sessions' if kind=='switch' else 'INSERT INTO notifications'}
 s,b,rh=h.request(path,method,data,token);probe=False;after=h.snap();trace=list(events)
 h.mark(kind+'-'+stage+'-actual-failure',s==503 and b.get('code')=='storage_unavailable',{'response':b,'status':s,'events':trace})
 first='DELETE FROM sessions WHERE token_hash' if kind=='switch' else ('INSERT INTO bookings' if kind=='create' else 'UPDATE bookings')
 first_events=[e for e in trace if e['event']=='execute-returned' and first in e.get('statement','')]
 h.mark('first-target-DML-returned-with-same-connection-readback',bool(first_events) and all('same_connection_readback' in e for e in first_events),first_events)
 h.mark('correct-fault-position',any(e['event']==('fault-before-second-write' if stage=='between' else 'fault-before-final-commit') for e in trace),trace)
 h.mark('new-independent-connection-no-partial-state',before==after,{'before':before,'after':after})
 for endpoint in ['/api/rooms?date=2030-04-11','/api/bookings?scope=mine','/api/notifications']:h.request(endpoint,cookie=u)
 if kind=='switch':h.mark('old-session-still-valid',h.request('/api/session',cookie=u)[0]==200)
 # Stop application, start unchanged source in a separate process on same DB.
 h.server.shutdown();h.server.server_close();h.thread.join();childlog=(h.OUT/(kind+'-'+stage+'-restart.log')).open('w')
 proc=subprocess.Popen([h.sys.executable,str(Path(__file__).with_name('runtime_child.py')),str(h.db),str(h.T)],stdout=subprocess.PIPE,stderr=childlog,text=True)
 try:
  port=json.loads(proc.stdout.readline())['port'];h.server=types.SimpleNamespace(server_port=port);h.base='http://127.0.0.1:'+str(port)
  h.mark('real-process-restart-unchanged-before-login',before==h.snap())
  h.server.login_attempts={} # local handle only; application process remains untouched
  renewed=h.login('admin' if kind=='admin-cancel' else 'alice');h.mark('restart-login-and-business-readable',bool(renewed) and h.request('/api/bookings',cookie=renewed)[0]==200)
  clean=business(h.snap());h.mark('restart-relogin-business-unchanged',clean==business(before))
  first_s,first_b,first_h=h.request(path,method,data,renewed);h.mark('same-payload-successful-retry',first_s in [200,201],first_b)
  once=business(h.snap())
  if kind!='switch':
   again_s,again_b,_=h.request(path,method,data,renewed);h.mark('successful-retry-no-duplicate-business-effect',again_s in [200,201] and once==business(h.snap()),again_b)
   h.mark('one-correct-recipient-notification',len(once['notifications'])==len(before['notifications'])+1 and once['notifications'][-1][1]==2,once['notifications'])
  h.request('/api/notifications',cookie=renewed);h.request('/api/rooms?date=2030-04-11',cookie=renewed)
 finally:
  proc.terminate();proc.wait(timeout=10);childlog.close();del h.server;del h.thread
for kind in ['create','cancel','admin-cancel','switch']:
 for stage in ['between','commit']:h.save(kind+'-'+stage,lambda k=kind,s=stage:case(k,s))
(h.OUT/'trace.json').write_text(json.dumps({'revision':'708c9c057b5c9014f4ff975fdc5774093a687abe','source_lines':sorted(h.trace),'policy':'Only SQLite dependency connection wrapper; business functions unchanged; every commit outside armed final-commit failure delegates real commit unchanged; no compensating cleanup.','environment':{'python':h.sys.version,'server_clock':'2030-04-10T09:00:00+08:00','database':'isolated synthetic SQLite','mode':'real HTTP + dependency fault before second write / final commit'}},indent=2)+'\n')
