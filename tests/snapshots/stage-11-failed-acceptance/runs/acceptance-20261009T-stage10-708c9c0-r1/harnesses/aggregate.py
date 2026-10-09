import json, hashlib, subprocess, collections, datetime
from pathlib import Path
ROOT=Path.cwd(); L=ROOT/'tests/delivery-acceptance';R=L/'runs/acceptance-20261009T-stage10-708c9c0-r1'
run=json.loads((R/'run.json').read_text()); base=json.loads((R/'evidence/revision-baseline.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==run['revision']==base['revision']
assert not subprocess.check_output(['git','status','--porcelain'],text=True)
for p,h in base['tracked_file_sha256'].items(): assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
for p,h in run['ledger_hashes'].items(): assert hashlib.sha256((L/p).read_bytes()).hexdigest()==h,p
sources=['api-execution-results.json','ui-execution-results.json','runtime-execution-results.json']
records={};envs={}
for s in sources:
 d=json.loads((R/s).read_text());assert d['revision']==run['revision'],s
 envs[s]=d.get('environment',d.get('environment_details','See fragment execution logs'))
 for m in d['method_results']:
  records.setdefault(m['method_id'],[]).append(dict(m,source_record=s))
defs=json.loads((L/'methods.json').read_text())['items'];methods=[]
for d in defs:
 mid=d['id'];rows=records.get(mid,[])
 if not rows: raise RuntimeError('Method not executed: '+mid)
 # A failed method is never replaced by another source's pass. Partial overlapping
 # probes cannot prove a method: designate complete claim only if there is one.
 failures=[x for x in rows if x['status']=='failed']
 proven=[x for x in rows if x['status']=='passed']
 selected=(failures or proven or rows)[0]
 m=dict(selected);m['description']=d['description'];m['kind']=d['kind'];m['observations']=rows
 m['evidence']=sorted({p for row in rows for p in row['evidence']})
 m['environment']=envs[selected['source_record']]
 for p in m['evidence']:assert (R/p).is_file(),(mid,p)
 methods.append(m)
byid={m['method_id']:m for m in methods};results=[]
for s in json.loads((L/'scenarios.json').read_text())['items']:
 rows=[byid[x] for x in s['method_ids']]
 st=next((x for x in ['failed','blocked','unproven'] if any(r['status']==x for r in rows)),'passed')
 results.append({'scenario_id':s['id'],'status':st,'method_ids':s['method_ids'],'method_statuses':{m['method_id']:m['status'] for m in rows},'actual':'；'.join(m['method_id']+'：'+m['actual'] for m in rows),'evidence':sorted({p for m in rows for p in m['evidence']})})
run.update(method_results=methods,results=results,execution_sources=sources,execution_environments=envs,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
run['verification']={'revision_unchanged':True,'tracked_file_hashes_unchanged':True,'tracked_worktree_clean':True,'ledger_hashes_unchanged':True,'evidence':'evidence/revision-baseline.json'}
run['summary']={'scenarios':dict(collections.Counter(x['status'] for x in results)),'methods':dict(collections.Counter(x['status'] for x in methods)),'total_scenarios':len(results),'total_methods':len(methods),'acceptance':'pending_independent_review'}
(R/'run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n');print(json.dumps(run['summary'],ensure_ascii=False))
