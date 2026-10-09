import subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
for view in sys.argv[1:] or ['hero']:
 subprocess.run(['blender','-b','-t','4','-P',str(p/'render_review.py'),'--','--assets',str(p/'out/compact-kowa_lm6hc/meshes'),'--out',str(p/'out/compact-kowa_lm6hc/renders'),'--view',view,'--samples','32','--revision','VERTICAL REVIEW CANDIDATE'],check=True)
