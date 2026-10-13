# SPDX-License-Identifier: MIT
"""Write the review hold register; exit 2 intentionally while release is blocked."""
import argparse
import json
from pathlib import Path
from camera_profile import ROOT, load_profile, release_status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'review/status.json')
    args = parser.parse_args()
    result = release_status(load_profile())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Bytes, so the record keeps LF line endings on Windows too (repository rule: LF, '* -text').
    args.out.write_bytes((json.dumps(result, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(result, indent=2))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
