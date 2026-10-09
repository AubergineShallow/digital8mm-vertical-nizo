"""Bind completed scoped reports without rerunning or relabeling CAD results."""
from pathlib import Path
import hashlib,json,time
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';M=D/'manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
m=read(M);mh=sha(M)
for rel,h in m['sources'].items():assert sha(P.parent/rel)==h,('Source mismatch',rel)
for rel,h in m['files'].items():assert sha(D/rel)==h,('Export mismatch',rel)
cases=[
 ('rigid','out/compact-kowa_lm6hc/verification.json','verify_candidate.py','verification_source_sha256','manifest_sha256'),
 ('mesh','out/compact-kowa_lm6hc/print-mesh-checks.json','verify_print_meshes.py','verification_source_sha256','manifest_sha256'),
 ('csi','out/compact-kowa_lm6hc/csi-source-tool-checks.json','verify_csi_source.py','verification_source_sha256','mechanical_manifest_sha256'),
 ('power_rigid','out/compact-kowa_lm6hc/power-service-checks.json','verify_power_service.py','source_sha256','manifest_sha256'),
 ('power_static','out/compact-kowa_lm6hc/wire-solid-checks.json','verify_wire_solids.py','verification_source_sha256','manifest_sha256'),
 ('hdmi','out/compact-kowa_lm6hc/hdmi-solid-checks.json','verify_hdmi.py','verification_source_sha256','mechanical_manifest_sha256'),
 ('fps','out/fps-service-study/integrated-fps-checks.json','verify_fps_integrated.py','source_sha256','mechanical_manifest_sha256'),
 ('usb_head','routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json','verify_shadow_usb_head.py','verification_source_sha256','mechanical.manifest_sha256'),
 ('plenum','out/compact-kowa_lm6hc/shadow-plenum-checks.json','verify_shadow_plenum.py','verification_source_sha256','manifest_sha256'),
 ('exterior_mouths','out/compact-kowa_lm6hc/shadow-outlet-context-checks.json','verify_shadow_outlet_context.py','verification_source_sha256','manifest_sha256'),
 ('microSD_rejected_closed_path','out/compact-kowa_lm6hc/microsd-service-dependency.json','verify_microsd_service.py','verification_source_sha256','manifest_sha256'),
 ('void','out/comparison/volume-compact-kowa_lm6hc.json','measure_volume.py','verification_source_sha256','manifest_sha256')]
rows=[]
for label,path,verifier,source_key,manifest_key in cases:
 f=P/path;j=read(f);v=j
 for k in manifest_key.split('.'):v=v[k]
 assert v==mh,('Different mechanical snapshot',label)
 assert j[source_key]==sha(P/verifier),('Different verifier',label)
 rows.append(dict(check=label,report=path,report_sha256=sha(f),verification_source=verifier,verification_source_sha256=j[source_key],status=j.get('status',j.get('closed_panel_case',j.get('operational_status'))),summary=j.get('summary'),physical_qualified=False))
# Check sampled geometry and helper inputs, not only each top-level verifier.
input_bindings=[(D/'hdmi-solid-checks.json','snapshot_sha256',P/'routing-snapshots/hdmi-export17-selected-20261009-0704/input.json'),(D/'power-service-checks.json','snapshot_sha256',P/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'),(D/'wire-solid-checks.json','snapshot_sha256',P/'routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json'),(P/'out/fps-service-study/integrated-fps-checks.json','input_sha256',P/'out/fps-service-study/mated-carry-input.json')]
for report,key,path in input_bindings:assert read(report)[key]==sha(path),('Input mismatch',str(path))
for rel,h in read(P/cases[7][1])['verification_dependency_sha256'].items():assert sha(P/rel)==h,('Head dependency mismatch',rel)
for rel,h in read(P/'out/fps-service-study/integrated-fps-checks.json')['verification_dependency_sha256'].items():assert sha(P/rel)==h,('FPS dependency mismatch',rel)
rigid=read(D/'verification.json');fails=[q for q in rigid['checks'] if q['status']=='fail']
assert len(fails)==1 and fails[0]['id']=='pi5/cooler',('New active rigid fault',fails)
for path in ['power-service-checks.json','wire-solid-checks.json']:assert read(D/path)['status']=='pass'
assert read(D/'print-mesh-checks.json')['fail_count']==0
assert read(D/'hdmi-solid-checks.json')['summary']['fail']==0
assert read(P/'out/fps-service-study/integrated-fps-checks.json')['status']=='geometric_pass_only'
assert read(P/cases[7][1])['status']=='pass_for_bounded_head_reservation'
assert read(D/'shadow-plenum-checks.json')['summary']['fail']==0
assert read(D/'shadow-outlet-context-checks.json')['summary']['fail']==0
assert read(D/'csi-source-tool-checks.json')['declared_rigid_reservation_clear']
result=dict(mechanical_manifest_sha256=mh,reconciler_sha256=sha(Path(__file__)),generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_and_export_hashes_verified=True,reports=rows,active_rigid_failures=fails,
 verdict='Review candidate only. Not fabrication, energization or complete-service release.',
 physical_qualified=False,open_inherited_gates=56,M1='open',
 prominent_holds=['Front-mouth frame is absent inZ5..40; first roof paths may require about35mm bridging. Slicer/expanded coupon and full-body cleanout are unqualified.',
 'Cooler/source overlap79.902671mm3 remains unresolved; measured cooler registration and real thermal tests are required.',
 'Exterior bay connectivity is not a sealed main-cavity cooler duct or a fan-flow/cooling result. Hand/strap/stand blockage requires separate tests.',
 'Complete camera FPC, USB-feed wire roots/stow and combined flexible service remain unresolved.'],
 historical_attempt='history/shadow-first-check-run/review-check-run.json preserves the initial USB-head dependency failure. The separately executed current whole-assembly checker replaces missing standalone support extracts with mandatory integrated-tub coverage and canonical helper hashes; it does not invent a USB service path.')
(D/'current-review-evidence.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(manifest=mh,reports=len(rows),active_rigid_failures=len(fails),physical_qualified=False)))
