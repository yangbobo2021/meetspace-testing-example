import pathlib,json,subprocess
base=pathlib.Path(__file__).resolve().parent;source=base.parent/'git-pinned-source';harness=base/'frozen-harness'
results=[]
for i in range(8):
 out=base/f'seed-e2-{i}';out.mkdir()
 cmd=['docker','run','--rm','--log-driver=none','--network','none','--read-only','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','seccomp=unconfined','--tmpfs','/tmp']
 for src,tgt,readonly in [(source/'app','/source/app',True),(source/'web','/source/web',True),(harness,'/harness',True),(out,'/output',False)]:cmd+=['--mount',f'type=bind,source={src},target={tgt}'+(',readonly' if readonly else '')]
 cmd+=['--entrypoint','python','sha256:6e73bceac9263be174946cc91d68a55cc2996fcc57cba43f33df17af20bad02c','-S','/harness/entropy_business_branch.py','--source','/source','--output','/output','--prefix','seed','--tape','E2','--revision','5247b360276f2900d20fdeab96bd75bb3ece73fa','--execute']
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
 # stdout includes in-memory comparison materials, never persist/print it.
 x=json.loads(r.stdout)['report'] if r.returncode==0 else json.loads((out/'business-results.json').read_text())
 findings=[]
 for phase in ['os_trace','os_trace_restart']:
  t=x.get(phase,{})
  findings.append({'phase':phase,'uncovered':t.get('uncovered',[]),'mapping_failures':[e for e in t.get('events',[]) if e['kind']=='mapping_read_failure']})
 results.append({'name':out.name,'exit_code':r.returncode,'findings':findings})
 print(json.dumps(results[-1]),flush=True)
(base/'diagnostic-results.json').write_text(json.dumps({'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','formal_verdict':None,'results':results},indent=2))
