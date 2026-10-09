import pathlib,subprocess,json
base=pathlib.Path(__file__).resolve().parent
image='sha256:6e73bceac9263be174946cc91d68a55cc2996fcc57cba43f33df17af20bad02c'
rows=[]
def run(name,command):
 out=base/name;out.mkdir()
 cmd=['docker','run','--rm','--log-driver=none','--network','none','--read-only','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','seccomp=unconfined','--tmpfs','/tmp:exec','--mount',f'type=bind,source={base},target=/probe,readonly','--mount',f'type=bind,source={out},target=/output','--entrypoint','sh',image,'-c',command]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=300);x=json.loads((out/'os-events.json').read_text())
 result={'name':name,'container_exit':r.returncode,'stderr':r.stderr,'target_exits_zero':all(v=={'exit_code':0,'signal':None} for v in x['exits'].values()),'uncovered':x['uncovered'],'leaks':x['counters'].get('leaks',0),'deferred':x['counters'].get('deferred_mapping_exit_scans',0),'resolved':x['counters'].get('deferred_mapping_exit_scans_resolved',0),'mapping_failures':[e for e in x['events'] if e['kind']=='mapping_read_failure'],'deferred_events':[e for e in x['events'] if 'mapping_exit_scan_' in e['kind']],'mapping_generations':sorted({e['generation'] for e in x['events'] if e['kind']=='file_shared_mapping'}),'leak_scan_generations':sorted({e['generation'] for e in x['events'] if e['kind']=='file_shared_mapping_scan' and e.get('leak')})};rows.append(result);print(json.dumps(result),flush=True);return result
for name in ['no-correspondence','unscanned','partial','failed']:
 arg=name.replace('-','_');r=run('guard-'+name,'gcc -O0 /probe/munmap_guard_probe.c -o /tmp/probe && python -S /probe/frozen-harness/ptrace_os_adapter.py --output /output -- /tmp/probe '+arg)
 if not r['target_exits_zero'] or 'mapping_unreadable_before_flush_or_exit' not in r['uncovered'] or r['resolved']:raise RuntimeError('guard did not preserve gap: '+name)
resolved=False
for i in range(12):
 r=run('positive-race-'+str(i),'gcc -O0 -pthread /probe/concurrent_mapping_probe.c -o /tmp/probe && python -S /probe/frozen-harness/ptrace_os_adapter.py --output /output -- /tmp/probe')
 if not r['target_exits_zero'] or r['uncovered'] or len(r['mapping_generations'])!=300 or r['mapping_generations']!=r['leak_scan_generations'] or r['deferred']!=r['resolved']:raise RuntimeError('positive race incomplete')
 if r['resolved']>0:resolved=True;break
report={'formal_verdict':None,'rows':rows,'all_negative_guards_preserve_gap':True,'positive_actual_deferred_and_confirmed':resolved,'scope':'真实系统调用/内存权限负控；不替换读取，不删任何缺口；旧产品缺口原因仍未证明'}
(base/'munmap-guard-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if not resolved:raise RuntimeError('positive deferred pathway not observed')
