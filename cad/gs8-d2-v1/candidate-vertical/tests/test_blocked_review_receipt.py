# SPDX-License-Identifier: MIT
"""CAD-free regression tests for recording blocked evidence without accepting its failures."""
from contextlib import redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import evidence_rules as ER
import reconcile_review_evidence as R
import make_coverage_vertical as C


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def set_path(value, path, item):
    keys = path.split('.')
    for key in keys[:-1]:
        value = value.setdefault(key, {})
    value[keys[-1]] = item


def fixture(root):
    """Small real files with valid identities and one retained, unqualified cooler witness."""
    root.mkdir(parents=True)
    put(root.parent / 'source.txt', 'geometry source')
    selected = root / 'out/compact-kowa_lm6hc'
    put(selected / 'step/tub.step', 'export bytes')
    put(selected / 'manifest.json', {'sources': {'source.txt': R.sha(root.parent / 'source.txt')},
                                     'files': {'step/tub.step': R.sha(selected / 'step/tub.step')}})
    mh = R.sha(selected / 'manifest.json')
    put(root.parent / 'out/build-receipt.json', {'hardware_gates': {'gates': {'coupon': 'open'}}})
    for _, _, verifier, _, _ in R.CASES:
        put(root / verifier, verifier)
    cooler = dict(category='interference', id='pi5/cooler', status='fail', overlap_mm3=79.902671)
    for label, path, verifier, source_key, manifest_key in R.CASES:
        value = {source_key: R.sha(root / verifier), 'summary': {'pass': 1, 'fail': 0, 'info': 0},
                 'checks': [], 'failing': {}, 'verification_dependency_sha256': {}}
        set_path(value, manifest_key, mh)
        if label == 'rigid':
            value['checks'] = [cooler] + [dict(category=c, id=i, status='info') for c, i in sorted(ER.expected_main_info())]
        put(root / path, value)
    for report, key, path in R.INPUT_BINDINGS:
        put(root / path, path)
        value = R.read(root / report)
        value[key] = R.sha(root / path)
        put(root / report, value)
    for report, path, want in R.STATUS_GATES:
        value = R.read(root / report)
        set_path(value, path, want)
        put(root / report, value)
    for variant in R.VARIANT_AUDITS:
        vd = root / 'out' / variant
        put(vd / 'manifest.json', {'variant': variant})
        for filename, verifier in R.VARIANT_REPORTS:
            put(vd / filename, dict(manifest_sha256=R.sha(vd / 'manifest.json'),
                                   verification_source_sha256=R.sha(root / verifier),
                                   checks=[cooler] if filename == 'verification.json' else [], failing={}, summary={}))
    return selected


