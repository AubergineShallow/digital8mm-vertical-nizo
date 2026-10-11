"""Final FPS static and36-pose carried checks bound to the accepted integrated STEP.
Uses the frozen sampled/analytic input; never invents a replacement USB/FPC wire.
"""
from cv_io import read_text, write_text
from pathlib import Path
import json,time,argparse
import cadquery as cq
from verify_fps_access import V,box,bb,overlaps,bbox,digest,tube
P=Path(__file__).parent
audit_source_sha256=digest(Path(__file__))
verification_dependencies={"verify_fps_access.py":digest(P/"verify_fps_access.py")}
ap=argparse.ArgumentParser();ap.add_argument('--variant',default='compact-kowa_lm6hc');ap.add_argument('--pair-part-id',default=None);args=ap.parse_args()
mp=P/'out'/args.variant/'manifest.json';m=json.loads(read_text(mp));mh=digest(mp);inputp=P/'out/fps-service-study/mated-carry-input.json';f=json.loads(read_text(inputp));receipt=json.loads(read_text(P/'out/fps-service-study/fps-final-source-receipt.json'))
input_sha256=digest(inputp)
assert input_sha256==receipt['frozen_input']['sha256']
for n in ['fps_fixed_support.py','fps_pair_guide.py','fps_ck1044_mated_carry.py']:
 assert digest(P/n)==receipt['canonical_sources'][n],('Frozen source changed',n)
stale=[n for n,h in m['sources'].items() if digest(P.parent/n)!=h]
invalid=[q['id'] for q in m['rows'] if q['kind']=='printed' and (not q['valid'] or q['solid_count']!=1)]
assert not stale,stale;assert not invalid,invalid
# An old manifest lacking the selected integrated helpers cannot be relabelled as final.
for n in ['fps_fixed_support.py','fps_pair_guide.py']:
 assert any(k.endswith(n) and h==digest(P/n) for k,h in m['sources'].items()),('Helper absent from integrated manifest',n)
sh={};step_hashes={}
for row in m['rows']:
 n=row['id'];p=mp.parent/'step'/f'{n}.step';h=digest(p);assert h==m['files'][f'step/{n}.step'];step_hashes[n]=h;sh[n]=cq.importers.importStep(str(p)).val()
# This row is a non-material storage-plug reservation, retained as a diagnostic.
# Its actual purchased head profile remains a separate receipt/fit gate.
reservation_ids={'usb_storage_plug_reserve'}
reservation_rows={q['id']:q for q in m['rows'] if q['id'] in reservation_ids}
for q in reservation_rows.values():
 assert q['kind']=='keepout' and q.get('geometry_role')=='non-material keepout' and q.get('occupied_material_volume_mm3')==0,('Unqualified material exclusion',q['id'])
reservations={n:sh.pop(n) for n in list(sh) if n in reservation_ids}
parts={q['id']:tube(q['curve'],q['od_mm'])[0] for q in f['wire_parts']};parts['mated_fps_pair']=box(bbox(f['junction']['box']));checks=[];crop_receipts=[];reservation_diagnostics=[]
def check(label,s,obs,target=checks):
 hits=[]
 for n,t in obs.items():
  if not overlaps(bb(s),bb(t)):continue
  common=s.intersect(t);vol=common.Volume()
  if vol>1e-6:hits.append(dict(part=n,overlap_mm3=vol,bbox_mm=bb(common)))
 q=dict(item=label,hits=hits);target.append(q);print(json.dumps(q),flush=True)
def crops_for(name,s,obs,shift):
 b=bb(s);b[3]+=shift;region=box([b[0]-.001,b[1]+.001,b[2]-.001,b[3]+.001,b[4]-.001,b[5]+.001]);out={}
 for n,o in obs.items():
  if not overlaps(b,bb(o)):continue
  c=o.intersect(region);vol=c.Volume();crop_receipts.append(dict(item=name,obstacle=n,shift_y_mm=shift,crop_volume_mm3=vol))
  if vol>1e-9:out[n]=c
 return out
