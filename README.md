# MeetSpace · 团队会议室预约

本项目由 Codex 为“已有项目在发布前补充测试”的教学场景新建，是自建的完整本地应用，不是从某个真实客户项目接手，也不是已发布的开源产品。业务账号、团队和数据均为合成示例。

最初交接版本为 **1.0.0-rc.1**：主要功能已实现，当时有少量原有冒烟测试，尚未完成系统发布验收。不能凭这三个测试通过认定版本可发布。没有故意植入故障，也不预设测试 Skill 一定发现严重缺陷。

## 启动

需要 Python 3.11+，使用标准库，无需安装依赖、申请云服务或配置真实邮件账号。macOS、Linux 和安装了 Python 的 Windows 可运行。

```sh
git clone https://github.com/yangbobo2021/meetspace-testing-example.git
cd meetspace-testing-example
python3 -m app.server
```

已有本地检出时，直接在项目根目录运行 `python3 -m app.server` 即可。

打开 <http://127.0.0.1:8766>。第一次启动自动创建 SQLite 数据库、示例团队、会议室、账号及明天的三场会议。时间统一使用 **Asia/Shanghai（UTC+8）**，不取决于浏览器或服务器所在时区。

其他端口或独立数据文件：

```sh
python3 -m app.server --port 8767 --db data/another-run.sqlite
```

为一轮新验收使用一个新的数据库文件即可获得初始数据。重启同一个文件会保留已有记录。数据库目录不进入 Git。

默认只监听本机。该版本的部署目标是本地示例环境；公网部署、真实企业身份登录、真实邮件和运维恢复不在本版本范围。

## 示例账号

所有账号的公开示例密码都是 `MeetSpace!2026`。登录页可点击账号填入，再点击登录。

| 邮箱 | 姓名 | 团队 | 角色 |
| --- | --- | --- | --- |
| admin@meetspace.test | 林可 | 见山设计 | 管理员 |
| alice@meetspace.test | 陈悦 | 见山设计 | 成员 |
| bob@meetspace.test | 周言 | 见山设计 | 成员 |
| other@meetspace.test | 许宁 | 远岸工作室 | 管理员 |

## 已实现功能

- 登录、退出及八小时有效的服务端会话。
- 按日期查看会议室占用日程，按容量和设备筛选。
- 创建预约、查看自己的预约及历史、取消未开始的预约。
- 同团队同会议室的时段冲突检测、参会人数和开放时间限制。
- 请求标识支持创建预约重试，避免同一次请求重复创建。
- 管理员查看团队预约、取消未开始的团队预约、添加与编辑会议室、停用会议室、变更成员角色。
- 两个团队的数据隔离；普通成员只能管理自己的预约。
- 预约确认与取消通知保存到站内通知中心，可标记已读。**没有声称发送真实邮件。**
- SQLite 持久化，浏览器刷新或服务重启后可继续使用已有数据。

## 现有验证

```sh
python3 -m unittest discover -s tests -v
```

现有三项测试通过真实 HTTP 服务验证：基础登录与退出、成员预约与取消及通知、管理员添加和停用会议室。测试使用临时数据库，不污染页面示例数据。

这些测试主要覆盖正常路径，未形成权限矩阵、并发测试、边界时间测试、重试与故障恢复、持久化重启、多浏览器或移动端的完整验收证据。对这些路径的状态应写“未验证”，不能写“通过”。

## 接手做发布验收

1. 阅读 [需求规约地图](specs/map.md) 和 [版本交接](docs/release-handoff.md)。用户已确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为黑盒场景设计基线，见 [DR-002](specs/decisions/002-black-box-baseline-confirmation.md)。登录窗口精确六十秒端点随后按 [DR-004](specs/decisions/004-login-window-endpoint.md) 补充。
2. 用户已选择 `tests` 目录；由 `app-delivery-acceptance` Skill 在 `tests/delivery-acceptance/` 保存需求快照、设计和独立审阅场景。黑盒设计阶段有 96 个场景、105 个方法，全部 96 条需求经独立审阅判定充分，设计门禁 `black_box_ready`，见 [DR-005](specs/decisions/005-black-box-design-ready.md)。
   白盒设计已新增 63 个场景、63 个方法，独立审阅及补充设计结构检查通过；合计 159 个场景、168 个方法，见 [DR-006](specs/decisions/006-white-box-design-review.md)。随后用户授权执行完整验收，见 [DR-007](specs/decisions/007-first-release-acceptance.md)。
3. 固定 Git 修订和数据库初始状态，执行实际界面、API 和必要的实现检查，保存证据。
4. 根据事实输出通过、失败、未覆盖和受阻项。测试流程不修改应用代码；发现缺陷后在开发流程中修复，再对新修订复测。

