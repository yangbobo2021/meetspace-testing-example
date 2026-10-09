import pathlib,subprocess,json,os
r=pathlib.Path(__file__).resolve().parents[2]
images={'311':'sha256:8129910271f9764b5c05038d351ad7b9f9d94b85351355b69c5526eadd111775','312':'sha256:ce9a404c2c0138e747a43e6ea022d2f7e670ed868df35d627a663ba7fb940ea9'}
for version,image in images.items():
 out=r/'evidence'/('cli'+version);out.mkdir()
 cmd=['docker','run','--rm','--network','none','--read-only','--tmpfs','/tmp','--mount',f'type=bind,source={r}/harnesses/runtime-source,target=/source,readonly','--mount',f'type=bind,source={r}/harnesses/entropy,target=/harness,readonly','--mount',f'type=bind,source={out},target=/output','--entrypoint','python',image,'-S','/harness/cli_isolation_matrix.py','--source','/source','--output','/output','--revision','5247b360276f2900d20fdeab96bd75bb3ece73fa','--freeze-clock','--execute']
 with open(out/'execution.log','w') as f:code=subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT)
 print(version,code,flush=True)
