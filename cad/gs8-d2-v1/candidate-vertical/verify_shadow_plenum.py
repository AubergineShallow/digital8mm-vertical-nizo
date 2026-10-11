"""Independent saved-STEP shadow-plenum review. Run through run_locked.py.

This measures named sections and finite paths. It does not establish a global
minimum flow area, fan operating point, printability, strength or cooling.
The older diagonal-channel verifier is deliberately left unchanged.
"""
from cv_io import read_text, write_text
from pathlib import Path
import argparse
import hashlib
import json
import math
import time

import cadquery as cq
import vent_geometry as VG

P = Path(__file__).resolve().parent
V = cq.Vector
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=P / 'out/compact-kowa_lm6hc')
parser.add_argument('--baseline', type=Path, default=P / 'history/reviewed-export18')
args = parser.parse_args()
D, H = args.out, args.baseline


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, V(x0, y0, z0))


mf = D / 'manifest.json'
mh = sha(mf)
m = json.loads(read_text(mf))
length = m['core_dimensions_mm'][0]
source_hashes = {name: sha(P / name) for name in ('model.py', 'vent_geometry.py')}
for name, digest in source_hashes.items():
    assert m['sources']['candidate-vertical/' + name] == digest, 'Source-stale export: ' + name
assert m.get('ventilation', {}).get('revision', '').startswith('shadow-gap'), 'Not a shadow-plenum export'
step = D / 'step/tub.step'
assert sha(step) == m['files']['step/tub.step'], 'Tub STEP hash mismatch'
s = cq.importers.importStep(str(step)).val()
hm = json.loads(read_text(H / 'manifest.json'))
assert sha(H / 'tub.step') == hm['files']['step/tub.step'], 'Historical tub hash mismatch'
old = cq.importers.importStep(str(H / 'tub.step')).val()
rows = []


def record(ident, passed=None, **data):
    row = dict(id=ident, status='info' if passed is None else ('pass' if passed else 'fail'), **data)
    rows.append(row)
    print(json.dumps(row), flush=True)


def ray(a, b):
    edges = s.intersect(cq.Edge.makeLine(V(*a), V(*b))).Edges()
    return sum(edge.Length() for edge in edges)


def rectangle(axis, position, u0, u1, v0, v1):
    def point(u, v):
        return {'x': (position, u, v), 'y': (u, position, v), 'z': (u, v, position)}[axis]
    points = [point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)]
    return cq.Face.makeFromWires(cq.Wire.makePolygon([V(*p) for p in points + points[:1]]))


def free_section(axis, position, u0, u1, v0, v1):
    # Exact planar face minus saved material, not nominal cutter area and not a
    # finite-thickness average. Reject unexpected face-Boolean results.
    face = rectangle(axis, position, u0, u1, v0, v1)
    gross = (u1-u0)*(v1-v0)
    free = face.cut(s).Area()
    assert -1e-6 <= free <= gross+1e-5, 'Invalid section Boolean area'
    return dict(position_mm=position, free_area_mm2=free, gross_area_mm2=gross,
                obstruction_mm2=max(0., gross-free), axis=axis,
                rectangle_uv_mm=[u0, u1, v0, v1])


record('tub_valid_single_solid', s.isValid() and len(s.Solids()) == 1,
       solids=len(s.Solids()), volume_mm3=s.Volume())

# Ports are measured in the original wall, independently of VG's cutter helpers.
port_totals = {}
for group, xa, xb, heights in [('cold', -103., -68., (18., 24., 30., 36.)),
                              ('hot', -59., -16.5, (16., 23., 30., 37.))]:
    total = 0.
    for i, z in enumerate(heights):
        section = free_section('y', -26.75, xa, xb, z, z+3.)
        total += section['free_area_mm2']
        material = ray(((xa+xb)/2, -28.05, z+1.5), ((xa+xb)/2, -25.45, z+1.5))
        record(f'{group}_wall_port_{i}', abs(section['free_area_mm2']-(xb-xa)*3.) < .002 and material < 1e-5,
               section=section, through_ray_material_mm=material)
    port_totals[group] = total

