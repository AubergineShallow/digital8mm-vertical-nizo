import subprocess,sys,json,time
from pathlib import Path
P=Path(__file__).parent
jobs=[('rigid','verify_candidate.py',[]),('mesh','verify_print_meshes.py',[]),('csi','verify_csi_source.py',[]),('power','verify_power_service.py',[]),('hdmi','verify_hdmi.py',['--snapshot',str(P/'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json')])]
jobs += [('fps','verify_fps_integrated.py',[]),('static-wire','verify_wire_solids.py',['--snapshot',str(P/'routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json')])]
jobs += [('wall-context','verify_wall_probe_context.py',[]),('microsd-dependency','verify_microsd_service.py',[])]
results=[]
for name,script,args in jobs:
 print('START',name,flush=True)
 with open('/tmp/d2-final-'+name+'.log','w') as f:r=subprocess.run([sys.executable,str(P/script),*args],stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(id=name,exit=r.returncode));print('END',name,r.returncode,flush=True)
(P/'out/primary-refresh.json').write_text(json.dumps(results,indent=2))
