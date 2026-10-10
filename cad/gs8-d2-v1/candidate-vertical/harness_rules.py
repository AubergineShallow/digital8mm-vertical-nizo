# SPDX-License-Identifier: MIT
"""FP-10 (VN-26, VN-28; check parts of VN-47 and VN-62): harness and power checks for the vertical candidate.

CAD-free. Ports the r7 checks.py (d38468e) categories cable_routes, mate_reach, lead_access (pigtail face_out with
flexible cores and ties as fixed points, pigtail_drop), cable_stow and header_housings onto the candidate's own
centreline routes (routes.py, signal_routes.py, power_routes.py) and assembly-state model (steps.py).
verify_harness_checks.py binds the manifest, supplies the solid-hit and distance functions and writes the report.

Rules: r7 numbers are never relaxed; a route stretched to its stock length is judged at the SHORTEST member of its
own family (the solver's own bound) and at the MINIMUM stock length; unknown data are ranges with a named gate; a
failing row is the expected result until the CAD/docs phase fixes the geometry. VN-47 (ties vs RTV-only) and
VN-62 (G-W5 fail branch) stay user decisions: both alternatives are computed and reported, neither is chosen.
"""
import copy
import math

# ------------------------------------------------------------------ r7 constants (checks.py / layout.py, d38468e)
ROUTE_ALLOWANCE = (10.0, 0.10)     # checks.py ROUTE_ALLOWANCE: service allowance max(10 mm, 10 % of the length)
ROUTE_END_TOL = 1.0                # checks.py ROUTE_END_TOL: a route end within this of its end part / plug
MATE_MARGIN = 10.0                 # layout.py MATE_MARGIN
MATE_POSE_TOL = 0.01               # checks.py MATE_POSE_TOL: a mating pose lies on its insertion path
TAIL_D = 3.0                       # checks.py TAIL_D: lead tail tested as a dia 3 cylinder
SWEEP_TOL = 0.5                    # checks.py SWEEP_TOL (mm3) for hand / tail hits
STOW_FILL = 0.25                   # checks.py STOW_FILL (reported; the candidate has no stow boxes)
HAND_ENVELOPES = {                 # layout.py HAND_ENVELOPES (a, t, r)
    'pinch_sh': (30.0, 20.0, 24.0), 'pinch_ph': (35.0, 22.0, 26.0), 'pinch_ph1': (20.0, 22.0, 26.0),
    'pinch_xt30': (40.0, 30.0, 30.0), 'pinch_zif': (25.0, 20.0, 30.0)}
HDR_MIN_GAP = 0.3                  # layout.py HDR_HOUSING['min_gap']
FACE_OUT_MIN = 15.0                # layout.py PIGTAIL['face_out_min']: XT30 face out of the grip mouth
JUNCTION_OUT = 15.0                # checks.py mate_reach default junction_out (inline pairs)
R7_SOURCE = 'r7 cad/gs8-d2-v1/checks.py + layout.py at d38468e'

# ------------------------------------------------------------------ G-W5 drop model (VN-62)
# r7 layout.PIGTAIL['drop'] + PIGTAIL_FUSE; the candidate's own model is make_bom_vertical.py validate() hot_drop
# (16 AWG 13.17 / 18 AWG 21 mohm/m, 270 + 60 mm per conductor, copper at 60 C). Limit 0.150 V: never relaxed.
DROP = dict(
    i_peak_a=8.6, limit_v=0.15, xt30_mohm=1.0, fuse_cold_mohm=4.46,          # r7 WIRING s4 / PIGTAIL_FUSE (251 rev VL)
    rho20_ohm_mm2_per_m=1.0 / 58.0, alpha_per_k=0.00393, t_ref_c=20.0, t_hot_c=60.0,   # IACS copper; existing model
    pigtail_path_mm=270.0, pack_lead_mm=60.0,                                # power_routes / D2-13
    prc_strands_min=250, prc_strand_d_mm=0.08,                               # vendor: "over 250 strands ... .08 mm"
    prc_src='https://www.progressiverc.com/products/prc-silicone-wire-16-awg (over 250 strands of pure copper, '
            'each .08 mm; OD 3.0 mm; read 2026-10-11)',
    awg16_mm2=1.3088, awg18_mm2=0.8231,                                      # AWG nominal areas (ASTM B258)
    pack_lead_hi_mm2=150 * math.pi / 4 * 0.08 ** 2,                          # assumption: 150 x 0.08 18 AWG silicone
    lay_range=(1.00, 1.03),          # assumed stranding lay increment range (review drop_probe); G-W5 measures
    fuse_hot_factor_range=(1.0, 1.3),  # assumed hot/cold fuse resistance range (review drop_probe; not data)
    gate='G-W5 hot 8.6 A drop test on the built pigtail (measured fuse, contacts, copper); MP-PACK pack lead')


def reach_margin(length):
    """checks.reach_margin: max(MATE_MARGIN, ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] x length)."""
    return max(MATE_MARGIN, ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] * length)


def route_allowance(length):
    """checks.check_cable_routes allowance: max(10 mm, 10 % of the cable length)."""
    return max(ROUTE_ALLOWANCE[0], ROUTE_ALLOWANCE[1] * length)


def _r(x, n=3):
    return None if x is None else round(float(x), n)


# ------------------------------------------------------------------ geometry helpers (pure math)
def bb(b):
    """[x0, x1, y0, y1, z0, z1] from a list or a routes.B() dict."""
    if isinstance(b, dict):
        return [b['x'][0], b['x'][1], b['y'][0], b['y'][1], b['z'][0], b['z'][1]]
    return [float(v) for v in b]


def pt_box_dist(p, b):
    return math.sqrt(sum(max(b[2 * i] - p[i], 0.0, p[i] - b[2 * i + 1]) ** 2 for i in range(3)))


def box_gap(a, b):
    """checks._box_gap: largest axis gap (<= 0: touch or overlap)."""
    return max(max(a[2 * i], b[2 * i]) - min(a[2 * i + 1], b[2 * i + 1]) for i in range(3))


def box_vol(a, b):
    out = 1.0
    for i in range(3):
        out *= max(0.0, min(a[2 * i + 1], b[2 * i + 1]) - max(a[2 * i], b[2 * i]))
    return out


def boxes_overlap(a, b, m=0.0):
    return all(a[2 * i] < b[2 * i + 1] + m and b[2 * i] < a[2 * i + 1] + m for i in range(3))


def shift(b, d):
    return [b[0] + d[0], b[1] + d[0], b[2] + d[1], b[3] + d[1], b[4] + d[2], b[5] + d[2]]


def add(p, d, s=1.0):
    return [p[i] + s * d[i] for i in range(3)]


def cumulative(points):
    out, s = [0.0], 0.0
    for a, b in zip(points, points[1:]):
        s += math.dist(a, b)
        out.append(s)
    return out


def arc_length(points):
    return cumulative(points)[-1] if points else 0.0


def nearest_on_polyline(points, q):
    """(arc position s, point, distance) of the polyline point nearest q (segments, not only samples)."""
    cum = cumulative(points)
    best = (None, None, float('inf'))
    for i, (a, b) in enumerate(zip(points, points[1:])):
        ab = [b[k] - a[k] for k in range(3)]
        n2 = sum(x * x for x in ab)
        t = 0.0 if n2 == 0 else max(0.0, min(1.0, sum((q[k] - a[k]) * ab[k] for k in range(3)) / n2))
        p = [a[k] + ab[k] * t for k in range(3)]
        d = math.dist(p, q)
        if d < best[2]:
            best = (cum[i] + t * math.sqrt(n2), p, d)
    return best


def plane_crossings(points, axis, value):
    """[(s, point)] where the polyline crosses coordinate `axis` == value."""
    cum, out = cumulative(points), []
    for i, (a, b) in enumerate(zip(points, points[1:])):
        if (a[axis] - value) * (b[axis] - value) <= 0 and a[axis] != b[axis]:
            t = (value - a[axis]) / (b[axis] - a[axis])
            out.append((cum[i] + t * math.dist(a, b), [a[k] + t * (b[k] - a[k]) for k in range(3)]))
    return out


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def hand_box(rear, axis, row, env):
    """checks._hand_box: hand envelope (a, t, r) a behind `rear` along -axis, t along axis x row, r along row."""
    a, t, r = env
    nrm = math.sqrt(sum(x * x for x in axis)) or 1.0
    ax = [x / nrm for x in axis]
    th = cross3(ax, row)
    cs = [[rear[i] - sa * a * ax[i] + st * t * th[i] + sr * r * row[i] for i in range(3)]
          for sa in (0.0, 1.0) for st in (-0.5, 0.5) for sr in (-0.5, 0.5)]
    return [f(c[i] for c in cs) for i in range(3) for f in (min, max)]


def out_of_mm(box, out_of):
    """checks._out_of_mm: how far the whole box lies beyond plane + margin on the signed side (>= 0 holds)."""
    sgn, ax = out_of[0][0], 'xyz'.index(out_of[0][1])
    return (box[2 * ax] - out_of[1] - out_of[2]) if sgn == '+' else (out_of[1] - out_of[2] - box[2 * ax + 1])


