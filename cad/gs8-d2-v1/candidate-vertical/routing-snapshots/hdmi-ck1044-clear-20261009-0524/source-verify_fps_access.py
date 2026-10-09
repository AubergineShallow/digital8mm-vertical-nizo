"""Bound FPS access study to saved STEP and analytic full-diameter wire sweeps.
No own-root contacts, retained guides, connector latch, or physical loads are waived.
Run only through ../run_locked.py, using the pinned CAD interpreter.
"""
import argparse, hashlib, json, math, time
from pathlib import Path
import cadquery as cq
V=cq.Vector
ROOT=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def overlaps(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-8 for i in (0,2,4))
def box(b):return cq.Solid.makeBox(b[1]-b[0],b[3]-b[2],b[5]-b[4],V(b[0],b[2],b[4]))
def bbox(d):return [v for k in 'xyz' for v in d[k]]
def rounded_wire(c):
 if c['errors']:raise ValueError(c['errors'])
 pts=[V(*p) for p in c['knots']];rad=c['centerline_radius_mm'];last=pts[0];edges=[]
 def line(a,b):
  if (b-a).Length>1e-8:edges.append(cq.Edge.makeLine(a,b))
 for i in range(1,len(pts)-1):
  angle=math.radians(c['turn_degrees'][i])
  if angle<1e-8:continue
  u=(pts[i]-pts[i-1]).normalized();v=(pts[i+1]-pts[i]).normalized();trim=c['corner_trim_mm'][i]
  enter=pts[i]-u*trim;leave=pts[i]+v*trim;center=pts[i]+(v-u).normalized()*(rad/math.cos(angle/2))
  middle=center+(enter-center)*math.cos(angle/2)+u*(rad*math.sin(angle/2))
  line(last,enter);edges.append(cq.Edge.makeThreePointArc(enter,middle,leave));last=leave
 line(last,pts[-1]);w=cq.Wire.assembleEdges(edges)
 if abs(w.Length()-c['rounded_length_mm'])>1e-6:raise ValueError('Analytic route length mismatch')
 return w,pts[0],(pts[1]-pts[0]).normalized()
