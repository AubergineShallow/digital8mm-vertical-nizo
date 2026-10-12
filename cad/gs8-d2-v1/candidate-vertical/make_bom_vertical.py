# SPDX-License-Identifier: MIT
"""Generate the unpriced vertical review BOM without importing or executing CAD.

Run from any directory: python path/to/make_bom_vertical.py [--check]
Reads the unchanged baseline make_bom.py LINES only; never invokes its write().
Installed quantities, purchases and included-kit detail are distinct fields.
"""
from cv_io import read_text, write_text
import evidence_rules as ER  # FP-04 (VN-08): repeated figures come from their source rows; CAD-free
import wiring_data as WD     # FP-14 (VN-61/63/64): J2 family, junctions, spares, buy split, wire SKUs; CAD-free
import harness_rules as HR   # Current pigtail failure bounds, not the superseded nominal-only estimate.
from pathlib import Path
import argparse
import csv
import importlib.util
import io
import json
import hashlib
import sys

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = ROOT / 'electronics/gs8-d2-v1/make_bom.py'
BASELINE_COMMIT = 'd38468e58eb2b02d56743e2e0cfdd8f780818a65'
SOURCES = {
 'storage': 'https://www.princeton.co.jp/product/storage/phdussd.html',
 'storage_studied_samsung': 'https://download.semiconductor.samsung.com/resources/data-sheet/2024_Samsung_Data_sheet_UFD_FIT_Plus_v1.2_10139817901318.pdf',
 'power': 'https://www.adafruit.com/product/1505',
 'power_drawing': 'https://cdn-shop.adafruit.com/datasheets/R13diagram.jpg',
 'picoblade_female': 'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/218/218112/2181120201_sd.pdf',
 'picoblade_male': 'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/218/218111/2181110201_sd.pdf',
 'picoblade_spec': 'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/510/51021/510211009-PS-000.pdf',
 'fps_switch': 'https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf',
 'fps_stop': 'https://www.mouser.com/catalog/specsheets/CK2373-6.35X17.5MM-D-SHAFT-Lorlin-datasheet-160875.pdf',
 'gpio_donor': 'https://www.adafruit.com/product/1950',
 'usb_donor': 'https://www.adafruit.com/product/4448',
 'usb_donor_drawing': 'https://cdn-shop.adafruit.com/product-files/4448/C14289-001_datasheet.pdf',
 'evf_socket': 'https://www.pololu.com/product/2180',
 'evf_pin': 'https://www.pololu.com/product/2181',
 'j2': 'https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#add-your-own-power-button',
 'hdmi_adapter': 'https://www.adafruit.com/product/3556',
 'hdmi_pi_adapter': 'https://www.adafruit.com/product/3557',
 'hdmi_ribbon': 'https://www.adafruit.com/product/3561',
 'hdmi_original_ribbon': 'https://www.adafruit.com/product/3562',
 'wire': 'https://www.progressiverc.com/products/prc-silicone-wire-16-awg',
 'wire_variants': 'https://www.progressiverc.com/products/prc-silicone-wire-16-awg.json',
}
FIELDS = ['section', 'line', 'item', 'variant', 'status', 'installed_qty', 'installed_unit',
          'purchase_qty', 'purchase_unit', 'spare_or_remainder', 'included_in', 'sku_or_class',
          'supplier', 'layout_id', 'note', 'source']


