# 交付验收报告

- 修订：`43bea9de0b8e2f8d3bd7723a6b734f242f36c794`
- 环境：macOS arm64; Python3.12; Chromium isolated headless; stage08新增8与细化2场景补测，非167场景全量重新验收；SQLite/loopback隔离；固定2030时钟与真实CLI时钟逐项记录
- Playbook 结论：**blocked**
- 审查角色：independent_ai

## 门禁

- **requirements — passed**: 存在已确认且版本可追溯的需求快照。
- **resources — passed**: 依赖、真实集成检查及 Mock／真实端到端模式的决策已就绪。
- **scenarios — passed**: 黑盒场景经逐需求独立反事实审查，白盒审查和操作方法均完整。
- **execution — blocked**: 全部场景及依赖均在本次确切修订上完成检查并留有证据。
  - scenario BB-application-runtime-1 is unproven
  - scenario BB-application-runtime-2 is unproven
  - scenario BB-application-runtime-3 is unproven
  - scenario BB-application-runtime-4 is unproven
  - scenario BB-application-runtime-5 is unproven
  - scenario BB-application-runtime-6 is unproven
  - scenario BB-application-runtime-7 is unproven
  - scenario BB-application-runtime-8 is unproven
  - scenario BB-application-runtime-9 is unproven
  - scenario BB-identity-session-1 is unproven
  - scenario BB-identity-session-2 is unproven
  - scenario BB-identity-session-3 is unproven
  - scenario BB-identity-session-4 is unproven
  - scenario BB-identity-session-5 is unproven
  - scenario BB-identity-session-6 is unproven
  - scenario BB-identity-session-7 is unproven
  - scenario BB-identity-session-8 is unproven
  - scenario BB-identity-session-9 is unproven
  - scenario BB-identity-session-10 is unproven
  - scenario BB-identity-session-11 is unproven
  - scenario BB-identity-session-12 is unproven
  - scenario BB-identity-session-13 is unproven
  - scenario BB-identity-session-14 is unproven
  - scenario BB-interface-experience-1 is unproven
  - scenario BB-interface-experience-2 is unproven
  - scenario BB-interface-experience-3 is unproven
  - scenario BB-interface-experience-4 is unproven
  - scenario BB-interface-experience-5 is unproven
  - scenario BB-interface-experience-6 is unproven
  - scenario BB-interface-experience-7 is unproven
  - scenario BB-interface-experience-8 is unproven
  - scenario BB-interface-experience-9 is unproven
  - scenario BB-interface-experience-10 is unproven
  - scenario BB-interface-experience-11 is unproven
  - scenario BB-interface-experience-12 is unproven
  - scenario BB-interface-experience-13 is unproven
  - scenario BB-interface-experience-14 is unproven
  - scenario BB-interface-experience-15 is unproven
  - scenario BB-interface-experience-16 is unproven
  - scenario BB-notification-center-1 is unproven
  - scenario BB-notification-center-2 is unproven
  - scenario BB-notification-center-3 is unproven
  - scenario BB-notification-center-4 is unproven
  - scenario BB-notification-center-5 is unproven
  - scenario BB-notification-center-6 is unproven
  - scenario BB-notification-center-7 is unproven
  - scenario BB-reservation-creation-1 is unproven
  - scenario BB-reservation-creation-2 is unproven
  - scenario BB-reservation-creation-3 is unproven
  - scenario BB-reservation-creation-4 is unproven
  - scenario BB-reservation-creation-5 is unproven
  - scenario BB-reservation-creation-6 is unproven
  - scenario BB-reservation-creation-7 is unproven
  - scenario BB-reservation-creation-8 is unproven
  - scenario BB-reservation-creation-9 is unproven
  - scenario BB-reservation-creation-10 is unproven
  - scenario BB-reservation-creation-11 is unproven
  - scenario BB-reservation-creation-12 is unproven
  - scenario BB-reservation-creation-13 is unproven
  - scenario BB-reservation-creation-14 is unproven
  - scenario BB-reservation-management-1 is unproven
  - scenario BB-reservation-management-2 is unproven
  - scenario BB-reservation-management-3 is unproven
  - scenario BB-reservation-management-4 is unproven
  - scenario BB-reservation-management-5 is unproven
  - scenario BB-reservation-management-6 is unproven
  - scenario BB-reservation-management-7 is unproven
  - scenario BB-reservation-management-8 is unproven
  - scenario BB-reservation-management-9 is unproven
  - scenario BB-reservation-management-10 is unproven
  - scenario BB-room-discovery-1 is unproven
  - scenario BB-room-discovery-2 is unproven
  - scenario BB-room-discovery-3 is unproven
  - scenario BB-room-discovery-4 is unproven
  - scenario BB-room-discovery-5 is unproven
  - scenario BB-room-discovery-6 is unproven
  - scenario BB-room-discovery-7 is unproven
  - scenario BB-room-discovery-8 is unproven
  - scenario BB-room-discovery-9 is unproven
  - scenario BB-space-administration-1 is unproven
  - scenario BB-space-administration-2 is unproven
  - scenario BB-space-administration-3 is unproven
  - scenario BB-space-administration-4 is unproven
  - scenario BB-space-administration-5 is unproven
  - scenario BB-space-administration-6 is unproven
  - scenario BB-space-administration-7 is unproven
  - scenario BB-space-administration-8 is unproven
  - scenario BB-space-administration-9 is unproven
  - scenario BB-space-administration-10 is unproven
  - scenario BB-team-administration-1 is unproven
  - scenario BB-team-administration-2 is unproven
  - scenario BB-team-administration-3 is unproven
  - scenario BB-team-administration-4 is unproven
  - scenario BB-team-administration-5 is unproven
  - scenario BB-team-administration-6 is unproven
  - scenario BB-team-administration-7 is unproven
  - scenario WB-runtime-entry is unproven
  - scenario WB-seed-empty-existing is unproven
  - scenario WB-password-derivation is unproven
  - scenario WB-persistence-restart is unproven
  - scenario WB-health-static-dispatch is unproven
  - scenario WB-request-origin is unproven
  - scenario WB-json-envelope is unproven
  - scenario WB-errors-and-response is unproven
  - scenario WB-transaction-failure-matrix is unproven
  - scenario WB-session-join is unproven
  - scenario WB-session-expiry is unproven
  - scenario WB-login-window-lock is unproven
  - scenario WB-login-switch-and-cookies is unproven
  - scenario WB-logout-revocation is unproven
  - scenario WB-route-authorizations is unproven
  - scenario WB-rooms-team-deserialization is unproven
  - scenario WB-day-range-intersection is unproven
  - scenario WB-agenda-title-redaction is unproven
  - scenario WB-booking-fields-guards is unproven
  - scenario WB-datetime-parse-normalize is unproven
  - scenario WB-booking-horizon is unproven
  - scenario WB-booking-duration is unproven
  - scenario WB-booking-open-hours is unproven
  - scenario WB-room-eligibility-capacity is unproven
  - scenario WB-booking-conflict-serialization is unproven
  - scenario WB-booking-insert-notify is unproven
  - scenario WB-idempotency-priority is unproven
  - scenario WB-idempotency-user-concurrency is unproven
  - scenario WB-booking-query-scope-join is unproven
  - scenario WB-cancel-authorization-and-clock is unproven
  - scenario WB-cancel-atomic-idempotent is unproven
  - scenario WB-notifications-select-limit is unproven
  - scenario WB-notifications-mark-all is unproven
  - scenario WB-room-write-and-return is unproven
  - scenario WB-room-text-capacity-active is unproven
  - scenario WB-room-equipment-set is unproven
  - scenario WB-room-name-unique-concurrency is unproven
  - scenario WB-room-state-existing-bookings is unproven
  - scenario WB-member-select-role-guards is unproven
  - scenario WB-last-admin-lock is unproven
  - scenario WB-ui-start-session-errors is unproven
  - scenario WB-ui-api-error-session-transition is unproven
  - scenario WB-ui-login-navigation is unproven
  - scenario WB-ui-load-parallel-error is unproven
  - scenario WB-ui-load-token-races is unproven
  - scenario WB-ui-filters-statistics is unproven
  - scenario WB-ui-room-timeline-agenda is unproven
  - scenario WB-ui-timezone-format is unproven
  - scenario WB-ui-booking-status-sort is unproven
  - scenario WB-ui-notification-render is unproven
  - scenario WB-ui-default-times is unproven
  - scenario WB-ui-booking-draft-key is unproven
  - scenario WB-ui-submit-button-matrix is unproven
  - scenario WB-ui-room-edit-draft is unproven
  - scenario WB-ui-role-demotion-reload is unproven
  - scenario WB-ui-text-escaping is unproven
  - scenario WB-ui-accessibility-focus is unproven
  - scenario WB-ui-responsive-breakpoints is unproven
  - scenario WB-seed-failure-retry is unproven
  - scenario WB-login-format-boundaries is unproven
  - scenario WB-idempotency-absolute-precision is unproven
  - scenario WB-ui-self-demotion-session-failure is failed
  - scenario WB-http-unsupported-methods is failed
