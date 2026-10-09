"""Analyst design only; no application execution and no independent review writes."""
import ast,datetime,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path.cwd();L=ROOT/'tests/delivery-acceptance'
sys.path.insert(0,'/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts')
import playbook as pb
pb.verify_project_binding(L,ROOT)
REV=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
C=pb.read_json(L/'current-release-context.json');assert REV==C['source_revision']
O=L/'design-updates/stage12-source-reassessment-20261009';O.mkdir();(O/'before').mkdir()
names=['requirements.json','scenarios.json','methods.json','coverage_review.json','white_box_review.json','white-box-map.json','white-box-context.json','design-assessment.json','white-box-design-summary.json']
before={n:pb.digest(L/n) for n in names}
for n in names:shutil.copyfile(L/n,O/'before'/n)
S=pb.read_json(L/'scenarios.json');M=pb.read_json(L/'methods.json');W=pb.read_json(L/'white-box-map.json');A=pb.read_json(L/'design-assessment.json');ctx=pb.read_json(L/'white-box-context.json')
sm={x['id']:x for x in S['items']};mm={x['id']:x for x in M['items']};tm={x['id']:x for x in W['targets']}
oldS=json.loads(json.dumps(S));oldM=json.loads(json.dumps(M))
for f,h in C['source_sha256'].items():assert pb.digest(ROOT/f)==h
# Explicit guards follow the current implementation; expectations remain requirement-derived.
descriptions={
'WBT-member-select-role-guards':'admin权限先于role类型；not isinstance(role,str)短路，不对list/dict做集合成员判断；精确admin/member枚举后才按team/id查对象、最后管理员校验和UPDATE。',
'WBT-ui-api-error-session-transition':'api固定请求identityGeneration，解析JSON后判断当前代业务401；仅当前401清身份/关弹窗并携带identityInvalidated给续段；旧代401、login401与非401不撤新身份。',
'WBT-ui-load-parallel-error':'无user返回；pending先读session并由loadToken及user守卫；角色成功提交递增loadToken使旧pending读失效；Promise.all成功/catch/finally仅当前加载可应用。',
'WBT-ui-load-token-races':'loadToken控制加载及pending身份读；identityGeneration控制跨身份响应；角色PATCH成功立即失效旧loadPage；roleRefreshToken控制同身份角色刷新，不能把当前代真实401当旧错误吞掉。',
'WBT-ui-role-demotion-reload':'changeRole起始保存identityGeneration与roleRefreshToken；PATCH成功先检查身份，随后递增刷新序并失效旧load；session续段和load后toast各检查身份/刷新序。旧PATCH错误比较起始刷新序，当前真实401例外保留反馈；有效晚成功重新刷新实际身份。',
'WBT-ui-role-update-session-expiry':'PATCH或提交后session真实401经api递增身份代次并标identityInvalidated；即使旧roleRefreshToken也不能吞当前会话失效；无user的catch只显示错误，不重载旧空间；已提交和未提交分别核对。',
'WBT-ui-self-demotion-session-failure':'自身PATCH已提交后先更新已知member、pending=true；后续session故障保留错误，原生重试先读身份；旧角色session/旧pending load/旧PATCH错误均不得覆盖较新pending；当前PATCH错误仍反馈，有效晚成功仍需确认身份。'}
for tid,desc in descriptions.items():tm[tid]['description']=desc
# Remove brittle line offsets. Symbol + immutable file hash is the source binding.
for t in W['targets']:
 for ref in t['source_refs']:
  ref.pop('line_start',None);ref.pop('line_end',None)
  ref['source_sha256']=pb.digest(ROOT/ref['path']);ref['revision']=REV
 t['implementation_revision']=REV
 for sid in t['scenario_ids']:
  sm[sid]['target_condition']='；'.join(dict.fromkeys(r['path']+' / '+r['symbol'] for r in t['source_refs']))+'：'+t['description']
