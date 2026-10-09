import json,hashlib,platform,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];raw=json.load(open(R/'ui-results.json'));m={x['method_id']:dict(x) for x in raw['method_results'] if x['evidence']!=['evidence/ui/progress.json']};audit=R/'evidence/ui-stage10';prefix='evidence/ui-stage10/'
def merge(mid,status,actual,ev,complete=False):
 old=m.get(mid,{});status='failed' if status=='failed' or old.get('status')=='failed' else status if complete else old.get('status',status)
 m[mid]={'method_id':mid,'status':status,'actual':old.get('actual','')+'；'+actual,'evidence':sorted(set(old.get('evidence',[])+ev))}
for source in [R/'ui-races-results.json',audit/'ui-identity-results.json',audit/'ui-dialog-results.json']:
 d=json.load(open(source));base='' if source.parent==R else prefix
 for x in d.get('method_results',d.get('results',[])):
  for mid in [x['method_id']] if 'method_id' in x else x['method_ids']:merge(mid,x['status'],x['actual'],[base+e for e in x['evidence']],True)
for fname in ['pending-guard-results.json','extended-pending-results.json']:
 src=audit/fname if fname.startswith('pending-') else R/'evidence/ui-stage10-r2'/fname;base=str(src.parent.relative_to(R))+'/'
 d=json.load(open(src))
 for row in d['results']:
  mids=[row['method_id']] if 'method_id' in row else (['AI-WB-ui-self-demotion-session-failure'] if row['name'].startswith('pending-retry-') else ['AI-WB-ui-load-token-races'] if row['name'] in ['stale-token','same-token-user-absent'] else ['AI-WB-ui-role-demotion-reload'])
  for mid in mids:merge(mid,row['status'],'补充分项 '+row['name']+' '+row['status'],[base+row['evidence']])
d=json.load(open(audit/'change-role-identity-race-results.json'))
for x in d['results']:
 for mid in ['AI-WB-ui-role-demotion-reload','AI-WB-ui-load-token-races']:merge(mid,x['status'],'当前真实新登录会话未变，但旧changeRole身份200到达后UI回到旧身份：'+x['name'],[prefix+x['evidence']],True)
for f in ['same-identity-role-race.json','pending-load-role-commit-race.json']:
 d=json.load(open(audit/f))
 for mid in d['method_ids']:merge(mid,d['status'],'原始JS真实UI竞态：'+d['name']+'；后台member/管理403而UI回admin（详见逐断言和前后快照）。',[prefix+f]+[prefix+x for x in d['screenshots']],True)
for x in m.values():
 if x['status']=='unproven':x['actual']+='；本次已执行证据列出的实际UI路径，但原累积harness未证明当前方法全部状态矩阵；保持unproven等待独立逐定义审阅，不从其他方法通过推定。'
 for e in x['evidence']:assert (R/e).exists(),e
report={'revision':'708c9c057b5c9014f4ff975fdc5774093a687abe','environment':raw['environment'],'dependency_checks':[{'id':'ui-python-playwright-local-app','status':'passed','actual':'真实Chromium142.0.7444.0，Python3.12/macOS15.3.1；每组匿名127.0.0.1端口、独立合成SQLite；精确app源码，UI故障仅路由边界，真实401来自到期/撤销。','evidence':['ui-harness-execution.json','ui-results.json','evidence/ui-stage10/ui-identity-results.json']}],'method_results':list(m.values()),'execution_manifest':'ui-harness-execution.json','limitations':['此报告不含API所有者的AI-reservation-creation-11/12、AI-notification-center-6空占位。','未将complete=False的分支通过自动视为完整方法通过；当前明确失败不被任何正常恢复抵消。','所有real local app与frontend dependency fault在原始证据逐项标注；无第三方集成或Mock替代产品。'],'harness_attempts':[{'evidence':'evidence/ui-launch-sandbox-attempt/execution.json','reason':'sandbox Chromium launch SIGTRAP；升级执行后重跑完整序列'}, {'evidence':'evidence/ui-stage10/extended-pending-results.json','reason':'初始wait表达式违反CSP及barrier误拦新login session，原记录保留；r2完整17项重新执行'}, {'evidence':'evidence/ui/1601-native-filter-labels-and-orders.json','reason':'旧harness设备空项文字全部设备不存在，改为实际所有设备；1701完整路径重新执行通过'}]}
(R/'ui-execution-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
from collections import Counter
print(len(m),Counter(x['status'] for x in m.values()))
