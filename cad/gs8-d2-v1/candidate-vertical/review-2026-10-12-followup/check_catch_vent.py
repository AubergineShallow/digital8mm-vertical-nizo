# SPDX-License-Identifier: MIT
"""Source-bound isolated vent/section check; not adhesive or print qualification."""
import sys,json,hashlib
from pathlib import Path
CV=Path(__file__).resolve().parents[1];sys.path[:0]=[str(CV),str(CV.parent)]
import cadquery as cq
import model as M
from cv_io import write_text
P=Path(__file__).resolve().parent
stock=cq.importers.importStep(str(P/'stock-trial.step')).val()
stub=cq.importers.importStep(str(P/'insert-trial.step')).val()
tub=cq.importers.importStep(str(P/'tub-trial.step')).val()
sp=M.tab_catch_split();v=sp['vent'];p=sp['pocket'];tc={(b['side'],b['kind']):b for b in M.L.tab_catch_boxes()};w=tc[(1,'web')]
x=sum(M.TAB_CATCH_TENON['x'])/2;yin=w['y'][0];edge=w['y'][1]+1.2
wall=M.box(x-.01,x+.01,yin+M.TAB_CATCH_TENON['t']+M.TAB_CATCH_POCKET_CLEAR['y']+M.TAB_CATCH_VENT['depth'],edge,88.49,88.51)
end=M.box(x-.01,x+.01,yin+.79,yin+.81,93.6,95.2)
rows=[dict(id='host_groove_clear',pass_=stock.intersect(v).Volume()<1e-6),dict(id='tenon_not_cut',pass_=stub.intersect(v).Volume()<1e-6),dict(id='groove_connected',pass_=len(v.Solids())==1 and v.isValid()),dict(id='groove_meets_pocket',pass_=v.intersect(p).Volume()>1e-5),dict(id='groove_reaches_accessible_edge',pass_=v.BoundingBox().ymax>edge),dict(id='remaining_host_wall',pass_=wall.cut(stock).Volume()<1e-6,nominal_mm=edge-wall.BoundingBox().ymin,minimum_mm=1.2),dict(id='end_floor_retained',pass_=end.cut(stock).Volume()<1e-6,nominal_mm=1.6,minimum_mm=1.2)]
b=cq.importers.importStep(str(CV/'out/compact-kowa_lm6hc/step/tub.step')).val()
a=M.bounds(tub);bb=M.bounds(b)
rows.append(dict(id='tub_bbox_unchanged',pass_=all(abs(x-y)<.001 for x,y in zip(a,bb)),before=bb,after=a))
r=dict(status='pass' if all(i['pass_'] for i in rows) else 'fail',physical_qualified=False,inputs={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in ['stock-trial.step','insert-trial.step','tub-trial.step']},source_sha256=hashlib.sha256((CV/'model.py').read_bytes()).hexdigest(),checks=rows)
write_text(P/'vent-geometry.json',json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
raise SystemExit(0 if r['status']=='pass' else 1)
