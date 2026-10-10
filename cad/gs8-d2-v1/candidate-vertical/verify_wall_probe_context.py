"""Resolve the obsolete wall ray crossing the intentional CSI opening, without rewriting main audit."""
from cv_io import read_text, write_text
from pathlib import Path
import json,hashlib,time
import cadquery as cq
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';mf=D/'manifest.json';mh=hashlib.sha256(mf.read_bytes()).hexdigest();m=json.loads(read_text(mf));f=D/'step/tub.step'
assert hashlib.sha256(f.read_bytes()).hexdigest()==m['files']['step/tub.step']
s=cq.importers.importStep(str(f)).val();rows=[]
for name,x,z,expected in [('obsolete_ray_inside_CSI_opening',-80,50,0),('wall_above_CSI_opening',-80,72,1.6),('wall_ahead_of_CSI_opening',-73,50,1.6),('wall_behind_CSI_opening',-93,50,1.6)]:
 a=(x,-32,z);b=(x,-20,z);es=s.intersect(cq.Edge.makeLine(cq.Vector(*a),cq.Vector(*b))).Edges();v=sum(e.Length() for e in es)
 rows.append(dict(id=name,origin=a,end=b,material_span_mm=v,spans=len(es),expected='empty designed slot' if expected==0 else 'local wall >=1.6mm',passed=(len(es)==0 if expected==0 else len(es)==1 and v>=expected-1e-7)))
r=dict(manifest_sha256=mh,verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),checks=rows,status='pass' if all(x['passed'] for x in rows) else 'fail',interpretation='Main audit tub_right_wall ray is obsolete because it crosses the intentional CSI opening. Original 288/2/18 report is retained; this supplement checks only three adjacent actual STEP wall locations and the opening. It is not a global minimum-wall or structural qualification.',physical_qualified=False)
assert hashlib.sha256(mf.read_bytes()).hexdigest()==mh
write_text(D/'wall-probe-context.json',json.dumps(r,indent=2));print(json.dumps(r),flush=True)
