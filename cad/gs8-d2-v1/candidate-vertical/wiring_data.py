# SPDX-License-Identifier: MIT
"""Wiring and purchase data of record for the vertical candidate (review 2026-10-10, FP-14: VN-61, VN-63, VN-64).

Pure data plus small pure functions: no CadQuery, no file I/O. make_bom_vertical.py (BOM rows, buy view, BOM checks)
and make_wiring_vertical.py (WIRING-VERTICAL.md) both read it, so the BOM, the wiring schedule and the route sources
cannot drift apart unnoticed (tests/test_wiring_bom.py).

Nothing here is a measurement. Lengths are purchase REQUIREMENTS derived from the route checks, or vendor figures
already in the BOM; every unknown is named with the gate that closes it.
"""

# ------------------------------------------------------------------ J2 connector (VN-63, user decision 13)
# The 9ced753 J2 pair used the same unkeyed Molex PicoBlade pigtails as the FPS junction (BOM D2-27), so one J2 half
# could mate an FPS half: PWR_BUT held to GND (shutdown, then boot cycling). The family is user decision 13. The
# default below is the conservative choice: a pitch used by no other mateable half in the camera (PicoBlade 1.25 mm,
# Pololu RCY-style 2.5 mm, 2.54 mm header sockets, XT30), polarized housings and a positive latch, and factory
# pre-crimped leads so no crimp tool is needed (ASSEMBLY section 1.1). It is larger than PicoBlade; the J2 junction
# was never placed (VN-73, G-V-POWER), so its envelope and stow are a placement gate, not a regression of a checked fit.
J2_DECISION = 'default pending user decision 13'
J2_DEFAULT = dict(
    family='Molex Micro-Fit 3.0 2-circuit wire-to-wire (3.0 mm pitch)',
    family_key='molex-micro-fit-3.0',
    why='no other mateable half in the camera uses its pitch, its housings are polarized with a positive latch, and '
        'factory pre-crimped leads need no crimp tool',
    sku_class=('class: Molex Micro-Fit 3.0 2-circuit wire-to-wire set = 1 receptacle housing (socket contacts) + '
               '1 plug housing (pin contacts) + 2 factory pre-crimped leads with female terminals + 2 with male '
               'terminals, 28-24 AWG, each lead >= {lead_min:g} mm exposed; part numbers recorded at order after '
               'user decision 13'),
    pi_side='receptacle housing with SOCKET (female) contacts on the Pi J2 side: the live side never shows a bare '
            'pin that could touch ground and press the button (same rule as the EVF RCY source half)',
    switch_side='plug housing with PIN (male) contacts on the 1505 switch side',
    lead_min_mm=231.0,
    lead_min_src=('longest 9ced753 V-28 tail upper bound (Molex 2181110202, 225 + 6 mm): each half may then sit on '
                  'either side and the harness_rules j2_btn halves (150 / 225 +/- 6 mm) and CABLES power_button '
                  '(363-387 mm) stay conservative lower bounds of what is bought; cut to the measured J2 route'),
    gate='G-V-POWER (VN-73): place the J2 pair and its stow after the real 1505 and J2 pads are measured; try-mate '
         'matrix on receipt (each J2 half must refuse every other mateable half in the camera)',
)
J2_ALTERNATIVES = [
    ('JST SM 2-circuit wire-to-wire (2.5 mm pitch, positive latch)', 'jst-sm-2.5',
     'same pitch as the EVF RCY pair: needs a try-mate proof against Pololu 2180/2181 before adoption'),
    ('Molex PicoBlade 3-circuit pair with the centre cavity blanked', 'molex-picoblade-1.25',
     'same family as FPS: a 2-circuit half may enter a 3-circuit shroud; the conservative family rule rejects it '
     'unless a try-mate proof is recorded'),
    ('Same PicoBlade pair as FPS with labels and coloured sleeves only (9ced753)', 'molex-picoblade-1.25',
     'rejected by VN-63: labels do not stop a cross-mate'),
]

# BOM SKU text -> mating family. Order matters: the Molex PicoBlade part numbers contain '2181'.
FAMILY_TOKENS = [
    ('Micro-Fit', 'molex-micro-fit-3.0'),
    ('Molex 2181110', 'molex-picoblade-1.25'), ('Molex 2181120', 'molex-picoblade-1.25'),
    ('PicoBlade', 'molex-picoblade-1.25'),
    ('JST SM', 'jst-sm-2.5'),
    ('Pololu 2180', 'pololu-rcy-2.5'), ('Pololu 2181', 'pololu-rcy-2.5'), ('RCY', 'pololu-rcy-2.5'),
    ('XT30', 'amass-xt30'),
]


