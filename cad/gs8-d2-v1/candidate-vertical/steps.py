# SPDX-License-Identifier: MIT
"""Assembly-state model of the vertical candidate (review 2026-10-10, FP-05; closes VN-22).

Pure data plus small set functions: no CadQuery, no file I/O, importable anywhere (tests, verifiers, guide builders).

What it holds
- STEPS: the CORRECTED build order as an ordered list of single-purpose operations ("ops"). Each op says which ids
  enter (adds) or leave (removes) the body, which screws/nuts are driven there, which motion rows sweep it and
  which cable ends are mated. Its `doc` is the instruction text the FP-06 docs (ASSEMBLY-VERTICAL.md, both guide
  builders) are written from. `step` is the ASSEMBLY section label (B0..B4 bench, 1..8 body).
- SERVICE: service routes as ordered removal ops from the service start state (final build state minus the
  section 1 safety removals), with `requires` (routes that must be done first) and `reverse_of` (the build op(s)
  that refit what the op removes). The refit of a route is its ops reversed.
- MOTIONS: every rigid motion of the build and service. Obstacles are DERIVED, never typed:
      obstacles = (present before the op | present after the op) - movers - riders - exempt
  so a part that is in the body at that moment can only be left out with a named reason (exempt) or because it
  moves with the movers (riders: checked in their own motion row). This replaces the hand-typed fixed sets of
  verify_candidate.py (VN-22: carrier_out and panel_out omitted present parts).
- driver_contexts(): the parts present when each fastener is driven (build) or turned (service), for FP-07.
- TOOLS: assembly tools that are temporarily in the body (the collar centring gauge) and the parts they can never
  coexist with (the seated gauge overlaps c_cs_adapter by 927.75 mm3; its rear cone needs the empty tub lip).
- lint(): order, tool, mating, refit, coverage and bookkeeping rules. It takes any step list, so the regression
  test feeds it the original 9ced753 order and expects the VN-39/40/41/43 errors.

Ids are manifest row ids (out/<variant>/manifest.json) plus TOOLS. OPTIONAL ids exist only in some variants;
consumers pass the ids they have (`available`) and missing optional ids are dropped, never silently others.
Geometry is not here: paths are rigid translations in mm (assembly frame: X lensward, Y operator-left, Z up),
copied from verify_candidate.py (9ced753) or r7 layout.INSERTIONS where named, or reversed from them. Nothing
here is a measurement or a physical qualification.
"""

# ----------------------------------------------------------------------------------------------- vocabulary
TOOLS = {
    'centring_gauge': dict(
        step_file='step/centring_gauge.step',
        excludes=('gs_camera', 'c_cs_adapter'),
        reason='seated gauge overlaps c_cs_adapter by 927.752 mm3 (review VN-39, reproduced 2026-10-10 on all three '
               'variants); its rear cone references the EMPTY tub lip (printed_collar.centring_gauge docstring)'),
}
OPTIONAL = {'stick_sleeve': 'original storage only (SDCZ880 sleeve); not a row of the compact manifests'}

# Rigid sub-assemblies built on the bench and inserted as one (members in insertion state).
CAMERA = ['gs_camera', 'c_cs_adapter']
MODULE = ['carrier', 'pi5', 'cooler', 'x1203', 'x1203_kit', 'microsd', 'switch_1824']
PANEL = ['panel', 'encoder', 'knob_exp', 'power_button', 'power_nut_reserve']
EVF = ['hmx039', 'foam_pad', 'evf_board']
STORAGE = ['usb_stick', 'stick_sleeve']
GRIP = ['base_grip', 'tripod_nut', 'run_button']
PANEL_SCREWS = ['p_panel1', 'p_panel2', 'p_panel3', 'p_panel4']
CARRIER_SCREWS = ['p_carrier1', 'p_carrier2']
COLLAR_ANCHORS = ['s_c1', 's_c2', 's_c3']

PH1 = 'straight PH1 driver on the screw axis (baseline bit/handle envelope); provisional torque cap per ASSEMBLY s2'
SOCKET = 'deep socket on the nut axis (straight-driver rule; no spanner: VN-46)'


def op(id, step, doc, **kw):
    """One single-purpose operation. Fields (all optional except id/step/doc):
    where   'body' (default) | 'bench' (builds `group` off the body) | 'prop' (`group` staged beside the body)
    group   bench sub-assembly name for bench/prop ops; inserts: the group a body op brings in (adds == members)
    adds / removes   ids entering / leaving the body (bench ops: entering the group)
    screws  fasteners tightened at this op (must be present after it); nuts: nuts driven with a socket
    connects  cable ends mated here, as 'cable:end' (see CONNECTIONS)
    no_motion  why an op that moves parts has no rigid sweep row
    closes  review ids whose fix is this op's placement
    secures  leads laid into and secured in their lanes here (CONNECTIONS keys, or 'pigtail'); a lead is free before
             (lint SECURE_BEFORE_MATE; harness mate_reach anchors on it)"""
    d = dict(id=id, step=step, doc=' '.join(doc.split()), where='body', group=None, inserts=None, adds=[], removes=[],
             screws=[], nuts=[], connects=[], no_motion=None, closes=[], tools='', secures=[], flex_scope=None, supported_groups=[])
    d.update(kw)
    for k in ('adds', 'removes', 'screws', 'nuts', 'connects', 'closes', 'secures', 'supported_groups'):
        d[k] = list(d[k])
    return d


