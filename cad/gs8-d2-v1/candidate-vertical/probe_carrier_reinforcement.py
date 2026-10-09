import json,sys,hashlib
from pathlib import Path
import cadquery as cq
import structure_geometry as S
P=Path(__file__).parent;sys.path.insert(0,str(P.parent));import fps_geometry as F
out=P/'out/compact-kowa_lm6hc';m=json.loads((out/'manifest.json').read_text());sh={r['id']:cq.importers.importStep(str(out/'step'/f"{r['id']}.step")).val() for r in m['rows']}
s=S.reinforce_carrier(sh['carrier']);sh.update(F.switch_parts());hits=[]
for n,t in sh.items():
 if n in ('carrier','knob_fps'):continue
 v=s.intersect(t).Volume()
 if v>.002:hits.append(dict(part=n,overlap_mm3=v))
tools=[]
for x in (-95.5,-37.5):
 for z in (10.5,59.5):
  tool=cq.Solid.makeCylinder(3.25,30,cq.Vector(x,21.6,z),cq.Vector(0,1,0))
  v=s.intersect(tool).Volume()
  if v>.002:tools.append(dict(x=x,z=z,overlap_mm3=v))
dest=P/'out/structural-proposals';dest.mkdir(exist_ok=True);cq.exporters.export(s,str(dest/'reinforced-carrier.step'))
r=dict(manifest_sha256=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest(),valid=s.isValid(),solids=len(s.Solids()),added_volume_mm3=s.Volume()-sh['carrier'].Volume(),fixed_hits=hits,kit_driver_corridor_hits=tools,physical_qualified=False)
(dest/'carrier-clearance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
