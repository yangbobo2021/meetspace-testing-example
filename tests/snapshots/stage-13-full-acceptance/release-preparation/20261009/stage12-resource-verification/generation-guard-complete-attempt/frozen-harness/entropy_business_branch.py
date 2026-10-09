"""容器内单个真实产品矩阵分支。
stdout只供外层--log-driver=none宿主控制器内存比较，含私有材料，禁止作为证据落盘或直接显示。
"""
import argparse,hashlib,http.client,json,os,pathlib,shutil,signal,sqlite3,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--prefix',choices=['seed','first','repeat','after-three','self-switch','cross-switch'],required=True);p.add_argument('--tape');p.add_argument('--baseline-db');p.add_argument('--save-baseline',action='store_true');p.add_argument('--revision',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
if not a.execute:raise SystemExit('需 --execute 且已明确修复后revision；本脚本不能认证通过')
base=pathlib.Path(__file__).resolve().parent;source=pathlib.Path(a.source);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);project=pathlib.Path('/tmp/meetspace-entropy-project');project.mkdir()
for d in ['app','web']:shutil.copytree(source/d,project/d,ignore=shutil.ignore_patterns('__pycache__'))
(project/'data').mkdir();db=project/'data/meetspace.sqlite'
if a.baseline_db:shutil.copyfile(a.baseline_db,db)
clock=pathlib.Path('/tmp/meetspace-controlled-clock')
def setclock(value):
 next_clock=clock.with_suffix('.next');next_clock.write_text(value);os.replace(next_clock,clock)
setclock('2030-04-10 01:00:00')
cmd=[sys.executable,'-S',str(base/'ptrace_os_adapter.py'),'--output',str(out/'os-trace')]+(['--tape',a.tape] if a.tape else [])+['--','/usr/bin/setarch','aarch64','-R','/usr/bin/env','PYTHONHASHSEED=0','PYTHONDONTWRITEBYTECODE=1','LD_PRELOAD=/usr/lib/aarch64-linux-gnu/faketime/libfaketime.so.1','FAKETIME_TIMESTAMP_FILE='+str(clock),'FAKETIME_NO_CACHE=1','FAKETIME_DONT_FAKE_MONOTONIC=0','TZ=UTC',sys.executable,'-S','-m','app.server']
target_handle='other' if a.prefix=='seed' else ('second' if a.prefix=='after-three' else 'target')
log=(out/'server.log').open('w');proc=subprocess.Popen(cmd,cwd=project,stdout=log,stderr=log);ops=[];cookies={};raw=[];target=None;report={'prefix':a.prefix,'revision':a.revision,'source_sha256':{str(x.relative_to(source)):hashlib.sha256(x.read_bytes()).hexdigest() for d in ['app','web'] for x in (source/d).rglob('*') if x.is_file() and '__pycache__' not in str(x)},'harness_sha256':{name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ['entropy_business_branch.py','ptrace_os_adapter.py']},'assertions':{},'formal_verdict':None}

def call(method,path,data=None,handle=None):
 c=http.client.HTTPConnection('127.0.0.1',8766,timeout=5);headers={'Content-Type':'application/json','Origin':'http://127.0.0.1:8766','X-Meeting-App':'1'}
 if handle in cookies:headers['Cookie']=cookies[handle]
 c.request(method,path,json.dumps(data) if data is not None else None,headers);r=c.getresponse();status=r.status;body=r.read();h=r.getheader('Set-Cookie');c.close()
 obj=json.loads(body);ops.append({'operation':method+' '+path,'handle':handle,'status':status,'response_contains_public_password':b'MeetSpace!2026' in body})
 if h:
  value=h.split(';',1)[0];cookies[handle]=value
  if value.startswith('meetspace_session=') and value.split('=',1)[1]:raw.append(value.split('=',1)[1])
 return status,obj

