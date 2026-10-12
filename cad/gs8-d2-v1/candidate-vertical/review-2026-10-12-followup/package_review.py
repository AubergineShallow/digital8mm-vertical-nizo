"""Package a committed review checkpoint without running CAD or changing evidence.

Run only after the final local commit, from any directory::

  python package_review.py --expect-commit <full HEAD> --output /outside/repo/delivery

Add --with-guide to copy the current followup PDF and distribute its verified
source/pages ZIP member set across ordinary size-limited ZIPs. The full guide
ZIP is a separate Library artifact, not duplicated in this small delivery set.
Without --with-guide, guide binaries are not delivered.
--check-only performs the same source/evidence preflight without packaging.
No push, checkout, commit, CAD generation, or report rewrite is performed.
"""

from collections import Counter
from datetime import datetime, timezone
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile

BRANCH = 'review/vn-catch-qt-cloud-20261012'
BASELINE = 'f9704ac03de8938dfafdb52e22e63d098287c3c6'
CANDIDATE = 'cad/gs8-d2-v1/candidate-vertical'
VARIANTS = ('compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc')
RENDER_VIEWS = ('hero', 'rear', 'vent_side', 'vent_front')
PREFIX = 'D2-Oct12-catch-QT-followup'
GUIDE_ID = 'D2-vertical-catch-QT-followup-f9704ac'
LIMIT = 14_000_000  # Decimal bytes, strictly less than 14 MB.
TEXT_SUFFIXES = {'.py', '.md', '.txt', '.json', '.csv', '.tsv', '.toml', '.yaml',
                 '.yml', '.ini', '.cfg', '.sh', '.lock', '.log', '.cpp', '.c', '.h'}
FORBIDDEN_PARTS = {'.git', '.ssh', '.aws', '.gnupg', '.venv', 'venv', '__pycache__',
                   '.cache', '.pytest_cache', 'node_modules'}
