"""Exact test-only angled forceps envelopes; no actual tool or latch qualification."""
import json,math
from pathlib import Path
import cadquery as cq
from verify_fps_access import V,box,bbox,bb,overlaps,tube,digest
P=Path(__file__).parent;mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(mp.read_text());mh=digest(mp);sp=P/'routing-snapshots/fps-access-20261009-0402/twenty-one-full-wire-shapes.json';pose=json.loads(sp.read_text())['shapes'][20]
rows={r['id']:r for r in m['rows']};moving={'panel','encoder','switch_1824','knob_exp','knob_fps','power_button','power_nut_reserve','foam_pad'}
sh={}
for n in rows:
 if n.startswith('p_panel'):continue
 f=mp.parent/'step'/f'{n}.step'
 if digest(f)!=m['files'][f'step/{n}.step']:raise ValueError('STEP hash mismatch: '+n)
 s=cq.importers.importStep(str(f)).val();sh[n]=s.translate(V(0,10,0)) if n in moving else s
for wire in pose['wire_parts']:sh[wire['id']]=tube(wire['curve'],wire['od_mm'])[0]
sh['fps_ph_pair']=box(bbox(pose['junction']['box']))
out=P/'out/fps-service-study';out.mkdir(exist_ok=True);results=[]
(out/'over-top-long-tine-source.py').write_bytes(Path(__file__).read_bytes())
def cyl(a,b,r):
 d=b-a;return cq.Solid.makeCylinder(r,d.Length,a,d.normalized())
for label,entry in [('parent_angled',V(-118,48,117)),('vertical_x',V(-133.5,43,119)),('frontward_steep',V(-112,48,125))]:
 target=V(-133.5,21.3,79.7);d=(entry-target).normalized();join=target+d*35
 # Two opposing 2mm-thick x jaws, 4mm high and6mm long, at the stated full PH box sides.
 # Arms are2mm diameter and converge over15mm to an8mm-diameter shaft.
 # Actual hinge, closing arc, teeth, latch actuation and split housing datums are absent.
 jaws=[box([-139.5,-137.5,14.1,21.3,77.7,81.7]),box([-129.5,-127.5,14.1,21.3,77.7,81.7])]
 arms=[cyl(V(x,21.3,79.7),join,1) for x in (-138.5,-128.5)]
 shaft=cyl(join,entry+d*25,4)
 tool=cq.Compound.makeCompound(jaws+arms+[shaft]);tb=bb(tool);hits=[];clearances=[]
 for n,f in sh.items():
  if not overlaps(tb,bb(f)):continue
  # Exact crop to this particular moving obstacle and whole tool extent.
  f=f.intersect(box([tb[k]-.01 if k%2==0 else tb[k]+.01 for k in range(6)]))
  if f.Volume()<1e-8:continue
  dist=tool.distance(f);v=0
  if dist<1e-7:
   common=tool.intersect(f);v=common.Volume()
   if v>1e-6:hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(common)))
  clearances.append(dict(part=n,gap_mm=dist,overlap_mm3=v))
 row=dict(label=label,target=list(target.toTuple()),entry=list(entry.toTuple()),status='blocked' if hits else 'proxy_clear_only',hits=hits,clearances=clearances,tool_parts='Two2×7.2×4mm rectangular jaw pads; two2mm-diameter35mm converging arm envelopes;8mm-diameter shaft extended25mm beyond entry. Not a catalogued real forceps model; whole approach/closing motion not tested.')
 if label=='vertical_x':
  # Withdraw the whole tool along its approach axis, with fixed PH and wires.
  # Reverse is the same geometric rigid insertion path; jaw closing is not modeled.
  swept_hits=[];steps=range(81);b0=bb(tool);end=tool.translate(d*40);be=bb(end);sweepbox=box([min(b0[k],be[k])-.01 if k%2==0 else max(b0[k],be[k])+.01 for k in range(6)])
  cropped={n:f.intersect(sweepbox) for n,f in sh.items() if overlaps(bb(f),bb(sweepbox))};cropped={n:f for n,f in cropped.items() if f.Volume()>1e-8}
  for idx in steps:
   dist=idx*.5;moving_tool=tool.translate(d*dist);mtb=bb(moving_tool)
   for n,f in cropped.items():
    if not overlaps(mtb,bb(f)):continue
    if moving_tool.distance(f)>1e-7:continue
    common=moving_tool.intersect(f);volume=common.Volume()
    if volume>1e-6:swept_hits.append(dict(tool_withdrawal_mm=dist,part=n,overlap_mm3=volume,bbox_mm=bb(common)))
  row['sampled_rigid_tool_approach']=dict(poses=len(steps),step_mm=.5,translation_mm=40,status='blocked' if swept_hits else 'sampled_clear_only',hits=swept_hits,note='Discrete poses only. Whole rigid jaw pads, arms and shaft move; actual jaw closing remains unmodeled.')
 results.append(row);print(json.dumps(row),flush=True)
 (out/'over-top-long-tine-checks.json').write_text(json.dumps(dict(diagnostic_only=True,physical_qualified=False,source_sha256=digest(Path(__file__)),mechanical_manifest_sha256=mh,snapshot_sha256=digest(sp),checks=results),indent=2))
