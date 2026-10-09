"""只读socket元数据补充观察：不抓HTTP载荷、不生成正式验收passed。"""
import argparse,hashlib,http.client,json,os,pathlib,shutil,signal,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--revision',required=True);a=p.parse_args();source=pathlib.Path(a.source);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);project=pathlib.Path('/tmp/network-source');project.mkdir()
for d in ['app','web']:shutil.copytree(source/d,project/d,ignore=shutil.ignore_patterns('__pycache__'))
log=(out/'server.log').open('w');cmd=['strace','-f','-qq','-e','trace=socket,connect,bind,listen,accept,accept4,getsockname,getpeername,shutdown','-o',str(out/'network-metadata.log'),sys.executable,'-S','-m','app.server'];proc=subprocess.Popen(cmd,cwd=project,stdout=log,stderr=log,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
try:
 for _ in range(100):
  try:
   c=http.client.HTTPConnection('127.0.0.1',8766,timeout=1);c.request('GET','/api/health');r=c.getresponse();healthy=r.status==200;r.read();c.close()
   if healthy:break
  except OSError:time.sleep(.05)
 children=pathlib.Path(f'/proc/{proc.pid}/task/{proc.pid}/children').read_text().split()
 for child in children:os.kill(int(child),signal.SIGINT)
 proc.wait(timeout=20)
finally:
 if proc.poll() is None:proc.kill();proc.wait()
 log.close()
text=(out/'network-metadata.log').read_text();connects=[line for line in text.splitlines() if 'connect(' in line];report={'revision':a.revision,'source_sha256':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for d in ['app','web'] for p in (source/d).rglob('*') if p.is_file() and '__pycache__' not in str(p)},'actual_connect_metadata':connects,'all_connects_failed_nscd':bool(connects) and all('"/var/run/nscd/socket"' in line and 'ENOENT' in line for line in connects),'healthy':healthy,'exit_code':proc.returncode,'formal_verdict':None,'scope':'socket系统调用类型/地址/返回码；不记录Cookie或HTTP载荷；同固定源和标准库独立解释r4各生命周期2次失败connect。'}
(out/'network-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
