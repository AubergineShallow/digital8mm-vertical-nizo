"""Package the exact guide checkpoint, editable renderer and supplied mesh inputs."""
import sys as _cvsys; _cvsys.path.append(str(__import__('pathlib').Path(__file__).resolve().parents[1]))  # candidate-vertical root: cv_io
from cv_io import read_text, rel_posix
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import importlib.metadata as md,json,hashlib
G=Path(__file__).resolve().parent;V=G.parent;CAD=V.parent;REPO=CAD.parents[1]
OUT=G/'out-concealed-vents';target=OUT/'D2-vertical-catch-QT-followup-f9704ac-source-and-pages.zip'
receipt=json.loads(read_text(OUT/'guide-receipt.json'))
if receipt.get('guide_identity')!='D2-vertical-catch-QT-followup-f9704ac':raise RuntimeError('Wrong guide identity')
from vent_guide_support import inspect_inputs
inspect_inputs(V,receipt['nominated_manifest_sha256'])
from followup_guide_support import inspect_variants
followup=inspect_variants(V)
from record_post_guide_check import verify_receipt
post_check=verify_receipt()
pdf=OUT/receipt['guide_pdf_filename']
qa_path=OUT/'visual-review-followup.json'
qa=json.loads(read_text(qa_path))
if (qa.get('status')!='pass' or qa.get('guide_receipt_sha256')!=hashlib.sha256((OUT/'guide-receipt.json').read_bytes()).hexdigest()
    or qa.get('guide_pdf_sha256')!=receipt['guide_pdf_sha256'] or qa.get('page_images')!=receipt['page_images']
    or qa.get('pages_inspected')!=receipt['page_count']):raise RuntimeError('Current complete-page visual review is required')
