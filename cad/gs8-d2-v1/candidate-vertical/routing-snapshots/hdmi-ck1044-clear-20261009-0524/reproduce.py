"""Reproduce geometry from archived math only, without live route dependencies."""
import ast, hashlib, importlib.util, json, math, sys, types
from pathlib import Path
P=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((P/'manifest.json').read_text())
for name,info in m['files'].items():
 if digest(P/name)!=info['sha256']:raise ValueError('Frozen file changed: '+name)
required={'B','center','hull','overlap','obstacle_overlap','vsub','vadd','vmul','norm','unit','dot','cross','rounded_path'}
tree=ast.parse((P/'source-routes.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in required]
assert len(nodes)==len(required)
R=types.ModuleType('routes');R.math=math;R.AXES='xyz'
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(P/'source-routes.py'),'exec'),R.__dict__)
sys.modules['routes']=R
spec=importlib.util.spec_from_file_location('frozen_hdmi',P/'hdmi300.py');H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
d=json.loads((P/'input.json').read_text());checks=[]
for key,lift,drop in [('hdmi_installed',0,0),('hdmi_premate',0,6),('hdmi_both_unplugged',6,6)]:
 shape=H.compact_300_service(lift,drop,())
 equal=shape==d[key]
 if not equal:raise ValueError('Geometry differs for '+key)
 checks.append(dict(state=key,identical=True,cells=len(shape['segments']),material_mm=shape['routed_length_mm'],
                    fold_radius_mm=shape['fold_radius_mm'],post_radius_mm=shape['explicit_slack_loops'][0]['radius_mm'],
                    natural_u_radius_mm=shape['explicit_slack_loops'][0]['initial_u_radius']))
for row in json.loads((P/'sampled-50-poses.json').read_text()):
 shape=H.compact_300_service(row['lift_mm'],row['drop_mm'],())
 assert shape['routed_length_mm']==row['length_mm']==300
 assert shape['explicit_slack_loops'][0]==row['loop']
 assert not shape['wall_overrun_axes']
result=dict(status='pass',checks=checks,sampled_poses=50,archived_math_only=True,
            source_sha256=digest(Path(__file__)),snapshot_input_sha256=digest(P/'input.json'),physical_qualified=False)
(P/'reproduction-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
