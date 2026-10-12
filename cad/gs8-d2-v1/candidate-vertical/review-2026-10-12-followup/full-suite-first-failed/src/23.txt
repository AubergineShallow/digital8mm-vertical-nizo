# SPDX-License-Identifier: MIT
"""Numbers, tolerances and mesh bindings in the evidence tooling (review 2026-10-10 FP-04: VN-06, VN-08, VN-32).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_evidence_numbers.py

VN-06: the structural refresh compares manifest rows with a stated tolerance: a 1.4e-13 relative perturbation (the
size seen after a rebuild) passes, a 1e-3 change fails, strings/bools stay exact; end to end in a copy of the tree.
VN-08: no generated or checked document repeats a cooler witness, rigid-power query count or inherited-gate count
that differs from its source row; the generators hold no typed copy of those figures (the 9ced753 versions did).
VN-32: each print-mesh row carries its binding result and the expected hash; a byte-flipped STL fails on the binding
alone. CAD-free.
"""
from pathlib import Path
import ast
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import _evidence_fixture as FX  # noqa: E402
import evidence_rules as ER  # noqa: E402

CV = FX.CV
SEL = CV / 'out/compact-kowa_lm6hc'
GENERATORS = ['reconcile_review_evidence.py', 'make_bom_vertical.py', 'verify_candidate.py',
              'structural-review/update_concealed_vent_structure.py', 'official_pi5_geometry.py',
              # fixup-1 (VN-08): the manifest, Pi receipt, USB-head, guide, guide-packager and structural-PDF generators
              'model.py', 'official_pi5_assembly.py', 'verify_shadow_usb_head.py', 'guide/build_guide_concealed_vents.py',
              'guide/build_guide_vertical.py', 'guide/package_concealed_guide.py', 'guide/package_guide.py',
              'structural-review/build_shadow_structural_pdf.py']
TYPED = [re.compile(r'\d+\.\d{4,}\s*mm(?:3|³)'), re.compile(r'\d+\s*(?:poses\s*/\s*)?\d*\s*queries'),
         re.compile(r'(?i)(?:\b|all)\d+\s*inherited'), re.compile(r'open_inherited_gates\s*=\s*\d'),
         re.compile(r'(?i)\bbaseline\s?\d+\s*and\s*M1')]


def rows(path):
    return {r['id']: r for r in json.loads(Path(path).read_text(encoding='utf-8'))['rows']}


def perturb(value, rel=0.0, add=0.0):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return value * (1 + rel) + add
    if isinstance(value, list):
        return [perturb(v, rel, add) for v in value]
    if isinstance(value, dict):
        return {k: perturb(v, rel, add) for k, v in value.items()}
    return value


def string_constants(src):
    out = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def typed_figures(src):
    hits = [s for s in string_constants(src) for rx in TYPED if rx.search(s)]
    hits += [m.group(0) for m in TYPED[3].finditer(src)]
    return hits


# FX (verifier C1 minor): the expected set is pinned here, not read from the guard constant it tests, so a later
# widening of the guard cannot loosen this test silently. Upper-body rows: FP-11c carrier, C2 lens_collar / s_c4, FX
# eyecup; the J4 lower row base_grip changes only through the new free body (ALLOWED_CHANGED_LOWER_ROWS).
EXPECTED_ALLOWED_UPPER = ('tub', 'panel', 'carrier', 'lens_collar', 's_c4', 'eyecup')
EXPECTED_ALLOWED_LOWER = ('base_grip',)


def structural_allowed():
    """The pinned allowed set; asserts the script's ALLOWED_CHANGED_ROWS / ALLOWED_CHANGED_LOWER_ROWS equal it."""
    src = (CV / 'structural-review/update_concealed_vent_structure.py').read_text(encoding='utf-8')
    upper = ast.literal_eval(re.search(r'^ALLOWED_CHANGED_ROWS=(\(.*?\))$', src, re.M).group(1))
    lower = ast.literal_eval(re.search(r'^ALLOWED_CHANGED_LOWER_ROWS=(\(.*?\))$', src, re.M).group(1))
    if tuple(upper) != EXPECTED_ALLOWED_UPPER or tuple(lower) != EXPECTED_ALLOWED_LOWER:
        raise AssertionError('structural allowed rows changed: %s / %s' % (upper, lower))
    return EXPECTED_ALLOWED_UPPER + EXPECTED_ALLOWED_LOWER


