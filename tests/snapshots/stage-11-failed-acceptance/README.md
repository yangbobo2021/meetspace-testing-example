# 阶段11：修复版本的完整验收，发现角色刷新竞态

被测修订 `708c9c057b5c9014f4ff975fdc5774093a687abe`，对应 `stage-10-fixes`。
编译的 app-delivery-acceptance 流程已完成，session `afdb230b-94fc-4b15-9378-aaa02f4fdc2c`，结果 `incomplete`。
全部96条确认需求、167条场景、176个方法纳入本轮，执行期间应用和台账定义固定。

| 结论来源 | 通过 | 失败 | 未证明 |
| --- | ---: | ---: | ---: |
| 实际执行汇总 | 157 | 9 | 1 |
| 正式独立审阅 | 160 | 6 | 1 |

需求、资源、场景三个门禁通过；执行、审阅门禁阻断，完整检查器退出码2。
独立审阅没有回写原执行结果，也没有用历史通过结果替代新运行。

## 产品反例与缺证

四个独立原生UI反例属于同一角色/身份异步刷新缺陷族：旧changeRole身份200跨新登录、同身份角色操作重排，以及旧pending身份读跨后续角色提交。
真实后台保持新账号或member权限，管理读取403；迟到回调却恢复旧账号或admin菜单，问题位于UI状态管理。
正式判定失败的6场景为 `BB-identity-session-7`、`BB-interface-experience-8`、`BB-team-administration-7`、`WB-ui-load-token-races`、`WB-ui-role-demotion-reload`、`WB-ui-self-demotion-session-failure`。
逐场景原因和反例引用见 [review.json](runs/acceptance-20261009T-stage10-708c9c0-r1/review.json)。

`WB-idempotency-absolute-precision` 的历史数据库生成器分支未执行：自动审批拒绝在固定修订测试中运行旧版应用。
另一次自动审批拒绝将旧脚本的非法角色400断言放宽为接受500；该脚本及原失败保留，未绕过拒绝。
独立审阅按已确认需求逐场景判断非法角色拒绝/无写入，以及当前源码行号的断连完整重跑；这些审阅不消除原始执行失败。
下一修订将使用明确审阅的合成历史格式夹具，仅运行当前目标源码；它不能冒充旧app的新执行。

## 新源码覆盖率和运行资源

| 源码 | 可执行行 | 分支 | 函数 |
| --- | ---: | ---: | ---: |
| app/server.py | 389/389 · 100% | 126/126 · 100% | — |
| web/app.js | 197/198 · 99.49% | 187/192 · 97.39% | 86/86 · 100% |

这些是708c9c0源码的全新计数，没有合并修复前计数，也不能验证下一次修复。
剩余5个已评估防御出口仍保留分母；独立复查没有要求为它们添加新正式场景。
运行时执行包括1,025条断言、Python3.11/3.12各11项CLI检查、31个熵分支及62段生命周期跟踪。
熵与持久化观察为明确的有界测试模型，私有熵比较材料不归档。

## 档案核验

- [运行和门禁](runs/acceptance-20261009T-stage10-708c9c0-r1/gate-report.json)
- [覆盖率](coverage-audits/coverage-stage10-fresh-20261009/summary.json)
- [四个反例的独立复现审查](release-preparation/20261009/product-failure-review.json)
- [流程完成与原记录SHA](release-preparation/20261009/workflow-terminal-evidence.json)
- [归档文件SHA](manifest.json)

绝对本机证据路径通过 evidence-path-map.json 对应归档文件；运行数据库、隔离源码、依赖、缓存及私有比较材料排除。
process-assessment.json 记录排除项及公开脱敏的原/归档SHA；原始本机证据和历史阶段保留。
下一过程必须在已结束流程之外修复，并单独提交，再对新修订完整验收。
