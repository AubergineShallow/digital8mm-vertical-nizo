"""Isolated source-derived Pi 5 feature correction and USB head reservation.

No existing model or frozen route is changed. Port envelopes include their
source voids; they are conservative reservations, not connector mating solids.
Both complete CSI assemblies are available through official_pi5_csi.exact_parts.
Redistributed manufacturer extracts retain official-fpc-sources/LICENSE.txt.
"""
from pathlib import Path
import hashlib,itertools,json
import cadquery as cq
import official_pi5_csi as C

SOURCE=C.SOURCE
USB2_UPPER_NATIVE_CENTRE=[87.779999264573,46.999680556192,13.92600076744]
USB2_LOWER_NATIVE_CENTRE=[87.779999264573,46.999680556192,5.346000767444]
USB3_UPPER_NATIVE_CENTRE=[88.0000001,29.000105,13.965999995665]
# Current storage centre is candidateY=-9.9,Z34; retain nominal underside datum.
STORAGE_DY=-0.365999995665
STORAGE_DZ=-0.000105
HDMI0_SOCKET_WINDOW_CENTRE_NATIVE=[25.8,-1.0,2.8855]
HDMI0_SOCKET_OUTER_LIP_NATIVE_Y=-1.6303501

def source_features():
    ports=json.loads((SOURCE/'port-landmarks.json').read_text())
    extracted=json.loads((SOURCE/'connector-extraction.json').read_text())
    if ports['source_step_sha256']!=C.OFFICIAL_STEP_SHA256:raise ValueError('Unexpected board source')
    if extracted['max_main_hole_residual_mm']>1e-6:raise ValueError('Unregistered board source')
    out={name:dict(native_bbox_mm=row['bbox_native_mm'],source='port-landmarks.json',
                  source_solid_indices=row['source_solid_indices'],source_file_sha256=row['sha256'])
         for name,row in ports['objects'].items()}
    for name,index in [('hdmi0',1937),('hdmi1',1926)]:
        row=extracted['leaves'][index]
        assert row['i']==index and row['type']=='Shell'
        out[name]=dict(native_bbox_mm=row['bbox_mm'],source='connector-extraction.json',
            source_leaf_index=index,source_shape_type='Shell',
            note='Whole connector shell bounds enclose the ten associated free-shell contact fragments; source has no closed HDMI solid')
    for name,row in extracted['components'].items():
        out[name]=dict(native_bbox_mm=row['native_bbox_mm'],source='connector-extraction.json',
            source_solid_indices=row['source_solid_indices'],source_file_sha256=row['source_sha256'])
    return out

def candidate_bounds(native_bbox,bracket=False,stack_y=22.2):
    pts=[]
    for p in itertools.product(*[native_bbox[i:i+2] for i in (0,2,4)]):
        if bracket:
            pts.extend([C.native_to_candidate_point(p,.03,18.5,stack_y),C.native_to_candidate_point(p,1.306,20.1,stack_y)])
        else:pts.append(C.native_to_candidate_point(p,stack_y=stack_y))
    return {a:[min(p[i] for p in pts),max(p[i] for p in pts)] for i,a in enumerate('xyz')}

def feature_envelopes(bracket=False,stack_y=22.2):
    out={}
    for name,row in source_features().items():
        b=candidate_bounds(row['native_bbox_mm'],bracket,stack_y)
        out[name]=dict(**row,box=b,kind='source-derived conservative whole-component envelope',
            shape=cq.Solid.makeBox(*[b[a][1]-b[a][0] for a in 'xyz'],cq.Vector(*[b[a][0] for a in 'xyz'])))
    return out

def exact_port_parts(names=('usb2','usb3','ethernet','gpio','usbc'),stack_y=22.2):
    """Source solids retain their real cavities and contacts; no plug cut-outs.

    A coarse solid plug reservation may intersect these detailed mating contacts.
    Such a result is a mating-envelope limitation, not permission to remove the
    source contacts or globally exempt that connector from collision checks.
    """
    rows=json.loads((SOURCE/'port-landmarks.json').read_text())['objects'];out={}
    for name in names:
        path=SOURCE/(name+'-native.step')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=rows[name]['sha256']:raise ValueError('Changed official port extract:'+name)
        out[name]=C.place(cq.importers.importStep(str(path)).val(),stack_y=stack_y)
    return out

