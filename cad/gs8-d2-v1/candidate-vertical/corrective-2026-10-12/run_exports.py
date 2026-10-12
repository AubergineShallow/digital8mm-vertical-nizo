"""Oct12 local review export batch. Run through run_locked.py; never publishes."""
import sys, subprocess, json, hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from cv_io import child_env, open_text, write_text
jobs=[('compact-kowa_lm6hc',[]),('compact-fujinon_hf6xa',['--lens','fujinon_hf6xa']),('original-kowa_lm6hc',['--storage','original'])]
out=Path(__file__).resolve().parent
records=[]
for variant,args in jobs:
    print(variant,'starting',flush=True)
    log=out/(variant+'-export.log')
    with open_text(log,'w') as f:
        r=subprocess.run([sys.executable,str(P/'export_candidate.py')]+args,stdout=f,stderr=subprocess.STDOUT,env=child_env())
    record=dict(variant=variant,exit_code=r.returncode,log=log.name)
    if r.returncode==0:
        m=P/'out'/variant/'manifest.json'
        record['manifest_sha256']=hashlib.sha256(m.read_bytes()).hexdigest()
    records.append(record)
    write_text(out/'export-run.json',json.dumps(dict(physical_qualified=False,published=False,checks=records),indent=2)+'\n')
    print(json.dumps(record),flush=True)
    if r.returncode:raise SystemExit(r.returncode)
