"""Exact model void inside the stated core box, not all void is removable waste.
COTS are source proxies; service/cooling/cable reservations are separately reported.
"""
import sys,json,hashlib,time
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
variant=sys.argv[1] if len(sys.argv)>1 else 'compact-kowa_lm6hc'
if variant=='baseline':
 sys.path.insert(0,str(BASE));import layout as L,cots
 shapes=[cq.importers.importStep(str(BASE/'out/step/parts'/f'{p}.step')).val() for p in L.PARTS]
 shapes += [r['shape'].val() for r in cots.build_all(L).values() if r.get('shape') is not None]
 dims=(154,70,100);origin=(-154,-35,0)
else:
 out=ROOT/'out'/variant;manifest_start=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest();meta=json.loads((out/'manifest.json').read_text())
 for rel,h in meta['sources'].items():
  if hashlib.sha256((BASE/rel).read_bytes()).hexdigest()!=h:raise ValueError('Source binding mismatch:'+rel)
 for r in meta['rows']:
  rel=f'step/{r["id"]}.step'
  if hashlib.sha256((out/rel).read_bytes()).hexdigest()!=meta['files'][rel]:raise ValueError('STEP binding mismatch:'+rel)
 shapes=[cq.importers.importStep(str(out/'step'/f'{r["id"]}.step')).val() for r in meta['rows'] if r['kind']!='keepout' and r['id']!='pi5']
 sys.path.insert(0,str(BASE));import layout as L,official_pi5_assembly as PiA
 pi_components=list(PiA.build_parts(L).values())
 dims=meta['core_dimensions_mm'];origin=tuple(meta.get('core_origin_mm',(-dims[0],-dims[1]/2,0)))
core=cq.Solid.makeBox(*dims,cq.Vector(*origin))
clipped=[]
for i,s in enumerate(shapes):
 b=s.BoundingBox()
 inside=all(origin[j]-1e-7<=v<=origin[j]+dims[j]+1e-7 for j,vs in enumerate(((b.xmin,b.xmax),(b.ymin,b.ymax),(b.zmin,b.zmax))) for v in vs)
 q=s if inside else core.intersect(s)
 if q.Volume()>.0001:clipped.append(q)
 print('clip',i,round(q.Volume(),3),flush=True)
# A single multi-tool boolean removes the union, so overlapping contacts are not double-counted.
void=core.cut(*clipped)
interval=None
if variant!='baseline':
 # Subtract the simple datum PCB exactly. For the remaining overlapping source
 # assemblies use a conservative union-volume bound, avoiding the known tiny
 # CSI contact Boolean failure and never treating compound volume as occupied.
 void=void.cut(pi_components[0])
 remaining_raw_sum=sum(q.Volume() for q in pi_components[1:])
 interval=[max(0.,void.Volume()-remaining_raw_sum),void.Volume()]
 print('bounded remaining source assembly volume',remaining_raw_sum,flush=True)
if not void.isValid():raise ValueError('Invalid void boolean')
result=dict(variant=variant,core_dimensions_mm=dims,core_envelope_mm3=core.Volume(),model_solid_union_mm3=core.Volume()-void.Volume(),model_void_mm3=void.Volume(),model_void_fraction=void.Volume()/core.Volume(),definition='Core box minus the Boolean union of exported material/proxy solids; named Pi components are subtracted sequentially, never volume-summed (non-material keepouts excluded), including enclosure, hardware and purchased-part proxies. Cooling air, cable space, assembly/service clearance and proxy omissions are included in this void; it is NOT a claim that all this volume can be removed.',qualification='CAD Boolean proxy-volume estimate, not measured internal volume; report only to1cm³. Source-kernel witness discrepancies remain documented; no sub-mm³ accuracy is claimed. Cables and reserved access envelopes are not subtracted.',generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
result['verification_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if variant!='baseline':
 if hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()!=manifest_start:raise ValueError('Manifest changed during volume calculation')
 result['manifest_sha256']=manifest_start
 result['model_void_mm3']=None
 result['model_void_fraction']=None
 result['model_solid_union_mm3']=None
 result['model_void_interval_mm3']=interval
 result['model_void_interval_cm3_outward_rounded']=[__import__('math').floor(interval[0]/1000),__import__('math').ceil(interval[1]/1000)]
 result['model_solid_union_interval_mm3']=[core.Volume()-interval[1],core.Volume()-interval[0]]
 result['interval_definition']='After subtracting the non-Pi material union and simple PCB, upper bound removes no further Pi material; lower bound subtracts the sum of every remaining Pi source-solid volume, including overlaps and any material outside the core. Actual union subtraction must lie between these CAD bounds. No raw compound sum is claimed as occupied volume.'
 result['definition']='Core box minus exported material/proxy union. Current detailed Pi assembly contributes a conservative interval, not a completed exact occupied union. Cooling air, cable/service clearance and omitted flexible material are within this empty-model volume; it is not removable waste.'
 result['qualification']='Conservative CAD proxy-volume interval, rounded outward to whole cm3; source/kernel and baseline representation caveats remain. The slow/unreliable complete CSI Boolean was stopped and preserved as a diagnostic. No physical measurement or precise unused-volume claim.'
 result['comparison_caveat']='The candidate uses source-corrected Pi geometry while baseline retains its original approximate proxy. Void differences include that representation change, not only packaging changes.'
folder=ROOT/'out'/'comparison';folder.mkdir(exist_ok=True)
(folder/f'volume-{variant}.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
