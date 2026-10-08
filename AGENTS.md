## Specs (Source of Truth)

- 规约存放于 `specs/`；从 `specs/map.md` 开始定位上下文，编写前阅读 `specs/meta.md`。
- 用户已确认 `stage-02-requirements`（`12d503a`）全部 96 条需求作为黑盒场景设计基线，见 DR-002；identity-session-9 的精确六十秒端点按 DR-004 补充，确认不代表应用验收通过。
- 按共同意图拆分规约包，每条需求采用 GEARS 句式和稳定的 `<pack>-<N>` ID；依赖用行内条目引用表达。
- 新增或修改规约时同步索引及相关 DR，保留已公开 ID，不生成并行的业务需求正文。
- 用户已授权使用 app-delivery-acceptance Skill 的角色分工生成并独立审阅黑盒及白盒场景，测试资产固定在 `tests/delivery-acceptance/`；本阶段不执行应用测试，当前白盒设计及仅设计流程范围见 DR-006。
- `specs/meta.md` 与 `specs/decisions/000-spec-structure-format.md` 沿用自行车项目的原文件，未经人类授权不修改。
- 修改完成后运行 `npx @sublang/spex lint`；结构检查通过不代表业务需求已确认或应用已验收。
