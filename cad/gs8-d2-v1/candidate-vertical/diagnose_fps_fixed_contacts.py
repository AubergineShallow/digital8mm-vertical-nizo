from cv_io import read_text, write_text
import ast,itertools,json,math
from pathlib import Path
import cadquery as cq,numpy as np
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
import routes as R
from verify_fps_access import V,bb,overlaps,digest
P=Path(__file__).parent;tree=ast.parse(read_text(P/'verify_hdmi.py'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cell');exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'verify_hdmi.py'),'exec'));r=R.build();s=json.loads(read_text(P/'out/fps-service-study/fixed-switch-proposal-checks.json'));old=s['hdmi_checks'];out=[]
for state,key in [('installed','hdmi_ribbon'),('premate','hdmi_ribbon_premate')]:
 rows=next(x for x in old if x['state']==state and x['shift_y_mm']==0);idxs=[h['cell'] for h in rows['switch_left_fixed_hits']];hd=r[key]
 for i in idxs:
  c=cell(hd['segments'][i]['vertices'])
  for p in s['switch']['pins']:
   x,z=p['center_xz'];pin=cq.Solid.makeCylinder(.85,4,V(x,7.1,z),V(0,1,0))
   if not overlaps(bb(c),bb(pin)):continue
   q=c.intersect(pin);v=q.Volume()
   if v>1e-7:out.append(dict(state=state,cell=i,pin=p['pin'],overlap_mm3=v,bbox_mm=bb(q)))
shelf=cq.importers.importStep(str(P/'out/fps-service-study/fixed-switch-shelf.step')).val();shelfrows=[]
for h in old:
 if h['shift_y_mm']!=20 or not h['shelf_hits']:continue
 hd=r[{'premate':'hdmi_ribbon_premate','both_unplugged':'hdmi_ribbon_unplugged'}[h['state']]]
 for hit in h['shelf_hits']:
  c=cell(hd['segments'][hit['cell']]['vertices']).translate(V(0,20,0));q=c.intersect(shelf);shelfrows.append(dict(state=h['state'],cell=hit['cell'],overlap_mm3=q.Volume(),bbox_mm=bb(q)))
result=dict(pin_hits=out,shelf_hits=shelfrows);write_text(P/'out/fps-service-study/fixed-switch-contact-diagnosis.json',json.dumps(result,indent=2));print(json.dumps(result),flush=True)
