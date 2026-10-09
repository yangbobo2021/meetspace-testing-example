from pathlib import Path
import json,collections,hashlib,subprocess
R=Path(__file__).resolve().parents[2];E=R/'evidence';rev='5247b360276f2900d20fdeab96bd75bb3ece73fa'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==rev
matrix=json.loads((E/'entropy/entropy-matrix-report.json').read_text());assert len(matrix['rows'])==31 and len(matrix['comparisons'])==6
assert all(all(v for k,v in x.items() if k!='prefix') for x in matrix['comparisons'])
paths=collections.Counter();traces=[];business=[];errors=[]
def true(v):return all(true(x) for x in v) if isinstance(v,list) else v is True
for p in sorted((E/'entropy').glob('*/business-results.json')):
 x=json.loads(p.read_text()); bad=[k for k,v in x['assertions'].items() if not true(v)]
 if bad:errors.append([str(p),bad])
 business.append({'evidence':str(p.relative_to(R)),'assertion_count':len(x['assertions']),'failed_assertions':bad,'revision':x['revision'],'source_sha256':x['source_sha256']})
for p in sorted((E/'entropy').glob('*/os-trace*/os-events.json')):
 x=json.loads(p.read_text());traces.append({'evidence':str(p.relative_to(R)),'uncovered':x['uncovered'],'leaks':x['counters'].get('leaks',0),'exits':x['exits']})
 if x['uncovered'] or x['counters'].get('leaks',0) or any(z.get('exit_code')!=0 for z in x['exits'].values()):errors.append(str(p))
 for event in x['events']:
  if 'path' in event:paths[event['path']]+=1
unknown=[p for p in paths if not (p.startswith('/dev/shm/') or '/data/meetspace.sqlite' in p or p.endswith(('/server.log','/server-restart.log')))]
assert len(business)==31 and len(traces)==62 and not errors and not unknown
inventory={'revision':rev,'status':'passed','business_runs':business,'lifecycle_traces':traces,'comparisons':matrix['comparisons'],'observed_paths':dict(paths),'unknown_paths':unknown,'source_basis':['app/server.py SCHEMA全表字段','app/server.py password_hash secrets.token_hex(16)+scrypt','app/server.py Store.connect SQLite事务唯一业务持久路径','app/server.py login secrets.token_urlsafe(32); sessions仅SHA256/user_id/expires','app/server.py send_json Cookie只由HTTP返回；错误日志只含异常类名'], 'field_interpretation':{'users.password_hash':'salt_hex:scrypt_digest_hex；每账号独立重算/错密码对照，盐变化由真实OS熵受控重放支持','sessions':'token_hash摘要、user_id关联、expires8小时；逐实际token在内存计算SHA256核对，不新增原文或可逆字段','other_tables':'teams/users身份、rooms设备JSON、bookings业务及幂等摘要、notifications消息。实际对象/字段均与固定SCHEMA一致；无额外blob/未知对象','db_auxiliary':'SQLite journal/WAL为相同事务页，SHM为WAL索引；根据固定源码实际SQL及全I/O范围解释，不以字符串未命中单独断定安全'},'outlet_interpretation':{'sqlite':'实际数据库及事务附属文件写入和共享mmap扫描，无泄漏','logs':'应用server.log/restart.log实际受扫描','shared_state':'libfaketime /dev/shm共享时钟/信号量全部在观察路径中','connections':'同固定源新strace证据 network-metadata/network-probe.json，2次AF_UNIX nscd ENOENT；HTTP已accept socket为协议Cookie输出，不是服务端持久化','test_backup':'private-baseline.sqlite为测试器正常初始化未登录备份，非应用额外出口'}, 'limits':'仅对固定源码和已解释实际出口成立。31分支不证明一般密码学随机强度；任意未知编码/mmap路径不可从样本扫描推出安全。每次因果比较之后重启恢复真实OS源，避免人为固定熵造成既有token碰撞。'}
(E/'entropy-current-validation.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
