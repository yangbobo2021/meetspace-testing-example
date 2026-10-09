from pathlib import Path
import json,os,shutil,subprocess,time
B=Path(__file__).resolve().parent;ROOT=B.parents[3];D=B/'replay-projects/ui-wait-corrections';D.mkdir(parents=True,exist_ok=True)
for folder in ['app','web']:shutil.copytree(ROOT/folder,D/folder,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
(D/'web/app.js').write_text((B/'instrumented-app.js').read_text())
L=D/'tests/delivery-acceptance';(L/'harnesses').mkdir(parents=True,exist_ok=True);(L/'runs/fresh-coverage-stage10/evidence/runtime').mkdir(parents=True,exist_ok=True)
S=B/'replay-projects/ui-sequence/tests/delivery-acceptance'
for f in S.glob('*.json'):shutil.copy2(f,L/f.name)
for f in (S/'harnesses').glob('*.py'):shutil.copy2(f,L/'harnesses'/f.name)
p=L/'harnesses/run_ui_acceptance.py';t=p.read_text().replace("p.wait_for_function('() => state.user.role===\"member\" && !state.loading')", "p.wait_for_function('() => state.user?.role===\"member\" && !state.loading && !state.identityPending && !state.loadError && !!document.querySelector(\"#filter-date\")')")
p.write_text(t)
p=L/'harnesses/run_ui_final.py';t=p.read_text().replace("p.wait_for_function('() => document.querySelector(\"#toast\").textContent.length>0');assert not button.is_disabled()", "p.wait_for_function('() => !Array.from(document.querySelectorAll(\"[data-logout]\")).find(e=>e.offsetParent!==null).disabled');p.wait_for_function('() => document.querySelector(\"#toast\").textContent.length>0');assert not button.is_disabled()")
p.write_text(t)
(L/'harnesses/run_wait_corrections.py').write_text('''import run_ui_acceptance as b\nimport run_ui_final as f\nfrom playwright.sync_api import sync_playwright\nwith sync_playwright() as pw:\n b.browser=pw.chromium.launch(headless=True)\n b.group('role-demotion-wait-corrected',['AI-team-administration-7','AI-WB-ui-role-demotion-reload','AI-interface-experience-8'],b.role)\n b.group('logout-wait-corrected',['AI-interface-experience-8','AI-WB-ui-logout-races'],f.logout)\n b.browser.close()\n''')
P=B/'python-data/ui-wait-corrections';P.mkdir(exist_ok=True);env={**os.environ,'COVERAGE_PROCESS_START':str(B/'coverage.ini'),'COVERAGE_FILE':str(P/'.coverage'),'PYTHONPATH':str(B/'bootstrap')+os.pathsep+str(B.parent/'coverage-20261008-stage06/tools/python'),'MEETSPACE_COVERAGE_AUDIT':str(B),'COVERAGE_AUDIT_JOB':'ui-wait-corrections','PYTHONDONTWRITEBYTECODE':'1'}
start=time.monotonic()
with (B/'logs/ui-wait-corrections.log').open('w') as log:r=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python','tests/delivery-acceptance/harnesses/run_wait_corrections.py'],cwd=D,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
(B/'harness-wait-corrections.json').write_text(json.dumps({'job':'ui-wait-corrections','exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'initial_evidence':['replay-projects/ui-sequence/tests/delivery-acceptance/runs/fresh-coverage-stage10/evidence/ui/108-role-demotion.json','replay-projects/ui-sequence/tests/delivery-acceptance/runs/fresh-coverage-stage10/evidence/ui/305-logout-failure-recovery.json'],'reason':'原harness等待条件可被提前确认member的state及上一轮toast满足；补充等待最终有效DOM/按钮恢复，不修改任何业务断言、需求或产品。','corrected_results':'replay-projects/ui-wait-corrections/tests/delivery-acceptance/runs/fresh-coverage-stage10/ui-results.json'},ensure_ascii=False,indent=2))
