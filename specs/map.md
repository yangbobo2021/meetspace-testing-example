# 规约地图

本阶段从 `stage-01-implemented`（`32306826ae8531d03d84d4465d51d419783a5d8a`）逆向整理候选需求。
条目尚待业务确认；验证章节仅占位，没有生成场景或执行测试。
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
