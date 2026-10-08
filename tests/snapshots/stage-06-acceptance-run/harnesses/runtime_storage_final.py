import runtime_execute as h
import json,sqlite3
h.OUT=h.OUT/'storage-final';h.OUT.mkdir(exist_ok=True)
def locks():
 for kind in ['create','cancel','edit','role']:
  path,method,data,token=h.setup_route(kind);before=h.snap();c=sqlite3.connect(h.db,isolation_level=None);c.execute('BEGIN IMMEDIATE');s,b,rh=h.request(path,method,data,token);h.mark('external-lock-'+kind,s==503 and b.get('code')=='storage_unavailable');c.rollback();c.close();h.mark('lock-no-change-'+kind,before==h.snap());h.mark('lock-recovery-'+kind,h.request(path,method,data,token)[0] in [200,201])
def real_integrity():
 path,method,data,token=h.setup_route('add');h.request(path,method,data,token);before=h.snap();s,b,rh=h.request(path,method,data,token);h.mark('real-unique-integrity',s==409 and b.get('code')=='data_conflict' and before==h.snap());h.mark('ordinary-no-cookie','Set-Cookie' not in rh);h.mark('recovered-unique',h.request(path,method,{**data,'name':'distinct-recovery'},token)[0]==201)
def wrong_methods():
 h.fresh();a=h.login();before=h.snap()
 for path,allowed in [('/api/rooms',{'GET','POST'}),('/api/rooms/1',{'PATCH'}),('/api/members',{'GET'}),('/api/members/3',{'PATCH'}),('/api/bookings',{'GET','POST'}),('/api/bookings/1/cancel',{'POST'}),('/api/logout',{'POST'}),('/api/notifications/read',{'POST'})]:
  for method in set(['GET','POST','PATCH','HEAD'])-allowed:
   s,b,rh=h.request(path,method,{} if method in ['POST','PATCH'] else None,a);h.mark('method-dispatch-'+method+path,s==404 and before==h.snap())
def read105():
 h.fresh();a=h.login();u=h.login('alice')
 with sqlite3.connect(h.db) as c:
  c.executemany('INSERT INTO notifications(user_id,booking_id,message,created_at,read) VALUES(2,1,?,?,0)',[(str(i),h.app.now_iso()) for i in range(105)]);c.execute("INSERT INTO notifications(user_id,booking_id,message,created_at,read) VALUES(3,2,'other',?,0)",(h.app.now_iso(),))
 before=h.snap();h.request('/api/notifications/read','POST',{},u);after=h.snap();own=[x for x in after['notifications'] if x[1]==2];peer=[x for x in after['notifications'] if x[1]==3];h.mark('all105-including-oldest-five',len(own)==105 and all(x[-1]==1 for x in own));h.mark('other-user-unread-unchanged',peer==[x for x in before['notifications'] if x[1]==3],peer)
for name,fn in [('required-external-locks',locks),('real-integrity',real_integrity),('wrong-route-methods',wrong_methods),('all105-success-peer-isolation',read105)]:h.save(name,fn)
h.server.shutdown();h.server.server_close();(h.OUT/'trace.json').write_text(json.dumps({'lines':sorted(h.trace),'sql_operations':h.sql_events},indent=2))
