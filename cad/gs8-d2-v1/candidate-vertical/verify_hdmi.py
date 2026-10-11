"""Exact printed-solid checks of the frozen complete-material HDMI reservation.
The reservation is a sampled developable strip, not a strength/material approval.
"""
from cv_io import read_text, write_text
import argparse,hashlib,json,itertools,math,time
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
p=argparse.ArgumentParser();p.add_argument('--variant',default='compact-kowa_lm6hc');p.add_argument('--snapshot',required=True);p.add_argument('--step',type=float,default=2);p.add_argument('--include-rejected',action='store_true',help='Reproduce archived in-body Pi-unplug and obsolete FPC-tool diagnostics; not selected service');p.add_argument('--out',default='',help='report path instead of out/<variant>/hdmi-solid-checks.json');a=p.parse_args()
ROOT=Path(__file__).resolve().parent;out=ROOT/'out'/a.variant;src=Path(a.snapshot);snap=json.loads(read_text(src));meta=json.loads(read_text(out/'manifest.json'))
rows={r['id']:r for r in meta['rows']};shapes={name:cq.importers.importStep(str(out/'step'/f'{name}.step')).val() for name in rows}
for name in rows:
 fp=out/'step'/f'{name}.step'
 if hashlib.sha256(fp.read_bytes()).hexdigest()!=meta['files'][f'step/{name}.step']:raise ValueError('STEP hash mismatch:'+name)
manifest_start=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()
checks=[]
def add(cat,id,ok=None,**kw):
 r=dict(category=cat,id=id,status='info' if ok is None else ('pass' if ok else 'fail'),**kw);checks.append(r)
 if ok is not True:print(json.dumps(r),flush=True)
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def bounds(b):return [v for k in 'xyz' for v in b[k]]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-7 for i in (0,2,4))
def bsolid(b):return cq.Solid.makeBox(*(b[k][1]-b[k][0] for k in 'xyz'),cq.Vector(*(b[k][0] for k in 'xyz')))
def cell(pts):
 points=np.unique(np.round(np.array(pts,dtype=float),10),axis=0)
 if len(points)<4:return None
 center=points.mean(axis=0);planes={}
 for ix in itertools.combinations(range(len(points)),3):
  pa,pb,pc=points[list(ix)];normal=np.cross(pb-pa,pc-pa);mag=np.linalg.norm(normal)
  if mag<1e-10:continue
  normal/=mag;dist=(points-pa)@normal
  if np.max(dist)>1e-7 and np.min(dist)<-1e-7:continue
  if np.dot(center-pa,normal)>0:normal=-normal
  ids=tuple(np.where(np.abs(dist)<1e-7)[0])
  planes[ids]=normal
 if len(planes)<4:return None
 sew=BRepBuilderAPI_Sewing(1e-7)
 for ids,normal in planes.items():
  q=points[list(ids)];c=q.mean(axis=0);u=q[0]-c;u/=np.linalg.norm(u);v=np.cross(normal,u)
  order=np.argsort(np.arctan2((q-c)@v,(q-c)@u));q=q[order]
  wire=cq.Wire.makePolygon([cq.Vector(*x) for x in q]+[cq.Vector(*q[0])])
  sew.Add(cq.Face.makeFromWires(wire).wrapped)
 sew.Perform();shell=cq.Shape.cast(sew.SewedShape())
 if not isinstance(shell,cq.Shell):shell=shell.Shells()[0]
 sol=cq.Solid.makeSolid(shell)
 if sol.Volume()<1e-8:return None
 if not sol.isValid():raise ValueError('Invalid convex ribbon cell')
 return sol
# Exact localization: discard only fixed material outside the union bounding box
# of every queried ribbon/head/header/tool pose. This removes unrelated floor
# wiring pockets from costly OCC booleans without omitting any queried space.
query_boxes=[]
for key in ('hdmi_installed','hdmi_premate','hdmi_both_unplugged'):
 if key not in snap:continue
 for seg in snap[key]['segments']:
  b=bounds(seg['box']);query_boxes.extend([b,[b[0],b[1],b[2]+70,b[3]+70,b[4],b[5]]])
