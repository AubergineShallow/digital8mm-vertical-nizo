"""Create ordinary, independently extractable review ZIPs; never claim print release."""
from cv_io import read_text, rel_posix, write_text
from pathlib import Path
import argparse, hashlib, json, subprocess, zipfile
P=Path(__file__).resolve().parent
R=P.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root): return [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.log','.zip')]
def build(dest,name,paths,readme,limit=True):
    paths=sorted(set(p for p in paths if p.is_file()))
    hashes={rel_posix(p,R):sha(p) for p in paths}
    zpath=dest/name
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('DELIVERY-README.txt',readme)
        z.writestr('CONTENTS-SHA256.json',json.dumps(hashes,indent=2)+'\n')
        for p in paths:z.write(p,rel_posix(p,R))
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        for n,h in hashes.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    if limit:assert zpath.stat().st_size<14_000_000,(name,zpath.stat().st_size)
    return dict(file=name,bytes=zpath.stat().st_size,sha256=sha(zpath),members=len(paths))
def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--full',action='store_true');o=a.parse_args();o.output.mkdir(parents=True,exist_ok=True)
    manifest=P/'out/compact-kowa_lm6hc/manifest.json';m=json.loads(read_text(manifest))
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True,encoding='utf-8').strip()
    text=f'''D2 concealed-vent review candidate — 2026-10-09\nGit checkpoint: {commit}\nSelected manifest SHA256: {sha(manifest)}\n\nExtract all three ordinary ZIPs into the same folder. They are not split ZIP volumes.\n01 contains source, BOM, review documents and evidence. 02 contains the selected assembled STEP.\n03 contains nine production-part STEP/STL files, separate fit gauge and screening coupons, and visuals.\nThe assembly guide PDF and structural supplement are supplied separately.\nAuthoritative full archive Library identity: libfile_d5f613cf0eec81919686a996032b31f0.\nUse the delivered Library attachment, not a private download URL.\n\nREVIEW ONLY. Not fabrication, energization or complete-service release.\nPossible 35 mm front-mouth roof bridge: slicer and expanded coupon HOLD; support-free printing is not established.\nCooler/Pi source-proxy conflict, actual connector mating, full flexible loom, thermal performance and all 56 inherited physical gates plus M1 remain open.\nScoped clearance results are described in REVIEW.md and current-review-evidence.json.\n\nSource reproduction: clone https://github.com/AubergineShallow/digital8mm.git at d38468e58eb2b02d56743e2e0cfdd8f780818a65, then overlay these files.\nUse REPRODUCE.md and pinned requirements. Large generated Pi cache/mesh files are omitted from the small source set; regenerate with make_corrected_pi.py before CAD export. Official source inputs and licence are included where listed.\nThe full Library archive retains the generated cache, all three variants, detailed history and guide assets.\nNo remote publication is claimed by this package.\n'''
    core=[R/x for x in json.loads(read_text(P/'delivery-core-paths.json'))]+[R/'.gitattributes',R/'.gitignore']
    core += [p for p in files(P) if p.suffix in ('.py','.md','.csv','.json','.txt','.cpp','.c','.h') and 'meshes' not in p.parts and 'history' not in p.parts]
    core += [p for p in files(P/'structural-review') if p.suffix=='.pdf']
    # Original core list includes source STEP inputs; preserve them, omit only generated outputs.
    omitted={'routing-snapshots/hdmi-ck1044-clear-20261009-0524/context.json','routing-snapshots/fps-access-20261009-0402/twenty-one-full-wire-shapes.json','routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json','routing-snapshots/hdmi-ck1044-clear-20261009-0524/input.json'}
    core=[p for p in core if not (p.is_relative_to(P) and rel_posix(p,P) in omitted)]
    text+='\nLarge superseded routing diagnostics are retained only in the full archive; selected routing inputs remain in set 01.\n'
    common=[manifest,P/'README.md',P/'REVIEW.md',P/'out/compact-kowa_lm6hc/current-review-evidence.json']
    out=P/'out/compact-kowa_lm6hc'
    assembled=common+[out/'assembly.step']
    printed=common+list((out/'stl').glob('*'))
    printed += [out/'step'/f"{r['id']}.step" for r in m['rows'] if r['kind']=='printed']
    printed += files(P/'structural-review/coupons')+files(P/'vent-study/shadow-plenum-coupon')
    printed += [out/'renders'/n for n in ('hero.png','rear.png','receipt.json')]
    printed += [P/'vent-study/D2-concealed-vent-comparison.png',P/'vent-study/render-comparison-receipt.json']
    reports=[build(o.output,'D2-shadow-01-source-and-review.zip',core,text),build(o.output,'D2-shadow-02-assembled-CAD.zip',assembled,text),build(o.output,'D2-shadow-03-prints-coupons-and-views.zip',printed,text)]
    if o.full:
        allfiles=[p for p in files(R) if not any(x in {'.git','.tools','.library-upload-20261009'} or x.startswith('.venv') for x in p.parts)]
        reports.append(build(o.output,'D2-concealed-vent-review-package.zip',allfiles,text,False))
    write_text(o.output/'DELIVERY-README.txt',text)
    write_text(o.output/'delivery-manifest.json',json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