def on_path(path, d, tol=MATE_POSE_TOL):
    """checks._on_path: the pose d lies on the insertion path polyline."""
    for a, b in zip(path, path[1:]):
        ab = [b[i] - a[i] for i in range(3)]
        n2 = sum(x * x for x in ab)
        t = 0.0 if n2 == 0 else max(0.0, min(1.0, sum((d[i] - a[i]) * ab[i] for i in range(3)) / n2))
        if math.dist(d, [a[i] + ab[i] * t for i in range(3)]) <= tol:
            return True
    return False


def tail_box(p0, p1, d=TAIL_D):
    return [f(p0[i], p1[i]) + s * d / 2 for i in range(3) for f, s in ((min, -1), (max, 1))]


# ------------------------------------------------------------------ route families (VN-28)
# A route stretched to its stock length by a solver is judged at the shortest member of its own family: the
# solver variable at its own bound. Each entry names the knots that carry the variable and the source literal.
FAMILIES = {
    'qt': dict(var='low', knots=(3, 4), axis=2, bound=(34.0, 50.0),
               src="signal_routes.py build(): QT top-loop 'lo,hi=34.,50.'"),
    'run_pin37': dict(var='top', knots=(6, 7), axis=2, bound=(35.0, 80.0),
                      src="signal_routes.py build(): run cores '_solve_top(make,250,35,80)'"),
    'run_pin39': dict(var='top', knots=(4, 5), axis=2, bound=(35.0, 80.0),
                      src="signal_routes.py build(): run cores '_solve_top(make,250,35,80)'"),
}


def family_eval(rounded_path, curve, fam, value, upto=None):
    """Rounded length of the family member with the variable = value (knots[:upto+1] when upto is given)."""
    knots = copy.deepcopy(curve['knots'])
    for i in fam['knots']:
        knots[i][fam['axis']] = float(value)
    if upto is not None:
        knots = knots[:upto + 1]
    c = rounded_path(knots, curve['centerline_radius_mm'], curve['first_straight_min_mm'],
                     0.0 if upto is not None else curve['last_straight_min_mm'], 0.5)
    return dict(length=c['rounded_length_mm'], errors=c['errors'], knots=knots, points=c['sampled_centerline'])


def family_range(rounded_path, curve, fam):
    """Recorded variable, recomputed recorded length, and the family lengths at both solver bounds."""
    vals = [curve['knots'][i][fam['axis']] for i in fam['knots']]
    rec = vals[0]
    same = all(abs(v - rec) < 1e-9 for v in vals)
    at = {b: family_eval(rounded_path, curve, fam, b) for b in fam['bound']}
    lens = {b: at[b]['length'] for b in fam['bound']}
    valid = {b: not at[b]['errors'] for b in fam['bound']}
    good = [lens[b] for b in fam['bound'] if valid[b]]
    return dict(variable=fam['var'], recorded=rec, knots_share_variable=same, bound=list(fam['bound']),
                src=fam['src'], recomputed_mm=family_eval(rounded_path, curve, fam, rec)['length'],
                recorded_mm=curve['rounded_length_mm'], length_at_bound_mm={str(b): lens[b] for b in fam['bound']},
                valid_at_bound={str(b): valid[b] for b in fam['bound']},
                min_mm=min(good) if good else None, max_mm=max(good) if good else None,
                min_at=min(fam['bound'], key=lambda b: lens[b] if valid[b] else float('inf')))


# ------------------------------------------------------------------ cable declarations (data of record)
CABLES = {
    'qt': dict(src=('signal_geometry', 'qt'), length=250.0, length_range=(240.0, 260.0), ends=('pi5', 'encoder'),
               range_src='BOM D2-24 / D2-24B: finished QT lead 250 +/- 10 mm (MP-QT measures)', end_plug='p_qt_enc'),
    'run_pin37': dict(src=('signal_geometry', 'run_cores', 0), length=250.0, length_range=None,
                      ends=('pi5', 'run_button'), housing='hdr_run_lead_37',
                      range_src='r7 CABLES run_lead length 250 mm design value; no vendor tolerance (MP-RUN measures)'),
    'run_pin39': dict(src=('signal_geometry', 'run_cores', 1), length=250.0, length_range=None,
                      ends=('pi5', 'run_button'), housing='hdr_run_lead_39',
                      range_src='r7 CABLES run_lead length 250 mm design value; no vendor tolerance (MP-RUN measures)'),
    'power_button': dict(src=('signal_geometry', 'power_button'), length=375.0, length_range=(363.0, 387.0),
                         ends=('pi5', 'power_button'), cut_to_length=True,
                         range_src='BOM V-28: 2181120201 female 150 +/- 6 mm + 2181110202 male 225 +/- 6 mm exposed '
                                   'tails, cut to measured length; side genders unassigned (VN-63). The signal_routes '
                                   '150 mm stock figure predates V-28.'),
    'fpc': dict(src=('signal_geometry', 'fpc'), length=200.0, length_range=None, ends=('pi5', 'gs_camera'),
                end_plug='p_fpc_cam', range_src='official 200 mm camera cable, design value (MTC camera-cable row)'),
    'fan': dict(src=('routes', 'fan'), length=60.0, length_range=None, ends=('cooler', 'pi5'),
                range_src='native Active Cooler lead, r7 length estimate'),
    'oled_flex': dict(src=('routes', 'oled_flex'), length=50.0, length_range=None, ends=('hmx039', 'evf_board'),
                      range_src='kit OLED flex 50 mm (r7 CABLES)'),
    'usb_5v': dict(src=('routes', 'usb_5v'), length=200.0, length_range=None, ends=('pi5', 'evf_board'),
                   range_src='Adafruit 4448 donor (MTC USB-donor row)'),
    'pack_lead': dict(src=('routes', 'pack_lead'), length=60.0, length_range=None, ends=('pack', 'xt30_pair'),
                      range_src='D2-13 existing 60 mm 18 AWG pack lead (MP-PACK)'),
    'hdmi': dict(delegated='verify_hdmi.py -> hdmi-solid-checks.json: the full developable 300 mm 3562 ribbon is laid '
                           'in explicit deployable loops and its carried / premate / unplugged poses are swept there'),
    'fps_lead': dict(delegated='verify_fps_integrated.py -> integrated-fps-checks.json: the selected D2-27 Molex '
                               'mated-carry harness; the signal_routes 200 + 50 mm PH model is superseded (BOM D2-27)'),
}
POWER_CORES = ('positive', 'negative')
PIGTAIL_LENGTH = 270.0     # power_routes finished-path allocation per polarity (cut to it; G-V-PIGTAIL)


def _dig(d, path):
    for k in path:
        d = d[k] if not isinstance(k, str) or not isinstance(d, list) else next(x for x in d if x['id'] == k)
    return d


def collect(out, rows, L, ST):
    """Harness data H from routes.build() output `out`, manifest rows {id: row}, the baseline layout module L and the
    assembly-state model ST (steps.py)."""
    routes = {r['id']: r for r in out['routes']}
    H = dict(boxes={k: bb(r['bbox_mm']) for k, r in rows.items()}, kinds={k: r['kind'] for k, r in rows.items()},
             plugs={p['id']: bb(p['box']) for p in out['plugs'] if p.get('box')},
             housings={h['id']: dict(id=h['id'], cable=h['cable'], pins=list(h['pins']), box=bb(h['box']),
                                     wire_exit=list(h['wire_exit'])) for h in out['header_housings']},
             used_pins={k: tuple(v) for k, v in L.HDR_USED_PINS.items()}, hdr=dict(L.HDR_HOUSING),
             header_types={'hdr_%s_%s' % (c, '_'.join(map(str, p))): t for c, t, p in L.HEADER_HOUSINGS},
             opening_y=rows['tub']['bbox_mm'][3], mouth_z=L.GRIP['bay']['z'][0],
             grip_bottom_z=rows['base_grip']['bbox_mm'][4], grip_top_z=rows['base_grip']['bbox_mm'][5],
             floor_z=out['signal_geometry']['body_inner_z_mm'][0], pack_in_start=list(ST.MOTIONS['pack_in']['path'][0]),
             cables={}, power=out['power_geometry'], signal_revision=out['signal_geometry']['revision'],
             routes_revision=out['revision'])
    sig = out['signal_geometry']
    H['branch_starts'] = ([(b['id'], list(b['curve']['sampled_centerline'][0])) for b in sig['branches']]
                          + [(c['source_housing_id'] if 'source_housing_id' in c else 'hdr_run_lead_%d' % c['pins'][0],
                              list(c['curve']['sampled_centerline'][0])) for c in sig['run_cores']])
    for cid, spec in CABLES.items():
        c = dict(id=cid, **{k: v for k, v in spec.items() if k != 'src'})
        if 'delegated' in spec:
            H['cables'][cid] = c
            continue
        src = sig if spec['src'][0] == 'signal_geometry' else routes
        item = _dig(src, spec['src'][1:])
        curve = item['curve']
        c.update(curve=curve, points=[list(p) for p in curve.get('sampled_centerline') or []],
                 errors=list(curve.get('errors') or []), family=FAMILIES.get(cid), branches=[], od_mm=item.get('od_mm'))
        if cid == 'qt':
            c['branches'] = [dict(id=b['id'], points=[list(p) for p in b['curve']['sampled_centerline']],
                                  length=b['curve']['rounded_length_mm']) for b in sig['branches'] if b['cable'] == 'qt']
        H['cables'][cid] = c
    st = out['retired_pigtail_service_estimate']['study']['service_path']
    H['pigtail_service'] = dict(knots=[list(k) for k in st['knots']], radius=st['centerline_radius_mm'],
                                first_tail=st['first_straight_min_mm'], last_tail=st['last_straight_min_mm'],
                                src='routes.pigtail_16_study() service_path (the conservative front-bypass service '
                                    'centreline; listed as retired_pigtail_service_estimate, the only flexible-service '
                                    'corridor in the source)')
    for core in out['power_geometry']['cores']:
        cid = 'pigtail_' + core['id']
        own = ('xt30_selected_housing',)   # r7: a cable's own end part is exempt (the core ends on its housing face)
        errs = (['hits %s' % h['obstacle'] for h in core['source_proxy_hits'] if h['obstacle'] not in own]
                + (['%d wall overrun points' % len(core['wall_overrun_points'])] if core['wall_overrun_points'] else [])
                + list(core['upper_curve']['errors']))
        H['cables'][cid] = dict(id=cid, length=PIGTAIL_LENGTH, length_range=None, ends=('x1203', 'xt30_pair'),
                                range_src='power_routes 270 mm finished-path allocation, cut to it (G-V-PIGTAIL)',
                                points=[list(p) for p in core['full_centerline_excluding_unmeasured_root_joint']],
                                errors=errs,
                                core=core, family=None, branches=[])
    return H


