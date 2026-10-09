"""Dependency-free binary STL edge, winding, volume and bed-placement checks."""
from pathlib import Path
import struct,json,math,collections,argparse
ap=argparse.ArgumentParser();ap.add_argument('--folder',type=Path,default=Path(__file__).parent/'coupons');args=ap.parse_args();P=args.folder;m=json.loads((P/'coupon-manifest.json').read_text());results=[]
for row in m['parts']:
 p=P/(row['id']+'.stl');buf=p.read_bytes();n=struct.unpack_from('<I',buf,80)[0];assert len(buf)==84+50*n,p
 edges=collections.Counter();directions=collections.Counter();vol=0;zmin=1e9;mins=[1e9]*3;maxs=[-1e9]*3
 for i in range(n):
  vals=struct.unpack_from('<12fH',buf,84+50*i);v=[tuple(round(x,6) for x in vals[3+3*k:6+3*k]) for k in range(3)];a,b,c=v
  vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
  for vv in v:
   for k in range(3):mins[k]=min(mins[k],vv[k]);maxs[k]=max(maxs[k],vv[k])
  for x,y in zip(v,v[1:]+v[:1]):
   edge=tuple(sorted([x,y]));edges[edge]+=1;directions[edge]+=1 if x<y else -1
 bad=sum(x!=2 for x in edges.values());wrong=sum(x!=0 for x in directions.values());err=abs(vol-row['volume_mm3'])/row['volume_mm3']
 assert bad==wrong==0,(p,bad,wrong);assert vol>0 and err<.01 and abs(mins[2])<1e-5,(p,vol,err,mins)
 results.append(dict(id=row['id'],triangles=n,nonmanifold_edges=bad,inconsistent_edge_winding=wrong,signed_volume_mm3=vol,relative_volume_error=err,print_bbox_min_mm=mins,print_bbox_max_mm=maxs))
(P/'mesh-verification.json').write_text(json.dumps({'all_pass':True,'method':'Each undirected edge has2oppositely oriented triangles after1e-6mm vertex quantisation;positive signedvolume;STEPvolumeerror<1%;bedZ=0','coupons':results},indent=2)+'\n');print('PASS:',len(results),'watertight consistently wound STL coupons')
