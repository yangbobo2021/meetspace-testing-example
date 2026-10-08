"""Verify independent review bindings and publish scoped results without self-review."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path.cwd();L=ROOT/'tests/delivery-acceptance';B=L/'coverage-audits/coverage-20261009-stage08-r1';R=L/'runs/supplement-20261009-stage08-r1';D=R/'evidence/coverage-cycle'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
review=load(B/'independent-review.json');run=load(R/'run.json');metrics=load(B/'metrics.json')
assert review['reviewer_kind']=='independent_ai' and review['status']=='completed'
assert review['formal_run_sha256']==sha(R/'run.json')
assert review['ledger_hashes']==run['ledger_hashes']
assert all(sha(L/f)==h for f,h in run['ledger_hashes'].items())
assert all(sha(ROOT/f)==h for f,h in review['source_hashes'].items())
assert all(sha(B/f)==h and sha(D/f)==h for f,h in review['scope_hashes'].items())
assert review['scenario_updates_required'] is False and review['additional_test_recommendations']==[]
assert len(review['scenario_reviews'])==10 and len(review['matrix_evidence_reviews'])==178
assert len(review['remaining_path_assessments'])==5
for item in review['matrix_evidence_reviews']:
 assert sha(B/item['evidence'])==item['evidence_sha256'] and sha(D/item['evidence'])==item['evidence_sha256']
baseline=load(L/'design-updates/coverage-supplement-20261009/baseline-binding.json');old=L/'runs/acceptance-20261008T-full-0b386b4-r1'
assert all(sha(old/f)==h for f,h in baseline['original_acceptance_sha256'].items())
scene_reviews={x['scenario_id']:x for x in review['scenario_reviews']};formal=[]
for result in run['results']:
 sid=result['scenario_id']
 if sid in scene_reviews:
  item=scene_reviews[sid];assert item['status']==result['status']
  refs=['evidence/coverage-cycle/'+f for f in item['evidence']];assert all(f in result['evidence'] for f in refs)
  formal.append({'scenario_id':sid,'status':item['status'],'reason':item['reason'],'evidence':refs})
 else:
  assert result['status']=='unproven';formal.append({'scenario_id':sid,'status':'unproven','reason':'独立审阅限定本轮10条补测；此项未重新执行，不复制旧run通过结论。','evidence':['scope.json']})
shutil.copyfile(B/'independent-review.json',D/'independent-review.json')
formal_review={'revision':run['revision'],'reviewer_kind':'independent_ai','review_reference':'evidence/coverage-cycle/independent-review.json','independent_review_sha256':sha(B/'independent-review.json'),'scope':run['scope'],'coverage':{'status':'unproven','reason':'补测设计与剩余路径审查已收敛；本run仅证明10条补测，其他157条没有重执行。保留5个实测未命中防御出口，不将本轮结论升级为完整发布验收。','requirements_reviewed':[x['id']for x in load(L/'requirements.json')['items']],'white_box_basis':['当前71白盒目标的独立设计审阅及相同业务源码SHA','evidence/coverage-cycle/independent-review.json','evidence/coverage-cycle/cumulative/backend-coverage.json','evidence/coverage-cycle/cumulative/frontend-coverage.json'],'uncovered_branches':review['remaining_path_assessments']},'results':formal}
write(R/'review.json',formal_review)
summary=review['execution_summary'];gate={'stage':'supplemental_coverage_cycle','status':'converged_with_product_failures','revision':run['revision'],'independent_review_sha256':sha(B/'independent-review.json'),'iteration':1,'execution_summary':summary,'additional_test_recommendations':[],'scenario_updates_required':False,'added_scenarios_this_cycle':0,'refined_scenarios_this_cycle':0,'formal_scene_count':167,'formal_method_count':176,'coverage':metrics['cumulative'],'checks':{'current_source_hashes_match':True,'current_six_ledger_hashes_match':True,'formal_run_review_binding_matches':True,'178_matrix_evidence_hashes_match_in_audit_and_run':True,'original_acceptance_unchanged':True,'all_ten_scope_results_independently_reviewed':True,'defensive_paths_retained_in_denominator':True,'no_new_material_scene_gap_in_agreed_scope':True},'release_approved':False,'full_acceptance':'not_established_in_this_partial_run'}
write(B/'cycle-gate.json',gate);write(D/'cycle-gate.json',gate)
b=metrics['cumulative']['backend'];f=metrics['cumulative']['frontend']
report=f'''# 补充场景执行与覆盖率循环

被测修订：`{run['revision']}`，六项业务源码/原测试SHA与阶段07一致。
测试Skill的Tester真实执行与独立Reviewer复核已完成；正式台账仍167场景、176方法。

| 源码 | 补测前可执行行 | 当前累计可执行行 | 补测前分支 | 当前累计分支 |
| --- | ---: | ---: | ---: | ---: |
| app/server.py | 380/384 · 98.96% | 384/384 · 100% | 124/124 · 100% | 124/124 · 100% |
| web/app.js | 180/181 · 99.44% | 180/181 · 99.44% | 165/177 · 93.22% | 172/177 · 97.17% |

前端函数86/86为100%，语句318/320为99.37%；未命中行仍为96。
累计为相同源码下阶段07所有27个既有业务入口与本轮真实计数并集，不是新run167场景全量通过。
仅本轮后端行345/384为89.84%、分支92/124为74.19%；仅本轮前端行150/181为82.87%、分支135/177为76.27%。
全部范围与计数保存于[metrics.json](metrics.json)，原始数据分别在backend/frontend-coverage及cumulative目录。

## 执行结果

新增8与细化2的完整10场景独立审阅为8通过、2失败；178分项116通过、62失败、0未证明，另3个原smoke通过。
失败一为未支持HTTP方法的60组合返回501 HTML，违反JSON error/code契约，数据保持不变。
失败二为自身降权已提交后session查询503/网络故障的2个数据重试项没有重新读身份，仍显示管理员菜单并请求403成员接口；整页刷新能恢复。
通过的恢复对照不抵消失败，本轮不改产品源码或测试预期。
其他157条场景未在本轮重执行；旧运行与stage06、stage07、stage08档案及其标签保持。

## 循环停止依据

本轮顺序为执行10场景→采集仅本轮及累计计数→独立复核未命中源码及重要语义组合。
后端旧4个未命中行和前端旧7个未命中出口、退出关闭弹窗回调已实际命中。
剩余5个前端出口：56登录反馈DOM缺失、81无身份renderShell、95–96非法page、99heading默认参数、107Intl星期fallback。
独立复核调用者、正常用户状态、页面枚举和当前Chromium格式后，无新的必要正式补测建议，新增0、再细化0，设计循环在当前源码/约定范围内收敛。
五处仍留在分母；直接调用辅助函数或修改DOM/Intl不会被计作普通真实业务验收，未来出现正常可达时序或新增支持环境时须重新评估。
产品失败属于已被场景捕获的问题，不需要无限追加同义场景；修复后应在新源码修订执行新验收。

## 审计入口

- [独立审阅](independent-review.json)：10场景理由、178项证据哈希、剩余路径、无新增建议及明确发布边界。
- [循环结构检查](cycle-gate.json)：源码、六项台账、新run及证据哈希、旧run完整性。
- [执行上下文](execution-context.json)：修订、工具版本、同源计数合并口径、隔离和隐私边界。
- [脱敏记录](evidence-redaction.json)：83份dialog证据去除合成password_hash，测试动作与业务等值断言不变。

收敛不等于100%物理覆盖或发布通过；完整验收门禁为blocked，发布验收尚未完成。
'''
(B/'cycle-report.md').write_text(report);shutil.copyfile(B/'cycle-report.md',D/'cycle-report.md')
scenario_gate=load(L/'scenario-gate.json');scenario_gate.update({'stage':'supplemental_coverage_cycle','status':'design_ready_supplemental_execution_complete','reason':'10条补测执行8通过2失败、独立剩余路径审查无新设计建议；167条全量发布验收未建立。','execution_status':'supplemental_subset_executed_and_reviewed','current_run':'supplement-20261009-stage08-r1','app_acceptance':'incomplete','cycle_gate_ref':'coverage-audits/coverage-20261009-stage08-r1/cycle-gate.json'})
write(L/'scenario-gate.json',scenario_gate)
print(json.dumps({'status':gate['status'],'passed':8,'failed':2,'unproven_not_rerun':157,'additional_scenarios':0}))