PRIVATE_KEY = re.compile(rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')


class PackageError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise PackageError(message)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args, data=None):
    result = subprocess.run(['git', '-C', str(repo), *args], input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise PackageError('Git command failed: ' + ' '.join(args[:3]) + '\n' +
                           result.stderr.decode('utf-8', 'replace'))
    return result.stdout


def safe_name(name):
    path = PurePosixPath(name)
    require(bool(name) and not path.is_absolute() and '..' not in path.parts and
            '\\' not in name and not any(ord(c) < 32 for c in name), 'Unsafe member path: ' + repr(name))
    lower = tuple(p.lower() for p in path.parts)
    require(not any(p in FORBIDDEN_PARTS or p.startswith('.venv') for p in lower),
            'Excluded credentials/cache/internal path: ' + name)
    require(not any(p == '.env' or p.startswith('.env.') for p in lower) and
            path.suffix.lower() not in {'.pem', '.p12', '.pfx', '.key'} and
            path.name.lower() not in {'credentials', 'credentials.json', 'secrets.json',
                                       'id_rsa', 'id_ed25519', '.netrc', '.npmrc'},
            'Potential credential file: ' + name)
    return path.as_posix()


def load_helper(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Snapshot:
    """Hash every tracked byte, independently of Git's stat-cache shortcuts."""

    def __init__(self, repo, expected_commit, branch=BRANCH, baseline=BASELINE):
        self.repo = Path(repo).resolve()
        self.branch, self.baseline = branch, baseline
        self.commit = git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        self.tree = git(self.repo, 'rev-parse', 'HEAD^{tree}').decode().strip()
        require(expected_commit == self.commit, 'HEAD is not the explicitly nominated full commit')
        self.check_identity()
        require(git(self.repo, 'rev-parse', '--is-shallow-repository').strip() == b'false',
                'A shallow checkout cannot supply a full-history bundle')
        self.object_format = git(self.repo, 'rev-parse', '--show-object-format').decode().strip()
        self.entries = {}
        self.hashes = {}
        self.extra_hashes = {}
        for record in git(self.repo, 'ls-tree', '-rz', self.commit).split(b'\0'):
            if not record:
                continue
            header, raw_name = record.split(b'\t', 1)
            mode, kind, oid = header.decode().split()
            name = safe_name(raw_name.decode('utf-8'))
            require(kind == 'blob' and mode in {'100644', '100755'},
                    'Symlinks/submodules are not supported in delivery: ' + name)
            self.entries[name] = (mode, oid)
            data = self._read(name)
            actual_oid = hashlib.new(self.object_format, b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            require(actual_oid == oid, 'Working bytes differ from the committed blob: ' + name)
            require(not PRIVATE_KEY.search(data), 'Potential private key content in tracked file: ' + name)
            self.hashes[name] = sha(data)
        require(bool(self.entries), 'Empty tracked checkpoint')

    def check_identity(self):
        require(git(self.repo, 'symbolic-ref', '--short', 'HEAD').decode().strip() == self.branch,
                'Wrong branch for this followup delivery')
        require(git(self.repo, 'rev-parse', 'HEAD').decode().strip() == self.commit and
                git(self.repo, 'rev-parse', 'HEAD^{tree}').decode().strip() == self.tree,
                'Commit/tree changed during packaging')
        git(self.repo, 'merge-base', '--is-ancestor', self.baseline, self.commit)
        require(not git(self.repo, 'status', '--porcelain=v1', '--untracked-files=all'),
                'Packaging requires a clean committed checkout, including no untracked files')

    def relative(self, path):
        path = Path(path)
        require(not path.is_symlink(), 'Symlink source is not allowed: ' + str(path))
        resolved = path.resolve()
        require(resolved.is_relative_to(self.repo), 'Bound input escapes repository: ' + str(path))
        return safe_name(resolved.relative_to(self.repo).as_posix())

    def _read(self, name):
        path = self.repo / name
        require(path.resolve().is_relative_to(self.repo) and not path.is_symlink() and path.is_file(),
                'Missing or unsafe source: ' + name)
        return path.read_bytes()

    def read(self, path, tracked=True):
        name = self.relative(path)
        require(not tracked or name in self.entries, 'Delivery source is not committed: ' + name)
        data = self._read(name)
        digest = sha(data)
        previous = self.hashes.get(name, self.extra_hashes.get(name))
        require(previous is None or digest == previous, 'Input changed during packaging: ' + name)
        if name not in self.hashes:
            self.extra_hashes[name] = digest
        return data

    def bind(self, path, digest, tracked=False):
        require(isinstance(digest, str) and bool(re.fullmatch(r'[0-9a-f]{64}', digest)),
                'Missing/invalid source digest: ' + str(path))
        require(sha(self.read(path, tracked=tracked)) == digest, 'Stale binding: ' + self.relative(path))

    def load(self, path, tracked=True):
        return json.loads(self.read(path, tracked=tracked))

    def finish(self):
        self.check_identity()
        for name, digest in {**self.hashes, **self.extra_hashes}.items():
            require(sha(self._read(name)) == digest, 'Source changed during packaging: ' + name)
        self.check_identity()


def check_summary(report):
    rows = report.get('checks')
    if isinstance(rows, list) and isinstance(report.get('summary'), dict) and 'pass' in report['summary']:
        counts = Counter(row.get('status') for row in rows)
        require(report['summary'] == {key: counts[key] for key in report['summary']},
                'Report summary differs from its check rows')


def report_view(path, value, snapshot):
    check_summary(value)
    failed = []

    def walk(node, location=''):
        if isinstance(node, dict):
            if node.get('status') == 'fail':
                # Preserve full failed rows in machine-readable status; the
                # README uses identifiers and original reports carry context.
                failed.append({'location': location, 'row': node})
                return
            for key, child in node.items():
                walk(child, location + '/' + str(key))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, location + '/' + str(index))

    # Do not let a top-level fail status hide individual failure rows.
    for key in ('checks', 'rows', 'failed_checks'):
        if key in value:
            walk(value[key], key)
    return {'path': snapshot.relative(path), 'sha256': sha(snapshot.read(path)),
            'status': value.get('status'), 'summary': value.get('summary'),
            'pass_count': value.get('pass_count'), 'fail_count': value.get('fail_count'),
            'failing': value.get('failing'), 'failed_rows': failed,
            'physical_qualified': False}


def verify_dependencies(snapshot, candidate, value):
    maps = (('verification_dependency_sha256', candidate), ('helper_source_sha256', candidate),
            ('input_sha256', candidate.parent), ('check_sources', candidate.parent),
            ('checked_source_sha256', candidate))
    for field, base in maps:
        items = value.get(field, {})
        if isinstance(items, str) and field == 'helper_source_sha256':
            items = {'power_geometry.py': items}
        elif isinstance(items, str) and field == 'input_sha256':
            require(value.get('source_sha256') == sha(snapshot.read(candidate / 'verify_fps_integrated.py')),
                    'Unsupported scalar input binding outside the current integrated FPS report')
            base = candidate
            items = {'out/fps-service-study/mated-carry-input.json': items}
        require(isinstance(items, dict), 'Unsupported dependency map: ' + field)
        for name, digest in items.items():
            snapshot.bind(base / name, digest)
    for field, name in (('state_model_sha256', 'steps.py'),
                        ('terminal_rule_source_sha256', 'wire_terminal_rules.py')):
        if field in value:
            snapshot.bind(candidate / name, value[field])


def execution_time(value, field):
    require(isinstance(value, str), 'Missing execution timestamp: ' + field)
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise PackageError('Invalid execution timestamp: ' + field) from error
    require(result.tzinfo is not None and result.utcoffset() is not None,
            'Execution timestamp must include a timezone: ' + field)
    return result


def inspect_harness_refresh(snapshot, candidate, harness, batch):
    """Keep the strengthened harness execution distinct from the primary batch."""
    followup = candidate / 'review-2026-10-12-followup'
    path = followup / 'harness-refresh.json'
    receipt = snapshot.load(path)
    report_path = candidate / 'out' / VARIANTS[0] / 'harness-checks.json'
    manifest_path = report_path.with_name('manifest.json')
    manifest = snapshot.load(manifest_path)
    check_summary(harness)
    require(receipt.get('manifest_sha256') == harness['manifest_sha256'] == sha(snapshot.read(manifest_path)),
            'Harness refresh binds a stale manifest')
    snapshot.bind(report_path, receipt.get('report_sha256'), tracked=True)
    snapshot.bind(followup / 'refresh_harness.py', receipt.get('source_sha256'), tracked=True)
    require(receipt.get('summary') == harness['summary'] and
            type(receipt.get('exit_code')) is int and
            receipt['exit_code'] == int(harness['summary']['fail'] > 0),
            'Harness refresh counts/exit differ from the current report')
    require(receipt.get('command') == ['verify_harness_checks.py'] and
            receipt.get('physical_qualified') is False,
            'Harness refresh lost its execution scope or physical hold')
    started = execution_time(receipt.get('started_utc'), 'harness refresh started_utc')
    completed = execution_time(receipt.get('completed_utc'), 'harness refresh completed_utc')
    require(started <= completed, 'Harness refresh ends before it starts')
    require(bool(batch.get('checks')), 'Original primary execution record is missing')
    last_primary = max(execution_time(row.get('completed_utc'), 'primary ' + row['check'])
                       for row in batch['checks'])
    require(started >= last_primary, 'Separate harness refresh predates the completed primary batch')
    inputs = receipt.get('input_sha256')
    require(isinstance(inputs, dict) and bool(inputs), 'Harness refresh input snapshot is empty')
    captured = {}
    for name, digest in inputs.items():
        input_path = candidate / name
        snapshot.bind(input_path, digest)
        key = snapshot.relative(input_path)
        require(key not in captured or captured[key] == digest, 'Conflicting harness input aliases')
        captured[key] = digest
    verifier_path = candidate / 'verify_harness_checks.py'
    required = {manifest_path: receipt['manifest_sha256'],
                verifier_path: harness['verification_source_sha256'],
                followup / 'refresh_harness.py': receipt['source_sha256']}
    dependencies = harness.get('verification_dependency_sha256')
    require(isinstance(dependencies, dict) and bool(dependencies), 'Current harness dependency map is empty')
    assignments = [node for node in ast.parse(snapshot.read(verifier_path).decode()).body
                   if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'DEPENDENCIES'
                                                          for target in node.targets)]
    require(len(assignments) == 1, 'Harness dependency declaration is not unique')
    declared = ast.literal_eval(assignments[0].value)
    require(isinstance(declared, list) and declared and all(isinstance(name, str) for name in declared) and
            len(declared) == len(set(declared)) and declared == receipt.get('declared_dependencies') and
            set(declared) == set(dependencies), 'Harness refresh dependency set differs from the current verifier')
    required.update({candidate / name: digest for name, digest in dependencies.items()})
    required.update({candidate.parent / name: digest for name, digest in manifest['sources'].items()})
    required.update({manifest_path.parent / name: digest for name, digest in manifest['files'].items()})
    for input_path, digest in required.items():
        require(captured.get(snapshot.relative(input_path)) == digest,
                'Harness refresh did not capture the current input: ' + snapshot.relative(input_path))
        snapshot.bind(input_path, digest)
    archive_name = 'review-2026-10-12-followup/prior-harness-before-full-minimum.json'
    require(receipt.get('prior_report_archive') == archive_name,
            'Unexpected prior harness archive path')
    archive_path = candidate / archive_name
    snapshot.bind(archive_path, receipt.get('prior_report_sha256'), tracked=True)
    prior = snapshot.load(archive_path)
    check_summary(prior)
    require(prior.get('variant') == VARIANTS[0] and prior.get('manifest_sha256') == receipt['manifest_sha256'],
            'Prior harness archive belongs to another variant/manifest')
    primary_harness = [row for row in batch['checks'] if row['check'] == 'harness']
    require(len(primary_harness) == 1 and
            primary_harness[0]['exit_code'] == int(prior['summary']['fail'] > 0),
            'Archived prior harness exit does not match the primary execution record')
    require(receipt.get('log') == 'review-2026-10-12-followup/harness-refresh.log',
            'Unexpected harness refresh log path')
    snapshot.bind(candidate / receipt['log'], receipt.get('log_sha256'), tracked=True)
    return {'receipt': snapshot.relative(path), 'receipt_sha256': sha(snapshot.read(path)),
            'started_utc': receipt['started_utc'], 'completed_utc': receipt['completed_utc'],
            'command': receipt['command'], 'exit_code': receipt['exit_code'],
            'manifest_sha256': receipt['manifest_sha256'], 'report_sha256': receipt['report_sha256'],
            'source_sha256': receipt['source_sha256'], 'declared_dependencies': declared,
            'summary': receipt['summary'], 'input_sha256': receipt['input_sha256'],
            'prior_report_archive': snapshot.relative(archive_path),
            'prior_report_sha256': receipt['prior_report_sha256'], 'prior_summary': prior['summary'],
            'log': snapshot.relative(candidate / receipt['log']), 'log_sha256': receipt['log_sha256'],
            'scope': 'Separate full strengthened harness rerun after the original primary batch. '
                     'The preserved primary batch does not claim execution of the current harness code.',
            'physical_qualified': False}


def validate_inherited_gate_states(current, baseline):
    """Preserve the pinned gate inventory, including its two deleted features."""
    require(isinstance(current, dict) and isinstance(baseline, dict) and bool(baseline) and
            all(isinstance(value, str) for value in baseline.values()),
            'Inherited physical gate inventory is invalid')
    require(current == baseline, 'Inherited physical gate identities/states changed from the baseline')
    withdrawn = sorted(name for name, value in baseline.items() if value.startswith('withdrawn'))
    require(withdrawn == ['G-SKIRT-1', 'G-SNAP-1'],
            'Unexpected withdrawn physical gates; no new waiver is authorized')
    require(all(value.startswith(('open', 'withdrawn')) for value in baseline.values()),
            'Unexpected closed/passed inherited physical gate state')
    return {'total': len(current), 'open': sum(value.startswith('open') for value in current.values()),
            'withdrawn': len(withdrawn), 'withdrawn_ids': withdrawn}


def inspect_physical_gates(snapshot, candidate):
    path = candidate.parent / 'out/build-receipt.json'
    relative = snapshot.relative(path)
    current = snapshot.load(path)['hardware_gates']['gates']
    baseline_object = snapshot.baseline + ':' + relative
    baseline_bytes = git(snapshot.repo, 'show', baseline_object)
    baseline = json.loads(baseline_bytes)['hardware_gates']['gates']
    counts = validate_inherited_gate_states(current, baseline)
    rules_path = candidate / 'evidence_rules.py'
    snapshot.read(rules_path)
    rules = load_helper(rules_path, '_delivery_physical_gate_rules').inherited_gates(candidate)
    require(all(rules[key] == counts[key] for key in ('total', 'open', 'withdrawn')) and
            rules['source_sha256'] == sha(snapshot.read(path)),
            'Physical gate counts differ from the source-bound inherited_gates rule')
    return {'inherited_total': counts['total'], 'inherited_open': counts['open'],
            'inherited_withdrawn': counts['withdrawn'], 'withdrawn_ids': counts['withdrawn_ids'],
            'M1': 'open', 'source': relative, 'source_sha256': rules['source_sha256'],
            'baseline_git_object': baseline_object, 'baseline_source_sha256': sha(baseline_bytes),
            'scope': 'Exact inherited gate identities/states retained from the pinned baseline; no new waiver.'}


def inspect_evidence(snapshot):
    candidate = snapshot.repo / CANDIDATE
    sys.path[:0] = [str(candidate), str(candidate / 'guide')]
    helper_path = candidate / 'guide/followup_guide_support.py'
    snapshot.read(helper_path)
    followup = load_helper(helper_path, '_delivery_followup').inspect_variants(candidate)
    for path in followup['files']:
        snapshot.read(path, tracked=False)
    status = {'scope': 'Computed review evidence only', 'physical_qualified': False, 'variants': {}}
    for variant, inspected in followup['variants'].items():
        export = candidate / 'out' / variant
        manifest = inspected['manifest']
        # Includes assembled CAD as well as all part/mesh source snapshots.
        for name, digest in manifest['files'].items():
            snapshot.bind(export / name, digest)
        prints = manifest['production_prints']
        require(len(prints['files']) == prints['piece_count'] and
                len(set(prints['files'])) == prints['piece_count'], 'Invalid production print count: ' + variant)
        require(sum(row['kind'] == 'printed' for row in manifest['rows']) == prints['assembly_row_count'],
                'Production assembly-row count differs: ' + variant)
        for name in prints['files']:
            require(name.startswith('stl/') and name.endswith('.stl') and name in manifest['files'],
                    'Production STL is absent from manifest: ' + name)
        reports = {}
        for label, item in inspected['reports'].items():
            reports[label] = report_view(item['path'], item['report'], snapshot)
        for label, filename, source in (('scope', 'check-scope-checks.json', 'verify_check_scope.py'),
                                        ('plenum', 'shadow-plenum-checks.json', 'verify_shadow_plenum.py')):
            path = export / filename
            value = snapshot.load(path)
            require(value.get('manifest_sha256') == inspected['manifest_sha256'], 'Stale report: ' + str(path))
            snapshot.bind(candidate / source, value.get('verification_source_sha256'))
            verify_dependencies(snapshot, candidate, value)
            reports[label] = report_view(path, value, snapshot)
        status['variants'][variant] = {
            'manifest_path': snapshot.relative(inspected['manifest_path']),
            'manifest_sha256': inspected['manifest_sha256'], 'state': manifest['state'],
            'production_prints': prints, 'core_dimensions_mm': manifest['core_dimensions_mm'],
            'reports': reports, 'catch': inspected['catch_summary'],
            'catch_report': snapshot.relative(inspected['catch_path']),
            'harness_scope': inspected['harness_scope']}
    primary = candidate / 'out' / VARIANTS[0]
    harness = snapshot.load(primary / 'harness-checks.json')
    require(harness['variant'] == VARIANTS[0] and harness['physical_qualified'] is False,
            'Harness scope/physical hold changed')
    require(harness['manifest_sha256'] == status['variants'][VARIANTS[0]]['manifest_sha256'], 'Stale harness manifest')
    snapshot.bind(candidate / 'verify_harness_checks.py', harness['verification_source_sha256'])
    verify_dependencies(snapshot, candidate, harness)
    status['harness'] = report_view(primary / 'harness-checks.json', harness, snapshot)
    status['qt_rows'] = [row for row in harness['checks'] if 'qt' in row.get('id', '').lower()]
    require(bool(status['qt_rows']), 'QT evidence is absent')
    receipt_path = primary / 'review-check-run.json'
    receipt = snapshot.load(receipt_path)
    aggregator = load_helper(candidate / 'review-2026-10-12-followup/aggregate_status.py', '_delivery_aggregate')
    runner = candidate / 'run_shadow_checks.py'
    require(receipt['runner_sha256'] == sha(snapshot.read(runner)) and
            receipt['manifest_sha256'] == status['variants'][VARIANTS[0]]['manifest_sha256'],
            'Primary child-check run binds stale inputs')
    require(Counter(row['check'] for row in receipt['checks']) ==
            Counter(aggregator.expected_child_names(snapshot.read(runner).decode())), 'Incomplete primary child-check set')
    for row in receipt['checks']:
        snapshot.read(primary / row['log'])
    status['primary_child_checks'] = receipt['checks']
    status['harness_refresh'] = inspect_harness_refresh(snapshot, candidate, harness, receipt)
    aggregate_path = candidate / 'review-2026-10-12-followup/validation-primary-summary.json'
    aggregate = snapshot.load(aggregate_path)
    for name, digest in aggregate['inputs'].items():
        snapshot.bind(candidate / name, digest, tracked=True)
    status['primary_aggregate'] = aggregate
    reconciled_path = primary / 'current-review-evidence.json'
    reconciled = snapshot.load(reconciled_path)
    require(reconciled.get('mechanical_manifest_sha256') == status['variants'][VARIANTS[0]]['manifest_sha256'] and
            reconciled.get('source_and_export_hashes_verified') is True and
            reconciled.get('evidence_bindings_verified') is True and
            not reconciled.get('source_and_export_failures') and not reconciled.get('evidence_binding_failures'),
            'Current review reconciliation has stale source/report bindings')
    snapshot.bind(candidate / 'reconcile_review_evidence.py', reconciled['reconciler_sha256'])
    snapshot.bind(candidate / 'evidence_rules.py', reconciled['rules_sha256'])
    for row in reconciled['reports']:
        snapshot.bind(candidate / row['report'], row['report_sha256'])
        snapshot.bind(candidate / row['verification_source'], row['verification_source_sha256'])
        verify_dependencies(snapshot, candidate, snapshot.load(candidate / row['report']))
    status['reconciliation'] = {key: reconciled.get(key) for key in
                                ('reconciliation_status', 'release_status', 'gate_failure_count', 'gate_failures')}
    status['physical_gates'] = inspect_physical_gates(snapshot, candidate)
    return status


def inspect_guide(snapshot, status):
    candidate = snapshot.repo / CANDIDATE
    output = candidate / 'guide/out-concealed-vents'
    receipt_path = output / 'guide-receipt.json'
    receipt = snapshot.load(receipt_path)
    require(receipt.get('guide_identity') == GUIDE_ID and receipt.get('guide_pdf_filename') == GUIDE_ID + '.pdf',
            'Current followup guide identity is required; an earlier guide cannot substitute')
    require(receipt['nominated_manifest_sha256'] == status['variants'][VARIANTS[0]]['manifest_sha256'],
            'Guide describes a stale manifest')
    for field, base in (('sources', candidate.parent), ('page_images', output),
                        ('mesh_files', candidate / 'out' / VARIANTS[0])):
        require(bool(receipt.get(field)), 'Guide binding map is empty: ' + field)
        for name, digest in receipt[field].items():
            snapshot.bind(base / name, digest)
    pdf = output / receipt['guide_pdf_filename']
    snapshot.bind(pdf, receipt['guide_pdf_sha256'], tracked=True)
    qa = snapshot.load(output / 'visual-review-followup.json')
    require(qa.get('status') == 'pass' and qa.get('guide_receipt_sha256') == sha(snapshot.read(receipt_path)) and
            qa.get('guide_pdf_sha256') == receipt['guide_pdf_sha256'] and qa.get('page_images') == receipt['page_images'] and
            qa.get('pages_inspected') == receipt['page_count'] == len(receipt['page_images']),
            'Current complete-page guide visual review is required')
    post = load_helper(candidate / 'guide/record_post_guide_check.py', '_delivery_postguide').verify_receipt()
    for name, digest in post['input_sha256'].items():
        snapshot.bind(candidate / name, digest)
    snapshot.bind(output / 'post-guide-build-order-check.log', post['log_sha256'])
    source_zip = output / (GUIDE_ID + '-source-and-pages.zip')
    snapshot.read(source_zip, tracked=False)
    extras = {}
    with zipfile.ZipFile(source_zip) as archive:
        require(archive.testzip() is None, 'Guide source ZIP CRC failure')
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate member in guide source ZIP')
        require(snapshot.relative(receipt_path) in names and snapshot.relative(pdf) in names, 'Guide ZIP omits PDF/receipt')
        for name in names:
            safe_name(name)
            if name in {'START-HERE.txt', 'requirements-guide.txt'}:
                extras[name] = archive.read(name)
                continue
            require(archive.read(name) == snapshot.read(snapshot.repo / name, tracked=False),
                    'Guide source ZIP member is stale: ' + name)
    return {'status': 'current separately generated guide verified', 'page_count': receipt['page_count'],
            'pdf': pdf.name, 'pdf_sha256': receipt['guide_pdf_sha256'],
            'full_source_zip_reference': source_zip.name,
            'full_source_zip_sha256': sha(snapshot.read(source_zip, tracked=False)),
            'full_source_zip_copied': False, 'source_members_distributed_across_small_zips': len(names),
            'post_guide_build_order_tests': post['tests_run']}, [pdf], names, extras


def inspect_product_renders(snapshot, status):
    candidate = snapshot.repo / CANDIDATE
    followup = candidate / 'review-2026-10-12-followup'
    run_path = followup / 'render-run.json'
    run = snapshot.load(run_path)
    snapshot.bind(followup / 'render_variants.py', run.get('source_sha256'), tracked=True)
    expected_pairs = {(variant, view) for variant in VARIANTS for view in RENDER_VIEWS}
    rows = run.get('checks', [])
    pairs = [(row.get('variant'), row.get('view')) for row in rows]
    require(len(pairs) == len(expected_pairs) and set(pairs) == expected_pairs,
            'Render execution receipt omits or duplicates required variant/view pairs')
    manifests = {variant: status['variants'][variant]['manifest_sha256'] for variant in VARIANTS}
    renderer_hash = sha(snapshot.read(candidate / 'render_review.py'))
    images = {}
    files = {run_path, followup / 'render-visual-review.json'}
    for row in rows:
        variant, view = row['variant'], row['view']
        require(row.get('manifest_sha256') == manifests[variant] and row.get('physical_qualified') is False,
                'Render execution receipt binds stale geometry or loses the physical hold')
        directory = candidate / 'out' / variant / 'renders'
        receipt_path = directory / (view + '-receipt.json')
        receipt = snapshot.load(receipt_path)
        require(receipt.get('view') == view and receipt.get('manifest_sha256') == manifests[variant] and
                receipt.get('renderer_sha256') == renderer_hash and receipt.get('physical_qualified') is False,
                'Per-view render receipt binds stale inputs: ' + snapshot.relative(receipt_path))
        image = directory / (view + '.png')
        snapshot.bind(image, receipt.get('image_sha256'), tracked=True)
        images[image.relative_to(candidate).as_posix()] = receipt['image_sha256']
        files.update((image, receipt_path))
    qa_path = followup / 'render-visual-review.json'
    qa = snapshot.load(qa_path)
    require(qa.get('status') == 'pass' and qa.get('physical_qualified') is False and
            qa.get('images_inspected') == len(expected_pairs) and
            qa.get('render_run_sha256') == sha(snapshot.read(run_path)) and
            qa.get('manifest_sha256') == manifests and qa.get('images') == images,
            'Complete current twelve-image visual review is required')
    return {'image_count': len(images), 'views_per_variant': list(RENDER_VIEWS),
            'manifest_sha256': manifests, 'images': images,
            'run_receipt': snapshot.relative(run_path), 'run_receipt_sha256': sha(snapshot.read(run_path)),
            'visual_review': snapshot.relative(qa_path), 'visual_review_sha256': sha(snapshot.read(qa_path)),
            'scope': 'Current source-bound product illustrations; no physical qualification.'}, files


def inspect_structural_pdf(snapshot, status):
    candidate = snapshot.repo / CANDIDATE
    directory = candidate / 'structural-review/output/pdf'
    pdf = directory / 'D2-shadow-plenum-structural-supplement.pdf'
    receipt_path = directory / 'structural-supplement-pdf-receipt.json'
    receipt = snapshot.load(receipt_path)
    require(receipt.get('artifact') == pdf.name and receipt.get('manifest_sha256') ==
            status['variants'][VARIANTS[0]]['manifest_sha256'] and
            receipt.get('text_checks_pass') is True and receipt.get('physical_qualified') is False,
            'Structural PDF receipt is stale, text-unchecked or lacks the physical hold')
    snapshot.bind(pdf, receipt.get('pdf_sha256'), tracked=True)
    sources = receipt.get('source_sha256', {})
    require(isinstance(sources, dict) and {
        'out/' + VARIANTS[0] + '/manifest.json', 'out/' + VARIANTS[0] + '/verification.json',
        'structural-review/build_shadow_structural_pdf.py', 'structural-review/CONCEALED-VENT-STRUCTURAL.md',
        'structural-review/concealed-vent-structural.json'}.issubset(sources),
        'Structural PDF source bindings are incomplete')
    for name, digest in sources.items():
        snapshot.bind(candidate / name, digest)
    qa = receipt.get('visual_review')
    pages = receipt.get('pages')
    require(isinstance(qa, dict) and type(pages) is int and pages > 0 and
            qa.get('status') == 'passed' and qa.get('pages_inspected') == pages and
            qa.get('physical_qualified') is False,
            'Complete current structural PDF visual review is required')
    rendered = qa.get('rendered_page_sha256', {})
    require(isinstance(rendered, dict) and set(rendered) == {f'qa/page-{number}.png' for number in range(1, pages + 1)},
            'Structural PDF visual-review page set is incomplete')
    files = {pdf, receipt_path}
    for name, digest in rendered.items():
        snapshot.bind(directory / name, digest, tracked=True)
        files.add(directory / name)
    return {'pdf': snapshot.relative(pdf), 'pdf_sha256': receipt['pdf_sha256'], 'pages': pages,
            'receipt': snapshot.relative(receipt_path), 'receipt_sha256': sha(snapshot.read(receipt_path)),
            'manifest_sha256': receipt['manifest_sha256'], 'catch_summary': receipt.get('catch_summary'),
            'visual_review_status': qa['status'], 'pages_inspected': qa['pages_inspected'],
            'physical_qualified': False}, files


def select_groups(snapshot, status):
    candidate = snapshot.repo / CANDIDATE
    core = []
    for name in snapshot.entries:
        path = PurePosixPath(name)
        if ('meshes' not in path.parts and
                (path.suffix.lower() in TEXT_SUFFIXES or path.name in {'.gitignore', '.gitattributes', 'Dockerfile', 'Makefile'})):
            core.append(name)
    groups = {'core-review': core}
    common = [CANDIDATE + '/' + name for name in ('README.md', 'REVIEW.md', 'REPRODUCE.md')]
    prints = []
    gauges = []
    for variant in VARIANTS:
        base = CANDIDATE + '/out/' + variant + '/'
        evidence = [base + n for n in ('manifest.json', 'verification.json', 'print-checks.json',
                                      'print-mesh-checks.json', 'check-scope-checks.json', 'shadow-plenum-checks.json')]
        groups[variant + '-assembly'] = common + evidence + [base + 'assembly.step']
        prints.extend(evidence + [base + name for name in status['variants'][variant]['production_prints']['files']])
        production = set(status['variants'][variant]['production_prints']['files'])
        manifest = snapshot.load(snapshot.repo / (base + 'manifest.json'))
        gauges.extend(base + n for n in manifest['files'] if n.startswith('stl/') and n not in production)
    groups['production-STL-review'] = common + prints
    coupon_dirs = ('structural-review/coupons', 'structural-review/bonded-catch-coupon', 'vent-study/shadow-plenum-coupon')
    coupons = [name for name in snapshot.entries if any(name.startswith(CANDIDATE + '/' + d + '/') for d in coupon_dirs)]
    # The bonded coupon is a current derivative; inherited structural/plenum
    # aids retain their own historical scopes rather than claiming current fit.
    bonded = candidate / 'structural-review/bonded-catch-coupon'
    receipt = snapshot.load(bonded / 'receipt.json')
    require(receipt['manifest_sha256'] == status['variants'][VARIANTS[0]]['manifest_sha256'] and
            receipt['physical_qualified'] is False, 'Bonded-catch coupon is stale or lost its physical hold')
    for name, digest in receipt['input_sha256'].items():
        snapshot.bind(candidate / name, digest)
    sources = receipt.get('source_sha256', {})
    require(isinstance(sources, dict), 'Unsupported bonded-coupon source binding')
    for name, digest in sources.items():
        snapshot.bind(candidate / name, digest)
    for name, digest in receipt['files'].items():
        snapshot.bind(bonded / name, digest, tracked=True)
    require(coupons, 'Custom coupon set is absent')
    groups['custom-test-aids'] = common + coupons + gauges
    status['product_renders'], render_files = inspect_product_renders(snapshot, status)
    status['structural_pdf'], structural_files = inspect_structural_pdf(snapshot, status)
    groups['visual-and-structural-review'] = common + [snapshot.relative(path) for path in render_files | structural_files]
    for names in groups.values():
        for name in names:
            require(name in snapshot.entries, 'Selected delivery member is not committed: ' + name)
    status['coupon_scope'] = ('Current source-bound bonded-catch local coupon; inherited structural and plenum '
                              'screening aids retain their own dated scope. Separate gauges are not production pieces. '
                              'No coupon qualifies the complete tub, bond process, or whole-camera loads.')
    return {key: sorted(set(value)) for key, value in groups.items()}


def readme(snapshot, status):
    lines = ['D2 CATCH/QT FOLLOWUP REVIEW HANDOFF', '', 'REVIEW ONLY. BLOCKED FOR PHYSICAL RELEASE.',
             'No fabrication, energization or complete-service release.',
             f"All {status['physical_gates']['inherited_open']} inherited physical gates plus M1 remain open.", '',
             f"Inherited inventory: {status['physical_gates']['inherited_total']} total / "
             f"{status['physical_gates']['inherited_open']} open / "
             f"{status['physical_gates']['inherited_withdrawn']} historically withdrawn.",
             'Previously withdrawn deleted features: ' + ', '.join(status['physical_gates']['withdrawn_ids']) +
             '. Exact baseline states are preserved; no new waiver.', '',
             'Branch: ' + snapshot.branch, 'Commit: ' + snapshot.commit, 'Tree: ' + snapshot.tree,
             'Required baseline ancestor: ' + snapshot.baseline, '',
             'No remote publication was performed by this packaging operation.',
             'Clone the full-history bundle for the complete tracked checkout and this branch history:',
             f'git clone -b {snapshot.branch} {PREFIX}-full-history.bundle digital8mm-review',
             'Verify git rev-parse HEAD and HEAD^{tree} against the values above.', '',
             'The core ZIP set contains tracked text/source/evidence, not a complete standalone CAD build.',
             'Every ZIP is ordinary and independently extractable, strictly below 14,000,000 bytes.',
             'Numbered ZIPs are separate archives, not split volumes. Extract them into one directory.',
             'CONTENTS-SHA256.json verifies every payload and generated metadata member in that ZIP.',
             'DELIVERY-STATUS.json preserves report summaries, failure rows, scope and input hashes.',
             'Older diagnostics and documentation remain historical; use this status and the followup review first.',
             'Start: ' + CANDIDATE + '/review-2026-10-12-followup/FOLLOWUP-REVIEW.md', '', 'CURRENT COMPUTED EVIDENCE']
    for variant, value in status['variants'].items():
        lines += [variant + ':', '  Manifest SHA256: ' + value['manifest_sha256'],
                  '  Production inventory: ' + str(value['production_prints']['assembly_row_count']) +
                  ' CAD assembly rows / ' + str(value['production_prints']['piece_count']) + ' physical prints; gauges/coupons excluded.']
        for label, report in value['reports'].items():
            summary = report['summary'] if report['summary'] is not None else {'pass': report['pass_count'], 'fail': report['fail_count']}
            lines.append('  ' + label + ': ' + json.dumps(summary, sort_keys=True))
            for failed in report['failed_rows']:
                row = failed['row']
                lines.append('    FAIL: ' + str(row.get('category', failed['location'])) + '/' + str(row.get('id', row.get('part', 'see report'))))
        lines += ['  Catch: ' + json.dumps(value['catch'], sort_keys=True), '  Harness scope: ' + value['harness_scope']]
    lines += ['', 'Compact-Kowa harness only: ' + json.dumps(status['harness']['summary'], sort_keys=True),
              'Harness failures: ' + json.dumps(status['harness']['failing'], sort_keys=True)]
    refresh = status['harness_refresh']
    lines += ['Current harness evidence comes from the separate strengthened full harness rerun:',
              '  Receipt: ' + refresh['receipt'],
              '  Started: ' + refresh['started_utc'] + '; completed: ' + refresh['completed_utc'],
              '  Exit: ' + str(refresh['exit_code']) + '; summary: ' + json.dumps(refresh['summary'], sort_keys=True),
              '  Current report SHA256: ' + refresh['report_sha256'],
              '  Prior batch harness archive: ' + refresh['prior_report_archive'],
              '  Prior batch harness summary: ' + json.dumps(refresh['prior_summary'], sort_keys=True),
              'The original primary batch remains execution history; it did not execute the current strengthened harness code.']
    for row in status['qt_rows']:
        lines.append('QT ' + str(row.get('category')) + '/' + str(row.get('id')) + ': ' + str(row.get('status')))
    failed_children = [{'check': row['check'], 'exit_code': row['exit_code']} for row in status['primary_child_checks'] if row['exit_code'] != 0]
    lines += ['Original primary-run nonzero child checks: ' + json.dumps(failed_children, sort_keys=True),
              'Primary aggregate status: ' + str(status['primary_aggregate']['status']),
              'Review reconciliation: ' + json.dumps(status['reconciliation'], sort_keys=True),
              'A separate post-guide rerun, if supplied, supplements rather than erases the recorded batch result.', '',
              'The original-storage plenum historical-reference diagnostic remains visible; it is not established physical interference.',
              'Finite-pose catch calculations and cable sweeps do not qualify continuous tolerances, adhesive/print process, or service.',
              'Actual cooler, flexible cables, electrical drop, thermal, print, bond and strength qualification remain open.',
              status['coupon_scope'], '', 'GUIDE', json.dumps(status['guide'], sort_keys=True), '',
              'CURRENT VISUAL AND STRUCTURAL REVIEW',
              str(status['product_renders']['image_count']) + ' inspected current product renders across all three variants.',
              'Views per variant: ' + ', '.join(status['product_renders']['views_per_variant']) + '.',
              'Structural supplement: ' + str(status['structural_pdf']['pages']) + ' pages, all visually inspected; ' +
              status['structural_pdf']['pdf'], '',
              'Archives exclude working .git internals, local credentials, virtual environments and caches.',
              'The bundle contains the full tracked branch history. Ignored meshes/vendor downloads must be regenerated as described in REPRODUCE.md.',
              'All source/report hashes and checkpoint identity were checked again before publishing this local output directory.', '']
    return '\n'.join(lines).encode()


def write_zip(path, payload, readme_bytes, status_bytes, identity, group):
    generated = {'DELIVERY-README.txt': readme_bytes, 'DELIVERY-STATUS.json': status_bytes}
    require(not (set(payload) & set(generated)), 'Payload collides with delivery metadata')
    members = {**payload, **generated}
    hashes = {name: sha(data) for name, data in sorted(members.items())}
    members['CONTENTS-SHA256.json'] = encoded({'identity': identity, 'group': group,
                                              'files': hashes, 'scope': 'All members except this self-describing hash inventory'})
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            safe_name(name)
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(path) as archive:
        require(archive.testzip() is None, 'ZIP CRC failure: ' + path.name)
        require(set(archive.namelist()) == set(members) and len(archive.namelist()) == len(members),
                'ZIP member set changed: ' + path.name)
        for name, data in members.items():
            require(sha(archive.read(name)) == sha(data), 'ZIP member SHA256 mismatch: ' + name)
    return {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()),
            'payload_members': len(payload), 'total_members': len(members), 'group': group}


