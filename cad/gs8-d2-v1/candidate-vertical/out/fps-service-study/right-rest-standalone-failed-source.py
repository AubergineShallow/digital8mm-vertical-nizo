"""Separate source for the stationary-switch assembly rest; not integrated CAD."""
import cadquery as cq
V=cq.Vector
def box(b):
 return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))

def shelf():
 cradle=box([-112,-98.5,21,24.5,64.4,72.8]).cut(cq.Solid.makeCylinder(14,3.7,V(-111,20.9,80),V(0,1,0)))
 beam=box([-101.5,-97.3,-27,24.5,64.4,66.9])
 # Deep rear web avoids the PCB belowZ63.45;45degree transition is above it byY1.9.
 # Exact obstacle checking, not this description, governs acceptance.
 points=[(-101.5,-27,58),(-101.5,-4.5,58),(-101.5,1.9,64.4),(-101.5,24.5,64.4),(-101.5,24.5,66.9),(-101.5,-27,66.9)]
 wire=cq.Wire.makePolygon([V(*p) for p in points]+[V(*points[0])])
 web=cq.Solid.extrudeLinear(wire,[],V(4.2,0,0))
 pad=box([-112,-110,21,24.5,66,66.4]).cut(cq.Solid.makeCylinder(13.75,3.7,V(-111,20.9,80),V(0,1,0)))
 return cradle.fuse(beam,web,pad)

def connector_rest():
 return box([-136,-131,6,15,76.3,78.05]).fuse(box([-136,-133,-27,15,76.3,78.05]))
