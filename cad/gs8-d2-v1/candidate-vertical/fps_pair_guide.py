"""Open axial guide: retain the housing flange, let narrow trailing wires exit upward."""
import cadquery as cq
from fps_fixed_support import box,connector_rest,V

def build():
 s=connector_rest()
 for b in [
  [-137.625,-136.125,6,15,76.3,83.35],
  [-130.875,-129.375,6,15,76.3,83.35],
  [-137.625,-134.9,6,15,81.85,83.35],
  [-132.1,-129.375,6,15,81.85,83.35]]:s=s.fuse(box(b))
 # Connect both sidewalls to the support bed with a full floor.
 s=s.fuse(box([-137.625,-129.375,6,15,76.3,78.05]))
 # Flare the wire slit from2.8mm at its retaining throat to4.6mm at the top.
 pts=[(-134.9,5.9,81.85),(-132.1,5.9,81.85),(-131.2,5.9,83.36),(-135.8,5.9,83.36)]
 w=cq.Wire.makePolygon([V(*q) for q in pts]+[V(*pts[0])])
 return s.cut(cq.Solid.extrudeLinear(w,[],V(0,9.2,0)))
