"""Exact corrected USB head reservation checks, with optional final export binding.

The final installed cuttable lead, overmold/exit and rigid joints are unresolved.
This script therefore does not select or approve a USB service trajectory.
"""
import argparse,ast,hashlib,itertools,json,math,sys
from pathlib import Path
import cadquery as cq
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path[:0]=[str(P),str(ROOT.parent)]
VERIFICATION_SOURCE_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
V=cq.Vector
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def bounds(d):return [v for a in 'xyz' for v in d[a]]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,2,4))
def xz_overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,4))
def box(b):return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))
tree=ast.parse((P/'source-verify_fps_access.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'rounded_wire','tube'}]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/'source-verify_fps_access.py'),'exec'))
ap=argparse.ArgumentParser();ap.add_argument('--mechanical-manifest',type=Path);ap.add_argument('--expected-sha');ap.add_argument('--report-name',default='head-fps-support-checks.json');args=ap.parse_args()
report_path=P/args.report_name
if report_path.exists():raise ValueError('Do not overwrite a completed named report')
input_hash=digest(P/'input.json');assert input_hash=='cf6b20f21e342414dbf001fe9a4d84ad9634fa2b93e81118b112cac4eaec6f88'
receipt=json.loads((P/'context-input-receipt.json').read_text())
for name,h in receipt['files'].items():assert digest(P/name)==h,name
assert digest(P/'usb-donor-provenance.json')==receipt['donor_addendum_sha256']
d=json.loads((P/'input.json').read_text());f=json.loads((P/'mated-carry-input.json').read_text());head_row=next(x for x in d['connectors'] if x['id']=='p_usb_pi');head=box(bounds(head_row['box']));hb=bb(head)
objects={};groups={};sources={}
for w in f['wire_parts']:
 objects[w['id']]=tube(w['curve'],w['od_mm'])[0];groups[w['id']]='carried FPS complete analytic wire'
objects['fps_mated_pair']=box(bounds(f['junction']['box']));groups['fps_mated_pair']='carried FPS junction'
objects['fps_protective_reservation']=box(bounds(f['junction']['protective_reserve']));groups['fps_protective_reservation']='protective reservation'
import fps_geometry as FG
objects['corrected_fps_switch']=FG.switch_parts()['switch_1824'];groups['corrected_fps_switch']='carried corrected switch'
for name in ('central-rest-pad','picoblade-open-guide'):
 path=P/(name+'.step');objects[name]=cq.importers.importStep(str(path)).val();groups[name]='fixed selected FPS support';sources[name]=digest(path)
checks=[]
def check(name,s,kind):
 b=bb(s);hit=None;tests=0
 if overlaps(hb,b):
  witnesses=[]
  for part in s.Solids():
   if not overlaps(hb,bb(part)):continue
   common=head.intersect(part);tests+=1;v=common.Volume()
   if v>1e-7:witnesses.append(dict(overlap_mm3=v,bbox_mm=bb(common)))
  if witnesses:hit=dict(witnesses=witnesses,pairwise_overlap_sum_mm3=sum(w['overlap_mm3'] for w in witnesses))
 row=dict(object=name,kind=kind,status='fail' if hit else 'pass',object_bbox_mm=b,xz_disjoint=not xz_overlaps(hb,b),exact_intersections=tests,hit=hit)
 checks.append(row);print(json.dumps(dict(object=name,status=row['status'],xz_disjoint=row['xz_disjoint'],exact=tests)),flush=True)
for name,s in objects.items():check(name,s,groups[name])
hdmi=[]
for state in ('installed','premate','both_unplugged'):
 cells=[i for i,seg in enumerate(d['hdmi_'+state]['segments']) if overlaps(hb,bounds(seg['box']))]
 # A broad-phase hit must not be quietly accepted: request material exact test.
 hdmi.append(dict(state=state,full_length_mm=d['hdmi_'+state]['routed_length_mm'],candidate_cells=cells,status='pass_by_complete_material_bounds' if not cells else 'requires_exact_material_intersection'))
mechanical=None
if args.mechanical_manifest:
 mp=args.mechanical_manifest.resolve();mh=digest(mp)
 if not args.expected_sha or mh!=args.expected_sha:raise ValueError('Final export manifest hash must match explicit parent receipt')
 m=json.loads(mp.read_text());rows=[];all_step_hashes={}
 for row in m['rows']:
  b=row['bbox_mm'];path=mp.parent/'step'/(row['id']+'.step')
  step_hash=digest(path);expected=m['files']['step/'+row['id']+'.step']
  if step_hash!=expected:raise ValueError('Final STEP differs from manifest:'+row['id'])
  all_step_hashes[row['id']]=step_hash
  if not overlaps(hb,b):
   rows.append(dict(object=row['id'],status='pass_by_final_export_bounds',bbox_mm=b));continue
  s=cq.importers.importStep(str(path)).val();sources['mechanical/'+row['id']]=step_hash
  check('mechanical/'+row['id'],s,'final installed mechanical part; no own-connector exemption')
  rows.append(dict(object=row['id'],status=checks[-1]['status'],step_sha256=sources['mechanical/'+row['id']]))
 if digest(mp)!=mh:raise RuntimeError('Mechanical export changed during check')
 for name,h in all_step_hashes.items():
  if digest(mp.parent/'step'/(name+'.step'))!=h:raise RuntimeError('Mechanical STEP changed during check:'+name)
 mechanical=dict(manifest_path=str(mp),manifest_sha256=mh,all_step_sha256=all_step_hashes,rows=rows)
if digest(Path(__file__))!=VERIFICATION_SOURCE_SHA256:raise RuntimeError('Verifier changed during execution')
result=dict(status='pass_for_bounded_head_reservation' if all(x['status']=='pass' for x in checks) and all(not x['candidate_cells'] for x in hdmi) else 'failed_or_incomplete',
 geometry_input_sha256=input_hash,donor_addendum_sha256=digest(P/'usb-donor-provenance.json'),fps_context_receipt_sha256=digest(P/'context-input-receipt.json'),
 head_bbox_mm=hb,checks=checks,full_hdmi_material_screen=hdmi,mechanical=mechanical,source_files=sources,verification_source_sha256=VERIFICATION_SOURCE_SHA256,
 motion_scope='Static hard-head reservation and full carried FPS group. Co-translation preserves mutual geometry; XZ-disjoint entries stay separated for any relativeYtranslation. No USB removal/carry trajectory is selected while its complete installed lead and exit remain unknown.',
 overlap_volume_scope='Per-solid positive witnesses establish contact; their sum is not reported as occupied union volume where source components may overlap.',
 physical_qualified=False,remaining=['Final mechanical binding pending' if mechanical is None else 'Final binding applies to installed hard-head reservation only',
 'Adafruit4448 cuttable donor final copper cuts, two Pololu tails, diode/joints and full installed lead placement remain TBD',
 'Received overmold, actual exit and engagement are unmeasured; no wire exit is invented','Complete camera FPC and cooler/latch/tool corridor','Adafruit3557 adapter-to-socket/root transform','All baseline56 andM1 physical gates'])
report_path.write_text(json.dumps(result,indent=2));print(json.dumps(dict(report=str(report_path),status=result['status'],mechanical_bound=bool(mechanical))),flush=True)