# ------------------------------------------------------------------ pigtail power cores (VN-47, VN-62)
# Retention of record: ASSEMBLY-VERTICAL.md 'Provisionally allocate four existing-class 2.5 mm cable ties ... at the
# new carrier lacing slots'. VN-47 user decision: carrier ties or r7 BX-3 RTV-only. Changing this value switches the
# gating row; the other alternative is always reported as 'info' with the decision reference.
PIGTAIL_RETENTION = 'carrier_ties'
TIE_SLOTS_XZ = [(-92.0, 25.0), (-92.0, 45.0), (-34.0, 25.0), (-34.0, 45.0)]   # model.py make_carrier()
TIE_SLOT_HALF = (1.5, 0.5)             # model.py: 3 x 1 mm through-plate slots (x, z half sizes)
TIE_SLOT_Y = (13.9 + 3.2, 17.1 + 3.2)  # model.py: plate y 13.9..17.1, carrier translated +3.2 in y
TIE_BAND_MAX = 0.7                     # ASSEMBLY-VERTICAL.md: band thickness must measure <= 0.7 mm
CORE_OD = 3.2                          # power_routes od_mm reservation per core (vendor OD 3.0)
HUMP_R2 = 16.0                         # power_routes side(): two 8 mm arcs per hump side


def tie_slot_boxes():
    return [[x - TIE_SLOT_HALF[0], x + TIE_SLOT_HALF[0], TIE_SLOT_Y[0], TIE_SLOT_Y[1], z - TIE_SLOT_HALF[1],
             z + TIE_SLOT_HALF[1]] for x, z in TIE_SLOTS_XZ]


def _side(drop):
    if drop <= HUMP_R2:
        a = math.acos(1 - max(0.0, drop) / HUMP_R2)
        return a, 0.0, HUMP_R2 * math.sin(a), HUMP_R2 * a
    return math.pi / 2, drop - HUMP_R2, HUMP_R2, HUMP_R2 * math.pi / 2 + drop - HUMP_R2


def hump_excess(sh):
    """Stored slack of a power core: designed hump length minus its family minimum (power_routes hump(low))."""
    a1, a2 = math.radians(sh['rise_angle_deg']), math.radians(sh['fall_angle_deg'])
    l1, l2, flat, high = sh['rise_straight_mm'], sh['fall_straight_mm'], sh['middle_straight_mm'], sh['top_z']
    bump = HUMP_R2 * (a1 + a2) + l1 + l2 + flat
    width = flat + HUMP_R2 * (math.sin(a1) + math.sin(a2))
    zbase = high - (HUMP_R2 * (1 - math.cos(a1)) + l1)
    endbase = high - (HUMP_R2 * (1 - math.cos(a2)) + l2)
    lo = max(zbase, endbase)
    s1, s2 = _side(lo - zbase), _side(lo - endbase)
    minimum = s1[3] + s2[3] + width - s1[2] - s2[2]
    return dict(bump_mm=bump, min_mm=minimum, excess_mm=bump - minimum, width_mm=width, zbase=zbase,
                endbase=endbase, top_z=high)


def junction_local(P, x):
    """Local (u, v, w) coordinates of a seated junction-attached point (power_routes junction frame)."""
    M, C = P['junction_transform_matrix'], P['junction_center']
    cols = [[M[i][j] for i in range(3)] for j in range(3)]
    return [sum((x[i] - C[i]) * cols[j][i] for i in range(3)) for j in range(3)]


def junction_posed(P, local, pose):
    return [pose['center'][a] + sum(pose['matrix'][a][b] * local[b] for b in range(3)) for a in range(3)]


def face_isolation(H, core_id):
    """Wire face of a core's XT30 housing in the last rigid service pose (the candidate's battery-isolation pose,
    swept by verify_power_service.py): positive = female face F, negative = F + 5 mm v (power_routes)."""
    P = H['power']
    core = next(c for c in P['cores'] if c['id'] == core_id)
    face = core['full_centerline_excluding_unmeasured_root_joint'][-1]
    return junction_posed(P, junction_local(P, face), P['rigid_service_poses'][-1])


def corridor(H, core_id, e, rounded_path):
    """The candidate's declared flexible-service corridor (routes.pigtail_16_study service_path: front bypass, floor
    hole, drop) for one core. The study's knots are kept (bend radius and tails as declared) except the last one,
    which becomes the core's isolation-pose face lowered to e mm below the grip mouth (the study dropped at the
    floor-hole x). The study starts at the negative-core root; for a core whose root differs, the first straight
    leg is re-measured from that root to the study's second knot (the positive's own first corner would violate the
    declared 8 mm bend radius on the 16 mm leg after it, so the study fillets are kept).
    -> dict(rounded_length_mm (None if invalid), errors, sampled_centerline, lead_in_mm)"""
    S = H['pigtail_service']
    core = next(c for c in H['power']['cores'] if c['id'] == core_id)
    k = copy.deepcopy(S['knots'])
    f = face_isolation(H, core_id)
    k[-1] = [f[0], f[1], H['mouth_z'] - e]
    c = rounded_path(k, S['radius'], S['first_tail'], S['last_tail'], 0.5)
    lead = math.dist(core['root'], k[1]) - math.dist(k[0], k[1])
    pts = [list(p) for p in c['sampled_centerline']]
    if math.dist(core['root'], k[0]) > 1e-9:
        pts = [list(core['root'])] + pts[1:]
    return dict(rounded_length_mm=None if c['rounded_length_mm'] is None else c['rounded_length_mm'] + lead,
                errors=c['errors'], sampled_centerline=pts, lead_in_mm=lead)


def _solve_e(f, lo=-60.0, hi=400.0):
    """Largest e with f(e) >= 0 (f decreasing in e); None if f(lo) < 0 (not even 60 mm inside the mouth)."""
    if f(lo) < 0:
        return None
    if f(hi) >= 0:
        return hi
    for _ in range(70):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) >= 0 else (lo, mid)
    return lo


