# reservation-creation: 新预约、冲突与重试

## 意图

使团队用户为合法时段创建唯一且可追溯的会议室预约，并明确拒绝不可接受的预约。

## 外部行为

### reservation-creation-1

当已登录用户提交新预约，预约服务应仅接受其所属团队已启用会议室 [[room-discovery-1](room-discovery.md#room-discovery-1)] 的预约，不接受另一团队或已停用的会议室。

### reservation-creation-2

当用户提交新预约资料，预约服务应按以下规则校验必填业务字段：

| 字段 | 规则 |
| --- | --- |
| 会议室编号 | 一至 2147483647 的整数 |
| 主题 | 字符串，去除首尾空格后为一至一百字符 |
| 参会人数 | 一至一百的整数，不接受布尔值或小数 |
| 请求标识 | 字符串，去除首尾空格后为一至一百字符 |

### reservation-creation-3

当用户提交预约开始和结束时间，预约服务应要求可解析且带时区的时间，以其绝对时刻进行比较。

### reservation-creation-4

当预约服务判定新预约的可预约日期，预约服务应仅接受晚于服务端当前时刻且不晚于该时刻加三十天的开始时间。

### reservation-creation-5

当预约服务判定新预约时长，预约服务应仅接受十五分钟至八小时的开始结束时间差，含两端边界。

### reservation-creation-6

当预约服务判定新预约的开放时间，预约服务应仅接受开始与结束位于同一北京时间日期且全部位于 08:00–20:00 内的时段。

### reservation-creation-7

当预约服务校验新预约的时间粒度，预约服务应要求开始与结束均对齐十五分钟，秒与微秒均为零。

### reservation-creation-8

当预约服务校验新预约参会人数，预约服务应拒绝超过该会议室当前容量 [[space-administration-5](space-administration.md#space-administration-5)] 的人数。

### reservation-creation-9

当新预约与同一会议室有效预约竞争时段，预约服务应拒绝任何重叠，包括同时提交的重叠请求；相邻时段满足前一场结束等于后一场开始时应允许预约。

### reservation-creation-10

当新预约通过全部校验，预约服务应原子保存编号、团队、会议室、预约人、主题、绝对开始结束时间、人数、创建时间和 confirmed 状态，并生成该预约的站内确认通知 [[notification-center-1](notification-center.md#notification-center-1)]。

### reservation-creation-11

当同一用户以同一请求标识重复提交相同预约内容，预约服务应返回原编号、当前状态与重放标记，不新增预约或通知，不重新判定原预约的时段资格。

### reservation-creation-12

当同一用户以已有请求标识提交不同内容，预约服务应拒绝请求且不改变原预约，内容比较包含会议室、去除首尾空格后的主题、绝对开始结束时刻及参会人数。

### reservation-creation-13

当原预约已取消后用户重放相同请求，预约服务应返回原已取消状态 [[reservation-management-7](reservation-management.md#reservation-management-7)]，不恢复预约或占用时段。

### reservation-creation-14

当新预约因资料、资格、容量或冲突校验失败，预约服务应返回具体错误且不创建预约、占用时段或确认通知。

## 验证

本阶段仅整理需求，尚未新增验证条目、场景、执行结果或证据。
逐行为的集成与系统验证由后续测试阶段补充。
