"""PicoBlade full-wire service hypothesis. Unselected; requires actual datums/support.
Nominal pigtail assembly lengths are NOT assumed to be free flexible wire.
"""
import math

def rounded(R,points,radii,first_tail=3,last_tail=3,step=.2):
 p=[list(map(float,q)) for q in points];r=[float(x) for x in radii];trims=[0.]*len(p);turn=[0.]*len(p);errors=[];leg=[math.dist(a,b) for a,b in zip(p,p[1:])]
 for i in range(1,len(p)-1):
  u=R.unit(R.vsub(p[i],p[i-1]));v=R.unit(R.vsub(p[i+1],p[i]));a=math.acos(max(-1,min(1,R.dot(u,v))));turn[i]=a
  if a>math.pi-1e-7:errors.append('Reversal at '+str(i));continue
  trims[i]=r[i]*math.tan(a/2)
 for i,l in enumerate(leg):
  need=trims[i]+trims[i+1]+(first_tail if i==0 else 0)+(last_tail if i==len(leg)-1 else 0)
  if l+1e-8<need:errors.append(f'leg{i}: {l:.4f} available / {need:.4f} required')
 length=sum(leg)-2*sum(trims)+sum(r[i]*turn[i] for i in range(len(p)));out=[]
 def line(a,b):
  n=max(1,math.ceil(math.dist(a,b)/step))
  for j in range(n):out.append(R.vadd(a,R.vmul(R.vsub(b,a),j/n)))
 if not errors:
  last=p[0]
  for i in range(1,len(p)-1):
   if turn[i]<1e-8:continue
   u=R.unit(R.vsub(p[i],p[i-1]));v=R.unit(R.vsub(p[i+1],p[i]));enter=R.vsub(p[i],R.vmul(u,trims[i]));leave=R.vadd(p[i],R.vmul(v,trims[i]));c=R.vadd(p[i],R.vmul(R.unit(R.vsub(v,u)),r[i]/math.cos(turn[i]/2)));e0=R.unit(R.vsub(enter,c));line(last,enter)
   n=max(2,math.ceil(r[i]*turn[i]/step))
   for j in range(n):
    t=turn[i]*j/n;out.append(R.vadd(c,R.vmul(R.vadd(R.vmul(e0,math.cos(t)),R.vmul(u,math.sin(t))),r[i])))
   last=leave
  line(last,p[-1]);out.append(p[-1])
 return dict(knots=p,corner_radii_mm=r,centerline_radius_mm=min(x for x in r if x),first_straight_min_mm=first_tail,last_straight_min_mm=last_tail,raw_length_mm=sum(leg),rounded_length_mm=length if not errors else None,corner_trim_mm=trims,turn_degrees=list(map(math.degrees,turn)),sampled_centerline=out,errors=errors,status='blocked' if errors else 'geometric-path-only')

def build(R,panel_shift=0,junction_shift=0,lead_budget=210,short_budget=140,step=.2):
 # Actual nominal mated housing9Y×4.25X×3.3Z inside separately retained6×8×12 old reserve.
 near=[-133.5,15.1+junction_shift,79.7];far=[-133.5,6.1+junction_shift,79.7]
 h=next(h for h in R.header_housings() if h['cable']=='fps_lead');root=h['wire_exit'];branch=R.rounded_path([root,[root[0],-23.4,root[2]],[root[0],-23.4,25]],3.2,3,0,step)
 def main(top):return R.rounded_path([[-82.91,-23.4,25],[-82.91,-23.4,33.5],[-103.5,-23.4,33.5],[-103.5,-23.4,top],[-114.5,-23.4,top],[-114.5,-23.4,62.2],[-125,-23.4,62.2],[-125,5+junction_shift,62.2],[-131,8.464101615137754+junction_shift,62.2],[-131,23.3+junction_shift,62.2],[-133.5,23.3+junction_shift,79.7],near],5.2,3,3,step)
 low,high=72.6,96.1
 for _ in range(64):
  mid=(low+high)/2;c=main(mid)
  if c['errors']:raise ValueError(c['errors'])
  if c['rounded_length_mm']+branch['rounded_length_mm']>lead_budget:high=mid
  else:low=mid
 lc=main((low+high)/2)
 if abs(lc['rounded_length_mm']+branch['rounded_length_mm']-lead_budget)>1e-6:return dict(status='blocked: lead budget',panel_shift=panel_shift,junction_shift=junction_shift,required_at_low=main(72.6)['rounded_length_mm']+branch['rounded_length_mm'],available_at_high=main(96.1)['rounded_length_mm']+branch['rounded_length_mm'])
 def tail(bottom):return R.rounded_path([far,[-133.5,-17+junction_shift,79.7],[-133.5,-17+junction_shift,bottom],[-120.5,-17+junction_shift,bottom],[-120.5,-17+junction_shift,85],[-111,-13+junction_shift,85],[-111,8+panel_shift,78],[-111,12.2+panel_shift,78]],5.2,3,3,step)
 low,high=9.,69.3
 for _ in range(64):
  mid=(low+high)/2;c=tail(mid)
  if c['errors']:return dict(status='blocked: short curve',errors=c['errors'],panel_shift=panel_shift,junction_shift=junction_shift)
  if c['rounded_length_mm']>short_budget:low=mid
  else:high=mid
 sc=tail((low+high)/2)
 if abs(sc['rounded_length_mm']-short_budget)>1e-6:return dict(status='blocked: short budget',panel_shift=panel_shift,junction_shift=junction_shift,minimum_required=tail(69.3)['rounded_length_mm'],max_available=tail(9)['rounded_length_mm'])
 return dict(status='UNSELECTED PicoBlade service hypothesis; true roots, purchased-length datums, support, guide release and other looms remain STOP',panel_shift_y_mm=panel_shift,junction_shift_y_mm=junction_shift,lead_200=dict(curve=lc,branch=branch,modeled_wire_length_mm=lc['rounded_length_mm']+branch['rounded_length_mm']),pigtail_50=dict(curve=sc,modeled_wire_length_mm=sc['rounded_length_mm']),wire_parts=[dict(id='fps_header_branch',curve=branch,od_mm=1.6),dict(id='fps_200_main',curve=lc,od_mm=2.6),dict(id='fps_150_switch',curve=sc,od_mm=2.6)],junction=dict(box=R.B(-135.625,-131.375,6.1+junction_shift,15.1+junction_shift,78.05,81.35),protective_reserve=R.B(-137.5,-129.5,3.1+junction_shift,15.1+junction_shift,76.7,82.7),source_dimensions_mm=[9,4.25,3.3],world_dimensions_mm=[4.25,9,3.3],wire_axis=[0,-1,0],near_wire_face=near,far_wire_face=far),nominal_flexible_budgets_mm=[lead_budget,short_budget])
