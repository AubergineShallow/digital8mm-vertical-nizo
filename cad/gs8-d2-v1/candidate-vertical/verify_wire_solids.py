"""Conservative static power-wire capsules versus saved printed solids.
The polyline model, root omissions and flexible service remain explicitly gated.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
from power_geometry import simplify,cylinder,ball
P=Path(__file__).parent;ap=argparse.ArgumentParser();ap.add_argument('--snapshot',required=True);ap.add_argument('--variant',default='compact-kowa_lm6hc');a=ap.parse_args();src=Path(a.snapshot);d=json.loads(src.read_text());out=P/'out'/a.variant;mf=out/'manifest.json';mh=hashlib.sha256(mf.read_bytes()).hexdigest();m=json.loads(mf.read_text())
# Accept the standalone reconciled power structure, never silently a different route.
if 'cores' not in d:raise ValueError('Expected explicit power cores snapshot')
sh={}
for r in m['rows']:
 if r['kind']!='printed':continue
 n=r['id'];f=out/'step'/f'{n}.step'
 if hashlib.sha256(f.read_bytes()).hexdigest()!=m['files'][f'step/{n}.step']:raise ValueError('STEP binding mismatch:'+n)
 sh[n]=cq.importers.importStep(str(f)).val()
 if not sh[n].isValid() or len(sh[n].Solids()) != 1:raise ValueError('Static-wire check requires one valid printed solid: '+n)
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def overlap(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-7 for i in (0,2,4))
bs={n:bb(s) for n,s in sh.items()};faces={n:np.array([bb(f) for f in s.Faces()]) for n,s in sh.items()};classifiers={n:[BRepClass3d_SolidClassifier(q.wrapped) for q in s.Solids()] for n,s in sh.items()}
def potential(n,b):
 if not overlap(bs[n],b):return False
 f=faces[n];mask=np.ones(len(f),dtype=bool)
 for i in (0,2,4):mask&=(np.minimum(f[:,i+1],b[i+1])-np.maximum(f[:,i],b[i]))>0
 if mask.any():return True
 p=gp_Pnt(*[(b[i]+b[i+1])/2 for i in (0,2,4)])
 for c in classifiers[n]:
  c.Perform(p,1e-7)
  if c.State()==TopAbs_IN or c.IsOnAFace():return True
 return False
rows=[]
wire_parts=[dict(core,id=part['id'],core_id=core['id'],geometry_points=part['points']) for core in d['cores'] for part in core['flexible_wire_parts']]
for core in wire_parts:
 points=simplify(core['geometry_points'],.04);r=core['od_mm']/2+.04
 # Segment cylinders plus endpoint balls contain the whole polyline tube.
 pieces=[cylinder(a,b,r) for a,b in zip(points,points[1:]) if np.linalg.norm(np.array(a)-np.array(b))>1e-7]+[ball(p,r) for p in points]
 hits=[];tested=0
 for i,piece in enumerate(pieces):
  if i%25==0:print(core['id'],'capsule piece',i,'/',len(pieces),flush=True)
  b=bb(piece)
  for n,f in sh.items():
   if not potential(n,b):continue
   v=piece.intersect(f).Volume();tested+=1
   if v>.002:hits.append(dict(piece=i,printed_part=n,overlap_mm3=v,bbox=b))
 rows.append(dict(id=core['id'],status='pass' if not hits else 'fail',core_id=core['core_id'],original_points=len(core['geometry_points']),simplified_points=len(points),radius_mm=r,max_polyline_chord_deviation_mm=.04,exact_intersections=tested,hits=hits,root_joint_omission_mm=core['unmodeled_root_joint_allowance_mm'],root_warning=core['root_warning']))
if hashlib.sha256(mf.read_bytes()).hexdigest()!=mh:raise ValueError('Manifest changed during check')
result=dict(status='pass' if all(r['status']=='pass' for r in rows) else 'fail',rows=rows,manifest_sha256=mh,snapshot_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),helper_source_sha256=hashlib.sha256((P/'power_geometry.py').read_bytes()).hexdigest(),physical_qualified=False,scope='Static power-wire conservative capsules versus printed solids only. No socket/pad/contact waiver, and no assertion that omitted root joints are solved. Purchased-part and wire-wire checks are separate source-envelope studies. Positive finished allocation includes rigid fuse/joint zone; it is not270mm copper plus fuse.',remaining_stop=['Full flexible withdrawal/staging','Real pad/pin/lug geometry and joint cut convention','Retention and abrasion','Supplier bend capability, hot drop and thermal tests'])
(out/'wire-solid-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);raise SystemExit(result['status']!='pass')
