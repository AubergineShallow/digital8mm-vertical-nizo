"""Mechanical reservations from frozen provisional power routing. Physical gates remain open."""
import json,math
from pathlib import Path
from functools import lru_cache
import cadquery as cq
V=cq.Vector
SOURCE=Path(__file__).parent/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'
DATA=json.loads(SOURCE.read_text())
def cylinder(a,b,r):
 a=V(*a);d=V(*b)-a;return cq.Solid.makeCylinder(r,d.Length,a,d.normalized())
def ball(p,r):
    # CadQuery makeSphere defaults to a hemisphere; both bend hemispheres are required.
    return cq.Solid.makeSphere(r,V(*p),angleDegrees1=-90,angleDegrees2=90)
def pose(shape,p):
 m=p['matrix'];ref=DATA['source_oldframe_reference'];pitch=math.degrees(math.atan2(-m[2][0],m[2][2]));yaw=math.degrees(math.atan2(m[1][0],m[0][0]))
 return shape.translate(V(*[-x for x in ref])).rotate((0,0,0),(0,1,0),pitch).rotate((0,0,0),(0,0,1),yaw).translate(V(*p['center']))
def simplify(pts,tol=.04):
 if len(pts)<3:return pts
 a=V(*pts[0]);ab=V(*pts[-1])-a;l=ab.dot(ab);ds=[]
 for p in pts[1:-1]:
  ap=V(*p)-a;t=max(0,min(1,ap.dot(ab)/l)) if l else 0;ds.append((ap-ab*t).Length)
 if max(ds)<=tol:return [pts[0],pts[-1]]
 k=ds.index(max(ds))+1;return simplify(pts[:k+1],tol)[:-1]+simplify(pts[k:],tol)
def prism_xy(pts,z0,z1):
 w=cq.Wire.makePolygon([V(x,y,z0) for x,y in pts]+[V(*pts[0],z0)])
 return cq.Solid.extrudeLinear(w,[],V(0,0,z1-z0))
@lru_cache(None)
def local_cutters():
 cutters=[]
 for path in DATA['pocket_paths']:
  pts=simplify(path['points']);r=path['radius_mm']+.04
  for a,b in zip(pts,pts[1:]):
   if min(a[2],b[2])-r<3 and max(a[2],b[2])+r>-12:cutters.append(cylinder(a,b,r))
  for p in pts:
   if -14<p[2]<5:cutters.append(ball(p,r))
 cutters.append(cylinder(DATA['fuse']['start'],DATA['fuse']['end'],2.8))
 return cutters
@lru_cache(None)
def floor_hull():
 # Conservative circumscribed disks around every sampled axis segment touching floor.
 # Convex union covers between-axis translations too; it deliberately reserves extra space.
 pts=[];r=3.0  # 0.5mm radial service reserve also joins tiny inter-pocket slivers
 for p in DATA['rigid_service_poses']:
  a,b=p['fuse_start'],p['fuse_end'];ts=[(-r-a[2])/(b[2]-a[2]),(2.5+r-a[2])/(b[2]-a[2])];lo=max(0,min(ts));hi=min(1,max(ts))
  if hi<lo:continue
  for t in (lo,hi):
   c=[a[i]+t*(b[i]-a[i]) for i in range(3)]
   for j in range(64):pts.append((c[0]+r/math.cos(math.pi/64)*math.cos(j*math.tau/64),c[1]+r/math.cos(math.pi/64)*math.sin(j*math.tau/64)))
 pts=sorted(set(pts))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 halves=[]
 for seq in (pts,list(reversed(pts))):
  h=[]
  for p in seq:
   while len(h)>1 and cross(h[-2],h[-1],p)<=0:h.pop()
   h.append(p)
  halves.append(h[:-1])
 return halves[0]+halves[1]
def tub_cuts():
 return local_cutters()+[prism_xy(floor_hull(),-.1,2.6),prism_xy([(-78,-13.01),(-74.99,-13.01),(-74.99,-10)],-1.9,2.6)]
def grip_cuts():
 return local_cutters()+[cq.Solid.makeBox(31,21.4,10.1,V(-66,-12.4,-10))]


def cut_passages(shape, cutters):
 """Cut overlapping capsule tools sequentially; validate each kernel result.

 A single multi-tool Boolean can create invalid zero-volume tool unions at
 tangent capsule joins. No clearance or collision threshold is relaxed here.
 """
 if not shape.isValid() or len(shape.Solids()) != 1:
  raise ValueError('Power passage input must be one valid solid')
 for i, cutter in enumerate(reversed(cutters)):
  result = shape.copy().cut(cutter.copy())
  if not result.isValid() or len(result.Solids()) != 1:
   raise ValueError(f'Power passage cut {i} failed solid validity: valid={result.isValid()}, solids={len(result.Solids())}')
  shape = result
 return shape
