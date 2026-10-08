"""Restore completeness only after independently approved current scoped design."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];L=ROOT/'tests/delivery-acceptance';U=L/'design-updates/coverage-supplement-20261009'
read=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('check',L/'scripts/check_coverage_supplement_design.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
review=read(L/'white_box_review.json')
assert review['status']=='passed' and review['reviewer_kind']=='independent_ai'
assert review['scope_hashes']==checker.scope(),'Reviewer approval must match exact current design'
assert (L/'white_box_review.json').read_bytes()==(U/'independent-review.json').read_bytes()
pre=checker.check();assert pre['issues']==['white-box completeness pending independent review'],pre['issues']
scenario=read(L/'scenarios.json');scenario['white_box_complete']=True;write(L/'scenarios.json',scenario)
assert review['scope_hashes']==checker.scope(),'Completion metadata must not change reviewed scenario definitions'
report=checker.check();assert report['status']=='white_box_design_ready' and not report['issues']
write(L/'white-box-design-gate.json',report)
summary=read(U/'change-summary.json');summary['status']='independently_reviewed_design_ready'
summary['review_required']=False;summary['independent_review_reference']='design-updates/coverage-supplement-20261009/independent-review.json'
summary['design_gate_ref']='white-box-design-gate.json';summary['scope_hashes']=checker.scope()
write(U/'change-summary.json',summary);write(L/'white-box-design-summary.json',summary)
assessment=read(L/'design-assessment.json');assessment.update({'status':'complete_after_independent_revalidation',
      'white_box_complete':True,'independent_review_status':'passed','scope_hashes':checker.scope(),
      'independent_review_reference':summary['independent_review_reference'],
      'prior_acceptance':'incomplete; old run only corresponds to old definitions'})
write(L/'design-assessment.json',assessment)
write(L/'scenario-gate.json',{'stage':'coverage-supplement-design-only','status':'design_ready_execution_pending',
      'reason':'独立设计审阅与补充结构检查通过；新方法资源/故障适配器待验证，新定义尚未执行，不能复用旧run判通过',
      'counts':summary['counts'],'scope_hashes':checker.scope(),'execution_status':summary['execution_status'],
      'prior_acceptance':'incomplete','app_acceptance':'not_established'})
write(U/'final-design-gate.json',report)
print(json.dumps({'status':report['status'],'counts':summary['counts']},ensure_ascii=False))
