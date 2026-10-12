# SPDX-License-Identifier: MIT
"""Light, CAD-free copy of the review tree for the FP-04 evidence-tooling tests.

The copy holds every text file of candidate-vertical (<= 4 MB; STEP/STL/mesh caches, renders and PDFs are left out),
the three complete required main-audit JSONs regardless of size, every manifest source file, the r7 build receipt and electronics/gs8-d2-v1. The scripts are run from inside the copy, so
they import the copy's own helpers and never touch the live tree. Missing binaries make the same bindings fail in every
run of a fixture, so tests compare failure sets between an untouched and a tampered copy.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

CV = Path(__file__).resolve().parents[1]
CAD = CV.parent
REPO = CAD.parents[1]
TEXT = {'.py', '.json', '.md', '.csv', '.txt'}
SKIP = {'step', 'stl', 'meshes', 'renders', '__pycache__', 'review-2026-10-10', 'tests', 'check-logs', '_mismatch'}
VARIANTS = ['compact-kowa_lm6hc', 'compact-fujinon_hf6xa', 'original-kowa_lm6hc']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build(dest):
    """Populate dest (a repo root) and return the copied candidate-vertical folder."""
    dest = Path(dest)
    for root, dirs, files in os.walk(CV):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        for f in files:
            p = Path(root) / f
            if p.suffix in TEXT and p.stat().st_size <= 4_000_000:
                _copy(p, dest / p.relative_to(REPO))
    for v in VARIANTS:
        required = CV / 'out' / v / 'verification.json'
        copied = dest / required.relative_to(REPO)
        _copy(required, copied)
        assert sha(copied) == sha(required), 'Required audit fixture copy differs'
        for rel in json.loads((CV / 'out' / v / 'manifest.json').read_text(encoding='utf-8'))['sources']:
            src = (CAD / rel).resolve()
            if src.is_file():
                _copy(src, dest / src.relative_to(REPO))
    _copy(CAD / 'out/build-receipt.json', dest / 'cad/gs8-d2-v1/out/build-receipt.json')
    for p in (REPO / 'electronics/gs8-d2-v1').rglob('*'):
        if p.is_file() and p.suffix in TEXT and '__pycache__' not in p.parts:
            _copy(p, dest / p.relative_to(REPO))
    return dest / CV.relative_to(REPO)


class Fixture:
    """A base copy built once; clone() gives a fresh copy per mutating test."""
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(prefix='fp04-')
        self.base = Path(self._tmp.name) / 'base'
        self.cv = build(self.base)
        self._n = 0

    def clone(self):
        self._n += 1
        dst = Path(self._tmp.name) / ('c%d' % self._n)
        shutil.copytree(self.base, dst)
        return dst / CV.relative_to(REPO)

    def cleanup(self):
        self._tmp.cleanup()


def run(script, *args, cwd=None, timeout=900):
    """Run a fixture (or live) script with UTF-8 mode on; returns (exit code, stdout, stderr) as text."""
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONIOENCODING',)}
    env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    r = subprocess.run([sys.executable, str(script), *map(str, args)], cwd=str(cwd or Path(script).parent), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def first_json(text):
    """The first top-level indent=2 JSON object a script printed (its own '{' and '}' lines)."""
    lines = text.splitlines()
    s = lines.index('{')
    return json.loads('\n'.join(lines[s:s + lines[s:].index('}') + 1]))
