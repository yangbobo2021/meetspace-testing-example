## Specs (Source of Truth)

- 规约存放于 `specs/`；从 `specs/map.md` 开始定位上下文，编写前阅读 `specs/meta.md`。
- 用户已确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为黑盒场景设计基线，见 DR-002；identity-session-9 的精确六十秒端点按 DR-004 补充，确认不代表应用验收通过。
- 按共同意图拆分规约包，每条需求采用 GEARS 句式和稳定的 `<pack>-<N>` ID；依赖用行内条目引用表达。
- 新增或修改规约时同步索引及相关 DR，保留已公开 ID，不生成并行的业务需求正文。
- 用户已授权使用 app-delivery-acceptance Skill 完成应用验收，测试资产固定在 `tests/delivery-acceptance/`；首轮完整流程未通过，正式审阅 139 通过、9 失败、11 未证明，见 DR-007；测试流程不修改应用或原测试，开发修复后针对新修订建立新运行。
- 代码覆盖率审计见 DR-008 与阶段07档案；补测建议未改写正式台账、未独立审阅或证明通过，后端分支100%不代表异常类型及状态组合完整。
- 用户已同意根据覆盖率补测建议更新设计，见DR-009与阶段08档案；新增8白盒、细化2旧场景，当前96黑盒+71白盒=167场景、176方法；该设计阶段未执行补测，旧运行不能验证新定义。
- 后续补测与覆盖率循环见DR-010及阶段09档案；10场景真实执行8通过、2失败，178分项116通过/62失败，其他157场景未在本轮重执行；累计同源码计数后端行/分支100%、前端分支97.17%，独立复查无新设计建议，仍不批准发布。
- 用户随后授权修复六类已知缺陷、完整重新验收及独立发布审阅，且每个过程单独提交，见DR-011；修复在开发阶段完成，提交stage-10-fixes后才启动新的Skill完整验收，保留旧失败记录及标签。
- 708c9c0完整Skill流程已终结incomplete，正式160通过/6失败/1未证明，见DR-012及stage-11-failed-acceptance；四个角色身份竞态已独立复现，下一开发修复及完整重验继续原授权，各自提交。
- stage-12-identity-fixes按DR-013开发修复身份代次、角色刷新序、旧loadPage失效、旧PATCH失败守卫及role字符串校验；最终75矩阵/8HTTP通过，独立19原生/8HTTP通过，r1三失败保持，完整验收尚未完成。
- 下一Skill流程先阅读tests/delivery-acceptance/current-release-context.json；在167场景/176方法原ID内明确角色原生34矩阵的重要状态、刷新源码依据、独立复审。stage10失败notice只作历史，不据此将新源码预判失败或通过。
- 历史app执行已被自动审批拒绝，不重试该动作；下一Analyst/Reviewer须明确审阅legacy-fixture-method-review.json提出的synthetic历史格式方法，只执行新HEAD，历史结果只作oracle来源；Tester须在本轮新run真实执行，不复用开发passed。
- 完整复验复用当前96需求/167场景/176方法稳定ID，白盒源码位置与实现依据须按新修订独立复审；全程不得改产品或以旧passed充当新运行证据。
- 新验收资源准备在tests/delivery-acceptance/release-preparation/20261009；已有uv Python3.11与Docker --network none隔离默认8766/不同loopback，不操作用户demo；harness可按正式需求修复写死的旧失败UI形态，须保留旧副本及独立理由。
- `specs/meta.md` 与 `specs/decisions/000-spec-structure-format.md` 沿用自行车项目的原文件，未经人类授权不修改。
- 修改完成后运行 `npx @sublang/spex lint`；结构检查通过不代表业务需求已确认或应用已验收。

- stage-13-full-acceptance按DR-014：5247b360完整167执行/独立审阅通过，五门禁通过；身份重要矩阵40、176稳定方法，后端行/分支100%、前端99.52%/97.64%，当前覆盖率无新必要建议；发布审阅另行提交，不修改历史失败。

- stage-14-release-readiness按DR-015：独立58核验通过，源码5247b360与档案6e525ea字节一致，当前本地示例范围ready；正式fa6资源与独立准备6fe来源分开，旧摘要/失败保持；未部署或创建GitHub Release，Windows实际系统及公网生产不在批准范围。
