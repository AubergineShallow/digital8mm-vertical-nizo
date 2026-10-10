"""Bound static corrected FPS wires, rest and staged panel/shaft service to exact STEP."""
from cv_io import read_text, write_text
from pathlib import Path
import sys,json,math,time
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import routes as R, fps_geometry as FG, fps_ck1044_static as F, fps_fixed_support as FS
from verify_fps_access import V,box,bb,overlaps,digest,tube,bbox
mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(read_text(mp));mh=digest(mp)
sh={row['id']:cq.importers.importStep(str(mp.parent/'step'/f"{row['id']}.step")).val() for row in m['rows']}
sourcehash={q:digest(P/q) for q in ['verify_fps_fixed_service.py','fps_geometry.py','fps_ck1044_static.py','fps_fixed_support.py','routes.py']}
sh.update(FG.switch_parts());sh['knob_fps']=FG.knob();support=FS.shelf()
# Diagnostic panel counterpart: fill both legacy holes, subtract source corrected holes.
cy=FG.cy
sh['panel']=sh['panel'].fuse(box([-116.3,-105.7,25.2,28,72.7,83.3]),box([-113,-109,25.2,28,84.3,87.6])).cut(cy(5,25.1,28.1),cy(1.7,25.1,28.1,-111,70.5))
allchecks=[]
def check(name,s,obstacles,reportclear=False):
 hits=[];near=[]
 for n,f in obstacles.items():
  if not overlaps(bb(s),bb(f)):continue
  d=s.distance(f);v=0
  if d<1e-7:
   c=s.intersect(f);v=c.Volume()
   if v>1e-6:hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(c)))
  if reportclear:near.append(dict(part=n,gap_mm=d,overlap_mm3=v))
 row=dict(item=name,hits=hits,near=near);allchecks.append(row)
 print(json.dumps(row),flush=True);return row
skip={'switch_1824','knob_fps','fps_nut','fps_mounting_washer'}
check('rest/static',support,{n:s for n,s in sh.items() if n!='tub'},True)
rest_union=sh['tub'].fuse(support)
rr=dict(valid=support.isValid(),solids=len(support.Solids()),tub_common_mm3=sh['tub'].intersect(support).Volume(),tub_union_valid=rest_union.isValid(),tub_union_solids=len(rest_union.Solids()))
f=F.build(R);wires={w['id']:tube(w['curve'],w['od_mm'])[0] for w in f['wire_parts']};wires['picoblade_body']=box(bbox(f['junction']['box']))
# Staggered full sleeve reservations on existing long vertical wire segment. These are maximum accepted finished envelopes.
for z in (41,55):wires['header_splice_reserve_'+str(z)]=cq.Solid.makeCylinder(1.5,10,V(-103.5,-23.4,z),V(0,0,1))
for n,s in wires.items():check(n,s,{**sh,'fps_rest':support},True)
# No panel wire travels with FPS in this sequence; all other panel looms retain independent gates.
panelgroup={'panel','encoder','knob_exp','power_button','power_nut_reserve','foam_pad'}
fixed={n:s for n,s in sh.items() if n not in panelgroup|{'knob_fps','fps_nut','fps_mounting_washer'} and not n.startswith('p_panel')}
for dy in [0,.5,1,1.5,2,3,4,5,6,7,8,8.5,9,10,11,12,15,20,30,45,60]:
 moving={n:sh[n].translate(V(0,dy,0)) for n in panelgroup}
 check('panel/switch/'+str(dy),moving['panel'],{'switch_1824':sh['switch_1824']})
 # Fingertip pad occupies only outside shaft-tip plane; physical softness/grip gate retained.
 if dy<=8.5:
  finger=cy(5,37,49)
  check('shaft_finger/'+str(dy),finger,{**moving,**{n:s for n,s in fixed.items() if n!='switch_1824'}})
# Switch alone withdraws after PicoBlade is separated. Unmodeled live wire deformation is explicitly not accepted here.
for dy in range(0,61,2):
 moving=sh['switch_1824'].translate(V(0,dy,0))
 check('switch_rigid_remove/'+str(dy),moving,{**{n:s for n,s in fixed.items() if n!='switch_1824'},'fps_rest':support})
for dy in range(0,71,2):
 for n in ['pi5','cooler','x1203','x1203_kit','carrier','microsd']:
  check('carried/'+n+'/'+str(dy),sh[n].translate(V(0,dy,0)),{'fps_rest':support})
# Direct approaches to the mated PicoBlade after complete panel removal; tool strokes must also clear.
b=bbox(f['junction']['box']);cx=-133.5;cz=79.7
# Two separate 1.5mm thick tip sets with4mm maximum footprint alongY; geometric bounded envelopes only.
tools={
 'near_x_jaws':cq.Compound.makeCompound([box([b[0]-1.5,b[0],11.1,65,cz-1.5,cz+1.5]),box([b[1],b[1]+1.5,11.1,65,cz-1.5,cz+1.5])]),
 'far_z_jaws':cq.Compound.makeCompound([box([cx-1.5,cx+1.5,6.1,65,b[4]-1.5,b[4]]),box([cx-1.5,cx+1.5,6.1,65,b[5],b[5]+1.5])])}
for n,s in tools.items():check(n,s,{**fixed,'fps_rest':support},True)
result=dict(status='diagnostic proposal only',mechanical_manifest_sha256=mh,source_sha256=sourcehash,rest=rr,wire_lengths=f['switch_branch_lengths_mm'],checks=allchecks,limitations=['Mechanical manifest is old export15; corrected switch and local panel modification are separately source-bound proposal','Real nut/washer dimensions and actual fingertip envelope/friction require physical verification','Two forceps are bounding geometric hypotheses, not sourced qualified tools','Connector support and wire deformation during unplug/removal remain unresolved','Other panel wires are not proved by stationary FPS body removal','True two-core fanout, solderlap, receivedterminal numbering/mirror and splice dimensions remain gates'])
out=P/'out/fps-service-study';write_text(out/'fixed-fps-service-checks.json',json.dumps(result,indent=2));cq.exporters.export(support,str(out/'fixed-fps-reinforced-rest.step'));cq.exporters.export(cq.Compound.makeCompound(list(wires.values())),str(out/'fixed-fps-wires.step'))
assert digest(mp)==mh
print('DONE',sum(bool(q['hits']) for q in allchecks),'failingchecks',flush=True)
