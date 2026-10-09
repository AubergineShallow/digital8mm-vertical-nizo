"""Isolated coordinated J4 hypothesis. Does not edit active model/layout files."""
from contextlib import contextmanager
import copy

def revised_tongues(existing,lip=2.4,head=2.4,gap=.25):
 if lip<1.6 or head<1.8 or gap<=0:raise ValueError('Invalid joint trial')
 out=copy.deepcopy(existing);neck_bottom=-(lip+gap);head_bottom=neck_bottom-head;pocket_bottom=head_bottom-gap
 for t in out:
  t['neck']['z']=(neck_bottom,0.);t['head']['z']=(head_bottom,neck_bottom)
  t['base_lips_z']=(-lip,0.);t['base_neck_slot']['z']=(-lip,0.)
  t['base_pocket']['z']=(pocket_bottom,-lip);t['base_window']['z']=(-lip,0.)
 return out

@contextmanager
def trial_layout(L,lip=2.4,head=2.4):
 oldt,olds=L.TONGUE,L.TONGUES
 try:
  L.TONGUE=copy.deepcopy(oldt);L.TONGUE.update(neck_h=lip+.25,head_h=head)
  L.TONGUES=revised_tongues(olds,lip,head)
  yield L.TONGUES
 finally:L.TONGUE,L.TONGUES=oldt,olds

def entry_floor_stock():
 """Local replacement of underside chamfer/pad relief, within original base bbox.
 Keeps Z>=-8 and frontX<=-0.5. Sound2.7mm floor under front pocket toZ-5.3.
 """
 import cadquery as cq
 V=cq.Vector
 def prism(poly):
  w=cq.Wire.makePolygon([V(x,-19.5,z) for x,z in poly]+[V(poly[0][0],-19.5,poly[0][1])]);return cq.Solid.extrudeLinear(w,[],V(0,39,0))
 floor=cq.Solid.makeBox(18.5,39,2.7,V(-22.25,-19.5,-8))
 front=prism([(-3.75,-8),(-.5,-3),(-.5,0),(-3.75,0)])
 rear=prism([(-23.25,-7),(-22.25,-8),(-22.25,-5.3),(-23.25,-5.3)])
 return floor.fuse(front,rear).clean()
