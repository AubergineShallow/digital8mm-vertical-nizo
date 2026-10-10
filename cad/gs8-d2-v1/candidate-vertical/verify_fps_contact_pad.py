"""Exact central-rest candidate: rigid, wire, complete carried sweep."""
from cv_io import read_text, write_text
import export_cache as EC  # fixup-1 (VN-17): the bound STEP gets a fixed header time
from pathlib import Path
import sys,json
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import routes as R,fps_geometry as FG,fps_fixed_support_pad_proposal as F,fps_ck1044_mated_carry as W
from verify_fps_access import V,box,bb,overlaps,digest,tube
mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(read_text(mp));sh={r['id']:cq.importers.importStep(str(mp.parent/'step'/f"{r['id']}.step")).val() for r in m['rows']};sh.update(FG.switch_parts());cp=P/'out/structural-proposals/reinforced-carrier.step';sh['carrier']=cq.importers.importStep(str(cp)).val();full_rest=F.shelf();import fps_fixed_support_central_wide as Previous
rest=full_rest.cut(Previous.shelf());checks=[]
def check(label,s):
 if not overlaps(bb(rest),bb(s)):return
 c=rest.intersect(s);v=c.Volume();q=dict(item=label,overlap_mm3=v)
 if v>1e-6:q['bbox_mm']=bb(c);print(json.dumps(q),flush=True)
 checks.append(q)
for n,s in sh.items():
 if n!='tub':check('static/'+n,s)
r=R.build();f=W.build(R,0,0)
for w in [q for q in r['routes'] if q['id'] in ['usb_5v','fan','power_button']]+[dict(id='qt',curve=r['signal_geometry']['qt']['curve'],od_mm=3.2)]+r['signal_geometry']['run_cores']:check('wire/'+w['id'],tube(w['curve'],w['od_mm'])[0])
parts={w['id']:tube(w['curve'],w['od_mm'])[0] for w in f['wire_parts']};parts.update({n:sh[n] for n in ['pi5','cooler','x1203','x1203_kit','carrier','microsd','switch_1824']})
for dy in range(0,71):
 for n,s in parts.items():check('carry/'+n+'/'+str(dy),s.translate(V(0,dy,0)))
import fps_pair_guide as G
guide=G.build();u=sh['tub'].fuse(full_rest,guide);
# Bounded fingertip pads touch the exposed bushing; they do not stand in for an entire hand.
for sign in [-1,1]:
 finger=cq.Solid.makeSphere(4.5,V(-111+sign*9.26,29.9,80),angleDegrees1=-90)
 for n,o in sh.items():
  if n in ['panel','knob_fps','fps_nut','fps_mounting_washer'] or n.startswith('p_panel'):continue
  if not overlaps(bb(finger),bb(o)):continue
  c=finger.intersect(o);vol=c.Volume();row=dict(item='bushing_finger/'+str(sign)+'/'+n,overlap_mm3=vol)
  if vol>1e-6:row['bbox_mm']=bb(c);print(json.dumps(row),flush=True)
  checks.append(row)
result=dict(status='interim proposal; corrected USB and CSI pending',mechanical_manifest_sha256=digest(mp),carrier_sha256=digest(cp),source_sha256={n:digest(P/n) for n in ['verify_fps_contact_pad.py','fps_fixed_support_pad_proposal.py','fps_ck1044_mated_carry.py','fps_geometry.py']},rest=dict(valid=full_rest.isValid(),solids=len(full_rest.Solids()),volume_mm3=full_rest.Volume(),added_contact_material_mm3=rest.Volume(),tub_contact_mm3=sh['tub'].intersect(rest).Volume(),tub_union_valid=u.isValid(),tub_union_solids=len(u.Solids())),checks=checks)
out=P/'out/fps-service-study';write_text(out/'central-rest-pad-checks.json',json.dumps(result,indent=2));EC.export_step(full_rest,out/'central-rest-pad.step');print(json.dumps(result['rest']),flush=True);print('DONE',sum(q['overlap_mm3']>1e-6 for q in checks),'hits',flush=True)
