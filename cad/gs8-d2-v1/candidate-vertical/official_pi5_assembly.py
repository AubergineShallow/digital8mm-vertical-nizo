"""Compose corrected source features without deleting mating contacts.

Named parts define occupied space by set union. A compound is only an assembly
container: its summed Volume is not the occupied union volume. Use occupied_union
for a validated Boolean union, or intersect each named solid for collision
existence and label pairwise witness volumes explicitly.
"""
from pathlib import Path
import hashlib
import cadquery as cq
import official_pi5_geometry as G
import official_pi5_csi as C

def legacy_proxy_parts(L,stack_y=22.2):
    """Retain only the explicitly approximate underside, SoC and button bodies."""
    x0,x1=L.PI['x'];y0,y1=L.PI['y'];f=L.COTS['pi5']['features']
    boxes={
        'legacy_underside_proxy':[x0+6.5,x1-6.5,y0+6.5,y1-6.5,16.,18.5],
        'legacy_soc_proxy':[x1-45.,x1-28.,y0+20.,y0+37.,20.1,21.4],
        'legacy_button_proxy':[x1-2.5,f['button']['x_face'],f['button']['y']-1.5,f['button']['y']+1.5,20.1,22.4],
    }
    out={}
    for name,b in boxes.items():
        s=cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],cq.Vector(b[0],b[2],b[4]))
        out[name]=s.rotate((0,0,0),(1,0,0),90).translate(cq.Vector(-28,stack_y,39.3))
    return out

def build_parts(L,stack_y=22.2,port_parts=None,csi_parts=None):
    """Reuse already imported candidate-coordinate parts when supplied.

    This is the corrected selected-feature proxy, not all electronic components
    from the full official board. Supplied parts must use the same nominal
    underside registration. No source solid or contact receives a plug cut.
    """
    ports=G.exact_port_parts(stack_y=stack_y) if port_parts is None else port_parts
    csi=C.exact_parts(stack_y=stack_y) if csi_parts is None else csi_parts
    if set(ports)!={'usb2','usb3','ethernet','gpio','usbc'}:raise ValueError('Need all five corrected port sets')
    if set(csi)!={'cam_disp0','cam_disp1'}:raise ValueError('Need both CSI assemblies')
    out={'kit_datum_pcb':G.candidate_pcb(stack_y)}
    out.update(ports);out.update(csi)
    envelopes=G.feature_envelopes(stack_y=stack_y)
    for name in ('hdmi0','hdmi1'):out[name+'_source_shell_envelope']=envelopes[name]['shape']
    out.update(legacy_proxy_parts(L,stack_y))
    for name,shape in out.items():
        if not shape.isValid() or not shape.Solids():raise ValueError('Invalid or non-solid part:'+name)
    return out

def as_assembly_compound(parts):
    """Visualization/container only; Volume may double-count internal overlap."""
    return cq.Compound.makeCompound(list(parts.values()))

def occupied_union(parts):
    """Historical Boolean-union experiment. NOT used for current exports: the pinned
    kernel discarded CSI contacts despite shape validity. Retained for diagnosis only.

    A failure is explicit. Never silently fall back to a compound and label its
    Volume as occupied volume. Disconnected solids are permitted after union.
    """
    values=list(parts.values())
    if not values:raise ValueError('Empty corrected Pi')
    shape=values[0].fuse(*values[1:])
    if not shape.isValid() or not shape.Solids():raise RuntimeError('Corrected Pi occupied union failed validation')
    return shape

def metadata():
    root=Path(__file__).resolve().parent
    return dict(source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
        for name in ('official_pi5_assembly.py','official_pi5_geometry.py','official_pi5_csi.py')},
        occupied_space='Named closed source components retained in overlapping assembly; raw compound volume is not occupied volume. Core void must subtract components as a union without summing their volumes',
        proxies=['Inherited kit1.6mm PCB thickness','Underside electronics','SoC body','Power button body','Closed envelopes of non-solid source HDMI shells'],
        preserved_mating_contacts=True,artificial_plug_subtractions=False,physical_qualified=False,
        remaining=['Detailed plug/source contacts require actual mating geometry; coarse plug boxes are only reservations','Adapter mating/root registration','Cooler/source CSI conflict','Full200mm FPC and both real cable roots','All baseline56 and M1 physical gates'])
