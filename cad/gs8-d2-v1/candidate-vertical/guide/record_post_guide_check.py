"""Record the separate build-order test rerun after the selected guide rebuild.

This supplements the original batch result, including its expected stale-banner
failure. It does not rewrite that result or imply CAD/physical qualification.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT.parent
OUT = ROOT / 'guide/out-concealed-vents'
RECEIPT = OUT / 'post-guide-build-order-check.json'
LOG = OUT / 'post-guide-build-order-check.log'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bindings():
    paths = [
        'tests/test_build_order_docs.py', 'tests/_repo_git.py', 'steps.py',
        'make_assembly_text.py', 'make_bom_vertical.py', 'wiring_data.py',
        'harness_rules.py', 'routes.py', 'signal_routes.py',
        'ASSEMBLY-VERTICAL.md', 'BOM-VERTICAL.md', 'FPS-SERVICE-STUDY.md',
        'guide/build_guide_vertical.py', 'guide/build_guide_concealed_vents.py',
        'guide/README-CONCEALED-VENTS.md', 'guide/record_post_guide_check.py',
        'out/compact-kowa_lm6hc/manifest.json',
        'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json',
        'guide/out-concealed-vents/guide-receipt.json',
        '../checks.py', '../layout.py', '../make_tables.py',
    ]
    guide = json.loads((OUT / 'guide-receipt.json').read_text(encoding='utf-8'))
    paths.append('guide/out-concealed-vents/' + guide['guide_pdf_filename'])
    return {name: sha(ROOT / name) for name in paths}


def expected_test_count():
    tree = ast.parse((ROOT / 'tests/test_build_order_docs.py').read_text(encoding='utf-8'))
    return sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')
               for cls in tree.body if isinstance(cls, ast.ClassDef) for node in cls.body)


def verify_receipt():
    value = json.loads(RECEIPT.read_text(encoding='utf-8'))
    if value['input_sha256'] != bindings():
        raise RuntimeError('Post-guide build-order evidence has changed inputs')
    if value['log_sha256'] != sha(LOG):
        raise RuntimeError('Post-guide build-order log changed')
    if (value['exit_code'] != 0 or value['tests_run'] != expected_test_count() or
            value.get('expected_tests') != expected_test_count() or value['status'] != 'pass'):
        raise RuntimeError('Post-guide build-order rerun did not pass every source-defined test')
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        value = verify_receipt()
        print('Post-guide build-order receipt current: %d tests, exit %d' % (value['tests_run'], value['exit_code']))
        return 0
    before = bindings()
    guide = json.loads((OUT / 'guide-receipt.json').read_text(encoding='utf-8'))
    manifest_sha = sha(ROOT / 'out/compact-kowa_lm6hc/manifest.json')
    if guide['nominated_manifest_sha256'] != manifest_sha:
        raise RuntimeError('Guide receipt does not bind the selected manifest')
    for name, digest in guide['sources'].items():
        if sha(CAD / name) != digest:
            raise RuntimeError('Guide source changed before post-guide test: ' + name)
    command = [sys.executable, str(ROOT / 'tests/test_build_order_docs.py')]
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    LOG.write_bytes(result.stdout)
    output = result.stdout.decode('utf-8', 'replace')
    matches = re.findall(r'^Ran (\d+) tests? in ', output, flags=re.MULTILINE)
    count = int(matches[-1]) if matches else None
    unchanged = before == bindings()
    expected = expected_test_count()
    status = 'pass' if result.returncode == 0 and count == expected and unchanged else 'fail'
    value = {
        'scope': 'Separate post-guide build-order rerun only; original batch result preserved',
        'command': command, 'working_directory': str(ROOT),
        'python_version': sys.version.split()[0],
        'manifest_sha256': manifest_sha,
        'guide_receipt_sha256': sha(OUT / 'guide-receipt.json'),
        'test_source_sha256': sha(ROOT / 'tests/test_build_order_docs.py'),
        'input_sha256': before, 'inputs_unchanged_during_test': unchanged,
        'exit_code': result.returncode, 'tests_run': count, 'expected_tests': expected, 'status': status,
        'log': LOG.name, 'log_sha256': sha(LOG), 'physical_qualified': False,
    }
    RECEIPT.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(output, end='')
    print(RECEIPT)
    return 0 if status == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
