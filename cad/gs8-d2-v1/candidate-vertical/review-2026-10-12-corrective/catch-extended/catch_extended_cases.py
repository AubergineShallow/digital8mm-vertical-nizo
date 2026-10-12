# SPDX-License-Identifier: MIT
"""Re-run the main bonded-catch acceptance against manifest-bound production STEPs.

The original catch-extended-*.json is immutable historical failure evidence.
This writes catch-acceptance-*.json, using the SAME pose generator, actual
production insert, feasibility checks and full-BFAR gates as the main audit.
Run through ../run_locked.py, from the repository root.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CV = HERE.parents[1]
for _p in (str(CV.parent), str(CV)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from cv_io import read_text, write_text, relpath_posix  # noqa: E402

VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
SOURCES = ('j7_collar_checks.py', 'model.py', 'steps.py', '../checks.py',
           'review-2026-10-12-corrective/catch-extended/catch_extended_cases.py')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def freshness_errors(meta, verification, manifest_digest, cv=CV):
    """Numeric agreement alone cannot authenticate a saved tub/current-cutter hybrid."""
    errors = []
    if verification.get('manifest_sha256') != manifest_digest:
        errors.append('main verification is not bound to the selected manifest')
    sources = meta.get('sources', {})
    if 'candidate-vertical/model.py' not in sources:
        errors.append('manifest lacks its production model source binding')
    for rel, digest in sources.items():
        path = cv.parent / rel
        if not path.is_file() or sha(path) != digest:
            errors.append('stale manifest geometry source: ' + rel)
    context = [r for r in verification.get('checks', []) if r.get('category') == 'j7_float' and
               r.get('id') == 'camera_model_match']
    if len(context) != 1 or context[0].get('status') != 'pass':
        errors.append('main audit lacks a passing unique camera source context')
    else:
        for field, rel in (('j7_collar_checks_sha256', 'j7_collar_checks.py'), ('steps_sha256', 'steps.py'),
                           ('r7_checks_sha256', '../checks.py')):
            if context[0].get(field) != sha(cv / rel):
                errors.append('stale main audit source: ' + rel)
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', default=VARIANTS[0], choices=VARIANTS)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    src0 = {s: sha(CV / s) for s in SOURCES}
    out_dir = CV / 'out' / a.variant
    mpath, vpath = out_dir / 'manifest.json', out_dir / 'verification.json'
    manifest0, verification0 = sha(mpath), sha(vpath)
    meta, verification = json.loads(read_text(mpath)), json.loads(read_text(vpath))
    stale = freshness_errors(meta, verification, manifest0)
    if stale:
        raise SystemExit('Current catch acceptance refused: ' + '; '.join(stale))
    import cadquery as cq
    import checks as CK
    import steps as ST
    import j7_collar_checks as J
    t0 = time.time()
    rows = {r['id']: r for r in meta['rows']}
    shapes, bound = {}, {}
    for k in sorted(rows):
        p = out_dir / 'step' / ('%s.step' % k)
        bound[k] = sha(p)
        if bound[k] != meta['files'].get('step/%s.step' % k):
            raise SystemExit('STEP %s does not match its manifest binding' % k)
        shapes[k] = cq.importers.importStep(str(p)).val()
    insert, insert_binding = J.production_insert(a.variant, meta)
    lens = J.lens_of(a.variant, meta)
    rr = J.r7_rows(shapes, rows)
    with J.candidate_layout(lens) as L:
        got = J.roll_catch_stub_rows(L, rr, shapes, CK, ST, production_insert=insert)
    checks = [dict(r, id=i, category=cat) for cat, i, r in got]
    cases = [r for r in checks if r['item'] == 'stub_feasibility']
    for rec in cases:
        functional = [r for r in checks if r.get('stub_case') == rec['stub_case'] and
                      r['item'] in ('window', 'first_contact')]
        rec['rows'] = len(functional)
        rec['fail_rows'] = [r['id'] for r in functional if r['status'] == 'fail']
        rec['min_worst_window_gap'] = min((r['worst_gap'] for r in functional if r['item'] == 'window'), default=None)
        print(json.dumps({k: rec[k] for k in ('case', 'feasible', 'stub_stock_overlap_mm3',
                                             'rows', 'min_worst_window_gap', 'fail_rows')}), flush=True)
    committed = {r['id']: r for r in verification['checks']
                 if r.get('category') == 'roll_catch' and r['id'].startswith('stub_') and
                 r['id'] != 'stub_production_context'}
    comparable = ('status', 'feasible', 'stub_stock_overlap_mm3', 'centred_gap', 'worst_gap',
                  'metal_min_deg', 'metal_max_deg', 'min_margin_deg', 'cases', 'errors', 's_values')
    mismatches = [r['id'] for r in checks if r['id'] not in committed or
                  any(r.get(k) != committed[r['id']].get(k) for k in comparable)]
    missing = sorted(set(committed) - {r['id'] for r in checks})
    stable = src0 == {s: sha(CV / s) for s in SOURCES}
    input_stable = manifest0 == sha(mpath) and verification0 == sha(vpath) and all(
        digest == sha(out_dir / 'step' / ('%s.step' % name)) for name, digest in bound.items()) and (
        insert_binding['step_sha256'] == sha(out_dir / insert_binding['step']))
    stale = freshness_errors(meta, verification, manifest0)
    validation = not mismatches and not missing and len(checks) == len(committed)
    failures = [r['id'] for r in checks if r['status'] == 'fail']
    status = 'error' if not stable or not input_stable or stale or not validation else ('fail' if failures else 'pass')
    rel = lambda p: relpath_posix(p, CV)
    result = dict(purpose='Independent rerun of main bonded-catch acceptance on production insert/host; '
                         'finite physical poses, not a continuous tolerance proof or physical qualification',
                  variant=a.variant, lens=lens, manifest=rel(mpath), manifest_sha256=manifest0,
                  verification=rel(vpath), verification_sha256=verification0, step_sha256=bound,
                  production_insert=insert_binding, sources=src0, sources_stable_during_run=stable,
                  inputs_stable_during_run=input_stable, freshness_errors=stale,
                  validation=dict(matches_committed=validation, mismatch=mismatches, missing=missing,
                                  rows_compared=len(checks), committed_rows=len(committed)),
                  rule='unchanged r7: centred >= 0.30, worst offset >= 0.10 mm; first-contact margin >= 1.0 deg',
                  feasible_overlap_mm3=J.STUB_FEASIBLE_OVERLAP_MM3,
                  status=status, failing_rows=failures, cases=cases, checks=checks,
                  seconds=round(time.time() - t0, 1))
    dest = Path(a.out) if a.out else HERE / ('catch-acceptance-%s.json' % a.variant)
    write_text(dest, json.dumps(result, indent=1, sort_keys=True) + '\n')
    print('status', status, 'validation', validation, 'failures', len(failures), flush=True)
    return 0 if status == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