def pigtail_reach_rows(H, rounded_path, retention=None):
    """lead_access pigtail rows (r7 C3 _pigtail_face_out on the candidate cores): ties on route; face_out with the
    four carrier ties as fixed points (design of record); face_out RTV-only (r7 BX-3, the pad as the only fixed
    point). The allowance reach_margin(270) is always kept; the root stub is fixed at the pad."""
    retention = PIGTAIL_RETENTION if retention is None else retention
    slots, cap, allow = tie_slot_boxes(), CORE_OD / 2 + TIE_BAND_MAX, reach_margin(PIGTAIL_LENGTH)
    cores = {c['id']: c for c in H['power']['cores']}
    ties, rtv, tie_res = [], {}, {}
    for cid in POWER_CORES:
        core = cores[cid]
        free0 = PIGTAIL_LENGTH - core['unmodeled_root_joint_allowance_mm']
        pts = [list(p) for p in core['full_centerline_excluding_unmeasured_root_joint']]
        k_end = len(core['flexible_wire_parts'][0]['points']) - 1 if cid == 'positive' else len(pts) - 1
        flex = pts[:k_end + 1]
        f_rtv = lambda e, cid=cid, free0=free0: free0 - corridor(H, cid, e, rounded_path)['rounded_length_mm'] - allow
        c15 = corridor(H, cid, FACE_OUT_MIN, rounded_path)
        rtv[cid] = dict(face_out_mm=_r(_solve_e(f_rtv), 2), slack_at_face_out_min_mm=_r(f_rtv(FACE_OUT_MIN), 2),
                        corridor_mm=_r(c15['rounded_length_mm'], 2), free_length_mm=_r(free0, 2), allowance_mm=allow,
                        root_stub_mm=_r(core['unmodeled_root_joint_allowance_mm'], 2), corridor_errors=c15['errors'])
        per = []
        for (x, z), sb in zip(TIE_SLOTS_XZ, slots):
            q = [x, (TIE_SLOT_Y[0] + TIE_SLOT_Y[1]) / 2, z]
            s_t, p_t, _ = nearest_on_polyline(flex, q)
            gap = min(pt_box_dist(p, sb) for p in flex)
            drawn = s_t + math.dist(p_t, q)          # as drawn: installed path to its nearest point, then to the slot
            lower = math.dist(core['root'], q)        # lower bound: straight pad root to slot (not obstacle-checked)

            def f_tie(e, fixed, q=q, cid=cid, free0=free0):
                c = corridor(H, cid, e, rounded_path)
                s_c, p_c, d_c = nearest_on_polyline(c['sampled_centerline'], q)
                return free0 - fixed - (d_c + arc_length(c['sampled_centerline']) - s_c) - allow
            rec = dict(core=cid, slot_xz=[x, z], core_to_slot_mm=_r(gap, 2), on_route=gap <= cap + 1e-9,
                       nearest_core_point=[_r(v, 2) for v in p_t], arc_s_mm=_r(s_t, 1),
                       fixed_as_drawn_mm=_r(drawn, 1), fixed_lower_bound_mm=_r(lower, 1),
                       face_out_as_drawn_mm=_r(_solve_e(lambda e: f_tie(e, drawn)), 2),
                       face_out_lower_bound_mm=_r(_solve_e(lambda e: f_tie(e, lower)), 2))
            per.append(rec)
            ties.append(rec)
        key = lambda t, k: -1e9 if t[k] is None else t[k]
        worst = min(per, key=lambda t: key(t, 'face_out_as_drawn_mm'))
        best = max(per, key=lambda t: key(t, 'face_out_lower_bound_mm'))
        tie_res[cid] = dict(face_out_mm=worst['face_out_as_drawn_mm'], worst_slot=worst['slot_xz'],
                            best_case_face_out_mm=best['face_out_lower_bound_mm'], best_case_slot=best['slot_xz'],
                            any_slot_on_route=any(t['on_route'] for t in per))
    pr = ['no allocated tie slot reaches the %s core (nearest %s mm; a tie binds a core within OD/2 + band = %.1f mm '
          'of its slot)' % (c, min(t['core_to_slot_mm'] for t in ties if t['core'] == c), cap)
          for c in POWER_CORES if not tie_res[c]['any_slot_on_route']]
    rows = [dict(category='lead_access', id='pigtail_ties_on_route', retention_of_record=retention, capture_mm=cap,
                 ties=ties, slots_off_route=sum(not t['on_route'] for t in ties), slot_boxes=slots,
                 status=('fail' if pr else 'pass') if retention == 'carrier_ties' else 'info', problems=pr,
                 gate='VN-47 user decision (carrier ties vs RTV-only); G-V-PIGTAIL routing mock-up',
                 note='Slots from model.py make_carrier(); the runner confirms each slot open in the carrier STEP.')]
    model = ('r7 _pigtail_face_out: free length (270 - root stub - fixed length up to the governing fixed point) minus '
             'the taut path along the declared service corridor to the isolation-pose face lowered to e below the '
             'mouth, minus reach_margin(270); face_out = the largest e that keeps slack >= 0. Ties: the design does '
             'not assign slots to cores, so the worst slot gates with the fixed length as drawn (installed path to '
             'its nearest point, then to the slot); the best slot with a straight pad-to-slot lower bound is reported')
    rows.append(dict(category='lead_access', id='pigtail_pad_range', status='info', gate='G-W2 / G-V-PIGTAIL',
                     assumed_pad=list(cores['positive']['source_assumed_pad']),
                     note='r7 pigtail_range (cut rule over the credible pad range) is not ported: the candidate uses one '
                          'fixed 270 mm allocation at one assumed pad, with no cut rule. Every reach and drop row here '
                          'holds only at that assumed pad; the real pad roots are a STOP (G-W2, G-V-PIGTAIL).'))
    for rid, res, ret in (('pigtail_xt30_mouth', tie_res, 'carrier_ties'), ('pigtail_xt30_mouth_rtv_only', rtv, 'rtv_only')):
        bad = [c for c, v in res.items() if v['face_out_mm'] is None or v['face_out_mm'] < FACE_OUT_MIN - 1e-9]
        msg = ['%s core: XT30 face out %s mm < %.1f' % (c, res[c]['face_out_mm'], FACE_OUT_MIN) for c in bad]
        if ret == 'carrier_ties':
            msg += ['ties as fixed points are not on the drawn %s route' % c for c in POWER_CORES
                    if not res[c]['any_slot_on_route']]
        gating = ret == retention
        rows.append(dict(category='lead_access', id=rid, retention=ret, gating=gating, cores=res, model=model,
                         corridor_src=H['pigtail_service']['src'], face_out_min=FACE_OUT_MIN, allowance_mm=allow,
                         estimate=True, status=('fail' if msg else 'pass') if gating else 'info',
                         problems=msg if gating else [], would_fail=None if gating else msg,
                         gate='G-V-PIGTAIL flexible withdrawal (mock-up)' if gating else 'VN-47 user decision'))
    return rows


def drop_v(area16_mm2, lay, area18_mm2, fuse_factor, path_mm=None, D=DROP):
    """G-W5 drop estimate (V): 2 conductors x (pigtail path + pack lead) at 60 C + fuse + XT30, at the peak current."""
    path_mm = D['pigtail_path_mm'] if path_mm is None else path_mm
    k = 1 + D['alpha_per_k'] * (D['t_hot_c'] - D['t_ref_c'])
    r16 = D['rho20_ohm_mm2_per_m'] / area16_mm2 * 1000.0 * lay       # mohm/m
    r18 = D['rho20_ohm_mm2_per_m'] / area18_mm2 * 1000.0 * lay
    r = 2 * (path_mm / 1000.0 * r16 + D['pack_lead_mm'] / 1000.0 * r18) * k + D['fuse_cold_mohm'] * fuse_factor + D['xt30_mohm']
    return D['i_peak_a'] * r / 1000.0


def pigtail_drop_row(D=DROP):
    """VN-62 computed row: drop range from the vendor strand data; asserts drop_hi <= 0.150 V (never relaxed)."""
    prc_min = D['prc_strands_min'] * math.pi / 4 * D['prc_strand_d_mm'] ** 2
    lay0, lay1 = D['lay_range']
    f0, f1 = D['fuse_hot_factor_range']
    cases = dict(
        lo=dict(area16=D['awg16_mm2'], lay=lay0, area18=D['awg18_mm2'], fuse=f0,
                basis='AWG nominal areas, no lay increment, cold fuse (= make_bom_vertical hot_drop model)'),
        hi_cold_fuse=dict(area16=prc_min, lay=lay1, area18=D['pack_lead_hi_mm2'], fuse=f0,
                          basis='vendor minimum 250 x 0.08 mm, lay 1.03, 150 x 0.08 pack lead, cold fuse'),
        nominal_hot_fuse=dict(area16=D['awg16_mm2'], lay=lay0, area18=D['awg18_mm2'], fuse=f1,
                              basis='AWG nominal copper with the hot fuse case'),
        hi=dict(area16=prc_min, lay=lay1, area18=D['pack_lead_hi_mm2'], fuse=f1,
                basis='vendor minimum strands, lay 1.03, 150 x 0.08 pack lead, hot fuse x 1.3'))
    out = {}
    for k, c in cases.items():
        out[k] = dict(c, drop_v=_r(drop_v(c['area16'], c['lay'], c['area18'], c['fuse'], D=D), 5),
                      margin_mv=_r(1000 * (D['limit_v'] - drop_v(c['area16'], c['lay'], c['area18'], c['fuse'], D=D)), 2))
        out[k]['area16'] = _r(c['area16'], 4)
        out[k]['area18'] = _r(c['area18'], 4)

    def max_path(fuse):
        lo, hi = 0.0, 1000.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if drop_v(prc_min, lay1, D['pack_lead_hi_mm2'], fuse, mid, D) <= D['limit_v'] else (lo, mid)
        return lo
    hi_v = drop_v(prc_min, lay1, D['pack_lead_hi_mm2'], f1, D=D)
    pr = [] if hi_v <= D['limit_v'] + 1e-12 else ['drop_hi %.4f V > %.3f V at %.1f A (hot fuse x %.2f, vendor minimum '
                                                   'strands, lay %.2f)' % (hi_v, D['limit_v'], D['i_peak_a'], f1, lay1)]
    decision = dict(
        shorter_path_max_mm_hot_fuse=_r(max_path(f1), 1), shorter_path_max_mm_cold_fuse=_r(max_path(f0), 1),
        awg14_nominal_hi_drop_v=_r(drop_v(2.0809, lay1, D['pack_lead_hi_mm2'], f1, D=D), 5),
        awg14_note='AWG 14 nominal 2.0809 mm2 for information only; OD and lane fit unchecked (lane re-check needed)',
        cutoff_raise_needed_v=_r(max(0.0, hi_v - D['limit_v']), 5),
        options='VN-62 user decision: shorter finished path, 14 AWG with a lane re-check, or a higher software cut-off. '
                'The 0.150 V limit is never relaxed by this check.')
    return dict(category='lead_access', id='pigtail_drop', kind='drop', model='r7 _pigtail_drop_v (G-W5) with '
                'vendor strand data', i_peak_a=D['i_peak_a'], limit_v=D['limit_v'], cases=out,
                drop_lo_v=out['lo']['drop_v'], drop_hi_v=out['hi']['drop_v'], vendor=D['prc_src'],
                assumptions=dict(lay_range=list(D['lay_range']), fuse_hot_factor_range=list(D['fuse_hot_factor_range']),
                                 pack_lead='150 x 0.08 mm 18 AWG silicone (strand count unknown; MP-PACK)',
                                 copper='IACS annealed copper 1/58 ohm mm2/m at 20 C, alpha 0.00393/K, 60 C'),
                decision_data=decision, gate=D['gate'], estimate=True, problems=pr, status='fail' if pr else 'pass')


