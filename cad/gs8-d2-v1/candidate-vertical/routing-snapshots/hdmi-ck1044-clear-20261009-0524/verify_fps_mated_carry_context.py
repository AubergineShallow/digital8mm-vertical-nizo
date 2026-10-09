"""Bound deployed FPS pair mated and fully co-carried snapshot against the complete corrected HDMI."""
import ast,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
P=Path(__file__).resolve().parent;V=cq.Vector
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def bounds(b):return [x for k in 'xyz' for x in b[k]]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,2,4))
def box(b):return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))
for name,functions in [('source-verify_hdmi.py',{'cell'}),('source-verify_fps_access.py',{'rounded_wire','tube'})]:
 tree=ast.parse((P/name).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/name),'exec'))
f=json.loads((P/'fps-mated-carry-context-0556.json').read_text());d=json.loads((P/'input.json').read_text())
objects={w['id']:tube(w['curve'],w['od_mm'])[0] for w in f['wire_parts']}
objects['junction_entire_reference_box']=box(bounds(f['junction']['box']))
objects['junction_protective_reservation']=box(bounds(f['junction']['protective_reserve']))
ob={n:bb(s) for n,s in objects.items()};checks=[]
for state in ['installed','premate','both_unplugged']:
 hits=[];tests=0
 for i,seg in enumerate(d['hdmi_'+state]['segments']):
  possible=[n for n,b in ob.items() if overlaps(bounds(seg['box']),b)]
  if not possible:continue
  c=cell(seg['vertices'])
  if c is None:continue
  for n in possible:
   common=c.intersect(objects[n]);tests+=1;v=common.Volume()
   if v>1e-7:hits.append(dict(cell=i,obstacle=n,overlap_mm3=v,bbox_mm=bb(common)))
 checks.append(dict(state=state,status='pass' if not hits else 'fail',hits=hits,exact_intersections=tests))
 print(state,len(hits),tests,flush=True)
result=dict(status='pass' if all(c['status']=='pass' for c in checks) else 'fail',checks=checks,
 fps_input_sha256=digest(P/'fps-mated-carry-context-0556.json'),fps_source_sha256=digest(P/'source-fps_ck1044_mated_carry-0556.py'),
 hdmi_input_sha256=digest(P/'input.json'),verification_source_sha256=digest(Path(__file__)),physical_qualified=False,
 scope='Full analytic round wires and entire connector/protective boxes at pair mated and fully co-carried versus each full sampled HDMI strip.',
 selected_relative_motion='If the complete pair mated and fully co-carried FPS wires and the premate HDMI translate together with the carrier, their relative geometry is unchanged. No validation of movement versus fixed hardware, unrelated flexible looms, wire stock roots or actual connector operation is implied.')
(P/'fps-mated-carry-context-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
