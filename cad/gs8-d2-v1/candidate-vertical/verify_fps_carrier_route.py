"""Corrected FPS main path and bounded retention/tool proposals; exact intersections."""
from cv_io import read_text, write_text
from pathlib import Path
import sys,json
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import routes as R,fps_geometry as FG,fps_fixed_support as FS,fps_ck1044_service_carrier as F
from verify_fps_access import V,box,bb,overlaps,digest,tube,bbox
mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(read_text(mp));mh=digest(mp)
cp=P/'out/structural-proposals/reinforced-carrier.step';sh={row['id']:cq.importers.importStep(str(mp.parent/'step'/f"{row['id']}.step")).val() for row in m['rows']};sh.update(FG.switch_parts());sh['carrier']=cq.importers.importStep(str(cp)).val();sh['fps_rest']=FS.shelf();sh['connector_rest']=FS.connector_rest()
source={n:digest(P/n) for n in ['verify_fps_carrier_route.py','fps_ck1044_service_carrier.py','fps_fixed_support.py','fps_geometry.py']};checks=[]
def check(label,s,obs):
 hits=[]
 for n,t in obs.items():
  if not overlaps(bb(s),bb(t)):continue
  c=s.intersect(t);v=c.Volume()
  if v>1e-6:hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(c)))
 q=dict(item=label,hits=hits);checks.append(q);print(json.dumps(q),flush=True)
off={'panel','encoder','knob_exp','knob_fps','fps_nut','fps_mounting_washer','power_button','power_nut_reserve','foam_pad'}
fixed={n:s for n,s in sh.items() if n not in off and not n.startswith('p_panel')}
poses=[]
for j,u in [(v,0) for v in [0,2,4,6,8,10,12,14,16,18,20,22,23]]+[(23,v) for v in range(1,11)]:
 f=F.build(R,j,u);poses.append(f);w=next(w for w in f['wire_parts'] if w['id']=='fps_225_main');s=tube(w['curve'],w['od_mm'])[0];check('main/'+str(j)+'/'+str(u),s,sh if j+u==0 else fixed)
# Carry wire with its GPIO/Pi and rest of the released assembly. Relative source clearance is checked separately.
f=F.build(R,23,10);w=next(w for w in f['wire_parts'] if w['id']=='fps_225_main');s=tube(w['curve'],w['od_mm'])[0]
carried={'pi5','cooler','x1203','x1203_kit','carrier','microsd','switch_1824'}
fixed_carry={n:s for n,s in fixed.items() if n not in carried and not n.startswith(('p_carrier','kit_'))}
for dy in range(0,71,2):check('main/carry/'+str(dy),s.translate(V(0,dy,0)),fixed_carry)
# Bounded two2mm jaws to take both mated housings together, shank begins in the open side.
jaw=cq.Compound.makeCompound([box([-137.625,-135.625,6.1,36,78.2,81.2]),box([-131.375,-129.375,6.1,36,78.2,81.2]),cq.Solid.makeCylinder(4,50,V(-133.5,36,79.7),V(0,1,0))])
for dy in [0,5,10,15,20,23]:check('draw_tool/'+str(dy),jaw.translate(V(0,dy,0)),fixed)
result=dict(status='geometric proposal only; physical gates open',mechanical_manifest_sha256=mh,reinforced_carrier_sha256=digest(cp),source_sha256=source,poses=poses,checks=checks,retention_status='No tie adopted; integral lip/clip and release remain open',remaining=['Tie clamp force, axial slip and cut-tool shape/safety are not physically qualified','Tiny female flange grip and actual stroke/tolerances remain STOP','No guarantee that approximate hand coordination preserves the modeled co-moving relation','Other panel leads and fullwidth CSI remain independent gates'])
out=P/'out/fps-service-study';write_text(out/'carrier-route-checks.json',json.dumps(result,indent=2));print('DONE',sum(bool(q['hits']) for q in checks),'failures',flush=True)
