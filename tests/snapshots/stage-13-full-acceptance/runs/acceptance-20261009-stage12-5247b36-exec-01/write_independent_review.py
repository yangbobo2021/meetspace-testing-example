import json,pathlib,hashlib,subprocess
r=pathlib.Path(__file__).resolve().parent;b=r.parent.parent
read=lambda p:json.loads(p.read_text())
run=read(r/'run.json');sc=read(b/'scenarios.json')['items'];methods=read(b/'methods.json')['items'];req=read(b/'requirements.json')['items']
api={x['method_id']:x for x in read(r/'independent-api-review.json')['results']}
ui=read(r/'ui-execution-results.json')['method_results'];rt=read(r/'runtime-execution-results.json')['method_results'];rm={x['method_id']:x for x in run['method_results']}
reasons={}
def assign(ids,reason):
 for x in ids.split():reasons[x]=reason
assign('AI-application-runtime-1 AI-application-runtime-2 AI-WB-runtime-entry','独立核对两个隔离无第三方Python运行时各11行CLI实际监听归属、默认/单参数/组合参数及持久化读回；默认CLI浏览器已真实登录，非仅启动日志。')
assign('AI-application-runtime-3 AI-application-runtime-4 AI-WB-seed-empty-existing','核对8个时钟/时区/新旧库组合、四种示例身份实际登录、示例会议相对日期和既有数据重启不重复播种；数据库与HTTP结果一致。')
assign('AI-application-runtime-5 AI-WB-persistence-restart','核对会议室修改、角色、预约、取消、通知已读跨真实子进程重启及两日后重开；原字段与日期保留，登录后实际读取可用。')
assign('AI-application-runtime-6 AI-WB-health-static-dispatch','健康响应实际含准确版本及时区，静态/未知路由/不支持方法分发及故障恢复响应符合；未以健康成功替代业务验证。')
assign('AI-application-runtime-7 AI-WB-errors-and-response','对照各HTTP拒绝正文、稳定错误代码/JSON头、无敏感字段、存储503与恢复，以及传输断开后的独立读取；未将预期错误当成功操作。')
assign('AI-application-runtime-8 AI-storage-exception-boundary','审阅真实SQLite外部锁和唯一性冲突、受控Integrity/Operational/普通异常及重复故障恢复；错误分类正确，独立连接未见部分业务写入。')
assign('AI-application-runtime-9 AI-new-room-write-failure-boundary AI-other-writes-failure-boundary AI-transaction-midwrite-boundary AI-WB-transaction-failure-matrix','逐写入入口核对DML返回后的同连接readback、实际故障位置、rollback轨迹、独立连接快照和真实进程重启；取消/创建的通知收件人、登录切换旧会话保留及同载荷重试符合，无重复或部分提交。')
assign('AI-WB-seed-failure-retry','种子插入/最终提交故障实际触发，回滚后独立读取为空、重启移除故障后完整初始化，没有部分种子。')
assign('AI-identity-session-1 AI-identity-session-3 AI-WB-login-format-boundaries','核对格式/类型/长度边界、trim邮箱与大小写、错密码和不存在用户的实际401一致；格式错误不消耗认证额度，正确修复后实际认证成功。')
assign('AI-identity-session-2 AI-WB-password-derivation','四公开合成身份经真实认证、身份和受保护业务查询；独立scrypt重算与错误密码反例一致，非只检查散列字段外形。')
assign('AI-identity-session-4 AI-WB-session-join','实际已有会话查询当前角色和团队连接结果；角色变动即时反映，过期记录清理不影响其他未过期会话。')
assign('AI-identity-session-5 AI-WB-route-authorizations','核对四种无效会话状态与12受保护入口、当前角色和团队边界、切换后首个读写请求，拒绝后业务不变量与合法恢复符合。')
assign('AI-identity-session-6 AI-WB-session-expiry','两会话实际28799/28800/28801秒端点，跨重启且反复访问不延长绝对期限；端点拒绝及另一会话保持符合。')
assign('AI-identity-session-7 AI-identity-session-12 AI-WB-login-switch-and-cookies','同浏览器同/跨团队切换实际新旧会话效果、其他浏览器不受影响及首请求权限均已检查；设置和撤销Cookie属性符合，UI完整结果另由951及原生竞态证据支持。')
assign('AI-identity-session-8 AI-WB-logout-revocation','真实退出后原会话401和清Cookie属性，其他会话保留；无效会话退出无误写，UI注销/重登及失败恢复完整路径符合。')
assign('AI-identity-session-9 AI-WB-login-window-lock','核对8次额度、正确认证同样计数、格式错误排除、独立源IP及同时间戳批量老化，精确60秒端点和滚动恢复符合DR-004。')
assign('AI-identity-session-10 AI-WB-request-origin','实际全部修改入口测试应用标记与Origin/Host组合；缺省/错误/跨源被拒绝，允许分支和修复后重试成功，业务状态核对无副作用。')
assign('AI-identity-session-11 AI-WB-json-envelope','实际媒体类型、对象与非对象JSON、UTF-8、正文大小及缺失/异常Content-Length边界均有HTTP结果，错误先后与不写入一致。')
assign('AI-identity-session-13 AI-identity-session-14 AI-password-persistence-scope AI-salt-entropy-dependence AI-subsequent-session-entropy AI-token-entropy-and-storage-scope','独立审阅31真实OS熵分支、六种前缀E1复现/E2E3差异及62初始/重启I/O轨迹；认证、摘要对应、8小时退出生命周期成立。逐字段解释六表、日志/SQLite附属文件/共享映射/连接出口，无未知对象或未解释持久化路径；结论限于固定源码及已观测出口，不从字符串未命中推导一般密码学安全。')
assign('AI-WB-runtime-sigint-persistence','核对真实CLI与两次SIGINT的KeyboardInterrupt轨迹、退出0/监听关闭、同库重启前后房间预约和已读通知全部字段；首次harness KeyError保留，完整r2证据证明本方法而非被其他路径替代。')
assign('AI-WB-ui-role-demotion-reload AI-WB-ui-self-demotion-session-failure AI-team-administration-7','独立核对本run纯源码原生34项及6新增旧角色刷新×新pending组合；CDP initiator均来自changeRole，旧续段已结束后UI/快照不变且无新请求，真实member403与原生重试成立。另核对自降503/network、重载、旧PATCH及当前401，符合身份代次和角色刷新顺序。')
assign('AI-WB-ui-load-token-races AI-WB-ui-load-parallel-error','逐日期/导航旧新完成顺序和成功/失败组合检查真实请求、UI及业务快照；额外8个P1/P2组合、同token无user和member/admin先session零prefetch、再次失败重试均保持当前状态，旧回调不越过守卫。')
assign('AI-WB-ui-api-error-session-transition AI-WB-ui-mark-read-session-expiry AI-WB-ui-role-update-session-expiry AI-interface-experience-10','实际撤销/过期会话产生真实401，标记已读及角色PATCH前/提交后查询等入口清理工作区与弹窗；当前401与跨身份旧401处理区分，数据库证明未授权操作未提交。')
assign('AI-WB-ui-logout-races','审阅成功/503/network退出及pending退出6组合、新登录与迟到旧结果；失败恢复按钮，成功真实撤销，重登不被旧结果覆盖，业务快照无误写。')
assign('AI-WB-ui-dialog-close-no-write AI-interface-experience-5 AI-interface-experience-11','审阅83个实际弹窗/退出分项，X/Escape/外侧/内侧/保留操作的坐标和pointer事件、无写网络及数据库不变量；不可达外侧方向按视口几何说明，没有伪造点击或扩展需求。')
assign('AI-WB-ui-responsive-breakpoints AI-interface-experience-12','核对16断点布局及320/390/1440完整登录、筛选、预约、取消、通知操作；长内容模态和小屏截图可读，真实控件可操作，无水平溢出；只证明所测Chromium视口。')
assign('AI-WB-ui-accessibility-focus AI-interface-experience-13','键盘真实导航/提交/错误纠正及小屏完整流程，焦点、可访问名称、成功status/错误alert与可见截图匹配。')
assign('AI-WB-ui-booking-draft-key AI-interface-experience-16','同草稿/trim保持幂等键，五字段变更新键，已提交响应丢失后实际重试返回同一预约与唯一通知；取消关闭不提交。')
assign('AI-WB-ui-room-edit-draft AI-interface-experience-9 AI-space-administration-3','核对新增/编辑错误后草稿和按钮恢复、实际冲突及网络失败重试；room-full-update逐字段和最终全字段保存后退出重登读回，联合API既有预约join检查完整证明字段更新。')
assign('AI-WB-ui-submit-button-matrix AI-interface-experience-7 AI-interface-experience-8','实际登录/创建/编辑/取消在等待、成功、业务失败、503、非JSON及网络异常的按钮状态与提示，并检查提交后加载失败不回滚已提交业务；恢复后可重新操作。')
assign('AI-WB-ui-timezone-format AI-interface-experience-15 AI-WB-ui-notification-render AI-notification-center-7','跨UTC/上海/洛杉矶UI实际日期时间和完整通知文本，结合macOS24与Linux12时区/locale/端点的独立北京时间重算；取消/预约文本、排序和已读状态符合。')
assign('AI-WB-ui-filters-statistics AI-room-discovery-5 AI-room-discovery-8 AI-room-discovery-9','25筛选组合及六实际控件切换含零匹配，多个角色/日期状态下统计与原始房间预约一致；过滤后剩余容量/占用不冒充团队总量。')
assign('AI-WB-ui-room-timeline-agenda AI-room-discovery-6 AI-room-discovery-7','0/8/9/10/47占用及取消后空日程完整可见结果，隐私标题按身份区分，排序与实际API及快照相符。')
assign('AI-WB-ui-booking-status-sort AI-reservation-management-3 AI-reservation-management-4 AI-reservation-management-10','实际开始/结束端点和取消状态、列表时间排序及状态样式，取消确认/刷新后只对允许记录开放操作；相同起点不强加额外排序约定。')
assign('AI-WB-ui-text-escaping AI-interface-experience-14','储存型标题、空间/用户/团队和错误文本以真实DOM呈现为字面内容，危险HTML未执行；多入口截图和DOM观察支持。')
assign('AI-WB-ui-default-times AI-interface-experience-6','多服务器/浏览器时区和日期端点检查默认时间、最小人数/新草稿、今日与明日选择，界面按北京时间和合法时段生成。')
assign('AI-WB-ui-start-session-errors','初始session真实401及受控503/非JSON/network分别呈现登录或错误恢复，未错误读取业务；重试真实请求后恢复。')
assign('AI-WB-ui-date-filter-empty-recovery','实际清空日期触发接口拒绝及重试面板，重新选择合法日期恢复查询；没有直接helper调用模拟正常路径。')
assign('AI-WB-ui-login-navigation AI-interface-experience-1 AI-interface-experience-2 AI-interface-experience-3 AI-interface-experience-4','四种真实身份的登录、页面导航、权限菜单和退出/重登完整操作，跨身份清空缓存/筛选；空数据与失败恢复可见结果符合，演示填充仅填表不自动认证。')
reviews=dict(api)
for m in ui+rt:
 mid=m['method_id']; assert mid in reasons,mid
 ev=sorted(set(rm[mid]['evidence']))
 for e in ev: assert (r/e).is_file(),e
 prior=reviews.get(mid)
 reviews[mid]={'method_id':mid,'status':'passed','reason':(prior['reason']+' ' if prior else '')+reasons[mid],'evidence':ev}
