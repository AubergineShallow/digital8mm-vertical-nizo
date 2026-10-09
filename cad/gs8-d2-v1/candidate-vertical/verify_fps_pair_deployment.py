"""Stationary switch, mated-pair deployment and straight separation: diagnostic exact study."""
from pathlib import Path
import sys,json,math,time
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import routes as R, fps_geometry as FG, fps_ck1044_service as F, fps_fixed_support as FS
from verify_fps_access import V,box,bb,overlaps,digest,tube,bbox
sourcehash={q:digest(P/q) for q in ['verify_fps_pair_deployment.py','fps_ck1044_service.py','fps_fixed_support.py','fps_geometry.py']}
mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(mp.read_text());mh=digest(mp)
sh={row['id']:cq.importers.importStep(str(mp.parent/'step'/f"{row['id']}.step")).val() for row in m['rows']};sh.update(FG.switch_parts())
fixed={n:s for n,s in sh.items() if n not in {'panel','encoder','knob_exp','knob_fps','power_button','power_nut_reserve','foam_pad','fps_nut','fps_mounting_washer'} and not n.startswith('p_panel')}
support=FS.shelf();rest=FS.connector_rest();fixed.update(fps_rest=support,connector_rest=rest)
checks=[]
def check(label,s,obs):
 hits=[];near=[]
 for n,f in obs.items():
  if not overlaps(bb(s),bb(f)):continue
  d=s.distance(f)
  if d<1e-7:
   c=s.intersect(f);v=c.Volume()
   if v>1e-6:hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(c)))
  near.append(dict(part=n,gap_mm=d))
 q=dict(item=label,hits=hits,near=near);checks.append(q);print(json.dumps(q),flush=True)
check('connector_rest_static',rest,{n:s for n,s in fixed.items() if n not in ['tub','connector_rest']})
ru=sh['tub'].fuse(rest,support);root=sh['tub'].intersect(rest).Volume()
# No moving panel in these poses; panel removal is separately verified.
poses=[]
for j,u in ([(0,0),(23,0),(23,10)] if '--quick' in sys.argv else [(v,0) for v in [0,2,4,6,8,10,12,14,16,18,20,22,23]]+[(23,v) for v in range(1,11)]):
 f=F.build(R,j,u);pose=dict(junction_shift_y_mm=j,unplug_shift_mm=u,wire_parts=f['wire_parts'],junction=f['junction'],switch_branch_lengths_mm=f['switch_branch_lengths_mm']);poses.append(pose)
 for w in f['wire_parts']:
  if w['id']=='fps_header_branch' and j+u>0:continue
  check('wire/'+w['id']+'/'+str(j)+'/'+str(u),tube(w['curve'],w['od_mm'])[0],fixed)
 # Both housing reserves each cover the whole9mm pair axial envelope: conservative whole-body separation study.
 for n,b in [('female',[-135.625,-131.375,6.1+j,15.1+j,78.05,81.35]),('male',[-135.625,-131.375,6.1+j+u,15.1+j+u,78.05,81.35])]:check(n+'/'+str(j)+'/'+str(u),box(b),fixed)
# Source-size bounded fingertip pads at true rear male3mm grip and female front grip after staging.
# Local spheres certify only the pad region; fingers/hand articulation and received housing grip remain physical gates.
for u in range(11):
 pads={};cx=-133.5;cz=79.7
 for side in [-1,1]:
  pads['male'+str(side)]=cq.Solid.makeSphere(4.5,V(cx+side*(1.475+4.5),36.6+u,cz),angleDegrees1=-90)
  pads['female'+str(side)]=cq.Solid.makeSphere(4.5,V(cx,31.8,cz+side*(1.65+4.5)),angleDegrees1=-90)
 for n,s in pads.items():check('finger/'+n+'/'+str(u),s,fixed)
 for n,s in pads.items():
  for k,t in pads.items():
   if k>n:check('finger_mutual/'+n+'/'+k+'/'+str(u),s,{k:t})
result=dict(status='diagnostic only; not adopted',mechanical_manifest_sha256=mh,source_sha256=sourcehash,support=dict(connector_rest_valid=rest.isValid(),connector_rest_solids=len(rest.Solids()),tub_contact_mm3=root,tub_union_valid=ru.isValid(),tub_union_solids=len(ru.Solids())),poses=poses,checks=checks,remaining=['Actual pair dimensions/tolerances, housing profile and gripping force;9mm mating dimension isreference','Thin-jaw acquisition and whole hand articulation not qualified by fingertip spheres','Complete corrected HDMI and neighboring-wire dynamic checks separate','Actual label removal, wire retention, bend fatigue and fanoutjoint dimensions','No wire deformation proof for switch removal after connector separation yet'])
out=P/'out/fps-service-study';(out/('pair-deployment-xy-quick-checks.json' if '--quick' in sys.argv else 'pair-deployment-xy-checks.json')).write_text(json.dumps(result,indent=2));cq.exporters.export(rest,str(out/'picoblade-rear-rest.step'));print('DONE',sum(bool(q['hits']) for q in checks),'failingchecks',flush=True)
