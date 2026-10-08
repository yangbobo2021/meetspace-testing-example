# 需求入口与旧 ID 对照

当前需求正文已迁移到 [specs/map.md](../specs/map.md)。
按自行车示例的规范，需求集中存放在 `specs/packages/`，使用 GEARS 条目和稳定的 `<pack>-<N>` ID。
用户已确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为本次黑盒场景设计基线，见 [DR-002](../specs/decisions/002-black-box-baseline-confirmation.md)。确认不代表应用已经验收。

原粗粒度规则可在 GitHub 的 [stage-01-implemented 版本](https://github.com/yangbobo2021/meetspace-testing-example/blob/stage-01-implemented/docs/requirements.md) 查阅。
旧 ID 已公开，保持原事项关联；本文件仅维护到新条目的映射，不再保存第二份业务正文。

## 旧 ID 映射

| 旧 ID | 对应规约条目 |
| --- | --- |
| AUTH-01 | [identity-session-1](../specs/packages/identity-session.md#identity-session-1)、[identity-session-2](../specs/packages/identity-session.md#identity-session-2)、[identity-session-3](../specs/packages/identity-session.md#identity-session-3) |
| AUTH-02 | [identity-session-5](../specs/packages/identity-session.md#identity-session-5)、[identity-session-6](../specs/packages/identity-session.md#identity-session-6) |
| AUTH-03 | [identity-session-8](../specs/packages/identity-session.md#identity-session-8) |
| AUTH-04 | [identity-session-9](../specs/packages/identity-session.md#identity-session-9)、[identity-session-10](../specs/packages/identity-session.md#identity-session-10) |
| ROOM-01 | [room-discovery-1](../specs/packages/room-discovery.md#room-discovery-1)、[room-discovery-2](../specs/packages/room-discovery.md#room-discovery-2)、[room-discovery-3](../specs/packages/room-discovery.md#room-discovery-3) |
| ROOM-02 | [room-discovery-5](../specs/packages/room-discovery.md#room-discovery-5)、[room-discovery-9](../specs/packages/room-discovery.md#room-discovery-9) |
| ROOM-03 | [room-discovery-4](../specs/packages/room-discovery.md#room-discovery-4)、[room-discovery-6](../specs/packages/room-discovery.md#room-discovery-6) |
| BOOK-01 | [reservation-creation-1](../specs/packages/reservation-creation.md#reservation-creation-1)、[reservation-creation-2](../specs/packages/reservation-creation.md#reservation-creation-2)、[reservation-creation-10](../specs/packages/reservation-creation.md#reservation-creation-10)、[reservation-management-1](../specs/packages/reservation-management.md#reservation-management-1)、[reservation-management-2](../specs/packages/reservation-management.md#reservation-management-2) |
| BOOK-02 | [reservation-creation-4](../specs/packages/reservation-creation.md#reservation-creation-4)、[reservation-creation-5](../specs/packages/reservation-creation.md#reservation-creation-5) |
| BOOK-03 | [reservation-creation-3](../specs/packages/reservation-creation.md#reservation-creation-3)、[reservation-creation-6](../specs/packages/reservation-creation.md#reservation-creation-6)、[reservation-creation-7](../specs/packages/reservation-creation.md#reservation-creation-7) |
| BOOK-04 | [reservation-creation-2](../specs/packages/reservation-creation.md#reservation-creation-2)、[reservation-creation-8](../specs/packages/reservation-creation.md#reservation-creation-8) |
| BOOK-05 | [reservation-creation-9](../specs/packages/reservation-creation.md#reservation-creation-9)、[reservation-creation-14](../specs/packages/reservation-creation.md#reservation-creation-14) |
| BOOK-06 | [reservation-creation-11](../specs/packages/reservation-creation.md#reservation-creation-11)、[reservation-creation-12](../specs/packages/reservation-creation.md#reservation-creation-12)、[reservation-creation-13](../specs/packages/reservation-creation.md#reservation-creation-13)、[interface-experience-16](../specs/packages/interface-experience.md#interface-experience-16) |
| BOOK-07 | [reservation-management-1](../specs/packages/reservation-management.md#reservation-management-1)、[reservation-management-5](../specs/packages/reservation-management.md#reservation-management-5)、[reservation-management-9](../specs/packages/reservation-management.md#reservation-management-9) |
| BOOK-08 | [reservation-management-6](../specs/packages/reservation-management.md#reservation-management-6)、[reservation-management-7](../specs/packages/reservation-management.md#reservation-management-7)、[reservation-management-8](../specs/packages/reservation-management.md#reservation-management-8) |
| BOOK-09 | [reservation-management-3](../specs/packages/reservation-management.md#reservation-management-3)、[reservation-management-4](../specs/packages/reservation-management.md#reservation-management-4)、[interface-experience-15](../specs/packages/interface-experience.md#interface-experience-15) |
| ADMIN-01 | [space-administration-1](../specs/packages/space-administration.md#space-administration-1)、[space-administration-2](../specs/packages/space-administration.md#space-administration-2)、[space-administration-3](../specs/packages/space-administration.md#space-administration-3)、[space-administration-4](../specs/packages/space-administration.md#space-administration-4)、[space-administration-5](../specs/packages/space-administration.md#space-administration-5)、[space-administration-9](../specs/packages/space-administration.md#space-administration-9) |
| ADMIN-02 | [space-administration-6](../specs/packages/space-administration.md#space-administration-6)、[space-administration-7](../specs/packages/space-administration.md#space-administration-7)、[space-administration-10](../specs/packages/space-administration.md#space-administration-10) |
| ADMIN-03 | [space-administration-3](../specs/packages/space-administration.md#space-administration-3)、[space-administration-8](../specs/packages/space-administration.md#space-administration-8)、[reservation-management-2](../specs/packages/reservation-management.md#reservation-management-2) |
| ADMIN-04 | [team-administration-1](../specs/packages/team-administration.md#team-administration-1)、[team-administration-2](../specs/packages/team-administration.md#team-administration-2)、[team-administration-3](../specs/packages/team-administration.md#team-administration-3)、[team-administration-6](../specs/packages/team-administration.md#team-administration-6) |
| ADMIN-05 | [team-administration-4](../specs/packages/team-administration.md#team-administration-4)、[team-administration-5](../specs/packages/team-administration.md#team-administration-5)、[team-administration-7](../specs/packages/team-administration.md#team-administration-7) |
| NOTICE-01 | [notification-center-1](../specs/packages/notification-center.md#notification-center-1)、[notification-center-2](../specs/packages/notification-center.md#notification-center-2)、[notification-center-3](../specs/packages/notification-center.md#notification-center-3) |
| NOTICE-02 | [notification-center-4](../specs/packages/notification-center.md#notification-center-4)、[notification-center-5](../specs/packages/notification-center.md#notification-center-5)、[notification-center-6](../specs/packages/notification-center.md#notification-center-6) |
| RUN-01 | [application-runtime-4](../specs/packages/application-runtime.md#application-runtime-4)、[application-runtime-5](../specs/packages/application-runtime.md#application-runtime-5) |
| RUN-02 | [interface-experience-4](../specs/packages/interface-experience.md#interface-experience-4)、[interface-experience-7](../specs/packages/interface-experience.md#interface-experience-7)、[interface-experience-8](../specs/packages/interface-experience.md#interface-experience-8)、[interface-experience-9](../specs/packages/interface-experience.md#interface-experience-9) |
| RUN-03 | [interface-experience-11](../specs/packages/interface-experience.md#interface-experience-11)、[interface-experience-12](../specs/packages/interface-experience.md#interface-experience-12)、[interface-experience-13](../specs/packages/interface-experience.md#interface-experience-13)、[interface-experience-14](../specs/packages/interface-experience.md#interface-experience-14) |
