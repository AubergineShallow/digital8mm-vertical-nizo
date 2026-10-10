# SPDX-License-Identifier: MIT
"""Computed print gates for the candidate (review VN-25, fix FP-09). Run through ../run_locked.py.

Bound to the variant manifest: every STL/STEP is checked against manifest['files'] before use and the
manifest hash must not change during the run. Categories (rows keep r7's row shapes):
  print_overhang          r7 checks.check_print_overhang, unchanged, on the bound print-pose STLs, with the
                          candidate's declared support zones (print_rules.j4_wing_zones) mapped by the pose
  print_bridge_direction  print_rules.check_bridge_direction: one raster direction per connected bridge region
  thin_wall               r7 checks.thin_wall on the bound finished-part STEPs, candidate loaded zones
  critical_features       r7 checks.check_critical_features on the same STEPs (r7 registries, candidate PARTS)
Failures are reported, never waived; exit 1 when any row fails. Writes out/<variant>/print-checks.json.
"""
from cv_io import read_text, rel_posix, write_text
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

CV = Path(__file__).resolve().parent
sys.path.insert(0, str(CV))
import print_rules as PR     # noqa: E402
CK = PR.CK
CATEGORIES = ('print_overhang', 'print_bridge_direction', 'thin_wall', 'critical_features')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jsonable(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def bound(out, manifest, rel):
    """Path of a manifest-bound output file; raises when missing or not the bound bytes."""
    p = out / rel
    want = manifest['files'].get(rel)
    if want is None or not p.exists() or sha(p) != want:
        raise ValueError('not the manifest-bound file: %s' % rel)
    return p


def overhang_rows(out, manifest, state, parts):
    L = state['layout']
    o = dict(L.PRINT_OVERHANG)
    rows_ov, rows_bd = [], []
    for pid in parts:
        pose = manifest['print_poses'][pid]
        fd = pose['face_down']
        R, t = PR.pose_transform(pose)
        zones = [dict(z, box=PR.map_box(z['box'], R, t)) for z in state['zones'].get(pid, [])]
        t0 = time.time()
        try:
            man = PR.manifold_from_stl(bound(out, manifest, 'stl/%s.stl' % pid))
            ov = CK.check_print_overhang(L, pid, man, zones, face_down=fd)
            bd = PR.check_bridge_direction(L, pid, man, zones, face_down=fd)
        except Exception as e:  # noqa: BLE001 - a failed check is a FAIL row, never a skipped one
            err = '%s: %s' % (type(e).__name__, str(e)[:300])
            ov = dict(kind='print_overhang', part=pid, face_down=fd, status='fail', error=err)
            bd = dict(kind='print_bridge_direction', part=pid, face_down=fd, status='fail', error=err)
        for r in (ov, bd):
            r.update(stl='stl/%s.stl' % pid, pose=dict(R=R, t=t), seconds=round(time.time() - t0, 1),
                     zones_assembly=[dict(id=z['id'], box=list(z['box'])) for z in state['zones'].get(pid, [])])
            PR.annotate_regions(r, R, t, o['layer'])
        rows_ov.append(ov)
        rows_bd.append(bd)
        print(pid, 'overhang', ov['status'], 'direction', bd['status'], bd.get('longest_bridge_mm'),
              'failing', bd.get('failing_region_count'), flush=True)
    return rows_ov, rows_bd


def step_shapes(out, manifest, parts):
    import cadquery as cq
    shapes = {}
    for pid in parts:
        shapes[pid] = cq.importers.importStep(str(bound(out, manifest, 'step/%s.step' % pid))).val()
    return shapes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', default='compact-kowa_lm6hc')
    ap.add_argument('--categories', default=','.join(CATEGORIES))
    ap.add_argument('--out', default=None, help='report path (default out/<variant>/print-checks.json)')
    a = ap.parse_args()
    cats = [c for c in a.categories.split(',') if c]
    if set(cats) - set(CATEGORIES):
        raise SystemExit('unknown category: %s' % sorted(set(cats) - set(CATEGORIES)))
    out = CV / 'out' / a.variant
    mpath = out / 'manifest.json'
    h0 = sha(mpath)
    manifest = json.loads(read_text(mpath))
    state = PR.candidate_state(manifest)
    L = state['layout']
    print_parts = sorted(manifest['print_poses'])
    finished = [p for p in print_parts if p != PR.GAUGE]
    res = {}
    if 'print_overhang' in cats or 'print_bridge_direction' in cats:
        ov, bd = overhang_rows(out, manifest, state, print_parts)
        if 'print_overhang' in cats:
            res['print_overhang'] = ov
        if 'print_bridge_direction' in cats:
            res['print_bridge_direction'] = bd
    if 'thin_wall' in cats or 'critical_features' in cats:
        shapes = step_shapes(out, manifest, finished)
        if 'thin_wall' in cats:
            res['thin_wall'] = []
            for pid in finished:
                r = CK.thin_wall(L, pid, shapes[pid], loaded_boxes=state['loaded'].get(pid, []))
                r.update(step='step/%s.step' % pid, loaded_zone_source='print_rules.candidate_state')
                res['thin_wall'].append(r)
                print(pid, 'thin_wall', r['status'], r.get('p1'), r.get('share_loaded_below_1_6'), flush=True)
        if 'critical_features' in cats:
            rows = {pid: dict(shape=shapes[pid]) for pid in finished}
            res['critical_features'] = CK.check_critical_features(L, rows)
            if 'thin_wall' in res:      # r7 build_d2: thin-spot classification gates critical_features
                res['unclassified_thin_spots'] = CK.unclassified_thin_spots(L, res['thin_wall'])
                res['critical_features'].append(PR.thin_spot_gate(res['unclassified_thin_spots']))
            print('critical_features', {s: sum(r.get('status') == s for r in res['critical_features'])
                                        for s in ('pass', 'fail', 'info', 'stub')}, flush=True)
    if sha(mpath) != h0:
        raise ValueError('Manifest changed during print checks')
    summary = {c: {s: sum(1 for r in rows if r.get('status') == s) for s in ('pass', 'fail', 'info', 'stub')}
               for c, rows in res.items()}
    failing = {c: sorted({r.get('part') or r.get('id') for r in rows if r.get('status') == 'fail'}, key=str)
               for c, rows in res.items()}
    srcs = [Path(__file__), CV / 'print_rules.py', CV / 'cv_io.py', CV / 'model.py', PR.ROOT / 'checks.py',
            PR.ROOT / 'layout.py', PR.ROOT / 'd2_common.py', CV / 'structural-review' / 'j4_trial_geometry.py']
    report = dict(manifest_sha256=h0, variant=a.variant, categories=cats, complete=list(cats) == list(CATEGORIES),
                  verification_source_sha256=sha(Path(__file__)),
                  check_sources={rel_posix(p, PR.ROOT): sha(p) for p in srcs},
                  rule=dict(L.PRINT_OVERHANG, single_direction_per_region=True), summary=summary,
                  failing=failing, physical_print_release=False,
                  note='Computed geometry gates only (r7 rules plus the per-region single-direction bridge rule). '
                       'Slicer review, coupons and every physical gate remain unrun.',
                  results=res)
    dest = Path(a.out) if a.out else out / 'print-checks.json'
    write_text(dest, json.dumps(report, indent=1, default=jsonable))
    print(json.dumps(dict(summary=summary, failing=failing), indent=1))
    raise SystemExit(1 if any(v['fail'] for v in summary.values()) else 0)


if __name__ == '__main__':
    main()