- **review — blocked**: 本次运行的证据和覆盖范围均经实质审查。
  - coverage review is not passed with a reason
  - coverage review has unassessed or uncovered branches
  - scenario BB-application-runtime-1 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-2 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-3 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-4 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-5 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-6 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-7 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-8 lacks a passed, reasoned evidence review
  - scenario BB-application-runtime-9 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-1 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-2 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-3 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-4 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-5 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-6 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-7 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-8 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-9 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-10 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-11 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-12 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-13 lacks a passed, reasoned evidence review
  - scenario BB-identity-session-14 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-1 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-2 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-3 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-4 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-5 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-6 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-7 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-8 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-9 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-10 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-11 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-12 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-13 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-14 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-15 lacks a passed, reasoned evidence review
  - scenario BB-interface-experience-16 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-1 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-2 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-3 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-4 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-5 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-6 lacks a passed, reasoned evidence review
  - scenario BB-notification-center-7 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-1 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-2 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-3 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-4 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-5 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-6 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-7 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-8 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-9 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-10 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-11 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-12 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-13 lacks a passed, reasoned evidence review
  - scenario BB-reservation-creation-14 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-1 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-2 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-3 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-4 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-5 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-6 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-7 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-8 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-9 lacks a passed, reasoned evidence review
  - scenario BB-reservation-management-10 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-1 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-2 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-3 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-4 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-5 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-6 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-7 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-8 lacks a passed, reasoned evidence review
  - scenario BB-room-discovery-9 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-1 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-2 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-3 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-4 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-5 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-6 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-7 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-8 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-9 lacks a passed, reasoned evidence review
  - scenario BB-space-administration-10 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-1 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-2 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-3 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-4 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-5 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-6 lacks a passed, reasoned evidence review
  - scenario BB-team-administration-7 lacks a passed, reasoned evidence review
  - scenario WB-runtime-entry lacks a passed, reasoned evidence review
  - scenario WB-seed-empty-existing lacks a passed, reasoned evidence review
  - scenario WB-password-derivation lacks a passed, reasoned evidence review
  - scenario WB-persistence-restart lacks a passed, reasoned evidence review
  - scenario WB-health-static-dispatch lacks a passed, reasoned evidence review
  - scenario WB-request-origin lacks a passed, reasoned evidence review
  - scenario WB-json-envelope lacks a passed, reasoned evidence review
  - scenario WB-errors-and-response lacks a passed, reasoned evidence review
  - scenario WB-transaction-failure-matrix lacks a passed, reasoned evidence review
  - scenario WB-session-join lacks a passed, reasoned evidence review
  - scenario WB-session-expiry lacks a passed, reasoned evidence review
  - scenario WB-login-window-lock lacks a passed, reasoned evidence review
  - scenario WB-login-switch-and-cookies lacks a passed, reasoned evidence review
  - scenario WB-logout-revocation lacks a passed, reasoned evidence review
  - scenario WB-route-authorizations lacks a passed, reasoned evidence review
  - scenario WB-rooms-team-deserialization lacks a passed, reasoned evidence review
  - scenario WB-day-range-intersection lacks a passed, reasoned evidence review
  - scenario WB-agenda-title-redaction lacks a passed, reasoned evidence review
  - scenario WB-booking-fields-guards lacks a passed, reasoned evidence review
  - scenario WB-datetime-parse-normalize lacks a passed, reasoned evidence review
  - scenario WB-booking-horizon lacks a passed, reasoned evidence review
  - scenario WB-booking-duration lacks a passed, reasoned evidence review
  - scenario WB-booking-open-hours lacks a passed, reasoned evidence review
  - scenario WB-room-eligibility-capacity lacks a passed, reasoned evidence review
  - scenario WB-booking-conflict-serialization lacks a passed, reasoned evidence review
  - scenario WB-booking-insert-notify lacks a passed, reasoned evidence review
  - scenario WB-idempotency-priority lacks a passed, reasoned evidence review
  - scenario WB-idempotency-user-concurrency lacks a passed, reasoned evidence review
  - scenario WB-booking-query-scope-join lacks a passed, reasoned evidence review
  - scenario WB-cancel-authorization-and-clock lacks a passed, reasoned evidence review
  - scenario WB-cancel-atomic-idempotent lacks a passed, reasoned evidence review
  - scenario WB-notifications-select-limit lacks a passed, reasoned evidence review
  - scenario WB-notifications-mark-all lacks a passed, reasoned evidence review
  - scenario WB-room-write-and-return lacks a passed, reasoned evidence review
  - scenario WB-room-text-capacity-active lacks a passed, reasoned evidence review
  - scenario WB-room-equipment-set lacks a passed, reasoned evidence review
  - scenario WB-room-name-unique-concurrency lacks a passed, reasoned evidence review
  - scenario WB-room-state-existing-bookings lacks a passed, reasoned evidence review
  - scenario WB-member-select-role-guards lacks a passed, reasoned evidence review
  - scenario WB-last-admin-lock lacks a passed, reasoned evidence review
  - scenario WB-ui-start-session-errors lacks a passed, reasoned evidence review
  - scenario WB-ui-api-error-session-transition lacks a passed, reasoned evidence review
  - scenario WB-ui-login-navigation lacks a passed, reasoned evidence review
  - scenario WB-ui-load-parallel-error lacks a passed, reasoned evidence review
  - scenario WB-ui-load-token-races lacks a passed, reasoned evidence review
  - scenario WB-ui-filters-statistics lacks a passed, reasoned evidence review
  - scenario WB-ui-room-timeline-agenda lacks a passed, reasoned evidence review
  - scenario WB-ui-timezone-format lacks a passed, reasoned evidence review
  - scenario WB-ui-booking-status-sort lacks a passed, reasoned evidence review
  - scenario WB-ui-notification-render lacks a passed, reasoned evidence review
  - scenario WB-ui-default-times lacks a passed, reasoned evidence review
  - scenario WB-ui-booking-draft-key lacks a passed, reasoned evidence review
  - scenario WB-ui-submit-button-matrix lacks a passed, reasoned evidence review
  - scenario WB-ui-room-edit-draft lacks a passed, reasoned evidence review
  - scenario WB-ui-role-demotion-reload lacks a passed, reasoned evidence review
  - scenario WB-ui-text-escaping lacks a passed, reasoned evidence review
  - scenario WB-ui-accessibility-focus lacks a passed, reasoned evidence review
  - scenario WB-ui-responsive-breakpoints lacks a passed, reasoned evidence review
  - scenario WB-seed-failure-retry lacks a passed, reasoned evidence review
  - scenario WB-login-format-boundaries lacks a passed, reasoned evidence review
  - scenario WB-idempotency-absolute-precision lacks a passed, reasoned evidence review
  - scenario WB-ui-self-demotion-session-failure lacks a passed, reasoned evidence review
  - scenario WB-http-unsupported-methods lacks a passed, reasoned evidence review

