#!/usr/bin/env python3
"""Reproducible pictorial review guide. Reads exported meshes, never changes CAD.
Run with repo .venv-cad/bin/python. All arrows are proposed motions unless explicitly checked.
"""
import sys as _cvsys; _cvsys.path.append(str(__import__('pathlib').Path(__file__).resolve().parents[1]))  # candidate-vertical root: cv_io
from cv_io import read_text, rel_posix, write_text
import export_cache as EC  # FP-03: no wall-clock time on pages or in the receipt; invariant PDF
from pathlib import Path
import sys,json,hashlib,math,datetime,argparse,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];CAD=ROOT.parent
sys.path[:0]=[str(CAD/'guide'),str(ROOT)]
import lineart
import software_lineart
lineart._render=software_lineart.render
GUIDE_ID='D2-vertical-concealed-vents-review'
PARSER=argparse.ArgumentParser(description='Render the separate concealed-channel review guide after manifest nomination.')
PARSER.add_argument('--manifest-sha256',required=True,help='Explicitly nominated final mechanical manifest hash.')
ARGS=PARSER.parse_args()
from vent_guide_support import inspect_inputs,draw_plenum_section
VENT_STATE=inspect_inputs(ROOT,ARGS.manifest_sha256)
VENT=VENT_STATE['metadata'];VC=VENT_STATE['constants']
VENT_CHECK_FILE=VENT_STATE['report_path']
VENT_GEOMETRY_PASS=VENT_STATE['geometry_pass']
HARNESS=VENT_STATE['scoped']['harness']['report']
FLOW=VENT_STATE['scoped']['flow']['report']
PRINT=VENT_STATE['scoped']['print']['report']
DROP=next(r for r in HARNESS['checks'] if r['id']=='pigtail_drop')
QT_REACH=next((r for r in HARNESS['checks'] if r['id']=='qt_enc' and r['category']=='mate_reach'), {})
OUT=Path(__file__).parent/'out-concealed-vents';OUT.mkdir(exist_ok=True)
MESH=ROOT/'out/compact-kowa_lm6hc/meshes'
HDMI_SNAPSHOT=ROOT/'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json'
POWER_SNAPSHOT=ROOT/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'
MAN=json.loads(read_text(MESH.parent/'manifest.json'))
PRINT_COUNTS=MAN.get('production_prints', {'assembly_row_count':9, 'piece_count':10})
MAIN_CHECK=json.loads(read_text(MESH.parent/'verification.json'))
MAIN_MATCHED=(MAIN_CHECK.get('manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest() and MAIN_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_candidate.py').read_bytes()).hexdigest())
COOLER_CLASH=next((r for r in MAIN_CHECK.get('checks',[]) if MAIN_MATCHED and r.get('category')=='interference' and r.get('id')=='pi5/cooler' and r.get('status')=='fail'),None)
HDMI_CHECK_FILE=MESH.parent/'hdmi-solid-checks.json'
HDMI_CHECK=json.loads(read_text(HDMI_CHECK_FILE)) if HDMI_CHECK_FILE.exists() else {}
HDMI_MATCHED=((ROOT/'verify_hdmi.py').exists() and HDMI_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_hdmi.py').read_bytes()).hexdigest() and HDMI_CHECK.get('snapshot_sha256')==hashlib.sha256(HDMI_SNAPSHOT.read_bytes()).hexdigest() and HDMI_CHECK.get('mechanical_manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest())
CARRIED_ROWS=[r for r in HDMI_CHECK.get('checks',[]) if r.get('category')=='carried_sweep']
CARRIED_PASS=HDMI_MATCHED and bool(CARRIED_ROWS) and all(r.get('status')=='pass' for r in CARRIED_ROWS)
CARRIED_FAIL=HDMI_MATCHED and any(r.get('category')=='carried_sweep' and r.get('status')=='fail' for r in HDMI_CHECK.get('checks',[]))
MATERIAL_PASS=HDMI_MATCHED and all(any(r.get('category')=='full_ribbon_vs_solids' and r.get('id')==name and r.get('status')=='pass' for r in HDMI_CHECK.get('checks',[])) for name in ('installed','premate'))
CARRIED_OBSTRUCTIONS=', '.join(sorted({h.get('id','head')+' / '+h.get('fixed','solid') for r in HDMI_CHECK.get('checks',[]) if r.get('category')=='carried_sweep' for h in r.get('hits',[])}))
START_HASHES={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'model.py',HDMI_SNAPSHOT,POWER_SNAPSHOT,ROOT/'ASSEMBLY-VERTICAL.md',ROOT/'BOM-VERTICAL.md',MESH.parent/'manifest.json',MESH.parent/'verification.json',Path(__file__),Path(__file__).parent/'software_lineart.py',Path(__file__).parent/'raster.cpp',CAD/'guide/lineart.py']}
for name in ('package_concealed_guide.py','README-CONCEALED-VENTS.md','STEP-REVIEW-CONCEALED-VENTS.md','vent_guide_support.py','STEP-REVIEW.md','run_with_numpy_raster.py','raster_numpy.py','record_post_guide_check.py'):
    p=Path(__file__).parent/name
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (CAD/'ASSEMBLY.md',CAD/'../../electronics/gs8-d2-v1/WIRING.md',CAD/'fonts/DejaVuSans.ttf',CAD/'fonts/DejaVuSans-Bold.ttf'):
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (ROOT/'REVIEW.md',ROOT/'BOM-VERTICAL.csv',ROOT/'WIRING-VERTICAL.md',ROOT/'make_wiring_vertical.py',ROOT/'make_bom_vertical.py',ROOT/'steps.py',ROOT/'wiring_data.py',ROOT/'routes.py',ROOT/'signal_routes.py',ROOT/'harness_rules.py',ROOT/'evidence_rules.py',CAD/'out/build-receipt.json'):
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [v['path'] for v in VENT_STATE['scoped'].values()]+[VENT_STATE['coupons_path'],ROOT/'corrective-2026-10-12/materials-and-ribbons-baseline-evidence.txt']:
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for evidence in VENT_STATE['scoped'].values():
    for field,base in (('verification_dependency_sha256',ROOT),('helper_source_sha256',ROOT),('input_sha256',CAD),('check_sources',CAD),('checked_source_sha256',ROOT)):
        dependencies=evidence['report'].get(field,{})
        if isinstance(dependencies,dict):
            for name in dependencies:
                p=base/name
                START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in [VENT_STATE['catch_path'],VENT_STATE['catch_path'].parent/'README.md']:
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for field,base in (('input_sha256',ROOT),('source_sha256',ROOT),('files',VENT_STATE['catch_path'].parent)):
    for name in VENT_STATE['catch'][field]:
        p=base/name
        START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('tub','panel'):
    p=MESH.parent/'step'/f'{name}.step'
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('microsd-service-dependency.json','wall-probe-context.json'):
    p=MESH.parent/name
    if p.exists():START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (VENT_CHECK_FILE,ROOT/'vent_geometry.py',ROOT/'cv_io.py',ROOT/'export_cache.py',ROOT/'history/reviewed-export18/tub.step',ROOT/'history/reviewed-export18/panel.step'):
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('CONCEALED-VENT-STRUCTURAL.md','concealed-vent-structural.json','update_concealed_vent_structure.py','reference-export18-structural-binding.json'):
    p=ROOT/'structural-review'/name
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'history/reviewed-export18/manifest.json'
START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in list((ROOT/'vent-study').glob('shadow-plenum*/*receipt.json'))+list(ROOT.glob('make_*plenum*coupon*.py')):
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
if HDMI_CHECK_FILE.exists():START_HASHES[str(HDMI_CHECK_FILE)]=hashlib.sha256(HDMI_CHECK_FILE.read_bytes()).hexdigest()
for p in ROOT.glob('verify_*.py'):START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
if POWER_SNAPSHOT.exists():START_HASHES[str(POWER_SNAPSHOT)]=hashlib.sha256(POWER_SNAPSHOT.read_bytes()).hexdigest()
for directory in [HDMI_SNAPSHOT.parent,ROOT/'routing-snapshots/hdmi-export17-selected-20261009-0704']:
    if directory.exists():
        for p in directory.iterdir():
            if p.suffix in ('.json','.md','.txt','.py'):START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
