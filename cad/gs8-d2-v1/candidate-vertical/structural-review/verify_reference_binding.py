"""Re-derive what can be re-derived of reference-export18-structural-binding.json (review VN-20, FP-15).

The structural supplement (update_concealed_vent_structure.py) scales everything from this base JSON, and the script
that wrote it is not in the repository (it is not in the upstream archive either). This check does not regenerate
it; it re-derives each field that the repository can still reproduce and lists the rest as non-reproducible
provenance (REPO-INDEX.md):
  re-derived (CAD-free): manifest_sha256 = history/reviewed-export18/manifest.json; estimated_mass_g and
    estimated_com_mm = that manifest's mass_est_g / com_est_mm; every parts[*].sha256 = the manifest's bound STEP
    hash; parts[*].valid / solids against the manifest rows; tub and panel STEP files in history/reviewed-export18
    hash to the same values; parts[*].volume_mm3 within 1e-6 relative of the manifest volume (the manifest holds
    the in-memory solid volume, the JSON the re-imported STEP volume);
  re-derived with --cad: tub and panel volumes re-imported from the history STEPs equal the JSON values within
    1e-6 mm3 (the other three part STEPs are not kept in history);
  not reproducible here: critical_region_comparisons (their reference STEPs are not in the repository), pi_mass_proxy,
    integrated_upper_body_screen, integrated_comparison_loads, unresolved_wiring_mass_sensitivity. Their inputs
    are r7's 1.6 mm lip / 1.8 mm head J4 geometry ("inherited" in the supplement means that geometry;
    (2.4/1.6)^2 = 2.25 is that geometry ratio, not a dropped load case).
Exit 0 when every re-derivable field matches; 1 otherwise. Writes nothing.
"""
import sys as _cvsys; _cvsys.path.append(str(__import__('pathlib').Path(__file__).resolve().parents[1]))  # candidate-vertical root: cv_io
from cv_io import read_text
from pathlib import Path
import argparse, hashlib, json, sys

P = Path(__file__).resolve().parent
C = P.parent
REF = P / 'reference-export18-structural-binding.json'
OLD = C / 'history/reviewed-export18'
NOT_REPRODUCIBLE = ('critical_region_comparisons', 'pi_mass_proxy', 'integrated_upper_body_screen',
                    'integrated_comparison_loads', 'unresolved_wiring_mass_sensitivity', 'all_critical_regions_equivalent')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(cad=False, ref_path=REF, old=OLD):
    ref = json.loads(read_text(ref_path))
    m = json.loads(read_text(old / 'manifest.json'))
    rows = {r['id']: r for r in m['rows']}
    out = []

    def row(ident, ok, **kw):
        out.append(dict(id=ident, status='pass' if ok else 'fail', **kw))

    row('manifest_sha256', ref['manifest_sha256'] == sha(old / 'manifest.json'))
    row('estimated_mass_g', ref['estimated_mass_g'] == m['mass_est_g'], ref=ref['estimated_mass_g'], manifest=m['mass_est_g'])
    row('estimated_com_mm', ref['estimated_com_mm'] == m['com_est_mm'])
    for name, part in ref['parts'].items():
        r = rows.get(name, {})
        row('parts/%s/sha256' % name, part['sha256'] == m['files'].get('step/%s.step' % name))
        row('parts/%s/valid_solids' % name, part['valid'] is True and part['solids'] == 1 and r.get('valid', True) is not False)
        rel = abs(part['volume_mm3'] - r.get('volume_mm3', float('nan'))) / part['volume_mm3']
        row('parts/%s/volume_vs_manifest' % name, rel <= 1e-6, relative_difference=rel)
        f = old / ('%s.step' % name)
        if f.is_file():
            row('parts/%s/history_step_sha256' % name, sha(f) == part['sha256'])
            if cad:
                import cadquery as cq
                v = cq.importers.importStep(str(f)).val().Volume()
                row('parts/%s/history_step_volume' % name, abs(v - part['volume_mm3']) <= 1e-6, step_volume_mm3=v,
                    ref_volume_mm3=part['volume_mm3'])
    missing = [k for k in NOT_REPRODUCIBLE if k not in ref]
    row('declared_non_reproducible_fields_present', not missing, missing=missing)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cad', action='store_true', help='also re-import the tub and panel STEPs kept in history')
    a = ap.parse_args(argv)
    rows = check(cad=a.cad)
    bad = [r for r in rows if r['status'] != 'pass']
    print(json.dumps(dict(reference_sha256=sha(REF), rows=rows, failures=len(bad), not_reproducible=list(NOT_REPRODUCIBLE)), indent=1))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
