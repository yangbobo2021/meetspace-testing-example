"""Repair independent review findings, design only."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];L=ROOT/'tests/delivery-acceptance';U=L/'design-updates/coverage-supplement-20261009'
read=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
methods=read(L/'methods.json');mm={m['id']:m for m in methods['items']}
marker='独立审阅R1澄清：'
assert marker not in mm['AI-WB-ui-logout-races']['actions'],'Do not apply design repair twice'
mm['AI-WB-ui-logout-races']['actions']+='\n'+marker+'旧加载必须由真实UI导航发起。先点击一个导航按钮并只暂存该次旧加载的一条真实成功rooms响应，使该Promise.all未完成；其余请求照常实际处理。再点击第二个真实导航按钮，允许最新加载的所有真实请求完成，回到spaces（预约弹窗）、manage（会议室弹窗）或bookings（取消弹窗）目标页面，确认按钮可见可点、state.loading=false、旧请求仍暂存。旧/新请求使用不同匿名标签，不能仅靠路径区分。然后原生点击退出，暂存实际服务处理完成的logout成功响应；原生点击目标业务按钮确认dialog.open=true，再释放logout，最后释放旧加载的成功或非401错误结果。旧加载不得用控制台loadPage、人工fetch或绕过inert的DOM.click代替。'
cookie=('撤销项的确定方法：在独立HTTP Cookie容器内携带被测UI当前旧会话Cookie，使用同一个公开账号发起真实成功POST /api/login，'
        '验证服务器删除旧摘要并创建新会话；新Set-Cookie只被该独立容器接收，绝不写入被测浏览器。被测浏览器仍携带原旧Cookie，'
        '因此其后续目标业务请求才实际返回401。令牌值不写证据，仅记录匿名句柄及摘要存活/删除事实。'
        '不能在同一被测浏览器完成重新登录后把更新后的有效Cookie误当失效会话。')
for mid in ['AI-WB-ui-mark-read-session-expiry','AI-WB-ui-role-update-session-expiry']:
    mm[mid]['preconditions']+='\n'+marker+cookie
mm['AI-WB-booking-response-loss-replay']['preconditions']+='\n准备同团队两个都可合法预约的空闲会议室，保证各内容变更单独仍满足格式/容量/时间条件。'
mm['AI-WB-booking-response-loss-replay']['actions']+='\n异内容拒绝必须逐一单维覆盖room_id、去首尾空格后的title、绝对start、绝对end、attendees全部五维，不能只测主题/开始/人数；每项使用合法变化值并核对K原记录及通知不变。另用仅首尾空格变化与等价UTC时刻作相同内容重放对照，避免把规范化等价值误当异内容拒绝。'
write(L/'methods.json',methods)
f=U/'defensive-reachability.json';d=read(f)
for row in d['items']:
    if row['id']=='COV-DEF-004':row['static_basis']=row['static_basis'].replace('bookingsContent117','bookingsContent123')
write(f,d)
write(U/'repair-round-01.json',{'source':'/root/coverage_scenario_reviewer independent round 01 findings',
    'status':'analyst_repaired_pending_independent_revalidation',
    'findings':['DEF004源码行号117应为123','退出待处理旧加载与已载入业务按钮需要真实UI导航时序','通知/角色401撤销必须隔离新Cookie不写被测浏览器','预约响应丢失后的异内容重试需明确room_id/title/start/end/attendees五维与规范化对照'],
    'changed_method_ids':['AI-WB-ui-logout-races','AI-WB-ui-mark-read-session-expiry','AI-WB-ui-role-update-session-expiry','AI-WB-booking-response-loss-replay'],
    'execution_status':'not_executed','app_acceptance':'not_established'})
print('Independent round-01 findings repaired; review still required')
