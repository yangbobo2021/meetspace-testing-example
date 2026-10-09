"""Synchronize completion metadata from existing independent evidence, never self-review."""
import datetime,hashlib,json,shutil,subprocess,sys
from pathlib import Path
R=Path.cwd();L=R/'tests/delivery-acceptance'
sys.path.insert(0,'/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts')
import playbook as pb
pb.verify_project_binding(L,R)
r=pb.read_json(L/'coverage_review.json');w=pb.read_json(L/'white_box_review.json');s=pb.read_json(L/'scenarios.json');a=pb.read_json(L/'design-assessment.json');d=pb.read_json(L/'white-box-design-summary.json');mapping=pb.read_json(L/'white-box-map.json')
ref=r['review_reference'];summary=pb.read_json(L/ref)
rev=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert r['status']==w['status']==summary['status']=='passed'
assert r['reviewer_kind']==w['reviewer_kind']=='independent_ai'
assert ref==w['review_reference']
assert rev==w['implementation_revision']==r['code_review']['revision']==summary['revision']
assert r['code_review']['code_sha256']==w['code_sha256']
for p,h in w['code_sha256'].items():assert pb.digest(R/p)==h
# Latest signed review-summary binds all current definitions; an older copied field in
# coverage_review remains untouched and is explicitly identified below as historical.
for p,h in summary['analyst_assets_sha256'].items():assert pb.digest(L/p)==h
scope=pb.coverage_scope_hashes(L)
assert all(r[k]==v and w['scope_hashes'][k]==v for k,v in scope.items())
reqids={x['id'] for x in pb.read_json(L/'requirements.json')['items']}
assert len(reqids)==len(r['items'])==96
assert {x['requirement_id'] for x in r['items']}==reqids==set(w['requirements_reviewed'])
assert all(x['verdict']=='sufficient' and x['uncovered_paths']==[] for x in r['items'])
assert w['uncovered_branches']==r['code_review']['uncovered_branches']==[]
assert w['items']==r['code_review']['white_box_items']
wb={x['id']:x for x in s['items'] if x['kind']=='white_box'};targets={x['id']:x for x in mapping['targets']}
assert len(w['items'])==len(wb)==len(targets)==71
assert {x['scenario_id'] for x in w['items']}==set(wb)
for x in w['items']:
 t=targets[x['target_id']]
 assert x['verdict']=='sufficient' and all(x[k] for k in ['reason','plausible_fault','failure_signal'])
 assert x['target_condition']==t['description'] and x['source_refs']==t['source_refs']
 assert x['scenario_id'] in t['scenario_ids'] and set(x['requirement_ids'])==set(t['requirement_ids'])
prior=pb.read_json(L/'scenario-gate.json')
assert [(k,v['issues']) for k,v in prior['gates'].items() if v['status']!='passed']==[('scenarios',['white-box scenario review is incomplete'])]
assert s['white_box_complete'] is False
O=L/'design-updates/stage12-completeness-reconciliation';O.mkdir();(O/'before').mkdir()
names=['scenarios.json','design-assessment.json','white-box-design-summary.json','repair-summary.json','scenario-gate.json','coverage_review.json','white_box_review.json']
for n in names:shutil.copyfile(L/n,O/'before'/n)
protected={n:pb.digest(L/n) for n in ['requirements.json','methods.json','coverage_review.json','white_box_review.json','white-box-map.json','white-box-context.json','resources.json']}
items_before=json.dumps(s['items'],ensure_ascii=False,sort_keys=True)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
binding={'review_reference':ref,'review_summary_sha256':pb.digest(L/ref),'coverage_review_sha256':protected['coverage_review.json'],'white_box_review_sha256':protected['white_box_review.json'],'reviewed_at':r['reviewed_at'],'revision':rev,'scope_hashes':scope,'reviewed_asset_sha256':summary['analyst_assets_sha256'],'actual_fault_probes':sum(len(x['fault_probes']) for x in r['items']),'metadata_notes':['coverage_review.summary.fault_probes仍为207，逐项实际为209，与最新review-summary一致；不改独立审阅原文件。','coverage_review.analyst_assets_unchanged_sha256是旧阶段遗留字段；本次以最新review_reference中的完整资产SHA及当前scope_hashes双重核验，均匹配。']}
basis='最新独立r2审阅明确96需求充分、71白盒目标充分、209实际反事实探针及40时序子项，旧角色session缺口已关闭；当前定义完整SHA、作用域SHA及源码修订/SHA匹配。唯一门禁阻塞是white_box_complete=false，本次仅同步完成元数据，不改场景条目、方法或独立审阅。'
s['white_box_complete']=True;pb.write_json(L/'scenarios.json',s)
a.update(status='complete_after_independent_revalidation',white_box_complete=True,independent_review_status='passed_existing_independent_r2_records',assessed_at=now,review_binding=binding,independent_review_refs=['coverage_review.json','white_box_review.json',ref])
a.pop('white_box_gate_pending_reason',None)
a['basis']=[basis]
a['limitations']=['设计充分不等于应用通过；必须针对当前HEAD新运行167场景，独立取证。','原34项原生脚本尚不包含新增6项；执行时须原生AI操作或ignored目录专用harness，不复用旧passed。','完整视口、时钟/熵/并发/存储故障设施须使用前验证；5防御出口保留覆盖分母。','原审阅缺口和blocked门禁已归档，本次独立审阅原文件保持字节不变。']
for row in a['items']:
 row['assessment']='complete_after_independent_revalidation';row['independent_review_ref']='coverage_review.json#'+row['requirement_id']
 if 'independent_review_outcome' in row:row['independent_review_outcome']='独立r2已判充分；原gap保留历史，未证明执行通过。'
 for f in row.get('repair_findings',[]):f['status']='resolved_in_design_by_independent_review';f['independent_review_ref']=ref
for f in a.get('repair_findings',[]):f['status']='resolved_in_design_by_independent_review';f['independent_review_ref']=ref
pb.write_json(L/'design-assessment.json',a)
d.update(status='independently_reviewed_design_ready',review_required=False,independent_review_reference='white_box_review.json',black_box_complete=True,white_box_complete=True,completion_reconciliation_basis=basis,review_binding=binding);pb.write_json(L/'white-box-design-summary.json',d)
report={'status':'completion_metadata_reconciled','basis':basis,'review_binding':binding,'before_ref':str((O/'before').relative_to(L)),'counts':a['counts'],'scenario_content_changes':0,'method_changes':0,'white_box_complete_change':{'before':False,'after':True},'independent_reviews_unchanged':True,'execution_performed':False,'release_approved':False,'protected_sha256':protected}
pb.write_json(O/'reconciliation.json',report)
pb.write_json(L/'repair-summary.json',{'status':'design_ready_after_independent_review','details_ref':str((O/'reconciliation.json').relative_to(L)),'previous_repair_ref':'design-updates/stage12-role-session-pending-repair/repair-summary.json','counts':a['counts'],'execution':'not_performed','release_approved':False})
assert json.dumps(pb.read_json(L/'scenarios.json')['items'],ensure_ascii=False,sort_keys=True)==items_before
assert all(pb.digest(L/n)==h for n,h in protected.items())
assert pb.coverage_scope_hashes(L)==scope
print(json.dumps({'status':report['status'],'counts':a['counts'],'scenario_content_changes':0,'independent_reviews_unchanged':True},ensure_ascii=False))
