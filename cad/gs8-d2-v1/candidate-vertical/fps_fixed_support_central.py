"""Central rest proposal avoiding both full FPS main-wire vertical legs."""
import cadquery as cq
V=cq.Vector
def box(b):return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))
def shelf():
 beam=box([-112.5,-108.3,-27,24.5,64.4,66.9])
 pts=[(-112.5,-27,58),(-112.5,-19.3,58),(-112.5,-12.9,64.4),(-112.5,24.5,64.4),(-112.5,24.5,66.9),(-112.5,-27,66.9)]
 w=cq.Wire.makePolygon([V(*q) for q in pts]+[V(*pts[0])]);web=cq.Solid.extrudeLinear(w,[],V(4.2,0,0))
 s=beam.fuse(web).cut(cq.Solid.makeCylinder(14,13.6,V(-111,11,80),V(0,1,0)))
 pad=box([-112,-110,21,24.5,66,66.4]).cut(cq.Solid.makeCylinder(13.75,3.7,V(-111,20.9,80),V(0,1,0)))
 return s.fuse(pad)