# ------------------------------------------------------------------ cable_routes (r7 C2 semantics, VN-26 / VN-28)
def _end_boxes(H, c, part, where):
    if where == 'start' and c.get('housing'):
        return [H['housings'][c['housing']]['box']]
    if where == 'end' and c.get('end_plug'):
        return [H['plugs'][c['end_plug']]]
    return [H['boxes'][part]] if part in H['boxes'] else []


def _gap(p, boxes):
    return min(pt_box_dist(p, b) for b in boxes) if boxes else float('inf')


def min_route(H, c, rounded_path):
    """(shortest route length, how): family minimum (+ longest branch), hump drawn out, or the fixed curve."""
    if c.get('family'):
        fr = family_range(rounded_path, c['curve'], c['family'])
        br = max([b['length'] for b in c['branches']] or [0.0])
        return (None if fr['min_mm'] is None else fr['min_mm'] + br), dict(family=fr, longest_branch_mm=br)
    if c.get('core'):
        hx = hump_excess(c['core']['upper_curve']['slack_hump'])
        return c['core']['modeled_length_mm'] - hx['excess_mm'], dict(hump=hx, modeled_mm=c['core']['modeled_length_mm'])
    L = c['curve'].get('rounded_length_mm') or arc_length(c['points'])
    return L, dict(fixed_curve_mm=L)


def cable_routes_rows(H, rounded_path):
    rows = []
    for cid, c in H['cables'].items():
        row = dict(category='cable_routes', id=cid, length_mm=c.get('length'), length_range=c.get('length_range'),
                   range_src=c.get('range_src'), estimate=True)
        if 'delegated' in c:
            rows.append(dict(row, status='info', covered_by=c['delegated']))
            continue
        if c['errors'] or not c['points']:
            rows.append(dict(row, status='fail', problems=['no current installed route: ' + '; '.join(
                c['errors'] or ['no centreline'])]))
            continue
        pts, probs = c['points'], []
        a, b = c['ends']
        if c['branches']:
            ga = max(_gap(br['points'][0], [H['housings'][br['id']]['box']]) for br in c['branches'])
            gb = _gap(pts[-1], _end_boxes(H, c, b, 'end'))
            end_gap = max(ga, gb)
            fan = max(math.dist(br['points'][-1], pts[0]) for br in c['branches'])
            row['fan_in_gap_mm'] = _r(fan, 2)
            if fan > ROUTE_END_TOL + 1e-9:
                probs.append('branch-to-main fan-in gap %.2f mm > %.1f (unmodeled fan-in; signal_routes fan_in_gate)'
                             % (fan, ROUTE_END_TOL))
        else:
            A0, B1 = _end_boxes(H, c, a, 'start'), _end_boxes(H, c, b, 'end')
            A1, B0 = _end_boxes(H, c, a, 'end'), _end_boxes(H, c, b, 'start')
            end_gap = min(max(_gap(pts[0], A0), _gap(pts[-1], B1)), max(_gap(pts[0], B0), _gap(pts[-1], A1)))
        if end_gap > ROUTE_END_TOL + 1e-9:
            probs.append('route ends %.2f mm from its end parts / plugs %s (> %.1f)' % (end_gap, list(c['ends']), ROUTE_END_TOL))
        lmin = (c.get('length_range') or (c['length'],))[0]
        mr, how = min_route(H, c, rounded_path)
        allow = route_allowance(c['length'])
        if mr is None:
            probs.append('no valid family member at the solver bounds')
        elif mr + allow > lmin + 1e-6:
            probs.append('shortest route %.1f + allowance %.1f > minimum stock %.1f mm' % (mr, allow, lmin))
        row.update(installed_mm=_r(c['curve'].get('rounded_length_mm') if c.get('curve') else arc_length(pts), 2),
                   min_route_mm=_r(mr, 2), allowance_mm=_r(allow, 1), length_min_mm=lmin,
                   slack_mm=None if mr is None else _r(lmin - mr - allow, 2), end_gap_mm=_r(end_gap, 2), basis=how,
                   problems=probs, status='fail' if probs else 'pass')
        rows.append(row)
    return rows


# ------------------------------------------------------------------ cable_stow (r7 C2 semantics)
def cable_stow_rows(H, rounded_path, finished=None):
    """Every mm of the longest purchased lead needs a modeled home: a stretched family absorbs up to its maximum;
    a fixed curve's spare with no home is 'info' (r7: 'no named home'); cut-to-length leads report the spare their
    finished length leaves in the closed pose (finished: {cable: minimum finished length from mate_reach})."""
    rows, finished = [], finished or {}
    for cid, c in H['cables'].items():
        row = dict(category='cable_stow', id=cid, estimate=True)
        if 'delegated' in c:
            rows.append(dict(row, status='info', covered_by=c['delegated']))
            continue
        if c['errors'] or not c['points']:
            rows.append(dict(row, status='info', home='no installed route (see cable_routes)'))
            continue
        lmax = (c.get('length_range') or (None, c['length']))[-1]
        if c.get('family'):
            fr = family_range(rounded_path, c['curve'], c['family'])
            br = max([b['length'] for b in c['branches']] or [0.0])
            cap = None if fr['max_mm'] is None else fr['max_mm'] + br
            pr = [] if cap is not None and cap >= lmax - 1e-6 else [
                'longest lead %.1f mm > family maximum %s mm: spare has no modeled home' % (lmax, _r(cap, 1))]
            rows.append(dict(row, kind='loop', home='%s loop (%s)' % (cid, fr['src']), length_max_mm=lmax,
                             family_min_mm=_r(None if fr['min_mm'] is None else fr['min_mm'] + br, 2),
                             family_max_mm=_r(cap, 2), problems=pr, status='fail' if pr else 'pass'))
        elif c.get('core'):
            hx = hump_excess(c['core']['upper_curve']['slack_hump'])
            rows.append(dict(row, kind='hump', home='stored hump (power_routes)', status='info',
                             hump_excess_mm=_r(hx['excess_mm'], 2),
                             note='cut to the 270 mm finished path; cut tolerance and stored-length fit are G-V-PIGTAIL'))
        else:
            route = c['curve'].get('rounded_length_mm') or arc_length(c['points'])
            total = finished.get(cid, lmax)
            rows.append(dict(row, kind='spare', status='info', closed_route_mm=_r(route, 2),
                             finished_length_mm=_r(total, 1), spare_mm=_r(total - route, 1),
                             home='no named home (r7 cable_stow info; give it a modeled home)'))
    return rows


