# SPDX-License-Identifier: MIT
"""Critical-feature registry of the vertical candidate (review 2026-10-10: VN-21, VN-25; phase-2 lane CF).

r7's checks.check_critical_features, check_joint_coverage and unclassified_thin_spots run unchanged
(verify_print_checks.py). They read their registries from the layout view print_rules.candidate_state builds; this
module supplies the candidate's registries in place of r7's, without touching r7's layout.py or checks.py:

- every r7 CRITICAL_FEATURES id is accounted for exactly once: KEEP (the r7 origin measures the same feature on the
  candidate), RENOMINATE (same id, part, min_mm and feature class; a new origin on the candidate's equivalent
  feature at its narrowest section, recorded as replaces=dict(origin, why) the way r7 layout.replace_feature does)
  or RETIRE (the feature is not built; one written reason per probe and the candidate entries that now carry its
  function, if any);
- ADDED entries cover what the candidate builds and r7 did not (the carrier, the +Y panel screws, the bonded
  tab-catch insert, the integral roof, ...). Each names an r7 feature class and an r7 analog entry and may never
  ask for less than that analog asks for (tests/test_critical_features_cf.py);
- joints follow r7's own fork rule (candidate-fr1 layout.py 'FR integrate'): a fork joint that supersedes r7 joints
  requires the union of its own ids and the superseded joints' ids minus RETIRE, and lists the superseded ids in
  `replaces`. r7's fixed REQUIRED_JOINT_IDS is not changed: the r7 check accepts a superseded id only when the fork
  joint that names it validates (all its probes measured and passing);
- r7's NONSTRUCTURAL_EXCEPTIONS are accounted for the same way (the exposure-label glyph ridge moves with the panel
  engraving; the others are retired); one candidate exception is added (carrier kit-boss lead-in rims), with the
  design numbers that give its thickness.

Origins come from the candidate model's own numbers (model.py, cited per entry); nothing is measured here. The
measured values are in out/<variant>/print-checks.json; tests pin each entry to its design value.
"""
import math

VERSION = 'cf-2026-10-11'
ADDED_LOAD_BEARING = ('carrier', 'tab_catch_insert')   # carrier: Pi/UPS stack; insert: the +Y camera tab catch
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

# ----------------------------------------------------------------------------------------------- KEEP (r7 origin)
# Verified on the bound STEPs (print-checks.json): the r7 origin lies in the same feature and measures the r7 value,
# or the candidate's declared J4 trial value (head and lip 2.4, print_rules.J4_TRIAL) where the joint was re-sized.
_TONGUE = 'J4 T-tongues unchanged in x/y (L.TONGUES); the candidate J4 trial head is 2.4 (r7 1.8), so 2.4 is measured'
KEEP = {
    **{'tub_tongue_%s_wing_%s' % (t, s): _TONGUE for t in 'fr' for s in 'lr'},
    **{'tub_tongue_%s_neck' % t: 'J4 tongue neck unchanged (8.0, as r7)' for t in 'fr'},
    **{'base_keyhole_lip_%s_%s' % (t, s): 'J4 keyhole lip over the same tongue; candidate trial lip 2.4 (r7 1.6)'
       for t in 'fr' for s in 'lr'},
    'tub_front_wall_lr_foot': 'LR compression foot unchanged at (-19, 44); the wall behind its recess is 2.5 (r7 2.5)',
    'tub_lip': 'adapter lip land x -3.9..-2.7 unchanged (model.make_tub r 16.2 / 18.75 cuts): 1.2 (r7 1.2)',
    'tub_insert_boss_tl': 'TL insert boss unchanged (feet TL (11, 90.5)): 2.0 over the dia 4.0 bore (r7 2.0)',
    'tub_insert_boss_tr': 'TR insert boss unchanged (feet TR (-11, 90.5)): 2.0 (r7 2.0)',
    'collar_foot_tl': 'collar TL foot unchanged: 2.1 round the 3.4 hole (r7 2.1)',
    'collar_foot_tr': 'collar TR foot unchanged: 2.1 (r7 2.1)',
    'collar_foot_lr': 'collar LR compression foot unchanged: 7.6 (r7 7.6)',
    'panel_cam_keeper': 'camera cover catch box(-30.67, -27.34, ...) in make_panel = the r7 keeper position: 3.33 (r7)',
    'grip_column_wall': 'grip column unchanged (L.GRIP): 2.5 (r7 2.5)',
    'base_tripod_wall': 'tripod nut pocket unchanged (tripod_nut x -113.4..-100.6): 2.3 under the nut (r7 2.3)',
    'grip_front_wall_pad_top': 'run-pad recess top unchanged: 1.75 (r7 1.75)',
    'grip_cap_lip_l': 'cap groove lip unchanged: 1.696 (r7)', 'grip_cap_lip_r': 'cap groove lip unchanged: 1.696 (r7)',
    'grip_cap_detent_arm': 'flexure unchanged: 1.5, gated G-CAP-1 (r7)',
    'grip_cap_detent_dimple_wall': 'flexure unchanged: 1.25, gated G-CAP-1 (r7)',
    'grip_cap_groove_corner': 'flexure unchanged: 1.275, gated G-CAP-1 (r7)',
    **{k: 'cap unchanged (printed_small cap, L.CAP): same value as r7' for k in
       ('cap_key_web_l', 'cap_key_web_r', 'cap_key_head_root', 'cap_key_head_tip', 'cap_detent_bump', 'cap_floor')},
}

