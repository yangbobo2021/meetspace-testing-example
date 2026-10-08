# DR-001: 逆向需求的来源、范围与状态

## 状态

已接受的需求整理方式；业务条目为候选逆向需求，尚待用户逐项审阅确认。
本阶段只整理需求，验证设计、测试执行和发布结论均未开展。

## 背景

- 用户要求逆向整理 MeetSpace 的需求，并参考自行车电商项目的需求存储规范。
- 用户已要求用公开 GitHub 仓库保存不同阶段的产出。
- 实现基线为 `stage-01-implemented`，修订为 `32306826ae8531d03d84d4465d51d419783a5d8a`。
- 原 `docs/requirements.md` 是二十六条粗粒度候选规则，不是已确认的业务基线。

### 整理来源

| 来源 | 用途 |
| --- | --- |
| app/server.py | 业务校验、授权、持久化与 HTTP 契约的静态依据 |
| web/app.js、web/index.html、web/style.css | 页面、表单、筛选、状态和反馈的静态依据 |
| docs/requirements.md 在实现基线中的版本 | 原有业务意图与范围；旧 ID 永久保留关联 |
| README.md、docs/release-handoff.md | 应用使用方式、示例身份和交接边界 |
| tests/test_smoke.py、docs/development-checks.md | 仅了解原有有限验证，未重新执行或扩大其结论 |
| premium-cycling/specs/meta.md、DR-000 | 原样沿用的组织、语法、ID 与引用规范 |

### 规约包的静态定位

| 规约包 | 主要源码位置 |
| --- | --- |
| identity-session | server.py 的 login、current_user、read_json、password_hash；会话常量与 Cookie 设置 |
| room-discovery | server.py 的 /api/rooms 与 day_range；app.js 的 spacesContent、roomCard |
| reservation-creation | server.py 的 create_booking 与 Store.connect；app.js 的预约提交处理 |
| reservation-management | server.py 的 /api/bookings 查询与 cancel 分支；app.js 的 bookingsContent、bookingRow、openCancel |
| space-administration | server.py 的 room_values 与会议室 POST/PATCH 分支；app.js 的 openRoom、会议室保存处理 |
| team-administration | server.py 的成员查询与角色修改分支；app.js 的 manageContent、changeRole |
| notification-center | server.py 的 notify 与通知接口；app.js 的 inboxContent、renderShell |
| application-runtime | server.py 的 main、Store.seed、Store.connect、健康接口与异常响应 |
| interface-experience | app.js 的登录、加载、弹窗与表单处理；index.html 的语义控件；style.css 的布局和焦点规则 |

## 决策

- 正文集中到 `specs/packages/`，按九个共同意图拆包，使用中文 GEARS 条目与稳定 ID。
- `map.md` 负责导航，DR 负责来源、边界和整理决策，不把实施细节当成额外业务需求。
- 本次条目描述从源码和已有文档归纳的目标行为；静态阅读不证明实际运行满足该行为，也不将潜在实现缺陷批准为产品需求。
- 各包保留规范要求的 `验证` 章节，但本阶段仅占位，不生成验证条目、测试场景、测试方法、需求 JSON 快照或测试台账。
- 规约覆盖的完整性仅针对此次需求整理；`meta-33` 要求的逐行为验证将在后续测试阶段补充，当前规约包的验收部分尚不完整。
- 原 `AUTH-*`、`ROOM-*`、`BOOK-*`、`ADMIN-*`、`NOTICE-*`、`RUN-*` ID 已公开，不改分配给其他事项；旧文档改为到新条目的映射，不再维护第二套正文。
- 运行范围为具备 Asia/Shanghai 时区数据的本地 Python 3.11+ 环境、浏览器界面与同源 HTTP API。
- 账号、团队和预约为合成示例；真实邮件、短信、SSO、注册、密码恢复、成员邀请、周期预约、支付、公网部署、高可用和备份恢复均不纳入当前版本。
- 原样沿用的 `meta.md` 与 DR-000 保留上游版权和来源标记；其 Apache-2.0 许可文本存放在 `docs/licenses/spex-Apache-2.0.txt`。

### 阅读边界

| 边界 | 本次处理 |
| --- | --- |
| 会员身份与时间 | 服务端会话和预约资格按服务端时间判断；界面状态与默认时间按浏览器时间计算，是否需统一时钟留待业务审阅 |
| 重试语义 | 仅承诺同一用户、同一请求标识、相同内容的重放；新标识不是同一次请求，取消后重放不自动恢复预约 |
| 通知数量 | 列表最多载入最近一百条；界面未读徽标统计已载入列表，不宣称全历史未读总数 |
| 会话切换 | 同一浏览器成功登录新账号替换原会话；其他浏览器的有效会话不因此注销 |
| 会议室停用 | 不接受新预约，已有预约不自动取消；停用空间仍可由管理员管理 |
| 验证状态 | 三项原有冒烟检查不构成新需求覆盖或全量发布验收结论 |

## 影响

- 后续业务确认和测试可直接引用细粒度条目，无需重新解释粗粒度规则。
- 此次只增加和整理文档，保留实现基线的应用代码与已有测试。
- GitHub 中以独立提交及 `stage-02-requirements` 标签保存需求阶段，供与实现阶段对比。
- 后续修订保留公开 ID，实质性的业务边界变化另记 DR。
