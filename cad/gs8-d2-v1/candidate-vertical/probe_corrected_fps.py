import sys,json
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P.parent))
import cadquery as cq
import fps_geometry as F
out=P/'out/fps-source-study';out.mkdir(exist_ok=True)
parts=F.switch_parts();parts['knob_fps']=F.knob()
for n,s in parts.items():
 cq.exporters.export(s,str(out/f'{n}.step'));print(n,s.isValid(),len(s.Solids()),s.Volume(),flush=True)
(out/'source-geometry.json').write_text(json.dumps(F.provenance(),indent=2))
