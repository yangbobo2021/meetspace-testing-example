import runtime_execute as h,sys,json
from pathlib import Path
h.clock[0]=float(sys.argv[2]);s=h.app.ApplicationServer(('127.0.0.1',0),h.app.Store(Path(sys.argv[1])));print(json.dumps({'port':s.server_port}),flush=True);s.serve_forever()