# H2 (VN-43): the module is carried in with the EVF head held stroke + 3 mm below its mated height (steps.py
# module_staged), not at the bare 6 mm stroke (0 mm margin). The carried ribbon at that drop comes from
# hdmi_routes.ribbon300, the generator that reproduces the snapshot's installed and premate ribbons exactly
# (tests/test_hdmi_carried.py); the snapshot premate (stroke only) stays the premate state.
import hdmi_routes as HDR
EVF_STROKE_MM=float(next(q for q in snap['connectors'] if q['id']=='p_hdmi_evf')['stroke'])
CARRIED_MARGIN_MM=3.0
CARRIED_DROP_MM=EVF_STROKE_MM+CARRIED_MARGIN_MM
carried_ribbon=HDR.ribbon300(158,pose='service',lift=0,drop=CARRIED_DROP_MM,initial_u=5.5,tail=2.0)
if abs(carried_ribbon['routed_length_mm']-300)>1e-6:raise ValueError('carried ribbon is not the full 300 mm stock')
for seg in carried_ribbon['segments']:
 b=bounds(seg['box']);query_boxes.extend([b,[b[0],b[1],b[2]+70,b[3]+70,b[4],b[5]]])
# H2 (VN-43): EVF HDMI unplug corridor (service op svc_evf_unplug, panel off). The 3556 head is pulled straight down
# its stroke by its body with smooth-jaw long-nose pliers coming in from the open +Y side. Tool numbers from r7
# layout.ACCESS acc_hdmi_evf_jaws (tips <= 2.0 thick, box 2.2; grip 8.0 of the head width; jaw height 9.4): one jaw on
# each thin (X) face over the +Y 8.0 mm of the head width and its lowest 9.4 mm, swept down the stroke; the shank box
# runs from the jaws to UNPLUG_OUT beyond the +Y opening at the jaw height. Defined here so the exact crop keeps
# the material around them.
_e=next(q for q in snap['connectors'] if q['id']=='p_hdmi_evf')['box']
JAW_T,JAW_GRIP,JAW_H,UNPLUG_OUT=2.2,8.0,9.4,10.0
_uz=(_e['z'][0]-EVF_STROKE_MM,_e['z'][0]+JAW_H);_uy=(_e['y'][1]-JAW_GRIP,_e['y'][1])
UNPLUG_BOXES={'jaw_minus_x':[_e['x'][0]-JAW_T,_e['x'][0],_uy[0],_uy[1],_uz[0],_uz[1]],
              'jaw_plus_x':[_e['x'][1],_e['x'][1]+JAW_T,_uy[0],_uy[1],_uz[0],_uz[1]],
              'shank':[_e['x'][0]-JAW_T,_e['x'][1]+JAW_T,_uy[1],rows['tub']['bbox_mm'][3]+UNPLUG_OUT,_uz[0],_uz[1]]}
query_boxes.extend(UNPLUG_BOXES.values())
for row in snap['header_housings']+[q for q in snap['connectors'] if q['id'] in ('p_hdmi_pi','p_hdmi_evf','p_usb_pi')]:
 b=bounds(row['box']);zpad=CARRIED_DROP_MM if row['id']=='p_hdmi_evf' else 6 if row['id']=='p_hdmi_pi' else 0;query_boxes.extend([[b[0],b[1],b[2],b[3]+70,b[4]-zpad,b[5]+zpad]])
for xx in (-87,-79):
 t=np.array([xx,-4.5,61.5]);d=np.array([0,34.5,25.5]);d=d/np.linalg.norm(d);e=t+90*d
 query_boxes.append([xx-4,xx+4,min(t[1],e[1])-4,max(t[1],e[1])+4,min(t[2],e[2])-4,max(t[2],e[2])+4])
analysis_bbox=[(min(b[i] for b in query_boxes)-.01 if i%2==0 else max(b[i] for b in query_boxes)+.01) for i in range(6)]
clipper=cq.Solid.makeBox(analysis_bbox[1]-analysis_bbox[0],analysis_bbox[3]-analysis_bbox[2],analysis_bbox[5]-analysis_bbox[4],cq.Vector(analysis_bbox[0],analysis_bbox[2],analysis_bbox[4]))
for n,sh in list(shapes.items()):
 b=bb(sh)
 if not overlaps(b,analysis_bbox):shapes[n]=cq.Compound.makeCompound([])
 elif any(b[i]<analysis_bbox[i]-.001 if i%2==0 else b[i]>analysis_bbox[i]+.001 for i in range(6)):
  shapes[n]=sh.intersect(clipper)
