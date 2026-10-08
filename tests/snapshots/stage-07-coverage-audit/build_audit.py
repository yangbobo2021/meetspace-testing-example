"""Build the coverage audit and gap inventory, without editing acceptance ledgers."""
import ast
import hashlib
import html
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
load = lambda name: json.loads((BASE/name).read_text())
write = lambda name, obj: (BASE/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
backend = load('backend-coverage.json')
frontend = load('frontend-coverage.json')
context = load('audit-context.json')
ui_context = load('ui-replay-context.json')
extra_context = load('extra-replay-context.json')
ledger = ROOT/'tests/delivery-acceptance'
scenarios = {x['id']:x for x in json.loads((ledger/'scenarios.json').read_text())['items']}
methods = {x['id']:x for x in json.loads((ledger/'methods.json').read_text())['items']}
requirements = {x['id'] for x in json.loads((ledger/'requirements.json').read_text())['items']}

category_labels={'missing_fault_mode':'遗漏故障模式','missing_lifecycle_mode':'遗漏生命周期模式','existing_design_execution_gap':'已有设计，执行未到达','missing_state_combination':'遗漏状态组合','missing_input_mode':'遗漏输入模式','scope_gap_outside_instrumented_file':'测量范围之外的入口'}
groups = []
def gap(number, title, category, priority, locations, scenario_ids, reqs, why, preconditions, matrix, expected, evidence):
    assert all(s in scenarios for s in scenario_ids), scenario_ids
    assert all(r in requirements for r in reqs), reqs
    method_ids = sorted({m for s in scenario_ids for m in scenarios[s]['method_ids']})
    assert all(m in methods for m in method_ids)
    groups.append({'id':f'COV-GAP-{number:03}', 'title':title, 'category':category, 'priority':priority,
                   'status':'proposed_unexecuted', 'code_locations':locations,
                   'existing_scenario_ids':scenario_ids, 'existing_method_ids':method_ids,
                   'requirement_ids':reqs, 'finding':why, 'preconditions':preconditions,
                   'operation_matrix':matrix, 'expected':expected, 'evidence_expected':evidence})

gap(1, '响应写入时客户端断开及提交后重试', 'missing_fault_mode', 'P1',
    ['app/server.py:259-260'], ['WB-errors-and-response', 'BB-reservation-creation-11'],
    ['application-runtime-7', 'application-runtime-9', 'reservation-creation-11'],
    '260行零命中；现有异常方法没有BrokenPipeError/ConnectionResetError模式。后端分支计数不会列出每一种except异常。',
    '隔离真实服务、独立数据库及有效身份；验证故障位于socket响应写入，不能替换dispatch或预约业务函数。',
    ['正常响应写入触发BrokenPipeError', '正常响应写入触发ConnectionResetError',
     '预约已提交、响应未收到就断开；同一请求标识与完全相同内容重试'],
    '服务进程仍能处理后续正常请求；断开不被包装成业务成功证据；已提交预约重试返回原记录，预约和通知只各增加一条；未提交故障遵循事务回滚要求。',
    'TCP事件或I/O依赖故障到达记录、260行命中、提交时间与断开顺序、前后独立数据库快照、健康请求及重试响应。')
gap(2, '真实CLI收到Ctrl+C后关闭监听并保持持久数据', 'missing_lifecycle_mode', 'P2',
    ['app/server.py:492-495'], ['WB-runtime-entry', 'BB-application-runtime-4'],
    ['application-runtime-2', 'application-runtime-4'],
    '492、493、495行零命中；现有main正常启动路径有覆盖，但子进程主要通过SIGTERM结束，未证明KeyboardInterrupt/finally。',
    '真实python -m app.server子进程、新库、显式随机端口；记录PID和该进程拥有的监听。',
    ['建立一条持久业务记录→向服务PID发送SIGINT→等待退出→同库同端口重新启动'],
    '进程正常响应中断，关闭监听；同端口可重新启动，原业务资料保持一致；不将该探针替代未完成的默认端口和Python3.11矩阵。',
    '真实命令/PID、信号、退出码、492/493/495行计数、端口释放和重启API读回及数据库快照。')
gap(3, '三种弹窗的右侧、上下侧及矩形内空白点击', 'existing_design_execution_gap', 'P2',
    ['web/app.js:258 / branch85[1], branch86[1,2,3]'], ['WB-ui-dialog-close-no-write'],
    ['interface-experience-11', 'reservation-management-10'],
    '原场景已要求矩形内外；实际外部点击集中在左上(2,2)，短路后右侧/上侧/下侧条件均未求值；内部只点击子元素，未进入event.target===dialog的矩形内空白分支。',
    '分别打开booking-dialog、room-dialog、confirm-dialog；保留未提交输入；实际浏览器指针事件。',
    ['在rect右侧点击', '横坐标位于rect范围、纵坐标在rect上侧点击',
     '横坐标位于rect范围、纵坐标在rect下侧点击',
     '矩形内dialog自身padding空白点击，确认event.target===dialog；保留左侧、子元素、X及Escape对照'],
    '矩形外关闭；矩形内空白及子元素不关闭；所有关闭动作均不产生业务POST/PATCH，数据保持不变。',
    '各弹窗getBoundingClientRect、事件target和clientX/Y、对应分支计数、dialog.open状态、零业务写请求和数据库快照。')
gap(4, '退出成功响应返回时仍有业务弹窗打开', 'existing_design_execution_gap', 'P1',
    ['web/app.js:162 / function66'], ['WB-ui-logout-races'],
    ['identity-session-8', 'interface-experience-10'],
    '162行被执行但forEach(d=>d.close())回调零命中；现有退出竞态测试退出时没有打开的弹窗，不能证明关闭逻辑。',
    '采用可操作的真实UI时序：先点击退出并暂存真实成功响应，再在工作空间仍显示时打开业务弹窗，最后释放响应；不可用DOM.click绕过原生modal对背景的inert限制。',
    ['预约弹窗打开时释放退出成功响应', '会议室编辑弹窗打开时释放退出成功响应',
     '取消确认弹窗打开时释放退出成功响应；分别保留旧加载迟到对照'],
    '所有业务弹窗关闭、回到登录；旧会话业务请求实际401；旧加载不得恢复空间，新登录不继续旧表单。',
    '退出请求与弹窗打开/响应释放事件顺序、回调命中、dialog.open/身份状态、旧会话拒绝、实际DOM与网络证据。')
gap(5, '标记全部已读遇到真实会话失效', 'missing_state_combination', 'P1',
    ['web/app.js:155 / branch73[1]'], ['WB-ui-notification-render', 'WB-ui-api-error-session-transition'],
    ['identity-session-5', 'interface-experience-10', 'notification-center-5'],
    'catch已覆盖但state.user为null的出口未命中；现有标已读故障主要是503/网络，此时用户仍存在。',
    '有未读通知的成员会话；真实会话到期或撤销；确保此次POST实际返回401，不以伪造响应证明服务器鉴权。',
    ['全部已读POST实际401→api清身份→wirePage.catch；重新合法登录作恢复对照'],
    '清身份回登录，不在catch中重新渲染旧工作空间；被拒绝的标已读请求不改变通知；不出现虚假成功提示。',
    '服务401、155行false出口、DOM/身份变化、通知只读快照及合法重新登录。')
gap(6, '角色更新后的身份401，以及自身降权后身份查询失败', 'missing_state_combination', 'P1',
    ['web/app.js:250-254 / branch83[1]'], ['WB-ui-role-demotion-reload', 'BB-team-administration-7'],
    ['team-administration-7', 'identity-session-5', 'interface-experience-10'],
    '254行user=null出口未命中；另外自身降权已经提交后/session的503或网络失败虽然可经过已覆盖行，却不是修改其他成员时的故障。首轮独立审阅已指出后一组合未证明。',
    '先建立第二个管理员，使当前管理员可合法降为成员；直连核对真实PATCH及最终角色；前端503/网络适配器只证明UI故障处理。',
    ['成员角色PATCH实际401', 'PATCH完成后/session实际401',
     '自身降权已真实提交后/session返回503→恢复并重试/刷新',
     '自身降权已真实提交后/session网络失败→恢复并重试/刷新'],
    '401清身份且不在catch重载旧空间；已提交角色不能假装回滚，失败明确可见；恢复重新读取身份后返回会议室页并移除管理员入口；真实服务继续拒绝降权身份的管理员操作。',
    'PATCH提交、后续/session故障位置与时序、后台实际role、254行false出口、菜单与选中页面、恢复动作及真实鉴权。')
gap(7, '用户清空日期筛选再选择合法日期', 'missing_input_mode', 'P2',
    ['web/app.js:143 / branch72[1]'], ['BB-room-discovery-2'], ['room-discovery-2'],
    'change事件value为空的出口未命中；API空日期已测试并发现缺陷，但UI清空输入是另一条guard路径。',
    '会议室页面已载入一个合法日期；使用日期控件原生清空操作及change事件。',
    ['清空日期控件→观察state.date、日程和网络→重新选择合法日期'],
    '清空动作不发送date=空字符串查询，不把非法输入作为选定业务日；随后合法日期查询与日程展示一致。空值提示或回填的具体交互未在需求中规定，本清单不新增该产品政策。',
    '控件值、state.date、change事件、143行false出口、请求参数及日程展示/恢复。')
gap(8, 'API未支持的HTTP方法穿过标准库入口', 'scope_gap_outside_instrumented_file', 'P1',
    ['BaseHTTPRequestHandler.handle_one_request / unsupported do_METHOD', 'app/server.py:Handler HTTP方法入口'],
    ['BB-application-runtime-7', 'WB-route-authorizations'], ['application-runtime-7', 'identity-session-5'],
    '应用文件branch100%不包含继承的标准库HTTP分派；DELETE/OPTIONS/PUT没有进入dispatch。额外独立诊断45次真实请求均501 text/html，而非稳定JSON错误；该新增探针未进入原有测试覆盖率。',
    '隔离真实HTTP服务，匿名、成员、管理员三种身份；有效同源和请求标识；不伪造API返回。',
    ['DELETE/OPTIONS/PUT × 匿名/成员/管理员 × /api/health、/api/rooms、/api/bookings、/api/members、/api/unknown'],
    '拒绝方法保持符合现有API错误契约的JSON error/code，不做业务写入；授权判断与方法拒绝的具体优先级不擅自新增要求。',
    '真实状态码、Content-Type、JSON结构与稳定code、业务数据库前后快照；标准库入口到达记录与应用dispatch未进入的说明。')

defensive = [
    {'id':'COV-DEF-001', 'location':'web/app.js:56 / branch9[1]', 'title':'登录catch找不到反馈DOM',
     'reason':'正常登录页保留目标节点；当前未证明可通过约定UI到达。先做可达性分析，必要时增加DOM契约/故障测试。'},
    {'id':'COV-DEF-002', 'location':'web/app.js:81 / branch20[0]', 'title':'renderShell在user为空时提前返回',
     'reason':'正常调用者已检查身份；可直接调用辅助函数验证guard，但不能当作真实业务场景通过。'},
    {'id':'COV-DEF-003', 'location':'web/app.js:95-96 / branch33[1]', 'title':'非法内部page枚举的默认内容',
     'reason':'所有导航入口使用固定合法枚举；单独内部状态防御测试，不对应新增业务需求。'},
    {'id':'COV-DEF-004', 'location':'web/app.js:99 / branch34[0]', 'title':'heading省略aside默认参数',
     'reason':'当前生产调用均传入参数；可作辅助函数测试，不能据此认定主要业务功能漏测。'},
    {'id':'COV-DEF-005', 'location':'web/app.js:107 / branch37[1]', 'title':'中文Intl日期没有星期后缀的fallback',
     'reason':'当前Chromium格式输出满足既定格式；需先确认支持环境是否有不同输出，再设计真实环境或明确的格式依赖故障测试。'}
]
for row in defensive: row['status']='uncovered_reachability_or_defensive_test_pending'
write('proposed-coverage-scenarios.json', {'baseline_revision':context['revision'],
      'status':'proposal_not_independently_reviewed_not_added_to_canonical_ledger',
      'groups':groups, 'defensive_paths':defensive})

inventory = []
for line in backend['files']['app/server.py']['missing_lines']:
    inventory.append({'kind':'line', 'file':'app/server.py', 'line':line,
                      'gap_ids':['COV-GAP-001' if line==260 else 'COV-GAP-002']})
branch_groups={'9':['COV-DEF-001'], '20':['COV-DEF-002'], '33':['COV-DEF-003'],
               '34':['COV-DEF-004'], '37':['COV-DEF-005'], '72':['COV-GAP-007'],
               '73':['COV-GAP-005'], '83':['COV-GAP-006'], '85':['COV-GAP-003'], '86':['COV-GAP-003']}
for item in frontend['missing_branches']:
    inventory.append({'kind':'branch', 'file':'web/app.js', **item, 'gap_ids':branch_groups[item['id']]})
for item in frontend['missing_functions']:
    assert item['id']=='66'
    inventory.append({'kind':'function', 'file':'web/app.js', **item, 'gap_ids':['COV-GAP-004']})
for line in frontend['uncovered_lines']:
    assert line==96
    inventory.append({'kind':'line', 'file':'web/app.js', 'line':line, 'gap_ids':['COV-DEF-003']})
for item in frontend['missing_statements']:
    line=item['location']['start']['line']
    inventory.append({'kind':'statement','file':'web/app.js',**item,
                      'gap_ids':['COV-DEF-003' if line==96 else 'COV-GAP-004']})
write('uncovered-inventory.json', {'items':inventory,
      'additional_semantic_gaps':['COV-GAP-006:self-demotion-followup-failure', 'COV-GAP-008'],
      'note':'一处源码可能同时出现在行、语句、函数、分支清单；这些不是独立缺陷计数。'})

final_jobs={j['job']:j for j in context['jobs']}
for doc in (ui_context,extra_context,load('startup-replay-context.json')):
    for job in doc['jobs']: final_jobs[job['job']]=job
assert len(final_jobs)==27 and all(j.get('exit_code')==0 for j in final_jobs.values()), final_jobs
write('execution-summary.json', {'business_entry_jobs':list(final_jobs.values()),
      'count':len(final_jobs), 'process_success_is_not_product_pass':True,
      'repaired_measurement_dependencies':'11个UI续测入口需要本轮前序UI结果元数据；启动探针需要runtime证据目录；独立探针需要空run元数据。修复测量副本后重跑，不修改测试断言；初始失败记录保留。',
      'aggregation':'取实际执行命中并集；不能合并跨运行passed结果判定验收。'})

smoke=load('smoke-coverage.json')['totals']; bt=backend['totals']; ft=frontend['summary']
line_pct=100*(bt['covered_lines']+ft['lines']['covered'])/(bt['num_statements']+ft['lines']['total'])
metrics={'revision':context['revision'], 'backend':{'lines':{'covered':bt['covered_lines'],'total':bt['num_statements'],'pct':bt['percent_statements_covered']},
           'branches':{'covered':bt['covered_branches'],'total':bt['num_branches'],'pct':bt['percent_branches_covered']}},
         'frontend':ft, 'weighted_executable_lines':{'covered':bt['covered_lines']+ft['lines']['covered'],
           'total':bt['num_statements']+ft['lines']['total'],'pct':line_pct},
         'original_smoke_backend':{'lines_pct':smoke['percent_statements_covered'], 'branches_pct':smoke['percent_branches_covered']}}
write('metrics.json',metrics)

source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in context['source_hashes']}
assert source_hashes==context['source_hashes']
assert context['revision']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
old_run=ledger/'runs/acceptance-20261008T-full-0b386b4-r1'
assert all(hashlib.sha256((old_run/f).read_bytes()).hexdigest()==h for f,h in context['original_acceptance_hashes'].items())
write('integrity-check.json', {'source_sha256':source_hashes, 'original_acceptance_sha256':context['original_acceptance_hashes'],
      'original_source_and_acceptance_unchanged':True,
      'ledger_sha256':{f:hashlib.sha256((ledger/f).read_bytes()).hexdigest() for f in ['requirements.json','scenarios.json','methods.json']},
      'new_proposals_do_not_modify_canonical_ledger':True})

