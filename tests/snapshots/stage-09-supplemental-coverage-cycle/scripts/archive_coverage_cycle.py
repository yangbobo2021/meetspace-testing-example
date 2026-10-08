"""Publish an immutable test snapshot, excluding fixtures and auth material."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path.cwd();L=ROOT/'tests/delivery-acceptance';R=L/'runs/supplement-20261009-stage08-r1';B=L/'coverage-audits/coverage-20261009-stage08-r1';S=ROOT/'tests/snapshots/stage-09-supplemental-coverage-cycle'
load=lambda p:json.loads(p.read_text())
review=load(B/'independent-review.json');assert review.get('scenario_updates_required') is False;assert not review.get('additional_test_recommendations')
assert (R/'review.json').exists() and (R/'gate-report.json').exists() and (B/'cycle-gate.json').exists()
assert load(R/'gate-report.json')['status']!='passed'
assert subprocess.check_output(['git','ls-files',str(S.relative_to(ROOT))],cwd=ROOT,text=True).strip()==''
if S.exists():shutil.rmtree(S)
S.mkdir(parents=True)
for filename in ['project.json','requirements.json','resources.json','scenarios.json','methods.json','coverage_review.json','white_box_review.json','white-box-map.json','white-box-context.json','white-box-design-gate.json','black-box-gate.json','scenario-gate.json']:
 shutil.copyfile(L/filename,S/filename)
shutil.copytree(L/'design-updates/coverage-supplement-20261009',S/'design-updates/coverage-supplement-20261009',ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(R,S/'runs'/R.name,ignore=shutil.ignore_patterns('private-evidence','*.sqlite','*.sqlite-wal','*.sqlite-shm','__pycache__','.gitignore'))
for subdir,filenames in {'harnesses':['coverage_cycle_api.py','coverage_cycle_ui_identity.py','coverage_cycle_ui_dialogs.py'],'scripts':['build_coverage_cycle_reports.py','compile_coverage_cycle_run.py','archive_coverage_cycle.py','finalize_coverage_cycle.py']}.items():
 (S/subdir).mkdir()
 for f in filenames:shutil.copyfile(L/subdir/f,S/subdir/f)
metrics=load(B/'metrics.json');counts={'requirements':96,'black_box_scenarios':96,'white_box_scenarios':71,'total_scenarios':167,'methods':176,'executed_scenarios':10,'passed':8,'failed':2,'not_reexecuted':157,'matrix_items':178,'matrix_passed':116,'matrix_failed':62,'additional_scenarios_this_cycle':0}
report=S/'runs'/R.name/'evidence/coverage-cycle'
(S/'README.md').write_text('''# 阶段09：补充场景执行与覆盖率循环

被测修订`43bea9de0b8e2f8d3bd7723a6b734f242f36c794`，业务源码与首轮验收相同。
实际执行阶段08新增8与细化2场景的178个独立矩阵项，独立审阅为8场景通过、2失败；分项116通过、62失败，另3个原冒烟复验通过。
10场景补测范围之外的157场景本轮没有重新验收，历史通过结果不迁入新run。

| 源码 | 补测前可执行行 | 当前累计可执行行 | 补测前分支 | 当前累计分支 |
| --- | ---: | ---: | ---: | ---: |
| app/server.py | 380/384 · 98.96% | 384/384 · 100% | 124/124 · 100% | 124/124 · 100% |
| web/app.js | 180/181 · 99.44% | 180/181 · 99.44% | 165/177 · 93.22% | 172/177 · 97.17% |

前端函数86/86为100%，语句318/320为99.37%。
当前所有测试累计计数联合阶段07实际执行的27个业务入口与本轮补测，仅在源码SHA完全相同条件下合并命中；不是本轮全部167场景通过。
`runs/supplement-20261009-stage08-r1/evidence/coverage-cycle/metrics.json`分别保存补测前、仅本轮及累计计数。
后端4个旧未命中行260/492/493/495全部命中，前端7个旧未命中分支出口及退出关闭弹窗回调实际命中。

## 执行与审阅

- [正式运行](runs/supplement-20261009-stage08-r1/run.json)：固定修订、六项台账哈希、当前资源验证及完整167项状态。
- [正式证据审阅](runs/supplement-20261009-stage08-r1/review.json)：10条独立审阅，其余157明确未重新证明。
- [覆盖率循环报告](runs/supplement-20261009-stage08-r1/evidence/coverage-cycle/cycle-report.md)：执行、覆盖、剩余路径与设计收敛结论。
- [独立审查](runs/supplement-20261009-stage08-r1/evidence/coverage-cycle/independent-review.json)：逐场景及剩余源码判断、真实矩阵、证据哈希。
- [计数概览](runs/supplement-20261009-stage08-r1/evidence/coverage-cycle/index.html)：累计后端原生HTML和前端逐行分支展示，另保存仅本轮计数。
- [循环检查](runs/supplement-20261009-stage08-r1/evidence/coverage-cycle/cycle-gate.json)：证据完整性、独立结论、源码与台账完整性。
- [完整验收门禁](runs/supplement-20261009-stage08-r1/gate-report.json)：机器门禁为blocked，发布验收尚未完成。

失败一：DELETE/OPTIONS/PUT×四身份×五API路径60项均返回501 HTML，不满足原JSON error/code契约；业务状态未改变。
失败二：自身降权已提交后身份查询503或网络失败，数据“重新加载”没有重新获取session，保留管理员界面并再次请求已无权限的成员接口；整页刷新正常恢复。
其他通过矩阵及恢复对照不能抵消这两个失败。

剩余5个前端出口为登录反馈DOM缺失、无身份renderShell、非法page默认内容、heading默认参数、Intl星期fallback。
独立审阅对调用者、合法UI状态及当前Chromium/时区输出复查后，没有发现约定业务模式下的新正式场景缺口；它们保留在覆盖率分母和清单。
本次执行→计数→独立复查达到限定固定点，追加场景0、再细化0，正式场景仍96黑盒+71白盒=167，方法176。
固定点表示没有新的必要设计建议，不表示物理覆盖100%、缺陷修复或发布验收通过。

## 复核与复用

场景JSON保持唯一正式设计来源；此档案没有生成第二份场景正文。
本轮并未修改产品代码、确认需求、原测试及旧运行，全部阶段标签保留。
证据中的users只保留id/team/email/name/role；独立审阅发现的合成密码摘要已按`evidence-redaction.json`记录脱敏，原始副本仅留本机不归档。
本档案排除数据库、会话值、浏览器资料、隔离源码副本、工具依赖及private-evidence；计数文件仅含源码路径和行/弧命中。

复用时先保留当前活跃资产，再恢复阶段08台账及此阶段新run、harnesses和scripts到用户选定tests/delivery-acceptance。
覆盖工具使用coverage.py7.16.2、istanbul-lib-instrument6.0.3、istanbul-lib-coverage3.2.2；Playwright使用已安装的隔离Chromium，版本在执行证据中。
采集启动需生成本机coverage.ini路径映射，并将MEETSPACE_COVERAGE_AUDIT、COVERAGE_PROCESS_START、COVERAGE_FILE、PYTHONPATH指向新的空测量目录，勿覆盖归档run或联合不同源码计数。
后端真实CLI测试使用实际系统日期的次日合法时段，其他矩阵固定2030-04-10；两个时钟模式在证据中区分。
完整文件SHA256见[manifest.json](manifest.json)；源码修复后应以新修订与新run复测，不改写当前失败证据。
''')
files={str(f.relative_to(S)):{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}for f in sorted(S.rglob('*'))if f.is_file()}
for name in files:assert not any(part in name for part in ['private-evidence','api-projects/','isolated-dialog-','isolated-ui-identity-','node_modules/']) and not name.endswith(('.sqlite','.sqlite-wal','.sqlite-shm'))
manifest={'stage':S.name,'tested_revision':load(R/'run.json')['revision'],'counts':counts,'cycle_status':load(B/'cycle-gate.json')['status'],'app_acceptance':'incomplete','coverage':metrics['cumulative'],'files':files}
(S/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'snapshot':str(S),'files':len(files),'bytes':sum(x['bytes']for x in files.values())}))
