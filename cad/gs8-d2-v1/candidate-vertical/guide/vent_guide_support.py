"""Lightweight source/report binding and diagrams for the concealed-vent guide.

This module imports neither CadQuery nor the guide renderer. It can preflight a
nominated manifest without running CAD, compiling the rasterizer or rendering.
"""
import sys as _cvsys; _cvsys.path.append(str(__import__('pathlib').Path(__file__).resolve().parents[1]))  # candidate-vertical root: cv_io
from cv_io import read_text, rel_posix
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_inputs(root, nominated_hash):
    root = Path(root)
    export = root / 'out/compact-kowa_lm6hc'
    manifest_path = export / 'manifest.json'
    if len(nominated_hash) != 64 or any(c not in '0123456789abcdef' for c in nominated_hash):
        raise ValueError('Supply the exact lowercase SHA-256 of the nominated manifest')
    if sha(manifest_path) != nominated_hash:
        raise RuntimeError('The mechanical manifest differs from the nominated checkpoint')
    manifest = json.loads(read_text(manifest_path))
    for name, expected in manifest['sources'].items():
        path = root.parent / name
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError('Mechanical source differs from nominated export: ' + name)
    source = root / 'vent_geometry.py'
    source_key = rel_posix(source, root.parent)
    if manifest['sources'].get(source_key) != sha(source):
        raise RuntimeError('Nominated manifest does not bind the ventilation source')
    report_path = export / 'shadow-plenum-checks.json'
    report = json.loads(read_text(report_path))
    expected_fields = {
        'manifest_sha256': nominated_hash,
        'verification_source_sha256': sha(root / 'verify_shadow_plenum.py'),
        'saved_tub_sha256': manifest['files']['step/tub.step'],
        'historical_tub_sha256': sha(root / 'history/reviewed-export18/tub.step'),
    }
    for key, expected in expected_fields.items():
        if report.get(key) != expected:
            raise RuntimeError('Ventilation evidence has a stale or absent binding: ' + key)
    checked_sources = report.get('checked_source_sha256', {})
    for name in ('model.py', 'vent_geometry.py'):
        if checked_sources.get(name) != sha(root / name):
            raise RuntimeError('Plenum report checked-source mismatch: ' + name)
    for part in ('tub', 'panel'):
        key = 'step/' + part + '.step'
        if sha(export / key) != manifest['files'].get(key):
            raise RuntimeError('Saved STEP differs from nominated manifest: ' + part)
    if report.get('physical_qualified') is not False:
        raise RuntimeError('Ventilation report must retain physical qualification hold')
    metadata = manifest['ventilation']
    checks = report.get('checks', [])
    if not checks or any(row.get('status') not in ('pass', 'fail', 'info') for row in checks):
        raise RuntimeError('Plenum report has no usable check rows')
    summary = {key: sum(row['status'] == key for row in checks) for key in ('pass', 'fail', 'info')}
    if report.get('summary') != summary or summary['pass'] + summary['fail'] == 0:
        raise RuntimeError('Plenum report summary differs from its check rows')
    required = {'tub_valid_single_solid', 'external_bay_topology', 'continuous_external_divider',
                'csi_straight_sleeve_area', 'no_added_material_in_original_cavity', 'print_and_thermal_limits'}
    if not required.issubset({row['id'] for row in checks}):
        raise RuntimeError('Plenum report is missing a required geometry or limitation check')
    constants = {}
    wanted = {'OUTER_Y', 'INNER_Y', 'SKIN_INNER', 'WALL_OUTER', 'GAP', 'SIDE_Z', 'HOT_Z'}
    for node in ast.parse(read_text(source)).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in wanted:
                constants[target.id] = ast.literal_eval(node.value)
    if constants.keys() != wanted:
        raise RuntimeError('Plenum section constants are incomplete')
    if (len(constants['SIDE_Z']) != 4 or len(constants['HOT_Z']) != 4 or
            not metadata.get('revision', '').startswith('shadow-gap plenum trial4') or
            not metadata.get('support', {}).get('hot_front_apertures_yz')):
        raise RuntimeError('Plenum topology changed; revise the guide diagrams and labels')
    expected_dimensions = {
        'outer_skin_mm': constants['SKIN_INNER'] - constants['OUTER_Y'],
        'plenum_gap_mm': constants['WALL_OUTER'] - constants['SKIN_INNER'],
        'original_side_wall_mm': constants['INNER_Y'] - constants['WALL_OUTER'],
    }
    for key, value in expected_dimensions.items():
        if not math.isclose(metadata[key], value, abs_tol=1e-8):
            raise RuntimeError('Report dimension differs from plenum source: ' + key)
    if (metadata.get('intake_wall_throat_mm2') != 420.0 or
            metadata.get('exhaust_wall_throat_mm2') != 510.0 or
            metadata.get('csi_unchanged_straight_access') is not True):
        raise RuntimeError('Plenum slot or CSI topology changed; revise the guide')
    structural = root / 'structural-review'
    structural_report = json.loads(read_text(structural / 'concealed-vent-structural.json'))
    structural_expected = {
        'manifest_sha256': nominated_hash,
        'verification_source_sha256': sha(structural / 'update_concealed_vent_structure.py'),
        'reference_manifest_sha256': sha(root / 'history/reviewed-export18/manifest.json'),
        'reference_structural_binding_sha256': sha(structural / 'reference-export18-structural-binding.json'),
    }
    for key, expected in structural_expected.items():
        if structural_report.get(key) != expected:
            raise RuntimeError('Structural supplement has a stale binding: ' + key)
    if (structural_report.get('physical_qualified') is not False or
            structural_report.get('ventilation_report', {}).get('sha256') != sha(report_path)):
        raise RuntimeError('Structural supplement must retain its hold and bind the current ventilation report')
    # Bind each final caption source while retaining its failures. A current
    # report is usable evidence even when it correctly blocks the design.
    scoped = {}
    report_specs = {
        'main': ('verification.json', 'verify_candidate.py'),
        'harness': ('harness-checks.json', 'verify_harness_checks.py'),
        'flow': ('check-scope-checks.json', 'verify_check_scope.py'),
        'print': ('print-checks.json', 'verify_print_checks.py'),
        'outlet': ('shadow-outlet-context-checks.json', 'verify_shadow_outlet_context.py'),
    }
    for label, (filename, verifier) in report_specs.items():
        path = export / filename
        value = json.loads(read_text(path))
        if value.get('manifest_sha256') != nominated_hash or value.get('verification_source_sha256') != sha(root / verifier):
            raise RuntimeError('Guide caption report is stale: ' + filename)
        for key, base in (('verification_dependency_sha256', root), ('helper_source_sha256', root),
                          ('input_sha256', root.parent), ('check_sources', root.parent),
                          ('checked_source_sha256', root)):
            bindings = value.get(key, {})
            if isinstance(bindings, dict):
                for name, digest in bindings.items():
                    if sha(base / name) != digest:
                        raise RuntimeError('Guide report dependency changed: ' + filename + ' / ' + name)
        scoped[label] = {'path': path, 'report': value}
    import steps
    if scoped['main']['report'].get('flex_scope') != steps.flexible_scope():
        raise RuntimeError('Main report does not preserve current complete-ribbon omissions')
    coupons_path = root / 'vent-study/shadow-plenum-coupon/coupon-index.json'
    coupons = json.loads(read_text(coupons_path))
    if coupons.get('manifest_sha256') != nominated_hash or coupons.get('coupon_count') != 3:
        raise RuntimeError('The three plenum coupon receipts are not bound to the nominated export')
    for name, digest in coupons.get('receipts', {}).items():
        if sha(coupons_path.parent / name) != digest:
            raise RuntimeError('Plenum coupon receipt changed: ' + name)
    catch_path = root / 'structural-review/bonded-catch-coupon/receipt.json'
    catch = json.loads(read_text(catch_path))
    if (catch.get('manifest_sha256') != nominated_hash or catch.get('piece_count') != 2 or
            catch.get('physical_qualified') is not False or catch.get('production_part_count_change') != 0):
        raise RuntimeError('Local bonded-catch coupon has a stale binding or lost its scope hold')
    for field, base in (('input_sha256', root), ('source_sha256', root), ('files', catch_path.parent)):
        for name, digest in catch.get(field, {}).items():
            if sha(base / name) != digest:
                raise RuntimeError('Local bonded-catch coupon dependency changed: ' + name)
    return {'metadata': metadata, 'constants': constants, 'report': report,
            'report_path': report_path, 'geometry_pass': summary['fail'] == 0,
            'scoped': scoped, 'coupons_path': coupons_path, 'coupons': coupons,
            'catch_path': catch_path, 'catch': catch}