print('Exact analysis crop',analysis_bbox,flush=True)
# Exact face-bounding broad phase: a convex cell intersecting a solid either
# crosses a boundary face or is wholly inside. This skips empty cavity booleans
# without replacing them with an assumed empty box.
face_boxes={n:np.array([[v-1e-6 if i%2==0 else v+1e-6 for i,v in enumerate(bb(f))] for f in sh.Faces()]) for n,sh in shapes.items()}
classifiers={n:[BRepClass3d_SolidClassifier(q.wrapped) for q in sh.Solids()] for n,sh in shapes.items()}
def potential(n,b):
 if not overlaps(b,rows[n]['bbox_mm']):return False
 f=face_boxes[n]
 if not len(f):return False
 mask=np.ones(len(f),dtype=bool)
 for i in (0,2,4):mask &= (np.minimum(f[:,i+1],b[i+1])-np.maximum(f[:,i],b[i]))>0
 if mask.any():return True
 c=gp_Pnt(*[(b[i]+b[i+1])/2 for i in (0,2,4)])
 for q in classifiers[n]:
  q.Perform(c,1e-7)
  if q.State()==TopAbs_IN or q.IsOnAFace():return True
 return False
# Header bodies are carried rather than declared magically unplugged behind the PCB.
headers={h['id']:bsolid(h['box']) for h in snap['header_housings']}
connectors={r['id']:r for r in snap['connectors']}
heads={n:bsolid(connectors[n]['box']) for n in ('p_hdmi_pi','p_hdmi_evf','p_usb_pi')}
# Fixed parts exclude the open panel and removed storage for assembly/service.
fixed_names=[n for n,r in rows.items() if r['kind']!='keepout' and not n.startswith(('p_','s_')) and n not in ('panel','encoder','switch_1824','knob_exp','knob_fps','power_button','power_nut_reserve','fps_nut','fps_mounting_washer','usb_stick')]
# FP-12 (VN-30): the 9ced753 sets above dropped every p_/s_ screw (and the stick). Each state now also takes every
# material part steps.py has in the body at that moment (screws, hardware, COTS), never fewer than before.
import steps as ST
material={n for n,r in rows.items() if r['kind']!='keepout'}
MOVERS=set(ST.MODULE)
STATE_SETS={'installed':(set(ST.final_state()),'final build state (closed body)'),
            'premate':(set(ST.state_before('evf_mate')),'body before op evf_mate (carrier screwed in, panel not yet on)'),
            'carried':(set(ST.state_before('carrier_in')),'body before op carrier_in, minus the moving module')}
PANEL_SET=[n for n in ['panel','encoder','switch_1824','power_button','power_nut_reserve','fps_nut','fps_mounting_washer'] if n in rows]
def state_fixed(state,legacy):
 present,_=STATE_SETS[state];derived=(present&material)-(MOVERS if state=='carried' else set())
 return sorted(set(legacy)|derived)
def state_exclusions(state,used):
 present,why=STATE_SETS[state];ex=[]
 for n in sorted((present&set(rows))-set(used)):
  ex.append(dict(id=n,reason='non-material keepout' if rows[n]['kind']=='keepout' else ('moves with the carried module (rider of the sweep)' if n in MOVERS else 'not in this state')))
 return dict(state_source=why,excluded_present_ids=ex)
STATE_FIXED={'installed':state_fixed('installed',fixed_names+PANEL_SET),'premate':state_fixed('premate',fixed_names+PANEL_SET),'both_unplugged':state_fixed('installed',fixed_names+PANEL_SET)}
obstacle_report={s:dict(obstacles=v,**state_exclusions('installed' if s=='both_unplugged' else s,v)) for s,v in STATE_FIXED.items()}
printed=[n for n,r in rows.items() if r['kind']=='printed' and n not in ('panel','knob_exp','knob_fps')]
for n,head in heads.items():
 hits=[]
 for fn in printed:
  if not overlaps(bb(head),rows[fn]['bbox_mm']):continue
  v=head.intersect(shapes[fn]).Volume()
  if v>.02:hits.append(dict(part=fn,overlap_mm3=v))
 add('hard_head_vs_printed',n,not hits,hits=hits)
