"""Consistent fresh-STEP candidate bounds; rounded design comparison, not metrology."""
from pathlib import Path
import json,hashlib,sys
import cadquery as cq
P=Path(__file__).parent;sys.path.insert(0,str(P.parent));import layout as L
base=json.loads((P/'out/comparison/baseline-envelopes.json').read_text());baseline={r['lens']:r for r in base['rows']};results=[]
for variant in ('compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc'):
 out=P/'out'/variant;mf=out/'manifest.json';m=json.loads(mf.read_text());boxes={};moment=[0,0,0];mass=0
 for r in m['rows']:
  if r['kind']=='keepout':continue
  f=out/'step'/f'{r["id"]}.step'
  if hashlib.sha256(f.read_bytes()).hexdigest()!=m['files'][f'step/{r["id"]}.step']:raise ValueError('STEP binding mismatch:'+str(f))
  s=cq.importers.importStep(str(f)).val();b=s.BoundingBox();boxes[r['id']]=[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
  c=L.lens_spec(m['lens'])['com'] if r['id']=='lens' else s.Center().toTuple();mass+=r['mass_est_g']
  for i in range(3):moment[i]+=r['mass_est_g']*c[i]
 b=[min(v[i] for v in boxes.values()) if i%2==0 else max(v[i] for v in boxes.values()) for i in range(6)];dims=[b[i+1]-b[i] for i in (0,2,4)];volume=dims[0]*dims[1]*dims[2];ref=baseline[m['lens']];core=m['core_dimensions_mm'];cv=core[0]*core[1]*core[2];com=[x/mass for x in moment]
 row=dict(variant=variant,manifest_sha256=hashlib.sha256(mf.read_bytes()).hexdigest(),core_dimensions_mm=core,core_envelope_mm3=cv,complete_bbox_mm=b,complete_dimensions_mm=dims,complete_bbox_volume_mm3=volume,overall_bbox_reduction_fraction=1-volume/ref['complete_bbox_volume_mm3'],core_envelope_reduction_fraction=1-cv/ref['core_envelope_mm3'],printed_part_count=sum(r['kind']=='printed' for r in m['rows']),mass_est_g=mass,com_est_mm=com,grip_axis_x=m['grip_axis_x'],com_offset_from_grip_mm=com[0]-m['grip_axis_x'],extrema_parts={str(i):[n for n,bb in boxes.items() if abs(bb[i]-b[i])<1e-5] for i in range(6)})
 results.append(row);print(variant, [round(x,1) for x in dims],round(volume/1e6,3),round(row['overall_bbox_reduction_fraction']*100,2),flush=True)
result=dict(baseline=base['rows'],candidates=results,method='Fresh STEP imports without tessellation for every candidate part; baseline printed STEP and fresh baseline COTS/hardware source solids. Report0.1mm/~0.1% precision only. Bounding envelope is not occupied material or measured product volume.',mass_caveat=base['mass_caveat'],physical_qualified=False)
(P/'out/comparison/assembled-comparison.json').write_text(json.dumps(result,indent=2))