class BlockedReceipt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='blocked-receipt-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'candidate'
        self.selected = fixture(self.root)
        self.target = self.selected / 'current-review-evidence.json'

    def run_main(self, *args):
        with patch.object(R, 'P', self.root), patch.object(R, 'TARGET', self.target), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return R.main(args)

    def fail_harness(self):
        path = self.selected / 'harness-checks.json'
        value = R.read(path)
        value.update(status='fail', failing={'mate_reach': ['j2_btn']},
                     checks=[dict(category='mate_reach', id='j2_btn', status='fail', problems=['lead too short'])])
        put(path, value)

    def test_generated_receipt_is_not_an_input_but_audits_still_check_it(self):
        put(self.target, {'mechanical_manifest_sha256': 'f' * 64})
        failures, result = R.reconcile(self.root)
        self.assertEqual(failures, [])
        self.assertTrue(result['source_and_export_hashes_verified'])
        self.assertTrue(result['evidence_bindings_verified'])
        self.assertEqual(result['active_rigid_failures'][0]['id'], 'pi5/cooler')
        self.assertEqual(result['release_status'], 'blocked')
        self.assertTrue(ER.selected_folder_findings(self.selected, R.sha(self.selected / 'manifest.json'), self.root))
        put(self.selected / 'unrelated.json', {'manifest_sha256': 'f' * 64})
        failures, _ = R.reconcile(self.root)
        self.assertEqual(failures[0][:2], ['foreign_manifest_report', 'out/compact-kowa_lm6hc/unrelated.json'])

    def test_blocked_record_is_current_deterministic_and_never_green(self):
        self.fail_harness()
        put(self.target, {'mechanical_manifest_sha256': 'f' * 64})
        original = self.target.read_bytes()
        self.assertEqual(self.run_main('--write'), 1)
        self.assertEqual(self.target.read_bytes(), original)
        self.assertEqual(self.run_main('--record-blocked'), 1)
        saved = self.target.read_bytes()
        receipt = R.read(self.target)
        self.assertEqual(receipt['mechanical_manifest_sha256'], R.sha(self.selected / 'manifest.json'))
        self.assertEqual(receipt['reconciliation_status'], 'blocked')
        self.assertFalse(receipt['evidence_gates_pass'])
        self.assertFalse(receipt['physical_qualified'])
        self.assertEqual(receipt['gate_failures'][0][0], 'harness_failures_differ')
        self.assertTrue(receipt['source_and_export_hashes_verified'])
        self.assertTrue(receipt['evidence_bindings_verified'])
        harness = next(row for row in receipt['reports'] if row['check'] == 'harness')
        self.assertEqual(harness['failing'], {'mate_reach': ['j2_btn']})
        self.assertEqual(harness['failed_checks'][0]['status'], 'fail')
        self.assertEqual(self.run_main('--record-blocked'), 1)
        self.assertEqual(self.target.read_bytes(), saved)
        self.assertEqual(self.run_main('--check'), 1)
        self.assertEqual(self.target.read_bytes(), saved)
        with patch.object(R, 'P', self.root), patch.object(R, 'TARGET', self.target), redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(R.main(['--check']), 1)
        self.assertNotIn('committed_evidence_stale', out.getvalue())
        receipt['gate_failures'] = []
        put(self.target, receipt)
        with patch.object(R, 'P', self.root), patch.object(R, 'TARGET', self.target), redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()):
            self.assertEqual(R.main(['--check']), 1)
        self.assertIn('committed_evidence_stale', out.getvalue())
        self.assertIn('harness_failures_differ', out.getvalue())

    def test_stale_report_and_source_are_preserved_as_identity_failures(self):
        path = self.selected / 'harness-checks.json'
        self.fail_harness()
        value = R.read(path)
        value['manifest_sha256'] = 'f' * 64
        put(path, value)
        put(self.root.parent / 'source.txt', 'changed source')
        failures, receipt = R.reconcile(self.root)
        self.assertFalse(receipt['source_and_export_hashes_verified'])
        self.assertFalse(receipt['evidence_bindings_verified'])
        self.assertTrue(any(f[0] == 'source_binding' for f in receipt['source_and_export_failures']))
        self.assertTrue(any(f[0] == 'report:harness' for f in failures))
        harness = next(row for row in receipt['reports'] if row['check'] == 'harness')
        self.assertFalse(harness['manifest_binding_current'])
        self.assertEqual(harness['failed_checks'][0]['id'], 'j2_btn')

    def test_failed_check_scope_is_an_acceptance_failure(self):
        path = self.selected / 'check-scope-checks.json'
        value = R.read(path)
        value['summary']['fail'] = 1
        value['checks'] = [dict(category='area_parity', id='hot_path_min_cut', status='fail')]
        put(path, value)
        failures, receipt = R.reconcile(self.root)
        self.assertTrue(any(f[:4] == ['status', 'Status', 'out/compact-kowa_lm6hc/check-scope-checks.json', 'summary.fail'] for f in failures))
        self.assertTrue(receipt['evidence_bindings_verified'])
        self.assertFalse(receipt['evidence_gates_pass'])
        value['summary']['fail'] = 0  # a misleading summary cannot hide the actual failed row
        put(path, value)
        failures, _ = R.reconcile(self.root)
        self.assertTrue(any(f[:2] == ['status', 'Failed check-scope rows'] for f in failures))

    def test_checkpoint_binds_blocked_receipt_without_claiming_acceptance(self):
        self.fail_harness()
        put(self.root / 'CHECKPOINT-STATUS.json', {'state': 'old checkpoint'})
        # The production generator compares both writer/rules identity and the complete fresh receipt.
        (self.root / 'reconcile_review_evidence.py').write_bytes(Path(R.__file__).read_bytes())
        (self.root / 'evidence_rules.py').write_bytes(Path(ER.__file__).read_bytes())
        self.assertEqual(self.run_main('--record-blocked'), 1)
        status = json.loads(C.checkpoint(self.root, {'reports': {}}))
        self.assertTrue(status['selected_evidence_current'])
        self.assertTrue(status['source_and_export_hashes_verified'])
        self.assertFalse(status['evidence_gates_pass'])
        self.assertFalse(status['physical_qualified'])
        self.assertEqual(status['evidence_reconciliation_status'], 'blocked')
        self.assertEqual(status['selected_evidence']['sha256'], R.sha(self.target))
        self.assertEqual(status['evidence_reconciler_that_wrote_current_evidence']['sha256'], R.read(self.target)['reconciler_sha256'])
        self.assertTrue(status['evidence_gate_failures'])
        put(self.root.parent / 'source.txt', 'later change')
        stale = json.loads(C.checkpoint(self.root, {'reports': {}}))
        self.assertFalse(stale['selected_evidence_current'])
        self.assertFalse(stale['source_and_export_hashes_verified'])
        self.assertEqual(stale['evidence_reconciliation_status'], 'stale')


class ProductionPrintCounts(unittest.TestCase):
    def manifest(self):
        return {'rows': [{'id': 'tub', 'kind': 'printed'}, {'id': 'panel', 'kind': 'printed'}],
                'print_poses': {'tub': {}, 'panel': {}, 'tab_catch_insert': {}, 'centring_gauge': {}},
                'files': {'stl/tub.stl': 'a', 'stl/panel.stl': 'b', 'stl/tab_catch_insert.stl': 'c'}}

    def test_historical_rows_are_not_reinterpreted_as_physical_pieces(self):
        count, failures = ER.production_print_counts(self.manifest())
        self.assertEqual(failures, [])
        self.assertEqual((count['assembly_row_count'], count['piece_count']), (2, 3))
        self.assertIsNone(count['declared_metadata'])

    def test_wrong_declared_counts_or_unbound_piece_fail(self):
        manifest = self.manifest()
        actual, _ = ER.production_print_counts(manifest)
        manifest['production_prints'] = {key: actual[key] for key in ('assembly_row_count', 'piece_count', 'files')}
        self.assertEqual(ER.production_print_counts(manifest)[1], [])
        for key, wrong in [('assembly_row_count', 3), ('piece_count', 2), ('files', ['stl/tub.stl'])]:
            bad = copy.deepcopy(manifest)
            bad['production_prints'][key] = wrong
            self.assertEqual(ER.production_print_counts(bad)[1][0][:2], ['production_print_metadata', key])
        del manifest['files']['stl/tab_catch_insert.stl']
        self.assertEqual(ER.production_print_counts(manifest)[1][0][0], 'production_print_files_unbound')


if __name__ == '__main__':
    unittest.main(verbosity=2)
