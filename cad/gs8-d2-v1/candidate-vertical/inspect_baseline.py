import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq,layout as L,cots
rows={}
for p in L.PARTS:
 s=cq.importers.importStep(str(R/'out/step/parts'/f'{p}.step')).val(); b=s.BoundingBox()
 rows[p]={'kind':'printed','bbox':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'volume':s.Volume()}
for p,r in cots.build_all(L).items():
 if r.get('shape'):
  s=r['shape'].val();b=s.BoundingBox();rows[p]={'kind':r['kind'],'bbox':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'volume':s.Volume(),'mass':r['mass']}
box=[min(r['bbox'][i] for r in rows.values()) if i%2==0 else max(r['bbox'][i] for r in rows.values()) for i in range(6)]
print(json.dumps({'bbox':box,'dimensions':[box[i+1]-box[i] for i in (0,2,4)],'rows':rows},indent=2))