class TestNumericTolerance(unittest.TestCase):
    def setUp(self):
        self.old = rows(CV / 'history/reviewed-export18/manifest.json')
        self.new = rows(SEL / 'manifest.json')

    def test_1e13_passes_1e3_fails_strings_exact(self):
        # FP-11c: the carrier row changed by design (VN-54/56/38), so the rows that differ from export18 are no longer
        # just tub and panel; they must stay inside the structural transfer's allowed set, and jitter must add none.
        changed = ER.changed_rows(self.old, self.new)
        self.assertTrue({'tub', 'panel'} <= set(changed) <= set(structural_allowed()), changed)
        jitter = {k: perturb(r, rel=1.4e-13) for k, r in self.new.items()}
        self.assertEqual(ER.changed_rows(self.old, jitter), changed)
        self.assertEqual(ER.changed_rows(self.new, jitter), [])
        exact = [k for k in self.new if self.new[k] != jitter[k]]
        self.assertGreater(len(exact), 2, 'negative control: exact equality flags the jittered rows (VN-06)')
        for field, change in [('volume_mm3', lambda v: v + 1e-3), ('bbox_mm', lambda b: b[:1] + [b[1] + 1e-3] + b[2:]),
                              ('mass_est_g', lambda v: v + 1e-3), ('valid', lambda v: not v), ('source', lambda s: s + ' '),
                              ('kind', lambda s: 'printed')]:
            moved = copy.deepcopy(self.new)
            moved['pi5'][field] = change(moved['pi5'][field])
            self.assertEqual(ER.changed_rows(self.new, moved), ['pi5'], field)
        self.assertFalse(ER.same_value(None, 0))
        self.assertFalse(ER.same_value(True, 1))
        self.assertTrue(ER.same_value(0, 0.0))

    def test_structural_refresh_end_to_end(self):
        tmp = tempfile.TemporaryDirectory(prefix='fp04-struct-')
        try:
            cv = FX.build(tmp.name)
            script = cv / 'structural-review/update_concealed_vent_structure.py'
            mp = cv / 'out/compact-kowa_lm6hc/manifest.json'
            pristine = mp.read_text(encoding='utf-8')
            m = json.loads(pristine)
            truth = ER.changed_rows(rows(cv / 'history/reviewed-export18/manifest.json'), {r['id']: r for r in m['rows']})
            m['rows'] = [r if r['id'] in ('tub', 'panel') else perturb(r, rel=1.4e-13) for r in m['rows']]
            mp.write_text(json.dumps(m, indent=2), encoding='utf-8', newline='\n')
            rc, so, se = FX.run(script)
            self.assertEqual(rc, 0, se[-1500:])
            out = json.loads((cv / 'structural-review/concealed-vent-structural.json').read_text(encoding='utf-8'))
            self.assertEqual(out['changed_manifest_rows'], truth)          # jitter adds no row (FP-11c: carrier, tub, panel)
            self.assertTrue({'tub', 'panel'} <= set(truth))
            m = json.loads(pristine)
            next(r for r in m['rows'] if r['id'] == 'pi5')['volume_mm3'] += 1e-3
            mp.write_text(json.dumps(m, indent=2), encoding='utf-8', newline='\n')
            rc, so, se = FX.run(script)
            self.assertNotEqual(rc, 0)
            self.assertIn('Unexpected changed components', se)
            self.assertIn("'pi5'", se)
        finally:
            tmp.cleanup()

    def test_structural_script_uses_the_rule(self):
        src = (CV / 'structural-review/update_concealed_vent_structure.py').read_text(encoding='utf-8')
        self.assertIn('ER.changed_rows(a,b)', src)
        self.assertNotIn('a[k]!=b[k]', src)
        j = json.loads((CV / 'structural-review/concealed-vent-structural.json').read_text(encoding='utf-8'))
        self.assertEqual(j['row_comparison']['numeric_abs_tol'], ER.ABS_TOL)
        self.assertEqual(j['row_comparison']['numeric_rel_tol'], ER.REL_TOL)


