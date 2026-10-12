# SPDX-License-Identifier: MIT
"""Evidence tooling hardening (review 2026-10-10 FP-04: VN-05, VN-09, VN-31).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_evidence_tooling.py

Docs audit: a failed binding, a stale or foreign selected report, a stale guide nomination, a broken link or a wrong
repeated figure makes it exit 1; default and --check never write; --check catches a stale committed audit; the output
is deterministic. Reconciler: a planted foreign-manifest or unbound JSON in the selected folder fails it, a declared
historical report must bind its declared manifest, the main audit's info rows must be exactly the accepted set, the
keepout rule only accepts the declared mating partner, and pass-only --write/--out never write while a gate fails.
The explicit --record-blocked mode has separate regressions in test_blocked_review_receipt.py. Stale reports are
out of the selected folder. CAD-free; scripts run inside a light copy of the tree (tests/_evidence_fixture.py).
"""
from pathlib import Path
import ast
import copy
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import _evidence_fixture as FX  # noqa: E402
import evidence_rules as ER  # noqa: E402

CV = FX.CV
SEL = CV / 'out/compact-kowa_lm6hc'
FIXTURE = None


def setUpModule():
    global FIXTURE
    FIXTURE = FX.Fixture()


def tearDownModule():
    FIXTURE.cleanup()


def audit(cv, *args):
    out = cv.parent / ('audit-%d.json' % len(list(cv.parent.glob('audit-*.json'))))
    rc, so, se = FX.run(cv / 'review_docs_audit.py', '--out', out, *args)
    assert 'Traceback' not in se, se[-2000:]
    return rc, json.loads(out.read_text(encoding='utf-8'))


def codes(a):
    return {(f[0], f[1]) for f in a['verdict']['failures']}


def clean_audit():
    """Smallest all-pass docs-audit structure evaluate_docs_audit() reads."""
    ok = {'checked': 1, 'missing': [], 'changed': [], 'pass': True}
    rep = lambda p: {'path': p, 'same_manifest': True, 'manifest_sha256': 'a' * 64, 'verifier_hash_current': True, 'verifier_file': 'v.py'}
    return {'variants': [{'variant': 'v', 'sources': dict(ok), 'files': dict(ok), 'bound_cache': {'state': 'complete', 'action': 'none'},
                          'mesh_manifest_identical': True, 'printed_count': 9, 'expected_printed_count': 9, 'printed_valid_one_solid': True,
                          'keepouts_non_material': True, 'selected_folder_findings': [], 'reports': [rep('out/v/verification.json')]}],
            'bom': {'generator_outputs_current': True, 'invalid_parent_references': [], 'missing_local_sources': [], 'cad_imported': False,
                    'export18_selection_claim': {'claimed': True}},
            'concealed_bom_preservation': {'unchanged': True, 'differences': []}, 'missing_document_local_links': [],
            'selected_supplemental_reports': [{'path': 's.json', 'same_primary_manifest': True, 'verifier_hash_current': True,
                                               'evidence_role': ER.CURRENT_ROLE}],
            'concealed_vent_reports': [], 'report_inputs': {'r/k': {'path': 'x', 'matches_report': True}},
            'assembly_comparison': {'candidate_manifest_bindings': [{'v': True}]},
            'core_void_reports': [{'path': 'c.json', 'same_variant_manifest': True, 'verifier_hash_current': True}],
            'selected_usb_head_report': {'path': 'h.json', 'evidence_role': ER.HEAD_CURRENT_ROLE, 'step_bindings': dict(ok)},
            'plenum_coupon_identity': {'path': 'i.json', 'same_primary_manifest': True, 'source_current': True, 'receipt_bindings': dict(ok),
                                       'receipts': [{'path': 'r.json', 'same_primary_manifest': True, 'files': dict(ok)}]},
            'structural_pdf': {'receipt': {'path': 'p.json'}, 'same_primary_manifest': True, 'pdf_hash_matches': True, 'source_bindings': dict(ok)},
            'checkpoint_status': {'same_primary_manifest': True, 'selected_evidence_binding': True, 'preserved_export18_binding': True,
                                  'guide_receipt_current': True, 'guide_nominated_manifest_current': True, 'guide_manifest_claim': True},
            'checkpoint_numbers': [{'field': 'open_inherited_gates', 'recorded': 56, 'source_value': 56, 'match': True}],
            'document_numbers': [],
            'guide_bound_cache': {'receipt': 'g.json', 'nominated_manifest_current': True, 'nominated_manifest_sha256': 'a' * 64,
                                  'state': 'complete', 'action': 'none', 'sources': dict(ok)}}


