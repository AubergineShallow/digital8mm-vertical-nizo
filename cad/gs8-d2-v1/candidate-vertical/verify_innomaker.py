#!/usr/bin/env python3
"""Scoped saved-STEP checks for the experimental Innomaker camera fork.

Requires CadQuery 2.6.1. Reads final manifest/STEP, never rebuilds the assembly.
Every manifest source/file hash is checked before CAD imports and again at end.
Earlier 32-check results are historical only; this run supplies fresh evidence.
Exit 0 means these bounded computational checks passed, NEVER release approval.

Input and output are separate (2026-10-13 fix pass): --export is the read-only export folder; the report and the
assumption-only header-study STEPs go to --out, which must not be the export folder. Rows that cannot fail
(bookkeeping, certificates whose failure aborts the run) are reported as INFO and are not counted as passes.
Gating rows added in that pass FAIL until the geometry or measured data fixes them: lens/converter/camera
interference (thread proxy), J7 float centring stack (official r7 rule), C-flange to sensor plane, image
orientation, lens-torque reaction before PCB contact, board outline versus the product page.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import traceback
from verify_innomaker_stl import json_load, sha, safe_path, verify_bindings
from cv_io import write_text

SOURCE_SHA256 = '3d53cc2b16f4c4bd91776e57548dcf191689a6d4f7ee4962411cfb3f1b496b51'
VOLUME_EPS_MM3 = 1e-6
BOUNDS_EPS_MM = 1e-5
HEADER_HEIGHTS_MM = [3, 6, 9, 12, 15, 18]
PANEL_REMOVAL_GROUP = ['panel','encoder','knob_exp','power_button','power_nut_reserve',
                       'p_panel1','p_panel2','p_panel3','p_panel4',
                       'knob_fps','fps_nut','fps_mounting_washer']
ROLL_ANGLES_DEG = [-2.,-1.5,-1.,-.5,0.,.5,1.,1.5,2.]
STATIC_TARGETS = ['tub','panel','carrier','pi5','cooler','x1203','x1203_kit',
                  'lens_collar','power_button','power_nut_reserve','xt30_pair','pack','base_grip',
                  's_c1','s_c2','s_c3','s_c4']
# Official r7 J7 float rule (checks.py J7_RUNNING/J7_TOL, layout.py COLLAR gauge centring_worst_mm,
# layout.py HOOD_TO_TUB_LATERAL reused for the removable panel per j7_collar_checks.LOCATION_EXTRA).
# Read from the official modules at run time; these literals only document the values at 2026-10-13.
J7_DOC_VALUES = dict(running_mm=.1, tol_mm=1e-3, centring_worst_mm=.30, panel_location_mm=.25)
# C-mount flange focal distance (standard, in air). No sensor plane has been verified for this camera.
C_MOUNT_FLANGE_FOCAL_MM = 17.526
# Product page (cam-imx296color, read 2026-10-13): 'Board Size 38mm x 38mm'. The STEP is 39 x 39 mm.
PRODUCT_PAGE_BOARD_MM = (38., 38.)
HOLDS = [
    'Optical stack, actual sensor plane and focus/infinity: HOLD; native Z13.2 is an unverified intended CS datum.',
    'Solid 4 exclusion as a removable source cap: HOLD until the supplied physical part is identified.',
    'Actual C-CS converter dimensions and thread engagement: HOLD.',
    'Lens/thread proxy overlap: HOLD; nominal overlapping thread volumes are not proof of engagement or clearance.',
    'Holder-supported lens assembly, retention, stiffness and torque reaction: HOLD.',
    'PCB strain, guide fit and force under assembly/use: HOLD.',
    'Full CSI connector/latch, FPC and flexible loom: HOLD; service reserve is only a declared coarse keepout.',
    'Two rear 2-pin headers (named in the manufacturer docs; seen in a photograph supplied with the delivery, not committed) are absent from source STEP; actual heights and XY locations unknown: HOLD.',
    'Rear-prism sensitivity cannot qualify actual header clearance, even when every assumed prism passes: HOLD.',
    'Physical fit, printing, assembly, electrical function, camera drivers and software qualification: HOLD.',
]


def bb(shape):
    b=shape.BoundingBox()
    return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]


def bbox_overlap(a,b):
    return all(min(a[k+1],b[k+1])-max(a[k],b[k])>0. for k in (0,2,4))


def bbox_distance(a,b):
    return math.sqrt(sum(max(a[k]-b[k+1],b[k]-a[k+1],0.)**2 for k in (0,2,4)))


def shape_of(value):
    if hasattr(value,'Solids'): return value
    if hasattr(value,'val'): return value.val()
    raise TypeError('Expected a CadQuery Shape or Workplane, got '+type(value).__name__)


def solids_of(value):
    if isinstance(value,dict):
        out=[]
        for v in value.values(): out.extend(solids_of(v))
        return out
    if isinstance(value,(list,tuple)):
        out=[]
        for v in value: out.extend(solids_of(v))
        return out
    return list(shape_of(value).Solids())


def common_components(a,b,eps=VOLUME_EPS_MM3):
    """Intersect individual solids only. Never pass an overlapping compound to OCCT.

    Positive sums may double count named source components; zero proves all
    tested component intersections were within tolerance. Quantities are not
    represented as occupied-material volume unless both operands are disjoint.
    """
    aa=solids_of(a); bbs=[(s,bb(s)) for s in solids_of(b)]
    total=0.; calls=0; contacts=[]
    for ia,s in enumerate(aa):
        ab=bb(s)
        for ib,(t,tb) in enumerate(bbs):
            if not bbox_overlap(ab,tb): continue
            common=s.intersect(t); calls+=1
            v=sum(abs(u.Volume()) for u in common.Solids())
            if not math.isfinite(v): raise ValueError('Nonfinite Boolean volume')
            total+=v
            if v>eps: contacts.append({'a_solid':ia,'b_solid':ib,'volume_mm3':v})
    return dict(component_overlap_sum_mm3=total,exact_intersection_calls=calls,
                hits=contacts,clear=total<=eps,
                volume_semantics='sum of per-solid intersections; may double-count source assemblies')


def distance_components(a,b):
    pairs=[]
    for s in solids_of(a):
        sb=bb(s)
        for t in solids_of(b): pairs.append((bbox_distance(sb,bb(t)),s,t))
    pairs.sort(key=lambda x:x[0]);best=float('inf');calls=0
    for lower,s,t in pairs:
        if lower>best+BOUNDS_EPS_MM: break
        best=min(best,float(s.distance(t)));calls+=1
        if best<=1e-9: break
    if not math.isfinite(best): raise ValueError('Distance requires nonempty solid operands')
    return best,calls


def regularize(value,label):
    """Fuse then clean into a valid union and prove resulting solids disjoint."""
    ss=solids_of(value)
    if not ss or any(not s.isValid() or s.Volume()<=0 for s in ss):
        raise ValueError(label+': invalid/empty input solid')
    result=ss[0].fuse(*ss[1:]).clean() if len(ss)>1 else ss[0].clean()
    output=list(result.Solids())
    if not result.isValid() or not output or any(not s.isValid() or s.Volume()<=0 for s in output):
        raise ValueError(label+': fuse/clean did not create a valid union')
    overlap=0.
    for i,a in enumerate(output):
        for b in output[i+1:]: overlap+=common_components(a,b)['component_overlap_sum_mm3']
    if overlap>VOLUME_EPS_MM3: raise ValueError(label+': output solids still overlap')
    uncovered=uncovered_volume(ss,output)
    if uncovered>VOLUME_EPS_MM3: raise ValueError(label+': union lost original material')
    return result,dict(label=label,input_solids=len(ss),output_solids=len(output),valid_union=True,
                       output_pair_overlap_mm3=overlap,input_uncovered_mm3=uncovered)


def uncovered_volume(a,b):
    """Sequential cuts by individual solids avoid compound boolean ambiguity."""
    cutters=solids_of(b); total=0.
    for source in solids_of(a):
        remainder=source
        source_bb=bb(source)
        ordered=sorted(cutters,key=lambda c:(max(abs(x-y) for x,y in zip(source_bb,bb(c)))>BOUNDS_EPS_MM,-c.Volume()))
        for cutter in ordered:
            if not remainder.Solids(): break
            if bbox_overlap(bb(remainder),bb(cutter)):
                remainder=remainder.cut(cutter)
        total+=sum(abs(s.Volume()) for s in remainder.Solids())
    return total


def named_guide_boxes(value,label):
    if isinstance(value,dict):
        out=[]
        for key,v in value.items(): out.extend(named_guide_boxes(v,label+'/'+str(key)))
        return out
    if isinstance(value,(list,tuple)):
        out=[]
        for i,v in enumerate(value): out.extend(named_guide_boxes(v,label+'/'+str(i)))
        return out
    return [(label+'/'+str(i),s) for i,s in enumerate(solids_of(value))]



def region_contains_bounds(region,bounds):
    if len(region)!=6 or len(bounds)!=6 or not all(math.isfinite(v) for v in list(region)+list(bounds)):
        return False
    if any(region[k]>=region[k+1] or bounds[k]>=bounds[k+1] for k in (0,2,4)):
        return False
    return all(bounds[k]>=region[k]-1e-7 and bounds[k+1]<=region[k+1]+1e-7 for k in (0,2,4))


def require_region_bounds(region,bounds,label):
    if not region_contains_bounds(region,bounds):
        raise ValueError(label+': nonfinite/invalid bounds or moving material extends outside exact-crop region')


def crop_fixed_scene(shapes,bounds):
    import cadquery as cq
    require_region_bounds(bounds,bounds,'crop region')
    cutter=cq.Solid.makeBox(bounds[1]-bounds[0],bounds[3]-bounds[2],bounds[5]-bounds[4],cq.Vector(bounds[0],bounds[2],bounds[4]))
    cropped={};certificates=[]
    for name,shape in shapes.items():
        retained=[];calls=0;original=solids_of(shape)
        for solid in original:
            b=bb(solid)
            if not bbox_overlap(b,bounds): continue
            if all(b[k]>=bounds[k] and b[k+1]<=bounds[k+1] for k in (0,2,4)):
                retained.append(solid)
            else:
                fragment=solid.intersect(cutter);calls+=1
                retained.extend(fragment.Solids())
        if any(not q.isValid() for q in retained): raise ValueError('Invalid cropped fixed solid: '+name)
        if retained: cropped[name]=cq.Compound.makeCompound(retained)
        certificates.append(dict(id=name,source_solids=len(original),cropped_solids=len(retained),exact_crop_calls=calls))
    return cropped,dict(bounds_mm=bounds,padding_mm=.01,rows=certificates,
        scope='Exact individual-solid intersections with a padded box enclosing every installed and sampled camera/converter/header position. Only outside-box fixed material is excluded; original STEP files stay unchanged. No cropped compound is passed to a Boolean as a whole.')


def scene_hit(moving,scene,name,region):
    require_region_bounds(region,bb(moving),'static mover vs '+name)
    if name not in scene:
        return dict(clear=True,component_overlap_sum_mm3=0.,exact_intersection_calls=0,hits=[],
                    volume_semantics='No fixed material in padded region enclosing moving geometry')
    return common_components(moving,scene[name])

def insertion_poses():
    poses=[dict(index=i,leg='Y approach',offset_mm=[-6.2,float(y),0.]) for i,y in enumerate(range(60,-1,-2))]
    for i in range(1,14):
        poses.append(dict(index=len(poses),leg='X seat',offset_mm=[0. if i==13 else -6.2+6.2*i/13.,0.,0.]))
    assert len(poses)==44 and len({tuple(p['offset_mm']) for p in poses})==44
    return poses


def screen_mover(mover,obstacles,poses,clip_bounds=None):
    rows=[]
    fixed_bounds={name:bb(s) for name,s in obstacles.items()}
    for pose in poses:
        moving=shape_of(mover).translate(tuple(pose['offset_mm'])); hits=[]; calls=0
        moving_bounds=bb(moving)
        if clip_bounds is not None: require_region_bounds(clip_bounds,moving_bounds,'actual sampled mover '+str(pose['index']))
        for name,fixed in obstacles.items():
            if not bbox_overlap(moving_bounds,fixed_bounds[name]): continue
            r=common_components(moving,fixed);calls+=r['exact_intersection_calls']
            if not r['clear']: hits.append(dict(fixed=name,**r))
        rows.append(dict(**pose,status='PASS' if not hits else 'FAIL',hits=hits,exact_intersection_calls=calls,moving_bounds_mm=moving_bounds,crop_bounds_containment_checked=clip_bounds is not None))
    return rows


def require_module_binding(module,manifest,source_root):
    path=Path(module.__file__).resolve()
    rel=path.relative_to(source_root).as_posix()
    if manifest['sources'].get(rel)!=sha(path): raise ValueError('Imported module not bound by final manifest: '+rel)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);here=Path(__file__).resolve().parent
    p.add_argument('--cad-dir',type=Path,default=here.parent)
    p.add_argument('--export',type=Path,default=here/'innomaker/out/compact-kowa_lm6hc',help='read-only export folder (input)')
    p.add_argument('--out',type=Path,default=here/'innomaker/checks/compact-kowa_lm6hc',help='report and study output folder; never the export folder')
    p.add_argument('--manifest',default='manifest.json');p.add_argument('--module',default='innomaker_geometry')
    p.add_argument('--report',type=Path)
    args=p.parse_args(argv);out=args.export.resolve();source=args.cad_dir.resolve();mf=out/args.manifest
    report_dir=args.out.resolve()
    if report_dir==out or out in report_dir.parents or report_dir in out.parents:
        raise ValueError('--out must be outside the export folder (and not contain it); the verifier never writes into its input')
    initial=sha(mf);manifest=json_load(mf)
    before=verify_bindings(manifest,source,out)
    self_hash=sha(__file__);helper_hash=sha(Path(__file__).with_name('verify_innomaker_stl.py'))
    if importlib.metadata.version('cadquery')!='2.6.1': raise RuntimeError('CadQuery 2.6.1 is required; no validation was run')
    import cadquery as cq
    sys.path.insert(0,str(source/'candidate-vertical'));sys.path.insert(1,str(source))
    IG=importlib.import_module(args.module);require_module_binding(IG,manifest,source)
    source_file=Path(IG.SOURCE).resolve()
    if sha(source_file)!=SOURCE_SHA256 or IG.SHA256!=SOURCE_SHA256:
        raise ValueError('Innomaker source must match independently recorded SHA-256')
    source_rel=source_file.relative_to(source).as_posix()
    if manifest['sources'].get(source_rel)!=SOURCE_SHA256: raise ValueError('Innomaker source STEP absent from manifest source binding')
    checks=[]
    def check(name,ok,**details):
        row=dict(name=name,status='PASS' if ok else 'FAIL',**details);checks.append(row)
        print(json.dumps({'check':name,'status':row['status']}),flush=True)
        return row
    def info(name,**details):
        # Cannot fail: bookkeeping or a certificate whose failure raises. Reported, never counted as a pass.
        row=dict(name=name,status='INFO',**details);checks.append(row)
        print(json.dumps({'check':name,'status':'INFO'}),flush=True)
        return row
    info('manifest_input_hashes_start',sources=len(manifest['sources']),files=len(manifest['files']),note='bookkeeping; bindings are verified (raising on mismatch) before this row')
    check('pinned_cadquery_runtime',cq.__version__=='2.6.1',cadquery=cq.__version__,cadquery_ocp=importlib.metadata.version('cadquery-ocp'))
    saved={};geometry=[]
    for row in manifest['rows']:
        name=row['id']
        if name in saved: raise ValueError('Duplicate saved row: '+name)
        rel='step/'+name+'.step'
        if rel not in manifest['files']: raise ValueError('Unbound saved STEP: '+name)
        s=cq.importers.importStep(str(safe_path(out,rel))).val();ss=s.Solids()
        # Exporter records BoundingBox after tessellate(.07,.15), which can
        # differ from an unmeshed analytic BRep box. Reproduce its convention.
        analytic_bounds=bb(s);s.tessellate(.07,.15);bounds=bb(s)
        match=all(abs(a-b)<=BOUNDS_EPS_MM for a,b in zip(bounds,row['bbox_mm']))
        valid=bool(ss) and s.isValid() and all(x.isValid() and x.Volume()>0 for x in ss)
        geometry.append(dict(id=name,valid=valid,solid_count=len(ss),recorded_solid_count=row.get('solid_count'),
                             solid_count_matches=len(ss)==row.get('solid_count'),bounds_mm=bounds,analytic_bounds_mm=analytic_bounds,bounds_match=match,bounds_convention='CadQuery tessellate(0.07,0.15) then BoundingBox'))
        saved[name]=s
    check('saved_STEP_rows_integrity',all(r['valid'] and r['solid_count_matches'] and r['bounds_match'] for r in geometry),rows=geometry)
    missing=set(STATIC_TARGETS+['gs_camera','c_cs_adapter','camera_csi_service_reserve','lens'])-saved.keys()
    if missing: raise ValueError('Required saved geometry missing: '+repr(sorted(missing)))
    camera=saved['gs_camera'];converter=saved['c_cs_adapter']
    source_raw=cq.importers.importStep(str(source_file)).val();source_solids=source_raw.Solids()
    check('source_identity',sha(source_file)==SOURCE_SHA256 and len(source_solids)==29 and IG.CAP_SOLID_INDEX==4,sha256=SOURCE_SHA256,source_solids=len(source_solids),cap_excluded_index=4,cap_identification_status='HOLD')
    pcb_native=shape_of(IG.pcb_material());pcb=shape_of(IG.place(pcb_native));pbb=bb(pcb)
    check('placed_PCB_envelope',all(abs(a-b)<=BOUNDS_EPS_MM for a,b in zip([pbb[1]-pbb[0],pbb[3]-pbb[2],pbb[5]-pbb[4]],[1.6,39.,39.])),
          bounds_mm=pbb,expected_thickness_width_height_mm=[1.6,39,39],note='Declared/reconstructed PCB material, not measured hardware')
    # Independent data (review A-06/A-07, B-15): the manufacturer STEP's own overall in-plane extent, and the product page.
    placed_source_bb=bb(shape_of(IG.place(source_raw)))
    source_extent=[placed_source_bb[3]-placed_source_bb[2],placed_source_bb[5]-placed_source_bb[4]]
    check('placed_PCB_matches_manufacturer_STEP_extent',all(abs(a-b)<=BOUNDS_EPS_MM for a,b in zip([pbb[3]-pbb[2],pbb[5]-pbb[4]],source_extent)),
          pcb_width_height_mm=[pbb[3]-pbb[2],pbb[5]-pbb[4]],manufacturer_STEP_width_height_mm=source_extent,
          note='Compares the reconstructed PCB with the overall Y/Z extent of the placed manufacturer STEP, not with its own constants')
    check('board_outline_agrees_with_product_page',all(abs(a-b)<=BOUNDS_EPS_MM for a,b in zip(sorted([pbb[3]-pbb[2],pbb[5]-pbb[4]]),sorted(PRODUCT_PAGE_BOARD_MM))),
          model_width_height_mm=[pbb[3]-pbb[2],pbb[5]-pbb[4]],product_page_mm=list(PRODUCT_PAGE_BOARD_MM),
          status_note='OPEN measurement: product page 38 x 38 vs STEP 39 x 39. Stays FAIL until the received board is measured and the guides are re-derived.')
    check('placed_PCB_axis_centre',abs((pbb[2]+pbb[3])/2)<=BOUNDS_EPS_MM and abs((pbb[4]+pbb[5])/2-60)<=BOUNDS_EPS_MM,
          y_centre_mm=(pbb[2]+pbb[3])/2,z_centre_mm=(pbb[4]+pbb[5])/2)
    if len(source_solids)!=29: raise ValueError('Unexpected manufacturer source solid ordering/count')
    active_native=cq.Compound.makeCompound([s for i,s in enumerate(source_solids) if i!=4]+[pcb_native])
    placed_native=shape_of(IG.place(active_native))
    reference=cq.Workplane('XY').box(39,39,1.6,centered=(True,True,False)).translate((0,0,.9)).edges('|Z').fillet(3.5).val()
    hole_specs=[(x,y,1.) for x in (-17.,17.) for y in (-17.,17.)]+[(-10.,0.,1.),(10.,0.,1.),(10.,-3.5,.755),(-10.,3.5,.755)]
    hole_results=[]
    for x,y,r in hole_specs:
        cutter=cq.Solid.makeCylinder(r,1.8,cq.Vector(x,y,.8),cq.Vector(0,0,1))
        hole_results.append(dict(native_xy_mm=[x,y],diameter_mm=2*r,intersection=common_components(pcb_native,cutter)))
        reference=reference.cut(cutter)
    native_error=uncovered_volume(pcb_native,reference)+uncovered_volume(reference,pcb_native)
    check('reconstructed_PCB_R3p5_and_all_eight_holes',native_error<=VOLUME_EPS_MM3 and all(r['intersection']['clear'] for r in hole_results),
          symmetric_difference_sum_mm3=native_error,holes=hole_results,source_scope='Reconstructed substrate follows stated source-derived dimensions, not a measurement')
    mapped=[]
    for name,point,expected in [('CS_reference',(0,0,13.2),(-4.4,0,60)),('native_X',(1,0,0),(IG.AXIAL_OFFSET,0,61)),
                                 ('native_Y',(0,1,0),(IG.AXIAL_OFFSET,-1,60)),('native_Z',(0,0,1),(IG.AXIAL_OFFSET+1,0,60))]:
        probe=cq.Solid.makeBox(.2,.2,.2,cq.Vector(*(v-.1 for v in point)));centre=IG.place(probe).Center().toTuple()
        mapped.append(dict(label=name,native_point=list(point),actual=list(centre),expected=list(expected),
                           match=all(abs(a-b)<=BOUNDS_EPS_MM for a,b in zip(centre,expected))))
    check('axis_mapping_and_unverified_CS_reference',all(r['match'] for r in mapped),rows=mapped,optical_datum_status='HOLD')
    native_to_saved=uncovered_volume(placed_native,camera);saved_to_native=uncovered_volume(camera,placed_native)
    check('saved_camera_equals_active_placed_model',native_to_saved<=VOLUME_EPS_MM3 and saved_to_native<=VOLUME_EPS_MM3,
          model_uncovered_mm3=native_to_saved,saved_uncovered_mm3=saved_to_native)
    check('PCB_is_in_saved_camera',uncovered_volume(pcb,camera)<=VOLUME_EPS_MM3,uncovered_mm3=uncovered_volume(pcb,camera))
    guides={}
    for label,fun,parent in [('tub_guides',IG.tub_guides,'tub'),('panel_guides',IG.panel_guides,'panel')]:
        items=named_guide_boxes(fun(),label)
        if not items: raise ValueError('No individual guide boxes: '+label)
        individual=[]
        for name,box in items:
            missed=uncovered_volume(box,saved[parent])
            r=common_components(camera,box)
            individual.append(dict(name=name,bounds_mm=bb(box),outside_parent_mm3=missed,
                                   contained=missed<=VOLUME_EPS_MM3,camera_overlap=r))
        check(label+'_individual_integral_containment',all(x['contained'] for x in individual),boxes=individual,parent=parent)
        check(label+'_individual_camera_clearance',all(x['camera_overlap']['clear'] for x in individual))
        union,certificate=regularize([b for _,b in items],label)
        guides[label]=union
        info(label+'_regularized_disjoint_union',certificate=certificate,note='certificate; regularize() raises on an invalid or overlapping union')
        check(label+'_union_camera_clearance',common_components(camera,union)['clear'],intersection=common_components(camera,union))
    roll_rows=[]
    all_guides,roll_union_certificate=regularize(list(guides.values()),'all passive roll guides')
    zero_gap,zero_gap_calls=distance_components(pcb,all_guides)
    for angle in ROLL_ANGLES_DEG:
        rotated=pcb.rotate((0,0,60),(1,0,60),angle)
        contacts={name:common_components(rotated,guide) for name,guide in guides.items()}
        roll_rows.append(dict(angle_deg=angle,contacts=contacts,any_contact=any(not c['clear'] for c in contacts.values())))
    ideal_theta=math.pi/4-math.acos(16.5/(16*math.sqrt(2)))
    tangent_z=16*(math.cos(ideal_theta)-math.sin(ideal_theta))
    roll_ok=abs(zero_gap-.5)<=BOUNDS_EPS_MM and all(r['any_contact']==(abs(r['angle_deg'])==2.) for r in roll_rows)
    check('passive_roll_guides_unloaded_kinematics',roll_ok,rows=roll_rows,zero_roll_gap_mm=zero_gap,
          ideal_R3p5_PCB_rail_first_contact_deg=math.degrees(ideal_theta),ideal_tangent_Z_offset_mm=tangent_z,
          lower_guide_Z_mm=[40.1,46.],upper_guide_Z_mm=[74.,81.],union_certificate=roll_union_certificate,
          qualification='Kinematic unloaded safety-guide contact only; no torque reaction, load, preload, PCB strain or retention qualification')
    axial_rows=[]
    for dx in (-.75,-.51,-.5,-.25,0.,.25,.5,.51,.75):
        translated=pcb.translate((dx,0,0))
        contacts={name:common_components(translated,guide) for name,guide in guides.items()}
        axial_rows.append(dict(axial_offset_mm=dx,contacts=contacts,any_contact=any(not r['clear'] for r in contacts.values())))
    check('passive_axial_guides_unloaded_kinematics',all(r['any_contact']==(abs(r['axial_offset_mm'])>.5) for r in axial_rows),
          rows=axial_rows,nominal_axial_float_each_side_mm=.5,
          qualification='Unloaded nominal PCB/catch contact with panel installed only; no holding force, pull-out, PCB strain, preload, retention strength or lens load qualification')
    # A simplified service envelope is usable only after fusion and exact
    # saved-camera containment. No bounding-box substitution earns a pass.
    envelope,certificate=regularize(IG.service_envelope(),'camera service envelope')
    uncovered=uncovered_volume(camera,envelope)
    check('service_envelope_covers_exact_saved_camera',uncovered<=VOLUME_EPS_MM3,
          uncovered_mm3=uncovered,certificate=certificate,volume_tolerance_mm3=VOLUME_EPS_MM3)
    if uncovered>VOLUME_EPS_MM3: raise ValueError('Service envelope leaves saved camera material uncovered')
    mover,mover_cert=regularize([envelope,converter],'camera plus converter mover')
    poses=insertion_poses()
    camera_bounds=bb(camera);converter_bounds=bb(converter)
    screen_region=[pbb[0]-max(HEADER_HEIGHTS_MM)-6.2-.01,max(camera_bounds[1],converter_bounds[1])+.01,
                   min(pbb[2],camera_bounds[2],converter_bounds[2])-.01,max(pbb[3],camera_bounds[3],converter_bounds[3])+60.01,
                   min(pbb[4],camera_bounds[4],converter_bounds[4])-.01,max(pbb[5],camera_bounds[5],converter_bounds[5])+.01]
    crop_bound_checks=[]
    for label,shape in [('exact saved public-STEP camera',camera),('converter',converter),('service envelope',envelope),('camera+converter union',mover)]:
        shape_bounds=bb(shape)
        for pose in poses:
            moved_bounds=[shape_bounds[i]+pose['offset_mm'][i//2] for i in range(6)]
            crop_bound_checks.append(dict(moving=label,sample=pose['index'],contained=region_contains_bounds(screen_region,moved_bounds)))
            require_region_bounds(screen_region,moved_bounds,label+' sample '+str(pose['index']))
    for region_name in ('full_board','opposite_CSI_half_board'):
        for h in HEADER_HEIGHTS_MM:
            assumed=[pbb[0]-h,pbb[0],pbb[2],pbb[3] if region_name=='full_board' else 0.,pbb[4],pbb[5]]
            for pose in poses:
                moved_bounds=[assumed[i]+pose['offset_mm'][i//2] for i in range(6)]
                crop_bound_checks.append(dict(moving=region_name,assumed_projection_mm=h,sample=pose['index'],contained=region_contains_bounds(screen_region,moved_bounds)))
                require_region_bounds(screen_region,moved_bounds,region_name+' H'+str(h)+' sample '+str(pose['index']))
    crop_ok=all(r['contained'] for r in crop_bound_checks)
    if not crop_ok: raise ValueError('Planned sample outside fixed-scene crop')
    cropped_scene,crop_certificate=crop_fixed_scene(saved,screen_region)
    crop_certificate['planned_mover_bounds_checks']=crop_bound_checks
    crop_certificate['all_planned_mover_bounds_finite_and_contained']=crop_ok
    info('fixed_scene_exact_padded_crop',certificate=crop_certificate,note='precondition; a planned sample outside the crop raises before this row')
    static=[]
    for name in STATIC_TARGETS:
        hit=scene_hit(camera,cropped_scene,name,screen_region)
        static.append(dict(fixed=name,**hit))
        check('saved_public_STEP_camera_vs_'+name,hit['clear'],intersection=hit,scope='Complete saved public-STEP camera, rear headers omitted; exact per-solid interference only')
    reserve=saved['camera_csi_service_reserve'];reserve_hits=[]
    for name in STATIC_TARGETS:
        r=common_components(reserve,saved[name])
        reserve_hits.append(dict(fixed=name,**r))
    check('declared_CSI_reserve_static',all(r['clear'] for r in reserve_hits),rows=reserve_hits,qualification='HOLD; no full CSI/FPC/latch qualification')
    thread_rows=[]
    for a,b in [('gs_camera','c_cs_adapter'),('c_cs_adapter','lens'),('gs_camera','lens')]:
        r=common_components(saved[a],saved[b])
        thread_rows.append(dict(a=a,b=b,**r,status='PASS' if r['clear'] else 'FAIL'))
        # Gating (review A-02/B-04): the official j7_float lens_vs_camera rule fails on any overlap above tolerance.
        check('interference_'+a+'_vs_'+b,r['clear'],intersection=r,volume_tolerance_mm3=VOLUME_EPS_MM3,
              note='Thread-proxy overlap is counted as interference; no allowance until a measured holder/converter/lens stack removes it')
    for name in STATIC_TARGETS:
        hit=scene_hit(converter,cropped_scene,name,screen_region)
        check('converter_vs_'+name,hit['clear'],intersection=hit,scope='Installed conditional converter reservation; exact per-solid interference')
    # J7 float centring stack (review A-04): official r7 rule, remaining = gap - centring stack - location (panel) >= running.
    import checks as OCK
    import layout as OLY
    j7=dict(running_mm=OCK.J7_RUNNING,tol_mm=OCK.J7_TOL,centring_worst_mm=OLY.COLLAR['gauge']['centring_worst_mm'],panel_location_mm=OLY.HOOD_TO_TUB_LATERAL)
    # Distance to the obstacle cropped to the camera box padded by J7_CROP_PAD_MM: exact whenever the result is below
    # the pad (any closer material lies inside the padded box); otherwise the pad is a proven lower bound.
    J7_CROP_PAD_MM=2.
    cb=bb(camera);j7_region=[cb[0]-J7_CROP_PAD_MM,cb[1]+J7_CROP_PAD_MM,cb[2]-J7_CROP_PAD_MM,cb[3]+J7_CROP_PAD_MM,cb[4]-J7_CROP_PAD_MM,cb[5]+J7_CROP_PAD_MM]
    j7_near,j7_crop_cert=crop_fixed_scene({'tub':saved['tub'],'panel':saved['panel']},j7_region)
    for oid in ('tub','panel'):
        if oid in j7_near:
            gap,calls=distance_components(camera,j7_near[oid])
        else:
            gap,calls=float('inf'),0
        exact=gap<J7_CROP_PAD_MM
        gap=min(gap,J7_CROP_PAD_MM)
        extra=j7['panel_location_mm'] if oid=='panel' else 0.
        left=gap-j7['centring_worst_mm']-extra
        check('J7_float_centring_camera_vs_'+oid,left>=j7['running_mm']-j7['tol_mm'],min_distance_mm=gap,stack_mm=j7['centring_worst_mm'],
              location_extra_mm=extra,remaining_mm=left,rule='remaining >= %.2f mm'%j7['running_mm'],official_constants=j7,
              documented_constants_2026_10_13=J7_DOC_VALUES,distance_calls=calls,distance_exact=exact,crop_pad_mm=J7_CROP_PAD_MM,crop_certificate=j7_crop_cert,
              note='3-D minimum distance (never larger than the lateral gap the official tool uses, so not looser). Axial band of the unverified CS register not sampled: OPEN.')
    # C-flange to sensor plane (review B-01): no verified sensor plane, so this FAILs until the received holder is measured.
    sensor_plane=IG.provenance().get('sensor_active_plane_mm')
    check('C_flange_to_sensor_plane_verified',sensor_plane is not None and abs((IG.C_FLANGE_X-sensor_plane)-C_MOUNT_FLANGE_FOCAL_MM)<=.4,
          sensor_active_plane_mm=sensor_plane,c_flange_x_mm=IG.C_FLANGE_X,required_flange_focal_mm=C_MOUNT_FLANGE_FOCAL_MM,
          review_B_reading='die face at native Z 3.30 (review B reading of the STEP) would sit at X %.2f, %.2f mm behind the C flange under the holder-mouth convention'%(IG.AXIAL_OFFSET+3.30,IG.C_FLANGE_X-(IG.AXIAL_OFFSET+3.30)),
          note='OPEN: holder mouth used as CS reference is unverified; measure holder/ring on receipt, then re-derive AXIAL_OFFSET')
    # Image orientation (review B-02): the sensor long axis must be horizontal (global Y); place() maps native X to global Z.
    probe_x=IG.place(cq.Solid.makeBox(.2,.2,.2,cq.Vector(.9,-.1,-.1))).Center().toTuple();probe_o=IG.place(cq.Solid.makeBox(.2,.2,.2,cq.Vector(-.1,-.1,-.1))).Center().toTuple()
    long_axis=[a-b for a,b in zip(probe_x,probe_o)]
    check('sensor_long_axis_horizontal',abs(long_axis[1])>abs(long_axis[2]) and abs(long_axis[1])>abs(long_axis[0]),
          native_long_axis='X (review B reading of the STEP sensor package 11 x 9 mm and connector; confirm with one bench capture)',
          placed_long_axis_vector=long_axis,note='Global Z = vertical: a portrait 1088 x 1456 frame; the imx296 overlay rotates only 0/180')
    # J7-R lens torque (review A-03/B-03): official layout.ROLL_CATCH needs a holder/metal reaction before PCB contact (+1.0 deg).
    reaction=getattr(IG,'LENS_TORQUE_REACTION',None)
    check('lens_torque_reaction_before_PCB_contact',reaction is not None,lens_torque_reaction=reaction,
          official_rule='layout.ROLL_CATCH: 0.5 N.m; PCB first contact >= metal contact + %.1f deg'%OLY.ROLL_CATCH['margin_deg'],
          first_contact='PCB corner on printed guides (ideal R3.5 first contact about 1.82 deg; see passive_roll_guides_unloaded_kinematics)',
          note='USER DECISION: lens-hold design (printed fixture on the metal holder/converter, flats, or threading the lens off-camera). Not buildable under J7-R until then.')
    row_kinds={r['id']:r['kind'] for r in manifest['rows']}
    cable_rows={name for name in saved if 'cable' in name.lower() or 'wire' in name.lower() or 'fpc' in name.lower()}
    absent={'gs_camera','c_cs_adapter','lens'}|set(PANEL_REMOVAL_GROUP)|cable_rows
    keepouts={name:s for name,s in saved.items() if row_kinds[name]=='keepout' and name!='camera_csi_service_reserve'}
    obstacle_names={name for name in saved if name not in absent and row_kinds[name]!='keepout'}
    obstacles={name:s for name,s in cropped_scene.items() if name in obstacle_names}
    # Exclusions are explicit: the removable panel/associated finishing hardware,
    # lens, cables and moving camera/converter. All other material rows stay.
    approach=screen_mover(mover,obstacles,poses,screen_region)
    keepout_static={name:common_components(camera,s) for name,s in keepouts.items()}
    keepout_approach=screen_mover(mover,keepouts,poses,screen_region)
    keepout_diagnostics=dict(static=keepout_static,approach=keepout_approach,
        status='PASS' if all(r['clear'] for r in keepout_static.values()) and all(r['status']=='PASS' for r in keepout_approach) else 'FAIL',
        note='Non-material reservation intersections screened separately; no keepout counted as a physical obstacle. Own moving CSI reserve is checked separately in installed pose.')
    check('44_discrete_camera_converter_approach_poses',all(r['status']=='PASS' for r in approach),
          pose_count=44,rows=approach,mover_certificate=mover_cert,obstacles=sorted(obstacle_names),obstacles_with_material_in_screen_region=sorted(obstacles),
          absent=sorted(absent),panel_and_finishing_hardware_removed=PANEL_REMOVAL_GROUP,cable_rows_absent=sorted(cable_rows),nonmaterial_keepouts_separate=sorted(keepouts),continuous_sweep=False,qualification='Discrete pose test only, lens/panel/cables absent; no installation release')
    header_cases=[]
    import export_cache as EC
    study_dir=report_dir/'header-sensitivity';study_dir.mkdir(parents=True,exist_ok=True)
    study_files={}
    for region,h in [(region,h) for region in ('full_board','opposite_CSI_half_board') for h in HEADER_HEIGHTS_MM]:
        # Worst-case full rectangular PCB area: does not infer either header's
        # actual XY location, pin count geometry or nominal manufacturer height.
        assumed_y_high=pbb[3] if region=='full_board' else 0.
        prism=cq.Solid.makeBox(h,assumed_y_high-pbb[2],pbb[5]-pbb[4],cq.Vector(pbb[0]-h,pbb[2],pbb[4]))
        # Short names (repo path-length limit); the ASSUMPTION-ONLY label lives in the report rows.
        study_rel='header-sensitivity/hs-%s-H%02d.step'%('full' if region=='full_board' else 'half',h)
        study_path=report_dir/study_rel
        EC.export_step(prism,study_path)
        study_files[study_rel]=sha(study_path)
        installed=[]
        for name in STATIC_TARGETS:
            r=scene_hit(prism,cropped_scene,name,screen_region);installed.append(dict(fixed=name,**r))
        swept=screen_mover(prism,obstacles,poses,screen_region)
        hit_rows=[r for r in swept if r['status']=='FAIL']
        header_cases.append(dict(region=region,assumed_rear_projection_mm=h,bounds_mm=bb(prism),assumption_STEP=study_rel,assumption_STEP_sha256=study_files[study_rel],
            geometry_assumption=('Full PCB-area rectangular prism' if region=='full_board' else 'Assumed opposite-CSI half-board rectangular prism, global Y -19.5..0 and Z40.5..79.5')+'; PCB_REAR_X-H to PCB_REAR_X; unknown real header height and XY positions; bounds are assumed, not manufacturer dimensions' ,
            installed_assumed_prism_clear=all(r['clear'] for r in installed),installed=installed,
            approach_assumed_prism_clear=not hit_rows,approach= swept,
            actual_header_clearance_qualified=False,actual_header_status='HOLD'))
        print(json.dumps({'header_region':region,'header_assumption_mm':h,'installed_prism_clear':header_cases[-1]['installed_assumed_prism_clear'],
                          'approach_prism_clear':not hit_rows,'actual_headers':'HOLD'}),flush=True)
    if any(sha(report_dir/rel)!=digest for rel,digest in study_files.items()): raise ValueError('Header study STEP changed during validation')
    after=verify_bindings(manifest,source,out)
    unchanged=before==after and sha(mf)==initial and sha(__file__)==self_hash and sha(Path(__file__).with_name('verify_innomaker_stl.py'))==helper_hash
    check('all_source_file_and_validator_hashes_unchanged_at_end',unchanged)
    if not unchanged: raise ValueError('Manifest/source/file/validator changed during verification')
    result=dict(status='PASS' if all(r['status'] in ('PASS','INFO') for r in checks) else 'FAIL',
        qualification_status='HOLD',physical_qualified=False,utc='UNRECORDED (deterministic report)',
        scope='Fresh scoped saved-STEP checks, static complete saved public-STEP camera intersections (rear headers omitted) and 44 discrete camera+converter poses; not full release qualification.',
        manifest_sha256=initial,validator_sha256=self_hash,stl_helper_sha256=helper_hash,
        runtime={'python':sys.version.split()[0],'cadquery':cq.__version__,'cadquery_ocp':importlib.metadata.version('cadquery-ocp')},
        volume_epsilon_mm3=VOLUME_EPS_MM3,bounds_epsilon_mm=BOUNDS_EPS_MM,
        checked_source_count=len(manifest['sources']),checked_file_count=len(manifest['files']),
        source_file_hashes_before=before,source_file_hashes_after=after,all_bindings_rechecked_at_end=True,
        check_count=len(checks),pass_count=sum(r['status']=='PASS' for r in checks),fail_count=sum(r['status']=='FAIL' for r in checks),info_count=sum(r['status']=='INFO' for r in checks),
        failing_checks=[r['name'] for r in checks if r['status']=='FAIL'],
        checks=checks,fixed_scene_crop=crop_certificate,thread_proxy_diagnostics=thread_rows,nonmaterial_keepout_diagnostics=keepout_diagnostics,
        export_folder_read_only=True,
        header_sensitivity={'status':'HOLD','cases':[r for r in header_cases if r['region']=='full_board'],'opposite_CSI_half_board_cases':[r for r in header_cases if r['region']=='opposite_CSI_half_board'],'study_files_sha256':study_files,'study_files_rechecked_at_end':True,'actual_header_height_known':False,'actual_header_XY_known':False,
            'clearance_qualified':False,'interpretation':'Assumption-only full-board and opposite-CSI half-board prism sensitivities. Neither bounds real header XY or height. A pass does not qualify real headers. A collision does not prove real headers collide because the assumed prism occupies much more area than the actual pins. No header study geometry is exported into the assembly.'},
        historical={'previous_32_checks':'Historical only; not reused as current evidence',
                    'original_QT_mm':-23.99,'original_QT_status':'FAIL','note':'Original QT result is retained as historical failure, not rerun or repaired by this camera-only fork.'},
        holds=HOLDS,provenance=IG.provenance())
    target=(args.report or report_dir/'innomaker-checks.json').resolve()
    if target==out or out in target.parents: raise ValueError('Report must be written outside the export folder')
    bound=[mf.resolve(),Path(__file__).resolve(),Path(__file__).with_name('verify_innomaker_stl.py').resolve()]+[safe_path(out,r) for r in manifest['files']]+[safe_path(source,r,source.parent) for r in manifest['sources']]
    if target in bound: raise ValueError('Report must not overwrite a bound input')
    target.parent.mkdir(parents=True,exist_ok=True);write_text(target,json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'qualification':'HOLD','checks':len(checks),'fails':result['failing_checks'],'report':target.name}),flush=True)
    return int(result['status']!='PASS')


if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);traceback.print_exc();raise SystemExit(2)
