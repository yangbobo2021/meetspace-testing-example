import json, collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]; L=R.parents[1]
defs=json.loads((L/'methods.json').read_text())['items']; groups=collections.defaultdict(list)
for name in ['api-execution-results.json','ui-execution-results.json','runtime-execution-results.json','root-supplement-results.json']:
 p=R/name
 if not p.exists(): continue
 for m in json.loads(p.read_text())['method_results']:groups[m['method_id']].append((name,m))
print('missing', [m['id'] for m in defs if m['id'] not in groups])
print('unknown',set(groups)-{m['id'] for m in defs})
for mid,records in groups.items():
 if any(m['status']!='passed' for _,m in records): print(mid,[(n,m['status'],m['actual']) for n,m in records])
print('unique methods',len(groups))
