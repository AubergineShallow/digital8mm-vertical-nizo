# SPDX-License-Identifier: MIT
"""Build-order and service text guard (review 2026-10-10, fix FP-06; VN-39, VN-40, VN-41, VN-42 docs, VN-43, VN-44,
VN-45, VN-46, VN-12 stale banner). Pure Python: no CadQuery, nothing written.

Run (tests):   run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_build_order_docs.py

Rules checked:
- ASSEMBLY-VERTICAL.md: every generated block (make_assembly_text.py) is current; the build operations appear exactly
  in steps.STEPS order, each under its own step heading; mutating steps.py makes the block stale;
- r7 checks.lens_turn_back_lint (taken unchanged from ../checks.py) passes on ASSEMBLY step 2, on steps.py step 2,
  on the closed-body lens service text and on the guide lens page of both builders, and fails on the 9ced753 text;
  none of r7 layout.LENS_HOLD_FORBIDDEN appears;
- no "spanner" as a tool anywhere in the text, steps.py docs or BOM rows (only negated mentions), with fixtures;
- every service removal is listed with its refit; the r7-vs-candidate matrix has every route once, both lens-change
  rows and the computed dependency chain; option A and option B of user decision 5 (VN-42) are both documented;
- both guide builders: GUIDE_OPS covers every body op in steps.py order, page() order matches, labels ascend,
  steps.py is bound, superseded 9ced753 wording is gone; FPS-SERVICE-STUDY.md refit order;
- the guide READMEs carry the STALE banner while the guide receipt binds older sources (removed after a rebuild).
"""
from pathlib import Path
from types import SimpleNamespace
import ast
import copy
import hashlib
import json
import re
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
CAD = CV.parent
sys.path[:0] = [str(CV), str(Path(__file__).resolve().parent)]
import steps as ST  # noqa: E402
import make_assembly_text as MA  # noqa: E402
from _repo_git import git, CV as CV_REL  # noqa: E402

UPSTREAM = CV.parents[3] / 'digital8mm' / 'cad' / 'gs8-d2-v1'
OLD = '9ced753'
BUILDERS = ('build_guide_vertical.py', 'build_guide_concealed_vents.py')


def rd(p):
    return Path(p).read_text(encoding='utf-8')


def old(rel):
    return git('show', '%s:%s%s' % (OLD, CV_REL, rel)).decode('utf-8')


def r7_function(name, path):
    """An r7 function, compiled from its unchanged source segment (no CadQuery import)."""
    src = rd(path)
    node = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == name)
    seg = ast.get_source_segment(src, node)
    ns = {}
    exec(compile(seg, str(path), 'exec'), ns)
    return ns[name], seg


def r7_constant(name, path):
    for n in ast.parse(rd(path)).body:
        if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == name for t in n.targets):
            return ast.literal_eval(n.value)
    raise KeyError(name)


LINT, LINT_SRC = r7_function('lens_turn_back_lint', CAD / 'checks.py')
TURN_BACK = r7_constant('LENS_TURN_BACK', CAD / 'layout.py')
FORBIDDEN = r7_constant('LENS_HOLD_FORBIDDEN', CAD / 'layout.py')


def turn_back(text, step='2'):
    """r7 lint on one step's action text, adapter: one tab-catch hold record (the lens thread) at that step."""
    L = SimpleNamespace(LENS_TURN_BACK=TURN_BACK, INSERTIONS=[dict(id='lens_in', step=step, hold='lock tab on catch')],
                        STEPS=[dict(step=step, action=text)])
    return LINT(L)


def section(text, label):
    """Text of '### <label>.' up to the next ### / ## heading."""
    m = re.search(r'^### %s\. .*?(?=^### |^## )' % re.escape(label), text, re.S | re.M)
    if not m:
        raise KeyError(label)
    return m.group(0)


_NEG = re.compile(r'(?i)\b(?:no|never(?:\s+use)?(?:\s+a)?|not(?:\s+a)?|instead\s+of(?:\s+a)?|nor(?:\s+a)?)\s+(?:thin\s+)?spanners?\b')


