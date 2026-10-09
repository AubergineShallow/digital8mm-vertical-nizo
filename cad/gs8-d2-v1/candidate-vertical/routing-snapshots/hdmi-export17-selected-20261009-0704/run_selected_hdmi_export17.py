"""Bind and preserve the parent's selected-only HDMI check for export17."""
from pathlib import Path
import hashlib,json,runpy,sys
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
MP=ROOT/'out/compact-kowa_lm6hc/manifest.json'
EXPECTED_MANIFEST='ed58af4220b6afebf3bf1d88d61a9f786f21fd717f74791387b613e62366be4b'
EXPECTED_SOURCE='8d842217a75aa1b3ba3b3fabbbf3c5be785e56c637ad3becc2096a836e1fa556'
EXPECTED_INPUT='cf6b20f21e342414dbf001fe9a4d84ad9634fa2b93e81118b112cac4eaec6f88'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(MP)==EXPECTED_MANIFEST,'Different mechanical export'
assert digest(ROOT/'verify_hdmi.py')==EXPECTED_SOURCE,'Different verifier'
assert digest(P/'input.json')==EXPECTED_INPUT,'Changed geometry input'
dst=P/'export17-selected-hdmi-checks.json'
if dst.exists():raise ValueError('Do not overwrite an existing named result')
sys.argv=[str(ROOT/'verify_hdmi.py'),'--variant','compact-kowa_lm6hc','--snapshot',str(P/'input.json'),'--step','2']
code=0
try:runpy.run_path(str(ROOT/'verify_hdmi.py'),run_name='__main__')
except SystemExit as e:code=e.code or 0
assert digest(MP)==EXPECTED_MANIFEST and digest(ROOT/'verify_hdmi.py')==EXPECTED_SOURCE
src=MP.parent/'hdmi-solid-checks.json';result=json.loads(src.read_text())
assert result['snapshot_sha256']==EXPECTED_INPUT and result['mechanical_manifest_sha256']==EXPECTED_MANIFEST
assert result['verification_source_sha256']==EXPECTED_SOURCE and not result['includes_rejected_diagnostics']
dst.write_bytes(src.read_bytes())
receipt=dict(selected_report_sha256=digest(dst),geometry_input_sha256=EXPECTED_INPUT,mechanical_manifest_sha256=EXPECTED_MANIFEST,
 verification_source_sha256=EXPECTED_SOURCE,donor_addendum_sha256=digest(P/'usb-donor-provenance.json'),
 exit_code=code,physical_qualified=False,scope='Selected installed/Pi-mated EVF-free geometry only. Full USB donor cuts/lead/junction placement, adapter registration, complete FPC, cooler/latch/tool and whole-loom staging remain explicit gates.')
(P/'export17-selected-hdmi-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
raise SystemExit(code)