class TestGeneratedNumbers(unittest.TestCase):
    def test_documents_match_their_source_rows(self):
        found = ER.documents_number_findings(CV)
        self.assertEqual([f for f in found if not f[1].endswith('/manifest.json')], [])
        # EXPECTED until the next export (FP-16): the frozen 53e668d4-era manifests still carry the typed
        # 'Retain32.3614mm3 CSI/coarse-cooler' provenance text; its source string no longer has a figure.
        for f in found:
            self.assertEqual((f[0], f[2]), ('cooler_witness_number', '32.3614'), f)
        self.assertNotIn('32.3614', (CV / 'official_pi5_geometry.py').read_text(encoding='utf-8'))

    def test_generator_outputs_match_their_source_rows(self):
        sys.argv = [sys.argv[0]]
        import make_bom_vertical as B
        r, _, base = B.build_rows()
        src = ER.number_sources(CV)
        for name, text in B.outputs(r, base).items():
            self.assertEqual(ER.document_number_findings(name, text, src), [], name)
        sys.path.insert(0, str(CV / 'structural-review'))
        import update_concealed_vent_structure as U
        d, text = U.make()
        self.assertEqual(ER.document_number_findings('structural', text + json.dumps(d), src), [])
        self.assertEqual(d['inherited_gates']['open'], src['gates']['open'])
        import reconcile_review_evidence as R
        _, result = R.reconcile(CV)
        self.assertEqual(result['open_inherited_gates'], src['gates']['open'])
        self.assertIn('%s mm3' % src['current']['cooler_witness_text'], result['prominent_holds'][1])
        self.assertEqual(ER.document_number_findings('reconciler', json.dumps(result, indent=2), src), [])

    def test_wrong_figures_are_caught(self):
        src = ER.number_sources(CV)
        text = ('Active cooler/source-Pi witness 79.902672 mm3 remains.\n- rigid power 201 poses / 625 queries / 0 hits.\n'
                'All 55 inherited physical gates and M1 remain open.\n"open_inherited_gates": 57\n')
        got = sorted(f[0] for f in ER.document_number_findings('t', text, src))
        self.assertEqual(got, ['cooler_witness_number', 'inherited_gate_number', 'inherited_gate_number', 'power_query_number'])
        self.assertEqual(src['gates']['open'], sum(v.startswith('open') for v in json.loads(
            (FX.CAD / 'out/build-receipt.json').read_text(encoding='utf-8'))['hardware_gates']['gates'].values()))

    def test_generators_hold_no_typed_figures(self):
        for rel in GENERATORS:
            self.assertEqual(typed_figures((CV / rel).read_text(encoding='utf-8')), [], rel)
        old = {}
        for rel in GENERATORS:
            r = subprocess.run(['git', 'show', '9ced753:cad/gs8-d2-v1/candidate-vertical/' + rel], cwd=str(CV), stdout=subprocess.PIPE)
            if r.returncode == 0:
                old[rel] = typed_figures(r.stdout.decode('utf-8'))
        self.assertTrue(all(old[k] for k in GENERATORS), 'negative control: the 9ced753 generators typed these figures: %s' % old)


class TestMeshBindingFields(unittest.TestCase):
    def test_rows_carry_binding_and_a_flipped_stl_fails_on_binding_alone(self):
        tmp = tempfile.TemporaryDirectory(prefix='fp04-mesh-')
        try:
            root = Path(tmp.name)
            for n in ('verify_print_meshes.py', 'cv_io.py'):
                shutil.copy2(CV / n, root / n)
            d = root / 'out/compact-kowa_lm6hc'
            shutil.copytree(SEL / 'stl', d / 'stl')
            shutil.copy2(SEL / 'manifest.json', d / 'manifest.json')
            m = json.loads((d / 'manifest.json').read_text(encoding='utf-8'))
            rc, so, se = FX.run(root / 'verify_print_meshes.py', '--out', root / 'a.json')
            a = json.loads((root / 'a.json').read_text(encoding='utf-8'))
            self.assertEqual((rc, a['fail_count']), (0, 0), se[-800:])
            for r in a['rows']:
                self.assertTrue(r['manifest_file_binding'])
                self.assertEqual(r['expected_sha256'], m['files']['stl/%s.stl' % r['id']])
                self.assertEqual(r['sha256'], r['expected_sha256'])
            self.assertFalse((d / 'print-mesh-checks.json').exists(), '--out must not write the default report')
            stl = d / 'stl/cap.stl'
            data = bytearray(stl.read_bytes())
            data[84 + 48] ^= 0x01          # attribute byte of the first facet: geometry unchanged, bytes changed
            stl.write_bytes(bytes(data))
            rc, so, se = FX.run(root / 'verify_print_meshes.py', '--out', root / 'b.json')
            b = {r['id']: r for r in json.loads((root / 'b.json').read_text(encoding='utf-8'))['rows']}
            self.assertEqual(rc, 1)
            cap = b['cap']
            self.assertEqual((cap['status'], cap['manifest_file_binding'], cap['watertight'], cap['fits_250x210x220']), ('fail', False, True, True))
            self.assertNotEqual(cap['sha256'], cap['expected_sha256'])
        finally:
            tmp.cleanup()


if __name__ == '__main__':
    unittest.main(verbosity=2)
