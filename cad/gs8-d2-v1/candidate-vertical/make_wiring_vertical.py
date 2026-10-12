# SPDX-License-Identifier: MIT
"""Generate WIRING-VERTICAL.md, the wiring specification of the vertical candidate (review 2026-10-10, FP-14, VN-61).

Run from any directory: python path/to/make_wiring_vertical.py [--check]

CAD-free. Every table is generated, nothing is typed twice:
- leads, colours, polarity, junctions, J2 family, spares: wiring_data.py
- plug ops and service partings: steps.py (STEPS, CONNECTIONS, SERVICE)
- stock lengths and tolerances, the pigtail drop model: harness_rules.py (CABLES, PIGTAIL_LENGTH, DROP)
- installed and shortest route lengths: routes.build() + harness_rules.cable_routes_rows (the CAD-free length rule;
  the bound harness report adds exact solid checks, and its row status is quoted with its binding state)
- SKUs: make_bom_vertical.build_rows()
--check exits 1 when WIRING-VERTICAL.md differs from a fresh generation (the final refresh regenerates it after
route changes).
"""
from cv_io import read_text, write_text
from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import steps as ST            # noqa: E402
import harness_rules as HR    # noqa: E402
import routes as R            # noqa: E402
import wiring_data as WD      # noqa: E402

