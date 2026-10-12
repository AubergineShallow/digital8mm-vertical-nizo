"""Record the performed twelve-image visual review; never infer physical fit."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
F=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
variants=('compact-kowa_lm6hc','compact-fujinon_hf6xa','original-kowa_lm6hc')
views=('hero','rear','vent_side','vent_front')
run=json.loads((F/'render-run.json').read_text(encoding='utf-8'))
assert {(r['variant'],r['view']) for r in run['checks']}=={(v,w) for v in variants for w in views}
assert len(run['checks'])==12
images={f'out/{v}/renders/{w}.png':sha(C/'out'/v/'renders'/f'{w}.png') for v in variants for w in views}
manifest={v:sha(C/'out'/v/'manifest.json') for v in variants}
findings=['All twelve rendered images were visually inspected in three four-view contact sheets. Hero/rear views show complete camera silhouettes and distinguish the two lenses and longer original-storage body.', 'Side/front views intentionally crop peripheral lens/grip context to show the concealed channels and separate CSI service opening. Front/rear edge mouths remain visible; broad cooler sides remain planar.', 'Captions and physical-hold/proxy disclaimers are present and unclipped. Intended finish is illustrative, not a manufacturing or thermal qualification. No new visual geometry defect identified.']
qa={'status':'pass','images_inspected':12,'physical_qualified':False,'render_run_sha256':sha(F/'render-run.json'),'manifest_sha256':manifest,'images':images,'findings':findings,'recorder_sha256':sha(Path(__file__))}
q=F/'render-visual-review.json';q.write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8',newline='\n')
archive=F/'prior-render-receipts';archive.mkdir(exist_ok=True)
for v in variants:
 d=C/'out'/v/'renders';p=d/'receipt.json'
 if p.exists():
  a=archive/f'{v}.json';assert not a.exists();a.write_bytes(p.read_bytes())
 receipt={'mechanical_manifest_sha256':manifest[v],'renderer_sha256':sha(C/'render_review.py'),'files':{w+'.png':sha(d/(w+'.png')) for w in views},'per_view_receipt_sha256':{w+'-receipt.json':sha(d/(w+'-receipt.json')) for w in views},'visual_review_receipt':'review-2026-10-12-followup/render-visual-review.json','visual_review_receipt_sha256':sha(q),'visual_review':findings,'physical_qualified':False}
 p.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(sha(q))
