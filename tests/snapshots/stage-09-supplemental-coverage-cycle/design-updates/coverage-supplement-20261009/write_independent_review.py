"""Persist this Reviewer's static design judgment; never import or run the app."""
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone

U = Path(__file__).resolve().parent
L = U.parents[1]
ROOT = L.parents[1]
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
binding = read(U / 'baseline-binding.json')
for f, h in binding['source_sha256'].items():
    assert sha(ROOT / f) == h, f
for f, h in binding['baseline_sha256'].items():
    assert sha(U / 'baseline' / f) == h, f
for f, h in binding['original_acceptance_sha256'].items():
    assert sha(L / 'runs/acceptance-20261008T-full-0b386b4-r1' / f) == h, f
scenes = read(L / 'scenarios.json')['items']
methods = read(L / 'methods.json')['items']
old_s = {s['id']: s for s in read(U / 'baseline/scenarios.json')['items']}
old_m = {m['id']: m for m in read(U / 'baseline/methods.json')['items']}
white = [s for s in scenes if s['kind'] == 'white_box']
targets = read(L / 'white-box-map.json')['targets']
by_scene = {sid: t for t in targets for sid in t['scenario_ids']}
refined = {'WB-ui-dialog-close-no-write', 'WB-ui-logout-races'}
assert len(white) == len(targets) == 71
assert len(scenes) == 167 and len(methods) == 176
assert set(old_s) <= {s['id'] for s in scenes}
assert all(s == old_s[s['id']] for s in scenes if s['id'] in old_s and s['id'] not in refined)
assert all(m == old_m[m['id']] for m in methods if m['id'] in old_m and m['id'] not in {'AI-' + s for s in refined})
assert sha(L / 'requirements.json') == sha(U / 'baseline/requirements.json')
assert sha(L / 'coverage_review.json') == sha(U / 'baseline/coverage_review.json')
hashes = json.loads(subprocess.check_output(['python3', str(L / 'scripts/check_coverage_supplement_design.py'), '--hashes'], cwd=ROOT, text=True))
# This is a persistence helper for this completed review, not a reviewer for
# future edits. Refuse changed designs instead of mechanically approving them.
assert hashes == {
 'requirements_sha256': 'fd62b1a6119975ca9a0e2e16782d0de23462e6cccd076e6eaf03c38ee94aa6b0',
 'white_box_scenarios_sha256': '6a48c666aab90c83a93300d9577850453c9e0f0d8489759d22816a108e7c917a',
 'white_box_methods_sha256': 'c0ae44c655b3e4f65f0d4f81885c238fd8dfea07e5ffe497341e182828dad7eb',
 'white_box_map_sha256': '16781f60899c6c50dad13d69f3220158bbfeb15f69bf36eeb9a98a5d8ba14ee6',
 'context_sha256': '4700a2f044d9415e5edfd4e6bfbdd04e72f104e01d003471b11c59881d6c54cf',
 'independent_inventory_sha256': '96460a8663ca4939d29d3eae10788b4658bc70eea0badc9b9899aec946d421e7',
 'baseline_binding_sha256': '3b0b910fc6b73dea82774c04cd39935c29547652471e042db569c950700eec23',
 'supplement_changes_sha256': 'dd8af073d7230de138c0246e363ccaab629ce134f8be4d88d0752d6d3b31cf93',
 'defensive_reachability_sha256': 'e6546dc476bd5c4271eedd4523c9727009af4257c17287fa4b564b212ae9a3d0',
}, 'Design changed after independent review; a new substantive review is required.'

