"""Render saved candidate meshes, without rebuilding CAD."""
from pathlib import Path
import subprocess,json,hashlib
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc'
m=json.loads((D/'manifest.json').read_text())
for rel,h in m['sources'].items():
 assert hashlib.sha256((P.parent/rel).read_bytes()).hexdigest()==h,('Source-stale meshes',rel)
for view in ['hero','rear','vent_side','vent_front']:
 subprocess.run(['blender','-b','-t','4','--python',str(P/'render_review.py'),'--','--assets',str(D/'meshes'),'--out',str(D/'renders'),'--view',view,'--samples','48','--revision','Concealed shadow-plenum review candidate'],check=True)
