import cadquery as cq,zipfile,json,time
from pathlib import Path
import power_geometry as P
import argparse
ap=argparse.ArgumentParser(description='Historical archive diagnostic; not a current release check');ap.add_argument('--archive',required=True);args=ap.parse_args()
z=zipfile.ZipFile(args.archive);prefix='cad/gs8-d2-v1/candidate-vertical/out/compact-kowa_lm6hc/step/'
for n,cuts in [('base_grip',P.grip_cuts()),('tub',P.tub_cuts())]:
 path=Path('/tmp')/('oldvalid-'+n+'.step');path.write_bytes(z.read(prefix+n+'.step'));sh=cq.importers.importStep(str(path)).val();print(n,'original',sh.isValid(),len(sh.Solids()),sh.Volume(),flush=True)
 t=time.time();tool=cuts[0].fuse(*cuts[1:]);print('tool',time.time()-t,tool.isValid(),len(tool.Solids()),flush=True)
 out=sh.copy().cut(tool.copy());print('cut',out.isValid(),len(out.Solids()),out.Volume(),flush=True)
 for s in out.Solids():
  b=s.BoundingBox();print('solid',s.Volume(),[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],flush=True)
 cq.exporters.export(out,str(Path('/tmp')/('corrected-'+n+'.step')))
