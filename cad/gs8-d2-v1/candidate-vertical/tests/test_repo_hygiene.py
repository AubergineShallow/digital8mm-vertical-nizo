# SPDX-License-Identifier: MIT
"""Repository hygiene and provenance (review VN-10, VN-11, VN-12, VN-15, VN-18, VN-19, VN-20; fix FP-15).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_repo_hygiene.py

CAD-free (standard library plus the pinned venv's package metadata). Checks:
- VN-10: no live script passes a machine-local absolute path (/tmp, /workspace, C:/Users ...) to a file or process
  call; the usb_head writer records a repo-relative manifest path; recorded path fields are never str(<path>); every
  JSON that still holds an absolute path is declared frozen, non-reproducible or pending FP-16 (planted file caught);
  the selected usb_head report is clean after FP-16 (expected failure until then);
- VN-11 / VN-20: the provenance entries exist; the Pi extraction records bind their native STEPs; the structural
  base JSON's re-derivable fields match the export18 manifest and history STEPs (a tampered copy fails);
- VN-12: every third-party import of the live scripts is declared in requirements-candidate-lock.txt; pinned
  modules match the base lock and the installed versions; optional modules are really absent (else they must be
  pinned); REPRODUCE.md gives the Windows commands;
- VN-15: the repository-wide link check has no failure (live documents 0 broken, frozen copies bannered);
- VN-18 / VN-19: no path longer than the documented limit; REPO-INDEX.md is current and classifies every script;
  the structural-review page PNGs are the images the PDF receipt binds (not stray files).
"""
from pathlib import Path
import ast
import hashlib
import importlib.metadata as md
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CV), str(CV / 'tests'), str(CV / 'structural-review')]
import make_repo_index as RI  # noqa: E402
import check_links_vertical as LK  # noqa: E402
import verify_reference_binding as VRB  # noqa: E402
from test_cross_platform_io import live_scripts  # noqa: E402
from cv_io import write_text  # noqa: E402

FILE_CALLS = {'Path', 'open', 'open_text', 'read_text', 'write_text', 'importStep', 'export', 'run', 'Popen',
              'check_output', 'call', 'save', 'write_bytes', 'read_bytes'}
PATH_KEY = re.compile(r'(^|_)(path|file|log|report|dir|folder)s?$')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def call_name(n):
    f = n.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ''


def machine_path_lint(src):
    """[(line, text)] of absolute machine paths reaching a file or process call."""
    bad = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call) and call_name(n) in FILE_CALLS:
            for a in list(n.args) + [k.value for k in n.keywords]:
                for c in ast.walk(a):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str) and RI.ABS_RE.search(c.value):
                        bad.append((c.lineno, c.value))
    return bad


