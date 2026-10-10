"""Check a declared straight tool reservation at source-registered CAM/DISP1.

A closed connector model cannot prove opening travel, real jaws, an engaged FPC,
or cooler clearance. This report always retains that operational HOLD.
"""
from cv_io import read_text, write_text
import hashlib,json,time
from pathlib import Path
import cadquery as cq
import official_pi5_geometry as OP
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def overlap(a,b):return all(min(a[i+1],b[i+1])>max(a[i],b[i])+1e-7 for i in (0,2,4))
mh=digest(D/'manifest.json');m=json.loads(read_text(D/'manifest.json'));parts={}
for r in m['rows']:
 f=D/'step'/(r['id']+'.step')
 if digest(f)!=m['files']['step/'+f.name]:raise ValueError('Stale STEP:'+f.name)
 parts[r['id']]=cq.importers.importStep(str(f)).val()
latch=OP.csi_latch_bounds(bracket=True)['cam_disp1']['box'];x=sum(latch['x'])/2
front=latch['y'][0]-.1;tools=[];checks=[]
for label,z in [('lower_end',latch['z'][0]),('upper_end',latch['z'][1])]:
 start=cq.Vector(x,front,z);direction=cq.Vector(0,-1,0)
 tool=cq.Solid.makeCylinder(2,15,start,direction).fuse(cq.Solid.makeCylinder(4,75,start+direction*15,direction))
 hits=[]
 for name,s in parts.items():
  if not overlap(bb(tool),bb(s)):continue
  iv=tool.intersect(s).Volume()
  if iv>.002:hits.append({'part':name,'intersection_mm3':iv})
 tools.append({'id':label,'tip':list(start.toTuple()),'axis':[0,-1,0],'tip_diameter_mm':4,'tip_length_mm':15,'shaft_diameter_mm':8,'shaft_length_mm':75})
 checks.append({'id':label,'declared_reservation_clear':not hits,'hits':hits})
if digest(D/'manifest.json')!=mh:raise ValueError('Manifest changed during check')
report={'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'mechanical_manifest_sha256':mh,'verification_source_sha256':digest(Path(__file__)),
 'source_helper_sha256':digest(P/'official_pi5_geometry.py'),'latch_source':OP.csi_latch_bounds(bracket=True)['cam_disp1'],
 'tool_reservations':tools,'checks':checks,'declared_rigid_reservation_clear':all(c['declared_reservation_clear'] for c in checks),
 'operational_status':'HOLD','physical_qualified':False,
 'limitations':['Straight cylindrical reservations are specified assumptions, not a sourced real tool or open-jaw shape.',
 'Static source latch bounds do not identify actual gripping surfaces, travel or pivot envelope.',
 'Full200mm FPC placement and camera-end inserted/free-flex datum remain unresolved.',
 'Official CSI parts conflict with the inherited cooler proxy; actual cooler fan/perimeter geometry is unregistered.',
 'Other flexible harnesses are not included in this rigid STEP check; no combined-looms access pass.']}
write_text(D/'csi-source-tool-checks.json',json.dumps(report,indent=2));print(json.dumps(report),flush=True)
raise SystemExit(0 if report['declared_rigid_reservation_clear'] else 1)
