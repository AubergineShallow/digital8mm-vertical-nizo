# SPDX-License-Identifier: MIT
"""CAD-free evidence rules shared by the verifiers, the reconciler and the docs audit (review 2026-10-10, FP-04).

* Numbers that documents repeat are formatted from their source rows, never typed (VN-08): the inherited
  physical-gate count from the r7 build receipt, the cooler/source-Pi witness from the main-audit row, and the
  rigid-power poses/queries from the power report.
* Manifest rows are compared with a stated numeric tolerance; ids, kinds and sources stay exact (VN-06).
* A keepout overlap is info only with that keepout's declared mating partner (VN-31).
* The exact info-row set the reconciler accepts from the main audit, and the exact print-check failure set (VN-31).
* Selected-folder hygiene: every JSON report in a selected output folder binds the selected manifest, or is
  declared historical together with the manifest it must bind (VN-09).
* evaluate_docs_audit(): the failure list behind review_docs_audit.py's exit code (VN-05).
* FX-D (2026-10-11): FPS counts / status / hit volume and core-void intervals in the documents are checked against
  their reports, unfilled [[FX-NUM:...]] placeholders fail, and every path/git_object + sha256 pair in
  CHECKPOINT-STATUS.json must match what it names.
Nothing here imports CAD; every function is pure apart from reading the named JSON files.
"""
from cv_io import read_text
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
R7_BUILD_RECEIPT = '../out/build-receipt.json'          # relative to candidate-vertical; r7 hardware_gates.gates
UNRECORDED = 'unrecorded (deterministic output, FP-04)'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(read_text(p))


# ------------------------------------------------------------------ numbers from source rows (VN-08)

def inherited_gates(root=HERE):
    """Inherited r7 physical gates, counted from the r7 build receipt (the same rule as r7 audit_cloud_release.py)."""
    p = (Path(root) / R7_BUILD_RECEIPT).resolve()
    gates = read(p)['hardware_gates']['gates']
    return dict(total=len(gates), open=sum(v.startswith('open') for v in gates.values()),
                withdrawn=sum(v.startswith('withdrawn') for v in gates.values()),
                source=R7_BUILD_RECEIPT, field='hardware_gates.gates', source_sha256=sha(p))


def dependency_mismatches(report, root=HERE):
    """[(field, path)] for every helper_source_sha256 entry (paths relative to candidate-vertical) and input_sha256 entry
    (relative to cad/gs8-d2-v1) of a run report that no longer matches the current file, plus the single-file bindings
    state_model_sha256 (steps.py), terminal_rule_source_sha256 (wire_terminal_rules.py) and a string
    helper_source_sha256 (power_geometry.py, the wire check). fixup-1 (FP-12): a rule change in a helper invalidates
    the report as a verifier change does."""
    root = Path(root)
    out = []
    single = {'state_model_sha256': 'steps.py', 'terminal_rule_source_sha256': 'wire_terminal_rules.py'}
    for field, base in (('helper_source_sha256', root), ('input_sha256', root.parent)):
        items = report.get(field)
        if isinstance(items, str) and field == 'helper_source_sha256':
            items = {'power_geometry.py': items}
        for rel, h in sorted((items or {}).items()):
            p = base / rel
            if not p.is_file() or sha(p) != h:
                out.append((field, rel))
    for field, rel in single.items():
        if field in report and (not (root / rel).is_file() or sha(root / rel) != report[field]):
            out.append((field, rel))
    return out


def main_audit_row(verification, category, ident):
    rows = [c for c in verification.get('checks', []) if c.get('category') == category and c.get('id') == ident]
    return rows[0] if len(rows) == 1 else None


def cooler_witness_mm3(verification):
    """overlap_mm3 of the main-audit interference row pi5/cooler (the retained active rigid failure), or None."""
    row = main_audit_row(verification, 'interference', 'pi5/cooler')
    return None if row is None else row.get('overlap_mm3')


def fmt_mm3(v):
    return '%.6f' % v


def power_counts(report):
    return dict(poses=report['poses'], queries=report['exact_intersections'], hits=len(report['hits']))


# ------------------------------------------------------------------ numeric row comparison (VN-06)

ABS_TOL = 1e-6      # mm (and the same absolute value for g / mm3 fields)
REL_TOL = 1e-9


