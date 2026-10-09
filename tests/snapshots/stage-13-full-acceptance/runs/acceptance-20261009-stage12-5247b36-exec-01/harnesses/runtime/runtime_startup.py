import os,sys,json,subprocess,shutil,time,re,http.client
from pathlib import Path
ROOT=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking');OUT=ROOT/'tests/delivery-acceptance/runs/acceptance-20261009-stage12-5247b36-exec-01/evidence/runtime';copy=OUT/'startup-copy';copy.mkdir(exist_ok=True)
for d in ['app','web']:shutil.copytree(ROOT/d,copy/d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
rows=[]
for name,args,host,port in [('default',[],'127.0.0.1',8766),('host',['--host','127.0.0.2'],'127.0.0.2',8766),('port',['--port','18766'],'127.0.0.1',18766),('db',['--db',str(copy/'custom.sqlite')],'127.0.0.1',8766),('all',['--host','127.0.0.2','--port','18766','--db',str(copy/'all.sqlite')],'127.0.0.2',18766)]:
 log=open(OUT/('startup-'+name+'.log'),'w');p=subprocess.Popen([sys.executable,'-S','-m','app.server',*args],cwd=copy,stdout=log,stderr=log,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 try:
  response=None
  for _ in range(50):
   try:c=http.client.HTTPConnection(host,port,timeout=1);c.request('GET','/api/health');r=c.getresponse();response={'status':r.status,'body':json.loads(r.read())};c.close();break
   except Exception:time.sleep(.1)
  sockets=subprocess.run(['lsof','-nP','-a','-p',str(p.pid),'-iTCP','-sTCP:LISTEN'],capture_output=True,text=True)
  rows.append({'branch':name,'command':[sys.executable,'-S','-m','app.server',*args],'response':response,'listeners':sockets.stdout,'default_db_exists':(copy/'data/meetspace.sqlite').exists(),'custom_db_exists':(copy/'custom.sqlite').exists(),'all_db_exists':(copy/'all.sqlite').exists()})
 finally:p.terminate();p.wait();log.close()
for command in [['/usr/bin/dtruss','/usr/bin/true'],['/usr/bin/fs_usage','-w','-f','filesys','-t','1']]:
 r=subprocess.run(command,capture_output=True,text=True,timeout=10);rows.append({'instrumentation_preflight':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
(OUT/'startup-and-instrumentation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