# Counterfactuals rechecked against current source and each retained method.
faults = {
 'runtime-entry': ('忽略单项启动参数或意外引入第三方依赖', '实际监听、库路径或重启记录与指定参数不一致'),
 'seed-empty-existing': ('已有团队仍重新播种，或按UTC日期生成初始会议', '种子字段增量、既有记录或北京时间明天日期不一致'),
 'password-derivation': ('读取熵却忽略结果，派生伪造或在另一个持久化出口保存可恢复密码', '有效熵因果/独立派生复算错误，或出口对账出现副本/未知遗漏'),
 'persistence-restart': ('已提交记录仅留内存或重启回退业务字段', '同库重启API与独立快照的房间、角色、预约、取消、通知不一致'),
 'health-static-dispatch': ('健康受登录门禁阻挡、不读取真实库，或HEAD发送正文', '匿名健康字段/真实读取、静态资源或HEAD无正文断言失败'),
 'request-origin': ('某条修改路由跳过标记/来源守卫，或宽松前缀匹配Origin', '对应拒绝矩阵产生真实业务修改或错误接受'),
 'json-envelope': ('按字符计长、接受顶层数组，或把合法空对象在全部路由统一拒绝', '实际字节边界与八入口对象解析/业务结果及副作用不符合'),
 'errors-and-response': ('异常类别合并或公开响应泄漏内部堆栈', '真实依赖故障的状态/code/JSON内容与恢复请求不符合'),
 'transaction-failure-matrix': ('仅预约回滚，其他单表/会话写提前提交，或通知与预约分步提交', '逐业务实际DML后/commit失败留下部分状态，恢复重试计数错误'),
 'session-join': ('授权缓存登录时角色、用户团队或误接受过期摘要', '首个业务请求权限/团队集合、身份字段或无会话拒绝不符合'),
 'session-expiry': ('相等端点仍有效或普通查询续期', '八小时精确边界响应、持久expires及其他有效会话对照错误'),
 'login-window-lock': ('格式错误占槽、成功不计数或并发检查移到锁外', '精确滚动窗口配额、同IP并发接受数或独立IP对照错误'),
 'login-switch-and-cookies': ('后续令牌按计数确定生成、保留旧当前会话或额外保存原令牌', '有效熵因果、真实身份/会话隔离、Cookie属性或完整出口对账错误'),
 'logout-revocation': ('只清Cookie而不撤销摘要，或注销该用户所有浏览器', '旧令牌仍有效或另一独立会话被注销'),
 'route-authorizations': ('某管理员路由缺守卫，或只匹配路径而忽略方法', '成员直连成功、跨队改动或错方法越过业务门禁'),
 'rooms-team-deserialization': ('只查启用室或接受客户端team_id覆盖', '当前团队精确集合、停用资料、设备数组或active布尔不符'),
 'day-range-intersection': ('按UTC日或仅开始日过滤、放宽贴边相交、包含取消记录', '指定/默认日期的严格相交ID集合、排序或取消排除不符'),
 'agenda-title-redaction': ('仅界面脱敏或缓存旧角色', '原始API向无权成员泄露主题，或本人/管理员实际主题缺失'),
 'booking-fields-guards': ('强制转换布尔/小数或遗漏字段trim长度边界', '逐字段类型/边界拒绝、规范化保存或无写快照错误'),
 'datetime-parse-normalize': ('自动补时区或按输入字符串比较绝对时刻', '非法时间接受、等价offset误冲突或保存绝对时刻不符'),
 'booking-horizon': ('舍入服务时间、容许start==now或偷偷扩展30天上界', '固定合法payload六个精确服务时钟端点允许/拒绝或副作用错误'),
 'booking-duration': ('只检查一个界限或将闭区间端点排除', '15分钟/8小时对照及过短/过长拒绝或后续粒度归因错误'),
 'booking-open-hours': ('按输入日期判定或只检查开始端点，截掉非零微秒', '营业OR各项、起止粒度、秒/微秒与异offset允许/拒绝错误'),
 'room-eligibility-capacity': ('使用客户端容量/启用缓存或忽略团队归属', '外队/停用/超容量新预约成功或原记录不变量错误'),
 'booking-conflict-serialization': ('遗漏包含形态或把INSERT移出串行事务', '真实并发重叠双成功、相邻误拒或通知/占用计数错误'),
 'booking-insert-notify': ('提前提交预约、错误通知接收者或遗漏保存字段', '同事务轨迹、完整记录与恰一条通知归属/内容不符'),
 'idempotency-priority': ('重放前重新判定时段资格，或取消后恢复预约', '原编号/当前状态不返回，资格变化导致拒绝或通知/占用增加'),
 'idempotency-user-concurrency': ('按团队查key或竞争请求重复插入/覆盖', '同用户竞争产生双记录/通知，或不同用户同key串用结果'),
 'booking-query-scope-join': ('team退化为mine、遗漏团队过滤或使用旧会议室缓存', '精确身份/范围集合、当前名称位置或显式返回字段不符'),
 'cancel-authorization-and-clock': ('全局ID查找泄露，或已取消短路绕过授权', '另一团队语义、本人/管理员授权及服务开始端点拒绝错误'),
 'cancel-atomic-idempotent': ('重复更新取消时间或重复通知，释放时段误伤新预约', '取消时间/通知数量改变或新预约被破坏'),
 'notifications-select-limit': ('按团队过滤、按created_at排序或只返回未读', '105条fixture最新100精确ID与字段/账号隔离不符'),
 'notifications-mark-all': ('只标可见100条或缺user过滤', '未载入5条仍未读或另一用户通知被改变'),
 'room-write-and-return': ('PATCH遗漏字段或更新另一团队房间', '保存/立即读回字段、独立编号或跨队不变量错误'),
 'room-text-capacity-active': ('强制转换容量/active类型或漏trim/新增默认值', '新增/修改类型边界、规范化值和拒绝后原资料错误'),
 'room-equipment-set': ('只验证首项、静默过滤非法项或仅一条路由去重', '首中尾错误项被接受、合法空集/重复集合或返回数组错误'),
 'room-name-unique-concurrency': ('只在POST手工查重或唯一性设为全局', '同队并发重复名、跨队同名误拒或失败编辑修改其他字段'),
 'room-state-existing-bookings': ('停用删除预约、降容更改原人数或重启用忽略当前容量', '旧预约字段变化或启用/停用新预约对照错误'),
 'member-select-role-guards': ('成员可自升、角色非法仍被写入或遗漏团队过滤', '成员列表/角色变更授权、枚举拒绝和前后role快照错误'),
 'last-admin-lock': ('计入另一团队管理员或把计数更新分离到锁外', '并发后本队零管理员或已降身份首个管理请求仍放行'),
 'ui-start-session-errors': ('将所有启动错误当成未登录或成功空空间', '真实401与非401启动错误DOM及恢复结果不符'),
 'ui-api-error-session-transition': ('业务401保留弹窗、login401误清表单或非JSON假成功', '身份/弹窗/login表单与错误可见性及输入保留不符'),
 'ui-login-navigation': ('示例按钮自动登录、角色本地推测或新账号保留旧缓存', '零POST填入、实际登录身份或跨队导航/缓存断言错误'),
 'ui-load-parallel-error': ('单个请求成功即画部分新数据或错误变空列表', '等待状态提前结束、某集合失败被掩盖或重试结果不符'),
 'ui-load-token-races': ('迟到旧401清除有效新身份，或旧finally结束最新加载', '新身份/最新页面被清除、旧内容错误覆盖或加载提前结束'),
 'ui-filters-statistics': ('6人标签误绑4、change不更新、谓词用OR或按过滤集计统计', '真实选项三前态、精确卡片集合/阈值边界及不变统计错误'),
 'ui-room-timeline-agenda': ('相邻端点用<=、采用浏览器时区或日程使用未脱敏主题', '48格逐格与API主题/owner、取消释放或管理编辑入口不符'),
 'ui-timezone-format': ('某一页面使用浏览器本地日期getter', '同一绝对时刻跨浏览器时区的北京时间日期/时段显示不同'),
 'ui-booking-status-sort': ('时间等号端点错误、历史全部升序或进行中仍有取消入口', '四状态/分组/顺序、取消可见性或确认资料错误'),
 'ui-notification-render': ('徽标按历史总未读计数或失败按钮永久禁用', '最新100未读/零徽标、通知字段或失败重试对照错误'),
 'ui-default-times': ('整刻选择已开始时间或19:45之后仍选择今天', '所选日期、默认粒度/开放范围/结束端点或房间资料错误'),
 'ui-booking-draft-key': ('重试每次新K或修改内容后仍旧K', '同弹窗key关联、实际唯一预约/通知或改变后结果不符'),
 'ui-submit-button-matrix': ('仅成功恢复按钮、错误丢输入或预约toast缺编号', '等待重入请求、失败锁死/输入丢失或实际保存与反馈错误'),
 'ui-room-edit-draft': ('编辑未预填、新增残留旧资料或发送错POST/PATCH目标', '输入/payload/目标对象、保存完整字段或失败重试不符'),
 'ui-role-demotion-reload': ('自降后沿用旧身份且不切回spaces/mine', '实际PATCH/session顺序、后台role、导航或下一管理拒绝错误'),
 'ui-text-escaping': ('只转<>而漏属性引号或删除原文替代按文本展示', 'DOM生成可执行节点/属性或业务原文不完整'),
 'ui-accessibility-focus': ('重渲染丢焦点、表单缺标签或反馈不能被感知', '实际键盘轨迹、可访问名称/树、焦点与反馈错误'),
 'ui-responsive-breakpoints': ('某断点隐藏必要入口或长文本将提交/关闭遮挡', '布局尺寸、控件rect、横向遮挡或完整任务不能完成'),
 'seed-failure-retry': ('种子部分提交使count非零，下一启动永久跳过补全', '各批实际写后/commit故障留下部分种子或恢复重试缺资料'),
 'login-format-boundaries': ('格式强转或非法格式消耗尝试配额', 'trim后类型/长度界限、统一凭证拒绝或剩余8槽错误'),
 'idempotency-absolute-precision': ('仅微秒差异被秒级fingerprint误判相同内容', '同K异绝对时刻误返回replayed，而等价offset对照错误'),
}
details = {
 'WB-response-transport-disconnect': ('成功/拒绝响应×BrokenPipe/Reset四项到达位置分开，拒绝except body不硬要求260命中；独立持久状态、新连接业务与正常JSON对照能区分断开和事务失败。', '连接断开杀死服务，或把已提交写入误称回滚', 'PID/新连接恢复失败或提交/拒绝前后状态对账错误'),
 'WB-booking-response-loss-replay': ('commit后真实响应丢失与DML后commit前故障分开，原ID/一单一通知重试、全部五维合法异内容拒绝及trim/UTC等价对照必做。', '丢失响应后的重试再建一单，或把未提交失败伪造为重放', '独立commit因果与K记录/通知计数或首次/重放标志不符'),
 'WB-runtime-sigint-persistence': ('指定PID/监听归属的真实CLI、SIGINT到KeyboardInterrupt/finally路径、同端口同库新进程API与快照对账完整；没有增加具体退出码/硬超时义务。', '中断路径未释放监听或重开同库丢失已提交业务', '端口不能由新目标进程持有或重启资料/种子日期不一致'),
 'WB-ui-mark-read-session-expiry': ('精确到期与独立Cookie容器撤销分别令被测UI旧Cookie真实401；拒绝无写、155 false、登录DOM及恢复对照完整，新Cookie不会污染被测浏览器。', '401后catch重画旧空间或已读拒绝仍修改通知', '真实POST401后旧workspace/成功提示出现或通知快照改变'),
 'WB-ui-role-update-session-expiry': ('自身/他人×PATCH前失效/commit后session前失效四项实际401，独立Cookie/请求屏障保持因果；提交后role不误判回滚，254 false和重新登录权限可观测。', 'PATCH401仍写角色，或session401后用旧user继续加载管理员空间', '后台role与阶段不符、254 false未到达或401后旧业务加载/菜单残留'),
 'WB-ui-self-demotion-session-failure': ('先有第二管理员，真实自降commit后只在session制造503/网络失败；两类故障×数据重试/整页刷新四项独立验证实际重新读身份与菜单，按钮不可达明确缺证。', '仅他人修改故障被测，自降故障后数据重试沿用旧管理员身份', '真实role已member而恢复未读取session、未回spaces/mine或管理入口残留'),
 'WB-ui-date-filter-empty-recovery': ('原生控件change空值路径、无date=空查询与合法D+1可区分日程恢复有独立网络/状态/快照；未新增提示或固定回填政策。', '清空控件发送空日期，或合法恢复后查询/当前日程仍错位', '143 false出口、请求参数与合法选择后的state/date/日程对照错误'),
 'WB-http-unsupported-methods': ('DELETE/OPTIONS/PUT×四身份×五API路径60项穿过真实标准库分派，重复code/JSON/无写及恢复对照，不以应用文件branch计数代替继承入口；不指定拒绝优先级。', '继承入口返回HTML或未知方法越过授权执行业务', '真实Content-Type/JSON结构/稳定code不符或业务快照变化'),
 'WB-ui-dialog-close-no-write': ('原关闭/内部矩阵保留，三弹窗四方向短路条件及dialog自身padding独立原生指针，桌面/窄屏可达性、零POST/PATCH和快照均明示。', '只左侧外部点击能关、右上下注漏，或内部padding误关闭', '坐标/target/求值出口、dialog.open或零写快照不符合'),
 'WB-ui-logout-races': ('旧加载由真实UI发起、第二导航最新加载完成恢复业务按钮，随后暂存真实logout成功再原生开三种弹窗；关闭回调、旧响应/旧会话、新登录及原失败恢复矩阵均保留。', '退出没有关闭业务弹窗，或迟到旧响应恢复旧身份表单', '162关闭回调/全部dialog状态、登录DOM及旧响应到达后状态不符'),
 'WB-json-envelope': ('本轮逐对象复核R1八入口{}：read_json解析合法对象后，三个无参数业务成功与五个缺字段业务拒绝分别判定，原UTF8/字节长度矩阵未移除；与coverage_review.code_review一致。', '把{}当解析失败或把对象合法等同所有业务成功', '三个无参数入口未成功、五个缺字段写入或解析/业务阶段归因错误'),
 'WB-ui-filters-statistics': ('本轮逐对象复核R2真实4/6/8/12 option、每阈值N±1以及6人三前态；容量/四设备交集、全队期望集合和明确零匹配fixture保留，统计/跨日分支未移除。', '6人标签误绑4、事件不更新或容量与设备用OR组合', '真实option/state与独立卡片ID集合或不随筛选变化的统计错误'),
}
items = []
for s in white:
    target = by_scene[s['id']]
    refs = '、'.join(f"{r['path']}:{r['line_start']}–{r['line_end']}" for r in target['source_refs'])
    if s['id'] in details:
        reason, fault, signal = details[s['id']]
    else:
        fault, signal = faults[s['id'][3:]]
        reason = ('逐对象核对场景和全部关联方法与冻结基线一致，并重读当前目标源码及方法前置/动作/证据；'
                  f"目标‘{target['description']}’仍有正常、拒绝及适用边界/状态矩阵，真实响应/独立状态与到达证据共同判定，"
                  f"可识别‘{fault}’的逃逸实现。有效复用范围是该不变设计与固定实现的语义，不沿用旧执行通过结论。")
    items.append({'scenario_id': s['id'], 'verdict': 'sufficient', 'reason': reason + ' 对照源码：' + refs + '。仅设计判断，尚未执行。', 'plausible_fault': fault, 'failure_signal': signal})
