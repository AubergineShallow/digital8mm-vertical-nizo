# SPDX-License-Identifier: MIT
"""FP-12 check-scope rules (review 2026-10-10: VN-30, VN-33, VN-34, VN-35, VN-36, VN-37, VN-38). CAD-free.

Pure functions used by verify_check_scope.py (the batch row `check_scope`), structural-review/
update_concealed_vent_structure.py and tests/test_check_scope.py. Nothing here is a measurement: every input comes
from a manifest, a saved STEP measured by the caller, a routing snapshot, steps.py or the r7 project files, and every
unknown stays an explicit None with the gate that closes it.
"""
import math

G = 9.80665

# ------------------------------------------------------------------------------------------- VN-33 J4 screen
# The export18 structural free body (reference-export18-structural-binding.json integrated_upper_body_screen)
# excludes the lower grip/battery hardware. The ids are the steps.py groups GRIP + strap + p_grip + POWER_IDS;
# j4_lower_set() proves they are exactly the excluded rows by the mass identity sum(lower) == total - upper.
J4_LOWER_IDS = ('base_grip', 'tripod_nut', 'run_button', 'strap', 'p_grip', 'xt30_pair', 'pack', 'cap')
J4_COMPACT_SCREEN_NM = 0.95      # the compact-Kowa proposal already printed in CONCEALED-VENT-STRUCTURAL.md
SHARE_70 = 0.7


def j4_lower_set(ref, old):
    """-> (ids, residual_g). Raises if the declared lower set does not reproduce the reference upper mass."""
    rows = {r['id']: r for r in old['rows']}
    missing = [i for i in J4_LOWER_IDS if i not in rows]
    if missing:
        raise ValueError('J4 lower ids missing from the reference manifest: %s' % missing)
    lower = sum(rows[i]['mass_est_g'] for i in J4_LOWER_IDS)
    residual = old['mass_est_g'] - ref['integrated_upper_body_screen']['estimated_mass_g'] - lower
    if abs(residual) > 1e-6:
        raise ValueError('J4 lower set does not match the reference free body (residual %.9f g)' % residual)
    return list(J4_LOWER_IDS), residual


def round_screen(x):
    return math.ceil(x * 20 - 1e-9) / 20


def j4_screen(ref, old, new, changed_rows):
    """First-moment transfer of the export18 upper free body to manifest `new` (update_concealed_vent_structure
    method). `changed_rows(a, b)` is evidence_rules.changed_rows. Refuses (valid=False) when a lower row changed,
    appeared or disappeared, because the transfer then needs a new free body."""
    lower, _ = j4_lower_set(ref, old)
    a = {r['id']: r for r in old['rows']}
    b = {r['id']: r for r in new['rows']}
    common = sorted(set(a) & set(b))
    changed = changed_rows({k: a[k] for k in common}, {k: b[k] for k in common})
    added, removed = sorted(set(b) - set(a)), sorted(set(a) - set(b))
    touched = set(changed) | set(added) | set(removed)
    bad = sorted(touched & set(lower))
    up = ref['integrated_upper_body_screen']
    res = dict(changed_rows=list(changed), added_rows=added, removed_rows=removed, lower_rows=lower,
               lower_rows_touched=bad, valid=not bad)
    if bad:
        res['reason'] = 'lower free-body rows changed: %s; the first-moment transfer needs a new free body' % bad
        return res
    dm = new['mass_est_g'] - old['mass_est_g']
    um = up['estimated_mass_g'] + dm
    first = [up['estimated_mass_g'] * up['estimated_com_mm'][i] + new['mass_est_g'] * new['com_est_mm'][i]
             - old['mass_est_g'] * old['com_est_mm'][i] for i in range(3)]
    floor = first[2] / 1000 * G * 5
    wire = ref['unresolved_wiring_mass_sensitivity']['added_5g_moment_Nmm']
    equal = (floor + wire) / 2000
    res.update(upper_mass_g=um, upper_com_mm=[x / um for x in first], floor_moment_5g_Nmm=floor,
               wiring_5g_moment_Nmm=wire, equal_share_plus_wiring_Nm=equal,
               seventy_percent_share_plus_wiring_Nm=(floor + wire) * SHARE_70 / 1000,
               proposed_rounded_equal_share_screen_Nm=round_screen(equal))
    return res