for name,digest in receipt['sources'].items():
 if hashlib.sha256((CAD/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Guide source changed after render: '+name)
if hashlib.sha256(pdf.read_bytes()).hexdigest()!=receipt['guide_pdf_sha256']:raise RuntimeError('PDF no longer matches receipt')
for name,digest in receipt['page_images'].items():
 if hashlib.sha256((OUT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Guide image changed after render: '+name)
for name,digest in receipt['mesh_files'].items():
 if hashlib.sha256((V/'out/compact-kowa_lm6hc'/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Guide mesh changed after render: '+name)
paths=[CAD/name for name in receipt['sources']]
bound_paths={p.resolve() for p in paths}
missing_followup=[str(p) for p in followup['files'] if p.resolve() not in bound_paths]
if missing_followup:raise RuntimeError('Guide receipt omits three-variant inputs: '+', '.join(missing_followup))
paths += [OUT/'post-guide-build-order-check.json',OUT/'post-guide-build-order-check.log',qa_path]
paths += [V/name for name in post_check['input_sha256']]
for name in ['build_guide_concealed_vents.py','software_lineart.py','raster.cpp','package_concealed_guide.py','README-CONCEALED-VENTS.md','STEP-REVIEW-CONCEALED-VENTS.md','vent_guide_support.py','followup_guide_support.py','run_with_numpy_raster.py','raster_numpy.py']:paths.append(G/name)
paths+=[OUT/name for name in receipt['page_images']]+[pdf,OUT/'guide-receipt.json']
for name in ['model.py','export_candidate.py','ASSEMBLY-VERTICAL.md','WIRING-VERTICAL.md','BOM-VERTICAL.md','BOM-VERTICAL.csv','REVIEW.md','FPS-SERVICE-STUDY.md','power_geometry.py','vent_geometry.py','verify_shadow_plenum.py','verify_candidate.py','verify_hdmi.py','verify_power_service.py','verify_csi_access.py','verify_csi_source.py','verify_print_meshes.py','verify_wire_solids.py']:
 p=V/name
 if p.exists():paths.append(p)
M=V/'out/compact-kowa_lm6hc'
paths+=list((M/'meshes').glob('*.json'))
# Current reports are supplied only through the guide's source bindings above.
# Do not sweep in unrelated or stale JSON receipts from an earlier checkpoint.
for dirname in ['hdmi-corrected-ports-20261009-0623','hdmi-export17-selected-20261009-0704','hdmi-ck1044-clear-20261009-0524','power-yaw21-270-provisional','power-csi-clear-20261009-0358','fps-access-20261009-0402']:
 if not (V/'routing-snapshots'/dirname).exists():continue
 for p in (V/'routing-snapshots'/dirname).iterdir():
  if p.suffix in ('.json','.py','.md','.txt'):paths.append(p)
paths += [CAD/'guide/lineart.py',CAD/'fonts/DejaVuSans-Bold.ttf',CAD/'fonts/LICENSE-DejaVu.txt']
manifest=json.loads(read_text(M/'manifest.json'))
for name,digest in manifest['sources'].items():
 p=CAD/name
 if p in paths and hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
  raise RuntimeError('Bundled CAD source differs from frozen export: '+name)
readme='''D2 catch and QT followup from f9704ac source bundle: BLOCKED REVIEW

Review only. All %d inherited physical gates and M1 remain open.

This bundle rebuilds the pictorial guide from the included exported mesh snapshots.
It includes the PDF, all page PNGs, editable Python/C++ renderer, source hashes,
assembly/BOM context and candidate verification evidence.
Main, print, print-mesh and catch evidence receipts plus mesh caches and part
STEP/STL inputs are included for all three variants. The mode is recorded per
variant: same-implementation rerun means a separate geometry recomputation;
saved-full-audit means rows derived from that current full main audit, with
source, STEP, policy and coverage validation and no geometry recomputation.
Detailed harness/service evidence applies only to compact Kowa; alternate
variants remain unqualified.

Rebuild on Linux with Python 3.12 and g++:
  python -m venv .venv-guide
  .venv-guide/bin/pip install -r requirements-guide.txt
  .venv-guide/bin/python cad/gs8-d2-v1/run_locked.py -- cad/gs8-d2-v1/candidate-vertical/guide/build_guide_concealed_vents.py --manifest-sha256 NOMINATED_HASH_FROM_RECEIPT

Read nominated_manifest_sha256 in guide-receipt.json and substitute that exact value for NOMINATED_HASH_FROM_RECEIPT.

This is a distinct guide identity. The original reviewed 29-page PDF is retained
separately, as is the independently reviewed 1b59395 delivery. This followup is a
distinct Library deliverable. No purchased substitutions are introduced by this
correction. Compact inventory is 10 physical prints in 9 CAD assembly rows: the
tub body and bonded stub are separate pieces. Original storage adds the sleeve.
Gauge and coupons are excluded. The separate two-piece bonded-catch local study
and its bound receipt are qualification aids; they do not qualify the whole-tub
0.5 N m case. Cure fixtures, adhesive process, per-build metrology and continuous
tolerance coverage remain unqualified. The installed-family QT length rule is
retained, with its failure visible.

Use the same frozen inputs. The generator rejects mesh/source mismatches or
mid-render changes. No display server, printer, device or network service is used
when generating the guide. The C++ rasterizer is compiled locally from its source.

Geometry source files are included for provenance. This is a guide-only bundle;
the complete CAD project and fabrication exports are separate. Do not manufacture
or energize the camera from this review checkpoint.
'''%(__import__('evidence_rules').inherited_gates(Path(__file__).resolve().parents[1])['open'])  # fixup-1 (VN-08)
requirements='\n'.join(f'{p}=={md.version(p)}' for p in ['numpy','Pillow','reportlab','vtk'])+'\n'
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('START-HERE.txt',readme);z.writestr('requirements-guide.txt',requirements)
 for p in sorted({p.resolve() for p in paths}):
  if not p.is_file():raise FileNotFoundError(p)
  z.write(p,rel_posix(p.resolve(),REPO.resolve()))
with ZipFile(target) as z:
 bad=z.testzip()
 if bad:raise RuntimeError('Corrupt archive member: '+bad)
 print(json.dumps({'path':str(target),'files':len(z.namelist()),'bytes':target.stat().st_size,'validated':True}))