def spanner_uses(text):
    """Occurrences of 'spanner' that are not negated ('no spanner', 'never a spanner', ...)."""
    allowed = {m.end() for m in _NEG.finditer(text)}
    return [text[max(0, m.start() - 40):m.end() + 10] for m in re.finditer(r'(?i)spanners?\b', text)
            if m.end() not in allowed]


def literals(src):
    return [n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def pages(src):
    """([(lineno, label)] in source order, {label: joined string literals of that page block})."""
    tree = ast.parse(src)
    calls = sorted((n.lineno, n.args[0].value) for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and getattr(n.func, 'id', '') == 'page' and n.args and isinstance(n.args[0], ast.Constant))
    consts = sorted((n.lineno, n.col_offset, n.value) for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str))
    text = {}
    for i, (ln, label) in enumerate(calls):
        end = calls[i + 1][0] if i + 1 < len(calls) else 10 ** 9
        text[label] = ' '.join(v for l, _c, v in consts if ln <= l < end)
    return calls, text


def guide_ops(src):
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and any(getattr(t, 'id', '') == 'GUIDE_OPS' for t in n.targets):
            return ast.literal_eval(n.value)
    return None


DOC = rd(CV / 'ASSEMBLY-VERTICAL.md')
OPS_ITEM = re.compile(r'^\d+\. \*\*`([a-z0-9_]+)`\*\*', re.M)


class GeneratedBlocks(unittest.TestCase):
    def test_blocks_current(self):
        new, probs = MA.apply(DOC)
        self.assertEqual(probs, [])
        self.assertEqual(MA.stale_blocks(DOC), [], 'run make_assembly_text.py')
        self.assertEqual(new, DOC)

    def test_doc_order_equals_steps(self):
        found = []
        for m in re.finditer(r'<!-- BEGIN:ops (\S+) -->\n(.*?)<!-- END:ops \1 -->', DOC, re.S):
            heading = [h for h in re.finditer(r'^### (\S+)\. ', DOC[:m.start()], re.M)][-1].group(1)
            self.assertEqual(heading, m.group(1), 'block under the wrong heading')
            found += [(m.group(1), op) for op in OPS_ITEM.findall(m.group(2))]
        self.assertEqual(found, [(o['step'], o['id']) for o in ST.STEPS])

    def test_mutated_steps_make_block_stale(self):
        mut = copy.deepcopy(ST.STEPS)
        i, j = [k for k, o in enumerate(mut) if o['id'] in ('collar_on', 'camera_in')]
        mut[i], mut[j] = mut[j], mut[i]
        self.assertNotEqual(MA.render_ops('2', mut), MA.blocks()['ops 2'])
        self.assertTrue(ST.lint(mut))           # and the model itself rejects that order


class LensTurnBack(unittest.TestCase):
    def test_r7_source_unchanged(self):
        if (UPSTREAM / 'checks.py').is_file():
            self.assertEqual(LINT_SRC, r7_function('lens_turn_back_lint', UPSTREAM / 'checks.py')[1])
            self.assertEqual(TURN_BACK, r7_constant('LENS_TURN_BACK', UPSTREAM / 'layout.py'))

    def test_assembly_step2(self):
        self.assertEqual(turn_back(section(DOC, '2')), [])

    def test_steps_model_step2(self):
        self.assertEqual(turn_back(' '.join(o['doc'] for o in ST.STEPS if o['step'] == '2')), [])

    def test_closed_body_lens_service(self):
        para = re.search(r'^- \*\*Lens change with the same collar.*?(?=^- \*\*)', DOC, re.S | re.M).group(0)
        self.assertEqual(turn_back(para, 'svc-lens'), [])

    def test_guide_lens_pages(self):
        for b in BUILDERS:
            calls, text = pages(rd(CV / 'guide' / b))
            self.assertEqual(turn_back(text['08c']), [], b)

    def test_negative_control_9ced753(self):
        self.assertTrue(turn_back(section(old('ASSEMBLY-VERTICAL.md'), '2')))
        self.assertTrue(turn_back(section(old('ASSEMBLY-VERTICAL.md'), '7')))
        for b in BUILDERS:
            self.assertTrue(turn_back(pages(old('guide/' + b))[1]['17']), b)

    def test_no_forbidden_hold_wording(self):
        texts = {'ASSEMBLY': DOC, 'FPS': rd(CV / 'FPS-SERVICE-STUDY.md'),
                 'steps': ' '.join(o['doc'] for o in ST.STEPS)}
        texts.update({b: ' '.join(literals(rd(CV / 'guide' / b))) for b in BUILDERS})
        for k, t in texts.items():
            flat = ' '.join(t.split()).lower()
            self.assertEqual([p for p in FORBIDDEN if p.lower() in flat], [], k)


