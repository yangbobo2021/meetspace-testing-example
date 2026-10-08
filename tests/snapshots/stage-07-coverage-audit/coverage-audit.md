# 当前测试代码覆盖率与补测缺口

被测修订：`5b7e2461476d4ee6bd6819d084cb1e4787c302c1`（stage-06-acceptance-run）；应用源码与首轮验收时相同。

| 业务源码 | 可执行行覆盖率 | 分支出口覆盖率 |
| --- | ---: | ---: |
| app/server.py | 380/384（98.96%） | 124/124（100.00%） |
| web/app.js | 180/181（99.44%） | 165/177（93.22%） |

按可执行行数量加权：560/565（99.12%）。
前端另有语句覆盖 317/320（99.06%），函数覆盖 85/86（98.83%）。
原有三个冒烟测试单独测得后端行覆盖290/384（75.52%）、分支71/124（57.26%）；冒烟不执行浏览器JavaScript。

## 补测清单

完整前置条件、执行矩阵、断言及证据要求保存在 [proposed-coverage-scenarios.json](proposed-coverage-scenarios.json)。
这些是8组补测建议，尚未独立审阅、尚未追加到正式159场景台账，不能计作验收通过。

| ID | 路径 | 缺口性质 | 优先级 |
| --- | --- | --- | --- |
| COV-GAP-001 | 响应写入时客户端断开及提交后重试 | 遗漏故障模式 | P1 |
| COV-GAP-002 | 真实CLI收到Ctrl+C后关闭监听并保持持久数据 | 遗漏生命周期模式 | P2 |
| COV-GAP-003 | 三种弹窗的右侧、上下侧及矩形内空白点击 | 已有设计，执行未到达 | P2 |
| COV-GAP-004 | 退出成功响应返回时仍有业务弹窗打开 | 已有设计，执行未到达 | P1 |
| COV-GAP-005 | 标记全部已读遇到真实会话失效 | 遗漏状态组合 | P1 |
| COV-GAP-006 | 角色更新后的身份401，以及自身降权后身份查询失败 | 遗漏状态组合 | P1 |
| COV-GAP-007 | 用户清空日期筛选再选择合法日期 | 遗漏输入模式 | P2 |
| COV-GAP-008 | API未支持的HTTP方法穿过标准库入口 | 测量范围之外的入口 | P1 |

弹窗点击和退出关闭弹窗已经写在现有白盒设计中，缺的是具体执行分支证据；不必重复新增同名场景。
连接中断、清空筛选值需要补充操作/故障模式；角色与401路径需要细化状态组合。
Ctrl+C检查补充启动生命周期，不把它当作已确认业务需求之外的新发布承诺。
unsupported HTTP方法及自身降权后身份查询失败，也是首轮独立审阅已经发现的语义覆盖缺口。

额外独立诊断探针执行DELETE/OPTIONS/PUT × 三种身份 × 五个API路径，共45次真实请求：均返回501 text/html，0次符合JSON error/code契约，业务数据均未变化。
该事实存于 [supplemental-http-verbs.json](supplemental-http-verbs.json)，未纳入“原有全部测试”的覆盖计数，也没有独立验收审阅。

## 未覆盖源码的逐项对应

后端未覆盖行：260（连接断开）、492/493/495（KeyboardInterrupt与最终关闭监听）；没有coverage.py报告的未命中分支弧。
前端未覆盖行：96（非法内部页面默认内容）；12个分支出口、1个函数及3个语句未命中。
逐位置的完整映射见 [uncovered-inventory.json](uncovered-inventory.json)，相同位置可被多个指标计入，不能累加成缺陷数。

另有5处防御/辅助函数出口：登录反馈DOM缺失、无身份renderShell、非法page枚举、heading默认参数、Intl星期fallback。
这些位置仍保留在覆盖率分母与清单中；未证明其可通过约定业务UI到达，不擅自认定为5个需求漏测。
可先分析可达性，再决定增加防御单元检查或支持环境测试。

