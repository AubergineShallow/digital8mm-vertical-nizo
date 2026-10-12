# SPDX-License-Identifier: MIT
"""Cross-platform zero serialization does not relax nonzero engineering values."""
import sys,unittest
from pathlib import Path
CV=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(CV),str(CV/'structural-review')]
from update_concealed_vent_structure import canonical_zero

class StructuralZero(unittest.TestCase):
    def test_occ_numerical_zero_is_canonical(self):
        self.assertEqual(canonical_zero({'a':[1.67e-16,-1.69e-16,0.0]}),{'a':[0.0,0.0,0.0]})
    def test_threshold_and_engineering_values_are_unchanged(self):
        for v in [1e-12,-1e-12,1e-10,.1,.3,1.6,1.374777]:
            self.assertEqual(canonical_zero(v),v)
    def test_identity_strings_and_booleans_are_exact(self):
        value={'physical_qualified':False,'hash':'abc','count':3,'tolerance':'1e-16'}
        self.assertEqual(canonical_zero(value),value)
        self.assertIs(canonical_zero(True),True)
if __name__=='__main__':unittest.main()
