"""12 mm flexible webbing routing proxy for reinforced heel; not a cut-length specification."""
import math
import cadquery as cq
V=cq.Vector
WIDTH=12.;THICKNESS=1.4
MAIN=[(-98.75,-15.5,-10),(-98,-15.5,-14),(-94,-12,-45),(-85,-5,-74),(-80,-2,-85)]
HEEL=[(-80,-85),(-76,-97),(-66.5,-97),(-66.5,-104),(-76,-104),(-79,-91)]
def ribbon_main():
 wires=[]
 for i,p in enumerate(MAIN):
  if i==0:t=V(*MAIN[1])-V(*p)
  elif i==len(MAIN)-1:t=V(-76,-2,-97)-V(*p)
  else:t=V(*MAIN[i+1])-V(*MAIN[i-1])
  t=t.normalized();w=(V(0,1,0)-t*t.dot(V(0,1,0))).normalized();n=t.cross(w).normalized();c=V(*p)
  pts=[c+w*(WIDTH/2)+n*(THICKNESS/2),c-w*(WIDTH/2)+n*(THICKNESS/2),c-w*(WIDTH/2)-n*(THICKNESS/2),c+w*(WIDTH/2)-n*(THICKNESS/2)]
  wires.append(cq.Wire.makePolygon(pts+[pts[0]]))
 return cq.Solid.makeLoft(wires,ruled=True)
def build(existing_upper):
 upper=existing_upper.intersect(cq.Solid.makeBox(100,60,15,V(-150,-40,-11)))
 pieces=[upper,ribbon_main()]
 for (ax,az),(bx,bz) in zip(HEEL[:-1],HEEL[1:]):
  length=math.hypot(bx-ax,bz-az);nx=-(bz-az)/length*THICKNESS/2;nz=(bx-ax)/length*THICKNESS/2
  pts=[V(ax+nx,-8,az+nz),V(bx+nx,-8,bz+nz),V(bx-nx,-8,bz-nz),V(ax-nx,-8,az-nz)]
  pieces.append(cq.Solid.extrudeLinear(cq.Wire.makePolygon(pts+[pts[0]]),[],V(0,12,0)))
 return pieces[0].fuse(*pieces[1:]).clean()
