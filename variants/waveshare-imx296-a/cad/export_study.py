# SPDX-License-Identifier: MIT
"""Bounded vendor-datum study ONLY. Run through the SHARED CAD lock.

No placed D2 assembly, release mesh, thread model, sensor plane or FPC route is
created. The bracket is an unanchored, UNAPPROVED hardware proposal.

The vendor drawing is not in the repository (R-03). Export requires a local copy
whose SHA-256 matches camera-profile.json (see camera_profile.DRAWING_LOCAL /
GS8_WAVESHARE_DRAWING). STEP headers get the repository's fixed FILE_NAME stamp
(export_cache.normalize_step_header, fix pass 2026-10-13).
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import importlib.metadata
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(1, str(Path(__file__).resolve().parents[3] / 'cad/gs8-d2-v1/candidate-vertical'))
from camera_profile import ROOT, load_profile, nominal_local_bounds, release_status, drawing_path, drawing_verified
from export_cache import normalize_step_header


def build(p):
    import cadquery as cq
    V = cq.Vector
    d = p['vendor_dimensions_mm']
    def box(x0, x1, y0, y1, z0, z1):
        return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, V(x0,y0,z0))
    def cyl(r, x0, x1, y, z):
        return cq.Solid.makeCylinder(r, x1-x0, V(x0,y,z), V(1,0,0))
    # Sharp square is a bounding approximation; drawing corner radius unspecified.
    pcb = box(-1.6,0,-19,19,-19,19)
    holes = [(y,z) for y in (-15.,15.) for z in (-15.,15.)]
    pcb = pcb.cut(*(cyl(1.25,-1.7,.1,y,z) for y,z in holes))
    housing = cyl(14.25,0,12.5,0,0)
    # Bore/thread/internal optics NOT modelled as material. Solid cylinder is an envelope.
    rear = box(-4.1,-1.6,-19.1,19.1,-19.1,19.1)
    max_pcb = box(-1.6,0,-19.1,19.1,-19.1,19.1)
    max_housing = cyl(14.25,0,12.7,0,0)
    # Unanchored U-frame. Open lower centre avoids falsely bridging CSI connector.
    # 3 mm is a DESIGN PROPOSAL standoff, not a vendor clearance requirement.
    frame = box(-7,-4.6,-18.6,-11.4,-15,15).fuse(
        box(-7,-4.6,11.4,18.6,-15,15),box(-7,-4.6,-15,15,11.4,18.6),
        *(cyl(3.6,-7,-4.6,y,z) for y,z in holes),
        *(cyl(3.,-4.6,-1.6,y,z) for y,z in holes))
    frame = frame.cut(*(cyl(1.1,-7.1,-1.5,y,z) for y,z in holes)).clean()
    # No nut trap because print and actual nut envelope are unqualified.
    return {'pcb_nominal_hole_pattern':pcb,'housing_nominal_envelope':housing,
            'rear_connector_unlocated_reserve':rear,'pcb_max_side_envelope':max_pcb,
            'housing_max_depth_envelope':max_housing,'UNAPPROVED_four_hole_frame_study':frame}


def main():
    import cadquery as cq
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'cad/out-study')
    a=parser.parse_args()
    p=load_profile(); out=a.out.resolve()
    if not drawing_verified(p):
        raise ValueError('export needs the local vendor drawing with the pinned SHA-256 (kept out of the repository, R-03)')
    drawing=drawing_path()
    sources=(ROOT/'camera-profile.json',ROOT/'camera_profile.py',Path(__file__).resolve())
    source_hashes={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    source_hashes['evidence/vendor-drawing.jpg']=hashlib.sha256(drawing.read_bytes()).hexdigest()
    if out.exists() and any(out.iterdir()):
        raise ValueError('export requires a new empty study directory')
    out.mkdir(parents=True,exist_ok=True)
    rows=[]; shapes=build(p)
    for name, shape in shapes.items():
        if not shape.isValid() or len(shape.Solids())!=1:
            raise ValueError(f'invalid/non-single study solid: {name}')
        path=out/f'{name}.step'
        cq.exporters.export(shape,str(path))
        normalize_step_header(path)
        reread=cq.importers.importStep(str(path)).val()
        if not reread.isValid() or abs(reread.Volume()-shape.Volume())>1e-4:
            raise ValueError(f'STEP round-trip failed: {name}')
        b=reread.BoundingBox()
        rows.append({'name':name,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'valid_step_roundtrip':True,'solid_count':len(reread.Solids()),
                     'bbox_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],
                     'proxy_volume_mm3':reread.Volume(),'physical_material_volume_known':False,
                     'geometry_role':'unapproved printed interface proposal' if 'UNAPPROVED' in name else 'vendor drawing envelope / non-material reserve'})
    # Separate-study assembly contains only the nominal proxies + proposed frame.
    asm=cq.Assembly(name='Waveshare_UNANCHORED_STUDY_NOT_D2_ASSEMBLY')
    for name in ('pcb_nominal_hole_pattern','housing_nominal_envelope','UNAPPROVED_four_hole_frame_study'):
        asm.add(shapes[name],name=name)
    assembly_path=out/'UNANCHORED-interface-study.step'
    asm.save(str(assembly_path))
    normalize_step_header(assembly_path)
    assembly_readback=cq.importers.importStep(str(assembly_path)).val()
    expected_assembly_volume=sum(shapes[n].Volume() for n in ('pcb_nominal_hole_pattern','housing_nominal_envelope','UNAPPROVED_four_hole_frame_study'))
    if not assembly_readback.isValid() or len(assembly_readback.Solids())!=3 or abs(assembly_readback.Volume()-expected_assembly_volume)>1e-4:
        raise ValueError('unanchored study assembly STEP round-trip failed')
    data={'profile_id':p['profile_id'],'release':release_status(p),'coordinate_system':p['coordinate_system'],
          'nominal_local_bounds':nominal_local_bounds(p),'rows':rows,
          'sources':source_hashes,
          'runtime':{'python':platform.python_version(),'cadquery':importlib.metadata.version('cadquery'),'platform':platform.platform()},
          'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.step'))},
          'drawing_sha256':p['drawing_sha256'],
          'assembly_step_roundtrip':{'valid':True,'solid_count':len(assembly_readback.Solids()),'volume_mm3':assembly_readback.Volume(),'role':'unanchored local study, NOT D2 integrated assembly'},
          'not_modelled':['sensor plane','C/CS thread and adapter','lens engagement','component keepouts','camera connector exact position/latch','FPC route','enclosure anchor','D2 assembly'],
          'manufacturing_status':'NO PRODUCTION STL; interface study only; fasteners not approved'}
    after={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    after['evidence/vendor-drawing.jpg']=hashlib.sha256(drawing.read_bytes()).hexdigest()
    if source_hashes!=after:
        raise RuntimeError('study sources changed during export; reject this output')
    (out/'study-receipt.json').write_bytes((json.dumps(data,indent=2)+'\n').encode('utf-8'))  # LF on every OS
    print(json.dumps({'study_exported':True,'files':len(rows)+2,'physical_release':False,'out':str(out)},indent=2))


if __name__=='__main__':
    main()
