"""Merge execution records only. Never change pinned design/source definitions."""
import collections, datetime, hashlib, json, subprocess
from pathlib import Path
ROOT=Path.cwd(); L=ROOT/'tests/delivery-acceptance'; R=L/'runs/acceptance-20261008T-full-0b386b4-r1'
run=json.loads((R/'run.json').read_text()); revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert revision==run['revision']=='0b386b4bd37b01eb996c5e74215ab1a4463a9487'
assert not subprocess.check_output(['git','status','--porcelain'],text=True)
for name,expected in run['ledger_hashes'].items():assert hashlib.sha256((L/name).read_bytes()).hexdigest()==expected,name
sources=['runtime-results.json','api-results-r2.json','ui-results.json','ui-races-results.json','api-review-completion-results.json']
documents={name:json.loads((R/name).read_text()) for name in sources}
for name,doc in documents.items():assert doc['revision']==revision,name
definitions=json.loads((L/'methods.json').read_text())['items']; scenarios=json.loads((L/'scenarios.json').read_text())['items']
by_source={name:{m['method_id']:m for m in doc['method_results']} for name,doc in documents.items()}
merged=[]
for definition in definitions:
 mid=definition['id']
 # Shared notification count method's full 105/100/3 UI+HTTP matrix is in API;
 # copied placeholders in other fragments never replace its actual execution.
 order=['api-review-completion-results.json','ui-races-results.json','api-results-r2.json','runtime-results.json','ui-results.json']
 owner=next((name for name in order if mid in by_source[name]),None); assert owner,mid
 m=dict(by_source[owner][mid]);m['source_record']=owner;m['description']=definition['description'];m['kind']=definition['kind']
 m['environment']=m.get('environment',documents[owner].get('environment','详见本方法执行元数据及run.environment_details'))
 m['supplementary_records']=[{'source':name,**by_source[name][mid]} for name in order if name!=owner and mid in by_source[name]]
 if mid=='AI-notification-center-1':
  m['prior_execution_claim']=m['status'];m['status']='failed';m['actual']+=' 独立审阅发现其真实notification message缺月日和开始时间；root以无时钟适配器的Python3.12实际UI/HTTP复现，Python3.14对照不抵消此失败。';m['evidence']+=['evidence/notification-runtime-control/results.json','evidence/notification-runtime-control/python312-notification.png']
 if mid in ['AI-transaction-midwrite-boundary','AI-WB-transaction-failure-matrix','AI-application-runtime-9','AI-other-writes-failure-boundary'] and (R/'evidence/runtime-write-gaps/branches.json').exists():
  m['evidence']+=['evidence/runtime-write-gaps/branches.json','evidence/runtime-write-gaps/trace.json'];m['actual']+=' 追加首目标DML已返回且同连接读回、允许真实commit原样通过、第二类写前异常的独立8分支；含真进程重启、恢复重试，不以首写后故障代替写间隙。'
 for p in m['evidence']:assert (R/p).is_file(),(mid,p)
 merged.append(m)
mapping={m['method_id']:m for m in merged};results=[]
for scenario in scenarios:
 methods=[mapping[mid] for mid in scenario['method_ids']]
 status=next((s for s in ['failed','blocked','unproven'] if any(m['status']==s for m in methods)),'passed')
 results.append({'scenario_id':scenario['id'],'status':status,'method_ids':scenario['method_ids'],'actual':'；'.join(m['method_id']+'：'+m['actual'] for m in methods),'evidence':sorted({p for m in methods for p in m['evidence']}),'method_statuses':{m['method_id']:m['status'] for m in methods}})
findings=json.loads((R/'evidence/confirmed-findings.json').read_text())['findings']
for result in results:
 relevant=[f for f in findings if result['scenario_id'] in f['scenario_ids']]
 if relevant:
  result['method_aggregate_before_counterexamples']=result['status'];result['status']='failed';result['observed_counterexamples']=[f['id'] for f in relevant]
  result['actual']+='；同revision实测反例：'+'；'.join(f['actual'] for f in relevant)
  result['evidence']=sorted(set(result['evidence']+['evidence/confirmed-findings.json']+[p for f in relevant for p in f['evidence']]))
run['method_results']=merged;run['results']=results
run['cross_scenario_findings']=findings
run['environment']='macOS 15.3.1 arm64; main browser/API suites Python 3.12.4 (Anaconda) and Chromium 143.0.7499.4; resource preflight and comparison target Python 3.14.2; Node v25.5.0; isolated SQLite/localhost; Asia/Shanghai plus explicitly recorded browser/system timezone variants; actual versions and clock/fault controls per-method evidence'
run['execution_sources']=sources
run['execution_history']={'api':'api-results.json and evidence/api/ retain first execution; evidence/api-r2/execution-scope-and-corrections.json explains precise failure attribution and harness fixes','ui':'evidence/ui/ preserves each incremental complete path and harness synchronization corrections','ui_races':'ui-races-harness-attempt1/2/3-results.json and evidence/ui-races-harness-corrections.json retain all prior observations; no app implementation changed'}
run['integration_evidence']={'real_third_party':{'status':'not_applicable','reason':'资源清单及运行网络审计未发现第三方业务服务。'},'real_local_application':'各方法证据中的真实localhost HTTP、SQLite和UI路径。','frontend_network_simulation':'仅用于前端失败/等待展示，route.abort/fulfill状态注入有逐分支标记；真实响应暂存另有原始HTTP状态。','dependency_fault_injection':'固定datetime/time及SQLite依赖故障适配器不替换业务函数，具体位置与实际回滚在方法证据内；不等同于真实外部故障。'}
run['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
run['summary']={'scenarios':dict(collections.Counter(r['status'] for r in results)),'methods':dict(collections.Counter(m['status'] for m in merged)),'total_scenarios':len(results),'total_methods':len(merged),'acceptance':'pending_independent_review'}
run['verification']={'revision_unchanged':True,'tracked_worktree_unchanged':True,'ledger_hashes_unchanged':True,'spex_lint':{'status':'passed' if (R/'evidence/spex-lint-retry.log').is_file() and 'error' not in (R/'evidence/spex-lint-retry.log').read_text().lower() else 'unproven','evidence':['evidence/spex-lint.log','evidence/spex-lint-retry.log'],'scope':'规约结构检查不代表业务验收通过。'}}
(R/'run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(run['summary'],ensure_ascii=False))
