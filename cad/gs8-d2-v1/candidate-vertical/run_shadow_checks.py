"""Run source-bound review checks serially. Failures are preserved, never waived.
Run this script through ../run_locked.py after selecting/exporting the candidate.
"""
from pathlib import Path
import subprocess,sys,json,hashlib,time,shutil
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';M=D/'manifest.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runner_sha=digest(Path(__file__));h=digest(M);snap=P/'routing-snapshots/hdmi-export17-selected-20261009-0704';logs=D/'check-logs';logs.mkdir(exist_ok=True)
commands=[
 ('mesh',[P/'verify_print_meshes.py']),
 ('csi',[P/'verify_csi_source.py']),
 ('power_rigid',[P/'verify_power_service.py']),
 ('power_static',[P/'verify_wire_solids.py','--snapshot',P/'routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json']),
 ('hdmi',[P/'verify_hdmi.py','--snapshot',snap/'input.json','--step','2']),
 ('fps',[P/'verify_fps_integrated.py']),
 ('usb_head',[P/'verify_shadow_usb_head.py','--mechanical-manifest',M,'--expected-sha',h,'--report-name','shadow-plenum-head-checks.json']),
 ('rigid',[P/'verify_candidate.py']),
 ('microsd_rejected_closed_path',[P/'verify_microsd_service.py']),
 ('void',[P/'measure_volume.py'])]
results=[]
for label,args in commands:
 assert digest(M)==h,'Mechanical manifest changed during checks'
 if label=='usb_head':
  previous=snap/'shadow-plenum-head-checks.json'
  if previous.exists():
   archive=P/'history/head-checks';archive.mkdir(parents=True,exist_ok=True)
   shutil.move(str(previous),str(archive/(digest(previous)+'.json')))
 log=logs/f'{label}.log';cmd=[sys.executable]+[str(x) for x in args]
 started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());print(label,'starting',started,flush=True)
 with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(check=label,command=[str(x.relative_to(P)) if isinstance(x,Path) and x.is_relative_to(P) else str(x) for x in args],exit_code=r.returncode,log=str(log.relative_to(D)),started_utc=started,completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
 (D/'review-check-run.json').write_text(json.dumps(dict(manifest_sha256=h,runner_sha256=runner_sha,checks=results,physical_qualified=False),indent=2))
 print(label,'exit',r.returncode,flush=True)
assert digest(M)==h and digest(Path(__file__))==runner_sha
