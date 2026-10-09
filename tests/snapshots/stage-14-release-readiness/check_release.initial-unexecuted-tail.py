from pathlib import Path
import json,hashlib,subprocess,collections,copy
P=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking');B=P/'tests/delivery-acceptance';O=B/'release-preparation/20261009/release-readiness-review';S=P/'tests/snapshots/stage-13-full-acceptance';R=B/'runs/acceptance-20261009-stage12-5247b36-exec-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=lambda p:json.loads(p.read_text())
git=lambda *a:subprocess.check_output(['git',*a],cwd=P)
checks=[]
def check(name,ok,details):checks.append(dict(check=name,passed=bool(ok),details=details))
head=git('rev-parse','HEAD').decode().strip();tested='5247b360276f2900d20fdeab96bd75bb3ece73fa';ctx=j(B/'current-release-context.json')
source=[]
for f,h in ctx['source_sha256'].items():
 vals={'working':sha(P/f),'head':hashlib.sha256(git('show',head+':'+f)).hexdigest(),'tested':hashlib.sha256(git('show',tested+':'+f)).hexdigest(),'declared':h};source.append(dict(path=f,hashes=vals));check('source:'+f,len(set(vals.values()))==1,vals)
check('archive_head',head=='6e525eaf3d1e98e201dc9b9776f8885a29f17aeb',head)
check('git_clean',not git('status','--porcelain').strip(),git('status','--porcelain').decode())
changed=git('diff','--name-only',tested,head).decode().splitlines();check('archive_commit_scope',all(x.startswith('tests/snapshots/stage-13-full-acceptance/') or x in ['AGENTS.md','README.md','specs/map.md','specs/decisions/013-identity-continuation-fix.md','specs/decisions/014-complete-fixed-release-acceptance.md','tests/delivery-acceptance/scripts/archive_release_process.py'] for x in changed),dict(file_count=len(changed),non_snapshot=[x for x in changed if not x.startswith('tests/snapshots/stage-13-full-acceptance/')]))
run=j(R/'run.json');rev=j(R/'review.json');gate=j(R/'gate-report.json');term=j(B/'release-preparation/20261009/stage12-workflow-terminal-evidence.json');protected=j(R/'review-revalidation/protected-inputs-final.json')
for f,h in protected['hashes'].items():check('protected:'+f,sha(P/f)==h,dict(declared=h,actual=sha(P/f)))
for f,h in run['ledger_hashes'].items():check('ledger:'+f,sha(B/f)==h,dict(declared=h,actual=sha(B/f)))
for name,idkey,count in [('requirements.json','id',96),('scenarios.json','id',167),('methods.json','id',176)]:
 d=j(B/name)['items'];ids=[x[idkey] for x in d]; old=j(P/'tests/snapshots/stage-09-supplemental-coverage-cycle'/name)['items'];check('stable_ids:'+name,len(ids)==count and len(set(ids))==count and set(ids)=={x['id'] for x in old},dict(count=len(ids),baseline_count=len(old),unique=len(set(ids))))
check('requirements_confirmed',ctx['requirements_sha256']==sha(B/'requirements.json') and j(B/'requirements.json')['confirmation']['status']=='confirmed',sha(B/'requirements.json'))
sc=j(B/'scenarios.json')['items'];ms=j(B/'methods.json')['items'];reqids={x['id'] for x in j(B/'requirements.json')['items']};scids={x['id'] for x in sc};mids={x['id'] for x in ms}
check('scenario_references',all(set(x['requirement_ids'])<=reqids and set(x['method_ids'])<=mids for x in sc),dict(kinds=dict(collections.Counter(x['kind'] for x in sc))))
for label,rows,key,ids in [('scenario_execution',run['results'],'scenario_id',scids),('method_execution',run['method_results'],'method_id',mids),('scenario_review',rev['results'],'scenario_id',scids),('method_review',j(R/'independent-method-review.json')['results'],'method_id',mids)]:
 counts=dict(collections.Counter(x['status'] for x in rows));check(label,len(rows)==len(ids) and {x[key] for x in rows}==ids and all(x['status']=='passed' for x in rows),dict(counts=counts,rows=len(rows)))
