# SPDX-License-Identifier: MIT
"""FP-10 (VN-26, VN-28; check parts of VN-47 / VN-62): manifest-bound harness and power checks for the selected
vertical candidate. Run through ../run_locked.py. Rules live in harness_rules.py (CAD-free); this runner binds the
mechanical manifest and every bound STEP it opens, records the route-source and snapshot hashes, supplies exact
solid hits (hand envelopes, dia 3 tails) and exact distances (header housings), confirms the tie slots in the carrier
STEP and writes out/<variant>/harness-checks.json. Exit 1 on any failing row; failures are kept, never waived.
"""
from cv_io import read_text, write_text
from pathlib import Path
import argparse, hashlib, json, math, sys

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--variant', default='compact-kowa_lm6hc')
ap.add_argument('--out', default='', help='report path (default out/<variant>/harness-checks.json)')
a = ap.parse_args()
if a.variant != 'compact-kowa_lm6hc':
    raise SystemExit('Only the selected compact-kowa_lm6hc routes exist; other variants need their own route solve (FP-13)')
OUT = P / 'out' / a.variant
MF = OUT / 'manifest.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


manifest_sha = sha(MF)
meta = json.loads(read_text(MF))
rows = {r['id']: r for r in meta['rows']}
# Manifest source drift is recorded, not raised: FP-02's I/O-only edits changed some bound sources (rebind at the next
# re-export, FP-16). Every STEP read here is hash-checked against the manifest; a drifted source that is also a
# harness dependency fails the drift row.
drift = sorted(rel for rel, h in meta['sources'].items() if not (P.parent / rel).is_file() or sha(P.parent / rel) != h)
sys.path.insert(0, str(P))
sys.path.insert(0, str(P.parent))
import routes as R
import steps as ST
import harness_rules as HR
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

DEPENDENCIES = ['harness_rules.py', 'routes.py', 'signal_routes.py', 'power_routes.py', 'hdmi_routes.py', 'steps.py',
                '../layout.py', 'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json']
out = R.build()
H = HR.collect(out, rows, R.L, ST)
shapes = {}


def shape(i):
    if i not in shapes:
        f = OUT / 'step' / (i + '.step')
        if sha(f) != meta['files']['step/%s.step' % i]:
            raise ValueError('STEP does not match manifest: ' + i)
        shapes[i] = cq.importers.importStep(str(f)).val()
    return shapes[i]


def box_solid(b):
    return cq.Solid.makeBox(b[1] - b[0], b[3] - b[2], b[5] - b[4], cq.Vector(b[0], b[2], b[4]))


def _pieces(spec, step=5.0):
    if spec['type'] == 'box':
        return [(spec['box'], box_solid(spec['box']))]
    p0, p1, d = spec['p0'], spec['p1'], spec['d']
    n = max(1, math.ceil(math.dist(p0, p1) / step))
    out_ = []
    for k in range(n):
        q0 = [p0[i] + (p1[i] - p0[i]) * k / n for i in range(3)]
        q1 = [p0[i] + (p1[i] - p0[i]) * (k + 1) / n for i in range(3)]
        h = math.dist(q0, q1)
        if h < 1e-9:
            continue
        cyl = cq.Solid.makeCylinder(d / 2, h, cq.Vector(*q0), cq.Vector(*[(q1[i] - q0[i]) / h for i in range(3)]))
        out_.append((HR.tail_box(q0, q1, d), cyl))
    return out_


def exact_hits(spec, targets):
    """Exact Boolean volume of the hand box / tail cylinder pieces with each present part; keepouts as boxes."""
    hits = []
    pieces = _pieces(spec)
    for t in targets:
        vol = 0.0
        for pb, solid in pieces:
            if not HR.boxes_overlap(pb, t['box']):
                continue
            if t['kind'] == 'keepout':
                vol += HR.box_vol(pb, t['box'])
                continue
            s = shape(t['id'].split(' ')[0])
            if any(t['disp']):
                s = s.translate(cq.Vector(*t['disp']))
            vol += solid.intersect(s).Volume()
        if vol > HR.SWEEP_TOL:
            hits.append(dict(obstacle=t['id'], volume_mm3=round(vol, 2), method='exact'))
    return hits


def exact_dist(i, b):
    return shape(i).distance(box_solid(b))


res = HR.run_all(H, R.rounded_path, ST, hits=exact_hits, printed_dist=exact_dist, cots_dist=exact_dist)

# Tie slots in the carrier STEP: centre open (through slot), both flanks in rail material.
carrier = shape('carrier')
cls = [BRepClass3d_SolidClassifier(s.wrapped) for s in carrier.Solids()]


def inside(p):
    for c in cls:
        c.Perform(gp_Pnt(*p), 1e-7)
        if c.State() == TopAbs_IN:
            return True
    return False


