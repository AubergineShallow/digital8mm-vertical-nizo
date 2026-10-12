"""Isolated mouth-extension probe; no live geometry changed."""
import sys,types,json,time
from pathlib import Path
CV=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(CV))
from cv_io import write_text
try: import cadquery
except ModuleNotFoundError:
    sys.modules['cadquery']=types.SimpleNamespace(Vector=object)
sys.path.insert(0,str(Path(__file__).parent/'baseline'))
import vent_geometry as VG
import plenum_flow as PF
base_frame=PF.nominal_frame_boxes
base_bays=PF.bays
base_rows=VG.hot_rows
rows=[]
for top in (40.,45.,48.,50.,54.,58.,62.):
    for more_mullion in (False,True) if top>49.6 else (False,):
        def bays(length):
            b=base_bays(length);b['hot']['mouths']['hot_front']=('x_max',5.,top);return b
        def frame(vg,length):
            b=base_frame(vg,length)
            b=[(q[0],q[1],q[2],q[3],top,q[5]) if q[:2]==(-2.5,0) and q[4]==40 else q for q in b]
            if more_mullion:b.append((-2.6,0,*VG.RIB_Y,48.4,49.6))
            return b
        def hot_rows(length):
            out=base_rows(length)
            return [(z,[(a,0. if more_mullion and z==49 else b) for a,b in segs]) for z,segs in out]
        PF.bays=bays;PF.nominal_frame_boxes=frame;VG.hot_rows=hot_rows
        s=time.monotonic();r=PF.nominal_min_cut(VG,158.,'hot');e=PF.nominal_min_cut(VG,158.,'hot',ribs=False)
        row=dict(front_top=top,extra_mullion=more_mullion,min_cut=r['min_cut_mm2'],empty_bound=e['min_cut_mm2'],mouths=r['mouth_face_mm2'],cut_bbox=r['internal_cut_bbox_xz'],seconds=time.monotonic()-s)
        print(json.dumps(row),flush=True);rows.append(row)
write_text(Path(__file__).with_suffix('.json'),json.dumps(rows,indent=2)+'\n')
