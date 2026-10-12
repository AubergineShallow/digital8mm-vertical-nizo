"""Distinguish a batch process exit from its recorded child-check verdicts."""
import hashlib
import json
import sys
import ast
from collections import Counter
from pathlib import Path


def expected_child_names(source):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'commands' for t in node.targets):
            if not isinstance(node.value, ast.List):
                raise ValueError('Runner commands are not a static list')
            names = [ast.literal_eval(row.elts[0]) for row in node.value.elts]
            if not names or len(names) != len(set(names)):
                raise ValueError('Runner commands are empty or duplicated')
            return names
    raise ValueError('Runner command list was not found')


def aggregate(record, child_report, expected_manifest, expected_names, expected_runner):
    errors = []
    process_exit = record['exit_code']
    if process_exit:
        errors.append('batch process returned nonzero')
    if not isinstance(child_report, dict) or not child_report.get('checks'):
        errors.append('child-check receipt is missing or empty')
        child_report = child_report if isinstance(child_report, dict) else {}
    if child_report.get('manifest_sha256') != expected_manifest:
        errors.append('child-check receipt belongs to a different manifest')
    if child_report.get('runner_sha256') != expected_runner:
        errors.append('child-check receipt belongs to a different runner')
    names = [row.get('check') for row in child_report.get('checks', [])]
    if Counter(names) != Counter(expected_names):
        errors.append('child-check set is incomplete, duplicated or unexpected')
    failed = []
    for row in child_report.get('checks', []):
        if row.get('exit_code') != 0:
            failed.append(dict(check=row.get('check'), exit_code=row.get('exit_code')))
    return dict(process_exit_code=process_exit, failed_children=failed,
                identity_errors=errors, status='blocked' if errors or failed else 'pass',
                scope='Recorded CAD/software checks only; no physical release')


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from cv_io import read_text, write_text
    receipt = Path(__file__).with_name('validation-run-primary_checks.json')
    child_path = root / 'out/compact-kowa_lm6hc/review-check-run.json'
    manifest = root / 'out/compact-kowa_lm6hc/manifest.json'
    runner = root / 'run_shadow_checks.py'
    prior = json.loads(read_text(receipt))
    record = next(r for r in prior['checks'] if r['check'] == 'primary_checks')
    child = json.loads(read_text(child_path))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = aggregate(record, child, digest(manifest), expected_child_names(read_text(runner)), digest(runner))
    result['inputs'] = {p.relative_to(root).as_posix(): digest(p)
                        for p in (receipt, child_path, manifest, runner, Path(__file__))}
    target = Path(__file__).with_name('validation-primary-summary.json')
    write_text(target, json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return int(result['status'] != 'pass')


if __name__ == '__main__':
    raise SystemExit(main())
