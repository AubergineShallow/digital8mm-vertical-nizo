"""Exploratory source-bound power pockets and rigid service; not release geometry."""
from cv_io import read_text, write_text
import json,math
from pathlib import Path
import cadquery as cq
import model as M
import power_geometry as PG
P=Path(__file__).parent
s=json.loads(read_text(P/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'))
V=cq.Vector
out=P/'out/power-fit-study';out.mkdir(exist_ok=True)
r={n:dict(shape=cq.importers.importStep(str(P/'out/compact-kowa_lm6hc/step'/f'{n}.step')).val()) for n in ('tub','base_grip')};print('STEP loaded',flush=True)
orig=M.cots.xt30_pair(M.L,M.L.COTS['xt30_pair']);pair=max(orig.Solids(),key=lambda q:q.Volume())
ref=s['source_oldframe_reference']
def pose(sh,d):
 mat=d['matrix'];c=d['center'];t=[c[i]-sum(mat[i][j]*ref[j] for j in range(3)) for i in range(3)]
 pitch=math.degrees(math.atan2(-mat[2][0],mat[2][2]));yaw=math.degrees(math.atan2(mat[1][0],mat[0][0]))
 return sh.translate(V(*[-x for x in ref])).rotate((0,0,0),(0,1,0),pitch).rotate((0,0,0),(0,0,1),yaw).translate(V(*c))
def cylinder(a,b,radius):
 a=V(*a);v=V(*b)-a;return cq.Solid.makeCylinder(radius,v.Length,a,v.normalized())
def bb(sh):return M.bounds(sh)
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-6 for i in (0,2,4))
# Subsample dense centerline with a conservative chord-deviation inflation.
def simplify(pts,tol=.04):
 if len(pts)<3:return pts
 a=V(*pts[0]);ab=V(*pts[-1])-a;l=ab.dot(ab)
 ds=[]
 for p in pts[1:-1]:
  ap=V(*p)-a;f=max(0,min(1,ap.dot(ab)/l)) if l else 0;ds.append((ap-ab*f).Length)
 d=max(ds)
 if d<=tol:return [pts[0],pts[-1]]
 k=ds.index(d)+1;return simplify(pts[:k+1],tol)[:-1]+simplify(pts[k:],tol)
cutters=[]
for path in s['pocket_paths']:
 pts=simplify(path['points']);rad=path['radius_mm']+.04
 for a,b in zip(pts,pts[1:]):
  if min(a[2],b[2])-rad<3 and max(a[2],b[2])+rad>-12:cutters.append(cylinder(a,b,rad))
 for p in pts:
  if -14<p[2]<5:cutters.append(PG.ball(p,rad))
cutters.append(cylinder(s['fuse']['start'],s['fuse']['end'],2.8))
print('Pocket cutters',len(cutters),flush=True)
# The upper grip web must admit the tilted plug. Retain the baseline sliding slots.
new={n:r[n]['shape'] for n in ['tub','base_grip']}
new['base_grip']=new['base_grip'].cut(M.box(-66,-35,-12.4,9,-10,.1))
for n in new:
 new[n]=new[n].cut(*cutters).clean();print(n,new[n].isValid(),len(new[n].Solids()),flush=True)
 cq.exporters.export(new[n],str(out/f'{n}.step'))
# Deliberate 3mm corner relief removes the accidental sliver at the rear neck.
pts=[(-78,-13.01),(-74.99,-13.01),(-74.99,-10)]
wire=cq.Wire.makePolygon([V(x,y,-1.9) for x,y in pts]+[V(*pts[0],-1.9)])
relief=cq.Solid.extrudeLinear(wire,[],V(0,0,4.5))
new['tub']=new['tub'].cut(relief,PG.prism_xy(PG.floor_hull(),-.1,2.6)).clean();cq.exporters.export(new['tub'],str(out/'tub-relieved.step'))
print('Relieved tub',new['tub'].isValid(),len(new['tub'].Solids()),flush=True)
hits=[]
for i,d in enumerate(s['rigid_service_poses']):
 if i%20==0:print('Pose',i,flush=True)
 moved={'pair':pose(pair,d),'fuse':cylinder(d['fuse_start'],d['fuse_end'],2.5)}
 for name,sh in moved.items():
  for fn,solid in new.items():
   if not overlaps(bb(sh),bb(solid)):continue
   inter=sh.intersect(solid);v=inter.Volume()
   if v>.02:hits.append(dict(pose=i,part=name,fixed=fn,volume_mm3=v,bbox=bb(inter)))
print(json.dumps(dict(hits=hits[:30],count=len(hits))),flush=True)
write_text(out/'result.json',json.dumps(dict(hits=hits,physical_qualified=False),indent=2))
