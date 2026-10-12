# SPDX-License-Identifier: MIT
"""J7-R float, roll catch, lens support / clamp, collar gauge and insert checks on the candidate (review 2026-10-10,
VN-24; fix FP-08). Rows for the main audit (verify_candidate.py, behind want('j7')).

The r7 implementations in ../checks.py (read-only, byte-identical to upstream d38468e) are called unchanged wherever
they are geometry-agnostic, through one adapter:
- layout: the candidate's own values. model.py's import-time layout edits, JG.trial_layout(lip 2.4, head 2.4),
  L.LENS = the variant lens and model.collar_setup() (collar body_r 25, LL foot (18, 30), lug y_out -30.8 / screw_y
  -26.8 / bit_relief_y -22.8 since C2 (r7 spacing), s_c3 and s_c4 moved) are applied exactly as model._build applies them, and
  restored. Collars are rebuilt with model.make_collar (r7 build_part + the C2 LR foot support), as model._build.
  The r7 functions that read module globals (collar_spec, tab_catch_boxes, ...) therefore see the candidate values.
  A context row proves it: the collar rebuilt in this context equals the manifest-bound STEP collar, and
  cots.gs_camera_parts at s_nom equals the STEP camera.
- rows: every manifest row from its manifest-bound STEP (verify_candidate.py loads and binds them). A multi-solid
  row outside the hanging unit is split into id#k solids (an OCCT boolean of a compound of overlapping solids is
  undefined); per-obstacle minima are reported per id#k and folded per id in j7_float/obstacle_minima.
- full BFAR range: r7 j7_s_values (s_range every 0.25 plus s_nom) with r7 J7_FLOAT_RULES (body lateral 0.5 / axial
  0.4, BFAR 0.6 / 0.4, adapter 0.6) and J7_LENS_GAP 0.5. Rows carry per-obstacle gaps and the minima.
Candidate differences, each stated in the rows, none looser than r7:
- centring stack: r7 adds HOOD_TO_TUB_LATERAL to obstacles on the hood. The candidate has no hood; its tab catch is
  integral to the tub (no location term), and the removable side panel (camera cover catch, 4 PT screws) takes the
  same 0.25 as a stand-in (LOCATION_EXTRA; the panel location stack is not declared anywhere: stricter, not measured).
- roll catch: the catch host is the tub. r7 check_roll_catch is called with the tub under the r7 key 'hood' and a
  layout view (LayoutView) whose HOOD tab_catch top is the candidate's 98.0 (model.make_tub grows the boxes to Z98),
  whose ZT1 (the tine root of the r7 cantilever estimate) is the tub roof underside measured on the STEP, whose
  INSERTIONS / REMOVALS / STEPS / present_at come from steps.py (the lens ops; hold = the tab catch when the op text
  names it), and whose COTS boxes are kept only where the r7 box still encloses the candidate STEP solid (moved
  parts are measured by their STEP solids only). 'hood' is renamed back to 'tub' in the output. The level window
  therefore measures the camera metal to the whole tub (r7: hood only). The lens-hold text lint runs on
  ASSEMBLY-VERTICAL.md, the candidate guide builders and the steps.py op texts.
- collar gauge: r7's 'hood >= 0.5' row becomes '>= 0.5 to every other part present at gauge_in' (steps.py), and the
  insertion sweep covers those parts too.
- washer seat: the two r7 test_mechanical_refinements washer tests are also computed rows (lens_clamp/washer_*),
  with the r7 thresholds; they failed on the 9ced753 collar (VN-55) and pass since C2 (FP-11d).
Nothing here is a measurement; every physical gate (G-COL-1, G-CAM-1/2, G-LENS, M1) stays open.
This module is CAD-free at import (evidence_rules imports INFO_ROWS); CadQuery loads inside the functions.
"""
from contextlib import contextmanager
import copy
import hashlib
import itertools
import math
import re
import sys
from pathlib import Path

CV = Path(__file__).resolve().parent
CAD = CV.parent
for _p in (str(CAD), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CATEGORIES = ('j7_float', 'roll_catch', 'lens_support', 'lens_clamp', 'inserts')
CATCH_TOP_Z = 98.0                      # model.make_tub: b['z']=(b['z'][0],98.0) (source-pinned in the tests)
CATCH_SOURCE = "b=dict(b);b['z']=(b['z'][0],98.0)"
LOCATION_EXTRA = ('panel',)             # removable side panel located on the tub by 4 PT screws
LOCATION_BASIS = ('r7 HOOD_TO_TUB_LATERAL reused for the removable side panel (camera cover catch, 4 PT 3x12 in '
                  '3.4 holes); no candidate panel location stack is declared: stand-in, stricter than r7, unmeasured')
ASSEMBLY = 'ASSEMBLY-VERTICAL.md'
GUIDE_SOURCES = ('guide/build_guide_vertical.py', 'guide/build_guide_concealed_vents.py')
GAUGE_OTHER_GAP = 0.5                   # r7 check_collar_gauge: gauge to the hood (here: every other present part)
SPLIT_NEVER = ('gs_camera', 'c_cs_adapter', 'lens', 'lens_collar', 'tub', 'panel')
NO_LENS_HOLD_PHRASE = 'tab catch'       # an op that turns the lens names what takes the thread torque

# Main-audit info rows (evidence_rules.expected_main_info; the reconciler wants the exact set). Each is an r7 WARN that
# r7 also reports as info: unmeasured lens bands (G-LENS), the data-only lens's entry design, the bolted-only anchor
# triangle (M1 / G-COL-1), the Kowa elastic rock at 5 g, and the roll-catch timing record.
INFO_ROWS = frozenset([
    ('lens_support', 'kowa_lm6hc/status'), ('lens_support', 'fujinon_hf6xa/status'),
    ('lens_support', 'computar_h6z0812/status'), ('lens_support', 'computar_h6z0812/rear_entry_plan'),
    ('lens_support', 'fujinon_hf6xa/thumb_keepouts'),
    ('lens_clamp', 'anchor_polygon_bolted'), ('lens_clamp', 'clamp/kowa_lm6hc'),
    ('roll_catch', 'timing'),
])


def source_sha256():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def lens_of(variant, meta=None):
    """Variant lens: the manifest's `lens` field, else the part after the first '-' of the variant name."""
    return (meta or {}).get('lens') or variant.split('-', 1)[1]


@contextmanager
def candidate_layout(lens):
    """The candidate's layout state as model._build sets it for the collar, tub and screws; restored on exit."""
    import model as M
    L = M.L
    saved = {k: getattr(L, k) for k in ('LENS', 'COLLAR', 'SCREWS')}
    with M.JG.trial_layout(L, lip=2.4, head=2.4):
        try:
            L.LENS = lens
            M.collar_setup()
            yield L
        finally:
            for k, v in saved.items():
                setattr(L, k, v)


class LayoutView:
    """Attribute view of the layout module with overrides (the module itself is never edited by the view)."""
    def __init__(self, base, **over):
        self.__dict__['_base'] = base
        self.__dict__.update(over)

    def __getattr__(self, k):
        return getattr(self.__dict__['_base'], k)


def r7_rows(shapes, manifest_rows):
    """{id: dict(shape, kind, parent)} in r7 row form; multi-solid rows outside SPLIT_NEVER become id#k solids."""
    out = {}
    for k in sorted(manifest_rows):
        s = shapes.get(k)
        if s is None:
            continue
        kind = manifest_rows[k].get('kind')
        sols = list(s.Solids())
        if len(sols) > 1 and k not in SPLIT_NEVER:
            for i, so in enumerate(sols):
                out['%s#%d' % (k, i)] = dict(shape=so, kind=kind, parent=k)
        else:
            out[k] = dict(shape=s, kind=kind, parent=k)
    return out


def parent(oid):
    return oid.split('#', 1)[0]


def _status_ok(st):
    return {'pass': True, 'fail': False, 'stub': False, 'info': None}.get(st, False)


def _clean(v):
    """JSON-safe copy (numpy scalars -> float/int, tuples -> lists, non-string keys -> str)."""
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set, frozenset)):
        return [_clean(x) for x in (sorted(v) if isinstance(v, (set, frozenset)) else v)]
    if hasattr(v, 'item') and not isinstance(v, (str, bytes)):
        try:
            return v.item()
        except Exception:  # noqa: BLE001
            return str(v)
    return v


