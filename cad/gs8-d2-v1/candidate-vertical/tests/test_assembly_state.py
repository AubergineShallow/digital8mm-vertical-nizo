# SPDX-License-Identifier: MIT
"""Assembly-state model guard (review VN-22, fix FP-05). Pure Python: no CadQuery, nothing written.

Run (tests):   run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_assembly_state.py

Rules checked:
- steps.lint() is clean and the final build state equals every variant's manifest rows (tools never final);
- the centring gauge is never in the body with gs_camera or c_cs_adapter, in any build, bench or service state;
- every motion's obstacle set equals the parts present at its op minus movers, riders and named exemptions,
  recomputed here by an independent state walk; the 9ced753 hand-typed obstacles are all still obstacles and the
  register's omissions (VN-22) are now obstacles;
- verify_candidate.py sweeps the derived table (no hand-typed obstacle lists) and keeps the 10 legacy rows/knots;
- the corrected order (VN-39/40/41/43/44) and the driver contexts FP-07 consumes;
- negative controls: the original 9ced753 order and single mutations each produce the expected lint errors.
"""
from pathlib import Path
import ast
import copy
import json
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import steps as ST  # noqa: E402

GAUGE = 'centring_gauge'
VARIANTS = {}
for _p in sorted((CV / 'out').glob('*/manifest.json')):
    _m = json.loads(_p.read_text(encoding='utf-8'))
    if 'rows' in _m and 'storage' in _m:
        VARIANTS[_p.parent.name] = _m
LEGACY = {   # verify_candidate.py at 9ced753: id -> (movers, hand-typed obstacles, knots)
    'fps_knob_off': (['knob_fps'], ['panel', 'switch_1824', 'fps_nut', 'fps_mounting_washer'], [(0, 0, 0), (0, 20, 0)]),
    'fps_nut_after_unthread': (['fps_nut'], ['panel', 'switch_1824', 'fps_mounting_washer'], [(0, 0, 0), (0, 20, 0)]),
    'fps_washer_off': (['fps_mounting_washer'], ['panel', 'switch_1824'], [(0, 0, 0), (0, 20, 0)]),
    'carrier_out': (['carrier', 'pi5', 'cooler', 'x1203', 'x1203_kit', 'microsd', 'switch_1824'],
                    ['tub', 'gs_camera', 'c_cs_adapter', 'evf_board', 'hmx039', 'foam_pad'], [(0, 0, 0), (0, 70, 0)]),
    'panel_out': (['panel', 'encoder', 'knob_exp', 'power_button', 'power_nut_reserve'],
                  ['tub', 'pi5', 'cooler', 'x1203', 'carrier', 'switch_1824', 'gs_camera', 'c_cs_adapter', 'eyepiece',
                   'evf_board', 'hmx039', 'foam_pad'], [(0, 0, 0), (0, 70, 0)]),
    'camera_in': (['gs_camera', 'c_cs_adapter'], ['tub', 'lens_collar'],
                  [(-11.1, 60, 2), (-11.1, 0, 2), (-11.1, 0, 0), (0, 0, 0)]),
    'evf_in': (['hmx039', 'foam_pad', 'evf_board'], ['tub'], [(0, 60, 0), (0, 0, 0)]),
    'storage_plug_reservation_through_enclosure': (['usb_storage_plug_reserve'], ['tub', 'evf_board', 'hmx039'],
                                                   [(0, 0, 0), (-70, 0, 0)]),
    'storage_out': (['usb_stick'], ['tub', 'pi5', 'evf_board', 'hmx039'], [(0, 0, 0), (-70, 0, 0)]),
    'microsd_out': (['microsd'], ['tub', 'gs_camera', 'c_cs_adapter'], [(0, 0, 0), (45, 0, 0)]),
}
# FP-12 (VN-29) replaced the straight microsd_out path by the dog-leg; ids, movers and obstacles stay pinned above.
LEGACY['microsd_out'] = LEGACY['microsd_out'][:2] + ([(0, 0, 0), (18, 0, 0), (18, 40, 0)],)
FASTENERS = ['p_panel1', 'p_panel2', 'p_panel3', 'p_panel4', 'p_carrier1', 'p_carrier2', 'p_grip',
             's_c1', 's_c2', 's_c3', 's_c4']


def available(variant):
    m = VARIANTS[variant]
    return {r['id'] for r in m['rows']} | {t for t, s in ST.TOOLS.items() if s['step_file'] in m['files']}


