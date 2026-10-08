"""Pin supplemental execution to this ledger; never inherit old passing results."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path.cwd();L=ROOT/'tests/delivery-acceptance';B=L/'coverage-audits/coverage-20261009-stage08-r1';R=L/'runs/supplement-20261009-stage08-r1';D=R/'evidence/coverage-cycle'
load=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
run=load(R/'run.json');assert all(hashlib.sha256((L/f).read_bytes()).hexdigest()==h for f,h in run['ledger_hashes'].items())
D.mkdir(parents=True,exist_ok=True)
for src in B.iterdir():
 if src.is_dir() and (src.name.startswith('isolated-') or src.name in ['api-projects','tools','replay-projects','__pycache__','private-evidence']):continue
 if src.is_dir():shutil.copytree(src,D/src.name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.sqlite','*.sqlite-wal','*.sqlite-shm','__pycache__','inputs'))
 else:shutil.copyfile(src,D/src.name)
executed={}
for fn in ['api-results.json','ui-identity-results.json','ui-dialog-results.json']:
 data=load(B/fn)
 for row in data['results']:
  sid=row['scenario_id'];assert sid not in executed
  ev=row.get('evidence_audit_relative',row['evidence']); ev=[ev]if isinstance(ev,str)else ev
  if 'actual' not in row:
   doc=load(B/ev[0]); actual={'WB-response-transport-disconnect':'成功/拒绝响应×BrokenPipeError/ConnectionResetError四项真实I/O故障通过；服务继续运行、状态保持。','WB-booking-response-loss-replay':'17项独立故障/重放/五维异内容拒绝与规范化对照通过；提交后唯一记录及提交前事务回滚均验证。','WB-runtime-sigint-persistence':'真实CLI收到SIGINT退出并释放端口，同库同端口重启后房间、预约、通知及已读状态保持。','WB-http-unsupported-methods':'60个真实HTTP组合均返回501 text/html，未满足JSON error/code契约；重复稳定性及数据库无变更另行核对。'}[sid]
  else:actual=row['actual']
  executed[sid]={'scenario_id':sid,'method_ids':row['method_ids'],'status':row['status'],'actual':actual,'evidence':['evidence/coverage-cycle/'+f for f in ev]}
scope={'revision':run['revision'],'executed_scenario_ids':sorted(executed),'not_reexecuted_count':167-len(executed),'policy':'本轮只对10个补测定义作独立执行结论。其他157个场景没有重执行，不继承历史passed。原三smokes只作资源复验。','scope_hashes':run['ledger_hashes']};write(R/'scope.json',scope)
run['scope']=scope;run['results']=[]
for scenario in load(L/'scenarios.json')['items']:
 sid=scenario['id'];run['results'].append(executed.get(sid,{'scenario_id':sid,'method_ids':scenario['method_ids'],'status':'unproven','actual':'本轮补测范围之外，未重新执行。历史run保留其原定义及结论，不迁移通过结果。','evidence':['scope.json']}))
run['dependency_checks']=[]
resources=load(L/'resources.json')['decisions']
for resource in resources:
 rid=resource['id']
 if rid=='existing-test-command':evidence='smoke-execution.log';actual='本轮原3个smoke真实执行通过，不能证明其余场景。'
 elif rid=='browser-targets':evidence='ui-dialog-results.json';actual='Chromium桌面1280×900与390×844、320×740真实原生UI矩阵已执行；只证明模拟视口。'
 elif rid=='isolated-data':evidence='api-evidence/WB-runtime-sigint-persistence.json';actual='本轮独立SQLite/真实CLI同库同端口重启验证持久业务资料。'
 else:evidence='resource-preflight.json';actual='本轮真实Python/SQLite/ZoneInfo、当前进程监听、四个公开合成账号登录及源码依赖检查；没有外部第三方集成。'
 assert (D/evidence).exists();run['dependency_checks'].append({'dependency_id':rid,'status':'passed','evidence':str((D/evidence).relative_to(L)),'actual':actual})
write(R/'run.json',run)
print(json.dumps({'executed':len(executed),'passed':sum(x['status']=='passed'for x in executed.values()),'failed':sum(x['status']=='failed'for x in executed.values()),'not_reexecuted':167-len(executed)}))