class Spanner(unittest.TestCase):
    def test_fixtures(self):
        self.assertEqual(len(spanner_uses('The nut may require a suitable thin spanner.')), 1)
        self.assertEqual(len(spanner_uses('1/2-inch switch-nut spanner/socket')), 1)
        self.assertEqual(spanner_uses('deep socket, never a spanner; no spanner: VN-46; not a spanner'), [])

    def test_no_spanner_tool(self):
        import make_bom_vertical as MB
        rows = MB.build_rows()[0]
        texts = {'ASSEMBLY': DOC, 'FPS': rd(CV / 'FPS-SERVICE-STUDY.md'),
                 'steps': ' '.join(o['doc'] + ' ' + o['tools'] for o in ST.STEPS) + ST.SOCKET,
                 'BOM rows': ' '.join(r['item'] + ' ' + r['note'] for r in rows),
                 'BOM-VERTICAL.md': rd(CV / 'BOM-VERTICAL.md'), 'BOM-VERTICAL.csv': rd(CV / 'BOM-VERTICAL.csv')}
        texts.update({b: ' \n'.join(literals(rd(CV / 'guide' / b))) for b in BUILDERS})
        for k, t in texts.items():
            self.assertEqual(spanner_uses(t), [], k)
        by = {r['line']: r for r in rows}
        for line in ('D2-61', 'V-62'):
            self.assertIn('deep socket', by[line]['item'].lower(), line)
        # size unknown until receipt: no purchase invented; the export18 purchased-selection claim stays true
        self.assertEqual(by['V-62']['purchase_qty'], 0)

    def test_negative_control_9ced753(self):
        self.assertGreaterEqual(len(spanner_uses(old('ASSEMBLY-VERTICAL.md'))), 2)
        self.assertTrue(spanner_uses(' '.join(literals(old('make_bom_vertical.py')))))


