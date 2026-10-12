# SPDX-License-Identifier: MIT
"""Service refit, strap order, camera retention and lead securing (fixup-1 of FP-05/FP-06). Pure Python.

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_refit_state.py

Defects this guards (verifier 2026-10-11):
- the strap was threaded after the tub, but its over-bridge pass lies in the base-top recess the tub floor closes;
- ASSEMBLY section 5 told the reader to refit a route's own ops, then its prerequisites in reverse: for the collar
  route that is lens_float with no lens, the carrier before the lens (VN-41) and the pack before the panel;
- the lint ran on build, bench and removal states only, never on a refit (the only post-build gauge use);
- the camera route took the lens off before the module, leaving the camera unretained while the module moved;
- evf_mate secured the QT and J2 leads before their panel ends were mated at panel_prop.
"""
from pathlib import Path
import copy
import re
import sys
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
import steps as ST  # noqa: E402
import make_assembly_text as MA  # noqa: E402

DOC = (CV / 'ASSEMBLY-VERTICAL.md').read_text(encoding='utf-8')


def codes(errs):
    return {c for c, _m in errs}


def literal_old_rule(route):
    """The superseded ASSEMBLY rule: the route's own refit ops, then each prerequisite's own ops in reverse order."""
    chain = ST.route_closure(route)
    out = []
    for q in [route] + list(reversed(chain[:-1])):
        out += [x for x in ST.route_refit(q, closure=False) if x not in out]
    return out


class Strap(unittest.TestCase):
    def test_strap_on_the_open_base(self):
        i = {o['id']: k for k, o in enumerate(ST.STEPS)}
        self.assertLess(i['strap_thread'], i['tub_on'])
        self.assertLess(i['strap_thread'], i['grip_lock'])
        self.assertIn(('strap', 'tub'), [(a, b) for a, b, _w in ST.ORDER_RULES])
        self.assertIn('strap', ST.state_before('tub_on'))
        self.assertIn('strap', {r['fastener']: set(r['context']) for r in ST.driver_contexts()
                                if r['phase'] == 'build'}['p_grip'])

    def test_strap_after_tub_fails(self):
        s = copy.deepcopy(ST.STEPS)
        o = s.pop([x['id'] for x in s].index('strap_thread'))
        s.insert([x['id'] for x in s].index('tub_on') + 1, o)        # the FP-05 order the verifier rejected
        errs = ST.lint(s, ST.SERVICE, ST.MOTIONS)
        self.assertTrue([m for c, m in errs if c == 'ORDER' and m.startswith('strap must enter before tub')], errs)


    def test_strap_returns_threaded_in_the_base(self):
        # grip route: the strap leaves with the base and returns with it; re-threading with the tub on is impossible
        self.assertIn('never re-thread it with the tub on', ST.SERVICE['grip']['ops'][1]['refit'])
        order = ST.route_refit('grip')
        late = [x for x in order if x != 'strap_thread']
        late.insert(late.index('grip_lock') + 1, 'strap_thread')
        self.assertTrue([m for c, m in ST.lint_refit('grip', order=late) if c == 'ORDER' and 'strap enters' in m])
        svc = copy.deepcopy(ST.SERVICE)
        svc['grip']['ops'][1]['removes'] = list(ST.GRIP)
        svc['grip']['ops'].insert(1, ST.sop('svc_strap_out', 'x', removes=['strap'], reverse_of=['strap_thread']))
        self.assertIn('SERVICE_TRAVEL', codes(ST.lint(copy.deepcopy(ST.STEPS), svc, ST.MOTIONS)))


