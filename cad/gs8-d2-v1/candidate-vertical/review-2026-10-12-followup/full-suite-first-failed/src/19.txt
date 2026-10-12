# SPDX-License-Identifier: MIT
"""Cross-platform I/O guard (review VN-02 and VN-03, fix FP-02).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_cross_platform_io.py

Pure standard library; no CAD import, no geometry. Checks:
- cv_io helpers: UTF-8 read/write, LF on write, '/' in every relative path, PYTHONUTF8 child guard;
- AST lint of every live candidate script (frozen snapshot folders excluded by name): no text I/O without
  encoding='utf-8' (and newline= on writes), no relative_to() result turned into a string without
  .as_posix(), no os.path.relpath / os.sep outside cv_io.py, every cv_io helper imported where used;
- the lint itself catches each violation in a planted source (negative control);
- no backslash in any key or string of any JSON file under candidate-vertical (meshes caches excluded),
  nor in the generated BOM CSV; a planted Windows-style manifest is caught (negative control);
- the manifest writers build keys with the posix helpers, and every literal manifest lookup in the
  candidate scripts resolves in the committed manifests.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import re
import sys
import tempfile
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import cv_io  # noqa: E402

FROZEN = ('history/', 'routing-snapshots/', 'out/', 'vent-study/', 'review-2026-10-10/')
# Restored-unchanged archive scripts: structural-review/coupon-reproducer-recovery.json and coupons/README.md
# state that their bytes are identical to the recovered archive, so they stay byte-frozen with their bare I/O
# (run them with `python -X utf8` on Windows). test_frozen_reproducer_matches_recovery_receipt ties this
# exclusion to that receipt: editing a file, or a receipt that no longer lists it, fails the test.
FROZEN_FILES = {'structural-review/make_coupons.py', 'structural-review/check_coupon_meshes.py',
                'structural-review/render_coupons.py'}
HELPERS = {'read_text', 'write_text', 'open_text', 'posix', 'rel_posix', 'relpath_posix', 'child_env'}
NON_FILE_OPENERS = {'Image', 'zipfile', 'tarfile', 'webbrowser', 'os', 'gzip', 'bz2', 'lzma'}
MODE_RE = re.compile(r'^[rwaxbtU+]+$')
BS = chr(92)
VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')


def live_scripts():
    for p in sorted(CV.rglob('*.py')):
        rel = p.relative_to(CV).as_posix()
        if rel.startswith(FROZEN) or rel in FROZEN_FILES or '__pycache__' in p.parts:
            continue
        yield rel, p


def _utf8(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and \
        node.value.lower().replace('-', '').replace('_', '') == 'utf8'


def _mode(call, first):
    kw = {k.arg: k.value for k in call.keywords}
    args = call.args[first:]
    node = args[0] if args else kw.get('mode')
    if node is None:
        return 'r'
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def lint_source(src, rel='<string>'):
    """Violations as (line, rule) tuples for one module's source text."""
    tree = ast.parse(src)
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == 'cv_io':
            imported |= {a.asname or a.name for a in n.names}
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            imported.add(n.name)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr == 'sep' and getattr(n.value, 'id', '') == 'os' and rel != 'cv_io.py':
            out.append((n.lineno, 'os.sep'))
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        kw = {k.arg: k.value for k in n.keywords}
        enc = _utf8(kw.get('encoding'))
        nl = isinstance(kw.get('newline'), ast.Constant) and kw['newline'].value in ('\n', '')
        name = f.id if isinstance(f, ast.Name) else None
        attr = f.attr if isinstance(f, ast.Attribute) else None
        dotted = ast.unparse(f)
        if rel == 'cv_io.py' or dotted.startswith('cv_io.'):
            pass      # the helper module itself (unit-tested in TestCvIo) and qualified helper calls
        elif attr == 'read_text' and not enc:
            out.append((n.lineno, 'read_text without utf-8'))
        elif attr == 'write_text' and not (enc and nl):
            out.append((n.lineno, 'write_text without utf-8 and newline'))
        elif name == 'open' or dotted in ('io.open', 'codecs.open') or (
                attr == 'open' and not (isinstance(f.value, ast.Name) and f.value.id in NON_FILE_OPENERS)
                and (not n.args or (isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)
                                    and MODE_RE.match(n.args[0].value)))):
            mode = _mode(n, 0 if attr == 'open' and dotted not in ('io.open', 'codecs.open') else 1)
            if mode is None:
                out.append((n.lineno, 'open with non-literal mode'))
            elif 'b' not in mode and not enc:
                out.append((n.lineno, 'text open without utf-8'))
            elif 'b' not in mode and set(mode) & set('wax+') and not nl:
                out.append((n.lineno, 'text write open without newline'))
        elif dotted.startswith('subprocess.') and (_true(kw.get('text')) or _true(kw.get('universal_newlines'))) and not enc:
            out.append((n.lineno, 'subprocess text without utf-8'))
        elif dotted in ('io.TextIOWrapper',) and not enc:
            out.append((n.lineno, 'TextIOWrapper without utf-8'))
        elif dotted.split('.')[-1] in ('NamedTemporaryFile', 'TemporaryFile', 'SpooledTemporaryFile'):
            mode = _mode(n, 0)
            if mode is None or ('b' not in mode and not enc):
                out.append((n.lineno, 'text temporary file without utf-8'))
        if attr == 'relative_to':
            p = parent.get(n)
            ok = (isinstance(p, ast.Attribute) and p.attr == 'as_posix') or \
                 (isinstance(p, ast.BinOp) and isinstance(p.op, ast.Div)) or \
                 (isinstance(p, ast.Call) and ast.unparse(p.func) in ('Path', 'PurePath', 'PurePosixPath'))
            if not ok:
                out.append((n.lineno, 'relative_to without as_posix'))
        if (dotted == 'os.path.relpath' or name == 'relpath') and rel != 'cv_io.py':
            out.append((n.lineno, 'os.path.relpath outside cv_io'))
        if name in HELPERS and name not in imported:
            out.append((n.lineno, 'cv_io helper not imported: ' + name))
    return out