# ----------------------------------------------------------------------------------------------- build order
STEPS = [
    # ---- bench (nothing enters the body) ----
    op('optics_bench', 'B0', where='bench', group='camera', adds=CAMERA,
       tools='camera clamp/tripod block, lens support, tripod-block screw driver (one-time bench exception)',
       closes=['VN-44'],
       doc='Supported optical setup. Camera on its tripod block in a clamp, lens supported separately; never react '
           'lens thread torque through the PCB or cover. Seat the C-CS adapter, mark adapter/BFAR and BFAR/housing, '
           'measure infinity back focus, rear-cell clearance, cover reach and the lens support band; record actual '
           'values. Lens off again; tripod block and its 2 screws off and bagged. Keep the camera connector '
           'accessible. The official 200 mm FPC Pi end is seated before the cooler at module_bench; its camera '
           'end is mated while supported immediately before camera_in. Complete linked-ribbon motion remains HOLD.'),
    op('print_inserts', 'B1', where='bench', group='inserts',
       tools='heat-set iron with the M3 tip; insert-repair tools',
       doc='After the print holds are closed: inspect the nominated parts and the selected lens\'s collar and '
           'centring gauge. Heat-set the 3 short tub inserts and the 1 long collar (pinch-lug) insert under the '
           'coupon-validated process, before any electronics are near. No insert may enter an optical, board or '
           'wiring clearance. Bond the printed +Y tab-catch stub into the tub (two-part epoxy V-68, default pending '
           'user decision 16): tenon into the pocket under the roof, stub pressed toward the camera axis (-Y) onto '
           'the pocket datum while it cures, no adhesive on the catch face (T2, VN-53).'),
    op('module_bench', 'B2', where='bench', group='module', adds=MODULE,
       connects=['camera_fpc:pi', 'fps_1824:pi', 'fps_1824:sw', 'evf_hdmi:pi', 'evf_5v:pi', 'qt:pi', 'j2:pi', 'fan:pi', 'fan:cooler',
                 'xt30:pigtail'],
       tools='soldering iron, multimeter, ESD strap, kit driver, PH1',
       closes=['VN-40'],
       doc='Electrical and stack preparation, fully unpowered. Seat the Pi end of the official 200 mm camera FPC '
           'straight in CAM/DISP 1 with the correct contacts and latch, BEFORE fitting the Active Cooler, as the '
           'Raspberry Pi camera instructions recommend. Keep its camera end protected and free. Then stack '
           'Pi, X1203, cooler and the 4 standoffs on the carrier with the 4 M2.5 x 8 lower screws; OS microSD in. '
           'Solder the 16 AWG pigtail with its one inline fuse to the X1203 pads (RTV strain relief), the J2 signal '
           'half to the Pi J2 pads, the EVF feed and the leads. The CK1044 FPS switch belongs to THIS module: '
           'mate its inline pair here and carry the switch with the carrier, hand-supported; its washer, nut and '
           'knob are fitted only after the panel is on (op fps_washer_on..knob_fps_on). Pre-mate on the bench: the '
           '3557 right-angle HDMI head on the Pi (300 mm 3562 ribbon pre-formed, EVF end free), the USB donor in '
           'the Pi USB2 port (EVF power, RCY pair half free), and the wall-facing GPIO housings (QT 1/3/5/6, '
           '18/24 33/34) that cannot be reached once the carrier is in. Run pins 37/39 stay free for the run lead '
           '(op module_staged). Bench test only under the inherited gate, then disconnect all power again.'),
    op('panel_bench', 'B3', where='bench', group='panel', adds=['panel', 'encoder', 'knob_exp'],
       tools='thumb backing, paper knob shims (2 strips), paint pen',
       closes=['VN-40'],
       doc='Panel subassembly, part 1. Paint-fill the engraving. Snap the encoder (A0 bridged, 0x37) into its cradle '
           'by pushing on the back of its board. Lay the 2 paper strips on the panel face round the encoder shaft, '
           'hold the panel with that thumb flat on the back of the encoder board and press knob_exp on until it '
           'stops on the paper (the thumb takes the push, not the hooks: r7 BX-5); pull the paper out. The FPS '
           'switch, its washer, nut and knob are NOT fitted here (they ride with the carrier, VN-40). If the CK1044 '
           'shaft must be cut, dry-fit the switch in this panel only to measure the knob projection, take it off '
           'and cut it off the panel.'),
    op('panel_power_switch', 'B3', where='bench', group='panel', adds=['power_button', 'power_nut_reserve'],
       nuts=['power_nut_reserve'], tools=SOCKET,
       closes=['VN-46'],
       doc='Panel subassembly, part 2. Fit the Adafruit 1505 power button through the panel (flange on the outer '
           'face Y28) and run its nut down on the inner face (Y25.2) with a deep socket on the button axis, never a '
           'spanner; confirm thread length and socket reach on the real panel first. Keep the J2 junction half on '
           'its terminals free and accessible.'),
    op('evf_bench', 'B4', where='bench', group='evf', adds=EVF,
       tools='tweezers, ESD strap',
       doc='EVF subassembly: foam pad stuck to the OLED back, native flex into the board ZIF and latch closed, as '
           'the qualified baseline optical module requires. No HDMI or power is mated to the board on the bench '
           '(both mate in the body at op evf_mate, after the carrier has brought their source ends).'),
    # ---- 1. base/grip and tub ----
    op('grip_prep', '1', adds=GRIP, connects=['run_lead:grip'],
       no_motion='press fits by hand (tripod nut slip fit, run button into its cradle); r7 swept neither',
       tools='flat bar for the tripod nut',
       doc='Press the tripod nut into its grip pocket from the top. Feed the pre-wired run lead\'s 1-pin header '
           'housings up through the floor passage while it is open, then drop the run button into its cradle. '
           'The pack stays out (power last).'),
    op('strap_thread', '1', adds=['strap'], no_motion='flexible webbing threaded by hand; routing proxy only',
       closes=['VN-23'],
       doc='Thread the 12 mm strap through both upper and heel slots on the OPEN base, before the tub is seated: its '
           'pass over the bridge lies in the 2 mm recess in the base top, which the seated tub floor closes (r7 '
           'threads the strap before the tub too). It is then fitted BEFORE the grip lock: the p_grip driver handle '
           'passes about 1.37 mm from the strap, so the screw is driven (and audited) with the strap fitted.'),
    op('tub_on', '1', adds=['tub'],
       doc='Seat the tub on the keyhole tongues in their keyed direction over the threaded strap, keeping the run '
           'lead in the passage; let its socket end hang out over the open +Y side. Do not lock yet.'),
    op('grip_lock', '1', adds=['p_grip'], screws=['p_grip'], tools=PH1,
       no_motion='screw: audited by the straight-driver check (FP-07) in this context, not swept',
       doc='Drive the independent grip-lock PT screw (p_grip) on its axis, 0.35-0.5 N m provisional, stop at head '
           'contact. The panel is never the grip lock.'),
    # ---- 2. optics, carrier and panel absent (VN-39, VN-41) ----
    op('collar_on', '2', adds=['lens_collar'], closes=['VN-39'],
       doc='Lens collar FIRST, camera still out: bring the collar for the selected lens in along -X and set its feet '
           'on the tub front face over the 3 short inserts.'),
    op('collar_screws_start', '2', adds=COLLAR_ANCHORS,
       no_motion='screws started by hand; audited at collar_tighten',
       doc='Start s_c1, s_c2, s_c3 (M3 x 10, washers) about 2 turns each from the front. Do not tighten.'),
    op('gauge_in', '2', adds=['centring_gauge'], closes=['VN-39'],
       doc='Push the centring gauge for this lens through the collar bore along -X until its rear cone seats in the '
           'empty tub lip and its front cone in the collar bore chamfer. The lip must be empty: the gauge and the '
           'camera/adapter can never be in the body together.'),
    op('collar_tighten', '2', screws=COLLAR_ANCHORS, tools=PH1 + '; thumb holding the gauge home',
       no_motion='screws tightened in place; audited with the gauge present',
       doc='Hold the gauge home with a thumb and tighten s_c1, s_c2, s_c3 from the front to the provisional '
           'collar-anchor cap (0.15 N m), stopping at head contact.'),
    op('gauge_out', '2', removes=['centring_gauge'], closes=['VN-39'],
       doc='Pull the gauge out forward (+X) through the collar. The tub lip is now free for the camera.'),
    op('camera_fpc_mate', '2', where='prop', group='camera', supported_groups=['module'],
       connects=['camera_fpc:cam'], tools='ESD support for camera and complete Pi module',
       no_motion='connector operation outside the body; actual latch and full linked FPC motion remain HOLD',
       doc='Support the camera and prepared Pi module beside the body, both unpowered. Seat the camera end of '
           'the full 200 mm FPC straight and close its latch before camera insertion. The Pi end was seated '
           'before the cooler at module_bench. Never let the ribbon carry either assembly; its full linked '
           'camera/module insertion and stored shape remain HOLD.'),
    op('camera_in', '2', adds=CAMERA, inserts='camera', closes=['VN-39', 'VN-44'],
       flex_scope='HOLD: rigid camera/adapter sweep omits the complete 200 mm CSI FPC linking the camera to the '
                  'supported module outside the body. Full-width stored material, linked motion, roots, bends '
                  'and latch operation remain unproved; no complete assembly qualification.',
       doc='With all power absent and the prepared Pi module supported outside the body, mate the camera end '
           'of its 200 mm FPC at camera_fpc_mate before insertion; the Pi end was seated before the cooler at module_bench. '
           'HOLD until the full linked camera/module ribbon motion is checked. Bring camera with adapter in through the open +Y side: '
           'approach 11.1 mm rearward and 2 mm high, lower 2 mm, then move lensward (+X) 11.1 mm until the adapter '
           'passes the lip and the metal lock tab enters between the tab-catch tines. Keep the linked FPC slack and '
           'out of the path; do not let it carry either assembly. Do not leave it: nothing holds the camera back until the lens is on (next ops).'),
    op('s_c4_start', '2', adds=['s_c4'], no_motion='screw started loosely in the collar lug insert',
       closes=['VN-41'],
       doc='Fit the pinch screw s_c4 (M3 x 16, washer) loosely in the collar lug.'),
    op('lens_in', '2', adds=['lens'], closes=['VN-41'],
       tools='fingertips only; folded cloth for the side rest',
       doc='Lens with the carrier and panel still out (r7 step 8 method). Rest the body on its side so the open +Y '
           'side is up; one fingertip on the centre of the camera cover presses the camera forward (+X) onto its '
           'lip catch: push only, never pinch or turn the cover. Pass the lens through the collar and screw it '
           'into the adapter with fingertips until it stops, no extra snug; the camera turns with it until the '
           'metal lock tab meets the tab catch, which takes the torque through metal. Never react thread torque '
           'through the PCB or cover.'),
    op('lens_float', '2', screws=['s_c4'], tools=PH1 + '; hand on the grip until s_c4 is snug',
       no_motion='rotation about the lens axis in place (roll window is FP-08 roll_catch), then a screw',
       closes=['VN-41'],
       doc='Set iris and focus and push the lens gently rearward until it seats on the collar cone. With s_c4 still '
           'loose, turn lens and camera together the other way until the lock tab stops on the other tine, then '
           'back about half way: a soft stop each way means the tab floats between the tines. Look and feel: the '
           'camera now hangs on the lens and touches neither the tub lip, the counterbore nor the tines (J7-R '
           'float). Snug s_c4 on its axis to the provisional pinch cap (0.2 N m). Check both optical witness '
           'marks. The camera is now retained before anything else enters the body.'),
    # ---- 3. EVF module, no matings (VN-43) ----
    op('eyepiece_in', '3', adds=['eyepiece'],
       doc='From behind the body, push the eyepiece spigot +X through the rear-wall bore until its flange sits on '
           'the rear face; the spigot rests in the inner seat and the panel supplies the +Y clamp later (r7 step 6 '
           'method; the bore is closed above, so it cannot be dropped in from +Y). Keep the body level or nose-down '
           'until the panel is on.'),
    op('evf_in', '3', adds=EVF, inserts='evf', closes=['VN-43'],
       doc='Slide the OLED/board subassembly in from +Y into its seats, foam and native flex unstressed. Do NOT '
           'mate the EVF HDMI head or the EVF power junction yet: their source ends arrive with the carrier '
           '(op evf_mate). Do not let the unclamped module fall.'),
    # ---- 4. carrier/stack ----
    op('module_staged', '4', where='prop', group='module', connects=['run_lead:pi'],
       doc='Hold the complete module (carrier, Pi, cooler, X1203, kit, OS microSD, FPS switch hand-supported, Pi '
           'HDMI head mated, EVF ends free) just outside the open +Y side. Plug the run lead from the grip onto Pi '
           'pins 37/39 (wall-facing: reachable only now). Carry the EVF HDMI head at least stroke + 3 mm below its '
           'mated height for the slide (VN-43 carried-head margin).'),
    op('carrier_in', '4', adds=MODULE, inserts='module', closes=['VN-44'],
       flex_scope='HOLD: rigid carrier sweep omits the complete 200 mm CSI FPC already connected to both camera '
                  'and Pi. The full flexible sweep, stored slack, roots, bends and interaction with other looms '
                  'are unproved; this operation is not a complete assembly or service pass.',
       doc='Bring the module in along -Y onto its two bosses, feeding the pigtail and XT30 through the floor '
           'passage without scraping the pair, fuse or XT30 body. HOLD: the whole 200 mm camera FPC is linked at both '
           'ends and is absent from this rigid sweep. Prove its complete motion and keep it clear of the 3.9 mm '
           'camera-to-carrier gap during the slide. Recording storage stays out. Do not force the USB 5 V adapter '
           'aside.'),
    op('carrier_screws', '4', adds=CARRIER_SCREWS, screws=CARRIER_SCREWS, tools=PH1,
       no_motion='screws: audited by the straight-driver check (FP-07)',
       doc='Drive the two carrier PT screws (p_carrier1, p_carrier2) on their axes, 0.35-0.5 N m provisional, stop at '
           'head contact.'),
    # ---- 5. internal connections, no new parts ----
    op('evf_mate', '5', connects=['evf_hdmi:evf', 'evf_5v:evf'], closes=['VN-43', 'VN-44'],
       secures=['pigtail', 'run_lead', 'fps_1824', 'evf_hdmi', 'evf_5v'],
       no_motion='no rigid part moves; connector and lead motions are harness checks (FP-10)',
       tools='tweezers, fingertip / steel-rule push stick, smooth-jaw pliers',
       doc='Fully unpowered. Push the 3556 straight EVF HDMI head UP from below into the board receptacle by its '
           'body, never by the ribbon. Mate the EVF power RCY pair (2180 source half to 2181 EVF half) by both '
           'housings. The camera FPC is already mated at both ends: inspect its full width, roots and folds without '
           'releasing its latch; complete route and actual latch service remain HOLD. Seat and tug-test the header leads; route and secure the pigtail, run, 18/24 and EVF leads in '
           'their qualified lanes. Leave the QT and J2 leads FREE (out of their lanes): their panel ends mate at '
           'panel_prop, and a lead already secured cannot reach the propped panel (FP-10 mate_reach).'),
    # ---- 6. panel, then FPS hardware (VN-40) ----
    op('panel_prop', '6', where='prop', group='panel', connects=['qt:enc', 'j2:btn'],
       doc='Prop the panel subassembly beside the open side on a stable support, inner face toward the body, never '
           'hanging from wires. Mate the QT lead at the encoder and the J2 junction with both housings in reach.'),
    op('panel_in', '6', adds=PANEL, inserts='panel', closes=['VN-40'], secures=['qt', 'j2'],
       doc='Move the panel in along -Y, guiding the FPS switch bushing and its locating peg into the panel hole and '
           'slot while the other hand supports the switch body; lay the QT and J2 leads into their lanes as the '
           'panel closes. '
           'Confirm the camera catch and EVF clamp engage without pinching.'),
    op('panel_screws', '6', adds=PANEL_SCREWS, screws=PANEL_SCREWS, tools=PH1,
       no_motion='screws: audited by the straight-driver check (FP-07) before the FPS knob is on',
       doc='Drive the four panel PT screws on their axes, 0.35-0.5 N m provisional, stop at head contact. The FPS '
           'knob is not on yet, so the driver handle is clear of it.'),
    op('fps_washer_on', '6', adds=['fps_mounting_washer'], closes=['VN-40'],
       doc='Fit the CK1044 mounting washer over the bushing on the panel face, stop/tang washer setting untouched.'),
    op('fps_nut_on', '6', adds=['fps_nut'], nuts=['fps_nut'], tools=SOCKET, closes=['VN-40', 'VN-46'],
       doc='Run the CK1044 nut down with a deep socket on the bushing axis and check anti-rotation (peg in slot).'),
    op('knob_fps_on', '6', adds=['knob_fps'], closes=['VN-40'], tools='paper knob shims (2 strips)',
       doc='Lay the 2 paper strips round the FPS shaft and press knob_fps on, D flat to the shaft flat, until it stops '
           'on the paper (the nut on the panel takes the push); pull the paper out.'),
    # ---- 7. media and exterior ----
    op('storage_in', '7', adds=STORAGE + ['usb_storage_plug_reserve'],
       doc='Remove and bag the drive cap (original storage: fit the sleeve on the bench first). Insert the one '
           'selected recording drive straight along +X into the upper USB3 port. Never two drives.'),
    op('eyecup_on', '7', adds=['eyecup'], no_motion='TPU sleeve pushed over the eyepiece barrel (r7 swept none)',
       doc='Push the eyecup over the eyepiece barrel from the rear.'),
    # ---- 8. power last ----
    op('pack_in', '8', adds=['xt30_pair', 'pack'], connects=['xt30:pack'],
       doc='Only after closure and the bench checks: draw the pigtail XT30 out of the grip mouth, mate it to the '
           'pack XT30 by both housings outside the bay, push the junction and fuse in ahead of the pack, then the '
           'pack. Never mate inside the bay; never force the cap against the fuse or leads.'),
    op('cap_on', '8', adds=['cap'], doc='Slide the battery cap on until it latches.'),
]

