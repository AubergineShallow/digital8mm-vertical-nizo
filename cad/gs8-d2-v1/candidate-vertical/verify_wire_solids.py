"""Conservative static power-wire capsules versus every saved material solid (printed, COTS and hardware).
FP-12 (VN-30): the 9ced753 version tested printed parts only. Keepouts are non-material and are listed as
exclusions. A capsule may touch its own declared terminal part only in one run contiguous from that wire end
(the pad/housing entry); every such run is listed with its length. Any other contact fails. Two planted fixtures
(a ball inside a hardware part and inside a COTS part) must be detected, or the report fails.
The polyline model, root omissions and flexible service remain explicitly gated.
"""
from cv_io import read_text, write_text
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN
from power_geometry import simplify,cylinder,ball
import wire_terminal_rules as WT  # fixup-1 (VN-30): bounded terminal entry runs
P=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--snapshot',required=True);ap.add_argument('--variant',default='compact-kowa_lm6hc');ap.add_argument('--out',default='',help='report path instead of out/<variant>/wire-solid-checks.json');a=ap.parse_args();src=Path(a.snapshot);d=json.loads(read_text(src));out=P/'out'/a.variant;mf=out/'manifest.json';mh=hashlib.sha256(mf.read_bytes()).hexdigest();m=json.loads(read_text(mf))
# Accept the standalone reconciled power structure, never silently a different route.
if 'cores' not in d:raise ValueError('Expected explicit power cores snapshot')
# Declared terminal part at each end of every wire part (start, end): snapshot roots/pads lie on the X1203 edge
# (root/source_assumed_pad z 63), the fuse sleeve and XT30 housing lie inside the xt30_pair proxy (snapshot fuse box
# and source_proxy_hits 'xt30_selected_housing'). Only these may be touched, and only from their own end.
TERMINALS={'positive_board_to_fuse':('x1203','xt30_pair'),'positive_fuse_to_housing':('xt30_pair','xt30_pair'),'negative_complete':('x1203','xt30_pair')}
sh={};excluded=[]
for r in m['rows']:
 n=r['id']
 if r['kind']=='keepout':excluded.append(dict(id=n,kind='keepout',reason='non-material reservation, not occupied hardware'));continue
 f=out/'step'/f'{n}.step'
 if hashlib.sha256(f.read_bytes()).hexdigest()!=m['files'][f'step/{n}.step']:raise ValueError('STEP binding mismatch:'+n)
 if n=='pi5':continue
 sh[n]=cq.importers.importStep(str(f)).val()
 if r['kind']=='printed' and (not sh[n].isValid() or len(sh[n].Solids()) != 1):raise ValueError('Static-wire check requires one valid printed solid: '+n)
