"""Independent checks against saved STEP, not a fabricated release pass."""
import argparse,hashlib,json,math,itertools,time
from pathlib import Path
import cadquery as cq
import numpy as np
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
p=argparse.ArgumentParser();p.add_argument('--variant',default='compact-kowa_lm6hc');p.add_argument('--motion-step',type=float,default=2.0);a=p.parse_args()
ROOT=Path(__file__).resolve().parent;out=ROOT/'out'/a.variant
manifest_start=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()
meta=json.loads((out/'manifest.json').read_text());rows={r['id']:r for r in meta['rows']};shapes={}
checks=[]
def add(category,id,ok=None,**kw):
 r=dict(category=category,id=id,status='info' if ok is None else ('pass' if ok else 'fail'),**kw);checks.append(r)
 if r['status']!='pass':print(json.dumps(r),flush=True)
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def broad(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-7 for i in (0,2,4))
for name,r in rows.items():
 path=out/'step'/f'{name}.step'
 s=cq.importers.importStep(str(path)).val();shapes[name]=s
 sha=hashlib.sha256(path.read_bytes()).hexdigest();bound=sha==meta['files'].get(f'step/{name}.step')
 add('integrity',name,bound and s.isValid() and (r['kind']!='printed' or len(s.Solids())==1),solids=len(s.Solids()),volume_mm3=s.Volume(),step_sha256=sha,manifest_file_binding=bound)
 add('roundtrip',name,abs(s.Volume()-r['volume_mm3'])<.02,volume_delta_mm3=s.Volume()-r['volume_mm3'])
for rel,sha in meta['sources'].items():add('source_binding',rel,hashlib.sha256((ROOT.parent/rel).read_bytes()).hexdigest()==sha)
# Exact distributive intersection for the detailed Pi union. Component broad
# phases remove only disjoint material; their intersection union is algebraically
# identical to intersecting the pre-fused Pi. No contacts are waived or deleted.
import sys
sys.path.insert(0,str(ROOT.parent))
import layout as PiL
import official_pi5_assembly as PiA
pi_components=PiA.build_parts(PiL)
pi_component_bounds={n:bb(q) for n,q in pi_components.items()}
face_cache={};classifier_cache={}
def material_possible(key,shape,b):
 # If no boundary face meets the connected query box, solid membership is
 # constant over that box. This rejects only proved empty regions of a solid.
 if key not in face_cache:face_cache[key]=np.array([bb(f) for f in shape.Faces()])
 faces=face_cache[key];mask=np.ones(len(faces),dtype=bool)
 for i in (0,2,4):mask &= (np.minimum(faces[:,i+1],b[i+1])-np.maximum(faces[:,i],b[i])) >= -1e-7
 if mask.any():return True
 if key not in classifier_cache:classifier_cache[key]=[BRepClass3d_SolidClassifier(q.wrapped) for q in shape.Solids()]
 p=gp_Pnt(*[(b[i]+b[i+1])/2 for i in (0,2,4)])
 for classifier in classifier_cache[key]:
  classifier.Perform(p,1e-7)
  if classifier.State()==TopAbs_IN or classifier.IsOnAFace():return True
 return False
