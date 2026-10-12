import sys,os,json,copy,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(P),str(P.parent)]
from cv_io import read_text,write_text
# Reuse the unchanged exact-sweep implementation without executing its full report writer.
ns={'__file__':str(P/'verify_harness_checks.py'),'__name__':'study_exact'}
sys.argv=[str(P/'verify_harness_checks.py')]
exec(compile(read_text(P/'verify_harness_checks.py').split('res = HR.run_all')[0],ns['__file__'],'exec'),ns)
H,R,HR,ST=map(ns.get,['H','R','HR','ST']); exact=ns['exact_hits'];mp=next(m for m in HR.MATE_POSES if m['id']=='qt_enc')
from cv_io import read_text, write_text
import hashlib
fl=copy.deepcopy(H['free_leads']['qt_enc'])
r=HR.free_lead_eval(H,mp,fl,R.rounded_path,ST,hits=exact)
old=copy.deepcopy(fl)
old['knots']=[[-45.445,-23.4,37.],[-45.445,-23.4,43.1],[-59.7,-18.9,55.2],[-45.5,-6.3,58.],[-46.,8.,68.8],[-88.7,74.8,77.],[-72.,74.8,77.]]
old_r=HR.free_lead_eval(H,mp,old,R.rounded_path,ST,hits=exact)
res=dict(scope='Scoped QT panel-prop static exact sweep on bound baseline STEP inputs. No continuous deformation, physical material, QT splice/core packing or actual CSI access qualification.',
    manifest_sha256=ns['manifest_sha'],source_sha256={q:hashlib.sha256((P/q).read_bytes()).hexdigest() for q in ('signal_routes.py','harness_rules.py','verify_harness_checks.py','hdmi_routes.py')},
    current=r,negative_control_previous_route=old_r,
    installed_storage_scope='Current stored family has a separate exact study; this script checks the propped free route only.',
    pass_scoped=not r['problems'] and 'pi5' in old_r['hits'])
write_text(Path(__file__).with_name('qt-free-lead-check.json'),json.dumps(res,indent=2)+'\n')
print(json.dumps({k:v for k,v in res.items() if k not in ('current','negative_control_previous_route')},indent=2),flush=True)
print('current',r['hits'],r['slack_mm'],'old',old_r['hits'],flush=True)
raise SystemExit(0 if res['pass_scoped'] else 1)
