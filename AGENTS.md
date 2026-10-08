## Specs (Source of Truth)

- 规约存放于 `specs/`；从 `specs/map.md` 开始定位上下文，编写前阅读 `specs/meta.md`。
- 用户已确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为黑盒场景设计基线，见 DR-002；identity-session-9 的精确六十秒端点按 DR-004 补充，确认不代表应用验收通过。
- 按共同意图拆分规约包，每条需求采用 GEARS 句式和稳定的 `<pack>-<N>` ID；依赖用行内条目引用表达。
- 新增或修改规约时同步索引及相关 DR，保留已公开 ID，不生成并行的业务需求正文。
- 用户已授权使用 app-delivery-acceptance Skill 完成应用验收，测试资产固定在 `tests/delivery-acceptance/`；首轮完整流程未通过，正式审阅 139 通过、9 失败、11 未证明，见 DR-007；测试流程不修改应用或原测试，开发修复后针对新修订建立新运行。
- 代码覆盖率审计见 DR-008 与阶段07档案；补测建议未改写正式台账、未独立审阅或证明通过，后端分支100%不代表异常类型及状态组合完整。
- `specs/meta.md` 与 `specs/decisions/000-spec-structure-format.md` 沿用自行车项目的原文件，未经人类授权不修改。
- 修改完成后运行 `npx @sublang/spex lint`；结构检查通过不代表业务需求已确认或应用已验收。
