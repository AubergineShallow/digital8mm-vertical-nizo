import json,hashlib
from pathlib import Path
import cadquery as cq
import structure_geometry as S
P=Path(__file__).parent;out=P/'out/compact-kowa_lm6hc';m=json.loads((out/'manifest.json').read_text())
sh={r['id']:cq.importers.importStep(str(out/'step'/f"{r['id']}.step")).val() for r in m['rows']}
s=S.reinforce_grip(sh['base_grip']);hits=[]
for n in ('cap','pack','tripod_nut','run_button','xt30_pair','tub'):
 v=s.intersect(sh[n]).Volume()
 if v>.002:hits.append(dict(part=n,overlap_mm3=v))
cap=[];added_only=s.cut(sh['base_grip']);new_cap=[]
for i in range(53):
 v=s.intersect(sh['cap'].translate(cq.Vector(i,0,0))).Volume()
 if v>.002:
  base_v=sh['base_grip'].intersect(sh['cap'].translate(cq.Vector(i,0,0))).Volume()
  cap.append(dict(x_shift=i,overlap_mm3=v,baseline_overlap_mm3=base_v))
 av=added_only.intersect(sh['cap'].translate(cq.Vector(i,0,0))).Volume()
 if av>.002:new_cap.append(dict(x_shift=i,added_material_overlap_mm3=av))
dest=P/'out/structural-proposals';dest.mkdir(exist_ok=True);cq.exporters.export(s,str(dest/'reinforced-grip.step'))
r=dict(manifest_sha256=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest(),valid=s.isValid(),solids=len(s.Solids()),added_volume_mm3=s.Volume()-sh['base_grip'].Volume(),fixed_hits=hits,cap_sweep_hits=cap,new_cap_sweep_hits=new_cap,physical_qualified=False)
(dest/'heel-clearance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
