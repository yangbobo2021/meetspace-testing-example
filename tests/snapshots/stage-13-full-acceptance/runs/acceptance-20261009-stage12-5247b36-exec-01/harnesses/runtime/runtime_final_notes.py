# Additional observed coverage from same-revision continuation; loaded by result compiler.
extra={
 'AI-application-runtime-3':(['all-seed-logins','seed-matrix'],'8种空库/时钟/系统时区组合均执行四个真实账号登录，完整身份/房间/预约HTTP记录及两团队/五室/三会议快照；日期均2030-04-11。'),
 'AI-application-runtime-4':(['real-process-restarts','two-days-process-restart'],'真实服务子进程两次重启及T+2天启动，原改名/新增室/取消状态/绝对会议日期完整数据库快照不变并API读回。'),
 'AI-application-runtime-5':(['real-process-restarts'],'真实子进程两次重启前后团队/角色/室/预约/取消时间/通知内容与已读快照一致，API读回及真实UI截图、退出刷新路径完成。'),
 'AI-application-runtime-6':(['real-process-restarts'],'重启前后匿名和登录健康JSON均为ok、1.0.0-rc.1、Asia/Shanghai。'),
 'AI-application-runtime-7':(['storage-errors','real-integrity','required-external-locks','extra-envelope-dispatch'],'真实业务错误、真实唯一性冲突、真实SQLite写锁及三异常类双入口各两次均保持JSON稳定code，无内部故障哨兵或凭据。'),
 'AI-application-runtime-8':(['storage-errors','real-integrity','required-external-locks'],'IntegrityError/OperationalError/RuntimeError在真实dependency边界双入口各2次，分别409/503/500；真实外部写锁503及释放后成功独立核验。'),
 'AI-application-runtime-9':(['write-matrix','required-external-locks','all105-success-peer-isolation'],'14种写状态真实DML后和commit前失败均独立快照回滚、服务重启不变、同请求重试成功；含创建/本人及管理员取消、房间五字段/新增启停状态、角色双向、105+通知/其他用户不变、登录旧删新插与退出；四外部锁矩阵也完成。'),
 'AI-identity-session-1':(['missing-formats'],'补完逐字段缺省、无效格式不计数、真实匹配1/160邮箱及1/256密码边界合成账号，结合原类型/空白/越界/trim大小写矩阵全部通过。'),
 'AI-identity-session-3':(['ui-switch-and-errors'],'真实UI不存在邮箱/错误密码同文案拒绝，已有U/A各目标错误登录拒绝且未切换；正确切换跨同队/跨队实际成功作为对照。'),
 'AI-identity-session-5':(['invalid-session-matrix','ui-switch-and-errors'],'12工作空间读写入口×无会话/错误token/已撤销/精确到期均401且独立数据库不变；浏览器退出刷新回登录界面。'),
 'AI-identity-session-6':(['two-expiry'],'两个独立同账号会话分别在8h−1s/8h/8h+1s真实身份/房间/到期写请求，业务访问和服务重启不延长截止。'),
 'AI-identity-session-7':(['cross-team-first-write','ui-switch-and-errors'],'补完跨团队新团队室首请求创建及旧团队室首请求拒绝；结合20条首业务请求矩阵、旧当前会话撤销和其他会话保留、实际UI切换/角色页面/退出证据。'),
 'AI-identity-session-8':(['real-process-restarts'],'实际点击UI退出、Cookie删除、根页刷新返回登录及同源子路径HttpOnly；原HTTP旧令牌重放拒绝、其他会话仍有效。'),
 'AI-identity-session-9':(['complete-rates','source-ip-and-rate','missing-formats'],'精确59.999/60/60.001、交替/全成功/全失败/格式插入、跨自然分钟、错开窗口、同时8次在60秒退出、429不延长均通过；第二本机IPv4来源真实独立且原IP仍429。'),
 'AI-identity-session-12':(['ui-switch-and-errors','real-process-restarts'],'真实UI首次与五种同队/跨队/升降权切换Cookie属性、浏览器存储、根/子路径document.cookie不可读、受保护读取新身份、退出无路径残留及刷新全部通过。')}
for mid,(gs,text) in extra.items():
 old=notes[mid];notes[mid]=('passed',list(dict.fromkeys(old[1]+gs)),text)
for mid in ['AI-storage-exception-boundary','AI-transaction-midwrite-boundary','AI-other-writes-failure-boundary','AI-new-room-write-failure-boundary']:
 gs=['faults','storage-errors','write-matrix','required-external-locks','all105-success-peer-isolation']
 notes[mid]=('passed',gs,'已追加对应所有可操作入口/状态的真实HTTP与SQLite失败/回滚/重启/恢复矩阵；'+notes['AI-application-runtime-9'][2]+' 新增室单条INSERT没有中间DML间隙，F2不适用；F1/F3真实执行，测试器无补偿回滚。')
for w,k in map_wb.items():
 if w in ['runtime-entry','password-derivation','login-switch-and-cookies']:continue
 gs=notes[k][1]+['extra-envelope-dispatch','session-dynamic-join-cleanup','wrong-route-methods','missing-length']
 notes['AI-WB-'+w]=('passed',list(dict.fromkeys(gs)),notes[k][2]+' 补充完整入口/异常/动态联接检查，实际app/server.py只读行覆盖及SQL事务轨迹保存在各追加证据trace.json。')
notes['AI-WB-seed-failure-retry']=('passed',['seed-faults','seed-final'],'原9个部分/全部INSERT后故障加最终seed commit失败，独立连接均无部分团队/用户/室/会议，移除故障后2/4/5/3完整播种；已有团队库只保留原队且不补种。')
notes['AI-WB-password-derivation']=('unproven',['password','ui','all-seed-logins'],'真实初始化/认证与独立scrypt重算通过；强制系统熵因果重放及所有I/O出口追踪因dtruss/SIP、fs_usage/root权限阻塞，不能完整证明该方法。')
notes['AI-WB-login-switch-and-cookies']=('unproven',['identity','first-request-switch','ui-switch-and-errors','cross-team-first-write'],'实际登录/切换/cookie/失效隔离完成；强制有效系统熵因果和全部存储出口观测受权限阻塞，不能完整证明该方法。')
notes['AI-WB-runtime-entry']=('blocked',[], '已尝试CLI默认/参数覆盖，但固定端口被其他服务占用且127.0.0.2不可绑定，没有目标归属的监听证据；未将别的服务响应当通过。见startup-and-instrumentation.json。')
