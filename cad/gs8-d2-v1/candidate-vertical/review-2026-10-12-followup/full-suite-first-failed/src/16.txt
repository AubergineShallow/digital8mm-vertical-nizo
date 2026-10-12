"""A successful orchestration process cannot hide a failed child check."""
import importlib.util
from pathlib import Path
import unittest
import contextlib
import io
import json
import runpy
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'corrective-2026-10-12/aggregate_status.py'
SPEC = importlib.util.spec_from_file_location('corrective_aggregate', PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class AggregateVerdicts(unittest.TestCase):
    def test_standalone_runner_preserves_child_failure_exit(self):
        cv=PATH.parents[1]
        sys.path.insert(0,str(cv))
        for failed in (False,True):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);runner=root/'run_shadow_checks.py'
                shutil.copyfile(cv/'run_shadow_checks.py',runner)
                out=root/'out/compact-kowa_lm6hc';out.mkdir(parents=True)
                (out/'manifest.json').write_text('{}',encoding='utf-8',newline='\n')
                def child(cmd,**kwargs):
                    return SimpleNamespace(returncode=1 if failed and Path(cmd[1]).name=='verify_harness_checks.py' else 0)
                with patch('subprocess.run',side_effect=child), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as stopped:
                        runpy.run_path(str(runner),run_name='__main__')
                self.assertEqual(stopped.exception.code,1 if failed else 0)
                receipt=json.loads((out/'review-check-run.json').read_text(encoding='utf-8'))
                self.assertEqual(len(receipt['checks']),15)
                self.assertEqual(sum(r['exit_code']!=0 for r in receipt['checks']),int(failed))

    def test_zero_process_exit_does_not_hide_child_failure(self):
        result = MOD.aggregate({'exit_code': 0}, {'manifest_sha256': 'm', 'runner_sha256': 'r', 'checks': [
            {'check': 'mesh', 'exit_code': 0}, {'check': 'harness', 'exit_code': 1}]}, 'm', ['mesh', 'harness'], 'r')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['process_exit_code'], 0)
        self.assertEqual(result['failed_children'], [{'check': 'harness', 'exit_code': 1}])

    def test_missing_or_stale_receipt_is_blocked(self):
        for report in (None, [], {}, {'manifest_sha256': 'old', 'checks': [{'exit_code': 0}]}):
            self.assertEqual(MOD.aggregate({'exit_code': 0}, report, 'm', ['mesh'], 'r')['status'], 'blocked')

    def test_complete_matching_success_is_only_a_software_pass(self):
        result = MOD.aggregate({'exit_code': 0}, {'manifest_sha256': 'm', 'runner_sha256': 'r',
                               'checks': [{'check': 'mesh', 'exit_code': 0}]}, 'm', ['mesh'], 'r')
        self.assertEqual(result['status'], 'pass')
        self.assertIn('no physical release', result['scope'])

    def test_partial_duplicate_and_wrong_runner_are_blocked(self):
        for rows, runner in ((['mesh'], 'r'), (['mesh', 'harness', 'harness'], 'r'),
                             (['mesh', 'harness'], 'old')):
            report = dict(manifest_sha256='m', runner_sha256=runner,
                          checks=[dict(check=name, exit_code=0) for name in rows])
            self.assertEqual(MOD.aggregate({'exit_code': 0}, report, 'm', ['mesh', 'harness'], 'r')['status'], 'blocked')

    def test_expected_set_is_derived_without_executing_runner(self):
        source = "commands=[('mesh', [dangerous()]), ('harness', [])]\nraise RuntimeError('not executed')"
        self.assertEqual(MOD.expected_child_names(source), ['mesh', 'harness'])


if __name__ == '__main__':
    unittest.main()
