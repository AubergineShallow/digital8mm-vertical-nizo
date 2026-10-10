# SPDX-License-Identifier: MIT
"""Small git helpers shared by the repository-level tests in this folder (FP-01).

Pure standard library; no CAD imports. Paths returned are repo-relative POSIX strings.
"""
from pathlib import Path
import os
import subprocess

REPO = Path(__file__).resolve().parents[4]   # tests -> candidate-vertical -> gs8-d2-v1 -> cad -> repo
CV = 'cad/gs8-d2-v1/candidate-vertical/'


def git(*args, input=None, env=None, cwd=None, check=True):
    """Run git with core.quotepath off and return raw stdout bytes."""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    r = subprocess.run(['git', '-c', 'core.quotepath=off', *args], cwd=str(cwd or REPO), input=input,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=full_env)
    if check and r.returncode != 0:
        raise RuntimeError('git %s failed (%d): %s' % (' '.join(args), r.returncode,
                                                      r.stderr.decode('utf-8', 'replace')))
    return r.stdout


def zsplit(raw):
    return [p for p in raw.decode('utf-8').split('\0') if p]


def tracked():
    """Every tracked path (index), repo-relative POSIX."""
    return zsplit(git('ls-files', '-z'))


def untracked_new():
    """Untracked, not ignored paths: the files the next commit would add."""
    return zsplit(git('ls-files', '-z', '--others', '--exclude-standard'))


def index_entries():
    """{path: (mode, blob_sha1)} from the index."""
    out = {}
    for rec in zsplit(git('ls-files', '-z', '-s')):
        meta, path = rec.split('\t', 1)
        mode, sha, _stage = meta.split()
        out[path] = (mode, sha)
    return out


def eol_info():
    """{path: (i_info, w_info, attr)} from `git ls-files --eol` (i/lf, i/crlf, i/mixed, i/none, i/-text)."""
    out = {}
    for rec in zsplit(git('ls-files', '-z', '--eol')):
        meta, path = rec.split('\t', 1)
        parts = meta.split()
        out[path] = (parts[0], parts[1], parts[2] if len(parts) > 2 else '')
    return out


def blob_sha1(data):
    import hashlib
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def is_binary(data):
    """Git's own content rule for 'binary' (NUL byte in the first 8000 bytes)."""
    return b'\0' in data[:8000]
