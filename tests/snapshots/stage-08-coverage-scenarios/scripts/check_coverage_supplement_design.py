"""Design-only gate: check current supplement and independent review, never run App."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
L=ROOT/'tests/delivery-acceptance'
U=L/'design-updates/coverage-supplement-20261009'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def scope():
    sc=read(L/'scenarios.json')['items'];ms=read(L/'methods.json')['items'];white=[s for s in sc if s['kind']=='white_box']
    linked={m for s in white for m in s['method_ids']}
    return {'requirements_sha256':sha(L/'requirements.json'),
            'white_box_scenarios_sha256':canonical(white),'white_box_methods_sha256':canonical([m for m in ms if m['id'] in linked]),
            'white_box_map_sha256':sha(L/'white-box-map.json'),'context_sha256':sha(L/'white-box-context.json'),
            'independent_inventory_sha256':sha(L/'review-history/white-box-independent-inventory.json'),
            'baseline_binding_sha256':sha(U/'baseline-binding.json'),
            'supplement_changes_sha256':canonical(read(U/'change-summary.json')['changes']),
            'defensive_reachability_sha256':sha(U/'defensive-reachability.json')}

def check():
    issues=[]
    def need(ok,message):
        if not ok:issues.append(message)
    binding=read(U/'baseline-binding.json');before=U/'baseline';context=read(L/'white-box-context.json')
    for f,h in binding['source_sha256'].items():need(sha(ROOT/f)==h,'source changed: '+f)
    for f,h in binding['baseline_sha256'].items():need(sha(before/f)==h,'baseline modified: '+f)
    for f,h in binding['original_acceptance_sha256'].items():need(sha(L/'runs/acceptance-20261008T-full-0b386b4-r1'/f)==h,'old acceptance modified: '+f)
    need(sha(L/'requirements.json')==sha(before/'requirements.json'),'confirmed requirement snapshot modified')
    need(sha(L/'coverage_review.json')==sha(before/'coverage_review.json'),'independent black-box review changed')
    need(context['implementation_revision']==binding['revision'],'context revision mismatch')
    need(context['execution_status']=='not_started_for_updated_design','new design incorrectly claims execution')
    scenario_document=read(L/'scenarios.json');need(scenario_document.get('white_box_complete') is True,'white-box completeness pending independent review')
    scenarios=scenario_document['items'];methods=read(L/'methods.json')['items'];mapping=read(L/'white-box-map.json')
    sm={x['id']:x for x in scenarios};mm={x['id']:x for x in methods};white={x['id']:x for x in scenarios if x['kind']=='white_box'}
    reqids={x['id'] for x in read(L/'requirements.json')['items']}
    need(len(sm)==len(scenarios),'duplicate scenarios');need(len(mm)==len(methods),'duplicate methods')
    changes=read(U/'change-summary.json')['changes'];added={c['scenario_id'] for c in changes if c['change']=='added'}
    refined={c['scenario_id'] for c in changes if c['change']=='refined'}
    changed_ms={c['method_id'] for c in changes}
    olds=read(before/'scenarios.json')['items'];oldm=read(before/'methods.json')['items']
    need(set(sm)=={s['id'] for s in olds}|added,'incorrect retained/new scenario IDs')
    need(len(added)==8 and len(refined)==2,'expected 8 new and 2 refined scenarios')
    for s in olds:
        current=sm.get(s['id'])
        if s['id'] not in refined:need(current==s,'unexpected existing scenario change: '+s['id'])
        else:
            need(all(current.get(k)==s[k] for k in ['id','kind','title','requirement_ids','method_ids']),'refined scenario changed identity/links: '+s['id'])
            need(current.get('expected','').startswith(s['expected']),'old expected removed: '+s['id'])
    for m in oldm:
        if m['id'] not in changed_ms:need(mm.get(m['id'])==m,'old method modified: '+m['id'])
        else:
            need(all(mm[m['id']][k].startswith(m[k]) for k in ['description','preconditions','actions','evidence_expected']),'old method matrix removed: '+m['id'])
    need(len(scenarios)==167 and len(white)==71 and len(methods)==176,'wrong scene/method counts')
    for s in scenarios:
        need(all(isinstance(s.get(k),str) and s[k].strip() for k in ['title','expected']),s['id']+' missing prose')
        need(bool(s['requirement_ids']) and set(s['requirement_ids'])<=reqids,s['id']+' invalid requirements')
        need(bool(s['method_ids']) and set(s['method_ids'])<=set(mm),s['id']+' invalid methods')
        if s['kind']=='white_box':need(bool(s.get('target_condition')),s['id']+' missing target')
    for m in methods:
        required=['reference'] if m['kind']=='case' else ['preconditions','actions','evidence_expected']
        need(bool(m.get('description')) and all(bool(m.get(k)) for k in required),m['id']+' incomplete method')
    targets=mapping['targets'];tm={x['id']:x for x in targets};mapped=set()
    need(len(tm)==len(targets)==71,'target mapping wrong/duplicate')
    for t in targets:
        need(bool(t.get('risk')) and bool(t.get('description')),t['id']+' incomplete target')
        need(set(t['scenario_ids'])<=set(white) and bool(t['scenario_ids']),t['id']+' invalid white scenario')
        mapped.update(t['scenario_ids'])
        linkedreq={r for sid in t['scenario_ids'] if sid in white for r in white[sid]['requirement_ids']}
        need(set(t['requirement_ids'])<=linkedreq,t['id']+' requirement map mismatch')
        for ref in t['source_refs']:
            p=ROOT/ref['path'];count=len(p.read_text().splitlines())
            need(ref['path'] in binding['source_sha256'] and 1<=ref['line_start']<=ref['line_end']<=count and bool(ref.get('symbol')),t['id']+' invalid source refs')
    need(mapped==set(white),'unmapped white scenario')
    assessed=mapping['requirement_assessment'];need({a['requirement_id'] for a in assessed}==reqids and len(assessed)==96,'requirement assessment missing')
    for a in assessed:
        expected={s['id'] for s in white.values() if a['requirement_id'] in s['requirement_ids']}
        need(set(a['white_box_scenario_ids'])==expected,a['requirement_id']+' stale reverse white links')
    need({c['gap_id'] for c in changes}=={f'COV-GAP-{n:03}' for n in range(1,9)},'audit gap omitted')
    defenses=read(U/'defensive-reachability.json')['items'];need(len(defenses)==5,'defensive inventory missing')
    for d in defenses:
        need(all(d.get(k) for k in ['id','static_basis','reachability','disposition','optional_probe']),d['id']+' incomplete defensive basis')
        need(d['execution_status']=='not_executed',d['id']+' incorrectly claims execution')
        need(set(d['related_scenario_ids'])<=set(sm),d['id']+' invalid linked scenario')
    skill=Path('/Users/boboyang/.codex/skills/app-delivery-acceptance')
    spec=importlib.util.spec_from_file_location('pb',skill/'scripts/playbook.py');pb=importlib.util.module_from_spec(spec);spec.loader.exec_module(pb)
    current_hashes=pb.coverage_scope_hashes(L);cr=read(L/'coverage_review.json')
    need(all(cr.get(k)==v for k,v in current_hashes.items()),'black-box independent scope stale')
    review=read(L/'white_box_review.json')
    need(review.get('status')=='passed' and review.get('reviewer_kind')=='independent_ai','independent white-box review not passed')
    need(review.get('implementation_revision')==binding['revision'] and review.get('scope_hashes')==scope(),'independent white-box review stale')
    need(bool(review.get('review_reference')) and bool(review.get('basis')),'missing independent identity/basis')
    need(set(review.get('requirements_reviewed',[]))==reqids,'independent review omits requirement')
    items=review.get('items',[]);need(len(items)==len(white) and {i['scenario_id'] for i in items}==set(white),'review omits scenario')
    for i in items:need(i.get('verdict')=='sufficient' and all(i.get(k) for k in ['reason','plausible_fault','failure_signal']),i['scenario_id']+' insufficient review')
    branches=review.get('branch_reviews',[]);need(len(branches)==len(targets) and {i['target_id'] for i in branches}==set(tm),'review omits target')
    for i in branches:need(i.get('verdict')=='sufficient' and bool(i.get('reason')) and set(i.get('scenario_ids',[]))<=set(tm[i['target_id']]['scenario_ids']),i['target_id']+' insufficient target review')
    gaps=review.get('supplement_gap_reviews',[]);need(len(gaps)==8 and {i['gap_id'] for i in gaps}=={f'COV-GAP-{n:03}' for n in range(1,9)},'missing supplement review')
    for i in gaps:need(i.get('verdict')=='sufficient' and bool(i.get('reason')) and bool(i.get('scenario_ids')) and set(i['scenario_ids'])<=set(white),i['gap_id']+' insufficient gap review')
    dr=review.get('defensive_path_reviews',[]);need(len(dr)==5 and {d['id'] for d in dr}=={d['id'] for d in defenses},'missing defensive path review')
    for i in dr:need(i.get('verdict') in ('excluded','sufficient') and bool(i.get('reason')),i['id']+' invalid defensive review')
    need(review.get('uncovered_branches')==[],'important design branches unresolved')
    return {'stage':'coverage-supplement-design-only','checker':'supplementary scoped design checker; not compiled app acceptance',
            'status':'white_box_design_ready' if not issues else 'blocked','issues':issues,'scope_hashes':scope(),
            'implementation_revision':binding['revision'],
            'counts':{'requirements':96,'black_box_scenarios':96,'white_box_scenarios':len(white),'total_scenarios':len(scenarios),'methods':len(methods),'added_scenarios':len(added),'refined_scenarios':len(refined)},
            'execution_status':'not_started_for_updated_design','prior_acceptance':'incomplete','app_acceptance':'not_established'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--hashes',action='store_true');parser.add_argument('--save',action='store_true');args=parser.parse_args()
    report=scope() if args.hashes else check()
    if args.save:(L/'white-box-design-gate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if args.hashes or report['status']=='white_box_design_ready' else 1)
