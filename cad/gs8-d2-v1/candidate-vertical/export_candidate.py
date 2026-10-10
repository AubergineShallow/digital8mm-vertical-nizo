"""Source-based CAD review export, never a fabrication release. Run through run_locked.py.
Deterministic (FP-03): fixed STEP header time, no wall-clock time recorded, sorted keys, mesh JSON rebuilt from
the saved STEP by export_cache.py, so two exports on the same platform and runtime are byte-identical."""
from cv_io import read_text, rel_posix, relpath_posix, write_text
import argparse,hashlib,json,sys,time,platform,importlib.metadata,os
from pathlib import Path
import cadquery as cq
import model
import export_cache as EC
p=argparse.ArgumentParser();p.add_argument('--storage',choices=['compact','original'],default='compact');p.add_argument('--lens',default='kowa_lm6hc');p.add_argument('--out',type=Path,help='output folder (default out/<storage>-<lens>); use a scratch folder to re-export without touching committed evidence');a=p.parse_args()
base=Path(__file__).resolve().parent;out=a.out.resolve() if a.out else base/'out'/f'{a.storage}-{a.lens}';out.mkdir(parents=True,exist_ok=True)
for n in ('step','stl','meshes'): (out/n).mkdir(exist_ok=True)
def geometry_sources():
 cache=base/'out/source-components/pi5-corrected.json'
 receipt=json.loads(read_text(cache))
 files=[base/n for n in ('model.py','vent_geometry.py','export_candidate.py','power_geometry.py','fps_geometry.py','structure_geometry.py','strap_route_proposal.py','fps_fixed_support.py','fps_pair_guide.py','official_pi5_geometry.py','official_pi5_csi.py','official_pi5_assembly.py','make_corrected_pi.py','cv_io.py','export_cache.py')]
 files += [base/'structural-review/j4_trial_geometry.py',model.PG.SOURCE,cache,cache.parent/receipt['file']]
 files += [model.ROOT/n for n in receipt['sources']]
 files += sorted(model.ROOT.glob('*.py'))+[model.ROOT/'fonts/DejaVuSans-Bold.ttf',model.ROOT.parent/'gs8-pxl-v3/cad-requirements-lock.txt']
 return list(dict.fromkeys(files))
sourcefiles=geometry_sources()
sources_before={relpath_posix(f,model.ROOT):hashlib.sha256(f.read_bytes()).hexdigest() for f in sourcefiles}
m=model.build(a.storage,a.lens);asm=cq.Assembly(name='D2_vertical_review');manifest=[]
print_poses={};written=set()
# Pre-flight (fixup-1): a file this run would not write would be bound as if current (output would depend on the
# folder's history). Checked against the planned names BEFORE anything is written, so a refusal leaves the folder as it was.
planned=EC.planned_export_files((n,r['kind']) for n,r in m['rows'].items())
leftover=EC.leftover_files(out,planned)
if leftover:raise RuntimeError('Output folder holds files this export would not write; remove them or export to a clean --out: '+', '.join(leftover))
written|=EC.write_licence_copies(out)  # FP-01 Raspberry Pi licence beside assembly.step and step/pi5.step
def print_pose(name,shape):
 face={'tub':'-Y','panel':'+Y','carrier':'+Y','lens_collar':'+X','centring_gauge':'-X'}.get(name,model.L.PARTS.get(name,{}).get('face_down','-Z'))
 ax,angle={'+X':((0,1,0),90),'-X':((0,1,0),-90),'+Y':((1,0,0),-90),'-Y':((1,0,0),90),'+Z':((1,0,0),180),'-Z':((0,0,1),0)}[face]
 sh=shape.rotate((0,0,0),ax,angle);b=sh.BoundingBox();move=(-b.xmin,-b.ymin,-b.zmin)
 sh=sh.translate(cq.Vector(*move));bb=sh.BoundingBox()
 print_poses[name]=dict(face_down=face,rotation_axis=ax,angle_deg=angle,translation_mm=move,footprint_mm=[bb.xlen,bb.ylen,bb.zlen],slicer_state='NOT RUN',physical_release=False)
 return sh