text=f'''# 当前测试代码覆盖率与补测缺口

被测修订：`{context['revision']}`（stage-06-acceptance-run）；应用源码与首轮验收时相同。

| 业务源码 | 可执行行覆盖率 | 分支出口覆盖率 |
| --- | ---: | ---: |
| app/server.py | {bt['covered_lines']}/{bt['num_statements']}（{bt['percent_statements_covered']:.2f}%） | {bt['covered_branches']}/{bt['num_branches']}（{bt['percent_branches_covered']:.2f}%） |
| web/app.js | {ft['lines']['covered']}/{ft['lines']['total']}（{ft['lines']['pct']:.2f}%） | {ft['branches']['covered']}/{ft['branches']['total']}（{ft['branches']['pct']:.2f}%） |

按可执行行数量加权：{metrics['weighted_executable_lines']['covered']}/{metrics['weighted_executable_lines']['total']}（{line_pct:.2f}%）。
前端另有语句覆盖 {ft['statements']['covered']}/{ft['statements']['total']}（{ft['statements']['pct']:.2f}%），函数覆盖 {ft['functions']['covered']}/{ft['functions']['total']}（{ft['functions']['pct']:.2f}%）。
原有三个冒烟测试单独测得后端行覆盖290/384（{smoke['percent_statements_covered']:.2f}%）、分支71/124（{smoke['percent_branches_covered']:.2f}%）；冒烟不执行浏览器JavaScript。

## 补测清单

完整前置条件、执行矩阵、断言及证据要求保存在 [proposed-coverage-scenarios.json](proposed-coverage-scenarios.json)。
这些是8组补测建议，尚未独立审阅、尚未追加到正式159场景台账，不能计作验收通过。

| ID | 路径 | 缺口性质 | 优先级 |
| --- | --- | --- | --- |
'''
for g in groups:
    text+=f"| {g['id']} | {g['title']} | {category_labels[g['category']]} | {g['priority']} |\n"