VARIANT = 'compact-kowa_lm6hc'
OUT = HERE / 'WIRING-VERTICAL.md'
REPORT = HERE / 'out' / VARIANT / 'harness-checks.json'
SOURCES = ['wiring_data.py', 'steps.py', 'harness_rules.py', 'routes.py', 'signal_routes.py', 'power_routes.py',
           'make_bom_vertical.py', 'out/%s/harness-checks.json' % VARIANT]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def esc(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')


def fmt(x, n=2):
    return '-' if x is None else format(round(float(x), n), 'g')


def op_step():
    return {o['id']: o['step'] for o in ST.STEPS}


def data():
    import make_bom_vertical as MB
    rows, _, base = MB.build_rows()
    MB.validate(rows, base)
    meta = json.loads(read_text(HERE / 'out' / VARIANT / 'manifest.json'))
    out = R.build()
    H = HR.collect(out, {r['id']: r for r in meta['rows']}, R.L, ST)
    lengths = {r['id']: r for r in HR.cable_routes_rows(H, R.rounded_path)}
    rep = json.loads(read_text(REPORT)) if REPORT.is_file() else None
    state = 'missing'
    if rep is not None:
        changed = sorted(k for k, v in rep.get('verification_dependency_sha256', {}).items()
                         if not (HERE / k).is_file() or sha(HERE / k) != v)
        if rep.get('manifest_sha256') != sha(HERE / 'out' / VARIANT / 'manifest.json'):
            changed.append('manifest')
        if rep.get('verification_source_sha256') != sha(HERE / 'verify_harness_checks.py'):
            changed.append('verify_harness_checks.py')
        state = 'current' if not changed else 'stale (changed since the report: %s)' % ', '.join(changed)
    return dict(bom={r['line']: r for r in rows}, rows=rows, out=out, H=H, lengths=lengths, report=rep,
                report_state=state, drop=HR.pigtail_drop_row())


def mated_at(conn):
    s = op_step()
    if conn is None:
        return 'bench op evf_bench (B4), not a steps.CONNECTIONS cable'
    return '; '.join('%s end on `%s` at `%s` (%s)' % (end, v[0], v[1], s.get(v[1], '?'))
                     for end, v in ST.CONNECTIONS[conn].items() if end != 'doc')


def parted_in(conn):
    hits = ['`%s`/`%s`' % (route, o['id']) for route, r in ST.SERVICE.items() for o in r['ops']
            if conn in o['disconnects']]
    return ', '.join(hits) or 'never parted in a service route'


def report_rows(d, lead):
    if d['report'] is None:
        return 'no harness report'
    ids = set(lead['route_ids']) | {lead['id']}
    mate = {m['id'] for m in HR.MATE_POSES if m['cable'] in ids}
    got = ['%s/%s %s' % (r['category'], r['id'], r['status']) for r in d['report']['checks']
           if r['id'] in ids or r['id'] in mate or (lead['id'] == 'pigtail' and r['id'].startswith('pigtail_'))
           or (r['category'] == 'feed_volumes' and r['id'].startswith(tuple(i + '_' for i in lead['route_ids'])))
           or (r['id'] == 'power_button_j2_pair' and 'power_button' in ids)]   # FX-H: the J2 pair stow row
    return '; '.join(got) or 'no row'


def stock_text(rid):
    if rid in ('pigtail_positive', 'pigtail_negative'):
        return '%s mm finished path per polarity (harness_rules.PIGTAIL_LENGTH; cut to it, G-V-PIGTAIL)' % fmt(HR.PIGTAIL_LENGTH)
    c = HR.CABLES[rid]
    if 'delegated' in c:
        return 'delegated: ' + c['delegated']
    rng = c.get('length_range')
    return '%s mm%s (%s)' % (fmt(c['length']), ' (%s-%s)' % (fmt(rng[0]), fmt(rng[1])) if rng else ', no tolerance',
                             c['range_src'])


def j2_stow_text(d):
    r = next((q for q in (d['report'] or {}).get('checks', []) if q['id'] == 'power_button_j2_pair'), None)
    if r is None:
        return 'no harness row yet (cable_stow/power_button_j2_pair)'
    if r.get('capacity_mm3') is None:
        return 'cable_stow/power_button_j2_pair %s (%s)' % (r['status'], '; '.join(r.get('problems', [])))
    return ('cable_stow/power_button_j2_pair %s: mated pair class %s-%s mm3 + loop %s mm3 = %s-%s mm3 vs capacity %s mm3 '
            '(box %s mm3 x fill %s); provisional class estimate only, not a guaranteed physical upper bound' % (
                r['status'], fmt(r['pair_class_mm3'][0], 0), fmt(r['pair_class_mm3'][1], 0), fmt(r['loop_demand_mm3'], 1),
                fmt(r['demand_range_mm3'][0], 1), fmt(r['demand_range_mm3'][1], 1), fmt(r['capacity_mm3'], 1),
                fmt(r['volume_mm3'], 0), fmt(r['fill_max'])))


def route_text(d, rid):
    r = d['lengths'].get(rid)
    if r is None:
        return 'no route row'
    if r['status'] == 'info':
        return 'see the delegated report'
    if r.get('min_route_mm') is None:
        return 'NO installed route (%s)' % '; '.join(r.get('problems', []))
    return 'installed %s, shortest %s + allowance %s vs minimum stock %s: slack %s mm (length rule %s)' % (
        fmt(r['installed_mm']), fmt(r['min_route_mm']), fmt(r['allowance_mm'], 1), fmt(r['length_min_mm']),
        fmt(r['slack_mm']), r['status'])


def block_diagram():
    return ['```',
            'pack 1S2P --60 mm 18 AWG--> XT30 male | XT30 FEMALE --fuse 15 A (+)--16 AWG red/black--> X1203 battery pads',
            'X1203 (pogo 5.1 V) --> Pi 5 pins 2/4 ............................ Pi 5 (vertical, carrier)',
            'Pi 5 J8 1/3/5/6  --QT lead (sockets / SH 4-pin)-----------------> encoder 5880 (0x37) [panel]',
            'Pi 5 J8 33/34    --donor stubs~Molex PicoBlade pair-------------> CK1044 18/24 (common A, throw 2) [carrier]',
            'Pi 5 J8 37/39    <--pre-wired run lead--------------------------- run button [grip]',
            'Pi 5 J2 pads     --J2 keyed pair (' + WD.J2_DEFAULT['family_key'] + ')---------> Adafruit 1505 NO [panel]',
            'Pi 5 upper USB2  --4448 red/black--1N5817 (+, band to EVF)--RCY 2180|2181--> EVF board EXT+/GND',
            'Pi 5 HDMI0       --3557 head~3562 ribbon 300 mm~3556 head--------> EVF board receptacle',
            'Pi 5 CAM/DISP 1  --official 200 mm FPC--------------------------> GS camera (Pi end BEFORE cooler)',
            'Pi 5 FAN         --native lead----------------------------------> Active Cooler',
            'Pi 5 upper USB3  <-- recording drive (storage, not a harness)',
            '```']


def generate(d):
    bom, s = d['bom'], op_step()
    j2 = WD.J2_DEFAULT
    md = ['# Vertical candidate: wiring specification', '',
          '<!-- Generated by make_wiring_vertical.py (FP-14, review VN-61). Do not edit by hand; edit the sources and '
          'regenerate, then run with --check. -->', '',
          '**Unqualified review candidate. Nothing here is bought, built or measured.** Lengths are route-model and '
          'purchase-requirement figures, not cut instructions; every open item names its gate.', '',
          'For this fork this file supersedes the baseline (r7) `electronics/gs8-d2-v1/WIRING.md` sections 2 (block '
          'diagram), 5 (header), 6 (cables) and 7 (plug order): the r7 file still describes the printed plunger, a '
          'JST PH pigtail and a PH EVF plug that the candidate does not buy. Still in force from r7: section 4 (power '
          'path, pack and current budget), section 8 (Pi configuration) and section 9 (bench gates). USB ports in this '
          'candidate: recording drive in the upper USB3 port (steps.py `storage_in`), EVF feed in the upper USB2 port '
          '(routes.py usb_5v note, official_pi5_geometry.py).', '',
          'Generated from: ' + ', '.join('`%s`' % x for x in SOURCES) + '. Harness report '
          '`out/%s/harness-checks.json`: %s.' % (VARIANT, d['report_state']), '']
    if 'corrected lower USB2' in read_text(HERE / 'routes.py'):
        md += ['Port naming note: a superseded-route error message in routes.py still says "corrected lower USB2"; '
               'the geometry and the usb_5v note use the upper USB2 port. Fix the message when the usb_5v route is '
               're-solved (FP-11f / VN-60).', '']
    md += ['## 1. Block diagram', ''] + block_diagram() + ['']
    md += ['## 2. Pi 5 header (J8), J2 and I2C', '',
           '| Pin | Signal | Connected to | Lead | Header housing |', '|---|---|---|---|---|']
    hs = {p: h['id'] for h in d['out']['header_housings'] for p in h['pins']}
    md += ['| %s | %s | %s | `%s` | `%s` |' % (p, sig, esc(to), lead, hs.get(p, '-')) for p, sig, to, lead in WD.HEADER]
    md += ['', 'All other J8 pins are free; GPIO6 / GPIO16 stay reserved for the X1203 (r7 W-2). Single 1-pin '
           'housings, seated with open tweezer tips and tug-tested (r7 G-HDR-1).', '',
           '| J2 pad | Signal | Connected to | Lead |', '|---|---|---|---|',
           '| J2 (one pad) | PWR_BUT | Adafruit 1505 terminal via the J2 pair | `power_button` |',
           '| J2 (other pad) | GND | Adafruit 1505 terminal via the J2 pair | `power_button` |', '',
           'Pad identity, position under the cooler and solder access are G-V-POWER (VN-73); the 1505 is in parallel '
           'with the onboard button (same semantics, never battery isolation).', '',
           'I2C bus 1: 0x36 X1203 fuel gauge (pogo); 0x37 Adafruit 5880 encoder with A0 bridged.', '']
    md += ['## 3. Junctions (wire-to-wire pairs)', '',
           'Rule (VN-63): no two junctions share a mating family, whatever the circuit count. Checked from the BOM rows '
           'by `make_bom_vertical.validate` and tests/test_wiring_bom.py. Shared families now: %s.' % (
               ', '.join('%s+%s' % p[:2] for p in WD.shared_family_pairs(d['rows'])) or 'none'), '',
           '| Junction | BOM | Family (from the BOM SKU) | Sides | Carries | Mated | Parted in service |',
           '|---|---|---|---|---|---|---|']
    for j in WD.JUNCTIONS:
        md.append('| `%s` | %s | %s | %s | %s | %s | %s |' % (
            j['id'], j['bom'], WD.junction_family(bom[j['bom']]['sku_or_class']), esc('; '.join(j['sides'])),
            esc(j['carries']), esc(mated_at(j['id'])), parted_in(j['id'])))
    md += ['', '### J2 connector family (%s)' % WD.J2_DECISION, '',
           '- Default: **%s**, chosen because %s. It replaces the 9ced753 J2 pair, which was the same unkeyed Molex '
           'PicoBlade family as the FPS junction. BOM V-28 (spare V-28S).' % (j2['family'], j2['why']),
           '- Genders: %s; %s.' % (j2['pi_side'], j2['switch_side']),
           '- Leads: each pre-crimped lead >= %s mm exposed; %s.' % (fmt(j2['lead_min_mm']), j2['lead_min_src']),
           '- Gate: %s.' % j2['gate']]
    md.append('- Criterion for user decision 13 / G-V-POWER: the chosen J2 family must fit the J2 stow space '
              '(routes.py power_stow, using the provisional modeled class envelope, not an established physical upper bound): '
              + j2_stow_text(d) + '.')   # FX-H (verifier D1 minor)
    md += ['- Source conflict: the existing 7.5 x 11 x 20 mm class proxy does not bound every Micro-Fit pair. The official 430250200 drawing gives 24.77 mm mated length for a compatible housing proposal; exact SKU, full envelope, roots and stow remain unqualified. This sourcing proposal is not an adopted substitution. [Molex drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/430/43025/430250200_sd.pdf).']
    md += ['- Micro-Fit root gate: Molex application specification 430450001-AS recommends 12.7 mm of free, unbiased wire from each 2–6-circuit housing before a bend, tie or twist. For the 24.77 mm housing proposal, an axial 50.17 mm overall reservation is a study assumption, not a fit result. Generic 3 mm modeled tails do not satisfy this physical gate. Latch travel and finger/tool volume remain unknown. [Molex application specification](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/applicationspecificationspdf/430/43045/430450001-AS-000.pdf).']
    md += ['- Alternative: %s (family `%s`): %s.' % a for a in WD.J2_ALTERNATIVES]
    md += ['', '## 4. Harness schedule (every lead, both ends)', '']
    for lead in WD.LEADS:
        md += ['### `%s`' % lead['id'], '', '| Field | Value |', '|---|---|',
               '| End A | %s |' % esc(lead['a']), '| End B | %s |' % esc(lead['b']),
               '| Conductors and colours | %s |' % esc(lead['conductors']),
               '| Polarity | %s |' % esc(lead['polarity']),
               '| BOM | %s |' % esc('; '.join('%s %s (%s)' % (l, bom[l]['item'], bom[l]['sku_or_class']) for l in lead['bom']))]
        for rid in lead['route_ids']:
            md += ['| Stock `%s` | %s |' % (rid, esc(stock_text(rid))), '| Route `%s` | %s |' % (rid, esc(route_text(d, rid)))]
            if rid == 'usb_5v':   # FX (verifier H1/D1 minor): the summed stock is not the binding figure; each segment is
                seg = [r for r in (d['report'] or {}).get('checks', []) if r['category'] == 'feed_volumes'
                       and r.get('slack_mm') is not None]
                for r in seg:
                    md.append('| Segment `%s` | stock %s mm, allowance %s mm: slack %s mm (feed_volumes/%s %s) |' % (
                        r['id'], fmt(r['stock_mm']), fmt(r['allowance_mm'], 1), fmt(r['slack_mm']), r['id'], r['status']))
                if seg:
                    w = min(seg, key=lambda r: r['slack_mm'])
                    md.append('| Binding segment | `%s`, slack %s mm (the summed 500 mm stock above is not the binding '
                              'figure: each segment is cut from its own stock) |' % (w['id'], fmt(w['slack_mm'])))
        md += ['| Mated | %s |' % esc(mated_at(lead['connection'])),
               '| Parted in service | %s |' % (parted_in(lead['connection']) if lead['connection'] else 'bench only'),
               '| Harness report rows | %s |' % esc(report_rows(d, lead)), '']
    lo = 2 * j2['lead_min_mm']
    rng = HR.CABLES['power_button']['length_range']
    md += ['J2 length note: the harness check assumes %s-%s mm per conductor (%s); the V-28 default buys >= %s mm per '
           'conductor, so the check stays a lower bound of what is bought.' % (fmt(rng[0]), fmt(rng[1]),
                                                                             HR.CABLES['power_button']['range_src'], fmt(lo)), '']
    md += ['### QT stored material versus mating reach', '',
           'The installed route must store the entire finished 250 +/- 10 mm QT lead, including every branch and '
           'the four insulated splices. Length variants and their rigid-surface checks are separate from the free '
           'curve used at the propped panel. The free curve plus the explicit 24 mm assembly allowance is a minimum '
           'reach budget; it is not an extra 24 mm to add to the finished lead and is not a complete stored shape. '
           'A reach pass cannot certify slack storage or the continuous transition from the prop pose to closure. '
           'Actual roots, sleeves, tie/head geometry, bend limits and full flexible motion remain HOLD.', '',
           '### Camera and other flexible ribbons', '',
           'Seat the official 200 mm camera cable Pi end before fitting the Active Cooler, following the '
           '[Raspberry Pi camera instructions](https://www.raspberrypi.com/documentation/accessories/camera.html). '
           'Support the complete Pi module outside the body and mate the camera end immediately before camera '
           'insertion. The entire linked ribbon is absent from the rigid camera/carrier sweeps; source-level '
           '`steps.flexible_scope()` records this omission. Actual latch service with the cooler retained remains '
           'HOLD. Do not repeatedly remove the cooler to make an unqualified service path appear feasible.', '',
           'The complete 300 mm HDMI ribbon, 200 mm camera FPC and native OLED flex must retain their actual '
           'width, thickness, stiffeners and contact orientation. Manufacturer bend-radius and flex-cycle '
           'limits for these exact cables remain UNKNOWN; round clearance reserves and connector mating-cycle '
           'ratings are not cable flex qualifications. Retain full-length stored and service-motion checks, '
           'continuity, video operation and fatigue gates. Baseline source evidence is in '
           '[the 12 October materials and ribbons research](corrective-2026-10-12/materials-and-ribbons-baseline-evidence.txt); '
           'it needs an applicability check after geometry changes.', '']
    md += ['## 5. Polarity and colour rules', '']
    md += ['- `%s`: %s' % (lead['id'], lead['polarity']) for lead in WD.LEADS]
    md += ['- Socket (female) contacts on the live or source side of every inline pair: EVF 2180 on the USB side, J2 '
           'receptacle on the Pi side, XT30 FEMALE on the camera (battery-source) side of the pigtail.',
           '- Never identify a conductor by colour alone where both cores are black (FPS Molex leads) or colours are '
           'not recorded: continuity-test end to end and label both housings.', '']
    md += ['## 6. Plug order (build)', '', 'From steps.STEPS; each end is mated once, at the op listed. Power last.', '',
           '| Step | Op | Where | Mates |', '|---|---|---|---|']
    for o in ST.STEPS:
        if o['connects']:
            md.append('| %s | `%s` | %s | %s |' % (o['step'], o['id'], o['where'], ', '.join(
                '`%s` (%s)' % (c, ST.CONNECTIONS[c.split(':')[0]][c.split(':')[1]][0]) for c in o['connects'])))
    md += ['', '## 7. Unplug order (service)', '',
           'From steps.SERVICE; a route runs after the routes it requires (section 1 safety first: pack out, XT30 '
           'parted). Refit is the reverse.', '', '| Route | Requires | Parts in order |', '|---|---|---|']
    for route, r in ST.SERVICE.items():
        parts = ['`%s`: %s' % (o['id'], ', '.join(o['disconnects'])) for o in r['ops'] if o['disconnects']]
        md.append('| `%s` | %s | %s |' % (route, ' -> '.join(ST.route_closure(route)[:-1]) or '-', '; '.join(parts) or 'none'))
    dr = d['drop']
    md += ['', '## 8. Battery pigtail drop (G-W5)', '',
           'harness_rules.pigtail_drop_row at %s A, limit %s V (never relaxed): low %s V, high %s V, status %s. '
           'Decision data (%s): shortest-path limit %s mm (hot fuse) / %s mm (cold fuse); cut-off raise needed %s V. '
           'This remains user decision 4. The 270 mm allocation is blocked by reach and hot-drop; proposals remain pending. No 14 AWG, fuse, connector or cutoff substitution is adopted.' % (
               fmt(dr['i_peak_a'], 1), fmt(dr['limit_v'], 3), fmt(dr['drop_lo_v'], 5), fmt(dr['drop_hi_v'], 5),
               dr['status'], dr['decision_data']['options'], fmt(dr['decision_data']['shorter_path_max_mm_hot_fuse'], 1),
               fmt(dr['decision_data']['shorter_path_max_mm_cold_fuse'], 1), fmt(dr['decision_data']['cutoff_raise_needed_v'], 5)), '']
    failing = d['report']['failing'] if d['report'] else {}
    md += ['## 9. Open items', '',
           '- J2 connector family: %s (VN-63).' % WD.J2_DECISION,
           '- V-62 deep socket purchase: gated on %s.' % WD.GATED['V-62'][0],
           '- Harness rows failing in the bound report: %s.' % ('; '.join('%s: %s' % (k, ', '.join(v)) for k, v in sorted(failing.items())) or 'none'),
           '- Lengths are regenerated from the route sources; the final refresh (FP-16) regenerates this file after '
           'the route and harness lanes land.', '']
    return '\n'.join(md)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    text = generate(data())
    if a.check:
        if not OUT.is_file() or read_text(OUT) != text:
            raise SystemExit('Stale output: WIRING-VERTICAL.md')
        print('WIRING-VERTICAL.md current')
        return
    write_text(OUT, text)
    print('wrote', OUT.name)


if __name__ == '__main__':
    main()