def draw_plenum_section(draw, text, arrow, x, y, width, height, skin, gap,
                        inner_wall, flow_in):
    """Representative section through an underside mouth and one wall slot.

    Skin, gap and wall thicknesses share one scale. Posts, end frames and other
    internal features are omitted. The arrows are intended routes, not a sealed
    air-domain or measured flow result.
    """
    scale = 20.0
    left = x + 70
    skin_end = left + skin * scale
    gap_end = skin_end + gap * scale
    wall_end = gap_end + inner_wall * scale
    top = y + 45
    bottom = y + height - 75
    slot_top = top + 95
    slot_bottom = slot_top + 3 * scale
    draw.rectangle((left, top, skin_end, bottom), fill='#D5D5D5', outline='#181818', width=3)
    draw.rectangle((skin_end, top, gap_end, bottom), fill='#F4F4F4')
    draw.rectangle((gap_end, top, wall_end, bottom), fill='#D5D5D5', outline='#181818', width=3)
    draw.rectangle((gap_end - 1, slot_top, wall_end + 1, slot_bottom), fill='white')
    draw.line((gap_end, slot_top, wall_end, slot_top), fill='#181818', width=3)
    draw.line((gap_end, slot_bottom, wall_end, slot_bottom), fill='#181818', width=3)
    bend = ((skin_end + gap_end) / 2, (slot_top + slot_bottom) / 2)
    mouth = (bend[0], bottom + 25)
    cavity = (wall_end + 65, bend[1])
    if flow_in:
        draw.line((*mouth, *bend), fill='#37658A', width=4)
        arrow(draw, bend, cavity, width=4)
    else:
        draw.line((*cavity, *bend), fill='#37658A', width=4)
        arrow(draw, bend, mouth, width=4)
    text(draw, x, y, 'EXTERIOR', 21, width=300)
    text(draw, x + 350, y, 'CAVITY', 21, width=300)
    text(draw, wall_end + 95, top + 32,
         f'{skin:g} mm skin\n{gap:g} mm gap\n{inner_wall:g} mm wall\n3 mm wall slot', 22, width=330)
    text(draw, x, y + height - 35, 'Underside mouth opens into the gap', 22, width=width)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preflight the nominated concealed-vent guide inputs without rendering')
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    result = inspect_inputs(Path(__file__).resolve().parents[1], args.manifest_sha256)
    from followup_guide_support import inspect_variants
    followup = inspect_variants(Path(__file__).resolve().parents[1])
    print(json.dumps({'manifest_sha256': args.manifest_sha256,
                      'ventilation_checks': result['report']['summary'],
                      'geometry_pass': result['geometry_pass'],
                      'followup_variants': {name: value['catch_summary']
                                            for name, value in followup['variants'].items()},
                      'physical_qualified': False}, indent=2))
