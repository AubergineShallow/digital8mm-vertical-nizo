"""Corrected CK1044Z80: separate fixed-switch shelf and panel-removal study.
Uses primary saved solids as obstacles; no mechanical source is changed.
"""
import json,math,hashlib,ast,itertools
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
from verify_fps_access import V,box,bb,overlaps,digest,bbox,tube
import routes as R
P=Path(__file__).parent;mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(mp.read_text());mh=digest(mp)
def cy(r,y0,y1,x=-111,z=80):return cq.Solid.makeCylinder(r,y1-y0,V(x,y0,z),V(0,1,0))
sh={n['id']:cq.importers.importStep(str(mp.parent/'step'/f"{n['id']}.step")).val() for n in m['rows']}
# Source-supported body/bushing, provisional pin-hole-envelope cylinders; no old nut/bore assumptions silently retained.
body=cy(13.75,11.1,25.2);bush=cy(4.76,25.2,33.2);shaft=cy(3.175,33.2,37.0)
# ShaftD-flat and nut metrology are separate gates; full cylinder is conservative for shaft/hole removal.
pins=[];pinspec=[]
for k in range(1,13):
 th=math.radians(255-30*(k-1));x=-111+11.1*math.cos(th);z=80+11.1*math.sin(th);pins.append(cy(.85,7.1,11.1,x,z));pinspec.append(dict(pin=k,center_xz=[x,z],radius_reserve_mm=.85))
th=math.radians(225);x=-111+3.85*math.cos(th);z=80+3.85*math.sin(th);pins.append(cy(.85,7.1,11.1,x,z));pinspec.append(dict(pin='A',center_xz=[x,z],radius_reserve_mm=.85))
anti=cy(1.525,25.2,26.7,-111,89.5);switch=body.fuse(bush,shaft,anti,*pins)
# A front-rooted beam avoids the current full FPC reservation and rear carrier diagonal.
shelf_block=box([-112,-98.5,21,24.5,64,74]).cut(cy(14.0,20.9,24.6))
beam=box([-101.5,-98.5,-27,24.5,64,66]);shelf=shelf_block.fuse(beam)
root_common=sh['tub'].intersect(shelf);union=sh['tub'].fuse(shelf);shelf_hits=[]
for n,f in sh.items():
 if n in ('tub','switch_1824','knob_fps') or not overlaps(bb(shelf),bb(f)):continue
 common=shelf.intersect(f);v=common.Volume()
 if v>1e-6:shelf_hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(common)))
sw=shelf.intersect(switch).Volume();r=R.build();wire_hits=[]
source_wires=[q for q in r['routes'] if q['id'] in ('usb_5v','fan','power_button')]+[dict(id='qt',curve=r['signal_geometry']['qt']['curve'],od_mm=3.2)]+r['signal_geometry']['run_cores']
for w in source_wires:
 s=tube(w['curve'],w['od_mm'])[0]
 if not overlaps(bb(s),bb(shelf)):continue
 common=s.intersect(shelf);v=common.Volume()
 if v>1e-6:wire_hits.append(dict(wire=w['id'],overlap_mm3=v,bbox_mm=bb(common)))
# Provisional correctedpanel: remove old hole locally, make revised new round hole and antirotation hole.
# Source panel is not mutated; the old engraving/recess stays untouched for this mechanical trial.
panel=sh['panel'].fuse(box([-116.2,-105.8,25.2,28,72.8,83.2])).cut(cy(5,25.1,28.1),cy(1.7,25.1,28.1,-111,89.5))
panel_hits=[]
for i in range(121):
 dy=i*.5;moving=panel.translate(V(0,dy,0))
 if not overlaps(bb(moving),bb(switch)):continue
 common=moving.intersect(switch);v=common.Volume()
 if v>1e-6:panel_hits.append(dict(shift_y_mm=dy,overlap_mm3=v,bbox_mm=bb(common)))
