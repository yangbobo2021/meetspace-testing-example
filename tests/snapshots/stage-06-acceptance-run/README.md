# stage-06: 首轮发布验收档案

本轮使用 app-delivery-acceptance Skill 已安装的完整编译工作流，固定实现 `0b386b4bd37b01eb996c5e74215ab1a4463a9487`，复用确认的 96 条需求、96 个黑盒和 63 个白盒场景、168 个方法。
**验收未通过，不建议发布当前版本。**
应用代码、原有测试与确认需求均未修改；阶段提交只保存测试产出和导航说明。

## 结果与门禁

| 判断来源 | 通过 | 失败 | 受阻／未证明 |
| --- | ---: | ---: | ---: |
| Tester 原执行记录 | 140 | 12 | 7 blocked |
| 正式 Reviewer 逐场景审阅 | 139 | 9 | 11 unproven |

两列分别保留，最终发布判断依据正式独立审阅，不合并不同运行的通过结果。
9 个失败场景对应四类实测缺陷，并非九个独立缺陷。

| 门禁 | 结果 |
| --- | --- |
| requirements | passed |
| resources | passed |
| scenarios | passed |
| execution | blocked |
| review | blocked |

指定检查器退出码 2，整体 `blocked`；编译工作流终态 `productFailed`／`incomplete`。
三个前置门禁及结构检查通过不代表实际分支覆盖充分或可以发布。
正式 Reviewer 新发现两组重要覆盖缺口，因此未认可完整覆盖。

## 确认的缺陷

- 显式 `?date=` 返回 200 并回退今天，应拒绝非法空日期。
- 同一请求标识下，起止绝对时刻增加 1 微秒仍返回成功重放。
- 旧身份的迟到 401 响应清除已经登录的新身份工作空间，服务端新会话仍有效。
- 本机 Python 3.12.4 中真实通知正文缺少日期和开始时间；Python 3.14.2 对照正常，不能抵消该运行目标的失败。

正式 Reviewer 将非法角色值必须返回 400 的额外断言剔除：确认需求只要求拒绝且不改角色，实际满足。
通知正文缺陷由明确要求该结果的专门场景判失败，不扩大其他创建场景的预期范围。
失败原始响应、截图及对照在 [review.json](runs/acceptance-20261008T-full-0b386b4-r1/review.json) 和 [release-assessment.json](release-assessment.json) 中可追踪。

## 未证明的范围

- 启动归属、默认端口及完整 host/port/db 参数隔离、Python 3.11 环境尚未证明。
- 密码盐和首次／后续会话的有效系统熵输入因果、完整持久化出口观测受本机权限限制，不能由样本不同或主表无明文判通过。
- 未实现 HTTP 动词的错误响应：已有 GET/POST/PATCH/HEAD 矩阵遗漏 DELETE/OPTIONS 等路径。
- 自身合法降权成功后身份查询网络／503 失败及恢复：已有异常检查修改他人角色，不能替代自身降权状态组合。

上述两组新增覆盖缺口属于未证明，源码反例没有冒充实际执行失败。
Skill 的完整工作流规定真实产品失败以 incomplete 结束，本轮没有在验收流程内修复产品或降低预期；下一阶段需修复、补场景后针对新修订重新验收。

## 原始档案与复核

- [requirements.json](requirements.json)、[scenarios.json](scenarios.json)、[methods.json](methods.json)：唯一需求／场景／方法正文；本轮修订了 `{}` 按入口判定与真实容量筛选矩阵。
- [coverage_review.json](coverage_review.json)、[scenario-gate.json](scenario-gate.json)：执行前正式充分性审阅与前置门禁；后续证据审阅发现的新缺口见本轮 review。
- [resources.json](resources.json)、[evidence/resources](evidence/resources/)：六项基础资源的实测记录。
- [run.json](runs/acceptance-20261008T-full-0b386b4-r1/run.json)、[review.json](runs/acceptance-20261008T-full-0b386b4-r1/review.json)、[gate-report.json](runs/acceptance-20261008T-full-0b386b4-r1/gate-report.json)、[acceptance-report.md](runs/acceptance-20261008T-full-0b386b4-r1/acceptance-report.md)：原执行、正式审阅和指定检查器报告。
- [harnesses](harnesses/)：真实 HTTP／浏览器、时间控制、SQLite 故障与恢复的测试脚本；注入范围与修正历史随证据保存。
- [workflow-result.json](workflow-result.json)、[acceptance-workflow.log](acceptance-workflow.log)：原会话终态；启动器退出 0 表示工作流结束，业务验收仍未通过。
- [manifest.json](manifest.json)：公开文件 SHA-256、冻结源文件哈希及未公开文件清单。

运行数据库、会话和缓存文件不公开，未公开项记录路径、大小和 SHA-256，未改动原结果或审阅哈希。
JSON 快照、SQL 轨迹、日志和截图保留；数据库文件本身仍仅在本机忽略目录中。
历史文件保留本机绝对路径、测试修订及固定运行 ID，公开档案不是可直接移植的当前验收通过证明。
测试脚本需要对应的 Python／Chromium 环境与路径适配，重新执行必须创建新的运行 ID，不覆盖本轮。
当前 stage-05 白盒辅助设计审阅属于历史设计来源，本轮正式依据是上述完整工作流记录。

本机活跃台账仍在用户选择的 `tests/delivery-acceptance/`；只读查看器逐次选择一个运行，不汇总跨轮通过。
新克隆可直接读取本档案 JSON、PNG 和报告，重新执行请安装同一 Skill 后使用新的验收运行。
