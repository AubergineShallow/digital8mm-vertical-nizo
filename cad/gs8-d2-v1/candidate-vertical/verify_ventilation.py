"""Saved-STEP ventilation connectivity, concealment and local-land review; not airflow qualification."""
from pathlib import Path
import json,hashlib,math,time
import cadquery as cq
import vent_geometry as VG
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc';H=P/'history/reviewed-export18';mf=D/'manifest.json';mh=hashlib.sha256(mf.read_bytes()).hexdigest();m=json.loads(mf.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):
 p=D/'step'/(n+'.step');assert sha(p)==m['files']['step/'+n+'.step'];return cq.importers.importStep(str(p)).val()
s=read('tub');panel=read('panel');old=cq.importers.importStep(str(H/'tub.step')).val();op=cq.importers.importStep(str(H/'panel.step')).val();rows=[]
def ray(shape,a,b):return sum(e.Length() for e in shape.intersect(cq.Edge.makeLine(cq.Vector(*a),cq.Vector(*b))).Edges())
def add(id,passed,**kw):rows.append(dict(id=id,passed=bool(passed),**kw));print(json.dumps(rows[-1]),flush=True)
for name,shape in [('tub',s),('panel',panel)]:add(name+'_valid_single_solid',shape.isValid() and len(shape.Solids())==1,solids=len(shape.Solids()),volume_mm3=shape.Volume())
for i,x in enumerate((-86.5,-78.5,-70.5,-62.5)):
 v=ray(op,(x,24,30),(x,29,30));nv=ray(panel,(x,24,30),(x,29,30))
 add('old_panel_blind_groove_'+str(i),abs(v-.2)<.001,old_material_floor_mm=v,old_through_air=False)
 add('new_panel_full_skin_'+str(i),nv>=2.8-.001,new_material_mm=nv)
for group,x0,x1 in [('intake',-103,-68),('side_exhaust',-40,-32)]:
 for i,z in enumerate(VG.SIDE_Z):
  cut=VG.side_channel(x0,x1,z);iv=cut.intersect(s).Volume();x=(x0+x1)/2
  a=(x,VG.OUTER_Y-.05,z+VG.SIDE_H/2+VG.OUTER_Y-.05-VG.INNER_Y);b=(x,VG.INNER_Y+.05,z+VG.SIDE_H/2+.05)
  v=ray(s,a,b);zz=z+VG.SIDE_H/2+VG.OUTER_Y-VG.INNER_Y;blocked=ray(s,(x,VG.OUTER_Y-.05,zz),(x,VG.INNER_Y+.05,zz))
  add(f'{group}_{i}_full_cutter_clear',iv<1e-5,overlap_mm3=iv)
  add(f'{group}_{i}_through_path',v<1e-5,blocked_material_mm=v,path=[a,b])
  add(f'{group}_{i}_normal_sight_blocked',blocked>.1,material_span_mm=blocked,note='Normal broadside sight only; oblique viewing can reveal channel mouths')
 for i,z in enumerate(VG.SIDE_Z[:-1]):
  cy=(VG.OUTER_Y+VG.INNER_Y)/2;cz=(z+VG.SIDE_H+VG.SIDE_Z[i+1])/2+cy-VG.INNER_Y;t=2/math.sqrt(2)
  v=ray(s,((x0+x1)/2,cy-t,cz+t),((x0+x1)/2,cy+t,cz-t));add(f'{group}_{i}_normal_web',v>=1.6,measured_mm=v,expected_mm=(7-VG.SIDE_H)/math.sqrt(2))
for i,z in enumerate(VG.FRONT_Z):
 for j,(a,b) in enumerate(VG.FRONT_BANKS):
  cut=VG.front_channel(a,b,z);iv=cut.intersect(s).Volume();y=(a+b)/2
  pa=(-5.25,y,z+VG.FRONT_H/2+.05);pb=(.05,y,z+VG.FRONT_H/2-5.25)
  v=ray(s,pa,pb);zz=z+VG.FRONT_H/2-5.2;blocked=ray(s,(-5.25,y,zz),(.05,y,zz))
  add(f'front_{i}_{j}_full_cutter_clear',iv<1e-5,overlap_mm3=iv)
  add(f'front_{i}_{j}_through_path',v<1e-5,blocked_material_mm=v,path=[pa,pb])
  add(f'front_{i}_{j}_normal_sight_blocked',blocked>.1,material_span_mm=blocked,note='Front-normal sight only; mouths remain visible at oblique angles')
for i,z in enumerate(VG.FRONT_Z[:-1]):
 cx=-2.6;cz=(z+VG.FRONT_H+VG.FRONT_Z[i+1])/2-(cx+5.2);t=2/math.sqrt(2)
 v=ray(s,(cx-t,-10,cz-t),(cx+t,-10,cz+t));add(f'front_{i}_normal_web',v>=1.6,measured_mm=v,expected_mm=(7.5-VG.FRONT_H)/math.sqrt(2))
for id,a,b,minv in [('microSD_left_land',(-2.6,1,33),(-2.6,4,33),1.6),('microSD_right_land',(-2.6,5,33),(-2.6,9,33),1.6),('LL_collar_lateral_land',(-1,11,30),(-1,15,30),1.6),('optical_port_lower_land',(-4.5,0,36),(-4.5,0,43),1.6)]:
 v=ray(s,a,b);add(id,v>=minv,material_span_mm=v,minimum_mm=minv,probe=[a,b])
# Added material must stay outside the unchanged inner cavity; this excludes joints/roofs by0.1mm.
box=cq.Solid.makeBox(m['core_dimensions_mm'][0]-8,50.5,94.8,cq.Vector(-m['core_dimensions_mm'][0]+2.6,-25.4,2.6))
added=s.cut(old);iv=added.intersect(box).Volume();add('no_added_material_in_original_cavity',iv<1e-5,overlap_mm3=iv)
meta=VG.metadata();areas={'intake':meta['intake_normal_throat_mm2'],'side_exhaust':meta['side_exhaust_normal_throat_mm2'],'front_exhaust':meta['front_normal_throat_mm2']}
for k,baseline in [('intake',420),('side_exhaust',96),('front_exhaust',412.5)]:add(k+'_nominal_normal_throat',areas[k]>=baseline,normal_throat_mm2=areas[k],baseline_gross_mm2=baseline,note='Geometric free-throat comparison only; longer/bent ducts have additional losses')
result=dict(manifest_sha256=mh,verification_source_sha256=sha(Path(__file__)),vent_source_sha256=sha(P/'vent_geometry.py'),historical_tub_sha256=sha(H/'tub.step'),historical_panel_sha256=sha(H/'panel.step'),generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),summary={'pass':sum(r['passed'] for r in rows),'fail':sum(not r['passed'] for r in rows)},checks=rows,ventilation=meta,delta={'tub_volume_mm3':s.Volume()-old.Volume(),'panel_volume_mm3':panel.Volume()-op.Volume(),'printed_mass_proxy_delta_g':(s.Volume()-old.Volume()+panel.Volume()-op.Volume())*.00107*.85},physical_qualified=False,remaining='No sealed air domain, fan operating point, thermal/hand/slicer qualification or real cooler clearance pass. CSI remains an unsealed service bypass.')
assert sha(mf)==mh
(D/'ventilation-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['summary']),flush=True)
raise SystemExit(bool(result['summary']['fail']))