POWER_CHECK_FILE=MESH.parent/'power-service-checks.json'
POWER_CHECK=json.loads(read_text(POWER_CHECK_FILE)) if POWER_CHECK_FILE.exists() else {}
POWER_PASS=(POWER_CHECK.get('source_sha256')==hashlib.sha256((ROOT/'verify_power_service.py').read_bytes()).hexdigest() and POWER_CHECK.get('status')=='pass' and POWER_CHECK.get('snapshot_sha256')==hashlib.sha256(POWER_SNAPSHOT.read_bytes()).hexdigest() and POWER_CHECK.get('manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest())
if POWER_CHECK_FILE.exists():START_HASHES[str(POWER_CHECK_FILE)]=hashlib.sha256(POWER_CHECK_FILE.read_bytes()).hexdigest()
CSI_CHECK_FILE=MESH.parent/'csi-source-tool-checks.json'
CSI_CHECK=json.loads(read_text(CSI_CHECK_FILE)) if CSI_CHECK_FILE.exists() else {}
CSI_MATCHED=((ROOT/'official_pi5_geometry.py').exists() and CSI_CHECK.get('source_helper_sha256')==hashlib.sha256((ROOT/'official_pi5_geometry.py').read_bytes()).hexdigest() and CSI_CHECK.get('mechanical_manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest() and (ROOT/'verify_csi_source.py').exists() and CSI_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_csi_source.py').read_bytes()).hexdigest())
CSI_PASS=CSI_MATCHED and CSI_CHECK.get('declared_rigid_reservation_clear',False)
CSI_OBSTRUCTIONS=', '.join(sorted({h['part'] for row in CSI_CHECK.get('checks',[]) for h in row.get('hits',[])}))
for p in [CSI_CHECK_FILE,ROOT/'verify_csi_source.py']:
    if p.exists():START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
WIRE_CHECK_FILE=MESH.parent/'wire-solid-checks.json'
WIRE_CHECK=json.loads(read_text(WIRE_CHECK_FILE)) if WIRE_CHECK_FILE.exists() else {}
WIRE_SNAPSHOT=next((p for p in (ROOT/'routing-snapshots').glob('*/power*.json') if hashlib.sha256(p.read_bytes()).hexdigest()==WIRE_CHECK.get('snapshot_sha256')),None)
WIRE_MATCHED=(WIRE_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_wire_solids.py').read_bytes()).hexdigest() and WIRE_CHECK.get('helper_source_sha256')==hashlib.sha256((ROOT/'power_geometry.py').read_bytes()).hexdigest() and WIRE_SNAPSHOT is not None and WIRE_CHECK.get('manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest())
WIRE_HITS=sum(len(r.get('hits',[])) for r in WIRE_CHECK.get('rows',[]))
WIRE_CAPTION=('Static wire capsules: '+('clear printed solids; root joints omitted.' if WIRE_CHECK.get('status')=='pass' else str(WIRE_HITS)+' printed-part overlaps. Redesign before closure.') if WIRE_MATCHED else 'Static wire clearance: no current source-bound pass.')
for p in [WIRE_CHECK_FILE,WIRE_SNAPSHOT]:
    if p is not None and p.exists():START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
FPS_INPUT=ROOT/'out/fps-service-study/mated-carry-input.json'
FPS_RECEIPT=ROOT/'out/fps-service-study/fps-final-source-receipt.json'
FPS_READY=FPS_INPUT.exists() and FPS_RECEIPT.exists()
FPS_PASS=False
if FPS_READY:
    fps_receipt=json.loads(read_text(FPS_RECEIPT))
    if hashlib.sha256(FPS_INPUT.read_bytes()).hexdigest()!=fps_receipt['frozen_input']['sha256']:raise RuntimeError('FPS input differs from source receipt')
    for p in [FPS_INPUT,FPS_RECEIPT,ROOT/'FPS-SERVICE-STUDY.md']:
        START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name,digest in fps_receipt.get('verification_reports',{}).items():
        p=FPS_RECEIPT.parent/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise RuntimeError('FPS evidence differs from receipt: '+name)
        START_HASHES[str(p)]=digest
    for key in ('final_fps_check','structural_screen','related_integrated_hdmi_check','related_corrected_head_check'):
        evidence=fps_receipt.get(key,{})
        if evidence.get('path'):
            p=ROOT/evidence['path']
            if hashlib.sha256(p.read_bytes()).hexdigest()!=evidence['sha256']:raise RuntimeError('FPS receipt evidence changed: '+key)
            START_HASHES[str(p)]=evidence['sha256']
    # Preserve the historical frozen-input receipt, but take a current limited
    # material pass only from the separately rerun selected-manifest report.
    FPS_CHECK_FILE=ROOT/'out/fps-service-study/integrated-fps-checks.json'
    if FPS_CHECK_FILE.exists():
        fj=json.loads(read_text(FPS_CHECK_FILE))
        START_HASHES[str(FPS_CHECK_FILE)]=hashlib.sha256(FPS_CHECK_FILE.read_bytes()).hexdigest()
        deps=dict(fj.get('verification_dependency_sha256',{}),**fj.get('frozen_helper_sha256',{}))
        fps_rows=fj.get('static_and_carried_checks',[])
        FPS_PASS=(fj.get('mechanical_manifest_sha256')==ARGS.manifest_sha256
            and fj.get('status')=='geometric_pass_only' and fj.get('physical_qualified') is False
            and fj.get('printed_parts_valid') is True and bool(fps_rows) and all(isinstance(r.get('hits'),list) and not r['hits'] for r in fps_rows)
            and fj.get('input_sha256')==hashlib.sha256(FPS_INPUT.read_bytes()).hexdigest()
            and fj.get('source_sha256')==hashlib.sha256((ROOT/'verify_fps_integrated.py').read_bytes()).hexdigest()
            and bool(deps) and all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in deps.items())
            and bool(fj.get('step_sha256')) and all(MAN['files'].get('step/'+n+'.step')==h for n,h in fj.get('step_sha256',{}).items()))
        for name in deps:
            p=ROOT/name
            START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
POWER_CURRENT=any(r.get('id')=='xt30_pair' and 'frozen21deg' in r.get('source','') for r in MAN['rows'])
SOURCE_MISMATCHES=[name for name,digest in MAN['sources'].items() if (CAD/name).exists() and hashlib.sha256((CAD/name).read_bytes()).hexdigest()!=digest]
for name in MAN['sources']:
    p=CAD/name
    if p.exists():START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in MAN['files'].items():
    if name.startswith('meshes/') and hashlib.sha256((MESH.parent/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Mesh/manifest changed: '+name)
if SOURCE_MISMATCHES:raise RuntimeError('CAD export is behind sources; wait for the selected freeze: '+str(SOURCE_MISMATCHES))
DATA={p.stem:json.loads(read_text(p)) for p in MESH.glob('*.json') if p.stem!='manifest'}
def print_mesh(name):
    path=MESH.parent/'stl'/f'{name}.stl'
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MAN['files'].get('stl/'+name+'.stl'):
        raise RuntimeError('Physical print STL differs from manifest: '+name)
    count=struct.unpack_from('<I',raw,80)[0]
    if len(raw)!=84+50*count:raise RuntimeError('Expected binary export STL: '+name)
    vv=[];ff=[]
    for i in range(count):
        q=struct.unpack_from('<12fH',raw,84+50*i)
        j=len(vv);vv.extend((q[3:6],q[6:9],q[9:12]));ff.append([j,j+1,j+2])
    START_HASHES[str(path)]=hashlib.sha256(raw).hexdigest()
    return {'vertices':vv,'faces':ff}
DATA['print_tub_body']=print_mesh('tub')
DATA['print_tab_catch']=print_mesh('tab_catch_insert')
W,H=1684,1190
INK='#181818';GRAY='#666666';ORANGE='#B23B19';BLUE='#37658A';YELLOW='#FFF0C4'
FONT=CAD/'fonts'
TEXT_PAGES=[]
CURRENT_TEXT=None
pdfmetrics.registerFont(TTFont('GuideSans',ImageFont.truetype(str(FONT/'DejaVuSans.ttf'),16).path))
pdfmetrics.registerFont(TTFont('GuideSansBold',str(FONT/'DejaVuSans-Bold.ttf')))
def f(n,b=False):return ImageFont.truetype(str(FONT/('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf')),n)
def text(d,x,y,s,size=27,b=False,color=INK,width=1480):
    for para in s.split('\n'):
        line=''
        for w in para.split():
            t=(line+' '+w).strip()
            if d.textlength(t,font=f(size,b))>width and line:
                d.text((x,y),line,font=f(size,b),fill=color)
                if CURRENT_TEXT is not None:CURRENT_TEXT.append((x,y,line,size,b))
                y+=int(size*1.38);line=w
            else:line=t
        d.text((x,y),line,font=f(size,b),fill=color)
        if CURRENT_TEXT is not None:CURRENT_TEXT.append((x,y,line,size,b))
        y+=int(size*1.38)
    return y
pages=[]
def page(n,title,sub=''):
    global CURRENT_TEXT
    CURRENT_TEXT=[];TEXT_PAGES.append(CURRENT_TEXT)
    im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
    text(d,50,36,n,46 if len(n)>2 else 58,True);text(d,182,45,title,42,True,width=1430)
    if sub:text(d,184,106,sub,23,color=GRAY,width=1420)
    d.line((50,1120,1634,1120),fill='#BBBBBB',width=2)
    text(d,50,1140,'D2 CONCEALED VENTS  |  COMPACT + KOWA LM6HC  |  '+('UNFROZEN DRAFT' if SOURCE_MISMATCHES else 'REVIEW ONLY'),19,color=GRAY)
    text(d,1360,1140,f'{len(pages)+1:02d}',19,color=GRAY)
    return im,d

def save(im):
    p=OUT/f'page-{len(pages)+1:02d}.png';im.save(p);pages.append(p)
def arrow(d,a,b,color=BLUE,width=7):
    d.line((*a,*b),fill=color,width=width);v=np.array(b)-np.array(a);v=v/max(1,np.linalg.norm(v));s=np.array([-v[1],v[0]])
    pts=[b,tuple(np.array(b)-v*23+s*11),tuple(np.array(b)-v*23-s*11)];d.polygon(pts,fill=color)
def scene(im, ids, news=(), offsets=None, rect=(45,175,1100,715),direction=(1,2,1),arrows=(),labels=()):
    offsets=offsets or {};x,y,w,h=rect;items=[]
    for ident in ids:
        m=DATA[ident];items.append((np.array(m['vertices']),np.array(m['faces']), 'new' if ident in news else 'old',offsets.get(ident,(0,0,0))))
    cam=lineart.fit_camera(direction,items,w,h,margin=1.17)
    img=lineart.render(items,cam)
    # Keep the exported paint-fill faces legible without altering any glyph geometry.
    polys=[]
    for ident,item in zip(ids,items):
        v,faces,style,off=item;mats=DATA[ident].get('materials',['plain']*len(faces))
        colors=np.array([[45,45,45] if m=='paint_black' else [255,255,255] for m in mats],dtype=np.uint8)
        polys.append((lineart._poly(v,faces,colors),off))
    mask,_=software_lineart.render(polys,cam,w,h)
    pixels=np.array(img);pixels[mask[:,:,0]<100]=[55,55,55];img=Image.fromarray(pixels)
    im.paste(img,(x,y));d=ImageDraw.Draw(im)
    def project(p):q=cam.project(p)[0];return (q[0]+x,q[1]+y)
    for a,b in arrows:arrow(d,project(a),project(b))
    for pos,label in labels:
        q=project(pos);d.ellipse((q[0]-21,q[1]-21,q[0]+21,q[1]+21),fill='white',outline=INK,width=2);d.text((q[0],q[1]),label,font=f(23,True),fill=INK,anchor='mm')
    return cam,(x,y)
def note(d,title,body,y=255):
    y=text(d,1190,y,title,29,True,width=430)
    return text(d,1190,y+22,body,25,width=420)
def stop(d,s,y=990):text(d,65,y,'STOP  '+s,25,True,ORANGE,width=1530)
# FP-06: page -> steps.py build operations shown on that page, in page order. tests/test_build_order_docs.py
# checks this literal and the page() order against steps.STEPS without running this builder.
GUIDE_OPS={
  '03':('optics_bench', 'print_inserts'),
  '03v':('print_inserts',),
  '03w':('print_inserts',),
  '03x':('print_inserts',),
  '04':('module_bench',),
  '05':('module_bench',),
  '06':('module_bench',),
  '06b':('module_bench',),
  '06c':('module_bench',),
  '06d':('module_bench',),
  '06e':('module_bench',),
  '06f':('module_bench',),
  '06g':('module_bench',),
  '06h':('panel_bench', 'panel_power_switch'),
  '07':('grip_prep', 'strap_thread'),
  '07b':('tub_on', 'grip_lock'),
  '08':('collar_on', 'collar_screws_start', 'gauge_in', 'collar_tighten', 'gauge_out'),
  '08b':('camera_fpc_mate', 'camera_in'),
  '08c':('s_c4_start', 'lens_in', 'lens_float'),
  '09':('eyepiece_in', 'evf_in'),
  '11':('module_staged', 'carrier_in', 'carrier_screws'),
  '12':('evf_mate',),
  '13':('evf_mate',),
  '15':('evf_mate',),
  '15q':('evf_mate',),
  '16':('panel_prop', 'panel_in', 'panel_screws', 'fps_washer_on', 'fps_nut_on', 'knob_fps_on'),
  '17':('storage_in', 'eyecup_on'),
  '18':('pack_in', 'cap_on')}
import steps as _steps
import evidence_rules as _ER  # fixup-1 (VN-08): inherited-gate count from the r7 build receipt
GATES_OPEN=_ER.inherited_gates(ROOT)['open']
_order=[o['id'] for o in _steps.STEPS];_seen=[op for ops in GUIDE_OPS.values() for op in ops]
if [o for o in _seen if o not in _order] or [_order.index(a) for a in _seen]!=sorted(_order.index(a) for a in _seen) or [o['id'] for o in _steps.STEPS if o['where']=='body' and o['id'] not in _seen]:raise RuntimeError('guide page order differs from steps.py (FP-06)')
BASE=['tub','base_grip','tripod_nut','run_button','p_grip']
OPT=['gs_camera','c_cs_adapter','lens_collar']
EVF=['evf_board','hmx039','foam_pad','eyepiece','eyecup']
EVF_IN=[p for p in EVF if p!='eyecup']  # FP-06: eyecup is fitted in step 7
STACK=['carrier','pi5','cooler','x1203','x1203_kit']
FPS_HARDWARE=[p for p in ('fps_nut','fps_mounting_washer') if p in DATA]
PANEL=['panel','encoder','switch_1824','knob_exp','knob_fps','power_button','power_nut_reserve']+FPS_HARDWARE
FROZEN=json.loads(read_text(HDMI_SNAPSHOT))
R=dict(hdmi_ribbon=FROZEN['hdmi_installed'],hdmi_ribbon_premate=FROZEN['hdmi_premate'],plugs=FROZEN['connectors'],header_housings=FROZEN['header_housings'])
def ribbon_mesh(study):
    vv=[];ff=[]
    for seg in study['segments']:
        start=len(vv);vv.extend(seg['vertices'])
        for quad in ((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)):
            a,b,c,e=[start+j for j in quad];ff.extend([[a,b,c],[a,c,e]])
    return {'vertices':vv,'faces':ff}
DATA['hdmi_strip']=ribbon_mesh(R['hdmi_ribbon'])
DATA['hdmi_premate']=ribbon_mesh(R['hdmi_ribbon_premate'])
DATA['hdmi_both_free']=ribbon_mesh(FROZEN['hdmi_both_unplugged'])
HEADERS=[p['id'] for p in R['header_housings']]
for plug in R['plugs']+R['header_housings']:
    if plug['id'] not in ('p_hdmi_pi','p_hdmi_evf','p_usb_pi') and plug['id'] not in HEADERS:continue
    b=plug['box'];x0,x1=b['x'];y0,y1=b['y'];z0,z1=b['z']
    DATA[plug['id']]={'vertices':[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],'faces':[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]}
def cylinder_mesh(origin,axis,radius,length):
    axis=np.asarray(axis,dtype=float);axis/=np.linalg.norm(axis);u=np.cross(axis,[1,0,0]);u/=np.linalg.norm(u);v=np.cross(axis,u);origin=np.asarray(origin)
    vv=[];ff=[]
    for h in (0,length):
        for i in range(32):vv.append((origin+axis*h+radius*(u*math.cos(i*math.tau/32)+v*math.sin(i*math.tau/32))).tolist())
    for i in range(32):
        j=(i+1)%32;ff.extend([[i,j,i+32],[j,j+32,i+32]])
    for i in range(1,31):ff.extend([[0,i+1,i],[32,32+i,33+i]])
    return {'vertices':vv,'faces':ff}
def tube_mesh(points,radius,sides=12):
    points=np.asarray(points,dtype=float);vv=[];ff=[];last=None
    for i,point in enumerate(points):
        tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)];tangent/=np.linalg.norm(tangent)
        if last is None:
            basis=np.eye(3)[np.argmin(np.abs(tangent))];u=np.cross(tangent,basis)
        else:u=last-tangent*np.dot(last,tangent)
        u/=np.linalg.norm(u);v=np.cross(tangent,u);last=u
        for j in range(sides):vv.append((point+radius*(u*math.cos(j*math.tau/sides)+v*math.sin(j*math.tau/sides))).tolist())
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;c=a+sides;e=b+sides;ff.extend([[a,b,c],[b,e,c]])
    for j in range(1,sides-1):ff.extend([[0,j+1,j],[(len(points)-1)*sides,(len(points)-1)*sides+j,(len(points)-1)*sides+j+1]])
    return {'vertices':vv,'faces':ff}
