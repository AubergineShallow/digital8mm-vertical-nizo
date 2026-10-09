"""Supplemental exact ribbon/carrier check for the proposed reinforced STEP."""
import ast,hashlib,itertools,json,math,shutil
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def bounds(b):return [x for k in 'xyz' for x in b[k]]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,2,4))
tree=ast.parse((P/'source-verify_hdmi.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cell')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'source-verify_hdmi.py'),'exec'))
src=ROOT/'out/structural-proposals/reinforced-carrier.step';h=digest(src);s=cq.importers.importStep(str(src)).val()
copy=P/'reinforced-carrier-input.step'
if copy.exists() and digest(copy)!=h:raise ValueError('Named supplemental input already exists with different contents')
if not copy.exists():shutil.copyfile(src,copy)
assert s.isValid() and len(s.Solids())==1
d=json.loads((P/'input.json').read_text());checks=[]
for state in ['installed','premate','both_unplugged']:
 hits=[];tests=0;minimum=math.inf
 for i,seg in enumerate(d['hdmi_'+state]['segments']):
  b=bounds(seg['box']);wide=[v+(-1 if j%2==0 else 1) for j,v in enumerate(bb(s))]
  if not overlaps(b,wide):continue
  c=cell(seg['vertices'])
  if c is None:continue
  distance=c.distance(s);minimum=min(minimum,distance)
  if not overlaps(b,bb(s)):continue
  common=c.intersect(s);tests+=1;v=common.Volume()
  if v>1e-7:hits.append(dict(cell=i,volume_mm3=v,bbox_mm=bb(common)))
 checks.append(dict(state=state,status='pass' if not hits else 'fail',full_material_mm=d['hdmi_'+state]['routed_length_mm'],exact_intersections=tests,hits=hits,minimum_nearby_distance_mm=minimum if math.isfinite(minimum) else None))
if digest(src)!=h:raise ValueError('Reinforced STEP changed during check')
result=dict(status='pass' if all(c['status']=='pass' for c in checks) else 'fail',checks=checks,
 step_sha256=h,input_sha256=digest(P/'input.json'),source_sha256=digest(Path(__file__)),physical_qualified=False,
 selected_motion='Premate ribbon and reinforced carrier translate together in the selected sequence, so their relative geometry is constant. This checks that mutual clearance, not the combined swept volume versus external wires or solids.',
 remaining='Parent must recheck reinforced carrier against fixed parts; complete carried/stowed loom deployment and FPC remain open. Both-unplugged is a separate rejected in-body head-motion diagnostic.')
(P/'reinforced-carrier-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
