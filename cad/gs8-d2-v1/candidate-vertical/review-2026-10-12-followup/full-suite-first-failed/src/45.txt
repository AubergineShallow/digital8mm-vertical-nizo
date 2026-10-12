# SPDX-License-Identifier: MIT
"""Third-party notice guard (review VN-13, fix FP-01).

Run (tests):   run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_third_party_notices.py
Regenerate:    same script with --write  (writes THIRD-PARTY-NOTICES.md and the LF licence copies)

Rules checked:
- every Pi-derived file (computed from the tree, not listed by hand) has the Raspberry Pi MIT licence
  in its own folder: the manufacturer's LICENSE.txt or LICENSE-RaspberryPi.txt with the same text;
- the manufacturer's LICENSE.txt keeps its hash-bound bytes;
- THIRD-PARTY-NOTICES.md names every Pi-derived file and licence copy, carries the full licence text, and
  the source URL and STEP SHA-256 that official_pi5_csi.py records; every path it names exists;
- every font file has its licence beside it and is named in the notice.
"""
from pathlib import Path, PurePosixPath
import fnmatch
import hashlib
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_git import REPO, CV, tracked, untracked_new  # noqa: E402

VENDOR_DIR = CV + 'routing-snapshots/hdmi-ck1044-clear-20261009-0524/official-fpc-sources/'
VENDOR_LICENSE = VENDOR_DIR + 'LICENSE.txt'
VENDOR_LICENSE_SHA256 = '4ca2d350552b24137e55587e13fb09a249b757c6af49652ff02ea524d154c7fc'  # bound in manifests
COPY_NAME = 'LICENSE-RaspberryPi.txt'
NOTICE = 'THIRD-PARTY-NOTICES.md'
GEOMETRY_EXT = ('.step', '.stp', '.stl', '.glb', '.gltf', '.obj', '.3mf', '.brep')
FONT_EXT = ('.ttf', '.otf', '.woff', '.woff2')


def lf(data):
    return data.replace(b'\r\n', b'\n')


def present_paths():
    """Tracked files plus the untracked, not ignored files the next commit would add."""
    return sorted(set(tracked()) | set(untracked_new()))


def _is_pi_derived(path, paths):
    """Return a short description if `path` holds Raspberry Pi model geometry, else None."""
    p = PurePosixPath(path)
    name = p.name.lower()
    if path.startswith(VENDOR_DIR) or '/official-fpc-sources/' in path:
        if name.startswith('license'):
            return None
        if p.suffix.lower() in GEOMETRY_EXT:
            return 'connector solids extracted unchanged from the official STEP'
        return 'indices and landmark positions measured on the official STEP'
    if not path.startswith(CV):
        return None    # r7 Pi proxies (cots.py pi5) are drawn by this project, not taken from the model
    if name.startswith('pi5') and p.suffix.lower() in GEOMETRY_EXT:
        if name.startswith('pi5-corrected'):
            return 'corrected Pi assembly built from the extracted solids'
        return 'Pi part as exported for this variant'
    if name.startswith('pi5') and p.suffix.lower() == '.json' and p.parent.name == 'meshes':
        return 'tessellation of the Pi part'
    if name.startswith('assembly') and p.suffix.lower() in GEOMETRY_EXT:
        folder = str(p.parent)
        has_pi = any(fnmatch.fnmatch(q, folder + '/step/pi5*') for q in paths)
        man = REPO / folder / 'manifest.json'
        if not has_pi and man.exists():
            has_pi = b'"pi_source_geometry"' in man.read_bytes()
        if has_pi:
            return 'whole-camera assembly that includes the Pi part'
    return None


def pi_derived(paths=None):
    paths = present_paths() if paths is None else paths
    out = {}
    for path in paths:
        what = _is_pi_derived(path, paths)
        if what:
            out[path] = what
    return out


def licence_for(folder):
    """The licence file that covers Pi-derived files in `folder` (repo-relative), or None."""
    for name in ('LICENSE.txt', COPY_NAME):
        f = REPO / folder / name
        if f.exists() and lf(f.read_bytes()) == lf((REPO / VENDOR_LICENSE).read_bytes()):
            return folder + '/' + name
    return None


