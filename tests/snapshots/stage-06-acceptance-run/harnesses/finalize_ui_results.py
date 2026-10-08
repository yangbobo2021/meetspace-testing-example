import json
from pathlib import Path
R=Path('tests/delivery-acceptance/runs/acceptance-20261008T-full-0b386b4-r1');E=R/'evidence/ui';d=json.load(open(R/'ui-results.json'))
actual={
'AI-interface-experience-1':'四身份逐导航与刷新；管理员team scope退出切成员/异队后page=spaces、scope=mine、缓存与权限正确；真实自降撤管理并后续members403。',
'AI-interface-experience-2':'同一未登录页面连续选择四示例，逐项仅填字段、零登录请求、session401；最后other主动提交后身份正确。',
'AI-interface-experience-4':'rooms/bookings/notifications/members逐一失败、断网、500、503、等待单响应均有错误/同步状态；恢复实际重载有记录；另真实空通知和无匹配房间提供非错误空态对照。',
'AI-interface-experience-5':'两间实际房间依次打开，标题位置容量对应，五输入可聚焦，开放/粒度/时长与日期min/max均核对。',
'AI-interface-experience-6':'上海/洛杉矶同瞬间，11时点×今天/过去/明天/第30天共88组合，默认日期/开放时间/十五分钟对齐/结束上限均通过。',
'AI-interface-experience-7':'登录/预约/新增会议室/编辑会议室/取消分别扣留请求检查disabled、重复Enter不重复提交；成功、4xx、503、网络、非JSON恢复，另真实预约冲突、编辑重复名和开始后取消409复核不变量及修正重试。',
'AI-interface-experience-8':'真实创建、取消、房间新增编辑、角色更新均完成持久读回、相关列表重载与具体toast；预约成功反馈含实际编号。',
'AI-interface-experience-9':'真实预约时段冲突、会议室新增/编辑重名拒绝均保留逐字段输入和数据库原状；修改后成功。预约/新增/编辑网络失败后保留输入且可恢复重试。',
'AI-interface-experience-10':'真实删除会话后booking/room/cancel提交和页面读取四分支401均关闭所有dialog回登录，无业务写入，逐分支重新登录成功。',
'AI-interface-experience-11':'booking/room/confirm×关闭按钮/Escape/外区域9组合，内部标题点击不关，网络零写及数据库逐分支不变；另保留预约后真实查询未取消。',
'AI-interface-experience-12':'1440×900、390×844、320×740分别重新登录，长40字房名/75字位置/95字主题，实际筛选创建取消读通知完整路径，DOM宽度及弹窗边界通过。',
'AI-interface-experience-13':'桌面与390手机键盘登录/筛选/预约/取消/通知，桌面键盘管理表单真实重名alert后修正成功status；保存可访问树、输入标签和outline、Escape关闭后焦点回原按钮。',
'AI-interface-experience-14':'真实存储HTML载荷房名/位置/主题，卡片/日程/弹窗/预约/通知/管理DOM无新增img或onerror，文字完整；其他成员日程脱敏；附业务错误和toast文字安全。',
'AI-interface-experience-15':'UTC/上海/洛杉矶×正常及上海午夜前后9组合，日期、08/19时段、日程、预约、确认、通知显示完全相同北京时间。',
'AI-interface-experience-16':'同弹窗原内容与仅主题首尾空格复用key，主题/日期/start/end/人数单字段改变均新key；真实提交后仅丢响应，再次提交读回同记录同通知。',
'AI-notification-center-7':'无通知空态→真实确认→真实取消→全部已读仍可阅读；三时区正文、时间、预约编号一致。',
'AI-reservation-management-3':'确认与取消预约在开始前1秒、开始、结束前1秒、结束、结束后1秒共五精确时点状态分别断言；取消状态不被时间覆盖。',
'AI-reservation-management-4':'交错创建时间与ID、未来/过去取消、浏览器跨结束边界后比较真实API记录独立排序，upcoming开始升序/history开始降序正确。',
'AI-reservation-management-10':'本人及admin team真实视图，未来确认可取消、进行/结束/取消无按钮；确认文案包含主题时间房名；保留不写、再次明确确认才取消。无权API拒绝由API tester交叉证据合并。',
'AI-room-discovery-5':'容量3/4/5/6/7/8/9/11/12/13、停用大室，真实4/6/8/12×四设备及未选共25组合逐ID独立计算；6从无/4/8切入；真实零匹配与清除恢复。',
'AI-room-discovery-6':'U/V各保存两日可识别主题，A/U/V三身份×两日实际展开收起再展开，预约时间owner与本人/管理员原文、他人已预约匹配。',
'AI-room-discovery-7':'48格逐索引核对08首格、10:00两格、邻接10:30、19:45末格；取消中间预约后只释放8/9保留10；空日无占用。',
'AI-room-discovery-8':'941完整重跑：normal U D/D+1；停服legacy H1-H6+异队记录integrity/FK检查后U D−1/D/D+1、V D、B D；各支真零匹配与清除后统计不变，7支独立身份/日期截图。',
'AI-room-discovery-9':'管理员实际调整资料确保12人+电话零匹配，显示无匹配空态仍有筛选；清人数出现匹配，清设备恢复全部启用房间。',
'AI-team-administration-7':'唯一管理员自降真实拒绝仍admin；提升第二管理员后自降成功，重新session→spaces无manage，刷新仍成员，后续管理读取403。',
'AI-WB-ui-start-session-errors':'有效cookie刷新恢复、真实失效401登录，session503/断网/非JSON独立故障展示连接错误，恢复后实际刷新成功。',
'AI-WB-ui-api-error-session-transition':'四真实401弹窗/读取路径关闭工作空间；登录真实错密统一错误；非JSON/503/无error字段分别错误与默认反馈，预约/房间输入仍保留。',
'AI-WB-ui-login-navigation':'四示例仅填表零登录；A team scope退出→U/B后spaces/mine及members空、异队不含旧队rooms；四角色入口和真实身份核对。',
'AI-WB-ui-load-parallel-error':'逐rooms/bookings/notifications/members单失败、扣留单个请求不出现部分成功；恢复真实重载；无user直接调用真实loadPage无请求，manage成员网络仅管理员分支。',
'AI-WB-ui-filters-statistics':'201控件ID交集矩阵与941完整跨午夜统计零匹配/清除矩阵共同覆盖；H1相交不计本人起始日，取消与异队排除。',
'AI-WB-ui-room-timeline-agenda':'首末/邻接/取消48格，三身份两日日程内容；管理停用室可编辑、空设备基础空间，spaces停用无预约入口。',
'AI-WB-ui-timezone-format':'三时区×三跨日时点的真实日期/日程/预约/通知/取消文案一致并标UTC+8。',
'AI-WB-ui-booking-status-sort':'精确start/end状态、取消状态、升降序分组、本人/admin team、相同start不同ID、确认保留和明确取消均执行。',
'AI-WB-ui-notification-render':'零/1/2/已读空徽标与禁用、正文时间编号，read503/断网不假成功且保留未读、恢复实际读成功；105/100/3计数由api-r2通知实际UI矩阵补证。',
'AI-WB-ui-default-times':'88时间日期时区默认组合，加容量1默认人数1/max1与容量8人数2/max8、日期min/max与两房间说明。',
'AI-WB-ui-booking-draft-key':'同弹窗trim等价复用、五字段改动新key；真实已提交丢响应重放仅一预约通知；重开不同room新draft/key并小容量合法默认。',
'AI-WB-ui-submit-button-matrix':'登录/booking/room新增及编辑/cancel成功、4xx、503、断网、非JSON矩阵，等待禁用和恢复；真实业务拒绝补证；三成功写入随后reload失败仍明确错误，重载恢复。',
'AI-WB-ui-room-edit-draft':'编辑原五字段含activefalse/设备后实际PATCH读回，新建reset/默认active与容量、重名失败保留修正后实际POST；编辑实际重名失败再修正。',
'AI-WB-ui-role-demotion-reload':'唯一admin拒绝/合法他人晋升与自降后身份重读和入口撤除；另PATCH成功后session失败、reload失败均有可见错误并可恢复。',
'AI-WB-ui-logout-races':'退出503/网络失败恢复按钮且真实session有效；真实成功退出旧session401。root ui-races logout/relogin成功/失败旧响应矩阵补证；初305同步缺陷重跑记录保留。',
'AI-WB-ui-dialog-close-no-write':'三dialog×三关闭手势+内部点击，网络零业务写与独立SQLite快照不变；取消保留与重复打开可编辑。',
'AI-WB-ui-text-escaping':'真实room/name/location/title载荷与DB合成user/team/member/属性五特殊字符，错误/toast/确认textContent；DOM无新增可执行节点，其他成员主题仍脱敏。',
'AI-WB-ui-accessibility-focus':'桌面及手机完整键盘操作，主要表单和dialog可访问树，真实错误alert/成功status，focus outline和Escape返回按钮；仅浏览器等价语义检查，不宣称系统读屏器实测。',
'AI-WB-ui-responsive-breakpoints':'16临界宽度真实创建取消通知；三指定视口独立登录长内容完整路径；15断点补长room/location/member email管理表单与dialog边界均无页面横向溢出。'
}
# These are tester execution conclusions, not evidence review. Original attempts are immutable evidence.
for m in d['method_results']:
 mid=m['method_id']
 if mid in actual:
  m['status']='passed';m['actual']=actual[mid];m['evidence']=[x for x in m['evidence'] if not x.endswith('progress.json')]
  if mid=='AI-WB-ui-notification-render':m['evidence']+=['evidence/api-r2/notifications.json']
  if mid=='AI-WB-ui-logout-races':m['evidence']+=['evidence/ui-races/'+x+'.json' for x in ['logout-success','logout-failure','relogin-success','relogin-failure'] if (R/'evidence/ui-races'/f'{x}.json').exists()]
 else:m['actual']='由root/api tester负责并在统一run合并，UI子任务不替代其判定。'