class Service(unittest.TestCase):
    def block(self, name):
        return re.search(r'<!-- BEGIN:%s -->\n(.*?)<!-- END:%s -->' % (name, name), DOC, re.S).group(1)

    def test_every_removal_has_its_refit_in_the_doc(self):
        rows = dict(re.findall(r'^\d+\. `(svc_[a-z0-9_]+)` .*\*Refit:\* (.*)$', self.block('service-routes'), re.M))
        for r, d in ST.SERVICE.items():
            for o in d['ops']:
                self.assertIn(o['id'], rows, o['id'])
                for x in o['reverse_of']:
                    self.assertIn('`%s`' % x, rows[o['id']], o['id'])
                if o['refit']:
                    self.assertIn(o['refit'].rstrip('.'), rows[o['id']])
                if o['removes']:
                    self.assertNotIn('none (nothing removed)', rows[o['id']])
        self.assertEqual([e for e in ST.lint() if e[0] == 'REFIT'], [])

    def test_dropped_refit_is_caught(self):
        saved = ST.SERVICE
        try:
            ST.SERVICE = copy.deepcopy(saved)
            ST.SERVICE['panel']['ops'][1]['reverse_of'] = []
            self.assertNotEqual(MA.render_service_routes(), self.block('service-routes'))
            self.assertIn('REFIT', [e[0] for e in ST.lint()])
        finally:
            ST.SERVICE = saved

    def test_matrix(self):
        rows = [l for l in self.block('service-matrix').splitlines() if l.startswith('| ') and '`' in l.split('|')[1]]
        seen = {}
        for l in rows:
            cells = [c.strip() for c in l.strip('|').split('|')]
            route = re.search(r'`([a-z]+)`$', cells[0]).group(1)
            seen[route] = cells
            self.assertEqual(cells[2], ' -> '.join('`%s`' % x for x in ST.route_closure(route)[:-1]) or 'none')
        self.assertEqual(sorted(seen), sorted(ST.SERVICE))
        self.assertEqual(sorted(r for r, c in seen.items() if c[0].startswith('Lens change')), ['collar', 'lens'])
        self.assertIn('collar_on', seen['collar'][4])
        self.assertIn('gauge_in', seen['collar'][4])
        self.assertIn('module', seen['camera'][2])          # VN-42: camera service needs the module out

    def test_vn42_vn45_text(self):
        dec = DOC[DOC.index('\n### 5.3 '):DOC.index('\n## 6. ')]
        for s in ('Option A', 'Option B', 'not decided here', '(B1)', '(B2)'):
            self.assertIn(s, dec)
        self.assertNotIn('where the reviewed clearance requires it', DOC)
        self.assertIn('module', ST.SERVICE['grip']['requires'])
        self.assertIn('Pi module out first', DOC)
        for b in BUILDERS:
            t = pages(rd(CV / 'guide' / b))[1]
            self.assertIn('Option A', t['19b'], b)
            self.assertIn('Option B', t['19b'], b)
            self.assertIn('Pi module out first', t['19'], b)


SUPERSEDED_DOC = ['Lens final installation can wait until step 7', 'Fit and centre the lens collar with the printed gauge',
                  'Mate the EVF HDMI head from the reviewed direction', 'Establish the removable EVF power junction',
                  'Seat the panel over its bushing and locating peg only after', 'where the reviewed clearance requires it',
                  'thin spanner', 'free run and pigtail leads before sliding the grip off',
                  'Check both end contacts/latches']
SUPERSEDED_GUIDE = ['Thread the strap after the grip lock', 'Thread after seating and locking the grip',
                    'Fit collar with gauge and 3 anchor screws', 'The straight HDMI head mates upward only after the board',
                    'Recording drive and lens last', 'Pinch screw is last optical operation',
                    'Trial panel removal and refit', 'Nut tools, saw']


