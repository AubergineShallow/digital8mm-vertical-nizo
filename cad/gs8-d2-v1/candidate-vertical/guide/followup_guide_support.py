"""Bind the three-variant catch/QT followup without importing CAD or rendering.

Failures remain useful evidence. Missing, stale, or internally inconsistent
reports are rejected; a finite-pose computed pass never closes a physical gate.
"""
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path

VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
REPORTS = {'main': ('verification.json', 'verify_candidate.py'),
           'print': ('print-checks.json', 'verify_print_checks.py'),
           'print_mesh': ('print-mesh-checks.json', 'verify_print_meshes.py')}
CATCH_DIR = 'review-2026-10-12-corrective/catch-extended'
LEGACY_HELPER_SHA256 = '2c558c90ca9f833c9ab3d11bc54565f7a80491d9fa9c474b902062a88476082d'
LEGACY_RECOMPUTE_PURPOSE = ('Independent rerun of main bonded-catch acceptance on production insert/host; '
                            'finite physical poses, not a continuous tolerance proof or physical qualification')
CATCH_COMPARE = ('status', 'feasible', 'stub_stock_overlap_mm3', 'centred_gap',
                 'worst_gap', 'metal_min_deg', 'metal_max_deg', 'min_margin_deg',
                 'cases', 'errors', 's_values', 'stub_case', 'stub_feasible',
                 'legacy_blocked_diagnostic', 'joint_face_gap_range_mm')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def bind(path, expected, files):
    path = Path(path)
    if not path.is_file() or sha(path) != expected:
        raise RuntimeError('Followup evidence changed or is absent: ' + str(path))
    files.add(path)


def catch_evidence_mode(report):
    """Normalize the executed frozen helper format without rewriting it."""
    mode = report.get('evidence_mode')
    if mode == 'saved_full_audit':
        if report.get('geometry_recomputed') is not False:
            raise RuntimeError('Saved-full-audit catch evidence must not claim geometry recomputation')
        return mode
    if (mode is None and report.get('variant') in VARIANTS and
            report.get('purpose') == LEGACY_RECOMPUTE_PURPOSE and
            report.get('sources', {}).get(CATCH_DIR + '/catch_extended_cases.py') == LEGACY_HELPER_SHA256):
        return 'same_implementation_rerun'
    raise RuntimeError('Absent or unknown catch evidence mode outside the frozen rerun format')


