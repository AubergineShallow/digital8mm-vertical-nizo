"""Bind completed scoped reports without rerunning or relabeling CAD results.

FP-04 (review 2026-10-10: VN-05, VN-08, VN-09, VN-31): every gate runs and every failure is listed. The selected
folder may hold only reports bound to the selected manifest (or reports
declared historical in evidence_rules.DECLARED_HISTORICAL with the manifest they must bind). The main audit's info
rows must be exactly the accepted set, the rigid failures exactly the one known witness, and the print-check
failures exactly the accepted (empty) set. Repeated figures are formatted from their source rows.

Modes: default = read-only (prints the verdict, writes nothing); --write rewrites
out/compact-kowa_lm6hc/current-review-evidence.json only if all evidence gates pass; --out PATH has the same rule.
--record-blocked records the current result even when gates fail, with every failure retained and exit 1. It never
grants design acceptance or physical release. The generated receipt is not its own input; independent folder audits
still validate it. --check is read-only and checks receipt freshness even when gates fail.
The output is deterministic (no wall-clock time). Exit 0 = evidence reconciled; 1 = a gate failed or receipt is stale.
"""
from cv_io import read_text, write_text
from contextlib import contextmanager
from pathlib import Path
import argparse, hashlib, json, sys

P = Path(__file__).resolve().parent
D = P / 'out/compact-kowa_lm6hc'
M = D / 'manifest.json'
TARGET = D / 'current-review-evidence.json'
CASES = [
 ('rigid', 'out/compact-kowa_lm6hc/verification.json', 'verify_candidate.py', 'verification_source_sha256', 'manifest_sha256'),
 ('mesh', 'out/compact-kowa_lm6hc/print-mesh-checks.json', 'verify_print_meshes.py', 'verification_source_sha256', 'manifest_sha256'),
 ('print', 'out/compact-kowa_lm6hc/print-checks.json', 'verify_print_checks.py', 'verification_source_sha256', 'manifest_sha256'),
 ('csi', 'out/compact-kowa_lm6hc/csi-source-tool-checks.json', 'verify_csi_source.py', 'verification_source_sha256', 'mechanical_manifest_sha256'),
 ('power_rigid', 'out/compact-kowa_lm6hc/power-service-checks.json', 'verify_power_service.py', 'source_sha256', 'manifest_sha256'),
 ('power_static', 'out/compact-kowa_lm6hc/wire-solid-checks.json', 'verify_wire_solids.py', 'verification_source_sha256', 'manifest_sha256'),
 ('hdmi', 'out/compact-kowa_lm6hc/hdmi-solid-checks.json', 'verify_hdmi.py', 'verification_source_sha256', 'mechanical_manifest_sha256'),
 ('fps', 'out/fps-service-study/integrated-fps-checks.json', 'verify_fps_integrated.py', 'source_sha256', 'mechanical_manifest_sha256'),
 ('usb_head', 'routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json', 'verify_shadow_usb_head.py', 'verification_source_sha256', 'mechanical.manifest_sha256'),
 ('plenum', 'out/compact-kowa_lm6hc/shadow-plenum-checks.json', 'verify_shadow_plenum.py', 'verification_source_sha256', 'manifest_sha256'),
 ('exterior_mouths', 'out/compact-kowa_lm6hc/shadow-outlet-context-checks.json', 'verify_shadow_outlet_context.py', 'verification_source_sha256', 'manifest_sha256'),
 ('microSD_rejected_closed_path', 'out/compact-kowa_lm6hc/microsd-service-dependency.json', 'verify_microsd_service.py', 'verification_source_sha256', 'manifest_sha256'),
 ('check_scope', 'out/compact-kowa_lm6hc/check-scope-checks.json', 'verify_check_scope.py', 'verification_source_sha256', 'manifest_sha256'),  # FP-12
 ('harness', 'out/compact-kowa_lm6hc/harness-checks.json', 'verify_harness_checks.py', 'verification_source_sha256', 'manifest_sha256'),  # FP-10
 ('void', 'out/comparison/volume-compact-kowa_lm6hc.json', 'measure_volume.py', 'verification_source_sha256', 'manifest_sha256')]
