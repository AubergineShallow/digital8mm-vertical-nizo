"""Freeze a new USB-port-corrected input while preserving accepted HDMI material."""
from pathlib import Path
import copy,hashlib,json,shutil
P=Path(__file__).resolve().parent
OLD=P/'routing-snapshots/hdmi-ck1044-clear-20261009-0524'
NEW=P/'routing-snapshots/hdmi-corrected-ports-20261009-0623'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD/'input.json')=='7c02b81255cbc9806e8ab6ada9cd24860ef3cd383882ea2c12afd94e772cabbb'
bound=json.loads((OLD/'official-pi5-geometry-checks-v2.json').read_text())
for name,h in bound['source_sha256'].items():assert sha(P/name)==h,name
old=json.loads((OLD/'input.json').read_text());new=copy.deepcopy(old)
reservation=bound['usb2_upper_head'];head=next(c for c in new['connectors'] if c['id']=='p_usb_pi')
previous=copy.deepcopy(head)
head.clear();head.update(id='p_usb_pi',cable='usb_5v',end='pi5',rigid=True,
    box=reservation['box'],head=reservation['box'],port_center=reservation['port_face_centre'],
    why='Upper receptacle of the actual GPIO-side USB2 stack, the lower candidate Z row',
    note='Whole original31x15.5x9.8mm exterior head/bend allowance preserved and source aligned. Actual housing/strain-relief split, inserted length and exit are unmeasured.',
    source='Official Pi5 RP-010083-CA-1 source window and front face; official_pi5_geometry.usb2_upper_head_reservation()',
    source_reservation=reservation,wire_exit=None,wire_exit_direction=None,
    cable_route_status='BLOCKED: received overmold and wire-exit datum required before a new complete200mm5V route and staging can be modeled',
    qualification='Source-aligned exterior reservation only; not measured mating geometry',physical_qualified=False)
new['revision']=str(old['revision'])+'; isolated corrected USB2 port input20261009-0623'
new['provenance']=dict(status='Corrected-port integration candidate; geometry and physical gates explicitly retained',
    previous_input_sha256=sha(OLD/'input.json'),official_geometry_report_sha256=sha(OLD/'official-pi5-geometry-checks-v2.json'),
    previous_study_provenance=old['provenance'],changed_connectors=['p_usb_pi'],
    frozen_hdmi_shapes_unchanged=True,selected_hdmi_poses=['installed','premate'],
    rejected_archived_diagnostic=['both_unplugged: Pi-head+Z6 conflicts with fixed power; not required by selected service'],
    service_sequence='EVF head unplugged first; Pi head remains mated. Complete ribbon, Pi/carrier, FPS switch and both complete mated FPS branches translate together. Other endpoints/looms require explicit staging.',
    mechanical_manifest_sha256=None,mechanical_binding_status='Final report will bind the new parent export; no old mechanical pass transferred',
    usb_5v_full_route_status=head['cable_route_status'],hdmi_adapter_registration_hold=bound['hdmi_socket_datum'],
    selected=True,physical_qualified=False)
NEW.mkdir(parents=True,exist_ok=False)
for key in ('hdmi_installed','hdmi_premate','hdmi_both_unplugged'):
    assert new[key]==old[key]
    assert abs(new[key]['routed_length_mm']-300)<1e-8
(NEW/'input.json').write_text(json.dumps(new,indent=2))
(NEW/'rejected-previous-usb-head.json').write_text(json.dumps(previous,indent=2))
(NEW/'usb2-head-reservation.json').write_text(json.dumps(reservation,indent=2))
(NEW/'source-create_corrected_port_hdmi_snapshot.py').write_bytes(Path(__file__).read_bytes())
for name in ('source-verify_fps_access.py','source-verify_hdmi.py','source-official_pi5_geometry.py','source-official_pi5_csi.py'):
    shutil.copyfile(OLD/name,NEW/name)
record=dict(previous_input_sha256=sha(OLD/'input.json'),new_input_sha256=sha(NEW/'input.json'),
    head_reservation_sha256=sha(NEW/'usb2-head-reservation.json'),
    unchanged_hdmi={key:dict(exact_object_equality=True,routed_length_mm=new[key]['routed_length_mm'],
        canonical_shape_sha256=hashlib.sha256(json.dumps(new[key],sort_keys=True,separators=(',',':')).encode()).hexdigest())
        for key in ('hdmi_installed','hdmi_premate','hdmi_both_unplugged')},
    physical_qualified=False,mechanical_binding='pending new parent manifest')
(NEW/'creation-checks.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
