"""Conservative exact-arc bounds for every complete selected FPS wire primitive."""
from pathlib import Path
import hashlib,json,math
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sub(a,b):return [x-y for x,y in zip(a,b)]
def add(a,b):return [x+y for x,y in zip(a,b)]
def mul(v,s):return [x*s for x in v]
def norm(v):return mul(v,1/math.sqrt(sum(x*x for x in v)))
def bb(points,r):return {a:[min(p[j] for p in points)-r,max(p[j] for p in points)+r] for j,a in enumerate('xyz')}
def overlap(a,b):return all(min(a[k][1],b[k][1])-max(a[k][0],b[k][0])>1e-9 for k in 'xyz')
data=json.loads((P/'mated-carry-input.json').read_text());h=json.loads((P/'usb2-head-reservation.json').read_text())['box'];rows=[]
for wire in data['wire_parts']:
 c=wire['curve'];pts=c['knots'];rad=c['centerline_radius_mm'];r=wire['od_mm']/2;last=pts[0];primitives=[]
 for i in range(1,len(pts)-1):
  angle=math.radians(c['turn_degrees'][i])
  if angle<1e-8:continue
  u=norm(sub(pts[i],pts[i-1]));v=norm(sub(pts[i+1],pts[i]));trim=c['corner_trim_mm'][i]
  enter=sub(pts[i],mul(u,trim));leave=add(pts[i],mul(v,trim));center=add(pts[i],mul(norm(sub(v,u)),rad/math.cos(angle/2)))
  if math.dist(last,enter)>1e-8:primitives.append(dict(kind='line',bounds=bb([last,enter],r)))
  e=mul(sub(enter,center),1/rad);ts=[0,angle]
  for j in range(3):
   theta=math.atan2(u[j],e[j])
   for k in range(-2,3):
    q=theta+k*math.pi
    if 0<q<angle:ts.append(q)
  extrema=[add(center,mul(add(mul(e,math.cos(t)),mul(u,math.sin(t))),rad)) for t in ts]
  assert math.dist(extrema[0],enter)<1e-6 and math.dist(extrema[1],leave)<1e-6
  primitives.append(dict(kind='circular_arc',bounds=bb(extrema,r)));last=leave
 if math.dist(last,pts[-1])>1e-8:primitives.append(dict(kind='line',bounds=bb([last,pts[-1]],r)))
 possible=[i for i,q in enumerate(primitives) if overlap(h,q['bounds'])]
 rows.append(dict(wire=wire['id'],complete_analytic_axis_mm=c['rounded_length_mm'],od_mm=wire['od_mm'],primitive_count=len(primitives),possible_intersections=possible,primitives=primitives,status='pass_by_conservative_exact_arc_bounds' if not possible else 'requires_exact_solid_intersection'))
result=dict(status='pass' if all(not q['possible_intersections'] for q in rows) else 'requires_exact_solid_intersection',
 method='Exact extrema of each analytic circular arc and line, expanded in every direction by full wire radius. Disjoint primitive boxes prove no tube material reaches the head; no sampled centreline clearance assumption.',
 rows=rows,input_sha256=sha(P/'input.json'),fps_input_sha256=sha(P/'mated-carry-input.json'),source_sha256=sha(Path(__file__)),physical_qualified=False)
(P/'head-fps-exact-arc-bounds.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':result['status'],'wires':[{k:q[k] for k in ('wire','status','primitive_count','possible_intersections')} for q in rows]},indent=2))
