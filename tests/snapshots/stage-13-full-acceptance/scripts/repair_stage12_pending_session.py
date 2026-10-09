"""Repair an independently identified design gap; no product execution/review approval."""
import datetime,json,shutil,subprocess,sys
from pathlib import Path
R=Path.cwd();L=R/'tests/delivery-acceptance'
sys.path.insert(0,'/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts')
import playbook as pb
O=L/'design-updates/stage12-role-session-pending-repair';O.mkdir();(O/'before').mkdir()
names=['scenarios.json','methods.json','design-assessment.json','white-box-map.json','white-box-context.json','white-box-design-summary.json','coverage_review.json','white_box_review.json','scenario-gate.json','requirements.json','resources.json']
before={n:pb.digest(L/n) for n in names}
for n in names:shutil.copyfile(L/n,O/'before'/n)
rev=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();ctx=pb.read_json(L/'current-release-context.json');assert rev==ctx['source_revision']
for p,h in ctx['source_sha256'].items():assert pb.digest(R/p)==h
S=pb.read_json(L/'scenarios.json');M=pb.read_json(L/'methods.json');A=pb.read_json(L/'design-assessment.json');W=pb.read_json(L/'white-box-map.json');C=pb.read_json(L/'white-box-context.json');D=pb.read_json(L/'white-box-design-summary.json')
sm={x['id']:x for x in S['items']};mm={x['id']:x for x in M['items']}
finding='GAP-STAGE12-ROLE-SESSION-PENDING';owner='AI-WB-ui-role-demotion-reload';keys=[]
pre='当前固定HEAD/SHA；每项新隔离库及独立浏览器上下文，A管理员、V本队成员，凭据仅从README公开fixture引用读取。只用原生select/重试；不直接调用changeRole/loadPage，不改state，不替换业务函数。全程不退出或重登，保持同一identityGeneration。第一项角色操作真实把V提升为admin，为随后A合法自降提供第二管理员。'
actions='原生选择V→admin，真实PATCH提交后，将该changeRole紧接着发起的第一次/session请求标记为S_old；让它实际得到user=A/admin的200，再暂存交付。用请求发起栈/顺序证明S_old属于第一次changeRole，绝不是导航/重试loadPage的身份读取。保持S_old未交付，确认A自身select可用，原生A→member并等待真实PATCH200及独立后台member确认。第二次changeRole的/session标记S_new，向它交付指定新故障；待当前错误面板已形成且user=A/member、spaces/mine、identityPending=true、loading=false、最新loadError与toast已捕获，记录刷新序为新序而S_old持旧序、身份代次仍相同。此时禁止先重试/刷新、禁止释放其他loadPage响应代替。记录DOM/状态及网络基线，再向真正的S_old交付指定旧结果。等待S_old响应已消费及其changeRole续段已完成（只读调试/事件跟踪证明，不靠固定短延迟猜测），在任何恢复操作前比对状态/DOM/网络。随后解除仅S_new的故障，点击实际重新加载按钮，等待新的真实/session及成员页面数据加载结束，独立确认后台身份及权限。'
expected='释放S_old后，A仍member、spaces/mine且管理入口不存在；identityPending仍true，loading仍false，roleRefreshToken和identityGeneration不变，loadError及toast文本保持S_new的最新错误，不能换旧错误、清错误或出现旧成功toast。旧200不得写回admin/清pending，旧503/网络不得污染新错误；S_old续段不得新增session或rooms/bookings/notifications/members加载。保持V/admin及A/member、两次真实提交以外无业务写；直连/session为member且/members精确403/forbidden。最后原生重试必须重新/session200读取当前member，清pending/错误后恢复spaces/mine、无管理入口；读取和重试不改变已提交角色。'
evidence='逐项保存S_old/S_new匿名请求ID、发起栈或等价归属证明、真实PATCH提交与旧admin200获取顺序；新错误已稳定且pending=true的释放前快照，旧响应真实交付及异步续段消费完成证据，释放后DOM/只读state/错误toast对照及网络增量为空，后台session/member403和角色快照，恢复请求与截图。200必须来自原真实响应；503/abort标记为前端依赖故障，不能证明服务真实503；Cookie/密码/会话原值不写证据。无法证明请求归属、原生可操作性或续段已消费则unproven，不把释放其他pending响应或旧开发通过算本项证据。'
for new in ['503','network']:
 for old in ['200','503','network']:
  key=f'old-changeRole-session-{old}-after-new-self-session-{new}-pending';keys.append(key)
  detail=('S_new返回带唯一新错误标识的受控503 JSON。' if new=='503' else '仅S_new执行网络abort；捕获浏览器实际错误文本为本项最新错误基线，不硬编码跨浏览器错误字面值。')
  detail+=('S_old释放原始真实admin200，禁止重新fetch改成当前member响应。' if old=='200' else 'S_old交付带可区分旧错误标识的受控503 JSON。' if old=='503' else '仅S_old网络abort；不改其他请求。')
  mm[owner]['matrix_checks'].append({'key':key,'operation_mode':'同身份旧changeRole.session在较新自降pending错误后到达','parameters':{'new_session_failure':new,'old_session_outcome':old},'user_state':'后台A已member；旧角色身份响应仍为admin；最新pending错误尚未恢复','preconditions':pre,'actions':actions+' '+detail,'expected':expected,'evidence_expected':evidence,'finding_id':finding,'execution_status':'not_executed_for_this_design','source_case_ref':None,'implementation_note':'AI-operated check；既有native34脚本不包含本项，Tester应原生操作或在ignored台账内补专用harness，不把原pending_cross视为本项。'})
