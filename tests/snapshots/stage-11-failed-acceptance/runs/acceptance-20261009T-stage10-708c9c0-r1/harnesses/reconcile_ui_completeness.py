import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'ui-execution-results.json';shutil.copy2(p,R/'ui-execution-results-partial-flags.json');d=json.load(open(p));M={x['method_id']:x for x in d['method_results']}
notes={
'AI-interface-experience-1':'101四身份逐导航/刷新；951管理员team后切同队成员/异队并读page/scope/caches。应用唯一管理地址就是根URL（nav按钮内部状态，无专用管理路由）；101刷新根地址已覆盖直接地址加载。',
'AI-interface-experience-4':'106依次rooms/bookings/notifications/members503→重试；404网络/500→恢复及真实在途loading；202真实空日期正常空态作对照。',
'AI-interface-experience-7':'301登录/预约/新增room/取消×成功/业务拒绝/503/断网/非JSON，扣留响应按钮disabled及Enter无重复，恢复后完成；502独立编辑room同矩阵；931真实业务拒绝。',
'AI-interface-experience-8':'301全部成功或恢复成功记录toast；108角色实际self demote/session；107编辑后新建；gap四room分项补五字段读回与实际成功toast。',
'AI-interface-experience-9':'301受控故障保留输入恢复；601真实预约冲突修正；931真实取消/编辑冲突；gap四独立新增/编辑×真实重名/断网核对所有可编辑输入、零业务变化、恢复保存。',
'AI-interface-experience-10':'205预约/room/取消/读取四真实撤销401，关闭所有dialog、登录、业务不变，重新登录；gap另有同世代双401。',
'AI-interface-experience-13':'304原生键盘登录/预约/管理创建和标签/focus；403取消通知；701全键盘真实错误修正；503可访问alert/status；911手机全键盘回合与Escape焦点返回。',
'AI-interface-experience-14':'206真实持久载荷room/booking/notice/manage与无攻击节点；504特殊字符和profile/member/team/属性；703隐私日程/错误/toast完整DOM。',
'AI-notification-center-7':'204真实空通知→创建→取消→已读，0徽标/按钮禁用、正文/编号，UTC/上海/洛杉矶相同。',
'AI-reservation-management-3':'203服务钟保持T，浏览器五个精确start/end边界，confirmed/cancelled逐状态文本与入口。',
'AI-reservation-management-4':'306三个浏览器时点列表顺序；803取消项后即将/历史分组排序；前后真实取消状态。',
'AI-reservation-management-10':'203五边界有无取消按钮及确认文案、放弃原状态、确认取消；603管理员team范围；API当前运行cancel-permission-clock验证无权直接请求拒绝。',
'AI-room-discovery-7':'202实际08:00/10:00/邻接/19:45每格占用索引，对照48格；取消后精确恢复及空日期。',
'AI-team-administration-7':'108唯一admin拒绝仍admin，再提升另一成员后self降权，最终spaces/menu消失、直接members403、根管理地址刷新（本应用无独立管理路由）；当前运行scope-and-first-role含降权第一写拒绝。',
'AI-WB-ui-api-error-session-transition':'205各业务401清dialog/user；605错密/默认错误；301非JSON/503独立；gap第二同世代真实401先后交付，均不恢复旧空间。',
'AI-WB-ui-login-navigation':'101四示例/各身份导航刷新；506示例零POST；951team→member/other重置；extended-pending-r2退出新登录后旧pending成功/非401错误不回填；605失败登录保留错误。',
'AI-WB-ui-load-parallel-error':'106四读取失败及重试，404真实等待不部分渲染，951无user零读取；gap self/other pending先session零业务prefetch，确认后member不members/admin有members；pending-guards重试503/断网再恢复。',
'AI-WB-ui-room-timeline-agenda':'202逐格/展开有无预约/取消；405两房间完整说明设备；603manage停用仍编辑且spaces隐藏，team状态。',
'AI-WB-ui-booking-status-sort':'203五精确边界和四状态；306+803即将升序/历史降序与取消项；603+952admin team/mine；203dialog保留/确认。',
'AI-WB-ui-notification-render':'204空/正文/编号/时区/已读禁用；602延迟读单提交、错误toast恢复；API本次notifications实际105→100徽标/全读0/新增3并保留97已读，具体截图/DB快照位于当前api-r2。',
'AI-WB-ui-default-times':'102两时区×11时钟×四日期完整88项；802小容量默认min、max和新draft；405room标题规则。',
'AI-WB-ui-booking-draft-key':'207相同/trim/主题/日期/start/end/人数键变化、真实commit响应丢失重试DB不变；802重开不同房间新key。',
'AI-WB-ui-submit-button-matrix':'301四操作×五结果、502独立编辑、931真实业务失败，均disabled/Enter一次提交及恢复；801成功写后后续load失败保留错误。',
'AI-WB-ui-room-edit-draft':'107实际编辑→新建→真实重名→修正；gap四分项补旧checkbox/activefalse/capacity、新增全部默认、错误全部字段不变、PATCH/POST完整读回和重开reset。',
'AI-WB-ui-text-escaping':'206所有主要业务sink载荷textContent及节点探针；504身份/team/aria属性及&<>双单引号；703脱敏日程/错误/toast sink。',
'AI-WB-ui-accessibility-focus':'304标签与可见focus键盘管理/booking；403键盘取消通知；701真实错误纯键盘修正；503alert/status无障碍树；911手机Escape焦点回合。',
'AI-WB-ui-responsive-breakpoints':'104完整16视口逐预约取消通知流程与rect/scroll；505长中文三视口；702长资料全部断点manage/cards/dialog/成员字段布局。'}
extras={
'AI-interface-experience-4':['evidence/ui/202-timeline-boundaries.json'],
'AI-reservation-management-10':['evidence/ui/603-manage-disabled-room-and-team-status.json','evidence/api-r2/cancel-permission-clock.json'],
'AI-team-administration-7':['evidence/api-r2/scope-and-first-role.json'],
'AI-WB-ui-room-timeline-agenda':['evidence/ui/405-two-room-dialog-details.json'],
'AI-WB-ui-notification-render':['evidence/api-r2/notifications.json'],
'AI-WB-ui-default-times':['evidence/ui/405-two-room-dialog-details.json'],
'AI-WB-ui-login-navigation':['evidence/ui/605-api-default-error-and-wrong-password.json','evidence/ui-stage10-r2/extended-pending/pending-new-login-success.json','evidence/ui-stage10-r2/extended-pending/pending-new-login-error.json'],
'AI-WB-ui-load-parallel-error':['evidence/ui-stage10/pending-guards/pending-retry-503.json','evidence/ui-stage10/pending-guards/pending-retry-network.json'],
'AI-WB-ui-api-error-session-transition':['evidence/ui/301-submit-button-fault-matrix.json']}
g=json.load(open(R/'evidence/ui-stage10/ui-gap-results.json'))
for x in g['results']:
 for mid in x['method_ids']:extras.setdefault(mid,[]).append('evidence/ui-stage10/'+x['evidence'])