# ------------------------------------------------------------------ header_housings (r7 C2 semantics)
def header_housing_rows(H, final_present, printed_dist=None, cots_dist=None):
    """r7 check_header_housings. COTS gaps use the proxy boxes (r7); where a box gap is under min_gap and cots_dist is
    given, the exact candidate proxy solid decides (the candidate's COTS proxies are STEP solids, not boxes)."""
    rows, hd = [], H['hdr']
    shrink = (max(hd['sec']) - min(hd['sec'])) / 2
    small = {k: [h['box'][0] + shrink, h['box'][1] - shrink, h['box'][2], h['box'][3], h['box'][4] + shrink,
                 h['box'][5] - shrink] for k, h in H['housings'].items()}
    for hid, h in H['housings'].items():
        b, pins, pr = h['box'], h['pins'], []
        typ = H['header_types'].get(hid)
        used = set(H['used_pins'].get(h['cable'], ()))
        if [p for p in pins if p not in used]:
            pr.append('covers unused pin(s) %s' % [p for p in pins if p not in used])
        if typ == '1' and len(pins) != 1:
            pr.append("type '1' with %d pins" % len(pins))
        elif typ == '1x2' and not (len(pins) == 2 and ((pins[0] % 2 == pins[1] % 2 and abs(pins[0] - pins[1]) == 2)
                                                     or (min(pins) % 2 == 1 and abs(pins[0] - pins[1]) == 1))):
            pr.append("type '1x2' on non-adjacent pins %s" % (pins,))
        elif typ not in ('1', '1x2'):
            pr.append('illegal housing type %r' % typ)
        cg = sorted((box_gap(H['boxes'][i], b), i) for i in final_present
                    if H['kinds'].get(i) == 'cots' and i != 'pi5' and i in H['boxes'])
        refined = {}
        if cots_dist:
            for g, i in cg:
                if g < HDR_MIN_GAP - 1e-9:
                    refined[i] = dict(box_gap_mm=_r(g, 2), exact_mm=_r(cots_dist(i, b), 3))
            cg = sorted((refined[i]['exact_mm'] if i in refined else g, i) for g, i in cg)
        if cg and cg[0][0] < HDR_MIN_GAP - 1e-9:
            pr.append('gap %.2f to COTS %s < %.1f' % (cg[0][0], cg[0][1], HDR_MIN_GAP))
        pg = []
        for i in final_present:
            if H['kinds'].get(i) != 'printed' or i not in H['boxes'] or box_gap(H['boxes'][i], b) > 3.0:
                continue
            d = printed_dist(i, b) if printed_dist else max(0.0, box_gap(H['boxes'][i], b))
            pg.append((d, i))
            if d < HDR_MIN_GAP - 1e-9:
                pr.append('distance %.2f to %s < %.1f' % (d, i, HDR_MIN_GAP))
        pg.sort()
        starts = [s for cab, s in H['branch_starts'] if cab == hid]
        con = min([math.dist(s, h['wire_exit']) for s in starts] or [float('inf')])
        if con > ROUTE_END_TOL + 1e-9:
            pr.append('no route starts at the housing wire exit (nearest %s mm)' % _r(con, 2))
        ov = [k for k, o in small.items() if k != hid and box_vol(small[hid], o) > 1e-9]
        if ov:
            pr.append('overlaps housing(s) %s' % ov)
        rows.append(dict(category='header_housings', id=hid, cable=h['cable'], type=typ, pins=pins,
                         box=[_r(x, 2) for x in b], cots_gap_mm=_r(cg[0][0], 2) if cg else None,
                         cots_nearest=cg[0][1] if cg else None, printed_gap_mm=_r(pg[0][0], 2) if pg else None,
                         cots_refined=refined, printed_nearest=pg[0][1] if pg else None, printed_method='exact STEP distance' if printed_dist
                         else 'bbox gap (no solids)', route_start_mm=_r(con, 3), problems=pr,
                         status='fail' if pr else 'pass'))
    return rows


# ------------------------------------------------------------------ family consistency (manifest-bound verifier)
def family_rows(H, rounded_path):
    rows = []
    for cid, c in H['cables'].items():
        if not c.get('family'):
            continue
        fr = family_range(rounded_path, c['curve'], c['family'])
        pr = []
        if not fr['knots_share_variable']:
            pr.append('family knots %s do not share one solver variable' % (c['family']['knots'],))
        if fr['recomputed_mm'] is None or abs(fr['recomputed_mm'] - fr['recorded_mm']) > 1e-6:
            pr.append('recomputed %s != recorded %s mm' % (fr['recomputed_mm'], fr['recorded_mm']))
        if not (min(fr['bound']) - 1e-9 <= fr['recorded'] <= max(fr['bound']) + 1e-9):
            pr.append('recorded %s outside the solver bound %s' % (fr['recorded'], fr['bound']))
        rows.append(dict(category='signal_routes', id='family_' + cid, family=fr, problems=pr,
                         status='fail' if pr else 'pass'))
    return rows


# ------------------------------------------------------------------ mate_reach (r7 C2/C3 semantics)
# One row per steps.CONNECTIONS end that is mated in a displaced pose. disp None: taken from the named motion's
# first knot (steps.MOTIONS). Anchor: the last route point fixed to the body at that op (see anchor_src).
MATE_POSES = [
    dict(id='qt_enc', connection='qt:enc', cable='qt', kind='plug', op='panel_prop', disp=(0.0, 60.0, 0.0),
         path_motion='panel_in', end='encoder', anchor_knot=6, axis=(1.0, 0.0, 0.0), row=(0.0, 0.0, 1.0),
         hand='pinch_sh', disp_src='ASSEMBLY-VERTICAL.md s6: baseline 60 mm prop offset (r7 MATE_POSES qt_enc)',
         anchor_src='secured-lane anchor: knot 6, the last route knot fixed to the body once the QT lead is in its '
                    'lanes (the wall loop may shrink to its family minimum); applies only if steps.py secures the '
                    'lead before panel_prop (lead_state, fixup-1)'),
    dict(id='j2_btn', connection='j2:btn', cable='power_button', kind='inline', op='panel_prop',
         disp=(0.0, 60.0, 0.0), path_motion='panel_in', end='power_button', anchor_knot=7, row=(0.0, 0.0, 1.0),
         hand='pinch_ph', junction_out=JUNCTION_OUT, halves=(('2181120201 female', 150.0, 6.0),
                                                             ('2181110202 male', 225.0, 6.0)),
         disp_src='ASSEMBLY-VERTICAL.md s6: baseline 60 mm prop offset',
         anchor_src='secured-lane anchor: knot 7, the last body-fixed knot once the J2 lead is in its lanes; applies '
                    'only if steps.py secures the lead before panel_prop (lead_state, fixup-1)'),
    dict(id='run_pi_37', connection='run_lead:pi', cable='run_pin37', kind='plug_reverse', op='module_staged',
         disp=None, path_motion='carrier_in', end='pi5', axis=(0.0, 1.0, 0.0), row=(0.0, 0.0, 1.0), hand='pinch_ph1',
         disp_src='steps.MOTIONS carrier_in first knot (module staged outside the open +Y side)',
         anchor_src='lanes are secured only at evf_mate (later): the lead is free beyond the top of its floor-hole '
                    'riser (the route knot after the button leg; the tail does not start lying on the floor)'),
    dict(id='run_pi_39', connection='run_lead:pi', cable='run_pin39', kind='plug_reverse', op='module_staged',
         disp=None, path_motion='carrier_in', end='pi5', axis=(0.0, 1.0, 0.0), row=(0.0, 0.0, 1.0), hand='pinch_ph1',
         disp_src='steps.MOTIONS carrier_in first knot (module staged outside the open +Y side)',
         anchor_src='as run_pi_37'),
    dict(id='xt30_pack', connection='xt30:pack', cable='pigtail', kind='pigtail', op='pack_in', end='xt30_pair',
         hand='pinch_xt30', axis=(0.0, 0.0, -1.0), row=(1.0, 0.0, 0.0), hang=('pack', 'pack_lead', 60.0),
         hang_motion='pack_in', disp_src='last rigid service pose of power_routes (battery-isolation pose)'),
]
MATE_INFO = [
    ('fps_1824', 'both ends mated on the bench (module_bench) and carried in one moving set (r7 both_moving info)'),
    ('fan', 'both ends mated on the bench (module_bench) and carried in one moving set (r7 both_moving info)'),
    ('camera_fpc:pi', 'in-situ mate at evf_mate through the CSI side slot: no displaced pose; reach = installed route '
                      '(cable_routes fpc), tool access = verify_csi_source; finger access HOLD'),
    ('evf_hdmi:evf', 'in-situ mate at evf_mate (head pushed up from below): reach = verify_hdmi carried ribbon'),
    ('evf_5v:evf', 'in-situ mate at evf_mate: the EVF feed has no current installed route (cable_routes usb_5v, '
                   'VN-60 / STOP)'),
]


def pose_state(ST, op_id):
    """(body ids before the op, moving ids) from the assembly-state model."""
    for o, before, _after, groups in ST.build_sequence():
        if o['id'] == op_id:
            moving = set(groups.get(o.get('group'), ())) if o['where'] in ('prop', 'bench') else set(o['adds'])
            return set(before), moving
    raise KeyError(op_id)


def box_hits(spec, targets):
    """Fallback hit test on boxes only (a cylinder by its bounding box): conservative."""
    b = spec['box'] if spec['type'] == 'box' else tail_box(spec['p0'], spec['p1'], spec['d'])
    return [dict(obstacle=t['id'], volume_mm3=_r(box_vol(b, t['box']), 2)) for t in targets
            if box_vol(b, t['box']) > SWEEP_TOL]


def _targets(H, body, moving, disp, exclude):
    out = []
    for i in sorted(body | moving):
        if i in exclude or i not in H['boxes']:
            continue
        d = tuple(disp) if i in moving else (0.0, 0.0, 0.0)
        out.append(dict(id=i, kind=H['kinds'][i], disp=d, box=shift(H['boxes'][i], d)))
    return out


def _segment_at_y(p0, p1, y):
    if (p1[1] - p0[1]) == 0 or not (min(p0[1], p1[1]) <= y <= max(p0[1], p1[1])):
        return None
    t = (y - p0[1]) / (p1[1] - p0[1])
    return [p0[i] + t * (p1[i] - p0[i]) for i in range(3)]