# FP-12 (VN-30): installed heads against every other material part present; only the head's own mating partner
# (the receptacle it is plugged into) is excluded, and named.
HEAD_PARTNER={'p_hdmi_pi':'pi5','p_hdmi_evf':'evf_board','p_usb_pi':'pi5'}
for n,head in heads.items():
 hits=[];hb=bb(head)
 for fn in STATE_FIXED['installed']:
  if fn==HEAD_PARTNER[n] or not potential(fn,hb):continue
  v=head.intersect(shapes[fn]).Volume()
  if v>.02:hits.append(dict(part=fn,overlap_mm3=v))
 add('hard_head_vs_material',n,not hits,hits=hits,excluded_mating_partner=HEAD_PARTNER[n])
# Regression fixtures: a 1 mm cube at each installed screw/hardware centroid must be found by the same broad phase
# and Boolean the ribbon cells use (the 9ced753 sets would miss all of them).
for fn in [x for x in STATE_FIXED['installed'] if rows[x]['kind']=='hardware']:
 c=shapes[fn].Center();q=cq.Solid.makeBox(1,1,1,cq.Vector(c.x-.5,c.y-.5,c.z-.5));qb=bb(q)
 if not overlaps(qb,analysis_bbox):continue          # cropped away: no ribbon cell can reach it either
 cls_in=False
 for k in classifiers[fn]:
  k.Perform(gp_Pnt(c.x,c.y,c.z),1e-7);cls_in=cls_in or k.State()==TopAbs_IN
 if not cls_in:continue                              # hollow centroid (nut, washer): no interior point to plant
 v=q.intersect(shapes[fn]).Volume() if potential(fn,qb) else 0.0
 add('obstacle_fixture',fn,v>1e-4,planted_cube_centre=[c.x,c.y,c.z],detected_overlap_mm3=v,purpose='hardware is in the installed ribbon obstacle set')
# Full material shapes in closed and pre-mate poses, checked against exact printed parts.
all_cells={};all_bounds={};all_vertices={}
def get_cell(state,i):
 if all_cells[state][i] is None:all_cells[state][i]=cell(all_vertices[state][i])
 return all_cells[state][i]
for state,key in [('installed','hdmi_installed'),('premate','hdmi_premate')]+([('both_unplugged','hdmi_both_unplugged')] if a.include_rejected and 'hdmi_both_unplugged' in snap else []):
 rr=snap[key];cells=[];bs=[];hits=[];tested=0
 all_cells[state]=[None]*len(rr['segments']);all_bounds[state]=[bounds(x['box']) for x in rr['segments']];all_vertices[state]=[x['vertices'] for x in rr['segments']]
 for i,seg in enumerate(rr['segments']):
  
  if i%250==0:print(f'{state}: cell {i}/{len(rr["segments"])}',flush=True)
  b=bounds(seg['box']);possible=[n for n in STATE_FIXED[state] if potential(n,b)]
  if not possible:continue
  s=get_cell(state,i)
  if s is None:continue
  for fn in possible:
   v=s.intersect(shapes[fn]).Volume();tested+=1
   if v>.001:hits.append(dict(segment=i,part=fn,overlap_mm3=v,bbox=bb(s.intersect(shapes[fn]))))
 add('full_ribbon_vs_solids',state,not hits,material_length_mm=rr['routed_length_mm'],cells=len(rr['segments']),exact_intersections=tested,hits=hits[:25],hit_count=len(hits),max_overlap_mm3=max((h['overlap_mm3'] for h in hits),default=0))
# Rigid carried pre-mate shape + adapters + headers. Ribbon/head stay below EVF mouth until the final upward mate;
# H2 (VN-43): the head and the ribbon are carried CARRIED_DROP_MM (stroke + 3) low.
carried={'pi_head':heads['p_hdmi_pi'],'evf_head':heads['p_hdmi_evf'].translate(cq.Vector(0,0,-CARRIED_DROP_MM)),'usb_5v_head':heads['p_usb_pi'],**headers}
all_cells['carried']=[None]*len(carried_ribbon['segments']);all_bounds['carried']=[bounds(x['box']) for x in carried_ribbon['segments']];all_vertices['carried']=[x['vertices'] for x in carried_ribbon['segments']]
fixed=state_fixed('carried',[n for n in fixed_names if n not in ('pi5','cooler','x1203','x1203_kit','carrier','microsd')])
obstacle_report['carried']=dict(obstacles=fixed,**state_exclusions('carried',fixed))
hits=[];tested=0
for yy in np.arange(0,70.0001,a.step):
 print(f'Carried sweep Y={yy}',flush=True)
 shift=cq.Vector(0,float(yy),0)
 for n,sh in carried.items():
  moved=sh.translate(shift);b=bb(moved)
  for fn in fixed:
   if not overlaps(b,rows[fn]['bbox_mm']):continue
   v=moved.intersect(shapes[fn]).Volume();tested+=1
   if v>.02:hits.append(dict(id=n,fixed=fn,y_offset=float(yy),overlap_mm3=v))
 for i,(s,b) in enumerate(zip(all_cells['carried'],all_bounds['carried'])):
  mb=b.copy();mb[2]+=yy;mb[3]+=yy;possible=[n for n in fixed if potential(n,mb)]
  if not possible:continue
  s=get_cell('carried',i)
  if s is None:continue
  moved=s.translate(shift)
  for fn in possible:
   v=moved.intersect(shapes[fn]).Volume();tested+=1
   if v>.001:hits.append(dict(id='ribbon-cell-'+str(i),fixed=fn,y_offset=float(yy),overlap_mm3=v))