def _true(node):
    return isinstance(node, ast.Constant) and bool(node.value)


def json_backslashes(root):
    """(file, where, text) for every backslash in a JSON key or string under root (meshes caches skipped)."""
    hits = []

    def walk(o, f, where):
        if isinstance(o, dict):
            for k, v in o.items():
                if BS in k:
                    hits.append((f, 'key', k[:120]))
                walk(v, f, k)
        elif isinstance(o, list):
            for x in o:
                walk(x, f, where)
        elif isinstance(o, str) and BS in o:
            hits.append((f, where, o[:120]))

    for p in sorted(Path(root).rglob('*.json')):
        if 'meshes' in p.parts:
            continue
        walk(json.loads(p.read_text(encoding='utf-8')), p.relative_to(root).as_posix(), '')
    return hits


class TestCvIo(unittest.TestCase):
    def test_write_is_utf8_lf_and_read_round_trips(self):
        text = 'a’b − c”\nsecond line\n'      # U+201D encodes to e2 80 9d: 0x9d is undefined in cp1252
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.md'
            cv_io.write_text(p, text)
            raw = p.read_bytes()
            self.assertEqual(raw, text.encode('utf-8'))
            self.assertNotIn(b'\r', raw)
            self.assertEqual(cv_io.read_text(p), text)
            with cv_io.open_text(Path(d) / 'y.txt', 'w') as f:
                f.write('one\ntwo−\n')
            self.assertEqual((Path(d) / 'y.txt').read_bytes(), 'one\ntwo−\n'.encode('utf-8'))
            with cv_io.open_text(Path(d) / 'y.txt') as f:
                self.assertEqual(f.read(), 'one\ntwo−\n')
            with self.assertRaises(ValueError):
                cv_io.open_text(p, 'rb')

    def test_relative_paths_are_posix(self):
        base = Path(tempfile.gettempdir()) / 'cv-base'
        self.assertEqual(cv_io.rel_posix(base / 'step' / 'pi5.step', base), 'step/pi5.step')
        self.assertEqual(cv_io.relpath_posix(base / 'model.py', base / 'sub'), '../model.py')
        self.assertEqual(cv_io.posix(Path('out') / 'compact-kowa_lm6hc' / 'x.json'), 'out/compact-kowa_lm6hc/x.json')
        with self.assertRaises(ValueError):
            cv_io.rel_posix(base.parent / 'elsewhere.txt', base)
        if os.name == 'nt':
            self.assertEqual(cv_io.posix('check-logs\\mesh.log'), 'check-logs/mesh.log')

    def test_child_env_sets_utf8_mode(self):
        env = cv_io.child_env(EXTRA='1')
        self.assertEqual(env['PYTHONUTF8'], '1')
        self.assertEqual(env['EXTRA'], '1')
        self.assertEqual(env.get('PATH'), os.environ.get('PATH'))


