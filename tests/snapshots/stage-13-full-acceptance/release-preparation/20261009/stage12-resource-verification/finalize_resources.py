"""汇总实际资源观测/出处；不写正式场景passed或发布结论。"""
import collections,hashlib,json,pathlib,subprocess
base=pathlib.Path(__file__).resolve().parent;project=base.parents[4];attempt=base/'generation-guard-complete-attempt';matrix=attempt/'entropy';report=json.loads((matrix/'entropy-matrix-report.json').read_text());revision=report['revision']
if len(report['rows'])!=31:raise RuntimeError('31分支未完成')
network_probe=json.loads((attempt/'network/network-probe.json').read_text())
binding={};paths=collections.Counter();unknown=[];modes=[];issues=[];source_hashes={};observer_counts=collections.Counter()
expected_source={p:hashlib.sha256(subprocess.run(['git','show',revision+':'+p],cwd=project,capture_output=True,check=True).stdout).hexdigest() for p in ['app/server.py','app/__init__.py','web/index.html','web/style.css','web/app.js']}
lifecycle_count=0
for row in report['rows']:
 if row.get('status')=='blocked':issues.append(row['name']+':blocked');continue
 r=row['report']
 if r.get('source_sha256')!=expected_source:issues.append(row['name']+':source_pin_mismatch')
 if r.get('revision')!=revision:issues.append(row['name']+':revision_mismatch')
 disk=json.loads((matrix/row['name']/'business-results.json').read_text())
 if disk!=r:issues.append(row['name']+':disk_outer_report_mismatch')
 for exit_name in ['first_tracer_exit_code','tracer_exit_code']:
  if r.get(exit_name)!=0:issues.append(row['name']+':'+exit_name)
 modes.append({'name':row['name'],'prefix':row['prefix'],'entropy_alias':row['tape_alias'],'app_pid':r['app_pid'],'baseline_before_any_login_sessions_zero':r['assertions'].get('baseline_before_any_login_sessions_zero'),'comparison_scope':r.get('comparison_scope'),'restart_entropy_source':r.get('restart_entropy_source')});source_hashes=r['source_sha256']
 for key,actual in r['assertions'].items():
  if actual is False or (isinstance(actual,list) and not all(actual)):issues.append(row['name']+':'+key)
 for name,value in r['harness_sha256'].items():
  if value!=report['harness_sha256'][name]:issues.append(row['name']+':harness_sha_changed:'+name)
 for phase in ['os_trace','os_trace_restart']:
  trace=r.get(phase,{})
  lifecycle_count+=1
  if not trace.get('exits') or not trace.get('counters'):issues.append(row['name']+':'+phase+':missing_trace')
  for pid,actual_exit in trace.get('exits',{}).items():
   if actual_exit!={'exit_code':0,'signal':None}:issues.append(row['name']+':'+phase+':process_exit:'+pid)
  if trace.get('uncovered'):issues.append(row['name']+':'+phase+':uncovered')
  if any(e.get('leak') for e in trace.get('events',[])):issues.append(row['name']+':'+phase+':leak')
  connect_count=trace.get('counters',{}).get('syscall_203',0)
  if connect_count and (not network_probe['all_connects_failed_nscd'] or connect_count!=len(network_probe['actual_connect_metadata'])):issues.append(row['name']+':unexplained_connect_syscalls')
  observer_counts.update(trace.get('counters',{}))
  for e in trace.get('events',[]):
   if 'path' in e:paths[e['path']]+=1
for path,count in sorted(paths.items()):
 if '/data/meetspace.sqlite' in path:category='application_sqlite_database_and_journal_wal_shm';purpose='固定源码Store.connect/SQLite事务状态；业务字段、索引及会话摘要字段由独立源码/外部格式审阅核对。'
 elif path.endswith('server.log') or path.endswith('server-restart.log'):category='application_stdout_stderr_log';purpose='应用自身stdout/stderr和HTTP访问日志，全部纳入扫描；不是测试工具排除项。'
 elif path.startswith('/dev/shm/faketime_shm_') or path.startswith('/dev/shm/sem.'):
  category='test_clock_adapter_shared_state';purpose='libfaketime时钟/信号量状态；测试依赖基础设施，仍有共享映射与写扫描记录。'
 else:category='unknown_requires_review';purpose='无法自动解释，不能批准完整存储观察';unknown.append(path)
 binding[path]={'category':category,'purpose':purpose,'events':count}
for p,sha in source_hashes.items():
 old=subprocess.run(['git','show',revision+':'+p],cwd=project,capture_output=True,check=True).stdout
 if hashlib.sha256(old).hexdigest()!=sha:issues.append('source_pin_mismatch:'+p)
