"""Custom D2 screening coupons. Not ASTM/ISO specimens or approved production parts.
Run with pinned CadQuery Python. Exports source STEP + print-oriented STL.
"""
from pathlib import Path
import cadquery as cq,hashlib,json,math,argparse
P=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--inherited-joint-only',action='store_true');args=ap.parse_args()
O=P/'coupons'/('inherited-joint' if args.inherited_joint_only else '');O.mkdir(exist_ok=True);V=cq.Vector

def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,V(x0,y0,z0))
def beam(b,t):
 L=math.hypot(34,16)
 return box(-15,.1,-10,10,0,8).fuse(box(0,L+5,-b/2,b/2,0,t)).clean()
def bridge(b,t):
 # Local Y spans13mm; two3.5mm slots flank centre bridge of localX width b.
 xmax=b/2+3.5+4;s=box(-xmax,xmax,-10.5,10.5,0,t)
 for xa,xb in [(-b/2-3.5,-b/2),(b/2,b/2+3.5)]:s=s.cut(box(xa,xb,-6.5,6.5,-.1,t+.1))
 return s.clean()
def seat():
 s=cq.Solid.makeCylinder(4.5,4,V(0,0,0),V(0,0,1)).fuse(box(-20,20,-4,4,1,4))
 s=s.cut(cq.Solid.makeCylinder(1.4,4.2,V(0,0,-.1),V(0,0,1)),cq.Solid.makeCylinder(2.65,1.1,V(0,0,3),V(0,0,1)))
 return s.clean()
def pose(s,face):
 if face=='+X':s=s.rotate((0,0,0),(0,1,0),90)
 elif face=='+Z':s=s.rotate((0,0,0),(1,0,0),180)
 elif face=='-Y':s=s.rotate((0,0,0),(1,0,0),90)
 elif face!='-Z':raise ValueError(face)
 bb=s.BoundingBox();return s.translate(V(-bb.xmin,-bb.ymin,-bb.zmin))
items=[]
for id,b,t in [('C01_carrier_original',4,3),('C02_carrier_reinforced',8,5)]:
 items.append((id,beam(b,t),'-Z',dict(type='custom uniform cantilever',beam_width_mm=b,beam_thickness_mm=t,clamp_x_mm=[-15,0],force_x_mm=math.hypot(34,16),force_direction='localZ',normal_print_axis='localZ corresponding to assemblyY',source='nominal arm section; does not reproduce ear, frame or root fillets')))
for id,b,t,face in [('C03_heel_original',3.5,2.5,'+X'),('C04_heel_reinforced',3.5,5.5,'+X'),('C05_upper_original',2,6,'-Z'),('C06_upper_widened',4,6,'-Z')]:
 items.append((id,bridge(b,t),face,dict(type='custom twin-slot bridge',span_mm=13,bridge_b_mm=b,bridge_t_mm=t,slot_width_mm=3.5,slot_span_y_mm=[-6.5,6.5],force_direction='localZ',load_point='localX0/Y0; compare centred pusher with actual12mm webbing',fixture='support/clamp outer frame beyond Y±6.5; keep span open',normal_print_axis=('localX corresponds to assemblyZ' if 'heel' in id else 'localZ corresponds to assemblyZ'),source='idealised local rectangular bridge; omits curved grip wall, full strap route and recess transitions')))
items.append(('C07_M2_5_seat',seat(),'+Z',dict(type='custom carrier seat',boss_diameter_mm=9,thickness_mm=4,clearance_diameter_mm=2.8,counterbore_diameter_mm=5.3,counterbore_depth_mm=1,under_head_material_mm=3,normal_print_axis='localZ corresponds to assemblyY',fixture='real kit screw/standoff with central printed boss and metal reaction; record clamp force if measured, not inferred; tabs allow separate pull-through test',source='nominal actual carrier boss/seat; no qualified torque')))
for id,name,face,z0,z1 in [('C08_J4_base','base_grip','+Z',-8,.01),('C09_J4_tongue','tub','-Y',-5.2,3)]:
 p=(P/'input-baseline/step'/f'{name}.step') if args.inherited_joint_only else (P/'j4-trial'/('grip.step' if name=='base_grip' else 'tub.step'));s=cq.importers.importStep(str(p)).val().intersect(box(-28,0,-30,30,z0,z1)).clean()
 items.append((id,s,face,dict(type='actual STEP extract',source_part=name,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),crop_bounds_mm=[-28,0,-30,30,z0,z1],normal_print_axis='same assembly-coordinate face down as production',fixture='mating pair; slide10mm to engage; clamp outer base and apply pull/rock to tub floor using a separate rigid fixture; do not clamp bearing lips',source=('inherited1.6mm lip/1.8mm head' if args.inherited_joint_only else 'selected coordinated2.4mm lip/head trial')+'; front tongue only; no independent lock screw, rear tongue, full floor or whole joint rating')))
if args.inherited_joint_only:items=[x for x in items if x[0].startswith(('C08','C09'))]
manifest={'status':'CUSTOM TEST COUPONS ONLY; no ASTM/ISO compliance, no slicer/physical qualification','units':'mm','production_part_count_effect':f'none;{len(items)}separate custom coupon pieces','design_cases':'screening report; not force ratings','process':'baseline0.20mm; comparison0.16/0.24mm;critical sections100%local infill with intended perimeter construction;layer normal preserved','parts':[]}
for id,s,face,meta in items:
 assert s.isValid() and len(s.Solids())==1,(id,s.isValid(),len(s.Solids()))
 st=O/f'{id}.step';sl=O/f'{id}.stl';cq.exporters.export(s,str(st));ps=pose(s,face);cq.exporters.export(ps,str(sl),tolerance=.05,angularTolerance=.1)
 b=ps.BoundingBox();manifest['parts'].append(dict(id=id,valid=True,solid_count=1,volume_mm3=s.Volume(),face_down_in_source_coords=face,print_bbox_mm=[b.xlen,b.ylen,b.zlen],step_sha256=hashlib.sha256(st.read_bytes()).hexdigest(),stl_sha256=hashlib.sha256(sl.read_bytes()).hexdigest(),**meta))
(O/'coupon-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('PASS:',len(items),'valid single-solid coupons exported')