# ----------------------------------------------------------------------------------------------- RETIRE
_HOOD = ('the r7 hood does not exist: its roof is integral to the tub (model.make_tub: one solid, roof z 97.5..100), '
         'so there is no hood hook, tooth, catch ledge or groove; the roof is probed by JV1_integral_roof')
_KEEPER = ('the r7 Pi keeper and the floor-mounted stack are gone: the Pi/UPS stack hangs on the printed carrier '
           '(4 kit screws, 2 PT ear screws into tub bosses, bottom-rail tongue on a tub seat under a panel stop); '
           'probed by JV9_carrier')
_SB = ('s_b1 / s_b2 are not built (model.make_base_grip drops them; the 4 p_panel screws close the panel from +Y)')
_SR = ('the r7 right-wall screws s_r1 / s_r2 are replaced by the 4 p_panel screws driven from +Y: their heads seat '
       'on the panel boss floors and their pilots are in tub bosses (JV3_panel_screws)')
_CARRIER = ('carrier_kit_boss_a_head_floor', 'carrier_kit_boss_b_head_floor', 'carrier_kit_boss_c_head_floor',
            'carrier_kit_boss_d_head_floor', 'carrier_ear_c1_head_floor', 'carrier_ear_c2_head_floor',
            'tub_carrier_boss_c1', 'tub_carrier_boss_c2', 'carrier_locator_tongue', 'tub_locator_seat',
            'panel_locator_stop')
_PANEL = tuple('panel_boss_p%d_head_floor' % i for i in range(1, 5)) + tuple('tub_panel_boss_p%d' % i for i in range(1, 5))
RETIRE = {
    **{'hood_hook_hk%d' % i: (_HOOD, ()) for i in range(1, 5)},
    **{'hood_tooth_hk%d' % i: (_HOOD, ()) for i in range(1, 5)},
    **{'tub_ledge_hk%d' % i: (_HOOD + ' (no ledge: probe origin lies in the tub cavity)', ()) for i in range(1, 5)},
    'hood_band': (_HOOD + '; the band function is the tub roof plate', ('tub_roof_plate',)),
    'hood_groove_lower_lip': (_HOOD + '; the panel top edge is screwed (p_panel2, p_panel4 at z 91.7)',
                              ('panel_boss_p2_head_floor', 'panel_boss_p4_head_floor')),
    'panel_tongue': ('no top tongue: the candidate panel is a flat 2.8 plate whose top edge is held by p_panel2 and '
                     'p_panel4 (model.make_panel)', ('panel_boss_p2_head_floor', 'panel_boss_p4_head_floor')),
    'panel_tongue_tooth': ('no top tongue tooth (flat panel; top edge screwed)',
                           ('panel_boss_p2_head_floor', 'panel_boss_p4_head_floor')),
    'panel_end_land_front': ('no R5 end corner or end land: the flat panel sits in the tub opening (0.3 seam) and '
                             'seats in -Y on the 4 boss faces at y 23.5', _PANEL),
    'panel_end_land_rear': ('no R5 end corner or end land (flat panel); the rear-bottom corner bears on the tub '
                            'compression landing', _PANEL + ('tub_panel_landing_rear',)),
    'panel_locate_rib_f': ('no locating ribs: X/Z location is the 4 p_panel screws in 3.4 holes plus the 0.3 seam',
                           _PANEL),
    'panel_locate_rib_r': ('no locating ribs (as panel_locate_rib_f)', _PANEL),
    'panel_boss_b1_wall': (_SB + '; the r7 origin now lies in the plain panel plate', _PANEL),
    'panel_boss_b2_wall': (_SB + '; the r7 origin now lies in the plain panel plate', _PANEL),
    'panel_boss_b1_cap': (_SB + '; the r7 origin now gives a 93.8 chord along the plate (not a boss cap)', _PANEL),
    'panel_boss_b2_cap': (_SB + '; the r7 origin now gives a 90.5 chord along the plate (not a boss cap)', _PANEL),
    'base_sb1_head_floor': (_SB, _PANEL), 'base_sb2_head_floor': (_SB, _PANEL),
    'panel_post_f_wall': (_SR, _PANEL),
    'tub_pad_pad_r1_under_head': (_SR, _PANEL), 'tub_pad_pad_r2_under_head': (_SR, _PANEL),
    **{k: (_KEEPER, _CARRIER) for k in ('keeper_finger_kf1', 'keeper_finger_kf2', 'keeper_finger_kf3',
                                        'keeper_finger_kf4', 'keeper_arm', 'keeper_bridge', 'keeper_bar',
                                        'tub_keeper_boss_s_k1', 'tub_keeper_boss_s_k2', 'tub_keeper_boss_s_k2_seam')},
    **{'tub_pi_boss_%d' % i: (_KEEPER + '; no Pi floor boss (r7 origins of 0 / 2 now meet unrelated tub material, 1.658 / 3.0; 1 / 3 meet nothing)', _CARRIER)
       for i in range(4)},
    'hood_stack_post': (_HOOD + '; no far-side stack post: the stack is held by the carrier', _CARRIER),
    **{'hood_foot_hole_%s' % k: ('no hood plate: the collar feet pass no plate and bear in recesses cut into the tub '
                                 'front plate (model.make_tub r 4.3, x -2.7..0.1)', ('tub_foot_recess_%s' % k,))
       for k in ('tl', 'tr', 'll', 'lr')},
    'hood_tab_catch_p': ('no hood: the +Y tine is the bonded tab_catch_insert (model.tab_catch_split, T2)',
                         ('insert_tab_catch_p', 'insert_tab_catch_tenon')),
    'hood_tab_catch_n': ('no hood: the -Y tine is integral to the tub (grown to the roof, T2 fill)',
                         ('tub_tab_catch_n',)),
    'tub_rib_l_tip': ('no rib_l gusset: make_tub adds no RIBS; the front wall is the full-height plate x -5.2..0 '
                      '(a ray at y 26, z 20 meets only the x -2.8..0 frame beside the panel pocket)', ()),
    'tub_evf_groove_wall_bot_mx': ('not built: model.evf_support cuts the bottom-rail -X groove wall above the shelf '
                                   'over the whole groove (box x rx0-0.1..xc-g, y -3.65..23.6, z 63.75..65.35); the '
                                   'board -X arrest is the top-rail -X wall (tub_evf_groove_wall_top_mx) and the '
                                   'direction is checked by check_scope evf_restraint', ()),
}