# Pi: the verify_candidate.py component set (official_pi5_assembly.build_parts); pi5.step is hash-checked above.
sys.path.insert(0,str(P.parent))
import layout as PiL
import official_pi5_assembly as PiA
for cn,q in PiA.build_parts(PiL).items():sh['pi5/'+cn]=q
owner=lambda n:n.split('/')[0]
def bb(s):
 b=s.BoundingBox();return [b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
def overlap(a,b):return all(min(a[i+1],b[i+1])-max(a[i],b[i])>1e-7 for i in (0,2,4))
bs={n:bb(s) for n,s in sh.items()};faces={n:np.array([bb(f) for f in s.Faces()]) for n,s in sh.items()};classifiers={n:[BRepClass3d_SolidClassifier(q.wrapped) for q in s.Solids()] for n,s in sh.items()}
def inside(n,p):
 q=gp_Pnt(*p)
 for c in classifiers[n]:
  c.Perform(q,1e-7)
  if c.State()==TopAbs_IN:return True
 return False
def potential(n,b):
 if not overlap(bs[n],b):return False
 f=faces[n];mask=np.ones(len(f),dtype=bool)
 for i in (0,2,4):mask&=(np.minimum(f[:,i+1],b[i+1])-np.maximum(f[:,i],b[i]))>0
 if mask.any():return True
 p=gp_Pnt(*[(b[i]+b[i+1])/2 for i in (0,2,4)])
 for c in classifiers[n]:
  c.Perform(p,1e-7)
  if c.State()==TopAbs_IN or c.IsOnAFace():return True
 return False
def piece_hits(piece):
 b=bb(piece);out_={};tested=0
 for n,f in sh.items():
  if not potential(n,b):continue
  v=piece.intersect(f).Volume();tested+=1
  if v>.002:out_[owner(n)]=out_.get(owner(n),0)+v
 return out_,tested,b
rows=[];terminal_runs=[]
wire_parts=[dict(core,id=part['id'],core_id=core['id'],geometry_points=part['points']) for core in d['cores'] for part in core['flexible_wire_parts']]
for core in wire_parts:
 points=simplify(core['geometry_points'],.04);r=core['od_mm']/2+.04
 # Segment cylinders plus endpoint balls contain the whole polyline tube. Station = position along the polyline.
 pieces=[(i+.5,cylinder(a_,b_,r)) for i,(a_,b_) in enumerate(zip(points,points[1:])) if np.linalg.norm(np.array(a_)-np.array(b_))>1e-7]+[(float(j),ball(p,r)) for j,p in enumerate(points)]
 pieces.sort(key=lambda t:t[0])
 per=[];tested=0
 for k,(st,piece) in enumerate(pieces):
  if k%25==0:print(core['id'],'capsule piece',k,'/',len(pieces),flush=True)
  h,t,b=piece_hits(piece);tested+=t;per.append((st,h,b))
 term=TERMINALS[core['id']]
 # fixup-1 (VN-30): bounded entry runs (snapshot limits, named gates); runs from both ends of one part must not meet
 excl,runs,term_probs=WT.terminal_runs(per,points,core['id'],term,WT.entry_limits(d,core));terminal_runs+=runs
 hits=[dict(station=st,part=n,overlap_mm3=v,bbox=b) for k,(st,h,b) in enumerate(per) for n,v in h.items() if (k,n) not in excl]
 rows.append(dict(id=core['id'],status='pass' if not hits and not term_probs else 'fail',terminal_problems=term_probs,core_id=core['core_id'],original_points=len(core['geometry_points']),simplified_points=len(points),radius_mm=r,max_polyline_chord_deviation_mm=.04,exact_intersections=tested,hits=hits[:40],hit_count=len(hits),hit_parts=sorted({h['part'] for h in hits}),terminals=list(term),terminal_runs=[t for t in terminal_runs if t['wire']==core['id']],root_joint_omission_mm=core['unmodeled_root_joint_allowance_mm'],root_warning=core['root_warning']))
# fixup-1 (VN-30) fixture: a wire lying inside xt30_pair from end to end (both terminals xt30_pair) must fail the
# terminal rule, so a buried route can never pass as two terminal entries.
xb=bs['xt30_pair'];grid=[(xb[0]+(xb[1]-xb[0])*i_/8,xb[2]+(xb[3]-xb[2])*j_/8,xb[4]+(xb[5]-xb[4])*k_/8) for i_ in range(1,8) for j_ in range(1,8) for k_ in range(1,8)]
ins=[g_ for g_ in grid if inside('xt30_pair',g_)];inner=[]
if ins:
 c0=np.array(min(ins,key=lambda g_:np.linalg.norm(np.array(g_)-np.array([(xb[0]+xb[1])/2,(xb[2]+xb[3])/2,(xb[4]+xb[5])/2]))))
 best=None
 for ax_ in np.eye(3):  # longest chord through c0 along a bbox axis that stays inside (0.25 mm steps)
  ends=[]
  for sg_ in (-1,1):
   s_=0.
   while inside('xt30_pair',tuple(c0+sg_*(s_+.25)*ax_)):s_+=.25
   ends.append(c0+sg_*.8*s_*ax_)
  if best is None or np.linalg.norm(ends[1]-ends[0])>np.linalg.norm(best[1]-best[0]):best=ends
 inner=[list(map(float,best[0])),list(map(float,best[1]))] if np.linalg.norm(best[1]-best[0])>1. else []
if len(inner)<2:rows.append(dict(id='fixture_buried_xt30_wire',status='fail',error='no interior xt30_pair chord longer than 1 mm found'))
else:
 fx=[inner[0],inner[-1]];fr=.4
 fp=[(.5,cylinder(fx[0],fx[1],fr)),(0.,ball(fx[0],fr)),(1.,ball(fx[1],fr))];fp.sort(key=lambda t_:t_[0])
 fper=[(st,piece_hits(pc)[0],None) for st,pc in fp]
 fexcl,fruns,fprobs=WT.terminal_runs(fper,fx,'positive_fuse_to_housing',('xt30_pair','xt30_pair'),WT.entry_limits(d,dict(d['cores'][0],core_id=d['cores'][0]['id'])))
 rows.append(dict(id='fixture_buried_xt30_wire',status='pass' if fprobs else 'fail',planted_wire=[fx,fr],terminal_problems=fprobs,purpose='regression fixture: a wire inside xt30_pair end to end must fail the terminal rule'))
# Planted fixtures: the obstacle set must detect a capsule ball inside a hardware part and inside a COTS part.
kinds={r['id']:r['kind'] for r in m['rows']}
for kind in ('hardware','cots'):
 cand=[n for n in sorted(sh) if kinds.get(owner(n))==kind and '/' not in n]
 pick=next((n for n in cand if inside(n,tuple(sh[n].Center().toTuple()))),None)
 if pick is None:rows.append(dict(id='fixture_'+kind,status='fail',error='no %s part with an interior centroid'%kind));continue
 c=tuple(sh[pick].Center().toTuple());h,t,b=piece_hits(ball(c,.5))
 rows.append(dict(id='fixture_'+kind,status='pass' if pick in h else 'fail',planted_ball_mm=[list(c),.5],part=pick,detected=sorted(h),purpose='regression fixture: %s solids are in the obstacle set'%kind))
if hashlib.sha256(mf.read_bytes()).hexdigest()!=mh:raise ValueError('Manifest changed during check')
material=sorted({owner(n) for n in sh})
result=dict(status='pass' if all(r['status']=='pass' for r in rows) else 'fail',rows=rows,manifest_sha256=mh,snapshot_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),verification_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),helper_source_sha256=hashlib.sha256((P/'power_geometry.py').read_bytes()).hexdigest(),obstacles=material,obstacle_count=len(material),exclusions=excluded,terminal_rule='a wire may touch only its declared terminal part, in one run contiguous from that end, no longer than the declared max entry (snapshot figure, gate named); runs from both ends of one part must not meet; every run is listed in terminal_runs',terminal_rule_source_sha256=hashlib.sha256((P/'wire_terminal_rules.py').read_bytes()).hexdigest(),terminal_runs=terminal_runs,pi5_method='verify_candidate.py component set (official_pi5_assembly.build_parts); pi5.step hash-checked',physical_qualified=False,scope='Static power-wire conservative capsules versus every saved material solid (printed, COTS, hardware; FP-12 VN-30). Keepouts excluded as non-material. No socket/pad/contact waiver beyond the listed terminal entry runs, and no assertion that omitted root joints are solved. Wire-wire checks are separate source-envelope studies. Positive finished allocation includes rigid fuse/joint zone; it is not270mm copper plus fuse.',remaining_stop=['Full flexible withdrawal/staging','Real pad/pin/lug geometry and joint cut convention','Retention and abrasion','Supplier bend capability, hot drop and thermal tests'])
write_text(Path(a.out) if a.out else out/'wire-solid-checks.json',json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ('status','obstacle_count')}|{'rows':[(r['id'],r['status'],r.get('hit_parts')) for r in rows]}),flush=True);raise SystemExit(result['status']!='pass')
