"""系统依赖设施预检；只写布尔判定，不执行产品。"""
import argparse,json,os,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);base=pathlib.Path(__file__).resolve().parent
probe='import os,json,time; print(json.dumps({"random":os.urandom(32).hex(),"wall":time.time(),"monotonic":time.monotonic()}))'
values=[];rows=[]
for i,tape in enumerate(['E1','E2','E3','E1',None]):
 d=out/f'control-{i}';cmd=[sys.executable,'-S',str(base/'ptrace_os_adapter.py'),'--output',str(d)]+(['--tape',tape] if tape else [])+['--','/usr/bin/setarch','aarch64','-R','/usr/bin/env','PYTHONHASHSEED=0','PYTHONDONTWRITEBYTECODE=1','LD_PRELOAD=/usr/lib/aarch64-linux-gnu/faketime/libfaketime.so.1','FAKETIME=2030-04-10 01:00:00','FAKETIME_DONT_FAKE_MONOTONIC=0','TZ=UTC',sys.executable,'-S','-c',probe]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=30);row={'tape_alias':tape or 'real_os','exit_code':r.returncode,'stderr':r.stderr}
 if r.returncode==0:
  v=json.loads(r.stdout);values.append(v['random']);events=json.loads((d/'os-events.json').read_text());row.update(wall=v['wall'],monotonic=v['monotonic'],getrandom_events=[x for x in events['events'] if x['kind']=='getrandom'],uncovered=events['uncovered'])
 rows.append(row)
# 泄漏观察、自删除文件、跨write拆分，以及mmap旁路的明确拒绝标志。
fixture='import os,mmap; p="/tmp/ptrace-probe"; f=os.open(p,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600);os.write(f,b"MeetSpace!");os.write(f,b"2026");os.ftruncate(f,4096);m=mmap.mmap(f,4096);m[:14]=b"MeetSpace!2026";m.flush();m.close();os.close(f);os.unlink(p)'
d=out/'outlet-probe';r=subprocess.run([sys.executable,'-S',str(base/'ptrace_os_adapter.py'),'--output',str(d),'--',sys.executable,'-S','-c',fixture],capture_output=True,text=True,timeout=30);io=json.loads((d/'os-events.json').read_text())
report={'python':sys.version,'rows':rows,'assertions':{'same_E1_reproduces':len(values)==5 and values[0]==values[3],'E1_E2_E3_differ':len(values)==5 and len(set(values[:3]))==3,'wall_fixed':len(rows)==5 and len({x.get('wall') for x in rows})==1,'monotonic_fixed':len(rows)==5 and len({x.get('monotonic') for x in rows})==1,'all_observed_getrandom_controlled_in_E_runs':all(x['controlled_return'] for row in rows[:4] for x in row.get('getrandom_events',[])),'outlet_probe_actual_exit_zero':all(x.get('exit_code')==0 for x in io['exits'].values()),'split_write_plaintext_detected':io['counters'].get('leaks',0)>0,'self_deleted_write_observed':any('ptrace-probe' in e.get('path','') for e in io['events']),'mmap_dirty_plaintext_detected':any(e.get('kind')=='file_shared_mapping_scan' and e.get('leak') for e in io['events'])},'outlet_probe':{'events':io['events'],'uncovered':io['uncovered']},'formal_acceptance':None,'scope':'验证实际Linux syscall熵源、依赖返回控制和I/O观察能力；尚未跑产品初始化、业务登录、真实存储字段核对。mmap出口若在产品实际运行出现，需要追加扫描或保持blocked。'}
(out/'ptrace-resource-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'assertions':report['assertions'],'formal_acceptance':None},ensure_ascii=False))