check('five_gates',gate['status']=='passed' and set(gate['gates'])=={'requirements','resources','scenarios','execution','review'} and all(x['status']=='passed' and not x['issues'] for x in gate['gates'].values()),gate['gates'])
check('terminal_run_review_gate_binding',term['run_sha256']==sha(R/'run.json') and term['review_sha256']==sha(R/'review.json') and term['gate_sha256']==sha(R/'gate-report.json') and run['revision']==rev['revision']==tested and run['execution_state']=='completed',dict(run=sha(R/'run.json'),review=sha(R/'review.json'),gate=sha(R/'gate-report.json')))
raw=Path('/Users/boboyang/.spex/sessions/cb18568a-7ebc-41fb-a307-e8c7038394e4.records.jsonl');records=[json.loads(x) for x in raw.read_text().splitlines()];last=records[-1]['record'];replies=[x['record'] for x in records if x['record'].get('type')=='captain_reply' and x['record'].get('turnId')==3]
check('captain_actual_terminal',sha(raw)==term['raw_records_sha256'] and len(records)==term['record_count']==945 and last['type']=='turn_finished' and last['turnId']==3 and replies[-1]['text']==term['terminal_reply'] and term['status']=='full_acceptance_passed',dict(raw_sha=sha(raw),record_count=len(records),last=last,reply=replies[-1]['text']))
refs=sorted({x for rows in [run['results'],run['method_results'],rev['results']] for row in rows for x in row.get('evidence',[])})
check('all_direct_evidence_exists',all((R/x).is_file() for x in refs),dict(count=len(refs),missing=[x for x in refs if not (R/x).is_file()]))
for manifestname,key in [('evidence/execution-evidence-manifest.json','evidence_files'),('review-revalidation/file-audit.json','files')]:
 d=j(R/manifestname);fs=d[key];bad=[x['path'] for x in fs if not (R/x['path']).is_file() or sha(R/x['path'])!=x['sha256'] or (R/x['path']).stat().st_size!=x['bytes']];check('actual_evidence_hashes:'+manifestname,not bad,dict(count=len(fs),bad=bad))
# Saved-observation recalculation only. Redirect its sole output into this independent folder.
p=R/'review-revalidation/recompute.py';text=p.read_text();original="(R/'review-revalidation/recomputed-observations.json').write_text";assert text.count(original)==1
text=text.replace(original,"(Path("+repr(str(O/'recomputed-observations.json'))+")).write_text")
exec(compile(text,str(p),'exec'),{'__file__':str(p)})
rr=j(O/'recomputed-observations.json');check('saved_observations_independently_recomputed',rr['counts']=={'passed':708} and rr==j(R/'review-revalidation/recomputed-observations.json'),dict(counts=rr['counts'],script_sha=sha(p),output_sha=sha(O/'recomputed-observations.json')))
# All public archived bytes, then comparison with local source except explicitly declared redactions.
man=j(S/'manifest.json');ass=j(S/'process-assessment.json');pathmap=j(S/'evidence-path-map.json');red={x['path']:x for x in ass['public_redactions']};bad=[];mismatch=[]
for f,v in man['files'].items():
 q=S/f
 if not q.is_file() or sha(q)!=v['sha256'] or q.stat().st_size!=v['bytes']:bad.append(f)
 originalfile=B/f
 if originalfile.is_file() and f not in red and sha(originalfile)!=sha(q):mismatch.append(f)
check('archive_manifest_3319',len(man['files'])==3319 and not bad,dict(count=len(man['files']),bad=bad,manifest_sha=sha(S/'manifest.json')))
check('archive_matches_original_nonredacted',not mismatch,dict(mismatches=mismatch))
check('absolute_archive_path_map',all(Path(a).is_file() and b in man['files'] and (S/b).is_file() for a,b in pathmap.items()),dict(mapped=len(pathmap)))
def diffs(a,b,loc=''):
 if type(a)!=type(b):return [loc]
 if isinstance(a,dict):
  if set(a)!=set(b):return [loc]
  return [z for k in a for z in diffs(a[k],b[k],loc+'/'+str(k).replace('~','~0').replace('/','~1'))]
 if isinstance(a,list):
  if len(a)!=len(b):return [loc]
  return [z for i,(x,y) in enumerate(zip(a,b)) for z in diffs(x,y,loc+'/'+str(i))]
 return [] if a==b else [loc]