text+='''
弹窗点击和退出关闭弹窗已经写在现有白盒设计中，缺的是具体执行分支证据；不必重复新增同名场景。
连接中断、清空筛选值需要补充操作/故障模式；角色与401路径需要细化状态组合。
Ctrl+C检查补充启动生命周期，不把它当作已确认业务需求之外的新发布承诺。
unsupported HTTP方法及自身降权后身份查询失败，也是首轮独立审阅已经发现的语义覆盖缺口。

额外独立诊断探针执行DELETE/OPTIONS/PUT × 三种身份 × 五个API路径，共45次真实请求：均返回501 text/html，0次符合JSON error/code契约，业务数据均未变化。
该事实存于 [supplemental-http-verbs.json](supplemental-http-verbs.json)，未纳入“原有全部测试”的覆盖计数，也没有独立验收审阅。

## 未覆盖源码的逐项对应

后端未覆盖行：260（连接断开）、492/493/495（KeyboardInterrupt与最终关闭监听）；没有coverage.py报告的未命中分支弧。
前端未覆盖行：96（非法内部页面默认内容）；12个分支出口、1个函数及3个语句未命中。
逐位置的完整映射见 [uncovered-inventory.json](uncovered-inventory.json)，相同位置可被多个指标计入，不能累加成缺陷数。

另有5处防御/辅助函数出口：登录反馈DOM缺失、无身份renderShell、非法page枚举、heading默认参数、Intl星期fallback。
这些位置仍保留在覆盖率分母与清单中；未证明其可通过约定业务UI到达，不擅自认定为5个需求漏测。
可先分析可达性，再决定增加防御单元检查或支持环境测试。

## 测量范围与限制

- 分母为两份业务程序源码：app/server.py、web/app.js；空的app/__init__.py没有可执行行，HTML/CSS、测试自身、工具依赖和标准库不进入业务代码分母。
- 重跑原三个冒烟与归档内全部27个业务测试入口，包括较早API矩阵、后续补充、运行时、UI、竞态及独立子分支探针；辅助浏览器/进程脚本由对应调用者运行。资源预检、结果合并、设计检查及描述性笔记不作为额外业务入口。
- Python使用coverage.py 7.16.2（branch、thread及子进程startup计数）；JavaScript使用Istanbul 6.0.3。浏览器仍执行真实业务JS，仅副本插入计数器，CSP不放宽。
- 每个入口采用源码隔离副本与独立数据库；测试断言不改。副本修订断言适配当前stage-06 HEAD，并将旧行追踪器替换为coverage.py，避免覆盖率追踪被覆盖。
- UI续测的结果结构依赖通过本轮前序结果按序复制解决；原验收结果不作为新命中数据。初次错误的退出记录与续测依赖纠正日志保留；所有27入口最终进程退出0不表示产品断言全通过。
- `-S`启动子进程不加载sitecustomize；该启动尝试的内部执行没有子进程覆盖计数，保留此测量限制。其他正常CLI子进程已经计入；仍未证明默认8766监听的进程归属、完整默认参数与Python3.11矩阵。
- 取本轮真实命中的并集，不合并跨运行通过判定。没有为提分而运行新增场景后混入基线，没有排除未覆盖防御行。
- 后端coverage.py把行与分支机会合并得到的percent_covered不是纯行覆盖率；本报告行覆盖使用covered_lines/num_statements。
- 行/分支命中证明执行到达，不能证明断言有效或产品正确。短路布尔条件、异常类型、角色状态、事务提交时序和继承的HTTP处理需要另行分析；本次没有宣称MC/DC、所有路径或所有状态组合100%。[coverage.py官方分支测量说明](https://coverage.readthedocs.io/en/latest/branch.html)。

前一轮验收的4类缺陷、9个失败场景和11个未证明场景仍保持原结论。
本审计不会改写需求、正式场景/方法台账、原run/review/gate，也不升级发布安全结论。
环境/观察限制详见旧 [首轮验收档案](../../../../snapshots/stage-06-acceptance-run/README.md)。

## 数据与复现

- [metrics.json](metrics.json)、[backend-coverage.json](backend-coverage.json)、[frontend-coverage.json](frontend-coverage.json)：计数和未覆盖位置。
- [execution-summary.json](execution-summary.json)：27入口与实际日志；[integrity-check.json](integrity-check.json)：源码、需求及旧验收哈希。
- [html/backend/index.html](html/backend/index.html)：coverage.py原生后端报告；[html/frontend.html](html/frontend.html)：前端逐行及分支报告；[index.html](index.html)：审计概览。

在仓库根目录恢复本档案到tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06，确保正式台账及阶段06归档的harnesses已恢复到tests/delivery-acceptance/harnesses，再运行：

```sh
python3 -m pip install --target tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/tools/python coverage==7.16.2
npm install --prefix tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/tools/node istanbul-lib-instrument@6.0.3 istanbul-lib-coverage@3.2.2
node tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/instrument.js
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/replay.py
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/replay_ui.py
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/replay_extra.py
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/report_python.py
node tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/report.js
```

脚本使用本机已安装Playwright的Python路径；其他机器需配置该路径和浏览器，coverage.ini按当前仓库路径生成。
覆盖复现不要求重跑或重写正式验收工作流。
重新运行会建立新测量，需使用空输出目录以免并入旧计数；当前审计保留全部测量setup尝试以备查。
公开快照不包含重放副本数据库、会话值、工具依赖或浏览器资料；覆盖计数文件只保存源码路径及行/弧命中。
'''
# The saved report is below coverage-audits; snapshots is three levels up.
text=text.replace('../../../../snapshots/', '../../../snapshots/')
(BASE/'coverage-audit.md').write_text(text)

