import pathlib,os,hashlib,json,shutil,subprocess,time,signal,http.client,sys
source=pathlib.Path('/source');out=pathlib.Path('/output');project=pathlib.Path('/tmp/mapping-source');project.mkdir()
for d in ['app','web']:shutil.copytree(source/d,project/d)
clock=pathlib.Path('/tmp/mapping-clock')
def setclock(value):
 new=clock.with_suffix('.next');new.write_text(value);os.replace(new,clock)
setclock('2030-04-10 01:00:00');cookies={};ops=[]
def call(method,path,data=None,handle=None):
 c=http.client.HTTPConnection('127.0.0.1',8766,timeout=5);headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:8766','X-Meeting-App':'1'}
 if handle in cookies:headers['Cookie']=cookies[handle]
 c.request(method,path,json.dumps(data) if data is not None else None,headers);r=c.getresponse();b=r.read();cookie=r.getheader('Set-Cookie');status=r.status;c.close()
 if cookie:cookies[handle]=cookie.split(';',1)[0]
 ops.append({'method':method,'path':path,'status':status,'handle':handle});return status,json.loads(b)
def login(email,handle):
 if call('POST','/api/login',{'email':email+'@meetspace.test','password':'MeetSpace!2026'},handle)[0]!=200:raise RuntimeError('login failed')
 if call('GET','/api/session',handle=handle)[0]!=200 or call('GET','/api/rooms',handle=handle)[0]!=200:raise RuntimeError('protected failed')
rows=[]
for phase in ['initial','same-db-restart']:
 trace=out/(phase+'-mapping-metadata.log');log=(out/(phase+'-server.log')).open('w')
 cmd=['strace','-f','-ttt','-yy','-s','256','-e','trace=mmap,mremap,mprotect,munmap,clone,clone3,execve','-o',str(trace),'/usr/bin/setarch','aarch64','-R','/usr/bin/env','PYTHONHASHSEED=0','PYTHONDONTWRITEBYTECODE=1','LD_PRELOAD=/usr/lib/aarch64-linux-gnu/faketime/libfaketime.so.1','FAKETIME_TIMESTAMP_FILE='+str(clock),'FAKETIME_NO_CACHE=1','FAKETIME_DONT_FAKE_MONOTONIC=0','TZ=UTC',sys.executable,'-S','-m','app.server']
 proc=subprocess.Popen(cmd,cwd=project,stdout=log,stderr=log)
 try:
  deadline=time.monotonic()+120
  while time.monotonic()<deadline:
   try:
    if call('GET','/api/health')[0]==200:break
   except (OSError,ValueError,http.client.HTTPException):time.sleep(.05)
  else:raise RuntimeError('listener unavailable')
  if phase=='initial':
   for email in ['admin','alice','bob','other']:login(email,email)
   login('alice','retire');call('POST','/api/logout',{},'retire');call('GET','/api/session',handle='retire')
   setclock('2030-04-10 09:00:00');call('GET','/api/session',handle='other')
  else:login('alice','restarted')
 finally:
  children=pathlib.Path(f'/proc/{proc.pid}/task/{proc.pid}/children').read_text().split()
  if len(children)!=1:raise RuntimeError('owned traced child not unique')
  os.kill(int(children[0]),signal.SIGINT);code=proc.wait(timeout=60);log.close()
 rows.append({'phase':phase,'exit_code':code,'trace':trace.name});setclock('2030-04-10 01:00:00')
report={'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','source_sha256':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for d in ['app','web'] for p in (source/d).rglob('*') if p.is_file()},'rows':rows,'operations':ops,'formal_verdict':None,'scope':'independent current-source syscall mapping metadata only; no read/write or HTTP payload tracing; actual initialization, logins/protected/logout/exact expiry, same-db realOS restart'}
(out/'mapping-metadata-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'rows':rows,'formal_verdict':None}))
