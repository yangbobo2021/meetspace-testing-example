import json, hashlib, subprocess, copy, ast
from pathlib import Path
from datetime import datetime, timezone
root=Path('/Users/boboyang/work/sublang.ai/meeting-room-booking')
p=root/'tests/delivery-acceptance'; out=p/'review-history/stage12-independent-20261009'
skill=Path('/Users/boboyang/work/sublangai/skills/app-delivery-acceptance')
now=datetime.now(timezone.utc).isoformat(); rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def read(name):return json.loads((p/name).read_text())
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for name in ['coverage_review.json','white_box_review.json','scenario-gate.json']:
 dst=out/('before-'+name)
 if not dst.exists():dst.write_bytes((p/name).read_bytes())
review=read('coverage_review.json'); scenarios=read('scenarios.json'); methods=read('methods.json'); mapping=read('white-box-map.json'); reqs=read('requirements.json')
frozen={n:sha(p/n) for n in ['requirements.json','scenarios.json','methods.json','white-box-map.json']}
hashes=json.loads(subprocess.check_output(['python3',str(skill/'scripts/playbook.py'),'review-hashes',str(root),'--test-dir',str(root/'tests')],text=True))
save(out/'review-hashes.json',hashes)
smap={s['id']:s for s in scenarios['items']}; mmap={m['id']:m for m in methods['items']}
source_hashes={str(x.relative_to(root)):sha(x) for folder in ['app','web'] for x in (root/folder).rglob('*') if x.is_file() and '__pycache__' not in x.parts}
assert rev==read('current-release-context.json')['source_revision']
assert all(read('current-release-context.json')['source_sha256'][n]==v for n,v in source_hashes.items())
gap={
 'id':'GAP-STAGE12-ROLE-SESSION-PENDING',
 'requirement_ids':['team-administration-7','interface-experience-8'],
 'scenario_ids':['WB-ui-role-demotion-reload','WB-ui-self-demotion-session-failure'],
 'branch_refs':['web/app.js:274 changeRole/session成功后的identityGeneration与roleRefreshToken守卫','web/app.js:275-278 旧session写user、清pending并加载','web/app.js:282 changeRole/catch旧刷新非401错误守卫','web/app.js:285 pending错误展示'],
 'mode':'同一身份较早changeRole的session响应晚于较新自降提交及其session失败',
 'state':'服务角色已经member；新session503或网络失败，当前identityPending=true且已有最新错误；旧changeRole仍扣留admin session响应',
 'counterexample':'错误实现保留身份代次守卫，但把成功续段的刷新序拒绝改为 roleRefreshToken !== state.roleRefreshToken && !state.identityPending；开发者误以为pending时应接受任一身份响应帮助恢复。较新操作成功结束时仍正确丢旧响应，跨身份仍丢弃，旧loadPage及旧PATCH错误守卫仍正确，故已有分支可全通过。较新自降的session失败后释放旧admin200，则会写回旧admin、清pending、恢复管理菜单，即使原有toast守卫继续抑制旧成功提示，旧admin身份及管理导航仍会恢复，身份与菜单断言应失败。另一个同类反例是catch仅在!identityPending时拒绝旧role-session503/网络错误，覆盖新错误/反馈。',
 'why_existing_definitions_do_not_catch':'original-same-identity-session200与same-identity-old-session503/network均先等较新member工作空间完成（pending=false）才释放旧changeRole.session。pending-cross三项只释放sessions[1]的loadPage身份读，明确first_changeRole_response_still_held=true，随后重试；没有释放sessions[0]的旧changeRole.session。same-identity-old-PATCH-*覆盖PATCH拒绝而非已提交PATCH后的session续段，same-identity-late-PATCH200为有效晚提交，应重新读当前身份，语义不同。一般性expected虽禁止旧响应影响新状态，动作没有构造本组合，不能用泛化文字充当必执行分支。',
 'definition_evidence':['methods.json#AI-WB-ui-role-demotion-reload.matrix_checks','methods.json#AI-WB-ui-self-demotion-session-failure.matrix_checks','methods.json#AI-WB-ui-load-token-races.matrix_checks','release-preparation/20261009/identity-continuation-regressions-r2/matrix.py:38-44','release-preparation/20261009/identity-continuation-regressions-r2/matrix.py:86-98'],
 'required_observable_failure':'独立基线真实提升另一成员并扣留该changeRole的session200；原生自降实际提交后让新的session503/abort形成pending错误。此时分别释放旧changeRole.session的200、503、网络错误，必须保持member、spaces/mine、无管理入口、pending及最新错误/反馈不变；禁止旧成功toast和旧续段发起业务加载。最后原生重试实际读当前session恢复正常。记录UI/只读状态及真实后台member和members403。若上述错误实现运行，至少旧200分支应在旧admin/menu/pending或toast断言失败。',
 'disposition':'拒绝设计充分性，交回Analyst在原ID内明确补齐；Reviewer不修改场景或方法。本次未运行产品，不判当前实现有此缺陷。'
}
save(out/'findings.json',{'revision':rev,'reviewed_at':now,'findings':[gap],'product_defect_claim':False,'analyst_assets_sha256':frozen})
# Current symbolic references are checked against complete files, not copied old line hashes.
py_tree=ast.parse((root/'app/server.py').read_text()); locations=[]
for n in py_tree.body:
 if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
  locations.append({'path':'app/server.py','symbol':n.name,'line_start':n.lineno,'line_end':n.end_lineno})
  if isinstance(n,ast.ClassDef):
   for f in n.body:
    if isinstance(f,ast.FunctionDef):locations.append({'path':'app/server.py','symbol':n.name+'.'+f.name,'line_start':f.lineno,'line_end':f.end_lineno})
