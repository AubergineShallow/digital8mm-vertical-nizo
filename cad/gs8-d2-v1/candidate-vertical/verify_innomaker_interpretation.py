#!/usr/bin/env python3
"""Bind staging caveats to completed Innomaker studies without altering their producer."""
from pathlib import Path
import argparse
import importlib.metadata
from cv_io import write_text
import json
import sys
from verify_innomaker_stl import sha, json_load, verify_bindings


def contains(outer,inner,eps=1e-7):
    return all(inner[k]>=outer[k]-eps and inner[k+1]<=outer[k+1]+eps for k in (0,2,4))


def translated(bounds,offset):
    return [bounds[i]+offset[i//2] for i in range(6)]


def main(argv=None):
    here=Path(__file__).resolve().parent;source=here.parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export',type=Path,default=here/'innomaker/out/compact-kowa_lm6hc',help='read-only export folder (input)')
    p.add_argument('--out',type=Path,default=here/'innomaker/checks/compact-kowa_lm6hc',help='folder holding the check reports; the addendum is written here')
    args=p.parse_args(argv);out=args.export.resolve();rd=args.out.resolve()
    if rd==out or out in rd.parents: raise ValueError('--out must be outside the export folder')
    mf=out/'manifest.json';m=json_load(mf);before=verify_bindings(m,source,out)
    inputs={'manifest.json':sha(mf),'innomaker-checks.json':sha(rd/'innomaker-checks.json'),'innomaker-stl-checks.json':sha(rd/'innomaker-stl-checks.json')}
    own=sha(__file__);r=json_load(rd/'innomaker-checks.json');stl=json_load(rd/'innomaker-stl-checks.json')
    assert r['manifest_sha256']==stl['manifest_sha256']==inputs['manifest.json']
    assert r['validator_sha256']==sha(here/'verify_innomaker.py')
    assert r['stl_helper_sha256']==sha(here/'verify_innomaker_stl.py')
    assert stl['validator_sha256']==sha(here/'verify_innomaker_stl.py')
    if importlib.metadata.version('cadquery')!='2.6.1': raise RuntimeError('CadQuery 2.6.1 required')
    import cadquery as cq
    import innomaker_geometry as IG
    from verify_innomaker import bb, regularize
    envelope,cert=regularize(IG.service_envelope(),'addendum service envelope')
    converter=cq.importers.importStep(str(out/'step/c_cs_adapter.step')).val()
    mover,mover_cert=regularize([envelope,converter],'addendum camera+converter envelope')
    mover_bounds=bb(mover);region=r['fixed_scene_crop']['bounds_mm']
    path=next(c for c in r['checks'] if c['name']=='44_discrete_camera_converter_approach_poses')
    pose_rows=[dict(index=p['index'],inside=contains(region,translated(mover_bounds,p['offset_mm']))) for p in path['rows']]
    header_rows=[]
    for family in ('cases','opposite_CSI_half_board_cases'):
        for case in r['header_sensitivity'][family]:
            rel=case['assumption_STEP'];assert sha(rd/rel)==case['assumption_STEP_sha256']
            header_rows.append(dict(region=case['region'],projection_mm=case['assumed_rear_projection_mm'],
                installed_inside=contains(region,case['bounds_mm']),
                all_44_poses_inside=all(contains(region,translated(case['bounds_mm'],p['offset_mm'])) for p in case['approach'])))
    crop_ok=all(p['inside'] for p in pose_rows) and all(p['installed_inside'] and p['all_44_poses_inside'] for p in header_rows)
    if not crop_ok: raise ValueError('Padded fixed-scene crop does not contain every sampled mover')
    after=verify_bindings(m,source,out)
    assert before==after and sha(mf)==inputs['manifest.json'] and all(sha(rd/n)==h for n,h in inputs.items() if n!='manifest.json') and sha(__file__)==own
    assert r['validator_sha256']==sha(here/'verify_innomaker.py') and r['stl_helper_sha256']==sha(here/'verify_innomaker_stl.py')
    data=dict(status='INTERPRETATION ADDENDUM; qualification remains HOLD',physical_qualified=False,
        input_sha256=inputs,producer='verify_innomaker_interpretation.py',producer_sha256=own,
        validator_source_sha256=r['validator_sha256'],all_manifest_bindings_rechecked=True,
        saved_geometry_scope='Complete saved public-STEP camera, rear headers omitted. The rear trigger/strobe headers (named in the manufacturer docs; photograph not committed) have unknown dimensions and positions; no actual camera/header clearance is qualified.',
        approach_scope={
            'computed':'44 discrete camera+converter poses, lens and removable panel/finishing hardware absent, no flexible cables; carrier/Pi/cooler/UPS module deliberately remains in the fixed obstacle set.',
            'actual_guide_sequence':'The guide inserts the camera while the carrier/module is out. Retaining that module in the screen is an extra-conservative obstruction condition for this camera-only operation.',
            'computed_removed_material':path['absent'],
            'computed_fixed_material':path['obstacles'],
            'interpretation':'A clear camera screen supports only the specified sampled rigid poses. A hypothetical header-prism collision with the extra-retained module does not demonstrate failure of the actual module-out camera insertion sequence.',
            'not_verified':['Continuous motion between samples','Later carrier/module insertion around the installed camera and actual headers','Complete linked camera+FPC+module assembly path','Flexible cables, latch motion, force, hand/tool access and physical assembly']},
        header_interpretation={
            'permanent_status':'HOLD: actual header height/XY remain unknown',
            'full_board':'All six full-PCB-area rear prisms intersect the +Y rear panel catches. This is a deliberately broad XY assumption and does not prove actual opposite-CSI headers collide.',
            'opposite_CSI_half_board':'The six additional prisms assume global Y -19.5..0 and Z40.5..79.5. These are not measured pin bounds. No installed intersection appears for these assumed3/6/9/12/15mm projections; assumed18mm overlaps Pi material. These results are not permissible pin-height limits.',
            'approach':'Assumed rear projections9mm and greater encounter the extra-retained module in sampled approach poses. Read these as a staging sensitivity, not a failure of the actual module-out insertion instruction.',
            'no_modification_authorized_or_assumed':'No shortening, bending, removal or relocation of actual headers is assumed.'},
        geometric_method={
            'no_optional_whole_obstacle_distance':'Minimum separation to every complete obstacle was not computed. Static PASS means exact per-solid intersection sum is within the reported1e-6mm3 tolerance. The0.5mm nominal PCB/guide gap was separately computed.',
            'intersection_method':'Exact individual-solid Booleans after clipping fixed solids to a padded region enclosing all sampled moving geometry; no overlapping compound is used as a single Boolean operand.',
            'crop_containment_verified':crop_ok,'crop_bounds_mm':region,'camera_converter_union_bounds_mm':mover_bounds,
            'camera_converter_pose_checks':pose_rows,'header_case_checks':header_rows,
            'service_union_certificate':cert,'mover_union_certificate':mover_cert},
        guide_interpretation='The roll and axial checks establish unloaded nominal kinematic contact only. They do not establish holder/lens torque support, catch strength, retention force, PCB strain or tolerance fit.',
        print_interpretation={'production_STLs_checked':stl['production_print_count'],'centring_gauge_STLs_checked':stl['centring_gauge_count'],
            'limits':'Edge/vertex-link topology and bounds checks are not a self-intersection analysis, slicer review or physical print release.'},
        historical='Earlier32 checks were not reused. Original QT -23.99mm remains a historical FAIL; this camera fork does not repair or rerun it.',
        gating_failures=r.get('failing_checks',[]),
        surviving_holds=r['holds'])
    target=rd/'innomaker-interpretation.json';write_text(target,json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'HOLD','crop_containment':'PASS','report':target.name,'sha256':sha(target)}))

if __name__=='__main__':main()