FINAL_OP = STEPS[-1]['id']

# ----------------------------------------------------------------------------------------------- cable ends
# Each cable has two ends: (part that carries the end, op where it is mated). At an end's op its part must be in the
# body or in that op's bench/staged group; at the later end's op the other end's part must be there too.
CONNECTIONS = {
    'camera_fpc': dict(cam=('gs_camera', 'camera_fpc_mate'), pi=('pi5', 'module_bench'),
                       doc='200 mm CSI FPC; Pi end before cooler, camera end supported before camera insertion; '
                           'complete linked camera/module flexible motion and actual latch service remain HOLD'),
    'evf_hdmi': dict(pi=('pi5', 'module_bench'), evf=('evf_board', 'evf_mate'),
                     doc='3557 Pi head / 300 mm 3562 ribbon / 3556 EVF head pushed up from below (VN-43)'),
    'evf_5v': dict(pi=('pi5', 'module_bench'), evf=('evf_board', 'evf_mate'),
                   doc='USB donor at the Pi USB2 port; Pololu 2180/2181 inline pair at the EVF side (VN-43)'),
    'qt': dict(pi=('pi5', 'module_bench'), enc=('encoder', 'panel_prop'), doc='QT lead, header pins 1/3/5/6'),
    'j2': dict(pi=('pi5', 'module_bench'), btn=('power_button', 'panel_prop'), doc='J2 signal pair junction'),
    'fps_1824': dict(pi=('pi5', 'module_bench'), sw=('switch_1824', 'module_bench'),
                     doc='18/24 lead, pins 33/34, inline pair mated on the bench'),
    'run_lead': dict(grip=('run_button', 'grip_prep'), pi=('pi5', 'module_staged'),
                     doc='run button lead, pins 37/39 on the wall-facing side'),
    'fan': dict(pi=('pi5', 'module_bench'), cooler=('cooler', 'module_bench'), doc='native cooler fan lead'),
    'xt30': dict(pigtail=('x1203', 'module_bench'), pack=('pack', 'pack_in'),
                 doc='16 AWG pigtail + one inline fuse to the pack XT30 (power last)'),
}

# ----------------------------------------------------------------------------------------------- service
# Service start = final build state after the section 1 safety route. The rigid xt30_pair proxy (both XT30 halves +
# fuse at the frozen 21/45 deg pose) stays in the body after the pack is pulled: it is the conservative stand-in for
# the parted pigtail half and fuse lying in the grip bay, and is an obstacle until the module route removes it.


def sop(id, doc, **kw):
    """Service op: removes, unscrews (fasteners taken out here; driver context = state before), loosens (turned in
    place), nuts (socket off), disconnects, reverse_of (build op ids whose adds refit the removes) or refit (text)."""
    d = dict(id=id, doc=' '.join(doc.split()), removes=[], unscrews=[], loosens=[], nuts=[], disconnects=[],
             reverse_of=[], refit=None, where='body', no_motion=None, remate_at={})
    d.update(kw)
    return d


