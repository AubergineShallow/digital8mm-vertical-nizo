# SPDX-License-Identifier: MIT
"""CAD-free controls for tests that consume the real canonical full-audit receipt."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from _full_audit_evidence import load_full_audit, sha


class FullAuditEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cv = Path(self.tmp.name) / 'candidate-vertical'
        self.variant = 'compact-kowa_lm6hc'
        self.out = self.cv / 'out' / self.variant
        self.out.mkdir(parents=True)
        for name in ('model.py', 'verify_candidate.py', 'steps.py', 'j7_collar_checks.py',
                     'driver_checks.py', 'j4_slide_checks.py', '../checks.py'):
            (self.cv / name).write_text('# synthetic test source: %s\n' % name, encoding='utf-8', newline='\n')
        self.manifest = dict(sources={'candidate-vertical/model.py': sha(self.cv / 'model.py')})
        self.write('manifest.json', self.manifest)
        self.record = dict(scope='full', variant=self.variant,
                           manifest_sha256=sha(self.out / 'manifest.json'),
                           verification_source_sha256=sha(self.cv / 'verify_candidate.py'),
                           state_model_sha256=sha(self.cv / 'steps.py'), checks=[
            dict(category='source_binding', id='candidate-vertical/model.py', status='pass'),
            dict(category='j7_float', id='camera_model_match', status='pass',
                 j7_collar_checks_sha256=sha(self.cv / 'j7_collar_checks.py'),
                 steps_sha256=sha(self.cv / 'steps.py'), r7_checks_sha256=sha(self.cv.parent / 'checks.py')),
            dict(category='driver_coverage', id='screws', status='pass',
                 driver_source_sha256=sha(self.cv / 'driver_checks.py')),
            dict(category='clearance', id='J4 synthetic fixture', status='pass',
                 j4_slide_checks_sha256=sha(self.cv / 'j4_slide_checks.py'),
                 r7_checks_sha256=sha(self.cv.parent / 'checks.py')),
            dict(category='interference', id='planted_failure', status='fail', overlap_mm3=2.0)])

    def write(self, name, value):
        (self.out / name).write_text(json.dumps(value), encoding='utf-8', newline='\n')

    def load(self, record=None):
        self.write('verification.json', self.record if record is None else record)
        return load_full_audit(self, self.cv, self.variant)

    def test_full_record_is_returned_unchanged_including_failures(self):
        self.assertEqual(self.load(), self.record)

    def test_partial_missing_scope_and_other_variant_are_rejected(self):
        for field, value in (('scope', 'j7'), ('scope', 'driver'),
                             ('scope', 'interference,motion,driver,clearance'),
                             ('scope', None), ('variant', 'original-kowa_lm6hc')):
            with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                self.load(dict(self.record, **{field: value}))

    def test_missing_canonical_report_fails_instead_of_skipping(self):
        with self.assertRaisesRegex(AssertionError, 'missing canonical full audit'):
            load_full_audit(self, self.cv, self.variant)

    def test_stale_manifest_checker_and_steps_are_rejected(self):
        for field in ('manifest_sha256', 'verification_source_sha256', 'state_model_sha256'):
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.load(dict(self.record, **{field: '0' * 64}))

    def test_stale_or_missing_helper_binding_is_rejected(self):
        for index in (1, 2, 3):
            for field in (k for k in self.record['checks'][index] if k.endswith('_sha256')):
                for value in ('0' * 64, None):
                    broken = copy.deepcopy(self.record)
                    broken['checks'][index][field] = value
                    with self.subTest(field=field, value=value), self.assertRaises(AssertionError):
                        self.load(broken)

    def test_export_source_bytes_and_binding_rows_must_match(self):
        for operation in ('missing', 'duplicate', 'failed'):
            broken = copy.deepcopy(self.record)
            if operation == 'missing':
                broken['checks'].pop(0)
            elif operation == 'duplicate':
                broken['checks'].append(copy.deepcopy(broken['checks'][0]))
            else:
                broken['checks'][0]['status'] = 'fail'
            with self.subTest(operation=operation), self.assertRaises(AssertionError):
                self.load(broken)
        (self.cv / 'model.py').write_text('# changed after export\n', encoding='utf-8', newline='\n')
        with self.assertRaisesRegex(AssertionError, 'stale export source'):
            self.load()

    def test_missing_and_duplicate_helper_contexts_are_rejected(self):
        for index in (1, 2, 3):
            broken = copy.deepcopy(self.record)
            broken['checks'].pop(index)
            with self.subTest(missing=index), self.assertRaises(AssertionError):
                self.load(broken)
        for index in (1, 2):
            broken = copy.deepcopy(self.record)
            broken['checks'].append(copy.deepcopy(broken['checks'][index]))
            with self.subTest(duplicate=index), self.assertRaises(AssertionError):
                self.load(broken)


if __name__ == '__main__':
    unittest.main(verbosity=2)
