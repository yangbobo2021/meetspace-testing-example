import ast,concurrent.futures,json,subprocess,time,shutil,os
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3];ASSETS=ROOT/'tests/delivery-acceptance';PYTHON='/Users/boboyang/.cloakbrowser-codex/venv/bin/python';OLD='0b386b4bd37b01eb996c5e74215ab1a4463a9487';REV=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();RUN='acceptance-20261008T-full-0b386b4-r1'
tree=ast.parse((BASE/'replay.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['prepare','run']],type_ignores=[]),str(BASE/'replay.py'),'exec'),globals())
config=BASE/'coverage.ini'
names=['full_api_matrix','execute_covered_review_probes']
for n in names:prepare(n)
probe_ledger=BASE/'replay-projects/execute_covered_review_probes/tests/delivery-acceptance'
probe_run=probe_ledger/'runs/independent-covered-probes-20261008'
probe_run.mkdir(parents=True,exist_ok=True)
run_doc=json.loads((ASSETS/'runs/independent-covered-probes-20261008/run.json').read_text())
run_doc['results']=[];run_doc['revision']=REV
(probe_run/'run.json').write_text(json.dumps(run_doc,ensure_ascii=False,indent=2)+'\n')
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,names))
(BASE/'extra-replay-context.json').write_text(json.dumps({'jobs':results,'scope':'同时重跑归档内早期API矩阵与独立子分支探针，仅收集真实执行计数，不合并任何跨轮通过判定。'},ensure_ascii=False,indent=2)+'\n')