# Sampled geometry and helper inputs, not only each top-level verifier.
INPUT_BINDINGS = [
 ('out/compact-kowa_lm6hc/hdmi-solid-checks.json', 'snapshot_sha256', 'routing-snapshots/hdmi-export17-selected-20261009-0704/input.json'),
 ('out/compact-kowa_lm6hc/power-service-checks.json', 'snapshot_sha256', 'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'),
 ('out/compact-kowa_lm6hc/wire-solid-checks.json', 'snapshot_sha256', 'routing-snapshots/power-csi-clear-20261009-0358/power-270-csi-clear.json'),
 ('out/fps-service-study/integrated-fps-checks.json', 'input_sha256', 'out/fps-service-study/mated-carry-input.json')]
STATUS_GATES = [  # (report, json path, required value)
 ('out/compact-kowa_lm6hc/power-service-checks.json', 'status', 'pass'),
 ('out/compact-kowa_lm6hc/wire-solid-checks.json', 'status', 'pass'),
 ('out/compact-kowa_lm6hc/print-mesh-checks.json', 'fail_count', 0),
 ('out/compact-kowa_lm6hc/hdmi-solid-checks.json', 'summary.fail', 0),
 ('out/fps-service-study/integrated-fps-checks.json', 'status', 'geometric_pass_only'),
 ('routing-snapshots/hdmi-export17-selected-20261009-0704/shadow-plenum-head-checks.json', 'status', 'pass_for_bounded_head_reservation'),
 ('out/compact-kowa_lm6hc/shadow-plenum-checks.json', 'summary.fail', 0),
 ('out/compact-kowa_lm6hc/shadow-outlet-context-checks.json', 'summary.fail', 0),
 ('out/compact-kowa_lm6hc/check-scope-checks.json', 'summary.fail', 0),
 ('out/compact-kowa_lm6hc/csi-source-tool-checks.json', 'declared_rigid_reservation_clear', True)]