def j4_envelope(per_variant):
    """Screen that covers every valid variant's equal-share target, and the coverage of the compact 0.95 value."""
    ok = {v: r for v, r in per_variant.items() if r.get('valid')}
    worst = max(ok.values(), key=lambda r: r['equal_share_plus_wiring_Nm']) if ok else None
    return dict(all_variants_screen_Nm=None if worst is None else round_screen(worst['equal_share_plus_wiring_Nm']),
                governing_variant=None if worst is None else [v for v, r in ok.items() if r is worst][0],
                compact_screen_Nm=J4_COMPACT_SCREEN_NM,
                compact_screen_covers={v: J4_COMPACT_SCREEN_NM + 1e-12 >= r['equal_share_plus_wiring_Nm']
                                       for v, r in ok.items()},
                invalid_variants=sorted(set(per_variant) - set(ok)))


# ------------------------------------------------------------------------------------------- VN-37 area parity
def branch_parity(branches, ports_mm2, tol=0.002):
    """branches: [{name, mouth_mm2, series_mm2: [sampled sections between the ports and that mouth]}].
    Effective branch area = min(mouth, every series section); pass iff the sum >= the wall ports (old row's tol)."""
    out = []
    for b in branches:
        smin = min(b['series_mm2']) if b['series_mm2'] else None
        eff = b['mouth_mm2'] if smin is None else min(b['mouth_mm2'], smin)
        out.append(dict(name=b['name'], mouth_mm2=b['mouth_mm2'], series_min_mm2=smin, effective_mm2=eff,
                        governed_by='mouth' if smin is None or b['mouth_mm2'] <= smin else 'series section'))
    total = sum(b['effective_mm2'] for b in out)
    return dict(branches=out, effective_sum_mm2=total, wall_ports_mm2=ports_mm2, margin_mm2=total - ports_mm2,
                margin_percent=(total - ports_mm2) / ports_mm2 * 100, passed=total >= ports_mm2 - tol)


# ------------------------------------------------------------------------------------------- VN-36 flow network
def series(*areas):
    """Orifice-equivalent area of restrictions in series (same discharge coefficient): (sum A^-2)^-1/2."""
    if any(a <= 0 for a in areas):
        return 0.0
    return sum(a ** -2 for a in areas) ** -0.5


def parallel(*areas):
    return sum(areas)


FLOW_CASES = [  # (id, {element: open fraction}, note). Elements absent from a case are fully open.
    ('nominal', {}, 'all mouths, ports and the CSI slot open'),
    ('cold_rear_blocked', {'cold_rear': 0.0}, 'rear cold mouth covered (hand/strap)'),
    ('cold_bottom_blocked', {'cold_bottom': 0.0}, 'underside cold mouth covered'),
    ('cold_bottom_strap_20_of_71', {'cold_bottom': 1 - 20 / 71.0},
     'strap envelope over 20 of 71 mm of the underside cold mouth (review PRI-12 geometry, not a measurement)'),
    ('hot_bottom_blocked', {'hot_bottom': 0.0}, 'underside hot mouth covered'),
    ('hot_front_blocked', {'hot_front': 0.0}, 'front hot mouth covered'),
    ('set_down_on_table', {'cold_bottom': 0.0, 'hot_bottom': 0.0}, 'both underside mouths on a flat surface'),
    ('csi_plugged', {'csi': 0.0}, 'CSI slot sealed: information for user decision VN-36 only, not adopted'),
]


