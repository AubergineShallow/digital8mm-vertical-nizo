"""Keep purchased hardware and envelope: offset the upper exit into the outer 3mm of the existing gap."""
import sys,json,time
from pathlib import Path
CV=Path(__file__).resolve().parents[2];sys.path.insert(0,str(CV))
from cv_io import write_text
sys.path.insert(0,str(Path(__file__).parent/'baseline'))
import vent_geometry as VG
import plenum_flow as PF
base_frame=PF.nominal_frame_boxes;base_bays=PF.bays
VG.HOT_F_ROWS=(21.,28.,35.,40.6,58.,77.)
rows=[]
for fulltop,top,depth in [(49.,56.,2.5)]:
 def bays(length):
    b=base_bays(length);b['hot']['mouths']['hot_front']=('x_max',5.,top);return b
 def frame(vg,length):
    b=base_frame(vg,length)
    b=[(q[0],q[1],q[2],q[3],top,q[5]) if q[:2]==(-2.5,0) and q[4]==40 else q for q in b]
    b.append((-2.5,0.,-34.+depth,VG.RIB_Y[1],fulltop,top))
    return b
 PF.bays=bays;PF.nominal_frame_boxes=frame
 s=time.monotonic();r=PF.nominal_min_cut(VG,158.,'hot')
 row=dict(full_height_top=fulltop,front_top=top,outer_gap_depth=depth,upper_row=58.,min_cut=r['min_cut_mm2'],mouths=r['mouth_face_mm2'],cut_bbox=r['internal_cut_bbox_xz'],seconds=time.monotonic()-s)
 print(json.dumps(row),flush=True);rows.append(row)
write_text(Path(__file__).with_suffix('.json'),json.dumps(rows,indent=2)+'\n')
