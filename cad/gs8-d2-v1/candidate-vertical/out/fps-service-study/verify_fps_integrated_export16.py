"""Final FPS static and36-pose carried checks bound to the accepted integrated STEP.
Uses the frozen sampled/analytic input; never invents a replacement USB/FPC wire.
"""
from pathlib import Path
import json,time,argparse
import cadquery as cq
from verify_fps_access import V,box,bb,overlaps,bbox,digest,tube
P=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--variant',default='compact-kowa_lm6hc');ap.add_argument('--pair-part-id',default=None);args=ap.parse_args()
mp=P/'out'/args.variant/'manifest.json';m=json.loads(mp.read_text());mh=digest(mp);inputp=P/'out/fps-service-study/mated-carry-input.json';f=json.loads(inputp.read_text());receipt=json.loads((P/'out/fps-service-study/fps-final-source-receipt.json').read_text())
assert digest(inputp)==receipt['frozen_input']['sha256']
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
parts={q['id']:tube(q['curve'],q['od_mm'])[0] for q in f['wire_parts']};parts['mated_fps_pair']=box(bbox(f['junction']['box']));checks=[];crop_receipts=[]
def check(label,s,obs):
 hits=[]
 for n,t in obs.items():
  if not overlaps(bb(s),bb(t)):continue
  common=s.intersect(t);vol=common.Volume()
  if vol>1e-6:hits.append(dict(part=n,overlap_mm3=vol,bbox_mm=bb(common)))
 q=dict(item=label,hits=hits);checks.append(q);print(json.dumps(q),flush=True)
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
carried={'pi5','cooler','x1203','x1203_kit','carrier','microsd','switch_1824'}
off={'panel','encoder','knob_exp','knob_fps','fps_nut','fps_mounting_washer','power_button','power_nut_reserve','foam_pad'}
if args.pair_part_id:carried.add(args.pair_part_id)
fixed={n:s for n,s in sh.items() if n not in carried|off and not n.startswith(('p_panel','p_carrier','kit_'))}
crops={n:crops_for('carry/'+n,s,fixed,70) for n,s in parts.items()}
for dy in range(0,71,2):
 for n,s in parts.items():check('carry/'+n+'/'+str(dy),s.translate(V(0,dy,0)),crops[n])
assert digest(mp)==mh
for n,h in step_hashes.items():assert digest(mp.parent/'step'/f'{n}.step')==h
result=dict(status='geometric_pass_only' if not any(q['hits'] for q in checks) else 'fail',physical_qualified=False,mechanical_manifest_sha256=mh,mechanical_sources=m['sources'],input_sha256=digest(inputp),source_sha256=digest(Path(__file__)),frozen_helper_sha256={n:digest(P/n) for n in ['fps_fixed_support.py','fps_pair_guide.py','fps_ck1044_mated_carry.py']},step_sha256=step_hashes,printed_parts_valid=True,static_and_carried_checks=checks,exact_crop_receipts=crop_receipts,closed_pose=True,carried_pose_count=36,carried_step_mm=2,carried_end_y_mm=70,sequence='Panel removed; FPS remains mated; Pi HDMI remains mated; EVF HDMI disconnected; switch and completeFPSwires co-carried withPi/carrier.',remaining=['New USB2 head has no measured wire exit or accepted full5V soft route; no full-loom pass follows from this test','Corrected CSI/FPC and other panel wires remain independently gated','Actual two-core GPIO fanout, solder/heatshrink roots, receivedMolex dimensions and wire bending remain unqualified','Rest/guide print strength, fit, creep, bushing grip and coordinated hand support require physical trial','Bench-only PicoBlade separation, continuity and30-cycle tin-contact durability remain gates'],completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
out=P/'out/fps-service-study/integrated-fps-checks.json';out.write_text(json.dumps(result,indent=2));print(json.dumps(dict(status=result['status'],failures=sum(bool(q['hits']) for q in checks),report=str(out))),flush=True)