def flow_network(el, cases=FLOW_CASES):
    """Report-only orifice network. el: cold_rear/cold_bottom/hot_bottom/hot_front = {mouth_mm2, series_min_mm2},
    cold_ports_mm2, hot_ports_mm2, csi_mm2. Topology: ambient -> (cold branches || -> cold wall ports) || CSI slot
    -> main cavity -> fan -> hot wall ports -> (hot branches ||) -> ambient. With one discharge coefficient for every
    restriction, flow fractions are independent of Cd and of the fan pressure; absolute flow needs the fan curve,
    which is UNKNOWN (no P-Q data in the repo), so no operating point is computed."""
    def branch(name, f):
        e = el[name]
        return f * series(e['mouth_mm2'], e['series_min_mm2']) if f > 0 else 0.0
    rows = []
    nominal = None
    for cid, open_, note in cases:
        f = lambda k: open_.get(k, 1.0)  # noqa: E731
        cold_mouths = parallel(branch('cold_rear', f('cold_rear')), branch('cold_bottom', f('cold_bottom')))
        cold = series(cold_mouths, el['cold_ports_mm2']) if cold_mouths > 0 else 0.0
        csi = el['csi_mm2'] * f('csi')
        intake = parallel(cold, csi)
        hot_mouths = parallel(branch('hot_bottom', f('hot_bottom')), branch('hot_front', f('hot_front')))
        exhaust = series(el['hot_ports_mm2'], hot_mouths) if hot_mouths > 0 else 0.0
        system = series(intake, exhaust) if intake > 0 and exhaust > 0 else 0.0
        r = dict(case=cid, note=note, open_fraction=dict(open_), cold_path_eff_mm2=cold, csi_eff_mm2=csi,
                 intake_eff_mm2=intake, exhaust_eff_mm2=exhaust, system_eff_mm2=system,
                 csi_share_of_intake=None if intake <= 0 else csi / intake,
                 cold_path_share_of_intake=None if intake <= 0 else cold / intake)
        if nominal is None:
            nominal = r
        r['system_flow_ratio_vs_nominal'] = system / nominal['system_eff_mm2'] if nominal['system_eff_mm2'] else None
        r['intake_area_change_percent'] = (intake / nominal['intake_eff_mm2'] - 1) * 100
        rows.append(r)
    return rows


def flow_drift(rows, baseline):
    """fixup-1 (VN-36): (ok, details). The flow-network rows stay report-only (fan curve UNKNOWN), but a recomputed
    effective area or share that differs from the recorded baseline (relative tolerance rel_tol) fails until the
    baseline file is rewritten with a reason, so a CAD change that cuts the cold path or enlarges the CSI share is seen."""
    tol = baseline['rel_tol']
    got = {r['case'] if 'case' in r else r['id']: r for r in rows}
    drifts, missing = [], sorted(set(baseline['cases']) - set(got))
    for cid, want in sorted(baseline['cases'].items()):
        if cid not in got:
            continue
        for k in baseline['fields']:
            a, b = got[cid].get(k), want[k]
            if a is None or b is None:
                if a != b:
                    drifts.append(dict(case=cid, field=k, recorded=b, computed=a))
            elif abs(a - b) > tol * max(1.0, abs(b)):
                drifts.append(dict(case=cid, field=k, recorded=b, computed=a, change_percent=(a / b - 1) * 100 if b else None))
    return not drifts and not missing, dict(drifts=drifts, missing_cases=missing, baseline_reason=baseline['reason'],
                                             rel_tol=tol, compared_cases=len(baseline['cases']) - len(missing))


# ------------------------------------------------------------------------------------------- VN-35 HDMI face normal
def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(a):
    m = math.sqrt(_dot(a, a))
    return [x / m for x in a]


def track_face(frames, max_step_mm=2.5, max_turn_deg=30.0):
    """Carry one physical face of the strip along hdmi_routes frames (material order). The per-frame `normal` is a
    formula vector whose sign may jump between route pieces; the physical normal is the frame normal with the sign
    that keeps it continuous. -> dict(end normals, formula sign changes, largest step and turn, ok)."""
    pts = [f['point'] for f in frames]
    steps = [math.dist(p, q) for p, q in zip(pts, pts[1:])]
    phys = [_norm(frames[0]['normal'])]
    sign_changes, worst_turn, sign = [], 0.0, 1
    for i in range(1, len(frames)):
        n = _norm(frames[i]['normal'])
        d = _dot(phys[-1], n)
        s = -1 if d < 0 else 1           # physical = s * formula normal
        if s != sign:
            sign_changes.append(i)       # the formula's sign convention changes here
            sign = s
        if s < 0:
            n = [-x for x in n]
        turn = math.degrees(math.acos(max(-1.0, min(1.0, abs(d)))))
        worst_turn = max(worst_turn, turn)
        phys.append(n)
    return dict(frames=len(frames), max_point_step_mm=max(steps) if steps else 0.0, max_turn_deg=worst_turn,
                formula_sign_changes_at=sign_changes, start_normal=phys[0], end_normal=phys[-1],
                start_point=pts[0], end_point=pts[-1],
                ok=(max(steps) if steps else 0.0) <= max_step_mm and worst_turn <= max_turn_deg)