# r7 NONSTRUCTURAL_EXCEPTIONS: none matches a candidate thin-wall sample; a retired one can only make a sample stricter
EXCEPTION_RETIRE = {
    'antirot_slot_skin': 'the candidate 18/24 anti-rotation slot is a through cut (make_panel cyl r 1.7 through the '
                         'plate): no skin',
    'badge_glyph_ridge': 'make_panel does not engrave the badge',
    'exposure_label_glyph_ridge_2': 'merged into the re-nominated exposure_label_glyph_ridge, whose points span the '
                                    'whole moved label',
    'plunger_channel_vent_web': 'hood part removed',
    'stick_rail_lip_tip': 'no candidate thin-wall sample within 2.5 mm of the r7 stick-rail points',
}

# model.make_carrier tie slots (3 x 1 through the rails); harness_rules.TIE_SLOTS_XZ holds the same list (tested)
CARRIER_TIE_SLOTS = ((-92.0, 25.0), (-92.0, 45.0), (-35.0, 25.0), (-34.0, 45.0))   # = model.CARRIER_TIE_SLOTS
CARRIER_TIE_SLOT_HALF_X = 1.5


def _unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def renominations(L, model, length, collar, lens_spec):
    """{r7 id: dict(origin, direction, span, why)}: the candidate's equivalent feature at its narrowest section."""
    f, ey = -length, model.EY
    fe, lug, j = collar['feet'], collar['lug'], L.J4_LOCK
    enc = model.CONTROL_MOVES['encoder']
    strap = model.candidate_strap_layout()
    xc, g, w = f + 16.4, 1.05, 1.3          # model.evf_support: PCB groove centre, half width, groove-wall thickness
    gy0 = -15.3 + ey                         # model.evf_support: groove -Y end (board -Y arrest), +EY in y
    evf_why = 'EVF moved with the candidate core (F -154 -> %g, axis y 16 -> %g; model.evf_support)' % (f, ey)
    out = {}

    def R(fid, origin, direction=None, span=None, why=''):
        out[fid] = dict(origin=tuple(round(float(v), 4) for v in origin), direction=direction, span=span, why=why)

    R('tub_front_wall_seat', (L.X_FW_IN + L.T / 2, fe['TL'][0], fe['TL'][1] - (4.0 + 4.3) / 2), X,
      why='the r7 origin (r 4.5 from the TL axis) lies outside the candidate foot recess (r 4.3) and gives the full '
          '5.2 front plate; the boss-root section is the annulus between the boss (r 4.0) and the recess, where the '
          'wall behind the recess is 2.5 as in r7')
    R('tub_j4_lock_boss', (j['c'][0] + L.PT['pilot_d'] / 2 + 1.0, j['c'][1], 8.0), X,
      why='J4 lock moved to y %g (r7 -20); the r7 origin measured 6.928 beside the boss' % j['c'][1])
    R('tub_insert_boss_ll', (-6.3, fe['LL'][0] + 3.0, fe['LL'][1]), Y,
      why='LL foot moved (28, 36) -> (%g, %g) (model.collar_setup); +Y side, the thinnest (the -Y side merges with '
          'the T2 boss cone)' % fe['LL'])
    R('tub_evf_groove_wall_bot_px', (xc + g + w / 2, 19.0, 64.5), X, (5, 2.0, Y),
      why=evf_why + '; bottom +X wall beyond the plug-gap thickening (y 14.65..23.5), its thinnest stretch; r7 '
                    'EXPECT_OUTSIDE (5 V relief) has no candidate counterpart')
    R('tub_evf_groove_wall_top_mx', (xc - g - w / 2, gy0 + 11.3, 92.0), X, (5, 5.0, Y), why=evf_why)
    R('tub_evf_groove_wall_top_px', (xc + g + w / 2, gy0 + 11.3, 92.0), X, (5, 5.0, Y), why=evf_why)
    R('tub_evf_groove_floor_bot', (f + (15.85 + 17.19) / 2, gy0 + 13.3, 62.5), Z, (5, 6.0, Y),
      why=evf_why + '; shelf under the PCB between the VN-34 relief (x <= f+15.85) and the +X relief (x >= f+17.19), '
                    'spanning the groove')
    R('tub_evf_groove_roof_top', (xc, gy0 + 11.3, 93.4), Z, (5, 5.0, Y), why=evf_why)
    R('tub_evf_groove_end_bot', (xc, gy0 - 0.5, 64.5), Y, why=evf_why)
    R('tub_evf_groove_end_top', (xc, gy0 - 0.5, 92.0), Y, why=evf_why)
    R('tub_evf_collar_radial', (f + 3.425, ey - 15.6, 78.0), Y,
      why=evf_why + '; same place relative to the bore as r7 (x mid of the half collar f+2.45..f+4.4)')
    R('tub_evf_collar_axial', (f + 2.0, ey - 15.6, 78.0), X, why=evf_why)
    R('panel_wall', (-80.0, model.PANEL_IN + 1.4, 30.0), Y, why='flat panel plate y 25.2..28.0 (make_panel)')
    R('panel_evf_clamp_prong', (f + 4.2, ey + 8.0 + 0.3, 64.0), Z,
      why=evf_why + '; lower prong 0.3 in from its -Y tip (clamp y0 = EY + 8), as r7')
    R('panel_evf_stop', (xc, ey + 12.3 + 1.2, 78.0), X, (5, 3.0, Z), why=evf_why + '; stop rib y EY+12.3..25.6')
    for k in ('side_l', 'side_r', 'top', 'tooth_top', 'tooth_left', 'tooth_right'):
        fid = 'panel_encoder_hook_' + k
        o = L_origin(L, fid)
        R(fid, tuple(o[i] + enc[i] for i in range(3)), None,
          why='encoder cradle moved by CONTROL_MOVES encoder %s, geometry unchanged (make_panel)' % (enc,))
    hole = collar['hole_d'] / 2
    R('collar_foot_ll', (-1.2, fe['LL'][0], fe['LL'][1] + (hole + collar['foot_d'] / 2) / 2), Z,
      why='LL foot moved to (%g, %g); same section (wall round the 3.4 hole)' % fe['LL'])
    R('collar_lug_upper', (lug['screw_x'], lug['y_out'] + 0.85, 63.5), Y,
      why='lug face moved to y %g (C2, r7 spacing)' % lug['y_out'])
    R('collar_lug_lower', (lug['screw_x'], lug['y_out'] + 0.85, 53.0), Y,
      why='lug face moved to y %g (C2, r7 spacing)' % lug['y_out'])
    ax = L.LENS_AXIS
    tgt = (lug['bit_relief_y'] - ax[0], lug['upper_z'][1] + 0.05 - ax[1])
    rr = math.hypot(*tgt)
    d = _unit((0.0,) + tgt)
    rm = (lens_spec['bore_r'] + rr) / 2
    R('collar_wall_min', (4.0, ax[0] + d[1] * rm, ax[1] + d[2] * rm), d,
      why='candidate body r 25 (r7 30): the thinnest ring section is the ligament from the bore (r %g) to the s_c4 '
          'bit-relief corner (y %g, z %g); the r7 origin (r 26 under the bore) lies outside the r 25 body, in the '
          'outline toward the LL ear (chord 6.516)' % (
              lens_spec['bore_r'], lug['bit_relief_y'], lug['upper_z'][1]))
    us = strap['upper_slots']
    bx = (max(s['x'][0] for s in us) + min(s['x'][1] for s in us)) / 2
    by = (us[0]['y'][0] + us[0]['y'][1]) / 2
    R('base_strap_bridge', (bx, by, -4.0), X, why='candidate strap slots (model.candidate_strap_layout): bridge x %g' % bx)
    R('base_strap_web', (bx, by, -5.0), X, (5, 2.5, Y), why='as base_strap_bridge')
    R('base_sj_head_floor', (j['c'][0] + 2.6, j['c'][1], -1.0), Z,
      why='s_j moved with the J4 lock to y %g' % j['c'][1])
    ls = strap['lower_slots']
    hx = (ls[0]['x'][0] + ls[0]['x'][1]) / 2
    hz = (max(s['z'][0] for s in ls) + min(s['z'][1] for s in ls)) / 2
    heel = ('the heel doubler makes the bar 5.5 deep in x (r7 2.5): its narrowest section is now the 3.5 height '
            'between the lower slots, measured along z')
    R('grip_strap_bar', (hx, -3.0, hz), Z, (3, 2.0, Y), why=heel)
    R('grip_heel_slot_end', (hx, ls[0]['y'][0] + 0.5, hz), Z, why=heel + ' (at the -Y slot end)')
    return out