def baseline():
    spec = importlib.util.spec_from_file_location('vertical_baseline_bom', BASELINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert 'cadquery' not in sys.modules, 'BOM generation must remain CAD-free'
    return mod


def export18_power():
    """Frozen export18 rigid-power counts, formatted from that report's row (FP-04, VN-08)."""
    c = ER.power_counts(json.loads(read_text(HERE / 'history/reviewed-export18/power-service-checks.json')))
    return dict(poses=c['poses'], queries=c['queries'], hits=c['hits'] or 'zero')


def build_rows():
    base = baseline()
    drop = HR.pigtail_drop_row()
    drop_note = (f"Current source-bound model at {drop['i_peak_a']:g} A: {drop['drop_lo_v']:.5f} to {drop['drop_hi_v']:.5f} V against unchanged {drop['limit_v']:.3f} V; status {drop['status']}. The high case includes hot fuse and vendor-minimum copper. The earlier nominal-only 0.142811 V estimate is insufficient. 270 mm is blocked by full reach and hot-drop; proposed changes remain pending, with no wire/fuse/connector substitution authorized. " )
    rows = []
    for sec, lid, item, qty, unit, sku, supplier, _pid, _est, ref, _note in base.LINES:
        outside = sec in (base.S_CO, base.S_TO)
        r = dict(section=sec, line=lid, item=item, variant='both', status='inherited; unqualified',
                 installed_qty=0 if outside else qty, installed_unit=unit,
                 purchase_qty=qty, purchase_unit=unit, spare_or_remainder='', included_in='',
                 sku_or_class=sku, supplier=supplier, layout_id=ref or '',
                 note='Inherited specification; baseline source line '+lid+'. Candidate assembly sequence supersedes baseline step numbers.',
                 source='../../../electronics/gs8-d2-v1/make_bom.py')
        if outside:
            r['note'] = ('Workshop supply; amount consumed in the candidate is not yet measured.' if sec == base.S_CO
                         else 'Workshop equipment, not an installed camera part; retained from baseline scope.')
        if qty == 0:
            r['status'] = 'optional; not adopted'
        rows.append(r)
    by = {r['line']: r for r in rows}
    def change(lid, **kw):
        by[lid].update(kw)
    def add(lid, sec, item, installed, purchase, unit='ea', **kw):
        r = dict(section=sec, line=lid, item=item, variant='both', status='candidate; unqualified',
                 installed_qty=installed, installed_unit=unit, purchase_qty=purchase, purchase_unit=unit,
                 spare_or_remainder='', included_in='', sku_or_class='class; confirm on receipt',
                 supplier='unselected', layout_id='', note='', source='model.py')
        r.update(kw); rows.append(r); by[lid] = r
    change('D2-01', item='Raspberry Pi 5, 8 GB', note='Same board, physically rolled into a vertical XZ PCB plane; no replacement compute platform.')
    change('D2-02', note='The official Raspberry Pi Active Cooler remains selected, confirmed for this followup; no cooler substitution. Its present perimeter, underside and push-pin geometry/registration are approximate proxies. The retained interference with the detailed official Pi STEP is an unresolved model/registration conflict, not proof that the official cooler is incompatible. Actual enclosure fit, fan-lead/service clearance, airflow and thermal qualification remain HOLD.')
    change('D2-03', note='One UPS purchase includes four standoffs and eight original M2.5 x 5 screws. Install four original upper screws and four replacement M2.5 x 8 lower screws (V-31); bag the four removed lower screws. Included detail below is not another purchase.')
    change('D2-04', note='Fit the OS card on the bench before carrier insertion; it stays with the carried stack. The closed-panel +X extraction path intersects the panel-mounted power-switch body. Remove the panel and verify actual reach before withdrawing the card, or service it on the bench with the complete module. The panel-off sweep is not a closed-body access pass.')
    change('D2-05', note='C-CS adapter included. Remove tripod block and its two supplied screws at supported optical bench setup; bag them. Never react lens torque through PCB or cover.')
    change('D2-06', note='Default review geometry only; final lens decision and measured support band remain open. M1 remains open for the revised collar.')
    change('D2-06b', note='Alternative, not an additional installed lens. Requires its own measured support band and collar; no baseline CoM claim is carried into the vertical candidate.')
    change('D2-07', note='One kit purchase covers OLED emitter, driver board and native flex; included detail below is not a second purchase. Identity, power range and flex/service gates remain open.')
    change('D2-09', variant='original only', installed_qty=1, purchase_qty=1, status='fallback; unqualified',
           note='SDCZ880-256G retained only with 185 mm original-storage body and sleeve. Do not buy with V-09 for one camera. Warm sustained G-W10 still required.')
    change('D2-10', note='Bridge A0 to select I2C address 0x37; same exposure control.')
    change('D2-11', item='18/24 selector: Lorlin CK1044 imperial PCB rotary switch with adjustable stop',
        sku_or_class='Lorlin CK1044', supplier='Lorlin / authorized distributor', source=SOURCES['fps_switch'],
        status='conditional corrected selection; physical integration/service unqualified',
        note='Replaces inconsistent inherited CK1049/6.35D description. CK1044 is 1 pole, 12 positions, BBM, silver contacts, PCB pins, standard 30-degree indexing; set supplied stop/tang washer to two adjacent positions and verify continuity. Body diameter 27.5 mm, mounting face to rear body 14.1 mm and PCB pin ends 18.1 mm. Preserve all 13 terminals, including unused ones; actual pin section/clocking remain receipt gates. Imperial bushing 9.52 mm x 32 TPI projects 8 mm; shaft diameter 6.35 mm, across-flat 5.5 mm, stock length 38 mm from mounting face with 30 mm end flat. Proposed cut 11.8 mm from mounting face gives about 3.55 mm flat engagement after 0.25 mm bushing clearance; measure actual stack before cutting and coupon-test knob fit/removal force. Corrected candidate knob is 24 mm diameter, with adjacent 30-degree detent markings. Common A and throw 2 give open/high 18 and closed/low 24 under existing software, only after real continuity confirms numbering. Nut, mounting washer and stop/tang washer are separate planned constituents; mounting-washer inclusion and all hardware dimensions remain receipt gates. Do not lose or reset the stop ring during knob/nut/panel removal.')

    change('D2-12', note='Prewired record/run button; its lead is included, not a separate purchase. GPIO26, pins 37/39 unchanged.')
    change('D2-13', note='Pack, BMS, existing 60 mm 18 AWG lead and XT30 male retained. Check the numeric R-PACK-BMS specification in baseline WIRING; no 2S or other power architecture substitution. Battery is physically disconnected before any internal service.')
    change('D2-14', installed_qty=1, installed_unit='female connector', spare_or_remainder='1 spare female + 2 loose male connectors when pack already has its male',
           note='Buy two pairs as baseline provision. Fit one female to the camera pigtail; pack-side male is included with D2-13. Loose males are not additionally installed; one can replace a missing pack male (+2 joints).')
    change('D2-14F', installed_qty=1, spare_or_remainder='1 spare fuse', note='Retain 15 A axial fuse near the XT30 female in the positive pigtail conductor. ONE installed inline fuse; legacy side-mounted duplicate is removed from the proxy. Frozen 21-degree yaw/45-degree pitch pose and source-driven swept floor passage are integrated. Export18 rigid-power report: {poses} poses/{queries} queries/{hits} hits. This is not a complete flexible-harness service pass. Flexible-path deployment, actual copper cuts/overlaps, pad/pin exits, retention and hot-drop remain STOPs; positive 270 mm finished path includes the 20 mm rigid fuse/joint-sleeve zone.'.format(**export18_power()))
    change('D2-15', note='Same hand strap; upper anchors move 12 mm in Y and 18.5 mm rearward in X. Check access with the strap installed.')
    change('D2-16', installed_qty=1, spare_or_remainder='1 spare diode', note='Baseline EVF feed provision only; G-W6 remains open. The vertical redesign does not qualify this feed or adopt the optional regulator.')
    for lid in ('D2-16R', 'D2-16D', 'D2-16C', 'D2-16P'):
        change(lid, note='Baseline EVF-feed option C retained at quantity zero; not adopted. See WIRING section 4.8 and G-W13. No geometry, power or thermal qualification is implied.')
    # H1 (VN-60 / FP-11f): r7's ko_5v_up keep-out does not exist in the candidate; the carrier reserve sits on the route.
    change('D2-16P', item=by['D2-16P']['item'].replace('inside ko_5v_up by box arithmetic',
                                                       'reserved on the installed usb_5v route (routes.py FEED_VOLUMES)'),
           note='Baseline EVF-feed option C retained at quantity zero; not adopted (default pending user decision 10, VN-80). '
                'Its 16 x 7.5 x 4.5 mm reserve is kept free on the installed usb_5v route, centred in the diode splice zone it '
                'would replace (harness feed_volumes usb_5v_option_c_reserve). See WIRING section 4.8 and G-W13. No power or '
                'thermal qualification is implied.')
    change('D2-20', status='source-corrected port; operational FPC access HOLD', note='Export18 uses source-registered CAM/DISP 1 and a 12 x 27 mm R1 slot, nominal area 323.14 mm2. The inherited rotated CSI proxy and prior tool pass are superseded. Official 200 mm cable retained; full material route remains unplaced. Both declared cylindrical reservations clear the selected saved solids; the retained straight opening remains an unsealed cooling bypass; this does not qualify actual latch/jaws, cooler outline, stiffeners, contact orientation or cable withdrawal.')
    change('D2-21', installed_qty=0, purchase_qty=0, status='replaced in both vertical variants',
           note='Replaced by one V-21 straight EVF head, one V-21P right-angle Pi head and one V-22O 300 mm ribbon in either body variant. V-22 200 mm ribbon is rejected at quantity zero. One old molded cable becomes three purchased pieces, net +2 pieces.')
    change('D2-22', item='USB-A power-feed donor: Adafruit 4448 four-core breakout cable, cut to verified route',
        sku_or_class='Adafruit 4448 / C14289-001', supplier='Adafruit', source=SOURCES['usb_donor_drawing'],
        status='conditional donor; source-registered USB2 reservation, actual plug/route unqualified',
        spare_or_remainder='Four removed jumper ends and unquantified wire offcuts; not installed parts',
        note='One purchased cable. Catalog says 300 mm; supplier drawing says 325 +/- 10 mm, 4 x 28 AWG copper (7/0.12), jacket OD 3.6 mm and 25 mm breakout. This explicitly replaces the inherited generic 24-26 AWG lead. The old 200 mm is a route allocation, not purchased length or a cut instruction. Retain the conservative full plug/bend reserve: overmold, strain relief and wire-exit dimensions are unpublished, so no exact fit/exit claim. Red VBUS and black GND only; individually insulate unused white D- and green D+ with TWO separate sleeves, plus shield insulation only if a shield is present. No data connection. Verify every conductor by continuity. Export18 places the estimated head at source-registered USB2; the rejected RJ45-row pose is historical. Actual plug/exit measurements and the full cable/service route remain unresolved. Retain the inline diode; final donor/RCY copper cuts, overlaps and storage are TBD. G-W6 must recheck EVF voltage/drop/heating at measured current with the 28 AWG donor.')
    change('D2-23', item='EVF power-only inline pair: Pololu 2180 socket-contact half + 2181 pin-contact half',
        sku_or_class='Pololu 2180 + 2181, Generic RCY-style; one of each', supplier='Pololu', source=SOURCES['evf_socket'],
        status='conditional matched Generic pair; no JST rating inherited', installed_qty=1, purchase_qty=1,
        installed_unit='matched pair', purchase_unit='pair (one 2180 and one 2181)', spare_or_remainder='No spare pair provision; actual tail offcuts TBD',
        note='Replaces unsupported PH wire-to-wire pair, not an EVF board socket. Buy ONE 2180 and ONE 2181. Both have nominal 100 mm 20 AWG silicone tails, stripped/tinned; trim only after complete routing and joint budgets are verified. Use 2180 recessed SOCKET contacts on USB source side, 2181 on the EVF board side; confirm actual mating/continuity and insulate when separated. Brand is explicitly Generic; no current/contact-resistance/OD/tolerance rating is published and JST specifications must not be borrowed. Vendor housing lengths are 13 mm and 19 mm; reserve their full sum 32 mm axially, width 7 mm and provisional thickness 7 mm until actual mated geometry is measured. This is a planning reserve, not a guaranteed vendor bound. Keep straight exit space and real disconnect access. Distinct family prevents mating to PicoBlade signal pairs; label EVF polarity. Preserve G-W6 voltage/drop, contact heating, pull retention and insulation gates. Two housings and four factory contacts are included below; no crimper. The EVF board receives two soldered pigtail joints at traced EXT+/GND pads.')
    change('D2-24', installed_unit='retained socket-end lead section', note='Join to D2-24B by pin-number continuity, not colour alone; four QT splice joints. Finished QT lead 250 +/- 10 mm. Complete 240-260 mm stored-length routes and a separate free route for minimum mating reach must both be qualified. The free curve plus 24 mm allowance is a reach budget, not a depiction of all stored cable. Four splice sleeves, roots and the full flexible transition remain open.')
    change('D2-24B', installed_unit='retained SH-end lead section', note='One purchased cable contributes the SH end; offcut is not another harness. Combined finished lead is 250 +/- 10 mm with D2-24.')
    change('D2-25', item='GPIO donor jumpers: two cut female-ended stubs from Adafruit 1950 pack',
        status='conditional new-build donor; measured cut/fit gates open', installed_qty=2, installed_unit='female-ended donor stubs; installed lengths TBD',
        purchase_qty=1, purchase_unit='pack of 20 female/female 150 mm jumpers', sku_or_class='Adafruit 1950', supplier='Adafruit', source=SOURCES['gpio_donor'],
        spare_or_remainder='18 intact jumpers plus two removed ends and unquantified wire offcuts',
        note='Use two distinct colours for GPIO13 pin 33 and ground pin 34. Each stock jumper has 2.54 mm female contacts at both ends and 28 AWG wire (7 strands of 36 AWG). Retain one female housing/contact on each selected jumper; cut measured stubs and join to trimmed blunt-ended PicoBlade male wires using TWO solder splices and TWO insulating sleeves. Included housing/contact counts below are constituents, not additional purchases. No crimp tool. Vendor does not specify complete housing dimensions or insulation OD and warns the silver-latch side is slightly wider than 2.54 mm; verify orientation, adjacent fit, retention and the modeled envelope on receipt. Stock length is not installed length; per-core stub/copper cuts, splice overlaps and combined route budgets remain TBD until actual root/termination dimensions are measured against the selected source-bound FPS route. Replaces the unsupported generic Dupont-to-PH donor identity.')
    change('D2-27', item='FPS inline pair: Molex 2181110202 male + 2181120201 female pigtail assemblies',
        sku_or_class='Molex 2181110202 + 2181120201 (one of each)', supplier='Molex / authorized distributor', source=SOURCES['picoblade_male'],
        status='selected mated-carry route; refreshed scoped CAD pass, physical cuts/service unqualified',
        installed_qty=1, installed_unit='mated pair within one FPS harness', purchase_qty=1, purchase_unit='pair (one 225 mm male and one 150 mm female assembly)',
        spare_or_remainder='Measured wire offcuts TBD; both factory Molex housings retained',
        note='Supersedes unsupported generic PH wire-to-wire identity and old 200+50 mm accounting. Purchased rear-housing-exit-to-blunt-end lengths: male 225 +/- 6 mm, female 150 +/- 6 mm; two black 28 AWG UL1061 cores per half. Installed main nominal axis is 200.000 mm INCLUDING D2-25 donor stubs and splice region; female-to-A axis 95.4644 mm and female-to-throw2 axis 102.4759 mm precede unresolved solder allowances. These are study axes, not copper cuts. See FPS-SERVICE-STUDY.md for staggered splice midpoints and illustrative overlap convention. Both housings and four contacts included below. Keep pair mated while the independently supported switch and whole harness move with carrier; disconnect only on bench. No sacrificial tie or in-body connector draw-out. Actual heads, individual-core fanout, terminal geometry, root allowances and complete integrated USB/CSI/service checks remain open. Mated body 9 mm is reference only; male 8 mm and female 3.95 mm are not equal halves. Polarized friction lock has no alternate keying; J2 now uses a different mating family (V-28, '+WD.J2_DECISION+'), so no other in-camera half mates this pair (FP-14 junction check). Still label FPS and continuity-test both black wires. Spare pair: V-27S. System 1.5 A maximum at 28 AWG / 125 V and 30 tin-contact mating cycles are not a physical service qualification.')
    change('D2-26', item='PRC high-flex pure-copper 16 AWG silicone wire, red and black',
           installed_qty=2, installed_unit='conductor-path allocations; copper cuts TBD', purchase_qty=2, purchase_unit='36 in lengths, one per colour',
           spare_or_remainder='Offcuts not fixed; determine after measured cuts, joint overlaps and pad allowance', sku_or_class='PRC 16 AWG silicone; red '+WD.WIRE_SKUS['red']+'; black '+WD.WIRE_SKUS['black'], supplier='ProgressiveRC',
           status='provisional length; service route blocked', source=SOURCES['wire'],
           note='Purchase one 914.4 mm stock length per colour: red '+WD.WIRE_SKUS['red']+', black '+WD.WIRE_SKUS['black']+' (store product record '+SOURCES['wire_variants']+', read 2026-10-11; the product page shows one SKU field with a colour selector). POSITIVE: 270 mm FINISHED-PATH allocation includes a 20 mm rigid fuse/joint-sleeve zone; actual copper cut and solder overlap must be measured/trimmed to that finished path, not 270 mm copper plus fuse. NEGATIVE: 270 mm total path budget includes unresolved pad-root allowances. BOTH budgets include those allowances; they are not extra length to add later. Neither is a proved production cut; no exact offcut claim. '+drop_note+' Vendor OD 3.0 mm; reserve 3.2 mm/core, 6.4 x 3.2 mm pair. Existing pack lead stays 60 mm 18 AWG. Four carrier tie eyes are present; separate red/black cold-side slack retention is provisional. Full stored-length/bend and battery-disconnect reach checks pending; fixed ties cannot be assumed to unfold for service. Nominal resistance is not a vendor specification or hot-test pass.')
    change('D2-30', installed_qty=7, purchase_qty=11, spare_or_remainder='4 spare', note='Four panel + two carrier + one independent grip-lock PT 3.0 x 12 PH1; seven installed, not eleven. Same body screw count as baseline.')
    change('D2-32', installed_qty=0, installed_unit='inserts', status='contingency stock', note='Fallback stock only; pack quantity unspecified. Do not count a pack as an installed insert. One long collar insert is separately counted at D2-36.')
    change('D2-33', installed_qty=0, status='contingency stock', note='Seven fallback screws for stripped PT bosses, not installed in the candidate. Requalify a repaired boss before use.')
    for lid, installed, remainder in [('D2-35',3,'2 spare'),('D2-36',1,'spare may come from D2-32; not another installed insert'),('D2-37',3,'1 spare'),('D2-38',1,'1 spare'),('D2-39',4,'2 spare')]:
        change(lid, installed_qty=installed, spare_or_remainder=remainder,
               note='Lens-collar hardware; revised collar geometry requires renewed coupon/load checks. M1 remains open. See ASSEMBLY-VERTICAL.md.')
    change('D2-34', note='Conditional four M2.5 x 5 PH1 upper replacements only if included upper screws have an unsuitable drive. Lower four are already replaced by V-31; never add eight extra kit screws.')
    change('D2-40', item='ASA filament 1.75 mm, satin silver (tub, panel; original-storage sleeve)', note='Workshop spool; actual slice mass and filament consumption pending. Does not include an invented production mass.')
    change('D2-41', item='ASA filament 1.75 mm, black (carrier, base/grip, cap, knobs, lens collar)', note='No hood, Pi keeper or printed power plunger in this candidate; actual slice mass pending. Collar material still follows thermal qualification.')
    change('D2-44', item='Paint pen / enamel, black and white, for labels and optical witness marks', note='Keep baseline two-pen workshop provision; no printed plunger symbol. Witness marks across adapter/BFAR and BFAR/housing remain required.')
    change('D2-46', note='Retain insulation for pigtail, fuse, diode and switch leads; include four QT splice sleeves, TWO FPS donor-splice sleeves and insulation for both J2 pads and both new power-switch terminal joints. Confirm diameters for 16 AWG.')
    change('D2-50', installed_qty=4, installed_unit='allocated slack-loop ties', purchase_qty=1, purchase_unit='pack',
           spare_or_remainder='Pack count and remaining baseline bundle consumption to be measured',
           note='Use existing-class 2.5 mm cable ties; measured band thickness must be <=0.7 mm for the four 3 x 1 mm carrier slots. Four provisionally allocated to separate red/black cold-side pigtail loops; exact retention scheme may change. Fixed tied folds cannot unfold for service: qualify battery-disconnect reach with retention as installed. No contact or pressure on UPS PCB; retain bend radii and a straight fuse section. Exact tie/head dimensions and routing remain gated.')
    change('D2-63', note='Planned complete baseline-style build: 24 solder joints with spliced QT, two FPS donor splices and preterminated J2 pair; +2 only if pack lacks XT30 male. See audited count breakdown below; optional EVF regulator excluded.')
    change('D2-69', item='Junior hacksaw + small flat file for measured 18/24 switch shaft trim', note='Retain saw, file and soft-jaw vise for physical 18/24 shaft fit. Measure the new panel projection; historical absolute-Y cut position is obsolete.')
    change('D2-71', installed_qty=0, purchase_qty=0, status='removed', note='The vertical tub has no separate hood; two hood-release pins are removed from required tool scope.')
    change('D2-76', purchase_qty=0, status='optional; not adopted', note='Retain in scope for EVF option C only. Baseline listed a tool set although the regulator was quantity zero; no purchase or installed part until that option is adopted.')
    change('D2-77', note='Retain adjustable torque PH1 driver; baseline numerical caps are provisional. Revised carrier/boss and collar coupons must validate actual torque limits.')
    add('V-09', base.S_EL, 'Princeton USB-A portable SSD, 500 GB', 1, 1, variant='compact only',
        sku_or_class='PHD-USSD-500G', supplier='Princeton / distributor', layout_id='usb_stick', source=SOURCES['storage'],
        note='Primary compact candidate under review. Official 34 x 15 x 7 mm INCLUDING CAP, about 5 g; model reserves full 34 mm outside port X=-122 to -156 plus assumed mating plug. Remove and bag cap. Advertised maximum write/read 500/600 MB/s, operating 0-70 C; no Linux claim in vendor OS list. G-W10 >=100 MB/s warm sustained, Linux/USB compatibility, power, identity, dimensions and availability all remain gates.')
    add('V-09S', base.S_EL, 'Studied alternative: Samsung FIT Plus 256 GB', 0, 0, variant='compact only',
        status='studied; not recommended or adopted', sku_or_class='MUF-256AB', supplier='Samsung / distributor', source=SOURCES['storage_studied_samsung'],
        note='Retained research record only. Up-to-110 MB/s advertised sequential write offers little headroom against >=100 MB/s warm sustained G-W10. Prior conservative 23.6 x 18.8 x 7.3 mm reserve is not the primary compact storage model.')
    add('V-17', base.S_EL, 'Normally-open black momentary panel power switch', 1, 1,
        sku_or_class='Adafruit 1505', supplier='Adafruit', layout_id='power_button', source=SOURCES['power'],
        note='Switch plus supplied fixing nut/washer, receipt check required. Signal switch across Pi 5 J2; same onboard-button semantics, not battery isolation. Full rear 29.4 mm reserve plus 5 mm button; drawing conflicts remain open.')
    add('V-21', base.S_CB, 'Straight micro-HDMI plug adapter, EVF end', 1, 1,
        sku_or_class='Adafruit 3556', supplier='Adafruit', layout_id='hdmi', source=SOURCES['hdmi_adapter'],
        note='26.5 x 17.3 x 4 mm; one at EVF only. Replaces earlier two-straight-head proposal. Ribbon not included. Mating, retention and tool access gated.')
    add('V-21P', base.S_CB, 'Right-angle R-bend micro-HDMI plug adapter, Pi end', 1, 1,
        sku_or_class='Adafruit 3557', supplier='Adafruit', layout_id='hdmi', source=SOURCES['hdmi_pi_adapter'],
        note='17.5 x 15 x 14.5 mm; one at Pi. Actual connector clocking, rigid envelope and service access gated. Together with V-21 and one selected ribbon, three purchased pieces total.')
    add('V-22', base.S_CB, 'Rejected study: HDMI ribbon cable, intact 200 x 10 mm', 0, 0, variant='compact only',
        status='rejected/fragile; not installed', sku_or_class='Adafruit 3561', supplier='Adafruit', source=SOURCES['hdmi_ribbon'],
        note='Full 200 mm study had effectively zero tolerance reserve with both heads unplugged. Retained research record only; primary compact length is now 300 mm V-22O. No procurement or service-fit recommendation.')
    add('V-22O', base.S_CB, 'HDMI ribbon cable, intact 300 x 10 mm', 1, 1, variant='both',
        status='conditional primary; selected scoped checks passed; physical HOLD', sku_or_class='Adafruit 3562', supplier='Adafruit', layout_id='hdmi', source=SOURCES['hdmi_original_ribbon'],
        note='One intact 300 mm ribbon for either compact or original-storage body, with 3557/3556 heads. Selected routing input: routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json. The selected HDMI report binds the current compact-Kowa manifest; read its complete scoped check summary; alternatives still require their own audit. Earlier over-PCB tool failures remain rejected diagnostics; CSI operational access stays on HOLD. This does not qualify complete interacting loom service. Actual availability, full-width/slack/service tolerance, bend/thickness/clocking/EMI and retention remain gates.')
    # FP-14 (VN-64): spare policy of record in wiring_data.SPARES; spare rows are separate lines so the buy view sums them.
    sp={s['line']:s for s in WD.SPARES}
    add('V-23S', base.S_CB, 'Spare EVF Generic RCY-style matched pair', 0, 1, unit='pair',
        status='spare (FP-14 spare policy); in the buy count, not installed', sku_or_class='Pololu 2180 + 2181', supplier='Pololu',
        source=SOURCES['evf_socket'], spare_or_remainder='1 spare pair (one 2180 + one 2181)',
        note='Spare for D2-23 ('+sp['V-23S']['why']+'). Same receipt, continuity, polarity-label and fit checks as D2-23; ordered with it (buy view sums the SKUs).')
    J2=WD.J2_DEFAULT
    add('V-28', base.S_CB, 'J2 removable signal pair: keyed 2-circuit wire-to-wire set, '+J2['family']+' ('+WD.J2_DECISION+')', 1, 1, unit='set',
        status='conditional; '+WD.J2_DECISION+'; family distinct from every other junction; placement and route unqualified',
        sku_or_class=J2['sku_class'].format(lead_min=J2['lead_min_mm']), supplier='Molex / authorized distributor ('+WD.J2_DECISION+')',
        layout_id='power_button', source='wiring_data.py',
        spare_or_remainder='Lead offcuts after cutting to the measured J2 route; spare set V-28S',
        note='FP-14 (VN-63): replaces the 9ced753 Molex 2181120201 + 2181110202 PicoBlade pair, which was the same unkeyed family as the FPS junction (D2-27), so a J2 half could mate an FPS half and hold PWR_BUT to GND. '
             'Default family: '+J2['family']+', chosen because '+J2['why']+'. The family is '+WD.J2_DECISION+' (alternatives and their gates in WIRING-VERTICAL.md). '
             'The retained 28-24 AWG / two-colour description is a conditional class requirement, not a verified exact-parts selection. See corrective-2026-10-12/j2-parts-proposal/README.md: its proposed 043030/043031 contacts accept 20-24 AWG with maximum insulation OD 1.85 mm, so they do not cover the class at 26/28 AWG. Path A uses 24 AWG with one colour per half; path B uses 22 AWG, all black. Neither satisfies two-colour circuit identification as written. Exact parts, gauge, measured OD, circuit marking and placement remain pending user decision 13; neither proposal is adopted in V-28 or V-28S. '
             'Genders: '+J2['pi_side']+'; '+J2['switch_side']+'. Each pre-crimped lead >= '+format(J2['lead_min_mm'],'g')+' mm exposed: '+J2['lead_min_src']+'. '
             'Four solder joints remain: two J2 pads and two switch terminals; no crimps or splices. Housing dimensions, mated length, latch travel, wire exits and stow are receipt and placement gates: the J2 junction was never placed (G-V-POWER, VN-73) and the larger housing is not shown to fit the old 6 x 8 x 12 mm reserve. '
             'Try-mate matrix on receipt: each J2 half must refuse the FPS, EVF RCY and header housings. Signal use only, never battery current. Label J2 at both housings; verify both circuits by continuity.')
    add('V-28S', base.S_CB, 'Spare J2 keyed pair set ('+WD.J2_DECISION+')', 0, 1, unit='set',
        status='spare (FP-14 spare policy); in the buy count, not installed',
        sku_or_class=J2['sku_class'].format(lead_min=J2['lead_min_mm']), supplier='Molex / authorized distributor ('+WD.J2_DECISION+')',
        layout_id='power_button', source='wiring_data.py', spare_or_remainder='1 spare set',
        note='Spare for V-28 ('+sp['V-28S']['why']+'). Same family decision and receipt checks as V-28.')
    add('V-27S', base.S_CB, 'Spare FPS PicoBlade pair: Molex 2181110202 male + 2181120201 female', 0, 1, unit='pair',
        status='spare (FP-14 spare policy); in the buy count, not installed',
        sku_or_class='Molex 2181110202 + 2181120201 (one of each)', supplier='Molex / authorized distributor',
        source=SOURCES['picoblade_male'], spare_or_remainder='1 spare pair',
        note='Spare for D2-27 ('+sp['V-27S']['why']+'). Ordered with D2-27; the buy view sums the two SKUs.')
    add('V-22OS', base.S_CB, 'Spare HDMI ribbon cable, intact 300 x 10 mm', 0, 1,
        status='spare (FP-14 spare policy); in the buy count, not installed',
        sku_or_class='Adafruit 3562', supplier='Adafruit', source=SOURCES['hdmi_original_ribbon'], spare_or_remainder='1 spare ribbon',
        note='Spare for V-22O ('+sp['V-22OS']['why']+'). Heads V-21/V-21P are not consumed in service; reorder only if damaged.')
    add('V-31', base.S_FA, 'M2.5 x 8 pan-head PH1 lower stack/carrier screws', 4, 5,
        spare_or_remainder='1 spare', sku_or_class='ISO 7045 PH1 class', layout_id='x1203_kit',
        note='Replace four original lower M2.5 x 5 screws. Recessed 4 mm bosses leave 3 mm below the heads; 8 - 3 - 1.6 = 3.4 mm nominal thread engagement. Actual thread depth, head profile and bottoming must be measured. Eight stack screws installed in total, never twelve.')
    # FP-06 (VN-46): straight-driver rule for both switch nuts: deep socket on the nut axis, never a spanner.
    change('D2-61', item='1/2 in (12.7 mm) deep socket for the CK1044 switch nut, driven on the bushing axis',
        note='Straight-driver rule (review VN-46): deep socket on the nut axis, never a spanner. 12.7 mm across-flats is the inherited reservation, not a published Lorlin dimension; confirm on receipt. Socket clearance to the panel face and exposure knob belongs to the straight-driver check (FP-07).')
    add('V-62', base.S_TO, 'Deep socket for the Adafruit 1505 power-button nut, sized to the measured across-flats', 0, 0,
        status='provisional; purchase gated on the measured 1505 nut across-flats (FP-14 gated purchase)', note='Straight-driver rule (review VN-46): the nut is run down with a deep socket on the button axis, never a spanner. Across-flats unknown until receipt: measure the nut, then reuse an existing deep socket that fits; buy the matching one only if none fits (purchase stays 0 until that measurement). Review CAD probe: a socket up to OD 28 mm clears the panel; actual reach unverified.')
    for lid,item in [('V-63','Smooth-jaw long-nose pliers, fine tips'),('V-64','Soft-jaw vise or vise with wood jaw pads'),('V-65','Flat steel rule / bar'),('V-66','Printer-paper knob shims and panel support block'),('V-67','Small inspection mirror, optional')]:
        add(lid,base.S_TO,item,0,0 if lid=='V-67' else 1,status='baseline toolset retained',
            note='Explicit ASSEMBLY section 1.1 tool formerly lacking its own baseline BOM line; not a new installed part. Reuse existing workshop item.')
    # Child rows describe installed kit constituents; purchase quantities must stay zero.
    inc='G. Included-kit detail (do not buy or sum with parent assemblies)'
    for lid,item,q,parent,ref,note in [
      ('I-03A','M2.5 F-F standoffs',4,'D2-03','x1203_kit','Retain actual supplied stack length; measure it.'),
      ('I-03B','Original upper M2.5 x 5 screws',4,'D2-03','x1203_kit','Four installed; four other supplied lower screws are removed and bagged.'),
      ('I-05A','C-CS adapter',1,'D2-05','c_cs_adapter','Included optical adapter; witness marks required.'),
      ('I-05B','Camera tripod block plus two screws',0,'D2-05','tripod_block','Removed and bagged at supported optical bench setup; no camera-body installation.'),
      ('I-07A','OLED emitter',1,'D2-07','hmx039','Constituent of one EVF kit.'),
      ('I-07B','EVF driver board',1,'D2-07','evf_board','Constituent of one EVF kit.'),
      ('I-07C','Native OLED flex',1,'D2-07','oled_flex','One included native harness; never count as another kit purchase.'),
      ('I-02B','Supplied Active Cooler push pins',2,'D2-02','cooler','Two actual mounting push pins; old four illustrative support feet are not four purchased fasteners. Cooler/fan internals remain within the purchased cooler assembly.'),
      ('I-02A','Native Active Cooler fan lead',1,'D2-02','fan','Stays with complete Pi/cooler/UPS module.'),
      ('I-12A','Prewired run lead',1,'D2-12','run_lead','One included harness.'),
      ('I-13A','60 mm pack-side 18 AWG lead',1,'D2-13','pack_lead','Unchanged; pack-side connector below.'),
      ('I-13B','Pack-side XT30 male',1,'D2-13','xt30_pair','Do not also install a loose male from D2-14.'),
      ('I-45A','Cut OLED foam pad, 16 x 14 x 1 mm',1,'D2-45','foam_pad','Cut from the purchased sheet; rides with OLED; actual pad compression is a gate.'),
      ('I-27A','FPS Molex 510470200 plug housing',1,'D2-27','fps_lead','Included in male 2181110202; remains installed.'),
      ('I-27B','FPS Molex 510210200 receptacle housing',1,'D2-27','fps_lead','Included in female 2181120201; remains installed.'),
      ('I-27C','FPS male factory-crimped contacts',2,'D2-27','fps_lead','Included Molex 501338000; no additional purchase or crimp.'),
      ('I-27D','FPS female factory-crimped contacts',2,'D2-27','fps_lead','Included Molex 500588000; no additional purchase or crimp.'),
      ('I-23A','EVF source-side socket-contact housing',1,'D2-23','usb_5v','Included in Pololu 2180; protected source contacts, identity checked on receipt.'),
      ('I-23B','EVF board-side pin-contact housing',1,'D2-23','usb_5v','Included in Pololu 2181; not an additional purchase.'),
      ('I-23C','EVF factory-crimped contacts',4,'D2-23','usb_5v','Two per half; no additional crimp or solder joint.'),
      ('I-46A','Individual USB data-core insulating sleeves',2,'D2-46','usb_5v','Two separate installed pieces for unused white and green cores; do not join the data conductors.'),
      ('I-46B','Conditional USB shield insulating sleeve',0,'D2-46','usb_5v','Fit one additional piece only if a shield/drain is actually present; verify on receipt.'),
      ('I-25A','GPIO female jumper housings retained from donor pack',2,'D2-25','fps_lead','One installed on each measured stub; do not count both ends of each stock jumper.'),
      ('I-25B','GPIO female preterminated contacts retained from donor pack',2,'D2-25','fps_lead','One installed contact per retained housing; factory termination adds no new crimp or solder joint.'),
      ('I-11A','18/24 switch retaining nut',1,'D2-11','switch_1824','Planned supplied nut; inclusion, imperial thread, dimensions and tool access require receipt verification.'),
      ('I-11B','18/24 switch mounting washer',1,'D2-11','switch_1824','Planned mounting washer; inclusion, type and dimensions unverified. This is NOT the adjustable stop/tang washer.'),
      ('I-11C','18/24 adjustable stop/tang washer',1,'D2-11','switch_1824','Distinct supplied position-limiting piece per CK catalog. Set for two adjacent detents; preserve its indexed seat during panel service. Actual shape and stack remain receipt gates.'),
      ('I-09A','Princeton SSD protective cap',0,'V-09','usb_stick','Remove before insertion and bag; official overall envelope includes this cap but it is not installed in camera.'),
      ('I-17A','Power-switch retaining nut',1,'V-17','power_nut_reserve','Receipt inclusion/geometry gate. Model OD 22 x 3 mm is an unverified reserve, not a vendor dimension. Nut bearing plane follows panel inner Y=25.2 mm.'),
      ('I-17B','Power-switch supplied washer',1,'V-17','power_button','Receipt inclusion/thickness gate; no separately qualified washer solid.'),
      ('I-28A','J2 two-circuit plug housing (pin contacts, switch side)',1,'V-28','power_button','Included in the V-28 set ('+WD.J2_DECISION+'); not another purchase.'),
      ('I-28B','J2 two-circuit receptacle housing (socket contacts, Pi side)',1,'V-28','power_button','Included in the V-28 set ('+WD.J2_DECISION+'); not another purchase.'),
      ('I-28C','J2 male-terminal pre-crimped leads',2,'V-28','power_button','Factory-crimped, included in the V-28 set; no crimp tool or solder splice.'),
      ('I-28D','J2 female-terminal pre-crimped leads',2,'V-28','power_button','Factory-crimped, included in the V-28 set; no crimp tool or solder splice.'),
    ]:
        add(lid,inc,item,q,0,included_in=parent,layout_id=ref,status='included; unqualified',note=note)
    for name,material in [('tub','ASA, satin silver'),('panel','ASA, satin silver'),('carrier','ASA, black'),
                          ('base_grip','ASA, black'),('cap','ASA, black'),('eyecup','TPU 95A, black'),
                          ('knob_exp','ASA, black'),('knob_fps','ASA, black'),('lens_collar','ASA, black; thermal qualification pending'),
                          ('stick_sleeve','ASA, satin silver')]:
        add('P-'+name,'D. Printed production parts',name,1,0,unit='CAD assembly row',variant='original only' if name=='stick_sleeve' else 'both',
            sku_or_class=material,supplier='print after qualification',layout_id=name,
            note=('Concealed-vent revision: tub incorporates the source-defined ventilation geometry; panel is plain 2.8 mm after removal of four blind grooves. ' if name in ('tub','panel') else '')
                 +('T2 (VN-53): TWO physical printed pieces: body (stl/tub.stl, -Y face down, tenon pocket open) and +Y tab-catch stub (stl/tab_catch_insert.stl, bed face down, catch face vertical), bonded with V-68 at B1 print_inserts (default pending user decision 16). The assembled CAD row contains both; count the stub as a separate print. ' if name=='tub' else 'One physical printed piece. ')
                 +'Slice orientation, supports, filament and measured print mass remain pending. Compact: 9 CAD assembly rows / 10 physical printed pieces. Original storage: 10 rows / 11 pieces. Gauge and coupons excluded; no purchase quantity is implied.')
    add('I-tub-stub',inc,'Separately printed bonded tab-catch insert',1,0,unit='physical printed piece',
        included_in='P-tub',layout_id='tab_catch_insert',supplier='print after qualification',
        sku_or_class='printed constituent; separate material specification unresolved',
        status='included in tub CAD assembly; print and bond qualification HOLD',
        source='out/compact-kowa_lm6hc/manifest.json',
        note='The production_prints manifest lists stl/tab_catch_insert.stl separately from stl/tub.stl. This row exposes the second physical print already counted in P-tub, not an additional CAD assembly row or purchase. The manifest does not specify a separate insert material; do not infer one from the tub class. Bed face down and catch face vertical per the bound print pose. Bond with V-68 at B1 print_inserts only after qualification; exact adhesive, seating, cure and whole-tub torque remain HOLD. Do not add this included row to the parent assembly to claim an extra production piece.')
    add('V-68',base.S_CO,'Two-part epoxy adhesive, small pack (bond the +Y tab-catch stub into the tub, B1 print_inserts)',0,1,unit='pack',
        sku_or_class='class; structural two-part epoxy, confirm on receipt',supplier='any',layout_id='tab_catch_insert',
        note='T2 (VN-53, FP-11b): default pending user decision 16 (bonded stub; alternatives: press fit with a printed detent, or a panel-held block, which needs the panel on at lens_in). Adhesive type, cure, gap fill (0.1 to 0.2 mm pocket clearance) and the bond and tenon strength under the r7 roll_catch design torque are a G-V-PRINT tine coupon gate; amount consumed not measured.')
    add('T-gauge',base.S_TO,'Printed collar centring gauge for selected lens',0,0,unit='tool',supplier='print after qualification',
        note='Retained baseline tool; excluded from the 10 compact / 11 original-storage physical production prints and 9 / 10 CAD assembly rows. Inspect candidate gauge export for selected lens.')
    return rows, set(by), base


def validate(rows, base):
    by={r['line']:r for r in rows}
    assert len(by)==len(rows), 'duplicate BOM ids'
    assert {x[1] for x in base.LINES} <= by.keys(), 'a baseline line disappeared'
    assert all(r['purchase_qty']==0 for r in rows if r['included_in'])
    assert by['D2-30']['installed_qty']==7 and by['V-31']['installed_qty']==4
    assert by['I-03B']['installed_qty']+by['V-31']['installed_qty']==8
    assert by['D2-35']['installed_qty']+by['D2-36']['installed_qty']==4
    assert by['D2-37']['installed_qty']+by['D2-38']['installed_qty']==4
    assert by['I-28C']['installed_qty']+by['I-28D']['installed_qty']==4
    for variant,count in [('compact',9),('original',10)]:
        parts=[r for r in rows if r['section']=='D. Printed production parts' and r['variant'] in ('both',variant+' only')]
        assert sum(r['installed_qty'] for r in parts)==count
    assert by['D2-09']['variant']=='original only' and by['V-09']['variant']=='compact only'
    assert by['V-09']['sku_or_class']=='PHD-USSD-500G' and by['V-09S']['installed_qty']==0
    assert by['V-21']['installed_qty']==by['V-21P']['installed_qty']==1
    assert by['V-22']['installed_qty']==by['V-22']['purchase_qty']==0
    assert by['V-22O']['variant']=='both' and by['V-22O']['sku_or_class']=='Adafruit 3562'
    for variant in ('compact','original'):
        hdmi=[r for r in rows if r['line'] in ('V-21','V-21P','V-22','V-22O') and r['variant'] in ('both',variant+' only')]
        assert sum(r['installed_qty'] for r in hdmi)==3
    assert by['D2-71']['purchase_qty']==0
    assert by['D2-50']['installed_qty']==4 and by['D2-50']['purchase_qty']==1
    assert by['D2-26']['installed_unit']=='conductor-path allocations; copper cuts TBD'
    assert '644.4' not in by['D2-26']['spare_or_remainder']
    assert 'FINISHED-PATH' in by['D2-26']['note'] and '20 mm' in by['D2-26']['note']
    hot_drop=8.6*(2*(0.270*13.17+0.060*21)*(1+0.00393*40)+4.46+1)/1000
    assert abs(hot_drop-0.142810903056)<1e-12
    validate_fp14(rows)


# ------------------------------------------------------------------ FP-14 (VN-63, VN-64): junctions, spares, buy view
EXPORT18_BOM=HERE/'history/reviewed-export18/BOM-VERTICAL.csv'
# Same fields as review_docs_audit.py concealed_bom_preservation (editorial item/note/status changes excluded).
SELECTION_FIELDS=['variant','installed_qty','installed_unit','purchase_qty','purchase_unit','included_in','sku_or_class','supplier']
BUY_FIELDS=['sku','unit','supplier','compact_qty','original_qty','lines','gate']


def _is_class(sku):
    return 'class' in sku.lower()


def buy_parts(r):
    """[(orderable sku, quantity, unit)] for one purchased row (wiring_data.BUY_SPLIT, else the row's own SKU).
    Class rows are not SKUs: each stays its own group, keyed by its line, and is never merged with another row."""
    q=r['purchase_qty']
    split=WD.BUY_SPLIT.get(r['line'])
    if split:
        return [(sku,n*(q if split['per']=='unit' else 1),'ea') for sku,n in split['parts']]
    sku=r['sku_or_class']
    if _is_class(sku):
        return [(r['line']+': '+r['item']+' ('+sku+')',q,r['purchase_unit'])]
    return [(sku,q,r['purchase_unit'])]


def buy_view(rows, variant):
    """Purchased rows of one storage variant grouped by orderable SKU; quantities of rows sharing a SKU are summed.
    Gated rows (purchase 0 until a measurement) are listed with quantity 0 and their gate."""
    groups={}
    for r in rows:
        if r['included_in'] or r['variant'] not in ('both',variant+' only'):continue
        if r['line'] in WD.GATED:
            g=groups.setdefault((r['line'],'gated'),dict(sku=r['line']+': '+r['item'],unit=r['purchase_unit'],supplier=r['supplier'],qty=0,lines=[],gate=WD.GATED[r['line']][0]))
            g['lines'].append((r['line'],r['purchase_qty']));g['qty']+=r['purchase_qty'];continue
        if not r['purchase_qty']:continue
        for sku,n,unit in buy_parts(r):
            g=groups.setdefault((sku,unit),dict(sku=sku,unit=unit,supplier=r['supplier'],qty=0,lines=[],gate=''))
            assert g['supplier']==r['supplier'],('one SKU, two suppliers',sku,g['supplier'],r['supplier'])
            g['qty']+=n;g['lines'].append((r['line'],n))
    return list(groups.values())


def export18_differences(rows):
    """[(line, 'added'|'removed'|'changed', fields)] against the frozen reviewed-export18 BOM."""
    old={r['line']:r for r in csv.DictReader(io.StringIO(read_text(EXPORT18_BOM)))}
    cur={r['line']:r for r in rows}
    out=[]
    for key in sorted(old.keys()|cur.keys()):
        if key not in old or key not in cur:
            out.append((key,'added' if key in cur else 'removed',[]));continue
        ch=[f for f in SELECTION_FIELDS if old[key][f]!=str(cur[key][f])]
        if ch:out.append((key,'changed',ch))
    return out


def validate_fp14(rows):
    by={r['line']:r for r in rows}
    # VN-63: no two wire-to-wire junctions share a mating family (conservative: whatever the circuit count).
    shared=WD.shared_family_pairs(rows)
    assert not shared,('junctions share an unkeyed mateable family',shared)
    assert WD.junction_family(by['V-28']['sku_or_class'])==WD.J2_DEFAULT['family_key']
    assert all(j['bom'] in by for j in WD.JUNCTIONS)
    # VN-64: spare policy rows bought, not installed, same orderable SKUs as their parent.
    for s in WD.SPARES:
        r,p=by[s['line']],by[s['parent']]
        assert r['purchase_qty']>=1 and r['installed_qty']==0 and not r['included_in'],s['line']
        assert sorted(x[0] for x in buy_parts(r))==sorted(x[0] for x in buy_parts(p)),s['line']
    # Black and red wire SKUs are orderable lines.
    assert WD.WIRE_SKUS['black'] in by['D2-26']['sku_or_class'] and WD.WIRE_SKUS['red'] in by['D2-26']['sku_or_class']
    for lid,s in WD.BUY_SPLIT.items():
        assert lid in by and by[lid]['purchase_qty']>0,lid
        if s['per']=='row':assert sum(n for _,n in s['parts'])==by[lid]['purchase_qty'],lid
    # Gated purchases stay 0 until their measurement closes.
    for lid in WD.GATED:assert by[lid]['purchase_qty']==0,lid
    # Duplicate SKUs are summed: one group per orderable SKU and unit, its quantity the sum of every contributing row.
    for variant in ('compact','original'):
        view=buy_view(rows,variant)
        keys=[(g['sku'],g['unit']) for g in view]
        assert len(keys)==len(set(keys))
        contrib={}
        for r in rows:
            if r['included_in'] or r['variant'] not in ('both',variant+' only') or not r['purchase_qty'] or r['line'] in WD.GATED:continue
            for sku,n,unit in buy_parts(r):contrib[(sku,unit)]=contrib.get((sku,unit),0)+n
        got={(g['sku'],g['unit']):g['qty'] for g in view if not g['gate']}
        assert got==contrib,('buy view does not sum the purchased rows',variant)
        for g in view:assert g['qty']==sum(n for _,n in g['lines'])


def ventilation_print_hold(manifest):
    """Describe the selected mouth support from its manifest, without a printability claim."""
    support=manifest.get('ventilation',{}).get('support',{})
    apertures=support.get('hot_front_apertures_yz',[])
    if not apertures:
        return ('- PRINT HOLD: selected manifest does not declare hot-front aperture/support geometry. '
                'Reconcile its support definition before stating bridge spans; slicer/bridge/cleanout qualification remains open.')
    openings='; '.join(f"Y{y0:g}..{y1:g} / Z{z0:g}..{z1:g} (height {z1-z0:g} mm)"
                       for y0,y1,z0,z1 in apertures)
    beam=(f" Hanging beams are {support['rib_thickness_mm']:g} mm thick with declared pillar-window maximum "
          f"{support['window_max_mm']:g} mm." if all(k in support for k in ('rib_thickness_mm','window_max_mm')) else '')
    return (f"- PRINT HOLD: manifest support revision {support.get('revision','unspecified')}. "
            f"Hot-front open rectangles: {openings}.{beam} "
            'Opening heights are not a qualified slicer bridge direction or unsupported span. '
            'Inspect the bound print_bridge_direction rows, actual toolpaths and representative coupons; '
            'bridge quality, beam/pillar bonds and closed-body cleanout remain unqualified.')


def outputs(rows, base):
    manifest_path=HERE/'out/compact-kowa_lm6hc/manifest.json'
    manifest=json.loads(read_text(manifest_path))
    core=' x '.join(format(v,'g') for v in manifest['core_dimensions_mm'])
    ventilation_revision=manifest.get('ventilation',{}).get('revision','source-defined ventilation candidate')
    counts=manifest.get('production_prints', {})
    compact_rows=counts.get('assembly_row_count', sum(r['kind']=='printed' for r in manifest['rows']))
    compact_pieces=counts.get('piece_count', compact_rows + 1)
    if (compact_rows, compact_pieces)!=(9, 10):
        raise ValueError('Printed inventory changed; reconcile assembly rows and actual printed pieces')
    drop=HR.pigtail_drop_row()
    manifest_hash=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    def bound_report(relative, verifier):
        path=HERE/relative
        if not path.exists():return None
        value=json.loads(read_text(path))
        expected=hashlib.sha256((HERE/verifier).read_bytes()).hexdigest()
        if value.get('manifest_sha256',value.get('mechanical_manifest_sha256'))!=manifest_hash:return None
        if value.get('verification_source_sha256',value.get('source_sha256'))!=expected:return None
        return value
    main_report=bound_report('out/compact-kowa_lm6hc/verification.json','verify_candidate.py')
    # FP-04 (VN-08): quote the witness from the main-audit row of a report bound to this manifest; never a typed figure.
    main_path=HERE/'out/compact-kowa_lm6hc/verification.json';main_any=json.loads(read_text(main_path)) if main_path.exists() else {}
    witness=ER.cooler_witness_mm3(main_any) if main_any.get('manifest_sha256')==manifest_hash else None
    cooler_text=('active cooler/source-Pi witness '+ER.fmt_mm3(witness)+' mm3 (main-audit row interference pi5/cooler'
                 +('' if main_report is not None else '; that report predates the current verifier source')+')') if witness is not None else \
                'active cooler/source-Pi witness (no main-audit report is bound to this manifest; see verification.json once rerun)'
    gates=ER.inherited_gates(HERE)
    plenum_report=bound_report('out/compact-kowa_lm6hc/shadow-plenum-checks.json','verify_shadow_plenum.py')
    hdmi_report=bound_report('out/compact-kowa_lm6hc/hdmi-solid-checks.json','verify_hdmi.py')
    fps_report=bound_report('out/fps-service-study/integrated-fps-checks.json','verify_fps_integrated.py')
    power_report=bound_report('out/compact-kowa_lm6hc/power-service-checks.json','verify_power_service.py')
    if all(v is not None for v in (main_report,plenum_report,hdmi_report,fps_report,power_report)):
        ms=main_report['summary'];ps=plenum_report['summary'];hs=hdmi_report['summary'];fc=fps_report['static_and_carried_checks']
        current_check_note=(f"- Selected {manifest_hash[:8]} bound review: main {ms['pass']} pass / {ms['fail']} fail / {ms['info']} info; "
            f"plenum {ps['pass']} pass / {ps['fail']} fail / {ps['info']} info; HDMI {hs['pass']} pass / {hs['fail']} fail; "
            f"FPS {len(fc)} material checks / {sum(bool(x['hits']) for x in fc)} hits plus {len(fps_report['non_material_reservation_diagnostics'])} separate keepout diagnostics; "
            f"rigid power {power_report['poses']} poses / {power_report['exact_intersections']} queries / {len(power_report['hits'])} hits. "
            "Read each report for its exact scope and failures. CSI tool reservations address declared geometry only; actual operation and all physical gates remain open.")
    else:current_check_note='- Current full scoped-report set is not yet bound to this manifest and current verifier sources. Do not import historical pass counts; inspect each report and its binding before use.'
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
    md=['# Vertical Pi candidate: complete review BOM','',
        '**Unqualified review candidate. Do not procure or fabricate from this list yet.** No costs or stock claims. '
        'Baseline commit `'+BASELINE_COMMIT+'` is preserved. Sharing review artifacts does not authorize procurement or production release.','',
        'Generated by `make_bom_vertical.py`, reading the unchanged baseline generator’s `LINES`; every baseline line is retained, '
        'including explicit replaced/removed/optional rows. Candidate assembly and notes supersede old step numbers. '
        'The CSV carries separate installed units, purchase units, spares and included-in fields.','',
        '## Current checkpoint: assembly STOPs','',
        '- Current compact ventilation geometry: '+ventilation_revision+'. Core '+core+' mm. Geometry identity: '+manifest_hash+'. The panel is plain 2.8 mm; four former grooves had blind 0.2 mm floors, not through-vent area. The compact inventory has 9 CAD assembly rows and 10 physical printed pieces because the tub body and bonded catch stub are separate prints; the purchased selections and quantities that differ from it are listed under "Purchase changes against reviewed export18" (computed from history/reviewed-export18/BOM-VERTICAL.csv).',
        current_check_note,
        '- Reviewed export18 is frozen history, manifest c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76. Its 288 pass / 2 fail / 18 info, six scoped HDMI passes, 332 clear FPS material checks plus nine separate clear keepout diagnostics and other service checks are not automatically current evidence for the shadow-plenum tub. Read the new manifest-bound ventilation report and structural supplement for this revision.',
        '- Retained unresolved failure: '+cooler_text+'. The old right-wall ray runs through the intentional CSI opening and does not measure adjacent wall thickness. The new checker records that location as expected-empty and separately probes outer skin and original wall; read its manifest-bound result for the current count. The original 288/2/18 result and old wall supplement remain historical. The former 11.669 mm3 Boolean-difference witness is not an established lost-material volume; the Pi raw component-volume sum is not occupied material. Full FPC and EVF donor wire routes remain unplaced. Storage plug keepout is non-material; actual mating stays open.',
        '- Pigtail convention: positive 270 mm is the FINISHED PATH including a 20 mm rigid fuse/joint-sleeve zone; both 270 mm total path budgets include unresolved pad-root allowances; they are not extra length to add later. Actual copper cuts/overlaps and offcuts are not established. Buy one 914.4 mm stock length per colour; full flexible deployment remains unqualified.',
        f"- Pigtail remains BLOCKED: current {drop['i_peak_a']:g} A drop model gives {drop['drop_lo_v']:.5f} to {drop['drop_hi_v']:.5f} V against the unchanged {drop['limit_v']:.3f} V limit ({drop['status']}); the nominal-only 0.142811 V estimate does not cover hot fuse/vendor-minimum copper. Both full service reach and hot-drop need a compatible solution. No proposed alternative is adopted.",
        ventilation_print_hold(manifest),
        '- Intact 300 mm HDMI selected; fragile 200 mm study rejected. Complete HDMI, official 200 mm camera FPC and native OLED flex retain unknown manufacturer bend/cycle limits. Limited geometry checks do not qualify full interacting loom or service. See corrective-2026-10-12/materials-and-ribbons-baseline-evidence.txt for baseline evidence and applicability limits.',
        '- CSI slot remains straight 12 x 27 mm R1 (323.14 mm2) and unsealed. Seat the Pi cable end before installing the cooler per the official camera manual; mate the camera end while supported before camera insertion. Complete 200 mm linked camera/module motion, latch/jaw/FPC/cooler service and all bend/cycle limits remain HOLD. Cylinder clearance does not close those holds.', '',
        'The detailed service evidence applies to selected compact Kowa. Fresh shadow-plenum compact Fujinon and original-storage Kowa exports have their own source/file, mesh, assembly-envelope, mass/CoM and core-void comparisons in out/comparison/assembled-comparison.json and the three volume reports. Their full service/harness audits were not rerun; compact-Kowa service results do not transfer. Export18 alternative main audits remain historical.','',
        '## Count rules','',
        '- Filter to one storage variant; compact and original drives are mutually exclusive.',
        '- Installed is the planned in-camera quantity after qualification. It is not evidence anything was built.',
        '- Buy is a planning provision, not an order. Zero for printed items and included-kit constituents.',
        '- Included rows decompose a parent printed assembly, kit or harness. Never add both a parent assembly and its constituents to claim a physical total.',
        '- Workshop tools and spools are outside the camera; consumption and slice masses remain unmeasured.',
        '- Qualification aids are separate: retain the nine prior structural coupon pieces. A preliminary regular-grid open-edge plenum coupon STEP/STL is generated; its open edges do not prove closed-body cleanout or represent all ports/CSI/post exclusions. The expanded feature-region crop and the all-four-mouths crop are also generated, giving three separate plenum coupons total. None has been sliced, printed or tested; none establishes every unsupported span or closed-body cleanout. The separate [bonded-catch local study](structural-review/bonded-catch-coupon/README.md) adds two test pieces, host plus exact production insert copy, bound by [its receipt](structural-review/bonded-catch-coupon/receipt.json). That local seating/tilt/adhesion/creep screen does not qualify the whole-tub 0.5 N m case. Coupons are neither additional production parts nor purchased items.','',
        '| Count | Baseline | Compact candidate | Original-storage candidate |',
        '|---|---:|---:|---:|',
        '| Physical printed production pieces | 12 | 10 (body and bonded stub counted separately) | 11 (includes sleeve) |',
        '| Printed CAD assembly rows | 12 | 9 | 10 |',
        '| Installed PT body screws | 7 | 7 (4 panel + 2 carrier + 1 grip) | 7 |',
        '| Installed lens M3 screws / washers / inserts | 4 / 4 / 4 | 4 / 4 / 4 | 4 / 4 / 4 |',
        '| Installed stack screws / standoffs | 8 / 4 | 8 / 4 (4 old + 4 longer screws) | 8 / 4 |',
        '| Functional harnesses, including kit leads | 10 | 11 | 11 |',
        '| HDMI purchased pieces for one cable assembly | 1 | 3, intact 300 mm ribbon | 3, intact 300 mm ribbon |','',
        'The new power signal switch, removable junction and longer carrier screws trade extra purchased parts and bench work '
        'for removal of the printed plunger/linkage and side extraction of the whole stack. This is not an overall purchased-part reduction.','',
        'Mass caveat: the legacy XT30 row carries a 12 g lump that includes an estimated pigtail mass concentrated at the rigid proxy. Other harness masses are excluded. Thus not all wires are excluded, and the mass distribution/centre of mass is not fully resolved.','',
        'Use the chosen manifest and its ventilation report for passage geometry and normal throat definitions; earlier visible angled-channel figures are not transferable to a new plenum. The straight CSI slot remains an unsealed bypass, and the source-driven floor passage adds body/grip air communication. Useful flow, pressure loss, hand occlusion, print/support quality and battery/thermal performance remain unqualified. Integral passages add no purchased fan, mesh, seal or duct part. See structural-review/CONCEALED-VENT-STRUCTURAL.md for the manifest-bound mass/load sensitivity; old whole-tub binding does not apply.','',
        '## Installed pieces by category (not a grand total)','',
        '| Category | Installed count and contents |', '|---|---|',
        '| Printed production pieces | Compact 10; original-stick 11 including sleeve. Gauge/coupons excluded. The tub body and bonded +Y tab-catch stub (T2) are TWO physical prints represented by ONE assembled CAD row. Thus there are 9 / 10 printed CAD assembly rows. Integrated FPS rest/guide add no loose pieces. |',
        '| Body screws | 7 PT: four panel, two carrier, one independent grip lock. |',
        '| Stack hardware | 4 standoffs + 4 retained upper M2.5 x 5 + 4 replacement lower M2.5 x 8 = 12. Removed lower screws are not installed. |',
        '| Cooler mounting | 2 supplied push pins, not four illustrative proxy feet. Other cooler/fan internals stay inside the purchased assembly count. |',
        '| Lens mounting | 4 M3 screws + 4 washers + 4 inserts = 12. |',
        '| Tripod mounting | 1 captured 1/4-20 nut. |',
        '| Control mounting | Planned 5: FPS nut, mounting washer, stop/tang washer; power nut and washer. Inclusion/actual dimensions remain receipt gates. Encoder support is integral; no invented loose hardware. |',
        '| Standalone purchased cable/connector inputs retained in six harnesses | 15 assembly/section inputs: FPC 1; HDMI heads/ribbon 3; USB donor 1; EVF RCY halves 2; QT donor sections 2; GPIO donor stubs 2; FPS Molex halves 2; J2 keyed halves 2 (each one housing plus two pre-crimped leads; family '+WD.J2_DECISION+'). Two GPIO stubs come from one 20-wire pack; this is not 15 separately ordered packages. |',
        '| Camera battery pigtail | Separate seventh external harness: two cut 16 AWG cores, one camera XT30 female and one inline fuse. Copper cuts/overlaps remain TBD; stock wire is not an installed cable assembly. |',
        '| Included/native leads | 4: cooler fan, OLED flex, run-button lead, pack lead. Total functional harnesses = 6 + 1 + 4 = 11. |',
        '| Explicit inline pair constituents | EVF, FPS and J2 together: 6 housings and 12 factory contacts, already inside the six half-assemblies above. GPIO donors add 2 retained housings/2 contacts, also already counted. Do not add them again. |',
        '| Retention/insulation consumption | Four allocated power-slack ties; no FPS service tie. Two USB data-core sleeves, optional shield sleeve only if present, plus two FPS splice sleeves and other required joint insulation. Final tape, RTV, sleeve and wire cuts are unquantified. |','',
        'No grand physical-part total is claimed: board/kit internals, purchased assembly internals and measured consumable cuts are not decomposed consistently. '
        'Tools, optional quantity-zero rows, spares, offcuts and non-material keepouts are excluded from these installed counts.','',
        '## Solder-joint accounting','',

        '| Operation | Planned joints |', '|---|---:|',
        '| Legacy generator tally: X1203 pads 2, fuse splice 2, EVF lead 3 (two diode/positive joints and one ground splice), encoder A0 1, 18/24 lugs 2, EVF board pigtail 2 | 12 |',
        '| QT splice explicitly required by baseline WIRING W-QT but absent from legacy tally | 4 |',
        '| Loose camera-side XT30 female terminations, absent from legacy tally | 2 |',
        '| New J2 signal lead: two Pi pads and two switch terminals | 4 |',
        '| FPS GPIO donor-stub to PicoBlade blunt-wire splices | 2 |',
        '| Planned total, supplied pack male, spliced QT, FPS donor splices, preterminated J2 pair | 24 |','',
        'Add two only if the supplied pack lacks its XT30 male. A verified one-piece QT cable removes four. '
        'Optional EVF option C is excluded; its additional parts/joints are still a separate decision. '
        'Four J2 connector contacts are preterminated, so they are not four further solder joints. '
        'This tally is an operation-level plan, not a completed harness audit or physical qualification.','',
        '## Harness inventory','',
        '`fpc`, `hdmi`, `usb_5v`, `oled_flex`, `qt`, `run_lead`, `fps_lead`, `pigtail`, `fan`, `pack_lead`, `power_button`. '
        'Two HDMI adapters plus a ribbon remain one functional harness; the two QT source cables become one; the J2 pair adds one.','']
    sections=list(dict.fromkeys(r['section'] for r in rows))
    for sec in sections:
        md += ['## '+sec,'','| Line / variant | Item and SKU | Installed | Buy | Spares / included | Qualification and source |','|---|---|---|---|---|---|']
        for r in rows:
            if r['section']!=sec: continue
            esc=lambda s:str(s).replace('|','\\|').replace('\n',' ')
            rem=(('Included in '+r['included_in']+'. ') if r['included_in'] else '')+r['spare_or_remainder']
            md.append('| '+' | '.join(map(esc,[r['line']+' / '+r['variant'],r['item']+'; '+r['sku_or_class'],
                str(r['installed_qty'])+' '+r['installed_unit'],str(r['purchase_qty'])+' '+r['purchase_unit'],rem,
                r['status']+'. '+r['note']+' [Source]('+r['source']+')']))+' |')
        md.append('')
    # FP-14 (VN-64): consolidated buy view, spare policy, gated purchases; (VN-63) junction families.
    views={v:{(g['sku'],g['unit']):g for g in buy_view(rows,v)} for v in ('compact','original')}
    keys=list(dict.fromkeys(list(views['compact'])+list(views['original'])))
    spare_lines={s['line'] for s in WD.SPARES}
    by={r['line']:r for r in rows}
    def lines_text(k):
        ls=dict.fromkeys(l for v in views.values() if k in v for l,_ in v[k]['lines'])
        return ', '.join(l+(' (spare)' if l in spare_lines else '') for l in ls)
    buy=io.StringIO(newline='');bw=csv.DictWriter(buy,fieldnames=BUY_FIELDS,lineterminator='\n');bw.writeheader()
    md += ['## Buy view (grouped by orderable SKU)','',
           'Generated from the rows above (FP-14). Every purchased row is broken into the SKUs that are actually ordered (`wiring_data.BUY_SPLIT`); rows sharing a SKU are summed, spares included. Class rows are not SKUs and are never merged. Included-kit rows and printed parts are excluded. Not a price, stock or order claim. Also written as `BUY-VERTICAL.csv`.','',
           '| SKU or class | Unit | Supplier | Compact buy | Original buy | From lines | Gate |','|---|---|---|---:|---:|---|---|']
    for k in keys:
        g=views['compact'].get(k) or views['original'][k]
        cq=views['compact'][k]['qty'] if k in views['compact'] else 0
        oq=views['original'][k]['qty'] if k in views['original'] else 0
        rec=dict(sku=g['sku'],unit=g['unit'],supplier=g['supplier'],compact_qty=cq,original_qty=oq,lines=lines_text(k),gate=g['gate'])
        bw.writerow(rec)
        md.append('| '+' | '.join(str(rec[f]).replace('|','\\|') for f in BUY_FIELDS)+' |')
    md += ['','Spare policy (`wiring_data.SPARES`): one spare for every inline pair that is cycled in build or service or has few rated mating cycles, and for the fragile HDMI ribbon.','']
    md += ['- '+s['line']+' for '+s['parent']+': '+s['what']+'; '+s['why']+'.' for s in WD.SPARES]
    md += ['','Gated purchases (quantity stays 0 until the measurement closes):','']
    md += ['- '+lid+': '+by[lid]['item']+'. Gate: '+gate+'; then '+then+'.' for lid,(gate,then) in WD.GATED.items()]
    md += ['','Junction families (VN-63): no two wire-to-wire junctions may share a mating family, whatever the circuit count (`wiring_data.shared_family_pairs`, checked in `validate`).','',
           '| Junction | BOM line | Family | Carries |','|---|---|---|---|']
    md += ['| `'+j['id']+'` | '+j['bom']+' | '+str(WD.junction_family(by[j['bom']]['sku_or_class']))+' | '+j['carries']+' |' for j in WD.JUNCTIONS]
    md += ['','J2 family: '+WD.J2_DEFAULT['family']+', '+WD.J2_DECISION+'. See WIRING-VERTICAL.md for the alternatives and the try-mate gate.','',
           '## Purchase changes against reviewed export18','',
           'Computed against history/reviewed-export18/BOM-VERTICAL.csv on the fields '+', '.join(SELECTION_FIELDS)+' (the docs audit compares the same fields; item, note and status edits are editorial and not listed). Inventory-detail additions are listed too: an included row with zero purchase quantity is not an additional purchase.','']
    diffs=export18_differences(rows)
    md += ['- '+line+': '+kind+(' ('+', '.join(f)+')' if f else '')
           +(' (included in '+by[line]['included_in']+'; zero purchase quantity)' if line in by and by[line]['included_in'] and not by[line]['purchase_qty'] else '')
           for line,kind,f in diffs] or ['- none']
    md += ['']
    md += ['## Primary source checks','',
           'Supplier facts were read on 2026-10-09. No current availability or pricing is asserted. CAD envelopes and bend allowances are proxies; vendor dimensions do not qualify service fit.','']
    md += ['- ['+key+']('+url+')' for key,url in SOURCES.items()]
    md += ['', 'All '+str(gates['open'])+' inherited physical gates and M1 remain open. New candidate-specific gates are documented in `REVIEW.md`. '
           'Physical HDMI bend/retention and complete-loom service, final power-slack retention, J2 full connector placement/route, power-nut access and warm storage speed remain blockers; a CSV validation pass is not a fabrication release.','']
    return {'BOM-VERTICAL.csv':buf.getvalue(),'BOM-VERTICAL.md':'\n'.join(md),'BUY-VERTICAL.csv':buy.getvalue()}


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    rows,_,base=build_rows();validate(rows,base);result=outputs(rows,base)
    stale=[]
    for name,content in result.items():
        path=HERE/name
        if args.check:
            if not path.exists() or read_text(path)!=content:stale.append(name)
        else:write_text(path,content)
    if stale:raise SystemExit('Stale output: '+', '.join(stale))
    print(f'BOM schema/count checks passed: {len(rows)} explicit rows; all {len(base.LINES)} baseline source lines covered; CAD not imported.')
    print('No physical qualification, procurement or price/stock assertion.')

if __name__=='__main__':main()
