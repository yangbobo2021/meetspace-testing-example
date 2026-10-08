import runtime_execute as h
import json,socket,subprocess,re,types,http.client,sqlite3
from pathlib import Path
h.OUT=h.OUT/'edges';h.OUT.mkdir(exist_ok=True)
def ip_rate():
 h.fresh()
 for i in range(8):h.request('/api/login','POST',{'email':'none','password':'wrong'})
 probe=subprocess.run(['/sbin/ifconfig'],capture_output=True,text=True)
 ips=[x for x in re.findall(r'inet (\d+\.\d+\.\d+\.\d+)',probe.stdout) if x!='127.0.0.1']
 usable=False
 for ip in ips:
  try:
   c=http.client.HTTPConnection('127.0.0.1',h.server.server_port,timeout=5,source_address=(ip,0));body=json.dumps({'email':'admin@meetspace.test','password':h.PW});c.request('POST','/api/login',body,{'Content-Type':'application/json','X-Meeting-App':'1'});r=c.getresponse();b=json.loads(r.read());c.close();h.mark('independent-source-ip',r.status==200,{'source':'local-interface-'+str(ips.index(ip)),'status':r.status,'body':b});usable=True;break
  except OSError as e:h.current.append({'branch':'second-source','status':'blocked','actual':str(e)})
 if not usable:h.current.append({'branch':'second-source','status':'blocked','actual':'No bindable distinct local IPv4 source reached loopback target','candidate_count':len(ips),'ifconfig_exit':probe.returncode})
 h.mark('first-source-remains-limited',h.request('/api/login','POST',{'email':'none','password':'wrong'})[0]==429)
 h.server.login_attempts.clear();h.clock[0]=h.T
 for i in range(8):h.request('/api/login','POST',{'email':'none','password':'wrong'})
 h.clock[0]=h.T+59;h.mark('429-before-window',h.request('/api/login','POST',{'email':'none','password':'wrong'})[0]==429);h.clock[0]=h.T+60
 for i in range(8):h.mark('same-timestamp-all-expire-'+str(i),h.request('/api/login','POST',{'email':'none','password':'wrong'})[0]==401)

def missing_length():
 h.fresh();c=http.client.HTTPConnection('127.0.0.1',h.server.server_port);c.putrequest('POST','/api/login');c.putheader('Content-Type','application/json');c.putheader('X-Meeting-App','1');c.endheaders();r=c.getresponse();b=json.loads(r.read());h.mark('absent-content-length',r.status==400,b);c.close()

def future_process():
 h.server.shutdown();h.server.server_close();h.thread.join();h.db=h.OUT.parent/'completion/process-persist.sqlite';before=h.snap();log=open(h.OUT/'future-process.log','w');p=subprocess.Popen([h.sys.executable,str(Path(__file__).with_name('runtime_child.py')),str(h.db),str(h.T+172800)],stdout=subprocess.PIPE,stderr=log,text=True);port=json.loads(p.stdout.readline())['port'];h.server=types.SimpleNamespace(server_port=port);h.base='http://127.0.0.1:'+str(port)
 try:
  h.mark('two-days-restart-preserved',before==h.snap());a=h.login();h.request('/api/rooms?date=2030-04-11',cookie=a);h.request('/api/bookings?scope=team',cookie=a);h.request('/api/members',cookie=a);h.mark('health-future-restart',h.request('/api/health')[0]==200)
 finally:p.terminate();p.wait();log.close()
for name,fn in [('source-ip-and-rate',ip_rate),('missing-length',missing_length),('two-days-process-restart',future_process)]:h.save(name,fn)
(h.OUT/'trace.json').write_text(json.dumps({'lines':sorted(h.trace)},indent=2))
