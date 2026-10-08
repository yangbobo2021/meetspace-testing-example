"""Separate this supplemental run from cumulative same-source coverage counters."""
import hashlib, html, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path.cwd();LEDGER=ROOT/'tests/delivery-acceptance';BASE=LEDGER/'coverage-audits/coverage-20261009-stage08-r1';OLD=BASE.parent/'coverage-20261008-stage06'
load=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
context=load(BASE/'execution-context.json')
assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in context['source_hashes'].items())
oldcontext=load(OLD/'audit-context.json')
assert all(oldcontext['source_hashes'][f]==h for f,h in context['source_hashes'].items())
subprocess.run([sys.executable,str(BASE/'report_python.py')],check=True)
subprocess.run(['node',str(BASE/'report.js')],check=True)
cum=BASE/'cumulative';cum.mkdir(exist_ok=True);inputs=cum/'inputs';inputs.mkdir(exist_ok=True)
shutil.copyfile(OLD/'.coverage',inputs/'.coverage.baseline');shutil.copyfile(BASE/'.coverage',inputs/'.coverage.supplemental')
sys.path.insert(0,str(OLD/'tools/python'));import coverage
cov=coverage.Coverage(config_file=str(BASE/'coverage.ini'),data_file=str(cum/'.coverage'),data_suffix=False)
cov.combine(data_paths=[str(inputs)],keep=True);cov.save();cov.json_report(outfile=str(cum/'backend-coverage.json'));cov.html_report(directory=str(cum/'html/backend'),title='MeetSpace cumulative same-source coverage')
node="""const fs=require('fs'),lib=require(process.argv[1]),base=process.argv[2],old=process.argv[3];const map=lib.createCoverageMap({'web/app.js':JSON.parse(fs.readFileSync(base+'/frontend-static-map.json'))});for(const dir of [old+'/javascript-data',base+'/javascript-data'])for(const f of fs.readdirSync(dir))map.merge(JSON.parse(fs.readFileSync(dir+'/'+f)).coverage);const file=map.fileCoverageFor('web/app.js');let result={file:'web/app.js',summary:file.toSummary().data,uncovered_lines:file.getUncoveredLines().map(Number),missing_statements:[],missing_functions:[],missing_branches:[],raw:file.data};for(const [id,n]of Object.entries(file.s))if(!n)result.missing_statements.push({id,location:file.statementMap[id]});for(const[id,n]of Object.entries(file.f))if(!n)result.missing_functions.push({id,location:file.fnMap[id]});for(const[id,ns]of Object.entries(file.b))ns.forEach((n,index)=>{if(!n)result.missing_branches.push({id,index,type:file.branchMap[id].type,condition:file.branchMap[id].loc,location:file.branchMap[id].locations[index]})});fs.writeFileSync(base+'/cumulative/frontend-coverage.json',JSON.stringify(result,null,2));"""
subprocess.run(['node','-e',node,str(OLD/'tools/node/node_modules/istanbul-lib-coverage'),str(BASE),str(OLD)],check=True)
def metrics(folder):
 b=load(folder/'backend-coverage.json')['totals'];f=load(folder/'frontend-coverage.json')['summary']
 return {'backend':{'lines':{'covered':b['covered_lines'],'total':b['num_statements'],'pct':100*b['covered_lines']/b['num_statements']},'branches':{'covered':b['covered_branches'],'total':b['num_branches'],'pct':100*b['covered_branches']/b['num_branches']}},'frontend':f}
m={'revision':context['revision'],'source_hashes':context['source_hashes'],'baseline':load(OLD/'metrics.json'),'supplemental_only':metrics(BASE),'cumulative':metrics(cum),'aggregation':'同业务源码SHA下stage07全部27入口实测计数＋本轮补测与原3smokes命中并集；绝不合并验收通过结果'};write(BASE/'metrics.json',m)
style='body{font:16px/1.7 system-ui;margin:30px auto;max-width:1150px;padding:0 24px;color:#24354a}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d5dce5;padding:8px;text-align:left}pre{white-space:pre-wrap;font-size:13px}.miss{background:#ffe3e3}.partial{background:#fff1c4}a{color:#135bb3}'
for folder,label in [(BASE,'本轮补测'),(cum,'当前所有测试累计')]:
 f=load(folder/'frontend-coverage.json');(folder/'html').mkdir(exist_ok=True);partial={x['condition']['start']['line'] for x in f['missing_branches']}
 code=''.join(f'<div id="L{n}" class="'+('miss' if n in f['uncovered_lines'] else 'partial' if n in partial else '')+f'">{n:3} {html.escape(line)}</div>' for n,line in enumerate((ROOT/'web/app.js').read_text().splitlines(),1))
 (folder/'html/frontend.html').write_text(f'<!doctype html><meta charset="utf-8"><title>{label}前端覆盖率</title><style>{style}</style><h1>{label} web/app.js</h1><p>行{f["summary"]["lines"]["pct"]}% · 分支{f["summary"]["branches"]["pct"]}%</p><a href="../frontend-coverage.json">完整计数</a><pre>{code}</pre>')
 for ignore in (folder/'html').rglob('.gitignore'):ignore.unlink()
b=m['cumulative']['backend'];f=m['cumulative']['frontend'];rows=''
for file,line,branch,link in [('app/server.py',b['lines'],b['branches'],'cumulative/html/backend/index.html'),('web/app.js',f['lines'],f['branches'],'cumulative/html/frontend.html')]:rows+=f'<tr><td><a href="{link}">{file}</a></td><td>{line["covered"]}/{line["total"]} · {line["pct"]:.2f}%</td><td>{branch["covered"]}/{branch["total"]} · {branch["pct"]:.2f}%</td></tr>'
(BASE/'index.html').write_text(f'<!doctype html><meta charset="utf-8"><title>MeetSpace 补测循环覆盖率</title><style>{style}</style><h1>MeetSpace 补测循环覆盖率</h1><p>修订{context["revision"]}；累计采用同SHA既有27入口与本轮实测命中。</p><table><tr><th>业务源码</th><th>可执行行</th><th>分支出口</th></tr>{rows}</table><p>覆盖率计数不等于验收通过。本轮仅执行新增8与细化2场景及3smokes，其他157场景没有重新验收。</p><p><a href="cycle-report.md">结果与循环收敛报告</a> · <a href="independent-review.json">独立证据及缺口审查</a> · <a href="metrics.json">前后计数与范围</a> · <a href="backend-coverage.json">仅本轮后端计数</a> · <a href="frontend-coverage.json">仅本轮前端计数</a></p>')
print(json.dumps(m['cumulative'],ensure_ascii=False))
