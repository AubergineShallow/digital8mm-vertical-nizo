"""Full-width corrected HDMI versus frozen neighboring wires and reservations.

Run through run_locked.py. Analytic round wire sweeps and conservative power
capsules retain their full modeled OD. Missing material and root joints remain
explicit gates. No cut length, material radius, or service approval is implied.
"""
import ast, hashlib, itertools, json, math
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing

P=Path(__file__).resolve().parent
V=cq.Vector
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def bounds(d):return [v for k in 'xyz' for v in d[k]]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,2,4))
def box(b):return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))
def load_functions(name,wanted):
 tree=ast.parse((P/name).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
 if len(nodes)!=len(wanted):raise ValueError('Missing frozen helper')
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/name),'exec'),globals())
load_functions('source-verify_hdmi.py',{'cell'})
load_functions('source-verify_fps_access.py',{'rounded_wire','tube'})
load_functions('source-power_geometry.py',{'simplify','cylinder','ball'})

data=json.loads((P/'input.json').read_text());r=json.loads((P/'context.json').read_text())
objects={};object_notes={}
def put(name,shape,note):objects[name]=shape;object_notes[name]=note
def wt(name,c,od):
 if c['errors']:return
 put(name,tube(c,od)[0],dict(kind='analytic circular wire sweep',od_mm=od,modeled_length_mm=c['rounded_length_mm']))
for w in r['routes']:
 if w['id'] in ('usb_5v','fan','power_button'):wt(w['id'],w['curve'],w['od_mm'])
for b in r['header_wire_branches']:wt('branch_'+b['id'],b['curve'],b['od_mm'])
q=r['signal_geometry'];wt('qt',q['qt']['curve'],q['qt']['od_mm'])
for w in q['run_cores']:wt(w['id'],w['curve'],w['od_mm'])
for w in q['fps']['wire_parts']:wt('legacy_fps_'+w['id'],w['curve'],w['od_mm'])
put('legacy_fps_pair',box(bounds(q['fps']['junction']['box'])),dict(kind='retired FPS pair hypothesis, corrected independent FPS study supersedes it'))
newfps=json.loads((P/'corrected-fps-context-0528.json').read_text())
for w in newfps['wire_parts']:wt('corrected_fps_'+w['id'],w['curve'],w['od_mm'])
put('corrected_fps_pair',box(bounds(newfps['junction']['box'])),dict(kind='corrected FPS pair hypothesis'))
put('corrected_fps_protective_reserve',box(bounds(newfps['junction']['protective_reserve'])),dict(kind='protective reservation only; support is not a solid design'))
for z0,z1 in [(41,51),(55,65)]:
 put('corrected_fps_splice_'+str(z0),cylinder([-103.5,-23.4,z0],[-103.5,-23.4,z1],1.5),dict(kind='separate OD3 x10 mm splice reservation'))
for core in r['power_geometry']['cores']:
 for part in core['flexible_wire_parts']:
  pts=simplify(part['points'],.04);radius=core['od_mm']/2+.04
  pieces=[cylinder(a,b,radius) for a,b in zip(pts,pts[1:]) if math.dist(a,b)>1e-8]+[ball(p,radius) for p in pts]
  put('power_'+core['id']+'_'+part['id'],cq.Compound.makeCompound(pieces),dict(kind='conservative full diameter polyline capsules',radius_mm=radius,chord_allowance_mm=.04,root_gap_mm=core['unmodeled_root_joint_allowance_mm']))
f=r['power_geometry']['fuse'];put('power_fuse',cylinder(f['start'],f['end'],f['radius_mm']),dict(kind='full rigid fuse reservation'))
for reserve in r['slack_reservations']:
 put('reserve_'+reserve['id'],box(bounds(reserve['box'])),dict(kind='space reservation only; not modeled stored material',cables=reserve['cables']))
# Parent full-width camera connector/approach reservation, retained unchanged.
put('fpc_connector_reservation',box([-116.8,-102.1,-21.6,-4.5,64.7,75]),dict(kind='full width FPC connector approach reservation; physical fold shape remains open'))
# The remaining FPC is still a centerline. Expand the complete modeled curve by
# half its full width in every direction; this rejects clearance only where this
# deliberately generous envelope overlaps. A hit does not prove actual contact.
fpc=q['fpc'];pts=simplify(fpc['curve']['sampled_centerline'],.02);rad=fpc['full_width_mm']/2+.02
pieces=[cylinder(a,b,rad) for a,b in zip(pts,pts[1:]) if math.dist(a,b)>1e-8]+[ball(p,rad) for p in pts]
put('fpc_orientation_unknown_fullwidth_envelope',cq.Compound.makeCompound(pieces),dict(kind='orientation-independent conservative envelope, not actual FPC geometry',radius_mm=rad,unmodeled_stock_mm=fpc['unmodeled_stock_mm']))
ob={n:bb(s) for n,s in objects.items()}
parts={n:s.Solids() for n,s in objects.items()}
pb={n:np.array([bb(s) for s in pieces]) for n,pieces in parts.items()}
def candidates(name,b):
 boxes=pb[name];mask=np.ones(len(boxes),dtype=bool)
 for j in (0,2,4):mask &= (np.minimum(boxes[:,j+1],b[j+1])-np.maximum(boxes[:,j],b[j]))>1e-8
 return [parts[name][i] for i in np.nonzero(mask)[0]]
