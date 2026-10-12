# SPDX-License-Identifier: MIT
"""FP-12 check-scope rows (review 2026-10-10). Run through ../run_locked.py; batch row `check_scope`.

Categories (all manifest-bound; failures are reported, never waived; exit 1 when any row fails):
  j4_screen          VN-33  per-variant J4 coupon screen (first-moment transfer) vs the supplement's stated screen
  area_parity        VN-37  per branch min(mouth neck, series sections) vs the wall ports, from the saved tub STEP;
                            FX: plus the path-aware min cut port set -> mouth set per bay (plenum_flow.py, gate)
  flow_network       VN-36  report-only orifice network with occlusion cases (fan curve unknown; CSI plug = user)
  hdmi_face          VN-35  conductor-face normal carried along the selected HDMI route; head contact sides HOLD
  evf_restraint      VN-34  r7 checks.check_evf_restraint, unchanged, on the candidate EVF (8 rows) + control
  evf_face           VN-34  EVF axis/flange r7 vs candidate side by side and eye/face no-regression screens
  stack_retention    VN-38  r7 check_stack_retention rules on the vertical carrier (r7 _hull2/_inside_margin/_max_lift);
                            declared locators credited only from the bound STEPs (check_scope.locator_point, FP-11c)
  post_root_bending  VN-38  carrier-post root bending screen, post section measured from the saved tub STEP
Writes out/<variant>/check-scope-checks.json (or --out).
"""
from cv_io import read_text, relpath_posix, write_text
import argparse, hashlib, json, math, sys
from pathlib import Path

