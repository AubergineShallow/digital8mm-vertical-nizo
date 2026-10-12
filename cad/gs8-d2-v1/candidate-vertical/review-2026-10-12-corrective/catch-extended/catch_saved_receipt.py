# SPDX-License-Identifier: MIT
"""Derive a catch receipt from an existing full audit; never recompute geometry.

The full audit remains the execution evidence. This reader authenticates its
sources and STEP inputs, checks the complete unchanged policy, and preserves
every saved stub row and failure. It is not an independent geometric validation.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
CV = HERE.parents[1]
sys.path[:0] = [str(CV), str(HERE)]
import j7_collar_checks as J
import catch_extended_cases as RERUN
from cv_io import read_text, write_text

SELF = 'review-2026-10-12-corrective/catch-extended/catch_saved_receipt.py'
SOURCES = RERUN.SOURCES + (SELF, 'verify_candidate.py', 'cv_io.py')
S_VALUES = [i / 4 for i in range(13)]
MODE = 'saved_full_audit'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def one(rows, category, ident):
    got = [r for r in rows if (r.get('category'), r.get('id')) == (category, ident)]
    require(len(got) == 1, 'missing or duplicate row: %s/%s' % (category, ident))
    return got[0]


def finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def validate_functional(row):
    """Check saved sampling and numeric consistency, without replacing CAD verdicts."""
    require(row.get('status') in ('pass', 'fail'), 'invalid functional status: ' + row['id'])
    require(row.get('status') != 'pass' or not row.get('error'), 'passing row hides an error: ' + row['id'])
    offsets = [(0., 0., False), (.55, 0., False), (-.55, 0., False),
               (0., .55, False), (0., -.55, False)]
    if row['item'] == 'window':
        require(row.get('window_deg') == 1.4 and row.get('rule') == 'centred >= 0.30, worst offset >= 0.10',
                'window policy changed: ' + row['id'])
        keys = {'%+.2f/%+.2f/%+d' % (dy, dz, direction) for dy, dz, _ in offsets for direction in (1, -1)}
        gaps = row.get('gaps', {})
        require(set(gaps) == keys and all(finite(v) for v in gaps.values()), 'window samples incomplete: ' + row['id'])
        require(row.get('centred_gap') == min(gaps['+0.00/+0.00/%+d' % d] for d in (1, -1))
                and row.get('worst_gap') == min(gaps.values()), 'window minima differ from samples: ' + row['id'])
        if row['status'] == 'pass':
            require(row['centred_gap'] >= .299 and row['worst_gap'] >= .099,
                    'failing window relabelled pass: ' + row['id'])
        return
    require(row.get('rule_margin_deg') == 1. and row.get('lateral_offset') == .55 and row.get('sag') == .75,
            'first-contact policy changed: ' + row['id'])
    offsets += [(0., -.75, True), (.55, -.75, True), (-.55, -.75, True)]
    wanted = {(dy, dz, direction, hold) for dy, dz, hold in offsets for direction in (1, -1)}
    cases = row.get('cases', [])
    signatures = [(c.get('dy'), c.get('dz'), c.get('dir'), c.get('lens_out')) for c in cases]
    require(len(cases) == len(wanted) and set(signatures) == wanted,
            'first-contact samples incomplete or duplicated: ' + row['id'])
    for case in cases:
        metal, pcb = case.get('metal_deg'), case.get('pcb_cover_deg')
        require(metal is None or finite(metal), 'non-finite metal contact')
        require(pcb is None or finite(pcb), 'non-finite PCB contact')
        margin = None if metal is None or pcb is None else round(pcb - metal, 3)
        require(case.get('margin_deg') == margin, 'saved contact margin inconsistent')
        if row['status'] == 'pass':
            require(metal is not None and 0 <= metal <= 14 and case.get('metal_to') == ['tub'],
                    'passing contact lacks metal catch within unchanged scan')
            require(pcb is None or pcb >= metal + 1. - 1e-9, 'first-contact margin weakened')
    metals = [c['metal_deg'] for c in cases if c['metal_deg'] is not None]
    pcbs = [c['pcb_cover_deg'] for c in cases if c['pcb_cover_deg'] is not None]
    margins = [c['margin_deg'] for c in cases if c['margin_deg'] is not None]
    for field, expected in (('metal_min_deg', min(metals, default=None)),
                            ('metal_max_deg', max(metals, default=None)),
                            ('pcb_cover_min_deg', min(pcbs, default=None)),
                            ('min_margin_deg', min(margins, default=None)),
                            ('centred_deg', next(c['metal_deg'] for c in cases
                                                if (c['dy'], c['dz'], c['dir']) == (0, 0, 1)))):
        require(row.get(field) == expected, 'contact summary differs from samples: ' + field)


def validate_saved_rows(meta, main):
    """Pure validation of full saved coverage. Failure rows remain failure rows."""
    require(main.get('scope') == 'full', 'saved catch receipt requires a full main audit')
    require(main.get('physical_qualified') is False, 'main audit lost physical qualification hold')
    all_rows = main.get('checks', [])
    identifiers = [(r.get('category'), r.get('id')) for r in all_rows]
    require(len(identifiers) == len(set(identifiers)), 'duplicate main audit rows')
    totals = Counter(r.get('status') for r in all_rows)
    require(set(totals) <= {'pass', 'fail', 'info'} and
            main.get('summary') == {s: totals[s] for s in ('pass', 'fail', 'info')}, 'main summary differs from rows')
    require(main.get('geometry_computed_pass') is (totals['fail'] == 0), 'main computed verdict differs from rows')
    context = one(all_rows, 'roll_catch', 'stub_production_context')
    require(context.get('status') == 'pass' and context.get('manifest_file_binding') is True and
            context.get('step') == 'step/tab_catch_insert.step' and
            context.get('step_sha256') == meta['files'].get(context['step']), 'production insert context is stale or invalid')
    checks = [r for r in all_rows if r['category'] == 'roll_catch' and r['id'].startswith('stub_')
              and r['id'] != 'stub_production_context']
    coverage = one(checks, 'roll_catch', 'stub_pose_coverage')
    require(coverage.get('s_values') == S_VALUES and coverage.get('production_insert_supplied') is True,
            'full BFAR coverage or production insert missing')
    bounds = coverage.get('pocket_bounds_mm', [])
    require(len(bounds) == 6 and all(finite(v) for v in bounds), 'invalid production pocket bounds')
    joint = meta['tab_catch_joint']
    model = SimpleNamespace(TAB_CATCH_TENON=joint['tenon_mm'], TAB_CATCH_SPLIT_Z=joint['split_z_mm'])
    geometry = one(all_rows, 'roll_catch', 'tab_catch_geometry')
    require(geometry.get('status') == 'pass', 'nominal catch geometry failed')
    # Recover the unchanged upper web from the saved geometry row, not an invented fixture.
    tenon_x = model.TAB_CATCH_TENON['x']
    webs = [b for b in geometry.get('catch_boxes', []) if b['z'][0] == model.TAB_CATCH_SPLIT_Z
            and abs(b['y'][0] - bounds[2]) < 1e-9 and b['x'][0] <= tenon_x[0] and b['x'][1] >= tenon_x[1]]
    require(len(webs) == 1, 'missing unique production web for pose policy')
    poses = json.loads(json.dumps(J.stub_pose_table(model, webs[0], bounds)))
    require(len(poses) == 69 and coverage.get('cases') == [p['case'] for p in poses]
            and coverage.get('pose_count') == len(poses), 'complete 69-pose table required')
    records, cases = {}, []
    required_ids = {'stub_pose_coverage'}
    for pose in poses:
        name = pose['case']
        ident = 'stub_' + name + ':feasibility'
        row = one(checks, 'roll_catch', ident)
        require(all(row.get(k) == v for k, v in pose.items()), 'saved pose differs from policy: ' + name)
        require(row.get('case') == name and row.get('stub_case') == name and
                row.get('pocket_bounds_mm') == bounds, 'pose identity or pocket differs: ' + name)
        require(type(row.get('feasible')) is bool and type(row.get('geometry_valid')) is bool and
                finite(row.get('minimum_axial_engagement_mm')), 'invalid feasibility fields: ' + name)
        gaps = row.get('joint_face_gap_range_mm', [])
        require(len(gaps) == 2 and all(finite(v) for v in gaps) and gaps[0] <= gaps[1] and
                row.get('joint_face_reference_points', 0) > 0, 'missing measured joint-face gap: ' + name)
        functional = [r for r in checks if r.get('stub_case') == name and r.get('item') in ('window', 'first_contact')]
        required_ids.add(ident)
        graded = row['feasible'] or pose.get('legacy', False)
        require(row.get('graded') == graded and row.get('legacy_blocked_diagnostic') == bool(pose.get('legacy') and not row['feasible']),
                'feasibility grading changed: ' + name)
        for item in ('window', 'first_contact'):
            if graded:
                required_ids.update('stub_%s:%s@s%.2f' % (name, item, s) for s in S_VALUES)
        for f in functional:
            require(f.get('s') in S_VALUES and f['id'] == 'stub_%s:%s@s%.2f' % (name, f['item'], f['s']),
                    'functional sample identity differs: ' + name)
            require(f.get('stub_feasible') == row['feasible'] and f.get('stub_shift_mm') == pose['shift_mm']
                    and f.get('stub_rotations') == pose['rotations'], 'functional pose context differs: ' + name)
            validate_functional(f)
        records[name] = dict(row, rows=functional)
        case = copy.deepcopy(row)
        case.update(rows=len(functional), fail_rows=[f['id'] for f in functional if f['status'] == 'fail'],
                    min_worst_window_gap=min((f['worst_gap'] for f in functional if f['item'] == 'window'), default=None))
        cases.append(case)
    require({r['id'] for r in checks} == required_ids, 'missing or unexpected catch functional/feasibility rows')
    errors = J.stub_acceptance_errors(poses, records, S_VALUES,
            SimpleNamespace(ROLL_CATCH=dict(J.STUB_CONTACT_RULES)), SimpleNamespace(J7_RUNNING=.1, J7_TOL=.001))
    require(not errors, 'saved catch policy invalid: ' + '; '.join(errors))
    require(coverage.get('errors') == [] and coverage.get('status') == 'pass' and
            coverage.get('feasible_count') == sum(r['feasible'] for r in cases), 'coverage verdict or feasibility count differs')
    return dict(checks=copy.deepcopy(checks), cases=cases, coverage=copy.deepcopy(coverage),
                production_insert={k: context[k] for k in ('step', 'step_sha256', 'manifest_file_binding')})


def build_receipt(cv, variant):
    """Authenticate before and after derivation; return a new explicitly derived receipt."""
    cv = Path(cv)
    start = time.monotonic()
    out = cv / 'out' / variant
    manifest_path, main_path = out / 'manifest.json', out / 'verification.json'
    manifest_hash, main_hash = sha(manifest_path), sha(main_path)
    sources = {name: sha(cv / name) for name in SOURCES}
    meta, main = json.loads(read_text(manifest_path)), json.loads(read_text(main_path))
    require(main.get('variant') == variant, 'main variant mismatch')
    require(main.get('verification_source_sha256') == sources['verify_candidate.py'] and
            main.get('state_model_sha256') == sources['steps.py'], 'main verifier or steps source is stale')
    require(not RERUN.freshness_errors(meta, main, manifest_hash, cv), 'stale main, manifest or context sources')
    bindings = [r for r in main['checks'] if r.get('category') == 'source_binding']
    require(sorted(r['id'] for r in bindings) == sorted(meta['sources']) and
            all(r['status'] == 'pass' for r in bindings), 'export-source binding rows incomplete or failed')
    inputs = {name: sha(out / name) for name in meta['files'] if name.endswith('.step')}
    require(inputs and all(digest == meta['files'][name] for name, digest in inputs.items()), 'STEP differs from manifest')
    for row in meta['rows']:
        name = row['id']
        integrity = one(main['checks'], 'integrity', name)
        require(integrity.get('status') == 'pass' and integrity.get('manifest_file_binding') is True and
                integrity.get('step_sha256') == inputs.get('step/' + name + '.step'), 'main STEP integrity differs: ' + name)
    validated = validate_saved_rows(meta, main)
    require(sources == {name: sha(cv / name) for name in SOURCES}, 'receipt sources changed during derivation')
    require(manifest_hash == sha(manifest_path) and main_hash == sha(main_path) and
            all(sha(out / name) == digest for name, digest in inputs.items()), 'inputs changed during derivation')
    require(not RERUN.freshness_errors(meta, main, manifest_hash, cv), 'export sources changed during derivation')
    checks, cases = validated['checks'], validated['cases']
    failures = [r['id'] for r in checks if r['status'] == 'fail']
    return dict(purpose='Derived from the exact saved full main audit; no geometry recomputation or independent validation. '
                        'Finite poses do not qualify continuous tolerances, assembly seating or bond retention.',
                evidence_mode=MODE, geometry_recomputed=False, physical_qualified=False,
                variant=variant, lens=meta['lens'], main_scope='full', main_generated_utc=main.get('generated_utc'),
                main_summary=main['summary'], main_geometry_computed_pass=main['geometry_computed_pass'],
                manifest='out/' + variant + '/manifest.json', manifest_sha256=manifest_hash,
                verification='out/' + variant + '/verification.json', verification_sha256=main_hash,
                verification_source_sha256=sources['verify_candidate.py'], receipt_writer_sha256=sources[SELF],
                step_sha256={name[5:-5]: digest for name, digest in inputs.items() if name.startswith('step/')},
                input_file_sha256=inputs, production_insert=validated['production_insert'], sources=sources,
                sources_stable_during_run=True, inputs_stable_during_run=True, freshness_errors=[],
                stability_scope='Receipt derivation only; main CAD execution is not repeated.',
                validation=dict(method='exact_saved_rows_and_policy', policy_errors=[], matches_committed=True,
                                mismatch=[], missing=[], rows_compared=len(checks), committed_rows=len(checks)),
                rule='unchanged r7: centred >= 0.30, worst offset >= 0.10 mm; first-contact margin >= 1.0 deg',
                feasible_overlap_mm3=.001, status='fail' if failures else 'pass', failing_rows=failures,
                cases=cases, checks=checks, seconds=round(time.monotonic() - start, 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=RERUN.VARIANTS, default=RERUN.VARIANTS[0])
    parser.add_argument('--out')
    args = parser.parse_args()
    receipt = build_receipt(CV, args.variant)
    destination = Path(args.out) if args.out else HERE / ('catch-acceptance-' + args.variant + '.json')
    require(not destination.exists(), 'refusing to overwrite existing execution/receipt evidence: ' + str(destination))
    write_text(destination, json.dumps(receipt, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: receipt[k] for k in ('evidence_mode', 'variant', 'status', 'seconds')}), flush=True)
    return 0 if receipt['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
