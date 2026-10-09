"""Check corrected USB hard-head reservation against unchanged full power axes."""
from pathlib import Path
import ast,hashlib,json,math
P=Path(__file__).resolve().parent;OLD=P.parent/'hdmi-ck1044-clear-20261009-0524'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=OLD/'check_head_polyline_distance.py';tree=ast.parse(source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='segbox')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'))
r=json.loads((OLD/'context.json').read_text());d=json.loads((P/'input.json').read_text());head=next(x for x in d['connectors'] if x['id']=='p_usb_pi')['box'];lo=[head[a][0] for a in 'xyz'];hi=[head[a][1] for a in 'xyz'];rows=[]
for core in r['power_geometry']['cores']:
 for part in core['flexible_wire_parts']:
  pts=part['points'];near=min(((*segbox(a,b,lo,hi),i) for i,(a,b) in enumerate(zip(pts,pts[1:]))),key=lambda q:q[0]);radius=core['od_mm']/2+.04
  rows.append(dict(core=core['id'],part=part['id'],radius_with_allowance_mm=radius,axis_to_box_distance_mm=near[0],conservative_gap_mm=near[0]-radius,segment=near[2],parameter=near[1]))
f=r['power_geometry']['fuse'];dist,t=segbox(f['start'],f['end'],lo,hi);rows.append(dict(core='rigid_inline_fuse',radius_mm=f['radius_mm'],conservative_gap_mm=dist-f['radius_mm'],method='Containing finite-axis capsule; source cylinder can occupy no more'))
result=dict(status='pass' if all(x['conservative_gap_mm']>0 for x in rows) else 'requires_exact_intersection',rows=rows,input_sha256=digest(P/'input.json'),
 power_context_sha256=digest(OLD/'context.json'),distance_source_sha256=digest(source),verification_source_sha256=digest(Path(__file__)),physical_qualified=False,
 scope='Static corrected USB head versus every segment of unchanged full modeled power cores and fuse. Full original sampled polylines retained;0.04mm radial allowance. Does not model missing terminal/root material or the unplaced cuttable USB lead.')
(P/'head-power-clearance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
