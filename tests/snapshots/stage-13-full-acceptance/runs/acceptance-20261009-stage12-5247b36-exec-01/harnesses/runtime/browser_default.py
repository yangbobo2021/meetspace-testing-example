import subprocess,threading,json,base64,time,shutil
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking');RUN=ROOT/'tests/delivery-acceptance/runs/acceptance-20261009-stage12-5247b36-exec-01';OUT=RUN/'evidence/cli-browser';OUT.mkdir(exist_ok=True)
for name in ['app','web']:shutil.copytree(ROOT/name,OUT/name,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
name='acceptance-stage12-exec01-default-browser'; rows=[]
relay="import sys,json,base64,http.client;x=json.load(sys.stdin);c=http.client.HTTPConnection('127.0.0.1',8766);c.request(x['method'],x['path'],base64.b64decode(x['body']),x['headers']);r=c.getresponse();print(json.dumps({'status':r.status,'headers':r.getheaders(),'body':base64.b64encode(r.read()).decode()}))"
class H(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):self.proxy()
 def do_POST(self):self.proxy()
 def proxy(self):
  b=self.rfile.read(int(self.headers.get('Content-Length',0))); x={'method':self.command,'path':self.path,'body':base64.b64encode(b).decode(),'headers':dict(self.headers)}
  p=subprocess.run(['docker','exec','-i',name,'python','-S','-c',relay],input=json.dumps(x),text=True,capture_output=True)
  if p.returncode:self.send_error(502);return
  x=json.loads(p.stdout);self.send_response(x['status'])
  for k,v in x['headers']:
   if k.lower() not in ['server','date','connection']:self.send_header(k,v)
  self.end_headers();self.wfile.write(base64.b64decode(x['body']));rows.append({'method':self.command,'path':self.path,'status':x['status']})
cmd=['docker','run','--rm','--name',name,'--network','none','--read-only','--cap-drop','ALL','--tmpfs','/tmp','--mount',f'type=bind,source={OUT},target=/work','--workdir','/work','--env','PYTHONDONTWRITEBYTECODE=1','--entrypoint','python','sha256:8129910271f9764b5c05038d351ad7b9f9d94b85351355b69c5526eadd111775','-S','-m','app.server']
log=(OUT/'server.log').open('w');proc=subprocess.Popen(cmd,stdout=log,stderr=log)
s=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=s.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{s.server_port}'
try:
 for _ in range(100):
  p=subprocess.run(['docker','exec',name,'python','-S','-c',"import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8766/api/health').status)"],capture_output=True,text=True)
  if p.returncode==0:break
  time.sleep(.1)
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True);page=b.new_page();page.goto(url);page.locator('#login-form').wait_for();page.locator('[data-account=admin]').click();page.locator('#login-form button[type=submit]').click();page.locator('[data-logout]').first.wait_for();health=page.evaluate("fetch('/api/health').then(r=>r.json())");assert health=={'status':'ok','version':'1.0.0-rc.1','timezone':'Asia/Shanghai'};page.screenshot(path=str(OUT/'default-browser.png'),full_page=True);assert (OUT/'data/meetspace.sqlite').exists();version=b.version;b.close()
 (OUT/'result.json').write_text(json.dumps({'status':'passed','revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','target_command':cmd,'browser_version':version,'browser_url':url,'proxy':'每请求docker exec传输到独立network none容器127.0.0.1:8766;不接触宿主8766','health':health,'requests':rows},ensure_ascii=False,indent=2))
finally:
 s.shutdown();s.server_close();subprocess.run(['docker','stop','-t','3',name],capture_output=True);proc.wait();log.close()