def axis_name(v, tol=1e-6):
    """'+X'/'-Y'/... for an axis-aligned unit vector, else None."""
    for i, ax in enumerate('XYZ'):
        if abs(abs(v[i]) - 1) < tol and all(abs(v[j]) < tol for j in range(3) if j != i):
            return ('+' if v[i] > 0 else '-') + ax
    return None


# Contact sides are UNMEASURED: each is the global axis toward which the head's ribbon contacts face when mated as
# modelled, or for the ribbon, 'same' / 'opposite' (contacts on the same face at both ends or not). None = HOLD.
# Gate: MEASUREMENTS-TO-CLOSE 'Adafruit HDMI 3557/3556 heads and intact 3562 ribbon' (G-V-HDMI).
HDMI_CONTACT_SIDES = dict(pi_head_3557=None, evf_head_3556=None, ribbon_3562=None)


def face_match(pi_normal, evf_normal, sides=None):
    """Required contact sides for both ribbon conventions, and pass/fail once the real sides are recorded.
    The ribbon face A is the physical face whose outward normal is `pi_normal` at the Pi head; it reaches the EVF
    head with outward normal `evf_normal`. Contacts on face A must meet head contacts lying on the face-A side."""
    sides = dict(HDMI_CONTACT_SIDES if sides is None else sides)
    pa, ea = axis_name(pi_normal), axis_name(evf_normal)
    neg = lambda s: None if s is None else ('-' if s[0] == '+' else '+') + s[1]  # noqa: E731
    req = {'same': dict(pi_head_3557=pa, evf_head_3556=ea), 'opposite': dict(pi_head_3557=pa, evf_head_3556=neg(ea))}
    res = dict(face_a_at_pi=pa, face_a_at_evf=ea, required_if_ribbon=req, recorded=sides)
    if any(v is None for v in sides.values()):
        res.update(status=None, hold='head and ribbon contact sides unmeasured (G-V-HDMI receipt gate)')
        return res
    want = req[sides['ribbon_3562']]
    # The ribbon may be flipped end for end at assembly only by re-forming the route; the route fixes face A.
    pi_ok = sides['pi_head_3557'] in (want['pi_head_3557'], neg(want['pi_head_3557']))
    flip = sides['pi_head_3557'] != want['pi_head_3557']       # contacts on face B instead: both ends swap
    evf_want = neg(want['evf_head_3556']) if flip else want['evf_head_3556']
    res.update(status=pi_ok and sides['evf_head_3556'] == evf_want, contacts_on='B' if flip else 'A')
    return res


# ------------------------------------------------------------------------------------------- VN-38 stack retention
def stack_retention(ret_points, com_xz, targets, CK, bearing_r=None):
    """r7 checks.check_stack_retention rules on the candidate's vertical carrier (plane XZ, lift = +-Y).
    ret_points: [((x, z), gap)] retention points; contacts (lift >= 0) are the same declared bearing points
    (post tops). CK = r7 checks module (_hull2, _inside_margin, _max_lift, unchanged)."""
    pts = [p for p, _ in ret_points]
    hull = CK._hull2(pts)
    margin = None if len(hull) < 3 else CK._inside_margin(hull, com_xz)
    lifts = {'(%.1f, %.1f)' % t: CK._max_lift(ret_points, pts, t) for t in targets}
    line = None
    if len(pts) == 2:
        (x0, z0), (x1, z1) = pts
        L = math.hypot(x1 - x0, z1 - z0)
        line = abs((x1 - x0) * (z0 - com_xz[1]) - (x0 - com_xz[0]) * (z1 - z0)) / L
    ok_lift = all(v is not None for v in lifts.values())
    return dict(retention_points=[[p[0], p[1], g] for p, g in ret_points], hull=hull, stack_com_xz=list(com_xz),
                com_inside_hull_margin_mm=margin, max_lift_mm=lifts, lift_bounded=ok_lift,
                com_distance_from_screw_line_mm=line, bearing_radius_mm=bearing_r,
                com_within_bearing_stadium=None if line is None or bearing_r is None else line <= bearing_r,
                passed=margin is not None and margin > 0 and ok_lift)