def login(email,handle):
 status,obj=call('POST','/api/login',{'email':email+'@meetspace.test','password':'MeetSpace!2026'},handle)
 if status!=200:raise RuntimeError(f'login {email} status={status}')
 status,obj=call('GET','/api/session',handle=handle);identity=obj.get('user',{});report['assertions'].setdefault('all_real_identities',[]).append(status==200 and identity.get('email')==email+'@meetspace.test')
 token=cookies[handle].split('=',1)[1];con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);snapshot=sqlite3.connect(':memory:');con.backup(snapshot);con.close();row=snapshot.execute('select user_id,expires from sessions where token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone();snapshot.close();report['assertions'].setdefault('all_login_digest_identity_expiry',[]).append(row is not None and row[0]==identity.get('id') and row[1]==1902042000.0)
 status,rooms=call('GET','/api/rooms',handle=handle);report['assertions'].setdefault('all_login_protected_business',[]).append(status==200)
 return token
try:
 startup_deadline=time.monotonic()+120
 while time.monotonic()<startup_deadline:
  if proc.poll() is not None:raise RuntimeError('traced process exited before listener')
  try:
   s,b=call('GET','/api/health')
   if s==200:break
  except (OSError,ValueError,http.client.HTTPException):time.sleep(.05)
 else:raise RuntimeError('owned child startup timeout')
 pid=json.loads((out/'os-trace/child-pid.json').read_text())['pid'];report['app_pid']=pid
 own=[]
 for f in pathlib.Path(f'/proc/{pid}/fd').iterdir():
  try:
   if os.readlink(f).startswith('socket:['):own.append(os.readlink(f)[8:-1])
  except OSError:pass
 report['assertions']['listener_owned_by_child']=any(x.split()[3]=='0A' and x.split()[1]=='0100007F:223E' and x.split()[9] in own for x in pathlib.Path('/proc/net/tcp').read_text().splitlines()[1:])
 if a.save_baseline:
  con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);snapshot=sqlite3.connect(str(out/'private-baseline.sqlite'));con.backup(snapshot);report['assertions']['baseline_before_any_login_sessions_zero']=snapshot.execute('select count(*) from sessions').fetchone()[0]==0;snapshot.close();con.close()
 if a.prefix=='seed':
  for email in ['admin','alice','bob','other']:target=login(email,email)
  s,b=call('POST','/api/login',{'email':'alice@meetspace.test','password':'wrong'},'wrong');report['assertions']['wrong_password_rejected']=s>=400
 elif a.prefix=='first':target=login('alice','target')
 elif a.prefix=='repeat':login('alice','old');target=login('alice','target');s,b=call('GET','/api/session',handle='old');report['assertions']['other_browser_still_valid']=s==200
 elif a.prefix=='after-three':
  for h in ['old','second','third']:login('alice',h)
  call('POST','/api/logout',{},'second');target=login('alice','second');s,b=call('GET','/api/session',handle='old');report['assertions']['independent_browser_valid']=s==200
 elif a.prefix in ['self-switch','cross-switch']:
  before,after=('admin','alice') if a.prefix=='self-switch' else ('alice','other');login(before,'old');login(before,'target');old=cookies['target'];target=login(after,'target');cookies['obsolete']=old;s,b=call('GET','/api/session',handle='obsolete');report['assertions']['old_current_session_rejected']=s==401;s,b=call('GET','/api/session',handle='old');report['assertions']['independent_browser_valid']=s==200
 s,b=call('GET','/api/rooms',handle=target_handle);report['assertions']['target_protected_business_access']=s==200
 # 请求结束后SQLite backup获得一致快照，检查源码约定格式只在内存。
 con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);snap=sqlite3.connect(':memory:');con.backup(snap);con.close();salt_by_email={};matches=[]
 for email,stored in snap.execute('select email,password_hash from users'):
  salt,digest=stored.split(':');salt_by_email[email]=salt;derived=hashlib.scrypt(b'MeetSpace!2026',salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();wrong=hashlib.scrypt(b'wrong',salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex();matches.append(derived==digest and wrong!=digest)
 report['assertions']['independent_scrypt_all_accounts']=all(matches);report['assertions']['different_account_salts']=len(set(salt_by_email.values()))==4
 fields=[r[1] for r in snap.execute('pragma table_info(sessions)')];report['session_field_names']=fields;report['database_objects']=[{'type':r[0],'name':r[1]} for r in snap.execute('select type,name from sqlite_schema')]
 report['assertions']['session_only_digest_user_expiry_fields']=set(fields)=={'token_hash','user_id','expires'}
 report['assertions']['every_actual_token_has_matching_digest']=all(snap.execute('select count(*) from sessions where token_hash=?',(hashlib.sha256(v.encode()).hexdigest(),)).fetchone()[0]==1 for v in raw if v==target)
 report['assertions']['responses_without_password']=not any(o['response_contains_public_password'] for o in ops)
 report['database_field_inventory']={name:[{'name':r[1],'type':r[2],'primary_key':bool(r[5])} for r in snap.execute('pragma table_info("'+name+'")')] for name, in snap.execute("select name from sqlite_schema where type='table'")}
 report['assertions']['no_unknown_blob_fields']=not any(f['type'].upper()=='BLOB' for fields in report['database_field_inventory'].values() for f in fields)
 if target:
  expiry=snap.execute('select expires from sessions where token_hash=?',(hashlib.sha256(target.encode()).hexdigest(),)).fetchone()[0];report['assertions']['exact_eight_hour_expiry']=expiry==1902042000.0
 snap.close();report['operations']=ops
  # 真实退出与精确到期，涵盖持久化删除入口；时钟文件仅是测试依赖状态。
 login('alice','retire');status,obj=call('POST','/api/logout',{},'retire');status_after,obj=call('GET','/api/session',handle='retire');report['assertions']['real_logout_revokes_session']=status==200 and status_after==401
 setclock('2030-04-10 09:00:00');status,obj=call('GET','/api/session',handle=target_handle);report['assertions']['exact_eight_hour_boundary_rejects']=status==401
 # 关闭后同库重启，独立检查初始化凭据没有重写并重新实际认证。
 proc.send_signal(signal.SIGINT);report['first_tracer_exit_code']=proc.wait(timeout=60);log.close();report['os_trace_initial']=json.loads((out/'os-trace/os-events.json').read_text())
 setclock('2030-04-10 01:00:00');cmd2=[str(out/'os-trace-restart') if x==str(out/'os-trace') else x for x in cmd]
 if '--tape' in cmd2:
  position=cmd2.index('--tape');del cmd2[position:position+2]
 report['restart_entropy_source']='real_os';report['comparison_scope']='initial_target_before_real_os_restart'
 log=(out/'server-restart.log').open('w');proc=subprocess.Popen(cmd2,cwd=project,stdout=log,stderr=log)
 startup_deadline=time.monotonic()+120
 while time.monotonic()<startup_deadline:
  if proc.poll() is not None:raise RuntimeError('restart traced child exited')
  try:
   status,obj=call('GET','/api/health')
   if status==200:break
  except (OSError,ValueError,http.client.HTTPException):time.sleep(.05)
 else:raise RuntimeError('restart listener unavailable')
 login('alice','restarted');report['assertions']['restart_real_authentication']=True
 con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True);after_salts={email:stored.split(':')[0] for email,stored in con.execute('select email,password_hash from users')};con.close();report['assertions']['restart_saved_salts_unchanged']=after_salts==salt_by_email
finally:
 if proc.poll() is None:proc.send_signal(signal.SIGINT)
 try:report['tracer_exit_code']=proc.wait(timeout=60)
 except subprocess.TimeoutExpired:proc.kill();proc.wait();report['cleanup_forced']=True
 log.close()
 report['os_trace']=json.loads((out/'os-trace/os-events.json').read_text()) if (out/'os-trace/os-events.json').exists() else {'uncovered':['tracer_report_missing']}
 if (out/'os-trace-restart/os-events.json').exists():report['os_trace_restart']=json.loads((out/'os-trace-restart/os-events.json').read_text())
 (out/'business-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'private_salts':salt_by_email,'private_target_token':target,'report':report},ensure_ascii=False))
