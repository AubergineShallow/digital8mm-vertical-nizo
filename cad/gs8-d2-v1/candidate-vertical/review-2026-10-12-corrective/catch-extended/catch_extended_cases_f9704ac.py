# SPDX-License-Identifier: MIT
"""Extended bonded-stub cases for the +Y tab catch (review 2026-10-12 corrective, GEO-1 / GEO-2 / CHE-2).

Run (repo root):  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/review-2026-10-12-corrective/catch-extended/catch_extended_cases.py --variant compact-kowa_lm6hc

Read-only on the design: it loads the committed STEPs of one variant (every manifest row, sha-checked against the
manifest), rebuilds the tub as print stock + displaced stub exactly as j7_collar_checks.roll_catch_stub_rows does,
and grades each pose with j7_collar_checks.roll_catch_rows (r7 check_roll_catch, unchanged rules, full BFAR range of
the variant lens, s_values=None as in verify_candidate). The rows kept are the ones roll_catch_stub_rows gates
(window and first_contact with status pass/fail). Nothing is copied from the rule code.

Cases (angles from model constants; pivots on the tenon datum or the joint-face bearing edges):
- tilt_on_joint_edge: the committed STUB_CASES pose (0.1 mm over the tenon height, about x). Validation only: its
  rows must equal the committed verification.json rows 'stub_tilt_on_joint_edge:*' (machinery check).
- T02_*: tilt about x at the full pocket y clearance (TAB_CATCH_POCKET_CLEAR y over the tenon height), pivot on the
  datum's joint edge (catch face swings -Y) or on its upper edge (whole stub swings +Y).
- Y*: yaw about z of the same 0.1 mm film variation across the tenon width, pivot on either x edge of the datum.
- R*: roll about y, pivot on either x edge of the stub joint face (bearing edge on the ceiling): (a) the 0.1 mm film
  variation across the joint-face width, (b) the pocket x clearance over the tenon height.
- info_committed_tilt_on_tenon_top_edge: the committed upper-pivot STUB_CASES pose, feasibility (overlap) only.
A pose whose displaced stub overlaps the print stock by more than FEASIBLE_OVERLAP_MM3 cannot occur inside the pocket
clearances; it is recorded as infeasible (with its overlap) and not graded. Source hashes are taken before the CAD
imports and re-checked at the end (sources_stable_during_run; a change makes the status 'error').
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CV = HERE.parents[1]
for _p in (str(CV.parent), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import read_text, write_text, relpath_posix  # noqa: E402

VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
FEASIBLE_OVERLAP_MM3 = 1e-3       # stub/stock overlap above this = pose blocked by the pocket or ceiling
FILM_VARIATION_MM = 0.1           # the same 0.1 mm the committed tilt case uses
SOURCES = ('j7_collar_checks.py', 'model.py', 'steps.py', '../checks.py',
           'review-2026-10-12-corrective/catch-extended/catch_extended_cases.py')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def case_table(model, web, jface):
    """[(case, axis, pivot, deg, basis)] from the model constants (deg is the right-hand rotation about +axis)."""
    tn, cl, zs = model.TAB_CATCH_TENON, model.TAB_CATCH_POCKET_CLEAR, model.TAB_CATCH_SPLIT_Z
    yin, h, w = web['y'][0], tn['h'], tn['x'][1] - tn['x'][0]
    wj = jface[1] - jface[0]
    xm = sum(web['x']) / 2
    t01 = math.degrees(math.atan(FILM_VARIATION_MM / h))
    t02 = math.degrees(math.atan(cl['y'] / h))
    yaw = math.degrees(math.atan(FILM_VARIATION_MM / w))
    rfilm = math.degrees(math.atan(FILM_VARIATION_MM / wj))
    rclr = math.degrees(math.atan(cl['x'] / h))
    return [
        ('tilt_on_joint_edge', 'x', (xm, yin, zs), -t01, 'validation: committed STUB_CASES pose, 0.1 mm over tenon h'),
        ('T02_tilt_on_joint_edge', 'x', (xm, yin, zs), -t02, 'pocket y clearance %.2f over tenon h %.1f' % (cl['y'], h)),
        ('T02_tilt_on_tenon_top_edge', 'x', (xm, yin, zs + h), t02, 'pocket y clearance over tenon h, upper pivot'),
        ('Y1_yaw_pivot_xminus', 'z', (tn['x'][0], yin, zs), yaw, '0.1 mm film variation across tenon width %.1f' % w),
        ('Y2_yaw_pivot_xplus', 'z', (tn['x'][1], yin, zs), -yaw, '0.1 mm film variation across tenon width %.1f' % w),
        ('R1_roll_film_pivot_xminus', 'y', (jface[0], yin, zs), rfilm, '0.1 mm film variation across joint face %.1f' % wj),
        ('R2_roll_film_pivot_xplus', 'y', (jface[1], yin, zs), -rfilm, '0.1 mm film variation across joint face %.1f' % wj),
        ('R3_roll_clear_pivot_xminus', 'y', (jface[0], yin, zs), rclr, 'pocket x clearance %.2f over tenon h' % cl['x']),
        ('R4_roll_clear_pivot_xplus', 'y', (jface[1], yin, zs), -rclr, 'pocket x clearance %.2f over tenon h' % cl['x']),
        ('info_committed_tilt_on_tenon_top_edge', 'x', (xm, yin, zs + h), t01,
         'committed STUB_CASES pose (graded by the main audit): feasibility only, not graded here'),
    ]


def keep(r):
    return r.get('item') in ('window', 'first_contact') and r.get('status') in ('pass', 'fail')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', default=VARIANTS[0], choices=VARIANTS)
    ap.add_argument('--out', default=None, help='default: catch-extended-<variant>.json next to this script')
    a = ap.parse_args()
    src0 = {s: sha(CV / s) for s in SOURCES}      # hashed before the imports: the record binds the code that ran
    import cadquery as cq
    import model
    import checks as CK
    import steps as ST
    import j7_collar_checks as J
    t0 = time.time()
    out_dir = CV / 'out' / a.variant
    mpath = out_dir / 'manifest.json'
    meta = json.loads(read_text(mpath))
    rows = {r['id']: r for r in meta['rows']}
    shapes, steps_bound = {}, {}
    for k in sorted(rows):
        p = out_dir / 'step' / ('%s.step' % k)
        s = sha(p)
        if s != meta['files'].get('step/%s.step' % k):
            raise SystemExit('STEP %s does not match the manifest binding' % k)
        steps_bound[k] = s
        shapes[k] = cq.importers.importStep(str(p)).val()
    load_s = time.time() - t0
    ver_path = out_dir / 'verification.json'
    ver = json.loads(read_text(ver_path))
    committed = {c['id']: c for c in ver['checks'] if c.get('category') == 'roll_catch'}
    lens = J.lens_of(a.variant, meta)
    rr = J.r7_rows(shapes, rows)
    tub = rr['tub']['shape']
    with __import__('j4_trial_geometry').trial_layout(model.L, lip=2.4, head=2.4):
        stock, stub = model.tub_print_parts(tub)
        tc = {(b['side'], b['kind']): b for b in model.L.tab_catch_boxes()}
    web = tc[(1, 'web')]
    jface = tuple(web['x'])                     # stub joint face x extent (web box; the flange lies inside it)
    axes = {'x': cq.Vector(1, 0, 0), 'y': cq.Vector(0, 1, 0), 'z': cq.Vector(0, 0, 1)}
    cases, out_rows = [], []
    with J.candidate_layout(lens) as L:
        for case, axis, piv, deg, basis in case_table(model, web, jface):
            t1 = time.time()
            pv = cq.Vector(*piv)
            sb = stub.rotate(pv, pv + axes[axis], deg)
            ov = float(stock.intersect(sb).Volume())
            rec = dict(case=case, axis=axis, pivot=list(piv), deg=deg, basis=basis, stub_stock_overlap_mm3=round(ov, 6),
                       feasible=ov <= FEASIBLE_OVERLAP_MM3)
            if rec['feasible'] and not case.startswith('info_'):
                t_case = stock.fuse(sb).clean()
                rr_case = dict(rr, tub=dict(rr['tub'], shape=t_case))
                got = [(ident, r) for _, ident, r in J.roll_catch_rows(L, rr_case, shapes, CK, ST) if keep(r)]
                for ident, r in got:
                    out_rows.append(dict(r, id='ext_%s:%s' % (case, ident), stub_case=case, stub_axis=axis,
                                         stub_deg=deg, stub_pivot=list(piv)))
                fails = [ident for ident, r in got if r['status'] == 'fail']
                wins = [r['worst_gap'] for _, r in got if r.get('item') == 'window' and r.get('worst_gap') is not None]
                rec.update(rows=len(got), fail_rows=fails, min_worst_window_gap=min(wins) if wins else None)
                if case == 'tilt_on_joint_edge':
                    diff = []
                    for ident, r in got:
                        c = committed.get('stub_tilt_on_joint_edge:%s' % ident)
                        k2 = ('status', 'worst_gap', 'centred_gap', 'metal_min_deg', 'metal_max_deg')
                        if c is None or any(c.get(x) != r.get(x) for x in k2):
                            diff.append(ident)
                    rec.update(validation_rows_compared=len(got), validation_mismatch=diff,
                               validation_committed_rows=len([i for i in committed if i.startswith('stub_tilt_on_joint_edge:')]))
            rec['seconds'] = round(time.time() - t1, 1)
            cases.append(rec)
            print(json.dumps({k: v for k, v in rec.items() if k != 'fail_rows'}), flush=True)
    ext = [c for c in cases if c['case'] != 'tilt_on_joint_edge' and not c['case'].startswith('info_')]
    val = cases[0]
    valid = val.get('feasible') and not val.get('validation_mismatch') and \
        val.get('validation_rows_compared') == val.get('validation_committed_rows')
    failing = [c['case'] for c in ext if c.get('feasible') and c.get('fail_rows')]
    stable = src0 == {s: sha(CV / s) for s in SOURCES}
    status = 'error' if not (valid and stable) else ('fail' if failing else 'pass')
    rel = lambda p: relpath_posix(p, CV)          # noqa: E731
    res = dict(
        purpose='Extended bonded-stub poses for the +Y tab catch (GEO-1 / GEO-2 / CHE-2); not part of the gated '
                'audit until folded into j7_collar_checks.STUB_CASES at the next re-export',
        variant=a.variant, lens=lens, manifest=rel(mpath), manifest_sha256=sha(mpath),
        verification=rel(ver_path), verification_sha256=sha(ver_path),
        step_sha256=steps_bound, sources=src0, sources_stable_during_run=stable,
        rule='r7 check_roll_catch unchanged: window centred >= 0.30 and worst offset >= 0.10 mm; first contact margin',
        feasible_overlap_mm3=FEASIBLE_OVERLAP_MM3, film_variation_mm=FILM_VARIATION_MM,
        tenon=model.TAB_CATCH_TENON, pocket_clear=model.TAB_CATCH_POCKET_CLEAR, split_z=model.TAB_CATCH_SPLIT_Z,
        validation=dict(case='tilt_on_joint_edge', matches_committed=bool(valid)),
        status=status, failing_cases=failing,
        catch='OPEN: decision 16 not closed' if status != 'pass' else 'extended cases pass',
        cases=cases, checks=out_rows, load_seconds=round(load_s, 1), seconds=round(time.time() - t0, 1))
    dest = Path(a.out) if a.out else HERE / ('catch-extended-%s.json' % a.variant)
    write_text(dest, json.dumps(res, indent=1, sort_keys=True) + '\n')
    print('status', status, 'failing', failing, 'valid', valid, flush=True)


if __name__ == '__main__':
    main()
