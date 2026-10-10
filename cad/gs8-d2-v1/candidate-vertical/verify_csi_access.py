"""Bounded tool-reservation check for the functional cooler-side CSI service slot.
This does not supply measured latch tabs, opened tweezers jaws, or actuation travel.
"""
from cv_io import read_text, write_text
import json,hashlib,math
from pathlib import Path
import cadquery as cq
P=Path(__file__).parent;out=P/'out/compact-kowa_lm6hc';mf=out/'manifest.json';m=json.loads(read_text(mf));binding=hashlib.sha256(mf.read_bytes()).hexdigest();sh={}
for r in m['rows']:
 n=r['id'];f=out/'step'/f'{n}.step'
 if hashlib.sha256(f.read_bytes()).hexdigest()!=m['files'][f'step/{n}.step']:raise ValueError('STEP hash mismatch:'+n)
 sh[n]=cq.importers.importStep(str(f)).val()
V=cq.Vector
back=V(0,-1,.1).normalized();rows=[]
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def overlap(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-7 for i in (0,2,4))
bounds={n:bb(s) for n,s in sh.items()}
for x in (-87.,-79.):
 tip=V(x,-4,61.5);tool=cq.Solid.makeCylinder(2,15,tip,back).fuse(cq.Solid.makeCylinder(4,75,tip+back*15,back));hits=[];tests=0
 for travel in range(0,101,2):
  moving=tool.translate(back*travel);b=bb(moving)
  for n,f in sh.items():
   if not overlap(b,bounds[n]):continue
   v=moving.intersect(f).Volume();tests+=1
   if v>.02:hits.append(dict(travel_mm=travel,fixed=n,overlap_mm3=v))
 rows.append(dict(target_x_mm=x,status='pass' if not hits else 'fail',hits=hits,exact_intersections=tests,tip_stop_mm=tip.toTuple(),back_axis=back.toTuple(),tip_diameter_mm=4,tip_length_mm=15,shank_diameter_mm=8,shank_length_mm=75,withdrawal_mm=100,step_mm=2))
result=dict(status='pass' if all(r['status']=='pass' for r in rows) else 'fail',rows=rows,manifest_sha256=binding,verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),physical_qualified=False,scope='Clearance of declared tool reserve through slot only. Tip stops before coarse socket face; no connector-contact waiver.',remaining_stop=['Actual latch tab positions, open jaws and latch travel','Full FPC and other flexible loom occupancy','Measured tweezers profile, hand access and force','Actual isolation and service procedure'])
if hashlib.sha256(mf.read_bytes()).hexdigest()!=binding:raise ValueError('Manifest changed during verification')
write_text(out/'csi-access-checks.json',json.dumps(result,indent=2));print(json.dumps(result));raise SystemExit(result['status']!='pass')