def intersect_pair(na,nb,offset=(0,0,0),fixed_shape=None,fixed_key=None):
 other_fixed=shapes[nb] if fixed_shape is None else fixed_shape
 other_key=nb if fixed_key is None else fixed_key
 moved=shapes[na].translate(cq.Vector(*offset)) if any(offset) else shapes[na]
 if na!='pi5' and nb!='pi5':
  return moved.intersect(other_fixed) if material_possible(other_key,other_fixed,bb(moved)) else cq.Compound.makeCompound([])
 pieces=[]
 for cn,component in pi_components.items():
  if na=='pi5':
   cb=[v+offset[i//2] for i,v in enumerate(pi_component_bounds[cn])]
   other=other_fixed;ob=bb(other)
   if not broad(cb,ob) or not material_possible(other_key,other,cb):continue
   q=component.translate(cq.Vector(*offset)).intersect(other)
  else:
   if not broad(bb(moved),pi_component_bounds[cn]) or not material_possible("pi/"+cn,component,bb(moved)):continue
   q=moved.intersect(component)
  if q.Volume()>1e-10:pieces.append(q)
 if not pieces:return cq.Compound.makeCompound([])
 return pieces[0].fuse(*pieces[1:]) if len(pieces)>1 else pieces[0]

# Narrow local contact allowances. Never a blanket part-pair exception.
L=meta['core_dimensions_mm'][0];ey=11
for na,nb in itertools.combinations(shapes,2):
 ra,rb=rows[na],rows[nb]
 if not broad(ra['bbox_mm'],rb['bbox_mm']):continue
 s=intersect_pair(na,nb);v=s.Volume()
 if v<.05:
  add('interference',na+'/'+nb,True,overlap_mm3=round(v,6));continue
 pair={na,nb};allowed=False;why=None
 if (ra['kind']=='keepout' or rb['kind']=='keepout') and ra['kind']!='printed' and rb['kind']!='printed':
  add('non_material_keepout',na+'/'+nb,None,overlap_mm3=round(v,6),bbox=bb(s),operational_status='HOLD',reason='Estimated mating envelope is not material. Actual plug/contact geometry and insertion remain unmeasured; failed full-solid export16 diagnostic is preserved.')
  continue
 # Self-tapping shanks deliberately cut into their own pilot; restrict to actual pilot cylinder.
 hardware=na if na.startswith('p_') else (nb if nb.startswith('p_') else None)
 if hardware and pair-{hardware}=={'tub'}:
  h=rows[hardware]['bbox_mm'];c=shapes[hardware].Center()
  # The intersecting extent must remain below the head and within a 3 mm shank diameter.
  b=bb(s)
  allowed=(b[1]-b[0]<=3.001 and b[5]-b[4]<=3.001) if hardware!='p_grip' else (b[1]-b[0]<=3.001 and b[3]-b[2]<=3.001)
  why='Local PT shank/pilot thread-forming interference; physical thread gate remains open'
 if pair=={'eyecup','eyepiece'}:
  b=bb(s);allowed=(v<104 and b[0]>=-L-20.31 and b[1]<=-L-17.29 and b[2]>=ey-18.36 and b[3]<=ey+18.36)
  why='Existing TPU eyecup sleeve radial interference, only its3mm engagement band; physical retention gate open'
 if pair=={'panel','eyepiece'}:
  b=bb(s);allowed=(v<8 and b[0]>=-L+2.59 and b[1]<=-L+4.51 and b[2]>=ey+7.99)
  why='Only the explicitly modelled 0.1 mm radial EVF clamp region; G-EVF-1 open'
 if pair=={'pi5','cooler'}:why='Active source/proxy conflict: source-corrected Pi features meet the approximate cooler perimeter/underside/pin profile. Actual cooler registration and geometry are unmeasured; no physical incompatibility or clearance qualification is inferred.'
 add('interference',na+'/'+nb,None if allowed else False,overlap_mm3=round(v,6),bbox=bb(s),reason=why or 'Unclassified physical proxy overlap')
# Required rigid-body service motions. Discrete sweeps are not continuous swept-volume proofs.
# Rigid submotions only. Battery isolation, named free-end disconnections and full
# carried harness checks are separate source-bound requirements. Pi HDMI stays mated.
# FPS knob/nut/washer are removed first; the switch is hand-supported on its rest.
paths=[
 ('fps_knob_off',['knob_fps'],['panel','switch_1824','fps_nut','fps_mounting_washer'],[(0,0,0),(0,20,0)]),
 ('fps_nut_after_unthread',['fps_nut'],['panel','switch_1824','fps_mounting_washer'],[(0,0,0),(0,20,0)]),
 ('fps_washer_off',['fps_mounting_washer'],['panel','switch_1824'],[(0,0,0),(0,20,0)]),
 ('carrier_out',['carrier','pi5','cooler','x1203','x1203_kit','microsd','switch_1824'],['tub','gs_camera','c_cs_adapter','evf_board','hmx039','foam_pad'],[(0,0,0),(0,70,0)]),
 ('panel_out',['panel','encoder','knob_exp','power_button','power_nut_reserve'],['tub','pi5','cooler','x1203','carrier','switch_1824','gs_camera','c_cs_adapter','eyepiece','evf_board','hmx039','foam_pad'],[(0,0,0),(0,70,0)]),
 ('camera_in',['gs_camera','c_cs_adapter'],['tub','lens_collar'],[(-11.1,60,2),(-11.1,0,2),(-11.1,0,0),(0,0,0)]),
 ('evf_in',['hmx039','foam_pad','evf_board'],['tub'],[(0,60,0),(0,0,0)]),
 ('storage_plug_reservation_through_enclosure',['usb_storage_plug_reserve'],['tub','evf_board','hmx039'],[(0,0,0),(-70,0,0)]),
 ('storage_out',['usb_stick'],['tub','pi5','evf_board','hmx039'],[(0,0,0),(-70,0,0)]),
 ('microsd_out',['microsd'],['tub','gs_camera','c_cs_adapter'],[(0,0,0),(45,0,0)])]
for pid,moving,fixed,knots in paths:
 print('Checking motion',pid,flush=True)
 points=[]
 for u,v in zip(knots,knots[1:]):
  n=math.ceil(math.dist(u,v)/a.motion_step)
  points += [[u[j]+(v[j]-u[j])*i/n for j in range(3)] for i in range(n)]
 points.append(knots[-1]);worst=0;hits=[]
 # Exact conservative region reduction for printed obstacles. All paths here
 # are pure translations: the union is contained in the coordinate envelope
 # of every knot bbox. Expanding by0.01mm retains boundary/tolerance material.
 # Detailed Pi components are never Boolean-cropped as an assembled union.
 regions={}
 for name in moving:
  b=bb(shapes[name]);envelope=[]
  for i in range(3):envelope += [b[2*i]+min(t[i] for t in knots)-.01,b[2*i+1]+max(t[i] for t in knots)+.01]
  for fn in fixed:
   if not broad(envelope,rows[fn]['bbox_mm']):regions[name,fn]=None;continue
   if rows[fn]['kind']!='printed':regions[name,fn]=shapes[fn];continue
   fb=rows[fn]['bbox_mm']
   if all(envelope[i]<=fb[i] and envelope[i+1]>=fb[i+1] for i in (0,2,4)):regions[name,fn]=shapes[fn];continue
   region=cq.Solid.makeBox(envelope[1]-envelope[0],envelope[3]-envelope[2],envelope[5]-envelope[4],cq.Vector(envelope[0],envelope[2],envelope[4]))
   crop=shapes[fn].intersect(region)
   regions[name,fn]=crop if crop.Solids() and crop.Volume()>1e-10 else None
   print('Motion region',pid,name,fn,'empty' if regions[name,fn] is None else len(crop.Faces()),flush=True)
 for index,t in enumerate(points):
  if index%10==0:print(pid,index,'/',len(points),flush=True)
  for name in moving:
   sm=shapes[name].translate(cq.Vector(*t));bm=bb(sm)
   for fn in fixed:
    if not broad(bm,rows[fn]['bbox_mm']):continue
    obstacle=regions[name,fn]
    if obstacle is None:continue
    iv=intersect_pair(name,fn,t,obstacle,(pid,name,fn)).Volume()
    # Only final EVF clamp contact is permitted, and it disappears with panel extraction.
    if pid=='panel_out' and name=='panel' and fn=='eyepiece' and t[1]<.2 and iv<8:continue
    worst=max(worst,iv)
    if iv>.05:hits.append(dict(moving=name,fixed=fn,offset=t,overlap_mm3=iv))
 add('motion',pid,not hits,step_mm=a.motion_step,samples=len(points),printed_obstacle_region_method='Exact Boolean crop to full translated-knot bounding envelope expanded0.01mm; all sample poses unchanged',worst_overlap_mm3=worst,first_hits=hits[:12],total_hits=len(hits))
# Basic load-bearing nominal dimensions; all tolerance/coupon checks remain physical gates.
for ident,value,minv in [('panel_screw_bearing_land',2.1,1.6),('panel_head_radial_wall',1.7,1.6),('carrier_PT_head_radial_wall',1.6,1.6),('carrier_M25_head_radial_wall',1.85,1.6),('carrier_M25_thread_engagement',3.4,2.5),('collar_hoop_nominal',25-21.15,1.6),('collar_relief_nominal_after_bed_chamfer',math.hypot(22.8,6)-21.15-.6,1.6)]:
 add('nominal_features',ident,None,value_mm=value,minimum_mm=minv,analytical_meets_rule=value+1e-8>=minv,note='Report-only analytical design value; not extracted from the current STEP and not a measured wall or strength result')
# Actual saved-STEP material spans on named local load paths. These are sampled rays,
# not a global minimum-wall or FEA qualification.
probes=[('panel_skin','panel',(-90,20,50),(-90,32,50)),
 ('panel_screw_bearing_land','panel',(-8.3,20,91.7),(-8.3,32,91.7)),
 ('carrier_M25_seat_stock','carrier',(-35.5,10,10.5),(-35.5,23,10.5)),
 ('carrier_PT_radial_wall','carrier',(-134,20,69),(-130.2,20,69)),
 ('collar_equatorial_hoop','lens_collar',(5,20,60),(5,27,60)),
 ('tub_outer_skin','tub',(-110,-37,50),(-110,-33,50)),
 ('tub_original_inner_wall','tub',(-110,-29,50),(-110,-24,50)),
 ('tub_floor','tub',(-100,20,-1),(-100,20,7)),
 ('tub_roof','tub',(-80,0,95),(-80,0,102)),
 ('grip_rear_wall','base_grip',(-73,0,-50),(-66,0,-50)),
 ('grip_upper_rear_path','base_grip',(-73,0,-8.5),(-63,0,-8.5)),
 ('carrier_tie_eye_land','carrier',(-97,18.5,25),(-93.5,18.5,25))]
for ident,pid,pa,pb in probes:
 edge=cq.Edge.makeLine(cq.Vector(*pa),cq.Vector(*pb))
 spans=shapes[pid].intersect(edge).Edges();value=sum(e.Length() for e in spans)
 add('step_material_probes',ident,len(spans)==1 and value>=1.6-1e-7,value_mm=value,spans=len(spans),minimum_mm=1.6,origin=pa,end=pb,note='Local ray through actual saved STEP only; other locations and material strength remain unqualified')
# Retain the old failed ray as a deliberate-aperture check; do not relabel it wall.
pa=(-80,-40,50);pb=(-80,-20,50)
es=shapes['tub'].intersect(cq.Edge.makeLine(cq.Vector(*pa),cq.Vector(*pb))).Edges()
add('step_aperture_probes','intentional_CSI_opening',len(es)==0,material_span_mm=sum(e.Length() for e in es),origin=pa,end=pb,note='Designated service aperture; old export18 tub_right_wall probe crossed this opening. No latch/tool qualification follows.')
add('physical','qualification',None,open_inherited_gates=56,M1='open',candidate_gates='unrun',fabrication_release=False)
summary={k:sum(r['status']==k for r in checks) for k in ('pass','fail','info')}
if hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()!=manifest_start:raise ValueError('Manifest changed during verification')
result=dict(manifest_sha256=manifest_start,verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),variant=a.variant,summary=summary,checks=checks,geometry_computed_pass=summary['fail']==0,physical_qualified=False,generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
(out/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(summary),flush=True)
sys_exit=summary['fail']>0
raise SystemExit(1 if sys_exit else 0)
