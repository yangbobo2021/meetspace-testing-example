import sys,json,socket,http.client,inspect
from pathlib import Path
import coverage_cycle_api as h
R=Path(__file__).resolve().parents[1]
h.PROJECTS.mkdir(parents=True,exist_ok=True)
items=[]
for kind in ['too_many_headers','long_header','static_delete','head_static','head_api']:
 f=h.Fixture('protocol-'+kind)
 try:
  before=f.snapshot(); replies=[]; traces=[]
  for repeat in range(2):
   f.calls.clear()
   if kind in ['too_many_headers','long_header']:
    extra=(b''.join(('X-Test-%d: x\r\n'%i).encode() for i in range(101)) if kind=='too_many_headers' else b'X-Test: '+b'x'*65537+b'\r\n')
    payload=b'GET /api/rooms HTTP/1.1\r\nHost: localhost\r\n'+extra+b'\r\n'
    s=socket.create_connection(('127.0.0.1',f.port),timeout=5);s.sendall(payload)
    response=http.client.HTTPResponse(s); response.begin();raw=response.read();replies.append({'status':response.status,'content_type':response.getheader('Content-Type'),'json':json.loads(raw),'request_shape':kind,'raw_request_line':'GET /api/rooms HTTP/1.1','extra_header_bytes':len(extra)});s.close()
   else:
    conn=http.client.HTTPConnection('127.0.0.1',f.port);conn.request('DELETE' if kind=='static_delete' else 'HEAD','/api/health' if kind=='head_api' else '/');res=conn.getresponse();raw=res.read();replies.append({'status':res.status,'body_length':len(raw),'content_length':res.getheader('Content-Length')});conn.close()
   traces.append(list(f.calls))
  health,_=f.req('GET','/api/health')
  checks={'no_business_writes':before==f.snapshot(),'healthy_after':health['status']==200}
  if kind in ['too_many_headers','long_header']:
   checks.update({'two_real_431':all(x['status']==431 for x in replies),'stable_json_error_code':all(x['json'].get('error') and x['json'].get('code') for x in replies) and replies[0]['json']['code']==replies[1]['json']['code'],'api_431_send_error_trace':all(any(x['function']=='send_error' and x['error_code']==431 and x['path']=='/api/rooms' for x in ts) for ts in traces),'no_dispatch':all(not any(x['function']=='dispatch' for x in ts) for ts in traces)})
  elif kind=='static_delete':checks['static_rejected']=all(x['status']>=400 for x in replies)
  else:checks['no_head_entity']=all(x['body_length']==0 for x in replies)
  items.append({'name':kind,'status':'passed' if all(checks.values()) else 'failed','checks':checks,'responses':replies,'traces':traces,'before':before,'after':f.snapshot()})
 finally:f.close()
result={'python':sys.version,'stdlib_parse_request_source':inspect.getsource(http.server.BaseHTTPRequestHandler.parse_request) if False else inspect.getsource(h.socketserver.BaseServer)[:0], 'items':items}
import http.server
result['stdlib_parse_request_source']=inspect.getsource(http.server.BaseHTTPRequestHandler.parse_request)
(R/'evidence/api-protocol-supplement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print([(x['name'],x['status']) for x in items])
