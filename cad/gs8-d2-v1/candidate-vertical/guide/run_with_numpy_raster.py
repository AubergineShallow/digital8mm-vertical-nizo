"""Run a guide builder with the pure-numpy Z-buffer instead of the compiled raster.cpp (review VN-12, FP-15).

Usage (under the CAD wrapper, from cad/gs8-d2-v1):
    <venv python> run_locked.py -- candidate-vertical/guide/run_with_numpy_raster.py [--builder NAME] -- <builder args>
NAME defaults to build_guide_concealed_vents.py (the selected guide); build_guide_vertical.py is the frozen original.

Why a launcher and not an edit of software_lineart.py: the guide receipt binds software_lineart.py and raster.cpp by
SHA-256, so both stay byte-identical. software_lineart.py builds raster.so with `g++ -fPIC` at import and loads it
with ctypes; on Windows (32-bit MinGW g++, 64-bit CPython) that library cannot load. This launcher, only while
`software_lineart` is imported, answers the raster.cpp build with "already built" and returns, for the raster.so
path only, an object whose `raster` entry point runs raster_numpy.raster on the same buffers (same arguments, same
in-place result; equivalence with raster.cpp is tested in tests/test_raster_fallback.py). Every other subprocess or
library load goes to the real functions. The builder then runs unchanged as __main__ with the given arguments.

Provenance: the builder's own receipt still binds raster.cpp and software_lineart.py; this launcher additionally
writes guide/out-concealed-vents/raster-backend.json (backend, launcher, raster_numpy.py and raster.cpp SHA-256,
numpy version) after a successful build of the selected guide, so a page set built this way says so.
"""
from pathlib import Path
import contextlib
import ctypes
import hashlib
import json
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import numpy as np  # noqa: E402
import raster_numpy  # noqa: E402
from cv_io import write_text  # noqa: E402

BACKEND = 'numpy (raster_numpy.py via run_with_numpy_raster.py)'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class NumpyRasterLib:
    """Stands in for ctypes.CDLL('raster.so'): raster(n, pts, colors, w, h, image, depth) on raw buffer addresses."""

    class _Entry:
        argtypes = None

        def __call__(self, n, pts, colors, w, h, image, depth):
            n, w, h = int(n), int(w), int(h)
            if n <= 0:
                return 0
            view = lambda addr, ct, k: np.ctypeslib.as_array((ct * k).from_address(int(addr)))
            raster_numpy.raster(view(pts, ctypes.c_double, 9 * n).reshape(n, 3, 3),
                                view(colors, ctypes.c_ubyte, 3 * n).reshape(n, 3), w, h,
                                view(image, ctypes.c_ubyte, h * w * 3).reshape(h, w, 3),
                                view(depth, ctypes.c_double, h * w).reshape(h, w))
            return 0

    def __init__(self):
        self.raster = self._Entry()


def _is_raster_build(cmd):
    return isinstance(cmd, (list, tuple)) and cmd and str(cmd[0]).endswith(('g++', 'g++.exe')) and any(str(c).endswith('raster.cpp') for c in cmd)


@contextlib.contextmanager
def numpy_raster():
    """While active: the raster.cpp build is skipped and ctypes.CDLL('.../raster.so') returns NumpyRasterLib()."""
    real_run, real_cdll = subprocess.run, ctypes.CDLL

    def run(cmd, *a, **k):
        if _is_raster_build(cmd):
            return subprocess.CompletedProcess(cmd, 0)
        return real_run(cmd, *a, **k)

    def cdll(name, *a, **k):
        if Path(str(name)).name == 'raster.so':
            return NumpyRasterLib()
        return real_cdll(name, *a, **k)

    subprocess.run, ctypes.CDLL = run, cdll
    try:
        yield
    finally:
        subprocess.run, ctypes.CDLL = real_run, real_cdll


def import_software_lineart():
    """Import guide/software_lineart.py (unchanged) with the numpy backend; returns the module."""
    if 'software_lineart' in sys.modules:
        mod = sys.modules['software_lineart']
        if not isinstance(mod.lib, NumpyRasterLib):
            raise RuntimeError('software_lineart was already imported with the native backend')
        return mod
    with numpy_raster():
        import software_lineart
    return software_lineart


def main(argv):
    builder = 'build_guide_concealed_vents.py'
    if argv[:1] == ['--builder']:
        builder, argv = argv[1], argv[2:]
    if argv[:1] == ['--']:
        argv = argv[1:]
    script = HERE / builder
    if script.parent != HERE or not script.is_file():
        raise SystemExit('unknown guide builder: %s' % builder)
    import_software_lineart()
    sys.argv = [str(script)] + list(argv)
    runpy.run_path(str(script), run_name='__main__')
    if builder == 'build_guide_concealed_vents.py':
        rec = dict(backend=BACKEND, builder=builder, launcher_sha256=sha(__file__),
                   raster_numpy_sha256=sha(HERE / 'raster_numpy.py'), raster_cpp_sha256=sha(HERE / 'raster.cpp'),
                   software_lineart_sha256=sha(HERE / 'software_lineart.py'), numpy_version=np.__version__,
                   equivalence_test='candidate-vertical/tests/test_raster_fallback.py')
        write_text(HERE / 'out-concealed-vents/raster-backend.json', json.dumps(rec, indent=2) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:])
