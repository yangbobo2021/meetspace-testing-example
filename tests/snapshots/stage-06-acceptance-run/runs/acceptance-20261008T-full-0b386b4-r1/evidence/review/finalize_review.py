import json, hashlib, subprocess
from pathlib import Path
P=Path('tests/delivery-acceptance');R=P/'runs/acceptance-20261008T-full-0b386b4-r1'
def read(p):return json.loads(p.read_text())
run=read(R/'run.json');sc=read(P/'scenarios.json')['items'];notes=read(R/'evidence/review/scenario-reasons.json')
notes['BB-application-runtime-9']='独立SQLite快照、实际业务读回及恢复请求覆盖预约/通知、取消/通知、房间、双向角色、105条已读。补测首DML真实返回并同连接读到写入后才在第二DML前抛错，所有非故障commit原样通过；八分支应用自行rollback，真子进程重启后同payload重试及重复无额外效果，排除测试器掩盖中途提交。'
notes['BB-room-discovery-8']='常规4/3/2与次日4/1/1；跨午夜三日团队2/3/2及U本人2/1/1，V/B隔离。941完整重跑每身份日期真实零匹配与恢复，指标不变；独立截图命名避免旧501覆写，原非零筛选证据不单独支持此分支。'
# Independent branch-specific reasoning; paired BB evidence reused only where behavior is identical.
rows='''runtime-entry|application-runtime-1,application-runtime-2|main参数到Store与监听归属尚未证明，其他临时端口服务可用不补默认入口缺口。
seed-empty-existing|application-runtime-3,application-runtime-4|count(teams)两路与已有非示例团队不补种均实跑；跨日期重启不是重建库。
password-derivation|identity-session-13|独立派生复算仅证明已保存盐对应的派生值，不证明盐熵链或全持久出口。
persistence-restart|application-runtime-5|Store重新连接/建表未回退资料；检查真正新进程而非仅新HTTP连接。
health-static-dispatch|application-runtime-6|另核真实静态allowlist、GET/HEAD元数据无正文及无身份业务401；health在身份读取前执行。
request-origin|identity-session-10|read_json先标记再严格Origin，对八入口非法请求确认无目标DML。
json-envelope|identity-session-11|重点检查65536字节合法对象成功和{}在三条无必填写路由成功，避免全部空对象拒绝的伪符合。
errors-and-response|application-runtime-7,application-runtime-8|依赖故障分别命中dispatch三个异常分支，HEAD无实体；未把合成注入当作真实外部锁。
transaction-failure-matrix|application-runtime-9|BEGIN IMMEDIATE、真实DML、第二写前与最终commit失败、应用rollback/close轨迹结合全快照判断；没有补偿清理冒充应用原子性。
session-join|identity-session-4,identity-session-5|同会话动态JOIN当前users/team，升降权后直接首业务请求覆盖旧角色缓存反例。
session-expiry|identity-session-6|expires严格大于now；另核login清过期保有效，会话到期值在业务访问前后不变。
login-window-lock|identity-session-9|有效格式才进入锁内计数，成功也append；边界剔除及双实际源IP独立均有原始响应。
login-switch-and-cookies|identity-session-7,identity-session-12,identity-session-14|删除旧摘要/插新摘要原子性和Cookie已证；随机输入与全存储出口方法仍未证，不能整体批准。
logout-revocation|identity-session-8|实际提交DELETE后旧token401，另一会话仍200；退出失败注入恢复也保留旧会话。
route-authorizations|team-administration-2|逐路由HTTP方法错配、外队/缺失目标及成员守卫有独立快照；并非只观察管理按钮。
rooms-team-deserialization|room-discovery-1|真实返回active布尔/equipment数组，查询包含停用室且团队条件不可伪造。
day-range-intersection|room-discovery-2,room-discovery-3|相交与排序子矩阵成立，但显式空日期漏过date校验，整个条件不成立。
agenda-title-redaction|room-discovery-4|核API原文以及展开DOM，动态role改变服务端脱敏而非CSS隐藏。
booking-fields-guards|reservation-creation-2|completion全矩阵102断言补六种双非法字段组合，按校验顺序首错误且零副作用；不只单字段探针。
datetime-parse-normalize|reservation-creation-3|fromisoformat异常和无offset拒绝，跨偏移UTC归一化正例与等价重放单独核对。
booking-horizon|reservation-creation-4|固定合法对齐T*避免其他粒度规则抢先；服务钟六边界和独立浏览器漂移均可辨认。
booking-duration|reservation-creation-5|独立绝对时长端点拒绝不被开门/粒度条件混为唯一证明。
booking-open-hours|reservation-creation-6,reservation-creation-7|起点终点各秒/微秒独立非零探针，20点后任何分量拒绝，跨offset仍按北京同日。
room-eligibility-capacity|reservation-creation-1,reservation-creation-8|服务提交时重读active/capacity；旧弹窗先开后改房间使客户端max不能代替服务判断。
booking-conflict-serialization|reservation-creation-9|实际写事务屏障竞争与最终表/通知对照，已取消和严格相邻分支分别排除假冲突。
booking-insert-notify|reservation-creation-10,notification-center-1|lastrowid/owner/未读及原子性虽成立，notify生成文本缺北京起点，整个白盒预期失败。
idempotency-priority|reservation-creation-11,reservation-creation-12|秒级fingerprint先于粒度守卫，导致已存在key的微秒差返回原单；不能用正常重放抵消不同内容失败。
idempotency-user-concurrency|reservation-creation-12|此分支专看user+key唯一性和并发：独立用户同key独立，单用户同内容仅一单通知、不同内容一个冲突；微秒精度缺陷另单列。
booking-query-scope-join|reservation-management-1,reservation-management-2|当前rooms/users JOIN及start DESC/id DESC原始顺序核对，mine/team/非法scope逐态授权。
cancel-authorization-and-clock|reservation-management-5,reservation-management-6|先团队再owner/admin，confirmed首次取消严格开始端点；不能把cancelled重放成功当作放行首次。
cancel-atomic-idempotent|reservation-management-7,reservation-management-8|取消UPDATE→owner通知在同事务；before-second-write允许所有真实commit故能检出意外中途提交，重复保持cancelled_at。
notifications-select-limit|notification-center-3,notification-center-4|检查ID生成倒序而非时间同值排序，101/105溢出最新100且管理员无跨用户特权。
notifications-mark-all|notification-center-5|旧5条未载入仍更新，真实105行写后故障rollback与其他用户快照不变；后增三条未读。
room-write-and-return|space-administration-2,space-administration-3,space-administration-9|新增lastrowid再读回，编辑team限定五字段保存，失败外队无泄漏。
room-text-capacity-active|space-administration-5|bool先于int、trim闭区间及缺active默认true，POST/PATCH各入口真实读回。
room-equipment-set|space-administration-6|list类型与逐元素检查、sorted(set)去重、空设备合法；非法混合元素没有部分保留。
room-name-unique-concurrency|space-administration-4|disabled R2仍参与UNIQUE；A/V独立管理员会话CC/EE/CE双顺序并发，九次真正子进程重启读回全资料与预约通知不变量。
room-state-existing-bookings|space-administration-7,space-administration-8,space-administration-10|UPDATE只room，旧bookings人数/状态不改；后续创建按当前active和capacity。
member-select-role-guards|team-administration-1,team-administration-3|role列表/字典在集合成员操作引发TypeError落500而非业务400，守卫类型分支失败。
last-admin-lock|team-administration-4,team-administration-5|事务内身份/count/update串行化，并发互降后的唯一管理员保留；无旧count缓存推断。
ui-start-session-errors|interface-experience-4,interface-experience-10|start session的200/401/非401分别显示shell/login/error，恢复后真正重新请求。
ui-api-error-session-transition|interface-experience-9,interface-experience-10|当前身份业务401关闭dialog；登录错密仍登录反馈；JSON解析失败和网络拒绝保留表单且可重试。
ui-login-navigation|interface-experience-1,interface-experience-2,identity-session-7|login后session重读重置四列表，示例仅填字段无网络写，跨队入口不携旧数据。
ui-load-parallel-error|interface-experience-4|四类请求每类失败单独拦截，Promise.all未完成保持loading，无部分假空列表，members仅admin/manage。
ui-load-token-races|interface-experience-3|16非401顺序分支成立，但api先清user再loadToken过滤；截图N合法后被O旧401踢回登录且N服务仍200。
ui-filters-statistics|room-discovery-5,room-discovery-8,room-discovery-9|941补真实每日期身份零匹配，统计按未过滤集合；6人选项不同前态分别触发change。
ui-room-timeline-agenda|room-discovery-6,room-discovery-7|格0/8/9/10/47等逐格数组比较，取消后只释放目标格；manage可编辑停用室并保留空设备显示。
ui-timezone-format|interface-experience-15|Intl显式上海在三浏览器时区一致；通知正文后端缺字不误归因于created_at前端格式。
ui-booking-status-sort|reservation-management-3,reservation-management-4,reservation-management-10|cancelled优先、end/start等号及未来升序历史降序按真实DOM核对，确认前不发取消。
ui-notification-render|notification-center-6,notification-center-7|100→0→3徽标与当前列表一致，0按钮disabled，read失败恢复且保留原列表。
ui-default-times|interface-experience-5,interface-experience-6|ceil((minute+1)/15)精确刻度也前推；19:45/20点和过去日期回明天9点，end上限20。
ui-booking-draft-key|interface-experience-16|抓真实POST payload区分trim不变与字段变化，响应丢失发生在服务已提交后，重试原ID无第二通知。
ui-submit-button-matrix|interface-experience-7,interface-experience-8,interface-experience-9|各表单成功/业务/网络/解析失败都有disabled到恢复记录及重试持久读回，不能只看toast。
ui-room-edit-draft|space-administration-3,interface-experience-9|编辑预填五字段，转新增form.reset与editingRoom区分POST/PATCH；失败保持输入后修正成功。
ui-role-demotion-reload|team-administration-7|自降后session新role驱动spaces/mine而非仅删除按钮；失败仍原身份可重试。
ui-logout-races|identity-session-8,interface-experience-3|成功退出loadToken递增、关dialog，旧成功/非401响应不复活；失败toast和按钮恢复，N新会话遭旧401另列失败。
ui-dialog-close-no-write|interface-experience-11|button/Escape/backdrop与内部点击分开，九关闭路径抓零写请求和前后业务状态。
ui-text-escaping|interface-experience-14|DOM无注入节点/事件，textContent与五字符escapeHtml各可见入口含aria属性均检，不靠CSP挡执行判安全。
ui-accessibility-focus|interface-experience-13|真实键盘完成流程，焦点/label/aria-labelledby/alert/status树与截图对应。
ui-responsive-breakpoints|interface-experience-12|跨CSS600/850/1150/1500边界和320/390视口真实操作，dialog尺寸及长文本无横向溢出。
seed-failure-retry|application-runtime-3|seed每批teams/users/rooms/bookings实际写后与commit故障回滚；再启动完成全部示例、四账号登录，已有team路径保持不变。
login-format-boundaries|identity-session-1,identity-session-9|trim长度端点和非字符串在attempts前拒绝；插入格式错误不占8次配额，合法错密与成功均占。
idempotency-absolute-precision|reservation-creation-12|confirmed/cancelled/started三态×start/end+1微秒六反例均201/replayed；−1差异拒绝和绝对等价成功不是全部精度符合。'''
for row in rows.splitlines():
 name,links,specific=row.split('|');notes['WB-'+name]=' '.join(notes['BB-'+k] for k in links.split(','))+' '+specific
