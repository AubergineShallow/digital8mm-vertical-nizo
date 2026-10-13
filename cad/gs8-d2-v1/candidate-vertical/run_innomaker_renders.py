"""Run conditional fork illustrations. Invoke through run_locked.py."""
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
OUT=HERE/'innomaker/out/compact-kowa_lm6hc'
for view in ('hero','optics'):
    subprocess.run(['blender','-b','-t','4','--python',str(HERE/'render_innomaker.py'),'--','--assets',str(OUT/'meshes'),'--out',str(OUT/'renders'),'--view',view,'--samples','32','--revision','Innomaker recovered / header-aware HOLD'],check=True)
