"""Publish a compact stage archive; omit product fixtures and installed tools."""
import hashlib
import json
import shutil
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
DEST=ROOT/'tests/snapshots/stage-07-coverage-audit'
DEST.mkdir(parents=True,exist_ok=True)
for p in BASE.iterdir():
    if p.is_file() and p.suffix in ('.json','.py','.js','.ini','.md','.html','.log'):
        shutil.copy2(p,DEST/p.name)
for name in ('html','logs','python-data','javascript-data'):
    shutil.copytree(BASE/name,DEST/name,dirs_exist_ok=True)
for name in ('package.json','package-lock.json'):
    target=DEST/'tools/node'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(BASE/'tools/node'/name,target)
shutil.copytree(BASE/'bootstrap',DEST/'bootstrap',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
shutil.copy2(BASE/'.coverage',DEST/'combined-python.coverage')

# Preserve the actual uninstrumented startup attempt observations, without DBs.
startup=BASE/'replay-projects/runtime_startup/tests/delivery-acceptance/runs/acceptance-20261008T-full-0b386b4-r1/evidence/runtime'
for p in startup.glob('startup*'):
    if p.is_file() and p.suffix in ('.json','.log'):
        target=DEST/'startup-observations'/p.name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)

report=DEST/'coverage-audit.md'
report.write_text(report.read_text().replace('../../../snapshots/stage-06-acceptance-run/README.md','../stage-06-acceptance-run/README.md'))
(DEST/'README.md').write_text('''# 阶段07：既有测试代码覆盖率审计

审计固定 `stage-06-acceptance-run` 修订 `5b7e2461476d4ee6bd6819d084cb1e4787c302c1`，业务代码与首轮验收时相同。
这是覆盖率测量与补测缺口分析；应用、原有测试、确认需求、正式场景/方法台账及原验收记录均保持不变。

| 业务源码 | 可执行行 | 分支出口 |
| --- | ---: | ---: |
| app/server.py | 380/384（98.96%） | 124/124（100%） |
| web/app.js | 180/181（99.44%） | 165/177（93.22%） |

可执行行加权560/565（99.12%）；原三个冒烟单独测量后端行75.52%、分支57.26%。
前端另有语句317/320（99.06%）、函数85/86（98.83%）。

实测27个既有业务测试入口；测试进程退出成功不代表产品断言通过。
coverage.py 7.16.2与Istanbul 6.0.3的计数、原始行/弧与浏览器计数文件、实际执行日志均保存。
覆盖率不能替代需求、状态组合与证据审阅，首轮139通过、9失败、11未证明的正式结论保持。

## 阅读入口

- [完整报告](coverage-audit.md)：范围、计数、8组补测建议、5处防御逻辑及测量限制。
- [可视化概览](index.html)、[后端原生报告](html/backend/index.html)、[前端逐行报告](html/frontend.html)：下载后用本地静态服务打开，GitHub不直接执行HTML。
- [补测矩阵](proposed-coverage-scenarios.json)：关联现有需求/场景/方法的前置条件、操作、预期及证据；尚未独立审阅或加入正式台账。
- [未覆盖逐位置映射](uncovered-inventory.json)、[计数](metrics.json)、[执行入口](execution-summary.json)、[完整性](integrity-check.json)。
- [额外HTTP方法诊断](supplemental-http-verbs.json)：45次真实请求均501 HTML，业务数据不变；新诊断不进入既有测试覆盖率分子，不构成独立验收结论。

## 复现与公开范围

复现步骤见完整报告；将档案恢复到指定tests/delivery-acceptance路径再安装隔离工具依赖。
需要阶段06归档的需求/场景/方法与harnesses；脚本中本机Playwright Python路径需按环境配置。
当前源码未改变，但将来源码修订后应建立新审计，不能将本档案覆盖率应用于新版本。
脚本相对路径按实际运行资产的四层嵌套布局设计，不应直接在stage快照目录执行。
原始coverage文件只含路径和行/分支计数；公开档案不包含SQLite业务库、会话值、重放项目副本、工具安装目录或浏览器资料。
旧阶段档案与标签保持不变，SHA256清单见[manifest.json](manifest.json)。
''')
files={str(p.relative_to(DEST)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
       for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='manifest.json'}
manifest={'stage':'stage-07-coverage-audit','tested_revision':'5b7e2461476d4ee6bd6819d084cb1e4787c302c1',
          'files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files.values()),
          'exclusions':['replay-projects','tools installed packages','business SQLite DBs','session values','browser profile'],
          'scope':'coverage audit; proposed gap scenarios not independently reviewed; prior acceptance unchanged'}
(DEST/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(files),'bytes':manifest['bytes']}))