# Keep the important matrix as method subchecks, not additional scenario/method IDs.
p=L/'release-preparation/20261009/identity-continuation-regressions-r2/matrix.py'
tree=ast.parse(p.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.Assign,ast.AugAssign)) and ((isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CASES' for t in n.targets)) or (isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='CASES'))]
ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);cases=ns['CASES'];assert len(cases)==34
# Per-family concrete native actions and expected signals; parameters expand each case.
families={
'cross-session200':('AI-WB-ui-role-demotion-reload','管理员原生修改本人/他人角色，暂存真实session200；原生退出并按参数登录异队管理员或同队成员，直连确认新会话后释放旧session。','新身份/团队/角色/page/scope/菜单保持，旧角色结果不写入新UI且不显示旧成功toast。'),
'cross-phase':('AI-WB-ui-role-demotion-reload','在参数指定PATCH或session阶段设置响应屏障；200/401用真实响应，401先真实撤销；503/网络失败仅作为UI故障适配。退出并登录新账号，验证新身份有效后释放旧响应。','旧响应不改新user/pending/loading/error/toast，不触发旧工作空间请求；实际后台提交与拒绝分别保存，不把响应失败等同回滚。'),
'same-session200':('AI-WB-ui-role-demotion-reload','原生提升周言为admin并暂存旧admin session200；利用另一可用select原生自降，待member加载完成再释放旧admin结果。','当前仍member、spaces/mine，无管理入口，真实members403；不恢复旧admin或改变已提交角色。'),
'same-late-patch':('AI-WB-ui-role-demotion-reload','分别暂存早PATCH已提交的200响应、或在实际提交前暂存请求；先完成另一次角色操作，再释放旧成功响应或使原生旧请求真实晚提交。','不能按点击先后忽略有效成功确认；必须重新读取服务当前身份，最终member界面与真实session一致，members403且无错误pending。'),
'same-error':('AI-WB-ui-role-demotion-reload','提升周言，暂存第一次session；原生自降并完成新member工作空间，再将旧session以参数503/网络错误释放。','较新member、页面、错误及toast保持，旧session失败不重新加载或污染新操作。'),
'pending-cross':('AI-WB-ui-load-token-races','提升周言后暂存首个角色session；自降PATCH先暂停，原生导航产生第二个pending session并暂停；释放自降提交，让新session503形成最新pending错误，再释放旧pending的参数200/503/网络结果。','旧pending结果不能改变新member/pending/loading/error或toast；直连session=member和members403，原生重新加载可恢复spaces/mine。'),
'current401':('AI-WB-ui-role-update-session-expiry','原生提升陈悦；在PATCH发出前或PATCH已commit后的session请求前真实撤销当前会话，实际请求返回401并释放。','回登录、关闭弹窗、清pending且有当前失效反馈；PATCH401目标仍member，session401目标已admin，不将已提交修改误判回滚；重登读当前角色。'),
'earlier-current401':('AI-WB-ui-role-update-session-expiry','暂存较早角色session请求（未到后台），之后原生自降完成；真实撤销当前同代会话，再发出旧请求获得真实401。','即使角色刷新序较旧，当前身份真实失效仍回登录并反馈；不得因旧序吞401，已提交member保留。'),
'stale-toast':('AI-WB-ui-load-token-races','角色提交及session成功后，暂存loadPage真实rooms200；退出并登录新身份完成加载，再释放旧rooms。','旧loadPage不能覆盖新数据，其外层changeRole也不能显示旧成功toast或发起旧身份请求。'),
'normal-nonself':('AI-WB-ui-role-demotion-reload','原生将陈悦提升admin，等待真实PATCH→session→完整管理页加载。','本人仍admin、管理页可用，陈悦select与后台均admin，有本次成功反馈且pending/loading清除。'),
'normal-self':('AI-WB-ui-role-demotion-reload','预置第二管理员后原生将自己改member，观察真实PATCH/session/工作空间请求。','实际member，spaces/mine且管理入口撤去，当前成功反馈可见，后台管理请求拒绝。'),
'demotion':('AI-WB-ui-self-demotion-session-failure','真实自降commit后只对session设置参数503/网络故障；直连核角色与权限，再解除故障并执行参数指定数据重试或整页刷新。','故障期间不假成功或回滚角色；恢复必须实际读session，member、spaces/mine和撤管理入口；按钮不可达则缺证，不调用内部函数代替。'),
'late-patch-error':('AI-WB-ui-self-demotion-session-failure','原生陈悦角色PATCH暂停在提交前；另select真实自降，随后session503形成新pending错误；旧PATCH返回503/网络失败，或真实到后台按已降权会话得到403，最后原生重试。','旧错误不覆盖最新错误/toast/pending/刷新序；角色及持久状态不变，真实member/members403；重试仍能读当前身份恢复。'),
'current-patch-error':('AI-WB-ui-role-demotion-reload','原生陈悦角色PATCH未提交时触发503/网络失败；真实403分支由第二管理员先降权当前账号，再让原请求真实到后台。解除故障后原生重试，403分支重登读取member。','当前错误不能被旧错误守卫吞掉，反馈可见且无成功提示；503/网络无业务写，保持admin可恢复；403目标不被修改、服务member且恢复后无管理入口。'),
'late-success-pending':('AI-WB-ui-self-demotion-session-failure','暂存早陈悦PATCH于提交前；后周言PATCH真实提交且session503进入pending；再使陈悦PATCH真实晚提交200，允许后续session与加载完成。','有效晚成功不能因起始刷新序旧而被丢弃；重新session确认本人admin、两目标admin、清pending/错误且本次成功反馈成立。')}
common_pre='当前HEAD及app/web SHA匹配current-release-context；新隔离库和独立浏览器上下文。A管理员管理页，四公开合成身份凭据只由README引用读取。所有操作由原生导航、select、退出、登录、重试触发，不改state、不直接调用changeRole/loadPage、不替换业务函数。'
common_ev='本轮逐项请求/响应释放时间线、实际commit/撤销证据、UI和只读state前后快照、后台session与管理请求对照、角色及相关表不变量、截图；401/403必须真实，503/abort注明仅前端依赖故障；不保存Cookie或密码。开发75矩阵及旧passed不是本轮证据。'
for name,kind,params,second in cases:
 mid,act,exp=families[kind]
 check={'key':name,'operation_mode':kind,'parameters':list(params),'user_state':'当前管理员；同队第二管理员已准备' if second else '当前管理员；按动作先完成必要晋升/切换','preconditions':common_pre+('先用真实接口准备第二管理员以允许自降。' if second else ''),'actions':act+' 参数='+json.dumps(params,ensure_ascii=False),'expected':exp,'evidence_expected':common_ev,'execution_status':'not_executed_for_this_design','source_case_ref':str(p.relative_to(L))+'#'+name}
 mm[mid].setdefault('matrix_checks',[]).append(check)
for mid in {v[0] for v in families.values()}:
 mm[mid]['actions']+='\n阶段12补充：必须逐项执行本方法matrix_checks，并保留此前所有矩阵；这是原稳定ID内细化，不能只运行开发脚本汇总而遗漏原定义。'
 mm[mid]['evidence_expected']+='\n'+common_ev
 sm[mid.removeprefix('AI-')]['expected']+='\n阶段12：关联方法matrix_checks的每项期望均必须满足；旧身份/旧刷新操作不得改写当前身份与反馈，但当前真实401及有效晚提交成功仍应正常处理。'
# Input type guard and precise rejection remain observable business invariants.
role_actions='当前修订补充：合法admin/member与同值正对照；缺字段、null、0、true、空串、大小写、首尾空格、[]、{}、[admin]及对象role逐项在管理员同队目标上精确400/invalid_request，六表只读前后相等。普通成员携非法数组仍先403/forbidden；管理员合法role对外队/不存在目标404/not_found；唯一管理员自降409/last_admin；有效升降200且后续授权按新role。错误不得降为任意4xx/5xx或只看无写入。'
for mid in ['AI-team-administration-3','AI-WB-member-select-role-guards']:
 mm[mid]['actions']=mm[mid]['actions'].replace('确认非法list/dict是否造成意外异常仍不能写入，预期拒非法角色','确认非法list/dict精确返回400/invalid_request且无副作用')+'\n'+role_actions
 mm[mid]['supporting_case_refs']=['tests/test_regressions.py::ReleaseRegressionTests.test_invalid_role_types_reject_without_writes_and_preserve_permissions']
# Explicitly replace the disallowed old-app execution branch; current source only.
old='使用固定修订的旧版应用在隔离库通过真实请求建立合法预约，停服后由当前修订同库重放，应返回原ID及当前状态且不新增通知；旧源码仅作迁移fixture，不以旧运行passed作证。'
assert old in mm['AI-WB-idempotency-absolute-precision']['actions']
legacy='使用独立synthetic历史canonical SQL夹具验证当前HEAD读取兼容；只执行新HEAD，不启动/导入任何历史应用。已提交stage10/reviewer-legacy-replay.json仅作旧秒精度摘要oracle来源，不是本轮通过证据。独立字面六表结构和旧UTC秒canonical数组SHA256与已知历史摘要双校验；当前SCHEMA只经AST读取比对，不调用业务函数生成预期。'
mm['AI-WB-idempotency-absolute-precision']['actions']=mm['AI-WB-idempotency-absolute-precision']['actions'].replace(old,legacy)
mm['AI-WB-idempotency-absolute-precision']['evidence_expected']=mm['AI-WB-idempotency-absolute-precision']['evidence_expected'].replace('旧库生成修订/当前读取修订','合成夹具来源/静态历史oracle/当前读取修订（不声称旧app新执行）')
legacy_matrix={'fixture_kind':'synthetic_historical_canonical_SQL','source_ref':'release-preparation/20261009/legacy-fixture-method-review.json','harness_ref':'release-preparation/20261009/legacy_fixture_current_only.py','states':['historic-started','future-confirmed','future-cancelled'],'preconditions':'受审manifest.source_revision==请求revision==HEAD且app/web逐文件SHA匹配；每状态新库，既有team避免补种；合成cookie只在内存、存储只有摘要；时钟datetime.now/time.time双适配先验证。historic创建2026，未来fixture创建2030且原创建满足30天规则、取消时间自洽。独立Reviewer须明确审阅本方法及资源适配。','actions':'启动当前实现前后核对全部既有行；已有合成session直接/session和/rooms返回200。三状态分别重放原payload、trim标题、等价UTC+08/Z/+00及显式零微秒；起止各±1微秒用原K重放。future-confirmed另将四项微秒变体改新K，再以空闲14–15时段合法零微秒新K创建并重放。','expected':'原K等价内容精确201/id4/原status/replayed true且全表不变；原K起止±1微秒精确409/idempotency_conflict，全表不变；future新K四项非零微秒精确400/invalid_interval，不以409或任意>=400代替；合法新K精确201/id5/replayed false仅增1预约1通知，重放不再增加且原记录保留。','evidence_expected':'独立schema/canonical来源和已知摘要匹配、三状态合法时间关系、当前源绑定、实际HTTP/全表内存比较布尔及计数，秘密值不输出；历史结果仅来源，夹具不宣称真实旧app生成。','execution_status':'not_executed_for_this_design'}
mm['AI-WB-idempotency-absolute-precision']['legacy_compatibility_matrix']=legacy_matrix
for mid in ['AI-WB-idempotency-priority','AI-reservation-creation-7']:
 mm[mid]['actions']+='\n阶段12合成历史格式交叉检查：执行AI-WB-idempotency-absolute-precision.legacy_compatibility_matrix；前者重点旧K优先返回原状态，后者重点future新K非零微秒精确400和合法零微秒201。不执行历史应用，不降低原本新预约粒度矩阵。'
 mm[mid]['related_method_ids']=['AI-WB-idempotency-absolute-precision']
# Current transport locations are advisory, validated before use rather than stale hardcoded hooks.
mm['AI-WB-response-transport-disconnect']['actions']+='\n当前源码send_json写入204、dispatch正常send_json261、AppError写263、连接异常捕获269为执行前定位提示；必须按当前AST/实际write栈核验而非把旧行号触发当作成功。旧stale-line失败保持历史，新run保留成功/拒绝×两异常及恢复对照。'
# Explicit expected results on every method, without duplicating requirements as a new business ledger.
for m in M['items']:
 linked=[s for s in S['items'] if m['id'] in s['method_ids']]
 assert linked
 m['expected_result_refs']=['scenarios.json#'+s['id']+'.expected' for s in linked]
# Source exclusions remain narrow and retain uncovered defensive outlets in denominator.
defensive={'COV-DEF-001':'web/app.js / login catch target存在性','COV-DEF-002':'web/app.js / renderShell无user早返','COV-DEF-003':'web/app.js / pageContent未知page默认空返回','COV-DEF-004':'web/app.js / heading默认aside参数','COV-DEF-005':'web/app.js / spacesContent prettyDate.split后备空串'}
for x in W['exclusions']:
 x['reassessed_revision']=REV
 if x.get('coverage_defensive_id') in defensive:x['source_ref']=defensive[x['coverage_defensive_id']];x['coverage_policy']='保留覆盖率分母；静态可达性分析不等于执行命中，新计数与独立复审仍需完成。'
 if x['source_ref']=='tests/test_regressions.py':x['reason']='当前五项开发HTTP回归及原三项冒烟可辅助对应AI方法，不能替代完整矩阵和新run证据；本轮设计未执行。'
W['basis']=['确认96需求（DR-002及DR-004）与原96黑盒/71白盒稳定ID逐项对照。','检查当前app/server.py全部入口、事务、SQLite查询与验证顺序；web/app.js身份/加载/角色续段及HTML/CSS交互；与708c9c0差异仅角色类型守卫及身份续段修复、对应回归。','原有需求级模式/用户状态和边界/异常矩阵保留；将34原生身份矩阵分配至原方法，不复用开发通过。','历史兼容按DR-012/013明确改为独立synthetic旧格式SQL，真实历史输出只作oracle来源；只执行当前HEAD。','全部71目标改用符号+固定源码SHA绑定，5个防御出口仍保留分母。','Analyst判断设计已覆盖当前重要路径；独立审阅待进行，不写coverage_review.json，不认定发布。']
# Requirement-by-requirement author mapping remains in the existing assessment ledger.
for row in A['items']:
 rid=row['requirement_id'];bb=[s for s in S['items'] if s['kind']=='black_box' and rid in s['requirement_ids']];wb=[s for s in S['items'] if s['kind']=='white_box' and rid in s['requirement_ids']]
 row.update(assessment='author_assessed_complete_pending_independent_review',black_box_scenario_ids=[s['id'] for s in bb],white_box_scenario_ids=[s['id'] for s in wb],method_ids=sorted({mid for s in bb+wb for mid in s['method_ids']}),mode_state_basis='按当前需求、既有场景/方法重新核对，继承模式清单作为设计输入而非本轮独立批准。',unresolved_design_gaps=[])
 relevant=[m for m in M['items'] if m['id'] in row['method_ids'] and m.get('matrix_checks')]
 if relevant:
  row['operation_modes']=list(dict.fromkeys(row['operation_modes']+[c['operation_mode'] for m in relevant for c in m['matrix_checks']]))
  row['user_states']=list(dict.fromkeys(row['user_states']+['同身份新角色提交已完成','新身份有效而旧角色响应待返回','较新身份确认失败且pending','当前真实会话失效']))
  row['basis']+=' 阶段12角色/身份刷新矩阵覆盖旧PATCH/session/load续段、最新pending、当前401、当前错误反馈和有效晚成功，逐项位于关联方法matrix_checks。'
 if rid=='team-administration-3':row['basis']+=' 列表/对象等非字符串精确400；权限先于输入的403与最后管理员409正反控制保持。'
 if rid in ['reservation-creation-7','reservation-creation-11','reservation-creation-12','application-runtime-4']:row['basis']+=' synthetic历史格式只执行当前源，旧K精度冲突与新K粒度拒绝分开，不执行旧app。'
 row['expectation_refs']=['scenarios.json#'+s['id']+'.expected' for s in bb+wb]
for row in W['requirement_assessment']:
 item=next(i for i in A['items'] if i['requirement_id']==row['requirement_id']);row['reason']=item['basis']+' 本轮仅Analyst设计判断，独立复审及实际执行待完成。'
S['black_box_complete']=True;S['white_box_complete']=False
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for k in ['review_binding','independent_review_refs']:A.pop(k,None)
A.update(status='author_assessed_complete_pending_independent_review',assessed_at=now,implementation_revision=REV,black_box_complete=True,white_box_complete=False,author_design_complete=True,code_sha256=C['source_sha256'],basis=W['basis'],changes_ref=str((O/'changes.json').relative_to(L)),independent_review_status='pending; coverage_review.json and white_box_review.json preserved byte-for-byte',execution_status='not_started_for_updated_design',white_box_gate_pending_reason='当前源码和方法已变化；旧独立审阅不绑定本设计，不能自行批准。')
A['limitations']=['设计完整性是Analyst判断，非独立审阅或应用通过。','黑盒关联方法细化使原作用域审阅哈希过期，Reviewer须重新审阅；旧review/gate保持历史事实。','34原生矩阵是原方法重要子集，不能替代原方法其他边界；Tester必须新run执行全部167场景。','时钟/熵/存储故障/并发/浏览器全部目标需执行前验证；不能到达或缺证保留blocked/unproven。','5防御出口仍在覆盖分母，不能联合不同源码计数。']
ctx.update(stage='stage12-source-reassessment',implementation_revision=REV,code_sha256=C['source_sha256'],created_at=now,baseline_ref=str((O/'before').relative_to(L)),execution_status='not_started_for_updated_design',coverage_audit_ref='阶段11覆盖率仅历史；当前HEAD新计数尚待执行',resources_status='resources.json绑定当前HEAD；专用harness及完整视口矩阵仍须使用前验证')
for n,d in [('scenarios.json',S),('methods.json',M),('white-box-map.json',W),('design-assessment.json',A),('white-box-context.json',ctx)]:pb.write_json(L/n,d)
changed_s=[s['id'] for s,old in zip(S['items'],oldS['items']) if s!=old]
changed_m=[m['id'] for m,old in zip(M['items'],oldM['items']) if any(m.get(k)!=old.get(k) for k in ['actions','preconditions','evidence_expected','matrix_checks','legacy_compatibility_matrix'])]
summary={'stage':'stage12-source-reassessment','status':A['status'],'implementation_revision':REV,'counts':A['counts'],'added_scenarios':0,'added_methods':0,'refined_scenarios':len(changed_s),'refined_method_ids':changed_m,'native_matrix_checks':34,'assessment_ref':'design-assessment.json','review_required':True,'independent_review_reference':None,'execution_status':'not_started_for_updated_design','app_acceptance':'not_established'}
pb.write_json(L/'white-box-design-summary.json',summary)
changes={'revision':REV,'previous_revision':'708c9c057b5c9014f4ff975fdc5774093a687abe','scenario_ids_preserved':True,'method_ids_preserved':True,'changed_scenario_ids':changed_s,'semantic_method_changes':changed_m,'expected_result_refs_added_to_all_methods':True,'native34_methods':{m['id']:[c['key'] for c in m['matrix_checks']] for m in M['items'] if m.get('matrix_checks')},'legacy_method_change':{'original':old,'replacement':legacy,'independent_review_required':True},'before_sha256':before,'after_sha256':{n:pb.digest(L/n) for n in names},'formal_execution':False}
pb.write_json(O/'changes.json',changes)
for n in ['requirements.json','coverage_review.json','white_box_review.json']:assert pb.digest(L/n)==before[n]
assert [x['id'] for x in S['items']]==[x['id'] for x in oldS['items']]
assert [x['id'] for x in M['items']]==[x['id'] for x in oldM['items']]
print(json.dumps(summary,ensure_ascii=False))
