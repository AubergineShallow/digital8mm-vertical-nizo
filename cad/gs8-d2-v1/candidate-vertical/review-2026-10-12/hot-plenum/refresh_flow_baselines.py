"""Recompute three saved-STEP flow baselines after the trial4 export, without relaxing any gate.

Run through run_locked.py (the child verifiers are intentionally not wrapped again).
Every baseline write follows successful unchanged area gates on its exact saved whole-tub STEP.
The source reports preserve the pre-update drift row as diagnostic; the final full verifier must run afterward.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

CV=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(CV))
from cv_io import child_env,open_text,read_text,write_text
import check_scope as CS

D=Path(__file__).resolve().parent
VARIANTS=('compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc')
GATE_TOL=.002
REASON_PREFIX='Corrective review 2026-10-12: trial4 geometric revision and independent sampling correction.'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rd(p):
    return json.loads(read_text(p))

proven=[]
for variant in VARIANTS:
    mp=CV/'out'/variant/'manifest.json'
    m=rd(mp)
    assert 'trial4' in m['ventilation']['revision'], 'Export is not the selected trial4: '+variant
    assert m['sources']['candidate-vertical/vent_geometry.py']==sha(CV/'vent_geometry.py'), 'Geometry source is stale'
    report=D/('check-scope-flow-'+variant+'.json')
    log=D/('check-scope-flow-'+variant+'.log')
    cmd=[sys.executable,str(CV/'verify_check_scope.py'),'--variant',variant,'--categories','area_parity,flow_network','--out',str(report)]
    with open_text(log,'w') as f:
        proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=child_env())
    assert proc.returncode in (0,1), (variant,proc.returncode)
    r=rd(report)
    assert r['manifest_sha256']==sha(mp), 'Manifest changed'
    assert r['verification_source_sha256']==sha(CV/'verify_check_scope.py'), 'Checker source changed'
    rows={(q['category'],q['id']):q for q in r['checks']}
    for ident,need in [('cold_path_min_cut',420.),('hot_path_min_cut',510.)]:
        q=rows[('area_parity',ident)]
        assert q['status']=='pass' and abs(q['wall_ports_mm2']-need)<GATE_TOL, q
        assert q['min_cut_mm2']>=need-GATE_TOL and q['port_face_blocked_mm2']<=GATE_TOL, q
    assert all(q['status']=='pass' for q in r['checks'] if q['category']=='area_parity'), 'An area gate is still failing'
    unexpected=[q for q in r['checks'] if q['status']=='fail' and (q['category'],q['id'])!=('flow_network','baseline_drift')]
    assert not unexpected, unexpected
    baseline=CV/'review-2026-10-10/fp12'/('flow-network-baseline.json' if variant==VARIANTS[0] else 'flow-network-baseline-'+variant+'.json')
    old=rd(baseline)
    assert old['rel_tol']==1e-6, 'Unexpected baseline tolerance'
    elements=rows[('flow_network','model')]['elements']
    network=CS.flow_network(elements)
    values={q['case']:{f:q[f] for f in old['fields']} for q in network}
    reason=(REASON_PREFIX+' Geometry: the front mouth is full 6 mm gap at Z5..49 and outer 2.5 mm gap (Y-34..-31.5) at Z49..58; '
            'the existing Z49 support row is continued as the second 1.2 mm mouth mullion. Skin, envelope, CSI, cooler and 510 mm2 hot wall ports are unchanged. '
            'Sampling: source rib-face interval midpoints now supplement all original planes; this corrects previously missed narrow cold-rear pillar intervals '
            '(the compact isolated body gave 534 mm2 on the old grid versus 522 mm2 at its actual smaller section), not a cold-geometry change. '
            'Saved '+variant+' manifest '+r['manifest_sha256'][:8]+' proves hot path %.6f and cold path %.6f mm2 with the unchanged 0.002 mm2 tolerance. '
            'The front minimum neck is %.2f mm2; cold-rear series minimum is %.2f mm2. '
            'This records a geometric/reporting revision only; the orifice network has no measured fan operating point or thermal qualification.'
            % (rows[('area_parity','hot_path_min_cut')]['min_cut_mm2'],rows[('area_parity','cold_path_min_cut')]['min_cut_mm2'],
               elements['hot_front']['mouth_mm2'],elements['cold_rear']['series_min_mm2']))
    previous=old['previous'] if old.get('reason','').startswith(REASON_PREFIX) else old
    new={k:old[k] for k in ('purpose','fields','rel_tol','variant')}
    new.update(cases=values,manifest_sha256=r['manifest_sha256'],source_report=report.relative_to(CV).as_posix(),
               source_report_sha256=sha(report),verification_source_sha256=r['verification_source_sha256'],reason=reason,previous=previous)
    assert CS.flow_drift(network,new)[0]
    proven.append((baseline,new,dict(variant=variant,manifest_sha256=r['manifest_sha256'],
        hot_min_cut_mm2=rows[('area_parity','hot_path_min_cut')]['min_cut_mm2'],
        cold_min_cut_mm2=rows[('area_parity','cold_path_min_cut')]['min_cut_mm2'],
        hot_branch_effective_mm2=rows[('area_parity','hot_branch_series')]['effective_sum_mm2'],
        elements=elements,baseline=baseline.relative_to(CV).as_posix(),source_report=report.relative_to(CV).as_posix())))
    print(json.dumps(proven[-1][2]),flush=True)

for baseline,new,_ in proven:
    write_text(baseline,json.dumps(new,indent=2)+'\n')
write_text(D/'flow-baseline-refresh.json',json.dumps(dict(physical_qualified=False,rule='Area gates unchanged: cold 420, hot 510, tolerance 0.002 mm2; baseline drift tolerance 1e-6',variants=[r for _,_,r in proven]),indent=2)+'\n')
print('All three flow baselines updated; run final full check-scope reports to bind them.',flush=True)