def recorded_path_lint(src):
    """[(line, key)] where a recorded path field (dict(...) keyword or dict literal key) is str(...).
    Dicts built inside print(...) go to stdout or a git-ignored log, not to recorded evidence, and are skipped."""
    bad = []
    tree = ast.parse(src)
    printed = {id(x) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == 'print' for x in ast.walk(n)}
    for n in ast.walk(tree):
        if id(n) in printed:
            continue
        pairs = []
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'dict':
            pairs = [(k.arg, k.value) for k in n.keywords if k.arg]
        elif isinstance(n, ast.Dict):
            pairs = [(k.value, v) for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        for key, v in pairs:
            if PATH_KEY.search(key) and isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == 'str':
                bad.append((v.lineno, key))
    return bad


class TestAbsolutePaths(unittest.TestCase):
    def test_live_scripts_pass_no_machine_paths(self):
        bad = {rel: machine_path_lint(p.read_text(encoding='utf-8')) for rel, p in live_scripts()}
        self.assertEqual({k: v for k, v in bad.items() if v}, {})

    def test_machine_path_lint_catches_the_fixed_forms(self):
        planted = ("from pathlib import Path\nimport cadquery as cq\npath=Path('/tmp')/'x.step'\n"
                   "s=cq.importers.importStep('/tmp/oldvalid-base_grip.step').val()\n"
                   "with open_text('/tmp/d2-final-'+name+'.log','w') as f:pass\nopen('C:/Users/me/x.json')\n")
        self.assertEqual(len(machine_path_lint(planted)), 4)
        self.assertEqual(machine_path_lint("x='/tmp/is only prose here'\nopen(P/'out/x.log')\n"), [])

    def test_recorded_path_fields_use_helpers(self):
        bad = {rel: recorded_path_lint(p.read_text(encoding='utf-8')) for rel, p in live_scripts()}
        self.assertEqual({k: v for k, v in bad.items() if v}, {})
        self.assertEqual(len(recorded_path_lint("a=dict(manifest_path=str(mp));b={'log':str(p),'n':str(3)}\n")), 2)
        self.assertEqual(recorded_path_lint("print(json.dumps(dict(report=str(p))))\n"), [])

    def test_usb_head_manifest_path_is_relative(self):
        tree = ast.parse((CV / 'verify_shadow_usb_head.py').read_text(encoding='utf-8'))
        vals = [k.value for n in ast.walk(tree) if isinstance(n, ast.Call) for k in n.keywords if k.arg == 'manifest_path']
        self.assertEqual(len(vals), 1)
        self.assertTrue(isinstance(vals[0], ast.Call) and call_name(vals[0]) in ('relpath_posix', 'rel_posix'))

    def test_every_absolute_path_in_json_is_declared(self):
        hits = RI.absolute_paths()
        self.assertEqual([r for r in hits if RI.classify_abs(r) == 'UNDECLARED'], [])
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'out').mkdir()
            planted_text = json.dumps({'log': 'C:\\Users\\someone\\x.log', 'm': '/workspace/a/b'})
            write_text(Path(d) / 'out/planted.json', planted_text)
            planted = RI.absolute_paths(d)
            self.assertEqual(planted, {'out/planted.json': 2})
            self.assertEqual(RI.classify_abs('out/planted.json'), 'UNDECLARED')

    @unittest.expectedFailure
    def test_selected_evidence_holds_no_absolute_path(self):
        # Expected to fail until FP-16 regenerates the selected usb_head report with the fixed writer (VN-10);
        # remove this mark when it passes.
        self.assertEqual([r for r in RI.absolute_paths() if RI.classify_abs(r) == 'pending FP-16'], [])


class TestProvenance(unittest.TestCase):
    SRC = CV / 'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources'

    def test_entries_exist(self):
        self.assertEqual([p for p in RI.problems() if p[0] == 'provenance_missing'], [])

    def test_extraction_records_bind_native_steps(self):
        ext = json.loads((self.SRC / 'connector-extraction.json').read_text(encoding='utf-8'))
        lm = json.loads((self.SRC / 'port-landmarks.json').read_text(encoding='utf-8'))
        seen = set()
        for name, c in ext['components'].items():
            self.assertEqual(sha(self.SRC / (name + '-native.step')), c['source_sha256'], name); seen.add(name)
        for name, o in lm['objects'].items():
            self.assertEqual(sha(self.SRC / (name + '-native.step')), o['sha256'], name); seen.add(name)
        self.assertEqual(seen, {p.name[:-len('-native.step')] for p in self.SRC.glob('*-native.step')})
        self.assertEqual(ext['source_step_sha256'], lm['source_step_sha256'])

    def test_structural_reference_rederives(self):
        rows = VRB.check()
        self.assertEqual([r for r in rows if r['status'] != 'pass'], [])
        self.assertGreaterEqual(len(rows), 20)
        with tempfile.TemporaryDirectory() as d:
            ref = json.loads(VRB.REF.read_text(encoding='utf-8'))
            ref['estimated_mass_g'] += 0.5
            ref['parts']['tub']['sha256'] = '0' * 64
            bad = Path(d) / 'ref.json'
            write_text(bad, json.dumps(ref))
            failed = {r['id'] for r in VRB.check(ref_path=bad) if r['status'] != 'pass'}
            self.assertTrue({'estimated_mass_g', 'parts/tub/sha256', 'parts/tub/history_step_sha256'} <= failed)


LOCK = CV / 'requirements-candidate-lock.txt'
DIST = {'cadquery': 'cadquery', 'OCP': 'cadquery-ocp', 'numpy': 'numpy', 'PIL': 'pillow', 'reportlab': 'reportlab',
        'vtk': 'vtk', 'manifold3d': 'manifold3d'}


