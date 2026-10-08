# stage-03: 黑盒验收场景设计快照

本目录是设计流程结束后的不可变公开档案，供 GitHub 阶段对比；继续工作使用用户指定的 `tests/delivery-acceptance/`。JSON 保留场景与方法的唯一正文，本说明只提供入口和结果摘要。

基线：用户已确认 `stage-02-requirements`（`12d503a3d66f175b22aef9678e1e1bba59673485`）全部九个规约包、96 条需求。应用实现仍与 `stage-01-implemented` 一致。

本次调用 app-delivery-acceptance Skill 的黑盒设计流程，生成 96 个场景、102 个 AI 操作方法，并完成三轮独立反事实充分性审阅。没有执行应用、核实实际测试资源或进行白盒验收。方法中的时钟、故障设施、存储观察和证据均为后续执行计划。

| 审阅轮次 | 场景 | 方法 | 充分的需求 | 有缺口的需求 |
| --- | --- | --- | --- | --- |
| 第一轮 | 96 | 96 | 73 | 23 |
| 第二轮 | 96 | 98 | 91 | 5 |
| 第三轮 | 96 | 102 | 92 | 4 |

最终黑盒设计门禁为 **blocked**，流程结论为 **incomplete**。需求关联全量存在，结构无缺失不等于场景充分，更不等于版本可发布。

## 剩余不足

| 需求 | 第三轮独立审阅发现的缺口 |
| --- | --- |
| application-runtime-9 | 新增会议室仍缺实际写后、适用写间隙和最终提交失败矩阵，部分新增记录可能残留。 |
| identity-session-9 | 恰好 60.000 秒时是否移出 t=0 的登录尝试尚待业务决定，不能写入唯一验收预期。 |
| identity-session-13 | 密码初始化缺完整持久化出口与字段范围观察，可能漏掉额外保存的可恢复副本。 |
| identity-session-14 | 熵因果测试仅覆盖第一次登录，缺后续登录或切换时的生成检查，可能漏掉计数器退化。 |

这些是**测试设计不足**，不是已经执行发现的应用缺陷。完整反例、模式、状态与失败信号见 [coverage_review.json](coverage_review.json)。

## 档案入口

- [requirements.json](requirements.json)：逐字保留的已确认需求快照。
- [scenarios.json](scenarios.json)、[methods.json](methods.json)：当前设计与可复用执行计划。
- [coverage_review.json](coverage_review.json)：最终独立审阅，一条记录对应一条需求，附 scoped SHA-256。
- [black-box-gate.json](black-box-gate.json)：最终当前台账的实际设计门禁结果。
- [repair-summary.json](repair-summary.json)：修订来源、改动关联和最终剩余项。
- [review-history](review-history/)：各轮原始 JSON；第一轮从原工作流工具记录恢复，三个 scoped SHA-256 与当时独立审阅完全一致，说明见 recovery.json。
- [manifest.json](manifest.json)：来源修订、状态、统计和档案文件哈希。

## 使用只读查看器

本机当前台账可直接使用已安装 Skill：

```sh
python3 /path/to/app-delivery-acceptance/scripts/serve_ledger.py . --test-dir tests
```

要在另一台机器或新克隆中查看此档案，先安装同一 Skill。在没有现有 `tests/delivery-acceptance/` 台账的克隆中，先用 `playbook.py init` 初始化本机路径，再复制本目录的场景、方法、审阅、门禁及可选记录到初始化目录；不要用档案覆盖正在进行的测试会话。

```sh
python3 /path/to/app-delivery-acceptance/scripts/playbook.py init . --test-dir tests --requirements tests/snapshots/stage-03-black-box-scenarios/requirements.json
cp tests/snapshots/stage-03-black-box-scenarios/{scenarios,methods,coverage_review,black-box-gate,pending-business-inputs,repair-summary}.json tests/delivery-acceptance/
cp -R tests/snapshots/stage-03-black-box-scenarios/review-history tests/delivery-acceptance/
python3 /path/to/app-delivery-acceptance/scripts/serve_ledger.py . --test-dir tests
```

查看器不会执行应用或批准场景。历史门禁中的本机路径是原始上下文；新机器的 project.json 由初始化产生，勿复制其他机器的绑定。之后继续流程必须保留目录选择并先解决缺口，不能把此档案当作全量通过报告。