class TestDocsAuditVerdict(unittest.TestCase):
    def test_clean_structure_exits_zero_and_each_defect_exits_one(self):
        self.assertEqual(ER.evaluate_docs_audit(clean_audit()), {'failures': [], 'rebuildable_caches': [], 'declared_pending': [], 'exit_code': 0})
        mutations = {
            'binding': lambda a: a['variants'][0]['sources'].update(changed=['candidate-vertical/model.py'], **{'pass': False}),
            'stale_selected_report': lambda a: a['variants'][0]['reports'][0].update(verifier_hash_current=False),
            'selected_report_missing': lambda a: a['variants'][0]['reports'][0].update(missing=True),
            'foreign_manifest_report': lambda a: a['variants'][0]['selected_folder_findings'].append(('foreign_manifest_report', 'out/v/x.json', 'binds f')),
            'missing_local_link': lambda a: a['missing_document_local_links'].append({'document': 'README.md', 'target': 'nope.md'}),
            'bom_outputs_stale': lambda a: a['bom'].update(generator_outputs_current=False),
            'bom_claim': lambda a: a['concealed_bom_preservation'].update(unchanged=False, differences=[{'line': 'D2-1'}]),
            'guide_manifest_stale': lambda a: a['guide_bound_cache'].update(nominated_manifest_current=False),
            'checkpoint_claim': lambda a: a['checkpoint_status'].update(guide_nominated_manifest_current=False),
            'checkpoint_number': lambda a: a['checkpoint_numbers'][0].update(recorded=55, match=False),
            'power_query_number': lambda a: a['document_numbers'].append(['power_query_number', 'REVIEW.md', '201/625', '201/659', 'ctx']),
            'bound_files': lambda a: a['guide_bound_cache'].update(state='mismatch'),
            'historical_report_binding': lambda a: a['selected_supplemental_reports'][0].update(declared_historical='x', historical_binding_ok=False),
        }
        for code, mutate in mutations.items():
            a = clean_audit()
            mutate(a)
            v = ER.evaluate_docs_audit(a)
            self.assertEqual(v['exit_code'], 1, code)
            self.assertIn(code, {f[0] for f in v['failures']}, code)

    def test_guide_receipt_source_drift_is_a_binding_failure(self):
        # fixup-1 (FP-04): an edited guide input or document leaves a stale guide; it must fail, not pass silently.
        a = clean_audit()
        a['guide_bound_cache']['sources'] = {'checked': 2, 'missing': [], 'changed': ['candidate-vertical/guide/raster.cpp'],
                                             'pass': False}
        v = ER.evaluate_docs_audit(a)
        self.assertEqual(v['exit_code'], 1)
        self.assertIn(['binding', 'g.json', 'sources', 'missing 0 changed 1: candidate-vertical/guide/raster.cpp'],
                      v['failures'])

    def test_rebuildable_cache_only_exits_three_and_pending_is_listed(self):
        a = clean_audit()
        a['variants'][0]['bound_cache'] = {'state': 'cache_missing', 'action': 'regenerate'}
        a['variants'][0]['reports'][0] = {'path': 'out/v/verification.json', 'missing': True, 'declared_pending': 'FP-13'}
        v = ER.evaluate_docs_audit(a)
        self.assertEqual((v['exit_code'], v['failures']), (3, []))
        self.assertEqual(v['declared_pending'], [['out/v/verification.json', 'FP-13']])


class TestDocsAuditFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc0, cls.a0 = audit(FIXTURE.base / CV.relative_to(FX.REPO))

    def test_untouched_copy_reports_the_known_failures_with_exit_one(self):
        self.assertEqual(self.rc0, 1)
        self.assertEqual(self.a0['verdict']['exit_code'], 1)
        self.assertEqual(self.a0['generated_utc'], ER.UNRECORDED)

    def test_tampered_source_is_a_failure(self):
        cv = FIXTURE.clone()
        m = json.loads((cv / 'out/compact-kowa_lm6hc/manifest.json').read_text(encoding='utf-8'))
        rel = next(r for r, h in sorted(m['sources'].items()) if (cv.parent / r).is_file() and FX.sha(cv.parent / r) == h)
        with open(cv.parent / rel, 'ab') as f:
            f.write(b'\n# tampered\n')
        rc, a = audit(cv)
        self.assertEqual(rc, 1)
        for v in a['variants']:
            self.assertIn(rel, v['sources']['changed'])
            self.assertFalse(v['sources']['pass'])
        self.assertIn(('binding', 'out/compact-kowa_lm6hc/manifest.json'), codes(a))
        before = {v['variant']: v['sources']['changed'] for v in self.a0['variants']}
        self.assertTrue(all(rel not in c for c in before.values()))

    def test_edited_guide_source_is_listed(self):
        # fixup-1 (FP-04): tamper one source the guide receipt binds (present and matching in the copy).
        cv = FIXTURE.clone()
        rec = json.loads((cv / 'guide/out-concealed-vents/guide-receipt.json').read_text(encoding='utf-8'))
        rel = next(r for r, h in sorted(rec['sources'].items())
                   if r.endswith('software_lineart.py') and (cv.parent / r).is_file() and FX.sha(cv.parent / r) == h)
        with open(cv.parent / rel, 'ab') as f:
            f.write(b'\n# tampered\n')
        rc, a = audit(cv)
        self.assertEqual(rc, 1)
        self.assertIn(rel, a['guide_bound_cache']['sources']['changed'])
        self.assertNotIn(rel, self.a0['guide_bound_cache']['sources']['changed'])
        self.assertIn(('binding', 'guide/out-concealed-vents/guide-receipt.json'), codes(a))

    def test_guide_nomination_link_figures_and_foreign_report_fail(self):
        cv = FIXTURE.clone()
        rp = cv / 'guide/out-concealed-vents/guide-receipt.json'
        r = json.loads(rp.read_text(encoding='utf-8'))
        r['nominated_manifest_sha256'] = 'f' * 64
        rp.write_text(json.dumps(r, indent=2), encoding='utf-8', newline='\n')
        with open(cv / 'README.md', 'a', encoding='utf-8', newline='\n') as f:
            f.write('\n[planted](no-such-file-fp04.md) 201 poses / 625 queries.\n')
        cp = cv / 'CHECKPOINT-STATUS.json'
        c = json.loads(cp.read_text(encoding='utf-8'))
        c['open_inherited_gates'] = 55
        c['guide']['manifest_binding_current'] = True   # FX: plant the false claim (the live CHECKPOINT honestly says False)
        cp.write_text(json.dumps(c, indent=2), encoding='utf-8', newline='\n')
        (cv / 'out/compact-kowa_lm6hc/zz-planted.json').write_text(json.dumps({'manifest_sha256': 'f' * 64}), encoding='utf-8', newline='\n')
        rc, a = audit(cv)
        self.assertEqual(rc, 1)
        new = {tuple(f[:2]) for f in a['verdict']['failures'] if f not in self.a0['verdict']['failures']}
        for want in [('guide_manifest_stale', 'guide/out-concealed-vents/guide-receipt.json'), ('checkpoint_claim', 'CHECKPOINT-STATUS.json'),
                     ('power_query_number', 'README.md'), ('checkpoint_number', 'CHECKPOINT-STATUS.json'),
                     ('inherited_gate_number', 'CHECKPOINT-STATUS.json'), ('foreign_manifest_report', 'out/compact-kowa_lm6hc/zz-planted.json')]:
            self.assertIn(want, new)
        self.assertIn(['missing_local_link', 'README.md', 'no-such-file-fp04.md'], a['verdict']['failures'])
        self.assertNotIn(['missing_local_link', 'README.md', 'no-such-file-fp04.md'], self.a0['verdict']['failures'])

    def test_default_and_check_are_read_only_and_check_detects_staleness(self):
        cv = FIXTURE.clone()
        committed = cv / 'out/review-docs-audit.json'
        h0 = FX.sha(committed)
        rc, so, se = FX.run(cv / 'review_docs_audit.py')
        self.assertEqual((rc, FX.sha(committed)), (1, h0))
        rc, so, se = FX.run(cv / 'review_docs_audit.py', '--check')
        self.assertEqual((rc, FX.sha(committed)), (1, h0))
        self.assertIn('committed_audit_stale', so)
        rc, so, se = FX.run(cv / 'review_docs_audit.py', '--write')
        self.assertNotEqual(FX.sha(committed), h0)
        h1 = FX.sha(committed)
        rc, so, se = FX.run(cv / 'review_docs_audit.py', '--check')
        self.assertNotIn('committed_audit_stale', so, 'the audit is not deterministic')
        self.assertEqual(FX.sha(committed), h1)
        self.assertNotIn(b'\r', committed.read_bytes())