class TestLint(unittest.TestCase):
    def test_live_scripts_are_clean(self):
        scripts = list(live_scripts())
        self.assertGreaterEqual(len(scripts), 110, 'live script set shrank; check the FROZEN prefixes')
        for prefix in ('guide/', 'structural-review/', 'tests/'):
            self.assertTrue(any(r.startswith(prefix) for r, _ in scripts), prefix)
        bad = []
        for rel, p in scripts:
            bad += ['%s:%d %s' % (rel, line, rule) for line, rule in lint_source(p.read_text(encoding='utf-8'), rel)]
        self.assertEqual(bad, [], '\n'.join(bad))

    def test_frozen_reproducer_matches_recovery_receipt(self):
        receipt = json.loads((CV / 'structural-review/coupon-reproducer-recovery.json').read_text(encoding='utf-8'))
        restored = {'structural-review/' + x['path']: x['restored_sha256'] for x in receipt['restored_files']
                    if x['path'].endswith('.py')}
        self.assertEqual(set(restored), FROZEN_FILES)
        for rel, digest in restored.items():
            self.assertEqual(hashlib.sha256((CV / rel).read_bytes()).hexdigest(), digest, rel + ' is no longer the restored archive copy')

    def test_lint_catches_each_violation(self):
        planted = '\n'.join([
            "import os, subprocess, io, tempfile",
            "from pathlib import Path",
            "p = Path('x')",
            "p.read_text()",
            "p.write_text('a', encoding='utf-8')",
            "open(p)",
            "open(p, 'w', encoding='utf-8')",
            "p.open('a')",
            "subprocess.run(['git'], text=True)",
            "k = str(p.relative_to(Path('.')))",
            "f'{p.relative_to(Path(\".\"))}'",
            "os.path.relpath(p, '.')",
            "s = 'a' + os.sep",
            "read_text(p)",
            "io.TextIOWrapper(None)",
            "tempfile.NamedTemporaryFile('w')",
            "open(p, mode_variable)",
        ])
        rules = sorted(rule for _, rule in lint_source(planted))
        self.assertEqual(rules, sorted([
            'read_text without utf-8', 'write_text without utf-8 and newline', 'text open without utf-8',
            'text write open without newline', 'text open without utf-8', 'subprocess text without utf-8',
            'relative_to without as_posix', 'relative_to without as_posix', 'os.path.relpath outside cv_io',
            'os.sep', 'cv_io helper not imported: read_text', 'TextIOWrapper without utf-8',
            'text temporary file without utf-8', 'open with non-literal mode']))

    def test_lint_accepts_compliant_forms(self):
        ok = '\n'.join([
            "import subprocess, csv",
            "from pathlib import Path",
            "from cv_io import read_text, write_text, open_text, rel_posix",
            "p = Path('x')",
            "read_text(p); write_text(p, 'a')",
            "p.read_text(encoding='utf-8'); p.write_text('a', encoding='utf-8', newline='\\n')",
            "open(p, 'rb'); open(p, 'w', encoding='utf-8', newline='')",
            "open_text(p, 'w')",
            "subprocess.run(['git'], text=True, encoding='utf-8')",
            "k = p.relative_to(Path('.')).as_posix(); q = Path('.') / p.relative_to(Path('.'))",
            "k2 = rel_posix(p, Path('.'))",
        ])
        self.assertEqual(lint_source(ok), [])


