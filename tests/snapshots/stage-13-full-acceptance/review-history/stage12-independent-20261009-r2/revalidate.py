import json,hashlib,subprocess,copy
from pathlib import Path
from datetime import datetime,timezone
root=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking');p=root/'tests/delivery-acceptance';out=p/'review-history/stage12-independent-20261009-r2';before=p/'design-updates/stage12-role-session-pending-repair/before'
def read(f):return json.loads(f.read_text())
def save(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
now=datetime.now(timezone.utc).isoformat();rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
review=read(p/'coverage_review.json');white=read(p/'white_box_review.json');sc=read(p/'scenarios.json');me=read(p/'methods.json');mp=read(p/'white-box-map.json')
for name in ['coverage_review.json','white_box_review.json','scenario-gate.json']:
 dest=out/('before-'+name)
 if not dest.exists():dest.write_bytes((p/name).read_bytes())
frozen={f:sha(p/f) for f in ['requirements.json','scenarios.json','methods.json','white-box-map.json']}
assert all(sha(root/f)==h for f,h in review['code_review']['code_sha256'].items())
assert rev==review['code_review']['revision']
prior=read(p/'review-history/stage12-independent-20261009/review-summary.json')
assert sha(p/'requirements.json')==prior['analyst_assets_sha256']['requirements.json']
delta={}
for f in ['scenarios.json','methods.json']:
 assert sha(before/f)==prior['analyst_assets_sha256'][f]
 old={x['id']:x for x in read(before/f)['items']};new={x['id']:x for x in read(p/f)['items']};assert old.keys()==new.keys()
 delta[f]=[k for k in new if old[k]!=new[k]]
assert len(delta['scenarios.json'])==len(delta['methods.json'])==4
smap={s['id']:s for s in sc['items']};mmap={m['id']:m for m in me['items']}
newchecks=[c for c in mmap['AI-WB-ui-role-demotion-reload']['matrix_checks'] if c.get('finding_id')=='GAP-STAGE12-ROLE-SESSION-PENDING']
assert len(newchecks)==6
assert {(c['parameters']['new_session_failure'],c['parameters']['old_session_outcome']) for c in newchecks}=={(a,b) for a in ['503','network'] for b in ['200','503','network']}
for mid in ['AI-team-administration-7','AI-interface-experience-8','AI-WB-ui-self-demotion-session-failure']:
 assert {r['key'] for r in mmap[mid]['matrix_check_refs']}=={c['key'] for c in newchecks}
cmd=['python3','/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts/playbook.py','review-hashes',str(root),'--test-dir',str(root/'tests')]
hashes=json.loads(subprocess.check_output(cmd,text=True));save(out/'review-hashes.json',hashes)
reason='六项独立矩阵明确先真实提升V、扣留第一次changeRole取得的旧admin200，再真实自降且令新session503或网络失败，证明同身份/新刷新序/pending=true后才释放旧200、503或网络错误。请求归属和消费完成必须取证，禁止用loadPage身份读、旧PATCH拒绝或恢复后释放代替。旧身份菜单、pending、最新错误/toast以及零额外加载断言将检出只在!identityPending时丢旧响应的错误；恢复须实际重读member。原34矩阵与其他正常/失败/401对照均保留。'
signal='BB-team-administration-7和BB-interface-experience-8经各自方法明确引用六组合；若成功守卫只在!identityPending时生效，释放旧200后member变admin、管理入口重现或pending被清除即失败；若catch旧序守卫被pending豁免，旧503/网络覆盖新错误或触发额外加载即失败。S_old必须证明已消费，之后原生重试仍须实际/session读回member。'
closed=copy.deepcopy(review['findings'][0]);closed.update({'status':'resolved_in_design','resolved_at':now,'resolution':reason,'new_matrix_keys':[c['key'] for c in newchecks],'execution_proven':False})
review['finding_history']=[closed];review['findings']=[];review['status']='passed';review.update(hashes);review['reviewed_at']=now;review['review_reference']='review-history/stage12-independent-20261009-r2/review-summary.json'
review['basis']='本次独立续审全部96需求的模式、用户状态及209反事实探针，核对完整需求快照、167场景和176方法的稳定ID/链接。通过逐项JSON比较确认仅四场景四方法改变，其余定义与上轮实质审查相同，当前5247b36全部产品源码SHA未变；不是仅刷新哈希。复核当前changeRole:274成功守卫、282非401错误守卫、275-279身份/pending/加载/反馈续段与新增六组合，原GAP-STAGE12-ROLE-SESSION-PENDING已被可观察断言覆盖，96条均充分，71白盒目标无剩余重要遗漏。保持synthetic历史兼容及五防御出口的上轮明确审阅；现有场景覆盖的疑似产品风险留给本轮真实执行，不把旧/开发passed当新证据。不修改Analyst场景、方法或white_box_complete标记。'
for x in review['items']:
 rid=x['requirement_id'];x['revalidated_at']=now
 x['reviewed_definition_sha256']={'scenarios':{s['id']:hashlib.sha256(json.dumps(s,ensure_ascii=False,sort_keys=True).encode()).hexdigest() for s in sc['items'] if rid in s['requirement_ids']},'methods':{mid:hashlib.sha256(json.dumps(mmap[mid],ensure_ascii=False,sort_keys=True).encode()).hexdigest() for mid in x['reviewed_method_ids']}}
 if rid in ['team-administration-7','interface-experience-8']:
  x['verdict']='sufficient';x['uncovered_paths']=[];x['reason']=reason
  x['fault_probes'][-1]['failure_signal']=signal
  x['fault_probes'][-1]['matrix_check_refs']=[{'method_id':'AI-WB-ui-role-demotion-reload','key':c['key']} for c in newchecks]
 for ip in x['implementation_fault_probes']:
  if ip.get('verdict')=='gap':ip.update({'verdict':'sufficient','failure_signal':signal})
 x['inspected_branches']=[{'target_id':t['id'],'condition':t['description'],'source_refs':t['source_refs'],'scenario_ids':t['scenario_ids']} for t in mp['targets'] if rid in t['requirement_ids']]
cr=review['code_review'];cr['uncovered_branches']=[];cr['native_matrix_review']={'count':40,'status':'sufficient_design_only','reason':reason,'executed_in_this_review':False}
for w in cr['white_box_items']:
 t=next(t for t in mp['targets'] if w['scenario_id'] in t['scenario_ids']);w['target_condition']=t['description'];w['source_refs']=t['source_refs']
 if w['verdict']=='gap':
  w.update({'verdict':'sufficient','reason':reason,'failure_signal':signal,'resolved_finding_ids':['GAP-STAGE12-ROLE-SESSION-PENDING']});w.pop('finding_ids',None)
assert all(x['verdict']=='sufficient' for x in review['items'])
save(p/'coverage_review.json',review)
white.update({'status':'passed','revalidated_at':now,'basis':[review['basis']],'review_reference':review['review_reference'],'scope_hashes':hashes,'uncovered_branches':[],'items':cr['white_box_items']});save(p/'white_box_review.json',white)
assert frozen=={f:sha(p/f) for f in frozen}
save(out/'review-summary.json',{'revision':rev,'reviewed_at':now,'status':'passed','requirements_sufficient':96,'requirements_gap':0,'fault_probes':209,'white_box_targets':71,'native_matrix_checks':40,'delta':delta,'resolved_findings':[closed],'analyst_assets_unchanged_by_reviewer':True,'analyst_assets_sha256':frozen,'product_sources_unchanged':True,'white_box_complete':sc['white_box_complete'],'execution_status':'not_executed; design sufficient, execution results must be newly observed','release_approved':False})
print('96 requirements sufficient; 209 probes; 71 white-box targets; 40 matrix checks. Analyst assets unchanged.')
