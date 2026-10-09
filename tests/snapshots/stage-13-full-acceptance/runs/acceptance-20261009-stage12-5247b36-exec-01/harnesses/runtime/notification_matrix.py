import os,sys,json,locale,time,datetime as dt,sqlite3,threading,http.client,importlib.util,pathlib,hashlib
source=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
s=importlib.util.spec_from_file_location('target',source/'app/server.py');app=importlib.util.module_from_spec(s);s.loader.exec_module(app)
T=dt.datetime(2030,4,8,1,tzinfo=dt.timezone.utc).timestamp()
class Date(dt.datetime):
 @classmethod
 def now(cls,tz=None):return cls.fromtimestamp(T,tz)
class Time:
 @staticmethod
 def time():return T
app.datetime=Date;app.time=Time
rows=[];locales=[]
for l in ['C','C.UTF-8','en_US.UTF-8','zh_CN.UTF-8']:
 try:locale.setlocale(locale.LC_TIME,l);locales.append(l)
 except locale.Error:pass
for zone in ['UTC','Asia/Shanghai']:
 os.environ['TZ']=zone;time.tzset()
 for loc in locales:
  locale.setlocale(locale.LC_TIME,loc)
  for start,end in [('08:00','08:15'),('09:00','09:15'),('19:45','20:00')]:
   db=out/f'db-{len(rows)}.sqlite';server=app.ApplicationServer(('127.0.0.1',0),app.Store(db));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
   def req(path,data=None,cookie=None):
    c=http.client.HTTPConnection('127.0.0.1',server.server_port);h={'Content-Type':'application/json','X-Meeting-App':'1','Origin':base}
    if cookie:h['Cookie']=cookie
    c.request('POST' if data else 'GET',path,json.dumps(data).encode() if data else None,h);r=c.getresponse();body=json.loads(r.read());heads=dict(r.getheaders());c.close();return r.status,body,heads
   try:
    _,_,h=req('/api/login',{'email':'alice@meetspace.test','password':'MeetSpace!2026'});cookie=h['Set-Cookie'].split(';')[0]
    body={'room_id':4,'title':'UTF8通知端点','start':'2030-04-09T'+start+':00+08:00','end':'2030-04-09T'+end+':00+08:00','attendees':2,'idempotency_key':'synthetic-notify-'+str(len(rows))};status,b,_=req('/api/bookings',body,cookie)
    with sqlite3.connect(db) as c:
     c.row_factory=sqlite3.Row;book=[dict(x) for x in c.execute('SELECT * FROM bookings WHERE idempotency_key=?',(body['idempotency_key'],))];notices=[dict(x) for x in c.execute('SELECT * FROM notifications WHERE booking_id=?',(book[0]['id'],))] if book else [];room=c.execute('SELECT name FROM rooms WHERE id=4').fetchone()[0]
    expected='04月09日 '+start+'–'+end;checks={'created':status==201,'single_booking':len(book)==1,'single_notice':len(notices)==1,'recipient_and_booking':bool(notices) and notices[0]['user_id']==2 and notices[0]['booking_id']==book[0]['id'],'unread':bool(notices) and notices[0]['read']==0,'message_complete':bool(notices) and all(x in notices[0]['message'] for x in [expected,room,body['title']])};rows.append({'timezone':zone,'locale':loc,'input':body,'status':status,'expected_beijing':expected,'bookings':book,'notifications':notices,'assertions':checks})
   finally:server.shutdown();server.server_close();thread.join()
(out/'results.json').write_text(json.dumps({'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','python':sys.version,'platform':sys.platform,'source_sha256':hashlib.sha256((source/'app/server.py').read_bytes()).hexdigest(),'available_locales':locales,'fixed_clock':T,'rows':rows},ensure_ascii=False,indent=2));print(len(rows),sum(not all(x['assertions'].values()) for x in rows))