def junction_family(sku):
    """Mating family of a BOM SKU text, or None."""
    for token, fam in FAMILY_TOKENS:
        if token in sku:
            return fam
    return None


# Wire-to-wire junctions that can be open at the same time on the bench or in service (steps.CONNECTIONS ids).
# Conservative rule (VN-63): no two junctions may share a mating family at all, whatever the circuit count, unless a
# recorded try-mate proof says otherwise (none exists).
JUNCTIONS = [
    dict(id='evf_5v', bom='D2-23', carries='EVF 5 V after the diode (power, Pi USB2 VBUS)',
         sides=('source side: Pololu 2180 SOCKET-contact half on the USB donor', 'EVF side: Pololu 2181 PIN-contact '
                'half, tails soldered to the EVF board EXT+/GND pads')),
    dict(id='fps_1824', bom='D2-27', carries='GPIO13 / GND (18/24 select)',
         sides=('Pi side: Molex 2181110202 male assembly (225 mm), spliced to the two D2-25 donor stubs',
                'switch side: Molex 2181120201 female assembly (150 mm), soldered to CK1044 common A and throw 2')),
    dict(id='j2', bom='V-28', carries='Pi 5 J2 PWR_BUT / GND (power-button signal; never battery current)',
         sides=('Pi side: ' + J2_DEFAULT['pi_side'], 'switch side: ' + J2_DEFAULT['switch_side'])),
    dict(id='xt30', bom='D2-14', carries='battery current (pigtail to pack; power last)',
         sides=('camera side: XT30U FEMALE on the pigtail, fuse in the + conductor', 'pack side: XT30U male on the '
                '60 mm pack lead (D2-13)')),
]


def shared_family_pairs(rows, junctions=None):
    """[(junction a, junction b, family)] for junctions whose BOM rows share a mating family (must be empty).
    A junction whose family cannot be identified from its SKU is reported as (id, None, None): unknown never passes."""
    junctions = JUNCTIONS if junctions is None else junctions
    by = {r['line']: r for r in rows}
    fam = {j['id']: junction_family(by[j['bom']]['sku_or_class']) for j in junctions}
    out = [(j['id'], None, None) for j in junctions if fam[j['id']] is None]
    for i, a in enumerate(junctions):
        for b in junctions[i + 1:]:
            if fam[a['id']] is not None and fam[a['id']] == fam[b['id']]:
                out.append((a['id'], b['id'], fam[a['id']]))
    return out


# ------------------------------------------------------------------ wire SKUs (VN-64)
# PRC 16 AWG silicone: the product page shows one SKU field (SW-16R) with a colour selector; the store's product
# record lists the variants Red = SW-16R and Black = SW-16B (read 2026-10-11).
WIRE_SKUS = dict(red='SW-16R', black='SW-16B',
                 src='https://www.progressiverc.com/products/prc-silicone-wire-16-awg.json (variants Red SW-16R, '
                     'Black SW-16B; read 2026-10-11)')

# ------------------------------------------------------------------ spare policy (VN-64)
# One spare for every inline pair that is cycled in build or service or has few rated mating cycles, and for the
# fragile HDMI ribbon. Spare rows are separate BOM lines (installed 0, buy 1) so the buy view sums them with their
# parent SKU.
SPARES = [
    dict(line='V-23S', parent='D2-23', what='EVF RCY-style pair (one 2180 + one 2181)',
         why='parted at every EVF and module service (steps.SERVICE evf, module); no rating published'),
    dict(line='V-27S', parent='D2-27', what='FPS PicoBlade pair (one 2181110202 + one 2181120201)',
         why='tin contacts with a low rated mating-cycle count (BOM D2-27 note); parted on the bench at FPS service'),
    dict(line='V-28S', parent='V-28', what='J2 keyed pair set (housings + pre-crimped leads)',
         why='one J2 mating cycle per panel removal (ASSEMBLY section 5.1 J2 cycles)'),
    dict(line='V-22OS', parent='V-22O', what='HDMI ribbon, intact 300 x 10 mm',
         why='less durable and less shielded than a moulded cable (Adafruit 3562 page; review ELE-14); FPC latch '
             'or fold fatigue after services'),
]

