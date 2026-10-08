"""Archive the reviewed design supplement; do not copy App runs or fixtures."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];L=ROOT/'tests/delivery-acceptance';U=L/'design-updates/coverage-supplement-20261009'
DEST=ROOT/'tests/snapshots/stage-08-coverage-scenarios'
tracked=subprocess.check_output(['git','ls-files',str(DEST.relative_to(ROOT))],cwd=ROOT,text=True)
if tracked.strip():raise SystemExit('Published stage-08 archive is immutable; create a new stage')
gate=json.loads((L/'white-box-design-gate.json').read_text())
assert gate['status']=='white_box_design_ready' and not gate['issues'],'Reviewed design gate must pass before archive'
DEST.mkdir(parents=True,exist_ok=True)
for name in ['project.json','requirements.json','scenarios.json','methods.json','coverage_review.json','white_box_review.json',
             'white-box-map.json','white-box-context.json','white-box-design-gate.json','white-box-design-summary.json',
             'design-assessment.json','scenario-gate.json','black-box-gate.json']:
    shutil.copy2(L/name,DEST/name)
shutil.copytree(U,DEST/'design-updates/coverage-supplement-20261009',dirs_exist_ok=True)
inventory=DEST/'review-history/white-box-independent-inventory.json';inventory.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(L/'review-history/white-box-independent-inventory.json',inventory)
scripts=DEST/'scripts';scripts.mkdir(exist_ok=True)
for name in ['update_coverage_scenarios.py','refine_coverage_supplement_round01.py','check_coverage_supplement_design.py','finalize_coverage_supplement_design.py','archive_coverage_scenarios.py']:
    shutil.copy2(L/'scripts'/name,scripts/name)
(DEST/'README.md').write_text('''# 阶段08：根据覆盖率更新正式验收场景

用户于2026-10-09同意根据阶段07补测建议更新正式设计。
本阶段采用app-delivery-acceptance Skill的Analyst与独立Reviewer设计步骤，不启动完整应用验收流程。
固定实现修订为`9abe0809a7996f27bbcb974e3bd3ffef963303b6`，六项源码与首轮验收及覆盖率审计相同。

| 设计资产 | 更新前 | 本轮变化 | 更新后 |
| --- | ---: | --- | ---: |
| 黑盒场景 | 96 | 保持 | 96 |
| 白盒场景 | 63 | 新增8，细化原有2 | 71 |
| 场景合计 | 159 | 新增8 | **167** |
| 方法 | 168 | 新增8，细化原有2 | **176** |

新增8条分别涉及连接断开、提交后响应丢失重试、SIGINT持久重启、通知真实401、角色更新真实401、自身降权后身份查询失败恢复、日期清空、未支持HTTP方法。
保留原ID细化的2条是`WB-ui-dialog-close-no-write`和`WB-ui-logout-races`，原预期与原矩阵保留。
五处防御逻辑保存静态可达性、限定验证建议与未执行状态，不新增业务义务、不从覆盖率分母排除。

## 台账与审阅入口

- [scenarios.json](scenarios.json)、[methods.json](methods.json)：正式定义及执行方法；没有额外并行的可读场景正文。
- [设计增量](design-updates/coverage-supplement-20261009/change-summary.json)：8组审计建议到新增/细化场景的对应关系。
- [防御逻辑分析](design-updates/coverage-supplement-20261009/defensive-reachability.json)：五处未命中出口的可达性、限定验证及覆盖口径。
- [独立审阅](white_box_review.json)：完整71条白盒、71个目标、8组建议、5处防御处理的反事实审阅和当前哈希。
- [设计门禁](white-box-design-gate.json)：补充结构检查，状态`white_box_design_ready`；它不是应用验收通过门禁。
- [设计基线](design-updates/coverage-supplement-20261009/baseline-binding.json)与[修订记录](design-updates/coverage-supplement-20261009/repair-round-01.json)：旧台账、源码/旧运行哈希及独立审阅提出的修订。
- [旧覆盖率审计](../stage-07-coverage-audit/README.md)、[旧首轮验收](../stage-06-acceptance-run/README.md)：保持原阶段事实。

独立首审指出退出真实UI准备时序、真实撤销会话的Cookie隔离、源码行号，以及幂等比较五维矩阵的表述缺口。
修订后重新读取当前定义与哈希复审，设计通过才恢复白盒完成标记。
96条确认需求、96条黑盒及其方法不变，原黑盒scoped独立审阅与结构门禁仍有效。
原63条白盒保留；历史运行只对应旧159场景定义，不能为新定义提供通过证明。

## 阶段边界与复用

本轮未执行应用、原测试或新增补测，也未修复产品缺陷。
设计中的矩阵是未来执行计划，不是已获得证据；新增覆盖率提升尚未测量。
首轮验收139通过、9失败、11未证明及不建议发布的正式结论保持。
后续执行须验证新增故障适配器、真实Cookie撤销因果、SIGINT及端口归属等资源，再在新run保存证据和独立审阅。

要查看此阶段独立定义，可将本目录恢复到用户选择的tests/delivery-acceptance后使用Skill只读台账viewer。
切换阶段时先保留现有活跃台账，避免覆盖后续设计或运行。
脚本按tests/delivery-acceptance/scripts嵌套运行路径设计，不直接在快照内运行；本轮补充checker允许保留历史run并验证其哈希不变。
本档案仅含设计与审阅资产、旧台账基线及结构检查脚本；不包含数据库、会话值、浏览器资料或测试工具安装目录。
已有阶段标签与档案不改写，完整文件SHA256见[manifest.json](manifest.json)。
''')
files={str(p.relative_to(DEST)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
       for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='manifest.json'}
manifest={'stage':'stage-08-coverage-scenarios','implementation_revision':gate['implementation_revision'],
          'counts':gate['counts'],'design_gate':gate['status'],'execution_status':'not_started_for_updated_design',
          'app_acceptance':'not_established','files':files,'file_count':len(files),'bytes':sum(v['bytes'] for v in files.values())}
(DEST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'archived_files':len(files),'bytes':manifest['bytes'],'counts':manifest['counts']}))
