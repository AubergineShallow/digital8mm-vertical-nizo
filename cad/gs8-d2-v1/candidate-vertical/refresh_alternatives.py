import subprocess,sys,json
from pathlib import Path
P=Path(__file__).parent
jobs=[('export-fujinon','export_candidate.py',['--storage','compact','--lens','fujinon_hf6xa']),('export-original','export_candidate.py',['--storage','original','--lens','kowa_lm6hc']),('rigid-fujinon','verify_candidate.py',['--variant','compact-fujinon_hf6xa']),('mesh-fujinon','verify_print_meshes.py',['--variant','compact-fujinon_hf6xa']),('rigid-original','verify_candidate.py',['--variant','original-kowa_lm6hc']),('mesh-original','verify_print_meshes.py',['--variant','original-kowa_lm6hc']),('comparison','measure_comparison.py',[]),('void-compact','measure_volume.py',[]),('void-original','measure_volume.py',['original-kowa_lm6hc'])]
results=[]
for name,script,args in jobs:
 print('START',name,flush=True)
 with open('/tmp/d2-final-'+name+'.log','w') as f:r=subprocess.run([sys.executable,str(P/script),*args],stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(id=name,exit=r.returncode));print('END',name,r.returncode,flush=True)
 if r.returncode and name.startswith('export'):break
 # A retained source/proxy collision is reported, not hidden by stopping measurements.
(P/'out/alternative-refresh.json').write_text(json.dumps(results,indent=2))