## 测量范围与限制

- 分母为两份业务程序源码：app/server.py、web/app.js；空的app/__init__.py没有可执行行，HTML/CSS、测试自身、工具依赖和标准库不进入业务代码分母。
- 重跑原三个冒烟与归档内全部27个业务测试入口，包括较早API矩阵、后续补充、运行时、UI、竞态及独立子分支探针；辅助浏览器/进程脚本由对应调用者运行。资源预检、结果合并、设计检查及描述性笔记不作为额外业务入口。
- Python使用coverage.py 7.16.2（branch、thread及子进程startup计数）；JavaScript使用Istanbul 6.0.3。浏览器仍执行真实业务JS，仅副本插入计数器，CSP不放宽。
- 每个入口采用源码隔离副本与独立数据库；测试断言不改。副本修订断言适配当前stage-06 HEAD，并将旧行追踪器替换为coverage.py，避免覆盖率追踪被覆盖。
- UI续测的结果结构依赖通过本轮前序结果按序复制解决；原验收结果不作为新命中数据。初次错误的退出记录与续测依赖纠正日志保留；所有27入口最终进程退出0不表示产品断言全通过。
- `-S`启动子进程不加载sitecustomize；该启动尝试的内部执行没有子进程覆盖计数，保留此测量限制。其他正常CLI子进程已经计入；仍未证明默认8766监听的进程归属、完整默认参数与Python3.11矩阵。
- 取本轮真实命中的并集，不合并跨运行通过判定。没有为提分而运行新增场景后混入基线，没有排除未覆盖防御行。
- 后端coverage.py把行与分支机会合并得到的percent_covered不是纯行覆盖率；本报告行覆盖使用covered_lines/num_statements。
- 行/分支命中证明执行到达，不能证明断言有效或产品正确。短路布尔条件、异常类型、角色状态、事务提交时序和继承的HTTP处理需要另行分析；本次没有宣称MC/DC、所有路径或所有状态组合100%。[coverage.py官方分支测量说明](https://coverage.readthedocs.io/en/latest/branch.html)。

前一轮验收的4类缺陷、9个失败场景和11个未证明场景仍保持原结论。
本审计不会改写需求、正式场景/方法台账、原run/review/gate，也不升级发布安全结论。
环境/观察限制详见旧 [首轮验收档案](../stage-06-acceptance-run/README.md)。

## 数据与复现

- [metrics.json](metrics.json)、[backend-coverage.json](backend-coverage.json)、[frontend-coverage.json](frontend-coverage.json)：计数和未覆盖位置。
- [execution-summary.json](execution-summary.json)：27入口与实际日志；[integrity-check.json](integrity-check.json)：源码、需求及旧验收哈希。
- [html/backend/index.html](html/backend/index.html)：coverage.py原生后端报告；[html/frontend.html](html/frontend.html)：前端逐行及分支报告；[index.html](index.html)：审计概览。

在仓库根目录恢复本档案到tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06，确保正式台账及阶段06归档的harnesses已恢复到tests/delivery-acceptance/harnesses，再运行：

```sh
python3 -m pip install --target tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/tools/python coverage==7.16.2
npm install --prefix tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/tools/node istanbul-lib-instrument@6.0.3 istanbul-lib-coverage@3.2.2
node tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/instrument.js
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/replay.py
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/replay_ui.py
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/replay_extra.py
python3 tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/report_python.py
node tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/report.js
```

脚本使用本机已安装Playwright的Python路径；其他机器需配置该路径和浏览器，coverage.ini按当前仓库路径生成。
覆盖复现不要求重跑或重写正式验收工作流。
重新运行会建立新测量，需使用空输出目录以免并入旧计数；当前审计保留全部测量setup尝试以备查。
公开快照不包含重放副本数据库、会话值、工具依赖或浏览器资料；覆盖计数文件只保存源码路径及行/弧命中。
