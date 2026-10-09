"""Source-based CAD review export, never a fabrication release. Run through run_locked.py."""
import argparse,hashlib,json,sys,time,platform,importlib.metadata,os
from pathlib import Path
import cadquery as cq
import model
p=argparse.ArgumentParser();p.add_argument('--storage',choices=['compact','original'],default='compact');p.add_argument('--lens',default='kowa_lm6hc');a=p.parse_args()
base=Path(__file__).resolve().parent;out=base/'out'/f'{a.storage}-{a.lens}';out.mkdir(parents=True,exist_ok=True)
for n in ('step','stl','meshes'): (out/n).mkdir(exist_ok=True)
def geometry_sources():
 cache=base/'out/source-components/pi5-corrected.json'
 receipt=json.loads(cache.read_text())
 files=[base/n for n in ('model.py','vent_geometry.py','export_candidate.py','power_geometry.py','fps_geometry.py','structure_geometry.py','strap_route_proposal.py','fps_fixed_support.py','fps_pair_guide.py','official_pi5_geometry.py','official_pi5_csi.py','official_pi5_assembly.py','make_corrected_pi.py')]
 files += [base/'structural-review/j4_trial_geometry.py',model.PG.SOURCE,cache,cache.parent/receipt['file']]
 files += [model.ROOT/n for n in receipt['sources']]
 files += list(model.ROOT.glob('*.py'))+[model.ROOT/'fonts/DejaVuSans-Bold.ttf',model.ROOT.parent/'gs8-pxl-v3/cad-requirements-lock.txt']
 return list(dict.fromkeys(files))
sourcefiles=geometry_sources()
sources_before={os.path.relpath(f,model.ROOT):hashlib.sha256(f.read_bytes()).hexdigest() for f in sourcefiles}
m=model.build(a.storage,a.lens);asm=cq.Assembly(name='D2_vertical_review');manifest=[]
print_poses={}
def print_pose(name,shape):
 face={'tub':'-Y','panel':'+Y','carrier':'+Y','lens_collar':'+X','centring_gauge':'-X'}.get(name,model.L.PARTS.get(name,{}).get('face_down','-Z'))
 ax,angle={'+X':((0,1,0),90),'-X':((0,1,0),-90),'+Y':((1,0,0),-90),'-Y':((1,0,0),90),'+Z':((1,0,0),180),'-Z':((0,0,1),0)}[face]
 sh=shape.rotate((0,0,0),ax,angle);b=sh.BoundingBox();move=(-b.xmin,-b.ymin,-b.zmin)
 sh=sh.translate(cq.Vector(*move));bb=sh.BoundingBox()
 print_poses[name]=dict(face_down=face,rotation_axis=ax,angle_deg=angle,translation_mm=move,footprint_mm=[bb.xlen,bb.ylen,bb.zlen],slicer_state='NOT RUN',physical_release=False)
 return sh
for name,row in m['rows'].items():
 s=row['shape'];kind=row['kind'];mat='silver' if name in ('tub','panel') else 'black'
 if kind in ('cots','hardware'):mat={'pi5':'pcb','x1203':'pcb','evf_board':'pcb','encoder':'pcb','cooler':'metal','x1203_kit':'brass','lens':'lens','eyepiece':'lens','hmx039':'glass','pack':'battery','xt30_pair':'connector','run_button':'red','tripod_nut':'metal','strap':'strap','foam_pad':'rubber'}.get(name,'metal' if kind=='hardware' else 'black')
 if name=='eyecup':mat='rubber'
 color=(.6,.6,.58) if mat=='silver' else (.03,.03,.03)
 if kind!='keepout':asm.add(s,name=name,color=cq.Color(*color))
 if kind=='printed':
  pass
 cq.exporters.export(s,str(out/'step'/f'{name}.step'))
 if kind=='printed':
  stock=m['collar_print_stock']['shape'] if name=='lens_collar' else s
  cq.exporters.export(print_pose(name,stock),str(out/'stl'/f'{name}.stl'),tolerance=.06,angularTolerance=.15)
 vv,ff=s.tessellate(.07,.15);vs=[[v.x,v.y,v.z] for v in vv];fs=[list(f) for f in ff]
 mats=[]
 for f in fs:
  pts=[vs[i] for i in f];vmat=mat
  if name=='panel' and all(abs(q[1]-27.6)<.008 for q in pts):vmat='paint_black'
  if name=='knob_fps' and all(abs(q[1]-36.6)<.008 for q in pts):vmat='paint_white'
  if name=='encoder' and all(q[1]>25.2 for q in pts):vmat='metal'
  mats.append(vmat)
 mesh={'id':name,'kind':kind,'vertices':vs,'faces':fs,'materials':mats}
 (out/'meshes'/f'{name}.json').write_text(json.dumps(mesh,separators=(',',':')))
 manifest.append({'id':name,'kind':kind,'mesh':f'{name}.json','bbox_mm':model.bounds(s),'volume_mm3':s.Volume(),'mass_est_g':row['mass'],'source':row['source'],'valid':s.isValid(),'solid_count':len(s.Solids()),'geometry_role':'non-material keepout' if kind=='keepout' else ('overlapping named source-component assembly' if name=='pi5' else 'material/source proxy'),'occupied_material_volume_mm3':0 if kind=='keepout' else (None if name=='pi5' else s.Volume()),'volume_semantics':'sum of overlapping solid volumes, not occupied material' if name=='pi5' else 'shape volume'})
 print(name,'exported',flush=True)