def L_origin(L, fid):
    """The r7 origin of an r7 CRITICAL_FEATURES id, with r7 registry semantics (last entry wins); KeyError if none."""
    hit = [it for it in L.CRITICAL_FEATURES if it['id'] == fid]
    if not hit:
        raise KeyError(fid)
    return tuple(float(v) for v in hit[-1]['origin'])


def added(L, model, length, collar):
    """New candidate entries: dict(id, part, origin, direction, span?, min_mm, cls, analog, note). `analog` is the r7
    entry whose requirement the entry may not undercut (tests compare the graded minima)."""
    f, ey, fe = -length, model.EY, collar['feet']
    ax = L.LENS_AXIS
    out = []

    def A(fid, part, origin, direction, min_mm, cls, analog, note, span=None):
        e = dict(id=fid, part=part, origin=tuple(round(float(v), 4) for v in origin), direction=direction,
                 min_mm=min_mm, cls=cls, structural=True, analog=analog, note=note)
        if span:
            e['span'] = span
        out.append(e)

    pt_wall = (L.PT['boss_od_min'] - L.PT['pilot_d']) / 2          # r7 PT boss rule (tub_keeper_boss, tub_j4_lock_boss)
    # JV1 integral roof (replaces J1): roof plate z 97.5..100 and the two walls that carry it (make_tub outer box)
    A('tub_roof_plate', 'tub', (-80.0, 0.0, 98.75), Z, 1.2, 'wall', 'hood_band', 'integral roof plate (the r7 hood band)')
    A('tub_wall_minus_y', 'tub', (-120.0, -26.75, 70.0), Y, 1.2, 'wall', 'hood_band', '-Y wall under the roof (y -28..-25.5)')
    A('tub_wall_rear', 'tub', (f + 1.25, -10.0, 55.0), X, 1.2, 'wall', 'hood_band', 'rear wall under the roof (x f..f+2.5)')
    # JV3 panel screws (replaces J3 and J2): 4 PT screws from +Y, heads on panel boss floors, pilots in tub bosses
    for i, (x, z) in enumerate(model.panel_screws(length), 1):
        A('panel_boss_p%d_head_floor' % i, 'panel', (x + (1.7 + 3.5) / 2, (23.5 + 25.6) / 2, z), Y, 1.6, 'boss',
          'base_sj_head_floor', 'p_panel%d head floor: boss y 23.5 to the counterbore floor y 25.6 (make_panel)' % i)
        A('tub_panel_boss_p%d' % i, 'tub', (x + L.PT['pilot_d'] / 2 + 1.0, 18.0, z), X, pt_wall, 'boss',
          'tub_keeper_boss_s_k1', 'p_panel%d PT boss wall round the 2.5 pilot (make_tub r 4.5)' % i)
    A('tub_panel_landing_rear', 'tub', (f + 8.5, 23.2, 4.0), Y, 1.2, 'land', 'panel_end_land_rear',
      'compression landing under the panel rear-bottom corner (make_tub box f+6..f+11, y 21.5..24.9, T2 wedge)')
    # JV9 carrier (replaces J9_pi_keeper and J9_stack_stop)
    for k, (hx, hy) in zip('abcd', L.PI['holes']):
        x, _, z = model.rp((hx, hy, 6))
        A('carrier_kit_boss_%s_head_floor' % k, 'carrier', (x + (1.4 + 2.65) / 2, (16.2 + 19.2) / 2, z), Y, 1.6,
          'boss', 'base_sj_head_floor', 'kit-screw head floor: boss y 16.2 to the head pocket floor y 19.2 '
          '(make_carrier: the stack hangs here)')
    for i, (x, z) in enumerate(model.CARRIER_SCREWS, 1):
        A('carrier_ear_c%d_head_floor' % i, 'carrier', (x + (1.7 + model.CARRIER_CBORE_R) / 2, (17.2 + 19.8) / 2, z),
          Y, 1.6, 'boss', 'base_sj_head_floor', 'p_carrier%d head floor: ear y 17.2 to the counterbore floor y 19.8' % i)
        A('tub_carrier_boss_c%d' % i, 'tub', (x + L.PT['pilot_d'] / 2 + 1.0, 12.0, z), X, pt_wall, 'boss',
          'tub_keeper_boss_s_k1', 'p_carrier%d PT boss wall round the 2.5 pilot (make_tub r 4.8)' % i)
    A('carrier_arm', 'carrier', (-110.0, 19.7, 61.0), _unit((16.0, 0.0, 34.0)), 1.6, 'bar', 'keeper_arm',
      'diagonal arm (-127, 69) -> (-93, 53), 8.0 across (make_carrier + structure_geometry.carrier_arm_addition)')
    for i, (sx, sz) in enumerate(CARRIER_TIE_SLOTS, 1):
        side = -1 if sx < -60 else 1                       # outer ligament: -X on the left rail, +X on the right rail
        A('carrier_tie_bar_%d' % i, 'carrier', (sx + side * (CARRIER_TIE_SLOT_HALF_X + 0.3), 20.1, sz), X, 1.6, 'bar',
          'base_strap_bridge', 'cable-tie bar outside the tie slot (%g, %g), through the plate depth' % (sx, sz),
          span=(3, 1.9, Y))
    lx, st = model.LOCATOR_X, model.LOCATOR_SEAT_TOP
    A('carrier_locator_tongue', 'carrier', (lx, 19.7, (4.0 + st) / 2), Y, 1.6, 'lug', 'panel_evf_stop',
      'bottom-rail tongue on the tub seat (FP-11c, VN-38)')
    A('tub_locator_seat', 'tub', (lx, 16.2, st - 0.5), Y, 1.6, 'lug', 'panel_evf_stop',
      'tub floor seat rib under the carrier tongue, 0.5 under its top (model.carrier_locator_seat)')
    A('panel_locator_stop', 'panel', (lx, model.CARRIER_BED_Y + model.LOCATOR_STOP_GAP + 1.15, 6.0), Y, 1.6, 'lug',
      'panel_evf_stop', 'panel stop pad over the carrier tongue (model.carrier_locator_stop)')
    # J7 additions: front-plate material round the collar-foot recesses (the r7 hood plate) and the tab-catch tines
    for k in ('TL', 'TR'):
        y, z = fe[k]
        A('tub_foot_recess_%s' % k.lower(), 'tub', (L.XT1 / 2, y, (z + 4.3 + 100.0) / 2), Z, 1.2, 'land',
          'hood_foot_hole_%s' % k.lower(), 'front plate above the %s recess (r 4.3) to the roof top' % k)
    y, z = fe['LL']
    A('tub_foot_recess_ll', 'tub', (L.XT1 / 2, (y + 4.3 + 28.0) / 2, z), Y, 1.2, 'land', 'hood_foot_hole_ll',
      'front plate +Y of the LL recess to the tub +Y face (y 28)')
    y, z = fe['LR']
    d = _unit((0.0, y - ax[0], z - ax[1]))
    rm = (18.25 + math.hypot(y - ax[0], z - ax[1]) - 4.3) / 2
    A('tub_foot_recess_lr', 'tub', (L.XT1 / 2, ax[0] + d[1] * rm, ax[1] + d[2] * rm), d, 1.2, 'land',
      'hood_foot_hole_lr', 'front-plate web between the lens bore (r 18.25) and the LR recess')
    tc = {(b['side'], b['kind']): b for b in L.tab_catch_boxes()}
    for sg, part, fid in ((-1, 'tub', 'tub_tab_catch_n'), (1, 'tab_catch_insert', 'insert_tab_catch_p')):
        web = tc[(sg, 'web')]
        A(fid, part, ((web['x'][0] + web['x'][1]) / 2, sum(web['y']) / 2, (web['z'][0] + model.TAB_CATCH_SPLIT_Z) / 2),
          Y, 2.4, 'wing', 'hood_tab_catch_%s' % ('n' if sg < 0 else 'p'),
          'camera tab-catch tine web below the T2 joint plane (%s)' % part)
    tn, yin = model.TAB_CATCH_TENON, tc[(1, 'web')]['y'][0]
    A('insert_tab_catch_tenon', 'tab_catch_insert', (sum(tn['x']) / 2, yin + tn['t'] / 2,
                                                    model.TAB_CATCH_SPLIT_Z + tn['h'] / 2), Y, 1.6, 'lug',
      'hood_tooth_hk1', 'tenon that locates the bonded +Y stub on the ceiling datum (shear while the tab bears)')
    # FX (verifier T2 major): the tenon pocket's side walls exist only in the tub PRINT STOCK (the bonded tub STEP fills
    # the pocket as adhesive), so they are probed on print_rules.TUB_STOCK. They locate the tenon in x; the catch load
    # uses the dry -Y datum/axial-stop bearing and unqualified clearanced-face bonding; no joint-plane adhesive
    # strength is credited. The class is the wall floor (r7 MIN_WALL 1.2, analog the
    # tub walls of JV1). The 9ced753..d848d413 tenon (x -13.5..-9.2) left 0.9 here.
    wp, C = tc[(1, 'web')], model.TAB_CATCH_POCKET_CLEAR
    px0, px1 = tn['x'][0] - C['x'], tn['x'][1] + C['x']
    pz = model.TAB_CATCH_SPLIT_Z + (tn['h'] + C['z']) / 2
    py = yin + (tn['t'] + C['y']) / 2
    # Review 2026-10-12 (corrective, check-integrity): with the 10 mm tenon the mid-height origin of the +X wall lies in
    # the panel-screw boss column (chord 7.0 to x -2.7), so one ray no longer sees the 1.5 mm wall near the joint plane.
    # Both walls are graded as the minimum of 11 rays along z over the pocket face (0.25 inside each pocket end).
    wspan = (11, round((tn['h'] + C['z'] - 0.5) / 10, 4), Z)
    A('tub_stock_tenon_pocket_wall_xm', 'tub_print_stock', ((wp['x'][0] + px0) / 2, py, pz), X, 1.2, 'wall', 'hood_band',
      'tub print stock: -X side wall of the bonded-stub tenon pocket (web x %.2f..%.2f, pocket from %.2f); minimum '
      'over the pocket height' % (wp['x'][0], wp['x'][1], px0), span=wspan)
    A('tub_stock_tenon_pocket_wall_xp', 'tub_print_stock', ((px1 + wp['x'][1]) / 2, py, pz), X, 1.2, 'wall', 'hood_band',
      'tub print stock: +X side wall of the bonded-stub tenon pocket (pocket to %.2f, web to %.2f); minimum over the '
      'pocket height (the boss column above the thin wall is wider)' % (px1, wp['x'][1]), span=wspan)
    vent_y=yin+tn['t']+C['y']+model.TAB_CATCH_VENT['depth']
    wall_y=wp['y'][1]+1.2
    A('tub_stock_vent_wall_y', 'tub_print_stock', (sum(tn['x'])/2,(vent_y+wall_y)/2,
      model.TAB_CATCH_SPLIT_Z+(tn['h']+C['z']+.5)/2), Y, 1.2, 'wall', 'hood_band',
      'remaining +Y host wall behind the adhesive escape groove; eleven height probes above intentional outlet',
      span=(11,(tn['h']+C['z']-.9)/10,Z))
    end_z=model.TAB_CATCH_SPLIT_Z+tn['h']+C['z']
    A('tub_stock_tenon_end_floor', 'tub_print_stock', (sum(tn['x'])/2,yin+tn['t']/2,
      (end_z+model.TAB_CATCH_CEILING_TOP)/2), Z, 1.2, 'wall', 'hood_band',
      'blind pocket end floor; escape groove must not perforate the ceiling')
    # J8 additions
    r0, r1 = model.EVF_HDMI_RECEPTACLE_Y
    A('tub_evf_floor_relief', 'tub', (f + 15.65, ((r0 - 16 + ey - 0.5) + (r1 - 16 + ey + 0.5)) / 2, (61.5 + 62.9) / 2),
      Z, 1.2, 'wall', 'tub_evf_groove_floor_bot', 'shelf under the VN-34 receptacle relief (T2, z 61.5..62.9)')
    A('tub_evf_collar_ring_end', 'tub', (f + 3.425, ey - 1.5, 93.8), Z, 1.6, 'lug', 'tub_evf_collar_radial',
      'eyepiece half collar at its +Y ring end over the bore (its narrowest section)', span=(3, 1.0, Y))
    return out