def usb2_upper_head_reservation(bracket=False,stack_y=22.2):
    """Retain inherited31x15.5x9.8mm exterior allowance, align to actual upper USB2.

    Front-face and transverse centre are source geometry. Plug housing, inserted
    metal length, actual cable exit, strain relief and tolerances remain unmeasured.
    The whole allowance lies outside the source front face, so it is not a
    connector mating proof. A separate rooted lead must be modeled.
    """
    centre=C.native_to_candidate_point(USB2_UPPER_NATIVE_CENTRE,stack_y=stack_y)
    x,y,z=centre
    b=dict(x=[x-31,x],y=[y-4.9,y+4.9],z=[z-7.75,z+7.75])
    if bracket:b['y']=[b['y'][0]-.294,b['y'][1]+.03]
    return dict(box=b,port_face_centre=centre,port_identity='GPIO-side USB2 stack, upper receptacle away from PCB',
        full_original_allowance_mm=[31,15.5,9.8],native_face_centre=USB2_UPPER_NATIVE_CENTRE,
        mating_axis_candidate=[1,0,0],unplug_direction_candidate=[-1,0,0],
        bracket_scope='Explicit native substrate-bottom/top registration bracket; does not move the kit datum' if bracket else 'Nominal native Z0 to local underside18.5',
        cable_exit=None,physical_qualified=False,
        remaining=['Unknown received USB head shape and engagement','Separate full200mm 5V lead/stow geometry','Lateral departure required before crossing storage height','All staged motions need refreshed whole-loom checks'])

def cooler_mount_axes():
    return [dict(native_xy=p,candidate_xz=[-34-p[0],63-p[1]],pcb_hole_diameter_mm=3.1,
        meaning='Actual board hole axis only; push-pin profile and cooler fan/perimeter location are not dimensioned')
        for p in ([3.5,9.5],[61.5,46.5])]

def candidate_pcb(stack_y=22.2):
    """Keep the inherited1.6mm kit datum; include four kit and two cooler holes.

    This is a rectangular PCB proxy with source-verified hole axes, not an
    import of every official copper layer or the received board thickness.
    """
    y0,y1=stack_y-20.1,stack_y-18.5
    board=cq.Solid.makeBox(85,y1-y0,56,cq.Vector(-119,y0,7))
    holes=[(x,y,1.35) for x in (3.5,61.5) for y in (3.5,52.5)]
    holes.extend((x,y,1.55) for x,y in ([3.5,9.5],[61.5,46.5]))
    for x,y,r in holes:
        cutter=cq.Solid.makeCylinder(r,y1-y0+2,cq.Vector(-34-x,y0-1,63-y),cq.Vector(0,1,0))
        board=board.cut(cutter)
    return board

def csi_latch_bounds(bracket=False,stack_y=22.2):
    out={}
    for name,index,x0,x1 in [('cam_disp0',1262,53.305,56.305),('cam_disp1',1310,47.105,50.105)]:
        b=[x0,x1,.145,16.845,1.636,5.286]
        out[name]=dict(original_source_solid_index=index,native_bbox_mm=b,
            box=candidate_bounds(b,bracket,stack_y),state='Single static closed source pose',
            operation='Qualitative pull-out then tilt away in manufacturer installation instructions; no quantified stroke, pivot or tool corridor')
    return out

def hdmi_socket_datum():
    return dict(native_window_section_y_mm=-1.0,native_window_z_mm=[1.7355,4.0355],
        window_centre_candidate=C.native_to_candidate_point(HDMI0_SOCKET_WINDOW_CENTRE_NATIVE),
        outer_lip_candidate_z_mm=63-HDMI0_SOCKET_OUTER_LIP_NATIVE_Y,
        inherited_inferred_adapter_port_y_mm=.35,nominal_socket_delta_y_mm=.4645,
        source='official-fpc-sources/hdmi-mouth-inspection.json',
        limitation='Official socket geometry does not define the Adafruit3557 body/ribbon-exit offset from its inserted plug. Existing300mm route proof is conditional on its frozen adapter pose. No silent route translation or mating approval is made.')

def provenance():
    return dict(**C.provenance(),landmark_scope='Four-hole registered port envelopes, both CSI assemblies, actual cooler board holes and an exterior upper USB2 head reservation',
        nominal_matrix=[[-1,0,0,-34],[0,0,-1,3.7],[0,-1,0,63],[0,0,0,1]],
        cooler_hold='Official RP-008187 drawing does not dimension fan-to-pin offsets or complete outline. Retain32.3614mm3 CSI/coarse-cooler conflicts until received-part geometry is registered.',
        changed_claims=['Inherited RJ45 and USB2 rows were reversed','Inherited second HDMI had the wrong sign of its spacing','Old CSI proxy had only one short connector and an unsupported departure direction','Four cooler feet were estimated; actual board has two cooler mounting holes'])
