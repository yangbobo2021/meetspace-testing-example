"""Adapt only writable-path spelling for installed Playbook 16 runtime.
Compiled Skill workflow, role assignments, checker and allowed directory stay unchanged.
"""
import json, os, runpy, sys
from pathlib import Path
_original_dumps = json.dumps
def compatible_dumps(value, *args, **kwargs):
    if isinstance(value, dict) and 'captain' in value and 'players' in value and 'playbooks' in value:
        for agent in [value['captain'], *value['players'].values()]:
            permissions = agent.get('permissions', {})
            if permissions.get('mode') == 'auto':
                permissions['writablePaths'] = [os.path.relpath(path, Path.cwd()) for path in permissions.get('writablePaths', [])]
                assert permissions['writablePaths'] == ['tests/delivery-acceptance']
    return _original_dumps(value, *args, **kwargs)
json.dumps = compatible_dumps
runpy.run_path('/Users/boboyang/.codex/skills/app-delivery-acceptance/scripts/run_workflow.py', run_name='__main__')
