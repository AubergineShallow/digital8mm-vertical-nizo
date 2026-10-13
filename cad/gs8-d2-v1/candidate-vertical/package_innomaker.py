"""Create a hash-indexed conditional-review archive; never implies physical release."""
from pathlib import Path
import hashlib,json,argparse,subprocess,sys
from zipfile import ZipFile,ZIP_DEFLATED
from cv_io import read_text
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT.parent.parent
OUT=HERE/'innomaker/out/compact-kowa_lm6hc'
CHECKS=HERE/'innomaker/checks/compact-kowa_lm6hc'
# Third-party files without a stated redistribution licence and exports containing the manufacturer camera
# geometry are never archived (they stay local; see .gitignore).
NOT_REDISTRIBUTED=('innomaker/fetch/','assembly.step','step/gs_camera.step','step/innomaker-as-supplied-reference.step','meshes/','renders/')
def redistributable(path):
 p=path.as_posix()
 return not any(('/'+n) in p or p.endswith('/'+n) for n in NOT_REDISTRIBUTED)
p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
m=json.loads(read_text(OUT/'manifest.json'));mh=sha(OUT/'manifest.json')
for rel,digest in m['sources'].items():
 if sha(ROOT/rel)!=digest:raise ValueError('Source changed: '+rel)
for rel,digest in m['files'].items():
 if sha(OUT/rel)!=digest:raise ValueError('CAD output changed: '+rel)
subprocess.run([sys.executable,str(HERE/'make_innomaker_records.py'),'--check'],check=True)
reports=['innomaker-checks.json','innomaker-stl-checks.json']
for name in reports:
 f=CHECKS/name
 if not f.exists():raise ValueError('Missing fresh report: '+name)
 r=json.loads(read_text(f))
 if r['manifest_sha256']!=mh:raise ValueError('Report belongs to different geometry: '+name)
 script='verify_innomaker.py' if name=='innomaker-checks.json' else 'verify_innomaker_stl.py'
 if r['validator_sha256']!=sha(HERE/script):raise ValueError('Validator changed: '+name)
 for rel,digest in r.get('header_sensitivity',{}).get('study_files_sha256',{}).items():
  if sha(CHECKS/rel)!=digest:raise ValueError('Study geometry changed: '+rel)
interpretation=json.loads(read_text(CHECKS/'innomaker-interpretation.json'))
for rel,digest in interpretation['input_sha256'].items():
 if sha((OUT if rel=='manifest.json' else CHECKS)/rel)!=digest:raise ValueError('Stale interpretation: '+rel)
if interpretation['producer_sha256']!=sha(HERE/'verify_innomaker_interpretation.py'):raise ValueError('Interpretation producer changed')
for f in (OUT/'renders').glob('*-receipt.json'):
 r=json.loads(read_text(f))
 if r['manifest_sha256']!=mh:raise ValueError('Stale render '+f.name)
 if r['renderer_sha256']!=sha(HERE/'render_innomaker.py'):raise ValueError('Renderer changed')
 if r['image_sha256']!=sha(f.with_name(f.name.replace('-receipt.json','.png'))):raise ValueError('Image changed')
files={}
def add(f):
 f=f.resolve()
 if not redistributable(f):return
 files[f.relative_to(REPO).as_posix()]=f
for rel in m['sources']:add(ROOT/rel)
add(HERE/'BOM-VERTICAL.csv')
for pattern in ('*innomaker*.py',):
 for f in HERE.glob(pattern):add(f)
for f in (HERE/'innomaker').rglob('*'):
 if f.is_file() and f.suffix not in ('.zip','.pyc') and '__pycache__' not in f.parts:add(f)
for name in ('README.md',):
 if (REPO/name).exists():add(REPO/name)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True,encoding='utf-8').strip()
index={'source_commit':commit,'baseline_commit':'a0bfed9f7ed88dad78ad1a5fcb6fc7504712b338','manifest_sha256':mh,'qualification':'HOLD: rear header dimensions and optical registration unknown; no physical release','scope':'Primary compact Kowa only; other variants pending','files':{n:sha(f) for n,f in sorted(files.items())}}
a.destination.parent.mkdir(parents=True,exist_ok=True)
with ZipFile(a.destination,'w',ZIP_DEFLATED,compresslevel=6) as z:
 for n,f in sorted(files.items()):z.write(f,n)
 z.writestr('PACKAGE-SHA256.json',json.dumps(index,indent=2)+'\n')
 z.writestr('START-HERE.txt','D2 INNOMAKER COLOUR IMX296 CONDITIONAL REVIEW FORK\n\nRead cad/gs8-d2-v1/candidate-vertical/innomaker/README.md and ASSEMBLY-AND-PRINT.md first.\n\nPrimary compact Kowa STEP/STL/renders and fresh hash-bound scoped checks are included. Real rear trigger/strobe headers are omitted from the manufacturer STEP; study prisms are explicit assumptions only. Actual fit, optical registration, assembly holder access, CSI routing and inherited physical/harness/QT gates remain open. Do not print or purchase on a claim of qualification. Other variants remain pending.\n\nThe archive includes all manifest-bound source inputs plus fork validation/render/record scripts. For the full project history use the separate incremental fork bundle atop baseline a0bfed9; inherited records are historical, not fresh evidence. PACKAGE-SHA256.json indexes the archived files.\n')
with ZipFile(a.destination) as z:
 if z.testzip():raise ValueError('Archive CRC failure')
 for name,digest in index['files'].items():
  if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError('Archive hash failure '+name)
print(json.dumps({'archive':str(a.destination),'bytes':a.destination.stat().st_size,'sha256':sha(a.destination),'files':len(files),'manifest_sha256':mh,'source_commit':commit},indent=2))