reftext='独立审阅缺口修复：必须执行AI-WB-ui-role-demotion-reload.matrix_checks中finding_id='+finding+'的六项；新自降session故障503/网络 × 旧changeRole.session结果200/503/网络，逐项独立基线。释放的是第一角色操作的S_old，且必须先证明最新自降已提交并处于pending错误；不能用旧loadPage身份读、旧PATCH拒绝或pending=false后释放替代。原34项和此前所有方法矩阵继续保留。'
for mid in [owner,'AI-WB-ui-self-demotion-session-failure','AI-team-administration-7','AI-interface-experience-8']:
 mm[mid]['actions']+='\n'+reftext
 mm[mid]['evidence_expected']+='\n'+evidence
 if mid!=owner:
  mm[mid]['matrix_check_refs']=[{'method_id':owner,'key':key} for key in keys]
  mm[mid]['related_method_ids']=list(dict.fromkeys(mm[mid].get('related_method_ids',[])+[owner]))
for sid in ['BB-team-administration-7','BB-interface-experience-8','WB-ui-role-demotion-reload','WB-ui-self-demotion-session-failure']:
 sm[sid]['expected']+='\n旧角色身份响应在较新自降提交、身份读取失败且待重试时到达，不得恢复旧管理员界面、清除当前待确认状态、覆盖最新错误或显示旧成功反馈；恢复操作仍必须重新读取当前成员身份。关联方法明确的六个响应/故障组合逐项满足。'
for t in W['targets']:
 if t['id'] in ['WBT-ui-role-demotion-reload','WBT-ui-self-demotion-session-failure']:
  t['description']+=' 同身份旧changeRole.session的成功刷新序守卫与catch非401旧刷新序守卫，在identityPending=true且新错误已形成时仍须拒绝旧续段；禁止仅在pending=false时丢旧结果。六组合覆盖旧200写user/清pending/后续load/toast和旧503/网络污染错误路径。'
  for sid in t['scenario_ids']:sm[sid]['target_condition']='；'.join(dict.fromkeys(r['path']+' / '+r['symbol'] for r in t['source_refs']))+'：'+t['description']