def emit(category, ident, r7row, **extra):
    """verify_candidate add() kwargs from an r7 row: status -> ok (stub = fail), r7's own fields kept."""
    f = {k: v for k, v in r7row.items() if k not in ('status', 'id', 'category')}
    if r7row.get('status') == 'stub':
        f['r7_status'] = 'stub'
    f.update(extra)
    return dict(category=category, id=ident, ok=_status_ok(r7row.get('status')), port='FP-08', **_clean(f))


def _as_shape(x):
    return x.val() if hasattr(x, 'val') else x


def _symdiff(a, b):
    return float(a.cut(b).Volume() + b.cut(a).Volume())


def _row(kind, status, error=None, **kw):
    r = dict(kind=kind, status=status, **kw)
    if error and status != 'pass':
        r['error'] = error
    return r


# ------------------------------------------------------------------------------------------------ context rows
def context_rows(L, rr, lens, CK):
    """The r7 functions see the exported geometry: rebuilt collar == STEP collar; gs_camera_parts(s_nom) == STEP."""
    import cots
    import model as M
    out = []
    # C2 (FP-11d): the candidate collar is model.make_collar (r7 build_part + the LR foot support, VN-58); the
    # rebuild must use the builder model._build uses, or this row compares a different part with the STEP.
    col = _as_shape(M.make_collar(lens))
    d = _symdiff(col, rr['lens_collar']['shape'])
    out.append(('lens_support', lens + '/collar_context_match', _row(
        'lens_support', 'pass' if d <= 0.01 else 'fail', 'candidate-context collar differs from the STEP collar',
        item='collar_context_match', lens=lens, symmetric_difference_mm3=CK._r(d, 4),
        rule='collar rebuilt with the candidate layout (model.collar_setup) == manifest-bound STEP (<= 0.01 mm3)')))
    p = cots.gs_camera_parts(L, None)
    cam = _as_shape(cots.gs_camera(L, None))
    d2 = _symdiff(cam, rr['gs_camera']['shape'])
    out.append(('j7_float', 'camera_model_match', _row(
        'j7_float', 'pass' if d2 <= 0.01 else 'fail', 'cots.gs_camera_parts at s_nom differs from the STEP camera',
        item='camera_model_match', s_nom=L.CAM['s_nom'], symmetric_difference_mm3=CK._r(d2, 4),
        hf_x=CK._r(p['hf_x'], 4), rule='r7 gs_camera_parts(s_nom) body + bfar == manifest-bound STEP gs_camera '
                                        '(<= 0.01 mm3): the float rows move the exported camera',
        j7_collar_checks_sha256=source_sha256(),
        steps_sha256=hashlib.sha256((CV / 'steps.py').read_bytes()).hexdigest(),
        r7_checks_sha256=hashlib.sha256((CAD / 'checks.py').read_bytes()).hexdigest())))
    return out, col


# ------------------------------------------------------------------------------------------------ J7-R float
def centring_rows(L, out, CK):
    """r7 checks._centring_rows with the candidate location term (LOCATION_EXTRA instead of the hood)."""
    g = L.COLLAR.get('gauge') or {}
    extra_mm = getattr(L, 'HOOD_TO_TUB_LATERAL', 0.25)
    worst = {}
    for r in out:
        if r.get('mover') not in ('body', 'bfar', 'adapter'):
            continue
        for oid, gp in (r.get('per_obstacle') or {}).items():
            if gp.get('lateral') is None:
                continue
            k = (r['mover'], oid)
            if k not in worst or gp['lateral'] < worst[k][0]:
                worst[k] = (gp['lateral'], r.get('s'))
    stack = g.get('centring_worst_mm')
    bare = (g.get('stack_without_gauge') or {}).get('worst_mm')
    rows = []
    for (mv, oid), (gap, s) in sorted(worst.items()):
        extra = extra_mm if parent(oid) in LOCATION_EXTRA else 0.0
        left = None if stack is None else gap - stack - extra
        ok = left is not None and left >= CK.J7_RUNNING - CK.J7_TOL
        rows.append(_row(
            'j7_float', 'pass' if ok else 'fail',
            'centring stack %s + location %s leaves %s mm lateral to %s (need >= %.2f)'
            % (stack, extra, None if left is None else CK._r(left), oid, CK.J7_RUNNING),
            mover='centring', item='lateral_stack', of=mv, obstacle=oid, s=s, lateral_gap=CK._r(gap), stack_mm=stack,
            location_extra_mm=extra or None, location_basis=LOCATION_BASIS if extra else None,
            remaining_mm=None if left is None else CK._r(left),
            remaining_without_gauge_mm=None if bare is None else CK._r(gap - bare - extra),
            rule='remaining >= %.2f' % CK.J7_RUNNING))
    if not rows:
        rows.append(_row('j7_float', 'fail', 'no lateral gap measured (the float is not measured): the centring '
                         'stack cannot be checked', mover='centring', item='lateral_stack'))
    return rows


def obstacle_minima(out):
    """Per obstacle (id#k folded to id): least overall / lateral / axial gap over every body / bfar / adapter row."""
    per, bad, offending, ss = {}, [], set(), set()
    for r in out:
        if r.get('mover') not in ('body', 'bfar', 'adapter'):
            continue
        ss.add(r.get('s'))
        if r.get('status') != 'pass':
            bad.append('%s@%s' % (r['mover'], r.get('s')))
        offending.update(parent(o) for o in r.get('offending_obstacles') or ())
        for oid, g in (r.get('per_obstacle') or {}).items():
            p = per.setdefault(parent(oid), {})
            for k in ('overall', 'lateral', 'axial'):
                v = g.get(k)
                if v is not None and (k not in p or v < p[k]['gap']):
                    p[k] = dict(gap=v, mover=r['mover'], s=r.get('s'), solid=oid)
            ov = g.get('overlap_mm3')
            if ov is not None and ov == ov and ov > p.get('max_overlap_mm3', 0.0):
                p['max_overlap_mm3'] = ov
    return _row('j7_float', 'fail' if bad or not per else 'pass',
                'float rows fail (%s); offending %s' % (', '.join(bad[:8]), sorted(offending)) if per else
                'no obstacle measured', item='obstacle_minima', per_obstacle=per, offending_obstacles=sorted(offending),
                failing_rows=len(bad), s_values=sorted(x for x in ss if x is not None),
                rule='every body / bfar / adapter row passes r7 J7_FLOAT_RULES over the full BFAR range')


def j7_ident(r):
    m, it = r.get('mover'), r.get('item')
    if it == 'obstacle_minima':
        return 'obstacle_minima'
    if m in ('body', 'bfar'):
        return '%s@s%.2f' % (m, r['s'])
    if m == 'adapter':
        return 'adapter'
    if m == 'centring':
        return 'centring:%s/%s' % (r['of'], r['obstacle']) if r.get('of') else 'centring'
    if m == 'lens':
        return 'lens/' + (it or 'overlap')
    if m == 'lens_vs_camera':
        return 'lens_vs_camera@s%.2f' % r['s']
    raise ValueError('unknown j7 row %r' % ({k: r.get(k) for k in ('mover', 'item', 's')},))


