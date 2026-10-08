# reservation-management: 预约查看、状态与取消

## 意图

使成员管理自己的预约，使管理员管理本团队预约，并在取消后保持历史与占用一致。

## 外部行为

### reservation-management-1

当用户查询预约列表，预约查询服务应按当前身份 [[identity-session-4](identity-session.md#identity-session-4)] 和请求范围返回记录：

| 范围 | 结果 |
| --- | --- |
| 未指定或 mine | 当前用户自己的全部预约 |
| team 且为管理员 | 当前用户所属团队的全部预约 |
| team 且为普通成员 | 拒绝请求 |
| 其他范围 | 拒绝无效范围 |

### reservation-management-2

当用户读取有权查看的预约，预约查询服务应提供编号、会议室编号、预约人编号与姓名、主题、开始结束时间、人数、状态、创建与取消时间，以及会议室当前名称与位置 [[space-administration-3](space-administration.md#space-administration-3)]。

### reservation-management-3

当界面判定预约的显示状态，界面应按浏览器当前时刻及记录状态作出以下分类：

| 条件 | 显示状态 |
| --- | --- |
| 记录状态为 cancelled | 已取消 |
| 未取消且结束时间不晚于当前时刻 | 已结束 |
| 未取消且开始时间不晚于当前时刻、结束仍在未来 | 进行中 |
| 未取消且开始时间在未来 | 已确认 |

### reservation-management-4

当界面展示预约列表，界面应将未取消且尚未结束的预约按开始时间升序列入“即将进行”，将已结束或已取消记录按开始时间降序列入历史区域。

### reservation-management-5

当用户请求取消预约，预约服务应仅允许预约本人或所属团队管理员操作，不允许其他成员或另一团队用户取消该预约。

### reservation-management-6

当用户请求首次取消已开始或已结束的有效预约，预约服务应以服务端当前时刻判定并拒绝取消。

### reservation-management-7

当有权用户取消尚未开始的有效预约，预约服务应原子记录 cancelled 状态和取消时间、保留原预约资料、释放日程占用 [[room-discovery-3](room-discovery.md#room-discovery-3)]，并生成预约所属成员的取消通知 [[notification-center-2](notification-center.md#notification-center-2)]。

### reservation-management-8

当有权用户再次取消已取消预约，预约服务应返回成功而不改变原取消时间、不重复释放或生成通知。

### reservation-management-9

当用户请求取消不存在或不属于其团队的预约，预约服务应返回预约不存在，不泄露另一团队的预约资料。

### reservation-management-10

当界面展示有权取消的预约卡片，界面应仅对尚未开始且未取消的预约提供取消入口，并在提交取消前显示主题、时间、会议室和确认选项。

## 验证

本阶段仅整理需求，尚未新增验证条目、场景、执行结果或证据。
逐行为的集成与系统验证由后续测试阶段补充。
