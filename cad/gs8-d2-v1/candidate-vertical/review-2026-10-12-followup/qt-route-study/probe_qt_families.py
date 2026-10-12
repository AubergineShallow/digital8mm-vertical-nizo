# SPDX-License-Identifier: MIT
"""Two rejected QT knot families; read-only screening, never a production route.

Run from repository root through cad/gs8-d2-v1/run_locked.py.
Printed/COTS exact clearance, transition motion and physical qualification are outside this probe.
"""
import copy
import json
import sys
from pathlib import Path
cv = Path.cwd() / 'cad/gs8-d2-v1/candidate-vertical'
sys.path[:0] = [str(cv), str(cv / 'tests'), str(cv.parent)]
from test_fxh_harness import data
import harness_rules as HR
import routes as R
import steps as ST
H = data()
c = H['cables']['qt']
F = c['points'][0]
branch = max(b['length'] for b in c['branches'])

def evaluate(cfg, low):
    y, top, cross = cfg['return_y'], cfg['top'], cfg['cross']
    knots = [F, [F[0], -23.4, top], [-72.5, -23.4, top],
             [-72.5, y, low], [-93.2, y, low], [-93.2, -23.4, cross],
             [-93.2, 14.8, cross], [-85.0, 14.8, 77.0], [-72.0, 14.8, 77.0]]
    return R.rounded_path(knots, 6.4, 3, 4, .5)

def screen(curve):
    h = copy.deepcopy(H)
    q = h['cables']['qt']
    q['curve'] = curve
    q['points'] = curve['sampled_centerline']
    def ko(spec, targets):
        return HR.box_hits(spec, [t for t in targets if t['kind'] == 'keepout'])
    ic = HR.installed_clearance(h, 'qt', set(ST.final_state()), ko)
    return dict(keepout_hits=ic['hits'], cable_overlaps=ic['cable_overlaps'])

out = dict(scope='Two read-only knot-family screens, no routing or stock changes; keepouts plus modeled cable separation, not exact printed/COTS clearance.', root=F, longest_branch_mm=branch, candidates=[])
for cfg in [dict(name='fixed_top_75_lateral_lower_return', return_y=-19.7, top=75.0, cross=68.0, low_bounds=[27.5,55.2]),
            dict(name='raise_cross_80', return_y=-23.4, top=90.5, cross=80.0, low_bounds=[44.0,67.2])]:
    rec = dict(cfg, bounds=[], stock=[])
    for low in cfg['low_bounds']:
        cur = evaluate(cfg,low)
        q = dict(low=low, total_mm=None if cur['errors'] else cur['rounded_length_mm']+branch, errors=cur['errors'], knots=cur['knots'])
        if not cur['errors']: q.update(screen(cur))
        rec['bounds'].append(q)
    if all(not q['errors'] for q in rec['bounds']):
        for stock in (240,250,260):
            lo,hi=cfg['low_bounds']
            for _ in range(40):
                mid=(lo+hi)/2
                cur=evaluate(cfg,mid)
                if cur['errors']: break
                if cur['rounded_length_mm']+branch > stock: lo=mid
                else: hi=mid
            cur=evaluate(cfg,(lo+hi)/2)
            q=dict(stock_mm=stock,low=(lo+hi)/2,total_mm=None if cur['errors'] else cur['rounded_length_mm']+branch,errors=cur['errors'])
            if not cur['errors']: q.update(screen(cur))
            rec['stock'].append(q)
    out['candidates'].append(rec)
print(json.dumps(out,indent=2))
