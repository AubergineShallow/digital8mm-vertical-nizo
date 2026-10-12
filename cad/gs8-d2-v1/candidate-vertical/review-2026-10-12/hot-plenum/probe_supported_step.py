"""Narrow upper front exit with existing row49 continued as a bridge-support mullion."""
import sys,json,time
from pathlib import Path
CV=Path(__file__).resolve().parents[2];sys.path.insert(0,str(CV))
from cv_io import write_text
sys.path.insert(0,str(Path(__file__).parent/'baseline'))
import vent_geometry as VG
import plenum_flow as PF
base_frame=PF.nominal_frame_boxes;base_bays=PF.bays;base_rows=VG.hot_rows
rows=[]
for top,depth in [(58.,2.5),(60.,2.5),(62.,2.5),(58.,3.),(60.,3.)]:
 def bays(length):
    b=base_bays(length);b['hot']['mouths']['hot_front']=('x_max',5.,top);return b
 def frame(vg,length):
    b=base_frame(vg,length)
    b=[(q[0],q[1],q[2],q[3],top,q[5]) if q[:2]==(-2.5,0) and q[4]==40 else q for q in b]
    b.append((-2.5,0.,-34.+depth,VG.RIB_Y[1],49.,top))
    b.append((-2.6,0.,*VG.RIB_Y,48.4,49.6))
    return b
 def hot_rows(length):
    return [(z,[(a,0. if z==49. else b) for a,b in segs]) for z,segs in base_rows(length)]
 PF.bays=bays;PF.nominal_frame_boxes=frame;VG.hot_rows=hot_rows
 s=time.monotonic();r=PF.nominal_min_cut(VG,158.,'hot')
 row=dict(full_height_top=49.,front_top=top,outer_gap_depth=depth,mullions=[21.,49.],min_cut=r['min_cut_mm2'],mouths=r['mouth_face_mm2'],cut_bbox=r['internal_cut_bbox_xz'],seconds=time.monotonic()-s)
 print(json.dumps(row),flush=True);rows.append(row)
write_text(Path(__file__).with_suffix('.json'),json.dumps(rows,indent=2)+'\n')
# Validate the smallest 2.5mm-deep supported extension that reaches the unchanged gate.
selected=next((r for r in rows if r['outer_gap_depth']==2.5 and r['min_cut']>=510.-PF.TOL_MM2),None)
if selected:
 import types
 import cadquery as cq
 sys.path.insert(0,str(CV/'tests'))
 import test_plenum_trial2 as PT
 top=selected['front_top'];depth=selected['outer_gap_depth']
 original_cuts=VG.mouth_cuts
 def cuts(length):
  out=[s for s in original_cuts(length) if not (s.BoundingBox().xmin>-3 and s.BoundingBox().xmax>0)]
  for za,zb in VG._openings(5.,top,[21.,49.]):
   if za<49.:out.append(VG.box(-2.6,.1,-34.,-28.,za,min(zb,49.)))
   if zb>49.:out.append(VG.box(-2.6,.1,-34.,-34.+depth,max(za,49.),zb))
  return out
 VG.mouth_cuts=cuts
 s=PT.plenum_body(158.)
 necks=[PT.free(s,'x',p,-34.,-28.,5.,top) for p in (-.05,-1.25,-2.49,-2.62)]
 r=PF.step_min_cut(s,158.,'hot')
 print(json.dumps(dict(selected=selected,step_hot_cut=r,mouth_neck_sections=necks,valid=s.isValid(),solids=len(s.Solids()))),flush=True)
 man=PT.print_manifold(s)
 L7=types.SimpleNamespace(PRINT_OVERHANG=dict(PT.R7L.PRINT_OVERHANG),PARTS={'tub':dict(face_down='-Y')})
 ov=PT.PR.CK.check_print_overhang(L7,'tub',man,[],face_down='-Y')
 bd=PT.PR.check_bridge_direction(L7,'tub',man,[],face_down='-Y')
 bc=PT.PR.check_bed_chamfer('tub',man,face_down='-Y')
 result=dict(selected=selected,step_hot_cut=r,mouth_neck_sections=necks,print_overhang=ov,print_bridge_direction=bd,bed_chamfer=bc,valid=s.isValid(),solid_count=len(s.Solids()),scope='Isolated plenum body, not the final whole tub export; envelope and hardware unchanged; actual print/cleanout/thermal performance unqualified')
 write_text(Path(__file__).with_name('supported-step-validation.json'),json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(validation={k:v['status'] for k,v in [('overhang',ov),('bridge',bd),('bed_chamfer',bc)]},failing_regions=bd.get('failing_regions'),longest_bridge_mm=bd.get('longest_bridge_mm'))),flush=True)
