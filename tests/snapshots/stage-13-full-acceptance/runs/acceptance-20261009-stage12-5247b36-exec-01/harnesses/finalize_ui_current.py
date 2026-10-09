import json,ast,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];L=R.parents[1];methods={x['id']:x for x in json.load(open(L/'methods.json'))['items']};raw=json.load(open(R/'ui-results.json'));out={};groups={};errors=[]
def add(mid,status,actual,ev):
 x=out.setdefault(mid,{'method_id':mid,'status':'passed','actual':'','evidence':[],'executed_paths':[]})
 if status=='failed' or x['status']=='failed':x['status']='failed'
 elif status!='passed':x['status']='unproven'
 x['executed_paths'].append({'status':status,'actual':actual,'evidence':ev});x['evidence']=sorted(set(x['evidence']+ev))
for p in sorted((R/'evidence/ui').glob('*.json')):
 d=json.load(open(p))
 if not d.get('methods'):continue
 status='passed' if d.get('assertions_completed') and not d.get('traceback') else 'failed' if 'AssertionError' in d.get('traceback','') else 'unproven'
 ev=[str(p.relative_to(R))]+([d['screenshot']] if d.get('screenshot') else [])
 for mid in d['methods']:add(mid,status,d['name'],ev)
 groups[d['name']]=(status,ev)
# Fresh composite matrix reports retain every asserted failure/unproven path.
for rel in ['ui-races-results.json','evidence/ui-stage10/ui-identity-results.json','evidence/ui-stage10/ui-dialog-results.json']:
 p=R/rel;d=json.load(open(p));base='' if p.parent==R else str(p.parent.relative_to(R))+'/'
 for row in d.get('method_results',d.get('results',[])):
  for mid in [row['method_id']] if 'method_id' in row else row['method_ids']:add(mid,row['status'],row['actual'],[base+z for z in row['evidence']])
for fname in ['pending-guard-results.json','extended-pending-results.json','ui-gap-results.json']:
 p=R/'evidence/ui-stage10'/fname;d=json.load(open(p));base=str(p.parent.relative_to(R))+'/'
 for row in d['results']:
  mids=[row['method_id']] if 'method_id' in row else row.get('method_ids')
  if not mids:mids=['AI-WB-ui-self-demotion-session-failure'] if row['name'].startswith('pending-retry-') else ['AI-WB-ui-load-token-races'] if row['name'] in ['stale-token','same-token-user-absent'] else ['AI-WB-ui-role-demotion-reload']
  for mid in mids:add(mid,row['status'],row['name'],[base+row['evidence']])
mat={}
for folder,count in [('native34',34),('pending-six',6)]:
 d=json.load(open(R/'evidence'/folder/'results.json'));assert len(d['results'])==count
 for row in d['results']:mat[row['name']]={**row,'evidence':'evidence/'+folder+'/'+row['evidence']}
for mid,m in methods.items():
 keys=[x['key'] for x in m.get('matrix_checks',[])]+[x['key'] for x in m.get('matrix_check_refs',[])]
 for key in keys:
  row=mat.get(key);add(mid,row['status'] if row else 'unproven',key,[row['evidence']] if row else [])
for row in json.load(open(R/'evidence/pending-retry-four/results.json'))['results']:
 for mid in ['AI-WB-ui-load-parallel-error','AI-WB-ui-self-demotion-session-failure','AI-WB-ui-role-demotion-reload']:
  add(mid,row['status'],row['name'],['evidence/pending-retry-four/'+row['evidence']])
# Explicit supplements on the same execution only; API owner supplied actual browser badge observations.
extras={
 'AI-WB-ui-notification-render':['evidence/api-r2/notifications.json'],
 'AI-reservation-management-10':['evidence/api-r2/cancel-permission-clock.json'],
 'AI-team-administration-7':['evidence/api-r2/scope-and-first-role.json'],
 'AI-WB-ui-api-error-session-transition':['evidence/ui/301-submit-button-fault-matrix.json'],
 'AI-WB-ui-default-times':['evidence/ui/405-two-room-dialog-details.json'],
 'AI-WB-ui-room-timeline-agenda':['evidence/ui/405-two-room-dialog-details.json'],
 'AI-interface-experience-4':['evidence/ui/202-timeline-boundaries.json'],
 'AI-WB-ui-login-navigation':['evidence/ui/605-api-default-error-and-wrong-password.json'],
 'AI-space-administration-3':['evidence/room-full-update/results.json']}
for mid,evs in extras.items():
 for ev in evs:
  assert (R/ev).exists(),ev
  d=json.load(open(R/ev));bad=d.get('status') in ['failed','unproven'] or bool(d.get('traceback')) or any(c.get('passed') is False for c in d.get('checks',[]));add(mid,'unproven' if bad else 'passed','本run完整方法补充分支 '+ev,[ev])
if 'AI-space-administration-3' in out:
 out['AI-space-administration-3']['supplement_only']=True
 out['AI-space-administration-3']['required_supplement']='与API room-crud每步已有预约详情读取共同构成完整方法；此新增证据负责真实UI逐字段/全字段/退出重登读回。'
for mid,x in out.items():
 for e in x['evidence']:assert (R/e).exists(),e
 x['actual']='当前固定HEAD在本run实际执行 '+str(len(x['executed_paths']))+' 个记录/矩阵项；'+('全部所列断言完成。' if x['status']=='passed' else '含失败或尚未证明分项，保持原状态。')+'路径：'+'；'.join(p['actual'] for p in x['executed_paths'])
 x['method_definition_sha256']=hashlib.sha256(json.dumps(methods[mid],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
expected={m for m in methods if m.startswith(('AI-interface-experience-','AI-WB-ui-'))};assert not expected-set(out),expected-set(out)
report={'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'run_id':R.name,'environment':raw['environment'],'dependency_checks':[{'id':'ui-python-playwright-local-app','status':'passed','actual':'本run Chromium '+raw['environment']['browser']+'；所有UI真实访问当前HEAD HTTP应用，独立合成SQLite/匿名127.0.0.1端口；北京时间2030-04-10及明确逐项浏览器/服务器时间矩阵；故障只在指定浏览器请求边界。','evidence':['ui-harness-execution.json','ui-harness-adaptation.json','evidence/native34/results.json','evidence/pending-six/results.json']}],'method_results':list(out.values()),'execution_manifest':'ui-harness-execution.json','native_matrix_items':len(mat),'real_integration_scope':'真实本地HTTP/SQLite/Chromium；无第三方集成','fault_injection_scope':'503/abort/nonJSON为UI依赖故障模拟，不能证明服务真实503；真实401来自后端会话到期/撤销。','limitations':['原ui-results.json complete=False是累积harness的局部分支标记；最终每方法按本run执行路径与矩阵逐项组合，不导入旧run passed。','新run未执行的API占位方法不在本fragment内，交API执行者负责。','未改产品、设计、tracked测试或run.json；无Git提交。'],'source_unchanged':subprocess.check_output(['git','status','--porcelain'],text=True).strip()==''}
(R/'ui-execution-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('methods',len(out));from collections import Counter;print(Counter(x['status'] for x in out.values()))