if lifecycle_count!=62:issues.append('lifecycle_count:'+str(lifecycle_count))
if len(report['comparisons'])!=6:issues.append('causal_comparison_prefixes_incomplete')
for comparison in report['comparisons']:
 if not all(v for k,v in comparison.items() if k!='prefix'):issues.append('causal_comparison:'+comparison['prefix'])
cli=[]
for name in ['cli311','cli312']:
 x=json.loads((attempt/name/'cli-matrix-results.json').read_text());cli.append({'path':'generation-guard-complete-attempt/'+name+'/cli-matrix-results.json','python':x['resource']['python'],'rows':len(x['rows']),'clock_control':x['resource']['clock_control'],'all_recorded_assertions_true':all(all(row['assertions'].values()) and not row.get('error') for row in x['rows'])})
 if len(x['rows'])!=11:issues.append(name+':row_count')
 if x['resource'].get('revision')!=revision or x['resource'].get('source_sha256')!=expected_source:issues.append(name+':source_pin_mismatch')
 if any(row.get('exit_code')!=0 for row in x['rows']):issues.append(name+':child_exit')
 if not cli[-1]['all_recorded_assertions_true']:issues.append(name+':false_assertion')
if network_probe.get('revision')!=revision or network_probe.get('source_sha256')!=expected_source:issues.append('network_probe:source_pin_mismatch')
if not network_probe.get('healthy') or network_probe.get('exit_code')!=0:issues.append('network_probe:incomplete')
for name in ['preflight-basic/ptrace-resource-report.json','preflight-extended/extended-preflight.json']:
 pre=json.loads((attempt/name).read_text())
 if not all(pre['assertions'].values()):issues.append(name+':false_assertion')
control=json.loads((attempt/'concurrent-mapping-probe/probe-results.json').read_text())
if not control.get('all_target_exits_zero') or control.get('target_exit_count')!=601 or control.get('detected_leaks',0)<300 or control.get('uncovered'):issues.append('concurrent_mapping_negative_control_incomplete')
positive_trace=json.loads((attempt/'concurrent-mapping-probe/os-events.json').read_text())
map_generations={e['generation'] for e in positive_trace['events'] if e['kind']=='file_shared_mapping'}
leak_generations={e['generation'] for e in positive_trace['events'] if e['kind']=='file_shared_mapping_scan' and e.get('leak')}
if len(map_generations)!=300 or map_generations!=leak_generations:issues.append('negative_control_generation_coverage')
guards=json.loads((attempt/'munmap-guard-results.json').read_text())
if not guards['all_negative_guards_preserve_gap'] or not guards['positive_actual_deferred_and_confirmed']:issues.append('munmap_guards_incomplete')
reuse=json.loads((attempt/'address-reuse-probe/probe-results.json').read_text())
if not reuse['all_targets_exit_zero'] or reuse['generations_created']!=1000 or reuse['old_unmap_new_mapping_retained']<=0 or 'mapping_unreadable_before_flush_or_exit' not in reuse['uncovered']:issues.append('address_reuse_guard_incomplete')
seccomp=json.loads((attempt/'seccomp-guard-results.json').read_text())
for guard in seccomp['rows']:
 expected='pending_full_unmap_failed_after_deferred_exit_scan' if guard['mode']=='failed' else 'pending_full_unmap_unresolved_after_deferred_exit_scan'
 if guard['deferred']<=0 or guard['resolved']!=0 or expected not in guard['uncovered']:issues.append('dependent_munmap_guard:'+guard['mode'])
