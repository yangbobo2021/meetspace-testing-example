#!/usr/bin/env python3
"""Supplementary design-only check; does not execute the App or certify acceptance."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def scope(assets):
    white = [s for s in read(assets/'scenarios.json')['items'] if s['kind']=='white_box']
    methods = read(assets/'methods.json')['items']
    linked = {i for s in white for i in s['method_ids']}
    return {'requirements_sha256':digest(assets/'requirements.json'),
            'white_box_scenarios_sha256':canonical(white),
            'white_box_methods_sha256':canonical([m for m in methods if m['id'] in linked]),
            'white_box_map_sha256':digest(assets/'white-box-map.json'),
            'context_sha256':digest(assets/'white-box-context.json'),
            'independent_inventory_sha256':digest(assets/'review-history/white-box-independent-inventory.json')}


def check(project,assets,skill):
    errors=[]
    def need(value,message):
        if not value: errors.append(message)
    context=read(assets/'white-box-context.json')
    for name,expected in context['code_sha256'].items():
        need(digest(project/name)==expected,'source changed: '+name)
    req=read(assets/'requirements.json')['items']; reqids={i['id'] for i in req}
    need(digest(assets/'requirements.json')==context['requirements_sha256'],'confirmed requirements changed')
    scenarios=read(assets/'scenarios.json')['items']; white=[s for s in scenarios if s['kind']=='white_box']
    methods=read(assets/'methods.json')['items']; methodmap={m['id']:m for m in methods}; scenariomap={s['id']:s for s in scenarios}; wbmap={s['id']:s for s in white}
    need(len(scenariomap)==len(scenarios),'duplicate scenario IDs'); need(len(methodmap)==len(methods),'duplicate method IDs');need(bool(white),'no white-box scenarios')
    old=assets/'review-history/pre-white-box-design'
    need([s for s in scenarios if s['kind']=='black_box']==read(old/'scenarios.json')['items'],'black-box scenarios changed')
    need(all(methodmap.get(m['id'])==m for m in read(old/'methods.json')['items']),'original methods changed')
    for filename in ['requirements.json','coverage_review.json']:
        need((assets/filename).read_bytes()==(old/filename).read_bytes(),filename+' changed from reviewed baseline')
    need(read(assets/'white-box-context.json')['execution_status']=='not_started','context claims execution')
    need(not (assets/'runs').exists() or not list((assets/'runs').iterdir()),'execution run exists')
    for s in white:
        for name in ['title','target_condition','expected']:
            need(isinstance(s.get(name),str) and bool(s[name].strip()),s['id']+' missing '+name)
        need(bool(s.get('requirement_ids')) and set(s['requirement_ids'])<=reqids,s['id']+' invalid requirements')
        need(bool(s.get('method_ids')) and set(s['method_ids'])<=set(methodmap),s['id']+' invalid methods')
        for identifier in s.get('method_ids',[]):
            m=methodmap.get(identifier,{})
            names=['description','reference'] if m.get('kind')=='case' else ['description','preconditions','actions','evidence_expected']
            need(m.get('kind') in ('case','ai_check'),identifier+' invalid method kind')
            for name in names: need(bool(m.get(name)),identifier+' missing '+name)
    mapping=read(assets/'white-box-map.json'); targets=mapping['targets']; targetmap={t['id']:t for t in targets}
    need(bool(mapping.get('basis')),'missing design/code basis');need(len(targetmap)==len(targets) and bool(targets),'invalid target IDs')
    mapped=set()
    for t in targets:
        need(bool(t.get('risk')) and bool(t.get('description')),t['id']+' missing risk/basis')
        need(bool(t.get('scenario_ids')) and set(t['scenario_ids'])<=set(wbmap),t['id']+' missing white-box scenario link')
        mapped.update(t.get('scenario_ids',[]))
        need(bool(t.get('requirement_ids')) and set(t['requirement_ids'])<=reqids,t['id']+' invalid requirement link')
        linkedreq={r for sid in t.get('scenario_ids',[]) for r in wbmap.get(sid,{}).get('requirement_ids',[])}
        need(set(t['requirement_ids'])<=linkedreq,t['id']+' requirement not represented in linked scenarios')
        need(bool(t.get('source_refs')),t['id']+' missing source refs')
        for ref in t.get('source_refs',[]):
            path=ref.get('path'); need(path in context['code_sha256'],t['id']+' unknown source file')
            if path in context['code_sha256']:
                lines=len((project/path).read_text().splitlines());start=ref.get('line_start',0);end=ref.get('line_end',0)
                need(isinstance(start,int) and isinstance(end,int) and 1<=start<=end<=lines,t['id']+' invalid line range')
            need(bool(ref.get('symbol')),t['id']+' missing source symbol')
    need(mapped==set(wbmap),'white-box scenarios without material target mapping')
    assessment=mapping['requirement_assessment'];need(len(assessment)==len(reqids) and {a['requirement_id'] for a in assessment}==reqids,'requirement assessment incomplete')
    for a in assessment:
        need(bool(a.get('reason')),a['requirement_id']+' missing assessment reason')
        for sid in a['white_box_scenario_ids']:
            need(sid in wbmap and a['requirement_id'] in wbmap[sid]['requirement_ids'],a['requirement_id']+' invalid white-box assessment link')
    review=read(assets/'white_box_review.json');need(review.get('status')=='passed','independent white-box review not passed')
    need(review.get('reviewer_kind')=='independent_ai' and bool(review.get('review_reference')),'missing independent review identity')
    need(review.get('implementation_revision')==context['implementation_revision'],'review code revision mismatch')
    need(review.get('scope_hashes')==scope(assets),'white-box independent review stale')
    need(set(review.get('requirements_reviewed',[]))==reqids,'review requirements incomplete')
    need(bool(review.get('basis')) and review.get('uncovered_branches')==[],'review missing basis or uncovered branches')
    reviewed=review.get('items',[]);need(len(reviewed)==len(white) and {r['scenario_id'] for r in reviewed}==set(wbmap),'review missing white-box scenarios')
    for r in reviewed:
        need(r.get('verdict')=='sufficient' and all(r.get(k) for k in ['reason','plausible_fault','failure_signal']),r['scenario_id']+' insufficient scenario review')
    branches=review.get('branch_reviews',[]);need(len(branches)==len(targets) and {r['target_id'] for r in branches}==set(targetmap),'review missing material targets')
    for r in branches:
        need(r.get('verdict')=='sufficient' and bool(r.get('reason')),r['target_id']+' insufficient branch review')
        need(bool(r.get('scenario_ids')) and set(r['scenario_ids'])<=set(targetmap.get(r['target_id'],{}).get('scenario_ids',[])),r['target_id']+' invalid reviewed scenarios')
    inventory=read(assets/'review-history/white-box-independent-inventory.json')['items']; inventoryids={i['id'] for i in inventory}
    checks=review.get('inventory_checks',[]);need(len(checks)==len(inventoryids) and {i['inventory_id'] for i in checks}==inventoryids,'independent inventory audit incomplete')
    for r in checks:
        need(r.get('verdict') in ('sufficient','excluded') and bool(r.get('reason')),r['inventory_id']+' invalid inventory review')
        if r.get('verdict')=='sufficient': need(bool(r.get('scenario_ids')) and set(r['scenario_ids'])<=set(wbmap),r['inventory_id']+' inventory has no white-box coverage')
    spec=importlib.util.spec_from_file_location('skill_checker',skill/'scripts/playbook.py'); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(all(read(assets/'coverage_review.json')[k]==v for k,v in module.coverage_scope_hashes(assets).items()),'black-box review hashes stale')
    report={'stage':'white-box-design-only','checker':'supplementary project design checker; not the compiled full-acceptance gate','status':'white_box_design_ready' if not errors else 'blocked','issues':errors,'scope_hashes':scope(assets),'implementation_revision':context['implementation_revision'],'counts':{'requirements':len(req),'black_box_scenarios':len(scenarios)-len(white),'white_box_scenarios':len(white),'methods':len(methods),'material_targets':len(targets)},'execution_status':'not_started','resources_status':'not_verified','app_acceptance':'not_established'}
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project',type=Path);parser.add_argument('--test-dir',default='tests');parser.add_argument('--skill',type=Path,default=Path('/Users/boboyang/.codex/skills/app-delivery-acceptance'));parser.add_argument('--hashes',action='store_true');parser.add_argument('--save',action='store_true');args=parser.parse_args()
    project=args.project.resolve();assets=project/args.test_dir/'delivery-acceptance'
    try:
        report=scope(assets) if args.hashes else check(project,assets,args.skill)
        if args.save: (assets/'white-box-design-gate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(report,ensure_ascii=False,indent=2))
        raise SystemExit(0 if args.hashes or report['status']=='white_box_design_ready' else 1)
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({'status':'blocked','error':str(error)},ensure_ascii=False));raise SystemExit(1)