checks=[];material_cache={}
def check(state,dy=0,active=None):
 shape=data['hdmi_'+state];hits={};broad=0;exact=0
 active=list(objects) if active is None else active
 for i,seg in enumerate(shape['segments']):
  b=bounds(seg['box']);b[2]+=dy;b[3]+=dy
  possible=[n for n in active if n not in hits and overlaps(b,ob[n]) and len(candidates(n,b))]
  if not possible:continue
  broad+=len(possible)
  c=material_cache.get((state,i))
  if c is None:c=cell(seg['vertices']);material_cache[(state,i)]=c
  if c is None:continue
  if dy:c=c.translate(V(0,dy,0))
  for name in possible:
   v=0.
   for piece in candidates(name,b):
    common=c.intersect(piece);v=common.Volume();exact+=1
    if v>1e-6:break
   if v>1e-6:
    h=hits.setdefault(name,dict(obstacle=name,cell_count=0,max_overlap_mm3=0,first_cells=[]))
    h['cell_count']+=1;h['max_overlap_mm3']=max(h['max_overlap_mm3'],v)
    if len(h['first_cells'])<5:h['first_cells'].append(dict(cell=i,overlap_mm3=v,bbox_mm=bb(common)))
 row=dict(state=state,shift_y_mm=dy,full_material_mm=shape['routed_length_mm'],hits=list(hits.values()),broad_phase_pairs=broad,exact_intersections=exact)
 checks.append(row);print(json.dumps(dict(state=state,shift_y_mm=dy,hits=[h['obstacle'] for h in row['hits']],exact=exact)),flush=True)
 return row
for state in ['installed','premate','both_unplugged']:check(state)
# Loose other looms are deliberately treated fixed to reveal what has to be
# staged before HDMI-only removal. This is not a service sequence approval.
for dy in range(2,61,2):check('both_unplugged',dy)

heads={c['id']:box(bounds(c['box'])) for c in data['connectors'] if c['id'] in ('p_hdmi_pi','p_hdmi_evf')}
head_checks=[]
for dy in range(0,61,2):
 for name,head in heads.items():
  moved=head.translate(V(0,dy,6 if name=='p_hdmi_pi' else -6));hits=[]
  for n,s in objects.items():
   if not overlaps(bb(moved),ob[n]):continue
   v=0.
   for piece in candidates(n,bb(moved)):
    v=moved.intersect(piece).Volume()
    if v>1e-6:break
   if v>1e-6:hits.append(dict(obstacle=n,overlap_mm3=v))
  if hits:head_checks.append(dict(head=name,shift_y_mm=dy,hits=hits))

# Direct corrected pin/body clearance in installed shape. Finite solid-distance
# checks only on cells whose expanded bounding box is near the switch.
def cy(rad,y0,y1,x,z):return cq.Solid.makeCylinder(rad,y1-y0,V(x,y0,z),V(0,1,0))
switch_parts={'body':cy(13.75,11.1,25.2,-111,80)}
for k in range(1,13):
 t=math.radians(255-30*(k-1));switch_parts['pin_'+str(k)]=cy(.85,7.1,11.1,-111+11.1*math.cos(t),80+11.1*math.sin(t))
pin_clearances=[]
for name,s in switch_parts.items():
 b=bb(s);wide=[x+(-2 if i%2==0 else 2) for i,x in enumerate(b)];minimum=math.inf;near=0
 for i,seg in enumerate(data['hdmi_installed']['segments']):
  if not overlaps(bounds(seg['box']),wide):continue
  c=material_cache.get(('installed',i))
  if c is None:c=cell(seg['vertices']);material_cache[('installed',i)]=c
  if c is None:continue
  minimum=min(minimum,c.distance(s));near+=1
 pin_clearances.append(dict(part=name,min_distance_mm=minimum if math.isfinite(minimum) else None,nearby_cells=near,scope='distance for cells within 2 mm expanded component box'))

result=dict(status='Geometry context study; physical and full-stock service gates remain open',
 input_sha256=digest(P/'input.json'),context_sha256=digest(P/'context.json'),source_sha256=digest(Path(__file__)),collision_reporting='First positive cell/solid witness per object per pose; all non-hit objects fully checked. Compound solids receive exact individual narrow-phase tests.',
 corrected_fps_context_sha256=digest(P/'corrected-fps-context-0528.json'),
 object_notes=object_notes,static_and_removal_checks=checks,hard_head_removal_checks=head_checks,installed_switch_clearances=pin_clearances,
 physical_qualified=False,remaining=['Legacy FPS route is superseded by separate corrected-switch/pair study; its hits are not silently waived',
 'Camera FPC has no full 16 mm developable geometry or complete stored 200 mm stock; generous envelope hits are unresolved, not exact material contact',
 'USB, power button, OLED and other reservation boxes do not constitute modeled complete stock or a staging procedure',
 'Every listed crossing loom must be explicitly staged/released before HDMI-only extraction',
 'Terminal and adapter dimensions, neutral axis, real laminate thickness/radius, EMI, retention, lengths and mechanical tolerances unmeasured',
 'Baseline 56 and M1 physical gates remain open'])
(P/'context-checks.json').write_text(json.dumps(result,indent=2))
print('Saved',P/'context-checks.json',flush=True)