_NM_PLUG = 'connector releases only; harness checks (FP-10)'
SERVICE = {
    'safety': dict(requires=[], doc='ASSEMBLY s1: shutdown, external power off, cap off, pack out, XT30 parted.',
                   ops=[sop('svc_cap_off', 'Slide the battery cap off.', removes=['cap'], reverse_of=['cap_on']),
                        sop('svc_pack_out', 'Pull the pack out by its ribbon and part the XT30 by its housings.',
                            removes=['pack'], disconnects=['xt30'], reverse_of=['pack_in'])]),
    'panel': dict(requires=['safety'], doc='Control panel off (FPS hardware first, switch stays with the carrier).',
                  ops=[sop('svc_knob_fps_off', 'Pull knob_fps off along +Y.', removes=['knob_fps'],
                           reverse_of=['knob_fps_on']),
                       sop('svc_fps_nut_off', 'Unthread the CK1044 nut with the deep socket, supporting the switch.',
                           removes=['fps_nut'], nuts=['fps_nut'], reverse_of=['fps_nut_on']),
                       sop('svc_fps_washer_off', 'Take the mounting washer off; keep the stop/tang setting.',
                           removes=['fps_mounting_washer'], reverse_of=['fps_washer_on']),
                       sop('svc_panel_screws_out', 'Remove the four panel PT screws.', removes=PANEL_SCREWS,
                           unscrews=PANEL_SCREWS, reverse_of=['panel_screws']),
                       sop('svc_panel_out', 'Translate the panel +Y over the released bushing and peg to the prop '
                           'pose; part QT and J2 by their housings.', removes=PANEL, disconnects=['qt', 'j2'],
                           reverse_of=['panel_in'])]),
    'storage': dict(requires=['safety'], doc='Recording drive out along -X after safe removal.',
                    ops=[sop('svc_storage_out', 'Withdraw the drive straight along -X; do not rock the receptacle.',
                             removes=STORAGE + ['usb_storage_plug_reserve'], reverse_of=['storage_in'])]),
    'lens': dict(requires=['safety'], doc='Lens off in the closed body (same collar). s_c4 is only loosened.',
                 ops=[sop('svc_s_c4_loosen', 'Loosen s_c4 one turn on its axis.', loosens=['s_c4'],
                          reverse_of=['lens_float'], no_motion='screw turned in place; driver context only'),
                      sop('svc_lens_out', 'Unscrew the lens with the tab catch taking the torque and draw it +X.',
                          removes=['lens'], reverse_of=['lens_in'])]),
    'evf': dict(requires=['panel'], doc='EVF board/OLED out with the carrier in place.',
                ops=[sop('svc_evf_unplug', 'Unplug the EVF HDMI head (down) and part the EVF power pair by both '
                         'housings.', disconnects=['evf_hdmi', 'evf_5v'], reverse_of=['evf_mate'],
                         no_motion=_NM_PLUG),
                     sop('svc_evf_out', 'Release the panel clamp (panel is off) and slide the module +Y.',
                         removes=EVF, reverse_of=['evf_in'])]),
    'microsd': dict(requires=['panel'], doc='OS microSD; the closed-panel +X path is blocked by the power switch and '
                    'the straight panel-off +X path by the lens collar.',
                    ops=[sop('svc_microsd_out', 'With the panel off, grip the card with straight fine-tip '
                             'non-conductive tweezers, draw it +X 18 mm out of the socket, then lift it +Y out of the '
                             'open panel side (dog-leg; the straight +X path meets the lens collar). Tool and finger '
                             'reach are unqualified (HOLD, MEASUREMENTS-TO-CLOSE microSD row; VN-29).',
                             removes=['microsd'],
                             refit='reverse of svc_microsd_out with the panel off once reach is qualified, or on the '
                                   'bench in module_bench with the module out (user decision VN-29)')]),
    'module': dict(requires=['storage', 'panel'], doc='Complete Pi/UPS/cooler module out (carrier with it).',
                   ops=[sop('svc_module_unplug', 'Unplug the EVF HDMI head at the EVF end and part the EVF power '
                            'pair; release the camera FPC at the Pi (latch HOLD); free the pigtail in the grip passage '
                            '(flexible: FP-10).', disconnects=['evf_hdmi', 'evf_5v', 'camera_fpc'],
                            remate_at={'camera_fpc': 'module_bench'},
                            refit='CSI Pi end only: use the connection named at module_bench with the assembled module '
                                  'supported; do not repeat cooler installation or soldering. HOLD until real latch '
                                  'access with the cooler retained and the complete linked-ribbon motion are proved',
                            reverse_of=['evf_mate'], no_motion=_NM_PLUG),
                        sop('svc_carrier_screws_out', 'Remove the two carrier PT screws.', removes=CARRIER_SCREWS,
                            unscrews=CARRIER_SCREWS, reverse_of=['carrier_screws']),
                        sop('svc_carrier_out', 'Stage the module +Y with the FPS switch hand-supported; part the run '
                            'lead at the staging pose.', removes=MODULE, disconnects=['run_lead'],
                            reverse_of=['carrier_in']),
                        sop('svc_pigtail_out', 'The pigtail, fuse and its XT30 half leave with the module, drawn up '
                            'through the floor passage (flexible withdrawal: FP-10 lead_access/pigtail checks).',
                            removes=['xt30_pair'], reverse_of=['pack_in'],
                            no_motion='flexible pigtail withdrawn with the module through the floor passage: FP-10 '
                                      'lead_access/pigtail checks, not a rigid sweep')]),
    'camera': dict(requires=['panel', 'storage', 'module', 'lens'],   # lens LAST: lens + s_c4 hold the camera while
                   # the module leaves (VN-42; lint CAMERA_RETAINED, service side); lens_out +X is carrier-independent
                   doc='Camera/adapter service and the first half of any lens change (VN-42 dependency chain).',
                   ops=[sop('svc_camera_out', 'Reverse the camera-first insertion: -X 11.1, up 2, out +Y.',
                            removes=CAMERA, reverse_of=['camera_in'])]),
    'collar': dict(requires=['camera'], doc='Collar swap for a different lens: camera out first (the gauge needs the '
                   'empty lip), then the full refit from op collar_on.',
                   ops=[sop('svc_collar_screws_out', 'Remove s_c1..s_c3 from the front.', removes=COLLAR_ANCHORS,
                            unscrews=COLLAR_ANCHORS, reverse_of=['collar_screws_start']),
                        sop('svc_collar_off', 'Draw the collar +X off its feet; s_c4 stays in its lug insert.',
                            removes=['lens_collar', 's_c4'], reverse_of=['collar_on', 's_c4_start'])]),
    'grip': dict(requires=['module'], doc='Grip/base off. Default per VN-45: Pi module out first (the run lead\'s Pi '
                 'end is reachable only with the carrier out); an inline junction is the user\'s alternative.',
                 ops=[sop('svc_grip_screw_out', 'Remove the grip-lock PT screw from below.', removes=['p_grip'],
                          unscrews=['p_grip'], reverse_of=['grip_lock']),
                      sop('svc_grip_off', 'Slide the grip off its keyholes with the run lead following through the '
                          'floor passage; the strap stays threaded in the base and leaves with it.',
                          removes=GRIP + ['strap'], reverse_of=['grip_prep', 'strap_thread'],
                          refit='the strap stays threaded in the removed base (never re-thread it with the tub on: the '
                                'seated tub floor closes its recess); slide base, tripod nut, run button and strap back '
                                'together onto the keyholes (the base_on relative motion), then grip_lock')]),
}

# ----------------------------------------------------------------------------------------------- motions
# path: rigid translation knots in motion order (insertion ends at (0,0,0); removal starts there).
# runner: 'verify_candidate' (swept by verify_candidate.py with the derived obstacles), 'covered' (covered_by names a
# swept motion with the same movers, the reversed path and a superset of obstacles: lint COVERAGE proves it) or
# 'open' (not swept for the candidate yet; open_reason says why and what exists in r7).
_SQ = (0.0, 0.0, 0.0)
_CAM = [(-11.1, 60.0, 2.0), (-11.1, 0.0, 2.0), (-11.1, 0.0, 0.0), _SQ]      # verify_candidate.py 9ced753 camera_in
MICROSD_DOGLEG_X = (18.0, 0.0, 0.0)    # FP-12 (VN-29): out of the socket +X, short of the tub front wall
MICROSD_DOGLEG_OUT = (18.0, 40.0, 0.0)  # then +Y out of the open panel side
MICROSD_TOOL = 'straight fine-tip non-conductive tweezers'
_PLUG_EXEMPT = {'pi5': 'the USB-A plug envelope starts seated in the Pi USB3 receptacle (reported as the '
                       'non_material_keepout pi5/usb_storage_plug_reserve info row, 195.9 mm3); unplugging is the '
                       'mating itself, actual plug/receptacle geometry HOLD (9ced753 excluded pi5 the same way)'}


def mo(op, movers, path, runner='verify_candidate', **kw):
    d = dict(op=op, movers=list(movers), path=[tuple(float(c) for c in p) for p in path] if path else None,
             runner=runner, riders=[], exempt={}, covered_by=None, open_reason=None, note='')
    d.update(kw)
    d['riders'] = list(d['riders'])
    return d


