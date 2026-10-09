"""Package the exact guide checkpoint, editable renderer and supplied mesh inputs."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import importlib.metadata as md,json,hashlib
G=Path(__file__).resolve().parent;V=G.parent;CAD=V.parent;REPO=CAD.parents[1]
OUT=G/'out-concealed-vents';target=OUT/'D2-vertical-concealed-vents-source-and-pages.zip'
receipt=json.loads((OUT/'guide-receipt.json').read_text())
if receipt.get('guide_identity')!='D2-vertical-concealed-vents-review':raise RuntimeError('Wrong guide identity')
from vent_guide_support import inspect_inputs
inspect_inputs(V,receipt['nominated_manifest_sha256'])
for name,digest in receipt['sources'].items():
 if hashlib.sha256((CAD/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Guide source changed after render: '+name)
if hashlib.sha256((OUT/'D2-vertical-concealed-vents-review.pdf').read_bytes()).hexdigest()!=receipt['guide_pdf_sha256']:raise RuntimeError('PDF no longer matches receipt')
for name,digest in receipt['page_images'].items():
 if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Guide image changed after render: '+name)
for name,digest in receipt['mesh_files'].items():
 if hashlib.sha256((V/'out/compact-kowa_lm6hc'/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Guide mesh changed after render: '+name)
paths=[CAD/name for name in receipt['sources']]
for name in ['build_guide_concealed_vents.py','software_lineart.py','raster.cpp','package_concealed_guide.py','README-CONCEALED-VENTS.md','STEP-REVIEW-CONCEALED-VENTS.md','vent_guide_support.py']:paths.append(G/name)
paths+=[OUT/name for name in receipt['page_images']]+[OUT/'D2-vertical-concealed-vents-review.pdf',OUT/'guide-receipt.json']
for name in ['model.py','export_candidate.py','ASSEMBLY-VERTICAL.md','BOM-VERTICAL.md','BOM-VERTICAL.csv','REVIEW.md','FPS-SERVICE-STUDY.md','power_geometry.py','vent_geometry.py','verify_shadow_plenum.py','verify_candidate.py','verify_hdmi.py','verify_power_service.py','verify_csi_access.py','verify_csi_source.py','verify_print_meshes.py','verify_wire_solids.py']:
 p=V/name
 if p.exists():paths.append(p)
M=V/'out/compact-kowa_lm6hc'
paths+=list((M/'meshes').glob('*.json'))
for p in M.glob('*.json'):
 if p.name!='ventilation-checks.json':paths.append(p)  # Angled trial report is historical, not selected plenum evidence.
for dirname in ['hdmi-corrected-ports-20261009-0623','hdmi-export17-selected-20261009-0704','hdmi-ck1044-clear-20261009-0524','power-yaw21-270-provisional','power-csi-clear-20261009-0358','fps-access-20261009-0402']:
 if not (V/'routing-snapshots'/dirname).exists():continue
 for p in (V/'routing-snapshots'/dirname).iterdir():
  if p.suffix in ('.json','.py','.md','.txt'):paths.append(p)
paths += [CAD/'guide/lineart.py',CAD/'fonts/DejaVuSans-Bold.ttf',CAD/'fonts/LICENSE-DejaVu.txt']
manifest=json.loads((M/'manifest.json').read_text())
for name,digest in manifest['sources'].items():
 p=CAD/name
 if p in paths and hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
  raise RuntimeError('Bundled CAD source differs from frozen export: '+name)
readme='''D2 vertical concealed-vent assembly and wiring review source bundle

Review only. All 56 inherited physical gates and M1 remain open.

This bundle rebuilds the pictorial guide from the included exported mesh snapshots.
It includes the PDF, all page PNGs, editable Python/C++ renderer, source hashes,
assembly/BOM context and candidate verification evidence.

Rebuild on Linux with Python 3.12 and g++:
  python -m venv .venv-guide
  .venv-guide/bin/pip install -r requirements-guide.txt
  .venv-guide/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 NOMINATED_HASH_FROM_RECEIPT

Read nominated_manifest_sha256 in guide-receipt.json and substitute that exact value for NOMINATED_HASH_FROM_RECEIPT.

This is a distinct guide identity. The original reviewed 29-page PDF is retained
separately. No purchased parts or extra production prints are introduced.

Use the same frozen inputs. The generator rejects mesh/source mismatches or
mid-render changes. No display server, printer, device or network service is used
when generating the guide. The C++ rasterizer is compiled locally from its source.

Geometry source files are included for provenance. This is a guide-only bundle;
the complete CAD project and fabrication exports are separate. Do not manufacture
or energize the camera from this review checkpoint.
'''
requirements='\n'.join(f'{p}=={md.version(p)}' for p in ['numpy','Pillow','reportlab','vtk'])+'\n'
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('START-HERE.txt',readme);z.writestr('requirements-guide.txt',requirements)
 for p in sorted({p.resolve() for p in paths}):
  if not p.is_file():raise FileNotFoundError(p)
  z.write(p,str(p.resolve().relative_to(REPO.resolve())))
with ZipFile(target) as z:
 bad=z.testzip()
 if bad:raise RuntimeError('Corrupt archive member: '+bad)
 print(json.dumps({'path':str(target),'files':len(z.namelist()),'bytes':target.stat().st_size,'validated':True}))