# ----------------------------------------------------------------------------------------------- joints
FORK_JOINTS = [
    dict(id='JV1_integral_roof', supersedes=['J1_hood_hooks'], parts=['tub'],
         required=['tub_roof_plate', 'tub_wall_minus_y', 'tub_wall_rear'],
         note='the r7 hood is merged into the tub (one printed solid): hood retention becomes material continuity of '
              'the roof plate and the walls that carry it'),
    dict(id='JV3_panel_screws', supersedes=['J3_panel_tub', 'J2_panel_tongue'], parts=['panel', 'tub'],
         required=list(_PANEL) + ['tub_panel_landing_rear'],
         note='flat panel closure: 4 PT screws from +Y (heads on the panel boss floors, pilots in tub bosses; the panel '
              'seats on the boss faces at y 23.5), rear-bottom compression landing; the top edge is screwed (no J2 '
              'tongue)'),
    dict(id='JV9_carrier', supersedes=['J9_pi_keeper', 'J9_stack_stop'], parts=['carrier', 'tub', 'panel'],
         required=list(_CARRIER) + ['carrier_arm'],
         note='Pi/UPS stack on the printed carrier: 4 kit screws into the carrier kit bosses, 2 PT ear screws into tub '
              'bosses, bottom-rail tongue on the tub seat rib under the panel stop pad (FP-11c, VN-38)'),
]
NEW_JOINTS = [   # candidate joints with no r7 counterpart
    dict(id='JV9_carrier_ties', parts=['carrier'], required=['carrier_tie_bar_%d' % i for i in range(1, 5)],
         note='cable-tie bars outside the 4 carrier tie slots (harness_rules.TIE_SLOTS_XZ; the pigtail ties, user '
              'decision 6 pending)'),
]
JOINT_ADDITIONS = {   # kept r7 joints: candidate parts and probes that join them
    'J7_camera': dict(parts=['tab_catch_insert', 'tub_print_stock'],
                      required=['tub_foot_recess_tl', 'tub_foot_recess_tr', 'tub_foot_recess_ll', 'tub_foot_recess_lr',
                                'tub_tab_catch_n', 'insert_tab_catch_p', 'insert_tab_catch_tenon',
                                'tub_stock_tenon_pocket_wall_xm', 'tub_stock_tenon_pocket_wall_xp']),
    'J8_evf': dict(parts=[], required=['tub_evf_floor_relief', 'tub_evf_collar_ring_end']),
}


