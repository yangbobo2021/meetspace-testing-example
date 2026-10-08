import json
from pathlib import Path
L=Path(__file__).resolve().parents[1];R=L/'runs/acceptance-20261008T-full-0b386b4-r1';O=R/'evidence/runtime'
scenarios=json.load(open(L/'scenarios.json'))['items'];methods={x['id']:x for x in json.load(open(L/'methods.json'))['items']}
wb=['runtime-entry','seed-empty-existing','password-derivation','persistence-restart','health-static-dispatch','request-origin','json-envelope','errors-and-response','transaction-failure-matrix','session-join','session-expiry','login-window-lock','login-switch-and-cookies','logout-revocation','route-authorizations','seed-failure-retry','login-format-boundaries']
selected=[x for x in scenarios if x['id'].startswith(('BB-application-runtime-','BB-identity-session-')) or x['id'] in ['WB-'+k for k in wb]]
groups={g['group']:g for g in json.load(open(O/'branches.json'))}
supp=json.load(open(O/'supplement/branches.json'));groups.update({x['group']:x for x in supp})
base_e=['evidence/runtime/branches.json','evidence/runtime/execution-meta.json','evidence/runtime/execution.log']
notes={
 'AI-application-runtime-1':('blocked',['health'],'已尝试标准库 -S 默认CLI；固定端口有其他进程响应、未取得本次目标进程监听归属；另缺Python3.11环境，不能证明完整默认启动路径。'),
 'AI-application-runtime-2':('blocked',[],'四种参数命令均已尝试；127.0.0.2不可绑定，固定端口返回并非本次进程的响应，未验证库隔离及业务重启。'),
 'AI-application-runtime-3':('unproven',['seed-matrix','ui'],'8种空库/时刻/系统时区种子矩阵已执行且日期正确；4账号UI登录仅在标准时刻执行，未在每一种种子组合登录全部账号。'),
 'AI-application-runtime-4':('unproven',['persistence'],'同日和两天后Store重开数据库快照一致，含改名、新室、取消；缺真正停进程重新启动并API读回的完整路径。'),
 'AI-application-runtime-5':('unproven',['persistence'],'角色、会议室、预约、取消、通知已读快照经Store重开一致；缺两次服务进程重启后的UI/API全量读回。'),
 'AI-application-runtime-6':('unproven',['health'],'匿名与登录健康JSON字段正确；尚缺重启后重复健康查询。'),
 'AI-application-runtime-7':('unproven',['health','formats','faults'],'实际业务错误和3类存储异常JSON代码检查通过；缺外部写锁与完整原定错误矩阵。'),
 'AI-application-runtime-8':('unproven',['faults'],'3类依赖异常实际在SQLite写后抛出并映射到409/503/500；尚缺每类2次/新增室和创建预约双入口以及外部写锁矩阵。'),
 'AI-application-runtime-9':('unproven',['faults'],'8种写入口均执行真实DML后/commit前异常并从独立连接核对回滚；未完成全部105通知、双向角色、五字段、管理员代取消和重启后成功重试矩阵。'),
 'AI-identity-session-1':('unproven',['formats'],'类型、空白、长度1/上界/超界和大小写trim实际HTTP检查通过；缺逐字段缺省输入与普通登录对照完整快照矩阵。'),
 'AI-identity-session-2':('passed',['ui','identity'],'4个公开账号均通过真实浏览器填写登录、查询完整身份、实际房间页面和刷新，截图及UI记录已保存。'),
 'AI-identity-session-3':('unproven',['identity'],'U/A已有会话各4类错误账号/密码被拒且状态未变；尚缺逐分支UI文案与全部正确切换对照。'),
 'AI-identity-session-4':('passed',['identity'],'4身份返回完整姓名/邮箱/团队/角色/版本/时区；A升降U后同一会话下一业务请求权限和身份随之变化。'),
 'AI-identity-session-5':('unproven',['authorizations','expiry','identity'],'多业务路由缺会话/无效token拒绝且快照不变，另有撤销/过期探针；未将每种失效状态×每入口笛卡尔矩阵全部执行。'),
 'AI-identity-session-6':('unproven',['expiry'],'精确28799/28800/28801秒身份、房间及到期写请求断言通过且截止不滑动；每个分支只建立1会话，未完成方法要求的两会话独立对照。'),
 'AI-identity-session-7':('unproven',['identity','first-request-switch'],'20项切换组合首业务请求及旧会话撤销/其他浏览器保留通过；跨团队创建本人预约及旧团队室拒绝、UI生命周期分支未完成。'),
 'AI-identity-session-8':('unproven',['identity'],'真实HTTP退出清Cookie属性、旧token重放拒绝且另一会话可用；尚未点击UI退出并刷新路径。'),
 'AI-identity-session-9':('unproven',['rate'],'59.999/60/60.001精确端点、交替成功失败、并发9请求均符合；缺第二来源IP、跨自然分钟、格式插入和全成功/全失败独立矩阵。'),
 'AI-identity-session-10':('passed',['envelopes'],'8个实际修改入口各自执行正确、缺/0/2标记、scheme/host/port异源、无Origin及缺标记异源组合；所有拒绝后独立数据库快照不变。'),
 'AI-identity-session-11':('passed',['envelopes'],'8入口独立基线执行有效对象、错误媒体/缺媒体、所有非对象类型/损坏JSON、0字节/1字节/{}、65536/65537字节，中文载荷按UTF8字节构造；成功/业务拒绝及无副作用断言通过。'),
 'AI-identity-session-12':('unproven',['ui','identity'],'4个UI登录cookie属性、document.cookie不可读及HTTP退出属性检查通过；缺各切换后浏览器存储、子路径及无残留矩阵。'),
 'AI-identity-session-13':('unproven',['password','ui'],'实际种子密码4账号独立scrypt重算匹配、错误密码不匹配、随机盐互异及真实UI登录；完整OS熵因果与全持久化出口范围未证。'),
 'AI-identity-session-14':('unproven',['identity','expiry'],'真实会话相互隔离、切换撤销、8小时边界已探测；缺独立令牌摘要核对及完整OS熵/存储范围。')}
