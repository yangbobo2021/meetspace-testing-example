import subprocess,os,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];H=R/'harnesses/ui';logs=R/'evidence/ui-logs';logs.mkdir(exist_ok=True)
sequence=['run_ui_acceptance','run_ui_more','run_ui_supplement','run_ui_final','run_ui_completion','run_ui_edges','run_ui_last','run_ui_precision','run_ui_state_paths','run_ui_business_rejects','run_ui_stats_final','run_ui_keyboard_mobile','ui_races_r1','coverage_cycle_ui_identity','coverage_cycle_ui_dialogs','pending_identity_guards','extended_pending_ui','ui_gap_completion','filter_controls_r3']
records=[]
for name in sequence:
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MEETSPACE_COVERAGE_AUDIT':str(R/'evidence/ui-stage10')};Path(env['MEETSPACE_COVERAGE_AUDIT']).mkdir(exist_ok=True)
 start=time.time()
 with (logs/(name+'.log')).open('w') as log:
  try:p=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python',str(H/(name+'.py'))],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=650);rc=p.returncode
  except subprocess.TimeoutExpired:rc='timeout'
 records.append({'harness':name,'returncode':rc,'duration_seconds':time.time()-start,'log':str((logs/(name+'.log')).relative_to(R))});(R/'ui-harness-execution.json').write_text(json.dumps(records,indent=2));print(name,rc,flush=True)