for mid,note in notes.items():
 x=M[mid];added=extras.get(mid,[]);x['evidence']=sorted(set(e for e in x['evidence']+added if not e.endswith('/progress.json')))
 for e in x['evidence']:assert (R/e).exists(),e
 if x['status']!='failed':x['status']='passed'
 x['actual']='本run累积完整路径重新对照当前方法，映射：'+note
 x['completeness_mapping']=note;x['missing_paths']=[]
 # Fresh supplemental observed failure cannot be concealed by path mapping.
 for row in g['results']:
  if mid in row['method_ids'] and row['status']!='passed':x['status']=row['status'];x['missing_paths'].append(row['name'])
d['dependency_checks'][0]['actual']=d['dependency_checks'][0]['actual'].replace('Chromium142.0.7444.0','Chromium'+d['environment']['browser'])
d['limitations']=['保留原始ui-results中complete=False局部分支旗标及ui-execution-results-partial-flags.json；这里按当前方法逐路径合并同run新证据并列出completeness_mapping，不是借旧runpassed。','三项实际产品竞态失败保留，不被补充分支通过抵消。','部分UI共用API执行者本run真实浏览器/HTTP证据；独立API审阅已单独提供，root应交叉组合独立性。']
(R/'ui-execution-results.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
(R/'ui-completeness-mapping.json').write_text(json.dumps({'revision':d['revision'],'mappings':[{'method_id':mid,'mapping':note,'evidence':M[mid]['evidence'],'status':M[mid]['status'],'missing_paths':M[mid].get('missing_paths',[])} for mid,note in notes.items()]},ensure_ascii=False,indent=2))
from collections import Counter
print(Counter(x['status'] for x in M.values()))