def joints(CK, L):
    """Candidate CRITICAL_JOINTS: kept r7 joints minus RETIRE plus JOINT_ADDITIONS, fork joints (union rule), new."""
    r7j = {j['id']: j for j in CK.registry(L, 'CRITICAL_JOINTS')}
    gone = set(RETIRE)
    sup = {s: fj['id'] for fj in FORK_JOINTS for s in fj['supersedes']}
    unknown = sorted((set(sup) | set(JOINT_ADDITIONS)) - set(r7j))
    if unknown:
        raise ValueError('fork joints name r7 joints that do not exist: %s' % unknown)
    out = []
    for jid, j in r7j.items():
        if jid in sup:
            continue
        n = dict(j, parts=list(j['parts']), required=[i for i in j['required'] if i not in gone])
        a = JOINT_ADDITIONS.get(jid)
        if a:
            n['parts'] += [p for p in a['parts'] if p not in n['parts']]
            n['required'] += [i for i in a['required'] if i not in n['required']]
            n['note'] = j.get('note', '') + ' [candidate: + %s]' % ', '.join(a['required'])
        out.append(n)
    for fj in FORK_JOINTS:
        req = list(fj['required'])
        parts = list(fj['parts'])
        for s in fj['supersedes']:
            req += [i for i in r7j[s]['required'] if i not in gone and i not in req]
            parts += [p for p in r7j[s]['parts'] if p not in parts]
        out.append(dict(id=fj['id'], parts=parts, required=req, replaces=list(fj['supersedes']),
                        supersedes=list(fj['supersedes']),
                        note=fj['note'] + ' [fork joint: supersedes %s]' % ', '.join(fj['supersedes'])))
    out += [dict(j) for j in NEW_JOINTS]
    return out


