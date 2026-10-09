"""Proposed printed reinforcements; load screens are not material qualification."""
import cadquery as cq
V=cq.Vector

def heel_doubler():
 p=[(-68.55,-88),(-71,-88),(-74,-91),(-74,-106),(-71,-109),(-68.55,-109)]
 w=cq.Wire.makePolygon([V(x,-11,z) for x,z in p]+[V(p[0][0],-11,p[0][1])])
 add=cq.Solid.extrudeLinear(w,[],V(0,19,0))
 # Round the external long side roots where possible; the3mm X/Z tapers remain.
 add=cq.Workplane(obj=add).edges('|Z').fillet(1).val()
 for z in (-104.,-97.):
  add=add.cut(cq.Solid.makeBox(5.65,13,3.5,V(-74.1,-8.5,z-1.75)))
 return add

def reinforce_grip(grip):
 s=grip.fuse(heel_doubler())
 for z in (-104.,-97.):
  s=s.cut(cq.Solid.makeBox(5.65,13,3.5,V(-74.1,-8.5,z-1.75)))
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('Invalid reinforced grip')
 return s

def carrier_arm_addition():
 # Preserve original upper edge; grow4mm toward the lower clear side.
 # Outer surface+Y22.2, original UPS-facing datum+Y17.2 remains unchanged.
 import math
 ax,az,bx,bz=-127.,69.,-93.,53.
 length=math.hypot(bx-ax,bz-az);nx=-(bz-az)/length;nz=(bx-ax)/length
 p=[(ax+nx*2,az+nz*2),(bx+nx*2,bz+nz*2),(bx-nx*6,bz-nz*6),(ax-nx*6,az-nz*6)]
 w=cq.Wire.makePolygon([V(x,17.2,z) for x,z in p]+[V(p[0][0],17.2,p[0][1])])
 s=cq.Solid.extrudeLinear(w,[],V(0,5,0))
 # Rounded root pads spread load into both frame rails without a sharp neck.
 for x,z,r in [(-127,69,4.8),(-96.2,55.5,3),(-96.2,47,3)]:
  s=s.fuse(cq.Solid.makeCylinder(r,5,V(x,17.2,z),V(0,1,0)))
 s=s.cut(cq.Solid.makeCylinder(1.7,5.2,V(-127,17.1,69),V(0,1,0)),
         cq.Solid.makeCylinder(3.2,2.5,V(-127,19.8,69),V(0,1,0)))
 # Preserve the existing lower kit screw-head and driver corridors where the
 # rounded frame-root pad approaches the rear upper stack fastener.
 for x in (-95.5,-37.5):
  for z in (10.5,59.5):
   s=s.cut(cq.Solid.makeCylinder(1.4,5.2,V(x,17.1,z),V(0,1,0)),
           cq.Solid.makeCylinder(2.65,3.2,V(x,19.1,z),V(0,1,0)),
           cq.Solid.makeCylinder(3.35,.8,V(x,21.5,z),V(0,1,0)))
 return s

def reinforce_carrier(carrier):
 s=carrier.fuse(carrier_arm_addition())
 if not s.isValid() or len(s.Solids())!=1:raise ValueError('Invalid reinforced carrier')
 return s
