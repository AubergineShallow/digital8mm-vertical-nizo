"""Saved-assembly mouth continuation checks, separate from the tub-only audit.

Run through run_locked.py. These finite 12 mm rectangular continuations test
nominal saved material only; they do not model hands, air flow or physical fit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time

import cadquery as cq

P = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=P / 'out/compact-kowa_lm6hc')
args = parser.parse_args()
D = args.out


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def overlap(a, b):
    return all(min(a[i+1], b[i+1])-max(a[i], b[i]) > 1e-7 for i in (0, 2, 4))


mf = D / 'manifest.json'
mh = sha(mf)
m = json.loads(mf.read_text())
assert m.get('ventilation', {}).get('revision', '').startswith('shadow-gap')
length = m['core_dimensions_mm'][0]
sources = {name: sha(P / name) for name in ('model.py', 'vent_geometry.py')}
for name, value in sources.items():
    assert m['sources']['candidate-vertical/' + name] == value, 'Source-stale export: ' + name

inventory = {}
excluded = []
for row in m['rows']:
    name = row['id']
    if row['kind'] == 'keepout' or name == 'tub':
        excluded.append(dict(id=name, reason='Tub is the aperture owner' if name == 'tub' else 'Non-material reservation'))
        continue
    path = D / 'step' / (name + '.step')
    expected = m['files']['step/' + name + '.step']
    assert sha(path) == expected, 'Saved STEP hash mismatch: ' + name
    shape = cq.importers.importStep(str(path)).val()
    assert shape.isValid(), 'Invalid saved material: ' + name
    inventory[name] = dict(shape=shape, bounds=bounds(shape), sha256=expected)

prisms = {
    'hot_front': [0.01, 12., -34., -28., 5., 40.],
    'cold_rear': [-length-12., -length-.01, -34., -28., 5., 75.],
    'cold_underside': [-length+4., -83., -34., -28., -12., -.01],
    'hot_underside': [-59., -5., -34., -28., -12., -.01],
}
checks = []
for name, b in prisms.items():
    prism = cq.Solid.makeBox(b[1]-b[0], b[3]-b[2], b[5]-b[4], cq.Vector(b[0], b[2], b[4]))
    queries, hits = [], []
    for part, data in inventory.items():
        if not overlap(b, data['bounds']):
            continue
        witness = prism.intersect(data['shape'])
        volume = witness.Volume()
        item = dict(part=part, overlap_mm3=volume, saved_material_bbox_mm=data['bounds'])
        queries.append(item)
        if volume > .002:
            item = dict(item, witness_bbox_mm=bounds(witness))
            hits.append(item)
    row = dict(id=name, status='fail' if hits else 'pass', continuation_bounds_mm=b,
               material_inventory_count=len(inventory), exact_queries=queries,
               bounding_box_rejected_count=len(inventory)-len(queries), hits=hits,
               tolerance_mm3=.002)
    checks.append(row)
    print(json.dumps(row), flush=True)

assert sha(mf) == mh, 'Manifest changed during context check'
assert all(sha(P / n) == h for n, h in sources.items()), 'Source changed during context check'
result = dict(manifest_sha256=mh, verification_source_sha256=sha(Path(__file__)),
              checked_source_sha256=sources,
              saved_material_sha256={name: data['sha256'] for name, data in inventory.items()},
              generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              summary={k: sum(row['status'] == k for row in checks) for k in ('pass', 'fail')},
              checks=checks, exclusions=excluded, physical_qualified=False,
              scope='Exact finite outward mouth prisms versus all other saved material rows; actual saved-shape AABBs used only to reject separated pairs',
              limitations=['Only the specified first 12 mm beyond each exterior face are checked.',
                           'No hand/finger/garment, desk contact or airflow streamlines are modeled.',
                           'COTS proxies, real parts, flexible looms, print deformation and thermal performance remain unqualified.',
                           'Clear outward prisms do not prove whole-plenum pressure loss, external recirculation or all-view concealment.'])
(D / 'shadow-outlet-context-checks.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result['summary']), flush=True)
raise SystemExit(bool(result['summary']['fail']))