def walk():
    """Independent state walk: {op id: (before, after)} for build body ops and every service op (own closure);
    refit occurrences of build ops go to REFIT_STATES."""
    REFIT_STATES.clear()
    states, body = {}, set()
    for o in ST.STEPS:
        before = set(body)
        if o['where'] != 'bench':
            body = (body | set(o['adds'])) - set(o['removes'])
        states[o['id']] = (before, set(body))
    final = set(body)
    for route in ST.SERVICE:
        order, todo = [], [route]
        while todo:                                   # requires first, each route once
            r = todo[-1]
            pend = [q for q in ST.SERVICE[r]['requires'] if q not in order]
            if pend:
                todo.append(pend[0])
            else:
                todo.pop()
                if r not in order:
                    order.append(r)
        s = set(final)
        for r in order:
            for o in ST.SERVICE[r]['ops']:
                before = set(s)
                s -= set(o['removes'])
                if r == route:
                    states[o['id']] = (before, set(s))
        # fixup-1: the documented refit (op list from the model) replayed here from this route's removal end state;
        # a build op repeated in a refit adds that refit's parts to its swept obstacles
        by = {o['id']: o for o in ST.STEPS}
        for oid in ST.route_refit(route):
            before = set(s)
            if by[oid]['where'] != 'bench':
                s = (s | set(by[oid]['adds'])) - set(by[oid]['removes'])
            REFIT_STATES.setdefault(oid, []).append((before, set(s)))
    return states


REFIT_STATES = {}


def original_order():
    """The 9ced753 ASSEMBLY-VERTICAL.md order (B3 panel with FPS washer/nut/knob, camera before collar+gauge, EVF
    matings in step 3, lens in step 7 after the panel)."""
    op, fps = ST.op, ['knob_fps', 'fps_mounting_washer', 'fps_nut']
    return [op('o_b0', 'B0', 'x', where='bench', group='camera', adds=ST.CAMERA, connects=['camera_fpc:cam']),
            op('o_b2', 'B2', 'x', where='bench', group='module', adds=ST.MODULE, connects=['evf_hdmi:pi', 'evf_5v:pi']),
            op('o_b3', 'B3', 'x', where='bench', group='panel', adds=ST.PANEL + fps),
            op('o_b4', 'B4', 'x', where='bench', group='evf', adds=ST.EVF),
            op('o_1', '1', 'x', adds=ST.GRIP + ['tub']), op('o_1b', '1', 'x', adds=['p_grip'], screws=['p_grip']),
            op('o_1c', '1', 'x', adds=['strap']),
            op('o_2a', '2', 'camera first', adds=ST.CAMERA, inserts='camera'),
            op('o_2b', '2', 'x', adds=['lens_collar'] + ST.COLLAR_ANCHORS), op('o_2c', '2', 'x', adds=[GAUGE]),
            op('o_2d', '2', 'x', screws=ST.COLLAR_ANCHORS), op('o_2e', '2', 'x', removes=[GAUGE]),
            op('o_3a', '3', 'x', adds=['eyepiece']),
            op('o_3', '3', 'x', adds=ST.EVF, inserts='evf', connects=['evf_hdmi:evf', 'evf_5v:evf']),
            op('o_4', '4', 'x', adds=ST.MODULE, inserts='module'),
            op('o_4b', '4', 'x', adds=ST.CARRIER_SCREWS, screws=ST.CARRIER_SCREWS),
            op('o_5', '5', 'x', connects=['camera_fpc:pi']),
            op('o_6', '6', 'x', adds=ST.PANEL + fps, inserts='panel'),
            op('o_6b', '6', 'x', adds=ST.PANEL_SCREWS, screws=ST.PANEL_SCREWS),
            op('o_7', '7', 'x', adds=['usb_stick', 'usb_storage_plug_reserve', 's_c4', 'lens'], screws=['s_c4']),
            op('o_7b', '7', 'x', adds=['eyecup']),
            op('o_8', '8', 'x', adds=['xt30_pair', 'pack', 'cap'])]


def codes(errs):
    return {c for c, _m in errs}