class Guides(unittest.TestCase):
    def test_guide_ops_follow_steps(self):
        idx = {o['id']: i for i, o in enumerate(ST.STEPS)}
        body = [o['id'] for o in ST.STEPS if o['where'] == 'body']
        for b in BUILDERS:
            src = rd(CV / 'guide' / b)
            g = guide_ops(src)
            self.assertIsNotNone(g, b)
            flat = [op for ops in g.values() for op in ops]
            self.assertEqual([op for op in flat if op not in idx], [], b)
            self.assertEqual([idx[op] for op in flat], sorted(idx[op] for op in flat), b)
            self.assertEqual([op for op in body if op not in flat], [], b)
            calls, _t = pages(src)
            labels = [l for _ln, l in calls]
            self.assertEqual([l for l in labels if l in g], list(g), b + ': page() order differs from GUIDE_OPS')
            self.assertEqual(labels[1:], sorted(labels[1:]), b + ': page labels not ascending')
            self.assertIn("guide page order differs from steps.py", src)
            self.assertIn("ROOT/'steps.py'", src)

    def test_superseded_wording_gone(self):
        for b in BUILDERS:
            self.assertEqual([p for p in SUPERSEDED_GUIDE if p in rd(CV / 'guide' / b)], [], b)
        prev = old('guide/' + BUILDERS[1])
        self.assertEqual([p for p in SUPERSEDED_GUIDE if p not in prev], [], 'list must name real 9ced753 wording')
        self.assertEqual([p for p in SUPERSEDED_DOC if p in DOC], [])
        self.assertEqual([p for p in SUPERSEDED_DOC if p not in old('ASSEMBLY-VERTICAL.md')], [])

    def test_scene_ids_exist(self):
        """Every part id a scene() call names is a bound mesh of the compact manifest, a DATA key the builder makes,
        or a connector / header housing of the frozen HDMI snapshot (made at runtime), so the next rebuild of the
        re-ordered pages cannot stop on an unknown id."""
        man = json.loads(rd(CV / 'out/compact-kowa_lm6hc/manifest.json'))
        known = {k[len('meshes/'):-len('.json')] for k in man['files'] if k.startswith('meshes/')}
        snap = json.loads(rd(CV / 'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json'))
        known |= {c['id'] for c in snap['connectors']} | {h['id'] for h in snap['header_housings']}
        for b in BUILDERS:
            tree = ast.parse(rd(CV / 'guide' / b))
            made = {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript) and
                    getattr(n.value, 'id', '') == 'DATA' and isinstance(n.slice, ast.Constant)}
            ids = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'scene':
                    for a in list(n.args[1:3]) + [k.value for k in n.keywords if k.arg == 'offsets']:
                        ids |= {c.value for c in ast.walk(a) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
            self.assertEqual(sorted(ids - known - made - {'pack_translation'}), [], b)  # pose field, not an id

    def test_page_semantics(self):
        for b in BUILDERS:
            t = pages(rd(CV / 'guide' / b))[1]
            self.assertIn('empty lip', t['08'], b)
            self.assertIn('No HDMI or EVF power mating yet', t['09'], b)
            self.assertIn('before the grip-lock screw', t['07b'], b)
            n = t['16']
            order = [n.index(s) for s in ('4 panel screws', 'washer, nut (deep socket', 'knob on the paper strips')]
            self.assertEqual(order, sorted(order), b)
            self.assertIn('FPC camera end here', t['03'], b)


class FPSStudy(unittest.TestCase):
    def test_refit_and_removal_order(self):
        t = rd(CV / 'FPS-SERVICE-STUDY.md')
        ids = {o['id'] for o in ST.STEPS} | {o['id'] for d in ST.SERVICE.values() for o in d['ops']}
        named = set(re.findall(r'`((?:svc_)?[a-z0-9]+(?:_[a-z0-9]+)+)`', t)) - {'reverse_of'}
        self.assertEqual(sorted(n for n in named if n not in ids and not n.endswith('.py')), [])
        for seq in (('svc_knob_fps_off', 'svc_fps_nut_off', 'svc_fps_washer_off'),
                    ('panel_in', 'panel_screws', 'fps_washer_on', 'fps_nut_on', 'knob_fps_on')):
            pos = [t.index('`%s`' % s) for s in seq]
            self.assertEqual(pos, sorted(pos), seq)
        self.assertIn('deep socket on the bushing axis', t)
        self.assertNotIn('use a matching tool', t)
        self.assertIn('use a matching tool', old('FPS-SERVICE-STUDY.md'))


class StaleGuideBanner(unittest.TestCase):
    def test_banner_tracks_receipt(self):
        rec = json.loads(rd(CV / 'guide/out-concealed-vents/guide-receipt.json'))['sources']
        keys = ['candidate-vertical/ASSEMBLY-VERTICAL.md', 'candidate-vertical/guide/build_guide_concealed_vents.py']
        stale = any(rec.get(k) != hashlib.sha256((CAD / k).read_bytes()).hexdigest() for k in keys)
        for name in ('README-CONCEALED-VENTS.md', 'README.md'):
            head = '\n'.join(rd(CV / 'guide' / name).splitlines()[:15])
            self.assertEqual('STALE (review 2026-10-10' in head, stale, name)
        # stale is expected until FP-16 rebuilds the guide in the rebuild worktree (VN-12); then the banners go.
        self.assertIn('**stale**', DOC[DOC.index('\n## 4. '):DOC.index('\n### B0. ')])


if __name__ == '__main__':
    unittest.main(verbosity=2)
