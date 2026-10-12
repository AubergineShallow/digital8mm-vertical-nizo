# SPDX-License-Identifier: MIT
"""Bound production adhesive-escape geometry, including rejected overshoot/fill controls."""
import hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
CV=Path(__file__).resolve().parents[1];sys.path[:0]=[str(CV),str(CV.parent)]
import cadquery as cq
import model as M
import verify_print_checks as VPC
from cv_io import read_text

class CatchVent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out=CV/'out/compact-kowa_lm6hc';m=json.loads(read_text(out/'manifest.json'))
        expected=m['sources']['candidate-vertical/model.py']
        if hashlib.sha256((CV/'model.py').read_bytes()).hexdigest()!=expected:
            raise AssertionError('Export the changed catch geometry before its production vent tests')
        shapes=VPC.step_shapes(out,m,['tub','tab_catch_insert'])
        cls.stock=VPC.tub_stock(shapes['tub'],out,m);cls.insert=shapes['tab_catch_insert']
    def test_production_escape_path_and_access(self):
        rows=VPC.catch_joint_manufacturing_rows(self.stock,self.insert)
        self.assertEqual(len(rows),5)
        self.assertTrue(all(r['status']=='pass' for r in rows),rows)
    def test_joint_plane_overshoot_is_rejected(self):
        sp=M.tab_catch_split();b=sp['vent'].BoundingBox();zs=M.TAB_CATCH_SPLIT_Z
        bad=M.box(b.xmin,b.xmax,b.ymin,b.ymax,zs-.01,zs+.01)
        changed=dict(sp,vent=sp['vent'].fuse(bad).clean())
        with patch.object(M,'tab_catch_split',return_value=changed):
            rows=VPC.catch_joint_manufacturing_rows(self.stock,self.insert)
        self.assertEqual(next(r for r in rows if r['id']=='bonded_joint_insert_uncut_by_vent')['status'],'fail')
    def test_filled_groove_is_rejected(self):
        blocked=self.stock.fuse(M.tab_catch_split()['vent']).clean()
        rows=VPC.catch_joint_manufacturing_rows(blocked,self.insert)
        self.assertEqual(next(r for r in rows if r['id']=='bonded_joint_vent_empty')['status'],'fail')
if __name__=='__main__':unittest.main()
