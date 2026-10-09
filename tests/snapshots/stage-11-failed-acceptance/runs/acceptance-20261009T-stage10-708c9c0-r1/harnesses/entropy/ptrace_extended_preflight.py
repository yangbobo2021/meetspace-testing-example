"""设施反例验证：fork继承共享mmap、编码/可逆载荷、随机设备、重命名删除事件。"""
import argparse,json,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);base=pathlib.Path(__file__).resolve().parent
program='''import os,mmap,base64
p="/tmp/probe-before";f=os.open(p,os.O_RDWR|os.O_CREAT|os.O_TRUNC,0o600);os.ftruncate(f,4096);m=mmap.mmap(f,4096)
child=os.fork()
if child==0:
 m[:14]=b"MeetSpace!2026";m.flush();m[:14]=b"0"*14;m.flush();os._exit(0)
os.waitpid(child,0);m.close();os.close(f);os.rename(p,"/tmp/probe-after");os.unlink("/tmp/probe-after")
for n,value in [("hex",b"MeetSpace!2026".hex().encode()),("base64",base64.b64encode(b"MeetSpace!2026")),("reversible",bytes(x^0x55 for x in b"MeetSpace!2026"))]:
 f=os.open("/tmp/"+n,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.write(f,value);os.close(f);os.unlink("/tmp/"+n)
f=os.open("/dev/urandom",os.O_RDONLY);v=os.read(f,32);os.close(f);print(len(v))
'''
r=subprocess.run([sys.executable,'-S',str(base/'ptrace_os_adapter.py'),'--output',str(out/'trace'),'--tape','E1','--',sys.executable,'-S','-c',program],capture_output=True,text=True,timeout=30);x=json.loads((out/'trace/os-events.json').read_text());events=x['events']
report={'exit_code':r.returncode,'stderr':r.stderr,'assertions':{'all_target_processes_exit_zero':all(v['exit_code']==0 for v in x['exits'].values()),'fork_inherited_mmap_secret_before_clear_detected':any(e.get('kind')=='file_shared_mapping_scan' and e.get('leak') for e in events),'hex_plaintext_detected':any(e.get('path')=='/tmp/hex' and e.get('leak') for e in events),'base64_plaintext_detected':any(e.get('path')=='/tmp/base64' and e.get('leak') for e in events),'known_reversible_sample_detected':any(e.get('path')=='/tmp/reversible' and e.get('leak') for e in events),'random_device_read_controlled':any(e.get('kind')=='random_device_read' and e.get('controlled_return') for e in events),'rename_and_unlink_observed':sum(e.get('kind')=='unlink_or_rename' for e in events)>=4,'uncovered_empty':not x['uncovered']},'events':events,'uncovered':x['uncovered'],'formal_verdict':None,'interpretation':'已知可逆XOR样本验证写出口被观察，并非任意加密内容可由字符串扫描判明；产品所有存储字段必须逐项解释，未知密文仍缺证。'}
(out/'extended-preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'assertions':report['assertions'],'formal_verdict':None},ensure_ascii=False))