# ----------------------------------------------------------------------------------------------- exceptions
KIT_BOSS = dict(r=4.5, pocket_r=2.65, rim_mm=round(4.5 - 0.6 - 2.65, 3))   # model.make_carrier (FX: no lead-in)
RETIRED_EXCEPTIONS = {'kit_boss_lead_in_rim': 'FX: the r 3.35 lead-in is gone; rim 1.25 mm at the carrier bed face'}


EXCEPTION_RENOMINATE = ('exposure_label_glyph_ridge',)
PANEL_ENGRAVE_SHIFT = (8.0, 21.0)     # model.make_panel: ENGRAVE items at (x + 8, z + 21), face_y 25 then +3 y -> 28


def exposure_label_exception(L):
    """r7 exposure_label_glyph_ridge, moved with the candidate panel engraving; points span the whole label."""
    it = next(i for i in L.ENGRAVE['items'] if i['id'] == 'exp_lbl')
    x0, z0 = it['at'][0] + PANEL_ENGRAVE_SHIFT[0], it['at'][1] + PANEL_ENGRAVE_SHIFT[1]
    pts = [(round(x0 + dx, 3), 27.8, z0) for dx in [-10.0 + 2.5 * k for k in range(9)]]
    return dict(part='panel', id='exposure_label_glyph_ridge', measured_mm=0.159, at=(-57.53, 27.81, 57.45),
                also_at=pts,
                why='face material between engraved strokes of the "exposure" label (0.4 deep, paint-filled), as r7; '
                    'decoration, no load. Fresh chord along z 0.159 at (-57.53, 27.81, 57.45) on the dbea5ca5 panel '
                    '(FX; the thin-wall sampler found 0.233 there on d848d413 and no sample on dbea5ca5, whose bed-face '
                    'chamfer changed the mesh); the label is centred at (%g, %g) on the panel face y 28 (r7 item exp_lbl '
                    'moved by make_panel +8 x, +21 z), points every 2.5 mm along it.' % (x0, z0))


