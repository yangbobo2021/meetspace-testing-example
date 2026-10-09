import ast, collections, hashlib, json, sys
from pathlib import Path
R=Path.cwd();B=R/'tests/delivery-acceptance/coverage-audits/coverage-stage12-fresh-20261009';OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ctx=read(B/'audit-context.json');assert ctx['source_unchanged'];assert ctx['source_hashes']=={f:sha(R/f) for f in ctx['source_hashes']}
static=read(B/'frontend-static-map.json');actual=read(B/'frontend-coverage.json');inputs=sorted((B/'javascript-data').glob('*.json'))
def normalize(v):
 if isinstance(v,list):return [normalize(x) for x in v]
 if isinstance(v,dict):return {k:normalize(x) for k,x in v.items() if x is not None}
 return v
s={k:0 for k in static['s']};f={k:0 for k in static['f']};br={k:[0]*len(v) for k,v in static['b'].items()}
for path in inputs:
 d=read(path)['coverage']['web/app.js']
 for kind in ('statementMap','fnMap','branchMap'):assert normalize(d[kind])==normalize(static[kind]),str(path)
 for k,n in d['s'].items():s[k]=max(s[k],n)
 for k,n in d['f'].items():f[k]=max(f[k],n)
 for k,vs in d['b'].items():br[k]=[max(x,y) for x,y in zip(br[k],vs)]
assert set(actual['counter_inputs'])=={x.name for x in inputs}
assert all((v>0)==(actual['raw']['s'][k]>0) for k,v in s.items())
assert all((v>0)==(actual['raw']['f'][k]>0) for k,v in f.items())
assert all([(v>0) for v in vs]==[(v>0) for v in actual['raw']['b'][k]] for k,vs in br.items())
lines={}
for k,n in s.items():line=static['statementMap'][k]['start']['line'];lines[line]=max(lines.get(line,0),n)
js={'lines':{'covered':sum(n>0 for n in lines.values()),'total':len(lines)},'statements':{'covered':sum(n>0 for n in s.values()),'total':len(s)},'functions':{'covered':sum(n>0 for n in f.values()),'total':len(f)},'branches':{'covered':sum(n>0 for vs in br.values() for n in vs),'total':sum(len(vs) for vs in br.values())}}
for k,v in js.items():assert v['covered']==actual['summary'][k]['covered'] and v['total']==actual['summary'][k]['total']
assert read(B/'frontend-source-map.json')['sourcesContent']==[(R/'web/app.js').read_text()]
sys.path.insert(0,str(B.parent/'coverage-20261008-stage06/tools/python'));import coverage
sources=set();arcs=set();verified_arcs=set();unavailable_sources=set();raw_inputs=sorted((B/'python-data').glob('*/.coverage.*'))
for path in raw_inputs:
 data=coverage.CoverageData(basename=str(path));data.read()
 for filename in data.measured_files():
  assert str(B) in filename or filename==str(R/'app/server.py'),filename
  if Path(filename).exists():
   assert sha(Path(filename))==ctx['source_hashes']['app/server.py'],filename
   verified_arcs.update(data.arcs(filename) or [])
  else:unavailable_sources.add(filename)
  sources.add(filename);arcs.update(data.arcs(filename) or [])
assert raw_inputs
cov=coverage.Coverage(data_file=str(OUT/'reviewer.coverage'),branch=True,config_file=False)
data=cov.get_data();data.erase();data.add_arcs({str(R/'app/server.py'):sorted(verified_arcs)});cov.save()
cov.json_report(outfile=str(OUT/'independent-backend-coverage.json'),include=[str(R/'app/server.py')])
ind=read(OUT/'independent-backend-coverage.json');published=read(B/'backend-coverage.json');assert ind['totals']==published['totals'],(ind['totals'],published['totals'])
ip=next(iter(ind['files'].values()));pp=published['files']['app/server.py']
for kind in ('executed_lines','missing_lines','executed_branches','missing_branches','excluded_lines'):assert sorted(ip[kind])==sorted(pp[kind]),kind
fn={k:v for k,v in pp['functions'].items() if k};functions={'covered':sum(bool(v['executed_lines']) for v in fn.values()),'total':len(fn)}
result={'source_revision':ctx['revision'],'source_hashes':ctx['source_hashes'],'fresh_inputs':{'python':len(raw_inputs),'javascript':len(inputs),'measured_backend_copies':len(sources),'existing_hash_verified_backend_copies':len(sources)-len(unavailable_sources)},'frontend_recomputed':js,'backend_independently_rebuilt_totals':ind['totals'],'backend_functions':functions,'frontend_static_map_and_sourcescontent_match':True,'backend_raw_arcs_and_executable_line_denominators_match':True,'existing_raw_sources_hash_match':True,'removed_temporary_sources':sorted(unavailable_sources),'removed_source_counters_not_required_for_published_coverage':True,'independent_backend_policy':'Only extant copies with independently verified current source SHA contribute to rebuilt report. Removed temporary source counters excluded; all published coverage still matches.','no_old_counters_merged':True,'counter_policy':'independent presence union, not execution hit frequency','formal_verdict':None,'release_approved':False}
(OUT/'independent-counter-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
