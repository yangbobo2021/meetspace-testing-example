## Specs (Source of Truth)

- 规约存放于 `specs/`；从 `specs/map.md` 开始定位上下文，编写前阅读 `specs/meta.md`。
- 业务条目当前是从 `stage-01-implemented` 逆向整理的候选需求，尚未获得逐项业务确认，也没有新增验收通过结论。
- 按共同意图拆分规约包，每条需求采用 GEARS 句式和稳定的 `<pack>-<N>` ID；依赖用行内条目引用表达。
- 新增或修改规约时同步索引及相关 DR，保留已公开 ID，不生成并行的业务需求正文。
- 本次需求整理仅保留各包的验证章节占位；测试条目、方法、执行与证据由后续单独授权的测试阶段补充。
- `specs/meta.md` 与 `specs/decisions/000-spec-structure-format.md` 沿用自行车项目的原文件，未经人类授权不修改。
- 修改完成后运行 `npx @sublang/spex lint`；结构检查通过不代表业务需求已确认或应用已验收。
