"""Coverage diagnostic for inherited non-API rejection; not an added business requirement."""
import hashlib,http.client,importlib.util,json,os,shutil,sqlite3,threading
from pathlib import Path
R=Path.cwd();B=Path(os.environ['MEETSPACE_COVERAGE_AUDIT']);D=B/'isolated-static-control';D.mkdir(exist_ok=True)
for folder in ['app','web']:shutil.copytree(R/folder,D/folder,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
assert hashlib.sha256((D/'app/server.py').read_bytes()).digest()==hashlib.sha256((R/'app/server.py').read_bytes()).digest()
spec=importlib.util.spec_from_file_location('static_control_server',D/'app/server.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
db=D/'fixture.sqlite';db.unlink(missing_ok=True);s=m.ApplicationServer(('127.0.0.1',0),m.Store(db));t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
def snap():
 with sqlite3.connect(db) as c:return {tab:c.execute('select count(*) from '+tab).fetchone()[0] for tab in ['teams','users','rooms','bookings','notifications','sessions']}
before=snap();rows=[]
try:
 for method in ['DELETE','OPTIONS','PUT']:
  for path in ['/','/app.js','/style.css']:
   c=http.client.HTTPConnection('127.0.0.1',s.server_port);c.request(method,path);r=c.getresponse();raw=r.read();row={'method':method,'path':path,'status':r.status,'content_type':r.getheader('Content-Type'),'body_excerpt':raw.decode(errors='replace')[:160],'business_counts_before':before,'business_counts_after':snap()};row['passed']=r.status==501 and 'text/html' in row['content_type'] and before==row['business_counts_after'];rows.append(row);c.close()
finally:s.shutdown();s.server_close();t.join()
(B/'static-unsupported-control.json').write_text(json.dumps({'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','source_sha256':hashlib.sha256((R/'app/server.py').read_bytes()).hexdigest(),'scope':'Non-API static path inherited rejection compatibility diagnostic; no new business requirement or formal ledger result. All API unsupported methods independently require JSON.','results':rows,'passed':all(x['passed'] for x in rows)},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'items':len(rows),'passed':all(x['passed'] for x in rows)}))
