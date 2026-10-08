"""Author coverage-derived design updates only; never execute or modify the App."""
import datetime
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
L=ROOT/'tests/delivery-acceptance'
U=L/'design-updates/coverage-supplement-20261009'
SKILL=Path('/Users/boboyang/.codex/skills/app-delivery-acceptance')
spec=importlib.util.spec_from_file_location('pb',SKILL/'scripts/playbook.py')
pb=importlib.util.module_from_spec(spec);spec.loader.exec_module(pb)
read=lambda name:pb.read_json(L/name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
baseline=U/'baseline'
if baseline.exists():raise SystemExit('Design baseline already exists: do not overwrite or rerun the authoring step')
baseline.mkdir(parents=True)
names=['project.json','requirements.json','scenarios.json','methods.json','coverage_review.json','white_box_review.json',
       'white-box-map.json','white-box-context.json','white-box-design-gate.json','white-box-design-summary.json',
       'design-assessment.json','scenario-gate.json','black-box-gate.json']
for name in names:shutil.copy2(L/name,baseline/name)
source_names=['app/server.py','app/__init__.py','web/app.js','web/index.html','web/style.css','tests/test_smoke.py']
old_run=L/'runs/acceptance-20261008T-full-0b386b4-r1'
bindings={'revision':revision,'created_at':now,'source_sha256':{f:sha(ROOT/f) for f in source_names},
          'baseline_sha256':{n:sha(baseline/n) for n in names},
          'original_acceptance_sha256':{n:sha(old_run/n) for n in ['run.json','review.json','gate-report.json']},
          'scope':'只更新设计；旧运行保持原ledger_hashes；本轮未执行应用或测试'}
pb.write_json(U/'baseline-binding.json',bindings)
sc=read('scenarios.json');mt=read('methods.json');mapping=read('white-box-map.json')
sm={x['id']:x for x in sc['items']};mm={x['id']:x for x in mt['items']}
targets={x['id']:x for x in mapping['targets']}
sc['white_box_complete']=False
common=('本轮仅设计，未执行。后续每个矩阵项使用tests/delivery-acceptance/内的独立源码副本、新SQLite库和匿名端口；'
        '记录修订与源码SHA。默认服务器datetime.now/time.time及浏览器Date分别固定T=2030-04-10T09:00:00+08:00，'
        '空闲预约D=2030-04-11 10:00–11:00+08:00；故障/到期时钟必须验证。A=见山管理员、U=陈悦成员、V=周言成员、B=另一团队管理员，'
        '独立Cookie会话；仅使用公开合成身份。真实HTTP采用有效JSON、同源Origin、X-Meeting-App:1。'
        '故障只能在已验证的I/O、时钟或网络依赖边界设置，禁止替换被测业务函数、事务或SQL判定。'
        '浏览器网络拦截仅证明前端展示/时序，不证明服务端故障；401必须来自真实失效会话。'
        '逐矩阵项单独记录结果，不能用成功项抵消失败项；不能用旧run通过结论认证新定义。'
        '不能证明故障位置、真实状态、操作可达性或证据时记blocked/unproven。Cookie、令牌只留内存，证据删除其值。')
evidence=('计划采集：本轮修订/源码哈希与资源能力、逐项输入和事件时间、真实请求状态及必要脱敏响应、目标路径到达记录、'
          '独立只读业务数据库前后快照、期望/实际对照；失败或拒绝恢复后再次核对相关不变量。命中只证明到达，不能替代行为断言。')
changes=[]
def add(identifier,title,reqs,condition,expected,prep,actions,proof,refs,gap):
    sid='WB-'+identifier;mid='AI-WB-'+identifier;tid='WBT-'+identifier
    assert sid not in sm and mid not in mm and tid not in targets
    scenario={'id':sid,'kind':'white_box','title':title,'requirement_ids':reqs,'target_condition':condition,
              'expected':expected,'method_ids':[mid]}
    method={'id':mid,'kind':'ai_check','description':title+'；全部矩阵项分别执行、断言并保存证据。',
            'preconditions':common+'\n'+prep,'actions':actions+'\n逐项断言场景expected，保留正常对照；任何本方法未执行项不得判通过。',
            'evidence_expected':evidence+'\n'+proof}
    target={'id':tid,'description':condition,'source_refs':refs,'requirement_ids':reqs,'scenario_ids':[sid],
            'risk':expected,'coverage_audit_gap':gap}
    sc['items'].append(scenario);mt['items'].append(method);mapping['targets'].append(target)
    changes.append({'scenario_id':sid,'method_id':mid,'target_id':tid,'change':'added','gap_id':gap})
def ref(path,symbol,start,end):return {'path':path,'symbol':symbol,'line_start':start,'line_end':end}

add('response-transport-disconnect','成功与拒绝响应写入时连接断开及服务恢复',
    ['application-runtime-7','application-runtime-9'],
    'app/server.py:249–260 / Handler.dispatch、184–195 / send_json：正常响应写入的BrokenPipeError/ConnectionResetError进入259–260；AppError拒绝响应在except body写入，捕获位置不同',
    '正常成功响应和业务拒绝响应的连接断开后，进程仍可处理新健康及合法业务请求；已提交业务不能因响应丢失被假装回滚，拒绝业务不留部分写入。断开客户端没有收到响应，不要求其收到JSON；正常连接的后续错误响应仍遵循稳定JSON契约。',
    '后续验证真实socket故障或透明wfile.write依赖适配器只在写响应时触发。每项有实际业务基线；优先真实TCP关闭/RST，无法稳定到达时可以验证依赖故障，但需标明证明范围。',
    '执行2×2矩阵：正常成功响应/实际AppError拒绝响应 × BrokenPipeError/ConnectionResetError。故障前后不改变业务函数。对正常响应用计数确认259–260；对拒绝响应追踪except body，不硬要求260命中。独立核对事务已提交或实际拒绝未写入，再用新连接健康/身份/合法业务及稳定JSON错误对照验证服务恢复；保留进程PID与存活事实。',
    'I/O异常真实种类/位置、响应write栈与259–260计数或except body到达、进程和新连接结果、提交/拒绝的数据库快照。',
    [ref('app/server.py','Handler.send_json',184,195),ref('app/server.py','Handler.dispatch exception bodies',249,263)],'COV-GAP-001')
add('booking-response-loss-replay','预约已提交但响应丢失后的同标识重试',
    ['reservation-creation-11','reservation-creation-12','notification-center-1','application-runtime-9'],
    'app/server.py:249–252 / 事务退出先于send_json；443–449 / existing-key replay；470–479 / 预约和通知同事务；响应写入断开与提交前失败两个阶段',
    '提交已经完成时，同用户同标识同内容重试返回原编号和重放状态，预约及通知只各一条；同标识不同内容仍拒绝且不改原记录。提交前事务失败时没有残留预约/通知，恢复后同请求首次成功，而非伪造重放。',
    '新空闲会议室、U有效会话及固定标识K；透明提交观察与socket响应写入控制，禁止以伪造201/网络响应作为实际提交证据。',
    'A组：分别以BrokenPipe/ConnectionReset在真实预约事务commit完成后、客户端收到响应前断开；直接数据库确认K已有唯一预约及通知，然后恢复HTTP并重发完全相同内容，查原ID/replayed及数量；再以K修改主题、绝对开始时刻或人数各一次，独立核对拒绝不变。B组：真实DML之后commit之前在存储依赖边界失败，独立快照确认没有半写，恢复重发同K应首次成功，再重发应重放。A、B状态不能混为回滚；每项新库/新K。',
    '真实commit/DML返回与失败/响应断开先后、客户端未获响应记录、K关联预约/通知独立计数、重试/异内容拒绝/恢复响应。',
    [ref('app/server.py','Store.connect commit/rollback',107,120),ref('app/server.py','Handler.dispatch commit before response',249,252),ref('app/server.py','Handler.create_booking replay',443,449),ref('app/server.py','create_booking and notify',470,479)],'COV-GAP-001')
add('runtime-sigint-persistence','CLI收到SIGINT后结束监听与同库重启保持资料',
    ['application-runtime-2','application-runtime-4','application-runtime-5'],
    'app/server.py:482–495 / main：serve_forever→KeyboardInterrupt→finally server_close；同库新进程读取已提交资料',
    '真实CLI中断后监听释放，使用同一端口和数据库可再次启动，已提交的会议室/预约/通知/已读资料保持一致，不重复播种。退出码和耗时作为生命周期观察，不新增特定退出码或硬超时业务要求。',
    '真实python -m app.server子进程，显式127.0.0.1与新库及可用端口，确认监听属于目标PID；此矩阵不替代原默认8766与Python3.11参数矩阵。',
    '通过真实API建立一组已保存的房间、预约、通知及已读状态，所有写请求已结束后记录独立快照。向该PID发送SIGINT（对应Ctrl+C），采集退出与492/493/495路径及监听关闭；确认端口不由别的进程代答，再以同库同端口创建新CLI进程，身份建立后API读回并独立对账，种子日期不重算。测试观察等待上限可用于blocked说明，不能无需求直接把超时/某退出码当产品失败。',
    '真实命令/PID/监听归属、SIGINT/进程退出/分支计数、端口释放、同库新进程启动、前后快照与API读回。',
    [ref('app/server.py','main SIGINT/finally',482,495),ref('app/server.py','Store seed/reopen',99,156)],'COV-GAP-002')
add('ui-mark-read-session-expiry','标记全部已读遇到真实到期或撤销会话',
    ['identity-session-5','interface-experience-10','notification-center-5'],
    'web/app.js:152–155 / wirePage mark-read；20–34 / api：实际401清user与dialog；155 if(state.user)为false',
    '本次失效会话的已读写入被拒绝且未读数据不变；界面清身份回登录，catch不得重画旧空间或显示已读成功。重新合法登录后仍可正常标已读。',
    'U登录通知页且有未读及另用户通知；分别建立精确到期和真实会话撤销前态。在用户点击前使会话失效，避免成功提交后才撤销造成不同因果。',
    '两项独立矩阵：服务器时钟到有效期端点；另一真实登录流程撤销当前会话。仍在已载入通知页点击全部已读，等待真实POST/notifications/read的401；跟踪api清user及155 false出口，确认登录页/无旧空间/无成功提示，U及其他用户通知独立快照不变。分别重新合法登录、载入通知并执行成功已读作恢复对照；只能恢复项通过不能抵消失效项未执行。',
    '真实expires/撤销事件（不保存token值）、POST401、155 false出口、DOM/user/按钮及通知快照，恢复API/UI。',
    [ref('web/app.js','api 401',20,34),ref('web/app.js','wirePage mark-read',152,156)],'COV-GAP-005')
add('ui-role-update-session-expiry','角色PATCH与后续身份查询的真实401分支',
    ['team-administration-2','team-administration-7','identity-session-5','interface-experience-10'],
    'web/app.js:247–254 / changeRole：PATCH→session；api401清user后catch的if(state.user)为false；提交前和提交后失效',
    'PATCH401时角色没有写入；PATCH已提交后session401时实际角色保持提交结果，不能误判回滚。两种情况均清身份回登录，catch不请求旧身份空间；重新登录恢复正确角色及菜单，服务实际拒绝降权身份的管理员操作。',
    'A管理页已载入；预先使V也成为同团队管理员，允许A合法自降。以真实到期或撤销构造401，截留只控制事件顺序；自降/修改他人两种对象分别独立准备。',
    '执行2对象×2故障阶段：自降/修改他人 × PATCH发出前会话已失效（实际PATCH401）/PATCH真实commit之后且session发出前会话失效（实际session401）。用请求屏障暂停session请求而不是伪造401，验证失效因果；每项记录后台role，界面state.user=null、254 false及无旧workspace load，旧管理员接口被拒绝。随后重新登录并核对最新角色、导航与数据；自降项回spaces/mine且无管理入口。',
    'PATCH和session实际请求/提交/撤销或到期顺序、两阶段role独立快照、254 false与DOM/后续网络、重新登录真实权限。',
    [ref('web/app.js','api real 401',20,34),ref('web/app.js','changeRole',247,255),ref('app/server.py','members role write',373,387)],'COV-GAP-006')
add('ui-self-demotion-session-failure','自身降权已提交后身份查询503或网络失败及恢复',
    ['team-administration-7','team-administration-4','interface-experience-8'],
    'web/app.js:250–254 / changeRole：自身PATCH成功后session失败仍持旧user，catch loadPage；恢复重新读取角色与菜单',
    '合法自降实际已经提交且服务权限立即按成员生效；身份查询失败明确反馈，不显示修改成功或假装服务角色回滚。故障解除后通过界面提供的重试或整页刷新重新读身份、回会议室并撤去管理员入口；旧管理员状态不应被错误重载当作已恢复身份。',
    'A当前管理员管理页、同团队V已为第二管理员；真实A会话持续有效。故障只放在自降commit之后的/api/session；浏览器503/abort只证明前端，后端role/权限通过直连API与数据库核对。',
    '四项独立矩阵：后续session 503/网络失败 × 故障恢复后现有数据重试按钮/整页刷新。逐项先让真实A PATCH自己role=member完成commit，随后以已验证网络控制使session失败，记录提交role和旧UI身份，不与修改他人故障替代。确认没有成功提示、后台A已为member且实际管理员请求拒绝；解除故障，执行该项指定可操作恢复动作，验证实际session读取、spaces/mine、管理菜单撤去与正常成员数据。若数据重试按钮在该实际状态不可操作，保存DOM事实并记该项unproven，不直接调用loadPage冒充点击。保留普通成功自降和他人修改失败对照。',
    'PATCH自身ID/commit、后续session故障位置、直连后台role和权限、失败反馈/菜单/user、可操作恢复按钮/刷新及重新session事件。',
    [ref('web/app.js','changeRole self demotion and failure',247,255),ref('web/app.js','loadPage error/retry state',60,89),ref('app/server.py','members/admin safeguards',373,387)],'COV-GAP-006')
add('ui-date-filter-empty-recovery','日期筛选清空的guard与合法日期恢复',
    ['room-discovery-2','interface-experience-3'],
    'web/app.js:143 / filter-date change：event.target.value为空时不进入更新/加载；随后有效日期更新state.date并发起真实查询',
    '空值不作为合法查询日发送或展示成功日程，不向API发送date=空字符串；随后选择合法日期，界面当前日期与实际查询/日程一致。未规定空值提示、自动回填或固定回退日期，不新增产品交互政策；API显式空日期拒绝仍由既有场景单独断言。',
    'U已载入日期D的会议室，D与D+1有可区分日程。真实日期控件通过浏览器清空并触发change；不得只在控制台修改state。',
    '使用原生日期输入清空（若自动化fill空值不触发change则通过真实焦点/失焦确认change），记录value、state.date、请求及143 false出口；保证不把空输入变成非法查询或虚假成功。接着选择D+1，等待真实date查询/最新加载，核对控件、state.date、实际返回日期及可区分日程。保留正常D→D+1对照，独立数据快照无写入。',
    '原生控件change事件/值、143出口、state.date与请求参数、查询返回日期/日程及零写快照。',
    [ref('web/app.js','wirePage date filter',142,145),ref('web/app.js','loadPage date query',60,78)],'COV-GAP-007')
add('http-unsupported-methods','未支持HTTP方法的标准库入口与API错误契约',
    ['application-runtime-7','identity-session-5'],
    'app/server.py:168–195 / Handler只实现GET/POST/PATCH/HEAD；继承BaseHTTPRequestHandler.handle_one_request的do_METHOD查找可在dispatch之前返回错误；DELETE/OPTIONS/PUT入口',
    '未支持方法被拒绝，API错误仍为可解析JSON error/code且同类错误代码稳定，不泄露内部异常或密码，不改变业务数据。不擅自规定401/404/405/501的优先级或特定状态码；无效会话不能借未知方法完成业务读写。',
    '真实HTTP服务及四类身份：匿名、有效成员、有效管理员、真实过期/撤销会话。独立有效请求格式/同源头；本方法仅API路径，不将静态HTML错误协议扩成API契约。',
    'DELETE/OPTIONS/PUT × 四身份 × /api/health、/api/rooms、/api/bookings、/api/members、/api/unknown，共60项逐项响应结构和数据库核对。同类请求另一次重复核对code稳定；禁止仅使用GET/POST/PATCH错路由替代继承入口。每项直接调用真实socket/HTTP而非浏览器route.fulfill，追踪标准库do_METHOD分派及是否进入dispatch，业务表前后不变、无身份越权。正常支持方法的健康、合法读写及匿名工作空间401另作恢复对照。',
    '60项身份/方法/路径矩阵、真实HTTP status/Content-Type/JSON error-code、标准库分派和应用dispatch轨迹、重复code与业务快照；不保存Cookie。',
    [ref('app/server.py','Handler HTTP entry methods/inherited handler',168,195),ref('app/server.py','dispatch/API entry',236,252)],'COV-GAP-008')
mapping['targets'][-1]['dependency_refs']=[{'path':'/opt/miniconda3/lib/python3.12/http/server.py','symbol':'BaseHTTPRequestHandler.handle_one_request','line_start':395,'line_end':426,'sha256':sha(Path('/opt/miniconda3/lib/python3.12/http/server.py'))}]

# Preserve IDs, expectations and every original matrix, then add required detail.
sid='WB-ui-dialog-close-no-write';mid='AI-WB-ui-dialog-close-no-write'
sm[sid]['target_condition']+='；逐弹窗分别评估left/right/top/bottom短路坐标与target===dialog的矩形内padding'
sm[sid]['expected']+=' 预约、会议室、取消三弹窗的四侧外部点击都关闭；矩形内dialog自身空白与子元素均不误关，全部路径无业务写入。'
mm[mid]['preconditions']+='\n本轮补充：1280×900、390×844和320×740均分别记录rect与可点击区域；三种dialog均准备未提交状态，不绕过原生modal/inert。'
mm[mid]['actions']+='\n新增必做3弹窗×7动作矩阵：X、Escape、rect左/右/上/下外侧、rect内dialog自身padding；另保留表单子元素内部对照。右侧点击Y在rect范围、上/下侧点击X在rect范围，避免左侧首先短路；左侧选择Y在范围。每次重新打开，记录真实pointer target===dialog与clientX/Y；padding项若事件target不是dialog不能算到达，不能用DOM.click伪造。每种真实视口均执行可达项；若视口没有某方向外部可点击区域，记录该视口不可达及原因，至少在已有桌面目标证实四方向，不强行合成离屏事件。每项没有POST/PATCH且独立业务快照不变。'
mm[mid]['evidence_expected']+='\n逐弹窗/视口/动作的rect、client坐标、event.target、短路条件求值顺序、dialog.open及零业务写；258行branch85 false、branch86后三操作数到达不得被左侧一次命中替代。'
targets['WBT-ui-dialog-close-no-write']['description']=sm[sid]['target_condition']
changes.append({'scenario_id':sid,'method_id':mid,'target_id':'WBT-ui-dialog-close-no-write','change':'refined','gap_id':'COV-GAP-003'})
sid='WB-ui-logout-races';mid='AI-WB-ui-logout-races'
sm[sid]['target_condition']+='；退出真实成功响应先暂存，在等待期间原生打开业务dialog再释放，forEach close回调确实执行'
sm[sid]['expected']+=' 退出成功返回时仍打开的预约/会议室/取消弹窗均关闭，旧身份表单不能延续到新登录。'
mm[mid]['preconditions']+='\n新增时序：先在与目标弹窗对应的真实页面准备按钮及待处理旧加载，然后点击退出并暂存真实响应，再通过仍可操作的界面按钮打开弹窗。禁止在原生modal已打开时用DOM.click强行点击被inert遮挡的退出按钮。'
mm[mid]['actions']+='\n新增3弹窗×旧加载成功/非401错误迟到矩阵：点击退出，真实服务处理完成并暂存响应；在页面仍显示且点击可达时打开booking/room/confirm弹窗，核对dialog.open=true，然后释放真实退出响应。验证162行d.close回调执行、所有弹窗关闭/回登录、实际旧会话业务401。最后释放旧加载，不能恢复旧空间；新登录不恢复旧表单。另保留原退出中双击、503及网络失败按钮恢复矩阵。若实际页面在待处理加载时业务按钮不可达，重新以已载入页面准备弹窗按钮，再创建独立旧加载控制，记录可操作顺序；任何DOM强制click不能充当普通UI证明。'
mm[mid]['evidence_expected']+='\n真实退出处理/响应暂存→原生按钮打开弹窗→响应释放→d.close回调→旧加载释放的有序日志，三弹窗open状态、旧会话实际拒绝、DOM/身份与按钮恢复。'
targets['WBT-ui-logout-races']['description']=sm[sid]['target_condition']
changes.append({'scenario_id':sid,'method_id':mid,'target_id':'WBT-ui-logout-races','change':'refined','gap_id':'COV-GAP-004'})

# Replace the earlier blanket transport exclusion; keep historical map in baseline.
mapping['exclusions']=[x for x in mapping['exclusions'] if 'BrokenPipeError' not in x.get('source_ref','')]
mapping['basis'].append('本轮覆盖率审计驱动设计补充；原测量98.96%/100%与99.44%/93.22%仍是旧测试实测值，不声称新增设计提升计数。')
for a in mapping['requirement_assessment']:
    a['white_box_scenario_ids']=[s['id'] for s in sc['items'] if s['kind']=='white_box' and a['requirement_id'] in s['requirement_ids']]
    if any(c['change']=='added' and a['requirement_id'] in next(s for s in sc['items'] if s['id']==c['scenario_id'])['requirement_ids'] for c in changes):
        a['reason']+=' 覆盖率审计新增故障模式/操作状态的具体矩阵；设计充分性由本轮独立审阅判定。'

defenses=[
 {'id':'COV-DEF-001','source_ref':'web/app.js:56','subject':'login catch的login-error DOM缺失',
  'static_basis':'renderLogin总是创建login-error；login依次await login、session、loadPage；loadPage内部处理请求失败。正常提交按钮在请求中禁用，但异步身份/DOM重建可交错，静态审查不能证明绝对不可达。',
  'reachability':'not_proven_reachable_in_agreed_ui','disposition':'不新增业务场景；在既有身份/加载竞态后续执行时观察DOM重建与未处理异常。如果实际合法UI时序出现缺节点，则新建对应时序补测，不把本分析当覆盖命中。',
  'related_scenario_ids':['WB-ui-load-token-races','WB-ui-api-error-session-transition'],'optional_probe':'隔离UI中刻意删除login-error可验证内部空节点防御，仅证明DOM故障依赖，不作为正常用户路径或本轮执行证据。'},
 {'id':'COV-DEF-002','source_ref':'web/app.js:81','subject':'renderShell无用户guard',
  'static_basis':'loadPage入口61检查user，finally76再次检查；标已读catch155先检查；capacity/equipment控件只在已登录空间存在。',
  'reachability':'normal_callers_guard_identity','disposition':'保留防御分析，不新增已确认业务行为；后续真实401/退出矩阵观察无旧shell复现。',
  'related_scenario_ids':['WB-ui-api-error-session-transition','WB-ui-logout-races','WB-ui-mark-read-session-expiry'],
  'optional_probe':'隔离页直接调用renderShell且user=null只证明内部guard，不能冒充真实业务UI验收。'},
 {'id':'COV-DEF-003','source_ref':'web/app.js:95-96','subject':'pageContent非法page默认分支',
  'static_basis':'初始state.page及login/self-demotion写入spaces；renderShell导航只给spaces/bookings/inbox/条件manage，导航事件读这些固定data-page。',
  'reachability':'no_invalid_enum_entry_found','disposition':'未发现约定UI能生成非法枚举，暂不为篡改内部state新增业务场景，仍保留未命中指标。',
  'related_scenario_ids':['WB-ui-login-navigation'],'optional_probe':'隔离页直接设置非法state.page然后调用pageContent，限定为内部防御测试；非业务状态证明。'},
 {'id':'COV-DEF-004','source_ref':'web/app.js:99','subject':'heading默认aside参数',
  'static_basis':'spacesContent107、bookingsContent117、inboxContent135、manageContent139的生产调用均显式传入第四参数。',
  'reachability':'all_production_calls_supply_argument','disposition':'不新增正式验收场景；未使用的默认值辅助出口仍在代码覆盖分母。',
  'related_scenario_ids':['WB-ui-login-navigation'],'optional_probe':'隔离环境直接省略第四参数调用heading，只证明辅助函数默认值，不能证明用户状态。'},
 {'id':'COV-DEF-005','source_ref':'web/app.js:107','subject':'prettyDate星期后缀fallback',
  'static_basis':'prettyDate15使用zh-CN、Asia/Shanghai和month/day/weekday；当前已验证Chromium输出有日分隔，fallback是Intl输出变化防御。',
  'reachability':'support_environment_variation_not_demonstrated','disposition':'当前支持环境没有已证明格式差异，不扩展浏览器兼容要求；未来实际支持环境出现差异时补环境矩阵。',
  'related_scenario_ids':['WB-ui-timezone-format'],'optional_probe':'透明Intl依赖格式适配器去掉星期后缀可测fallback，仅证明格式依赖故障，不证明真实浏览器兼容。'}]
valid={s['id'] for s in sc['items']}
# The historical navigation/formatter targets use their existing stable names.
for d in defenses:
    d['related_scenario_ids']=[s for s in d['related_scenario_ids'] if s in valid]
    assert d['related_scenario_ids'], 'Defensive analysis must link a real related scene'
    d['execution_status']='not_executed';d['coverage_policy']='保留在原覆盖率分母；不使用exclude或pragma提分'
mapping['exclusions'] += [{'source_ref':d['source_ref'],'reason':d['disposition'],'coverage_defensive_id':d['id']} for d in defenses]
pb.write_json(U/'defensive-reachability.json',{'status':'analyst_static_analysis_pending_independent_review','items':defenses,'basis_revision':revision,'execution_status':'not_executed'})

context={'stage':'coverage-supplement-design-only','workflow_mode':'Skill Analyst/independent Reviewer design steps; full acceptance workflow not launched',
         'authorization':'用户同意根据覆盖率补测建议更新测试场景；本轮不执行补测',
         'implementation_revision':revision,'requirements_sha256':sha(L/'requirements.json'),
         'code_sha256':bindings['source_sha256'],'source_files':source_names,'execution_status':'not_started_for_updated_design',
         'resources_status':'not_reverified_for_updated_design','baseline_ref':'design-updates/coverage-supplement-20261009/baseline-binding.json',
         'coverage_audit_ref':'coverage-audits/coverage-20261008-stage06/metrics.json','created_at':now}
pb.write_json(L/'scenarios.json',sc);pb.write_json(L/'methods.json',mt);pb.write_json(L/'white-box-map.json',mapping);pb.write_json(L/'white-box-context.json',context)
summary={'stage':'coverage-supplement-design-only','status':'pending_independent_review','implementation_revision':revision,
         'counts':{'requirements':96,'black_box_scenarios':96,'white_box_scenarios':71,'total_scenarios':167,'methods':176,'added_scenarios':8,'refined_scenarios':2,'added_methods':8,'refined_methods':2},
         'changes':changes,'audit_gap_ids':[f'COV-GAP-{n:03}' for n in range(1,9)],'defensive_path_count':5,
         'execution_status':'not_started_for_updated_design','prior_acceptance':'incomplete; prior run retained under original ledger hashes',
         'coverage_percentages':'旧测试实测覆盖率不变；新设计未执行，覆盖率提升尚未测量',
         'baseline_ref':context['baseline_ref'],'review_required':True,'created_at':now}
pb.write_json(U/'change-summary.json',summary)
pb.write_json(L/'white-box-design-summary.json',summary)
pb.write_json(L/'design-assessment.json',{'status':'pending_independent_review','role':'Analyst','requirements_sha256':sha(L/'requirements.json'),
     'white_box_complete':False,'black_box_complete':sc['black_box_complete'],'counts':summary['counts'],
     'basis':['当前正式台账新增8个具体白盒场景，细化2条已有矩阵；业务预期仍以96条确认需求为准。','五个防御出口做静态可达性分析，不声称已覆盖。'],
     'execution_status':summary['execution_status'],'independent_review_status':'pending','app_acceptance':'not_established'})
pb.write_json(L/'scenario-gate.json',{'stage':'coverage-supplement-design-only','status':'pending_independent_review',
     'reason':'新白盒定义及方法变更，旧设计门禁与旧run不认证新定义','counts':summary['counts'],'execution_status':summary['execution_status']})
print(json.dumps(summary['counts'],ensure_ascii=False))