MOTIONS = {
    # ---- swept by verify_candidate.py (the 10 rows of 9ced753 keep their ids and paths) ----
    'fps_knob_off': mo('svc_knob_fps_off', ['knob_fps'], [_SQ, (0, 20, 0)]),
    'fps_nut_after_unthread': mo('svc_fps_nut_off', ['fps_nut'], [_SQ, (0, 20, 0)]),
    'fps_washer_off': mo('svc_fps_washer_off', ['fps_mounting_washer'], [_SQ, (0, 20, 0)]),
    'carrier_out': mo('svc_carrier_out', MODULE, [_SQ, (0, 70, 0)],
                      note='the rigid xt30_pair proxy is an obstacle (pigtail still in the bay); see SERVICE note'),
    'panel_out': mo('svc_panel_out', PANEL, [_SQ, (0, 70, 0)],
                    note='verify_candidate keeps its pose-local allowance: panel/eyepiece clamp contact < 8 mm3 only '
                         'while the panel is within 0.2 mm of home (modelled 0.1 mm radial EVF clamp)'),
    'camera_in': mo('camera_in', CAMERA, _CAM),
    'evf_in': mo('evf_in', EVF, [(0, 60, 0), _SQ]),
    'storage_plug_reservation_through_enclosure': mo('svc_storage_out', ['usb_storage_plug_reserve'],
                                                     [_SQ, (-70, 0, 0)], riders=STORAGE, exempt=_PLUG_EXEMPT),
    'storage_out': mo('svc_storage_out', STORAGE, [_SQ, (-70, 0, 0)], riders=['usb_storage_plug_reserve']),
    'microsd_out': mo('svc_microsd_out', ['microsd'], [_SQ, MICROSD_DOGLEG_X, MICROSD_DOGLEG_OUT],
                      note='FP-12 (VN-29) dog-leg replaces the straight +X 45 path of 9ced753, which meets lens_collar '
                           'from about +X 32 with the derived obstacles (rejected-path record and window probes: '
                           'verify_microsd_service.py). FP-12 probes at 2 mm: +X 10 hits the carrier, +X 12 is clear, '
                           '+X 24 grazes the tub (0.45 mm3), +X 26 hits tub and s_c3; +X 18 sits inside the clear window; '
                           '+Y 40 takes the card 16 mm past the open panel side (y 28).'),
    # ---- new rows swept by verify_candidate.py ----
    'gauge_out': mo('gauge_out', ['centring_gauge'], [_SQ, (40, 0, 0)],
                    note='gauge x -3.4..21.0 (saved STEP): 40 mm takes its rear end past the collar front (x 8.6)'),
    'collar_off': mo('svc_collar_off', ['lens_collar', 's_c4'], [_SQ, (30, 0, 0)],
                     note='reverse of r7 INSERTIONS collar_on (+X 30); s_c4 rides in its lug insert'),
    'lens_out': mo('svc_lens_out', ['lens'], [_SQ, (40, 0, 0)], note='reverse of r7 INSERTIONS lens_in (+X 40)'),
    'eyepiece_in': mo('eyepiece_in', ['eyepiece'], [(-30, 0, 0), _SQ],
                      note='r7 INSERTIONS eyepiece_in / r7 ASSEMBLY step 6: spigot pushed +X through the rear-wall bore '
                           'from behind. A +Y drop-in (read from the open inner seat in model.evf_support) was probed '
                           'on 2026-10-10 and is NOT a path: the rear wall closes the bore above it (337.942 mm3 tub '
                           'overlap at +Y 12, region x -158..-155.5, y 17.2..28); -Z/+Z drops hit too. Not a measured '
                           'hand path.'),
    'camera_out': mo('svc_camera_out', CAMERA, list(reversed(_CAM))),
    'evf_out': mo('svc_evf_out', EVF, [_SQ, (0, 60, 0)]),
    # ---- build insertions covered by a swept service removal ----
    'collar_on': mo('collar_on', ['lens_collar'], [(30, 0, 0), _SQ], 'covered', covered_by='collar_off'),
    'gauge_in': mo('gauge_in', ['centring_gauge'], [(40, 0, 0), _SQ], 'covered', covered_by='gauge_out'),
    'lens_in': mo('lens_in', ['lens'], [(40, 0, 0), _SQ], 'covered', covered_by='lens_out'),
    'carrier_in': mo('carrier_in', MODULE, [(0, 70, 0), _SQ], 'covered', covered_by='carrier_out'),
    'panel_in': mo('panel_in', PANEL, [(0, 70, 0), _SQ], 'covered', covered_by='panel_out'),
    'fps_washer_on': mo('fps_washer_on', ['fps_mounting_washer'], [(0, 20, 0), _SQ], 'covered',
                        covered_by='fps_washer_off'),
    'fps_nut_on': mo('fps_nut_on', ['fps_nut'], [(0, 20, 0), _SQ], 'covered', covered_by='fps_nut_after_unthread'),
    'knob_fps_on': mo('knob_fps_on', ['knob_fps'], [(0, 20, 0), _SQ], 'covered', covered_by='fps_knob_off'),
    'storage_in': mo('storage_in', STORAGE, [(-70, 0, 0), _SQ], 'covered', covered_by='storage_out',
                     riders=['usb_storage_plug_reserve']),
    'storage_plug_in': mo('storage_in', ['usb_storage_plug_reserve'], [(-70, 0, 0), _SQ], 'covered',
                          covered_by='storage_plug_reservation_through_enclosure', riders=STORAGE,
                          exempt=_PLUG_EXEMPT),
    # ---- not swept for the candidate yet ----
    'base_on': mo('tub_on', ['tub'], [(10, 0, 15), (10, 0, 0), _SQ], 'open',
                  open_reason='keyhole engagement not swept for the candidate (r7 INSERTIONS base_on moves the base '
                              '(-10,0,-15)->(-10,0,0)->0; this is the same relative motion with the tub moving); '
                              'lock moved 2 mm and lip/head 2.4 mm differ from r7; the strap is already threaded '
                              '(its over-bridge pass lies in the base-top recess under the tub floor), so it is an '
                              'obstacle of this motion'),
    'grip_off': mo('svc_grip_off', GRIP + ['strap'], [_SQ, (-10, 0, 0), (-10, 0, -15)], 'open',
                   open_reason='reverse keyhole motion of base_on; not swept for the candidate'),
    'pack_in': mo('pack_in', ['xt30_pair', 'pack'], [(0, 0, -110.2), (0, 0, -80.0), _SQ], 'open',
                  open_reason='r7 INSERTIONS pack_in path from the XT30 mating pose; the candidate re-posed the XT30 '
                              '(21/45 deg) and needs the FP-10 mate_reach/cable_stow port first'),
    'pack_out': mo('svc_pack_out', ['pack'], [_SQ, (0, 0, -80.0), (0, 0, -110.2)], 'open',
                   open_reason='as pack_in; the parted pigtail half stays (xt30_pair proxy)'),
    'cap_on': mo('cap_on', ['cap'], None, 'open',
                 open_reason='r7 INSERTIONS cap_on uses layout.CAP travel (grip/cap unchanged in the candidate); '
                             'not swept for the candidate'),
    'cap_off': mo('svc_cap_off', ['cap'], None, 'open', open_reason='reverse of cap_on; not swept'),
}
SCREW_IDS = set(COLLAR_ANCHORS + ['s_c4'] + PANEL_SCREWS + CARRIER_SCREWS + ['p_grip'])
NUT_IDS = {'fps_nut', 'power_nut_reserve'}
# ----------------------------------------------------------------------------------------------- state functions
def build_sequence(steps=None):
    """[(op, body_before, body_after, groups_after)] for every build op, in order. Bench ops change only their group;
    a body op with `inserts` consumes that group. Sets are frozensets of ids. Bookkeeping errors are left to lint()."""
    steps = STEPS if steps is None else steps
    body, groups, out = set(), {}, []
    for o in steps:
        before = frozenset(body)
        if o['where'] == 'bench':
            groups.setdefault(o['group'], set()).update(o['adds'])
        else:
            body |= set(o['adds'])
            body -= set(o['removes'])
            if o.get('inserts'):
                groups[o['inserts']] = set()
        out.append((o, before, frozenset(body), {k: frozenset(v) for k, v in groups.items()}))
    return out


def _op_index(steps):
    return {o['id']: i for i, o in enumerate(steps)}


def present_at(op_id, steps=None):
    """Ids in the body at the END of build op `op_id` (op id, or 1-based int position like r7 layout.present_at)."""
    seq = build_sequence(steps)
    i = op_id - 1 if isinstance(op_id, int) else _op_index([s[0] for s in seq])[op_id]
    return seq[i][2]


def state_before(op_id, steps=None):
    seq = build_sequence(steps)
    return seq[_op_index([s[0] for s in seq])[op_id]][1]


def final_state(steps=None):
    return build_sequence(steps)[-1][2]


def route_closure(route, service=None):
    """Routes in the order they are carried out to reach `route` (requires first, each once, `route` last)."""
    service = SERVICE if service is None else service
    out = []

    def visit(r, stack=()):
        if r in stack:
            raise ValueError('service requires cycle: %s' % ' -> '.join(stack + (r,)))
        if r in out:
            return
        for q in service[r]['requires']:
            visit(q, stack + (r,))
        out.append(r)
    visit(route)
    return out


def service_sequence(route, steps=None, service=None):
    """[(route_name, sop, before, after)] from the final build state through every op of route_closure(route)."""
    service = SERVICE if service is None else service
    body, out = set(final_state(steps)), []
    for r in route_closure(route, service):
        for o in service[r]['ops']:
            before = frozenset(body)
            body -= set(o['removes'])
            out.append((r, o, before, frozenset(body)))
    return out


def route_of(sop_id, service=None):
    service = SERVICE if service is None else service
    for r, d in service.items():
        if any(o['id'] == sop_id for o in d['ops']):
            return r
    return None


def route_refit(route, closure=True, steps=None, service=None):
    """Build ops (in build order) that put back what the route (and, with closure, its prerequisites) took out:
    reverse_of ops, the op that re-mates every parted cable, body ops driving a fastener the routes removed or
    loosened, and a tool's in/out ops when an included op is carried out with that tool in the body (gauge_in /
    gauge_out around collar_tighten). The documented refit is the whole chain (closure=True) in build order
    (fixup-1: a per-route partial refit followed by the prerequisites gave impossible sequences)."""
    steps = STEPS if steps is None else steps
    service = SERVICE if service is None else service
    idx = _op_index(steps)
    conns = connections_from(steps)
    names = route_closure(route, service) if closure else [route]
    sops = [o for r in names for o in service[r]['ops']]
    taken = {x for o in sops for x in o['removes'] + o['loosens']}
    ops = set()
    for o in sops:
        ops.update(x for x in o['reverse_of'] if x in idx)
        for c in o['disconnects']:
            ends = [oid for _part, oid in conns.get(c, {}).values() if oid in idx]
            if ends:
                remate = o.get('remate_at', {}).get(c)
                if remate is not None and remate not in ends:
                    raise ValueError('service remate op is not an endpoint of %s: %s' % (c, remate))
                ops.add(remate or max(ends, key=idx.get))
    for o in steps:
        if o['where'] == 'body' and (set(o['screws']) | set(o['nuts'])) & taken:
            ops.add(o['id'])
    for tool in TOOLS:
        ins = [i for i, o in enumerate(steps) if tool in o['adds']]
        outs = [i for i, o in enumerate(steps) if tool in o['removes']]
        for i, j in zip(ins, outs):
            if any(i < idx[x] < j for x in ops):
                ops.update((steps[i]['id'], steps[j]['id']))
    return sorted(ops, key=idx.get)


