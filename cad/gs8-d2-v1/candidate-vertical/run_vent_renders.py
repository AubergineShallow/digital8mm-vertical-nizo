from pathlib import Path
import subprocess,argparse
P=Path(__file__).resolve().parent;D=P/'out/compact-kowa_lm6hc'
ap=argparse.ArgumentParser();ap.add_argument('--reference-assets',type=Path,required=True,help='Recovered export18 mesh directory');args=ap.parse_args();R=args.reference_assets.parent
for view in ['hero','rear','vent_side','vent_front']:
 subprocess.run(['blender','-b','-t','4','--python',str(P/'render_review.py'),'--','--assets',str(D/'meshes'),'--out',str(D/'renders'),'--view',view,'--samples','48','--revision','Concealed-channel review candidate'],check=True)
for view in ['vent_side','vent_front']:
 subprocess.run(['blender','-b','-t','4','--python',str(P/'render_review.py'),'--','--assets',str(R/'meshes'),'--out',str(P/'vent-study/reviewed-export18-renders'),'--view',view,'--samples','48','--revision','Reviewed export18 reference'],check=True)
