"""Two full variant audits, serial within an isolated output/lock lane.

The primary lane remains unchanged. Inputs are immutable and hashed before and
after each audit; canonical reports are copied only after identity checks.
Stop this secondary lane if available physical RAM falls below 2 GiB.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cv_io import child_env, open_text, read_text, write_text, rel_posix, relpath_posix


def validate_result(data, code, started):
    if code not in (0, 1):
        raise RuntimeError('Verifier did not finish with a normal verdict')
    if not data.get('checks'):
        raise RuntimeError('Verifier report is empty')
    counts = {name: sum(row.get('status') == name for row in data['checks'])
              for name in ('pass', 'fail', 'info')}
    if counts != data.get('summary') or sum(counts.values()) != len(data['checks']):
        raise RuntimeError('Verifier summary does not match its rows')
    if code != int(counts['fail'] > 0):
        raise RuntimeError('Verifier exit does not match its verdict')
    if data.get('generated_utc', '') < started:
        raise RuntimeError('Verifier report predates this run')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def available_mb():
    for line in Path('/proc/meminfo').read_text(encoding='utf-8').splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) / 1024
    raise RuntimeError('Cannot establish available RAM')


def inputs(variant):
    folder = ROOT / 'out' / variant
    meta = json.loads(read_text(folder / 'manifest.json'))
    paths = {folder / 'manifest.json'}
    paths.update(folder / rel for rel in meta['files'])
    paths.update(ROOT.parent / rel for rel in meta['sources'])
    paths.update(ROOT / name for name in ('verify_candidate.py', 'steps.py', 'cv_io.py',
                 'evidence_rules.py', 'driver_checks.py', 'j7_collar_checks.py', 'j4_slide_checks.py'))
    paths.update(ROOT.parent.glob('*.py'))
    return {relpath_posix(p, ROOT): sha(p) for p in sorted(paths)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    work = Path(args.workspace).resolve()
    work.mkdir(parents=True, exist_ok=True)
    records = []
    for variant in ('compact-fujinon_hf6xa', 'original-kowa_lm6hc'):
        if available_mb() < 4000:
            raise RuntimeError('Secondary audit requires 4 GiB available before launch')
        before = inputs(variant)
        report = work / (variant + '-verification.json')
        if report.exists():
            raise RuntimeError('Use a fresh workspace: an output report already exists')
        log = work / (variant + '.log')
        started = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        command = [sys.executable, str(ROOT / 'verify_candidate.py'), '--variant', variant, '--out', str(report)]
        print(variant, 'starting', started, flush=True)
        low_memory = False
        with open_text(log, 'w') as stream:
            child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                     env=child_env(), close_fds=False)
            try:
                while child.poll() is None:
                    if available_mb() < 2000:
                        low_memory = True
                        child.terminate()
                        break
                    time.sleep(2)
                code = child.wait(timeout=30)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait()
        if low_memory:
            raise RuntimeError('Secondary audit stopped at the 2 GiB RAM reserve; no report adopted')
        if before != inputs(variant):
            raise RuntimeError('Audit inputs changed; isolated report was not adopted')
        data = json.loads(read_text(report))
        validate_result(data, code, started)
        manifest = ROOT / 'out' / variant / 'manifest.json'
        if not (data['scope'] == 'full' and data['variant'] == variant and
                data['manifest_sha256'] == sha(manifest) and
                data['verification_source_sha256'] == sha(ROOT / 'verify_candidate.py') and
                data['state_model_sha256'] == sha(ROOT / 'steps.py')):
            raise RuntimeError('Isolated report identity is invalid; report was not adopted')
        target = manifest.parent / 'verification.json'
        shutil.copyfile(report, target)
        row = dict(variant=variant, started_utc=started,
                   completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   process_exit_code=code, summary=data['summary'], report_sha256=sha(report),
                   input_sha256=before, scope='full, unchanged verifier and thresholds',
                   canonical_report=rel_posix(target, ROOT), physical_qualified=False)
        records.append(row)
        write_text(Path(__file__).with_name('isolated-rigid-run.json'),
                   json.dumps(dict(checks=records, helper_sha256=sha(Path(__file__)),
                                   isolation='Separate report paths and one secondary lock; immutable shared inputs'), indent=2) + '\n')
        print(json.dumps({k: row[k] for k in ('variant', 'process_exit_code', 'summary', 'report_sha256')}), flush=True)
    return int(any(r['process_exit_code'] for r in records))


if __name__ == '__main__':
    raise SystemExit(main())