def lock_sections():
    text = LOCK.read_text(encoding='utf-8')
    pinned = re.search(r'^# pinned-in-base: (.+)$', text, re.M).group(1).split()
    optional = {m.group(1): m.group(2) for m in re.finditer(r'^# optional: (\S+) \| (.+)$', text, re.M)}
    external = re.search(r'^# external: ([^|]+)\|', text, re.M).group(1).split()
    base = re.search(r'^-r (\S+)$', text, re.M).group(1)
    return pinned, optional, external, (LOCK.parent / base).resolve()


def third_party_imports():
    local = {p.stem for p in CV.rglob('*.py')} | {p.stem for p in CV.parent.glob('*.py')} | {p.stem for p in (CV.parent / 'guide').glob('*.py')}
    out = {}
    for rel, p in live_scripts():
        for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
            names = [a.name.split('.')[0] for a in n.names] if isinstance(n, ast.Import) else \
                [n.module.split('.')[0]] if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module else []
            for m in names:
                if m not in sys.stdlib_module_names and m not in local:
                    out.setdefault(m, set()).add(rel)
    return out


class TestToolchain(unittest.TestCase):
    def test_every_import_is_declared_once(self):
        pinned, optional, external, _ = lock_sections()
        declared = pinned + list(optional) + external
        self.assertEqual(len(declared), len(set(declared)))
        self.assertEqual(sorted(set(third_party_imports()) - set(declared)), [])

    def test_pinned_match_base_lock_and_venv(self):
        pinned, _, _, base = lock_sections()
        pins = dict(l.split('==') for l in base.read_text(encoding='utf-8').splitlines() if '==' in l)
        pins = {k.lower(): v for k, v in pins.items()}
        for m in pinned:
            d = DIST[m]
            self.assertIn(d, pins, m)
            self.assertEqual(md.version(d), pins[d], d)

    def test_optional_modules_are_absent_or_must_be_pinned(self):
        _, optional, _, _ = lock_sections()
        used = third_party_imports()
        for m, users in optional.items():
            self.assertIsNone(importlib.util.find_spec(m), '%s is installed: pin its version in the lock' % m)
            for rel in used.get(m, ()):
                self.assertIn(Path(rel).name, users, (m, rel))

    def test_reproduce_gives_windows_commands(self):
        text = (CV / 'REPRODUCE.md').read_text(encoding='utf-8')
        for frag in ('run_with_numpy_raster.py', 'core.longpaths', '.venv-cad\\Scripts\\python.exe', 'requirements-candidate-lock.txt'):
            self.assertIn(frag, text)


class TestLinksAndIndex(unittest.TestCase):
    def test_link_check_has_no_failure(self):
        r = LK.run()
        self.assertEqual(r['failures'], [])
        self.assertNotIn('live', r['broken_by_class'])

    def test_link_parser_and_banner(self):
        self.assertEqual(list(LK.links('[a](x.md#h) [b](https://e) [c](#top) `[d](no.md)` [e](<sp ace.md>)')), ['x.md', 'sp ace.md'])
        self.assertTrue(LK.bannered('cad/gs8-d2-v1/candidate-vertical/history/reviewed-export18/BOM-VERTICAL.md'))
        self.assertFalse(LK.bannered('cad/gs8-d2-v1/candidate-vertical/history/reviewed-export18/README.md'))

    def test_paths_and_index(self):
        self.assertEqual([p for p in RI.problems() if p[0] in ('path_too_long', 'pipeline_missing')], [])
        self.assertEqual((CV / RI.DOC).read_text(encoding='utf-8'), RI.render(), 'run make_repo_index.py --write')
        roles = RI.roles()
        self.assertEqual(sorted(roles), RI.top_scripts())
        self.assertIn('driver_checks.py', [k for k, v in roles.items() if v == 'helper'])   # dynamic __import__ seen

    def test_structural_page_images_are_bound(self):
        rec = json.loads((CV / 'structural-review/output/pdf/structural-supplement-pdf-receipt.json').read_text(encoding='utf-8'))
        imgs = rec['visual_review']['rendered_page_sha256']
        for name, h in imgs.items():
            self.assertEqual(sha(CV / 'structural-review/tmp/pdfs' / name), h, name)


if __name__ == '__main__':
    unittest.main()