def mate_reach_rows(H, rounded_path, ST, hits=box_hits, lengths=None, retention=None):
    """lengths: {cable: L_min override} (regression fixtures). -> (rows, finished {cable: min finished length})."""
    lengths, rows, finished = lengths or {}, [], {}
    opening = ('+y', H['opening_y'], 0.0)
    for mp in MATE_POSES:
        row = dict(category='mate_reach', id=mp['id'], connection=mp['connection'], op=mp['op'], estimate=True,
                   disp_src=mp.get('disp_src'), anchor_src=mp.get('anchor_src'))
        body, moving = pose_state(ST, mp['op'])
        probs = []
        if mp['kind'] == 'pigtail':
            rows.append(_pigtail_mate_row(H, mp, row, body, moving, hits, retention, rounded_path))
            continue
        if mp['kind'] == 'inline':
            r, fin = _inline_row(H, mp, rounded_path, ST, hits, opening, lengths)
            rows.append(r)
            finished[mp['cable']] = fin
            continue
        c = H['cables'][mp['cable']]
        path = ST.MOTIONS[mp['path_motion']]['path']
        disp = tuple(mp['disp']) if mp.get('disp') else tuple(path[0])
        lmin = lengths.get(mp['cable'], (c.get('length_range') or (c['length'],))[0])
        if not on_path(path, disp):
            probs.append('mate pose %s not on the %s path' % (list(disp), mp['path_motion']))
        if mp['kind'] == 'plug':
            fam, curve = c['family'], c['curve']
            fr = family_range(rounded_path, curve, fam)
            br = max([b['length'] for b in c['branches']] or [0.0])
            fixed = br + family_eval(rounded_path, curve, fam, fr['min_at'], upto=mp['anchor_knot'])['length']
            apt = list(curve['knots'][mp['anchor_knot']])
            W = c['points'][-1]
            free_from = c['points'][0]
        else:   # plug_reverse: the fixed end is the route END (run button); the plug is the route START (header)
            pts, kn = c['points'], c['curve']['knots']
            if not (kn[-1][2] < H['floor_z'] < kn[-2][2]):
                probs.append('the last route leg does not rise through the floor plane z %.1f' % H['floor_z'])
            apt = list(kn[-2])
            fixed = math.dist(kn[-1], kn[-2])
            W = pts[0]
            free_from = None
        Wd = add(W, disp)
        tail = math.dist(apt, Wd)
        m = reach_margin(lmin)
        slack = lmin - fixed - tail - m

        def slack_at(dy):
            return lmin - fixed - math.dist(apt, [W[0] + disp[0], W[1] + dy, W[2] + disp[2]]) - m
        lo, hi = 0.0, 300.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if slack_at(mid) >= 0 else (lo, mid)
        row.update(cable=mp['cable'], pose=list(disp), length_min=lmin, margin=_r(m, 1), fixed_mm=_r(fixed, 1),
                   anchor_pt=[_r(x, 2) for x in apt], W_pose=[_r(x, 2) for x in Wd], tail_mm=_r(tail, 1),
                   slack_mm=_r(slack, 1), max_offset_y_for_reach_mm=_r(lo, 1) if slack_at(0.0) >= 0 else None)
        if free_from is not None:
            row['info_free_lead_need_mm'] = _r(br + math.dist(free_from, Wd) + m, 1)
            row['info_free_lead_note'] = ('if the lead were left out of its lanes until the panel closes: longest '
                                          'branch + straight main start to the posed plug + margin (lower bound, '
                                          'not obstacle-checked); see lead_state for whether this is the documented order')
        if slack < -1e-9:
            probs.append('lead short by %.1f mm in the mating pose (L %.0f, fixed %.1f, tail %.1f, margin %.1f)'
                         % (-slack, lmin, fixed, tail, m))
        hb = hand_box(Wd, mp['axis'], mp['row'], HAND_ENVELOPES[mp['hand']])
        tg = _targets(H, body, moving, disp, {mp['end']})
        hh = hits(dict(type='box', box=hb), tg)
        th = hits(dict(type='cyl', p0=apt, p1=Wd, d=TAIL_D), tg)
        oo = out_of_mm(hb, opening)
        row.update(hand=mp['hand'], hand_box=[_r(x, 2) for x in hb], hand_hits=hh, tail_hits=th,
                   out_of=list(opening), out_of_mm=_r(oo, 2), targets=len(tg))
        for bad, msg in ((hh, 'hand envelope hits %s' % ', '.join(h['obstacle'] for h in hh)),
                         (oo < -1e-9, 'hand envelope %.2f mm short of %s' % (-oo, list(opening))),
                         (th, 'tail path blocked by %s' % ', '.join(h['obstacle'] for h in th))):
            if bad:
                probs.append(msg)
        rows.append(dict(row, problems=probs, status='fail' if probs else 'pass'))
    for mp in MATE_POSES:
        if mp['kind'] in ('plug', 'inline'):
            _apply_lead_state(next(r for r in rows if r['id'] == mp['id']), mp, ST)
    for cid, why in MATE_INFO:
        rows.append(dict(category='mate_reach', id='info_' + cid.replace(':', '_'), connection=cid, status='info',
                         note=why))
    return rows, finished


def _apply_lead_state(row, mp, ST):
    """fixup-1: the reach above assumes the lead is already secured in its lanes (anchor knot). steps.py `secures`
    decides whether that is the documented order. If the lead is still free at the mating op, the secured-lane figures
    do not describe it: the row fails until a free-lead route from the header end is computed and obstacle-checked
    (no such route exists yet), and the secured-lane problems are kept, labelled, never dropped."""
    lead = mp['connection'].split(':')[0]
    at = ST.secured_at(lead)
    secured = ST.secured_before(lead, mp['op'])
    row['lead_state'] = ('secured in its lanes at %s, before %s' % (at, mp['op']) if secured else
                         'free at %s; laid into its lanes at %s (steps.py secures)' % (mp['op'], at))
    if secured:
        return
    lb = row.get('info_free_lead_need_mm')
    msg = ('lead is free at %s (secured only at %s): no obstacle-checked free-lead route from the header end to the '
           'posed end exists yet (FP-10 HOLD)' % (mp['op'], at))
    if lb is not None:
        msg += '; straight lower bound %.1f mm vs L_min %s (necessary only)' % (lb, row.get('length_min'))
        if lb > (row.get('length_min') or 0) + 1e-9:
            msg += ' - short even on the lower bound'
    row['problems'] = [msg] + ['secured-lane case (not the documented order): ' + p for p in row['problems']]
    row['status'] = 'fail'


def _inline_row(H, mp, rounded_path, ST, hits, opening, lengths=None):
    c = H['cables'][mp['cable']]
    body, moving = pose_state(ST, mp['op'])
    path = ST.MOTIONS[mp['path_motion']]['path']
    disp = tuple(mp['disp'])
    probs = [] if on_path(path, disp) else ['mate pose %s not on the %s path' % (list(disp), mp['path_motion'])]
    curve = c['curve']
    k = mp['anchor_knot']
    fixed = rounded_path(curve['knots'][:k + 1], curve['centerline_radius_mm'], curve['first_straight_min_mm'], 0.0,
                         0.5)['rounded_length_mm']
    apt, far = list(curve['knots'][k]), c['points'][-1]
    fd = add(far, disp)
    # The halves are cut to length, so the junction J is placed (not given): the first point on the anchor -> posed
    # far-end line that is junction_out beyond the opening AND puts the whole pinch box beyond it (r7 out_of).
    env = HAND_ENVELOPES[mp['hand']]
    dd = math.dist(apt, fd)
    u = [(fd[i] - apt[i]) / dd for i in range(3)]
    hb0 = hand_box(add([0.0, 0.0, 0.0], u, env[0] / 2), u, mp['row'], env)
    J = _segment_at_y(apt, fd, H['opening_y'] + max(mp['junction_out'], -hb0[2]))
    row = dict(category='mate_reach', id=mp['id'], connection=mp['connection'], op=mp['op'], cable=mp['cable'],
               pose=list(disp), fixed_mm=_r(fixed, 1), anchor_pt=[_r(x, 2) for x in apt],
               far_pose=[_r(x, 2) for x in fd], d_mm=_r(dd, 1), junction_out=mp['junction_out'],
               junction_rule='junction_out beyond the opening and the centred pinch box wholly beyond it (cut to length)',
               disp_src=mp['disp_src'], anchor_src=mp['anchor_src'], estimate=True)
    if J is None:
        probs.append('the posed far end lies less than %.1f mm beyond the opening' % mp['junction_out'])
        return dict(row, problems=probs, status='fail'), None
    body_need = fixed + math.dist(apt, J)
    far_need = math.dist(J, fd)
    assign = []
    halves = (lengths or {}).get(mp['cable'], mp['halves'])
    for (bn, bl, bt), (fn, fl, ft) in ((halves[0], halves[1]), (halves[1], halves[0])):
        nb, nf = body_need + reach_margin(bl - bt), far_need + reach_margin(fl - ft)
        assign.append(dict(body_side=bn, far_side=fn, body_need_mm=_r(nb, 1), body_min_mm=bl - bt,
                           far_need_mm=_r(nf, 1), far_min_mm=fl - ft,
                           feasible=nb <= bl - bt + 1e-9 and nf <= fl - ft + 1e-9))
    if not all(a['feasible'] for a in assign):
        probs.append('junction cannot sit %.1f mm beyond the opening for %s (side genders unassigned: VN-63)'
                     % (mp['junction_out'], [a['body_side'] for a in assign if not a['feasible']]))
    hb = hand_box(add(J, u, env[0] / 2), u, mp['row'], env)
    tg = _targets(H, body, moving, disp, {mp['end']})
    hh = hits(dict(type='box', box=hb), tg)
    th = hits(dict(type='cyl', p0=apt, p1=J, d=TAIL_D), tg)
    oo = out_of_mm(hb, opening)
    for bad, msg in ((hh, 'hand envelope hits %s' % ', '.join(h['obstacle'] for h in hh)),
                     (oo < -1e-9, 'hand envelope %.2f mm short of %s' % (-oo, list(opening))),
                     (th, 'tail path blocked by %s' % ', '.join(h['obstacle'] for h in th))):
        if bad:
            probs.append(msg)
    fin = min(a['body_need_mm'] + a['far_need_mm'] for a in assign)
    row.update(junction_at=[_r(x, 2) for x in J], assignments=assign, min_finished_length_mm=_r(fin, 1),
               hand=mp['hand'], hand_box=[_r(x, 2) for x in hb], hand_hits=hh, tail_hits=th, out_of=list(opening),
               out_of_mm=_r(oo, 2), targets=len(tg), problems=probs, status='fail' if probs else 'pass')
    return row, fin