add('carried_sweep','carrier_headers_hdmi_premate',not hits,step_mm=a.step,full_material=True,exact_intersections=tested,hits=hits[:30],hit_count=len(hits),
    evf_head_drop_mm=CARRIED_DROP_MM,evf_stroke_mm=EVF_STROKE_MM,margin_below_mouth_mm=CARRIED_MARGIN_MM,
    ribbon_source='hdmi_routes.ribbon300(158, drop=%.1f): full %.1f mm ribbon, %d cells'%(CARRIED_DROP_MM,carried_ribbon['routed_length_mm'],len(carried_ribbon['segments'])),
    evf_head_mated_top_z=connectors['p_hdmi_evf']['box']['z'][1],evf_head_carried_top_z=connectors['p_hdmi_evf']['box']['z'][1]-CARRIED_DROP_MM,
    note='H2 (VN-43): head and ribbon carried stroke + 3 mm below the mated height (steps.py module_staged); the 9ced753 sweep used the bare stroke (0 mm margin)')
# H2 (VN-43): unplug corridor rows. Obstacles: every material part steps.py has in the body before svc_evf_unplug
# (the head's receptacle board included: the jaws stay below it) and the installed ribbon cells (exact), so a ribbon
# loop in the pliers' path fails too.
_ph,_rt,_op,_before,_after=ST.op_states('svc_evf_unplug')
UNPLUG_FIXED=sorted(set(_before)&material)
obstacle_report['evf_unplug']=dict(obstacles=UNPLUG_FIXED,state_source='steps.py state before service op svc_evf_unplug (route %s)'%_rt)
for _n,_bx in UNPLUG_BOXES.items():
 _sol=bsolid({'x':_bx[0:2],'y':_bx[2:4],'z':_bx[4:6]});_hits=[];_rib=[];_t=0
 for fn in UNPLUG_FIXED:
  if not potential(fn,_bx):continue
  v=_sol.intersect(shapes[fn]).Volume();_t+=1
  if v>.001:_hits.append(dict(part=fn,overlap_mm3=v))
 for i,b in enumerate(all_bounds['installed']):
  if not overlaps(b,_bx):continue
  cl_=get_cell('installed',i)
  if cl_ is None:continue
  v=cl_.intersect(_sol).Volume();_t+=1
  if v>.001:_rib.append(dict(segment=i,overlap_mm3=v))
 add('service_access','evf_head_unplug_'+_n,not _hits and not _rib,box_mm=_bx,exact_intersections=_t,hits=_hits,ribbon_hits=_rib[:20],
     ribbon_hit_count=len(_rib),tool='smooth-jaw long-nose pliers, tips <= 2.0 thick (r7 tool 15; r7 layout.ACCESS acc_hdmi_evf_jaws / acc_hdmi_evf_pliers_svc)',
     stroke_mm=EVF_STROKE_MM,note='Head pulled straight down its stroke by its body; the panel is off (service route evf). Physical grip and finger reach stay a hold (MEASUREMENTS-TO-CLOSE EVF HDMI row).')
