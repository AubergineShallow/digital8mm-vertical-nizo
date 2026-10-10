# SPDX-License-Identifier: MIT
"""Deterministic export and bound-cache tests (review VN-04 / VN-17, fix FP-03).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_deterministic_export.py

CAD-free part: the STEP header normaliser, the tracked/cache classification of every binding, the reconciler
gate, the agreement of the cache rule with .gitignore, and a lint that keeps wall-clock times and un-normalised
STEP writes out of the exporters. CAD part (small solids, about a minute): two exports in separate processes are
byte-identical (STEP, assembly STEP, STL, mesh JSON), a raw export pair is not (negative control), and a
fixture variant's deleted mesh cache is rebuilt byte-for-byte from its bound STEP.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import shutil
import subprocess
import re
import sys
import tempfile
import textwrap
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CV), str(Path(__file__).resolve().parent)]
import export_cache as EC  # noqa: E402
from _repo_git import CV as CV_REL, git, zsplit  # noqa: E402

VARIANTS = EC.VARIANTS
HEADER = (b"ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Open CASCADE Model'),'2;1');\n"
          b"FILE_NAME('Open CASCADE Shape Model','2026-10-09T22:57:35',('Author'),(\n    'Open CASCADE'),"
          b"'Open CASCADE STEP processor 7.8','Open CASCADE 7.8'\n  ,'Unknown');\nFILE_SCHEMA(('X'));\nENDSEC;\n")
DATA = b"DATA;\n#1 = PRODUCT('FILE_NAME(''a'',''2026-01-01T00:00:00'')','x','',(#2));\nENDSEC;\nEND-ISO-10303-21;\n"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def env():
    e = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    e.pop('PYTHONHASHSEED', None)
    return e


class StepHeader(unittest.TestCase):
    def test_only_header_time_changes_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.step'
            p.write_bytes(HEADER + DATA)
            self.assertEqual(EC.normalize_step_header(p), '2026-10-09T22:57:35')
            out = p.read_bytes()
            self.assertEqual(out, HEADER.replace(b'2026-10-09T22:57:35', EC.STEP_STAMP.encode()) + DATA)
            self.assertIn(b"''2026-01-01T00:00:00''", out)          # a DATA string is never touched
            self.assertEqual(EC.normalize_step_header(p), EC.STEP_STAMP)
            self.assertEqual(p.read_bytes(), out)

    def test_escaped_quote_in_name(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.step'
            p.write_bytes(HEADER.replace(b"'Open CASCADE Shape Model'", b"'it''s a model'") + DATA)
            self.assertEqual(EC.normalize_step_header(p), '2026-10-09T22:57:35')
            self.assertIn(b"'it''s a model','%s'" % EC.STEP_STAMP.encode(), p.read_bytes())

    def test_rejects_non_step(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.step'
            p.write_bytes(b'solid x\nendsolid\n')
            self.assertRaises(ValueError, EC.normalize_step_header, p)

    def test_committed_occt_header_is_recognised(self):
        # The supplied STEP files carry OCCT 7.8 wall-clock stamps; the normaliser must find exactly that field.
        src = CV / 'out/compact-kowa_lm6hc/step/tub.step'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'tub.step'
            shutil.copyfile(src, p)
            raw = src.read_bytes()
            old = EC.normalize_step_header(p)
            self.assertRegex(old, r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$')
            new = p.read_bytes()
            self.assertEqual(len(new), len(raw))
            diff = [i for i in range(2048) if new[i] != raw[i]]
            self.assertTrue(diff and len(diff) <= 19, diff)
            self.assertEqual(new[2048:], raw[2048:])


GEOM = "#1 = CARTESIAN_POINT('',(0.,0.,0.));\n#2 = CARTESIAN_POINT('',(1.,0.,0.));\n#3 = CONTEXT_A(3);\n#4 = CONTEXT_B(3);\n"
SILVER = ('COLOUR_RGB', "'',0.6,0.6,0.58", [])
BLACK = ('COLOUR_RGB', "'',0.03,0.03,0.03", [])


def styled(target, colour):
    node = ('FILL_AREA_STYLE_COLOUR', "'',{0}", [colour])
    for kind, fmt in (('FILL_AREA_STYLE', "'',({0})"), ('SURFACE_STYLE_FILL_AREA', '{0}'), ('SURFACE_SIDE_STYLE', "'',({0})"),
                      ('SURFACE_STYLE_USAGE', '.BOTH.,{0}'), ('PRESENTATION_STYLE_ASSIGNMENT', '({0})')):
        node = (kind, fmt, [node])
    return ('STYLED_ITEM', "'color',({0}),#%d" % target, [node])


def mdgpr(ctx, items):
    return ('MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION',
            "'',(" + ','.join('{%d}' % k for k in range(len(items))) + "),#%d" % ctx, items)


def emit(roots, start=5):
    """OCCT-like pre-order colour section: parents first, shared colours written once."""
    ids, order = {}, []

    def visit(n):
        if id(n) not in ids:
            ids[id(n)] = start + len(order)
            order.append(n)
            for c in n[2]:
                visit(c)
    for r in roots:
        visit(r)
    return ''.join('#%d = %s(%s);\n' % (ids[id(n)], n[0], n[1].format(*['#%d' % ids[id(c)] for c in n[2]])) for n in order)


def step_file(geom, tail):
    return (HEADER + b'DATA;\n' + (geom + tail).encode() + b'ENDSEC;\nEND-ISO-10303-21;\n')


class StepColourSection(unittest.TestCase):
    """OCCT orders the assembly colour section by memory address; the canonical form must not depend on it."""

    def canon(self, data):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'a.step'
            p.write_bytes(data)
            n = EC.canonicalize_step_styles(p)
            return n, p.read_bytes()

    def test_permuted_sections_give_identical_bytes(self):
        a, b = styled(1, SILVER), styled(2, BLACK)
        one = step_file(GEOM, emit([mdgpr(3, [a, b]), mdgpr(4, [styled(1, BLACK)])]))
        a2, b2 = styled(1, SILVER), styled(2, BLACK)
        two = step_file(GEOM, emit([mdgpr(4, [styled(1, BLACK)]), mdgpr(3, [b2, a2])]))
        self.assertNotEqual(one, two)
        n1, c1 = self.canon(one)
        n2, c2 = self.canon(two)
        self.assertEqual((n1, n2), (25, 25))           # 2 MDGPR + 3 styled items x 7 entities + 2 shared colours
        self.assertEqual(c1, c2)
        self.assertTrue(c1.startswith(HEADER + b'DATA;\n' + GEOM.encode()))   # geometry untouched
        self.assertEqual(self.canon(c1)[1], c1)                                 # idempotent

    def test_line_wrapping_is_ignored(self):
        tail = emit([mdgpr(3, [styled(1, SILVER), styled(2, BLACK)])])
        wrapped = tail.replace("'',(#6,", "'',(\n    #6,").replace('),#3);', ')\n  ,#3);')
        self.assertNotEqual(tail, wrapped)
        self.assertEqual(self.canon(step_file(GEOM, tail))[1], self.canon(step_file(GEOM, wrapped))[1])

    def test_refuses_unsafe_rewrites(self):
        tail = emit([mdgpr(3, [styled(1, SILVER)])])
        with self.assertRaises(ValueError):                     # a non-style record inside the section
            self.canon(step_file(GEOM, tail + "#99 = CARTESIAN_POINT('',(2.,0.,0.));\n"))
        with self.assertRaises(ValueError):                     # geometry referencing the section
            self.canon(step_file(GEOM.replace('CONTEXT_B(3)', 'CONTEXT_B(#5)'), tail))
        n, out = self.canon(step_file(GEOM, ''))                # no colour section: untouched
        self.assertEqual((n, out), (0, step_file(GEOM, '')))


def fixture(root, determinism=True):
    """A tiny CAD-free variant folder: bound STEP, STL and mesh files plus its manifest."""
    d = Path(root) / 'fixture-variant'
    for n in ('step', 'stl', 'meshes'):
        (d / n).mkdir(parents=True)
    (d / 'step/a.step').write_bytes(HEADER + DATA)
    (d / 'stl/a.stl').write_bytes(b'\0' * 84)
    (d / 'meshes/a.json').write_bytes(b'{"id":"a"}')
    (d / 'assembly.step').write_bytes(HEADER + DATA)
    files = {r: sha((d / r).read_bytes()) for r in ('step/a.step', 'stl/a.stl', 'meshes/a.json', 'assembly.step')}
    m = {'rows': [{'id': 'a', 'kind': 'printed', 'mesh': 'a.json'}], 'files': files, 'runtime': EC.runtime()}
    if determinism:
        m['determinism'] = EC.POLICY
    raw = json.dumps(m, indent=2)
    (d / 'manifest.json').write_text(raw, encoding='utf-8', newline='\n')
    (d / 'meshes/manifest.json').write_text(raw, encoding='utf-8', newline='\n')
    return d


class BindingStatus(unittest.TestCase):
    def test_complete_then_cache_missing_then_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            d = fixture(t)
            r = EC.variant_report(d)
            self.assertEqual((r['state'], r['cache']['checked'], r['tracked']['checked']), ('complete', 1, 3))
            EC.require_files(json.loads((d / 'manifest.json').read_text(encoding='utf-8'))['files'], d)
            (d / 'meshes/a.json').unlink()
            r = EC.variant_report(d)
            self.assertEqual((r['state'], r['cache']['missing']), ('cache_missing', ['meshes/a.json']))
            self.assertIn('export_cache.py regenerate --variant fixture-variant', r['action'])
            with self.assertRaises(AssertionError) as e:
                EC.require_files(json.loads((d / 'manifest.json').read_text(encoding='utf-8'))['files'], d)
            self.assertEqual(e.exception.args[:2], ('Bound cache missing', 1))
            self.assertIn('regenerate --variant fixture-variant', e.exception.args[2])
            (d / 'stl/a.stl').write_bytes(b'\1' * 84)                       # a tracked file changes
            self.assertEqual(EC.variant_report(d)['state'], 'mismatch')
            with self.assertRaises(AssertionError) as e:
                EC.require_files(json.loads((d / 'manifest.json').read_text(encoding='utf-8'))['files'], d)
            self.assertEqual(e.exception.args[:2], ('Export mismatch', 'stl/a.stl'))

    def test_tampered_cache_and_missing_tracked_file_fail(self):
        with tempfile.TemporaryDirectory() as t:
            d = fixture(t)
            files = json.loads((d / 'manifest.json').read_text(encoding='utf-8'))['files']
            (d / 'meshes/a.json').write_bytes(b'{"id":"b"}')
            self.assertEqual(EC.variant_report(d)['state'], 'mismatch')
            self.assertRaises(AssertionError, EC.require_files, files, d)
            (d / 'meshes/a.json').unlink()
            (d / 'assembly.step').unlink()
            with self.assertRaises(AssertionError) as e:
                EC.require_files(files, d)
            self.assertEqual(e.exception.args[:2], ('Export mismatch', 'assembly.step'))

    def test_legacy_manifest_is_not_called_regenerable(self):
        with tempfile.TemporaryDirectory() as t:
            d = fixture(t, determinism=False)
            (d / 'meshes/a.json').unlink()
            r = EC.variant_report(d)
            self.assertEqual(r['state'], 'cache_missing_unregenerable')
            self.assertIn('predates FP-03', r['action'])
            with self.assertRaises(AssertionError) as e:
                EC.require_files(json.loads((d / 'manifest.json').read_text(encoding='utf-8'))['files'], d)
            self.assertIn('predates FP-03', e.exception.args[2])
            self.assertRaises(ValueError, EC.regenerate_variant, d)

    def test_docs_audit_summary_agrees_with_report(self):
        with tempfile.TemporaryDirectory() as t:
            d = fixture(t)
            (d / 'meshes/a.json').unlink()
            m = json.loads((d / 'manifest.json').read_text(encoding='utf-8'))
            s = EC.summarize_bindings({'missing': ['meshes/a.json'], 'changed': []}, m, d.name)
            self.assertEqual((s['state'], s['cache']['bound'], s['cache']['missing']), ('cache_missing', 1, ['meshes/a.json']))
            s = EC.summarize_bindings({'missing': ['meshes/a.json', 'stl/a.stl'], 'changed': []}, m, d.name)
            self.assertEqual((s['state'], s['tracked']['missing']), ('mismatch', ['stl/a.stl']))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            d = fixture(t)
            run = lambda: subprocess.run([sys.executable, str(CV / 'export_cache.py'), 'status', '--no-guide',
                                          '--variant', str(d)], env=env(), capture_output=True).returncode
            self.assertEqual(run(), 0)
            (d / 'meshes/a.json').unlink()
            self.assertEqual(run(), 3)
            (d / 'stl/a.stl').unlink()
            self.assertEqual(run(), 1)


class RepositoryBindings(unittest.TestCase):
    """VN-04: every bound file is either tracked by git or a declared, git-ignored regenerable cache."""

    def bound(self):
        rows = []
        for v in VARIANTS:
            m = json.loads((CV / 'out' / v / 'manifest.json').read_text(encoding='utf-8'))
            rows += [('out/%s/%s' % (v, rel), EC.is_mesh_cache(rel)) for rel in m['files']]
        rec = json.loads((CV / EC.GUIDE_RECEIPT).read_text(encoding='utf-8'))
        rows += [('out/%s/%s' % (EC.GUIDE_VARIANT, rel), EC.is_mesh_cache(rel)) for rel in rec['mesh_files']]
        rows += [('%s/%s' % (EC.GUIDE_DIR, rel), EC.is_page_cache(rel)) for rel in rec['page_images']]
        rows += [('%s/%s' % (EC.GUIDE_DIR, rec['guide_pdf_filename']), False)]
        return rows

    def test_cache_rule_matches_gitignore_and_rest_is_tracked(self):
        rows = self.bound()
        self.assertGreater(len(rows), 300)
        paths = [CV_REL + p for p, _ in rows]
        ignored = set(zsplit(git('check-ignore', '-z', '--no-index', '--stdin', input='\0'.join(paths).encode(), check=False)))
        tracked = set(zsplit(git('ls-files', '-z', '--', CV_REL)))
        bad = [(p, c) for (p, c), full in zip(rows, paths) if c != (full in ignored) or (not c and full not in tracked)]
        self.assertEqual(bad, [], bad[:10])
        rec = json.loads((CV / EC.GUIDE_RECEIPT).read_text(encoding='utf-8'))
        self.assertEqual(sum(EC.is_page_cache(r) for r in rec['page_images']), rec['page_count'])
        for v in VARIANTS:     # every variant binds a mesh cache for each manifest row
            m = json.loads((CV / 'out' / v / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(sum(map(EC.is_mesh_cache, m['files'])), len(m['rows']), v)

    def test_live_tracked_bindings_hold(self):
        # Tracked STEP/STL/assembly bindings must match on any checkout; only declared caches may be absent.
        for v in VARIANTS:
            r = EC.variant_report(CV / 'out' / v)
            self.assertEqual((r['tracked']['missing'], r['tracked']['changed'], r['cache']['changed']), ([], [], []), v)
            self.assertIn(r['state'], ('complete', 'cache_missing', 'cache_missing_unregenerable'), v)
        g = EC.guide_report(CV)
        self.assertTrue(g['pdf_match'])
        self.assertEqual(g['unexpected_tracked'], 0)


def calls(rel):
    tree = ast.parse((CV / rel).read_text(encoding='utf-8'))
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)]


class ExporterLint(unittest.TestCase):
    CLOCK = {'time.strftime', 'time.gmtime', 'time.time', 'time.localtime', 'datetime.datetime.now',
             'datetime.datetime.utcnow', 'datetime.now', 'datetime.date.today'}

    def test_no_wall_clock_in_deterministic_outputs(self):
        for rel in ('export_candidate.py', 'make_corrected_pi.py', 'export_cache.py', 'guide/build_guide_concealed_vents.py',
                    'make_shadow_plenum_coupon.py'):
            used = sorted({ast.unparse(c.func) for c in calls(rel)} & self.CLOCK)
            self.assertEqual(used, [], rel)

    # fixup-1 (VN-17): every live script that writes a STEP file goes through export_cache.export_step/save_assembly,
    # or is listed here with the reason its raw OCCT header (wall-clock time) is acceptable. REPRODUCE.md names them.
    NORMALISED = ('export_candidate.py', 'make_corrected_pi.py', 'make_shadow_plenum_coupon.py', 'verify_fps_contact_pad.py',
                  'verify_fps_pair_guide.py')
    RAW_STEP_WRITERS = {
        'export_cache.py': 'the normaliser itself: export_step and save_assembly rewrite the header after OCCT writes it',
        'probe_carrier_reinforcement.py': 'exploratory structural proposal; its STEP is bound only in the frozen routing snapshot '
                                          'hdmi-ck1044-clear-20261009-0524 (historical, never regenerated)',
        'probe_corrected_fps.py': 'exploratory probe; no live receipt binds its STEP output',
        'probe_power_boolean.py': 'exploratory probe writing to /tmp only',
        'probe_power_boolean2.py': 'exploratory probe writing to /tmp only',
        'probe_power_fit.py': 'exploratory probe; no live receipt binds its STEP outputs',
        'probe_structure_additions.py': 'exploratory structural proposal; no live receipt binds its STEP output',
        'study_fps_fixed_switch.py': 'rejected FPS study proposal; no live receipt binds its STEP outputs',
        'study_fps_saddle.py': 'FPS study proposal; no live receipt binds its STEP output',
        'study_pi_cooler_union.py': 'bounded cooler-union diagnosis; its STEP shas sit in its own diagnostic record only',
        'structural-review/make_coupons.py': 'retained structural-review coupon reproducer (historical input-baseline/j4-trial '
                                             'sources); its coupon-manifest is a frozen record',
        'verify_fps_central_rest.py': 'FPS study verifier; no live receipt binds central-rest.step',
        'verify_fps_central_rest_wide.py': 'FPS study verifier; no live receipt binds central-rest-wide.step',
        'verify_fps_fixed_service.py': 'FPS study verifier; no live receipt binds its two STEP outputs',
        'verify_fps_pair_deployment.py': 'FPS study verifier; no live receipt binds picoblade-rear-rest.step',
        'vent-study/angled-channel-trial/export_candidate.py': 'rejected angled-channel trial copy of the exporter (historical)',
    }

    def test_every_live_step_writer_is_normalised_or_listed(self):
        found = {}
        for p in sorted(CV.rglob('*.py')):
            rel = p.relative_to(CV).as_posix()
            if rel.split('/')[0] in ('routing-snapshots', 'history', 'tests', 'out', '__pycache__'):
                continue
            for c in calls(rel):
                f = ast.unparse(c.func)
                arg = ast.unparse(c.args[1]) if len(c.args) > 1 else ''
                stl = 'stl' in arg.lower() or any(k.arg in ('tolerance', 'angularTolerance') for k in c.keywords)
                if ((f.endswith('exporters.export') and not stl) or 'STEPControl_Writer' in f
                        or (f.endswith('.save') and ('asm' in f.lower() or 'assembly' in f.lower()))):
                    found.setdefault(rel, []).append(c.lineno)
        self.assertEqual(sorted(set(found) - set(self.RAW_STEP_WRITERS)), [], found)
        self.assertEqual(sorted(set(self.RAW_STEP_WRITERS) - set(found)), [], 'stale allowlist entry')
        for rel in self.NORMALISED:
            self.assertNotIn(rel, found)
            self.assertIn('EC.export_step(', (CV / rel).read_text(encoding='utf-8'), rel)
        # live receipts bind only normalised STEP outputs (negative check on the allowlisted writers' literal names)
        bound = set(re.findall(r'([\w.-]+\.step)"', (CV / 'out/fps-service-study/fps-final-source-receipt.json').read_text(encoding='utf-8')))
        self.assertTrue({'central-rest-pad.step', 'picoblade-open-guide.step'} <= bound)
        for rel in self.RAW_STEP_WRITERS:
            names = set(re.findall(r'[\w.-]+\.step', (CV / rel).read_text(encoding='utf-8')))
            self.assertEqual(sorted(names & bound), [], rel)
        text = (CV / 'REPRODUCE.md').read_text(encoding='utf-8')
        self.assertIn('RAW_STEP_WRITERS', text)

    def test_step_writes_go_through_the_normaliser(self):
        for rel in ('export_candidate.py', 'make_corrected_pi.py'):
            for c in calls(rel):
                f = ast.unparse(c.func)
                if f == 'cq.exporters.export':
                    self.assertIn('.stl', ast.unparse(c.args[1]), '%s:%d writes a non-STL file directly' % (rel, c.lineno))
                self.assertFalse(f.endswith('.save') and 'asm' in f, '%s:%d saves the assembly directly' % (rel, c.lineno))
        src = (CV / 'export_candidate.py').read_text(encoding='utf-8')
        for needle in ("'export_cache.py'", 'EC.save_assembly(', 'EC.write_mesh(', "'determinism':EC.POLICY",
                       "'runtime':EC.runtime()", "'built_utc':EC.UNRECORDED", 'sorted(model.ROOT.glob(',
                       "sources=dict(sorted(sources.items()))", "meta['files']=dict(sorted(meta['files'].items()))"):
            self.assertIn(needle, src)
        # bbox_mm comes from Shape.BoundingBox(), which uses a triangulation when present: the in-memory
        # tessellation must still precede manifest.append, or 39 of 45 recorded boxes shrink by up to 0.69 mm.
        self.assertLess(src.index('s.tessellate(*EC.MESH_TOLERANCE)'), src.index('manifest.append('))

    def test_guide_build_is_deterministic(self):
        src = (CV / 'guide/build_guide_concealed_vents.py').read_text(encoding='utf-8')
        for needle in ('invariant=1', "'generated_utc':EC.UNRECORDED", "ROOT/'export_cache.py'", "'sources':dict(sorted("):
            self.assertIn(needle, src)


CHILD = textwrap.dedent('''
    import sys; sys.path.insert(0, sys.argv[1]); from pathlib import Path
    import cadquery as cq, export_cache as EC
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True); raw = sys.argv[3] == 'raw'
    s = cq.Workplane().box(10, 7.6, 5).translate((0, 23.8, 0)).edges('|Z').fillet(1).val()
    if raw:
        cq.exporters.export(s, str(out / 'panel.step'))
    else:
        EC.export_step(s, out / 'panel.step')
        asm = cq.Assembly(name='t'); asm.add(s, name='panel', color=cq.Color(.6, .6, .58))
        for k in range(8):   # several coloured parts, so the colour section has many entries to order
            asm.add(cq.Workplane().box(4, 4, 4).translate((20 + 6 * k, 0, 0)).val(), name='p%d' % k,
                    color=cq.Color(.6, .6, .58) if k % 2 else cq.Color(.03, .03, .03))
        EC.save_assembly(asm, out / 'assembly.step')
        cq.exporters.export(s, str(out / 'panel.stl'), tolerance=.06, angularTolerance=.15)
        EC.write_mesh(out / 'panel.json', 'panel', 'printed', out / 'panel.step')
''')


class CadDeterminism(unittest.TestCase):
    def export(self, out, mode):
        r = subprocess.run([sys.executable, '-c', CHILD, str(CV), str(out), mode], env=env(), capture_output=True, timeout=600)
        self.assertEqual(r.returncode, 0, r.stderr.decode('utf-8', 'replace')[-2000:])

    def test_two_exports_are_byte_identical_and_raw_ones_are_not(self):
        import time
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            self.export(t / 'a', 'det')
            self.export(t / 'raw1', 'raw')
            time.sleep(1.2)                                   # the OCCT stamp has one-second resolution
            self.export(t / 'b', 'det')
            self.export(t / 'raw2', 'raw')
            for name in ('panel.step', 'assembly.step', 'panel.stl', 'panel.json'):
                self.assertEqual((t / 'a' / name).read_bytes(), (t / 'b' / name).read_bytes(), name)
            self.assertIn(b"'%s'" % EC.STEP_STAMP.encode(), (t / 'a/panel.step').read_bytes()[:400])
            self.assertIn(b"'%s'" % EC.STEP_STAMP.encode(), (t / 'a/assembly.step').read_bytes()[:400])
            self.assertNotEqual((t / 'raw1/panel.step').read_bytes(), (t / 'raw2/panel.step').read_bytes(),
                                'negative control: a raw OCCT export pair should differ by its wall-clock stamp')
            import cadquery as cq                              # colours survive the canonical colour section
            got = {n: tuple(round(c, 4) for c in ch.color.toTuple()) for n, ch in
                   cq.Assembly.importStep(str(t / 'a/assembly.step')).traverse() if ch.obj is not None and ch.color}
            want = {'panel': (.6, .6, .58, 1.0), **{'p%d' % k: (.6, .6, .58, 1.0) if k % 2 else (.03, .03, .03, 1.0) for k in range(8)}}
            self.assertEqual(got, want)
            mesh = json.loads((t / 'a/panel.json').read_text(encoding='utf-8'))
            self.assertEqual(len(mesh['materials']), len(mesh['faces']))
            self.assertIn('paint_black', mesh['materials'])     # panel face at y = 27.6 (moved material rule)
            self.assertEqual(set(mesh['materials']), {'silver', 'paint_black'})

    def test_regenerate_rebuilds_a_deleted_cache_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            self.export(t / 'src', 'det')
            d = t / 'variant'
            for n in ('step', 'stl', 'meshes'):
                (d / n).mkdir(parents=True)
            shutil.copyfile(t / 'src/panel.step', d / 'step/panel.step')
            shutil.copyfile(t / 'src/panel.stl', d / 'stl/panel.stl')
            shutil.copyfile(t / 'src/panel.json', d / 'meshes/panel.json')
            shutil.copyfile(t / 'src/assembly.step', d / 'assembly.step')
            files = {r: sha((d / r).read_bytes()) for r in ('step/panel.step', 'stl/panel.stl', 'meshes/panel.json', 'assembly.step')}
            m = {'rows': [{'id': 'panel', 'kind': 'printed', 'mesh': 'panel.json'}], 'files': files,
                 'runtime': EC.runtime(), 'determinism': EC.POLICY}
            (d / 'manifest.json').write_text(json.dumps(m, indent=2), encoding='utf-8', newline='\n')
            shutil.rmtree(d / 'meshes')
            self.assertEqual(EC.variant_report(d)['state'], 'cache_missing')
            self.assertEqual(EC.regenerate_variant(d, log=lambda *a, **k: None), {'meshes/panel.json': 'regenerated'})
            self.assertEqual(EC.variant_report(d)['state'], 'complete')
            self.assertEqual((d / 'meshes/manifest.json').read_bytes(), (d / 'manifest.json').read_bytes())
            # A binding the rebuild cannot meet is never overwritten; the bytes go to meshes/_mismatch/.
            m['files']['meshes/panel.json'] = '0' * 64
            (d / 'manifest.json').write_text(json.dumps(m, indent=2), encoding='utf-8', newline='\n')
            before = (d / 'meshes/panel.json').read_bytes()
            self.assertEqual(EC.regenerate_variant(d, force=True, log=lambda *a, **k: None), {'meshes/panel.json': 'mismatch'})
            self.assertEqual((d / 'meshes/panel.json').read_bytes(), before)
            self.assertTrue((d / 'meshes/_mismatch/panel.json').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
