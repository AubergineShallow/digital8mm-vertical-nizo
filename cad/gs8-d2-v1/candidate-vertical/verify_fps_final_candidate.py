"""Exact FPS proposal screen against reinforced carrier and carried-group obstacles."""
from cv_io import read_text, write_text
from pathlib import Path
import sys,json,time
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import routes as R,fps_geometry as FG,fps_fixed_support as FS,fps_ck1044_service as F
from verify_fps_access import V,box,bb,overlaps,digest,tube,bbox
mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(read_text(mp));mh=digest(mp)
carrier=P/'out/structural-proposals/reinforced-carrier.step';ch=digest(carrier)
source={n:digest(P/n) for n in ['verify_fps_final_candidate.py','fps_ck1044_service.py','fps_fixed_support.py','fps_geometry.py']}
sh={row['id']:cq.importers.importStep(str(mp.parent/'step'/f"{row['id']}.step")).val() for row in m['rows']};sh.update(FG.switch_parts());sh['carrier']=cq.importers.importStep(str(carrier)).val();rest=FS.shelf();cr=FS.connector_rest()
checks=[]
def check(name,s,obs):
 hits=[];gaps=[]
 for n,f in obs.items():
  if not overlaps(bb(s),bb(f)):continue
  d=s.distance(f)
  if d<1e-7:
   c=s.intersect(f);v=c.Volume()
   if v>1e-6:hits.append(dict(part=n,volume_mm3=v,bbox_mm=bb(c)))
  gaps.append(dict(part=n,gap_mm=d))
 q=dict(item=name,hits=hits,gaps=gaps);checks.append(q);print(json.dumps(q),flush=True)
for j,u in [(0,0),(23,0),(23,10)]:
 f=F.build(R,j,u)
 for w in f['wire_parts']:
  check('reinforced_carrier/'+w['id']+'/'+str(j)+'/'+str(u),tube(w['curve'],w['od_mm'])[0],{'carrier':sh['carrier']})
check('rest/carrier',rest,{'carrier':sh['carrier']});check('connector_rest/carrier',cr,{'carrier':sh['carrier']})
# Coupled translation keeps source-clear relative position among switch, FPS wires and HDMI/carrier.
f=F.build(R,23,10);wires={w['id']:tube(w['curve'],w['od_mm'])[0] for w in f['wire_parts']};parts={**wires,'switch':sh['switch_1824'],'carrier':sh['carrier']}
# Panel and its controls are off. EVF remains fixed, including its disconnected board.
fixed={n:s for n,s in sh.items() if n not in ['panel','encoder','knob_exp','knob_fps','switch_1824','fps_nut','fps_mounting_washer','power_button','power_nut_reserve','foam_pad','pi5','cooler','x1203','x1203_kit','carrier','microsd'] and not n.startswith(('p_panel','p_carrier','kit_'))};fixed.update(fps_rest=rest,connector_rest=cr)
for dy in [0,2,4,6,8,10,12,16,20,25,30,40,50,60,70]:
 for n,s in parts.items():check('coupled/'+n+'/'+str(dy),s.translate(V(0,dy,0)),fixed)
result=dict(status='diagnostic candidate only',mechanical_manifest_sha256=mh,reinforced_carrier_sha256=ch,source_sha256=source,checks=checks,limitations=['Other carried wires and HDMI exact relative geometry require separate source-bound check','No coordinated-hand load or support qualification','Actual housing flange grip, received stack and termination dimensions remain open'])
write_text(P/'out/fps-service-study/final-candidate-checks.json',json.dumps(result,indent=2));print('DONE',sum(bool(q['hits']) for q in checks),'hits',flush=True)
