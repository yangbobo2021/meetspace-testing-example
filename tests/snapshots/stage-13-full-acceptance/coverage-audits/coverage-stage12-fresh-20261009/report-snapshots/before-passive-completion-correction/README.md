# Stage12 固定源码新覆盖率

版本 `5247b360276f2900d20fdeab96bd75bb3ece73fa`。后端行 389/389 (100.0%)，分支 126/126 (100.0%)，函数 31/31 (100.0%)；前端行 209/210 (99.52%)，分支 207/212 (97.64%)，函数 86/86 (100%)，语句 360/362 (99.44%)。无行/分支排除，全部分母保留。Python“语句”沿coverage.py可执行源码行统计，与行分母相同；Python函数按coverage.py具名函数区域实际body执行计数，不含模块区域与匿名lambda。

计数仅由本目录新执行生成，旧目录只供工具与harness实现参考，不合并旧counter，不seed旧passed。33项初始进程作业包括全部先前30作业：实际8条标准HTTP unittest，历史完整API/runtime/UI最终脚本，stage09 API/13identity/dialog矩阵与旧full_api_matrix和covered探针。12个UI续脚本共享全新项目/进度顺序运行；runtime_edges读取本轮刚执行runtime_complete新建的库。额外34项身份竞态透明插桩矩阵、6项pending guards与9项非API静态拒绝诊断也实际重跑。另有1项运输源位置绑定纠正作业，随后正式内容设计独立passed后追加6个旧changeRole/session×新自降身份故障pending组合（24强断言），对应1个新采集作业，总35进程作业。旧报告冻结于report-snapshots/before-role-session-pending-followup，原summary SHA为1fccef1525af3f8e7a17d96b332877155f64ec61e929dc85d288e229e34fed22。新增6项只是coverage collector实测，不代正式Tester或Reviewer。初始运输结果因旧硬编码行195/252/254/260判failed；当前AST锚点实为204/261/263/269，原failed JSON保留，精准重新绑定强断言后独立4项全部passed，属于工具映射错误，不能混同产品失败。

`raw-native-r2`保留原始native34脚本，覆盖率副本仅显式加入Istanbul模式、纯源码SHA/插桩SHA双核验和scope声明。原动作、断言、网络barrier函数AST完全一致，helper及原反例序列SHA完全一致，详见`transparent-instrumentation-proof.json`。正式流程另以不插桩原源码执行矩阵，不能迁入本报告passed。`frontend-static-map.json`由固定原app.js生成，所有JS合并输入位置map核验，原行号和分母保留。`backend-source-verification.json`核对所有实际源码copy并归一同源位置。

复制harness仅修改pin/输出隔离路径、禁用旧sys.settrace覆盖计数冲突、以及已知历史DOM/按钮等待同步；业务断言不弱化，原脚本/旧失败证据不改。CLI覆盖率变体使用port0/localhost并允许coverage启动，避免操作用户demo。默认8766/另一loopback/Python311真正资源矩阵由独立正式流程证明，覆盖率变体不替代其证据。

未覆盖出口逐位置列于`uncovered-inventory.json`。确认原生范围的防御出口保留计数，不伪造状态来提升覆盖率；新未审阅出口数量 0，须独立Reviewer确认补测建议充分性。34项覆盖变体和8HTTP实测通过，未观察新产品失败；这与正式167场景通过不是同义，不能据此批准发布。本审计没有修改产品、正式ledger或run。
