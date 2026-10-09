# Stage10 新源码覆盖率审计

固定版本 `708c9c057b5c9014f4ff975fdc5774093a687abe`。后端行 **389/389（100%）**、分支 **126/126（100%）**；前端行 **197/198（99.49%）**、分支 **187/192（97.39%）**、函数 **86/86（100%）**、语句 **343/345（99.42%）**。无行/分支排除，全部分母保留。

本目录只使用当前源码新产生的计数，旧目录仅提供 coverage.py 与 Istanbul 工具。`backend-source-verification.json`核对所有现存隔离server.py的SHA并将同源码位置归一；`frontend-static-map.json`直接从当前app.js产生，所有JS输入在合并前校验映射一致（仅统一JS undefined/null序列化差异）。

30项原harness重跑包括7条unittest、完整旧API/runtime/UI最终脚本、stage09 API/identity/dialog矩阵与旧full_api_matrix和独立covered probes；12项UI续脚本在单个全新进度中顺序执行，不seed旧passed。`audit-context.json`保存每次进程退出事实；退出0不等于完整方法通过。

新增 `pending_identity_guards.py` 真实执行6条新代码路径：pending旧200遇stale token；token未变但早期真实401清user后阻止旧200复活；非self修改后恢复admin；pending重试真实401、503、网络及再次恢复。故障仅在浏览器网络边界，实际角色PATCH、会话HTTP撤销、route.fetch的200/401、loadToken、DOM和后续请求均保留。6项全部断言通过，正式设计应在既有方法独立细化与审阅，不新增平行业务需求。

`static_unsupported_control.py`另实测9项非API静态unsupported方法继承拒绝，仅兼容诊断，不冒充正式API新增场景；API的60项unsupported矩阵仍独立要求JSON。

初始两条UI断言在state先更新而DOM未完成、上一轮toast仍非空时过早检查。严格增加最终DOM/按钮恢复等待后独立两组业务断言完成；保留初始失败JSON/截图与纠正副本。runtime_edges依赖本轮runtime_complete真正创建的process-persist.sqlite，已按真实依赖顺序再执行；初始缺前置库日志保留。CLI覆盖率变体使用port0及localhost保护用户demo并启用计数，Mac无127.0.0.2别名及stdout读取适配失败尝试保留；实际默认8766/不同loopback/Python311以正式Docker矩阵证明。

剩余5条前端出口在`uncovered-inventory.json`逐位置说明，属于当前原生界面未触发的防御备用；计数保留。Tester在6条新guard路径实测后未提出额外必要场景，须由独立Reviewer确认。

覆盖率与逐场景验收证据不是同义。本审计没有修改正式ledger或run，不能据此声称全部167场景通过或允许发布。正式结论以当前Playbook单一新run、证据审阅与最终gate为准。

补充状态组合实测发现真实产品失败：changeRole本身的/session实际200跨原生logout和新登录延迟到达时，旧user覆盖新身份。自身降权→跨团队other、他人晋升→同团队bob成员两项均失败；实际后台新session始终正确，UI账号、团队/权限菜单却被旧身份改写并出现旧成功toast。参见`change-role-identity-race-results.json`及逐项HTTP/DOM/截图。这说明分支覆盖完成仍可能缺重要状态组合；须细化既有角色修改/身份竞态方法、修复产品后建立新源码新运行。本版本不批准发布。
