"""Archive a settled acceptance run without publishing SQLite/session files."""
from pathlib import Path
import hashlib,json,shutil,subprocess,collections,datetime
root=Path(__file__).resolve().parents[3]
assets=root/'tests/delivery-acceptance'
run_id='acceptance-20261008T-full-0b386b4-r1'
stage='stage-06-acceptance-run'
revision='0b386b4bd37b01eb996c5e74215ab1a4463a9487'
dst=root/'tests/snapshots'/stage
assert not dst.exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==revision
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()
last=json.loads((assets/'acceptance-workflow.log').read_text().splitlines()[-1])
assert last['sessionId']=='dc39aa9b-85c1-4166-9a18-375c42f84718'
run=json.loads((assets/'runs'/run_id/'run.json').read_text())
review=json.loads((assets/'runs'/run_id/'review.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert review['reviewed_run_sha256']==sha(assets/'runs'/run_id/'run.json')
for n,h in run['ledger_hashes'].items(): assert sha(assets/n)==h,(n,'changed ledger')
files=['project.json','requirements.json','resources.json','scenarios.json','methods.json','coverage_review.json','scenario-gate.json','design-assessment.json','acceptance-context.json','workflow-sessions.json','acceptance-workflow.log']
selected=[assets/f for f in files]
for folder in ['harnesses','evidence/resources','runs/'+run_id]: selected.extend(p for p in (assets/folder).rglob('*') if p.is_file())
selected += [Path(__file__),assets/'scripts/launch_acceptance.py']
excluded=[]
for src in sorted(set(selected)):
 rel=src.relative_to(assets)
 if '__pycache__' in rel.parts or src.name.endswith(('.sqlite','.sqlite-shm','.sqlite-wal','.db','.db-shm','.db-wal','.pyc')):
  excluded.append({'path':str(rel),'sha256':sha(src),'bytes':src.stat().st_size,'reason':'本机运行数据库、会话或缓存，不公开'})
  continue
 target=dst/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
(dst/'workflow-result.json').write_text(json.dumps({**last,'launcher_exit_code':0,'acceptance':'incomplete','terminal_run_id':run_id},ensure_ascii=False,indent=2)+'\n')
gate=json.loads((assets/'runs'/run_id/'gate-report.json').read_text())
assessment={'stage':stage,'tested_revision':revision,'terminal_run_id':run_id,'workflow_session_id':last['sessionId'],'acceptance':'incomplete','release_recommendation':'不建议发布当前版本','execution_claims':dict(collections.Counter(r['status'] for r in run['results'])),'independent_review':dict(collections.Counter(r['status'] for r in review['results'])),'gate_status':gate['status'],'gates':{k:v['status'] for k,v in gate['gates'].items()},'uncovered_branches':review['coverage']['uncovered_branches'],'failed_scenarios':[r['scenario_id'] for r in review['results'] if r['status']=='failed'],'unproven_scenarios':[r['scenario_id'] for r in review['results'] if r['status']=='unproven'],'findings':[{'id':'F-date-empty','actual':'显式空日期被回退为今天，应拒绝非法日期','evidence':'evidence/api-r2/room-read-dates.json'},{'id':'F-idempotency-microsecond','actual':'同请求标识下，起止时刻增加1微秒仍错误重放','evidence':'evidence/api-r2/precision.json'},{'id':'F-stale-401','actual':'旧身份迟到401清空已登录的新工作空间','evidence':'evidence/ui-races/old401-new-session.json'},{'id':'F-notification-runtime-format','actual':'本机Python3.12.4实际通知缺少日期和开始时刻，3.14对照不能抵消','evidence':'evidence/notification-runtime-control/results.json'}],'review_corrections':['非法角色的400断言超出确认需求，只需拒绝且不改角色，正式审阅改判通过','通知正文缺陷由专门场景判失败，不任意扩展所有创建场景的expected','未知HTTP动词、自身降权后身份读取失败缺完整证据，4个相关场景改判未证明'],'application_changes':False,'requirements_changes':False,'publication_exclusions':excluded}
(dst/'release-assessment.json').write_text(json.dumps(assessment,ensure_ascii=False,indent=2)+'\n')
manifest={'stage':stage,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tested_revision':revision,'requirements_sha256':sha(assets/'requirements.json'),'workflow_session_id':last['sessionId'],'run_id':run_id,'acceptance':'incomplete','independent_review_counts':assessment['independent_review'],'code_sha256':{f:sha(root/f) for f in ['app/server.py','app/__init__.py','web/app.js','web/index.html','web/style.css','tests/test_smoke.py']},'publication_exclusions':excluded,'files':{str(p.relative_to(dst)):sha(p) for p in sorted(dst.rglob('*')) if p.is_file()}}
(dst/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'archive':str(dst),'files':len(manifest['files']),'excluded':len(excluded),'review':assessment['independent_review']},ensure_ascii=False))