def source_constants():
    text = (REPO / CV / 'official_pi5_csi.py').read_text(encoding='utf-8')
    url = re.search(r"^SOURCE_URL='([^']+)'", text, re.M).group(1)
    sha = re.search(r"^OFFICIAL_STEP_SHA256='([0-9a-f]{64})'", text, re.M).group(1)
    return url, sha


def fonts(paths=None):
    paths = present_paths() if paths is None else paths
    return [p for p in paths if p.lower().endswith(FONT_EXT)]


def generate_notice(derived=None, paths=None):
    paths = present_paths() if paths is None else paths
    derived = pi_derived(paths) if derived is None else derived
    url, sha = source_constants()
    folders = sorted({str(PurePosixPath(p).parent) for p in derived})
    rows = []
    for folder in folders:
        lic = licence_for(folder) or (folder + '/' + COPY_NAME)
        files = '<br>'.join('`%s` (%s)' % (PurePosixPath(p).name, derived[p])
                            for p in sorted(derived) if str(PurePosixPath(p).parent) == folder)
        rows.append('| `%s` | `%s` | %s |' % (folder + '/', PurePosixPath(lic).name, files))
    licence_text = lf((REPO / VENDOR_LICENSE).read_bytes()).decode('utf-8').rstrip('\n')
    font_lines = []
    for f in fonts(paths):
        folder = str(PurePosixPath(f).parent)
        font_lines.append('- `%s`. Licence: `%s/LICENSE-DejaVu.txt`.' % (f, folder))
    L = []
    L += ['# Third-party notices', '',
          'This repository contains material made by others. This file names each item, its licence, and every',
          'copy or derived file of it in the repository. The project\'s own licences are listed at the end.', '',
          'This file is generated by `%stests/test_third_party_notices.py` with `--write`.' % CV,
          'The same script\'s tests fail when a Pi-derived file has no licence beside it or is missing here.', '',
          '## 1. Raspberry Pi 5 3D model (Raspberry Pi Ltd, MIT licence)', '',
          '- Source: the official Raspberry Pi 5 STEP model, document RP-010083-CA-1 ("No Graphics small file"):',
          '  <%s>' % url,
          '- SHA-256 of the source STEP inside that archive: `%s`.' % sha,
          '  It is recorded in `%sofficial_pi5_csi.py` and in each variant manifest. The archive itself is not stored here.' % CV,
          '- The manufacturer\'s licence file is kept unchanged at `%s`' % VENDOR_LICENSE,
          '  (SHA-256 `%s`; build receipts bind these exact bytes).' % VENDOR_LICENSE_SHA256,
          '- Every folder that holds Pi geometry has a copy of that licence: the original `LICENSE.txt`, or',
          '  `%s` (the same text with LF line endings). A copy covers only the Pi-derived files listed' % COPY_NAME,
          '  for its folder, not the project\'s own parts stored next to them.',
          '- Renders and guide pages that show the assembled camera also depict this geometry. This notice covers them.', '',
          '| Folder | Licence file | Pi-derived files |', '|---|---|---|']
    L += rows
    L += ['', '### Licence text (verbatim from the manufacturer\'s LICENSE.txt)', '', '```text', licence_text, '```', '',
          '## 2. DejaVu fonts', '',
          'Used to engrave text on printed parts and to set text in rendered guide pages. Generated PDFs may embed',
          'subsets of these fonts. The licence (Bitstream Vera terms, with DejaVu changes in the public domain) is in the',
          'file named next to each font.', '']
    L += font_lines
    L += ['', '## 3. The project\'s own material', '',
          '- `tools/`: MIT licence, see `tools/LICENSE`.',
          '- `software/gs8-camera-evf/`: MIT licence, see `software/gs8-camera-evf/LICENSE`.',
          '- Individual files with an `SPDX-License-Identifier: MIT` header: MIT licence.',
          '- No licence has been chosen yet for the remaining CAD models and documents. That choice is open with the',
          '  project owner (review item VN-13). Until it is made, only the items above grant any rights.', '']
    return '\n'.join(L)


