"""Validate CAD-export mesh topology and bed transforms; not a slicer/print release."""
import argparse,hashlib,json,math
from pathlib import Path
import struct,collections
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--variant',default='compact-kowa_lm6hc');a=p.parse_args()
out=Path(__file__).resolve().parent/'out'/a.variant
manifest_start=hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()
m=json.loads((out/'manifest.json').read_text());printed={r['id']:r for r in m['rows'] if r['kind']=='printed'}
rows=[]
for name,pose in m['print_poses'].items():
 f=out/'stl'/f'{name}.stl';data=f.read_bytes();n=struct.unpack_from('<I',data,80)[0]
 if len(data)!=84+50*n:raise ValueError('Expected binary STL with exact record count:'+str(f))
 triangles=[];ids={};edges=collections.Counter();winding=collections.Counter()
 for i in range(n):
  row=struct.unpack_from('<12fH',data,84+50*i);tri=np.array(row[3:12],float).reshape(3,3);triangles.append(tri)
  ix=[]
  for pt in tri:
   key=tuple(round(float(v),6) for v in pt)
   if key not in ids:ids[key]=len(ids)
   ix.append(ids[key])
  for u,v in ((ix[0],ix[1]),(ix[1],ix[2]),(ix[2],ix[0])):
   key=tuple(sorted((u,v)));edges[key]+=1;winding[key]+=1 if u<v else -1
 tris=np.array(triangles);pts=tris.reshape(-1,3)
 volume=float(np.einsum('ij,ij->i',tris[:,0],np.cross(tris[:,1],tris[:,2])).sum()/6)
 watertight=all(v==2 for v in edges.values()) and all(v==0 for v in winding.values());positive=volume>0
 bounds=[pts.min(axis=0).tolist(),pts.max(axis=0).tolist()];size=(pts.max(axis=0)-pts.min(axis=0)).tolist()
 expected=printed.get(name,{}).get('volume_mm3')
 if expected is not None and name=='lens_collar':expected+=3*math.pi*1.7**2*.2
 err=abs(volume-expected) if expected else None
 within=err is None or err<=max(1.0,.005*expected)
 bed=min(size[0],size[1])<=210 and max(size[0],size[1])<=250 and size[2]<=220
 bound=hashlib.sha256(data).hexdigest()==m['files'].get(f'stl/{name}.stl')
 ok=bound and watertight and positive and within and bed and abs(bounds[0][2])<.002
 rows.append(dict(id=name,status='pass' if ok else 'fail',watertight=watertight,positive_volume=positive,volume_mm3=float(volume),expected_print_stock_mm3=expected,volume_error_mm3=err,bounds_mm=bounds,dimensions_mm=size,fits_250x210x220=bed,bed_z_zero=abs(bounds[0][2])<.002,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),physical_print_release=False))
if hashlib.sha256((out/'manifest.json').read_bytes()).hexdigest()!=manifest_start:raise ValueError('Manifest changed during mesh validation')
r=dict(manifest_sha256=manifest_start,verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),variant=a.variant,pass_count=sum(x['status']=='pass' for x in rows),fail_count=sum(x['status']=='fail' for x in rows),rows=rows,validator='stdlib binarySTL + numpy; vertex welding at1e-6mm, no mesh repair',note='Topology and bed envelope only. Supports, layer strength, slicer and every physical gate remain unrun. Collar STL includes three removable0.2mm membranes; STEP is cleared finished geometry.')
(out/'print-mesh-checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));raise SystemExit(bool(r['fail_count']))