by_review = {i['scenario_id']: i for i in items}
changes = read(U / 'change-summary.json')['changes']
gaps = []
for n in range(1, 9):
    gid = f'COV-GAP-{n:03}'
    sids = [c['scenario_id'] for c in changes if c['gap_id'] == gid]
    gaps.append({'gap_id': gid, 'verdict': 'sufficient', 'scenario_ids': sids, 'reason': ' '.join(details[s][0] for s in sids) + '本记录只关闭设计遗漏，执行/覆盖命中仍待后续新run。'})
defenses = read(U / 'defensive-reachability.json')['items']
defense_reasons = {
 'COV-DEF-001': '逐行核对37–58和60–78：普通登录DOM有节点且loadPage内部处理数据异常，但异步DOM/身份交错不能证明绝对不可达；保留未证明状态及竞态观察/限定DOM故障探针合理。',
 'COV-DEF-002': '核对61/64/76、144–145/155等调用点：正常调用有身份前提；直接调用null guard只证明内部防御，真实401/退出矩阵负责防旧shell，不新增用户流程。',
 'COV-DEF-003': '核对5/54/83/85/92–96/252：生产入口枚举固定，没有发现非法page输入来源；直接篡改state的helper探针不能当作用户路径，继续保留覆盖分母。',
 'COV-DEF-004': '核对heading99及四生产调用107/123/135/139，第四参数均显式提供；省略参数属于辅助函数限定探针，不扩展业务验收义务。定位123已修正。',
 'COV-DEF-005': '核对prettyDate15及107的日分割：真实支持环境格式差异尚未证明，Intl适配器可检fallback但不证明浏览器兼容；现有上海时区场景继续有效，未缩减覆盖分母。',
}
review = {
 'status': 'passed', 'reviewer_kind': 'independent_ai',
 'review_reference': '/root/coverage_scenario_reviewer 独立静态复审 round 02；R1提出定位、真实UI时序、Cookie撤销因果及五维内容探针修订后逐项重读',
 'implementation_revision': binding['revision'],
 'created_at': datetime.now(timezone.utc).isoformat(),
 'basis': [
  '读取测试Skill与data-model；独立反事实审阅，不执行或导入App，不把设计充分作为发布证明。',
  '独立先读stage07八组补测建议/未覆盖库存及五防御路径，再阅读固定app/server.py、web/app.js、HTML/CSS、冒烟测试；71场景/71目标逐项source_refs对照。',
  '全部原159场景/168方法与冻结基线逐对象比较，原63白盒保留；61白盒设计不变，其中json-envelope与filters-statistics另重读覆盖审阅code_review所记录的R1/R2既有修订及当前完整方法。',
  '完整阅读新增8方法、细化2方法与所有关联原方法；矩阵项要求逐项判定。R1修订明确两个实际UI加载恢复按钮、独立Cookie容器撤销、五维内容变化及DEF004行123。',
  '8组缺口映射为8新增和2细化；连接捕获与已提交响应丢失分开；继承标准库方法不由app文件branch100%推定。',
  '五防御处置经静态callsite/枚举/参数/Intl核对；没有绝对不可达声明、没有exclude/pragma提分、没有把内部直接调用当正常业务通过。',
  '核实96确认需求、黑盒设计和独立coverage_review不变，六源码哈希及历史run/review/gate SHA与binding一致；本审阅只绑定当前设计哈希，不重新认证旧run。',
 ],
 'scope_hashes': hashes,
 'requirements_reviewed': [r['id'] for r in read(L / 'requirements.json')['items']],
 'uncovered_branches': [],
 'items': items,
 'branch_reviews': [{'target_id': t['id'], 'verdict': 'sufficient', 'reason': '已独立对照当前source_refs的函数/分支与场景链接及方法；' + ' '.join(by_review[s]['reason'] for s in t['scenario_ids']), 'scenario_ids': t['scenario_ids']} for t in targets],
 'supplement_gap_reviews': gaps,
 'defensive_path_reviews': [{'id': d['id'], 'verdict': 'excluded', 'reason': defense_reasons[d['id']] + ' excluded仅指不新增正式业务场景，不从代码覆盖率分母删除；未执行，不宣称命中。'} for d in defenses],
 'execution_status': 'not_started_for_updated_design',
 'app_acceptance': 'not_established',
 'coverage_statement': '旧实测覆盖率不变；本审阅没有运行新测试，不能声称100%覆盖或当前版本通过验收。',
}
payload = json.dumps(review, ensure_ascii=False, indent=2) + '\n'
(U / 'independent-review.json').write_text(payload)
(L / 'white_box_review.json').write_text(payload)
print(json.dumps({'status': review['status'], 'scenario_reviews': len(items), 'target_reviews': len(targets), 'gap_reviews': len(gaps), 'defensive_reviews': len(defenses), 'scope_hashes': hashes}, ensure_ascii=False))