# Both HDMI heads disconnected: remove only the complete loom, with Pi/carrier fixed.
if 'both_unplugged' in all_cells:
 hits=[];tested=0
 free_heads={'pi':heads['p_hdmi_pi'].translate(cq.Vector(0,0,6)),'evf':heads['p_hdmi_evf'].translate(cq.Vector(0,0,-6))}
 for yy in np.arange(0,60.0001,a.step):
  print(f'HDMI-only removal Y={yy}',flush=True);shift=cq.Vector(0,float(yy),0)
  for hn,head in free_heads.items():
   moved=head.translate(shift);b=bb(moved)
   for fn in fixed_names:
    if not overlaps(b,rows[fn]['bbox_mm']):continue
    v=moved.intersect(shapes[fn]).Volume();tested+=1
    if v>.02:hits.append(dict(id=hn,fixed=fn,y_offset=float(yy),overlap_mm3=v))
  for i,b in enumerate(all_bounds['both_unplugged']):
   mb=b.copy();mb[2]+=yy;mb[3]+=yy;possible=[n for n in fixed_names if potential(n,mb)]
   if not possible:continue
   cell_=get_cell('both_unplugged',i)
   if cell_ is None:continue
   moved=cell_.translate(shift)
   for fn in possible:
    v=moved.intersect(shapes[fn]).Volume();tested+=1
    if v>.001:hits.append(dict(id='ribbon-cell-'+str(i),fixed=fn,y_offset=float(yy),overlap_mm3=v))
 add('hdmi_only_removal','both_heads_and_full_material',not hits,step_mm=a.step,exact_intersections=tested,hits=hits[:30],hit_count=len(hits),note='Panel and its controls removed first; other flexible looms not included in these rigid STEP obstacles')
# Test-only Pi FPC tool corridor, both with and without HDMI material present.
for xx in ((-87,-79) if a.include_rejected else ()):
 tip=np.array([xx,-4.5,61.5]);entry=np.array([xx,30,87]);d=(entry-tip)/np.linalg.norm(entry-tip)
 tool=cq.Solid.makeCylinder(2,15,cq.Vector(*tip),cq.Vector(*d)).fuse(cq.Solid.makeCylinder(4,75,cq.Vector(*(tip+15*d)),cq.Vector(*d)))
 hits=[]
 for fn in fixed_names:
  if not overlaps(bb(tool),rows[fn]['bbox_mm']):continue
  v=tool.intersect(shapes[fn]).Volume()
  if v>.02:hits.append(dict(part=fn,overlap_mm3=v))
 rh=[]
 for i,(c,b) in enumerate(zip(all_cells['installed'],all_bounds['installed'])):
  if not overlaps(bb(tool),b):continue
  c=get_cell('installed',i)
  if c is None:continue
  v=tool.intersect(c).Volume()
  if v>.001:rh.append(dict(cell=i,overlap_mm3=v))
 add('fpc_tool_without_hdmi',str(xx),not hits,rigid_hits=hits,note='Requires HDMI removed/parked first; real jaws/latch remain measured gates')
 add('fpc_tool_with_hdmi',str(xx),not hits and not rh,rigid_hits=hits,hdmi_hits=rh[:8],hdmi_hit_count=len(rh),note='TEST ONLY:4mm tip for15mm then8mm shank; actual latch/jaws and tool dimensions unmeasured, not a completed release procedure')
if hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()!=manifest_start:raise ValueError('Manifest changed during check')
summary={k:sum(r['status']==k for r in checks) for k in ('pass','fail','info')}
result=dict(selected_service='Pi HDMI stays mated; EVF end disconnected; complete ribbon and heads carried with carrier. Other looms need their own complete checks.',includes_rejected_diagnostics=a.include_rejected,summary=summary,checks=checks,analysis_bbox_mm=analysis_bbox,verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),snapshot_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),mechanical_manifest_sha256=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest(),physical_qualified=False,note='Non-material keepouts are excluded from the physical collision inventory. Convex cells of sampled full-width material. Chord approximation and proxy dimensions require physical gates; this is not a material strength or EMI validation.')
result.update(carried_ribbon_source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('hdmi_routes.py','routes.py')},carried_drop_mm=CARRIED_DROP_MM)  # H2 (VN-43)
result.update(obstacle_sets=obstacle_report,state_model_sha256=hashlib.sha256((ROOT/'steps.py').read_bytes()).hexdigest(),obstacle_rule='FP-12 (VN-30): every material part steps.py has in the body in that state (screws and hardware included) plus the 9ced753 sets; exclusions listed per state; rejected --include-rejected diagnostics keep their 9ced753 sets')
write_text(Path(a.out) if a.out else out/'hdmi-solid-checks.json',json.dumps(result,indent=2));print(json.dumps(summary),flush=True);raise SystemExit(bool(summary['fail']))