# Include a section just beyond each mouth cutter: overlap stock can make that
# inboard neck smaller than the visible mouth despite matching mouth metadata.
mouths = [
    ('cold_rear', 'x', [-length+.05, -length+1.25, -length+2.49, -length+2.62], -34., -28., 5., 75.,
     (-length-.05, -31., 40.), (-length+2.7, -31., 40.), (-length+2.51, -31., 40.), 'cold'),
    ('cold_bottom', 'z', [.05, 1.25, 2.49, 2.62], -length+4., -83., -34., -28.,
     ((-length+4.-83.)/2, -31., -.05), ((-length+4.-83.)/2, -31., 2.7),
     ((-length+4.-83.)/2, -31., 2.51), 'cold'),
    ('hot_bottom', 'z', [.05, 1.25, 2.49, 2.62], -59., -5., -34., -28.,
     (-32., -31., -.05), (-32., -31., 2.7), (-32., -31., 2.51), 'hot'),
    ('hot_front', 'x', [-.05, -1.25, -2.49, -2.62], -34., -28., 5., 40.,
     (.05, -31., 22.5), (-2.7, -31., 22.5), (-2.51, -31., 22.5), 'hot'),
]
mouth_results = {}
for name, axis, planes, u0, u1, v0, v1, a, b, seed, bay in mouths:
    sections = [free_section(axis, plane, u0, u1, v0, v1) for plane in planes]
    minimum = min(q['free_area_mm2'] for q in sections)
    material = ray(a, b)
    mouth_results[name] = dict(minimum_sampled_neck_mm2=minimum, sections=sections, bay=bay, seed=seed)
    record(name + '_sections_and_path', minimum > 0 and material < 1e-5,
           **mouth_results[name], through_ray_material_mm=material)
for bay in ('cold', 'hot'):
    area = sum(r['minimum_sampled_neck_mm2'] for r in mouth_results.values() if r['bay'] == bay)
    record(bay + '_summed_sampled_mouth_necks', area >= port_totals[bay]-.002,
           minimum_sampled_necks_sum_mm2=area, wall_ports_mm2=port_totals[bay],
           note='Parallel-mouth area comparison, not a proof of global series minimum or pressure loss')

# Named interior sections capture full-gap post rows. They are not treated as a
# single serial flow duct: each bay receives/discharges distributed side ports.
for z in (7.2, 8., 8.8, 12., 16., 21., 22.5, 28.5, 34.5, 43.):
    for name, xa, xb in [('cold', -length+2.5, -65.), ('hot', -62., -2.5)]:
        section = free_section('z', z, xa, xb, -34., -28.)
        record(f'{name}_interior_horizontal_section_z{z:g}', None, section=section,
               note='One measured cut; ports and branches mean this is not a global flow bottleneck')

# Air topology is restricted to the external bays and old side-wall ports. Stop
# before the original inner face so the deliberately open main body cannot join
# the bays behind the retained partial internal baffle.
domain = box(-length+2.5, -2.5, -34., -25.51, 2.5, 97.5)
air = domain.cut(s)
air_solids = [q for q in air.Solids() if q.Volume() > .001]
def owners(point):
    return [i for i, q in enumerate(air_solids) if q.isInside(V(*point), 1e-6)]
bay_seeds = {'cold': (-110., -31., 50.), 'hot': (-40., -31., 50.), 'csi': (-83., -31., 50.)}
bay_ids = {name: owners(point) for name, point in bay_seeds.items()}
record('external_bay_topology', len(air_solids) == 3 and all(len(v) == 1 for v in bay_ids.values()) and
       len({v[0] for v in bay_ids.values() if v}) == 3,
       significant_void_solids=len(air_solids), seed_ownership=bay_ids,
       void_solid_volumes_mm3=[q.Volume() for q in air_solids],
       domain='External cold bay, external hot bay, isolated straight CSI sleeve; main cavity excluded')
for name, data in mouth_results.items():
    hits = owners(data['seed'])
    record(name + '_feeds_correct_bay', hits == bay_ids[data['bay']] and len(hits) == 1, ownership=hits)
for bay, x, heights in [('cold', -85.5, (18., 24., 30., 36.)), ('hot', -37.75, (16., 23., 30., 37.))]:
    for i, z in enumerate(heights):
        hits = owners((x, -26.75, z+1.5))
        record(f'{bay}_port_{i}_joins_correct_bay', hits == bay_ids[bay] and len(hits) == 1, ownership=hits)

divider = box(-64.9, -62.1, -33.9, -28.1, 2.6, 97.4)
missing = divider.cut(s).Volume()
record('continuous_external_divider', missing < 1e-5, missing_material_mm3=missing,
       note='Interior baffle remains partial; this checks the external divider only')

