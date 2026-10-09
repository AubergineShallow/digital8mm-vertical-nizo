"""Two real1mm core envelopes routed on opposite sides of the lower HDMI row."""
import fps_ck1044_service as S

def build(R,junction_shift=0,unplug_shift=0,step=.15):
 f=S.build(R,junction_shift,unplug_shift,step);j=junction_shift
 A=[-108.2776388924318,7.1,77.2776388924318];T=[-103.151114728829,7.1,72.151114728829]
 def ac(x):return R.rounded_path([[-132.875,6.1+j,79.7],[-132.875,-19,79.7],[x,-19,79.7],[x,-7.5,79.7],[A[0],-7.5,A[2]],A],3.2,3,3.2,step)
 def tc(x):return R.rounded_path([[-134.125,6.1+j,79.7],[-134.125,-2,79.7],[-138,-5.875,79.7],[-138,-13,79.7],[-138,-13,T[2]],[-138,4.5,T[2]],[x,4.5,T[2]],[x,-2.5,T[2]],[T[0],-2.5,T[2]],T],3.2,3,3.2,step)
 def solve(fun,budget,lo,hi):
  for _ in range(64):
   mid=(lo+hi)/2;c=fun(mid)
   if c['errors']:raise ValueError(c['errors'])
   if c['rounded_length_mm']>budget:hi=mid
   else:lo=mid
  c=fun((lo+hi)/2)
  if abs(c['rounded_length_mm']-budget)>1e-6:raise ValueError('Unrealizable core budget '+str((budget,c['rounded_length_mm'])))
  return c
 c1=solve(ac,112,-101,-70);c2=solve(tc,128,-96.7,-70)
 f['wire_parts']=f['wire_parts'][:2]+[dict(id='fps_A_full_core',curve=c1,od_mm=1.0,terminal_tip=A),dict(id='fps_2_full_core',curve=c2,od_mm=1.0,terminal_tip=T)]
 f['switch_branch_lengths_mm']={'A':112,'2':128}
 return f
