"""Isolated deeper-tenon study; unchanged r7 catch thresholds and displacement cases."""
import sys, json, hashlib, argparse
from pathlib import Path
CV = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(CV), str(CV.parent)]
import cadquery as cq
import model as M
import checks as CK
import steps as ST
import j7_collar_checks as J
from cv_io import read_text, write_text
p=argparse.ArgumentParser();p.add_argument('--height',type=float,default=4.8);p.add_argument('--sample',type=float);p.add_argument('--case');a=p.parse_args()
if a.sample is not None and not M.L.CAM['s_range'][0] <= a.sample <= M.L.CAM['s_range'][1]:
    p.error('sample must be inside the declared BFAR range')
folder=CV/'out/compact-kowa_lm6hc'
meta=json.loads(read_text(folder/'manifest.json'))
rows={r['id']:r for r in meta['rows']}
shapes={k:cq.importers.importStep(str(folder/'step'/f'{k}.step')).val() for k in rows}
M.TAB_CATCH_TENON=dict(M.TAB_CATCH_TENON,h=a.height)
M.TAB_CATCH_CEILING_TOP=max(M.TAB_CATCH_CEILING_TOP,M.TAB_CATCH_SPLIT_Z+a.height+M.TAB_CATCH_POCKET_CLEAR['z']+1.6)
if a.case:
    J.STUB_CASES=tuple(c for c in J.STUB_CASES if c[0]==a.case)
    if not J.STUB_CASES:p.error('unknown case')
for addition in M.tab_catch_split()['adds']:
    shapes['tub']=shapes['tub'].fuse(addition).clean()
rr=J.r7_rows(shapes,rows)
with J.candidate_layout('kowa_lm6hc') as L:
    result=J.roll_catch_stub_rows(L,rr,shapes,CK,ST,s_values=None if a.sample is None else [a.sample])
    stock,stub=M.tub_print_parts(shapes['tub'])
receipt=dict(height_mm=a.height,ceiling_floor_mm=M.TAB_CATCH_CEILING_TOP-M.TAB_CATCH_SPLIT_Z-a.height-M.TAB_CATCH_POCKET_CLEAR['z'],
             baseline_manifest_sha256=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
             stock_valid=stock.isValid(),stub_valid=stub.isValid(),rows=[dict(category=c,id=i,**r) for c,i,r in result])
target=Path(__file__).with_name('catch-h%g%s%s.json'%(a.height,'' if a.sample is None else '-sample',('-'+a.case) if a.case else ''))
write_text(target,json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(output=str(target),height=a.height,counts={s:sum(r['status']==s for _,_,r in result) for s in ('pass','fail','info')},failures=[r for _,_,r in result if r['status']=='fail'])),flush=True)