failed=set('BB-interface-experience-3 BB-notification-center-1 BB-reservation-creation-10 BB-reservation-creation-12 BB-room-discovery-2 BB-team-administration-3 WB-day-range-intersection WB-booking-insert-notify WB-idempotency-priority WB-member-select-role-guards WB-ui-load-token-races WB-idempotency-absolute-precision'.split())
unproven=set('BB-application-runtime-1 BB-application-runtime-2 BB-identity-session-13 BB-identity-session-14 WB-runtime-entry WB-password-derivation WB-login-switch-and-cookies'.split())
assert len(notes)==159
by={x['scenario_id']:x for x in run['results']}
assert set(by)==set(notes)
results=[]
for x in sc:
 k=x['id'];status='failed' if k in failed else 'unproven' if k in unproven else 'passed'
 assert by[k]['status']==status or (status=='unproven' and by[k]['status']=='blocked'),(k,status,by[k]['status'])
 results.append({'scenario_id':k,'status':status,'reason':notes[k],'evidence':by[k]['evidence']})
rev=run['revision'];assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==rev
assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip()
for n,h in run['ledger_hashes'].items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h
review={'revision':rev,'reviewer_kind':'independent_ai','review_reference':'/root/independent_reviewer；evidence/review/initial-findings.json；evidence/review/scenario-reasons.json','reviewed_run_sha256':hashlib.sha256((R/'run.json').read_bytes()).hexdigest(),'coverage':{'status':'unproven','reason':'独立比对96条确认需求、159场景及168方法的前置/操作/预期与本轮实际证据；140场景证据支持、12实际失败、7仍缺必要环境或因果/全出口证明。补测修复的是测试证明缺口，不是应用代码；不能判完整验收。','requirements_reviewed':[i['id'] for i in read(P/'requirements.json')['items']],'white_box_basis':['app/server.py：Store.connect/seed、read_json/current_user/login、路由授权与异常分类、create_booking/cancel/notify；对照API r2 SQL及source line轨迹、runtime各阶段trace与真实HTTP/快照','web/app.js：api/loadPage/loadToken、login/logout、defaultTimes、表单key与提交/重载、房间格子和预约状态、通知/转义；真实浏览器网络/DOM/截图及旧401反例','web/index.html与web/style.css：原生dialog、label/aria/alert/status、响应断点与焦点；键盘及各视口真实流程','runtime_gap_faults_r1.py及runtime-write-gaps/branches.json：依赖适配只在第二DML前或最终commit抛错，其余commit原样执行；同连接首写读回、独立连接及新进程恢复','API completion disabled名称唯一及双非法字段完整重跑；UI941逐日身份零匹配与独立截图；notification-runtime-control未注入时钟的3.12/3.14对照','仅源行命中不能代表分支完整；基于实际输入/输出/持久变化判定。'],'uncovered_branches':['默认CLI归属监听及默认库、host/port/db单项与组合完整参数隔离、Python3.11运行环境未证。','密码盐的有效OS随机输入因果与全部文件/数据库/WAL/临时/mmap/删除/子进程持久出口未证；dtruss/SIP、fs_usage权限受阻。','首次及后续登录/切换令牌有效熵输入因果与全部持久出口只存摘要的完整观察未证。']},'results':results,'review_integrity':{'ledger_hashes':run['ledger_hashes'],'head_verified':rev,'tracked_working_tree_clean':True,'no_application_changes':True},'history_interpretation':'保留早期执行失败；collapsed details/selector/非零筛选和首工具序列化属于测试器错误，已检查后续完整路径才支持当前结果。role/date/微秒/旧401/通知文本实际产品反例始终failed；其他子矩阵通过不抵消。真实本地集成、依赖故障注入和浏览器响应注入不混称同一真实集成证明。'}
(R/'evidence/review/scenario-reasons.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
(R/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('review written',len(results),'140 passed,12 failed,7 unproven')
