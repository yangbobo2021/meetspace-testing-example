import concurrent.futures,datetime,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
BASE=Path(__file__).resolve().parent; ROOT=BASE.parents[3]
PYTHON='/Users/boboyang/.cloakbrowser-codex/venv/bin/python';OLD='0b386b4bd37b01eb996c5e74215ab1a4463a9487';REV=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
ASSETS=ROOT/'tests/delivery-acceptance';RUN='acceptance-20261008T-full-0b386b4-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sourcehash={f:sha(ROOT/f) for f in ['app/server.py','app/__init__.py','web/app.js','web/index.html','web/style.css','tests/test_smoke.py']}
BASE.joinpath('python-data').mkdir(exist_ok=True);BASE.joinpath('logs').mkdir(exist_ok=True)
config=BASE/'coverage.ini'
config.write_text(f'''[run]\nbranch = True\nparallel = True\nsigterm = True\nconcurrency = thread\ninclude = */app/server.py\n[report]\nexclude_lines =\n[paths]\nserver =\n    {ROOT}/app\n    {BASE}/replay-projects/*/app\n    {BASE}/replay-projects/*/tests/delivery-acceptance/runs/{RUN}/evidence/runtime/startup-copy/app\n    {BASE}/replay-projects/*/tests/delivery-acceptance/runs/independent-covered-probes-20261008/isolated-*/app\n''')
jobs=['test_smoke','full_api_matrix_r2','api_review_completion','runtime_execute','runtime_supplement','runtime_complete','runtime_edges','runtime_finish','runtime_storage_final','runtime_gap_faults_r1','runtime_startup','run_ui_acceptance','run_ui_more','run_ui_supplement','run_ui_final','run_ui_completion','run_ui_edges','run_ui_last','run_ui_precision','run_ui_state_paths','run_ui_business_rejects','run_ui_stats_final','run_ui_keyboard_mobile','ui_races_r1','notification_runtime_control_r1']
manifest={'revision':REV,'source_hashes':sourcehash,'previous_acceptance_revision':OLD,'original_acceptance_hashes':{n:sha(ASSETS/'runs'/RUN/n) for n in ['run.json','review.json','gate-report.json']},'tools':{'python_coverage':'7.16.2','istanbul':'6.0.3'},'scope':'all current executable smoke + final acceptance harnesses, isolated copies; library helpers invoked by their callers; historical superseded full_api_matrix excluded in favour of r2; old verifier/compilers do not constitute additional business tests','adaptations':['copied project and independent SQLite per harness','copy historical revision strings to current Git revision; original application SHA unchanged','replace copied sys.settrace/threading.settrace collectors with coverage.py measurement; no assertion changes','serve only copied JavaScript with Istanbul counters; collect before navigation/close','copied fixture metadata is coverage replay, not new reviewed acceptance'], 'jobs':[]}
(BASE/'audit-context.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def prepare(name):
 d=BASE/'replay-projects'/name;d.mkdir(parents=True,exist_ok=True)
 for folder in ['app','web']:shutil.copytree(ROOT/folder,d/folder,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
 (d/'web/app.js').write_text((BASE/'instrumented-app.js').read_text())
 led=d/'tests/delivery-acceptance';(led/'harnesses').mkdir(parents=True,exist_ok=True);(led/'runs'/RUN/'evidence/runtime').mkdir(parents=True,exist_ok=True)
 for f in ASSETS.glob('*.json'):shutil.copy2(f,led/f.name)
 for f in (ASSETS/'harnesses').glob('*.py'):
  text=f.read_text().replace(OLD,REV).replace('threading.settrace(tracer)','pass').replace('sys.settrace(tracer)','pass')
  (led/'harnesses'/f.name).write_text(text)
 shutil.copy2(ROOT/'tests/test_smoke.py',d/'tests/test_smoke.py')
 return d
for job in jobs:prepare(job)
def run(name):
 cwd=BASE/'replay-projects'/name;out=BASE/'python-data'/name;out.mkdir(exist_ok=True)
 env={**os.environ,'COVERAGE_PROCESS_START':str(config),'COVERAGE_FILE':str(out/'.coverage'),'PYTHONPATH':str(BASE/'bootstrap')+os.pathsep+str(BASE/'tools/python'),'MEETSPACE_COVERAGE_AUDIT':str(BASE),'COVERAGE_AUDIT_JOB':name,'PYTHONDONTWRITEBYTECODE':'1'}
 cmd=[PYTHON,'-m','unittest','discover','-s','tests','-v'] if name=='test_smoke' else [PYTHON,'tests/delivery-acceptance/harnesses/'+name+'.py']
 start=time.monotonic()
 try:
  with (BASE/'logs'/(name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  result={'job':name,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'log':'logs/'+name+'.log'}
 except subprocess.TimeoutExpired:result={'job':name,'status':'timeout','seconds':round(time.monotonic()-start,2),'log':'logs/'+name+'.log'}
 print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(run,jobs):
  manifest['jobs'].append(result);(BASE/'audit-context.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
assert sourcehash=={f:sha(ROOT/f) for f in sourcehash}
for n,h in manifest['original_acceptance_hashes'].items():assert sha(ASSETS/'runs'/RUN/n)==h
manifest['original_source_and_acceptance_unchanged']=True;(BASE/'audit-context.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
