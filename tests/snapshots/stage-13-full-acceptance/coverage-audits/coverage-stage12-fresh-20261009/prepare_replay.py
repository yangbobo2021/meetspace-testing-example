import concurrent.futures,datetime,hashlib,json,os,shutil,subprocess,time,re
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];ASSETS=ROOT/'tests/delivery-acceptance';OLD_BASE=BASE.parent/'coverage-20261008-stage06'
PYTHON='/Users/boboyang/.cloakbrowser-codex/venv/bin/python';REV='5247b360276f2900d20fdeab96bd75bb3ece73fa';OLD='0b386b4bd37b01eb996c5e74215ab1a4463a9487';RUN='fresh-coverage-stage12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['app/server.py','app/__init__.py','web/app.js','web/index.html','web/style.css','tests/test_smoke.py','tests/test_regressions.py']
sourcehash={f:sha(ROOT/f) for f in files}
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==REV
for d in ['bootstrap','python-data','logs','harnesses']: (BASE/d).mkdir(exist_ok=True)
# bootstrap already frozen from previous tooling; no old counters copied
instrument=(OLD_BASE/'instrument.js').read_text().replace("require('./tools/node/node_modules/istanbul-lib-instrument')",f"require({json.dumps(str(OLD_BASE/'tools/node/node_modules/istanbul-lib-instrument'))})")
(BASE/'instrument.js').write_text(instrument);subprocess.run(['node',str(BASE/'instrument.js')],check=True)
config=BASE/'coverage.ini';config.write_text(f'[run]\nbranch = True\nparallel = True\nsigterm = True\nconcurrency = thread\ninclude = */app/server.py\n[report]\nexclude_lines =\n')
ui=['run_ui_acceptance','run_ui_more','run_ui_supplement','run_ui_final','run_ui_completion','run_ui_edges','run_ui_last','run_ui_precision','run_ui_state_paths','run_ui_business_rejects','run_ui_stats_final','run_ui_keyboard_mobile']
other=['test_smoke','full_api_matrix_r2','api_review_completion','runtime_execute','runtime_supplement','runtime_complete','runtime_finish','runtime_storage_final','runtime_gap_faults_r1','runtime_startup','ui_races_r1','notification_runtime_control_r1','full_api_matrix','execute_covered_review_probes']
manifest={'revision':REV,'source_hashes':sourcehash,'coverage_is_not_acceptance':True,'tools_reused_not_counters':str(OLD_BASE/'tools'),'counter_input_root':str(BASE),'instrumented_sha256':sha(BASE/'instrumented-app.js'),'adaptations':['Historical source pins replaced only in copied harnesses.','Historical sys.settrace/threading.settrace collectors disabled only in copies; fault injectors unchanged.','All UI continuations use one fresh shared project and sequential progress; no old passed metadata seeded; known historical DOM/button synchronization wait corrections applied only to copied harnesses before run.','runtime_startup coverage variant uses port0/localhost+decodedstdout and removes -S; protects userdemo; actual default/Python311 CLI matrix remains formal isolatedDocker.','Current malformed role rejects require400 stableJSON, copied assertions remain strict.','Identity supplement uses corrected native13 harness; raw r2 34 harness preserved, only explicit transparent Istanbul mode inserted in copied guardrails, assertions unchanged.'],'job_count_planned':33,'standard_unittest_count_expected':8,'native_identity_matrix_expected':34,'raw_native_harness_preserved':'raw-native-r2','coverage_transparent_harness':'native-r2-coverage-harness','jobs':[]}
(BASE/'audit-context.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def adapt(text):
 text=text.replace(OLD,REV).replace('acceptance-20261008T-full-0b386b4-r1',RUN).replace('threading.settrace(tracer)','pass').replace('sys.settrace(tracer)','pass')
 text=text.replace('/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts','/Users/boboyang/.codex/skills/app-delivery-acceptance/scripts')
 return text

def prepare(name):
 d=BASE/'replay-projects'/name;d.mkdir(parents=True,exist_ok=True)
 for folder in ['app','web']:shutil.copytree(ROOT/folder,d/folder,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
 (d/'web/app.js').write_text((BASE/'instrumented-app.js').read_text())
 led=d/'tests/delivery-acceptance';(led/'harnesses').mkdir(parents=True,exist_ok=True);(led/'runs'/RUN/'evidence/runtime').mkdir(parents=True,exist_ok=True)
 for f in ASSETS.glob('*.json'):shutil.copy2(f,led/f.name)
 for f in (ASSETS/'harnesses').glob('*.py'):(led/'harnesses'/f.name).write_text(adapt(f.read_text()))
 for f in ['test_smoke.py','test_regressions.py']:shutil.copy2(ROOT/'tests'/f,d/'tests'/f)
 if name=='runtime_startup':
  p=led/'harnesses/runtime_startup.py';text=p.read_text().replace("[sys.executable,'-S','-m','app.server',*args]","[sys.executable,'-m','app.server',*args]")
  start=text.index("for name,args,host,port in ");end=text.index(':\n log=',start)
  text=text[:start]+"for name,args,host,port in [('default',['--port','0'],'127.0.0.1',0),('host',['--host','localhost','--port','0'],'localhost',0),('port',['--port','0'],'127.0.0.1',0),('db',['--port','0','--db',str(copy/'custom.sqlite')],'127.0.0.1',0),('all',['--host','localhost','--port','0','--db',str(copy/'all.sqlite')],'localhost',0)]"+text[end:]
  text=text.replace("log=open(OUT/('startup-'+name+'.log'),'w');p=subprocess.Popen", "log=open(OUT/('startup-'+name+'.log'),'w');p=subprocess.Popen")
  text=text.replace("stdout=log,stderr=log","stdout=subprocess.PIPE,stderr=log,text=True").replace("  response=None","  line=p.stdout.readline();port=int(re.search(r':(\\d+)',line).group(1));response=None")
  p.write_text(text)
 if name=='execute_covered_review_probes':
  r=led/'runs/independent-covered-probes-20261008';r.mkdir(parents=True,exist_ok=True);(r/'run.json').write_text(json.dumps({'revision':REV,'results':[],'ledger_hashes':{n:sha(led/n) for n in ['requirements.json','scenarios.json','methods.json']}}))
 # Known historical synchronization corrections apply only to copied harnesses.
 p=led/'harnesses/run_ui_acceptance.py';text=p.read_text().replace("p.wait_for_function('() => state.user.role===\"member\" && !state.loading')", "p.wait_for_function('() => state.user?.role===\"member\" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector(\"#filter-date\")')");p.write_text(text)
 p=led/'harnesses/run_ui_final.py';text=p.read_text().replace("p.wait_for_function('() => document.querySelector(\"#toast\").textContent.length>0');assert not button.is_disabled()", "p.wait_for_function('() => !Array.from(document.querySelectorAll(\"[data-logout]\")).find(e=>e.offsetParent!==null).disabled');p.wait_for_function('() => document.querySelector(\"#toast\").textContent.length>0');assert not button.is_disabled()");p.write_text(text)
 return d
for name in other+['ui-sequence']:prepare(name)
# runtime_edges uses the actual runtime_complete same-round process-persist fixture.
for name in ['coverage_cycle_api','coverage_cycle_ui_dialogs']:
 text=adapt((ASSETS/'harnesses'/f'{name}.py').read_text())
 if name=='coverage_cycle_api':text=text.replace('ROOT = Path(__file__).resolve().parents[3]','ROOT = Path.cwd()').replace("BASE = ROOT / 'tests/delivery-acceptance/coverage-audits/coverage-20261009-stage08-r1'","BASE = Path(os.environ['MEETSPACE_COVERAGE_AUDIT'])")
 (BASE/'harnesses'/f'{name}.py').write_text(text)
shutil.copy2(ASSETS/'release-preparation/20261009/identity-fix-development-controls-r2/harnesses/coverage_cycle_ui_identity.py',BASE/'harnesses/coverage_cycle_ui_identity.py')
shutil.copy2(ASSETS/'release-preparation/20261009/identity-fix-development-controls-r2/harnesses/pending_identity_guards.py',BASE/'harnesses/pending_identity_guards.py')
(BASE/'harnesses/static_unsupported_control.py').write_text((BASE.parent/'coverage-stage10-fresh-20261009/harnesses/static_unsupported_control.py').read_text().replace('708c9c057b5c9014f4ff975fdc5774093a687abe',REV))
NATIVE=BASE/'native-identity';NATIVE.mkdir();shutil.copy2(BASE/'instrumented-app.js',NATIVE/'instrumented-app.js')
def run(name,cwd=None,args=None):
 cwd=cwd or BASE/'replay-projects'/name;out=BASE/'python-data'/name;out.mkdir(exist_ok=True)
 env={**os.environ,'COVERAGE_PROCESS_START':str(config),'COVERAGE_FILE':str(out/'.coverage'),'PYTHONPATH':str(BASE/'bootstrap')+os.pathsep+str(OLD_BASE/'tools/python'),'MEETSPACE_COVERAGE_AUDIT':str(BASE),'COVERAGE_AUDIT_JOB':name,'PYTHONDONTWRITEBYTECODE':'1'}
 cmd=args or ([PYTHON,'-m','unittest','discover','-s','tests','-v'] if name=='test_smoke' else [PYTHON,'tests/delivery-acceptance/harnesses/'+name+'.py'])
 start=time.monotonic()
 try:
  with (BASE/'logs'/(name+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
  result={'job':name,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'log':'logs/'+name+'.log'}
 except subprocess.TimeoutExpired:result={'job':name,'status':'timeout','seconds':round(time.monotonic()-start,2),'log':'logs/'+name+'.log'}
 print(json.dumps(result),flush=True)
 manifest['jobs'].append(result);(BASE/'audit-context.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');return result

def ui_group():
 for name in ui:run(name,BASE/'replay-projects/ui-sequence')

def supplemental():
 for name in ['coverage_cycle_api','coverage_cycle_ui_identity','coverage_cycle_ui_dialogs','pending_identity_guards','static_unsupported_control']:run(name,ROOT,[PYTHON,str(BASE/'harnesses'/f'{name}.py')])
def runtime_dependency():
 run('runtime_complete')
 run('runtime_edges',BASE/'replay-projects/runtime_complete')
def native_matrix():
 return run('native-identity-r2',ROOT,[PYTHON,str(BASE/'native-r2-coverage-harness/matrix.py'),'--coverage-transparent-instrumentation','--expected-js-sha256',sourcehash['web/app.js'],'--output',str(NATIVE)])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 fs=[pool.submit(ui_group),pool.submit(supplemental),pool.submit(native_matrix),pool.submit(runtime_dependency)]+[pool.submit(run,name) for name in other if name!='runtime_complete']
 for f in concurrent.futures.as_completed(fs):f.result()
assert sourcehash=={f:sha(ROOT/f) for f in sourcehash}
manifest['source_unchanged']=True;(BASE/'audit-context.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
