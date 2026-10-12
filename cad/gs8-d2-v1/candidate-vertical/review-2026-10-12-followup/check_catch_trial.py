"""Isolated candidate catch geometry; no release or adhesive qualification."""
import sys,json,hashlib
from pathlib import Path
CV=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(CV),str(CV.parent)]
import model as M
from cv_io import write_text
from export_cache import export_step
with M.JG.trial_layout(M.L,lip=2.4,head=2.4):
 M.collar_setup()
 tub=M.make_tub(158.0)
 stock,stub=M.tub_print_parts(tub)
 sp=M.tab_catch_split()
 export_step(tub,Path(__file__).with_name('tub-trial.step'))
 export_step(stock,Path(__file__).with_name('stock-trial.step'))
 export_step(stub,Path(__file__).with_name('insert-trial.step'))
 r={'source_sha256':hashlib.sha256((CV/'model.py').read_bytes()).hexdigest(),'face_recess_mm':M.TAB_CATCH_FACE_RECESS_MM,'valid':{k:s.isValid() and len(s.Solids())==1 for k,s in [('tub',tub),('stock',stock),('stub',stub)]},'vent_host_overlap_mm3':stock.intersect(sp['vent']).Volume(),'stub_stock_overlap_mm3':stock.intersect(stub).Volume(),'qualification':False}
 write_text(Path(__file__).with_name('trial-geometry.json'),json.dumps(r,indent=2)+'\n')
 print(r,flush=True)