# ------------------------------------------------------------------ buy view (VN-64)
# Purchased rows broken into orderable SKUs. 'per': 'unit' = quantity per purchase unit of the row; 'row' = absolute
# quantity for the whole row (checked against the row's purchase quantity). Rows not listed order their own SKU.
_J2_PARTS = [('J2 class: Micro-Fit 3.0 2-circuit receptacle housing (socket contacts)', 1),
             ('J2 class: Micro-Fit 3.0 2-circuit plug housing (pin contacts)', 1),
             ('J2 class: Micro-Fit 3.0 pre-crimped lead, female terminal, >= 231 mm', 2),
             ('J2 class: Micro-Fit 3.0 pre-crimped lead, male terminal, >= 231 mm', 2)]
BUY_SPLIT = {
    'D2-23': dict(per='unit', parts=[('Pololu 2180', 1), ('Pololu 2181', 1)]),
    'V-23S': dict(per='unit', parts=[('Pololu 2180', 1), ('Pololu 2181', 1)]),
    'D2-27': dict(per='unit', parts=[('Molex 2181110202', 1), ('Molex 2181120201', 1)]),
    'V-27S': dict(per='unit', parts=[('Molex 2181110202', 1), ('Molex 2181120201', 1)]),
    'V-28': dict(per='unit', parts=_J2_PARTS),
    'V-28S': dict(per='unit', parts=_J2_PARTS),
    'D2-26': dict(per='row', parts=[('PRC ' + WIRE_SKUS['red'] + ' (16 AWG red, 36 in)', 1),
                                    ('PRC ' + WIRE_SKUS['black'] + ' (16 AWG black, 36 in)', 1)]),
    'V-22O': dict(per='unit', parts=[('Adafruit 3562', 1)]),
    'V-22OS': dict(per='unit', parts=[('Adafruit 3562', 1)]),
}

# ------------------------------------------------------------------ gated purchases
# A purchase that stays 0 until a measurement closes; the BOM row and the buy view name the gate.
GATED = {
    'V-62': ('Adafruit 1505 nut across-flats (MEASUREMENTS-TO-CLOSE "Adafruit 1505 power switch and J2 signal '
             'harness" row; VN-73)', 'reuse a fitting deep socket; buy one only if none fits, after the measurement'),
}