## 场景

| 场景 | 需求 | 执行 | 证据审查 | 证据 |
| --- | --- | --- | --- | --- |
| BB-application-runtime-1 | application-runtime-1 | unproven | unproven | scope.json |
| BB-application-runtime-2 | application-runtime-2 | unproven | unproven | scope.json |
| BB-application-runtime-3 | application-runtime-3 | unproven | unproven | scope.json |
| BB-application-runtime-4 | application-runtime-4 | unproven | unproven | scope.json |
| BB-application-runtime-5 | application-runtime-5 | unproven | unproven | scope.json |
| BB-application-runtime-6 | application-runtime-6 | unproven | unproven | scope.json |
| BB-application-runtime-7 | application-runtime-7 | unproven | unproven | scope.json |
| BB-application-runtime-8 | application-runtime-8 | unproven | unproven | scope.json |
| BB-application-runtime-9 | application-runtime-9, notification-center-1, notification-center-2 | unproven | unproven | scope.json |
| BB-identity-session-1 | identity-session-1 | unproven | unproven | scope.json |
| BB-identity-session-2 | identity-session-2 | unproven | unproven | scope.json |
| BB-identity-session-3 | identity-session-3 | unproven | unproven | scope.json |
| BB-identity-session-4 | identity-session-4, team-administration-5 | unproven | unproven | scope.json |
| BB-identity-session-5 | identity-session-5 | unproven | unproven | scope.json |
| BB-identity-session-6 | identity-session-6 | unproven | unproven | scope.json |
| BB-identity-session-7 | identity-session-7 | unproven | unproven | scope.json |
| BB-identity-session-8 | identity-session-8 | unproven | unproven | scope.json |
| BB-identity-session-9 | identity-session-9 | unproven | unproven | scope.json |
| BB-identity-session-10 | identity-session-10 | unproven | unproven | scope.json |
| BB-identity-session-11 | identity-session-11 | unproven | unproven | scope.json |
| BB-identity-session-12 | identity-session-12 | unproven | unproven | scope.json |
| BB-identity-session-13 | identity-session-13 | unproven | unproven | scope.json |
| BB-identity-session-14 | identity-session-14 | unproven | unproven | scope.json |
| BB-interface-experience-1 | interface-experience-1 | unproven | unproven | scope.json |
| BB-interface-experience-2 | interface-experience-2 | unproven | unproven | scope.json |
| BB-interface-experience-3 | interface-experience-3 | unproven | unproven | scope.json |
| BB-interface-experience-4 | interface-experience-4 | unproven | unproven | scope.json |
| BB-interface-experience-5 | interface-experience-5 | unproven | unproven | scope.json |
| BB-interface-experience-6 | interface-experience-6 | unproven | unproven | scope.json |
| BB-interface-experience-7 | interface-experience-7 | unproven | unproven | scope.json |
| BB-interface-experience-8 | interface-experience-8 | unproven | unproven | scope.json |
| BB-interface-experience-9 | interface-experience-9 | unproven | unproven | scope.json |
| BB-interface-experience-10 | interface-experience-10 | unproven | unproven | scope.json |
| BB-interface-experience-11 | interface-experience-11 | unproven | unproven | scope.json |
| BB-interface-experience-12 | interface-experience-12 | unproven | unproven | scope.json |
| BB-interface-experience-13 | interface-experience-13 | unproven | unproven | scope.json |
| BB-interface-experience-14 | interface-experience-14 | unproven | unproven | scope.json |
| BB-interface-experience-15 | interface-experience-15 | unproven | unproven | scope.json |
| BB-interface-experience-16 | interface-experience-16, reservation-creation-11, reservation-creation-12 | unproven | unproven | scope.json |
| BB-notification-center-1 | notification-center-1, reservation-creation-10 | unproven | unproven | scope.json |
| BB-notification-center-2 | notification-center-2, reservation-management-8 | unproven | unproven | scope.json |
| BB-notification-center-3 | notification-center-3 | unproven | unproven | scope.json |
| BB-notification-center-4 | notification-center-4 | unproven | unproven | scope.json |
| BB-notification-center-5 | notification-center-5 | unproven | unproven | scope.json |
| BB-notification-center-6 | notification-center-6 | unproven | unproven | scope.json |
| BB-notification-center-7 | notification-center-7 | unproven | unproven | scope.json |
| BB-reservation-creation-1 | reservation-creation-1, space-administration-7 | unproven | unproven | scope.json |
| BB-reservation-creation-2 | reservation-creation-2 | unproven | unproven | scope.json |
| BB-reservation-creation-3 | reservation-creation-3 | unproven | unproven | scope.json |
| BB-reservation-creation-4 | reservation-creation-4 | unproven | unproven | scope.json |
| BB-reservation-creation-5 | reservation-creation-5 | unproven | unproven | scope.json |
| BB-reservation-creation-6 | reservation-creation-6 | unproven | unproven | scope.json |
| BB-reservation-creation-7 | reservation-creation-7 | unproven | unproven | scope.json |
| BB-reservation-creation-8 | reservation-creation-8 | unproven | unproven | scope.json |
| BB-reservation-creation-9 | reservation-creation-9, reservation-creation-14 | unproven | unproven | scope.json |
| BB-reservation-creation-10 | reservation-creation-10, notification-center-1 | unproven | unproven | scope.json |
| BB-reservation-creation-11 | reservation-creation-11 | unproven | unproven | scope.json |
| BB-reservation-creation-12 | reservation-creation-12 | unproven | unproven | scope.json |
| BB-reservation-creation-13 | reservation-creation-13, reservation-management-7 | unproven | unproven | scope.json |
| BB-reservation-creation-14 | reservation-creation-14 | unproven | unproven | scope.json |
| BB-reservation-management-1 | reservation-management-1, team-administration-5 | unproven | unproven | scope.json |
| BB-reservation-management-2 | reservation-management-2, space-administration-3, space-administration-8 | unproven | unproven | scope.json |
| BB-reservation-management-3 | reservation-management-3 | unproven | unproven | scope.json |
| BB-reservation-management-4 | reservation-management-4 | unproven | unproven | scope.json |
| BB-reservation-management-5 | reservation-management-5 | unproven | unproven | scope.json |
| BB-reservation-management-6 | reservation-management-6 | unproven | unproven | scope.json |
| BB-reservation-management-7 | reservation-management-7, notification-center-2 | unproven | unproven | scope.json |
| BB-reservation-management-8 | reservation-management-8 | unproven | unproven | scope.json |
| BB-reservation-management-9 | reservation-management-9 | unproven | unproven | scope.json |
| BB-reservation-management-10 | reservation-management-10 | unproven | unproven | scope.json |
| BB-room-discovery-1 | room-discovery-1 | unproven | unproven | scope.json |
| BB-room-discovery-2 | room-discovery-2 | unproven | unproven | scope.json |
| BB-room-discovery-3 | room-discovery-3 | unproven | unproven | scope.json |
| BB-room-discovery-4 | room-discovery-4 | unproven | unproven | scope.json |
| BB-room-discovery-5 | room-discovery-5 | unproven | unproven | scope.json |
| BB-room-discovery-6 | room-discovery-6, room-discovery-4 | unproven | unproven | scope.json |
| BB-room-discovery-7 | room-discovery-7 | unproven | unproven | scope.json |
| BB-room-discovery-8 | room-discovery-8 | unproven | unproven | scope.json |
| BB-room-discovery-9 | room-discovery-9 | unproven | unproven | scope.json |
| BB-space-administration-1 | space-administration-1 | unproven | unproven | scope.json |
| BB-space-administration-2 | space-administration-2 | unproven | unproven | scope.json |
| BB-space-administration-3 | space-administration-3 | unproven | unproven | scope.json |
| BB-space-administration-4 | space-administration-4 | unproven | unproven | scope.json |
| BB-space-administration-5 | space-administration-5 | unproven | unproven | scope.json |
| BB-space-administration-6 | space-administration-6 | unproven | unproven | scope.json |
| BB-space-administration-7 | space-administration-7, reservation-creation-1 | unproven | unproven | scope.json |
| BB-space-administration-8 | space-administration-8, reservation-creation-8 | unproven | unproven | scope.json |
| BB-space-administration-9 | space-administration-9 | unproven | unproven | scope.json |
| BB-space-administration-10 | space-administration-10 | unproven | unproven | scope.json |
| BB-team-administration-1 | team-administration-1 | unproven | unproven | scope.json |
| BB-team-administration-2 | team-administration-2 | unproven | unproven | scope.json |
| BB-team-administration-3 | team-administration-3 | unproven | unproven | scope.json |
| BB-team-administration-4 | team-administration-4 | unproven | unproven | scope.json |
| BB-team-administration-5 | team-administration-5, identity-session-4 | unproven | unproven | scope.json |
| BB-team-administration-6 | team-administration-6 | unproven | unproven | scope.json |
| BB-team-administration-7 | team-administration-7 | unproven | unproven | scope.json |
| WB-runtime-entry | application-runtime-1, application-runtime-2 | unproven | unproven | scope.json |
| WB-seed-empty-existing | application-runtime-3, application-runtime-4 | unproven | unproven | scope.json |
| WB-password-derivation | identity-session-1, identity-session-2, identity-session-3, identity-session-13 | unproven | unproven | scope.json |
| WB-persistence-restart | application-runtime-5 | unproven | unproven | scope.json |
| WB-health-static-dispatch | application-runtime-1, application-runtime-6, application-runtime-7, identity-session-5 | unproven | unproven | scope.json |
| WB-request-origin | identity-session-10, application-runtime-9 | unproven | unproven | scope.json |
| WB-json-envelope | identity-session-11, application-runtime-7, application-runtime-9 | unproven | unproven | scope.json |
| WB-errors-and-response | application-runtime-7, application-runtime-8 | unproven | unproven | scope.json |
| WB-transaction-failure-matrix | application-runtime-9, application-runtime-8, reservation-creation-10, reservation-management-7, notification-center-1, notification-center-2 | unproven | unproven | scope.json |
| WB-session-join | identity-session-4, identity-session-5, team-administration-5 | unproven | unproven | scope.json |
| WB-session-expiry | identity-session-6, identity-session-2 | unproven | unproven | scope.json |
| WB-login-window-lock | identity-session-1, identity-session-3, identity-session-9 | unproven | unproven | scope.json |
| WB-login-switch-and-cookies | identity-session-2, identity-session-3, identity-session-7, identity-session-12, identity-session-14 | unproven | unproven | scope.json |
| WB-logout-revocation | identity-session-8, identity-session-12, application-runtime-9 | unproven | unproven | scope.json |
| WB-route-authorizations | space-administration-1, team-administration-1, team-administration-2, reservation-management-1, identity-session-5 | unproven | unproven | scope.json |
| WB-rooms-team-deserialization | room-discovery-1, space-administration-7 | unproven | unproven | scope.json |
| WB-day-range-intersection | room-discovery-2, room-discovery-3 | unproven | unproven | scope.json |
| WB-agenda-title-redaction | room-discovery-4, room-discovery-6 | unproven | unproven | scope.json |
| WB-booking-fields-guards | reservation-creation-2, reservation-creation-14 | unproven | unproven | scope.json |
| WB-datetime-parse-normalize | reservation-creation-3, reservation-creation-12 | unproven | unproven | scope.json |
| WB-booking-horizon | reservation-creation-4, reservation-creation-14 | unproven | unproven | scope.json |
| WB-booking-duration | reservation-creation-5, reservation-creation-14 | unproven | unproven | scope.json |
| WB-booking-open-hours | reservation-creation-6, reservation-creation-7, reservation-creation-14 | unproven | unproven | scope.json |
| WB-room-eligibility-capacity | reservation-creation-1, reservation-creation-8, space-administration-7, space-administration-10 | unproven | unproven | scope.json |
| WB-booking-conflict-serialization | reservation-creation-9, reservation-creation-14, application-runtime-9 | unproven | unproven | scope.json |
| WB-booking-insert-notify | reservation-creation-10, notification-center-1 | unproven | unproven | scope.json |
| WB-idempotency-priority | reservation-creation-11, reservation-creation-13, reservation-creation-12 | unproven | unproven | scope.json |
| WB-idempotency-user-concurrency | reservation-creation-11, reservation-creation-12, reservation-creation-10 | unproven | unproven | scope.json |
| WB-booking-query-scope-join | reservation-management-1, reservation-management-2, space-administration-3, identity-session-4 | unproven | unproven | scope.json |
| WB-cancel-authorization-and-clock | reservation-management-5, reservation-management-6, reservation-management-9 | unproven | unproven | scope.json |
| WB-cancel-atomic-idempotent | reservation-management-7, reservation-management-8, notification-center-2 | unproven | unproven | scope.json |
| WB-notifications-select-limit | notification-center-3, notification-center-4 | unproven | unproven | scope.json |
| WB-notifications-mark-all | notification-center-5, application-runtime-9 | unproven | unproven | scope.json |
| WB-room-write-and-return | space-administration-2, space-administration-3, space-administration-9 | unproven | unproven | scope.json |
| WB-room-text-capacity-active | space-administration-5, space-administration-2, space-administration-3 | unproven | unproven | scope.json |
| WB-room-equipment-set | space-administration-6 | unproven | unproven | scope.json |
| WB-room-name-unique-concurrency | space-administration-4, application-runtime-8, application-runtime-9 | unproven | unproven | scope.json |
| WB-room-state-existing-bookings | space-administration-7, space-administration-8, space-administration-10 | unproven | unproven | scope.json |
| WB-member-select-role-guards | team-administration-1, team-administration-2, team-administration-3, team-administration-6 | unproven | unproven | scope.json |
| WB-last-admin-lock | team-administration-4, team-administration-5 | unproven | unproven | scope.json |
| WB-ui-start-session-errors | identity-session-4, interface-experience-4, interface-experience-10 | unproven | unproven | scope.json |
| WB-ui-api-error-session-transition | interface-experience-9, interface-experience-10, identity-session-3 | unproven | unproven | scope.json |
| WB-ui-login-navigation | interface-experience-1, interface-experience-2, identity-session-2, identity-session-7 | unproven | unproven | scope.json |
| WB-ui-load-parallel-error | interface-experience-3, interface-experience-4 | unproven | unproven | scope.json |
| WB-ui-load-token-races | interface-experience-3, interface-experience-4, interface-experience-10 | unproven | unproven | scope.json |
| WB-ui-filters-statistics | room-discovery-5, room-discovery-8, room-discovery-9 | unproven | unproven | scope.json |
| WB-ui-room-timeline-agenda | room-discovery-6, room-discovery-7, space-administration-7 | unproven | unproven | scope.json |
| WB-ui-timezone-format | interface-experience-15, room-discovery-2 | unproven | unproven | scope.json |
| WB-ui-booking-status-sort | reservation-management-3, reservation-management-4, reservation-management-10 | unproven | unproven | scope.json |
| WB-ui-notification-render | notification-center-6, notification-center-7, notification-center-5, interface-experience-7 | unproven | unproven | scope.json |
| WB-ui-default-times | interface-experience-6, interface-experience-5 | unproven | unproven | scope.json |
| WB-ui-booking-draft-key | interface-experience-16, reservation-creation-11, reservation-creation-12, interface-experience-9 | unproven | unproven | scope.json |
| WB-ui-submit-button-matrix | interface-experience-7, interface-experience-9, interface-experience-8 | unproven | unproven | scope.json |
| WB-ui-room-edit-draft | space-administration-2, space-administration-3, interface-experience-9 | unproven | unproven | scope.json |
| WB-ui-role-demotion-reload | team-administration-7, team-administration-4, interface-experience-8 | unproven | unproven | scope.json |
| WB-ui-logout-races | identity-session-8, interface-experience-10, interface-experience-3 | passed | passed | evidence/coverage-cycle/evidence/ui-dialogs/booking-success.json, evidence/coverage-cycle/evidence/ui-dialogs/booking-non401-error.json, evidence/coverage-cycle/evidence/ui-dialogs/room-success.json, evidence/coverage-cycle/evidence/ui-dialogs/room-non401-error.json, evidence/coverage-cycle/evidence/ui-dialogs/confirm-success.json, evidence/coverage-cycle/evidence/ui-dialogs/confirm-non401-error.json, evidence/coverage-cycle/evidence/ui-dialogs/503.json, evidence/coverage-cycle/evidence/ui-dialogs/network.json |
| WB-ui-dialog-close-no-write | interface-experience-11, reservation-management-10 | passed | passed | evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-X.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-left.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-right.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-top.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-booking-child.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-X.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-left.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-right.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-top.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-room-child.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-X.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-left.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-right.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-top.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-child.json, evidence/coverage-cycle/evidence/ui-dialogs/1280-confirm-retain.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-X.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-left.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-right.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-top.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/390-booking-child.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-X.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-left.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-right.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-top.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/390-room-child.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-X.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-left.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-right.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-top.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-child.json, evidence/coverage-cycle/evidence/ui-dialogs/390-confirm-retain.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-X.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-left.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-right.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-top.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/320-booking-child.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-X.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-left.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-right.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-top.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/320-room-child.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-X.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-Escape.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-left.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-right.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-top.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-bottom.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-padding.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-child.json, evidence/coverage-cycle/evidence/ui-dialogs/320-confirm-retain.json |
| WB-ui-text-escaping | interface-experience-14, interface-experience-13 | unproven | unproven | scope.json |
| WB-ui-accessibility-focus | interface-experience-13 | unproven | unproven | scope.json |
| WB-ui-responsive-breakpoints | interface-experience-12 | unproven | unproven | scope.json |
| WB-seed-failure-retry | application-runtime-3, application-runtime-4, application-runtime-9 | unproven | unproven | scope.json |
| WB-login-format-boundaries | identity-session-1, identity-session-9 | unproven | unproven | scope.json |
| WB-idempotency-absolute-precision | reservation-creation-3, reservation-creation-12, reservation-creation-11 | unproven | unproven | scope.json |
| WB-response-transport-disconnect | application-runtime-7, application-runtime-9 | passed | passed | evidence/coverage-cycle/api-evidence/WB-response-transport-disconnect.json |
| WB-booking-response-loss-replay | reservation-creation-11, reservation-creation-12, notification-center-1, application-runtime-9 | passed | passed | evidence/coverage-cycle/api-evidence/WB-booking-response-loss-replay.json |
| WB-runtime-sigint-persistence | application-runtime-2, application-runtime-4, application-runtime-5 | passed | passed | evidence/coverage-cycle/api-evidence/WB-runtime-sigint-persistence.json |
| WB-ui-mark-read-session-expiry | identity-session-5, interface-experience-10, notification-center-5 | passed | passed | evidence/coverage-cycle/ui-identity/mark-expiry.json, evidence/coverage-cycle/ui-identity/mark-revocation.json |
| WB-ui-role-update-session-expiry | team-administration-2, team-administration-7, identity-session-5, interface-experience-10 | passed | passed | evidence/coverage-cycle/ui-identity/role-self-before-patch.json, evidence/coverage-cycle/ui-identity/role-self-after-commit.json, evidence/coverage-cycle/ui-identity/role-other-before-patch.json, evidence/coverage-cycle/ui-identity/role-other-after-commit.json |
| WB-ui-self-demotion-session-failure | team-administration-7, team-administration-4, interface-experience-8 | failed | failed | evidence/coverage-cycle/ui-identity/demote-503-data-retry.json, evidence/coverage-cycle/ui-identity/demote-503-reload.json, evidence/coverage-cycle/ui-identity/demote-network-data-retry.json, evidence/coverage-cycle/ui-identity/demote-network-reload.json, evidence/coverage-cycle/ui-identity/demote-normal-control.json, evidence/coverage-cycle/ui-identity/other-patch-failure-control.json |
| WB-ui-date-filter-empty-recovery | room-discovery-2, interface-experience-3 | passed | passed | evidence/coverage-cycle/ui-identity/date-empty-recovery.json |
| WB-http-unsupported-methods | application-runtime-7, identity-session-5 | failed | failed | evidence/coverage-cycle/api-evidence/WB-http-unsupported-methods.json |

此表记录执行结论；实质验收判断须结合本次运行的证据和 review.json。状态枚举及检查器诊断保留原值。
