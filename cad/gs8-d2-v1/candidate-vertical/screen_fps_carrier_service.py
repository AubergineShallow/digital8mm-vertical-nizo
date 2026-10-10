"""Fast sampled screening, never a substitute for exact swept-solid checks."""
from cv_io import write_text
import sys,json,importlib.util
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).parent;import routes as R,fps_ck1044_service_carrier as F
r=R.build();f=F.build(R)
spec=importlib.util.spec_from_file_location('corrected_hdmi',P/'routing-snapshots/hdmi-ck1044-clear-20261009-0524/hdmi300.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
h=H.compact_300_service(0,0); hb=np.asarray([[q['box'][a] for a in 'xyz'] for q in h['segments']]);obs=[]
for q in r['routes']:
 if q['id'] in ['usb_5v','fan','power_button']:obs.append((q['id'],q['curve']['sampled_centerline'],q['od_mm']))
sg=r['signal_geometry'];obs += [('qt',sg['qt']['curve']['sampled_centerline'],3.2)]+[(q['id'],q['curve']['sampled_centerline'],q['od_mm']) for q in sg['run_cores']]
rows=[]
for j,u in [(0,0),(5,0),(10,0),(15,0),(20,0),(23,0),(23,5),(23,10)]:
 f=F.build(R,j,u)
 for w in f['wire_parts']:
  pts=np.array(w['curve']['sampled_centerline']);rad=w['od_mm']/2;gaps={n:float(cKDTree(p).query(pts)[0].min()-rad-od/2) for n,p,od in obs};d=np.linalg.norm(np.maximum(np.maximum(hb[None,:,:,0]-pts[:,None,:],pts[:,None,:]-hb[None,:,:,1]),0),axis=2);ix=np.unravel_index(d.argmin(),d.shape);gaps['HDMI_conservative_AABB_lower_bound']=float(d[ix]-rad)
  rows.append(dict(wire=w['id'],pair_shift=j,unplug=u,minimum_sampled_gaps_mm=gaps,closest_hdmi_point=pts[ix[0]].tolist(),cell=int(ix[1])))
result=dict(status='Sampled source-only screening; HDMI segment AABB is conservative',rows=rows)
write_text(P/'out/fps-service-study/ck1044-carrier-service-source-screen.json',json.dumps(result,indent=2));print(json.dumps([r for r in rows if min(r['minimum_sampled_gaps_mm'].values())<0],indent=2))
