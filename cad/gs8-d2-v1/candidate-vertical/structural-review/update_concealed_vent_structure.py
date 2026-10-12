"""Manifest-bound mass/load sensitivity; no FEA or qualification.
Allowed upper-row changes use the export18 transfer. Allowed lower-row changes
require a new free body from manifest-bound STEP centres (or their bound cache).
Refuse all other changed rows; report geometry and physical evidence separately.
"""
import sys as _cvsys; _cvsys.path.append(str(__import__('pathlib').Path(__file__).resolve().parents[1]))  # candidate-vertical root: cv_io
from cv_io import read_text, rel_posix, write_text
import evidence_rules as ER  # FP-04: numeric row tolerance (VN-06) and the inherited gate count from its source (VN-08)
from pathlib import Path
import argparse, hashlib, json, math
P=Path(__file__).resolve().parent; C=P.parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def canonical_zero(value):
    """Serialize numerical zero consistently across OCC platforms, without rounding useful values.

    This changes only magnitudes below 1e-12, long below the unchanged engineering
    tolerances; geometry/hash identities and all nonzero loads remain strict.
    """
    if isinstance(value, float):
        return 0.0 if abs(value) < 1e-12 else value
    if isinstance(value, dict):
        return {k: canonical_zero(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_zero(v) for v in value]
    return value
# FP-11c (VN-54/56/38): the carrier row may change too. It is upper-body (not a J4 lower row), so the first-moment
# transfer below still holds; its mass change is carrier payload, so the retained reinforced-arm screen scales with it.
# FX (verifier C2 major): lens_collar and s_c4 (C2 collar lug, FP-11d) and eyecup (FX bed chamfer) are upper-body rows
# too (collar and its screw on the tub front, eyecup on the EVF): fixed upper mass, not carrier payload, so the same
# transfer holds for them. base_grip (C2 grip pocket, FX scar allowance) is a J4 LOWER row: for it the transfer is
# replaced by the new free body computed directly from the bound STEPs (check_scope.j4_direct, tested against the
# export18 transfer); no other lower row may change.
ALLOWED_CHANGED_ROWS=('tub','panel','carrier','lens_collar','s_c4','eyecup')
ALLOWED_CHANGED_LOWER_ROWS=('base_grip',)
def check_changed(changed):
    bad=sorted(set(changed)-set(ALLOWED_CHANGED_ROWS)-set(ALLOWED_CHANGED_LOWER_ROWS))
    if bad: raise AssertionError(f'Unexpected changed components: {bad}')
def carrier_section(oldloads,a,b,changed):
    """Reinforced-arm 5g half-reaction screen at the current payload. Beam stress and deflection are linear in the
    load and FP-11c leaves the reinforced arm section as it was (same arm polygon and 5 mm depth; the root pad r 4.8 ->
    5.2 and the thicker frame rails only add material), so the export18 screen scales with payload."""
    ref=oldloads['carrier_reinforced_at_integrated_payload']
    if 'carrier' not in changed:
        return {'payload_g':oldloads['carrier_payload_g'],'reinforced_screen':ref,'reason':'Carried inventory and all carrier/payload manifest rows unchanged; added tub/panel material is fixed housing, not carrier payload.'}
    d=b['carrier']['mass_est_g']-a['carrier']['mass_est_g'];pay=oldloads['carrier_payload_g']+d;k=pay/oldloads['carrier_payload_g']
    return {'payload_g':pay,'reference_payload_g':oldloads['carrier_payload_g'],'carrier_mass_delta_g':d,'payload_ratio':k,
            'reinforced_screen':{'stress_MPa':ref['stress_MPa']*k,'deflection_mm':ref['deflection_mm']*k},
            'reference_reinforced_screen':ref,'scaling':'linear in payload; reinforced arm section unchanged by FP-11c',
            'reason':'FP-11c thickened the carrier frame to its 22.2 bed face (VN-54) and opened its counterbores (VN-56): the carrier mass change is carrier payload; the other carried rows are unchanged.'}
def read(p): return json.loads(read_text(p))

def plenum_document_context(manifest, report, manifest_hash, report_hash=None):
    """Copy measured mouth/coupon fields, never promote stale reports to current facts.

    check-scope is deliberately not an input here: it consumes this supplement's
    J4 screen. The final PDF binds that later report separately, avoiding a cycle.
    """
    current = report.get('manifest_sha256') == manifest_hash
    rows = {r['id']: r for r in report.get('checks', [])} if current else {}
    mouths = {}
    for name in ('cold_rear', 'cold_bottom', 'hot_bottom', 'hot_front'):
        row = rows.get(name + '_sections_and_path')
        if row:
            mouths[name] = {'minimum_sampled_neck_mm2': row['minimum_sampled_neck_mm2'],
                            'status': row['status']}
    ports = {bay: sum(r['section']['free_area_mm2'] for key, r in rows.items()
                     if key.startswith(bay + '_wall_port_')) for bay in ('cold', 'hot')}
    ci = C/'vent-study/shadow-plenum-coupon/coupon-index.json'
    coupons = {'same_manifest': False, 'count': None, 'receipts': [], 'source_sha256': {}}
    if ci.exists():
        index = read(ci)
        coupons['same_manifest'] = index.get('manifest_sha256') == manifest_hash
        coupons['source_sha256'][rel_posix(ci, C)] = sha(ci)
        if coupons['same_manifest']:
            assert index['coupon_count'] == len(index['receipts']), 'Coupon count disagrees with receipt inventory'
            coupons['count'] = index['coupon_count']
            for name, expected in index['receipts'].items():
                path = ci.parent/name
                assert sha(path) == expected, 'Coupon receipt changed: ' + name
                row = read(path)
                assert row['manifest_sha256'] == manifest_hash, 'Foreign-manifest coupon: ' + name
                assert row['tub_sha256'] == manifest['files']['step/tub.step'], 'Coupon binds another tub: ' + name
                if report_hash is not None:
                    assert row['source_check_sha256'] == report_hash, 'Coupon binds another plenum report: ' + name
                coupons['source_sha256'][rel_posix(path, C)] = sha(path)
                coupons['receipts'].append({k: row[k] for k in
                    ('name', 'print_dimensions_mm', 'valid', 'solid_count', 'step_reimport_valid',
                     'physical_qualified', 'status', 'limitations')})
    assembly_parts = [r['id'] for r in manifest['rows'] if r['kind'] == 'printed']
    physical_pieces = [name for name in manifest['print_poses'] if name != 'centring_gauge']
    if 'production_prints' in manifest:
        inventory = manifest['production_prints']
        assert inventory['assembly_row_count'] == len(assembly_parts), 'Printed assembly-row count disagrees'
        assert inventory['piece_count'] == len(physical_pieces), 'Physical production-print count disagrees'
        assert set(inventory['files']) == {f'stl/{name}.stl' for name in physical_pieces}, 'Production-print inventory disagrees'
    return {'same_manifest': current, 'revision': manifest.get('ventilation', {}).get('revision'),
            'printed_assembly_rows': len(assembly_parts), 'physical_print_pieces': len(physical_pieces),
            'tab_catch_joint': manifest.get('tab_catch_joint'),
            'mouths': mouths, 'wall_ports_mm2': ports if current else {}, 'coupons': coupons}

def coupon_description(context):
    c = context['coupons']
    if not c['same_manifest']:
        return 'No current manifest-bound plenum coupon inventory is available. Regenerate and inspect the coupons before making a current geometry claim.'
    labels = {'preliminary_regular_grid': 'small roof/beam/pillar crop (legacy regular-grid name)',
              'port_service_and_edge_regions': 'port-service and edge crop', 'all_four_mouths': 'all-four-mouths crop'}
    parts = []
    for r in c['receipts']:
        dims = ' x '.join(f'{v:.1f}' for v in r['print_dimensions_mm'])
        validity = ('valid saved-STEP single solid' if r['valid'] and r['step_reimport_valid'] and r['solid_count'] == 1
                    else 'geometry validity not established')
        parts.append(f"{labels.get(r['name'], r['name'])}: {dims} mm ({validity})")
    return (f"The {c['count']} source-bound open-edge plenum coupons are " + '; '.join(parts) +
            f'. They remain separate from the {context["printed_assembly_rows"]} printed assembly rows '
            f'({context["physical_print_pieces"]} physical production prints, because the tub body and bonded stub print separately), '
            'the centring gauge and the nine retained structural coupon pieces. '
            'None has been sliced, printed or tested. The all-four-mouths crop opens the inner wall face and omits the tub body; '
            'cut edges cannot establish closed-body cleanout or tub stiffness. The smaller crops omit regions of the complete plenum. '
            'Coupon geometry does not prove roof toolpaths, strength, pressure loss, thermal performance or a whole-camera rating.')

def blocked_hot_mouth_description(context):
    if not context['same_manifest'] or 'hot_front' not in context['mouths']:
        return 'No current saved-STEP hot-front neck measurement is available; blocked-mouth area remains unreported until the plenum checks are refreshed.'
    front = context['mouths']['hot_front']['minimum_sampled_neck_mm2']
    bottom = context['mouths']['hot_bottom']['minimum_sampled_neck_mm2']
    return (f'Blocking the hot underside mouth leaves the front mouth, whose minimum sampled saved-STEP neck is {front:.2f} mm2 '
            f'against {context["wall_ports_mm2"]["hot"]:.2f} mm2 of measured hot wall ports, before internal losses. '
            f'The {bottom + front:.2f} mm2 sum of the two sampled mouth necks cannot be credited in that case. '
            'These areas are geometric samples, not useful airflow or rated blocked-vent operation.')

def selected_catch_description(context):
    joint = context.get('tab_catch_joint')
    if not joint:
        return 'The saved manifest does not expose bonded-catch dimensions; no corrective joint dimensions are claimed from it.'
    t, c = joint['tenon_mm'], joint['pocket_clearance_mm']
    return (f"The selected manifest records a {t['h']:g} mm nominal tenon height with a "
            f"{t['x'][1]-t['x'][0]:.1f} x {t['t']:g} mm tenon section, X/Y/Z pocket clearances "
            f"{c['x']:g}/{c['y']:g}/{c['z']:g} mm, ceiling top Z{joint['ceiling_top_z_mm']:g} mm and "
            f"{joint['ceiling_floor_mm']:.1f} mm ceiling floor. These are modeled dimensions. "
            f"The lower working face recess is {joint.get('working_face_recess_mm',0):g} mm; "
            f"the host escape groove is {joint.get('adhesive_escape_groove_mm',{}).get('width',0):g} mm wide "
            f"and {joint.get('adhesive_escape_groove_mm',{}).get('depth',0):g} mm deep. "
            'The unchanged catch-window and first-contact rules now cover separately reported feasible sampled '
            'tilts, yaw, translations and coupled poses; this is not exhaustive tolerance or withdrawal proof. '
            'Actual engaged height, dry seating, adhesive flow, bond, torque and creep require separate qualification.')

def bonded_coupon_context(manifest_hash):
    path = P/'bonded-catch-coupon/receipt.json'
    if not path.exists():
        return {'same_manifest': False, 'status': 'No generated bonded-catch joint coupon is recorded'}
    receipt = read(path)
    current = receipt.get('manifest_sha256') == manifest_hash
    out = {'same_manifest': current, 'path': rel_posix(path, C), 'sha256': sha(path),
           'status': receipt['status'] if current else 'Coupon binds another manifest'}
    if current:
        out.update(piece_count=receipt['piece_count'], crop_bounds_mm=receipt['crop_bounds_mm'],
                   purpose=receipt['purpose'], physical_qualified=receipt['physical_qualified'],
                   parts=[{'id': r['id'], 'face_down': r['face_down'],
                           'print_dimensions_mm': r['mesh']['print_dimensions_mm']} for r in receipt['parts']])
    return out

def bonded_coupon_description(context):
    if not context['same_manifest']:
        return context['status'] + '. The local joint physical gate remains open.'
    pieces = '; '.join(r['id'] + ': ' + ' x '.join(f'{x:.1f}' for x in r['print_dimensions_mm']) +
                      f" mm, {r['face_down']} down" for r in context['parts'])
    return (f"A separate {context['piece_count']}-piece bonded-catch study is generated from the selected tub print stock "
            'and the exact production insert: ' + pieces + '. It retains production layer orientations. '
            'It screens local seating, datum tilt, adhesion and warm creep only. Cropped host and fixture omit whole-tub '
            'compliance and complete lens/camera constraints, so no whole-tub 0.5 N m torque qualification follows. '
            'The study is additional to the retained structural and plenum coupons, with no production-part count change. '
            'It has not been sliced, printed, bonded or mechanically tested.')

LAST_CENTRES={}   # FX: the J4 lower-row centres of the last make() call (written as j4-lower-centres.json)
def make():
    oldpath=C/'history/reviewed-export18/manifest.json'; newpath=C/'out/compact-kowa_lm6hc/manifest.json'
    refpath=P/'reference-export18-structural-binding.json'
    old,new,ref=map(read,[oldpath,newpath,refpath]); h=sha(newpath)
    assert sha(oldpath)==ref['manifest_sha256'], 'Reference structural binding is not export18'
    a={r['id']:r for r in old['rows']}; b={r['id']:r for r in new['rows']}
    assert a.keys()==b.keys(), 'Changed component inventory needs a new free body'
    changed=ER.changed_rows(a,b)  # numbers within max(ER.ABS_TOL, ER.REL_TOL*|x|); ids, kinds, sources and other strings exact
    check_changed(changed)
    oldup=ref['integrated_upper_body_screen']; oldloads=ref['integrated_comparison_loads']
    delta_mass=new['mass_est_g']-old['mass_est_g']; um=oldup['estimated_mass_g']+delta_mass
    assert abs(sum(b[k]['mass_est_g']-a[k]['mass_est_g'] for k in changed)-delta_mass)<1e-7, 'Assembly mass delta does not match changed rows'
    first=[oldup['estimated_mass_g']*oldup['estimated_com_mm'][i]+new['mass_est_g']*new['com_est_mm'][i]-old['mass_est_g']*old['com_est_mm'][i] for i in range(3)]
    import check_scope as CS
    # FX: J4 lower-row centres per variant, from the bound STEPs when present (CAD), else the committed cache bound by
    # the STEP hashes in each manifest (CAD-free fixture copies); written as j4-lower-centres.json (checked by --check)
    variants=[mp for mp in sorted((C/'out').glob('*/manifest.json')) if 'storage' in read(mp)]
    cpath=P/'j4-lower-centres.json'; cache=read(cpath)['variants'] if cpath.exists() else {}
    def _c(p):
        import cadquery as cq
        c=cq.importers.importStep(str(p)).val().Center(); return (c.x,c.y,c.z)
    centres={mp.parent.name:CS.lower_centres(read(mp),mp.parent,_c,sha,cache.get(mp.parent.name)) for mp in variants}
    lower_changed=sorted(set(changed)&set(CS.J4_LOWER_IDS))
    free_body='export18 first-moment transfer (lower rows unchanged)'
    if lower_changed:   # FX: new free body from the bound STEPs (check_scope.j4_direct)
        lf=CS.first_from_centres(new,centres['compact-kowa_lm6hc'])
        um=new['mass_est_g']-sum(b[i]['mass_est_g'] for i in CS.J4_LOWER_IDS)
        first=[new['mass_est_g']*new['com_est_mm'][k]-sum(lf[i][k] for i in CS.J4_LOWER_IDS) for k in range(3)]
        free_body='new free body: complete manifest minus the J4 lower rows measured from their bound STEPs (lower rows changed: %s)' % ', '.join(lower_changed)
    uc=[x/um for x in first]; g=9.80665
    floor=first[2]/1000*g*5; floor_ratio=floor/oldup['5g_floor_Mx_Nmm']
    gf=new['mass_est_g']/1000*g*5; gm=gf*(uc[2]+55); grip_ratio=gm/oldloads['grip_moment_Nmm']
    wire=ref['unresolved_wiring_mass_sensitivity']['added_5g_moment_Nmm']
    coupon=(floor+wire)/2000; proposed=math.ceil(coupon*20)/20
    # FP-12 (VN-33): the same transfer per variant (check_scope.j4_screen refuses a variant whose lower free-body rows
    # change); the stated screen is the one that covers every valid variant.
    per={mp.parent.name:dict(CS.j4_screen(ref,old,read(mp),ER.changed_rows,lower_first=CS.first_from_centres(read(mp),centres[mp.parent.name])),manifest_sha256=sha(mp)) for mp in variants}
    env=CS.j4_envelope(per)
    assert abs(per['compact-kowa_lm6hc']['equal_share_plus_wiring_Nm']-coupon)<1e-12 and CS.J4_COMPACT_SCREEN_NM==proposed, 'per-variant J4 screen disagrees with the compact calculation'
    vent_report='shadow-plenum-checks.json' if 'shadow' in new.get('ventilation',{}).get('revision','').lower() else 'ventilation-checks.json'
    vp=C/'out/compact-kowa_lm6hc'/vent_report; vr=read(vp) if vp.exists() else {}
    plenum = plenum_document_context(new, vr, h, sha(vp) if vp.exists() else None)
    bonded_coupon = bonded_coupon_context(h)
    gates=ER.inherited_gates(C)
    out={
      'method':'CAD-free analytical mass/load sensitivity using retained export18 sections; no FEA, contact solution, physical test or strength qualification',
      'manifest_sha256':h,'built_utc':new['built_utc'],'verification_source_sha256':sha(Path(__file__)),
      'reference_manifest_sha256':sha(oldpath),'reference_structural_binding_sha256':sha(refpath),
      'changed_manifest_rows':changed,'unchanged_manifest_rows_checked':len(a)-len(changed),
      'row_comparison':{'numeric_abs_tol':ER.ABS_TOL,'numeric_rel_tol':ER.REL_TOL,'rule':'numbers equal within max(abs_tol, rel_tol*max(|a|,|b|)); ids, kinds, sources, other strings and bools exact'},
      'inherited_gates':gates,
      'geometry_scope':('Changed manifest rows: %s. All other rows are identical.' % ', '.join(changed))+' This is metadata consistency, not a new geometric equivalence test. Retained local sections require source/STEP preservation evidence. Old full-tub and full-panel zero-difference bindings do not apply.',
      'ventilation_report':{'path':rel_posix(vp,C), 'sha256':sha(vp) if vp.exists() else None,'same_manifest':vr.get('manifest_sha256')==h,'summary':vr.get('summary')},
      'plenum_document_context':plenum,
      'bonded_catch_coupon':bonded_coupon,
      'assembly':{'reference_mass_g':old['mass_est_g'],'current_mass_g':new['mass_est_g'],'delta_mass_g':delta_mass,'delta_mass_percent':delta_mass/old['mass_est_g']*100,'com_mm':new['com_est_mm'],'manifest_mesh_dimensions_mm':new['complete_dimensions_mm'],'core_dimensions_mm':new['core_dimensions_mm']},
      'printed':{k:{'reference_proxy_mass_g':a[k]['mass_est_g'],'current_proxy_mass_g':b[k]['mass_est_g'],'delta_volume_mm3':b[k]['volume_mm3']-a[k]['volume_mm3']} for k in ['tub','panel']+(['carrier'] if 'carrier' in changed else [])},
      'upper_body':{'free_body':free_body,'mass_g':um,'com_mm':uc,'force_5g_N':um/1000*g*5,'floor_moment_5g_Nmm':floor,'moment_change_percent':(floor_ratio-1)*100,'lip_stress_MPa':oldup['lip_stress_MPa']*floor_ratio,'head_wing_stress_MPa':oldup['head_wing_stress_MPa']*floor_ratio,'unequal_station_sharing_multiplier':[0.6,1.4]},
      'grip':{'force_5g_N':gf,'load_point_z_mm':uc[2],'hand_plane_z_mm':-55,'moment_Nmm':gm,'moment_change_percent':(grip_ratio-1)*100,'nominal_stress_x_y_MPa':[v*grip_ratio for v in oldloads['grip_nominal_stress_x_y_MPa']]},
      'carrier':carrier_section(oldloads,a,b,changed),
      'coupon_load':{'wiring_mass_sensitivity_g':12,'wiring_upper_height_mm':100,'added_5g_moment_Nmm':wire,'equal_share_plus_wiring_Nm':coupon,'proposed_rounded_equal_share_screen_Nm':proposed,'seventy_percent_share_plus_wiring_Nm':(floor+wire)*.7/1000,'old_0_90_Nm_covers_equal_share_plus_wiring':.9>=coupon,'all_variants_screen_Nm':env['all_variants_screen_Nm'],'governing_variant':env['governing_variant'],'compact_screen_covers':env['compact_screen_covers'],'per_variant':{v:{k:r[k] for k in ('valid','changed_rows','added_rows','upper_mass_g','floor_moment_5g_Nmm','equal_share_plus_wiring_Nm','seventy_percent_share_plus_wiring_Nm','proposed_rounded_equal_share_screen_Nm','manifest_sha256') if k in r} for v,r in per.items()},'warning':'Proposed inert-sample screen only, not a rating or approved load test. Equal-share target does not bound 70% station reaction; fixture capacity, local contact, warm creep and whole-assembly response remain unqualified.'},
      'material_sensitivity':{'E_MPa':[800,1600,2400],'deflection_multiplier_relative_to_1600':[2,1,2/3],'normal_strength_scenarios_MPa':[5,10,20,30],'not_allowables':True,'notches_creep_fatigue_impact_excluded':True,
          'asa_density':{'inherited_g_cm3':1.07,'manufacturer_reference_g_cm3':1.13,'contribution_change_percent':(1.13/1.07-1)*100,
                        'scope':'ASA contribution at fixed volume and unchanged empirical mass factor only; not a complete-camera mass change or adopted grade',
                        'source':'https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa',
                        'exact_grade_batch_and_process_confirmed':False}},
      'physical_qualified':False}
    FREE_BODY_TEXT=('The changed first moment is transferred from the complete manifests into the old upper free body: new upper first moment = old upper first moment + (new complete mass × new complete CoM − old complete mass × old complete CoM). This is valid only while the lower excluded parts remain unchanged.' if not lower_changed else
        'A J4 lower row changed (' + ', '.join(lower_changed) + '), so the export18 transfer is not used: the upper free body is the complete manifest (mass × CoM) minus the eight J4 lower rows, each row mass × the centre of mass of its manifest-bound STEP (check_scope.j4_direct; on the phase-1 export, whose lower rows equal those of export18, this reproduces the export18 transfer, tests/test_fx_fixup.py).')
    ass=out['assembly'];up=out['upper_body'];gr=out['grip'];car=out['carrier'];cl=out['coupon_load']; dims=ass['manifest_mesh_dimensions_mm']; cg=ass['com_mm']
    text=f'''# Concealed vent structural supplement

This supplement updates mass and quasi-static load sensitivity for the selected shadow-plenum compact Kowa candidate. It uses the retained export18 section models and the current manifest. It is not FEA, a drop rating, a physical strength result, or permission to print/energize. All {gates['open']} inherited physical gates and M1 remain open.

**PRINT HOLD:** all four plenum edge mouths and the roof need slicer, bridge and cleanout evidence from current source-bound coupons; none exists yet. Selected geometry metadata: {plenum['revision']}. Roof and beam checks are geometric screens; they do not show actual toolpaths or bridge quality.

## Exact scope

Current manifest: `{h}`, built {new['built_utc']}. Frozen export18 reference: `{sha(oldpath)}`. The reproducible calculation is `update_concealed_vent_structure.py`; exact inputs and unrounded results are in `concealed-vent-structural.json` and the copied reference `reference-export18-structural-binding.json`.

{'Changed manifest rows: ' + ', '.join(changed)}; all {len(a)-len(changed)} other rows are identical. This checks metadata, not occupied-solid equivalence. The retained carrier, grip and J4 sections are conditional inputs to the calculation and must stay tied to the independent source/STEP preservation checks. The former whole-tub and whole-panel zero-difference bindings are historical and do not apply to this revision. The new integral skin, cold/hot plenums, divider, support beams and pillars, CSI sleeve and panel surface are outside those old whole-part claims.

## Mass and applied loads

| Quantity | Reviewed export18 | Concealed candidate |
|---|---:|---:|
| Estimated complete Kowa mass | {ass['reference_mass_g']:.2f} g | {ass['current_mass_g']:.2f} g |
| Tub proxy mass | {a['tub']['mass_est_g']:.2f} g | {b['tub']['mass_est_g']:.2f} g |
| Panel proxy mass | {a['panel']['mass_est_g']:.2f} g | {b['panel']['mass_est_g']:.2f} g |
| Upper-body free-body mass | {oldup['estimated_mass_g']:.2f} g | {up['mass_g']:.2f} g |
| Upper-body 5g floor moment | {oldup['5g_floor_Mx_Nmm']/1000:.4f} N·m | {up['floor_moment_5g_Nmm']/1000:.4f} N·m |
| Conservative grip 5g moment | {oldloads['grip_moment_Nmm']/1000:.4f} N·m | {gr['moment_Nmm']/1000:.4f} N·m |

The net modeled mass change is {ass['delta_mass_g']:.2f} g ({ass['delta_mass_percent']:.2f}%). Current complete CoM is ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f}) mm. Core is {new['core_dimensions_mm'][0]} × {new['core_dimensions_mm'][1]} × {new['core_dimensions_mm'][2]} mm. Manifest mesh-derived complete bounds are {dims[0]:.2f} × {dims[1]:.2f} × {dims[2]:.2f} mm; these are not fresh untessellated STEP measurements or a measured camera envelope.

Tub/panel mass uses the inherited ASA density 1.07 g/cm³ and empirical 0.85 mass factor. Polymaker's current reference density is 1.13 g/cm³: at equal volume this gives {out['material_sensitivity']['asa_density']['contribution_change_percent']:.1f}% more ASA contribution. This is not the same percentage increase in complete-camera mass and is not silently applied to the mass model. The exact ASA grade, lot and print process are unconfirmed. Neither density nor the empirical factor is a slicer measurement or stiffness multiplier. See [the source and applicability note](../corrective-2026-10-12/RESEARCH-INTEGRATION.md). The legacy 12 g connector/fuse/pigtail lump has an unresolved real distribution; other harness masses remain omitted. Weigh the printed parts, loaded body and actual harness before setting final qualification loads.

{FREE_BODY_TEXT} The 5g floor moment uses upper mass only, avoiding false credit from the low battery as a counterbalance across J4. Grip screening conservatively places the whole new assembly mass at upper-body Z{uc[2]:.2f} with hand reaction Z−55. The 1g/3g/5g cases are quasi-static handling sensitivities, not drop or life ratings.

## Retained sections under changed load

With the same equal tongue sharing and local strip assumptions, J4 nominal lip/head stresses become {up['lip_stress_MPa']:.2f}/{up['head_wing_stress_MPa']:.2f} MPa, a {up['moment_change_percent']:.2f}% increase. The 30–70% station-sharing sensitivity multiplies these by 0.6–1.4. Joint contact, local notches, anisotropy, wear and creep are not solved. Grip gross nominal stresses become {gr['nominal_stress_x_y_MPa'][0]:.2f}/{gr['nominal_stress_x_y_MPa'][1]:.2f} MPa, a {gr['moment_change_percent']:.2f}% increase; tub/floor compliance and joint slip remain excluded.

{('The carrier payload remains ' + format(car['payload_g'], '.2f') + ' g because the added material belongs to the fixed tub/panel. Its retained reinforced-arm 5g, half-reaction screen remains ' + format(car['reinforced_screen']['stress_MPa'], '.2f') + ' MPa and ' + format(car['reinforced_screen']['deflection_mm'], '.3f') + ' mm at assumed E=1600 MPa.') if 'carrier' not in changed else ('FP-11c thickened the carrier frame to its continuous 22.2 bed face and opened its counterbores, so the carrier payload rises by ' + format(car['carrier_mass_delta_g'], '.2f') + ' g to ' + format(car['payload_g'], '.2f') + ' g. The reinforced arm section is unchanged, so its retained 5g, half-reaction screen scales with payload to ' + format(car['reinforced_screen']['stress_MPa'], '.2f') + ' MPa and ' + format(car['reinforced_screen']['deflection_mm'], '.3f') + ' mm (export18: ' + format(car['reference_reinforced_screen']['stress_MPa'], '.2f') + ' MPa, ' + format(car['reference_reinforced_screen']['deflection_mm'], '.3f') + ' mm) at assumed E=1600 MPa.')} This does not qualify the arm, boss roots, screws or service pulls. Current lens/collar mass is included in the manifest free body; preload cautions, FPS-rest load cases and 100 N strap comparison inputs remain inherited assumptions; thermal and physical tests remain necessary.

The old 0.90 N·m per-front-joint coupon target {'still covers' if cl['old_0_90_Nm_covers_equal_share_plus_wiring'] else 'does not cover'} the new equal-share floor moment plus the retained 12 g-at-Z100 wiring-location sensitivity. The calculated minimum is {cl['equal_share_plus_wiring_Nm']:.4f} N·m; use {cl['proposed_rounded_equal_share_screen_Nm']:.2f} N·m as the rounded proposed equal-share screening target after fixture review. A 70% station reaction with that same wiring sensitivity would be {cl['seventy_percent_share_plus_wiring_Nm']:.4f} N·m and is a separate unqualified case. Existing C08/C09 geometry can screen the retained local mating surfaces; it omits the rear joint, independent lock and full tub. Do not turn a local coupon result into a whole-camera rating.

Variant coverage (FP-12, VN-33; FX). The same first-moment transfer applies to every exported variant whose lower grip/battery rows are unchanged, and a variant whose lower rows changed gets the new free body from its bound STEPs (check_scope.j4_direct); {sum(r['valid'] for r in cl['per_variant'].values())} of {len(cl['per_variant'])} have a valid analytical free body{'' if all(r['valid'] for r in cl['per_variant'].values()) else ' (' + ', '.join(v for v,r in cl['per_variant'].items() if not r['valid']) + ' need a new free body)'}. Equal-share plus wiring targets: {'; '.join('{} {:.4f} N·m (70% share {:.4f} N·m)'.format(v,r['equal_share_plus_wiring_Nm'],r['seventy_percent_share_plus_wiring_Nm']) for v,r in cl['per_variant'].items() if r['valid'])}. The {CS.J4_COMPACT_SCREEN_NM:.2f} N·m compact value covers {', '.join(v for v,ok in cl['compact_screen_covers'].items() if ok) or 'no variant'} and does not cover {', '.join(v for v,ok in cl['compact_screen_covers'].items() if not ok) or 'none'}. Use {cl['all_variants_screen_Nm']:.2f} N·m (governed by {cl['governing_variant']}) as the rounded equal-share screen that covers every variant. The 70% cases remain separate unqualified cases.

## Print material and thermal implications

{selected_catch_description(plenum)}

{bonded_coupon_description(bonded_coupon)} See [the local coupon instructions](bonded-catch-coupon/README.md) for source identity and test limits.

Retain the current broad-face starting poses and 0.20 mm layer baseline: tub −Y face down, panel/carrier +Y face down, grip +Z top down and collar +X front down. The selected 1.6 mm skin and windowed ribs, 6 mm plenum gap, divider and CSI sleeve change toolpath transitions, warping and local cooling; they do not establish greater shell stiffness or printability. The retained 2.5 mm inner wall forms a roof over the plenum in this print pose. Its spans around support interruptions and ports require section coupons, contiguous toolpaths, bridge/sag inspection and verified cleanout. Concealment of broadside grilles does not establish a self-supporting roof.

The plain panel restores material where four blind grooves previously retained only 0.2 mm floors. This removes those local thin floors but does not prove panel flatness, screw-seat strength or clamp performance. The CSI access slot remains straight and unsealed, so its bypass must remain in the airflow and thermal interpretation. Actual cooler profile, fan operating point, separate normal-hand/strap/stand occlusion cases and closed-body battery temperature remain open.

{blocked_hot_mouth_description(plenum)} The later `check-scope-checks.json` report assesses branch-series and path minimum-cut area against the same saved tub; read its current statuses separately. The PDF binds that report after it is regenerated; this mass calculation does not infer a flow pass.

Use the earlier independent E=0.8/1.6/2.4 GPa sensitivity (deflection multipliers 2/1/0.667) and 5/10/20/30 MPa normal-strength scenarios only to expose dependence, never as material allowables. Print direction, dense local sections, conditioning, layer bonds and warm creep need measured evidence. No infill factor, catalogue tensile result or heat-deflection temperature establishes a safe service temperature or factor of safety.

{coupon_description(plenum)} Record every stopped or failed physical test. Purchased BOM selections and quantities are unchanged by this calculation. Material allowables, the epoxy SKU and cure process, and supplier minimum bend radii for the actual camera/HDMI/OLED ribbons remain unknown. A geometric pass does not close those gates.

'''
    out['j4_lower_centres_file']='structural-review/j4-lower-centres.json'
    LAST_CENTRES.clear();LAST_CENTRES.update(note='J4 lower rows: centre of mass of each manifest-bound STEP (check_scope.'
                                             'lower_centres); first moment = manifest row mass x centre',variants=centres)
    return out,text.rstrip()+'\n'
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    try:
        d,t=make();cen=dict(LAST_CENTRES)
    except AssertionError as e:   # FX: a refusal is a message and exit 1, not a traceback
        import sys;print('REFUSED: %s (nothing written)' % e,file=sys.stderr,flush=True);raise SystemExit(1)
    if args.check:
        assert d['ventilation_report']['same_manifest'], 'Ventilation report does not bind the selected manifest'
        assert d['plenum_document_context']['coupons']['same_manifest'], 'Coupon inventory does not bind the selected manifest'
    outputs={'concealed-vent-structural.json':json.dumps(canonical_zero(d),indent=2)+'\n','CONCEALED-VENT-STRUCTURAL.md':t,
             'j4-lower-centres.json':json.dumps(canonical_zero(cen),indent=2)+'\n'}
    for n,content in outputs.items():
        if args.check: assert read_text(P/n)==content, f'Stale structural output: {n}'
        else: write_text(P/n,content)
    print(json.dumps({'manifest_sha256':d['manifest_sha256'],'mass_delta_g':d['assembly']['delta_mass_g'],'coupon_load':d['coupon_load'],'physical_qualified':False},indent=2))
