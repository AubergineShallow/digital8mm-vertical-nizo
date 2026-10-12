"""Serialized Oct12 checks. Every exit code is recorded; failures remain failures."""
import sys, subprocess, json, hashlib, time, argparse
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P))
from cv_io import child_env, open_text, write_text
out=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('prelude','checks','all'),default='all');parser.add_argument('--job')
parser.add_argument('--remaining-variants',action='store_true',help='Run alternate non-rigid checks and comparison after separately recorded full rigid audits')
opts=parser.parse_args()
jobs=[
 ('plenum',['verify_shadow_plenum.py']),
 ('outlet',['verify_shadow_outlet_context.py']),
 ('coupons',['make_shadow_plenum_coupon.py']),
 ('structure',['structural-review/update_concealed_vent_structure.py']),
 ('structure_check',['structural-review/update_concealed_vent_structure.py','--check']),
 ('primary_checks',['run_shadow_checks.py'])]
for variant in ('compact-fujinon_hf6xa','original-kowa_lm6hc'):
    for label,script in (('mesh','verify_print_meshes.py'),('print','verify_print_checks.py'),
                         ('rigid','verify_candidate.py'),('scope','verify_check_scope.py')):
        jobs.append((variant+'-'+label,[script,'--variant',variant]))
    jobs.extend([(variant+'-plenum',['verify_shadow_plenum.py','--out',str(P/'out'/variant)]),
                 (variant+'-outlet',['verify_shadow_outlet_context.py','--out',str(P/'out'/variant)]),
                 (variant+'-void',['measure_volume.py',variant])])
jobs.append(('comparison',['measure_comparison.py']))
if opts.phase=='prelude':jobs=jobs[:5]
elif opts.phase=='checks':jobs=jobs[5:]
if opts.remaining_variants:
    if opts.phase != 'checks' or opts.job:parser.error('--remaining-variants requires --phase checks and no --job')
    jobs=[j for j in jobs if j[0]!='primary_checks' and not j[0].endswith('-rigid')]
if opts.job:
    jobs=[j for j in jobs if j[0]==opts.job]
    if not jobs:parser.error('unknown job in selected phase')
records=[]
primary_aggregate_exit=0
hashes={v:hashlib.sha256((P/'out'/v/'manifest.json').read_bytes()).hexdigest()
        for v in ('compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc')}
for label,args in jobs:
    print(label,'starting',time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),flush=True)
    log=out/(label+'-validation.log')
    with open_text(log,'w') as f:
        r=subprocess.run([sys.executable,str(P/args[0])]+args[1:],stdout=f,stderr=subprocess.STDOUT,env=child_env())
    record=dict(check=label,exit_code=r.returncode,log=log.name)
    records.append(record)
    assert all(hashlib.sha256((P/'out'/v/'manifest.json').read_bytes()).hexdigest()==h for v,h in hashes.items())
    write_text(out/('validation-run-'+(opts.job or opts.phase)+'.json'),json.dumps(dict(physical_qualified=False,manifest_sha256=hashes,checks=records),indent=2)+'\n')
    if label == 'primary_checks':
        # Keep the batch process result verbatim. Its inherited zero exit does
        # not imply every recorded child check passed.
        write_text(out/'validation-run-primary_checks.json',json.dumps(dict(physical_qualified=False,manifest_sha256=hashes,checks=[record]),indent=2)+'\n')
        summary=subprocess.run([sys.executable,str(out/'aggregate_status.py')],env=child_env())
        primary_aggregate_exit=summary.returncode
    print(json.dumps(record),flush=True)
raise SystemExit(bool(primary_aggregate_exit or any(r['exit_code'] for r in records)))