# FP-13 (review VN-27): every other variant carries its own full main audit and print checks, bound to its own
# manifest and the current verifier, with the same failure rules as the selected variant (rigid: only the shared
# pi5/cooler witness; print: exactly the accepted, empty, set). A missing report is a failure, never a skip.
VARIANT_AUDITS = ('compact-fujinon_hf6xa', 'original-kowa_lm6hc')
VARIANT_REPORTS = (('verification.json', 'verify_candidate.py'), ('print-checks.json', 'verify_print_checks.py'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(read_text(p))


def dig(d, path):
    for k in path.split('.'):
        d = d[k]
    return d


def reconcile(root=P):
    """(failures, result). A blocked result is current review evidence, never a passed gate or physical release."""
    import evidence_rules as ER
    import export_cache as EC  # FP-03: bound files are tracked or git-ignored regenerable caches; no binding is dropped
    root = Path(root)
    D, M = root / 'out/compact-kowa_lm6hc', root / 'out/compact-kowa_lm6hc/manifest.json'
    F, binding_failures, source_export_failures = [], [], []

    @contextmanager
    def gate(name, *, identity=False, source_export=False):
        try:
            yield
        except (AssertionError, KeyError, FileNotFoundError, ValueError, TypeError) as e:
            args = e.args[0] if len(e.args) == 1 and isinstance(e.args[0], tuple) else e.args
            finding = [name] + [str(a) for a in args]
            F.append(finding)
            if identity:
                binding_failures.append(finding)
            if source_export:
                source_export_failures.append(finding)

    m = read(M)
    mh = sha(M)
    receipt_rel = 'out/compact-kowa_lm6hc/current-review-evidence.json'
    folder_findings = [list(x) for x in ER.selected_folder_findings(D, mh, root, generated_outputs=(receipt_rel,))]
    F += folder_findings
    binding_failures += folder_findings
    for rel, h in sorted(m['sources'].items()):
        p = root.parent / rel
        if not p.is_file() or sha(p) != h:
            finding = ['source_binding', 'Source missing' if not p.is_file() else 'Source mismatch', rel]
            F.append(finding)
            binding_failures.append(finding)
            source_export_failures.append(finding)
    with gate('export_files', identity=True, source_export=True):
        EC.require_files(m['files'], D)  # AssertionError('Export mismatch', rel) or ('Bound cache missing', n, how to rebuild)
    rows = []
    for label, path, verifier, source_key, manifest_key in CASES:
        with gate('report:' + label, identity=True):
            f = root / path
            j = read(f)
            rows.append(dict(check=label, report=path, report_sha256=sha(f), verification_source=verifier,
                             verification_source_sha256=j.get(source_key),
                             manifest_sha256=ER.bound_manifest(j),
                             manifest_binding_current=ER.bound_manifest(j) == mh,
                             verifier_hash_current=j.get(source_key) == sha(root / verifier),
                             status=j.get('status', j.get('closed_panel_case', j.get('operational_status'))),
                             summary=j.get('summary'), failing=j.get('failing'),
                             failed_checks=[q for q in j.get('checks', []) if q.get('status') == 'fail'],
                             physical_qualified=False))
            assert dig(j, manifest_key) == mh, ('Different mechanical snapshot', path, str(dig(j, manifest_key))[:8])
            assert j[source_key] == sha(root / verifier), ('Different verifier', path, verifier)
    for report, key, path in INPUT_BINDINGS:
        with gate('input', identity=True):
            assert read(root / report)[key] == sha(root / path), ('Input mismatch', path)
    for name, report in (('head_dependency', CASES[8][1]), ('fps_dependency', 'out/fps-service-study/integrated-fps-checks.json'), ('harness_dependency', 'out/compact-kowa_lm6hc/harness-checks.json')):
        with gate(name, identity=True):
            for rel, h in sorted(read(root / report)['verification_dependency_sha256'].items()):
                assert sha(root / rel) == h, ('Dependency mismatch', report, rel)
    with gate('check_scope_dependency', identity=True):  # fixup-1 (FP-12): helper and input shas of the run reports, as dependencies above
        bad = [(rep, f, rel) for rep in ('out/compact-kowa_lm6hc/check-scope-checks.json', 'out/compact-kowa_lm6hc/wire-solid-checks.json', 'out/compact-kowa_lm6hc/microsd-service-dependency.json') if (root / rep).is_file() for f, rel in ER.dependency_mismatches(read(root / rep), root)]
        assert not bad, ('Dependency mismatch', bad[:5])
    rigid, fails = None, []
    with gate('rigid'):
        rigid = read(D / 'verification.json')
        fails = [q for q in rigid['checks'] if q['status'] == 'fail']
        assert len(fails) == 1 and fails[0]['id'] == 'pi5/cooler', (
            'New active rigid fault', sorted(q['category'] + '/' + q['id'] for q in fails))
    accepted_info = sorted(ER.expected_main_info())
    if rigid is not None:
        F += [list(x) for x in ER.info_set_findings(rigid)]  # VN-31: the exact info-row set
    with gate('print'):
        F += [list(x) for x in ER.print_failure_findings(read(D / 'print-checks.json'))]
    with gate('harness'):  # FP-10: harness failures are findings unless accepted in ER.EXPECTED_HARNESS_FAILURES (kept empty)
        F += [list(x) for x in ER.harness_failure_findings(read(D / 'harness-checks.json'))]
    variant_rows = []
    for v in VARIANT_AUDITS:  # FP-13 (VN-27)
        vd = root / 'out' / v
        vmh = None
        with gate('variant_audit:' + v, identity=True):
            vmh = sha(vd / 'manifest.json')
        for name, verifier in VARIANT_REPORTS:
            with gate('variant_audit:' + v, identity=True):
                rel = 'out/%s/%s' % (v, name)
                j = read(vd / name)
                variant_rows.append(dict(variant=v, report=rel, report_sha256=sha(vd / name), verification_source=verifier,
                                         manifest_sha256=j.get('manifest_sha256'),
                                         manifest_binding_current=vmh is not None and j.get('manifest_sha256') == vmh,
                                         verifier_hash_current=j.get('verification_source_sha256') == sha(root / verifier),
                                         summary=j.get('summary'), failing=j.get('failing'),
                                         failed_checks=[q for q in j.get('checks', []) if q.get('status') == 'fail'],
                                         physical_qualified=False))
                assert vmh is not None and j.get('manifest_sha256') == vmh, ('Different mechanical snapshot', rel, str(j.get('manifest_sha256'))[:8])
                assert j.get('verification_source_sha256') == sha(root / verifier), ('Different verifier', rel, verifier)
        with gate('variant_audit:' + v):
            vfails = sorted(q['category'] + '/' + q['id'] for q in read(vd / 'verification.json')['checks'] if q['status'] == 'fail')
            assert vfails == ['interference/pi5/cooler'], ('New active rigid fault', v, vfails)
        with gate('variant_audit:' + v):
            F += [[x[0], v] + list(x[1:]) for x in ER.print_failure_findings(read(vd / 'print-checks.json'))]
    for report, path, want in STATUS_GATES:
        with gate('status'):
            got = dig(read(root / report), path)
            assert got == want, ('Status', report, path, json.dumps(got), json.dumps(want))
            if report == 'out/compact-kowa_lm6hc/check-scope-checks.json':
                scope_fails = [q for q in read(root / report)['checks'] if q.get('status') == 'fail']
                assert not scope_fails, ('Failed check-scope rows', report, [q['id'] for q in scope_fails])
    gates, witness = None, None
    with gate('numbers'):
        gates = ER.inherited_gates(root)
        witness = ER.cooler_witness_mm3(rigid or {})
        assert witness is not None, ('No main-audit row interference pi5/cooler to quote',)
    holds = ['Saved-STEP print and plenum checks are scoped geometric evidence only. Slicer paths, plenum coupons and full-body cleanout remain unqualified.',
             'Cooler/source overlap %s mm3 (main audit row interference pi5/cooler) remains unresolved; measured cooler registration and real thermal tests are required.' % (
                 'unknown' if witness is None else ER.fmt_mm3(witness)),
             'Exterior bay connectivity is not a sealed main-cavity cooler duct or a fan-flow/cooling result. Hand/strap/stand blockage requires separate tests.',
             'Complete camera FPC, USB-feed wire roots/stow and combined flexible service remain unresolved.']
    result = dict(mechanical_manifest_sha256=mh, reconciler_sha256=sha(Path(__file__)),
                  rules_sha256=sha(Path(ER.__file__)), generated_utc=ER.UNRECORDED,
                  source_and_export_hashes_verified=not source_export_failures,
                  source_and_export_binding_scope='Selected manifest sources and all selected manifest export files only.',
                  source_and_export_failures=source_export_failures,
                  evidence_bindings_verified=not binding_failures, evidence_binding_failures=binding_failures,
                  reconciliation_status='blocked' if F else 'reconciled_with_open_physical_holds',
                  evidence_gates_pass=not F, gate_failure_count=len(F), gate_failures=list(F), release_status='blocked',
                  reports=rows, variant_audits=variant_rows, active_rigid_failures=fails,
                  accepted_info_rows=[list(x) for x in accepted_info],
                  accepted_print_failures=ER.EXPECTED_PRINT_FAILURES,
                  declared_historical_in_selected_folder=sorted(k for k in ER.DECLARED_HISTORICAL if k.startswith('out/compact-kowa_lm6hc/')),
                  verdict='Review candidate only. Not fabrication, energization or complete-service release.',
                  physical_qualified=False, open_inherited_gates=None if gates is None else gates['open'],
                  inherited_gate_source=gates, M1='open', prominent_holds=holds,
                  historical_attempt='history/shadow-first-check-run/review-check-run.json preserves the initial USB-head dependency failure. The separately executed current whole-assembly checker replaces missing standalone support extracts with mandatory integrated-tub coverage and canonical helper hashes; it does not invent a USB service path.')
    return F, result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--write', action='store_true', help='rewrite out/compact-kowa_lm6hc/current-review-evidence.json')
    g.add_argument('--out', type=Path, help='write the evidence record here instead')
    g.add_argument('--record-blocked', action='store_true', help='record the current receipt even when gates fail; retain failures and exit 1')
    g.add_argument('--check', action='store_true', help='read-only; also fail if the committed record is stale')
    args = ap.parse_args(argv)
    F, result = reconcile(P)
    text = json.dumps(result, indent=2) + '\n'
    if args.check and (not TARGET.is_file() or read_text(TARGET) != text):
        F.append(['committed_evidence_stale', TARGET.relative_to(P).as_posix(), 'differs from a fresh reconciliation; review, then use --record-blocked or, when gates pass, --write'])
    print(json.dumps(dict(manifest=result['mechanical_manifest_sha256'], reports=len(result['reports']),
                          active_rigid_failures=len(result['active_rigid_failures']), failure_count=len(F),
                          failures=F, physical_qualified=False), indent=2))
    if args.record_blocked or (not F and (args.write or args.out)):
        path = args.out.resolve() if args.out else TARGET
        write_text(path, text)
        print(path)
    if F:
        print('RECONCILE FAIL: %d gate failure(s); %s' % (len(F), 'blocked review receipt recorded; failures retained' if args.record_blocked else 'nothing written'), file=sys.stderr)
    return 1 if F else 0


if __name__ == '__main__':
    raise SystemExit(main())