locations += [{'path':'web/app.js','symbol':s,'line_start':a,'line_end':b} for s,a,b in [('api',19,38),('login',51,65),('loadPage',67,91),('changeRole',260,289),('logout',179,184),('renderShell',93,104)]]
old_w={x['scenario_id']:x for x in review['code_review']['white_box_items']}; whites=[]
for target in mapping['targets']:
 for sid in target['scenario_ids']:
  x=copy.deepcopy(old_w[sid]);x['source_refs']=copy.deepcopy(target['source_refs']);x['target_condition']=target['description'];x['requirement_ids']=smap[sid]['requirement_ids'];x['reviewed_method_ids']=smap[sid]['method_ids'];x['verdict']='gap' if sid in gap['scenario_ids'] else 'sufficient'
  for ref in x['source_refs']:assert sha(root/ref['path'])==ref['source_sha256'] and ref['revision']==rev
  if sid in gap['scenario_ids']:
   x['plausible_fault']=gap['counterexample'];x['failure_signal']=gap['required_observable_failure'];x['reason']=gap['why_existing_definitions_do_not_catch'];x['finding_ids']=[gap['id']]
  else:x['reason']='本次独立核对当前源码、输入状态和关联方法：'+x['plausible_fault']+'将由本场景的'+x['failure_signal']+'捕获；此为设计审阅，不复用执行通过。'
  whites.append(x)
assert len(whites)==71
for item in review['items']:
 rid=item['requirement_id']; linked=[s for s in scenarios['items'] if rid in s['requirement_ids']]
 item['revalidated_at']=now;item['implementation_revision']=rev;item['reviewed_method_ids']=sorted({mid for s in linked for mid in s['method_ids']})
 item['inspected_branches']=[{'target_id':t['id'],'condition':t['description'],'source_refs':t['source_refs'],'scenario_ids':t['scenario_ids']} for t in mapping['targets'] if rid in t['requirement_ids']]
 item['implementation_fault_probes']=[{'target_id':w['target_id'],'scenario_ids':[w['scenario_id']],'plausible_fault':w['plausible_fault'],'failure_signal':w['failure_signal'],'verdict':w['verdict']} for w in whites if rid in w['requirement_ids']]
 if rid in gap['requirement_ids']:
  item['verdict']='gap';item['reason']='正常成功、自降拒绝及已有竞态分支仍有效，但重要pending状态下的旧changeRole.session续段未被动作矩阵覆盖。'+gap['why_existing_definitions_do_not_catch']
  item['operation_modes'].append(gap['mode']);item['user_states'].append(gap['state'])
  item['fault_probes'].append({'mode':gap['mode'],'state':gap['state'],'plausible_fault':gap['counterexample'],'scenario_ids':['BB-'+rid],'failure_signal':'现有BB正常成功/拒绝步骤不释放此迟到响应，不能保证失败；关联WB也缺该组合。补齐后应观察旧admin菜单/pending被错误清除或旧toast覆盖而失败，详见GAP-STAGE12-ROLE-SESSION-PENDING。'})
  item['uncovered_paths']=[gap['id']+': '+gap['mode']+'；'+gap['required_observable_failure']]