redout=[]
for f,v in red.items():
 paths=diffs(j(B/f),j(S/f));ok=sha(B/f)==v['original_sha256'] and sha(S/f)==v['archived_sha256'] and paths==['/files/app~1server.py/functions/password_hash'] and v['fields']==['/files/app/server.py/functions/password_hash'];redout.append(dict(path=f,passed=ok,changed_paths=paths,original_sha=sha(B/f),archive_sha=sha(S/f)))
check('six_redaction_original_archive_mappings',len(redout)==6 and all(x['passed'] for x in redout),redout)
check('database_private_exclusion',not any(f.endswith(('.sqlite','.db','.sqlite3','.coverage')) or '/private-baseline/' in f or '/node_modules/' in f for f in man['files']),dict(exclusion_count=len(ass['publication_exclusions'])))
# All historical files/manifests unchanged from tested commit, plus each manifest's own byte hashes.
history=[]
for p in sorted((P/'tests/snapshots').glob('*/manifest.json')):
 if p.parent==S:continue
 d=j(p);fs=d.get('files',{});bad=[]
 for f,v in fs.items():
  h=v['sha256'] if isinstance(v,dict) else v;q=p.parent/f
  if not q.is_file() or sha(q)!=h:bad.append(f)
 histpath=str(p.parent.relative_to(P));unchanged=not git('diff','--name-only',tested,head,'--',histpath).strip();history.append(dict(stage=p.parent.name,manifest_sha=sha(p),files=len(fs),bad=bad,unchanged=unchanged))
check('historical_snapshots_preserved',all(not x['bad'] and x['unchanged'] for x in history),history)
tags={t:git('rev-parse',t+'^{commit}').decode().strip() for t in git('tag','--list','stage-*').decode().splitlines()};check('stage_tags',tags['stage-12-identity-fixes']==tested and tags['stage-13-full-acceptance']==head, tags)
# The six formal pending cases independently recalculate source return and continuation invariants.
rows=[]
for p in sorted((R/'evidence/pending-six').glob('old-*.json')):
 d=j(p);a=d['checks'][1]['actual'];z=d['checks'][2]['actual'];tok=a['old_guard_locals'];ok=all(c.get('passed',c.get('status')=='passed') for c in d['checks']) and a['before']==a['after'] and a['database_before']==a['database_after'] and a['events_after_release']==[] and tok['old']<tok['current'] and tok['identity']==tok['currentIdentity'] and tok['pending'] and a['completion_function']!='changeRole' and a['members_status']==403 and a['session']['user']['role']=='member' and not z['after']['identityPending'] and not z['after']['manage'] and z['session_requests']==3
 rows.append(dict(case=p.name,passed=ok,sha=sha(p),tokens=tok,guard=a['guard_location'],completion=a['completion_location']))
check('formal_six_pending_continuation',len(rows)==6 and all(x['passed'] for x in rows),rows)
# Previously performed independent source and export facility reviews are read again and hash protected.
for name,h,status in [('stage12-coverage-followup-review/final-six-collector-review.json','cab69a3205e8c818a614bc9809750f50b2b119cf9e9b7704e193086f343ef140','additional_six_collector_and_same_revision_coverage_verified'),('facility-review-confirmed-unmap/fixed-product-resource-final-review.json','9fcc8e683ca6b8be9568973db5e90e60e1efb5e83ca99c77cc10e527351c5ac6','ready_for_formal_resource_binding_in_fixed_product_scope')]:
 p=B/'release-preparation/20261009'/name;d=j(p);check('independent_prior_review:'+name,sha(p)==h and d['status']==status,dict(sha=sha(p),status=d['status']))
(O/'checks.json').write_text(json.dumps(dict(acceptedArchiveRevision=head,testedSourceRevision=tested,source=source,checks=checks,summary=dict(collections.Counter('passed' if x['passed'] else 'failed' for x in checks))),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(checks=len(checks),failed=[x['check'] for x in checks if not x['passed']]),ensure_ascii=False))
