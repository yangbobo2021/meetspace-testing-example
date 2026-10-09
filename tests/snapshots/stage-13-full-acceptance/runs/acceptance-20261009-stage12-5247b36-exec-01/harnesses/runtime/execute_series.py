import subprocess,pathlib,os
h=pathlib.Path(__file__).resolve().parent;r=h.parents[1]
for name in ['runtime_execute','runtime_supplement','runtime_complete','runtime_finish','runtime_edges','runtime_storage_final','runtime_gap_faults_r1']:
 with open(r/'evidence/runtime'/f'{name}.log','w') as f:p=subprocess.run(['python3','-B',str(h/(name+'.py'))],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 print(name,p.returncode,flush=True)
