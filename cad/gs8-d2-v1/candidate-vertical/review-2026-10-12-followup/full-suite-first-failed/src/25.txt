# SPDX-License-Identifier: MIT
"""Export folder plan: licence copies and the stale-file pre-flight (fixup-1 of FP-01/FP-03).

Run:  run_locked.py -- cad/gs8-d2-v1/candidate-vertical/tests/test_export_plan.py

CAD-free. export_candidate.py refuses an output folder that holds files it would not write. FP-01 added
LICENSE-RaspberryPi.txt to every variant's step/ folder, which made every documented in-place re-export fail
(and the check ran only after the part files had been overwritten). The exporter now writes the licence copies
itself and checks the planned file names before writing. These tests apply the same rule to the real out/
folders, check that a clean --out export carries the licence the third-party notice rule needs, and pin the
order of the pre-flight in the exporter source.
"""
from pathlib import Path, PurePosixPath
import ast
import json
import sys
import tempfile
import unittest

CV = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CV), str(Path(__file__).resolve().parent)]
import export_cache as EC  # noqa: E402
import test_third_party_notices as TPN  # noqa: E402
from _repo_git import CV as CV_REL  # noqa: E402


def manifest(v):
    return json.loads((CV / 'out' / v / 'manifest.json').read_text(encoding='utf-8'))


def plan_for(m):
    return EC.planned_export_files((r['id'], r['kind']) for r in m['rows'])


class ExportPlan(unittest.TestCase):
    def test_real_variant_folders_hold_no_leftovers(self):
        # The defect: step/LICENSE-RaspberryPi.txt was reported as a leftover for all three variants.
        for v in EC.VARIANTS:
            self.assertEqual(EC.leftover_files(CV / 'out' / v, plan_for(manifest(v))), [], v)

    def test_plan_covers_every_file_the_last_export_bound(self):
        for v in EC.VARIANTS:
            m = manifest(v)
            bound = {rel for rel in m['files'] if rel.split('/')[0] in EC.EXPORT_FOLDERS}
            self.assertEqual(sorted(bound - plan_for(m)), [], v)
            extra = plan_for(m) - bound - set(EC.PI_LICENCE_COPIES)   # licences are bound from the next export on
            self.assertEqual(sorted(extra), [], v)

    def test_licence_copies_are_planned_and_match_the_vendor_text(self):
        for rel in EC.PI_LICENCE_COPIES:
            self.assertIn(rel, EC.planned_export_files([]))
        self.assertEqual(EC.licence_bytes(), TPN.lf((TPN.REPO / TPN.VENDOR_LICENSE).read_bytes()))
        self.assertEqual(CV_REL + EC.PI_LICENCE_SOURCE, TPN.VENDOR_LICENSE)
        self.assertEqual(EC.PI_LICENCE_COPY, TPN.COPY_NAME)

    def test_stray_file_is_reported_and_licence_is_not(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            EC.write_licence_copies(out)
            (out / 'step').mkdir(exist_ok=True)
            (out / 'step' / 'pi5.step').write_bytes(b'x')
            (out / 'step' / 'old_part.step').write_bytes(b'x')     # negative control: not in the plan
            (out / 'meshes').mkdir()
            (out / 'meshes' / 'manifest.json').write_bytes(b'{}')  # rewritten by the export, not a leftover
            plan = EC.planned_export_files([('pi5', 'cots')])
            self.assertEqual(EC.leftover_files(out, plan), ['step/old_part.step'])
            self.assertEqual(EC.leftover_files(out, plan | {'step/old_part.step'}), [])

    def test_clean_out_export_meets_the_third_party_notice_rule(self):
        # A fresh --out folder gets exactly the files export_candidate.py writes; every Pi-derived file in it
        # must have the Raspberry Pi licence in its own folder (the rule of test_third_party_notices).
        m = manifest(EC.GUIDE_VARIANT)
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            written = EC.write_licence_copies(out)
            for rel in sorted(plan_for(m) - written) + ['assembly.step']:
                (out / rel).parent.mkdir(parents=True, exist_ok=True)
                (out / rel).write_bytes(b'placeholder')
            fake = CV_REL + 'out/zz-clean-export/'
            paths = [fake + p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()]
            derived = [p for p in paths if TPN._is_pi_derived(p, paths)]
            names = {PurePosixPath(p).name for p in derived}
            self.assertTrue({'pi5.step', 'assembly.step'} <= names, names)
            vendor = TPN.lf((TPN.REPO / TPN.VENDOR_LICENSE).read_bytes())
            for p in derived:
                if p.endswith('.json'):
                    continue   # meshes/*.json are git-ignored caches, never distributed (VN-04)
                folder = out / str(PurePosixPath(p).parent)[len(fake):]
                lic = folder / TPN.COPY_NAME
                self.assertTrue(lic.is_file() and TPN.lf(lic.read_bytes()) == vendor, p)

    def test_exporter_checks_the_plan_before_writing(self):
        src = (CV / 'export_candidate.py').read_text(encoding='utf-8')
        tree = ast.parse(src)
        line = lambda pred: min(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and pred(ast.unparse(n.func)))
        first_write = line(lambda f: f in ('EC.export_step', 'cq.exporters.export', 'EC.write_mesh', 'EC.save_assembly',
                                           'EC.write_licence_copies', 'write_text'))
        self.assertLess(line(lambda f: f == 'EC.planned_export_files'), first_write)
        self.assertLess(line(lambda f: f == 'EC.leftover_files'), first_write)
        self.assertIn('written|=EC.write_licence_copies(out)', src)
        self.assertIn("if written!=planned:raise RuntimeError", src)
        self.assertIn("meta['files'][EC.PI_LICENCE_COPY]=", src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
