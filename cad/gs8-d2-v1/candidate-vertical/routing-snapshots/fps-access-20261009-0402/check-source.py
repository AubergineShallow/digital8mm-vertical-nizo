import routes as R,fps_service_routes as F,numpy as np,json,math
from scipy.spatial import cKDTree
r=R.build();S=r['signal_geometry'];P=r['power_geometry'];H=r['hdmi_ribbon'];hdlo=np.array([[s['box'][x][0] for x in 'xyz'] for s in H['segments']]);hdhi=np.array([[s['box'][x][1] for x in 'xyz'] for s in H['segments']]);
obs=[o for o in r['obstacles'] if o['id']!='fps_inline_ph_junction']
fixed_wires=[('qt',S['qt']['curve']['sampled_centerline'],3.2)]+[(c['id'],c['curve']['sampled_centerline'],c['od_mm']) for c in S['run_cores']]+[(c['id'],c['full_centerline_excluding_unmeasured_root_joint'],3.2) for c in P['cores']]+[(c['id'],c['curve']['sampled_centerline'],c['od_mm']) for c in r['routes'] if c['id'] in ['usb_5v','power_button','fan']]
trees=[(n,cKDTree(p),od/2) for n,p,od in fixed_wires]
def dist(a,o):
 b=o['box'];p=o.get('primitive',{});lo=np.array([b[x][0] for x in 'xyz']);hi=np.array([b[x][1] for x in 'xyz'])
 if p.get('type')=='cylinder_y':
  q=a[:,[0,2]]-np.array(p['center_xz']);rr=np.maximum(np.linalg.norm(q,axis=1)-p['radius'],0);ax=np.maximum(np.maximum(lo[1]-a[:,1],a[:,1]-hi[1]),0);return np.hypot(rr,ax)
 if p.get('type')=='xz_rectangle':
  aa,bb=np.array(p['ends_xz']);u=(bb-aa)/np.linalg.norm(bb-aa);v=np.array([-u[1],u[0]]);q=a[:,[0,2]]-(aa+bb)/2;xx=np.maximum(abs(q@u)-np.linalg.norm(bb-aa)/2,0);zz=np.maximum(abs(q@v)-p['half_width'],0);yy=np.maximum(np.maximum(lo[1]-a[:,1],a[:,1]-hi[1]),0);return np.sqrt(xx*xx+yy*yy+zz*zz)
 if p.get('type')=='oriented_box':
  q=(a-p['center'])@np.array(p['axes']).T;return np.linalg.norm(np.maximum(abs(q)-p['half_sizes'],0),axis=1)
 return np.linalg.norm(np.maximum(np.maximum(lo-a,a-hi),0),axis=1)
rows=[];minimums={};allhits={}
for j in range(21):
 shift=j/2;J=shift/2;f=F.build(R,shift,J,step=.15);rr=dict(panel_shift=shift,junction_shift=J,status=f['status'],hits=[])
 for wire in f['wire_parts']:
  a=np.array(wire['curve']['sampled_centerline']);rad=wire['od_mm']/2;n=wire['id']
  for o0 in obs:
   o=dict(o0);o['box']={x:list(o0['box'][x]) for x in 'xyz'}
   if o['id'] in ['encoder','switch_1824','power_switch_proxy','power_switch_nut_reserve','connector_p_qt_enc']:
    o['box']['y']=[v+shift for v in o['box']['y']]
   dd=dist(a,o)-rad;i=dd.argmin()
   if dd[i]<-1e-5:
    hit=dict(wire=n,item=o['id'],gap=float(dd[i]),point=a[i].tolist());rr['hits'].append(hit);allhits.setdefault((n,o['id']),hit)
  for name,tree,radius in trees:
   d,_=tree.query(a);gap=float(d.min()-rad-radius);key=n+' / '+name;minimums[key]=min(minimums.get(key,100),gap)
   if gap<0:rr['hits'].append(dict(wire=n,item=name,gap=gap))
  hdmin=100
  for st in range(0,len(a),100):
   ds=np.linalg.norm(np.maximum(np.maximum(hdlo[None,:,:]-a[st:st+100,None,:],a[st:st+100,None,:]-hdhi[None,:,:]),0),axis=2)-rad;hdmin=min(hdmin,float(ds.min()))
  minimums[n+' / HDMI']=min(minimums.get(n+' / HDMI',100),hdmin)
 rows.append(rr)
print('HITS',allhits);print('MINS',[(k,v) for k,v in minimums.items() if v<1]);print('othernegative',[(r['panel_shift'],h) for r in rows for h in r['hits'] if h['item'] in ['positive','negative','usb_5v','qt']][:8])
out=dict(status='Provisional source screening only; own housing root contacts remain local and actual unplugging/tool proof absent',rows=rows,minimums=minimums)
json.dump(out,open('/tmp/fps_service_review.json','w'),indent=2)
