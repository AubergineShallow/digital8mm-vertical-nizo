"""Exact printed-solid checks of the frozen complete-material HDMI reservation.
The reservation is a sampled developable strip, not a strength/material approval.
"""
import argparse,hashlib,json,itertools,math,time
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
p=argparse.ArgumentParser();p.add_argument('--variant',default='compact-kowa_lm6hc');p.add_argument('--snapshot',required=True);p.add_argument('--step',type=float,default=2);p.add_argument('--include-rejected',action='store_true',help='Reproduce archived in-body Pi-unplug and obsolete FPC-tool diagnostics; not selected service');a=p.parse_args()
ROOT=Path(__file__).resolve().parent;out=ROOT/'out'/a.variant;src=Path(a.snapshot);snap=json.loads(src.read_text());meta=json.loads((out/'manifest.json').read_text())
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
for row in snap['header_housings']+[q for q in snap['connectors'] if q['id'] in ('p_hdmi_pi','p_hdmi_evf','p_usb_pi')]:
 b=bounds(row['box']);zpad=6 if row['id'] in ('p_hdmi_pi','p_hdmi_evf') else 0;query_boxes.extend([[b[0],b[1],b[2],b[3]+70,b[4]-zpad,b[5]+zpad]])
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
fixed_names=[n for n,r in rows.items() if not n.startswith(('p_','s_')) and n not in ('panel','encoder','switch_1824','knob_exp','knob_fps','power_button','power_nut_reserve','fps_nut','fps_mounting_washer','usb_stick')]
printed=[n for n,r in rows.items() if r['kind']=='printed' and n not in ('panel','knob_exp','knob_fps')]
for n,head in heads.items():
 hits=[]
 for fn in printed:
  if not overlaps(bb(head),rows[fn]['bbox_mm']):continue
  v=head.intersect(shapes[fn]).Volume()
  if v>.02:hits.append(dict(part=fn,overlap_mm3=v))
 add('hard_head_vs_printed',n,not hits,hits=hits)
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
  b=bounds(seg['box']);possible=[n for n in fixed_names+[n for n in ['panel','encoder','switch_1824','power_button','power_nut_reserve','fps_nut','fps_mounting_washer'] if n in rows] if potential(n,b)]
  if not possible:continue
  s=get_cell(state,i)
  if s is None:continue
  for fn in possible:
   v=s.intersect(shapes[fn]).Volume();tested+=1
   if v>.001:hits.append(dict(segment=i,part=fn,overlap_mm3=v,bbox=bb(s.intersect(shapes[fn]))))
 add('full_ribbon_vs_solids',state,not hits,material_length_mm=rr['routed_length_mm'],cells=len(rr['segments']),exact_intersections=tested,hits=hits[:25],hit_count=len(hits),max_overlap_mm3=max((h['overlap_mm3'] for h in hits),default=0))
# Rigid carried pre-mate shape + adapters + headers. Ribbon/head stay below EVF mouth until final6mm upward mate.
carried={'pi_head':heads['p_hdmi_pi'],'evf_head':heads['p_hdmi_evf'].translate(cq.Vector(0,0,-6)),'usb_5v_head':heads['p_usb_pi'],**headers}
fixed=[n for n in fixed_names if n not in ('pi5','cooler','x1203','x1203_kit','carrier','microsd')]
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
 for i,(s,b) in enumerate(zip(all_cells['premate'],all_bounds['premate'])):
  mb=b.copy();mb[2]+=yy;mb[3]+=yy;possible=[n for n in fixed if potential(n,mb)]
  if not possible:continue
  s=get_cell('premate',i)
  if s is None:continue
  moved=s.translate(shift)
  for fn in possible:
   v=moved.intersect(shapes[fn]).Volume();tested+=1
   if v>.001:hits.append(dict(id='ribbon-cell-'+str(i),fixed=fn,y_offset=float(yy),overlap_mm3=v))
add('carried_sweep','carrier_headers_hdmi_premate',not hits,step_mm=a.step,full_material=True,exact_intersections=tested,hits=hits[:30],hit_count=len(hits))
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
result=dict(selected_service='Pi HDMI stays mated; EVF end disconnected; complete ribbon and heads carried with carrier. Other looms need their own complete checks.',includes_rejected_diagnostics=a.include_rejected,summary=summary,checks=checks,analysis_bbox_mm=analysis_bbox,verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),snapshot_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),mechanical_manifest_sha256=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest(),physical_qualified=False,note='Convex cells of sampled full-width material. Chord approximation and proxy dimensions require physical gates; this is not a material strength or EMI validation.')
(out/'hdmi-solid-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(summary),flush=True);raise SystemExit(bool(summary['fail']))