FPS_WIRES=[]
if FPS_READY:
    fps=json.loads(read_text(FPS_INPUT))
    for part in fps['wire_parts']:
        key='guide_'+part['id'];FPS_WIRES.append(key);DATA[key]=tube_mesh(part['curve']['sampled_centerline'],part['od_mm']/2)
    b=fps['junction']['box'];x0,x1=b['x'];y0,y1=b['y'];z0,z1=b['z']
    DATA['guide_fps_pair']={'vertices':[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],'faces':[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]}
    FPS_WIRES.append('guide_fps_pair')
    for i,z in enumerate((41,55)):
        key='guide_fps_splice_'+str(i);DATA[key]=cylinder_mesh([-103.5,-23.4,z],[0,0,1],1.5,10);FPS_WIRES.append(key)
# Shape sources are frozen with the harness report; these proxy diagrams are not copper cut patterns.
import routes as _guide_routes
_qt_source=_guide_routes.build()['signal_geometry']
QT_MODEL=_qt_source['qt'];QT_FREE=_qt_source['free_leads']['qt_enc']
QT_BRANCH_IDS=[]
for branch in _qt_source['branches']:
    if branch['cable']=='qt':
        key='guide_'+branch['id'];QT_BRANCH_IDS.append(key)
        DATA[key]=tube_mesh(branch['curve']['sampled_centerline'],branch['od_mm']/2)
DATA['guide_qt_stored']=tube_mesh(QT_MODEL['curve']['sampled_centerline'],QT_MODEL['od_mm']/2)
DATA['guide_qt_free']=tube_mesh(QT_FREE['curve']['sampled_centerline'],QT_FREE['od_mm']/2)
CSI_ARROWS=[]
if CSI_MATCHED and CSI_CHECK.get('tool_reservations'):
    tool=CSI_CHECK['tool_reservations'][0];tip=np.array(tool['tip']);back=np.array(tool['axis'])
    DATA['csi_tip_reserve']=cylinder_mesh(tip,back,tool['tip_diameter_mm']/2,tool['tip_length_mm'])
    DATA['csi_shank_reserve']=cylinder_mesh(tip+back*tool['tip_length_mm'],back,tool['shaft_diameter_mm']/2,tool['shaft_length_mm'])
    CSI_ARROWS=[(tip+back*80,tip+back*40)]