def exceptions(CK, L, model):
    r7e = {e['id'] for e in CK.registry(L, 'NONSTRUCTURAL_EXCEPTIONS')}
    acc = set(EXCEPTION_RETIRE) | set(EXCEPTION_RENOMINATE)
    if r7e != acc or set(EXCEPTION_RETIRE) & set(EXCEPTION_RENOMINATE):
        raise ValueError('r7 NONSTRUCTURAL_EXCEPTIONS not accounted for: %s' % sorted(r7e ^ acc))
    # FX (verifier CF minor): the kit_boss_lead_in_rim exception is retired with its geometry: model.make_carrier no
    # longer cuts the r 3.35 x 0.7 lead-in, so the kit-boss rim at the bed face is r 4.5 - 0.6 bed chamfer - r 2.65 pocket
    # = 1.25 (KIT_BOSS rim_mm), above r7 MIN_WALL, and no thin-wall sample there needs an exception.
    return [exposure_label_exception(L)]


# ----------------------------------------------------------------------------------------------- build
def build(CK, L, model, length, collar, lens_spec):
    """-> dict(layout: registry overrides for print_rules.LayoutView, record: the accounting written to the report)."""
    r7 = {f['id']: f for f in CK.registry(L, 'CRITICAL_FEATURES')}
    ren = renominations(L, model, length, collar, lens_spec)
    add = added(L, model, length, collar)
    groups = dict(keep=set(KEEP), renominate=set(ren), retire=set(RETIRE))
    seen = [i for g in groups.values() for i in g]
    dup = sorted({i for i in seen if seen.count(i) > 1})
    missing, extra = sorted(set(r7) - set(seen)), sorted(set(seen) - set(r7))
    clash = sorted({e['id'] for e in add} & set(r7))
    if dup or missing or extra or clash:
        raise ValueError('critical-feature accounting: duplicate %s, unaccounted r7 %s, unknown %s, added clash %s'
                         % (dup, missing, extra, clash))
    feats = []
    for fid, e in r7.items():
        if fid in RETIRE:
            continue
        n = dict(e)
        if fid in ren:
            r = ren[fid]
            rep = dict(origin=tuple(e['origin']), why='candidate (CF): ' + r['why'])
            if e.get('replaces'):
                rep['r7_replaces'] = e['replaces']          # keep r7's own replace_feature record
            n.update(origin=r['origin'], replaces=rep)
            if r['direction'] is not None:
                n['direction'] = tuple(r['direction'])
            if r['span'] is not None:
                n['span'] = r['span']
        feats.append(n)
    feats += [dict(e) for e in add]
    layout = dict(CRITICAL_FEATURES=feats, CRITICAL_JOINTS=joints(CK, L),
                  NONSTRUCTURAL_EXCEPTIONS=exceptions(CK, L, model), EXPECT_OUTSIDE={})
    record = dict(version=VERSION, source='candidate-vertical/critical_features_vertical.py',
                  r7_entries=len(r7), keep=dict(sorted(KEEP.items())),
                  renominate={k: dict(r7_origin=list(r7[k]['origin']), origin=list(v['origin']), why=v['why'])
                              for k, v in sorted(ren.items())},
                  retire={k: dict(r7_origin=list(r7[k]['origin']), part=r7[k]['part'], why=v[0],
                                  superseded_by=list(v[1])) for k, v in sorted(RETIRE.items())},
                  added={e['id']: dict(part=e['part'], cls=e['cls'], min_mm=e['min_mm'], analog=e['analog'])
                         for e in add},
                  fork_joints={fj['id']: fj['supersedes'] for fj in FORK_JOINTS},
                  new_joints=[j['id'] for j in NEW_JOINTS], joint_additions=JOINT_ADDITIONS,
                  exceptions_retired=dict(sorted(EXCEPTION_RETIRE.items())),
                  exceptions_renominated=list(EXCEPTION_RENOMINATE),
                  expect_outside_retired={'tub_evf_groove_wall_bot_px': 'r7 offset -0.5 lay in the r7 5 V relief; the '
                                          'candidate bottom rail has none and the entry is re-nominated'},
                  load_bearing_added=list(ADDED_LOAD_BEARING))
    return dict(layout=layout, record=record)
