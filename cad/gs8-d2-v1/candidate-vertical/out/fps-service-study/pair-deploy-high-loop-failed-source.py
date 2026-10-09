"""Stationary CK1044 Z80 routing, real A/throw2 fanout, source-bound hypothesis."""
import math

def build(R,junction_shift=0,unplug_shift=0,step=.15):
 # Keep the validated S-bend main route to the upper-rear PicoBlade housing.
 import importlib.util
 from pathlib import Path
 src=Path(__file__).parent/'routing-snapshots/fps-access-sbend-normal-root-20261009-0448/fps_service_routes-source.py'
 spec=importlib.util.spec_from_file_location('frozen_s',src);F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F);base=F.build(R,0,0,step)
 # Nominal genuine PicoBlade mated9Y×4.25X×3.3Z; preserve larger legacy keepout separately.
 j=junction_shift; u=unplug_shift
 box=R.B(-135.625,-131.375,6.1+j,15.1+j+u,78.05,81.35);far=[-133.5,6.1+j,79.7];near=[-133.5,15.1+j+u,79.7]
 branch=base['lead_200']['branch']
 def main(top):
  q=j+u
  return R.rounded_path([[-82.91,-23.4,25],[-82.91,-23.4,33.5],[-103.5,-23.4,33.5],[-103.5,-23.4,top],[-114.5,-23.4,top],[-114.5,-23.4,62.2],[-125,-23.4,62.2],[-125,5+q,62.2],[-131,8.464101615137754+q,62.2],[-131,23.3+q,62.2],[-133.5,23.3+q,79.7],near],5.2,3,3,step)
 def solve(fun,budget,lo,hi):
  for _ in range(64):
   mid=(lo+hi)/2;c=fun(mid)
   if c['errors']:raise ValueError(c['errors'])
   if c['rounded_length_mm']>budget:hi=mid
   else:lo=mid
  c=fun((lo+hi)/2)
  if abs(c['rounded_length_mm']-budget)>1e-6:raise ValueError('budget cannot be realized: '+str((budget,c['rounded_length_mm'])))
  return c
 #225mm installed axis includes retained GPIO donor stub and overlap, not225mm factory lead alone.
 main_pi=solve(main,225-branch['rounded_length_mm'],72.6,104)
 def sw(top):
  return R.rounded_path([far,[-133.5,-2,79.7],[-133.5,-19,top],[-110,-19,top],[-110,-12.7,79.7],[-110,-7.5,79.7]],5.2,3,0,step)
 main=solve(sw,81,84.5,106)
 branches=[]
 for name,angle,rad,sx in [('A',225,3.85,-109.375),('2',225,11.1,-110.625)]:
  th=math.radians(angle);end=[-111-rad*math.cos(th),7.1,80+rad*math.sin(th)];start=[sx,-7.5,79.7];lateral=math.hypot(end[0]-sx,end[2]-79.7);r=3.2
  # Descend on the rear side of the HDMI material before approaching the terminal +Y.
  if name=='2': points=[start,[sx,-2.5,79.7],[end[0],-2.5,end[2]],end]
  else:
   theta=min(math.pi/2,math.acos(max(-1,1-lateral/(2*r)))*.98);trim=r*math.tan(theta/2);dy=lateral/math.tan(theta) if theta<math.pi/2-1e-9 else 0.;k2=end[1]-3.2-trim;k1=k2-dy
   points=[start,[sx,k1,79.7],[end[0],k2,end[2]],end]
  c=R.rounded_path(points,r,0,3.2,step)
  if c['errors']:raise ValueError(c['errors'])
  branches.append(dict(id='fps_ck1044_pin_'+name,curve=c,od_mm=1.0,pin=name,terminal_tip=end,conductor_axis_length_including_shared_bundle_mm=main['rounded_length_mm']+c['rounded_length_mm']))
 return dict(status='Stationary switch proposal only; crimp/root fanouttransition, polarity/mirror, splice, tool and physical gates remain',junction=dict(box=box,protective_reserve=R.B(-137.5,-129.5,3.1+j,15.1+j+u,76.7,82.7),wire_axis=[0,-1,0],near_wire_face=near,far_wire_face=far),panel_shift_y_mm=60,junction_shift_y_mm=junction_shift,unplug_shift_mm=unplug_shift,wire_parts=[dict(id='fps_header_branch',curve=branch,od_mm=1.6),dict(id='fps_225_main',curve=main_pi,od_mm=2.6)]+[dict(id='fps_switch_bundle',curve=main,od_mm=2.6)]+branches,lead_225=dict(curve=main_pi,branch=branch,modeled_wire_length_mm=225),switch_branch_lengths_mm={b['pin']:b['conductor_axis_length_including_shared_bundle_mm'] for b in branches},stock=dict(pi_assembly='Molex2181110202,225±6mm exposed freewire',switch_assembly='Molex2181120201,150±6mm exposed freewire',gpio_donor='Adafruit1950,2×female-headerpigtails;2splices/2heatshrinks added'),unqualified=['Source front-PCB diagram mirror and selected A/throw2 mapping must be checked onreceivedswitch','Wireends touch reservedpin tips; solderlap/joint/sleeve consumedlength unmodeled','Shared bundle to two distinct branches hasunmeasured fanouttransition geometry','ExistingGPIO mating heads/proxy and true two-core fanoutremain gates','9mm connectorlength isreference; receivedmaximum andcrimp exits unmeasured'])