# Exact full-material HDMI cells. The switch is removed before ordinary carrier/HDMI translation.
tree=ast.parse((P/'verify_hdmi.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cell');exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'verify_hdmi.py'),'exec'))
hds=[]
for name,key in [('installed','hdmi_ribbon'),('premate','hdmi_ribbon_premate'),('both_unplugged','hdmi_ribbon_unplugged')]:
 hd=r[key]
 for dy in ([0] if name=='installed' else range(0,61,2)):
  hits=[];fixed_hits=[]
  for i,seg in enumerate(hd['segments']):
   b=bbox(seg['box']);b[2]+=dy;b[3]+=dy
   candidates=[(n,s) for n,s in [('shelf',shelf),('fixed_switch',switch)] if overlaps(b,bb(s))]
   if not candidates:continue
   c=cell(seg['vertices'])
   if c is None:continue
   c=c.translate(V(0,dy,0))
   for n,s in candidates:
    common=c.intersect(s);v=common.Volume()
    if v>1e-7:(hits if n=='shelf' else fixed_hits).append(dict(cell=i,overlap_mm3=v))
  if hits or fixed_hits or dy==0:hds.append(dict(state=name,shift_y_mm=dy,shelf_hits=hits,switch_left_fixed_hits=fixed_hits))
  if dy%10==0:print('Fixed FPS HDMI',name,dy,len(hits),len(fixed_hits),flush=True)
# Carried rigidstack must clearthe shelf after the switch has been lifted/removed.
carried=['pi5','cooler','x1203','x1203_kit','carrier','microsd'];stack_hits=[]
for dy in range(0,71,2):
 for n in carried:
  s=sh[n].translate(V(0,dy,0))
  if not overlaps(bb(s),bb(shelf)):continue
  common=s.intersect(shelf);v=common.Volume()
  if v>1e-6:stack_hits.append(dict(part=n,shift_y_mm=dy,overlap_mm3=v,bbox_mm=bb(common)))
result=dict(status='HYPOTHESIS; not adopted',mechanical_manifest_sha256=mh,source_sha256=digest(Path(__file__)),switch_source='https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf',switch=dict(center=[-111,80],body_radius=13.75,body_y=[11.1,25.2],bushing_radius=4.76,bushing_y=[25.2,33.2],conservative_shaft_radius=3.175,trim_end_y=37,anti_rotation_center=[-111,89.5],anti_pin_radius=1.525,pins=pinspec,unqualified=['terminal section inferred only from1.5mm PCBholes,0.85mm envelope used','actual pin clocking/mirror and electrical selected throw','anti-pin axial projection1.5mm remains legacy estimate','nut and washer dimensions are not published','received shafttrim,knobborefit and30deg endpoints']),shelf=dict(valid=shelf.isValid(),solids=len(shelf.Solids()),tub_contact_mm3=root_common.Volume(),tub_union_valid=union.isValid(),tub_union_solids=len(union.Solids()),block=[-112,-98.5,21,24.5,64,74],cradle_inner_radius_mm=14.0,beam=[-101.5,-98.5,-27,24.5,64,66],shelf_switch_overlap_mm3=sw,rigid_hits=shelf_hits,source_wire_hits=wire_hits,full_width_fpc_reservation=R.B(-116.8,-102.1,-21.6,-4.5,64.7,75),full_width_fpc_reservation_overlap=R.overlap(R.B(-101.5,-98.5,-27,24.5,64,66),R.B(-116.8,-102.1,-21.6,-4.5,64.7,75))),panel_slide=dict(poses=121,step_mm=.5,end_mm=60,hits=panel_hits),hdmi_checks=hds,carrier_translation_hits=stack_hits,remaining=['axial body restraint while nut is off and before hand support','actual printed flex/strength and contact surfacefit','nuttool,knobpull and electricalrootmetrology','PicoBlade pair/support/unplug and splices','otherpanelwirestagings remain independently gated'])
out=P/'out/fps-service-study';out.mkdir(exist_ok=True);(out/'fixed-switch-proposal-checks.json').write_text(json.dumps(result,indent=2));cq.exporters.export(shelf,str(out/'fixed-switch-shelf.step'));cq.exporters.export(switch,str(out/'ck1044-corrected-proxy.step'));print(json.dumps({k:v for k,v in result.items() if k not in ('switch','hdmi_checks')}),flush=True)