for name,row in m['rows'].items():
 s=row['shape'];kind=row['kind'];mat=EC.base_material(name,kind)
 color=(.6,.6,.58) if mat=='silver' else (.03,.03,.03)
 if kind!='keepout':asm.add(s,name=name,color=cq.Color(*color))
 EC.export_step(s,out/'step'/f'{name}.step');written.add(f'step/{name}.step')
 if kind=='printed':
  stock=m['collar_print_stock']['shape'] if name=='lens_collar' else s
  cq.exporters.export(print_pose(name,stock),str(out/'stl'/f'{name}.stl'),tolerance=.06,angularTolerance=.15);written.add(f'stl/{name}.stl')
 # Mesh JSON from the saved STEP (not the in-memory shape), so export_cache.py can rebuild it from tracked files.
 EC.write_mesh(out/'meshes'/f'{name}.json',name,kind,out/'step'/f'{name}.step');written.add(f'meshes/{name}.json')
 # Keep the in-memory tessellation the pre-FP-03 exporter made here: Shape.BoundingBox() uses a triangulation when
 # present, so bbox_mm (and complete_bbox_mm) keep their established values (dropping it shrank 39 of 45 boxes by up to 0.69 mm).
 s.tessellate(*EC.MESH_TOLERANCE)
 manifest.append({'id':name,'kind':kind,'mesh':f'{name}.json','bbox_mm':model.bounds(s),'volume_mm3':s.Volume(),'mass_est_g':row['mass'],'source':row['source'],'valid':s.isValid(),'solid_count':len(s.Solids()),'geometry_role':'non-material keepout' if kind=='keepout' else ('overlapping named source-component assembly' if name=='pi5' else 'material/source proxy'),'occupied_material_volume_mm3':0 if kind=='keepout' else (None if name=='pi5' else s.Volume()),'volume_semantics':'sum of overlapping solid volumes, not occupied material' if name=='pi5' else 'shape volume'})
 print(name,'exported',flush=True)
EC.save_assembly(asm,out/'assembly.step')
EC.export_step(m['gauge'],out/'step'/'centring_gauge.step');cq.exporters.export(print_pose('centring_gauge',m['gauge']),str(out/'stl'/'centring_gauge.stl'),tolerance=.06);written|={'step/centring_gauge.step','stl/centring_gauge.stl'}
# Post-check: the plan the pre-flight used must be exactly what was written, and nothing else appeared meanwhile.
if written!=planned:raise RuntimeError('Export plan and written files differ: '+', '.join(sorted(written^planned)))
leftover=EC.leftover_files(out,written)
if leftover:raise RuntimeError('Output folder holds files this export did not write: '+', '.join(leftover))
sourcefiles=geometry_sources()
sources={relpath_posix(f,model.ROOT):hashlib.sha256(f.read_bytes()).hexdigest() for f in sourcefiles}
sources=dict(sorted(sources.items()))
if sources != sources_before:raise RuntimeError('Geometry source changed during export; do not use this output')
bb=[min(r['bbox_mm'][i] for r in manifest if r['kind']!='keepout') if i%2==0 else max(r['bbox_mm'][i] for r in manifest if r['kind']!='keepout') for i in range(6)]
dims=[bb[i+1]-bb[i] for i in (0,2,4)];mass=sum(r['mass_est_g'] for r in manifest)
com=[]
for ki,k in enumerate(('x','y','z')):
    com.append(sum(r['mass_est_g']*(model.L.lens_spec(a.lens)['com'][ki] if r['id']=='lens' else getattr(m['rows'][r['id']]['shape'].Center(),k)) for r in manifest)/mass)
meta={'runtime':EC.runtime(),'determinism':EC.POLICY,'print_poses':print_poses,'revision':model.REV,'storage':a.storage,'lens':a.lens,'state':m['physical_state'],'built_utc':EC.UNRECORDED,'rows':manifest,'sources':sources,'core_dimensions_mm':[m['length'],m['width'],m['height']],'core_origin_mm':list(m['core_origin']),'ventilation':m['ventilation'],'complete_bbox_mm':bb,'complete_dimensions_mm':dims,'complete_bbox_volume_mm3':dims[0]*dims[1]*dims[2],'mass_est_g':mass,'com_est_mm':com,'grip_axis_x':model.L.GRIP['axis_x'],'com_offset_from_grip_mm':com[0]-model.L.GRIP['axis_x'],'qualification':'Computed geometry only. COTS proxies, mass and centre of mass are estimates. The legacy12g XT30/fused-pigtail mass is concentrated at its rigid proxy; other harness masses are excluded. The270mm16AWG distributed mass and actual weights remain unmeasured. No physical qualification claimed.'}
meta['fps_geometry']=m['fps_geometry']
meta['pi_source_geometry']=m['pi_source_geometry']
meta['joint_geometry']={'lip_mm':2.4,'head_mm':2.4,'axial_gap_mm':.25,'front_floor_min_mm':2.7,'physical_qualified':False}
meta['files']={rel_posix(f,out):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ('step','stl','meshes') for f in (out/folder).glob('*') if f.is_file() and f.name!='manifest.json'}
meta['files']['assembly.step']=hashlib.sha256((out/'assembly.step').read_bytes()).hexdigest()
meta['files'][EC.PI_LICENCE_COPY]=hashlib.sha256((out/EC.PI_LICENCE_COPY).read_bytes()).hexdigest()  # step/ copy is bound by the glob above
meta['files']=dict(sorted(meta['files'].items()))
write_text(out/'manifest.json',json.dumps(meta,indent=2));write_text(out/'meshes'/'manifest.json',json.dumps(meta,indent=2))
print(json.dumps({k:v for k,v in meta.items() if k not in ('rows','sources')},indent=2))