def write_zip_set(folder, name, names, snapshot, readme_bytes, status_bytes, identity, limit=LIMIT,
                  allow_untracked=False, extras=None):
    """Bisect oversized sets; each resulting ZIP remains a standalone archive."""
    chunks = []

    def partition(selected):
        trial = folder / ('trial-' + name + '.zip')
        payload = {member: extras[member] if extras and member in extras else
                   snapshot.read(snapshot.repo / member, tracked=not allow_untracked) for member in selected}
        record = write_zip(trial, payload, readme_bytes, status_bytes, identity, name)
        if record['bytes'] < limit:
            target = folder / (PREFIX + '-' + name + '-' + str(len(chunks) + 1).zfill(2) + '.zip')
            trial.rename(target)
            record['file'] = target.name
            chunks.append(record)
            return
        trial.unlink()
        require(len(selected) > 1, 'One member plus metadata exceeds ZIP limit: ' + selected[0])
        midpoint = len(selected) // 2
        partition(selected[:midpoint])
        partition(selected[midpoint:])

    require(names, 'Empty ZIP group: ' + name)
    partition(names)
    if len(chunks) == 1:
        target = folder / (PREFIX + '-' + name + '.zip')
        (folder / chunks[0]['file']).rename(target)
        chunks[0]['file'] = target.name
    return chunks