def tube(c,od):
 w,p,n=rounded_wire(c);profile=cq.Wire.makeCircle(od/2,p,n);s=cq.Solid.sweep(profile,[],w,makeSolid=True,isFrenet=False)
 if not s.isValid():raise ValueError('Invalid analytic FPS swept tube')
 expected=w.Length()*math.pi*(od/2)**2
 if abs(s.Volume()-expected)>1e-4:raise ValueError('Unexpected swept wire volume')
 return s,w

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--variant',default='compact-kowa_lm6hc');ap.add_argument('--snapshot',default='fps-access-20261009-0402');ap.add_argument('--poses',default='all');ap.add_argument('--label',default='saved-fps');ap.add_argument('--allow-invalid-diagnostic',action='store_true');a=ap.parse_args()
 sd=ROOT/'routing-snapshots'/a.snapshot;mp=ROOT/'out'/a.variant/'manifest.json';mh=digest(mp);m=json.loads(mp.read_text());sm=json.loads((sd/'manifest.json').read_text());src=sd/'twenty-one-full-wire-shapes.json';data=json.loads(src.read_text())
 for n,h in sm['files'].items():
  if digest(sd/n)!=h:raise ValueError('Snapshot hash mismatch: '+n)
 stale_sources=[n for n,h in m['sources'].items() if digest(ROOT.parent/n)!=h]
 invalid_rows=[dict(id=r['id'],valid=r['valid'],solid_count=r['solid_count']) for r in m['rows'] if r['kind']=='printed' and (not r['valid'] or r['solid_count']!=1)]
 if (stale_sources or invalid_rows) and not a.allow_invalid_diagnostic:raise ValueError('Rejected mechanical input: '+str(dict(stale_sources=stale_sources,invalid_printed_rows=invalid_rows)))
 rows={r['id']:r for r in m['rows']};sh={};step_hashes={}
 for n in rows:
  p=mp.parent/'step'/f'{n}.step';h=digest(p)
  if h!=m['files'][f'step/{n}.step']:raise ValueError('STEP hash mismatch: '+n)
  sh[n]=cq.importers.importStep(str(p)).val();step_hashes[n]=h
 moving={'panel','encoder','switch_1824','knob_exp','knob_fps','power_button','power_nut_reserve','foam_pad'}
 # Panel screws are removed at the first step; their tub bosses remain exact STEP material.
 fixed={n:s for n,s in sh.items() if n not in moving and not n.startswith('p_panel')}
 # Exact geometric crop removes irrelevant floor pockets, never inferred empty material.
 crop=box([-153,-77,-27,60,7,105]);cropped={}
 for n,s in {**fixed,**{n:sh[n] for n in moving}}.items():
  if not overlaps(bb(s),bb(crop)):continue
  b=bb(s)
  cropped[n]=s.intersect(crop) if any(b[i]<bb(crop)[i]-.001 if i%2==0 else b[i]>bb(crop)[i]+.001 for i in range(6)) else s
  print('Loaded/cropped',n,flush=True)
 result=dict(status='running',physical_qualified=False,mechanical_input_acceptable=not(stale_sources or invalid_rows),stale_sources=stale_sources,invalid_printed_rows=invalid_rows,diagnostic_only=a.allow_invalid_diagnostic,source_sha256=digest(Path(__file__)),snapshot_sha256=digest(src),snapshot_manifest_sha256=digest(sd/'manifest.json'),mechanical_manifest_sha256=mh,mechanical_built_utc=m.get('built_utc'),mechanical_sources=m['sources'],step_sha256=step_hashes,wire_representation='Exact cylinders and circular corner arcs swept at nominal full wire OD, planar end faces; no endpoint waivers.',checks=[],access_studies=[],remaining_gates=['Actual PH purchased geometry, two housings, key and latch orientation, separation stroke and root datums','Support carried through all poses without traction on crimp wires; no supported carrier geometry is present','Printed guide attachment, release and retention absent','Other moving panel wires and complete full-width camera FPC service states','Tolerances, material bend strain and fatigue, real tool jaw dimensions and grip force','Electrical isolation and physical assembly/disassembly trial'])
 out=ROOT/'out'/'fps-service-study';out.mkdir(exist_ok=True);dest=out/f'{a.label}-checks.json'
 def save():dest.write_text(json.dumps(result,indent=2))
 indices=list(range(len(data['shapes']))) if a.poses=='all' else [int(v) for v in a.poses.split(',')]
 exact=0
 for i in indices:
  pose=data['shapes'][i];shift=pose['panel_shift_y_mm'];print('FPS pose',i,'panel +Y',shift,flush=True)
  obstacles={n:s.translate(V(0,shift,0)) if n in moving else s for n,s in cropped.items()}
  obs_bounds={n:bb(s) for n,s in obstacles.items()};items={}
  for wire in pose['wire_parts']:
   items[wire['id']]=tube(wire['curve'],wire['od_mm'])[0]
  items['fps_ph_pair']=box(bbox(pose['junction']['box']))
  for name,s in items.items():
   hits=[];clearances=[];sb=bb(s)
   for n,f in obstacles.items():
    # True minimum distance is reported for nearby same-space parts only.
    if not overlaps(sb,obs_bounds[n]):continue
    d=s.distance(f);v=0.
    if d<1e-7:
     common=s.intersect(f);v=common.Volume();exact+=1
     if v>1e-6:hits.append(dict(part=n,kind=rows[n]['kind'],overlap_mm3=v,bbox_mm=bb(common)))
    clearances.append(dict(part=n,minimum_gap_mm=d,overlap_mm3=v))
   check=dict(pose=i,panel_shift_y_mm=shift,junction_shift_y_mm=pose['junction_shift_y_mm'],item=name,status='fail' if hits else 'pass',hits=hits,nearby_clearances=clearances)
   result['checks'].append(check);print(json.dumps(check),flush=True);save()
  # Test hypothesized straight +Y grasp only. Does not stand in for real PH jaws.
  if i in (0,20):
   b=bbox(pose['junction']['box']);cx=(b[0]+b[1])/2;cz=(b[4]+b[5])/2
   studies={
    'two_2mm_side_jaws_straight_plus_y':cq.Compound.makeCompound([box([b[0]-2,b[0]-.1,b[2]+1,55,cz-2,cz+2]),box([b[1]+.1,b[1]+2,b[2]+1,55,cz-2,cz+2])]),
    'finger_pair_35x22x26_at_pair':box([cx-17.5,cx+17.5,b[2]-5,b[2]+17,cz-13,cz+13]),
    'support_saddle_1mm_under_pair':box([b[0]-.5,b[1]+.5,b[2],b[3],b[4]-1,b[4]-.05])}
   for name,tool in studies.items():
    hits=[]
    for n,f in obstacles.items():
     if not overlaps(bb(tool),obs_bounds[n]):continue
     common=tool.intersect(f);v=common.Volume();exact+=1
     if v>1e-6:hits.append(dict(part=n,overlap_mm3=v,bbox_mm=bb(common)))
    result['access_studies'].append(dict(pose=i,study=name,status='blocked' if hits else 'proxy_clear_only',hits=hits,qualification='Hypothesis envelope, not measured hardware or complete support/release mechanism.'))
   save()
 if digest(mp)!=mh:raise ValueError('Manifest changed during verification')
 for n,h in step_hashes.items():
  if digest(mp.parent/'step'/f'{n}.step')!=h:raise ValueError('STEP changed during verification: '+n)
 result['status']='diagnostic_fail' if a.allow_invalid_diagnostic and any(r['status']=='fail' for r in result['checks']) else 'diagnostic_only' if a.allow_invalid_diagnostic else 'fail' if any(r['status']=='fail' for r in result['checks']) else 'geometric_pass_only';result['summary']={k:sum(r['status']==k for r in result['checks']) for k in ('pass','fail')};result['exact_intersections']=exact;result['completed_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save();print(json.dumps(dict(result=result['status'],summary=result['summary'],path=str(dest))),flush=True)
 return int(result['status']=='fail')
if __name__=='__main__':raise SystemExit(main())
