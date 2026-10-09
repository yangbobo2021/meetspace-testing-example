import pathlib,json,subprocess
base=pathlib.Path(__file__).resolve().parent;source=base.parent/'git-pinned-source';harness=base/'frozen-harness';revision='5247b360276f2900d20fdeab96bd75bb3ece73fa'
image='sha256:6e73bceac9263be174946cc91d68a55cc2996fcc57cba43f33df17af20bad02c'
results=[]
def run(name,args,image_id=image,entry='python',exec_tmp=False):
 out=base/name;out.mkdir()
 cmd=['docker','run','--rm','--log-driver=none','--network','none','--read-only','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','seccomp=unconfined','--tmpfs','/tmp:exec' if exec_tmp else '/tmp']
 for src,tgt,readonly in [(source/'app','/source/app',True),(source/'web','/source/web',True),(harness,'/harness',True),(base/'concurrent_mapping_probe.c','/concurrent_mapping_probe.c',True),(out,'/output',False)]:cmd+=['--mount',f'type=bind,source={src},target={tgt}'+(',readonly' if readonly else '')]
 cmd+=['--entrypoint',entry,image_id]+args
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
 results.append({'name':name,'exit_code':r.returncode,'stderr':r.stderr,'image_id':image_id});print(json.dumps(results[-1]),flush=True)
 if r.returncode:raise RuntimeError(name+' incomplete')
run('preflight-basic',['-S','/harness/ptrace_preflight.py','--output','/output'])
run('preflight-extended',['-S','/harness/ptrace_extended_preflight.py','--output','/output'])
run('concurrent-mapping-probe',['-c','gcc -O0 -pthread /concurrent_mapping_probe.c -o /tmp/probe && python -S /harness/ptrace_os_adapter.py --output /output -- /tmp/probe'],entry='sh',exec_tmp=True)
trace=json.loads((base/'concurrent-mapping-probe/os-events.json').read_text());probe={'container_exit_code':results[-1]['exit_code'],'iterations':300,'target_exit_count':len(trace['exits']),'all_target_exits_zero':all(v=={'exit_code':0,'signal':None} for v in trace['exits'].values()),'detected_leaks':trace['counters'].get('leaks',0),'uncovered':trace['uncovered'],'formal_verdict':None,'scope':'公開合成密码写入共享映射后munmap与另一线程退出；负控，非产品成功断言'};(base/'concurrent-mapping-probe/probe-results.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2))
run('network',['-S','/harness/network_metadata_probe.py','--source','/source','--output','/output','--revision',revision])
for name,image_id in [('cli311','sha256:8129910271f9764b5c05038d351ad7b9f9d94b85351355b69c5526eadd111775'),('cli312','sha256:ce9a404c2c0138e747a43e6ea022d2f7e670ed868df35d627a663ba7fb940ea9')]:
 run(name,['-S','/harness/cli_isolation_matrix.py','--source','/source','--output','/output','--revision',revision,'--freeze-clock','--execute'],image_id=image_id)
(base/'controls-execution.json').write_text(json.dumps({'revision':revision,'rows':results,'formal_verdict':None},ensure_ascii=False,indent=2))