def validate_catch(report, main):
    """Check either supported evidence mode against the source-bound main rows."""
    mode = catch_evidence_mode(report)
    if report.get('sources_stable_during_run') is not True:
        raise RuntimeError('Catch sources changed during evidence collection')
    if report.get('inputs_stable_during_run') is not True or report.get('freshness_errors') != []:
        raise RuntimeError('Catch evidence has unstable inputs or stale source context')
    validation = report.get('validation', {})
    if (validation.get('matches_committed') is not True or validation.get('mismatch') or
            validation.get('missing')):
        raise RuntimeError('Catch evidence does not match the main audit')
    rows = report.get('checks', [])
    committed = {r['id']: r for r in main.get('checks', [])
                 if r.get('category') == 'roll_catch' and r['id'].startswith('stub_')
                 and r['id'] != 'stub_production_context'}
    by = {r['id']: r for r in rows}
    if (not rows or len(by) != len(rows) or set(by) != set(committed) or
            validation.get('rows_compared') != len(rows) or
            validation.get('committed_rows') != len(committed)):
        raise RuntimeError('Catch rows are missing, duplicated, or unaccounted for')
    for ident, row in by.items():
        if any(row.get(k) != committed[ident].get(k) for k in CATCH_COMPARE):
            raise RuntimeError('Catch evidence row differs from main audit: ' + ident)
    coverage = by.get('stub_pose_coverage', {})
    cases = report.get('cases', [])
    names = [r['case'] for r in cases]
    if (len(set(names)) != len(names) or set(names) != set(coverage.get('cases', [])) or
            coverage.get('pose_count') != len(cases) or
            coverage.get('feasible_count') != sum(r.get('feasible') is True for r in cases)):
        raise RuntimeError('Catch pose accounting differs from coverage row')
    failing = sorted(r['id'] for r in rows if r.get('status') == 'fail')
    status = 'fail' if failing else 'pass'
    if sorted(report.get('failing_rows', [])) != failing or report.get('status') != status:
        raise RuntimeError('Catch status does not preserve its failing rows')
    functional = [r for r in rows if r.get('item') in ('window', 'first_contact')]
    window = [r['worst_gap'] for r in functional if r.get('item') == 'window']
    feasible_cases = set()
    diagnostic_cases = set()
    feasible_openings = []
    for case in cases:
        row = by.get(case.get('id'), {})
        if (row.get('item') != 'stub_feasibility' or row.get('case') != case['case'] or
                row.get('feasible') != case.get('feasible')):
            raise RuntimeError('Catch case feasibility differs from its main row')
        if row.get('feasible') is True:
            feasible_cases.add(case['case'])
            opening = row.get('joint_face_gap_range_mm', [])
            if (len(opening) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in opening)
                    or opening[0] > opening[1]):
                raise RuntimeError('Feasible catch pose lacks a measured joint-face gap range')
            feasible_openings.append(opening[1])
        elif row.get('legacy_blocked_diagnostic') is True:
            diagnostic_cases.add(case['case'])
    feasible_rows = [r for r in functional if r.get('stub_case') in feasible_cases]
    diagnostic_rows = [r for r in functional if r.get('stub_case') in diagnostic_cases]
    if len(functional) != len(feasible_rows) + len(diagnostic_rows):
        raise RuntimeError('Functional catch row lacks a feasible or blocked legacy pose')
    feasible_windows = [r['worst_gap'] for r in feasible_rows if r['item'] == 'window']
    return {'status': status, 'evidence_mode': mode,
            'evidence_mode_label': 'Same-code rerun' if mode == 'same_implementation_rerun' else 'Saved full audit',
            'geometry_recomputed': mode == 'same_implementation_rerun', 'pose_count': len(cases),
            'feasible_count': coverage['feasible_count'],
            'excluded_new_pose_count': sum(not r.get('feasible') and not r.get('legacy') for r in cases),
            'legacy_blocked_diagnostic_count': sum(bool(r.get('legacy_blocked_diagnostic')) for r in cases),
            'functional_rows': len(functional), 'failing_rows': len(failing),
            'feasible_functional_rows': len(feasible_rows),
            'feasible_window_rows': sum(r['item'] == 'window' for r in feasible_rows),
            'feasible_first_contact_rows': sum(r['item'] == 'first_contact' for r in feasible_rows),
            'blocked_legacy_diagnostic_rows': len(diagnostic_rows),
            'minimum_worst_window_gap_mm': min(window) if window else None,
            'minimum_feasible_worst_window_gap_mm': min(feasible_windows) if feasible_windows else None,
            'maximum_feasible_joint_face_opening_mm': max(feasible_openings) if feasible_openings else None,
            'coverage_status': coverage.get('status'), 'physical_qualified': False}


