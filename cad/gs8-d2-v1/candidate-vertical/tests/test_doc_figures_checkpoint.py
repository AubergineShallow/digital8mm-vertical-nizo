# SPDX-License-Identifier: MIT
"""FPS / core-void document figures, unfilled placeholders and CHECKPOINT hash pairs (FX-D, 2026-10-11).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_doc_figures_checkpoint.py

Phase-2 verifier finding: evidence_rules.document_number_findings checked only the cooler witness, the power counts
and the gate count, so REVIEW.md still claimed '332 material checks / zero hits' for FPS while the selected report
failed, and its core-void intervals were stale. CHECKPOINT-STATUS.json called the 9ced753 reconciler hash
'evidence_reconciler' although the file had changed. Checks (CAD-free; the reports are synthetic so that the
evening refresh cannot move them):
- correct current and historical FPS / void sentences give no finding; planted wrong counts, status, hit volume,
  diagnostics count, void interval and an unfilled [[FX-NUM:...]] token each give exactly the expected finding;
- number_sources reads the FPS summary and void intervals from report files (a planted tree);
- checkpoint_hash_pairs: path, git_object and writer-of-selected-evidence pairs match; a tampered copy (changed file,
  missing file, wrong blob, evidence written by another reconciler) fails each pair; evaluate_docs_audit turns a
  mismatch into a 'checkpoint_hash' failure and the clean structure still exits 0;
- the live CHECKPOINT names the 9ced753 reconciler by git object and it equals the hash inside selected_evidence.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import evidence_rules as ER  # noqa: E402
from cv_io import write_text  # noqa: E402
from test_evidence_tooling import clean_audit  # noqa: E402

CV = HERE.parent
DASH = '–'
SRC = {
    'fps': {'current': {'status': 'fail', 'total': 332, 'hit_rows': 7, 'clear_rows': 325, 'max_hit_mm3': 23.131422911491473,
                        'diagnostics': 9, 'diagnostics_clear': True, 'report': 'cur.json'},
            'export18': {'status': 'geometric_pass_only', 'total': 332, 'hit_rows': 0, 'clear_rows': 332, 'max_hit_mm3': None,
                         'diagnostics': 9, 'diagnostics_clear': True, 'report': 'e18.json'}},
    'core_void': {'compact-kowa_lm6hc': {'interval': [658, 676]}, 'compact-fujinon_hf6xa': {'interval': [659, 677]},
                  'original-kowa_lm6hc': {'interval': [790, 808]}},
}
GOOD = (
    'FPS now **fails**: 325 of 332 material checks are clear, and 7 hit the tub (the switch bundle, 23.131 mm³ '
    'installed), plus nine clear non-material diagnostics.\n'
    '- Reviewed export18 is frozen history, manifest c9e1. Its 332 clear FPS material checks plus nine separate clear '
    'keepout diagnostics are not automatically current evidence.\n'
    'The frozen export18 reference is kept. Its **288 pass**, 332 clear FPS material checks plus nine clear '
    'non-material diagnostics are historical evidence for that geometry.\n'
    '| Selected FPS mated-carry | Current selected: 332 material checks / 7 hits; nine clear keepout diagnostics reported separately. |\n'
    'Conservative intervals are **658%s676 cm³** for [compact Kowa](out/comparison/volume-compact-kowa_lm6hc.json), '
    '**659%s677 cm³** for [compact Fujinon](out/comparison/volume-compact-fujinon_hf6xa.json) and **790%s808 cm³** '
    'for [original-storage Kowa](out/comparison/volume-original-kowa_lm6hc.json).\n' % (DASH, DASH, DASH))
BAD = (
    'the refreshed selected report records 332 material checks with zero hits plus nine separate clear non-material\n'
    'reservation diagnostics, bound to the shadow-plenum manifest.\n'
    '| Selected FPS mated-carry | Current selected: 332 material checks / zero hits; eight clear keepout diagnostics reported separately. |\n'
    'FPS now passes: 330 of 332 material checks are clear, and 2 hit the tub (switch bundle, 23.200 mm³).\n'
    'Intervals are **672%s689 cm³** for [compact Kowa](out/comparison/volume-compact-kowa_lm6hc.json).\n'
    'Result: [[FX-NUM:fps_selected_result]].\n'
    'The frozen export18 run had 325 of 332 material checks clear.\n' % DASH)


def sha(b):
    return hashlib.sha256(b).hexdigest()


class TestFiguresRules(unittest.TestCase):
    def test_correct_figures_give_no_finding(self):
        self.assertEqual(ER.document_number_findings('good.md', GOOD, SRC), [])

    def test_planted_wrong_figures_are_caught(self):
        got = ER.document_number_findings('bad.md', BAD, SRC)
        codes = sorted(f[0] for f in got)
        self.assertEqual(codes, ['core_void_interval'] + ['fps_check_number'] * 6 +
                         ['fps_hit_volume', 'fps_status_claim', 'unfilled_number_placeholder'], got)
        found = {(f[0], f[2]) for f in got}
        for x in [('fps_check_number', '332 checks / 0 hits'), ('fps_check_number', '8 diagnostics'),
                  ('fps_check_number', '330 of 332 clear'), ('fps_check_number', '2 hit'), ('fps_hit_volume', '23.200'),
                  ('fps_status_claim', 'pass'), ('core_void_interval', '672-689'),
                  ('unfilled_number_placeholder', '[[FX-NUM:fps_selected_result]]')]:
            self.assertIn(x, found)
        hist = [f for f in got if f[2] == '325 of 332 clear']
        self.assertEqual(len(hist), 1)
        self.assertIn('export18', hist[0][3])            # historical sentence checked against the export18 report

    def test_sources_read_from_reports(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rows = [{'item': 'a', 'hits': []}, {'item': 'b', 'hits': [{'part': 'tub', 'overlap_mm3': 1.25}, {'part': 'x', 'overlap_mm3': 2.5}]}]
            rep = {'status': 'fail', 'static_and_carried_checks': rows, 'non_material_reservation_diagnostics': [{'item': 'k', 'hits': []}]}
            for rel, obj in ((ER.FPS_REPORTS['current'], rep), (ER.VOID_REPORT % 'compact-kowa_lm6hc', {ER.VOID_FIELD: [1, 2]})):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                write_text(root / rel, json.dumps(obj))
            s = ER.fps_summary(root / ER.FPS_REPORTS['current'])
            self.assertEqual((s['total'], s['hit_rows'], s['clear_rows'], s['max_hit_mm3'], s['diagnostics'], s['diagnostics_clear']),
                             (2, 1, 1, 2.5, 1, True))
            self.assertIsNone(ER.fps_summary(root / ER.FPS_REPORTS['export18']))
            # a missing source is a finding, not a silent pass
            src = {'fps': {'current': None, 'export18': None}, 'core_void': {x: None for x in ER.VOID_VARIANTS}}
            got = sorted(f[0] for f in ER.document_number_findings('t', 'Current selected: 332 material checks / zero hits.\n'
                                                                   'Intervals **1%s2 cm3** for [compact Kowa](x).\n' % DASH, src))
            self.assertEqual(got, ['core_void_interval', 'fps_check_number'])

    def test_placeholders_are_found_in_every_live_page(self):
        token = '[[FX-NUM:' + 'coupon_state]]'
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel in ('vent-study/x/README.md', 'history/old/README.md', 'review-2026-10-10/FIX-LOG.md', 'REVIEW.md'):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                write_text(root / rel, 'State: %s.\n' % token if rel != 'REVIEW.md' else 'No placeholder here.\n')
            got = ER.documents_number_findings(root, src={})
            self.assertEqual([(f[0], f[1], f[2]) for f in got], [('unfilled_number_placeholder', 'vent-study/x/README.md', token)])
            write_text(root / 'REVIEW.md', 'Void **%s cm3** for [compact Kowa](x).\n' % token)
            got = ER.documents_number_findings(root, src={})
            self.assertEqual(sorted(f[1] for f in got), ['REVIEW.md', 'vent-study/x/README.md'])

    def test_live_sources_are_the_report_values(self):
        src = ER.number_sources(CV)
        for era, rel in ER.FPS_REPORTS.items():
            self.assertEqual(src['fps'][era], dict(ER.fps_summary(CV / rel), report=rel), era)
        for v in ER.VOID_VARIANTS:
            want = json.loads((CV / (ER.VOID_REPORT % v)).read_text(encoding='utf-8'))[ER.VOID_FIELD]
            self.assertEqual(src['core_void'][v]['interval'], list(want), v)


class TestCheckpointHashPairs(unittest.TestCase):
    def tree(self, d):
        root = Path(d)
        write_text(root / 'recon.py', 'print(1)\n')
        blob = b'old reconciler\n'
        write_text(root / 'ev.json', json.dumps({'reconciler_sha256': sha(blob)}))
        status = {'selected_evidence': {'path': 'ev.json', 'sha256': sha((root / 'ev.json').read_bytes())},
                  'evidence_reconciler_that_wrote_current_evidence': {'git_object': 'c0ffee:x/recon.py', 'sha256': sha(blob)},
                  'current_evidence_reconciler': {'path': 'recon.py', 'sha256': sha((root / 'recon.py').read_bytes())},
                  'guide': {'receipt': {'path': 'recon.py', 'sha256': sha((root / 'recon.py').read_bytes())}}}
        blobs = {'c0ffee:x/recon.py': blob}
        return root, status, blobs

    def test_pairs_match_and_tampering_fails_each(self):
        with tempfile.TemporaryDirectory() as d:
            root, status, blobs = self.tree(d)
            rows = ER.checkpoint_hash_pairs(status, root, git_blob=blobs.get)
            self.assertEqual(sorted((r['field'], r['kind']) for r in rows), [
                ('current_evidence_reconciler', 'path'), ('evidence_reconciler_that_wrote_current_evidence', 'git_object'),
                ('evidence_reconciler_that_wrote_current_evidence.sha256', 'writer_of_selected_evidence'),
                ('guide.receipt', 'path'), ('selected_evidence', 'path')])
            self.assertTrue(all(r['match'] for r in rows), rows)
            # tampered copy: changed file, missing nested file, unknown blob, evidence from another reconciler
            write_text(root / 'recon.py', 'print(2)\n')
            bad = copy.deepcopy(status)
            bad['guide']['receipt']['path'] = 'missing.json'
            bad['evidence_reconciler_that_wrote_current_evidence']['git_object'] = 'c0ffee:other.py'
            write_text(root / 'ev.json', json.dumps({'reconciler_sha256': '0' * 64}))
            failed = sorted(r['field'] for r in ER.checkpoint_hash_pairs(bad, root, git_blob=blobs.get) if not r['match'])
            self.assertEqual(failed, ['current_evidence_reconciler', 'evidence_reconciler_that_wrote_current_evidence',
                                      'evidence_reconciler_that_wrote_current_evidence.sha256', 'guide.receipt',
                                      'selected_evidence'])

    def test_verdict_fails_on_a_mismatch(self):
        a = clean_audit()
        a['checkpoint_hashes'] = [dict(field='current_evidence_reconciler', kind='path', target='recon.py',
                                       recorded='a' * 64, actual='a' * 64, match=True)]
        self.assertEqual(ER.evaluate_docs_audit(a)['exit_code'], 0)
        a['checkpoint_hashes'][0].update(actual='b' * 64, match=False)
        v = ER.evaluate_docs_audit(a)
        self.assertEqual(v['exit_code'], 1)
        self.assertEqual([f[:4] for f in v['failures']], [['checkpoint_hash', 'CHECKPOINT-STATUS.json', 'current_evidence_reconciler', 'recon.py']])

    def test_live_checkpoint_names_the_reconciler_that_wrote_the_evidence(self):
        status = json.loads((CV / 'CHECKPOINT-STATUS.json').read_text(encoding='utf-8'))
        self.assertNotIn('evidence_reconciler', status)   # the old name read as the current reconciler
        w = status['evidence_reconciler_that_wrote_current_evidence']
        rows = {r['field']: r for r in ER.checkpoint_hash_pairs(status, CV)}
        self.assertTrue(rows['evidence_reconciler_that_wrote_current_evidence']['match'], w)
        self.assertTrue(rows['evidence_reconciler_that_wrote_current_evidence.sha256']['match'])
        self.assertEqual(status['current_evidence_reconciler']['path'], 'reconcile_review_evidence.py')
        self.assertIn('current_evidence_reconciler', rows)


if __name__ == '__main__':
    unittest.main()
