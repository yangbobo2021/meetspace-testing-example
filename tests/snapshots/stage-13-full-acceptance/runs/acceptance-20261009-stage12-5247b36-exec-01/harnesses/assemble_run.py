import collections, datetime, hashlib, json, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; L=R.parents[1]; ROOT=L.parents[1]
def read(p):return json.loads(p.read_text())
run=read(R/'run.json');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==run['revision'];assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip()
for k,v in run['ledger_hashes'].items():assert hashlib.sha256((L/k).read_bytes()).hexdigest()==v,k
sources=['api-execution-results.json','ui-execution-results.json','runtime-execution-results.json','root-supplement-results.json']
groups=collections.defaultdict(list)
for name in sources:
 doc=read(R/name);assert doc['revision']==run['revision'],name
 for m in doc['method_results']:
  record=dict(m);record['source_record']=name;record.setdefault('environment',doc.get('environment',{'reference':name}));groups[m['method_id']].append(record)
supps={m['method_id']:m for m in read(R/'runtime-api-supplement.json')['method_supplements']}
defs=read(L/'methods.json')['items'];assert set(groups)=={m['id'] for m in defs}, {'missing':list({m['id'] for m in defs}-set(groups)),'unknown':list(set(groups)-{m['id'] for m in defs})}
merged=[]
for definition in defs:
 mid=definition['id'];records=groups[mid];states=[m['status'] for m in records];evidence={p for m in records for p in m['evidence']};actual='；'.join(m['source_record']+'：'+m['actual'] for m in records);closure=None
 if mid in supps:
  s=supps[mid];evidence.update(s['evidence']);evidence.add('runtime-api-supplement.json');states.append(s['status']);actual+='；本轮扩展矩阵：'+s['scope']+'，详见逐项原始观察。'
  if mid in ['AI-WB-idempotency-absolute-precision','AI-WB-booking-insert-notify'] and s['status']=='passed' and all(m['status']=='passed' or (m['source_record']=='api-execution-results.json' and m['status']=='unproven') for m in records):
   states=[x for x in states if x!='unproven'];closure={'kind':'completed_missing_scope_in_same_run','partial_source':'api-execution-results.json','new_evidence':s['evidence'],'reason':'首片段明确未执行的扩展范围已在本轮相同修订真实补执行；原partial未证明记录原样保留。没有失败被其他路径抵消。'}
 if mid=='AI-reservation-creation-7':
  evidence.update(supps['AI-WB-idempotency-absolute-precision']['evidence']);actual+='；同一精度方法的synthetic历史canonical兼容3状态66断言亦本轮实测。'
 status=next((s for s in ['failed','blocked','unproven'] if s in states),'passed')
 assert records and any(not m.get('supplement_only') for m in records),mid
 for p in evidence:assert (R/p).is_file(),(mid,p)
 result={'method_id':mid,'kind':definition['kind'],'description':definition['description'],'status':status,'actual':actual,'evidence':sorted(evidence),'environment':[m['environment'] for m in records],'execution_records':records}
 if closure:result['scope_completion']=closure
 merged.append(result)
byid={m['method_id']:m for m in merged};scenarios=[]
for s in read(L/'scenarios.json')['items']:
 methods=[byid[mid] for mid in s['method_ids']];states=[m['status'] for m in methods];status=next((v for v in ['failed','blocked','unproven'] if v in states),'passed')
 scenarios.append({'scenario_id':s['id'],'status':status,'method_ids':s['method_ids'],'actual':'；'.join(m['method_id']+'：'+m['actual'] for m in methods),'evidence':sorted({p for m in methods for p in m['evidence']}),'method_statuses':{m['method_id']:m['status'] for m in methods}})
run.update(method_results=merged,results=scenarios,execution_state='executed_pending_independent_review',execution_sources=sources+['runtime-api-supplement.json'],updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),summary={'total_scenarios':len(scenarios),'total_methods':len(merged),'scenarios':dict(collections.Counter(x['status'] for x in scenarios)),'methods':dict(collections.Counter(x['status'] for x in merged)),'acceptance':'pending_independent_review'})
run['verification'].update(revision_unchanged=True,tracked_worktree_unchanged=True,ledger_hashes_unchanged=True)
(R/'run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n');print(json.dumps(run['summary'],ensure_ascii=False))