mapping_metadata=json.loads((attempt/'mapping-metadata/mapping-metadata-analysis.json').read_text())
mapping_probe=json.loads((attempt/'mapping-metadata/mapping-metadata-probe.json').read_text())
if mapping_probe['source_sha256']!=expected_source or any(row['exit_code']!=0 for row in mapping_probe['rows']):issues.append('mapping_metadata:source_or_exit')
if not mapping_metadata['all_observed_mremap_inputs_anonymous_private'] or mapping_metadata['tracked_shared_file_mremap_observed'] or mapping_metadata['shared_readonly_to_write_observed'] or mapping_metadata['unknown_write_permission_mprotect']:issues.append('mapping_metadata:unexplained_persistent_mapping')
final={'revision':revision,'business_branches':len(report['rows']),'observed_lifecycles':lifecycle_count,'source_sha256':source_hashes,'frozen_harness_sha256':report['harness_sha256'],'formal_verdict':None,'accepted_resource_attempt':'generation-guard-complete-attempt' if not issues and not unknown else None,'resource_observation_complete':not issues and not unknown,'issues':issues,'unexplained_outlets':unknown,'entropy_comparisons':report['comparisons'],'branch_control_binding':modes,'cli_matrices':cli,'observed_outlets':binding,'aggregate_syscall_observation_counts':dict(observer_counts),'secret_transport':'Docker--log-driver=none stdout匿名管道仅宿主内存比较；公开报告只布尔/元数据；private-baseline.sqlite是私有测试快照，不得归档公开。','initial_snapshot':'baseline-real-os在真实Store完成正常初始化、任何登录之前backup，sessions=0；各后续prefix从此同一快照重建，禁止通过SQL删除会话伪造。','restart_scope':'完成初始fixed-tape目标后，同库重启恢复真实OS随机输入并真实认证；不宣称整个生命周期同E1重启输出相同。','network_metadata_probe_reference':'generation-guard-complete-attempt/network/network-probe.json','socket_scope':'当前固定源码使用HTTPServer被接受的HTTP连接输出协议；每个生命周期实际2次connect尝试均由同源独立网络元数据探针解释为/var/run/nscd/socket ENOENT；没有观测到成功应用外连，socket协议输出与持久化出口分开；独立Reviewer仍须核源码/Socket入口匹配，任何未解释外连不能排除。','database_scope':'database_field_inventory枚举全部表/列，登录每次从API identity及只读内存SQLite backup联查SHA256、user_id、expires；无未知blob不是完整性的单独依据，TEXT及索引用途需独立源码/外部格式审查。','runtime_pid_scope':'保留真实PID交叉表；无关PID变化不被伪装为逐bit同机器状态。是否影响实际盐/token生成因果范围由独立Reviewer结合固定源码/同E1复现审阅。','independent_review_references':['../resource-readiness-review.json（仅设施前史，新源须独立重新审阅）'],'preflight_references':['generation-guard-complete-attempt/preflight-basic/ptrace-resource-report.json','generation-guard-complete-attempt/preflight-extended/extended-preflight.json'],'concurrent_mapping_negative_control_reference':'generation-guard-complete-attempt/concurrent-mapping-probe/probe-results.json','observer_generation_guard_diff':'generation-guard-complete-attempt/observer-generation-guard.diff','observer_prior_narrow_fix_diff':'confirmed-unmap-complete-attempt/observer-confirmed-unmap.diff','generation_guard_control_references':['generation-guard-complete-attempt/munmap-guard-results.json','generation-guard-complete-attempt/address-reuse-probe/probe-results.json','generation-guard-complete-attempt/seccomp-guard-results.json'],'observer_scope':'固定产品实际映射、存储字段与路径独立审阅；不宣传任意并发普通内存写完整性。正控实证duplicate exit/full munmap竞态，不泛化原seed-1未知缺口原因已证明。','diagnostic_history_reference':'entropy/entropy-matrix-report.json（31项中3项缺证原样保留，不被迁移为通过）','startup_budget_reference':'generation-guard-complete-attempt/attempt-plan.json','prior_attempts':[{'reference':'entropy/entropy-matrix-report.json','state':'3启动或重启观察缺证，保留原始'},{'reference':'retry-increased-startup-budget/entropy/entropy-matrix-report.json','state':'seed-1重启映射不可读缺口原因未证，保留原uncovered；不迁移旧pass、不解释为无写/无泄漏'}],'additional_preserved_attempts':['metadata-only-complete-attempt：产品31/62完整但并发300负控捕获一个合法munmap重复exit扫描缺口','confirmed-unmap-complete-attempt：控制计数断言错误与同地址代际缺口候选，不作accepted'], 'release_approved':False,'history':'本目录为5247b360固定新源与全新数据实际重执行；未迁移旧业务passed或私有基线。此摘要仅验证资源适用性，正式Tester仍须fresh执行正式场景，不是正式完整验收或发布批准。'}
final.update({'mapping_metadata_reference': 'generation-guard-complete-attempt/mapping-metadata/mapping-metadata-analysis.json', 'mapping_metadata_scope': '独立同固定源初始化/真实业务/同DB重启两个生命周期sample，每个4次mremap均按实际地址关联MAP_PRIVATE|MAP_ANONYMOUS fd=-1；没有shared-file mremap或共享只读→可写mprotect。本sample不是原62 trace逐call属性补写。原62各4次/总248次由独立Reviewer核对。各sample6处用户态mmap origin未登记的mprotect仅PROT_READ，保留其地址/范围未知origin，不声明完整初始ELF归属。', 'observer_scope': '固定产品已登记shared writable file mmap及其实际出口/字段独立审阅；不声明未登记MAP_FIXED替换、只读→mprotect写、tracked mremap并发替换或任意并发普通内存store的通用完整观察能力。原seed-1原因仍未知，合成竞态只解释设施改进依据。'})
(base/'resource-execution-summary.json').write_text(json.dumps(final,ensure_ascii=False,indent=2));print(json.dumps({'resource_observation_complete':final['resource_observation_complete'],'issues':issues,'unexplained_outlets':unknown,'formal_verdict':None},ensure_ascii=False))
