# stage-04: 黑盒场景设计通过

本目录是流程结束后的不可变公开档案，供 GitHub 阶段对比。
活跃台账继续使用用户指定的 `tests/delivery-acceptance/`；JSON 保留场景和方法的唯一正文。

基线为已确认的 `stage-02-requirements`（`12d503a`）全部 96 条需求，加上用户按 [DR-004](../../../specs/decisions/004-login-window-endpoint.md) 确认的登录窗口端点：时刻 t 计数范围为 `(t - 60 秒, t]`。
其余 95 条需求正文不变，应用实现及原有冒烟测试不变。

**96 个黑盒场景、105 个 AI 操作方法，全部 96 条需求经独立反事实审阅判定设计充分。**
编译的黑盒流程执行确定性门禁，退出码为 0，保存状态为 `black_box_ready`。
本阶段未执行应用测试、资源验证或白盒验收，方法中的设施和证据仍是执行计划，尚不能据此发布版本。

| 本基线审阅轮次 | 场景 | 方法 | 充分的需求 | 有缺口的需求 |
| --- | --- | --- | --- | --- |
| 第一轮 | 96 | 105 | 90 | 6 |
| 第二轮 | 96 | 105 | 96 | 0 |

上一阶段四项缺口均已补齐设计；第一轮续审提出的六项缺口也已修订并经第二轮独立审阅关闭。
[stage-03 档案](../stage-03-black-box-scenarios/README.md) 保留当时 92 条充分、4 条不足的历史结论。

## 档案入口

- [requirements.json](requirements.json)：当前已确认需求快照，包含用户端点决定。
- [scenarios.json](scenarios.json)、[methods.json](methods.json)：完整设计与操作计划。
- [coverage_review.json](coverage_review.json)：全部需求的独立充分性结论及 scoped SHA-256。
- [black-box-gate.json](black-box-gate.json)：编译流程保存的实际设计门禁结果。
- [pending-business-inputs.json](pending-business-inputs.json)、[repair-summary.json](repair-summary.json)：决策与修订追溯，设计缺口已关闭、实际执行未开始。
- [review-history](review-history/)：本基线两轮原始需求、设计与独立审阅快照。
- [manifest.json](manifest.json)：来源、状态、统计及档案文件 SHA-256。

## 使用只读查看器

本机当前台账使用已安装 Skill：

```sh
python3 /path/to/app-delivery-acceptance/scripts/serve_ledger.py . --test-dir tests
```

另一台机器或新克隆先安装同一 Skill。
仅在没有现有活跃台账时初始化本机路径，再复制档案；不要覆盖正在进行的测试会话。

```sh
python3 /path/to/app-delivery-acceptance/scripts/playbook.py init . --test-dir tests --requirements tests/snapshots/stage-04-black-box-ready/requirements.json
cp tests/snapshots/stage-04-black-box-ready/{scenarios,methods,coverage_review,black-box-gate,pending-business-inputs,repair-summary}.json tests/delivery-acceptance/
cp -R tests/snapshots/stage-04-black-box-ready/review-history tests/delivery-acceptance/
python3 /path/to/app-delivery-acceptance/scripts/serve_ledger.py . --test-dir tests
```

查看器不执行应用、不批准场景，也不建立完整验收结论。
历史门禁中的本机路径保留原始上下文，新机器的 project.json 由初始化产生。
后续发布验收仍须完成资源、白盒、真实执行与证据门禁。
