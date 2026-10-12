# SPDX-License-Identifier: MIT
"""Run the final strengthened harness audit and record its separate execution.

The earlier primary batch receipt stays unchanged as history of that execution.
This run does not rerun or relabel the independent rigid/contact checks.
"""
import ast,hashlib,json,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parents[1];sys.path.insert(0,str(C))
from cv_io import child_env,open_text,read_text,write_text
D=C/'out/compact-kowa_lm6hc';O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=D/'manifest.json';m=json.loads(read_text(manifest));mh=sha(manifest)
inputs={manifest:mh,C/'verify_harness_checks.py':sha(C/'verify_harness_checks.py'),C/'harness_rules.py':sha(C/'harness_rules.py'),C/'steps.py':sha(C/'steps.py')}
inputs.update({C.parent/n:h for n,h in m['sources'].items()})
inputs.update({D/n:h for n,h in m['files'].items()})
assignments=[n for n in ast.parse(read_text(C/'verify_harness_checks.py')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEPENDENCIES' for t in n.targets)]
assert len(assignments)==1,'Harness dependency declaration is not unique'
deps=ast.literal_eval(assignments[0].value)
assert isinstance(deps,list) and deps and all(isinstance(n,str) for n in deps) and len(set(deps))==len(deps)
inputs.update({(C/n).resolve():sha(C/n) for n in deps})
inputs[Path(__file__).resolve()]=sha(Path(__file__))
assert all(p.is_file() and sha(p)==h for p,h in inputs.items()),'Stale input before harness refresh'
old=D/'harness-checks.json';archive=O/'prior-harness-before-full-minimum.json'
if archive.exists():raise RuntimeError('Previous harness refresh archive exists; do not overwrite execution history')
oldbytes=old.read_bytes();archive.write_bytes(oldbytes)
start=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());log=O/'harness-refresh.log'
with open_text(log,'w') as f:
 r=subprocess.run([sys.executable,str(C/'verify_harness_checks.py')],stdout=f,stderr=subprocess.STDOUT,env=child_env())
end=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
assert all(sha(p)==h for p,h in inputs.items()),'Inputs changed during harness refresh'
report=json.loads(read_text(old));counts={k:sum(x.get('status')==k for x in report['checks']) for k in ('pass','fail','info')}
assert report['manifest_sha256']==mh and report['verification_source_sha256']==sha(C/'verify_harness_checks.py')
assert set(report['verification_dependency_sha256'])==set(deps),'Verifier changed its dependency set'
assert all(sha(C/n)==h==inputs[(C/n).resolve()] for n,h in report['verification_dependency_sha256'].items())
assert counts==report['summary'] and r.returncode==int(counts['fail']>0)
receipt=dict(started_utc=start,completed_utc=end,command=['verify_harness_checks.py'],exit_code=r.returncode,
 manifest_sha256=mh,source_sha256=sha(Path(__file__)),report_sha256=sha(old),summary=counts,
 prior_report_archive=archive.relative_to(C).as_posix(),prior_report_sha256=sha(archive),
 input_sha256={p.relative_to(C).as_posix() if p.is_relative_to(C) else '../'+p.relative_to(C.parent).as_posix():h for p,h in inputs.items()},
 log=log.relative_to(C).as_posix(),log_sha256=sha(log),physical_qualified=False,
 declared_dependencies=deps,scope='Separate complete harness rerun after adding installed-scene minimum-member coverage; original primary batch remains an execution record, not overwritten.')
write_text(O/'harness-refresh.json',json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
raise SystemExit(r.returncode)