def j7_float_rows(L, rr, CK, s_values=None, parts_of=None):
    """r7 check_j7_float over the full BFAR range, centring rows with the candidate location term, minima row."""
    out = CK.check_j7_float(L, rr, s_values=s_values, parts_of=parts_of)
    out = [r for r in out if r.get('mover') != 'centring']
    out += centring_rows(L, out, CK)
    out.append(obstacle_minima(out))
    return [('j7_float', j7_ident(r), r) for r in out]


# ------------------------------------------------------------------------------------------------ roll catch
def candidate_catch_boxes(L):
    """Actual catch sections, including the local recess below the bonded joint."""
    import model
    view = LayoutView(L, HOOD=dict(copy.deepcopy(L.HOOD), tab_catch=dict(L.HOOD['tab_catch'], top=CATCH_TOP_Z)))
    boxes = []
    recess = getattr(model, 'TAB_CATCH_FACE_RECESS_MM', 0.0)
    for b in L.tab_catch_boxes(view):
        if b['side'] == 1 and recess:
            lower = dict(b, y=(b['y'][0] + recess, b['y'][1]), z=(b['z'][0], model.TAB_CATCH_SPLIT_Z))
            boxes += [lower, dict(b, z=(model.TAB_CATCH_SPLIT_Z, b['z'][1]))]
        else:
            boxes.append(b)
    # r7's section-strength estimate uses the declared web/flange depths. Use the
    # smallest (recessed) section for both tines, retaining its original limits.
    hood = copy.deepcopy(view.HOOD)
    hood['tab_catch']['t'] -= recess
    hood['tab_catch']['flange']['dy'] -= recess
    return boxes, hood


