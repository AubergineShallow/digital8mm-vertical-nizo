import sys,os,json,copy,math,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(P),str(P.parent)]
from cv_io import read_text,write_text
ns={'__file__':str(P/'verify_harness_checks.py'),'__name__':'study_exact'};sys.argv=[ns['__file__']]
exec(compile(read_text(P/'verify_harness_checks.py').split('res = HR.run_all')[0],ns['__file__'],'exec'),ns)
H,R,HR,ST=map(ns.get,['H','R','HR','ST']);exact=ns['exact_hits'];base=copy.deepcopy(H['cables']['qt']['curve']);br=max(b['length'] for b in H['cables']['qt']['branches']);results=[]
for length in (240,250,260):
 lo,hi=35,55.2
 for _ in range(50):
  low=(lo+hi)/2;knots=copy.deepcopy(base['knots']);knots[1][2]=knots[2][2]=90.5;knots[3][2]=knots[4][2]=low;knots[5][2]=knots[6][2]=68.
  cv=R.rounded_path(knots,6.4,3,4,.2)
  if cv['errors']:raise ValueError(cv['errors'])
  if cv['rounded_length_mm']+br>length:lo=low
  else:hi=low
 hh=copy.deepcopy(H);hh['cables']['qt']['curve']=cv;hh['cables']['qt']['family']=dict(var='low',knots=(3,4),axis=2,bound=(35,55.2))
 row=HR.member_clearance(hh,R.rounded_path,'qt',low,set(ST.final_state()),hits=exact,installed=True)
 row.update(stock_length_mm=length,complete_longest_branch_and_main_mm=cv['rounded_length_mm']+br,knots=knots)
 print('stored QT',length,row['hits'],row['cable_overlaps'],flush=True);results.append(row)
targets=HR._targets(H,set(ST.final_state()),set(),(0,0,0),set());homes=[]
for name,bb in [('upper_class_housing',[-25.25,-17.75,-19.5,-8.5,15,35]),('expanded_reserve',[-33,-9,-24,-7,15,39.5])]:
 hits=exact({'type':'box','box':bb,'tol':.01},targets);homes.append(dict(name=name,box=bb,hits=hits,capacity_at_20pct_mm3=math.prod(bb[i+1]-bb[i] for i in (0,2,4))*.2));print('J2',name,hits,flush=True)
r=dict(scope='Exploratory static routing, not selected geometry; full QT stock lengths and strict source-bound exact sweeps. No service deformation or J2 mating-access proof.',manifest_sha256=ns['manifest_sha'],source_sha256={q:hashlib.sha256((P/q).read_bytes()).hexdigest() for q in ('signal_routes.py','harness_rules.py','verify_harness_checks.py','hdmi_routes.py')},stored_qt=results,j2_home_candidates=homes,remaining=['Stored QT family needs released minimum and service/guide-state integration before selection.', 'Actual QT splice sleeves and four-core bundle cross section remain unmodeled.', 'J2 exact SKU, root datums, housing exits, latch clearance, wire stock allocation and withdrawal stroke are unknown. A class bounding box cannot close those gates.'])
write_text(P/'corrective-study-2026-10-12/stored-qt-j2-study.json',json.dumps(r,indent=2)+'\n')
