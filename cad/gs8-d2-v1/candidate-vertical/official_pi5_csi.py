"""Isolated official Pi5 CSI correction; not installed in model.py.

The two complete connector assemblies are extracted unchanged from the official
RP-010083-CA-1 STEP. Component identity comes from manufacturer silkscreen, not
an invented connector SKU. Preserve the manufacturer's LICENSE.txt with copies.
Bare connector geometry does not define the cable stiffener or latch travel.
"""
from cv_io import read_text
from pathlib import Path
import hashlib,json,itertools
import cadquery as cq

SOURCE=Path(__file__).resolve().parent/'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources'
OFFICIAL_STEP_SHA256='78164070c1cc7ab854382950d2e85926c6e35432f1e5a146b733397a7c6afb44'
SOURCE_URL='https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-010083-CA-1-rpi-5%203D%20STEP%20-%20No%20Graphics%20small%20file.zip'
IDENTITY_URL='https://www.raspberrypi.com/app/uploads/2023/09/58f150c0-bd72-4e42-a77f-6be0890c8a80-1024x685.png'

def native_to_candidate_point(p,native_board_z=0,local_board_z=18.5,stack_y=22.2):
    """85x56 board, four-hole/edge registration; no scale or stack movement.

    Native X0 is the button end, X85 the USB edge, Y56 the GPIO edge.
    Local PI x1=-6, y1=23.7. Candidate roll adds X-28 and Z+39.3.
    Default native board datum Z0 maps to the original underside datum18.5.
    """
    x,y,z=p
    return [-34-x,stack_y-local_board_z+native_board_z-z,63-y]

def place(shape,native_board_z=0,local_board_z=18.5,stack_y=22.2):
    return (shape.rotate((0,0,0),(0,0,1),180)
                 .rotate((0,0,0),(1,0,0),90)
                 .translate(cq.Vector(-34,stack_y-local_board_z+native_board_z,63)))

def load_native():
    meta=json.loads(read_text(SOURCE/'connector-extraction.json'))
    if meta['source_step_sha256']!=OFFICIAL_STEP_SHA256:raise ValueError('Unexpected official STEP')
    if meta['max_main_hole_residual_mm']>1e-6:raise ValueError('Official board registration did not match source holes')
    out={}
    for name,row in meta['components'].items():
        src=SOURCE/(name+'-native.step')
        if hashlib.sha256(src.read_bytes()).hexdigest()!=row['source_sha256']:raise ValueError('Changed extracted connector:'+name)
        out[name]=cq.importers.importStep(str(src)).val()
    return out

def exact_parts(native_board_z=0,local_board_z=18.5,stack_y=22.2):
    return {name:place(s,native_board_z,local_board_z,stack_y) for name,s in load_native().items()}

def conservative_envelopes(stack_y=22.2):
    """Conservative boxes spanning the registered source thickness ambiguity.

    Envelope bracket uses substrate-bottom0.03 -> local underside18.5 and
    substrate-top1.306 -> local top20.1. Native whole-board bottom0 and mating
    pads1.336 registrations lie within this wider0.324mm bracket. This changes
    connector reservation only, never the stack/pogo/standoff datum.
    """
    meta=json.loads(read_text(SOURCE/'connector-extraction.json'));out={}
    for name,row in meta['components'].items():
        b=row['native_bbox_mm'];pts=[]
        for point in itertools.product(*[b[i:i+2] for i in (0,2,4)]):
            pts.extend([native_to_candidate_point(point,.03,18.5,stack_y),
                        native_to_candidate_point(point,1.306,20.1,stack_y)])
        box={ax:[min(p[j] for p in pts),max(p[j] for p in pts)] for j,ax in enumerate('xyz')}
        out[name]=dict(box=box,source='Official complete48-solid connector assembly and stated thickness-registration bracket',
            kind='source-derived conservative envelope, not actual material or measured tolerance',
            shape=cq.Solid.makeBox(*[box[a][1]-box[a][0] for a in 'xyz'],cq.Vector(*[box[a][0] for a in 'xyz'])))
    return out

def provenance():
    return dict(source_url=SOURCE_URL,source_sha256=OFFICIAL_STEP_SHA256,identity_url=IDENTITY_URL,
        identity={'cam_disp0':'J3, nativeX55.205, Ethernet-side','cam_disp1':'J4, nativeX49.005, HDMI-side'},
        nominal_native_exit_direction=[0,0,1],nominal_candidate_exit_direction=[0,-1,0],
        nominal_native_width_direction=[0,1,0],nominal_candidate_width_direction=[0,0,-1],
        direction_scope='Directions follow the vertical opening/contact arrangement of the bare source connector. Actual fully inserted cable free-flex station/contact-side normal remains unassigned.',
        latch_scope='Official installation instructions prescribe gently pulling the flap out, then tilting away from the opening. The STEP has only one static pose; travel and open-latch swept volume are not dimensioned.',
        physical_qualified=False,selected_cable_width_reservation_mm=16,
        remaining=['Source model is guidance only, may differ from received hardware','No guessed connector SKU','Cable engagement/stiffener/transition and contact clocking','Latch travel/tool jaws','Physical fit and laminate capability'])
