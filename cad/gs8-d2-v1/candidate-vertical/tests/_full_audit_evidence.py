# SPDX-License-Identifier: MIT
"""Read the canonical full audit without running CAD or deriving a replacement report."""
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_full_audit(test, cv, variant):
    """Fail on absent/partial/stale evidence; return the saved report unchanged.

    The manifest binds export sources. The full verifier, state model, and the
    J7/driver/J4 helpers bind separately because they are verification inputs.
    Individual tests retain responsibility for their category/value contracts.
    """
    cv = Path(cv)
    out = cv / 'out' / variant
    path = out / 'verification.json'
    test.assertTrue(path.is_file(), 'missing canonical full audit: %s' % path)
    rec = json.loads(path.read_text(encoding='utf-8'))
    test.assertEqual(rec.get('scope'), 'full', 'partial audit cannot supply full-audit evidence')
    test.assertEqual(rec.get('variant'), variant)
    test.assertEqual(rec.get('manifest_sha256'), sha(out / 'manifest.json'), 'stale full-audit manifest')
    test.assertEqual(rec.get('verification_source_sha256'), sha(cv / 'verify_candidate.py'),
                     'stale full-audit checker')
    test.assertEqual(rec.get('state_model_sha256'), sha(cv / 'steps.py'), 'stale full-audit steps')

    meta = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    sources = meta['sources']
    test.assertIn('%s/model.py' % cv.name, sources, 'manifest must bind the geometry source')
    bindings = [r for r in rec['checks'] if r['category'] == 'source_binding']
    test.assertEqual(sorted(r['id'] for r in bindings), sorted(sources),
                     'missing, duplicate, or extra export-source binding')
    for rel, digest in sources.items():
        test.assertEqual(digest, sha(cv.parent / rel), 'stale export source: %s' % rel)
    for row in bindings:
        test.assertEqual(row['status'], 'pass', row)

    def one(category, row_id):
        rows = [r for r in rec['checks'] if (r['category'], r['id']) == (category, row_id)]
        test.assertEqual(len(rows), 1, 'missing or duplicate binding: %s/%s' % (category, row_id))
        test.assertEqual(rows[0]['status'], 'pass', rows[0])
        return rows[0]

    context = one('j7_float', 'camera_model_match')
    for field, source in (('j7_collar_checks_sha256', cv / 'j7_collar_checks.py'),
                          ('steps_sha256', cv / 'steps.py'),
                          ('r7_checks_sha256', cv.parent / 'checks.py')):
        test.assertEqual(context.get(field), sha(source), 'stale J7 binding: %s' % field)
    driver = one('driver_coverage', 'screws')
    test.assertEqual(driver.get('driver_source_sha256'), sha(cv / 'driver_checks.py'),
                     'stale driver helper')
    clearance = [r for r in rec['checks'] if r['category'] == 'clearance']
    test.assertTrue(clearance, 'missing J4 helper bindings')
    for row in clearance:
        for field, source in (('j4_slide_checks_sha256', cv / 'j4_slide_checks.py'),
                              ('r7_checks_sha256', cv.parent / 'checks.py')):
            test.assertEqual(row.get(field), sha(source), 'stale J4 binding: %s' % field)
    return rec