# ------------------------------------------------------------------ leads (harness schedule)
# One entry per functional harness (BOM 'Harness inventory'), keyed by the harness_rules CABLES / route ids it covers
# and the steps.CONNECTIONS id that carries its plug ops. Colours and polarity are stated only where the BOM or the
# r7 wiring records them; otherwise the rule is "record on receipt".
LEADS = [
    dict(id='qt', connection='qt', route_ids=['qt'], bom=['D2-24', 'D2-24B'],
         a='Pi 5 header pins 1 / 3 / 5 / 6: four single 2.54 mm female housings (Adafruit 4397 sockets)',
         b='Adafruit 5880 encoder STEMMA QT socket: JST SH 4-pin plug (Pololu 5521)',
         conductors='4 x QT cores: pin 1 3V3 red, pin 3 SDA blue, pin 5 SCL yellow, pin 6 GND black (STEMMA QT '
                    'colours, r7 W-QT); splice the two sources by SH pin number with a meter, never by colour alone',
         polarity='3V3 on pin 1 only; never 5 V'),
    dict(id='run_lead', connection='run_lead', route_ids=['run_pin37', 'run_pin39'], bom=['D2-12'],
         a='run button in the grip cradle (pre-wired, factory joints)',
         b='Pi 5 header pins 37 (GPIO26) and 39 (GND): two single female housings',
         conductors='2 cores as supplied (colours record on receipt)', polarity='none (contact to GND)'),
    dict(id='fps_lead', connection='fps_1824', route_ids=['fps_lead'], bom=['D2-27', 'D2-25', 'D2-11'],
         a='Pi 5 header pins 33 (GPIO13) and 34 (GND): two single female housings kept from the D2-25 donor stubs',
         b='CK1044 18/24 switch: common A and throw 2 (solder)',
         conductors='donor stubs: two distinct colours, record which is pin 33; Molex leads: both black, so label '
                    'FPS and continuity-test each core end to end',
         polarity='none (contact to GND); GPIO13 = common A'),
    dict(id='power_button', connection='j2', route_ids=['power_button'], bom=['V-28', 'V-17'],
         a='Pi 5 J2 pads PWR_BUT and GND (solder; pad identity from the official drawing and the board, G-V-POWER)',
         b='Adafruit 1505 normally-open terminals (solder)',
         conductors='2 cores of two distinct colours (record which is PWR_BUT); label J2 at both housings',
         polarity='the 1505 is a non-polarized NO contact: polarity matters only for the label and the try-mate '
                  'matrix'),
    dict(id='usb_5v', connection='evf_5v', route_ids=['usb_5v'], bom=['D2-22', 'D2-16', 'D2-23', 'D2-46'],
         a='Pi 5 upper USB2 port: Adafruit 4448 USB-A plug',
         b='EVF board EXT+ / GND pads: Pololu 2181 tails (solder, strain-relieved at the board edge)',
         conductors='4448 red VBUS and black GND only; white D- and green D+ each in its own sleeve (two pieces), '
                    'shield sleeved only if present; RCY tail colours record on receipt',
         polarity='1N5817 in the + conductor, cathode band toward the EVF board (current flows USB -> EVF); 2180 '
                  'socket half on the USB (source) side'),
    dict(id='pigtail', connection='xt30', route_ids=['pigtail_positive', 'pigtail_negative'],
         bom=['D2-26', 'D2-14', 'D2-14F'],
         a='X1203 battery pads + / - (solder, neutral-cure RTV strain relief)',
         b='camera-side XT30U FEMALE (solder)',
         conductors='16 AWG PRC silicone: red ' + WIRE_SKUS['red'] + ' = +, black ' + WIRE_SKUS['black'] + ' = -',
         polarity='red to X1203 + and XT30 +; the one 15 A inline fuse in the red (+) conductor near the XT30; check '
                  'polarity with a meter before the first pack mate'),
    dict(id='pack_lead', connection='xt30', route_ids=['pack_lead'], bom=['D2-13'],
         a='1S2P pack BMS (existing 60 mm 18 AWG lead)', b='pack-side XT30U male',
         conductors='as supplied with the pack', polarity='XT30 housing marks'),
    dict(id='fpc', connection='camera_fpc', route_ids=['fpc'], bom=['D2-20'],
         a='GS camera 15-pin connector (mated on the bench)', b='Pi 5 CAM/DISP 1 (22-pin, through the CSI side slot)',
         conductors='official 200 mm 22-to-15 FPC', polarity='contact side per the official cable; latch HOLD'),
    dict(id='hdmi', connection='evf_hdmi', route_ids=['hdmi'], bom=['V-21P', 'V-22O', 'V-21'],
         a='Pi 5 HDMI0: Adafruit 3557 right-angle head', b='EVF board receptacle: Adafruit 3556 straight head',
         conductors='intact 300 x 10 mm Adafruit 3562 ribbon',
         polarity='contact face per head: check_scope HDMI_CONTACT_SIDES (HOLD until the parts are in hand)'),
    dict(id='fan', connection='fan', route_ids=['fan'], bom=['D2-02'],
         a='Active Cooler fan', b='Pi 5 FAN header (native JST SH)', conductors='native lead', polarity='keyed'),
    dict(id='oled_flex', connection=None, route_ids=['oled_flex'], bom=['D2-07'],
         a='HMX039 OLED', b='EVF driver board ZIF (bench op evf_bench)', conductors='native kit flex',
         polarity='ZIF orientation per the kit'),
]

# Pi 5 J8 header pins used by the candidate (unchanged from r7: electronics/gs8-d2-v1/pi5-header.csv).
HEADER = [
    (1, '3V3', 'encoder V+ (QT red)', 'qt'),
    (3, 'GPIO2 / SDA1', 'encoder SDA (QT blue); X1203 gauge (pogo)', 'qt'),
    (5, 'GPIO3 / SCL1', 'encoder SCL (QT yellow); X1203 gauge (pogo)', 'qt'),
    (6, 'GND', 'encoder GND (QT black)', 'qt'),
    (33, 'GPIO13', '18/24 switch, common A', 'fps_lead'),
    (34, 'GND', '18/24 switch, throw 2', 'fps_lead'),
    (37, 'GPIO26', 'run button', 'run_lead'),
    (39, 'GND', 'run button', 'run_lead'),
]