map_wb={'runtime-entry':'AI-application-runtime-2','seed-empty-existing':'AI-application-runtime-3','password-derivation':'AI-identity-session-13','persistence-restart':'AI-application-runtime-5','health-static-dispatch':'AI-application-runtime-6','request-origin':'AI-identity-session-10','json-envelope':'AI-identity-session-11','errors-and-response':'AI-application-runtime-8','transaction-failure-matrix':'AI-application-runtime-9','session-join':'AI-identity-session-4','session-expiry':'AI-identity-session-6','login-window-lock':'AI-identity-session-9','login-switch-and-cookies':'AI-identity-session-7','logout-revocation':'AI-identity-session-8','route-authorizations':'AI-identity-session-5','seed-failure-retry':'AI-application-runtime-9','login-format-boundaries':'AI-identity-session-1'}
for w,k in map_wb.items():
 status,g,n=notes[k];notes['AI-WB-'+w]=('unproven',g,n+' 白盒联合行覆盖已保存，但逐项分支追踪/扩展矩阵尚不完整。')
notes['AI-WB-seed-failure-retry']=('unproven',['seed-faults'],'teams/users/rooms部分与全部、bookings每条共9处实际INSERT后故障均回滚且重试完整2/4/5/3；缺最终种子commit失败和已有团队库分支。')
for k in ['AI-salt-entropy-dependence','AI-password-persistence-scope','AI-token-entropy-and-storage-scope','AI-subsequent-session-entropy']:
 notes[k]=('blocked',['password','identity'],'已尝试dtruss与fs_usage观测设施预检：SIP/权限限制、必须root；未能验证有效系统熵重放或覆盖mmap/已删除文件/子进程全部持久化出口，不能由盐/令牌不同推出随机因果或存储完整。')