首轮完整验收已执行，**结果未通过，不建议发布当前版本**。正式独立审阅 139 项通过、9 项失败、11 项未证明；9 个失败场景对应空日期、微秒重放、迟到401、通知时间缺失四类缺陷。另有两组新增覆盖缺口及环境观测限制，详见 [首轮验收档案](tests/snapshots/stage-06-acceptance-run/README.md)。应用和原测试均未修改，后续需修复并针对新修订复测。测试 Skill 需要 Node.js 和 Playbook；它们不是应用运行依赖。

随后对既有冒烟、API、运行时、UI及竞态测试重跑测量：后端行覆盖 **98.96%**、分支 **100%**；前端行覆盖 **99.44%**、分支 **93.22%**。覆盖率不能替代行为断言与证据审阅；审计提出8组补测路径及5处防御逻辑分析项，详见 [覆盖率审计档案](tests/snapshots/stage-07-coverage-audit/README.md) 与 [DR-008](specs/decisions/008-code-coverage-audit.md)，首轮验收失败结论保持。

用户随后同意更新正式设计：新增 **8 条白盒场景**、细化 **2 条已有场景**及其方法；当前 **96 条黑盒 + 71 条白盒 = 167 条场景**，共 **176 个方法**。设计及独立审阅见 [阶段08档案](tests/snapshots/stage-08-coverage-scenarios/README.md) 与 [DR-009](specs/decisions/009-coverage-supplement-scenarios.md)。本轮不执行补测，旧运行保留原定义与结论，覆盖率提升尚未测量。

## GitHub 阶段对比

公共仓库：<https://github.com/yangbobo2021/meetspace-testing-example>。

- `v1.0.0-rc.1` 保留最初的本地候选版本。
- `stage-01-implemented` 标记首次公开交接的当前实现，包括公开仓库启动说明；业务代码与原候选版本相同，完整发布验收尚未执行。
- `stage-02-requirements` 标记逆向需求整理阶段，按 `specs/` 规范组织候选条目；本阶段未启动测试 Skill 或执行应用测试。
- `stage-03-black-box-scenarios` 保存[黑盒设计公开档案](tests/snapshots/stage-03-black-box-scenarios/README.md)：96 个场景、102 个方法，三轮独立审阅后 92 条需求充分、4 条有缺口，设计门禁 blocked；未执行应用测试。
- `stage-04-black-box-ready` 保存[修订后设计公开档案](tests/snapshots/stage-04-black-box-ready/README.md)：按用户决定补充需求端点，96 个场景、105 个方法，全部 96 条需求充分，独立审阅与确定性设计门禁通过；未执行应用测试。
- `stage-05-white-box-scenarios` 保存[白盒设计公开档案](tests/snapshots/stage-05-white-box-scenarios/README.md)：新增 63 个白盒场景、63 个方法，全部独立审阅充分，合计 159 个场景、168 个方法；本次仅设计，未启动完整编译验收流程或执行应用测试。
- `stage-06-acceptance-run` 保存[首轮验收公开档案](tests/snapshots/stage-06-acceptance-run/README.md)：完整工作流真实执行和独立审阅；139 通过、9 失败、11 未证明，验收 incomplete，应用代码保持不变。
- `stage-07-coverage-audit` 保存[代码覆盖率审计档案](tests/snapshots/stage-07-coverage-audit/README.md)：既有测试重跑计数、逐位置未覆盖映射、补测建议与测量范围；不修改应用或升级验收结论。
- `stage-08-coverage-scenarios` 保存[覆盖率驱动的设计更新档案](tests/snapshots/stage-08-coverage-scenarios/README.md)：新增8白盒、细化2旧场景，正式台账167场景/176方法，五处防御逻辑按可达性处置；本轮不执行补测。
- 后续修复和复测分别提交真实产出，添加新的阶段标签，保留已有标签用于对比。

例如，查看当前实现到后续版本的变化：

```sh
git diff stage-01-implemented..HEAD
```

测试流程生成的资产仍先放在用户指定的测试目录；阶段结束后，可将适合公开的场景与结果快照整理进仓库，记录测试对应的应用修订。运行数据库、会话数据和真实服务凭据不进入公开提交。

## 结构

```text
app/server.py           HTTP API、权限、预约业务及 SQLite
web/                    中文响应式操作界面
tests/test_smoke.py      原有少量冒烟测试
tests/snapshots/         不可变的各阶段设计与验收档案
specs/map.md            需求入口与规约索引
specs/meta.md           沿用自行车项目的存储与语法规范
specs/packages/         按业务意图拆分的需求条目
specs/decisions/        结构决策、逆向来源与边界
docs/requirements.md    旧需求 ID 到新条目的映射
docs/release-handoff.md  版本边界、资源和接手验收说明
data/                   本机运行数据（不进 Git）
```