def _pigtail_mate_row(H, mp, row, body, moving, hits, retention, rounded_path):
    retention = PIGTAIL_RETENTION if retention is None else retention
    W = face_isolation(H, 'positive')
    rr = {r['id']: r for r in pigtail_reach_rows(H, rounded_path, retention)}
    gate_row = rr['pigtail_xt30_mouth' if retention == 'carrier_ties' else 'pigtail_xt30_mouth_rtv_only']
    probs = ['reach: ' + p for p in gate_row['problems']]
    pose_out = H['mouth_z'] - W[2]
    if pose_out < FACE_OUT_MIN - 1e-9:
        probs.append('isolation pose puts the face only %.2f mm out of the mouth' % pose_out)
    hb = hand_box(W, tuple(-a for a in mp['axis']), mp['row'], HAND_ENVELOPES[mp['hand']])
    out_of = ('-z', H['mouth_z'], FACE_OUT_MIN)
    oo = out_of_mm(hb, out_of)
    part, lead, lead_len = mp['hang']
    tg = _targets(H, body, set(), (0.0, 0.0, 0.0), {mp['end'], part})
    pk = shift(H['boxes'][part], H['pack_in_start'])
    lower = min(0.0, hb[4] - pk[5])
    pk = shift(pk, (0.0, 0.0, lower))
    tg.append(dict(id=part + ' (hanging)', kind='cots', disp=tuple(add(H['pack_in_start'], (0.0, 0.0, lower))), box=pk))
    near = [min(max(W[i], pk[2 * i]), pk[2 * i + 1]) if i < 2 else pk[5] for i in range(3)]
    need = math.dist(W, near) + reach_margin(lead_len)
    if need > lead_len + 1e-9:
        probs.append('%s cannot hang below the hand on its %s: needs %.1f > %.0f mm' % (part, lead, need, lead_len))
    hh = hits(dict(type='box', box=hb), tg)
    for bad, msg in ((hh, 'hand envelope hits %s' % ', '.join(h['obstacle'] for h in hh)),
                     (oo < -1e-9, 'hand envelope %.2f mm short of %s' % (-oo, list(out_of)))):
        if bad:
            probs.append(msg)
    row.update(cable='pigtail', retention=retention, reach_model='lead_access ' + gate_row['id'],
               cores=gate_row['cores'], W_pose=[_r(x, 2) for x in W], pose_out_mm=_r(pose_out, 2), hand=mp['hand'],
               hand_box=[_r(x, 2) for x in hb], hand_hits=hh, out_of=list(out_of), out_of_mm=_r(oo, 2),
               hang=dict(part=part, cable=lead, lowered_mm=_r(-lower, 2), need_mm=_r(need, 1),
                         slack_mm=_r(lead_len - need, 1)), targets=len(tg), problems=probs,
               status='fail' if probs else 'pass')
    return row


def run_all(H, rounded_path, ST, hits=box_hits, printed_dist=None, retention=None, lengths=None, cots_dist=None):
    rows = family_rows(H, rounded_path)
    rows += cable_routes_rows(H, rounded_path)
    mr, finished = mate_reach_rows(H, rounded_path, ST, hits, lengths, retention)
    rows += mr
    rows += pigtail_reach_rows(H, rounded_path, retention)
    rows.append(pigtail_drop_row())
    rows += cable_stow_rows(H, rounded_path, finished)
    rows += header_housing_rows(H, set(ST.final_state()), printed_dist, cots_dist)
    apply_member_clearance(rows, H, rounded_path, set(ST.final_state()), hits)   # fixup-1 (FP-10)
    return rows


# ------------------------------------------------------------------ family member clearance (fixup-1, FP-10)
# A cable_stow 'loop' pass (the longest family member is the spare's home) and a cable_routes family-minimum pass
# (the shortest member is a valid route) rely on members at the solver bounds that routes never clearance-checked.
# r7 covered a stow home or route as a KEEPOUT box in its interference audit. Here each member used is swept as a
# cable-OD capsule (segment cylinders plus a cube of the capsule diameter at every joint, both enclosing the capsule)
# against the material present in the closed camera; the cable's own end parts are exempt (r7 own-end rule).
MEMBER_TOL = 0.1   # mm: polyline simplification tolerance; the capsule diameter is inflated by 2 x this


def simplify_polyline(points, tol=MEMBER_TOL):
    """Ramer-Douglas-Peucker: kept points such that every dropped point lies within tol of its chord."""
    pts = [list(p) for p in points]
    if len(pts) < 3:
        return pts
    keep, stack = {0, len(pts) - 1}, [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = pts[i], pts[j]
        ab = [b[k] - a[k] for k in range(3)]
        L2 = sum(x * x for x in ab) or 1e-18
        far, dmax = None, -1.0
        for m in range(i + 1, j):
            t = max(0.0, min(1.0, sum((pts[m][k] - a[k]) * ab[k] for k in range(3)) / L2))
            d = math.dist(pts[m], [a[k] + t * ab[k] for k in range(3)])
            if d > dmax:
                far, dmax = m, d
        if far is not None and dmax > tol:
            keep.add(far)
            stack += [(i, far), (far, j)]
    return [pts[k] for k in sorted(keep)]


def member_clearance(H, rounded_path, cid, value, final_present, hits=box_hits, tol=MEMBER_TOL):
    """Capsule sweep of cable `cid`'s family member with its solver variable = value."""
    c = H['cables'][cid]
    mem = family_eval(rounded_path, c['curve'], c['family'], value)
    pts = simplify_polyline(mem['points'], tol)
    d = (c.get('od_mm') or 0.0) + 2 * tol
    targets = _targets(H, set(final_present), set(), (0.0, 0.0, 0.0), set(c['ends']))
    found = {}
    specs = [dict(type='cyl', p0=p0, p1=p1, d=d) for p0, p1 in zip(pts, pts[1:]) if math.dist(p0, p1) > 1e-9]
    specs += [dict(type='box', box=[p[0] - d / 2, p[0] + d / 2, p[1] - d / 2, p[1] + d / 2, p[2] - d / 2, p[2] + d / 2])
              for p in pts[1:-1]]
    for spec in specs:
        for h in hits(spec, targets):
            found[h['obstacle']] = round(found.get(h['obstacle'], 0.0) + h['volume_mm3'], 2)
    return dict(variable=c['family']['var'], value=value, od_mm=c.get('od_mm'), capsule_d_mm=_r(d, 2),
                polyline_points=len(pts), pieces=len(specs), member_length_mm=_r(mem['length'], 2),
                exempt=sorted(c['ends']), targets=len(targets), hits=found, member_errors=mem['errors'])


def apply_member_clearance(rows, H, rounded_path, final_present, hits=box_hits):
    for r in rows:
        c = H['cables'].get(r.get('id'))
        if not c or not c.get('family') or r.get('status') != 'pass':
            continue
        if r['category'] == 'cable_stow' and r.get('kind') == 'loop':
            fr = family_range(rounded_path, c['curve'], c['family'])
            value = max(c['family']['bound'], key=lambda b: fr['length_at_bound_mm'][str(b)] if fr['valid_at_bound'][str(b)]
                        else float('-inf'))
            use = 'longest member (the spare home)'
        elif r['category'] == 'cable_routes' and isinstance(r.get('basis'), dict) and 'family' in r['basis']:
            value, use = r['basis']['family']['min_at'], 'shortest member (the minimum route)'
        else:
            continue
        mc = member_clearance(H, rounded_path, r['id'], value, final_present, hits)
        r['member_clearance'] = dict(mc, use=use)
        if mc['hits'] or mc['member_errors']:
            r.setdefault('problems', []).append(
                '%s at %s=%s intersects %s in the closed camera (capsule d %.2f mm)%s'
                % (use, mc['variable'], value, ', '.join('%s %.2f mm3' % kv for kv in sorted(mc['hits'].items())) or 'nothing',
                   mc['capsule_d_mm'], '; member errors: %s' % mc['member_errors'] if mc['member_errors'] else ''))
            r['status'] = 'fail'