CV = Path(__file__).resolve().parent
R7 = CV.parent
for _p in (str(R7), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import check_scope as CS          # noqa: E402
import evidence_rules as ER       # noqa: E402
import steps as ST                # noqa: E402

CATS = ['j4_screen', 'area_parity', 'flow_network', 'hdmi_face', 'evf_restraint', 'evf_face', 'stack_retention',
        'post_root_bending']
HDMI_SNAPSHOT = CV / 'routing-snapshots/hdmi-export17-selected-20261009-0704/input.json'   # run_shadow_checks 'hdmi'
REF_MANIFEST = CV / 'history/reviewed-export18/manifest.json'
STRUCT_REF = CV / 'structural-review/reference-export18-structural-binding.json'
STRUCT_OUT = CV / 'structural-review/concealed-vent-structural.json'
R7_PARTS = R7 / 'out/parts-manifest.json'
R7_CHECKS = R7 / 'out/checks.json'
FLOW_BASELINE = CV / 'review-2026-10-10/fp12/flow-network-baseline.json'   # fixup-1 (VN-36) regression pin
# FX (verifier T1 minor): one baseline per variant (a variant without its own baseline fails the drift row; it never
# compares against another variant's numbers)
FLOW_BASELINES = {'compact-kowa_lm6hc': FLOW_BASELINE}


def flow_baseline(variant):
    return FLOW_BASELINES.get(variant, CV / ('review-2026-10-10/fp12/flow-network-baseline-%s.json' % variant))
STACK = ['carrier', 'pi5', 'x1203', 'x1203_kit', 'cooler', 'microsd']   # rigid on the carrier (switch is panel-nutted)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(p):
    return json.loads(read_text(p))


ap = argparse.ArgumentParser()
ap.add_argument('--variant', default='compact-kowa_lm6hc')
ap.add_argument('--categories', default=','.join(CATS))
ap.add_argument('--out', default='')
a = ap.parse_args()
cats = [c for c in a.categories.split(',') if c]
if set(cats) - set(CATS):
    raise SystemExit('unknown category: %s' % sorted(set(cats) - set(CATS)))
if cats != CATS and not a.out:
    raise SystemExit('a partial run needs --out')
D = CV / 'out' / a.variant
MF = D / 'manifest.json'
mh = sha(MF)
man = rd(MF)
mrows = {r['id']: r for r in man['rows']}
length = float(man['core_dimensions_mm'][0])
checks, inputs = [], {}


def add(cat, ident, ok=None, **kw):
    r = dict(category=cat, id=ident, status='info' if ok is None else ('pass' if ok else 'fail'), **kw)
    checks.append(r)
    print(json.dumps({k: r[k] for k in ('category', 'id', 'status')}), flush=True)


def bind(p):
    inputs[relpath_posix(p, CV.parent)] = sha(p)  # VN-10: relative POSIX key even outside cad/gs8-d2-v1 (was str(p), absolute)


_step_cache = {}


def step(name):
    if name not in _step_cache:
        import cadquery as cq
        p = D / 'step' / ('%s.step' % name)
        if sha(p) != man['files']['step/%s.step' % name]:
            raise ValueError('STEP binding mismatch: ' + name)
        _step_cache[name] = cq.importers.importStep(str(p)).val()
    return _step_cache[name]


# ------------------------------------------------------------------------------------------- VN-33
if 'j4_screen' in cats:
    ref, old = rd(STRUCT_REF), rd(REF_MANIFEST)
    for p in (STRUCT_REF, REF_MANIFEST, STRUCT_OUT):
        bind(p)
    per = {}
    import cadquery as cq

    def _centre(p):
        c = cq.importers.importStep(str(p)).val().Center()
        return (c.x, c.y, c.z)
    for mp in sorted((CV / 'out').glob('*/manifest.json')):
        m = rd(mp)
        if 'rows' in m and 'storage' in m:
            # FX (verifier C2 major): the lower rows' first moments from the variant's bound STEPs give a new free body
            # when a lower row changed (check_scope.j4_direct); otherwise the transfer and the direct value are compared
            lf = CS.lower_first_moments(m, mp.parent, _centre, sha)
            per[mp.parent.name] = CS.j4_screen(ref, old, m, ER.changed_rows, lower_first=lf)
            per[mp.parent.name]['manifest_sha256'] = sha(mp)
    env = CS.j4_envelope(per)
    sup = rd(STRUCT_OUT).get('coupon_load', {})
    stated = sup.get('all_variants_screen_Nm')
    for v, r in per.items():
        ok = r['valid'] and stated is not None and stated + 1e-12 >= r['equal_share_plus_wiring_Nm']
        add('j4_screen', v, ok, stated_supplement_screen_Nm=stated, compact_screen_Nm=CS.J4_COMPACT_SCREEN_NM,
            covered_by_compact_screen=bool(r.get('valid')) and CS.J4_COMPACT_SCREEN_NM + 1e-12 >= r['equal_share_plus_wiring_Nm'],
            **r)
    add('j4_screen', 'envelope', stated is not None and abs(stated - (env['all_variants_screen_Nm'] or -1)) < 1e-12,
        computed=env, stated_supplement_screen_Nm=stated,
        note='The supplement must state the screen that covers every variant (VN-33); the 0.95 N m compact value '
             'covers only the variants listed in compact_screen_covers. The 70 percent rows stay separate cases.')

# ------------------------------------------------------------------------------------------- VN-37 / VN-36
el = None
if 'area_parity' in cats or 'flow_network' in cats:
    import cadquery as cq
    V = cq.Vector
    tub = step('tub')

    def rect(axis, pos, u0, u1, v0, v1):
        pt = lambda u, v: {'x': (pos, u, v), 'y': (u, pos, v), 'z': (u, v, pos)}[axis]  # noqa: E731
        ps = [pt(u0, v0), pt(u1, v0), pt(u1, v1), pt(u0, v1)]
        return cq.Face.makeFromWires(cq.Wire.makePolygon([V(*p) for p in ps + ps[:1]]))

    def free(axis, pos, u0, u1, v0, v1):     # verify_shadow_plenum.free_section, same Boolean
        f = rect(axis, pos, u0, u1, v0, v1).cut(tub).Area()
        assert -1e-6 <= f <= (u1 - u0) * (v1 - v0) + 1e-5, 'Invalid section Boolean area'
        return f

    def frange(x0, x1, dx):
        n = int(math.floor((x1 - x0) / dx + 1e-9))
        return [round(x0 + i * dx, 6) for i in range(n + 1)]
    ports = {'cold': sum(free('y', -26.75, -103., -68., z, z + 3.) for z in (18., 24., 30., 36.)),
             'hot': sum(free('y', -26.75, -59., -16.5, z, z + 3.) for z in (16., 23., 30., 37.))}
    import vent_geometry as VG
    mouths = {   # Saved-STEP planes; bounds follow the source-bound stepped mouth geometry
        'cold_rear': ('x', [-length + .05, -length + 1.25, -length + 2.49, -length + 2.62], -34., -28., 5., 75.),
        'cold_bottom': ('z', [.05, 1.25, 2.49, 2.62], -length + 4., -83., -34., -28.),
        'hot_bottom': ('z', [.05, 1.25, 2.49, 2.62], -59., -5., -34., -28.),
        'hot_front': ('x', [-.05, -1.25, -2.49, -2.62], -34., -28., *VG.HOT_FRONT_Z)}
    neck = {k: min(free(ax, p, *uv) for p in planes) for k, (ax, planes, *uv) in mouths.items()}
    import plenum_flow as PF

    def planes(grid,axis,lo,hi):
        return PF.section_sample_planes(VG,length,axis,lo,hi,grid)
    series = {   # sections across the bay between the wall ports and each mouth (flow-normal planes)
        'cold_rear': [('x', x, -34., -28., 2.5, 97.5) for x in planes(frange(-length + 3., -104., 2.), 'x', -length + 3., -104.)],
        'cold_bottom': [('z', z, -length + 2.5, -65., -34., -28.) for z in planes(frange(2.6, 17.8, .4), 'z', 2.6, 17.8)],
        # FX (verifier T1 major): also through the hot port band and the rows above it (z 16.05..42.95, 0.5 mm pitch:
        # every 1.2 mm row band is sampled), where the trial2 rows choked the underside branch unseen
        'hot_bottom': [('z', z, -62., -2.5, -34., -28.) for z in planes(frange(2.6, 15.8, .4), 'z', 2.6, 15.8)]
                      + [('z', z, -62., -2.5, -34., -28.) for z in planes(frange(16.05,42.95,.5),'z',16.05,42.95)],
        'hot_front': [('x', x, -34., -28., 2.5, 97.5) for x in planes(frange(-16., -2.7, 1.), 'x', -16., -2.7)]}
    sec = {k: [(s[1], free(*s)) for s in v] for k, v in series.items()}
    csi = free('y', -31., -89., -77., 41., 68.)
    el = {k: dict(mouth_mm2=neck[k], series_min_mm2=min(f for _, f in sec[k])) for k in neck}
    el.update(cold_ports_mm2=ports['cold'], hot_ports_mm2=ports['hot'], csi_mm2=csi)
    if 'area_parity' in cats:
        for bay, names in (('cold', ('cold_rear', 'cold_bottom')), ('hot', ('hot_bottom', 'hot_front'))):
            res = CS.branch_parity([dict(name=n, mouth_mm2=neck[n], series_mm2=[f for _, f in sec[n]])
                                    for n in names], ports[bay])
            add('area_parity', bay + '_branch_series', res.pop('passed'), **res,
                sections={n: dict(axis=series[n][0][0], positions_mm=[p for p, _ in sec[n]],
                                  free_area_mm2=[f for _, f in sec[n]]) for n in names},
                rule='sum over branches of min(mouth neck, every sampled series section) >= wall ports - 0.002 mm2 '
                     '(replaces the parallel-mouth-only comparison of hot/cold_summed_sampled_mouth_necks)')
        # FX (verifier T1 major, VN-37): path-aware gate. Planes can only sample; the minimum cut between the wall-port
        # faces and the mouth faces over the free gap volume of the saved STEP (plenum_flow.step_min_cut) is the
        # smallest section on ANY path. The empty-bay bound (same ports, mouths, frame and mullions, no rib at all,
        # nominal CAD-free) is what no internal layout can exceed.
        import plenum_flow as PF
        import vent_geometry as VG
        for bay in ('cold', 'hot'):
            mc = PF.step_min_cut(tub, length, bay)
            empty = PF.nominal_min_cut(VG, length, bay, ribs=False)
            nom = PF.nominal_min_cut(VG, length, bay, ribs=True)
            need = mc['wall_ports_mm2']
            add('area_parity', bay + '_path_min_cut', mc['min_cut_mm2'] >= need - PF.TOL_MM2,
                min_cut_mm2=mc['min_cut_mm2'], wall_ports_mm2=need, shortfall_mm2=max(0.0, need - mc['min_cut_mm2']),
                port_face_mm2=mc['port_face_mm2'], port_face_blocked_mm2=mc['port_face_blocked_mm2'],
                mouth_face_mm2=mc['mouth_face_mm2'], cut_composition_mm2=mc['cut_composition_mm2'],
                internal_cut_bbox_xz=mc['internal_cut_bbox_xz'], grid=mc['grid'], step_grid=mc['step_grid'],
                min_cut_quantization=mc['quantization'],nominal_quantization=nom['quantization'],empty_bay_quantization=empty['quantization'],
                empty_bay_bound_nominal_mm2=empty['min_cut_mm2'], nominal_with_ribs_mm2=nom['min_cut_mm2'],
                empty_bay_bound_reaches_ports=empty['min_cut_mm2'] >= need - PF.TOL_MM2,
                rule='minimum cut (max flow) from the wall-port faces to the mouth faces of the bay over the free gap '
                     'volume of the saved tub STEP >= wall ports - %g mm2 (verifier rectangles; plenum_flow.py)' % PF.TOL_MM2,
                note=None if empty['min_cut_mm2'] >= need - PF.TOL_MM2 else
                     'No internal layout can pass: with these wall ports, mouths, mullions and frame the bay without any '
                     'rib reaches only the empty-bay bound; closing the row needs a port or mouth change (user decision 17)')
    if 'flow_network' in cats:
        fb = flow_baseline(a.variant)   # FX: the variant's own baseline (fixup-1 VN-36 row; can fail)
        if fb.exists():
            bind(fb)
            fbd = rd(fb)
            fd_ok, fd = CS.flow_drift(CS.flow_network(el), fbd)
            fd_ok = fd_ok and fbd.get('variant', 'compact-kowa_lm6hc') == a.variant
            add('flow_network', 'baseline_drift', fd_ok, baseline=relpath_posix(fb, CV.parent),
                baseline_variant=fbd.get('variant', 'compact-kowa_lm6hc'), **fd)
        else:
            add('flow_network', 'baseline_drift', False, baseline=relpath_posix(fb, CV.parent),
                error='no flow-network baseline for this variant (one per variant; never another variant\'s numbers)')
        for r in CS.flow_network(el):
            add('flow_network', r.pop('case'), None, **r)
        add('flow_network', 'model', None, elements=el,
            fan_curve='UNKNOWN: no Active Cooler fan P-Q curve in the repo; operating point not computed (gate: '
                      'MEASUREMENTS-TO-CLOSE shadow-gap airflow row, G-W10/G-W11/G-W12 thermal tests)',
            excluded=['panel seams and other unmodelled leaks', 'laminar channel friction (review estimate < 1 Pa)',
                      'turn losses', 'per-element discharge coefficients (one common Cd assumed)'],
            decision='A CSI plug is user decision VN-36; this report only informs it.')

# ------------------------------------------------------------------------------------------- VN-35
if 'hdmi_face' in cats:
    snap = rd(HDMI_SNAPSHOT)
    bind(HDMI_SNAPSHOT)
    con = {c['id']: c for c in snap['connectors']}
    for pose, key in (('installed', 'hdmi_installed'), ('premate', 'hdmi_premate')):
        rr = snap[key]
        tr = CS.track_face(rr['frames'])
        add('hdmi_face', pose + '/continuity', tr['ok'], **{k: v for k, v in tr.items() if k != 'ok'},
            rule='consecutive frames <= 2.5 mm apart and the carried normal turns <= 30 deg per frame')
        pi_exit = [x + d for x, d in zip(con['p_hdmi_pi']['wire_exit'], rr['pi_head_displacement'])]
        evf_exit = [x + d for x, d in zip(con['p_hdmi_evf']['wire_exit'], rr['evf_head_displacement'])]
        ends = dict(pi_end_gap_mm=math.dist(tr['start_point'], pi_exit), evf_end_gap_mm=math.dist(tr['end_point'], evf_exit),
                    pi_normal_dot_exit=CS._dot(tr['start_normal'], con['p_hdmi_pi']['wire_exit_direction']),
                    pi_normal_dot_width=CS._dot(tr['start_normal'], rr['width_at_pi']),
                    evf_normal_dot_exit=CS._dot(tr['end_normal'], con['p_hdmi_evf']['wire_exit_direction']),
                    evf_normal_dot_width=CS._dot(tr['end_normal'], rr['width_at_evf']))
        add('hdmi_face', pose + '/end_frames', ends['pi_end_gap_mm'] < 1e-6 and ends['evf_end_gap_mm'] < 1e-6 and
            all(abs(ends[k]) < 1e-6 for k in ends if 'dot' in k), **ends,
            rule='route ends on each head wire exit, strip normal perpendicular to the exit direction and width')
        fm = CS.face_match(tr['start_normal'], tr['end_normal'])
        add('hdmi_face', pose + '/contact_sides', fm.pop('status'), **fm,
            operational_status='HOLD' if fm.get('hold') else None,
            note='face A = the strip face whose outward normal is face_a_at_pi at the Pi head. Record the measured '
                 'sides in check_scope.HDMI_CONTACT_SIDES (receipt) and this row becomes pass/fail.')

# ------------------------------------------------------------------------------------------- VN-34
if 'evf_restraint' in cats:
    import checks as CK
    import model
    snap = rd(HDMI_SNAPSHOT)
    bind(HDMI_SNAPSHOT)
    bind(R7_CHECKS)
    c7 = model.L.COTS['evf_board']['box']
    bbx = step('evf_board').BoundingBox()
    t = (bbx.xmin - c7['x'][0], bbx.ymin - c7['y'][0], bbx.zmin - c7['z'][0])
    span_err = max(abs((bbx.xmax - bbx.xmin) - (c7['x'][1] - c7['x'][0])),
                   abs((bbx.ymax - bbx.ymin) - (c7['y'][1] - c7['y'][0])),
                   abs((bbx.zmax - bbx.zmin) - (c7['z'][1] - c7['z'][0])))
    want = (154.0 - length, model.EY - 16.0, 0.0)
    frame_ok = span_err < .05 and max(abs(x - y) for x, y in zip(t, want)) < .05
    import cadquery as cq
    back = cq.Vector(-want[0], -want[1], -want[2])
    rows7 = {n: dict(shape=step(n).translate(back)) for n in ('evf_board', 'tub', 'panel')}
    hb = con_box = {c['id']: c for c in snap['connectors']}['p_hdmi_evf']['box']
    plug = {k: (hb[k][0] - w, hb[k][1] - w) for k, w in zip('xyz', want)}
    R = dict(part='evf_board', arrest=['tub', 'panel'], limit_mm=0.6, max_travel_mm=8.0)   # r7 values; no hood
    import print_rules as PR
    keep = dict(getattr(model.L, 'KEEPOUTS', {}) or {})
    keep['ko_hdmi_evf'] = plug
    Lv = PR.LayoutView(model.L, EVF_RESTRAINT=R, KEEPOUTS=keep)
    r7res = {r['direction']: r for r in rd(R7_CHECKS)['results']['evf_restraint']}
    res = CK.check_evf_restraint(Lv, rows7)
    for r in res:
        d = r.pop('direction')
        st = r.pop('status')
        r7r = r7res.get(d, {})
        add('evf_restraint', d, None if st == 'stub' else (st == 'pass' and frame_ok), **r,
            r7_gap_mm=r7r.get('gap_mm'), r7_arresting=r7r.get('arresting', r7r.get('arrest')), r7_status=r7r.get('status'),
            frame='r7 frame: candidate shapes translated by -%s (EVF set moved by model.py tr(154-length, EY-16, 0))' % (list(want),),
            frame_check=dict(ok=frame_ok, measured_translation=list(t), span_error_mm=span_err),
            plug_zone='selected HDMI snapshot p_hdmi_evf head box (rides with the board)')
    ctl = CK.check_evf_restraint(PR.LayoutView(Lv, EVF_RESTRAINT=dict(R, arrest=['tub'])), rows7)
    cy = {r['direction']: r for r in ctl}['+Y']
    add('evf_restraint', 'control_without_panel', cy['status'] == 'fail', control_plus_y=cy,
        purpose='regression fixture: with the panel removed from the arrest set the +Y row must fail (the panel is '
                'the +Y stop), so the check still sees a missing stop')

if 'evf_face' in cats:
    r7m = rd(R7_PARTS)
    bind(R7_PARTS)
    r7rows = {p['id']: p['bbox'] for p in r7m['parts'] if p.get('bbox')}
    g7 = CS.evf_geometry(r7rows, ('tub', 'panel', 'hood'))
    for mp in sorted((CV / 'out').glob('*/manifest.json')):
        m = rd(mp)
        if 'rows' not in m or 'storage' not in m:
            continue
        v = mp.parent.name
        gc = CS.evf_geometry({r['id']: r['bbox_mm'] for r in m['rows']}, ('tub', 'panel', 'hood'))
        add('evf_face', v + '/axis_side_by_side', None, r7=g7, candidate=gc, manifest_sha256=sha(mp),
            delta=dict(axis_y=gc['axis_y'] - g7['axis_y'], axis_z=gc['axis_z'] - g7['axis_z'],
                       flange_x=gc['flange_x'] - g7['flange_x']),
            r7_layout='layout.py EVF axis Y16 Z78, F -154 (EVF dict); candidate model.EY=%s' % 11.0)
        for row in CS.evf_face_screen(gc, g7):
            add('evf_face', '%s/%s' % (v, row.pop('id')), row.pop('passed'), **row,
                gate='face/nose fit with a user at the eyecup (no anthropometric data in the repo): r7 is the baseline')

# ------------------------------------------------------------------------------------------- VN-38
if 'stack_retention' in cats or 'post_root_bending' in cats:
    import cadquery as cq
    import checks as CK
    import model
    tub = step('tub')
    posts = []
    for x, z in model.CARRIER_SCREWS:      # make_tub carrier bosses: cyl y r4.8, y -25.55..17.2; measured here
        f = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*p) for p in
                                  [(x - 6, -24.5, z - 6), (x + 6, -24.5, z - 6), (x + 6, -24.5, z + 6), (x - 6, -24.5, z + 6),
                                   (x - 6, -24.5, z - 6)]]))
        s = f.intersect(tub)
        area = s.Area()
        edges = tub.intersect(cq.Edge.makeLine(cq.Vector(x + 3, -25.55, z), cq.Vector(x + 3, 30, z))).Edges()
        posts.append(dict(axis_xz=[x, z], root_section_area_mm2=area, root_section_faces=len(s.Faces()),
                          equivalent_d_mm=2 * math.sqrt(area / math.pi), length_mm=sum(e.Length() for e in edges),
                          length_spans=len(edges)))
    cm, mx, my, mz = 0.0, 0.0, 0.0, 0.0
    for i in STACK:
        c = step(i).Center()
        w = mrows[i]['mass_est_g']
        cm, mx, my, mz = cm + w, mx + w * c.x, my + w * c.y, mz + w * c.z
    com = (mx / cm, my / cm, mz / cm)
    if 'stack_retention' in cats:
        holes = [model.rp((hx, hy, 6)) for hx, hy in model.L.PI['holes']]
        cb = mrows['carrier']['bbox_mm']
        targets = [(h[0], h[2]) for h in holes] + [(cb[0], cb[4]), (cb[0], cb[5]), (cb[1], cb[4]), (cb[1], cb[5])]
        # FP-11c (VN-38): declared printed locating features (model.CARRIER_LOCATORS) are credited only from the bound
        # STEPs (CS.locator_point: seat touching on -Y, stop gap inside r7's hood-stop window on +Y), as r7 reads its
        # keeper and hood stop from layout and measures the stop gap. An uncredited locator fails the row.
        locs = [CS.locator_point(d, step('carrier'), step(d['seat_part']), step(d['stop_part']))
                for d in getattr(model, 'CARRIER_LOCATORS', [])]
        ret = [((x, z), 0.0) for x, z in model.CARRIER_SCREWS] + [((l['at'][0], l['at'][1]), l['stop_gap_mm'])
                                                                  for l in locs if l['credited']]
        rs = CS.stack_retention(ret, (com[0], com[2]), targets, CK,
                                bearing_r=min(p['equivalent_d_mm'] for p in posts) / 2)
        ok = rs.pop('passed') and all(l['credited'] for l in locs)
        add('stack_retention', 'vertical_carrier', ok, **rs, stack=STACK, stack_mass_g=cm,
            stack_com_mm=list(com), locators=locs,
            declared_retention='model.CARRIER_SCREWS (two PT screws clamping the carrier ears onto the tub posts, gap 0) '
                               'plus each model.CARRIER_LOCATORS point credited from the STEPs with its measured stop gap',
            rule='r7 check_stack_retention: CoM inside the hull of the retention points (margin > 0) and a bounded '
                 'rigid lift at every target (r7 LP, unchanged). Incidental contacts are not credited; a locator counts '
                 'only with a measured seat contact and a stop gap in %s mm.' % list(CS.STOP_GAP_WINDOW),
            remedy=None if ok else 'CAD: every declared locator must be credited and the CoM inside the hull (VN-38)')
    if 'post_root_bending' in cats:
        sup = rd(STRUCT_OUT)
        bind(STRUCT_OUT)
        screen = min(sup['material_sensitivity']['normal_strength_scenarios_MPa'])
        wire = rd(STRUCT_REF)['unresolved_wiring_mass_sensitivity']['mass_g']   # reference wiring sensitivity, g
        bind(STRUCT_REF)
        geo_ok = all(p['root_section_faces'] == 1 and p['length_spans'] == 1 for p in posts)
        d = min(p['equivalent_d_mm'] for p in posts)
        L_ = max(p['length_mm'] for p in posts)
        top_y = -25.55 + L_                                      # rays start on the inner-wall face (make_tub)
        pb = CS.post_root_bending(cm + wire, len(posts), d, L_, abs(top_y - com[1]), screen_mpa=screen)
        add('post_root_bending', 'carrier_posts_5g', geo_ok and pb.pop('passed'), **pb, posts=posts,
            mass_basis='rigid stack %.3f g + %.1f g wiring sensitivity (reference-export18 unresolved wiring)' % (cm, wire), post_top_y_mm=top_y,
            screen_basis='lowest normal-strength scenario of the structural supplement (%.1f MPa, across layers: the '
                         'posts print along the build axis); a screen, not an allowable; coupon and creep gates open'
                         % screen)

summary = {k: sum(r['status'] == k for r in checks) for k in ('pass', 'fail', 'info')}
if sha(MF) != mh:
    raise ValueError('Manifest changed during check')
srcs = {n: sha(CV / n) for n in ('check_scope.py', 'steps.py', 'evidence_rules.py', 'cv_io.py', 'print_rules.py',
                                  'plenum_flow.py', 'vent_geometry.py')}
srcs['../checks.py'] = sha(R7 / 'checks.py')
result = dict(manifest_sha256=mh, verification_source_sha256=sha(Path(__file__)), helper_source_sha256=srcs,
              input_sha256=inputs, variant=a.variant, scope=a.categories if cats != CATS else 'full', summary=summary,
              checks=checks, physical_qualified=False,
              note='FP-12 check-scope rows (VN-33/34/35/36/37/38). Report-only rows are info; HOLD rows wait for a '
                   'named measurement. Not a thermal, strength or optical qualification.')
write_text(Path(a.out) if a.out else D / 'check-scope-checks.json', json.dumps(result, indent=2))
print(json.dumps(summary), flush=True)
raise SystemExit(1 if summary['fail'] else 0)