def refit_sequence(route, steps=None, service=None, order=None):
    """[(route, op, before, after)]: the documented refit of `route` (route_refit, whole chain, build order) carried
    out from the end state of its removal (service_sequence(route)[-1]). Bench ops do not change the body."""
    steps = STEPS if steps is None else steps
    service = SERVICE if service is None else service
    seq = service_sequence(route, steps, service)
    body = set(seq[-1][3]) if seq else set(final_state(steps))
    by = {o['id']: o for o in steps}
    out = []
    for oid in (route_refit(route, True, steps, service) if order is None else order):
        o = by[oid]
        before = frozenset(body)
        if o['where'] != 'bench':
            body = (body | set(o['adds'])) - set(o['removes'])
        out.append((route, o, before, frozenset(body)))
    return out


def text_refit_ids(route, service=None):
    """Ids the chain of `route` removes whose refit is only a text refit (no build op re-adds them)."""
    service = SERVICE if service is None else service
    return {x for r in route_closure(route, service) for o in service[r]['ops'] if o['refit'] and not o['reverse_of']
            for x in o['removes']}


def secured_at(lead, steps=None):
    """Build op id at which `lead` is laid into and secured in its lanes (op field `secures`), or None."""
    for o in (STEPS if steps is None else steps):
        if lead in o.get('secures', []):
            return o['id']
    return None


def secured_before(lead, op_id, steps=None):
    """True if `lead` is already secured in its lanes when build op `op_id` starts."""
    steps = STEPS if steps is None else steps
    at = secured_at(lead, steps)
    return at is not None and _op_index(steps)[at] < _op_index(steps)[op_id]


def op_states(op_id, steps=None, service=None):
    """(phase, route, op, before, after) for a build or service op id."""
    for o, before, after, _g in build_sequence(steps):
        if o['id'] == op_id:
            return 'build', None, o, before, after
    r = route_of(op_id, service)
    if r is None:
        raise KeyError(op_id)
    for rr, o, before, after in service_sequence(r, steps, service):
        if o['id'] == op_id:
            return 'service', r, o, before, after
    raise KeyError(op_id)


def _avail(ids, available):
    return sorted(ids) if available is None else sorted(i for i in ids if i in available)


def motion_table(available=None, motions=None, steps=None, service=None, skip_unknown=False):
    """Every motion with its DERIVED obstacle set: (before | after) - movers - riders - exempt. With `available`
    (the ids a variant has: manifest rows plus tool STEP files) ids outside it are dropped and listed in `missing`;
    only OPTIONAL ids may be missing (lint MISSING_ID)."""
    motions = MOTIONS if motions is None else motions
    service_d = SERVICE if service is None else service
    # fixup-1 (FP-05): a build op carried out again in a service refit sees that refit's body (e.g. gauge_in with the
    # EVF and eyepiece in during a collar swap), so its obstacles are the union over the build and every refit state.
    refits = {}
    for r in service_d:
        try:
            for _rr, ro, rb, ra in refit_sequence(r, steps, service_d):
                refits.setdefault(ro['id'], []).append((r, set(rb) | set(ra)))
        except (KeyError, ValueError):   # lint reports SERVICE_ROUTE / REFIT_ROUTE
            pass
    out = []
    for mid, m in motions.items():
        try:
            phase, route, o, before, after = op_states(m['op'], steps, service)
        except KeyError:
            if skip_unknown:          # lint reports MOTION_OP
                continue
            raise
        group = set(m['movers']) | set(m['riders'])
        base = set(before) | set(after)
        again = refits.get(m['op'], []) if phase == 'build' else []
        present = base.union(*[s for _r, s in again])
        obst = present - group - set(m['exempt'])
        every = set(m['movers']) | obst
        out.append(dict(id=mid, phase=phase, route=route, op=m['op'], step=o.get('step', route),
                        movers=_avail(m['movers'], available), riders=_avail(m['riders'], available),
                        obstacles=_avail(obst, available), exempt=dict(m['exempt']), path=m['path'],
                        runner=m['runner'], covered_by=m['covered_by'], open_reason=m['open_reason'],
                        refit_routes=sorted({r for r, _s in again}),
                        refit_only_obstacles=_avail(obst - base, available),
                        missing=[] if available is None else sorted(i for i in every if i not in available)))
    return out


def verify_paths(available):
    """[(motion id, movers, obstacles, knots)] for the motions verify_candidate.py sweeps (runner verify_candidate),
    in MOTIONS order. Raises if a non-optional id is missing from `available` (never sweep a partial set)."""
    rows = []
    for m in motion_table(available):
        if m['runner'] != 'verify_candidate':
            continue
        bad = [i for i in m['missing'] if i not in OPTIONAL]
        if bad:
            raise ValueError('motion %s: ids not available: %s' % (m['id'], bad))
        rows.append((m['id'], m['movers'], m['obstacles'], [list(p) for p in m['path']]))
    return rows


def driver_contexts(available=None, steps=None, service=None):
    """Parts present when each fastener is driven: build (end of the op that tightens it, the fastener itself
    excluded, other screws and tools such as the gauge included) and service (state before the op that loosens or
    removes it). Bench nuts use the bench group state. One row per (fastener, op)."""
    service = SERVICE if service is None else service
    out = []
    for o, before, after, groups in build_sequence(steps):
        here = groups.get(o['group'], frozenset()) if o['where'] == 'bench' else after
        for kind, ids in (('screw', o['screws']), ('nut', o['nuts'])):
            for f in ids:
                out.append(dict(fastener=f, kind=kind, phase='build', route=None, op=o['id'], step=o['step'],
                                where=o['where'], tool=SOCKET if kind == 'nut' else PH1,
                                context=_avail(set(here) - {f}, available)))
    for r in service:
        for rr, o, before, after in service_sequence(r, steps, service):
            if rr != r:
                continue
            for kind, ids in (('screw', o['unscrews'] + o['loosens']), ('nut', o['nuts'])):
                for f in ids:
                    out.append(dict(fastener=f, kind=kind, phase='service', route=r, op=o['id'], step=None,
                                    where='body', tool=SOCKET if kind == 'nut' else PH1,
                                    context=_avail(set(before) - {f}, available)))
    return out


def all_states(steps=None, service=None):
    """Every body state (build after each op, service after each op of every route, and the documented refit of
    every route after each of its ops: phase 'refit', fixup-1) and every bench group state,
    as (phase, route, op_id, frozenset)."""
    service = SERVICE if service is None else service
    for o, before, after, groups in build_sequence(steps):
        yield 'build', None, o['id'], after
        for g, s in groups.items():
            yield 'bench', g, o['id'], s
    for r in service:
        for rr, o, before, after in service_sequence(r, steps, service):
            yield 'service', rr, o['id'], after
    for r in service:
        try:
            seq = refit_sequence(r, steps, service)
        except (KeyError, ValueError):   # lint reports REFIT_ROUTE
            continue
        for rr, o, before, after in seq:
            yield 'refit', rr, o['id'], after
# ----------------------------------------------------------------------------------------------- lint
# (earlier, later, why): the first op that puts `earlier` in the body must come strictly before the one for `later`.
ORDER_RULES = [
    ('strap', 'tub', 'the strap\'s over-bridge pass lies in the 2 mm base-top recess that the seated tub floor closes '
                     '(layout.STRAP upper_recess z -2..0; r7 threads the strap before the tub)'),
    ('lens_collar', 'centring_gauge', 'the gauge centres the fitted collar'),
    ('lens_collar', 'gs_camera', 'VN-39: collar and gauge on the EMPTY lip, camera after'),
    ('gs_camera', 'lens', 'the lens screws into the camera adapter'),
    ('lens', 'carrier', 'VN-41: lens fingertip push and turn-back need the open +Y side'),
    ('s_c4', 'carrier', 'VN-41: camera retained by lens + pinch screw before the carrier'),
    ('lens', 'panel', 'VN-41: lens with the panel off'),
    ('gs_camera', 'carrier', 'the camera cannot pass the installed vertical stack'),
    ('carrier', 'panel', 'the panel closes over the FPS bushing carried by the module'),
    ('eyepiece', 'panel', 'the panel clamps the eyepiece'),
    ('evf_board', 'panel', 'the panel clamps the EVF module'),
    ('panel', 'fps_mounting_washer', 'VN-40: FPS washer refitted on the panel face after the panel'),
    ('fps_mounting_washer', 'fps_nut', 'VN-40'),
    ('fps_nut', 'knob_fps', 'VN-40: the knob press is backed by the nut'),
    ('p_panel1', 'knob_fps', 'panel screws are driven before the FPS knob is on'),
]
POWER_IDS = ('xt30_pair', 'pack', 'cap')
# Parts that never enter the body on their own once their host could close them in: in service they leave with the
# host, and in a refit they re-enter with it (same op or the next one), never while the blocking part is already in.
# {part: (host, blocking part, reason)} (fixup-1; lint ORDER in lint_refit, SERVICE_TRAVEL in service).
TRAVELS_WITH = {'strap': ('base_grip', 'tub', 'the strap stays threaded in the base; with the tub on, its over-bridge '
                                              'recess is closed, so it can only return threaded in the base')}
# Ids a refit op may re-add while still present (lint REFIT_ADD_PRESENT), each with its reason.
REFIT_READD = {'xt30_pair': 'rigid proxy of both XT30 halves + fuse: it stays in the body when only the pack is pulled '
                            '(SERVICE note above), so pack_in re-adds nothing physical on those routes'}