class TestReconciler(unittest.TestCase):
    def reconcile(self, cv, *args):
        target = cv / 'out/compact-kowa_lm6hc/current-review-evidence.json'
        h = FX.sha(target)
        rc, so, se = FX.run(cv / 'reconcile_review_evidence.py', *args)
        self.assertNotIn('Traceback', se, se[-2000:])
        self.assertEqual(FX.sha(target), h, 'the reconciler wrote while a gate failed')
        return rc, FX.first_json(so)

    def test_planted_foreign_unbound_and_historical_reports_fail(self):
        base_rc, base = self.reconcile(FIXTURE.clone())
        self.assertEqual(base_rc, 1)
        cv = FIXTURE.clone()
        d = cv / 'out/compact-kowa_lm6hc'
        (d / 'zz-foreign.json').write_text(json.dumps({'manifest_sha256': 'f' * 64, 'status': 'pass'}), encoding='utf-8', newline='\n')
        (d / 'renders/zz-unbound.json').parent.mkdir(exist_ok=True)
        (d / 'renders/zz-unbound.json').write_text(json.dumps({'status': 'pass'}), encoding='utf-8', newline='\n')
        wp = d / 'wall-probe-context.json'
        w = json.loads(wp.read_text(encoding='utf-8'))
        w['manifest_sha256'] = FX.sha(d / 'manifest.json')
        wp.write_text(json.dumps(w), encoding='utf-8', newline='\n')
        rc, out = self.reconcile(cv, '--write')
        self.assertEqual(rc, 1)
        got = {(f[0], f[1]) for f in out['failures']}
        for want in [('foreign_manifest_report', 'out/compact-kowa_lm6hc/zz-foreign.json'),
                     ('unbound_report', 'out/compact-kowa_lm6hc/renders/zz-unbound.json'),
                     ('historical_report_binding', 'out/compact-kowa_lm6hc/wall-probe-context.json')]:
            self.assertIn(want, got)
            self.assertNotIn(want, {(f[0], f[1]) for f in base['failures']})

    def test_live_selected_folders_are_clean(self):
        for v in FX.VARIANTS:
            d = CV / 'out' / v
            self.assertEqual(ER.selected_folder_findings(d, FX.sha(d / 'manifest.json'), CV), [], v)

    def test_exact_info_set(self):
        # phase-1 closeout: the committed main audit was refreshed by run_shadow_checks.py (20 categories, incl. the
        # FP-05 motion_coverage and FP-08 J7 info rows), so it is held to the reconciler's own accepted set, exactly.
        v = json.loads((SEL / 'verification.json').read_text(encoding='utf-8'))
        accepted = ER.expected_main_info()
        self.assertEqual(ER.info_set_findings(v, accepted), [])
        extra = copy.deepcopy(v)
        extra['checks'].append({'category': 'interference', 'id': 'cooler/x1203', 'status': 'info'})
        self.assertEqual(ER.info_set_findings(extra, accepted), [('unexpected_info_row', 'interference', 'cooler/x1203')])
        fewer = copy.deepcopy(v)
        fewer['checks'] = [c for c in fewer['checks'] if c['id'] != 'eyepiece/panel']
        self.assertEqual(ER.info_set_findings(fewer, accepted), [('missing_info_row', 'interference', 'eyepiece/panel')])
        import steps
        opened = {m for m, s in steps.MOTIONS.items() if s['runner'] == 'open'}
        self.assertEqual(ER.expected_main_info() - set(ER.MAIN_AUDIT_INFO), {('motion_coverage', m) for m in opened} | set(__import__('j7_collar_checks').INFO_ROWS))  # FP-08 rows (registered in expected_main_info)

    def test_print_failures_must_equal_the_accepted_set(self):
        p = json.loads((SEL / 'print-checks.json').read_text(encoding='utf-8'))
        # FX: the FX refresh passes every print check (EXPECTED_PRINT_FAILURES stays empty, reviewed as this sentinel
        # asked); the rule is now exercised with a planted failing row instead of the live report
        planted = dict(p, failing=dict(p['failing'], bed_chamfer=['planted_part']))
        self.assertTrue(ER.print_failure_findings(planted))
        self.assertEqual(ER.EXPECTED_PRINT_FAILURES, {} if isinstance(ER.EXPECTED_PRINT_FAILURES, dict) else type(ER.EXPECTED_PRINT_FAILURES)())
        clean = dict(p, failing={k: [] for k in p['failing']})
        self.assertEqual(ER.print_failure_findings(clean), [])

    def test_keepout_rule_accepts_only_the_mating_partner(self):
        kinds = {'usb_storage_plug_reserve': 'keepout', 'pi5': 'cots', 'usb_stick': 'cots', 'cooler': 'cots', 'tub': 'printed', 'other_keepout': 'keepout'}
        self.assertTrue(ER.keepout_mating_info('pi5', 'usb_storage_plug_reserve', kinds))
        self.assertTrue(ER.keepout_mating_info('usb_storage_plug_reserve', 'usb_stick', kinds))
        for other in ('cooler', 'tub', 'other_keepout'):
            self.assertFalse(ER.keepout_mating_info(other, 'usb_storage_plug_reserve', kinds), other)
        self.assertFalse(ER.keepout_mating_info('other_keepout', 'pi5', kinds))
        src = (CV / 'verify_candidate.py').read_text(encoding='utf-8')
        self.assertIn('EVR.keepout_mating_info(na,nb,', src)
        self.assertNotIn("(ra['kind']=='keepout' or rb['kind']=='keepout')", src)
        m = json.loads((SEL / 'manifest.json').read_text(encoding='utf-8'))
        k = {r['id']: r['kind'] for r in m['rows']}
        v = json.loads((SEL / 'verification.json').read_text(encoding='utf-8'))
        for c in v['checks']:
            if c['category'] == 'non_material_keepout':
                self.assertTrue(ER.keepout_mating_info(*c['id'].split('/'), k), c['id'])


