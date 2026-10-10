"""Bounded static diagnosis of saved-Pi versus distributed cooler witnesses.

No geometry is modified. Every result is tied to the nominated export and
source parts; a discrepancy is retained instead of declaring either method exact.
Run under the shared CAD lock.
"""
from cv_io import rel_posix, write_text
from pathlib import Path
import hashlib, json, sys, time
import cadquery as cq

ROOT = Path(__file__).resolve().parent
P = ROOT/'routing-snapshots/pi-cooler-union-diagnosis-20261009-0704'
P.mkdir(exist_ok=True)
OUT = ROOT/'out/compact-kowa_lm6hc'
EXPECTED = 'ed58af4220b6afebf3bf1d88d61a9f786f21fd717f74791387b613e62366be4b'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OUT/'manifest.json') == EXPECTED
assert not (P/'static-comparison.json').exists(), 'Never overwrite a named result'
sys.path.insert(0, str(ROOT.parent))
import layout as L
import official_pi5_assembly as A

def bb(s):
    if not s.Solids(): return None
    b = s.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]

def broad(a, b):
    return a and b and all(min(a[i+1], b[i+1])-max(a[i], b[i]) > 1e-7 for i in (0, 2, 4))

def describe(s):
    solids=s.Solids()
    solid_faces={f.hashCode() for q in solids for f in q.Faces()}
    return dict(volume_mm3=s.Volume(), bbox_mm=bb(s), valid=s.isValid(), solids=len(solids),
        summed_solid_volume_mm3=sum(q.Volume() for q in solids),
        shells=len(s.Shells()), faces=len(s.Faces()),
        free_face_count=sum(f.hashCode() not in solid_faces for f in s.Faces()))

def save(name, s):
    data = describe(s)
    if s.Solids():
        f = P/(name+'.step'); cq.exporters.export(s, str(f)); data['step_sha256'] = sha(f)
    return data

files = [ROOT/n for n in ('official_pi5_assembly.py','official_pi5_geometry.py','official_pi5_csi.py')]
files += [ROOT.parent/'layout.py', OUT/'manifest.json', OUT/'step/pi5.step', OUT/'step/cooler.step', ROOT/'out/source-components/pi5-corrected.json']
before = {rel_posix(f, ROOT.parent):sha(f) for f in files}
print('Load saved Pi, cooler, and named source parts', flush=True)
pi = cq.importers.importStep(str(OUT/'step/pi5.step')).val()
cooler = cq.importers.importStep(str(OUT/'step/cooler.step')).val()
parts = A.build_parts(L)
records = {}; pieces = []
for name, component in parts.items():
    r = dict(component=describe(component))
    if not broad(bb(component),bb(cooler)):
        r['result'] = 'disjoint_bounds'; records[name] = r; continue
    print('Component witness: '+name, flush=True)
    q = component.intersect(cooler)
    r['witness'] = save('component-'+name, q)
    print(json.dumps(dict(component=name,witness=r['witness'])),flush=True)
    if q.Volume() > 1e-10: pieces.append((name,q))
    records[name] = r
print('Fuse distributed intersection witnesses', flush=True)
distributed = pieces[0][1].fuse(*[q for _,q in pieces[1:]]) if len(pieces)>1 else pieces[0][1]
distributed_data = save('distributed-witness', distributed)
print('Direct saved Pi/cooler intersection', flush=True)
direct = pi.intersect(cooler)
direct_data = save('saved-pi-witness', direct)
print(json.dumps(dict(distributed=distributed_data,direct=direct_data)), flush=True)
print('Compare difference witnesses', flush=True)
extra = distributed.cut(direct)
missing = direct.cut(distributed)
differences = dict(distributed_only=save('distributed-only',extra),saved_only=save('saved-only',missing))
for name,q in pieces:
    print('Local saved-Pi membership: '+name, flush=True)
    outside = q.cut(pi)
    records[name]['outside_saved_pi'] = save('outside-saved-pi-'+name, outside)
    print(json.dumps(dict(component=name,outside_saved_pi=records[name]['outside_saved_pi'])),flush=True)
after = {rel_posix(f, ROOT.parent):sha(f) for f in files}
assert before == after, 'Source changed during diagnosis'
result = dict(generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
    mechanical_manifest_sha256=EXPECTED,source_sha256=after,verification_source_sha256=sha(Path(__file__)),
    pi=describe(pi),cooler=describe(cooler),components=records,
    distributed=distributed_data,direct=direct_data,differences=differences,
    agreement=max(extra.Volume(),missing.Volume())<.001,
    interpretation='Diagnostic only. Investigate any positive difference before treating the two CAD representations as identical occupied space.',
    physical_qualified=False)
write_text(P/'static-comparison.json', json.dumps(result,indent=2))
print(json.dumps(dict(agreement=result['agreement'],differences=differences)),flush=True)
