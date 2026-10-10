"""microSD service paths (VN-29, FP-12). Run through ../run_locked.py.

1. closed_panel_case (unchanged diagnostic of 9ced753): card +X versus the panel power-switch body only -> REJECTED.
2. Panel-off paths with the full obstacle set steps.py derives for motion `microsd_out` (the same set and sampling as
   the rigid batch row): the straight +X 45 path of 9ced753 (must be detected as blocked, by the lens collar), the
   selected dog-leg from steps.MOTIONS (+X 18 then +Y 40; must be clear) and window probes at +X 10/12/24/26.
   The +X 10 and +X 26 probes are regression fixtures: they hit today (carrier, tub); if a later obstacle-set or
   sampling change stops detecting them, their rows fail.
Tool and finger reach stay a HOLD (MEASUREMENTS-TO-CLOSE microSD row). Writes out/<variant>/microsd-service-dependency.json.
"""
from cv_io import read_text, write_text
from pathlib import Path
import argparse, json, hashlib
import cadquery as cq
import rigid_sweep as RS
import steps as ST

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--variant', default='compact-kowa_lm6hc')
ap.add_argument('--out', default='', help='report path instead of out/<variant>/microsd-service-dependency.json')
ap.add_argument('--step', type=float, default=2.0, help='sweep sample spacing, mm (verify_candidate default)')
a = ap.parse_args()
D = P / 'out' / a.variant
mf = D / 'manifest.json'
mh = RS.sha(mf)
m = json.loads(read_text(mf))
sh = {}
for name in ['microsd', 'power_button']:
    f = D / 'step' / (name + '.step')
    assert RS.sha(f) == m['files']['step/' + f.name]
    sh[name] = cq.importers.importStep(str(f)).val()
hits = []
for x in range(46):
    q = sh['microsd'].translate(cq.Vector(x, 0, 0)).intersect(sh['power_button'])
    v = q.Volume()
    if v > .02:
        hits.append({'translation_x_mm': x, 'overlap_mm3': v})

# ---- panel-off paths with the derived obstacle set (FP-12)
rows_ids = {r['id'] for r in m['rows']}
mot = {x['id']: x for x in ST.motion_table(rows_ids)}['microsd_out']
movers, obstacles = mot['movers'], mot['obstacles']
scene = RS.Scene(D, m, movers + obstacles)
sel = [list(k) for k in ST.MOTIONS['microsd_out']['path']]
dy = ST.MICROSD_DOGLEG_OUT[1] - ST.MICROSD_DOGLEG_X[1]
paths = [('panel_off_straight_x45', [[0, 0, 0], [45, 0, 0]], 'hit', 'rejected 9ced753 path; must stay detected'),
         ('dogleg_selected', sel, 'clear', 'selected procedure (steps.MOTIONS microsd_out)'),
         ('dogleg_window_x10', [[0, 0, 0], [10, 0, 0], [10, dy, 0]], 'hit', 'regression fixture: carrier'),
         ('dogleg_window_x12', [[0, 0, 0], [12, 0, 0], [12, dy, 0]], None, 'window edge, reported'),
         ('dogleg_window_x24', [[0, 0, 0], [24, 0, 0], [24, dy, 0]], None, 'window edge, reported'),
         ('dogleg_window_x26', [[0, 0, 0], [26, 0, 0], [26, dy, 0]], 'hit', 'regression fixture: tub')]
checks = []
for pid, knots, expect, why in paths:
    print('sweep', pid, knots, flush=True)
    worst, h, n = scene.sweep(movers, obstacles, knots, a.step)
    status = 'info' if expect is None else ('pass' if (bool(h) == (expect == 'hit')) else 'fail')
    parts = sorted({x['fixed'] for x in h})
    checks.append(dict(id=pid, status=status, expected=expect, purpose=why, knots=knots, samples=n,
                       step_mm=a.step, worst_overlap_mm3=worst, total_hits=len(h), hit_parts=parts,
                       first_hit=h[0] if h else None, first_hits=h[:8]))
    print(json.dumps({k: checks[-1][k] for k in ('id', 'status', 'worst_overlap_mm3', 'total_hits', 'hit_parts')}),
          flush=True)
assert RS.sha(mf) == mh
summary = {k: sum(c['status'] == k for c in checks) for k in ('pass', 'fail', 'info')}
r = {'manifest_sha256': mh, 'verification_source_sha256': RS.sha(Path(__file__)),
     'helper_source_sha256': {'rigid_sweep.py': RS.sha(P / 'rigid_sweep.py'), 'steps.py': RS.sha(P / 'steps.py')},
     'closed_panel_case': 'REJECTED' if hits else 'No modeled switch contact in this limited pair test',
     'sample_step_mm': 1, 'hits': hits,
     'panel_off': dict(motion='microsd_out', op=mot['op'], movers=movers, obstacles=obstacles,
                       obstacle_source='steps.motion_table (present before/after svc_microsd_out minus movers)',
                       pi5_method='verify_candidate.py component set (official_pi5_assembly.build_parts); pi5.step '
                                  'hash-checked; component overlaps summed (upper bound)',
                       step_bindings=scene.bindings, summary=summary, checks=checks),
     'selected_procedure': 'Bench-fit the OS microSD before carrier insertion and carry it with the module. In-body '
                           'service only with the panel off, by the dog-leg: %s, +X 18 out of the socket, then +Y 40 out '
                           'of the open panel side. The straight +X path meets the lens collar and the closed-panel '
                           'path meets the power switch. Tool and finger reach remain a HOLD.' % ST.MICROSD_TOOL,
     'tool': ST.MICROSD_TOOL,
     'scope': 'Rigid card proxy translations against saved STEPs with the derived obstacle set; no socket-latch, card '
              'grasp, tool-body or finger-reach qualification. The front slit (model.py) passes no card path: its '
              'closure is user decision VN-29.',
     'physical_qualified': False}
write_text(Path(a.out) if a.out else D / 'microsd-service-dependency.json', json.dumps(r, indent=2))
print(json.dumps({'closed_case': r['closed_panel_case'], 'hit_samples': len(hits),
                  'max_overlap_mm3': max((q['overlap_mm3'] for q in hits), default=0), 'panel_off': summary,
                  'manifest_sha256': mh}), flush=True)
raise SystemExit(1 if summary['fail'] else 0)
