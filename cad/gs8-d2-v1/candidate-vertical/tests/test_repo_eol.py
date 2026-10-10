# SPDX-License-Identifier: MIT
"""Line-ending safety of the whole repository (review VN-01, fix FP-01).

Build receipts and manifests hash exact file bytes, so Git must never convert line endings. Checks:
- `.gitattributes` starts with `* -text`, and `git check-attr` reports text unset (and no eol, filter or
  working-tree-encoding) for every tracked file and every file the next commit would add;
- no CR in tracked text files, except the frozen list in eol-cr-allowlist.json (r7-inherited bytes, identical to
  the r7 commit, and the manufacturer's hash-bound licence); new untracked text files carry no CR either;
- an emulated fresh Windows clone (`git -c core.autocrlf=true checkout-index` from a temporary index holding the
  next-commit bytes and .gitattributes) reproduces every sampled file byte for byte, while the 9ced753 attributes
  do not (negative control, so the emulation cannot go blind);
- the r7 `audit_cloud_release.py --final-release` passes on such an emulated clone (set FP01_SKIP_AUDIT=1 to skip).

Run: run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_repo_eol.py
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_git import REPO, CV, git, zsplit, tracked, untracked_new, index_entries, eol_info, blob_sha1  # noqa: E402

ALLOWLIST = Path(__file__).resolve().parent / 'eol-cr-allowlist.json'
SAMPLE_MAX_BYTES = 4_000_000
# Fixture: the attributes of 9ced753 that caused VN-01 (binary-only rules, no `* -text`).
OLD_ATTRS = (b'# Treat generated CAD and document artifacts as opaque review assets.\n*.step -diff -text\n'
             b'*.stp -diff -text\n*.stl -diff -text\n*.pdf -diff -text\n*.png -diff -text\n*.ttf -diff -text\n'
             b'*.docx -diff -text\n')
TEXT_INFO = ('i/lf', 'i/crlf', 'i/mixed', 'i/none')


def next_commit_paths():
    return sorted(set(tracked()) | set(untracked_new()))


def check_attrs(paths, attrs=('text', 'eol', 'working-tree-encoding', 'filter')):
    raw = git('check-attr', '-z', '--stdin', *attrs, input=('\0'.join(paths) + '\0').encode('utf-8'))
    f = zsplit(raw)
    return {(f[i], f[i + 1]): f[i + 2] for i in range(0, len(f), 3)}


class Emulation:
    """A throwaway repository that borrows this clone's objects (alternates); nothing is written to the clone."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='fp01-'))
        self.work = self.tmp / 'w'
        git('init', '-q', str(self.work))
        alt = self.work / '.git' / 'objects' / 'info' / 'alternates'
        alt.write_bytes(((REPO / '.git' / 'objects').as_posix() + '\n').encode('utf-8'))   # LF: git rejects CR
        self.env = {'GIT_DIR': str(self.work / '.git'), 'GIT_INDEX_FILE': str(self.tmp / 'index')}

    def g(self, *args, **kw):
        return git('-c', 'core.longpaths=true', *args, env=self.env, cwd=self.work, **kw)

    def hash_files(self, abs_paths):
        if not abs_paths:
            return []
        out = self.g('hash-object', '-w', '--no-filters', '--stdin-paths',
                     input=('\n'.join(str(p) for p in abs_paths) + '\n').encode('utf-8'))
        return out.decode().split()

    def checkout(self, entries, attrs_bytes, name, autocrlf='true'):
        """entries {path: (mode, sha)}; returns {path: written blob sha1} under prefix `name`."""
        attrs_sha = self.g('hash-object', '-w', '--stdin', input=attrs_bytes).decode().strip()
        idx = dict(entries)
        idx['.gitattributes'] = ('100644', attrs_sha)
        index = self.tmp / 'index'
        if index.exists():
            index.unlink()
        info = ''.join('%s %s\t%s\0' % (m, s, p) for p, (m, s) in sorted(idx.items()))
        self.g('update-index', '-z', '--index-info', input=info.encode('utf-8'))
        self.g('-c', 'core.autocrlf=' + autocrlf, 'checkout-index', '-a', '-f', '--prefix=%s/' % name)
        root = self.work / name
        return {p: blob_sha1((root / p).read_bytes()) for p in entries}

    def close(self):
        if not os.environ.get('FP01_KEEP_TMP'):
            def make_writable(func, path, _exc):   # git writes loose objects read-only; Windows refuses to delete them
                os.chmod(path, 0o666)
                func(path)
            key = 'onexc' if sys.version_info >= (3, 12) else 'onerror'
            shutil.rmtree(self.tmp, **{key: make_writable})


def next_commit_entries(paths, emu):
    """{path: (mode, sha)} as the next commit would store them: index blobs, or working bytes if changed/new."""
    index = index_entries()
    changed = set(zsplit(git('diff', '--name-only', '-z'))) | set(untracked_new())
    out, to_hash = {}, []
    for p in paths:
        if not (REPO / p).is_file():
            continue          # deleted in the working tree: not part of the next commit
        if p in changed or p not in index:
            to_hash.append(p)
        else:
            out[p] = index[p]
    for p, sha in zip(to_hash, emu.hash_files([REPO / p for p in to_hash])):
        out[p] = (index.get(p, ('100644', ''))[0], sha)
    return out


