"""Generate a source-bound overlapping component assembly for the corrected Pi feature model.
Run under ../run_locked.py; model.py verifies this receipt before reusing the STEP.
"""
from pathlib import Path
import hashlib,json,sys,time
import cadquery as cq
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent))
import layout as L
import official_pi5_assembly as A
import official_pi5_geometry as G
S=G.SOURCE;D=P/'out/source-components';D.mkdir(exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[P/n for n in ('official_pi5_assembly.py','official_pi5_geometry.py','official_pi5_csi.py')]+[P.parent/'layout.py']
inputs += [S/n for n in ('connector-extraction.json','port-landmarks.json','cam_disp0-native.step','cam_disp1-native.step','usb2-native.step','usb3-native.step','ethernet-native.step','gpio-native.step','usbc-native.step','LICENSE.txt')]
before={str(f.relative_to(P.parent)):digest(f) for f in inputs}
print('Load source-registered Pi feature solids',flush=True);parts=A.build_parts(L)
print('Preserve named source components without Boolean fusion',flush=True);s=A.as_assembly_compound(parts)
print('Export corrected Pi',flush=True);f=D/'pi5-corrected.step';cq.exporters.export(s,str(f))
after={str(f.relative_to(P.parent)):digest(f) for f in inputs}
if before!=after:raise RuntimeError('Source changed during Pi union')
b=s.BoundingBox();meta={'generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sources':after,'generator_sha256':digest(Path(__file__)),
 'file':'pi5-corrected.step','sha256':digest(f),'valid':s.isValid(),'solid_count':len(s.Solids()),'raw_solid_volume_sum_mm3':s.Volume(),'occupied_volume_mm3':None,'representation':'Overlapping named component assembly; raw solid-volume sum is not occupied material',
 'bbox_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],'named_parts':list(parts),'component_solid_counts':{n:len(q.Solids()) for n,q in parts.items()},'provenance':A.metadata(),'physical_qualified':False}
(D/'pi5-corrected.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta),flush=True)
