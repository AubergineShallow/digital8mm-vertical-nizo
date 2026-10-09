"""Exact original power-polyline segment distance to HDMI head AABB hypotheses."""
import hashlib,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((P/'context.json').read_text());d=json.loads((P/'input.json').read_text())
h=next(c for c in d['connectors'] if c['id']=='p_hdmi_pi')['box']
def segbox(a,b,lo,hi):
 v=[y-x for x,y in zip(a,b)];ts=[0.,1.]
 for j in range(3):
  if abs(v[j])>1e-12:
   ts += [t for z in [lo[j],hi[j]] if 0<(t:=(z-a[j])/v[j])<1]
 ts=sorted(set(ts));best=(math.inf,None)
 def value(t):return sum(max(lo[j]-(a[j]+v[j]*t),0,a[j]+v[j]*t-hi[j])**2 for j in range(3))
 for t0,t1 in zip(ts,ts[1:]):
  mid=(t0+t1)/2;aa=bb=0
  for j in range(3):
   x=a[j]+v[j]*mid
   if x<lo[j]:c=a[j]-lo[j]
   elif x>hi[j]:c=a[j]-hi[j]
   else:continue
   aa+=v[j]**2;bb+=v[j]*c
  t=max(t0,min(t1,-bb/aa)) if aa else mid
  for q in (t0,t,t1):
   val=value(q)
   if val<best[0]:best=val,q
 return math.sqrt(best[0]),best[1]
out=[]
for state,lift,ys in [('installed_pi_mated',0,[0]),('rejected_in_body_pi_unplug_and_translate',6,range(0,61,2))]:
 for dy in ys:
  lo=[h['x'][0],h['y'][0]+dy,h['z'][0]+lift];hi=[h['x'][1],h['y'][1]+dy,h['z'][1]+lift];near=[]
  for core in r['power_geometry']['cores']:
   for part in core['flexible_wire_parts']:
    pts=part['points'];res=min(((*segbox(a,b,lo,hi),i) for i,(a,b) in enumerate(zip(pts,pts[1:]))),key=lambda q:q[0])
    near.append(dict(core=core['id'],part=part['id'],distance_mm=res[0],nominal_surface_gap_mm=res[0]-core['od_mm']/2,segment=res[2],parameter=res[1],segment_ends=pts[res[2]:res[2]+2]))
  out.append(dict(state=state,pi_lift_mm=lift,shift_y_mm=dy,near=near))
result=dict(method='Exact distance between each original full sampled polyline segment and shifted hard-head AABB; no simplification or radial padding',
 context_sha256=digest(P/'context.json'),input_sha256=digest(P/'input.json'),source_sha256=digest(Path(__file__)),rows=out,
 selected_sequence='Keep Pi head mated and carry it with carrier; do not use rejected +Z6 in-body diagnostic as an assembly instruction',physical_qualified=False)
(P/'power-head-distance-complete.json').write_text(json.dumps(result,indent=2))
print(json.dumps([row for row in out if row['shift_y_mm']==0],indent=2))
