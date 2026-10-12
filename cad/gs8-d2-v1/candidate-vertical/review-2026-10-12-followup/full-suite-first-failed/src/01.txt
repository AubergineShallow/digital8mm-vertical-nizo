# SPDX-License-Identifier: MIT
"""Run every candidate test file in an isolated interpreter under one outer CAD lock."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
CV=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CV))
from cv_io import write_text,open_text,relpath_posix,child_env
O=Path(__file__).resolve().parent/'full-suite';O.mkdir(exist_ok=True)
files=sorted(list((CV/'tests').glob('test_*.py'))+[Path(__file__).with_name('test_package_review.py')])
dependency_files=sorted(set(files+list((CV/'tests').glob('*.py'))+[Path(__file__).resolve(),Path(__file__).with_name('package_review.py')]))
initial={relpath_posix(p,CV):hashlib.sha256(p.read_bytes()).hexdigest() for p in dependency_files}
rows=[]
for p in files:
 start=time.time();log=O/(p.stem+'.txt');print(p.name,'starting',flush=True)
 with open_text(log,'w') as f:r=subprocess.run([sys.executable,str(p)],stdout=f,stderr=subprocess.STDOUT,env=child_env())
 counts=re.findall(r'Ran (\d+) tests?',log.read_text(encoding='utf-8',errors='replace'))
 cases=int(counts[-1]) if len(counts)==1 else None
 valid_count=cases is not None and cases>0
 rows.append(dict(status='pass' if r.returncode==0 and valid_count else 'fail',reported_nonempty_test_run=valid_count,test_cases_run=cases,test=relpath_posix(p,CV),source_sha256=initial[relpath_posix(p,CV)],exit_code=r.returncode,seconds=round(time.time()-start,2),log=relpath_posix(log,CV),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
 stable=all(hashlib.sha256(p.read_bytes()).hexdigest()==initial[relpath_posix(p,CV)] for p in dependency_files)
 result=dict(scope='All candidate tests/test_*.py files plus follow-up packager tests, separate processes under one outer run_locked.py lock',tests=len(files),completed=len(rows),test_cases_run=sum(r['test_cases_run'] or 0 for r in rows),sources_stable=stable,test_source_sha256=initial,passed=sum(r['status']=='pass' for r in rows),failed=sum(r['status']!='pass' for r in rows),rows=rows)
 write_text(O/'receipt.json',json.dumps(result,indent=2)+'\n');print(p.name,'exit',r.returncode,flush=True)
 if not stable:raise SystemExit('Test sources changed during suite; receipt is invalid')
raise SystemExit(0 if all(r['status']=='pass' for r in rows) else 1)