asm.save(str(out/'assembly.step'))
cq.exporters.export(m['gauge'],str(out/'step'/'centring_gauge.step'));cq.exporters.export(print_pose('centring_gauge',m['gauge']),str(out/'stl'/'centring_gauge.stl'),tolerance=.06)
sourcefiles=geometry_sources()
sources={os.path.relpath(f,model.ROOT):hashlib.sha256(f.read_bytes()).hexdigest() for f in sourcefiles}
if sources != sources_before:raise RuntimeError('Geometry source changed during export; do not use this output')
bb=[min(r['bbox_mm'][i] for r in manifest if r['kind']!='keepout') if i%2==0 else max(r['bbox_mm'][i] for r in manifest if r['kind']!='keepout') for i in range(6)]
dims=[bb[i+1]-bb[i] for i in (0,2,4)];mass=sum(r['mass_est_g'] for r in manifest)
com=[]
for ki,k in enumerate(('x','y','z')):
    com.append(sum(r['mass_est_g']*(model.L.lens_spec(a.lens)['com'][ki] if r['id']=='lens' else getattr(m['rows'][r['id']]['shape'].Center(),k)) for r in manifest)/mass)
meta={'runtime':{'python':platform.python_version(),'cadquery':cq.__version__,'cadquery_ocp':importlib.metadata.version('cadquery-ocp')},'print_poses':print_poses,'revision':model.REV,'storage':a.storage,'lens':a.lens,'state':m['physical_state'],'built_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'rows':manifest,'sources':sources,'core_dimensions_mm':[m['length'],m['width'],m['height']],'core_origin_mm':list(m['core_origin']),'ventilation':m['ventilation'],'complete_bbox_mm':bb,'complete_dimensions_mm':dims,'complete_bbox_volume_mm3':dims[0]*dims[1]*dims[2],'mass_est_g':mass,'com_est_mm':com,'grip_axis_x':model.L.GRIP['axis_x'],'com_offset_from_grip_mm':com[0]-model.L.GRIP['axis_x'],'qualification':'Computed geometry only. COTS proxies, mass and centre of mass are estimates. The legacy12g XT30/fused-pigtail mass is concentrated at its rigid proxy; other harness masses are excluded. The270mm16AWG distributed mass and actual weights remain unmeasured. No physical qualification claimed.'}
meta['fps_geometry']=m['fps_geometry']
meta['pi_source_geometry']=m['pi_source_geometry']
meta['joint_geometry']={'lip_mm':2.4,'head_mm':2.4,'axial_gap_mm':.25,'front_floor_min_mm':2.7,'physical_qualified':False}
meta['files']={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ('step','stl','meshes') for f in (out/folder).glob('*') if f.is_file() and f.name!='manifest.json'}
meta['files']['assembly.step']=hashlib.sha256((out/'assembly.step').read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(meta,indent=2));(out/'meshes'/'manifest.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({k:v for k,v in meta.items() if k not in ('rows','sources')},indent=2))
