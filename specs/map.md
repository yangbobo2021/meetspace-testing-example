# 规约地图

本阶段从 `stage-01-implemented`（`32306826ae8531d03d84d4465d51d419783a5d8a`）逆向整理候选需求。
用户于 2026-10-08 确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为黑盒场景设计基线，见 [DR-002](decisions/002-black-box-baseline-confirmation.md)。
用户已按 [DR-004](decisions/004-login-window-endpoint.md) 补充 identity-session-9 的精确六十秒端点；其余 95 条正文保持不变。
黑盒设计阶段全部 96 条需求充分，设计门禁 black_box_ready，见 [DR-005](decisions/005-black-box-design-ready.md)。
白盒设计阶段新增 63 个场景，独立审阅及补充设计检查通过，见 [DR-006](decisions/006-white-box-design-review.md)。
首轮完整验收正式审阅为139通过、9失败、11未证明，结果incomplete，见 [DR-007](decisions/007-first-release-acceptance.md)。
既有测试代码覆盖率审计及补测建议见 [DR-008](decisions/008-code-coverage-audit.md)，不改变首轮验收结论。
覆盖率驱动的正式设计更新见 [DR-009](decisions/009-coverage-supplement-scenarios.md)：新增8条白盒并细化2条，总计167条场景；本轮不执行补测。
后续补测与覆盖率循环见 [DR-010](decisions/010-supplemental-coverage-cycle.md)：10场景执行8通过、2失败；累计后端行与分支100%、前端分支97.17%，独立复查无新增场景建议。
已知缺陷修复与分过程提交见 [DR-011](decisions/011-release-defect-fixes.md)，完整验收须固定修复后的新修订。
修复后完整验收160通过、6失败、1未证明，新增角色刷新竞态，见 [DR-012](decisions/012-fixed-release-acceptance.md)。
角色异步续段与输入稳健性修复、75矩阵及独立复核见 [DR-013](decisions/013-identity-continuation-fix.md)，仍须新修订完整验收。
当前固定5247b360完整验收167通过、五门禁通过，覆盖率循环闭合，见 [DR-014](decisions/014-complete-fixed-release-acceptance.md)。
验证章节保留需求阶段占位；黑白盒场景、执行与审阅台账存放于 `tests/delivery-acceptance/`，公开阶段归档在 `tests/snapshots/`。
规约正文集中在 `packages/`；旧的 `docs/requirements.md` 仅保留迁移入口与旧 ID 对照。

## 编写与审阅

先阅读 [meta.md](meta.md) 和 [DR-001](decisions/001-reverse-engineered-requirements.md)。

## 目录结构

```text
decisions/    决策记录
intents/      意图记录
packages/     按共同业务意图组织的需求
map.md        需求导航
meta.md       结构、语法与引用规范
```

## 决策

| ID | 文件 | 摘要 |
| --- | --- | --- |
| [DR-000](decisions/000-spec-structure-format.md) | 000-spec-structure-format.md | 沿用的规约结构与格式 |
| [DR-001](decisions/001-reverse-engineered-requirements.md) | 001-reverse-engineered-requirements.md | 逆向来源、范围、状态与旧 ID 迁移 |
| [DR-002](decisions/002-black-box-baseline-confirmation.md) | 002-black-box-baseline-confirmation.md | 用户确认 96 条需求及黑盒设计范围 |
| [DR-003](decisions/003-black-box-design-review.md) | 003-black-box-design-review.md | 黑盒设计产出、三轮独立审阅及剩余不足 |
| [DR-004](decisions/004-login-window-endpoint.md) | 004-login-window-endpoint.md | 六十秒窗口端点确认与续轮基线 |
| [DR-005](decisions/005-black-box-design-ready.md) | 005-black-box-design-ready.md | 续轮场景充分性通过与不可变阶段档案 |
| [DR-006](decisions/006-white-box-design-review.md) | 006-white-box-design-review.md | 白盒重要实现路径设计、独立审阅与阶段档案 |
| [DR-007](decisions/007-first-release-acceptance.md) | 007-first-release-acceptance.md | 首轮完整验收、独立证据结论与公开阶段归档 |
| [DR-008](decisions/008-code-coverage-audit.md) | 008-code-coverage-audit.md | 既有测试覆盖率、未命中分支与补测建议 |
| [DR-009](decisions/009-coverage-supplement-scenarios.md) | 009-coverage-supplement-scenarios.md | 根据覆盖率更新正式场景及独立设计审阅 |
| [DR-010](decisions/010-supplemental-coverage-cycle.md) | 010-supplemental-coverage-cycle.md | 补测执行、累计覆盖率、剩余路径及循环收敛审查 |
| [DR-011](decisions/011-release-defect-fixes.md) | 011-release-defect-fixes.md | 六类已知缺陷修复及单独提交、复验边界 |
| [DR-012](decisions/012-fixed-release-acceptance.md) | 012-fixed-release-acceptance.md | 修复后完整验收、追加角色竞态与未证明分支 |
| [DR-013](decisions/013-identity-continuation-fix.md) | 013-identity-continuation-fix.md | 角色异步续段及类型校验修复、迭代开发证据 |
| [DR-014](decisions/014-complete-fixed-release-acceptance.md) | 014-complete-fixed-release-acceptance.md | 固定修复版本全量验收及覆盖率循环通过 |

## 规约包

| 文件 | 意图 |
| --- | --- |
| [identity-session.md](packages/identity-session.md) | 身份、会话与请求保护 |
| [room-discovery.md](packages/room-discovery.md) | 会议室发现、日程与筛选 |
| [reservation-creation.md](packages/reservation-creation.md) | 新预约资格、时间、冲突与重试 |
| [reservation-management.md](packages/reservation-management.md) | 预约查看、状态与取消 |
| [space-administration.md](packages/space-administration.md) | 会议室资料与可预约状态管理 |
| [team-administration.md](packages/team-administration.md) | 成员、角色与团队管理员约束 |
| [notification-center.md](packages/notification-center.md) | 站内通知与已读状态 |
| [application-runtime.md](packages/application-runtime.md) | 本地启动、示例数据与持久运行 |
| [interface-experience.md](packages/interface-experience.md) | 页面导航、表单、反馈与可访问性 |
