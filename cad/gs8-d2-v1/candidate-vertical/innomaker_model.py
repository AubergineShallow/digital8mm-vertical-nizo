"""Innomaker build of the shared candidate model, applied without editing model.py.

model.py stays byte-identical to the official branch, so the three official variant manifests keep their
source binding and export_candidate.py still builds the official Raspberry Pi GS camera layout unchanged.
This module applies the Innomaker delta from the delivered fork (d319a35) to model.py's text at import
time and registers the result as the module 'model' for the current process only. Every replacement must
match exactly once; if the official model.py changes in a patched region the import fails closed and the
delta must be reviewed again (never loosen the match).

Only export_innomaker.py imports this module. It refuses to run if the official model was already imported
in the same process, so one process never mixes the two camera builds.
"""
import hashlib
import sys
import types
from pathlib import Path

from cv_io import read_text

BASE = Path(__file__).resolve().parent
OFFICIAL = BASE / 'model.py'
CAMERA = 'innomaker'
# Exact text of the delivered fork's model.py (d319a35) after the delta; the delta is checked against it.
DELIVERED_MODEL_SHA256 = 'aef924da316b89b60e59d60361d834441b450f91db16320cc28e592bbdef0fb7'

PATCHES = [
    ('import vent_geometry as VG\nsys.path.insert(0,str(Path(__file__).resolve().parent / "structural-review"))\n',
     'import vent_geometry as VG\nimport innomaker_geometry as IG\nsys.path.insert(0,str(Path(__file__).resolve().parent / "structural-review"))\n'),
    ("V=cq.Vector\nREV='D2-V1 vertical-board shadow-plenum corrective candidate, 2026-10-12'\nSTACK_DX=-28.0\n",
     "V=cq.Vector\nREV='D2 Innomaker header-aware conditional reconstruction, 2026-10-13'\nSTACK_DX=-28.0\n"),
    ("    f=-length;adds=[];cuts=[]\n    # (1) -Y tine\n    tc={b['kind']:b for b in L.tab_catch_boxes() if b['side']==-1}\n    web,fl=tc['web'],tc['flange'];z0,zt=web['z'][0],98.0\n    adds.append(box(fl['x'][0],fl['x'][1],-25.55,fl['y'][0]+.01,z0,zt))\n    wy=fl['y'][0]+(web['x'][1]-fl['x'][1])*rise\n    pts=[(fl['x'][1]-.01,fl['y'][0]),(web['x'][1],wy),(web['x'][1],web['y'][0]+.01),(fl['x'][1]-.01,web['y'][0]+.01)]\n    w=cq.Wire.makePolygon([V(x,y,z0) for x,y in pts]+[V(pts[0][0],pts[0][1],z0)])\n    adds.append(cq.Solid.extrudeLinear(w,[],V(0,0,zt-z0)))\n    # (2) LL collar insert boss cone (lower half)\n",
     '    f=-length;adds=[];cuts=[]\n    # Innomaker has no BFAR lock-tab tine/corbel.\n    # (2) LL collar insert boss cone (lower half)\n'),
    ("    for b in L.FLOOR_HOLES.values():cuts.append(dc.box_solid(dict(b,z=(-.1,2.6))))\n    # Camera floating rear catch remains on removable panel; front datum and counterbore unchanged.\n    cuts.extend([cyl('x',16.2,-3.9,-2.69,0,60),cyl('x',18.75,-5.3,-3.9,0,60),\n                 cyl('x',18.25,-2.7,.1,0,60)])\n",
     "    for b in L.FLOOR_HOLES.values():cuts.append(dc.box_solid(dict(b,z=(-.1,2.6))))\n    # Converter clearance only; obsolete BFAR counterbore removed.\n    cuts.extend([cyl('x',16.2,-5.3,-2.69,0,60),\n                 cyl('x',18.25,-2.7,.1,0,60)])\n"),
    ("            cuts.extend([cyl('x',2,-7,-2.7,y,z),cyl('x',1.7,-7.7,-6.9,y,z)])\n    # Original two-tine metal lock-tab torque catch, now grown from integral roof.\n    for b in L.tab_catch_boxes():\n        b=dict(b);b['z']=(b['z'][0],98.0);adds.append(dc.box_solid(b))\n    # Real vertical-PCB carrier mounting bosses, facing the open left side.\n",
     "            cuts.extend([cyl('x',2,-7,-2.7,y,z),cyl('x',1.7,-7.7,-6.9,y,z)])\n    # Passive PCB-edge guides; no BFAR torque reaction.\n    adds.extend(IG.tub_guides())\n    # Real vertical-PCB carrier mounting bosses, facing the open left side.\n"),
    ("    t2a,t2c=tub_print_fixes(length);adds+=t2a;cuts+=t2c   # T2: print-pose fixes and the VN-34 relief\n    t2s=tab_catch_split();adds+=t2s['adds']                 # T2 (VN-53): ceiling + pad over the +Y tine joint\n\n",
     '    t2a,t2c=tub_print_fixes(length);adds+=t2a;cuts+=t2c   # T2: print-pose fixes and the VN-34 relief\n\n'),
    ("    s=PG.cut_passages(s, PG.tub_cuts())\n    s=s.cut(t2s['envelope']).fuse(t2s['stub']).cut(t2s['vent']).clean()\n    if not s.isValid() or len(s.Solids())!=1:raise ValueError('bonded tub is not one valid solid')\n    return s\n",
     "    s=PG.cut_passages(s, PG.tub_cuts())\n    if not s.isValid() or len(s.Solids())!=1:raise ValueError('Innomaker tub is not one valid solid')\n    return s\n"),
    ("    adds.extend(tr(a,(CONTROL_MOVES['encoder'][0],CONTROL_MOVES['encoder'][1]-3,CONTROL_MOVES['encoder'][2])) for a in printed_panel._cradle(L))\n    # Camera cover catch: 0.5 behind maximum cover, while carrier is behind -34.\n    adds.append(box(-30.67,-27.34,1,22.6,66,76))\n    # EVF clamp/flex pad and positive PCB edge stop, mechanically rooted to the panel.\n",
     "    adds.extend(tr(a,(CONTROL_MOVES['encoder'][0],CONTROL_MOVES['encoder'][1]-3,CONTROL_MOVES['encoder'][2])) for a in printed_panel._cradle(L))\n    # Removable passive PCB-corner safety stops; no rear cover datum.\n    adds.extend(IG.panel_guides(local_y_shift=-3))\n    # EVF clamp/flex pad and positive PCB edge stop, mechanically rooted to the panel.\n"),
    ("            s=tr(roll(tr(body_native,(0,0,7.7))),(0,OP.STORAGE_DY,OP.STORAGE_DZ))\n        elif k=='cooler':\n",
     "            s=tr(roll(tr(body_native,(0,0,7.7))),(0,OP.STORAGE_DY,OP.STORAGE_DZ))\n        elif k=='gs_camera':\n            s=IG.operating_camera();mass=IG.MASS_ESTIMATE_G;r=dict(r,src=IG.camera_source())\n        elif k=='c_cs_adapter':\n            s=IG.converter_reserve();mass=4.;r=dict(r,src=IG.converter_source())\n        elif k=='cooler':\n"),
    ("    rows['usb_storage_plug_reserve']=dict(shape=reserve,kind='keepout',mass=0,source='NON-MATERIAL estimated USB-A plug envelope. Not an installed part or occupied material. Actual plug shell/contact geometry, engagement and insertion remain OPEN; export16 full-solid conflict preserved. No source contacts removed.')\n    # Corrected real SKU. Original12g total estimate is retained, not double counted.\n",
     "    rows['usb_storage_plug_reserve']=dict(shape=reserve,kind='keepout',mass=0,source='NON-MATERIAL estimated USB-A plug envelope. Not an installed part or occupied material. Actual plug shell/contact geometry, engagement and insertion remain OPEN; export16 full-solid conflict preserved. No source contacts removed.')\n    rows['camera_csi_service_reserve']=dict(shape=IG.csi_service_reserve(),kind='keepout',mass=0,source='Nonmaterial provisional camera CSI service corridor. Rear headers absent from source; full cable route and all real mating datums HOLD.')\n    # Corrected real SKU. Original12g total estimate is retained, not double counted.\n"),
]


def patched_source():
    """Return the Innomaker model text; raise if any replacement does not match exactly once."""
    text = read_text(OFFICIAL)
    for index, (old, new) in enumerate(PATCHES):
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f'Innomaker delta {index} matches official model.py {count} times (expected 1); '
                               'model.py changed, so review the Innomaker delta before building')
        text = text.replace(old, new)
    return text


def delta_matches_delivered_fork():
    """True when the patched text is byte-identical to the delivered fork's model.py (d319a35)."""
    return hashlib.sha256(patched_source().encode('utf-8')).hexdigest() == DELIVERED_MODEL_SHA256


def load():
    """Build the Innomaker model module and register it as 'model' for this process."""
    current = sys.modules.get('model')
    if current is not None:
        if getattr(current, 'CAMERA', None) == CAMERA:
            return current
        raise RuntimeError('The official model is already imported in this process; build Innomaker in its own process')
    module = types.ModuleType('model')
    module.__file__ = str(OFFICIAL)
    module.CAMERA = CAMERA
    sys.modules['model'] = module
    try:
        exec(compile(patched_source(), str(OFFICIAL), 'exec'), module.__dict__)
    except BaseException:
        del sys.modules['model']
        raise
    module.CAMERA = CAMERA
    return module
