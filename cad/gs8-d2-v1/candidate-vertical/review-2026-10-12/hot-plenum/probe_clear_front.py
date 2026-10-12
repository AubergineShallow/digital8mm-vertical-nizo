"""Same-envelope front extent, support row and exact saved-part outlet study."""
import sys,json,time
from pathlib import Path
CV=Path(__file__).resolve().parents[2];sys.path.insert(0,str(CV))
from cv_io import write_text
import cadquery as cq
sys.path.insert(0,str(Path(__file__).parent/'baseline'))
import vent_geometry as VG
import plenum_flow as PF
D=CV/'out/compact-kowa_lm6hc'
parts={n:cq.importers.importStep(str(D/'step'/f'{n}.step')).val() for n in ['lens_collar','s_c4']}
for top in (48.,49.,49.8,50.,54.,58.):
    q=cq.Solid.makeBox(11.99,6.,top-5.,cq.Vector(.01,-34.,5.))
    print(json.dumps(dict(context_top=top,overlaps={n:p.intersect(q).Volume() for n,p in parts.items()})),flush=True)
base_frame=PF.nominal_frame_boxes;base_bays=PF.bays
rows=[]
for top,upper,beam in [(49.8,49.,-29.),(49.8,54.,-29.),(49.8,55.,-29.),(49.,54.,-29.),(49.8,54.,-28.6),(49.8,54.,-28.8),(49.8,55.,-28.8)]:
    def bays(length):
        b=base_bays(length);b['hot']['mouths']['hot_front']=('x_max',5.,top);return b
    def frame(vg,length):
        b=base_frame(vg,length)
        return [(q[0],q[1],q[2],q[3],top,q[5]) if q[:2]==(-2.5,0) and q[4]==40 else q for q in b]
    PF.bays=bays;PF.nominal_frame_boxes=frame;VG.HOT_F_ROWS=(21.,28.,35.,40.6,upper,77.);VG.BEAM_Y0=beam
    s=time.monotonic();r=PF.nominal_min_cut(VG,158.,'hot')
    row=dict(front_top=top,upper_row=upper,beam=beam,min_cut=r['min_cut_mm2'],mouths=r['mouth_face_mm2'],cut_bbox=r['internal_cut_bbox_xz'],seconds=time.monotonic()-s)
    print(json.dumps(row),flush=True);rows.append(row)
write_text(Path(__file__).with_suffix('.json'),json.dumps(rows,indent=2)+'\n')