def same_value(a, b, abs_tol=ABS_TOL, rel_tol=REL_TOL):
    """Numbers within max(abs_tol, rel_tol*max(|a|,|b|)); bools, strings, None and keys exact; lists element-wise."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not (math.isfinite(a) and math.isfinite(b)):
            return a == b
        return abs(a - b) <= max(abs_tol, rel_tol * max(abs(a), abs(b)))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_value(x, y, abs_tol, rel_tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same_value(a[k], b[k], abs_tol, rel_tol) for k in a)
    return type(a) is type(b) and a == b


def changed_rows(old_rows, new_rows):
    """Ids whose manifest row differs beyond the numeric tolerance (inventories must already match)."""
    return [k for k in old_rows if not same_value(old_rows[k], new_rows[k])]


# ------------------------------------------------------------------ keepouts and the accepted info set (VN-31)

# A keepout is a non-material mating envelope. Its overlap is info ONLY with the part it mates with.
KEEPOUT_MATING_PARTNERS = {
    'usb_storage_plug_reserve': ('pi5', 'usb_stick'),   # USB-A plug envelope: Pi USB3 receptacle; the stick carrying it
}


def keepout_mating_info(a, b, kinds):
    for k, other in ((a, b), (b, a)):
        if kinds.get(k) == 'keepout' and other in KEEPOUT_MATING_PARTNERS.get(k, ()) and kinds.get(other) != 'printed':
            return True
    return False


MAIN_AUDIT_INFO = frozenset(
    [('non_material_keepout', 'pi5/usb_storage_plug_reserve'),
     ('interference', 'eyepiece/eyecup'), ('interference', 'eyepiece/panel')]
    + [('interference', 'tub/' + p) for p in ('p_panel1', 'p_panel2', 'p_panel3', 'p_panel4',
                                             'p_carrier1', 'p_carrier2', 'p_grip')]
    + [('nominal_features', n) for n in ('panel_screw_bearing_land', 'panel_head_radial_wall',
                                         'carrier_PT_head_radial_wall', 'carrier_M25_head_radial_wall',
                                         'carrier_M25_thread_engagement', 'collar_hoop_nominal',
                                         'collar_relief_nominal_after_bed_chamfer')]
    + [('physical', 'qualification')])


def open_motion_ids():
    """Motions the assembly-state model declares 'open' (with an open_reason); verify_candidate.py reports each as an
    info row motion_coverage/<id>."""
    import steps
    return sorted(mid for mid, m in steps.MOTIONS.items() if m['runner'] == 'open')


def expected_main_info():
    return set(MAIN_AUDIT_INFO) | {('motion_coverage', m) for m in open_motion_ids()} | set(__import__('j7_collar_checks').INFO_ROWS)  # FP-08 (VN-24): J7-R family WARN rows, not yet in the committed verification.json (FP-16)


def info_set_findings(verification, expected=None):
    """[(code, category, id)]: info rows the reconciler did not accept, and accepted rows that vanished."""
    expected = expected_main_info() if expected is None else set(expected)
    got = {(c['category'], c['id']) for c in verification.get('checks', []) if c.get('status') == 'info'}
    return ([('unexpected_info_row',) + k for k in sorted(got - expected)]
            + [('missing_info_row',) + k for k in sorted(expected - got)])


# Print checks (FP-09, verify_print_checks.py): failures the reconciler accepts. Empty: every current failure is a
# CAD-phase defect (VN-51..VN-58) that must be fixed, not accepted.
EXPECTED_PRINT_FAILURES = {}


def print_failure_findings(report, expected=None):
    expected = EXPECTED_PRINT_FAILURES if expected is None else expected
    got = {k: sorted(v) for k, v in report.get('failing', {}).items() if v}
    want = {k: sorted(v) for k, v in expected.items() if v}
    return [] if got == want else [('print_failures_differ', json.dumps(got, sort_keys=True), json.dumps(want, sort_keys=True))]


# Harness checks (FP-10, verify_harness_checks.py): failures the reconciler accepts. Empty: every current failure is a
# CAD/docs-phase defect or a documented user decision (VN-47, VN-62), never accepted here.
EXPECTED_HARNESS_FAILURES = {}


def harness_failure_findings(report, expected=None):
    expected = EXPECTED_HARNESS_FAILURES if expected is None else expected
    got = {k: sorted(v) for k, v in report.get('failing', {}).items() if v}
    want = {k: sorted(v) for k, v in expected.items() if v}
    return [] if got == want else [('harness_failures_differ', json.dumps(got, sort_keys=True), json.dumps(want, sort_keys=True))]


# ------------------------------------------------------------------ selected-folder hygiene (VN-09)

# Reports that stay at their path although they bind another manifest: path (relative to candidate-vertical) ->
# (manifest they must bind, relative to candidate-vertical; reason). Anything else foreign moves to history/.
DECLARED_HISTORICAL = {
    'out/compact-kowa_lm6hc/wall-probe-context.json': (
        'history/reviewed-export18/manifest.json',
        'Frozen export18 right-wall probe supplement. The concealed guide builder reads it at this path and the guide '
        'receipt binds it here; historical context only, never current evidence.'),
    'out/fps-service-study/integrated-fps-export18-checks.json': (
        'history/reviewed-export18/manifest.json', 'Frozen export18 FPS integrated check; history only.'),
    'history/stale-selected-reports-2026-10-10/ventilation-checks.json': (
        'vent-study/angled-channel-trial/manifest.json', 'Rejected angled-channel trial report (moved out of the '
        'selected folder by FP-04).'),
}
SKIP_DIRS = frozenset({'step', 'stl', 'meshes', 'check-logs'})


def bound_manifest(report):
    for path in ('manifest_sha256', 'mechanical_manifest_sha256', 'mechanical.manifest_sha256'):
        v = report
        for k in path.split('.'):
            v = v.get(k) if isinstance(v, dict) else None
        if isinstance(v, str):
            return v
    return None


def historical_binding(rel, root=HERE):
    """(ok, detail) for a DECLARED_HISTORICAL report: it exists and binds exactly its declared manifest."""
    want_path, _ = DECLARED_HISTORICAL[rel]
    p, m = Path(root) / rel, Path(root) / want_path
    if not p.is_file():
        return False, 'missing'
    want = sha(m) if m.is_file() else None
    got = bound_manifest(read(p))
    return got is not None and got == want, 'binds %s, declared %s = %s' % (
        (got or 'nothing')[:8], want_path, (want or 'missing')[:8])


def selected_folder_findings(folder, manifest_sha, root=HERE):
    """[(code, path, detail)] for every JSON in a selected output folder that does not bind manifest_sha, unless it is
    DECLARED_HISTORICAL and binds its declared manifest. manifest.json and cache/STEP/STL/log folders are skipped."""
    folder, root = Path(folder), Path(root)
    out = []
    for p in sorted(folder.rglob('*.json')):
        inner = p.relative_to(folder).as_posix()
        if inner == 'manifest.json' or SKIP_DIRS & set(inner.split('/')[:-1]):
            continue
        rel = p.relative_to(root).as_posix() if p.is_relative_to(root) else inner
        if rel in DECLARED_HISTORICAL:
            ok, detail = historical_binding(rel, root)
            if not ok:
                out.append(('historical_report_binding', rel, detail))
            continue
        try:
            data = read(p)
        except ValueError as e:
            out.append(('unreadable_report', rel, str(e)[:120]))
            continue
        bound = bound_manifest(data) if isinstance(data, dict) else None
        if bound is None:
            out.append(('unbound_report', rel, 'no manifest_sha256 / mechanical_manifest_sha256 field'))
        elif bound != manifest_sha:
            out.append(('foreign_manifest_report', rel, 'binds %s, selected manifest %s' % (bound[:8], manifest_sha[:8])))
    return out


# ------------------------------------------------------------------ document numbers vs source rows (VN-08)

import re as _re

_MM3 = _re.compile(r'(\d+\.\d{4,})\s*mm(?:3|³)')
_POWER = _re.compile(r'(\d+)\s*(?:rigid\s+power-service\s+)?poses\s*/\s*(\d+)\s*(?:exact\s+)?queries')
_GATES = [_re.compile(r'(?i)(?:\b|all)(\d+)\s*inherited\s+(?:physical\s+)?gates'),
          _re.compile(r'"open_inherited_gates":\s*(\d+)'), _re.compile(r'(?i)\bbaseline\s*(\d+)\s*and\s*M1')]
_HISTORY_WORDS = ('export18', 'historical', 'frozen')
NUMBER_DOCUMENTS = ['README.md', 'REVIEW.md', 'ASSEMBLY-VERTICAL.md', 'MEASUREMENTS-TO-CLOSE.md', 'REPRODUCE.md',
                    'BOM-VERTICAL.md', 'BOM-VERTICAL.csv', 'CHECKPOINT-STATUS.json',
                    'structural-review/CONCEALED-VENT-STRUCTURAL.md', 'out/compact-kowa_lm6hc/current-review-evidence.json',
                    # Manifest text is generated from model/source helpers at export (e.g. provenance cooler_hold).
                    'out/compact-kowa_lm6hc/manifest.json', 'out/compact-fujinon_hf6xa/manifest.json',
                    'out/original-kowa_lm6hc/manifest.json']


def number_sources(root=HERE):
    """The source rows the repeated figures come from (current selected reports and frozen export18 history)."""
    root = Path(root)
    cur, old = root / 'out/compact-kowa_lm6hc', root / 'history/reviewed-export18'
    src = {'gates': inherited_gates(root)}
    for key, folder in (('current', cur), ('export18', old)):
        v = folder / 'verification.json'
        w = cooler_witness_mm3(read(v)) if v.is_file() else None
        pw = folder / 'power-service-checks.json'
        src[key] = {'cooler_witness_mm3': w, 'cooler_witness_text': None if w is None else fmt_mm3(w),
                    'power': power_counts(read(pw)) if pw.is_file() else None,
                    'verification': v.relative_to(root).as_posix(), 'power_report': pw.relative_to(root).as_posix()}
    src['fps'] = {}
    for era, rel in FPS_REPORTS.items():
        s = fps_summary(root / rel)
        src['fps'][era] = None if s is None else dict(s, report=rel)
    src['core_void'] = {}
    for v in VOID_VARIANTS:
        p = root / (VOID_REPORT % v)
        iv = read(p).get(VOID_FIELD) if p.is_file() else None
        src['core_void'][v] = None if iv is None else {'interval': list(iv), 'report': VOID_REPORT % v, 'field': VOID_FIELD}
    return src


def _sentence(text, start, end):
    a = max(text.rfind('\n', 0, start), text.rfind('. ', 0, start), text.rfind('|', 0, start))
    bs = [i for i in (text.find('\n', end), text.find('. ', end), text.find('|', end)) if i >= 0]
    return text[a + 1:min(bs) if bs else len(text)]


def document_number_findings(name, text, src):
    """[(code, document, found, expected, context)] for repeated figures that differ from their source row."""
    out = []
    for m in _MM3.finditer(text):
        ctx = _sentence(text, m.start(), m.end())
        if 'cooler' not in ctx.lower():
            continue
        era = 'export18' if any(w in ctx.lower() for w in _HISTORY_WORDS) else 'current'
        want = src[era]['cooler_witness_text']
        if m.group(1) != want:
            out.append(('cooler_witness_number', name, m.group(1), '%s (%s %s)' % (want, era, src[era]['verification']), ctx.strip()[:160]))
    for m in _POWER.finditer(text):
        ctx = _sentence(text, m.start(), m.end())
        era = 'export18' if any(w in ctx.lower() for w in _HISTORY_WORDS) else 'current'
        p = src[era]['power']
        got = (int(m.group(1)), int(m.group(2)))
        if p is None or got != (p['poses'], p['queries']):
            out.append(('power_query_number', name, '%d/%d' % got, '%s (%s %s)' % (
                None if p is None else '%d/%d' % (p['poses'], p['queries']), era, src[era]['power_report']), ctx.strip()[:160]))
    for rx in _GATES:
        for m in rx.finditer(text):
            if int(m.group(1)) != src['gates']['open']:
                out.append(('inherited_gate_number', name, m.group(1), '%d (%s %s)' % (
                    src['gates']['open'], src['gates']['source'], src['gates']['field']), _sentence(text, m.start(), m.end()).strip()[:160]))
    if src.get('fps') is not None:
        out += fps_number_findings(name, text, src)
    if src.get('core_void') is not None:
        out += core_void_number_findings(name, text, src)
    out += placeholder_findings(name, text)
    return out


# ------------------------------------------------------------------ FPS, core-void and placeholder figures (FX-D)
# Added 2026-10-11 (phase-2 verifier finding): the rules above covered the cooler witness, the power counts and the
# gate count only, so REVIEW.md kept "332 material checks / zero hits" after the selected FPS report failed.
# "material checks" is the FPS report's phrase in these documents (static_and_carried_checks rows). A sentence is
# historical when it names export18 / historical / frozen; otherwise it is current when it carries a current marker
# (now, selected, refreshed); otherwise a sentence that opens with a back-reference (Its, Their, These, ...) takes
# the era of the sentence before it on the same line (so "Its 288 pass ... 332 clear FPS material checks" after
# "Reviewed export18 is frozen history." is history); otherwise it is current. Historical FPS claims are checked
# against the export18 FPS report; historical core-void intervals have no source here and are skipped. Unfilled
# [[FX-NUM:...]] placeholders are also looked for in every other candidate Markdown page (PLACEHOLDER_SKIP aside).

FPS_REPORTS = {'current': 'out/fps-service-study/integrated-fps-checks.json',
               'export18': 'out/fps-service-study/integrated-fps-export18-checks.json'}
VOID_REPORT = 'out/comparison/volume-%s.json'
VOID_FIELD = 'model_void_interval_cm3_outward_rounded'
VOID_VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
_VOID_NAMES = (('compact kowa', 'compact-kowa_lm6hc'), ('compact fujinon', 'compact-fujinon_hf6xa'),
               ('original-storage kowa', 'original-kowa_lm6hc'), ('original kowa', 'original-kowa_lm6hc'))
_HISTORY_RE = _re.compile(r'(?i)export18|historical|frozen')
_CURRENT_RE = _re.compile(r'(?i)\b(now|selected|refreshed)\b')
_WORDNUM = dict(zero=0, no=0, one=1, two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10,
                eleven=11, twelve=12)
_N = r'(\d+|zero|no|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)'
_FPS_OF = _re.compile(r'(?i)(\d+)\s+of\s+(\d+)\s+(?:FPS\s+)?material\s+checks\s+(?:are\s+)?clear(?:,?\s*and\s+' + _N + r'\s+hit)?')
_FPS_HITS = _re.compile(r'(?i)(\d+)\s+(?:FPS\s+)?material\s+checks?\s*(?:/|,|with|:)\s*' + _N + r'\s+hits?\b')
_FPS_CLEAR = _re.compile(r'(?i)(\d+)\s+clear\s+(?:FPS\s+)?material\s+checks')
_FPS_DIAG = _re.compile(r'(?i)\b' + _N + r'\s+(?:separate\s+)?(clear\s+)?(?:non-material|keepout)\s+(?:[\w-]+\s+)?diagnostics?')
_FPS_STATUS = _re.compile(r'\bFPS\b(?:\s+[\w-]+){0,3}?\s+\**(passes|passed|fails|failed)\**')
_FPS_MM3 = _re.compile(r'(\d+\.\d+)\s*mm(?:3|³)')
_VOID = _re.compile(r'(\d+)\s*[–-]\s*(\d+)\s*cm(?:3|³)')
_PLACEHOLDER = _re.compile(r'\[\[FX-NUM:([^\]]*)\]\]')


def _num(s):
    return int(s) if s.isdigit() else _WORDNUM[s.lower()]


_BACKREF = _re.compile(r'^\W*(its|their|these|they|this|that|both)\b', _re.I)


def _sentence_start(text, start):
    return max(text.rfind('\n', 0, start), text.rfind('. ', 0, start), text.rfind('|', 0, start)) + 1


def _era(text, start, end, depth=2):
    ctx = _sentence(text, start, end)
    if _HISTORY_RE.search(ctx):
        return 'export18', ctx
    if _CURRENT_RE.search(ctx):
        return 'current', ctx
    a = _sentence_start(text, start)
    # "Its 288 pass ... 332 clear FPS material checks" after "Reviewed export18 is frozen history." takes the era of
    # the sentence it refers back to (same line only, at most two sentences back).
    if depth and _BACKREF.match(ctx) and a >= 2 and text[a - 1] == '.':     # a is the ' ' of the '. ' delimiter
        return _era(text, a - 1, a - 1, depth - 1)[0], ctx
    return 'current', ctx


def fps_summary(report_path):
    """Status and counts of an integrated FPS report (None if absent)."""
    p = Path(report_path)
    if not p.is_file():
        return None
    d = read(p)
    rows = d['static_and_carried_checks']
    hits = [h['overlap_mm3'] for r in rows for h in r['hits']]
    diag = d.get('non_material_reservation_diagnostics', [])
    return {'status': d['status'], 'total': len(rows), 'hit_rows': sum(bool(r['hits']) for r in rows),
            'clear_rows': sum(not r['hits'] for r in rows), 'max_hit_mm3': max(hits) if hits else None,
            'diagnostics': len(diag), 'diagnostics_clear': all(not r['hits'] for r in diag)}


def fps_number_findings(name, text, src):
    """[(code, document, found, expected, context)] for FPS counts, hit volumes and pass/fail claims that differ from
    the integrated FPS report of their era."""
    out = []

    def check(m, era, ctx, code, got, want):
        if got != want:
            s = src['fps'].get(era)
            out.append((code, name, str(got), '%s (%s %s)' % (want, era, None if s is None else s['report']), ctx.strip()[:160]))

    def summary(era):
        return src['fps'].get(era) or {}

    for m in _FPS_OF.finditer(text):
        era, ctx = _era(text, m.start(), m.end())
        s = summary(era)
        check(m, era, ctx, 'fps_check_number', '%s of %s clear' % (m.group(1), m.group(2)),
              '%s of %s clear' % (s.get('clear_rows'), s.get('total')))
        if m.group(3):
            check(m, era, ctx, 'fps_check_number', '%d hit' % _num(m.group(3)), '%s hit' % s.get('hit_rows'))
    for m in _FPS_HITS.finditer(text):
        era, ctx = _era(text, m.start(), m.end())
        s = summary(era)
        check(m, era, ctx, 'fps_check_number', '%s checks / %d hits' % (m.group(1), _num(m.group(2))),
              '%s checks / %s hits' % (s.get('total'), s.get('hit_rows')))
    for m in _FPS_CLEAR.finditer(text):
        era, ctx = _era(text, m.start(), m.end())
        s = summary(era)
        check(m, era, ctx, 'fps_check_number', '%s clear checks of %s' % (m.group(1), m.group(1)),
              '%s clear checks of %s' % (s.get('clear_rows'), s.get('total')))
    for m in _FPS_DIAG.finditer(text):
        era, ctx = _era(text, m.start(), m.end())
        s = summary(era)
        check(m, era, ctx, 'fps_check_number', '%d diagnostics' % _num(m.group(1)), '%s diagnostics' % s.get('diagnostics'))
        if m.group(2):
            check(m, era, ctx, 'fps_check_number', 'diagnostics clear', 'diagnostics clear' if s.get('diagnostics_clear') else 'diagnostics with hits')
    for m in _FPS_STATUS.finditer(text):
        era, ctx = _era(text, m.start(), m.end())
        st = str(summary(era).get('status', 'missing'))
        claim = 'fail' if m.group(1).startswith('fail') else 'pass'
        check(m, era, ctx, 'fps_status_claim', claim, 'fail' if st.startswith('fail') else 'pass' if 'pass' in st else st)
    # Hit volume: the first mm3 figure within 120 characters after a non-zero FPS hit count ("7 hit the tub (switch
    # bundle ..., 23.131 mm3"), rounded to the decimals the document uses, vs the report's largest hit overlap.
    hit_claims = [m for m in _FPS_OF.finditer(text) if m.group(3) and _num(m.group(3))] + \
                 [m for m in _FPS_HITS.finditer(text) if _num(m.group(2))]
    for m in hit_claims:
        era, ctx = _era(text, m.start(), m.end())
        v = _FPS_MM3.search(text, m.end(), min(len(text), m.end() + 120))
        if v is None:
            continue
        mx = summary(era).get('max_hit_mm3')
        want = None if mx is None else '%.*f' % (len(v.group(1).split('.')[1]), mx)
        check(m, era, ctx, 'fps_hit_volume', v.group(1), want)
    return out


def core_void_number_findings(name, text, src):
    """Current core-void intervals (A–B cm3 followed by a variant name or its volume report link) vs the report's
    model_void_interval_cm3_outward_rounded."""
    out = []
    for m in _VOID.finditer(text):
        era, ctx = _era(text, m.start(), m.end())
        tail = text[m.end():m.end() + 160].lower()
        cands = [(tail.find(k), v) for k, v in _VOID_NAMES if k in tail]
        cands += [(tail.find('volume-%s.json' % v), v) for v in VOID_VARIANTS if 'volume-%s.json' % v in tail]
        if not cands or era != 'current':
            continue
        variant = min(cands)[1]
        s = src['core_void'].get(variant)
        want = None if s is None else '%d-%d' % tuple(s['interval'])
        got = '%s-%s' % (m.group(1), m.group(2))
        if got != want:
            out.append(('core_void_interval', name, got, '%s (%s %s)' % (want, variant, VOID_REPORT % variant), ctx.strip()[:160]))
    return out


def placeholder_findings(name, text):
    """An unfilled [[FX-NUM:<name>]] token marks a figure that must come from a refreshed report before release."""
    return [('unfilled_number_placeholder', name, m.group(0), 'a figure from its source report', _sentence(text, m.start(), m.end()).strip()[:160])
            for m in _PLACEHOLDER.finditer(text)]


# ------------------------------------------------------------------ CHECKPOINT-STATUS.json hash pairs (FX-D)

def _git_blob(obj, root):
    import subprocess
    try:
        r = subprocess.run(['git', 'show', obj], cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def checkpoint_hash_pairs(status, root=HERE, git_blob=None):
    """Every {path|git_object, sha256} pair in CHECKPOINT-STATUS.json with the hash of what it names.

    path is relative to candidate-vertical (a working-tree file); git_object is '<commit>:<repo path>' (a committed
    blob). evidence_reconciler_that_wrote_current_evidence must also equal the reconciler_sha256 recorded inside the
    selected evidence file it claims to have written."""
    root = Path(root)
    git_blob = git_blob or (lambda obj: _git_blob(obj, root))
    rows = []

    def walk(o, field):
        if isinstance(o, dict):
            if isinstance(o.get('sha256'), str) and ('path' in o or 'git_object' in o):
                if 'path' in o:
                    p = root / o['path']
                    actual = sha(p) if p.is_file() else None
                    rows.append(dict(field=field, kind='path', target=o['path'], recorded=o['sha256'], actual=actual))
                else:
                    blob = git_blob(o['git_object'])
                    actual = None if blob is None else hashlib.sha256(blob).hexdigest()
                    rows.append(dict(field=field, kind='git_object', target=o['git_object'], recorded=o['sha256'], actual=actual))
            for k, v in o.items():
                walk(v, '%s.%s' % (field, k) if field else k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, '%s[%d]' % (field, i))

    walk(status, '')
    w, ev = status.get('evidence_reconciler_that_wrote_current_evidence'), status.get('selected_evidence')
    if isinstance(w, dict) and isinstance(ev, dict):
        p = root / ev.get('path', '')
        recorded = read(p).get('reconciler_sha256') if p.is_file() else None
        rows.append(dict(field='evidence_reconciler_that_wrote_current_evidence.sha256', kind='writer_of_selected_evidence',
                         target='%s reconciler_sha256' % ev.get('path'), recorded=w.get('sha256'), actual=recorded))
    for r in rows:
        r['match'] = r['actual'] is not None and r['actual'] == r['recorded']
    return rows


def documents_number_findings(root=HERE, names=None, src=None):
    root = Path(root)
    src = number_sources(root) if src is None else src
    out = []
    for n in (NUMBER_DOCUMENTS if names is None else names):
        p = root / n
        if p.is_file():
            out += document_number_findings(n, read_text(p), src)
    if names is None:      # FX-D: unfilled placeholders anywhere else in the candidate's live Markdown pages
        for p in sorted(root.rglob('*.md')):
            rel = p.relative_to(root).as_posix()
            if rel not in NUMBER_DOCUMENTS and not set(rel.split('/')[:-1]) & PLACEHOLDER_SKIP:
                out += placeholder_findings(rel, read_text(p))
    return out


# Folders whose Markdown is not scanned for placeholders: frozen history, the review records (the fix log names the
# placeholder tokens it left) and generated or cache folders.
PLACEHOLDER_SKIP = frozenset({'history', 'review-2026-10-10', 'meshes', '__pycache__', 'step', 'stl', 'check-logs'})


# ------------------------------------------------------------------ docs-audit verdict (VN-05)

CURRENT_ROLE = 'current manifest-bound scoped evidence'
HEAD_CURRENT_ROLE = 'current manifest-bound limited head reservation'


def evaluate_docs_audit(a):
    """Verdict of a review_docs_audit.py result: failures (exit 1), rebuildable caches only (exit 3) or clean (0).

    Selected evidence must bind the current manifest and current verifier; declared-historical reports must bind
    their declared manifest; declared-pending items (FP-13 alternative audits) are listed, not failed."""
    F, R, N = [], [], []

    def fail(code, *detail):
        F.append([code] + [str(x) for x in detail])

    def cache(state, label, action):
        if state == 'cache_missing':
            R.append([label, action])
        elif state != 'complete':
            fail('bound_files', label, state, action)

    def binding(label, path, b):
        if b is not None and not b.get('pass'):
            fail('binding', path, label, 'missing %d changed %d: %s' % (
                len(b['missing']), len(b['changed']), ', '.join((b['missing'] + b['changed'])[:5])))

    for v in a['variants']:
        name = v['variant']
        binding('sources', 'out/%s/manifest.json' % name, v['sources'])
        cache(v['bound_cache']['state'], name, v['bound_cache']['action'])
        if v['bound_cache']['state'] == 'complete' and not v['mesh_manifest_identical']:
            fail('mesh_manifest_copy', name)
        if v['printed_count'] != v['expected_printed_count']:
            fail('printed_count', name, v['printed_count'], v['expected_printed_count'])
        for k in ('printed_valid_one_solid', 'keepouts_non_material'):
            if not v[k]:
                fail(k, name)
        for f in v.get('selected_folder_findings', []):
            fail(*f)
        for r in v['reports']:
            if r.get('declared_pending'):
                N.append([r['path'], r['declared_pending']])
            elif r.get('missing'):
                fail('selected_report_missing', r['path'])
            elif not r['same_manifest']:
                fail('stale_selected_report', r['path'], 'binds manifest %s' % str(r['manifest_sha256'])[:8])
            elif not r['verifier_hash_current']:
                fail('stale_selected_report', r['path'], 'verifier %s changed since the report' % r['verifier_file'])
    b = a['bom']
    if not b['generator_outputs_current']:
        fail('bom_outputs_stale', 'make_bom_vertical.py --check')
    for x in b['invalid_parent_references']:
        fail('bom_parent_reference', *x)
    for x in b['missing_local_sources']:
        fail('bom_missing_source', *x)
    if b['cad_imported']:
        fail('cad_imported', 'the docs audit must stay CAD-free')
    if b.get('export18_selection_claim', {}).get('claimed') and not a['concealed_bom_preservation']['unchanged']:
        fail('bom_claim', 'BOM-VERTICAL.md claims purchased selections are unchanged from export18, but %d line(s) differ'
             % len(a['concealed_bom_preservation']['differences']))
    for x in a['missing_document_local_links']:
        fail('missing_local_link', x['document'], x['target'])

    def report(r, current_role=CURRENT_ROLE):
        if r.get('declared_historical'):
            if not r.get('historical_binding_ok'):
                fail('historical_report_binding', r['path'], r.get('historical_binding'))
            return
        if r.get('pending'):
            fail('selected_report_missing', r['path'])
            return
        if 'evidence_role' in r and r['evidence_role'] != current_role:
            fail('stale_selected_report', r['path'], r['evidence_role'])
        elif r.get('same_primary_manifest') is False:
            fail('stale_selected_report', r['path'], 'binds another manifest')
        elif r.get('verifier_hash_current') is False:
            fail('stale_selected_report', r['path'], 'verifier %s changed since the report' % r.get('verifier_file'))
        for k in ('helper_bindings', 'verification_dependencies', 'step_bindings', 'checked_sources', 'saved_material_bindings'):
            binding(k, r['path'], r.get(k))
        if r.get('frozen_input_matches') is False:
            fail('binding', r['path'], 'frozen input')

    for r in a['selected_supplemental_reports']:
        report(r)
    for r in a['concealed_vent_reports']:
        report(r)
    for key, x in a['report_inputs'].items():
        if not x['matches_report']:
            fail('report_input', key, x['path'])
    for item in a['assembly_comparison']['candidate_manifest_bindings']:
        for variant, ok in item.items():
            if not ok:
                fail('stale_selected_report', 'out/comparison/assembled-comparison.json', 'binds an old %s manifest' % variant)
    for r in a['core_void_reports']:
        if not r['same_variant_manifest']:
            fail('stale_selected_report', r['path'], 'binds another manifest')
        elif not r['verifier_hash_current']:
            fail('stale_selected_report', r['path'], 'verifier measure_volume.py changed since the report')
    head = a.get('selected_usb_head_report')
    if head is None:
        fail('selected_report_missing', 'USB-head report')
    else:
        report(head, HEAD_CURRENT_ROLE)
    c = a.get('plenum_coupon_identity')
    if c is None:
        fail('selected_report_missing', 'vent-study/shadow-plenum-coupon/coupon-index.json')
    else:
        if not (c['same_primary_manifest'] and c['source_current']):
            fail('stale_selected_report', c['path'], 'manifest %s, source %s' % (c['same_primary_manifest'], c['source_current']))
        binding('receipts', c['path'], c['receipt_bindings'])
        for r in c['receipts']:
            if not r['same_primary_manifest']:
                fail('stale_selected_report', r['path'], 'binds another manifest')
            binding('files', r['path'], r['files'])
    rc = a.get('restored_coupon_reproducer')
    if rc is not None:
        binding('restored files', rc['receipt']['path'], rc['restored_file_bindings'])
        binding('retained outputs', rc['receipt']['path'], rc['retained_output_bindings'])
    s = a.get('structural_pdf')
    if s is None:
        fail('selected_report_missing', 'structural-review/output/pdf/structural-supplement-pdf-receipt.json')
    else:
        if not s['same_primary_manifest']:
            fail('stale_selected_report', s['receipt']['path'], 'binds another manifest')
        if not s['pdf_hash_matches']:
            fail('binding', s['receipt']['path'], 'pdf')
        binding('sources', s['receipt']['path'], s['source_bindings'])
    cp = a['checkpoint_status']
    for k in ('same_primary_manifest', 'selected_evidence_binding', 'preserved_export18_binding', 'guide_receipt_current'):
        if not cp.get(k):
            fail('checkpoint_binding', 'CHECKPOINT-STATUS.json', k)
    if cp.get('guide_manifest_claim') and not cp.get('guide_nominated_manifest_current'):
        fail('checkpoint_claim', 'CHECKPOINT-STATUS.json',
             'guide.manifest_binding_current is true but the guide receipt nominates another manifest')
    for x in a.get('checkpoint_numbers', []):
        if not x['match']:
            fail('checkpoint_number', 'CHECKPOINT-STATUS.json', x['field'], json.dumps(x['recorded']), json.dumps(x['source_value']))
    for x in a.get('checkpoint_hashes', []):      # FX-D: every path/git_object + sha256 pair in CHECKPOINT-STATUS.json
        if not x['match']:
            fail('checkpoint_hash', 'CHECKPOINT-STATUS.json', x['field'], x['target'],
                 'recorded %s, actual %s' % (str(x['recorded'])[:12], str(x['actual'])[:12]))
    for x in a.get('document_numbers', []):
        fail(*x)
    g = a['guide_bound_cache']
    binding('sources', g.get('receipt'), g.get('sources'))   # fixup-1: guide receipt sources (inputs and documents)
    if not g.get('nominated_manifest_current'):
        fail('guide_manifest_stale', g.get('receipt'),
             'nominates %s, not the current manifest' % str(g.get('nominated_manifest_sha256'))[:8])
    cache(g['state'], 'guide', g['action'])
    return {'failures': F, 'rebuildable_caches': R, 'declared_pending': N, 'exit_code': 1 if F else (3 if R else 0)}
