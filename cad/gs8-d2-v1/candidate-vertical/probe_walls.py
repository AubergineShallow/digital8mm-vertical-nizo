import cadquery as cq
from pathlib import Path
p=Path(__file__).resolve().parent/'out/compact-kowa_lm6hc/step'
rows=[('panel_skin','panel',(-90,20,50),(-90,32,50)),('panel_bearing','panel',(-147.2,20,8.3),(-147.2,32,8.3)),('carrier_pad','carrier',(-35.5,10,10.5),(-35.5,23,10.5)),('carrier_PT_wall','carrier',(-134,20,55),(-130.2,20,55)),('collar_hoop','lens_collar',(5,20,60),(5,27,60)),('tub_wall','tub',(-80,-32,50),(-80,-20,50)),('tub_floor','tub',(-100,20,-1),(-100,20,7)),('tub_roof','tub',(-80,0,95),(-80,0,102)),('grip_rear','base_grip',(-73,0,-50),(-66,0,-50)),('grip_upper_web','base_grip',(-73,0,-8.5),(-63,0,-8.5)),('carrier_tie_eye_land','carrier',(-97,18.5,25),(-93.5,18.5,25))]
for name,pid,a,b in rows:
 s=cq.importers.importStep(str(p/f'{pid}.step')).val();e=cq.Edge.makeLine(cq.Vector(*a),cq.Vector(*b));r=s.intersect(e)
 print(name,sum(q.Length() for q in r.Edges()),len(r.Edges()),flush=True)