review.update(hashes);review.update({'status':'failed','reviewed_at':now,'reviewer_kind':'independent_ai','basis':'独立重新核对DR-002/DR-004全部96需求、96黑盒与71白盒的关联方法和重要状态，读当前5247b36后端全部分支、前端全部业务函数、HTML/CSS及当前差异；保留并重验逐需求反事实探针。94需求充分，team-administration-7与interface-experience-8因GAP-STAGE12-ROLE-SESSION-PENDING缺少旧changeRole.session到达新pending状态的必执行分支而拒绝。34原生矩阵不等于所有重要状态组合；当前源码正确守卫不抵消设计遗漏。明确审阅synthetic历史canonical SQL替代设计，接受其只运行当前HEAD的范围，不将历史/开发passed用于新运行。不改Analyst场景、方法或完成标记；现有场景能捕获的疑似产品风险仍保留执行，只有这里明确的逃逸反例阻断设计。','findings':[gap],'review_reference':'review-history/stage12-independent-20261009/findings.json'})
review['code_review']={'revision':rev,'code_sha256':source_hashes,'branch_basis':'当前app/server.py完整静态分支与web/app.js全部函数；71目标逐项反事实复核，源码位置/完整文件SHA绑定当前修订。覆盖率报告仅用于发现遗漏，不作本轮执行证据。','inspected_source_locations':locations,'white_box_items':whites,'uncovered_branches':[gap],'native_matrix_review':{'count':sum(len(m.get('matrix_checks',[])) for m in methods['items']),'status':'insufficient_state_combination','reason':gap['why_existing_definitions_do_not_catch']},'legacy_method_review':{'status':'sufficient_design_only','method_id':'AI-WB-idempotency-absolute-precision','source_ref':'release-preparation/20261009/legacy-fixture-method-review.json','basis':'明确接受synthetic历史canonical SQL方法与datetime/time依赖适配设计：独立六表与秒canonical摘要、已知历史摘要双校验，historic-started/future-confirmed/future-cancelled三态；等价原K201、微秒原K409、新K微秒400及合法新K201，全表不变量及通知数量。当前SCHEMA仅AST读，只有当前HEAD执行；合成会话与种子绕过不冒称旧app登录/生成，原历史未证明记录保留。Tester须新run实际执行并验证源/时钟绑定，不把预备报告算通过。'},'coverage_report_refs':['coverage-audits/coverage-stage12-fresh-20261009/summary.json','release-preparation/20261009/stage12-coverage-review/review.json'],'defensive_exit_review':{'lines':[63,94,109,112,120],'decision':'保留分母，无新增原生业务场景要求','reason':'缺失login-error、无user renderShell、未知page、heading省略aside与Intl备用分支在已确认原生路径有上游守卫或所有调用显式传参；不靠直接helper调用制造覆盖。五个未覆盖出口不是本次ROLE-SESSION-PENDING状态组合遗漏的豁免理由。'}}
for rid in ['reservation-creation-7','reservation-creation-11','reservation-creation-12','application-runtime-4']:
 next(x for x in review['items'] if x['requirement_id']==rid)['method_change_review']='已明文审阅synthetic历史canonical SQL方法，详见code_review.legacy_method_review；仅设计充分，不认证历史或新执行结果。'
for rid in ['team-administration-3']:
 next(x for x in review['items'] if x['requirement_id']==rid)['method_change_review']='当前app/server.py:386非str短路避免list/dict集合求值异常；方法含精确400/invalid_request及六表不变，普通成员403、外队/不存在404、最后管理员409、合法200对照，不以无写入掩盖500。'
save(p/'coverage_review.json',review)
wreview=read('white_box_review.json');wreview.update({'status':'failed','implementation_revision':rev,'created_at':now,'revalidated_at':now,'reviewer_kind':'independent_ai','review_reference':review['review_reference'],'basis':[review['basis']],'scope_hashes':hashes,'code_sha256':source_hashes,'requirements_reviewed':[r['id'] for r in reqs['items']],'uncovered_branches':[gap],'items':whites});save(p/'white_box_review.json',wreview)
assert frozen=={n:sha(p/n) for n in frozen}
save(out/'review-summary.json',{'revision':rev,'reviewed_at':now,'requirements':96,'sufficient':94,'gap':2,'black_box_scenarios':96,'white_box_scenarios':71,'methods':176,'native_matrix_items':sum(len(m.get('matrix_checks',[])) for m in methods['items']),'fault_probes':sum(len(r['fault_probes']) for r in review['items']),'analyst_assets_unchanged':True,'analyst_assets_sha256':frozen,'coverage_review_sha256':sha(p/'coverage_review.json'),'verdict':'failed','execution':'未执行产品；有具体设计逃逸反例，须Analyst修订后重审，不启动另一工作流。'})
print(json.dumps(read('review-history/stage12-independent-20261009/review-summary.json'),ensure_ascii=False,indent=2))
