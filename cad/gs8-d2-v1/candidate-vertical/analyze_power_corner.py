"""Sampled spacing around an intentionally relieved grip tongue; not stress analysis."""
from cv_io import read_text, write_text
import json,math,hashlib
from pathlib import Path
P=Path(__file__).parent;src=P/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json';s=json.loads(read_text(src))
poly=[(-83,-13),(-78,-13),(-75,-10),(-75,13),(-83,13)]
def edge_distance(p,a,b):
 v=[b[i]-a[i] for i in range(2)];t=max(0,min(1,sum((p[i]-a[i])*v[i] for i in range(2))/sum(x*x for x in v)));return math.dist(p[:2],[a[i]+t*v[i] for i in range(2)])
def dist(p,z0,z1):
 xy=min(edge_distance(p,a,b) for a,b in zip(poly,poly[1:]+poly[:1]));dz=max(0,z0-p[2],p[2]-z1);return math.hypot(xy,dz)
# Every sampled path point lies outside this polygon; no inside-point distance assumption.
points=s['cores'][1]['local_points'];values={}
for label,z0,z1 in [('neck',-1.85,0),('floor_attachment',0,2.5)]:
 d,p=min((dist(p,z0,z1)-1.94,p) for p in points);values[label]=dict(minimum_sampled_surface_spacing_mm=d,wire_center_mm=p)
fuse=[]
for i,pose in enumerate(s['rigid_service_poses']):
 for j in range(101):
  p=[pose['fuse_start'][k]+(pose['fuse_end'][k]-pose['fuse_start'][k])*j/100 for k in range(3)]
  if -5<p[2]<6:fuse.append((dist(p,-1.85,2.5)-2.8,i,p))
d,i,p=min(fuse);values['fuse_motion']=dict(conservative_sampled_sphere_envelope_spacing_mm=d,pose=i,axis_point_mm=p)
result=dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),neck_polygon_xy_mm=poly,clip_leg_mm=3,original_area_mm2=208,remaining_area_mm2=203.5,remaining_fraction=203.5/208,wire_cut_radius_mm=1.94,values=values,scope='Sampled spacing to retained attachment prism; not continuous motion proof, printed strength, layer bonding, contact wear, or a closed physical gate.')
out=P/'out/power-fit-study';out.mkdir(exist_ok=True);write_text(out/'corner-analysis.json',json.dumps(result,indent=2));print(json.dumps(result,indent=2))