class TestStaleReportsMoved(unittest.TestCase):
    def test_index_and_paths(self):
        h = CV / 'history/stale-selected-reports-2026-10-10'
        index = json.loads((h / 'INDEX.json').read_text(encoding='utf-8'))
        selected = FX.sha(SEL / 'manifest.json')
        self.assertEqual(index['selected_manifest_sha256'], selected)
        self.assertEqual({x['to'] for x in index['moved']}, {'history/stale-selected-reports-2026-10-10/csi-access-checks.json',
                                                             'history/stale-selected-reports-2026-10-10/ventilation-checks.json'})
        for x in index['moved']:
            self.assertFalse((CV / x['from']).exists(), x['from'])
            self.assertEqual(FX.sha(CV / x['to']), x['sha256'])
            self.assertNotEqual(ER.bound_manifest(json.loads((CV / x['to']).read_text(encoding='utf-8'))), selected)
        paths = json.loads((CV / 'delivery-core-paths.json').read_text(encoding='utf-8'))
        self.assertNotIn('cad/gs8-d2-v1/candidate-vertical/out/compact-kowa_lm6hc/csi-access-checks.json', paths)
        self.assertIn('cad/gs8-d2-v1/candidate-vertical/history/stale-selected-reports-2026-10-10/csi-access-checks.json', paths)
        for rel in ER.DECLARED_HISTORICAL:
            self.assertEqual(ER.historical_binding(rel, CV)[0], True, rel)

    def test_inspection_modes_are_declared(self):
        for name in ('review_docs_audit.py', 'reconcile_review_evidence.py'):
            tree = ast.parse((CV / name).read_text(encoding='utf-8'))
            flags = {a.value for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, 'attr', '') == 'add_argument'
                     for a in n.args if isinstance(a, ast.Constant)}
            self.assertTrue({'--check', '--out', '--write'} <= flags, name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