for n,s in parts.items():
 obs={k:v for k,v in sh.items() if not(n=='mated_fps_pair' and k==args.pair_part_id)}
 check('static/'+n,s,crops_for('static/'+n,s,obs,0))
# Full finished-splice reservations; selected donor/stock cut lengths are still receipt-based.
for z in [41,55]:
 s=cq.Solid.makeCylinder(1.5,10,V(-103.5,-23.4,z),V(0,0,1));parts['splice_'+str(z)]=s;check('static/splice_'+str(z),s,crops_for('static/splice_'+str(z),s,sh,0))
parts['switch_1824']=sh['switch_1824']
for n,s in parts.items():check('non_material_reservation/'+n,s,reservations,target=reservation_diagnostics)
carried={'pi5','cooler','x1203','x1203_kit','carrier','microsd','switch_1824'}
off={'panel','encoder','knob_exp','knob_fps','fps_nut','fps_mounting_washer','power_button','power_nut_reserve','foam_pad'}
if args.pair_part_id:carried.add(args.pair_part_id)
fixed={n:s for n,s in sh.items() if n not in carried|off and not n.startswith(('p_panel','p_carrier','kit_'))}
crops={n:crops_for('carry/'+n,s,fixed,70) for n,s in parts.items()}
for dy in range(0,71,2):
 for n,s in parts.items():check('carry/'+n+'/'+str(dy),s.translate(V(0,dy,0)),crops[n])
assert digest(mp)==mh
assert digest(Path(__file__))==audit_source_sha256
assert digest(inputp)==input_sha256
for n,h in verification_dependencies.items():assert digest(P/n)==h
for n,h in m['sources'].items():assert digest(P.parent/n)==h
for n,h in step_hashes.items():assert digest(mp.parent/'step'/f'{n}.step')==h
result=dict(status='geometric_pass_only' if not any(q['hits'] for q in checks) else 'fail',physical_qualified=False,mechanical_manifest_sha256=mh,mechanical_sources=m['sources'],input_sha256=input_sha256,source_sha256=audit_source_sha256,verification_dependency_sha256=verification_dependencies,frozen_helper_sha256={n:digest(P/n) for n in ['fps_fixed_support.py','fps_pair_guide.py','fps_ck1044_mated_carry.py']},step_sha256=step_hashes,printed_parts_valid=True,material_inventory=sorted(sh),non_material_reservation_inventory=sorted(reservations),non_material_reservation_rows=reservation_rows,non_material_reservation_diagnostics=reservation_diagnostics,reservation_note="The explicit usb_storage_plug_reserve row is a non-material fit reservation. Its static relation to co-carried FPS pieces is invariant during the selected translation; diagnostics do not certify a purchased storage head.",static_and_carried_checks=checks,exact_crop_receipts=crop_receipts,closed_pose=True,carried_pose_count=36,carried_step_mm=2,carried_end_y_mm=70,sequence='Panel removed; FPS remains mated; Pi HDMI remains mated; EVF HDMI disconnected; switch and completeFPSwires co-carried withPi/carrier.',remaining=['New USB2 head has no measured wire exit or accepted full5V soft route; no full-loom pass follows from this test','Corrected CSI/FPC and other panel wires remain independently gated','Actual two-core GPIO fanout, solder/heatshrink roots, receivedMolex dimensions and wire bending remain unqualified','Rest/guide print strength, fit, creep, bushing grip and coordinated hand support require physical trial','Bench-only PicoBlade separation, continuity and30-cycle tin-contact durability remain gates'],completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
out=P/'out/fps-service-study/integrated-fps-checks.json';write_text(out,json.dumps(result,indent=2));print(json.dumps(dict(status=result['status'],failures=sum(bool(q['hits']) for q in checks),report=str(out))),flush=True)
# FX (verifier T2 major): a failing report exits non-zero (it always exited 0, so the batch run record showed exit 0 for
# a failing FPS report); the report itself is unchanged.
raise SystemExit(0 if result['status']=='geometric_pass_only' else 1)