style='body{font:16px/1.65 system-ui;margin:30px auto;max-width:1150px;padding:0 24px;color:#24354a}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d5dce5;padding:8px;text-align:left}pre{white-space:pre-wrap;font-size:13px}.miss{background:#ffe3e3}.partial{background:#fff1c4}a{color:#135bb3}code{background:#eef1f6;padding:2px 4px}'
line_counts=frontend['raw']['s']; maps=frontend['raw']['statementMap']
covered={}; missing_branch_lines={x['condition']['start']['line'] for x in frontend['missing_branches']}
for key,loc in maps.items():
    line=loc['start']['line']; covered[line]=covered.get(line,False) or line_counts[key]>0
code=''
for number,line in enumerate((ROOT/'web/app.js').read_text().splitlines(),1):
    cls='miss' if number in frontend['uncovered_lines'] else 'partial' if number in missing_branch_lines else ''
    code+=f'<div id="L{number}" class="{cls}">{number:3} {html.escape(line)}</div>'
(BASE/'html/frontend.html').write_text(f'<!doctype html><meta charset="utf-8"><title>前端覆盖率</title><style>{style}</style><h1>web/app.js 覆盖率</h1><p>行99.44% · 分支93.22% · 红色：未覆盖行；黄色：存在未覆盖分支出口。</p><a href="../frontend-coverage.json">完整分支与函数计数</a><pre>{code}</pre>')
rows=''.join(f'<tr><td>{g["id"]}</td><td>{html.escape(g["title"])}</td><td>{g["priority"]}</td><td>{html.escape(category_labels[g["category"]])}</td></tr>' for g in groups)
(BASE/'index.html').write_text(f'''<!doctype html><meta charset="utf-8"><title>MeetSpace 覆盖率审计</title><style>{style}</style>
<h1>MeetSpace 当前测试覆盖率</h1><p>被测修订：<code>{context['revision']}</code> · 27个既有业务测试入口 · 应用源码保持不变</p>
<table><tr><th>业务源码</th><th>可执行行</th><th>分支出口</th></tr>
<tr><td><a href="html/backend/index.html">app/server.py</a></td><td>380/384 · 98.96%</td><td>124/124 · 100%</td></tr>
<tr><td><a href="html/frontend.html">web/app.js</a></td><td>180/181 · 99.44%</td><td>165/177 · 93.22%</td></tr></table>
<p>加权可执行行覆盖率：560/565 · 99.12%。原3项冒烟后端：行75.52%、分支57.26%。</p>
<p>覆盖率不等于验收通过。异常类型、继承入口和状态组合仍需检查；首轮验收失败结论保持。</p>
<h2>8组补测建议</h2><p>尚未独立审阅或追加正式台账。弹窗和退出两组已有设计，需细化执行。</p>
<table><tr><th>ID</th><th>路径</th><th>优先级</th><th>缺口性质</th></tr>{rows}</table>
<p>另外5个未命中防御/辅助出口需要可达性分析，仍保留在分母中。</p>
<p>额外45次unsupported HTTP探针全部返回501 HTML；该新增诊断未混入既有测试覆盖率。</p>
<p><a href="coverage-audit.md">完整报告与限制</a> · <a href="proposed-coverage-scenarios.json">补测前置条件/矩阵/断言</a> · <a href="uncovered-inventory.json">逐位置映射</a> · <a href="metrics.json">计数</a> · <a href="execution-summary.json">执行记录</a></p>''')
print(json.dumps({'groups':len(groups),'defensive_paths':len(defensive),'jobs':len(final_jobs),'weighted_lines_pct':line_pct}))
