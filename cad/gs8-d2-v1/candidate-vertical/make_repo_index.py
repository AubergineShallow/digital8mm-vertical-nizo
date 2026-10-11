"""Pipeline index, evidence provenance and repository hygiene facts for the vertical candidate (review VN-10, VN-11,
VN-18, VN-19, VN-20; fix FP-15). CAD-free.

Writes REPO-INDEX.md (--write) or checks it (--check, exit 1 when stale or a rule fails); default prints the problems.
- Pipeline: the selected entry scripts are listed by hand (PIPELINE); their helper modules are the computed local
  import closure; every other top-level script is a study, probe or superseded runner (kept for provenance, not part
  of the selected pipeline). Moving the studies into a sub-folder would change paths that receipts and snapshots
  record, so they stay where they are and this index separates them.
- Provenance: evidence files whose producing code is not in the repository (PROVENANCE), with what still checks them.
- Absolute paths: every JSON under candidate-vertical that records a machine-local absolute path, classified frozen
  (byte-kept history), non-reproducible (listed in PROVENANCE) or pending (selected evidence whose writer is fixed and
  which the FP-16 refresh regenerates). Anything else fails.
- Path length: the longest repository-relative path and the Windows clone guidance.
"""
from cv_io import read_text, write_text
from pathlib import Path
import argparse, ast, json, re, subprocess, sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOC = 'REPO-INDEX.md'
MAX_PATH_CHARS = 132          # longest repository-relative path when this index was written (review VN-18)

PIPELINE = {
    'export': ['make_corrected_pi.py', 'export_candidate.py', 'export_cache.py', 'export_shadow_alternatives.py'],
    'checks (run_shadow_checks.py batch, then the plenum/outlet verifiers)': [
        'run_shadow_checks.py', 'verify_candidate.py', 'verify_print_meshes.py', 'verify_print_checks.py',
        'verify_csi_source.py', 'verify_power_service.py', 'verify_wire_solids.py', 'verify_hdmi.py',
        'verify_fps_integrated.py', 'verify_harness_checks.py', 'verify_shadow_usb_head.py', 'verify_microsd_service.py',
        'verify_check_scope.py', 'measure_volume.py', 'measure_comparison.py', 'verify_shadow_plenum.py',
        'verify_shadow_outlet_context.py', 'verify_wall_probe_context.py'],
    'evidence and documents': [
        'make_assembly_text.py', 'make_bom_vertical.py', 'make_wiring_vertical.py', 'make_shadow_plenum_coupon.py',
        'structural-review/update_concealed_vent_structure.py', 'structural-review/build_shadow_structural_pdf.py',
        'structural-review/verify_reference_binding.py', 'reconcile_review_evidence.py', 'review_docs_audit.py',
        'make_coverage_vertical.py', 'make_gates_vertical.py', 'make_repo_index.py', 'check_links_vertical.py'],
    'guide and renders': [
        'guide/build_guide_concealed_vents.py', 'guide/run_with_numpy_raster.py', 'guide/package_concealed_guide.py',
        'run_shadow_renders.py', 'render_review.py'],
}
SUPERSEDED = {
    'refresh_primary_evidence.py': 'the 9ced753 primary refresh runner; run_shadow_checks.py replaces it',
    'refresh_alternatives.py': 'the 9ced753 alternative-variant runner; export_shadow_alternatives.py replaces it',
    'run_review_batch.py': 'earlier batch runner; run_shadow_checks.py replaces it',
    'render_views.py': 'earlier render runner; run_shadow_renders.py replaces it',
    'run_vent_renders.py': 'renders of the rejected angled-channel trial',
    'package_delivery.py': 'the 9ced753 delivery packager (delivery-core-paths.json)',
    'guide/build_guide_vertical.py': 'the original 29-page guide builder (frozen; superseded by the concealed-vent guide)',
    'guide/package_guide.py': 'packager of the original guide',
}
# file (relative to candidate-vertical) -> (what, why it is not reproducible here, what still checks it)
PROVENANCE = {
    'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/connector-extraction.json': (
        'Pi 5 connector components extracted from the official Raspberry Pi 5 STEP (source SHA-256 78164070, THIRD-PARTY-NOTICES.md)',
        'the extractor script is not in the repository or the upstream archive; re-deriving needs the official archive (a download)',
        'each component source_sha256 equals its *-native.step (tests/test_repo_hygiene.py); readers official_pi5_geometry.py, official_pi5_csi.py, routes.py, make_corrected_pi.py'),
    'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/port-landmarks.json': (
        'Pi 5 port landmark boxes (USB2, USB3, Ethernet, GPIO, USB-C) from the same official STEP',
        'same extractor, not in the repository',
        'each object sha256 equals its *-native.step (tests/test_repo_hygiene.py); routes.py binds p_usb_pi to the usb2 landmark (test_routes_source.py)'),
    'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/*-native.step': (
        'seven native component STEPs (cam_disp0, cam_disp1, ethernet, gpio, usb2, usb3, usbc)',
        'written by the same missing extractor',
        'hash-bound by connector-extraction.json / port-landmarks.json and by the export manifests through make_corrected_pi.py'),
    'routing-snapshots/power-csi-clear-20261009-0358/independent-audit.json': (
        'independent XT30 route audit of 2026-10-09',
        'its reproduction_commands name /tmp/xt30_independent_audit/*.py on the author machine; those scripts were never committed',
        'historical only; the current power checks are verify_power_service.py and verify_wire_solids.py'),
    'out/final-check-run.json': (
        'the author run record of 2026-10-09 (main, hdmi, fps)',
        'no writer in the repository; its logs were /tmp/d2-final-*.log on the author machine and were not kept',
        'historical only; the current run record is out/compact-kowa_lm6hc/review-check-run.json (VN-07)'),
    'structural-review/reference-export18-structural-binding.json': (
        'base of the structural supplement (export18 mass, parts, critical-region equivalence, upper-body loads)',
        'its generator is not in the repository; the critical-region reference STEPs are not kept',
        'structural-review/verify_reference_binding.py re-derives the manifest, mass, centre of mass, part hashes, history STEP hashes and volumes; "inherited" there means r7 1.6 mm lip / 1.8 mm head J4 geometry'),
    'probe_power_boolean.py --archive': (
        'input of a historical boolean diagnostic: an export archive zip',
        'the archive is not in the repository (git history holds the same STEPs)',
        'not evidence; prints only'),
}
FROZEN_PREFIXES = ('history/', 'routing-snapshots/')
PENDING = {
    'routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json':
        'selected usb_head report (reconciler case usb_head); still holds the author /workspace manifest path; '
        'verify_shadow_usb_head.py now records a repo-relative path; FP-16 regenerates it',
}
# POSIX roots end in '/', at the end of a string constant, or before the closing quote in raw JSON; Windows
# separators may be doubled (raw JSON text escapes each backslash).
ABS_RE = re.compile(r'(?<![A-Za-z0-9_.])(?:/(?:tmp|workspace|home|Users|mnt|root|var/folders)(?:/|$|(?="))'
                    r'|[A-Za-z]:[\\/]+(?:Users|tmp|Temp)[\\/])')


