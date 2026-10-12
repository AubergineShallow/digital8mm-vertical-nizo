"""Structural supplement from bound reports; natural pagination, no CAD or FEA.

Build after plenum, coupons, structural calculation and check-scope, in that order.
The receipt remains visually pending until every rendered page is inspected.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from cv_io import read_text, relpath_posix, write_text
import hashlib
import html
import json
from importlib.metadata import version
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
import update_concealed_vent_structure as structural

P = Path(__file__).resolve().parent
C = P.parent
OUT = P/'output/pdf'
PDF = OUT/'D2-shadow-plenum-structural-supplement.pdf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(read_text(path))


def require_hashes(mapping, root):
    for name, expected in mapping.items():
        assert sha(root/name) == expected, 'Stale source or input: ' + name


d = read(P/'concealed-vent-structural.json')
manifest_path = C/'out/compact-kowa_lm6hc/manifest.json'
m = read(manifest_path)
vr = C/d['ventilation_report']['path']
v = read(vr)
scope_path = C/'out/compact-kowa_lm6hc/check-scope-checks.json'
scope = read(scope_path)
audit_path = C/'out/compact-kowa_lm6hc/verification.json'
audit = read(audit_path)
assert sha(manifest_path) == d['manifest_sha256']
assert d['ventilation_report']['same_manifest'] and d['ventilation_report']['sha256'] == sha(vr)
assert v['manifest_sha256'] == scope['manifest_sha256'] == d['manifest_sha256']
assert audit['manifest_sha256'] == d['manifest_sha256'] and audit['scope'] == 'full'
assert audit['verification_source_sha256'] == sha(C/'verify_candidate.py')
assert audit['state_model_sha256'] == sha(C/'steps.py')
stub_rows = [r for r in audit['checks'] if r['category'] == 'roll_catch' and 'stub_case' in r]
stub_windows = [r for r in stub_rows if r.get('item') == 'window']
assert stub_windows, 'No current bonded-stub window rows'
assert all(r['rule'] == 'centred >= 0.30, worst offset >= 0.10' for r in stub_windows), 'Reassess changed catch criterion'
stub_minimum = min(r['worst_gap'] for r in stub_windows)
stub_passes = sum(r['status'] == 'pass' for r in stub_rows)
assert d['verification_source_sha256'] == sha(P/'update_concealed_vent_structure.py')
assert d['inherited_gates'] == structural.ER.inherited_gates(C), 'Inherited gate context is stale'
assert v['verification_source_sha256'] == sha(C/'verify_shadow_plenum.py')
assert scope['verification_source_sha256'] == sha(C/'verify_check_scope.py')
require_hashes(v.get('checked_source_sha256', {}), C)
require_hashes(v.get('helper_source_sha256', {}), C)
require_hashes(scope['helper_source_sha256'], C)
require_hashes(scope['input_sha256'], C.parent)
context = structural.plenum_document_context(m, v, d['manifest_sha256'], sha(vr))
assert context == d['plenum_document_context'], 'Structural plenum context is stale'
assert context['coupons']['same_manifest'], 'Coupon inventory binds another manifest'
bonded_coupon = structural.bonded_coupon_context(d['manifest_sha256'])
assert bonded_coupon == d['bonded_catch_coupon'], 'Bonded-catch coupon context is stale'
assert bonded_coupon['same_manifest'], 'Current bonded-catch coupon is required for this corrective supplement'
joint_receipt_path = C/bonded_coupon['path']
joint_receipt = read(joint_receipt_path)
require_hashes(joint_receipt['input_sha256'], C)
require_hashes(joint_receipt['source_sha256'], C)
require_hashes(joint_receipt['files'], joint_receipt_path.parent)
assert not d['physical_qualified'], 'This builder cannot establish physical qualification'
flow = {row['id']: row for row in scope['checks'] if row['category'] == 'area_parity'}
for name in ('cold_path_min_cut', 'hot_path_min_cut', 'hot_branch_series'):
    assert name in flow, 'Missing current area check: ' + name
sources = [P/'CONCEALED-VENT-STRUCTURAL.md', P/'concealed-vent-structural.json',
           P/'update_concealed_vent_structure.py', P/'reference-export18-structural-binding.json',
           manifest_path, vr, scope_path, audit_path, C/'verify_candidate.py', C/'steps.py', Path(__file__),
           C/'corrective-2026-10-12/RESEARCH-INTEGRATION.md',
           C/'corrective-2026-10-12/materials-and-ribbons-baseline-evidence.txt',
           C/'corrective-2026-10-12/cooler-baseline-evidence.docx',
           C.parent/'fonts/DejaVuSans.ttf', C.parent/'fonts/DejaVuSans-Bold.ttf',
           C/d['inherited_gates']['source'], joint_receipt_path,
           P/'bonded-catch-coupon/README.md']
sources += [C/name for name in context['coupons']['source_sha256']]
start = {relpath_posix(f, C): sha(f) for f in sources}
OUT.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('ReviewSans', str(C.parent/'fonts/DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('ReviewBold', str(C.parent/'fonts/DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('ReviewSans', normal='ReviewSans', bold='ReviewBold')
styles = {
    'title': ParagraphStyle('title', fontName='ReviewBold', fontSize=21, leading=26, spaceAfter=8),
    'sub': ParagraphStyle('sub', fontName='ReviewSans', fontSize=9.5, leading=13, spaceAfter=12),
    'h': ParagraphStyle('h', fontName='ReviewBold', fontSize=12, leading=16, spaceBefore=11, spaceAfter=6, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='ReviewSans', fontSize=10, leading=13, spaceAfter=7),
    'small': ParagraphStyle('small', fontName='ReviewSans', fontSize=8.6, leading=12, spaceAfter=6),
    'hash': ParagraphStyle('hash', fontName='Courier', fontSize=7.1, leading=10, spaceAfter=5),
    'cell': ParagraphStyle('cell', fontName='ReviewSans', fontSize=8.9, leading=12),
    'head': ParagraphStyle('head', fontName='ReviewBold', fontSize=8.9, leading=12, textColor=colors.white),
}
story = []
required = []


def para(text, kind='body'):
    return Paragraph(text, styles[kind])


def add(text, kind='body'):
    story.append(para(text, kind))


def table(rows, widths):
    result = Table([[para(html.escape(str(cell)), 'head' if i == 0 else 'cell') for cell in row]
                    for i, row in enumerate(rows)], colWidths=widths, hAlign='LEFT', repeatRows=1)
    result.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#303B45')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F5F6')]),
        ('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#D9D9D9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([result, Spacer(1, 8)])


A, U, G, L, CAR, T = (d[k] for k in ('assembly', 'upper_body', 'grip', 'coupon_load', 'carrier', 'printed'))
R = read(P/'reference-export18-structural-binding.json')
vent = m['ventilation']
mat = d['material_sensitivity']['asa_density']
gates_text = f"All {d['inherited_gates']['open']} inherited physical gates"
add('D2 shadow plenum structural supplement', 'title')
add('Compact Kowa review | Corrective documentation 12 October 2026 | Separate from the historical structural report', 'sub')
add(f"The selected candidate changes the planning mass by <b>{A['delta_mass_g']:+.2f} g</b> relative to export18. "
    f"J4 floor moment changes by <b>{U['moment_change_percent']:+.2f}%</b> and conservative grip moment by "
    f"<b>{G['moment_change_percent']:+.2f}%</b>. The proposed compact equal-share J4 coupon screen is "
    f"<b>{L['proposed_rounded_equal_share_screen_Nm']:.2f} N m</b>; the all-variant screen is "
    f"<b>{L['all_variants_screen_Nm']:.2f} N m</b>. These are analytical screening loads, not qualified capacities.")
add('<b>PRINT AND POWER HOLD.</b> No FEA, drop rating, print test, adhesive qualification or physical strength result is claimed. '
    + gates_text + ' and M1 remain open. All four plenum mouths, roof layers and bonded catch require physical evidence.', 'small')
add('Planning mass and load comparison', 'h')
rows = [['Quantity', 'Reviewed export18', 'Selected candidate'],
        ['Complete mass', f"{A['reference_mass_g']:.2f} g", f"{A['current_mass_g']:.2f} g"],
        ['Tub / panel mass', f"{T['tub']['reference_proxy_mass_g']:.2f} / {T['panel']['reference_proxy_mass_g']:.2f} g",
         f"{T['tub']['current_proxy_mass_g']:.2f} / {T['panel']['current_proxy_mass_g']:.2f} g"],
        ['Upper-body mass', f"{R['integrated_upper_body_screen']['estimated_mass_g']:.2f} g", f"{U['mass_g']:.2f} g"],
        ['Upper-body 5g floor moment', f"{R['integrated_upper_body_screen']['5g_floor_Mx_Nmm']/1000:.4f} N m", f"{U['floor_moment_5g_Nmm']/1000:.4f} N m"],
        ['Conservative grip 5g moment', f"{R['integrated_comparison_loads']['grip_moment_Nmm']/1000:.4f} N m", f"{G['moment_Nmm']/1000:.4f} N m"],
        ['Carrier payload', f"{CAR.get('reference_payload_g', CAR['payload_g']):.2f} g", f"{CAR['payload_g']:.2f} g"]]
table(rows, [240, 142, 142])
cg = ', '.join(f'{n:.2f}' for n in A['com_mm'])
core = ' x '.join(f'{n:g}' for n in A['core_dimensions_mm'])
bbox = ' x '.join(f'{n:.2f}' for n in A['manifest_mesh_dimensions_mm'])
add(f'Estimated complete CoM: ({cg}) mm. Core: {core} mm. Manifest mesh-derived bounds: {bbox} mm. '
    'These are CAD/proxy estimates, not a weighed or measured camera.', 'small')
add('Free body and retained sections', 'h')
add(html.escape(d['geometry_scope']))
add('<b>Upper-body method:</b> ' + html.escape(U['free_body']) + '. The lower grip and battery are excluded from J4 upper-body '
    'loading. Grip screening places the entire assembly mass at the upper-body CoM, with hand reaction at '
    f"Z={G['hand_plane_z_mm']:g} mm. The 1g/3g/5g cases are quasi-static handling sensitivities.")
add(f"Equal-share J4 nominal lip/head stresses are {U['lip_stress_MPa']:.2f}/{U['head_wing_stress_MPa']:.2f} MPa; "
    f"30-70% station sharing scales them by 0.6-1.4. Grip gross nominal stresses are "
    f"{G['nominal_stress_x_y_MPa'][0]:.2f}/{G['nominal_stress_x_y_MPa'][1]:.2f} MPa. "
    f"The carrier screen is {CAR['reinforced_screen']['stress_MPa']:.2f} MPa and "
    f"{CAR['reinforced_screen']['deflection_mm']:.3f} mm at E=1600 MPa and half the 5g payload reaction. "
    'Where carrier mass changes, these retained-arm results scale with payload. Contact, root notches, screws, slip, wear, '
    'anisotropy, warm creep and service pulls remain unqualified.')
add('Coupon load coverage', 'h')
add(f"The retained {L['wiring_mass_sensitivity_g']:g} g wiring-location sensitivity at Z={L['wiring_upper_height_mm']:g} mm "
    f"gives {L['equal_share_plus_wiring_Nm']:.4f} N m per equally sharing compact joint. The old 0.90 N m target "
    + ('covers' if L['old_0_90_Nm_covers_equal_share_plus_wiring'] else 'does not cover') + ' that case. '
    f"A 70% station reaction gives {L['seventy_percent_share_plus_wiring_Nm']:.4f} N m and remains a separate unqualified case.")
rows = [['Variant', 'Equal-share + wiring', '70% station reaction']]
for name, row in L['per_variant'].items():
    rows.append([name.replace('_', ' '), f"{row['equal_share_plus_wiring_Nm']:.4f} N m" if row['valid'] else 'Invalid free body',
                 f"{row['seventy_percent_share_plus_wiring_Nm']:.4f} N m" if row['valid'] else 'Not calculated'])
table(rows, [240, 142, 142])
add(f"The rounded all-variant equal-share screen is {L['all_variants_screen_Nm']:.2f} N m, governed by "
    f"{html.escape(L['governing_variant'])}. Fixture capacity and procedure need review before an inert-coupon test. "
    'C08/C09 omit the rear joint, independent lock and full tub; a local result cannot establish a whole-camera rating.')
add('Plenum geometry and physical print holds', 'h')
add(html.escape(vent['revision']) + '. ' +
    f"The skin is {vent['outer_skin_mm']:g} mm, the gap {vent['plenum_gap_mm']:g} mm and the inner wall "
    f"{vent['original_side_wall_mm']:g} mm. The wall becomes a roof in the tub's -Y-down print pose. "
    'Keep the 0.20 mm layer baseline and declared orientations as starting conditions. Geometric bridge checks do not '
    'prove slicer direction, first-layer continuity, pillar bonds, sag or debris removal. Trapped automatic supports are unacceptable.')
add(structural.coupon_description(context))
add('Measured area and occlusion scope', 'h')
rows = [['Saved-STEP geometric quantity', 'Area', 'Reported status']]
for name in ('cold_path_min_cut', 'hot_path_min_cut'):
    row = flow[name]
    rows.append([name.replace('_', ' '), f"{row['min_cut_mm2']:.2f} / {row['wall_ports_mm2']:.2f} mm2", row['status'].upper()])
row = flow['hot_branch_series']
rows.append(['Hot parallel branch series screen', f"{row['effective_sum_mm2']:.2f} / {row['wall_ports_mm2']:.2f} mm2", row['status'].upper()])
table(rows, [280, 152, 92])
add('Path minimum cut is a geometric graph-capacity screen over the saved tub, not a fan operating point or measured flow. '
    'The series screen samples named sections; neither gives pressure loss or temperature. A PASS here closes only its stated geometric rule.')
add(structural.blocked_hot_mouth_description(context))
add('Test unobstructed operation, normal hand positions, fitted straps and stand/support contacts separately. External bay '
    'separation excludes the main cavity and does not seal the baffle, CSI bypass or grip communication. Actual cooler '
    'registration, lead sweep, complete wiring, useful flow, SSD temperature and closed-body battery temperature remain open.')
add('Materials bonds and ribbon evidence', 'h')
add(structural.selected_catch_description(context))
add(f"The current full main audit records {stub_passes}/{len(stub_rows)} passing bonded-stub checks. "
    f"Its minimum reported tilted-window clearance is {stub_minimum:.3f} mm against the unchanged 0.100 mm criterion, "
    f"giving {stub_minimum - 0.100:.3f} mm nominal headroom. This small modeled margin does not establish tolerance-robust "
    'manufacture. Print variation, seating, adhesive film/cure, datum movement and warm creep remain physical HOLDs.')
add(structural.bonded_coupon_description(bonded_coupon))
add(f"The mass model retains ASA {mat['inherited_g_cm3']:.2f} g/cm3 and the empirical 0.85 factor. Polymaker's reference density "
    f"is {mat['manufacturer_reference_g_cm3']:.2f} g/cm3: <b>+{mat['contribution_change_percent']:.1f}% to the ASA contribution</b> "
    'at fixed volume and factor. This is not the same percentage increase in complete-camera mass, and no new grade or density '
    'is adopted. Actual print and harness weights are needed before final CoM and load qualification.')
add('Retain E=0.8/1.6/2.4 GPa and 5/10/20/30 MPa strength scenarios as sensitivities only. Published tensile results and HDT '
    'do not establish D2 allowables, warm creep, loaded-service temperature or a safety factor. Exact filament grade/process, '
    'epoxy SKU/preparation/bondline/cure and the actual camera, HDMI and OLED ribbon minimum bend radii remain unknown.')
add('A deeper bonded engagement may improve the geometric tolerance screen while retaining its datum-tilt test; it still needs '
    'production-pose coupons with the selected epoxy, hot dwell and measured permanent shift. No supplier ribbon bend limit '
    'is inferred from a different cable family. Confirm seating, latch access, strain relief, continuity and full-mode operation '
    'on the actual routed parts.')
add('Source identity and research applicability', 'h')
add('Calculation: concealed-vent-structural.json. Mouths: shadow-plenum-checks.json. Path and series areas: '
    'check-scope-checks.json. Bonded-stub rows: the current full verification.json. Coupon dimensions and validity: the current coupon index and its individual receipts. '
    'The machine-readable PDF receipt binds each source hash and records visual review separately.', 'small')
add('The 12 October materials/ribbons and cooler research describe preserved baseline bdfd44fc and identify evidence gaps. '
    'The accompanying RESEARCH-INTEGRATION.md maps their conclusions to this corrective review; baseline geometry figures '
    'are not carried forward as current measurements. Manufacturer sources include '
    '<link href="https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa">Polymaker ASA data</link>, '
    '<link href="https://www.raspberrypi.com/documentation/accessories/camera.html">Raspberry Pi camera instructions</link>, '
    '<link href="https://www.adafruit.com/product/3562">Adafruit 3562</link> and '
    '<link href="https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-product-brief.pdf">the Active Cooler brief</link>.', 'small')
add('Selected mechanical manifest', 'small')
add(d['manifest_sha256'], 'hash')
add('Frozen export18 reference manifest', 'small')
add(d['reference_manifest_sha256'], 'hash')


def footer(c, doc):
    c.saveState()
    c.setFont('ReviewSans', 8)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawString(44, 25, 'Review candidate | ' + d['manifest_sha256'][:8] + ' | Physical gates remain open')
    c.drawRightString(568, 25, str(doc.page))
    c.restoreState()


doc = SimpleDocTemplate(str(PDF), pagesize=letter, rightMargin=44, leftMargin=44, topMargin=40, bottomMargin=42,
                        title='D2 shadow plenum structural supplement', author='D2 candidate review', invariant=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
assert all(sha(C/name) == expected for name, expected in start.items()), 'Source changed during PDF generation'
reader = PdfReader(str(PDF))
assert reader.pages and all((p.extract_text() or '').strip() for p in reader.pages), 'Empty PDF page'
text = ' '.join('\n'.join(p.extract_text() or '' for p in reader.pages).split())
required = [f"{A['current_mass_g']:.2f} g", f"{L['proposed_rounded_equal_share_screen_Nm']:.2f} N m",
            f"{L['all_variants_screen_Nm']:.2f} N m", f"{context['coupons']['count']} source-bound",
            f"{context['physical_print_pieces']} physical production prints", f"{mat['manufacturer_reference_g_cm3']:.2f} g/cm3",
            f"+{mat['contribution_change_percent']:.1f}%",
            d['manifest_sha256'], gates_text, 'PRINT AND POWER HOLD', f'{stub_minimum:.3f} mm', f'{stub_minimum - 0.100:.3f} mm nominal headroom']
required += [f"{flow[name]['min_cut_mm2']:.2f} / {flow[name]['wall_ports_mm2']:.2f} mm2"
             for name in ('cold_path_min_cut', 'hot_path_min_cut')]
for token in required:
    assert token in text, 'Missing PDF text: ' + token
receipt = {'artifact': PDF.name, 'pdf_sha256': sha(PDF), 'pages': len(reader.pages),
           'manifest_sha256': d['manifest_sha256'], 'source_sha256': start,
           'document_toolchain': {'pypdf': version('pypdf'), 'reportlab': version('reportlab')},
           'text_checks_pass': True, 'text_checks': required,
           'visual_review': 'pending PNG inspection', 'physical_qualified': False}
write_text(OUT/'structural-supplement-pdf-receipt.json', json.dumps(receipt, indent=2) + '\n')
print(PDF)
