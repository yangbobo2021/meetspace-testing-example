import json,hashlib,collections,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];L=R.parents[1]
run=json.loads((R/'run.json').read_text());sources=['independent-api-review.json','independent-ui-review.json','independent-runtime-review.json'];byid={};refs={}
for name in sources:
 d=json.loads((R/name).read_text());assert d['revision']==run['revision']
 for m in d['method_reviews']:
  byid.setdefault(m['method_id'],[]).append(dict(m,review_source=name))
 refs[name]={'sha256':hashlib.sha256((R/name).read_bytes()).hexdigest(),'review_reference':d.get('review_reference')}
# Join only complementary, independently inspected notification subparts.
subpath=R/'independent-api-notification-subpart-review.json'
sub=json.loads(subpath.read_text())
assert sub['revision']==run['revision']
ref='AI-WB-ui-notification-render'
part=byid[ref][0]
assert part['status']=='unproven' and part.get('independent_remaining_method_ids')
assert sub.get('status')=='passed' or sub.get('verdict')=='passed'
for mid in part['independent_remaining_method_ids']:
 assert any(x['status']=='passed' and x['review_source']=='independent-api-review.json' for x in byid[mid]),mid
part['status']='passed'
part['reason']+='；交叉证据份额已由另一审阅者独立核对通过：independent-api-notification-subpart-review.json；完整方法结论由两份互补独立审阅组成。'
refs[subpath.name]={'sha256':hashlib.sha256(subpath.read_bytes()).hexdigest(),'review_reference':sub.get('review_reference')}
results=[];missing=[]
for s in json.loads((L/'scenarios.json').read_text())['items']:
 mr=[]
 for mid in s['method_ids']:
  rows=byid.get(mid,[])
  if not rows:missing.append(mid);continue
  # Conservative join: any independent failed/unproven finding survives.
  r=next((x for state in ['failed','unproven'] for x in rows if x['status']==state),rows[0]);mr.append(r)
 rr=next(x for x in run['results'] if x['scenario_id']==s['id'])
 status=next((x for x in ['failed','unproven'] if any(m['status']==x for m in mr)),'passed')
 if rr['status']=='failed':status='failed'
 elif rr['status'] in ['blocked','unproven'] and status=='passed':status='unproven'
 evidence=sorted({p for m in mr for p in m['evidence'] if p in rr['evidence']})
 assert evidence,s['id']
 results.append({'scenario_id':s['id'],'status':status,'reason':'；'.join(m['method_id']+'：'+m['reason'] for m in mr),'evidence':evidence,'reviewed_method_ids':s['method_ids'],'independent_review_sources':sorted({m['review_source'] for m in mr})})
assert not missing,missing
unproven=[m['method_id'] for m in run['method_results'] if m['status'] in ['unproven','blocked']]
review={'revision':run['revision'],'reviewer_kind':'independent_ai','review_reference':'Cross-review: /root/ui_execution reviews API; /root/api_execution reviews UI/runtime; detailed references and inspected evidence hashes in independent-*-review.json. /root joins independent method verdicts without upgrading any failed execution.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_run_sha256':hashlib.sha256((R/'run.json').read_bytes()).hexdigest(),'independent_sources':refs,'coverage':{'status':'unproven' if unproven else 'passed','reason':'96需求/167场景/176方法固定定义已逐方法交叉审阅；当前源码和已绑定独立白盒设计适用性另见reviewer-harness-corrections.json。设计充分性不等于本轮证据完整，未证明方法如下。' if unproven else '全部固定方法已独立审阅；失败反例属于实现问题，未改场景或降低预期。','requirements_reviewed':[x['id'] for x in json.loads((L/'requirements.json').read_text())['items']],'white_box_basis':['app/server.py SHA256 '+hashlib.sha256(Path('app/server.py').read_bytes()).hexdigest(),'web/app.js SHA256 '+hashlib.sha256(Path('web/app.js').read_bytes()).hexdigest(),'Pinned coverage_review.json, white_box_review.json and white-box-map.json; independent current-source and raw evidence review in independent-api-review.json, independent-ui-review.json, independent-runtime-review.json.'],'uncovered_branches':unproven},'results':results,'summary':dict(collections.Counter(x['status'] for x in results)),'release_approved':False}
(R/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps(review['summary']))
