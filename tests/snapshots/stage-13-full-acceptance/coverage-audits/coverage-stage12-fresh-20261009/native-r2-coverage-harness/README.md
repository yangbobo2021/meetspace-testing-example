# 身份与角色异步续段开发回归（仅准备）

当前状态：**prepared_only_not_executed**。当前产品仍为原始 `708c9c0`，没有运行拟议源，也没有编辑正式台账、运行或旧证据。

`matrix.py` 准备 27 个独立原生 Chromium / HTTP / SQLite 子矩阵：

- 4 条真实原始反例：自身/他人角色查询跨退出与新登录、同身份两个角色操作响应重排、旧 pending 身份读跨新角色提交与 503。
- 迟到 PATCH 200/503/network/真实401、迟到角色 session503/network/真实401跨新身份。
- 同身份迟到 PATCH 成功响应与真正较晚 commit，验证按实际成功确认刷新角色，而非按点击顺序丢弃有效提交。
- 同身份旧 session503/network；当前真实 PATCH401/session401反馈；较早操作收到仍属当前身份的真实401也必须撤销身份及显示错误。
- changeRole 的 loadPage 已捕获200但期间退出/新登录，不能显示旧成功提示。
- 旧 pending200/503/network 不修改新 pending/loading/error，随后原生“重新加载”实际完成。
- 普通 nonself 成功、自降正常成功、自降 session503/network 的数据重试及整页刷新对照。

所有业务提交及200来自真实 server，真实401通过实际HTTP撤销当前会话与 route.fetch 获得。只在浏览器传输边界 hold、503 或 abort，不调用产品 helper 来制造结果。不替换源文件，不加载 `proposed-identity-continuation-fix/app.js`。

`original-evidence/` 保存原始4条失败 JSON和原始脚本的未改副本；`original-evidence-manifest.json`核对来源SHA。新 `native_original_sequences.py` 只复用两条已实测原生操作的函数体，成功期待保持身份与后台一致；原始脚本保留。

必须等主任务明确通知已应用修复后，才在项目目录运行（以下是使用说明，尚未执行）：

```sh
MEETSPACE_COVERAGE_AUDIT=/absolute/path/to/new-output \
/Users/boboyang/.cloakbrowser-codex/venv/bin/python \
  tests/delivery-acceptance/release-preparation/20261009/identity-continuation-regressions/matrix.py \
  --expected-js-sha256 <actually-applied-web-app-js-sha256> \
  --output /absolute/path/to/new-output
```

`--expected-js-sha256` 必须匹配已应用的项目源码；原始已失败 JS SHA会被拒绝。当前静审拟议 SHA为 `dcc1488e74676faacc68344513f2941615226df8bb689c93681b1e89e7feccd5`，不据此自动执行。输出目录必须为新的测试资产目录，且没有 `instrumented-app.js`，确保前端原生源码。

可用 `--only <case-id>` 执行指定项。每项隔离数据库、匿名监听端口与浏览器上下文，保存实际SHA、工作树状态/源码diff SHA、HTTP事件、角色/业务快照、DOM观察、截图及逐条断言。部分成功不得合并为整套通过；任何失败/缺证都会保留，整套有非passed项以非零退出。

开发回归不能替代修复提交后的全量167场景验收，也没有修改正式需求或生成平行台账。
