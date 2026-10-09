"""测试专用 Linux 网络隔离 CLI 矩阵；仅 --execute 启动产品，不能自行批准验收。"""
import argparse, hashlib, http.client, json, os, pathlib, shutil, signal, socket, subprocess, sys, time
from zoneinfo import ZoneInfo
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--execute',action='store_true');p.add_argument('--revision');p.add_argument('--freeze-clock',action='store_true');a=p.parse_args()
source=pathlib.Path(a.source);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
resource={'python':sys.version,'python_executable':sys.executable,'stdlib_zone':str(ZoneInfo('Asia/Shanghai')),'network_namespace':os.readlink('/proc/self/ns/net') if pathlib.Path('/proc/self/ns/net').exists() else None,'platform':sys.platform,'source_sha256':{str(x.relative_to(source)):hashlib.sha256(x.read_bytes()).hexdigest() for d in ['app','web'] for x in (source/d).rglob('*') if x.is_file() and '__pycache__' not in str(x)},'revision':a.revision,'clock_control':{'wall':'2030-04-10T01:00:00Z','monotonic':'fixed'} if a.freeze_clock else None,'formal_verdict':None}
for host in ['127.0.0.1','127.0.0.2']:
 with socket.socket() as s:s.bind((host,8766));resource.setdefault('bindable_addresses',[]).append(host)
(out/'runtime-resources.json').write_text(json.dumps(resource,ensure_ascii=False,indent=2))
if not a.execute: print(json.dumps(resource,ensure_ascii=False));sys.exit(0)
if sys.platform!='linux' or not resource['network_namespace']:raise SystemExit('本harness只执行Linux隔离网络；禁止占用Mac用户demo8766')
project=out/'private-cli-copy';project.mkdir(exist_ok=True)
for d in ['app','web']:shutil.copytree(source/d,project/d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))

def req(host,port,method,path,data=None,cookie=None):
 c=http.client.HTTPConnection(host,port,timeout=3)
 headers={'Content-Type':'application/json','X-Meeting-App':'1','Origin':f'http://{host}:{port}'}
 if cookie:headers['Cookie']=cookie
 c.request(method,path,json.dumps(data) if data is not None else None,headers);r=c.getresponse();body=r.read();h=r.getheader('Set-Cookie');status=r.status;c.close();return status,json.loads(body),h.split(';',1)[0] if h else None

def listeners(pid,host,port):
 inodes=set()
 for f in pathlib.Path(f'/proc/{pid}/fd').iterdir():
  try:
   x=os.readlink(f)
   if x.startswith('socket:['):inodes.add(x[8:-1])
  except FileNotFoundError:pass
 rows=[]
 for line in pathlib.Path('/proc/net/tcp').read_text().splitlines()[1:]:
  parts=line.split(); addr,hexport=parts[1].split(':')
  if parts[3]=='0A' and int(hexport,16)==port and parts[9] in inodes:
   rows.append({'pid':pid,'address':socket.inet_ntoa(bytes.fromhex(addr)[::-1]),'port':port,'inode':parts[9]})
 return rows

def run(name,args,host,port,expected_db,write=False):
 log=(out/f'{name}.log').open('w');cmd=[sys.executable,'-S','-m','app.server',*args]
 server_env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 if a.freeze_clock:server_env.update(LD_PRELOAD=str(pathlib.Path(__file__).resolve().parent/'libfaketime.so.1'),FAKETIME='2030-04-10 01:00:00',FAKETIME_DONT_FAKE_MONOTONIC='0',TZ='UTC')
 proc=subprocess.Popen(cmd,cwd=project,stdout=log,stderr=log,env=server_env)
 result={'name':name,'command':cmd,'pid':proc.pid,'host':host,'port':port,'db':str(expected_db),'observations':[],'assertions':{}}
 try:
  for _ in range(100):
   if proc.poll() is not None:raise RuntimeError('目标进程提前退出')
   own=listeners(proc.pid,host,port)
   if own:
    status,health,_=req(host,port,'GET','/api/health');break
   time.sleep(.05)
  else:raise RuntimeError('未获得目标PID监听')
  result.update(listeners=own,health={'status':status,'body':health})
  result['assertions']['target_owns_expected_listener']=any(x['address']==host and x['port']==port for x in own)
  status,body,cookie=req(host,port,'POST','/api/login',{'email':'admin@meetspace.test','password':'MeetSpace!2026'})
  result['assertions']['real_login']=status==200
  if status!=200:raise RuntimeError(f'实际登录拒绝:{status}, {body}')
  if write:
   status,body,_=req(host,port,'POST','/api/rooms',{'name':f'CLI-{name}','capacity':8,'location':'隔离参数矩阵','equipment':[]},cookie)
   result['observations'].append({'operation':'create_room','status':status,'body':body})
   result['assertions']['real_write']=status in (200,201)
  status,body,_=req(host,port,'GET','/api/rooms',cookie=cookie)
  result['observations'].append({'operation':'read_rooms','status':status,'body':body})
  result['assertions']['db_created']=expected_db.is_file()
  rooms=body.get('rooms',[]) if isinstance(body,dict) else body
  result['assertions']['expected_room_present']=any(x.get('name')==f'CLI-{name.removesuffix("-restart")}' for x in rooms)
 except Exception as e:result['error']=str(e)
 finally:
  if proc.poll() is None:proc.send_signal(signal.SIGINT)
  try:result['exit_code']=proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill();result['exit_code']=proc.wait();result['cleanup_forced']=True
  log.close();result['assertions']['listener_released']=not listeners(proc.pid,host,port) if pathlib.Path(f'/proc/{proc.pid}/fd').exists() else True
 return result
rows=[]
for name,args,host,port,db in [('default',[],'127.0.0.1',8766,project/'data/meetspace.sqlite'),('host',['--host','127.0.0.2'],'127.0.0.2',8766,project/'data/meetspace.sqlite'),('port',['--port','18766'],'127.0.0.1',18766,project/'data/meetspace.sqlite'),('db',['--db',str(project/'custom.sqlite')],'127.0.0.1',8766,project/'custom.sqlite'),('all',['--host','127.0.0.2','--port','18766','--db',str(project/'all.sqlite')],'127.0.0.2',18766,project/'all.sqlite')]:
 rows.append(run(name,args,host,port,db,True));rows.append(run(name+'-restart',args,host,port,db))
rows.append(run('default-revisit',[],'127.0.0.1',8766,project/'data/meetspace.sqlite'))
# 最后一项查看的是既存默认库；默认最初创建名由前面的default/restart证据判断。
rows[-1]['assertions'].pop('expected_room_present',None)
(out/'cli-matrix-results.json').write_text(json.dumps({'resource':resource,'rows':rows,'formal_verdict':None,'limitation':'结果仅为实际观测，正式判定需Skill独立审阅；本文件不提交认证通过。'},ensure_ascii=False,indent=2))
print(json.dumps({'rows':len(rows),'errors':[r['name'] for r in rows if r.get('error')],'formal_verdict':None}))
