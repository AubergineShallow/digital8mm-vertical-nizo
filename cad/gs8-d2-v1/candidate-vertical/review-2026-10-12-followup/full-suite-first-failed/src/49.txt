# SPDX-License-Identifier: MIT
"""Wiring, BOM and routes agree (review 2026-10-10, FP-14: VN-61, VN-63, VN-64).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_wiring_bom.py

- Generated outputs are current: WIRING-VERTICAL.md, BOM-VERTICAL.md/.csv, BUY-VERTICAL.csv.
- Wiring vs steps.py: every cable end and its plug op/step, the build plug order and every service parting.
- Wiring vs route sources: every harness_rules cable and pigtail core is in exactly one lead, with the stock length
  and the route lengths recomputed CAD-free; header pins equal the r7 layout, the route header housings and r7
  pi5-header.csv.
- Wiring vs BOM: every lead's BOM lines and SKUs; J2 lead requirement covers what the harness check assumes.
- Junctions: no two junctions share a mating family; the 9ced753 BOM (J2 = FPS PicoBlade) fails, and so does a
  fixture with the old J2 SKU.
- Buy view: duplicate SKUs are summed, class rows never merge, the CSV equals the view; spares, black wire SKU,
  gated V-62.
"""
import copy
import csv
import io
import re
import sys
import unittest
from pathlib import Path

