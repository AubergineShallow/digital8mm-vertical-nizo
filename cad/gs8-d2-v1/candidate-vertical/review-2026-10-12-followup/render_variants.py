# SPDX-License-Identifier: MIT
"""Render all saved variants serially; no geometry rebuilding or qualification."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parents[1];sys.path.insert(0,str(C))
from cv_io import child_env,read_text,write_text
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for variant in ('compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc'):
 d=C/'out'/variant;m=json.loads(read_text(d/'manifest.json'));mh=sha(d/'manifest.json')
 inputs={d/'manifest.json':mh,C/'render_review.py':sha(C/'render_review.py')}
 inputs.update({C.parent/n:h for n,h in m['sources'].items()})
 inputs.update({d/n:h for n,h in m['files'].items()})
 assert all(p.is_file() and sha(p)==h for p,h in inputs.items()),'Stale or missing render input'
 for view in ('hero','rear','vent_side','vent_front'):
  print(variant,view,'starting',flush=True);start=time.time()
  cmd=['blender','-b','-t','4','--python',str(C/'render_review.py'),'--','--assets',str(d/'meshes'),'--out',str(d/'renders'),'--view',view,'--samples','48','--revision','Bonded-catch / QT review followup; physical holds open']
  subprocess.run(cmd,check=True,env=child_env())
  assert all(sha(p)==h for p,h in inputs.items()),'Input changed while rendering'
  records.append(dict(variant=variant,view=view,manifest_sha256=mh,seconds=round(time.time()-start,2),physical_qualified=False))
  write_text(Path(__file__).with_name('render-run.json'),json.dumps(dict(checks=records,source_sha256=sha(Path(__file__))),indent=2)+'\n')
