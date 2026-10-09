"""Check isolated official CSI assemblies against current candidate context.

Exact source nominal geometry and conservative registration envelopes are
reported separately. A proxy conflict is not a real-hardware impossibility.
"""
import ast,hashlib,itertools,json,math,sys
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
P=Path(__file__).resolve().parent;ROOT=P.parents[1];sys.path.insert(0,str(ROOT))
import official_pi5_csi as C
V=cq.Vector
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def bounds(b):return [v for k in 'xyz' for v in b[k]]
def overlap(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,2,4))
def box(b):return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))
for name,functions in [('source-verify_hdmi.py',{'cell'}),('source-verify_fps_access.py',{'rounded_wire','tube'}),('source-power_geometry.py',{'simplify','cylinder','ball'})]:
 tree=ast.parse((P/name).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/name),'exec'))
objects={};sources={};notes={}
def add(n,s,note):objects[n]=s;notes[n]=note
manifest=ROOT/'out/compact-kowa_lm6hc/manifest.json';mh=digest(manifest)
for path in sorted((manifest.parent/'step').glob('*.step')):
 if path.stem in ('assembly','pi5','carrier'):continue
 # Individual component files; the inherited Pi includes the proxy being replaced.
 add(path.stem,cq.importers.importStep(str(path)).val(),'Candidate rigid proxy; source geometry not hardware-qualified')
 sources[str(path.relative_to(ROOT))]=digest(path)
carrier=ROOT/'out/structural-proposals/reinforced-carrier.step'
add('reinforced_carrier',cq.importers.importStep(str(carrier)).val(),'Reinforced carrier candidate');sources[str(carrier.relative_to(ROOT))]=digest(carrier)
r=json.loads((P/'context.json').read_text());f=json.loads((P/'fps-mated-carry-context-0556.json').read_text());h=json.loads((P/'input.json').read_text())
for w in r['routes']:
 if w['id'] in ('usb_5v','fan','power_button'):add('wire_'+w['id'],tube(w['curve'],w['od_mm'])[0],'Analytic modeled route, may not include whole stock')
for w in r['header_wire_branches']:add('branch_'+w['id'],tube(w['curve'],w['od_mm'])[0],'Analytic modeled branch')
q=r['signal_geometry'];add('wire_qt',tube(q['qt']['curve'],q['qt']['od_mm'])[0],'Analytic modeled QT')
for w in q['run_cores']:add('wire_'+w['id'],tube(w['curve'],w['od_mm'])[0],'Analytic modeled RUN')
for w in f['wire_parts']:add('fps_'+w['id'],tube(w['curve'],w['od_mm'])[0],'Selected complete mated FPS branch')
for core in r['power_geometry']['cores']:
 for part in core['flexible_wire_parts']:
  pts=simplify(part['points'],.04);radius=core['od_mm']/2+.04
  pieces=[cylinder(a,b,radius) for a,b in zip(pts,pts[1:]) if math.dist(a,b)>1e-8]+[ball(p,radius) for p in pts]
  add('power_'+core['id']+'_'+part['id'],cq.Compound.makeCompound(pieces),'Complete polyline diameter capsules including0.04mm chord allowance; root joints remain gated')
for p in h['connectors']:
 if p['id'].startswith('p_hdmi'):add(p['id'],box(bounds(p['box'])),'HDMI hard-head envelope')
for state in ('installed','premate'):
 relevant=[cell(seg['vertices']) for seg in h['hdmi_'+state]['segments'] if overlap(bounds(seg['box']),[-91,-80,-2,3,46,63])]
 relevant=[s for s in relevant if s is not None]
 if relevant:add('hdmi_'+state,cq.Compound.makeCompound(relevant),'Complete sampled HDMI checked by bounding rejection then exact potentially interacting cells')
 else:notes['hdmi_'+state]='No full-width HDMI cell bounds overlap either CSI region; complete material screened'
objects['fps_junction']=box(bounds(f['junction']['box']));notes['fps_junction']='Complete selected mated junction box'
parts={n:[(s,bb(s)) for s in obj.Solids()] for n,obj in objects.items()}
checks=[]
def check(name,shape,kind):
 b=bb(shape);hits=[];tests=0
 for n,rows in parts.items():
  witnesses=[]
  for s,sb in rows:
   if not overlap(b,sb):continue
   for comp in shape.Solids():
    if not overlap(bb(comp),sb):continue
    common=comp.intersect(s);tests+=1;v=common.Volume()
    if v>1e-7:witnesses.append(dict(overlap_mm3=v,bbox_mm=bb(common)))
  if witnesses:hits.append(dict(obstacle=n,sum_pair_overlap_mm3=sum(x['overlap_mm3'] for x in witnesses),witnesses=witnesses))
 row=dict(component=name,kind=kind,bbox_mm=b,hits=hits,exact_intersections=tests)
 checks.append(row);print(json.dumps(dict(component=name,kind=kind,hits=[x['obstacle'] for x in hits],exact=tests)),flush=True)
for n,s in C.exact_parts().items():check(n,s,'exact official source nominal underside registration')
for n,row in C.conservative_envelopes().items():check(n,row['shape'],'source-derived envelope spanning explicit PCB thickness datum bracket')
if digest(manifest)!=mh:raise RuntimeError('Mechanical export changed during check')
result=dict(mechanical_manifest_sha256=mh,source_files=sources,checks=checks,provenance=C.provenance(),helper_sha256=digest(ROOT/'official_pi5_csi.py'),
 context_sha256=digest(P/'context.json'),fps_input_sha256=digest(P/'fps-mated-carry-context-0556.json'),hdmi_input_sha256=digest(P/'input.json'),
 object_notes=notes,excluded_inherited_pi='The inherited pi5 STEP contains the old CSI proxy itself and is superseded locally by this isolated source correction. PCB mounting contact is inherent to the source model, not a cable clearance exception.',
 physical_qualified=False,remaining=['USB5V route is the old wrong-jack diagnostic and will be corrected separately','The GS camera connector/stiffener free-flex datum remains absent','No full200mm16mm-wide FPC geometry exists','Open latch and tools are not represented by the closed source pose','Cooler proxy conflicts require source-derived cooler geometry, not invented local cuts'])
(P/'official-csi-context-checks.json').write_text(json.dumps(result,indent=2))
print('Saved official-csi-context-checks.json',flush=True)