assert set(reviews)=={x['id'] for x in methods},(set(x['id'] for x in methods)-set(reviews))
for mid,x in reviews.items():
 for e in x['evidence']:assert (r/e).is_file(),e
review={'revision':run['revision'],'reviewer_kind':'independent_ai','review_reference':'/root/independent_review; independent-api-review.json; independent-method-review.json; independent-evidence-audit.json; independent-final-evidence-audit.json','coverage':{'status':'passed','reason':'独立复审全部96确认需求、167场景及176方法与当前源码71白盒目标。本轮原生34加6新增组合、旧库合成三状态、完整权限/事务/错误矩阵与实际UI路径证据关闭已发现缺口。5防御出口保留覆盖率分母且在确认原生操作范围内无新增必要路径，详见defensive_exit_disposition；uncovered_branches为空表示无尚未证明的重要验收路径，不声称逐分支100%。','requirements_reviewed':[x['id'] for x in req],'white_box_basis':['固定5247b360276f2900d20fdeab96bd75bb3ece73fa的app/server.py、web/app.js、index.html、style.css及tests原测试。','当前scenarios.json/methods.json/white-box-map.json和stage12独立r3设计审阅；71源码目标与176方法一致。','release-preparation/20261009/stage12-coverage-review/review.json及其5剩余防御出口解释只用于设计挑战，不作为本轮passed证据。','本run independent-evidence-audit.json及independent-final-evidence-audit.json；同run真实执行原始请求、快照、I/O轨迹、原生UI事件及截图。'],'uncovered_branches':[]},'results':[],'defensive_exit_disposition':read(b/'release-preparation/20261009/stage12-coverage-review/review.json')['remaining_uncovered_exit_review'],'limitations':['仅固定修订、合成数据、已声明Python/OS/Chromium环境；未宣称真实手机、多浏览器或第三方服务验证。','真实同源HTTP/UI与专门前端失败/时序注入分开；没有第三方Mock E2E通过冒充真实集成。','旧run和开发coverage结果不作本轮通过依据；旧app没有运行，legacy仅当前源码读取经独立方法审定的合成历史格式。','初始sandbox/环境/harness失败和两项扩展范围unproven记录保留；本run后续完整同方法证据单独证明，没有借其他方法pass抹去失败。','源码无修复、tracked文件无变化；harness适配与补执行均保持同一revision。','UI截图只作对应可见状态佐证；例如runtime/finish/alice-other.png仍为加载状态，切换完成由UI951和原生结果、请求及快照另行证明。']}
for s in sc:
 rr=[reviews[x] for x in s['method_ids']]
 review['results'].append({'scenario_id':s['id'],'status':'passed','reason':' '.join(x['method_id']+'：'+x['reason'] for x in rr),'evidence':sorted(set(e for x in rr for e in x['evidence']))})
assert len(review['results'])==167 and len(reviews)==176 and len(req)==96
(r/'independent-method-review.json').write_text(json.dumps({'revision':run['revision'],'reviewer_kind':'independent_ai','review_reference':'/root/independent_review','results':list(reviews.values())},ensure_ascii=False,indent=2)+'\n')
(r/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print('Wrote independent 176 method judgments and 167 scenario judgments, 96 requirements.')