def connections_from(steps):
    """CONNECTIONS-shaped dict rebuilt from the steps' `connects` tokens (part per end from CONNECTIONS)."""
    out = {}
    for o in steps:
        for tok in o['connects']:
            c, e = tok.split(':')
            part = CONNECTIONS.get(c, {}).get(e, (None,))[0]
            out.setdefault(c, {})[e] = (part, o['id'])
    return out


def lint(steps=None, service=None, motions=None, connections=None):
    """[(code, message)] for a step list (default STEPS with SERVICE and MOTIONS). Empty means consistent."""
    main = steps is None
    steps = STEPS if steps is None else steps
    service = SERVICE if service is None and main else (service or {})
    motions = MOTIONS if motions is None and main else (motions or {})
    E = []
    ids = [o['id'] for o in steps] + [o['id'] for r in service.values() for o in r['ops']]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        E.append(('DUP_OP', i))
    seq = build_sequence(steps)
    idx = _op_index(steps)
    first, body, groups, inserted = {}, set(), {}, set()
    for n, (o, before, after, grp) in enumerate(seq):
        if o['where'] not in ('body', 'bench', 'prop'):
            E.append(('WHERE', o['id']))
        if o['where'] == 'bench':
            have = groups.setdefault(o['group'], set())
            E += [('ADD_PRESENT', '%s: %s already in group %s' % (o['id'], a, o['group'])) for a in o['adds'] if a in have]
            have.update(o['adds'])
            here = have
        else:
            E += [('ADD_PRESENT', '%s: %s already in the body' % (o['id'], a)) for a in o['adds'] if a in before]
            E += [('REMOVE_ABSENT', '%s: %s' % (o['id'], a)) for a in o['removes'] if a not in before]
            if o.get('inserts'):
                g = set(groups.get(o['inserts'], ()))
                if g != set(o['adds']):
                    E.append(('INSERT_MISMATCH', '%s: group %s %s vs adds %s' % (o['id'], o['inserts'], sorted(g),
                                                                              sorted(o['adds']))))
                groups[o['inserts']] = set()
                inserted.add(o['inserts'])
            here = after
            for a in o['adds']:
                first.setdefault(a, n)
        E += [('FASTENER_ABSENT', '%s: %s' % (o['id'], f)) for f in o['screws'] + o['nuts'] if f not in here]
    for g, s in groups.items():
        if s:
            E.append(('BENCH_LEFTOVER', '%s never inserted: %s' % (g, sorted(s))))
    final = seq[-1][2] if seq else frozenset()
    # tools
    states = list(all_states(steps, service))
    for t, spec in TOOLS.items():
        if t in final:
            E.append(('TOOL_IN_FINAL', t))
        for phase, route, oid, s in states:
            hit = [x for x in spec['excludes'] if t in s and x in s]
            if hit:
                E.append(('TOOL_COEXIST', '%s with %s at %s %s' % (t, hit, phase, oid)))
    gauge_ops = [o['id'] for o, b, a, g in seq if 'centring_gauge' in a and set(COLLAR_ANCHORS) <= set(o['screws'])]
    if 'centring_gauge' in first and not gauge_ops:
        E.append(('GAUGE_SCREWS', 's_c1..s_c3 are not tightened while the gauge is home'))
    # order, camera retention, power last
    for a, b, why in ORDER_RULES:
        if a not in first or b not in first:
            E.append(('ORDER_MISSING', '%s / %s' % (a, b)))
        elif not first[a] < first[b]:
            E.append(('ORDER', '%s must enter before %s (%s)' % (a, b, why)))
    if 'gs_camera' in first and 'lens' in first:
        between = [a for o, b, af, g in seq[first['gs_camera'] + 1:first['lens']] if o['where'] == 'body'
                   for a in o['adds'] if a != 's_c4']
        if between:
            E.append(('CAMERA_RETAINED', 'parts enter between camera and lens (camera unretained): %s' % between))
    if 'pack' in first:
        late = [a for a, n in first.items() if n > first['pack'] and a not in POWER_IDS]
        early = [p for p in POWER_IDS if p in first and first[p] < max(n for a, n in first.items()
                                                                       if a not in POWER_IDS)]
        if late or early:
            E.append(('POWER_LAST', 'after pack: %s; power parts early: %s' % (late, early)))
    # cable ends
    conns = connections_from(steps) if connections is None else connections
    if main:
        for c, ends in CONNECTIONS.items():
            for e, (part, oid) in ((k, v) for k, v in ends.items() if k != 'doc'):
                if conns.get(c, {}).get(e) != (part, oid):
                    E.append(('MATE_DECL', '%s:%s declared at %s, steps say %s' % (c, e, oid, conns.get(c, {}).get(e))))
    for c, ends in conns.items():
        if len(ends) != 2:
            E.append(('MATE_ENDS', '%s has ends %s' % (c, sorted(ends))))
            continue
        for e, (part, oid) in ends.items():
            if oid not in idx:
                E.append(('MATE_OP', '%s:%s op %s' % (c, e, oid)))
        if any(oid not in idx for part, oid in ends.values()):
            continue
        late = max(ends.values(), key=lambda v: idx[v[1]])
        for e, (part, oid) in ends.items():
            for need, at in ((part, oid), (part, late[1])):
                o, before, after, grp = seq[idx[at]]
                near = set(after) | set(grp.get(o['group'], ())) if o['group'] else set(after)
                for group in o.get('supported_groups', []):
                    if group not in grp:
                        E.append(('MATE_GROUP', '%s: supported group %s is absent at %s' % (c, group, at)))
                    near |= set(grp.get(group, ()))
                if need not in near:
                    E.append(('MATE', '%s: end part %s not present at %s' % (c, need, at)))
    # leads secured in their lanes (fixup-1): never before their far end is mated in a displaced (prop) pose
    seen = {}
    for o in steps:
        for lead in o.get('secures', []):
            if lead in seen:
                E.append(('SECURE_DUP', '%s secured at %s and %s' % (lead, seen[lead], o['id'])))
            seen[lead] = o['id']
            if lead not in conns and lead != 'pigtail':
                E.append(('SECURE_ID', '%s: unknown lead %s' % (o['id'], lead)))
                continue
            for e, (part, oid) in conns.get(lead, {}).items():
                if oid in idx and steps[idx[oid]]['where'] == 'prop' and idx[o['id']] < idx[oid]:
                    E.append(('SECURE_BEFORE_MATE', '%s secured at %s before its %s end is mated at %s (prop pose)'
                              % (lead, o['id'], e, oid)))
    # service bookkeeping and refits
    for r, d in service.items():
        try:
            sseq = service_sequence(r, steps, service)
        except (KeyError, ValueError) as exc:
            E.append(('SERVICE_ROUTE', '%s: %s' % (r, exc)))
            continue
        for rr, o, before, after in sseq:
            if rr != r:
                continue
            E += [('SERVICE_REMOVE_ABSENT', '%s: %s' % (o['id'], a)) for a in o['removes'] if a not in before]
            E += [('FASTENER_ABSENT', '%s: %s' % (o['id'], f)) for f in o['unscrews'] + o['loosens'] + o['nuts']
                  if f not in before]
            if o['removes'] and not o['refit']:
                missing = [x for x in o['reverse_of'] if x not in idx]
                refit = {a for x in o['reverse_of'] if x in idx for a in steps[idx[x]]['adds']}
                if missing or not o['reverse_of'] or not set(o['removes']) <= refit:
                    E.append(('REFIT', '%s removes %s; reverse_of %s adds %s' % (o['id'], o['removes'],
                                                                                o['reverse_of'], sorted(refit))))
    E += _lint_refits(steps, service)
    if motions:
        E += _lint_motions(steps, service, motions)
    return list(dict.fromkeys(E))     # refit TOOL_COEXIST is found by both all_states and lint_refit


def _lint_refits(steps, service):
    """fixup-1 (FP-05/FP-06): the build rules (ORDER, CAMERA_RETAINED, FASTENER_ABSENT, POWER_LAST, bookkeeping) on
    every route's documented refit (whole chain, build order, from the end of its removal; TOOL_COEXIST sees these
    states through all_states), plus camera retention on the service side: no module motion while gs_camera is in
    the body and the lens (with s_c4) is out (VN-42; the camera can drop back 3.9 mm onto the carrier)."""
    E = []
    for r in service:
        try:
            E += lint_refit(r, steps, service)
        except (KeyError, ValueError) as exc:
            E.append(('REFIT_ROUTE', '%s: %s' % (r, exc)))
    return E