def inspect_variants(root):
    root = Path(root)
    files = {Path(__file__)}
    variants = {}
    for variant in VARIANTS:
        export = root / 'out' / variant
        manifest_path = export / 'manifest.json'
        manifest = load(manifest_path)
        manifest_hash = sha(manifest_path)
        files.add(manifest_path)
        for name, digest in manifest['sources'].items():
            bind(root.parent / name, digest, files)
        # Supply all three mesh caches and the exact part STEP/STL inputs that
        # the main, print, and mode-labelled catch evidence actually describe.
        export_files = {name: digest for name, digest in manifest['files'].items()
                        if name.startswith(('meshes/', 'step/', 'stl/'))}
        if not any(name.startswith('meshes/') for name in export_files):
            raise RuntimeError('Missing mesh bindings for ' + variant)
        for name, digest in export_files.items():
            bind(export / name, digest, files)
        reports = {}
        for label, (filename, verifier) in REPORTS.items():
            path = export / filename
            value = load(path)
            if (value.get('variant') != variant or value.get('manifest_sha256') != manifest_hash or
                    value.get('verification_source_sha256') != sha(root / verifier)):
                raise RuntimeError('Stale ' + variant + ' ' + filename)
            files.update((path, root / verifier))
            for key, base in (('verification_dependency_sha256', root), ('helper_source_sha256', root),
                              ('input_sha256', root.parent), ('check_sources', root.parent),
                              ('checked_source_sha256', root)):
                for name, digest in value.get(key, {}).items():
                    bind(base / name, digest, files)
            reports[label] = {'path': path, 'report': value}
        main = reports['main']['report']
        if (main.get('scope') != 'full' or main.get('state_model_sha256') != sha(root / 'steps.py') or
                main.get('physical_qualified') is not False):
            raise RuntimeError('Main audit lost the current assembly binding or physical hold: ' + variant)
        actual_summary = Counter(r['status'] for r in main['checks'])
        if main.get('summary') != {s: actual_summary[s] for s in ('pass', 'fail', 'info')}:
            raise RuntimeError('Main audit summary does not match rows: ' + variant)
        catch_path = root / CATCH_DIR / ('catch-acceptance-' + variant + '.json')
        catch = load(catch_path)
        if (catch.get('variant') != variant or catch.get('manifest_sha256') != manifest_hash or
                catch.get('verification_sha256') != sha(reports['main']['path'])):
            raise RuntimeError('Stale catch evidence: ' + variant)
        files.add(catch_path)
        mode = catch_evidence_mode(catch)
        required_sources = {'model.py', 'steps.py', 'j7_collar_checks.py', '../checks.py',
                            CATCH_DIR + '/catch_extended_cases.py'}
        if mode == 'saved_full_audit':
            required_sources.update((CATCH_DIR + '/catch_saved_receipt.py', 'verify_candidate.py', 'cv_io.py'))
        if not required_sources.issubset(catch.get('sources', {})):
            raise RuntimeError('Catch evidence is missing source bindings: ' + variant)
        for name, digest in catch.get('sources', {}).items():
            bind(root / name, digest, files)
        if mode == 'saved_full_audit':
            expected_steps = {name: digest for name, digest in manifest['files'].items()
                              if name.endswith('.step')}
            if catch.get('input_file_sha256') != expected_steps:
                raise RuntimeError('Saved catch evidence omits or changes manifest STEP bindings: ' + variant)
            for name, digest in expected_steps.items():
                bind(export / name, digest, files)
            writer_path = root / CATCH_DIR / 'catch_saved_receipt.py'
            spec = importlib.util.spec_from_file_location('guide_catch_saved_receipt', writer_path)
            writer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(writer)
            expected = writer.validate_saved_rows(manifest, main)
            validation = catch.get('validation', {})
            if (catch.get('physical_qualified') is not False or catch.get('main_scope') != 'full' or
                    catch.get('main_generated_utc') != main.get('generated_utc') or
                    validation.get('method') != 'exact_saved_rows_and_policy' or
                    validation.get('policy_errors') != [] or
                    catch.get('checks') != expected['checks'] or catch.get('cases') != expected['cases'] or
                    catch.get('production_insert') != expected['production_insert']):
                raise RuntimeError('Saved catch evidence differs from exact main rows or policy: ' + variant)
        for name, digest in catch.get('step_sha256', {}).items():
            bind(export / 'step' / (name + '.step'), digest, files)
        insert = catch.get('production_insert', {})
        insert_path = export / insert.get('step', '__missing_insert__')
        bind(insert_path, insert.get('step_sha256'), files)
        if (insert.get('manifest_file_binding') is not True or
                insert.get('step_sha256') != manifest['files'].get(insert.get('step'))):
            raise RuntimeError('Catch production insert differs from its manifest: ' + variant)
        summary = validate_catch(catch, main)
        variants[variant] = {'manifest_path': manifest_path, 'manifest_sha256': manifest_hash,
                             'manifest': manifest, 'export_files': export_files,
                             'reports': reports, 'catch_path': catch_path, 'catch': catch,
                             'catch_summary': summary,
                             'harness_scope': 'compact-only bound study' if variant == VARIANTS[0]
                             else 'No variant-specific harness/service solve; unqualified'}
    return {'variants': variants, 'files': sorted(files)}
