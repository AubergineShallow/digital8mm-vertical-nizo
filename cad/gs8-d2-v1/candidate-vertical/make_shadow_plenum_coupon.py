"""Crop an open-edge bridge-inspection coupon from the checked saved tub.

Run through run_locked.py after verify_shadow_plenum.py. This is a separate test
artifact, not a tenth production print or a replacement for the older coupons.
No support geometry is invented and no print or thermal release is granted.
"""
from pathlib import Path
import hashlib
import json
import time

import cadquery as cq

P = Path(__file__).resolve().parent
D = P / 'out/compact-kowa_lm6hc'
O = P / 'vent-study/shadow-plenum-coupon'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


mf = D / 'manifest.json'
mh = sha(mf)
m = json.loads(mf.read_text())
checks_path = D / 'shadow-plenum-checks.json'
checks = json.loads(checks_path.read_text())
assert checks['manifest_sha256'] == mh, 'Plenum check belongs to another export'
assert checks['summary']['fail'] == 0, 'Resolve failed saved-STEP checks before coupon export'
source = D / 'step/tub.step'
assert sha(source) == m['files']['step/tub.step'], 'Tub STEP hash mismatch'
tub = cq.importers.importStep(str(source)).val()

O.mkdir(parents=True, exist_ok=True)


def make_coupon(name, crop_bounds, stem, receipt_name, purpose, local_limit):
    a, b, c, d, e, f = crop_bounds
    crop = cq.Solid.makeBox(b-a, d-c, f-e, cq.Vector(a, c, e))
    coupon = tub.intersect(crop)
    receipt = dict(name=name, manifest_sha256=mh, tub_sha256=sha(source),
                   source_check_sha256=sha(checks_path), crop_bounds_mm=crop_bounds,
                   generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   valid=coupon.isValid(), solid_count=len(coupon.Solids()),
                   volume_mm3=coupon.Volume(), production_part=False,
                   physical_qualified=False, purpose=purpose,
                   limitations=['Does not prove closed-body cleanout; its cut edges permit access absent in the complete camera.',
                                local_limit,
                                'No supports added. Automatic internal support would be unacceptable in the complete plenum.',
                                'No strength, cooling, pressure-loss, hand-occlusion or full-body print qualification follows from this crop.'])
    if not receipt['valid'] or receipt['solid_count'] != 1:
        receipt['exported'] = False
        receipt['status'] = 'BLOCKED: invalid or disconnected crop; no substitute supports generated'
        (O / receipt_name).write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt), flush=True)
        raise SystemExit(1)
    step = O / (stem + '.step')
    stl = O / (stem + '.stl')
    cq.exporters.export(coupon, str(step))
    check = cq.importers.importStep(str(step)).val()
    assert check.isValid() and len(check.Solids()) == 1
    assert abs(check.Volume()-coupon.Volume()) < .001
    posed = coupon.rotate((0, 0, 0), (1, 0, 0), 90.)
    bb = posed.BoundingBox()
    translation = [-bb.xmin, -bb.ymin, -bb.zmin]
    posed = posed.translate(cq.Vector(*translation))
    bb = posed.BoundingBox()
    assert abs(bb.zmin) < 1e-6
    cq.exporters.export(posed, str(stl), tolerance=.04, angularTolerance=.12)
    receipt.update(exported=True, status='Geometry-only open-edge coupon; not print released',
                   step_reimport_valid=True, face_down='-Y', rotation_axis=[1, 0, 0],
                   rotation_deg=90., translation_mm=translation,
                   print_dimensions_mm=[bb.xlen, bb.ylen, bb.zlen],
                   files={step.name: sha(step), stl.name: sha(stl)},
                   source_sha256=sha(Path(__file__)))
    assert sha(mf) == mh, 'Manifest changed during coupon export'
    (O / receipt_name).write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    return receipt_name


receipts = []
receipts.append(make_coupon(
    'preliminary_regular_grid', [-152., -104., -35.6, -25.5, 8., 40.],
    'plenum-bridge-open-edge-coupon', 'receipt.json',
    'Open-edge regular-grid post-supported roof-bridge inspection crop from the exact selected tub',
    'Does not reproduce the ports, CSI sleeve, post exclusions or front/top enclosure edge spans.'))
receipts.append(make_coupon(
    'port_service_and_edge_regions', [-110., 0., -35.6, -25.5, 0., 100.],
    'plenum-port-service-open-edge-coupon', 'port-service-receipt.json',
    'Open-edge crop retaining inlet/hot ports, CSI sleeve, post exclusions, front mouth, bottom support row and top/front frame spans',
    'The rear section and complete cold-rear mouth are absent; retained edge spans are not a global maximum-span proof.'))
(O / 'coupon-index.json').write_text(json.dumps(dict(
    manifest_sha256=mh, source_sha256=sha(Path(__file__)),
    coupon_count=2, production_part_count_change=0, replaces_earlier_coupon_set=False,
    receipts={name: sha(O / name) for name in receipts}, physical_qualified=False,
    status='Two separate open-edge inspection tests; no closed-body cleanout, occlusion, strength or thermal qualification'), indent=2))
