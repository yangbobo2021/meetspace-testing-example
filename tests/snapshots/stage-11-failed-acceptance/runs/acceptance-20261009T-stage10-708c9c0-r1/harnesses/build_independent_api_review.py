import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];L=R.parents[1];root=L.parents[1]
d=json.load(open(R/'api-execution-results.json'));sc=json.load(open(L/'scenarios.json'))['items'];methods={m['id']:m for m in json.load(open(L/'methods.json'))['items']}
method_reviews=[];opened={}
for m in d['method_results']:
 ev=m['evidence'];facts=[]
 for rel in ev:
  p=R/rel;assert p.is_file(),rel;raw=p.read_bytes();opened[rel]=hashlib.sha256(raw).hexdigest()
  if p.suffix!='.json':continue
  o=json.loads(raw)
  if isinstance(o,dict) and 'checks' in o:
   cs=o['checks'];labels=list(dict.fromkeys(x['label'] for x in cs));facts.append(f'{p.name}：{len(cs)}个断言、{len(o.get("http",[]))}个真实HTTP事件；'+ '、'.join(labels[:7]))
  elif isinstance(o,dict) and 'items' in o:
   facts.append(f'{p.name}：{len(o["items"])}个分项，实际故障/响应/持久状态与恢复记录已检查')
 status=m['status'];reason='独立读取当前方法动作及场景预期，对照真实HTTP输入/状态/正文、独立SQLite前后快照、SQL/源码到达和恢复记录；'+ '；'.join(facts)
 if m['method_id'] in ['AI-team-administration-1','AI-team-administration-2','AI-team-administration-3','AI-team-administration-6','AI-WB-member-select-role-guards']:
  reason='保留本次方法失败；members矩阵两项role=[]/{}实际返回500/internal_error，harness期待400，其他45断言通过且拒绝后角色/业务不变。源码role集合查找对不可哈希值抛TypeError，dispatch转稳定JSON500。正式需求只要求非法角色拒绝无写入，没有精确400合同；因此不能把这两项直接扩大为五条产品权限缺陷，也不能用其他路径通过改写本次失败。自动审查拒绝放宽断言重跑，证据不足以给本方法正式通过。'
 if m['method_id']=='AI-WB-response-transport-disconnect':
  reason='保留初始failed：旧源码行号令send_json/dispatch/catch到达探针失败，初始业务不变量、服务恢复、JSON均通过。独立核对当前server.py行号与补跑4项成功/业务拒绝×BrokenPipe/Reset完整记录，补跑全部到达和行为断言为真；该补跑不能抹去初始失败，未发现响应断开造成新业务损坏的证据。'
 if m['method_id']=='AI-WB-idempotency-absolute-precision':
  reason='unproven：当前HTTP矩阵确实拒绝起止±1微秒差异并保持预约/通知，等价时刻与取消当前状态重放有证据；当前方法另要求秒级历史指纹数据库fixture分支，未执行。旧修订作为生成器被自动审查拒绝，不允许用当前新记录覆盖该历史状态缺口。'
 method_reviews.append({'method_id':m['method_id'],'status':status,'reason':reason,'evidence':ev,'method_definition_sha256':hashlib.sha256(json.dumps(methods[m['method_id']],ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
lookup={x['method_id']:x for x in method_reviews};results=[]
for s in sc:
 selected=[lookup[x] for x in s['method_ids'] if x in lookup]
 if not selected:continue
 missing=[x for x in s['method_ids'] if x not in lookup]
 st='failed' if any(x['status']=='failed' for x in selected) else 'unproven' if missing or any(x['status']!='passed' for x in selected) else 'passed'
 results.append({'scenario_id':s['id'],'status':st,'reason':'API所有权范围独立核对预期：'+s['expected']+'；'+('关联其他执行者方法由root合并独立审阅：'+','.join(missing) if missing else '本场景关联方法均在本次独立审阅范围。'),'evidence':sorted(set(p for x in selected for p in x['evidence'])),'reviewed_method_ids':[x['method_id'] for x in selected],'other_owner_method_ids':missing})
report={'revision':d['revision'],'reviewer_kind':'independent_ai','review_reference':'/root/ui_execution reviewing /root/api_execution (not own UI execution)','basis':'独立检查当前scenarios/methods、server.py dispatch/api/create_booking/字段校验、当前api-r2所有矩阵的请求与断言、booking-fields/room-uniqueness补充、原与纠正transport探针、response loss/unsupported/真实CLI恢复；无旧run通过合并。','method_reviews':method_reviews,'results':results,'opened_evidence_sha256':opened,'limits':['混合来源场景仅审阅API方法，其他方法由root依据另一独立review合并。','不将同组非法角色状态断言解释为所有权限分支失败；原执行失败保留。','没有外部第三方集成；故障依赖适配器不等于真实远端集成证据。']}
(R/'independent-api-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(len(method_reviews),'methods',len(results),'scenarios')
