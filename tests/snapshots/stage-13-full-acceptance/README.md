# 阶段13：固定修复版本的完整验收通过

被测应用修订 `5247b360276f2900d20fdeab96bd75bb3ece73fa`，标签 `stage-12-identity-fixes`。
编译的 app-delivery-acceptance 流程在同一 session `cb18568a-7ebc-41fb-a307-e8c7038394e4` 正式结束，结论全面验收通过。
正式运行 `acceptance-20261009-stage12-5247b36-exec-01`：执行167通过，独立逐场景审阅167通过，0失败、0未证明，五项门禁全部通过。
96条确认需求、96黑盒加71白盒、176方法的稳定ID保持。
本阶段保存完整验收及覆盖率循环结果，独立发布审阅另行提交。

## 设计与实际执行

- 新源码依据独立复审，新增身份矩阵从34项扩至40项；第二轮补入2种新session失败×3种旧changeRole身份响应，细化4场景/4方法。
- 96条需求独立判定充分，209个反事实探针依据；角色请求归属及旧续段退出由被动CDP/源码位置证明，固定短延迟首次尝试不能替代完成证明。
- 正式运行重新执行全部方法并补足取消权限与服务时钟、全字段会议室修改及重登、63项HTTP协议控制、成员/管理员重试再失败、通知格式和SIGINT等完整矩阵。
- 历史格式兼容使用明文审阅的synthetic SQL夹具、历史摘要oracle，仅执行当前固定源；没有重试此前被拒的旧应用执行。
- 实际执行保存559张截图及请求、数据库、时序和断言；正式Reviewer重新读取378个直接引用文件，独立重算708项观测，目视检查范围明确列于review_basis，不把读图片字节冒充逐图目视审查。
- 两次模型容量故障及恢复参数首次缺失均保留，相同compiled session恢复，没有修改工作流或降低门禁。

## 最终源码覆盖率

| 源码 | 行 | 分支 | 函数 | 语句 |
| --- | ---: | ---: | ---: | ---: |
| app/server.py | 389/389 · 100% | 126/126 · 100% | 31/31 · 100% | 389/389 · 100% |
| web/app.js | 209/210 · 99.52% | 207/212 · 97.64% | 86/86 · 100% | 360/362 · 99.44% |

36个采集作业只合并同一5247源码的全新计数，独立重算77个Python和31个JS计数文件。
五处既有防御出口仍保留分母；重要状态补齐后独立复核没有新的必要补测建议。
原报告及350ms缺证据尝试保持，最终六组合采集6/6、30强断言及CDP完成证明另行保存。

## 运行资源与观察范围

当前资源的独立准备复核接受唯一 `generation-guard-complete-attempt`，fresh31熵分支、62生命周期及22CLI全部完整。
观察器的线程退出/合法munmap重叠及同址映射复用候选缺口，通过独立实际负控核验窄条件与mapping generation修正。
原3启动缺证、seed-1原因未知映射读缺口及旧候选失败原样保留，不把它们迁入当前通过结果或声称均已归因。
实际mremap/mprotect及125条路径均给出范围解释；资源结论限定当前固定产品的实际实现、持久字段与已登记共享写映射，不宣称通用无限I/O证明，也不代替正式167场景结论。

## 档案核验

- [正式运行、门禁和报告](runs/acceptance-20261009-stage12-5247b36-exec-01/gate-report.json)
- [正式独立审阅](runs/acceptance-20261009-stage12-5247b36-exec-01/review.json)
- [最终覆盖率](coverage-audits/coverage-stage12-fresh-20261009/summary.json)
- [追加采集独立复核](release-preparation/20261009/stage12-coverage-followup-review/final-six-collector-review.json)
- [资源独立复核](release-preparation/20261009/facility-review-confirmed-unmap/fixed-product-resource-final-review.json)
- [流程正式终结](release-preparation/20261009/stage12-workflow-terminal-evidence.json)
- [逐文件SHA](manifest.json)

Reviewer的精确run/台账/源码SHA绑定在其protected-inputs-final.json；归档工具只增加该已存在绑定格式的读取，不改原审阅或断言。
绝对本机路径由evidence-path-map.json对应归档文件；数据库、私有比较材料、工具依赖、缓存和隔离产品副本排除。
process-assessment.json记录6份合成认证数据脱敏的原/归档SHA及字段，原本机证据保留；归档SHA变化不会冒充原运行SHA。