def top_scripts(root=HERE):
    root = Path(root)
    names = [p.name for p in root.glob('*.py')] + ['guide/' + p.name for p in (root / 'guide').glob('*.py')] + \
            ['structural-review/' + p.name for p in (root / 'structural-review').glob('*.py')]
    return sorted(names)


def local_imports(rel, root=HERE):
    root = Path(root)
    p = root / rel
    tree = ast.parse(read_text(p))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            mods.add(n.module.split('.')[0])
        elif (isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)
              and ((isinstance(n.func, ast.Name) and n.func.id == '__import__') or
                   (isinstance(n.func, ast.Attribute) and n.func.attr == 'import_module'))):
            mods.add(n.args[0].value.split('.')[0])        # __import__('driver_checks') / importlib.import_module(...)
    out = set()
    for m in mods:
        for cand in (p.parent / (m + '.py'), root / (m + '.py'), root / 'guide' / (m + '.py')):
            if cand.is_file():
                out.add(cand.relative_to(root).as_posix())
                break
    return out


def closure(entries, root=HERE):
    seen, todo = set(), list(entries)
    while todo:
        r = todo.pop()
        if r in seen or not (Path(root) / r).is_file():
            continue
        seen.add(r)
        todo += sorted(local_imports(r, root) - seen)
    return seen


def roles(root=HERE):
    entries = [s for v in PIPELINE.values() for s in v]
    libs = closure(entries, root) - set(entries)
    out = {}
    for s in top_scripts(root):
        if s in entries:
            out[s] = 'pipeline'
        elif s in SUPERSEDED:
            out[s] = 'superseded'
        elif s in libs:
            out[s] = 'helper'
        elif s.startswith('test_'):
            out[s] = 'test'
        else:
            out[s] = 'study'
    return out


def absolute_paths(root=HERE):
    root = Path(root)
    hits = {}
    for p in sorted(root.rglob('*.json')):
        if 'meshes' in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        n = len(ABS_RE.findall(read_text(p)))
        if n:
            hits[rel] = n
    return hits


def classify_abs(rel):
    if rel in PENDING:
        return 'pending FP-16'
    if rel in PROVENANCE:
        return 'non-reproducible provenance'
    if rel.startswith(FROZEN_PREFIXES):
        return 'frozen history'
    return 'UNDECLARED'


