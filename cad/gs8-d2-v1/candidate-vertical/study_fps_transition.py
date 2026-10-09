"""Diagnostic-only rear screw avoidance search; never changes selected routes."""
import json,hashlib,math
from pathlib import Path
import cadquery as cq
import routes as R
from verify_fps_access import tube,bb,box,overlaps,digest
P=Path(__file__).parent;mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(mp.read_text());mh=digest(mp)
nom=json.loads((P/'routing-snapshots/fps-access-20261009-0402/twenty-one-full-wire-shapes.json').read_text())['shapes'][0]
branch=nom['lead_200']['branch'];out=P/'out/fps-service-study';out.mkdir(exist_ok=True)
names=['tub','panel','carrier','p_carrier1','evf_board','switch_1824'];ss={n:cq.importers.importStep(str(mp.parent/'step'/f'{n}.step')).val() for n in names};crop=box([-140,-79,-26,27,25,95])
ss={n:s.intersect(crop) for n,s in ss.items() if overlaps(bb(s),bb(crop))};ss={n:s for n,s in ss.items() if s.Volume()>1e-8}
rows=[]
for xx in [-125,-126,-127,-128,-129,-130,-131]:
 def build(top):return R.rounded_path([[-82.91,-23.4,25],[-82.91,-23.4,33.5],[-103.5,-23.4,33.5],[-103.5,-23.4,top],[-114.5,-23.4,top],[-114.5,-23.4,62.2],[xx,-23.4,62.2],[xx,23.3,62.2],[-133.5,23.3,79.7],[-133.5,15.1,79.7]],5.2,3,3,.15)
 lo,hi=72.6,96
 for _ in range(64):
  mid=(lo+hi)/2;c=build(mid)
  if c['errors']:raise ValueError(c['errors'])
  if c['rounded_length_mm']+branch['rounded_length_mm']>200:hi=mid
  else:lo=mid
 c=build((lo+hi)/2);s,w=tube(c,2.6);row=dict(cross_x=xx,curve=c,clearances=[],hits=[])
 for n,f in ss.items():
  d=s.distance(f);v=0
  if d<1e-7:
   common=s.intersect(f);v=common.Volume()
   if v>1e-6:row['hits'].append(dict(part=n,overlap_mm3=v,bbox_mm=bb(common)))
  row['clearances'].append(dict(part=n,gap_mm=d))
 rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='curve'}),flush=True)
 (out/'transition-search.json').write_text(json.dumps(dict(diagnostic_only=True,mechanical_manifest_sha256=mh,verification_source_sha256=digest(Path(__file__)),routes_source_sha256=digest(P/'routes.py'),rows=rows),indent=2))
