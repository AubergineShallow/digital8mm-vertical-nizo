# SPDX-License-Identifier: MIT
"""Save source/trial recovery material while verification is unfinished; never a final review package."""
import subprocess,json,hashlib,zipfile
from pathlib import Path
C=Path(__file__).resolve().parents[1];R=C.parents[2]
Z=R.parent/'D2-f970-followup-work-in-progress.zip'
paths=set(subprocess.check_output(['git','diff','--name-only','-z'],cwd=R).decode().split('\0'))
paths.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=R).decode().split('\0'))
allowed={'.py','.md','.json','.txt','.csv','.lock'}
data={n:(R/n).read_bytes() for n in sorted(paths) if n and (R/n).is_file() and (R/n).suffix in allowed and '__pycache__' not in n}
for v in ('compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc'):
 p=C/'out'/v/'manifest.json';data[p.relative_to(R).as_posix()]=p.read_bytes()
text='WORK IN PROGRESS, NOT FINAL ACCEPTANCE. Baseline f9704ac03de8938dfafdb52e22e63d098287c3c6; branch review/vn-catch-qt-cloud-20261012. All three geometry exports complete. Full audits and a later strengthened harness rerun are pending/running; reports and guide may still be stale. This is source/trial recovery material, not a standalone checkout. Preserve all physical holds and the failed QT installed-family rule. No push or purchased-part change.\n'
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,9) as z:
 z.writestr('README-WORK-IN-PROGRESS.txt',text)
 z.writestr('SOURCE-SHA256.json',json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in data.items()},indent=2))
 z.writestr('tracked-changes.patch',subprocess.check_output(['git','diff','--no-ext-diff'],cwd=R))
 for n,b in data.items():z.writestr(n,b)
with zipfile.ZipFile(Z) as z:assert z.testzip() is None
print(json.dumps({'files':len(data),'bytes':Z.stat().st_size,'sha256':hashlib.sha256(Z.read_bytes()).hexdigest()}))