class Refits(unittest.TestCase):
    def test_lint_clean_and_refit_states_seen(self):
        self.assertEqual(ST.lint(), [])
        phases = {p for p, _r, _o, _s in ST.all_states()}
        self.assertIn('refit', phases)
        gauge = [(r, o) for p, r, o, s in ST.all_states() if p == 'refit' and 'centring_gauge' in s]
        self.assertEqual(sorted({o for _r, o in gauge}), ['collar_tighten', 'gauge_in'])

    def test_every_documented_refit_restores_the_build(self):
        final = set(ST.final_state())
        for r in ST.SERVICE:
            with self.subTest(route=r):
                seq = ST.refit_sequence(r)
                end = set(seq[-1][3]) if seq else set(ST.service_sequence(r)[-1][3])
                self.assertEqual(sorted(final - end - ST.text_refit_ids(r)), [])
                self.assertEqual(sorted(end - final), [])
                self.assertEqual(ST.lint_refit(r), [])
                ops = [o['id'] for _r, o, _b, _a in seq]
                idx = {o['id']: k for k, o in enumerate(ST.STEPS)}
                self.assertEqual(ops, sorted(ops, key=idx.get))               # build order
                if 'pack_in' in ops:
                    self.assertEqual(ops[-2:], ['pack_in', 'cap_on'])         # power last

    def test_superseded_literal_rule_fails(self):
        # Negative control: the old section 5 rule, replayed, breaks the build rules for these routes.
        got = {r: codes(ST.lint_refit(r, order=literal_old_rule(r))) for r in ('module', 'camera', 'collar', 'grip')}
        for r in got:
            self.assertIn('POWER_LAST', got[r], r)
        self.assertIn('REFIT_PRECONDITION', got['collar'])                 # s_c4 / lens_float with no camera or lens
        msgs = ' | '.join(m for _c, m in ST.lint_refit('collar', order=literal_old_rule('collar')))
        self.assertIn("refit collar lens_float: build had ['c_cs_adapter', 'gs_camera', 'lens']", msgs)

    def test_carrier_before_lens_in_a_refit_fails(self):
        order = ST.route_refit('camera')
        k = order.index('module_staged')
        mod = order[k:k + 2]                                   # module_staged, carrier_in
        rest = [x for x in order if x not in mod]
        j = rest.index('camera_in') + 1                        # anchored on camera_in, not on a list position: the
        bad = rest[:j] + mod + rest[j:]                        # refit now opens with the module_bench CSI re-mate
        self.assertEqual(mod, ['module_staged', 'carrier_in'])
        self.assertLess(bad.index('carrier_in'), bad.index('lens_in'))   # VN-41 order: module in before the lens
        c = codes(ST.lint_refit('camera', order=bad))
        self.assertTrue({'ORDER', 'CAMERA_RETAINED'} <= c, c)

    def test_collar_route_without_camera_seats_the_gauge_on_it(self):
        svc = copy.deepcopy(ST.SERVICE)
        svc['collar']['requires'] = ['lens', 'panel']
        errs = ST.lint(copy.deepcopy(ST.STEPS), svc, ST.MOTIONS)
        self.assertIn(('TOOL_COEXIST', "centring_gauge with ['gs_camera', 'c_cs_adapter'] at refit gauge_in"), errs)

    def test_refit_obstacles_reach_the_swept_motions(self):
        t = {m['id']: m for m in ST.motion_table()}
        for mid in ('gauge_out', 'camera_in'):
            self.assertTrue({'evf_board', 'hmx039', 'foam_pad', 'eyepiece', 'eyecup'} <= set(t[mid]['obstacles']), mid)
            self.assertIn('collar', t[mid]['refit_routes'])
        self.assertIn('s_c4', t['camera_in']['refit_only_obstacles'])     # s_c4 stays in its lug during a camera swap
        self.assertTrue({'carrier', 'pi5'} <= set(t['evf_in']['refit_only_obstacles']))


class CameraRetention(unittest.TestCase):
    def test_lens_stays_on_while_the_module_moves(self):
        self.assertEqual(ST.SERVICE['camera']['requires'][-1], 'lens')
        for r in ('camera', 'collar'):
            for rr, o, before, after in ST.service_sequence(r):
                if set(o['removes']) & set(ST.MODULE):
                    self.assertIn('lens', before, (r, o['id']))

    def test_old_camera_order_fails(self):
        svc = copy.deepcopy(ST.SERVICE)
        svc['camera']['requires'] = ['lens', 'panel', 'storage', 'module']
        msgs = [m for c, m in ST.lint(copy.deepcopy(ST.STEPS), svc, ST.MOTIONS) if c == 'CAMERA_RETAINED']
        self.assertIn('service camera svc_carrier_out: the module moves with the camera in and the lens out', msgs)


class LeadSecuring(unittest.TestCase):
    def test_qt_and_j2_free_until_the_panel_goes_in(self):
        self.assertEqual(ST.secured_at('qt'), 'panel_in')
        self.assertEqual(ST.secured_at('j2'), 'panel_in')
        self.assertFalse(ST.secured_before('qt', 'panel_prop'))
        doc = {o['id']: o['doc'] for o in ST.STEPS}
        self.assertIn('Leave the QT and J2 leads FREE', doc['evf_mate'])
        self.assertNotIn('QT, 18/24, J2', doc['evf_mate'])
        self.assertIn('lay the QT and J2 leads into their lanes', doc['panel_in'])

    def test_securing_before_the_prop_mate_fails(self):
        s = copy.deepcopy(ST.STEPS)
        for o in s:
            if o['id'] == 'evf_mate':
                o['secures'] = o['secures'] + ['qt']
            if o['id'] == 'panel_in':
                o['secures'] = ['j2']
        self.assertIn('SECURE_BEFORE_MATE', codes(ST.lint(s, ST.SERVICE, ST.MOTIONS)))


class Docs(unittest.TestCase):
    def block(self, name):
        return re.search(r'<!-- BEGIN:%s -->\n(.*?)<!-- END:%s -->' % (name, name), DOC, re.S).group(1)

    def test_refit_rule_text(self):
        sec = DOC[DOC.index('\n## 5. Service routes'):DOC.index('<!-- BEGIN:service-routes -->')]
        self.assertIn('whole-chain list', sec)
        self.assertNotIn('then the routes it required in reverse', DOC)
        self.assertNotIn('Refit of this route, in build order', DOC)

    def test_documented_refit_lines_are_the_replayed_sequences(self):
        lines = dict(re.findall(r'^\*\*`([a-z]+)`\*\*.*?\n(?:.*\n)*?Refit, whole chain \(this route and every route '
                                r'done first\), in build order: (.*)\.$', self.block('service-routes'), re.M))
        self.assertEqual(sorted(lines), sorted(ST.SERVICE))
        for r, text in lines.items():
            self.assertEqual(re.findall(r'`([a-z0-9_]+)`', text), [o['id'] for _r, o, _b, _a in ST.refit_sequence(r)], r)
        self.assertEqual(MA.route_refit('collar'), ST.route_refit('collar'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
