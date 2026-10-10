"""Separate, unselected2mm carrier saddle proposal; never mutates mechanical model."""
from cv_io import read_text, write_text
import json,hashlib,math,itertools,ast
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
import routes as R
from verify_fps_access import V,box,bb,overlaps,digest,bbox
P=Path(__file__).parent;mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(read_text(mp));mh=digest(mp)
# Reuse only the exact convex material-cell constructor, not the executable verifier.
tree=ast.parse(read_text(P/'verify_hdmi.py'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='cell');exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'verify_hdmi.py'),'exec'))
definition=dict(floor=[-136.2,-130.8,6.1,15.1,76.05,78.05],bridge=[-136.2,-125.5,11.1,20.2,76.05,78.05],root=[-130.5,-125.5,17.2,20.2,73.,78.05])
saddle=box(definition['floor']).fuse(box(definition['bridge']),box(definition['root']));sh={}
for row in m['rows']:
 n=row['id'];fp=mp.parent/'step'/f'{n}.step'
 if digest(fp)!=m['files'][f'step/{n}.step']:raise ValueError(n+' STEP mismatch')
 sh[n]=cq.importers.importStep(str(fp)).val()
attachment=sh['carrier'].intersect(saddle).Volume();union=sh['carrier'].fuse(saddle);hits=[];sb=bb(saddle)
for n,s in sh.items():
 if n=='carrier' or not overlaps(sb,bb(s)):continue
 common=saddle.intersect(s);v=common.Volume()
 if v>1e-6:hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(common)))
r=R.build();usd=next(x for x in r['routes'] if x['id']=='usb_5v');from verify_fps_access import tube
us=tube(usd['curve'],usd['od_mm'])[0];uv=saddle.intersect(us).Volume() if saddle.distance(us)<1e-7 else 0
hds=[]
for pose in ('installed','premate','both_unplugged'):
 hd=r[{'installed':'hdmi_ribbon','premate':'hdmi_ribbon_premate','both_unplugged':'hdmi_ribbon_unplugged'}[pose]]
 if 'segments' not in hd:continue
 for shift in [0] if pose=='installed' else range(0,61,2):
  candidates=[]
  for i,s in enumerate(hd['segments']):
   b=bbox(s['box']);b[2]+=shift;b[3]+=shift
   if overlaps(sb,b):candidates.append((i,s))
  hh=[]
  for i,s in candidates:
   c=cell(s['vertices'])
   if c is None:continue
   c=c.translate(V(0,shift,0));common=c.intersect(saddle);v=common.Volume()
   if v>1e-7:hh.append(dict(cell=i,overlap_mm3=v,bbox_mm=bb(common)))
  if shift%10==0:print('HDMI support study',pose,shift,'candidates',len(candidates),'hits',len(hh),flush=True)
  if hh or shift==0:hds.append(dict(hdmi_pose=pose,shift_y_mm=shift,hits=hh,candidate_cells=len(candidates)))
result=dict(status='UNSELECTED SUPPORT STUDY; failed wire deployment blocks integration',mechanical_manifest_sha256=mh,source_sha256=digest(Path(__file__)),saddle_boxes_mm=definition,saddle_valid=saddle.isValid(),saddle_solids=len(saddle.Solids()),carrier_contact_mm3=attachment,carrier_union_valid=union.isValid(),carrier_union_solids=len(union.Solids()),rigid_hits=hits,usb5v_overlap_mm3=uv,hdmi_checks=hds,remaining=['Tie placement, full strap/head geometry and threading','Actual cut-and-replace tie restraint of both housing halves','Measured cutter jaws/cutting stroke and wire protection','Saddle/root printed strength and maximum housing dimension receipt check','Full source-backed wire deployment currently collides; no integration or retention approval'])
out=P/'out/fps-service-study';out.mkdir(exist_ok=True);write_text(out/'saddle-proposal-checks.json',json.dumps(result,indent=2));cq.exporters.export(saddle,str(out/'saddle-proposal.step'));print(json.dumps(result),flush=True)
