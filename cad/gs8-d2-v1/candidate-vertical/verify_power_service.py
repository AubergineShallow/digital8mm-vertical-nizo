"""Saved-STEP check of closed-body, cap-off rigid battery-junction withdrawal.
Full flexible harness deformation, finger force, electrical isolation and hot-load gates stay open.
"""
from cv_io import read_text, write_text
import json,math,hashlib,argparse
from pathlib import Path
import cadquery as cq
P=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--variant',default='compact-kowa_lm6hc');a=ap.parse_args();out=P/'out'/a.variant
src=P/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json';snap=json.loads(read_text(src));mf=out/'manifest.json';manifest_hash=hashlib.sha256(mf.read_bytes()).hexdigest();m=json.loads(read_text(mf))
r={x['id']:x for x in m['rows']};sh={}
for n in r:
 f=out/'step'/f'{n}.step';actual=hashlib.sha256(f.read_bytes()).hexdigest()
 if actual!=m['files'][f'step/{n}.step']:raise ValueError('STEP does not match manifest:'+n)
 sh[n]=cq.importers.importStep(str(f)).val()
for rel,h in m['sources'].items():
 if hashlib.sha256((P.parent/rel).read_bytes()).hexdigest()!=h:raise ValueError('Stale source:'+rel)
V=cq.Vector
c0=snap['junction_center'];yaw0=snap['junction_yaw_deg'];pitch0=snap['junction_pitch_deg']
local=sh['xt30_pair'].translate(V(*[-x for x in c0])).rotate((0,0,0),(0,0,1),-yaw0).rotate((0,0,0),(0,1,0),-pitch0)
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-7 for i in (0,2,4))
fixed={n:s for n,s in sh.items() if n not in ('pack','xt30_pair','cap') and r[n]['kind']!='keepout'}
fb={n:bb(s) for n,s in fixed.items()};hits=[];count=0
for i,p in enumerate(snap['rigid_service_poses']):
 if i%25==0:print('Pose',i,flush=True)
 mat=p['matrix'];pitch=math.degrees(math.atan2(-mat[2][0],mat[2][2]));yaw=math.degrees(math.atan2(mat[1][0],mat[0][0]))
 junction=local.rotate((0,0,0),(0,1,0),pitch).rotate((0,0,0),(0,0,1),yaw).translate(V(*p['center']))
 pack=sh['pack'].translate(V(*p['pack_translation']))
 for name,mover in [('junction_and_fuse',junction),('pack',pack)]:
  mb=bb(mover)
  for n,f in fixed.items():
   if not overlaps(mb,fb[n]):continue
   v=mover.intersect(f).Volume();count+=1
   if v>.02:hits.append(dict(pose=i,mover=name,fixed=n,overlap_mm3=v))
 if overlaps(bb(junction),bb(pack)):
  v=junction.intersect(pack).Volume();count+=1
  if v>.02:hits.append(dict(pose=i,mover='junction',fixed='moving_pack',overlap_mm3=v))
if hashlib.sha256(mf.read_bytes()).hexdigest()!=manifest_hash:raise ValueError('Manifest changed during verification')
result=dict(status='pass' if not hits else 'fail',poses=len(snap['rigid_service_poses']),exact_intersections=count,hits=hits,body='closed; cap removed before withdrawal',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),snapshot_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),manifest_sha256=manifest_hash,physical_qualified=False,remaining_stop=['Full270mm flexible-core deployment and retention','Unmeasured pad and pin exits','Finger grip and unplug force','Hot voltage drop and fuse/contact heating','Printed attachment strength and wear'])
write_text(out/'power-service-checks.json',json.dumps(result,indent=2));print(json.dumps(result),flush=True);raise SystemExit(bool(hits))
