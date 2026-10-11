# SPDX-License-Identifier: MIT
"""Declared non-plenum additions inside the original tub cavity (review 2026-10-10 fix-up FX; verifier C1+T2 major).

verify_shadow_plenum's row no_added_material_in_original_cavity compares the saved tub with the historical export18 tub
inside the original cavity box. Two phase-2 lanes added material there on purpose (FP-11c: the carrier locator seat;
T2: the print-pose fills, the FPS pair-guide corbel and the tab-catch ceiling and pad), so the row failed on intended
geometry. The row is rescoped, not weakened: the added material minus an explicit inventory of declared additions,
each rebuilt here from model.py in model.build's layout state, must be empty (< 1e-5 mm3, the row's original
tolerance). Undeclared material still fails, a declared addition that is missing from the tub fails as a stale
declaration, and the inventory ids are pinned in tests/test_fx_fixup.py.

Every declared addition is part of the saved tub STEP, so every row that checks the whole tub covers it: the main audit
interference and motion rows, the harness installed-route and feed-volume sweeps, the FPS integrated carry and the
HDMI sweeps (COVERED_BY).
"""
import copy

# id -> (model source, what it is)
INVENTORY = {
    'carrier_locator_seat': 'model.carrier_locator_seat (FP-11c, VN-38): tub floor seat rib under the carrier tongue',
    't2_minus_y_tine_flange': 'model.tub_print_fixes (1) (T2, VN-53): -Y tab-catch flange grown from the -Y wall',
    't2_minus_y_tine_fill': 'model.tub_print_fixes (1) (T2, VN-53): 50 deg fill under the -Y web outer face',
    't2_ll_insert_boss_cone': 'model.tub_print_fixes (2) (T2): cone under the LL collar insert boss',
    't2_rear_landing_wedge': 'model.tub_print_fixes (3) (T2): wedge under the rear panel-screw landing',
    't2_fps_guide_corbel': 'model.tub_print_fixes (5) (T2; FX bundle lane): corbel under the FPS pair guide',
    't2_tab_catch_ceiling': 'model.tab_catch_split (T2, VN-53): ceiling over the tab slot above the +Y tine joint',
    't2_tab_catch_pad': 'model.tab_catch_split (T2, VN-53): +Y web pad above the joint (pocket wall)',
}
COVERED_BY = ['verification.json interference (tub vs every part) and motion sweeps',
              'harness-checks.json installed_clearance / feed_volumes / member sweeps (tub in the obstacle set)',
              'fps-service-study/integrated-fps-checks.json static and carried checks (tub fixed)',
              'hdmi-checks.json installed / premate / carried sweeps (tub in the obstacle set)']
TOL_MM3 = 1e-5


def declared_additions(model, length, lens='kowa_lm6hc'):
    """-> [(id, solid)] rebuilt from model.py in model.build's layout state (J4 trial layout, collar setup)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(model.__file__).resolve().parent / 'structural-review'))
    import j4_trial_geometry as JG
    L = model.L
    with JG.trial_layout(L, lip=2.4, head=2.4):
        old_lens, L.LENS = getattr(L, 'LENS', None), lens
        oldc, olds = copy.deepcopy(L.COLLAR), copy.deepcopy(L.SCREWS)
        try:
            model.collar_setup()
            fixes, _ = model.tub_print_fixes(length)
            ll = 'LL' in L.COLLAR['bolted']
            split = model.tab_catch_split()
            seat = model.carrier_locator_seat()
        finally:
            L.COLLAR, L.SCREWS = oldc, olds
            if old_lens is not None:
                L.LENS = old_lens
    names = ['t2_minus_y_tine_flange', 't2_minus_y_tine_fill'] + (['t2_ll_insert_boss_cone'] if ll else []) + \
            ['t2_rear_landing_wedge', 't2_fps_guide_corbel']
    if len(names) != len(fixes):
        raise ValueError('model.tub_print_fixes additions changed (%d, inventory %d): update cavity_rules.INVENTORY'
                         % (len(fixes), len(names)))
    out = [('carrier_locator_seat', seat)] + list(zip(names, fixes))
    out += list(zip(['t2_tab_catch_ceiling', 't2_tab_catch_pad'], split['adds']))
    unknown = [n for n, _ in out if n not in INVENTORY]
    if unknown:
        raise ValueError('undeclared inventory ids: %s' % unknown)
    return out


def _vol(shape):
    """Volume of a Boolean result; an empty (null) result is 0."""
    try:
        return shape.Volume() if shape is not None and not shape.isNull() else 0.0
    except ValueError:
        return 0.0


def undeclared_material(new, old, cavity, declared, tol=TOL_MM3):
    """Material of `new` inside `cavity` that is neither in `old` nor in a declared addition.
    -> dict(passed, added_mm3, undeclared_mm3, undeclared_bbox, declared_inside_mm3 {id: mm3}, stale [ids])."""
    added = new.intersect(cavity).cut(old.intersect(cavity))
    total = _vol(added)
    rest = added
    inside = {}
    for name, solid in declared:
        part = solid.intersect(cavity)
        v = _vol(part)
        inside[name] = v
        if v > tol and _vol(rest) > 0.0:
            rest = rest.cut(part)
    und = _vol(rest) if not rest.isNull() and rest.Solids() else 0.0
    bb = None
    if und > tol:
        b = rest.BoundingBox()
        bb = [round(q, 3) for q in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]
    # a declared addition that is no longer in the tub is stale (declared but absent): at least half of its material
    # inside the cavity must be tub material (later bores and reliefs may cut into it)
    stale = [n for n, s in declared if inside[n] <= tol or _vol(s.intersect(cavity).intersect(new)) < 0.5 * inside[n]]
    return dict(passed=und <= tol and not stale, added_mm3=total, undeclared_mm3=und, undeclared_bbox=bb,
                declared_inside_mm3=inside, stale=stale, tol_mm3=tol)
