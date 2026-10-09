"""宿主控制器：私有材料只经Docker无日志stdout管道留内存，磁盘仅存布尔比较/元数据。"""
import argparse,hashlib,json,pathlib,shutil,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--output',required=True);p.add_argument('--revision',required=True);p.add_argument('--source-root',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
if not a.execute:raise SystemExit('只准备资源；执行需 --execute 和已提交revision')
root=pathlib.Path(a.project).resolve();source_root=pathlib.Path(a.source_root).resolve();base=pathlib.Path(__file__).resolve().parent;out=pathlib.Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
frozen=out/'frozen-harness';frozen.mkdir()
for name in ['run_entropy_matrix.py','entropy_business_branch.py','ptrace_os_adapter.py']:shutil.copyfile(base/name,frozen/name)
harness_hashes={name:hashlib.sha256((frozen/name).read_bytes()).hexdigest() for name in ['run_entropy_matrix.py','entropy_business_branch.py','ptrace_os_adapter.py']}
actual=subprocess.run(['git','rev-parse','HEAD'],cwd=root,text=True,capture_output=True,check=True).stdout.strip()
if actual!=a.revision:raise SystemExit('revision不同，拒绝执行')
for directory in ['app','web']:
 for file in (source_root/directory).rglob('*'):
  if not file.is_file():continue
  relative=file.relative_to(source_root).as_posix();committed=subprocess.run(['git','show',a.revision+':'+relative],cwd=root,capture_output=True,check=True).stdout
  if file.read_bytes()!=committed:raise SystemExit('git-pinned source不同，拒绝执行:'+relative)
rows=[]
def branch(prefix,tape,name,baseline=None,save=False):
 destination=out/name;destination.mkdir()
 cmd=['docker','run','--rm','--log-driver=none','--network','none','--read-only','--cap-drop','ALL','--cap-add','SYS_PTRACE','--security-opt','seccomp=unconfined','--tmpfs','/tmp']
 for source,target,readonly in [(source_root/'app','/source/app',True),(source_root/'web','/source/web',True),(frozen,'/harness',True),(destination,'/output',False)]:
  cmd+=['--mount',f'type=bind,source={source},target={target}'+(',readonly' if readonly else '')]
 if baseline:cmd+=['--mount',f'type=bind,source={baseline},target=/baseline.sqlite,readonly']
 cmd+=['--entrypoint','python','sha256:6e73bceac9263be174946cc91d68a55cc2996fcc57cba43f33df17af20bad02c','-S','/harness/entropy_business_branch.py','--source','/source','--output','/output','--prefix',prefix,'--revision',a.revision,'--execute']
 if tape:cmd+=['--tape',tape]
 if baseline:cmd+=['--baseline-db','/baseline.sqlite']
 if save:cmd+=['--save-baseline']
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
 if r.returncode:rows.append({'name':name,'exit_code':r.returncode,'stderr':r.stderr,'status':'blocked'});return None
 x=json.loads(r.stdout);rows.append({'name':name,'prefix':prefix,'tape_alias':tape or 'real_os','exit_code':0,'report':x['report']});return x
# 真OS初始化快照作为各会话前缀共用基线；应用正常初始化，不改SQL。
base_result=branch('seed',None,'baseline-real-os',save=True);baseline=out/'baseline-real-os/private-baseline.sqlite'
comparisons=[]
for prefix in ['seed','first','repeat','after-three','self-switch','cross-switch']:
 data=[]
 for i,tape in enumerate(['E1','E2','E3','E1',None]):data.append(branch(prefix,tape,prefix+f'-{i}',None if prefix=='seed' else baseline))
 if all(x is not None for x in data):
  if prefix=='seed':
   e=[x['private_salts'] for x in data];compare={'prefix':prefix,'same_E1_all_salts_reproduce':e[0]==e[3],'E1_E2_E3_each_account_changes':all(len({v[email] for v in e[:3]})==3 for email in e[0])}
  else:
   e=[x['private_target_token'] for x in data];compare={'prefix':prefix,'same_E1_token_reproduces':e[0]==e[3],'E1_E2_E3_target_token_changes':len(set(e[:3]))==3}
  comparisons.append(compare)
report={'revision':a.revision,'harness_sha256':harness_hashes,'comparisons':comparisons,'rows':rows,'formal_verdict':None,'interpretation':'实际OS熵、真实App动作、同快照同E1控制只支持指定反事实，非有限样本随机强度证明；全出口/字段范围仍须独立核对。'}
(out/'entropy-matrix-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'revision':a.revision,'branches':len(rows),'comparisons':comparisons,'blocked':[x['name'] for x in rows if x.get('status')=='blocked'],'formal_verdict':None},ensure_ascii=False))
