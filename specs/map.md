# 规约地图

本阶段从 `stage-01-implemented`（`32306826ae8531d03d84d4465d51d419783a5d8a`）逆向整理候选需求。
用户于 2026-10-08 确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为黑盒场景设计基线，见 [DR-002](decisions/002-black-box-baseline-confirmation.md)。
用户已按 [DR-004](decisions/004-login-window-endpoint.md) 补充 identity-session-9 的精确六十秒端点；其余 95 条正文保持不变。
当前黑盒设计全部 96 条需求充分，设计门禁 black_box_ready，见 [DR-005](decisions/005-black-box-design-ready.md)。
验证章节保留需求阶段占位；黑盒场景与审阅台账存放于 `tests/delivery-acceptance/`，本阶段不执行应用测试。
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
