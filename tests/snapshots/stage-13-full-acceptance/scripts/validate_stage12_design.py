"""Read-only Analyst structure check; never approve independent coverage review."""
import ast,json,subprocess,sys
from pathlib import Path
R=Path.cwd();L=R/'tests/delivery-acceptance';O=L/'design-updates/stage12-source-reassessment-20261009'
sys.path.insert(0,'/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts')
import playbook as pb
changes=pb.read_json(O/'changes.json');S=pb.read_json(L/'scenarios.json');M=pb.read_json(L/'methods.json');W=pb.read_json(L/'white-box-map.json');A=pb.read_json(L/'design-assessment.json');errors=[]
def need(c,msg):
 if not c:errors.append(msg)
r=pb.unique_ids(pb.read_json(L/'requirements.json')['items'],'requirement',errors);s=pb.unique_ids(S['items'],'scenario',errors);m=pb.unique_ids(M['items'],'method',errors)
for x in s.values():
 need(bool(x['requirement_ids']) and set(x['requirement_ids'])<=r.keys(),x['id']+' requirements')
 need(bool(x['method_ids']) and set(x['method_ids'])<=m.keys(),x['id']+' methods')
 need(all(pb.filled(x.get(k)) for k in ['title','expected']),x['id']+' title/expected')
 if x['kind']=='white_box':need(pb.filled(x.get('target_condition')),x['id']+' condition')
for x in m.values():
 fields=['description','reference'] if x['kind']=='case' else ['description','preconditions','actions','evidence_expected']
 need(all(pb.filled(x.get(k)) for k in fields),x['id']+' method fields')
 expected={'scenarios.json#'+y['id']+'.expected' for y in s.values() if x['id'] in y['method_ids']}
 need(bool(expected) and set(x['expected_result_refs'])==expected,x['id']+' expected refs')
 for ref in x.get('supporting_case_refs',[]):
  path,symbol=ref.split('::');tree=ast.parse((R/path).read_text());cls,fun=symbol.split('.')
  need(any(isinstance(n,ast.ClassDef) and n.name==cls and any(isinstance(t,ast.FunctionDef) and t.name==fun for t in n.body) for n in tree.body),'supporting case missing '+ref)
 for c in x.get('matrix_checks',[]):need(all(pb.filled(c.get(k)) for k in ['key','preconditions','actions','expected','evidence_expected']),x['id']+' subcheck')
for rid in r:need(any(x['kind']=='black_box' and rid in x['requirement_ids'] for x in s.values()),rid+' missing black box')
for n in ['scenarios.json','methods.json']:
 need([x['id'] for x in pb.read_json(L/n)['items']]==[x['id'] for x in pb.read_json(O/'before'/n)['items']],n+' stable ids')
for n in ['requirements.json','coverage_review.json','white_box_review.json']:need(pb.digest(L/n)==changes['before_sha256'][n],n+' protected')
need(len(r)==96 and len(s)==167 and len(m)==176,'counts')
need({x['requirement_id'] for x in A['items']}==set(r) and len(A['items'])==96,'assessment coverage')
for x in A['items']:
 need(bool(x['basis']) and bool(x['operation_modes']) and bool(x['user_states']),x['requirement_id']+' assessment basis')
 for kind,field in [('black_box','black_box_scenario_ids'),('white_box','white_box_scenario_ids')]:
  need(set(x[field])=={y['id'] for y in s.values() if y['kind']==kind and x['requirement_id'] in y['requirement_ids']},x['requirement_id']+' reverse mapping')
mapped=set()
for t in W['targets']:
 for sid in t['scenario_ids']:
  need(sid in s and s[sid]['kind']=='white_box',t['id']+' target')
  need(set(t['requirement_ids'])<=set(s[sid]['requirement_ids']),t['id']+' requirement link');mapped.add(sid)
 for ref in t['source_refs']:need(pb.digest(R/ref['path'])==ref['source_sha256'] and ref['revision']==A['implementation_revision'],t['id']+' source binding')
need(mapped=={x['id'] for x in s.values() if x['kind']=='white_box'},'white box map')
checks=[c for x in m.values() for c in x.get('matrix_checks',[])];need(len(checks)==len({x['key'] for x in checks})==34,'native34 uniqueness')
need(not S['white_box_complete'],'white box awaits review')
need(not subprocess.check_output(['git','status','--porcelain'],text=True),'tracked changes')
need(subprocess.run(['git','check-ignore','-q',str(L/'scenarios.json')]).returncode==0,'not ignored')
black=pb.validate_black_box(R,test_dir=R/'tests');pb.write_json(O/'black-box-current-check.json',black)
result={'status':'passed' if not errors else 'blocked','scope':'Analyst traceability and structure only','counts':A['counts'],'matrix_checks':len(checks),'issues':errors,'independent_reviews_unchanged':True,'black_box_current_gate':black['status'],'independent_review_status':'pending; modified methods invalidate previous scoped hashes','white_box_complete':False,'execution':'not_performed','acceptance':'not_established'}
pb.write_json(O/'author-validation.json',result);print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
