import pathlib,subprocess
r=pathlib.Path(__file__).resolve().parents[2]
for name,script in [('ptrace-preflight','ptrace_preflight.py'),('ptrace-extended','ptrace_extended_preflight.py'),('network-metadata','network_metadata_probe.py'),('notification-linux','notification_matrix.py')]:
 out=r/'evidence'/name;out.mkdir()
 h=r/'harnesses'/('runtime' if name=='notification-linux' else 'entropy')
 cmd=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','seccomp=unconfined','--tmpfs','/tmp','--mount',f'type=bind,source={r}/harnesses/runtime-source,target=/source,readonly','--mount',f'type=bind,source={h},target=/harness,readonly','--mount',f'type=bind,source={out},target=/output','--entrypoint','python','sha256:6e73bceac9263be174946cc91d68a55cc2996fcc57cba43f33df17af20bad02c','-B','/harness/'+script]
 cmd+=['/source','/output'] if name=='notification-linux' else ['--output','/output']
 if name=='network-metadata':cmd+=['--source','/source','--revision','5247b360276f2900d20fdeab96bd75bb3ece73fa']
 with open(out/'execution.log','w') as f:code=subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT)
 print(name,code,flush=True)
