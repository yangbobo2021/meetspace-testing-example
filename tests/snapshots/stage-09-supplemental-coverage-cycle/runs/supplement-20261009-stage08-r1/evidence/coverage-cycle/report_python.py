import json,os,sys
from pathlib import Path
base=Path(__file__).resolve().parent;root=base.parents[3];sys.path.insert(0,'/Users/boboyang/work/sublang.ai/meeting-room-booking/tests/delivery-acceptance/coverage-audits/coverage-20261008-stage06/tools/python')
import coverage
os.chdir(root)
cov=coverage.Coverage(config_file=str(base/'coverage.ini'),data_file=str(base/'.coverage'),data_suffix=False)
paths=[str(p) for p in (base/'python-data').iterdir() if p.is_dir()]
cov.combine(data_paths=paths,keep=True);cov.save()
cov.json_report(outfile=str(base/'backend-coverage.json'))
cov.html_report(directory=str(base/'html/backend'),title='MeetSpace current-test coverage audit')
d=json.loads((base/'backend-coverage.json').read_text());print(json.dumps(d['totals']))
for f,data in d['files'].items():print(f,data['missing_lines'],data.get('missing_branches'))