class ModelTests(unittest.TestCase):
    def test_lint_clean(self):
        self.assertEqual(ST.lint(), [])

    def test_manifests_built_and_tools_bound(self):
        self.assertEqual(len(VARIANTS), 3, sorted(VARIANTS))
        final = ST.final_state()
        self.assertFalse(set(ST.TOOLS) & final)
        for v, m in VARIANTS.items():
            with self.subTest(variant=v):
                self.assertEqual(ST.check_manifest({r['id'] for r in m['rows']}), [])
                self.assertIn(ST.TOOLS[GAUGE]['step_file'], m['files'])

    def test_gauge_never_with_camera_or_adapter(self):
        n = 0
        for phase, route, op_id, s in ST.all_states():
            n += 1
            if GAUGE in s:
                self.assertFalse({'gs_camera', 'c_cs_adapter'} & s, (phase, route, op_id))
        self.assertGreater(n, 60)
        i = {o['id']: k for k, o in enumerate(ST.STEPS)}
        self.assertTrue(i['collar_on'] < i['gauge_in'] < i['collar_tighten'] < i['gauge_out'] < i['camera_in'])
        self.assertIn(GAUGE, ST.present_at('collar_tighten'))

    def test_obstacles_are_present_minus_movers(self):
        states = walk()
        table = {m['id']: m for m in ST.motion_table()}
        self.assertEqual(set(table), set(ST.MOTIONS))
        for mid, m in ST.MOTIONS.items():
            with self.subTest(motion=mid):
                before, after = states[m['op']]
                present = before | after
                if table[mid]['phase'] == 'build':
                    present = present.union(*[x | y for x, y in REFIT_STATES.get(m['op'], [])])
                expect = present - set(m['movers']) - set(m['riders']) - set(m['exempt'])
                self.assertEqual(set(table[mid]['obstacles']), expect)
                self.assertTrue(set(m['movers']) <= present)
                for x, why in m['exempt'].items():
                    self.assertIn(x, present)
                    self.assertGreater(len(why.strip()), 20)

    def test_verify_candidate_uses_derived_table(self):
        src = (CV / 'verify_candidate.py').read_text(encoding='utf-8')
        self.assertIn('ST.verify_paths(', src)
        ids = {r['id'] for m in VARIANTS.values() for r in m['rows']} | set(ST.TOOLS)
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.List) and len(node.elts) >= 2 and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
                self.assertFalse({e.value for e in node.elts} <= ids, 'hand-typed id list at line %d' % node.lineno)
        for v in VARIANTS:
            with self.subTest(variant=v):
                paths = {pid: (mov, obs, knots) for pid, mov, obs, knots in ST.verify_paths(available(v))}
                for pid, (mov, old, knots) in LEGACY.items():
                    self.assertIn(pid, paths)
                    self.assertTrue(set(mov) <= set(paths[pid][0]))
                    self.assertEqual([tuple(float(c) for c in k) for k in paths[pid][2]],
                                     [tuple(float(c) for c in k) for k in knots])
                    self.assertEqual(sorted(set(old) - set(paths[pid][1])), [], 'obstacle dropped from %s' % pid)

    def test_register_omissions_now_obstacles(self):
        t = {pid: set(obs) for pid, mov, obs, k in ST.verify_paths(available('compact-kowa_lm6hc'))}
        self.assertTrue({'xt30_pair', 'lens_collar', 's_c1', 's_c2', 's_c3', 'eyepiece', 'eyecup'} <= t['carrier_out'])
        self.assertTrue({'x1203_kit', 'microsd', 'xt30_pair', 'usb_stick'} <= t['panel_out'])
        self.assertIn('lens', t['carrier_out'])
        self.assertTrue({'s_c1', 's_c2', 's_c3'} <= t['camera_in'])

    def test_corrected_order(self):
        i = {o['id']: k for k, o in enumerate(ST.STEPS)}
        chain = ['collar_on', 'gauge_in', 'collar_tighten', 'gauge_out', 'camera_in', 's_c4_start', 'lens_in',
                 'lens_float', 'eyepiece_in', 'evf_in', 'module_staged', 'carrier_in', 'carrier_screws', 'evf_mate',
                 'panel_prop', 'panel_in', 'panel_screws', 'fps_washer_on', 'fps_nut_on', 'knob_fps_on',
                 'storage_in', 'pack_in', 'cap_on']
        self.assertEqual(sorted(chain, key=i.get), chain)
        tok = {t: o['id'] for o in ST.STEPS for t in o['connects']}
        self.assertEqual({tok['evf_hdmi:evf'], tok['evf_5v:evf'], tok['camera_fpc:pi']}, {'evf_mate'})
        self.assertEqual(ST.STEPS[i[tok['camera_fpc:cam']]]['where'], 'bench')
        panel_bench = {a for o in ST.STEPS if o['group'] == 'panel' and o['where'] == 'bench' for a in o['adds']}
        self.assertFalse({'switch_1824', 'knob_fps', 'fps_nut', 'fps_mounting_washer'} & panel_bench)
        self.assertIn('switch_1824', ST.MODULE)
        labels = [s['step'] for s in ST.describe()]          # each ASSEMBLY section once, in order (FP-06 render)
        self.assertEqual(labels, ['B0', 'B1', 'B2', 'B3', 'B4', '1', '2', '3', '4', '5', '6', '7', '8'])
        for o in ST.STEPS:
            self.assertGreater(len(o['doc']), 40, o['id'])
            self.assertNotIn('spanner', (o['doc'] + o['tools']).replace('no spanner', '').replace('never a spanner', ''))

    def test_driver_contexts(self):
        rows = ST.driver_contexts()
        for f in FASTENERS:
            with self.subTest(fastener=f):
                b = [r for r in rows if r['fastener'] == f and r['phase'] == 'build']
                s = [r for r in rows if r['fastener'] == f and r['phase'] == 'service']
                self.assertEqual(len(b), 1)
                self.assertGreaterEqual(len(s), 1)
                for r in b + s:
                    self.assertNotIn(f, r['context'])
                    self.assertIn('tub', r['context'])
        ctx = {(r['fastener'], r['phase']): set(r['context']) for r in rows}
        self.assertIn('strap', ctx['p_grip', 'build'])
        for f in ST.COLLAR_ANCHORS:
            self.assertIn(GAUGE, ctx[f, 'build'])
        for f in ST.PANEL_SCREWS:
            self.assertNotIn('knob_fps', ctx[f, 'build'])
            self.assertNotIn('knob_fps', ctx[f, 'service'])
        self.assertIn('lens', ctx['s_c4', 'build'])
        nuts = [r for r in rows if r['kind'] == 'nut']
        self.assertEqual({r['fastener'] for r in nuts}, {'fps_nut', 'power_nut_reserve'})
        self.assertTrue(all(r['tool'] == ST.SOCKET for r in nuts))
        self.assertEqual(set(ctx['power_nut_reserve', 'build']), {'panel', 'encoder', 'knob_exp', 'power_button'})

    def test_every_removal_has_its_refit(self):
        adds = {o['id']: set(o['adds']) for o in ST.STEPS}
        for r, d in ST.SERVICE.items():
            self.assertEqual(ST.route_closure(r)[0], 'safety')
            for o in d['ops']:
                if o['removes'] and not o['refit']:
                    self.assertTrue(set(o['removes']) <= set().union(*[adds[x] for x in o['reverse_of']]), o['id'])