class RepoEol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = next_commit_paths()
        cls.eol = eol_info()
        cls.allow = json.loads(ALLOWLIST.read_text(encoding='utf-8'))

    def test_gitattributes_first_rule(self):
        lines = [l.strip() for l in (REPO / '.gitattributes').read_text(encoding='utf-8').splitlines()]
        rules = [l for l in lines if l and not l.startswith('#')]
        self.assertEqual(rules[0], '* -text')
        for r in rules[1:]:
            for a in r.split()[1:]:
                self.assertFalse(a in ('text', 'crlf') or a.startswith(('text=', 'eol=', 'filter=', 'working-tree-encoding=')), r)

    def test_check_attr_text_unset_everywhere(self):
        got = check_attrs(self.paths)
        bad = [(p, a, v) for (p, a), v in got.items()
               if (a == 'text' and v != 'unset') or (a != 'text' and v != 'unspecified')]
        self.assertEqual(len(got), 4 * len(self.paths))
        self.assertEqual(bad[:20], [], '%d attribute violations' % len(bad))

    def test_no_cr_in_tracked_text(self):
        files = self.allow['files']
        index = index_entries()
        bad = []
        for p, (i, w, _attr) in self.eol.items():
            if i not in TEXT_INFO or not (REPO / p).is_file():
                continue
            if p in files:
                continue
            if w[2:] != i[2:] or b'\r' in (REPO / p).read_bytes():   # i/lf vs w/lf, i/none vs w/none
                bad.append((p, i, w))
        self.assertEqual(bad[:20], [], '%d tracked text files with CR or converted endings' % len(bad))
        for p, rec in files.items():
            self.assertIn(p, index, 'allowlisted file no longer tracked: ' + p)
            self.assertEqual(index[p][1], rec['blob_sha1'], 'allowlisted bytes changed in index: ' + p)
            self.assertEqual(blob_sha1((REPO / p).read_bytes()), rec['blob_sha1'], 'working bytes changed: ' + p)
            self.assertIn(rec['reason'], ('r7-inherited', 'vendor-verbatim'), p)

    def test_allowlist_entries_are_justified(self):
        files = self.allow['files']
        r7 = self.allow['r7_commit']
        have_r7 = subprocess.run(['git', 'cat-file', '-e', r7 + '^{commit}'], cwd=str(REPO)).returncode == 0
        bound = json.loads((REPO / CV / 'out/source-components/pi5-corrected.json').read_text(encoding='utf-8'))['sources']
        for p, rec in files.items():
            if rec['reason'] == 'r7-inherited' and have_r7:
                self.assertEqual(git('rev-parse', '%s:%s' % (r7, p)).decode().strip(), rec['blob_sha1'], p)
            if rec['reason'] == 'vendor-verbatim':
                key = p[len('cad/gs8-d2-v1/'):]
                self.assertEqual(hashlib.sha256((REPO / p).read_bytes()).hexdigest(), bound[key], p)

    def test_new_untracked_text_has_no_cr(self):
        info = {}
        for rec in zsplit(git('ls-files', '-z', '--eol', '--others', '--exclude-standard')):
            meta, path = rec.split('\t', 1)
            info[path] = meta.split()[1]
        bad = sorted(p for p, w in info.items() if w in ('w/crlf', 'w/mixed'))
        self.assertEqual(bad, [], 'new files with CR would be committed byte-exact; write them with LF')

    def _sample(self):
        return [p for p in self.paths if (REPO / p).is_file() and (REPO / p).stat().st_size <= SAMPLE_MAX_BYTES
                and p != '.gitattributes']

    def test_emulated_autocrlf_clone_is_byte_exact(self):
        emu = Emulation()
        try:
            entries = next_commit_entries(self._sample(), emu)
            new_attrs = (REPO / '.gitattributes').read_bytes()
            got = emu.checkout(entries, new_attrs, 'new')
            bad = sorted(p for p, (m, s) in entries.items() if got[p] != s)
            print('\n[emulation] new attributes: %d files checked, %d changed' % (len(entries), len(bad)))
            self.assertGreater(len(entries), 900)
            self.assertEqual(bad[:20], [], '%d files changed by an autocrlf checkout' % len(bad))
            old = emu.checkout(entries, OLD_ATTRS, 'old')
            changed = sorted(p for p, (m, s) in entries.items() if old[p] != s)
            print('[emulation] 9ced753 attributes (negative control): %d changed, e.g. %s' % (len(changed), changed[:3]))
            self.assertGreater(len(changed), 100, 'emulation no longer detects the VN-01 regression')
        finally:
            emu.close()

    @unittest.skipIf(os.environ.get('FP01_SKIP_AUDIT'), 'FP01_SKIP_AUDIT set')
    def test_r7_final_release_audit_on_emulated_clone(self):
        emu = Emulation()
        try:
            paths = [p for p in self.paths if not p.startswith(CV) and p != '.gitattributes']
            entries = next_commit_entries(paths, emu)
            got = emu.checkout(entries, (REPO / '.gitattributes').read_bytes(), 'clone')
            self.assertEqual([p for p, (m, s) in entries.items() if got[p] != s], [])
            root = emu.work / 'clone'
            out = root / 'cad/gs8-d2-v1/out'
            report = emu.tmp / 'audit.json'
            cmd = [sys.executable, str(root / 'cad/gs8-d2-v1/audit_cloud_release.py'), '--project', str(root),
                   '--out', str(out), '--final-release', '--alternate-out', str(out / '_fujinon-cloud-polish-20261007'),
                   '--json', str(report)]
            r = subprocess.run(cmd, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            tail = r.stdout.decode('utf-8', 'replace')[-1500:]
            print('\n[r7 audit on emulated clone] exit %d\n%s' % (r.returncode, tail))
            self.assertEqual(r.returncode, 0, tail)
        finally:
            emu.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