def catch_material(L, tub, boxes):
    """Sample points (0.1 / 0.5 / 0.9 of each box span) that are NOT tub material: [] when the catch is solid."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_IN
    from OCP.gp import gp_Pnt
    cl = [BRepClass3d_SolidClassifier(so.wrapped) for so in tub.Solids()]
    miss = []
    for b in boxes:
        for fx in (0.1, 0.5, 0.9):
            for fy in (0.1, 0.5, 0.9):
                for fz in (0.1, 0.5, 0.9):
                    p = tuple(b[a][0] + f * (b[a][1] - b[a][0]) for a, f in zip('xyz', (fx, fy, fz)))
                    inside = False
                    for c in cl:
                        c.Perform(gp_Pnt(*p), 1e-6)
                        inside = inside or c.State() == TopAbs_IN
                    if not inside:
                        miss.append([round(v, 3) for v in p])
    return miss


def tine_root(L, tub, CK):
    """Tub roof underside beside the catch (ray +Z at x = catch x0 - 3, y = axis, from the tine bottom) = the r7
    cantilever root (r7: ZT1, the hood band underside). Also the first material above the slot centre (the
    panel-screw boss, VN-53), reported only: the r7 estimate keeps the longer roof arm."""
    tc = L.HOOD['tab_catch']
    ly = L.LENS_AXIS[0]
    H = CK._Hits(tub)
    z0 = tc['z0']
    w_roof = CK._first(H((tc['x'][0] - 3.0, ly, z0), (0.0, 0.0, 1.0), 0.0, 40.0), -1e-6)
    w_slot = CK._first(H((sum(tc['x']) / 2, ly, z0), (0.0, 0.0, 1.0), 0.0, 40.0), -1e-6)
    return (None if w_roof is None else z0 + w_roof), (None if w_slot is None else z0 + w_slot)


def lens_records(L, ST):
    """r7-form STEPS (one per candidate build step label, op texts joined), the last op of each, and the lens
    INSERTIONS / REMOVALS from steps.py (hold = the tab catch when the op text names it)."""
    labels, ops_of = [], {}
    for o in ST.STEPS:
        if o['step'] not in ops_of:
            labels.append(o['step'])
            ops_of[o['step']] = []
        ops_of[o['step']].append(o)
    num = {lab: i + 1 for i, lab in enumerate(labels)}
    steps = [dict(step=num[lab], name='candidate step %s' % lab, label=lab,
                  tool='; '.join(o['tools'] for o in ops_of[lab] if o['tools']),
                  action=' '.join(o['doc'] for o in ops_of[lab])) for lab in labels]
    last = {num[lab]: ops_of[lab][-1]['id'] for lab in labels}

    def hold(o):
        return 'hood_tab_catch' if NO_LENS_HOLD_PHRASE in o['doc'].lower() else None
    ins = [dict(id=o['id'], step=num[o['step']], moving=['lens'], hold=hold(o)) for o in ST.STEPS if 'lens' in o['adds']]
    final = set(ST.final_state())
    rem = []
    for r in ST.SERVICE:
        for rr, o, before, after in ST.service_sequence(r):
            if rr == r and 'lens' in o['removes']:
                rem.append(dict(id=o['id'], route=r, moving=['lens'], off=sorted(final - set(before)), hold=hold(o)))
    return steps, last, ins, rem


def _alias(ids):
    return [('hood' if i == 'tub' else i) for i in ids]


def _unalias(v):
    """'hood' (the r7 catch-host key) back to 'tub' in values, keys and texts."""
    if isinstance(v, dict):
        return {('tub' if k == 'hood' else k): _unalias(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_unalias(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_unalias(x) for x in v)
    if v == 'hood':
        return 'tub'
    if isinstance(v, str) and 'hood' in v:
        return re.sub(r'\bhood\b', 'tub', v)
    return v


def cots_box_view(L, shapes, CK):
    """L.COTS with a box only where the r7 box still encloses the candidate STEP solid (moved COTS: no box)."""
    out, kept, dropped = {}, [], []
    for k, c in L.COTS.items():
        b = c.get('box') if isinstance(c, dict) else None
        if not b or k not in shapes:
            out[k] = c
            continue
        bt, sb = CK.box_bb(b), CK.bb_tuple(shapes[k])
        if all(sb[2 * i] >= bt[2 * i] - 0.05 and sb[2 * i + 1] <= bt[2 * i + 1] + 0.05 for i in range(3)):
            kept.append(k)
            out[k] = c
        else:
            dropped.append(k)
            out[k] = {kk: vv for kk, vv in c.items() if kk != 'box'}
    return out, kept, dropped


def roll_catch_rows(L, rr, shapes, CK, ST, s_values=None, parts_of=None):
    """r7 check_roll_catch on the candidate through the adapter described in the module docstring."""
    tub = rr['tub']['shape']
    boxes, hood = candidate_catch_boxes(L)
    root, slot = tine_root(LayoutView(L, HOOD=hood), tub, CK)
    steps, last, ins, rem = lens_records(L, ST)
    cots, kept, dropped = cots_box_view(L, shapes, CK)
    view = LayoutView(L, HOOD=hood, ZT1=root if root is not None else float('nan'), STEPS=steps,
                      INSERTIONS=ins, REMOVALS=rem, LATCH_FREE={}, COTS=cots,
                      present_at=lambda n: _alias(ST.present_at(last[n])), tab_catch_boxes=lambda _L: boxes)
    rows = {('hood' if k == 'tub' else k): v for k, v in rr.items()}
    out = CK.check_roll_catch(view, rows, s_values=s_values, parts_of=parts_of, assembly_path=str(CV / ASSEMBLY))
    out = [r for r in out if r.get('item') != 'lens_hold_lint']
    guides = [CV / g for g in GUIDE_SOURCES]
    bad, have_asm = CK.lens_hold_lint(view, assembly_path=str(CV / ASSEMBLY), guide_paths=[str(g) for g in guides])
    probs = (['%s: "%s"' % (w, p) for w, p in bad] + ([] if have_asm else ['%s not found: not linted' % ASSEMBLY])
             + ['%s not found: not linted' % g.name for g in guides if not g.exists()] + CK.lens_turn_back_lint(view))
    out.append(_row('roll_catch', 'fail' if probs else 'pass', '; '.join(probs[:8]), item='lens_hold_lint',
                    phrases=list(L.LENS_HOLD_FORBIDDEN), hits=len(bad),
                    scope='steps.py op texts (per build step), %s hand-written text (lines + paragraphs), guide '
                          'sources %s (string literals); turn-back before s_c4 for hold records'
                          % (ASSEMBLY, list(GUIDE_SOURCES))))
    miss = catch_material(L, tub, boxes)
    for r in out:
        if r.get('item') == 'tab_catch_geometry':
            r.update(catch_host='tub', top_z=CATCH_TOP_Z, catch_boxes=[{a: list(b[a]) for a in 'xyz'} for b in boxes],
                     not_tub_material=miss[:12], tine_root_z=root, slot_first_material_z=slot,
                     tine_root_basis='tub roof underside beside the catch (ray +Z on the STEP); r7 used ZT1 (hood band '
                                     'underside). The panel-screw boss above the slot (first material at the slot '
                                     'centre) is not credited: the longer roof arm is kept (conservative)',
                     cots_boxes_kept=kept, cots_boxes_dropped_moved=dropped)
            errs = [r['error']] if r.get('error') else []
            if miss:
                errs.append('%d catch sample points are not tub material' % len(miss))
            if root is None or not (CATCH_TOP_Z - 1.0 <= root <= CATCH_TOP_Z + 0.01):
                errs.append('tine root %s not at the roof (catch top %.1f)' % (root, CATCH_TOP_Z))
            if errs:
                r.update(status='fail', error='; '.join(errs))
        if r.get('item') == 'tine_strength':
            r['note'] = ('E %.0f MPa and the r7 limits unchanged; cantilever from the tub roof underside (z %s, '
                         'measured) to the lowest contact; the boss above the slot is not credited and the tub prints '
                         '-Y down (tine printability: VN-53, FP-09 / FP-11b); G-CAM-2 records the roll under fingertip '
                         'torque' % (L.ROLL_CATCH['E_MPa'], root))
    out = [dict(_unalias(r), catch_host='tub') for r in out]
    return [('roll_catch', roll_ident(r), r) for r in out]


# FX (verifier T2 minor): the +Y catch is a bonded stub (model.tab_catch_split); the roll_catch rows above grade the
# ideal bonded tub. Its location stack-up: the tenon's -Y face is the zero-clearance datum, so an adhesive film moves
# the stub +Y by its thickness; the pocket clearances let it shift +-0.1 in x and tilt 0.1 mm over the modeled tenon
# about x with the tenon's -Y face still on the datum at one end (pivot on the datum's lower edge on the joint plane:
# the tenon top swings +Y and the catch face below swings -Y; or pivot on its upper edge: the whole stub swings +Y).
# Each case rebuilds the tub as print stock + displaced stub and reruns r7 check_roll_catch; its window and
# first-contact rows gate exactly as the nominal ones.
STUB_FILM_MM = 0.05
STUB_CASES = (('x+0.1', (0.1, 0.0, 0.0), 0.0, 0.0), ('x-0.1', (-0.1, 0.0, 0.0), 0.0, 0.0),
              ('film+y0.05', (0.0, STUB_FILM_MM, 0.0), 0.0, 0.0),
              ('tilt_on_joint_edge', (0.0, 0.0, 0.0), -1.0, 0.0), ('tilt_on_tenon_top_edge', (0.0, 0.0, 0.0), 1.0, 1.0))
STUB_FEASIBLE_OVERLAP_MM3 = 0.001
STUB_FILM_VARIATION_MM = 0.1
STUB_UNDERSEAT_SCREEN_MM = 0.1  # chosen numerical screen; the open pocket has no withdrawal stop
STUB_WINDOW_CENTRED_MM = 0.30
STUB_WINDOW_WORST_MM = 0.10
STUB_CONTACT_RULES = dict(window_deg=1.4, window_gap=.30, scan_deg=14.0, step_deg=.5, tol=.01, margin_deg=1.0)
STUB_REQUIRED_FEASIBLE = frozenset(('T02_tilt_on_joint_edge', 'Y2_yaw_pivot_xplus'))
STUB_TRANSLATION_CASES = frozenset(['P_full_y_clearance', 'P_underseat_zminus'] + [
    'P_corner_%s_%s_%s' % (x, y, z) for x in ('xminus', 'xplus')
    for y in ('ynear', 'yfar') for z in ('zseated', 'zunder') if (y, z) != ('ynear', 'zseated')])
STUB_POCKET_YAW_CASES = frozenset('YP_yaw_%s_%s_%s' % (sign, x, y)
    for sign in ('m', 'p') for x in ('xminus', 'xplus') for y in ('near', 'far'))


def _rotate_point(point, axis, pivot, deg):
    """Same right-hand, fixed-world-axis transform as OCCT Shape.rotate, without importing CAD."""
    q = [point[i] - pivot[i] for i in range(3)]
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    i, j = {'x': (1, 2), 'y': (2, 0), 'z': (0, 1)}[axis]
    q[i], q[j] = c * q[i] - s * q[j], s * q[i] + c * q[j]
    return tuple(q[k] + pivot[k] for k in range(3))


def stub_pose_table(model, web, pocket_bounds):
    """Finite physical-pose sampling, not a continuous clearance proof or a cure-fixture allowance.

    Keep the five original transforms, add both signs at both bearing edges for
    all three axes, then half- and quarter-allowance coupled poses. X/Y limits
    come from the production pocket; Z underseat is an explicitly chosen screen,
    NOT its cutter-overlap epsilon or a mechanical withdrawal stop. Whole-insert/
    host intersection is still required. No rated production tolerance is claimed.
    """
    tn, zs = model.TAB_CATCH_TENON, model.TAB_CATCH_SPLIT_Z
    yin, xm = web['y'][0], sum(web['x']) / 2
    h, w, wj = tn['h'], tn['x'][1] - tn['x'][0], web['x'][1] - web['x'][0]
    xmin, xmax, ymin, ymax, zmin, zmax = pocket_bounds
    cx = min(tn['x'][0] - xmin, xmax - tn['x'][1])
    cy = ymax - (yin + tn['t'])
    if min(cx, cy, zmax - (zs + h)) < -1e-7 or abs(ymin - yin) > 1e-6:
        raise ValueError('production pocket does not enclose the declared tenon and dry -Y datum')
    t01, t02 = (math.degrees(math.atan(v / h)) for v in (STUB_FILM_VARIATION_MM, cy))
    yaw = math.degrees(math.atan(STUB_FILM_VARIATION_MM / w))
    full_yaw = math.degrees(math.atan(cy / w))
    roll = math.degrees(math.atan(cx / h))
    rfilm = math.degrees(math.atan(STUB_FILM_VARIATION_MM / wj))
    poses = []

    def add(name, rotations=(), shift=(0., 0., 0.), **kw):
        poses.append(dict(case=name, rotations=[dict(axis=a, pivot=list(p), deg=d) for a, p, d in rotations],
                          shift_mm=list(shift), **kw))
    for name, d, tilt, top in STUB_CASES:
        piv = (xm, yin, zs + top * h)
        add(name, [('x', piv, tilt * t01)] if tilt else [], d, family='legacy', legacy=True,
            basis='unchanged original five-case displacement')
    under = STUB_UNDERSEAT_SCREEN_MM
    translation_basis = ('actual X/Y pocket bounds; chosen axial-underseat screen %.9g mm, '
                         'not a mechanical stop or qualified production tolerance') % under
    add('P_full_y_clearance', shift=(0., cy, 0.), family='translation', basis=translation_basis)
    add('P_underseat_zminus', shift=(0., 0., -under), family='translation', basis=translation_basis)
    for plus, far, low in itertools.product((False, True), repeat=3):
        if not far and not low:
            continue  # exactly the original x +/-0.1 cases, checked against actual X limits below
        add('P_corner_%s_%s_%s' % ('xplus' if plus else 'xminus', 'yfar' if far else 'ynear',
                                   'zunder' if low else 'zseated'),
            shift=(xmax - tn['x'][1] if plus else xmin - tn['x'][0], cy if far else 0., -under if low else 0.),
            family='translation', basis=translation_basis)
    if abs(cx - .1) > 1e-7:
        raise ValueError('reviewed X corner bounds changed; retain explicit endpoint coverage')
    for top in (False, True):
        edge = 'tenon_top_edge' if top else 'joint_edge'
        for sign in (-1, 1):
            canonical = sign == (1 if top else -1)
            name = 'T02_tilt_on_' + edge + ('' if canonical else '_reverse')
            add(name, [('x', (xm, yin, zs + top * h), sign * t02)], family='tilt_x',
                basis='full measured +Y pocket clearance %.9g / tenon height %.9g' % (cy, h))
    for plus in (False, True):
        edge, x = ('xplus', tn['x'][1]) if plus else ('xminus', tn['x'][0])
        for sign in (-1, 1):
            canonical = sign == (-1 if plus else 1)
            name = ('Y2' if plus else 'Y1') + '_yaw_pivot_' + edge + ('' if canonical else '_reverse')
            add(name, [('z', (x, yin, zs), sign * yaw)], family='yaw_z',
                basis='0.1 mm film variation across actual tenon width %.9g' % w)
    corners = list(itertools.product(tn['x'], (yin, yin + tn['t']), (zs, zs + h)))
    yaw_center = ((tn['x'][0] + tn['x'][1]) / 2, yin + tn['t'] / 2, zs)
    for sign in (-1, 1):
        rotations = [('z', yaw_center, sign * full_yaw)]
        points = [_rotate_point(p, 'z', yaw_center, sign * full_yaw) for p in corners]
        intervals = [(pocket_bounds[2 * i] - min(p[i] for p in points),
                      pocket_bounds[2 * i + 1] - max(p[i] for p in points)) for i in (0, 1)]
        fits = all(lo <= hi + 1e-9 for lo, hi in intervals)
        for plus, far in itertools.product((False, True), repeat=2):
            add('YP_yaw_%s_%s_%s' % ('p' if sign > 0 else 'm', 'xplus' if plus else 'xminus',
                                      'far' if far else 'near'), rotations,
                shift=(intervals[0][plus], intervals[1][far], 0.), family='pocket_yaw_z',
                fits_pocket_bounds=fits, translation_intervals_mm=intervals,
                basis='full actual Y clearance %.9g / tenon width %.9g; fitted to actual X/Y pocket bounds' % (cy, w))
    for film, angle in ((True, rfilm), (False, roll)):
        for plus in (False, True):
            edge, x = ('xplus', web['x'][1]) if plus else ('xminus', web['x'][0])
            for sign in (-1, 1):
                canonical = sign == (-1 if plus else 1)
                n = (2 if plus else 1) + (0 if film else 2)
                name = 'R%d_roll_%s_pivot_%s%s' % (n, 'film' if film else 'clear', edge,
                                                  '' if canonical else '_reverse')
                add(name, [('y', (x, yin, zs), sign * angle)], family='roll_y',
                    basis=('0.1 mm film variation / joint-face width' if film else
                           'measured pocket X side clearance %.9g / tenon height' % cx))
    fit_bounds = list(pocket_bounds)
    fit_bounds[4] = zs - STUB_UNDERSEAT_SCREEN_MM
    center = ((tn['x'][0] + tn['x'][1]) / 2, yin + tn['t'] / 2, zs + h / 2)
    for fraction, prefix in ((.5, 'C'), (.25, 'CI')):
        for signs in itertools.product((-1, 1), repeat=3):
            rots = [(axis, center, sign * angle * fraction) for axis, sign, angle in zip('xyz', signs, (t02, roll, full_yaw))]
            points = corners
            for axis, pivot, angle in rots:
                points = [_rotate_point(p, axis, pivot, angle) for p in points]
            intervals = [(fit_bounds[2 * i] - min(p[i] for p in points),
                          fit_bounds[2 * i + 1] - max(p[i] for p in points)) for i in range(3)]
            fits = all(lo <= hi + 1e-9 for lo, hi in intervals)
            for far in (False, True):
                # Both film/datum Y extremes and sign-selected X extremes. This
                # bounded sample uses the explicit underseat-screen lower Z;
                # the open mouth does NOT mechanically limit withdrawal or prove
                # seating/retention. Actual ceiling collisions are never waived.
                shift = (intervals[0][signs[2] > 0], intervals[1][far], intervals[2][0])
                add(prefix + '_xyz_%s_%s' % (''.join('p' if s > 0 else 'm' for s in signs), 'far' if far else 'near'),
                    rots, shift, family='coupled_xyz', rotation_fraction=fraction, fits_pocket_bounds=fits,
                    translation_intervals_mm=intervals, rotation_order='fixed world X, then Y, then Z',
                    underseat_screen_mm=STUB_UNDERSEAT_SCREEN_MM,
                    basis='%.2f axis allowances; actual X/Y pocket bounds and explicit Z underseat screen; '
                          'no fixture credit or production tolerance qualification' % fraction)
    for pose in poses:
        ends = []
        for z in (zs, zs + h):
            pts = [_pose_point(p, pose) for p in itertools.product(tn['x'], (yin, yin + tn['t']), (z,))]
            ends.append(pts)
        pts = ends[0] + ends[1]
        pose['tenon_core_bounds_mm'] = [f(p[i] for p in pts) for i in range(3) for f in (min, max)]
        pose['minimum_axial_engagement_mm'] = (min(zmax, min(p[2] for p in ends[1])) -
                                                max(zs, max(p[2] for p in ends[0])))
        pose['engagement_scope'] = 'bounded joint pose with retained tenon; further withdrawal and bond retention unqualified'
    return poses


def _pose_point(point, pose):
    for r in pose['rotations']:
        point = _rotate_point(point, r['axis'], r['pivot'], r['deg'])
    return tuple(p + d for p, d in zip(point, pose['shift_mm']))


def transform_stub(stub, pose):
    import cadquery as cq
    axes = dict(x=(1, 0, 0), y=(0, 1, 0), z=(0, 0, 1))
    for r in pose['rotations']:
        pv = cq.Vector(*r['pivot'])
        stub = stub.rotate(pv, pv + cq.Vector(*axes[r['axis']]), r['deg'])
    return stub.translate(cq.Vector(*pose['shift_mm']))


def stub_pose_feasibility(stock, displaced, pose):
    """Never infer feasibility from a nominal angle or from contact to adhesive-filled assembly stock."""
    overlap = float(stock.intersect(displaced).Volume())
    valid = math.isfinite(overlap) and overlap >= -1e-9 and displaced.isValid() and len(displaced.Solids()) == 1
    engagement = pose.get('minimum_axial_engagement_mm', float('nan'))
    retained = math.isfinite(engagement) and engagement > 0
    feasible = valid and retained and overlap <= STUB_FEASIBLE_OVERLAP_MM3 and pose.get('fits_pocket_bounds', True)
    return dict(feasible=bool(feasible), geometry_valid=bool(valid), stub_stock_overlap_mm3=overlap,
                feasible_overlap_mm3=STUB_FEASIBLE_OVERLAP_MM3,
                exclusion_reason=None if feasible else ('tenon engagement not retained' if not retained else
                    'tenon exceeds pocket bounds' if not pose.get(
                    'fits_pocket_bounds', True) else 'whole displaced production insert intersects production host'))


def cached_camera_parts(parts_of=None):
    """One immutable camera build per BFAR/head configuration, scoped to one fixed-layout catch run."""
    if parts_of is None:
        import cots
        parts_of = cots.gs_camera_parts
    cache = {}

    def get(L, s=None, head_side='both'):
        key = (id(getattr(L, '_base', L)), s, head_side)
        if key not in cache:
            cache[key] = parts_of(L, s) if head_side == 'both' else parts_of(L, s, head_side=head_side)
        return cache[key]
    return get


def stub_acceptance_errors(poses, records, s_values, L, CK):
    """Fail closed on removed cases, missing feasible rows, hidden failures, or relaxed rules."""
    errors = []
    names = [p['case'] for p in poses]
    if len(names) != len(set(names)) or set(names) != set(records):
        errors.append('pose/feasibility records are missing or duplicated')
    if not STUB_REQUIRED_FEASIBLE <= set(names):
        errors.append('required T02 or Y2 case missing')
    if {p['case'] for p in poses if p['family'] == 'translation'} != STUB_TRANSLATION_CASES:
        errors.append('full-Y, axial-underseat or translation pocket-corner coverage missing')
    if {p['case'] for p in poses if p['family'] == 'pocket_yaw_z'} != STUB_POCKET_YAW_CASES:
        errors.append('full-pocket yaw boundary coverage missing')
    if {p['case'] for p in poses if p.get('legacy')} != {p[0] for p in STUB_CASES}:
        errors.append('original five cases missing')
    for family, axis in (('tilt_x', 'x'), ('roll_y', 'y'), ('yaw_z', 'z')):
        candidates = [p for p in poses if p['family'] == family]
        pivots = {}
        for p in candidates:
            r = p['rotations'][0]
            if r['axis'] == axis:
                pivots.setdefault(tuple(r['pivot']), set()).add(math.copysign(1, r['deg']))
        if len(pivots) < 2 or any(signs != {-1, 1} for signs in pivots.values()):
            errors.append('missing both-sign/both-edge %s coverage' % family)
    for fraction in (.5, .25):
        coupled = [p for p in poses if p['family'] == 'coupled_xyz' and p.get('rotation_fraction') == fraction]
        signatures = {tuple(math.copysign(1, r['deg']) for r in p['rotations']) for p in coupled
                      if ''.join(r['axis'] for r in p['rotations']) == 'xyz'}
        if len(coupled) != 16 or signatures != set(itertools.product((-1, 1), repeat=3)):
            errors.append('bounded %.2f-allowance coupled XYZ coverage missing' % fraction)
    if (L.ROLL_CATCH['window_gap'] != STUB_WINDOW_CENTRED_MM or CK.J7_RUNNING != STUB_WINDOW_WORST_MM
            or CK.J7_TOL != 1e-3 or STUB_FEASIBLE_OVERLAP_MM3 != 1e-3):
        errors.append('window/feasibility/tolerance rules changed')
    if any(L.ROLL_CATCH.get(k) != v for k, v in STUB_CONTACT_RULES.items()):
        errors.append('first-contact/window scan rules changed')
    expected = {(item, float(s)) for item in ('window', 'first_contact') for s in s_values}
    pose_by_name = {p['case']: p for p in poses}
    for name, rec in records.items():
        overlap = rec.get('stub_stock_overlap_mm3', float('nan'))
        physical = (rec.get('geometry_valid', False) and math.isfinite(overlap) and -1e-9 <= overlap <= .001
                    and pose_by_name.get(name, {}).get('fits_pocket_bounds', True)
                    and rec.get('minimum_axial_engagement_mm', 0) > 0)
        if not rec.get('geometry_valid') or rec['feasible'] != physical or rec.get('feasible_overlap_mm3') != .001:
            errors.append('%s: invalid or inconsistent physical feasibility' % name)
        rows = rec.get('rows', [])
        got = [(r['item'], float(r['s'])) for r in rows]
        if rec['feasible'] or rec.get('legacy'):
            if set(got) != expected or len(got) != len(expected):
                errors.append('%s: missing or duplicate full-BFAR functional rows' % name)
        elif rows:
            errors.append('%s: infeasible new pose was graded' % name)
        if name in STUB_REQUIRED_FEASIBLE and not rec['feasible']:
            errors.append('%s: required reviewed physical pose unexpectedly excluded' % name)
        for r in rows:
            if r['item'] == 'window' and r.get('status') == 'pass' and (r.get('centred_gap') is None or
                    r.get('worst_gap') is None or r['centred_gap'] < .30 - .001 or r['worst_gap'] < .10 - .001):
                errors.append('%s: failing window was relabelled pass' % name)
            if r['item'] == 'first_contact' and r.get('rule_margin_deg') != L.ROLL_CATCH['margin_deg']:
                errors.append('%s: first-contact margin changed' % name)
    if not any(r.get('feasible') for r in records.values() if r.get('family') == 'coupled_xyz'):
        errors.append('no coupled physical pose was tested')
    return errors


def roll_catch_stub_rows(L, rr, shapes, CK, ST, s_values=None, parts_of=None, production_insert=None):
    import cadquery as cq
    import model
    tub = rr['tub']['shape']
    with __import__('j4_trial_geometry').trial_layout(model.L, lip=2.4, head=2.4):
        stock, stub = model.tub_print_parts(tub)
        tc = {(b['side'], b['kind']): b for b in model.L.tab_catch_boxes()}
        pb = model.tab_catch_split()['pocket'].BoundingBox()
    web = tc[(1, 'web')]
    pocket_bounds = [getattr(pb, a + end) for a in 'xyz' for end in ('min', 'max')]
    if production_insert is not None:
        delta = _symdiff(stub, production_insert)
        if delta > 0.001:
            raise ValueError('production insert differs from model by %.9g mm3' % delta)
        stub = production_insert
    poses = stub_pose_table(model, web, pocket_bounds)
    joint_points = [v.toTuple() for v in stub.Vertices() if abs(v.Z - model.TAB_CATCH_SPLIT_Z) < 1e-6]
    if not joint_points:
        raise ValueError('production insert has no joint-face vertices for the seating-gap measurement')
    for pose in poses:
        gaps = [model.TAB_CATCH_SPLIT_Z - _pose_point(p, pose)[2] for p in joint_points]
        pose['joint_face_gap_range_mm'] = [min(gaps), max(gaps)]
        pose['joint_face_reference_points'] = len(joint_points)
    sv = tuple(s_values if s_values is not None else CK.j7_s_values(L))
    parts_of = cached_camera_parts(parts_of)
    out = []
    records = {}
    for pose in poses:
        case = pose['case']
        sb = transform_stub(stub, pose)
        feasibility = stub_pose_feasibility(stock, sb, pose)
        rec = records[case] = dict(pose, **feasibility, rows=[])
        out.append(('roll_catch', 'stub_%s:feasibility' % case, _row(
            'roll_catch', 'pass' if feasibility['geometry_valid'] else 'fail', 'invalid feasibility geometry',
            item='stub_feasibility', stub_case=case, **pose, **feasibility,
            pocket_bounds_mm=pocket_bounds, graded=feasibility['feasible'] or pose.get('legacy', False),
            legacy_blocked_diagnostic=bool(pose.get('legacy') and not feasibility['feasible']))))
        if not feasibility['feasible'] and not pose.get('legacy'):
            continue
        t_case = stock.fuse(sb).clean()
        rr_case = dict(rr, tub=dict(rr['tub'], shape=t_case))
        rows = roll_catch_rows(L, rr_case, shapes, CK, ST, s_values=sv, parts_of=parts_of)
        for cat, ident, r in rows:
            if r.get('item') in ('window', 'first_contact') and r.get('status') in ('pass', 'fail'):
                r = dict(r, stub_case=case, stub_shift_mm=pose['shift_mm'], stub_rotations=pose['rotations'],
                         stub_feasible=feasibility['feasible'],
                         legacy_blocked_diagnostic=bool(pose.get('legacy') and not feasibility['feasible']),
                         note='Actual production host and transformed insert; unchanged r7 window and first-contact '
                              'rules. Finite pocket-bounded samples, no cure-fixture credit.')
                rec['rows'].append(r)
                out.append((cat, 'stub_%s:%s' % (case, ident), r))
    errors = stub_acceptance_errors(poses, records, sv, L, CK)
    out.append(('roll_catch', 'stub_pose_coverage', _row('roll_catch', 'fail' if errors else 'pass', '; '.join(errors),
        item='stub_pose_coverage', cases=[p['case'] for p in poses], pose_count=len(poses),
        feasible_count=sum(r['feasible'] for r in records.values()), pocket_bounds_mm=pocket_bounds,
        production_insert_supplied=production_insert is not None, errors=errors,
        s_values=list(sv), rule='original five, full-Y/axial-underseat and pocket translation corners, '
                              'both-sign edge rotations XYZ, thirty-two bounded coupled poses; '
                              'every feasible case retains full-BFAR window and first-contact rows')))
    return out


def production_insert(variant, meta):
    """The separately printed insert STEP is outside manifest rows, but inside the file hash binding."""
    import cadquery as cq
    rel = 'step/tab_catch_insert.step'
    path = CV / 'out' / variant / rel
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != meta['files'].get(rel):
        raise ValueError('production tab_catch_insert STEP is not manifest-bound')
    shape = cq.importers.importStep(str(path)).val()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError('production tab_catch_insert STEP is not one valid solid')
    return shape, dict(step_sha256=digest, manifest_file_binding=True, step=rel)


def roll_ident(r):
    it = r.get('item')
    if it in ('first_contact', 'first_contact_unconfirmed'):
        return '%s%s@s%.2f' % (it, '' if r.get('variant') in (None, 'declared') else ':' + r['variant'], r['s'])
    if it == 'window':
        return 'window@s%.2f' % r['s']
    if it == 'lens_hold':
        return 'lens_hold:%s' % r['record']
    return it


# ------------------------------------------------------------------------------------------------ lens support + gauge
def lens_collars(L, rr, lens, CK, variant=None):
    """({lens: collar}, rows): the STEP collar for the variant lens, the others rebuilt in the candidate layout context
    (as r7 build_d2.lens_collars) and each compared with the manifest-bound collar STEP of its own variant."""
    import json
    import cadquery as cq
    import model as M
    out, rows = {lens: rr['lens_collar']['shape']}, []
    storage = (variant or 'compact-').split('-', 1)[0]
    for n in L.LENSES:
        if n == lens or L.collar_spec(n) is None:
            continue
        out[n] = _as_shape(M.make_collar(n))      # C2: model._build's collar builder (see context_rows)
        folder = next((CV / 'out' / v for v in ('%s-%s' % (storage, n), 'compact-%s' % n)
                       if (CV / 'out' / v / 'step' / 'lens_collar.step').exists()), None)
        d, bound, ref = None, False, None
        if folder is not None:
            p = folder / 'step' / 'lens_collar.step'
            ref = '%s/step/lens_collar.step' % folder.name
            files = json.loads((folder / 'manifest.json').read_bytes().decode('utf-8'))['files']
            bound = hashlib.sha256(p.read_bytes()).hexdigest() == files.get('step/lens_collar.step')
            d = _symdiff(out[n], cq.importers.importStep(str(p)).val())
        ok = bound and d is not None and d <= 0.01
        rows.append(('lens_support', n + '/collar_context_match', _row(
            'lens_support', 'pass' if ok else 'fail', 'rebuilt %s collar vs %s: bound %s, symmetric difference %s'
            % (n, ref, bound, d), item='collar_context_match', lens=n, reference=ref, manifest_file_binding=bound,
            symmetric_difference_mm3=None if d is None else CK._r(d, 4),
            rule='collar rebuilt in the candidate layout context == that variant\'s manifest-bound STEP (<= 0.01 mm3)')))
    return out, rows


def lens_support_rows(L, rr, collars, CK):
    """r7 check_lens_support for every lens (no inherited G-LENS record: the candidate inherits no gate)."""
    out = CK.check_lens_support(L, rr, collars=collars, measured={'G-LENS': False}, require_collars=set(L.LENSES))
    return [('lens_support', '%s/%s' % (r['lens'], r['item']), r) for r in out]


def gauge_rows(L, rr, gauge, CK, ST, travel=40.0, step_mm=1.0):
    """r7 check_collar_gauge (tub / collar seats, insertion, s_c1..s_c3 driver) plus, for r7's hood row, >= 0.5 to
    every other part present at gauge_in (steps.py) and the insertion sweep against them."""
    base = {k: rr[k] for k in ('tub', 'lens_collar') if k in rr}
    out = [r for r in CK.check_collar_gauge(L, base, gauge, travel=travel, step_mm=step_mm) if r.get('part') != 'hood']
    present = set(ST.present_at('gauge_in')) - {'centring_gauge', 'tub', 'lens_collar'}
    others = {oid: r for oid, r in rr.items() if parent(oid) in present}
    tag = dict(kind='lens_support', item='centring_gauge', lens=L.LENS)
    missing = sorted(present - {parent(o) for o in others})
    out.append(_row('lens_support', 'fail' if missing else 'pass', 'present at gauge_in but not loaded: %s' % missing,
                    part='present_set', present=sorted(present), missing=missing,
                    **{k: v for k, v in tag.items() if k != 'kind'}))
    gaps, hits = {}, {}
    if gauge is not None:
        mg = CK.manifold_of(gauge)
        for oid in sorted(others):
            sh = others[oid]['shape']
            v, _ = CK.common(gauge, sh)
            gap = float(gauge.distance(sh)) if v == v and v <= CK.VOL_TOL else 0.0
            gaps[oid] = dict(overlap_mm3=CK._r(v, 4), gap=CK._r(gap, 4))
            mo = CK.manifold_of(sh)
            if mo is None or mg is None:
                hits[oid] = 'no mesh'
                continue
            for k in range(1, int(round(travel / step_mm)) + 1):
                vv = (mg.translate([k * step_mm, 0.0, 0.0]) ^ mo).volume()
                if vv > CK.SWEEP_TOL:
                    hits[oid] = max(hits.get(oid, 0.0), CK._r(vv, 2))
    near = {o: g for o, g in gaps.items() if not (g['overlap_mm3'] == g['overlap_mm3'] and g['overlap_mm3'] <=
                                                    CK.VOL_TOL and g['gap'] >= GAUGE_OTHER_GAP - CK.J7_TOL)}
    out.append(_row('lens_support', 'fail' if gauge is None or near else 'pass',
                    'gauge within %.1f of %s' % (GAUGE_OTHER_GAP, near) if gauge is not None else 'no gauge solid',
                    part='other_present', gaps=gaps, offending_obstacles=sorted(near),
                    rule='seated gauge >= %.1f to every other part present at gauge_in (r7: the hood)' % GAUGE_OTHER_GAP,
                    **{k: v for k, v in tag.items() if k != 'kind'}))
    out.append(_row('lens_support', 'fail' if gauge is None or hits else 'pass',
                    'gauge insertion meets %s' % hits, part='insertion_other_present', hits=hits,
                    path='-X %.0f to the seated pose in %.1f steps (manifold, SWEEP_TOL %.1f mm3)'
                         % (travel, step_mm, CK.SWEEP_TOL), **{k: v for k, v in tag.items() if k != 'kind'}))
    return [('lens_support', 'centring_gauge/%s' % r['part'], r) for r in out]


# ------------------------------------------------------------------------------------------------ clamp + washer
def lens_clamp_rows(L, rr, collars, CK):
    out = CK.check_lens_clamp(L, rr, collars=collars)
    return [('lens_clamp', 'clamp/%s' % r['lens'] if r.get('item') == 'clamp' else r['item'], r) for r in out]


def washer_rows(L, collars, CK):
    """r7 test_mechanical_refinements washer tests as rows, r7 thresholds, per lens collar:
    flat support: the washer footprint (washer d/2 + washer_float + washer_edge_min, 0.05 thick under the seat, less
    the clearance hole) is collar material (unsupported < 0.002 mm3); free seat: the washer at the centre and at +-float
    in x and y overlaps nothing (< 0.001 mm3). Also the nominal margins to the lug face and the bit relief."""
    import cadquery as cq
    V = cq.Vector
    lug, W, M3 = L.COLLAR['lug'], L.M3['washer'], L.M3
    x, y, z = lug['screw_x'], lug['screw_y'], lug['upper_z'][1]
    f = lug['washer_float']
    r_fp = W['d'] / 2 + f + lug['washer_edge_min']
    out = []
    for name in sorted(collars):
        sh = collars[name]
        fp = cq.Solid.makeCylinder(r_fp, 0.05, V(x, y, z - 0.05), V(0, 0, 1)).cut(
            cq.Solid.makeCylinder(M3['clear_d'] / 2 + 0.01, 0.2, V(x, y, z - 0.1), V(0, 0, 1)))
        un = float(fp.cut(sh).Volume())
        margins = dict(lug_face_mm=CK._r(abs(y - lug['y_out']) - r_fp, 3),
                       bit_relief_mm=CK._r(abs(lug['bit_relief_y'] - y) - W['d'] / 2, 3))
        out.append(('lens_clamp', 'washer_flat_support/%s' % name, _row(
            'lens_clamp', 'pass' if un < 0.002 else 'fail',
            'washer flat support: %.4f mm3 (%.3f mm2) of the r %.2f footprint is not collar material' % (un, un / 0.05, r_fp),
            item='washer_flat_support', lens=name, unsupported_mm3=CK._r(un, 4), unsupported_mm2=CK._r(un / 0.05, 3),
            footprint_r_mm=r_fp, seat=[x, y, z], nominal_margins=margins,
            rule='r7 test_washer_flat_support_with_float_and_margin: unsupported < 0.002 mm3',
            source='../test_mechanical_refinements.py (r7, read-only)')))
        cases, worst = [], 0.0
        # gap = washer to the collar material above the seat plane (the seat face itself is the intended contact)
        above = sh.intersect(cq.Solid.makeBox(24.0, 24.0, 6.0, V(x - 12.0, y - 12.0, z + 0.01)))
        for dx, dy in ((0, 0), (f, 0), (-f, 0), (0, f), (0, -f)):
            w = cq.Solid.makeCylinder(W['d'] / 2, W['t'], V(x + dx, y + dy, z), V(0, 0, 1))
            v = float(w.intersect(sh).Volume())
            gap = float(w.distance(above)) if v < 1e-9 and above.Volume() > 1e-9 else (0.0 if v >= 1e-9 else None)
            cases.append(dict(dx=dx, dy=dy, overlap_mm3=CK._r(v, 4), gap_mm=CK._r(gap, 4)))
            worst = max(worst, v)
        out.append(('lens_clamp', 'washer_free_seat/%s' % name, _row(
            'lens_clamp', 'pass' if worst < 0.001 else 'fail',
            'washer seat not free: worst overlap %.4f mm3 at %s' % (worst, [c for c in cases if c['overlap_mm3'] >= 0.001]),
            item='washer_free_seat', lens=name, cases=cases, worst_overlap_mm3=CK._r(worst, 4),
            min_gap_mm=min((c['gap_mm'] for c in cases if c['gap_mm'] is not None), default=None),
            gap_basis='washer to the collar material above the seat plane (bit-relief wall)', nominal_margins=margins,
            rule='r7 test_washer_has_free_seat_at_every_float_extreme: overlap < 0.001 mm3 at 0 and +-%.1f in x, y' % f,
            source='../test_mechanical_refinements.py (r7, read-only)')))
    return out


def insert_rows(L, rr, CK):
    return [('inserts', r['screw'], r) for r in CK.check_inserts(L, rr)]


# ------------------------------------------------------------------------------------------------ entry point
SECTIONS = ('context', 'j7_float', 'roll_catch', 'lens_support', 'centring_gauge', 'lens_clamp', 'washer', 'inserts')


def j7_rows(shapes, manifest_rows, meta, variant, s_values=None, only=SECTIONS):
    """verify_candidate add() kwargs for every FP-08 row. A section that raises becomes a fail row (never skipped)."""
    import traceback
    import checks as CK
    import steps as ST
    lens = lens_of(variant, meta)
    rr = r7_rows(shapes, manifest_rows)
    out, seen = [], set()

    def put(items, extra=None):
        for cat, ident, r in items:
            if (cat, ident) in seen:
                raise ValueError('duplicate FP-08 row %s/%s' % (cat, ident))
            seen.add((cat, ident))
            out.append(emit(cat, ident, r, **(extra or {})))
    collars = {lens: rr['lens_collar']['shape']}

    def other_collars():
        built, rows = lens_collars(L, rr, lens, CK, variant)
        collars.update(built)
        return rows

    def catch_rows():
        insert, binding = production_insert(variant, meta)
        return ([('roll_catch', 'stub_production_context', _row('roll_catch', 'pass',
                    item='stub_production_context', **binding))]
                + roll_catch_rows(L, rr, shapes, CK, ST, s_values=s_values)
                + roll_catch_stub_rows(L, rr, shapes, CK, ST, s_values=s_values, production_insert=insert))
    with candidate_layout(lens) as L:
        jobs = [('context', lambda: context_rows(L, rr, lens, CK)[0]),
                ('j7_float', lambda: j7_float_rows(L, rr, CK, s_values=s_values)),
                ('roll_catch', catch_rows),
                ('collars', other_collars),
                ('lens_support', lambda: lens_support_rows(L, rr, collars, CK)),
                ('centring_gauge', lambda: gauge_rows(L, rr, shapes.get('centring_gauge'), CK, ST)),
                ('lens_clamp', lambda: lens_clamp_rows(L, rr, collars, CK)),
                ('washer', lambda: washer_rows(L, collars, CK)),
                ('inserts', lambda: insert_rows(L, rr, CK))]
        for name, job in jobs:
            if name != 'collars' and name not in only:
                continue
            try:
                put(job(), dict(variant=variant))
            except Exception as e:  # noqa: BLE001  a crash is a failed row, never a pass or a skip
                put([('lens_clamp' if name == 'washer' else ('lens_support' if name in ('context', 'collars', 'centring_gauge')
                      else name), 'section_error:%s' % name,
                      _row(name, 'fail', '%s: %s' % (type(e).__name__, e), item='section_error',
                           traceback=traceback.format_exc()[-2000:]))])
    return out
