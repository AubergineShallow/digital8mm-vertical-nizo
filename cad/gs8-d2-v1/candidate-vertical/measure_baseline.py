"""Read-only baseline complete-assembly bounds and proxy mass for both lenses."""
import json,sys,hashlib
from pathlib import Path
import cadquery as cq
P=Path(__file__).parent;R=P.parent;sys.path.insert(0,str(R));import layout as L,cots,printed_collar
printed={n:cq.importers.importStep(str(R/'out/step/parts'/f'{n}.step')).val() for n in L.PARTS}
results=[]
for lens in ('kowa_lm6hc','fujinon_hf6xa'):
 L.LENS=lens;rows={}
 for n,shape in printed.items():
  if n=='lens_collar' and lens=='fujinon_hf6xa':shape=printed_collar.build_part(L).val()
  rows[n]=dict(shape=shape,mass=L.mass_g(shape.Volume(),n),kind='printed')
 for n,row in cots.build_all(L).items():
  if row.get('shape') is not None:rows[n]=dict(shape=row['shape'].val(),mass=row.get('mass') or 0,kind=row['kind'])
 boxes={}
 for n,r in rows.items():
  b=r['shape'].BoundingBox();boxes[n]=[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
 bounds=[(min(v[i] for v in boxes.values()) if i%2==0 else max(v[i] for v in boxes.values())) for i in range(6)];dims=[bounds[i+1]-bounds[i] for i in (0,2,4)];mass=sum(r['mass'] for r in rows.values());moment=[0,0,0]
 for n,r in rows.items():
  c=L.lens_spec(lens)['com'] if n=='lens' else r['shape'].Center().toTuple()
  for i in range(3):moment[i]+=r['mass']*c[i]
 com=[x/mass for x in moment]
 results.append(dict(lens=lens,complete_bbox_mm=bounds,complete_dimensions_mm=dims,complete_bbox_volume_mm3=dims[0]*dims[1]*dims[2],core_dimensions_mm=[154,70,100],core_envelope_mm3=154*70*100,printed_part_count=len(printed),mass_est_g=mass,com_est_mm=com,grip_axis_x=L.GRIP['axis_x'],com_offset_from_grip_mm=com[0]-L.GRIP['axis_x'],extrema_parts={str(i):[n for n,b in boxes.items() if abs(b[i]-bounds[i])<1e-5] for i in range(6)}))
sourcefiles=list(R.glob('*.py'))+list((R/'out/step/parts').glob('*.step'))
result=dict(baseline_head='d38468e58eb2b02d56743e2e0cfdd8f780818a65',rows=results,sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sourcefiles},definition='Axis-aligned bounding union of every baseline printed/COTS/individual hardware solid; not occupied material volume.',mass_caveat='Source proxy masses, printed density/infill estimates and lens source CoM. LegacyXT30 mass12g includes fused pigtail lump at rigid proxy; other harness masses omitted. No measured balance.',physical_qualified=False)
folder=P/'out/comparison';folder.mkdir(exist_ok=True);(folder/'baseline-envelopes.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