slot_rows, ok = [], True
yc = sum(HR.TIE_SLOT_Y) / 2
for x, z in HR.TIE_SLOTS_XZ:
    rec = dict(slot_xz=[x, z], centre_open=not inside((x, yc, z)), flank_minus_x_material=inside((x - 2.5, yc, z)),
               flank_plus_x_material=inside((x + 2.5, yc, z)))
    ok &= rec['centre_open'] and rec['flank_minus_x_material'] and rec['flank_plus_x_material']
    slot_rows.append(rec)
res.append(dict(category='lead_access', id='tie_slots_in_step', slots=slot_rows, status='pass' if ok else 'fail',
                problems=[] if ok else ['tie slot data differ from the carrier STEP'],
                note='harness_rules.TIE_SLOTS_XZ (model.py make_carrier) confirmed by point classification'))

# Manifest-bound signal-route verifier (VN-28): sources, snapshot and pose bindings.
snap_rel = 'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'
snap = json.loads(read_text(P / snap_rel))
pw = out['power_geometry']
pr = []
if pw['mechanical_snapshot']['sha256'] != sha(P / snap_rel):
    pr.append('power_routes mechanical_snapshot sha differs from the snapshot file')
if meta['sources'].get('candidate-vertical/' + snap_rel) != sha(P / snap_rel):
    pr.append('manifest does not bind the power snapshot')
for k in ('junction_center', 'junction_yaw_deg', 'junction_pitch_deg'):
    if snap[k] != pw[k]:
        pr.append('junction %s differs from the snapshot' % k)
if len(snap['rigid_service_poses']) != len(pw['rigid_service_poses']) or any(
        math.dist(p['center'], q['center']) > 1e-9 or
        max(abs(p['matrix'][r][c] - q['matrix'][r][c]) for r in range(3) for c in range(3)) > 1e-9   # float noise 1e-16
        for p, q in zip(snap['rigid_service_poses'], pw['rigid_service_poses'])):
    pr.append('rigid service poses differ from the snapshot')
scope = out['signal_geometry'].get('parameter_scope_gate', '')
if not scope.startswith('Selected parameter scope matched'):
    pr.append('route parameter scope is not the selected one: ' + scope[:80])
dep = {d: sha(P / d) for d in DEPENDENCIES}
dep_drift = [d for d in drift if any((P / x).resolve() == (P.parent / d).resolve() for x in DEPENDENCIES)]
res.append(dict(category='signal_routes', id='manifest_source_drift', drifted_sources=drift,
                drifted_harness_dependencies=dep_drift, status='fail' if dep_drift else 'info',
                problems=['a harness dependency drifted from the manifest: %s' % dep_drift] if dep_drift else [],
                note='Bound sources changed since export (FP-02 I/O-only edits, rebind at FP-16; the reconciler '
                     'source_binding gate owns them). STEP inputs are hash-checked individually.'))
res.append(dict(category='signal_routes', id='binding', manifest_sha256=manifest_sha, route_revision=out['revision'],
                signal_revision=out['signal_geometry']['revision'], dependency_sha256=dep, problems=pr,
                status='fail' if pr else 'pass'))
orphan, idx = P / 'signal_routes_review.json', P / 'history/orphan-signal-routes-2026-10-11/INDEX.json'
pr = []
if orphan.exists():
    pr.append('stale signal_routes_review.json still in the live folder')
if not idx.exists():
    pr.append('archive index missing')
else:
    for m_ in json.loads(read_text(idx))['moved']:
        if sha(P / m_['to']) != m_['sha256']:
            pr.append('archived copy changed: ' + m_['to'])
res.append(dict(category='signal_routes', id='orphan_report_archived', problems=pr, status='fail' if pr else 'pass'))

if sha(MF) != manifest_sha:
    raise ValueError('Manifest changed during verification')
summary = {k: sum(r['status'] == k for r in res) for k in ('pass', 'fail', 'info')}
cats = sorted({r['category'] for r in res})
failing = {c: sorted(r['id'] for r in res if r['category'] == c and r['status'] == 'fail') for c in cats}
report = dict(manifest_sha256=manifest_sha, verification_source_sha256=sha(Path(__file__)),
              verification_dependency_sha256=dep, variant=a.variant, r7_source=HR.R7_SOURCE,
              summary=summary, per_category={c: {k: sum(r['status'] == k for r in res if r['category'] == c)
                                                 for k in ('pass', 'fail', 'info')} for c in cats},
              failing={c: v for c, v in failing.items() if v}, checks=res, status='fail' if summary['fail'] else 'pass',
              geometry_computed_pass=summary['fail'] == 0, physical_qualified=False,
              decisions_left_to_user=['VN-47 carrier ties vs RTV-only (both rows computed; retention of record: %s)'
                                      % HR.PIGTAIL_RETENTION, 'VN-62 G-W5 fail branch (decision_data in pigtail_drop)',
                                      'VN-63 J2 side genders (both assignments computed in j2_btn)'])
write_text(Path(a.out) if a.out else OUT / 'harness-checks.json', json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(summary=summary, failing=report['failing'])), flush=True)
raise SystemExit(1 if summary['fail'] else 0)
