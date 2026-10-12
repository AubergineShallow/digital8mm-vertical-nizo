"""A successful orchestration process cannot hide a failed child check."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'corrective-2026-10-12/aggregate_status.py'
SPEC = importlib.util.spec_from_file_location('corrective_aggregate', PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class AggregateVerdicts(unittest.TestCase):
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