# 1
CORE=' x '.join(f'{v:g}' for v in MAN['core_dimensions_mm'])
im,d=page('D2','2026-10-12 corrective assembly review',f"BLOCKED REVIEW | Vertical Pi candidate  |  {CORE} mm core  |  {PRINT_COUNTS['piece_count']} physical prints / {PRINT_COUNTS['assembly_row_count']} CAD rows")
scene(im,BASE+OPT+EVF+STACK+PANEL+['lens','cap','usb_stick'],['panel','lens_collar'],rect=(50,170,1100,820))
note(d,'A sequence to test','Pictures expose fit, insertion and service dependencies.\n\nAmber: new part.\nGrey: already present.\nBlue: proposed motion.\nDashed: hidden part.\n\nThe outer plenum is integral to the tub.\n\nNo physical build is qualified.')
stop(d,'All %d inherited physical gates and M1 remain open. Do not fabricate or energize from this review.'%GATES_OPEN)
save(im)
# 2
im,d=page('00','Disconnect before opening','The J2 button requests power control. It does not isolate the battery.')
scene(im,BASE+OPT+EVF+STACK+PANEL+['lens','pack','cap','xt30_pair'],['pack','cap'],offsets={'cap':(0,0,-60),'pack':(0,0,-45)},arrows=[((-48,0,-48),(-48,0,-100))])
note(d,'Four prerequisites','1  Stop recording; clean shutdown.\n\n2  Remove every external supply.\n\n3  Withdraw pack; part XT30 by housings. Protect contacts.\n\n4  Only then touch internal connectors. Use ESD protection. Charge the pack outside the body.')
stop(d,'XT30 must be reachable with body closed and retention fitted. Fixed tied loops cannot unfold for service.')
save(im)
# 3 printed inventory
im,d=page('01','Count the printed parts','Compact: 10 physical prints in 9 CAD assembly rows. Body and bonded catch stub are separate prints. Gauge / coupons excluded.')
parts=[('tub','1 + 2  Body + bonded stub'),('panel','3  Panel'),('carrier','4  Carrier'),('base_grip','5  Base / grip'),('cap','6  Battery cap'),('eyecup','7  Eyecup'),('knob_exp','8  Exposure knob'),('knob_fps','9  18 / 24 knob'),('lens_collar','10  Lens collar')]
for i,(pid,label) in enumerate(parts):
    x=65+(i%3)*535;y=176+(i//3)*292
    scene(im,[pid],[pid],rect=(x,y,490,226));text(d,x+15,y+231,label,25,True,width=490)
text(d,65,1065,'Tub shown assembled above; separate print pieces on page 03x. Original storage adds one sleeve: 11 physical prints / 10 CAD rows.',22,color=GRAY)
save(im)
# Purchased components in the compact camera, distinct from printed parts and spares.
im,d=page('01b','Identify the purchased assemblies','CAD envelopes. Match actual purchased identities and revisions; each group is one installed assembly.')
kit=[(['pi5'],'A  Raspberry Pi 5'),(['cooler'],'B  Active Cooler envelope'),(['x1203','x1203_kit'],'C  X1203 + kit hardware'),(['gs_camera','c_cs_adapter'],'D  GS camera + C-CS'),(['lens'],'E  Kowa LM6HC lens'),(EVF[:-1],'F  EVF kit (flex not shown)'),(['encoder'],'G  QT encoder'),(['switch_1824'],'H  18 / 24 switch'),(['power_button','power_nut_reserve'],'I  J2 power switch'),(['run_button'],'J  Run button'),(['pack','xt30_pair'],'K  Protected pack + XT30'),(['usb_stick'],'L  Princeton USB SSD')]
for i,(ids,label) in enumerate(kit):
    x=55+(i%4)*411;y=176+(i//4)*267
    scene(im,ids,ids,rect=(x,y,380,210),direction=(1,-2,1) if i<3 else (1,2,1))
    text(d,x+5,y+212,label,21,True,width=390)
text(d,65,1030,'Also identify microSD, camera FPC, HDMI heads + ribbon, EVF feed, QT / switch / run / J2 leads, fuse and insulation.',23,width=1530)
save(im)
# 4 hardware
im,d=page('02','Sort hardware and tools','Counts are installed quantities. Purchased spares are not extra installed hardware.')
rows=[('A','7 x PT 3.0 x 12 PH1','Panel 4  |  carrier 2  |  independent grip lock 1'),('B','3 x M3 x 10 + washers','Collar anchors into 3 short M3 inserts'),('C','1 x M3 x 16 + washer','Collar pinch into 1 long M3 insert'),('D','4 x M2.5 x 5 retained','Upper kit screws; retain 4 original standoffs'),('E','4 x M2.5 x 8 replacements','Lower screws through carrier; bag 4 old M2.5 x 5'),('F','2 x supplied cooler push pins','Included in cooler kit; proxy feet are not fasteners'),('G','1 x tripod nut','Capture in grip before joining the tub')]
for i,(a,b,c) in enumerate(rows):
 y=190+i*117;d.ellipse((65,y,128,y+63),outline=INK,width=3);text(d,86,y+9,a,32,True);text(d,165,y,b,31,True);text(d,165,y+47,c,25,color=GRAY)
text(d,980,190,'TOOLS',29,True,width=600)
text(d,980,250,'T1   PH1 + torque driver\nT2   Iron + correct insert tip\nT3   Solder / flux / wick + heat gun\nT4   Stripper / cutter\nT5   Meter, thermocouple, calipers\nT6   Fine tweezers + smooth pliers\nT7   Deep sockets, saw, file, soft vise\nT8   ESD mat + wrist strap\nT9   Panel prop, shims, rule, gauge\nT10  Bench supply, Pi PSU, charger\nT11  Scope, USB meter, DC load\nT12  Insert-repair pin vise / drills',25,width=610)
stop(d,'Torque and insert process need revised coupons. No threadlocker on ASA. Power-nut deep-socket fit is unmeasured.')
save(im)
# 5
im,d=page('03','Prepare optics and prints','Bench preparation before electronics go inside')
scene(im,['gs_camera','c_cs_adapter','lens','lens_collar'],['lens_collar'],offsets={'lens':(45,0,0),'lens_collar':(22,0,0)},rect=(60,210,1080,700),arrows=[((70,0,60),(35,0,60))])
note(d,'Support the load','Support camera and lens separately. Never react lens torque through PCB or cover.\n\nMeasure back focus and support band. Keep adapter / BFAR witness marks.\n\nBag tripod block after setup. Install inserts before electronics.\n\nKeep the camera socket accessible. Seat the Pi cable end before the cooler (04); mate the camera end just before insertion (08b).')
stop(d,'Review the outer plenum on 03v / 03w plus collar and horizontal-bores supports. Measured optics and M1 remain open.')
save(im)
# Plenum section diagrams explain the source geometry; these are not saved-STEP cutaways.
im,d=page('03v','Inspect the concealed outer plenum','Representative sections. Blue arrows show intended paths. Windowed ribs and mouth lintels omitted; use the saved print geometry.')
text(d,65,177,'COLD BAY  /  INTAKE',28,True,width=730)
text(d,865,177,'HOT BAY  /  EXHAUST',28,True,width=730)
draw_plenum_section(d,text,arrow,65,225,730,385,VENT['outer_skin_mm'],VENT['plenum_gap_mm'],VENT['original_side_wall_mm'],flow_in=True)
draw_plenum_section(d,text,arrow,865,225,730,385,VENT['outer_skin_mm'],VENT['plenum_gap_mm'],VENT['original_side_wall_mm'],flow_in=False)
text(d,65,638,f"Rear + underside perimeter mouths feed the cold bay. Four internal wall slots have {VENT['intake_wall_throat_mm2']:.0f} mm2 nominal total area.",25,width=730)
text(d,65,762,f"Net mouth necks: rear {VENT['cold_rear_mouth_mm2']:.0f} mm2; underside {VENT['cold_bottom_mouth_mm2']:.0f} mm2.",25,width=730)
text(d,865,638,f"Four internal wall slots feed the hot bay: {VENT['exhaust_wall_throat_mm2']:.0f} mm2 nominal total area. Air is intended to leave at front + underside perimeter mouths.",25,width=730)
text(d,865,795,f"Net mouth necks: front {VENT['hot_front_mouth_mm2']:.0f} mm2; underside {VENT['hot_bottom_mouth_mm2']:.0f} mm2.",25,width=730)
text(d,65,912,f"Side skin {VENT['outer_skin_mm']:g} mm + gap {VENT['plenum_gap_mm']:g} mm + original wall {VENT['original_side_wall_mm']:g} mm. Cavity datum stays Y {VENT['inner_side_y_mm']:g}. Broad-side grille is concealed; perimeter mouths remain.",23,width=1530)
stop(d,'CSI is an explicit service aperture. Direct rear/front views expose mouths. No sealed-flow, dust or water rating.')
save(im)
im,d=page('03w','Print and inspect the outer plenum','Do not fit electronics or inserts until the full air path can be inspected and cleaned.')
scene(im,['tub','panel'],['tub','panel'],offsets={'panel':(0,50,0)},rect=(45,180,850,560),direction=(1,-2,.6))
text(d,65,770,'PRINT HOLD: continuous windowed beam lines, pillars, mouth mullions and cold-mouth lintels replace the old post grid. Geometric bridge screens are not slicer or printed-part evidence.',24,True,color=ORANGE,width=805)
text(d,65,920,'Old panel grooves were blind, with 0.2 mm floors. The revised source specifies a plain 2.8 mm skin.',22,width=805)
text(d,960,183,'PRINT AND INSPECT',29,True,width=650)
pose=MAN.get('print_poses',{}).get('tub',{}).get('face_down','unrecorded')
support=VENT['support']
print_steps=[f"1  Tub body STL is {pose}-face down. Stub is a separate print. Review each actual print pose and first roof layer in the slicer.",f"2  Source support: {support['rib_thickness_mm']:g} mm beam lines on pillars; beam-window spans up to {support['window_max_mm']:g} mm. Preserve the declared bridge direction in each roof region.",'3  Qualify three coupons: preliminary region, port/service crop and all-four-mouths crop. Geometry-only results do not establish printing or cleanout.','4  No trapped support. Inspect both full-body bays through their intended mouths; remove every loose particle and reject inaccessible debris.','5  Check all four perimeter mouths and eight inner-wall slots. Recheck printed openings, roof sag and actual handling occlusion before electronics.']
y=245
for body in print_steps:y=text(d,960,y,body,24,width=650)+23
stop(d,'Blocked slots, roof sag, damaged beams or trapped support are rejects. This plenum has no slicer, bridge, cleanout or physical print pass.')
save(im)
# Separate physical prints are shown in their saved print poses, not an invented assembly split.
im,d=page('03x','Count and qualify the bonded catch','The tub CAD row combines two prints. Bond strength, creep, exact adhesive and actual printed fit remain unqualified.')
scene(im,['print_tub_body'],['print_tub_body'],rect=(45,190,920,640),direction=(1,2,1))
scene(im,['print_tab_catch'],['print_tab_catch'],rect=(1100,190,440,460),direction=(1,2,1))
text(d,65,860,'Piece 1  Tub body in its exported print pose',26,True,width=900)
text(d,1100,680,'Piece 2  Catch stub',26,True,width=500)
joint=MAN.get('tab_catch_joint',{})
text(d,1100,740,'Separate STL and layer direction. Tenon seats against the -Y datum. Keep adhesive off the catch face.',24,width=490)
if joint:text(d,65,790,f"Source tenon: {joint['tenon_mm']}; ceiling floor {joint['ceiling_floor_mm']:.2f} mm. Nominal geometry only.",22,width=900)
text(d,65,930,'Use the nominated joint dimensions and full stub/pocket coupons. Compare production layer direction, gap/tilt, cure and hot dwell. A beam estimate does not qualify an adhesive or interlayer joint.',24,width=1530)
stop(d,'No epoxy SKU, print process, loaded service temperature or joint strength is certified. Optical torque and alignment gates remain open.',y=1040)
save(im)
# 6
im,d=page('04','Build one removable stack','Prepare J2, battery-pad and header wiring while both board faces remain accessible.')
scene(im,STACK,['carrier'],offsets={'carrier':(0,27,0)},direction=(.7,2,1),arrows=[((-70,42,35),(-70,19,35))],labels=[((-70,47,35),'3')])
note(d,'Keep kit spacing','Seat Pi CSI end BEFORE the cooler. Correct contact face; straight cable and latch. Keep camera end protected.\n\nThen fit cooler with its 2 push pins and native fan lead once.\n\nRetain upper 4 x M2.5 x 5 + original standoffs.\n\nLower 4 x M2.5 x 8 pass through carrier. Check thread depth before tightening.\n\n3.4 mm engagement is nominal only.')
text(d,65,907,(f"SOURCE / PROXY HOLD: registered Pi intersects the illustrative cooler perimeter / pin model ({COOLER_CLASH.get('overlap_mm3',0):.2f} mm3). Measure and register the actual cooler outline before assembly." if COOLER_CLASH else 'Actual cooler footprint and fan-lead routing remain unmeasured; kit spacing does not establish fit.'),24,color=ORANGE if COOLER_CLASH else GRAY,width=1510)
stop(d,'No battery. No assumed pad location. Do not change pogo geometry or repeatedly unclip the cooler.')
save(im)
# 7
im,d=page('05','Wire the detachable power button','Electrical schematic, not a measured pad-location drawing')
# schematic
for x,title in [(90,'Pi 5 J2'),(655,'Molex signal pair'),(1220,'NO momentary')]:
 d.rounded_rectangle((x,280,x+340,530),radius=20,outline=INK,width=4);text(d,x+25,306,title,27,True,width=295)
for yy in (405,470):
 d.ellipse((385,yy-9,403,yy+9),fill=INK);d.line((405,yy,655,yy),fill=BLUE,width=7);d.line((995,yy,1220,yy),fill=BLUE,width=7)
d.line((1220,405,1380,405),fill=INK,width=4);d.line((1410,405,1460,405),fill=INK,width=4);d.line((1380,405,1415,375),fill=INK,width=4);d.line((1460,405,1460,470,1220,470),fill=INK,width=4)
text(d,90,640,'Bridge only the two J2 pads with a normally-open momentary switch.',33,True)
text(d,90,720,'Identify J2 on the actual Pi: between RTC battery connector and board edge. Insulate and strain-relieve all four solder joints. Meter open / pressed continuity before power.',28,width=1490)
text(d,90,858,'J2 class: Micro-Fit 3.0, 2 circuits, pre-crimped leads. Exact SKU, roots, latch travel and stow remain unqualified. It must not mate to the FPS PicoBlade or EVF RCY halves.',27,width=1490)
stop(d,'J2 is signal-only, not GPIO or battery isolation. Finished cuts, pad reach, wire exits and nut access remain gates.')
save(im)
# 8
im,d=page('06','Prepare control wiring','Physical J8 pin numbers below. This is a pin map, not a rotated-board orientation drawing.')
for x,heading,lines in [(70,'QT encoder','Pin 1  3V3  -> SH 2\nPin 3  SDA   -> SH 3\nPin 5  SCL    -> SH 4\nPin 6  GND  -> SH 1\nBridge A0: address 0x37'),(615,'18 / 24','Pin 33  GPIO13\nPin 34  GND\nCK1044 common A / throw 2\nClosed / low = 24 fps\nOpen / high = 18 fps'),(1140,'Run button','Pin 37  GPIO26\nPin 39  GND\n\nNormally open\nPressed / low = run')]:
 text(d,x,215,heading,33,True,width=480);text(d,x,300,lines,29,width=475)
text(d,70,625,'Match physical pin 1 to the real board silkscreen / official pinout before plugging.',32,True,width=1510)
text(d,70,705,'QT target: 250 +/- 10 mm, two source leads, four staggered insulated splices. Meter by SH pin number; never match wire colours alone. Place splice sleeves on a straight, accessible run.',28,width=1510)
text(d,70,848,'The panel carries encoder and J2. Support the FPS switch on its tub rest; keep its complete pair mated during carrier service. Separate that pair only on the bench.',28,width=1510)
stop(d,'Header plugs and every wire tail must clear the stack, HDMI, fan and carrier motion.')
save(im)
# A real switch and its service stack replace the inherited generic rotary proxy.
if 'fps_nut' in DATA:
 im,d=page('06b','Set the real frame-rate switch','Conditional Lorlin CK1044. Two adjacent detents are 30 degrees apart.')
 ids=['switch_1824','knob_fps']+FPS_HARDWARE
 scene(im,ids,ids,offsets={'knob_fps':(0,40,0),'fps_nut':(0,24,0),'fps_mounting_washer':(0,12,0)},rect=(45,175,1080,710),direction=(1,2,1))
 note(d,'Three distinct pieces','Nut. Mounting washer. Stop / tang washer.\n\nStop washer shape is not measured and is not drawn. Confirm supplied hardware.\n\nSet two adjacent positions. Meter A / 2: open = 18; closed = 24.\n\nPreserve the stop setting when removing knob, nut and panel.\n\nThe switch rides with the module; washer, nut and knob go on after the panel (page 16).')
 text(d,65,900,'Measure the actual stack before cutting. Proposed shaft length 11.8 mm from mounting face is a fit study; 6.35 mm D shaft / 5.5 mm flat needs a real knob coupon.',26,width=1520)
 stop(d,'Nut / mounting-washer shapes are estimated. Actual stop stack, pin clocking, shaft cut and tool access remain gates.')
 save(im)
if FPS_READY:
 im,d=page('06c','Keep the full FPS harness together','Two donor female GPIO heads + two splices + both factory Molex housings + A / throw 2.')
 scene(im,['switch_1824','hdr_fps_lead_33_34']+FPS_WIRES,['switch_1824','hdr_fps_lead_33_34']+FPS_WIRES,rect=(45,175,1080,715),direction=(1,2,1))
 note(d,'Identify both black wires',('FPS-only CAD group clears; other looms remain gated.\n\n' if FPS_PASS else 'Integrated FPS group clearance awaiting current report.\n\n')+'Male 2181110202: 225 +/- 6 mm exposed stock.\n\nFemale 2181120201: 150 +/- 6 mm exposed stock.\n\n200 mm main axis includes donor stubs / splices.\n\nKeep pair mated in the camera. Bench separation only.')
 text(d,65,900,'Amber cylinders reserve two finished splices, maximum diameter 3 x 10 mm. Cut lengths, solder overlaps, individual-core fanout and terminal joints still require measurement.',26,width=1520)
 stop(d,'Label and continuity-test FPS. J2 uses a distinct Micro-Fit class; exact receipt try-mate checks remain open. Axes are not cuts.')
 save(im)
im,d=page('06d','Fit the OS card on the bench','The microSD travels with the removable Pi stack. Closed-panel card access is blocked by the power switch.')
scene(im,['pi5','microsd'],['microsd'],offsets={'microsd':(20,0,0)},rect=(45,175,1090,715),direction=(1,2,.6),arrows=[((-15.9,4.8,33.8),(-35.9,4.8,33.8))])
note(d,'Card before carrier','Prepare and verify the OS image on the bench.\n\nIdentify real contact orientation. Insert -X before the stack enters the body.\n\nLeave the card with the stack during carrier insertion.\n\nFor later card service: isolate all power, remove the panel, then withdraw +X.')
text(d,65,910,'The panel-mounted J2 power switch occupies the card extraction route. The front slit alone does not establish service access.',25,width=1510)
stop(d,'No closed-panel microSD service. Only a panel-off rigid path is checked; real contact orientation and handling remain open.')
save(im)
# B2 bench (moved before step 1, FP-06)
im,d=page('06e','Preform HDMI on the bench','3557 right-angle micro-HDMI at Pi  |  intact 300 mm 3562 ribbon  |  3556 straight head at EVF')
# Three full-length poses retain every millimetre of the proposed stock ribbon.
for i,(key,label) in enumerate([('hdmi_strip','Installed'),('hdmi_premate','EVF end free / Pi still mated')]):
    scene(im,[key],[key],rect=(45+i*535,235,510,610),direction=(1,2,1))
    text(d,65+i*535,850,label,25,True,width=510)
note(d,'A full-length study','Each selected pose models 300 mm.\n\nKeep Pi head mated during service.\n\nBoth-end-free pose rejected: power-wire conflict.\n\nR3 / R5 are allowances, not manufacturer limits.')
text(d,70,925,'The complete serpentine strip and both rigid heads must fit through every assembly and service pose.',25,True,width=1520)
stop(d,('Full material clears checked solids; head/carry status is separate. Real bend, clocking, retention and EMI remain open.' if MATERIAL_PASS else 'This 300 mm route needs source-matched exact checks plus real length, clocking, material and EMI tests.'),y=1003)
save(im)
# B2 bench: EVF feed (moved before step 1, FP-06)
im,d=page('06f','Build the detachable EVF feed','Unpowered electrical schematic. Contact identity is traced by continuity, never colour alone.')
for x,w,label in [(70,290,'USB donor 4448'),(850,245,'2180 socket'),(1150,235,'2181 pins'),(1430,190,'EVF board')]:
 d.rounded_rectangle((x,250,x+w,540),radius=12,outline=INK,width=3);text(d,x+12,278,label,24,True,width=w-20)
for yy in (390,478):
 d.line((360,yy,850,yy),fill=INK,width=5);d.line((1095,yy,1150,yy),fill=BLUE,width=5);d.line((1385,yy,1430,yy),fill=INK,width=5)
text(d,85,373,'VBUS +',25);text(d,85,462,'GND',25)
d.rectangle((540,364,670,416),fill='white',outline=INK,width=3);d.line((648,365,648,416),fill=INK,width=8)
text(d,490,320,'1N5817',24,True);text(d,422,553,'Anode: USB side  |  Band / cathode: EVF side',23,width=780)
text(d,1443,373,'EXT +',25);text(d,1443,462,'GND',25)
text(d,70,655,'USB side: 2 diode / positive joints + 1 ground splice. EVF side: 2 traced board joints.',28,True,width=1530)
text(d,70,739,'Remove four donor jumper ends only after qualifying the length budget. Separately sleeve D+ and D-; insulate a shield only if present. Keep all joints off bends and strain-relieve both cable ends.',27,width=1530)
text(d,70,854,'4448 length conflict: catalog 300 mm; supplier drawing 325 +/- 10 mm. Both Generic RCY-style tails: nominal 100 mm / 20 AWG. Final cuts, overlaps and actual plug / junction envelopes remain unmeasured.',25,width=1530)
stop(d,'Isolate USB and battery. Meter polarity and diode direction. A diode does not guarantee the EVF voltage ceiling; G-W6 remains open.')
save(im)
im,d=page('06g','Verify the battery and EVF power paths','Electrical intent only. Bench qualification is required before any full-camera power-up.')
text(d,65,190,'1S2P protected pack',31,True);text(d,65,246,'60 mm 18 AWG lead',25)
arrow(d,(410,243),(565,243));text(d,595,190,'XT30 junction',31,True);text(d,595,246,'Mate by housings',25)
arrow(d,(920,243),(1075,243));text(d,1100,190,'X1203 battery pads',31,True);text(d,1100,246,'Pogo feed -> Pi 5',25)
d.line((170,355,720,355),fill=ORANGE,width=8);d.line((820,355,1430,355),fill=ORANGE,width=8);d.rectangle((720,335,820,375),outline=ORANGE,width=5);text(d,90,331,'+',32,True,color=ORANGE);text(d,90,494,'-',32,True)
text(d,555,427,'Positive: 15 A 0251015.MXL fuse near XT30',28,True,width=820)
d.line((170,515,1430,515),fill=INK,width=8);text(d,65,555,'16 AWG: buy 914.4 mm per colour. Both 270 mm path budgets include unresolved pad-root allowances. Positive also includes 20 mm rigid fuse / joint zone. Copper cuts / overlaps TBD.',29,width=1510)
text(d,65,666,'EVF USB positive -> qualified feed -> EXT+; USB ground -> EVF GND.',29,True,width=1510)
text(d,65,735,'Inherited diode option: 1N5817 band / cathode toward EVF. It does not guarantee the required voltage ceiling. Regulator alternative is not adopted. Trace the actual EVF revision before soldering.',27,width=1510)
stop(d,f"BLOCKED: {DROP['drop_lo_v']:.5f} to {DROP['drop_hi_v']:.5f} V at {DROP['i_peak_a']:g} A versus {DROP['limit_v']:.3f} V. Reach and hot-drop need one compatible solution.")
save(im)
# B3 bench: panel subassembly (FP-06, VN-40 / VN-46)
im,d=page('06h','Build the panel subassembly','Bench. Encoder, exposure knob and power button only; the FPS switch rides with the module.')
pids=['panel','encoder','knob_exp','power_button','power_nut_reserve']
scene(im,pids,['knob_exp','power_nut_reserve'],offsets={'knob_exp':(0,30,0),'power_nut_reserve':(0,-15,0)},rect=(45,175,1080,710),direction=(1,2,1))
note(d,'Thumb behind the board','Snap the encoder into its cradle.\n\nThumb flat on the back of the encoder board; press knob_exp onto 2 paper strips; pull the paper out.\n\nPower button flange on the outer face; nut on the inner face with a deep socket on the button axis.\n\nNo FPS washer, nut or knob here.')
stop(d,'Thread length and deep-socket reach on the real panel are unmeasured. Keep the J2 junction half free.')
save(im)
# 9
# fixup-1: the strap is threaded on the OPEN base (its over-bridge pass lies in the base-top recess that the seated
# tub floor closes; r7 order), then the tub is seated and the grip locked. Shows both anchors with the routing proxy.
im,d=page('07','Prepare the grip, then thread the strap','Battery stays out. Tub off: strap and run lead go in while the base top and floor passage are open.')
scene(im,['base_grip','tripod_nut','run_button','strap'],['strap','run_button'],rect=(45,175,1090,710),direction=(-1,-2,.6))
note(d,'Strap on the open base','Fit the tripod nut. Feed the run lead up through the open floor passage, then drop the run button into its cradle.\n\nThread the 12 mm strap through both upper and heel slots now: its pass over the bridge lies in a 2 mm recess in the base top that the seated tub floor closes.\n\nThe lower return passes through both heel slots and inside the grip wall. Keep the cap, battery travel and tripod seat clear.\n\nBuckle, closure overlap and retained tail still need real-part layout.')
text(d,65,910,'Strap routing proxy only; actual bends, threading, hand clearance and the assumed 1.4 mm thickness need measurement.',25,width=1040)
stop(d,'Neither anchor nor this routing is a rated safety tether. Qualify the actual strap, closure and both anchors before use.')
save(im)
im,d=page('07b','Seat the tub, then lock the grip','Over the threaded strap. Keep the run lead in the floor passage.')
scene(im,BASE+['strap'],['tub','p_grip'],offsets={'base_grip':(0,0,-22),'run_button':(0,0,-22),'tripod_nut':(0,0,-22),'strap':(0,0,-22),'p_grip':(0,0,-34)},arrows=[((-55,0,-29),(-55,0,-5))])
note(d,'Tub on, then lock','Engage the keyhole tongues in their actual keyed direction over the threaded strap; do not lock yet.\n\nThe strap is already fitted: it went in on the open base (page 07), before the tub and before the grip-lock screw, whose driver handle passes close to it.\n\nThen drive the 1 x PT grip-lock screw on its axis.\n\nThe panel is never the grip lock.')
stop(d,'Arrows show approach only. Keyhole engagement, driver access and actual lead passage need dry fitting.')
save(im)
# 10 (FP-06, VN-39: collar and centring gauge on the EMPTY lip, camera still out)
im,d=page('08','Collar and centring gauge first','The camera is still out: the gauge seats in the empty tub lip. Carrier and panel absent.')
scene(im,BASE+['strap','lens_collar','s_c1','s_c2','s_c3'],['lens_collar','s_c1','s_c2','s_c3'],offsets={p:(22,0,0) for p in ('lens_collar','s_c1','s_c2','s_c3')},direction=(1,2,1),arrows=[((48,0,60),(26,0,60))])
note(d,'Gauge, then camera','1  Collar feet onto the tub face over the 3 short inserts.\n\n2  Start s_c1..s_c3 about 2 turns.\n\n3  Push the gauge for this lens through the collar until its rear cone seats in the empty lip.\n\n4  Thumb on the gauge; tighten s_c1..s_c3 on axis, 0.15 N m provisional.\n\n5  Pull the gauge out forward.')
stop(d,'The gauge and the camera / adapter are never in the body together (CAD overlap 927.75 mm3). The gauge is a tool and is not drawn.')
save(im)
# 10b
im,d=page('08b','Camera before the carrier','The board cannot be pushed through the installed vertical stack. Collar fitted, gauge out.')
scene(im,BASE+['strap']+OPT,['gs_camera','c_cs_adapter'],offsets={'gs_camera':(-11.1,65,2),'c_cs_adapter':(-11.1,65,2)},direction=(-1,2,1),arrows=[((-29,60,62),(-29,8,62)),((-29,8,62),(-29,8,60)),((-29,8,60),(-18,8,60))])
note(d,'Three-part motion','Support the prepared Pi module outside. Mate the camera FPC end before insertion; Pi end is already under the fitted cooler.\n\n1  Approach from +Y with rearward / upward offset.\n\n2  Lower onto seating height.\n\n3  Move lensward to datum; lock tab between the tines.\n\nNothing holds the camera back until the lens is on: go straight to page 08c.')
stop(d,'HOLD: rigid camera drawing omits the full 200 mm linked FPC. Finger access, optical support and torque catch remain open.')
save(im)
# 10c (FP-06, VN-41: lens and pinch screw before the carrier and panel)
im,d=page('08c','Lens before the carrier and panel','r7 step 8 method through the open +Y side. Fingertips only; never react thread torque through the PCB or cover.')
scene(im,BASE+['strap']+OPT+['lens','s_c4'],['lens','s_c4'],offsets={'lens':(40,0,0)},direction=(1,2,1),arrows=[((75,0,60),(45,0,60))])
note(d,'Float, then pinch','Fit s_c4 loosely.\n\nBody on its side, open side up; one fingertip pushes the camera cover forward onto its lip catch.\n\nScrew the lens in with fingertips until it stops; the tab catch takes the torque.\n\nPush the lens onto the collar cone.')
text(d,65,875,'With s_c4 still loose, turn lens and camera together the other way until the lock tab stops on the other tine, then back about half way; look and feel: the camera touches nothing. Then snug s_c4 on its axis, 0.2 N m provisional.',24,True,width=1520)
stop(d,'Source-bound roll / J7 geometry does not qualify printed float, bond strength or optical alignment. Check both witness marks.')
save(im)
# 11
im,d=page('09','Eyepiece, then the EVF module','Keep OLED foam, native flex and connector latches unstressed.')
scene(im,BASE+['strap']+OPT+['lens','s_c4']+EVF_IN,['eyepiece','evf_board','hmx039','foam_pad'],offsets={'eyepiece':(-30,0,0),'evf_board':(0,45,0),'hmx039':(0,45,0),'foam_pad':(0,45,0)},direction=(-1,2,1),arrows=[((-206,11,105),(-176,11,105)),((-142,60,78),(-142,13,78))])  # eyepiece +X push from behind first (r7 INSERTIONS eyepiece_in), then the EVF from +Y
note(d,'Keep the board secure','Push the eyepiece spigot +X through the rear-wall bore from behind first.\n\nSlide the module from +Y into its seats; foam and native flex unstressed.\n\nThe panel supplies clamping later; do not let the open module fall.\n\nNo HDMI or EVF power mating yet: their ends arrive with the carrier.')
stop(d,'Native flex contact face follows the actual EVF kit. Do not infer it from a CAD envelope.')
save(im)
# 13
im,d=page('11','Insert the stack with a free EVF end','Intended trial sequence: Pi HDMI adapter and OS microSD fitted first; recording drive absent.')
carried=STACK+HEADERS+['microsd','hdmi_premate','p_hdmi_pi','p_hdmi_evf','p_usb_pi']+(['switch_1824']+FPS_WIRES if FPS_READY else [])
scene(im,BASE+['strap']+OPT+['lens','s_c4']+EVF_IN+carried,carried,offsets={p:(0,50,-9 if p=='p_hdmi_evf' else 0) for p in carried},arrows=[((-75,70,40),(-75,23,40))])
text(d,70,912,(f"CAD: full HDMI and carried heads checked at {CARRIED_ROWS[0]['step_mm']:g} mm poses, with {CARRIED_ROWS[0]['evf_head_drop_mm']:g} mm head drop ({CARRIED_ROWS[0]['evf_stroke_mm']:g} mm stroke + {CARRIED_ROWS[0]['margin_below_mouth_mm']:g} mm margin). Other looms remain gated." if CARRIED_PASS else ('BLOCKED: carried '+CARRIED_OBSTRUCTIONS+'. Geometry must change before this step.' if CARRIED_FAIL else 'Complete HDMI strip + heads shown. FPS full mated harness shown; combined motion remains gated.')),23,color=GRAY,width=1040)
note(d,'Hold before proceeding','Run lead onto Pi pins 37 / 39 at the staging pose.\n\nCarry FPS bushing and stack together from +Y, both supported.\n\nEVF HDMI end free, at least stroke + 3 mm low.\n\nPigtail through the floor opening; FPC clear of the 3.9 mm gap.\n\nSeat carrier; 2 x PT screws.')
stop(d,'HOLD: complete 200 mm CSI ribbon is already linked at both ends and is absent from the rigid carrier sweep. Full flexible motion is unproved.')
save(im)
# 14
im,d=page('12','Mate the EVF ends from inside','Step 5, fully unpowered. Storage stays out. Hold the adapter body, never pull the ribbon.')
scene(im,EVF_IN+STACK+['hdmi_strip','p_hdmi_pi','p_hdmi_evf'],['hdmi_strip','p_hdmi_pi','p_hdmi_evf'],direction=(-1,2,.6),arrows=[((-145.6,5.5,15),(-145.6,5.5,36))])
text(d,70,912,'Tub omitted for visibility. Adapter blocks are unmeasured catalog envelopes, not detailed keyed connectors.',23,color=GRAY,width=1040)
note(d,'EVF head upward','Bring the straight 3556 head from below.\n\nConfirm the keyed receptacle and actual contact face.\n\nMate fully by its body. Add qualified strain relief clear of the latch.\n\nNo twist to correct a wrong head.\n\nThen mate the EVF power RCY pair by both housings.')
stop(d,'Upward head travel, fingers / pliers and simultaneous USB + HDMI access must all clear. Final pose is insufficient.')
save(im)
# 15
im,d=page('13','Prove camera connector access','Pi end seats before cooler; camera end before camera insertion. This is a tool-reserve view, not an instruction to mate late.')
csi_tools=['csi_tip_reserve','csi_shank_reserve'] if CSI_MATCHED and CSI_CHECK.get('tool_reservations') else []
scene(im,['tub']+OPT+EVF_IN+STACK+csi_tools,csi_tools,rect=(50,180,1050,700),direction=(1,-2,.65),arrows=CSI_ARROWS)
text(d,70,885,('Rigid cylindrical reserve clears only; actual tool, cooler and full FPC remain unresolved.' if CSI_PASS else ('Declared cylinders intersect: '+CSI_OBSTRUCTIONS+'. Access remains blocked.' if CSI_MATCHED and CSI_OBSTRUCTIONS else 'No current clear CSI tool reservation. The inherited rotated connector / old side-slot proof is superseded.')),23,color=GRAY,width=1040)
text(d,70,950,f"Intake wall slots: {VENT['intake_wall_throat_mm2']:.0f} mm2 nominal. CSI remains a straight unsealed bypass; keep latch/tool access clear.",21,color=GRAY,width=1510)
note(d,'Keep the complete ribbon','Pi end BEFORE cooler (04). Camera end supported before insertion (08b).\n\nBoth ends are linked when the carrier moves. The rigid sweep omits all 200 mm of FPC.\n\nProve full width, roots, slack, actual latch/jaws and motion with other looms.\n\nSide cylinders do not qualify service with the cooler retained.')
stop(d,'OPERATIONAL HOLD: actual cooler outline, latch operation, inserted FPC and interacting flexible looms are unresolved.')

save(im)
# 17
im,d=page('15','Prove stored slack and disconnection','Complete cable lengths, connector bodies, sleeves and tie heads must fit at the same time.')
scene(im,BASE+STACK+['xt30_pair','pack'],['xt30_pair','carrier'],direction=(1,2,1))
note(d,'No hidden excess',WIRE_CAPTION+'\n\nKeep fuse straight and supported. Keep joints off bends.\n\nFour tie slots are provisions, not a tested retention scheme.\n\nLoops must clear CSI tools, GPIO tails and UPS PCB.\n\nTest pack extraction with retention unchanged.')
stop(d,'If XT30 cannot be parted before opening the body, the assembly is not safely serviceable. Redesign before closure.')
save(im)
# This page is enabled only when the exported mesh is the frozen 21-degree power pose.
if POWER_CURRENT:
    power=json.loads(read_text(POWER_SNAPSHOT));poses=power['rigid_service_poses'];initial=poses[0]
    m0=np.array(initial['matrix']);c0=np.array(initial['center'])
    local=(np.array(DATA['xt30_pair']['vertices'])-c0)@m0
    selected=[0,len(poses)//2,len(poses)-1]
    im,d=page('15b','Rigid connector withdrawal study','Body omitted for clarity; it stays closed during isolation. Full flexible-harness service is still blocked.')
    for i,pi in enumerate(selected):
        pose=poses[pi];mat=np.array(pose['matrix']);center=np.array(pose['center'])
        # Validate that one rigid transformation preserves the modeled fuse endpoints as well.
        for key in ('fuse_start','fuse_end'):
            transformed=(np.array(initial[key])-c0)@m0@mat.T+center
            if np.linalg.norm(transformed-np.array(pose[key]))>1e-5:raise RuntimeError('Fuse is not rigidly carried in this power pose')
        key='power_pose_'+str(pi);DATA[key]=dict(DATA['xt30_pair']);DATA[key]['vertices']=(local@mat.T+center).tolist()
        scene(im,['base_grip','pack',key],['pack',key],offsets={'pack':pose['pack_translation']},rect=(45+i*365,190,350,690),direction=(1,2,.45))
        text(d,65+i*365,904,['Stored','Unwind / lower','Withdrawal limit'][i],24,True,width=335)
    note(d,'What changed',('CAD checked: 201 sampled poses clear the closed assembly, with pack moving and cap removed.' if POWER_PASS else 'The floor passage and local tongue-corner relief are being checked for rigid junction / fuse withdrawal.')+'\n\nThe pack moves with the junction.\n\nThis does not prove the complete conductor paths, joints and retained slack can deploy or return safely.')
    stop(d,'Do not pull the pack through a blocked loom. Complete wires, pad joints, retention and pinch clearance remain STOPs.')
    save(im)
# Stored cable and free reach are deliberately drawn as distinct states.
im,d=page('15q','Separate QT storage from free mating reach','Source-bound routing study. The allowance is a reach budget; full flexible transition and real cable packing remain HOLD.')
for i,(key,label) in enumerate([('guide_qt_stored','Stored nominal 250 mm lead'),('guide_qt_free','Free curve at propped panel')]):
    scene(im,QT_BRANCH_IDS+[key],QT_BRANCH_IDS+[key],rect=(55+i*540,200,500,560),direction=(1,2,.7))
    text(d,65+i*540,780,label,24,True,width=500)
branch_len=max(b['curve']['rounded_length_mm'] for b in _qt_source['branches'] if b['cable']=='qt')
text(d,65,845,f"Stored: main {QT_MODEL['curve']['rounded_length_mm']:.2f} + longest branch {branch_len:.2f} = 250 mm nominal. The 240-260 mm family is checked separately.",23,width=1000)
text(d,65,935,f"Free reach: curve {QT_FREE['curve']['rounded_length_mm']:.2f} + branch {branch_len:.2f} + 24 mm allowance. Remaining stock is not drawn as a qualified flexible shape.",23,width=1000)
note(d,'Interpret the scope','Round routing envelopes only.\n\nFour 1.6 mm cores cannot pack inside the 3.2 mm bundle proxy. Real MP-QT section, sleeves and roots are unqualified.\n\nA minimum-reach pass cannot prove all cable stows or moves between these poses.\n\nKeep four splices and finished 250 +/- 10 mm intent.')
stop(d,'No cut instruction or flexible-motion pass. Keep purchased parts and finished-length range unchanged.',y=1030)
save(im)
# 18
im,d=page('16','Close the panel, then fit the FPS hardware','Step 6. Shown part-open; service removal is the exact reverse. Keep the FPS pair mated.')
scene(im,BASE+['strap']+OPT+['lens','s_c4','microsd']+EVF_IN+STACK+PANEL,PANEL,offsets={p:((0,42,0) if p=='knob_fps' else (0,25,0) if p=='fps_nut' else (0,15,0) if p=='fps_mounting_washer' else (0,0,0) if p=='switch_1824' else (0,8.5,0)) for p in PANEL},arrows=[((-10,30.5,50),(-10,39,50))])
note(d,'Panel, screws, then FPS','Prop the panel; mate QT and J2.\n\nMove it in along -Y, guiding bushing and peg; support the switch body.\n\nDrive the 4 panel screws before the FPS knob is on.\n\nThen washer, nut (deep socket on the bushing axis), knob on the paper strips.\n\nRemoval: knob, nut, washer, screws; tip support for the first 8.5 mm, then bushing.')
stop(d,'Never use screws to crush slack into the enclosure. Real shaft grip, stop-stack retention and whole-harness motion remain STOPs.')
save(im)
# 19
im,d=page('17','Recording drive and eyecup','Fit selected compact Princeton drive with its protective cap removed. OS microSD is already installed.')
scene(im,BASE+['strap']+OPT+['lens','s_c4','microsd']+EVF+STACK+PANEL+['usb_stick'],['usb_stick','eyecup'],offsets={'usb_stick':(-35,0,0),'eyecup':(-25,0,0)},arrows=[((-188,-7,39),(-156,-7,39))])
note(d,'Straight insertion','Drive travels +X into upper USB3.\n\nOS microSD was fitted on the bench. Later card service requires panel removal.\n\nPush the eyecup over the eyepiece barrel from the rear.\n\nThe lens and s_c4 went on in step 2 (page 08c).')
text(d,70,912,'Estimated storage-plug keepout omitted: it is not a physical inventory item or a proven mating shape.',23,color=GRAY,width=1040)
stop(d,'Published Princeton size includes cap. Real plug fit and warm sustained >=100 MB/s are not measured.')
save(im)
# Air-path assembly and physical qualification are separate from nominal aperture checks.
im,d=page('17v','Keep ventilation clear during assembly','The outer bays conceal the inner slots. Their pressure loss, leakage, recirculation and cooling remain unmeasured.')
scene(im,['tub','pi5','cooler','carrier'],['tub'],rect=(45,185,850,580),direction=(1,-2,.6))
text(d,65,790,'Tub, stack and illustrative cooler. Panel and looms omitted for visibility; prove clearance with the complete final assembly.',24,color=GRAY,width=805)
flow_rows={r['id']:r for r in FLOW['checks'] if r['id'] in ('cold_path_min_cut','hot_path_min_cut')}
hot_min=flow_rows.get('hot_path_min_cut',{}).get('min_cut_mm2')
summary=VENT_STATE['report']['summary']
status=f"Saved-STEP checks: {summary['pass']} pass / {summary['fail']} fail / {summary['info']} info. "
status+=(f"Path-aware hot min cut: {hot_min:.1f} / {VENT['exhaust_wall_throat_mm2']:.0f} mm2 ({flow_rows['hot_path_min_cut']['status']}). Mouth totals are not a flow result." if hot_min is not None else 'No sampled hot-bay section is available. Mouth totals are not a global flow minimum.')
text(d,65,880,status,23,True,color=GRAY if VENT_GEOMETRY_PASS else ORANGE,width=805)
text(d,960,183,'BEFORE CLOSURE',29,True,width=650)
text(d,960,242,f"Keep mouths, inner slots and baffles clear of full FPC, EVF feed, power loop, tie heads and fan lead.\n\nCSI stays 12 x 27 mm R1 and uncovered. It is an unsealed cooling bypass.\n\nTest hand, strap and stand occlusion. Blocking the hot underside leaves only the front neck: {VENT['hot_front_mouth_mm2']:.1f} mm2 versus {VENT['exhaust_wall_throat_mm2']:.0f} mm2 wall slots. No blocked-vent operation is qualified.",24,width=650)
text(d,960,665,'THERMAL GATE',29,True,width=650)
text(d,960,720,'After electrical prerequisites pass, record ambient, closed-body load, fan speed/duty, component temperatures and throttling at normal hand positions. Compare with the open reference using the same hardware and conditions.\n\nMeasure the actual cooler first; its proxy/source conflict remains open.',24,width=650)
stop(d,'No airflow, fan operating-point, hand-occlusion or thermal pass. All %d inherited physical gates, M1 and candidate gates stay open.'%GATES_OPEN)
save(im)
# 20
im,d=page('18','Close the loop before power','Physical checks and measured records decide whether this candidate can become a build.')
checks=['Pack disconnected during all internal work','Connector identities, contact faces and continuity verified','No trapped ribbon, fuse sleeve, splice, tie head or fan lead','Panel flush; grip lock, strap and optical support secure','Plenum mouths and wall slots clear; no trapped support; CSI open','XT30 disconnect reachable with retention fitted','Required bench gates passed before pack is connected last']
for i,s in enumerate(checks):
 y=205+i*87;d.rectangle((70,y,105,y+35),outline=INK,width=3);text(d,140,y-5,s,30,width=1430)
text(d,70,880,'Then qualify closed-body power, thermal, storage and recording performance, plus revised collar / strap loads. Nothing in this booklet closes a physical gate.',28,width=1510)
stop(d,'%d inherited gates + M1 + candidate gates remain open. No fabrication, safety or performance certification.'%GATES_OPEN)
save(im)
# 21
im,d=page('19','Service in dependency order','Always start with page 00 and physical battery disconnection. Routes and refits: ASSEMBLY-VERTICAL section 5.')
SERVICE_ROWS=[('Panel','Knob, FPS nut (deep socket), washer, 4 screws off -> tip, then bushing support, +Y -> QT / J2 apart (one J2 cycle). Refit: panel, screws, washer, nut, knob.'),
 ('Pi module','Drive out -X -> panel off -> EVF HDMI / power and Pi FPC released -> 2 carrier screws -> stage +Y, switch supported; run lead apart there; pigtail drawn up.'),
 ('Lens, same collar','Closed body: s_c4 one turn, nose-down, fingertip unscrew. Refit nose-down; turn back to float; then s_c4.'),
 ('Lens, other collar','Full chain: lens, panel, drive, module, camera, then collar. Refit from that collar and its gauge (lip empty), camera, lens float, module, panel, drive, pack.'),
 ('Camera','Lens, panel, drive and the whole module out first (VN-42, user decision); reverse camera path. Refit camera, then lens, before the carrier.'),
 ('EVF','Panel off -> EVF power pair and HDMI body unplugged -> flex protected -> module +Y.'),
 ('OS card','Panel off before in-body microSD withdrawal, or on the bench with the module out.'),
 ('Grip','Pi module out first (run lead at pins 37 / 39) -> grip-lock screw -> grip off.'),
 ('Refit','Collar + gauge before camera. Lens + s_c4 before carrier. Junctions before panel. FPS hardware after panel screws. Pack last.')]
y=196
for label,body in SERVICE_ROWS:
 text(d,75,y,label,27,True,width=300);y=max(y+40,text(d,390,y,body,24,width=1200))+14
stop(d,'CSI tool clearance is not latch qualification. GPIO plugs stay carried; actual FPC release, run slack and wire withdrawal must pass.')
save(im)
# 21b (FP-06, VN-42: user decision, both options)
im,d=page('19b','Camera and collar service: a user decision','VN-42. The current geometry needs the whole module out before the camera can leave.')
text(d,75,205,'Option A   Accept',30,True,width=1500)
text(d,75,255,'Camera, collar and any lens change that needs a different collar go through the full module route: panel off (one J2 cycle), module STOPs, camera out. A collar change always removes the camera because the centring gauge needs the empty lip. r7 needed only the pack out and the panel off.',25,width=1500)
text(d,75,470,'Option B   Redesign',30,True,width=1500)
text(d,75,520,'B1: let the camera leave ahead of the carrier front, so camera service needs only the panel, as in r7.\n\nB2: a centring gauge that seats without entering the lip, so a collar can be re-centred with the camera in place.\n\nEither changes the service model and needs new motion checks; neither is modelled.',25,width=1500)
stop(d,'Not decided in this guide. Pages 08 to 08c and 19 show option A, the current geometry.')
save(im)
# 22 sources & audit
im,d=page('20','Evidence and open checks','Source-linked review candidate. Vendor facts are not real-part measurements.')
text(d,65,180,'Snapshot',30,True);text(d,65,230,f"Mesh manifest: {ARGS.manifest_sha256[:16]}. No build time is printed, so the same inputs give the same pages.",24,width=1510)
text(d,65,286,'Geometry: compact-kowa_lm6hc meshes plus source-bound concealed-vent STEP checks; 300 mm HDMI snapshot. Wiring intent: candidate assembly/BOM and WIRING-VERTICAL. The separate receipt records exact source hashes.',24,width=1510)
text(d,65,398,'What the CAD motions check',30,True);text(d,65,448,'Rigid body motions are sampled, not continuous swept-volume proofs. Complete HDMI shapes and carried heads have a separate source-bound check. The source-registered CSI ends have a limited declared-tool check; real cooler, latch and full FPC access remain blocked. Other flexible leads, hands, tolerances and physical retention remain unqualified.',25,width=1510)
text(d,65,581,'Primary sources and 12 October evidence',30,True)
links=[('Official camera connection order','https://www.raspberrypi.com/documentation/accessories/camera.html'),('Pi right-angle head 3557','https://www.adafruit.com/product/3557'),('EVF straight head 3556','https://www.adafruit.com/product/3556'),('Intact 30 cm ribbon 3562','https://www.adafruit.com/product/3562'),('Compact Princeton SSD','https://www.princeton.co.jp/product/storage/phdussd.html'),('Lorlin CK rotary switch drawing','https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf'),('USB donor 4448 + supplier drawing','https://www.adafruit.com/product/4448'),('EVF source socket half 2180','https://www.pololu.com/product/2180'),('EVF pin half 2181','https://www.pololu.com/product/2181'),('Molex male assembly drawing','https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/218/218111/2181110201_sd.pdf')]
for i,(name,url) in enumerate(links):text(d,65+(i//5)*790,645+(i%5)*66,name,25,color=BLUE,width=750)
stop(d,'No manufacturer bend limit, purchased cable measurement or production release is invented here.')
save(im)
# Refuse a mixed-generation deliverable if another worker changed a source during rendering.
for p,digest in START_HASHES.items():
    if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest:raise RuntimeError('Source changed during render; rerun after freeze: '+p)
# Assemble image-based PDF; links on evidence page remain clickable.
pdf=OUT/(GUIDE_ID+'.pdf');c=canvas.Canvas(str(pdf),pagesize=(842,595),invariant=1);c.setTitle('D2 2026-10-12 corrective assembly and wiring: blocked review');c.setAuthor('D2 design review')
for i,p in enumerate(pages):
 c.drawImage(str(p),0,0,width=842,height=595)
 # Searchable text layer follows the visible typography; it never paints over the drawings.
 for x,y,line,size,bold in TEXT_PAGES[i]:
  t=c.beginText(x/2,595-(y+size)/2);t.setFont('GuideSansBold' if bold else 'GuideSans',size/2);t.setTextRenderMode(3);t.textOut(line);c.drawText(t)
 if i==len(pages)-1:
  for j,(name,url) in enumerate(links):c.linkURL(url,((65+(j//5)*790)/2,595-(645+(j%5)*66+36)/2,(815+(j//5)*790)/2,595-(645+(j%5)*66)/2),relative=0)
 c.showPage()
c.save()
files=[ROOT/'model.py',HDMI_SNAPSHOT,POWER_SNAPSHOT,ROOT/'ASSEMBLY-VERTICAL.md',ROOT/'BOM-VERTICAL.md',MESH.parent/'manifest.json',MESH.parent/'verification.json',*( [HDMI_CHECK_FILE] if HDMI_CHECK_FILE.exists() else []),*( [POWER_CHECK_FILE] if POWER_CHECK_FILE.exists() else []),*( [CSI_CHECK_FILE] if CSI_CHECK_FILE.exists() else []),*( [WIRE_CHECK_FILE] if WIRE_CHECK_FILE.exists() else []),*( [WIRE_SNAPSHOT] if WIRE_SNAPSHOT is not None else []),Path(__file__),Path(__file__).parent/'software_lineart.py',Path(__file__).parent/'raster.cpp',CAD/'guide/lineart.py']
files=list(dict.fromkeys(files+[Path(p) for p in START_HASHES]))
receipt={'guide_identity':GUIDE_ID,'guide_pdf_filename':pdf.name,'nominated_manifest_sha256':ARGS.manifest_sha256,'generated_utc':EC.UNRECORDED,'guide_pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'mesh_export_utc':MAN.get('built_utc'),'page_count':len(pages),'sources':dict(sorted({rel_posix(p,CAD):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}.items())),'scope':'Compact Princeton storage and Kowa LM6HC only; unqualified review','physical_gates':'%d inherited + M1 remain open'%GATES_OPEN,'source_export_mismatches':SOURCE_MISMATCHES,'mesh_files':{n:h for n,h in MAN['files'].items() if n.startswith('meshes/')} }
receipt['page_images']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pages}
receipt['computed_caption_status']={'main_source_matched':MAIN_MATCHED,'cooler_pi_clash':COOLER_CLASH is not None,'hdmi_source_matched':HDMI_MATCHED,'hdmi_selected_full_material_pass':MATERIAL_PASS,'hdmi_carried_pass':CARRIED_PASS,'power_rigid_pass':POWER_PASS,'csi_source_matched':CSI_MATCHED,'csi_cylinder_reserve_pass':CSI_PASS,'wire_source_matched':WIRE_MATCHED,'fps_material_pass':FPS_PASS,'ventilation_source_matched':True,'ventilation_saved_step_geometry_pass':VENT_GEOMETRY_PASS,'ventilation_physical_qualified':False}
receipt['flex_scope']=MAIN_CHECK.get('flex_scope')
receipt['scoped_reports']={k:{'path':rel_posix(v['path'],ROOT),'sha256':hashlib.sha256(v['path'].read_bytes()).hexdigest(),'summary':v['report'].get('summary'),'failing':v['report'].get('failing')} for k,v in VENT_STATE['scoped'].items()}
receipt['production_prints']=PRINT_COUNTS
receipt['local_bonded_catch_coupon']={'path':rel_posix(VENT_STATE['catch_path'],ROOT),'sha256':hashlib.sha256(VENT_STATE['catch_path'].read_bytes()).hexdigest(),'piece_count':2,'physical_qualified':False,'scope':'Local seating/tilt/adhesion/creep screening only; no whole-tub 0.5 N m qualification'}
receipt['ventilation_review']={'source_report_sha256':hashlib.sha256(VENT_CHECK_FILE.read_bytes()).hexdigest(),'check_summary':VENT_STATE['report']['summary'],'metadata':VENT,'scope':'Saved-STEP plenum and sampled path checks only; no flow, hand-occlusion, thermal or print qualification'}
write_text(OUT/'guide-receipt.json',json.dumps(receipt,indent=2)+'\n')
print(pdf, len(pages),flush=True)
