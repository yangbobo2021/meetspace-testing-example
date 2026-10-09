"""Archive one settled process; preserve raw hashes when public data is redacted."""
import argparse, collections, hashlib, json, shutil, subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--stage', required=True)
ap.add_argument('--run', required=True)
ap.add_argument('--coverage', required=True)
ap.add_argument('--extras', nargs='*', default=[])
args = ap.parse_args()
root = Path.cwd()
assets = root / 'tests/delivery-acceptance'
dst = root / 'tests/snapshots' / args.stage
run_dir = assets / 'runs' / args.run
assert not dst.exists(), 'immutable snapshot already exists'
assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
run = load(run_dir / 'run.json')
review = load(run_dir / 'review.json')
gate = load(run_dir / 'gate-report.json')
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == run['revision']
assert len(run['results']) == 167 and len(review['results']) == 167
if 'reviewed_run_sha256' in review:
    assert review['reviewed_run_sha256'] == sha(run_dir / 'run.json')
else:
    # The final reviewer binds its immutable inputs in a separate evidence file.
    binding_path = run_dir / 'review-revalidation/protected-inputs-final.json'
    binding = load(binding_path)
    assert binding['revision'] == run['revision']
    assert binding['all_protected_inputs_unchanged'] is True
    assert binding['hashes'][str((run_dir / 'run.json').relative_to(root))] == sha(run_dir / 'run.json')
    for name, expected_hash in binding['hashes'].items():
        assert sha(root / name) == expected_hash, ('review input changed', name)
    assert review['revision'] == run['revision']

for n, h in run['ledger_hashes'].items():
    assert sha(assets / n) == h, ('changed ledger', n)
selected = []
for name in ['project.json', 'requirements.json', 'resources.json', 'scenarios.json',
             'methods.json', 'coverage_review.json', 'white_box_review.json',
             'white-box-map.json', 'white-box-context.json', 'scenario-gate.json',
             'design-assessment.json', 'workflow-sessions.json',
             'stage10-product-failure-notice.json']:
    if (assets / name).is_file():
        selected.append(assets / name)
for name in ['runs/' + args.run, 'coverage-audits/' + args.coverage, *args.extras]:
    p = assets / name
    assert p.exists(), p
    selected.extend([p] if p.is_file() else [f for f in p.rglob('*') if f.is_file()])
selected.append(Path(__file__).resolve())
excluded, redactions, path_map = [], [], {}

def excluded_reason(p):
    rel = p.relative_to(assets)
    if any(part in ['__pycache__', 'node_modules', 'private-evidence', 'tools',
                    'python-data', 'bootstrap', 'source', 'source-map'] for part in rel.parts):
        return '运行缓存、依赖、隔离源码或私有比较材料'
    if any('projects' in part or part.startswith(('isolated-', 'private-')) for part in rel.parts):
        return '隔离运行实例及运行数据库'
    if p.parent.name in ['app', 'web']:
        return '隔离产品源码副本；以固定被测Git修订及逐文件SHA追溯'
    if p.suffix.lower() not in ['.json', '.jsonl', '.log', '.txt', '.md', '.py', '.js',
                                '.html', '.css', '.png', '.svg', '.patch', '.ini']:
        return '数据库、二进制工具或其他本机运行材料'
    return None

def sanitize(value, trail='', changed=None):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            path = trail + '/' + k
            if k in ['password_hash', 'salt', 'session_cookie', 'cookie_value', 'token_value']:
                out[k] = '[REDACTED_SYNTHETIC_AUTH_DATA]'
                changed.append(path)
            else:
                out[k] = sanitize(v, path, changed)
        return out
    if isinstance(value, list):
        return [sanitize(v, trail + '/' + str(i), changed) for i, v in enumerate(value)]
    return value

for src in sorted(set(selected)):
    rel = src.relative_to(assets)
    reason = excluded_reason(src)
    if reason:
        excluded.append({'path': str(rel), 'bytes': src.stat().st_size,
                         'sha256': sha(src), 'reason': reason})
        continue
    target = dst / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    if src.suffix == '.json':
        changes = []
        sanitized = sanitize(load(src), changed=changes)
        if changes:
            target.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2) + '\n')
            redactions.append({'path': str(rel), 'original_sha256': sha(src),
                               'archived_sha256': sha(target), 'fields': changes})
    path_map[str(src)] = str(rel)
assessment = {'stage': args.stage, 'tested_revision': run['revision'],
              'run_id': args.run, 'acceptance': gate['status'],
              'execution_counts': dict(collections.Counter(x['status'] for x in run['results'])),
              'independent_review_counts': dict(collections.Counter(x['status'] for x in review['results'])),
              'gates': {k: v['status'] for k, v in gate['gates'].items()},
              'full_acceptance_passed': gate['status'] == 'passed',
              'release_approved': False,
              'public_redactions': redactions, 'publication_exclusions': excluded}
(dst / 'process-assessment.json').write_text(json.dumps(assessment, ensure_ascii=False, indent=2) + '\n')
(dst / 'evidence-path-map.json').write_text(json.dumps(path_map, ensure_ascii=False, indent=2) + '\n')
(dst / 'manifest.json').write_text(json.dumps({
    'stage': args.stage, 'tested_revision': run['revision'],
    'source_sha256': {n: sha(root / n) for n in ['app/server.py', 'web/app.js']},
    'files': {str(p.relative_to(dst)): {'sha256': sha(p), 'bytes': p.stat().st_size}
              for p in sorted(dst.rglob('*')) if p.is_file()}
}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'archive': str(dst), 'assessment': {k: v for k, v in assessment.items()
                  if k not in ['publication_exclusions', 'public_redactions']},
                  'files': len(path_map), 'excluded': len(excluded),
                  'redactions': len(redactions)}, ensure_ascii=False))