W['basis'].append('按独立发现GAP-STAGE12-ROLE-SESSION-PENDING修补旧changeRole.session在新pending错误下的六组合，区别于原pending_cross只释放loadPage身份响应；仅设计修复，须独立复审与新执行。')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
repair={'finding_id':finding,'status':'addressed_in_design_pending_independent_review','requirement_ids':['team-administration-7','interface-experience-8'],'scenario_ids':['BB-team-administration-7','BB-interface-experience-8','WB-ui-role-demotion-reload','WB-ui-self-demotion-session-failure'],'method_id':owner,'matrix_check_keys':keys,'basis':'2种新身份查询故障×3种旧角色身份响应；先固定当前pending=true、后台member，再释放真正旧changeRole.session，观察错误实现可见的身份/菜单/pending/错误/toast及额外加载；恢复后真实session重新确认。','counterfactual':'若旧刷新序守卫仅在!identityPending时生效，旧admin200会恢复admin或清pending，旧错误会替换最新错误；新增释放前/后断言可识别。此为设计反事实分析，未执行变异或产品。','source_refs':['web/app.js / changeRole session后刷新序守卫','web/app.js / changeRole catch旧刷新非401守卫','web/app.js / changeRole user/pending及loadPage/toast续段'],'independent_review_preserved':True,'execution_status':'not_executed'}
for row in A['items']:
 if row['requirement_id'] in repair['requirement_ids']:
  row['basis']+=' '+repair['basis'];row['operation_modes']=list(dict.fromkeys(row['operation_modes']+['旧changeRole.session在新自降pending错误之后到达，2×3组合']))
  row['user_states']=list(dict.fromkeys(row['user_states']+['同一会话代次，后台已member，新身份确认失败，旧角色查询持有admin结果']))
  row['repair_findings']=[repair];row['assessment']='author_repaired_pending_independent_review';row['unresolved_design_gaps']=[]
  row['independent_review_outcome']='原审阅gap保留；修复未获独立复审'
for row in W['requirement_assessment']:
 if row['requirement_id'] in repair['requirement_ids']:row['reason']+=' '+repair['basis']+' 待独立复审。'
A.update(status='author_repaired_pending_independent_review',assessed_at=now,basis=W['basis'],repair_findings=[repair],independent_review_status='previous_review_failed_94_sufficient_2_gap; repaired_design_pending_re_review',execution_status='not_started_for_updated_design',changes_ref=str((O/'repair-summary.json').relative_to(L)))
A['limitations'].append('原34项原生脚本未实现新增6项；新增动作是可由AI原生操作的明确方法，不宣称harness已实现或场景已执行。')
S['black_box_complete']=True;S['white_box_complete']=False
C.update(stage='stage12-role-session-pending-repair',created_at=now,baseline_ref=str((O/'before').relative_to(L)),repair_finding_id=finding)
D.update(stage='stage12-role-session-pending-repair',status=A['status'],native_matrix_checks=40,original_native_matrix_checks=34,added_pending_session_checks=6,refined_scenarios=4,refined_method_ids=[owner,'AI-WB-ui-self-demotion-session-failure','AI-team-administration-7','AI-interface-experience-8'],review_required=True,independent_review_reference=None)
for n,d in [('scenarios.json',S),('methods.json',M),('design-assessment.json',A),('white-box-map.json',W),('white-box-context.json',C),('white-box-design-summary.json',D)]:pb.write_json(L/n,d)
summary={'revision':rev,'repair':repair,'before_sha256':before,'after_sha256':{n:pb.digest(L/n) for n in names},'counts':A['counts'],'matrix_checks':40,'protected_records':['requirements.json','coverage_review.json','white_box_review.json','resources.json'],'stable_ids_and_requirement_links_preserved':True,'independent_review':'not_performed','execution':'not_performed'}
for n in summary['protected_records']:assert pb.digest(L/n)==before[n]
pb.write_json(O/'repair-summary.json',summary);pb.write_json(L/'repair-summary.json',{'status':A['status'],'finding_id':finding,'details_ref':str((O/'repair-summary.json').relative_to(L)),'counts':A['counts'],'additional_matrix_checks':6,'independent_review':'pending','execution':'not_performed'})
print(json.dumps({'status':A['status'],'matrix_checks':40,'additional_checks':6,'counts':A['counts']},ensure_ascii=False))
