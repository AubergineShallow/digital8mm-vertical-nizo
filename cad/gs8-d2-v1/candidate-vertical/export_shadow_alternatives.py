"""Export comparison variants; no compact-service qualification is transferred."""
from pathlib import Path
import subprocess,sys,json,time
P=Path(__file__).resolve().parent;logs=P/'out/comparison/logs';logs.mkdir(parents=True,exist_ok=True)
commands=[('fujinon_export',['export_candidate.py','--lens','fujinon_hf6xa']),('original_export',['export_candidate.py','--storage','original']),('fujinon_mesh',['verify_print_meshes.py','--variant','compact-fujinon_hf6xa']),('original_mesh',['verify_print_meshes.py','--variant','original-kowa_lm6hc']),('fujinon_void',['measure_volume.py','compact-fujinon_hf6xa']),('original_void',['measure_volume.py','original-kowa_lm6hc']),('comparison',['measure_comparison.py'])]
rows=[]
for name,args in commands:
 print(name,'starting',flush=True)
 cmd=[sys.executable,str(P/args[0])]+args[1:]
 with (logs/(name+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(check=name,arguments=args,exit_code=r.returncode));print(name,'exit',r.returncode,flush=True)
 if r.returncode:break
(P/'out/comparison/shadow-variant-run.json').write_text(json.dumps(dict(checks=rows,physical_qualified=False,scope='Variant exports, print-mesh topology and fresh STEP bounds/void only. Selected compact service checks are not transferred to alternatives.'),indent=2))
raise SystemExit(any(x['exit_code'] for x in rows))
