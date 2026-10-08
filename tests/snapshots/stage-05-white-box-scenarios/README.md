# stage-05: 白盒验收场景设计档案

本目录是设计结束后的不可变 GitHub 阶段档案。
活跃台账仍在用户指定的 `tests/delivery-acceptance/`；场景与方法正文以 JSON 为唯一来源。

需求基线沿用 `stage-02-requirements` 的全部 96 条需求及已确认的 DR-004 端点，逐字未改。
实现基线固定为 `stage-04-black-box-ready`（`5a0fd19`），源文件 SHA-256 见 [white-box-context.json](white-box-context.json)。

新增 **63 个白盒场景、63 个方法、63 个重要实现目标**，全部 96 条需求都有白盒关联。
合并后 **159 个场景（96 黑盒＋63 白盒）、168 个方法**；原黑盒场景、105 个方法及独立审阅保持不变。
独立 Reviewer 逐场景、逐实现目标检查，并对独立枚举的 64 组路径逐项核对，最终白盒设计审阅 passed。
设计未运行应用、测试或资源设施，不代表实际分支覆盖率或版本验收通过。

## 流程范围

本次按用户仅设计范围采用 app-delivery-acceptance Skill 的 Analyst／Reviewer 分工、反事实审阅原则和台账模型。
已安装 Skill 的白盒步骤位于完整验收流程内，尚无独立白盒设计启动阶段；本次没有启动会继续实际执行的完整编译流程，也没有修改全局 Skill。
[white-box-design-gate.json](white-box-design-gate.json) 是本项目补充的设计结构检查结果，退出码 0，状态 white_box_design_ready；它不是完整验收门禁。
检查包括源文件与需求绑定、场景与方法链接、实现目标映射、独立审阅完整性及哈希时效，以及原黑盒资产保持不变。
Skill 原黑盒检查也保持 black_box_ready。
资源验证、真实执行、执行覆盖率和证据验收均尚未开展。

## 审阅轮次

| 轮次 | 充分的白盒场景 | 有缺口的白盒场景 | 审阅结论 |
| --- | --- | --- | --- |
| white-box-round-01 | 60 | 3 | gaps |
| white-box-round-02 | 63 | 0 | passed |
| white-box-round-03 | 63 | 0 | passed |

第三轮核验代码定位校正与设计行为保持不变；前两轮原始档案未覆盖。

## 档案入口

- [scenarios.json](scenarios.json)、[methods.json](methods.json)：黑白盒场景与计划方法；白盒含 target_condition。
- [white-box-map.json](white-box-map.json)：代码符号和行号、重要目标、场景与全部需求的关联及排除理由。
- [white_box_review.json](white_box_review.json)：独立白盒充分性审阅、反事实故障、可观察失败信号和 scoped SHA-256。
- [white-box-context.json](white-box-context.json)、[white-box-design-summary.json](white-box-design-summary.json)：固定来源、范围、统计、资源假设和未执行风险探针。
- [white-box-design-gate.json](white-box-design-gate.json)：补充设计结构检查。
- [coverage_review.json](coverage_review.json)、[black-box-gate.json](black-box-gate.json)：保持有效的原黑盒审阅和门禁。
- [review-history](review-history/)：设计前台账、独立路径库存与各轮原始审阅。
- [manifest.json](manifest.json)：统计、历史状态和全部档案文件哈希。

疑似实现风险保留为待执行探针，不作为已实测缺陷，也不为取得设计通过而修改应用或需求。

## 查看与核对

本机使用已安装 Skill 的只读查看器，可在场景类型中选择“白盒”：

```sh
python3 /path/to/app-delivery-acceptance/scripts/serve_ledger.py . --test-dir tests
```

查看器已有的“覆盖充分”标签来自黑盒审阅；白盒独立结论请读取本档案的 white_box_review.json。
另一台机器或新克隆，在没有活跃台账时先安装同一 Skill 并初始化本机 project.json，再复制档案；不要覆盖进行中的会话。

```sh
python3 /path/to/app-delivery-acceptance/scripts/playbook.py init . --test-dir tests --requirements tests/snapshots/stage-05-white-box-scenarios/requirements.json
cp tests/snapshots/stage-05-white-box-scenarios/*.json tests/delivery-acceptance/
cp -R tests/snapshots/stage-05-white-box-scenarios/review-history tests/delivery-acceptance/
mkdir -p tests/delivery-acceptance/scripts
cp tests/snapshots/stage-05-white-box-scenarios/scripts/check_white_box_design.py tests/delivery-acceptance/scripts/
python3 tests/delivery-acceptance/scripts/check_white_box_design.py . --test-dir tests --skill /path/to/app-delivery-acceptance
python3 /path/to/app-delivery-acceptance/scripts/serve_ledger.py . --test-dir tests
```

历史门禁中的本机路径保留原始上下文，project.json 使用本机初始化文件。
后续发布验收必须在固定新修订上完成资源、场景、实际执行和独立证据门禁。
