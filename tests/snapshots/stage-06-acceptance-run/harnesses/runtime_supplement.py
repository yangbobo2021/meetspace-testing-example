import runtime_execute as h
import json, sqlite3
from pathlib import Path
h.OUT=h.OUT/'supplement';h.OUT.mkdir(exist_ok=True)
def seeds():
 for hour in ['00:30:00','09:00:00']:
  for tz in ['UTC','Asia/Shanghai']:
   for empty in [False,True]:
    h.counter+=1;h.db=h.OUT/f'seed-{h.counter}.sqlite';h.os.environ['TZ']=tz;h.time.tzset();h.clock[0]=h.dt.datetime.fromisoformat('2030-04-10T'+hour+'+08:00').timestamp()
    if empty:sqlite3.connect(h.db).close()
    h.app.Store(h.db);s=h.snap();rows=s['bookings']; dates=[row[6][:10] for row in rows];h.mark('seed-date-'+hour+tz+str(empty),dates==['2030-04-11']*3,{'dates':dates,'teams':s['teams'],'users':s['users'],'rooms':s['rooms'],'bookings':rows})
def authorization():
 h.fresh();a=h.login();u=h.login('alice');v=h.login('bob');b=h.login('other');before=h.snap()
 routes=[('/api/rooms','POST',h.room),('/api/rooms/1','PATCH',h.room),('/api/members','GET',None),('/api/members/3','PATCH',{'role':'admin'}),('/api/bookings?scope=team','GET',None),('/api/bookings/2/cancel','POST',{})]
 for path,method,data in routes:
  s,r,rh=h.request(path,method,data,u);h.mark('member-forbidden-'+path,s==403 and before==h.snap())
 for path,method,data in routes+ [('/api/session','GET',None),('/api/rooms','GET',None),('/api/notifications','GET',None),('/api/logout','POST',{})]:
  for token in [None,'synthetic-invalid-token']:
   s,r,rh=h.request(path,method,data,token);h.mark('invalid-auth-'+path,s==401 and before==h.snap())
def switch():
 routes={'mine':('/api/bookings','GET',None),'notifications':('/api/notifications','GET',None),'rooms':('/api/rooms','GET',None),'members':('/api/members','GET',None),'team':('/api/bookings?scope=team','GET',None),'add':('/api/rooms','POST',h.room),'edit':('/api/rooms/1','PATCH',h.room),'role':('/api/members/3','PATCH',{'role':'admin'}),'cancel':('/api/bookings/2/cancel','POST',{})}
 for src,dst,keys in [('alice','bob',['mine','notifications']),('alice','other',['rooms','mine','notifications']),('other','alice',['rooms','mine','notifications']),('admin','alice',['members','team','add','edit','role','cancel']),('alice','admin',['members','team','add','edit','role','cancel'])]:
  for key in keys:
   h.fresh();old=h.login(src);other=h.login(src);new=h.login(dst,old);path,method,data=routes[key];before=h.snap();s,r,rh=h.request(path,method,data,new);expected=403 if src=='admin' else 201 if key=='add' else 200;h.mark('first-request-'+src+'-'+dst+'-'+key,s==expected,r)
   if expected==403:h.mark('switch-no-write',before==h.snap())
   h.mark('old-revoked',h.request('/api/session',cookie=old)[0]==401);h.mark('other-valid',h.request('/api/session',cookie=other)[0]==200)
for name,fn in [('seed-matrix',seeds),('authorizations',authorization),('first-request-switch',switch)]:h.save(name,fn)
h.server.shutdown();h.server.server_close()
