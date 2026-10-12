"""Run source-bound review checks serially. Failures are preserved, never waived.
Run this script through ../run_locked.py after selecting/exporting the candidate.
"""
from cv_io import child_env, open_text, rel_posix, write_text
from pathlib import Path
import subprocess,sys,json,hashlib,time,shutil
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';M=D/'manifest.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runner_sha=digest(Path(__file__));h=digest(M);snap=P/'routing-snapshots/hdmi-export17-selected-20261009-0704';logs=D/'check-logs';logs.mkdir(exist_ok=True)
commands=[
 ('bound_files',[P/'export_cache.py','status','--variant','compact-kowa_lm6hc','--no-guide']),  # FP-03: every manifest-bound file present and byte-identical (exit 3 = git-ignored mesh cache missing)
 ('mesh',[P/'verify_print_meshes.py']),
 ('print',[P/'verify_print_checks.py']),
 ('build_order_docs',[P/'tests/test_build_order_docs.py']),  # FP-06: ASSEMBLY/guide/FPS text vs steps.py order, r7 lens_turn_back_lint, refits, no spanner
 ('csi',[P/'verify_csi_source.py']),
 ('power_rigid',[P/'verify_power_service.py']),
 ('power_static',[P/'verify_wire_solids.py','--snapshot',P/'routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json']),
 ('hdmi',[P/'verify_hdmi.py','--snapshot',snap/'input.json','--step','2']),
 ('fps',[P/'verify_fps_integrated.py']),
 ('harness',[P/'verify_harness_checks.py']),  # FP-10: cable_routes, mate_reach, lead_access/pigtail_drop, cable_stow, header_housings, signal-route bindings
 ('usb_head',[P/'verify_shadow_usb_head.py','--mechanical-manifest',M,'--expected-sha',h,'--report-name','shadow-plenum-head-checks.json']),
 ('rigid',[P/'verify_candidate.py']),
 ('microsd_rejected_closed_path',[P/'verify_microsd_service.py']),
 ('check_scope',[P/'verify_check_scope.py']),  # FP-12: VN-33 J4 per variant, VN-37 area parity, VN-36 flow network, VN-35 HDMI face, VN-34 evf_restraint/face, VN-38 stack_retention/posts
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
 with open_text(log,'w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=child_env())
 results.append(dict(check=label,command=[rel_posix(x,P) if isinstance(x,Path) and x.is_relative_to(P) else str(x) for x in args],exit_code=r.returncode,log=rel_posix(log,D),started_utc=started,completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
 write_text(D/'review-check-run.json',json.dumps(dict(manifest_sha256=h,runner_sha256=runner_sha,checks=results,physical_qualified=False),indent=2))
 print(label,'exit',r.returncode,flush=True)
assert digest(M)==h and digest(Path(__file__))==runner_sha
raise SystemExit(0 if all(r['exit_code']==0 for r in results) else 1)