# Keep externally owned scenarios for merge; never claim their absent results passed.
for s in d['results']:
 ms=[next(m for m in d['method_results'] if m['method_id']==k) for k in s['method_ids']];s['status']='failed' if any(m['status']=='failed' for m in ms) else ('passed' if all(m['status']=='passed' for m in ms) else 'unproven');s['actual']='；'.join(m['method_id']+'：'+m['actual'] for m in ms);s['evidence']=sorted(set(x for m in ms for x in m['evidence']))
d['execution_notes']={'source_changed':False,'self_review_written':False,'real_integration':'无第三方服务；真实应用HTTP+SQLite结果与前端受控错误展示分支分开说明。','frontend_fault_evidence':'301/502/404/604/605/703/801等JSON逐fault明确503/网络/非JSON等前端故障；不宣称这些为真实后端故障契约证明。','initial_attempts':['001-008初始CSP不兼容polling；101以后改为函数表达式完整重跑','305退出等待复用旧toast导致抢先断言；402完整重跑','401统计字符串4间解析错误；501重跑；独立审阅指出零匹配不足后941再完整重跑','901取消控件locator含种子预约严格歧义；911完整重跑','921服务推进49小时先触发会话过期未到目标409；931同日预约推进1小时完整重跑'],'retained_attempts':'未删除失败/未证明原始证据；上述为可定位harness/fixture问题，不将应用失败改成通过。'}
(R/'ui-results.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(E/'method-execution-summary.json').write_text(json.dumps({'methods':d['method_results'],'notes':d['execution_notes']},ensure_ascii=False,indent=2))
print({x:sum(m['status']==x for m in d['method_results']) for x in ['passed','failed','unproven']})
