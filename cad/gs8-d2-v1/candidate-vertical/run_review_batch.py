"""Serialized reproducible review evidence. Run this script through run_locked.py."""
import subprocess,sys,json,time
from pathlib import Path
P=Path(__file__).parent;logs=P/'out/checklogs';logs.mkdir(exist_ok=True)
jobs=[('rigid-compact-kowa','verify_candidate.py',[]),('mesh-compact-kowa','verify_print_meshes.py',[]),('power-service','verify_power_service.py',[]),('csi-access','verify_csi_access.py',[]),('hdmi300','verify_hdmi.py',['--snapshot',str(P/'routing-snapshots/hdmi-300-exact-input/input.json')]),('rigid-compact-fujinon','verify_candidate.py',['--variant','compact-fujinon_hf6xa']),('mesh-compact-fujinon','verify_print_meshes.py',['--variant','compact-fujinon_hf6xa']),('rigid-original-kowa','verify_candidate.py',['--variant','original-kowa_lm6hc']),('mesh-original-kowa','verify_print_meshes.py',['--variant','original-kowa_lm6hc']),('volume-compact','measure_volume.py',[]),('volume-original','measure_volume.py',['original-kowa_lm6hc']),('volume-baseline','measure_volume.py',['baseline'])]
results=[]
for name,script,args in jobs:
 t=time.time();print('START',name,flush=True)
 with (logs/f'{name}.log').open('w') as f:r=subprocess.run([sys.executable,str(P/script),*args],stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(id=name,exit_code=r.returncode,elapsed_seconds=time.time()-t,log=str((logs/f'{name}.log').relative_to(P))));print('END',name,r.returncode,flush=True)
(logs/'batch.json').write_text(json.dumps(dict(jobs=results,note='HDMI report preserves rejected over-PCB tool failures. Read every scope and physical STOP; this batch is not a release audit.'),indent=2))
