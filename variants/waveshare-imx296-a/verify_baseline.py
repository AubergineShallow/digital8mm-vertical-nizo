# SPDX-License-Identifier: MIT
"""Verify unchanged baseline constraints; never certify the new camera's fit."""
from pathlib import Path
import hashlib
import json
from camera_profile import ROOT


def verify(repo=None):
    repo=Path(repo or ROOT.parents[1])
    expected=json.loads((ROOT/'review/baseline-constraints.json').read_text(encoding='utf-8'))
    mismatches=[]
    for name,digest in expected['files'].items():
        path=repo/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            mismatches.append(name)
    return {'baseline_constraints_unchanged':not mismatches,'mismatches':mismatches,
            'physical_release':False,'camera_fit_result':'NOT TESTED'}


if __name__=='__main__':
    result=verify()
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['baseline_constraints_unchanged'] else 1)