def write():
    vendor = lf((REPO / VENDOR_LICENSE).read_bytes())
    for folder in sorted({str(PurePosixPath(p).parent) for p in pi_derived()}):
        if licence_for(folder) is None:
            (REPO / folder / COPY_NAME).write_bytes(vendor)
            print('wrote', folder + '/' + COPY_NAME)
    (REPO / NOTICE).write_bytes(generate_notice().encode('utf-8'))
    print('wrote', NOTICE)


class ThirdPartyNotices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = present_paths()
        cls.derived = pi_derived(cls.paths)
        cls.notice = (REPO / NOTICE).read_text(encoding='utf-8') if (REPO / NOTICE).exists() else ''

    def test_vendor_licence_bytes_unchanged(self):
        data = (REPO / VENDOR_LICENSE).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), VENDOR_LICENSE_SHA256)
        self.assertIn(b'Copyright (c) 2026 Raspberry Pi Ltd', data)

    def test_derived_set_is_found(self):
        # Fixture: the rule must find the files the review counted (VN-13), so it cannot silently go blind.
        names = sorted(PurePosixPath(p).name for p in self.derived)
        self.assertGreaterEqual(names.count('pi5.step'), 3, names)
        self.assertGreaterEqual(names.count('assembly.step'), 3, names)
        self.assertIn('pi5-corrected.step', names)
        self.assertGreaterEqual(sum(n.endswith('-native.step') for n in names), 7, names)

    def test_every_pi_derived_file_has_licence_beside_it(self):
        missing = sorted({str(PurePosixPath(p).parent) for p in self.derived
                          if licence_for(str(PurePosixPath(p).parent)) is None})
        self.assertEqual(missing, [], 'Pi-derived folders without the Raspberry Pi licence; run --write')

    def test_notice_names_every_derived_file_and_copy(self):
        self.assertTrue(self.notice, NOTICE + ' missing')
        for p in sorted(self.derived):
            folder, name = str(PurePosixPath(p).parent), PurePosixPath(p).name
            self.assertIn('`%s/`' % folder, self.notice, p)
            self.assertIn('`%s`' % name, self.notice, p)

    def test_notice_carries_licence_text_and_source(self):
        url, sha = source_constants()
        self.assertIn(url, self.notice)
        self.assertIn(sha, self.notice)
        for line in lf((REPO / VENDOR_LICENSE).read_bytes()).decode('utf-8').split('\n'):
            if line.strip():
                self.assertIn(line, self.notice)

    def test_notice_paths_exist(self):
        known = set(self.paths)
        for ref in re.findall(r'`([^`\s]+/[^`\s]*)`', self.notice):
            if ref.endswith('/'):
                self.assertTrue((REPO / ref).is_dir(), ref)
            elif '.' in PurePosixPath(ref).name:
                self.assertTrue(ref in known or (REPO / ref).exists(), ref)

    def test_notice_is_current(self):
        self.assertEqual(self.notice, generate_notice(self.derived, self.paths), 'stale notice; run --write')

    def test_fonts_have_licence(self):
        for f in fonts(self.paths):
            lic = str(PurePosixPath(f).parent) + '/LICENSE-DejaVu.txt'
            self.assertTrue((REPO / lic).exists(), f)
            self.assertIn('`%s`' % f, self.notice)

    def test_rule_flags_a_planted_derived_file(self):
        # Regression fixture: a new variant folder with a Pi part and no licence must be reported.
        fake = CV + 'out/zz-fixture-variant/step/pi5.step'
        got = pi_derived(self.paths + [fake])
        self.assertIn(fake, got)
        self.assertIsNone(licence_for(str(PurePosixPath(fake).parent)))


if __name__ == '__main__':
    if '--write' in sys.argv:
        write()
        sys.exit(0)
    unittest.main(verbosity=2)
