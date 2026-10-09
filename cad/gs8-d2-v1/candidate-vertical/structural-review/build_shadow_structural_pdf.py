"""Two-page structural supplement from bound review inputs; no CAD or FEA."""
from pathlib import Path
import hashlib,json,html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
P=Path(__file__).resolve().parent;C=P.parent
OUT=P/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
PDF=OUT/'D2-shadow-plenum-structural-supplement.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
d=read(P/'concealed-vent-structural.json');m=read(C/'out/compact-kowa_lm6hc/manifest.json')
vr=C/d['ventilation_report']['path'];v=read(vr)
assert sha(C/'out/compact-kowa_lm6hc/manifest.json')==d['manifest_sha256']
assert d['ventilation_report']['same_manifest'] and d['ventilation_report']['sha256']==sha(vr)
assert v['manifest_sha256']==d['manifest_sha256']
assert d['verification_source_sha256']==sha(P/'update_concealed_vent_structure.py')
ci=C/'vent-study/shadow-plenum-coupon/coupon-index.json';cr=read(ci)
assert cr['manifest_sha256']==d['manifest_sha256'] and cr['coupon_count']==2
sources=[P/'CONCEALED-VENT-STRUCTURAL.md',P/'concealed-vent-structural.json',P/'update_concealed_vent_structure.py',P/'reference-export18-structural-binding.json',C/'out/compact-kowa_lm6hc/manifest.json',vr,ci,Path(__file__)]
start={str(f.relative_to(C)):sha(f) for f in sources}
pdfmetrics.registerFont(TTFont('ReviewSans',str(C.parent/'fonts/DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('ReviewBold',str(C.parent/'fonts/DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('ReviewSans',normal='ReviewSans',bold='ReviewBold')
style={
 'title':ParagraphStyle('title',fontName='ReviewBold',fontSize=22,leading=27,spaceAfter=9),
 'sub':ParagraphStyle('sub',fontName='ReviewSans',fontSize=9.5,leading=13,textColor=colors.HexColor('#4A4A4A'),spaceAfter=12),
 'h':ParagraphStyle('h',fontName='ReviewBold',fontSize=12,leading=16,spaceBefore=12,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='ReviewSans',fontSize=10,leading=14,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='ReviewSans',fontSize=8.4,leading=11.5,spaceAfter=5),
 'hash':ParagraphStyle('hash',fontName='Courier',fontSize=7.4,leading=10,spaceAfter=5),
 'cell':ParagraphStyle('cell',fontName='ReviewSans',fontSize=9,leading=12),
 'head':ParagraphStyle('head',fontName='ReviewBold',fontSize=9,leading=12,textColor=colors.white),
}
def para(text,kind='body'):return Paragraph(text,style[kind])
def add(text,kind='body'):story.append(para(text,kind))
A=d['assembly'];U=d['upper_body'];G=d['grip'];L=d['coupon_load'];R=read(P/'reference-export18-structural-binding.json');CARR=d['carrier'];T=d['printed']
story=[]
add('D2 shadow plenum<br/>structural supplement','title')
add('Compact Kowa candidate | 9 October 2026 | Separate supplement to the historical structural report','sub')
add(f"The selected housing adds <b>{A['delta_mass_g']:.2f} g</b> in the planning mass model. The same analytical assumptions raise J4 floor moment by <b>{U['moment_change_percent']:.2f}%</b> and conservative grip moment by <b>{G['moment_change_percent']:.2f}%</b>. The revised proposed equal-share J4 coupon screen is <b>{L['proposed_rounded_equal_share_screen_Nm']:.2f} N m</b>.")
add('<b>PRINT HOLD:</b> the front mouth removes first-roof frame support over Z5..40. A nominal 10.7 mm distance there is not a two-ended supported span; raster direction may require about 35 mm bridging. The expanded coupon includes it, but slicer, bridge and cleanout evidence remain open.','small')
add('<b>Unqualified review only.</b> No FEA, drop rating, print test or physical strength result is claimed. All 56 inherited physical gates and collar M1 remain open.','small')
rows=[['Planning quantity','Reviewed export18','Shadow plenum'],
 ['Complete mass',f"{A['reference_mass_g']:.2f} g",f"{A['current_mass_g']:.2f} g"],
 ['Tub / panel mass',f"{T['tub']['reference_proxy_mass_g']:.2f} / {T['panel']['reference_proxy_mass_g']:.2f} g",f"{T['tub']['current_proxy_mass_g']:.2f} / {T['panel']['current_proxy_mass_g']:.2f} g"],
 ['Upper-body mass',f"{R['integrated_upper_body_screen']['estimated_mass_g']:.2f} g",f"{U['mass_g']:.2f} g"],
 ['Upper-body 5g floor moment',f"{R['integrated_upper_body_screen']['5g_floor_Mx_Nmm']/1000:.4f} N m",f"{U['floor_moment_5g_Nmm']/1000:.4f} N m"],
 ['Conservative grip 5g moment',f"{R['integrated_comparison_loads']['grip_moment_Nmm']/1000:.4f} N m",f"{G['moment_Nmm']/1000:.4f} N m"],
 ['Carrier payload',f"{CARR['payload_g']:.2f} g",f"{CARR['payload_g']:.2f} g (retained)"]]
table=Table([[para(html.escape(c),'head' if i==0 else 'cell') for c in row] for i,row in enumerate(rows)],colWidths=[240,142,142],hAlign='LEFT')
table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#303B45')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F5F6')]),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story.extend([table,Spacer(1,8)])
cg=A['com_mm'];bbox=A['manifest_mesh_dimensions_mm']
add(f"Estimated complete CoM: ({cg[0]:.2f}, {cg[1]:.2f}, {cg[2]:.2f}) mm. Core: 158 x 63.6 x 100 mm. Manifest mesh-derived complete bounds: {bbox[0]:.2f} x {bbox[1]:.2f} x {bbox[2]:.2f} mm. These are CAD/proxy figures, not a weighed or measured camera.",'small')
add('Assumptions retained','h')
add('Only tub and panel manifest rows change. The upper-body first-moment change is taken from the difference between complete manifests; the excluded lower components stay fixed. Grip screening places the whole assembly mass at the upper-body CoM, with hand reaction at Z=-55 mm. The 1g/3g/5g cases are quasi-static handling sensitivities, not drop ratings.')
add('Tub/panel mass retains ASA density 1.07 g/cm3 and the empirical 0.85 mass factor. That factor is not stiffness or slicer mass. The 12 g connector/fuse/pigtail lump has unresolved distribution; other harness masses remain omitted. Weigh actual parts and the loaded assembly before setting qualification loads.')
add('Retained sections under the new load','h')
add(f"Equal-share J4 nominal lip/head screens are {U['lip_stress_MPa']:.2f}/{U['head_wing_stress_MPa']:.2f} MPa; 30-70% station sharing scales these by 0.6-1.4. Grip gross stresses are {G['nominal_stress_x_y_MPa'][0]:.2f}/{G['nominal_stress_x_y_MPa'][1]:.2f} MPa. The unchanged carrier screen remains {CARR['reinforced_screen']['stress_MPa']:.2f} MPa and {CARR['reinforced_screen']['deflection_mm']:.3f} mm at E=1600 MPa and half of the 5g payload reaction.")
add(f"Adding the retained 12 g-at-Z100 wiring sensitivity gives {L['equal_share_plus_wiring_Nm']:.4f} N m per equally sharing joint. Round upward to the proposed {L['proposed_rounded_equal_share_screen_Nm']:.2f} N m inert-coupon screen after fixture review. The old 0.90 N m target is insufficient; 70% reaction would be {L['seventy_percent_share_plus_wiring_Nm']:.4f} N m and remains a separate unqualified case.")
story.append(PageBreak())
add('Print and thermal holds','title')
add('The selected geometry and its limitations','sub')
add('The 1.6 mm integral skin and support posts cover a 6 mm plenum gap, while the original 2.5 mm wall forms the roof in the -Y-face-down print pose. Keep the current 0.20 mm layer starting point and original part orientations. Nominal 8 mm post spacing does not establish the largest bridge span or two-ended support for every roof extrusion.')
add('Inspect first roof layers, post bonds, sag, slot/mouth area and debris-removal paths in the slicer and actual coupons. The front-mouth band interrupts the frame beneath the first roof layer. Automatic support trapped inside the full plenum is unacceptable. The plain 2.8 mm panel removes four former blind grooves with 0.2 mm floors; it still needs flatness and screw-seat checks.')
add('Two new open-edge coupons','h')
add('Generated STEP/STL inspection crops are 48 x 32 x 10.1 mm (regular grid) and 110 x 100 x 10.1 mm (ports, CSI sleeve, post exclusions and front/top edge regions). Both saved STEP crops are valid single solids. They are separate from the nine production pieces and the prior nine structural coupons. Neither has been sliced, printed or tested. Cut-open edges cannot prove closed-body cleanout; the larger crop omits the complete rear region and does not prove a global maximum unsupported span.')
add('Occlusion and airflow remain unqualified','h')
add('Test unobstructed reference, normal hand positions, fitted strap positions and stand/support contacts separately under the inherited thermal qualification program. Blocking the hot underside mouth leaves only 210 mm2 at the front versus 510 mm2 of hot wall slots, before internal losses. The 534 mm2 gross outlet sum cannot be credited in that case. No rated blocked-vent operation is established.')
add('The smallest named sampled hot horizontal section is 299.4 mm2, not a proven global hydraulic minimum. External cold/hot/CSI void separation excludes the main cavity and does not seal its baffle, CSI bypass or grip communication. Actual cooler registration, fan operating point, complete wiring, pressure loss, useful flow and closed-body battery temperature remain open.')
add('Material and structural scope','h')
add('Retain E=0.8/1.6/2.4 GPa and 5/10/20/30 MPa strength scenarios only as sensitivity cases, never allowables. Layer bonds, notches, preload, warm creep, wear and impact remain unmeasured. Matching unchanged manifest rows is metadata consistency, not a new occupied-solid equivalence test. Old whole-tub/panel zero-difference bindings do not apply to the skin, plenums, divider, posts or CSI sleeve. No factor of safety is certified.')
add('Source receipt','h')
add('Selected mechanical manifest','small');add(d['manifest_sha256'],'hash')
add('Frozen export18 reference manifest','small');add(d['reference_manifest_sha256'],'hash')
add('Saved STEP plenum report SHA-256','small');add(sha(vr),'hash')
def footer(c,doc):
 c.saveState();c.setFont('ReviewSans',8);c.setFillColor(colors.HexColor('#555555'))
 c.drawString(44,25,'Review candidate | '+d['manifest_sha256'][:8]+' | All physical gates remain open')
 c.drawRightString(568,25,str(doc.page));c.restoreState()
doc=SimpleDocTemplate(str(PDF),pagesize=letter,rightMargin=44,leftMargin=44,topMargin=40,bottomMargin=42,title='D2 shadow plenum structural supplement',author='D2 candidate review')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
assert all(sha(C/name)==h for name,h in start.items()), 'Source changed during PDF generation'
r=PdfReader(str(PDF));assert len(r.pages)==2, f'Expected 2 pages, got {len(r.pages)}'
text='\n'.join(x.extract_text() for x in r.pages)
for required in ['864.10','0.95','299.4','210','510',d['manifest_sha256'],'All 56 inherited physical gates']:
 assert required in ' '.join(text.split()), 'Missing PDF text: '+required
receipt={'artifact':PDF.name,'pdf_sha256':sha(PDF),'pages':len(r.pages),'manifest_sha256':d['manifest_sha256'],'source_sha256':start,'text_checks_pass':True,'visual_review':'pending PNG inspection','physical_qualified':False}
(OUT/'structural-supplement-pdf-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(PDF)
