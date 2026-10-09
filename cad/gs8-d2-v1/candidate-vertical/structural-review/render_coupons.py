from pathlib import Path
import struct,json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
P=Path(__file__).parent/'coupons';m=json.loads((P/'coupon-manifest.json').read_text());f=plt.figure(figsize=(13,10));f.suptitle('Custom coupon geometry in printing pose\nGeometry preview only, not a stress plot or a print release',fontsize=14)
for i,r in enumerate(m['parts']):
 buf=(P/(r['id']+'.stl')).read_bytes();n=struct.unpack_from('<I',buf,80)[0];v=np.array([struct.unpack_from('<12fH',buf,84+50*k)[3:12] for k in range(n)]).reshape(-1,3,3);a=f.add_subplot(3,3,i+1,projection='3d');a.add_collection3d(Poly3DCollection(v,facecolor='#a4b7c9',edgecolor='#506174',linewidth=.15,alpha=1));mins=v.min(axis=(0,1));maxs=v.max(axis=(0,1));mid=(mins+maxs)/2;span=max(maxs-mins)*.6
 a.set_xlim(mid[0]-span,mid[0]+span);a.set_ylim(mid[1]-span,mid[1]+span);a.set_zlim(mid[2]-span,mid[2]+span);a.set_box_aspect([1,1,1]);a.view_init(elev=25,azim=-60);a.set_axis_off();a.set_title(r['id'].replace('_',' ')+'\n'+ ' × '.join(f'{x:.1f}' for x in r['print_bbox_mm'])+' mm',fontsize=9)
f.subplots_adjust(top=.87,hspace=.05,wspace=.02);f.savefig(P/'coupon-geometry.png',dpi=150,bbox_inches='tight')
