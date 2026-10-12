"""Search simple port-band-preserving hot-support spacing, no live edits."""
import sys,json,time
from pathlib import Path
CV=Path(__file__).resolve().parents[2];sys.path.insert(0,str(CV))
from cv_io import write_text
sys.path.insert(0,str(Path(__file__).parent/'baseline'))
import vent_geometry as VG
import plenum_flow as PF
base_frame=PF.nominal_frame_boxes;base_bays=PF.bays
base_w=VG._windowed
TOP=49.8
VG.HOT_F_ROWS=(21.,28.,35.,40.6,54.,77.)
def bays(length):
    b=base_bays(length);b['hot']['mouths']['hot_front']=('x_max',5.,TOP);return b
def frame(vg,length):
    b=base_frame(vg,length)
    return [(q[0],q[1],q[2],q[3],TOP,q[5]) if q[:2]==(-2.5,0) and q[4]==40 else q for q in b]
PF.bays=bays;PF.nominal_frame_boxes=frame
rows=[]
for beam,band,col,uz in [(-28.6,12.,-17.1,-48.)]:
 VG.BEAM_Y0=beam;VG.HOT_BAND_ROW=(band,-16.5,-2.6);VG.HOT_COLUMN_X=col;VG.HOT_UZ_X=(uz,)
 s=time.monotonic();r=PF.nominal_min_cut(VG,158.,'hot')
 row=dict(front_top=TOP,beam=beam,band=band,column=col,uz=uz,min_cut=r['min_cut_mm2'],cut_bbox=r['internal_cut_bbox_xz'],seconds=time.monotonic()-s)
 print(json.dumps(row),flush=True);rows.append(row)
write_text(Path(__file__).with_suffix('.json'),json.dumps(rows,indent=2)+'\n')