def post_root_bending(mass_g, posts, d_mm, length_mm, ecc_mm, g_level=5.0, shares=(0.5, SHARE_70),
                      screen_mpa=5.0):
    """Solid round post, lateral load F = m g g_level at the carrier, share s per post. Root moment
    M = s F (length + ecc): cantilever tip load plus the eccentric couple of the stack CoM about the post tops,
    added to one post (conservative). sigma = 32 M / (pi d^3)."""
    F = mass_g / 1000 * G * g_level
    z = math.pi * d_mm ** 3 / 32
    rows = []
    for s in shares:
        M = s * F * (length_mm + ecc_mm)
        rows.append(dict(share=s, post_force_N=s * F, root_moment_Nmm=M, root_stress_MPa=M / z))
    worst = max(r['root_stress_MPa'] for r in rows)
    return dict(mass_g=mass_g, post_count=posts, g_level=g_level, force_N=F, diameter_mm=d_mm, length_mm=length_mm,
                eccentricity_mm=ecc_mm, section_modulus_mm3=z, cases=rows, worst_stress_MPa=worst,
                screen_MPa=screen_mpa, passed=worst <= screen_mpa)


# ------------------------------------------------------------------------------------------- VN-34 eye/face
def evf_geometry(rows, body_ids, eyepiece='eyepiece', eyecup='eyecup', spigot_mm=4.5):
    """Axis, flange and face-side extents from manifest bboxes [x0,x1,y0,y1,z0,z1]. The eyepiece is a solid of
    revolution about the EVF axis, so its bbox centre is the axis; its +X end is the spigot end (F + spigot)."""
    e, c = rows[eyepiece], rows[eyecup]
    ay, az = (e[2] + e[3]) / 2, (e[4] + e[5]) / 2
    body = [rows[i] for i in body_ids if i in rows]
    bx0 = min(b[0] for b in body)
    by0, by1 = min(b[2] for b in body), max(b[3] for b in body)
    bz1 = max(b[5] for b in body)
    return dict(axis_y=ay, axis_z=az, flange_x=e[1] - spigot_mm, eyecup_rear_x=c[0], body_rear_x=bx0,
                eyecup_protrusion_mm=bx0 - c[0], left_extent_mm=by1 - ay, right_extent_mm=ay - by0,
                top_extent_mm=bz1 - az, body_ids=[i for i in body_ids if i in rows])


BBOX_RESOLUTION_MM = 0.05   # r7 out/parts-manifest.json bboxes are OCC bounding boxes rounded to 0.01 mm (its
#                            eyepiece gives axis Z 78.01 / F -153.98 for layout Z78 / F-154); finer differences are
#                            below what the r7 source resolves, so they are reported but not judged.


def evf_face_screen(cand, r7, tol=BBOX_RESOLUTION_MM):
    """No-regression screen against r7 (the only accepted baseline; no anthropometric data in the repo):
    the eyecup must protrude at least as far behind the body, and the body must extend no further beyond the axis
    on the operator-left (+Y, nose side for the right eye), operator-right (-Y) and top sides."""
    rows = []
    for k, better in (('eyecup_protrusion_mm', 'higher'), ('left_extent_mm', 'lower'),
                      ('right_extent_mm', 'lower'), ('top_extent_mm', 'lower')):
        d = cand[k] - r7[k]
        ok = d >= -tol if better == 'higher' else d <= tol
        rows.append(dict(id=k, candidate=cand[k], r7=r7[k], delta=d, better=better, resolution_mm=tol, passed=ok))
    return rows
