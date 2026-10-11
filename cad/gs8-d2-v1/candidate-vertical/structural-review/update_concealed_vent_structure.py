"""Manifest-bound mass/load sensitivity only; no CAD, FEA, or qualification.
The inherited upper free body excludes the lower grip/battery hardware. Only
upper tub/panel may change, so transfer their first-moment change from complete
assembly manifests. Refuse if any other manifest row changes.
"""
import sys as _cvsys; _cvsys.path.append(str(__import__('pathlib').Path(__file__).resolve().parents[1]))  # candidate-vertical root: cv_io
from cv_io import read_text, rel_posix, write_text
import evidence_rules as ER  # FP-04: numeric row tolerance (VN-06) and the inherited gate count from its source (VN-08)
from pathlib import Path
import argparse, hashlib, json, math
P=Path(__file__).resolve().parent; C=P.parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
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
    gates=ER.inherited_gates(C)
    out={
      'method':'CAD-free analytical mass/load sensitivity using retained export18 sections; no FEA, contact solution, physical test or strength qualification',
      'manifest_sha256':h,'built_utc':new['built_utc'],'verification_source_sha256':sha(Path(__file__)),
      'reference_manifest_sha256':sha(oldpath),'reference_structural_binding_sha256':sha(refpath),
      'changed_manifest_rows':changed,'unchanged_manifest_rows_checked':len(a)-len(changed),
      'row_comparison':{'numeric_abs_tol':ER.ABS_TOL,'numeric_rel_tol':ER.REL_TOL,'rule':'numbers equal within max(abs_tol, rel_tol*max(|a|,|b|)); ids, kinds, sources, other strings and bools exact'},
      'inherited_gates':gates,
      'geometry_scope':('All non-tub/panel manifest rows are identical.' if 'carrier' not in changed else 'All manifest rows other than %s are identical.' % '/'.join(changed))+' This is metadata consistency, not a new geometric equivalence test. Retained local sections require source/STEP preservation evidence. Old full-tub and full-panel zero-difference bindings do not apply.',
      'ventilation_report':{'path':rel_posix(vp,C), 'sha256':sha(vp) if vp.exists() else None,'same_manifest':vr.get('manifest_sha256')==h,'summary':vr.get('summary')},
      'assembly':{'reference_mass_g':old['mass_est_g'],'current_mass_g':new['mass_est_g'],'delta_mass_g':delta_mass,'delta_mass_percent':delta_mass/old['mass_est_g']*100,'com_mm':new['com_est_mm'],'manifest_mesh_dimensions_mm':new['complete_dimensions_mm'],'core_dimensions_mm':new['core_dimensions_mm']},
      'printed':{k:{'reference_proxy_mass_g':a[k]['mass_est_g'],'current_proxy_mass_g':b[k]['mass_est_g'],'delta_volume_mm3':b[k]['volume_mm3']-a[k]['volume_mm3']} for k in ['tub','panel']+(['carrier'] if 'carrier' in changed else [])},
      'upper_body':{'free_body':free_body,'mass_g':um,'com_mm':uc,'force_5g_N':um/1000*g*5,'floor_moment_5g_Nmm':floor,'moment_change_percent':(floor_ratio-1)*100,'lip_stress_MPa':oldup['lip_stress_MPa']*floor_ratio,'head_wing_stress_MPa':oldup['head_wing_stress_MPa']*floor_ratio,'unequal_station_sharing_multiplier':[0.6,1.4]},
      'grip':{'force_5g_N':gf,'load_point_z_mm':uc[2],'hand_plane_z_mm':-55,'moment_Nmm':gm,'moment_change_percent':(grip_ratio-1)*100,'nominal_stress_x_y_MPa':[v*grip_ratio for v in oldloads['grip_nominal_stress_x_y_MPa']]},
      'carrier':carrier_section(oldloads,a,b,changed),
      'coupon_load':{'wiring_mass_sensitivity_g':12,'wiring_upper_height_mm':100,'added_5g_moment_Nmm':wire,'equal_share_plus_wiring_Nm':coupon,'proposed_rounded_equal_share_screen_Nm':proposed,'seventy_percent_share_plus_wiring_Nm':(floor+wire)*.7/1000,'old_0_90_Nm_covers_equal_share_plus_wiring':.9>=coupon,'all_variants_screen_Nm':env['all_variants_screen_Nm'],'governing_variant':env['governing_variant'],'compact_screen_covers':env['compact_screen_covers'],'per_variant':{v:{k:r[k] for k in ('valid','changed_rows','added_rows','upper_mass_g','floor_moment_5g_Nmm','equal_share_plus_wiring_Nm','seventy_percent_share_plus_wiring_Nm','proposed_rounded_equal_share_screen_Nm','manifest_sha256') if k in r} for v,r in per.items()},'warning':'Proposed inert-sample screen only, not a rating or approved load test. Equal-share target does not bound 70% station reaction; fixture capacity, local contact, warm creep and whole-assembly response remain unqualified.'},
      'material_sensitivity':{'E_MPa':[800,1600,2400],'deflection_multiplier_relative_to_1600':[2,1,2/3],'normal_strength_scenarios_MPa':[5,10,20,30],'not_allowables':True,'notches_creep_fatigue_impact_excluded':True},
      'physical_qualified':False}
    FREE_BODY_TEXT=('The changed first moment is transferred from the complete manifests into the old upper free body: new upper first moment = old upper first moment + (new complete mass × new complete CoM − old complete mass × old complete CoM). This is valid only while the lower excluded parts remain unchanged.' if not lower_changed else
        'A J4 lower row changed (' + ', '.join(lower_changed) + '), so the export18 transfer is not used: the upper free body is the complete manifest (mass × CoM) minus the eight J4 lower rows, each row mass × the centre of mass of its manifest-bound STEP (check_scope.j4_direct; on the phase-1 export, whose lower rows equal those of export18, this reproduces the export18 transfer, tests/test_fx_fixup.py).')
    ass=out['assembly'];up=out['upper_body'];gr=out['grip'];car=out['carrier'];cl=out['coupon_load']; dims=ass['manifest_mesh_dimensions_mm']; cg=ass['com_mm']
    text=f'''# Concealed vent structural supplement

This supplement updates mass and quasi-static load sensitivity for the selected shadow-plenum compact Kowa candidate. It uses the retained export18 section models and the current manifest. It is not FEA, a drop rating, a physical strength result, or permission to print/energize. All {gates['open']} inherited physical gates and M1 remain open.

**PRINT HOLD:** all four plenum edge mouths (rear Z5..75, cold underside, hot underside, front Z5..40) and the trial3 roof (1.2 mm beams on pillars, at most 14 mm beam bridges, roof spans computed by print_bridge_direction) need slicer, bridge and cleanout evidence from the three plenum coupons (the third covers all four mouths); none exists yet.

## Exact scope

Current manifest: `{h}`, built {new['built_utc']}. Frozen export18 reference: `{sha(oldpath)}`. The reproducible calculation is `update_concealed_vent_structure.py`; exact inputs and unrounded results are in `concealed-vent-structural.json` and the copied reference `reference-export18-structural-binding.json`.

{'Only tub and panel manifest rows change' if 'carrier' not in changed else 'Only the ' + ', '.join(changed) + ' manifest rows change'}; all {len(a)-len(changed)} other rows are identical. This checks metadata, not occupied-solid equivalence. The retained carrier, grip and J4 sections are conditional inputs to the calculation and must stay tied to the independent source/STEP preservation checks. The former whole-tub and whole-panel zero-difference bindings are historical and do not apply to this revision. The new integral skin, cold/hot plenums, divider, support posts, CSI sleeve and panel surface are outside those old whole-part claims.

## Mass and applied loads

| Quantity | Reviewed export18 | Concealed candidate |
|---|---:|---:|
| Estimated complete Kowa mass | {ass['reference_mass_g']:.2f} g | {ass['current_mass_g']:.2f} g |
| Tub proxy mass | {a['tub']['mass_est_g']:.2f} g | {b['tub']['mass_est_g']:.2f} g |
| Panel proxy mass | {a['panel']['mass_est_g']:.2f} g | {b['panel']['mass_est_g']:.2f} g |
| Upper-body free-body mass | {oldup['estimated_mass_g']:.2f} g | {up['mass_g']:.2f} g |
| Upper-body 5g floor moment | {oldup['5g_floor_Mx_Nmm']/1000:.4f} N·m | {up['floor_moment_5g_Nmm']/1000:.4f} N·m |
| Conservative grip 5g moment | {oldloads['grip_moment_Nmm']/1000:.4f} N·m | {gr['moment_Nmm']/1000:.4f} N·m |

The net modeled mass increase is {ass['delta_mass_g']:.2f} g ({ass['delta_mass_percent']:.2f}%). Current complete CoM is ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f}) mm. Core is {new['core_dimensions_mm'][0]} × {new['core_dimensions_mm'][1]} × {new['core_dimensions_mm'][2]} mm. Manifest mesh-derived complete bounds are {dims[0]:.2f} × {dims[1]:.2f} × {dims[2]:.2f} mm; these are not fresh untessellated STEP measurements or a measured camera envelope.

Tub/panel mass uses the inherited ASA density 1.07 g/cm³ and empirical 0.85 mass factor. These are not slicer measurements or stiffness multipliers. The legacy 12 g connector/fuse/pigtail lump has an unresolved real distribution; other harness masses remain omitted. Weigh the printed parts, loaded body and actual harness before setting final qualification loads.

{FREE_BODY_TEXT} The 5g floor moment uses upper mass only, avoiding false credit from the low battery as a counterbalance across J4. Grip screening conservatively places the whole new assembly mass at upper-body Z{uc[2]:.2f} with hand reaction Z−55. The 1g/3g/5g cases are quasi-static handling sensitivities, not drop or life ratings.

## Retained sections under changed load

With the same equal tongue sharing and local strip assumptions, J4 nominal lip/head stresses become {up['lip_stress_MPa']:.2f}/{up['head_wing_stress_MPa']:.2f} MPa, a {up['moment_change_percent']:.2f}% increase. The 30–70% station-sharing sensitivity multiplies these by 0.6–1.4. Joint contact, local notches, anisotropy, wear and creep are not solved. Grip gross nominal stresses become {gr['nominal_stress_x_y_MPa'][0]:.2f}/{gr['nominal_stress_x_y_MPa'][1]:.2f} MPa, a {gr['moment_change_percent']:.2f}% increase; tub/floor compliance and joint slip remain excluded.

{('The carrier payload remains ' + format(car['payload_g'], '.2f') + ' g because the added material belongs to the fixed tub/panel. Its retained reinforced-arm 5g, half-reaction screen remains ' + format(car['reinforced_screen']['stress_MPa'], '.2f') + ' MPa and ' + format(car['reinforced_screen']['deflection_mm'], '.3f') + ' mm at assumed E=1600 MPa.') if 'carrier' not in changed else ('FP-11c thickened the carrier frame to its continuous 22.2 bed face and opened its counterbores, so the carrier payload rises by ' + format(car['carrier_mass_delta_g'], '.2f') + ' g to ' + format(car['payload_g'], '.2f') + ' g. The reinforced arm section is unchanged, so its retained 5g, half-reaction screen scales with payload to ' + format(car['reinforced_screen']['stress_MPa'], '.2f') + ' MPa and ' + format(car['reinforced_screen']['deflection_mm'], '.3f') + ' mm (export18: ' + format(car['reference_reinforced_screen']['stress_MPa'], '.2f') + ' MPa, ' + format(car['reference_reinforced_screen']['deflection_mm'], '.3f') + ' mm) at assumed E=1600 MPa.')} This does not qualify the arm, boss roots, screws or service pulls. Lens/collar mass, preload cautions, FPS-rest load cases and 100 N strap comparison inputs are unchanged; thermal and physical tests remain necessary.

The old 0.90 N·m per-front-joint coupon target {'still covers' if cl['old_0_90_Nm_covers_equal_share_plus_wiring'] else 'does not cover'} the new equal-share floor moment plus the retained 12 g-at-Z100 wiring-location sensitivity. The calculated minimum is {cl['equal_share_plus_wiring_Nm']:.4f} N·m; use {cl['proposed_rounded_equal_share_screen_Nm']:.2f} N·m as the rounded proposed equal-share screening target after fixture review. A 70% station reaction with that same wiring sensitivity would be {cl['seventy_percent_share_plus_wiring_Nm']:.4f} N·m and is a separate unqualified case. Existing C08/C09 geometry can screen the retained local mating surfaces; it omits the rear joint, independent lock and full tub. Do not turn a local coupon result into a whole-camera rating.

Variant coverage (FP-12, VN-33; FX). The same first-moment transfer applies to every exported variant whose lower grip/battery rows are unchanged, and a variant whose lower rows changed gets the new free body from its bound STEPs (check_scope.j4_direct); {sum(r['valid'] for r in cl['per_variant'].values())} of {len(cl['per_variant'])} qualify{'' if all(r['valid'] for r in cl['per_variant'].values()) else ' (' + ', '.join(v for v,r in cl['per_variant'].items() if not r['valid']) + ' need a new free body)'}. Equal-share plus wiring targets: {'; '.join('{} {:.4f} N·m (70% share {:.4f} N·m)'.format(v,r['equal_share_plus_wiring_Nm'],r['seventy_percent_share_plus_wiring_Nm']) for v,r in cl['per_variant'].items() if r['valid'])}. The {CS.J4_COMPACT_SCREEN_NM:.2f} N·m compact value covers {', '.join(v for v,ok in cl['compact_screen_covers'].items() if ok) or 'no variant'} and does not cover {', '.join(v for v,ok in cl['compact_screen_covers'].items() if not ok) or 'none'}. Use {cl['all_variants_screen_Nm']:.2f} N·m (governed by {cl['governing_variant']}) as the rounded equal-share screen that covers every variant. The 70% cases remain separate unqualified cases.

## Print material and thermal implications

Retain the current broad-face starting poses and 0.20 mm layer baseline: tub −Y face down, panel/carrier +Y face down, grip +Z top down and collar +X front down. The selected 1.6 mm skin and windowed ribs, 6 mm plenum gap, divider and CSI sleeve change toolpath transitions, warping and local cooling; they do not establish greater shell stiffness or printability. The retained 2.5 mm inner wall forms a roof over the plenum in this print pose. Its spans around post exclusions and ports require section coupons, contiguous toolpaths, bridge/sag inspection and verified cleanout. Concealment of broadside grilles does not establish a self-supporting roof.

The plain panel restores material where four blind grooves previously retained only 0.2 mm floors. This removes those local thin floors but does not prove panel flatness, screw-seat strength or clamp performance. The CSI access slot remains straight and unsealed, so its bypass must remain in the airflow and thermal interpretation. Actual cooler profile, fan operating point, separate normal-hand/strap/stand occlusion cases and closed-body battery temperature remain open. Blocking the hot underside mouth leaves only the 210 mm² front mouth against 510 mm² wall ports, before internal losses; no minimum useful airflow or rated blocked-vent operation is established.

Use the earlier independent E=0.8/1.6/2.4 GPa sensitivity (deflection multipliers 2/1/0.667) and 5/10/20/30 MPa normal-strength scenarios only to expose dependence, never as material allowables. Print direction, dense local sections, conditioning, layer bonds and warm creep need measured evidence. No infill factor, catalogue tensile result or heat-deflection temperature establishes a safe service temperature or factor of safety.

The nine original structural coupon pieces stay separate from nine production camera parts. A preliminary regular-grid open-edge plenum coupon STEP/STL is generated separately, with its source receipt in `../vent-study/shadow-plenum-coupon/receipt.json`; it is not print-released, sliced or tested. Open cut edges allow access absent in the closed plenum, and that crop omits ports, the CSI sleeve and some post exclusions. The second generated crop spans X−110..0 / Z0..100, nominal 110 × 100 × 10.1 mm, covering both port banks, the CSI sleeve, edge spans and the lower support row. Its receipt and the two-coupon index are in the same directory. It omits the complete rear region and does not prove a maximum global roof span. Both crops are valid saved-STEP single solids and have STEP/STL exports, but neither has been sliced, printed or tested. The two plenum coupons remain separate from the prior nine structural pieces. Record every stopped/failed test. Purchased BOM selections and quantities remain unchanged.
'''
    out['j4_lower_centres_file']='structural-review/j4-lower-centres.json'
    LAST_CENTRES.clear();LAST_CENTRES.update(note='J4 lower rows: centre of mass of each manifest-bound STEP (check_scope.'
                                             'lower_centres); first moment = manifest row mass x centre',variants=centres)
    return out,text
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    try:
        d,t=make();cen=dict(LAST_CENTRES)
    except AssertionError as e:   # FX: a refusal is a message and exit 1, not a traceback
        import sys;print('REFUSED: %s (nothing written)' % e,file=sys.stderr,flush=True);raise SystemExit(1)
    if args.check: assert d['ventilation_report']['same_manifest'], 'Ventilation report does not bind the selected manifest'
    outputs={'concealed-vent-structural.json':json.dumps(d,indent=2)+'\n','CONCEALED-VENT-STRUCTURAL.md':t,
             'j4-lower-centres.json':json.dumps(cen,indent=2)+'\n'}
    for n,content in outputs.items():
        if args.check: assert read_text(P/n)==content, f'Stale structural output: {n}'
        else: write_text(P/n,content)
    print(json.dumps({'manifest_sha256':d['manifest_sha256'],'mass_delta_g':d['assembly']['delta_mass_g'],'coupon_load':d['coupon_load'],'physical_qualified':False},indent=2))