def lint_refit(r, steps=None, service=None, order=None):
    """[(code, message)] for route `r`: service-side camera retention, then the refit (refit_sequence with `order`,
    default the documented whole-chain build order) against the build rules. Tests pass other orders."""
    steps = STEPS if steps is None else steps
    service = SERVICE if service is None else service
    E = []
    final = set(final_state(steps))
    seq = service_sequence(r, steps, service)
    rseq = refit_sequence(r, steps, service, order)
    for rr, o, before, after in seq:
        for part, (host, block, why) in TRAVELS_WITH.items():
            if part in o['removes'] and host in before and host not in o['removes']:
                E.append(('SERVICE_TRAVEL', 'service %s %s: %s leaves without %s (%s)' % (r, o['id'], part, host, why)))
        if set(o['removes']) & set(MODULE) and 'gs_camera' in before and 'lens' not in before:
            E.append(('CAMERA_RETAINED', 'service %s %s: the module moves with the camera in and the lens out'
                      % (r, o['id'])))
    first = {}
    build_before = {o['id']: b for o, b, _a, _g in build_sequence(steps)}
    text_ids = text_refit_ids(r, service)
    for n, (rr, o, before, after) in enumerate(rseq):
        # every part the op had in the build must be back before it is repeated (e.g. lens_float needs the lens)
        lack = sorted(set(build_before[o['id']]) - set(before) - text_ids) if o['where'] != 'bench' else []
        if lack:
            E.append(('REFIT_PRECONDITION', 'refit %s %s: build had %s in the body' % (r, o['id'], lack)))
        E += [('REFIT_ADD_PRESENT', 'refit %s %s: %s already in the body' % (r, o['id'], a))
              for a in o['adds'] if o['where'] != 'bench' and a in before and a not in REFIT_READD]
        E += [('REFIT_REMOVE_ABSENT', 'refit %s %s: %s' % (r, o['id'], a)) for a in o['removes'] if a not in before]
        E += [('FASTENER_ABSENT', 'refit %s %s: %s' % (r, o['id'], f)) for f in o['screws'] + o['nuts']
              if f not in after]
        if o['where'] == 'bench':
            continue
        for a in o['adds']:
            if a not in before:
                first.setdefault(a, n)
        if set(o['adds']) & set(MODULE) and 'gs_camera' in before and 'lens' not in before:
            E.append(('CAMERA_RETAINED', 'refit %s %s: the module enters with the camera in and the lens out '
                      '(VN-41 order)' % (r, o['id'])))
    for part, (host, block, why) in TRAVELS_WITH.items():
        if part in first and block in rseq[first[part]][2]:
            hop = [n for n in range(first.get(host, -9), first[part] + 1) if rseq[n][1]['where'] != 'bench']                 if host in first else []
            if not hop or len(hop) > 2:
                E.append(('ORDER', 'refit %s: %s enters at %s with %s in the body, not together with %s (%s)'
                          % (r, part, rseq[first[part]][1]['id'], block, host, why)))
    for a, b, why in ORDER_RULES:
        if b in first and a not in rseq[first[b]][2]:
            E.append(('ORDER', 'refit %s: %s must be in the body before %s enters at %s (%s)'
                      % (r, a, b, rseq[first[b]][1]['id'], why)))
    if 'gs_camera' in first:
        between = [a for rr, o, b, af in rseq[first['gs_camera'] + 1:first.get('lens', len(rseq))]
                   if o['where'] == 'body' for a in o['adds'] if a != 's_c4']
        if between:
            E.append(('CAMERA_RETAINED', 'refit %s: parts enter between camera and lens (camera unretained): %s'
                      % (r, between)))
    power = [first[p] for p in POWER_IDS if p in first]
    late = sorted(a for a, n in first.items() if a not in POWER_IDS and power and n > min(power))
    if late:
        E.append(('POWER_LAST', 'refit %s: enter after a power part: %s' % (r, late)))
    end = set(rseq[-1][3]) if rseq else (set(seq[-1][3]) if seq else final)
    missing = sorted(final - end - text_refit_ids(r, service))
    extra = sorted(end - final)
    if missing or extra:
        E.append(('REFIT_INCOMPLETE', 'refit %s ends with missing %s, extra %s' % (r, missing, extra)))
    for rr, o, before, after in rseq:
        for tname, spec in TOOLS.items():
            hit = [x for x in spec['excludes'] if tname in after and x in after]
            if hit:
                E.append(('TOOL_COEXIST', '%s with %s at refit %s' % (tname, hit, o['id'])))
    return E
def _changed(o):
    return set(o.get('adds', [])) | set(o.get('removes', []))


def _lint_motions(steps, service, motions):
    E = []
    table = {m['id']: m for m in motion_table(None, motions, steps, service, skip_unknown=True)}
    by_op = {}
    for mid, m in motions.items():
        by_op.setdefault(m['op'], []).append(mid)
        try:
            phase, route, o, before, after = op_states(m['op'], steps, service)
        except KeyError:
            E.append(('MOTION_OP', '%s: op %s' % (mid, m['op'])))
            continue
        if set(m['movers']) | set(m['riders']) != _changed(o):
            E.append(('MOTION_SET', '%s: movers+riders %s vs op %s changes %s' % (
                mid, sorted(set(m['movers']) | set(m['riders'])), o['id'], sorted(_changed(o)))))
        for x, why in m['exempt'].items():
            if not str(why).strip() or x not in (set(before) | set(after)):
                E.append(('EXEMPT', '%s: %s' % (mid, x)))
        if m['runner'] not in ('verify_candidate', 'covered', 'open'):
            E.append(('RUNNER', '%s: %s' % (mid, m['runner'])))
        if m['runner'] == 'open' and not m['open_reason']:
            E.append(('RUNNER', '%s: open without open_reason' % mid))
        if m['runner'] != 'open':
            p = m['path'] or []
            seated = p[-1] if set(o.get('adds', [])) else (p[0] if p else None)
            if len(p) < 2 or seated != (0.0, 0.0, 0.0):
                E.append(('PATH', '%s: path %s must have the seated pose (0,0,0) at its op end' % (mid, p)))
        if m['runner'] == 'covered':
            c = motions.get(m['covered_by'])
            if c is None or c['runner'] != 'verify_candidate':
                E.append(('COVERAGE', '%s: covered_by %s is not a swept motion' % (mid, m['covered_by'])))
                continue
            if mid not in table or m['covered_by'] not in table:
                continue
            a, b = table[mid], table[m['covered_by']]
            # every covered mover is swept by the coverer, nothing the coverer carries is a covered obstacle, and the
            # positions are the same (reversed knots)
            if (not set(m['movers']) <= set(c['movers'])
                    or not set(m['riders']) <= set(c['movers']) | set(c['riders'])
                    or (set(c['movers']) | set(c['riders'])) & set(a['obstacles'])
                    or list(reversed(m['path'])) != list(c['path'])):
                E.append(('COVERAGE', '%s vs %s: movers/riders/reversed path differ' % (mid, m['covered_by'])))
            if not set(a['obstacles']) <= set(b['obstacles']):
                E.append(('COVERAGE', '%s obstacles not in %s: %s' % (
                    mid, m['covered_by'], sorted(set(a['obstacles']) - set(b['obstacles'])))))
            if not set(c['exempt']) <= set(m['exempt']):
                E.append(('COVERAGE', '%s: %s exempts more' % (mid, m['covered_by'])))
    ops = [(o, before, after) for o, before, after, g in build_sequence(steps) if o['where'] == 'body']
    ops += [(o, b, a) for r in service for rr, o, b, a in service_sequence(r, steps, service) if rr == r]
    for o, before, after in ops:
        moved = _changed(o) - SCREW_IDS
        if moved and o['id'] not in by_op and not o.get('no_motion'):
            E.append(('MOTION_MISSING', '%s changes %s without a motion or no_motion reason' % (o['id'], sorted(moved))))
    return E


def check_manifest(row_ids, steps=None):
    """[(code, message)] comparing the final build state with one variant's manifest row ids."""
    final, rows = set(final_state(steps)), set(row_ids)
    E = [('MANIFEST_NOT_BUILT', i) for i in sorted(rows - final)]
    E += [('UNKNOWN_ID', i) for i in sorted(final - rows) if i not in OPTIONAL]
    return E


def describe(steps=None):
    """Rendering data for the FP-06 docs and guide builders, one dict per ASSEMBLY step label in order: its ops
    (id, where, doc, adds, removes, fasteners with tool, motions with runner, cable ends) and the body count after
    the step (like r7 'In the body after this step')."""
    by_op = {}
    for mid, m in MOTIONS.items():
        by_op.setdefault(m['op'], []).append(dict(id=mid, runner=m['runner'], covered_by=m['covered_by']))
    out = []
    for o, before, after, g in build_sequence(steps):
        if not out or out[-1]['step'] != o['step']:
            out.append(dict(step=o['step'], ops=[], in_body_after=0))
        out[-1]['ops'].append(dict(id=o['id'], where=o['where'], doc=o['doc'], adds=list(o['adds']),
                                   removes=list(o['removes']), tools=o['tools'],
                                   fasteners=[dict(id=f, tool=PH1) for f in o['screws']] +
                                             [dict(id=f, tool=SOCKET) for f in o['nuts']],
                                   motions=by_op.get(o['id'], []), no_motion=o['no_motion'],
                                   connects=list(o['connects']), closes=list(o['closes']), flex_scope=o.get('flex_scope')))
        out[-1]['in_body_after'] = len(after)
    return out


def flexible_scope():
    """Explicit omissions carried into reports; these holds are not rigid-check failures or passes."""
    return dict(physical_qualified=False, complete_flexible_motion_qualified=False,
                operations={o['id']: o['flex_scope'] for o in STEPS if o.get('flex_scope')})


def summary():
    """Compact, JSON-ready description for evidence rows."""
    return dict(build_ops=[o['id'] for o in STEPS], service_routes={r: [o['id'] for o in d['ops']]
                                                                    for r, d in SERVICE.items()},
                motions={k: v['runner'] for k, v in MOTIONS.items()}, flex_scope=flexible_scope(), lint=lint())


if __name__ == '__main__':
    import json
    errs = lint()
    for o, before, after, g in build_sequence():
        print('%-4s %-20s +%s -%s' % (o['step'], o['id'], ','.join(o['adds']), ','.join(o['removes'])))
    print(json.dumps(dict(lint_errors=errs), indent=1))
    raise SystemExit(1 if errs else 0)