class NegativeControls(unittest.TestCase):
    def lint(self, steps=None, motions=None):
        return codes(ST.lint(steps if steps is not None else copy.deepcopy(ST.STEPS), ST.SERVICE,
                             motions if motions is not None else ST.MOTIONS))

    def test_original_order_fails(self):
        errs = ST.lint(original_order(), {}, {})
        c, text = codes(errs), ' | '.join(m for _c, m in errs)
        for want in ('TOOL_COEXIST', 'ORDER', 'CAMERA_RETAINED', 'MATE'):
            self.assertIn(want, c)
        for frag in ('lens_collar must enter before gs_camera', 'lens must enter before carrier',
                     'panel must enter before fps_mounting_washer', 'evf_hdmi: end part pi5 not present'):
            self.assertIn(frag, text)

    def move_after(self, ids, anchor):
        s = copy.deepcopy(ST.STEPS)
        moved = [o for o in s if o['id'] in ids]
        s = [o for o in s if o['id'] not in ids]
        k = [o['id'] for o in s].index(anchor) + 1
        return s[:k] + moved + s[k:]

    def test_mutations_are_caught(self):
        self.assertEqual(self.lint(), set())
        self.assertTrue({'ORDER', 'CAMERA_RETAINED'} <= self.lint(self.move_after(
            ['s_c4_start', 'lens_in', 'lens_float'], 'carrier_screws')))
        self.assertIn('TOOL_COEXIST', self.lint(self.move_after(['gauge_out'], 'camera_in')))
        self.assertIn('REFIT', self.lint([o for o in copy.deepcopy(ST.STEPS) if o['id'] != 'fps_nut_on']))
        m = copy.deepcopy(ST.MOTIONS)
        m['carrier_in']['path'] = [(0.0, 60.0, 0.0), (0.0, 0.0, 0.0)]
        self.assertIn('COVERAGE', self.lint(motions=m))
        m = copy.deepcopy(ST.MOTIONS)
        m['carrier_out']['riders'] = ['xt30_pair']                # dropping a present part by calling it a rider
        self.assertIn('MOTION_SET', self.lint(motions=m))
        m = copy.deepcopy(ST.MOTIONS)
        m['carrier_out']['exempt'] = {'xt30_pair': ' '}           # dropping it without a reason
        self.assertIn('EXEMPT', self.lint(motions=m))
        m = copy.deepcopy(ST.MOTIONS)
        del m['eyepiece_in']                                      # a moving op with no sweep and no reason
        self.assertIn('MOTION_MISSING', self.lint(motions=m))


if __name__ == '__main__':
    unittest.main(verbosity=2)
