#!/usr/bin/env python3
"""Reproducible pictorial review guide. Reads exported meshes, never changes CAD.
Run with repo .venv-cad/bin/python. All arrows are proposed motions unless explicitly checked.
"""
from pathlib import Path
import sys,json,hashlib,math,datetime,argparse
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
OUT=Path(__file__).parent/'out-concealed-vents';OUT.mkdir(exist_ok=True)
MESH=ROOT/'out/compact-kowa_lm6hc/meshes'
HDMI_SNAPSHOT=ROOT/'routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json'
POWER_SNAPSHOT=ROOT/'routing-snapshots/power-yaw21-270-provisional/power-270-yaw21.json'
MAN=json.loads((MESH.parent/'manifest.json').read_text())
MAIN_CHECK=json.loads((MESH.parent/'verification.json').read_text())
MAIN_MATCHED=(MAIN_CHECK.get('manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest() and MAIN_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_candidate.py').read_bytes()).hexdigest())
COOLER_CLASH=next((r for r in MAIN_CHECK.get('checks',[]) if MAIN_MATCHED and r.get('category')=='interference' and r.get('id')=='pi5/cooler' and r.get('status')=='fail'),None)
HDMI_CHECK_FILE=MESH.parent/'hdmi-solid-checks.json'
HDMI_CHECK=json.loads(HDMI_CHECK_FILE.read_text()) if HDMI_CHECK_FILE.exists() else {}
HDMI_MATCHED=((ROOT/'verify_hdmi.py').exists() and HDMI_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_hdmi.py').read_bytes()).hexdigest() and HDMI_CHECK.get('snapshot_sha256')==hashlib.sha256(HDMI_SNAPSHOT.read_bytes()).hexdigest() and HDMI_CHECK.get('mechanical_manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest())
CARRIED_ROWS=[r for r in HDMI_CHECK.get('checks',[]) if r.get('category')=='carried_sweep']
CARRIED_PASS=HDMI_MATCHED and bool(CARRIED_ROWS) and all(r.get('status')=='pass' for r in CARRIED_ROWS)
CARRIED_FAIL=HDMI_MATCHED and any(r.get('category')=='carried_sweep' and r.get('status')=='fail' for r in HDMI_CHECK.get('checks',[]))
MATERIAL_PASS=HDMI_MATCHED and all(any(r.get('category')=='full_ribbon_vs_solids' and r.get('id')==name and r.get('status')=='pass' for r in HDMI_CHECK.get('checks',[])) for name in ('installed','premate'))
CARRIED_OBSTRUCTIONS=', '.join(sorted({h.get('id','head')+' / '+h.get('fixed','solid') for r in HDMI_CHECK.get('checks',[]) if r.get('category')=='carried_sweep' for h in r.get('hits',[])}))
START_HASHES={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'model.py',HDMI_SNAPSHOT,POWER_SNAPSHOT,ROOT/'ASSEMBLY-VERTICAL.md',ROOT/'BOM-VERTICAL.md',MESH.parent/'manifest.json',MESH.parent/'verification.json',Path(__file__),Path(__file__).parent/'software_lineart.py',Path(__file__).parent/'raster.cpp',CAD/'guide/lineart.py']}
for name in ('package_concealed_guide.py','README-CONCEALED-VENTS.md','STEP-REVIEW-CONCEALED-VENTS.md','vent_guide_support.py','STEP-REVIEW.md'):
    p=Path(__file__).parent/name
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (CAD/'ASSEMBLY.md',CAD/'../../electronics/gs8-d2-v1/WIRING.md',CAD/'fonts/DejaVuSans.ttf',CAD/'fonts/DejaVuSans-Bold.ttf'):
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (ROOT/'REVIEW.md',ROOT/'BOM-VERTICAL.csv'):
    START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ('microsd-service-dependency.json','wall-probe-context.json'):
    p=MESH.parent/name
    if p.exists():START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (VENT_CHECK_FILE,ROOT/'vent_geometry.py',ROOT/'history/reviewed-export18/tub.step',ROOT/'history/reviewed-export18/panel.step'):
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
POWER_CHECK=json.loads(POWER_CHECK_FILE.read_text()) if POWER_CHECK_FILE.exists() else {}
POWER_PASS=(POWER_CHECK.get('source_sha256')==hashlib.sha256((ROOT/'verify_power_service.py').read_bytes()).hexdigest() and POWER_CHECK.get('status')=='pass' and POWER_CHECK.get('snapshot_sha256')==hashlib.sha256(POWER_SNAPSHOT.read_bytes()).hexdigest() and POWER_CHECK.get('manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest())
if POWER_CHECK_FILE.exists():START_HASHES[str(POWER_CHECK_FILE)]=hashlib.sha256(POWER_CHECK_FILE.read_bytes()).hexdigest()
CSI_CHECK_FILE=MESH.parent/'csi-source-tool-checks.json'
CSI_CHECK=json.loads(CSI_CHECK_FILE.read_text()) if CSI_CHECK_FILE.exists() else {}
CSI_MATCHED=((ROOT/'official_pi5_geometry.py').exists() and CSI_CHECK.get('source_helper_sha256')==hashlib.sha256((ROOT/'official_pi5_geometry.py').read_bytes()).hexdigest() and CSI_CHECK.get('mechanical_manifest_sha256')==hashlib.sha256((MESH.parent/'manifest.json').read_bytes()).hexdigest() and (ROOT/'verify_csi_source.py').exists() and CSI_CHECK.get('verification_source_sha256')==hashlib.sha256((ROOT/'verify_csi_source.py').read_bytes()).hexdigest())
CSI_PASS=CSI_MATCHED and CSI_CHECK.get('declared_rigid_reservation_clear',False)
CSI_OBSTRUCTIONS=', '.join(sorted({h['part'] for row in CSI_CHECK.get('checks',[]) for h in row.get('hits',[])}))
for p in [CSI_CHECK_FILE,ROOT/'verify_csi_source.py']:
    if p.exists():START_HASHES[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
WIRE_CHECK_FILE=MESH.parent/'wire-solid-checks.json'
WIRE_CHECK=json.loads(WIRE_CHECK_FILE.read_text()) if WIRE_CHECK_FILE.exists() else {}
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
    fps_receipt=json.loads(FPS_RECEIPT.read_text())
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
        fj=json.loads(FPS_CHECK_FILE.read_text())
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
DATA={p.stem:json.loads(p.read_text()) for p in MESH.glob('*.json') if p.stem!='manifest'}
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
BASE=['tub','base_grip','tripod_nut','run_button','p_grip']
OPT=['gs_camera','c_cs_adapter','lens_collar']
EVF=['evf_board','hmx039','foam_pad','eyepiece','eyecup']
STACK=['carrier','pi5','cooler','x1203','x1203_kit']
FPS_HARDWARE=[p for p in ('fps_nut','fps_mounting_washer') if p in DATA]
PANEL=['panel','encoder','switch_1824','knob_exp','knob_fps','power_button','power_nut_reserve']+FPS_HARDWARE
FROZEN=json.loads(HDMI_SNAPSHOT.read_text())
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
    fps=json.loads(FPS_INPUT.read_text())
    for part in fps['wire_parts']:
        key='guide_'+part['id'];FPS_WIRES.append(key);DATA[key]=tube_mesh(part['curve']['sampled_centerline'],part['od_mm']/2)
    b=fps['junction']['box'];x0,x1=b['x'];y0,y1=b['y'];z0,z1=b['z']
    DATA['guide_fps_pair']={'vertices':[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]],'faces':[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]}
    FPS_WIRES.append('guide_fps_pair')
    for i,z in enumerate((41,55)):
        key='guide_fps_splice_'+str(i);DATA[key]=cylinder_mesh([-103.5,-23.4,z],[0,0,1],1.5,10);FPS_WIRES.append(key)
CSI_ARROWS=[]
if CSI_MATCHED and CSI_CHECK.get('tool_reservations'):
    tool=CSI_CHECK['tool_reservations'][0];tip=np.array(tool['tip']);back=np.array(tool['axis'])
    DATA['csi_tip_reserve']=cylinder_mesh(tip,back,tool['tip_diameter_mm']/2,tool['tip_length_mm'])
    DATA['csi_shank_reserve']=cylinder_mesh(tip+back*tool['tip_length_mm'],back,tool['shaft_diameter_mm']/2,tool['shaft_length_mm'])
    CSI_ARROWS=[(tip+back*80,tip+back*40)]
# 1
CORE=' x '.join(f'{v:g}' for v in MAN['core_dimensions_mm'])
im,d=page('D2','Assembly and wiring with concealed vents',f'Vertical Pi candidate  |  {CORE} mm core  |  9 printed parts  |  revised review')
scene(im,BASE+OPT+EVF+STACK+PANEL+['lens','cap','usb_stick'],['panel','lens_collar'],rect=(50,170,1100,820))
note(d,'A sequence to test','Pictures expose fit, insertion and service dependencies.\n\nAmber: new part.\nGrey: already present.\nBlue: proposed motion.\nDashed: hidden part.\n\nThe outer plenum is integral to the tub.\n\nNo physical build is qualified.')
stop(d,'All 56 inherited physical gates and M1 remain open. Do not fabricate or energize from this review.')
save(im)
# 2
im,d=page('00','Disconnect before opening','The J2 button requests power control. It does not isolate the battery.')
scene(im,BASE+OPT+EVF+STACK+PANEL+['lens','pack','cap','xt30_pair'],['pack','cap'],offsets={'cap':(0,0,-60),'pack':(0,0,-45)},arrows=[((-48,0,-48),(-48,0,-100))])
note(d,'Four prerequisites','1  Stop recording; clean shutdown.\n\n2  Remove every external supply.\n\n3  Withdraw pack; part XT30 by housings. Protect contacts.\n\n4  Only then touch internal connectors. Use ESD protection. Charge the pack outside the body.')
stop(d,'XT30 must be reachable with body closed and retention fitted. Fixed tied loops cannot unfold for service.')
save(im)
# 3 printed inventory
im,d=page('01','Count the printed parts','Nine compact production parts, each x1. Gauges and plenum / structural coupons are separate test pieces.')
parts=[('tub','1  Tub'),('panel','2  Panel'),('carrier','3  Carrier'),('base_grip','4  Base / grip'),('cap','5  Battery cap'),('eyecup','6  Eyecup'),('knob_exp','7  Exposure knob'),('knob_fps','8  18 / 24 knob'),('lens_collar','9  Lens collar')]
for i,(pid,label) in enumerate(parts):
    x=65+(i%3)*535;y=176+(i//3)*292
    scene(im,[pid],[pid],rect=(x,y,490,226));text(d,x+15,y+231,label,25,True,width=490)
text(d,65,1065,'Same 9 prints; no vent covers or added fasteners. Panel is plain 2.8 mm. Purchased parts are unchanged.',22,color=GRAY)
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
text(d,980,250,'T1   PH1 + torque driver\nT2   Iron + correct insert tip\nT3   Solder / flux / wick + heat gun\nT4   Stripper / cutter\nT5   Meter, thermocouple, calipers\nT6   Fine tweezers + smooth pliers\nT7   Nut tools, saw, file, soft vise\nT8   ESD mat + wrist strap\nT9   Panel prop, shims, rule, gauge\nT10  Bench supply, Pi PSU, charger\nT11  Scope, USB meter, DC load\nT12  Insert-repair pin vise / drills',25,width=610)
stop(d,'Torque and insert process need revised coupons. No threadlocker on ASA. Power-nut tool fit is unmeasured.')
save(im)
# 5
im,d=page('03','Prepare optics and prints','Bench preparation before electronics go inside')
scene(im,['gs_camera','c_cs_adapter','lens','lens_collar'],['lens_collar'],offsets={'lens':(45,0,0),'lens_collar':(22,0,0)},rect=(60,210,1080,700),arrows=[((70,0,60),(35,0,60))])
note(d,'Support the load','Support camera and lens separately. Never react lens torque through PCB or cover.\n\nMeasure back focus and support band. Keep adapter / BFAR witness marks.\n\nBag tripod block after setup. Install inserts before electronics.')
stop(d,'Review the outer plenum on 03v / 03w plus collar and horizontal-bores supports. Measured optics and M1 remain open.')
save(im)
# Plenum section diagrams explain the source geometry; these are not saved-STEP cutaways.
im,d=page('03v','Inspect the concealed outer plenum','Representative sections. Blue arrows show proposed cold/hot paths, not measured airflow. Posts omitted for clarity.')
text(d,65,177,'COLD BAY  /  INTAKE',28,True,width=730)
text(d,865,177,'HOT BAY  /  EXHAUST',28,True,width=730)
draw_plenum_section(d,text,arrow,65,225,730,385,VENT['outer_skin_mm'],VENT['plenum_gap_mm'],VENT['original_side_wall_mm'],flow_in=True)
draw_plenum_section(d,text,arrow,865,225,730,385,VENT['outer_skin_mm'],VENT['plenum_gap_mm'],VENT['original_side_wall_mm'],flow_in=False)
text(d,65,638,f"Rear + underside perimeter mouths feed the cold bay. Four internal wall slots have {VENT['intake_wall_throat_mm2']:.0f} mm2 nominal total area.",25,width=730)
text(d,65,762,f"Gross mouth areas: rear {VENT['cold_rear_mouth_mm2']:.0f} mm2; underside {VENT['cold_bottom_mouth_mm2']:.0f} mm2.",25,width=730)
text(d,865,638,f"Four internal wall slots feed the hot bay: {VENT['exhaust_wall_throat_mm2']:.0f} mm2 nominal total area. Air is intended to leave at front + underside perimeter mouths.",25,width=730)
text(d,865,795,f"Gross mouth areas: front {VENT['hot_front_mouth_mm2']:.0f} mm2; underside {VENT['hot_bottom_mouth_mm2']:.0f} mm2.",25,width=730)
text(d,65,912,f"Side skin {VENT['outer_skin_mm']:g} mm + gap {VENT['plenum_gap_mm']:g} mm + original wall {VENT['original_side_wall_mm']:g} mm. Cavity datum stays Y {VENT['inner_side_y_mm']:g}. Broad-side grille is concealed; perimeter mouths remain.",23,width=1530)
stop(d,'CSI is an explicit service aperture. Direct rear/front views expose mouths. No sealed-flow, dust or water rating.')
save(im)
im,d=page('03w','Print and inspect the outer plenum','Do not fit electronics or inserts until the full air path can be inspected and cleaned.')
scene(im,['tub','panel'],['tub','panel'],offsets={'panel':(0,50,0)},rect=(45,180,850,560),direction=(1,-2,.6))
text(d,65,770,'PRINT HOLD: the front mouth removes edge support at Z5..40. The 10.7 mm gap is not a supported bridge; toolpaths may need about 35 mm bridging, depending on raster direction.',24,True,color=ORANGE,width=805)
text(d,65,920,'Old panel grooves were blind, with 0.2 mm floors. The revised source specifies a plain 2.8 mm skin.',22,width=805)
text(d,960,183,'PRINT AND INSPECT',29,True,width=650)
pose=MAN.get('print_poses',{}).get('tub',{}).get('face_down','unrecorded')
print_steps=[f"1  Current tub STL is {pose}-face down. Inspect the skin, posts, chamber roof and every first bridge in the slicer.",'2  Posts: diameter 1.6 mm, nominal grid 8 mm. Qualify the 48 x 32 grid and 110 x 100 port/CSI crops in the slicer and on the bench; both are geometry-only.','3  No trapped support. If slicing or either coupon fails, add local support webs and repeat the airflow-section checks before any new build trial.','4  Open-edge coupons cannot prove closed-body cleanout. Inspect both actual bays through their mouths using light/mirror or a suitable scope; remove all debris.','5  Check four perimeter mouths and all eight inner-wall slots. If any chamber region cannot be inspected or cleared, stop; do not seal debris inside.']
y=245
for body in print_steps:y=text(d,960,y,body,24,width=650)+23
stop(d,'Blocked slots, roof sag, loose posts or trapped support are rejects. This plenum has no slicer, bridge, cleanout or physical print pass.')
save(im)
# 6
im,d=page('04','Build one removable stack','Prepare J2, battery-pad and header wiring while both board faces remain accessible.')
scene(im,STACK,['carrier'],offsets={'carrier':(0,27,0)},direction=(.7,2,1),arrows=[((-70,42,35),(-70,19,35))],labels=[((-70,47,35),'3')])
note(d,'Keep kit spacing','Fit cooler with its 2 push pins and native fan lead once.\n\nRetain upper 4 x M2.5 x 5 + original standoffs.\n\nLower 4 x M2.5 x 8 pass through carrier. Check thread depth before tightening.\n\n3.4 mm engagement is nominal only.')
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
text(d,90,858,'One 2181120201 + one 2181110202 pair. Both wires are black: trace continuity. Label PWR separately from FPS; their shared key does not prevent cross-connection.',27,width=1490)
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
 note(d,'Three distinct pieces','Nut. Mounting washer. Stop / tang washer.\n\nStop washer shape is not measured and is not drawn. Confirm supplied hardware.\n\nSet two adjacent positions. Meter A / 2: open = 18; closed = 24.\n\nPreserve the stop setting when removing knob, nut and panel.')
 text(d,65,900,'Measure the actual stack before cutting. Proposed shaft length 11.8 mm from mounting face is a fit study; 6.35 mm D shaft / 5.5 mm flat needs a real knob coupon.',26,width=1520)
 stop(d,'Nut / mounting-washer shapes are estimated. Actual stop stack, pin clocking, shaft cut and tool access remain gates.')
 save(im)
if FPS_READY:
 im,d=page('06c','Keep the full FPS harness together','Two donor female GPIO heads + two splices + both factory Molex housings + A / throw 2.')
 scene(im,['switch_1824','hdr_fps_lead_33_34']+FPS_WIRES,['switch_1824','hdr_fps_lead_33_34']+FPS_WIRES,rect=(45,175,1080,715),direction=(1,2,1))
 note(d,'Identify both black wires',('FPS-only CAD group clears; other looms remain gated.\n\n' if FPS_PASS else 'Integrated FPS group clearance awaiting current report.\n\n')+'Male 2181110202: 225 +/- 6 mm exposed stock.\n\nFemale 2181120201: 150 +/- 6 mm exposed stock.\n\n200 mm main axis includes donor stubs / splices.\n\nKeep pair mated in the camera. Bench separation only.')
 text(d,65,900,'Amber cylinders reserve two finished splices, maximum diameter 3 x 10 mm. Cut lengths, solder overlaps, individual-core fanout and terminal joints still require measurement.',26,width=1520)
 stop(d,'Label FPS distinctly from PWR. These same-key connectors can be cross-connected. Stock and study axes are not cut instructions.')
 save(im)
im,d=page('06d','Fit the OS card on the bench','The microSD travels with the removable Pi stack. Closed-panel card access is blocked by the power switch.')
scene(im,['pi5','microsd'],['microsd'],offsets={'microsd':(20,0,0)},rect=(45,175,1090,715),direction=(1,2,.6),arrows=[((-15.9,4.8,33.8),(-35.9,4.8,33.8))])
note(d,'Card before carrier','Prepare and verify the OS image on the bench.\n\nIdentify real contact orientation. Insert -X before the stack enters the body.\n\nLeave the card with the stack during carrier insertion.\n\nFor later card service: isolate all power, remove the panel, then withdraw +X.')
text(d,65,910,'The panel-mounted J2 power switch occupies the card extraction route. The front slit alone does not establish service access.',25,width=1510)
stop(d,'No closed-panel microSD service. Only a panel-off rigid path is checked; real contact orientation and handling remain open.')
save(im)
# 9
im,d=page('07','Join grip and tub','Battery stays out. Route the run lead while the floor passage is open.')
scene(im,BASE,['base_grip','run_button','p_grip'],offsets={'base_grip':(0,0,-22),'run_button':(0,0,-22),'tripod_nut':(0,0,-22)},arrows=[((-55,0,-29),(-55,0,-5))])
note(d,'Independent lock','Fit tripod nut and run button.\n\nEngage keyhole tongues in their actual keyed direction.\n\nUse 1 x PT grip-lock screw.\n\nCheck strap and shifted lock clearances. Panel is not the grip lock.')
stop(d,'Arrow shows approach only. Keyhole engagement, driver access and actual lead passage need dry fitting.')
save(im)
# Show both revised anchors with the complete exported routing proxy.
im,d=page('07b','Thread the strap after the grip lock','12 mm webbing through both upper and heel slots. Shown thickness 1.4 mm is a routing assumption.')
scene(im,BASE+['strap'],['strap'],rect=(45,175,1090,710),direction=(-1,-2,.6))
note(d,'Keep both returns visible','Thread after seating and locking the grip.\n\nThe lower return passes through both heel slots and inside the grip wall.\n\nKeep the cap, battery travel and tripod seat clear.\n\nBuckle, closure overlap and retained tail still need real-part layout.')
text(d,65,910,'This is a full routing proxy, not a webbing cut pattern. Piecewise folds do not prove textile bend radius, hand clearance or physical threading.',25,width=1510)
stop(d,'Neither anchor nor this routing is a rated safety tether. Qualify the actual strap, closure and both anchors before use.')
save(im)
# 10
im,d=page('08','Camera before the carrier','The board cannot be pushed through the installed vertical stack.')
scene(im,BASE+OPT,['gs_camera','c_cs_adapter'],offsets={'gs_camera':(-11.1,65,2),'c_cs_adapter':(-11.1,65,2)},direction=(-1,2,1),arrows=[((-29,60,62),(-29,8,62)),((-29,8,62),(-29,8,60)),((-29,8,60),(-18,8,60))])
note(d,'Three-part motion','1  Approach from +Y with rearward / upward offset.\n\n2  Lower onto seating height.\n\n3  Move lensward to datum.\n\nFit collar with gauge and 3 anchor screws. Support optics throughout.')
stop(d,'Rigid camera path is sampled CAD only. Finger access, tolerances, optical support and torque catch remain open.')
save(im)
# 11
im,d=page('09','Seat the EVF module','Keep OLED foam, native flex and connector latches unstressed.')
scene(im,BASE+OPT+EVF,['evf_board','hmx039','foam_pad'],offsets={'evf_board':(0,45,0),'hmx039':(0,45,0),'foam_pad':(0,45,0)},direction=(-1,2,1),arrows=[((-142,60,78),(-142,13,78))])
note(d,'Keep the board secure','Slide module from +Y into its seats. Support the eyepiece.\n\nThe final panel supplies clamping; do not let the open module fall.\n\nThe straight HDMI head mates upward only after the board seats.')
stop(d,'Native flex contact face follows the actual EVF kit. Do not infer it from a CAD envelope.')
save(im)
# 12
im,d=page('10','Preform HDMI on the bench','3557 right-angle micro-HDMI at Pi  |  intact 300 mm 3562 ribbon  |  3556 straight head at EVF')
# Three full-length poses retain every millimetre of the proposed stock ribbon.
for i,(key,label) in enumerate([('hdmi_strip','Installed'),('hdmi_premate','EVF end free / Pi still mated')]):
    scene(im,[key],[key],rect=(45+i*535,235,510,610),direction=(1,2,1))
    text(d,65+i*535,850,label,25,True,width=510)
note(d,'A full-length study','Each selected pose models 300 mm.\n\nKeep Pi head mated during service.\n\nBoth-end-free pose rejected: power-wire conflict.\n\nR3 / R5 are allowances, not manufacturer limits.')
text(d,70,925,'The complete serpentine strip and both rigid heads must fit through every assembly and service pose.',25,True,width=1520)
stop(d,('Full material clears checked solids; head/carry status is separate. Real bend, clocking, retention and EMI remain open.' if MATERIAL_PASS else 'This 300 mm route needs source-matched exact checks plus real length, clocking, material and EMI tests.'),y=1003)
save(im)
# 13
im,d=page('11','Insert the stack with a free EVF end','Intended trial sequence: Pi HDMI adapter and OS microSD fitted first; recording drive absent.')
carried=STACK+HEADERS+['microsd','hdmi_premate','p_hdmi_pi','p_hdmi_evf','p_usb_pi']+(['switch_1824']+FPS_WIRES if FPS_READY else [])
scene(im,BASE+OPT+EVF+carried,carried,offsets={p:(0,50,-6 if p=='p_hdmi_evf' else 0) for p in carried},arrows=[((-75,70,40),(-75,23,40))])
text(d,70,912,('CAD checked: full HDMI + carried heads at 2 mm poses through +Y70. FPS full mated harness shown separately; remaining loom motions are gated.' if CARRIED_PASS else ('BLOCKED: carried '+CARRIED_OBSTRUCTIONS+'. Geometry must change before this step.' if CARRIED_FAIL else 'Complete HDMI strip + heads shown. FPS full mated harness shown; combined motion remains gated.')),23,color=GRAY,width=1040)
note(d,'Hold before proceeding','Support FPS bushing and stack separately; carry them together from +Y.\n\nFPS pair and Pi HDMI stay mated. EVF HDMI end stays free.\n\nGuide pigtail through floor opening.\n\nSeat carrier; 2 x PT screws. Do not pull leads to seat it.')
stop(d,'Only use a sweep that includes every carried plug and the full ribbon. Bare-stack clearance is insufficient.')
save(im)
# 14
im,d=page('12','Mate HDMI without forcing the ribbon','Storage stays out to preserve access. Hold the adapter body, never pull the ribbon.')
scene(im,EVF+STACK+['hdmi_strip','p_hdmi_pi','p_hdmi_evf'],['hdmi_strip','p_hdmi_pi','p_hdmi_evf'],direction=(-1,2,.6),arrows=[((-145.6,5.5,15),(-145.6,5.5,36))])
text(d,70,912,'Tub omitted for visibility. Adapter blocks are unmeasured catalog envelopes, not detailed keyed connectors.',23,color=GRAY,width=1040)
note(d,'EVF head upward','Bring the straight 3556 head from below.\n\nConfirm the keyed receptacle and actual contact face.\n\nMate fully by its body. Add qualified strain relief clear of the latch.\n\nNo twist to correct a wrong head.')
stop(d,'Upward head travel, fingers / pliers and simultaneous USB + HDMI access must all clear. Final pose is insufficient.')
save(im)
# 15
im,d=page('13','Prove camera connector access','12 x 27 mm R1 CSI opening = 323.14 mm2. All internal work remains unpowered.')
csi_tools=['csi_tip_reserve','csi_shank_reserve'] if CSI_MATCHED and CSI_CHECK.get('tool_reservations') else []
scene(im,['tub']+OPT+EVF+STACK+csi_tools,csi_tools,rect=(50,180,1050,700),direction=(1,-2,.65),arrows=CSI_ARROWS)
text(d,70,885,('Rigid cylindrical reserve clears only; actual tool, cooler and full FPC remain unresolved.' if CSI_PASS else ('Declared cylinders intersect: '+CSI_OBSTRUCTIONS+'. Access remains blocked.' if CSI_MATCHED and CSI_OBSTRUCTIONS else 'No current clear CSI tool reservation. The inherited rotated connector / old side-slot proof is superseded.')),23,color=GRAY,width=1040)
text(d,70,950,f"Intake wall slots: {VENT['intake_wall_throat_mm2']:.0f} mm2 nominal. CSI remains a straight unsealed bypass; keep latch/tool access clear.",21,color=GRAY,width=1510)
note(d,'Actual connector first','Do not cover the CSI opening.\n\nCAM/DISP 1 -> official 22-to-15 FPC -> GS camera.\n\nThe inherited CSI proxy was wrongly oriented. Its old tool pass is rejected.\n\nNew reserve: 4 mm tip / 8 mm shaft at the connector ends.\n\nShow real jaws, latch travel and the complete 200 mm camera FPC before attempting this step.')
stop(d,'OPERATIONAL HOLD: actual cooler outline, latch operation, inserted FPC and interacting flexible looms are unresolved.')

save(im)
# 16 power schematic
im,d=page('13b','Build the detachable EVF feed','Unpowered electrical schematic. Contact identity is traced by continuity, never colour alone.')
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
im,d=page('14','Verify the battery and EVF power paths','Electrical intent only. Bench qualification is required before any full-camera power-up.')
text(d,65,190,'1S2P protected pack',31,True);text(d,65,246,'60 mm 18 AWG lead',25)
arrow(d,(410,243),(565,243));text(d,595,190,'XT30 junction',31,True);text(d,595,246,'Mate by housings',25)
arrow(d,(920,243),(1075,243));text(d,1100,190,'X1203 battery pads',31,True);text(d,1100,246,'Pogo feed -> Pi 5',25)
d.line((170,355,720,355),fill=ORANGE,width=8);d.line((820,355,1430,355),fill=ORANGE,width=8);d.rectangle((720,335,820,375),outline=ORANGE,width=5);text(d,90,331,'+',32,True,color=ORANGE);text(d,90,494,'-',32,True)
text(d,555,427,'Positive: 15 A 0251015.MXL fuse near XT30',28,True,width=820)
d.line((170,515,1430,515),fill=INK,width=8);text(d,65,555,'16 AWG: buy 914.4 mm per colour. Both 270 mm path budgets include unresolved pad-root allowances. Positive also includes 20 mm rigid fuse / joint zone. Copper cuts / overlaps TBD.',29,width=1510)
text(d,65,666,'EVF USB positive -> qualified feed -> EXT+; USB ground -> EVF GND.',29,True,width=1510)
text(d,65,735,'Inherited diode option: 1N5817 band / cathode toward EVF. It does not guarantee the required voltage ceiling. Regulator alternative is not adopted. Trace the actual EVF revision before soldering.',27,width=1510)
stop(d,'Meter polarity / shorts. The 8.6 A / 0.15 V hot-drop gate remains open; the conservative 60 C copper model leaves only about 7 mV margin.')
save(im)
# 17
im,d=page('15','Prove stored slack and disconnection','Complete cable lengths, connector bodies, sleeves and tie heads must fit at the same time.')
scene(im,BASE+STACK+['xt30_pair','pack'],['xt30_pair','carrier'],direction=(1,2,1))
note(d,'No hidden excess',WIRE_CAPTION+'\n\nKeep fuse straight and supported. Keep joints off bends.\n\nFour tie slots are provisions, not a tested retention scheme.\n\nLoops must clear CSI tools, GPIO tails and UPS PCB.\n\nTest pack extraction with retention unchanged.')
stop(d,'If XT30 cannot be parted before opening the body, the assembly is not safely serviceable. Redesign before closure.')
save(im)
# This page is enabled only when the exported mesh is the frozen 21-degree power pose.
if POWER_CURRENT:
    power=json.loads(POWER_SNAPSHOT.read_text());poses=power['rigid_service_poses'];initial=poses[0]
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
# 18
im,d=page('16','Trial panel removal and refit','Opening shown. Reverse the support transfer for refit; keep the FPS pair mated.')
scene(im,BASE+OPT+EVF+STACK+PANEL,PANEL,offsets={p:((0,42,0) if p=='knob_fps' else (0,25,0) if p=='fps_nut' else (0,15,0) if p=='fps_mounting_washer' else (0,0,0) if p=='switch_1824' else (0,8.5,0)) for p in PANEL},arrows=[((-10,30.5,50),(-10,39,50))])
note(d,'Tip, then bushing','FPS stays on its rest.\n\nUse gentle axial tip support for initial 8.5 mm.\n\nOnly 0.5 mm tip then remains; do not pinch it. Transfer support to accessible bushing.\n\nRefit: reverse support transfer. Preserve stop setting; washer, nut and knob go on last.\n\nFPS pair stays mated.')
stop(d,'Never use screws to crush slack into the enclosure. Real shaft grip, stop-stack retention and whole-harness motion remain STOPs.')
save(im)
# 19
im,d=page('17','Recording drive and lens last','Fit selected compact Princeton drive with its protective cap removed. OS microSD is already installed.')
scene(im,BASE+OPT+EVF+STACK+PANEL+['lens','usb_stick'],['usb_stick','lens'],offsets={'usb_stick':(-35,0,0),'lens':(35,0,0)},arrows=[((-188,-7,39),(-156,-7,39))])
note(d,'Straight insertion','Drive travels +X into upper USB3.\n\nOS microSD was fitted on the bench. Later card service requires panel removal.\n\nSupport lens at collar; verify witness marks. Pinch screw is last optical operation.')
text(d,70,912,'Estimated storage-plug keepout omitted: it is not a physical inventory item or a proven mating shape.',23,color=GRAY,width=1040)
stop(d,'Published Princeton size includes cap. Real plug fit and warm sustained >=100 MB/s are not measured.')
save(im)
# Air-path assembly and physical qualification are separate from nominal aperture checks.
im,d=page('17v','Keep ventilation clear during assembly','The outer bays conceal the inner slots. Their pressure loss, leakage, recirculation and cooling remain unmeasured.')
scene(im,['tub','pi5','cooler','carrier'],['tub'],rect=(45,185,850,580),direction=(1,-2,.6))
text(d,65,790,'Tub, stack and illustrative cooler. Panel and looms omitted for visibility; prove clearance with the complete final assembly.',24,color=GRAY,width=805)
hot_sections=[r['section']['free_area_mm2'] for r in VENT_STATE['report']['checks'] if r['id'].startswith('hot_interior_horizontal_section_')]
hot_min=min(hot_sections) if hot_sections else None
summary=VENT_STATE['report']['summary']
status=f"Saved-STEP checks: {summary['pass']} pass / {summary['fail']} fail / {summary['info']} info. "
status+=(f"Smallest sampled hot-bay horizontal cut: {hot_min:.1f} mm2. Mouth totals are not a global flow minimum." if hot_min is not None else 'No sampled hot-bay section is available. Mouth totals are not a global flow minimum.')
text(d,65,880,status,23,True,color=GRAY if VENT_GEOMETRY_PASS else ORANGE,width=805)
text(d,960,183,'BEFORE CLOSURE',29,True,width=650)
text(d,960,242,'Keep mouths, inner slots and baffles clear of the full FPC, EVF feed, power loop, tie heads and fan lead. All loom holds stay open.\n\nCSI stays 12 x 27 mm R1 and uncovered. Its unsealed bypass means not all intake air must reach the cooler.\n\nTest hand, strap and stand occlusion. Blocking the hot underside leaves 210 mm2 front opening for 510 mm2 wall slots. No blocked-vent operation is qualified.',24,width=650)
text(d,960,665,'THERMAL GATE',29,True,width=650)
text(d,960,720,'After electrical prerequisites pass, record ambient, closed-body load, fan speed/duty, component temperatures and throttling at normal hand positions. Compare with the open reference using the same hardware and conditions.\n\nMeasure the actual cooler first; its proxy/source conflict remains open.',24,width=650)
stop(d,'No airflow, fan operating-point, hand-occlusion or thermal pass. All 56 inherited physical gates, M1 and candidate gates stay open.')
save(im)
# 20
im,d=page('18','Close the loop before power','Physical checks and measured records decide whether this candidate can become a build.')
checks=['Pack disconnected during all internal work','Connector identities, contact faces and continuity verified','No trapped ribbon, fuse sleeve, splice, tie head or fan lead','Panel flush; grip lock, strap and optical support secure','Plenum mouths and wall slots clear; no trapped support; CSI open','XT30 disconnect reachable with retention fitted','Required bench gates passed before pack is connected last']
for i,s in enumerate(checks):
 y=205+i*87;d.rectangle((70,y,105,y+35),outline=INK,width=3);text(d,140,y-5,s,30,width=1430)
text(d,70,880,'Then qualify closed-body power, thermal, storage and recording performance, plus revised collar / strap loads. Nothing in this booklet closes a physical gate.',28,width=1510)
stop(d,'56 inherited gates + M1 + candidate gates remain open. No fabrication, safety or performance certification.')
save(im)
# 21
im,d=page('19','Service in dependency order','Always start with page 00 and physical battery disconnection.')
text(d,75,205,'Panel',33,True);text(d,390,205,'FPS knob / nut / mounting washer off -> axial tip support + panel -> initial +Y8.5 -> bushing support -> detach QT / J2; keep FPS pair mated',29,width=1200)
text(d,75,330,'Pi module',33,True);text(d,390,330,'Drive out -X -> panel / EVF junctions detached -> release Pi FPC via qualified CSI access -> free pigtail / fuse -> stage carrier +Y with headers, supported FPS switch and full mated FPS harness; prove run reach',29,width=1200)
text(d,75,500,'Camera',33,True);text(d,390,500,'Support / remove lens -> panel off -> STOP until actual CSI latch release is proved -> Pi FPC free -> carrier removed -> camera FPC free -> reverse camera seating path',29,width=1200)
text(d,75,670,'EVF',33,True);text(d,390,670,'Panel off -> power junction and HDMI body unplugged -> flex protected -> module +Y',29,width=1200)
text(d,75,788,'OS card',33,True);text(d,390,788,'Panel off before in-body microSD withdrawal. Closed-panel route is blocked.',29,width=1200)
text(d,75,870,'Refit',33,True);text(d,390,870,'OS card on bench. Camera before carrier. Junctions before panel. Pack last.',29,width=1200)
stop(d,'CSI tool clearance is not latch qualification. GPIO plugs stay carried; actual FPC release, run slack and wire withdrawal must pass.')
save(im)
# 22 sources & audit
im,d=page('20','Evidence and open checks','Source-linked review candidate. Vendor facts are not real-part measurements.')
text(d,65,180,'Snapshot',30,True);text(d,65,230,f"Mesh export: {MAN.get('built_utc','unknown')}. Generated {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}.",24,width=1510)
text(d,65,286,'Geometry: compact-kowa_lm6hc meshes plus source-bound concealed-vent STEP checks; 300 mm HDMI snapshot. Wiring intent: candidate assembly/BOM and inherited WIRING. The separate receipt records exact source hashes.',24,width=1510)
text(d,65,398,'What the CAD motions check',30,True);text(d,65,448,'Rigid body motions are sampled, not continuous swept-volume proofs. Complete HDMI shapes and carried heads have a separate source-bound check. The source-registered CSI ends have a limited declared-tool check; real cooler, latch and full FPC access remain blocked. Other flexible leads, hands, tolerances and physical retention remain unqualified.',25,width=1510)
text(d,65,581,'Primary sources checked 2026-10-09',30,True)
links=[('Pi J2 and GPIO reference','https://www.raspberrypi.com/documentation/computers/raspberry-pi.html'),('Pi right-angle head 3557','https://www.adafruit.com/product/3557'),('EVF straight head 3556','https://www.adafruit.com/product/3556'),('Intact 30 cm ribbon 3562','https://www.adafruit.com/product/3562'),('Compact Princeton SSD','https://www.princeton.co.jp/product/storage/phdussd.html'),('Lorlin CK rotary switch drawing','https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf'),('USB donor 4448 + supplier drawing','https://www.adafruit.com/product/4448'),('EVF source socket half 2180','https://www.pololu.com/product/2180'),('EVF pin half 2181','https://www.pololu.com/product/2181'),('Molex male assembly drawing','https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/218/218111/2181110201_sd.pdf')]
for i,(name,url) in enumerate(links):text(d,65+(i//5)*790,645+(i%5)*66,name,25,color=BLUE,width=750)
stop(d,'No manufacturer bend limit, purchased cable measurement or production release is invented here.')
save(im)
# Refuse a mixed-generation deliverable if another worker changed a source during rendering.
for p,digest in START_HASHES.items():
    if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest:raise RuntimeError('Source changed during render; rerun after freeze: '+p)
# Assemble image-based PDF; links on evidence page remain clickable.
pdf=OUT/(GUIDE_ID+'.pdf');c=canvas.Canvas(str(pdf),pagesize=(842,595));c.setTitle('D2 vertical assembly and wiring concealed vent review');c.setAuthor('D2 design review')
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
receipt={'guide_identity':GUIDE_ID,'guide_pdf_filename':pdf.name,'nominated_manifest_sha256':ARGS.manifest_sha256,'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'guide_pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'mesh_export_utc':MAN.get('built_utc'),'page_count':len(pages),'sources':{str(p.relative_to(CAD)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Compact Princeton storage and Kowa LM6HC only; unqualified review','physical_gates':'56 inherited + M1 remain open','source_export_mismatches':SOURCE_MISMATCHES,'mesh_files':{n:h for n,h in MAN['files'].items() if n.startswith('meshes/')} }
receipt['page_images']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pages}
receipt['computed_caption_status']={'main_source_matched':MAIN_MATCHED,'cooler_pi_clash':COOLER_CLASH is not None,'hdmi_source_matched':HDMI_MATCHED,'hdmi_selected_full_material_pass':MATERIAL_PASS,'hdmi_carried_pass':CARRIED_PASS,'power_rigid_pass':POWER_PASS,'csi_source_matched':CSI_MATCHED,'csi_cylinder_reserve_pass':CSI_PASS,'wire_source_matched':WIRE_MATCHED,'fps_material_pass':FPS_PASS,'ventilation_source_matched':True,'ventilation_saved_step_geometry_pass':VENT_GEOMETRY_PASS,'ventilation_physical_qualified':False}
receipt['ventilation_review']={'source_report_sha256':hashlib.sha256(VENT_CHECK_FILE.read_bytes()).hexdigest(),'check_summary':VENT_STATE['report']['summary'],'metadata':VENT,'scope':'Saved-STEP plenum and sampled path checks only; no flow, hand-occlusion, thermal or print qualification'}
(OUT/'guide-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(pdf, len(pages),flush=True)