def inspect_history(snapshot):
    """Reject credential paths/key material in the selected history as well."""
    objects = git(snapshot.repo, 'rev-list', '--objects', snapshot.commit).decode().splitlines()
    for line in objects:
        if ' ' in line and line.split(' ', 1)[1]:
            safe_name(line.split(' ', 1)[1])
    process = subprocess.Popen(['git', '-C', str(snapshot.repo), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for line in objects:
            oid = line.split(' ', 1)[0]
            process.stdin.write(oid.encode() + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            require(len(header) == 3 and header[0].decode() == oid, 'Cannot inspect a history object')
            remaining, tail = int(header[2]), b''
            while remaining:
                block = process.stdout.read(min(remaining, 1024 * 1024))
                require(bool(block), 'Truncated history object')
                remaining -= len(block)
                if header[1] == b'blob':
                    require(not PRIVATE_KEY.search(tail + block),
                            'Potential private key material in branch history; bundle not created')
                    tail = block[-128:]
            require(process.stdout.read(1) == b'\n', 'Invalid history object framing')
        process.stdin.close()
        require(process.wait() == 0, 'History object inspection failed')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if not process.stdin.closed:
            process.stdin.close()
        process.stdout.close()
        process.stderr.close()


def create_bundle(snapshot, folder):
    # Only the selected branch and its ancestry, never arbitrary local refs.
    inspect_history(snapshot)
    path = folder / (PREFIX + '-full-history.bundle')
    ref = 'refs/heads/' + snapshot.branch
    git(snapshot.repo, 'bundle', 'create', '--version=3', str(path), ref)
    git(snapshot.repo, 'bundle', 'verify', str(path))
    require(git(snapshot.repo, 'bundle', 'list-heads', str(path)).decode().strip() == snapshot.commit + ' ' + ref,
            'Bundle refs differ from the nominated branch/commit')
    with path.open('rb') as stream:
        require(stream.readline().startswith(b'# v3 git bundle'), 'Unexpected bundle header')
        while True:
            line = stream.readline()
            require(bool(line), 'Truncated bundle header')
            if line == b'\n':
                break
            require(not line.startswith(b'-'), 'Bundle has prerequisites; full history is required')
    with tempfile.TemporaryDirectory(prefix='verify-bundle-', dir=folder) as temporary:
        checkout = Path(temporary) / 'verified.git'
        git(folder, 'clone', '--bare', '--quiet', str(path), str(checkout))
        git(checkout, 'fsck', '--full', '--no-reflogs')
        require(git(checkout, 'rev-parse', ref).decode().strip() == snapshot.commit and
                git(checkout, 'rev-parse', ref + '^{tree}').decode().strip() == snapshot.tree,
                'Restored bundle commit/tree differs')
        require(git(checkout, 'rev-list', snapshot.commit) == git(snapshot.repo, 'rev-list', snapshot.commit),
                'Restored bundle history differs')
    return {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()),
            'scope': 'Complete ancestry and tracked checkout of the nominated delivery branch; no ZIP-size limit',
            'verified_by': 'bundle verify, fresh bare clone, fsck, exact HEAD/tree/history comparison'}


def main(argv=None):
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--expect-commit', required=True, help='Full final local commit SHA, supplied explicitly')
    parser.add_argument('--output', type=Path, help='New output directory outside the repository')
    parser.add_argument('--with-guide', action='store_true', help='Require current PDF and all verified source/pages members in small ZIPs')
    parser.add_argument('--check-only', action='store_true', help='Verify checkpoint and evidence without producing archives')
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[4]
    snapshot = Snapshot(repo, args.expect_commit)
    status = inspect_evidence(snapshot)
    status['guide'] = {'status': 'Not included; current followup PDF/source ZIP are separate deliverables. No older guide is claimed current.'}
    guide_paths = []
    guide_names, guide_extras = [], {}
    if args.with_guide:
        status['guide'], guide_paths, guide_names, guide_extras = inspect_guide(snapshot, status)
    groups = select_groups(snapshot, status)
    if guide_names:
        supplied = set().union(*map(set, groups.values()))
        groups['guide-source-and-pages'] = sorted(set(guide_names) - supplied)
        require(set(guide_names) <= set().union(*map(set, groups.values())), 'Guide reproducibility set is incomplete')
    identity = {'branch': snapshot.branch, 'commit': snapshot.commit, 'tree': snapshot.tree, 'baseline_ancestor': snapshot.baseline}
    status['identity'] = identity
    status['group_payload_counts'] = {name: len(paths) for name, paths in groups.items()}
    if args.check_only:
        snapshot.finish()
        print(json.dumps({'preflight': 'pass', **identity, 'groups': status['group_payload_counts'], 'physical_release': False}))
        return 0
    require(args.output is not None, '--output is required unless --check-only is selected')
    destination = args.output.resolve()
    require(not destination.is_relative_to(repo) and not destination.exists(), 'Output must be a new directory outside the repository')
    require(destination.parent.is_dir(), 'Output parent must already exist')
    readme_bytes, status_bytes = readme(snapshot, status), encoded(status)
    with tempfile.TemporaryDirectory(prefix='.delivery-staging-', dir=destination.parent) as staging:
        folder = Path(staging) / 'verified-delivery'
        folder.mkdir()
        records = []
        for name, paths in groups.items():
            records.extend(write_zip_set(folder, name, paths, snapshot, readme_bytes, status_bytes, identity,
                                         allow_untracked=name == 'guide-source-and-pages', extras=guide_extras))
        if guide_names:
            delivered = set()
            for record in records:
                with zipfile.ZipFile(folder / record['file']) as archive:
                    delivered.update(archive.namelist())
            require(set(guide_names) <= delivered, 'Written ZIP set omits guide reproducibility members')
        records.append(create_bundle(snapshot, folder))
        for source in guide_paths:
            data = snapshot.read(source, tracked=False)
            (folder / source.name).write_bytes(data)
            require((folder / source.name).read_bytes() == data, 'Copied guide differs')
            records.append({'file': source.name, 'bytes': len(data), 'sha256': sha(data), 'scope': 'Separately verified guide deliverable'})
        (folder / 'DELIVERY-README.txt').write_bytes(readme_bytes)
        (folder / 'DELIVERY-STATUS.json').write_bytes(status_bytes)
        records.extend({'file': name, 'bytes': (folder / name).stat().st_size, 'sha256': sha((folder / name).read_bytes())}
                       for name in ('DELIVERY-README.txt', 'DELIVERY-STATUS.json'))
        snapshot.finish()
        inventory = {'identity': identity, 'created_utc': datetime.now(timezone.utc).isoformat(),
                     'physical_release': False, 'source_snapshot_verified': True,
                     'zip_limit_bytes_exclusive': LIMIT, 'artifacts': records}
        (folder / 'delivery-manifest.json').write_bytes(encoded(inventory))
        require(not destination.exists(), 'Output appeared during packaging; refusing to replace it')
        os.rename(folder, destination)
    print(json.dumps({'output': str(destination), **identity, 'artifacts': len(records), 'physical_release': False}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (PackageError, OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print('Packaging blocked: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
