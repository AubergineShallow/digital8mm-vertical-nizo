# SPDX-License-Identifier: MIT
"""Guide scenes follow the assembly-state model (fixup-1 of FP-06). Pure Python, nothing rendered.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_guide_scenes.py

For every build page of both guide builders (pages named in GUIDE_OPS whose last op is a body/prop op):
- the manifest part ids a scene draws are a subset of steps.present_at(last op of the page): a page never shows a
  part before it is fitted (page 16 used to draw the eyecup of step 7);
- a whole-body scene (one that draws the tub and the grip) draws every material part present then, except screws,
  nuts and tools (page 16 used to leave out the lens and s_c4 fitted in step 2, and pages 08b-17 the strap);
- page 07 threads the strap on the open base, page 09 draws the eyepiece's +X push, and STEP-REVIEW.md names the
  re-ordered page set. Proof drawings that intentionally show another state are listed with their reason.
"""
from pathlib import Path
import ast
import json
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import steps as ST  # noqa: E402

BUILDERS = ('build_guide_vertical.py', 'build_guide_concealed_vents.py')
MANIFEST = json.loads((CV / 'out/compact-kowa_lm6hc/manifest.json').read_text(encoding='utf-8'))
KIND = {r['id']: r['kind'] for r in MANIFEST['rows']}
MATERIAL = {i for i, k in KIND.items() if k != 'keepout'}
PROOF_PAGES = {'15': 'power-stow proof: draws the step 8 pack and XT30 pose beside the stack (r7 C6 stow proof)'}
LIST_NAMES = ('BASE', 'OPT', 'EVF', 'EVF_IN', 'STACK', 'FPS_HARDWARE', 'PANEL', 'carried')


def namespace(tree):
    ns = {'DATA': set(KIND) | {'fps_nut', 'fps_mounting_washer'}, 'HEADERS': [], 'FPS_WIRES': [], 'FPS_READY': True}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], 'id', '') in LIST_NAMES:
            ns[node.targets[0].id] = eval(compile(ast.Expression(node.value), '<guide>', 'eval'), {}, dict(ns))
    return ns


def scenes(src):
    """[(page label, [scene id lists], [scene call nodes])] in source order; unknown list names count as empty."""
    tree = ast.parse(src)
    ns = namespace(tree)
    out = []
    for node in tree.body:
        call = node.value if isinstance(node, (ast.Expr, ast.Assign)) else None
        if isinstance(node, ast.Assign) and isinstance(call, ast.Call) and getattr(call.func, 'id', '') == 'page':
            out.append((call.args[0].value, [], []))
            continue
        for c in [n for n in ast.walk(node) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'scene']:
            if not out:
                continue
            expr = c.args[1]
            local = dict(ns)
            for n in ast.walk(expr):
                if isinstance(n, ast.Name) and n.id not in local:
                    local[n.id] = []
            ids = eval(compile(ast.Expression(expr), '<scene>', 'eval'), {}, local)
            out[-1][1].append({x for x in ids if isinstance(x, str)})
            out[-1][2].append(c)
    return tree, out


def guide_ops(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'GUIDE_OPS':
            return ast.literal_eval(node.value)
    raise AssertionError('GUIDE_OPS missing')


class GuideScenes(unittest.TestCase):
    def test_scenes_match_present_at(self):
        by = {o['id']: o for o in ST.STEPS}
        for b in BUILDERS:
            tree, pages = scenes((CV / 'guide' / b).read_text(encoding='utf-8'))
            g = guide_ops(tree)
            checked = 0
            for label, idsets, _calls in pages:
                if label not in g or label in PROOF_PAGES or by[g[label][-1]]['where'] == 'bench':
                    continue
                present = set(ST.present_at(g[label][-1]))
                need = (present & MATERIAL) - ST.SCREW_IDS - ST.NUT_IDS - set(ST.TOOLS) - set(ST.OPTIONAL)
                for ids in idsets:
                    with self.subTest(builder=b, page=label):
                        self.assertEqual(sorted((ids & set(KIND)) - present), [], 'drawn before it is fitted')
                        if {'tub', 'base_grip'} <= ids:
                            self.assertEqual(sorted(need - ids), [], 'whole-body scene leaves out present parts')
                            checked += 1
            self.assertGreaterEqual(checked, 8, b)     # 07b, 08, 08b, 08c, 09, 11, 16, 17

    def test_strap_page_and_eyepiece_arrow(self):
        for b in BUILDERS:
            src = (CV / 'guide' / b).read_text(encoding='utf-8')
            tree, pages = scenes(src)
            g = guide_ops(tree)
            self.assertEqual(g['07'], ('grip_prep', 'strap_thread'), b)
            self.assertEqual(g['07b'], ('tub_on', 'grip_lock'), b)
            p = {label: (ids, calls) for label, ids, calls in pages}
            self.assertNotIn('tub', p['07'][0][0], b)                  # strap threaded with the tub off
            self.assertIn('seated tub floor closes', src)
            self.assertNotIn('Thread after seating the tub', src)     # the FP-05 wording the verifier rejected
            call = p['09'][1][0]
            kw = {k.arg: k.value for k in call.keywords}
            self.assertIn('eyepiece', ast.literal_eval(call.args[2]), b)
            off = ast.literal_eval(kw['offsets'])['eyepiece']
            self.assertTrue(off[0] < 0 and off[1] == 0 and off[2] == 0, off)   # drawn behind: pushed +X
            self.assertGreaterEqual(len(ast.literal_eval(kw['arrows'])), 2, b)

    def test_step_review_names_the_page_set(self):
        t = (CV / 'guide/STEP-REVIEW.md').read_text(encoding='utf-8')
        labels = [l.split('|')[1].split()[0] for l in t.splitlines() if l.startswith('| ') and not l.startswith('| Step')]
        for want in ('06e', '06h', '07', '07b', '08', '08b', '08c', '09', '16', '17'):
            self.assertIn(want, labels)
        self.assertNotIn('17 Recording drive / lens', t)
        self.assertIn('before the tub', t[t.index('| 07 '):t.index('| 07b ')].lower().replace('before the tub', 'before the tub'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