def tracked_paths():
    out = subprocess.run(['git', '-C', str(REPO), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                         capture_output=True, check=True).stdout.decode('utf-8')
    return [n for n in out.split('\0') if n]


def problems(root=HERE):
    root = Path(root)
    bad = []
    entries = [s for v in PIPELINE.values() for s in v]
    bad += [('pipeline_missing', s) for s in entries + list(SUPERSEDED) if not (root / s).is_file()]
    for k in PROVENANCE:
        if '*' in k:
            if not list(root.glob(k)):
                bad.append(('provenance_missing', k))
        elif ' ' not in k and not (root / k).is_file():
            bad.append(('provenance_missing', k))
    bad += [('absolute_path_undeclared', r) for r in absolute_paths(root) if classify_abs(r) == 'UNDECLARED']
    longest = max(tracked_paths(), key=len)
    if len(longest) > MAX_PATH_CHARS:
        bad.append(('path_too_long', longest))
    return bad


def render(root=HERE):
    root = Path(root)
    r = roles(root)
    longest = max(tracked_paths(), key=len)
    out = ['# Repository index of the vertical candidate', '',
           'Generated by `make_repo_index.py`; do not edit. `make_repo_index.py --check` fails when this file is stale, an '
           'evidence file records an undeclared absolute path, or a path grows past the Windows limit below. Review '
           '2026-10-10 VN-10, VN-11, VN-18, VN-19, VN-20.', '', '## Selected pipeline', '']
    for stage, items in PIPELINE.items():
        out.append('- %s: %s' % (stage, ', '.join('`%s`' % s for s in items)))
    out += ['', 'Helper modules (the local import closure of the scripts above, computed): ' +
            ', '.join('`%s`' % s for s in sorted(k for k, v in r.items() if v == 'helper')) + '.', '',
            'Superseded runners, kept for provenance:', '']
    out += ['- `%s`: %s' % (k, v) for k, v in SUPERSEDED.items()]
    studies = sorted(k for k, v in r.items() if v == 'study')
    out += ['', 'Studies, probes and one-off generators (%d; not part of the selected pipeline, kept because snapshots '
            'and receipts record their paths and hashes): %s.' % (len(studies), ', '.join('`%s`' % s for s in studies)), '',
            'Tests: `tests/` (phase-1 and phase-2 review tests) and `test_routes_source.py` (the candidate\'s own route test).', '',
            '## Evidence produced by code that is not in the repository', '',
            '| File | What | Why not reproducible here | What still checks it |', '|---|---|---|---|']
    out += ['| `%s` | %s | %s | %s |' % (k, a, b, c) for k, (a, b, c) in PROVENANCE.items()]
    out += ['', '## Machine-local absolute paths in recorded JSON', '',
            'Writers record repository-relative POSIX paths (VN-10; `verify_shadow_usb_head.py`, `verify_check_scope.py` and the '
            'refresh runners were fixed in FP-15). These files still hold an absolute path from the machine that wrote them:', '',
            '| File | Occurrences | Class |', '|---|---|---|']
    out += ['| `%s` | %d | %s |' % (k, n, classify_abs(k)) for k, n in absolute_paths(root).items()]
    out += ['', 'Frozen history is kept byte-for-byte; pending files are regenerated by the FP-16 refresh, never hand-edited.', '',
            '## Windows path length', '',
            'The longest repository-relative path is %d characters (`%s`). Windows limits a full path to 259 characters, '
            'and git adds a `.lock` suffix while writing, so either clone into a folder whose own path is at most 120 '
            'characters, or enable long paths for the clone: `git config --global core.longpaths true` before cloning '
            '(and the Windows `LongPathsEnabled` policy for other tools). The routing-snapshot folder names are recorded '
            'in receipts and reconciler cases, so they are not shortened.' % (len(longest), longest), '',
            '## Toolchain', '',
            'Pinned environment and optional extras: `requirements-candidate-lock.txt` (base: `../../gs8-pxl-v3/cad-requirements-lock.txt`). '
            'Blender version of the 9ced753 renders: unrecorded (render receipts now record it). Guide rasterizer on '
            'Windows: `guide/run_with_numpy_raster.py`.', '']
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--write', action='store_true')
    g.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    bad = problems()
    text = render()
    if a.write and not bad:
        write_text(HERE / DOC, text)
    if a.check and (not (HERE / DOC).is_file() or read_text(HERE / DOC) != text):
        bad.append(('stale_output', DOC))
    print(json.dumps(dict(problems=bad, roles={k: sum(1 for v in roles().values() if v == k) for k in
                                                ('pipeline', 'helper', 'superseded', 'study', 'test')}), indent=1))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