class TestKeys(unittest.TestCase):
    def test_no_backslash_in_any_json_key_or_string(self):
        hits = json_backslashes(CV)
        self.assertEqual(hits, [], '\n'.join(map(str, hits[:40])))

    def test_no_backslash_in_generated_bom_csv(self):
        self.assertNotIn(BS, (CV / 'BOM-VERTICAL.csv').read_text(encoding='utf-8'))

    def test_detector_catches_windows_style_keys(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'manifest.json').write_text(json.dumps(
                {'files': {'step' + BS + 'pi5.step': 'x', 'step/tub.step': 'y'},
                 'checks': [{'log': 'check-logs' + BS + 'mesh.log'}]}), encoding='utf-8', newline='\n')
            self.assertEqual(len(json_backslashes(d)), 2)

    def test_manifest_writers_use_posix_helpers(self):
        def keys_of(rel):
            tree = ast.parse((CV / rel).read_text(encoding='utf-8'))
            return [ast.unparse(n.key.func) for n in ast.walk(tree)
                    if isinstance(n, ast.DictComp) and isinstance(n.key, ast.Call)]
        self.assertEqual(keys_of('export_candidate.py'), ['relpath_posix', 'relpath_posix', 'rel_posix'])
        self.assertEqual(keys_of('make_corrected_pi.py'), ['rel_posix', 'rel_posix'])
        src = (CV / 'structural-review/update_concealed_vent_structure.py').read_text(encoding='utf-8')
        self.assertIn("'path':rel_posix(vp,C)", src)

    def test_literal_manifest_lookups_resolve(self):
        keys = {'files': set(), 'sources': set()}
        for v in VARIANTS:
            m = json.loads((CV / 'out' / v / 'manifest.json').read_text(encoding='utf-8'))
            for k in keys:
                keys[k] |= set(m[k])
        lookups = []
        for rel, p in live_scripts():
            for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
                target = key = None
                if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Subscript):
                    target, key = n.value.slice, n.slice
                elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'get' \
                        and isinstance(n.func.value, ast.Subscript) and n.args:
                    target, key = n.func.value.slice, n.args[0]
                if isinstance(target, ast.Constant) and target.value in keys:
                    t = _template(key)
                    if t and ('/' in t[0] + t[1] or '.' in t[0] + t[1]):   # file-path keys, not record fields
                        lookups.append((rel, n.lineno, target.value) + t)
        self.assertGreaterEqual(len(lookups), 20)
        bad = []
        for rel, line, field, prefix, suffix, exact in lookups:
            pool = keys[field]
            hit = (prefix in pool) if exact else any(k.startswith(prefix) and k.endswith(suffix) for k in pool)
            if BS in prefix + suffix or not hit:
                bad.append('%s:%d %s[%r...%r]' % (rel, line, field, prefix, suffix))
        self.assertEqual(bad, [], '\n'.join(bad))


def _template(node):
    """(prefix, suffix, exact) of a literal / f-string / '+' key expression, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, '', True
    parts = []
    if isinstance(node, ast.JoinedStr):
        parts = [v.value if isinstance(v, ast.Constant) else None for v in node.values]
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        def flat(x):
            if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add):
                return flat(x.left) + flat(x.right)
            return [x.value if isinstance(x, ast.Constant) and isinstance(x.value, str) else None]
        parts = flat(node)
    if not parts or all(p is not None for p in parts) or (parts[0] is None and parts[-1] is None):
        return None
    prefix = ''
    i = 0
    while i < len(parts) and parts[i] is not None:
        prefix += parts[i]
        i += 1
    suffix = ''
    j = len(parts) - 1
    while j >= 0 and parts[j] is not None:
        suffix = parts[j] + suffix
        j -= 1
    return prefix, suffix, False


if __name__ == '__main__':
    unittest.main(verbosity=2)
