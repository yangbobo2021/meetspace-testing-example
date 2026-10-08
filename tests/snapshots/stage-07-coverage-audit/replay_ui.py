import json,os,shutil,subprocess,time
from pathlib import Path
BASE=Path(__file__).resolve().parent;RUN='acceptance-20261008T-full-0b386b4-r1';seed=BASE/'replay-projects/run_ui_acceptance/tests/delivery-acceptance/runs'/RUN
jobs=['run_ui_more','run_ui_supplement','run_ui_final','run_ui_completion','run_ui_edges','run_ui_last','run_ui_precision','run_ui_state_paths','run_ui_business_rejects','run_ui_stats_final','run_ui_keyboard_mobile']
results=[]
for name in jobs:
 cwd=BASE/'replay-projects'/name;run=cwd/'tests/delivery-acceptance/runs'/RUN
 shutil.copy2(seed/'ui-results.json',run/'ui-results.json');shutil.copy2(seed/'evidence/ui/progress.json',run/'evidence/ui/progress.json')
 out=BASE/'python-data'/name
 env={**os.environ,'COVERAGE_PROCESS_START':str(BASE/'coverage.ini'),'COVERAGE_FILE':str(out/'.coverage'),'PYTHONPATH':str(BASE/'bootstrap')+os.pathsep+str(BASE/'tools/python'),'MEETSPACE_COVERAGE_AUDIT':str(BASE),'COVERAGE_AUDIT_JOB':name,'PYTHONDONTWRITEBYTECODE':'1'}
 start=time.monotonic()
 with (BASE/'logs'/(name+'-dependency-replay.log')).open('w') as log:
  r=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python','tests/delivery-acceptance/harnesses/'+name+'.py'],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 rec={'job':name,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'log':'logs/'+name+'-dependency-replay.log'};results.append(rec);print(json.dumps(rec),flush=True)
 (BASE/'ui-replay-context.json').write_text(json.dumps({'reason':'续测依赖前轮UI结果与progress结构；从本次实际重跑结果按顺序复制，不使用旧验收的业务断言作为覆盖证据','jobs':results},ensure_ascii=False,indent=2)+'\n')
 if r.returncode==0:seed=run