CV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CV))
sys.path.insert(0, str(CV.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_io import read_text        # noqa: E402
import wiring_data as WD           # noqa: E402
import steps as ST                 # noqa: E402
import harness_rules as HR         # noqa: E402
import routes as R                 # noqa: E402
import make_bom_vertical as MB     # noqa: E402
import make_wiring_vertical as MW  # noqa: E402
from _repo_git import git, CV as CV_REL  # noqa: E402

_C = {}


def D():
    if 'd' not in _C:
        _C['d'] = MW.data()
        _C['md'] = MW.generate(_C['d'])
    return _C['d'], _C['md']


def rows():
    r, _, base = MB.build_rows()
    MB.validate(r, base)
    return r, base


def section(md, title):
    m = re.search(r'^### `%s`\n(.*?)(?=^### |^## |\Z)' % re.escape(title), md, re.S | re.M)
    return m.group(1)


class Generated(unittest.TestCase):
    def test_cad_free(self):
        D()
        self.assertNotIn('cadquery', sys.modules)

    def test_wiring_current(self):
        self.assertEqual(read_text(CV / 'WIRING-VERTICAL.md'), D()[1],
                         'WIRING-VERTICAL.md is stale: run make_wiring_vertical.py')

    def test_bom_outputs_current(self):
        r, base = rows()
        for name, text in MB.outputs(r, base).items():
            self.assertEqual(read_text(CV / name), text, name)


class WiringVsSteps(unittest.TestCase):
    def test_every_cable_end_and_plug_op(self):
        _, md = D()
        steps = {o['id']: o['step'] for o in ST.STEPS}
        covered = {l['connection'] for l in WD.LEADS} | {j['id'] for j in WD.JUNCTIONS}
        self.assertEqual(set(ST.CONNECTIONS) - covered, set(), 'cable without a lead in wiring_data.LEADS')
        for lead in WD.LEADS:
            if not lead['connection']:
                continue
            sec = section(md, lead['id'])
            for end, v in ST.CONNECTIONS[lead['connection']].items():
                if end == 'doc':
                    continue
                self.assertIn('%s end on `%s` at `%s` (%s)' % (end, v[0], v[1], steps[v[1]]), sec, lead['id'])

    def test_plug_order_is_steps_order(self):
        _, md = D()
        table = md.split('## 6. Plug order (build)')[1].split('## 7.')[0]
        got = re.findall(r'^\| (\S+) \| `(\w+)` \|', table, re.M)
        want = [(o['step'], o['id']) for o in ST.STEPS if o['connects']]
        self.assertEqual(got, want)
        last = [o for o in ST.STEPS if o['connects']][-1]
        self.assertEqual(last['connects'], ['xt30:pack'], 'power last')

    def test_every_service_parting_listed(self):
        _, md = D()
        table = md.split('## 7. Unplug order (service)')[1].split('## 8.')[0]
        for route, r in ST.SERVICE.items():
            line = next(l for l in table.splitlines() if l.startswith('| `%s` |' % route))
            for o in r['ops']:
                if o['disconnects']:
                    self.assertIn('`%s`: %s' % (o['id'], ', '.join(o['disconnects'])), line)


class WiringVsRoutes(unittest.TestCase):
    def test_every_cable_in_one_lead_with_lengths(self):
        d, md = D()
        ids = [rid for l in WD.LEADS for rid in l['route_ids']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(d['H']['cables']), 'harness_rules cables vs wiring leads')
        for lead in WD.LEADS:
            sec = section(md, lead['id'])
            for rid in lead['route_ids']:
                self.assertIn('| Stock `%s` | %s |' % (rid, MW.esc(MW.stock_text(rid))), sec)
                r = d['lengths'][rid]
                if r.get('min_route_mm') is not None:
                    want = 'installed %s, shortest %s + allowance %s vs minimum stock %s: slack %s mm' % (
                        MW.fmt(r['installed_mm']), MW.fmt(r['min_route_mm']), MW.fmt(r['allowance_mm'], 1),
                        MW.fmt(r['length_min_mm']), MW.fmt(r['slack_mm']))
                    self.assertIn(want, sec, rid)
                elif r['status'] == 'fail':
                    self.assertIn('NO installed route', sec, rid)

    def test_route_lengths_follow_the_route_source(self):
        # A route change moves the generated text: shorten the QT top loop and the schedule must differ.
        d, md = D()
        d2 = copy.deepcopy(d)
        d2['lengths']['qt']['installed_mm'] -= 10.0
        self.assertNotEqual(MW.generate(d2), md)

    def test_header_pins(self):
        d, _ = D()
        used = {}
        for p, _sig, _to, lead in WD.HEADER:
            used.setdefault(lead, []).append(p)
        self.assertEqual({k: tuple(v) for k, v in used.items()}, dict(R.L.HDR_USED_PINS))
        route_pins = {}
        for h in d['out']['header_housings']:
            route_pins.setdefault(h['cable'], []).extend(h['pins'])
        self.assertEqual({k: sorted(v) for k, v in route_pins.items()}, {k: sorted(v) for k, v in used.items()})
        r7 = {}
        for row in csv.DictReader(io.StringIO(read_text(CV.parents[2] / 'electronics/gs8-d2-v1/pi5-header.csv'))):
            for p in re.findall(r'\d+', row['pin']):
                r7[int(p)] = row['signal']
        for p, sig, _to, _lead in WD.HEADER:
            self.assertEqual(sig, r7[p], p)


class WiringVsBOM(unittest.TestCase):
    def test_lead_bom_lines_and_skus(self):
        d, md = D()
        for lead in WD.LEADS:
            sec = section(md, lead['id'])
            for line in lead['bom']:
                self.assertIn(line, d['bom'], line)
                self.assertIn('%s %s (%s)' % (line, d['bom'][line]['item'], d['bom'][line]['sku_or_class']),
                              sec.replace('\\|', '|'))

    def test_j2_purchase_covers_the_harness_assumption(self):
        j2 = WD.J2_DEFAULT
        mp = next(m for m in HR.MATE_POSES if m['id'] == 'j2_btn')
        self.assertEqual(len(mp['halves']), 2)
        for _name, length, tol in mp['halves']:
            self.assertGreaterEqual(j2['lead_min_mm'], length + tol)
        self.assertGreaterEqual(2 * j2['lead_min_mm'], HR.CABLES['power_button']['length_range'][1])
        r, _ = rows()
        by = {x['line']: x for x in r}
        self.assertIn('>= %g mm' % j2['lead_min_mm'], by['V-28']['sku_or_class'])
        self.assertEqual(by['I-28C']['installed_qty'] + by['I-28D']['installed_qty'], 4)


class Junctions(unittest.TestCase):
    def test_no_shared_family_now(self):
        r, _ = rows()
        self.assertEqual(WD.shared_family_pairs(r), [])
        by = {x['line']: x for x in r}
        fams = [WD.junction_family(by[j['bom']]['sku_or_class']) for j in WD.JUNCTIONS]
        self.assertNotIn(None, fams)
        self.assertEqual(WD.junction_family(by['V-28']['sku_or_class']), WD.J2_DEFAULT['family_key'])

    def test_old_j2_sku_fails(self):
        r, _ = rows()
        bad = copy.deepcopy(r)
        next(x for x in bad if x['line'] == 'V-28')['sku_or_class'] = 'Molex 2181120201 + 2181110202 (one of each)'
        self.assertEqual(WD.shared_family_pairs(bad), [('fps_1824', 'j2', 'molex-picoblade-1.25')])
        with self.assertRaises(AssertionError):
            MB.validate_fp14(bad)
        unknown = copy.deepcopy(r)
        next(x for x in unknown if x['line'] == 'V-28')['sku_or_class'] = 'class; confirm on receipt'
        self.assertEqual(WD.shared_family_pairs(unknown), [('j2', None, None)], 'an unidentified family must not pass')
        last = [j for j in WD.JUNCTIONS if j['id'] != 'xt30'] + [j for j in WD.JUNCTIONS if j['id'] == 'xt30']
        unknown_last = copy.deepcopy(r)
        next(x for x in unknown_last if x['line'] == 'D2-14')['sku_or_class'] = 'class'
        self.assertEqual(WD.shared_family_pairs(unknown_last, last), [('xt30', None, None)], 'also when listed last')

    def test_negative_control_9ced753(self):
        raw = git('show', '9ced753:' + CV_REL + 'BOM-VERTICAL.csv').decode('utf-8')
        old = list(csv.DictReader(io.StringIO(raw)))
        self.assertEqual(WD.shared_family_pairs(old), [('fps_1824', 'j2', 'molex-picoblade-1.25')])


class BuyView(unittest.TestCase):
    def test_duplicate_skus_summed(self):
        r, _ = rows()
        by = {x['line']: x for x in r}
        view = {g['sku']: g for g in MB.buy_view(r, 'compact')}
        for sku, lines in [('Pololu 2180', ('D2-23', 'V-23S')), ('Molex 2181110202', ('D2-27', 'V-27S')),
                           ('Adafruit 3562', ('V-22O', 'V-22OS'))]:
            self.assertEqual(view[sku]['qty'], sum(by[l]['purchase_qty'] for l in lines), sku)
            self.assertEqual(sorted(l for l, _ in view[sku]['lines']), sorted(lines))

    def test_fixture_rows(self):
        base = dict(section='B', item='x', variant='both', installed_qty=0, installed_unit='ea', purchase_unit='ea',
                    included_in='', supplier='S', spare_or_remainder='', status='', layout_id='', note='', source='')
        fx = [dict(base, line='X-1', sku_or_class='ACME 1', purchase_qty=2),
              dict(base, line='X-2', sku_or_class='ACME 1', purchase_qty=3),
              dict(base, line='X-3', sku_or_class='class', purchase_qty=1),
              dict(base, line='X-4', sku_or_class='class', purchase_qty=1),
              dict(base, line='X-5', sku_or_class='ACME 1', purchase_qty=4, included_in='X-1')]
        view = MB.buy_view(fx, 'compact')
        acme = [g for g in view if g['sku'] == 'ACME 1']
        self.assertEqual(len(acme), 1)
        self.assertEqual(acme[0]['qty'], 5, 'summed, included rows excluded')
        self.assertEqual(len([g for g in view if 'class' in g['sku']]), 2, 'class rows never merge')

    def test_csv_equals_view_and_every_purchase_is_bought(self):
        r, _ = rows()
        got = list(csv.DictReader(io.StringIO(read_text(CV / 'BUY-VERTICAL.csv'))))
        for v in ('compact', 'original'):
            view = {g['sku']: g['qty'] for g in MB.buy_view(r, v)}
            self.assertEqual({x['sku']: int(x[v + '_qty']) for x in got if x['sku'] in view}, view)
            seen = {l for g in MB.buy_view(r, v) for l, _ in g['lines']}
            want = {x['line'] for x in r if not x['included_in'] and x['purchase_qty']
                    and x['variant'] in ('both', v + ' only')}
            self.assertEqual(want - seen, set())

    def test_spares_wire_and_gate(self):
        r, _ = rows()
        by = {x['line']: x for x in r}
        for s in WD.SPARES:
            self.assertGreaterEqual(by[s['line']]['purchase_qty'], 1)
            self.assertEqual(by[s['line']]['installed_qty'], 0)
        self.assertEqual({s['parent'] for s in WD.SPARES} >= {'D2-23', 'D2-27', 'V-22O'}, True)
        self.assertIn('SW-16B', by['D2-26']['sku_or_class'])
        self.assertIn('SW-16R', by['D2-26']['sku_or_class'])
        self.assertIn('PRC SW-16B', read_text(CV / 'BUY-VERTICAL.csv'))
        self.assertEqual(by['V-62']['purchase_qty'], 0)
        self.assertIn('across-flats', read_text(CV / 'MEASUREMENTS-TO-CLOSE.md').split('Adafruit 1505 power switch')[1].split('\n')[0])
        bad = copy.deepcopy(r)
        next(x for x in bad if x['line'] == 'V-62')['purchase_qty'] = 1
        with self.assertRaises(AssertionError):
            MB.validate_fp14(bad)


class Docs(unittest.TestCase):
    def test_supersession_links_and_text(self):
        _, md = D()
        self.assertIn('supersedes the baseline (r7) `electronics/gs8-d2-v1/WIRING.md`', md)
        self.assertIn('upper USB2 port', md)
        quoted = [l for l in md.splitlines() if 'lower USB2' in l]
        for line in quoted:   # only the note, or the routes.py error it flags, quoted verbatim in the usb_5v route row
            self.assertTrue(line.startswith('Port naming note:') or line.startswith('| Route `usb_5v` |'), line)
        if quoted:
            self.assertTrue(any(l.startswith('Port naming note:') for l in quoted))
        self.assertIn('cathode band toward the EVF board', md)
        self.assertIn('XT30U FEMALE', md)
        for doc in ('ASSEMBLY-VERTICAL.md', 'REVIEW.md'):
            self.assertIn('](WIRING-VERTICAL.md)', read_text(CV / doc), doc)
        asm = read_text(CV / 'ASSEMBLY-VERTICAL.md')
        for phrase in ('within qualified lanes', 'Prepare the baseline EVF feed', 'Molex 2181120201/2181110202'):
            self.assertNotIn(phrase, asm)

    def test_export18_claim_and_changes(self):
        r, base = rows()
        text = MB.outputs(r, base)['BOM-VERTICAL.md']
        diffs = MB.export18_differences(r)
        self.assertTrue(diffs)
        self.assertNotIn('every purchased selection/quantity are unchanged from reviewed export18', text)
        listed = text.split('## Purchase changes against reviewed export18')[1].split('## ')[0]
        self.assertEqual(re.findall(r'^- (\S+):', listed, re.M), [x[0] for x in diffs])


if __name__ == '__main__':
    unittest.main(verbosity=2)