for k in ['AI-storage-exception-boundary','AI-transaction-midwrite-boundary','AI-other-writes-failure-boundary','AI-new-room-write-failure-boundary']:
 notes[k]=('unproven',['faults'],'已执行对应真实HTTP写入后的SQLite异常和commit前失败，独立连接确认回滚；缺方法规定的全部状态/入口/重复、完整重启成功重试，详见枝项，未补偿删除业务状态。')
exec((Path(__file__).with_name('runtime_final_notes.py')).read_text())
for directory in ['completion','finish','edges','storage-final']:
 for g in json.load(open(O/directory/'branches.json')):groups[g['group']]=g
ms=[]
for mid in sorted({m for s in selected for m in s['method_ids']}):
 status,gs,actual=notes.get(mid,('unproven',[],'方法尚无完整证据。'))
 ev=list(base_e)
 for directory in ['completion','finish','edges','storage-final']:
  ev.extend(['evidence/runtime/'+directory+'/branches.json','evidence/runtime/'+directory+'/trace.json'])
 if 'ui-switch-and-errors' in gs:ev.extend('evidence/runtime/finish/'+p.name for p in (O/'finish').glob('*.png'))
 if 'real-process-restarts' in gs:ev.extend('evidence/runtime/completion/'+p.name for p in (O/'completion').glob('*.png'))
 if any(g in ['seed-matrix','authorizations','first-request-switch'] for g in gs):ev.append('evidence/runtime/supplement/branches.json')
 if 'ui' in gs:ev.extend(['evidence/runtime/ui-results.json']+['evidence/runtime/ui-'+a+'.png' for a in ['admin','alice','bob','other']])
 if status=='blocked':ev.append('evidence/runtime/startup-and-instrumentation.json')
 failures=[x for g in gs if g in groups for x in groups[g]['checks'] if x.get('passed') is False]
 if failures:status='failed';actual+=' 实际失败断言：'+str(failures)
 ms.append({'method_id':mid,'status':status,'actual':actual,'branch_groups':gs,'evidence':ev,'integration_mode':'real_local_app_dependency_fault_adapter' if 'faults' in gs else 'real_local_app','environment':'macOS arm64; Python 3.12.4; SQLite stdlib; Chromium 143.0.7499.4 via Playwright; server datetime.now/time.time fixed to 2030-04-10T09:00:00+08:00 or recorded exact boundary; browser clock independently installed; real local HTTP listeners; source revision pinned'})
by={m['method_id']:m for m in ms};results=[]
for s in selected:
 rows=[by[x] for x in s['method_ids']];status='failed' if any(x['status']=='failed' for x in rows) else 'passed' if all(x['status']=='passed' for x in rows) else 'blocked' if all(x['status']=='blocked' for x in rows) else 'unproven'
 results.append({'scenario_id':s['id'],'status':status,'method_ids':s['method_ids'],'actual':'；'.join(x['method_id']+'：'+x['actual'] for x in rows),'evidence':sorted({e for x in rows for e in x['evidence']})})
report={'revision':'0b386b4bd37b01eb996c5e74215ab1a4463a9487','run_id':R.name,'results':results,'method_results':ms,'summary':{'scenario_count':len(results),'method_count':len(ms),'executed_assertions':sum(sum('passed'in x for x in g['checks']) for g in groups.values()),'failed_assertions':sum(sum(x.get('passed') is False for x in g['checks']) for g in groups.values()),'note':'Partial matrix probes are not full method passes. Sandbox-denied initial attempt retained separately; final target execution did not change source.'}}
(R/'runtime-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report['summary']));print({s:sum(x['status']==s for x in results) for s in ['passed','failed','unproven','blocked']})