# Sleeve area and isolation; real tools/latches/full FPC remain independently gated.
csi_areas = [free_section('y', y, -89., -77., 41., 68.) for y in (-35.5, -31., -26.75)]
csi_expected = 12*27-(4-math.pi)
record('csi_straight_sleeve_area', all(abs(q['free_area_mm2']-csi_expected) < .002 for q in csi_areas),
       expected_mm2=csi_expected, sections=csi_areas)
for name, a, b in [('left', (-90., -33.9, 50.), (-90., -28.1, 50.)),
                   ('right', (-76., -33.9, 50.), (-76., -28.1, 50.)),
                   ('bottom', (-83., -33.9, 40.), (-83., -28.1, 40.)),
                   ('top', (-83., -33.9, 69.), (-83., -28.1, 69.))]:
    material = ray(a, b)
    record('csi_sleeve_' + name + '_wall', material >= 5.8-1e-5, material_span_mm=material)
for name, z in [('lower', 46.155), ('upper', 62.855)]:
    start = V(-82.605, -1.98, z)
    tool = cq.Solid.makeCylinder(2., 15., start, V(0, -1, 0)).fuse(
        cq.Solid.makeCylinder(4., 75., start+V(0, -15., 0), V(0, -1, 0)))
    overlap = tool.intersect(s).Volume()
    record('csi_declared_' + name + '_tool_vs_tub', overlap < .002, overlap_mm3=overlap,
           source='Export18 csi-source-tool-checks.json declared cylinders; all other components and real jaws remain separate')

# Normal sight rays verify the facade, not all-angle concealment. The front edge
# outlet is intentionally open and must be judged in the rendered front views.
for i, (x, z) in enumerate([(-85.5, 19.5), (-85.5, 37.5), (-37.75, 17.5), (-37.75, 38.5),
                           (-120., 50.), (-40., 70.), (-110., 90.)]):
    material = ray((x, -35.7, z), (x, -33.8, z))
    record('blank_outer_face_ray_' + str(i), material >= 1.6-1e-5, material_span_mm=material, xz=[x, z])
for z in (9.5, 15.5, 21.5, 27.5, 33.5):
    material = ray((-.05, -10., z), (-5.15, -10., z))
    record('old_front_grille_closed_z' + str(z), material >= 5.1-1e-5, material_span_mm=material)

# Compare only original cavity material, independently of the revised helper.
cavity = box(-length+2.6, -5.3, -25.4, 25.1, 2.6, 97.4)
added_in_cavity = s.intersect(cavity).cut(old.intersect(cavity)).Volume()
record('no_added_material_in_original_cavity', added_in_cavity < 1e-5,
       overlap_mm3=added_in_cavity, boundary_exclusion_mm=.1)

# Info row only (no pass/fail): describes the roof support of the checked source. FP-11a (trial2) replaced the
# trial1 1.6 mm post grid with continuous ribs; the bridge rule itself is computed by verify_print_checks.py.
record('print_and_thermal_limits', None,
       post_count=len(VG.post_centres(length)), roof_support=VG.support_summary(length),
       support_free_claim=False, cleanout_qualified=False, thermal_qualified=False,
       limitations=['Roof bridges run between continuous 1.2 mm ribs; the per-region single-direction bridge rule is '
                    'computed by verify_print_checks.py (print_bridge_direction), not here, and no slicer result exists.',
                    'Ribs, row breaks, mullions and lintels add flow resistance beyond the sampled planar sections.',
                    'No trapped support is permitted; slicer/bridge coupon and debris removal remain gates.',
                    'Cold/hot mouths may be occluded by hands and may recirculate externally.',
                    'CSI remains an unsealed direct bypass to the main enclosure.',
                    'Fan operating point, actual cooler geometry, full loom and all physical gates remain open.'])

assert sha(mf) == mh, 'Manifest changed during verification'
assert all(sha(P / n) == h for n, h in source_hashes.items()), 'Source changed during verification'
result = dict(manifest_sha256=mh, saved_tub_sha256=sha(step), historical_tub_sha256=sha(H / 'tub.step'),
              verification_source_sha256=sha(Path(__file__)), checked_source_sha256=source_hashes,
              generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              summary={k: sum(q['status'] == k for q in rows) for k in ('pass', 'fail', 'info')},
              checks=rows, physical_qualified=False,
              scope='Exact saved-STEP named planar sections, finite rays, external void connectivity and local material comparison; no global flow/strength/print/thermal qualification')
write_text(D / 'shadow-plenum-checks.json', json.dumps(result, indent=2))
print(json.dumps(result['summary']), flush=True)
raise SystemExit(bool(result['summary']['fail']))
