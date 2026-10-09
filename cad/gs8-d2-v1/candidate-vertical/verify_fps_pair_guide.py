"""Bounded open axial guide and whole mated-harness rigid sweep."""
from pathlib import Path
import sys,json
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import routes as R,fps_geometry as FG,fps_fixed_support as FS,fps_pair_guide as G,fps_ck1044_mated_carry as F
from verify_fps_access import V,box,bb,overlaps,digest,tube,bbox
mp=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(mp.read_text());mh=digest(mp)
sh={r['id']:cq.importers.importStep(str(mp.parent/'step'/f"{r['id']}.step")).val() for r in m['rows']};sh.update(FG.switch_parts());cp=P/'out/structural-proposals/reinforced-carrier.step';sh['carrier']=cq.importers.importStep(str(cp)).val()
g=G.build();checks=[]
def check(name,s,t):
 if not overlaps(bb(s),bb(t)):return
 c=s.intersect(t);v=c.Volume();q=dict(item=name,overlap_mm3=v)
 if v>1e-6:q['bbox_mm']=bb(c)
 checks.append(q)
 if v>1e-6:print(json.dumps(q),flush=True)
for n,s in sh.items():
 if n!='tub':check('static/'+n,g,s)
f=F.build(R,0,0);parts={w['id']:tube(w['curve'],w['od_mm'])[0] for w in f['wire_parts']};parts.update(pair=box(bbox(f['junction']['box'])),switch=sh['switch_1824'],carrier=sh['carrier'])
for dy in range(0,71):
 for n,s in parts.items():check('carry/'+n+'/'+str(dy),g,s.translate(V(0,dy,0)))
u=sh['tub'].fuse(g,FS.shelf());result=dict(status='geometric guide proposal only',mechanical_manifest_sha256=mh,carrier_sha256=digest(cp),source_sha256={n:digest(P/n) for n in ['verify_fps_pair_guide.py','fps_pair_guide.py','fps_fixed_support.py','fps_ck1044_mated_carry.py']},guide=dict(valid=g.isValid(),solids=len(g.Solids()),volume_mm3=g.Volume(),tub_common_mm3=sh['tub'].intersect(g).Volume(),combined_tub_valid=u.isValid(),combined_tub_solids=len(u.Solids()),inner_x=[-136.125,-130.875],floor_top_z=78.05,lip_bottom_z=81.85,lip_top_z=83.35,wire_slot_width_bottom_mm=2.8,wire_slot_width_top_mm=4.6,y=[6,15]),checks=checks,physical_gates=['Actual maximum body profile/corner radii and narrow throat retention','Print tolerance, lip flex/strength and handling loads','Whole harness staging, received wire insulation OD and bend memory'])
out=P/'out/fps-service-study';(out/'open-guide-checks.json').write_text(json.dumps(result,indent=2));cq.exporters.export(g,str(out/'picoblade-open-guide.step'));print(json.dumps(result['guide']),flush=True);print('DONE',sum(q['overlap_mm3']>1e-6 for q in checks),'hits',flush=True)
