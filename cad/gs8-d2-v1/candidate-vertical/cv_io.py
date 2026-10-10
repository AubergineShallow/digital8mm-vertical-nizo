# SPDX-License-Identifier: MIT
"""Platform-neutral text and path I/O for the candidate-vertical scripts (review VN-02/VN-03, fix FP-02).

Every candidate script reads and writes text through these helpers, so a result does not depend on the
platform it was produced on:

- text is decoded and encoded as UTF-8, never the locale code page (cp1252 on this Windows machine);
- text is written with LF line endings, never CRLF (Path.write_text without newline= writes CRLF on Windows);
- every recorded relative path and every manifest key uses '/' separators (str(Path) gives '\\' on Windows).

On POSIX these helpers produce exactly the bytes and strings the bare calls produced, so outputs made on
Linux before FP-02 stay comparable. tests/test_cross_platform_io.py lints every live candidate script so
that no bare text I/O or OS-separator path recording comes back.

Notes
- The module is called cv_io, not _io as the fix plan suggested: `_io` is CPython's built-in I/O module,
  so `import _io` would always load the built-in, never a file of that name.
- ../run_locked.py does not set PYTHONUTF8=1: it is an r7 hash-bound source (r7 audit FONT_SOURCES and the
  candidate manifests bind its bytes), so editing it would break the r7 final-release audit. The candidate
  batch runners pass child_env() (PYTHONUTF8=1) to the Python children they start instead.
- render_review.py runs inside Blender's bundled Python, where this folder is not on sys.path; it passes
  encoding='utf-8' and newline='\\n' explicitly instead of importing this module.
"""
import os
from pathlib import Path, PurePath

ENCODING = 'utf-8'
NEWLINE = '\n'
_WRITE_MODES = set('wax+')


def read_text(path):
    """Text of `path`, decoded as UTF-8 (universal newlines, like Path.read_text)."""
    return Path(path).read_text(encoding=ENCODING)


def write_text(path, text):
    """Write `text` to `path` as UTF-8 with LF line endings; return the number of characters written."""
    return Path(path).write_text(text, encoding=ENCODING, newline=NEWLINE)


def open_text(path, mode='r', **kwargs):
    """open() in text mode with UTF-8; write/append/create modes default to newline='\\n' (no CRLF).

    Read modes keep universal newlines, like a bare open(). Pass newline='' explicitly for the csv module.
    """
    if 'b' in mode:
        raise ValueError('open_text() is for text mode; use open(path, %r) for binary data' % mode)
    kwargs.setdefault('encoding', ENCODING)
    if _WRITE_MODES & set(mode):
        kwargs.setdefault('newline', NEWLINE)
    return open(path, mode, **kwargs)


def posix(path):
    """A relative path as a '/'-separated string on every platform (for keys and recorded paths)."""
    return PurePath(os.fspath(path)).as_posix()


def rel_posix(path, base):
    """Path(path).relative_to(base) as a '/'-separated string, e.g. 'step/pi5.step'.

    Raises ValueError when `path` is not inside `base`, exactly like Path.relative_to.
    """
    return Path(path).relative_to(base).as_posix()


def relpath_posix(path, start):
    """os.path.relpath(path, start) as a '/'-separated string; it may climb, e.g. '../gs8-pxl-v3/x.txt'."""
    return PurePath(os.path.relpath(path, start)).as_posix()


def child_env(**extra):
    """Environment for a Python child process: this one plus PYTHONUTF8=1 (UTF-8 mode guard) and `extra`."""
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env.update(extra)
    return env
