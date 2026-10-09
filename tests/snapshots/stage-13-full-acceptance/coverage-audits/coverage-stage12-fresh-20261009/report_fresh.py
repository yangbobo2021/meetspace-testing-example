import json,os,sys,hashlib
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[3];tools=base.parent/'coverage-20261008-stage06/tools';sys.path.insert(0,str(tools/'python'));import coverage
os.chdir(root)
paths=[str(p) for p in (base/'python-data').iterdir() if p.is_dir()]; measured=set()
for d in paths:
 for p in Path(d).glob('.coverage.*'):
  data=coverage.CoverageData(basename=str(p));data.read();measured.update(data.measured_files())
assert measured and all(str(base) in f or f==str(root/'app/server.py') for f in measured), 'Non-fresh counter path'
actual={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in measured if Path(f).exists()}; expected=hashlib.sha256((root/'app/server.py').read_bytes()).hexdigest();assert set(actual.values())=={expected}, actual
config=base/'coverage.ini';txt=config.read_text().split('[paths]')[0];config.write_text(txt+'[paths]\nserver =\n    '+str(root/'app')+'\n'+''.join('    '+str(Path(f).parent)+'\n' for f in sorted(measured) if f!=str(root/'app/server.py')))
(base/'.coverage').unlink(missing_ok=True)
cov=coverage.Coverage(config_file=str(config),data_file=str(base/'.coverage'),data_suffix=False);cov.combine(data_paths=paths,keep=True);cov.save();cov.json_report(outfile=str(base/'backend-coverage.json'));cov.html_report(directory=str(base/'html/backend'),title='Stage12 fresh source coverage')
(base/'backend-source-verification.json').write_text(json.dumps({'canonical_source_sha256':expected,'fresh_measured_files':sorted(measured),'existing_copy_sha256':actual,'removed_temporary_copy_count':len(measured)-len(actual),'old_counter_data_merged':False},ensure_ascii=False,indent=2))
print(json.dumps(json.loads((base/'backend-coverage.json').read_text())['totals']))
