"""Reject stale, crashed or internally inconsistent isolated audit results."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'corrective-2026-10-12/run_isolated_rigid.py'
spec = importlib.util.spec_from_file_location('isolated_audit', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReceiptValidation(unittest.TestCase):
    def report(self):
        return dict(checks=[dict(status='pass'), dict(status='fail')],
                    summary=dict(pass_=1), generated_utc='2026-10-12T03:00:01Z')

    def valid(self):
        result = self.report()
        result['summary'] = {'pass': 1, 'fail': 1, 'info': 0}
        return result

    def test_completed_failure_is_preserved(self):
        module.validate_result(self.valid(), 1, '2026-10-12T03:00:00Z')

    def test_crash_cannot_adopt_an_old_report(self):
        with self.assertRaises(RuntimeError):
            module.validate_result(self.valid(), 2, '2026-10-12T03:00:00Z')

    def test_exit_and_summary_must_agree(self):
        with self.assertRaises(RuntimeError):
            module.validate_result(self.valid(), 0, '2026-10-12T03:00:00Z')

    def test_old_report_is_rejected(self):
        with self.assertRaises(RuntimeError):
            module.validate_result(self.valid(), 1, '2026-10-12T03:00:02Z')

    def test_inconsistent_rows_are_rejected(self):
        with self.assertRaises(RuntimeError):
            module.validate_result(self.report(), 1, '2026-10-12T03:00:00Z')


if __name__ == '__main__':
    unittest.main()
